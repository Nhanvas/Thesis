"""
================================================================================
 visualize_channel_attribution.py
================================================================================
WHY THIS FILE EXISTS
---------------------
Phase B's channel-attribution result (RESULTS_OF_RECORD.md SS7) has a single
authoritative numeric output: `attribution_pernode_profile.csv`, produced by
attribution_gae_pernode.py (primary method = per-node GAE reconstruction
error). It contains, for every (subject, channel) pair:
    subject, ch_index, channel, region, hemisphere, mean_abs_z, sd_abs_z
This script visualizes exactly THAT file -- no numbers are recomputed,
re-estimated, or invented. `attribution_pernode_summary.csv` (top-5 dominant
channels, lateralization index, consistency/specificity/faithfulness flags)
is used only for annotation (bordering the top-k cells, printing LI in the
montage titles), never as a data source for color/magnitude.

TWO COMPLEMENTARY VIEWS (use whichever communicates better in the thesis;
both are the same data, just laid out differently)
-------------------------------------------------------------------------
1. fig_channel_heatmap.{png,pdf}
   Subjects (rows) x 18 channels (columns), columns grouped by anatomical
   region (L-temporal | L-central | R-central | R-temporal | Midline) with
   divider lines, colored by mean_abs_z. Top-5 attributed channels per
   subject (from the summary CSV, if provided) get a black border. This is
   the clearest view for comparing magnitude ACROSS subjects at a glance.

2. fig_channel_montage.{png,pdf}
   One bipolar double-banana montage schematic PER SUBJECT (small multiple
   grid), each channel drawn as a colored segment positioned in its real
   montage chain (L-temporal / L-central / midline / R-central / R-temporal,
   anterior-to-posterior top-to-bottom) -- this is the "channel layout
   diagram" version, closer to how a clinical EEG montage is actually read.
   Segment color = mean_abs_z; title annotates n_seizures, consistency/
   specificity/faithfulness pass-fail, and lateralization index if the
   summary CSV is supplied.

CHANNEL / REGION CONVENTION (must match attribution_gae_pernode.py exactly)
----------------------------------------------------------------------------
  0-3   L-temporal   FP1-F7, F7-T7, T7-P7, P7-O1
  4-7   L-central    FP1-F3, F3-C3, C3-P3, P3-O1
  8-11  R-central    FP2-F4, F4-C4, C4-P4, P4-O2
  12-15 R-temporal   FP2-F8, F8-T8, T8-P8, P8-O2
  16-17 Midline      FZ-CZ, CZ-PZ

USAGE
-----
  python visualize_channel_attribution.py \
      --profile_csv results/phaseB/attribution_pernode_profile.csv \
      --summary_csv results/phaseB/attribution_pernode_summary.csv \
      --out_dir results/phaseB/figures

If --summary_csv is omitted, the heatmap/montage are still produced, just
without the top-k border / pass-fail annotations.

Requires: pandas, numpy, matplotlib. No GPU, no cached scores -- pure
visualization of an already-computed CSV.
================================================================================
"""

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

CH_NAMES = ["FP1-F7", "F7-T7", "T7-P7", "P7-O1", "FP1-F3", "F3-C3", "C3-P3", "P3-O1",
            "FP2-F4", "F4-C4", "C4-P4", "P4-O2", "FP2-F8", "F8-T8", "T8-P8", "P8-O2",
            "FZ-CZ", "CZ-PZ"]
REGION = (["L-temp"] * 4 + ["L-cent"] * 4 + ["R-cent"] * 4 + ["R-temp"] * 4 + ["Mid"] * 2)
HEMI = (["L"] * 8 + ["R"] * 8 + ["M"] * 2)
REGION_ORDER = ["L-temp", "L-cent", "Mid", "R-cent", "R-temp"]
CHAIN_X = {"L-temp": -1.5, "L-cent": -0.5, "Mid": 0.0, "R-cent": 0.5, "R-temp": 1.5}

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.titlesize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 130,
})


# ============================================================================
# Loading + validation
# ============================================================================
def load_profile(path):
    df = pd.read_csv(path)
    required = {"subject", "ch_index", "channel", "region", "hemisphere",
               "mean_abs_z", "sd_abs_z"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"attribution_pernode_profile.csv is missing columns: "
                        f"{missing}. This script only visualizes the exact "
                        f"authoritative schema written by "
                        f"attribution_gae_pernode.py.")
    return df


