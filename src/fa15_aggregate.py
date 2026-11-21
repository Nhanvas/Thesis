#!/usr/bin/env python
"""
fa15_aggregate.py -- F-A1.5 / PC5 reading: ASR in the preprocessing vs the control (chat D35-F; design
results/fa15/DESIGN_D35F.md §7, approved by the author 21/11 19:13; written, tested on synthetic data and committed BEFORE
the training notebooks run). Descriptive: no pass / fail threshold on any result (plan P2); every set reported.

Inputs: the control record (results/r2/r1_system/rp: rp2/per_subject.csv, errors.csv, k.json, aggregate/
summary_per_seed.csv; seeds 42, 1, 2, 3, 4), the control's new seeds (results/fa15/fa15_ctrl: run/..., seeds 5, 6, 7) and
the ASR arm (results/fa15/fa15_asr_a, fa15_asr_b: run/..., seeds 42, 1, ..., 7).

Gates (STOP):
  A0  the per-seed per-patient means of this script (sensitivity, precision, F1, FP/day; e22_test_oneshot.metrics's
      definitions) on the control record's rp2 rows = results/r2/r1_system/rp/aggregate/summary_per_seed.csv (relative
      1e-12) -> the metric code is the record's
  A1  every gate of the three runs PASS (G-mod, G-data, G-repro, G-vec, R1.1-training, RUN-complete, G-worker-sha; the
      ctrl run G-const-new; the asr runs G-asr-data, G-asr-counts)
  A2  rows complete: each arm holds exactly its expected seeds x every case x 4 budget arms x 3 stages, no seed twice;
      n_ref of every row = the control's for its subject (same annotations)
Readings (per-patient means over the patients of a set; stage cpd = after the change point localizer, as V5):
  T1  per set (development, test, chb24, siena) x evaluation (held-out = budget 0.5 %, final = per-patient budget):
      control and ASR mean +- SD over seeds of the per-patient mean (sensitivity, F1, FP/day, precision); ASR - control
      with a two-level bootstrap (patients resampled as units, chb01 + chb21 one unit; seeds resampled within each arm;
      B = 10,000, rng 0; the method of eur_pc7_read.py Q5, re-implemented here); chb24 (one patient): seeds only
  T2  per seed: the per-patient means (sets x evaluations), k per seed, validation loss (from the model jsons)
  T3  per patient: 8-seed means of both arms and their difference (final, cpd)
  T4  onset / offset: median |error| (s) of detected events, pairs pooled over seeds, detector / CPD / hybrid, per arm
  T5  data: clean training / validation windows of both arms (the ASR flag is recomputed on the cleaned signal)
Outputs (--out, default results/fa15/reading): t1.csv, t2_seeds.csv, t3_patients.csv, t4_boundaries.csv, t5_data.csv,
gates.json, T_PC5.md.
  python src/fa15_aggregate.py [--rp DIR] [--ctrl DIR] [--asr DIR DIR] [--out DIR]
"""
import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(os.environ.get("THESIS_REPO", Path(__file__).resolve().parents[1]))
SEEDS_CTRL = [42, 1, 2, 3, 4, 5, 6, 7]
SEEDS_ASR = [42, 1, 2, 3, 4, 5, 6, 7]
SETS = ["development", "test", "chb24", "siena"]
EVALS = {"held-out": "frozen", "final": "L2f"}
ARMS4 = ["frozen", "L2", "L2f", "S"]
STAGES = ["detector", "cpd", "hybrid"]
METRICS = ("sens", "f1", "fa", "prec")
UNIT = {"chb21": "chb01"}
B, RNG = 10_000, 0
RUN_GATES = ["G-mod", "G-data", "G-repro", "G-vec", "R1.1-training", "RUN-complete", "G-worker-sha"]
EXTRA_GATES = {"ctrl": ["G-const-new"], "asr": ["G-asr-data", "G-asr-counts"]}


def log(*a):
    print(*a, flush=True)


