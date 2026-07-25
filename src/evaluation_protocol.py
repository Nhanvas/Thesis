"""
================================================================================
 evaluation_protocol.py
 Two-tier (sample-based + event-based) evaluation for the unsupervised
 GAE + ensemble + PELT seizure-onset localization pipeline (CHB-MIT).
================================================================================

WHY THIS FILE EXISTS
--------------------
The production pipeline (cpd_pipeline_v13.py) already SCORES the EEG and runs
PELT. This file does NOT re-score anything. It consumes the cached 1-D ensemble
scores produced by v13:

    results/cpd/scores/{subject}_ens_inter.npy   (real interictal windows)
    results/cpd/scores/{subject}_ens_ictal.npy   (real ictal windows)

and produces a publication-grade, SzCORE-aligned evaluation in two tiers:

  TIER 1 — SAMPLE-BASED (a.k.a. window-level), measured on the RAW ensemble
           scores BEFORE PELT. Answers: "can the score separate ictal from
           interictal windows?"
           Metrics: AUROC (+DeLong 95% CI), AUC-PR / Average Precision
           (+bootstrap 95% CI), and at an UNSUPERVISED operating threshold
           (interictal percentile, no ictal labels): sensitivity (recall),
           specificity, precision, F1, FPR. Plus Mann-Whitney U + effect size.

  TIER 2 — EVENT-BASED, measured on the reconstructed timeline AFTER PELT.
           Answers: "does the system localize seizure onsets as clinical
           events?" Metrics: event sensitivity (detection rate), event
           precision, event F1, false positives per hour (FCP/h) AND per 24 h
           (+exact Poisson 95% CI), mean detection latency.

DESIGN PRINCIPLES (so this survives a committee / Q2-Q3 reviewer)
-----------------------------------------------------------------
1. Unsupervised at run time. Annotations are used ONLY to score results, never
   to set thresholds or make detection decisions. The operating threshold is
   the q-th percentile of the INTERICTAL score distribution (negative class
   only) -> no ictal label ever touches the decision rule.
2. Dual reporting (SzCORE, Dan et al., Epilepsia 2024). Both tiers are always
   reported together; reporting only one is misleading under ~0.2% prevalence.
3. AUC-PR is reported alongside AUROC because AUROC is optimistic under extreme
   class imbalance.
4. Every headline number carries an interval: DeLong CI (AUROC), bootstrap CI
   (AUC-PR), exact Poisson CI (false-alarm rate), and cross-subject mean +/- SD.
5. The timeline reconstruction and PELT call are mirrored VERBATIM from v13 so
   event-level numbers reproduce exactly; v13 remains the source of truth.

OUTPUTS (written to --out_dir, default: results/cpd/evaluation)
---------------------------------------------------------------
  eval_window_level.csv     per-subject Tier-1 metrics + CIs
  eval_event_level.csv      per-subject x penalty Tier-2 metrics + CIs
  eval_summary.csv          macro mean +/- SD headline table
  eval_stat_tests.csv       Mann-Whitney U, p, effect size r per subject
  figures/                  one figure per file (ROC, PR, trade-off, bars,
                            representative timeline)

USAGE
-----
  python evaluation_protocol.py
  python evaluation_protocol.py --op_percentile 99 --rep_subject chb18
  python evaluation_protocol.py --scores_dir results/cpd/scores \
         --summary_dir "F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary"

No PyTorch / torch_geometric needed: this layer is pure numpy/scipy/ruptures.
================================================================================
"""

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd
import ruptures as rpt
from scipy import stats
from sklearn.metrics import (roc_auc_score, average_precision_score,
                             roc_curve, precision_recall_curve)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------------
# CONFIG (mirrors cpd_pipeline_v13.py; override via argparse)
# ----------------------------------------------------------------------------
WIN_SEC      = 4          # window length (s)
BUFFER_H     = 4          # post-ictal exclusion buffer (h)
TOLERANCE_S  = 30         # +/- tolerance around onset for an event TP (s)
MERGE_GAP_S  = 32         # merge predicted CPs closer than this into one event
TEST_SUBJS   = ["chb03", "chb06", "chb13", "chb14",
                "chb15", "chb16", "chb17", "chb18"]
