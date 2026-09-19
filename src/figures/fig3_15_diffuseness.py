"""
fig3_15_diffuseness.py -- writes Figure 3.10 (figures/fig3_10_diffuseness.png).

Revised 2026-09-18 under docs/ATTRIBUTION_SPEC.md v4, Amendment A4.6: the figure is now
SYNTHETIC ONLY. The real-annotation strips (focal vs diffuse) belonged to the retired
machine-generated draft annotation and are removed. The diffuseness ("spread", normalised
entropy of the 18-channel score vector) is shown against the number of injected channels on the
synthetic grid, for the validation and test panels at alpha = 2.0. It is U-shaped in the number of
injected channels, so it cannot separate focal from generalized seizures; it is reported as a
methodological negative and never used to classify.

Source (label-free, final): results/attribution_v6/synthetic_spread.csv
  columns panel, alpha, n_injected, spread_mean, spread_sd; grid |S| in {1, 2, 4, 12, 18}
  (the spread experiment's own grid, different from the discrimination grid {1,2,4,8,12}).

Self-check: the validation curve must equal the values quoted in ATTRIBUTION_SPEC v4 §9.4 and
RESULTS_OF_RECORD_phaseB §10.1 (0.9644, 0.9567, 0.9441, 0.9503, 0.9755). The script stops rather
than draw a value it cannot confirm. It reads the CSV only and recomputes nothing.
"""
import os as _os, sys as _sys
from pathlib import Path
_here = _os.path.dirname(_os.path.abspath(__file__))
_src = _os.path.dirname(_here)
for _p in (_here, _src):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from palette import INTERICTAL, ICTAL, apply_rc

ROOT = Path(_src).parent
SYNTH_CSV = ROOT / "results" / "attribution_v6" / "synthetic_spread.csv"
OUT = ROOT / "figures" / "fig3_10_diffuseness.png"

EXPECTED_VAL = {1: 0.9644, 2: 0.9567, 4: 0.9441, 12: 0.9503, 18: 0.9755}
ALPHA = 2.0


def main():
    apply_rc()
    if not SYNTH_CSV.is_file():
        raise SystemExit(f"Fig 3.10: missing {SYNTH_CSV} -- stop")
    df = pd.read_csv(SYNTH_CSV)
    df = df[np.isclose(df.alpha, ALPHA)]
    panels = {}
    for p in ("VAL", "TEST"):
        d = df[df.panel == p].sort_values("n_injected")
        if d.empty:
            raise SystemExit(f"Fig 3.10: no {p} rows at alpha={ALPHA} -- stop")
        panels[p] = d

    got = {int(k): round(float(v), 4) for k, v in zip(panels["VAL"].n_injected, panels["VAL"].spread_mean)}
    print(f"[Fig 3.10] self-check VAL spread: {got}")
    if got != EXPECTED_VAL:
        raise ValueError(f"Fig 3.10 self-check failed: expected {EXPECTED_VAL}, got {got} -- stop")
    k_min = min(got, key=got.get)
    print(f"[Fig 3.10] U-shape: minimum at |S|={k_min} ({got[k_min]}); ends {got[1]} (|S|=1) "
          f"and {got[18]} (|S|=18)")

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    for p, colour, name, off in (("VAL", INTERICTAL, "Validation patients", -0.12),
                                 ("TEST", ICTAL, "Test patients", 0.12)):
        d = panels[p]
        ax.errorbar(d.n_injected + off, d.spread_mean, yerr=d.spread_sd, fmt="-o", color=colour,
                    lw=1.4, ms=5.5, capsize=3, elinewidth=0.9, label=name, zorder=3)
    ticks = sorted(got)
    ax.set_xticks(ticks)
    ax.set_xticklabels([str(t) for t in ticks])
    ax.set_xlabel("Number of injected channels, |S|")
    ax.set_ylabel("Diffuseness (normalised entropy of the 18 scores)")
    ax.legend(fontsize=8.5, frameon=False, loc="upper center")
    ax.grid(alpha=0.25, lw=0.5)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[saved] {OUT.resolve()}")


if __name__ == "__main__":
    main()
