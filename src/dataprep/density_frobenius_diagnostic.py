"""
density_frobenius_diagnostic.py — sparsification diagnostic for Table 3.1
(graph density under each rule) and Fig 3.1 (separation between ictal and
interictal connectivity, per subject).

WHY THIS SCRIPT EXISTS
-----------------------
graph_construction.py's docstring and the earlier solution document both quote
summary numbers for this comparison from a diagnostic run whose per-subject
output was never committed under results/. This script reconstructs the same
comparison from the raw preprocessed windows, which are present locally. It is
a fresh measurement, not a reproduction of that run, and it will not
necessarily reproduce the docstring figures.

WHY THE RAW FROBENIUS COLUMN IS NOT A FAIR COMPARISON
------------------------------------------------------
The two rules produce matrices with very different numbers of non-zero entries:
a fixed threshold retains almost every edge, the proportional rule retains about
a fifth of them. The unnormalised Frobenius norm of the ictal-minus-interictal
difference sums over those entries, so it shrinks mechanically when edges are
removed, whatever happens to the separation itself. Comparing the two raw norms
therefore measures sparsity, not discriminability, and it must not be read as
evidence that one rule separates the two states better than the other.

Two scale-comparable measures are added for that purpose:

  relative Frobenius  = ||A_ictal - A_inter||_F / ||A_inter||_F
      the difference expressed as a fraction of the interictal structure it is
      measured against, so the units cancel.

  cosine distance     = 1 - cos(vec(A_ictal), vec(A_inter))   [upper triangle]
      depends only on the direction of the two connectivity patterns, not on
      their magnitude or on how many edges survive.

Both are reported alongside the raw values. Fig 3.1 should be built from one of
the normalised columns; the raw columns are kept only so the earlier figures
remain traceable.

Outputs -> results/diagnostics/density_frobenius_v2/
    density_per_subject.csv     subject, split, rule, n_windows_sampled, mean_density
    separation_per_subject.csv  subject,
                                frobenius_fixed_t0_05, frobenius_topk20,
                                pct_change_topk_vs_fixed,
                                rel_frobenius_fixed_t0_05, rel_frobenius_topk20,
                                pct_change_rel_topk_vs_fixed,
                                cosine_dist_fixed_t0_05, cosine_dist_topk20,
                                pct_change_cos_topk_vs_fixed

USAGE (CPU; interictal subsampled for tractability, ictal used in full)
    python src/dataprep/density_frobenius_diagnostic.py --stride 20
"""
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
_src = _os.path.dirname(_here)
_root = _os.path.dirname(_src)
for _p in (_here, _src):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import argparse
import csv
from pathlib import Path

import numpy as np

from graph_construction import (apply_car, compute_wpli, compute_aec, combine_adjacency,
                                apply_topk_threshold, DEFAULT_ALPHA, FIXED_THRESHOLD,
                                DEFAULT_KEEP_RATIO)

ROOT = Path(_root)
PROC = ROOT / "data" / "processed"
TEST_SUBJ = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]


def raw_combined(window, alpha=DEFAULT_ALPHA, fs=256):
    """CAR -> wPLI + AEC -> combined, WITHOUT the final fixed-threshold step, so
    both sparsification rules apply downstream to the SAME matrix."""
    w = apply_car(window.astype(np.float64))
    wpli = compute_wpli(w, fs=fs)
    aec = compute_aec(w) if alpha < 1.0 else np.zeros_like(wpli)
    return combine_adjacency(wpli, aec, alpha=alpha)


def density(A):
    iu = np.triu_indices(A.shape[0], k=1)
    return float(np.count_nonzero(A[iu]) / len(iu[0]))


def upper(A):
    iu = np.triu_indices(A.shape[0], k=1)
    return A[iu]


def separation(A_ictal, A_inter):
    """Three measures of how far the mean ictal graph sits from the mean
    interictal graph. Only the last two are comparable across sparsity levels."""
    d = A_ictal - A_inter
    frob = float(np.linalg.norm(d))
    base = float(np.linalg.norm(A_inter))
    rel = frob / base if base > 0 else float("nan")
    a, b = upper(A_ictal), upper(A_inter)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    cos = float(1.0 - (a @ b) / (na * nb)) if na > 0 and nb > 0 else float("nan")
    return frob, rel, cos


def pct_change(new, old):
    return round((new - old) / old * 100.0, 1) if old and old == old and old > 0 \
        else float("nan")


