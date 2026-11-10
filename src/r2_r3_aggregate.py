#!/usr/bin/env python
"""
r2_r3_aggregate.py -- stage R3 reading (docs/FUTURE_RESEARCH_PLAN.md rev 2, §7 "Pre-registered reading"; §12 row 10/11,
chat D18-F). Written and tested on synthetic data and committed BEFORE any R3 output exists. Descriptive beside the
pre-registered F1 / F2 reading: no new pass/fail threshold (plan P2); nothing here replaces a locked number of the thesis.

Inputs (read only): the record -- results/f1_repcv/ (raw/p1..p5 = the F1 notebooks on the earlier data copy; the committed
tables and VERDICT.json), results/model_cmp/ (partition 0 of the record: GAE and MLP-AE rows, seed 42); the rerun --
results/r2/r3_repcv/p1..p5 (the R3 notebooks, src/r2_r3.py; F1 layout + cf/ + r30/), results/r2/r2_cv/a (partition 0 of
the rerun = R2_A) and results/r2/r2_cv/b/cf (its counterfactual).

Steps:
  A0 (gate, STOP) the closed pre-registered reading src/f1_aggregate.py, run unchanged on results/f1_repcv/raw, reproduces
     the committed results/f1_repcv/{F1_per_partition, F1_across_partitions, F1_bootstrap, F2_per_partition,
     F2_across_partitions, per_subject_table, notebooks}.csv (relative 1e-9) and VERDICT.json, and the locked S18 §18.8
     numbers (GAE 0.736 +- 0.012, range 0.723-0.753, 27.3 +- 1.1 FP/day, F1 0.210 +- 0.009, CI [0.612, 0.854], 8 test
     patients 0.575 +- 0.013, other 16 0.817 +- 0.016; dF1 > 0 in 6/6, +0.075 [+0.034, +0.121]; dSens -0.009 [-0.086,
     +0.062]; dFP/day -8.1 [-11.0, -5.3]; dAUROC +0.082 [+0.058, +0.111]; dF1 at 0.005 +0.060 [-0.012, +0.127]).
  A1 (gate, STOP) the rerun is complete and gated: partitions 1-5 each once; run_meta partition / seed / epochs 200 /
     partitions sha = the committed file; one r2_r3 code sha for all five, r2_r2 sha 542968bb; gates.json holds G-data,
     D0', R3-projection, G-const, G-vec, G-mlp, G-const-p, R3.0-gae, R3.0-mlp, all PASS and nothing else failed; 8 training
     jobs DONE (G2 PASS, 3,964 parameters, 200 epochs, training windows = the notebook's expected count, seed = partition);
     8 counterfactual jobs DONE; rows 2 models x 24 cases x 2 points x 2 stages for the run and the counterfactual, no
     duplicate, each case in the fold partitions.json gives it; partition 0 = R2_A (G-data, D0', G-const, G-vec, G-mlp
     PASS; 8 jobs; GAE / MLP-AE rows complete) with R2_B's GAE / MLP-AE counterfactual rows; n_ref of every case = the
     record's in every partition; non-ictal hours equal across the six rerun partitions and = the record except chb11 /
     chb21 (larger).
  A2 the pre-registered F1 / F2 reading, src/f1_aggregate.py run unchanged on the rerun (partition 0 = R2_A's rows; the
     closed script reads partition 0 from <root>/results/model_cmp, so it runs with its ROOT pointed at a staging folder
     holding R2_A's rows there, and with its required-gate set replaced by the R3 gate names above -- its own D0 / GG0
     are R2-era names; everything else unchanged) -> aggregate/f1_reading/ (tables, SUMMARY.md, VERDICT.json).
  A3 record_vs_rerun.csv: F1 per partition (GAE, MLP-AE) and F2 per partition, record beside rerun; verdict.csv.
  A4 bootstrap.csv: paired subject bootstrap (B = 10,000, rng seed 0; unit = subject, chb01 + chb21 one unit; statistic =
     mean over the resampled cases) of rerun - record, data (cf - record) and new models (rerun - cf); per model, per
     partition and across partitions (each case first averaged over the partitions); sensitivity, F1, FP/day; points own
     and fixed0.005, stage localized. Also dF1 (MLP-AE - GAE) of the record, the counterfactual and the rerun per partition.
  A5 per_subject.csv (partition x model x case x system; role thesis test / other; chb11, chb21 flagged), k.csv (own-point
     k per partition x model x fold: record, cf, rerun), seizures.csv (caught record / rerun per partition and model:
     both, record only, rerun only, neither), test8.csv (descriptive, not pre-registered: per partition the per-patient
     sensitivity and FP/day of both models on the 8 thesis test patients, record and rerun), r30.csv (the R3.0 gate
     summaries of the five notebooks).
  A6 SUMMARY.md (tables only; the reading is written in the plan by the chat, from these files).
  python src/r2_r3_aggregate.py --runs results/r2/r3_repcv [--out DIR]
  python src/r2_r3_aggregate.py --a0-only
"""
import argparse
import json
import math
import os
import shutil
import sys
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(os.environ.get("THESIS_REPO", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(REPO / "src"))
import f1_aggregate as FA                # noqa: E402  (closed, read only: the pre-registered F1 / F2 reading)
from r2_r2_aggregate import boot, per_case  # noqa: E402  (closed, read only: the R2 bootstrap and per-case metrics)

F1 = REPO / "results" / "f1_repcv"
MC = REPO / "results" / "model_cmp"
R2A = REPO / "results" / "r2" / "r2_cv" / "a"
R2B_CF = REPO / "results" / "r2" / "r2_cv" / "b" / "cf"
PARTS = (1, 2, 3, 4, 5)
MODELS = ("gae", "mlp")
POINTS, STAGES = ("own", "fixed0.005"), ("detector", "localized")
GAP = ("chb11", "chb21")
TEST8 = ("chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18")
KEYS = ["partition", "model", "subject", "point", "stage"]
R2_SHA = "542968bb851bc05c"
R3_GATES = {"G-data", "D0'", "R3-projection", "G-const", "G-vec", "G-mlp", "G-const-p", "R3.0-gae", "R3.0-mlp"}
R2A_GATES = {"G-data", "D0'", "G-const", "G-vec", "G-mlp"}
A0_FILES = ("F1_per_partition", "F1_across_partitions", "F1_bootstrap", "F2_per_partition", "F2_across_partitions",
            "per_subject_table", "notebooks")
TEST = bool(os.environ.get("R2_TEST"))


def log(*a):
    print(*a, flush=True)


def _same(a, b):
    if a.shape != b.shape or list(a.columns) != list(b.columns):
        return False
    num = a.select_dtypes("number").columns
    return bool(np.allclose(a[num].values.astype(float), b[num].values.astype(float), rtol=1e-9, atol=1e-12,
                            equal_nan=True)) and bool((a.drop(columns=num).astype(str).values
                                                       == b.drop(columns=num).astype(str).values).all())


def run_f1_reading(indir, out, root=None, gates_req=None, allow_test=False):
    """src/f1_aggregate.main, unchanged, in this process: ROOT (where it reads partition 0) and GATES_REQ (its required
    gate names) set for the call and restored afterwards. Returns its printed text."""
    keep = (FA.ROOT, FA.GATES_REQ, sys.argv)
    try:
        if root is not None:
            FA.ROOT = Path(root)
        if gates_req is not None:
            FA.GATES_REQ = set(gates_req)
        sys.argv = ["f1_aggregate.py", str(indir), "--out", str(out), "--partitions", str(F1 / "partitions.json")] + \
            (["--allow-test"] if allow_test else [])
        buf = StringIO()
        with redirect_stdout(buf):
            FA.main()
        return buf.getvalue()
    finally:
        FA.ROOT, FA.GATES_REQ, sys.argv = keep


# ============================================================================ A0
LOCKED = [  # S18 §18.8 (rounded as written there); table, selector, column, decimals, locked value
    ("F1_across_partitions", dict(model="gae", set="all", metric="sens"), "mean", 3, 0.736),
    ("F1_across_partitions", dict(model="gae", set="all", metric="sens"), "sd", 3, 0.012),
    ("F1_across_partitions", dict(model="gae", set="all", metric="sens"), "min", 3, 0.723),
    ("F1_across_partitions", dict(model="gae", set="all", metric="sens"), "max", 3, 0.753),
    ("F1_across_partitions", dict(model="gae", set="all", metric="fp_day"), "mean", 1, 27.3),
    ("F1_across_partitions", dict(model="gae", set="all", metric="fp_day"), "sd", 1, 1.1),
    ("F1_across_partitions", dict(model="gae", set="all", metric="f1"), "mean", 3, 0.210),
    ("F1_across_partitions", dict(model="gae", set="all", metric="f1"), "sd", 3, 0.009),
    ("F1_across_partitions", dict(model="gae", set="all", metric="sens_test8"), "mean", 3, 0.575),
    ("F1_across_partitions", dict(model="gae", set="all", metric="sens_test8"), "sd", 3, 0.013),
    ("F1_across_partitions", dict(model="gae", set="all", metric="sens_other16"), "mean", 3, 0.817),
    ("F1_across_partitions", dict(model="gae", set="all", metric="sens_other16"), "sd", 3, 0.016),
    ("F1_bootstrap", dict(model="gae", metric="sens"), "lo", 3, 0.612),
    ("F1_bootstrap", dict(model="gae", metric="sens"), "hi", 3, 0.854),
    ("F2_across_partitions", dict(quantity="dF1"), "mean", 3, 0.075),
    ("F2_across_partitions", dict(quantity="dF1"), "lo", 3, 0.034),
    ("F2_across_partitions", dict(quantity="dF1"), "hi", 3, 0.121),
    ("F2_across_partitions", dict(quantity="dSens"), "mean", 3, -0.009),
    ("F2_across_partitions", dict(quantity="dSens"), "lo", 3, -0.086),
    ("F2_across_partitions", dict(quantity="dSens"), "hi", 3, 0.062),
    ("F2_across_partitions", dict(quantity="dFP_day"), "mean", 1, -8.1),
    ("F2_across_partitions", dict(quantity="dFP_day"), "lo", 1, -11.0),
    ("F2_across_partitions", dict(quantity="dFP_day"), "hi", 1, -5.3),
    ("F2_across_partitions", dict(quantity="dAUROC"), "mean", 3, 0.082),
    ("F2_across_partitions", dict(quantity="dAUROC"), "lo", 3, 0.058),
    ("F2_across_partitions", dict(quantity="dAUROC"), "hi", 3, 0.111),
    ("F2_across_partitions", dict(quantity="dF1_fixed0005"), "mean", 3, 0.060),
    ("F2_across_partitions", dict(quantity="dF1_fixed0005"), "lo", 3, -0.012),
    ("F2_across_partitions", dict(quantity="dF1_fixed0005"), "hi", 3, 0.127),
]


def gate_a0(tmp):
    out = Path(tmp) / "a0"
    run_f1_reading(F1 / "raw", out, allow_test=TEST)
    checks = [dict(check=f"f1_aggregate reproduces {f}.csv", ok=_same(pd.read_csv(out / f"{f}.csv"),
                                                                       pd.read_csv(F1 / f"{f}.csv"))) for f in A0_FILES]
    v_new, v_rec = json.loads((out / "VERDICT.json").read_text()), json.loads((F1 / "VERDICT.json").read_text())
    checks.append(dict(check="f1_aggregate reproduces VERDICT.json", ok=v_new == v_rec))
    if TEST:                                    # synthetic test: the record is generated, the locks do not apply
        bad = [c for c in checks if not c["ok"]]
        return dict(gate="A0", status="PASS" if not bad else "FAIL", checks=checks, bad=bad, locked="skipped (test)")
    for tab, sel, col, dec, want in LOCKED:
        t = pd.read_csv(F1 / f"{tab}.csv")
        for k, v in sel.items():
            t = t[t[k] == v]
        got = round(float(t[col].iloc[0]), dec) if len(t) == 1 else None
        checks.append(dict(check=f"S18 §18.8 {tab} {sel} {col}", locked=want, computed=got,
                           ok=got is not None and abs(got - want) < 0.5 * 10 ** -dec))
    checks.append(dict(check="S18 §18.8 dF1 > 0 in 6/6, verdict", locked="6/6 stable advantage of the MLP-AE",
                       computed=f"{v_rec['n_pos']}/{len(v_rec['partitions'])} {v_rec['verdict']}",
                       ok=v_rec["n_pos"] == 6 and len(v_rec["partitions"]) == 6 and "MLP-AE" in v_rec["verdict"]))
    bad = [c for c in checks if not c["ok"]]
    return dict(gate="A0", status="PASS" if not bad else "FAIL", checks=checks, bad=bad)


# ============================================================================ inputs
def _rows(folder, name):
    f = Path(folder) / f"{name}.csv"
    return pd.read_csv(f) if f.exists() and f.stat().st_size > 1 else pd.DataFrame()


def load_record():
    """record rows (F1 layout): partitions 1-5 from results/f1_repcv/raw, partition 0 = results/model_cmp (GAE, MLP-AE)."""
    T = {}
    for nm in ("per_subject", "seizures", "auroc", "curves"):
        parts = []
        for p in PARTS:
            x = _rows(F1 / "raw" / f"p{p}", nm)
            parts.append(x.assign(partition=p))
        x = _rows(MC, nm)
        parts.append(x[x.model.isin(MODELS)].assign(partition=0))
        T[nm] = pd.concat(parts, ignore_index=True)
    return T


def load_rerun(runs):
    """rerun rows: partitions 1-5 from the R3 folders (run and cf), partition 0 = R2_A (run) and R2_B's cf."""
    run, cf, seiz, au, r30 = [], [], [], [], {}
    for p in PARTS:
        d = Path(runs) / f"p{p}"
        run.append(_rows(d, "per_subject").assign(partition=p))
        cf.append(_rows(d / "cf", "per_subject").assign(partition=p))
        seiz.append(_rows(d, "seizures").assign(partition=p))
        au.append(_rows(d, "auroc").assign(partition=p))
        s = d / "r30" / "r30_summary.json"
        r30[p] = json.loads(s.read_text()) if s.exists() else None
    a = _rows(R2A / "model_cmp", "per_subject")
    run.append(a[a.model.isin(MODELS)].assign(partition=0))
    c = _rows(R2B_CF, "per_subject")
    cf.append(c[c.model.isin(MODELS)].assign(partition=0) if len(c) else c)
    s = _rows(R2A / "model_cmp", "seizures")
    seiz.append(s[s.model.isin(MODELS)].assign(partition=0))
    u = _rows(R2A / "model_cmp", "auroc")
    au.append(u[u.model.isin(MODELS)].assign(partition=0))
    cat = lambda L: pd.concat([x for x in L if len(x)], ignore_index=True)  # noqa: E731
    return cat(run), cat(cf), cat(seiz), cat(au), r30


# ============================================================================ A1
def gate_a1(runs, rec, run, cf):
    bad, metas = [], {}
    parts = json.loads((F1 / "partitions.json").read_text())["partitions"]
    want_psha = __import__("hashlib").sha256((F1 / "partitions.json").read_bytes()).hexdigest()[:16]
    for p in PARTS:
        d = Path(runs) / f"p{p}"
        if not (d / "run_meta.json").exists():
            bad.append((p, "no run_meta.json"))
            continue
        m = json.loads((d / "run_meta.json").read_text())
        metas[p] = m
        if int(m.get("partition", -1)) != p or int(m.get("seed", -1)) != p:
            bad.append((p, "partition / seed", m.get("partition"), m.get("seed")))
        if m.get("partitions_sha") != want_psha:
            bad.append((p, "partitions sha", m.get("partitions_sha"), want_psha))
        if not TEST and (m.get("epochs") != 200 or m.get("r2_r2_sha") != R2_SHA or m.get("test_mode")):
            bad.append((p, "epochs / r2_r2 sha / test mode", m.get("epochs"), m.get("r2_r2_sha"), m.get("test_mode")))
        g = json.loads((d / "gates.json").read_text()) if (d / "gates.json").exists() else []
        st = {x["gate"]: x["status"] for x in g}
        if not R3_GATES <= {k for k, v in st.items() if v == "PASS"} or any(v != "PASS" for v in st.values()):
            bad.append((p, "gates", sorted(R3_GATES - set(st)), {k: v for k, v in st.items() if v != "PASS"}))
        metas_new = json.loads((d / "fold_metas_new.json").read_text()) if (d / "fold_metas_new.json").exists() else {}
        for stage, names in (("jobs", [f"{x}_fold{f}" for x in MODELS for f in (1, 2, 3, 4)]),
                             ("cfjobs", [f"cf_{x}_fold{f}" for x in MODELS for f in (1, 2, 3, 4)])):
            for n in names:
                fj = d / stage / n / "fit.json"
                if not (d / stage / n / "DONE.json").exists() or not fj.exists():
                    bad.append((p, f"{stage}/{n} not done"))
                    continue
                fit = json.loads(fj.read_text())
                if fit.get("code_sha") != m.get("r2_r3_sha"):
                    bad.append((p, f"{stage}/{n} code sha"))
                if stage == "jobs":
                    exp = sum(int(v) for v in metas_new.get(str(fit.get("fold")), {}).get("n_train", {}).values())
                    if fit.get("G2") != "PASS" or fit.get("n_params") != 3964 or int(fit.get("seed", -1)) != p or \
                            fit.get("n_train") != exp or (not TEST and fit.get("epochs") != 200):
                        bad.append((p, f"jobs/{n}", {k: fit.get(k) for k in ("G2", "n_params", "seed", "n_train", "epochs")},
                                    exp))
    shas = {m.get("r2_r3_sha") for m in metas.values()}
    if len(shas) != 1:
        bad.append(("all", "r2_r3 code sha differs between notebooks", shas))
    ga = json.loads((R2A / "gates.json").read_text()) if (R2A / "gates.json").exists() else []
    sa = {x["gate"]: x["status"] for x in ga}
    if not R2A_GATES <= {k for k, v in sa.items() if v == "PASS"} or any(v not in ("PASS",) for v in sa.values()):
        bad.append((0, "R2_A gates", sa))
    if len(list((R2A / "jobs").glob("*/DONE.json"))) != 8:
        bad.append((0, "R2_A jobs"))
    for name, d in (("run", run), ("cf", cf)):
        dup = d.duplicated(KEYS)
        if dup.any():
            bad.append((name, "duplicated rows", int(dup.sum())))
        for p in (0,) + PARTS:
            for model in MODELS:
                g = d[(d.partition == p) & (d.model == model)]
                if len(g) != 24 * len(POINTS) * len(STAGES) or g.subject.nunique() != 24:
                    bad.append((name, p, model, "rows", len(g)))
                if p in PARTS:
                    for f, v in parts[str(p)]["folds"].items():
                        got = sorted(g[g.fold == int(f)].subject.unique())
                        if got != sorted(v["held_out_cases"]):
                            bad.append((name, p, model, f"fold {f} cases", got))
    mg = rec.merge(run, on=KEYS, suffixes=("_rec", ""))
    if len(mg) != len(rec) or (mg.n_ref != mg.n_ref_rec).any():
        bad.append(("n_ref differs from the record or rows unmatched", len(mg), len(rec)))
    h = run.drop_duplicates(["partition", "subject"]).pivot(index="subject", columns="partition", values="nonict_h")
    if not np.allclose(h.values, h.values[:, :1], rtol=0, atol=1e-9):
        bad.append(("non-ictal hours differ between rerun partitions",))
    hr = rec.drop_duplicates("subject").set_index("subject").nonict_h
    hn = h.iloc[:, 0]
    free = [s for s in hn.index if s not in GAP]
    if not np.allclose(hn[free], hr[free], atol=1e-6) or not (hn[list(GAP)] > hr[list(GAP)]).all():
        bad.append(("non-ictal hours vs record (22 equal, chb11 / chb21 larger)",))
    return dict(gate="A1", status="PASS" if not bad else "FAIL", bad=bad, partitions=list(PARTS),
                r2_r3_sha=sorted(s for s in shas if s), run_rows=len(run), cf_rows=len(cf))


# ============================================================================ tables
def stage_reading_input(runs, tmp):
    """the rerun in the layout f1_aggregate reads: indir = copies of p1..p5 (top-level files, gates, run_meta, jobs/*
    fit + DONE); root/results/model_cmp = R2_A's GAE / MLP-AE rows (partition 0)."""
    ind, root = Path(tmp) / "rerun_in", Path(tmp) / "root"
    for p in PARTS:
        src, dst = Path(runs) / f"p{p}", ind / f"p{p}"
        dst.mkdir(parents=True)
        for f in src.iterdir():
            if f.is_file():
                shutil.copyfile(f, dst / f.name)
        for j in (src / "jobs").iterdir():
            (dst / "jobs" / j.name).mkdir(parents=True)
            for nm in ("fit.json", "DONE.json"):
                if (j / nm).exists():
                    shutil.copyfile(j / nm, dst / "jobs" / j.name / nm)
    mc = root / "results" / "model_cmp"
    mc.mkdir(parents=True)
    for nm in ("per_subject", "curves", "auroc", "seizures"):
        x = _rows(R2A / "model_cmp", nm)
        x[x.model.isin(MODELS)].to_csv(mc / f"{nm}.csv", index=False)
    return ind, root


def tables(rec, run, cf):
    sysd = {"record": per_case(rec), "cf": per_case(cf), "rerun": per_case(run)}
    S = []
    for name, d in sysd.items():
        g = d.groupby(["partition", "model", "point", "stage"])
        s = g[["sens", "prec", "f1", "fp_day"]].mean().join(g[["tp", "fp", "n_ref"]].sum()).join(g.size().rename("cases"))
        S.append(s.reset_index().assign(system=name))
    summary = pd.concat(S, ignore_index=True)
    Bt = []
    for m in MODELS:
        for pt in POINTS:
            sel = lambda d, p: d[(d.model == m) & (d.point == pt) & (d.stage == "localized")  # noqa: E731
                                 & ((d.partition == p) if p != "all" else True)]
            for p in (0,) + PARTS + ("all",):
                r, c, n = (sel(sysd[k], p).groupby("subject")[["sens", "f1", "fp_day"]].mean()
                           for k in ("record", "cf", "rerun"))
                for step, a, b in (("rerun - record", n, r), ("data (cf - record)", c, r), ("new models (rerun - cf)", n, c)):
                    for met in ("sens", "f1", "fp_day"):
                        Bt.append(dict(model=m, point=pt, stage="localized", partition=p, step=step, metric=met,
                                       **boot(a[met] - b[met])))
    bootstrap = pd.DataFrame(Bt)
    dd = []
    for name, d in sysd.items():
        o = d[(d.point == "own") & (d.stage == "localized")]
        w = o.pivot_table(index=["partition", "subject"], columns="model", values="f1")
        dl = (w["mlp"] - w["gae"])
        for p in (0,) + PARTS + ("all",):
            v = dl.groupby(level="subject").mean() if p == "all" else dl.loc[p]
            dd.append(dict(system=name, partition=p, quantity="dF1 (MLP-AE - GAE)", **boot(v)))
    dF1 = pd.DataFrame(dd)
    ps = []
    for name, d in sysd.items():
        ps.append(d[KEYS + ["fold", "tp", "fp", "n_ref", "nonict_h", "sens", "f1", "fp_day"]].assign(system=name))
    per_subject = pd.concat(ps, ignore_index=True)
    per_subject["data_changed"] = per_subject.subject.isin(GAP)
    per_subject["role"] = np.where(per_subject.subject.isin(TEST8), "thesis test", "other")
    kk = []
    for name, d in sysd.items():
        kk.append(d[(d.point == "own") & (d.stage == "localized")].groupby(["partition", "model", "fold"]).k.first()
                  .rename(f"k_{name}"))
    k_tab = pd.concat(kk, axis=1).reset_index()
    t8 = []
    for name in ("record", "rerun"):
        o = sysd[name][(sysd[name].point == "own") & (sysd[name].stage == "localized") & sysd[name].subject.isin(TEST8)]
        g = o.groupby(["partition", "model"])
        t8.append(g[["sens", "fp_day", "f1"]].mean().join(g.tp.sum().rename("caught")).join(g.n_ref.sum())
                  .reset_index().assign(system=name))
    test8 = pd.concat(t8, ignore_index=True)
    return summary, bootstrap, dF1, per_subject, k_tab, test8


def seizure_table(rec_seiz, run_seiz):
    key = ["partition", "model", "subject", "file", "onset_s"]
    mg = rec_seiz[key + ["caught"]].merge(run_seiz[key + ["caught"]], on=key, how="outer",
                                          suffixes=("_record", "_rerun"), indicator=True)
    out = []
    for (p, m), g in mg.groupby(["partition", "model"]):
        both = g[g._merge == "both"]
        cr, cn = both.caught_record.astype(bool), both.caught_rerun.astype(bool)
        out.append(dict(partition=p, model=m, seizures=len(both), unmatched=int((g._merge != "both").sum()),
                        caught_record=int(cr.sum()), caught_rerun=int(cn.sum()), both=int((cr & cn).sum()),
                        record_only=int((cr & ~cn).sum()), rerun_only=int((~cr & cn).sum()),
                        neither=int((~cr & ~cn).sum())))
    return pd.DataFrame(out)


def record_vs_rerun(out):
    rows = []
    for tab in ("F1_per_partition", "F2_per_partition"):
        r, n = pd.read_csv(F1 / f"{tab}.csv"), pd.read_csv(out / "f1_reading" / f"{tab}.csv")
        key = ["partition", "model"] if "model" in r.columns else ["partition"]
        rows.append(r.merge(n, on=key, suffixes=("_record", "_rerun")).assign(table=tab))
    rv = pd.concat(rows, ignore_index=True)
    vr, vn = json.loads((F1 / "VERDICT.json").read_text()), json.loads((out / "f1_reading" / "VERDICT.json").read_text())
    verdict = pd.DataFrame([dict(system="record (earlier data copy)", **vr), dict(system="rerun (complete data)", **vn)])
    verdict["partitions"] = verdict.partitions.astype(str)
    across = pd.read_csv(F1 / "F2_across_partitions.csv").merge(
        pd.read_csv(out / "f1_reading" / "F2_across_partitions.csv"), on="quantity", suffixes=("_record", "_rerun"))
    f1a = pd.read_csv(F1 / "F1_across_partitions.csv").merge(
        pd.read_csv(out / "f1_reading" / "F1_across_partitions.csv"), on=["model", "set", "metric"],
        suffixes=("_record", "_rerun"))
    return rv, verdict, across, f1a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=str(REPO / "results" / "r2" / "r3_repcv"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--a0-only", action="store_true")
    a = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="r3agg_"))
    try:
        a0 = gate_a0(tmp)
        log(f"A0 {a0['status']}: {a0['bad']}")
        if a0["status"] != "PASS":
            raise SystemExit(f"STOP A0: {a0['bad']}")
        if a.a0_only:
            return
        out = Path(a.out or (Path(a.runs) / "aggregate"))
        out.mkdir(parents=True, exist_ok=True)
        R = load_record()
        run, cf, seiz, au, r30 = load_rerun(a.runs)
        a1 = gate_a1(a.runs, R["per_subject"], run, cf)
        log(f"A1 {a1['status']}: {a1['bad']}")
        (out / "gates.json").write_text(json.dumps([a0, a1], indent=1, default=str))
        if a1["status"] != "PASS":
            raise SystemExit(f"STOP A1: {a1['bad']}")
        ind, root = stage_reading_input(a.runs, tmp)
        txt = run_f1_reading(ind, out / "f1_reading", root=root, gates_req=R3_GATES, allow_test=TEST)
        rv, verdict, across, f1a = record_vs_rerun(out)
        summary, bootstrap, dF1, per_subject, k_tab, test8 = tables(R["per_subject"], run, cf)
        stab = seizure_table(R["seizures"], seiz)
        r30t = pd.DataFrame([dict(partition=p, model=m, **{k: v for k, v in c.items()
                                                           if k not in ("differing_rows", "checkpoints_sha256")})
                             for p, s in r30.items() if s for m, c in s.items()])
        for name, df in (("record_vs_rerun", rv), ("verdict", verdict), ("F2_across_record_vs_rerun", across),
                         ("F1_across_record_vs_rerun", f1a), ("summary", summary), ("bootstrap", bootstrap),
                         ("dF1_by_system", dF1), ("per_subject", per_subject), ("k", k_tab), ("seizures", stab),
                         ("test8", test8), ("r30", r30t)):
            df.to_csv(out / f"{name}.csv", index=False)
        own = summary[(summary.point == "own") & (summary.stage == "localized")]
        main_t = own.pivot_table(index=["model", "partition"], columns="system", values=["sens", "f1", "fp_day"])
        acr = bootstrap[(bootstrap.partition == "all") & (bootstrap.point == "own")]
        L = ["# R3 aggregate — F1 / F2 re-executed on complete data vs the record (earlier data copy)\n",
             f"Gates: A0 {a0['status']}, A1 {a1['status']} (partitions {a1['partitions']}; r2_r3 {a1['r2_r3_sha']})\n",
             "## Pre-registered verdict (src/f1_aggregate.py, unchanged)\n", "```",
             verdict[["system", "n_pos", "n_neg", "need", "dF1_mean", "dF1_lo", "dF1_hi", "verdict"]].round(3)
             .to_string(index=False), "```",
             "\n## F2 across partitions, record vs rerun\n", "```", across.round(3).to_string(index=False), "```",
             "\n## F1 across partitions (GAE, MLP-AE; SD = sensitivity to partition + seed, not uncertainty)\n", "```",
             f1a[f1a.set == "all"].round(3).to_string(index=False), "```",
             "\n## Per-case means per partition, own point, after CPD (record / cf / rerun)\n", "```",
             main_t.round(3).to_string(), "```",
             "\n## Rerun vs record and its split, across partitions (own point, after CPD)\n", "```",
             acr.round(3).to_string(index=False), "```",
             "\n## dF1 (MLP-AE - GAE) per partition: record, counterfactual, rerun\n", "```",
             dF1.round(3).to_string(index=False), "```",
             "\n## 8 thesis test patients (descriptive, not pre-registered)\n", "```", test8.round(3).to_string(index=False),
             "```", "\n## R3.0 gates\n", "```", r30t.to_string(index=False) if len(r30t) else "(none)", "```",
             "\nThe pre-registered reading itself: `f1_reading/` (SUMMARY.md, VERDICT.json). Per subject: `per_subject.csv`; "
             "k per fold: `k.csv`; seizures: `seizures.csv`. Descriptive only (plan P2); no row replaces a locked number "
             "of the thesis."]
        (out / "SUMMARY.md").write_text("\n".join(L) + "\n")
        log("\n".join(L))
        log(txt[-600:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
