"""
fig_3scores_8subj.py
3 rows (z_recon | z_temporal | |z_gamma|)  x  8 columns (test subjects)
Each panel: score values before and after seizure 1 onset.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

DATA_DIR   = Path("data/processed")
TEMP_DIR   = Path("data/processed/temporal_zscores")
SCORES_DIR = Path("results/cpd/scores")
OUT_DIR    = Path("results/cpd/figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

WIN_SEC      = 4
W_R, W_T, W_G = 0.35, 0.30, 0.35
N_PRE        = 25   # interictal windows before onset to show  (100 s)
N_POST       = 15   # ictal windows after onset to show        (60 s, capped)

TEST_SUBJS = ["chb03","chb06","chb13","chb14","chb15","chb16","chb17","chb18"]
AUROC_MAP  = {
    "chb03":0.9518,"chb06":0.4093,"chb13":0.8191,"chb14":0.8624,
    "chb15":0.7915,"chb16":0.8973,"chb17":0.7455,"chb18":0.9253,
}

# (key, colour, y-axis label)
SCORE_ROWS = [
    ("recon", "#1565C0", "z_recon\n(Reconstruction)"),
    ("temp",  "#E65100", "z_temporal\n(Temporal LSTM)"),
    ("gamma", "#2E7D32", "|z_gamma|\n(Gamma AEC)"),
]


def robust_z(a, b):
    s = np.concatenate([a, b])
    m = np.median(s)
    d = np.median(np.abs(s - m)) + 1e-9
    return (a - m) / d, (b - m) / d


def load_components(subj, n_pre, n_post):
    """Return dict key → (inter_segment, ictal_segment), each centred on onset."""
    ens_i   = np.load(SCORES_DIR / f"{subj}_ens_inter.npy")
    ens_c   = np.load(SCORES_DIR / f"{subj}_ens_ictal.npy")
    raw_t_i = np.load(TEMP_DIR   / f"temporal_{subj}_zinter.npy")
    raw_t_c = np.load(TEMP_DIR   / f"temporal_{subj}_zictal.npy")
    raw_g_i = np.load(DATA_DIR   / f"gamma_aec_{subj}_inter.npy")
    raw_g_c = np.load(DATA_DIR   / f"gamma_aec_{subj}_ictal.npy")

    ni = min(len(ens_i), len(raw_t_i), len(raw_g_i))
    nc = min(len(ens_c), len(raw_t_c), len(raw_g_c))

    z_t_i, z_t_c = robust_z(raw_t_i[:ni], raw_t_c[:nc])
    z_g_i, z_g_c = robust_z(raw_g_i[:ni], raw_g_c[:nc])
    ga_i = np.abs(z_g_i)
    ga_c = np.abs(z_g_c)

    # Recover reconstruction component from cached ensemble
    z_r_i = (ens_i[:ni] - W_T * z_t_i - W_G * ga_i) / W_R
    z_r_c = (ens_c[:nc] - W_T * z_t_c - W_G * ga_c) / W_R

    n_pre_use  = min(n_pre,  ni)
    n_post_use = min(n_post, nc)

    return {
        "recon": (z_r_i[-n_pre_use:], z_r_c[:n_post_use]),
        "temp":  (z_t_i[-n_pre_use:], z_t_c[:n_post_use]),
        "gamma": (ga_i[-n_pre_use:],  ga_c[:n_post_use]),
    }


def main():
    print("Generating fig_3scores_8subj ...")

    fig, axes = plt.subplots(3, 8, figsize=(26, 8))
    plt.subplots_adjust(hspace=0.42, wspace=0.09)

    for col, subj in enumerate(TEST_SUBJS):
        print(f"  {subj} ...", end=" ", flush=True)
        comp = load_components(subj, N_PRE, N_POST)

        for row, (key, color, ylabel) in enumerate(SCORE_ROWS):
            ax = axes[row, col]
            inter_seg, ictal_seg = comp[key]

            n_i = len(inter_seg)
            n_c = len(ictal_seg)
            t_i = np.arange(-n_i, 0) * WIN_SEC   # seconds before onset
            t_c = np.arange(0,  n_c) * WIN_SEC    # seconds after onset
            t   = np.concatenate([t_i, t_c])
            y   = np.concatenate([inter_seg, ictal_seg])

            # Light smoothing (3 windows = 12 s) for cleaner display
            y_sm = pd.Series(y).rolling(3, min_periods=1, center=True).mean().values

            # Ictal period shading
            if n_c > 0:
                ax.axvspan(0, n_c * WIN_SEC, color="#FFCDD2", alpha=0.60, zorder=0)

            ax.fill_between(t, y_sm, alpha=0.18, color=color, zorder=1)
            ax.plot(t, y_sm,  color=color, lw=1.1, zorder=2)
            ax.axvline(0, color="#C62828", lw=1.5, ls="--", zorder=3)
            ax.axhline(0, color="gray",   lw=0.5, ls=":",  zorder=0)
            ax.grid(axis="y", alpha=0.18)

            # Titles and axis labels
            if row == 0:
                ax.set_title(f"{subj}\nAUROC={AUROC_MAP[subj]:.3f}",
                             fontsize=8.5, fontweight="bold", pad=3)
            if col == 0:
                ax.set_ylabel(ylabel, fontsize=8.0)
            else:
                ax.set_yticklabels([])
            if row == 2:
                ax.set_xlabel("Time (s)", fontsize=7.5)
                ax.tick_params(axis="x", labelsize=7)
            else:
                ax.set_xticklabels([])
            ax.tick_params(axis="y", labelsize=6.5)

        print("done")

    from matplotlib.patches import Patch
    from matplotlib.lines   import Line2D
    handles = [
        Patch(facecolor="#FFCDD2", alpha=0.65, label="Ictal period (annotation)"),
        Line2D([0],[0], color="#C62828", lw=1.5, ls="--", label="Seizure onset (t = 0 s)"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=2, fontsize=9,
               bbox_to_anchor=(0.5, -0.03), framealpha=0.9)

    fig.suptitle(
        "Three Anomaly Score Components Around Seizure 1 Onset — All 8 Test Subjects",
        fontsize=12, fontweight="bold", y=1.01,
    )

    out = OUT_DIR / "fig_3scores_8subj.png"
    plt.savefig(out, dpi=220, bbox_inches="tight")
    plt.close()
    print(f"\nSaved → {out}")


if __name__ == "__main__":
    main()