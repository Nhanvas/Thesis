"""
train_lstm_temporal_v3.py — LSTM retrain. normfix (raw-Z) + PREREG_02 §2 registered schedule.

ROOT CAUSE (confirmed from src/retrain): the round-1 trainer trained on per-dim z-normalised flat-Z
(mu/sd fit on train-interictal) and NEVER persisted mu/sd, while every scorer (lstm_gate_full.py,
final_eval.py -> lstm_temporal.score_full_array) scores on RAW flat-Z. So the LSTM optimised a
different quantity (MSE on znorm'd Z) than the pipeline measures (MSE on raw Z). The normfix trains on
RAW flat-Z so training objective == eval metric.

UPDATE 2026-08-14 (v3.1): the norm-fix isolation is complete (normfix-alone did NOT recover the
number), so this script now ALSO restores the schedule PREREG_02 §2 actually registered —
Adam lr 1e-3 + CosineAnnealingLR over 200 epochs, batch 64 — which the round-1 production trainer had
silently reduced to 40 epochs / no cosine / batch 256 (a 3-axis deviation, a plausible driver of the
seed instability). This is FAITHFUL EXECUTION of the registered design, NOT number-tuning; acceptance
stays on the pre-registered VAL stability gate (per-seed VAL AUROC; L3 across-seed SD <= 0.05), and the
8 test subjects are reported as-is downstream (never touched here).

Held at the registered design / eval-path:
  - train on RAW flat-Z(288) (normfix), context L=16, per-split-array chronological sequence, SeqDS
  - Adam lr 1e-3, cosine anneal, 200 epochs, batch 64  (PREREG_02 §2)
  - warm-up + robust-z export convention identical to the eval path
Uses lstm_temporal.LSTMPredictor (the class the scorers load) so the checkpoint is byte-loadable.
GAE seed-42 is loaded dir-tolerant (no manual re-zip). GAE + gamma are reused as-is.

RUN (Kaggle GPU). Attach: gae-seed-checkpoints + chbmit graph/feature datasets. Do NOT attach the
old lstm.temporal dataset (avoids a seed-42 checkpoint collision downstream). Multi-account split OK
(same dataset -> identical paths): give each account a subset of --seeds and collect every .pt to Cursor.
    !python train_lstm_temporal_v3.py --input_root /kaggle/input --epochs 200 --seeds 42 1 2 3 4
Then evaluate with the UNCHANGED locked eval path (build_ens.py equal-weight -> score_ens.py on Cursor).
"""
import argparse
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import roc_auc_score

import gae_joint as G
import lstm_temporal as T          # canonical class + scoring the pipeline uses
import retrain_io as IO            # dir-tolerant checkpoint discovery/loader

TRAIN_SUBJS = IO.TRAIN_SUBJS
VAL_SUBJS = IO.VAL_SUBJS
TEST_SUBJS = IO.TEST_SUBJS
L = 16
D = 18 * 16                        # 288


def embed(model, adj_dir, feat_dir, subj, split, suffix, device):
    """RAW flat-Z, identical construction to T.flat(T.compute_raw_Z(...)) used at eval."""
    Z = T.compute_raw_Z(model,
                        Path(adj_dir) / f"{subj}_{split}_adjs{suffix}.npy",
                        Path(feat_dir) / f"{subj}_{split}_features.npy",
                        device)
    return T.flat(Z)               # [n_win, 288], RAW (no znorm)


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


