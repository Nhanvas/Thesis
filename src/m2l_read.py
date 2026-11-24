#!/usr/bin/env python
"""
m2l_read.py -- reading of milestone M2 stream L (chat F2-03; design results/m2l/DESIGN_L2.md §5–§7, approved
23/11/2026 14:19). Committed BEFORE the outputs it reads. Laptop (no EEG needed).

  --l2       results/m2l/l2_rec + l2_rob -> results/m2l/l2/: T_L2.md, summary.csv, bootstrap.csv, per_patient.csv,
             SELECTION.md, selection.json (the rule of DESIGN §6, applied mechanically)
  --l3short  results/m2l/l3short_a + l3short_b (+ l2) -> results/m2l/l3short/: T_L3SHORT.md, summary.csv, minlen.json
  --l3       results/m2l/l3eval (+ l2, l3short) -> results/m2l/l3/: T_L3.md, summary.csv, bootstrap.csv, per_patient.csv

Metrics (as eur_abl_aggregate): per patient and seed sensitivity tp / n_ref (patients with seizures), F1 = 2 tp /
(2 tp + fp + fn), FP/day = fp / non-ictal hours x 24; seeds averaged within a patient; set value = mean over patients.
Paired patient bootstrap of the difference of 4-seed means (B = 10,000, rng 0, chb01 + chb21 one unit), 95 % percentile.
Gates: A0 the runs' gates all PASS and the required gates present; A1 rows complete (patients x seeds x arms x stages).
  python src/m2l_read.py --l2 | --l3short | --l3 [--root results/m2l]
"""
import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(os.environ.get("THESIS_REPO", Path(__file__).resolve().parents[1]))
B, RNG_SEED = 10_000, 0
UNIT = {"chb21": "chb01"}
TAGS = ["clean_seed42", "clean_seed1", "clean_seed2", "clean_seed3"]
STAGES = ["detector", "cpd", "hybrid"]
DEV = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08", "chb09", "chb12", "chb19", "chb20", "chb21", "chb23",
       "chb10", "chb11", "chb22"]
TEST = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
ARMS_L2 = [f"{s}-{c}-{f}" for s in ("R", "B") for c in ("LW", "MCD") for f in ("F", "N", "FX")]
SELECT = [a for a in ARMS_L2 if not a.endswith("-FX")]
P0 = "R-LW-F"
SIMPLE = {"F": 0, "N": 1, "LW": 0, "MCD": 1, "R": 0, "B": 1}
RULE_SENS = -0.03                     # DESIGN §6: sensitivity - P0 point estimate >= -0.03
ML_F1, ML_SENS, SEG = 0.02, 0.03, (5, 10, 20, 30)
NEED_L2 = ["G-raw", "G-data", "G-stats1", "G-feat1", "R1.0-dev", "G-k", "G-chain", "G-split", "PROJ",
           "G-struct[dev]", "G-worker[build]"]
NEED_SEG = ["G-sel", "G-raw", "G-data", "R1.0-dev", "PROJ", "G-struct[seg]", "G-worker[build]"]
NEED_EVAL = ["G-sel", "G-raw", "G-data", "R1.0-test", "GE", "PROJ", "G-struct[test]", "G-struct[ext]", "G-worker[build]"]


def say(*a):
    print(*a, flush=True)


def metrics(R, keys):
    d = R.copy()
    d["sens"] = d.tp / d.n_ref.where(d.n_ref > 0)
    d["f1"] = 2 * d.tp / (2 * d.tp + d.fp + (d.n_ref - d.tp))
    d["fa"] = d.fp / d.nonict_h * 24
    return d.groupby(keys + ["subject"])[["sens", "f1", "fa", "tp", "n_ref", "fp"]].mean().reset_index()


