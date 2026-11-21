#!/usr/bin/env python
"""eur_pc8_read.py -- reading of PC8, the decomposition of the 7 absolute features (Track F, chat D37-F, 21/11/2026; design
results/eureka_d37f/DESIGN_PC8.md, approved 12:42). Written and committed before any PC8 output. Container / laptop only.

Inputs: the three committed run folders of EUR_PC8_a / _b / _c (arms P8a / P8b / P8c, 8 seeds each, with V0 and PC1's R0
seed 42 rescored), the R0 control = PC7's primary seeds (its gates.json; the 16 new seeds of results/eureka_d34f/pc7_A, pc7_B; rows read,
not rescored),
PC1's control run (results/eureka_d32f/pc1_r0), the merged PC1 folder (results/eureka_d32f/pc1, arm 10a) and the PC7
reading (results/eureka_d34f/pc7, for gate M4).
Gates (STOP):
  M-gates  every gate of each PC8 run PASS (G-pc7plat / G-pc7rep recorded: PASS or DIFF); the required gates present
           (incl. G-pc8cols, G-pc7reuse, G-pc7k, G-pc7r0, G-guard)
  M0       V0 rows (per_subject, errors, curve) identical in every PC8 run, both control runs and pc1_r0
  M1       R0 seed 42 rows (per_subject, errors) of every PC8 run = pc1_r0's; R0 k of every PC8 run = pc1_r0's = each
           control run's (the control rows were scored with the same k)
  M2       completeness: V0 x 4 seeds, R0 x seed 42, the arm x every seed trained, 6 rows (2 budgets x 3 stages) per
           subject and seed; control R0 x its 16 trained seeds on every case
  M4       10a - R0 development point estimates (sensitivity, F1, FP/day) = PC7's q5.csv (the same data, the same rule)
Readings (design §4; per-patient means, own label-free point, after the localizer; development primary; test, chb24,
Siena descriptive):
  R1 arm - R0 for P8a, P8b, P8c (and 10a, PC1, for reference): two-level bootstrap (patient units, chb01 + chb21 one
     unit; seeds resampled within each group), B = 10,000; the wording rule of the design
  R2 share of 10a's loss: (arm - R0) / (10a - R0) in the same bootstrap draws (development; descriptive)
  R3 seeds: training / validation loss, parameters, ms per step, machine (CPU model, G-pc7rep) and development / test
     metrics per seed
  R4 events at each budget (CPD stage; per-seed means): events, seizures found, false alarms, seconds per event, flagged
     time (as DIAG_PC1)
Outputs (--out): per_subject.csv, errors.csv, k.csv, seeds.csv, r1.csv, r2.csv, events.csv, machines.csv, gates.json,
T_PC8.md.
  python src/eur_pc8_read.py --runs results/eureka_d37f/pc8_a results/eureka_d37f/pc8_b results/eureka_d37f/pc8_c \
      --control results/eureka_d34f/pc7_A results/eureka_d34f/pc7_B --ref results/eureka_d32f/pc1_r0 \
      --pc1 results/eureka_d32f/pc1 --pc7 results/eureka_d34f/pc7 --out results/eureka_d37f/pc8
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eur_pc7_read as RD                # noqa: E402  (loading, metrics and the unit bootstrap: unchanged)

ARMS = ["P8a", "P8b", "P8c"]
TEXT = {"P8a": "without the 5 log band powers", "P8b": "without log line length + kurtosis",
        "P8c": "the 7 absolute features only", "10a": "without the 7 absolute features (PC1, 4 seeds)"}
SETS, METRICS, TAGS4 = RD.SETS, RD.METRICS, RD.TAGS4
INFO_GATES = RD.INFO_GATES
REQUIRED = RD.REQUIRED + ["G-pc8cols"]
B, RNG_SEED = 10_000, 0
TOL = 1e-12


def load_run(run):
    r = RD.load(run)
    r["arm_train"] = {}
    for md in sorted((Path(run) / "models").glob("*")):
        for js in sorted(md.glob("gae_v2_clean_seed*.json")):
            if js.name.endswith("_DONE.json"):
                continue
            m = json.loads(js.read_text())
            done = js.with_name(js.stem + "_DONE.json")
            dj = json.loads(done.read_text()) if done.exists() else {}
            r["arm_train"][(md.name, js.stem.replace("gae_v2_", ""))] = dict(
                val_loss=m.get("final_val"), train_loss=m.get("last_loss"), first_loss=m.get("first_loss"),
                epochs=m.get("epochs"), n_params=m.get("n_params"), in_dim=m.get("in_dim"), out_x=m.get("out_x"),
                ms_per_step=dj.get("ms_per_step", m.get("ms_per_step")))
    return r


def arm_of(run):
    v = [x for x in run["meta"]["variants"] if x in ARMS]
    if len(v) != 1:
        raise SystemExit(f"STOP: a PC8 run must hold exactly one PC8 arm, found {v}")
    return v[0]


def gate_runs(runs):
    bad, info = {}, {}
    for name, r in runs.items():
        g = {x["gate"]: x for x in r["gates"]}
        b = [k for k, x in g.items() if k not in INFO_GATES and x.get("status") != "PASS"]
        b += [f"missing {k}" for k in REQUIRED if k not in g]
        b += [f"{k} {g[k].get('status')}" for k in INFO_GATES if k in g and g[k].get("status") not in ("PASS", "DIFF")]
        if b:
            bad[name] = b
        info[name] = {k: g.get(k, {}).get("status") for k in INFO_GATES} | {"skipped": g.get("G-guard", {}).get("skipped")}
    return bad, info


def m1(runs, ref, controls):
    for f in ("per_subject.csv", "errors.csv"):
        want = RD.canon(ref[f][(ref[f].variant == "R0") & (ref[f].seed == "clean_seed42")])
        for n, r in runs.items():
            cur = RD.canon(r[f][(r[f].variant == "R0") & (r[f].seed == "clean_seed42")])
            if len(cur) == 0 or not cur.equals(want[list(cur.columns)]):
                raise SystemExit(f"STOP M1: {n}: R0 seed 42 rows of {f} differ from pc1_r0")
    k_ref = float(ref["k"][ref["k"].variant == "R0"].k.iloc[0])
    for n, r in list(runs.items()) + list(controls.items()):
        k = r["k"][r["k"].variant == "R0"]
        if "seed" in k.columns:
            k = k[k.seed.isna()]
        kk = float(k.k.iloc[0])
        if abs(kk - k_ref) / abs(k_ref) > 1e-6:
            raise SystemExit(f"STOP M1: {n}: R0 k {kk!r} != pc1_r0 {k_ref!r}")
    return k_ref


def m2(R, want):
    bad = []
    for v, seeds in want.items():
        d = R[R.variant == v]
        for s, g in d.groupby("subject"):
            got = g.groupby("seed").size()
            if set(got.index) != set(seeds) or (got != 6).any():
                bad.append(f"{s}/{v}: seeds {sorted(set(got.index) ^ set(seeds))} counts {sorted(set(got.values))}")
        if d.subject.nunique() != R.subject.nunique():
            bad.append(f"{v}: {d.subject.nunique()} of {R.subject.nunique()} subjects")
    if bad:
        raise SystemExit(f"STOP M2: incomplete rows {bad[:10]}")


def two_level(groups, ref_key, rng, nb, subj):
    """groups: {name: (patients x seeds) array, rows aligned on subj}. Returns point differences (name - ref) and the
    bootstrap draws (nb x names) with common patient-unit draws and a common resample of the reference seeds."""
    uix, draws, U = RD.unit_draw(subj, rng, nb)
    names = [k for k in groups if k != ref_key]
    Rv = groups[ref_key]
    point = {k: float((groups[k].mean(axis=1) - Rv.mean(axis=1)).mean()) for k in names}
    bs = np.empty((nb, len(names)))
    for b in range(nb):
        rr = Rv[:, rng.integers(0, Rv.shape[1], Rv.shape[1])].mean(axis=1)
        for j, k in enumerate(names):
            A = groups[k]
            bs[b, j] = RD.unit_mean(A[:, rng.integers(0, A.shape[1], A.shape[1])].mean(axis=1) - rr, uix, draws[b], U)
    return point, {k: bs[:, j] for j, k in enumerate(names)}


def wording(met, lo, hi):
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return "descriptive (one patient)"
    if met == "fa":
        return "more false alarms" if lo > 0 else ("fewer false alarms" if hi < 0 else "no measurable difference")
    return "loses" if hi < 0 else ("gains" if lo > 0 else "no measurable difference")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--control", nargs="+", required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--pc1", required=True)
    ap.add_argument("--pc7", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RNG_SEED)
    if len({Path(r).resolve() for r in a.runs}) != len(a.runs) or len({Path(r).name for r in a.runs}) != len(a.runs):
        raise SystemExit(f"STOP: one run per arm expected, got the same run twice: {a.runs}")
    runs = {Path(r).name: load_run(r) for r in a.runs}
    controls = {Path(r).name: RD.load(r) for r in a.control}
    ref = RD.load(a.ref)
    bad, info = gate_runs(runs)
    if bad:
        raise SystemExit(f"STOP M-gates: {bad}")
    arm_by_run = {n: arm_of(r) for n, r in runs.items()}
    if sorted(arm_by_run.values()) != ARMS:
        raise SystemExit(f"STOP: one run per arm expected, got {arm_by_run}")
    RD.m0({**runs, **controls}, ref)
    k_r0 = m1(runs, ref, controls)

    # merge: V0 once (first PC8 run); control R0 = each control run's trained (not reused) seeds; each run's arm rows
    first = list(runs)[0]
    primary = json.loads((Path(a.pc7) / "gates.json").read_text())["primary_seeds"]     # PC7's primary R0 seeds
    cnames = list(controls)
    ctrl_seeds = {n: [t for t in primary if t in c["meta"]["arm_seeds"] and t not in c["meta"].get("arm_reuse", [])]
                  for n, c in controls.items()}
    reused_p = [t for t in primary if not any(t in v for v in ctrl_seeds.values())]
    ctrl_seeds[cnames[0]] = ctrl_seeds[cnames[0]] + reused_p                     # pooled reading only (not on real PC7)
    if sorted(sum(ctrl_seeds.values(), []), key=RD.seed_num) != sorted(primary, key=RD.seed_num):
        raise SystemExit(f"STOP: control seeds {ctrl_seeds} != PC7's primary seeds {primary}")
    parts = {f: [] for f in ("per_subject.csv", "errors.csv")}
    for f in parts:
        d = runs[first][f]
        parts[f].append(d[d.variant == "V0"])
        for n, c in controls.items():
            d = c[f]
            parts[f].append(d[(d.variant == "R0") & d.seed.isin(ctrl_seeds[n])])
        for n, r in runs.items():
            d = r[f]
            parts[f].append(d[d.variant == arm_by_run[n]])
    R = pd.concat(parts["per_subject.csv"], ignore_index=True)
    E = pd.concat(parts["errors.csv"], ignore_index=True)
    trained = {arm_by_run[n]: sorted(set(r["per_subject.csv"].query(f"variant == '{arm_by_run[n]}'").seed), key=RD.seed_num)
               for n, r in runs.items()}
    r0_seeds = sorted(sum(ctrl_seeds.values(), []), key=RD.seed_num)
    m2(R, {"V0": TAGS4, "R0": r0_seeds, **trained})
    R.to_csv(out / "per_subject.csv", index=False)
    E.to_csv(out / "errors.csv", index=False)
    pd.concat([r["k"].assign(run=n) for n, r in runs.items()], ignore_index=True).to_csv(out / "k.csv", index=False)
    print(f"M-gates / M0 / M1 / M2 PASS; arms {arm_by_run}; seeds {trained}; R0 control N = {len(r0_seeds)} (k {k_r0:.9f})")

    R = RD.set_names(R)
    P = RD.per_patient_seed(R)
    pc1 = Path(a.pc1)
    Pa = RD.per_patient_seed(RD.set_names(pd.read_csv(pc1 / "per_subject.csv")))
    Pa = Pa[Pa.variant == "10a"]
    P_all = pd.concat([P, Pa], ignore_index=True)
    SV = RD.seed_values(P_all)

    # R3 seeds and machines
    seeds_tab, mach = [], []
    for n, r in runs.items():
        arm = arm_by_run[n]
        meta, g = r["meta"], {x["gate"]: x for x in r["gates"]}
        ms = [v["ms_per_step"] for (am, _), v in r["arm_train"].items() if am == arm and v.get("ms_per_step")]
        mach.append(dict(run=n, arm=arm, cpu_model=meta.get("cpu_model"), cpu_models="; ".join(meta.get("cpu_models", [])),
                         g_pc7rep=g.get("G-pc7rep", {}).get("status"), g_pc7plat=g.get("G-pc7plat", {}).get("status"),
                         ms_per_step_min=min(ms) if ms else np.nan, ms_per_step_max=max(ms) if ms else np.nan,
                         runtime_h=meta.get("runtime_h"), skipped=info[n]["skipped"]))
        for t in trained[arm]:
            tr = r["arm_train"].get((arm, t), {})
            row = dict(arm=arm, seed=t, **{k: tr.get(k) for k in ("val_loss", "train_loss", "n_params", "in_dim", "out_x",
                                                                  "ms_per_step")})
            for st in ("development", "test"):
                x = SV[(SV.set == st) & (SV.variant == arm) & (SV.seed == t)]
                for met in METRICS:
                    row[f"{st}_{met}"] = float(x[met].iloc[0]) if len(x) else np.nan
            seeds_tab.append(row)
    ST = pd.DataFrame(seeds_tab)
    ST.to_csv(out / "seeds.csv", index=False)
    MA = pd.DataFrame(mach)
    MA.to_csv(out / "machines.csv", index=False)

    # R1 / R2
    r1, r2 = [], []
    seeds_of = {"R0": r0_seeds, "10a": TAGS4, **trained}
    for st in SETS:
        for met in METRICS:
            mats = {}
            for v in ["R0", "10a"] + ARMS:
                mats[v] = RD.matrix(P_all, st, v, met, seeds_of[v])
            subj = [s for s in mats["R0"].index if all(s in m.index for m in mats.values())]
            if not subj:
                continue
            groups = {v: m.loc[subj].values for v, m in mats.items()}
            if len(subj) >= 2:
                point, bs = two_level(groups, "R0", rng, B, subj)
            else:
                point = {k: float((groups[k].mean(axis=1) - groups["R0"].mean(axis=1)).mean()) for k in groups if k != "R0"}
                bs = {k: np.full(1, np.nan) for k in point}
            for v in ["10a"] + ARMS:
                lo, hi = (np.nanpercentile(bs[v], 2.5), np.nanpercentile(bs[v], 97.5)) if len(subj) >= 2 else (np.nan, np.nan)
                r1.append(dict(comparison=f"{v} - R0", arm=v, set=st, metric=met, patients=len(subj),
                               arm_seeds=groups[v].shape[1], r0_seeds=groups["R0"].shape[1], diff=point[v], ci_lo=lo,
                               ci_hi=hi, reading="primary" if (st == "development" and v in ARMS) else "descriptive",
                               wording=wording(met, lo, hi)))
            if st == "development" and len(subj) >= 2:
                for v in ARMS:
                    with np.errstate(divide="ignore", invalid="ignore"):
                        ratio = bs[v] / bs["10a"]
                    r2.append(dict(arm=v, metric=met, share=point[v] / point["10a"] if point["10a"] else np.nan,
                                   ci_lo=float(np.nanpercentile(ratio, 2.5)), ci_hi=float(np.nanpercentile(ratio, 97.5))))
    R1t, R2t = pd.DataFrame(r1), pd.DataFrame(r2)
    R1t.to_csv(out / "r1.csv", index=False)
    R2t.to_csv(out / "r2.csv", index=False)

    # M4: 10a - R0 on development = PC7's Q5 point estimates
    q5 = pd.read_csv(Path(a.pc7) / "q5.csv", float_precision="round_trip")
    for met in METRICS:
        mine = R1t[(R1t.arm == "10a") & (R1t.set == "development") & (R1t.metric == met)]["diff"].iloc[0]
        want = q5[(q5.comparison == "10a - R0") & (q5.set == "development") & (q5.metric == met)]["diff"].iloc[0]
        if abs(mine - want) > TOL * max(1.0, abs(want)):
            raise SystemExit(f"STOP M4: 10a - R0 development {met} {mine!r} != PC7 q5 {want!r}")
    print("M4 PASS: 10a - R0 development = PC7's q5")

    # R4 events (CPD stage, per-seed means of per-set sums)
    C = R[(R.stage == "cpd") & R.set.isin(["development", "test"])].copy()
    Ca = RD.set_names(pd.read_csv(pc1 / "per_subject.csv"))
    Ca = Ca[(Ca.variant == "10a") & (Ca.stage == "cpd") & Ca.set.isin(["development", "test"])]
    C = pd.concat([C, Ca], ignore_index=True)
    C["ev"] = C.tp + C.fp
    per_seed = (C.groupby(["set", "budget", "variant", "seed"])
                .agg(tp=("tp", "sum"), fp=("fp", "sum"), events=("ev", "sum"), review_s=("review_s", "sum"),
                     rec_s=("rec_s", "sum"), n_ref=("n_ref", "sum"), top=("top", "mean")).reset_index())
    per_seed["s_per_event"] = per_seed.review_s / per_seed.events
    per_seed["flagged_time_pct"] = 100 * per_seed.review_s / per_seed.rec_s
    EV = (per_seed.groupby(["set", "budget", "variant"])
          .agg(seeds=("seed", "nunique"), events=("events", "mean"), tp=("tp", "mean"), n_ref=("n_ref", "mean"),
               fp=("fp", "mean"), s_per_event=("s_per_event", "mean"), flagged_time_pct=("flagged_time_pct", "mean"),
               windows_flagged_pct=("top", lambda x: 100 * x.mean())).reset_index())
    EV.to_csv(out / "events.csv", index=False)

    gates = dict(m_gates="PASS", m0="PASS", m1="PASS", m2="PASS", m4="PASS", info=info, arms=arm_by_run, seeds=trained,
                 r0_control=r0_seeds, k_r0=k_r0)
    (out / "gates.json").write_text(json.dumps(gates, indent=1, default=str), encoding="utf-8")
    (out / "T_PC8.md").write_text(report(ST, MA, R1t, R2t, EV, SV, gates), encoding="utf-8")
    print((out / "T_PC8.md").read_text(encoding="utf-8")[:6000])


def _f(x, met, sign=False):
    if not np.isfinite(x):
        return "—"
    s = f"{x:+.3f}" if sign else f"{x:.3f}"
    if met == "fa":
        s = f"{x:+.1f}" if sign else f"{x:.1f}"
    return s


def report(ST, MA, R1t, R2t, EV, SV, g):
    L = ["# Table T_PC8 — decomposition of the 7 absolute features (retraining, Kaggle CPU)", "",
         "Design `results/eureka_d37f/DESIGN_PC8.md` (written before the run). Arms retrained with the thesis recipe, "
         f"8 seeds each; control R0 = PC7's primary seeds (N = {len(g['r0_control'])}; rows read, scored with the same chain and "
         "k; gates M0, M1). "
         "Per-patient means, own label-free point, after the localizer; development = 15 patients (primary); test, chb24, "
         "Siena descriptive. Two-level bootstrap (patient units, chb01 + chb21 one unit; seeds within each group), "
         f"B = {B}.", "", "## Machines", "",
         "| run | arm | CPU model | G-pc7rep | ms per step | runtime h | seeds skipped |", "|---|---|---|---|---|---|---|"]
    for _, r in MA.iterrows():
        L.append(f"| {r.run} | {r.arm} | {r.cpu_model} | {r.g_pc7rep} | {r.ms_per_step_min:.2f}–{r.ms_per_step_max:.2f} | "
                 f"{r.runtime_h} | {r.skipped} |")
    L += ["", "## R1 — arm − R0 (development primary)", "",
          "| comparison | set | metric | arm seeds | Δ [95 %] | reading | wording |", "|---|---|---|---|---|---|---|"]
    for _, r in R1t.iterrows():
        L.append(f"| {r.comparison} ({TEXT[r.arm]}) | {r.set} | {r.metric} | {r.arm_seeds} | {_f(r['diff'], r.metric, True)} "
                 f"[{_f(r.ci_lo, r.metric, True)}, {_f(r.ci_hi, r.metric, True)}] | {r.reading} | {r.wording} |")
    L += ["", "## R2 — share of 10a's loss, development (descriptive; ratio of paired bootstrap draws)", "",
          "| arm | metric | share [95 %] |", "|---|---|---|"]
    for _, r in R2t.iterrows():
        L.append(f"| {r.arm} | {r.metric} | {r.share:.2f} [{r.ci_lo:.2f}, {r.ci_hi:.2f}] |")
    L += ["", "## Means over seeds", "", "| set | variant | seeds | sensitivity | F1 | FP/day |", "|---|---|---|---|---|---|"]
    for st in SETS:
        for v in ["V0", "R0", "10a"] + ARMS:
            x = SV[(SV.set == st) & (SV.variant == v)]
            if len(x):
                L.append(f"| {st} | {v} | {len(x)} | {x.sens.mean():.3f} ± {x.sens.std(ddof=1):.3f} | "
                         f"{x.f1.mean():.3f} ± {x.f1.std(ddof=1):.3f} | {x.fa.mean():.1f} ± {x.fa.std(ddof=1):.1f} |")
    L += ["", "## R4 — events at each budget (CPD stage; per-seed means of the set sums)", "",
          "| set | budget | variant | seeds | events | seizures found | false alarms | s per event | flagged time % | windows flagged % |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in EV.iterrows():
        L.append(f"| {r.set} | {r.budget} | {r.variant} | {r.seeds} | {r.events:.0f} | {r.tp:.1f} / {r.n_ref:.0f} | "
                 f"{r.fp:.0f} | {r.s_per_event:.1f} | {r.flagged_time_pct:.2f} | {r.windows_flagged_pct:.2f} |")
    L += ["", "## R3 — seeds", "", "| arm | seed | parameters | validation loss | training loss | ms per step | dev sensitivity | "
          "dev F1 | dev FP/day | test sensitivity |", "|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in ST.iterrows():
        L.append(f"| {r.arm} | {r.seed} | {r.n_params} | {r.val_loss:.5f} | {r.train_loss:.5f} | {r.ms_per_step} | "
                 f"{r.development_sens:.3f} | {r.development_f1:.3f} | {r.development_fa:.1f} | {r.test_sens:.3f} |")
    L += ["", f"Gates: {json.dumps({k: g[k] for k in ('m_gates', 'm0', 'm1', 'm2', 'm4')})}; R0 k {g['k_r0']:.9f}.", ""]
    return "\n".join(L)


if __name__ == "__main__":
    main()
