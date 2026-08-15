import re, csv, numpy as np
from pathlib import Path
from math import comb
WIN_SEC=4; UP='/mnt/user-data/uploads'; LB='/mnt/user-data/outputs'
CH=["FP1-F7","F7-T7","T7-P7","P7-O1","FP1-F3","F3-C3","C3-P3","P3-O1",
    "FP2-F4","F4-C4","C4-P4","P4-O2","FP2-F8","F8-T8","T8-P8","P8-O2","FZ-CZ","CZ-PZ"]
IDX={c:i for i,c in enumerate(CH)}
SUBS=["chb03","chb06","chb13","chb14","chb15","chb16","chb17","chb18"]
def ptime(s): h,m,x=[int(v) for v in s.split(':')]; return h*3600+m*60+x
def edflist(subj):
    t=Path(f'{subj}-summary.txt').read_text()
    pat=re.compile(r'File Name:\s*(\S+\.edf)\s+File Start Time:\s*(\S+)\s+File End Time:\s*(\S+)\s+Number of Seizures in File:\s*(\d+)(.*?)(?=File Name:|$)',re.DOTALL)
    E=[]
    for m in pat.finditer(t):
        fn,t0,t1,ns,rest=m.groups(); d=ptime(t1)-ptime(t0)
        if d<=0: d+=86400
        szs=[]
        if int(ns)>0:
            on=[int(x) for x in re.findall(r'Seizure.*?Start Time.*?:\s*(\d+)',rest,re.I)]
            of=[int(x) for x in re.findall(r'Seizure.*?End Time.*?:\s*(\d+)',rest,re.I)]
            szs=list(zip(on,of))
        E.append({'fname':fn,'seizures':szs,'dur':d})
    E.sort(key=lambda x:x['fname']); return E
def blocks(subj):
    out=[]; ptr=0
    for e in edflist(subj):
        d=int(e['dur']); nw=d//WIN_SEC; tl=nw*WIN_SEC
        if tl==0: continue
        sid=np.zeros(d,dtype=np.int32)
        for k,(on,off) in enumerate(e['seizures'],1): sid[min(on,d):min(off,d)]=k
        ws=sid[:tl].reshape(nw,WIN_SEC).max(1)
        loc={k:[] for k in range(1,len(e['seizures'])+1)}
        for w in range(nw):
            if ws[w]>0: loc[int(ws[w])].append(ptr); ptr+=1
        for k in range(1,len(e['seizures'])+1):
            if loc[k]: out.append(np.array(loc[k]))
    return out

def parse_dom(row):
    raw=(row.get('dominant_ch') or '').strip()
    idx=[IDX[t.strip()] for t in raw.split(',') if t.strip() in IDX]
    return idx

print(f"{'subj':<7}{'nSz':>4}{'diff':>5}{'foc':>4}  {'hit@1':>6}{'hit@3':>6}{'hit@5':>6}{'medR':>6}{'ch@3':>6}")
print('-'*54)
POOL={'h1':[],'h3':[],'h5':[],'rank':[],'c3':[]}
TOT_SZ=TOT_DIFF=TOT_FOC=0
for s in SUBS:
    ic=np.load(f'{UP}/{s}_ictal_pernode.npy'); it=np.load(f'{UP}/{s}_interictal_pernode.npy')
    med=np.median(it,0); mad=np.median(np.abs(it-med),0)+1e-9
    bl=blocks(s)
    rows=list(csv.DictReader(open(f'{LB}/labels_{s}_FINAL.csv')))
    assert len(bl)==len(rows), f"{s}: {len(bl)} blocks vs {len(rows)} rows"
    h1=h3=h5=foc=diff=0; ranks=[]; chance=[]
    for idxs,row in zip(bl,rows):
        tgt=parse_dom(row)
        if not tgt: diff+=1; continue
        foc+=1
        idxs=idxs[idxs<len(ic)]
        z=(ic[idxs].mean(0)-med)/mad
        order=list(np.argsort(z)[::-1])
        best=min(order.index(c)+1 for c in tgt)
        h1+=best<=1; h3+=best<=3; h5+=best<=5; ranks.append(best)
        L=len(tgt); ch3=1-comb(18-L,3)/comb(18,3); chance.append(ch3)
        POOL['h1'].append(int(best<=1)); POOL['h3'].append(int(best<=3)); POOL['h5'].append(int(best<=5))
        POOL['rank'].append(best); POOL['c3'].append(ch3)
    TOT_SZ+=len(rows); TOT_DIFF+=diff; TOT_FOC+=foc
    if foc:
        print(f"{s:<7}{len(rows):>4}{diff:>5}{foc:>4}  {h1/foc:>6.2f}{h3/foc:>6.2f}{h5/foc:>6.2f}{np.median(ranks):>6.1f}{np.mean(chance):>6.2f}")
    else:
        print(f"{s:<7}{len(rows):>4}{diff:>5}{foc:>4}  {'--':>6}{'--':>6}{'--':>6}{'--':>6}{'--':>6}  (all diffuse)")
print('-'*54)
n=len(POOL['h3'])
print(f"{'POOL':<7}{TOT_SZ:>4}{TOT_DIFF:>5}{TOT_FOC:>4}  {np.mean(POOL['h1']):>6.2f}{np.mean(POOL['h3']):>6.2f}{np.mean(POOL['h5']):>6.2f}{np.median(POOL['rank']):>6.1f}{np.mean(POOL['c3']):>6.2f}")
print(f"\nTong: {TOT_SZ} con | focal(co dominant)={TOT_FOC} | diffuse={TOT_DIFF} ({100*TOT_DIFF/TOT_SZ:.0f}%)")
print("hit@k tinh tren {} con focal. medR chance=9.5. ch@3=chance hit@3.".format(TOT_FOC))