def load_summary(path):
    if path is None:
        return None
    df = pd.read_csv(path)
    if "dominant_channels" not in df.columns:
        print(f"  [warn] {path} has no 'dominant_channels' column -- "
              f"top-k borders/annotations will be skipped.")
        return None
    return df.set_index("subject")


def top5_set(summary_row):
    if summary_row is None:
        return set()
    names = [c.strip() for c in str(summary_row["dominant_channels"]).split(",")]
    return set(names)


# ============================================================================
# Panel 1 -- subject x channel heatmap
# ============================================================================
def plot_heatmap(profile_df, summary_df, out_dir):
    subjects = sorted(profile_df["subject"].unique())
    # channel order: fixed anatomical order (matches CH_NAMES / REGION exactly)
    ch_order = CH_NAMES
    mat = np.full((len(subjects), len(ch_order)), np.nan)
    for si, subj in enumerate(subjects):
        sub = profile_df[profile_df.subject == subj].set_index("channel")
        for ci, ch in enumerate(ch_order):
            if ch in sub.index:
                mat[si, ci] = sub.loc[ch, "mean_abs_z"]

    fig, ax = plt.subplots(figsize=(12, 0.55 * len(subjects) + 1.8))
    im = ax.imshow(mat, aspect="auto", cmap="magma")
    ax.set_xticks(range(len(ch_order)))
    ax.set_xticklabels(ch_order, rotation=90, fontsize=8)
    ax.set_yticks(range(len(subjects)))
    ax.set_yticklabels(subjects, fontsize=10)

    # region divider lines + region labels on top
    boundaries = []
    pos = 0
    for reg in REGION_ORDER:
        n = REGION.count(reg)
        boundaries.append((pos, pos + n, reg))
        pos += n
    for (s, e, reg) in boundaries:
        if s > 0:
            ax.axvline(s - 0.5, color="white", lw=1.4)
        ax.text((s + e - 1) / 2, -1.05, reg, ha="center", va="bottom",
               fontsize=9, fontweight="bold", transform=ax.transData)

    # border top-5 attributed channels per subject
    if summary_df is not None:
        for si, subj in enumerate(subjects):
            if subj not in summary_df.index:
                continue
            top5 = top5_set(summary_df.loc[subj])
            for ci, ch in enumerate(ch_order):
                if ch in top5:
                    ax.add_patch(Rectangle((ci - 0.5, si - 0.5), 1, 1,
                                          fill=False, edgecolor="cyan", lw=1.8))

    cbar = plt.colorbar(im, ax=ax, fraction=0.025, pad=0.01)
    cbar.set_label("mean |z| (per-node GAE reconstruction error)", fontsize=9)
    ax.set_title("Channel attribution -- per-node GAE reconstruction error "
                "(cyan border = top-5 attributed channel for that subject)",
                fontsize=11, pad=28)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(Path(out_dir) / f"fig_channel_heatmap.{ext}", bbox_inches="tight")
    plt.close(fig)


# ============================================================================
# Panel 2 -- per-subject bipolar montage schematic
# ============================================================================
def montage_positions():
    """Returns {channel_name: (x, y_top, y_bottom)} for the double-banana
    montage layout: 5 chains side by side, anterior (y=0) at top, each
    segment one unit tall, ordered exactly as CH_NAMES/REGION define."""
    pos = {}
    chain_counter = {r: 0 for r in REGION_ORDER}
    for ch, reg in zip(CH_NAMES, REGION):
        i = chain_counter[reg]
        x = CHAIN_X[reg]
        pos[ch] = (x, -i, -(i + 1))
        chain_counter[reg] += 1
    return pos


