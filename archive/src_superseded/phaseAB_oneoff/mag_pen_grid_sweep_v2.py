"""
================================================================================
 mag_pen_grid_sweep_v2.py  —  CORRECTED re-run of the mag% x pen Pareto grid
================================================================================
WHY THIS FILE (v2) EXISTS
--------------------------
The original mag_pen_grid_sweep.py (written in an earlier chat session, not
preserved in project knowledge) produced Decision #16's numbers (mag60/pen1.0
"balanced" = 0.750/38.0, mag50/pen1.0 "high-sens" = 0.8158/47.97). Those
numbers are the basis for RESULTS_OF_RECORD.md §10 and for the duration-
stratified analysis in §11.

A SEEDING BUG WAS FOUND AND CONFIRMED BY DIRECT EXPERIMENT (2026-07/08):
evaluate_subject() calls build_timeline_masked() internally, which draws from
np.random via `np.random.choice(inter_scores, size=250000, replace=True)` for
bootstrap-padding post-ictal buffer windows. evaluate_subject() does NOT
reseed np.random itself -- it relies on the CALLER seeding before each call.
The original script appears to have seeded np.random ONCE per subject (or
once at the top of the whole run), then looped evaluate_subject() across all
8 mag_pct values for that subject WITHOUT reseeding between mag_pct values.
Because each evaluate_subject() call consumes from the global np.random
stream, the bootstrap-padded timeline for mag_pct=X ends up DIFFERENT
depending on how many mag_pct values were evaluated before it in the loop --
i.e. NOT independently reproducible, and NOT what canonical_seed=0 is
supposed to mean anywhere else in this project.

CONFIRMED BY DIRECT TEST (see chat log, 2026-07/08): calling
evaluate_subject(mag=60) as the FIRST call after seed(0) gives a different
tp than calling it as the 4th call in a sequence of mag values, with the
SAME seed(0) at the very start. This reproduces exactly the kind of drift
observed between the previously-locked mag60 (0.750, smaller drift, likely
called early) and mag50 (0.8158, larger drift, likely called soon after)
figures versus their re-verification through rebuild_ensemble_new_weight.py
(which reseeds before every single evaluate_subject() call and got 0.7105/
0.7500 for the OLD weight at mag60/mag50 respectively).

THE FIX (this script): reseed np.random(canonical_seed) IMMEDIATELY BEFORE
EVERY SINGLE evaluate_subject() call, for every (subject, mag_pct) pair --
never relying on a seed set earlier in the loop to carry over correctly.
This makes every cell in the 48-point grid independently reproducible
regardless of iteration order, matching the convention used everywhere else
in this project (szcore_eval.py's own main(), duration_stratified_
sensitivity.py, rebuild_ensemble_new_weight.py all reseed per-call).

WHAT THIS SCRIPT DOES
----------------------
Full re-run of the 8 mag_pct x 6 pen_mult = 48-combo grid, for BOTH the OLD
locked weight (0.35, 0.30, 0.35) and the NEW Decision #19 weight (0.40, 0.35,
0.25), so:
  1. The OLD-weight grid can be compared against the previously-locked
     Decision #16 figures to quantify exactly how much the seeding bug
     affected them (not just at mag60/mag50, but across the WHOLE grid --
     the Pareto-frontier conclusion itself may need re-checking).
  2. The NEW-weight grid gives the correct, bug-free numbers for Decision
     #19's operating points going forward.

Both weights are rebuilt from cached components (data/processed/components),
NOT from the .npy ensemble score cache (which only exists for whichever
weight was last exported from GPU) -- this guarantees both weights go
through the IDENTICAL harness, the same principle already used in
weight_candidate_crosscheck.py and rebuild_ensemble_new_weight.py.

OUTPUT
------
  mag_pen_grid_v2_pooled.csv       one row per (weight, mag_pct, pen_mult),
                                    pooled/micro sensitivity + FP/day + a
                                    recomputed on_pareto_frontier flag
  mag_pen_grid_v2_persubject.csv   one row per (weight, subject, mag_pct, pen_mult)
  mag_pen_grid_v2_reproducibility_check.csv
                                    OLD-weight grid vs the previously-locked
                                    Decision #16 figures, cell by cell, with
                                    an explicit drift column

USAGE (Cursor / CPU)
  python mag_pen_grid_sweep_v2.py --comp_dir data/processed/components \
      --summary_dir "F:\\...\\summary" --out_dir results/phaseA_appendix

Requires szcore_eval.py, evaluation_protocol.py, cpd_pipeline_v14.py, timescoring.

PERFORMANCE NOTE (lesson from PLAN_AND_STATUS.md's own "Key Learnings"):
PELT's .fit() is cheap; .predict(pen=beta) is the real cost and is called
once per pen_mult inside detect_changepoints, which evaluate_subject()
already handles correctly (loops PEN_MULTS internally around a single
build_timeline_masked() call). This script does NOT re-fit PELT per pen --
it only re-seeds and rebuilds the timeline once per (subject, mag_pct), then
gets all 6 pens from that single evaluate_subject() call, exactly like the
original design intent. Expected runtime: comparable to the original grid
sweep (~4h reported previously) since the per-call cost is unchanged; only
the SEEDING is fixed, not the algorithm's cost profile.
================================================================================
"""
import argparse
import csv
import os
import glob as _glob
import numpy as np

