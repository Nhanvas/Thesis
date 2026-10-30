#!/usr/bin/env python
"""
v9_x3_train_fold.py -- V9-X3 (docs/prompts/V9_X3_CV_PREP.md), step 3: one GAE v2 (variant
"clean", seed 42) per fold, trained on the Kaggle GPU. Read-only reuse of
retrain/train_gae_v2.py's own functions (mask, scale_add, bp_minmax, window_data, batch_loss,
set_seed, norm_constants, load_set, sanity_auroc) -- same architecture family, loss and schedule
as the locked thesis model (Adam lr 1e-3, cosine, 200 epochs, batch 32, final epoch kept,
LAMBDA 0.1, encoder GCNConv in->64->16, decoder MLP 16->32->out; node input 30 = adjacency row
(18) + v1 band powers per-window min-max (5) + f7 (7)). ONLY the subject list and the
normalisation constants change: TRAIN = every subject of the OTHER three folds
(results/v9_x3/folds.json / fold_manifests.json), fit from that pool's own windows only -- no
EEG re-extraction, every file already exists in data/trainset_v2/, data/testset_v2/ or
results/v9_x3/chb24.npz (built by v9_x3_build_chb24.py; the ONLY subject not already in the
thesis's own per-subject arrays).

DEVIATION from train_gae_v2.py, disclosed (flagged for the author to confirm before the Kaggle
run): no held-out VAL subjects. The original VAL (chb10, chb11, chb22) exists only to print a
per-epoch monitoring curve and a non-ictal/ictal sanity AUROC; the model-selection rule is fixed
("last epoch kept") regardless of val loss, so VAL carries no decision weight there either. This
study's own stated goal is training on MORE patients per fold, so no validation subset is carved
out of the fold's training pool; a train-loss curve is still printed for a sanity check. If the
author wants the original per-epoch monitoring restored, the simplest fix is 2 validation
subjects per fold (lowest seizure count in the training pool) -- not done here without
confirmation.

Expected directory layout under --data_root (what the author zips into the Kaggle dataset
v9-x3-fold{k}, one subject's .npz per file, any nesting -- resolved by filename, not by a fixed
parent dir): the files named in results/v9_x3/fold_manifests.json's "train_sources" for this
fold.

Output (under --out_dir, default /kaggle/working/v9_x3): gae_fold{k}_seed{seed}.pt (state dict),
gae_fold{k}_seed{seed}.json (meta: add_mean/add_std/clip, in_dim, out_x, n_train, elapsed_s,
parameter count -- must be 3,964, same architecture), gae_fold{k}_seed{seed}_loss.npz (train
curve only).

  python src/v9_x3_train_fold.py --fold 1 --seed 42 --smoke   (2 epochs, CPU, one training subject)
  python src/v9_x3_train_fold.py --fold 1 --seed 42           (Kaggle: --data_root /kaggle/input,
                                                                  GPU T4x2 picked up automatically)
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch_geometric.loader import DataLoader

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import gae_joint as G                 # noqa: E402
import train_gae_v2 as TGV2           # noqa: E402

OUT_V9X3 = ROOT / "results" / "v9_x3"
IN_DIM, OUT_X, N_ADD = TGV2.IN_DIM, TGV2.OUT_X, TGV2.N_ADD


def fold_train_subjects(fold):
    man = json.loads((OUT_V9X3 / "fold_manifests.json").read_text())[str(fold)]
    return man["train_cases"], man["train_sources"]


def find_npz(data_root, subj):
    hits = sorted(Path(data_root).rglob(f"{subj}.npz"))
    if not hits:
        raise SystemExit(f"{subj}.npz not found under {data_root}")
    return hits[0]


def norm_constants_fold(data_root, subs, variant):
    """train_gae_v2.norm_constants, generalised: iterates an explicit subject list resolved by
    filename under data_root instead of the module's hardcoded TRAIN and single data_dir."""
    n, s1, s2 = 0, np.zeros(N_ADD), np.zeros(N_ADD)
    for s in subs:
        z = np.load(find_npz(data_root, s), allow_pickle=True)
        F = z["f7"][TGV2.mask(z, variant)].reshape(-1, N_ADD).astype(np.float64)
        if not np.isfinite(F).all():
            raise SystemExit(f"{s}: non-finite f7 inside the training mask")
        n += len(F); s1 += F.sum(0); s2 += (F * F).sum(0)
    mu = s1 / n
    return mu, np.sqrt(np.maximum(s2 / n - mu * mu, 1e-12))


