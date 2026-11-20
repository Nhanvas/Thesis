#!/usr/bin/env python
"""
r4_f5a_aggregate.py -- F5a reading tables (Track F, chat D36-F; design results/r4_f5a/DESIGN_F5A.md, approved
21/11/2026 02:37). Written and committed BEFORE the F5A_V5 run output exists. Container only, no model.

Inputs: the F5A_V5 run (results/r4_f5a/v5: gates.json, events.csv, seizures.csv, series.csv.gz), the committed V5
record of the EUR suite (results/eureka_d31f/abl: per_subject.csv, errors.csv, variant V0) and the x1 record
(results/x1_external/errors_*.csv, Table 10's external rows).
Gates (STOP unless PASS): A0 every run gate PASS and the required gates present; A1 completeness (every case x seed x
arm has its pairs; every pair's seizure has a segment); A2 the run's six signed errors = abl/errors.csv V0, exactly,
pair by pair (development, test; chb24 / Siena from the same rebuilt features); A3 localizer (e18.cpd_event) and run-rule
(e18.run_event) boundaries recomputed from the stored series = the run's, exactly, every pair.
Tables (results/r4_f5a/aggregate/): V1 detection (detector, localizer, hybrid; paired differences), V2 boundaries
(medians, signed, IQR, shares; paired differences of median |error|), D1 bias per patient, D2 strata, D3 profiles
(return, rise, fall times; median curves), D4 end position, D5 interventions (3 change points; margin 30), H table, figures.
Statistics: patient bootstrap, B = 10,000, rng 0, chb01 + chb21 one resampling unit; no pass / fail threshold.
  python src/r4_f5a_aggregate.py [--run results/r4_f5a/v5] [--abl results/eureka_d31f/abl] [--out DIR] [--b 10000]
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

TAGS = ["clean_seed42", "clean_seed1", "clean_seed2", "clean_seed3"]
SEEDS = {t: t.split("seed")[1] for t in TAGS}
WIN, MARGIN = 4, 15
UNIT = {"chb21": "chb01"}
READ = [("development", "own"), ("test", "fixed"), ("test", "own"), ("chb24", "own"), ("siena", "own")]
SET_LABEL = {("development", "own"): "development", ("test", "fixed"): "test held-out", ("test", "own"): "test final",
             ("chb24", "own"): "chb24", ("siena", "own"): "Siena"}
STAGE_COLS = {"detector": ("det_on", "det_off"), "localizer": ("cpd_on", "cpd_off"), "hybrid": ("hyb_on", "hyb_off")}
PRE = (-300, -60)                         # pre-onset reference, seconds
CENSOR = 180
KRET = (3, 2, 5)
MF = ("ll", "d", "t", "a", "b", "g", "pow")
B = 10_000
RNG = 0


def log(*a):
    print(*a, flush=True)


def fail(name, msg):
    raise SystemExit(f"STOP {name}: {msg}")


# ============================================================================ bootstrap
def units_of(subjects):
    return np.array([UNIT.get(s, s) for s in subjects])


def boot_stat(df, fn, b=B, seed=RNG):
    """df with column 'subject'; fn(df) -> float. Units resampled with replacement, their rows pooled."""
    df = df.reset_index(drop=True)
    if not len(df):
        return np.nan, np.nan, np.nan
    u = units_of(df.subject)
    uids = np.unique(u)
    groups = [np.flatnonzero(u == x) for x in uids]
    rng = np.random.default_rng(seed)
    est = fn(df)
    if len(uids) < 2:
        return est, np.nan, np.nan
    draws = rng.integers(0, len(uids), size=(b, len(uids)))
    vals = np.empty(b)
    for i in range(b):
        idx = np.concatenate([groups[j] for j in draws[i]])
        vals[i] = fn(df.iloc[idx])
    vals = vals[np.isfinite(vals)]
    if not len(vals):
        return est, np.nan, np.nan
    return est, float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def boot_mean_by_subject(a, b_, b=B, seed=RNG):
    """a, b_: Series by subject (4-seed means). Paired mean difference; units resampled (chb01 + chb21 together)."""
    s = a.index.intersection(b_.index)
    d = (a[s] - b_[s]).dropna()
    if len(d) < 2:
        return float(d.mean()) if len(d) else np.nan, np.nan, np.nan
    u = units_of(d.index)
    uids = np.unique(u)
    sums = np.array([d.values[u == x].sum() for x in uids]); ns = np.array([(u == x).sum() for x in uids])
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(uids), size=(b, len(uids)))
    bs = sums[idx].sum(1) / ns[idx].sum(1)
    return float(d.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def within_spearman(df, xc, yc):
    """Spearman correlation of x and y after centring both on each patient's median."""
    from scipy.stats import spearmanr
    d = df[["subject", xc, yc]].dropna()
    if len(d) < 4:
        return np.nan
    xm = d[xc] - d.groupby("subject")[xc].transform("median")
    ym = d[yc] - d.groupby("subject")[yc].transform("median")
    if xm.nunique() < 2 or ym.nunique() < 2:
        return np.nan
    return float(spearmanr(xm, ym).statistic)


