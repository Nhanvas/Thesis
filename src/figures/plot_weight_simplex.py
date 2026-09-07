"""
================================================================================
 plot_weight_simplex.py -- Fig 2.9 ensemble weight surface
================================================================================
Ternary heatmap over the 231 systematic grid points (0.05 step) in
results/phaseB/tier2/weights_rlg/derive_weights_rlg_grid.csv, plus the
equal-weight point which is the 232nd row and does not sit on that grid.

Marks: the best point (0.10, 0.45, 0.45; 0.9405), the equal-weight point
(0.9283, the last row of the file), and the region within 0.005 of the best,
which holds 29 points. The equal-weight point falls OUTSIDE that region --
that is what this figure is for.
"""
import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
from palette import apply_rc

BEST = dict(w_recon=0.10, w_latent=0.45, w_gamma=0.45, auroc=0.9405)
EQUAL = dict(w_recon=1 / 3, w_latent=1 / 3, w_gamma=1 / 3, auroc=0.9283)
BAND = 0.005


def to_xy(w_recon, w_latent, w_gamma):
    """Barycentric -> cartesian. Vertices: recon=(0,0), latent=(1,0), gamma=(0.5, sqrt3/2)."""
    x = w_latent + 0.5 * w_gamma
    y = (np.sqrt(3) / 2) * w_gamma
    return x, y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="results/phaseB/tier2/weights_rlg/derive_weights_rlg_grid.csv")
    ap.add_argument("--out_dir", default="figures/weights")
    a = ap.parse_args()

    apply_rc()
    df = pd.read_csv(a.csv)

    # Row 232 (index 231) is the equal-weight point, off the 0.05 systematic grid.
    is_equal = np.isclose(df.w_recon, 1 / 3) & np.isclose(df.w_latent, 1 / 3) & np.isclose(df.w_gamma, 1 / 3)
    grid = df[~is_equal].reset_index(drop=True)
    eq_row = df[is_equal].iloc[0]

    print(f"[Fig 2.9] loaded {len(df)} rows: {len(grid)} systematic grid points + "
         f"1 equal-weight point")
    if len(grid) != 231:
        raise ValueError(f"expected 231 systematic grid points, got {len(grid)} -- stop")

    best_idx = grid.val_macro_auroc.idxmax()
    best_row = grid.loc[best_idx]
    print(f"  best point: w=({best_row.w_recon:.2f},{best_row.w_latent:.2f},{best_row.w_gamma:.2f}) "
         f"auroc={best_row.val_macro_auroc:.4f}  (brief: (0.10,0.45,0.45), 0.9405)")
    if not (np.isclose(best_row.w_recon, BEST["w_recon"]) and
            np.isclose(best_row.w_latent, BEST["w_latent"]) and
            np.isclose(best_row.w_gamma, BEST["w_gamma"]) and
            round(best_row.val_macro_auroc, 4) == BEST["auroc"]):
        raise ValueError("best point does not match the brief -- stop")

    print(f"  equal-weight point: auroc={eq_row.val_macro_auroc:.4f}  (brief: 0.9283)")
    if round(eq_row.val_macro_auroc, 4) != EQUAL["auroc"]:
        raise ValueError("equal-weight AUROC does not match the brief -- stop")

    within_band = grid[grid.val_macro_auroc >= best_row.val_macro_auroc - BAND]
    print(f"  points within {BAND} of best: {len(within_band)}  (brief: 29)")
    if len(within_band) != 29:
        raise ValueError(f"expected 29 points within {BAND} of best, got {len(within_band)} -- stop")
    eq_in_band = eq_row.val_macro_auroc >= best_row.val_macro_auroc - BAND
    print(f"  equal-weight point inside band: {eq_in_band}  (brief: False, outside)")
    if eq_in_band:
        raise ValueError("equal-weight point unexpectedly falls inside the tolerance band -- stop")

    x, y = to_xy(grid.w_recon.values, grid.w_latent.values, grid.w_gamma.values)

    fig, ax = plt.subplots(figsize=(7.5, 7))
    sc = ax.scatter(x, y, c=grid.val_macro_auroc, cmap="viridis", s=140, marker="h",
                    edgecolor="none", zorder=2)
    cb = fig.colorbar(sc, ax=ax, fraction=0.045, pad=0.03)
    cb.set_label("validation macro AUROC")

    bx, by = to_xy(within_band.w_recon.values, within_band.w_latent.values, within_band.w_gamma.values)
    ax.scatter(bx, by, s=220, facecolor="none", edgecolor="#d62728", linewidth=1.6, zorder=3,
              label=f"within {BAND} of best (n={len(within_band)})")

    xb, yb = to_xy(BEST["w_recon"], BEST["w_latent"], BEST["w_gamma"])
    ax.scatter([xb], [yb], marker="*", s=420, color="#d62728", edgecolor="black",
              linewidth=0.8, zorder=5, label=f"best (0.10, 0.45, 0.45) = {BEST['auroc']:.4f}")

    xe, ye = to_xy(EQUAL["w_recon"], EQUAL["w_latent"], EQUAL["w_gamma"])
    ax.scatter([xe], [ye], marker="D", s=140, color="white", edgecolor="black",
              linewidth=1.3, zorder=5, label=f"equal weighting, as used = {EQUAL['auroc']:.4f}")

    # triangle outline + vertex labels
    tri = np.array([[0, 0], [1, 0], [0.5, np.sqrt(3) / 2], [0, 0]])
    ax.plot(tri[:, 0], tri[:, 1], color="black", lw=1.0, zorder=1)
    ax.text(0, -0.05, "w_recon = 1", ha="center", va="top", fontsize=9)
    ax.text(1, -0.05, "w_latent = 1", ha="center", va="top", fontsize=9)
    ax.text(0.5, np.sqrt(3) / 2 + 0.03, "w_gamma = 1", ha="center", va="bottom", fontsize=9)

    ax.set_xlim(-0.12, 1.12)
    ax.set_ylim(-0.12, np.sqrt(3) / 2 + 0.12)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.legend(loc="upper right", fontsize=8, framealpha=0.95, bbox_to_anchor=(1.02, 1.0))
    ax.set_title("Fig 2.9 — ensemble weight surface, validation macro AUROC\n"
                "231-point simplex grid; equal weighting falls outside the near-best region",
                fontsize=11)

    fig.tight_layout()
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / "fig2_9_weight_simplex.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  [saved] {(out_dir / 'fig2_9_weight_simplex.png').resolve()}")


if __name__ == "__main__":
    main()
