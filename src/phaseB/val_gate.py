"""
val_gate.py — clean VAL-only representation gate for any GAE upgrade (S2/S5/...).

Computes the GAE-reconstruction branch window AUROC + AUPRC (interictal vs ictal) on the
3 held-out VAL subjects (chb10, chb11, chb22). This is the ONLY iteration gate for GAE
graph/feature/objective changes.

INTEGRITY: the 8 TEST subjects (chb03,06,13,14,15,16,17,18) are NEVER scored here — a hard
guard aborts if any is passed. TEST is touched once, at the final integrated one-shot test.
chb06/chb14 are the *motivation* for S2, not the gate.

Model forward reuses gae_joint.score_windows (already byte-validated) unchanged.

Usage (Kaggle):
    # baseline A/B reference (run once):
    python val_gate.py --ckpt <baseline gae_joint_seed42.pt> --suffix _topk20
    # an upgrade (e.g. S5 multiband):
    python val_gate.py --ckpt /kaggle/working/gae_mb/gae_joint_seed42.pt --suffix _multiband_topk20
"""
import argparse
import importlib
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import roc_auc_score, average_precision_score

# G (the scorer module) is selected at runtime via --gae_module:
#   gae_joint      -> baseline / S5 multiband (fixed graph)
#   gae_joint_gsl  -> S2 learned-graph variant
# All must expose: load_checkpoint(ckpt, device), score_windows(model, adj, feat, device, batch)

VAL_SUBJS = ["chb10", "chb11", "chb22"]
TEST_SUBJS = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}


def subj_auc(G, model, adj_dir, feat_dir, subj, suffix, device, batch):
    si = G.score_windows(model, Path(adj_dir) / f"{subj}_interictal_adjs{suffix}.npy",
                         Path(feat_dir) / f"{subj}_interictal_features.npy", device, batch)
    sc = G.score_windows(model, Path(adj_dir) / f"{subj}_ictal_adjs{suffix}.npy",
                         Path(feat_dir) / f"{subj}_ictal_features.npy", device, batch)
    y = np.r_[np.zeros(len(si)), np.ones(len(sc))]
    s = np.r_[si, sc]
    return roc_auc_score(y, s), average_precision_score(y, s), len(si), len(sc)


def main():
    ap = argparse.ArgumentParser()
    base = "/kaggle/input/datasets/nhn2mm"
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--adj_dir", default=f"{base}/chbmit-topk20")
    ap.add_argument("--feat_dir", default=f"{base}/chbmit-processed")
    ap.add_argument("--suffix", default="_topk20")
    ap.add_argument("--gae_module", default="gae_joint",
                    help="scorer module: gae_joint (baseline/S5) or gae_joint_gsl (S2)")
    ap.add_argument("--subjs", nargs="+", default=VAL_SUBJS)
    ap.add_argument("--batch", type=int, default=512)
    a = ap.parse_args()

    leak = [s for s in a.subjs if s in TEST_SUBJS]
    if leak:
        raise SystemExit(f"INTEGRITY ABORT: TEST subject(s) {leak} passed to val_gate. "
                         "TEST is scored once at the final one-shot test, never as a gate.")

    G = importlib.import_module(a.gae_module)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = G.load_checkpoint(a.ckpt, device)
    print(f"module={a.gae_module}  ckpt={Path(a.ckpt).name}  suffix={a.suffix}  device={device}\n")

    aucs, aps = [], []
    print(f"{'subj':8}{'AUROC':>8}{'AUPRC':>8}{'n_int':>8}{'n_ict':>8}")
    for s in a.subjs:
        auc, ap_, ni, nc = subj_auc(G, model, a.adj_dir, a.feat_dir, s, a.suffix, device, a.batch)
        aucs.append(auc); aps.append(ap_)
        print(f"{s:8}{auc:8.4f}{ap_:8.4f}{ni:8d}{nc:8d}")
    print(f"\n{'MACRO':8}{np.mean(aucs):8.4f}{np.mean(aps):8.4f}")
    print("\nGATE = GAE-recon branch only. KEEP iff macro AUROC & AUPRC >= baseline "
          "(same cmd, baseline ckpt + _topk20) and no VAL subject regresses hard.")


if __name__ == "__main__":
    main()
