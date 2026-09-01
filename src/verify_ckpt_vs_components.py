#!/usr/bin/env python
"""verify_ckpt_vs_components.py — which checkpoint reproduces the COMMITTED zrecon
components of the one-shot TEST? Read-only diagnostic, writes nothing.

zrecon on disk is robust-z'd (affine, per subject) => Pearson corr against the raw
recon score is the correct test: the true checkpoint gives corr = 1.000000."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB"):
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

import numpy as np, torch
from gae_joint import load_checkpoint, score_windows

PROC = ROOT / "data" / "processed"
COMP = ROOT / "results" / "phaseB" / "tier2" / "ens_test_tf" / "components"
SUBJ = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
CANDS = [ROOT / "data" / "models" / "best_model_joint_lambda01.pt",
         ROOT / "data" / "models_retrain" / "gae_joint_seed42.pt"]
dev = torch.device("cpu")

found = sorted(COMP.glob("zrecon_*"))
if not found:
    print(f"[FATAL] no zrecon_* in {COMP}\nfiles present: {sorted(p.name for p in COMP.iterdir())[:6]}")
    sys.exit(1)
print(f"found {len(found)} committed zrecon arrays, e.g. {found[0].name}\n")

for ck in CANDS:
    if not ck.is_file():
        print(f"{ck.name}: MISSING"); continue
    m = load_checkpoint(ck, dev)
    print(f"--- {ck.relative_to(ROOT)}  bias_fp={m.encoder.conv1.bias.abs().max():.4f}")
    worst = 1.0
    for s in SUBJ:
        for split, tag in [("interictal", "inter"), ("ictal", "ictal")]:
            f = COMP / f"zrecon_{s}_{tag}.npy"
            if not f.is_file():
                print(f"   {s}_{tag:<6} committed file absent"); continue
            ref = np.load(f).ravel()
            mine = score_windows(m, PROC / f"{s}_{split}_adjs_topk20.npy",
                                 PROC / f"{s}_{split}_features.npy", dev, 256).ravel()
            if len(ref) != len(mine):
                print(f"   {s}_{tag:<6} LEN {len(ref)} vs {len(mine)}"); worst = 0.0; continue
            r = float(np.corrcoef(ref, mine)[0, 1])
            worst = min(worst, r)
            print(f"   {s}_{tag:<6} n={len(ref):<6} corr={r:.7f}")
    print(f"   >>> WORST corr = {worst:.7f}\n")