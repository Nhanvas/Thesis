#!/usr/bin/env python3
"""
Per-subject label-free FP-budget operating point (Phase-B), per PREREG_07.

Selection uses ONLY interictal quantities (fp, n_inter_h) per subject -> label-free.
Sensitivity/TP are read off AFTER selection, never used to select (asserted).
Grid version (reportable): discrete mag in {40..80}. Optional .npy refinement noted in PREREG_07 s6.
"""
import numpy as np, pandas as pd
from scipy import stats

TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
SHARED = dict(mag=80.0, pen=5.0, sens=0.395, prec=0.316, f1=0.351, fpd=5.61)  # RESELECT headline


def wilson_ci(k, n, z=1.96):
    if n == 0: return (float("nan"),) * 2
    p = k/n; d = 1+z*z/n
    c = (p+z*z/(2*n))/d; h = (z/d)*np.sqrt(p*(1-p)/n+z*z/(4*n*n))
    return (max(0.0, c-h), min(1.0, c+h))


def poisson_rate_ci(k, days, a=0.05):
    lo = stats.chi2.ppf(a/2, 2*k)/2 if k > 0 else 0.0
    hi = stats.chi2.ppf(1-a/2, 2*k+2)/2
    return (lo/days, hi/days)


def ref_events(df):
    out = {}
    for s in df.subject.unique():
        c = df[(df.subject == s) & (df.sensitivity > 0)]
        out[s] = int(round((c.tp/c.sensitivity).median())) if len(c) else int(df[df.subject == s].n_seizures.iloc[0])
    return out


def select_cell_label_free(sub_rows, B):
    """PREREG_07 s2. Input MUST expose only interictal columns for selection."""
    sub = sub_rows.copy()
    sub["fpd"] = sub.fp / sub.n_inter_h * 24
    within = sub[sub.fpd <= B]
    if within.empty:
        pick = sub.sort_values(["fpd", "mag_pct", "pen_mult"]).iloc[0]        # tightest
    else:
        pick = within.sort_values(["fpd", "mag_pct", "pen_mult"],
                                  ascending=[False, True, True]).iloc[0]       # spend budget
    return pick.mag_pct, pick.pen_mult


def run_budget(df, refmap, B):
    rows = []; TP = FP = 0; N = 0; H = 0.0
    for s in TEST_SUBJS:
        d = df[df.subject == s]
        # selection sees only interictal columns
        mag, pen = select_cell_label_free(d[["mag_pct", "pen_mult", "fp", "n_inter_h"]], B)
        r = d[(d.mag_pct == mag) & (d.pen_mult == pen)].iloc[0]  # now read off TP/sens
        tp, fp, ref, h = int(r.tp), int(r.fp), refmap[s], float(r.n_inter_h)
        sens = tp/ref; prec = tp/(tp+fp) if tp+fp else 0.0
        f1 = 2*prec*sens/(prec+sens) if prec+sens else 0.0
        rows.append(dict(subject=s, mag=mag, pen=pen, tp=tp, fp=fp, ref=ref,
                         sens=sens, prec=prec, f1=f1, fpd=fp/h*24))
        TP += tp; FP += fp; N += ref; H += h
    sens = TP/N; prec = TP/(TP+FP) if TP+FP else 0.0
    f1 = 2*prec*sens/(prec+sens) if prec+sens else 0.0; fpd = FP/H*24
    pooled = dict(B=B, sens=sens, prec=prec, f1=f1, fpd=fpd, TP=TP, FN=N-TP, FP=FP,
                  sens_ci=wilson_ci(TP, N), prec_ci=wilson_ci(TP, TP+FP), fpd_ci=poisson_rate_ci(FP, H/24))
    return pooled, pd.DataFrame(rows)


def main():
    test = pd.read_csv("test_grid.csv")
    rt = ref_events(test)
    # harness self-check
    g = test[(test.mag_pct == 70) & (test.pen_mult == 0.5)]
    assert abs(g.tp.sum()/sum(rt[s] for s in g.subject)-0.632) < 0.003
    print("[selfcheck §0] OK\n")

    print(f"{'SHARED mag80/pen5':22} sens={SHARED['sens']:.3f} prec={SHARED['prec']:.3f} "
          f"F1={SHARED['f1']:.3f} FP/day={SHARED['fpd']:.2f}\n")
    all_pooled = []
    for B in (5, 10, 20):
        pooled, per = run_budget(test, rt, B)
        all_pooled.append(pooled)
        print(f"=== per-subject budget B={B} FP/day ===")
        print(f"  POOLED sens={pooled['sens']:.3f} [{pooled['sens_ci'][0]:.3f},{pooled['sens_ci'][1]:.3f}] "
              f"prec={pooled['prec']:.3f} [{pooled['prec_ci'][0]:.3f},{pooled['prec_ci'][1]:.3f}] "
              f"F1={pooled['f1']:.3f} FP/day={pooled['fpd']:.2f} [{pooled['fpd_ci'][0]:.2f},{pooled['fpd_ci'][1]:.2f}] "
              f"TP/FN/FP={pooled['TP']}/{pooled['FN']}/{pooled['FP']}")
        for _, r in per.iterrows():
            print(f"    {r.subject}: mag{r.mag:g}/pen{r.pen:g}  sens={r.sens:.3f} prec={r.prec:.3f} "
                  f"F1={r.f1:.3f} fpd={r.fpd:.1f} TP/FP={r.tp}/{r.fp}")
        per.to_csv(f"persubj_fp_budget_B{B}.csv", index=False)
        print()

    # success check vs shared (PREREG_07 s4): budget with pooled fpd <= 5.61
    cand = [p for p in all_pooled if p["fpd"] <= SHARED["fpd"] + 1e-9]
    print("=== PREREG_07 s4 verdict (matched FP/day <= shared 5.61) ===")
    if cand:
        best = min(cand, key=lambda p: abs(p["fpd"]-SHARED["fpd"]))
        win = (best["sens"] >= SHARED["sens"] and best["prec"] >= SHARED["prec"] and best["f1"] >= SHARED["f1"]
               and (best["sens"] > SHARED["sens"] or best["prec"] > SHARED["prec"] or best["f1"] > SHARED["f1"]))
        print(f"  B={best['B']} @ {best['fpd']:.2f} FP/day: sens={best['sens']:.3f} prec={best['prec']:.3f} F1={best['f1']:.3f}")
        print(f"  Pareto-superior to shared? {'YES -> per-subject becomes primary' if win else 'NO -> shared stays headline'}")
    else:
        print("  no per-subject budget lands at/under 5.61 FP/day; compare at nearest budget instead.")


if __name__ == "__main__":
    main()
