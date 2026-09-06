"""
score_alternatives.py — apply the pre-registered per-subject FP-budget operating
point rule to the incumbent and to every design alternative, at one budget ladder.

WHY THIS EXISTS
  Each alternative has a committed 48-cell (magnitude x penalty) grid, but the
  event-tier numbers that decide pass or fail were never written to a single
  file. Reading a cell straight out of a grid is not the pipeline's rule: the
  rule selects a different cell per subject to meet a false-alarm budget, then
  pools. This script applies that rule, unchanged, to every grid, so the
  alternatives table is built from one reproducible procedure.

  The selection functions are imported from fp_budget_operating_point (the
  PREREG_04 implementation). Nothing about the rule is reimplemented here; the
  only addition is the budget ladder, taken from the committed summary rather
  than chosen now.

USAGE
  python src/phaseB/score_alternatives.py --manifest alternatives.txt
  python src/phaseB/score_alternatives.py --smoke

  manifest: one entry per line, "<label>|<tab-or-comma>|<path to grid csv>"
            lines starting with # are ignored. The FIRST entry is the incumbent;
            every other row is reported as a difference from it.

OUTPUT
  results/phaseB/tier2/alternatives/alternatives_operating_points.csv
      one row per (variant, budget): sensitivity, precision, F1, FP/day, TP, FP
  results/phaseB/tier2/alternatives/alternatives_vs_incumbent.csv
      one row per variant at the headline budget, with the difference in F1
"""
import os as _os
import sys as _sys

_here = _os.path.dirname(_os.path.abspath(__file__))
for _p in (_here, _os.path.dirname(_here),
           _os.path.join(_os.path.dirname(_here), "retrain")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import argparse
import csv
from pathlib import Path

import fp_budget_operating_point as OP

# Budget ladder as used for the committed summary table. The first entry is the
# headline: it is the budget at which every design alternative was gated.
BUDGETS = [5.0, 10.0, 20.0, 40.0, 75.0]
HEADLINE_BUDGET = 5.0

DEFAULT_OUT_DIR = Path("results/phaseB/tier2/alternatives")


def score_one(csv_path: Path, budgets) -> dict:
    """Returns {budget: pooled metrics dict} for one grid file."""
    rows = OP.load_rows(str(csv_path))
    subjects = sorted({r["subject"] for r in rows})
    out = {}
    for b in budgets:
        ref = OP.pooled_shared_nearest(rows, b)          # shared reference cell
        ref = {"mag_pct": float(ref["mag_pct"]), "pen_mult": float(ref["pen_mult"])}
        sel, pooled = OP.calibrate(rows, b, ref)
        cells = ",".join(f"{r['subject']}:m{r['mag_pct']:.0f}/p{r['pen_mult']}"
                         for r in sel)
        out[b] = {"sensitivity": pooled["sensitivity"],
                  "precision": pooled["precision"],
                  "f1": pooled["f1"],
                  "fp_per_day": pooled["fp_per_day"],
                  "TP": pooled["TP"], "FP": pooled["FP"],
                  "n_seizures": pooled["n_seizures"],
                  "n_subjects": len(subjects),
                  "reference_cell": f"m{ref['mag_pct']:.0f}/p{ref['pen_mult']}",
                  "per_subject_cells": cells}
    return out


def read_manifest(path: Path):
    entries = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2:
            raise SystemExit(f"bad manifest line (need 'label | path'): {line}")
        entries.append((parts[0], Path(parts[-1])))
    if not entries:
        raise SystemExit("manifest is empty")
    return entries


def run(manifest: Path, out_dir: Path, budgets, headline: float) -> None:
    entries = read_manifest(manifest)
    out_dir.mkdir(parents=True, exist_ok=True)

    scored = {}
    for label, path in entries:
        if not path.exists():
            raise SystemExit(f"missing grid file for '{label}': {path}")
        scored[label] = score_one(path, budgets)
        print(f"[scored] {label:<34} {path}")

    long_path = out_dir / "alternatives_operating_points.csv"
    fields = ["variant", "budget_fp_per_day", "n_subjects", "n_seizures",
              "sensitivity", "precision", "f1", "fp_per_day", "TP", "FP",
              "reference_cell", "per_subject_cells"]
    with open(long_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for label, _ in entries:
            for b in budgets:
                r = dict(scored[label][b])
                r["variant"] = label
                r["budget_fp_per_day"] = b
                w.writerow({k: r[k] for k in fields})

    incumbent = entries[0][0]
    base = scored[incumbent][headline]
    cmp_path = out_dir / "alternatives_vs_incumbent.csv"
    with open(cmp_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["variant", "sensitivity", "precision", "f1", "fp_per_day",
                    "delta_f1_vs_incumbent", "delta_sensitivity_vs_incumbent"])
        for label, _ in entries:
            r = scored[label][headline]
            w.writerow([label, r["sensitivity"], r["precision"], r["f1"],
                        r["fp_per_day"],
                        round(r["f1"] - base["f1"], 4),
                        round(r["sensitivity"] - base["sensitivity"], 4)])

    print(f"\n--- at the headline budget ({headline:g} FP/day target) ---")
    print(f"{'variant':<34}{'sens':>8}{'prec':>8}{'F1':>8}{'FP/day':>9}{'dF1':>9}")
    for label, _ in entries:
        r = scored[label][headline]
        print(f"{label:<34}{r['sensitivity']:>8.3f}{r['precision']:>8.3f}"
              f"{r['f1']:>8.3f}{r['fp_per_day']:>9.1f}"
              f"{r['f1'] - base['f1']:>9.3f}")
    print(f"\n[saved] {long_path}")
    print(f"[saved] {cmp_path}")


def smoke() -> None:
    for fn in ("load_rows", "pooled_shared_nearest", "calibrate", "pooled_ci"):
        assert hasattr(OP, fn), f"fp_budget_operating_point is missing {fn}"
    print(f"smoke OK: rule imported, budgets {BUDGETS}, headline {HEADLINE_BUDGET}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="alternatives.txt")
    ap.add_argument("--out_dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--headline", type=float, default=HEADLINE_BUDGET)
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    if a.smoke:
        smoke()
        return
    run(Path(a.manifest), Path(a.out_dir), BUDGETS, a.headline)


if __name__ == "__main__":
    main()
