"""
fig2_4_graph_construction.py -- Fig 2.4, Figure Brief Round 2 Task C.

Four panels, one window of chb11 (validation patient), showing a single
window becoming a graph:
  (a) the 4 s signal segment, all 18 channels, stacked with an offset
  (b) the five log band powers per channel, an 18x5 heatmap
  (c) the weighted adjacency before sparsification, 18x18
  (d) the graph after retaining the strongest 20% of edges, fixed node
      layout shared with (c), edge width proportional to weight

Sources: data/processed/chb11_interictal.npy, chb11_interictal_features.npy,
and graph_construction.py (compute_wpli / compute_aec / combine_adjacency /
apply_topk_threshold at their locked defaults -- brief §4's "adjacency
trap": no new implementation of the construction rule).

The window index and the resulting edge count in (d) are printed (the brief
expects 30 for keep_ratio=0.20 on 18 channels).
"""
import os as _os, sys as _sys
from pathlib import Path
_here = _os.path.dirname(_os.path.abspath(__file__))
_src = _os.path.dirname(_here)
for _p in (_here, _src, str(Path(_src) / "dataprep")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import numpy as np
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from graph_construction import (apply_car, compute_wpli, compute_aec, combine_adjacency,
                                apply_topk_threshold, DEFAULT_ALPHA, DEFAULT_KEEP_RATIO)
import preprocessing as P
from feature_extraction import BANDS
from palette import INTERICTAL, SEQUENTIAL_CMAP, apply_rc

ROOT = Path(_src).parent
PROC = ROOT / "data" / "processed"
SUBJ = "chb11"
WINDOW_IDX = 0
OUT = ROOT / "figures" / "fig2_4_graph_construction.png"


def main():
    apply_rc()
    channels = P.COMMON_CHANNELS
    window = np.load(PROC / f"{SUBJ}_interictal.npy", mmap_mode="r")[WINDOW_IDX]
    feats = np.load(PROC / f"{SUBJ}_interictal_features.npy", mmap_mode="r")[WINDOW_IDX]
    print(f"[Fig 2.4] {SUBJ}, interictal window index {WINDOW_IDX} "
          f"(of {np.load(PROC / f'{SUBJ}_interictal.npy', mmap_mode='r').shape[0]})")

    w = apply_car(window.astype(np.float64))
    wpli = compute_wpli(w, fs=P.FS)
    aec = compute_aec(w)
    A = combine_adjacency(wpli, aec, alpha=DEFAULT_ALPHA)
    A_topk = apply_topk_threshold(A, keep_ratio=DEFAULT_KEEP_RATIO)
    n_edges = int(np.count_nonzero(np.triu(A_topk, k=1)))
    print(f"[Fig 2.4] edges retained at keep_ratio={DEFAULT_KEEP_RATIO}: {n_edges} (brief: 30)")
    if n_edges != 30:
        raise ValueError(f"Fig 2.4: {n_edges} edges retained, expected 30 -- stop")

    fig = plt.figure(figsize=(14, 11))
    gs = fig.add_gridspec(2, 2, hspace=0.32, wspace=0.28, top=0.93, bottom=0.06,
                          left=0.07, right=0.97)
    ax_sig = fig.add_subplot(gs[0, 0])
    ax_band = fig.add_subplot(gs[0, 1])
    ax_adj = fig.add_subplot(gs[1, 0])
    ax_graph = fig.add_subplot(gs[1, 1])

    # (a) signal segment, stacked with offset. docs/FIGURE_FIXES_R3.md §1, Fig 2.4: no
    # amplitude scale was shown -- same fix as Fig 2.3, an explicit scale bar in microvolts.
    t = np.arange(window.shape[1]) / P.FS
    offset = 6.0 * np.median(np.std(window, axis=1))
    for i, ch in enumerate(channels):
        ax_sig.plot(t, window[len(channels) - 1 - i] + i * offset, color=INTERICTAL, lw=0.6)
    ax_sig.set_yticks([i * offset for i in range(len(channels))])
    ax_sig.set_yticklabels(list(reversed(channels)), fontsize=6)
    ax_sig.set_xlabel("Time (s)")
    ax_sig.set_title("(a)")
    bar_uv = round(offset / 6.0, -1) or 10.0
    y0, y1 = ax_sig.get_ylim(); x0, x1 = ax_sig.get_xlim()
    bx = x0 + 0.02 * (x1 - x0); by0 = y0 + 0.02 * (y1 - y0); by1 = by0 + bar_uv
    ax_sig.plot([bx, bx], [by0, by1], color="black", lw=1.6, solid_capstyle="butt", clip_on=False)
    ax_sig.text(bx + 0.012 * (x1 - x0), (by0 + by1) / 2, f"{bar_uv:g} µV",
               fontsize=7, va="center", ha="left")

    # (b) band power heatmap -- one sequential colormap shared with (c), Fig 1.2 and Fig 2.5
    # (docs/FIGURE_FIXES_R3.md §1: they previously used different colormaps), and the
    # colorbar is now labelled with the quantity and its unit.
    band_names = list(BANDS.keys())
    im_b = ax_band.imshow(feats, aspect="auto", cmap=SEQUENTIAL_CMAP)
    ax_band.set_xticks(range(len(band_names)))
    ax_band.set_xticklabels(band_names)
    ax_band.set_yticks(range(len(channels)))
    ax_band.set_yticklabels(channels, fontsize=6)
    ax_band.set_title("(b)")
    cb_b = fig.colorbar(im_b, ax=ax_band, shrink=0.85, pad=0.02)
    cb_b.set_label("Log band power (z-scored)")

    # (c) weighted adjacency before sparsification
    im_c = ax_adj.imshow(A, vmin=0, vmax=A.max(), cmap=SEQUENTIAL_CMAP)
    ax_adj.set_xticks(range(len(channels))); ax_adj.set_yticks(range(len(channels)))
    ax_adj.set_xticklabels(channels, rotation=90, fontsize=6)
    ax_adj.set_yticklabels(channels, fontsize=6)
    ax_adj.set_title("(c)")
    fig.colorbar(im_c, ax=ax_adj, shrink=0.85, pad=0.02)

    # (d) graph after top-20% sparsification -- SAME node layout as (c). Node labels are
    # placed radially OUTSIDE the node markers (docs/FIGURE_FIXES_R3.md §1: they were
    # unreadable at print size sitting on top of the nodes -- panel (d) is the payoff of the
    # figure), and the axes are widened so the outward labels are not clipped.
    G = nx.from_numpy_array(A_topk)
    G = nx.relabel_nodes(G, {i: channels[i] for i in range(len(channels))})
    n = len(channels)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    pos = {channels[i]: (np.cos(angles[i]), np.sin(angles[i])) for i in range(n)}
    label_pos = {channels[i]: (1.18 * np.cos(angles[i]), 1.18 * np.sin(angles[i])) for i in range(n)}
    weights = [G[u][v]["weight"] for u, v in G.edges()]
    max_w = max(weights) if weights else 1.0
    nx.draw_networkx_nodes(G, pos, ax=ax_graph, node_size=180, node_color=INTERICTAL)
    nx.draw_networkx_labels(G, label_pos, ax=ax_graph, font_size=7.5)
    nx.draw_networkx_edges(G, pos, ax=ax_graph,
                           width=[3.5 * wt / max_w for wt in weights], alpha=0.7)
    ax_graph.set_xlim(-1.4, 1.4)
    ax_graph.set_ylim(-1.4, 1.4)
    ax_graph.set_aspect("equal")
    ax_graph.set_title("(d)")
    ax_graph.set_axis_off()

    # No figure number / descriptive title on the image (brief §1 rule 5) --
    # subject, window index and edge count are printed to console above.
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[saved] {OUT.resolve()}")


if __name__ == "__main__":
    main()
