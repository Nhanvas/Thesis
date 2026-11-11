#!/usr/bin/env python
"""
r2_rp_aggregate.py -- stage RP reading (RP1-RP3): the tables of the final report's main model (docs/FUTURE_RESEARCH_PLAN.md
§7b, §12 row 11/11 D20-F). Written, tested on synthetic data and committed BEFORE the RP_RUN output exists. Descriptive:
no pass/fail threshold on any result (plan P2).

Inputs: the RP_RUN output (results/r2/r1_system/rp: rp2/per_subject.csv, errors.csv, q.csv, k.json, demo_model.json,
gates.json, models/) and the R1_RUN output (results/r2/r1_system/run: r13/run, aggregate/summary_per_seed.csv, models/).
Report seeds = 1-4 ("4 seeds"); seed 42 is read only for gate A1 and the size of the k correction.

  A0 (STOP) the per-patient metric (e22_test_oneshot.metrics, SzCORE per-patient mean) on R1's r13/run rows reproduces
     R1's committed aggregate/summary_per_seed.csv (system "rerun"; relative 1e-12).
  A1 (STOP) RP_RUN gates all PASS (G-data, G-const-new, RP.0, G-vec, G-val, R1.1-training, RP2-complete, RP3-demo);
     rows complete (38 cases x 5 seeds x 4 arms x 3 stages); n_ref of every row = R1's for its subject and arm; seed 42
     rows = R1's (exact mode: tp, fp, top equal; tolerance mode: |dtp| <= 1, |dfp| <= 2); frozen-arm rows of seeds 1-3 =
     R1's (same rule); k of seed 42 = R1's k; demo_model.json = the RP3 rule recomputed from the model jsons.
  Tables (seeds 1-4; sets test, development, chb24, siena; arms frozen = held-out, L2f = final, L2, S; stages detector,
  cpd, hybrid; the frozen localizer is CPD):
     summary_per_seed.csv  per seed: tp, n_ref, fp, per-patient sensitivity, precision, F1, FP/day (5 seeds)
     summary.csv           4-seed mean +- SD (ddof 1) and a patient-bootstrap 95 % CI of the per-patient mean (B =
                           10,000, rng 0; unit = subject, chb01 + chb21 one unit; a subject's value = its 4-seed mean)
     per_subject.csv       per subject x seed: budget top-p, tp, n_ref, fp, FP/day; per_subject_mean.csv: 4-seed means
     final_vs_heldout.csv  paired bootstrap of L2f - frozen per set and stage (sensitivity, F1, FP/day)
     k.csv, correction.csv k and median development q_i per seed; seeds 1-3 at their own k vs R1's k (seed 42's), arms
                           L2, L2f, S: per-patient means of both and the paired bootstrap of the difference (3-seed means)
     errors.csv            onset / offset errors (s): pairs, median |error| and signed median, detector / CPD / hybrid,
                           seeds 1-4 pooled; errors_per_seed.csv per seed
     review.csv            review fraction = flagged time / recorded time, per seed and 4-seed mean +- SD
     demo.csv              validation loss per seed and the chosen seed
     SUMMARY.md            the main tables
  python src/r2_rp_aggregate.py --rp results/r2/r1_system/rp [--r1 results/r2/r1_system/run] [--out DIR]
  python src/r2_rp_aggregate.py --a0-only
"""
import argparse
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
import e22_test_oneshot as E22          # noqa: E402  (record, read only)

