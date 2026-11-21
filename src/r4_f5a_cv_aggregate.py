#!/usr/bin/env python
"""
r4_f5a_cv_aggregate.py -- F5a Part B reading tables (Track F, chat D36-F; design results/r4_f5a/DESIGN_F5A.md §10,
approved 21/11/2026 12:43). Written and committed BEFORE the F5A_CV output exists. Container only, no model.

Input: the F5A_CV run (results/r4_f5a/cv). The helpers of src/r4_f5a_aggregate.py (bootstrap, profiles, 3-change-point
fit, within-patient correlation) are imported unchanged. The 6 partitions play the role of V5's 4 seeds: every case is
scored once per partition (out of fold); the patient bootstrap resamples patients (B = 10,000, rng 0, chb01 + chb21 one
unit) and pools their pairs / seizures over partitions.
Gates (STOP unless PASS): A0 every run gate PASS and the required gates present; A1 completeness (48 jobs; every model x
partition has the 24 cases x 2 arms x 3 stages; every pair's seizure has a segment); A3 localizer (e18.cpd_event) and
run-rule (e18.run_event) boundaries recomputed from the stored series = the run's, exactly, every pair.
Tables (results/r4_f5a/cv_aggregate/): per model — V1 detection, V2 boundaries (pooled and per partition), D3 (return -
null, fall - rise, level after the offset relative to the seizure level), D4, D5; model-free D3 (once); HB1 / HB2 /
HB3 items; GAE - MLP-AE paired by patient; figures.
  python src/r4_f5a_cv_aggregate.py [--run results/r4_f5a/cv] [--out DIR] [--b 10000]
"""
import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(os.environ.get("THESIS_REPO", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "src"))
import e18_cpd_localizer as E18          # noqa: E402  (record functions, read only)
import r4_f5a_aggregate as AG            # noqa: E402  (Part A helpers, unchanged)

WIN, MARGIN = 4, 15
MODELS = ("gae", "mlp")
PARTS = (0, 1, 2, 3, 4, 5)
MF = AG.MF
B = 10_000


def log(*a):
    print(*a, flush=True)


def gate_a0(gates):
    bad = [g["gate"] for g in gates if g.get("status") not in ("PASS", "n/a")]
    names = {g["gate"] for g in gates}
    for need in ("G-data", "D0'", "SMOKE", "G-k[full]", "G-rows[full]", "G-eng[full]", "G-seg[full]", "G-worker-sha[full]"):
        if need not in names:
            bad.append(f"missing {need}")
    return dict(gate="A0", status="PASS" if not bad else "FAIL", bad=bad)


def gate_a1(J, R, E, S):
    bad = []
    if len(J) != len(MODELS) * len(PARTS) * 4:
        bad.append(f"{len(J)} jobs")
    for (m, p), g in R.groupby(["model", "partition"]):
        if g.subject.nunique() != 24 or len(g) != 24 * 2 * 3:
            bad.append(f"{m} p{p}: {g.subject.nunique()} cases, {len(g)} rows")
    if R.groupby(["model", "partition"]).ngroups != len(MODELS) * len(PARTS):
        bad.append("model x partition missing")
    k = ["model", "partition", "subject", "file", "ref_on"]
    mg = E.merge(S[k + ["sz"]], on=k, how="left")
    if mg.sz.isna().any():
        bad.append(f"{int(mg.sz.isna().sum())} pairs without a segment")
    return dict(gate="A1", status="PASS" if not bad else "FAIL", bad=bad[:20], pairs=int(len(E)))


def seg_index(X):
    return {key: g.sort_values("w") for key, g in X.groupby(["model", "partition", "sz"])}


def arrays(SI, S, ev):
    s = S[(S.model == ev.model) & (S.partition == ev.partition) & (S.subject == ev.subject) & (S.file == ev.file)
          & (S.ref_on == ev.ref_on)].iloc[0]
    seg = SI[(ev.model, ev.partition, s.sz)]
    n = int(ev.n_file)
    x = np.full(n, np.nan); ok = np.zeros(n, bool)
    x[seg.w.values] = seg.x.values
    ok[seg.w.values] = seg.ok.values.astype(bool)
    return x, ok, s.sz


