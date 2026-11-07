#!/usr/bin/env python
"""
r2_r1_aggregate.py -- stage R1 reading (docs/FUTURE_RESEARCH_PLAN.md rev 2, §5 "Reading"; §12 row 07/11 18:55).
Written, tested on synthetic data and committed BEFORE any R1_RUN output exists. Descriptive: no pass/fail threshold on
any difference (plan P2); nothing here replaces a locked number of the thesis.

Inputs: the record (committed, read only) -- results/p3c_freeze/per_subject.csv + errors.csv (development),
results/e23_test_look7/per_subject_seed.csv + errors.csv (test, points balanced = L2f and sensitivity = S),
results/e22_test_oneshot/per_subject_seed.csv (test, look 6 = frozen), results/x1_external/rows_*.csv + errors_*.csv
(chb24, Siena); and the R1_RUN output folder (r13/run = new models on the new data; r13/cf = committed models on the
new data, k recomputed; r13/cf_krec = the same at the record's k; r13/<label>/k.json; models/*.json).

Steps:
  A0 (gate, STOP) the per-patient metric used here (e22_test_oneshot.metrics, the SzCORE aggregate) reproduces the
     locked numbers from the record files: held-out seed 42 0.508 @ 21.8 (F1 0.174), 4 seeds 0.498 ± 0.010 @ 23.8 ± 1.3;
     final seed 42 0.577 @ 26.8 (F1 0.190), 4 seeds 0.567 ± 0.019 @ 28.7 ± 1.3; Siena 4 seeds 0.633 ± 0.079 @ 41.0,
     precision 0.160, F1 0.226; chb24 seed 42 14/16 @ 29.5; development (L2f, CPD) 4 seeds 0.832.
  A1 (gate, STOP) the run's files are complete: (15 + 8 + 15) cases x 4 seeds x 4 arms x 3 stages rows per system;
     n_ref of every rerun row = the record's (same annotations); record-vs-record differences are exactly 0.
  A2 rows_vs_record.csv: every record row beside the rerun (and the two counterfactuals): tp, fp, n_ref, non-ictal
     hours, differences. Mapping: e23 / x1 point balanced -> arm L2f, sensitivity -> S, look 6 -> frozen; stage
     'localized' -> cpd.
  A3 summary_per_seed.csv / summary.csv: per set (development, test, chb24, siena) x arm x stage x system, the
     per-patient means (sensitivity, precision, F1, FP/day) per seed and 4-seed mean ± SD (ddof 1), with counts.
  A4 bootstrap.csv: paired subject bootstrap (B = 10,000, rng seed 0; unit = subject; each subject's metric = its
     4-seed mean) of the per-patient mean difference, for rerun - record, cf_krec - record (data), cf - cf_krec (k),
     rerun - cf (new models); sensitivity, F1, FP/day. Subjects whose precision is undefined are kept (precision not
     bootstrapped).
  A5 attribution.csv + per_subject.csv: for every set x arm x stage the four systems' per-patient means and the three
     steps, beside the record's across-seed SD (scale of retraining randomness); per subject the 4-seed means, flags
     data_changed (chb11, chb21) and role (train / validation / test / external).
  A6 errors.csv: median |onset| / |offset| error (detector, CPD, hybrid) per set, arm and system, with n pairs.
  A7 SUMMARY.md (tables only; the reading is written in the plan by the chat, from these files).
  python src/r2_r1_aggregate.py --run results/r2/r1_system/run [--out <dir>]     (default out: <run>/aggregate)
  python src/r2_r1_aggregate.py --a0-only                                        (gate A0 on the record files only)
"""
import argparse
import glob
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(os.environ.get("THESIS_REPO", Path(__file__).resolve().parents[1]))
for _p in ("src", "src/retrain", "src/dataprep", "src/phaseB", "src/phaseC"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))
import e22_test_oneshot as E22          # noqa: E402  (record, read only: metrics = the per-patient SzCORE aggregate)

