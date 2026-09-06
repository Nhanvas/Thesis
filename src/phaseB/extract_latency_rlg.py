"""
extract_latency_rlg.py — regenerate SzCORE detection-latency numbers for the LOCKED rlg
pipeline at the four operating points reported in RESULTS_OF_RECORD_phaseB.md §2-3.

WHY THIS SCRIPT EXISTS
-----------------------
`mean_lat_s` IS computed inside the production scoring path (szcore_eval.evaluate_subject,
score_ens.fast_grid_rows both call SE.matched_latency and attach mean_lat_s to each row
dict) but score_ens.py's CSV writer uses a FIXED column list (COLS) that does not include
mean_lat_s, and DictWriter(..., extrasaction="ignore") silently drops any key not in that
list. So every committed `final_eval_seed*.csv` under results/phaseB/tier2/ that produced
the locked RoR numbers has NO latency column, even though it was computed in memory during
that same run. This script re-derives it from the already-built rlg ensemble arrays, at
exactly the four (mag_pct, pen_mult) pairs already locked in RESULTS_OF_RECORD_phaseB.md
§2-3, and as an integrity check reproduces the locked sensitivity/precision/FP-day at each
point BEFORE trusting the latency numbers (per project integrity rule #10: reproduce
before trusting a number).

Inputs (already committed by build_ens_tier2.py — NOT rebuilt here):
    results/phaseB/tier2/ens_test_tf/rlg/ens_seed42_{subj}_{inter,ictal}.npy

Outputs:
    results/phaseB/tier2/latency/latency_per_seizure.csv
        operating_point, subject, ref_onset_s, matched, latency_s
    results/phaseB/tier2/latency/latency_summary.csv
        operating_point, subject, n_seizures, n_matched, mean_lat_s, median_lat_s, sd_lat_s
    results/phaseB/tier2/latency/reproduction_check.csv
        operating_point, sensitivity/precision/fp_per_day vs the RoR §2-3 locked values

USAGE (Cursor, CPU)
    python src/phaseB/extract_latency_rlg.py \
        --ens_dir results/phaseB/tier2/ens_test_tf/rlg \
        --summary_dir "F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary" \
        --out_dir results/phaseB/tier2/latency
"""
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
_src = _os.path.dirname(_here)
for _p in (_here, _src):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import argparse
import csv
from pathlib import Path

import numpy as np

import szcore_eval as SE
import cpd_pipeline_v14 as V14

TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]

# The four LOCKED operating points, RESULTS_OF_RECORD_phaseB.md §2-3.
OPERATING_POINTS = {
    "s0_balanced_matched_cell": dict(mag_pct=70, pen_mult=0.5),   # rlg @ m70/p0.5 -> 0.645/0.099/38.4
    "s0_highsens_matched_cell": dict(mag_pct=55, pen_mult=0.3),   # rlg @ m55/p0.3 -> 0.763/0.065/72.0
    "val_derived_balanced":     dict(mag_pct=50, pen_mult=2.0),   # HONEST HEADLINE -> 0.618/0.129/27.4
    "val_derived_highsens":     dict(mag_pct=50, pen_mult=0.5),   # -> 0.711/0.068/64.4
}

# Reference values from RESULTS_OF_RECORD_phaseB.md §3, for the reproduction check.
LOCKED_POOLED = {
    "s0_balanced_matched_cell": dict(sensitivity=0.645, precision=0.099, fp_per_day=38.4),
    "s0_highsens_matched_cell": dict(sensitivity=0.763, precision=0.065, fp_per_day=72.0),
    "val_derived_balanced":     dict(sensitivity=0.618, precision=0.129, fp_per_day=27.4),
    "val_derived_highsens":     dict(sensitivity=0.711, precision=0.068, fp_per_day=64.4),
}


def matched_latencies(ref_intervals, hyp_intervals, tol_start=30, tol_end=60):
    """Per-seizure latency (hyp_onset - ref_onset) for SzCORE-tolerance-matched
    events. Returns a list aligned to ref_intervals; None = seizure not detected
    (FN) at this operating point -- reported explicitly, never dropped."""
    out = []
    for (r0, r1) in ref_intervals:
        cands = [(h0, h1) for (h0, h1) in hyp_intervals
                 if h1 >= r0 - tol_start and h0 <= r1 + tol_end]
        if cands:
            h0 = min(cands, key=lambda h: abs(h[0] - r0))[0]
            out.append(h0 - r0)
        else:
            out.append(None)
    return out


