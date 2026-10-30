#!/usr/bin/env python
"""
v9_x3_aggregate.py -- V9-X3 (docs/prompts/V9_X3_CV_PREP.md), step 5-6: combine the 4 folds'
GAE-CV results (v9_x3_cv_eval.py), the B4 leave-one-case-out baseline and the per-fold GAE+kNN
fusion (v9_x3_knn_b4.py) into one set of tables + SUMMARY.md.

Reporting (per the prompt's step 5): per case and per fold; per-case mean over 24 cases AND over
23 subjects (chb21 excluded, so chb01's patient is not double-counted); patient bootstrap 95% CI
(v9_e1_baselines.boot_mean_ci, unchanged); paired bootstrap GAE-CV vs kNN-LOO and GAE+kNN-CV vs
GAE-CV on the SAME 24 cases (paired_boot below -- the same construction as v9_e2_veto.py's own
paired_boot, duplicated here rather than importing that module, which pulls in unrelated heavy
raw-EEG-cache code); the 8 original test patients and the 15 original development patients as
separate subsets; duration bins; onset/offset error.

Run: python src/v9_x3_aggregate.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import v9_e1_baselines as V9E1   # noqa: E402

OUT = ROOT / "results" / "v9_x3"
ALL24 = [f"chb{i:02d}" for i in range(1, 25)]
DEV15 = list(V9E1.DEV)
TEST8 = list(V9E1.TEST)


def paired_boot(a, b, n=10_000, seed=0):
    """Same construction as v9_e2_veto.paired_boot (duplicated, not imported -- see module
    docstring): a, b are pandas Series indexed by case, same index resampled for both each draw."""
    rng = np.random.default_rng(seed)
    subs = sorted(set(a.index) & set(b.index))
    av, bv = a.loc[subs].values, b.loc[subs].values
    N = len(subs)
    diffs = np.empty(n)
    for i in range(n):
        idx = rng.integers(0, N, N)
        diffs[i] = av[idx].mean() - bv[idx].mean()
    return dict(mean_diff=float(diffs.mean()), ci_lo=float(np.percentile(diffs, 2.5)),
                ci_hi=float(np.percentile(diffs, 97.5)), share_gt0=float((diffs > 0).mean()), n=N)


# ------------------------------------------------------------------------------------- loaders
def load_gae_cv():
    rows = []
    for k in (1, 2, 3, 4):
        fp = OUT / f"fold{k}_seed42_per_subject.csv"
        if not fp.exists():
            raise SystemExit(f"missing {fp} -- run v9_x3_cv_eval.py --score --fold {k} first")
        rows.append(pd.read_csv(fp))
    return pd.concat(rows, ignore_index=True)


def load_gae_cv_errors():
    rows = [pd.read_csv(OUT / f"fold{k}_seed42_errors.csv") for k in (1, 2, 3, 4)
            if (OUT / f"fold{k}_seed42_errors.csv").exists()]
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def load_gae_cv_bins():
    rows = [pd.read_csv(OUT / f"fold{k}_seed42_duration_bins.csv") for k in (1, 2, 3, 4)
            if (OUT / f"fold{k}_seed42_duration_bins.csv").exists()]
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def load_knn_loo():
    return pd.read_csv(OUT / "b4_loo_per_subject.csv")


def load_knn_loo_errors():
    fp = OUT / "b4_loo_errors.csv"
    return pd.read_csv(fp) if fp.exists() else pd.DataFrame()


def load_knn_loo_bins():
    fp = OUT / "b4_loo_duration_bins.csv"
    return pd.read_csv(fp) if fp.exists() else pd.DataFrame()


def load_fusion_cv():
    rows = []
    for k in (1, 2, 3, 4):
        fp = OUT / f"fold{k}_seed42_F_per_subject.csv"
        if fp.exists():
            rows.append(pd.read_csv(fp))
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def load_fusion_cv_errors():
    rows = [pd.read_csv(OUT / f"fold{k}_seed42_F_errors.csv") for k in (1, 2, 3, 4)
            if (OUT / f"fold{k}_seed42_F_errors.csv").exists()]
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def load_fusion_cv_bins():
    rows = [pd.read_csv(OUT / f"fold{k}_seed42_F_duration_bins.csv") for k in (1, 2, 3, 4)
            if (OUT / f"fold{k}_seed42_F_duration_bins.csv").exists()]
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


# ------------------------------------------------------------------------------------- metrics
def per_case_sens(df, stage="localized", subset=None):
    d = df[df.stage == stage]
    if subset is not None:
        d = d[d.subject.isin(subset)]
    return d.set_index("subject").assign(sens=lambda x: x.tp / x.n_ref).sens


def pooled_metrics(df, stage="localized", subset=None):
    d = df[df.stage == stage]
    if subset is not None:
        d = d[d.subject.isin(subset)]
    tp, fp, nr, h = d.tp.sum(), d.fp.sum(), d.n_ref.sum(), d.nonict_h.sum()
    sens = tp / nr if nr else float("nan")
    prec = tp / (tp + fp) if (tp + fp) else float("nan")
    f1 = 2 * tp / (2 * tp + fp + (nr - tp)) if (2 * tp + fp + (nr - tp)) else float("nan")
    fa = fp / h * 24 if h else float("nan")
    sm = d.assign(sens=d.tp / d.n_ref)
    s_sens = sm.sens.mean()
    lo, hi = V9E1.boot_mean_ci(sm.sens.values) if len(sm) else (float("nan"), float("nan"))
    return dict(n_cases=len(d), tp=int(tp), n_ref=int(nr), fp=int(fp), pooled_sens=sens,
                pooled_prec=prec, pooled_f1=f1, pooled_fa_day=fa, subject_mean_sens=s_sens,
                boot_ci_lo=lo, boot_ci_hi=hi)


def err_stats(E, col):
    if len(E) == 0 or col not in E.columns:
        return dict(median=float("nan"), iqr_lo=float("nan"), iqr_hi=float("nan"), bias=float("nan"), n=0)
    v = E[col].abs()
    return dict(median=float(v.median()), iqr_lo=float(v.quantile(0.25)), iqr_hi=float(v.quantile(0.75)),
                bias=float(E[col].median()), n=len(E))


def dur_bin_table(bins_df):
    if len(bins_df) == 0:
        return pd.DataFrame()
    g = bins_df.groupby(["lo", "hi"])[["caught", "n"]].sum().reset_index()
    g["sens"] = g.caught / g.n
    return g


def fmt_dur_bins(g):
    if len(g) == 0:
        return "  (no data)"
    return "\n".join(f"  [{r.lo:>4g},{r.hi:<4g}) s: {int(r.caught):3d}/{int(r.n):<3d} = {r.sens:.3f}"
                      for _, r in g.iterrows())


def main():
    GAE = load_gae_cv(); GAE_E = load_gae_cv_errors(); GAE_B = load_gae_cv_bins()
    KNN = load_knn_loo(); KNN_E = load_knn_loo_errors(); KNN_B = load_knn_loo_bins()
    FUS = load_fusion_cv(); FUS_E = load_fusion_cv_errors(); FUS_B = load_fusion_cv_bins()
    have_fusion = len(FUS) > 0

    combined = pd.concat([
        GAE.assign(arm="GAE-CV"), KNN.assign(arm="kNN-LOO"),
        FUS.assign(arm="GAE+kNN-CV") if have_fusion else pd.DataFrame(),
    ], ignore_index=True)
    combined.to_csv(OUT / "combined_per_subject.csv", index=False)

    subsets = dict(all24=ALL24, subj23=[c for c in ALL24 if c != "chb21"], test8=TEST8, dev15=DEV15)

    L = ["# V9-X3 -- 4-fold patient-wise cross-validation of the GAE: results\n",
         "Source: docs/prompts/V9_X3_CV_PREP.md. GAE-CV = each fold's own held-out cases, scored "
         "by that fold's own GAE (trained on the other 3 folds, seed 42, last epoch kept). "
         "kNN-LOO = B4 (12-feature per-channel kNN distance, no trained component), leave-one-"
         "case-out k, all 24 cases -- results/v9_x3/b4_loo_*.csv, SAME per-case ctx/inputs as "
         "GAE-CV (not results/v9_e4/'s own chb24 inputs, which used a different, label-free "
         "z-scoring -- see v9_x3_knn_b4.py's docstring). GAE+kNN-CV = per-fold fusion (F arm), "
         "k_F calibrated once per fold on that fold's own training cases, label-free.\n"]

    L.append("\n## Per-case (localized stage), all 3 arms\n```")
    piv = combined[combined.stage == "localized"].assign(sens=lambda d: d.tp / d.n_ref)
    piv = piv.pivot_table(index="subject", columns="arm", values=["tp", "fp", "n_ref", "sens"])
    L.append(piv.round(3).to_string())
    L.append("```")

    L.append("\n## Pooled + subject-mean metrics, by subset (localized stage)\n")
    for setname, subs in subsets.items():
        L.append(f"\n### {setname} (n={len(subs)})\n```")
        L.append(f"{'arm':14s} {'n':>3s} {'tp/ref':>9s} {'FP':>5s}  {'sens':>6s} {'prec':>6s} "
                 f"{'F1':>6s} {'FP/day':>7s} | {'subj-mean':>9s} {'95% CI':>18s}")
        for arm, df in (("GAE-CV", GAE), ("kNN-LOO", KNN)) + ((("GAE+kNN-CV", FUS),) if have_fusion else ()):
            m = pooled_metrics(df, "localized", subs)
            L.append(f"{arm:14s} {m['n_cases']:3d} {m['tp']:4d}/{m['n_ref']:<4d} {m['fp']:5d}  "
                      f"{m['pooled_sens']:.3f} {m['pooled_prec']:.3f} {m['pooled_f1']:.3f} "
                      f"{m['pooled_fa_day']:6.2f} | {m['subject_mean_sens']:9.3f} "
                      f"[{m['boot_ci_lo']:.3f}, {m['boot_ci_hi']:.3f}]")
        L.append("```")

    L.append("\n## Paired bootstrap (per-case sensitivity, localized stage, 10,000 draws)\n```")
    s_gae = per_case_sens(GAE, "localized")
    s_knn = per_case_sens(KNN, "localized")
    pb1 = paired_boot(s_gae, s_knn)
    L.append(f"GAE-CV - kNN-LOO   (all {pb1['n']} cases):  mean diff {pb1['mean_diff']:+.3f}  "
              f"95% CI [{pb1['ci_lo']:+.3f}, {pb1['ci_hi']:+.3f}]  P(diff>0) {pb1['share_gt0']:.3f}")
    if have_fusion:
        s_fus = per_case_sens(FUS, "localized")
        pb2 = paired_boot(s_fus, s_gae)
        L.append(f"GAE+kNN-CV - GAE-CV (n={pb2['n']} held-out cases): mean diff {pb2['mean_diff']:+.3f}  "
                  f"95% CI [{pb2['ci_lo']:+.3f}, {pb2['ci_hi']:+.3f}]  P(diff>0) {pb2['share_gt0']:.3f}")
    L.append("```")

    L.append("\n## Duration bins (caught/n, localized stage)\n")
    for label, bdf in (("GAE-CV", GAE_B), ("kNN-LOO", KNN_B)) + ((("GAE+kNN-CV", FUS_B),) if have_fusion else ()):
        L.append(f"\n**{label}**\n```\n{fmt_dur_bins(dur_bin_table(bdf))}\n```")

    L.append("\n## Onset / offset |error| (median [IQR], bias, n), matched seizures\n```")
    for label, E in (("GAE-CV", GAE_E), ("kNN-LOO", KNN_E)) + ((("GAE+kNN-CV", FUS_E),) if have_fusion else ()):
        on, off = err_stats(E, "onset_err"), err_stats(E, "offset_err")
        L.append(f"{label:12s} onset  median {on['median']:5.1f} s IQR [{on['iqr_lo']:.1f}, "
                  f"{on['iqr_hi']:.1f}] bias {on['bias']:+5.1f} (n={on['n']})")
        L.append(f"{'':12s} offset median {off['median']:5.1f} s IQR [{off['iqr_lo']:.1f}, "
                  f"{off['iqr_hi']:.1f}] bias {off['bias']:+5.1f} (n={off['n']})")
    L.append("```")

    L.append("\n## Per fold (localized stage, GAE-CV)\n```")
    for k in (1, 2, 3, 4):
        d = GAE[(GAE.fold == k) & (GAE.stage == "localized")]
        m = pooled_metrics(d, "localized")
        L.append(f"fold {k}: {m['n_cases']} held-out cases, tp/ref {m['tp']}/{m['n_ref']}, "
                 f"fp {m['fp']}, sens {m['pooled_sens']:.3f}, FP/day {m['pooled_fa_day']:.2f}")
    L.append("```")

    L.append(
        "\n## Disclosures\n"
        "(a) The architecture and post-processing (members, correction, smoothing, localizer, "
        "SzCORE config) were designed on the 15 original development patients, and the per-"
        "patient budget cap partly with the test set in view -- CV numbers on those 15 patients "
        "(and, to a lesser extent, the 8 original test patients) may be mildly optimistic for that "
        "reason, independent of the CV split itself. The 8 original test patients' numbers are "
        "reported as a separate subset above for this reason.\n"
        "(b) One seed (42) per fold -- no multi-seed averaging, unlike the thesis model's own "
        "4-seed report.\n"
        "(c) chb24 is inside a fold here (fold 3's held-out case), trained into folds 1/2/4 -- "
        "this CV analysis is therefore separate from, and not a replacement for, the external "
        "evaluation of the unchanged thesis model on chb24 (results/v9_anatomy, results/x1_external).\n")

    (OUT / "SUMMARY.md").write_text("\n".join(L), encoding="utf-8")
    print(f"wrote {OUT / 'SUMMARY.md'}")
    print(f"wrote {OUT / 'combined_per_subject.csv'}")


if __name__ == "__main__":
    main()