TAGS = ["clean_seed42", "clean_seed1", "clean_seed2", "clean_seed3"]
ARMS = ["frozen", "L2", "L2f", "S"]
STAGES = ["detector", "cpd", "hybrid"]
POINT_ARM = {"balanced": "L2f", "sensitivity": "S"}
SETS = ["development", "test", "chb24", "siena"]
TRAIN = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08", "chb09", "chb12", "chb19", "chb20", "chb21", "chb23"]
VAL = ["chb10", "chb11", "chb22"]
GAP = ("chb11", "chb21")
SYSTEMS = ["record", "cf_krec", "cf", "rerun"]
STEPS = [("rerun - record", "rerun", "record"), ("data (cf_krec - record)", "cf_krec", "record"),
         ("k (cf - cf_krec)", "cf", "cf_krec"), ("new models (rerun - cf)", "rerun", "cf")]
KEYS = ["set", "subject", "seed", "arm", "stage"]
B, RNG_SEED = 10_000, 0


def log(*a):
    print(*a, flush=True)


# ============================================================================ the record in one long table
def record_rows():
    rr = REPO / "results"
    p = pd.read_csv(rr / "p3c_freeze" / "per_subject.csv").rename(columns={"budget": "arm"}).assign(set="development")
    e = pd.read_csv(rr / "e23_test_look7" / "per_subject_seed.csv")
    e = e.assign(set="test", arm=e.point.map(POINT_ARM), stage=e.stage.replace({"localized": "cpd"}))
    l6 = pd.read_csv(rr / "e22_test_oneshot" / "per_subject_seed.csv")
    l6 = l6.assign(set="test", arm="frozen", stage=l6.stage.replace({"localized": "cpd"}))
    x = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(rr / "x1_external" / "rows_*.csv")))], ignore_index=True)
    x = x.assign(set=x["set"].map({"chb24": "chb24", "siena": "siena"}), arm=x.point.map(POINT_ARM),
                 stage=x.stage.replace({"localized": "cpd"}))
    cols = KEYS + ["tp", "fp", "n_ref", "nonict_h"]
    return pd.concat([d[cols] for d in (p, e, l6, x)], ignore_index=True).assign(system="record")


def record_errors():
    rr = REPO / "results"
    p = pd.read_csv(rr / "p3c_freeze" / "errors.csv").rename(columns={"budget": "arm"}).assign(set="development")
    e = pd.read_csv(rr / "e23_test_look7" / "errors.csv")
    e = e.assign(set="test", arm=e.point.map(POINT_ARM))
    fs = [f for f in sorted(glob.glob(str(rr / "x1_external" / "errors_*.csv"))) if Path(f).stat().st_size > 2]
    x = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
    x = x.assign(arm=x.point.map(POINT_ARM))
    cols = ["set", "subject", "seed", "arm", "det_on", "det_off", "cpd_on", "cpd_off", "hyb_on", "hyb_off"]
    return pd.concat([d[cols] for d in (p, e, x)], ignore_index=True).assign(system="record")


def run_rows(run, label, system):
    d = pd.read_csv(Path(run) / "r13" / label / "per_subject.csv").rename(columns={"budget": "arm"})
    d["set"] = np.where(d["set"] != "external", d["set"], np.where(d.subject == "chb24", "chb24", "siena"))
    return d[KEYS + ["tp", "fp", "n_ref", "nonict_h"]].assign(system=system)


def run_errors(run, label, system):
    d = pd.read_csv(Path(run) / "r13" / label / "errors.csv").rename(columns={"budget": "arm"})
    d["set"] = np.where(d["set"] != "external", d["set"], np.where(d.subject == "chb24", "chb24", "siena"))
    return d[["set", "subject", "seed", "arm", "det_on", "det_off", "cpd_on", "cpd_off", "hyb_on", "hyb_off"]].assign(
        system=system)


# ============================================================================ per-patient metrics
def per_seed(R):
    """per set x arm x stage x system x seed: e22_test_oneshot.metrics (one row per subject)."""
    out = []
    for (st, arm, stage, sysm, seed), g in R.groupby(["set", "arm", "stage", "system", "seed"]):
        m = E22.metrics(g.assign(short_tp=0, short_n=0))
        out.append(dict(set=st, arm=arm, stage=stage, system=sysm, seed=seed, subjects=int(g.subject.nunique()),
                        **{k: m[k] for k in ("tp", "n_ref", "fp", "s_sens", "s_prec", "s_f1", "s_fa")}))
    return pd.DataFrame(out)


