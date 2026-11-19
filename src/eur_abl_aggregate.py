#!/usr/bin/env python
"""
eur_abl_aggregate.py -- tables of the Euréka ablation suite (src/eur_abl.py; design results/eureka_d31f/STEP1_DESIGN.md
§2.3). Written and committed before EUR_ABL produced any output.

Gates (STOP):
  A0  the per-patient metric used here (e22_test_oneshot.metrics, SzCORE's aggregate) reproduces the locked V5 numbers
      from the record files (r2_r1_aggregate.LOCKED, unchanged)
  A1  the run is complete: every gate of gates.json PASS (smoke and full); every (set, subject, seed, variant, arm,
      stage) row present except the variants listed as not available (3g on the external sets)
Readings (no threshold; design §2.3):
  primary    development, each variant's own operating point, after the localizer (stage cpd): per-patient mean
             sensitivity, F1, FP/day (4-seed mean +- SD) and the paired patient bootstrap of variant - V0 (B = 10,000,
             rng 0; seeds averaged within a patient first; chb01 + chb21 one resampling unit)
  secondary  (i) the fixed 0.5 % budget (arm fixed); (ii) sensitivity at matched FP/day 20 and 28.7 on the global-budget
             curve (detector stage, linear interpolation between grid points)
  descriptive test, chb24, Siena: the same columns (bootstrap intervals labelled descriptive); onset / offset errors
  special    6a = V0 fixed - V0 own; 7a = V0 detector stage vs cpd; 7b = V0 hybrid stage vs cpd
  R214       a variant is a replacement candidate only if, on development, the 95 % interval of its F1 difference is
             above 0 and its point sensitivity difference is >= 0 (printed; the author decides)
Outputs (--out, default <run>/aggregate): summary.csv, bootstrap.csv, errors_table.csv, matched.csv, candidates.csv,
T2.md, gates.json.
  python src/eur_abl_aggregate.py --run results/eureka_d31f/abl
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
import e22_test_oneshot as E22          # noqa: E402
import r2_r1_aggregate as AG            # noqa: E402  (record_rows, per_seed, gate_a0: unchanged)

TAGS = AG.TAGS
SETS = ["development", "test", "chb24", "siena"]
STAGES = ["detector", "cpd", "hybrid"]
B, RNG_SEED = 10_000, 0
FA_TARGETS = (20.0, 28.7)
UNIT = {"chb21": "chb01"}                   # chb21 = chb01 recorded 1.5 years later: one resampling unit


def log(*a):
    print(*a, flush=True)


def load_run(run):
    run = Path(run)
    R = pd.read_csv(run / "per_subject.csv").rename(columns={"budget": "arm"})
    E = pd.read_csv(run / "errors.csv").rename(columns={"budget": "arm"})
    C = pd.read_csv(run / "curve.csv")
    for d in (R, E, C):
        d["set"] = np.where(d["set"] != "external", d["set"], np.where(d.subject == "chb24", "chb24", "siena"))
    return R, E, C, json.loads((run / "gates.json").read_text()), pd.read_csv(run / "k.csv")


def gate_a1(R, gates, na):
    bad = [g["gate"] for g in gates if g.get("status") != "PASS"]
    names = {g["gate"] for g in gates}
    for need in ("G-data", "SMOKE", "R1.0-dev", "R1.0-test", "G-k", "G-kv0", "G-D0[full]", "G-x0[full]", "G-eng[full]",
                 "G-worker[full]", "G-self"):
        if need not in names:
            bad.append(f"missing {need}")
    var = sorted(R.variant.unique())
    cnt = R.groupby(["set", "subject", "variant"]).size()
    want = len(TAGS) * 2 * len(STAGES)
    short = [f"{i}" for i, v in cnt.items() if v != want]
    subj = R.groupby(["set"]).subject.nunique().to_dict()
    for (st, s), g in R.groupby(["set", "subject"]):
        miss = sorted(set(var) - set(g.variant) - set(na.get(s, [])))
        if miss:
            short.append(f"{s}: {miss}")
    return dict(gate="A1", status="PASS" if not bad and not short else "FAIL", bad_gates=bad, incomplete=short[:30],
                variants=var, subjects=subj)


def per_seed(R):
    X = R.rename(columns={"variant": "system"})
    return AG.per_seed(X[["set", "subject", "seed", "arm", "stage", "system", "tp", "fp", "n_ref", "nonict_h"]])


def per_subject(R):
    d = R.copy()
    d["sens"] = d.tp / d.n_ref.where(d.n_ref > 0)
    d["f1"] = 2 * d.tp / (2 * d.tp + d.fp + (d.n_ref - d.tp))
    d["fa"] = d.fp / d.nonict_h * 24
    return d.groupby(["set", "variant", "arm", "stage", "subject"])[["sens", "f1", "fa"]].mean().reset_index()


def boot_pair(a, b, rng):
    """a, b: Series by subject (4-seed means); paired difference, units resampled (chb01 + chb21 together)."""
    s = a.index.intersection(b.index)
    d = (a[s] - b[s]).dropna()
    if len(d) < 2:
        return dict(diff=float(d.mean()) if len(d) else np.nan, ci_lo=np.nan, ci_hi=np.nan, subjects=int(len(d)))
    units = pd.Series([UNIT.get(x, x) for x in d.index], index=d.index)
    uids = units.unique()
    groups = [d[units == u].values for u in uids]
    idx = rng.integers(0, len(uids), size=(B, len(uids)))
    sums = np.array([g.sum() for g in groups]); ns = np.array([len(g) for g in groups])
    bs = sums[idx].sum(axis=1) / ns[idx].sum(axis=1)
    return dict(diff=float(d.mean()), ci_lo=float(np.percentile(bs, 2.5)), ci_hi=float(np.percentile(bs, 97.5)),
                subjects=int(len(d)))


def bootstrap(P):
    rng = np.random.default_rng(RNG_SEED)
    out = []
    comps = [(v, "own", "cpd", "V0", "own", "cpd", f"{v} - V0") for v in sorted(P.variant.unique()) if v != "V0"]
    comps += [(v, "fixed", "cpd", "V0", "fixed", "cpd", f"{v} - V0 (fixed 0.5 %)") for v in sorted(P.variant.unique())
              if v != "V0"]
    comps += [("V0", "fixed", "cpd", "V0", "own", "cpd", "6a: fixed 0.5 % - per-patient budget"),
              ("V0", "own", "detector", "V0", "own", "cpd", "7a: detector boundaries - localizer"),
              ("V0", "own", "hybrid", "V0", "own", "cpd", "7b: hybrid - localizer")]
    for st in SETS:
        g = P[P.set == st]
        for va, aa, sa, vb, ab, sb, name in comps:
            A = g[(g.variant == va) & (g.arm == aa) & (g.stage == sa)].set_index("subject")
            Bb = g[(g.variant == vb) & (g.arm == ab) & (g.stage == sb)].set_index("subject")
            if not len(A) or not len(Bb):
                continue
            for met in ("sens", "f1", "fa"):
                r = boot_pair(A[met], Bb[met], rng)
                out.append(dict(set=st, comparison=name, variant=va, arm=aa, stage=sa, metric=met,
                                reading="primary" if st == "development" else "descriptive", **r))
    return pd.DataFrame(out)


def errors_table(E):
    rows = []
    for (st, v, arm), g in E.groupby(["set", "variant", "arm"]):
        r = dict(set=st, variant=v, arm=arm, pairs=int(len(g)))
        for c in ("det_on", "det_off", "cpd_on", "cpd_off", "hyb_on", "hyb_off"):
            r[f"med_abs_{c}"] = float(g[c].abs().median())
        rows.append(r)
    return pd.DataFrame(rows)


def matched(C):
    d = C.copy()
    d["sens"] = d.tp / d.n_ref.where(d.n_ref > 0)
    d["fa"] = d.fp / d.nonict_h * 24
    m = d.groupby(["set", "variant", "seed", "top"])[["sens", "fa"]].mean().reset_index()
    m = m.groupby(["set", "variant", "top"])[["sens", "fa"]].mean().reset_index()
    out = []
    for (st, v), g in m.groupby(["set", "variant"]):
        g = g.sort_values("fa")
        for t in FA_TARGETS:
            val = float(np.interp(t, g.fa.values, g.sens.values)) if g.fa.min() <= t <= g.fa.max() else np.nan
            out.append(dict(set=st, variant=v, fa_target=t, sens=val, fa_min=float(g.fa.min()), fa_max=float(g.fa.max())))
    return pd.DataFrame(out)


def fmt_ci(b, st, comp, met, dec=3):
    r = b[(b.set == st) & (b.comparison == comp) & (b.metric == met)]
    if not len(r) or not np.isfinite(r["diff"].iloc[0]):
        return "—"
    r = r.iloc[0]
    if not np.isfinite(r.ci_lo):
        return f"{r['diff']:+.{dec}f}"
    return f"{r['diff']:+.{dec}f} [{r.ci_lo:+.{dec}f}, {r.ci_hi:+.{dec}f}]"


def t2(F, Bt, M, ERR, K, cand):
    def lvl(st, v, arm="own", stage="cpd"):
        r = F[(F.set == st) & (F.system == v) & (F.arm == arm) & (F.stage == stage)]
        if not len(r):
            return "—"
        r = r.iloc[0]
        return f"{r.sens:.3f} ± {r.sens_sd:.3f} @ {r.fa:.1f}"

    def mt(st, v, t):
        r = M[(M.set == st) & (M.variant == v) & (M.fa_target == t)]
        return "—" if not len(r) or not np.isfinite(r.sens.iloc[0]) else f"{r.sens.iloc[0]:.3f}"

    def er(st, v, col):
        r = ERR[(ERR.set == st) & (ERR.variant == v) & (ERR.arm == "own")]
        return "—" if not len(r) else f"{r[col].iloc[0]:.0f}"

    texts = dict(zip(K.variant, K.text))
    L = ["# Table T2 — Euréka ablation suite on the V5 model (EUR_ABL)", "",
         "Per-patient mean after the change point localizer, 4 seeds. Development = primary reading (paired patient "
         "bootstrap of variant − V0, 95 % interval; chb01 + chb21 one unit). Test, chb24 and Siena are descriptive "
         "(no variant is chosen from them). Sensitivity ± SD over seeds @ FP/day.", "",
         "| variant | change | dev sensitivity @ FP/day | dev Δ sensitivity | dev Δ F1 | dev Δ FP/day | dev Δ sens at fixed 0.5 % "
         "| dev sens at 28.7 FP/day | test | chb24 | Siena | dev onset / offset (s) |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for v in K.variant:
        c = f"{v} - V0"
        L.append(f"| {v} | {texts.get(v, '')} | {lvl('development', v)} | "
                 f"{'—' if v == 'V0' else fmt_ci(Bt, 'development', c, 'sens')} | "
                 f"{'—' if v == 'V0' else fmt_ci(Bt, 'development', c, 'f1')} | "
                 f"{'—' if v == 'V0' else fmt_ci(Bt, 'development', c, 'fa', 1)} | "
                 f"{'—' if v == 'V0' else fmt_ci(Bt, 'development', c + ' (fixed 0.5 %)', 'sens')} | "
                 f"{mt('development', v, 28.7)} | {lvl('test', v)} | {lvl('chb24', v)} | {lvl('siena', v)} | "
                 f"{er('development', v, 'med_abs_cpd_on')} / {er('development', v, 'med_abs_cpd_off')} |")
    for comp, lab in (("6a: fixed 0.5 % - per-patient budget", "6a"), ("7a: detector boundaries - localizer", "7a"),
                      ("7b: hybrid - localizer", "7b")):
        L.append(f"| {lab} | {comp} | — | {fmt_ci(Bt, 'development', comp, 'sens')} | {fmt_ci(Bt, 'development', comp, 'f1')} "
                 f"| {fmt_ci(Bt, 'development', comp, 'fa', 1)} | — | — | test Δsens {fmt_ci(Bt, 'test', comp, 'sens')} "
                 f"| — | Siena Δsens {fmt_ci(Bt, 'siena', comp, 'sens')} | — |")
    L += ["", "Onset / offset of V0 by boundary rule (development, median |error| s): detector "
          f"{er('development', 'V0', 'med_abs_det_on')} / {er('development', 'V0', 'med_abs_det_off')}, localizer "
          f"{er('development', 'V0', 'med_abs_cpd_on')} / {er('development', 'V0', 'med_abs_cpd_off')}, hybrid "
          f"{er('development', 'V0', 'med_abs_hyb_on')} / {er('development', 'V0', 'med_abs_hyb_off')}.", "",
          "R214 replacement candidates (development: F1 interval above 0 and Δ sensitivity ≥ 0): "
          + (", ".join(cand) if cand else "none") + "."]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--out")
    ap.add_argument("--a0-only", action="store_true")
    a = ap.parse_args()
    test_mode = bool(os.environ.get("R2_TEST"))
    g0 = AG.gate_a0(AG.per_seed(AG.record_rows()))
    log(f"A0 {g0['status']}{' (reported only: test mode, synthetic record)' if test_mode else ''}: {g0['bad']}")
    if g0["status"] != "PASS" and not test_mode:
        raise SystemExit("STOP A0: the per-patient metric does not reproduce the locked V5 numbers from the record files")
    if a.a0_only:
        return
    run = Path(a.run)
    out = Path(a.out) if a.out else run / "aggregate"
    out.mkdir(parents=True, exist_ok=True)
    R, E, C, gates, K = load_run(run)
    na = json.loads((run / "not_available.json").read_text()) if (run / "not_available.json").exists() else {}
    g1 = gate_a1(R, gates, na)
    log(f"A1 {g1['status']}: {g1['bad_gates']} {g1['incomplete'][:5]}")
    (out / "gates.json").write_text(json.dumps([g0, g1], indent=1, default=str))
    if g1["status"] != "PASS":
        raise SystemExit("STOP A1: the run is incomplete or a gate did not pass")
    S = per_seed(R)
    F = AG.four_seed(S)
    F.to_csv(out / "summary.csv", index=False)
    S.to_csv(out / "summary_per_seed.csv", index=False)
    P = per_subject(R)
    P.to_csv(out / "per_subject_means.csv", index=False)
    Bt = bootstrap(P)
    Bt.to_csv(out / "bootstrap.csv", index=False)
    ERR = errors_table(E)
    ERR.to_csv(out / "errors_table.csv", index=False)
    M = matched(C)
    M.to_csv(out / "matched.csv", index=False)
    cand = []
    for v in K.variant:
        if v == "V0":
            continue
        f1 = Bt[(Bt.set == "development") & (Bt.comparison == f"{v} - V0") & (Bt.metric == "f1")]
        se = Bt[(Bt.set == "development") & (Bt.comparison == f"{v} - V0") & (Bt.metric == "sens")]
        if len(f1) and len(se) and f1.ci_lo.iloc[0] > 0 and se["diff"].iloc[0] >= 0:
            cand.append(v)
    pd.DataFrame(dict(candidate=cand)).to_csv(out / "candidates.csv", index=False)
    (out / "T2.md").write_text(t2(F, Bt, M, ERR, K, cand))
    log(f"tables written to {out}; R214 candidates: {cand or 'none'}")


if __name__ == "__main__":
    main()
