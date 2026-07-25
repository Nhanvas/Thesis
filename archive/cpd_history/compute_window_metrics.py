"""
compute_window_metrics.py — Window-level precision, recall, F1, specificity
Uses per-subject P95 interictal threshold (fully unsupervised, no val labels).
Reads cached bidirectional gamma ensemble scores.
Usage: python src/compute_window_metrics.py
"""

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import (roc_auc_score, precision_score,
                             recall_score, f1_score, confusion_matrix)

SCORES_DIR  = Path("results/cpd/scores")
RESULTS_DIR = Path("results/cpd")
TEST_SUBJS  = ["chb03","chb06","chb13","chb14","chb15","chb16","chb17","chb18"]

def compute_metrics(ens_inter, ens_ictal, percentile=95):
    """
    Threshold: P{percentile} of interictal scores (per-subject, unsupervised).
    Returns dict of all window-level metrics.
    """
    tau = np.percentile(ens_inter, percentile)

    y_true  = np.concatenate([np.zeros(len(ens_inter)), np.ones(len(ens_ictal))])
    scores  = np.concatenate([ens_inter, ens_ictal])
    y_pred  = (scores >= tau).astype(int)

    auroc       = roc_auc_score(y_true, scores)
    sensitivity = recall_score(y_true, y_pred, zero_division=0)      # TPR
    precision   = precision_score(y_true, y_pred, zero_division=0)
    f1          = f1_score(y_true, y_pred, zero_division=0)

    tn,fp,fn,tp = confusion_matrix(y_true, y_pred, labels=[0,1]).ravel()
    specificity  = tn / (tn+fp) if (tn+fp)>0 else 0.0
    fpr          = fp / (tn+fp) if (tn+fp)>0 else 0.0  # = 1-specificity = FPR at threshold

    n_inter  = len(ens_inter)
    n_ictal  = len(ens_ictal)
    prev     = n_ictal / (n_inter + n_ictal)  # seizure prevalence (window-level)

    return {
        'tau': round(float(tau), 4),
        'auroc': round(auroc, 4),
        'sensitivity': round(sensitivity, 4),
        'specificity': round(specificity, 4),
        'precision': round(precision, 4),
        'f1': round(f1, 4),
        'fpr': round(fpr, 4),
        'n_inter': n_inter, 'n_ictal': n_ictal,
        'prevalence_pct': round(prev*100, 3),
        'tp_windows': int(tp), 'fn_windows': int(fn),
        'fp_windows': int(fp), 'tn_windows': int(tn),
    }

def main():
    print("="*65)
    print("WINDOW-LEVEL METRICS — P95 Interictal Threshold (Unsupervised)")
    print("="*65)

    rows = []
    for subj in TEST_SUBJS:
        ens_i = np.load(str(SCORES_DIR / f"{subj}_ens_inter.npy"))
        ens_c = np.load(str(SCORES_DIR / f"{subj}_ens_ictal.npy"))
        m = compute_metrics(ens_i, ens_c, percentile=95)
        rows.append({'subject': subj, **m})

        print(f"\n  {subj}  "
              f"({m['n_inter']:,} inter | {m['n_ictal']:,} ictal | "
              f"prevalence={m['prevalence_pct']:.3f}%)")
        print(f"    tau (P95)   = {m['tau']:.4f}")
        print(f"    AUROC       = {m['auroc']:.4f}")
        print(f"    Sensitivity = {m['sensitivity']:.4f}  "
              f"({m['tp_windows']} TP / {m['tp_windows']+m['fn_windows']} ictal windows)")
        print(f"    Specificity = {m['specificity']:.4f}  "
              f"(FPR = {m['fpr']:.4f})")
        print(f"    Precision   = {m['precision']:.4f}  "
              f"[low expected due to {m['prevalence_pct']:.3f}% prevalence]")
        print(f"    F1 score    = {m['f1']:.4f}")

    # ── Macro averages ────────────────────────────────────────────────────────
    df = pd.DataFrame(rows)
    macro = df[['auroc','sensitivity','specificity','precision','f1']].mean()

    print(f"\n{'='*65}")
    print("MACRO (mean across 8 subjects)")
    print(f"  AUROC       : {macro['auroc']:.4f}")
    print(f"  Sensitivity : {macro['sensitivity']:.4f}")
    print(f"  Specificity : {macro['specificity']:.4f}")
    print(f"  Precision   : {macro['precision']:.4f}  (dominated by class imbalance)")
    print(f"  F1          : {macro['f1']:.4f}  (dominated by class imbalance)")

    print(f"\n  NOTE: Precision and F1 are low by construction (~0.18% window prevalence).")
    print(f"  Report AUROC and Sensitivity+Specificity as primary window-level metrics.")
    print(f"  F1 is reported for completeness but not the appropriate primary metric.")

    # ── Save ─────────────────────────────────────────────────────────────────
    out = RESULTS_DIR / "window_metrics.csv"
    df.to_csv(str(out), index=False)
    print(f"\nCSV saved: {out}")

if __name__ == "__main__":
    main()