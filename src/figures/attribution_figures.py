#!/usr/bin/env python
"""
attribution_figures.py — report figures for the channel-attribution chapter.

READS ONLY THE COMMITTED CSVs in results/attribution_v6/. It recomputes nothing, so a figure can
never disagree with the numbers in ATTRIBUTION_SPEC.md §9 / RESULTS_OF_RECORD_phaseB.md §10.
If a number looks wrong here, the CSV is wrong — fix the CSV by rerunning
`src/attribution_pipeline.py`, never by editing this file.

Usage (from repo ROOT):
    python src/figures/attribution_figures.py

Outputs -> figures/ (root, exhibit-numbered) and tables/csv/ for the appendix table
(moved from results/report_tables/ by docs/FIGURE_ROUND6.md §2),
per docs/FIGURE_FIXES_R3.md §2 (renamed off the old figures/attribution/ working names so a
writer looking for the figure by its report number can find it):

    fig3_11_attribution_synthetic.png        LABEL-FREE.  macro-AUROC vs injection strength, VAL + TEST.
                                          Rubric #6 (validity) and #8. The single strongest visual
                                          exhibit that the machinery is correct: clean null at a=1.0,
                                          monotone rise, ceiling at a=3.0.
    fig3_12_attribution_seed_stability.png  LABEL-FREE.  Channel-ranking agreement across GAE seeds
                                          {42,1,2,3}. Rubric #6.
    fig3_13_attribution_rank_heatmap.png     LABEL-FREE.  Per-seizure channel RANK (1..18) for all 76
                                          TEST seizures, grouped by subject. Rank is scale-free, so
                                          seizures are directly comparable. Rubric #7, #8.
    fig3_14_attribution_persubject_forest.png
                                          PROVISIONAL (uses draft labels). Per-subject AUROC with
                                          bootstrap CI, against the macro and the D7 control. Replaces
                                          the AUROC-vs-|S| scatter: the on-disk labels give |S| in
                                          {1,2} only (SPEC §3.3), so a trend over |S| is not
                                          estimable. Rerun if the labels are frozen.
    tables/csv/table_A7_top_channels.csv
                                          LABEL-FREE.  Appendix table: top-3 channels per seizure.

Figures 1-3 and the table never need redoing. Only fig 4 depends on the label freeze.
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emit_tables  # for render_markdown, docs/FIGURE_ROUND6.md §3

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SRC = ROOT / "results" / "attribution_v6"
OUT = ROOT / "figures"
TABLE_OUT = ROOT / "tables" / "csv"
CH = ["FP1-F7", "F7-T7", "T7-P7", "P7-O1", "FP1-F3", "F3-C3", "C3-P3", "P3-O1",
      "FP2-F4", "F4-C4", "C4-P4", "P4-O2", "FP2-F8", "F8-T8", "T8-P8", "P8-O2",
      "FZ-CZ", "CZ-PZ"]
TEST_SUBJ = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
SEEDS = [42, 1, 2, 3]
DPI = 200


def die(m):
    print(f"\n[FATAL] {m}\n", file=sys.stderr)
    sys.exit(1)


def read(name):
    f = SRC / name
    if not f.is_file():
        die(f"missing {f} — run: python src/attribution_pipeline.py all")
    return list(csv.DictReader(open(f)))


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / name
    fig.savefig(p, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {p}")


# ---------------------------------------------------------------- fig 1
def fig1_synthetic():
    rows = read("synthetic_sanity.csv")
    sizes = sorted({int(r["n_injected"]) for r in rows})
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for ax, panel in zip(axes, ["VAL", "TEST"]):
        for k in sizes:
            sel = sorted((float(r["alpha"]), float(r["macro_AUROC"]))
                         for r in rows if r["panel"] == panel and int(r["n_injected"]) == k)
            ax.plot([a for a, _ in sel], [v for _, v in sel], "o-", ms=4, lw=1.4,
                    label=f"|S| = {k}")
        nulls = [float(r["null_mean"]) for r in rows if r["panel"] == panel]
        ax.axhline(0.5, color="0.4", ls="--", lw=1)
        ax.text(2.55, 0.512, f"permutation null\n{min(nulls):.4f}–{max(nulls):.4f}",
                fontsize=7.5, color="0.35", ha="center")
        ax.set_xlabel("injection strength  α  (multiplier on reconstruction error)")
        ax.set_title(f"{panel}" + ("  (pre-registered gate)" if panel == "VAL"
                                   else "  (confirmatory)"), fontsize=10)
        ax.set_ylim(0.42, 1.02)
        ax.grid(alpha=0.25, lw=0.6)
    axes[0].set_ylabel("macro-AUROC over 200 pseudo-seizures")
    axes[1].legend(fontsize=8, frameon=False, loc="lower right")
    fig.suptitle("Synthetic channel-anomaly injection: the attribution score recovers a known "
                 "ground truth", fontsize=11.5)
    save(fig, "fig3_11_attribution_synthetic.png")


# ---------------------------------------------------------------- shared loader
def load_scores(agg="p95"):
    S = defaultdict(lambda: np.zeros(18))
    nwin = {}
    for r in read("attribution_scores.csv"):
        if r["agg"] != agg:
            continue
        key = (int(r["seed"]), r["subject"], int(r["seizure_idx"]))
        S[key][int(r["ch_idx"])] = float(r["score"])
        nwin[(r["subject"], int(r["seizure_idx"]))] = int(r["n_windows"])
    return dict(S), nwin


# ---------------------------------------------------------------- fig 2
def fig2_seed_robustness():
    from scipy.stats import spearmanr
    S, _ = load_scores()
    keys = sorted({(s, k) for (sd, s, k) in S if sd == 42})
    rho, agree = [], []
    for (s, k) in keys:
        v = [S[(sd, s, k)] for sd in SEEDS]
        rho += [spearmanr(v[0], v[i]).statistic for i in range(1, len(v))]
        t = [int(np.argmax(x)) for x in v]
        agree.append(sum(1 for x in t[1:] if x == t[0]) / (len(SEEDS) - 1))

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.8))
    a1.hist(rho, bins=24, color="#4878a8", edgecolor="white")
    a1.axvline(np.mean(rho), color="#c04040", lw=1.6)
    a1.set_xlabel("Spearman ρ, seed 42 vs seeds 1/2/3")
    a1.set_ylabel("seizure × seed pairs")
    a1.set_title(f"ranking agreement:  ρ = {np.mean(rho):.3f} ± {np.std(rho):.3f}", fontsize=10)
    a1.grid(alpha=0.25, lw=0.6)

    frac = [np.mean([x == 1.0 for x in agree]),
            np.mean([(x > 0) and (x < 1.0) for x in agree]),
            np.mean([x == 0.0 for x in agree])]
    a2.bar(["all 3 seeds\nagree", "partial", "none\nagree"], frac,
           color=["#4c8c4a", "#d8a23a", "#b05050"], edgecolor="white")
    for i, v in enumerate(frac):
        a2.text(i, v + 0.015, f"{v*100:.0f}%", ha="center", fontsize=9)
    a2.set_ylim(0, 1.05)
    a2.set_ylabel("fraction of 76 seizures")
    a2.set_title(f"top-1 channel agreement  (mean {np.mean(agree):.3f})", fontsize=10)
    a2.grid(alpha=0.25, lw=0.6, axis="y")

    fig.suptitle("Channel attribution is stable across GAE random seeds", fontsize=11.5)
    save(fig, "fig3_12_attribution_seed_stability.png")


# ---------------------------------------------------------------- fig 3
def fig3_rank_heatmap():
    S, nwin = load_scores()
    keys = [k for k in sorted(S) if k[0] == 42]
    order = sorted(((s, i) for (_, s, i) in keys), key=lambda x: (TEST_SUBJ.index(x[0]), x[1]))
    M = np.zeros((len(order), 18))
    for r, (s, i) in enumerate(order):
        v = S[(42, s, i)]
        rk = np.empty(18)
        rk[np.argsort(-v)] = np.arange(1, 19)
        M[r] = rk

    fig, ax = plt.subplots(figsize=(9.5, 12))
    im = ax.imshow(M, aspect="auto", cmap="viridis_r", vmin=1, vmax=18,
                   interpolation="nearest")
    ax.set_xticks(range(18))
    ax.set_xticklabels(CH, rotation=90, fontsize=8)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([f"{s} sz{i}" for s, i in order], fontsize=6)
    for b in np.cumsum([sum(1 for s, _ in order if s == t) for t in TEST_SUBJ])[:-1]:
        ax.axhline(b - 0.5, color="w", lw=1.6)
    for b in (3.5, 7.5, 11.5, 15.5):
        ax.axvline(b, color="w", lw=0.9, alpha=0.65)
    cb = fig.colorbar(im, ax=ax, fraction=0.030, pad=0.02)
    cb.set_label("channel rank within the seizure  (1 = most anomalous)")
    ax.set_title("Per-seizure channel ranking, GAE reconstruction anomaly\n"
                 "76 TEST seizures × 18 channels, seed 42, p95 aggregation", fontsize=11)
    save(fig, "fig3_13_attribution_rank_heatmap.png")


# ---------------------------------------------------------------- fig 4
def fig4_persubject_forest():
    """Per-subject AUROC + CI vs the macro line and the D7 control.

    Replaces the AUROC-vs-|S| scatter: the label file is dominant-channel, so |S| only takes the
    values 1 and 2 and no trend can be shown (ATTRIBUTION_SPEC §3.3).
    """
    rows = read("attribution_summary.csv")
    per = read("attribution_perseizure.csv")

    def get(panel):
        for r in rows:
            if r["panel"] == panel:
                return r
        return None

    entries = []
    for label, panel in [("all labelled  (n=36)", "ALL focal (D5 primary)"),
                         ("excluding chb15  (n=16)", "focal excl. chb15"),
                         ("chb15 only  (n=20)", "chb15 only")]:
        r = get(panel)
        if r:
            entries.append((label, float(r["macro_AUROC"]), float(r["AUROC_CI_lo"]),
                            float(r["AUROC_CI_hi"]), float(r["AUROC_subject_ctrl"]), True))
    entries.append((None, None, None, None, None, None))          # separator
    for s_ in TEST_SUBJ:
        r = get(f"subject {s_}")
        n = sum(1 for x in per if x["subject"] == s_)
        if r:
            entries.append((f"{s_}  (n={n})", float(r["macro_AUROC"]), float(r["AUROC_CI_lo"]),
                            float(r["AUROC_CI_hi"]), float(r["AUROC_subject_ctrl"]), False))
        elif n == 1:
            v = float(next(x["AUROC"] for x in per if x["subject"] == s_))
            entries.append((f"{s_}  (n=1, no CI)", v, v, v, None, False))

    macro = float(get("ALL focal (D5 primary)")["macro_AUROC"])
    ctrl = float(get("ALL focal (D5 primary)")["AUROC_subject_ctrl"])

    fig, ax = plt.subplots(figsize=(8.4, 5.4))
    ys, labels = [], []
    for idx, e in enumerate(reversed(entries)):
        if e[0] is None:
            continue
        lab, v, lo, hi, c, pooled = e
        y = idx
        ys.append(y); labels.append(lab)
        ax.errorbar(v, y, xerr=[[v - lo], [hi - v]], fmt="o", ms=7 if pooled else 5.5,
                    color="#20406a" if pooled else "#4878a8", ecolor="0.55",
                    elinewidth=1.3, capsize=3, zorder=3)
        if c is not None:
            ax.plot(c, y, "D", ms=6, mfc="none", mec="#c07000", mew=1.5, zorder=4)

    ax.axvline(0.5, color="0.45", ls="--", lw=1)
    ax.axvline(macro, color="#c04040", lw=1.3)
    ax.axvline(ctrl, color="#c07000", lw=1.1, ls=":")
    ax.text(0.5, len(entries) + 0.15, "chance", color="0.4", fontsize=8, ha="center")
    ax.text(macro, len(entries) + 0.15, f"macro {macro:.4f}", color="#c04040", fontsize=8,
            ha="center")
    ax.text(ctrl, len(entries) + 0.55, f"D7 control {ctrl:.4f}", color="#c07000", fontsize=8,
            ha="center")

    ax.set_yticks(ys); ax.set_yticklabels(labels, fontsize=9)
    ax.set_ylim(-0.8, len(entries) + 1.1)
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("macro-AUROC over seizures  (bootstrap 95% CI; ◇ = subject-constant control)")
    ax.grid(alpha=0.25, lw=0.6, axis="x")
    ax.set_title("Attribution vs the reader's dominant channel — PROVISIONAL\n"
                 "draft labels are dominant-channel (1-2 per seizure), not the full ictal set",
                 fontsize=10.5)
    save(fig, "fig3_14_attribution_persubject_forest.png")


# ---------------------------------------------------------------- appendix table
def table_top3():
    S, nwin = load_scores()
    out = []
    for (sd, s, i) in sorted(S):
        if sd != 42:
            continue
        v = S[(sd, s, i)]
        top = np.argsort(-v)[:3]
        out.append({"subject": s, "seizure_idx": i, "n_windows": nwin[(s, i)],
                    "rank1_channel": CH[top[0]], "rank1_score": round(float(v[top[0]]), 4),
                    "rank2_channel": CH[top[1]], "rank2_score": round(float(v[top[1]]), 4),
                    "rank3_channel": CH[top[2]], "rank3_score": round(float(v[top[2]]), 4)})
    TABLE_OUT.mkdir(parents=True, exist_ok=True)
    p = TABLE_OUT / "table_A7_top_channels.csv"
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print(f"  wrote {p}  ({len(out)} seizures)")

    import pandas as pd
    df = pd.DataFrame(out)
    emit_tables.render_markdown(df, {
        "subject": "Patient", "seizure_idx": "Seizure index", "n_windows": "Ictal windows",
        "rank1_channel": "Rank-1 channel", "rank1_score": "Rank-1 score",
        "rank2_channel": "Rank-2 channel", "rank2_score": "Rank-2 score",
        "rank3_channel": "Rank-3 channel", "rank3_score": "Rank-3 score"}, p)


if __name__ == "__main__":
    print("reading committed CSVs from results/attribution_v6/ — nothing is recomputed\n")
    fig1_synthetic()
    fig2_seed_robustness()
    fig3_rank_heatmap()
    fig4_persubject_forest()
    table_top3()
    print("\nDONE. Figures 1-3 and the CSV are LABEL-FREE and final.")
    print("Figure 4 is PROVISIONAL — rerun after the supervisor freezes the labels.")