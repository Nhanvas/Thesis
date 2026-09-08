"""
fig4_1_comparison.py -- Fig 4.1, This work against published results
(Figure Round 7, item 3)
================================================================================
Plane: event sensitivity (vertical) against false alarms per day (horizontal,
LOGARITHMIC -- the three published points span 1.34 to 127.7, and a linear
axis would collapse everything below ten into a single column).

This work's curve is the Pareto front over the committed grid in
`results/phaseB/tier2/rlg_test/final_eval_seed42.csv`, pooled across the eight
held-out subjects for each of the 48 (magnitude percentile, penalty
multiplier) cells: for each false-alarm level, the highest sensitivity
achieved at or below it. Two points on that front are marked:

  - the REPORTED operating point (m50/p2.0), in the headline colour;
  - the BEST point on the curve (m80/p5.0), in the post-hoc colour, labelled
    as located after the held-out set was scored -- never as a result.

Both are self-checked against docs/VERIFIED_NUMBERS.md Part 1.1 before
drawing; the script stops rather than plotting a value it cannot confirm.

Three published points qualify for this plane -- scored at event level, on a
patient-independent split, with a reported false-alarm rate (tables/
tables_ch4.md, "Figure 4.1 -- which points may be plotted"). Every other row
of Table 4.1 fails at least one of those conditions and does not appear here.
Nothing is added to make the plane look fuller: the sparseness is a finding
about the literature, not a defect of the figure.

USAGE
    python src/figures/fig4_1_comparison.py
"""
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
for _p in (_here,):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from palette import HEADLINE, BEST_ACHIEVABLE, apply_rc

apply_rc()

GRID_CSV = Path("results/phaseB/tier2/rlg_test/final_eval_seed42.csv")
OUT = Path("figures/fig4_1_comparison.png")

# docs/VERIFIED_NUMBERS.md Part 1.1 / Part 1 headline table
EXPECTED_HEADLINE = dict(mag_pct=50.0, pen_mult=2.0, sens=0.618, fp_day=27.4)
EXPECTED_BEST = dict(mag_pct=80.0, pen_mult=5.0, sens=0.474, fp_day=4.9)
TOL_SENS = 0.001
TOL_FP = 0.05

# tables/tables_ch4.md "Figure 4.1 -- which points may be plotted"
PUBLISHED_POINTS = [
    dict(name="Ali et al. 2024, 5-fold", sens=0.726, fp_day=127.7,
         corpus="CHB-MIT", same_corpus=True),
    dict(name="Ali et al. 2024, leave-one-out", sens=0.753, fp_day=115.0,
         corpus="CHB-MIT", same_corpus=True),
    dict(name="Community challenge 2025, winner", sens=0.370, fp_day=1.34,
         corpus="private", same_corpus=False),
]


def compute_pareto_front(csv_path):
    df = pd.read_csv(csv_path)
    if len(df) != 384 or df["subject"].nunique() != 8:
        raise SystemExit(
            f"[STOP] {csv_path} has {len(df)} rows / {df['subject'].nunique()} subjects, "
            f"expected 384 rows across 8 subjects"
        )
    g = (df.groupby(["mag_pct", "pen_mult"])
           .agg(tp=("tp", "sum"), fp=("fp", "sum"),
                nsz=("n_seizures", "sum"), hrs=("n_inter_h", "sum"))
           .reset_index())
    g["sens"] = g["tp"] / g["nsz"]
    g["fp_day"] = g["fp"] / g["hrs"] * 24.0
    g = g.sort_values("fp_day").reset_index(drop=True)

    pareto_rows = []
    best_sens = -1.0
    for _, row in g.iterrows():
        if row["sens"] > best_sens:
            pareto_rows.append(row)
            best_sens = row["sens"]
    pareto = pd.DataFrame(pareto_rows).reset_index(drop=True)
    return g, pareto


def _find_cell(table, mag_pct, pen_mult):
    hit = table[(table["mag_pct"] == mag_pct) & (table["pen_mult"] == pen_mult)]
    if hit.empty:
        raise SystemExit(f"[STOP] cell m{mag_pct}/p{pen_mult} not found in the grid")
    return hit.iloc[0]


