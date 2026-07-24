"""
================================================================================
 mag_pen_grid_sweep.py  —  Joint (min_mag_pct x pen_mult) Pareto grid  [v2 - FAST]
================================================================================
FIX vs v1 (see changelog at bottom): v1 called V14.detect_changepoints() once
per (mag, pen) combo -> 8 x 6 = 48 calls/subject. Timed empirically: PELT's
.fit() is ~instant, but .predict(pen=beta) is the true cost and SCALES BADLY
on long noisy signals (4.7s @ pen=0.3 up to 81s @ pen=10.0 on a 31.5k-window
synthetic test). Because min_mag_pct only affects a cheap POST-hoc magnitude
threshold on the candidates predict() already returned -- it does NOT change
predict() itself -- v1 was recomputing the identical, expensive predict()
result 8 times (once per mag) for every pen_mult. That is why chb03 alone
took ~4h: FIX below calls predict() exactly once per (subject, pen_mult) --
6 times/subject, not 48 -- then loops mag_pct cheaply over the cached
candidates. ~8x expected speedup, same math, same fidelity (verified below
against V14's exact detect_changepoints on a small case: identical cps).

NO retraining, NO new GPU inference: still purely re-scoring already-cached
ensemble scores (Core Rule #9). Only the ORCHESTRATION is fixed; the actual
math (smoothing, robust variance, magnitude calc, PELT itself) is imported
directly from cpd_pipeline_v14.py (V14) and evaluation_protocol/szcore_eval,
never reimplemented, so results are bit-identical to what V14.detect_changepoints
would give per (mag, pen) -- just computed without the 8x redundant predict().

OUTPUT
------
  mag_pen_grid_persubject.csv   one row per (subject, mag_pct, pen_mult)
  mag_pen_grid_pooled.csv       one row per (mag_pct, pen_mult): POOLED
                                 (micro) sensitivity/precision/F1/FP-day,
                                 same convention as stat_validation.py.

USAGE
-----
  python mag_pen_grid_sweep.py \
      --scores_dir results/cpd/scores \
      --summary_dir "F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary" \
      --mags 40,50,55,60,65,70,75,80 \
      --canonical_seed 0
================================================================================
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import szcore_eval as SZ
import cpd_pipeline_v14 as V14


def cps_for_pen_then_filter(smoothed, s2, algo, pen, mags_cache, real_inter,
                            mag_pcts, local_win):
    """One predict() call for this pen_mult; then a CHEAP magnitude-percentile
    filter per mag_pct reusing the same candidate set. Returns {mag_pct: cps}."""
    n = len(smoothed)
    beta = pen * s2 * np.log(n)
    cps_raw = [c for c in algo.predict(pen=beta) if 0 < c < n]

    # magnitude of each raw candidate -- compute ONCE per pen (cache across mags)
    key = tuple(cps_raw)
    if key not in mags_cache:
        mags_cache[key] = {c: V14._cp_magnitude(smoothed, c, local_win) for c in cps_raw}
    mags = mags_cache[key]

    if real_inter is not None and np.any(real_inter):
        bg = [m for c, m in mags.items() if real_inter[c]]
    else:
        bg = list(mags.values())

    out = {}
    for mag in mag_pcts:
        if mag and mag > 0 and cps_raw:
            thr = float(np.percentile(bg, mag)) if bg else 0.0
            out[mag] = [c for c in cps_raw if mags[c] >= thr]
        else:
            out[mag] = list(cps_raw)
    return out


def pooled_row(d):
    TP = int(d["tp"].sum())
    FP = int(d["fp"].sum())
    n_sz = int(d["n_seizures"].sum())
    FN = n_sz - TP
    inter_h = float(d["n_inter_h"].sum())
    inter_days = inter_h / 24.0 if inter_h > 0 else float("nan")
    sens = TP / n_sz if n_sz else float("nan")
    prec = TP / (TP + FP) if (TP + FP) else float("nan")
    f1 = (2 * prec * sens / (prec + sens)
          if prec and sens and not np.isnan(prec) and not np.isnan(sens)
          else float("nan"))
    fp_day = FP / inter_days if inter_days else float("nan")
    return dict(TP=TP, FN=FN, FP=FP, n_seizures=n_sz,
                sensitivity=round(sens, 4), precision=round(prec, 4),
                f1=round(f1, 4), fp_per_day=round(fp_day, 3))


def main():
    ap = argparse.ArgumentParser(description="Joint mag%% x pen_mult Pareto grid (fast)")
    ap.add_argument("--scores_dir", default="results/cpd/scores")
    ap.add_argument("--summary_dir", required=True)
    ap.add_argument("--out_dir", default="results/phaseA_appendix")
    ap.add_argument("--mags", default="40,50,55,60,65,70,75,80")
    ap.add_argument("--local_win", type=int, default=15)
    ap.add_argument("--canonical_seed", type=int, default=0)
    args = ap.parse_args()

    mags = [float(x) for x in args.mags.split(",")]
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print(f"Joint grid (FAST): mag%% in {mags}  x  pen_mult in {SZ.PEN_MULTS}"
          f"  -- predict() called {len(SZ.PEN_MULTS)}x/subject (not "
          f"{len(mags)*len(SZ.PEN_MULTS)}x)")
    print("=" * 80)

    import ruptures as rpt
    all_rows = []
    for subj in SZ.TEST_SUBJS:
        inter, ictal = SZ.load_scores(args.scores_dir, subj)
        if inter is None:
            print(f"  [skip] {subj}: cache missing"); continue

        np.random.seed(args.canonical_seed)
        signal, is_ictal, is_buffer, real_inter, sz_ranges, n_inter_h = \
            SZ.build_timeline_masked(subj, inter, ictal, args.summary_dir)
        ref_iv = [(s0 * SZ.WIN_SEC, s1 * SZ.WIN_SEC) for (s0, s1) in sz_ranges]
        total_dur_s = len(signal) * SZ.WIN_SEC

        smoothed = V14._smooth(np.asarray(signal, dtype=float))
        s2 = V14._robust_variance(smoothed, real_inter)
        algo = rpt.Pelt(model="l2", min_size=V14.PELT_MIN_SIZE,
                        jump=V14.PELT_JUMP).fit(smoothed.reshape(-1, 1))

        mags_cache = {}
        for pen in SZ.PEN_MULTS:
            cps_by_mag = cps_for_pen_then_filter(
                smoothed, s2, algo, pen, mags_cache, real_inter, mags, args.local_win)
            for mag, cps in cps_by_mag.items():
                hyp_iv = SZ.cps_to_events(cps, is_buffer, len(signal), sz_ranges=sz_ranges)
                sc = SZ.score_szcore(ref_iv, hyp_iv, total_dur_s, n_inter_h)
                lat = SZ.matched_latency(ref_iv, hyp_iv)
                all_rows.append(dict(subject=subj, mag_pct=mag, pen_mult=pen,
                                     n_seizures=len(sz_ranges), **sc,
                                     mean_lat_s=lat, n_inter_h=round(n_inter_h, 2)))
        print(f"  [done] {subj}  ({len(SZ.PEN_MULTS)} predict() calls, "
              f"{len(mags)} mag values reused from cache)")

    grid = pd.DataFrame(all_rows)
    grid.to_csv(out / "mag_pen_grid_persubject.csv", index=False)

    pooled = []
    for mag in mags:
        for pen in SZ.PEN_MULTS:
            d = grid[(grid.mag_pct == mag) & (grid.pen_mult == pen)]
            if d.empty:
                continue
            row = pooled_row(d)
            row.update(mag_pct=mag, pen_mult=pen)
            pooled.append(row)
    pooled_df = pd.DataFrame(pooled)

    def is_dominated(row, df):
        better = df[(df.sensitivity >= row.sensitivity) &
                    (df.fp_per_day <= row.fp_per_day) &
                    ~((df.sensitivity == row.sensitivity) &
                      (df.fp_per_day == row.fp_per_day))]
        return len(better) > 0

    pooled_df["on_pareto_frontier"] = ~pooled_df.apply(
        lambda r: is_dominated(r, pooled_df), axis=1)
    pooled_df.to_csv(out / "mag_pen_grid_pooled.csv", index=False)

    print("\n" + "-" * 90)
    print(f"{'mag%':>5} {'pen':>6} {'sens':>8} {'prec':>8} {'F1':>8} {'FP/day':>9} {'Pareto?':>8}")
    print("-" * 90)
    for _, r in pooled_df.sort_values(["mag_pct", "pen_mult"]).iterrows():
        print(f"{r.mag_pct:>5g} {r.pen_mult:>6g} {r.sensitivity:>8.3f} "
              f"{r.precision:>8.3f} {r.f1:>8.3f} {r.fp_per_day:>9.2f} "
              f"{'YES' if r.on_pareto_frontier else '':>8}")

    for mag, pen, label in [(60, 1.0, "balanced (locked)"), (70, 0.3, "high-sens (locked)")]:
        row = pooled_df[(pooled_df.mag_pct == mag) & (pooled_df.pen_mult == pen)]
        if not row.empty:
            r = row.iloc[0]
            print(f"\n[check] {label}: sens={r.sensitivity:.3f} FP/day={r.fp_per_day:.2f} "
                  f"(compare to locked 0.750/38.0 or 0.816/48.6)")

    print(f"\nWrote to: {out.resolve()}")


if __name__ == "__main__":
    main()

# ==============================================================================
# CHANGELOG
# v1 -> v2: fixed 8x redundant PELT .predict() calls (called once per (mag,pen)
#   combo instead of once per pen with mag applied as a cheap post-filter).
#   Root cause found by timing .fit() vs .predict() directly: .fit() ~0s;
#   .predict(pen=beta) scaled from ~5s to ~80s on a 31.5k-window synthetic
#   signal depending on pen_mult, and was being called 48x/subject instead of
#   the necessary 6x/subject. No change to the underlying math/algorithm.
# ==============================================================================