def load_set_fold(data_root, subs, variant, mu, sd, max_windows=None):
    """train_gae_v2.load_set, generalised the same way as norm_constants_fold."""
    ds, info = [], {}
    for s in subs:
        z = np.load(find_npz(data_root, s), allow_pickle=True)
        m = TGV2.mask(z, variant)
        idx = np.flatnonzero(m)
        if max_windows:
            idx = idx[:max_windows]
        adj = z["adj"][idx].astype(np.float32)
        xn = TGV2.bp_minmax(z["bp5"][idx].astype(np.float32))
        fa = TGV2.scale_add(z["f7"][idx].astype(np.float64), mu, sd)
        ds += [TGV2.window_data(adj[i], xn[i], fa[i]) for i in range(len(idx))]
        info[s] = int(len(idx))
        print(f"  {s}: {len(idx)} windows ({variant})", flush=True)
    return ds, info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fold", type=int, required=True, choices=[1, 2, 3, 4])
    ap.add_argument("--variant", choices=["clean", "all"], default="clean")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--data_root", default="/kaggle/input")
    ap.add_argument("--out_dir", default="/kaggle/working/v9_x3")
    ap.add_argument("--epochs", type=int, default=200)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    tag = f"gae_fold{a.fold}_seed{a.seed}" + ("_SMOKE" if a.smoke else "")

    train_subs, train_sources = fold_train_subjects(a.fold)
    print(f"fold {a.fold}: {len(train_subs)} training subjects: {train_subs}", flush=True)
    print(f"device={device} data_root={a.data_root} variant={a.variant} seed={a.seed}", flush=True)

    t0 = time.time()
    trs = train_subs[:1] if a.smoke else train_subs
    mu, sd = norm_constants_fold(a.data_root, trs, a.variant)
    print("f7 train mean:", np.round(mu, 3).tolist(), "std:", np.round(sd, 3).tolist(), flush=True)
    maxw = 2000 if a.smoke else None
    epochs = 2 if a.smoke else a.epochs
    print("Building TRAIN set ...")
    train_ds, n_tr = load_set_fold(a.data_root, trs, a.variant, mu, sd, maxw)
    print(f"  train {len(train_ds)} windows, built in {time.time()-t0:.0f}s", flush=True)

    TGV2.set_seed(a.seed)
    g = torch.Generator().manual_seed(a.seed)
    model = G.GAEModel(in_dim=IN_DIM, bands=OUT_X).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print("parameters:", n_params, flush=True)
    if n_params != 3964:
        raise SystemExit(f"STOP: parameter count {n_params} != 3964 (architecture must match the "
                          "thesis model exactly)")
    tl = DataLoader(train_ds, batch_size=a.batch, shuffle=True, generator=g)
    opt = torch.optim.Adam(model.parameters(), lr=a.lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    tr_curve = []
    for ep in range(epochs):
        model.train(); tot = 0.0; n = 0
        for b in tl:
            opt.zero_grad()
            loss = TGV2.batch_loss(model, b, device).mean()
            loss.backward(); opt.step()
            tot += loss.item() * b.num_graphs; n += b.num_graphs
        sched.step()
        tr_curve.append(tot / n)
        if ep < 3 or (ep + 1) % 20 == 0 or ep == epochs - 1:
            print(f"  epoch {ep+1:3}/{epochs} train={tr_curve[-1]:.6f} "
                  f"({time.time()-t0:.0f}s)", flush=True)

    torch.save(model.state_dict(), out / f"{tag}.pt")
    np.savez(out / f"{tag}_loss.npz", train=np.array(tr_curve))
    meta = dict(fold=a.fold, held_out_cases=json.loads((OUT_V9X3 / "fold_manifests.json").read_text())
                [str(a.fold)]["held_out_cases"], train_cases=train_subs, train_sources=train_sources,
                variant=a.variant, seed=a.seed, in_dim=IN_DIM, out_x=OUT_X, n_add=N_ADD,
                add_features=["logbp_delta", "logbp_theta", "logbp_alpha", "logbp_beta", "logbp_gamma",
                              "log_linelen", "slog_kurtosis"],
                add_mean=mu.tolist(), add_std=sd.tolist(), clip=4.0, n_train=n_tr, no_val_subset=True,
                epochs=epochs, batch=a.batch, lr=a.lr, lambda_=G.LAMBDA, n_params=n_params,
                final_train=tr_curve[-1], elapsed_s=round(time.time() - t0))
    (out / f"{tag}.json").write_text(json.dumps(meta, indent=1))
    print(f"SAVED {tag}.pt | final train loss {tr_curve[-1]:.6f} | {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
