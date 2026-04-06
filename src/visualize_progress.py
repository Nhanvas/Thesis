"""
visualize_progress.py
=====================
Create 3 figures for supervisor report.

Output (saved in results/figures/):
  fig1_preprocessing_summary.png  — ictal/interictal windows per subject
  fig2_raw_vs_filtered.png        — EEG signal before/after filter
  fig3_adjacency_heatmap.png      — interictal vs ictal functional connectivity
"""

import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

PROCESSED_DIR = Path("F:/Study/Thesis/Code/data/processed")
RAW_DIR       = Path("F:/Study/Thesis/Dataset/CHB-MIT")
FIG_DIR       = Path("F:/Study/Thesis/Code/results/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)


# ── Figure 1: Preprocessing summary ──────────────────────────────────────────

def plot_preprocessing_summary():
    import json

    subjects, n_inter, n_ictal, n_rejected = [], [], [], []

    for i in range(1, 24):
        subj = f"chb{i:02d}"
        stats_path = PROCESSED_DIR / f"{subj}_stats.json"
        if not stats_path.exists():
            continue
        with open(stats_path) as f:
            s = json.load(f)
        subjects.append(subj)
        n_inter.append(s["n_interictal"])
        n_ictal.append(s["n_ictal"])
        n_rejected.append(s["n_rejected"])

    x = np.arange(len(subjects))
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))

    # Top: interictal vs ictal windows
    bar_w = 0.35
    b1 = ax1.bar(x - bar_w/2, n_inter, bar_w,
                 label="Interictal", color="#2196F3", alpha=0.85)
    b2 = ax1.bar(x + bar_w/2, n_ictal, bar_w,
                 label="Ictal", color="#F44336", alpha=0.85)

    ax1.set_xticks(x)
    ax1.set_xticklabels(subjects, rotation=45, ha="right", fontsize=9)
    ax1.set_ylabel("Number of 4s windows")
    ax1.set_title("CHB-MIT Preprocessing Summary — Windows per Subject",
                  fontweight="bold")
    ax1.legend()
    ax1.set_yscale("log")
    ax1.grid(axis="y", alpha=0.3)

    # Bottom: artifact rejected
    ax2.bar(x, n_rejected, color="#FF9800", alpha=0.85,
            label="Artifact rejected (interictal)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(subjects, rotation=45, ha="right", fontsize=9)
    ax2.set_ylabel("Windows rejected")
    ax2.set_title("Artifact Rejection per Subject (±500 µV threshold)",
                  fontweight="bold")
    ax2.legend()
    ax2.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    out = FIG_DIR / "fig1_preprocessing_summary.png"
    plt.savefig(str(out), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")


# ── Figure 2: Raw vs filtered EEG ────────────────────────────────────────────

def plot_raw_vs_filtered():
    import mne
    import warnings
    import re
    from scipy.signal import butter, sosfiltfilt

    warnings.filterwarnings("ignore")
    mne.set_log_level("ERROR")

    FS = 256
    SOS = butter(4, [0.5, 40.0], btype="bandpass", fs=FS, output="sos")

    # chb01_18.edf: seizure at 1720-1810s
    # Window at ~1700s = pre-ictal, high amplitude, DC drift visible
    edf_path = RAW_DIR / "chb01" / "chb01_18.edf"
    raw = mne.io.read_raw_edf(str(edf_path), preload=False, verbose=False)
    raw.rename_channels({ch: ch.upper().strip() for ch in raw.ch_names})

    rename_map, seen = {}, set()
    for ch in raw.ch_names:
        m = re.match(r"^(.*)-(\d+)$", ch)
        if m:
            base = m.group(1)
            if base not in seen:
                rename_map[ch] = base
                seen.add(base)
    if rename_map:
        raw.rename_channels(rename_map)

    raw.pick(["FP1-F7", "F7-T7", "T7-P7", "FZ-CZ"])

    # Scan windows to find one with high peak-to-peak (noisy but < 500µV)
    best_start = 0
    best_ptp   = 0
    for trial_start in range(0, min(int(raw.n_times) - 1024, 1800*256), 1024):
        seg = raw.get_data(start=trial_start,
                           stop=trial_start + 1024) * 1e6
        ptp = float(np.ptp(seg))
        if 150 < ptp < 800 and ptp > best_ptp:
            best_ptp   = ptp
            best_start = trial_start

    segment  = raw.get_data(start=best_start,
                             stop=best_start + 1024) * 1e6
    filtered = sosfiltfilt(SOS, segment, axis=1)
    time     = np.arange(1024) / FS

    channels = ["FP1-F7", "F7-T7", "T7-P7", "FZ-CZ"]
    fig, axes = plt.subplots(4, 2, figsize=(14, 9), sharex=True)

    for idx, ch in enumerate(channels):
        raw_sig  = segment[idx]
        filt_sig = filtered[idx]

        # Raw
        axes[idx, 0].plot(time, raw_sig, color="#555", linewidth=0.8)
        axes[idx, 0].set_ylabel(ch, fontsize=9)
        lim = max(abs(raw_sig).max() * 1.2, 100)
        axes[idx, 0].set_ylim(-lim, lim)
        axes[idx, 0].axhline(500,  color="red", linestyle="--",
                             linewidth=0.7, alpha=0.6, label="±500µV")
        axes[idx, 0].axhline(-500, color="red", linestyle="--",
                             linewidth=0.7, alpha=0.6)
        axes[idx, 0].grid(alpha=0.2)

        # Filtered
        axes[idx, 1].plot(time, filt_sig, color="#1976D2", linewidth=0.8)
        axes[idx, 1].set_ylim(-lim, lim)
        axes[idx, 1].grid(alpha=0.2)

        # Annotate DC removal on first channel if visible
        dc_raw  = float(np.mean(raw_sig))
        dc_filt = float(np.mean(filt_sig))
        if abs(dc_raw) > 20:
            axes[idx, 0].axhline(dc_raw, color="orange", linestyle=":",
                                 linewidth=1.0, alpha=0.8)
            axes[idx, 1].axhline(dc_filt, color="orange", linestyle=":",
                                 linewidth=1.0, alpha=0.8)

    axes[0, 0].set_title("Raw EEG (µV) — DC drift + broadband noise",
                         fontweight="bold")
    axes[0, 1].set_title("After bandpass filter 0.5–40 Hz — DC removed",
                         fontweight="bold")
    for ax in axes[-1]:
        ax.set_xlabel("Time (s)")

    window_time = best_start // FS
    plt.suptitle(
        f"EEG Preprocessing: Raw vs Filtered\n"
        f"chb01_18.edf — window at t={window_time}s "
        f"(near seizure onset at 1720s)",
        fontweight="bold")
    plt.tight_layout()
    out = FIG_DIR / "fig2_raw_vs_filtered.png"
    plt.savefig(str(out), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}  [window at t={window_time}s, peak-to-peak={best_ptp:.0f}µV]")


# ── Figure 3: Adjacency heatmap — interictal vs ictal ────────────────────────

def plot_adjacency_heatmap():
    from graph_construction import build_adjacency

    CHANNELS = [
        "FP1-F7", "F7-T7", "T7-P7", "P7-O1",
        "FP1-F3", "F3-C3", "C3-P3", "P3-O1",
        "FP2-F4", "F4-C4", "C4-P4", "P4-O2",
        "FP2-F8", "F8-T8", "T8-P8", "P8-O2",
        "FZ-CZ",  "CZ-PZ"
    ]

    # Load 1 interictal and 1 ictal window from chb01
    inter_windows = np.load(
        str(PROCESSED_DIR / "chb01_interictal.npy"), mmap_mode="r")
    ictal_windows = np.load(
        str(PROCESSED_DIR / "chb01_ictal.npy"), mmap_mode="r")

    # Use middle of dataset for representative window
    inter_win = inter_windows[len(inter_windows)//2].astype(np.float64)
    ictal_win = ictal_windows[len(ictal_windows)//2].astype(np.float64)

    A_inter = build_adjacency(inter_win, alpha=0.5, top_k_percent=30)
    A_ictal = build_adjacency(ictal_win, alpha=0.5, top_k_percent=30)

    # Also compute mean adjacency across multiple windows
    n_sample = min(50, len(inter_windows))
    A_inter_mean = np.mean([
        build_adjacency(inter_windows[i].astype(np.float64))
        for i in range(n_sample)], axis=0)

    n_sample_i = min(50, len(ictal_windows))
    A_ictal_mean = np.mean([
        build_adjacency(ictal_windows[i].astype(np.float64))
        for i in range(n_sample_i)], axis=0)

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    vmax = max(A_inter.max(), A_ictal.max(),
               A_inter_mean.max(), A_ictal_mean.max())

    for ax, A, title in zip(
        axes.flat,
        [A_inter, A_ictal, A_inter_mean, A_ictal_mean],
        ["Interictal (single window)",
         "Ictal (single window)",
         f"Interictal (mean of {min(50,len(inter_windows))} windows)",
         f"Ictal (mean of {min(50,len(ictal_windows))} windows)"]
    ):
        im = ax.imshow(A, cmap="hot", vmin=0, vmax=vmax,
                       aspect="auto")
        ax.set_title(title, fontweight="bold", fontsize=10)
        ax.set_xticks(range(18))
        ax.set_yticks(range(18))
        ax.set_xticklabels(CHANNELS, rotation=90, fontsize=6)
        ax.set_yticklabels(CHANNELS, fontsize=6)
        plt.colorbar(im, ax=ax, shrink=0.8)

    plt.suptitle(
        "EEG Functional Connectivity (wPLI+AEC, top-30%)\nchb01 — Interictal vs Ictal",
        fontweight="bold", fontsize=12)
    plt.tight_layout()
    out = FIG_DIR / "fig3_adjacency_heatmap.png"
    plt.savefig(str(out), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating figures for supervisor report...")
    print("\n[1/3] Preprocessing summary...")
    plot_preprocessing_summary()

    print("\n[2/3] Raw vs filtered EEG...")
    plot_raw_vs_filtered()

    print("\n[3/3] Adjacency heatmaps...")
    plot_adjacency_heatmap()

    print(f"\nAll figures saved to: {FIG_DIR}")