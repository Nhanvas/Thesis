"""
lstm_forensic.py — temporal-branch DESIGN validation (PREREG 02 §4 + R1).

Question this answers (on VAL subjects only, no test contact):
  (R1) Does the LSTM input work better as pooled-Z (18x16 -> 16) or flattened-Z (-> 288)?
  (L1) Does a predictive LSTM on the GAE latent sequence discriminate ictal from interictal
       on held-out VAL subjects (mean AUROC >= 0.60)?

This is a DESIGN PROBE, run on the CURRENT validated GAE checkpoint. The production temporal
branch will be re-run on the ADOPTED GAE (after Gate R-GAE). Nothing here touches the 8 test
subjects. Short-run LSTM (few epochs) — enough to compare designs, not the final model.

Run on Kaggle (account-2 is fine; GPU helps but not required):
    !python lstm_forensic.py
"""
import argparse
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import roc_auc_score

import gae_joint as G   # validated GAE class + build_batch

TRAIN_SUBJS = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08",
               "chb09", "chb12", "chb19", "chb20", "chb21", "chb23"]
VAL_SUBJS = ["chb10", "chb11", "chb22"]
L = 16                      # sequence context (15 past + current); from warm-up evidence


# ---- embeddings: run GAE encoder, pool or flatten -------------------------
def embed(model, adj_path, feat_path, device, mode, batch=512):
    adjs = np.load(adj_path, mmap_mode="r"); feats = np.load(feat_path, mmap_mode="r")
    out = []
    model.eval()
    with torch.no_grad():
        for s in range(0, len(adjs), batch):
            e = min(s + batch, len(adjs))
            A = torch.tensor(adjs[s:e].astype(np.float32))
            Xt = torch.tensor(feats[s:e].astype(np.float32))
            pg, _, _, B = G.build_batch(A, Xt, device)
            z = model.encoder(pg.x, pg.edge_index, pg.edge_attr).view(B, G.N_CH, G.LATENT_DIM)
            emb = z.mean(dim=1) if mode == "pool" else z.reshape(B, -1)   # [B,16] or [B,288]
            out.append(emb.cpu().numpy().astype(np.float32))
    return np.concatenate(out, 0)


def subj_emb(model, base, subj, suffix, device, mode, split):
    adj = f"{base}/chbmit-topk20/{subj}_{split}_adjs{suffix}.npy"
    feat = f"{base}/chbmit-processed/{subj}_{split}_features.npy"
    return embed(model, adj, feat, device, mode)


# ---- predictive-LSTM dataset over one contiguous embedding array ----------
class SeqDS(Dataset):
    """(context[L-1,D], target[D]) pairs from a single [T,D] chronological array."""
    def __init__(self, arrays):     # arrays: list of [T,D] (per subject / per run)
        self.idx = []; self.arrays = arrays
        for a_i, a in enumerate(arrays):
            for t in range(L - 1, len(a)):
                self.idx.append((a_i, t))
    def __len__(self): return len(self.idx)
    def __getitem__(self, k):
        a_i, t = self.idx[k]; a = self.arrays[a_i]
        return a[t - L + 1:t], a[t]


class PredLSTM(nn.Module):
    def __init__(self, d, hidden=64):
        super().__init__()
        self.lstm = nn.LSTM(d, hidden, batch_first=True)
        self.head = nn.Linear(hidden, d)
    def forward(self, x):
        o, _ = self.lstm(x)
        return self.head(o[:, -1, :])


def zfit(arrs):
    allx = np.concatenate(arrs, 0)
    mu, sd = allx.mean(0), allx.std(0) + 1e-6
    return mu, sd


def score_seq(model, arr, device):
    """raw_temp[t] = ||e_t - pred||^2, masked (nan) for first L-1."""
    n, d = arr.shape
    out = np.full(n, np.nan, np.float32)
    if n < L: return out
    ctx = np.stack([arr[t - L + 1:t] for t in range(L - 1, n)])   # [n-L+1, L-1, d]
    with torch.no_grad():
        pred = model(torch.tensor(ctx, dtype=torch.float32, device=device)).cpu().numpy()
    tgt = arr[L - 1:]
    out[L - 1:] = ((tgt - pred) ** 2).mean(1)
    return out


def run_mode(gae, base, suffix, device, mode, epochs):
    print(f"\n########## INPUT = {mode}  (D={16 if mode=='pool' else 288}) ##########")
    # ---- train embeddings (interictal, TRAIN subjects) ----
    tr = [subj_emb(gae, base, s, suffix, device, mode, "interictal") for s in TRAIN_SUBJS]
    mu, sd = zfit(tr)
    tr = [(a - mu) / sd for a in tr]
    d = tr[0].shape[1]
    dl = DataLoader(SeqDS(tr), batch_size=256, shuffle=True)

    lstm = PredLSTM(d).to(device)
    opt = torch.optim.Adam(lstm.parameters(), lr=1e-3)
    lossf = nn.MSELoss()
    for ep in range(epochs):
        lstm.train(); tot = 0; nb = 0
        for ctx, tgt in dl:
            ctx = ctx.to(device); tgt = tgt.to(device)
            opt.zero_grad(); loss = lossf(lstm(ctx), tgt); loss.backward(); opt.step()
            tot += loss.item(); nb += 1
        if ep == 0 or (ep + 1) % 5 == 0:
            print(f"  epoch {ep+1}/{epochs} train_mse={tot/nb:.4f}")

    # ---- evaluate: VAL standalone AUROC (inter vs ictal) ----
    aucs = []
    for s in VAL_SUBJS:
        ei = (subj_emb(gae, base, s, suffix, device, mode, "interictal") - mu) / sd
        ec = (subj_emb(gae, base, s, suffix, device, mode, "ictal") - mu) / sd
        si = score_seq(lstm, ei, device); sc = score_seq(lstm, ec, device)
        si = si[~np.isnan(si)]; sc = sc[~np.isnan(sc)]
        auc = roc_auc_score(np.r_[np.zeros(len(si)), np.ones(len(sc))], np.r_[si, sc])
        aucs.append(auc)
        print(f"  VAL {s}: standalone AUROC = {auc:.4f}  (inter={len(si)}, ictal={len(sc)})")
    m = float(np.mean(aucs))
    print(f"  >>> {mode}: VAL mean AUROC = {m:.4f}  (bar >= 0.60)")
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="/kaggle/input/datasets/nhn2mm")
    ap.add_argument("--model", default="/kaggle/input/datasets/nhn2mm/gae-joint-model/best_model_joint_lambda01.pt")
    ap.add_argument("--suffix", default="_topk20")
    ap.add_argument("--epochs", type=int, default=20)
    a = ap.parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={device} | DESIGN PROBE on current checkpoint | VAL={VAL_SUBJS}")
    gae = G.load_checkpoint(a.model, device)

    res = {m: run_mode(gae, a.base, a.suffix, device, m, a.epochs) for m in ["pool", "flat"]}
    print("\n================ FORENSIC VERDICT ================")
    for m, v in res.items():
        print(f"  {m:5}: VAL mean AUROC = {v:.4f}  {'PASS' if v >= 0.60 else 'below bar'}")
    win = max(res, key=res.get)
    print(f"  -> pick input = {win}  (higher VAL AUROC). Locks R1 for PREREG 02.")
    print("  NOTE: production LSTM re-runs on the ADOPTED GAE; this only fixes the design.")


if __name__ == "__main__":
    main()
