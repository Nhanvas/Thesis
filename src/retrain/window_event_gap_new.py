"""
window_event_gap_new.py — DIAGNOSTIC (Cursor CPU, no GPU/torch).

Question: for the rebuilt deep-ensemble, where is event-sensitivity lost —
in the SIGNAL (window discrimination too weak) or in the shared patient-independent
OPERATING POINT (a subject is detectable, but the one grid point picked for
everyone is wrong for it)?

Reads only:
  results/retrain/final_eval_seed{TAG}.csv   (per subject/mag/pen: tp,fp,n_seizures,n_inter_h, window_auroc)
  results/retrain/ens/window_auroc_seed{TAG}.json  (optional; CSV already carries window_auroc)

For each test subject it reports, at the pooled option-A BALANCED point:
  - window AUROC (signal quality)
  - event sensitivity AT the shared balanced point
  - the subject's OWN best event sensitivity anywhere on the grid (+ where, + that
    subject's FP/day there)
  - gap = own-best - at-shared-point

Reading the result:
  * high window AUROC + low sens@shared + high own-best  -> OPERATING-POINT cost
    (recoverable by better label-free per-subject threshold calibration)
  * low window AUROC + low own-best everywhere           -> SIGNAL-limited (e.g. chb06)
It also prints the pooled sensitivity if every subject used its own-best point
(an upper bound = how much the single shared operating point is costing us).

USAGE (Cursor)
  python window_event_gap_new.py --in_dir results/retrain --tag 99
Smoke:
  python window_event_gap_new.py --smoke
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

import final_eval as FE
import retrain_io as IO

SIGNAL_BAR = 0.60      # window AUROC below this -> call it signal-limited
GAP_BAR = 0.15         # own-best minus at-shared above this -> operating-point cost


def load_rows(csv_path):
    rows = []
    with open(csv_path) as f:
        for r in csv.DictReader(f):
            rows.append(dict(subject=r["subject"], mag_pct=float(r["mag_pct"]),
                             pen_mult=float(r["pen_mult"]), tp=int(float(r["tp"])),
                             fp=int(float(r["fp"])), n_seizures=int(float(r["n_seizures"])),
                             n_inter_h=float(r["n_inter_h"]),
                             window_auroc=float(r.get("window_auroc", "nan") or "nan")))
    return rows


def diagnose(rows, wa_json=None):
    # pooled frontier + option-A balanced point
    pooled = IO.mark_pareto(FE.pool_grid(rows))
    sel = IO.select_operating_points_optionA(pooled, target_fp=40.0, fp_cap=75.0)
    bal = sel["balanced"]
    bmag, bpen = bal["mag_pct"], bal["pen_mult"]

    subjects = sorted({r["subject"] for r in rows})
    per = []
    for s in subjects:
        srows = [r for r in rows if r["subject"] == s]
        # window AUROC: prefer json, else the csv column
        if wa_json and s in wa_json:
            wauroc = float(wa_json[s])
        else:
            wauroc = next((r["window_auroc"] for r in srows
                           if r["window_auroc"] == r["window_auroc"]), float("nan"))
        # event sens at the shared balanced point
        at = next((r for r in srows
                   if abs(r["mag_pct"] - bmag) < 1e-9 and abs(r["pen_mult"] - bpen) < 1e-9), None)
        sens_at = (at["tp"] / at["n_seizures"]) if at and at["n_seizures"] else float("nan")
        # subject's own best sens anywhere on the grid (tie-break: lower FP/day)
        def subj_fp(r):
            return r["fp"] / r["n_inter_h"] * 24 if r["n_inter_h"] else float("inf")
        best = max(srows, key=lambda r: (r["tp"] / r["n_seizures"] if r["n_seizures"] else 0,
                                         -subj_fp(r)))
        sens_best = best["tp"] / best["n_seizures"] if best["n_seizures"] else float("nan")
        per.append(dict(subject=s, n_sz=srows[0]["n_seizures"], window_auroc=wauroc,
                        sens_at_balanced=sens_at, sens_best=sens_best,
                        best_mag=best["mag_pct"], best_pen=best["pen_mult"],
                        best_fp_day=subj_fp(best), gap=sens_best - sens_at))

    # pooled sens if everyone used own-best point (oracle upper bound)
    tp_best = sum(round(p["sens_best"] * p["n_sz"]) for p in per)
    tp_at = sum(round(p["sens_at_balanced"] * p["n_sz"]) for p in per)
    n_sz_tot = sum(p["n_sz"] for p in per)
    return bal, per, tp_at / n_sz_tot, tp_best / n_sz_tot, n_sz_tot


def report(bal, per, pooled_at, pooled_best, n_sz):
    print(f"\nBALANCED operating point (pooled option-A): "
          f"mag{bal['mag_pct']:g}/pen{bal['pen_mult']:g}  "
          f"pooled sens={bal['sensitivity']:.3f} FP/day={bal['fp_per_day']:.1f}\n")
    print(f"{'subj':7s} {'nSz':>3s} {'winAUROC':>8s} {'sens@bal':>8s} "
          f"{'ownBest':>7s} {'@mag/pen':>10s} {'subjFP':>7s} {'gap':>6s}  verdict")
    for p in per:
        if p["window_auroc"] < SIGNAL_BAR:
            v = "SIGNAL-limited"
        elif p["gap"] >= GAP_BAR:
            v = "OP-POINT cost (recoverable)"
        else:
            v = "ok / near-ceiling"
        print(f"{p['subject']:7s} {p['n_sz']:3d} {p['window_auroc']:8.3f} "
              f"{p['sens_at_balanced']:8.3f} {p['sens_best']:7.3f} "
              f"{p['best_mag']:g}/{p['best_pen']:<6g} {p['best_fp_day']:7.1f} "
              f"{p['gap']:+6.3f}  {v}")
    print(f"\npooled sens @ shared balanced point   = {pooled_at:.3f}")
    print(f"pooled sens if each subj used own-best = {pooled_best:.3f}  "
          f"(upper bound; NOT patient-independent — diagnostic only)")
    print(f"=> cost of the single shared operating point = {pooled_best - pooled_at:+.3f} "
          f"sensitivity")
    print("\nInterpretation:")
    print("  * big gap + high winAUROC  -> a label-free per-subject threshold "
          "calibration could recover sensitivity (cheap, in-scope).")
    print("  * low winAUROC everywhere  -> signal-limited; only a better signal "
          "(e.g. SSL) helps (expensive).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_dir", default="results/retrain")
    ap.add_argument("--tag", default="99")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()

    if a.smoke:
        # synthetic: chb14-like subject detectable only at a high-FP point (OP cost),
        # chb06-like subject low everywhere (signal-limited)
        rows = []
        grid = [(m, p) for m in FE.MAG_PCTS for p in FE.DEFAULT_PENS]
        for (m, p) in grid:
            aggr = (1 - m / 100) + (1 - p / 10) / 2
            # good subject: high everywhere
            rows.append(dict(subject="chb03", mag_pct=m, pen_mult=p,
                             tp=min(7, round(6 + aggr)), fp=int(30 * aggr),
                             n_seizures=7, n_inter_h=20, window_auroc=0.95))
            # OP-cost subject: only catches seizures at aggressive (high-FP) points
            rows.append(dict(subject="chb14", mag_pct=m, pen_mult=p,
                             tp=(8 if aggr > 1.0 else 2), fp=int(40 * aggr),
                             n_seizures=8, n_inter_h=22, window_auroc=0.83))
            # signal-limited subject: low everywhere
            rows.append(dict(subject="chb06", mag_pct=m, pen_mult=p,
                             tp=(1 if aggr > 1.2 else 0), fp=int(50 * aggr),
                             n_seizures=10, n_inter_h=40, window_auroc=0.44))
        bal, per, pat, pbest, nsz = diagnose(rows)
        report(bal, per, pat, pbest, nsz)
        assert any(p["subject"] == "chb06" and p["window_auroc"] < SIGNAL_BAR for p in per)
        assert pbest >= pat
        print("\n[SMOKE] PASS")
        return

    in_dir = Path(a.in_dir)
    csv_path = in_dir / f"final_eval_seed{a.tag}.csv"
    wa_path = in_dir / "ens" / f"window_auroc_seed{a.tag}.json"
    if not csv_path.exists():
        raise SystemExit(f"not found: {csv_path}")
    rows = load_rows(csv_path)
    wa = json.loads(wa_path.read_text()) if wa_path.exists() else None
    bal, per, pat, pbest, nsz = diagnose(rows, wa)
    report(bal, per, pat, pbest, nsz)


if __name__ == "__main__":
    main()
