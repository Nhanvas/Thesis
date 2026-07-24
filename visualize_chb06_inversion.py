"""
================================================================================
 visualize_chb06_inversion.py
================================================================================
WHY THIS FILE EXISTS
---------------------
"Inverted connectivity" for chb06 has been a text-only claim across every
document (med_z_ictal negative, AUROC 0.44 near chance, event sens 2-4/10).
This script makes it VISIBLE, using data that is already cached (no GPU, no
retrain) plus an optional best-effort layer if raw adjacency arrays are
available on disk.

THREE PANELS
------------
1. TIMELINE (always available -- uses cached ensemble scores):
   chb06 vs a comparison "normal-direction" subject (default chb18), full
   recording, z-normalized ensemble score over time, true seizures shaded.
   For chb18 the shaded regions should show the score SPIKING; for chb06 the
   same shaded regions should show the score DIPPING -- that visual contrast
   *is* the inversion.

2. Z-SCORE DISTRIBUTION (always available, same data):
   interictal vs ictal z-score histograms for both subjects side by side.
   Normal subject: ictal distribution shifted RIGHT of interictal. chb06:
   ictal distribution shifted LEFT of interictal.

3. MEAN CONNECTIVITY HEATMAP (best-effort, optional):
   If raw adjacency .npy files (interictal / ictal, e.g. *_adjs_topk20.npy)
   can be found on disk for the requested subjects, plots mean interictal
   adjacency, mean ictal adjacency, and their difference (ictal - inter) as
   an 18x18 heatmap grid. For chb06 the diff matrix should be predominantly
   NEGATIVE (blue); for the comparison subject predominantly POSITIVE (red).
   If no adjacency files are found, this panel is skipped with a clear
   message -- the script does NOT fail, since panels 1-2 already make the
   point using data every setup already has cached.

Z-NORMALIZATION (matches the locked ensemble spec exactly)
------------------------------------------------------------
  all_s = concatenate([scores_inter, scores_ictal])
  med = median(all_s); mad = median(|all_s - med|) + 1e-9
  z = (score - med) / mad
This is the same all-windows-pooled formula used to build the locked
ensemble (no ictal-label dependency at the z-norm step itself; only the
FIGURE afterwards uses the true seizure timestamps, for shading/labeling).

USAGE
-----
  python visualize_chb06_inversion.py --summary_dir "F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary"
  python visualize_chb06_inversion.py --target chb06 --contrast chb18
  python visualize_chb06_inversion.py --adj_root data/processed --adj_variant _adjs_topk20

Requires: evaluation_protocol.py (same dir, for build_timeline/parse_summary_edf_list),
matplotlib, numpy. Runs entirely on cached scores (CPU, no GPU, no retrain).
================================================================================
"""

import argparse
import glob
import os
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import evaluation_protocol as E

WIN_SEC = E.WIN_SEC

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 130,
})


# ============================================================================
# Data loading
# ============================================================================
def load_scores(scores_dir, subj):
    i = Path(scores_dir) / f"{subj}_ens_inter.npy"
    c = Path(scores_dir) / f"{subj}_ens_ictal.npy"
    if not (i.exists() and c.exists()):
        return None, None
    return np.load(str(i)), np.load(str(c))


def z_normalize(inter, ictal):
    all_s = np.concatenate([inter, ictal])
    med = np.median(all_s)
    mad = np.median(np.abs(all_s - med)) + 1e-9
    return (inter - med) / mad, (ictal - med) / mad, med, mad


def find_adj(adj_root, subj, split, variant):
    """Mirrors attribution_c1.find_adj exactly, for consistency with the
    Phase-B attribution scripts' file-discovery convention."""
    excl = ["interictal", "_inter"] if split == "ictal" else []
    toks = ["interictal", "inter"] if split == "inter" else ["ictal"]
    for p in sorted(glob.glob(os.path.join(adj_root, "**", "*.npy"), recursive=True)):
        b = os.path.basename(p).lower()
        if subj not in b or not b.endswith(variant.lower() + ".npy"):
            continue
        if any(t in b for t in excl):
            continue
        if any(t in b for t in toks):
            return p
    return None


