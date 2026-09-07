"""
================================================================================
 plot_latency.py -- Fig 3.5 detection latency
================================================================================
Histogram of matched-seizure detection latency at the headline operating point.
Source: results/phaseB/tier2/latency/latency_per_seizure.csv, rows where
operating_point == 'val_derived_balanced' and matched == True.

Vertical lines at -30 s and +60 s mark the latency matcher's tolerance window.
The distribution is truncated exactly at -28 s because of that tolerance (4 s
window quantisation on top of the 30 s allowance) -- this is what the figure is
for: showing the negative values come from the matching rule, not detection
before onset (docs/VERIFIED_NUMBERS.md Part 8, item 1).
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
from palette import DETECTED, CHANCE, apply_rc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="results/phaseB/tier2/latency/latency_per_seizure.csv")
    ap.add_argument("--out_dir", default="figures/event_level")
    a = ap.parse_args()

    apply_rc()
    df = pd.read_csv(a.csv)
    d = df[(df.operating_point == "val_derived_balanced") & (df.matched == True)]

    n = len(d)
    lat = d["latency_s"].values
    med = np.median(lat)
    n_neg = int((lat < 0).sum())
    print(f"[Fig 3.5] n={n} (brief: 48), median={med:.1f}s (brief: -4s), "
         f"negative={n_neg}/{n} (brief: 25/48), min={lat.min():.1f}s (brief: truncated at -28s)")
    if n != 48:
        raise ValueError(f"n={n}, expected 48 -- stop, wrong filter or file")
    if med != -4.0:
        raise ValueError(f"median={med}, expected -4 -- stop")
    if n_neg != 25:
        raise ValueError(f"negative count={n_neg}, expected 25 -- stop")
    if lat.min() != -28.0:
        raise ValueError(f"min={lat.min()}, expected exactly -28 -- stop")

    fig, ax = plt.subplots(figsize=(8, 5.2))
    bin_width = 4  # matches the 4 s window quantisation
    bins = np.arange(lat.min() - bin_width / 2, lat.max() + bin_width, bin_width)
    ax.hist(lat, bins=bins, color=DETECTED, edgecolor="black", linewidth=0.5, alpha=0.85)

    ax.axvline(-30, color=CHANCE, ls="--", lw=1.3, label="-30 s before onset (matching tolerance)")
    ax.axvline(60, color=CHANCE, ls=":", lw=1.3, label="+60 s after seizure end (matching tolerance)")
    ax.axvline(med, color="black", ls="-", lw=1.3, label=f"median = {med:.0f} s")

    ax.set_xlabel("Latency of detected interval relative to annotated onset (s)")
    ax.set_ylabel("Matched seizures")
    ax.set_title(f"Fig 3.5 — detection latency, headline operating point (m50/p2.0)\n"
                f"n={n} matched of 76 seizures; truncated at {lat.min():.0f} s by the -30 s "
                f"tolerance and 4 s window quantisation")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(axis="y", alpha=0.25, lw=0.5)

    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(out_dir / f"fig3_5_detection_latency.{ext}", bbox_inches="tight")
    plt.close(fig)
    print(f"  [saved] {(out_dir / 'fig3_5_detection_latency.png').resolve()}")


if __name__ == "__main__":
    main()