R1_TAGS = ["clean_seed42", "clean_seed1", "clean_seed2", "clean_seed3"]
TAGS = R1_TAGS + ["clean_seed4"]
REPORT = ["clean_seed1", "clean_seed2", "clean_seed3", "clean_seed4"]
OLD3 = ["clean_seed1", "clean_seed2", "clean_seed3"]
ARMS = ["frozen", "L2", "L2f", "S"]
ARM_NAME = {"frozen": "held-out (0.5 %)", "L2f": "final (per-patient budget)", "L2": "L2", "S": "S"}
STAGES = ["detector", "cpd", "hybrid"]
SETS = ["test", "development", "chb24", "siena"]
UNIT = {"chb21": "chb01+chb21", "chb01": "chb01+chb21"}
B, RNG_SEED, TIE_REL = 10_000, 0, 1e-9
GATES = ["G-data", "G-const-new", "RP.0", "G-vec", "G-val", "R1.1-training", "RP2-complete", "RP3-demo"]


def log(*a):
    print(*a, flush=True)


def load_rows(path):
    d = pd.read_csv(path).rename(columns={"budget": "arm"})
    d["set"] = np.where(d["set"] != "external", d["set"], np.where(d.subject == "chb24", "chb24", "siena"))
    return d


def per_seed(R):
    out = []
    for (st, arm, stage, seed), g in R.groupby(["set", "arm", "stage", "seed"]):
        m = E22.metrics(g.assign(short_tp=0, short_n=0))
        out.append(dict(set=st, arm=arm, stage=stage, seed=seed, subjects=int(g.subject.nunique()),
                        **{k: m[k] for k in ("tp", "n_ref", "fp", "s_sens", "s_prec", "s_f1", "s_fa")}))
    return pd.DataFrame(out)


def subj_metrics(R):
    return R.assign(sens=R.tp / R.n_ref, f1=2 * R.tp / (2 * R.tp + R.fp + (R.n_ref - R.tp)), fa=R.fp / R.nonict_h * 24,
                    prec=R.tp / (R.tp + R.fp).where(R.tp + R.fp > 0))


def boot_mean(vals, units, rng):
    """95 % bootstrap CI of the mean over subjects; resampling unit = units (chb01 + chb21 together)."""
    vals = np.asarray(vals, float)
    u = pd.Series(units).astype(str).values
    keys = np.unique(u)
    s = np.array([vals[u == k].sum() for k in keys])
    n = np.array([(u == k).sum() for k in keys])
    idx = rng.integers(0, len(keys), size=(B, len(keys)))
    bs = s[idx].sum(1) / n[idx].sum(1)
    return float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def units_of(subjects):
    return [UNIT.get(s, s) for s in subjects]


# ============================================================================ gates
def gate_a0(r1):
    R = load_rows(Path(r1) / "r13" / "run" / "per_subject.csv")
    S = per_seed(R)
    ref = pd.read_csv(Path(r1) / "aggregate" / "summary_per_seed.csv")
    ref = ref[ref.system == "rerun"].drop(columns="system")
    m = S.merge(ref, on=["set", "arm", "stage", "seed"], suffixes=("", "_ref"), how="outer", indicator=True)
    bad = int((m._merge != "both").sum())
    for c in ("tp", "n_ref", "fp", "s_sens", "s_prec", "s_f1", "s_fa"):
        a, b = m[c].astype(float).values, m[f"{c}_ref"].astype(float).values
        both_nan = np.isnan(a) & np.isnan(b)
        rel = np.abs(a - b) / np.maximum(np.abs(b), 1e-12)
        bad += int(((rel > 1e-12) & ~both_nan).sum())
    return dict(gate="A0", status="PASS" if bad == 0 else "FAIL", rows=int(len(m)), differ=bad)


