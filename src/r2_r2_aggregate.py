#!/usr/bin/env python
"""
r2_r2_aggregate.py -- stage R2 reading (docs/FUTURE_RESEARCH_PLAN.md rev 2, §6 "Reading"; §12 row 08/11, chat D16-F).
Written and tested on synthetic data and committed BEFORE any R2 output exists. Descriptive: no pass/fail threshold on
any difference (plan P2); nothing here replaces a locked number of the thesis.

Inputs: the record (read only) -- results/model_cmp/ (per_subject.csv, seizures.csv, raw/, summary.csv,
paired_bootstrap.csv, ...); the R2 notebook outputs results/r2/r2_cv/<tag>/ (tags a = R2_A, b = R2_B, c = R2_C), each with
model_cmp/ (run rows, the comparison's format) and cf/ (counterfactual rows: committed models on the new data).

Steps:
  A0 (gate, STOP) the closed pre-registered aggregate (src/model_cmp_aggregate.py, run unchanged on results/model_cmp/raw)
     reproduces the committed results/model_cmp/{summary, paired_bootstrap, matched_rate, complementarity, transfer}.csv
     (relative 1e-9) and the locked S18 §18.6 numbers (per-case sensitivity / F1 / FP/day of the six models at their own
     point after CPD; MLP-AE - GAE F1 +0.070 [+0.026, +0.117]).
  A1 (gate, STOP) the rerun is complete: 6 models x 24 cases x 2 points x 2 stages, no duplicate, n_ref = the record's;
     counterfactual rows complete for gae, mlp and cnn; every run folder's gates.json has G-data and D0' PASS and no
     failed gate, and the folder holding the CNN rows has R2.0-cnn PASS (plan §12 08/11 19:10: R2_C gates the CNN code
     path before training).
  A2 the pre-registered analyses A-F of the comparison plan (§4 there), run unchanged on the rerun
     (src/model_cmp_aggregate.py) -> aggregate/model_cmp/; and model_vs_gae.csv: table B (model - GAE, paired subject
     bootstrap) of the record beside the rerun's.
  A3 rows_vs_record.csv, summary.csv: per model x point x stage x system (record, cf, rerun) the per-case means
     (sensitivity, precision, F1, FP/day) and summed counts.
  A4 bootstrap.csv: paired subject bootstrap (B = 10,000, rng seed 0; unit = subject, chb01 + chb21 one unit; statistic =
     the mean over the resampled cases) of rerun - record and its split: data = cf - record (autoencoders, CNN) or
     rerun - record (IF: no training; trees, SVM: deterministic training), new models = rerun - cf; sensitivity, F1,
     FP/day; points own and fixed0.005, stage localized.
  A5 per_subject.csv (role: thesis test / other; chb11, chb21 flagged), k.csv (own-point k per model and fold: record,
     cf, rerun), seizures.csv (caught by the record, by the rerun: both / record only / rerun only / neither, per model).
  A6 SUMMARY.md (tables only; the reading is written in the plan by the chat, from these files).
  python src/r2_r2_aggregate.py --runs results/r2/r2_cv/a results/r2/r2_cv/b results/r2/r2_cv/c [--out DIR]
  python src/r2_r2_aggregate.py --a0-only
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MC = REPO / "results" / "model_cmp"
ORDER = ["gae", "mlp", "if", "svm", "hgb", "cnn"]
CF_MODELS = ("gae", "mlp", "cnn")
POINTS, STAGES = ("own", "fixed0.005"), ("detector", "localized")
GAP = ("chb11", "chb21")
TEST8 = ("chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18")
B, RNG_SEED = 10_000, 0
UNIT = lambda s: "chb01" if s in ("chb01", "chb21") else s   # noqa: E731
KEYS = ["model", "subject", "point", "stage"]
LOCKED = {  # S18 §18.6: per-case means, own point, after CPD (sensitivity, F1, FP/day)
    "gae": (0.735, 0.203, 28.4), "mlp": (0.711, 0.273, 20.2), "if": (0.680, 0.212, 24.1),
    "svm": (0.626, 0.163, 33.7), "hgb": (0.755, 0.221, 35.2), "cnn": (0.777, 0.218, 35.1)}
LOCKED_MLP_F1 = (0.070, 0.026, 0.117)
A0_FILES = ("summary.csv", "paired_bootstrap.csv", "matched_rate.csv", "complementarity.csv", "transfer.csv")


def log(*a):
    print(*a, flush=True)


def run_closed_aggregate(indir, out):
    r = subprocess.run([sys.executable, str(REPO / "src" / "model_cmp_aggregate.py"), str(indir), "--out", str(out)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"STOP: model_cmp_aggregate.py failed on {indir}:\n{r.stderr[-2000:]}")
    return r.stdout


def _same(a, b):
    if a.shape != b.shape or list(a.columns) != list(b.columns):
        return False
    num = a.select_dtypes("number").columns
    return bool(np.allclose(a[num].values.astype(float), b[num].values.astype(float), rtol=1e-9, atol=1e-12,
                            equal_nan=True)) and bool((a.drop(columns=num).astype(str).values
                                                       == b.drop(columns=num).astype(str).values).all())


def gate_a0(tmp):
    out = Path(tmp) / "a0"
    run_closed_aggregate(MC / "raw", out)
    checks = [dict(check=f"model_cmp_aggregate reproduces {f}", ok=_same(pd.read_csv(out / f), pd.read_csv(MC / f)))
              for f in A0_FILES]
    if os.environ.get("R2_TEST"):                     # synthetic test: the record is generated, the locks do not apply
        bad = [c for c in checks if not c["ok"]]
        return dict(gate="A0", status="PASS" if not bad else "FAIL", checks=checks, bad=bad, locked="skipped (test)")
    s = pd.read_csv(MC / "summary.csv")
    s = s[(s.point == "own") & (s.stage == "localized")].set_index("model")
    for m, (se, f1, fa) in LOCKED.items():
        got = (round(float(s.loc[m, "sens"]), 3), round(float(s.loc[m, "f1"]), 3), round(float(s.loc[m, "fp_day"]), 1))
        checks.append(dict(check=f"S18 §18.6 {m} sens / F1 / FP/day", locked=(se, f1, fa), computed=got, ok=got == (se, f1, fa)))
    pb = pd.read_csv(MC / "paired_bootstrap.csv")
    r = pb[(pb.model == "mlp") & (pb.metric == "f1")].iloc[0]
    got = (round(float(r["diff"]), 3), round(float(r.lo), 3), round(float(r.hi), 3))
    checks.append(dict(check="S18 §18.6 MLP-AE - GAE F1 [CI]", locked=LOCKED_MLP_F1, computed=got, ok=got == LOCKED_MLP_F1))
    bad = [c for c in checks if not c["ok"]]
    return dict(gate="A0", status="PASS" if not bad else "FAIL", checks=checks, bad=bad)


# ============================================================================ inputs
def per_case(d):
    d = d.copy()
    d["sens"] = d.tp / d.n_ref
    d["prec"] = d.tp / (d.tp + d.fp).where(d.tp + d.fp > 0)
    d["f1"] = 2 * d.tp / (2 * d.tp + d.fp + (d.n_ref - d.tp))
    d["fp_day"] = d.fp / d.nonict_h * 24
    return d


def run_gates(runs):
    """per run folder: {gate: status} from its gates.json and the models of its run rows (A1 provenance check)."""
    out = {}
    for r in runs:
        r = Path(r)
        g = json.loads((r / "gates.json").read_text()) if (r / "gates.json").exists() else []
        ps = r / "model_cmp" / "per_subject.csv"
        out[str(r)] = dict(gates={x["gate"]: x["status"] for x in g},
                           models=sorted(set(pd.read_csv(ps).model)) if ps.exists() else [])
    return out


def load_runs(runs):
    run, cf, seiz_run, seiz_cf, folders = [], [], [], [], []
    for r in runs:
        r = Path(r)
        if (r / "model_cmp" / "per_subject.csv").exists():
            run.append(pd.read_csv(r / "model_cmp" / "per_subject.csv"))
            folders.append(r / "model_cmp")
            if (r / "model_cmp" / "seizures.csv").exists():
                seiz_run.append(pd.read_csv(r / "model_cmp" / "seizures.csv"))
        if (r / "cf" / "per_subject.csv").exists():
            cf.append(pd.read_csv(r / "cf" / "per_subject.csv"))
            if (r / "cf" / "seizures.csv").exists():
                seiz_cf.append(pd.read_csv(r / "cf" / "seizures.csv"))
    cat = lambda L: pd.concat(L, ignore_index=True) if L else pd.DataFrame(columns=KEYS)  # noqa: E731
    return cat(run), cat(cf), cat(seiz_run), cat(seiz_cf), folders


def gate_a1(rec, run, cf, rg=None):
    bad = []
    for r, v in (rg or {}).items():
        g = v["gates"]
        if g.get("G-data") != "PASS" or g.get("D0'") != "PASS":
            bad.append(("G-data / D0' not PASS", r))
        if any(st not in ("PASS", "n/a") for st in g.values()):
            bad.append(("failed gate", r, {k: st for k, st in g.items() if st not in ("PASS", "n/a")}))
        if "cnn" in v["models"] and g.get("R2.0-cnn") != "PASS":
            bad.append(("CNN rows without R2.0-cnn PASS", r))
    if run.duplicated(KEYS).any():
        bad.append(("duplicated run rows", int(run.duplicated(KEYS).sum())))
    want = {(m, s, p, st) for m in ORDER for s in rec.subject.unique() for p in POINTS for st in STAGES}
    got = set(map(tuple, run[KEYS].values))
    if want - got:
        bad.append(("missing run rows", len(want - got), sorted(want - got)[:10]))
    mg = rec.merge(run, on=KEYS, suffixes=("_rec", ""))
    if (mg.n_ref != mg.n_ref_rec).any():
        bad.append(("n_ref differs", int((mg.n_ref != mg.n_ref_rec).sum())))
    cfm = sorted(set(cf.model)) if len(cf) else []
    for m in cfm:
        c = cf[cf.model == m]
        if c.duplicated(KEYS).any() or len(c) != 24 * len(POINTS) * len(STAGES):
            bad.append((f"cf {m} rows", len(c)))
    for m in CF_MODELS:
        if m not in cfm:
            bad.append((f"cf {m} missing",))
    return dict(gate="A1", status="PASS" if not bad else "FAIL", bad=bad, cf_models=cfm, run_rows=len(run))


# ============================================================================ tables
def boot(d, seed=RNG_SEED):
    """d: Series indexed by subject (per-case difference). Paired subject bootstrap of the mean over cases."""
    d = d.dropna()
    units = sorted({UNIT(s) for s in d.index})
    usum = np.array([d[[s for s in d.index if UNIT(s) == u]].sum() for u in units])
    ucnt = np.array([sum(UNIT(s) == u for s in d.index) for u in units])
    rng = np.random.default_rng(seed)
    pick = rng.integers(0, len(units), (B, len(units)))
    stats = usum[pick].sum(1) / ucnt[pick].sum(1)
    return dict(diff=float(d.mean()), lo=float(np.percentile(stats, 2.5)), hi=float(np.percentile(stats, 97.5)),
                n_cases=int(len(d)), n_units=len(units), cases_changed=int((d != 0).sum()))


def tables(rec, run, cf):
    sysd = {"record": per_case(rec), "rerun": per_case(run), "cf": per_case(cf) if len(cf) else per_case(rec.iloc[:0])}
    wide = sysd["record"][KEYS + ["fold", "n_ref", "nonict_h", "tp", "fp", "k"]].rename(
        columns={"tp": "tp_record", "fp": "fp_record", "k": "k_record", "nonict_h": "nonict_h_record"})
    for name in ("cf", "rerun"):
        x = sysd[name][KEYS + ["tp", "fp", "k", "nonict_h"]].rename(
            columns={"tp": f"tp_{name}", "fp": f"fp_{name}", "k": f"k_{name}", "nonict_h": f"nonict_h_{name}"})
        wide = wide.merge(x, on=KEYS, how="left")
    wide["data_changed"] = wide.subject.isin(GAP)
    wide["role"] = np.where(wide.subject.isin(TEST8), "thesis test", "other")
    S = []
    for name, d in sysd.items():
        if not len(d):
            continue
        g = d.groupby(["model", "point", "stage"])
        s = g[["sens", "prec", "f1", "fp_day"]].mean().join(g[["tp", "fp", "n_ref"]].sum()).join(g.size().rename("cases"))
        S.append(s.reset_index().assign(system=name))
    summary = pd.concat(S, ignore_index=True)
    Bt = []
    for m in ORDER:
        for p in POINTS:
            sel = lambda d: d[(d.model == m) & (d.point == p) & (d.stage == "localized")].set_index("subject")  # noqa: E731
            r, n = sel(sysd["record"]), sel(sysd["rerun"])
            c = sel(sysd["cf"]) if m in set(sysd["cf"].model) else None
            steps = [("rerun - record", n, r)]
            if m in CF_MODELS:
                if c is not None and len(c):
                    steps += [("data (cf - record)", c, r), ("new models (rerun - cf)", n, c)]
            else:
                steps += [("data (rerun - record; no training / deterministic)", n, r)]
            for step, a, b in steps:
                for met in ("sens", "f1", "fp_day"):
                    Bt.append(dict(model=m, point=p, stage="localized", step=step, metric=met, **boot(a[met] - b[met])))
    bootstrap = pd.DataFrame(Bt)
    ps = []
    for name, d in sysd.items():
        if len(d):
            ps.append(d[KEYS + ["fold", "tp", "fp", "n_ref", "nonict_h", "sens", "f1", "fp_day"]].assign(system=name))
    per_subject = pd.concat(ps, ignore_index=True)
    per_subject["data_changed"] = per_subject.subject.isin(GAP)
    per_subject["role"] = np.where(per_subject.subject.isin(TEST8), "thesis test", "other")
    kk = []
    for name, d in sysd.items():
        if len(d):
            k = d[(d.point == "own") & (d.stage == "localized")].groupby(["model", "fold"]).k.first().rename(f"k_{name}")
            kk.append(k)
    k_tab = pd.concat(kk, axis=1).reset_index()
    return wide, summary, bootstrap, per_subject, k_tab


def seizure_table(seiz_run):
    rec = pd.read_csv(MC / "seizures.csv")
    key = ["model", "subject", "file", "onset_s"]
    mg = rec[key + ["caught"]].merge(seiz_run[key + ["caught"]], on=key, how="outer", suffixes=("_record", "_rerun"),
                                     indicator=True)
    out = []
    for m, g in mg.groupby("model"):
        both = g[g._merge == "both"]
        cr, cn = both.caught_record.astype(bool), both.caught_rerun.astype(bool)
        out.append(dict(model=m, seizures=len(both), unmatched=int((g._merge != "both").sum()),
                        caught_record=int(cr.sum()), caught_rerun=int(cn.sum()), both=int((cr & cn).sum()),
                        record_only=int((cr & ~cn).sum()), rerun_only=int((~cr & cn).sum()), neither=int((~cr & ~cn).sum())))
    return pd.DataFrame(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="*", default=[])
    ap.add_argument("--out", default=None)
    ap.add_argument("--a0-only", action="store_true")
    a = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="r2agg_"))
    try:
        a0 = gate_a0(tmp)
        log(f"A0 {a0['status']}: {a0['bad']}")
        if a0["status"] != "PASS":
            raise SystemExit(f"STOP A0: {a0['bad']}")
        if a.a0_only:
            return
        out = Path(a.out or (REPO / "results" / "r2" / "r2_cv" / "aggregate"))
        out.mkdir(parents=True, exist_ok=True)
        rec = pd.read_csv(MC / "per_subject.csv")
        run, cf, seiz_run, _seiz_cf, folders = load_runs(a.runs)
        a1 = gate_a1(rec, run, cf, run_gates(a.runs))
        log(f"A1 {a1['status']}: {a1['bad']}")
        gates = [a0, a1]
        (out / "gates.json").write_text(json.dumps(gates, indent=1, default=str))
        if a1["status"] != "PASS":
            raise SystemExit(f"STOP A1: {a1['bad']}")
        ind = tmp / "rerun_in"
        for i, f in enumerate(folders):
            shutil.copytree(f, ind / f"nb{i}")          # a copy: rglob does not follow symlinked folders
        run_closed_aggregate(ind, out / "model_cmp")
        rb, nb = pd.read_csv(MC / "paired_bootstrap.csv"), pd.read_csv(out / "model_cmp" / "paired_bootstrap.csv")
        mvg = rb.merge(nb, on=["model", "reference", "metric"], suffixes=("_record", "_rerun"))
        wide, summary, bootstrap, per_subject, k_tab = tables(rec, run, cf)
        stab = seizure_table(seiz_run) if len(seiz_run) else pd.DataFrame()
        for name, df in (("rows_vs_record", wide), ("summary", summary), ("bootstrap", bootstrap),
                         ("per_subject", per_subject), ("k", k_tab), ("seizures", stab), ("model_vs_gae", mvg)):
            df.to_csv(out / f"{name}.csv", index=False)
        main_t = summary[(summary.point == "own") & (summary.stage == "localized")].pivot_table(
            index="model", columns="system", values=["sens", "f1", "fp_day"]).reindex(ORDER)
        L = ["# R2 aggregate — four-fold CV and six models re-executed on complete data vs the record (descriptive)\n",
             f"Gates: A0 {a0['status']}, A1 {a1['status']} (counterfactual models: {a1['cf_models']})\n",
             "## Per-case means, own label-free point, after CPD (record / counterfactual / rerun)\n", "```",
             main_t.round(3).to_string(), "```",
             "\n## Model - GAE (paired subject bootstrap): record vs rerun\n", "```",
             mvg[["model", "metric", "diff_record", "lo_record", "hi_record", "diff_rerun", "lo_rerun", "hi_rerun"]]
             .round(3).to_string(index=False), "```",
             "\n## Rerun vs record and its split (own point, after CPD)\n", "```",
             bootstrap[bootstrap.point == "own"].round(3).to_string(index=False), "```",
             "\n## Own-point k per fold\n", "```", k_tab.round(4).to_string(index=False), "```",
             "\n## Seizures caught, record vs rerun\n", "```", stab.to_string(index=False) if len(stab) else "(none)", "```",
             "\nPre-registered analyses A-F on the rerun: `model_cmp/`. Per row: `rows_vs_record.csv`; per subject: "
             "`per_subject.csv`. Descriptive only (plan P2); no row replaces a locked number of the thesis."]
        (out / "SUMMARY.md").write_text("\n".join(L) + "\n")
        log("\n".join(L))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
