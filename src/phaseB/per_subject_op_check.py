"""
per_subject_op_check.py — CURSOR CPU. LAST legitimate lever: per-subject label-free FP-budget on rlg.
Each subject picks its OWN cell nearest budget B by ITS interictal FP/day (label-free — no seizure
labels), applied to the FROZEN TEST grid. Compares to a shared OP at the same B on the same grid.
Targets decision-limited subjects (chb16: window AUROC 0.871 but 0 TP at the global OP).
This is the §0 "calibrated" variant (fp_budget_locked.csv), valid on TEST; NOT tuning on labels.

USAGE
  python per_subject_op_check.py --tier2_dir results/phaseB/tier2 --seed 42 --cand rlg
"""
import argparse
from pathlib import Path
import numpy as np, pandas as pd


def reftrue(df):
    out = {}
    for s, g in df.groupby("subject"):
        gg = g[g.sensitivity > 0]
        out[s] = int(round((gg.tp / gg.sensitivity).median())) if len(gg) else int(g.n_seizures.iloc[0])
    return out


def pooled_shared(df, rt, B):
    best = None
    for (m, p), g in df.groupby(["mag_pct", "pen_mult"]):
        TP, FP = int(g.tp.sum()), int(g.fp.sum()); H = float(g.n_inter_h.sum()); fp = FP / (H / 24)
        if best is None or abs(fp - B) < best[0]:
            best = (abs(fp - B), TP, FP, H, m, p)
    _, TP, FP, H, m, p = best; RT = sum(rt.values())
    se = TP / RT; pr = TP / (TP + FP) if TP + FP else 0; f1 = 2 * pr * se / (pr + se) if pr + se else 0
    return se, pr, f1, FP / (H / 24), f"m{int(m)}/p{p}"


def per_subject(df, rt, B):
    TP = FP = 0; H = 0.0; rows = []
    for subj, g in df.groupby("subject"):
        i = (g.fp_per_day - B).abs().idxmin(); r = g.loc[i]   # subject's own cell nearest B (label-free)
        TP += int(r.tp); FP += int(r.fp); H += float(r.n_inter_h)
        rows.append((subj, int(r.tp), int(r.fp), f"m{int(r.mag_pct)}/p{r.pen_mult}"))
    RT = sum(rt.values()); se = TP / RT; pr = TP / (TP + FP) if TP + FP else 0
    f1 = 2 * pr * se / (pr + se) if pr + se else 0
    return se, pr, f1, FP / (H / 24), rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier2_dir", default="results/phaseB/tier2")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--cand", default="rlg")
    a = ap.parse_args()
    tg = pd.read_csv(Path(a.tier2_dir) / f"{a.cand}_test" / f"final_eval_seed{a.seed}.csv")
    rt = reftrue(tg)
    print(f"{'B':>4} | {'SHARED (same-grid nearest)':^30} | {'PER-SUBJECT (label-free)':^26}")
    print(f"{'':>4} | {'sens':>6}{'prec':>6}{'F1':>6}{'FP/d':>6} | {'sens':>6}{'prec':>6}{'F1':>6}{'FP/d':>6}")
    for B in (5, 10, 20, 40):
        ss = pooled_shared(tg, rt, B); ps = per_subject(tg, rt, B)
        print(f"{B:>4} | {ss[0]:>6.3f}{ss[1]:>6.3f}{ss[2]:>6.3f}{ss[3]:>6.1f} | "
              f"{ps[0]:>6.3f}{ps[1]:>6.3f}{ps[2]:>6.3f}{ps[3]:>6.1f}")
    ps = per_subject(tg, rt, 10)
    print("\nPer-subject cells @ B=10: " + "  ".join(f"{s}:{c}(tp{tp})" for s, tp, fp, c in ps[4]))


if __name__ == "__main__":
    main()