def gate_a1(rp, r1, R, n_cases):
    bad = []
    gl = json.loads((Path(rp) / "gates.json").read_text())
    st = {g["gate"]: g["status"] for g in gl}
    for g in GATES:
        if st.get(g) != "PASS":
            bad.append(f"gate {g}: {st.get(g)}")
    mode = next((g.get("mode") for g in gl if g["gate"] == "RP.0"), None)
    want = sum(n_cases.values()) * len(TAGS) * len(ARMS) * len(STAGES)
    if len(R) != want:
        bad.append(f"{len(R)} rows, expected {want}")
    for s, n in n_cases.items():
        for tag in TAGS:
            got = R[(R.set == s) & (R.seed == tag)].subject.nunique()
            if got != n:
                bad.append(f"{s} {tag}: {got} subjects, expected {n}")
    R1r = load_rows(Path(r1) / "r13" / "run" / "per_subject.csv")
    keys = ["set", "subject", "seed", "arm", "stage"]
    m = R.merge(R1r, on=keys, suffixes=("", "_r1"), how="left")
    q = m[m.seed.isin(R1_TAGS)]
    if q.tp_r1.isna().any():
        bad.append("rows of R1 tags missing in R1")
    if (q.n_ref != q.n_ref_r1).any():
        bad.append("n_ref differs from R1")
    nref42 = R1r[R1r.seed == "clean_seed42"].set_index(["set", "subject", "arm", "stage"]).n_ref
    s4 = R[R.seed == "clean_seed4"]
    if not np.array_equal(s4.n_ref.values, [nref42[tuple(r)] for r in s4[["set", "subject", "arm", "stage"]].values]):
        bad.append("seed 4 n_ref differs from R1's")
    must = q[(q.seed == "clean_seed42") | (q.arm == "frozen")]
    if mode == "exact":
        d = must[(must.tp != must.tp_r1) | (must.fp != must.fp_r1) | ((must.top - must.top_r1).abs() > 1e-12)]
    else:
        d = must[((must.tp - must.tp_r1).abs() > 1) | ((must.fp - must.fp_r1).abs() > 2)]
    if len(d):
        bad.append(f"seed 42 / frozen rows differ from R1 ({mode}): {len(d)} rows, e.g. "
                   f"{d[keys + ['tp', 'tp_r1', 'fp', 'fp_r1']].head(3).to_dict('records')}")
    k = json.loads((Path(rp) / "rp2" / "k.json").read_text())
    k1 = json.loads((Path(r1) / "r13" / "run" / "k.json").read_text())["k"]
    krel = abs(k["k"]["clean_seed42"] - k1) / k1
    if krel > (1e-12 if mode == "exact" else 1e-6):
        bad.append(f"k of seed 42 {k['k']['clean_seed42']} vs R1 {k1}")
    demo = json.loads((Path(rp) / "demo_model.json").read_text())
    vals = {}
    for tag in REPORT:
        p = (Path(rp) / "models" if tag == "clean_seed4" else Path(r1) / "models") / f"gae_v2_{tag}.json"
        vals[int(tag.split("seed")[1])] = float(json.loads(p.read_text())["final_val"])
    lo = min(vals.values())
    pick = sorted(s for s, v in vals.items() if (v - lo) / abs(lo) <= TIE_REL)[0]
    if pick != demo["seed"] or abs(demo["k"] - k["k"][f"clean_seed{pick}"]) > 0:
        bad.append(f"demo_model.json seed {demo['seed']} / k {demo['k']} vs rule {pick}")
    return dict(gate="A1", status="PASS" if not bad else "FAIL", bad=bad, mode=mode, rows=int(len(R)),
                compared_with_r1=int(len(must)), validation_loss=vals, demo_seed=pick)


# ============================================================================ tables
def summary(R, S):
    rng = np.random.default_rng(RNG_SEED)
    out = []
    P = subj_metrics(R[R.seed.isin(REPORT)])
    Sm = S[S.seed.isin(REPORT)]
    for (st, arm, stage), g in Sm.groupby(["set", "arm", "stage"]):
        p = P[(P.set == st) & (P.arm == arm) & (P.stage == stage)].groupby("subject")[["sens", "f1", "fa", "prec"]].mean()
        r = dict(set=st, arm=arm, stage=stage, seeds=int(g.seed.nunique()), subjects=int(g.subjects.max()),
                 n_ref=int(g.n_ref.max()), tp_mean=float(g.tp.mean()), fp_mean=float(g.fp.mean()))
        for c, sc in (("sens", "s_sens"), ("prec", "s_prec"), ("f1", "s_f1"), ("fa", "s_fa")):
            r[c], r[f"{c}_sd"] = float(g[sc].mean()), float(g[sc].std(ddof=1))
        for c in ("sens", "f1", "fa"):
            r[f"{c}_ci_lo"], r[f"{c}_ci_hi"] = boot_mean(p[c].values, units_of(p.index), rng)
        out.append(r)
    return pd.DataFrame(out)


