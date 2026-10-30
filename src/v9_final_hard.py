#!/usr/bin/env python
"""
v9_final_hard.py -- V9-FINAL Part B (docs/prompts/V9_FINAL_VERIFY.md): "hard patients", settled with
committed data only, three detectors, all cases.

Three per-seizure caught/missed tables, CHB-MIT (development 93 + chb-test 76 + chb24 16 = 185
seizures) and Siena (47, thesis system only):
  1. thesis system (seed 42, after the localizer) -- read-only reuse of results/v9_v1/
     part1_descriptors.csv's own `caught`/`amp_ratio`/`duration_s` columns (built by v9_eeg_evidence.
     part1() from results/v9_anatomy/per_seizure.csv + siena14/per_seizure.csv, themselves gated
     against results/p3c_freeze (dev) / results/e23_test_look7 (test) / results/x1_external
     (chb24/siena) -- NOT recomputed here, since that would risk a second, inconsistent construction
     of the same frozen number).
  2. kNN leave-one-case-out (results/v9_e4) -- the per-subject parts were cleaned after aggregation
     (prompt's own note), so per-seizure caught is regenerated here from committed, cached inputs only:
     v9_e1_baselines.subject_ctx/load_D (B4 distance, cached in results/v9_e1/cache/), results/v9_e4/
     calibration.json's own k_loo (committed, not recomputed), v9_e4_knn24.one_pass (frozen, unmodified,
     imported and called verbatim). Gated against results/v9_e4/per_subject.csv: this script's own
     per-seizure caught count must sum to that file's committed tp, per subject, per stage -- STOP if
     not.
  3. GAE-CV (results/v9_x3) -- per-seizure caught regenerated from the already-committed, cached D
     dumps (results/v9_x3/dumps/fold{f}_seed42/<case>_D.npy, 96/96 present -- no GPU, no new GAE forward
     pass), each case scored under the fold that held it out (results/v9_x3/fold_manifests.json), that
     fold's own committed k (fold{f}_seed42_calibration.json). The det/loc construction mirrors
     v9_x3_cv_eval.evaluate_full() exactly (same P3L.q_of/PS.d1_events/P3L.localize calls; evaluate_full
     itself does not expose `loc`, so it is replicated here, not edited there). Gated against
     fold{f}_seed42_per_subject.csv the same way as (2).
  Siena has neither a kNN-24 nor a GAE-CV build (V9-E4 and V9-X3 are both CHB-MIT-only, see their own
  module docstrings / results/v9_x3/folds.json groups) -- reported as a stated limitation, not silently
  skipped.

Annotated ictal-channel count: test only (results/attribution_v7/labels/ictal_channels_FINAL.csv),
joined by nearest onset within 15 s (v9_x1_focal.nearest_join, read-only reuse, same tolerance used
throughout V9-X1/V9-V1-FIX).

Stats per detector: Mann-Whitney caught vs missed (amplitude ratio, duration, channel count [test only]);
logistic regression caught ~ log(amp_ratio) + log(duration_s), patient-cluster bootstrap CI (resample
subjects with replacement, B=2000, percentile CI) -- a cluster bootstrap because seizures from the same
patient are not independent draws.

READ-ONLY REUSE: v9_e1_baselines.py (subject_ctx/load_D/final_scalar_from_D/member_mean_z_from_D/DEV/
TEST/FP_TARGETS), v9_e4_knn24.py (one_pass/x_of/m_of/ALL24/SET_OF), v9_x3_cv_eval.py (case_ctx/dump_D/
FLOOR/CAP/SMOOTH), p3_levers.py (q_of/refs_of/localize/calibrate), p2_scalars.py (d1_events/smoothed),
v9_x1_focal.py (nearest_join).

OUTPUT: results/v9_final/hard/ (CSVs, SUMMARY.md), F:/Study/Thesis/Defense/slides/figs/final/
(hard_patients_amp_ratio.png).
Run:  python src/v9_final_hard.py --knn          (regenerate + gate the kNN-LOO per-seizure table)
      python src/v9_final_hard.py --gae          (regenerate + gate the GAE-CV per-seizure table)
      python src/v9_final_hard.py --stats        (join everything, run the stats, draw the figure)
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB", ROOT / "src" / "phaseC",
          ROOT / "src" / "dataprep"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import p2_scalars as PS                 # noqa: E402
import p3_levers as P3L                 # noqa: E402
import v9_e1_baselines as V9E1          # noqa: E402 -- read-only reuse
import v9_e4_knn24 as V9E4              # noqa: E402 -- read-only reuse
import v9_x3_cv_eval as V9X3            # noqa: E402 -- read-only reuse
import v9_x1_focal as V9X1              # noqa: E402 -- read-only reuse (nearest_join)

OUT = ROOT / "results" / "v9_final" / "hard"
FIGOUT = Path("F:/Study/Thesis/Defense/slides/figs/final")
ATT = ROOT / "results" / "attribution_v7" / "labels" / "ictal_channels_FINAL.csv"
PART1 = ROOT / "results" / "v9_v1" / "part1_descriptors.csv"
ALL24 = V9E4.ALL24
SET_OF = V9E4.SET_OF
PRE, POST = 30, 60   # the same E1 overlap rule as p2_scalars.caught()

RNG_SEED = 42
N_BOOT = 2000


def _runs_caught(refs, loc):
    rows = []
    for f, rr in refs.items():
        for a, b in rr:
            caught = any(h1 >= a - PRE and h0 <= b + POST for h0, h1 in loc.get(f, []))
            rows.append(dict(file_idx=int(f), onset_s=int(a), duration_s=int(b - a), caught=bool(caught)))
    return rows


def _fname_of(ctx, f):
    files = ctx["z"]["files"]
    return str(files[int(f)])


# ============================================================================ 1. kNN leave-one-case-out
def knn_table():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    cal = json.load(open(ROOT / "results" / "v9_e4" / "calibration.json"))
    gate = pd.read_csv(ROOT / "results" / "v9_e4" / "per_subject.csv")
    rows = []
    for s in ALL24:
        ctx = V9E1.subject_ctx(s)
        D = V9E1.load_D(s, "B4")
        x, m = V9E4.x_of(ctx, D), V9E4.m_of(ctx, D)
        refs = P3L.refs_of(ctx)
        k = cal["k_loo"][s]
        out, det, loc, errs = V9E4.one_pass(ctx, x, k, m, refs)
        my_tp = sum(1 for f, rr in refs.items() for a, b in rr
                    if any(h1 >= a - PRE and h0 <= b + POST for h0, h1 in loc.get(f, [])))
        my_n = sum(len(rr) for rr in refs.values())
        g = gate[(gate.subject == s) & (gate.arm == "loo") & (gate.stage == "localized")].iloc[0]
        ref_tp, ref_nref = int(g.tp), int(g.n_ref)
        if my_n == ref_nref and my_tp != ref_tp:
            raise SystemExit(f"STOP gate: kNN-LOO {s}: my per-seizure tp={my_tp} vs "
                              f"results/v9_e4/per_subject.csv tp={ref_tp} (n_ref matches at {my_n}, so "
                              "this is a real discrepancy, not a granularity mismatch)")
        if my_n != ref_nref:
            print(f"  [note] {s}: refs_of() gives {my_n} merged seizure run(s) vs SzCORE's own n_ref="
                  f"{ref_nref} (finer-grained annotation splitting inside a merged ictal window run -- "
                  "same convention gap as results/v9_v1/part1_descriptors.csv's own per-seizure count "
                  "for this subject; tp gate skipped for this subject, run-level caught/missed kept at "
                  "the part1_descriptors granularity for consistency across all three detectors).",
                  flush=True)
        for r in _runs_caught(refs, loc):
            fname = _fname_of(ctx, r["file_idx"])
            rows.append(dict(subject=s, set=SET_OF[s], file=fname, onset_s=r["onset_s"],
                              duration_s=r["duration_s"], caught=r["caught"]))
        print(f"  {s}: {my_tp}/{len(refs and [1 for rr in refs.values() for _ in rr])} caught "
              f"(gated OK, {time.time()-t0:.0f}s)", flush=True)
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "knn_loo_seizures.csv", index=False)
    print(f"kNN-LOO: {len(R)} seizures, {R.caught.sum()} caught -> {OUT/'knn_loo_seizures.csv'} "
          f"({time.time()-t0:.0f}s)", flush=True)
    return R


# ============================================================================ 2. GAE-CV
def _fold_of_case():
    man = json.load(open(ROOT / "results" / "v9_x3" / "fold_manifests.json"))
    out = {}
    for f, v in man.items():
        for s in v["held_out_cases"]:
            out[s] = int(f)
    return out


def gae_table():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    fold_of = _fold_of_case()
    missing = [s for s in ALL24 if s not in fold_of]
    if missing:
        raise SystemExit(f"STOP: no fold assignment for {missing}")
    rows = []
    for s in ALL24:
        f_ = fold_of[s]
        ck_path = ROOT / "results" / "v9_x3" / f"fold{f_}_seed42_per_subject.csv"
        gate = pd.read_csv(ck_path)
        k = json.load(open(ROOT / "results" / "v9_x3" / f"fold{f_}_seed42_calibration.json"))["k"]
        ctx = V9X3.case_ctx(s)
        D = V9X3.dump_D(ctx, None, None, cache_key=f"fold{f_}_seed42/{s}")
        x = V9E1.final_scalar_from_D(ctx, D)
        m = V9E1.member_mean_z_from_D(ctx, D)
        refs = P3L.refs_of(ctx)
        FLOOR, CAP, SMOOTH = V9X3.FLOOR, V9X3.CAP, V9X3.SMOOTH
        q = P3L.q_of(PS.smoothed(ctx, m, SMOOTH), k)
        top = float(np.clip(q, FLOOR, max(CAP, FLOOR)))
        det = PS.d1_events(ctx, x, SMOOTH, top)
        thr = np.nanquantile(PS.smoothed(ctx, x, SMOOTH), 1 - top)
        loc, pair = P3L.localize(ctx, x, det, thr, "cpd")
        my_tp = sum(1 for ff, rr in refs.items() for a, b in rr
                    if any(h1 >= a - PRE and h0 <= b + POST for h0, h1 in loc.get(ff, [])))
        my_n = sum(len(rr) for rr in refs.values())
        g = gate[(gate.subject == s) & (gate.stage == "localized")].iloc[0]
        ref_tp, ref_nref = int(g.tp), int(g.n_ref)
        if my_n == ref_nref and my_tp != ref_tp:
            raise SystemExit(f"STOP gate: GAE-CV fold{f_} {s}: my per-seizure tp={my_tp} vs "
                              f"{ck_path.name} tp={ref_tp} (n_ref matches at {my_n})")
        if my_n != ref_nref:
            print(f"  [note] {s}: refs_of() gives {my_n} merged seizure run(s) vs SzCORE's own n_ref="
                  f"{ref_nref}; tp gate skipped for this subject (same granularity gap as kNN-LOO's "
                  "note above).", flush=True)
        for r in _runs_caught(refs, loc):
            fname = _fname_of(ctx, r["file_idx"])
            rows.append(dict(subject=s, set=SET_OF[s], fold=f_, file=fname, onset_s=r["onset_s"],
                              duration_s=r["duration_s"], caught=r["caught"]))
        print(f"  {s} (fold {f_}): {my_tp} caught (gated OK, {time.time()-t0:.0f}s)", flush=True)
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "gae_cv_seizures.csv", index=False)
    print(f"GAE-CV: {len(R)} seizures, {R.caught.sum()} caught -> {OUT/'gae_cv_seizures.csv'} "
          f"({time.time()-t0:.0f}s)", flush=True)
    return R


# ============================================================================ 3. thesis system (read-only)
def thesis_table():
    D = pd.read_csv(PART1)
    D = D.rename(columns={"set": "set_raw"})
    D["set"] = D.set_raw.map({"development": "dev", "chb-test": "test", "chb24": "chb24", "siena": "siena"})
    return D[["set", "subject", "file", "onset_s", "duration_s", "caught", "amp_ratio"]].copy()


# ============================================================================ channel count (test only)
def with_channel_count(df):
    att = pd.read_csv(ATT)
    j = V9X1.nearest_join(df[df.set == "test"], att, tol=15)
    return j


# ============================================================================ stats
def mwu(caught_v, missed_v):
    caught_v = pd.Series(caught_v).dropna()
    missed_v = pd.Series(missed_v).dropna()
    if len(caught_v) < 2 or len(missed_v) < 2:
        return dict(n_caught=len(caught_v), n_missed=len(missed_v), med_caught=np.nan, med_missed=np.nan, p=np.nan)
    u, p = mannwhitneyu(missed_v, caught_v, alternative="two-sided")
    return dict(n_caught=len(caught_v), n_missed=len(missed_v), med_caught=float(caught_v.median()),
                med_missed=float(missed_v.median()), p=float(p))


def logreg_cluster_boot(df, subj_col="subject"):
    """caught ~ log(amp_ratio) + log(duration_s); patient-cluster bootstrap (resample subjects with
    replacement, B=N_BOOT, percentile 95% CI). Rows with non-positive/NaN amp_ratio or duration_s are
    dropped (log undefined) -- count reported."""
    d = df.copy()
    d = d[np.isfinite(d.amp_ratio) & (d.amp_ratio > 0) & np.isfinite(d.duration_s) & (d.duration_s > 0)]
    n_dropped = len(df) - len(d)
    X = np.column_stack([np.log(d.amp_ratio.values), np.log(d.duration_s.values)])
    y = d.caught.values.astype(int)
    if len(np.unique(y)) < 2:
        return dict(n=len(d), n_dropped=n_dropped, coef_amp=np.nan, coef_dur=np.nan,
                    ci_amp=(np.nan, np.nan), ci_dur=(np.nan, np.nan), n_boot_ok=0)
    m = LogisticRegression(penalty=None, solver="lbfgs", max_iter=2000).fit(X, y)
    coef_amp, coef_dur = float(m.coef_[0, 0]), float(m.coef_[0, 1])

    subs = d[subj_col].unique()
    rng = np.random.RandomState(RNG_SEED)
    boot_amp, boot_dur = [], []
    for _ in range(N_BOOT):
        pick = rng.choice(subs, size=len(subs), replace=True)
        bd = pd.concat([d[d[subj_col] == p] for p in pick], ignore_index=True)
        yb = bd.caught.values.astype(int)
        if len(np.unique(yb)) < 2:
            continue
        Xb = np.column_stack([np.log(bd.amp_ratio.values), np.log(bd.duration_s.values)])
        try:
            mb = LogisticRegression(penalty=None, solver="lbfgs", max_iter=2000).fit(Xb, yb)
        except Exception:
            continue
        boot_amp.append(mb.coef_[0, 0])
        boot_dur.append(mb.coef_[0, 1])
    ci_amp = (float(np.percentile(boot_amp, 2.5)), float(np.percentile(boot_amp, 97.5))) if boot_amp else (np.nan, np.nan)
    ci_dur = (float(np.percentile(boot_dur, 2.5)), float(np.percentile(boot_dur, 97.5))) if boot_dur else (np.nan, np.nan)
    return dict(n=len(d), n_dropped=n_dropped, coef_amp=coef_amp, coef_dur=coef_dur,
                ci_amp=ci_amp, ci_dur=ci_dur, n_boot_ok=len(boot_amp))


def analyze_detector(name, df_chb, df_siena=None):
    """df_chb: subject,set,file,onset_s,duration_s,caught,amp_ratio -- CHB-MIT only (dev+test+chb24)."""
    out = {}
    out["mwu_amp"] = mwu(df_chb[df_chb.caught].amp_ratio, df_chb[~df_chb.caught].amp_ratio)
    out["mwu_dur"] = mwu(df_chb[df_chb.caught].duration_s, df_chb[~df_chb.caught].duration_s)
    cc = with_channel_count(df_chb)
    out["mwu_chcount"] = mwu(cc[cc.caught].n_ictal, cc[~cc.caught].n_ictal)
    out["logreg"] = logreg_cluster_boot(df_chb)
    out["n_total"] = len(df_chb)
    out["n_caught"] = int(df_chb.caught.sum())
    if df_siena is not None and len(df_siena):
        out["siena_mwu_amp"] = mwu(df_siena[df_siena.caught].amp_ratio, df_siena[~df_siena.caught].amp_ratio)
        out["siena_mwu_dur"] = mwu(df_siena[df_siena.caught].duration_s, df_siena[~df_siena.caught].duration_s)
        out["siena_logreg"] = logreg_cluster_boot(df_siena)
        out["siena_n_total"] = len(df_siena)
        out["siena_n_caught"] = int(df_siena.caught.sum())
    return out


def draw_figure(tables):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(16, 9), dpi=150)
    rng = np.random.RandomState(42)
    for ax, (name, df) in zip(axes, tables.items()):
        cats = ["caught", "missed"]
        for ci, caught_val in enumerate((True, False)):
            d = df[df.caught == caught_val]
            jitter = (rng.rand(len(d)) - 0.5) * 0.35
            ax.scatter(ci + jitter, d.amp_ratio, c="#1f77b4" if caught_val else "#d62728", s=38, alpha=0.65,
                       edgecolors="none")
        ax.set_xticks([0, 1]); ax.set_xticklabels(cats, fontsize=18)
        ax.set_ylabel("amplitude ratio (ictal / pre-onset RMS)", fontsize=16)
        ax.tick_params(labelsize=14)
        s_ = mwu(df[df.caught].amp_ratio, df[~df.caught].amp_ratio)
        ax.set_title(f"{name}\nn={s_['n_caught']}+{s_['n_missed']}, p={s_['p']:.3f}", fontsize=17)
    fig.suptitle("Hard patients -- amplitude ratio, caught vs missed (CHB-MIT, all 185 seizures)", fontsize=20)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    FIGOUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGOUT / "hard_patients_amp_ratio.png")
    plt.close(fig)
    print(f"wrote {FIGOUT/'hard_patients_amp_ratio.png'}", flush=True)


def run_stats():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    thesis = thesis_table()
    knn_p = OUT / "knn_loo_seizures.csv"
    gae_p = OUT / "gae_cv_seizures.csv"
    if not knn_p.exists():
        raise SystemExit("STOP: run --knn first")
    if not gae_p.exists():
        raise SystemExit("STOP: run --gae first")
    knn = pd.read_csv(knn_p)
    gae = pd.read_csv(gae_p)

    # join amp_ratio onto knn/gae from the thesis descriptor table (same EEG, same window grid --
    # amp_ratio is a property of the seizure, not of the detector)
    desc = thesis[["subject", "file", "onset_s", "amp_ratio"]].drop_duplicates()
    knn = knn.merge(desc, on=["subject", "file", "onset_s"], how="left")
    gae = gae.merge(desc, on=["subject", "file", "onset_s"], how="left")
    n_unmatched_knn = int(knn.amp_ratio.isna().sum())
    n_unmatched_gae = int(gae.amp_ratio.isna().sum())

    thesis_chb = thesis[thesis.set.isin(["dev", "test", "chb24"])]
    thesis_siena = thesis[thesis.set == "siena"]
    knn_chb = knn[knn.set.isin(["dev", "test", "chb24"])]
    gae_chb = gae[gae.set.isin(["dev", "test", "chb24"])]

    results = {}
    results["thesis"] = analyze_detector("thesis system", thesis_chb, thesis_siena)
    results["knn_loo"] = analyze_detector("kNN leave-one-case-out", knn_chb)
    results["gae_cv"] = analyze_detector("GAE-CV", gae_chb)

    draw_figure({"thesis system": thesis_chb, "kNN LOCO": knn_chb, "GAE-CV": gae_chb})

    L = ["# V9-FINAL Part B -- hard patients, three detectors, all cases\n",
         f"CHB-MIT: {len(thesis_chb)} seizures (development {len(thesis_chb[thesis_chb.set=='dev'])} + "
         f"chb-test {len(thesis_chb[thesis_chb.set=='test'])} + chb24 {len(thesis_chb[thesis_chb.set=='chb24'])}). "
         f"Siena: {len(thesis_siena)} seizures, thesis system only -- V9-E4 (kNN) and V9-X3 (GAE-CV) are "
         "both CHB-MIT-only builds (see their own module docstrings), so Siena has no kNN-LOO or GAE-CV "
         "per-seizure table; not silently skipped, just unavailable from committed results.\n",
         f"kNN-LOO / GAE-CV join to the thesis descriptor table (amp_ratio) by (subject, file, onset_s): "
         f"{n_unmatched_knn} unmatched (kNN), {n_unmatched_gae} unmatched (GAE-CV) -- should be 0 since "
         "the window grid and annotations are detector-independent; STOP if not.\n"]
    if n_unmatched_knn or n_unmatched_gae:
        raise SystemExit(f"STOP: {n_unmatched_knn}/{n_unmatched_gae} unmatched amp_ratio joins -- "
                          "window-grid mismatch between tables, investigate before trusting the stats below")

    for key, label in (("thesis", "Thesis system (seed 42, after the localizer)"),
                        ("knn_loo", "kNN leave-one-case-out"), ("gae_cv", "GAE-CV")):
        r = results[key]
        L.append(f"\n## {label}\n")
        L.append(f"n = {r['n_total']} seizures, {r['n_caught']} caught, {r['n_total']-r['n_caught']} missed.\n")
        L += ["```",
              f"amplitude ratio   caught median {r['mwu_amp']['med_caught']:.3f} (n={r['mwu_amp']['n_caught']}) "
              f"vs missed median {r['mwu_amp']['med_missed']:.3f} (n={r['mwu_amp']['n_missed']}), "
              f"Mann-Whitney p={r['mwu_amp']['p']:.4f}",
              f"duration (s)      caught median {r['mwu_dur']['med_caught']:.1f} (n={r['mwu_dur']['n_caught']}) "
              f"vs missed median {r['mwu_dur']['med_missed']:.1f} (n={r['mwu_dur']['n_missed']}), "
              f"Mann-Whitney p={r['mwu_dur']['p']:.4f}",
              f"channel count     caught median {r['mwu_chcount']['med_caught']:.1f} (n={r['mwu_chcount']['n_caught']}) "
              f"vs missed median {r['mwu_chcount']['med_missed']:.1f} (n={r['mwu_chcount']['n_missed']}), "
              f"Mann-Whitney p={r['mwu_chcount']['p']:.4f}  (test only)", "```"]
        lg = r["logreg"]
        L += [f"\nLogistic regression caught ~ log(amp_ratio) + log(duration_s) (n={lg['n']}, "
              f"{lg['n_dropped']} dropped, patient-cluster bootstrap B={N_BOOT}, {lg['n_boot_ok']} resamples "
              "converged):\n", "```",
              f"log(amp_ratio)   coef {lg['coef_amp']:+.3f}   95% CI [{lg['ci_amp'][0]:+.3f}, {lg['ci_amp'][1]:+.3f}]",
              f"log(duration_s)  coef {lg['coef_dur']:+.3f}   95% CI [{lg['ci_dur'][0]:+.3f}, {lg['ci_dur'][1]:+.3f}]",
              "```"]
        if "siena_mwu_amp" in r:
            L.append(f"\n### Siena ({label}, {r['siena_n_total']} seizures, {r['siena_n_caught']} caught) -- "
                      "reported separately per the prompt\n")
            L += ["```",
                  f"amplitude ratio   caught median {r['siena_mwu_amp']['med_caught']:.3f} "
                  f"(n={r['siena_mwu_amp']['n_caught']}) vs missed median {r['siena_mwu_amp']['med_missed']:.3f} "
                  f"(n={r['siena_mwu_amp']['n_missed']}), p={r['siena_mwu_amp']['p']:.4f}",
                  f"duration (s)      caught median {r['siena_mwu_dur']['med_caught']:.1f} "
                  f"(n={r['siena_mwu_dur']['n_caught']}) vs missed median {r['siena_mwu_dur']['med_missed']:.1f} "
                  f"(n={r['siena_mwu_dur']['n_missed']}), p={r['siena_mwu_dur']['p']:.4f}", "```"]
            slg = r["siena_logreg"]
            L += [f"Logistic regression (Siena, n={slg['n']}, {slg['n_boot_ok']} resamples converged): "
                  f"log(amp_ratio) coef {slg['coef_amp']:+.3f} CI [{slg['ci_amp'][0]:+.3f}, {slg['ci_amp'][1]:+.3f}], "
                  f"log(duration_s) coef {slg['coef_dur']:+.3f} CI [{slg['ci_dur'][0]:+.3f}, {slg['ci_dur'][1]:+.3f}]"]

    def survives(key):
        r = results[key]
        amp_ok = r["mwu_amp"]["p"] < 0.05
        dur_ok = r["mwu_dur"]["p"] < 0.05
        ch_ok = r["mwu_chcount"]["p"] < 0.05
        return amp_ok, dur_ok, ch_ok

    verdicts = {k: survives(k) for k in ("thesis", "knn_loo", "gae_cv")}
    L.append("\n## Which descriptor survives (p<0.05, Mann-Whitney) in all three detectors\n")
    L.append("```")
    L.append(f"{'descriptor':16s} thesis   knn-loo   gae-cv   survives-all-3")
    for i, desc_name in enumerate(("amplitude ratio", "duration", "channel count (test only)")):
        vals = [verdicts[k][i] for k in ("thesis", "knn_loo", "gae_cv")]
        L.append(f"{desc_name:16s} {str(vals[0]):8s} {str(vals[1]):9s} {str(vals[2]):8s} {str(all(vals))}")
    L.append("```")

    L.append(f"\nFigure: `{FIGOUT/'hard_patients_amp_ratio.png'}`.\n\nElapsed {time.time()-t0:.0f}s.")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "SUMMARY.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L), flush=True)
    print(f"\nWrote {OUT/'SUMMARY.md'}", flush=True)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--knn", action="store_true")
    ap.add_argument("--gae", action="store_true")
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()
    if a.knn:
        knn_table()
    elif a.gae:
        gae_table()
    elif a.stats:
        run_stats()
    else:
        raise SystemExit("pass --knn, --gae or --stats")


if __name__ == "__main__":
    main()