def run_subject(subj, ens_dir, summary_dir, canonical_seed=0):
    ei = np.load(Path(ens_dir) / f"ens_seed42_{subj}_inter.npy")
    ec = np.load(Path(ens_dir) / f"ens_seed42_{subj}_ictal.npy")
    np.random.seed(canonical_seed)     # matches szcore_eval's bootstrap-padding convention
    signal, is_ictal, is_buffer, real_inter, sz_ranges, n_inter_h = \
        SE.build_timeline_masked(subj, ei, ec, summary_dir)
    ref_iv = [(s * SE.WIN_SEC, e * SE.WIN_SEC) for (s, e) in sz_ranges]
    total_dur_s = len(signal) * SE.WIN_SEC

    out = {}
    for op_name, p in OPERATING_POINTS.items():
        cps, _ = V14.detect_changepoints(signal, p["pen_mult"], min_mag_pct=p["mag_pct"],
                                         local_win=15, inter_mask=real_inter)
        hyp_iv = SE.cps_to_events(cps, is_buffer, len(signal), sz_ranges=sz_ranges)
        sc = SE.score_szcore(ref_iv, hyp_iv, total_dur_s, n_inter_h)
        lats = matched_latencies(ref_iv, hyp_iv)
        out[op_name] = dict(ref_iv=ref_iv, sc=sc, lats=lats, n_inter_h=n_inter_h)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ens_dir", default="results/phaseB/tier2/ens_test_tf/rlg")
    ap.add_argument("--summary_dir",
                    default=r"F:\Study\Thesis\Dataset\CHB-MIT\CHB info\summary")
    ap.add_argument("--out_dir", default="results/phaseB/tier2/latency")
    a = ap.parse_args()
    out_dir = Path(a.out_dir); out_dir.mkdir(parents=True, exist_ok=True)

    per_sz_rows, summary_rows, check_rows = [], [], []
    pooled = {op: dict(tp=0, fp=0, nsz=0, ih=0.0) for op in OPERATING_POINTS}

    for subj in TEST_SUBJS:
        try:
            res = run_subject(subj, a.ens_dir, a.summary_dir)
        except FileNotFoundError as e:
            print(f"[skip] {subj}: {e}")
            continue
        for op_name, d in res.items():
            for (onset_s, _end_s), lat in zip(d["ref_iv"], d["lats"]):
                per_sz_rows.append(dict(operating_point=op_name, subject=subj,
                                        ref_onset_s=onset_s, matched=lat is not None,
                                        latency_s=("" if lat is None else lat)))
            matched = [l for l in d["lats"] if l is not None]
            summary_rows.append(dict(
                operating_point=op_name, subject=subj, n_seizures=len(d["lats"]),
                n_matched=len(matched),
                mean_lat_s=round(float(np.mean(matched)), 2) if matched else "",
                median_lat_s=round(float(np.median(matched)), 2) if matched else "",
                sd_lat_s=round(float(np.std(matched, ddof=1)), 2) if len(matched) > 1 else ""))
            sc = d["sc"]; p = pooled[op_name]
            p["tp"] += sc["tp"]; p["fp"] += sc["fp"]
            p["nsz"] += len(d["ref_iv"]); p["ih"] += d["n_inter_h"]
        print(f"  {subj} done")

    for op_name, p in pooled.items():
        sens = p["tp"] / p["nsz"] if p["nsz"] else float("nan")
        prec = p["tp"] / (p["tp"] + p["fp"]) if (p["tp"] + p["fp"]) else float("nan")
        fpd = p["fp"] / (p["ih"] / 24.0) if p["ih"] else float("nan")
        ref = LOCKED_POOLED[op_name]
        check_rows.append(dict(operating_point=op_name,
                               sensitivity=round(sens, 3), sensitivity_locked=ref["sensitivity"],
                               precision=round(prec, 3), precision_locked=ref["precision"],
                               fp_per_day=round(fpd, 1), fp_per_day_locked=ref["fp_per_day"],
                               MATCH=(abs(sens - ref["sensitivity"]) < 0.01
                                      and abs(prec - ref["precision"]) < 0.01
                                      and abs(fpd - ref["fp_per_day"]) < 1.0)))

    def write(name, rows):
        with open(out_dir / name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
        print(f"wrote {out_dir/name}  ({len(rows)} rows)")

    write("latency_per_seizure.csv", per_sz_rows)
    write("latency_summary.csv", summary_rows)
    write("reproduction_check.csv", check_rows)

    print("\nREPRODUCTION CHECK vs RESULTS_OF_RECORD_phaseB.md §2-3:")
    for r in check_rows:
        flag = "OK" if r["MATCH"] else "MISMATCH -- do not trust the latency numbers yet"
        print(f"  {r['operating_point']:<28} sens {r['sensitivity']} (locked {r['sensitivity_locked']})  "
              f"prec {r['precision']} (locked {r['precision_locked']})  "
              f"FP/day {r['fp_per_day']} (locked {r['fp_per_day_locked']})  -> {flag}")


if __name__ == "__main__":
    main()