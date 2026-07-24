"""
fig6_raw_eeg.py — Raw EEG Illustration for Chapter 1
Uses preprocessed (z-scored) EEG windows to illustrate interictal vs ictal.
Shows 18 channels with seizure onset marker. No external EDF library needed.
Usage: python src/fig6_raw_eeg.py
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import re
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────
DATA_DIR = Path("data/processed")
OUT_DIR  = Path("results/cpd/figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SUBJ = "chb13"   # Good AUROC, clear seizure morphology
N_INTER_SHOW = 5  # interictal windows before seizure (= 20 seconds)
N_ICTAL_SHOW = 10  # ictal windows to show (= 40 seconds)
# Inter windows to sample: windows around index 5000 (middle of recording, quiet)
INTER_START_IDX = 5000

CHANNEL_NAMES = [
    "FP1-F7","F7-T7","T7-P7","P7-O1",
    "FP1-F3","F3-C3","C3-P3","P3-O1",
    "FP2-F4","F4-C4","C4-P4","P4-O2",
    "FP2-F8","F8-T8","T8-P8","P8-O2",
    "FZ-CZ","CZ-PZ",
]
FS = 256
WIN_SAMPLES = FS * 4   # 1024 samples per 4s window

def main():
    print(f"Generating Figure 6: Raw EEG illustration ({SUBJ})")

    inter = np.load(DATA_DIR / f"{SUBJ}_interictal.npy", mmap_mode='r')
    ictal = np.load(DATA_DIR / f"{SUBJ}_ictal.npy",      mmap_mode='r')

    # Select representative windows
    i0 = min(INTER_START_IDX, len(inter) - N_INTER_SHOW - 1)
    inter_windows = inter[i0 : i0 + N_INTER_SHOW]    # [5, 18, 1024]
    ictal_windows = ictal[:N_ICTAL_SHOW]               # [10, 18, 1024]

    # Concatenate along time axis per channel: [18, (N_inter+N_ictal)*1024]
    n_ch = inter_windows.shape[1]
    seg = np.concatenate(
        [inter_windows.transpose(1,0,2).reshape(n_ch,-1),
         ictal_windows.transpose(1,0,2).reshape(n_ch,-1)],
        axis=1)   # [18, total_samples]

    total_samples = seg.shape[1]
    onset_sample  = N_INTER_SHOW * WIN_SAMPLES   # where ictal begins
    t_sec = np.arange(total_samples) / FS        # time in seconds

    # Normalize each channel for display (peak-to-peak = 2 units)
    seg_norm = np.zeros_like(seg)
    for ch in range(n_ch):
        pp = np.ptp(seg[ch]) + 1e-9
        seg_norm[ch] = (seg[ch] - seg[ch].mean()) / pp * 2.5

    # Stack channels with offset
    offset = 3.5   # vertical spacing between channels
    fig, ax = plt.subplots(figsize=(14, 10))

    for ch in range(n_ch):
        y = seg_norm[ch] + (n_ch - 1 - ch) * offset
        color = '#37474F'
        ax.plot(t_sec, y, color=color, lw=0.55, alpha=0.85)

    # Seizure onset line
    onset_t = onset_sample / FS
    ax.axvline(onset_t, color='#C62828', lw=2.5, ls='--', label='Seizure onset', zorder=5)
    ax.axvspan(onset_t, t_sec[-1], color='#EF5350', alpha=0.07, label='Ictal period')

    # Background shading for interictal
    ax.axvspan(0, onset_t, color='#E3F2FD', alpha=0.5, label='Interictal period', zorder=0)

    # Labels
    ax.set_yticks([(n_ch - 1 - ch) * offset for ch in range(n_ch)])
    ax.set_yticklabels(CHANNEL_NAMES, fontsize=8)
    ax.set_xlabel('Time (seconds)', fontsize=11)
    ax.set_title(f'Subject {SUBJ}: Scalp EEG — Interictal (left) vs Ictal (right)',
                 fontsize=12, fontweight='bold')
    ax.legend(loc='upper right', fontsize=9)
    ax.set_xlim(0, t_sec[-1])
    ax.grid(True, axis='x', alpha=0.3)

    # Annotation labels above the plot
    ax.text(onset_t/2, (n_ch-0.3)*offset, 'Interictal\n(normal EEG)',
            ha='center', va='bottom', fontsize=10, color='#1565C0', fontweight='bold')
    ax.text(onset_t + (t_sec[-1]-onset_t)/2, (n_ch-0.3)*offset, 'Ictal\n(seizure activity)',
            ha='center', va='bottom', fontsize=10, color='#C62828', fontweight='bold')

    plt.tight_layout()
    out = OUT_DIR / f"fig6_raw_eeg_{SUBJ}.png"
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"→ {out}")

if __name__ == "__main__":
    main()