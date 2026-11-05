#!/usr/bin/env python
"""
f1_aggregate.py -- verification and PRE-REGISTERED reading of Track F1/F2 (docs/FUTURE_RESEARCH_PLAN.md rev 1, section 3).
Written before any Track F result exists. Inputs: the downloaded notebook outputs (one folder p{r} per partition, as
written by f1_run.py) + partition 0 = the committed model comparison (results/model_cmp/, rows of the GAE and the
MLP-AE, seed 42).

Verification (STOP on failure): every gate PASS in every notebook; 200 epochs; code and partitions sha identical in
every notebook and equal to the committed partitions.json; 8 jobs done per partition with G2 PASS; 24 cases x 2 models
x 2 points x 2 stages per partition; n_ref and non-ictal hours of every case identical in every partition (= partition
0); each case scored in the fold that partitions.json assigns it.

Pre-registered reading (unit = per-case mean over the 24 cases, own label-free point, after CPD; P = all partitions
incl. partition 0; random-only = sensitivity analysis):
  F1  per partition: sensitivity, precision, F1, FP/day, window AUROC of each model (+ the 8 thesis test patients and
      the other 16 cases); across partitions: mean +- SD, range (SD = sensitivity to the partition and seed, NOT
      uncertainty: the training sets overlap); uncertainty = paired-subject bootstrap (23 units, B = 10,000) of the
      across-partition mean (each case first averaged over partitions).
  F2  per partition: paired subject bootstrap of dF1 = MLP-AE - GAE; across partitions: n_pos = partitions with
      dF1 > 0, and the bootstrap CI of the across-partition mean dF1 (each case's dF1 averaged over partitions).
      "stable advantage of the MLP-AE" iff n_pos >= ceil(0.8 P) AND CI low > 0; "stable advantage of the GAE" iff
      n_neg >= ceil(0.8 P) AND CI high < 0; otherwise "not stable".
  Secondary, pre-registered, never decisive: dF1 at the fixed 0.005 budget; sensitivity of each model on its detector
  curve at the GAE's own FP/day (same alarm rate); dFP/day at the own point; d window AUROC; seizures caught and
  false alarms (counts) per partition.

  python src/f1_aggregate.py results/f1_repcv/raw [--out results/f1_repcv] [--allow-test]
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
B = 10_000
MODELS = ("gae", "mlp")
TEST8 = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}
UNIT = lambda s: "chb01" if s in ("chb01", "chb21") else s   # noqa: E731
GATES_REQ = {"D0", "G-const", "G-vec", "G-mlp", "GG0"}


def per_case(d):
    d = d.copy()
    d["sens"] = d.tp / d.n_ref
    d["prec"] = d.tp / (d.tp + d.fp).where(d.tp + d.fp > 0)
    d["f1"] = 2 * d.tp / (2 * d.tp + d.fp + (d.n_ref - d.tp))
    d["fp_day"] = d.fp / d.nonict_h * 24
    return d


def boot_mean(v, seed=0):
    """paired-subject bootstrap of the mean over cases of a per-case Series v (index = case)."""
    v = v.dropna()
    units = sorted({UNIT(s) for s in v.index})
    by = {u: [s for s in v.index if UNIT(s) == u] for u in units}
    rng = np.random.default_rng(seed)
    st = np.empty(B)
    for b in range(B):
        st[b] = v.loc[[s for u in rng.choice(units, len(units), replace=True) for s in by[u]]].mean()
    return float(v.mean()), float(np.percentile(st, 2.5)), float(np.percentile(st, 97.5)), len(units)


def load(indir, parts_json, allow_test):
    want_sha = hashlib.sha256(parts_json.read_bytes()).hexdigest()[:16]
    P = json.loads(parts_json.read_text())["partitions"]
    T = {k: [] for k in ("per_subject", "curves", "auroc", "seizures", "training_log")}
    problems, meta_rows = [], []
    seen_parts = {}
    for d in sorted(Path(indir).rglob("p*/run_meta.json")):
        pdir = d.parent
        meta = json.loads(d.read_text()); p = int(meta["partition"])
        if "SMOKE" in str(meta.get("notebook", "")):
            print(f"skipped (smoke notebook, not a run): {pdir}")
            continue
        if p in seen_parts:
            problems.append((p, "partition loaded twice", str(seen_parts[p]), str(pdir)))
            continue
        seen_parts[p] = pdir
        meta_rows.append(dict(partition=p, **{k: meta.get(k) for k in ("notebook", "torch", "gpus", "cpu_count",
                                                                       "core_sha", "partitions_sha", "epochs",
                                                                       "repo_commit", "notebook_runtime_h")}))
        if meta.get("partitions_sha") != want_sha:
            problems.append((p, "partitions sha", meta.get("partitions_sha"), want_sha))
        if meta.get("epochs") != 200 and not allow_test:
            problems.append((p, "epochs", meta.get("epochs")))
        gates = json.loads((pdir / "gates.json").read_text()) if (pdir / "gates.json").exists() else []
        seen = {g["gate"] for g in gates if g.get("status") == "PASS"}
        if not GATES_REQ <= seen or any(g.get("status") != "PASS" for g in gates):
            problems.append((p, "gates", sorted(GATES_REQ - seen), [g for g in gates if g.get("status") != "PASS"]))
        done = sorted(x.parent.name for x in (pdir / "jobs").glob("*/DONE.json"))
        if len(done) != 8:
            problems.append((p, "jobs done", done))
        for fj in (pdir / "jobs").glob("*/fit.json"):
            fit = json.loads(fj.read_text())
            if fit.get("G2") != "PASS":
                problems.append((p, "G2", fj.parent.name))
            if fit.get("core_sha") != meta.get("core_sha"):
                problems.append((p, "core sha differs inside the partition", fj.parent.name))
        for k in T:
            if (pdir / f"{k}.csv").exists():
                x = pd.read_csv(pdir / f"{k}.csv")
                x["partition"] = p
                T[k].append(x)
        for f, v in P[str(p)]["folds"].items():                        # each case scored in its own fold
            ps = pd.read_csv(pdir / "per_subject.csv") if (pdir / "per_subject.csv").exists() else pd.DataFrame()
            if len(ps):
                got = sorted(ps[ps.fold == int(f)].subject.unique())
                if got != sorted(v["held_out_cases"]):
                    problems.append((p, f"fold {f} cases", got, sorted(v["held_out_cases"])))
    shas = {m["core_sha"] for m in meta_rows}
    if len(shas) > 1:
        problems.append(("all", "different core sha between notebooks", shas))
    # partition 0 = the committed model comparison (GAE and MLP-AE rows, seed 42)
    mc = ROOT / "results" / "model_cmp"
    for k in ("per_subject", "curves", "auroc", "seizures"):
        x = pd.read_csv(mc / f"{k}.csv")
        x = x[x.model.isin(MODELS)].copy(); x["partition"] = 0
        T[k].append(x)
    return {k: (pd.concat(v, ignore_index=True) if v else pd.DataFrame()) for k, v in T.items()}, problems, meta_rows


def completeness(per, problems):
    dup = per.groupby(["partition", "model", "subject", "point", "stage"]).size()
    if (dup > 1).any():
        problems.append(("duplicated rows", dup[dup > 1].to_dict()))
    for (p, m), g in per.groupby(["partition", "model"]):
        if len(g) != 24 * 4 or g.subject.nunique() != 24:
            problems.append((p, m, "rows", len(g), g.subject.nunique()))
    ref = per[per.partition == 0].drop_duplicates("subject").set_index("subject")[["n_ref", "nonict_h"]]
    for p, g in per.groupby("partition"):
        x = g.drop_duplicates("subject").set_index("subject")[["n_ref", "nonict_h"]].reindex(ref.index)
        if not ((x.n_ref == ref.n_ref).all() and (np.abs(x.nonict_h - ref.nonict_h) < 1e-6).all()):
            problems.append((p, "n_ref / non-ictal hours differ from partition 0"))


def curve_at(curves, model, p, fp_target):
    c = per_case(curves[(curves.model == model) & (curves.partition == p)])
    c = c.groupby("top")[["sens", "fp_day"]].mean().sort_values("fp_day")
    return float(np.interp(fp_target, c.fp_day.values, c.sens.values))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("indir")
    ap.add_argument("--out", default=str(ROOT / "results" / "f1_repcv"))
    ap.add_argument("--partitions", default=str(ROOT / "results" / "f1_repcv" / "partitions.json"))
    ap.add_argument("--allow-test", action="store_true", help="synthetic tests only (epochs != 200)")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    T, problems, metas = load(a.indir, Path(a.partitions), a.allow_test)
    per = per_case(T["per_subject"])
    completeness(per, problems)
    if problems:
        (out / "VERIFICATION_FAILED.json").write_text(json.dumps(problems, indent=1, default=str))
        raise SystemExit(f"STOP verification: {problems}")
    own = per[(per.point == "own") & (per.stage == "localized")]
    fix = per[(per.point == "fixed0.005") & (per.stage == "localized")]
    au = T["auroc"]
    parts = sorted(int(x) for x in own.partition.unique())
    rnd = [p for p in parts if p != 0]
    Pn = len(parts)
    # ---------------------------------------------------------------- F1: per partition and across partitions
    rows = []
    for (p, m), g in own.groupby(["partition", "model"]):
        t8, o16 = g[g.subject.isin(TEST8)], g[~g.subject.isin(TEST8)]
        rows.append(dict(partition=p, model=m, sens=g.sens.mean(), prec=g.prec.mean(), f1=g.f1.mean(),
                         fp_day=g.fp_day.mean(), auroc=au[(au.partition == p) & (au.model == m)].auroc.mean(),
                         seizures_caught=int(g.tp.sum()), n_ref=int(g.n_ref.sum()), false_alarms=int(g.fp.sum()),
                         sens_test8=t8.sens.mean(), fp_day_test8=t8.fp_day.mean(), caught_test8=int(t8.tp.sum()),
                         sens_other16=o16.sens.mean(), fp_day_other16=o16.fp_day.mean()))
    T1 = pd.DataFrame(rows)
    T2 = []
    for m in MODELS:
        for setname, sel in (("all", parts), ("random_only", rnd)):
            x = T1[(T1.model == m) & T1.partition.isin(sel)]
            for met in ("sens", "prec", "f1", "fp_day", "auroc", "sens_test8", "sens_other16"):
                T2.append(dict(model=m, set=setname, n_partitions=len(x), metric=met, mean=x[met].mean(),
                               sd=x[met].std(ddof=1) if len(x) > 1 else np.nan, min=x[met].min(), max=x[met].max()))
    T2 = pd.DataFrame(T2)
    T3 = []
    for m in MODELS:
        g = own[own.model == m]
        for met in ("sens", "f1", "fp_day", "prec"):
            mean, lo, hi, nu = boot_mean(g.groupby("subject")[met].mean())
            T3.append(dict(model=m, metric=met, mean_over_partitions=mean, lo=lo, hi=hi, n_units=nu, n_partitions=Pn))
    T3 = pd.DataFrame(T3)
    # ---------------------------------------------------------------- F2: paired dF1 per partition and across
    def delta(tab, met):
        w = tab.pivot_table(index=["partition", "subject"], columns="model", values=met)
        return (w["mlp"] - w["gae"]).rename(f"d_{met}")
    dF1, dF1_fix = delta(own, "f1"), delta(fix, "f1")
    dS, dFP = delta(own, "sens"), delta(own, "fp_day")
    dAU = (au.pivot_table(index=["partition", "subject"], columns="model", values="auroc")
           .pipe(lambda w: w["mlp"] - w["gae"]))
    T4 = []
    for p in parts:
        m_, lo, hi, _ = boot_mean(dF1.loc[p])
        f_, flo, fhi, _ = boot_mean(dF1_fix.loc[p])
        s_, slo, shi, _ = boot_mean(dS.loc[p])
        gfp = T1[(T1.partition == p) & (T1.model == "gae")].fp_day.iloc[0]
        T4.append(dict(partition=p, dF1=m_, dF1_lo=lo, dF1_hi=hi, dSens=s_, dSens_lo=slo, dSens_hi=shi,
                       dFP_day=dFP.loc[p].mean(), dAUROC=dAU.loc[p].mean(), dF1_fixed0005=f_, dF1_fixed_lo=flo,
                       dF1_fixed_hi=fhi, wins=int((dF1.loc[p] > 0).sum()), losses=int((dF1.loc[p] < 0).sum()),
                       gae_fp_day=gfp, sens_at_gae_fp_gae=curve_at(T["curves"], "gae", p, gfp),
                       sens_at_gae_fp_mlp=curve_at(T["curves"], "mlp", p, gfp),
                       caught_gae=int(own[(own.partition == p) & (own.model == "gae")].tp.sum()),
                       caught_mlp=int(own[(own.partition == p) & (own.model == "mlp")].tp.sum()),
                       fa_gae=int(own[(own.partition == p) & (own.model == "gae")].fp.sum()),
                       fa_mlp=int(own[(own.partition == p) & (own.model == "mlp")].fp.sum())))
    T4 = pd.DataFrame(T4)
    need = math.ceil(0.8 * Pn)
    n_pos, n_neg = int((T4.dF1 > 0).sum()), int((T4.dF1 < 0).sum())
    across = {}
    for name, ser in (("dF1", dF1), ("dF1_fixed0005", dF1_fix), ("dSens", dS), ("dFP_day", dFP), ("dAUROC", dAU)):
        across[name] = boot_mean(ser.groupby(level="subject").mean())[:3]
    mean, lo, hi = across["dF1"]
    if n_pos >= need and lo > 0:
        verdict = "stable advantage of the MLP-AE (without message passing)"
    elif n_neg >= need and hi < 0:
        verdict = "stable advantage of the GAE"
    else:
        verdict = "not stable"
    T5 = pd.DataFrame([dict(quantity=k, mean=v[0], lo=v[1], hi=v[2]) for k, v in across.items()])
    # ---------------------------------------------------------------- per-subject table (case x partition x model)
    PS = own[["partition", "model", "fold", "subject", "tp", "fp", "n_ref", "nonict_h", "sens", "prec", "f1", "fp_day", "k"]]
    for name, df in (("F1_per_partition", T1), ("F1_across_partitions", T2), ("F1_bootstrap", T3),
                     ("F2_per_partition", T4), ("F2_across_partitions", T5), ("per_subject_table", PS),
                     ("notebooks", pd.DataFrame(metas))):
        df.to_csv(out / f"{name}.csv", index=False)
    g2 = T2[(T2.model == "gae") & (T2.set == "all")].set_index("metric")
    g3 = T3[T3.model == "gae"].set_index("metric")
    L = [f"# Track F1/F2 — repeated random patient-wise 4-fold CV (CHB-MIT, 24 cases / 23 subjects)\n",
         f"Partitions: {parts} (0 = the committed CV, seed 42; r = random partition r, seed r). Verification: PASS. "
         "Per-case means, own label-free point, after CPD.\n",
         "## F1 — per partition\n", "```", T1.round(3).to_string(index=False), "```",
         "\n## F1 — across partitions (SD = sensitivity to partition + seed, not uncertainty)\n", "```",
         T2.round(3).to_string(index=False), "```",
         "\n## F1 — subject bootstrap of the across-partition mean (uncertainty)\n", "```",
         T3.round(3).to_string(index=False), "```",
         f"\n**Statement (pre-registered form):** over {Pn} patient partitions (each with its own training seed), the "
         f"GAE's 4-fold CV per-case mean sensitivity is {g2.loc['sens', 'mean']:.3f} ± {g2.loc['sens', 'sd']:.3f} "
         f"(range {g2.loc['sens', 'min']:.3f}–{g2.loc['sens', 'max']:.3f}) at {g2.loc['fp_day', 'mean']:.1f} ± "
         f"{g2.loc['fp_day', 'sd']:.1f} FP/day; 95 % CI of the mean over subjects [{g3.loc['sens', 'lo']:.3f}, "
         f"{g3.loc['sens', 'hi']:.3f}].\n",
         "## F2 — MLP-AE minus GAE, per partition (paired subject bootstrap)\n", "```", T4.round(3).to_string(index=False),
         "```", "\n## F2 — across partitions\n", "```", T5.round(3).to_string(index=False), "```",
         f"\n**Rule:** stable iff dF1 > 0 in ≥ {need} of {Pn} partitions AND the CI of the across-partition mean "
         f"excludes 0. dF1 > 0 in {n_pos} / {Pn}; across-partition mean dF1 {mean:+.3f} [{lo:+.3f}, {hi:+.3f}] → "
         f"**{verdict}**. Secondary rows (fixed 0.005, same alarm rate, AUROC) are descriptive only.\n"]
    (out / "SUMMARY.md").write_text("\n".join(L) + "\n")
    (out / "VERDICT.json").write_text(json.dumps(dict(partitions=parts, n_pos=n_pos, n_neg=n_neg, need=need,
                                                      dF1_mean=mean, dF1_lo=lo, dF1_hi=hi, verdict=verdict), indent=1, default=float))
    print("\n".join(L))


if __name__ == "__main__":
    main()
