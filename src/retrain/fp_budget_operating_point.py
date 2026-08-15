"""
fp_budget_operating_point.py — PREREG_04 (PHA 1.5, step a). Cursor CPU, no GPU.

Per-subject operating point chosen to hit a pre-specified SzCORE false-alarm
budget B (FP/day) on each subject's INTERICTAL (seizure-free) data. Selection uses
ONLY interictal FP/day; the tie-break is forbidden from using sensitivity. Model is
unchanged and patient-independent; this only calibrates the decision threshold
per patient on baseline data (standard clinical practice).

Two stages (run VAL first — cach 1, approved):
  --stage val  : build A1-A3 guardrail verdict on the VAL grid. If A2 fails, STOP.
  --stage test : (requires VAL PASS) re-select per subject on the TEST grid; report
                 SHARED (option-A) vs CALIBRATED, both with 95% CIs. Reports BOTH.

Budgets (pre-registered): balanced B=40, high-sens B=75 FP/day.
All FP/day and sensitivity are SzCORE event scores (timescoring), taken from the
already-scored grid CSV.

USAGE (Cursor)
  python fp_budget_operating_point.py --stage val  --val_csv  results/retrain/val/final_eval_seed99.csv --out_dir results/retrain
  python fp_budget_operating_point.py --stage test --test_csv results/retrain/final_eval_seed99.csv     --out_dir results/retrain
Smoke:
  python fp_budget_operating_point.py --smoke
"""
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
for _p in (_here, _os.path.dirname(_here)):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import argparse
import csv
import json
from pathlib import Path

import numpy as np

import final_eval as FE
import retrain_io as IO
import stat_validation as ST

BUDGETS = {"balanced": 40.0, "high-sensitivity": 75.0}
TIE_EPS = 2.0          # FP/day window for the tie-break (PREREG_04 §1)


def load_rows(csv_path):
    rows = []
    with open(csv_path) as f:
        for r in csv.DictReader(f):
            fp = int(float(r["fp"])); ih = float(r["n_inter_h"])
            rows.append(dict(subject=r["subject"], mag_pct=float(r["mag_pct"]),
                             pen_mult=float(r["pen_mult"]), tp=int(float(r["tp"])),
                             fp=fp, n_seizures=int(float(r["n_seizures"])),
                             n_inter_h=ih, fpd=(fp / ih * 24 if ih else float("inf"))))
    return rows


# ---- the pre-registered per-subject selection rule (label-free) ----
def select_subject_op(srows, budget, ref_mag, ref_pen, eps=TIE_EPS):
    dmin = min(abs(r["fpd"] - budget) for r in srows)
    cands = [r for r in srows if abs(r["fpd"] - budget) <= dmin + eps]
    # tie-break: closest to the shared reference point; NEVER by sensitivity
    return min(cands, key=lambda r: abs(r["mag_pct"] - ref_mag) + 10 * abs(r["pen_mult"] - ref_pen))


def pooled_shared_nearest(rows, budget):
    """Single (mag,pen) whose POOLED FP/day is nearest budget (the VAL 'shared' baseline)."""
    pooled = FE.pool_grid(rows)
    return min(pooled, key=lambda r: abs(r["fp_per_day"] - budget))


def rows_at(rows, mag, pen):
    return [r for r in rows if abs(r["mag_pct"] - mag) < 1e-9 and abs(r["pen_mult"] - pen) < 1e-9]


def pooled_ci(selected_rows, label, mag_pen=None):
    TP = sum(r["tp"] for r in selected_rows); FP = sum(r["fp"] for r in selected_rows)
    nsz = sum(r["n_seizures"] for r in selected_rows)
    ih = sum(r["n_inter_h"] for r in selected_rows); days = ih / 24.0
    sens = TP / nsz if nsz else float("nan")
    prec = TP / (TP + FP) if (TP + FP) else float("nan")
    f1 = (2 * prec * sens / (prec + sens)) if (prec and sens) else float("nan")
    fpd = FP / days if days else float("nan")
    s_lo, s_hi = ST.wilson_ci(TP, nsz); p_lo, p_hi = ST.wilson_ci(TP, TP + FP)
    f_lo, f_hi = ST.poisson_rate_ci(FP, days)
    return dict(operating_point=label, mag_pen=(mag_pen or "per-subject"),
                n_subjects=len(selected_rows), n_seizures=nsz, TP=TP, FN=nsz - TP, FP=FP,
                interictal_hours=round(ih, 1), sensitivity=round(sens, 4),
                sensitivity_CI=f"[{s_lo:.3f}, {s_hi:.3f}]", precision=round(prec, 4),
                precision_CI=f"[{p_lo:.3f}, {p_hi:.3f}]", f1=round(f1, 4),
                fp_per_day=round(fpd, 2), fp_per_day_CI=f"[{f_lo:.2f}, {f_hi:.2f}]")


