#!/usr/bin/env python3
"""fp_filter_step2b_duration_diag.py -- #23 STEP 2 EXTENSION. Widens the CUSUM-persistence
P sweep down into the lenient region (Step 2 only tested P in [80,97.5], where 18/57 seizures
were already lost at the mildest point) and adds two diagnostics needed to interpret ANY
verdict correctly:

  1. Per-subject TP/FP breakdown at EVERY swept P (Step 2 only printed chb06). Needed because
     a pooled "sz_lost<=2" pass could still hide a subject-specific collapse.
  2. Per-seizure DURATION vs hit/miss at each P, via the same tpMask-introspection technique
     already used and validated in duration_stratified_sensitivity.py (per_seizure_hits).
     This directly tests the hypothesis raised after Step 2: is TP loss concentrated in SHORT
     seizures (CUSUM cannot accumulate persistence before the seizure ends -- an intrinsic
     limitation of a forward-looking persistence filter) or scattered across durations (a
     calibration problem instead, potentially fixable by re-tuning k/POST rather than abandoning
     the approach)? This distinction changes what we are allowed to claim in Chapter 4: an
     intrinsic limitation is an honest negative result; a calibration problem would mean the
     filter deserves another iteration before being retired.

Everything upstream of the filter (ensemble build, timeline reconstruction, PELT+magnitude
filter, CUSUM persistence definition) is UNCHANGED from fp_filter_step2_cusum.py -- this file
only widens P_SWEEP and adds read-only diagnostics. Baseline must still reproduce 57/461/39.77.

Two safety checks not in Step 1:
  - P=0 sanity: keeps ~all cps (threshold = min interictal persistence) -> TP should ~= baseline,
    confirming the filter mechanics don't have an off-by-one/sign bug.
  - Monotonicity: TP must be non-increasing as P increases (stricter threshold can only drop
    seizures, never rescue one) -- printed as a hard check, not just eyeballed.

Kill criteria are UNCHANGED from the Step-2 pre-registration: viable iff some P achieves
>=20% FP/day reduction at <=2 seizures lost (pooled). This file does not change that bar --
it only searches harder for a P that might clear it, and explains the result mechanistically
either way.
"""
import os, sys, glob, csv
import numpy as np
sys.path.insert(0, os.path.abspath(".")); sys.path.insert(0, os.path.abspath("src"))
import ensemble_recipe as ER, evaluation_protocol as E, szcore_eval as SZ, cpd_pipeline_v14 as V14
import duration_stratified_sensitivity as DSS   # reuse the already-validated per_seizure_hits

assert tuple(round(float(w), 3) for w in ER.ENS_WEIGHTS) == (0.40, 0.35, 0.25), "weight drift"
WIN = getattr(E, "WIN_SEC", 4); MAG, PEN = 60, 1.0; POST = 15

# Widened grid: dense in the region below Step 1's mildest point (80), where the practical
# boundary (if one exists) must live, plus the original coarse high end for continuity with
# the already-reported Step-2 numbers.
P_SWEEP = [0, 10, 20, 30, 40, 50, 60, 65, 70, 72.5, 75, 77.5, 80, 85, 90, 92.5, 95, 97.5]

comp_dir = next((d for d in [sys.argv[2] if len(sys.argv) > 2 else None,
                             "data/processed/components"] if d and os.path.isdir(d)), None)
summ_dir = None
if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]) and glob.glob(os.path.join(sys.argv[1], "chb03-summary.txt")):
    summ_dir = sys.argv[1]
if summ_dir is None:
    for h in glob.glob("**/chb03-summary.txt", recursive=True) + glob.glob("../**/chb03-summary.txt", recursive=True):
        summ_dir = os.path.dirname(h); break
assert comp_dir and summ_dir, f"comp_dir={comp_dir} summ_dir={summ_dir}"
print(f"comp_dir={comp_dir}  summ_dir={summ_dir}  point=mag{MAG}/pen{PEN}  POST={POST}")
print(f"P_SWEEP (widened, {len(P_SWEEP)} points) = {P_SWEEP}\n")


def cusum_pers(z, c, k, post):
    S = 0.0; mx = 0.0
    for t in range(c, min(c + post, len(z))):
        S = max(0.0, S + (z[t] - k)); mx = max(mx, S)
    return mx


