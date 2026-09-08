"""
fig3_15_diffuseness.py -- Fig 3.15, Figure Brief Round 2 Task C.

Diffuseness (the "spread" measure) against the number of annotated
channels: a line for the synthetic case across the injected-channel counts,
and points for the real annotations at their own channel counts.

Sources: results/attribution_v6/synthetic_spread.csv (TEST panel, alpha=2.0
-- the held-out-subject panel, matching the real points below, which are
all held-out subjects) for the line, and
results/attribution_v6/attribution_perseizure.csv (columns n_ictal_ch,
spread) for the real per-seizure points -- this file carries a diffuseness
column ("spread"), so Task C's stop condition ("if that file has no
diffuseness column, stop") does not apply.

Self-check against docs/VERIFIED_NUMBERS.md §7.6: on the real annotations,
focal 0.9693 against generalized 0.9594, one-sided p = 0.984 -- read from
results/attribution_v6/attribution_summary.csv, row "spread focal vs
generalized". The caption states the measure is U-shaped in channel count
for the synthetic injections and runs the wrong way on the real
annotations, so it is reported as a methodological negative and never used
to classify.
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
PERSZ_CSV = ROOT / "results" / "attribution_v6" / "attribution_perseizure.csv"
SUMMARY_CSV = ROOT / "results" / "attribution_v6" / "attribution_summary.csv"
OUT = ROOT / "figures" / "fig3_15_diffuseness.png"

EXPECTED_FOCAL, EXPECTED_GENERALIZED, EXPECTED_P = 0.9693, 0.9594, 0.984


def main():
    apply_rc()

    persz = pd.read_csv(PERSZ_CSV)
    if "spread" not in persz.columns:
        raise SystemExit("Fig 3.15: attribution_perseizure.csv has no diffuseness ('spread') "
                         "column -- stop, per Task C instructions (do not compute the measure "
                         "inside the plotting script).")

    synth = pd.read_csv(SYNTH_CSV)
    test_panel = synth[(synth.panel == "TEST") & (np.isclose(synth.alpha, 2.0))].sort_values("n_injected")
    if test_panel.empty:
        raise SystemExit(f"Fig 3.15: no TEST/alpha=2.0 rows in {SYNTH_CSV} -- stop")

    summ = pd.read_csv(SUMMARY_CSV)
    row = summ[summ.panel == "spread focal vs generalized"]
    if row.empty:
        raise SystemExit(f"Fig 3.15: no 'spread focal vs generalized' row in {SUMMARY_CSV} -- stop")
    # This row repurposes macro_AUROC / AUROC_subject_ctrl / p_perm to carry the
    # focal / generalized / permutation-p triple (a quirk of the shared summary
    # schema, not a labelling error -- values verified against the brief below).
    focal, generalized, p_perm = (round(float(row.macro_AUROC.iloc[0]), 4),
                                  round(float(row.AUROC_subject_ctrl.iloc[0]), 4),
                                  float(row.p_perm.iloc[0]))
    print(f"[Fig 3.15] self-check: focal={focal} (expected {EXPECTED_FOCAL}), "
         f"generalized={generalized} (expected {EXPECTED_GENERALIZED}), "
         f"p={p_perm:.3f} (expected ~{EXPECTED_P})")
    if focal != EXPECTED_FOCAL or generalized != EXPECTED_GENERALIZED or round(p_perm, 3) != EXPECTED_P:
        raise ValueError("Fig 3.15 self-check failed against docs/VERIFIED_NUMBERS.md Part 7.6 -- stop")

    print(f"[Fig 3.15] real points: n={len(persz)} seizures, "
         f"channel counts present: {sorted(persz.n_ictal_ch.unique())}")

    fig, ax = plt.subplots(figsize=(8, 5.6))
    ax.plot(test_panel.n_injected, test_panel.spread_mean, "-o", color=INTERICTAL,
           lw=1.4, ms=6, label="Synthetic injection (held-out panel)", zorder=3)

    rng = np.random.default_rng(0)
    jitter = rng.uniform(-0.15, 0.15, size=len(persz))
    ax.scatter(persz.n_ictal_ch + jitter, persz.spread, color=ICTAL, s=28, alpha=0.75,
              edgecolor="black", linewidth=0.3, label="Real annotations (per seizure, n=36)",
              zorder=4)

    ax.set_xlabel("Number of channels")
    ax.set_ylabel("Diffuseness (spread)")
    # No figure number / descriptive title, and no restated-caption text box
    # on the image (brief §1 rule 5) -- the focal-vs-generalized comparison
    # is printed to console above and belongs in the report's caption.
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(alpha=0.25, lw=0.5)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[saved] {OUT.resolve()}")


if __name__ == "__main__":
    main()
