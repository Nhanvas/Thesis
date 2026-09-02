"""
================================================================================
 rebuild_ensemble_new_weight.py  —  official Phase-A numbers on the NEW
                                     locked ensemble weight (Decision #19)
================================================================================
WHY THIS FILE
-------------
Decision #19 (2026-07/08): the ensemble weight was changed from the original
(w_recon=0.35, w_temp=0.30, w_gamma=0.35) to (w_recon=0.40, w_temp=0.35,
w_gamma=0.25), based on 3 independent verification layers (wide weight grid,
8-seed paired robustness check at the balanced point, and a cross-operating-
point + per-subject check confirming the gain holds at BOTH locked operating
points with chb06 benefiting most and no tradeoff pattern -- see
weight_sensitivity_sweep.py, weight_seed_robustness_check.py,
weight_candidate_crosscheck.py and their outputs).

ALL of that verification work used mean-over-8-seeds numbers from bootstrap-
padding, which is appropriate for detecting a robust signal but is NOT the
canonical, citable number. Every other locked figure in this thesis
(szcore_event_level_mag60.csv, mag70.csv, mag_pen_grid_*.csv,
duration_bucket_summary.csv) was produced by evaluate_subject() from
szcore_eval.py at canonical_seed=0 -- exactly ONE deterministic run, not an
average. This script reproduces that exact convention for the NEW weight, so
the new "official" numbers are directly comparable to (and replace) the old
mag60/mag50 event-level tables, and can be fed straight into
stat_validation.py without any changes to that script.

WHAT THIS SCRIPT DOES
----------------------
For BOTH locked operating points (balanced: mag=60,pen=1.0; high_sens:
mag=50,pen=1.0):
  1. Rebuilds ens_inter/ens_ictal per subject from cached components using
     the NEW weight (0.40, 0.35, 0.25).
  2. Runs szcore_eval.evaluate_subject() -- the exact authoritative path,
     canonical_seed=0 -- to get per-subject, per-pen_mult TP/FN/FP etc.
  3. Writes output in the SAME SCHEMA as szcore_event_level_mag60.csv /
     mag70.csv, so stat_validation.py's --ops flag can point at these files
     with zero code changes (they are NOT grid-style multi-mag_pct files,
     so the plain label=csv@pen calling convention applies, same as before
     Decision #16's mag_pct extension was needed for the grid file).

OUTPUT
------
  szcore_event_level_newweight_mag60.csv   (balanced operating point, all 6 pens)
  szcore_event_level_newweight_mag50.csv   (high-sens operating point, all 6 pens)

Both written to --out_dir, default results/cpd/evaluation (same location as
the original szcore_event_level_mag*.csv, for consistency).

NEXT STEP AFTER RUNNING THIS
------------------------------
  python stat_validation.py --ops \
    "balanced=szcore_event_level_newweight_mag60.csv@1.0;highsens=szcore_event_level_newweight_mag50.csv@1.0"

This gives the official CI-bearing numbers for Decision #19 to go into
RESULTS_OF_RECORD.md, in exactly the same format as every other locked
operating point.

WHY BOTH WEIGHTS ARE RUN HERE (added after a reproducibility discrepancy)
---------------------------------------------------------------------------
When this script was first run for only the NEW weight, the resulting
high_sens sensitivity (0.7632) was compared against the previously-LOCKED
Decision #16 figure (0.816, from mag_pen_grid_sweep.py). Those two numbers
are NOT directly comparable: they were produced by different scripts, and
CHB-MIT's bootstrap-padding step (np.random.choice on inter_scores) is only
reproducible if the exact same code path seeds np.random at the exact same
point. mag_pen_grid_sweep.py and this script may not do so identically.

To get an honest, apples-to-apples delta, THIS SCRIPT NOW RUNS BOTH WEIGHTS
through the IDENTICAL evaluate_subject() call sequence, same canonical_seed.
Compare the OLD-weight numbers below against the previously-locked 0.750/0.816
figures: if they match, the harness is faithful and the NEW-weight numbers are
trustworthy for a direct comparison. If they do NOT match, that itself is an
important finding to report (a reproducibility gap in the locked pipeline)
and must be resolved BEFORE using this script's new-weight numbers to update
any locked document.

USAGE (Cursor / CPU)
  python rebuild_ensemble_new_weight.py --comp_dir data/processed/components \
      --summary_dir "F:\\...\\summary" --out_dir results/cpd/evaluation

Requires szcore_eval.py, evaluation_protocol.py, cpd_pipeline_v14.py, timescoring.
================================================================================
"""
import argparse
import csv
import os
import glob as _glob
import numpy as np