# precompute per subject (detection is the expensive part; do once) -- identical to Step 1
S = {}
for subj in E.TEST_SUBJS:
    ei, ec = ER.ensemble_for_subject(comp_dir, subj); np.random.seed(0)
    signal, is_ictal, is_buffer, real_inter, sz_ranges, n_inter_h = SZ.build_timeline_masked(subj, ei, ec, summ_dir)
    cps, sm = V14.detect_changepoints(signal, PEN, min_mag_pct=MAG, local_win=15, inter_mask=real_inter)
    k = float(np.percentile(sm[real_inter], 75)) if np.any(real_inter) else 0.0
    pers = {c: cusum_pers(sm, c, k, POST) for c in cps}
    inter_pers = [pers[c] for c in cps if real_inter[c]]
    S[subj] = dict(cps=cps, pers=pers, inter_pers=inter_pers, is_buffer=is_buffer, n=len(signal),
                   sz_ranges=sz_ranges, ref_iv=[(s0 * WIN, s1 * WIN) for s0, s1 in sz_ranges],
                   total=len(signal) * WIN, n_inter_h=n_inter_h)


def run(P):
    """Returns pooled + persubject metrics AND the hyp events per subject (needed for the
    duration diagnostic below, so cps_to_events is never recomputed twice for the same P)."""
    TP = FP = NSZ = 0; IH = 0.0; persub = {}; hyp_by_subj = {}
    for subj, d in S.items():
        if P is None:
            kept = d['cps']
        else:
            h = float(np.percentile(d['inter_pers'], P)) if d['inter_pers'] else 0.0
            kept = [c for c in d['cps'] if d['pers'][c] >= h]
        hyp = SZ.cps_to_events(kept, d['is_buffer'], d['n'], sz_ranges=d['sz_ranges'])
        sc = SZ.score_szcore(d['ref_iv'], hyp, d['total'], d['n_inter_h'])
        TP += sc['tp']; FP += sc['fp']; NSZ += len(d['sz_ranges']); IH += d['n_inter_h']
        persub[subj] = (sc['tp'], sc['fp'], len(d['sz_ranges']))
        hyp_by_subj[subj] = hyp
    return dict(TP=TP, FP=FP, sens=TP / NSZ, fp_day=FP / IH * 24, persub=persub, hyp=hyp_by_subj)


# ---------------------------------------------------------------- baseline
base = run(None)
print(f"BASELINE (no filter): TP={base['TP']} FP={base['FP']} sens={base['sens']:.4f} "
      f"FP/day={base['fp_day']:.2f}   (expect 57 / 461 / 0.7500 / 39.77 -- STOP if this differs)")

# ---------------------------------------------------------------- main sweep
print(f"\n{'P':>6} {'TP':>4} {'sens':>7} {'FP':>5} {'FP/day':>8} {'dFP%':>7} {'sz_lost':>8}")
pooled_rows = []; persubj_rows = []; cand = []
prev_tp = None
for P in P_SWEEP:
    r = run(P)
    lost = base['TP'] - r['TP']; dfp = 100 * (base['fp_day'] - r['fp_day']) / base['fp_day']
    print(f"{P:>6} {r['TP']:>4} {r['sens']:>7.4f} {r['FP']:>5} {r['fp_day']:>8.2f} {dfp:>6.1f}% {lost:>8}")
    pooled_rows.append(dict(P=P, TP=r['TP'], sens=round(r['sens'], 4), FP=r['FP'],
                            fp_day=round(r['fp_day'], 2), dFP_pct=round(dfp, 1), seizures_lost=lost))
    for subj, (tp, fp, nsz) in r['persub'].items():
        persubj_rows.append(dict(P=P, subject=subj, tp=tp, fp=fp, n_seizures=nsz))
    r['_P'] = P; r['_lost'] = lost; r['_dfp'] = dfp
    cand.append(r)
    if prev_tp is not None and r['TP'] > prev_tp:
        print(f"  !! MONOTONICITY VIOLATION at P={P}: TP rose from {prev_tp} to {r['TP']} -- "
              f"this should be impossible (a stricter threshold cannot rescue a seizure). "
              f"STOP and investigate before trusting anything above.")
    prev_tp = r['TP']

results_by_P = {r['_P']: r for r in cand}; results_by_P[None] = base

# ---------------------------------------------------------------- P=0 sanity
p0 = results_by_P[0]
print(f"\nP=0 sanity check: TP={p0['TP']} FP={p0['FP']}  (expect TP ~= baseline {base['TP']}; "
      f"a large gap here would indicate a filter-mechanics bug, not a real effect)")

# ---------------------------------------------------------------- chb06 across the full grid
print("\n-- chb06 (fragile subject, must keep its TP) across the full P grid --")
print(f"   baseline chb06: TP={base['persub']['chb06'][0]} FP={base['persub']['chb06'][1]}")
for r in cand:
    print(f"   P={r['_P']:>5}: chb06 TP={r['persub']['chb06'][0]} FP={r['persub']['chb06'][1]}")