PEN_MULTS    = [0.3, 0.5, 1.0, 2.0, 5.0, 10.0]
SEED         = 42

# serif look to match the Times-New-Roman thesis body (DejaVu Serif fallback)
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 120,
})


# ============================================================================
# SECTION 1 — TIMELINE RECONSTRUCTION + PELT  (mirrored verbatim from v13)
# ----------------------------------------------------------------------------
# These reproduce v13's event-level signal EXACTLY. Do not "improve" them here;
# any change would desynchronize evaluation from the locked pipeline.
# ============================================================================
def parse_time_hms(t):
    p = t.strip().split(":")
    return int(p[0]) * 3600 + int(p[1]) * 60 + int(p[2])


def parse_summary_edf_list(summary_path):
    text = Path(summary_path).read_text()
    pat = re.compile(
        r'File Name:\s*(\S+\.edf)\s+File Start Time:\s*(\S+)\s+'
        r'File End Time:\s*(\S+)\s+Number of Seizures in File:\s*(\d+)(.*?)(?=File Name:|$)',
        re.DOTALL)
    edfs = []
    for m in pat.finditer(text):
        fname, t0, t1, nsz, rest = m.groups()
        dur = parse_time_hms(t1) - parse_time_hms(t0)
        if dur <= 0:
            dur += 86400
        szs = []
        if int(nsz) > 0:
            ons = [int(x) for x in re.findall(r'Seizure.*?Start Time.*?:\s*(\d+)', rest, re.I)]
            ofs = [int(x) for x in re.findall(r'Seizure.*?End Time.*?:\s*(\d+)',   rest, re.I)]
            szs = list(zip(ons, ofs))
        edfs.append({'fname': fname, 'duration_s': dur, 'seizures': szs})
    edfs.sort(key=lambda x: x['fname'])
    return edfs


def build_timeline(subj, inter_scores, ictal_scores, summary_dir):
    """Chronological 1-D timeline reconstruction with bootstrap-padded buffers.
    Returns (timeline, is_ictal, sz_ranges, n_inter_h). Verbatim from v13."""
    edfs = parse_summary_edf_list(Path(summary_dir) / f"{subj}-summary.txt")
    scores_out, is_ictal_out = [], []
    inter_ptr = ictal_ptr = 0
    total_inter_s = 0.0
    bootstrap_pool = np.random.choice(inter_scores, size=250000, replace=True)
    boot_ptr = 0

    for edf in edfs:
        dur = edf['duration_s']
        n_win = dur // WIN_SEC
        labels = np.zeros(dur, dtype=np.int8)
        buf = np.zeros(dur, dtype=bool)
        for (on, off) in edf['seizures']:
            on = min(on, dur); off = min(off, dur)
            labels[on:off] = 1
            buf[off:min(dur, off + BUFFER_H * 3600)] = True
        truncated_len = n_win * WIN_SEC
        window_labels = labels[:truncated_len].reshape(n_win, WIN_SEC).max(axis=1)
        window_buf    = buf[:truncated_len].reshape(n_win, WIN_SEC).any(axis=1)

        for w in range(n_win):
            lbl = int(window_labels[w]); bfr = bool(window_buf[w])
            if lbl == 1:
                if ictal_ptr < len(ictal_scores):
                    scores_out.append(float(ictal_scores[ictal_ptr])); ictal_ptr += 1
                else:
                    scores_out.append(0.0)
                is_ictal_out.append(True)
            elif bfr:
                scores_out.append(float(bootstrap_pool[boot_ptr]))
                boot_ptr = (boot_ptr + 1) % len(bootstrap_pool)
                is_ictal_out.append(False); total_inter_s += WIN_SEC
            else:
                if inter_ptr < len(inter_scores):
                    scores_out.append(float(inter_scores[inter_ptr])); inter_ptr += 1
                else:
                    scores_out.append(float(bootstrap_pool[boot_ptr]))
                    boot_ptr = (boot_ptr + 1) % len(bootstrap_pool)
                is_ictal_out.append(False); total_inter_s += WIN_SEC

    if inter_ptr < len(inter_scores):
        diff = len(inter_scores) - inter_ptr
        scores_out = np.concatenate([scores_out, inter_scores[inter_ptr:]])
        is_ictal_out.extend([False] * diff)
        total_inter_s += diff * WIN_SEC

    scores_out = np.array(scores_out, dtype=np.float32)
    is_ictal = np.array(is_ictal_out, dtype=bool)

    sz_ranges, in_s, ss_idx = [], False, 0
    for i, ic in enumerate(is_ictal):
        if ic and not in_s:
            ss_idx = i; in_s = True
        elif not ic and in_s:
            sz_ranges.append((ss_idx, i)); in_s = False
    if in_s:
        sz_ranges.append((ss_idx, len(is_ictal)))

    return scores_out, is_ictal, sz_ranges, total_inter_s / 3600.0


