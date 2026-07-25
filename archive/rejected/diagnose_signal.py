"""
diagnose_signal.py
==================
Diagnose whether the signal exists in adjacency matrices BEFORE
trying to fix the model. If adjacency matrices for ictal vs interictal
are not meaningfully different, no model will achieve AUROC > 0.5.

Checks performed:
  1. NaN / Inf counts in adjacency matrices (all subjects)
  2. Mean adjacency values: interictal vs ictal (chb01)
  3. Frobenius distance: ictal vs interictal mean
  4. Edge count distribution: ictal vs interictal
  5. Per-window reconstruction error using MEAN interictal adj as template
     (oracle test — if this AUROC < 0.6, signal is too weak)
  6. Band power features: interictal vs ictal mean (chb01)

Run from src/:
    python diagnose_signal.py
"""

import sys
import numpy as np
from pathlib import Path
from scipy.stats import mannwhitneyu

PROCESSED_DIR = Path("F:/Study/Thesis/Code/data/processed")
SUBJECTS = [f"chb{i:02d}" for i in range(1, 24)]

# ─────────────────────────────────────────────────────────────────────────────
# 1. NaN / Inf scan — ALL subjects
# ─────────────────────────────────────────────────────────────────────────────

def check_nan_all():
    print("=" * 65)
    print("CHECK 1: NaN / Inf in adjacency matrices (all subjects)")
    print("=" * 65)

    total_nan_subjects = []
    for subj in SUBJECTS:
        inter_path = PROCESSED_DIR / f"{subj}_interictal_adjs.npy"
        ictal_path  = PROCESSED_DIR / f"{subj}_ictal_adjs.npy"
        if not inter_path.exists():
            print(f"  {subj}: MISSING _adjs.npy — skip")
            continue

        adjs = np.load(str(inter_path), mmap_mode="r")
        n_nan = int(np.isnan(adjs).sum())
        n_inf = int(np.isinf(adjs).sum())

        flag = ""
        if n_nan > 0 or n_inf > 0:
            flag = "  *** WARNING ***"
            total_nan_subjects.append(subj)

        print(f"  {subj}: interictal shape={adjs.shape}  "
              f"NaN={n_nan}  Inf={n_inf}{flag}")

        if ictal_path.exists():
            adjs_i = np.load(str(ictal_path), mmap_mode="r")
            n_nan_i = int(np.isnan(adjs_i).sum())
            n_inf_i = int(np.isinf(adjs_i).sum())
            if n_nan_i > 0 or n_inf_i > 0:
                print(f"  {subj}: ictal NaN={n_nan_i}  Inf={n_inf_i}  *** WARNING ***")
                if subj not in total_nan_subjects:
                    total_nan_subjects.append(subj)

    if total_nan_subjects:
        print(f"\n  Subjects with NaN/Inf: {total_nan_subjects}")
        print("  ACTION: NaN in adjacency = broken signal. Fix graph_construction.py.")
    else:
        print("\n  No NaN/Inf found — adjacency matrices are clean.")
    return total_nan_subjects


# ─────────────────────────────────────────────────────────────────────────────
# 2. Signal check — chb01 mean adjacency comparison
# ─────────────────────────────────────────────────────────────────────────────

def check_signal_chb01():
    print("\n" + "=" * 65)
    print("CHECK 2: Mean adjacency — interictal vs ictal (chb01)")
    print("=" * 65)

    inter_adjs = np.load(
        str(PROCESSED_DIR / "chb01_interictal_adjs.npy"), mmap_mode="r")
    ictal_adjs = np.load(
        str(PROCESSED_DIR / "chb01_ictal_adjs.npy"), mmap_mode="r")

    A_inter_mean = inter_adjs.mean(axis=0)  # [18, 18]
    A_ictal_mean = ictal_adjs.mean(axis=0)  # [18, 18]

    print(f"  Interictal: {len(inter_adjs)} windows")
    print(f"  Ictal:      {len(ictal_adjs)} windows")

    print(f"\n  Mean adjacency value:")
    print(f"    Interictal: {A_inter_mean.mean():.4f}  "
          f"(std={A_inter_mean.std():.4f}  "
          f"max={A_inter_mean.max():.4f})")
    print(f"    Ictal:      {A_ictal_mean.mean():.4f}  "
          f"(std={A_ictal_mean.std():.4f}  "
          f"max={A_ictal_mean.max():.4f})")

    # Frobenius distance between class means
    frob = np.linalg.norm(A_inter_mean - A_ictal_mean, 'fro')
    frob_self = np.linalg.norm(A_inter_mean, 'fro')
    print(f"\n  Frobenius distance (ictal_mean vs inter_mean): {frob:.4f}")
    print(f"  Frobenius norm of inter_mean:                  {frob_self:.4f}")
    print(f"  Relative difference:                           {frob/frob_self:.4f}")

    if frob / frob_self < 0.05:
        print("  WARNING: ictal and interictal adjacency means are nearly identical.")
        print("  This means the graph signal may be too weak for GAE detection.")
    elif frob / frob_self > 0.15:
        print("  GOOD: clear difference between ictal and interictal mean adjacency.")
    else:
        print("  MODERATE: some difference — signal may be detectable with good model.")

    # Edge count comparison
    inter_edges = (inter_adjs > 0).sum(axis=(1, 2))
    ictal_edges  = (ictal_adjs  > 0).sum(axis=(1, 2))
    print(f"\n  Edge count per window:")
    print(f"    Interictal: mean={inter_edges.mean():.1f}  "
          f"std={inter_edges.std():.1f}  "
          f"min={inter_edges.min()}  max={inter_edges.max()}")
    print(f"    Ictal:      mean={ictal_edges.mean():.1f}  "
          f"std={ictal_edges.std():.1f}  "
          f"min={ictal_edges.min()}  max={ictal_edges.max()}")

    return A_inter_mean, inter_adjs, ictal_adjs


