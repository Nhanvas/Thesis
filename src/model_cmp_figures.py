#!/usr/bin/env python
"""
model_cmp_figures.py -- the two figures of the model comparison rev 2, drawn only from committed results
(results/model_cmp/). No number is computed here that is not in those files.
  fig_model_cmp_curves.png   per-case mean sensitivity vs per-case mean FP/day, detector stage, common budget grid
                             (analysis C); colour only, no markers (author 04/11); also saved as .pdf
  fig_model_cmp_seizures.png the 185 annotated seizures split by who catches them: both / GAE only / model only /
                             neither (analysis D), one bar per compared model
Palette: validated categorical slots (dataviz reference palette, light mode); direct labels on every line.
  python src/model_cmp_figures.py [--res results/model_cmp] [--out results/model_cmp/figures]
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402
import pandas as pd               # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ORDER = ["gae", "mlp", "if", "svm", "hgb", "cnn"]
NAME = {"gae": "GAE (label-free)", "if": "Isolation Forest (label-free)", "svm": "Linear SVM (labels)",
        "hgb": "Gradient-boosted trees (labels)", "cnn": "1-D CNN (labels)"}
COL = {"gae": "#2a78d6", "if": "#eb6834", "svm": "#1baf7a", "hgb": "#eda100", "cnn": "#e87ba4"}
MARK = {"gae": "o", "if": "s", "svm": "^", "hgb": "D", "cnn": "v"}
INK, INK2, GRID, SURF = "#1f1f1e", "#5f5e5a", "#e6e5e0", "#fcfcfb"


def style(ax):
    ax.set_facecolor(SURF)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=9)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def curves(res, out):
    """classic journal style: white background, full frame, colour only (no markers), one legend."""
    c = pd.read_csv(res / "curves_mean.csv")
    colors = {"gae": "#1f1f1f", "mlp": "#9467bd", "if": "#1f77b4", "svm": "#2ca02c", "hgb": "#ff7f0e", "cnn": "#d62728"}
    names = {"gae": "GAE (label-free)", "mlp": "MLP autoencoder (label-free)", "if": "Isolation Forest (label-free)", "svm": "Linear SVM (supervised)",
             "hgb": "Gradient-boosted trees (supervised)", "cnn": "1-D CNN (supervised)"}
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 10, "axes.linewidth": 0.8}):
        fig, ax = plt.subplots(figsize=(7.0, 4.2), facecolor="white")
        for m in [m for m in ORDER if m in set(c.model)]:
            d = c[(c.model == m) & (c.fp_day <= 60)].sort_values("fp_day")
            ax.plot(d.fp_day, d.sens, color=colors[m], lw=2.2 if m == "gae" else 1.6, label=names[m],
                    zorder=3 if m == "gae" else 2)
        ax.set_xlim(0, 60)
        ax.set_ylim(0, 1)
        ax.set_xlabel("False alarms per day")
        ax.set_ylabel("Sensitivity")
        ax.tick_params(direction="in", top=True, right=True, length=4)
        ax.legend(loc="lower right", frameon=True, fancybox=False, edgecolor="#bbbbbb", fontsize=9)
        fig.tight_layout()
        fig.savefig(out / "fig_model_cmp_curves.png", dpi=300, facecolor="white")
        fig.savefig(out / "fig_model_cmp_curves.pdf", facecolor="white")
        plt.close(fig)


def seizures(res, out):
    d = pd.read_csv(res / "complementarity.csv")
    groups = [("both", "Both catch", "#9e9d97"), ("gae_only", "GAE only", COL["gae"]),
              ("model_only", "Other model only", "#eb6834"), ("neither", "Both miss", "#d6d5cf")]
    models = [m for m in ORDER if m != "gae"]
    fig, ax = plt.subplots(figsize=(7.2, 3.0), facecolor=SURF)
    style(ax)
    ax.grid(False)
    for i, m in enumerate(models):
        left = 0
        for g, lab, col in groups:
            n = int(d[(d.model == m) & (d.group == g)].n.iloc[0])
            ax.barh(i, n, left=left, color=col, edgecolor=SURF, linewidth=2, height=0.62)
            if n >= 8:
                ax.text(left + n / 2, i, str(n), ha="center", va="center", fontsize=8.5,
                        color=SURF if g in ("gae_only", "model_only") else INK)
            left += n
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels([f"GAE vs {NAME[m]}" for m in models], fontsize=9, color=INK)
    ax.invert_yaxis()
    ax.set_xlabel("Annotated seizures (185, 24 cases)", color=INK, fontsize=10)
    from matplotlib.patches import Patch
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.legend(handles=[Patch(color=col, label=lab) for g, lab, col in groups], ncol=4, fontsize=8.5,
               frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.0), labelcolor=INK)
    fig.savefig(out / "fig_model_cmp_seizures.png", dpi=200, facecolor=SURF)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", default=str(ROOT / "results" / "model_cmp"))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    res = Path(a.res)
    out = Path(a.out) if a.out else res / "figures"
    out.mkdir(parents=True, exist_ok=True)
    curves(res, out)
    # seizures(res, out)   # not used on slides (author 04/11); kept for reference
    print("wrote", sorted(p.name for p in out.glob("*.png")))


if __name__ == "__main__":
    main()