def plot_one_montage(ax, subj, sub_profile, summary_row, vmin, vmax, cmap):
    pos = montage_positions()
    top5 = top5_set(summary_row)
    for ch in CH_NAMES:
        row = sub_profile[sub_profile.channel == ch]
        val = float(row["mean_abs_z"].iloc[0]) if len(row) else np.nan
        x, yt, yb = pos[ch]
        color = cmap((val - vmin) / (vmax - vmin)) if np.isfinite(val) else "#dddddd"
        lw = 10
        ax.plot([x, x], [yt, yb], color=color, lw=lw, solid_capstyle="butt",
               zorder=2)
        if ch in top5:
            ax.plot([x, x], [yt, yb], color="none", lw=lw + 3,
                   solid_capstyle="butt", zorder=1,
                   path_effects=None)
            ax.plot([x, x], [yt, yb], lw=lw + 4, color="cyan", zorder=1,
                   solid_capstyle="butt", alpha=0.9)
            ax.plot([x, x], [yt, yb], color=color, lw=lw, solid_capstyle="butt",
                   zorder=2)
        ax.text(x + 0.18, (yt + yb) / 2, ch, fontsize=5.5, va="center", ha="left")

    ax.set_xlim(-2.3, 2.6)
    ax.set_ylim(-4.4, 0.6)
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    title = subj
    if summary_row is not None:
        li = summary_row.get("lateralization_index", None)
        pc = summary_row.get("p_consistency", None)
        ps = summary_row.get("p_seizure_specific", None)
        po = summary_row.get("p_occlusion", None)
        flags = "".join([
            "C" if (pc is not None and pc < 0.05) else "-",
            "S" if (ps is not None and ps < 0.05) else "-",
            "F" if (po is not None and po < 0.05) else "-",
        ])
        li_txt = f"LI={li:+.2f}" if li is not None and pd.notna(li) else ""
        title = f"{subj}  [{flags}]  {li_txt}"
    ax.set_title(title, fontsize=9)


def plot_montage_grid(profile_df, summary_df, out_dir):
    subjects = sorted(profile_df["subject"].unique())
    vmin = profile_df["mean_abs_z"].min()
    vmax = profile_df["mean_abs_z"].max()
    cmap = plt.get_cmap("magma")

    ncol = 4
    nrow = int(np.ceil(len(subjects) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(4.2 * ncol, 4.0 * nrow))
    axes = np.atleast_2d(axes)
    for idx, subj in enumerate(subjects):
        ax = axes[idx // ncol][idx % ncol]
        sub_profile = profile_df[profile_df.subject == subj]
        summary_row = (summary_df.loc[subj] if (summary_df is not None and
                                                subj in summary_df.index) else None)
        plot_one_montage(ax, subj, sub_profile, summary_row, vmin, vmax, cmap)
    for idx in range(len(subjects), nrow * ncol):
        axes[idx // ncol][idx % ncol].axis("off")

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
    cbar = fig.colorbar(sm, ax=axes, fraction=0.02, pad=0.02, shrink=0.6)
    cbar.set_label("mean |z|", fontsize=9)

    fig.suptitle("Channel attribution -- bipolar double-banana montage schematic\n"
                "(L-temporal | L-central | Midline | R-central | R-temporal; "
                "cyan outline = top-5 attributed; [C/S/F] = pass consistency/"
                "specificity/faithfulness)", fontsize=10, y=1.02)
    for ext in ("png", "pdf"):
        fig.savefig(Path(out_dir) / f"fig_channel_montage.{ext}", bbox_inches="tight")
    plt.close(fig)


# ============================================================================
# Orchestration
# ============================================================================
def main():
    ap = argparse.ArgumentParser(description="Visualize channel attribution "
                                             "(attribution_pernode_profile.csv)")
    ap.add_argument("--profile_csv", required=True,
                    help="attribution_pernode_profile.csv (authoritative, required)")
    ap.add_argument("--summary_csv", default=None,
                    help="attribution_pernode_summary.csv (optional, for top-5/"
                        "LI/pass-fail annotation only)")
    ap.add_argument("--out_dir", default="results/phaseB/figures")
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    profile_df = load_profile(args.profile_csv)
    summary_df = load_summary(args.summary_csv)

    n_subj = profile_df["subject"].nunique()
    n_ch = profile_df.groupby("subject")["channel"].nunique()
    print(f"Loaded {args.profile_csv}: {n_subj} subjects, "
         f"channels/subject = {sorted(n_ch.unique())}")
    if summary_df is not None:
        print(f"Loaded {args.summary_csv}: {len(summary_df)} subjects "
             f"(used for top-5 border + LI + pass/fail annotation only)")

    plot_heatmap(profile_df, summary_df, out)
    plot_montage_grid(profile_df, summary_df, out)

    print(f"\nWrote to: {out.resolve()}")
    print("  fig_channel_heatmap.{png,pdf}  -- subject x 18-channel matrix, grouped by region")
    print("  fig_channel_montage.{png,pdf}  -- per-subject bipolar montage schematic")


if __name__ == "__main__":
    main()