def stop(msg):
    raise SystemExit(f"STOP {msg}")


def load_rows(path, arm):
    d = pd.read_csv(path)
    d["set"] = np.where(d["set"] != "external", d["set"], np.where(d.subject == "chb24", "chb24", "siena"))
    d["seed_n"] = d.seed.str.replace("clean_seed", "").astype(int)
    d["arm_name"] = arm
    return d


def subj_metrics(R):
    return R.assign(sens=R.tp / R.n_ref, f1=2 * R.tp / (2 * R.tp + R.fp + (R.n_ref - R.tp)), fa=R.fp / R.nonict_h * 24,
                    prec=R.tp / (R.tp + R.fp).where(R.tp + R.fp > 0))


def per_seed(R):
    M = subj_metrics(R)
    g = M.groupby(["set", "budget", "stage", "seed"])
    return g.agg(subjects=("subject", "nunique"), tp=("tp", "sum"), n_ref=("n_ref", "sum"), fp=("fp", "sum"),
                 s_sens=("sens", "mean"), s_prec=("prec", "mean"), s_f1=("f1", "mean"), s_fa=("fa", "mean")).reset_index()


# ============================================================================ gates
def gate_a0(rp):
    R = load_rows(Path(rp) / "rp2" / "per_subject.csv", "control")
    S = per_seed(R).rename(columns={"budget": "arm"})
    ref = pd.read_csv(Path(rp) / "aggregate" / "summary_per_seed.csv")
    m = S.merge(ref, on=["set", "arm", "stage", "seed"], suffixes=("", "_ref"), how="inner")
    bad = 0
    for c in ("tp", "n_ref", "fp", "s_sens", "s_prec", "s_f1", "s_fa"):
        a, b = m[c].astype(float).values, m[f"{c}_ref"].astype(float).values
        both = np.isnan(a) & np.isnan(b)
        bad += int(((np.abs(a - b) / np.maximum(np.abs(b), 1e-12) > 1e-12) & ~both).sum())
    ok = bad == 0 and len(m) == len(ref) and len(m) > 0
    return dict(gate="A0", status="PASS" if ok else "FAIL", rows=int(len(m)), ref_rows=int(len(ref)), differ=bad,
                summary=f"{len(m)} of {len(ref)} per-seed rows of the record reproduced; {bad} values differ")


def gate_a1(runs):
    bad = {}
    for kind, d in runs:
        gl = {g["gate"]: g["status"] for g in json.loads((Path(d) / "gates.json").read_text())}
        need = RUN_GATES + EXTRA_GATES["ctrl" if kind == "ctrl" else "asr"]
        miss = {g: gl.get(g) for g in need if gl.get(g) != "PASS"}
        if miss:
            bad[str(d)] = miss
    return dict(gate="A1", status="PASS" if not bad else "FAIL", runs=[str(d) for _, d in runs], bad=bad,
                summary=f"{len(runs)} runs; gates not PASS: {bad}")


def gate_a2(C, A, ncases, seeds_c, seeds_a):
    bad = []
    for name, D, want in (("control", C, seeds_c), ("asr", A, seeds_a)):
        got = sorted(D.seed_n.unique())
        if sorted(want) != got:
            bad.append(f"{name}: seeds {got} != {sorted(want)}")
        n = len(D)
        exp = ncases * len(want) * len(ARMS4) * len(STAGES)
        if n != exp:
            bad.append(f"{name}: {n} rows != {exp}")
        if D.duplicated(["set", "subject", "seed", "budget", "stage"]).any():
            bad.append(f"{name}: duplicated rows")
    nref = C.groupby("subject").n_ref.agg(["min", "max"])
    if (nref["min"] != nref["max"]).any():
        bad.append("control n_ref not constant per subject")
    m = A.merge(nref, left_on="subject", right_index=True, how="left")
    if (m.n_ref != m["min"]).any():
        bad.append("asr n_ref != control n_ref")
    return dict(gate="A2", status="PASS" if not bad else "FAIL", bad=bad, cases=ncases,
                summary=f"{ncases} cases; control seeds {sorted(C.seed_n.unique())}, asr seeds {sorted(A.seed_n.unique())}; "
                        f"problems {bad}")


