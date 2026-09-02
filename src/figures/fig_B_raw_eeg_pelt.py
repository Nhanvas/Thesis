#!/usr/bin/env python3
"""
fig_B_raw_eeg_pelt.py
Preprocessed EEG with PELT Change Point — All 8 Test Subjects

For each subject: stacked 18-channel preprocessed EEG (z-scored, bandpass-filtered)
around the first detected True-Positive seizure.
  - Red dashed line : clinical seizure onset (annotation, x = 0 s)
  - Blue dotted line: PELT change point (pen = 0.3)
Allows visual validation that the algorithm locates the correct moment.

Layout: 4x2 grid.
Usage: python src/fig_B_raw_eeg_pelt.py
"""

import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import ruptures as rpt

# ── Config ───────────────────────────────────────────────────────────────────
DATA_DIR    = Path("data/processed")
SCORES_DIR  = Path("results/cpd/scores")
OUT_DIR     = Path("results/cpd/figures")
SUMMARY_DIR = Path(r"F:\Study\Thesis\Dataset\CHB-MIT\CHB info\summary")
OUT_DIR.mkdir(parents=True, exist_ok=True)

WIN_SEC  = 4
FS       = 256
BUFFER_H = 4
PEN      = 0.3
TOL_S    = 30

N_BEFORE = 15   # interictal windows before onset (= 60 s)
N_AFTER  = 20   # ictal windows after onset (= 80 s)

TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]

CH_NAMES = [
    "FP1-F7", "F7-T7",  "T7-P7",  "P7-O1",
    "FP1-F3", "F3-C3",  "C3-P3",  "P3-O1",
    "FP2-F4", "F4-C4",  "C4-P4",  "P4-O2",
    "FP2-F8", "F8-T8",  "T8-P8",  "P8-O2",
    "FZ-CZ",  "CZ-PZ",
]
N_CH = len(CH_NAMES)

AUROC_MAP = {
    "chb03": 0.9579, "chb06": 0.4401, "chb13": 0.8163, "chb14": 0.7301,
    "chb15": 0.8192, "chb16": 0.9095, "chb17": 0.7729, "chb18": 0.9194,
}

# ── Helpers (duplicated for self-contained script) ───────────────────────────
def parse_time_hms(t):
    p = t.strip().split(":")
    return int(p[0]) * 3600 + int(p[1]) * 60 + int(p[2])


def parse_summary(path):
    text = Path(path).read_text()
    pat = re.compile(
        r"File Name:\s*(\S+\.edf)\s+File Start Time:\s*(\S+)\s+"
        r"File End Time:\s*(\S+)\s+Number of Seizures in File:\s*(\d+)(.*?)(?=File Name:|$)",
        re.DOTALL,
    )
    edfs = []
    for m in pat.finditer(text):
        fn, t0, t1, nsz, rest = m.groups()
        dur = parse_time_hms(t1) - parse_time_hms(t0)
        if dur <= 0: dur += 86400
        szs = []
        if int(nsz) > 0:
            ons = [int(x) for x in re.findall(r"Seizure.*?Start Time.*?:\s*(\d+)", rest, re.I)]
            ofs = [int(x) for x in re.findall(r"Seizure.*?End Time.*?:\s*(\d+)",   rest, re.I)]
            szs = list(zip(ons, ofs))
        edfs.append({"fname": fn, "duration_s": dur, "seizures": szs})
    edfs.sort(key=lambda x: x["fname"])
    return edfs


def build_timeline_indexed(subj, inter_scores, ictal_scores):
    np.random.seed(42)
    edfs = parse_summary(SUMMARY_DIR / f"{subj}-summary.txt")
    tl, is_ic, idx_map = [], [], []
    ip = icp = 0; total_is = 0.0
    pool = np.random.choice(inter_scores, size=250_000, replace=True); bp = 0

    for edf in edfs:
        dur = edf["duration_s"]; nw = dur // WIN_SEC
        lab = np.zeros(dur, dtype=np.int8); buf = np.zeros(dur, dtype=bool)
        for on, off in edf["seizures"]:
            on = min(on, dur); off = min(off, dur)
            lab[on:off] = 1; buf[off : min(dur, off + BUFFER_H * 3600)] = True
        tlen = nw * WIN_SEC
        wl = lab[:tlen].reshape(nw, WIN_SEC).max(axis=1)
        wb = buf[:tlen].reshape(nw, WIN_SEC).any(axis=1)
        for w in range(nw):
            if wl[w] == 1:
                tl.append(float(ictal_scores[icp]) if icp < len(ictal_scores) else 0.0)
                idx_map.append(("ictal", icp if icp < len(ictal_scores) else -1))
                if icp < len(ictal_scores): icp += 1
                is_ic.append(True)
            elif wb[w]:
                tl.append(float(pool[bp])); idx_map.append(("buffer", -1))
                bp = (bp + 1) % len(pool); is_ic.append(False); total_is += WIN_SEC
            else:
                if ip < len(inter_scores):
                    tl.append(float(inter_scores[ip])); idx_map.append(("inter", ip)); ip += 1
                else:
                    tl.append(float(pool[bp])); idx_map.append(("buffer", -1))
                    bp = (bp + 1) % len(pool)
                is_ic.append(False); total_is += WIN_SEC

    if ip < len(inter_scores):
        for i in range(ip, len(inter_scores)):
            tl.append(float(inter_scores[i])); idx_map.append(("inter", i))
            is_ic.append(False); total_is += WIN_SEC

    tl_arr = np.array(tl, dtype=np.float32)
    ic_arr = np.array(is_ic, dtype=bool)
    sz_ranges = []; in_s = False; ss = 0
    for i, ic in enumerate(ic_arr):
        if ic and not in_s:  ss = i; in_s = True
        elif not ic and in_s: sz_ranges.append((ss, i)); in_s = False
    if in_s: sz_ranges.append((ss, len(ic_arr)))
    return tl_arr, sz_ranges, idx_map


