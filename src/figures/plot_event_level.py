"""
================================================================================
 plot_event_level.py  —  E1 + E2 event-level result figures (baseline-of-record, §0)
================================================================================
WHY THIS FILE
-------------
Both figures are built ONLY from `final_eval_seed42.csv` — the raw per-(subject,
mag_pct, pen_mult) SzCORE grid produced by `score_ens.py`'s fast grid (bit-identical
to `szcore_eval.evaluate_subject`; see that script's own --verify flag). Nothing
here reads a pre-pooled summary table (e.g. `report_metrics.csv` or the numbers
printed in RESULTS_OF_RECORD.md) — every number on both plots is recomputed from
TP/FP/n_seizures/n_inter_h at the row level, using the same pooled (micro)
aggregation SzCORE prescribes and §0 was locked with.

Verified before writing this script (see the two `pool()` checks against
RESULTS_OF_RECORD.md §0):
  balanced  (mag70/pen0.5): pooled sens=0.6316, FP/day=38.56, TP/FN/FP=48/28/447
      -> matches locked 0.632 / 38.6 / 48/28/447
  high-sens (mag55/pen0.3): pooled sens=0.7763, FP/day=72.72, TP/FN/FP=59/17/843
      -> matches locked 0.776 / 72.7 / 59/17/843

FIGURES
-------
E1  Sensitivity vs FP/day operating curve (Pareto trade-off), the full 48-point
    mag_pct x pen_mult grid, pooled/micro across the 8 test subjects. Dominated
    points shown de-emphasised (grey); the Pareto frontier connected; the two
    LOCKED operating points (balanced, high-sensitivity) marked + annotated with
    their exact sensitivity / FP-day / TP-FN-FP.

E2  Per-subject breakdown at the two locked operating points only:
      panel (a) sensitivity / precision / F1 per subject x 2 operating points
                (balanced = solid, high-sensitivity = hatched)
      panel (b) FP/day per subject x 2 operating points, own log-scale axis
                (FP/day spans ~2 orders of magnitude across subjects; sens/
                precision/F1 do not, so a shared axis would flatten one of them)

USAGE
-----
  python plot_event_level.py
  python plot_event_level.py --figure e1
  python plot_event_level.py --figure e2
  python plot_event_level.py --csv results/retrain_v3p1/final_eval_seed42.csv \
      --out_dir docs/figures/event_level
================================================================================
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# ----------------------------------------------------------------------------
# Locked operating points (RESULTS_OF_RECORD.md §0 / docs/REBUILD_BASELINE_LOCK.md)
# ----------------------------------------------------------------------------
LOCKED_OPS = [
    dict(key="balanced", label="Balanced (mag70/pen0.5)", mag=70.0, pen=0.5,
         color="#1f4e79", marker="o"),
    dict(key="highsens", label="High-sensitivity (mag55/pen0.3)", mag=55.0, pen=0.3,
         color="#c0392b", marker="^"),
]

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
})


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

    for i, op in enumerate(LOCKED_OPS):
        r = locate_locked(pooled, op)
        ax.scatter([r.fp_per_day], [r.sensitivity], s=170, marker=op["marker"],
                  facecolor=op["color"], edgecolor="black", linewidth=1.1, zorder=6,
                  label=op["label"])
        xytext = (16, -36) if op["key"] == "balanced" else (-150, 26)
        ax.annotate(
            f"{op['label']}\nsens={r.sensitivity:.3f}  FP/day={r.fp_per_day:.1f}\n"
            f"TP/FN/FP={int(r.tp)}/{int(r.fn)}/{int(r.fp)}",
            xy=(r.fp_per_day, r.sensitivity), xytext=xytext, textcoords="offset points",
            fontsize=8, color=op["color"],
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor=op["color"],
                      linewidth=0.6, alpha=0.95),
            arrowprops=dict(arrowstyle="-", color=op["color"], lw=0.8), zorder=7)

    ax.set_xlabel("False positives per day (pooled, 278.2 interictal h)")
    ax.set_ylabel("Event sensitivity (pooled, 76 seizures)")
    ax.set_title("Event-level operating curve — SzCORE pooled, 8 test subjects\n"
                "full mag% x pen grid, seed 42 (baseline-of-record)")
    ax.set_ylim(0.20, 0.95)
    ax.set_xlim(0, pooled.fp_per_day.max() * 1.08)
    ax.grid(alpha=0.25, lw=0.5)
    ax.legend(loc="lower right", fontsize=8, framealpha=0.95)

    _save(fig, out_dir, "E1_operating_curve")
    return pooled


# ============================================================================
# E2 — per-subject breakdown at the two locked operating points
# ============================================================================
def plot_e2(df, out_dir):
    subs = sorted(df.subject.unique())
    n = len(subs)
    x = np.arange(n)

    op_rows = {}
    for op in LOCKED_OPS:
        d = df[(np.isclose(df.mag_pct, op["mag"])) & (np.isclose(df.pen_mult, op["pen"]))]
        d = d.set_index("subject").reindex(subs)
        if d[["tp", "fp", "n_seizures", "n_inter_h"]].isna().any().any():
            raise ValueError(f"missing subject rows at {op['key']} (mag{op['mag']}/pen{op['pen']})")
        op_rows[op["key"]] = d

    metric_colors = dict(sensitivity="#1b7837", precision="#762a83", f1="#2166ac")
    metric_labels = dict(sensitivity="Sensitivity", precision="Precision", f1="F1")
    metrics = ["sensitivity", "precision", "f1"]

    fig, (axa, axb) = plt.subplots(2, 1, figsize=(9.4, 8.4),
                                   gridspec_kw=dict(height_ratios=[1.35, 1]))

    # ---- panel (a): sensitivity / precision / F1, grouped OP -> metric ----
    n_ops, n_met = len(LOCKED_OPS), len(metrics)
    group_w = 0.80
    bar_w = group_w / (n_ops * n_met)
    for oi, op in enumerate(LOCKED_OPS):
        d = op_rows[op["key"]]
        tp = d["tp"].values.astype(float); fp = d["fp"].values.astype(float)
        nsz = d["n_seizures"].values.astype(float)
        sens = tp / nsz
        prec = np.divide(tp, tp + fp, out=np.full_like(tp, np.nan), where=(tp + fp) > 0)
        f1 = np.divide(2 * prec * sens, prec + sens,
                       out=np.full_like(tp, np.nan), where=(prec + sens) > 0)
        vals = dict(sensitivity=sens, precision=prec, f1=f1)
        for mi, met in enumerate(metrics):
            offset = (oi * n_met + mi - (n_ops * n_met - 1) / 2) * bar_w
            hatch = None if op["key"] == "balanced" else "//"
            axa.bar(x + offset, vals[met], width=bar_w * 0.92, color=metric_colors[met],
                   hatch=hatch, edgecolor="black", linewidth=0.4)

    axa.set_xticks(x); axa.set_xticklabels(subs)
    axa.set_ylabel("Score")
    axa.set_ylim(0, 1.22)
    axa.set_title("(a) Per-subject event sensitivity / precision / F1 — "
                 "balanced (solid) vs high-sensitivity (hatched)")
    axa.grid(axis="y", alpha=0.25, lw=0.5)
    metric_handles = [Patch(facecolor=metric_colors[m], edgecolor="black", label=metric_labels[m])
                      for m in metrics]
    op_handles = [Patch(facecolor="white", edgecolor="black", label="Balanced"),
                 Patch(facecolor="white", edgecolor="black", hatch="//", label="High-sensitivity")]
    axa.legend(handles=metric_handles + op_handles, loc="upper right", ncol=2, fontsize=8,
              framealpha=1.0)

    # ---- panel (b): FP/day per subject, own log-scale axis ----
    bw = 0.34
    for oi, op in enumerate(LOCKED_OPS):
        d = op_rows[op["key"]]
        fpd = d["fp"].values.astype(float) / d["n_inter_h"].values.astype(float) * 24
        offset = (oi - (n_ops - 1) / 2) * bw
        axb.bar(x + offset, fpd, width=bw * 0.92, color=op["color"], edgecolor="black",
               linewidth=0.4, label=op["label"])
        for xi, v in zip(x + offset, fpd):
            axb.text(xi, v * 1.06, f"{v:.0f}", ha="center", va="bottom", fontsize=7)

    axb.set_xticks(x); axb.set_xticklabels(subs)
    axb.set_ylabel("False positives / day (log scale)")
    axb.set_yscale("log")
    axb.set_title("(b) Per-subject false-positive rate")
    axb.grid(axis="y", which="both", alpha=0.2, lw=0.5)
    axb.legend(loc="upper left", fontsize=8)

    fig.suptitle("Event-level per-subject breakdown at the two locked operating points\n"
                "(seed 42, baseline-of-record, SzCORE any-overlap scoring)", y=1.01, fontsize=10.5)
    fig.tight_layout()
    _save(fig, out_dir, "E2_persubject_breakdown")


# ----------------------------------------------------------------------------
def _save(fig, out_dir, name):
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(out_dir / f"{name}.{ext}", bbox_inches="tight")
    plt.close(fig)
    print(f"  [saved] {(out_dir / (name + '.png')).resolve()}")
    print(f"  [saved] {(out_dir / (name + '.pdf')).resolve()}")


# ============================================================================
def main():
    ap = argparse.ArgumentParser(description="E1 + E2 event-level figures (baseline-of-record, §0)")
    ap.add_argument("--csv", default="results/retrain_v3p1/final_eval_seed42.csv")
    ap.add_argument("--out_dir", default="docs/figures/event_level")
    ap.add_argument("--figure", choices=["e1", "e2", "both"], default="both")
    a = ap.parse_args()

    df = load_grid(a.csv)
    print(f"loaded grid: {df.shape[0]} rows, {df.subject.nunique()} subjects, "
         f"{df.mag_pct.nunique()} mag_pct x {df.pen_mult.nunique()} pen_mult")

    if a.figure in ("e1", "both"):
        print("\n[E1] operating curve ...")
        pooled = plot_e1(df, a.out_dir)
        for op in LOCKED_OPS:
            r = locate_locked(pooled, op)
            print(f"  check {op['key']}: sens={r.sensitivity:.4f} fp/day={r.fp_per_day:.2f} "
                 f"TP/FN/FP={int(r.tp)}/{int(r.fn)}/{int(r.fp)}")

    if a.figure in ("e2", "both"):
        print("\n[E2] per-subject breakdown ...")
        plot_e2(df, a.out_dir)

    print(f"\nDone -> {Path(a.out_dir).resolve()}")


if __name__ == "__main__":
    main()
