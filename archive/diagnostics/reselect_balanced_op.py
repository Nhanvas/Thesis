#!/usr/bin/env python3
"""
Balanced multi-metric operating-point re-selection (Phase-B), per PREREG_06.
Supersedes the argmax-F1 objective of T1/PREREG_05.

Knob-free balanced headline (min|sens-prec| on the VAL Pareto frontier) + two
SzCORE-convention FP-budget points (~5, ~10 FP/day). VAL-derived, frozen, one-shot test.
Correct SzCORE denominator (per-subject reference-event count backed out from the
scorer's sensitivity column). Harness reproduces §0 before use.
"""
import numpy as np, pandas as pd
from scipy import stats

VAL_SUBJS  = ["chb10", "chb11", "chb22"]
TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
SOTA = dict(sens=0.37, prec_lo=0.29, prec_hi=0.45, f1_lo=0.32, f1_hi=0.43)


def wilson_ci(k, n, z=1.96):
    if n == 0: return (float("nan"), float("nan"))
    p = k/n; d = 1+z*z/n
    c = (p+z*z/(2*n))/d; h = (z/d)*np.sqrt(p*(1-p)/n+z*z/(4*n*n))
    return (max(0.0, c-h), min(1.0, c+h))


def poisson_rate_ci(k, days, a=0.05):
    lo = stats.chi2.ppf(a/2, 2*k)/2 if k > 0 else 0.0
    hi = stats.chi2.ppf(1-a/2, 2*k+2)/2
    return (lo/days, hi/days)


def ref_events(df):
    """Authoritative per-subject SzCORE reference-event count (not n_seizures)."""
    out = {}
    for s in df.subject.unique():
        c = df[(df.subject == s) & (df.sensitivity > 0)]
        out[s] = int(round((c.tp/c.sensitivity).median())) if len(c) else int(df[df.subject == s].n_seizures.iloc[0])
    return out


def pooled_grid(df, subjects, refmap):
    df = df[df.subject.isin(subjects)]
    rows = []
    for (mag, pen), sub in df.groupby(["mag_pct", "pen_mult"]):
        TP = int(sub.tp.sum()); FP = int(sub.fp.sum())
        N = sum(refmap[s] for s in sub.subject); H = float(sub.n_inter_h.sum())
        sens = TP/N if N else 0.0; prec = TP/(TP+FP) if TP+FP else 0.0
        f1 = 2*prec*sens/(prec+sens) if prec+sens else 0.0
        rows.append(dict(mag_pct=mag, pen_mult=pen, TP=TP, FP=FP, N=N, H=H,
                         sensitivity=sens, precision=prec, f1=f1, fp_per_day=FP/H*24 if H else np.nan))
    return pd.DataFrame(rows)


def mark_pareto(g):
    keep = []
    for _, r in g.iterrows():
        dom = ((g.sensitivity >= r.sensitivity) & (g.fp_per_day <= r.fp_per_day) &
               ((g.sensitivity > r.sensitivity) | (g.fp_per_day < r.fp_per_day))).any()
        keep.append(not dom)
    g = g.copy(); g["front"] = keep
    return g


def report(df, subjects, refmap, mag, pen, label):
    sub = df[(df.subject.isin(subjects)) & (df.mag_pct == mag) & (df.pen_mult == pen)]
    TP = int(sub.tp.sum()); FP = int(sub.fp.sum())
    N = sum(refmap[s] for s in sub.subject); H = float(sub.n_inter_h.sum())
    sens = TP/N; prec = TP/(TP+FP) if TP+FP else 0.0
    f1 = 2*prec*sens/(prec+sens) if prec+sens else 0.0; fpd = FP/H*24
    s_ci = wilson_ci(TP, N); p_ci = wilson_ci(TP, TP+FP); f_ci = poisson_rate_ci(FP, H/24)
    # SOTA proportionality flags
    flags = []
    flags.append(("sens", sens, "OK" if sens >= 0.35 else "BELOW SOTA"))
    flags.append(("prec", prec, "OK" if prec >= SOTA["prec_lo"] else "BELOW SOTA"))
    flags.append(("F1", f1, "OK" if f1 >= 0.30 else "BELOW SOTA"))
    flags.append(("FP/day", fpd, "OK" if fpd <= 10 else "HIGH"))
    print(f"\n[{label}] mag{mag:g}/pen{pen:g}  TP/FN/FP={TP}/{N-TP}/{FP}")
    print(f"  sens={sens:.3f} [{s_ci[0]:.3f},{s_ci[1]:.3f}] | prec={prec:.3f} [{p_ci[0]:.3f},{p_ci[1]:.3f}] "
          f"| F1={f1:.3f} | FP/day={fpd:.2f} [{f_ci[0]:.2f},{f_ci[1]:.2f}]")
    print("  SOTA check: " + " | ".join(f"{n}={v:.3f}:{s}" for n, v, s in flags))
    return dict(label=label, mag=mag, pen=pen, sens=sens, prec=prec, f1=f1, fpd=fpd,
                TP=TP, FN=N-TP, FP=FP)