def main():
    full_grid, pareto = compute_pareto_front(GRID_CSV)

    headline = _find_cell(full_grid, EXPECTED_HEADLINE["mag_pct"], EXPECTED_HEADLINE["pen_mult"])
    best = _find_cell(full_grid, EXPECTED_BEST["mag_pct"], EXPECTED_BEST["pen_mult"])

    for label, computed, expected in (
        ("headline (m50/p2.0)", headline, EXPECTED_HEADLINE),
        ("best point (m80/p5.0)", best, EXPECTED_BEST),
    ):
        if abs(computed["sens"] - expected["sens"]) > TOL_SENS:
            raise SystemExit(
                f"[STOP] {label}: computed sensitivity {computed['sens']:.4f} disagrees "
                f"with docs/VERIFIED_NUMBERS.md value {expected['sens']}"
            )
        if abs(computed["fp_day"] - expected["fp_day"]) > TOL_FP:
            raise SystemExit(
                f"[STOP] {label}: computed FP/day {computed['fp_day']:.2f} disagrees "
                f"with docs/VERIFIED_NUMBERS.md value {expected['fp_day']}"
            )
        print(f"[self-check] {label}: sensitivity {computed['sens']:.4f} "
              f"(committed {expected['sens']}), {computed['fp_day']:.2f} FP/day "
              f"(committed {expected['fp_day']}) -- match")

    if not ((pareto["mag_pct"] == EXPECTED_HEADLINE["mag_pct"]) &
            (pareto["pen_mult"] == EXPECTED_HEADLINE["pen_mult"])).any():
        raise SystemExit("[STOP] the headline cell does not lie on the computed Pareto front")
    if not ((pareto["mag_pct"] == EXPECTED_BEST["mag_pct"]) &
            (pareto["pen_mult"] == EXPECTED_BEST["pen_mult"])).any():
        raise SystemExit("[STOP] the best-point cell does not lie on the computed Pareto front")

    fig, ax = plt.subplots(figsize=(9.2, 6.2))

    ax.plot(pareto["fp_day"], pareto["sens"], color="#4C4C4C", lw=1.4, marker="o",
            ms=3.5, zorder=3, label="This work -- Pareto front (committed grid)")

    ax.scatter([headline["fp_day"]], [headline["sens"]], color=HEADLINE, s=110,
               marker="D", zorder=5, edgecolor="black", linewidth=0.6,
               label="Reported operating point (m50/p2.0)")
    ax.annotate("Reported\noperating point", (headline["fp_day"], headline["sens"]),
                xytext=(12, -34), textcoords="offset points", fontsize=8, color=HEADLINE,
                ha="left", bbox=dict(facecolor="white", alpha=0.85, edgecolor="none", pad=1))

    ax.scatter([best["fp_day"]], [best["sens"]], color=BEST_ACHIEVABLE, s=110,
               marker="*", zorder=5, edgecolor="black", linewidth=0.6,
               label="Best point on the curve (located post-hoc)")
    ax.annotate("Best point,\nlocated after scoring", (best["fp_day"], best["sens"]),
                xytext=(-105, 8), textcoords="offset points", fontsize=8,
                color=BEST_ACHIEVABLE, ha="left",
                bbox=dict(facecolor="white", alpha=0.85, edgecolor="none", pad=1))

    same_corpus_marker = "o"
    diff_corpus_marker = "s"
    plotted_same_label = False
    plotted_diff_label = False
    label_offsets = {
        "Ali et al. 2024, 5-fold": (14, 22),
        "Ali et al. 2024, leave-one-out": (14, -30),
        "Community challenge 2025, winner": (8, 6),
    }
    for p in PUBLISHED_POINTS:
        marker = same_corpus_marker if p["same_corpus"] else diff_corpus_marker
        label = None
        if p["same_corpus"] and not plotted_same_label:
            label = "Published, same corpus (CHB-MIT)"
            plotted_same_label = True
        elif not p["same_corpus"] and not plotted_diff_label:
            label = "Published, different corpus"
            plotted_diff_label = True
        ax.scatter([p["fp_day"]], [p["sens"]], color="#666666", s=80, marker=marker,
                   zorder=4, edgecolor="black", linewidth=0.5, label=label)
        ax.annotate(f"{p['name']}\n({p['corpus']})", (p["fp_day"], p["sens"]),
                    xytext=label_offsets[p["name"]], textcoords="offset points",
                    fontsize=7.5, color="#333333",
                    arrowprops=dict(arrowstyle="-", color="#999999", lw=0.6))

    ax.set_xscale("log")
    ax.set_xlabel("False alarms per day (logarithmic scale)")
    ax.set_ylabel("Event sensitivity")
    ax.set_xlim(1.0, 280.0)
    ax.set_ylim(0.0, 1.0)
    ax.legend(fontsize=7.5, loc="lower right", framealpha=1.0)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, bbox_inches="tight")
    plt.close(fig)

    print("\n[Pareto front vertices] (mag_pct, pen_mult, sensitivity, fp_per_day)")
    for _, r in pareto.iterrows():
        print(f"  m{r['mag_pct']:.0f}/p{r['pen_mult']:.1f}  "
              f"sens={r['sens']:.4f}  fp/day={r['fp_day']:.2f}")

    print("\n[Marked points]")
    print(f"  Reported operating point: m50/p2.0  sens={headline['sens']:.4f}  "
          f"fp/day={headline['fp_day']:.2f}")
    print(f"  Best point (post-hoc):    m80/p5.0  sens={best['sens']:.4f}  "
          f"fp/day={best['fp_day']:.2f}")

    print("\n[Published points]")
    for p in PUBLISHED_POINTS:
        print(f"  {p['name']} ({p['corpus']}): sens={p['sens']}  fp/day={p['fp_day']}")

    print(f"\n[saved] {OUT.resolve()}")


if __name__ == "__main__":
    main()