def run_global_pelt_all(signal, pen_multipliers):
    """PELT (model='l2', MAD-robust variance, jump=5). Verbatim from v13."""
    n = len(signal)
    if n < 10:
        return {pm: ([], 0.0) for pm in pen_multipliers}
    med = np.median(signal)
    mad = np.median(np.abs(signal - med)) + 1e-9
    s2 = (1.4826 * mad) ** 2
    if s2 < 1e-10:
        s2 = 1.0
    algo = rpt.Pelt(model="l2", min_size=3, jump=5).fit(signal.reshape(-1, 1))
    out = {}
    for pm in pen_multipliers:
        beta = pm * s2 * np.log(n)
        cps = [c for c in algo.predict(pen=beta) if c < n]
        out[pm] = (cps, beta)
    return out


# ============================================================================
# SECTION 2 — TIER 1: SAMPLE-BASED (WINDOW-LEVEL) METRICS
# ============================================================================
def _compute_midrank(x):
    """Helper for DeLong: midranks with ties averaged."""
    J = np.argsort(x)
    Z = x[J]
    N = len(x)
    T = np.zeros(N, dtype=float)
    i = 0
    while i < N:
        j = i
        while j < N and Z[j] == Z[i]:
            j += 1
        T[i:j] = 0.5 * (i + j - 1) + 1
        i = j
    T2 = np.empty(N, dtype=float)
    T2[J] = T
    return T2


def delong_auroc_ci(y_true, scores, alpha=0.05):
    """AUROC with DeLong (1988; fast form Sun & Xu 2014) 95% CI.
    Analytically exact for a single classifier; faster than bootstrap."""
    y_true = np.asarray(y_true)
    scores = np.asarray(scores, dtype=float)
    pos = scores[y_true == 1]
    neg = scores[y_true == 0]
    m, n = len(pos), len(neg)
    if m == 0 or n == 0:
        return float("nan"), (float("nan"), float("nan"))

    tx = _compute_midrank(pos)
    ty = _compute_midrank(neg)
    tz = _compute_midrank(np.concatenate([pos, neg]))
    auc = (tz[:m].sum() / (m * n)) - (m + 1.0) / (2.0 * n)

    v01 = (tz[:m] - tx) / n           # structural components, positives
    v10 = 1.0 - (tz[m:] - ty) / m     # structural components, negatives
    s01 = np.var(v01, ddof=1) if m > 1 else 0.0
    s10 = np.var(v10, ddof=1) if n > 1 else 0.0
    var = s01 / m + s10 / n
    se = np.sqrt(var) if var > 0 else 0.0
    z = stats.norm.ppf(1 - alpha / 2)
    lo, hi = max(0.0, auc - z * se), min(1.0, auc + z * se)
    return float(auc), (float(lo), float(hi))


def auprc_bootstrap_ci(y_true, scores, n_boot=1000, alpha=0.05, seed=SEED):
    """Average Precision (AUC-PR) with stratified bootstrap percentile 95% CI.
    AUC-PR is the honest headline under ~0.2% prevalence."""
    y_true = np.asarray(y_true)
    scores = np.asarray(scores, dtype=float)
    ap = average_precision_score(y_true, scores)
    rng = np.random.default_rng(seed)
    pos_idx = np.where(y_true == 1)[0]
    neg_idx = np.where(y_true == 0)[0]
    if len(pos_idx) < 2 or len(neg_idx) < 2:
        return float(ap), (float("nan"), float("nan"))
    boots = np.empty(n_boot)
    for b in range(n_boot):
        pi = rng.choice(pos_idx, size=len(pos_idx), replace=True)
        ni = rng.choice(neg_idx, size=len(neg_idx), replace=True)
        idx = np.concatenate([pi, ni])
        boots[b] = average_precision_score(y_true[idx], scores[idx])
    lo, hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(ap), (float(lo), float(hi))


