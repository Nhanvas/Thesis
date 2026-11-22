#!/usr/bin/env python
"""eur_pc8b_read.py -- reading of PC8b: which input block (connectivity row or relative band powers) keeps the detection
of the full node input on patients not used for training (Track F, chat D37-F, 22/11/2026; design
results/eureka_d37f/DESIGN_PC8B.md, approved 13:22). Written and committed before any PC8b output. Container / laptop only.

Inputs: the two committed run folders of EUR_PC8_d / _e (arms P8d / P8e, 8 seeds each, with V0 and PC1's R0 seed 42
rescored), the PC8 run of arm P8c (results/eureka_d37f/pc8_c; rows read, not rescored), the PC8 reading
(results/eureka_d37f/pc8, gates M6 / M7), the R0 control = PC7's primary seeds (results/eureka_d34f/pc7_A, pc7_B; rows
read), PC1's control run (results/eureka_d32f/pc1_r0), the merged PC1 folder (results/eureka_d32f/pc1, arm 10a) and the PC7
reading (results/eureka_d34f/pc7, gate M4).
Gates (STOP):
  M-gates  every gate of the two PC8b runs and of the P8c run PASS (G-pc7plat / G-pc7rep recorded: PASS or DIFF); the
           required gates present (incl. G-pc8cols)
  M0       V0 rows identical in the PC8b runs, the P8c run, both control runs and pc1_r0
  M1       R0 seed 42 rows of the PC8b runs and the P8c run = pc1_r0's; R0 k of each = pc1_r0's = each control run's
  M2       completeness: V0 x 4 seeds, R0 x the 16 control seeds, P8c / P8d / P8e x every seed trained, 6 rows per subject
           and seed
  M4       10a - R0 development point estimates = PC7's q5.csv
  M5       split: the development rows hold exactly the training + validation patients of src/retrain/train_gae_v2.py
           (read with ast, not imported), the test rows the 8 test patients; unseen = validation + test = 11 patients
  M6       the P8c rows read here = the P8c rows of the PC8 reading (per_subject.csv, errors.csv)
  M7       P8c - R0 point estimates (every set of the PC8 reading, every metric) = the PC8 reading's r1.csv
Readings (design §4; per-patient means, own label-free point, after the localizer; the 11 unseen patients primary;
development secondary; validation, test, chb24, Siena descriptive):
  R1  arm - R0 for P8d, P8e (P8c and 10a for reference): two-level bootstrap (patient units, chb01 + chb21 one unit; seeds
      resampled within each group), B = 10,000; the wording rule of the design
  R5  arm - P8c for P8d, P8e (and R0 - P8c): what each block adds to the 7 absolute features; same bootstrap
  R6  share of P8c's gap recovered = (arm - P8c) / (R0 - P8c) in the same draws as R5 (unseen; descriptive)
  R1m arm - R0 with the control restricted to the control runs whose G-pc7rep status equals the arm run's (secondary)
  R3  seeds and machines; R4 events at each budget (CPD stage; per-seed means of the set sums)
Outputs (--out): per_subject.csv, errors.csv, k.csv, seeds.csv, machines.csv, r1.csv, r5.csv, r6.csv, r1_machine.csv,
events.csv, gates.json, T_PC8B.md.
  python src/eur_pc8b_read.py --runs results/eureka_d37f/pc8_d results/eureka_d37f/pc8_e --p8c results/eureka_d37f/pc8_c \
      --pc8 results/eureka_d37f/pc8 --control results/eureka_d34f/pc7_A results/eureka_d34f/pc7_B \
      --ref results/eureka_d32f/pc1_r0 --pc1 results/eureka_d32f/pc1 --pc7 results/eureka_d34f/pc7 \
      --out results/eureka_d37f/pc8b
"""
import argparse
import ast
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eur_pc8_read as P8                 # noqa: E402  (loading, gates, two-level bootstrap, wording: unchanged)

RD = P8.RD
ARMS = ["P8d", "P8e"]
TEXT = {"P8d": "connectivity row + the 7 absolute features (without the relative band powers)",
        "P8e": "relative band powers + the 7 absolute features (without the connectivity row)",
        "P8c": "the 7 absolute features only (PC8)", "10a": "without the 7 absolute features (PC1, 4 seeds)",
        "R0": "the full node input (control)"}