import szcore_eval as SE

TEST_SUBJS = SE.TEST_SUBJS
PEN_MULTS = SE.PEN_MULTS

# Decision #19: run BOTH weights through the identical harness for an honest
# apples-to-apples comparison (see the docstring note above on why).
WEIGHTS = [("old_locked", (0.35, 0.30, 0.35)), ("new_decision19", (0.40, 0.35, 0.25))]

# the two locked operating points, by magnitude-filter percentile
MAG_POINTS = [("mag60", 60.0), ("mag50", 50.0)]

# what was previously reported as locked for the OLD weight (for the
# reproducibility sanity check printed at the end)
PREVIOUSLY_LOCKED = {
    ("old_locked", "mag60"): dict(sensitivity=0.750, fp_per_day=38.04, tp=57),
    ("old_locked", "mag50"): dict(sensitivity=0.8158, fp_per_day=47.97, tp=62),
}


def load_comp(comp_dir, subj):
    def L(name, split):
        p = os.path.join(comp_dir, f"{name}_{subj}_{split}.npy")
        return np.load(p).astype(np.float64) if os.path.exists(p) else None
    return {k: (L(k, "inter"), L(k, "ictal")) for k in ("zrecon", "ztemp", "zgamma")}


def main():
    ap = argparse.ArgumentParser(description="Official Phase-A re-evaluation "
                                             "on the new locked weight (Decision #19)")
    ap.add_argument("--comp_dir", default="data/processed/components")
    ap.add_argument("--summary_dir", required=True)
    ap.add_argument("--out_dir", default="results/cpd/evaluation")
    ap.add_argument("--canonical_seed", type=int, default=0)
    ap.add_argument("--subjs", default=",".join(TEST_SUBJS))
    args = ap.parse_args()
    subjs = args.subjs.split(",")
    os.makedirs(args.out_dir, exist_ok=True)
    print(f"[diag] outputs -> {os.path.abspath(args.out_dir)}")

    probe = f"zrecon_{subjs[0]}_inter.npy"
    if not os.path.exists(os.path.join(args.comp_dir, probe)):
        hits = _glob.glob(os.path.join(".", "**", probe), recursive=True)
        if hits:
            args.comp_dir = os.path.dirname(hits[0])
            print(f"[diag] components not at default; using {os.path.abspath(args.comp_dir)}")
    print(f"[diag] components dir: {os.path.abspath(args.comp_dir)}")
    print(f"[diag] running BOTH weights through the identical harness: "
         f"{[(n, w) for n, w in WEIGHTS]}")

    comps = {}
    for s in subjs:
        c = load_comp(args.comp_dir, s)
        if not all(c[k][0] is not None and c[k][1] is not None for k in c):
            print(f"[warn] {s}: components missing -> skipped")
            continue
        ni = min(len(c["zrecon"][0]), len(c["ztemp"][0]), len(c["zgamma"][0]))
        nc = min(len(c["zrecon"][1]), len(c["ztemp"][1]), len(c["zgamma"][1]))
        comps[s] = {k: (c[k][0][:ni], c[k][1][:nc]) for k in c}
    subjs = [s for s in subjs if s in comps]
    if not subjs:
        print("[error] no subjects with complete components found -- aborting.")
        return

    pooled_results = {}   # (weight_name, mag_label) -> dict(sens, fp_per_day, tp, n_sz)

    for weight_name, (wr, wt, wg) in WEIGHTS:
        for mag_label, mag_pct in MAG_POINTS:
            print(f"\n{'=' * 78}\n{weight_name} w=({wr},{wt},{wg}) / {mag_label} "
                 f"(mag_pct={mag_pct}) -- canonical_seed={args.canonical_seed}\n{'=' * 78}")
            all_rows = []
            for s in subjs:
                zr_i, zr_c = comps[s]["zrecon"]; zt_i, zt_c = comps[s]["ztemp"]; zg_i, zg_c = comps[s]["zgamma"]
                ens_i = wr * zr_i + wt * zt_i + wg * zg_i
                ens_c = wr * zr_c + wt * zt_c + wg * zg_c

                np.random.seed(args.canonical_seed)  # matches szcore_eval.main() determinism
                rows = SE.evaluate_subject(s, ens_i, ens_c, args.summary_dir,
                                           min_mag_pct=mag_pct, local_win=15)
                all_rows.extend(rows)
                r_target = next((r for r in rows if abs(r["pen_mult"] - 1.0) < 1e-9), rows[0])
                print(f"  {s}: @pen=1.0  sens={r_target['sensitivity']:.3f}  "
                     f"prec={r_target['precision']:.3f}  fp_per_day={r_target['fp_per_day']:.1f}  "
                     f"({r_target['n_hyp']} hyp events)")

            out_name = f"szcore_event_level_{weight_name}_{mag_label}.csv"
            out_path = os.path.join(args.out_dir, out_name)
            with open(out_path, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys())); w.writeheader(); w.writerows(all_rows)

            d1 = [r for r in all_rows if abs(r["pen_mult"] - 1.0) < 1e-9]
            tp_sum = sum(r["tp"] for r in d1); nsz_sum = sum(r["n_seizures"] for r in d1)
            fp_sum = sum(r["fp"] for r in d1); h_sum = sum(r["n_inter_h"] for r in d1)
            sens = tp_sum / nsz_sum; fp_day = fp_sum / h_sum * 24
            pooled_results[(weight_name, mag_label)] = dict(
                sensitivity=sens, fp_per_day=fp_day, tp=tp_sum, n_sz=nsz_sum)
            print(f"\n  [pooled @pen=1.0] sens={sens:.4f} ({tp_sum}/{nsz_sum})  FP/day={fp_day:.2f}")
            print(f"  [saved] {os.path.abspath(out_path)}")

    # ---- reproducibility sanity check: does old_locked match what was previously reported? ----
    print("\n" + "=" * 78)
    print("REPRODUCIBILITY CHECK: old_locked (this run) vs previously-locked figures")
    print("=" * 78)
    any_mismatch = False
    for mag_label in ["mag60", "mag50"]:
        this_run = pooled_results[("old_locked", mag_label)]
        prev = PREVIOUSLY_LOCKED[("old_locked", mag_label)]
        drift = abs(this_run["sensitivity"] - prev["sensitivity"])
        status = "MATCH" if drift < 0.005 else "MISMATCH"
        if status == "MISMATCH":
            any_mismatch = True
        print(f"  {mag_label}: this run sens={this_run['sensitivity']:.4f} (tp={this_run['tp']})  "
             f"vs previously-locked sens={prev['sensitivity']:.4f} (tp={prev['tp']})  "
             f"drift={drift:.4f}  [{status}]")
    if any_mismatch:
        print("\n  [WARNING] old_locked does NOT reproduce the previously-locked figures "
             "exactly through this harness. This means the earlier locked numbers "
             "(e.g. Decision #16's 0.816) came from a DIFFERENT bootstrap-padding "
             "seed state than canonical_seed=0 run through evaluate_subject() -- a "
             "real reproducibility gap in the pipeline, not a mistake in this script. "
             "The NEW-weight numbers below should be compared against THIS RUN's "
             "old_locked row (the fair, same-harness baseline), NOT against the "
             "previously-locked figures directly.")
    else:
        print("\n  [OK] old_locked reproduces the previously-locked figures. The "
             "new-weight numbers below are directly comparable to both this run's "
             "old_locked row AND the previously-locked figures.")

    # ---- honest old-vs-new delta, using THIS RUN's old_locked as the baseline ----
    print("\n" + "=" * 78)
    print("OLD vs NEW WEIGHT, same harness, same canonical_seed=0 (the fair comparison)")
    print("=" * 78)
    for mag_label in ["mag60", "mag50"]:
        old = pooled_results[("old_locked", mag_label)]
        new = pooled_results[("new_decision19", mag_label)]
        d_sens = new["sensitivity"] - old["sensitivity"]
        d_fp = new["fp_per_day"] - old["fp_per_day"]
        print(f"  {mag_label}: old sens={old['sensitivity']:.4f} ({old['tp']}/{old['n_sz']})  "
             f"-> new sens={new['sensitivity']:.4f} ({new['tp']}/{new['n_sz']})   "
             f"Δsens={d_sens:+.4f}   ΔFP/day={d_fp:+.2f}")

    print("\n" + "=" * 78)
    print("NEXT STEP: run stat_validation.py on the new_decision19 files for official CIs:")
    print('  python stat_validation.py --ops '
         '"balanced=szcore_event_level_new_decision19_mag60.csv@1.0;'
         'highsens=szcore_event_level_new_decision19_mag50.csv@1.0"')
    print("=" * 78)


if __name__ == "__main__":
    main()