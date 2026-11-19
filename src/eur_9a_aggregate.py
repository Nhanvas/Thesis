#!/usr/bin/env python
"""
eur_9a_aggregate.py -- tables of EUR_9A (src/eur_9a.py: V5 with label-free z-score statistics on CHB-MIT; design
results/eureka_d31f/STEP1_DESIGN.md §3). Written and committed before EUR_9A produced any output.

Gates (STOP):
  A0  the per-patient metric reproduces the locked V5 numbers from the record files (r2_r1_aggregate.gate_a0, unchanged)
  A1  every gate of the run PASS (G-raw, G-data, G-stats0, G-feat0, G-worker[smoke], R1.0-dev, R1.0-test, G-k, PROJ,
      G-struct, G-worker[build]); rows complete: 23 cases x 4 seeds x 4 arms x 3 stages in r10, r13/lf and r13/lf_krec
Systems (rows of p3c_freeze.run_budget; arm L2f = V5's own label-free budget clip(q, 0.5 %, 2 %) -> 'own';
frozen = the fixed 0.5 % budget -> 'fixed'):
  V5         r10 rows (= the record, gate R1.0)
  LF         label-free statistics, k recalibrated by V5's rule (r13/lf)   <- the completely label-free system
  LF_krec    label-free statistics at the record's k (r13/lf_krec)          <- the statistics alone
  REBUILD    committed results/r2/r1_system/run/r13/cf_krec (record statistics, features rebuilt from verified EDF in
             R0, record k) on the 21 cases whose file set did not change (chb11, chb21 excluded) <- size of the
             numerical rebuild difference, which LF also carries (descriptive context only)
Readings (no threshold, no selection; design §3): per set (development 15, test 8), stage cpd, arms own and fixed:
per-patient mean sensitivity, F1, FP/day, 4-seed mean +- SD; paired patient bootstrap (B = 10,000, rng 0, seeds
averaged within a patient, chb01 + chb21 one unit) of LF - V5, LF_krec - V5 and REBUILD - V5; seizures detected
(4-seed mean of the pooled TP); k; the change of the statistics (stats_change.csv).
Outputs (<run>/aggregate): summary.csv, summary_per_seed.csv, per_subject_means.csv, bootstrap.csv, seizures.csv,
stats_change_by_case.csv, T9A.md, gates.json.
  python src/eur_9a_aggregate.py --run results/eureka_d31f/9a
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
import r2_r1_aggregate as AG            # noqa: E402
import eur_abl_aggregate as EA          # noqa: E402  (per_seed, per_subject, boot_pair: unchanged)

TAGS = AG.TAGS
ARM = {"L2f": "own", "frozen": "fixed"}
SETS = ["development", "test"]
GAP = ("chb11", "chb21")
NEED = ("G-raw", "G-data", "G-stats0", "G-feat0", "G-worker[smoke]", "R1.0-dev", "R1.0-test", "G-k", "PROJ",
        "G-struct", "G-worker[build]")
REBUILD = REPO / "results" / "r2" / "r1_system" / "run" / "r13" / "cf_krec" / "per_subject.csv"


def log(*a):
    print(*a, flush=True)


def rows(run):
    run = Path(run)
    parts = {"V5": pd.concat([pd.read_csv(run / "r10" / "dev_per_subject.csv"),
                              pd.read_csv(run / "r10" / "test_run_budget.csv")], ignore_index=True),
             "LF": pd.read_csv(run / "r13" / "lf" / "per_subject.csv"),
             "LF_krec": pd.read_csv(run / "r13" / "lf_krec" / "per_subject.csv")}
    if REBUILD.exists():
        rb = pd.read_csv(REBUILD)
        parts["REBUILD"] = rb[rb["set"].isin(SETS) & ~rb.subject.isin(GAP)]
    out = []
    for name, d in parts.items():
        d = d.copy()
        d["variant"] = name
        out.append(d)
    R = pd.concat(out, ignore_index=True)
    return R.rename(columns={"budget": "arm"})


def gate_a1(run, R):
    gates = json.loads((Path(run) / "gates.json").read_text())
    bad = [g["gate"] for g in gates if g.get("status") != "PASS"]
    names = {g["gate"] for g in gates}
    bad += [f"missing {n}" for n in NEED if n not in names]
    short = []
    for v in ("V5", "LF", "LF_krec"):
        g = R[R.variant == v]
        cnt = g.groupby(["set", "subject"]).size()
        short += [f"{v} {i}: {n}" for i, n in cnt.items() if n != len(TAGS) * 4 * 3]
        for st, n_want in (("development", 15), ("test", 8)):
            n = g[g["set"] == st].subject.nunique()
            if n != n_want:
                short.append(f"{v} {st}: {n} subjects (want {n_want})")
    return dict(gate="A1", status="PASS" if not bad and not short else "FAIL", bad_gates=bad, incomplete=short[:30])


def bootstrap(P):
    rng = np.random.default_rng(EA.RNG_SEED)
    out = []
    for st in SETS:
        g = P[P.set == st]
        for v in ("LF", "LF_krec", "REBUILD"):
            for arm in ("own", "fixed"):
                A = g[(g.variant == v) & (g.arm == arm) & (g.stage == "cpd")].set_index("subject")
                Bb = g[(g.variant == "V5") & (g.arm == arm) & (g.stage == "cpd")].set_index("subject")
                if not len(A) or not len(Bb):
                    continue
                for met in ("sens", "f1", "fa"):
                    out.append(dict(set=st, comparison=f"{v} - V5", arm=arm, metric=met,
                                    **EA.boot_pair(A[met], Bb[met], rng)))
    return pd.DataFrame(out)


def seizures(R):
    g = R[(R.stage == "cpd") & R.arm.isin(["own", "fixed"])]
    s = g.groupby(["set", "variant", "arm", "seed"])[["tp", "n_ref", "fp"]].sum().reset_index()
    return s.groupby(["set", "variant", "arm"]).agg(tp_mean=("tp", "mean"), tp_min=("tp", "min"), tp_max=("tp", "max"),
                                                    n_ref=("n_ref", "first"), fp_mean=("fp", "mean")).reset_index()


def stats_by_case(run):
    p = Path(run) / "stats_change.csv"
    if not p.exists():
        return pd.DataFrame()
    S = pd.read_csv(p)
    S["abs_rel"] = S.std_rel_change.abs()
    return S.groupby("case").agg(std_rel_change_median=("std_rel_change", "median"),
                                 std_rel_change_max_abs=("abs_rel", "max"),
                                 mean_shift_sd_median=("mean_shift_in_record_sd", "median")).reset_index()


def t9a(F, Bt, SZ, SC, k):
    def lvl(st, v, arm):
        r = F[(F.set == st) & (F.system == v) & (F.arm == arm) & (F.stage == "cpd")]
        if not len(r):
            return "— | — | —"
        r = r.iloc[0]
        return f"{r.sens:.3f} ± {r.sens_sd:.3f} | {r.f1:.3f} | {r.fa:.1f}"

    def sz(st, v, arm):
        r = SZ[(SZ.set == st) & (SZ.variant == v) & (SZ.arm == arm)]
        return "—" if not len(r) else f"{r.tp_mean.iloc[0]:.2f} of {int(r.n_ref.iloc[0])} ({int(r.tp_min.iloc[0])}–{int(r.tp_max.iloc[0])})"

    L = ["# Table T9A — V5 with label-free z-score statistics (EUR_9A)", "",
         f"k: label-free {k.get('k', float('nan')):.4f}, record {k.get('k_record', float('nan')):.4f}. Per-patient mean "
         "after the change point localizer, 4 seeds (sensitivity ± SD over seeds, F1, FP/day). Paired patient bootstrap "
         "of the difference with V5 (95 % interval; chb01 + chb21 one unit). REBUILD = record statistics with features "
         "rebuilt from the verified EDF (R0), 21 cases with an unchanged file set: the size of the numerical rebuild "
         "difference that LF also carries (its level row covers those 21 cases only; its Δ is paired on them). "
         "Descriptive; no threshold.", ""]
    for arm, lab in (("own", "each patient's label-free budget (V5's operating point)"), ("fixed", "fixed 0.5 % budget")):
        L += [f"## Arm: {lab}", "", "| set | system | sensitivity ± SD | F1 | FP/day | seizures detected (4-seed mean, "
              "range) | Δ sensitivity vs V5 | Δ F1 vs V5 | Δ FP/day vs V5 |", "|---|---|---|---|---|---|---|---|---|"]
        for st in SETS:
            for v in ("V5", "LF", "LF_krec", "REBUILD"):
                c = f"{v} - V5"
                cell = lambda m, d=3: "—" if v == "V5" else EA.fmt_ci(Bt[Bt.arm == arm], st, c, m, d)
                L.append(f"| {st} | {v} | {lvl(st, v, arm)} | {sz(st, v, arm)} | {cell('sens')} | {cell('f1')} | "
                         f"{cell('fa', 1)} |")
        L.append("")
    if len(SC):
        L += ["## Change of the statistics (label-free vs record), per case", "",
              "| case | median relative change of channel SD | largest |change| | median mean shift (record SD) |",
              "|---|---|---|---|"]
        for r in SC.itertuples():
            L.append(f"| {r.case} | {r.std_rel_change_median:+.3%} | {r.std_rel_change_max_abs:.3%} | "
                     f"{r.mean_shift_sd_median:+.4f} |")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run")
    ap.add_argument("--out")
    ap.add_argument("--a0-only", action="store_true")
    a = ap.parse_args()
    if not a.a0_only and not a.run:
        ap.error("--run is required")
    test_mode = bool(os.environ.get("R2_TEST"))
    try:
        g0 = AG.gate_a0(AG.per_seed(AG.record_rows()))
    except Exception as e:              # noqa: BLE001  (the synthetic world has no external record rows)
        if not test_mode:
            raise
        g0 = dict(gate="A0", status=f"not computable in test mode ({type(e).__name__})", bad=[])
    log(f"A0 {g0['status']}{' (reported only: test mode, synthetic record)' if test_mode else ''}: {g0['bad']}")
    if g0["status"] != "PASS" and not test_mode:
        raise SystemExit("STOP A0: the per-patient metric does not reproduce the locked V5 numbers from the record files")
    if a.a0_only:
        return
    run = Path(a.run)
    out = Path(a.out) if a.out else run / "aggregate"
    out.mkdir(parents=True, exist_ok=True)
    R = rows(run)
    g1 = gate_a1(run, R)
    log(f"A1 {g1['status']}: {g1['bad_gates']} {g1['incomplete'][:5]}")
    (out / "gates.json").write_text(json.dumps([g0, g1], indent=1, default=str))
    if g1["status"] != "PASS":
        raise SystemExit("STOP A1: the run is incomplete or a gate did not pass")
    R = R[R.arm.isin(ARM)].copy()
    R["arm"] = R.arm.map(ARM)
    S = EA.per_seed(R)
    F = AG.four_seed(S)
    F.to_csv(out / "summary.csv", index=False)
    S.to_csv(out / "summary_per_seed.csv", index=False)
    P = EA.per_subject(R)
    P.to_csv(out / "per_subject_means.csv", index=False)
    Bt = bootstrap(P)
    Bt.to_csv(out / "bootstrap.csv", index=False)
    SZ = seizures(R)
    SZ.to_csv(out / "seizures.csv", index=False)
    SC = stats_by_case(run)
    SC.to_csv(out / "stats_change_by_case.csv", index=False)
    kp = run / "r13" / "lf" / "k.json"
    k = json.loads(kp.read_text()) if kp.exists() else {}
    (out / "T9A.md").write_text(t9a(F, Bt, SZ, SC, k))
    log(f"tables written to {out}")


if __name__ == "__main__":
    main()
