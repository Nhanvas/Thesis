"""
================================================================================
 duration_stratified_sensitivity.py  —  per-seizure hit/miss x duration
================================================================================
WHY THIS FILE
-------------
locked_phaseA_event_results.csv / szcore_event_level_mag*.csv only give
per-SUBJECT tp/fn counts. To answer "is sensitivity different for seizures
below the ACNS 10s electrographic-seizure threshold?" we need per-SEIZURE
hit/miss, which nothing currently exported provides.

This script does NOT reimplement scoring. It calls the exact same authoritative
path as szcore_eval.py (evaluate_subject's ref/hyp construction ->
scoring.EventScoring with the same SZ_PARAM), then INTROSPECTS the internal
tpMask that timescoring already computed to read off, for each of the 76
original CHB-MIT-annotated seizures, whether it was individually a hit.

Because we already confirmed (separately) that no two annotated seizures in
these 8 subjects are <90s apart, the SzCORE merge step never changes n_ref
here -> EventScoring's internal self.ref.events stays in 1:1 correspondence
with the original annotated seizures, in the same order. That is what makes
this per-seizure readout valid; the script re-checks this assumption itself
(assert no merge occurred) rather than assuming it silently.

NO retraining, NO GPU: pure CPU re-scoring of already-cached per-component
z-scores, Core Rule #9.

WEIGHT (updated for Decision #19/#20): this script now BUILDS the ensemble
from cached per-component z-scores (zrecon/ztemp/zgamma) using the NEW
locked weight (0.40, 0.35, 0.25), the same way rebuild_ensemble_new_weight.py
and mag_pen_grid_sweep_v2.py do -- it no longer reads
results/cpd/scores/{subj}_ens_*.npy directly, because that cache holds the
OLD weight's ensemble unless separately re-exported from GPU. If you see a
--scores_dir argument in an older version of this script, that version is
using the OLD weight silently; do not trust its numbers.

SANITY CHECK (built in): sum(hit) per subject MUST equal the locked `tp` in
szcore_event_level_new_decision19_mag60.csv (balanced) /
szcore_event_level_new_decision19_mag50.csv @ pen=0.5 (high_sens). Any
mismatch is printed loudly.

OUTPUT
------
  duration_hit_persubject.csv   one row per (subject, seizure_idx, operating_point):
                                 duration_s, hit (bool)
  duration_bucket_summary.csv   sensitivity per duration bucket x operating point,
                                 pooled (micro) across all 8 subjects

USAGE
-----
  python duration_stratified_sensitivity.py \
      --comp_dir data/processed/components \
      --summary_dir "F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary"

Requires: szcore_eval.py, evaluation_protocol.py, cpd_pipeline_v14.py, timescoring.
================================================================================
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from timescoring import scoring
from timescoring.annotations import Annotation

import szcore_eval as SZ
import cpd_pipeline_v14 as V14

# Decision #19: the ensemble is now built from cached per-component z-scores
# with the NEW weight, NOT read directly from results/cpd/scores/*.npy (that
# cache still holds the OLD weight's ensemble unless it has been separately
# re-exported from GPU -- do not assume it has been). This mirrors
# rebuild_ensemble_new_weight.py and mag_pen_grid_sweep_v2.py exactly, so all
# three scripts agree on what "the ensemble" means.
NEW_W = (0.40, 0.35, 0.25)   # Decision #19


def load_components(comp_dir, subj):
    def L(name, split):
        p = Path(comp_dir) / f"{name}_{subj}_{split}.npy"
        return np.load(str(p)).astype(np.float64) if p.exists() else None
    return {k: (L(k, "inter"), L(k, "ictal")) for k in ("zrecon", "ztemp", "zgamma")}


def build_ensemble(comp_dir, subj, weight):
    c = load_components(comp_dir, subj)
    if not all(c[k][0] is not None and c[k][1] is not None for k in c):
        return None, None
    ni = min(len(c["zrecon"][0]), len(c["ztemp"][0]), len(c["zgamma"][0]))
    nc = min(len(c["zrecon"][1]), len(c["ztemp"][1]), len(c["zgamma"][1]))
    wr, wt, wg = weight
    ens_i = wr * c["zrecon"][0][:ni] + wt * c["ztemp"][0][:ni] + wg * c["zgamma"][0][:ni]
    ens_c = wr * c["zrecon"][1][:nc] + wt * c["ztemp"][1][:nc] + wg * c["zgamma"][1][:nc]
    return ens_i, ens_c

# the two LOCKED operating points (Phase A, RESULTS_OF_RECORD.md).
#
# PROVENANCE (read before changing these again):
#   v1 (original):        high_sens = mag70/pen0.3   -- superseded by Decision #16
#   v2 (Decision #16):     high_sens = mag50/pen1.0   -- SUPERSEDED: this came from
#                          mag_pen_grid_sweep.py, which had a seeding bug (np.random
#                          was not reseeded between mag_pct values in its 8-value
#                          loop per subject, so results drifted with loop position --
#                          confirmed by direct forward/reverse-order experiment).
#   v3 (Decision #20, CURRENT): high_sens = mag50/pen0.5, sensitivity=0.8289 (63/76),
#                          FP/day=71.25, CI [0.729,0.897]. Derived from
#                          mag_pen_grid_sweep_v2.py (reseeds np.random immediately
#                          before EVERY evaluate_subject() call -- confirmed
#                          order-independent and confirmed to match
#                          rebuild_ensemble_new_weight.py exactly at old-weight
#                          mag60/mag50, an independent implementation). Selection
#                          criterion: cheapest (lowest FP/day) Pareto-optimal point
#                          whose sensitivity gain over balanced exceeds 2x the known
#                          seed-to-seed noise SD (~0.03, from
#                          weight_candidate_crosscheck.py's 8-seed runs) -- i.e. a
#                          defensibly real improvement, not noise. mag60/pen0.3 is
#                          numerically IDENTICAL (same TP at every one of the 8
#                          subjects) and may be cited interchangeably.
#   balanced is UNCHANGED throughout: mag60/pen1.0 (still Pareto-optimal for both
#   the old and the new ensemble weight per mag_pen_grid_v2_pooled.csv).
#
# If you have an OLDER duration_bucket_summary.csv computed before this fix,
# it was run against a superseded high_sens point -- re-run this script.
OPERATING_POINTS = [
    ("balanced",  60.0, 1.0),
    ("high_sens", 50.0, 0.5),
]

BUCKETS = [(0, 10, "<10s"), (10, 20, "10-20s"), (20, 60, "20-60s"), (60, 1e9, ">=60s")]


def bucket_of(dur):
    for lo, hi, label in BUCKETS:
        if lo <= dur < hi:
            return label
    return ">=60s"


def per_seizure_hits(ref_iv, hyp_iv, total_dur_s):
    """Run the authoritative EventScoring, then read per-original-seizure hit
    status off its internal tpMask. Returns list of (duration_s, hit)."""
    N = max(int(total_dur_s), 1)
    ref = Annotation(list(ref_iv), 1, N)
    hyp = Annotation(list(hyp_iv), 1, N)
    s = scoring.EventScoring(ref, hyp, SZ.SZ_PARAM)

    # assert merge never collapsed our reference events (must hold for these
    # 8 subjects; if it ever doesn't, the 1:1 mapping below is invalid and we
    # must stop rather than silently mis-attribute durations)
    if len(s.ref.events) != len(ref_iv):
        raise AssertionError(
            f"Reference events were merged ({len(ref_iv)} -> {len(s.ref.events)}): "
            "per-seizure duration attribution below would be WRONG for this "
            "subject. Stop and handle explicitly (rare, but must be checked).")

    extended = scoring.EventScoring._extendEvents(
        s.ref, SZ.SZ_PARAM.toleranceStart, SZ.SZ_PARAM.toleranceEnd)

    out = []
    for orig_evt, ext_evt in zip(s.ref.events, extended.events):
        duration_s = orig_evt[1] - orig_evt[0]
        seg = s.tpMask[round(ext_evt[0] * s.fs):round(ext_evt[1] * s.fs)]
        hit = bool(np.any(seg))
        out.append((duration_s, hit))
    return out, int(s.tp)


def main():
    ap = argparse.ArgumentParser(description="Per-seizure duration x hit/miss")
    ap.add_argument("--comp_dir", default="data/processed/components")
    ap.add_argument("--summary_dir", required=True)
    ap.add_argument("--out_dir", default="results/phaseA_appendix")
    ap.add_argument("--local_win", type=int, default=15)
    ap.add_argument("--canonical_seed", type=int, default=0)
    args = ap.parse_args()

    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    rows = []

    for subj in SZ.TEST_SUBJS:
        ens_inter, ens_ictal = build_ensemble(args.comp_dir, subj, NEW_W)
        if ens_inter is None:
            print(f"  [skip] {subj}: components missing"); continue

        for label, mag, pen in OPERATING_POINTS:
            np.random.seed(args.canonical_seed)
            signal, is_ictal, is_buffer, real_inter, sz_ranges, n_inter_h = \
                SZ.build_timeline_masked(subj, ens_inter, ens_ictal, args.summary_dir)
            ref_iv = [(s0 * SZ.WIN_SEC, s1 * SZ.WIN_SEC) for (s0, s1) in sz_ranges]
            total_dur_s = len(signal) * SZ.WIN_SEC

            cps, _ = V14.detect_changepoints(signal, pen, min_mag_pct=mag,
                                             local_win=args.local_win,
                                             inter_mask=real_inter)
            hyp_iv = SZ.cps_to_events(cps, is_buffer, len(signal), sz_ranges=sz_ranges)

            hits, tp_check = per_seizure_hits(ref_iv, hyp_iv, total_dur_s)
            for i, (dur, hit) in enumerate(hits):
                rows.append(dict(subject=subj, operating_point=label,
                                 seizure_idx=i, duration_s=dur, hit=hit,
                                 bucket=bucket_of(dur)))

            # sanity check: cross-reference this printed tp by hand against the
            # locked per-subject tp. balanced (mag60/pen1.0) is in
            # szcore_event_level_new_decision19_mag60.csv @ pen=1.0; high_sens
            # (mag50/pen0.5) is in szcore_event_level_new_decision19_mag50.csv
            # @ pen=0.5 (same file, different pen row -- that file already has
            # all 6 pen_mult values from rebuild_ensemble_new_weight.py). A
            # mismatch means STOP and debug before trusting the duration-bucket
            # table -- do not assume this printed number is right just because
            # the script ran without an error.
            ref_file = (f"szcore_event_level_new_decision19_mag{int(mag)}.csv")
            print(f"  [{subj}/{label}] computed tp={tp_check}  <- cross-check by hand "
                  f"against {ref_file} @ pen={pen}")

    df = pd.DataFrame(rows)
    df.to_csv(out / "duration_hit_persubject.csv", index=False)

    print("\n" + "=" * 78)
    print("POOLED sensitivity by duration bucket (micro, across all 8 subjects)")
    print("=" * 78)
    summary = []
    for label, _, _ in OPERATING_POINTS:
        d = df[df.operating_point == label]
        for lo, hi, bname in BUCKETS:
            b = d[d.bucket == bname]
            if b.empty:
                continue
            n = len(b); tp = int(b.hit.sum())
            summary.append(dict(operating_point=label, bucket=bname, n=n, tp=tp,
                                sensitivity=round(tp / n, 3) if n else float("nan")))
        # overall row for cross-check vs locked pooled sensitivity
        n_all = len(d); tp_all = int(d.hit.sum())
        summary.append(dict(operating_point=label, bucket="ALL", n=n_all, tp=tp_all,
                            sensitivity=round(tp_all / n_all, 3) if n_all else float("nan")))

    sdf = pd.DataFrame(summary)
    sdf.to_csv(out / "duration_bucket_summary.csv", index=False)
    print(sdf.to_string(index=False))
    print(f"\n[check] 'ALL' row per operating_point should equal the locked pooled "
          f"sensitivity: balanced ~0.750 (57/76, mag60/pen1.0, unchanged), "
          f"high_sens ~0.829 (63/76, mag50/pen0.5, Decision #20).")
    print(f"\nWrote to: {out.resolve()}")


if __name__ == "__main__":
    main()