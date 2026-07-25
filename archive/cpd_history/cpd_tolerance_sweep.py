"""
cpd_tolerance_sweep.py — Tolerance Sensitivity Analysis
Tests ±10s, ±20s, ±30s at pen=0.3, 0.5, 1.0
Reads cached bidirectional gamma ensemble scores. No recomputation.
Usage: python src/cpd_tolerance_sweep.py
"""

import numpy as np
import pandas as pd
import ruptures as rpt
import re
from pathlib import Path

SCORES_DIR  = Path("results/cpd/scores")
RESULTS_DIR = Path("results/cpd")
SUMMARY_DIR = Path(r"F:\Study\Thesis\Dataset\CHB-MIT\CHB info\summary")

WIN_SEC     = 4
BUFFER_H    = 4
MERGE_GAP_S = 32
TOLERANCES  = [10, 20, 30]          # seconds — the sweep
PEN_MULTS   = [0.3, 0.5, 1.0]
TEST_SUBJS  = ["chb03","chb06","chb13","chb14","chb15","chb16","chb17","chb18"]

# ── Summary parsing ─────────────────────────────────────────────────────────
def parse_time_hms(t):
    p = t.strip().split(":"); return int(p[0])*3600+int(p[1])*60+int(p[2])

def parse_summary_edf_list(path):
    text = Path(path).read_text()
    pat  = re.compile(
        r'File Name:\s*(\S+\.edf)\s+File Start Time:\s*(\S+)\s+'
        r'File End Time:\s*(\S+)\s+Number of Seizures in File:\s*(\d+)(.*?)(?=File Name:|$)',
        re.DOTALL)
    edfs = []
    for m in pat.finditer(text):
        fname,t0,t1,nsz,rest = m.groups()
        dur = parse_time_hms(t1) - parse_time_hms(t0)
        if dur <= 0: dur += 86400
        szs = []
        if int(nsz) > 0:
            ons = [int(x) for x in re.findall(r'Seizure.*?Start Time.*?:\s*(\d+)', rest, re.I)]
            ofs = [int(x) for x in re.findall(r'Seizure.*?End Time.*?:\s*(\d+)',   rest, re.I)]
            szs = list(zip(ons, ofs))
        edfs.append({'fname': fname, 'duration_s': dur, 'seizures': szs})
    edfs.sort(key=lambda x: x['fname']); return edfs

# ── Timeline reconstruction (same as v13) ──────────────────────────────────
def build_timeline(subj, inter_scores, ictal_scores):
    np.random.seed(42)
    edfs = parse_summary_edf_list(SUMMARY_DIR / f"{subj}-summary.txt")
    scores_out, is_ictal_out = [], []
    inter_ptr = ictal_ptr = 0; total_inter_s = 0.0
    pool = np.random.choice(inter_scores, size=250000, replace=True); bp = 0

    for edf in edfs:
        dur = edf['duration_s']; n_win = dur // WIN_SEC
        labels = np.zeros(dur, dtype=np.int8); buf = np.zeros(dur, dtype=bool)
        for (on,off) in edf['seizures']:
            on=min(on,dur); off=min(off,dur)
            labels[on:off]=1; buf[off:min(dur,off+BUFFER_H*3600)]=True
        tl = n_win*WIN_SEC
        wl = labels[:tl].reshape(n_win,WIN_SEC).max(axis=1)
        wb = buf[:tl].reshape(n_win,WIN_SEC).any(axis=1)
        for w in range(n_win):
            lbl=int(wl[w]); bfr=bool(wb[w])
            if lbl==1:
                scores_out.append(float(ictal_scores[ictal_ptr]) if ictal_ptr<len(ictal_scores) else 0.0)
                if ictal_ptr<len(ictal_scores): ictal_ptr+=1
                is_ictal_out.append(True)
            elif bfr:
                scores_out.append(float(pool[bp])); bp=(bp+1)%len(pool)
                is_ictal_out.append(False); total_inter_s+=WIN_SEC
            else:
                if inter_ptr<len(inter_scores):
                    scores_out.append(float(inter_scores[inter_ptr])); inter_ptr+=1
                else:
                    scores_out.append(float(pool[bp])); bp=(bp+1)%len(pool)
                is_ictal_out.append(False); total_inter_s+=WIN_SEC

    if inter_ptr<len(inter_scores):
        diff=len(inter_scores)-inter_ptr
        scores_out=np.concatenate([scores_out,inter_scores[inter_ptr:]])
        is_ictal_out.extend([False]*diff); total_inter_s+=diff*WIN_SEC

    scores_out=np.array(scores_out,dtype=np.float32)
    is_ictal=np.array(is_ictal_out,dtype=bool)
    sz_ranges,in_s,ss_idx=[],False,0
    for i,ic in enumerate(is_ictal):
        if ic and not in_s: ss_idx=i; in_s=True
        elif not ic and in_s: sz_ranges.append((ss_idx,i)); in_s=False
    if in_s: sz_ranges.append((ss_idx,len(is_ictal)))
    return scores_out, sz_ranges, total_inter_s/3600.0