def gate_a3(E, S, SI):
    bad = []
    for ev in E.itertuples():
        x, ok, _ = arrays(SI, S, ev)
        aw, bw = ev.det_a // WIN, ev.det_b // WIN
        ca, cb, used = E18.cpd_event(x, ok, aw, bw, MARGIN)
        ua, ub = E18.run_event(x, ok, aw, bw, MARGIN, ev.thr)
        if (ca * WIN, cb * WIN, bool(used)) != (ev.cpd_a, ev.cpd_b, bool(ev.used_cpd)) or (ua * WIN, ub * WIN) != (ev.run_a, ev.run_b):
            bad.append(f"{ev.model} p{ev.partition} {ev.subject} {ev.file} {ev.ref_on}")
    return dict(gate="A3", status="PASS" if not bad else "FAIL", bad=bad[:20], pairs=int(len(E)))


def levels(t, v, ok, on, off):
    """level of the series after the offset relative to the pre-onset median: median over [off, off + 60 s) and over
    the seizure [on, off), and their ratio (seizure level > 0 only)."""
    pre = (t >= on - 300) & (t < on - 60) & ok & np.isfinite(v)
    if pre.sum() < 30:
        return dict()
    med = np.median(v[pre])
    post = (t >= off) & (t < off + 60) & ok & np.isfinite(v)
    sz = (t >= on) & (t < off) & ok & np.isfinite(v)
    out = dict(post60=float(np.median(v[post] - med)) if post.any() else np.nan,
               szlev=float(np.median(v[sz] - med)) if sz.any() else np.nan)
    out["ratio"] = out["post60"] / out["szlev"] if np.isfinite(out["szlev"]) and out["szlev"] > 0 else np.nan
    return out


def d3(S, SI, MFX):
    Sv = AG.seizure_table(S.drop_duplicates(["model", "partition", "sz"]))
    rows, curves = [], []
    rel = np.arange(-120, AG.CENSOR + 1, WIN)
    for s in Sv.itertuples():
        seg = SI[(s.model, s.partition, s.sz)]
        t = seg.w.values * WIN; ok = seg.ok.values.astype(bool); v = seg.x.values
        pr = AG.profile_one(t, v, ok, s.ref_on, s.ref_off, 3)
        rows.append(dict(model=s.model, partition=s.partition, subject=s.subject, sz=s.sz, valid=s.valid,
                         matched=s.matched, series="x", **pr, **levels(t, v, ok, s.ref_on, s.ref_off)))
        if s.valid and pr.get("pre_ok"):
            vv = pd.Series(np.where(ok, v - pr["pre_med"], np.nan), index=t)
            for anchor, a0 in (("offset", s.ref_off), ("onset", s.ref_on)):
                curves.append(pd.DataFrame(dict(model=s.model, sz=s.sz, subject=s.subject, anchor=anchor, rel=rel,
                                                value=vv.reindex(a0 + rel).values)))
    mf_rows = []
    if MFX is not None and len(MFX):
        base = Sv.drop_duplicates("sz").set_index("sz")
        for sz, seg in MFX.groupby("sz"):
            if sz not in base.index:
                continue
            s = base.loc[sz]
            seg = seg.sort_values("w")
            t = seg.w.values * WIN; ok = seg.ok.values.astype(bool)
            for k in ("ll", "d", "pow"):
                pr = AG.profile_one(t, seg[f"mf_{k}"].values, ok, s.ref_on, s.ref_off, 3)
                mf_rows.append(dict(subject=s.subject, sz=sz, valid=bool(s.valid), series=f"mf_{k}", **pr))
    return pd.DataFrame(rows), (pd.concat(curves, ignore_index=True) if curves else pd.DataFrame()), pd.DataFrame(mf_rows)