def four_seed(S):
    g = S.groupby(["set", "arm", "stage", "system"])
    out = g.agg(seeds=("seed", "nunique"), subjects=("subjects", "max"), tp_mean=("tp", "mean"), n_ref=("n_ref", "max"),
                fp_mean=("fp", "mean"), sens=("s_sens", "mean"), sens_sd=("s_sens", "std"), prec=("s_prec", "mean"),
                f1=("s_f1", "mean"), f1_sd=("s_f1", "std"), fa=("s_fa", "mean"), fa_sd=("s_fa", "std")).reset_index()
    s42 = S[S.seed == "clean_seed42"].set_index(["set", "arm", "stage", "system"])
    for c, k in (("sens42", "s_sens"), ("fa42", "s_fa"), ("f1_42", "s_f1"), ("tp42", "tp"), ("fp42", "fp")):
        out[c] = [s42[k].get(tuple(r)) for r in out[["set", "arm", "stage", "system"]].values]
    return out


def per_subject(R):
    """each subject's 4-seed mean of its per-subject sensitivity, F1, FP/day (and precision where defined)."""
    d = R.assign(sens=R.tp / R.n_ref, f1=2 * R.tp / (2 * R.tp + R.fp + (R.n_ref - R.tp)), fa=R.fp / R.nonict_h * 24,
                 prec=R.tp / (R.tp + R.fp).where(R.tp + R.fp > 0))
    out = d.groupby(["set", "arm", "stage", "system", "subject"]).agg(
        seeds=("seed", "nunique"), sens=("sens", "mean"), f1=("f1", "mean"), fa=("fa", "mean"), prec=("prec", "mean"),
        tp=("tp", "mean"), fp=("fp", "mean"), n_ref=("n_ref", "max"), nonict_h=("nonict_h", "mean")).reset_index()
    out["role"] = out.subject.map(lambda s: "train" if s in TRAIN else "validation" if s in VAL else
                                  "external" if (s == "chb24" or s.startswith("PN")) else "test")
    out["data_changed"] = out.subject.isin(GAP)
    return out


def boot(P):
    """paired subject bootstrap of the per-patient mean difference for each step."""
    rng = np.random.default_rng(RNG_SEED)
    out = []
    for (st, arm, stage), g in P.groupby(["set", "arm", "stage"]):
        w = g.pivot_table(index="subject", columns="system", values=["sens", "f1", "fa"])
        subs = w.index.values
        idx = rng.integers(0, len(subs), size=(B, len(subs)))
        for name, a, b in STEPS:
            if ("sens", a) not in w.columns or ("sens", b) not in w.columns:
                continue
            for met in ("sens", "f1", "fa"):
                dlt = (w[(met, a)] - w[(met, b)]).values
                if np.isnan(dlt).any():
                    continue
                bs = dlt[idx].mean(axis=1)
                out.append(dict(set=st, arm=arm, stage=stage, step=name, metric=met, subjects=len(subs),
                                diff=float(dlt.mean()), ci_lo=float(np.percentile(bs, 2.5)),
                                ci_hi=float(np.percentile(bs, 97.5)), subjects_changed=int((np.abs(dlt) > 0).sum())))
    return pd.DataFrame(out)


def attribution(F, P, kinfo):
    rows = []
    for (st, arm, stage), g in F.groupby(["set", "arm", "stage"]):
        v = g.set_index("system")
        r = dict(set=st, arm=arm, stage=stage)
        for sysm in SYSTEMS:
            for c in ("sens", "fa", "f1"):
                r[f"{c}_{sysm}"] = float(v[c].get(sysm, np.nan)) if sysm in v.index else np.nan
        for name, a, b in STEPS:
            for c in ("sens", "fa", "f1"):
                r[f"d{c} {name}"] = r[f"{c}_{a}"] - r[f"{c}_{b}"]
        r["record_seed_sd_sens"] = float(v["sens_sd"].get("record", np.nan)) if "record" in v.index else np.nan
        r["record_seed_sd_fa"] = float(v["fa_sd"].get("record", np.nan)) if "record" in v.index else np.nan
        rows.append(r)
    A = pd.DataFrame(rows)
    for k_, val in kinfo.items():
        A[f"k_{k_}"] = val
    return A


