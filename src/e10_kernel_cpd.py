#!/usr/bin/env python
"""
e10_kernel_cpd.py -- detection stage designed for the two gaps named in the registration form
("threshold calibration and baseline drifts") with the method the form names (Objective 2:
"non-parametric change point detection on the ensemble anomaly score time series").

Measured motivation (non-test data and E9 counts):
  * D1 thresholds the GLOBAL level of the score (patient's top-p quantile). Long elevated
    states (sleep, sustained artefact) occupy that tail, so a seizure must be globally extreme.
  * SzCORE splits events longer than 5 min, so long elevated plateaus become several FPs
    (E9: SzCORE FP count exceeded the number of D1 events).
Design (fixed before any number of this script was read):
  K  per file, KernelCPD (ruptures, rbf kernel = non-parametric, min_size 2 windows = 8 s) on the
     UNSMOOTHED ensemble score; penalty c in {2, 4, 8}. For every segment k: mean m_k, duration d_k,
     prominence r_k = m_k - max(m_{k-1}, m_{k+1}) (one neighbour at file edges).
     A segment is a candidate when r_k > 0 (it rises above BOTH neighbours: an onset AND an offset
     change point) and d_k <= 300 s (a priori: SzCORE's maximum event length; seizures longer than
     5 min are status epilepticus). Alarm = candidate whose prominence is in the patient's own top
     p of all CANDIDATE prominences (label-free), p in {1, 2, 5, 10, 20} %. Event = the segment.
  D1 reference = the E8-frozen cell (smooth 15, top 2 %) and its top-p grid.
  D1c (mechanism check) = D1 with events longer than 300 s removed.
Score = GAE v2 clean V2_LW (the E8-adopted score), seeds 42 and 1 (E8 cache), seed-mean per cell.
GATE (event level, 15 non-test subjects, full recordings):
  K adopted if  best seed-mean sensitivity at FA/day <= 25  >=  D1 + 0.10,
                validation-only (chb10, chb11, chb22) >= D1's, and
                K's TP >= D1's TP in at least 9 of the subjects that have seizures.
TEST GUARD: non-test subjects only. Writes only results/e10_kernel_cpd/.
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import ruptures as rpt
from sklearn.covariance import LedoitWolf

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain"):
    sys.path.insert(0, str(p))
import e8_gae_v2_eval as E8      # noqa: E402
import ensemble_recipe as ER     # noqa: E402
import szcore_eval as SE         # noqa: E402

OUT = ROOT / "results" / "e10_kernel_cpd"
OUT.mkdir(parents=True, exist_ok=True)
WIN, MAXDUR, MERGE = 4, 300, 90
PENS, PS = [2.0, 4.0, 8.0], [0.01, 0.02, 0.05, 0.10, 0.20]
TOPS = [0.05, 0.02, 0.01, 0.005, 0.002, 0.001]
TAGS = ["clean_seed42", "clean_seed1"]


def rz(x, ok):
    m = np.median(x[ok]); s = np.median(np.abs(x[ok] - m)) + 1e-9; return (x - m) / s


def merge(ev):
    out = []
    for a, b in sorted(ev):
        if out and a - out[-1][1] <= MERGE:
            out[-1] = (out[-1][0], max(b, out[-1][1]))
        else:
            out.append((a, b))
    return out


def runs(mask):
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            out.append((i, j)); i = j
        else:
            i += 1
    return out


def score_events(z, per_file):
    ok = ~z["is_signal_loss"].astype(bool); ict = z["is_ictal"].astype(bool); fidx = z["file_idx"].astype(int)
    ref, hyp, off, durs = [], [], 0, []
    for f in np.unique(fidx):
        m = np.flatnonzero(fidx == f)
        ref += [(a * WIN + off, b * WIN + off) for a, b in runs(ict[m])]
        ev = per_file.get(f, [])
        hyp += [(a + off, b + off) for a, b in ev]; durs += [b - a for a, b in ev]
        off += len(m) * WIN + 600
    h = float((~ict & ok).sum()) * WIN / 3600
    r = SE.score_szcore(ref, hyp, off, h)
    return int(r["tp"]), int(r["fp"]), int(r["n_ref"]), h, durs


def d1_events(z, sc, top, cap=None):
    ok = ~z["is_signal_loss"].astype(bool); fidx = z["file_idx"].astype(int)
    sm = np.full(len(sc), np.nan)
    for f in np.unique(fidx):
        m = fidx == f
        sm[m] = pd.Series(np.where(ok[m], sc[m], np.nan)).rolling(15, min_periods=1, center=True).mean().values
    thr = np.nanquantile(sm[ok], 1 - top)
    ev = {}
    for f in np.unique(fidx):
        m = np.flatnonzero(fidx == f)
        e = merge([(a * WIN, b * WIN) for a, b in runs(np.nan_to_num(sm[m], nan=-np.inf) > thr)])
        ev[f] = [x for x in e if cap is None or x[1] - x[0] <= cap]
    return ev


def k_segments(z, sc, pen):
    ok = ~z["is_signal_loss"].astype(bool); fidx = z["file_idx"].astype(int)
    segs = {}
    for f in np.unique(fidx):
        m = np.flatnonzero(fidx == f)
        x = sc[m].copy(); x[~ok[m]] = np.median(x[ok[m]]) if ok[m].any() else 0.0
        if len(x) < 6:
            segs[f] = []; continue
        bk = rpt.KernelCPD(kernel="rbf", min_size=2).fit(x.reshape(-1, 1)).predict(pen=pen)
        st = [0] + bk[:-1]
        mu = [float(x[a:b].mean()) for a, b in zip(st, bk)]
        out = []
        for k, (a, b) in enumerate(zip(st, bk)):
            nb = [mu[j] for j in (k - 1, k + 1) if 0 <= j < len(mu)]
            prom = mu[k] - max(nb) if nb else 0.0
            out.append((a, b, prom))
        segs[f] = out
    return segs


def main():
    t0 = time.time()
    rows = []
    for s in E8.SUBJS:
        z = np.load(E8.DATA / f"{s}.npz", allow_pickle=True)
        c = np.load(E8.OUT / "scores" / f"{s}.npz")
        n = len(z["is_ictal"]); ok = ~z["is_signal_loss"].astype(bool); idx = c["idx"]

        def full(v):
            o = np.full(n, np.nan); o[idx] = v; o[~ok] = np.nanmedian(v); return o
        zg = rz(full(z["zgamma_raw"][idx].astype(float)), ok)
        for tag in TAGS:
            lat = c[f"{tag}_lat"]
            sc = np.asarray(ER.build_ensemble_subset(
                {"zrecon": rz(full(c[f"{tag}_recon"]), ok),
                 "zlatent": rz(full(LedoitWolf().fit(lat).mahalanobis(lat)), ok), "zgamma": zg},
                ER.CANDIDATES["rlg"]), float)
            for top in TOPS:
                for det, cap in (("D1", None), ("D1c", MAXDUR)):
                    tp, fp, nr, h, durs = score_events(z, d1_events(z, sc, top, cap))
                    rows.append(dict(subject=s, seed=tag, det=det, param=15, p=top, tp=tp, fp=fp, n_ref=nr,
                                     nonict_h=h, n_ev=len(durs), n_ev_long=int(sum(d > MAXDUR for d in durs))))
            for pen in PENS:
                segs = k_segments(z, sc, pen)
                allprom = np.array([pr for sg in segs.values() for (a, b, pr) in sg
                                    if pr > 0 and (b - a) * WIN <= MAXDUR])      # candidates only
                for p in PS:
                    thr = np.quantile(allprom, 1 - p) if len(allprom) else np.inf
                    ev = {f: merge([(a * WIN, b * WIN) for a, b, pr in sg
                                    if pr > 0 and pr >= thr and (b - a) * WIN <= MAXDUR]) for f, sg in segs.items()}
                    tp, fp, nr, h, durs = score_events(z, ev)
                    rows.append(dict(subject=s, seed=tag, det="K", param=pen, p=p, tp=tp, fp=fp, n_ref=nr,
                                     nonict_h=h, n_ev=len(durs), n_ev_long=0))
        print(f"{s}: done ({time.time()-t0:.0f}s)", flush=True)

    df = pd.DataFrame(rows); df.to_csv(OUT / "grid_per_subject.csv", index=False)

    def pool(d):
        g = d.groupby(["seed", "det", "param", "p"])[["tp", "fp", "n_ref", "nonict_h", "n_ev", "n_ev_long"]].sum().reset_index()
        g["sens"] = g.tp / g.n_ref; g["fa_day"] = g.fp / g.nonict_h * 24
        return (g.groupby(["det", "param", "p"]).agg(sens=("sens", "mean"), fa_day=("fa_day", "mean"),
                                                    n_ev=("n_ev", "mean"), n_ev_long=("n_ev_long", "mean"))
                .reset_index())
    P = pool(df); V = pool(df[df.subject.isin(E8.VAL)])
    P.to_csv(OUT / "grid_pooled.csv", index=False)

    def best(T, det, cap=25):
        q = T[(T.det == det) & (T.fa_day <= cap)]
        if not len(q):
            return 0.0, None
        r = q.loc[q.sens.idxmax()]; return float(r.sens), dict(param=r.param, p=r.p, fa_day=round(r.fa_day, 2))
    lines = ["# E10 -- kernel-CPD bump detector (K) vs D1, 15 non-test subjects, v2 clean seeds 42+1\n"]
    for det in ("D1", "D1c", "K"):
        b, c_ = best(P, det); bv, _ = best(V, det)
        lines.append(f"{det}: best sens FA/day<=25 = {b:.3f} {c_} | <=15: {best(P, det, 15)[0]:.3f} | "
                     f"<=10: {best(P, det, 10)[0]:.3f} | validation-only {bv:.3f}")
    d1f = P[(P.det == "D1") & (P.p == 0.02)].iloc[0]
    lines.append(f"\nD1 frozen cell: {d1f.n_ev:.0f} events, of which longer than 300 s: {d1f.n_ev_long:.0f}")
    bK, cK = best(P, "K"); bD, _ = best(P, "D1"); bKv, _ = best(V, "K"); bDv, _ = best(V, "D1")
    if cK:
        k = df[(df.det == "K") & (df.param == cK["param"]) & (df.p == cK["p"])].groupby("subject").tp.mean()
        dcell = best(P, "D1")[1]
        d = df[(df.det == "D1") & (df.p == dcell["p"])].groupby("subject").tp.mean()
        has = df[df.det == "D1"].groupby("subject").n_ref.max() > 0
        n_ok = int(((k >= d) & has).sum()); n_has = int(has.sum())
    else:
        n_ok, n_has = 0, 0
    passed = bK >= bD + 0.10 and bKv >= bDv and n_ok >= 9
    lines += [f"- Gate: K {bK:.3f} vs D1 {bD:.3f}+0.10; validation {bKv:.3f} vs {bDv:.3f}; "
              f"subjects K>=D1: {n_ok}/{n_has} -> {'ADOPTED' if passed else 'NOT adopted'}",
              f"\n**{'FROZEN: K ' + str(cK) if passed else 'D1 stays'}**",
              "\n## Pooled grid (seed mean)\n", "```", P.round(3).to_string(index=False), "```",
              f"\nElapsed {time.time()-t0:.0f} s."]
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:12]))


if __name__ == "__main__":
    main()