def pairs_table(E, S, SI, P):
    rets = P.set_index(["model", "partition", "sz"])
    out = []
    for ev in E[E.arm == "own"].itertuples():
        x, ok, sz = arrays(SI, S, ev)
        r = rets.loc[(ev.model, ev.partition, sz)] if (ev.model, ev.partition, sz) in rets.index else None
        ret = float(r.ret) if r is not None and np.isfinite(r.get("ret", np.nan)) else np.nan
        fall = float(r.fall) if r is not None and "fall" in r and np.isfinite(r.fall) else np.nan
        row = dict(model=ev.model, partition=ev.partition, subject=ev.subject, sz=sz, used_cpd=ev.used_cpd,
                   cpd_off=ev.cpd_off, det_off=ev.det_off, cpd_on=ev.cpd_on, det_on=ev.det_on, hyb_off=ev.hyb_off,
                   ret=ret, fall=fall, edge=bool(ev.cpd_b >= ev.win_b - 2 * WIN) if ev.used_cpd else np.nan)
        if np.isfinite(ret):
            row["d_ret"] = ev.cpd_b - (ev.ref_off + ret)
            row["nearer_ret"] = abs(row["d_ret"]) < abs(ev.cpd_off)
        aw, bw = ev.det_a // WIN, ev.det_b // WIN
        k3 = AG.cpd_k(x, ok, aw, bw, MARGIN, 3)
        if k3 is not None:
            row["k3_b2_off"], row["k3_b3_off"] = k3[1] * WIN - ev.ref_off, k3[2] * WIN - ev.ref_off
            if np.isfinite(ret):
                tr = ev.ref_off + ret
                row["k3_b3_nearer_ret"] = abs(k3[2] * WIN - tr) < abs(k3[1] * WIN - tr)
        ca, cb, used = E18.cpd_event(x, ok, aw, bw, 2 * MARGIN)
        row["m30_off"] = (cb * WIN - ev.ref_off) if used else ev.det_off
        out.append(row)
    return pd.DataFrame(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=str(ROOT / "results" / "r4_f5a" / "cv"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--b", type=int, default=B)
    a = ap.parse_args()
    b = a.b
    run = Path(a.run)
    out = Path(a.out or run.parent / "cv_aggregate")
    out.mkdir(parents=True, exist_ok=True)
    gates = json.loads((run / "gates.json").read_text())
    J = pd.read_csv(run / "jobs.csv")
    R = pd.read_csv(run / "rows.csv")
    E = pd.read_csv(run / "events.csv")
    S = pd.read_csv(run / "seizures.csv")
    X = pd.read_csv(run / "series.csv.gz", float_precision="round_trip")
    MFX = pd.read_csv(run / "mf_series.csv.gz", float_precision="round_trip") if (run / "mf_series.csv.gz").exists() else None
    SI = seg_index(X)
    G = [gate_a0(gates), gate_a1(J, R, E, S), gate_a3(E, S, SI)]
    (out / "gates.json").write_text(json.dumps(G, indent=1, default=str), encoding="utf-8")
    for g in G:
        log(f"{g['gate']} {g['status']}" + ("" if g["status"] == "PASS" else f": {g}"))
        if g["status"] != "PASS":
            raise SystemExit(f"STOP {g['gate']}: {g}")
    H = []
    L = ["# F5a Part B — CV models (GAE, MLP-AE; partitions 0–5) — reading tables (aggregate written before the run)\n",
         f"Gates: {', '.join(g['gate'] + ' ' + g['status'] for g in G)}. 24 CHB-MIT cases out of fold, 6 partitions "
         f"(as seeds), patient bootstrap B = {b}, rng 0, chb01 + chb21 one unit. Seconds; [95 % interval].\n"]
    # ---- V1 detection
    R2 = R.copy()
    R2["sens"] = R2.tp / R2.n_ref.where(R2.n_ref > 0)
    R2["f1"] = 2 * R2.tp / (2 * R2.tp + R2.fp + (R2.n_ref - R2.tp))
    R2["fa"] = R2.fp / R2.nonict_h * 24
    Pm = R2.groupby(["model", "arm", "stage", "subject"])[["sens", "f1", "fa", "tp", "fp"]].mean().reset_index()
    L += ["## V1 · Detection (per-patient means over partitions)\n",
          "| model | arm | detector sens / F1 / FP/day | localizer | hybrid | loc − det Δsens | ΔFP/day | hyb − loc Δsens | ΔFP/day |",
          "|---|---|---|---|---|---|---|---|---|"]
    V1 = []
    for m in MODELS:
        for arm in ("own", "fixed"):
            g = Pm[(Pm.model == m) & (Pm.arm == arm)]
            st = {s: g[g.stage == s].set_index("subject") for s in ("detector", "cpd", "hybrid")}
            d1 = [AG.boot_mean_by_subject(st["cpd"][c], st["detector"][c], b=b) for c in ("sens", "fa")]
            d2 = [AG.boot_mean_by_subject(st["hybrid"][c], st["cpd"][c], b=b) for c in ("sens", "fa")]
            L.append(f"| {m} | {arm} | " + " | ".join(f"{st[s].sens.mean():.3f} / {st[s].f1.mean():.3f} / {st[s].fa.mean():.1f}"
                                                     for s in ("detector", "cpd", "hybrid"))
                     + f" | {AG.fmt(*d1[0], 3)} | {AG.fmt(*d1[1])} | {AG.fmt(*d2[0], 3)} | {AG.fmt(*d2[1])} |")
            V1.append(dict(model=m, arm=arm, **{f"{s}_{c}": st[s][c].mean() for s in st for c in ("sens", "f1", "fa")}))
    pd.DataFrame(V1).to_csv(out / "V1_detection.csv", index=False)
    # ---- V2 boundaries (pooled) + per partition
    L += ["\n## V2 · Boundaries (matched pairs pooled over partitions)\n",
          "| model | arm | pairs | onset det / loc / hyb | offset det / loc / hyb | offset signed det / loc / hyb | loc − det \\|onset\\| | loc − det \\|offset\\| | hyb − loc \\|offset\\| | localizer offset signed |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    V2 = []
    for m in MODELS:
        for arm in ("own", "fixed"):
            g = E[(E.model == m) & (E.arm == arm)]
            c1 = AG.boot_stat(g, AG.diff_med_abs("cpd_on", "det_on"), b=b)
            c2 = AG.boot_stat(g, AG.diff_med_abs("cpd_off", "det_off"), b=b)
            c3 = AG.boot_stat(g, AG.diff_med_abs("hyb_off", "cpd_off"), b=b)
            c4 = AG.boot_stat(g, lambda d: float(d.cpd_off.median()), b=b)
            L.append(f"| {m} | {arm} | {len(g)} | {g.det_on.abs().median():.0f} / {g.cpd_on.abs().median():.0f} / "
                     f"{g.hyb_on.abs().median():.0f} | {g.det_off.abs().median():.0f} / {g.cpd_off.abs().median():.0f} / "
                     f"{g.hyb_off.abs().median():.0f} | {g.det_off.median():+.0f} / {g.cpd_off.median():+.0f} / "
                     f"{g.hyb_off.median():+.0f} | {AG.fmt(*c1, 0)} | {AG.fmt(*c2, 0)} | {AG.fmt(*c3, 0)} | {AG.fmt(*c4, 0)} |")
            V2.append(dict(model=m, arm=arm, pairs=len(g), loc_det_on=c1, loc_det_off=c2, hyb_loc_off=c3, loc_off_signed=c4))
            if arm == "own":
                H += [dict(model=m, item="loc-det |onset|", est=c1[0], lo=c1[1], hi=c1[2]),
                      dict(model=m, item="loc-det |offset|", est=c2[0], lo=c2[1], hi=c2[2]),
                      dict(model=m, item="localizer offset signed", est=c4[0], lo=c4[1], hi=c4[2])]
    pd.DataFrame(V2).to_csv(out / "V2_boundaries.csv", index=False)
    L += ["\n**Per partition (own arm):** localizer signed offset median / localizer − detector median |offset| / "
          "localizer − detector median |onset|\n", "| model | " + " | ".join(f"p{p}" for p in PARTS) +
          " | partitions with signed offset > 0 |", "|---|" + "---|" * (len(PARTS) + 1)]
    PP = []
    for m in MODELS:
        cells, npos = [], 0
        for p in PARTS:
            g = E[(E.model == m) & (E.arm == "own") & (E.partition == p)]
            so = float(g.cpd_off.median())
            dd = float(g.cpd_off.abs().median() - g.det_off.abs().median())
            do = float(g.cpd_on.abs().median() - g.det_on.abs().median())
            npos += int(so > 0)
            cells.append(f"{so:+.0f} / {dd:+.0f} / {do:+.0f}")
            PP.append(dict(model=m, partition=p, pairs=len(g), loc_off_signed=so, loc_det_off=dd, loc_det_on=do))
        L.append(f"| {m} | " + " | ".join(cells) + f" | {npos} / {len(PARTS)} |")
        H.append(dict(model=m, item="partitions with signed offset > 0", est=npos, lo=np.nan, hi=np.nan))
    pd.DataFrame(PP).to_csv(out / "V2_per_partition.csv", index=False)
    # ---- D3
    P, C, MFP = d3(S, SI, MFX)
    P.to_csv(out / "D3_seizure_profiles.csv", index=False)
    MFP.to_csv(out / "D3_mf_profiles.csv", index=False)
    L += ["\n## D3 · Post-ictal profile of the score x (every valid seizure; partitions averaged per seizure)\n",
          "| model | seizures | return − null | fall − rise | level 0–60 s after offset | level / seizure level |",
          "|---|---|---|---|---|---|"]
    PS_ = {}
    for m in MODELS:
        q = P[(P.model == m) & P.valid & P.pre_ok.fillna(False).astype(bool)]
        q2 = q.groupby(["subject", "sz"])[["ret", "ret_null", "rise", "fall", "post60", "ratio"]].mean().reset_index()
        PS_[m] = q2
        c1 = AG.boot_stat(q2.dropna(subset=["ret_null"]), lambda d: float((d.ret - d.ret_null).median()), b=b)
        c2 = AG.boot_stat(q2.dropna(subset=["rise", "fall"]), lambda d: float((d.fall - d.rise).median()), b=b)
        c3 = AG.boot_stat(q2.dropna(subset=["post60"]), lambda d: float(d.post60.median()), b=b)
        c4 = AG.boot_stat(q2.dropna(subset=["ratio"]), lambda d: float(d.ratio.median()), b=b)
        L.append(f"| {m} | {len(q2)} | {AG.fmt(*c1, 0)} | {AG.fmt(*c2, 0)} | {AG.fmt(*c3, 3)} | {AG.fmt(*c4, 2)} |")
        H += [dict(model=m, item="return-null x", est=c1[0], lo=c1[1], hi=c1[2]),
              dict(model=m, item="fall-rise x", est=c2[0], lo=c2[1], hi=c2[2]),
              dict(model=m, item="post60 level", est=c3[0], lo=c3[1], hi=c3[2]),
              dict(model=m, item="post60 / seizure level", est=c4[0], lo=c4[1], hi=c4[2])]
    if len(MFP):
        L += ["\nModel-free (the EEG features, once per seizure): " + "; ".join(
            f"{k}: return − null {AG.fmt(*AG.boot_stat(MFP[(MFP.series == k) & MFP.valid].dropna(subset=['ret_null']), lambda d: float((d.ret - d.ret_null).median()), b=b), 0)}"
            for k in ("mf_ll", "mf_d", "mf_pow"))]
    # ---- D4 / D5
    Q = pairs_table(E, S, SI, P)
    Q.to_csv(out / "D4_D5_pairs.csv", index=False)
    L += ["\n## D4 · Where the localizer puts the offset (own arm, localizer accepted)\n",
          "| model | pairs | end − return point | share nearer return point | within-patient ρ(error, return) | ρ(error, fall) | edge share |",
          "|---|---|---|---|---|---|---|"]
    for m in MODELS:
        q = Q[(Q.model == m) & Q.used_cpd.astype(bool)]
        qq = q.dropna(subset=["d_ret"])
        c = [AG.boot_stat(qq, lambda d: float(d.d_ret.median()), b=b),
             AG.boot_stat(qq, lambda d: float(d.nearer_ret.astype(float).mean()), b=b),
             AG.boot_stat(qq, lambda d: AG.within_spearman(d, "cpd_off", "ret"), b=b),
             AG.boot_stat(q.dropna(subset=["fall"]), lambda d: AG.within_spearman(d, "cpd_off", "fall"), b=b),
             AG.boot_stat(q, lambda d: float(d.edge.astype(float).mean()), b=b)]
        L.append(f"| {m} | {len(q)} | {AG.fmt(*c[0], 0)} | {AG.fmt(*c[1], 2)} | {AG.fmt(*c[2], 2)} | {AG.fmt(*c[3], 2)} | "
                 f"{AG.fmt(*c[4], 2)} |")
        for nm, e in zip(("end-return", "nearer return", "rho error-return", "rho error-fall", "edge"), c):
            H.append(dict(model=m, item=nm, est=e[0], lo=e[1], hi=e[2]))
    L += ["\n## D5 · Diagnostic interventions (own arm, localizer accepted; not a localizer rule)\n",
          "| model | \\|offset\\| record | 3 cp 2nd point Δ \\|offset\\| | 3rd point nearer return | m30 Δ signed |", "|---|---|---|---|---|"]
    for m in MODELS:
        q = Q[(Q.model == m) & Q.used_cpd.astype(bool)].dropna(subset=["k3_b2_off"])
        c1 = AG.boot_stat(q, lambda d: float(d.k3_b2_off.abs().median() - d.cpd_off.abs().median()), b=b)
        c2 = AG.boot_stat(q.dropna(subset=["k3_b3_nearer_ret"]), lambda d: float(d.k3_b3_nearer_ret.astype(float).mean()), b=b)
        c3 = AG.boot_stat(q, lambda d: float(d.m30_off.median() - d.cpd_off.median()), b=b)
        L.append(f"| {m} | {q.cpd_off.abs().median():.0f} | {AG.fmt(*c1, 0)} | {AG.fmt(*c2, 2)} | {AG.fmt(*c3, 0)} |")
        H += [dict(model=m, item="k3 2nd-record |off|", est=c1[0], lo=c1[1], hi=c1[2]),
              dict(model=m, item="m30-record signed", est=c3[0], lo=c3[1], hi=c3[2])]
    # ---- HB2: GAE - MLP-AE paired by patient
    L += ["\n## HB2 · GAE − MLP-AE, paired by patient (own arm)\n", "| quantity | GAE | MLP-AE | GAE − MLP-AE |",
          "|---|---|---|---|"]
    eo = E[E.arm == "own"]
    per_pat = {
        "localizer signed offset (patient median)": {m: eo[eo.model == m].groupby("subject").cpd_off.median() for m in MODELS},
        "loc − det |offset| (patient)": {m: eo[eo.model == m].groupby("subject").apply(
            lambda d: d.cpd_off.abs().median() - d.det_off.abs().median(), include_groups=False) for m in MODELS},
        "return − null x (patient mean)": {m: PS_[m].assign(dd=PS_[m].ret - PS_[m].ret_null).groupby("subject").dd.mean()
                                           for m in MODELS},
        "level 0–60 s after offset (patient mean)": {m: PS_[m].groupby("subject").post60.mean() for m in MODELS},
        "level / seizure level (patient mean)": {m: PS_[m].groupby("subject").ratio.mean() for m in MODELS},
    }
    for nm, d in per_pat.items():
        e = AG.boot_mean_by_subject(d["gae"], d["mlp"], b=b)
        L.append(f"| {nm} | {d['gae'].mean():+.3f} | {d['mlp'].mean():+.3f} | {AG.fmt(*e, 3)} |")
        H.append(dict(model="gae-mlp", item=nm, est=e[0], lo=e[1], hi=e[2]))
    pd.DataFrame(H).to_csv(out / "H_items.csv", index=False)
    # ---- curves + figure
    if len(C):
        cm = C.groupby(["model", "anchor", "rel"]).value.median().reset_index()
        cm.to_csv(out / "D3_median_curves.csv", index=False)
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
            for j, anchor in enumerate(("onset", "offset")):
                for m, col in (("gae", "tab:red"), ("mlp", "tab:blue")):
                    d = cm[(cm.model == m) & (cm.anchor == anchor)]
                    ax[j].plot(d.rel, d.value, color=col, label="GAE" if m == "gae" else "MLP-AE")
                ax[j].axvline(0, color="k", lw=0.8); ax[j].axhline(0, color="0.6", lw=0.6)
                ax[j].set_title(f"score x around the annotated {anchor} (median, 24 cases, 6 partitions)", fontsize=9)
                ax[j].set_xlabel("seconds")
            ax[0].legend(fontsize=8)
            fig.tight_layout(); fig.savefig(out / "fig_cv_profiles.png", dpi=130); plt.close(fig)
        except Exception as e:           # noqa: BLE001
            log(f"figure skipped: {e}")
    (out / "T_F5A_CV.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    log("\n".join(L))
    log("AGGREGATE DONE")


if __name__ == "__main__":
    main()