def boot_pair(a, b, rng):
    s = a.index.intersection(b.index)
    d = (a[s] - b[s]).dropna()
    if len(d) < 2:
        return dict(diff=float(d.mean()) if len(d) else np.nan, ci_lo=np.nan, ci_hi=np.nan, subjects=int(len(d)))
    units = pd.Series([UNIT.get(x, x) for x in d.index], index=d.index)
    uids = units.unique()
    groups = [d[units == u].values for u in uids]
    idx = rng.integers(0, len(uids), size=(B, len(uids)))
    sums = np.array([g.sum() for g in groups])
    ns = np.array([len(g) for g in groups])
    bs = sums[idx].sum(axis=1) / ns[idx].sum(axis=1)
    return dict(diff=float(d.mean()), ci_lo=float(np.percentile(bs, 2.5)), ci_hi=float(np.percentile(bs, 97.5)),
                subjects=int(len(d)))


def gate_a0(run, need):
    gates = json.loads((Path(run) / "gates.json").read_text())
    bad = [g["gate"] for g in gates if g.get("status") != "PASS"]
    names = {g["gate"] for g in gates}
    bad += [f"missing {n}" for n in need if n not in names]
    return dict(gate=f"A0[{Path(run).name}]", status="PASS" if not bad else "FAIL", bad=bad)


def stop_unless(recs):
    for r in recs:
        say(f"{r['gate']}: {r['status']}" + ("" if r["status"] == "PASS" else f" {r}"))
    if any(r["status"] != "PASS" for r in recs):
        raise SystemExit("STOP: reader gate failed")


def level(P, keys):
    g = P.groupby(keys)
    return g.agg(sens=("sens", "mean"), f1=("f1", "mean"), fa=("fa", "mean"), patients=("subject", "nunique")).reset_index()


def seed_sd(R, keys):
    d = R.copy()
    d["sens"] = d.tp / d.n_ref.where(d.n_ref > 0)
    s = d.groupby(keys + ["seed"]).sens.mean().reset_index()
    return s.groupby(keys).sens.std(ddof=1).rename("sens_sd").reset_index()


def fmt_ci(r):
    return f"{r['diff']:+.3f} [{r['ci_lo']:+.3f}, {r['ci_hi']:+.3f}]" if np.isfinite(r["ci_lo"]) else f"{r['diff']:+.3f}"


def fmt_ci1(r):
    return f"{r['diff']:+.1f} [{r['ci_lo']:+.1f}, {r['ci_hi']:+.1f}]" if np.isfinite(r["ci_lo"]) else f"{r['diff']:+.1f}"


# ============================================================================ rules (DESIGN §6)
def select_arm(L, BT):
    """L: arm -> f1 (column); BT: bootstrap rows (arm, vs, metric, diff, ci_lo). Returns (chosen, candidates)."""
    f1 = L.set_index("arm").f1
    cand = []
    for a in SELECT:
        if a == P0 or a not in f1.index:
            continue
        r_f1 = BT[(BT.arm == a) & (BT.vs == P0) & (BT.metric == "f1")].iloc[0]
        r_s = BT[(BT.arm == a) & (BT.vs == P0) & (BT.metric == "sens")].iloc[0]
        if r_f1.ci_lo > 0 and r_s["diff"] >= RULE_SENS:
            cand.append(a)
    if not cand:
        return P0, cand
    best = max(round(float(f1[a]), 3) for a in cand)
    tied = [a for a in cand if round(float(f1[a]), 3) == best]
    tied.sort(key=lambda a: tuple(SIMPLE[x] for x in a.split("-")[::-1]))
    return tied[0], cand


def min_length(L, f1_full, s_full, segs):
    """L: seg_min, f1, sens. Smallest qualifying L, else 30."""
    ok = sorted(int(r.seg_min) for r in L.itertuples() if r.f1 >= f1_full - ML_F1 and r.sens >= s_full - ML_SENS)
    return (min(ok) if ok else 30), ok


# ============================================================================ L2
def references_dev():
    out = {}
    v5 = REPO / "results" / "p3c_freeze" / "per_subject.csv"
    d = pd.read_csv(v5)
    out["V5"] = d[d.subject.isin(DEV) & (d.budget == "L2f")].assign(arm="V5")
    lf = REPO / "results" / "eureka_d31f" / "9a" / "r13" / "lf" / "per_subject.csv"
    if lf.exists():
        d = pd.read_csv(lf)
        out["L0"] = d[d.subject.isin(DEV) & (d.budget == "L2f")].assign(arm="L0")
    return out


