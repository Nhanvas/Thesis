#!/usr/bin/env python
"""
fa16_aggregate.py -- verification and tables of F-A1.6 (the K-means baseline; src/fa16_kmeans.py; plan §12 17/11 01:30).
Written before any result exists. Reads the notebook output (a folder holding fa16/), checks it, and joins the K-means
rows to the committed six-model comparison (results/model_cmp, read only) with the record's own functions
(src/model_cmp_aggregate.py: per_case, boot_diff, curve_at).

Checks (STOP if any fails):
  A0  every run gate present and PASS (D0, G-mini, GG, GG-mc, G-IF, G-km); every job done (16); the rows of both
      K-means arms (km primary, km_u secondary) cover the 24 cases at both points and stages; their seizure counts and
      non-seizure hours equal the GAE's case by case
  A1  the record's functions reproduce the committed tables they made: curves_mean.csv (gae ... cnn) and
      paired_bootstrap.csv (f1, sens) from the committed per_subject / curves
Tables (out, default results/fa16):
  table7.csv            per-case means of the seven models + the secondary arm km_u (u-CBLOF) (own label-free point and fixed 0.005, after the localizer):
                        sensitivity, precision, F1, FP/day, window AUROC; totals of seizures caught / annotated and of
                        false alarms
  km_per_case.csv       the K-means arm per case (own point, localized) with the chosen k per channel summarised
  paired_bootstrap_km.csv  K-means - GAE and u-CBLOF - GAE, per-case sensitivity, F1, FP/day (own point, localized), paired subject
                        bootstrap B = 10,000, chb01 + chb21 one unit (model_cmp_aggregate.boot_diff, seed 0)
  matched_rate_km.csv   sensitivity of each model read on its detector curve at the GAE's own FP/day (analysis C)
  curves_mean7.csv      the committed curves_mean.csv + the K-means curve
  km_k_summary.csv      chosen k (count over case x channel), IQR-0 features, smallest cluster share
  km_small_diag.csv     per case: share of all windows and of the seizure windows in small clusters (mean over the 18
                        channels; diagnostic computed after scoring), and km_u - km per-case F1 / sensitivity
  figures/fig_model_cmp_curves7.png / .pdf  Figure 11 redrawn with seven curves (style of
                        results/model_cmp/figures/fig_model_cmp_curves.png)
  SUMMARY.md, gates_all.json (the notebook output itself is committed where it was downloaded, e.g. results/fa16/run/)
  python src/fa16_aggregate.py <dir with the notebook output> [--ref results/model_cmp] [--out results/fa16]
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
import sys  # noqa: E402
sys.path.insert(0, str(ROOT / "src"))
import model_cmp_aggregate as MA  # noqa: E402

ORDER7 = ["gae", "mlp", "if", "km", "svm", "hgb", "cnn"]
TABLE = ORDER7 + ["km_u"]
LABEL = dict(MA.LABEL, km="K-means (label-free)", km_u="K-means, u-CBLOF score (label-free, secondary)")
GATES = ("D0", "G-mini", "GG", "GG-mc", "G-IF", "G-km")
COLORS = {"gae": "#1f1f1f", "mlp": "#9467bd", "if": "#1f77b4", "km": "#8c564b", "svm": "#2ca02c", "hgb": "#ff7f0e",
          "cnn": "#d62728"}
NAMES = {"gae": "GAE (label-free)", "mlp": "MLP autoencoder (label-free)", "if": "Isolation Forest (label-free)",
         "km": "K-means (label-free)", "svm": "Linear SVM (supervised)", "hgb": "Gradient-boosted trees (supervised)",
         "cnn": "1-D CNN (supervised)"}


def stop(msg):
    raise SystemExit(f"STOP {msg}")


def find_run(d):
    hits = sorted(Path(d).rglob("fa16/gates.json"))
    if len(hits) != 1:
        stop(f"A0: expected one fa16/gates.json under {d}, found {len(hits)}")
    return hits[0].parent


def a0(run):
    gates = json.loads((run / "gates.json").read_text())
    jobs = json.loads((run / "jobs.json").read_text()) if (run / "jobs.json").exists() else []
    st = {}
    for g in gates:
        st.setdefault(g["gate"], []).append(g["status"])
    bad = [k for k in GATES if st.get(k) is None or any(s != "PASS" for s in st[k])]
    if bad:
        stop(f"A0: gates missing or not PASS: {bad} ({st})")
    nr = [j for j in jobs if j["status"] != "done"]
    if nr or len(jobs) != 16:
        stop(f"A0: jobs not done or missing: {nr}, {len(jobs)} of 16")
    per = pd.read_csv(run / "per_subject.csv")
    g = per[(per.model == "gae") & (per.point == "own") & (per.stage == "localized")].set_index("subject")
    for arm in ("km", "km_u"):
        k = per[per.model == arm]
        if len(k) != 24 * 4 or k.subject.nunique() != 24:
            stop(f"A0: {arm} rows {len(k)} for {k.subject.nunique()} cases (need 96 for 24)")
        kk = k[(k.point == "own") & (k.stage == "localized")].set_index("subject").reindex(g.index)
        if not ((kk.n_ref == g.n_ref).all() and (np.abs(kk.nonict_h - g.nonict_h) < 1e-9).all()):
            stop(f"A0: {arm} seizure counts / non-seizure hours differ from the GAE's")
    return gates, jobs


def a1(ref):
    per = MA.per_case(pd.read_csv(ref / "per_subject.csv"))
    own = per[(per.point == "own") & (per.stage == "localized")]
    cur = pd.read_csv(ref / "curves.csv")
    cm = pd.read_csv(ref / "curves_mean.csv")
    bad = []
    if set(cm.model) != set(cur.model):
        bad.append(("curves_mean models", sorted(set(cm.model)), sorted(set(cur.model))))
    for m in sorted(set(cm.model)):
        _, c = MA.curve_at(cur, m, 0.0)
        r = cm[cm.model == m].sort_values("fp_day").reset_index(drop=True)
        c = c.sort_values("fp_day").reset_index(drop=True)
        if len(c) != len(r) or not (np.allclose(c.sens, r.sens, atol=1e-12) and np.allclose(c.fp_day, r.fp_day, atol=1e-12)):
            bad.append(("curves_mean", m))
    pb = pd.read_csv(ref / "paired_bootstrap.csv")
    for r in pb.itertuples():
        x = MA.boot_diff(own, r.model, metric=r.metric)
        if not all(abs(x[a] - getattr(r, a)) < 1e-12 for a in ("diff", "lo", "hi")):
            bad.append(("paired_bootstrap", r.model, r.metric))
    if bad:
        stop(f"A1: the record's functions do not reproduce the committed tables: {bad}")
    return own


def figure(cm, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 10, "axes.linewidth": 0.8}):
        fig, ax = plt.subplots(figsize=(7.0, 4.2), facecolor="white")
        for m in [m for m in ORDER7 if m in set(cm.model)]:
            d = cm[(cm.model == m) & (cm.fp_day <= 60)].sort_values("fp_day")
            ax.plot(d.fp_day, d.sens, color=COLORS[m], lw=2.2 if m == "gae" else 1.6, label=NAMES[m],
                    zorder=3 if m == "gae" else 2)
        ax.set_xlim(0, 60)
        ax.set_ylim(0, 1)
        ax.set_xlabel("False alarms per day")
        ax.set_ylabel("Sensitivity")
        ax.tick_params(direction="in", top=True, right=True, length=4)
        ax.legend(loc="lower right", frameon=True, fancybox=False, edgecolor="#bbbbbb", fontsize=9)
        fig.tight_layout()
        (out / "figures").mkdir(parents=True, exist_ok=True)
        fig.savefig(out / "figures" / "fig_model_cmp_curves7.png", dpi=300, facecolor="white")
        fig.savefig(out / "figures" / "fig_model_cmp_curves7.pdf", facecolor="white")
        plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("indir")
    ap.add_argument("--ref", default=str(ROOT / "results" / "model_cmp"))
    ap.add_argument("--out", default=str(ROOT / "results" / "fa16"))
    a = ap.parse_args()
    ref, out = Path(a.ref), Path(a.out)
    run = find_run(a.indir)
    gates, jobs = a0(run)
    a1(ref)
    print("A0 / A1 PASS")
    out.mkdir(parents=True, exist_ok=True)
    T = {t: pd.concat([pd.read_csv(ref / f"{t}.csv"), pd.read_csv(run / f"{t}.csv").query("model in ('km', 'km_u')")],
                      ignore_index=True) for t in ("per_subject", "curves", "auroc", "seizures")}
    per = MA.per_case(T["per_subject"])
    own = per[(per.point == "own") & (per.stage == "localized")]
    present = [m for m in TABLE if m in set(T["curves"].model)]
    # table 7
    rows = []
    au = T["auroc"].groupby("model").auroc.mean()
    for m in present:
        for pt in ("own", "fixed0.005"):
            d = per[(per.model == m) & (per.point == pt) & (per.stage == "localized")]
            rows.append(dict(model=m, point=pt, n_cases=len(d), sens=d.sens.mean(), prec=d.prec.mean(), f1=d.f1.mean(),
                             fp_day=d.fp_day.mean(), window_auroc=au.get(m), seizures_caught=int(d.tp.sum()),
                             seizures=int(d.n_ref.sum()), false_alarms=int(d.fp.sum())))
    t7 = pd.DataFrame(rows)
    # K-means per case + k
    kk = pd.read_csv(run / "km_k.csv")
    kc = own[own.model == "km"][["fold", "subject", "k", "tp", "fp", "n_ref", "nonict_h", "sens", "prec", "f1", "fp_day"]]
    kc = kc.rename(columns={"k": "budget_k"}).merge(
        kk.groupby("subject").agg(k_median=("k", "median"), k_min=("k", "min"), k_max=("k", "max"),
                                  iqr0_median=("iqr0_features", "median"), km_seconds=("seconds", "sum")).reset_index(),
        on="subject").sort_values("subject")
    ks = pd.concat([kk.k.value_counts().sort_index().rename("n").reset_index().assign(what="chosen k (case x channel)"),
                    pd.DataFrame([dict(what="IQR-0 features per channel (median, max)", k=np.nan,
                                       n=f"{kk.iqr0_features.median():.0f}, {kk.iqr0_features.max():.0f}"),
                                  dict(what="smallest cluster share (median, min)", k=np.nan,
                                       n=f"{kk.min_cluster_share.median():.4f}, {kk.min_cluster_share.min():.4f}")])],
                   ignore_index=True)
    # bootstrap K-means - GAE
    pb = pd.DataFrame([MA.boot_diff(own, m, metric=mt) for m in ("km", "km_u") for mt in ("sens", "f1", "fp_day")])
    # small-cluster diagnostic (after scoring) and the km_u - km difference per case
    dg = kk.groupby("subject").agg(k_median=("k", "median"), share_small=("share_small", "mean"),
                                   ictal_windows=("diag_ictal_windows", "first"),
                                   ictal_share_small=("diag_ictal_share_small", "mean"),
                                   nonictal_share_small=("diag_nonictal_share_small", "mean")).reset_index()
    ow = own.set_index(["model", "subject"])
    dg["f1_km"] = [ow.loc[("km", s), "f1"] for s in dg.subject]
    dg["d_f1_kmu_minus_km"] = [ow.loc[("km_u", s), "f1"] - ow.loc[("km", s), "f1"] for s in dg.subject]
    dg["d_sens_kmu_minus_km"] = [ow.loc[("km_u", s), "sens"] - ow.loc[("km", s), "sens"] for s in dg.subject]
    pb = pd.concat([pb, pd.DataFrame([MA.boot_diff(own, "km_u", ref="km", metric=mt) for mt in ("sens", "f1", "fp_day")])],
                   ignore_index=True)
    # curves + matched rate
    gae_fp = own[own.model == "gae"].fp_day.mean()
    cm0 = pd.read_csv(ref / "curves_mean.csv")
    s_at, ck = MA.curve_at(T["curves"], "km", gae_fp)
    cm = pd.concat([cm0, ck.assign(model="km")[["top", "sens", "fp_day", "model"]]], ignore_index=True)
    mr = pd.DataFrame([dict(model=m, sens_at_gae_fp_day=MA.curve_at(T["curves"], m, gae_fp)[0], gae_fp_day=gae_fp)
                       for m in present])
    for name, df in (("table7", t7), ("km_per_case", kc), ("paired_bootstrap_km", pb), ("matched_rate_km", mr),
                     ("curves_mean7", cm), ("km_k_summary", ks), ("km_small_diag", dg)):
        df.to_csv(out / f"{name}.csv", index=False)
    figure(cm, out)
    meta = json.loads((run / "run_meta.json").read_text())
    proj = json.loads((run / "projection.json").read_text()) if (run / "projection.json").exists() else {}
    (out / "gates_all.json").write_text(json.dumps(dict(gates=gates, jobs=jobs, run_meta=meta), indent=1, default=str))
    m7 = t7[t7.point == "own"].set_index("model")
    L = ["# F-A1.6 -- K-means baseline in the six-model comparison (CHB-MIT, 4-fold patient-wise CV, 24 cases, seed 42)\n",
         f"Run: {meta.get('notebook')} at {str(meta.get('repo_commit'))[:7]}, code sha {meta.get('code_sha')}, "
         f"measured runtime {meta.get('runtime_h')} h; K-means jobs "
         f"{sum(j.get('seconds', 0) for j in jobs if j['model'] == 'km') / 60:.1f} min. A0 / A1 PASS.\n",
         "Per-case means (macro-average) at each model's own label-free point, after the change point localizer.\n",
         "| model | sensitivity | precision | F1 | FP/day | window AUROC | seizures caught | false alarms |",
         "|---|---|---|---|---|---|---|---|"]
    L += [f"| {LABEL[m]} | {r.sens:.3f} | {r.prec:.3f} | {r.f1:.3f} | {r.fp_day:.1f} | {r.window_auroc:.3f} | "
          f"{r.seizures_caught} / {r.seizures} | {r.false_alarms} |" for m, r in m7.reindex(present).iterrows()]
    for title, df in (("K-means - GAE, u-CBLOF - GAE, u-CBLOF - K-means: paired subject bootstrap (23 units, B = 10,000)", pb),
                      ("Small-cluster diagnostic per case (computed after scoring; means over 18 channels)", dg),
                      ("Sensitivity on each detector curve at the GAE's own FP/day", mr),
                      ("Chosen number of clusters (label-free rule)", ks),
                      ("K-means per case", kc), ("Fixed 0.005 point", t7[t7.point == "fixed0.005"])):
        L += [f"\n## {title}\n", "```", df.round(4).to_string(index=False), "```"]
    L += [f"\nSmoke projection (computed): {proj}"]
    (out / "SUMMARY.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