# ---------------------------------------------------------------- per-subject table, every P
print("\n-- Per-subject TP at every swept P (columns = subjects) --")
subj_list = list(S.keys())
print("P".rjust(6) + "".join(s.rjust(9) for s in subj_list))
print("base".rjust(6) + "".join(str(base['persub'][s][0]).rjust(9) for s in subj_list))
for r in cand:
    print(f"{r['_P']:>6}" + "".join(str(r['persub'][s][0]).rjust(9) for s in subj_list))

# ---------------------------------------------------------------- cliff point
viable_all = [r for r in cand if r['_lost'] <= 2]
if viable_all:
    cliff_P = max(r['_P'] for r in viable_all)
    cliff_r = next(r for r in cand if r['_P'] == cliff_P)
    print(f"\nCLIFF: largest P with sz_lost<=2 is P={cliff_P} "
          f"(sz_lost={cliff_r['_lost']}, dFP%={cliff_r['_dfp']:.1f}%)")
else:
    worst_best = min(cand, key=lambda r: r['_lost'])
    print(f"\nCLIFF: no P in the widened grid keeps sz_lost<=2. "
          f"Smallest loss observed anywhere: {worst_best['_lost']} seizures at P={worst_best['_P']}.")

# ---------------------------------------------------------------- duration diagnostic
print("\n" + "=" * 78)
print("DURATION DIAGNOSTIC -- is TP loss concentrated in short seizures (intrinsic CUSUM")
print("limit) or scattered across durations (a calibration problem instead)?")
print("=" * 78)


def per_seizure_table(P):
    r = results_by_P[P]
    out = []
    for subj, d in S.items():
        hits, _tp_check = DSS.per_seizure_hits(d['ref_iv'], r['hyp'][subj], d['total'])
        for i, (dur, hit) in enumerate(hits):
            out.append(dict(subject=subj, seizure_idx=i, duration_s=dur, hit=hit, P=P))
    return out


base_table = per_seizure_table(None)
base_hit_key = {(row['subject'], row['seizure_idx']): row['hit'] for row in base_table}
diag_rows = list(base_table)

first_loss_P = next((r['_P'] for r in cand if r['_lost'] > 0), None)
first_gt2_P = next((r['_P'] for r in cand if r['_lost'] > 2), None)
representative_Ps = sorted(set(p for p in [first_loss_P, first_gt2_P, 80] if p is not None))

for P in representative_Ps:
    table = per_seizure_table(P)
    diag_rows.extend(table)
    lost_durs = [row['duration_s'] for row in table
                if base_hit_key.get((row['subject'], row['seizure_idx']), False) and not row['hit']]
    kept_durs = [row['duration_s'] for row in table
                if base_hit_key.get((row['subject'], row['seizure_idx']), False) and row['hit']]
    if lost_durs:
        print(f"\nP={P}: {len(lost_durs)} newly-lost seizures (vs baseline), duration (s): "
              f"mean={np.mean(lost_durs):.1f} median={np.median(lost_durs):.1f} "
              f"range=[{min(lost_durs):.0f},{max(lost_durs):.0f}]")
        if kept_durs:
            print(f"       {len(kept_durs)} still-hit seizures, duration (s): "
                  f"mean={np.mean(kept_durs):.1f} median={np.median(kept_durs):.1f} "
                  f"range=[{min(kept_durs):.0f},{max(kept_durs):.0f}]")
        else:
            print("       (no seizures remain hit at this P)")
    else:
        print(f"\nP={P}: no newly-lost seizures relative to baseline.")

# ---------------------------------------------------------------- verdict (unchanged kill criteria)
viable = [r for r in cand if r['_lost'] <= 2 and r['_dfp'] >= 20]
if viable:
    best = max(viable, key=lambda r: r['_dfp'])
    print(f"\nVERDICT: VIABLE. Best P={best['_P']} -> sens {best['sens']:.4f} "
          f"(lost {best['_lost']} sz), FP/day {best['fp_day']:.2f} (-{best['_dfp']:.1f}%)")
else:
    print("\nVERDICT: NO P in the widened grid achieves >=20% FP/day cut at <=2 seizure loss "
          "-> report as a null result, using the duration diagnostic above to state the "
          "mechanism (intrinsic vs calibration) honestly in Chapter 4.")

# ---------------------------------------------------------------- write outputs
os.makedirs("results/phaseB", exist_ok=True)
with open("results/phaseB/fp_filter_step2b_pooled.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(pooled_rows[0].keys())); w.writeheader(); w.writerows(pooled_rows)
with open("results/phaseB/fp_filter_step2b_persubject.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(persubj_rows[0].keys())); w.writeheader(); w.writerows(persubj_rows)
with open("results/phaseB/fp_filter_step2b_duration_diag.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(diag_rows[0].keys())); w.writeheader(); w.writerows(diag_rows)
print("\n[done] wrote results/phaseB/fp_filter_step2b_{pooled,persubject,duration_diag}.csv. "
      "Read-only otherwise -- no locked file touched.")