def mannwhitney_effect(inter_scores, ictal_scores):
    """Two-sided Mann-Whitney U + rank-biserial-derived effect size r = Z/sqrt(N).
    Tests H0: ictal and interictal scores share the same distribution."""
    inter = np.asarray(inter_scores, dtype=float)
    ictal = np.asarray(ictal_scores, dtype=float)
    n1, n2 = len(ictal), len(inter)
    if n1 == 0 or n2 == 0:
        return dict(U=float("nan"), p=float("nan"), r=float("nan"))
    U, p = stats.mannwhitneyu(ictal, inter, alternative="two-sided")
    mu = n1 * n2 / 2.0
    sigma = np.sqrt(n1 * n2 * (n1 + n2 + 1) / 12.0)
    z = (U - mu) / sigma if sigma > 0 else 0.0
    r = z / np.sqrt(n1 + n2)
    return dict(U=float(U), p=float(p), r=float(abs(r)))


def operating_point_metrics(inter_scores, ictal_scores, q):
    """UNSUPERVISED operating point: threshold = q-th percentile of INTERICTAL
    scores only (no ictal labels touch the threshold). Reports sensitivity,
    specificity, precision, F1, FPR at that point.
    By construction specificity ~= q/100, so the informative numbers are
    recall and precision at a fixed, label-free background false-positive rate."""
    inter = np.asarray(inter_scores, dtype=float)
    ictal = np.asarray(ictal_scores, dtype=float)
    thr = np.percentile(inter, q)
    tp = int(np.sum(ictal >= thr))
    fn = int(np.sum(ictal < thr))
    fp = int(np.sum(inter >= thr))
    tn = int(np.sum(inter < thr))
    sens = tp / (tp + fn) if (tp + fn) else float("nan")     # recall
    spec = tn / (tn + fp) if (tn + fp) else float("nan")
    prec = tp / (tp + fp) if (tp + fp) else float("nan")
    f1 = (2 * prec * sens / (prec + sens)
          if (prec + sens) and not np.isnan(prec) and not np.isnan(sens)
          else float("nan"))
    fpr = fp / (fp + tn) if (fp + tn) else float("nan")
    return dict(threshold=float(thr), sensitivity=sens, specificity=spec,
                precision=prec, f1=f1, fpr=fpr, tp=tp, fn=fn, fp=fp, tn=tn)


# ============================================================================
# SECTION 3 — TIER 2: EVENT-BASED METRICS
# ============================================================================
def poisson_rate_ci(k, T, alpha=0.05):
    """Exact (Garwood) Poisson 95% CI for a rate lambda = k / T events per unit.
    Used for the false-alarm rate (FCP/h)."""
    if T <= 0:
        return (float("nan"), float("nan"))
    lo = stats.chi2.ppf(alpha / 2, 2 * k) / 2.0 / T if k > 0 else 0.0
    hi = stats.chi2.ppf(1 - alpha / 2, 2 * (k + 1)) / 2.0 / T
    return (float(lo), float(hi))


