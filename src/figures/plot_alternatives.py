"""
================================================================================
 plot_alternatives.py -- Fig 3.9 effect of each design alternative
================================================================================
Horizontal dot plot of the difference in event-level F1 vs the incumbent (final)
system, from results/phaseB/tier2/alternatives/alternatives_vs_incumbent.csv.
Shades the band [-0.034, +0.034] around zero -- the spread across four
independently trained models (docs/VERIFIED_NUMBERS.md §6.4, SD of F1 = 0.0345,
rounded to 0.034 in the results of record) -- every variant inside it is a tie,
not a result.

Only the design-alternative rows are plotted (the "initialisation N" rows are
the seed-spread check from §6.4, a different comparison, and are excluded here).
Six alternatives were actually measured; a seventh (per-channel time-domain
features) was never built and is absent from the source file by construction
(docs/VERIFIED_NUMBERS.md §6.6).
"""
import argparse
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
from palette import apply_rc


def round3(x):
    """Round to 3 decimals the way the committed 4-decimal CSV values were meant
    to be read (half-up on the decimal value), not Python's round() on the binary
    float -- 0.0115 is stored as 0.011499999... in binary and round() gives 0.011,
    but the intended value rounds to 0.012."""
    return float(Decimal(str(x)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP))

BAND = 0.034
DESIGN_VARIANTS = [
    "drop reconstruction readout",
    "drop latent readout",
    "directed connectivity, score level",
    "alternative smoothing, median 9",
    "alternative smoothing, median 15",
    "onset-slope change-point filtering",
    "artifact gate, isolated spikes",
    "artifact gate, per-window",
]
LABELS = {
    "drop reconstruction readout": "Remove reconstruction readout",
    "drop latent readout": "Remove latent readout",
    "directed connectivity, score level": "Directed connectivity, score level",
    "alternative smoothing, median 9": "Alternative smoothing, median 9",
    "alternative smoothing, median 15": "Alternative smoothing, median 15",
    "onset-slope change-point filtering": "Onset-slope change-point filtering",
    "artifact gate, isolated spikes": "Artifact gate, isolated spikes only",
    "artifact gate, per-window": "Artifact gate, every window (undefined F1)",
}
EXPECTED_DELTA = {
    "drop reconstruction readout": 0.012, "drop latent readout": -0.103,
    "directed connectivity, score level": -0.034, "alternative smoothing, median 9": -0.123,
    "alternative smoothing, median 15": -0.078, "onset-slope change-point filtering": -0.010,
    "artifact gate, isolated spikes": 0.002,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="results/phaseB/tier2/alternatives/alternatives_vs_incumbent.csv")
    ap.add_argument("--out_dir", default="figures/alternatives")
    a = ap.parse_args()

    apply_rc()
    df = pd.read_csv(a.csv).set_index("variant")
    d = df.loc[DESIGN_VARIANTS]

    print(f"[Fig 3.9] delta F1 vs incumbent (band = +/-{BAND}):")
    for v in DESIGN_VARIANTS:
        delta = d.loc[v, "delta_f1_vs_incumbent"]
        if v == "artifact gate, per-window":
            print(f"  {v}: F1 undefined (no detections) -- excluded from the dot plot")
            continue
        print(f"  {v}: delta_f1={delta:+.3f}  {'(tie, inside band)' if abs(delta) <= BAND else '(outside band)'}")
        if round3(delta) != EXPECTED_DELTA[v]:
            raise ValueError(f"{v}: delta_f1 {delta} != brief {EXPECTED_DELTA[v]} -- stop")

    plot_rows = [v for v in DESIGN_VARIANTS if v != "artifact gate, per-window"]
    deltas = [d.loc[v, "delta_f1_vs_incumbent"] for v in plot_rows]
    labels = [LABELS[v] for v in plot_rows]
    order = np.argsort(deltas)
    plot_rows = [plot_rows[i] for i in order]
    deltas = [deltas[i] for i in order]
    labels = [labels[i] for i in order]
    inside = [abs(dv) <= BAND for dv in deltas]

    y = np.arange(len(plot_rows))
    fig, ax = plt.subplots(figsize=(8.5, 5.2))

    ax.axvspan(-BAND, BAND, color="#cccccc", alpha=0.4, zorder=0,
              label=f"tie band (+/-{BAND}, spread across 4 seeds)")
    ax.axvline(0, color="black", lw=0.8, zorder=1)

    colors = ["#8c8c8c" if ins else "#c0392b" for ins in inside]
    ax.hlines(y, 0, deltas, color=colors, lw=1.6, zorder=2)
    ax.scatter(deltas, y, color=colors, s=70, zorder=3, edgecolor="black", linewidth=0.5)

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_ylim(-0.8, len(plot_rows) - 0.2)
    ax.set_xlabel("Change in event-level F1 vs final system (validation, 3 subjects, 13 seizures)")
    ax.set_title("Fig 3.9 — effect of each design alternative on event-level F1", fontsize=11)
    ax.grid(axis="x", alpha=0.25, lw=0.5)
    ax.legend(loc="upper left", fontsize=8)
    fig.text(0.5, -0.02,
             "Not plotted: artifact gate, every window — 0 detections, F1 undefined "
             "(suppresses nearly all ictal windows).",
             ha="center", fontsize=8, color="#555555")

    fig.tight_layout()
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(out_dir / f"fig3_9_alternatives_effect.{ext}", bbox_inches="tight")
    plt.close(fig)
    print(f"  [saved] {(out_dir / 'fig3_9_alternatives_effect.png').resolve()}")


if __name__ == "__main__":
    main()
