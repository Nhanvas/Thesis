"""
================================================================================
 mag_pen_sweep.py  —  WEEK 3 (optimization): operating-point grid search
================================================================================

The buffer don't-care fix + magnitude filter improved sensitivity, precision and
FP/day simultaneously. min_mag_pct=60 was an arbitrary first try. This script
sweeps the 2-D operating space (magnitude-filter percentile x PELT penalty) and
reports the macro trade-off so we can pick a defensible operating point on the
Pareto frontier.

It uses the FAST matcher (no timescoring) so the whole grid runs in minutes;
PELT is fit once per (subject, penalty) and the magnitude threshold is applied
on top, which is cheap. The chosen operating point should then be CONFIRMED with
the authoritative timescoring scorer via:
    python szcore_eval.py --min_mag_pct <best> --out_dir <...>

All filtering is label-free (threshold from interictal CP magnitudes); the
post-ictal buffer is handled as a SzCORE don't-care region (eval-only).

OUTPUTS (to --out_dir, default results/cpd/evaluation/sweep)
  mag_pen_grid.csv         macro sens / precision / F1 / FP-day for every
                           (min_mag_pct, pen) cell, + per-subject detail
  mag_pen_pareto.csv       the Pareto-optimal cells (max sensitivity at each
                           FP/day level) and the best-F1 cell
  figures/fig_mag_pen_tradeoff.{pdf,png}   sensitivity vs FP/day, one curve per
                           magnitude-filter percentile

USAGE
  python mag_pen_sweep.py
  python mag_pen_sweep.py --mag_pcts 0,40,50,60,70 --local_win 15
  python mag_pen_sweep.py --summary_dir "F:/.../summary"

Requires evaluation_protocol.py and szcore_eval.py in the same directory.
================================================================================
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import szcore_eval as S

WIN_SEC = S.WIN_SEC


def sweep_subject(subj, inter, ictal, summary_dir, mag_pcts, local_win, seed):
    """PELT once per penalty; apply each magnitude percentile on top; fast-match."""
    np.random.seed(seed)
    signal, is_ictal, is_buffer, real_inter, sz_ranges, n_inter_h = \
        S.build_timeline_masked(subj, inter, ictal, summary_dir)
    smoothed = pd.Series(signal).rolling(window=15, min_periods=1,
                                         center=True).mean().values
    pelt = S.run_pelt_seedindep(smoothed, S.PEN_MULTS, real_inter)
    n = len(signal)
    rows = []
    for pm in S.PEN_MULTS:
        cps, _ = pelt[pm]
        # precompute magnitudes once per CP
        mags = {c: S.cp_magnitude(smoothed, c, local_win)
                for c in cps if 0 < c < n}
        inter_mags = [m for c, m in mags.items() if real_inter[c]]
        for q in mag_pcts:
            thr = (float(np.percentile(inter_mags, q))
                   if q > 0 and inter_mags else 0.0)
            kept = [c for c in cps if 0 < c < n and mags[c] >= thr]
            r = S.fast_event_match(kept, is_buffer, sz_ranges, n, n_inter_h)
            prec = (r["tp"] / (r["tp"] + r["fp"])
                    if (r["tp"] + r["fp"]) else float("nan"))
            f1 = (2 * prec * r["sensitivity"] / (prec + r["sensitivity"])
                  if prec and r["sensitivity"] and not np.isnan(prec) else float("nan"))
            rows.append(dict(subject=subj, min_mag_pct=q, pen_mult=pm,
                             n_seizures=r["n_seizures"], tp=r["tp"], fp=r["fp"],
                             sensitivity=r["sensitivity"], precision=prec, f1=f1,
                             fp_per_day=r["fp_per_day"]))
    return rows


def main():
    ap = argparse.ArgumentParser(description="Week 3 magnitude x penalty sweep")
    ap.add_argument("--scores_dir", default="results/cpd/scores")
    ap.add_argument("--summary_dir",
                    default=r"F:\Study\Thesis\Dataset\CHB-MIT\CHB info\summary")
    ap.add_argument("--out_dir", default="results/cpd/evaluation/sweep")
    ap.add_argument("--mag_pcts", default="0,40,50,60,70",
                    help="comma-separated magnitude-filter percentiles to sweep")
    ap.add_argument("--local_win", type=int, default=15)
    ap.add_argument("--canonical_seed", type=int, default=0)
    args = ap.parse_args()

    mag_pcts = [float(x) for x in args.mag_pcts.split(",")]
    out = Path(args.out_dir); fig_dir = out / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print(f"MAG x PEN SWEEP  |  mag_pcts={mag_pcts}  pens={S.PEN_MULTS}")
    print("(fast matcher; confirm the chosen cell with szcore_eval.py afterwards)")
    print("=" * 78)

    all_rows = []
    for subj in S.TEST_SUBJS:
        inter, ictal = S.load_scores(args.scores_dir, subj)
        if inter is None:
            print(f"  [skip] {subj}: cache missing"); continue
        all_rows += sweep_subject(subj, inter, ictal, args.summary_dir,
                                  mag_pcts, args.local_win, args.canonical_seed)
        print(f"  {subj} done")

    df = pd.DataFrame(all_rows)
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "mag_pen_grid_detail.csv", index=False)

    # ---- macro grid (sum tp/sz for sensitivity; mean precision/FP-day) ----
    grid = []
    for q in mag_pcts:
        for pm in S.PEN_MULTS:
            d = df[(df.min_mag_pct == q) & (df.pen_mult == pm)]
            if d.empty:
                continue
            dr = d.tp.sum() / max(d.n_seizures.sum(), 1)
            grid.append(dict(min_mag_pct=q, pen_mult=pm,
                             sensitivity=round(dr, 4),
                             precision=round(d.precision.mean(), 4),
                             f1=round(d.f1.mean(), 4),
                             fp_per_day=round(d.fp_per_day.mean(), 2),
                             n_detected=int(d.tp.sum()),
                             n_total=int(d.n_seizures.sum())))
    gdf = pd.DataFrame(grid)
    gdf.to_csv(out / "mag_pen_grid.csv", index=False)

    # ---- Pareto frontier: max sensitivity at each FP/day, + best F1 ----
    gsort = gdf.sort_values("fp_per_day")
    pareto, best_sens = [], -1
    for _, r in gsort.iterrows():
        if r.sensitivity > best_sens:
            pareto.append(r); best_sens = r.sensitivity
    pareto_df = pd.DataFrame(pareto)
    best_f1 = gdf.loc[gdf.f1.idxmax()]
    pareto_df.to_csv(out / "mag_pen_pareto.csv", index=False)

    print("\n" + "-" * 78)
    print("MACRO GRID (sensitivity | precision | FP/day)")
    print("-" * 78)
    print(f"{'mag%':>5} " + " ".join(f"pen{pm:>5g}" for pm in S.PEN_MULTS))
    for q in mag_pcts:
        cells = []
        for pm in S.PEN_MULTS:
            r = gdf[(gdf.min_mag_pct == q) & (gdf.pen_mult == pm)]
            if r.empty:
                cells.append("    -   ")
            else:
                cells.append(f"{r.sensitivity.iloc[0]:.2f}/{r.fp_per_day.iloc[0]:>4.0f}")
        print(f"{q:>5g} " + " ".join(cells))

    print("\nBEST-F1 cell: "
          f"mag%={best_f1.min_mag_pct:g} pen={best_f1.pen_mult:g} -> "
          f"sens={best_f1.sensitivity:.3f} prec={best_f1.precision:.3f} "
          f"F1={best_f1.f1:.3f} FP/day={best_f1.fp_per_day:.1f}")
    print("\nPARETO frontier (max sensitivity per FP/day level):")
    for _, r in pareto_df.iterrows():
        print(f"  mag%={r.min_mag_pct:>3g} pen={r.pen_mult:>4g} | "
              f"sens={r.sensitivity:.3f} FP/day={r.fp_per_day:>6.1f} "
              f"prec={r.precision:.3f}")

    # ---- figure: sensitivity vs FP/day, one curve per mag_pct ----
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for q in mag_pcts:
        d = gdf[gdf.min_mag_pct == q].sort_values("fp_per_day")
        ax.plot(d.fp_per_day, d.sensitivity, "o-", lw=1.3,
                label=f"mag%={q:g}")
    ax.set_xlabel("False positives per day (lower = better)")
    ax.set_ylabel("Event sensitivity")
    ax.set_title("Operating curves: magnitude filter x PELT penalty")
    ax.grid(alpha=0.25); ax.legend(fontsize=8, title="magnitude filter")
    for ext in ("pdf", "png"):
        fig.savefig(fig_dir / f"fig_mag_pen_tradeoff.{ext}", bbox_inches="tight")
    plt.close(fig)

    print(f"\nWrote grid + pareto + figure to: {out.resolve()}")


if __name__ == "__main__":
    main()