def event_scoring(cps, sz_ranges, n_inter_h, fp_mode="overlap"):
    """SzCORE-aligned event scoring on PELT change points.

    Detection rule (onset localization): a reference seizure is a TP if >=1
    predicted change point falls within +/-TOLERANCE_S of its ONSET. Predicted
    CPs are merged into events using MERGE_GAP_S before counting false alarms.

    Returns a dict with event TP/FP/FN, sensitivity, precision, F1, FCP/h,
    FP/24h, mean latency, and the raw latency list.

    fp_mode:
      'overlap' (default, SzCORE-aligned): a predicted event is a true
         detection iff any of its CPs lies within tolerance of ANY seizure
         onset; otherwise it is one false positive. Sensitivity and precision
         are decoupled (standard event-based convention).
      'strict' (v13-compatible): only the single closest event per seizure is
         credited; every other event is a false positive. Reproduces the FCP/h
         in cpd_results_v12_combined.csv for cross-checking.
    """
    tol = TOLERANCE_S // WIN_SEC      # 7 windows (28 s)
    gap = MERGE_GAP_S // WIN_SEC      # 8 windows (32 s)

    n_sz = len(sz_ranges)
    if not cps:
        return dict(tp=0, fp=0, fn=n_sz, n_events=0,
                    sensitivity=0.0 if n_sz else float("nan"),
                    precision=float("nan"), f1=float("nan"),
                    fcp_h=0.0, fp_24h=0.0, mean_lat_s=float("nan"),
                    latencies=[])

    # merge raw CPs into events
    groups = []
    curr = [cps[0]]
    for c in cps[1:]:
        if c - curr[-1] <= gap:
            curr.append(c)
        else:
            groups.append(curr); curr = [c]
    groups.append(curr)

    onsets = [s for (s, e) in sz_ranges]

    # ---- reference side: sensitivity / FN / latency ----
    tp = fn = 0
    lats = []
    matched_group_idx = set()
    for sz_start in onsets:
        hits = [(gi, c) for gi, g in enumerate(groups)
                for c in g if abs(c - sz_start) <= tol]
        if hits:
            tp += 1
            best_gi, best_c = min(hits, key=lambda x: abs(x[1] - sz_start))
            matched_group_idx.add(best_gi)
            lats.append((best_c - sz_start) * WIN_SEC)
        else:
            fn += 1

    # ---- prediction side: false positives ----
    if fp_mode == "overlap":
        def is_true(g):
            return any(abs(c - s) <= tol for c in g for s in onsets)
        fp = sum(0 if is_true(g) else 1 for g in groups)
        n_true_events = len(groups) - fp
    else:  # strict, v13-compatible
        fp = len([gi for gi in range(len(groups)) if gi not in matched_group_idx])
        n_true_events = len(matched_group_idx)

    sens = tp / (tp + fn) if (tp + fn) else float("nan")
    prec = n_true_events / len(groups) if len(groups) else float("nan")
    f1 = (2 * prec * sens / (prec + sens)
          if (prec and sens and not np.isnan(prec) and not np.isnan(sens))
          else float("nan"))
    fcp_h = fp / max(n_inter_h, 1e-6)
    return dict(tp=tp, fp=fp, fn=fn, n_events=len(groups),
                sensitivity=sens, precision=prec, f1=f1,
                fcp_h=fcp_h, fp_24h=fcp_h * 24.0,
                mean_lat_s=float(np.mean(lats)) if lats else float("nan"),
                latencies=lats)


# ============================================================================
# SECTION 4 — FIGURES (one figure per file, vector PDF + PNG)
# ============================================================================
def _save(fig, fig_dir, name):
    for ext in ("pdf", "png"):
        fig.savefig(Path(fig_dir) / f"{name}.{ext}", bbox_inches="tight")
    plt.close(fig)


def fig_roc_curves(per_subj_scores, fig_dir):
    fig, ax = plt.subplots(figsize=(5, 5))
    for subj, (y, s, auc) in per_subj_scores.items():
        fpr, tpr, _ = roc_curve(y, s)
        ax.plot(fpr, tpr, lw=1.2, label=f"{subj} (AUC={auc:.3f})")
    ax.plot([0, 1], [0, 1], "k--", lw=0.8, alpha=0.5)
    ax.set_xlabel("False positive rate"); ax.set_ylabel("True positive rate")
    ax.set_title("Sample-level ROC curves (per test subject)")
    ax.legend(fontsize=7, loc="lower right")
    _save(fig, fig_dir, "fig_roc_curves")


