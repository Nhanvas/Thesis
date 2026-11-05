#!/usr/bin/env python
"""
model_cmp_aggregate.py -- verification and the PRE-REGISTERED analysis of the model comparison rev 2
(docs/MODEL_COMPARISON_PLAN.md rev 2, sections 4-5). Written before any result exists. Reads the Kaggle outputs
(one folder per notebook, each with model_cmp/...), checks the gates and the completeness, then:

  A  main table: per-case means (24 cases) at each model's own label-free point after CPD -- sensitivity,
     precision, F1, FP/day; + the fixed 0.005 point; + window AUROC.
  B  paired subject bootstrap (B = 10,000) of every model minus the GAE, per-case F1 and sensitivity; the unit is
     the SUBJECT (chb01 + chb21 one unit, 23 units), the statistic the mean over the resampled cases.
  C  detector-stage curve: per-case mean sensitivity vs per-case mean FP/day over the common budget grid, and
     sensitivity interpolated at the GAE's own per-case FP/day (each model read at the same alarm rate).
  D  per-seizure complementarity with the GAE (185 seizures): both / GAE only / model only / neither, joined to
     results/v9_v1/part1_descriptors.csv (amplitude ratio vs own background, duration): do other models catch
     the low-amplitude, short seizures the GAE misses?
  E  where the difference comes from: per-case wins / ties / losses vs the GAE and the largest single-case
     influence on the mean F1 difference (leave-one-subject-out of the mean difference).
  F  transfer: Spearman correlation across cases between window AUROC and event F1 for each model.

Reading rules (fixed now): a difference is stated only if the 95 % bootstrap CI excludes 0, otherwise "no
difference shown on 23 subjects, one seed"; supervised rows are a reference ceiling (labels of other patients),
never the system; no model is called "best" without that CI; no conclusion from C or D alone if B disagrees.

  python src/model_cmp_aggregate.py <dir_with_notebook_outputs> [--out results/model_cmp]
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ORDER = ["gae", "mlp", "if", "svm", "hgb", "cnn"]
LABEL = {"gae": "GAE (graph autoencoder, label-free)", "mlp": "MLP autoencoder (no graph, label-free)", "if": "Isolation Forest (label-free)",
         "svm": "Linear SVM (supervised)", "hgb": "Gradient-boosted trees (supervised)", "cnn": "1-D CNN (supervised)"}
B = 10_000
UNIT = lambda s: "chb01" if s in ("chb01", "chb21") else s   # noqa: E731


def per_case(d):
    d = d.copy()
    d["sens"] = d.tp / d.n_ref
    d["prec"] = d.tp / (d.tp + d.fp).where(d.tp + d.fp > 0)
    d["f1"] = 2 * d.tp / (2 * d.tp + d.fp + (d.n_ref - d.tp))
    d["fp_day"] = d.fp / d.nonict_h * 24
    return d


def load(indir):
    out = {k: [] for k in ("per_subject", "curves", "auroc", "seizures", "training_log")}
    gates, jobs = [], []
    for g in sorted(Path(indir).rglob("gates.json")):
        d = g.parent
        nb = json.loads((d / "run_meta.json").read_text()).get("notebook", d.parent.name)
        gates += [dict(x, notebook=nb) for x in json.loads(g.read_text())]
        if (d / "jobs.json").exists():
            jobs += [dict(x, notebook=nb) for x in json.loads((d / "jobs.json").read_text())]
        for k in out:
            if (d / f"{k}.csv").exists():
                out[k].append(pd.read_csv(d / f"{k}.csv"))
    return {k: (pd.concat(v, ignore_index=True) if v else pd.DataFrame()) for k, v in out.items()}, gates, jobs


def check(T, gates, jobs):
    bad = [g for g in gates if g.get("status") != "PASS"]
    notrun = [j for j in jobs if j["status"] != "done"]
    per = T["per_subject"]
    dup = per.groupby(["model", "subject", "point", "stage"]).size()
    if (dup > 1).any():
        raise SystemExit(f"STOP: duplicated rows {dup[dup > 1]}")
    own = per[(per.point == "own") & (per.stage == "localized")]
    for m, g in own.groupby("model"):
        if g.subject.nunique() != 24:
            print(f"INCOMPLETE: {m} has {g.subject.nunique()} of 24 cases -> not analysed")
    return bad, notrun


def boot_diff(own, model, ref="gae", metric="f1", seed=0):
    a = own[own.model == model].set_index("subject")[metric]
    r = own[own.model == ref].set_index("subject")[metric]
    d = (a - r).dropna()
    units = sorted({UNIT(s) for s in d.index})
    by_unit = {u: [s for s in d.index if UNIT(s) == u] for u in units}
    rng = np.random.default_rng(seed)
    stats = np.empty(B)
    for b in range(B):
        pick = rng.choice(units, len(units), replace=True)
        cases = [s for u in pick for s in by_unit[u]]
        stats[b] = d.loc[cases].mean()
    loo = {u: d.drop(by_unit[u]).mean() for u in units}
    worst = max(loo, key=lambda u: abs(loo[u] - d.mean()))
    return dict(model=model, reference=ref, metric=metric, n_cases=len(d), n_units=len(units), diff=d.mean(),
                lo=np.percentile(stats, 2.5), hi=np.percentile(stats, 97.5), wins=int((d > 0).sum()),
                ties=int((d == 0).sum()), losses=int((d < 0).sum()), most_influential_unit=worst,
                diff_without_it=loo[worst])


def curve_at(curves, model, fp_target):
    c = per_case(curves[curves.model == model]).groupby("top")[["sens", "fp_day"]].mean().sort_values("fp_day")
    return float(np.interp(fp_target, c.fp_day.values, c.sens.values)), c.reset_index()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("indir")
    ap.add_argument("--out", default=str(ROOT / "results" / "model_cmp"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    T, gates, jobs = load(a.indir)
    bad, notrun = check(T, gates, jobs)
    per = per_case(T["per_subject"])
    own = per[(per.point == "own") & (per.stage == "localized")]
    present = [m for m in ORDER if m in set(own.model) and own[own.model == m].subject.nunique() == 24]
    # A
    A = (per[per.model.isin(present)].groupby(["model", "point", "stage"])
         [["sens", "prec", "f1", "fp_day"]].mean().reset_index())
    au = T["auroc"].groupby("model").auroc.mean().rename("window_auroc")
    A = A.merge(au, on="model", how="left")
    # B, E
    Bt = pd.DataFrame([boot_diff(own, m, metric=mt) for m in present if m != "gae" for mt in ("f1", "sens")])
    # C
    gae_fp = own[own.model == "gae"].fp_day.mean() if "gae" in present else np.nan
    Cr, curves_all = [], []
    for m in present:
        s_at, c = curve_at(T["curves"], m, gae_fp)
        Cr.append(dict(model=m, sens_at_gae_fp_day=s_at, gae_fp_day=gae_fp)); curves_all.append(c.assign(model=m))
    Ct = pd.DataFrame(Cr)
    # D
    S = T["seizures"]
    desc = pd.read_csv(ROOT / "results" / "v9_v1" / "part1_descriptors.csv")
    desc = desc[desc.set != "siena"][["subject", "file", "onset_s", "amp_ratio"]]
    Dr = []
    if "gae" in present:
        g = S[S.model == "gae"][["subject", "file", "onset_s", "duration_s", "caught"]].rename(columns={"caught": "gae"})
        g = g.merge(desc, on=["subject", "file", "onset_s"], how="left")
        if g.amp_ratio.isna().any():
            print(f"WARNING: {int(g.amp_ratio.isna().sum())} seizures without a descriptor row")
        for m in present:
            if m == "gae":
                continue
            x = g.merge(S[S.model == m][["subject", "file", "onset_s", "caught"]], on=["subject", "file", "onset_s"])
            for name, sel in (("both", x.gae & x.caught), ("gae_only", x.gae & ~x.caught),
                              ("model_only", ~x.gae & x.caught), ("neither", ~x.gae & ~x.caught)):
                Dr.append(dict(model=m, group=name, n=int(sel.sum()), amp_ratio_median=x.amp_ratio[sel].median(),
                               duration_median=x.duration_s[sel].median()))
    Dt = pd.DataFrame(Dr)
    # F
    from scipy.stats import spearmanr
    Fr = []
    for m in present:
        j = own[own.model == m].merge(T["auroc"][T["auroc"].model == m], on=["model", "subject"])
        r, p = spearmanr(j.auroc, j.f1, nan_policy="omit")
        Fr.append(dict(model=m, spearman_auroc_vs_f1=r, p=p, n=len(j)))
    Ft = pd.DataFrame(Fr)
    for name, df in (("summary", A), ("paired_bootstrap", Bt), ("matched_rate", Ct), ("complementarity", Dt),
                     ("transfer", Ft), ("curves_mean", pd.concat(curves_all) if curves_all else pd.DataFrame())):
        df.to_csv(out / f"{name}.csv", index=False)
    for k, v in T.items():
        v.to_csv(out / f"{k}.csv", index=False)
    (out / "gates_all.json").write_text(json.dumps(dict(gates=gates, jobs=jobs), indent=1, default=str))
    main_t = A[(A.point == "own") & (A.stage == "localized")].set_index("model").reindex(present)
    L = ["# Model comparison rev 2 -- CHB-MIT, 4-fold patient-wise CV, 24 cases, seed 42\n",
         f"Gates not PASS: {len(bad)}; jobs not run: {len(notrun)}. Per-case means, own label-free point, after CPD.\n",
         "| model | sensitivity | precision | F1 | FP/day | window AUROC |", "|---|---|---|---|---|---|"]
    L += [f"| {LABEL[m]} | {r.sens:.3f} | {r.prec:.3f} | {r.f1:.3f} | {r.fp_day:.1f} | {r.window_auroc:.3f} |"
          for m, r in main_t.iterrows()]
    for title, df in (("B · paired subject bootstrap (model - GAE)", Bt), ("C · sensitivity at the GAE's FP/day", Ct),
                      ("D · per-seizure complementarity with the GAE", Dt), ("F · window AUROC vs event F1", Ft)):
        L += [f"\n## {title}\n", "```", df.round(3).to_string(index=False) if len(df) else "(none)", "```"]
    (out / "SUMMARY.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