import szcore_eval as SE

TEST_SUBJS = SE.TEST_SUBJS
PEN_MULTS = SE.PEN_MULTS  # [0.3, 0.5, 1.0, 2.0, 5.0, 10.0]
MAG_PCTS = [40.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0]

WEIGHTS = [("old_locked", (0.35, 0.30, 0.35)), ("new_decision19", (0.40, 0.35, 0.25))]

# previously-locked figures (Decision #16, OLD weight only) for the
# reproducibility-check output -- only meaningful for old_locked rows
PREVIOUSLY_LOCKED_OLD = {
    (60.0, 1.0): dict(sensitivity=0.7500, fp_per_day=38.04, tp=57, label="balanced"),
    (50.0, 1.0): dict(sensitivity=0.8158, fp_per_day=47.97, tp=62, label="high-sens (Decision #16)"),
    (70.0, 0.3): dict(sensitivity=0.816, fp_per_day=48.6, tp=62, label="high-sens (superseded pre-#16)"),
}


def load_comp(comp_dir, subj):
    def L(name, split):
        p = os.path.join(comp_dir, f"{name}_{subj}_{split}.npy")
        return np.load(p).astype(np.float64) if os.path.exists(p) else None
    return {k: (L(k, "inter"), L(k, "ictal")) for k in ("zrecon", "ztemp", "zgamma")}


