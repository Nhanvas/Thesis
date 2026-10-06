#!/usr/bin/env python
"""
train_gae_v2.py -- GAE v2 (option C). Same architecture family, loss and schedule as the
locked v1 (train_gae_joint.py: Adam lr 1e-3, cosine, 200 epochs, batch 32, final epoch saved,
LAMBDA 0.1, encoder GCNConv in->64->16, decoder MLP 16->32->out); ONLY the node features change.

Node input (30) = [ adjacency row / max (18) | v1 band powers, per-window min-max (5) |
                    ADDED f7 (7) ]
Feature-reconstruction target (12) = [ v1 band powers, per-window min-max (5) | ADDED f7 (7) ]
ADDED f7 = log band power x5, log line length, signed-log kurtosis (c1b_build_trainset.py),
standardised with the TRAINING windows' mean/std (Tang et al., ICLR 2022, App. A), clipped to
[-4, 4] and mapped to [0, 1] so the reconstruction loss is not dominated by one block.
The constants are saved next to the checkpoint and must be used at score time.

Variants (data from one source, data/trainset_v2):
  clean : not ictal, not 4 h buffer, not flagged (+-5 SD rule), not signal loss  (= v1 definition)
  all   : not ictal, not 4 h buffer, not signal loss (flagged windows included)
Validation loss on the 3 validation subjects with the same variant mask. Sanity at the end:
ictal vs non-ictal AUROC of the joint score on each validation subject (no test subject used).

  python train_gae_v2.py --variant clean --seed 42 --smoke
  python train_gae_v2.py --variant clean --seed 42
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from torch_geometric.utils import dense_to_sparse

import gae_joint as G

TRAIN = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08", "chb09", "chb12",
         "chb19", "chb20", "chb21", "chb23"]
VAL = ["chb10", "chb11", "chb22"]
TEST = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}
assert not (set(TRAIN + VAL) & TEST), "TEST GUARD"
N_ADD = 7
IN_DIM = 18 + 5 + N_ADD
OUT_X = 5 + N_ADD


def find_data_dir(root):
    hits = sorted(Path(root).rglob("chb01.npz"))
    if not hits:
        raise SystemExit(f"chb01.npz not found under {root}")
    return hits[0].parent


def mask(z, variant):
    m = ~z["is_ictal"] & ~z["is_buffer"] & ~z["is_signal_loss"]
    if variant == "clean":
        m &= ~z["is_flag5sd"]
    return m


def norm_constants(data_dir, variant):
    n, s1, s2 = 0, np.zeros(N_ADD), np.zeros(N_ADD)
    for s in TRAIN:
        z = np.load(data_dir / f"{s}.npz", allow_pickle=True)
        F = z["f7"][mask(z, variant)].reshape(-1, N_ADD).astype(np.float64)
        if not np.isfinite(F).all():
            raise SystemExit(f"{s}: non-finite f7 inside the training mask")
        n += len(F); s1 += F.sum(0); s2 += (F * F).sum(0)
    mu = s1 / n
    return mu, np.sqrt(np.maximum(s2 / n - mu * mu, 1e-12))


def scale_add(f7, mu, sd):
    return ((np.clip((f7 - mu) / sd, -4.0, 4.0) + 4.0) / 8.0).astype(np.float32)


def bp_minmax(bp):
    mn = bp.min(axis=1, keepdims=True); mx = bp.max(axis=1, keepdims=True)
    return ((bp - mn) / (mx - mn + 1e-8)).astype(np.float32)


def window_data(A_np, xn_np, fa_np):
    A = torch.tensor(A_np, dtype=torch.float32)
    An = A / (A.amax() + 1e-8)
    xn = torch.tensor(xn_np); fa = torch.tensor(fa_np)
    ei, ew = dense_to_sparse(A)
    return Data(x=torch.cat([An, xn, fa], dim=1), edge_index=ei, edge_attr=ew,
                A=A, Xt=torch.cat([xn, fa], dim=1))


def load_set(data_dir, subjs, variant, mu, sd, max_windows=None, with_ictal=False):
    ds, info = [], {}
    for s in subjs:
        z = np.load(data_dir / f"{s}.npz", allow_pickle=True)
        m = mask(z, variant)
        idx = np.flatnonzero(m)
        if max_windows:
            idx = idx[:max_windows]
        adj = z["adj"][idx].astype(np.float32)
        xn = bp_minmax(z["bp5"][idx].astype(np.float32))
        fa = scale_add(z["f7"][idx].astype(np.float64), mu, sd)
        ds += [window_data(adj[i], xn[i], fa[i]) for i in range(len(idx))]
        info[s] = int(len(idx))
        print(f"  {s}: {len(idx)} windows ({variant})", flush=True)
    return ds, info


def batch_loss(model, b, device):
    b = b.to(device); B = b.num_graphs
    z = model.encoder(b.x, b.edge_index, b.edge_attr)
    zp = z.view(B, G.N_CH, G.LATENT_DIM)
    Ah = torch.clamp(torch.bmm(zp, zp.transpose(1, 2)), 0.0, 1.0)
    Xh = model.x_decoder(z).view(B, G.N_CH, OUT_X)
    A = b.A.view(B, G.N_CH, G.N_CH); X = b.Xt.view(B, G.N_CH, OUT_X)
    per_win = ((A - Ah) ** 2).mean(dim=(1, 2)) + G.LAMBDA * ((X - Xh) ** 2).mean(dim=(1, 2))
    return per_win


def set_seed(seed):
    torch.manual_seed(seed); np.random.seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def sanity_auroc(model, data_dir, mu, sd, device):
    from sklearn.metrics import roc_auc_score
    out = {}
    model.eval()
    for s in VAL:
        z = np.load(data_dir / f"{s}.npz", allow_pickle=True)
        ok = ~z["is_signal_loss"] & ~z["is_buffer"]
        idx = np.flatnonzero(ok)
        adj = z["adj"][idx].astype(np.float32)
        xn = bp_minmax(z["bp5"][idx].astype(np.float32))
        fa = scale_add(z["f7"][idx].astype(np.float64), mu, sd)
        ds = [window_data(adj[i], xn[i], fa[i]) for i in range(len(idx))]
        sc = []
        with torch.no_grad():
            for b in DataLoader(ds, batch_size=512, shuffle=False):
                sc.append(batch_loss(model, b, device).cpu().numpy())
        y = z["is_ictal"][idx].astype(int)
        out[s] = round(float(roc_auc_score(y, np.concatenate(sc))), 4) if 0 < y.sum() < len(y) else None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=["clean", "all"], required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--data_root", default="/kaggle/input")
    ap.add_argument("--out_dir", default="/kaggle/working/gae_v2")
    ap.add_argument("--epochs", type=int, default=200)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    data_dir = find_data_dir(a.data_root)
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    tag = f"gae_v2_{a.variant}_seed{a.seed}" + ("_SMOKE" if a.smoke else "")
    print(f"device={device} data={data_dir} variant={a.variant} seed={a.seed}", flush=True)

    t0 = time.time()
    mu, sd = norm_constants(data_dir, a.variant)
    print("f7 train mean:", np.round(mu, 3).tolist(), "std:", np.round(sd, 3).tolist(), flush=True)
    trs, vas = (TRAIN[:1], VAL[:1]) if a.smoke else (TRAIN, VAL)
    maxw = 2000 if a.smoke else None
    epochs = 2 if a.smoke else a.epochs
    print("Building TRAIN set ..."); train_ds, n_tr = load_set(data_dir, trs, a.variant, mu, sd, maxw)
    print("Building VAL set ...");   val_ds, n_va = load_set(data_dir, vas, a.variant, mu, sd, maxw)
    print(f"  train {len(train_ds)} / val {len(val_ds)} windows, built in {time.time()-t0:.0f}s", flush=True)

    set_seed(a.seed)
    g = torch.Generator().manual_seed(a.seed)
    model = G.GAEModel(in_dim=IN_DIM, bands=OUT_X).to(device)
    print("parameters:", sum(p.numel() for p in model.parameters()), flush=True)
    tl = DataLoader(train_ds, batch_size=a.batch, shuffle=True, generator=g)
    vl = DataLoader(val_ds, batch_size=512, shuffle=False)
    opt = torch.optim.Adam(model.parameters(), lr=a.lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    tr_curve, va_curve = [], []
    for ep in range(epochs):
        model.train(); tot = 0.0; n = 0
        for b in tl:
            opt.zero_grad()
            loss = batch_loss(model, b, device).mean()
            loss.backward(); opt.step()
            tot += loss.item() * b.num_graphs; n += b.num_graphs
        sched.step()
        model.eval(); vt = 0.0; vn = 0
        with torch.no_grad():
            for b in vl:
                l = batch_loss(model, b, device); vt += l.sum().item(); vn += len(l)
        tr_curve.append(tot / n); va_curve.append(vt / vn)
        if ep < 3 or (ep + 1) % 20 == 0 or ep == epochs - 1:
            print(f"  epoch {ep+1:3}/{epochs} train={tr_curve[-1]:.6f} val={va_curve[-1]:.6f} "
                  f"({time.time()-t0:.0f}s)", flush=True)

    torch.save(model.state_dict(), out / f"{tag}.pt")
    np.savez(out / f"{tag}_loss.npz", train=np.array(tr_curve), val=np.array(va_curve))
    san = sanity_auroc(model, data_dir, mu, sd, device) if not a.smoke else {}
    meta = dict(variant=a.variant, seed=a.seed, in_dim=IN_DIM, out_x=OUT_X, n_add=N_ADD,
                add_features=["logbp_delta", "logbp_theta", "logbp_alpha", "logbp_beta", "logbp_gamma",
                              "log_linelen", "slog_kurtosis"],
                add_mean=mu.tolist(), add_std=sd.tolist(), clip=4.0, n_train=n_tr, n_val=n_va,
                epochs=epochs, batch=a.batch, lr=a.lr, lambda_=G.LAMBDA,
                final_train=tr_curve[-1], final_val=va_curve[-1], val_sanity_auroc=san,
                elapsed_s=round(time.time() - t0))
    (out / f"{tag}.json").write_text(json.dumps(meta, indent=1))
    print(f"SAVED {tag}.pt | val ictal-vs-rest AUROC {san} | {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