def paired(P, a_mask, b_mask, keys, label):
    """paired subject bootstrap of mean(a) - mean(b) over subjects (values = per-subject means)."""
    rng = np.random.default_rng(RNG_SEED)
    out = []
    for grp, g in P.groupby(keys):
        a = g[a_mask(g)].groupby("subject")[["sens", "f1", "fa"]].mean()
        b = g[b_mask(g)].groupby("subject")[["sens", "f1", "fa"]].mean()
        sub = a.index.intersection(b.index)
        if not len(sub):
            continue
        for met in ("sens", "f1", "fa"):
            d = (a.loc[sub, met] - b.loc[sub, met]).values
            lo, hi = boot_mean(d, units_of(sub), rng)
            out.append(dict(**dict(zip(keys, grp if isinstance(grp, tuple) else (grp,))), comparison=label, metric=met,
                            subjects=len(sub), a=float(a.loc[sub, met].mean()), b=float(b.loc[sub, met].mean()),
                            diff=float(d.mean()), ci_lo=lo, ci_hi=hi, subjects_changed=int((np.abs(d) > 0).sum())))
    return pd.DataFrame(out)


def errors_tables(E):
    E = E.rename(columns={"budget": "arm"})
    E["set"] = np.where(E["set"] != "external", E["set"], np.where(E.subject == "chb24", "chb24", "siena"))
    E = E[E.seed.isin(REPORT)]

    def one(g):
        r = dict(pairs=int(len(g)))
        for c in ("det_on", "det_off", "cpd_on", "cpd_off", "hyb_on", "hyb_off"):
            r[f"med_abs_{c}"] = float(g[c].abs().median())
            r[f"med_{c}"] = float(g[c].median())
        return pd.Series(r)
    pooled = E.groupby(["set", "arm"]).apply(one, include_groups=False).reset_index()
    seeds = E.groupby(["set", "arm", "seed"]).apply(one, include_groups=False).reset_index()
    return pooled, seeds


def review(R):
    g = R[R.seed.isin(REPORT)].groupby(["set", "arm", "stage", "seed"])[["review_s", "rec_s"]].sum().reset_index()
    g["review_fraction"] = g.review_s / g.rec_s
    s = g.groupby(["set", "arm", "stage"]).review_fraction.agg(["mean", "std"]).reset_index()
    return g, s.rename(columns={"mean": "review_mean", "std": "review_sd"})


