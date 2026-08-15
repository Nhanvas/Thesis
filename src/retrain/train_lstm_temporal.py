"""
train_lstm_temporal.py — PRODUCTION temporal branch (PREREG 02, locked design).

Design (locked): predictive LSTM on FLATTENED GAE latent Z (288-D), context L=16, run over each
split-array as one chronological sequence (context-A), robust-z per subject. Trained on interictal of
the 12 TRAIN subjects; VAL = {chb10,chb11,chb22} for the gate; the 8 TEST subjects are scored (inference)
but never trained on. Multi-seed {42,1,2,3,4}; seed 42 canonical.

RUN AFTER Gate R-GAE: pass --model = the ADOPTED GAE checkpoint (retrained seed-42 if adopted, else the
current joint checkpoint). This script is GAE-path-parameterised, so it is valid regardless of the Gate R
outcome.

    !python train_lstm_temporal.py --model /kaggle/working/gae_retrain/gae_joint_seed42.pt --seeds 42 1 2 3 4
"""
import argparse
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import roc_auc_score

import gae_joint as G

TRAIN_SUBJS = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08",
               "chb09", "chb12", "chb19", "chb20", "chb21", "chb23"]
VAL_SUBJS = ["chb10", "chb11", "chb22"]
TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
L = 16
D = G.N_CH * G.LATENT_DIM        # 288 (flattened Z, locked)


# ---- flattened-Z embeddings ------------------------------------------------
def embed(model, base, subj, split, suffix, device, batch=512):
    adjs = np.load(f"{base}/chbmit-topk20/{subj}_{split}_adjs{suffix}.npy", mmap_mode="r")
    feats = np.load(f"{base}/chbmit-processed/{subj}_{split}_features.npy", mmap_mode="r")
    out = []
    model.eval()
    with torch.no_grad():
        for s in range(0, len(adjs), batch):
            e = min(s + batch, len(adjs))
            A = torch.tensor(adjs[s:e].astype(np.float32)); Xt = torch.tensor(feats[s:e].astype(np.float32))
            pg, _, _, B = G.build_batch(A, Xt, device)
            z = model.encoder(pg.x, pg.edge_index, pg.edge_attr).view(B, G.N_CH, G.LATENT_DIM)
            out.append(z.reshape(B, -1).cpu().numpy().astype(np.float32))
    return np.concatenate(out, 0)


class SeqDS(Dataset):
    def __init__(self, arrays):
        self.arrays = arrays; self.idx = []
        for ai, a in enumerate(arrays):
            for t in range(L - 1, len(a)):
                self.idx.append((ai, t))
    def __len__(self): return len(self.idx)
    def __getitem__(self, k):
        ai, t = self.idx[k]; a = self.arrays[ai]
        return a[t - L + 1:t], a[t]


class PredLSTM(nn.Module):
    def __init__(self, d=D, hidden=64):
        super().__init__(); self.lstm = nn.LSTM(d, hidden, batch_first=True); self.head = nn.Linear(hidden, d)
    def forward(self, x):
        o, _ = self.lstm(x); return self.head(o[:, -1, :])


def robust_z_norm(raw_inter, raw_ictal):
    all_s = np.concatenate([raw_inter, raw_ictal]); med = np.median(all_s)
    mad = np.median(np.abs(all_s - med)) + 1e-9
    return (raw_inter - med) / mad, (raw_ictal - med) / mad


def score_seq(lstm, arr, device):
    n = len(arr); out = np.full(n, np.nan, np.float32)
    if n >= L:
        ctx = np.stack([arr[t - L + 1:t] for t in range(L - 1, n)])
        with torch.no_grad():
            pred = lstm(torch.tensor(ctx, dtype=torch.float32, device=device)).cpu().numpy()
        out[L - 1:] = ((arr[L - 1:] - pred) ** 2).mean(1)
    return out


def set_seed(s):
    torch.manual_seed(s); np.random.seed(s)
    torch.backends.cudnn.deterministic = True; torch.backends.cudnn.benchmark = False


