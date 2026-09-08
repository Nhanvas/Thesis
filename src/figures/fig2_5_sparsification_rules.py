"""
fig2_5_sparsification_rules.py -- Fig 2.5, Figure Brief Round 2 Task C.

Two rows, patient chb11 (validation). Top row: fixed correlation threshold
(0.05). Bottom row: retain the strongest 20% of edges. Each row shows the
adjacency heatmap and the resulting graph, with the density printed in the
panel title.

The density values are READ from the Task E diagnostic output
(results/diagnostics/density_frobenius_v2_val/density_per_subject.csv,
interictal rows, mean over 712 windows at stride 20) -- not recomputed here
(brief §4: "If Task E has not been run, stop."). The heatmap/graph shown is
a SINGLE representative window (window 0, the same window Fig 2.4 uses),
built with graph_construction.py's own functions -- no new implementation.
A window-averaged adjacency was tried first and rejected: averaging the
top-20% mask across hundreds of windows (a different 30 edges survive in
each) produces a near-complete-looking mean matrix that visually
contradicts the 0.196 density in the title, even though the title's number
(the mean of each window's OWN density) is correct. A single window's own
top-20% graph is genuinely sparse and matches the printed number.
"""
import os as _os, sys as _sys
from pathlib import Path
_here = _os.path.dirname(_os.path.abspath(__file__))
_src = _os.path.dirname(_here)
for _p in (_here, _src, str(Path(_src) / "dataprep")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import numpy as np
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from graph_construction import (apply_car, compute_wpli, compute_aec, combine_adjacency,
                                apply_fixed_threshold, apply_topk_threshold,
                                DEFAULT_ALPHA, FIXED_THRESHOLD, DEFAULT_KEEP_RATIO)
import preprocessing as P
from palette import INTERICTAL, SEQUENTIAL_CMAP, apply_rc

ROOT = Path(_src).parent
PROC = ROOT / "data" / "processed"
SUBJ = "chb11"
STRIDE = 20
WINDOW_IDX = 0   # same window Fig 2.4 uses
TASK_E_CSV = ROOT / "results" / "diagnostics" / "density_frobenius_v2_val" / "density_per_subject.csv"
OUT = ROOT / "figures" / "fig2_5_sparsification_rules.png"


def raw_combined(window, alpha=DEFAULT_ALPHA, fs=256):
    w = apply_car(window.astype(np.float64))
    wpli = compute_wpli(w, fs=fs)
    aec = compute_aec(w) if alpha < 1.0 else np.zeros_like(wpli)
    return combine_adjacency(wpli, aec, alpha=alpha)


def draw_graph(ax, A, channels, title=None):
    n = len(channels)
    G = nx.from_numpy_array(A)
    G = nx.relabel_nodes(G, {i: channels[i] for i in range(n)})
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    pos = {channels[i]: (np.cos(angles[i]), np.sin(angles[i])) for i in range(n)}
    # Labels OUTSIDE the node markers (docs/FIGURE_FIXES_R3.md §1, Fig 2.5: "same
    # legibility fix as Fig 2.4" -- they were unreadable at print size on the nodes).
    label_pos = {channels[i]: (1.18 * np.cos(angles[i]), 1.18 * np.sin(angles[i])) for i in range(n)}
    weights = [G[u][v]["weight"] for u, v in G.edges()]
    max_w = max(weights) if weights else 1.0
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=140, node_color=INTERICTAL)
    nx.draw_networkx_labels(G, label_pos, ax=ax, font_size=6.5)
    if weights:
        nx.draw_networkx_edges(G, pos, ax=ax, width=[2.5 * wt / max_w for wt in weights],
                               alpha=0.6)
    if title:
        ax.set_title(title, fontsize=10)
    ax.set_xlim(-1.4, 1.4)
    ax.set_ylim(-1.4, 1.4)
    ax.set_aspect("equal")
    ax.set_axis_off()


