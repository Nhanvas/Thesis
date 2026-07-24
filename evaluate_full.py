"""
Full Evaluation Script — Two-Tier Assessment
=============================================
Tier 1: Window/Score-level  →  AUROC + AUPRC per subject
Tier 2: Event/CPD-level     →  Event Sensitivity, FAR/h, Event Precision, Mean Latency

Run entirely on local CPU (no GPU needed).
Requires:
  - results/cpd/scores/{subj}_ens_inter.npy  (cached ensemble scores)
  - results/cpd/scores/{subj}_ens_ictal.npy
  - results/cpd/cpd_results_v12_combined.csv  (existing CPD sweep output)
  - summary files in SUMMARY_DIR (for seizure count ground truth)

Output files:
  - results/eval/tier1_auroc_auprc.csv
  - results/eval/tier2_event_metrics.csv
  - results/eval/tier2_macro_summary.csv
  - figures/fig_auroc_auprc.png
  - figures/fig_event_tradeoff.png
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from pathlib import Path
from sklearn.metrics import roc_auc_score, average_precision_score, roc_curve, precision_recall_curve

# ── Paths (match your local project structure) ────────────────────────────────
SCORES_DIR  = Path("results/cpd/scores")
CPD_CSV     = Path("results/cpd/cpd_results_v12_combined.csv")
EVAL_DIR    = Path("results/eval");   EVAL_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR     = Path("figures");        FIG_DIR.mkdir(parents=True, exist_ok=True)

TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]

# Ground-truth seizure counts per subject (from CHB-MIT summary files).
# Used only for display cross-check; actual TP/FN come from cpd_results CSV.
GT_SEIZURES = {
    "chb03": 7, "chb06": 10, "chb13": 12, "chb14": 8,
    "chb15": 20, "chb16": 10, "chb17": 3,  "chb18": 6
}

# ═══════════════════════════════════════════════════════════════════════════════
# TIER 1  —  AUROC + AUPRC  (window / score level)
# ═══════════════════════════════════════════════════════════════════════════════

def compute_tier1(subjs, scores_dir):
    """
    Load cached ensemble scores (inter + ictal) and compute AUROC and AUPRC.
    These are threshold-independent metrics that assess the quality of the
    anomaly scoring model independently of PELT.
    """
    records = []
    roc_data = {}   # store curves for Figure 1
    prc_data = {}

    for subj in subjs:
        inter = np.load(scores_dir / f"{subj}_ens_inter.npy")
        ictal = np.load(scores_dir / f"{subj}_ens_ictal.npy")

        y_true  = np.concatenate([np.zeros(len(inter)), np.ones(len(ictal))])
        y_score = np.concatenate([inter, ictal])

        auroc = roc_auc_score(y_true, y_score)
        auprc = average_precision_score(y_true, y_score)

        # Store curves
        fpr, tpr, _ = roc_curve(y_true, y_score)
        prec, rec, _ = precision_recall_curve(y_true, y_score)

        roc_data[subj] = (fpr, tpr, auroc)
        prc_data[subj] = (rec, prec, auprc)   # note: sklearn returns prec, rec

        # Baseline precision (random classifier) = prevalence
        prevalence = y_true.mean()

        print(f"  {subj}: AUROC={auroc:.4f}  AUPRC={auprc:.4f}  "
              f"(n_inter={len(inter)}, n_ictal={len(ictal)}, prevalence={prevalence:.4f})")

        records.append({
            "subject":    subj,
            "n_inter":    len(inter),
            "n_ictal":    len(ictal),
            "prevalence": round(float(prevalence), 6),
            "AUROC":      round(float(auroc), 4),
            "AUPRC":      round(float(auprc), 4),
        })

    df = pd.DataFrame(records)

    # Macro averages (unweighted — each subject counts equally)
    macro_auroc = df["AUROC"].mean()
    macro_auprc = df["AUPRC"].mean()
    print(f"\n  Macro AUROC = {macro_auroc:.4f}   Macro AUPRC = {macro_auprc:.4f}")

    # Add macro row
    macro_row = {
        "subject": "MACRO", "n_inter": df["n_inter"].sum(),
        "n_ictal": df["n_ictal"].sum(),
        "prevalence": round(float(df["n_ictal"].sum() / (df["n_inter"].sum() + df["n_ictal"].sum())), 6),
        "AUROC": round(macro_auroc, 4),
        "AUPRC": round(macro_auprc, 4),
    }
    df = pd.concat([df, pd.DataFrame([macro_row])], ignore_index=True)

    return df, roc_data, prc_data


def plot_tier1(roc_data, prc_data, fig_dir):
    """
    Figure 1: Two-panel figure.
      Left panel  — ROC curves per subject + macro average
      Right panel — Precision-Recall curves per subject + macro average
    Publication-quality (Times New Roman, 300 dpi).
    """
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))

    # Colour palette — 8 subjects, distinct and print-safe
    colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
        "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"
    ]

    # ── Left: ROC ──────────────────────────────────────────────────────────────
    ax = axes[0]
    mean_fpr = np.linspace(0, 1, 500)
    interp_tprs = []

    for i, (subj, (fpr, tpr, auroc)) in enumerate(roc_data.items()):
        interp_tpr = np.interp(mean_fpr, fpr, tpr)
        interp_tprs.append(interp_tpr)
        ax.plot(fpr, tpr, color=colors[i], lw=1.2, alpha=0.75,
                label=f"{subj} (AUC={auroc:.3f})")

    mean_tpr = np.mean(interp_tprs, axis=0)
    mean_tpr[0] = 0.0
    macro_auroc = np.mean([v[2] for v in roc_data.values()])
    ax.plot(mean_fpr, mean_tpr, color="black", lw=2.0, linestyle="--",
            label=f"Macro avg (AUC={macro_auroc:.3f})")
    ax.plot([0, 1], [0, 1], "k:", lw=0.8, alpha=0.5)

    ax.set_xlim([0, 1]); ax.set_ylim([0, 1.02])
    ax.set_xlabel("False Positive Rate", fontsize=11)
    ax.set_ylabel("True Positive Rate", fontsize=11)
    ax.set_title("(a) Receiver Operating Characteristic (ROC)", fontsize=12, pad=8)
    ax.legend(fontsize=7.5, loc="lower right", framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle=":")
    ax.set_aspect("equal", adjustable="box")

    # ── Right: PRC ─────────────────────────────────────────────────────────────
    ax = axes[1]
    for i, (subj, (rec, prec, auprc)) in enumerate(prc_data.items()):
        ax.plot(rec, prec, color=colors[i], lw=1.2, alpha=0.75,
                label=f"{subj} (AUPRC={auprc:.3f})")

    macro_auprc = np.mean([v[2] for v in prc_data.values()])

    # Baseline (random classifier) = prevalence
    all_ictal  = sum(len(np.load(SCORES_DIR / f"{s}_ens_ictal.npy")) for s in roc_data)
    all_total  = all_ictal + sum(len(np.load(SCORES_DIR / f"{s}_ens_inter.npy")) for s in roc_data)
    prevalence = all_ictal / all_total
    ax.axhline(y=prevalence, color="gray", linestyle=":", lw=1.0,
               label=f"Baseline (prevalence={prevalence:.4f})")

    ax.set_xlim([0, 1]); ax.set_ylim([0, 1.02])
    ax.set_xlabel("Recall", fontsize=11)
    ax.set_ylabel("Precision", fontsize=11)
    ax.set_title(f"(b) Precision-Recall Curve  [Macro AUPRC={macro_auprc:.3f}]",
                 fontsize=12, pad=8)
    ax.legend(fontsize=7.5, loc="upper right", framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle=":")

    fig.suptitle(
        "Tier 1 — Window-Level Score Quality (Ensemble Anomaly Score)\n"
        "GAE Reconstruction + Temporal LSTM + Gamma AEC",
        fontsize=12, y=1.01
    )
    fig.tight_layout()
    out = fig_dir / "fig_auroc_auprc.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved → {out}")


# ═══════════════════════════════════════════════════════════════════════════════
# TIER 2  —  Event-Level CPD Metrics
# ═══════════════════════════════════════════════════════════════════════════════

def compute_tier2(cpd_csv):
    """
    From the existing CPD sweep CSV, derive:
      - Event Sensitivity   = TP / (TP + FN)          [already in CSV as det_rate]
      - FAR/h               = FP_events / n_inter_h    [fcp_h in CSV — renamed here]
      - Event Precision     = TP / (TP + FP_events)    [new column]
      - Mean Latency (s)    [already in CSV as mean_lat_s]

    Naming note:
      fcp_h in the existing CSV stores FP_events / n_inter_h.
      This is identical to False Alarm Rate per hour (FAR/h) used in:
        - Chung et al. 2024 (Frontiers in Neurology)
        - Ingolfsson et al. 2024 (Scientific Reports)
        - Ziyabari et al. 2019 (IEEE J. Biomed. Health Inform.)
      We rename it FAR_h to match literature convention.
    """
    df = pd.read_csv(cpd_csv)

    # ── Derive FP_events from TP, FN, n_inter_h, fcp_h ──────────────────────
    # fcp_h = FP_events / n_inter_h  →  FP_events = fcp_h * n_inter_h
    df["fp_events"] = (df["fcp_h"] * df["n_inter_h"]).round().astype(int)
    df["FAR_h"]     = df["fcp_h"]           # rename for clarity
    df["event_precision"] = df["tp"] / (df["tp"] + df["fp_events"]).clip(lower=1)
    df["event_precision"] = df["event_precision"].round(4)

    # ── Per-subject table at selected operating points ─────────────────────────
    records = []
    for subj in TEST_SUBJS:
        sub = df[df["subject"] == subj].set_index("pen_mult")
        for pm in [0.3, 0.5, 1.0, 2.0]:
            if pm not in sub.index:
                continue
            row = sub.loc[pm]
            records.append({
                "subject":          subj,
                "pen_mult":         pm,
                "n_seizures_gt":    int(row["n_seizures"]),
                "TP":               int(row["tp"]),
                "FN":               int(row["fn"]),
                "FP_events":        int(row["fp_events"]),
                "Event_Sensitivity":round(float(row["det_rate"]), 4),
                "FAR_h":            round(float(row["FAR_h"]), 2),
                "Event_Precision":  round(float(row["event_precision"]), 4),
                "Mean_Latency_s":   row["mean_lat_s"],
                "n_inter_h":        round(float(row["n_inter_h"]), 2),
                "AUROC":            round(float(row["auroc"]), 4),
            })

    per_subj_df = pd.DataFrame(records)
    return df, per_subj_df


def compute_tier2_macro(df):
    """
    Macro-level summary: aggregate TP, FN, FP across all 8 subjects at each pen_mult.
    Returns one row per pen_mult.
    """
    pen_multipliers = sorted(df["pen_mult"].unique())
    macro_rows = []

    for pm in pen_multipliers:
        sub = df[df["pen_mult"] == pm]
        tp_sum  = sub["tp"].sum()
        fn_sum  = sub["fn"].sum()
        fp_sum  = sub["fp_events"].sum()
        gt_sum  = (sub["tp"] + sub["fn"]).sum()
        h_sum   = sub["n_inter_h"].sum()

        sens  = tp_sum / max(gt_sum, 1)
        far_h = fp_sum / max(h_sum, 1e-6)
        prec  = tp_sum / max(tp_sum + fp_sum, 1)
        lats  = sub["mean_lat_s"].dropna()

        macro_rows.append({
            "pen_mult":              pm,
            "TP_total":              int(tp_sum),
            "GT_total":              int(gt_sum),
            "FP_total":              int(fp_sum),
            "Event_Sensitivity":     round(sens, 4),
            "FAR_h":                 round(far_h, 2),
            "Event_Precision":       round(prec, 4),
            "Mean_Latency_s":        round(float(lats.mean()), 1) if len(lats) else None,
            "Mean_AUROC":            round(float(sub["auroc"].mean()), 4),
        })

    macro_df = pd.DataFrame(macro_rows)
    return macro_df


def plot_tier2(macro_df, fig_dir):
    """
    Figure 2: Two-panel trade-off figure.
      Left panel  — Event Sensitivity vs FAR/h  (trade-off curve as pen_mult varies)
      Right panel — Event Sensitivity vs Event Precision
    Points labelled with pen_mult value.
    """
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))

    pm_vals = macro_df["pen_mult"].values
    sens    = macro_df["Event_Sensitivity"].values * 100   # convert to %
    far_h   = macro_df["FAR_h"].values
    prec    = macro_df["Event_Precision"].values * 100

    # ── Left: Sensitivity vs FAR/h ─────────────────────────────────────────────
    ax = axes[0]
    ax.plot(far_h, sens, "o-", color="#1f77b4", lw=2, markersize=8, zorder=3)

    for x, y, pm in zip(far_h, sens, pm_vals):
        ax.annotate(
            f"  β×{pm}", (x, y),
            fontsize=8.5, va="center", color="#333333"
        )

    # Mark recommended operating point (pen=0.5)
    idx_05 = list(pm_vals).index(0.5)
    ax.scatter([far_h[idx_05]], [sens[idx_05]], s=120, color="red",
               zorder=5, label=f"Recommended (β×0.5): "
                               f"Sens={sens[idx_05]:.1f}%, FAR/h={far_h[idx_05]:.1f}")

    ax.set_xlabel("False Alarm Rate per Hour (FAR/h)", fontsize=11)
    ax.set_ylabel("Event Sensitivity (%)", fontsize=11)
    ax.set_title("(a) Sensitivity – FAR/h Trade-off\n(BIC penalty multiplier varies)", fontsize=12)
    ax.legend(fontsize=9, loc="lower right")
    ax.grid(True, alpha=0.3, linestyle=":")
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f%%'))
    ax.set_ylim([35, 92])
    ax.set_xlim([0, None])

    # ── Right: Sensitivity vs Precision ────────────────────────────────────────
    ax = axes[1]
    ax.plot(prec, sens, "s-", color="#2ca02c", lw=2, markersize=8, zorder=3)

    for x, y, pm in zip(prec, sens, pm_vals):
        ax.annotate(
            f"  β×{pm}", (x, y),
            fontsize=8.5, va="center", color="#333333"
        )

    ax.scatter([prec[idx_05]], [sens[idx_05]], s=120, color="red",
               zorder=5, label=f"Recommended (β×0.5): "
                               f"Sens={sens[idx_05]:.1f}%, Prec={prec[idx_05]:.1f}%")

    ax.set_xlabel("Event Precision (%)", fontsize=11)
    ax.set_ylabel("Event Sensitivity (%)", fontsize=11)
    ax.set_title("(b) Sensitivity – Precision Trade-off\n(BIC penalty multiplier varies)", fontsize=12)
    ax.legend(fontsize=9, loc="lower right")
    ax.grid(True, alpha=0.3, linestyle=":")
    ax.xaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f%%'))
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f%%'))
    ax.set_ylim([35, 92])

    fig.suptitle(
        "Tier 2 — Event-Level CPD Localization Quality\n"
        "PELT (L2-cost, MAD penalty) on 76 annotated seizures, 8 test subjects",
        fontsize=12, y=1.01
    )
    fig.tight_layout()
    out = fig_dir / "fig_event_tradeoff.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved → {out}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 65)
    print("TIER 1 — Window-Level Score Quality (AUROC + AUPRC)")
    print("=" * 65)
    tier1_df, roc_data, prc_data = compute_tier1(TEST_SUBJS, SCORES_DIR)
    tier1_df.to_csv(EVAL_DIR / "tier1_auroc_auprc.csv", index=False)
    print(f"  Saved → {EVAL_DIR}/tier1_auroc_auprc.csv")
    plot_tier1(roc_data, prc_data, FIG_DIR)

    print()
    print("=" * 65)
    print("TIER 2 — Event-Level CPD Metrics (FAR/h, Precision, Latency)")
    print("=" * 65)
    df_full, per_subj_df = compute_tier2(CPD_CSV)
    macro_df = compute_tier2_macro(df_full)

    per_subj_df.to_csv(EVAL_DIR / "tier2_event_metrics.csv", index=False)
    macro_df.to_csv(EVAL_DIR / "tier2_macro_summary.csv", index=False)
    print(f"  Saved → {EVAL_DIR}/tier2_event_metrics.csv")
    print(f"  Saved → {EVAL_DIR}/tier2_macro_summary.csv")

    print("\n  MACRO SUMMARY (all 8 subjects):")
    print(f"  {'pen':>5} {'TP/GT':>7} {'Sens':>7} {'FAR/h':>7} {'Prec':>7} {'Lat_s':>7}")
    print("  " + "-" * 45)
    for _, row in macro_df.iterrows():
        lat = f"{row['Mean_Latency_s']:.1f}" if row['Mean_Latency_s'] is not None else "  —"
        print(f"  {row['pen_mult']:>5.1f}  "
              f"{row['TP_total']:>3}/{row['GT_total']:<3} "
              f"{row['Event_Sensitivity']*100:>5.1f}%  "
              f"{row['FAR_h']:>7.2f}  "
              f"{row['Event_Precision']*100:>5.1f}%  "
              f"{lat:>7}")

    plot_tier2(macro_df, FIG_DIR)

    print()
    print("=" * 65)
    print("ALL DONE.")
    print(f"  CSV  → results/eval/")
    print(f"  Figs → figures/fig_auroc_auprc.png")
    print(f"         figures/fig_event_tradeoff.png")
    print("=" * 65)


if __name__ == "__main__":
    main()