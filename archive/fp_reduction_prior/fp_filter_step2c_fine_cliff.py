#!/usr/bin/env python3
"""fp_filter_step2c_fine_cliff.py -- #23 STEP 2 FINAL REFINEMENT. Step 2b's grid jumped from
P=30 (0 seizures lost, FP/day -8.5%) straight to P=40 (7 seizures lost, FP/day -30.2%) -- a
10-point gap, wider than any other step in that sweep. The pre-registered kill criterion
(>=20% FP/day cut at <=2 seizures lost) could plausibly be satisfied somewhere INSIDE that
unobserved gap. This script does nothing new methodologically -- same filter, same kill
criteria, same per-subject/chb06/duration diagnostics as Step 2b -- it only increases the
resolution of the P grid exactly where the decision boundary lives (P in [28,42], step 1),
which is the same "widen the grid where the boundary might be" move already used going from
Step 2 to Step 2b.

This is the LAST sweep before the #23 verdict is finalized. If no point in [28,42] clears the
kill criteria without disproportionately hurting chb06, the verdict is NULL and the mechanism
(short-seizure dilution in a fixed-window CUSUM, quantified in Step 2b's duration diagnostic)
is what gets reported in Chapter 4 -- not a further widening of scope. A fixed-window CUSUM
redesign (e.g. duration-adaptive lookback) would be a NEW algorithm, not a threshold retune,
and is out of scope for the thesis; if warranted, it is future work for the larger product-scope
project, not squeezed into the remaining thesis weeks.
"""
import os, sys, glob, csv
import numpy as np
sys.path.insert(0, os.path.abspath(".")); sys.path.insert(0, os.path.abspath("src"))
import ensemble_recipe as ER, evaluation_protocol as E, szcore_eval as SZ, cpd_pipeline_v14 as V14
import duration_stratified_sensitivity as DSS

assert tuple(round(float(w), 3) for w in ER.ENS_WEIGHTS) == (0.40, 0.35, 0.25), "weight drift"
WIN = getattr(E, "WIN_SEC", 4); MAG, PEN = 60, 1.0; POST = 15

# Fine grid spanning the unobserved gap from Step 2b (30 -> 40), with a small margin on
# each side (28, 41-42) in case the true boundary sits just outside [30,40].
P_SWEEP = list(range(28, 43))  # 28,29,...,42

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
print(f"P_SWEEP (fine, {len(P_SWEEP)} points spanning the Step-2b gap) = {P_SWEEP}\n")


def cusum_pers(z, c, k, post):
    S = 0.0; mx = 0.0
    for t in range(c, min(c + post, len(z))):
        S = max(0.0, S + (z[t] - k)); mx = max(mx, S)
    return mx


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
    TP = FP = NSZ = 0; IH = 0.0; persub = {}; hyp_by_subj = {}
    for subj, d in S.items():
        h = float(np.percentile(d['inter_pers'], P)) if d['inter_pers'] else 0.0
        kept = [c for c in d['cps'] if d['pers'][c] >= h]
        hyp = SZ.cps_to_events(kept, d['is_buffer'], d['n'], sz_ranges=d['sz_ranges'])
        sc = SZ.score_szcore(d['ref_iv'], hyp, d['total'], d['n_inter_h'])
        TP += sc['tp']; FP += sc['fp']; NSZ += len(d['sz_ranges']); IH += d['n_inter_h']
        persub[subj] = (sc['tp'], sc['fp'], len(d['sz_ranges']))
        hyp_by_subj[subj] = hyp
    return dict(TP=TP, FP=FP, sens=TP / NSZ, fp_day=FP / IH * 24, persub=persub, hyp=hyp_by_subj)


def run_baseline():
    TP = FP = NSZ = 0; IH = 0.0; persub = {}; hyp_by_subj = {}
    for subj, d in S.items():
        hyp = SZ.cps_to_events(d['cps'], d['is_buffer'], d['n'], sz_ranges=d['sz_ranges'])
        sc = SZ.score_szcore(d['ref_iv'], hyp, d['total'], d['n_inter_h'])
        TP += sc['tp']; FP += sc['fp']; NSZ += len(d['sz_ranges']); IH += d['n_inter_h']
        persub[subj] = (sc['tp'], sc['fp'], len(d['sz_ranges']))
        hyp_by_subj[subj] = hyp
    return dict(TP=TP, FP=FP, sens=TP / NSZ, fp_day=FP / IH * 24, persub=persub, hyp=hyp_by_subj)


base = run_baseline()
print(f"BASELINE (no filter): TP={base['TP']} FP={base['FP']} sens={base['sens']:.4f} "
      f"FP/day={base['fp_day']:.2f}   (expect 57 / 461 / 0.7500 / 39.77 -- STOP if this differs)")
print(f"reference: Step-2b already showed P=30 -> TP=57 (0 lost, -8.5% FP/day), "
      f"P=40 -> TP=50 (7 lost, -30.2% FP/day). Finding the boundary between them below.\n")

