#!/usr/bin/env python3
"""
T1 — VAL-derived operating points (Phase-B), per PREREG_05.

Pipeline:
  1. Pool the VAL mag x pen grid; select OP-F1 (F1-optimal) and OP-5 (~5 FP/day)
     by the COMMITTED rule in PREREG_05 section 3. Freeze + print BEFORE test.
  2. Apply the two frozen (mag,pen) to the 8 TEST subjects ONCE; pooled metrics
     + Wilson (sens/prec) & Poisson (FP/day) 95% CIs; per-subject breakdown.
  3. Dump the full test Pareto frontier.
  4. Print the H1 falsification verdict (test OP-F1 F1 >= 0.30).

Wilson/Poisson CIs are copied verbatim from stat_validation.py (consistent with §0).
Pure decision-layer: no retraining, weights stay equal, algorithm unchanged.
Harness self-check reproduces §0 (mag70/pen0.5 -> 0.632/38.6; mag55/pen0.3 -> 0.776/72.7).
"""
import argparse
import numpy as np
import pandas as pd
from scipy import stats

VAL_SUBJS  = ["chb10", "chb11", "chb22"]
TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]


# ---- CI machinery (verbatim from stat_validation.py) ------------------------
def wilson_ci(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z / denom) * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, center - half), min(1.0, center + half))


def poisson_rate_ci(k, exposure_days, alpha=0.05):
    lo = stats.chi2.ppf(alpha / 2, 2 * k) / 2 if k > 0 else 0.0
    hi = stats.chi2.ppf(1 - alpha / 2, 2 * k + 2) / 2
    return (lo / exposure_days, hi / exposure_days)


# ---- pooling ----------------------------------------------------------------
def pool_cell(sub):
    """Pool a set of per-subject rows sharing one (mag,pen)."""
    TP = int(sub.tp.sum()); FP = int(sub.fp.sum())
    N = int(sub.n_seizures.sum()); H = float(sub.n_inter_h.sum())
    sens = TP / N if N else 0.0
    prec = TP / (TP + FP) if (TP + FP) else 0.0
    f1 = 2 * prec * sens / (prec + sens) if (prec + sens) else 0.0
    fpd = FP / H * 24 if H else float("nan")
    return dict(TP=TP, FP=FP, N=N, H=H, sensitivity=sens, precision=prec,
                f1=f1, fp_per_day=fpd)


def pooled_grid(df, subjects):
    df = df[df.subject.isin(subjects)]
    rows = []
    for (mag, pen), sub in df.groupby(["mag_pct", "pen_mult"]):
        r = pool_cell(sub); r["mag_pct"] = mag; r["pen_mult"] = pen
        rows.append(r)
    return pd.DataFrame(rows).sort_values(["mag_pct", "pen_mult"]).reset_index(drop=True)


def mark_pareto(g):
    """maximize sensitivity, minimize fp_per_day."""
    keep = []
    for _, r in g.iterrows():
        dominated = ((g.sensitivity >= r.sensitivity) & (g.fp_per_day <= r.fp_per_day) &
                     ((g.sensitivity > r.sensitivity) | (g.fp_per_day < r.fp_per_day))).any()
        keep.append(not dominated)
    g = g.copy(); g["on_pareto_frontier"] = keep
    return g


# ---- COMMITTED selection rule (PREREG_05 §3) --------------------------------
def select_op_f1(g):
    # argmax F1; tie -> higher sens, lower fpd, lower mag, lower pen
    cand = g.sort_values(
        by=["f1", "sensitivity", "fp_per_day", "mag_pct", "pen_mult"],
        ascending=[False, False, True, True, True]).iloc[0]
    return cand