def errors_table(E):
    out = []
    for (st, arm, sysm), g in E.groupby(["set", "arm", "system"]):
        r = dict(set=st, arm=arm, system=sysm, pairs=int(len(g)))
        for c in ("det_on", "det_off", "cpd_on", "cpd_off", "hyb_on", "hyb_off"):
            r[f"med_abs_{c}"] = float(g[c].abs().median())
        out.append(r)
    return pd.DataFrame(out)


# ============================================================================ gates
LOCKED = [  # (name, set, arm, stage, which, metric, value, decimals) -- NUMBERS_LOCK / project instructions §4
    ("held-out seed 42 sensitivity", "test", "frozen", "cpd", "s42", "s_sens", 0.508, 3),
    ("held-out seed 42 FP/day", "test", "frozen", "cpd", "s42", "s_fa", 21.8, 1),
    ("held-out seed 42 F1", "test", "frozen", "cpd", "s42", "s_f1", 0.174, 3),
    ("held-out 4 seeds sensitivity", "test", "frozen", "cpd", "mean", "s_sens", 0.498, 3),
    ("held-out 4 seeds sensitivity SD", "test", "frozen", "cpd", "sd", "s_sens", 0.010, 3),
    ("held-out 4 seeds FP/day", "test", "frozen", "cpd", "mean", "s_fa", 23.8, 1),
    ("held-out 4 seeds FP/day SD", "test", "frozen", "cpd", "sd", "s_fa", 1.3, 1),
    ("final seed 42 sensitivity", "test", "L2f", "cpd", "s42", "s_sens", 0.577, 3),
    ("final seed 42 FP/day", "test", "L2f", "cpd", "s42", "s_fa", 26.8, 1),
    ("final seed 42 F1", "test", "L2f", "cpd", "s42", "s_f1", 0.190, 3),
    ("final 4 seeds sensitivity", "test", "L2f", "cpd", "mean", "s_sens", 0.567, 3),
    ("final 4 seeds sensitivity SD", "test", "L2f", "cpd", "sd", "s_sens", 0.019, 3),
    ("final 4 seeds FP/day", "test", "L2f", "cpd", "mean", "s_fa", 28.7, 1),
    ("final 4 seeds FP/day SD", "test", "L2f", "cpd", "sd", "s_fa", 1.3, 1),
    ("Siena 4 seeds sensitivity", "siena", "L2f", "cpd", "mean", "s_sens", 0.633, 3),
    ("Siena 4 seeds sensitivity SD", "siena", "L2f", "cpd", "sd", "s_sens", 0.079, 3),
    ("Siena 4 seeds FP/day", "siena", "L2f", "cpd", "mean", "s_fa", 41.0, 1),
    ("Siena 4 seeds precision", "siena", "L2f", "cpd", "mean", "s_prec", 0.160, 3),
    ("Siena 4 seeds F1", "siena", "L2f", "cpd", "mean", "s_f1", 0.226, 3),
    ("chb24 seed 42 TP", "chb24", "L2f", "cpd", "s42", "tp", 14, 0),
    ("chb24 seed 42 references", "chb24", "L2f", "cpd", "s42", "n_ref", 16, 0),
    ("chb24 seed 42 FP/day", "chb24", "L2f", "cpd", "s42", "s_fa", 29.5, 1),
    ("development 4 seeds sensitivity", "development", "L2f", "cpd", "mean", "s_sens", 0.832, 3),
]


def gate_a0(Srec):
    bad, rows = [], []
    for name, st, arm, stage, which, met, val, dec in LOCKED:
        g = Srec[(Srec.set == st) & (Srec.arm == arm) & (Srec.stage == stage)]
        if which == "s42":
            got = float(g[g.seed == "clean_seed42"][met].iloc[0])
        elif which == "mean":
            got = float(g[met].mean())
        else:
            got = float(g[met].std(ddof=1))
        ok = round(got, dec) == round(val, dec)
        rows.append(dict(check=name, locked=val, computed=round(got, 6), ok=ok))
        if not ok:
            bad.append(name)
    return dict(gate="A0", status="PASS" if not bad else "FAIL", bad=bad, checks=rows)


