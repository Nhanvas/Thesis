"""
fig3_15_diffuseness.py -- Fig 3.15, Figure Brief Round 2 Task C, redrawn per
docs/FIGURE_FIXES_R3.md §1 ("Fig 3.15 -- conceptual error, fix this one first").

The 76 held-out seizures split into 36 with a channel annotation (focal) and 40 annotated as
diffuse (generalized) -- the diffuse group has no channel count and was therefore previously
absent from the plot entirely, even though the caption's claim is about focal against
generalized. This version adds the diffuse group as its own categorical strip to the right of
the numeric channel-count axis, so both groups actually appear.

Diffuseness (the "spread" measure) against the number of annotated channels: a line for the
synthetic case across the injected-channel counts; points for the real focal annotations at
their own channel counts (jittered); a strip of points for the real diffuse (generalized)
annotations in the categorical position; group means marked for both real groups.

Sources:
  results/attribution_v6/synthetic_spread.csv (TEST panel, alpha=2.0 -- the held-out-subject
    panel, matching the real points, which are all held-out subjects) for the line.
  results/attribution_v6/attribution_perseizure.csv (n_ictal_ch, spread) for the 36 real focal
    per-seizure points.
  results/attribution_v6/attribution_perseizure_generalized.csv for the 40 real diffuse
    per-seizure points -- written by `python src/attribution_pipeline.py eval`
    (docs/FIGURE_FIXES_R3.md §1: these are the individual points behind the group mean that
    was already committed in attribution_summary.csv; attribution_pipeline.py already computed
    them internally via the locked `spread_one` call and discarded them, so persisting them is
    not a new computation -- attribution_perseizure.csv and attribution_summary.csv are
    reproduced byte-identical by the same run).

Self-check against docs/VERIFIED_NUMBERS.md §7.6: on the real annotations, focal 0.9693
against generalized 0.9594, one-sided p = 0.984 -- read from
results/attribution_v6/attribution_summary.csv, row "spread focal vs generalized", and
cross-checked against the mean of the two per-seizure files read here. The caption states the
measure is U-shaped in channel count for the synthetic injections and runs the wrong way
(generalized sits LOWER, not higher) on the real annotations, so it is reported as a
methodological negative and never used to classify.
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

from palette import INTERICTAL, ICTAL, DIFFUSE_GROUP, apply_rc

ROOT = Path(_src).parent
SYNTH_CSV = ROOT / "results" / "attribution_v6" / "synthetic_spread.csv"
PERSZ_CSV = ROOT / "results" / "attribution_v6" / "attribution_perseizure.csv"
PERSZ_GEN_CSV = ROOT / "results" / "attribution_v6" / "attribution_perseizure_generalized.csv"
SUMMARY_CSV = ROOT / "results" / "attribution_v6" / "attribution_summary.csv"
OUT = ROOT / "figures" / "fig3_15_diffuseness.png"

EXPECTED_FOCAL, EXPECTED_GENERALIZED, EXPECTED_P = 0.9693, 0.9594, 0.984
NUMERIC_TICKS = [1, 2, 4, 8, 12, 18]
DIFFUSE_X = 21.5          # categorical position, right of 18, visually detached
JITTER_HALF_WIDTH = 0.15  # data units on the (integer channel count) x-axis


def main():
    apply_rc()

    persz = pd.read_csv(PERSZ_CSV)
    if "spread" not in persz.columns:
        raise SystemExit("Fig 3.15: attribution_perseizure.csv has no diffuseness ('spread') "
                         "column -- stop, per Task C instructions (do not compute the measure "
                         "inside the plotting script).")
    if not PERSZ_GEN_CSV.exists():
        raise SystemExit(f"Fig 3.15: {PERSZ_GEN_CSV} not found -- run "
                         "`python src/attribution_pipeline.py eval` first, stop.")
    persz_gen = pd.read_csv(PERSZ_GEN_CSV)
    if "spread" not in persz_gen.columns:
        raise SystemExit("Fig 3.15: attribution_perseizure_generalized.csv has no 'spread' "
                         "column -- stop.")

    synth = pd.read_csv(SYNTH_CSV)
    test_panel = synth[(synth.panel == "TEST") & (np.isclose(synth.alpha, 2.0))].sort_values("n_injected")
    if test_panel.empty:
        raise SystemExit(f"Fig 3.15: no TEST/alpha=2.0 rows in {SYNTH_CSV} -- stop")
    # docs/FIGURE_ROUND5.md §5: synthetic_spread.csv's own grid is {1,2,4,12,18}, not
    # {1,2,4,8,12} -- the pre-registered grid for the DISCRIMINATION experiment
    # (synthetic_sanity.csv / docs/ATTRIBUTION_REPORT_PACK.md §2.6). The spread
    # (diffuseness) experiment was run on its own, different grid
    # (docs/ATTRIBUTION_REPORT_PACK.md §3.5 quotes it at |S|=1,2,4,12,18); this is a
    # fact about that experiment's design, not a missing point, and no point at 8 is
    # added here to make the two grids agree.
    grid_here = sorted(int(x) for x in test_panel.n_injected.unique())
    print(f"[Fig 3.15] synthetic_spread.csv injected-channel grid (TEST, alpha=2.0): "
         f"{grid_here} -- differs from the discrimination experiment's pre-registered "
         f"grid [1, 2, 4, 8, 12] (synthetic_sanity.csv); the two experiments were run "
         f"on different grids, this is not an omission")

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
    print(f"[Fig 3.15] self-check (committed group means): focal={focal} (expected {EXPECTED_FOCAL}), "
         f"generalized={generalized} (expected {EXPECTED_GENERALIZED}), "
         f"p={p_perm:.3f} (expected ~{EXPECTED_P})")
    if focal != EXPECTED_FOCAL or generalized != EXPECTED_GENERALIZED or round(p_perm, 3) != EXPECTED_P:
        raise ValueError("Fig 3.15 self-check failed against docs/VERIFIED_NUMBERS.md Part 7.6 -- stop")

    # Cross-check the per-seizure files reproduce the same two group means.
    focal_pts_mean = round(float(persz.spread.mean()), 4)
    gen_pts_mean = round(float(persz_gen.spread.mean()), 4)
    print(f"[Fig 3.15] self-check (per-seizure files): focal n={len(persz)} mean={focal_pts_mean}, "
         f"generalized n={len(persz_gen)} mean={gen_pts_mean}")
    if focal_pts_mean != EXPECTED_FOCAL or gen_pts_mean != EXPECTED_GENERALIZED:
        raise ValueError("Fig 3.15: per-seizure file means disagree with the committed group "
                         "means above -- stop")
    if len(persz) != 36 or len(persz_gen) != 40:
        raise ValueError(f"Fig 3.15: expected 36 focal / 40 generalized seizures, got "
                         f"{len(persz)} / {len(persz_gen)} -- stop")

    print(f"[Fig 3.15] real focal points: n={len(persz)}, channel counts present: "
         f"{sorted(persz.n_ictal_ch.unique())}")
    print(f"[Fig 3.15] real diffuse (generalized) points: n={len(persz_gen)}, drawn as a "
         f"categorical strip at x={DIFFUSE_X} (no channel count exists for this group)")

    rng = np.random.default_rng(0)
    jitter_focal = rng.uniform(-JITTER_HALF_WIDTH, JITTER_HALF_WIDTH, size=len(persz))
    jitter_gen = rng.uniform(-JITTER_HALF_WIDTH, JITTER_HALF_WIDTH, size=len(persz_gen))
    print(f"[Fig 3.15] real points ARE jittered: uniform +/-{JITTER_HALF_WIDTH:.2f} channel-count "
         f"units on the x-axis only (y = the actual spread value, unjittered); seed 0.")

    fig, ax = plt.subplots(figsize=(9, 5.8))

    # Synthetic line -- numeric axis only, the injected-channel-count axis is meaningful here.
    ax.plot(test_panel.n_injected, test_panel.spread_mean, "-o", color=INTERICTAL,
           lw=1.4, ms=6, label="Synthetic injection (held-out panel)", zorder=3)

    # Real focal points, jittered around their own (integer) channel count.
    ax.scatter(persz.n_ictal_ch + jitter_focal, persz.spread, color=ICTAL, s=26, alpha=0.75,
              edgecolor="black", linewidth=0.3, label=f"Real, focal (per seizure, n={len(persz)})",
              zorder=4)
    # Focal group mean -- a horizontal marker spanning the numeric channel counts actually
    # annotated (1-2), so it sits visibly among the points it summarises.
    ax.plot([1 - JITTER_HALF_WIDTH - 0.1, 2 + JITTER_HALF_WIDTH + 0.1], [focal, focal],
           color=ICTAL, lw=2.2, solid_capstyle="butt", zorder=5,
           label=f"Focal group mean ({focal:.4f})")

    # Divider marking the numeric axis is over; diffuse group is categorical, detached.
    divider_x = (18 + DIFFUSE_X) / 2
    ax.axvline(divider_x, color="0.75", lw=1.0, ls=":", zorder=1)

    # Real diffuse (generalized) points -- categorical strip, jittered in x only.
    ax.scatter(DIFFUSE_X + jitter_gen, persz_gen.spread, color=DIFFUSE_GROUP, s=26, alpha=0.75,
              edgecolor="black", linewidth=0.3,
              label=f"Real, diffuse / generalized (per seizure, n={len(persz_gen)})", zorder=4)
    ax.plot([DIFFUSE_X - JITTER_HALF_WIDTH - 0.35, DIFFUSE_X + JITTER_HALF_WIDTH + 0.35],
           [generalized, generalized], color=DIFFUSE_GROUP, lw=2.2, solid_capstyle="butt", zorder=5,
           label=f"Diffuse/generalized group mean ({generalized:.4f})")

    ax.set_xticks(NUMERIC_TICKS + [DIFFUSE_X])
    ax.set_xticklabels([str(t) for t in NUMERIC_TICKS] + ["diffuse\n(no count)"])
    ax.set_xlim(0, DIFFUSE_X + 2.2)
    ax.set_ylim(0.885, 1.005)
    ax.set_xlabel("Number of annotated channels")
    ax.set_ylabel("Diffuseness (spread)")

    # docs/FIGURE_ROUND5.md §5: the explanatory sentence used to sit inside the image as
    # an axes text box. No figure in this report carries a sentence of prose inside the
    # axes -- moved out, printed to console below as caption text instead.
    print(f"[CAPTION] generalized mean sits LOWER than focal "
         f"({generalized:.4f} < {focal:.4f}, one-sided p={p_perm:.3f}) -- the wrong "
         "direction for the hypothesis.")
    ax.legend(fontsize=7.8, loc="upper center", ncol=2)
    ax.grid(alpha=0.25, lw=0.5)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[saved] {OUT.resolve()}")


if __name__ == "__main__":
    main()