def select_op_5(g, budget=5.0):
    within = g[g.fp_per_day <= budget]
    fallback = within.empty
    pool = g[g.fp_per_day > budget] if fallback else within
    if fallback:
        # closest to 5 from above == smallest fpd among cells > 5
        cand = pool.sort_values(
            by=["fp_per_day", "sensitivity", "mag_pct", "pen_mult"],
            ascending=[True, False, True, True]).iloc[0]
    else:
        # max sensitivity within budget; tie -> higher F1, lower fpd, lower mag/pen
        cand = pool.sort_values(
            by=["sensitivity", "f1", "fp_per_day", "mag_pct", "pen_mult"],
            ascending=[False, False, True, True, True]).iloc[0]
    return cand, fallback


# ---- reporting --------------------------------------------------------------
def report_point(df, subjects, mag, pen, label):
    sub = df[(df.subject.isin(subjects)) & (df.mag_pct == mag) & (df.pen_mult == pen)]
    p = pool_cell(sub)
    s_lo, s_hi = wilson_ci(p["TP"], p["N"])
    pr_lo, pr_hi = wilson_ci(p["TP"], p["TP"] + p["FP"]) if (p["TP"] + p["FP"]) else (float("nan"),) * 2
    days = p["H"] / 24.0
    f_lo, f_hi = poisson_rate_ci(p["FP"], days)
    print(f"\n[{label}]  mag{mag:g}/pen{pen:g}")
    print(f"  TP/FN/FP = {p['TP']}/{p['N']-p['TP']}/{p['FP']}  (N_sz={p['N']}, interictal_h={p['H']:.1f})")
    print(f"  sensitivity = {p['sensitivity']:.3f}  Wilson95 [{s_lo:.3f}, {s_hi:.3f}]")
    print(f"  precision   = {p['precision']:.3f}  Wilson95 [{pr_lo:.3f}, {pr_hi:.3f}]")
    print(f"  F1          = {p['f1']:.3f}")
    print(f"  FP/day      = {p['fp_per_day']:.2f}  Poisson95 [{f_lo:.2f}, {f_hi:.2f}]")
    per = []
    for s in subjects:
        ss = sub[sub.subject == s]
        if len(ss):
            r = pool_cell(ss); r["subject"] = s; r["mag_pct"] = mag; r["pen_mult"] = pen
            r["operating_point"] = label; per.append(r)
    return dict(operating_point=label, mag_pct=mag, pen_mult=pen, **p,
                sensitivity_CI=f"[{s_lo:.3f}, {s_hi:.3f}]",
                precision_CI=f"[{pr_lo:.3f}, {pr_hi:.3f}]",
                fp_per_day_CI=f"[{f_lo:.2f}, {f_hi:.2f}]"), per


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--val_csv", default="results/retrain_v3p1/val/final_eval_seed42.csv")
    ap.add_argument("--test_csv", default="results/retrain_v3p1/final_eval_seed42.csv")
    ap.add_argument("--out_prefix", default="results/retrain_v3p1/t1_")
    ap.add_argument("--budget", type=float, default=5.0)
    args = ap.parse_args()

    val = pd.read_csv(args.val_csv)
    test = pd.read_csv(args.test_csv)

    # ---- harness self-check: reproduce §0 on test (Guardrail §8.4) -----------
    for (mg, pn, es, ef) in [(70.0, 0.5, 0.632, 38.6), (55.0, 0.3, 0.776, 72.7)]:
        c = pool_cell(test[(test.subject.isin(TEST_SUBJS)) & (test.mag_pct == mg) & (test.pen_mult == pn)])
        ok = abs(c["sensitivity"] - es) < 0.002 and abs(c["fp_per_day"] - ef) < 0.3
        print(f"[selfcheck §0] mag{mg:g}/pen{pn:g}: sens={c['sensitivity']:.3f} fpd={c['fp_per_day']:.1f} "
              f"-> {'OK' if ok else 'MISMATCH'}")
        assert ok, "Harness does not reproduce §0 — abort (Guardrail 8.4)."

    # ---- STEP 1: derive on VAL, freeze, print BEFORE touching test -----------
    print("\n" + "=" * 70 + "\nSTEP 1 — VAL derivation (chb10, chb11, chb22)\n" + "=" * 70)
    gval = mark_pareto(pooled_grid(val, VAL_SUBJS))
    op_f1 = select_op_f1(gval)
    op_5, fb = select_op_5(gval, args.budget)
    print(f"OP-F1 (VAL argmax F1): mag{op_f1.mag_pct:g}/pen{op_f1.pen_mult:g} | "
          f"VAL F1={op_f1.f1:.3f} sens={op_f1.sensitivity:.3f} prec={op_f1.precision:.3f} fpd={op_f1.fp_per_day:.1f}")
    print(f"OP-5  (VAL <= {args.budget:g} FP/day, max sens){'  [FALLBACK]' if fb else ''}: "
          f"mag{op_5.mag_pct:g}/pen{op_5.pen_mult:g} | "
          f"VAL sens={op_5.sensitivity:.3f} F1={op_5.f1:.3f} fpd={op_5.fp_per_day:.1f}")
    frozen = {"OP-F1_val_derived": (op_f1.mag_pct, op_f1.pen_mult),
              "OP-5_val_derived": (op_5.mag_pct, op_5.pen_mult)}
    print("FROZEN operating points:", frozen)
    gval.to_csv(f"{args.out_prefix}val_pooled_grid.csv", index=False)

    # ---- STEP 2: one-shot test application -----------------------------------
    print("\n" + "=" * 70 + "\nSTEP 2 — one-shot TEST application (8 held-out subjects)\n" + "=" * 70)
    summary, per_all = [], []
    for label, (mag, pen) in frozen.items():
        row, per = report_point(test, TEST_SUBJS, mag, pen, label)
        summary.append(row); per_all.extend(per)

    print("\n  per-subject @ OP-F1:")
    for r in per_all:
        if r["operating_point"] == "OP-F1_val_derived":
            print(f"    {r['subject']}: sens={r['sensitivity']:.3f} prec={r['precision']:.3f} "
                  f"F1={r['f1']:.3f} TP/FP={r['TP']}/{r['FP']} fpd={r['fp_per_day']:.1f}")

    # ---- STEP 3: full test Pareto frontier -----------------------------------
    gtest = mark_pareto(pooled_grid(test, TEST_SUBJS))
    front = gtest[gtest.on_pareto_frontier].sort_values("fp_per_day")
    print("\n  TEST Pareto frontier (sens vs FP/day):")
    print("    mag/pen      sens   prec   F1     FP/day")
    for _, r in front.iterrows():
        print(f"    mag{r.mag_pct:g}/pen{r.pen_mult:g}   {r.sensitivity:.3f}  {r.precision:.3f}  "
              f"{r.f1:.3f}  {r.fp_per_day:.1f}")
    gtest.to_csv(f"{args.out_prefix}test_pooled_grid.csv", index=False)
    pd.DataFrame(summary).to_csv(f"{args.out_prefix}selected_points_test.csv", index=False)
    pd.DataFrame(per_all).to_csv(f"{args.out_prefix}per_subject_test.csv", index=False)

    # ---- STEP 4: falsification verdict ---------------------------------------
    f1_test = [r for r in summary if r["operating_point"] == "OP-F1_val_derived"][0]["f1"]
    on_ridge = (op_f1.pen_mult == 5.0) and (65.0 <= op_f1.mag_pct <= 80.0)
    print("\n" + "=" * 70 + "\nSTEP 4 — H1 falsification verdict\n" + "=" * 70)
    print(f"  §0 balanced F1 = 0.168  ->  T1 OP-F1 test F1 = {f1_test:.3f}")
    print(f"  H1 (test OP-F1 F1 >= 0.30): {'CONFIRMED' if f1_test >= 0.30 else 'FALSIFIED'}")
    print(f"  Transfer sanity — VAL cell on the pen=5/mag65-80 ridge? {on_ridge}")
    print(f"\n  Wrote: {args.out_prefix}{{val_pooled_grid,test_pooled_grid,selected_points_test,per_subject_test}}.csv")


if __name__ == "__main__":
    main()
