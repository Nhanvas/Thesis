# verify_spli.py — chạy local sau khi build_spli.py xong
import numpy as np
from pathlib import Path

DATA_DIR   = Path("data/processed")
TEST_SUBJS = ["chb03","chb06","chb13","chb14","chb15","chb16","chb17","chb18"]

print(f"{'Subj':<6} {'density':>8} {'mean_inter':>11} {'mean_ictal':>11} {'direction':>10}")
print("-" * 54)

for subj in TEST_SUBJS:
    Ai = np.load(DATA_DIR / f"{subj}_interictal_adjs_spli_topk20.npy")
    Ac = np.load(DATA_DIR / f"{subj}_ictal_adjs_spli_topk20.npy")
    
    density   = float((np.abs(Ai) > 0).mean())
    mean_inter = float(np.abs(Ai).mean())
    mean_ictal = float(np.abs(Ac).mean())
    direction = "correct" if mean_ictal > mean_inter else "inverted"
    
    print(f"{subj:<6} {density:>8.4f} {mean_inter:>11.5f} {mean_ictal:>11.5f} {direction:>10}")