# ============================================================================
# Panel 1+2: timeline + z-distribution
# ============================================================================
def build_timeline_for_plot(subj, inter, ictal, z_inter, z_ictal, summary_dir):
    """Chronological z-normalized timeline for plotting, mirroring
    evaluation_protocol.build_timeline's window ordering but consuming the
    already z-normalized inter/ictal arrays (deterministic bootstrap seed)."""
    np.random.seed(0)
    zi_padded = z_inter  # feed z-normalized scores through the same reconstruction
    signal, is_ictal, sz_ranges, n_inter_h = E.build_timeline(
        subj, zi_padded, z_ictal, summary_dir)
    return signal, is_ictal, sz_ranges


def plot_timeline_and_distribution(target, contrast, data, out_dir):
    """data: dict subj -> (signal, is_ictal, sz_ranges, z_inter, z_ictal)"""
    fig, axes = plt.subplots(2, 1, figsize=(11, 6.5), sharex=False)
    for ax, subj in zip(axes, [target, contrast]):
        signal, is_ictal, sz_ranges, _, _ = data[subj]
        t = np.arange(len(signal)) * WIN_SEC / 3600.0
        ax.plot(t, signal, lw=0.4, color="#444444", alpha=0.85)
        ax.axhline(0, color="#aaaaaa", lw=0.6, ls="--")
        in_s, start = False, 0
        for i, ic in enumerate(is_ictal):
            if ic and not in_s:
                start, in_s = i, True
            elif not ic and in_s:
                ax.axvspan(start * WIN_SEC / 3600.0, i * WIN_SEC / 3600.0,
                          color="#d62728", alpha=0.30, lw=0)
                in_s = False
        if in_s:
            ax.axvspan(start * WIN_SEC / 3600.0, len(is_ictal) * WIN_SEC / 3600.0,
                      color="#d62728", alpha=0.30, lw=0)
        tag = " (inverted -- score DROPS at seizure onset)" if subj == target else \
              " (normal direction -- score RISES at seizure onset)"
        ax.set_title(f"{subj}{tag}", fontsize=10)
        ax.set_ylabel("z-normalized\nensemble score")
    axes[-1].set_xlabel("Time (hours)")
    fig.suptitle("Ensemble anomaly-score timeline: shaded = true seizure "
                 f"({target} vs {contrast})", fontsize=11, y=1.01)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(Path(out_dir) / f"fig_timeline_{target}_vs_{contrast}.{ext}",
                   bbox_inches="tight")
    plt.close(fig)

    # ---- z-score distribution panel ----
    fig2, axes2 = plt.subplots(1, 2, figsize=(10, 4))
    for ax, subj in zip(axes2, [target, contrast]):
        _, _, _, z_inter, z_ictal = data[subj]
        bins = np.linspace(
            min(z_inter.min(), z_ictal.min()), max(z_inter.max(), z_ictal.max()), 40)
        ax.hist(z_inter, bins=bins, density=True, alpha=0.55, color="#1f4e79",
               label=f"interictal (n={len(z_inter)})")
        ax.hist(z_ictal, bins=bins, density=True, alpha=0.55, color="#d62728",
               label=f"ictal (n={len(z_ictal)})")
        ax.axvline(np.median(z_inter), color="#1f4e79", lw=1.2, ls="--")
        ax.axvline(np.median(z_ictal), color="#d62728", lw=1.2, ls="--")
        mzi = np.median(z_ictal)
        ax.set_title(f"{subj}  (median z_ictal = {mzi:+.3f})", fontsize=10)
        ax.set_xlabel("z-normalized ensemble score")
        ax.legend(fontsize=8)
    axes2[0].set_ylabel("density")
    fig2.suptitle("Interictal vs ictal score distribution", fontsize=11, y=1.02)
    fig2.tight_layout()
    for ext in ("png", "pdf"):
        fig2.savefig(Path(out_dir) / f"fig_zdist_{target}_vs_{contrast}.{ext}",
                    bbox_inches="tight")
    plt.close(fig2)


