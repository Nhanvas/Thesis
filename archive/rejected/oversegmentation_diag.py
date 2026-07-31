"""
================================================================================
 oversegmentation_diag.py  —  WEEK 3 (diagnosis): why does PELT over-segment?
================================================================================

CONTEXT
-------
SzCORE re-scoring showed the dominant problem is over-segmentation: PELT emits
~200-580 change points per subject (uniformly across all 8 subjects) for only a
handful of seizures, so event precision is ~0.02 and FP/day ~150, and this
persists across the whole penalty range. Penalty tuning alone cannot fix it.

This script does NOT intervene. It tests a falsifiable hypothesis before we
choose an intervention (per the research plan):

  HYPOTHESIS  Spurious change points are LOW-magnitude (small mean shifts in a
              still-fluctuating interictal baseline), while seizure-related
              change points are HIGH-magnitude. If so, a minimum-change-
              magnitude filter calibrated on interictal noise will remove most
              spurious CPs while keeping seizure CPs.
  FALSIFIED IF  seizure-aligned and spurious CPs have overlapping magnitude
                distributions, i.e. no threshold separates them. Then the fix
                must be elsewhere (stronger/adaptive smoothing or a different
                cost model), not a magnitude filter.

It also checks a SECOND question raised by the SzCORE results:

  Did the buffer-CP drop (a change I added) remove legitimate seizure-OFFSET
  change points for brief-seizure subjects (chb16, chb06)? It reports, per
  subject, how many seizure-aligned CPs fall in buffer windows.

For each test subject at a chosen penalty it computes, for every change point:
  - magnitude = | mean(signal after) - mean(signal before) | over a local window
  - whether it is seizure-aligned (within [onset-30s, offset+60s] of any seizure)
  - whether it lies in a post-ictal buffer window
and then simulates a magnitude-threshold sweep showing the trade-off between
spurious CPs removed and seizure CPs lost.

OUTPUTS (to --out_dir, default results/cpd/evaluation/oversegmentation)
  overseg_cp_level.csv        one row per change point (subject, time, magnitude,
                              seizure_aligned, in_buffer)
  overseg_subject_summary.csv per subject: n_cps, n seizure-aligned, n spurious,
                              n in buffer, seizure-aligned CPs lost to buffer
  overseg_threshold_sweep.csv magnitude threshold vs (spurious removed %,
                              seizure CPs kept %) — macro
  figures/fig_overseg_magnitude_hist.{pdf,png}
  figures/fig_overseg_threshold_sweep.{pdf,png}

USAGE
  python oversegmentation_diag.py
  python oversegmentation_diag.py --pen 0.3 --local_win 15
  python oversegmentation_diag.py --summary_dir "F:/.../summary"

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
import evaluation_protocol as E

WIN_SEC = S.WIN_SEC
TOL_START, TOL_END = 30, 60   # SzCORE tolerance (s) for "seizure-aligned"


def cp_magnitude(signal, c, L):
    """Local mean shift across change point c, averaged over L windows each side."""
    a0, a1 = max(0, c - L), c
    b0, b1 = c, min(len(signal), c + L)
    if a1 <= a0 or b1 <= b0:
        return 0.0
    return abs(float(signal[b0:b1].mean()) - float(signal[a0:a1].mean()))


def seizure_aligned(c_sec, sz_ranges):
    """True if change-point time (s) is within SzCORE tolerance of any seizure."""
    for (s, e) in sz_ranges:
        on, off = s * WIN_SEC, e * WIN_SEC
        if on - TOL_START <= c_sec <= off + TOL_END:
            return True
    return False


def main():
    ap = argparse.ArgumentParser(description="Week 3 over-segmentation diagnosis")
    ap.add_argument("--scores_dir", default="results/cpd/scores")
    ap.add_argument("--summary_dir",
                    default=r"F:\Study\Thesis\Dataset\CHB-MIT\CHB info\summary")
    ap.add_argument("--out_dir", default="results/cpd/evaluation/oversegmentation")
    ap.add_argument("--pen", type=float, default=0.5,
                    help="penalty multiplier to diagnose at")
    ap.add_argument("--local_win", type=int, default=15,
                    help="windows each side for the magnitude estimate (15 = 1 min)")
    ap.add_argument("--canonical_seed", type=int, default=0)
    args = ap.parse_args()

    out = Path(args.out_dir); fig_dir = out / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print(f"OVER-SEGMENTATION DIAGNOSIS  |  pen={args.pen:g}  "
          f"local_win={args.local_win} ({args.local_win*WIN_SEC}s/side)")
    print("=" * 78)

    cp_rows, subj_rows = [], []
    for subj in S.TEST_SUBJS:
        inter, ictal = S.load_scores(args.scores_dir, subj)
        if inter is None:
            print(f"  [skip] {subj}: cache missing"); continue
        np.random.seed(args.canonical_seed)
        signal, is_ictal, is_buffer, real_inter, sz_ranges, n_inter_h = \
            S.build_timeline_masked(subj, inter, ictal, args.summary_dir)
        smoothed = pd.Series(signal).rolling(window=15, min_periods=1,
                                             center=True).mean().values
        pelt = S.run_pelt_seedindep(smoothed, [args.pen], real_inter)
        cps, _ = pelt[args.pen]

        n_align = n_spur = n_buf = n_align_lost_buf = 0
        for c in cps:
            if not (0 < c < len(signal)):
                continue
            mag = cp_magnitude(smoothed, c, args.local_win)
            aligned = seizure_aligned(c * WIN_SEC, sz_ranges)
            inbuf = bool(is_buffer[c])
            cp_rows.append(dict(subject=subj, cp_window=int(c),
                                time_s=int(c * WIN_SEC), magnitude=round(mag, 5),
                                seizure_aligned=aligned, in_buffer=inbuf))
            n_align += aligned
            n_spur += (not aligned)
            n_buf += inbuf
            n_align_lost_buf += (aligned and inbuf)

        subj_rows.append(dict(subject=subj, n_seizures=len(sz_ranges),
                              n_cps=len(cps), n_aligned=n_align, n_spurious=n_spur,
                              n_in_buffer=n_buf,
                              aligned_lost_to_buffer=n_align_lost_buf,
                              n_inter_h=round(n_inter_h, 2)))
        print(f"  {subj}: {len(cps):>4} CPs | aligned={n_align:>3} spurious={n_spur:>4} "
              f"| in_buffer={n_buf:>3} (aligned-in-buffer={n_align_lost_buf})")

    cp_df = pd.DataFrame(cp_rows)
    subj_df = pd.DataFrame(subj_rows)
    out.mkdir(parents=True, exist_ok=True)
    cp_df.to_csv(out / "overseg_cp_level.csv", index=False)
    subj_df.to_csv(out / "overseg_subject_summary.csv", index=False)

    # ---- magnitude separation test ----
    aligned_mag = cp_df.loc[cp_df.seizure_aligned, "magnitude"].values
    spur_mag = cp_df.loc[~cp_df.seizure_aligned, "magnitude"].values

    print("\n" + "-" * 78)
    print("MAGNITUDE SEPARATION (the hypothesis test)")
    print("-" * 78)
    if len(aligned_mag) and len(spur_mag):
        print(f"  seizure-aligned CPs: n={len(aligned_mag):>4}  "
              f"median mag={np.median(aligned_mag):.4f}  "
              f"p25={np.percentile(aligned_mag,25):.4f}")
        print(f"  spurious CPs:        n={len(spur_mag):>4}  "
              f"median mag={np.median(spur_mag):.4f}  "
              f"p90={np.percentile(spur_mag,90):.4f}")

    # ---- threshold sweep: for delta = percentile of spurious magnitudes ----
    sweep = []
    if len(spur_mag) and len(aligned_mag):
        for pct in range(0, 100, 5):
            delta = np.percentile(spur_mag, pct)
            spur_removed = float(np.mean(spur_mag < delta))      # fraction pruned
            aligned_kept = float(np.mean(aligned_mag >= delta))  # fraction retained
            sweep.append(dict(delta=round(delta, 5), spur_pct=pct,
                              spurious_removed_frac=round(spur_removed, 4),
                              aligned_kept_frac=round(aligned_kept, 4)))
    sweep_df = pd.DataFrame(sweep)
    sweep_df.to_csv(out / "overseg_threshold_sweep.csv", index=False)

    # best operating delta: maximize (spurious_removed + aligned_kept)/2
    if not sweep_df.empty:
        sweep_df["score"] = (sweep_df.spurious_removed_frac
                             + sweep_df.aligned_kept_frac) / 2
        best = sweep_df.loc[sweep_df.score.idxmax()]
        print(f"\n  Best magnitude threshold delta={best.delta:.4f}: "
              f"removes {best.spurious_removed_frac:.0%} of spurious CPs "
              f"while keeping {best.aligned_kept_frac:.0%} of seizure-aligned CPs.")
        if best.spurious_removed_frac > 0.6 and best.aligned_kept_frac > 0.8:
            print("  -> HYPOTHESIS SUPPORTED: a magnitude filter separates them well.")
        elif best.aligned_kept_frac < 0.7:
            print("  -> HYPOTHESIS FALSIFIED: cannot prune spurious CPs without "
                  "losing seizure CPs. Need smoothing/cost-model change instead.")
        else:
            print("  -> PARTIAL: a magnitude filter helps but is not sufficient alone.")

    # ---- buffer-drop check ----
    total_aligned_in_buf = int(subj_df.aligned_lost_to_buffer.sum())
    print("\n" + "-" * 78)
    print("BUFFER-DROP CHECK (chb16 / chb06 regression suspect)")
    print("-" * 78)
    print(f"  seizure-aligned CPs falling in buffer windows (would be dropped): "
          f"{total_aligned_in_buf}")
    for _, r in subj_df.iterrows():
        if r.aligned_lost_to_buffer > 0:
            print(f"    {r.subject}: {int(r.aligned_lost_to_buffer)} aligned CP(s) in buffer")

    # ---- figures ----
    if len(aligned_mag) and len(spur_mag):
        fig, ax = plt.subplots(figsize=(6, 4))
        hi = np.percentile(np.concatenate([aligned_mag, spur_mag]), 99)
        bins = np.linspace(0, hi, 40)
        ax.hist(spur_mag, bins=bins, alpha=0.6, label=f"spurious (n={len(spur_mag)})",
                color="#c55a11", density=True)
        ax.hist(aligned_mag, bins=bins, alpha=0.6, label=f"seizure-aligned (n={len(aligned_mag)})",
                color="#1f4e79", density=True)
        ax.set_xlabel("Change-point magnitude (|mean shift|)")
        ax.set_ylabel("density")
        ax.set_title(f"CP magnitude: seizure-aligned vs spurious (pen={args.pen:g})")
        ax.legend(fontsize=8)
        for ext in ("pdf", "png"):
            fig.savefig(fig_dir / f"fig_overseg_magnitude_hist.{ext}", bbox_inches="tight")
        plt.close(fig)

    if not sweep_df.empty:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(sweep_df.delta, sweep_df.spurious_removed_frac, "o-",
                label="spurious removed", color="#c55a11")
        ax.plot(sweep_df.delta, sweep_df.aligned_kept_frac, "s-",
                label="seizure-aligned kept", color="#1f4e79")
        ax.set_xlabel("magnitude threshold delta")
        ax.set_ylabel("fraction")
        ax.set_title("Magnitude-filter trade-off")
        ax.legend(fontsize=8); ax.grid(alpha=0.25)
        for ext in ("pdf", "png"):
            fig.savefig(fig_dir / f"fig_overseg_threshold_sweep.{ext}", bbox_inches="tight")
        plt.close(fig)

    print(f"\nWrote CSVs + figures to: {out.resolve()}")


if __name__ == "__main__":
    main()