def run_pelt(sig, pen):
    n = len(sig)
    if n < 10: return []
    med = np.median(sig); mad = np.median(np.abs(sig - med)) + 1e-9
    s2 = (1.4826 * mad) ** 2
    if s2 < 1e-10: s2 = 1.0
    algo = rpt.Pelt(model="l2", min_size=3, jump=5).fit(sig.reshape(-1, 1))
    return [c for c in algo.predict(pen=pen * s2 * np.log(n)) if c < n]


# ── EEG context loader ───────────────────────────────────────────────────────
def get_eeg_context(subj, sz_start_idx, idx_map, first_tp_cp):
    """
    Load N_BEFORE interictal + N_AFTER ictal EEG windows around a seizure.

    Returns:
        eeg        : np.array [18, total_samples]  (float32)
        onset_samp : sample index of clinical onset
        cp_samp    : sample index of PELT CP  (-1 if none)
        n_inter    : actual interictal windows loaded
    """
    # Collect inter window indices before sz_start (chronological order)
    inter_ptrs = []
    j = sz_start_idx - 1
    while len(inter_ptrs) < N_BEFORE and j >= 0:
        src, ptr = idx_map[j]
        if src == "inter" and ptr >= 0:
            inter_ptrs.append(ptr)
        j -= 1
    inter_ptrs.reverse()

    # Collect ictal window indices from sz_start
    ictal_ptrs = []
    j = sz_start_idx
    while len(ictal_ptrs) < N_AFTER and j < len(idx_map):
        src, ptr = idx_map[j]
        if src == "ictal" and ptr >= 0:
            ictal_ptrs.append(ptr)
        j += 1

    inter_data = np.load(DATA_DIR / f"{subj}_interictal.npy", mmap_mode="r")
    ictal_data  = np.load(DATA_DIR / f"{subj}_ictal.npy",      mmap_mode="r")

    parts = []
    if inter_ptrs:
        parts.append(inter_data[inter_ptrs].transpose(1, 0, 2).reshape(N_CH, -1))
    if ictal_ptrs:
        parts.append(ictal_data[ictal_ptrs].transpose(1, 0, 2).reshape(N_CH, -1))

    if not parts:
        return None, 0, -1, 0

    eeg = np.concatenate(parts, axis=1).astype(np.float32)   # [18, total_samples]
    onset_samp = len(inter_ptrs) * (WIN_SEC * FS)

    if first_tp_cp >= 0:
        cp_win_offset = first_tp_cp - sz_start_idx   # negative = pre-ictal
        cp_samp = onset_samp + cp_win_offset * (WIN_SEC * FS)
    else:
        cp_samp = -1

    return eeg, onset_samp, cp_samp, len(inter_ptrs)


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    np.random.seed(42)
    print("Generating Figure B: Preprocessed EEG with PELT change point")

    fig, axes = plt.subplots(4, 2, figsize=(16, 18))
    axes = axes.flatten()
    tol_win = TOL_S // WIN_SEC
    OFFSET  = 5.0   # z-score units between channel traces

    for idx, subj in enumerate(TEST_SUBJS):
        ax = axes[idx]
        print(f"  {subj} ...", end="", flush=True)

        ens_i = np.load(SCORES_DIR / f"{subj}_ens_inter.npy")
        ens_c = np.load(SCORES_DIR / f"{subj}_ens_ictal.npy")

        tl_ens, sz_ranges, idx_map = build_timeline_indexed(subj, ens_i, ens_c)

        # PELT on 1-min smoothed ensemble
        ens_sm = pd.Series(tl_ens).rolling(15, min_periods=1, center=True).mean().values
        cps    = sorted(run_pelt(ens_sm, PEN))

        # Find first TP seizure and its matched CP
        first_tp_sz_start = -1
        first_tp_cp       = -1
        for ss, _ in sz_ranges:
            hits = [c for c in cps if abs(c - ss) <= tol_win]
            if hits:
                first_tp_sz_start = ss
                first_tp_cp = min(hits, key=lambda c: abs(c - ss))
                break

        # Fall back to first seizure if no TP found
        if first_tp_sz_start < 0 and sz_ranges:
            first_tp_sz_start = sz_ranges[0][0]

        if first_tp_sz_start < 0:
            print(" no seizure — skip"); continue

        eeg, onset_samp, cp_samp, n_inter_loaded = get_eeg_context(
            subj, first_tp_sz_start, idx_map, first_tp_cp
        )
        if eeg is None:
            print(" EEG load failed — skip"); continue

        total_samples = eeg.shape[1]
        t_sec = (np.arange(total_samples) - onset_samp) / FS   # relative to onset

        # Plot each channel with vertical offset
        # Channel 0 (FP1-F7) at top, channel 17 (CZ-PZ) at bottom
        for ch in range(N_CH):
            y_off = (N_CH - 1 - ch) * OFFSET
            # Downsample by 2 for display speed (still 128 Hz effective)
            ax.plot(t_sec[::2], eeg[ch, ::2] + y_off,
                    color="#37474F", lw=0.45, alpha=0.85)

        # Clinical onset (annotation)
        ax.axvline(0, color="#C62828", lw=2.0, ls="--", zorder=5,
                   label="Clinical onset (annotation)")

        # PELT CP
        if cp_samp >= 0:
            cp_t = (cp_samp - onset_samp) / FS
            lat  = cp_t   # latency in seconds (negative = pre-ictal)
            ax.axvline(cp_t, color="#1565C0", lw=2.0, ls=":", zorder=5,
                       label=f"PELT CP  (lat={lat:+.0f} s)")
        else:
            ax.text(0.5, 0.5, "No TP at pen=0.3", transform=ax.transAxes,
                    ha="center", va="center", fontsize=9, color="gray")

        # Shade interictal and ictal regions
        t_onset = 0.0
        ax.axvspan(t_sec[0], t_onset, color="#E3F2FD", alpha=0.30, zorder=0)
        ax.axvspan(t_onset, t_sec[-1], color="#FFEBEE", alpha=0.30, zorder=0)

        # Y-ticks: channel names
        ytick_pos = [(N_CH - 1 - ch) * OFFSET for ch in range(N_CH)]
        ax.set_yticks(ytick_pos)
        ax.set_yticklabels(CH_NAMES, fontsize=6.5)
        ax.set_ylim(-OFFSET, N_CH * OFFSET)

        ax.set_xlim(t_sec[0], t_sec[-1])
        ax.set_xlabel("Time relative to clinical onset (s)", fontsize=8)
        ax.set_title(
            f"{subj}  |  AUROC = {AUROC_MAP[subj]:.4f}  |  "
            f"Preprocessed EEG (z-scored, bandpass 0.5–60 Hz)",
            fontsize=9.5, fontweight="bold",
        )
        ax.grid(True, axis="x", alpha=0.20, lw=0.5)
        ax.tick_params(axis="x", labelsize=7.5)

        if idx == 0:
            handles = [
                mpatches.Patch(color="#E3F2FD", alpha=0.6, label="Interictal"),
                mpatches.Patch(color="#FFEBEE", alpha=0.6, label="Ictal"),
                Line2D([0], [0], color="#C62828", lw=2.0, ls="--",
                       label="Clinical onset"),
                Line2D([0], [0], color="#1565C0", lw=2.0, ls=":",
                       label="PELT CP (pen=0.3)"),
            ]
            ax.legend(handles=handles, fontsize=7.5, loc="upper right",
                      framealpha=0.9)

        print(" done")

    fig.suptitle(
        "Preprocessed 18-Channel EEG with PELT Change Point — All 8 Test Subjects\n"
        "Blue background = interictal  ·  Red background = ictal  ·  "
        "Dashed red = clinical onset  ·  Dotted blue = PELT CP",
        fontsize=11, fontweight="bold", y=0.999,
    )
    plt.tight_layout(rect=[0, 0, 1, 0.975])
    out = OUT_DIR / "figB_raw_eeg_pelt_8subjects.png"
    plt.savefig(out, dpi=220, bbox_inches="tight")
    plt.close()
    print(f"\n→ Saved: {out}")


if __name__ == "__main__":
    main()