#!/usr/bin/env python
"""
r2_rpsprobe.py -- research track, stage RP, path 2: second diagnosis step of the slow RP_SERIES pass A (plan §12 15/11
11:30, D27-F). Kaggle CPU, notebook RPS_PROBE (src/r2_rpsprobe_make_notebook.py). TIMING ONLY: nothing is scored for the
report.

WHY. The container test on the real development series exported by RPS_DEVX (src/r2_rpsdevx_timing.py) rejects H1 and H2:
on chb10, seed 1, the locked PELT takes 7 + 11 s, the exact E7 D2 5 s, E10 4 s, the D1b grid 0.4 s; RPS_DEVX itself ran
run_budget for all 15 development patients in 360 s. Yet RP_SERIES spent 16,054 s on chb10. What remains is measured here,
on Kaggle, on the real inputs (the latents and distances exist only there): every step of series_job for one development
patient, in the main process (no pool), each step timed and logged the moment it ends, and the e16 arms and Table 7
detectors also profiled (cProfile, top functions by cumulative time) per seed.

Per case: load; model_outputs_z; chb_ctx; final_scalar + q + run_budget (4 seeds x 4 arms); then for each seed: S9 base and
e16 arms a-e (c_scalar, robust z, e16 grid, mechanism, diagnostics), the D1b grid, the locked PELT (2 points), E7 D2
(exact), E10 D1, E10 K; the A-latent save. The final scalar is checked against the RPS_DEVX export (same path).
Output: WORK/r2/r1_system/rps_probe/ (probe.csv rows as they finish, profiles/*.txt, run_meta.json, SUMMARY.md).
"""
import cProfile
import io
import pstats
import time
from pathlib import Path

import numpy as np
import pandas as pd

import r2_rps as RS
RP, R1 = RS.RP, RS.R1
E16, E8, E11, P3C, P3L, PS, E22 = RS.E16, RS.E8, RS.E11, RS.P3C, RS.P3L, RS.PS, RS.E22
TAG = "rps_probe"
DEVX = RS.REPO / "results" / "r2" / "r1_system" / "rps_devx" / "scores_dev"


def _out():
    return R1.out_dir()


ROWS = []


def put(row):
    """log the row at once and rewrite probe.csv with every row so far (rows carry different extra columns)."""
    ROWS.append(row)
    pd.DataFrame(ROWS).to_csv(_out() / "probe.csv", index=False)
    R1.log(f"PROBE {row}")


def prof(name, case, tag, fn):
    """run fn under cProfile; write the top 25 functions by cumulative time; return (result, seconds)."""
    pr = cProfile.Profile()
    t = time.perf_counter()
    pr.enable()
    try:
        r = fn()
    finally:
        pr.disable()
    s = time.perf_counter() - t
    buf = io.StringIO()
    pstats.Stats(pr, stream=buf).sort_stats("cumulative").print_stats(25)
    d = _out() / "profiles"
    d.mkdir(exist_ok=True)
    (d / f"{case}_{tag}_{name}.txt").write_text(buf.getvalue())
    return r, s


def e16_one_seed(case, z, idx, ctx, Z, tag):
    """the body of r2_rps.e16_patient for one seed, each part timed (same calls, same grid)."""
    d = E8.d_for_grid(z)
    n = len(d["is_ictal"]); ok = ~d["is_signal_loss"]
    fidx = z["file_idx"].astype(int); wf = fidx[idx]
    fl5 = z["is_flag5sd"].astype(bool); ict = z["is_ictal"].astype(bool) & ok
    nonict = ~z["is_ictal"].astype(bool) & ~z["is_buffer"].astype(bool) & ok
    nh = float((~d["is_ictal"] & ok).sum()) * E8.WIN / 3600

    def full(v):
        o = np.full(n, np.nan); o[idx] = v; o[~ok] = np.nanmedian(v); return o
    D = ctx["D"][tag]
    t = time.perf_counter()
    scores = {"S9base": (E16.rz(full(E16.s_from_d(D)), ok), None)}
    put(dict(case=case, seed=tag, step="e16_S9base_scalar", s=round(time.perf_counter() - t, 2)))
    for arm in RS.E16_ARMS:
        t = time.perf_counter()
        v_, extra_ = E16.c_scalar(arm, D, Z[tag], wf)
        scores[f"E16{arm}"] = (E16.rz(full(v_), ok), extra_)
        put(dict(case=case, seed=tag, step=f"e16_{arm}_scalar", s=round(time.perf_counter() - t, 2)))
    for kind, (v, extra) in scores.items():
        t = time.perf_counter()
        RS.grid(d, v, *RS.E16_GRID)
        put(dict(case=case, seed=tag, step=f"e16_{kind}_grid", s=round(time.perf_counter() - t, 2)))
        t = time.perf_counter()
        float(np.nanmedian(v[ict])); float(np.nanmedian(v[nonict & fl5]))
        if kind == "S9base":
            sm = E11.smooth(v, ok, fidx)
            T = (sm > np.nanquantile(sm[ok], 0.98)) & nonict
            meds = pd.Series(v[nonict]).groupby(fidx[nonict]).median()
            topf = meds[meds >= meds.quantile(0.75)].index
            np.isin(fidx[T], topf).mean() if T.any() else np.nan
        elif extra is not None and extra[1].any():
            Da, bm = extra
            np.median(Da[bm].std(axis=0) / (Da[~bm & nonict[idx]].std(axis=0) + 1e-9))
        put(dict(case=case, seed=tag, step=f"e16_{kind}_diag", s=round(time.perf_counter() - t, 2)))
    return nh


