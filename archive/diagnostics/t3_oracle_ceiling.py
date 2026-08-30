#!/usr/bin/env python3
"""
T3 — Per-subject GRID-ORACLE ceiling (Phase-B diagnostic, per plan §5).

DIAGNOSTIC ONLY — this PEEKS at per-subject labels to find each subject's best
(mag,pen) cell. It is an ORACLE: NOT a reportable operating point, NEVER cited as
a result. Purpose: separate representation-limited (low oracle) from
decision-limited (high oracle) subjects BEFORE spending any GPU on Phase 2.

Grid-oracle = best F1 over the 48 discrete (mag,pen) cells. It is a LOWER BOUND on
the true continuous-threshold oracle: if even the grid-oracle is low, the subject is
strongly representation-limited (no operating point on this grid rescues it).

Reads the same grid CSVs as T1. No retraining, no new scores.
"""
import argparse
import numpy as np
import pandas as pd

VAL_SUBJS  = ["chb10", "chb11", "chb22"]
TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
SHARED_OP = (80.0, 10.0)   # T1 VAL-derived reportable shared point (mag,pen)


def f1_row(r):
    """Authoritative SzCORE F1 from the scorer's own sensitivity/precision columns.
    (Do NOT recompute sens as tp/n_seizures: SzCORE splits >5-min seizures, so the
    scorer's reference-event count can exceed n_seizures — e.g. chb11 has 5 ref
    events from 3 summary seizures. The csv sensitivity column is the truth.)"""
    sens = float(r.sensitivity); prec = float(r.precision)
    f1 = 2 * prec * sens / (prec + sens) if (prec + sens) else 0.0
    return f1, sens, prec


def per_subject_oracle(df, subjects):
    rows = []
    for s in subjects:
        d = df[df.subject == s]
        auroc = float(d.window_auroc.iloc[0])
        # oracle-F1 cell (peeks at this subject's labels)
        best = None
        for _, r in d.iterrows():
            f1, sens, prec = f1_row(r)
            fpd = r.fp / r.n_inter_h * 24 if r.n_inter_h else float("nan")
            cand = dict(mag=r.mag_pct, pen=r.pen_mult, f1=f1, sens=sens, prec=prec,
                        fpd=fpd, tp=int(r.tp), fp=int(r.fp), n_sz=int(r.n_seizures))
            if best is None or (cand["f1"], cand["sens"], -cand["fpd"]) > \
                               (best["f1"], best["sens"], -best["fpd"]):
                best = cand
        # F1 at the T1 shared reportable point
        sh = d[(d.mag_pct == SHARED_OP[0]) & (d.pen_mult == SHARED_OP[1])].iloc[0]
        sh_f1, sh_sens, _ = f1_row(sh)
        rows.append(dict(subject=s, window_auroc=auroc,
                         oracle_f1=best["f1"], oracle_sens=best["sens"], oracle_prec=best["prec"],
                         oracle_fpd=best["fpd"], oracle_cell=f"mag{best['mag']:g}/pen{best['pen']:g}",
                         oracle_tp=best["tp"], n_sz=best["n_sz"],
                         shared_f1=sh_f1, shared_sens=sh_sens,
                         gap_f1=best["f1"] - sh_f1))
    return pd.DataFrame(rows)


def classify(r, auroc_lo=0.65, oracle_lo=0.30, gap_hi=0.15):
    """Route each subject. Thresholds are diagnostic heuristics, stated up-front."""
    if r.window_auroc < 0.5:
        return "REPRESENTATION (below-chance AUROC) -> Phase 2"
    if r.window_auroc < auroc_lo and r.oracle_f1 < oracle_lo:
        return "REPRESENTATION (weak AUROC + low oracle) -> Phase 2"
    if r.oracle_f1 >= oracle_lo and r.gap_f1 >= gap_hi:
        return "DECISION (good oracle, shared OP strangles) -> Phase 1"
    if r.oracle_f1 >= oracle_lo and r.gap_f1 < gap_hi:
        return "OK at shared OP (near ceiling)"
    return "MIXED / inspect"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--val_csv", default="val_grid.csv")
    ap.add_argument("--test_csv", default="test_grid.csv")
    ap.add_argument("--out", default="t3_oracle_ceiling.csv")
    args = ap.parse_args()

    val = pd.read_csv(args.val_csv); test = pd.read_csv(args.test_csv)
    print("=" * 78)
    print("T3 — GRID-ORACLE ceiling (DIAGNOSTIC / peeks labels; NOT a reportable OP)")
    print("Shared reportable OP = T1 mag80/pen10.  oracle = best F1 over 48 grid cells.")
    print("=" * 78)

    for tag, df, subs in [("TEST", test, TEST_SUBJS), ("VAL", val, VAL_SUBJS)]:
        t = per_subject_oracle(df, subs)
        t["route"] = t.apply(classify, axis=1)
        t = t.sort_values("window_auroc")
        print(f"\n### {tag}")
        print(f"{'subj':7} {'AUROC':>6} {'oracle_F1':>9} {'orc_sens':>8} {'orc_cell':>12} "
              f"{'shared_F1':>9} {'gap':>6}  route")
        for _, r in t.iterrows():
            print(f"{r.subject:7} {r.window_auroc:6.3f} {r.oracle_f1:9.3f} {r.oracle_sens:8.3f} "
                  f"{r.oracle_cell:>12} {r.shared_f1:9.3f} {r.gap_f1:6.3f}  {r.route}")
        if tag == "TEST":
            t.to_csv(args.out, index=False)
            # recoverable-sensitivity accounting
            dec = t[t.route.str.startswith("DECISION")]
            rep = t[t.route.str.startswith("REPRESENTATION")]
            print(f"\n  DECISION-limited (Phase 1 target): {list(dec.subject)}")
            print(f"  REPRESENTATION-limited (Phase 2 target): {list(rep.subject)}")
            # what pooled sens/F1 would be if decision-limited subjects hit their oracle
            print("\n  Recoverable accounting @ shared point vs if Phase-1 recovers DECISION subjects:")
            TP_sh = 0; FP_sh = 0; N = int(t.n_sz.sum())
            for _, r in t.iterrows():
                sh = test[(test.subject == r.subject) & (test.mag_pct == SHARED_OP[0]) &
                          (test.pen_mult == SHARED_OP[1])]
                TP_sh += int(sh.tp.iloc[0]); FP_sh += int(sh.fp.iloc[0])
            print(f"    shared point pooled: TP={TP_sh}/{N} sens={TP_sh/N:.3f}")

    print(f"\n  Wrote {args.out}")


if __name__ == "__main__":
    main()
