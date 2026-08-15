"""
compare_labels_pernode.py  —  PREREG_05 agreement preview (PROVISIONAL)

Compares GAE per-node attribution against manual channel labels (onset_ch / dominant_ch).
Runs THREE per-node signals so you can see whether the z-score is the weak link:
  P0  = signed-elevated robust-z:  (mean_ictal - med_inter) / MAD_inter      (thesis default)
  A1  = raw baseline-subtracted:   mean_ictal - mean_inter   (NO MAD scaling; "what the eye sees")
  |z| = |P0|                                                    (old code default)
Metric = top-k hit (NOT AUC): for each non-diffuse seizure, is >=1 labelled channel in
the model's top-k? Reports onset hit@3 for all 3 signals + medRank/MRR (P0) + dominant hit@3 (P0),
per subject and pooled. diffuse=Y excluded (count shown). Chance printed (hit@3 ~ 0.17-0.31, NOT 0.5).

Reads files directly:
  pernode : {pernode_dir}/{subj}_ictal_pernode.npy  and  {subj}_interictal_pernode.npy
  labels  : {labels_dir}/labels_{subj}.csv   (must be the FILLED versions, not blank templates)
  summary : {summary_dir}/{subj}-summary.txt

Usage (Git Bash, from repo root):
  python compare_labels_pernode.py \
    --subjects chb17,chb03,chb06,chb18,chb14,chb16,chb13,chb15 \
    --pernode_dir "F:/Study/Thesis/Code/data/pernode" \
    --labels_dir  "results/attribution_v5/labels" \
    --summary_dir "F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary"
"""
import argparse, csv, re
from math import comb
from pathlib import Path
import numpy as np

CH_NAMES = ["FP1-F7","F7-T7","T7-P7","P7-O1","FP1-F3","F3-C3","C3-P3","P3-O1",
            "FP2-F4","F4-C4","C4-P4","P4-O2","FP2-F8","F8-T8","T8-P8","P8-O2","FZ-CZ","CZ-PZ"]
WIN_SEC = 4
def _norm(s): return re.sub(r'-\d+$', '', re.sub(r'\s+', '', s).upper().replace("-REF", ""))
NORM2IX = {_norm(c): i for i, c in enumerate(CH_NAMES)}

def parse_time_hms(t):
    p = t.strip().split(":"); return int(p[0])*3600+int(p[1])*60+int(p[2])

def parse_summary(path):
    text = Path(path).read_text()
    pat = re.compile(r'File Name:\s*(\S+\.edf)\s+File Start Time:\s*(\S+)\s+File End Time:\s*(\S+)\s+'
                     r'Number of Seizures in File:\s*(\d+)(.*?)(?=File Name:|$)', re.DOTALL)
    edfs = []
    for m in pat.finditer(text):
        fname, t0, t1, nsz, rest = m.groups()
        dur = parse_time_hms(t1)-parse_time_hms(t0); dur += 86400 if dur <= 0 else 0
        szs = []
        if int(nsz) > 0:
            ons = [int(x) for x in re.findall(r'Seizure.*?Start Time.*?:\s*(\d+)', rest, re.I)]
            ofs = [int(x) for x in re.findall(r'Seizure.*?End Time.*?:\s*(\d+)', rest, re.I)]
            szs = list(zip(ons, ofs))
        edfs.append(dict(fname=fname, dur=dur, szs=szs))
    edfs.sort(key=lambda x: x['fname'])
    return edfs

def seizure_window_counts(edfs):
    counts = []
    for e in edfs:
        n_win = e['dur']//WIN_SEC; tl = n_win*WIN_SEC
        if tl == 0: continue
        sid = np.zeros(e['dur'], dtype=np.int32)
        for k,(on,off) in enumerate(e['szs'], start=1):
            sid[min(on,e['dur']):min(off,e['dur'])] = k
        wsid = sid[:tl].reshape(n_win, WIN_SEC).max(axis=1)
        for k in range(1, len(e['szs'])+1):
            n = int((wsid == k).sum())
            if n > 0: counts.append(n)
    return counts

def idx_list(cell):
    out = []
    for c in (cell or "").replace(";", ",").split(","):
        n = _norm(c.strip())
        if n in NORM2IX: out.append(NORM2IX[n])
    return out

def hit_chance(L, k, C=18):
    return float('nan') if L == 0 else 1 - comb(C-L, k)/comb(C, k)

SIGNALS = ["P0", "A1", "absz"]

def attribution(seg, med, mad, mean_inter, sig):
    m = seg.mean(0)
    if sig == "P0":   return (m - med)/mad          # signed elevated
    if sig == "A1":   return m - mean_inter          # raw, no scaling
    if sig == "absz": return np.abs((m - med)/mad)   # |z|