def probe_case(case, kmap):
    t0 = time.perf_counter()
    t = time.perf_counter()
    z, _ = R1.load_case(case, "new")
    put(dict(case=case, seed="", step="load", s=round(time.perf_counter() - t, 2), windows=int(len(z["file_idx"]))))
    t = time.perf_counter()
    idx, D, Z = RS.model_outputs_z(z)
    put(dict(case=case, seed="", step="model_outputs_z", s=round(time.perf_counter() - t, 2)))
    Ds = {t_: D[t_].astype(np.float32) for t_ in R1.TAGS}
    t = time.perf_counter()
    ctx = R1.chb_ctx(case, z, idx, Ds)
    X = {}
    ref = pd.read_csv(DEVX / f"{case}.csv.gz", float_precision="round_trip")
    for tag in R1.TAGS:
        x = E22.final_scalar(ctx, tag)
        X[tag] = x
        q = P3L.q_of(PS.smoothed(ctx, P3L.member_mean_z(ctx, tag), P3C.SMOOTH), kmap[tag])
        rows, errs = [], []
        for name, (fl, cp) in R1.ARMS.items():
            P3C.run_budget(ctx, case, tag, x, q, fl, cp, name, rows, errs)
        same = bool(np.array_equal(x, ref[f"x_s{RS.SEED_N[tag]}"].values, equal_nan=True))
        put(dict(case=case, seed=tag, step="x_equals_rpsdevx", s=0.0, value=same))
    put(dict(case=case, seed="", step="ctx_final_scalar_budget", s=round(time.perf_counter() - t, 2)))
    for tag in R1.TAGS:
        _, s = prof("e16", case, tag, lambda: e16_one_seed(case, z, idx, ctx, Z, tag))
        put(dict(case=case, seed=tag, step="e16_total", s=round(s, 2)))
        d = E8.d_for_grid(z)
        t = time.perf_counter()
        RS.grid(d, X[tag], *RS.D1B_GRID)
        put(dict(case=case, seed=tag, step="d1b_grid", s=round(time.perf_counter() - t, 2)))
        tm = {}
        _, s = prof("table7", case, tag, lambda: RS.table7_patient(case, z, X[tag], tag, tm))
        put(dict(case=case, seed=tag, step="table7_total", s=round(s, 2), **{k: round(v, 2) for k, v in tm.items()}))
    t = time.perf_counter()
    if case in RS.TRAIN:
        pos = np.flatnonzero(RS.TGV2.mask(z, "clean")[idx])
        al = R1.SCRATCH / "probe_alat"
        al.mkdir(parents=True, exist_ok=True)
        for tag in R1.TAGS:
            np.save(al / f"{case}_{tag}.npy", Z[tag][pos])
    put(dict(case=case, seed="", step="alat_save", s=round(time.perf_counter() - t, 2)))
    put(dict(case=case, seed="", step="case_total", s=round(time.perf_counter() - t0, 2)))


def run(cases):
    kmap = {k: float(v) for k, v in RS.json.loads((RS.RP_DIR / "rp2" / "k.json").read_text())["k"].items() if k in RS.TAGS}
    RP.set_tags(list(RS.TAGS))                       # as the pool workers of RP_SERIES (r2_rp._init)
    RS.PD.CKPT = RP.ckpt_dir_all(RS.RP_DIR / "models")
    for c in cases:
        probe_case(c, kmap)


def summary_md():
    p = _out() / "probe.csv"
    L = ["# RPS_PROBE — step timing of RP_SERIES' series_job on real development patients (timing only)\n"]
    if p.exists():
        df = pd.read_csv(p)
        L += ["```", df.to_string(index=False), "```"]
    (_out() / "SUMMARY.md").write_text("\n".join(L) + "\n")
    return "\n".join(L)