def main():
    val = pd.read_csv("val_grid.csv"); test = pd.read_csv("test_grid.csv")
    rt = ref_events(test); rv = ref_events(val)
    print("VAL ref-events:", rv, "| TEST ref-events:", rt)

    # harness self-check vs §0 (test uses n_seizures==ref so pooled sens matches)
    gt0 = pooled_grid(test, TEST_SUBJS, rt)
    for mg, pn, es in [(70.0, 0.5, 0.632), (55.0, 0.3, 0.776)]:
        c = gt0[(gt0.mag_pct == mg) & (gt0.pen_mult == pn)].iloc[0]
        assert abs(c.sensitivity-es) < 0.003, f"selfcheck fail {mg}/{pn}"
    print("[selfcheck §0] pooled sens 0.632 / 0.776 reproduced -> OK")

    # ---- VAL derivation (frozen before test) ----
    gv = mark_pareto(pooled_grid(val, VAL_SUBJS, rv))
    fr = gv[gv.front].copy()
    fr["imbal"] = (fr.sensitivity - fr.precision).abs()
    p_bal = fr.sort_values(["imbal", "f1", "sensitivity", "fp_per_day", "mag_pct", "pen_mult"],
                           ascending=[True, False, False, True, True, True]).iloc[0]
    def nearest(fr, tgt):
        fr = fr.copy(); fr["d"] = (fr.fp_per_day-tgt).abs()
        return fr.sort_values(["d", "sensitivity", "mag_pct", "pen_mult"],
                              ascending=[True, False, True, True]).iloc[0]
    p5 = nearest(fr, 5.0); p10 = nearest(fr, 10.0)
    print("\n=== VAL frozen points ===")
    print(f"  P_balanced (min|sens-prec|): mag{p_bal.mag_pct:g}/pen{p_bal.pen_mult:g} "
          f"(VAL sens={p_bal.sensitivity:.3f} prec={p_bal.precision:.3f} f1={p_bal.f1:.3f} fpd={p_bal.fp_per_day:.1f})")
    print(f"  P_fp5:  mag{p5.mag_pct:g}/pen{p5.pen_mult:g} (VAL fpd={p5.fp_per_day:.1f})")
    print(f"  P_fp10: mag{p10.mag_pct:g}/pen{p10.pen_mult:g} (VAL fpd={p10.fp_per_day:.1f})")
    frozen = [("P_balanced", p_bal.mag_pct, p_bal.pen_mult),
              ("P_fp5", p5.mag_pct, p5.pen_mult), ("P_fp10", p10.mag_pct, p10.pen_mult)]

    # ---- one-shot test ----
    print("\n=== ONE-SHOT TEST ===")
    summ = [report(test, TEST_SUBJS, rt, m, p, lab) for lab, m, p in frozen]

    # per-subject at P_balanced
    m, p = frozen[0][1], frozen[0][2]
    print(f"\n  per-subject @ P_balanced (mag{m:g}/pen{p:g}):")
    for s in TEST_SUBJS:
        r = test[(test.subject == s) & (test.mag_pct == m) & (test.pen_mult == p)].iloc[0]
        prec = r.tp/(r.tp+r.fp) if r.tp+r.fp else 0
        f1 = 2*prec*r.sensitivity/(prec+r.sensitivity) if prec+r.sensitivity else 0
        print(f"    {s}: sens={r.sensitivity:.3f} prec={prec:.3f} F1={f1:.3f} TP/FP={int(r.tp)}/{int(r.fp)}")

    pd.DataFrame(summ).to_csv("reselect_points_test.csv", index=False)
    print("\n  wrote reselect_points_test.csv")


if __name__ == "__main__":
    main()
