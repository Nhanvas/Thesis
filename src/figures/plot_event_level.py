"""
================================================================================
 plot_event_level.py  —  Fig 3.6 + Fig 3.7 event-level result figures (final system)
================================================================================
WHY THIS FILE
-------------
Both figures are built ONLY from `results/phaseB/tier2/rlg_test/final_eval_seed42.csv`
— the raw per-(subject, mag_pct, pen_mult) SzCORE grid for the final system. Nothing
here reads a pre-pooled summary table — every number on both plots is recomputed from
TP/FP/n_seizures/n_inter_h at the row level, using the pooled (micro) aggregation:
totals summed across the 8 held-out subjects first, then divided.

This is the second generation of this script. The first drew the earlier
configuration's two operating points (mag70/pen0.5 balanced, mag55/pen0.3
high-sensitivity) and a pooled macro curve on E2 that the exhibit list forbids;
see docs/FIGURE_REBUILD_BRIEF.md for why it was replaced. Verified against
docs/VERIFIED_NUMBERS.md before writing this version:
  headline    (m50/p2.0): pooled sens=0.6184, prec=0.1288, F1=0.2132, FP/day=27.4
      -> matches 0.618 / 0.129 / 0.213 / 27.4
  best-on-curve (m80/p5.0): pooled sens=0.4737, prec=0.3871, F1=0.4260, FP/day=4.9
      -> matches 0.474 / 0.387 / 0.426 / 4.9

FIGURES
-------
Fig 3.6  Sensitivity vs FP/day operating curve (Pareto trade-off), the full 48-cell
    mag_pct x pen_mult grid, pooled/micro across the 8 held-out subjects. Dominated
    points shown de-emphasised (grey); the Pareto frontier connected. Exactly two
    points are marked: the headline (m50/p2.0, the system's reported result) and
    the best point on the curve (m80/p5.0), labelled as the best achievable point
    on this curve and NOT as a result — it was located after the held-out set had
    already been scored.

Fig 3.7  Per-subject breakdown at the headline operating point ONLY (one operating
    point, not two — the earlier figure's second point was the earlier
    configuration's and does not belong here):
      panel (a) sensitivity / precision / F1 per subject
      panel (b) FP/day per subject, own log-scale axis
                (FP/day spans ~2 orders of magnitude across subjects; sens/
                precision/F1 do not, so a shared axis would flatten one of them)

No confidence intervals (brief rule 4). One shared palette (src/figures/palette.py).

USAGE
-----
  python plot_event_level.py
  python plot_event_level.py --figure fig3_6
  python plot_event_level.py --figure fig3_7
================================================================================
"""
import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).parent))
from palette import INTERICTAL, ICTAL, HEADLINE, BEST_ACHIEVABLE, apply_rc

# ----------------------------------------------------------------------------
# The headline operating point (brief rule 3) and the best point on the
# trade-off curve, located post hoc and never presented as a result.
# ----------------------------------------------------------------------------
HEADLINE_OP = dict(key="headline", label="Headline (m50/p2.0)", mag=50.0, pen=2.0,
                    color=HEADLINE, marker="o")
BEST_ON_CURVE_OP = dict(key="best_on_curve",
                        label="Best point on curve (m80/p5.0) — located post hoc, not a result",
                        mag=80.0, pen=5.0, color=BEST_ACHIEVABLE, marker="^")
MARKED_OPS = [HEADLINE_OP, BEST_ON_CURVE_OP]

apply_rc()