print(f"{'P':>6} {'TP':>4} {'sens':>7} {'FP':>5} {'FP/day':>8} {'dFP%':>7} {'sz_lost':>8}")
pooled_rows = []; persubj_rows = []; cand = []; prev_tp = None
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
        print(f"  !! MONOTONICITY VIOLATION at P={P}: TP rose from {prev_tp} to {r['TP']} -- STOP.")
    prev_tp = r['TP']

results_by_P = {r['_P']: r for r in cand}

print("\n-- chb06 across the fine grid (must not be disproportionately hit) --")
print(f"   baseline chb06: TP={base['persub']['chb06'][0]} FP={base['persub']['chb06'][1]}")
for r in cand:
    print(f"   P={r['_P']:>5}: chb06 TP={r['persub']['chb06'][0]} FP={r['persub']['chb06'][1]}")

print("\n-- Per-subject TP at every fine-grid P (columns = subjects) --")
subj_list = list(S.keys())
print("P".rjust(6) + "".join(s.rjust(9) for s in subj_list))
print("base".rjust(6) + "".join(str(base['persub'][s][0]).rjust(9) for s in subj_list))
for r in cand:
    print(f"{r['_P']:>6}" + "".join(str(r['persub'][s][0]).rjust(9) for s in subj_list))

# ---------------------------------------------------------------- cliff localization
exact_transitions = []
prev_lost = 0
for r in cand:
    if r['_lost'] != prev_lost:
        exact_transitions.append((r['_P'], prev_lost, r['_lost']))
    prev_lost = r['_lost']
print("\n-- Exact P where seizure count first drops (cliff localization) --")
for P, before, after in exact_transitions:
    print(f"   at P={P}: sz_lost {before} -> {after}")

viable_all = [r for r in cand if r['_lost'] <= 2]
if viable_all:
    cliff_P = max(r['_P'] for r in viable_all)
    cliff_r = next(r for r in cand if r['_P'] == cliff_P)
    # chb06-specific integrity check: how much of the pooled loss at this P is chb06?
    chb06_lost_here = base['persub']['chb06'][0] - cliff_r['persub']['chb06'][0]
    print(f"\nCLIFF (fine): largest P with sz_lost<=2 is P={cliff_P} "
          f"(sz_lost={cliff_r['_lost']}, dFP%={cliff_r['_dfp']:.1f}%, "
          f"chb06 contributes {chb06_lost_here} of those {cliff_r['_lost']} lost seizures)")
else:
    worst_best = min(cand, key=lambda r: r['_lost'])
    print(f"\nCLIFF (fine): no P in [28,42] keeps sz_lost<=2. "
          f"Smallest loss in this range: {worst_best['_lost']} at P={worst_best['_P']}.")

# ---------------------------------------------------------------- verdict against pre-registered bar
viable = [r for r in cand if r['_lost'] <= 2 and r['_dfp'] >= 20]
print("\n" + "=" * 78)
if viable:
    best = max(viable, key=lambda r: r['_dfp'])
    chb06_lost = base['persub']['chb06'][0] - best['persub']['chb06'][0]
    print(f"VERDICT: VIABLE. Best P={best['_P']} -> sens {best['sens']:.4f} "
          f"(lost {best['_lost']} sz total, chb06 lost {chb06_lost} of those), "
          f"FP/day {best['fp_day']:.2f} (-{best['_dfp']:.1f}%)")
    if chb06_lost > 0:
        print(f"  NOTE: this point costs chb06 {chb06_lost} of its {base['persub']['chb06'][0]} "
              f"baseline TP -- review before adopting; chb06 is the hardest subject and "
              f"pre-registration flagged sacrificing it as disqualifying even if pooled looks fine.")
else:
    # report the best achievable within the strict <=2 constraint, for transparency, even
    # though it doesn't clear the 20% bar
    best_le2 = max([r for r in cand if r['_lost'] <= 2], key=lambda r: r['_dfp'], default=None)
    print("VERDICT: NO P in [28,42] clears the pre-registered bar (>=20% FP/day cut at <=2 "
          "seizures lost).")
    if best_le2:
        print(f"  Best achievable at sz_lost<=2: P={best_le2['_P']} -> dFP%={best_le2['_dfp']:.1f}% "
              f"(sz_lost={best_le2['_lost']}) -- a free/near-free improvement, but well short of 20%.")
    print("  Combined with Step 2b's duration diagnostic (lost seizures are systematically "
          "shorter than retained ones), this is reported as a NULL result for the kill "
          "criterion, with the mechanism (fixed 60s CUSUM window dilutes short-seizure "
          "elevation) as the honest explanation for Chapter 4/Discussion.")
print("=" * 78)

os.makedirs("results/phaseB", exist_ok=True)
with open("results/phaseB/fp_filter_step2c_pooled.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(pooled_rows[0].keys())); w.writeheader(); w.writerows(pooled_rows)
with open("results/phaseB/fp_filter_step2c_persubject.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(persubj_rows[0].keys())); w.writeheader(); w.writerows(persubj_rows)
print("\n[done] wrote results/phaseB/fp_filter_step2c_{pooled,persubject}.csv. Read-only otherwise.")