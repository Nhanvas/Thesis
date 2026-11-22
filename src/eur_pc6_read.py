#!/usr/bin/env python
"""eur_pc6_read.py -- reading of PC6, the edge type of the graph (Track F, chat D37-F, 22/11/2026; design
results/eureka_d37f/DESIGN_PC6.md §6, approved 07:32). Written and committed before the PC6 training runs.

Inputs: the two committed run folders of EUR_PC6_11a / _11b (arms 11a wPLI only, 11b AEC only, 8 seeds each, with V0 and
PC1's R0 seed 42 rescored), the control runs of PC7 (rows of PC7's primary seeds, read), pc1_r0, the merged PC1 folder and
the PC7 reading (gate M4), as src/eur_pc8_read.py (whose loading, gates and bootstrap are imported unchanged).
Gates (STOP): M-gates (every run gate PASS incl. G-g11data, G-pc6view; G-pc7plat / G-pc7rep recorded), M0, M1, M2, M4,
one run per arm (as PC8).
Readings (per-patient means, own label-free point, after the localizer; development primary; test, chb24, Siena
descriptive): R1 arm - R0 (two-level bootstrap, B = 10,000, PC8's wording); R1m the same against the control seeds of the
arm run's machine type (G-pc7rep status); R5 11a - 11b (descriptive, the same bootstrap with 11b as the reference);
R3 seeds and machines; R4 events at each budget (CPD stage); means over seeds.
Outputs (--out): per_subject.csv, errors.csv, k.csv, seeds.csv, r1.csv, r1_machine.csv, r5.csv, events.csv, machines.csv,
gates.json, T_PC6.md.
  python src/eur_pc6_read.py --runs results/eureka_d37f/pc6_11a results/eureka_d37f/pc6_11b \
      --control results/eureka_d34f/pc7_A results/eureka_d34f/pc7_B --ref results/eureka_d32f/pc1_r0 \
      --pc1 results/eureka_d32f/pc1 --pc7 results/eureka_d34f/pc7 --out results/eureka_d37f/pc6
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eur_pc7_read as RD                # noqa: E402
import eur_pc8_read as R8                # noqa: E402  (load_run, m1, m2, two_level, wording, _f: unchanged)

ARMS = ["11a", "11b"]
TEXT = {"11a": "graph of wPLI only", "11b": "graph of AEC only"}
SETS, METRICS, TAGS4 = RD.SETS, RD.METRICS, RD.TAGS4
REQUIRED = RD.REQUIRED + ["G-g11data", "G-pc6view"]
B, RNG_SEED, TOL = 10_000, 0, 1e-12


def arm_of(run):
    v = [x for x in run["meta"]["variants"] if x in ARMS]
    if len(v) != 1:
        raise SystemExit(f"STOP: a PC6 run must hold exactly one PC6 arm, found {v}")
    return v[0]


def gate_runs(runs):
    bad, info = {}, {}
    for name, r in runs.items():
        g = {x["gate"]: x for x in r["gates"]}
        b = [k for k, x in g.items() if k not in RD.INFO_GATES and x.get("status") != "PASS"]
        b += [f"missing {k}" for k in REQUIRED if k not in g]
        b += [f"{k} {g[k].get('status')}" for k in RD.INFO_GATES if k in g and g[k].get("status") not in ("PASS", "DIFF")]
        if b:
            bad[name] = b
        info[name] = {k: g.get(k, {}).get("status") for k in RD.INFO_GATES} | {"skipped": g.get("G-guard", {}).get("skipped")}
    return bad, info


def diff_rows(groups, ref_key, others, st, met, subj, rng, label, reading):
    rows = []
    if len(subj) >= 2:
        point, bs = R8.two_level({k: groups[k] for k in [ref_key] + others}, ref_key, rng, B, subj)
    else:
        point = {k: float((groups[k].mean(axis=1) - groups[ref_key].mean(axis=1)).mean()) for k in others}
        bs = {k: np.full(1, np.nan) for k in others}
    for v in others:
        lo, hi = (np.nanpercentile(bs[v], 2.5), np.nanpercentile(bs[v], 97.5)) if len(subj) >= 2 else (np.nan, np.nan)
        rows.append(dict(comparison=f"{v} - {label}", arm=v, set=st, metric=met, patients=len(subj),
                         arm_seeds=groups[v].shape[1], ref_seeds=groups[ref_key].shape[1], diff=point[v], ci_lo=lo,
                         ci_hi=hi, reading=reading, wording=R8.wording(met, lo, hi)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    for k in ("--runs", "--control"):
        ap.add_argument(k, nargs="+", required=True)
    for k in ("--ref", "--pc1", "--pc7", "--out"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RNG_SEED)
    if len({Path(r).resolve() for r in a.runs}) != len(a.runs) or len({Path(r).name for r in a.runs}) != len(a.runs):
        raise SystemExit(f"STOP: one run per arm expected, got the same run twice: {a.runs}")
    runs = {Path(r).name: R8.load_run(r) for r in a.runs}
    controls = {Path(r).name: RD.load(r) for r in a.control}
    ref = RD.load(a.ref)
    bad, info = gate_runs(runs)
    if bad:
        raise SystemExit(f"STOP M-gates: {bad}")
    arm_by_run = {n: arm_of(r) for n, r in runs.items()}
    if sorted(arm_by_run.values()) != ARMS:
        raise SystemExit(f"STOP: one run per arm expected, got {arm_by_run}")
    RD.m0({**runs, **controls}, ref)
    k_r0 = R8.m1(runs, ref, controls)
    first = list(runs)[0]
    primary = json.loads((Path(a.pc7) / "gates.json").read_text())["primary_seeds"]
    cnames = list(controls)
    ctrl_seeds = {n: [t for t in primary if t in c["meta"]["arm_seeds"] and t not in c["meta"].get("arm_reuse", [])]
                  for n, c in controls.items()}
    reused_p = [t for t in primary if not any(t in v for v in ctrl_seeds.values())]
    ctrl_seeds[cnames[0]] = ctrl_seeds[cnames[0]] + reused_p
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
    R8.m2(R, {"V0": TAGS4, "R0": r0_seeds, **trained})
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
    seeds_of = {"R0": r0_seeds, "10a": TAGS4, **trained}

    # M4 (the control rows are PC7's)
    q5 = pd.read_csv(Path(a.pc7) / "q5.csv", float_precision="round_trip")
    for met in METRICS:
        Am, Rm = RD.matrix(P_all, "development", "10a", met, TAGS4), RD.matrix(P_all, "development", "R0", met, r0_seeds)
        s_ = [x for x in Rm.index if x in Am.index]
        mine = float((Am.loc[s_].values.mean(axis=1) - Rm.loc[s_].values.mean(axis=1)).mean())
        want = q5[(q5.comparison == "10a - R0") & (q5.set == "development") & (q5.metric == met)]["diff"].iloc[0]
        if abs(mine - want) > TOL * max(1.0, abs(want)):
            raise SystemExit(f"STOP M4: 10a - R0 development {met} {mine!r} != PC7 q5 {want!r}")
    print("M4 PASS: 10a - R0 development = PC7's q5")

    # R1, R5
    r1, r5 = [], []
    for st in SETS:
        for met in METRICS:
            mats = {v: RD.matrix(P_all, st, v, met, seeds_of[v]) for v in ["R0"] + ARMS}
            subj = [s for s in mats["R0"].index if all(s in m.index for m in mats.values())]
            if not subj:
                continue
            groups = {v: m.loc[subj].values for v, m in mats.items()}
            r1 += diff_rows(groups, "R0", ARMS, st, met, subj, rng, "R0",
                            "primary" if st == "development" else "descriptive")
            r5 += diff_rows(groups, "11b", ["11a"], st, met, subj, rng, "11b", "descriptive")
    R1t, R5t = pd.DataFrame(r1), pd.DataFrame(r5)
    R1t.to_csv(out / "r1.csv", index=False)
    R5t.to_csv(out / "r5.csv", index=False)

    # R1m
    rep_of = lambda r: {x["gate"]: x for x in r["gates"]}.get("G-pc7rep", {}).get("status")
    r1m, matched = [], {}
    for n, r in runs.items():
        arm = arm_by_run[n]
        cs = [t for c in controls for t in ctrl_seeds[c] if rep_of(controls[c]) == rep_of(r)
              and t in controls[c]["meta"]["arm_seeds"] and t not in controls[c]["meta"].get("arm_reuse", [])]
        matched[arm] = dict(arm_rep=rep_of(r), control_seeds=cs)
        if len(cs) < 2:
            continue
        for st in SETS:
            for met in METRICS:
                mats = {"R0": RD.matrix(P_all, st, "R0", met, cs), arm: RD.matrix(P_all, st, arm, met, trained[arm])}
                subj = [x for x in mats["R0"].index if x in mats[arm].index]
                if subj:
                    groups = {v: m.loc[subj].values for v, m in mats.items()}
                    r1m += diff_rows(groups, "R0", [arm], st, met, subj, rng, f"R0 (control {rep_of(r)})", "secondary")
    R1m = pd.DataFrame(r1m)
    R1m.to_csv(out / "r1_machine.csv", index=False)

    # R3 seeds / machines, R4 events
    seeds_tab, mach = [], []
    for n, r in runs.items():
        arm = arm_by_run[n]
        meta, g = r["meta"], {x["gate"]: x for x in r["gates"]}
        ms = [v["ms_per_step"] for (am, _), v in r["arm_train"].items() if am == arm and v.get("ms_per_step")]
        mach.append(dict(run=n, arm=arm, cpu_model=meta.get("cpu_model"), g_pc7rep=g.get("G-pc7rep", {}).get("status"),
                         ms_per_step_min=min(ms) if ms else np.nan, ms_per_step_max=max(ms) if ms else np.nan,
                         runtime_h=meta.get("runtime_h"), skipped=info[n]["skipped"]))
        for t in trained[arm]:
            tr = r["arm_train"].get((arm, t), {})
            row = dict(arm=arm, seed=t, **{k: tr.get(k) for k in ("val_loss", "train_loss", "n_params", "ms_per_step")})
            for st in ("development", "test"):
                x = SV[(SV.set == st) & (SV.variant == arm) & (SV.seed == t)]
                for met in METRICS:
                    row[f"{st}_{met}"] = float(x[met].iloc[0]) if len(x) else np.nan
            seeds_tab.append(row)
    ST, MA = pd.DataFrame(seeds_tab), pd.DataFrame(mach)
    ST.to_csv(out / "seeds.csv", index=False)
    MA.to_csv(out / "machines.csv", index=False)
    C = R[(R.stage == "cpd") & R.set.isin(["development", "test"])].copy()
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
                 r0_control=r0_seeds, k_r0=k_r0, machine_matched=matched)
    (out / "gates.json").write_text(json.dumps(gates, indent=1, default=str), encoding="utf-8")
    (out / "T_PC6.md").write_text(report(MA, R1t, R1m, R5t, EV, SV, ST, gates), encoding="utf-8")
    print((out / "T_PC6.md").read_text(encoding="utf-8")[:6000])


def report(MA, R1t, R1m, R5t, EV, SV, ST, g):
    f = R8._f
    L = ["# Table T_PC6 — edge type of the graph (retraining, Kaggle CPU)", "",
         "Design `results/eureka_d37f/DESIGN_PC6.md` (written before the run). 11a = graph of wPLI only, 11b = graph of AEC "
         f"only (top 20 %), retrained with the thesis recipe, 8 seeds each; control R0 = PC7's primary seeds "
         f"(N = {len(g['r0_control'])}; rows read). Per-patient means, own label-free point, after the localizer; "
         f"development primary. Two-level bootstrap, B = {B}.", "", "## Machines", "",
         "| run | arm | CPU model | G-pc7rep | ms per step | runtime h | seeds skipped |", "|---|---|---|---|---|---|---|"]
    for _, r in MA.iterrows():
        L.append(f"| {r.run} | {r.arm} | {r.cpu_model} | {r.g_pc7rep} | {r.ms_per_step_min:.2f}–{r.ms_per_step_max:.2f} | "
                 f"{r.runtime_h} | {r.skipped} |")
    for title, T in (("R1 — arm − R0 (development primary)", R1t),
                     ("R1m — arm − R0 with the machine-matched control (secondary)", R1m),
                     ("R5 — 11a − 11b (descriptive)", R5t)):
        L += ["", f"## {title}", "", "| comparison | set | metric | seeds | Δ [95 %] | reading | wording |",
              "|---|---|---|---|---|---|---|"]
        for _, r in T.iterrows():
            L.append(f"| {r.comparison} | {r.set} | {r.metric} | {r.arm_seeds} / {r.ref_seeds} | "
                     f"{f(r['diff'], r.metric, True)} [{f(r.ci_lo, r.metric, True)}, {f(r.ci_hi, r.metric, True)}] | "
                     f"{r.reading} | {r.wording} |")
    L += ["", f"Machine-matched control: {json.dumps(g['machine_matched'])}", "", "## Means over seeds", "",
          "| set | variant | seeds | sensitivity | F1 | FP/day |", "|---|---|---|---|---|---|"]
    for st in SETS:
        for v in ["V0", "R0"] + ARMS:
            x = SV[(SV.set == st) & (SV.variant == v)]
            if len(x):
                L.append(f"| {st} | {v} | {len(x)} | {x.sens.mean():.3f} ± {x.sens.std(ddof=1):.3f} | "
                         f"{x.f1.mean():.3f} ± {x.f1.std(ddof=1):.3f} | {x.fa.mean():.1f} ± {x.fa.std(ddof=1):.1f} |")
    L += ["", "## R4 — events at each budget (CPD stage; per-seed means)", "",
          "| set | budget | variant | seeds | events | seizures found | false alarms | s per event | flagged time % |",
          "|---|---|---|---|---|---|---|---|---|"]
    for _, r in EV.iterrows():
        L.append(f"| {r.set} | {r.budget} | {r.variant} | {r.seeds} | {r.events:.0f} | {r.tp:.1f} / {r.n_ref:.0f} | "
                 f"{r.fp:.0f} | {r.s_per_event:.1f} | {r.flagged_time_pct:.2f} |")
    L += ["", "## R3 — seeds", "", "| arm | seed | validation loss | training loss | ms per step | dev sensitivity | "
          "dev F1 | dev FP/day | test sensitivity |", "|---|---|---|---|---|---|---|---|---|"]
    for _, r in ST.iterrows():
        L.append(f"| {r.arm} | {r.seed} | {r.val_loss:.5f} | {r.train_loss:.5f} | {r.ms_per_step} | "
                 f"{r.development_sens:.3f} | {r.development_f1:.3f} | {r.development_fa:.1f} | {r.test_sens:.3f} |")
    L += ["", f"Gates: {json.dumps({k: g[k] for k in ('m_gates', 'm0', 'm1', 'm2', 'm4')})}; R0 k {g['k_r0']:.9f}.", ""]
    return "\n".join(L)


if __name__ == "__main__":
    main()
