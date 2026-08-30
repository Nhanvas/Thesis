"""
c1_lowfp_compare.py — CURSOR CPU (Phase C). NO new compute; reads existing VAL grids.

The G2 gate lives at B=40 FP/day where precision is structurally ~0.07 — NOT where the
thesis headline lives. The reported rlg headline is the LOW-FP triage point
(F1 0.361 @ 3.6 FP/day on TEST). This tool asks the decision-relevant question on VAL:
at the low-FP triage region, does any challenger raise POOLED event F1 over rlg, or is
the headline unchanged (decision-layer exhausted -> go representational)?

Pooling is SzCORE-correct and REUSED verbatim from g2_val_gate (reftrue / pooled_cell /
shared_at_budget): pooled sens = Σtp/Σref, prec = Σtp/Σ(tp+fp), F1 from those, fp/day =
Σfp / Σinter-days. refTrue is ensemble-invariant -> taken once from the rlg baseline grid.

USAGE (Cursor)
  python src/phaseC/c1_lowfp_compare.py --seed 42 \
    --grids "rlg=results/phaseC/c1/rlg_ma15/final_eval_seed42.csv,\
rltg_te=results/phaseC/c4lite/rltg_te/final_eval_seed42.csv,\
median9=results/phaseC/c1/rlg_median9/final_eval_seed42.csv,\
median15=results/phaseC/c1/rlg_median15/final_eval_seed42.csv"
Smoke:
  python src/phaseC/c1_lowfp_compare.py --smoke
"""
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
_src = _os.path.dirname(_here)
for _p in (_src, _here, _os.path.join(_src, "phaseB")):
    if _os.path.isdir(_p) and _p not in _sys.path:
        _sys.path.insert(0, _p)

import argparse
from pathlib import Path
import numpy as np
import pandas as pd

from g2_val_gate import reftrue, pooled_cell, shared_at_budget   # single-source pooling


def best_f1_lowfp(df, rt, cap):
    """Pooled cell with the highest F1 among cells with fp/day <= cap."""
    best = None
    for (m, p), g in df.groupby(["mag_pct", "pen_mult"]):
        c = pooled_cell(g, rt)
        if c["fpday"] <= cap and (best is None or c["f1"] > best["f1"]):
            c["mag"], c["pen"] = m, p; best = c
    return best


def lowfp_pareto(df, rt, cap):
    """Non-dominated (max sens, min fp/day) cells with fp/day <= cap."""
    cells = []
    for (m, p), g in df.groupby(["mag_pct", "pen_mult"]):
        c = pooled_cell(g, rt)
        if c["fpday"] <= cap:
            c["mag"], c["pen"] = m, p; cells.append(c)
    par = []
    for c in cells:
        if not any(o is not c and o["sens"] >= c["sens"] and o["fpday"] <= c["fpday"]
                   and (o["sens"] > c["sens"] or o["fpday"] < c["fpday"]) for o in cells):
            par.append(c)
    return sorted(par, key=lambda c: c["fpday"])


def _fmt(c):
    return (f"m{int(c['mag'])}/p{c['pen']}" if c else "-",
            c["sens"] if c else float("nan"), c["prec"] if c else float("nan"),
            c["f1"] if c else float("nan"), c["fpday"] if c else float("nan"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--grids", default=None, help="comma list tag=csvpath")
    ap.add_argument("--budgets", default="3.6,5.0", help="matched FP/day budgets to compare F1 at")
    ap.add_argument("--cap", type=float, default=5.0, help="low-FP region ceiling")
    ap.add_argument("--baseline", default="rlg", help="tag used as the reference (refTrue + Δ)")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()

    if a.smoke:
        # two synthetic grids: 'chal' shifts one FP off at a low-FP cell vs 'base'
        rows = []
        for tag, dfp in (("base", 0), ("chal", -1)):
            for subj, rt_ in (("chb10", 7), ("chb11", 5), ("chb22", 3)):
                for m in (70, 80):
                    for p in (0.5, 2.0):
                        tp = 2; fp = (5 if (m == 80 and p == 2.0) else 30) + (dfp if tag == "chal" else 0)
                        rows.append(dict(seed=42, subject=subj, mag_pct=m, pen_mult=p, tp=tp,
                                         fp=max(fp, 0), n_seizures=rt_, n_inter_h=100.0,
                                         sensitivity=tp / rt_, precision=tp / (tp + max(fp, 0)),
                                         fp_per_day=max(fp, 0) / (100 / 24), window_auroc=0.9, _tag=tag))
        df = pd.DataFrame(rows)
        grids = {t: df[df._tag == t].drop(columns="_tag") for t in ("base", "chal")}
        rt = reftrue(grids["base"])
        for t, g in grids.items():
            b = best_f1_lowfp(g, rt, 5.0)
            print(f"[SMOKE] {t}: best-F1@≤5fp {_fmt(b)}")
        print("[SMOKE] PASS")
        return

    pairs = [kv.split("=", 1) for kv in a.grids.split(",")] if a.grids else []
    grids = {t.strip(): pd.read_csv(p.strip()) for t, p in pairs}
    if a.baseline not in grids:
        raise SystemExit(f"baseline '{a.baseline}' not in {list(grids)}")
    rt = reftrue(grids[a.baseline])
    print(f"[refTrue] {rt}  (Σ={sum(rt.values())})   low-FP region: fp/day ≤ {a.cap}")

    budgets = [float(x) for x in a.budgets.split(",")]
    # matched-budget F1 comparison (the headline question)
    for B in budgets:
        print(f"\n=== pooled cell nearest B={B} FP/day (matched-budget F1) ===")
        print(f"{'candidate':10}{'cell':>12}{'sens':>7}{'prec':>7}{'F1':>7}{'FP/d':>7}{'ΔF1 vs base':>12}")
        baseF1 = shared_at_budget(grids[a.baseline], rt, B)["f1"]
        for t, g in grids.items():
            c = shared_at_budget(g, rt, B); cell, s, pr, f1, fp = _fmt(c)
            d = "" if t == a.baseline else f"{f1 - baseF1:+.3f}"
            print(f"{t:10}{cell:>12}{s:7.3f}{pr:7.3f}{f1:7.3f}{fp:7.1f}{d:>12}")

    # best achievable F1 in the whole low-FP region
    print(f"\n=== best pooled F1 with fp/day ≤ {a.cap} (best-case low-FP) ===")
    print(f"{'candidate':10}{'cell':>12}{'sens':>7}{'prec':>7}{'F1':>7}{'FP/d':>7}")
    for t, g in grids.items():
        cell, s, pr, f1, fp = _fmt(best_f1_lowfp(g, rt, a.cap))
        print(f"{t:10}{cell:>12}{s:7.3f}{pr:7.3f}{f1:7.3f}{fp:7.1f}")

    # low-FP Pareto frontier for the baseline vs each challenger (shape check)
    print(f"\n=== low-FP Pareto (sens↑, fp/day↓ ≤ {a.cap}) ===")
    for t, g in grids.items():
        fr = lowfp_pareto(g, rt, a.cap)
        pts = " ".join(f"({c['sens']:.2f}@{c['fpday']:.1f},F1={c['f1']:.3f})" for c in fr)
        print(f"  {t:10}: {pts}")


if __name__ == "__main__":
    main()
