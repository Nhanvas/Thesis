"""
fig5_eight_subjects.py — 8-Subject Detection Overview Figure (v5)
4x2 grid: ensemble z-score timeline for each subject, with seizure markers
and PELT change points at pen=0.5.

Changes vs v4:
  - REMOVED FCP/h from panel titles (not a standardised published metric
    at this granularity; removed per researcher decision).
  - FIXED duplicate CP plot: a raw CP can now only be claimed by ONE seizure
    (first-come-first-served by seizure order), preventing the same dashed
    line from being drawn twice when two seizures fall within the tolerance
    window of the same CP.

Usage: python src/fig5_eight_subjects.py
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import ruptures as rpt
import re
from pathlib import Path
from sklearn.metrics import roc_auc_score

# ── Config ──────────────────────────────────────────────────────────────────
SCORES_DIR   = Path("results/cpd/scores")
OUT_DIR      = Path("results/cpd/figures")
SUMMARY_DIR  = Path(r"F:\Study\Thesis\Dataset\CHB-MIT\CHB info\summary")
CSV_RESULTS  = Path("results/cpd/cpd_results_v12_combined.csv")
OUT_DIR.mkdir(parents=True, exist_ok=True)

WIN_SEC      = 4    # Each window is 4 seconds
BUFFER_H     = 4    # 4-hour post-ictal exclusion buffer
MERGE_GAP_S  = 32   # seconds to merge close CPs into single events (kept for
                    # internal use but not displayed)
PEN          = 0.5  # operating point to display (must exist in CSV)
AUROC_TOL    = 0.005  # tolerance for computed vs CSV AUROC check

TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]

# ── Load canonical AUROC values from locked CSV (NOT hardcoded) ─────────────
if not CSV_RESULTS.exists():
    raise FileNotFoundError(
        f"Cannot find {CSV_RESULTS}. Run cpd_pipeline_v13.py first.")

_df = pd.read_csv(CSV_RESULTS)
AURC_FROM_CSV = _df.groupby("subject")["auroc"].first().to_dict()

missing = [s for s in TEST_SUBJS if s not in AURC_FROM_CSV]
if missing:
    raise ValueError(f"Subjects missing from CSV: {missing}. "
                     f"Re-run cpd_pipeline_v13.py to regenerate.")

print("AUROC values loaded from CSV:")
for s in TEST_SUBJS:
    print(f"  {s}: {AURC_FROM_CSV[s]:.4f}")


# ── Helpers ──────────────────────────────────────────────────────────────────
def parse_time_hms(t):
    p = t.strip().split(':')
    return int(p[0]) * 3600 + int(p[1]) * 60 + int(p[2])


def parse_summary(path):
    text = Path(path).read_text()
    pat = re.compile(
        r'File Name:\s*(\S+\.edf)\s+File Start Time:\s*(\S+)\s+'
        r'File End Time:\s*(\S+)\s+Number of Seizures in File:\s*(\d+)(.*?)(?=File Name:|$)',
        re.DOTALL)
    edfs = []
    for m in pat.finditer(text):
        fn, t0, t1, nsz, rest = m.groups()
        dur = parse_time_hms(t1) - parse_time_hms(t0)
        if dur <= 0:
            dur += 86400
        szs = []
        if int(nsz) > 0:
            ons = [int(x) for x in re.findall(r'Seizure.*?Start Time.*?:\s*(\d+)', rest, re.I)]
            ofs = [int(x) for x in re.findall(r'Seizure.*?End Time.*?:\s*(\d+)',   rest, re.I)]
            szs = list(zip(ons, ofs))
        edfs.append({'fname': fn, 'duration_s': dur, 'seizures': szs})
    edfs.sort(key=lambda x: x['fname'])
    return edfs


def build_timeline(subj, inter_scores, ictal_scores):
    """Chronological timeline with Bootstrap Resampling for buffer windows.
    Identical logic to cpd_pipeline_v13.py to guarantee reproducibility."""
    np.random.seed(42)
    edfs = parse_summary(SUMMARY_DIR / f"{subj}-summary.txt")
    out = []; is_ic = []; ip = ic_p = 0; tot_i = 0.0
    pool = np.random.choice(inter_scores, size=250000, replace=True); bp = 0

    for edf in edfs:
        dur = edf['duration_s']; nw = dur // WIN_SEC
        lab = np.zeros(dur, dtype=np.int8)
        buf = np.zeros(dur, dtype=bool)
        for (on, off) in edf['seizures']:
            on = min(on, dur); off = min(off, dur)
            lab[on:off] = 1
            buf[off:min(dur, off + BUFFER_H * 3600)] = True
        tl = nw * WIN_SEC
        wl = lab[:tl].reshape(nw, WIN_SEC).max(axis=1)
        wb = buf[:tl].reshape(nw, WIN_SEC).any(axis=1)
        for w in range(nw):
            if wl[w] == 1:
                out.append(float(ictal_scores[ic_p]) if ic_p < len(ictal_scores) else 0.0)
                if ic_p < len(ictal_scores):
                    ic_p += 1
                is_ic.append(True)
            elif wb[w]:
                out.append(float(pool[bp])); bp = (bp + 1) % len(pool)
                is_ic.append(False); tot_i += WIN_SEC
            else:
                out.append(float(inter_scores[ip]) if ip < len(inter_scores)
                           else float(pool[bp]))
                if ip < len(inter_scores):
                    ip += 1
                else:
                    bp = (bp + 1) % len(pool)
                is_ic.append(False); tot_i += WIN_SEC

    if ip < len(inter_scores):
        out = np.concatenate([out, inter_scores[ip:]])
        is_ic += [False] * (len(inter_scores) - ip)

    tl_arr = np.array(out, dtype=np.float32)
    ic_arr  = np.array(is_ic, dtype=bool)

    sz = []; in_s = False; ss = 0
    for i, v in enumerate(ic_arr):
        if v and not in_s:
            ss = i; in_s = True
        elif not v and in_s:
            sz.append((ss, i)); in_s = False
    if in_s:
        sz.append((ss, len(ic_arr)))

    return tl_arr, sz, tot_i / 3600.0


def run_pelt_single(signal, pen):
    n = len(signal)
    if n < 10:
        return []
    med = np.median(signal)
    mad = np.median(np.abs(signal - med)) + 1e-9
    s2  = (1.4826 * mad) ** 2
    if s2 < 1e-10:
        s2 = 1.0
    algo = rpt.Pelt(model="l2", min_size=3, jump=5).fit(signal.reshape(-1, 1))
    return [c for c in algo.predict(pen=pen * s2 * np.log(n)) if c < n]


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    np.random.seed(42)
    print(f"\nGenerating Figure 5 — 8-subject overview (pen={PEN})\n")

    fig, axes = plt.subplots(4, 2, figsize=(16, 14))
    axes = axes.flatten()

    for idx, subj in enumerate(TEST_SUBJS):
        ax = axes[idx]
        print(f"  [{subj}]", end=' ', flush=True)

        # Load cached ensemble scores
        ens_i_path = SCORES_DIR / f"{subj}_ens_inter.npy"
        ens_c_path = SCORES_DIR / f"{subj}_ens_ictal.npy"
        if not ens_i_path.exists() or not ens_c_path.exists():
            raise FileNotFoundError(
                f"Cache missing for {subj}. Run cpd_pipeline_v13.py first.\n"
                f"  Expected: {ens_i_path}")

        ens_i = np.load(ens_i_path)
        ens_c = np.load(ens_c_path)

        # ── Verify AUROC matches locked CSV ───────────────────────────────
        y_true  = np.concatenate([np.zeros(len(ens_i)), np.ones(len(ens_c))])
        y_score = np.concatenate([ens_i, ens_c])
        auroc_computed = roc_auc_score(y_true, y_score)
        auroc_csv      = AURC_FROM_CSV[subj]

        if abs(auroc_computed - auroc_csv) > AUROC_TOL:
            raise RuntimeError(
                f"\n{'='*60}\n"
                f"STALE CACHE DETECTED for {subj}!\n"
                f"  Computed AUROC : {auroc_computed:.4f}\n"
                f"  CSV AUROC      : {auroc_csv:.4f}\n"
                f"  Difference     : {abs(auroc_computed - auroc_csv):.4f} > tolerance {AUROC_TOL}\n\n"
                f"Fix: delete results/cpd/scores/*.npy and re-run cpd_pipeline_v13.py\n"
                f"{'='*60}")

        # Use the locked CSV value in the title (canonical number)
        auroc_display = auroc_csv

        # ── Build timeline and run PELT ────────────────────────────────────
        tl, sz_ranges, n_inter_h = build_timeline(subj, ens_i, ens_c)
        smooth = pd.Series(tl).rolling(15, min_periods=1, center=True).mean().values
        cps    = sorted(run_pelt_single(smooth, PEN))

        # Time axis in hours
        t_h = np.arange(len(tl)) * WIN_SEC / 3600.0

        # Downsample for plotting
        step = max(1, len(tl) // 3000)
        ax.plot(t_h[::step], smooth[::step], color='#37474F', lw=0.7, alpha=0.7)

        # Shade seizure periods
        for i, (ss, se) in enumerate(sz_ranges):
            ax.axvspan(t_h[ss], t_h[min(se, len(t_h) - 1)],
                       color='#EF5350', alpha=0.35,
                       label='Seizure period' if i == 0 else None)

        tol = 30 // WIN_SEC  # ±30s tolerance in windows

        # ── Detection rate ─────────────────────────────────────────────────
        # Each CP can only be claimed by ONE seizure (first-come-first-served).
        # This prevents the same CP from satisfying two nearby seizures and
        # being plotted twice as separate dashed lines.
        used_cps    = set()
        matched     = set()
        tp_plot_cps = []

        for k, (ss, se) in enumerate(sz_ranges):
            candidates = [cp for cp in cps
                          if abs(cp - ss) <= tol and cp not in used_cps]
            if candidates:
                best = min(candidates, key=lambda c: abs(c - ss))
                matched.add(k)
                used_cps.add(best)
                tp_plot_cps.append(best)

        dr = len(matched) / max(len(sz_ranges), 1)

        # Plot exactly ONE dashed line per detected seizure
        for cp in tp_plot_cps:
            ax.axvline(t_h[cp], color='#1565C0', lw=1.8, ls=':', alpha=0.9, zorder=4)

        # chb17: multi-session baseline drift reaches z~150 → symlog
        if subj == "chb17":
            ax.set_yscale('symlog', linthresh=2)
            ax.set_ylim(-1, 200)
            ax.text(0.02, 0.95,
                    'symlog y-axis — multi-session drift reaches z≈150 (see Ch.4 Discussion)',
                    transform=ax.transAxes, ha='left', va='top', fontsize=7.5,
                    style='italic', color='#B71C1C',
                    bbox=dict(facecolor='white', alpha=0.85, edgecolor='none', pad=2))

        # Title: AUROC and DR only (FCP/h removed)
        ax.set_title(
            f'{subj}  |  AUROC={auroc_display:.3f}  |  '
            f'DR={dr:.0%} ({len(matched)}/{len(sz_ranges)})',
            fontsize=10, fontweight='bold')
        ax.set_xlabel('Recording time (hours)', fontsize=8)
        ax.set_ylabel('z_ensemble', fontsize=8)
        ax.tick_params(labelsize=7)
        ax.grid(True, alpha=0.2)
        ax.axhline(0, color='gray', lw=0.5, ls=':')

        # Legend — only once, top-left panel
        if idx == 0:
            from matplotlib.patches import Patch
            from matplotlib.lines import Line2D
            handles = [
                Patch(facecolor='#EF5350', alpha=0.4, label='Seizure period'),
                Line2D([0], [0], color='#1565C0', lw=1.8, ls=':',
                       label='PELT change point (matched, ±30s)'),
            ]
            ax.legend(handles=handles, fontsize=7.5, loc='upper right')

        print(f"AUROC={auroc_display:.4f}  DR={dr:.0%} ({len(matched)}/{len(sz_ranges)})")

    fig.suptitle(f'8-Subject Ensemble Anomaly Score Timeline  (pen_mult={PEN})',
                 fontsize=14, fontweight='bold', y=0.998)
    plt.tight_layout()

    out = OUT_DIR / "fig5_eight_subjects_overview.png"
    plt.savefig(out, dpi=250, bbox_inches='tight')
    plt.close()
    print(f"\n→ Saved: {out}")


if __name__ == "__main__":
    main()