# ============================================================================
# DATA — raw grid in, pooled aggregates out (never read a pre-pooled table)
# ============================================================================
def load_grid(csv_path):
    df = pd.read_csv(csv_path)
    required = {"seed", "subject", "mag_pct", "pen_mult", "tp", "fp", "n_seizures", "n_inter_h"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{csv_path} is missing columns: {missing}")
    if df["seed"].nunique() != 1:
        raise ValueError("expected a single-seed grid (canonical seed 42); got seeds "
                         f"{sorted(df['seed'].unique())}")
    return df


def pool_grid(df):
    """Pooled (micro) sensitivity/precision/FP-day per (mag_pct, pen_mult) — TP/FP/
    n_seizures/n_inter_h summed across the 8 subjects first, THEN divided. This is
    the SzCORE-correct aggregation and the one §0 was locked with (never average
    per-subject ratios)."""
    rows = []
    for (mag, pen), d in df.groupby(["mag_pct", "pen_mult"]):
        tp = int(d.tp.sum()); fp = int(d.fp.sum())
        nsz = int(d.n_seizures.sum()); ih = float(d.n_inter_h.sum())
        sens = tp / nsz if nsz else float("nan")
        fpd = fp / ih * 24 if ih else float("nan")
        prec = tp / (tp + fp) if (tp + fp) else float("nan")
        rows.append(dict(mag_pct=mag, pen_mult=pen, tp=tp, fn=nsz - tp, fp=fp,
                         n_seizures=nsz, n_inter_h=ih, sensitivity=sens,
                         fp_per_day=fpd, precision=prec,
                         n_subjects=d["subject"].nunique()))
    return pd.DataFrame(rows)


def mark_pareto(pooled):
    """Pareto frontier: maximise sensitivity, minimise FP/day. Same dominance rule
    as src/retrain_io.mark_pareto (the rule the operating points were selected by)."""
    pooled = pooled.copy()
    recs = pooled.to_dict("records")
    frontier = []
    for r in recs:
        dominated = any(
            (o["sensitivity"] >= r["sensitivity"] and o["fp_per_day"] <= r["fp_per_day"]
             and (o["sensitivity"] > r["sensitivity"] or o["fp_per_day"] < r["fp_per_day"]))
            for o in recs if o is not r)
        frontier.append(not dominated)
    pooled["on_pareto_frontier"] = frontier
    return pooled


def locate_locked(pooled, op):
    row = pooled[(np.isclose(pooled.mag_pct, op["mag"])) & (np.isclose(pooled.pen_mult, op["pen"]))]
    if row.empty:
        raise ValueError(f"locked operating point mag{op['mag']}/pen{op['pen']} not found "
                         f"in the grid — check --csv points at the right file")
    return row.iloc[0]


# ============================================================================
# E1 — Sensitivity vs FP/day operating curve (Pareto trade-off)
# ============================================================================
def plot_e1(df, out_dir):
    pooled = mark_pareto(pool_grid(df))
    frontier = pooled[pooled.on_pareto_frontier].sort_values("fp_per_day")
    dominated = pooled[~pooled.on_pareto_frontier]

    fig, ax = plt.subplots(figsize=(6.6, 5.2))

    ax.scatter(dominated.fp_per_day, dominated.sensitivity, s=22, color="#b5b5b5",
              alpha=0.75, zorder=2, label="Dominated grid points (mag% x pen)")

    ax.plot(frontier.fp_per_day, frontier.sensitivity, "-", color="#404040",
           lw=1.1, zorder=3, alpha=0.85)
    ax.scatter(frontier.fp_per_day, frontier.sensitivity, s=32, color="#404040",
              zorder=4, label="Pareto frontier")

    for i, op in enumerate(MARKED_OPS):
        r = locate_locked(pooled, op)
        f1 = 2 * r.precision * r.sensitivity / (r.precision + r.sensitivity)
        ax.scatter([r.fp_per_day], [r.sensitivity], s=170, marker=op["marker"],
                  facecolor=op["color"], edgecolor="black", linewidth=1.1, zorder=6,
                  label=op["label"])
        xytext = (20, 22) if op["key"] == "headline" else (30, -60)
        ax.annotate(
            f"{op['label']}\nsens={r.sensitivity:.3f}  F1={f1:.3f}  FP/day={r.fp_per_day:.1f}\n"
            f"TP/FN/FP={int(r.tp)}/{int(r.fn)}/{int(r.fp)}",
            xy=(r.fp_per_day, r.sensitivity), xytext=xytext, textcoords="offset points",
            fontsize=8, color=op["color"],
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor=op["color"],
                      linewidth=0.6, alpha=0.95),
            arrowprops=dict(arrowstyle="-", color=op["color"], lw=0.8), zorder=7)

    ax.set_xlabel("False positives per day (pooled, 278.2 interictal h)")
    ax.set_ylabel("Event sensitivity (pooled, 76 seizures)")
    ax.set_title("Fig 3.6 — event-level operating curve, final system\n"
                "full mag% x pen grid, pooled across 8 held-out subjects, seed 42")
    ax.set_ylim(0.20, 0.95)
    ax.set_xlim(0, pooled.fp_per_day.max() * 1.08)
    ax.grid(alpha=0.25, lw=0.5)
    ax.legend(loc="upper left", fontsize=8, framealpha=0.95)

    _save(fig, out_dir, "fig3_6_operating_curve")
    return pooled


