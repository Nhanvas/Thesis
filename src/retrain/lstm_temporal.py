"""
lstm_temporal.py — shared module for the redesigned temporal branch (PREREG_02, PHA 1 step 2).
Reuses the ADOPTED (Gate R-GAE PASS) gae_joint.py for Z extraction; nothing here touches decoding.
"""
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import roc_auc_score

import gae_joint as G

FLAT_DIM = 18 * 16      # 288 — decided input representation (PREREG_02 §5, L0)
POOLED_DIM = 16
HIDDEN = 64


def compute_raw_Z(model, adj_path, feat_path, device, batch_size=512):
    """[n_win, 18, 16] encoder latents. Identical input construction to gae_joint.score_windows
    (An/Xn normalisation, edges from raw A) — only the readout differs (encoder output, not decoded)."""
    adjs = np.load(adj_path, mmap_mode="r")
    feats = np.load(feat_path, mmap_mode="r")
    out = []
    model.eval()
    with torch.no_grad():
        for s in range(0, len(adjs), batch_size):
            e = min(s + batch_size, len(adjs))
            A = torch.tensor(adjs[s:e].astype(np.float32))
            Xt = torch.tensor(feats[s:e].astype(np.float32))
            pg, A, Xn, B = G.build_batch(A, Xt, device)
            z = model.encoder(pg.x, pg.edge_index, pg.edge_attr)
            out.append(z.view(B, 18, 16).cpu().numpy().astype(np.float32))
    return np.concatenate(out, axis=0)


def flat(Z):
    return Z.reshape(Z.shape[0], -1)          # [n_win, 288]


def pooled(Z):
    return Z.mean(axis=1)                     # [n_win, 16]


class LSTMPredictor(nn.Module):
    """1-layer LSTM, hidden=64. head dim = in_dim (matches whichever representation is used —
    see note re: PREREG_02 §2 vs §5 head-dim discrepancy, resolved in favour of §5's DECIDED input)."""
    def __init__(self, in_dim=FLAT_DIM, hidden=HIDDEN, layers=1):
        super().__init__()
        self.lstm = nn.LSTM(in_dim, hidden, num_layers=layers, batch_first=True)
        self.head = nn.Linear(hidden, in_dim)

    def forward(self, seq):
        out, _ = self.lstm(seq)
        return self.head(out[:, -1, :])


def build_sequences(Z_repr, L=16):
    """Full sliding-window materialisation — fine for SMALL arrays (VAL scoring, forensic probe).
    Do NOT use this for the large TRAIN set (see build_anchor_index below)."""
    n = len(Z_repr)
    if n < L:
        return np.zeros((0, L - 1, Z_repr.shape[1]), np.float32), np.zeros((0, Z_repr.shape[1]), np.float32)
    X = np.stack([Z_repr[t - (L - 1):t] for t in range(L - 1, n)])
    y = Z_repr[L - 1:n]
    return X.astype(np.float32), y.astype(np.float32)


def build_anchor_index(Z_by_subj, L):
    """[(subj, t)] for every valid training example across per-subject compact Z arrays.
    Avoids materialising the full sliding-window tensor for a large TRAIN set (each window would
    otherwise be duplicated across up to L-1 overlapping sequences — real RAM concern at ~270k windows)."""
    anchors = []
    for s, Z in Z_by_subj.items():
        for t in range(L - 1, len(Z)):
            anchors.append((s, t))
    return anchors


def gather_anchor_batch(Z_by_subj, anchors, idx, L):
    xb = np.stack([Z_by_subj[anchors[i][0]][anchors[i][1] - (L - 1): anchors[i][1]] for i in idx])
    yb = np.stack([Z_by_subj[anchors[i][0]][anchors[i][1]] for i in idx])
    return xb.astype(np.float32), yb.astype(np.float32)


def score_full_array(model, Z_repr, L, device, batch_size=512):
    """Scores EVERY window. First L-1 entries = np.nan — explicit warm-up mask, NOT a zero-fill
    (avoids the synthetic-zero variance-dilution bug already documented for the CPD stage).
    How to fill this region in the FINAL exported ztemp array is a LATER decision, out of scope here."""
    n = len(Z_repr)
    raw_temp = np.full(n, np.nan, dtype=np.float32)
    if n < L:
        return raw_temp
    X, y = build_sequences(Z_repr, L)
    model.eval()
    preds = []
    with torch.no_grad():
        for s in range(0, len(X), batch_size):
            e = min(s + batch_size, len(X))
            xb = torch.tensor(X[s:e], device=device)
            preds.append(model(xb).cpu().numpy())
    pred = np.concatenate(preds, axis=0)
    raw_temp[L - 1:] = ((y - pred) ** 2).mean(axis=1)
    return raw_temp


def window_auroc(raw_temp_inter, raw_temp_ictal):
    """AUROC on post-warm-up (non-NaN) windows only."""
    si = raw_temp_inter[~np.isnan(raw_temp_inter)]
    sc = raw_temp_ictal[~np.isnan(raw_temp_ictal)]
    if len(si) == 0 or len(sc) == 0:
        return float("nan")
    y = np.r_[np.zeros(len(si)), np.ones(len(sc))]
    return float(roc_auc_score(y, np.r_[si, sc]))