# ============================================================================
# Panel 3: mean-adjacency heatmaps (best-effort)
# ============================================================================
def plot_adjacency_panel(target, contrast, adj_root, adj_variant, out_dir):
    subjects = [target, contrast]
    found = {}
    for subj in subjects:
        ip = find_adj(adj_root, subj, "inter", adj_variant)
        cp = find_adj(adj_root, subj, "ictal", adj_variant)
        if ip and cp:
            found[subj] = (np.load(ip), np.load(cp))
    if not found:
        print(f"  [adjacency panel skipped] no *{adj_variant}.npy found under "
              f"'{adj_root}' for {subjects} -- panels 1-2 already show the "
              f"inversion using cached scores; this panel is optional.")
        return

    n_rows = len(found)
    fig, axes = plt.subplots(n_rows, 3, figsize=(11, 3.6 * n_rows), squeeze=False)
    for row, subj in enumerate(subjects):
        if subj not in found:
            for c in range(3):
                axes[row][c].axis("off")
            axes[row][0].text(0.5, 0.5, f"{subj}: adjacency not found",
                             ha="center", va="center", transform=axes[row][0].transAxes)
            continue
        inter_adj, ictal_adj = found[subj]
        mean_inter = inter_adj.mean(axis=0)
        mean_ictal = ictal_adj.mean(axis=0)
        diff = mean_ictal - mean_inter
        vmax_pair = max(mean_inter.max(), mean_ictal.max())
        im0 = axes[row][0].imshow(mean_inter, cmap="viridis", vmin=0, vmax=vmax_pair)
        axes[row][0].set_title(f"{subj}: mean interictal", fontsize=9)
        im1 = axes[row][1].imshow(mean_ictal, cmap="viridis", vmin=0, vmax=vmax_pair)
        axes[row][1].set_title(f"{subj}: mean ictal", fontsize=9)
        vmax_diff = np.abs(diff).max()
        im2 = axes[row][2].imshow(diff, cmap="RdBu_r", vmin=-vmax_diff, vmax=vmax_diff)
        sign = "predominantly NEGATIVE" if np.median(diff) < 0 else "predominantly POSITIVE"
        axes[row][2].set_title(f"{subj}: ictal - inter ({sign})", fontsize=9)
        for ax, im in zip(axes[row], [im0, im1, im2]):
            plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle("Mean connectivity: interictal vs ictal (blue diff = "
                 "connectivity DECREASES during seizure)", fontsize=11, y=1.02)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(Path(out_dir) / f"fig_adjacency_{target}_vs_{contrast}.{ext}",
                   bbox_inches="tight")
    plt.close(fig)
    print(f"  [adjacency panel written] for: {list(found.keys())}")


# ============================================================================
# Orchestration
# ============================================================================
def main():
    ap = argparse.ArgumentParser(description="Visualize chb06's inverted connectivity")
    ap.add_argument("--scores_dir", default="results/cpd/scores")
    ap.add_argument("--summary_dir",
                    default=r"F:\Study\Thesis\Dataset\CHB-MIT\CHB info\summary")
    ap.add_argument("--out_dir", default="results/phaseB/fp_diagnosis/figures")
    ap.add_argument("--target", default="chb06")
    ap.add_argument("--contrast", default="chb18",
                    help="a 'normal-direction' subject for visual contrast")
    ap.add_argument("--adj_root", default="data/processed",
                    help="root to search for raw adjacency .npy (optional panel)")
    ap.add_argument("--adj_variant", default="_adjs_topk20")
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    data = {}
    for subj in [args.target, args.contrast]:
        inter, ictal = load_scores(args.scores_dir, subj)
        if inter is None:
            print(f"[skip] {subj}: cached ensemble scores not found in "
                  f"{args.scores_dir}")
            continue
        z_inter, z_ictal, med, mad = z_normalize(inter, ictal)
        signal, is_ictal, sz_ranges = build_timeline_for_plot(
            subj, inter, ictal, z_inter, z_ictal, args.summary_dir)
        data[subj] = (signal, is_ictal, sz_ranges, z_inter, z_ictal)
        print(f"  {subj}: median z_ictal = {np.median(z_ictal):+.3f}   "
              f"({len(sz_ranges)} seizures, n_inter={len(inter)}, n_ictal={len(ictal)})")

    if args.target not in data or args.contrast not in data:
        print("\nCannot build the timeline/distribution figures -- both "
              "--target and --contrast need cached ensemble scores.")
        return

    plot_timeline_and_distribution(args.target, args.contrast, data, out)
    plot_adjacency_panel(args.target, args.contrast, args.adj_root,
                        args.adj_variant, out)

    print(f"\nWrote figures to: {out.resolve()}")
    print("  fig_timeline_*        -- score dips vs spikes at seizure onset")
    print("  fig_zdist_*           -- ictal distribution shifted below/above interictal")
    print("  fig_adjacency_*       -- (if adjacency found) mean connectivity inversion")


if __name__ == "__main__":
    main()