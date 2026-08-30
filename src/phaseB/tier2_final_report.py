"""
tier2_final_report.py — CURSOR CPU. COMPLETE reporting suite from FROZEN Tier-2 artifacts.
NO new TEST exposure, NO TEST-selection: TEST grids are already committed; every operating point
below is derived on VAL (pooled-nearest-B) and read off the frozen TEST grid. The FULL budget sweep
is reported (B=5,10,20,40,75) so nothing is cherry-picked.

Outputs:
  (A) OP sweep: VAL-derived cell @ each B -> applied to TEST, for rlg (headline) + lg (secondary),
      vs §0 balanced/high-sens. Pooled sens/prec/F1/FP-day (refTrue-correct).
  (B) rlg at §0's exact cells (matched-cell).
  (C) per-subject at the triage OP (B=10, VAL-derived) for rlg.
  (D) window-tier macro AUROC + AUPRC for rlg (from committed ensemble arrays).

USAGE
  python tier2_final_report.py --tier2_dir results/phaseB/tier2 --seed 42 \
    --s0_test results/retrain_v3p1/final_eval_seed42.csv \
    --ens_root results/phaseB/tier2/ens_test_tf \
    --out results/phaseB/tier2/FINAL_report.csv
"""
import argparse
from pathlib import Path
import numpy as np, pandas as pd

S0_BAL=(70.0,0.5); S0_HI=(55.0,0.3)
BUDGETS=[5,10,20,40,75]
TEST_SUBJS=["chb03","chb06","chb13","chb14","chb15","chb16","chb17","chb18"]

def reftrue(df):
    out={}
    for s,g in df.groupby("subject"):
        gg=g[g.sensitivity>0]
        out[s]=int(round((gg.tp/gg.sensitivity).median())) if len(gg) else int(g.n_seizures.iloc[0])
    return out

def pooled(g,rt):
    TP,FP=int(g.tp.sum()),int(g.fp.sum()); RT=sum(rt[s] for s in g.subject); H=float(g.n_inter_h.sum())
    sens=TP/RT if RT else 0; prec=TP/(TP+FP) if TP+FP else 0
    f1=2*prec*sens/(prec+sens) if prec+sens else 0
    return dict(sens=sens,prec=prec,f1=f1,fpday=FP/(H/24) if H else 0,TP=TP,FP=FP)

def cell(df,rt,m,p):
    g=df[(df.mag_pct==m)&(df.pen_mult==p)]; return pooled(g,rt) if len(g) else None