def main():
    ap = argparse.ArgumentParser(description="Corrected (per-call reseeded) mag% x pen grid sweep")
    ap.add_argument("--comp_dir", default="data/processed/components")
    ap.add_argument("--summary_dir", required=True)
    ap.add_argument("--out_dir", default="results/phaseA_appendix")
    ap.add_argument("--canonical_seed", type=int, default=0)
    ap.add_argument("--subjs", default=",".join(TEST_SUBJS))
    ap.add_argument("--local_win", type=int, default=15)
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

    total = len(WEIGHTS) * len(subjs) * len(MAG_PCTS)
    print(f"\n[plan] {len(WEIGHTS)} weights x {len(subjs)} subjects x {len(MAG_PCTS)} "
         f"mag_pct values = {total} evaluate_subject() calls, each internally "
         f"covering all {len(PEN_MULTS)} pen_mult values -> "
         f"{total * len(PEN_MULTS)} (weight,subject,mag,pen) cells total.\n")
    print("[fix] np.random is reseeded to canonical_seed IMMEDIATELY BEFORE "
         "EVERY evaluate_subject() call below -- this is the fix for the "
         "seeding bug described in this file's docstring.\n")

    persubj_rows = []
    done = 0
    for weight_name, (wr, wt, wg) in WEIGHTS:
        for s in subjs:
            zr_i, zr_c = comps[s]["zrecon"]; zt_i, zt_c = comps[s]["ztemp"]; zg_i, zg_c = comps[s]["zgamma"]
            ens_i = wr * zr_i + wt * zt_i + wg * zg_i
            ens_c = wr * zr_c + wt * zt_c + wg * zg_c
            for mag in MAG_PCTS:
                # THE FIX: reseed immediately before this specific call, every time,
                # regardless of how many other (weight, subject, mag) combos ran before it.
                np.random.seed(args.canonical_seed)
                rows = SE.evaluate_subject(s, ens_i, ens_c, args.summary_dir,
                                           min_mag_pct=mag, local_win=args.local_win)
                for r in rows:
                    persubj_rows.append(dict(weight=weight_name, mag_pct=mag, **r))
                done += 1
                r1 = next(r for r in rows if abs(r["pen_mult"] - 1.0) < 1e-9)
                print(f"  [{done}/{total}] {weight_name}/{s}/mag={mag:g}  "
                     f"(pen=1.0: tp={r1['tp']} fp={r1['fp']} sens={r1['sensitivity']:.3f})", flush=True)

    # ---- pooled (micro) aggregation per (weight, mag_pct, pen_mult) ----
    pooled_rows = []
    key_to_rows = {}
    for r in persubj_rows:
        key = (r["weight"], r["mag_pct"], r["pen_mult"])
        key_to_rows.setdefault(key, []).append(r)
    for (weight, mag, pen), rs in key_to_rows.items():
        tp = sum(r["tp"] for r in rs)
        nsz = sum(r["n_seizures"] for r in rs)
        fp = sum(r["fp"] for r in rs); h = sum(r["n_inter_h"] for r in rs)
        sens = tp / nsz if nsz else float("nan")
        fp_day = fp / h * 24 if h else float("nan")
        prec = tp / (tp + fp) if (tp + fp) else float("nan")
        f1 = (2 * prec * sens / (prec + sens)) if (prec and sens) else float("nan")
        pooled_rows.append(dict(weight=weight, mag_pct=mag, pen_mult=pen,
                                TP=tp, FN=nsz - tp, FP=fp, n_seizures=nsz,
                                sensitivity=round(sens, 4), precision=round(prec, 4),
                                f1=round(f1, 4), fp_per_day=round(fp_day, 3)))

    # recompute Pareto frontier per weight (maximize sensitivity, minimize fp_per_day)
    for weight_name, _ in WEIGHTS:
        rows_w = [r for r in pooled_rows if r["weight"] == weight_name]
        for r in rows_w:
            dominated = any(
                (o["sensitivity"] >= r["sensitivity"] and o["fp_per_day"] <= r["fp_per_day"]
                 and (o["sensitivity"] > r["sensitivity"] or o["fp_per_day"] < r["fp_per_day"]))
                for o in rows_w if o is not r)
            r["on_pareto_frontier"] = not dominated

    pooled_path = os.path.join(args.out_dir, "mag_pen_grid_v2_pooled.csv")
    with open(pooled_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(pooled_rows[0].keys())); w.writeheader(); w.writerows(pooled_rows)
    persubj_path = os.path.join(args.out_dir, "mag_pen_grid_v2_persubject.csv")
    with open(persubj_path, "w", newline="") as f:
        fieldnames = ["weight", "mag_pct"] + [k for k in persubj_rows[0].keys()
                                              if k not in ("weight", "mag_pct")]
        w = csv.DictWriter(f, fieldnames=fieldnames); w.writeheader(); w.writerows(persubj_rows)

    # ---- reproducibility check: old_locked grid vs previously-locked Decision #16 figures ----
    print("\n" + "=" * 78)
    print("REPRODUCIBILITY CHECK: old_locked grid (this corrected run) vs "
         "previously-locked figures")
    print("=" * 78)
    check_rows = []
    for (mag, pen), prev in PREVIOUSLY_LOCKED_OLD.items():
        this = next((r for r in pooled_rows
                    if r["weight"] == "old_locked" and abs(r["mag_pct"] - mag) < 1e-9
                    and abs(r["pen_mult"] - pen) < 1e-9), None)
        if this is None:
            print(f"  mag={mag:g}/pen={pen:g} ({prev['label']}): not in this grid, skipped")
            continue
        drift = abs(this["sensitivity"] - prev["sensitivity"])
        status = "MATCH" if drift < 0.005 else "MISMATCH (still drifting)"
        print(f"  mag={mag:g}/pen={pen:g} ({prev['label']}): "
             f"this run sens={this['sensitivity']:.4f} (tp={this['TP']})  vs  "
             f"previously-locked sens={prev['sensitivity']:.4f} (tp={prev['tp']})  "
             f"drift={drift:.4f}  [{status}]")
        check_rows.append(dict(mag_pct=mag, pen_mult=pen, label=prev["label"],
                              this_run_sensitivity=this["sensitivity"], this_run_tp=this["TP"],
                              previously_locked_sensitivity=prev["sensitivity"],
                              previously_locked_tp=prev["tp"], drift=round(drift, 4), status=status))
    check_path = os.path.join(args.out_dir, "mag_pen_grid_v2_reproducibility_check.csv")
    if check_rows:
        with open(check_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(check_rows[0].keys())); w.writeheader(); w.writerows(check_rows)
        print(f"\n  [saved] {os.path.abspath(check_path)}")

    print(f"\n  [saved] {os.path.abspath(pooled_path)}")
    print(f"  [saved] {os.path.abspath(persubj_path)}")
    print("\n  This script does NOT auto-adopt any operating point. Review the "
         "reproducibility check and the Pareto frontier before updating any "
         "locked document.\n")


if __name__ == "__main__":
    main()