def process_split(path, stride, alpha, keep_ratio):
    arr = np.load(path, mmap_mode="r")
    n = arr.shape[0]
    idx = range(0, n, max(stride, 1))
    sum_fixed = sum_topk = None
    dens_fixed, dens_topk = [], []
    count = 0
    for i in idx:
        Araw = raw_combined(arr[i])
        Af = np.where(Araw >= FIXED_THRESHOLD, Araw, 0.0); np.fill_diagonal(Af, 0.0)
        At = apply_topk_threshold(Araw, keep_ratio=keep_ratio)
        dens_fixed.append(density(Af)); dens_topk.append(density(At))
        sum_fixed = Af.copy() if sum_fixed is None else sum_fixed + Af
        sum_topk = At.copy() if sum_topk is None else sum_topk + At
        count += 1
    return dict(n=count, mean_density_fixed=float(np.mean(dens_fixed)),
                mean_density_topk=float(np.mean(dens_topk)),
                mean_A_fixed=sum_fixed / count, mean_A_topk=sum_topk / count)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proc_dir", default=str(PROC))
    ap.add_argument("--stride", type=int, default=20, help="interictal subsample stride")
    ap.add_argument("--alpha", type=float, default=DEFAULT_ALPHA)
    ap.add_argument("--keep_ratio", type=float, default=DEFAULT_KEEP_RATIO)
    ap.add_argument("--out_dir",
                    default=str(ROOT / "results" / "diagnostics" / "density_frobenius_v2"))
    a = ap.parse_args()
    proc, out = Path(a.proc_dir), Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)

    dens_rows, sep_rows = [], []
    for subj in TEST_SUBJ:
        fi, fc = proc / f"{subj}_interictal.npy", proc / f"{subj}_ictal.npy"
        if not (fi.is_file() and fc.is_file()):
            print(f"[skip] {subj}: raw windows not found at {fi} / {fc}"); continue
        r_i = process_split(fi, a.stride, a.alpha, a.keep_ratio)
        r_c = process_split(fc, 1, a.alpha, a.keep_ratio)   # ictal: no subsampling
        for split, r in [("interictal", r_i), ("ictal", r_c)]:
            dens_rows.append(dict(subject=subj, split=split, rule="fixed_t0.05",
                                  n_windows_sampled=r["n"],
                                  mean_density=round(r["mean_density_fixed"], 4)))
            dens_rows.append(dict(subject=subj, split=split, rule="topk20",
                                  n_windows_sampled=r["n"],
                                  mean_density=round(r["mean_density_topk"], 4)))

        f_fix, rel_fix, cos_fix = separation(r_c["mean_A_fixed"], r_i["mean_A_fixed"])
        f_top, rel_top, cos_top = separation(r_c["mean_A_topk"], r_i["mean_A_topk"])
        sep_rows.append(dict(
            subject=subj,
            frobenius_fixed_t0_05=round(f_fix, 4), frobenius_topk20=round(f_top, 4),
            pct_change_topk_vs_fixed=pct_change(f_top, f_fix),
            rel_frobenius_fixed_t0_05=round(rel_fix, 4),
            rel_frobenius_topk20=round(rel_top, 4),
            pct_change_rel_topk_vs_fixed=pct_change(rel_top, rel_fix),
            cosine_dist_fixed_t0_05=round(cos_fix, 4),
            cosine_dist_topk20=round(cos_top, 4),
            pct_change_cos_topk_vs_fixed=pct_change(cos_top, cos_fix)))

        print(f"{subj}: density(fixed) I/C = {r_i['mean_density_fixed']:.3f}/"
              f"{r_c['mean_density_fixed']:.3f}  "
              f"density(topk) = {r_i['mean_density_topk']:.3f}/"
              f"{r_c['mean_density_topk']:.3f}")
        print(f"        raw Frobenius  fixed {f_fix:.3f}  topk {f_top:.3f}  "
              f"({pct_change(f_top, f_fix):+.1f}%)   [not scale-comparable]")
        print(f"        rel Frobenius  fixed {rel_fix:.3f}  topk {rel_top:.3f}  "
              f"({pct_change(rel_top, rel_fix):+.1f}%)")
        print(f"        cosine dist    fixed {cos_fix:.4f}  topk {cos_top:.4f}  "
              f"({pct_change(cos_top, cos_fix):+.1f}%)")

    def write(name, rows):
        if not rows:
            print(f"[warn] nothing to write for {name}"); return
        with open(out / name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
        print(f"wrote {out/name}  ({len(rows)} rows)")

    write("density_per_subject.csv", dens_rows)
    write("separation_per_subject.csv", sep_rows)


if __name__ == "__main__":
    main()