# ── PELT (same as v13) ──────────────────────────────────────────────────────
def run_pelt_all(signal, pen_mults):
    n=len(signal)
    if n<10: return {pm:([],0.0) for pm in pen_mults}
    med=np.median(signal); mad=np.median(np.abs(signal-med))+1e-9
    s2=(1.4826*mad)**2
    if s2<1e-10: s2=1.0
    algo=rpt.Pelt(model="l2",min_size=3,jump=5).fit(signal.reshape(-1,1))
    return {pm:([c for c in algo.predict(pen=pm*s2*np.log(n)) if c<n], pm*s2*np.log(n))
            for pm in pen_mults}

# ── Evaluate with configurable tolerance ────────────────────────────────────
def evaluate_tol(cps, sz_ranges, n_inter_h, tolerance_s):
    """Same logic as v13 evaluate_cpd but tolerance_s is a parameter."""
    tol = tolerance_s // WIN_SEC
    gap = MERGE_GAP_S  // WIN_SEC
    if not cps: return 0, len(sz_ranges), 0.0, float('nan')
    groups=[]; curr=[cps[0]]
    for c in cps[1:]:
        if c-curr[-1]<=gap: curr.append(c)
        else: groups.append(curr); curr=[c]
    groups.append(curr)
    if not sz_ranges:
        return 0,0,len(groups)/max(n_inter_h,1e-6),float('nan')
    matched=set(); tp,fn,lats=0,0,[]
    for (ss,se) in sz_ranges:
        hits=[(gi,c) for gi,g in enumerate(groups) for c in g if abs(c-ss)<=tol]
        if hits:
            tp+=1; bgi,bc=min(hits,key=lambda x:abs(x[1]-ss))
            matched.add(bgi); lats.append((bc-ss)*WIN_SEC)
        else: fn+=1
    fp=len([gi for gi in range(len(groups)) if gi not in matched])
    return tp,fn,fp/max(n_inter_h,1e-6),(float(np.mean(lats)) if lats else float('nan'))

# ── Main ────────────────────────────────────────────────────────────────────
def main():
    np.random.seed(42)
    print("="*70)
    print("TOLERANCE SENSITIVITY ANALYSIS")
    print(f"Testing tolerances: {TOLERANCES} seconds | pens: {PEN_MULTS}")
    print("="*70)

    all_rows = []

    for subj in TEST_SUBJS:
        ens_i = np.load(str(SCORES_DIR / f"{subj}_ens_inter.npy"))
        ens_c = np.load(str(SCORES_DIR / f"{subj}_ens_ictal.npy"))

        timeline, sz_ranges, n_inter_h = build_timeline(subj, ens_i, ens_c)
        smoothed = pd.Series(timeline).rolling(window=15,min_periods=1,center=True).mean().values
        pelt_res = run_pelt_all(smoothed, PEN_MULTS)

        print(f"\n  {subj}  ({len(sz_ranges)} seizures | {n_inter_h:.1f}h inter)")
        header = f"  {'pen':>5} {'tol':>5} | {'TP':>3} {'FN':>3} {'DR':>6} {'FCP/h':>7} {'lat':>7}"
        print(header); print("  " + "─"*50)

        for pm in PEN_MULTS:
            cps, _ = pelt_res[pm]
            for tol_s in TOLERANCES:
                tp,fn,fcp_h,lat = evaluate_tol(cps, sz_ranges, n_inter_h, tol_s)
                dr = tp/max(tp+fn,1)
                ls = f"{lat:.1f}" if not np.isnan(lat) else "—"
                print(f"  {pm:>5.1f} {tol_s:>4}s | {tp:>3} {fn:>3} {dr:>5.1%} {fcp_h:>7.1f} {ls:>7}")
                all_rows.append({'subject':subj,'pen':pm,'tolerance_s':tol_s,
                                 'tp':tp,'fn':fn,'n_sz':len(sz_ranges),
                                 'dr':round(dr,4),'fcp_h':round(fcp_h,2),
                                 'lat_s':round(lat,1) if not np.isnan(lat) else None,
                                 'n_inter_h':round(n_inter_h,2)})

    # ── Macro summary ────────────────────────────────────────────────────────
    df = pd.DataFrame(all_rows)
    out = RESULTS_DIR / "cpd_tolerance_sweep.csv"
    df.to_csv(str(out), index=False)

    print(f"\n{'='*70}")
    print("MACRO SUMMARY (TP/76 and DR) by pen × tolerance")
    print(f"  {'pen':>5} | {'±10s':>12} {'±20s':>12} {'±30s':>12}")
    print("  " + "─"*45)
    for pm in PEN_MULTS:
        row_parts = []
        for tol_s in TOLERANCES:
            sub = df[(df.pen==pm)&(df.tolerance_s==tol_s)]
            tp_sum = sub.tp.sum()
            dr = tp_sum/76
            row_parts.append(f"{tp_sum:>2}/76={dr:>5.1%}")
        print(f"  {pm:>5.1f} | {'   '.join(row_parts)}")

    print(f"\nCSV saved: {out}")

if __name__ == "__main__":
    main()