# ============================================================================ bootstrap
def unit_draw(subjects, rng):
    units = pd.Series([UNIT.get(x, x) for x in subjects])
    uids = list(dict.fromkeys(units))
    uix = np.array([uids.index(u) for u in units])
    return uix, rng.integers(0, len(uids), size=(B, len(uids))), len(uids)


def unit_mean(d, uix, draws, U):
    sums = np.bincount(uix, weights=d, minlength=U)
    ns = np.bincount(uix, minlength=U).astype(float)
    return sums[draws].sum(axis=-1) / ns[draws].sum(axis=-1)


def matrix(M, st, budget, met, seeds):
    g = M[(M.set == st) & (M.budget == budget) & (M.stage == "cpd") & (M.seed_n.isin(seeds))]
    g = g.pivot(index="subject", columns="seed_n", values=met)
    return g[[s for s in seeds if s in g.columns]]


def diff_boot(Am, Cm, rng):
    """ASR - control: per-patient means over seeds; two-level bootstrap (patients as units; seeds within each arm).
    NaN cells (precision without any event) are skipped in the per-patient seed mean."""
    subj = [s for s in Am.index if s in Cm.index]
    Av, Cv = Am.loc[subj].values, Cm.loc[subj].values
    a_m, c_m = np.nanmean(Av, axis=1), np.nanmean(Cv, axis=1)
    keep = np.isfinite(a_m) & np.isfinite(c_m)
    subj = [s for s, k in zip(subj, keep) if k]
    Av, Cv = Av[keep], Cv[keep]
    diff = float(np.mean(np.nanmean(Av, axis=1) - np.nanmean(Cv, axis=1))) if len(subj) else np.nan
    bs = np.empty(B)
    if len(subj) >= 2:
        uix, draws, U = unit_draw(subj, rng)
        for b in range(B):
            sa = rng.integers(0, Av.shape[1], Av.shape[1])
            sc = rng.integers(0, Cv.shape[1], Cv.shape[1])
            with np.errstate(invalid="ignore"):
                d = np.nanmean(Av[:, sa], axis=1) - np.nanmean(Cv[:, sc], axis=1)
            d = np.where(np.isfinite(d), d, 0.0)
            bs[b] = unit_mean(d, uix, draws[b], U)
        kind = "patients x seeds"
    elif len(subj) == 1:
        for b in range(B):
            sa = rng.integers(0, Av.shape[1], Av.shape[1])
            sc = rng.integers(0, Cv.shape[1], Cv.shape[1])
            bs[b] = np.nanmean(Av[0, sa]) - np.nanmean(Cv[0, sc])
        kind = "seeds only (one patient)"
    else:
        return diff, np.nan, np.nan, 0, "none"
    return diff, float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5)), len(subj), kind


def seed_summary(M, st, budget, met, seeds):
    m = matrix(M, st, budget, met, seeds)
    v = m.mean(axis=0, skipna=True)
    return float(v.mean()), float(v.std(ddof=1)) if len(v) > 1 else np.nan, int(len(v))