def fmt(e, lo, hi, nd=1):
    if not np.isfinite(e):
        return "n/a"
    f = f"{{:+.{nd}f}}" if nd >= 0 else "{:+.0f}"
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return f.format(e)
    return f"{f.format(e)} [{f.format(lo)}, {f.format(hi)}]"


# ============================================================================ loading and gates
def load(run, abl):
    run, abl = Path(run), Path(abl)
    gates = json.loads((run / "gates.json").read_text())
    E = pd.read_csv(run / "events.csv")
    S = pd.read_csv(run / "seizures.csv")
    X = pd.read_csv(run / "series.csv.gz")
    R = pd.read_csv(abl / "per_subject.csv")
    A = pd.read_csv(abl / "errors.csv")
    for d in (R, A):
        d.drop(d.index[d.variant != "V0"], inplace=True)
        d["set"] = np.where(d["set"] != "external", d["set"], np.where(d.subject == "chb24", "chb24", "siena"))
        d.rename(columns={"budget": "arm"}, inplace=True)
    return gates, E, S, X, R, A


def gate_a0(gates):
    bad = [g["gate"] for g in gates if g.get("status") != "PASS"]
    names = {g["gate"] for g in gates}
    for need in ("G-self", "G-data", "SMOKE", "R1.0-dev", "R1.0-test", "GE", "G-k", "G-eng[full]", "G-seg[full]",
                 "G-mf[full]", "G-worker-sha[full]"):
        if need not in names:
            bad.append(f"missing {need}")
    return dict(gate="A0", status="PASS" if not bad else "FAIL", bad=bad)


def gate_a1(E, S, A):
    bad = []
    keys = ["set", "subject", "seed", "arm"]
    want = A.groupby(keys).size()
    got = E.groupby(keys).size()
    for k, v in want.items():
        if got.get(k, 0) != v:
            bad.append(f"{k}: {got.get(k, 0)} pairs vs {v}")
    for k in set(got.index) - set(want.index):
        bad.append(f"{k}: unexpected")
    m = E.merge(S[["subject", "file", "ref_on", "sz"]], on=["subject", "file", "ref_on"], how="left")
    if m.sz.isna().any():
        bad.append(f"{int(m.sz.isna().sum())} pairs without a segment")
    return dict(gate="A1", status="PASS" if not bad else "FAIL", bad=bad[:20], pairs=int(len(E)), seizures=int(len(S)))


def gate_a2(E, A):
    cols = ["det_on", "det_off", "cpd_on", "cpd_off", "hyb_on", "hyb_off"]
    keys = ["set", "subject", "seed", "arm"]
    bad = []
    for k, g in A.groupby(keys):
        e = E.set_index(keys).loc[[k]] if k in set(map(tuple, E[keys].values)) else None
        if e is None or len(e) != len(g) or not np.array_equal(e[cols].values.astype(int), g[cols].values.astype(int)):
            bad.append(str(k))
    return dict(gate="A2", status="PASS" if not bad else "FAIL", bad=bad[:20], groups=int(A.groupby(keys).ngroups))


def file_arrays(X, S, ev, seed):
    """full-length file arrays (x, ok) from the stored segment of the pair's seizure; NaN / False outside it."""
    s = S[(S.subject == ev.subject) & (S.file == ev.file) & (S.ref_on == ev.ref_on)].iloc[0]
    seg = X[X.sz == s.sz]
    n = int(ev.n_file)
    x = np.full(n, np.nan); ok = np.zeros(n, bool)
    x[seg.w.values] = seg[f"x{seed}"].values
    ok[seg.w.values] = seg.ok.values.astype(bool)
    return x, ok


def gate_a3(E, S, X):
    bad = []
    for ev in E.itertuples():
        x, ok = file_arrays(X, S, ev, SEEDS[ev.seed])
        aw, bw = ev.det_a // WIN, ev.det_b // WIN
        ca, cb, used = E18.cpd_event(x, ok, aw, bw, MARGIN)
        ua, ub = E18.run_event(x, ok, aw, bw, MARGIN, ev.thr)
        if (ca * WIN, cb * WIN, bool(used)) != (ev.cpd_a, ev.cpd_b, bool(ev.used_cpd)) or (ua * WIN, ub * WIN) != (ev.run_a, ev.run_b):
            bad.append(f"{ev.subject} {ev.seed} {ev.arm} {ev.file} {ev.ref_on}")
    return dict(gate="A3", status="PASS" if not bad else "FAIL", bad=bad[:20], pairs=int(len(E)))


