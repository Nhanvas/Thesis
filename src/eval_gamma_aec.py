# src/eval_gamma_aec.py
import numpy as np
from pathlib import Path
from sklearn.metrics import roc_auc_score

DATA_DIR   = Path("data/processed")
TEST_SUBJS = ["chb03","chb06","chb13","chb14","chb15","chb16","chb17","chb18"]

# Reference từ v10 log
WPLI_TTA_AUROC = {"chb03":0.6783,"chb06":0.3134,"chb13":0.8482,"chb14":0.6786,
                   "chb15":0.8117,"chb16":0.6694,"chb17":0.6059,"chb18":0.8897}

print(f"{'Subj':<6} {'AUROC_gamma':>12} {'mzi':>8} {'n_inter':>8} {'n_ictal':>8} "
      f"{'vs_wPLI_TTA':>13}")
print("-" * 68)

aurocs = {}
for subj in TEST_SUBJS:
    zi   = np.load(str(DATA_DIR / f"gamma_aec_{subj}_inter.npy"))
    zc   = np.load(str(DATA_DIR / f"gamma_aec_{subj}_ictal.npy"))
    y    = np.concatenate([np.zeros(len(zi)), np.ones(len(zc))])
    auroc = roc_auc_score(y, np.concatenate([zi, zc]))
    mzi  = float(np.median(zc))
    delta = auroc - WPLI_TTA_AUROC[subj]
    aurocs[subj] = auroc
    print(f"{subj:<6} {auroc:>12.4f} {mzi:>8.4f} {len(zi):>8} {len(zc):>8} "
          f"{delta:>+13.4f}")

macro_gamma = np.mean(list(aurocs.values()))
macro_wpli  = np.mean(list(WPLI_TTA_AUROC.values()))
print("-" * 68)
print(f"{'MACRO':<6} {macro_gamma:>12.4f} {'':>8} {'':>8} {'':>8} "
      f"{macro_gamma - macro_wpli:>+13.4f}")
print(f"\nReference: wPLI+TTA macro = {macro_wpli:.4f}")
print(f"Reference: Ensemble best = 0.7320")