# ============================================================================ main
def model_json(run_dir, tag):
    for d in ([Path(run_dir) / "models"] if run_dir else []):
        p = d / f"gae_v2_{tag}.json"
        if p.exists():
            return json.loads(p.read_text())
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rp", default=str(REPO / "results" / "r2" / "r1_system" / "rp"))
    ap.add_argument("--r1", default=str(REPO / "results" / "r2" / "r1_system" / "run"))
    ap.add_argument("--ctrl", default=str(REPO / "results" / "fa15" / "fa15_ctrl"))
    ap.add_argument("--asr", nargs="+", default=[str(REPO / "results" / "fa15" / "fa15_asr_a"),
                                                  str(REPO / "results" / "fa15" / "fa15_asr_b")])
    ap.add_argument("--out", default=str(REPO / "results" / "fa15" / "reading"))
    ap.add_argument("--seeds-ctrl", default=",".join(map(str, SEEDS_CTRL)))
    ap.add_argument("--seeds-asr", default=",".join(map(str, SEEDS_ASR)))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    seeds_c = [int(x) for x in a.seeds_ctrl.split(",")]
    seeds_a = [int(x) for x in a.seeds_asr.split(",")]
    gates = []

    def gate(g):
        gates.append(g)
        (out / "gates.json").write_text(json.dumps(gates, indent=1, default=str))
        log(f"{g['gate']}: {g['status']} -- {g.get('summary', '')}")
        if g["status"] != "PASS":
            stop(f"{g['gate']}: {g.get('summary')}")

    gate(gate_a0(a.rp))
    gate(gate_a1([("ctrl", a.ctrl)] + [("asr", d) for d in a.asr]))
    C = pd.concat([load_rows(Path(a.rp) / "rp2" / "per_subject.csv", "control"),
                   load_rows(Path(a.ctrl) / "run" / "per_subject.csv", "control")], ignore_index=True)
    A = pd.concat([load_rows(Path(d) / "run" / "per_subject.csv", "asr") for d in a.asr], ignore_index=True)
    ncases = int(C.subject.nunique())
    gate(gate_a2(C, A, ncases, seeds_c, seeds_a))
    MC, MA = subj_metrics(C), subj_metrics(A)
    rng = np.random.default_rng(RNG)

    # T1
    t1 = []
    for st in SETS:
        for ev, budget in EVALS.items():
            for met in METRICS:
                cm, csd, cn = seed_summary(MC, st, budget, met, seeds_c)
                am, asd, an = seed_summary(MA, st, budget, met, seeds_a)
                d, lo, hi, ns, kind = diff_boot(matrix(MA, st, budget, met, seeds_a), matrix(MC, st, budget, met, seeds_c),
                                                rng)
                t1.append(dict(set=st, evaluation=ev, metric=met, control_mean=cm, control_sd=csd, control_seeds=cn,
                               asr_mean=am, asr_sd=asd, asr_seeds=an, diff=d, ci_lo=lo, ci_hi=hi, patients=ns,
                               bootstrap=kind))
    T1 = pd.DataFrame(t1)
    T1.to_csv(out / "t1.csv", index=False)

    # T2
    t2 = []
    kc = {**json.loads((Path(a.rp) / "rp2" / "k.json").read_text())["k"],
          **json.loads((Path(a.ctrl) / "run" / "k.json").read_text())["k"]}
    ka = {}
    for d in a.asr:
        ka.update(json.loads((Path(d) / "run" / "k.json").read_text())["k"])
    for name, M, seeds, kk, dirs in (("control", MC, seeds_c, kc, [a.rp, a.r1, a.ctrl]), ("asr", MA, seeds_a, ka, a.asr)):
        for s in seeds:
            tag = f"clean_seed{s}"
            mj = next((m for m in (model_json(d, tag) for d in dirs) if m), None)
            row = dict(arm=name, seed=s, k=kk.get(tag), final_val=mj.get("final_val") if mj else np.nan,
                       n_train=sum(mj["n_train"].values()) if mj else np.nan)
            for st in SETS:
                for ev, budget in EVALS.items():
                    g = M[(M.set == st) & (M.budget == budget) & (M.stage == "cpd") & (M.seed_n == s)]
                    row[f"{st}_{ev}_sens"] = float(g.sens.mean())
                    row[f"{st}_{ev}_fa"] = float(g.fa.mean())
            t2.append(row)
    pd.DataFrame(t2).to_csv(out / "t2_seeds.csv", index=False)

    # T3
    t3 = []
    for st in SETS:
        for met in ("sens", "fa", "f1"):
            am = matrix(MA, st, "L2f", met, seeds_a).mean(axis=1)
            cm = matrix(MC, st, "L2f", met, seeds_c).mean(axis=1)
            for s in am.index:
                t3.append(dict(set=st, subject=s, metric=met, control=float(cm.get(s, np.nan)), asr=float(am[s]),
                               diff=float(am[s] - cm.get(s, np.nan))))
    pd.DataFrame(t3).to_csv(out / "t3_patients.csv", index=False)

    # T4
    EC = pd.concat([pd.read_csv(Path(a.rp) / "rp2" / "errors.csv"), pd.read_csv(Path(a.ctrl) / "run" / "errors.csv")])
    EA = pd.concat([pd.read_csv(Path(d) / "run" / "errors.csv") for d in a.asr])
    t4 = []
    for name, E, seeds in (("control", EC, seeds_c), ("asr", EA, seeds_a)):
        E = E.copy()
        E["set"] = np.where(E["set"] != "external", E["set"], np.where(E.subject == "chb24", "chb24", "siena"))
        E = E[E.seed.isin([f"clean_seed{s}" for s in seeds]) & (E.budget == "L2f")]
        for st in SETS:
            g = E[E.set == st]
            row = dict(arm=name, set=st, pairs=int(len(g)))
            for c in ("det_on", "det_off", "cpd_on", "cpd_off", "hyb_on", "hyb_off"):
                row[f"med_abs_{c}"] = float(g[c].abs().median()) if len(g) else np.nan
            t4.append(row)
    pd.DataFrame(t4).to_csv(out / "t4_boundaries.csv", index=False)

    # T5
    t5 = []
    for d in a.asr:
        g = {x["gate"]: x for x in json.loads((Path(d) / "gates.json").read_text())}
        c = g.get("G-asr-counts", {})
        t5.append(dict(run=Path(d).name, n_train_asr=c.get("n_train"), n_train_r0=c.get("n_train_r0"),
                       val_asr=sum((c.get("val") or {}).values()), val_r0=sum((c.get("val_r0") or {}).values())))
    T5 = pd.DataFrame(t5)
    T5.to_csv(out / "t5_data.csv", index=False)

    # report
    def f(x, n=3):
        return "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:.{n}f}"
    L = ["# PC5 / F-A1.5 — ASR in the preprocessing vs the control (reading; fa15_aggregate.py)", "",
         "Per-patient means after the change point localizer; mean ± SD over seeds; ASR − control with a two-level "
         "bootstrap (patients as units, seeds within each arm; B = 10,000). Descriptive: no threshold (plan P2). "
         f"Control seeds {seeds_c}, ASR seeds {seeds_a}.", "",
         "| set | evaluation | metric | control | ASR | ASR − control [95 % CI] | patients | bootstrap |",
         "|---|---|---|---|---|---|---|---|"]
    for r in T1.itertuples():
        nd = 1 if r.metric == "fa" else 3
        L.append(f"| {r.set} | {r.evaluation} | {r.metric} | {f(r.control_mean, nd)} ± {f(r.control_sd, nd)} | "
                 f"{f(r.asr_mean, nd)} ± {f(r.asr_sd, nd)} | {f(r.diff, nd)} [{f(r.ci_lo, nd)}, {f(r.ci_hi, nd)}] | "
                 f"{r.patients} | {r.bootstrap} |")
    L += ["", "Training data (clean windows of the 12 training patients): " +
          "; ".join(f"{r.run}: ASR {r.n_train_asr} vs R0 {r.n_train_r0}" for r in T5.itertuples()), "",
          "Gates: " + ", ".join(f"{g['gate']} {g['status']}" for g in gates) + ".", "",
          "Files: t1.csv (this table), t2_seeds.csv, t3_patients.csv, t4_boundaries.csv, t5_data.csv."]
    (out / "T_PC5.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    log("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