# ============================================================================ V: verification from the record
def v1_detection(R, b):
    R = R.copy()
    R["sens"] = R.tp / R.n_ref.where(R.n_ref > 0)
    R["f1"] = 2 * R.tp / (2 * R.tp + R.fp + (R.n_ref - R.tp))
    R["fa"] = R.fp / R.nonict_h * 24
    P = R.groupby(["set", "arm", "stage", "subject"])[["sens", "f1", "fa", "tp", "fp"]].mean().reset_index()
    out = []
    for st, arm in READ:
        g = P[(P.set == st) & (P.arm == arm)]
        if not len(g):
            continue
        row = dict(set=SET_LABEL[(st, arm)])
        for stage in ("detector", "cpd", "hybrid"):
            q = g[g.stage == stage]
            row.update({f"{stage}_sens": q.sens.mean(), f"{stage}_f1": q.f1.mean(), f"{stage}_fa": q.fa.mean()})
        for a_, b_, name in (("cpd", "detector", "loc-det"), ("hybrid", "cpd", "hyb-loc")):
            A_ = g[g.stage == a_].set_index("subject"); B_ = g[g.stage == b_].set_index("subject")
            for met in ("sens", "f1", "fa"):
                e, lo, hi = boot_mean_by_subject(A_[met], B_[met], b=b)
                row[f"{name}_{met}"] = e; row[f"{name}_{met}_lo"] = lo; row[f"{name}_{met}_hi"] = hi
            row[f"{name}_dtp_per_seed"] = float((A_.tp - B_.tp).sum())
            row[f"{name}_dfp_per_seed"] = float((A_.fp - B_.fp).sum())
        out.append(row)
    return pd.DataFrame(out)


def med_abs(col):
    return lambda d: float(d[col].abs().median()) if len(d) else np.nan


def diff_med_abs(c1, c2):
    return lambda d: float(d[c1].abs().median() - d[c2].abs().median()) if len(d) else np.nan


def v2_boundaries(A, b):
    out = []
    for st, arm in READ:
        g = A[(A.set == st) & (A.arm == arm)]
        if not len(g):
            continue
        row = dict(set=SET_LABEL[(st, arm)], pairs=int(len(g)), patients=int(g.subject.nunique()))
        for stage, (on, off) in STAGE_COLS.items():
            for side, c in (("on", on), ("off", off)):
                v = g[c]
                row[f"{stage}_{side}_abs"] = float(v.abs().median())
                row[f"{stage}_{side}_signed"] = float(v.median())
                row[f"{stage}_{side}_q1"] = float(v.quantile(.25)); row[f"{stage}_{side}_q3"] = float(v.quantile(.75))
                row[f"{stage}_{side}_late"] = float((v > 0).mean()); row[f"{stage}_{side}_early"] = float((v < 0).mean())
        for name, (a1, a2) in (("loc-det_on", ("cpd_on", "det_on")), ("loc-det_off", ("cpd_off", "det_off")),
                               ("hyb-loc_on", ("hyb_on", "cpd_on")), ("hyb-loc_off", ("hyb_off", "cpd_off"))):
            e, lo, hi = boot_stat(g, diff_med_abs(a1, a2), b=b)
            row[name] = e; row[f"{name}_lo"] = lo; row[f"{name}_hi"] = hi
        for c in ("cpd_off", "det_off"):
            e, lo, hi = boot_stat(g, lambda d, c=c: float(d[c].median()), b=b)
            row[f"{c}_signed_lo"], row[f"{c}_signed_hi"] = lo, hi
        out.append(row)
    return pd.DataFrame(out)


def x1_check():
    d = ROOT / "results" / "x1_external"
    fs = [p for p in sorted(d.glob("errors_*.csv")) if p.stat().st_size > 2]
    if not fs:
        return pd.DataFrame()
    X = pd.concat([pd.read_csv(p) for p in fs], ignore_index=True)
    X = X[X.point == "balanced"]
    rows = []
    for s, g in X.groupby("set"):
        rows.append(dict(set=s, pairs=len(g), **{c: float(g[c].abs().median()) for c in
                                                 ("det_on", "det_off", "cpd_on", "cpd_off", "hyb_on", "hyb_off")}))
    return pd.DataFrame(rows)


# ============================================================================ D3: profiles
def seizure_table(S):
    """exclusions: span [on - 300, off + 180] outside the file, or overlapping another seizure's [on, off + 180]."""
    S = S.copy()
    S["span_out"] = (S.ref_on + PRE[0] < 0) | (S.ref_off + CENSOR > S.n_file * WIN)
    ov = []
    for r in S.itertuples():
        o = S[(S.subject == r.subject) & (S.file == r.file) & (S.ref_on != r.ref_on)]
        ov.append(bool(((o.ref_on < r.ref_off + CENSOR) & (o.ref_off + CENSOR > r.ref_on + PRE[0])).any()))
    S["overlap"] = ov
    S["valid"] = ~S.span_out & ~S.overlap
    return S


def first_return(t, inside, t0, horizon, k):
    """first window start t >= t0 from which `inside` holds for k consecutive windows (4-s grid); seconds after t0,
    or NaN if none starts within the horizon."""
    for i in np.flatnonzero(t >= t0):
        if t[i] - t0 > horizon:
            break
        if i + k <= len(t) and inside[i:i + k].all() and np.all(np.diff(t[i:i + k]) == WIN):
            return float(t[i] - t0)
    return np.nan