# ============================================================================
# Fig 3.7 — per-subject breakdown at the headline operating point only
# ============================================================================
def plot_fig3_7(df, out_dir):
    subs = sorted(df.subject.unique())
    n = len(subs)
    x = np.arange(n)

    op = HEADLINE_OP
    d = df[(np.isclose(df.mag_pct, op["mag"])) & (np.isclose(df.pen_mult, op["pen"]))]
    d = d.set_index("subject").reindex(subs)
    if d[["tp", "fp", "n_seizures", "n_inter_h"]].isna().any().any():
        raise ValueError(f"missing subject rows at {op['key']} (mag{op['mag']}/pen{op['pen']})")

    tp = d["tp"].values.astype(float); fp = d["fp"].values.astype(float)
    nsz = d["n_seizures"].values.astype(float)
    sens = tp / nsz
    prec = np.divide(tp, tp + fp, out=np.full_like(tp, np.nan), where=(tp + fp) > 0)
    f1 = np.divide(2 * prec * sens, prec + sens,
                   out=np.full_like(tp, np.nan), where=(prec + sens) > 0)
    fpd = fp / d["n_inter_h"].values.astype(float) * 24

    print(f"\n[Fig 3.7] per-subject values at the headline point ({op['label']}):")
    for s, sv, pv, fv, fd in zip(subs, sens, prec, f1, fpd):
        print(f"  {s}: sens={sv:.3f} prec={pv:.3f} f1={fv:.3f} fp/day={fd:.1f}")

    metric_colors = dict(sensitivity="#1b7837", precision="#762a83", f1="#2166ac")
    metric_labels = dict(sensitivity="Sensitivity", precision="Precision", f1="F1")
    vals = dict(sensitivity=sens, precision=prec, f1=f1)
    metrics = ["sensitivity", "precision", "f1"]

    fig, (axa, axb) = plt.subplots(2, 1, figsize=(9.4, 8.4),
                                   gridspec_kw=dict(height_ratios=[1.35, 1]))

    # ---- panel (a): sensitivity / precision / F1, grouped by subject ----
    bar_w = 0.8 / len(metrics)
    for mi, met in enumerate(metrics):
        offset = (mi - (len(metrics) - 1) / 2) * bar_w
        axa.bar(x + offset, vals[met], width=bar_w * 0.92, color=metric_colors[met],
               edgecolor="black", linewidth=0.4)

    axa.set_xticks(x); axa.set_xticklabels(subs)
    axa.set_ylabel("Score")
    axa.set_ylim(0, 1.1)
    axa.set_title(f"(a) Per-subject event sensitivity / precision / F1 — {op['label']}")
    axa.grid(axis="y", alpha=0.25, lw=0.5)
    metric_handles = [Patch(facecolor=metric_colors[m], edgecolor="black", label=metric_labels[m])
                      for m in metrics]
    axa.legend(handles=metric_handles, loc="upper right", fontsize=8, framealpha=1.0)
    for xi, sv in zip(x, sens):
        if sv == 0:
            axa.text(xi, 0.02, "0", ha="center", va="bottom", fontsize=8)

    # ---- panel (b): FP/day per subject, linear axis (range spans well under one decade) ----
    axb.bar(x, fpd, width=0.55, color=op["color"], edgecolor="black", linewidth=0.4)
    for xi, v in zip(x, fpd):
        axb.text(xi, v + fpd.max() * 0.015, f"{v:.1f}", ha="center", va="bottom", fontsize=7)

    axb.set_xticks(x); axb.set_xticklabels(subs)
    axb.set_ylabel("False positives / day")
    axb.set_ylim(0, fpd.max() * 1.15)
    axb.set_title("(b) Per-subject false-positive rate")
    axb.grid(axis="y", alpha=0.2, lw=0.5)

    fig.suptitle(f"Fig 3.7 — event-level per-subject breakdown at the headline point only "
                f"({op['label']})\n(seed 42, final system, SzCORE any-overlap scoring)",
                y=1.01, fontsize=10.5)
    fig.tight_layout()
    _save(fig, out_dir, "fig3_7_persubject_event")