def main():
    ap = argparse.ArgumentParser()
    base = "/kaggle/input/datasets/nhn2mm"
    ap.add_argument("--base", default=base)
    ap.add_argument("--model", required=True, help="ADOPTED GAE checkpoint (post Gate R-GAE)")
    ap.add_argument("--suffix", default="_topk20")
    ap.add_argument("--out_dir", default="/kaggle/working/lstm_retrain")
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 1, 2, 3, 4])
    ap.add_argument("--canonical", type=int, default=42)
    a = ap.parse_args()
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    out = Path(a.out_dir); (out / "components").mkdir(parents=True, exist_ok=True)
    print(f"device={dev} | GAE={a.model} | input=flat-Z(288) context-A L={L}")

    gae = G.load_checkpoint(a.model, dev)

    # L4 leakage guard
    assert not (set(TRAIN_SUBJS) & set(TEST_SUBJS)) and not (set(TRAIN_SUBJS) & set(VAL_SUBJS)), "LEAK"

    # embeddings once (train interictal + val/test both splits) — GAE is fixed
    print("Extracting flat-Z embeddings ...")
    emb = {}
    for s in TRAIN_SUBJS:
        emb[(s, "interictal")] = embed(gae, a.base, s, "interictal", a.suffix, dev)
    for s in VAL_SUBJS + TEST_SUBJS:
        for sp in ["interictal", "ictal"]:
            emb[(s, sp)] = embed(gae, a.base, s, sp, a.suffix, dev)

    # train-normalisation fit on TRAIN interictal embeddings
    allx = np.concatenate([emb[(s, "interictal")] for s in TRAIN_SUBJS], 0)
    mu, sd = allx.mean(0), allx.std(0) + 1e-6
    znorm = lambda x: (x - mu) / sd

    val_auc_per_seed = {}
    for seed in a.seeds:
        print(f"\n=== SEED {seed} ===")
        set_seed(seed)
        tr = [znorm(emb[(s, "interictal")]) for s in TRAIN_SUBJS]
        g = torch.Generator().manual_seed(seed)
        dl = DataLoader(SeqDS(tr), batch_size=256, shuffle=True, generator=g)
        lstm = PredLSTM().to(dev); opt = torch.optim.Adam(lstm.parameters(), lr=1e-3); lf = nn.MSELoss()
        for ep in range(a.epochs):
            lstm.train(); tot = 0; nb = 0
            for ctx, tgt in dl:
                ctx = ctx.to(dev); tgt = tgt.to(dev)
                opt.zero_grad(); loss = lf(lstm(ctx), tgt); loss.backward(); opt.step()
                tot += loss.item(); nb += 1
            if ep == 0 or (ep + 1) % 10 == 0:
                print(f"  epoch {ep+1}/{a.epochs} train_mse={tot/nb:.4f}")
        torch.save(lstm.state_dict(), out / f"lstm_temporal_seed{seed}.pt")

        # score VAL (gate) + TEST (final component); produce ztemp aligned to arrays
        vaucs = []
        for s in VAL_SUBJS + TEST_SUBJS:
            ri = score_seq(lstm, znorm(emb[(s, "interictal")]), dev)
            rc = score_seq(lstm, znorm(emb[(s, "ictal")]), dev)
            # VAL standalone AUROC on valid (non-warmup) windows
            if s in VAL_SUBJS:
                vi, vc = ri[~np.isnan(ri)], rc[~np.isnan(rc)]
                vaucs.append(roc_auc_score(np.r_[np.zeros(len(vi)), np.ones(len(vc))], np.r_[vi, vc]))
            # fill warm-up with interictal-median (neutral) -> robust-z -> ztemp component
            fill = np.nanmedian(ri)
            ri = np.where(np.isnan(ri), fill, ri); rc = np.where(np.isnan(rc), fill, rc)
            zi, zc = robust_z_norm(ri, rc)
            tag = "" if seed == a.canonical else f"_seed{seed}"
            np.save(out / "components" / f"ztemp_{s}_inter{tag}.npy", zi.astype(np.float32))
            np.save(out / "components" / f"ztemp_{s}_ictal{tag}.npy", zc.astype(np.float32))
        val_auc_per_seed[seed] = float(np.mean(vaucs))
        print(f"  [seed {seed}] VAL mean standalone AUROC = {val_auc_per_seed[seed]:.4f}")

    # ---- Gate R-LSTM (L1 discriminative, L3 stability, L4 leakage) ----
    vals = np.array(list(val_auc_per_seed.values()))
    m, s_ = vals.mean(), (vals.std(ddof=1) if len(vals) > 1 else 0.0)
    L1 = m >= 0.60; L3 = s_ <= 0.05
    print("\n================ Gate R-LSTM ================")
    print(f"  per-seed VAL AUROC: {{{', '.join(f'{k}:{v:.3f}' for k,v in val_auc_per_seed.items())}}}")
    print(f"  L1 mean VAL AUROC = {m:.4f} (>=0.60) -> {'PASS' if L1 else 'FAIL'}")
    print(f"  L3 across-seed SD = {s_:.4f} (<=0.05) -> {'PASS' if L3 else 'FAIL'}")
    print(f"  L4 leakage guard  -> PASS (asserted); warm-up filled with interictal median")
    print(f"  L2 (complementary) -> deferred to PREREG 03 ensemble assembly on VAL")
    print("\nVERDICT:", "PASS — temporal branch accepted" if (L1 and L3) else "REVIEW — see PREREG 02 §5")
    import csv
    with open(out / "lstm_gate_report.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["seed", "val_mean_auroc"])
        for k, v in val_auc_per_seed.items(): w.writerow([k, f"{v:.4f}"])
    print(f"Wrote {out/'lstm_gate_report.csv'}  |  ztemp components -> {out/'components'}")


if __name__ == "__main__":
    main()