def gate_a1(R, run):
    bad = []
    n_cases = {"development": 15, "test": 8, "chb24": 1, "siena": 14}
    if os.environ.get("R2_TEST") and os.environ.get("R2_TEST_N_CASES"):          # synthetic world only
        n_cases = json.loads(os.environ["R2_TEST_N_CASES"])
    for sysm in ("rerun", "cf", "cf_krec"):
        q = R[R.system == sysm]
        if not len(q):
            if sysm == "rerun":
                bad.append("rerun rows missing")
            continue
        want = sum(n_cases.values()) * len(TAGS) * len(ARMS) * len(STAGES)
        if len(q) != want:
            bad.append(f"{sysm}: {len(q)} rows, expected {want}")
        for st, n in n_cases.items():
            if q[q.set == st].subject.nunique() != n:
                bad.append(f"{sysm} {st}: {q[q.set == st].subject.nunique()} subjects, expected {n}")
    rec = R[R.system == "record"]
    m = R[R.system != "record"].merge(rec[KEYS + ["n_ref"]], on=KEYS, suffixes=("", "_rec"))
    nref_bad = m[m.n_ref != m.n_ref_rec]
    if len(nref_bad):
        bad.append(f"n_ref differs from the record in {len(nref_bad)} rows: "
                   f"{nref_bad[KEYS + ['system', 'n_ref', 'n_ref_rec']].head(5).to_dict('records')}")
    return dict(gate="A1", status="PASS" if not bad else "FAIL", bad=bad, rows={s: int((R.system == s).sum()) for s in SYSTEMS},
                n_ref_compared=int(len(m)))


def gate_self(P):
    """record - record must be exactly 0 in the bootstrap code path (sanity of the pairing)."""
    q = P[P.system == "record"]
    w = q.assign(system="record_copy")
    b = boot(pd.concat([q, w]).replace({"system": {"record_copy": "rerun"}}))
    b = b[b.step == "rerun - record"]
    ok = bool(len(b)) and bool((b[["diff", "ci_lo", "ci_hi"]].abs().max().max() == 0))
    return dict(gate="A1-self", status="PASS" if ok else "FAIL", rows=int(len(b)))


