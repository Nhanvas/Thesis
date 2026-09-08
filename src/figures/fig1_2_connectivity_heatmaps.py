"""
fig1_2_connectivity_heatmaps.py -- Fig 1.2, Figure Brief Round 2 Task C.

Two adjacency heatmaps side by side (interictal, ictal), shared colour
scale, one colorbar, 18x18, channels labelled on both axes. Patient chb11
(validation, per the illustration policy). Weighted adjacency BEFORE
sparsification -- sparsification is a Chapter 2 concept and this figure
sits in Chapter 1 -- averaged over windows.

Source: data/processed/chb11_{interictal,ictal}.npy, adjacency rebuilt with
graph_construction.compute_wpli / compute_aec / combine_adjacency at
DEFAULT_ALPHA (brief §4, "the adjacency trap" -- no committed fixed-
threshold array exists, so this figure legitimately rebuilds the adjacency;
no new implementation of the construction rule itself). Interictal windows
are subsampled (stride 20, matching the Task E diagnostic's convention) for
tractability; ictal is used in full. The number of windows averaged in each
panel is printed, never assumed.
"""
import os as _os, sys as _sys
from pathlib import Path
_here = _os.path.dirname(_os.path.abspath(__file__))
_src = _os.path.dirname(_here)
for _p in (_here, _src, str(Path(_src) / "dataprep")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from graph_construction import apply_car, compute_wpli, compute_aec, combine_adjacency, DEFAULT_ALPHA
import preprocessing as P
from palette import apply_rc

ROOT = Path(_src).parent
PROC = ROOT / "data" / "processed"
SUBJ = "chb11"
STRIDE_INTER = 20
OUT = ROOT / "figures" / "fig1_2_connectivity_heatmaps.png"


def raw_combined(window, alpha=DEFAULT_ALPHA, fs=256):
    w = apply_car(window.astype(np.float64))
    wpli = compute_wpli(w, fs=fs)
    aec = compute_aec(w) if alpha < 1.0 else np.zeros_like(wpli)
    return combine_adjacency(wpli, aec, alpha=alpha)


def mean_adjacency(path, stride):
    arr = np.load(path, mmap_mode="r")
    idx = range(0, arr.shape[0], max(stride, 1))
    total = None
    n = 0
    for i in idx:
        A = raw_combined(arr[i])
        total = A.copy() if total is None else total + A
        n += 1
    return total / n, n


def main():
    apply_rc()
    A_inter, n_inter = mean_adjacency(PROC / f"{SUBJ}_interictal.npy", STRIDE_INTER)
    A_ictal, n_ictal = mean_adjacency(PROC / f"{SUBJ}_ictal.npy", 1)
    print(f"[Fig 1.2] {SUBJ}: interictal windows averaged = {n_inter} (stride {STRIDE_INTER}), "
          f"ictal windows averaged = {n_ictal} (all)")

    vmax = max(A_inter.max(), A_ictal.max())
    channels = P.COMMON_CHANNELS

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.6))
    im0 = axes[0].imshow(A_inter, vmin=0, vmax=vmax, cmap="viridis")
    axes[0].set_title("Interictal")
    im1 = axes[1].imshow(A_ictal, vmin=0, vmax=vmax, cmap="viridis")
    axes[1].set_title("Ictal")

    for ax in axes:
        ax.set_xticks(range(len(channels)))
        ax.set_yticks(range(len(channels)))
        ax.set_xticklabels(channels, rotation=90, fontsize=6)
        ax.set_yticklabels(channels, fontsize=6)

    cbar = fig.colorbar(im1, ax=axes, shrink=0.85, pad=0.02)
    cbar.set_label("Combined wPLI + AEC adjacency weight (unsparsified)")

    # No figure number / descriptive title on the image (brief §1 rule 5).
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[saved] {OUT.resolve()}")


if __name__ == "__main__":
    main()