def load_pernode(d, subj, split):
    cands = [f"{subj}_{split}_pernode.npy"]
    if split == "interictal":
        cands += [f"{subj}_inter_pernode.npy", f"{subj}_interictal_pernode.npy"]
    for c in cands:
        p = Path(d) / c
        if p.exists():
            return np.load(p)
    raise FileNotFoundError(f"{subj} {split}: none of {cands} in {d}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", required=True)
    ap.add_argument("--pernode_dir", required=True)
    ap.add_argument("--labels_dir", required=True)
    ap.add_argument("--summary_dir", required=True)
    args = ap.parse_args()
    subs = args.subjects.split(",")

    P = {s: {1:[],3:[],5:[],"rank":[],"rr":[]} for s in SIGNALS}          # pooled onset per signal
    Pdom = {1:[],3:[],5:[]}                                               # pooled dominant (P0)
    n_diff_all = n_used_all = 0
    print("\nAttribution vs manual labels. Metric = top-k hit. [PROVISIONAL: AI-draft labels]")
    print(f"{'subj':<7}{'nsz':>4}{'dif':>4}{'use':>4}   onset hit@3  P0 / A1 / |z|   medRank MRR(P0)   domHit@3")
    print("-"*92)
    for subj in subs:
        pi = Path(args.pernode_dir)/f"{subj}_ictal_pernode.npy"
        pn = Path(args.pernode_dir)/f"{subj}_interictal_pernode.npy"
        lp = Path(args.labels_dir)/f"labels_{subj}.csv"
        for f in (pi, pn, lp):
            if not f.exists():
                print(f"{subj:<7}  [MISSING] {f}"); f = None
        if not (pi.exists() and pn.exists() and lp.exists()): continue
        ict, inter = np.load(pi), np.load(pn)
        med = np.median(inter,0); mad = np.median(np.abs(inter-med),0)+1e-9; mean_inter = inter.mean(0)
        counts = seizure_window_counts(parse_summary(Path(args.summary_dir)/f"{subj}-summary.txt"))
        seg_ok = (sum(counts) == len(ict))
        bounds, s = [], 0
        for c in counts: bounds.append((s, min(s+c, len(ict)))); s += c
        rows = {}
        with open(lp, newline="") as f:
            for r in csv.DictReader(f): rows[int(r["seizure_idx"])] = r

        sub = {sg: {1:[],3:[],5:[],"rank":[],"rr":[]} for sg in SIGNALS}; sdom={1:[],3:[],5:[]}
        n_diff = n_used = 0
        for gi,(a,b) in enumerate(bounds):
            r = rows.get(gi, {})
            if (r.get("diffuse","N") or "N").strip().upper() == "Y": n_diff += 1; continue
            on_labs = idx_list(r.get("onset_ch","")); dom_labs = idx_list(r.get("dominant_ch",""))
            if not on_labs and not dom_labs: continue
            if b <= a: continue
            n_used += 1
            for sg in SIGNALS:
                v = attribution(ict[a:b], med, mad, mean_inter, sg)
                order = list(np.argsort(v)[::-1]); rank = {int(order[i]): i+1 for i in range(18)}
                if on_labs:
                    best = min(rank[i] for i in on_labs)
                    for k in (1,3,5): sub[sg][k].append(1.0 if best<=k else 0.0)
                    sub[sg]["rank"].append(rank[on_labs[0]]); sub[sg]["rr"].append(1.0/rank[on_labs[0]])
                if sg=="P0" and dom_labs:
                    bd = min(rank[i] for i in dom_labs)
                    for k in (1,3,5): sdom[k].append(1.0 if bd<=k else 0.0)
        n_diff_all += n_diff; n_used_all += n_used
        for sg in SIGNALS:
            for key in (1,3,5,"rank","rr"): P[sg][key] += sub[sg][key]
        for k in (1,3,5): Pdom[k]+=sdom[k]
        def mv(d,key,fmt="{:.2f}"): return fmt.format(np.mean(d[key])) if d[key] else " - "
        flag = "" if seg_ok else f"  [!SEG {sum(counts)}vs{len(ict)}]"
        print(f"{subj:<7}{len(bounds):>4}{n_diff:>4}{n_used:>4}   "
              f"{mv(sub['P0'],3)} / {mv(sub['A1'],3)} / {mv(sub['absz'],3)}      "
              f"{mv(sub['P0'],'rank','{:.1f}'):>5} {mv(sub['P0'],'rr')}     {mv(sdom,3)}{flag}")
    print("-"*92)
    def pv(d,key,fmt="{:.3f}"): return fmt.format(np.mean(d[key])) if d[key] else "-"
    print(f"POOLED  ({n_used_all} used, {n_diff_all} diffuse excluded)")
    print(f"  ONSET hit@3:   P0={pv(P['P0'],3)}   A1(raw)={pv(P['A1'],3)}   |z|={pv(P['absz'],3)}")
    print(f"  ONSET (P0):    hit@1={pv(P['P0'],1)}  hit@5={pv(P['P0'],5)}  medRank={pv(P['P0'],'rank','{:.1f}')}  MRR={pv(P['P0'],'rr')}")
    print(f"  DOMINANT (P0): hit@3={pv(Pdom,3)}")
    print(f"  chance hit@3: L=1 ->{hit_chance(1,3):.3f}  L=2 ->{hit_chance(2,3):.3f}   (MRR chance ~0.194)")
    print("\n[PROVISIONAL — AI-draft labels, not supervisor-frozen. For method-check only.]\n")

if __name__ == "__main__":
    main()
