"""
attribution_detail.py  —  per-seizure view of per-node ranking vs manual labels

For each seizure prints: your onset_ch / dominant_ch and WHERE they rank in the model's
full 18-channel per-node ranking (P0 = signed-elevated robust-z), plus the model's top-6
channels. Lets you see, per seizure, how the attribution compares beyond the 3 coloured
channels in the review PNG.

Usage (from repo root):
  python attribution_detail.py --subjects chb15 \
    --pernode_dir "F:/Study/Thesis/Code/data/pernode" \
    --labels_dir  "results/attribution_v5/labels" \
    --summary_dir "F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary"
"""
import argparse, csv, re
from pathlib import Path
import numpy as np

CH = ["FP1-F7","F7-T7","T7-P7","P7-O1","FP1-F3","F3-C3","C3-P3","P3-O1",
      "FP2-F4","F4-C4","C4-P4","P4-O2","FP2-F8","F8-T8","T8-P8","P8-O2","FZ-CZ","CZ-PZ"]
WIN = 4
def _n(s): return re.sub(r'-\d+$','',re.sub(r'\s+','',s).upper().replace("-REF",""))
N2I = {_n(c):i for i,c in enumerate(CH)}

def hms(t): p=t.strip().split(":"); return int(p[0])*3600+int(p[1])*60+int(p[2])
def summary(path):
    txt=Path(path).read_text()
    pat=re.compile(r'File Name:\s*(\S+\.edf)\s+File Start Time:\s*(\S+)\s+File End Time:\s*(\S+)\s+'
                   r'Number of Seizures in File:\s*(\d+)(.*?)(?=File Name:|$)',re.DOTALL)
    e=[]
    for m in pat.finditer(txt):
        fn,t0,t1,ns,rest=m.groups(); d=hms(t1)-hms(t0); d+=86400 if d<=0 else 0; sz=[]
        if int(ns)>0:
            on=[int(x) for x in re.findall(r'Seizure.*?Start Time.*?:\s*(\d+)',rest,re.I)]
            of=[int(x) for x in re.findall(r'Seizure.*?End Time.*?:\s*(\d+)',rest,re.I)]
            sz=list(zip(on,of))
        e.append((fn,d,sz))
    e.sort(key=lambda x:x[0]); return e
def counts(e):
    out=[]
    for fn,d,sz in e:
        nw=d//WIN; tl=nw*WIN
        if tl==0: continue
        sid=np.zeros(d,dtype=np.int32)
        for k,(on,off) in enumerate(sz,1): sid[min(on,d):min(off,d)]=k
        w=sid[:tl].reshape(nw,WIN).max(1)
        for k in range(1,len(sz)+1):
            n=int((w==k).sum())
            if n>0: out.append((fn,sz[k-1][0],sz[k-1][1],n))
    return out
def ix(cell):
    return [N2I[_n(c.strip())] for c in (cell or "").replace(";",",").split(",") if _n(c.strip()) in N2I]
def load(d,subj,split):
    for c in ([f"{subj}_{split}_pernode.npy"]+([f"{subj}_inter_pernode.npy"] if split=="interictal" else [])):
        p=Path(d)/c
        if p.exists(): return np.load(p)
    raise FileNotFoundError(f"{subj} {split}")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--subjects",required=True); ap.add_argument("--pernode_dir",required=True)
    ap.add_argument("--labels_dir",required=True); ap.add_argument("--summary_dir",required=True)
    a=ap.parse_args()
    for subj in a.subjects.split(","):
        try:
            ict=load(a.pernode_dir,subj,"ictal"); inter=load(a.pernode_dir,subj,"interictal")
        except FileNotFoundError as e:
            print(f"[SKIP] {e}"); continue
        med=np.median(inter,0); mad=np.median(np.abs(inter-med),0)+1e-9
        cnt=counts(summary(Path(a.summary_dir)/f"{subj}-summary.txt"))
        bounds=[]; s=0
        for _,_,_,n in cnt: bounds.append((s,min(s+n,len(ict)))); s+=n
        rows={}
        with open(Path(a.labels_dir)/f"labels_{subj}.csv",newline="") as f:
            for r in csv.DictReader(f): rows[int(r["seizure_idx"])]=r
        print(f"\n================ {subj}  (pernode ictal {len(ict)} win, seg_ok={sum(n for *_,n in cnt)==len(ict)}) ================")
        for gi,(ai,bi) in enumerate(bounds):
            r=rows.get(gi,{}); dif=(r.get("diffuse","N") or "N").strip().upper()=="Y"
            z=(ict[ai:bi].mean(0)-med)/mad if bi>ai else np.full(18,np.nan)
            order=list(np.argsort(z)[::-1]); rank={int(order[i]):i+1 for i in range(18)}
            def show(cell):
                out=[]
                for i in ix(cell): out.append(f"{CH[i]}#{rank[i]}(z{z[i]:+.1f})")
                return ", ".join(out) if out else "-"
            top=" ".join(f"{CH[order[i]]}({z[order[i]]:+.1f})" for i in range(6))
            tag=" [DIFFUSE]" if dif else ""
            print(f" sz{gi:<2}{tag}  onset: {show(r.get('onset_ch',''))}   dominant: {show(r.get('dominant_ch',''))}")
            print(f"        model top6: {top}")

if __name__=="__main__":
    main()