def profile_one(t, v, ok, on, off, k):
    """t: window start times (s, in file), v values, ok valid. Returns pre-onset stats, return time (band = the pre-onset
    5th-95th percentiles), its null value (the same rule started at the beginning of the pre-onset reference), rise and
    fall times."""
    out = dict(pre_ok=False)
    pre = (t >= on + PRE[0]) & (t < on + PRE[1]) & ok & np.isfinite(v)
    if pre.sum() < 30:
        return out
    p05, med, p95 = np.percentile(v[pre], [5, 50, 95])
    out.update(pre_ok=True, pre_med=med, pre_p05=p05, pre_p95=p95)
    inside = ok & np.isfinite(v) & (v >= p05) & (v <= p95)
    ret = first_return(t, inside, off, CENSOR, k)
    out["ret"] = CENSOR if not np.isfinite(ret) else ret
    out["ret_cens"] = not np.isfinite(ret)
    nul = first_return(t, inside, on + PRE[0], PRE[1] - PRE[0] - k * WIN, k)
    out["ret_null"] = nul
    # rise and fall
    sz = (t >= on) & (t < off) & ok & np.isfinite(v)
    if not sz.any():
        return out
    p = float(np.max(v[sz]))
    if p <= med:
        out["peak_le_base"] = True
        return out
    l10, l90 = med + 0.1 * (p - med), med + 0.9 * (p - med)
    good = ok & np.isfinite(v)
    i90 = np.flatnonzero((t >= on - 60) & (t <= off) & good & (v >= l90))
    if len(i90):
        j = i90[0]
        back = np.flatnonzero((t < t[j]) & (t >= on - 120) & good & (v <= l10))
        out["rise"] = float(t[j] - (t[back[-1]] if len(back) else on - 120))
        out["rise_cens"] = not len(back)
    i90b = np.flatnonzero((t >= on) & (t <= off + 60) & good & (v >= l90))
    if len(i90b):
        j = i90b[-1]
        fwd = np.flatnonzero((t > t[j]) & (t <= off + CENSOR) & good & (v <= l10))
        out["fall"] = float((t[fwd[0]] if len(fwd) else off + CENSOR) - t[j])
        out["fall_cens"] = not len(fwd)
    return out


def d3_profiles(S, X):
    rows, curves = [], []
    rel = np.arange(-120, CENSOR + 1, WIN)
    for s in S.itertuples():
        seg = X[X.sz == s.sz].sort_values("w")
        t = seg.w.values * WIN
        ok = seg.ok.values.astype(bool)
        series = {f"x{SEEDS[g]}": seg[f"x{SEEDS[g]}"].values for g in TAGS}
        series.update({f"m{SEEDS[g]}": seg[f"m{SEEDS[g]}"].values for g in TAGS})
        series.update({f"mf_{k}": seg[f"mf_{k}"].values for k in MF})
        for name, v in series.items():
            for k in KRET:
                pr = profile_one(t, v, ok, s.ref_on, s.ref_off, k)
                rows.append(dict(set=s.set, subject=s.subject, sz=s.sz, ref_dur=s.ref_off - s.ref_on, valid=s.valid,
                                 matched=s.matched, series=name, k=k, **pr))
            if not s.valid:
                continue
            pre = (t >= s.ref_on + PRE[0]) & (t < s.ref_on + PRE[1]) & ok & np.isfinite(v)
            if pre.sum() < 30:
                continue
            med = np.median(v[pre])
            for anchor, a0 in (("offset", s.ref_off), ("onset", s.ref_on)):
                vv = pd.Series(np.where(ok, v - med, np.nan), index=t)
                c = vv.reindex(a0 + rel).values
                curves.append(pd.DataFrame(dict(set=s.set, subject=s.subject, sz=s.sz, series=name, anchor=anchor,
                                                rel=rel, value=c)))
    P = pd.DataFrame(rows)
    C = pd.concat(curves, ignore_index=True) if curves else pd.DataFrame()
    return P, C


def series_group(name):
    if name.startswith("x"):
        return "x"
    if name.startswith("m") and not name.startswith("mf_"):
        return "m"
    return name


# ============================================================================ D4, D5
def cpd_k(x, ok, a_w, b_w, margin, n_bkps):
    """e18.cpd_event's preparation with n_bkps change points (diagnostic D5a); returns the change points in file
    windows (or None if the segment is too short / the fit fails)."""
    import ruptures as rpt
    s0, s1 = max(0, a_w - margin), min(len(x), b_w + margin)
    seg = x[s0:s1].astype(float).copy()
    good = ok[s0:s1] & np.isfinite(seg)
    if good.sum() < 6 or len(seg) < 6:
        return None
    seg[~good] = np.median(seg[good])
    try:
        bk = rpt.KernelCPD(kernel="rbf", min_size=2).fit(seg.reshape(-1, 1)).predict(n_bkps=n_bkps)
    except Exception:                    # noqa: BLE001
        return None
    return [s0 + b for b in bk[:-1]]