# ----------------------------------------------------------------------------
def _save(fig, out_dir, name):
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(out_dir / f"{name}.{ext}", bbox_inches="tight")
    plt.close(fig)
    print(f"  [saved] {(out_dir / (name + '.png')).resolve()}")
    print(f"  [saved] {(out_dir / (name + '.pdf')).resolve()}")


# Values from docs/VERIFIED_NUMBERS.md §1.1, checked to the brief's stated precision
# (three decimals for sensitivity/precision/F1, one decimal for FP/day).
EXPECTED = {
    "headline": dict(sens=0.618, prec=0.129, f1=0.213, fpd=27.4),
    "best_on_curve": dict(sens=0.474, prec=0.387, f1=0.426, fpd=4.9),
}


def check_marked_points(pooled):
    print("\n[check] marked operating points against docs/VERIFIED_NUMBERS.md:")
    for op in MARKED_OPS:
        r = locate_locked(pooled, op)
        exp = EXPECTED[op["key"]]
        sens, prec, fpd = round(r.sensitivity, 3), round(r.precision, 3), round(r.fp_per_day, 1)
        f1 = round(2 * r.precision * r.sensitivity / (r.precision + r.sensitivity), 3)
        print(f"  {op['key']}: sens={sens} prec={prec} f1={f1} fp/day={fpd}  "
             f"TP/FN/FP={int(r.tp)}/{int(r.fn)}/{int(r.fp)}")
        if (sens, prec, f1, fpd) != (exp["sens"], exp["prec"], exp["f1"], exp["fpd"]):
            raise ValueError(f"{op['key']} does not match VERIFIED_NUMBERS.md: "
                             f"got {(sens, prec, f1, fpd)}, expected "
                             f"{(exp['sens'], exp['prec'], exp['f1'], exp['fpd'])} -- stop")
        print(f"    OK, matches {exp}")


# ============================================================================
def main():
    ap = argparse.ArgumentParser(description="Fig 3.6 + Fig 3.7 event-level figures (final system)")
    ap.add_argument("--csv", default="results/phaseB/tier2/rlg_test/final_eval_seed42.csv")
    ap.add_argument("--out_dir", default="figures/event_level")
    ap.add_argument("--figure", choices=["fig3_6", "fig3_7", "both"], default="both")
    a = ap.parse_args()

    df = load_grid(a.csv)
    print(f"loaded grid: {df.shape[0]} rows, {df.subject.nunique()} subjects, "
         f"{df.mag_pct.nunique()} mag_pct x {df.pen_mult.nunique()} pen_mult")

    if a.figure in ("fig3_6", "both"):
        print("\n[Fig 3.6] operating curve ...")
        pooled = plot_e1(df, a.out_dir)
        check_marked_points(pooled)

    if a.figure in ("fig3_7", "both"):
        print("\n[Fig 3.7] per-subject breakdown ...")
        plot_fig3_7(df, a.out_dir)

    print(f"\nDone -> {Path(a.out_dir).resolve()}")


if __name__ == "__main__":
    main()