def nearest_cell(df,rt,B):
    best=None
    for (m,p),g in df.groupby(["mag_pct","pen_mult"]):
        c=pooled(g,rt); c["mag"],c["pen"]=m,p
        if best is None or abs(c["fpday"]-B)<abs(best["fpday"]-B): best=c
    return best

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--tier2_dir",default="results/phaseB/tier2")
    ap.add_argument("--seed",type=int,default=42)
    ap.add_argument("--s0_test",default="results/retrain_v3p1/final_eval_seed42.csv")
    ap.add_argument("--ens_root",default="results/phaseB/tier2/ens_test_tf")
    ap.add_argument("--cands",default="rlg,lg")
    ap.add_argument("--triage_B",type=int,default=10)
    ap.add_argument("--out",default="results/phaseB/tier2/FINAL_report.csv")
    a=ap.parse_args(); td=Path(a.tier2_dir); S=a.seed

    s0=pd.read_csv(a.s0_test); rt0=reftrue(s0)
    s0b=cell(s0,rt0,*S0_BAL); s0h=cell(s0,rt0,*S0_HI)
    print("=== §0 reference ===")
    print(f"  balanced  m70/p0.5: sens {s0b['sens']:.3f} prec {s0b['prec']:.3f} F1 {s0b['f1']:.3f} @ {s0b['fpday']:.1f}")
    print(f"  high-sens m55/p0.3: sens {s0h['sens']:.3f} prec {s0h['prec']:.3f} F1 {s0h['f1']:.3f} @ {s0h['fpday']:.1f}")

    rows=[]
    for tag in a.cands.split(","):
        vg=pd.read_csv(td/tag/f"final_eval_seed{S}.csv")
        tg=pd.read_csv(td/f"{tag}_test"/f"final_eval_seed{S}.csv")
        rtv,rtt=reftrue(vg),reftrue(tg)
        print(f"\n=== {tag}: VAL-derived OP sweep -> applied to frozen TEST ===")
        print(f"  {'B':>4} {'VALcell':>10} {'TEST_FP/d':>9} {'sens':>6} {'prec':>6} {'F1':>6}")
        for B in BUDGETS:
            vc=nearest_cell(vg,rtv,B); tc=cell(tg,rtt,vc["mag"],vc["pen"])
            print(f"  {B:>4} m{int(vc['mag'])}/p{vc['pen']:<5} {tc['fpday']:>9.1f} {tc['sens']:>6.3f} {tc['prec']:>6.3f} {tc['f1']:>6.3f}")
            rows.append(dict(cand=tag,view=f"VAL-OP B={B}",cell=f"m{int(vc['mag'])}/p{vc['pen']}",
                             fpday=round(tc['fpday'],1),sens=round(tc['sens'],3),prec=round(tc['prec'],3),
                             f1=round(tc['f1'],3),TP=tc['TP'],FP=tc['FP']))
        # matched §0 cells
        for lab,(m,p) in [("@§0 bal",S0_BAL),("@§0 hi",S0_HI)]:
            c=cell(tg,rtt,m,p)
            rows.append(dict(cand=tag,view=lab,cell=f"m{int(m)}/p{p}",fpday=round(c['fpday'],1),
                             sens=round(c['sens'],3),prec=round(c['prec'],3),f1=round(c['f1'],3),TP=c['TP'],FP=c['FP']))

    # (C) per-subject at triage OP for headline
    tag=a.cands.split(",")[0]; vg=pd.read_csv(td/tag/f"final_eval_seed{S}.csv"); tg=pd.read_csv(td/f"{tag}_test"/f"final_eval_seed{S}.csv")
    vc=nearest_cell(vg,reftrue(vg),a.triage_B)
    print(f"\n=== {tag} per-subject @ triage OP B={a.triage_B} (VAL cell m{int(vc['mag'])}/p{vc['pen']}) ===")
    g=tg[(tg.mag_pct==vc['mag'])&(tg.pen_mult==vc['pen'])]
    print(f"  {'subj':>6} {'nsz':>3} {'TP':>3} {'FP':>4} {'sens':>6} {'prec':>6} {'F1':>6} {'FP/d':>6}")
    for _,r in g.iterrows():
        tp,fp,ns=int(r.tp),int(r.fp),int(r.n_seizures)
        se=tp/ns if ns else 0; pr=tp/(tp+fp) if tp+fp else 0; f1=2*pr*se/(pr+se) if pr+se else 0
        print(f"  {r.subject:>6} {ns:>3} {tp:>3} {fp:>4} {se:>6.3f} {pr:>6.3f} {f1:>6.3f} {r.fp_per_day:>6.1f}")

    # (D) window macro AUROC/AUPRC for headline
    try:
        from sklearn.metrics import roc_auc_score, average_precision_score
        au,ap_=[],[]
        for subj in TEST_SUBJS:
            zi=np.load(f"{a.ens_root}/{tag}/ens_seed{S}_{subj}_inter.npy")
            zc=np.load(f"{a.ens_root}/{tag}/ens_seed{S}_{subj}_ictal.npy")
            y=np.r_[np.zeros(len(zi)),np.ones(len(zc))]; s=np.r_[zi,zc]
            au.append(roc_auc_score(y,s)); ap_.append(average_precision_score(y,s))
        print(f"\n=== {tag} window-tier: macro AUROC {np.mean(au):.3f}  macro AUPRC {np.mean(ap_):.3f}  (§0 AUROC 0.775) ===")
    except Exception as e:
        print(f"[window suite skipped: {e}]")

    pd.DataFrame(rows).to_csv(a.out,index=False); print(f"\n[written] {a.out}")

if __name__=="__main__":
    main()
