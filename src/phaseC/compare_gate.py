"""
compare_gate.py — Phase C-final, artifact-gate VAL Pareto A/B. numpy only.

Reads two score_ens final_eval CSVs (base rlg vs artifact-gated) and, per subject +
macro, reports sensitivity & event-F1 at matched FP/day budgets. First-look Pareto:
per-subject sens-at-budget then macro-average (a proper pooled SzCORE comparison follows
only if this shows signal). rlg locked refs: F1 0.361 @ 3.6 FP/day; sens 0.632 @ ~38;
0.776 @ ~73.

Usage:
  python src/phaseC/compare_gate.py \
    --base results/phaseC/artifact_gate/scored_base/final_eval_seed42.csv \
    --gate results/phaseC/artifact_gate/scored_gated_iso2/final_eval_seed42.csv
"""
import argparse, csv
from collections import defaultdict

BUDGETS = [3.6, 5.0, 10.0, 38.0, 73.0]


def f1(sn, pr):
    return 2 * sn * pr / (sn + pr) if (sn + pr) > 0 else 0.0


def load(path):
    rows = defaultdict(list)
    with open(path) as f:
        for r in csv.DictReader(f):
            rows[r["subject"]].append(dict(
                sens=float(r["sensitivity"]), prec=float(r["precision"]),
                fp=float(r["fp_per_day"])))
    return rows


def best_at_budget(subj_rows, B):
    """max sensitivity among rows with fp_per_day <= B; return (sens, F1, fp)."""
    ok = [r for r in subj_rows if r["fp"] <= B]
    if not ok:
        return (0.0, 0.0, 0.0)
    r = max(ok, key=lambda x: x["sens"])
    return (r["sens"], f1(r["sens"], r["prec"]), r["fp"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--gate", required=True)
    a = ap.parse_args()
    B, G = load(a.base), load(a.gate)
    subjs = sorted(set(B) & set(G))

    print(f"{'budget':>7s} {'metric':>6s} | " + " ".join(f"{s:>16s}" for s in subjs) + f" | {'MACRO':>14s}")
    for bud in BUDGETS:
        for metric, idx in [("sens", 0), ("F1", 1)]:
            bvals, gvals = [], []
            cells = []
            for s in subjs:
                b = best_at_budget(B[s], bud)[idx]
                g = best_at_budget(G[s], bud)[idx]
                bvals.append(b); gvals.append(g)
                cells.append(f"{b:.3f}->{g:.3f}")
            mb, mg = sum(bvals)/len(bvals), sum(gvals)/len(gvals)
            d = mg - mb
            flag = "  <== gate wins" if d > 0.001 else ("  (gate worse)" if d < -0.001 else "")
            print(f"{bud:7.1f} {metric:>6s} | " + " ".join(f"{c:>16s}" for c in cells) +
                  f" | {mb:.3f}->{mg:.3f} ({d:+.3f}){flag}")
        print()


if __name__ == "__main__":
    main()