# ─────────────────────────────────────────────────────────────────────────────
# 3. Oracle AUROC — using Frobenius distance from interictal MEAN
#    (bypasses model entirely — tests if signal is in adjacency at all)
# ─────────────────────────────────────────────────────────────────────────────

def oracle_auroc(A_inter_mean, inter_adjs, ictal_adjs):
    print("\n" + "=" * 65)
    print("CHECK 3: Oracle AUROC (no model — pure adjacency signal)")
    print("  Score = ||A_window - A_interictal_mean||_F  (WEIGHTED)")
    print("  If this AUROC < 0.60: signal too weak, model cannot help.")
    print("  If this AUROC > 0.70: signal exists, model training issue.")
    print("=" * 65)

    # Use WEIGHTED adjacency — signal is in connectivity strength, not binary
    # Binary adjacency loses the wPLI weight difference (0.23 vs 0.35)
    scores_inter = []
    for i in range(len(inter_adjs)):
        scores_inter.append(
            np.linalg.norm(inter_adjs[i].astype(np.float32) - A_inter_mean, 'fro')
        )

    scores_ictal = []
    for i in range(len(ictal_adjs)):
        scores_ictal.append(
            np.linalg.norm(ictal_adjs[i].astype(np.float32) - A_inter_mean, 'fro')
        )

    scores_inter = np.array(scores_inter)
    scores_ictal  = np.array(scores_ictal)

    print(f"\n  Reconstruction error (weighted, vs interictal mean):")
    print(f"    Interictal: mean={scores_inter.mean():.3f}  "
          f"std={scores_inter.std():.3f}  p95={np.percentile(scores_inter, 95):.3f}")
    print(f"    Ictal:      mean={scores_ictal.mean():.3f}  "
          f"std={scores_ictal.std():.3f}  p95={np.percentile(scores_ictal, 95):.3f}")

    stat, pval = mannwhitneyu(
        scores_ictal, scores_inter, alternative="greater")
    print(f"\n  Mann-Whitney U (ictal > interictal): "
          f"U={stat:.0f}  p={pval:.4f}")
    if pval < 0.05:
        print("  GOOD: ictal scores significantly higher (p<0.05)")
    else:
        print("  WARNING: not significant")

    n_pos = len(scores_ictal)
    n_neg = len(scores_inter)
    rank_sum = sum(
        (scores_inter < s).sum() + 0.5 * (scores_inter == s).sum()
        for s in scores_ictal
    )
    auroc = rank_sum / (n_pos * n_neg)

    print(f"\n  Oracle AUROC: {auroc:.4f}")
    if auroc > 0.70:
        print("  VERDICT: Signal EXISTS. Problem is in model training.")
    elif auroc > 0.55:
        print("  VERDICT: Weak signal. May improve with better training.")
    else:
        print("  VERDICT: Signal weak or absent.")

    return auroc, scores_inter, scores_ictal


# ─────────────────────────────────────────────────────────────────────────────
# 4. Feature check — band powers interictal vs ictal
# ─────────────────────────────────────────────────────────────────────────────

