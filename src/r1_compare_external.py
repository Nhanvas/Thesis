#!/usr/bin/env python
"""
r1_compare_external.py -- R1 reproducibility check 2 (2026-10-22): compares an external-validation rerun
from a clean clone (x1_external.py run, committed checkpoints, raw EDF) with the committed rows of
results/x1_external/. Reads two folders of rows_<subject>.csv; computes nothing from EEG.

CRITERION (fixed 2026-10-22 before the rerun; never changed after seeing a number). For every subject and
every row (2 operating points x 4 seeds x 2 stages = 16 rows per subject):
  primary   n_ref equal; skipped equal; |hours - hours_ref| <= 0.01; tp equal; |fp - fp_ref| <= 2
  reported  fp difference, budget `top` difference, q_raw difference (descriptive only)
PASS = every primary condition holds on every row. Precedent: PN10 rebuilt on the laptop on 12/10 gave
tp 7 = 7 and fp 17 vs 18 (seed 42, balanced, localized).

  python src/r1_compare_external.py --ref results/r1_repro/committed --new results/r1_repro/rerun --out results/r1_repro
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

KEY = ["subject", "point", "seed", "stage"]
FP_TOL = 2
HOURS_TOL = 0.01


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ref_files = sorted(Path(a.ref).glob("rows_*.csv"))
    if not ref_files:
        raise SystemExit(f"no rows_*.csv in {a.ref}")
    out = []
    for rf in ref_files:
        nf = Path(a.new) / rf.name
        if not nf.exists():
            raise SystemExit(f"STOP: {nf} missing (subject not rerun)")
        R = pd.read_csv(rf).set_index(KEY)
        N = pd.read_csv(nf).set_index(KEY)
        if set(R.index) != set(N.index):
            raise SystemExit(f"STOP: {rf.name}: different rows (point/seed/stage) in the rerun")
        for k in R.index:
            r, n = R.loc[k], N.loc[k]
            row = dict(zip(KEY, k),
                       n_ref=int(r.n_ref), n_ref_new=int(n.n_ref),
                       hours=round(float(r.hours), 4), hours_new=round(float(n.hours), 4),
                       skipped=int(r.skipped), skipped_new=int(n.skipped),
                       tp=int(r.tp), tp_new=int(n.tp), fp=int(r.fp), fp_new=int(n.fp),
                       fp_diff=int(n.fp) - int(r.fp), top_diff=float(n.top) - float(r.top),
                       q_raw_diff=float(n.q_raw) - float(r.q_raw))
            row["pass"] = bool(row["n_ref"] == row["n_ref_new"] and row["skipped"] == row["skipped_new"]
                               and abs(row["hours"] - row["hours_new"]) <= HOURS_TOL
                               and row["tp"] == row["tp_new"] and abs(row["fp_diff"]) <= FP_TOL)
            out.append(row)
    D = pd.DataFrame(out)
    Path(a.out).mkdir(parents=True, exist_ok=True)
    D.to_csv(Path(a.out) / "compare.csv", index=False)
    s42 = D[(D.point == "balanced") & (D.seed == "clean_seed42") & (D.stage == "localized")]
    lines = ["# R1 check 2 -- external rerun from a clean clone vs committed results/x1_external/", "",
             f"Criterion: tp equal, |fp diff| <= {FP_TOL}, n_ref and skipped equal, hours within {HOURS_TOL} h, "
             "on every row (2 points x 4 seeds x 2 stages per subject).", "",
             f"Rows compared: {len(D)}; rows passing: {int(D['pass'].sum())}; "
             f"VERDICT: {'PASS' if D['pass'].all() else 'FAIL'}", "",
             "Seed 42, balanced point, after the localizer:", "", "```",
             s42[["subject", "n_ref", "tp", "tp_new", "fp", "fp_new", "hours", "hours_new", "top_diff"]]
             .to_string(index=False), "```", "",
             "Per subject (all 16 rows): rows with tp equal, max |fp diff|, max |budget diff|:", "", "```",
             D.assign(tp_eq=D.tp == D.tp_new, afp=D.fp_diff.abs(), atop=D.top_diff.abs())
             .groupby("subject").agg(rows=("pass", "size"), passing=("pass", "sum"), tp_equal=("tp_eq", "sum"),
                                     max_abs_fp_diff=("afp", "max"), max_abs_budget_diff=("atop", "max"))
             .to_string(), "```"]
    (Path(a.out) / "COMPARE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    sys.exit(0 if D["pass"].all() else 2)


if __name__ == "__main__":
    main()
