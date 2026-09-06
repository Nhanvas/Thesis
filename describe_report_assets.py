#!/usr/bin/env python
"""
describe_report_assets.py — run this ONCE, paste the FULL output back into chat.

Supersedes check_report_assets.py: in addition to checking existence, this prints
enough structure (columns, dtypes, shape, a few rows) for every source file needed
by FIGURES_TABLES_LIST.md that even the files you do NOT upload directly still give
Claude enough context to write a correct plotting script against them.

READ-ONLY. Nothing is modified, nothing is uploaded by this script itself — you paste
the printed text back manually, and separately upload whichever files are small enough
(CSV / PNG / short .py) directly into the chat.

USAGE (from repo root, F:/Study/Thesis/Code)
    python describe_report_assets.py
    python describe_report_assets.py --subj chb03      # try a different running-example candidate
    python describe_report_assets.py --subj chb13
"""
import argparse
from pathlib import Path

try:
    import numpy as np
except ImportError:
    np = None
try:
    import pandas as pd
except ImportError:
    pd = None

# (id, description, [relative paths]); "{subj}" substituted with --subj.
FILES = [
    ("Fig1.2", "connectivity heatmaps (one running-example subject)",
     ["data/processed/{subj}_interictal_adjs_topk20.npy",
      "data/processed/{subj}_ictal_adjs_topk20.npy"]),

    ("Fig2.2 / Table2.3", "seizure blocks (TEST set, durations + counts)",
     ["results/attribution_v6/seizure_blocks.csv"]),

    ("Fig2.3", "raw vs preprocessed EEG (already exists)",
     ["figures/raw_vs_preprocessed.png",
      "src/dataprep/plot_raw_vs_preprocessed.py"]),

    ("Fig2.4 / Fig2.5", "one window -> graph construction, and sparsification",
     ["data/processed/{subj}_interictal.npy",
      "data/processed/{subj}_interictal_features.npy",
      "data/processed/{subj}_interictal_adjs_topk20.npy"]),

    ("Fig2.8", "reconstruction error, inverted vs normal patient",
     ["data/pernode_v2/seed42/chb06_interictal_pernode.npy",
      "data/pernode_v2/seed42/chb06_ictal_pernode.npy",
      "data/pernode_v2/seed42/{subj}_interictal_pernode.npy",
      "data/pernode_v2/seed42/{subj}_ictal_pernode.npy",
      "src/figures/visualize_chb06_inversion.py"]),

    ("Fig2.9", "ensemble weight-sweep grid (PREREG_03)",
     ["results/retrain/prereg03/derive_weights_grid.csv",
      "results/retrain/derive_weights_grid.csv",
      "results/phaseB/prereg03/derive_weights_grid.csv"]),

    ("Fig3.1 dependency", "Frobenius separation before/after sparsification (DM1)",
     ["results/history_topology/topo_features",
      "results/dm1_frobenius.csv"]),

    ("Table3.2 / Fig3.8", "window-level per-subject results (TEST)",
     ["results/phaseB/tier2/rlg_test/final_eval_seed42.csv"]),

    ("Fig3.2 / Fig3.3", "window-level distributions, ROC, PR (already exist)",
     ["figures/window_level/W1_roc_curves.png",
      "figures/window_level/W2_pr_curves.png",
      "figures/window_level/W3_score_distribution.png"]),

    ("Fig3.6 / Fig3.7", "event-level operating curve + per-subject (already exist)",
     ["figures/event_level/E1_operating_curve.png",
      "figures/event_level/E2_persubject_breakdown.png",
      "src/figures/plot_event_level.py"]),

    ("Fig3.5", "detection latency per matched seizure",
     ["results/phaseB/tier2/rlg_test/",   # directory listing only
      ]),

    ("Fig3.11 / Table3.8", "synthetic attribution validation grid",
     ["results/attribution_v6/synthetic_sanity.csv"]),

    ("Fig3.12 / Fig3.13", "attribution scores, all seeds (already have figures, need data)",
     ["results/attribution_v6/attribution_scores.csv"]),

    ("Table3.9 / Fig3.14", "attribution vs reference annotation",
     ["results/attribution_v6/attribution_summary.csv",
      "results/attribution_v6/attribution_perseizure.csv"]),

    ("Table3.10", "within-patient annotation similarity",
     ["results/attribution_v6/label_diversity.csv"]),

    ("Fig3.15", "diffuseness (spread) vs |S|",
     ["results/attribution_v6/synthetic_spread.csv"]),

    ("Table A.2", "channel annotation per seizure (PROVISIONAL)",
     ["results/attribution_v6/labels/ictal_channels_DRAFT.csv"]),

    ("Table A.4", "top-1 concentration vs random null",
     ["results/attribution_v6/attribution_diagnostics.csv"]),

    ("Table A.7", "top-3 channels per seizure (already exists)",
     ["figures/attribution/attribution_top3_channels.csv"]),

    ("running example (Fig2.10/3.4/3.10)", "raw EDF root + gamma-AEC script "
     "(needed for the regeneration script, next step)",
     ["src/dataprep/compute_gamma_aec.py"]),
]


def describe_csv(p):
    if pd is None:
        print("    (pandas not installed here; just confirming existence)")
        return
    try:
        df = pd.read_csv(p)
        print(f"    shape={df.shape}  columns={list(df.columns)}")
        print(f"    head:\n{df.head(3).to_string(max_colwidth=20)}")
    except Exception as e:
        print(f"    [could not read as CSV: {e}]")


def describe_npy(p):
    if np is None:
        print("    (numpy not installed here; just confirming existence)")
        return
    try:
        a = np.load(p, mmap_mode="r")
        print(f"    shape={a.shape}  dtype={a.dtype}  "
              f"min={float(a.min()):.4g}  max={float(a.max()):.4g}")
    except Exception as e:
        print(f"    [could not read as .npy: {e}]")


def describe_png(p):
    try:
        from PIL import Image
        im = Image.open(p)
        print(f"    image size={im.size}  mode={im.mode}")
    except Exception:
        print(f"    size on disk = {Path(p).stat().st_size} bytes (PIL not available to open it)")


def describe_py(p):
    lines = Path(p).read_text(errors="ignore").splitlines()
    print(f"    {len(lines)} lines. First 15:")
    for l in lines[:15]:
        print(f"      {l}")


def describe_dir(p):
    items = sorted(Path(p).iterdir())[:30]
    print(f"    {len(items)} item(s) shown (first 30):")
    for it in items:
        print(f"      {it.name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--subj", default="chb03")
    a = ap.parse_args()
    root = Path(a.root)

    print(f"Repo root: {root.resolve()}   subj={a.subj}\n")
    for fig_id, desc, paths in FILES:
        print(f"### {fig_id} — {desc}")
        for rel in paths:
            rel_sub = rel.replace("{subj}", a.subj)
            p = root / rel_sub
            if not p.exists():
                print(f"  MISSING: {p}")
                continue
            print(f"  FOUND: {p}")
            if p.is_dir():
                describe_dir(p)
            elif p.suffix == ".csv":
                describe_csv(p)
            elif p.suffix == ".npy":
                describe_npy(p)
            elif p.suffix == ".png":
                describe_png(p)
            elif p.suffix == ".py":
                describe_py(p)
        print()


if __name__ == "__main__":
    main()
