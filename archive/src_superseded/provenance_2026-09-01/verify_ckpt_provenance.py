#!/usr/bin/env python
"""verify_ckpt_provenance.py — which checkpoint reproduces RoR S7 chb13 recon AUROC = 0.836?
Read-only diagnostic. No outputs written."""
import hashlib, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain"):
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

import numpy as np, torch
from sklearn.metrics import roc_auc_score
from gae_joint import load_checkpoint, score_windows

PROC = ROOT / "data" / "processed"
dev = torch.device("cpu")
cands = sorted(set(list((ROOT / "data" / "models_retrain").rglob("*.pt"))
                   + list(ROOT.rglob("*.pt"))))
cands = [c for c in cands if ".git" not in c.parts]

print(f"{'file':<58} {'size':>7} {'bias_fp':>8} {'sha8':>10} {'chb13_AUROC':>12}")
for c in cands:
    sha = hashlib.sha256(c.read_bytes()).hexdigest()[:8]
    try:
        m = load_checkpoint(c, dev)
        bf = m.encoder.conv1.bias.abs().max().item()
        si = score_windows(m, PROC / "chb13_interictal_adjs_topk20.npy",
                           PROC / "chb13_interictal_features.npy", dev, 256)
        sc = score_windows(m, PROC / "chb13_ictal_adjs_topk20.npy",
                           PROC / "chb13_ictal_features.npy", dev, 256)
        y = np.r_[np.zeros(len(si)), np.ones(len(sc))]
        auc = f"{roc_auc_score(y, np.r_[si, sc]):.4f}"
    except Exception as e:
        bf, auc = float("nan"), f"LOAD_FAIL({type(e).__name__})"
    print(f"{str(c.relative_to(ROOT)):<58} {c.stat().st_size:>7} {bf:>8.4f} {sha:>10} {auc:>12}")