def read_l2(root):
    runs = [root / "l2_rec", root / "l2_rob"]
    recs = [gate_a0(r, NEED_L2) for r in runs]
    recs[1]["status"] = recs[1]["status"] if "G-c" in {g["gate"] for g in json.loads((runs[1] / "gates.json").read_text())} else "FAIL"
    R = pd.concat([pd.read_csv(r / "per_subject.csv") for r in runs], ignore_index=True).rename(columns={"budget": "arm"})
    cnt = R.groupby(["arm"]).size().to_dict()
    want = len(DEV) * len(TAGS) * len(STAGES)
    short = {a: cnt.get(a, 0) for a in ARMS_L2 if cnt.get(a, 0) != want}
    recs.append(dict(gate="A1", status="PASS" if not short else "FAIL", incomplete=short, rows_per_arm=want))
    stop_unless(recs)
    refs = references_dev()
    allr = pd.concat([R] + [v for v in refs.values()], ignore_index=True)
    P = metrics(allr[allr.stage == "cpd"], ["arm"])
    L = level(P, ["arm"]).merge(seed_sd(allr[allr.stage == "cpd"], ["arm"]), on="arm", how="left")
    rng = np.random.default_rng(RNG_SEED)
    bt = []
    for a in ARMS_L2:
        A_ = P[P.arm == a].set_index("subject")
        for ref in ["R-LW-F", "V5", "L0"]:
            if ref == a or ref not in set(P.arm):
                continue
            B_ = P[P.arm == ref].set_index("subject")
            for met in ("sens", "f1", "fa"):
                bt.append(dict(arm=a, vs=ref, metric=met, **boot_pair(A_[met], B_[met], rng)))
    BT = pd.DataFrame(bt)
    # ---- selection rule (DESIGN §6)
    f1 = L.set_index("arm").f1
    chosen, cand = select_arm(L, BT)
    S, cov, fl = chosen.split("-")
    k = json.loads((root / ("l2_rec" if S == "R" else "l2_rob") / "k.json").read_text())["k"][cov]
    sel = dict(arm=chosen, S=S, cov=cov, floor=fl, k=k, candidates=cand,
               dev_f1=float(f1[chosen]), dev_sens=float(L.set_index("arm").sens[chosen]),
               dev_fa=float(L.set_index("arm").fa[chosen]),
               rule="among arms with F1 - P0 interval above 0 and sensitivity - P0 >= -0.03, highest F1 "
                    "(3 decimals; ties -> F, LW, R); none -> P0 = R-LW-F",
               source_runs=[str(r.relative_to(REPO)) if REPO in r.parents else str(r) for r in runs])
    o = root / "l2"
    o.mkdir(parents=True, exist_ok=True)
    L.to_csv(o / "summary.csv", index=False)
    BT.to_csv(o / "bootstrap.csv", index=False)
    P.to_csv(o / "per_patient.csv", index=False)
    (o / "selection.json").write_text(json.dumps(sel, indent=1))
    # ---- descriptive: per arm, events per recording, recordings with no event, review share
    Fr = pd.concat([pd.read_csv(r / "per_file.csv") for r in runs], ignore_index=True)
    ev = Fr.groupby("budget").agg(files=("file", "size"), no_event=("events", lambda v: float((v == 0).mean())),
                                  events_per_rec=("events", "mean"), short=("short", "mean")).reset_index()
    ev.to_csv(o / "events.csv", index=False)
    lines = ["# T_L2 — the per-recording protocol on the 15 development patients", "",
             f"Reader `src/m2l_read.py --l2`; runs {', '.join(sel['source_runs'])}; every run gate PASS (A0), rows "
             f"complete (A1). Per-patient means after the change point localizer, 4 seeds; paired patient bootstrap "
             f"(chb01 + chb21 one unit). V5 = committed record rows (L2f); L0 = EUR_9A label-free patient-level "
             f"statistics (committed; another session, rebuild tolerance). Development includes the 12 training "
             f"patients.", "",
             "| arm | sensitivity ± seed SD | F1 | FP/day | Δ sens vs P0 | Δ F1 vs P0 | Δ FP/day vs P0 | Δ sens vs V5 | Δ sens vs L0 |",
             "|---|---|---|---|---|---|---|---|---|"]

    def bt_s(a, vs, met):
        r = BT[(BT.arm == a) & (BT.vs == vs) & (BT.metric == met)]
        return "—" if not len(r) else (fmt_ci1(r.iloc[0]) if met == "fa" else fmt_ci(r.iloc[0]))
    for a in ["V5", "L0"] + ARMS_L2:
        r = L[L.arm == a]
        if not len(r):
            continue
        r = r.iloc[0]
        sd = f" ± {r.sens_sd:.3f}" if np.isfinite(r.sens_sd) else ""
        lines.append(f"| {a} | {r.sens:.3f}{sd} | {r.f1:.3f} | {r.fa:.1f} | {bt_s(a, P0, 'sens')} | {bt_s(a, P0, 'f1')} | "
                     f"{bt_s(a, P0, 'fa')} | {bt_s(a, 'V5', 'sens')} | {bt_s(a, 'L0', 'sens')} |")
    lines += ["", "## Events per recording (cpd, all seeds)", "", "| arm | recordings × seeds | no event | events per recording | under the guard |",
              "|---|---|---|---|---|"]
    lines += [f"| {r.budget} | {r.files} | {r.no_event:.3f} | {r.events_per_rec:.2f} | {r.short:.3f} |" for r in ev.itertuples()]
    (o / "T_L2.md").write_text("\n".join(lines) + "\n")
    (o / "SELECTION.md").write_text(
        f"# Selection (DESIGN §6, applied by src/m2l_read.py)\n\nCandidates (F1 − P0 interval above 0 and sensitivity − P0 ≥ "
        f"−0.03): {cand or 'none'}.\n\n**Chosen arm: {chosen}** (S = {S}, covariance {cov}, budget {fl}; k = {k:.6f}); "
        f"development sensitivity {sel['dev_sens']:.3f}, F1 {sel['dev_f1']:.3f}, {sel['dev_fa']:.1f} FP/day.\n")
    say(f"L2 read: chosen {chosen} (candidates {cand}); outputs {o}")
    return sel


