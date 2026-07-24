"""
================================================================================
 eval_multiseed.py  —  WEEK 1: calibrate the measuring instrument
================================================================================

PURPOSE
-------
Before optimizing anything (Weeks 3-4), we must know whether the EVENT-LEVEL
evaluation is a stable ruler or a noisy one. The only stochastic element in the
event tier is the bootstrap padding of post-ictal buffer windows inside
build_timeline (np.random.choice). That randomness propagates:

    padding -> smoothed timeline -> MAD variance s^2 -> beta = pen*s^2*log(n)
            -> PELT change points -> TP / FP / latency

This script re-runs the ENTIRE event tier N times with N different padding seeds
and reports how much the headline numbers (detection rate, FCP/h, latency) move.
It does NOT retrain the model and does NOT touch the GPU: it reads the cached
1-D ensemble scores produced by the pipeline and reuses the exact functions in
evaluation_protocol.py, so the event-level logic is identical.

WHAT THIS IS NOT
----------------
- Window-level metrics (AUROC, AUC-PR, Mann-Whitney) are computed on the raw
  ensemble scores with NO padding, so they are seed-independent. They are not
  recomputed here.
- This is NOT training-seed robustness (that is a Phase-B task and would require
  retraining). This isolates the cheap, evaluation-only randomness.

DECISION THIS RUN FEEDS
-----------------------
If detection rate swings by more than ~2 seizures (~3% of 76) across seeds at
the recommended operating points, the padding is a non-trivial noise source and
we will FREEZE it (deterministic padding) for the optimization phase so that
Week 3-4 interventions are measured on a clean, repeatable baseline. If the
swing is negligible, we proceed with a single seed and simply report the SD.

OUTPUTS (to --out_dir, default results/cpd/evaluation/multiseed)
----------------------------------------------------------------
  multiseed_runs.csv              one row per (seed, subject, pen_mult)
  multiseed_summary_macro.csv     per penalty: macro DR / FCP-h / latency
                                  mean +/- SD across seeds, and TP swing
  multiseed_summary_persubject.csv per (subject, penalty): TP / sensitivity /
                                  FCP-h mean +/- SD across seeds  <- shows WHICH
                                  subjects are unstable
  figures/fig_multiseed_macro_dr.{pdf,png}        DR spread per penalty
  figures/fig_multiseed_tp_persubject.{pdf,png}   TP spread per subject @ pen

USAGE
-----
  python eval_multiseed.py
  python eval_multiseed.py --n_seeds 20 --diag_pen 0.3
  python eval_multiseed.py --scores_dir results/cpd/scores \
         --summary_dir "F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary"

Requires evaluation_protocol.py in the same directory.
================================================================================
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import evaluation_protocol as E   # reuse identical event-tier logic


def load_scores(scores_dir, subj):
    i = Path(scores_dir) / f"{subj}_ens_inter.npy"
    c = Path(scores_dir) / f"{subj}_ens_ictal.npy"
    if not (i.exists() and c.exists()):
        return None, None
    return np.load(str(i)), np.load(str(c))


def run_one_seed(seed, scores_dir, summary_dir, fp_mode, verbose=True):
    """Run the full event tier for every test subject under one padding seed."""
    rows = []
    for subj in E.TEST_SUBJS:
        inter, ictal = load_scores(scores_dir, subj)
        if inter is None:
            if verbose:
                print(f"      {subj}: cache missing, skipped")
            continue
        if verbose:
            print(f"      {subj} ...", end="", flush=True)
        np.random.seed(seed)  # padding depends only on this seed (order-independent)
        timeline, is_ictal, sz_ranges, n_inter_h = E.build_timeline(
            subj, inter, ictal, summary_dir)
        if len(timeline) == 0:
            continue
        smoothed = pd.Series(timeline).rolling(
            window=15, min_periods=1, center=True).mean().values
        pelt = E.run_global_pelt_all(smoothed, E.PEN_MULTS)
        subj_tp_diag = None
        for pm in E.PEN_MULTS:
            cps, _ = pelt[pm]
            ev = E.event_scoring(cps, sz_ranges, n_inter_h, fp_mode=fp_mode)
            rows.append(dict(
                seed=seed, subject=subj, pen_mult=pm,
                n_seizures=len(sz_ranges), tp=ev["tp"], fp=ev["fp"], fn=ev["fn"],
                sensitivity=ev["sensitivity"], fcp_h=ev["fcp_h"],
                mean_lat_s=ev["mean_lat_s"]))
        if verbose:
            print(" done", flush=True)
    return rows


# ----------------------------------------------------------------------------
# Figures
# ----------------------------------------------------------------------------
def _save(fig, fig_dir, name):
    for ext in ("pdf", "png"):
        fig.savefig(Path(fig_dir) / f"{name}.{ext}", bbox_inches="tight")
    plt.close(fig)


def fig_macro_dr(macro, fig_dir):
    """Boxplot of macro detection rate across seeds, one box per penalty."""
    pens = sorted(macro["pen_mult"].unique())
    data = [macro.loc[macro.pen_mult == pm, "macro_dr"].values for pm in pens]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.boxplot(data, labels=[str(p) for p in pens], showmeans=True)
    ax.set_xlabel("PELT penalty multiplier")
    ax.set_ylabel("Macro detection rate (over 76 seizures)")
    ax.set_title("Event-level detection-rate stability across padding seeds")
    ax.grid(alpha=0.25, axis="y")
    _save(fig, fig_dir, "fig_multiseed_macro_dr")


def fig_tp_persubject(runs, diag_pen, fig_dir):
    """Boxplot of TP count per subject across seeds at the diagnostic penalty."""
    sub = runs[runs.pen_mult == diag_pen]
    subjs = E.TEST_SUBJS
    data, labels = [], []
    for s in subjs:
        v = sub.loc[sub.subject == s, "tp"].values
        if len(v):
            data.append(v); labels.append(s)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.boxplot(data, labels=labels, showmeans=True)
    # annotate ground-truth seizure count per subject
    for i, s in enumerate(labels):
        gt = int(sub.loc[sub.subject == s, "n_seizures"].iloc[0])
        ax.annotate(f"GT={gt}", (i + 1, gt), textcoords="offset points",
                    xytext=(0, 6), ha="center", fontsize=7, color="#999999")
    ax.set_xlabel("Subject")
    ax.set_ylabel(f"True positives @ pen={diag_pen}")
    ax.set_title(f"Per-subject TP stability across padding seeds (pen={diag_pen})")
    ax.grid(alpha=0.25, axis="y")
    _save(fig, fig_dir, "fig_multiseed_tp_persubject")


# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Week 1 multi-seed stability check")
    ap.add_argument("--scores_dir", default="results/cpd/scores")
    ap.add_argument("--summary_dir",
                    default=r"F:\Study\Thesis\Dataset\CHB-MIT\CHB info\summary")
    ap.add_argument("--out_dir", default="results/cpd/evaluation/multiseed")
    ap.add_argument("--n_seeds", type=int, default=10)
    ap.add_argument("--base_seed", type=int, default=0)
    ap.add_argument("--fp_mode", choices=["overlap", "strict"], default="overlap")
    ap.add_argument("--diag_pen", type=float, default=0.3,
                    help="penalty used for the per-subject TP figure")
    args = ap.parse_args()

    out = Path(args.out_dir)
    fig_dir = out / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    seeds = list(range(args.base_seed, args.base_seed + args.n_seeds))

    print("=" * 78)
    print(f"MULTI-SEED EVENT-LEVEL STABILITY  |  {args.n_seeds} seeds "
          f"({seeds[0]}..{seeds[-1]})  |  fp_mode={args.fp_mode}")
    print("Window-level metrics are seed-independent and not recomputed here.")
    print("=" * 78)

    all_rows = []
    out.mkdir(parents=True, exist_ok=True)
    ckpt_path = out / "multiseed_runs.csv"
    for k, s in enumerate(seeds):
        print(f"  seed {s:>3} ({k+1:>2}/{len(seeds)}):", flush=True)
        rows = run_one_seed(s, args.scores_dir, args.summary_dir, args.fp_mode)
        all_rows.extend(rows)
        # checkpoint after every seed so a Ctrl-C never loses completed work
        pd.DataFrame(all_rows).to_csv(ckpt_path, index=False)
        if rows:
            tp_tot = sum(r["tp"] for r in rows if r["pen_mult"] == args.diag_pen)
            sz_tot = sum(r["n_seizures"] for r in rows if r["pen_mult"] == args.diag_pen)
            print(f"    -> DR@pen{args.diag_pen:g} = {tp_tot}/{sz_tot} = "
                  f"{tp_tot/max(sz_tot,1):.1%}  [checkpoint saved: {k+1} seed(s)]",
                  flush=True)
        else:
            print(f"    -> no data (check --scores_dir / --summary_dir)", flush=True)

    runs = pd.DataFrame(all_rows)
    if runs.empty:
        print("\nNo results produced. Verify cached scores and summary paths.")
        return
    runs.to_csv(ckpt_path, index=False)

    # ---- macro per (seed, pen): DR = sum(tp)/sum(seizures) ----
    macro_rows = []
    for s in seeds:
        for pm in E.PEN_MULTS:
            d = runs[(runs.seed == s) & (runs.pen_mult == pm)]
            if d.empty:
                continue
            tp_tot, sz_tot = d.tp.sum(), d.n_seizures.sum()
            macro_rows.append(dict(
                seed=s, pen_mult=pm,
                macro_dr=tp_tot / max(sz_tot, 1),
                tp_total=int(tp_tot), sz_total=int(sz_tot),
                fcp_h_macro=d.fcp_h.mean(),
                lat_macro=np.nanmean(d.mean_lat_s.values)))
    macro = pd.DataFrame(macro_rows)

    # ---- summary across seeds, per penalty ----
    summ_rows = []
    for pm in E.PEN_MULTS:
        m = macro[macro.pen_mult == pm]
        if m.empty:
            continue
        summ_rows.append(dict(
            pen_mult=pm, sz_total=int(m.sz_total.iloc[0]),
            dr_mean=round(m.macro_dr.mean(), 4),
            dr_std=round(m.macro_dr.std(ddof=1), 4) if len(m) > 1 else 0.0,
            tp_mean=round(m.tp_total.mean(), 2),
            tp_min=int(m.tp_total.min()), tp_max=int(m.tp_total.max()),
            tp_swing=int(m.tp_total.max() - m.tp_total.min()),
            fcp_h_mean=round(m.fcp_h_macro.mean(), 3),
            fcp_h_std=round(m.fcp_h_macro.std(ddof=1), 3) if len(m) > 1 else 0.0,
            lat_mean=round(np.nanmean(m.lat_macro.values), 2),
            lat_std=round(np.nanstd(m.lat_macro.values), 2)))
    summ = pd.DataFrame(summ_rows)
    summ.to_csv(out / "multiseed_summary_macro.csv", index=False)

    # ---- per-subject TP variability ----
    ps_rows = []
    for subj in E.TEST_SUBJS:
        for pm in E.PEN_MULTS:
            d = runs[(runs.subject == subj) & (runs.pen_mult == pm)]
            if d.empty:
                continue
            ps_rows.append(dict(
                subject=subj, pen_mult=pm,
                n_seizures=int(d.n_seizures.iloc[0]),
                tp_mean=round(d.tp.mean(), 2),
                tp_std=round(d.tp.std(ddof=1), 3) if len(d) > 1 else 0.0,
                tp_min=int(d.tp.min()), tp_max=int(d.tp.max()),
                sens_mean=round(d.sensitivity.mean(), 4),
                sens_std=round(d.sensitivity.std(ddof=1), 4) if len(d) > 1 else 0.0,
                fcp_h_mean=round(d.fcp_h.mean(), 3),
                fcp_h_std=round(d.fcp_h.std(ddof=1), 3) if len(d) > 1 else 0.0))
    persubj = pd.DataFrame(ps_rows)
    persubj.to_csv(out / "multiseed_summary_persubject.csv", index=False)

    # ---- figures ----
    fig_macro_dr(macro, fig_dir)
    if args.diag_pen in set(runs.pen_mult.unique()):
        fig_tp_persubject(runs, args.diag_pen, fig_dir)

    # ---- console verdict (soft hint; final diagnosis done by advisor) ----
    print("\n" + "=" * 78)
    print("SUMMARY (macro across subjects, mean +/- SD over seeds)")
    print("=" * 78)
    print(f"{'pen':>5} {'DR':>16} {'TP range':>12} {'FCP/h':>14} {'latency_s':>14}")
    print("-" * 70)
    for _, r in summ.iterrows():
        print(f"{r['pen_mult']:>5g} "
              f"{r['dr_mean']*100:>6.1f} +/- {r['dr_std']*100:<5.1f}% "
              f"{r['tp_min']:>3}-{r['tp_max']:<3}/{r['sz_total']:<3} "
              f"{r['fcp_h_mean']:>6.2f} +/- {r['fcp_h_std']:<5.2f} "
              f"{r['lat_mean']:>6.1f} +/- {r['lat_std']:<5.1f}")

    # flag instability at the two recommended operating points
    flagged = summ[summ.pen_mult.isin([0.3, 0.5])]
    worst = int(flagged["tp_swing"].max()) if not flagged.empty else 0
    print("\nDIAGNOSTIC HINT:")
    if worst > 2:
        print(f"  TP swings up to {worst} seizures across seeds at pen 0.3/0.5.")
        print("  -> Padding is a NON-TRIVIAL noise source. Recommend FREEZING the")
        print("     bootstrap padding (deterministic) before Week 3-4 optimization.")
    else:
        print(f"  TP swings at most {worst} seizure(s) at pen 0.3/0.5.")
        print("  -> Padding noise is small; a single seed is acceptable, but report")
        print("     the SD for due diligence.")
    print(f"\nWrote CSVs + figures to: {out.resolve()}")


if __name__ == "__main__":
    main()