def md_table(df, cols, fmt=None):
    fmt = fmt or {}
    L = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        L.append("| " + " | ".join((fmt[c].format(r[c]) if c in fmt and pd.notna(r[c]) else ("" if pd.isna(r[c]) else str(r[c])))
                                   for c in cols) + " |")
    return L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rp", help="RP_RUN output folder (results/r2/r1_system/rp)")
    ap.add_argument("--r1", default=str(REPO / "results" / "r2" / "r1_system" / "run"))
    ap.add_argument("--out")
    ap.add_argument("--a0-only", action="store_true")
    a = ap.parse_args()
    g0 = gate_a0(a.r1)
    log(f"A0 {g0['status']} ({g0['rows']} rows, {g0['differ']} differ)")
    if g0["status"] != "PASS":
        raise SystemExit("STOP A0: the per-patient metric does not reproduce R1's summary_per_seed.csv")
    if a.a0_only:
        return
    rp = Path(a.rp)
    out = Path(a.out) if a.out else rp / "aggregate"
    out.mkdir(parents=True, exist_ok=True)
    n_cases = {"development": 15, "test": 8, "chb24": 1, "siena": 14}
    if os.environ.get("R2_TEST") and os.environ.get("R2_TEST_N_CASES"):          # synthetic world only
        n_cases = json.loads(os.environ["R2_TEST_N_CASES"])
    R = load_rows(rp / "rp2" / "per_subject.csv")
    g1 = gate_a1(rp, a.r1, R, n_cases)
    log(f"A1 {g1['status']}: {g1['bad']}")
    if g1["status"] != "PASS":
        raise SystemExit(f"STOP A1: {g1['bad']}")
    S = per_seed(R)
    S.to_csv(out / "summary_per_seed.csv", index=False)
    F = summary(R, S)
    F.to_csv(out / "summary.csv", index=False)
    P = subj_metrics(R)
    keep = ["set", "subject", "seed", "arm", "stage", "top", "tp", "n_ref", "fp", "nonict_h", "sens", "fa", "f1"]
    P[P.seed.isin(REPORT)][keep].to_csv(out / "per_subject.csv", index=False)
    P[P.seed.isin(REPORT)].groupby(["set", "arm", "stage", "subject"])[["top", "tp", "n_ref", "fp", "sens", "fa", "f1"]] \
        .mean().reset_index().to_csv(out / "per_subject_mean.csv", index=False)
    PR = P[P.seed.isin(REPORT) & P.arm.isin(["frozen", "L2f"])]
    FH = paired(PR, lambda g: g.arm == "L2f", lambda g: g.arm == "frozen", ["set", "stage"], "final - held-out")
    FH.to_csv(out / "final_vs_heldout.csv", index=False)
    # k correction: seeds 1-3 at their own k vs at R1's k (seed 42's)
    k = json.loads((rp / "rp2" / "k.json").read_text())
    R1r = subj_metrics(load_rows(Path(a.r1) / "r13" / "run" / "per_subject.csv"))
    q_rp = pd.read_csv(rp / "rp2" / "q.csv")
    q_r1 = pd.read_csv(Path(a.r1) / "r13" / "run" / "q.csv")
    K = pd.DataFrame([dict(seed=t, k=k["k"][t], k_r1=k["k_r1"],
                           median_dev_q_own_k=float(q_rp[(q_rp.set == "development") & (q_rp.seed == t)].q_raw.median()),
                           median_dev_q_r1_k=float(q_r1[(q_r1.set == "development") & (q_r1.seed == t)].q_raw.median())
                           if t in R1_TAGS else np.nan) for t in TAGS])
    K.to_csv(out / "k.csv", index=False)
    both = pd.concat([P[P.seed.isin(OLD3) & P.arm.isin(["L2", "L2f", "S"])].assign(system="own k"),
                      R1r[R1r.seed.isin(OLD3) & R1r.arm.isin(["L2", "L2f", "S"])].assign(system="R1 k")])
    C = paired(both, lambda g: g.system == "own k", lambda g: g.system == "R1 k", ["set", "arm", "stage"],
               "seeds 1-3: own k - R1 k")
    C.to_csv(out / "correction.csv", index=False)
    Ep, Es = errors_tables(pd.read_csv(rp / "rp2" / "errors.csv"))
    Ep.to_csv(out / "errors.csv", index=False)
    Es.to_csv(out / "errors_per_seed.csv", index=False)
    rv_seed, rv = review(R)
    rv_seed.to_csv(out / "review_per_seed.csv", index=False)
    rv.to_csv(out / "review.csv", index=False)
    demo = json.loads((rp / "demo_model.json").read_text())
    pd.DataFrame([dict(seed=s, validation_loss=v, chosen=s == demo["seed"]) for s, v in g1["validation_loss"].items()]) \
        .to_csv(out / "demo.csv", index=False)
    (out / "gates.json").write_text(json.dumps([g0, g1], indent=1, default=str))
    # SUMMARY.md
    sel = F[(F.stage == "cpd") & F.arm.isin(["frozen", "L2f"])].copy()
    sel["set"] = pd.Categorical(sel.set, SETS)
    sel = sel.sort_values(["set", "arm"])
    sel["arm"] = sel.arm.map(ARM_NAME)
    f3 = {c: "{:.3f}" for c in ("sens", "sens_sd", "sens_ci_lo", "sens_ci_hi", "prec", "f1", "f1_sd", "f1_ci_lo", "f1_ci_hi")}
    f1_ = {c: "{:.1f}" for c in ("fa", "fa_sd", "fa_ci_lo", "fa_ci_hi", "tp_mean", "fp_mean")}
    L = ["# RP aggregate — main model of the final report (seeds 1-4, k per seed); descriptive\n",
         f"Gates: A0 {g0['status']}, A1 {g1['status']} (RP_RUN mode {g1['mode']}). Demo model: seed {demo['seed']} "
         f"(validation loss {json.dumps(g1['validation_loss'])}).\n",
         "## Per-patient means, CPD stage: 4-seed mean ± SD, patient bootstrap 95 % CI\n"]
    L += md_table(sel, ["set", "arm", "subjects", "n_ref", "tp_mean", "fp_mean", "sens", "sens_sd", "sens_ci_lo", "sens_ci_hi",
                        "prec", "f1", "f1_sd", "fa", "fa_sd", "fa_ci_lo", "fa_ci_hi"], f3 | f1_)
    L += ["\n## Per seed (CPD stage)\n"]
    ps = S[(S.stage == "cpd") & S.arm.isin(["frozen", "L2f"])].copy()
    ps["set"] = pd.Categorical(ps.set, SETS)
    L += md_table(ps.sort_values(["set", "arm", "seed"]), ["set", "arm", "seed", "tp", "n_ref", "fp", "s_sens", "s_f1", "s_fa"],
                  {"s_sens": "{:.3f}", "s_f1": "{:.3f}", "s_fa": "{:.1f}"})
    L += ["\n## Final − held-out (paired, CPD stage)\n"]
    L += md_table(FH[FH.stage == "cpd"], ["set", "metric", "subjects", "a", "b", "diff", "ci_lo", "ci_hi"],
                  {c: "{:+.3f}" for c in ("diff", "ci_lo", "ci_hi")} | {"a": "{:.3f}", "b": "{:.3f}"})
    L += ["\n## k per seed; correction (seeds 1-3, own k − R1 k), arm final, CPD stage\n"]
    L += md_table(K, ["seed", "k", "k_r1", "median_dev_q_own_k", "median_dev_q_r1_k"],
                  {"k": "{:.4f}", "k_r1": "{:.4f}", "median_dev_q_own_k": "{:.4f}", "median_dev_q_r1_k": "{:.4f}"})
    L += [""] + md_table(C[(C.arm == "L2f") & (C.stage == "cpd")], ["set", "metric", "subjects", "a", "b", "diff", "ci_lo", "ci_hi"],
                         {c: "{:+.3f}" for c in ("diff", "ci_lo", "ci_hi")} | {"a": "{:.3f}", "b": "{:.3f}"})
    L += ["\n## Onset / offset errors (s), seeds 1-4 pooled, median |error|\n"]
    L += md_table(Ep[Ep.arm.isin(["frozen", "L2f"])], ["set", "arm", "pairs", "med_abs_cpd_on", "med_abs_cpd_off",
                                                        "med_abs_hyb_on", "med_abs_hyb_off", "med_cpd_off", "med_hyb_off"])
    L += ["\nAll arms and stages: `summary.csv`, `summary_per_seed.csv`; per subject: `per_subject*.csv`; review load: "
          "`review.csv`. Descriptive only (plan P2)."]
    (out / "SUMMARY.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    log(f"written: {sorted(p.name for p in out.iterdir())}")


if __name__ == "__main__":
    main()
