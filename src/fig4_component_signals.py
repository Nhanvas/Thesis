"""
fig4_component_signals.py — 3-Signal Decomposition Figure (v2 - fixed)
Shows z_recon, z_temporal, |z_gamma|, z_ensemble around a representative seizure.
Produces one figure per subject in PLOT_CONFIG.
v2 changes:
  - Fixed title to include actual AUROC value
  - For chb14: overlay signed z_gamma (pre-fix) on gamma panel to show
    the inversion that motivated the bidirectional |z_gamma| fix
Usage: python src/fig4_component_signals.py
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import ruptures as rpt
import re
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────
DATA_DIR    = Path("data/processed")
TEMP_DIR    = Path("data/processed/temporal_zscores")
SCORES_DIR  = Path("results/cpd/scores")
OUT_DIR     = Path("results/cpd/figures")
SUMMARY_DIR = Path(r"F:\Study\Thesis\Dataset\CHB-MIT\CHB info\summary")
OUT_DIR.mkdir(parents=True, exist_ok=True)

WIN_SEC = 4; BUFFER_H = 4; MERGE_GAP_S = 32
W_R, W_T, W_G = 0.35, 0.30, 0.35

# Subject-level test AUROC (from window_metrics.csv, bidirectional gamma)
AURC_MAP = {"chb03":0.9518,"chb06":0.4093,"chb13":0.8191,"chb14":0.8624,
            "chb15":0.7915,"chb16":0.8973,"chb17":0.7455,"chb18":0.9253}

# Subjects + seizure index (0 = first) + pen_mult for showing CP
PLOT_CONFIG = [
    ("chb18", 0, 0.5),
    ("chb14", 0, 0.5),
]
N_CONTEXT = 75   # windows on each side of seizure = 5 minutes

COLORS = {'recon':'#1565C0','temp':'#E65100','gamma':'#2E7D32','ens':'#B71C1C'}
LABELS = {
    'recon':'Reconstruction  z_recon',
    'temp' :'Temporal LSTM   z_temporal',
    'gamma':'Gamma AEC       |z_gamma|',
    'ens'  :'Ensemble        z_ensemble',
}

# ── Helper functions ────────────────────────────────────────────────────────
def rznorm(a, b):
    s = np.concatenate([a, b]); m = np.median(s)
    d = np.median(np.abs(s - m)) + 1e-9
    return (a - m) / d, (b - m) / d

def parse_time_hms(t):
    p = t.strip().split(':'); return int(p[0])*3600+int(p[1])*60+int(p[2])

def parse_summary(path):
    text = Path(path).read_text()
    pat  = re.compile(
        r'File Name:\s*(\S+\.edf)\s+File Start Time:\s*(\S+)\s+'
        r'File End Time:\s*(\S+)\s+Number of Seizures in File:\s*(\d+)(.*?)(?=File Name:|$)',
        re.DOTALL)
    edfs = []
    for m in pat.finditer(text):
        fn,t0,t1,nsz,rest = m.groups()
        dur = parse_time_hms(t1) - parse_time_hms(t0)
        if dur <= 0: dur += 86400
        szs = []
        if int(nsz) > 0:
            ons = [int(x) for x in re.findall(r'Seizure.*?Start Time.*?:\s*(\d+)',rest,re.I)]
            ofs = [int(x) for x in re.findall(r'Seizure.*?End Time.*?:\s*(\d+)',  rest,re.I)]
            szs = list(zip(ons,ofs))
        edfs.append({'fname':fn,'duration_s':dur,'seizures':szs})
    edfs.sort(key=lambda x:x['fname']); return edfs

def build_timeline(subj, inter_scores, ictal_scores):
    np.random.seed(42)
    edfs = parse_summary(SUMMARY_DIR / f"{subj}-summary.txt")
    out=[]; is_ic=[]; ip=ic_p=0; tot_i=0.0
    pool = np.random.choice(inter_scores, size=250000, replace=True); bp=0
    for edf in edfs:
        dur=edf['duration_s']; nw=dur//WIN_SEC
        lab=np.zeros(dur,dtype=np.int8); buf=np.zeros(dur,dtype=bool)
        for (on,off) in edf['seizures']:
            on=min(on,dur); off=min(off,dur)
            lab[on:off]=1; buf[off:min(dur,off+BUFFER_H*3600)]=True
        tl=nw*WIN_SEC
        wl=lab[:tl].reshape(nw,WIN_SEC).max(axis=1)
        wb=buf[:tl].reshape(nw,WIN_SEC).any(axis=1)
        for w in range(nw):
            if wl[w]==1:
                out.append(float(ictal_scores[ic_p]) if ic_p<len(ictal_scores) else 0.0)
                if ic_p<len(ictal_scores): ic_p+=1
                is_ic.append(True)
            elif wb[w]:
                out.append(float(pool[bp])); bp=(bp+1)%len(pool)
                is_ic.append(False); tot_i+=WIN_SEC
            else:
                out.append(float(inter_scores[ip]) if ip<len(inter_scores) else float(pool[bp]))
                if ip<len(inter_scores): ip+=1
                else: bp=(bp+1)%len(pool)
                is_ic.append(False); tot_i+=WIN_SEC
    if ip<len(inter_scores):
        out=np.concatenate([out,inter_scores[ip:]]); is_ic+=[False]*(len(inter_scores)-ip)
    tl_arr=np.array(out,dtype=np.float32); ic_arr=np.array(is_ic,dtype=bool)
    sz=[]; in_s=False; ss=0
    for i,ic in enumerate(ic_arr):
        if ic and not in_s: ss=i; in_s=True
        elif not ic and in_s: sz.append((ss,i)); in_s=False
    if in_s: sz.append((ss,len(ic_arr)))
    return tl_arr, sz

def run_pelt(signal, pen):
    n=len(signal)
    if n<10: return []
    med=np.median(signal); mad=np.median(np.abs(signal-med))+1e-9
    s2=(1.4826*mad)**2
    if s2<1e-10: s2=1.0
    algo=rpt.Pelt(model="l2",min_size=3,jump=5).fit(signal.reshape(-1,1))
    return [c for c in algo.predict(pen=pen*s2*np.log(n)) if c<n]

# ── Component score extraction ───────────────────────────────────────────────
def get_components(subj):
    ens_i = np.load(SCORES_DIR / f"{subj}_ens_inter.npy")
    ens_c = np.load(SCORES_DIR / f"{subj}_ens_ictal.npy")
    raw_t_i = np.load(TEMP_DIR / f"temporal_{subj}_zinter.npy")
    raw_t_c = np.load(TEMP_DIR / f"temporal_{subj}_zictal.npy")
    raw_g_i = np.load(DATA_DIR / f"gamma_aec_{subj}_inter.npy")
    raw_g_c = np.load(DATA_DIR / f"gamma_aec_{subj}_ictal.npy")
    z_t_i, z_t_c = rznorm(raw_t_i, raw_t_c)
    z_g_i, z_g_c = rznorm(raw_g_i, raw_g_c)
    ni, nc = len(ens_i), len(ens_c)
    gai = np.abs(z_g_i[:ni]); gac = np.abs(z_g_c[:nc])
    z_r_i = (ens_i - W_T*z_t_i[:ni] - W_G*gai) / W_R
    z_r_c = (ens_c - W_T*z_t_c[:nc] - W_G*gac) / W_R
    return {
        'recon':        (z_r_i, z_r_c),
        'temp':         (z_t_i[:ni], z_t_c[:nc]),
        'gamma':        (gai,   gac),
        'gamma_signed': (z_g_i[:ni], z_g_c[:nc]),
        'ens':          (ens_i, ens_c),
    }

# ── Plot ─────────────────────────────────────────────────────────────────────
def make_figure(subj, k_sz, pen):
    print(f"  [{subj}] seizure {k_sz+1}, pen={pen}")
    np.random.seed(42)
    comp = get_components(subj)
    keys = ['recon','temp','gamma','ens']

    # Build timelines for the 4 main panels
    timelines = {}; sz_ref = None
    for k in keys:
        tl, sz = build_timeline(subj, *comp[k])
        timelines[k] = tl
        if sz_ref is None: sz_ref = sz

    if not sz_ref or k_sz >= len(sz_ref):
        print(f"  Seizure {k_sz+1} not found"); return

    ss, se = sz_ref[k_sz]
    w0 = max(0, ss - N_CONTEXT); w1 = min(len(timelines['ens']), se + N_CONTEXT)
    t  = (np.arange(w0, w1) - ss) * WIN_SEC  # seconds relative to onset

    # PELT change points in segment
    smooth = pd.Series(timelines['ens']).rolling(15,min_periods=1,center=True).mean().values
    cps = run_pelt(smooth, pen)
    seg_cps = [(c-ss)*WIN_SEC for c in cps if w0 <= c < w1]

    # For chb14: also build signed gamma timeline (pre-fix) for overlay
    signed_seg = None
    if subj == "chb14":
        tl_signed, _ = build_timeline(subj, *comp['gamma_signed'])
        signed_seg = tl_signed[w0:w1]

    # Figure
    fig, axes = plt.subplots(4,1,figsize=(13,9),sharex=True)
    fig.suptitle(f'{subj} — Seizure {k_sz+1}  (Subject-level test AUROC = {AURC_MAP[subj]:.3f})',
                 fontsize=12, fontweight='bold', y=0.98)

    sz_dur_s = (se - ss) * WIN_SEC
    for ax, key in zip(axes, keys):
        seg  = timelines[key][w0:w1]
        smo  = pd.Series(seg).rolling(5,min_periods=1,center=True).mean().values
        col  = COLORS[key]
        ax.fill_between(t, seg, alpha=0.2, color=col)
        ax.plot(t, smo,  color=col, lw=1.8, label=LABELS[key])

        # chb14 gamma panel: overlay signed (pre-fix) z_gamma
        if key == 'gamma' and signed_seg is not None:
            smo_signed = pd.Series(signed_seg).rolling(5,min_periods=1,center=True).mean().values
            ax.plot(t, smo_signed, color='#9E9E9E', lw=1.4, ls='--', alpha=0.9,
                    label='z_gamma (signed, pre-fix)')
            ax.axhline(0, color='gray', lw=0.6, ls=':')

        ax.axvspan(0, sz_dur_s, color='#EF5350', alpha=0.15, label='Seizure period')
        ax.axvline(0,            color='#C62828', lw=2.0, ls='--', label='Seizure onset')
        for i, cp_t in enumerate(seg_cps):
            ax.axvline(cp_t, color='#1A237E', lw=2.0, ls=':', alpha=0.9,
                       label=f'PELT CP (pen={pen})' if i==0 else None)
        ax.axhline(0, color='gray', lw=0.6, ls=':')
        ax.set_ylabel('z-score', fontsize=9)
        ax.legend(loc='upper left', fontsize=8, ncol=3)
        ax.grid(True, alpha=0.2)
        ax.set_ylim(np.percentile(seg,1)-0.5, np.percentile(seg,99)+0.5)

    axes[-1].set_xlabel('Time relative to seizure onset (seconds)', fontsize=10)
    plt.tight_layout()
    out = OUT_DIR / f"fig4_{subj}_sz{k_sz+1}.png"
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.close(); print(f"  → {out}")

def main():
    print("Generating Figure 4: Component signal decomposition (v2)")
    for subj, k_sz, pen in PLOT_CONFIG:
        make_figure(subj, k_sz, pen)

if __name__ == "__main__":
    main()