def d4_d5(E, S, X, P):
    rets = P[(P.series.str.match(r"^x\d+$")) & (P.k == 3)][["sz", "series", "ret", "ret_cens", "fall"]].copy()
    rets["seed"] = "clean_seed" + rets.series.str[1:]
    sz_of = S.set_index(["subject", "file", "ref_on"]).sz
    rows = []
    for ev in E.itertuples():
        sz = sz_of.loc[(ev.subject, ev.file, ev.ref_on)]
        r = rets[(rets.sz == sz) & (rets.seed == ev.seed)]
        ret = float(r.ret.iloc[0]) if len(r) and np.isfinite(r.ret.iloc[0]) else np.nan
        fall = float(r.fall.iloc[0]) if len(r) and np.isfinite(r.fall.iloc[0]) else np.nan
        row = dict(set=ev.set, subject=ev.subject, seed=ev.seed, arm=ev.arm, sz=sz, used_cpd=ev.used_cpd,
                   cpd_off=ev.cpd_off, det_off=ev.det_off, hyb_off=ev.hyb_off, cpd_on=ev.cpd_on, ret=ret,
                   ret_cens=bool(r.ret_cens.iloc[0]) if len(r) else np.nan, fall=fall,
                   edge=bool(ev.cpd_b >= ev.win_b - 2 * WIN) if ev.used_cpd else np.nan,
                   ev_long=ev.ev_dur > 300, merged=ev.n_runs >= 2, multi_ref=ev.n_refs >= 2, ref_dur=ev.ref_dur)
        if np.isfinite(ret):
            row["d_ret"] = ev.cpd_b - (ev.ref_off + ret)
            row["nearer_ret"] = abs(row["d_ret"]) < abs(ev.cpd_off)
        x, ok = file_arrays(X, S, ev, SEEDS[ev.seed])
        aw, bw = ev.det_a // WIN, ev.det_b // WIN
        k3 = cpd_k(x, ok, aw, bw, MARGIN, 3)
        if k3 is not None:
            row["k3_b1_on"], row["k3_b2_off"], row["k3_b3_off"] = (k3[0] * WIN - ev.ref_on, k3[1] * WIN - ev.ref_off,
                                                                   k3[2] * WIN - ev.ref_off)
            if np.isfinite(ret):
                tr = ev.ref_off + ret
                row["k3_b3_nearer_ret"] = abs(k3[2] * WIN - tr) < abs(k3[1] * WIN - tr)
        ca, cb, used = E18.cpd_event(x, ok, aw, bw, 2 * MARGIN)
        row["m30_used"] = bool(used)
        row["m30_off"] = (cb * WIN - ev.ref_off) if used else ev.det_off
        rows.append(row)
    return pd.DataFrame(rows)