# ============================================================================ main
def md_table(df, cols, fmt=None):
    fmt = fmt or {}
    L = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        L.append("| " + " | ".join((fmt[c].format(r[c]) if c in fmt and pd.notna(r[c]) else ("" if pd.isna(r[c]) else str(r[c])))
                                   for c in cols) + " |")
    return L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", help="R1_RUN output folder (…/r2/r1_system/run)")
    ap.add_argument("--out")
    ap.add_argument("--a0-only", action="store_true")
    a = ap.parse_args()
    REC = record_rows()
    Srec = per_seed(REC)
    g0 = gate_a0(Srec)
    test_mode = bool(os.environ.get("R2_TEST"))
    log(f"A0 {g0['status']}{' (reported only: test mode, synthetic record)' if test_mode else ''}: {g0['bad']}")
    if g0["status"] != "PASS" and not test_mode:
        for c in g0["checks"]:
            log(c)
        raise SystemExit("STOP A0: the per-patient metric does not reproduce the locked numbers from the record files")
    if a.a0_only:
        for c in g0["checks"]:
            log(c)
        return
    run = Path(a.run)
    out = Path(a.out) if a.out else run / "aggregate"
    out.mkdir(parents=True, exist_ok=True)
    parts = [REC, run_rows(run, "run", "rerun")]
    errs = [record_errors(), run_errors(run, "run", "rerun")]
    for label in ("cf", "cf_krec"):
        if (run / "r13" / label / "per_subject.csv").exists():
            parts.append(run_rows(run, label, label)); errs.append(run_errors(run, label, label))
    R = pd.concat(parts, ignore_index=True)
    g1 = gate_a1(R, run)
    log(f"A1 {g1['status']}: {g1['bad']}")
    if g1["status"] != "PASS":
        raise SystemExit(f"STOP A1: {g1['bad']}")
    P = per_subject(R)
    gs = gate_self(P)
    log(f"A1-self {gs['status']}")
    if gs["status"] != "PASS":
        raise SystemExit("STOP A1-self: record - record is not 0 in the bootstrap path")
    # A2 rows vs record
    W = R.pivot_table(index=KEYS, columns="system", values=["tp", "fp", "nonict_h"]).reset_index()
    W.columns = ["_".join([c for c in col if c]) if isinstance(col, tuple) else col for col in W.columns]
    nref = R[R.system == "record"].set_index(KEYS).n_ref
    W["n_ref"] = [nref.get(tuple(r)) for r in W[KEYS].values]
    for sysm in ("rerun", "cf", "cf_krec"):
        if f"tp_{sysm}" in W:
            W[f"dtp_{sysm}"] = W[f"tp_{sysm}"] - W["tp_record"]
            W[f"dfp_{sysm}"] = W[f"fp_{sysm}"] - W["fp_record"]
    W.to_csv(out / "rows_vs_record.csv", index=False)
    # A3
    S = per_seed(R)
    S.to_csv(out / "summary_per_seed.csv", index=False)
    F = four_seed(S)
    F.to_csv(out / "summary.csv", index=False)
    # A4, A5
    P.to_csv(out / "per_subject.csv", index=False)
    Bt = boot(P)
    Bt.to_csv(out / "bootstrap.csv", index=False)
    kinfo = {"record": json.loads((REPO / "results" / "p3_levers" / "calibration.json").read_text())["k"]}
    for label in ("run", "cf"):
        kp = run / "r13" / label / "k.json"
        if kp.exists():
            kinfo[label] = json.loads(kp.read_text())["k"]
    At = attribution(F, P, kinfo)
    At.to_csv(out / "attribution.csv", index=False)
    # A6
    Et = errors_table(pd.concat(errs, ignore_index=True))
    Et.to_csv(out / "errors.csv", index=False)
    # A7
    rec_rows = W[W.tp_record.notna()]
    L = ["# R1 aggregate — the thesis system rerun on complete data vs the record (descriptive)\n",
         "Gates: " + ", ".join(f"{g['gate']} {g['status']}" for g in (g0, g1, gs)),
         f"\nk: " + ", ".join(f"{k} {v:.6f}" for k, v in kinfo.items()),
         f"\nRecord rows matched: {len(rec_rows)}; rows with tp different (rerun): "
         f"{int((rec_rows.dtp_rerun != 0).sum()) if 'dtp_rerun' in rec_rows else 'n/a'}, fp different: "
         f"{int((rec_rows.dfp_rerun != 0).sum()) if 'dfp_rerun' in rec_rows else 'n/a'}\n",
         "## Per-patient means (4 seeds; seed 42 in brackets), CPD stage, arms frozen and L2f\n"]
    sel = F[(F.stage == "cpd") & (F.arm.isin(["frozen", "L2f"]))].copy()
    sel["set"] = pd.Categorical(sel.set, SETS); sel["system"] = pd.Categorical(sel.system, SYSTEMS)
    sel = sel.sort_values(["set", "arm", "system"])
    L += md_table(sel, ["set", "arm", "system", "subjects", "sens", "sens_sd", "sens42", "fa", "fa_sd", "fa42", "f1", "prec"],
                  {c: "{:.3f}" for c in ("sens", "sens_sd", "sens42", "f1", "prec")} | {c: "{:.1f}" for c in ("fa", "fa_sd", "fa42")})
    L += ["\n## Paired subject bootstrap (B = 10,000), CPD stage, arms frozen and L2f\n"]
    bsel = Bt[(Bt.stage == "cpd") & (Bt.arm.isin(["frozen", "L2f"]))].copy()
    bsel["set"] = pd.Categorical(bsel.set, SETS)
    L += md_table(bsel.sort_values(["set", "arm", "step", "metric"]),
                  ["set", "arm", "step", "metric", "subjects", "diff", "ci_lo", "ci_hi", "subjects_changed"],
                  {c: "{:+.3f}" for c in ("diff", "ci_lo", "ci_hi")})
    L += ["\nAll arms and stages: `summary.csv`, `bootstrap.csv`, `attribution.csv`; per row: `rows_vs_record.csv`; per "
          "subject: `per_subject.csv`; boundaries: `errors.csv`. Descriptive only (plan P2); no row replaces a locked "
          "number of the thesis."]
    (out / "SUMMARY.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (out / "gates.json").write_text(json.dumps([g0, g1, gs], indent=1, default=str))
    log(f"written: {sorted(p.name for p in out.iterdir())}")


if __name__ == "__main__":
    main()
