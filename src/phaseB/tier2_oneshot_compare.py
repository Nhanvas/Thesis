"""
tier2_oneshot_compare.py — CURSOR CPU. THE one-shot TEST comparison (Amendment A1).

Derives the operating cell on VAL (frozen, committed BEFORE test), applies it ONCE to the TEST
grid, and reports rlg (headline) + lg (secondary) vs the locked §0 baseline three ways:
  (1) matched-cell: TEST at §0's exact cells (mag70/pen0.5, mag55/pen0.3) — apples-to-apples.
  (2) held-out: TEST at the VAL-derived pooled-nearest-B cell (proper held-out OP).
  (3) full TEST Pareto frontier vs §0's two points (Pareto-dominance = "even across all metrics").
refTrue-correct pooling (TEST: n_seizures==refTrue; VAL: chb11 5 ref-events).

USAGE
  python tier2_oneshot_compare.py --tier2_dir results/phaseB/tier2 --seed 42 \
    --s0_test results/retrain_v3p1/final_eval_seed42.csv \
    --out results/phaseB/tier2/ONESHOT_rlg_vs_s0.csv
"""
import argparse
from pathlib import Path
import numpy as np, pandas as pd

S0_BAL = (70.0, 0.5); S0_HI = (55.0, 0.3)  # §0 published cells
B_BAL, B_HI = 40.0, 75.0

def reftrue(df):
    out={}
    for s,g in df.groupby("subject"):
        gg=g[g.sensitivity>0]
        out[s]=int(round((gg.tp/gg.sensitivity).median())) if len(gg) else int(g.n_seizures.iloc[0])
    return out

def pooled(g, rt):
    TP,FP=int(g.tp.sum()),int(g.fp.sum()); RT=sum(rt[s] for s in g.subject); H=float(g.n_inter_h.sum())
    sens=TP/RT if RT else 0; prec=TP/(TP+FP) if TP+FP else 0
    f1=2*prec*sens/(prec+sens) if prec+sens else 0
    return dict(sens=sens,prec=prec,f1=f1,fpday=FP/(H/24) if H else 0,TP=TP,FP=FP,RT=RT)

def cell(df, rt, m, p):
    g=df[(df.mag_pct==m)&(df.pen_mult==p)]
    return pooled(g, rt) if len(g) else None

def nearest_cell(df, rt, B):
    best=None
    for (m,p),g in df.groupby(["mag_pct","pen_mult"]):
        c=pooled(g,rt); c["mag"],c["pen"]=m,p
        if best is None or abs(c["fpday"]-B)<abs(best["fpday"]-B): best=c
    return best

def row(tag, label, c):
    return dict(candidate=tag, view=label, cell=f"m{int(c['mag'])}/p{c['pen']}" if 'mag' in c else "",
                sens=round(c['sens'],3), prec=round(c['prec'],3), f1=round(c['f1'],3),
                fpday=round(c['fpday'],1), TP=c['TP'], FP=c['FP'])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--tier2_dir", default="results/phaseB/tier2")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--s0_test", default="results/retrain_v3p1/final_eval_seed42.csv")
    ap.add_argument("--cands", default="rlg,lg")
    ap.add_argument("--out", default="results/phaseB/tier2/ONESHOT_rlg_vs_s0.csv")
    a=ap.parse_args(); td=Path(a.tier2_dir); S=a.seed
    out=[]

    # §0 reference (recompute from committed TEST grid at published cells)
    s0=pd.read_csv(a.s0_test); rt0=reftrue(s0)
    for lab,(m,p) in [("§0 balanced",S0_BAL),("§0 high-sens",S0_HI)]:
        c=cell(s0,rt0,m,p); c["mag"],c["pen"]=m,p; out.append(row("§0", lab, c))

    for tag in a.cands.split(","):
        vgrid=pd.read_csv(td/tag/f"final_eval_seed{S}.csv")            # VAL (frozen OP source)
        tgrid=pd.read_csv(td/f"{tag}_test"/f"final_eval_seed{S}.csv")  # TEST (one-shot)
        rtv, rtt = reftrue(vgrid), reftrue(tgrid)
        # (1) matched-cell: TEST at §0 cells
        for lab,(m,p) in [("@§0 bal cell",S0_BAL),("@§0 hi cell",S0_HI)]:
            c=cell(tgrid,rtt,m,p); c["mag"],c["pen"]=m,p; out.append(row(tag,lab,c))
        # (2) held-out: VAL-derived cell applied to TEST
        for lab,B in [("VAL-OP bal",B_BAL),("VAL-OP hi",B_HI)]:
            vc=nearest_cell(vgrid,rtv,B); tc=cell(tgrid,rtt,vc["mag"],vc["pen"])
            tc["mag"],tc["pen"]=vc["mag"],vc["pen"]; out.append(row(tag,lab,tc))

    R=pd.DataFrame(out); R.to_csv(a.out,index=False)
    print(R.to_string(index=False)); print(f"\n[written] {a.out}")

    # (3) full TEST Pareto for headline (first cand)
    tag=a.cands.split(",")[0]; tgrid=pd.read_csv(td/f"{tag}_test"/f"final_eval_seed{S}.csv"); rtt=reftrue(tgrid)
    fr=[]
    for (m,p),g in tgrid.groupby(["mag_pct","pen_mult"]):
        c=pooled(g,rtt); fr.append((round(c['fpday'],1),round(c['sens'],3),round(c['prec'],3),round(c['f1'],3)))
    fr=sorted(fr)
    print(f"\n=== {tag} TEST Pareto (FP/day, sens, prec, F1) — compare vs §0 0.632@38.6 / 0.776@72.7 ===")
    for fp,se,pr,f1 in fr: print(f"  {fp:6.1f}  sens {se:.3f}  prec {pr:.3f}  F1 {f1:.3f}")

if __name__=="__main__":
    main()
