"""
================================================================================
 plot_separation.py -- Fig 3.1 separation between ictal and interictal connectivity
================================================================================
Bars per patient from results/diagnostics/density_frobenius_v2/separation_per_subject.csv,
plotting the two normalised measures (relative Frobenius change, cosine-distance
change) rather than the raw Frobenius column. The raw column is not comparable
between the fixed-threshold and top-k rules -- the proportional rule removes about
80% of the entries the norm sums over, so it shrinks for arithmetic reasons and
reverses the apparent direction on 6 of 8 subjects. See docs/VERIFIED_NUMBERS.md
Part 4.2.
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

EXPECTED_REL = {
    "chb03": 106.9, "chb06": 97.8, "chb13": 82.3, "chb14": 128.9,
    "chb15": 47.9, "chb16": 75.3, "chb17": 195.9, "chb18": 59.9,
}
EXPECTED_COS = {
    "chb03": 881.1, "chb06": 806.1, "chb13": 800.9, "chb14": 728.5,
    "chb15": 545.3, "chb16": 902.9, "chb17": 870.8, "chb18": 766.9,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="results/diagnostics/density_frobenius_v2/separation_per_subject.csv")
    ap.add_argument("--out_dir", default="figures/graph")
    a = ap.parse_args()

    apply_rc()
    df = pd.read_csv(a.csv).set_index("subject")

    print("[Fig 3.1] normalised separation change, top-k(20%) vs fixed threshold:")
    for s in df.index:
        rel = df.loc[s, "pct_change_rel_topk_vs_fixed"]
        cos = df.loc[s, "pct_change_cos_topk_vs_fixed"]
        print(f"  {s}: rel_frobenius={rel:+.1f}%  cosine={cos:+.1f}%")
        if round(rel, 1) != EXPECTED_REL[s]:
            raise ValueError(f"{s}: rel_frobenius {rel} != brief {EXPECTED_REL[s]} -- stop")
        if round(cos, 1) != EXPECTED_COS[s]:
            raise ValueError(f"{s}: cosine {cos} != brief {EXPECTED_COS[s]} -- stop")

    n_pos_rel = (df["pct_change_rel_topk_vs_fixed"] > 0).sum()
    n_pos_cos = (df["pct_change_cos_topk_vs_fixed"] > 0).sum()
    print(f"  positive on {n_pos_rel}/8 subjects (relative Frobenius), "
         f"{n_pos_cos}/8 (cosine)  (brief: 8/8 for both)")
    if n_pos_rel != 8 or n_pos_cos != 8:
        raise ValueError("expected all 8 subjects positive under both measures -- stop")

    subs = list(df.index)
    x = np.arange(len(subs))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 5))

    ax1.bar(x, df["pct_change_rel_topk_vs_fixed"], color="#1f4e79", edgecolor="black", linewidth=0.5)
    ax1.set_xticks(x); ax1.set_xticklabels(subs)
    ax1.axhline(0, color="black", lw=0.8)
    ax1.set_ylabel("% change, relative Frobenius separation")
    ax1.set_title("(a) Relative Frobenius norm")
    ax1.grid(axis="y", alpha=0.25, lw=0.5)
    for xi, v in zip(x, df["pct_change_rel_topk_vs_fixed"]):
        ax1.text(xi, v + 3, f"+{v:.0f}%", ha="center", va="bottom", fontsize=8)

    ax2.bar(x, df["pct_change_cos_topk_vs_fixed"], color="#762a83", edgecolor="black", linewidth=0.5)
    ax2.set_xticks(x); ax2.set_xticklabels(subs)
    ax2.axhline(0, color="black", lw=0.8)
    ax2.set_ylabel("% change, cosine-distance separation")
    ax2.set_title("(b) Cosine distance")
    ax2.grid(axis="y", alpha=0.25, lw=0.5)
    for xi, v in zip(x, df["pct_change_cos_topk_vs_fixed"]):
        ax2.text(xi, v + 15, f"+{v:.0f}%", ha="center", va="bottom", fontsize=8)

    fig.suptitle("Fig 3.1 — top-k(20%) sparsification increases ictal/interictal separation "
                "on 8 of 8 subjects, both normalised measures\n"
                "(the raw Frobenius column is not shown: it is not comparable between "
                "sparsification rules)", fontsize=10.5, y=1.05)
    fig.tight_layout()

    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / "fig3_1_separation.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  [saved] {(out_dir / 'fig3_1_separation.png').resolve()}")


if __name__ == "__main__":
    main()