def set_seed(s):
    torch.manual_seed(s); np.random.seed(s)
    torch.backends.cudnn.deterministic = True; torch.backends.cudnn.benchmark = False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input_root", default="/kaggle/input")
    ap.add_argument("--suffix", default="_topk20")
    ap.add_argument("--out_dir", default="/kaggle/working/lstm_v3")
    ap.add_argument("--epochs", type=int, default=200)     # PREREG_02 §2 registered schedule
    ap.add_argument("--batch", type=int, default=64)       # PREREG_02 §2 (was 256 in round-1)
    ap.add_argument("--seeds", type=int, nargs="+", default=[42])
    ap.add_argument("--canonical", type=int, default=42)
    a = ap.parse_args()
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)

    adj_dir = IO.find_data_dir(a.input_root, f"chb13_interictal_adjs{a.suffix}.npy")
    feat_dir = IO.find_data_dir(a.input_root, "chb13_interictal_features.npy")
    gae_ck = IO.find_ckpts(a.input_root, "gae_joint_seed")
    assert a.canonical in gae_ck, f"GAE seed-{a.canonical} not found under {a.input_root}"
    print(f"device={dev} | GAE seed-{a.canonical}={gae_ck[a.canonical][0]} | input=RAW flat-Z(288) L={L} "
          f"| epochs={a.epochs} cosine batch{a.batch} (PREREG_02 §2) | TRAIN ON RAW Z (normfix)")

    gae = G.GAEModel().to(dev)
    gsd = IO.load_state(gae_ck[a.canonical]); gae.load_state_dict(gsd.get("state_dict", gsd), strict=True); gae.eval()
    assert not (set(TRAIN_SUBJS) & set(TEST_SUBJS)) and not (set(TRAIN_SUBJS) & set(VAL_SUBJS)), "LEAK"

    print("Extracting RAW flat-Z embeddings ...")
    emb = {}
    for s in TRAIN_SUBJS:
        emb[(s, "interictal")] = embed(gae, adj_dir, feat_dir, s, "interictal", a.suffix, dev)
    for s in VAL_SUBJS:
        for sp in ["interictal", "ictal"]:
            emb[(s, sp)] = embed(gae, adj_dir, feat_dir, s, sp, a.suffix, dev)

    for seed in a.seeds:
        print(f"\n=== SEED {seed} ===")
        set_seed(seed)
        tr = [emb[(s, "interictal")] for s in TRAIN_SUBJS]          # RAW (no znorm)
        g = torch.Generator().manual_seed(seed)
        dl = DataLoader(SeqDS(tr), batch_size=a.batch, shuffle=True, generator=g)
        lstm = T.LSTMPredictor(in_dim=D).to(dev)                    # canonical class
        opt = torch.optim.Adam(lstm.parameters(), lr=1e-3); lf = nn.MSELoss()
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=a.epochs)   # PREREG_02 §2
        for ep in range(a.epochs):
            lstm.train(); tot = 0; nb = 0
            for ctx, tgt in dl:
                ctx = ctx.to(dev); tgt = tgt.to(dev)
                opt.zero_grad(); loss = lf(lstm(ctx), tgt); loss.backward(); opt.step()
                tot += loss.item(); nb += 1
            sched.step()
            if ep == 0 or (ep + 1) % 10 == 0:
                print(f"  epoch {ep+1}/{a.epochs} train_mse={tot/nb:.4f} lr={sched.get_last_lr()[0]:.2e}")
        torch.save(lstm.state_dict(), out / f"lstm_temporal_seed{seed}.pt")

        # sanity: VAL standalone AUROC scored the SAME way the pipeline scores (raw Z)
        vaucs = []
        for s in VAL_SUBJS:
            ri = T.score_full_array(lstm, emb[(s, "interictal")], L, dev)
            rc = T.score_full_array(lstm, emb[(s, "ictal")], L, dev)
            vi, vc = ri[~np.isnan(ri)], rc[~np.isnan(rc)]
            vaucs.append(roc_auc_score(np.r_[np.zeros(len(vi)), np.ones(len(vc))], np.r_[vi, vc]))
        print(f"  [seed {seed}] VAL standalone AUROC (raw-Z scoring) = {np.mean(vaucs):.4f}  "
              f"per-subj {[round(float(x),3) for x in vaucs]}")
        print(f"  saved -> {out / f'lstm_temporal_seed{seed}.pt'}")

    print("\nDONE. Next: build_ens.py (equal weight) -> score_ens.py on Cursor. Collect ALL .pt to Cursor.")


if __name__ == "__main__":
    main()