def calibrate(rows, budget, ref):
    """Per-subject FP-budget selection -> (selected rows per subject, pooled CI dict)."""
    subjects = sorted({r["subject"] for r in rows})
    sel = []
    for s in subjects:
        srows = [r for r in rows if r["subject"] == s]
        sel.append(select_subject_op(srows, budget, ref["mag_pct"], ref["pen_mult"]))
    return sel, pooled_ci(sel, "calibrated (per-subject FP-budget)")


# ============================================================================
def stage_val(val_rows, out_dir):
    print("=" * 74); print("PREREG_04 - VAL guardrail (A1-A3)"); print("=" * 74)
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    verdicts = {}; wrows = []
    for name, B in BUDGETS.items():
        shared = pooled_shared_nearest(val_rows, B); ref = shared
        sel, calib = calibrate(val_rows, B, ref)
        shared_ci = pooled_ci(rows_at(val_rows, shared["mag_pct"], shared["pen_mult"]),
                              "shared", mag_pen=f"mag{shared['mag_pct']:g}/pen{shared['pen_mult']:g}")
        A1 = abs(calib["fp_per_day"] - B) <= 0.15 * B
        A2 = calib["sensitivity"] >= shared_ci["sensitivity"] - 0.02
        max_subj_fpd = max(r["fpd"] for r in sel)
        A3 = max_subj_fpd <= 1.5 * B
        ok = A1 and A2 and A3; verdicts[name] = ok
        print(f"\n[{name}] B={B:g} FP/day")
        print(f"  shared  : {shared_ci['mag_pen']}  sens={shared_ci['sensitivity']:.3f} "
              f"FP/day={shared_ci['fp_per_day']:.1f}")
        print(f"  calib   : sens={calib['sensitivity']:.3f} FP/day={calib['fp_per_day']:.1f} (per-subject)")
        print(f"  A1 budget |{calib['fp_per_day']:.1f}-{B:g}|<= {0.15*B:.1f} -> {'PASS' if A1 else 'FAIL'}")
        print(f"  A2 no-harm {calib['sensitivity']:.3f} >= {shared_ci['sensitivity']:.3f}-0.02 -> {'PASS' if A2 else 'FAIL'}")
        print(f"  A3 max subj FP/day {max_subj_fpd:.1f} <= {1.5*B:.1f} -> {'PASS' if A3 else 'FAIL'}")
        print(f"  => {name}: {'PASS' if ok else 'FAIL'}")
        for r in sel:
            wrows.append(dict(budget=name, subject=r["subject"], mag_pct=r["mag_pct"],
                              pen_mult=r["pen_mult"], fp_per_day=round(r["fpd"], 2),
                              sensitivity=round(r["tp"] / r["n_seizures"], 4) if r["n_seizures"] else "",
                              A1=int(A1), A2=int(A2), A3=int(A3)))
    overall = all(verdicts.values())
    with open(out / "fp_budget_val_check.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["budget", "subject", "mag_pct", "pen_mult",
                                          "fp_per_day", "sensitivity", "A1", "A2", "A3"])
        w.writeheader(); w.writerows(wrows)
    (out / "fp_budget_val_verdict.json").write_text(json.dumps(
        {"overall_PASS": overall, "per_budget": verdicts}, indent=2))
    print(f"\nOVERALL VAL verdict: {'PASS -> proceed to --stage test' if overall else 'FAIL -> reject, keep shared point'}")
    print(f"[saved] {out/'fp_budget_val_check.csv'} , fp_budget_val_verdict.json")
    return overall


