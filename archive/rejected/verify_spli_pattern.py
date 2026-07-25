# src/verify_spli_pattern.py
import numpy as np
from pathlib import Path

DATA_DIR   = Path("data/processed")
TEST_SUBJS = ["chb03","chb06","chb13","chb14","chb15","chb16","chb17","chb18"]
TRIU       = np.triu_indices(18, k=1)   # 153 upper-triangle pairs


def analyze_pattern(subj):
    Ai = np.load(DATA_DIR / f"{subj}_interictal_adjs_spli_topk20.npy")
    Ac = np.load(DATA_DIR / f"{subj}_ictal_adjs_spli_topk20.npy")

    # Mean signed sPLI pattern per edge across all windows
    mean_inter = Ai[:, TRIU[0], TRIU[1]].mean(axis=0)   # [153]
    mean_ictal = Ac[:, TRIU[0], TRIU[1]].mean(axis=0)   # [153]

    # Metric 1: Pearson correlation of mean patterns
    # High corr = same edges dominant, same signs → E_DIRECTED unlikely to help
    # Low corr  = patterns differ → E_DIRECTED can detect this
    pattern_corr = float(np.corrcoef(mean_inter, mean_ictal)[0, 1])

    # Metric 2: Sign flip rate — fraction of edges where dominant sign FLIPS
    inter_sign = np.sign(mean_inter)
    ictal_sign = np.sign(mean_ictal)
    sign_flip  = float((inter_sign != ictal_sign).mean())

    # Metric 3: Which edges are the top-5 in each condition?
    top5_inter = set(np.argsort(np.abs(mean_inter))[-5:])
    top5_ictal = set(np.argsort(np.abs(mean_ictal))[-5:])
    top5_overlap = len(top5_inter & top5_ictal) / 5.0   # 1.0 = same 5 edges

    # Magnitude ratio (already known, included for reference)
    mag_ratio = float(np.abs(mean_ictal).mean() / (np.abs(mean_inter).mean() + 1e-9))

    return pattern_corr, sign_flip, top5_overlap, mag_ratio


print(f"{'Subj':<6} {'PatternCorr':>12} {'SignFlip%':>10} {'Top5Overlap':>12} {'MagRatio':>10}")
print("-" * 58)

for subj in TEST_SUBJS:
    pc, sf, ov, mr = analyze_pattern(subj)
    print(f"{subj:<6} {pc:>12.4f} {sf*100:>9.1f}% {ov:>12.2f} {mr:>10.4f}")

print("""
Decision criteria for chb06:
  PatternCorr < 0.80 → pattern changes significantly → E_DIRECTED PROCEED
  PatternCorr > 0.95 → pattern barely changes → E_DIRECTED unlikely to help
  SignFlip%   > 25%  → directional changes strong → E_DIRECTED PROCEED
  Top5Overlap < 0.4  → dominant edges completely different → E_DIRECTED PROCEED
""")