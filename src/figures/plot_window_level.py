"""
================================================================================
 plot_window_level.py -- Fig 3.2 (score distributions) + Fig 3.3 (ROC / PR)
================================================================================
Rebuilds the two window-tier figures from the final system's committed ensemble
score arrays (`results/phaseB/tier2/ens_test_tf/rlg/`), replacing the earlier
configuration's W1/W2/W3. See docs/FIGURE_REBUILD_BRIEF.md.

Fig 3.2 -- fused score distributions per patient: interictal vs ictal, one panel
per patient (violin), eight panels.

Fig 3.3 -- per-patient ROC (left) and precision-recall (right) curves. One curve
per patient, no pooled curve and no macro-mean curve (the earlier figure drew a
pooled curve; the spec forbids it here). Each curve's AUROC is checked against
`window_auroc_seed42.json` to four decimals before the figure is accepted.

No confidence intervals, one shared palette (src/figures/palette.py).
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve, roc_auc_score, precision_recall_curve, average_precision_score

import sys
sys.path.insert(0, str(Path(__file__).parent))
from palette import INTERICTAL, ICTAL, CHANCE, apply_rc

import matplotlib.pyplot as plt

SUBJECTS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]

# Window counts stated in the brief, for a hard check against the loaded arrays.
EXPECTED_COUNTS = {
    "chb03": (17204, 106), "chb06": (19826, 45), "chb13": (12452, 144),
    "chb14": (13983, 49), "chb15": (17026, 515), "chb16": (6428, 28),
    "chb17": (9304, 74), "chb18": (14853, 83),
}


def load_scores(score_dir):
    data = {}
    for s in SUBJECTS:
        inter = np.load(Path(score_dir) / f"ens_seed42_{s}_inter.npy")
        ictal = np.load(Path(score_dir) / f"ens_seed42_{s}_ictal.npy")
        exp_inter, exp_ictal = EXPECTED_COUNTS[s]
        if len(inter) != exp_inter or len(ictal) != exp_ictal:
            raise ValueError(
                f"{s}: loaded {len(inter)}/{len(ictal)} windows, brief states "
                f"{exp_inter}/{exp_ictal} -- wrong arrays are being read")
        data[s] = (inter, ictal)
    return data


# ============================================================================
# Fig 3.2 -- fused score distributions per patient
# ============================================================================
def plot_fig3_2(data, out_dir):
    fig, axes = plt.subplots(2, 4, figsize=(15, 7), sharey=False)
    for ax, s in zip(axes.flat, SUBJECTS):
        inter, ictal = data[s]
        parts = ax.violinplot([inter, ictal], showmedians=True, widths=0.8)
        for pc, color in zip(parts["bodies"], [INTERICTAL, ICTAL]):
            pc.set_facecolor(color)
            pc.set_alpha(0.65)
            pc.set_edgecolor("black")
            pc.set_linewidth(0.6)
        for key in ("cbars", "cmins", "cmaxes", "cmedians"):
            parts[key].set_color("black")
            parts[key].set_linewidth(0.8)
        ax.set_xticks([1, 2])
        ax.set_xticklabels([f"interictal\n(n={len(inter)})", f"ictal\n(n={len(ictal)})"], fontsize=8)
        ax.set_title(s, fontsize=10)
        ax.grid(axis="y", alpha=0.25, lw=0.5)
    fig.suptitle("Fig 3.2 — fused ensemble score distributions per patient, held-out set "
                 "(seed 42, final system)", fontsize=11, y=1.02)
    axes[0, 0].set_ylabel("fused ensemble score")
    axes[1, 0].set_ylabel("fused ensemble score")
    fig.tight_layout()
    _save(fig, out_dir, "fig3_2_score_distributions")


# ============================================================================
# Fig 3.3 -- per-patient ROC + PR curves
# ============================================================================
def plot_fig3_3(data, out_dir, window_auroc_path):
    with open(window_auroc_path) as f:
        expected_auroc = json.load(f)

    cmap = plt.get_cmap("tab10")
    colors = {s: cmap(i) for i, s in enumerate(SUBJECTS)}

    fig, (ax_roc, ax_pr) = plt.subplots(1, 2, figsize=(12.5, 5.6))

    print("\n[Fig 3.3] per-patient discrimination check against window_auroc_seed42.json:")
    computed = {}
    for s in SUBJECTS:
        inter, ictal = data[s]
        y = np.concatenate([np.zeros(len(inter)), np.ones(len(ictal))])
        scores = np.concatenate([inter, ictal])

        auroc = roc_auc_score(y, scores)
        computed[s] = auroc
        exp = expected_auroc[s]
        if round(auroc, 4) != round(exp, 4):
            raise ValueError(
                f"{s}: computed AUROC {auroc:.4f} does not match "
                f"window_auroc_seed42.json value {exp:.4f} to four decimals -- "
                f"stop, the wrong arrays are being read")
        print(f"  {s}: computed={auroc:.4f}  file={exp:.4f}  OK")

        fpr, tpr, _ = roc_curve(y, scores)
        ax_roc.plot(fpr, tpr, color=colors[s], lw=1.4, label=f"{s} (AUROC={auroc:.3f})")

        prec, rec, _ = precision_recall_curve(y, scores)
        auprc = average_precision_score(y, scores)
        ax_pr.plot(rec, prec, color=colors[s], lw=1.4, label=f"{s} (AUPRC={auprc:.3f})")

    macro = np.mean(list(computed.values()))
    print(f"  macro (recomputed) = {macro:.4f}  (docs/VERIFIED_NUMBERS.md: 0.8053, reported 0.805)")
    if round(macro, 3) != 0.805:
        raise ValueError(f"macro AUROC {macro:.4f} does not round to 0.805 -- stop")

    ax_roc.plot([0, 1], [0, 1], "--", color=CHANCE, lw=1.0, label="chance")
    ax_roc.set_xlabel("False positive rate")
    ax_roc.set_ylabel("True positive rate")
    ax_roc.set_title("(a) Receiver-operating curves, per patient")
    ax_roc.legend(fontsize=7, loc="lower right")
    ax_roc.grid(alpha=0.25, lw=0.5)

    for s in SUBJECTS:
        inter, ictal = data[s]
        prevalence = len(ictal) / (len(ictal) + len(inter))
        ax_pr.axhline(prevalence, color=colors[s], lw=0.5, ls=":", alpha=0.5)
    ax_pr.set_xlabel("Recall")
    ax_pr.set_ylabel("Precision")
    ax_pr.set_title("(b) Precision-recall curves, per patient\n"
                    "(dotted lines: each patient's chance level = seizure prevalence)")
    ax_pr.legend(fontsize=7, loc="upper right")
    ax_pr.grid(alpha=0.25, lw=0.5)

    fig.suptitle("Fig 3.3 — per-patient discrimination curves, held-out set "
                "(seed 42, final system) — no pooled or macro-mean curve", fontsize=11, y=1.02)
    fig.tight_layout()
    _save(fig, out_dir, "fig3_3_roc_pr_curves")


def _save(fig, out_dir, name):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"{name}.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  [saved] {(out_dir / (name + '.png')).resolve()}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--score_dir", default="results/phaseB/tier2/ens_test_tf/rlg")
    ap.add_argument("--window_auroc_json",
                    default="results/phaseB/tier2/ens_test_tf/rlg/window_auroc_seed42.json")
    ap.add_argument("--out_dir", default="figures/window_level")
    args = ap.parse_args()

    apply_rc()
    data = load_scores(args.score_dir)
    print("window counts OK for all 8 subjects (matches brief)")

    plot_fig3_2(data, args.out_dir)
    plot_fig3_3(data, args.out_dir, args.window_auroc_json)


if __name__ == "__main__":
    main()