def stage_test(test_rows, out_dir, val_verdict_path, override=False):
    vpath = Path(val_verdict_path)
    if not override:
        if not vpath.exists():
            raise SystemExit("VAL verdict missing - run --stage val first (cach 1). "
                             "Use --override only if you deliberately skip the gate.")
        v = json.loads(vpath.read_text())
        if not v.get("overall_PASS"):
            raise SystemExit("VAL guardrail FAILED - per PREREG_04, reject the calibration and "
                             "keep the shared operating point. Not proceeding to test.")
    print("=" * 74); print("PREREG_04 - TEST (one pass): SHARED vs CALIBRATED"); print("=" * 74)
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    pooled = IO.mark_pareto(FE.pool_grid(test_rows))
    sel_ab = IO.select_operating_points_optionA(pooled, target_fp=40.0, fp_cap=75.0)
    refs = {"balanced": sel_ab["balanced"], "high-sensitivity": sel_ab["highsens"]}

    lock_rows, persubj_rows = [], []
    for name, B in BUDGETS.items():
        ref = refs[name]
        shared_ci = pooled_ci(rows_at(test_rows, ref["mag_pct"], ref["pen_mult"]),
                              f"{name} - shared (held-out)",
                              mag_pen=f"mag{ref['mag_pct']:g}/pen{ref['pen_mult']:g}")
        sel, calib_ci = calibrate(test_rows, B, ref)
        calib_ci["operating_point"] = f"{name} - calibrated (per-subject FP-budget)"
        print(f"\n[{name}]  budget {B:g} FP/day  (shared ref {shared_ci['mag_pen']})")
        print(f"  SHARED    : sens {shared_ci['sensitivity']:.3f} {shared_ci['sensitivity_CI']}  "
              f"FP/day {shared_ci['fp_per_day']:.1f}  (TP/FN/FP {shared_ci['TP']}/{shared_ci['FN']}/{shared_ci['FP']})")
        print(f"  CALIBRATED: sens {calib_ci['sensitivity']:.3f} {calib_ci['sensitivity_CI']}  "
              f"FP/day {calib_ci['fp_per_day']:.1f}  (TP/FN/FP {calib_ci['TP']}/{calib_ci['FN']}/{calib_ci['FP']})")
        print(f"  delta sensitivity = {calib_ci['sensitivity'] - shared_ci['sensitivity']:+.3f}")
        lock_rows.append(shared_ci); lock_rows.append(calib_ci)
        for r in sel:
            persubj_rows.append(dict(budget=name, subject=r["subject"], mag_pct=r["mag_pct"],
                                     pen_mult=r["pen_mult"], fp_per_day=round(r["fpd"], 2),
                                     tp=r["tp"], n_seizures=r["n_seizures"],
                                     sensitivity=round(r["tp"] / r["n_seizures"], 4) if r["n_seizures"] else ""))
    cols = list(lock_rows[0].keys())
    with open(out / "fp_budget_locked.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(lock_rows)
    with open(out / "fp_budget_test_persubject.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["budget", "subject", "mag_pct", "pen_mult",
                                          "fp_per_day", "tp", "n_seizures", "sensitivity"])
        w.writeheader(); w.writerows(persubj_rows)
    print(f"\n[saved] {out/'fp_budget_locked.csv'} , fp_budget_test_persubject.csv")
    print("Report BOTH shared (held-out) and calibrated (per-subject FP-budget) - never one alone.")


# ============================================================================
def _synth(seed, subjects, strangled=None):
    rng = np.random.default_rng(seed); strangled = strangled or set()
    n_sz = {s: 8 for s in subjects}; ih = {s: 20.0 for s in subjects}
    rows = []
    for m in FE.MAG_PCTS:
        for p in FE.DEFAULT_PENS:
            aggr = (1 - m / 100) + (1 - p / 10) / 2
            fpd = 8 + 90 * aggr
            for s in subjects:
                if s in strangled:
                    tp = n_sz[s] if fpd > 60 else 1
                else:
                    tp = min(n_sz[s], round(3 + 5 * aggr))
                fp = int(fpd * ih[s] / 24)
                rows.append(dict(subject=s, mag_pct=m, pen_mult=p, tp=tp, fp=fp,
                                 n_seizures=n_sz[s], n_inter_h=ih[s], fpd=fp / ih[s] * 24))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["val", "test"], default=None)
    ap.add_argument("--val_csv", default="results/retrain/val/final_eval_seed99.csv")
    ap.add_argument("--test_csv", default="results/retrain/final_eval_seed99.csv")
    ap.add_argument("--out_dir", default="results/retrain")
    ap.add_argument("--override", action="store_true", help="skip the VAL gate (cach 2 only)")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()

    if a.smoke:
        val = _synth(1, IO.VAL_SUBJS)
        test = _synth(2, IO.TEST_SUBJS, strangled={"chb16", "chb13"})
        ok = stage_val(val, "/tmp/fpb_smoke")
        assert ok, "VAL should pass on well-behaved synthetic"
        stage_test(test, "/tmp/fpb_smoke", "/tmp/fpb_smoke/fp_budget_val_verdict.json")
        lk = list(csv.DictReader(open("/tmp/fpb_smoke/fp_budget_locked.csv")))
        bal = {r["operating_point"]: r for r in lk}
        cal = float(bal["balanced - calibrated (per-subject FP-budget)"]["sensitivity"])
        sh = float(bal["balanced - shared (held-out)"]["sensitivity"])
        assert cal >= sh, (cal, sh)
        print(f"\n[SMOKE] calibrated {cal:.3f} >= shared {sh:.3f} -> PASS")
        return

    if a.stage == "val":
        stage_val(load_rows(a.val_csv), a.out_dir)
    elif a.stage == "test":
        stage_test(load_rows(a.test_csv), a.out_dir,
                   Path(a.out_dir) / "fp_budget_val_verdict.json", a.override)
    else:
        raise SystemExit("pass --stage val | --stage test  (or --smoke)")


if __name__ == "__main__":
    main()
