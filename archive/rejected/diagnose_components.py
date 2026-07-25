"""
diagnose_components.py
======================
Diagnose whether AEC or wPLI individually carries the ictal signal.

Hypothesis: wPLI suppresses zero-lag synchrony. During seizures,
high-amplitude rhythmic activity IS zero-lag. So wPLI may DECREASE
during seizures while AEC INCREASES. Combined wPLI+AEC may cancel out.

This script computes Oracle AUROC for:
  1. AEC-only adjacency
  2. wPLI-only adjacency
  3. Combined (current)
  4. AEC-only with NO threshold (full matrix)

Run from src/:
    python diagnose_components.py --subject chb01
    python diagnose_components.py --subject chb12
"""

import sys
import argparse
import numpy as np
from pathlib import Path
from scipy.signal import hilbert

PROCESSED_DIR = Path("F:/Study/Thesis/Code/data/processed")
FS = 256
FIXED_THRESHOLD = 0.05


# ── Connectivity functions (recompute from raw windows) ───────────────────────

def apply_car(w):
    return w - np.mean(w, axis=0, keepdims=True)


def compute_wpli(w, fs=256):
    n = w.shape[0]
    out = np.zeros((n, n))
    fft = np.fft.rfft(w, axis=1)
    for i in range(n):
        for j in range(i+1, n):
            cross = fft[i] * np.conj(fft[j])
            im    = np.imag(cross)
            val   = np.abs(np.mean(im)) / (np.mean(np.abs(im)) + 1e-8)
            out[i, j] = out[j, i] = val
    return out


def compute_aec(w):
    env = np.abs(hilbert(w, axis=1))
    aec = np.corrcoef(env)
    np.fill_diagonal(aec, 0.0)
    return np.abs(np.nan_to_num(aec, nan=0.0))


def threshold(A, t=FIXED_THRESHOLD):
    A2 = np.where(A >= t, A, 0.0)
    np.fill_diagonal(A2, 0.0)
    return A2


def oracle_auroc(scores_inter, scores_ictal, label=""):
    """Compute AUROC: P(score_ictal > score_inter)."""
    n_pos = len(scores_ictal)
    n_neg = len(scores_inter)
    rank_sum = 0
    for s in scores_ictal:
        rank_sum += (scores_inter < s).sum() + 0.5*(scores_inter == s).sum()
    auroc = rank_sum / (n_pos * n_neg)

    from scipy.stats import mannwhitneyu
    _, pval = mannwhitneyu(scores_ictal, scores_inter, alternative="greater")

    direction = "ictal > inter" if scores_ictal.mean() > scores_inter.mean() \
                else "ictal < inter (WRONG DIRECTION)"
    print(f"  {label:<30}  AUROC={auroc:.4f}  p={pval:.4f}  "
          f"| inter_mean={scores_inter.mean():.3f}  "
          f"ictal_mean={scores_ictal.mean():.3f}  [{direction}]")
    return auroc


def run_subject(subject_id: str, n_sample_inter: int = 500,
                n_sample_ictal: int = None):
    """
    Recompute adjacency from raw windows using different metrics.
    Uses a random sample of interictal windows for speed.
    """
    inter_path = PROCESSED_DIR / f"{subject_id}_interictal.npy"
    ictal_path  = PROCESSED_DIR / f"{subject_id}_ictal.npy"

    if not inter_path.exists():
        print(f"  Missing {inter_path} — skip")
        return

    inter_windows = np.load(str(inter_path), mmap_mode="r")
    ictal_windows  = np.load(str(ictal_path),  mmap_mode="r")

    # Sample interictal to speed up computation
    n_inter = min(n_sample_inter, len(inter_windows))
    n_ictal  = len(ictal_windows) if n_sample_ictal is None \
               else min(n_sample_ictal, len(ictal_windows))

    rng = np.random.default_rng(42)
    inter_idx = rng.choice(len(inter_windows), n_inter, replace=False)
    ictal_idx  = rng.choice(len(ictal_windows),  n_ictal,  replace=False)

    print(f"\n  {subject_id}: sampling {n_inter} interictal + "
          f"{n_ictal} ictal windows for component analysis")
    print(f"  {'Metric':<30}  {'AUROC':>6}  {'p-value':>8}  "
          f"{'inter_mean':>12}  {'ictal_mean':>12}  direction")
    print("  " + "-" * 95)

    # Build adjacency matrices for each metric
    results = {}
    for label, use_wpli, use_aec, alpha, apply_thresh in [
        ("wPLI-only (thresh 0.05)",     True,  False, 1.0, True),
        ("AEC-only  (thresh 0.05)",     False, True,  0.0, True),
        ("wPLI+AEC  (thresh 0.05)",     True,  True,  0.5, True),
        ("AEC-only  (no threshold)",    False, True,  0.0, False),
        ("wPLI+AEC  (alpha=0.2)",       True,  True,  0.2, True),
        ("wPLI+AEC  (alpha=0.8)",       True,  True,  0.8, True),
    ]:
        scores_inter_list = []
        scores_ictal_list  = []

        # Compute mean adjacency from interictal sample
        mean_A = np.zeros((18, 18))
        for idx in inter_idx:
            w = apply_car(inter_windows[idx].astype(np.float64))
            wpli = compute_wpli(w) if use_wpli else np.zeros((18, 18))
            aec  = compute_aec(w)  if use_aec  else np.zeros((18, 18))
            A    = alpha * wpli + (1 - alpha) * aec
            if apply_thresh:
                A = threshold(A)
            mean_A += A
        mean_A /= n_inter

        # Score interictal windows
        for idx in inter_idx:
            w = apply_car(inter_windows[idx].astype(np.float64))
            wpli = compute_wpli(w) if use_wpli else np.zeros((18, 18))
            aec  = compute_aec(w)  if use_aec  else np.zeros((18, 18))
            A    = alpha * wpli + (1 - alpha) * aec
            if apply_thresh:
                A = threshold(A)
            scores_inter_list.append(np.linalg.norm(A - mean_A, 'fro'))

        # Score ictal windows
        for idx in ictal_idx:
            w = apply_car(ictal_windows[idx].astype(np.float64))
            wpli = compute_wpli(w) if use_wpli else np.zeros((18, 18))
            aec  = compute_aec(w)  if use_aec  else np.zeros((18, 18))
            A    = alpha * wpli + (1 - alpha) * aec
            if apply_thresh:
                A = threshold(A)
            scores_ictal_list.append(np.linalg.norm(A - mean_A, 'fro'))

        scores_inter = np.array(scores_inter_list)
        scores_ictal  = np.array(scores_ictal_list)

        auroc = oracle_auroc(scores_inter, scores_ictal, label=label)
        results[label] = auroc

    # Find best
    best_label = max(results, key=results.get)
    print(f"\n  Best metric: {best_label}  (AUROC={results[best_label]:.4f})")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", default="chb01",
                        help="Subject ID to diagnose. Default: chb01")
    parser.add_argument("--n_inter", type=int, default=300,
                        help="Number of interictal windows to sample. Default: 300")
    args = parser.parse_args()

    print(f"\nCOMPONENT DIAGNOSTIC — {args.subject}")
    print("=" * 65)
    print("Testing which connectivity metric carries ictal signal.\n")

    run_subject(args.subject, n_sample_inter=args.n_inter)

    print("\n" + "=" * 65)
    print("INTERPRETATION:")
    print("  AUROC > 0.65: this metric can detect seizures")
    print("  AUROC < 0.50: signal INVERTED (wrong direction)")
    print("  AUROC ~ 0.50: no signal")
    print()