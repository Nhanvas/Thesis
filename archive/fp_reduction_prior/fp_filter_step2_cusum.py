#!/usr/bin/env python3
"""fp_filter_step2_cusum.py -- #23 STEP 2. Label-free CUSUM persistence post-filter, measured at
the SEIZURE level via the authoritative timescoring path, at the locked balanced point (mag60/pen1.0).

Filter: for each detected change-point c, persistence(c) = max CUSUM of the smoothed ensemble z over
[c, c+POST], with allowance k = per-subject interictal 75th-pct (label-free). Keep c iff
persistence(c) >= h, where h = P-th percentile of persistence over INTERICTAL cps (same calibration
philosophy as the locked magnitude filter). P is the single GLOBAL knob (swept). The filter drops
cps BEFORE cps_to_events; everything downstream is the untouched authoritative path.

Baseline (no filter) must reproduce 57 TP / 461 FP / 0.750 / 39.77 first. Writes ONE sweep CSV."""
import os, sys, glob, csv
import numpy as np
sys.path.insert(0, os.path.abspath(".")); sys.path.insert(0, os.path.abspath("src"))
import ensemble_recipe as ER, evaluation_protocol as E, szcore_eval as SZ, cpd_pipeline_v14 as V14

assert tuple(round(float(w),3) for w in ER.ENS_WEIGHTS)==(0.40,0.35,0.25), "weight drift"
WIN=getattr(E,"WIN_SEC",4); MAG,PEN=60,1.0; POST=15
P_SWEEP=[80,85,90,92.5,95,97.5]

comp_dir=next((d for d in [sys.argv[2] if len(sys.argv)>2 else None,"data/processed/components"] if d and os.path.isdir(d)),None)
summ_dir=None
if len(sys.argv)>1 and os.path.isdir(sys.argv[1]) and glob.glob(os.path.join(sys.argv[1],"chb03-summary.txt")): summ_dir=sys.argv[1]
if summ_dir is None:
    for h in glob.glob("**/chb03-summary.txt",recursive=True)+glob.glob("../**/chb03-summary.txt",recursive=True):
        summ_dir=os.path.dirname(h); break
assert comp_dir and summ_dir, f"comp_dir={comp_dir} summ_dir={summ_dir}"
print(f"comp_dir={comp_dir}  summ_dir={summ_dir}  point=mag{MAG}/pen{PEN}  POST={POST}")

def cusum_pers(z,c,k,post):
    S=0.0; mx=0.0
    for t in range(c, min(c+post,len(z))):
        S=max(0.0,S+(z[t]-k)); mx=max(mx,S)
    return mx

# precompute per subject (detection is the expensive part; do once)
S={}
for subj in E.TEST_SUBJS:
    ei,ec=ER.ensemble_for_subject(comp_dir,subj); np.random.seed(0)
    signal,is_ictal,is_buffer,real_inter,sz_ranges,n_inter_h=SZ.build_timeline_masked(subj,ei,ec,summ_dir)
    cps,sm=V14.detect_changepoints(signal,PEN,min_mag_pct=MAG,local_win=15,inter_mask=real_inter)
    k=float(np.percentile(sm[real_inter],75)) if np.any(real_inter) else 0.0
    pers={c:cusum_pers(sm,c,k,POST) for c in cps}
    inter_pers=[pers[c] for c in cps if real_inter[c]]
    S[subj]=dict(cps=cps,pers=pers,inter_pers=inter_pers,is_buffer=is_buffer,n=len(signal),
                 sz_ranges=sz_ranges,ref_iv=[(s*WIN,e*WIN) for s,e in sz_ranges],
                 total=len(signal)*WIN,n_inter_h=n_inter_h)

def run(P):
    TP=FP=NSZ=0; IH=0.0; persub={}
    for subj,d in S.items():
        if P is None:
            kept=d['cps']
        else:
            h=float(np.percentile(d['inter_pers'],P)) if d['inter_pers'] else 0.0
            kept=[c for c in d['cps'] if d['pers'][c]>=h]
        hyp=SZ.cps_to_events(kept,d['is_buffer'],d['n'],sz_ranges=d['sz_ranges'])
        sc=SZ.score_szcore(d['ref_iv'],hyp,d['total'],d['n_inter_h'])
        TP+=sc['tp']; FP+=sc['fp']; NSZ+=len(d['sz_ranges']); IH+=d['n_inter_h']
        persub[subj]=(sc['tp'],sc['fp'],len(d['sz_ranges']))
    return dict(TP=TP,FP=FP,sens=TP/NSZ,fp_day=FP/IH*24,persub=persub)

base=run(None)
print(f"\nBASELINE (no filter): TP={base['TP']} FP={base['FP']} sens={base['sens']:.4f} FP/day={base['fp_day']:.2f}")
print("  (expect 57 / 461 / 0.7500 / 39.77)")

print(f"\n{'P':>6} {'TP':>4} {'sens':>7} {'FP':>5} {'FP/day':>8} {'dFP%':>7} {'sz_lost':>8}")
rows=[]
for P in P_SWEEP:
    r=run(P); lost=base['TP']-r['TP']; dfp=100*(base['fp_day']-r['fp_day'])/base['fp_day']
    print(f"{P:>6} {r['TP']:>4} {r['sens']:>7.4f} {r['FP']:>5} {r['fp_day']:>8.2f} {dfp:>6.1f}% {lost:>8}")
    rows.append(dict(P=P,TP=r['TP'],sens=round(r['sens'],4),FP=r['FP'],fp_day=round(r['fp_day'],2),
                     dFP_pct=round(dfp,1),seizures_lost=lost))
    r['_lost']=lost; r['_dfp']=dfp; r['_P']=P

# best P with <=2 seizure loss
cand=[run(P) for P in P_SWEEP]
for c,P in zip(cand,P_SWEEP): c['_P']=P; c['_lost']=base['TP']-c['TP']; c['_dfp']=100*(base['fp_day']-c['fp_day'])/base['fp_day']
viable=[c for c in cand if c['_lost']<=2 and c['_dfp']>=20]
print("\n-- chb06 (fragile, must keep its TP) per P --")
print(f"   baseline chb06: TP={base['persub']['chb06'][0]} FP={base['persub']['chb06'][1]}")
for c in cand:
    print(f"   P={c['_P']:>5}: chb06 TP={c['persub']['chb06'][0]} FP={c['persub']['chb06'][1]}")
if viable:
    best=max(viable,key=lambda c:c['_dfp'])
    print(f"\nVERDICT: VIABLE. Best P={best['_P']} -> sens {best['sens']:.4f} (lost {best['_lost']} sz), "
          f"FP/day {best['fp_day']:.2f} (-{best['_dfp']:.1f}%)")
else:
    print("\nVERDICT: NO P achieves >=20% FP/day cut at <=2 seizure loss -> report null.")

out="results/phaseB/fp_filter_step2_sweep.csv"; os.makedirs(os.path.dirname(out),exist_ok=True)
with open(out,"w",newline="") as f: w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(f"[done] wrote {out}. Otherwise read-only.")