def fig_pr_curves(per_subj_scores, fig_dir):
    fig, ax = plt.subplots(figsize=(5, 5))
    for subj, (y, s, _) in per_subj_scores.items():
        prec, rec, _ = precision_recall_curve(y, s)
        ap = average_precision_score(y, s)
        ax.plot(rec, prec, lw=1.2, label=f"{subj} (AP={ap:.3f})")
    ax.set_xlabel("Recall (sensitivity)"); ax.set_ylabel("Precision")
    ax.set_title("Sample-level precision-recall curves\n(honest under ~0.2% prevalence)")
    ax.legend(fontsize=7, loc="upper right")
    _save(fig, fig_dir, "fig_pr_curves")


def fig_event_tradeoff(event_df, fig_dir):
    """Macro detection rate vs FCP/h across the penalty sweep."""
    g = event_df.groupby("pen_mult")
    dr = g["sensitivity"].mean()
    fcp = g["fcp_h"].mean()
    fig, ax = plt.subplots(figsize=(5.5, 4.2))
    ax.plot(fcp.values, dr.values, "o-", color="#1f4e79", lw=1.5)
    for pm in dr.index:
        ax.annotate(f"pen={pm}", (fcp[pm], dr[pm]),
                    textcoords="offset points", xytext=(6, 4), fontsize=7)
    ax.set_xlabel("Mean false change points per hour (FCP/h)")
    ax.set_ylabel("Mean event detection rate")
    ax.set_title("Event-level operating curve (sensitivity vs false-alarm burden)")
    ax.grid(alpha=0.25)
    _save(fig, fig_dir, "fig_event_tradeoff")


def fig_per_subject_bars(window_df, fig_dir):
    """Per-subject AUROC and AUC-PR side by side."""
    subj = window_df["subject"].tolist()
    x = np.arange(len(subj)); w = 0.38
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x - w / 2, window_df["auroc"], w, label="AUROC", color="#1f4e79")
    ax.bar(x + w / 2, window_df["auprc"], w, label="AUC-PR", color="#c55a11")
    ax.set_xticks(x); ax.set_xticklabels(subj, rotation=0)
    ax.set_ylabel("Score"); ax.set_ylim(0, 1)
    ax.set_title("Per-subject sample-level separability")
    ax.legend(fontsize=8)
    _save(fig, fig_dir, "fig_per_subject_auroc_auprc")


def fig_representative_timeline(subj, timeline, is_ictal, cps, fig_dir):
    """Anomaly-score timeline with detected change points and true onsets.
    Illustrates event-level localization (and pre-ictal detection if present)."""
    t = np.arange(len(timeline)) * WIN_SEC / 3600.0  # hours
    fig, ax = plt.subplots(figsize=(9, 3.2))
    ax.plot(t, timeline, lw=0.5, color="#444444", alpha=0.8)
    # shade true ictal windows
    in_s = False; start = 0
    for i, ic in enumerate(is_ictal):
        if ic and not in_s:
            start = i; in_s = True
        elif not ic and in_s:
            ax.axvspan(start * WIN_SEC / 3600.0, i * WIN_SEC / 3600.0,
                       color="#e06666", alpha=0.35, lw=0)
            in_s = False
    if in_s:
        ax.axvspan(start * WIN_SEC / 3600.0, len(is_ictal) * WIN_SEC / 3600.0,
                   color="#e06666", alpha=0.35, lw=0)
    for c in cps:
        ax.axvline(c * WIN_SEC / 3600.0, color="#1f4e79", lw=0.6, alpha=0.7)
    ax.set_xlabel("Time (hours)"); ax.set_ylabel("Ensemble anomaly score")
    ax.set_title(f"{subj}: ensemble score timeline — red = true seizure, "
                 f"blue = detected change point")
    _save(fig, fig_dir, f"fig_timeline_{subj}")


# ============================================================================
# SECTION 5 — ORCHESTRATION
# ============================================================================
def load_scores(scores_dir, subj):
    i = Path(scores_dir) / f"{subj}_ens_inter.npy"
    c = Path(scores_dir) / f"{subj}_ens_ictal.npy"
    if not (i.exists() and c.exists()):
        return None, None
    return np.load(str(i)), np.load(str(c))