SETS = ["unseen", "development", "validation", "test", "chb24", "siena"]
METRICS, TAGS4 = RD.METRICS, RD.TAGS4
B, RNG_SEED, TOL = 10_000, 0, 1e-12
SPLIT_SRC = Path(__file__).resolve().parent / "retrain" / "train_gae_v2.py"


def split_lists(src=SPLIT_SRC):
    """TRAIN and VAL of the thesis training script, read with ast (the module imports torch)."""
    out = {}
    for node in ast.parse(Path(src).read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and getattr(node.targets[0], "id", None) in ("TRAIN", "VAL"):
            out[node.targets[0].id] = list(ast.literal_eval(node.value))
    if set(out) != {"TRAIN", "VAL"}:
        raise SystemExit(f"STOP M5: TRAIN / VAL not found in {src}")
    return out["TRAIN"], out["VAL"]


def m5(R, train, val):
    dev = set(R[R.set == "development"].subject)
    test = set(R[R.set == "test"].subject)
    if dev != set(train) | set(val) or len(val) != 3 or len(test) != 8 or dev & test:
        raise SystemExit(f"STOP M5: development {sorted(dev)} != TRAIN + VAL, or test {sorted(test)} not 8 patients")
    return sorted(val), sorted(test)


def same_rows(cur, want):
    """M6: the same rows; text and integer columns exactly, float columns to a relative 1e-12 (the PC8 reading's csv was
    written from the parsed run csv, and pandas' default parser is not bit-exact on a round trip: measured on the real
    P8c rows, nonict_h differs by <= 3.6e-15 in 96 of 1,824 rows)."""
    if len(cur) == 0 or len(cur) != len(want) or set(cur.columns) - set(want.columns):
        return False
    w = want[list(cur.columns)].reset_index(drop=True)
    c = cur.reset_index(drop=True)
    for col in c.columns:
        x, y = c[col], w[col]
        if x.dtype.kind == "f" or y.dtype.kind == "f":
            x, y = x.astype(float).to_numpy(), y.astype(float).to_numpy()
            if not np.array_equal(np.isnan(x), np.isnan(y)):
                return False
            ok = ~np.isnan(x)
            if (np.abs(x[ok] - y[ok]) > TOL * np.maximum(1.0, np.abs(y[ok]))).any():
                return False
        elif not x.equals(y):
            return False
    return True


def arm_of(run, allowed):
    v = [x for x in run["meta"]["variants"] if x in allowed]
    if len(v) != 1:
        raise SystemExit(f"STOP: a run must hold exactly one arm of {allowed}, found {v}")
    return v[0]


def add_sets(P, val, test):
    """adds the derived sets: unseen = validation + test patients, validation = the 3 validation patients."""
    u = P[P.subject.isin(val + test)].assign(set="unseen")
    v = P[P.subject.isin(val)].assign(set="validation")
    return pd.concat([P, u, v], ignore_index=True)


def boot(P_all, st, met, seeds_of, names, ref_key, rng):
    mats = {v: RD.matrix(P_all, st, v, met, seeds_of[v]) for v in names}
    subj = [s for s in mats[ref_key].index if all(s in m.index for m in mats.values())]
    if not subj:
        return None
    groups = {v: m.loc[subj].values for v, m in mats.items()}
    if len(subj) >= 2:
        point, bs = P8.two_level(groups, ref_key, rng, B, subj)
    else:
        point = {k: float((groups[k].mean(axis=1) - groups[ref_key].mean(axis=1)).mean()) for k in groups if k != ref_key}
        bs = {k: np.full(1, np.nan) for k in point}
    return subj, groups, point, bs


def ci(bs, n):
    return (float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))) if n >= 2 else (np.nan, np.nan)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--p8c", required=True)
    ap.add_argument("--pc8", required=True)
    ap.add_argument("--control", nargs="+", required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--pc1", required=True)
    ap.add_argument("--pc7", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--split-src", default=str(SPLIT_SRC))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RNG_SEED)
    allp = a.runs + [a.p8c]
    if len({Path(r).resolve() for r in allp}) != len(allp) or len({Path(r).name for r in allp}) != len(allp):
        raise SystemExit(f"STOP: one run per arm expected, got the same run twice: {allp}")
    runs = {Path(r).name: P8.load_run(r) for r in a.runs}
    crun = {Path(a.p8c).name: P8.load_run(a.p8c)}
    controls = {Path(r).name: RD.load(r) for r in a.control}
    ref = RD.load(a.ref)
    bad, info = P8.gate_runs({**runs, **crun})
    if bad:
        raise SystemExit(f"STOP M-gates: {bad}")
    arm_by_run = {n: arm_of(r, ARMS) for n, r in runs.items()}
    if sorted(arm_by_run.values()) != ARMS:
        raise SystemExit(f"STOP: one run per arm expected, got {arm_by_run}")
    cname = list(crun)[0]
    if arm_of(crun[cname], ["P8a", "P8b", "P8c"]) != "P8c":
        raise SystemExit(f"STOP: --p8c must be the PC8 run of arm P8c, got {crun[cname]['meta']['variants']}")
    arm_by_run_all = {**arm_by_run, cname: "P8c"}
    RD.m0({**runs, **crun, **controls}, ref)
    k_r0 = P8.m1({**runs, **crun}, ref, controls)

    first = list(runs)[0]
    primary = json.loads((Path(a.pc7) / "gates.json").read_text())["primary_seeds"]
    cnames = list(controls)
    ctrl_seeds = {n: [t for t in primary if t in c["meta"]["arm_seeds"] and t not in c["meta"].get("arm_reuse", [])]
                  for n, c in controls.items()}
    reused_p = [t for t in primary if not any(t in v for v in ctrl_seeds.values())]
    ctrl_seeds[cnames[0]] = ctrl_seeds[cnames[0]] + reused_p                     # pooled reading only (not on real PC7)
    if sorted(sum(ctrl_seeds.values(), []), key=RD.seed_num) != sorted(primary, key=RD.seed_num):
        raise SystemExit(f"STOP: control seeds {ctrl_seeds} != PC7's primary seeds {primary}")
    parts = {f: [] for f in ("per_subject.csv", "errors.csv")}
    allruns = {**runs, **crun}
    for f in parts:
        d = runs[first][f]
        parts[f].append(d[d.variant == "V0"])
        for n, c in controls.items():
            d = c[f]
            parts[f].append(d[(d.variant == "R0") & d.seed.isin(ctrl_seeds[n])])
        for n, r in allruns.items():
            d = r[f]
            parts[f].append(d[d.variant == arm_by_run_all[n]])
    R = pd.concat(parts["per_subject.csv"], ignore_index=True)
    E = pd.concat(parts["errors.csv"], ignore_index=True)
    trained = {arm_by_run_all[n]: sorted(set(r["per_subject.csv"].query(f"variant == '{arm_by_run_all[n]}'").seed),
                                         key=RD.seed_num) for n, r in allruns.items()}
    r0_seeds = sorted(sum(ctrl_seeds.values(), []), key=RD.seed_num)
    P8.m2(R, {"V0": TAGS4, "R0": r0_seeds, **trained})

    # M6: the P8c rows = the PC8 reading's P8c rows
    pc8 = Path(a.pc8)
    for f in ("per_subject.csv", "errors.csv"):
        want = pd.read_csv(pc8 / f)
        want = RD.canon(want[want.variant == "P8c"])
        cur = RD.canon(R[R.variant == "P8c"] if f == "per_subject.csv" else E[E.variant == "P8c"])
        if not same_rows(cur, want):
            raise SystemExit(f"STOP M6: P8c rows of {f} differ from the PC8 reading")
    train, val = split_lists(a.split_src)
    val, test = m5(R, train, val)
    R.to_csv(out / "per_subject.csv", index=False)
    E.to_csv(out / "errors.csv", index=False)
    pd.concat([r["k"].assign(run=n) for n, r in allruns.items()], ignore_index=True).to_csv(out / "k.csv", index=False)
    print(f"M-gates / M0 / M1 / M2 / M5 / M6 PASS; arms {arm_by_run_all}; seeds {trained}; R0 control N = "
          f"{len(r0_seeds)} (k {k_r0:.9f}); unseen = {val} + {test}")

    R = RD.set_names(R)
    P = RD.per_patient_seed(R)
    pc1 = Path(a.pc1)
    Pa = RD.per_patient_seed(RD.set_names(pd.read_csv(pc1 / "per_subject.csv")))
    Pa = Pa[Pa.variant == "10a"]
    P_all = add_sets(pd.concat([P, Pa], ignore_index=True), val, test)
    SV = RD.seed_values(P_all)
    seeds_of = {"R0": r0_seeds, "10a": TAGS4, **trained}

    # R1 arm - R0
    r1 = []
    for st in SETS:
        for met in METRICS:
            res = boot(P_all, st, met, seeds_of, ["R0", "10a", "P8c"] + ARMS, "R0", rng)
            if res is None:
                continue
            subj, groups, point, bs = res
            for v in ["10a", "P8c"] + ARMS:
                lo, hi = ci(bs[v], len(subj))
                r1.append(dict(comparison=f"{v} - R0", arm=v, set=st, metric=met, patients=len(subj),
                               arm_seeds=groups[v].shape[1], r0_seeds=groups["R0"].shape[1], diff=point[v], ci_lo=lo,
                               ci_hi=hi, reading="primary" if (st == "unseen" and v in ARMS) else
                               ("secondary" if (st == "development" and v in ARMS) else "descriptive"),
                               wording=P8.wording(met, lo, hi)))
    R1t = pd.DataFrame(r1)
    R1t.to_csv(out / "r1.csv", index=False)

    # M7: P8c - R0 point estimates = the PC8 reading's r1.csv
    q = pd.read_csv(pc8 / "r1.csv", float_precision="round_trip")
    q = q[q.arm == "P8c"]
    if len(q) == 0:
        raise SystemExit("STOP M7: no P8c rows in the PC8 reading's r1.csv")
    for _, w in q.iterrows():
        mine = R1t[(R1t.arm == "P8c") & (R1t.set == w.set) & (R1t.metric == w.metric)]
        if len(mine) != 1 or abs(mine["diff"].iloc[0] - w["diff"]) > TOL * max(1.0, abs(w["diff"])):
            raise SystemExit(f"STOP M7: P8c - R0 {w.set} {w.metric}: {mine['diff'].tolist()} != PC8 {w['diff']!r}")
    print("M7 PASS: P8c - R0 = the PC8 reading")

    # R5 arm - P8c (and R0 - P8c); R6 share of P8c's gap recovered (same draws)
    r5, r6 = [], []
    for st in SETS:
        for met in METRICS:
            res = boot(P_all, st, met, seeds_of, ["P8c", "R0"] + ARMS, "P8c", rng)
            if res is None:
                continue
            subj, groups, point, bs = res
            for v in ["R0"] + ARMS:
                lo, hi = ci(bs[v], len(subj))
                r5.append(dict(comparison=f"{v} - P8c", arm=v, set=st, metric=met, patients=len(subj),
                               arm_seeds=groups[v].shape[1], p8c_seeds=groups["P8c"].shape[1], diff=point[v], ci_lo=lo,
                               ci_hi=hi, reading="primary" if (st == "unseen" and v in ARMS) else
                               ("secondary" if (st == "development" and v in ARMS) else "descriptive"),
                               wording=P8.wording(met, lo, hi)))
            if st in ("unseen", "development") and len(subj) >= 2:
                for v in ARMS:
                    with np.errstate(divide="ignore", invalid="ignore"):
                        ratio = bs[v] / bs["R0"]
                    r6.append(dict(arm=v, set=st, metric=met, gap_r0_minus_p8c=point["R0"],
                                   share=point[v] / point["R0"] if point["R0"] else np.nan,
                                   ci_lo=float(np.nanpercentile(ratio, 2.5)), ci_hi=float(np.nanpercentile(ratio, 97.5))))
    R5t, R6t = pd.DataFrame(r5), pd.DataFrame(r6)
    R5t.to_csv(out / "r5.csv", index=False)
    R6t.to_csv(out / "r6.csv", index=False)

    # R1m machine-matched control
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
                res = boot(P_all, st, met, {"R0": cs, arm: trained[arm]}, ["R0", arm], "R0", rng)
                if res is None:
                    continue
                subj, groups, point, bs = res
                lo, hi = ci(bs[arm], len(subj))
                r1m.append(dict(comparison=f"{arm} - R0 (control {rep_of(r)})", arm=arm, set=st, metric=met,
                                patients=len(subj), arm_seeds=groups[arm].shape[1], r0_seeds=groups["R0"].shape[1],
                                diff=point[arm], ci_lo=lo, ci_hi=hi, reading="secondary", wording=P8.wording(met, lo, hi)))
    R1m = pd.DataFrame(r1m)
    R1m.to_csv(out / "r1_machine.csv", index=False)

    # M4: 10a - R0 development = PC7's q5
    q5 = pd.read_csv(Path(a.pc7) / "q5.csv", float_precision="round_trip")
    for met in METRICS:
        mine = R1t[(R1t.arm == "10a") & (R1t.set == "development") & (R1t.metric == met)]["diff"].iloc[0]
        want = q5[(q5.comparison == "10a - R0") & (q5.set == "development") & (q5.metric == met)]["diff"].iloc[0]
        if abs(mine - want) > TOL * max(1.0, abs(want)):
            raise SystemExit(f"STOP M4: 10a - R0 development {met} {mine!r} != PC7 q5 {want!r}")
    print("M4 PASS: 10a - R0 development = PC7's q5")

    # R3 seeds and machines
    seeds_tab, mach = [], []
    for n, r in allruns.items():
        arm = arm_by_run_all[n]
        meta, g = r["meta"], {x["gate"]: x for x in r["gates"]}
        ms = [v["ms_per_step"] for (am, _), v in r["arm_train"].items() if am == arm and v.get("ms_per_step")]
        mach.append(dict(run=n, arm=arm, cpu_model=meta.get("cpu_model"), g_pc7rep=g.get("G-pc7rep", {}).get("status"),
                         g_pc7plat=g.get("G-pc7plat", {}).get("status"), ms_per_step_min=min(ms) if ms else np.nan,
                         ms_per_step_max=max(ms) if ms else np.nan, runtime_h=meta.get("runtime_h"),
                         skipped=info[n]["skipped"]))
        for t in trained[arm]:
            tr = r["arm_train"].get((arm, t), {})
            row = dict(arm=arm, seed=t, **{k: tr.get(k) for k in ("val_loss", "train_loss", "n_params", "in_dim", "out_x",
                                                                  "ms_per_step")})
            for st in ("unseen", "development", "siena"):
                x = SV[(SV.set == st) & (SV.variant == arm) & (SV.seed == t)]
                for met in METRICS:
                    row[f"{st}_{met}"] = float(x[met].iloc[0]) if len(x) else np.nan
            seeds_tab.append(row)
    ST, MA = pd.DataFrame(seeds_tab), pd.DataFrame(mach)
    ST.to_csv(out / "seeds.csv", index=False)
    MA.to_csv(out / "machines.csv", index=False)

    # R4 events (CPD stage, per-seed means of the set sums)
    C = R[R.stage == "cpd"].copy()
    Ca = RD.set_names(pd.read_csv(pc1 / "per_subject.csv"))
    C = pd.concat([C, Ca[(Ca.variant == "10a") & (Ca.stage == "cpd")]], ignore_index=True)
    C = pd.concat([C[C.set.isin(["development", "siena"])], C[C.subject.isin(val + test)].assign(set="unseen")],
                  ignore_index=True)
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

    gates = dict(m_gates="PASS", m0="PASS", m1="PASS", m2="PASS", m4="PASS", m5="PASS", m6="PASS", m7="PASS", info=info,
                 arms=arm_by_run_all, seeds=trained, r0_control=r0_seeds, k_r0=k_r0, unseen=dict(validation=val, test=test),
                 machine_matched=matched)
    (out / "gates.json").write_text(json.dumps(gates, indent=1, default=str), encoding="utf-8")
    (out / "T_PC8B.md").write_text(report(ST, MA, R1t, R5t, R6t, R1m, EV, SV, gates), encoding="utf-8")
    print((out / "T_PC8B.md").read_text(encoding="utf-8")[:6000])


def _f(x, met, sign=False):
    return P8._f(x, met, sign)


def _rows(L, T, label):
    for _, r in T.iterrows():
        L.append(f"| {r.comparison} | {r.set} | {r.metric} | {r.patients} | {r.arm_seeds} | {_f(r['diff'], r.metric, True)} "
                 f"[{_f(r.ci_lo, r.metric, True)}, {_f(r.ci_hi, r.metric, True)}] | {r.reading} | {r.wording} |")


def report(ST, MA, R1t, R5t, R6t, R1m, EV, SV, g):
    L = ["# Table T_PC8B — which input block keeps the detection on unseen patients (retraining, Kaggle CPU)", "",
         "Design `results/eureka_d37f/DESIGN_PC8B.md` (written before the run). Arms retrained with the thesis recipe, 8 "
         f"seeds each; P8c = the PC8 run (rows read); control R0 = PC7's primary seeds (N = {len(g['r0_control'])}; rows "
         "read; gates M0, M1). Per-patient means, own label-free point, after the localizer. Unseen = the 3 validation + "
         f"8 test patients ({', '.join(g['unseen']['validation'] + g['unseen']['test'])}; primary); development (15) "
         "secondary; validation, test, chb24, Siena descriptive. Two-level bootstrap (patient units, chb01 + chb21 one "
         f"unit; seeds within each group), B = {B}.", "",
         "Arms: " + "; ".join(f"{k} = {v}" for k, v in TEXT.items()) + ".", "",
         "## Machines", "", "| run | arm | CPU model | G-pc7rep | ms per step | runtime h | seeds skipped |",
         "|---|---|---|---|---|---|---|"]
    for _, r in MA.iterrows():
        L.append(f"| {r.run} | {r.arm} | {r.cpu_model} | {r.g_pc7rep} | {r.ms_per_step_min:.2f}–{r.ms_per_step_max:.2f} | "
                 f"{r.runtime_h} | {r.skipped} |")
    head = "| comparison | set | metric | patients | arm seeds | Δ [95 %] | reading | wording |"
    L += ["", "## R1 — arm − R0 (unseen primary)", "", head, "|---|---|---|---|---|---|---|---|"]
    _rows(L, R1t, "R1")
    L += ["", "## R5 — arm − P8c: what each block adds to the 7 absolute features (unseen primary)", "", head,
          "|---|---|---|---|---|---|---|---|"]
    _rows(L, R5t, "R5")
    L += ["", "## R6 — share of P8c's gap to R0 recovered by the block (ratio of paired bootstrap draws; descriptive)", "",
          "| arm | set | metric | R0 − P8c | share [95 %] |", "|---|---|---|---|---|"]
    for _, r in R6t.iterrows():
        L.append(f"| {r.arm} | {r.set} | {r.metric} | {_f(r.gap_r0_minus_p8c, r.metric, True)} | {r.share:.2f} "
                 f"[{r.ci_lo:.2f}, {r.ci_hi:.2f}] |")
    if len(R1m):
        L += ["", "## R1m — arm − R0 with the machine-matched control (secondary)", "",
              f"Control seeds per arm: {json.dumps(g.get('machine_matched', {}))}", "", head,
              "|---|---|---|---|---|---|---|---|"]
        _rows(L, R1m, "R1m")
    L += ["", "## Means over seeds", "", "| set | variant | seeds | sensitivity | F1 | FP/day |", "|---|---|---|---|---|---|"]
    for st in SETS:
        for v in ["V0", "R0", "10a", "P8c"] + ARMS:
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
    L += ["", "## R3 — seeds", "", "| arm | seed | parameters | validation loss | training loss | ms per step | unseen sensitivity | "
          "unseen FP/day | dev sensitivity | Siena sensitivity |", "|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in ST.iterrows():
        L.append(f"| {r.arm} | {r.seed} | {r.n_params} | {r.val_loss:.5f} | {r.train_loss:.5f} | {r.ms_per_step} | "
                 f"{r.unseen_sens:.3f} | {r.unseen_fa:.1f} | {r.development_sens:.3f} | {r.siena_sens:.3f} |")
    L += ["", "Gates: " + json.dumps({k: g[k] for k in ("m_gates", "m0", "m1", "m2", "m4", "m5", "m6", "m7")}) +
          f"; R0 k {g['k_r0']:.9f}.", ""]
    return "\n".join(L)


if __name__ == "__main__":
    main()