# ============================================================================ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=str(ROOT / "results" / "r4_f5a" / "v5"))
    ap.add_argument("--abl", default=str(ROOT / "results" / "eureka_d31f" / "abl"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--b", type=int, default=B)
    a = ap.parse_args()
    b = a.b
    out = Path(a.out or Path(a.run).parent / "aggregate")
    out.mkdir(parents=True, exist_ok=True)
    gates, E, S, X, R, A = load(a.run, a.abl)
    G = [gate_a0(gates), gate_a1(E, S, A), gate_a2(E, A), gate_a3(E, S, X)]
    (out / "gates.json").write_text(json.dumps(G, indent=1, default=str), encoding="utf-8")
    for g in G:
        log(f"{g['gate']} {g['status']}" + ("" if g["status"] == "PASS" else f": {g}"))
        if g["status"] != "PASS":
            fail(g["gate"], g)
    # ---- V
    V1 = v1_detection(R, b); V1.to_csv(out / "V1_detection.csv", index=False)
    V2 = v2_boundaries(A, b); V2.to_csv(out / "V2_boundaries.csv", index=False)
    XC = x1_check(); XC.to_csv(out / "V3_x1_record.csv", index=False)
    # ---- D1 per patient
    D1 = []
    for (st, arm), g in E.groupby(["set", "arm"]):
        if (st, arm) not in SET_LABEL:
            continue
        for s, h in g.groupby("subject"):
            D1.append(dict(set=SET_LABEL[(st, arm)], subject=s, pairs=len(h),
                           **{f"{c}_signed": float(h[c].median()) for c in ("det_on", "cpd_on", "det_off", "cpd_off",
                                                                             "hyb_off")},
                           **{f"{c}_abs": float(h[c].abs().median()) for c in ("det_off", "cpd_off", "hyb_off")}))
    D1 = pd.DataFrame(D1); D1.to_csv(out / "D1_per_patient.csv", index=False)
    # ---- D3
    S = seizure_table(S)
    P, C = d3_profiles(S, X)
    P.to_csv(out / "D3_seizure_profiles.csv", index=False)
    C.to_csv(out / "D3_curves_long.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    P["group"] = P.series.map(series_group)
    # ---- D4 / D5 / D2 per pair
    Q = d4_d5(E, S, X, P)
    Q.to_csv(out / "D4_D5_pairs.csv", index=False)
    # ---- summary tables per read set
    lines = ["# F5a on V5 — reading tables (aggregate written before the run; design results/r4_f5a/DESIGN_F5A.md)\n",
             f"Gates: {', '.join(g['gate'] + ' ' + g['status'] for g in G)}. Patient bootstrap B = {b}, rng 0, chb01 + "
             "chb21 one unit. Values in seconds unless stated; [95 % interval].\n"]
    lines += ["## V1 · Detection (per-patient means; paired differences)\n",
              "| set | detector sens / F1 / FP/day | localizer | hybrid | localizer − detector Δsens | ΔFP/day | hybrid − localizer Δsens | ΔF1 | ΔFP/day | seizures Δ (loc−det, hyb−loc; per seed) |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in V1.iterrows():
        lines.append(f"| {r['set']} | {r.detector_sens:.3f} / {r.detector_f1:.3f} / {r.detector_fa:.1f} | "
                     f"{r.cpd_sens:.3f} / {r.cpd_f1:.3f} / {r.cpd_fa:.1f} | {r.hybrid_sens:.3f} / {r.hybrid_f1:.3f} / "
                     f"{r.hybrid_fa:.1f} | {fmt(r['loc-det_sens'], r['loc-det_sens_lo'], r['loc-det_sens_hi'], 3)} | "
                     f"{fmt(r['loc-det_fa'], r['loc-det_fa_lo'], r['loc-det_fa_hi'])} | "
                     f"{fmt(r['hyb-loc_sens'], r['hyb-loc_sens_lo'], r['hyb-loc_sens_hi'], 3)} | "
                     f"{fmt(r['hyb-loc_f1'], r['hyb-loc_f1_lo'], r['hyb-loc_f1_hi'], 3)} | "
                     f"{fmt(r['hyb-loc_fa'], r['hyb-loc_fa_lo'], r['hyb-loc_fa_hi'])} | "
                     f"{r['loc-det_dtp_per_seed'] / 4:+.2f}, {r['hyb-loc_dtp_per_seed'] / 4:+.2f} |")
    lines += ["\n## V2 · Boundaries (matched pairs; median |error|, signed median, share late)\n",
              "| set | pairs | onset det / loc / hyb | offset det / loc / hyb | offset signed det / loc / hyb | offset late det / loc / hyb | loc − det \\|onset\\| | loc − det \\|offset\\| | hyb − loc \\|offset\\| |",
              "|---|---|---|---|---|---|---|---|---|"]
    for _, r in V2.iterrows():
        lines.append(f"| {r['set']} | {r.pairs} | {r.detector_on_abs:.0f} / {r.localizer_on_abs:.0f} / {r.hybrid_on_abs:.0f} | "
                     f"{r.detector_off_abs:.0f} / {r.localizer_off_abs:.0f} / {r.hybrid_off_abs:.0f} | "
                     f"{r.detector_off_signed:+.0f} / {r.localizer_off_signed:+.0f} / {r.hybrid_off_signed:+.0f} | "
                     f"{r.detector_off_late:.2f} / {r.localizer_off_late:.2f} / {r.hybrid_off_late:.2f} | "
                     f"{fmt(r['loc-det_on'], r['loc-det_on_lo'], r['loc-det_on_hi'], 0)} | "
                     f"{fmt(r['loc-det_off'], r['loc-det_off_lo'], r['loc-det_off_hi'], 0)} | "
                     f"{fmt(r['hyb-loc_off'], r['hyb-loc_off_lo'], r['hyb-loc_off_hi'], 0)} |")
    if len(XC):
        lines += ["\nx1 record (Table 10, external): " + "; ".join(
            f"{r['set']} {r.pairs} pairs, offset det {r.det_off:.0f} / loc {r.cpd_off:.0f} / hyb {r.hyb_off:.0f}"
            for _, r in XC.iterrows())]
    # ---- D3 / D4 / D5 / H per read set
    H = []
    lines += ["\n## D3 · Post-ictal profile (every valid annotated seizure; return time k = 3, censored at 180 s)\n",
              "| set | seizures valid / all | series | return time median | null (same rule in the pre-onset background) | return − null | share censored | fall − rise |",
              "|---|---|---|---|---|---|---|---|"]
    sets_d3 = [("development", "development"), ("test", "test"), ("chb24", "chb24"), ("siena", "Siena")]
    for st, lab in sets_d3:
        p = P[(P.set == st) & P.valid & (P.k == 3) & P.pre_ok.fillna(False).astype(bool)]
        n_all = int(S[S.set == st].shape[0]); n_val = int(S[(S.set == st) & S.valid].shape[0])
        for grp in ("x", "x caught", "m", "ll", "d", "pow"):
            gname = grp.split()[0] if grp.split()[0] in ("x", "m") else f"mf_{grp}"
            q = p[p.group == gname]
            if grp == "x caught":
                q = q[q.matched.astype(bool)]
            if not len(q):
                continue
            q2 = q.groupby(["subject", "sz"])[["ret", "ret_null", "rise", "fall"]].mean().reset_index()   # seeds averaged
            e, lo, hi = boot_stat(q2, lambda d: float(d.ret.median()), b=b)
            qn = q2.dropna(subset=["ret_null"])
            en = boot_stat(qn, lambda d: float(d.ret_null.median()), b=b)
            ed = boot_stat(qn, lambda d: float((d.ret - d.ret_null).median()), b=b)
            H.append(dict(set=lab, item=f"return-null {grp}", est=ed[0], lo=ed[1], hi=ed[2]))
            cens = float(q.ret_cens.astype(float).mean())
            fr = ""
            if grp in ("x", "x caught", "ll"):
                q3 = q2.dropna(subset=["rise", "fall"])
                e2, lo2, hi2 = boot_stat(q3, lambda d: float((d.fall - d.rise).median()), b=b)
                fr = fmt(e2, lo2, hi2, 0)
                H.append(dict(set=lab, item=f"fall-rise {grp}", est=e2, lo=lo2, hi=hi2))
            lines.append(f"| {lab} | {n_val} / {n_all} | {grp} | {fmt(e, lo, hi, 0)} | {fmt(*en, 0)} | {fmt(*ed, 0)} | "
                         f"{cens:.2f} | {fr} |")
            H.append(dict(set=lab, item=f"return {grp}", est=e, lo=lo, hi=hi))
    # return-time agreement x vs model-free line length / delta power (within patient, seeds averaged for x)
    lines += ["\n| set | within-patient ρ(return x, return line length) | ρ(return x, return δ power) |", "|---|---|---|"]
    for st, lab in sets_d3:
        p = P[(P.set == st) & P.valid & (P.k == 3) & P.pre_ok.fillna(False).astype(bool)]
        rx = p[p.group == "x"].groupby(["subject", "sz"]).ret.mean().rename("rx")
        cells = []
        for grp in ("mf_ll", "mf_d"):
            rm = p[p.group == grp].groupby(["subject", "sz"]).ret.mean().rename("rm")
            j = pd.concat([rx, rm], axis=1).dropna().reset_index()
            e = boot_stat(j, lambda d: within_spearman(d, "rx", "rm"), b=b)
            cells.append(fmt(*e, 2))
            H.append(dict(set=lab, item=f"rho return x-{grp}", est=e[0], lo=e[1], hi=e[2]))
        lines.append(f"| {lab} | {cells[0]} | {cells[1]} |")
    lines += ["\n## D4 · Where the localizer puts the offset (matched pairs, localizer accepted)\n",
              "| set | pairs | signed offset error | end − return point | share nearer return point | within-patient ρ(error, return) | ρ(error, fall) | edge share |",
              "|---|---|---|---|---|---|---|---|"]
    for st, arm in READ:
        q = Q[(Q.set == st) & (Q.arm == arm) & (Q.used_cpd)]
        if not len(q):
            continue
        lab = SET_LABEL[(st, arm)]
        e1 = boot_stat(q, lambda d: float(d.cpd_off.median()), b=b)
        qq = q.dropna(subset=["d_ret"])
        e2 = boot_stat(qq, lambda d: float(d.d_ret.median()), b=b)
        e3 = boot_stat(qq, lambda d: float(d.nearer_ret.astype(float).mean()), b=b)
        e4 = boot_stat(qq, lambda d: within_spearman(d, "cpd_off", "ret"), b=b)
        e5 = boot_stat(q.dropna(subset=["fall"]), lambda d: within_spearman(d, "cpd_off", "fall"), b=b)
        e6 = boot_stat(q, lambda d: float(d.edge.astype(float).mean()), b=b)
        lines.append(f"| {lab} | {len(q)} | {fmt(*e1, 0)} | {fmt(*e2, 0)} | {fmt(*e3, 2)} | {fmt(*e4, 2)} | "
                     f"{fmt(*e5, 2)} | {fmt(*e6, 2)} |")
        for nm, e in (("signed offset", e1), ("end-return", e2), ("nearer return", e3), ("rho error-return", e4),
                      ("rho error-fall", e5), ("edge", e6)):
            H.append(dict(set=lab, item=nm, est=e[0], lo=e[1], hi=e[2]))
    lines += ["\n## D5 · Diagnostic interventions (same pairs; not a localizer rule)\n",
              "| set | \\|offset\\| record (2 cp, m15) | 3 cp: 2nd point \\|offset\\| | Δ (2nd − record) | 3rd point nearer return | m30 \\|offset\\| | Δ signed (m30 − record) |",
              "|---|---|---|---|---|---|---|"]
    for st, arm in READ:
        q = Q[(Q.set == st) & (Q.arm == arm) & (Q.used_cpd)].dropna(subset=["k3_b2_off"])
        if not len(q):
            continue
        lab = SET_LABEL[(st, arm)]
        e1 = boot_stat(q, lambda d: float(d.k3_b2_off.abs().median() - d.cpd_off.abs().median()), b=b)
        qq = q.dropna(subset=["k3_b3_nearer_ret"])
        e2 = boot_stat(qq, lambda d: float(d.k3_b3_nearer_ret.astype(float).mean()), b=b)
        e3 = boot_stat(q, lambda d: float(d.m30_off.median() - d.cpd_off.median()), b=b)
        lines.append(f"| {lab} | {q.cpd_off.abs().median():.0f} | {q.k3_b2_off.abs().median():.0f} | {fmt(*e1, 0)} | "
                     f"{fmt(*e2, 2)} | {q.m30_off.abs().median():.0f} | {fmt(*e3, 0)} |")
        for nm, e in (("k3 2nd-record |off|", e1), ("k3 3rd nearer return", e2), ("m30-record signed", e3)):
            H.append(dict(set=lab, item=nm, est=e[0], lo=e[1], hi=e[2]))
    lines += ["\n## D2 · Strata (localizer − detector median |offset| in the remaining pairs without the stratum)\n",
              "| set | all | − fallback | − event > 300 s | − merged runs | − ≥ 2 references | − reference < 20 s | − reference > 300 s |",
              "|---|---|---|---|---|---|---|---|"]
    strata = dict(fallback=lambda d: ~d.used_cpd.astype(bool), long=lambda d: d.ev_long.astype(bool),
                  merged=lambda d: d.merged.astype(bool), multi=lambda d: d.multi_ref.astype(bool),
                  short=lambda d: d.ref_dur < 20, vlong=lambda d: d.ref_dur > 300)
    D2 = []
    for st, arm in READ:
        q = Q[(Q.set == st) & (Q.arm == arm)]
        if not len(q):
            continue
        lab = SET_LABEL[(st, arm)]
        cells = [fmt(*boot_stat(q, diff_med_abs("cpd_off", "det_off"), b=b), 0)]
        for nm, fn in strata.items():
            m = fn(q)
            D2.append(dict(set=lab, stratum=nm, n=int(m.sum()), cpd_abs=float(q[m].cpd_off.abs().median()) if m.any() else np.nan,
                           det_abs=float(q[m].det_off.abs().median()) if m.any() else np.nan,
                           cpd_signed=float(q[m].cpd_off.median()) if m.any() else np.nan))
            rest = q[~m]
            cells.append(f"{fmt(*boot_stat(rest, diff_med_abs('cpd_off', 'det_off'), b=b), 0)} (n−{int(m.sum())})")
        lines.append(f"| {lab} | " + " | ".join(cells) + " |")
    pd.DataFrame(D2).to_csv(out / "D2_strata.csv", index=False)
    lines += ["\n## H7 · Pair-weighted vs patient-weighted (localizer − detector median |offset|)\n",
              "| set | pair-weighted | patient-weighted (median of patient medians) | share of pairs in the 2 largest patients |",
              "|---|---|---|---|"]
    for st, arm in READ:
        q = Q[(Q.set == st) & (Q.arm == arm)]
        if not len(q):
            continue
        lab = SET_LABEL[(st, arm)]
        pw = float(q.cpd_off.abs().median() - q.det_off.abs().median())
        pm = q.groupby("subject").apply(lambda d: d.cpd_off.abs().median() - d.det_off.abs().median(),
                                        include_groups=False)
        top2 = float(q.subject.value_counts().iloc[:2].sum() / len(q))
        lines.append(f"| {lab} | {pw:+.0f} | {float(pm.median()):+.0f} | {top2:.2f} |")
        H.append(dict(set=lab, item="patient-weighted loc-det |off|", est=float(pm.median()), lo=np.nan, hi=np.nan))
    pd.DataFrame(H).to_csv(out / "H_items.csv", index=False)
    # ---- curves table and figure
    if len(C):
        C["group"] = C.series.map(series_group)
        cm = C.groupby(["set", "group", "anchor", "rel"]).value.median().reset_index()
        cm.to_csv(out / "D3_median_curves.csv", index=False)
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(2, 4, figsize=(14, 6), sharex=True)
            for j, (st, lab) in enumerate(sets_d3):
                for i, grp in enumerate(("x", "mf_ll")):
                    for anchor, col in (("onset", "tab:blue"), ("offset", "tab:red")):
                        d = cm[(cm.set == st) & (cm.group == grp) & (cm.anchor == anchor)]
                        ax[i, j].plot(d.rel, d.value, color=col, label=f"around {anchor}")
                    ax[i, j].axvline(0, color="k", lw=0.8)
                    ax[i, j].axhline(0, color="0.6", lw=0.6)
                    ax[i, j].set_title(f"{lab}: {'score x' if grp == 'x' else 'line length (model-free)'}", fontsize=9)
            ax[1, 0].set_xlabel("seconds from the annotated boundary")
            ax[0, 0].legend(fontsize=8)
            fig.tight_layout()
            fig.savefig(out / "fig_d3_profiles.png", dpi=130)
            plt.close(fig)
        except Exception as e:           # noqa: BLE001
            log(f"figure skipped: {e}")
    (out / "T_F5A.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    log("\n".join(lines))
    log("AGGREGATE DONE")


if __name__ == "__main__":
    main()