def main():
    ap = argparse.ArgumentParser(description="Two-tier SzCORE-aligned evaluation")
    ap.add_argument("--scores_dir", default="results/cpd/scores")
    ap.add_argument("--summary_dir",
                    default=r"F:\Study\Thesis\Dataset\CHB-MIT\CHB info\summary")
    ap.add_argument("--out_dir", default="results/cpd/evaluation")
    ap.add_argument("--op_percentile", type=float, default=95,
                    help="interictal percentile for the unsupervised operating point")
    ap.add_argument("--n_boot", type=int, default=1000,
                    help="bootstrap iterations for AUC-PR CI")
    ap.add_argument("--fp_mode", choices=["overlap", "strict"], default="overlap")
    ap.add_argument("--rep_subject", default="chb18",
                    help="subject for the representative timeline figure")
    ap.add_argument("--rep_pen", type=float, default=0.5)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    window_rows, event_rows, stat_rows = [], [], []
    per_subj_scores = {}   # for ROC/PR figures
    rep_payload = None     # for representative timeline figure

    print("=" * 78)
    print("TWO-TIER EVALUATION (Tier 1 = sample/window, Tier 2 = event)")
    print(f"Operating point: interictal P{args.op_percentile:g} (unsupervised) | "
          f"fp_mode={args.fp_mode}")
    print("=" * 78)

    for subj in TEST_SUBJS:
        np.random.seed(SEED)  # reproducible bootstrap padding in build_timeline
        inter, ictal = load_scores(args.scores_dir, subj)
        if inter is None:
            print(f"[skip] {subj}: cached ensemble scores not found in {args.scores_dir}")
            continue

        # ---------------- TIER 1: sample / window level ----------------
        y = np.concatenate([np.zeros(len(inter)), np.ones(len(ictal))])
        s = np.concatenate([inter, ictal])
        auroc, (a_lo, a_hi) = delong_auroc_ci(y, s)
        auprc, (p_lo, p_hi) = auprc_bootstrap_ci(y, s, n_boot=args.n_boot)
        op = operating_point_metrics(inter, ictal, args.op_percentile)
        mw = mannwhitney_effect(inter, ictal)
        prevalence = 100.0 * len(ictal) / (len(inter) + len(ictal))

        per_subj_scores[subj] = (y, s, auroc)
        window_rows.append(dict(
            subject=subj, n_inter=len(inter), n_ictal=len(ictal),
            prevalence_pct=round(prevalence, 4),
            auroc=round(auroc, 4), auroc_lo=round(a_lo, 4), auroc_hi=round(a_hi, 4),
            auprc=round(auprc, 4), auprc_lo=round(p_lo, 4), auprc_hi=round(p_hi, 4),
            op_threshold=round(op["threshold"], 4),
            sensitivity=round(op["sensitivity"], 4),
            specificity=round(op["specificity"], 4),
            precision=round(op["precision"], 4),
            f1=round(op["f1"], 4), fpr=round(op["fpr"], 4)))
        stat_rows.append(dict(subject=subj, U=mw["U"],
                              p_value=mw["p"], effect_r=round(mw["r"], 4)))
        print(f"[{subj}] AUROC={auroc:.3f} [{a_lo:.3f},{a_hi:.3f}]  "
              f"AUC-PR={auprc:.3f} [{p_lo:.3f},{p_hi:.3f}]  "
              f"sens@P{args.op_percentile:g}={op['sensitivity']:.3f}  "
              f"prec={op['precision']:.3f}  MWU p={mw['p']:.1e}")

        # ---------------- TIER 2: event level (after PELT) ----------------
        timeline, is_ictal, sz_ranges, n_inter_h = build_timeline(
            subj, inter, ictal, args.summary_dir)
        if len(timeline) == 0:
            print(f"    [{subj}] empty timeline; event tier skipped")
            continue
        smoothed = pd.Series(timeline).rolling(
            window=15, min_periods=1, center=True).mean().values
        pelt = run_global_pelt_all(smoothed, PEN_MULTS)

        for pm in PEN_MULTS:
            cps, beta = pelt[pm]
            ev = event_scoring(cps, sz_ranges, n_inter_h, fp_mode=args.fp_mode)
            f_lo, f_hi = poisson_rate_ci(ev["fp"], n_inter_h)
            event_rows.append(dict(
                subject=subj, pen_mult=pm, beta=round(beta, 4),
                n_events=ev["n_events"], n_seizures=len(sz_ranges),
                tp=ev["tp"], fp=ev["fp"], fn=ev["fn"],
                sensitivity=round(ev["sensitivity"], 4),
                precision=round(ev["precision"], 4) if not np.isnan(ev["precision"]) else None,
                f1=round(ev["f1"], 4) if not np.isnan(ev["f1"]) else None,
                fcp_h=round(ev["fcp_h"], 3),
                fcp_h_lo=round(f_lo, 3), fcp_h_hi=round(f_hi, 3),
                fp_24h=round(ev["fp_24h"], 2),
                mean_lat_s=round(ev["mean_lat_s"], 1) if not np.isnan(ev["mean_lat_s"]) else None,
                n_inter_h=round(n_inter_h, 2)))

        if subj == args.rep_subject:
            cps_rep = pelt[args.rep_pen][0]
            rep_payload = (subj, smoothed, is_ictal, cps_rep)

    # ---------------- assemble dataframes ----------------
    window_df = pd.DataFrame(window_rows)
    event_df = pd.DataFrame(event_rows)
    stat_df = pd.DataFrame(stat_rows)

    out_dir.mkdir(parents=True, exist_ok=True)
    window_df.to_csv(out_dir / "eval_window_level.csv", index=False)
    event_df.to_csv(out_dir / "eval_event_level.csv", index=False)
    stat_df.to_csv(out_dir / "eval_stat_tests.csv", index=False)

    # ---------------- macro summary (mean +/- SD across subjects) ----------------
    def msd(series):
        s = pd.to_numeric(series, errors="coerce").dropna()
        return f"{s.mean():.3f} +/- {s.std(ddof=1):.3f}" if len(s) > 1 else f"{s.mean():.3f}"

    summary_rows = []
    if not window_df.empty:
        summary_rows += [
            dict(tier="sample", metric="AUROC", value=msd(window_df["auroc"])),
            dict(tier="sample", metric="AUC-PR", value=msd(window_df["auprc"])),
            dict(tier="sample", metric=f"sensitivity@P{args.op_percentile:g}",
                 value=msd(window_df["sensitivity"])),
            dict(tier="sample", metric="specificity", value=msd(window_df["specificity"])),
            dict(tier="sample", metric="precision", value=msd(window_df["precision"])),
            dict(tier="sample", metric="F1", value=msd(window_df["f1"])),
        ]
    if not event_df.empty:
        for pm in PEN_MULTS:
            sub = event_df[event_df.pen_mult == pm]
            if sub.empty:
                continue
            tp_sum = sub["tp"].sum(); sz_sum = (sub["tp"] + sub["fn"]).sum()
            summary_rows.append(dict(
                tier="event", metric=f"pen={pm}",
                value=(f"DR={tp_sum}/{sz_sum}={tp_sum/max(sz_sum,1):.1%} | "
                       f"sens={msd(sub['sensitivity'])} | "
                       f"prec={msd(sub['precision'])} | "
                       f"F1={msd(sub['f1'])} | "
                       f"FCP/h={msd(sub['fcp_h'])} | "
                       f"FP/24h={msd(sub['fp_24h'])} | "
                       f"lat_s={msd(sub['mean_lat_s'])}")))
    pd.DataFrame(summary_rows).to_csv(out_dir / "eval_summary.csv", index=False)

    # ---------------- figures ----------------
    if per_subj_scores:
        fig_roc_curves(per_subj_scores, fig_dir)
        fig_pr_curves(per_subj_scores, fig_dir)
        fig_per_subject_bars(window_df, fig_dir)
    if not event_df.empty:
        fig_event_tradeoff(event_df, fig_dir)
    if rep_payload is not None:
        fig_representative_timeline(*rep_payload, fig_dir)

    print("\n" + "=" * 78)
    print("MACRO SUMMARY")
    print("=" * 78)
    for r in summary_rows:
        print(f"  [{r['tier']:>6}] {r['metric']:<22} {r['value']}")
    print(f"\nWrote CSVs + figures to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()