def check_features_chb01():
    print("\n" + "=" * 65)
    print("CHECK 4: Band power features — interictal vs ictal (chb01)")
    print("  Bands: delta theta alpha beta gamma")
    print("=" * 65)

    inter_feat = np.load(
        str(PROCESSED_DIR / "chb01_interictal_features.npy"), mmap_mode="r")
    ictal_feat  = np.load(
        str(PROCESSED_DIR / "chb01_ictal_features.npy"), mmap_mode="r")

    band_names = ["delta", "theta", "alpha", "beta ", "gamma"]

    print(f"\n  Mean band power across all channels:")
    print(f"  {'Band':<8} {'Interictal':>15} {'Ictal':>15} {'Ratio':>10}")
    print(f"  {'-'*50}")

    for i, band in enumerate(band_names):
        inter_mean = inter_feat[:, :, i].mean()
        ictal_mean  = ictal_feat[:, :, i].mean()
        ratio = ictal_mean / (inter_mean + 1e-10)
        flag = "  <-- HIGH" if ratio > 2.0 or ratio < 0.5 else ""
        print(f"  {band:<8} {inter_mean:>15.6f} {ictal_mean:>15.6f} "
              f"{ratio:>10.3f}{flag}")

    # NaN check
    n_nan_inter = int(np.isnan(inter_feat).sum())
    n_nan_ictal  = int(np.isnan(ictal_feat).sum())
    print(f"\n  NaN in features: interictal={n_nan_inter}  ictal={n_nan_ictal}")
    if n_nan_inter > 0 or n_nan_ictal > 0:
        print("  WARNING: NaN in features — will corrupt model training.")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Percentile threshold scan (oracle)
# ─────────────────────────────────────────────────────────────────────────────

def threshold_scan(scores_inter, scores_ictal):
    print("\n" + "=" * 65)
    print("CHECK 5: Threshold scan (oracle, chb01)")
    print(f"  {'Percentile':>12} {'Threshold':>12} {'Sensitivity':>13} "
          f"{'Specificity':>13} {'FDR_windows/h':>15}")
    print("  " + "-" * 70)

    total_inter_hours = len(scores_inter) * 4 / 3600  # 4s windows

    for pct in [85, 90, 95, 97, 99]:
        tau = np.percentile(scores_inter, pct)
        tp = int((scores_ictal >= tau).sum())
        fn = int((scores_ictal < tau).sum())
        fp = int((scores_inter >= tau).sum())
        tn = int((scores_inter < tau).sum())

        sens = tp / (tp + fn + 1e-8)
        spec = tn / (tn + fp + 1e-8)
        fdr_windows = fp / total_inter_hours  # window-level (not event-level)

        print(f"  {pct:>12}% {tau:>12.4f} {sens:>13.4f} "
              f"{spec:>13.4f} {fdr_windows:>15.2f}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", default="chb01")
    args = parser.parse_args()

    SUBJ = args.subject
    print(f"\nDIAGNOSTIC REPORT — {SUBJ}\n")

    # Patch paths for chosen subject
    inter_adjs_path = PROCESSED_DIR / f"{SUBJ}_interictal_adjs.npy"
    ictal_adjs_path  = PROCESSED_DIR / f"{SUBJ}_ictal_adjs.npy"
    inter_feat_path  = PROCESSED_DIR / f"{SUBJ}_interictal_features.npy"
    ictal_feat_path  = PROCESSED_DIR / f"{SUBJ}_ictal_features.npy"

    nan_subjects = check_nan_all()

    inter_adjs = np.load(str(inter_adjs_path), mmap_mode="r")
    ictal_adjs  = np.load(str(ictal_adjs_path),  mmap_mode="r")
    A_inter_mean = inter_adjs.mean(axis=0)

    print(f"\n{'='*65}")
    print(f"CHECK 2: {SUBJ}  interictal={len(inter_adjs)}  ictal={len(ictal_adjs)}")
    print(f"{'='*65}")
    print(f"  Mean adj: inter={inter_adjs.mean():.4f}  ictal={ictal_adjs.mean():.4f}")
    frob = np.linalg.norm(A_inter_mean - ictal_adjs.mean(axis=0), 'fro')
    frob_self = np.linalg.norm(A_inter_mean, 'fro')
    print(f"  Frobenius relative diff: {frob/frob_self:.4f}")
    inter_edges = (inter_adjs > 0).sum(axis=(1,2))
    ictal_edges  = (ictal_adjs  > 0).sum(axis=(1,2))
    print(f"  Edge count: inter={inter_edges.mean():.1f}±{inter_edges.std():.1f}  "
          f"ictal={ictal_edges.mean():.1f}±{ictal_edges.std():.1f}")

    auroc, scores_inter, scores_ictal = oracle_auroc(
        A_inter_mean, inter_adjs, ictal_adjs)
    threshold_scan(scores_inter, scores_ictal)

    print(f"\nSUMMARY: {SUBJ}  Oracle AUROC={auroc:.4f}")