# ============================================================================ L3-short
def read_l3short(root):
    runs = [root / "l3short_a", root / "l3short_b"]
    recs = [gate_a0(r, NEED_SEG) for r in runs]
    sel = json.loads((root / "l2" / "selection.json").read_text())
    R = pd.concat([pd.read_csv(r / "per_subject.csv") for r in runs], ignore_index=True).rename(columns={"budget": "arm"})
    R = R[(R.arm == sel["arm"]) & (R.stage == "cpd")]
    have = sorted(R.seg_min.unique())
    cnt = R.groupby("seg_min").size()
    segs = [int(v) for v in os.environ.get("M2L_SEG_LIST", ",".join(map(str, SEG))).split(",")]
    short = {int(L): int(cnt.get(L, 0)) for L in segs if cnt.get(L, 0) != len(DEV) * len(TAGS)}
    recs.append(dict(gate="A1", status="PASS" if not short else "FAIL", incomplete=short, seg_min=[int(x) for x in have]))
    stop_unless(recs)
    P = metrics(R, ["seg_min"])
    L = level(P, ["seg_min"])
    f1_full, s_full = sel["dev_f1"], sel["dev_sens"]
    minutes, ok = min_length(L, f1_full, s_full, segs)
    ml = dict(minutes=minutes, windows=int(minutes * 60 // 4), qualifying=ok, f1_full=f1_full, sens_full=s_full,
              rule=f"smallest L in {segs} with F1_L >= F1_full - {ML_F1} and Sens_L >= Sens_full - {ML_SENS}; "
                   "none -> 30 min", arm=sel["arm"])
    o = root / "l3short"
    o.mkdir(parents=True, exist_ok=True)
    L.to_csv(o / "summary.csv", index=False)
    P.to_csv(o / "per_patient.csv", index=False)
    (o / "minlen.json").write_text(json.dumps(ml, indent=1))
    lines = ["# T_L3SHORT — the chosen arm on development segments", "",
             f"Arm {sel['arm']} (k {sel['k']:.6f}); whole recordings: sensitivity {s_full:.3f}, F1 {f1_full:.3f}. "
             f"Segments of L minutes cut from each development recording (cuts never split a seizure); descriptive.", "",
             "| L (min) | sensitivity | F1 | FP/day | qualifies |", "|---|---|---|---|---|"]
    lines += [f"| {int(r.seg_min)} | {r.sens:.3f} | {r.f1:.3f} | {r.fa:.1f} | {'yes' if int(r.seg_min) in ok else 'no'} |"
              for r in L.itertuples()]
    lines += ["", f"**Minimum recording length: {minutes} min** ({ml['rule']})."]
    (o / "T_L3SHORT.md").write_text("\n".join(lines) + "\n")
    say(f"L3-short read: minimum length {minutes} min (qualifying {ok}); outputs {o}")
    return ml


# ============================================================================ L3
def references_eval(run):
    out = []
    e = pd.read_csv(run / "r10" / "test_e23_rows.csv")
    e = e[(e.point == "balanced") & (e.stage == "localized")].assign(set="test", arm="V5", stage="cpd")
    out.append(e)
    x = pd.read_csv(run / "r10" / "ext_x1_rows.csv")
    x = x[(x.point == "balanced") & (x.stage == "localized")].copy()
    x["set"] = np.where(x.subject == "chb24", "chb24", "siena")
    out.append(x.assign(arm="V5", stage="cpd"))
    lf = REPO / "results" / "eureka_d31f" / "9a" / "r13" / "lf" / "per_subject.csv"
    if lf.exists():
        d = pd.read_csv(lf)
        out.append(d[d.subject.isin(TEST) & (d.budget == "L2f") & (d.stage == "cpd")].assign(set="test", arm="L0"))
    return pd.concat(out, ignore_index=True)


def read_l3(root):
    run = root / "l3eval"
    sel = json.loads((root / "l2" / "selection.json").read_text())
    ml = json.loads((root / "l3short" / "minlen.json").read_text())
    recs = [gate_a0(run, NEED_EVAL)]
    R = pd.read_csv(run / "per_subject.csv").rename(columns={"budget": "arm"})
    fx = f"{sel['S']}-{sel['cov']}-FX"
    cnt = R.groupby("arm").size()
    n_sub = R.subject.nunique()
    short = {a: int(cnt.get(a, 0)) for a in (sel["arm"], fx) if cnt.get(a, 0) != n_sub * len(TAGS) * len(STAGES)}
    want_sub = set(TEST) | set(pd.read_csv(run / "r10" / "ext_x1_rows.csv").subject)
    recs.append(dict(gate="A1", status="PASS" if not short and set(R.subject) == want_sub else "FAIL", incomplete=short,
                     subjects=int(n_sub), subjects_expected=len(want_sub)))
    stop_unless(recs)
    Rr = R[R.stage == "cpd"].copy()
    Rr["arm"] = Rr.arm.map({sel["arm"]: "L3", fx: "L3-FX"})
    allr = pd.concat([Rr, references_eval(run)], ignore_index=True)
    P = metrics(allr, ["set", "arm"])
    L = level(P, ["set", "arm"]).merge(seed_sd(allr, ["set", "arm"]), on=["set", "arm"], how="left")
    rng = np.random.default_rng(RNG_SEED)
    bt = []
    for st in ("test", "chb24", "siena"):
        for a, ref in (("L3", "V5"), ("L3", "L0"), ("L3-FX", "V5")):
            A_ = P[(P.set == st) & (P.arm == a)].set_index("subject")
            B_ = P[(P.set == st) & (P.arm == ref)].set_index("subject")
            if not len(A_) or not len(B_):
                continue
            for met in ("sens", "f1", "fa"):
                bt.append(dict(set=st, arm=a, vs=ref, metric=met, **boot_pair(A_[met], B_[met], rng)))
    BT = pd.DataFrame(bt)
    Fr = pd.read_csv(run / "per_file.csv")
    Fr = Fr[Fr.budget == sel["arm"]]
    sh = Fr[Fr.seed == TAGS[0]].groupby("set").agg(recordings=("file", "size"), short=("short", "sum"),
                                                   seizures_in_short=("n_ref", lambda v: int(v[Fr.loc[v.index, "short"]].sum())),
                                                   no_event=("events", lambda v: float((v == 0).mean()))).reset_index()
    o = root / "l3"
    o.mkdir(parents=True, exist_ok=True)
    L.to_csv(o / "summary.csv", index=False)
    BT.to_csv(o / "bootstrap.csv", index=False)
    P.to_csv(o / "per_patient.csv", index=False)
    sh.to_csv(o / "short_recordings.csv", index=False)

    def b(st, a, vs, met):
        r = BT[(BT.set == st) & (BT.arm == a) & (BT.vs == vs) & (BT.metric == met)]
        return "—" if not len(r) else (fmt_ci1(r.iloc[0]) if met == "fa" else fmt_ci(r.iloc[0]))
    lines = ["# T_L3 — SzScan 1.0 baseline: the per-recording protocol scored once", "",
             f"Arm {sel['arm']} (k {sel['k']:.6f}), minimum recording length {ml['minutes']} min; V5 checkpoints, 4 seeds; "
             f"per-patient means after the localizer; paired patient bootstrap. V5 = the record rows reproduced in the "
             f"same session (test: e23; chb24 / Siena: V0 from the rebuilt external features). L0 (test) = EUR_9A "
             f"label-free patient-level statistics. Test is descriptive (it entered earlier decisions); Siena is the "
             f"external set.", "",
             "| set | system | sensitivity ± seed SD | F1 | FP/day | Δ sens vs V5 | Δ F1 vs V5 | Δ FP/day vs V5 | Δ sens vs L0 |",
             "|---|---|---|---|---|---|---|---|---|"]
    for st in ("test", "chb24", "siena"):
        for a in ("V5", "L0", "L3", "L3-FX"):
            r = L[(L.set == st) & (L.arm == a)]
            if not len(r):
                continue
            r = r.iloc[0]
            sd = f" ± {r.sens_sd:.3f}" if np.isfinite(r.sens_sd) else ""
            lines.append(f"| {st} | {a} | {r.sens:.3f}{sd} | {r.f1:.3f} | {r.fa:.1f} | {b(st, a, 'V5', 'sens')} | "
                         f"{b(st, a, 'V5', 'f1')} | {b(st, a, 'V5', 'fa')} | {b(st, a, 'L0', 'sens')} |")
    lines += ["", "## Recordings under the minimum length (seed 42 rows)", "",
              "| set | recordings | under the minimum | seizures in them | recordings with no event |", "|---|---|---|---|---|"]
    lines += [f"| {r.set} | {r.recordings} | {int(r.short)} | {r.seizures_in_short} | {r.no_event:.3f} |" for r in sh.itertuples()]
    (o / "T_L3.md").write_text("\n".join(lines) + "\n")
    say(f"L3 read: outputs {o}")


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--l2", action="store_true")
    g.add_argument("--l3short", action="store_true")
    g.add_argument("--l3", action="store_true")
    ap.add_argument("--root", default=str(REPO / "results" / "m2l"))
    a = ap.parse_args()
    root = Path(a.root)
    if a.l2:
        read_l2(root)
    elif a.l3short:
        read_l3short(root)
    else:
        read_l3(root)


if __name__ == "__main__":
    main()
