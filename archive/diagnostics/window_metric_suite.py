#!/usr/bin/env python3
"""
W1 — Window-metric suite (Phase-B), per PREREG_08.

Reads per-window ensemble scores ens_seed42_{subj}_{inter,ictal}.npy.
Reports per-subject + macro AUROC, AUPRC (+ lift vs prevalence), and window
precision/recall/F1 at a VAL-derived F1-optimal threshold t* (frozen on VAL).
Sanity gate: macro AUROC must reproduce §0 window 0.775 (+/-0.01).

Usage:
  python window_metric_suite.py \
      --ens_dir results/retrain_v3p1/ens \
      --val_ens_dir results/retrain_v3p1/val_ens --seed 42
"""
import argparse, json
from pathlib import Path
import numpy as np

try:
    from sklearn.metrics import roc_auc_score, average_precision_score
except Exception:
    roc_auc_score = average_precision_score = None

TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
VAL_SUBJS  = ["chb10", "chb11", "chb22"]


def load(ens_dir, seed, subj):
    ei = np.load(Path(ens_dir) / f"ens_seed{seed}_{subj}_inter.npy").astype(float).ravel()
    ec = np.load(Path(ens_dir) / f"ens_seed{seed}_{subj}_ictal.npy").astype(float).ravel()
    y = np.concatenate([np.zeros(len(ei)), np.ones(len(ec))])
    s = np.concatenate([ei, ec])
    return y, s, len(ei), len(ec)


def prf_at(y, s, t):
    pred = (s >= t).astype(int)
    tp = int(((pred == 1) & (y == 1)).sum()); fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    prec = tp/(tp+fp) if tp+fp else 0.0
    rec = tp/(tp+fn) if tp+fn else 0.0
    f1 = 2*prec*rec/(prec+rec) if prec+rec else 0.0
    return prec, rec, f1


def val_threshold(scores, labels):
    """t* maximizing VAL window F1 (tie -> higher recall)."""
    cand = np.unique(scores)
    if len(cand) > 2000:
        cand = np.quantile(scores, np.linspace(0, 1, 2000))
    best = (-1, -1, None)  # (f1, recall, t)
    for t in cand:
        p, r, f = prf_at(labels, scores, t)
        if (f, r) > (best[0], best[1]):
            best = (f, r, t)
    return best[2], best[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ens_dir", default="results/retrain_v3p1/ens")
    ap.add_argument("--val_ens_dir", default="results/retrain_v3p1/val_ens")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="w1_window_suite.json")
    a = ap.parse_args()
    assert roc_auc_score is not None, "pip install scikit-learn"

    # ---- VAL: derive frozen threshold t* ----
    vy, vs = [], []
    for s in VAL_SUBJS:
        y, sc, _, _ = load(a.val_ens_dir, a.seed, s); vy.append(y); vs.append(sc)
    vy = np.concatenate(vy); vs = np.concatenate(vs)
    tstar, val_f1 = val_threshold(vs, vy)
    print(f"[VAL] frozen t* = {tstar:.4f} (VAL window F1 = {val_f1:.3f})")

    # ---- TEST: per-subject metrics ----
    rows = []
    for s in TEST_SUBJS:
        y, sc, n_i, n_c = load(a.ens_dir, a.seed, s)
        prev = n_c/(n_i+n_c)
        auroc = roc_auc_score(y, sc); auprc = average_precision_score(y, sc)
        p, r, f = prf_at(y, sc, tstar)
        rows.append(dict(subject=s, n_inter=n_i, n_ictal=n_c, prevalence=prev,
                         auroc=auroc, auprc=auprc, auprc_lift=auprc/prev if prev else np.nan,
                         w_prec=p, w_recall=r, w_f1=f))
    def mac(k): return float(np.mean([x[k] for x in rows]))
    macro = dict(auroc=mac("auroc"), auprc=mac("auprc"), auprc_lift=mac("auprc_lift"),
                 w_prec=mac("w_prec"), w_recall=mac("w_recall"), w_f1=mac("w_f1"))

    # pooled (scale caveat)
    ally, alls = [], []
    for s in TEST_SUBJS:
        y, sc, _, _ = load(a.ens_dir, a.seed, s); ally.append(y); alls.append(sc)
    ally = np.concatenate(ally); alls = np.concatenate(alls)
    pooled = dict(auroc=float(roc_auc_score(ally, alls)),
                  auprc=float(average_precision_score(ally, alls)),
                  prevalence=float(ally.mean()))

    print("\nsubj    prev    AUROC   AUPRC   lift   w_prec w_rec  w_F1")
    for x in rows:
        print(f"{x['subject']:7}{x['prevalence']:6.3f} {x['auroc']:7.3f} {x['auprc']:7.3f} "
              f"{x['auprc_lift']:5.1f} {x['w_prec']:6.3f}{x['w_recall']:6.3f}{x['w_f1']:6.3f}")
    print(f"\nMACRO   AUROC={macro['auroc']:.3f} AUPRC={macro['auprc']:.3f} "
          f"(lift {macro['auprc_lift']:.1f}x) | @t*: prec={macro['w_prec']:.3f} "
          f"recall={macro['w_recall']:.3f} F1={macro['w_f1']:.3f}")
    print(f"POOLED  AUROC={pooled['auroc']:.3f} AUPRC={pooled['auprc']:.3f} (prev {pooled['prevalence']:.4f})")

    gate = abs(macro["auroc"]-0.775) <= 0.01
    print(f"\n[sanity gate] macro AUROC {macro['auroc']:.3f} vs §0 0.775 -> {'PASS' if gate else 'CHECK'}")
    Path(a.out).write_text(json.dumps(dict(tstar=float(tstar), per_subject=rows,
                                           macro=macro, pooled=pooled, gate=bool(gate)), indent=2))
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