def main():
    apply_rc()
    if not TASK_E_CSV.exists():
        raise SystemExit(f"Fig 2.5: Task E diagnostic output not found at {TASK_E_CSV} -- "
                         "run src/dataprep/density_frobenius_diagnostic.py for chb11 first, stop.")
    dens = pd.read_csv(TASK_E_CSV)
    dens = dens[(dens.subject == SUBJ) & (dens.split == "interictal")]
    dens_fixed = dens[dens.rule == "fixed_t0.05"]["mean_density"].iloc[0]
    dens_topk = dens[dens.rule == "topk20"]["mean_density"].iloc[0]
    n_sampled = int(dens[dens.rule == "topk20"]["n_windows_sampled"].iloc[0])
    print(f"[Fig 2.5] densities read from {TASK_E_CSV}: fixed={dens_fixed}, topk={dens_topk}, "
          f"n_windows_sampled={n_sampled}")

    arr = np.load(PROC / f"{SUBJ}_interictal.npy", mmap_mode="r")
    idx = list(range(0, arr.shape[0], STRIDE))
    if len(idx) != n_sampled:
        raise ValueError(f"Fig 2.5: stride {STRIDE} gives {len(idx)} windows, Task E used "
                         f"{n_sampled} -- stop, stride mismatch")

    A_raw = raw_combined(arr[WINDOW_IDX])
    A_fixed = apply_fixed_threshold(A_raw, threshold=FIXED_THRESHOLD)
    A_topk = apply_topk_threshold(A_raw, keep_ratio=DEFAULT_KEEP_RATIO)
    this_window_fixed_density = float(np.count_nonzero(np.triu(A_fixed, k=1))) / (18 * 17 / 2)
    this_window_topk_density = float(np.count_nonzero(np.triu(A_topk, k=1))) / (18 * 17 / 2)
    # docs/FIGURE_FIXES_R3.md §1, Fig 2.5: the densities printed in the panel titles were
    # subject-level values from the Task E diagnostic, but the matrix DISPLAYED is a single
    # window -- two different quantities, so a reader counting non-zero cells in the image
    # would not reproduce the printed number. The panel titles now print the DISPLAYED
    # window's own density; both numbers are printed to the console so the caption can state
    # the subject-level value separately.
    print(f"[Fig 2.5] subject-level mean density (Task E, {SUBJ}, {n_sampled} windows): "
          f"fixed={dens_fixed:.3f}, topk={dens_topk:.3f}")
    print(f"[Fig 2.5] window {WINDOW_IDX} own density (what the panels display and title): "
          f"fixed={this_window_fixed_density:.3f}, topk={this_window_topk_density:.3f}")
    fixed_diff = abs(dens_fixed - this_window_fixed_density)
    if fixed_diff > 0.01:
        print(f"[Fig 2.5] CAPTION NOTE: fixed-threshold rule -- displayed window's own density "
             f"({this_window_fixed_density:.3f}) differs from the subject-level mean "
             f"({dens_fixed:.3f}) by {fixed_diff:.3f} (> 0.01); state both in the caption "
             "rather than only the subject-level figure.")
    else:
        print(f"[Fig 2.5] fixed-threshold rule: window vs subject-level mean differ by "
             f"{fixed_diff:.3f} (<= 0.01, no caption note required)")

    channels = P.COMMON_CHANNELS
    fig, axes = plt.subplots(2, 2, figsize=(12, 11.5))

    im0 = axes[0, 0].imshow(A_fixed, vmin=0, vmax=A_fixed.max(), cmap=SEQUENTIAL_CMAP)
    axes[0, 0].set_xticks(range(len(channels))); axes[0, 0].set_yticks(range(len(channels)))
    axes[0, 0].set_xticklabels(channels, rotation=90, fontsize=6)
    axes[0, 0].set_yticklabels(channels, fontsize=6)
    # Brief §4, Fig 2.5: "the density printed in the panel title" -- kept as a
    # bare data value, not a narrative title (brief §1 rule 5). Printed once per row, on
    # the heatmap only -- the graph panel to its right no longer repeats it.
    axes[0, 0].set_title(f"density = {this_window_fixed_density:.3f}")
    fig.colorbar(im0, ax=axes[0, 0], shrink=0.85, pad=0.02)
    draw_graph(axes[0, 1], A_fixed, channels)

    im1 = axes[1, 0].imshow(A_topk, vmin=0, vmax=A_topk.max(), cmap=SEQUENTIAL_CMAP)
    axes[1, 0].set_xticks(range(len(channels))); axes[1, 0].set_yticks(range(len(channels)))
    axes[1, 0].set_xticklabels(channels, rotation=90, fontsize=6)
    axes[1, 0].set_yticklabels(channels, fontsize=6)
    axes[1, 0].set_title(f"density = {this_window_topk_density:.3f}")
    fig.colorbar(im1, ax=axes[1, 0], shrink=0.85, pad=0.02)
    draw_graph(axes[1, 1], A_topk, channels)

    # No figure number / descriptive title beyond the density values above
    # (brief §1 rule 5) -- rule identity (fixed vs top-20%), subject, window
    # index and the Task E sample size are printed to console above.
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[saved] {OUT.resolve()}")


if __name__ == "__main__":
    main()
