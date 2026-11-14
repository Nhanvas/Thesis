#!/usr/bin/env python
"""
r2_rps.py -- research track, stage RP, path 2, step RP_SERIES (docs/FUTURE_RESEARCH_PLAN.md §12 rows 14/11 01:27 (design,
approved) and 14/11 D26-F (implementation, written before any output)). Kaggle CPU, one notebook RP_SERIES.

The path-2 model (board R190) = the R1 checkpoints of seeds 1-3 + the RP seed-4 checkpoint, k per seed (rp2/k.json). Its
per-window series and per-channel distances were never committed for the development patients (only the final scores
of test / chb24 / Siena, rp2/scores). This module recomputes them from the R0 dataset with the record code and runs the
thesis's own experiments on them, so that Chapter 2 of report version A2 and RP5 / RP9-E1 can be filled:

  F-dm.1  Table 6 (normal reference): C = the patient's whole recording (S9 base: per-patient per-channel Ledoit-Wolf on the
          node latent, 9th largest, e16_recording_baseline.s_from_d); B = baseline from the first 10 / 30 min of each file
          and a causal 30-min window (e16 arms a, c, d); A = A-latent: per-channel Ledoit-Wolf fitted on the latents of the
          clean windows of the 12 training patients, the evaluated patient left out, same tail as C. Detector grid of
          e16 (e1_normal_definition.event_grid, smoothing {1, 3, 5, 15} x top-p {5 ... 0.1 %}).
  F-dm.2  Table 7 (detection): on the final scalar (e22_test_oneshot.final_scalar): the locked PELT detector exactly as
          src/diag_detector_ceiling.py runs it (cpd_pipeline_v14.detect_events on the patient's timeline, points 50/2.0/90
          and 75/5/300, magnitude threshold from the non-ictal, non-buffer, non-flagged windows); the kernel bump detector
          of src/e10_kernel_cpd.py (k_segments, penalties {2, 4, 8} x p {1 ... 20 %}) with E10's own D1 (smoothing 15);
          the threshold detector D1 = the D1b grid below. Added beside (D26-F, routine): the PELT segmenter D2 of
          src/e7_ensemble_cpd.py (d2_grid), which produced the thesis value 0.213.
  F-dm.3a best single development budget: the D1b grid of src/p3b_diag.py (event_grid, smoothing {1, 2, 3, 5, 9} x fine
          top-p grid) on the final scalar.
  F-dm.4-5 drift diagnostics of e16 (a) under S9 base (share of the top-2 % non-ictal windows in the patient's top-quartile
          files, share of those files holding a seizure, flagged shares).
  F-dm.9  median seizure-window robust z (e16 mechanism) of S9 base, arm e (level only, adopted) and arm b (level and
          spread).
  F-dm.7  the c1b 5-SD flag rule (any channel's peak |x| of the whole-file-filtered window above its R0 threshold) on the
          seizure windows of the 12 training patients, from the raw EDF (every file verified against PhysioNet in the
          notebook by r2_core.inventory).
  RP5     channel ranking: src/attribution_v8.py's score (p95 over the seizure's windows of |per-channel robust z|) and
          attribution_pipeline.cmd_eval7 (labels, tests, bootstrap and permutation settings of the record), once per
          path-2 seed as the primary seed.
  RP9-E1  data of report Figure 6: the 9th-largest member of chb03, files 1-3, seed 3, before and after the +-15 min
          running-median correction.
No reading here: the report numbers are made by src/r2_rps_aggregate.py, committed before RP_SERIES runs.

Gates (STOP):
  G-data      the 63 dataset files = R1_SMOKE's pinned hashes (r2_rp.gate_data).
  G-grid      the literal grids of the record scripts this module re-executes (e1_normal_definition defaults, p3b_diag
              SMOOTHS / FINE, e10 PENS / PS, e7 PENS) = the constants used here.
  versions    library versions vs R1_RUN (= RP_RUN's): equal -> mode exact, else tolerance (r2_rp.check_versions).
  RS.0        the recomputed series reproduce the committed path-2 output: run_budget rows of the 15 development and 8
              test patients, seeds 1-4, 4 arms x 3 stages = rp2/per_subject.csv (exact: integers equal, floats relative
              1e-9, error pairs equal and in order, q_raw relative 1e-9; tolerance: |dtp| <= 1, |dfp| <= 2); the final
              scalar x and its 5-window smoothing of every test window and seed = rp2/scores (exact: equal after the
              same %.7g float32 serialisation; tolerance: reported).
  G-alat      the clean latent windows of the 12 training patients = the training-window count of the checkpoints
              (n_train of the seed-4 json: 270,758).
  G-flags     the flag pass reproduces the R0 dataset window by window for every file of the 12 training patients:
              window count, is_ictal, is_buffer and is_flag5sd (the c1b rule) equal; files not in the dataset = files
              preprocessing.open_edf refuses (chb12_27-29); and the seizure-window flag count of the 11 patients whose
              R0 statistics RB1c used = results/r2/r0_data/rb1c/cases.csv (chb12 is excluded: RB1c used the 24-file
              rebuild).
  RS-attr     the alignment of the 76 test seizures = results/attribution_v8/alignment.csv; cmd_eval7 fed with the
              committed attribution_v8 scores reproduces the committed attribution_v8 tables byte for byte.
Outputs: WORK/r2/r1_system/rp_series/ (-> results/r2/r1_system/rp_series/): gates.json, run_meta.json, data_sha256.csv,
rs0/ (per_subject.csv, errors.csv, q.csv, scores_cmp.csv), grid_e16.csv, mechanism.csv, diagnostics.csv, grid_d1b.csv,
table7.csv, flags.csv, flags_files.csv, rp5/ (alignment.csv, attribution_scores.csv, seed_map.json, seed{1-4}/), e1_chb03_seed3.csv,
timing.csv, SUMMARY.md. Scratch (latents, distances) in SCRATCH only.
Test mode (synthetic data, build container only): src/r2_rps_synthetic_test.py.
"""
import contextlib
import csv
import importlib.util
import io
import json
import os
import pickle
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

import r2_rp as RP                       # stage RP (RP1-RP3), read only: views, G-data, versions, pools, compare
R1 = RP.R1
R0, PS, P3L, P3C, E22, X1, PD, TGV2 = R1.R0, R1.PS, R1.P3L, R1.P3C, R1.E22, R1.X1, R1.PD, R1.TGV2
import e16_recording_baseline as E16     # noqa: E402  (record, read only)
import e17b_latent_family as F17         # noqa: E402
import e8_gae_v2_eval as E8              # noqa: E402
import e1_normal_definition as E1        # noqa: E402
import e10_kernel_cpd as E10             # noqa: E402
import e7_ensemble_cpd as E7             # noqa: E402
import e11_tail_anatomy as E11           # noqa: E402
import cpd_pipeline_v14 as V14           # noqa: E402
import szcore_eval as SE                 # noqa: E402
import p3b_diag as P3B                   # noqa: E402
import attribution_pipeline as AP        # noqa: E402

REPO = R1.REPO


def _load_av8():
    """src/attribution_v8.py, imported unchanged. Test mode only (synthetic world with fewer than 76 test seizures):
    its two literal counts of 76 are replaced by R2_TEST_N_TEST_SEIZURES before execution."""
    n = os.environ.get("R2_TEST_N_TEST_SEIZURES") if os.environ.get("R2_TEST") else None
    if not n:
        import attribution_v8 as m
        return m
    src = (REPO / "src" / "attribution_v8.py").read_text(encoding="utf-8")
    src = src.replace("len(blocks) != 76", f"len(blocks) != {int(n)}").replace("76 * len(SEEDS) * 2", f"{int(n)} * len(SEEDS) * 2")
    spec = importlib.util.spec_from_loader("attribution_v8", loader=None, origin=str(REPO / "src" / "attribution_v8.py"))
    m = importlib.util.module_from_spec(spec)
    m.__file__ = str(REPO / "src" / "attribution_v8.py")
    exec(compile(src, m.__file__, "exec"), m.__dict__)
    sys.modules["attribution_v8"] = m
    AP.EXPECTED_TEST_SEIZURES = int(n)
    return m


AV8 = _load_av8()
_OUTSIDE = [m.__name__ for m in (E16, F17, E8, E1, E10, E7, E11, V14, SE, P3B, AP)
            if (REPO / "src") not in Path(m.__file__).resolve().parents]
if _OUTSIDE:
    raise SystemExit(f"STOP: record modules imported from outside {REPO / 'src'}: {_OUTSIDE}")

RP_DIR = REPO / "results" / "r2" / "r1_system" / "rp"
RB1C = REPO / "results" / "r2" / "r0_data" / "rb1c" / "cases.csv"
ATTR8 = REPO / "results" / "attribution_v8"
TAG = "rp_series"
TAGS = list(RP.REPORT_TAGS)                          # clean_seed1 ... clean_seed4 (path 2, no main seed)
SEED_N = {t: int(t.split("seed")[1]) for t in TAGS}
DEV, TEST, TRAIN, VAL = list(R1.DEV), list(R1.TEST), list(R1.TRAIN), list(R1.VAL)
E16_GRID = ([1, 3, 5, 15], [0.05, 0.02, 0.01, 0.005, 0.002, 0.001])      # e1_normal_definition's literal defaults
D1B_GRID = (list(P3B.SMOOTHS), list(P3B.FINE))                            # p3b_diag D1b
E16_ARMS = ("a", "b", "c", "d", "e")
PELT_POINTS = ((50.0, 2.0, 90), (75.0, 5.0, 300))                          # diag_detector_ceiling q1_q2
E1_CASE, E1_TAG, E1_FILES = "chb03", "clean_seed3", (0, 1, 2)

def _n_train():
    """training windows per training patient of the path-2 checkpoints (seed 4's json; seeds 1-3 = R1's, same data)."""
    m = json.loads((RP_DIR / "models" / "gae_v2_clean_seed4.json").read_text())
    return {k: int(v) for k, v in m["n_train"].items()}


N_TRAIN_CASE = _n_train()
N_TRAIN_EXPECTED = int(sum(N_TRAIN_CASE.values()))   # 270,758 on the real data
WIN = 4
log, jdumps, _jdump = R1.log, R1.jdumps, R1._jdump


def out_dir():
    return R1.out_dir()


# ============================================================================ G-grid
def gate_grid():
    """the grids re-executed here are the record scripts' own: e1_normal_definition's literal SMOOTH / TOPS (E16 and E7
    ran with them; importing e17b_latent_family overwrites E1.TOPS in memory, so the literals are read from the source),
    p3b_diag's D1b grid, e10's penalties and p, e7's penalties."""
    src = (REPO / "src" / "e1_normal_definition.py").read_text(encoding="utf-8")
    want = {"SMOOTH = [1, 3, 5, 15]": "e1 SMOOTH", "TOPS = [0.05, 0.02, 0.01, 0.005, 0.002, 0.001]": "e1 TOPS"}
    bad = [v for k, v in want.items() if k not in src]
    if (list(E16_GRID[0]), list(E16_GRID[1])) != ([1, 3, 5, 15], [0.05, 0.02, 0.01, 0.005, 0.002, 0.001]):
        bad.append("E16_GRID")
    if D1B_GRID != ([1, 2, 3, 5, 9], [0.05, 0.03, 0.02, 0.015, 0.01, 0.0075, 0.005, 0.002, 0.001]):
        bad.append(f"p3b grid {D1B_GRID}")
    if list(E10.PENS) != [2.0, 4.0, 8.0] or list(E10.PS) != [0.01, 0.02, 0.05, 0.10, 0.20] or E10.MAXDUR != 300:
        bad.append("e10 grid")
    if list(E7.PENS) != [1.0, 3.0, 10.0]:
        bad.append("e7 PENS")
    if V14.PELT_MIN_SIZE != 3 or V14.PELT_JUMP != 5 or V14.SMOOTHER != "ma15" or V14.MIN_SLOPE_PCT:
        bad.append("cpd_pipeline_v14 constants")
    R1.gate(dict(gate="G-grid", status="PASS" if not bad else "FAIL", bad=bad,
                 summary="record grids = e1 defaults, p3b D1b, e10, e7, v14 PELT constants" if not bad else str(bad)))


@contextlib.contextmanager
def e1_grid(smooths, tops):
    old = (E1.SMOOTH, E1.TOPS)
    E1.SMOOTH, E1.TOPS = list(smooths), list(tops)
    try:
        yield
    finally:
        E1.SMOOTH, E1.TOPS = old


def grid(d, score, smooths, tops):
    with e1_grid(smooths, tops):
        return E1.event_grid(d, score)


# ============================================================================ distances + latents
def model_outputs_z(z):
    """x1_external.model_outputs with its input preparation copied verbatim (same p2_dump_seeds23.run_model, same
    per-channel LedoitWolf), also returning the node latents Z (the per-file baseline arms of e16 and A-latent need them).
    The synthetic test proves D = x1_external.model_outputs(z) bit for bit; gate RS.0 proves it on the real data."""
    from sklearn.covariance import LedoitWolf
    idx = np.flatnonzero(~z["is_signal_loss"].astype(bool))
    adj = z["adj"][idx].astype(np.float32); adj[~np.isfinite(adj).all(axis=(1, 2))] = 0.0
    bp5 = z["bp5"][idx].astype(np.float32); bp5[~np.isfinite(bp5)] = 0.0
    f7 = z["f7"][idx].astype(np.float64)
    xn = (bp5 - bp5.min(axis=1, keepdims=True)) / (bp5.max(axis=1, keepdims=True) - bp5.min(axis=1, keepdims=True) + 1e-8)
    D, Z = {}, {}
    for tag in R1.TAGS:
        _, Zt = PD.run_model(tag, adj, xn, f7)
        D[tag] = np.column_stack([LedoitWolf().fit(Zt[:, c, :].astype(np.float64)).mahalanobis(Zt[:, c, :].astype(np.float64))
                                  for c in range(Zt.shape[1])]).astype(np.float64)
        Z[tag] = Zt
    return idx, D, Z


def _same_csv(mine, stored):
    """equality after the serialisation r2_rp.score_k_job used (float32, %.7g)."""
    a = pd.read_csv(io.StringIO(pd.DataFrame({"v": np.asarray(mine, dtype=np.float32)}).to_csv(index=False, float_format="%.7g"))).v
    b = pd.Series(np.asarray(stored, dtype=float))
    eq = (a.values == b.values) | (np.isnan(a.values) & np.isnan(b.values))
    return int((~eq).sum()), float(np.nanmax(np.abs(a.values - b.values))) if len(a) else 0.0


# ============================================================================ development analyses (one patient)
def e16_patient(case, z, idx, ctx, Z):
    """e16_recording_baseline.main for one subject and the 4 path-2 seeds (S9 base + arms a-e), its loop body copied
    verbatim; grid = e1 defaults (as E16 ran)."""
    d = E8.d_for_grid(z)
    n = len(d["is_ictal"]); ok = ~d["is_signal_loss"]
    fidx = z["file_idx"].astype(int); wf = fidx[idx]
    fl5 = z["is_flag5sd"].astype(bool); ict = z["is_ictal"].astype(bool) & ok
    nonict = ~z["is_ictal"].astype(bool) & ~z["is_buffer"].astype(bool) & ok
    nh = float((~d["is_ictal"] & ok).sum()) * E8.WIN / 3600

    def full(v):
        o = np.full(n, np.nan); o[idx] = v; o[~ok] = np.nanmedian(v); return o

    rows, mech, diag = [], [], []
    for tag in R1.TAGS:
        D = ctx["D"][tag]
        scores = {"S9base": (E16.rz(full(E16.s_from_d(D)), ok), None)}
        for arm in E16_ARMS:
            v_, extra_ = E16.c_scalar(arm, D, Z[tag], wf)
            scores[f"E16{arm}"] = (E16.rz(full(v_), ok), extra_)
        for kind, (v, extra) in scores.items():
            for r_ in grid(d, v, *E16_GRID):
                r_.update(subject=case, score=f"{tag}|{kind}", nonict_h=nh, kind=kind, seed=tag); rows.append(r_)
            mech.append(dict(subject=case, seed=tag, kind=kind, sz_median_z=float(np.nanmedian(v[ict])),
                             flag_median_z=float(np.nanmedian(v[nonict & fl5]))))
            if kind == "S9base":                     # diagnostic (a): drift under S9 base (e16 verbatim)
                sm = E11.smooth(v, ok, fidx)
                T = (sm > np.nanquantile(sm[ok], 0.98)) & nonict
                meds = pd.Series(v[nonict]).groupby(fidx[nonict]).median()
                mad = np.median(np.abs(v[nonict] - np.median(v[nonict]))) + 1e-9
                topf = meds[meds >= meds.quantile(0.75)].index
                sz_files = np.unique(fidx[ict])
                in_top = np.isin(fidx, topf)
                diag.append(dict(subject=case, seed=tag, kind=kind, drift_iqr_over_mad=float(
                    (meds.quantile(0.75) - meds.quantile(0.25)) / mad),
                    tail_share_top_quartile_files=float(np.isin(fidx[T], topf).mean()) if T.any() else np.nan,
                    top_files_with_seizure=float(np.isin(topf, sz_files).mean()) if len(topf) else np.nan,
                    flag_share_top_files=float(fl5[nonict & in_top].mean()) if (nonict & in_top).any() else np.nan,
                    flag_share_other_files=float(fl5[nonict & ~in_top].mean()) if (nonict & ~in_top).any() else np.nan))
            elif extra is not None and extra[1].any():  # diagnostics (b), (c) for baseline arms (e16 verbatim)
                Da, bm = extra
                inb, outb = bm, ~bm & nonict[idx]
                vv = v[idx]
                diag.append(dict(subject=case, seed=tag, kind=kind,
                                 fit_noise_std_in_over_out=float(np.median(Da[inb].std(axis=0) /
                                                                          (Da[outb].std(axis=0) + 1e-9))),
                                 self_scoring_dz=float(np.median(vv[inb]) - np.median(vv[outb]))))
    return rows, mech, diag


def pelt_locked(z, x, mag, pen, ms):
    """the locked PELT detector as src/diag_detector_ceiling.py q1_q2 runs it: V14.detect_events on the patient's
    timeline (files in dataset order, no gap), magnitude threshold from the non-ictal, non-buffer, non-flagged,
    non-signal-loss windows; scored with szcore_eval.score_szcore over the same timeline."""
    ict = z["is_ictal"].astype(bool); buf = z["is_buffer"].astype(bool)
    art = z["is_flag5sd"].astype(bool); sl = z["is_signal_loss"].astype(bool)
    fidx = z["file_idx"].astype(int)
    inter = (~ict) & (~buf) & (~art) & (~sl)
    ev = V14.detect_events(x, pen, min_mag_pct=mag, local_win=15, inter_mask=inter, merge_s=ms)
    ref = []
    for f in np.unique(fidx):
        m = np.flatnonzero(fidx == f)
        ref += [((m[0] + a) * WIN, (m[0] + b) * WIN) for a, b in PS._runs(ict[m])]
    h = float((~ict & ~sl).sum()) * WIN / 3600
    s = SE.score_szcore(ref, ev, len(x) * WIN, h)
    return int(s["tp"]), int(s["fp"]), int(s["n_ref"]), h, len(ev)


def table7_patient(case, z, x, tag):
    """detectors of Table 7 on the final scalar x of one seed."""
    rows = []
    d = E8.d_for_grid(z)
    for mag, pen, ms in PELT_POINTS:
        tp, fp, nr, h, ne = pelt_locked(z, x, mag, pen, ms)
        rows.append(dict(subject=case, seed=tag, detector="PELT_locked", param=f"{int(mag)}_{pen}_{ms}", p=np.nan,
                         tp=tp, fp=fp, n_ref=nr, nonict_h=h, n_ev=ne))
    with e1_grid(*E16_GRID):                                  # e7 ran with the e1 defaults
        for r in E7.d2_grid(d, x):
            rows.append(dict(subject=case, seed=tag, detector="E7_D2", param=str(r["param"]), p=r["top"], tp=r["tp"],
                             fp=r["fp"], n_ref=r["n_ref"], nonict_h=r["nonict_h"], n_ev=np.nan))
    for top in E10.TOPS:                                      # e10's own D1 reference (smoothing 15)
        tp, fp, nr, h, durs = E10.score_events(z, E10.d1_events(z, x, top))
        rows.append(dict(subject=case, seed=tag, detector="E10_D1", param="15", p=top, tp=tp, fp=fp, n_ref=nr,
                         nonict_h=h, n_ev=len(durs)))
    for pen in E10.PENS:                                      # e10 K, its loop body copied verbatim
        segs = E10.k_segments(z, x, pen)
        allprom = np.array([pr for sg in segs.values() for (a, b, pr) in sg if pr > 0 and (b - a) * E10.WIN <= E10.MAXDUR])
        for p in E10.PS:
            thr = np.quantile(allprom, 1 - p) if len(allprom) else np.inf
            ev = {f: E10.merge([(a * E10.WIN, b * E10.WIN) for a, b, pr in sg
                                if pr > 0 and pr >= thr and (b - a) * E10.WIN <= E10.MAXDUR]) for f, sg in segs.items()}
            tp, fp, nr, h, durs = E10.score_events(z, ev)
            rows.append(dict(subject=case, seed=tag, detector="E10_K", param=str(pen), p=p, tp=tp, fp=fp, n_ref=nr,
                             nonict_h=h, n_ev=len(durs)))
    return rows


# ============================================================================ pass A: one patient, every seed
def series_job(a):
    """one development or test patient: distances + latents of the 4 path-2 seeds; RS.0 rows (run_budget at RP's k per
    seed) and, for test, the final-score comparison; development: e16 grid / mechanism / diagnostics, D1b grid, Table 7,
    and the clean latents of training patients for A-latent; test: per-channel distances for RP5 and the RP9-E1 data."""
    case, ckpt_dir, kmap, scratch = a
    t = time.time()
    try:
        PD.CKPT = Path(ckpt_dir)
        scratch = Path(scratch)
        z, _ = R1.load_case(case, "new")
        idx, D, Z = model_outputs_z(z)
        Ds = {t_: D[t_].astype(np.float32) for t_ in R1.TAGS}           # the dump convention of r2_rp (d_job)
        ctx = R1.chb_ctx(case, z, idx, Ds)
        set_name = "development" if case in DEV else "test"
        out = dict(case=case, set=set_name, rows=[], errs=[], q=[], scmp=[], grid=[], mech=[], diag=[], d1b=[], t7=[],
                   e1=[], n_windows=int(ctx["n"]), n_dumped=int(len(idx)))
        X = {}
        for tag in R1.TAGS:
            x = E22.final_scalar(ctx, tag)
            X[tag] = x
            q = P3L.q_of(PS.smoothed(ctx, P3L.member_mean_z(ctx, tag), P3C.SMOOTH), kmap[tag])
            out["q"].append(dict(set=set_name, subject=case, seed=tag, k=kmap[tag], q_raw=q))
            for name, (fl, cp) in R1.ARMS.items():
                P3C.run_budget(ctx, case, tag, x, q, fl, cp, name, out["rows"], out["errs"])
        for r in out["rows"] + out["errs"]:
            r["set"] = set_name
        if set_name == "test":
            ref = pd.read_csv(RP_DIR / "rp2" / "scores" / f"{case}.csv.gz")
            for tag in R1.TAGS:
                s = f"s{SEED_N[tag]}"
                nx, mx = _same_csv(X[tag], ref[f"x_{s}"])
                ns, ms_ = _same_csv(PS.smoothed(ctx, X[tag], P3C.SMOOTH), ref[f"xs_{s}"])
                out["scmp"].append(dict(subject=case, seed=tag, windows=int(len(X[tag])), windows_ref=int(len(ref)),
                                        x_differ=nx, x_max_abs=mx, xs_differ=ns, xs_max_abs=ms_))
            p2 = scratch / "p2test"
            p2.mkdir(parents=True, exist_ok=True)
            np.savez(p2 / f"{case}.npz", idx=idx, **{f"clean_seed{SEED_N[t_]}_d": Ds[t_] for t_ in R1.TAGS})
            if case == E1_CASE:
                Dt = ctx["D"][E1_TAG]
                v = E16.s_from_d(Dt)
                mem = F17.member(Dt, ctx["wf"], 9)
                tif = np.zeros(ctx["n"], int)
                for f in np.unique(ctx["fidx"]):
                    m = np.flatnonzero(ctx["fidx"] == f)
                    tif[m] = np.arange(len(m)) * WIN
                for j, w in enumerate(idx):
                    if int(ctx["fidx"][w]) in E1_FILES:
                        out["e1"].append(dict(window=int(w), file_idx=int(ctx["fidx"][w]), t_in_file_s=int(tif[w]),
                                              ictal=int(ctx["ict"][w]), s9=float(v[j]), running_median=float(v[j] - mem[j]),
                                              s9_corrected=float(mem[j])))
        else:
            out["grid"], out["mech"], out["diag"] = e16_patient(case, z, idx, ctx, Z)
            d = E8.d_for_grid(z)
            for tag in R1.TAGS:
                for r_ in grid(d, X[tag], *D1B_GRID):
                    r_.update(subject=case, seed=tag, nonict_h=ctx["nh"]); out["d1b"].append(r_)
                out["t7"] += table7_patient(case, z, X[tag], tag)
            if case in TRAIN:
                pos = np.flatnonzero(TGV2.mask(z, "clean")[idx])
                al = scratch / "alat"
                al.mkdir(parents=True, exist_ok=True)
                for tag in R1.TAGS:
                    np.save(al / f"{case}_{tag}.npy", Z[tag][pos])
                out["n_clean"] = int(len(pos))
        out["s"] = round(time.time() - t, 1)
        return out
    except SystemExit as e:
        return dict(case=case, error=f"STOP: {e}")
    except Exception:                    # noqa: BLE001
        return dict(case=case, error=traceback.format_exc()[-3000:])


# ============================================================================ pass B / C: A-latent
def alat_fit_job(a):
    """one seed: per-channel LedoitWolf on the clean latents of the 12 training patients, once with all 12 (for the
    validation patients) and once without each training patient (leave that patient out)."""
    tag, scratch = a
    t = time.time()
    try:
        from sklearn.covariance import LedoitWolf
        al = Path(scratch) / "alat"
        Zs = {c: np.load(al / f"{c}_{tag}.npy") for c in TRAIN}
        fits, n_fit = {}, {}
        for left in ["none"] + TRAIN:
            Zc = np.concatenate([Zs[c] for c in TRAIN if c != left])
            n_fit[left] = int(len(Zc))
            fits[left] = [LedoitWolf().fit(Zc[:, ch, :].astype(np.float64)) for ch in range(Zc.shape[1])]
            del Zc
        with open(al / f"fit_{tag}.pkl", "wb") as fh:
            pickle.dump(fits, fh)
        return dict(case=tag, tag=tag, n_fit=n_fit, n_per_case={c: int(len(v)) for c, v in Zs.items()},
                    s=round(time.time() - t, 1))
    except Exception:                    # noqa: BLE001
        return dict(case=tag, error=traceback.format_exc()[-3000:])


def alat_job(a):
    """one development patient: A-latent = per-channel Mahalanobis of its latents to the training patients' fit (itself
    left out if it is a training patient), then the tail of C (e16 s_from_d, robust z), e16 grid and mechanism."""
    case, ckpt_dir, scratch = a
    t = time.time()
    try:
        PD.CKPT = Path(ckpt_dir)
        z, _ = R1.load_case(case, "new")
        idx, _, Z = model_outputs_z(z)
        d = E8.d_for_grid(z)
        n = len(d["is_ictal"]); ok = ~d["is_signal_loss"]
        fl5 = z["is_flag5sd"].astype(bool); ict = z["is_ictal"].astype(bool) & ok
        nonict = ~z["is_ictal"].astype(bool) & ~z["is_buffer"].astype(bool) & ok
        nh = float((~d["is_ictal"] & ok).sum()) * E8.WIN / 3600

        def full(v):
            o = np.full(n, np.nan); o[idx] = v; o[~ok] = np.nanmedian(v); return o
        rows, mech = [], []
        for tag in R1.TAGS:
            with open(Path(scratch) / "alat" / f"fit_{tag}.pkl", "rb") as fh:
                fits = pickle.load(fh)[case if case in TRAIN else "none"]
            DA = np.column_stack([fits[ch].mahalanobis(Z[tag][:, ch, :].astype(np.float64)) for ch in range(len(fits))])
            v = E16.rz(full(E16.s_from_d(DA)), ok)
            for r_ in grid(d, v, *E16_GRID):
                r_.update(subject=case, score=f"{tag}|A_latent", nonict_h=nh, kind="A_latent", seed=tag); rows.append(r_)
            mech.append(dict(subject=case, seed=tag, kind="A_latent", sz_median_z=float(np.nanmedian(v[ict])),
                             flag_median_z=float(np.nanmedian(v[nonict & fl5]))))
        return dict(case=case, grid=rows, mech=mech, s=round(time.time() - t, 1))
    except Exception:                    # noqa: BLE001
        return dict(case=case, error=traceback.format_exc()[-3000:])


# ============================================================================ the passes (parent)
def pass_a(workers, scratch):
    t = time.time()
    kmap = {k: float(v) for k, v in json.loads((RP_DIR / "rp2" / "k.json").read_text())["k"].items() if k in TAGS}
    ck = RP.ckpt_dir_all(RP_DIR / "models")
    specs = sorted([(c, str(ck), kmap, str(scratch)) for c in DEV + TEST], key=lambda s: -R1._size(s[0], "new"))
    res = {r["case"]: r for r in RP._run(series_job, specs, workers, TAGS, "series")}
    R1.phase("pass_a", t)
    return res, ck, kmap


def rs0(res):
    """gate RS.0 (see the docstring)."""
    t = time.time()
    mode = RP.STATE["mode"]
    tol = RP.TOL[mode]
    order = DEV + TEST
    rows = pd.DataFrame([r for c in order for r in res[c]["rows"]])
    errs = pd.DataFrame([r for c in order for r in res[c]["errs"]])
    q = pd.DataFrame([r for c in order for r in res[c]["q"]])
    sc = pd.DataFrame([r for c in TEST for r in res[c]["scmp"]])
    o = out_dir() / "rs0"
    o.mkdir(parents=True, exist_ok=True)
    rows.to_csv(o / "per_subject.csv", index=False); errs.to_csv(o / "errors.csv", index=False)
    q.to_csv(o / "q.csv", index=False); sc.to_csv(o / "scores_cmp.csv", index=False)
    keep = lambda df: df[df.seed.isin(TAGS) & df["set"].isin(["development", "test"])]   # noqa: E731
    ref_rows = keep(pd.read_csv(RP_DIR / "rp2" / "per_subject.csv"))
    ref_errs = keep(pd.read_csv(RP_DIR / "rp2" / "errors.csv"))
    ref_q = keep(pd.read_csv(RP_DIR / "rp2" / "q.csv"))
    n, exact, bad = RP._cmp_rows(rows, ref_rows, mode)
    ne, ebad = RP._cmp_errors(errs, ref_errs)
    qm = q.merge(ref_q, on=["set", "subject", "seed"], suffixes=("", "_ref"), how="outer", indicator=True)
    qrel = (qm.q_raw - qm.q_raw_ref).abs() / qm.q_raw_ref.abs().clip(lower=1e-12)
    qbad = int((qm._merge != "both").sum() + (qrel > tol["float_rel"]).sum())
    sbad = int((sc.windows != sc.windows_ref).sum() + (sc.x_differ > 0).sum() + (sc.xs_differ > 0).sum())
    n_want = (len(DEV) + len(TEST)) * len(TAGS) * len(R1.ARMS) * 3
    ok = n == n_want and not bad and (mode == "tolerance" or (not ebad and not qbad and not sbad and exact == n))
    rec = dict(gate="RS.0", status="PASS" if ok else "FAIL", mode=mode, rows=n, rows_expected=n_want, exact_rows=exact,
               n_mismatch=len(bad), mismatches=bad[:30], error_pairs=ne, error_groups_differ=len(ebad),
               error_mismatches=ebad[:5], q_rows=int(len(qm)), q_differ=qbad, score_rows=int(len(sc)),
               score_rows_differ=sbad, x_max_abs=float(sc.x_max_abs.max()) if len(sc) else None,
               summary=f"mode {mode}: {n} rows ({exact} exact, expected {n_want}), {ne} error pairs ({len(ebad)} groups "
                       f"differ), q {qbad} differ, test scores {sbad} of {len(sc)} seed-patients differ")
    R1.phase("rs0", t)
    R1.gate(rec)
    return rec


def write_dev(res):
    t = time.time()
    o = out_dir()
    for key, name in (("grid", "grid_e16.csv"), ("mech", "mechanism.csv"), ("diag", "diagnostics.csv"),
                      ("d1b", "grid_d1b.csv"), ("t7", "table7.csv")):
        pd.DataFrame([r for c in DEV for r in res[c][key]]).to_csv(o / name, index=False)
    pd.DataFrame(res[E1_CASE]["e1"]).to_csv(o / "e1_chb03_seed3.csv", index=False)
    R1.phase("write_dev", t)


def a_latent(workers, scratch, ck, res):
    """pass B (one worker per seed) + G-alat + pass C (one worker per development patient)."""
    t = time.time()
    n_clean = {c: res[c]["n_clean"] for c in TRAIN}
    fit = {r["tag"]: r for r in RP._run(alat_fit_job, [(tag, str(scratch)) for tag in TAGS], min(workers, len(TAGS)),
                                        TAGS, "A-latent fit")}
    tot = int(sum(n_clean.values()))
    bad = [tag for tag in TAGS if fit[tag]["n_fit"]["none"] != N_TRAIN_EXPECTED or fit[tag]["n_per_case"] != n_clean]
    if tot != N_TRAIN_EXPECTED or n_clean != N_TRAIN_CASE:
        bad.append(f"clean windows {tot} / per patient differ from the checkpoint json")
    R1.gate(dict(gate="G-alat", status="PASS" if not bad else "FAIL", n_clean_total=tot, expected=N_TRAIN_EXPECTED,
                 n_clean=n_clean, bad=bad, summary=f"clean latent windows of the 12 training patients {tot} "
                                                   f"(expected {N_TRAIN_EXPECTED}); leave-one-out fits per seed"))
    specs = sorted([(c, str(ck), str(scratch)) for c in DEV], key=lambda s: -R1._size(s[0], "new"))
    out = {r["case"]: r for r in RP._run(alat_job, specs, workers, TAGS, "A-latent score")}
    o = out_dir()
    g = pd.read_csv(o / "grid_e16.csv")
    g = pd.concat([g, pd.DataFrame([r for c in DEV for r in out[c]["grid"]])], ignore_index=True)
    g.to_csv(o / "grid_e16.csv", index=False)
    m = pd.read_csv(o / "mechanism.csv")
    pd.concat([m, pd.DataFrame([r for c in DEV for r in out[c]["mech"]])], ignore_index=True).to_csv(o / "mechanism.csv",
                                                                                                        index=False)
    R1.phase("a_latent", t)


# ============================================================================ F-dm.7: flags on the raw EEG
def flags_job(a):
    """one training patient: the c1b flag rule on every window of every file read by the record loader, from the raw
    EDF (continuous_eval.filter_file), with the R0 thresholds; compared window by window with the R0 dataset."""
    case, raw_dir, summary, ref_npz, stats_json = a
    t = time.time()
    try:
        import preprocessing as P
        import continuous_eval as CE
        R0._limit_threads()
        thr = np.asarray(json.loads(Path(stats_json).read_text())["artifact_thresh_uV"], np.float64) * 1e-6
        smap = P.parse_summary(Path(summary))
        z = np.load(ref_npz, allow_pickle=True)
        files = [str(f) for f in z["files"]]
        fidx = z["file_idx"].astype(int)
        present = sorted(p.name for p in Path(raw_dir).glob("*.edf"))
        extra = [f for f in present if f not in files]
        refused = [f for f in extra if P.open_edf(Path(raw_dir) / f) is None]
        rows, mism = [], dict(windows=0, is_ictal=0, is_buffer=0, is_flag5sd=0, missing_files=sorted(set(files) - set(present)),
                              extra_not_refused=sorted(set(extra) - set(refused)))
        for i, fn in enumerate(files):
            if fn not in present:
                continue
            filt, n = CE.filter_file(Path(raw_dir) / fn)
            peak = np.abs(filt.astype(np.float64)).max(axis=2)
            del filt
            secs = n * P.WIN_S
            sz = smap.get(fn, [])
            lab = P.build_labels(secs, sz).reshape(n, P.WIN_S).max(axis=1) == 1
            buf = P.build_buffer_mask(secs, sz).reshape(n, P.WIN_S).any(axis=1)
            over = (peak > thr[None, :]).any(axis=1)
            m = np.flatnonzero(fidx == i)
            if len(m) != n:
                mism["windows"] += abs(len(m) - n)
                continue
            sl = z["is_signal_loss"][m].astype(bool)
            mism["is_ictal"] += int((lab != z["is_ictal"][m].astype(bool)).sum())
            mism["is_buffer"] += int((buf != z["is_buffer"][m].astype(bool)).sum())
            mism["is_flag5sd"] += int(((over & ~lab & ~buf) != z["is_flag5sd"][m].astype(bool)).sum())
            rows.append(dict(case=case, file=fn, windows=int(n), ictal=int(lab.sum()), ictal_flagged=int((over & lab).sum()),
                             ictal_ok=int((lab & ~sl).sum()), ictal_ok_flagged=int((over & lab & ~sl).sum()),
                             base=int((~lab & ~buf).sum()), base_flagged=int((over & ~lab & ~buf).sum())))
        return dict(case=case, files=rows, mismatch=mism, refused=refused, s=round(time.time() - t, 1))
    except Exception:                    # noqa: BLE001
        return dict(case=case, error=traceback.format_exc()[-3000:])


def flags(workers, complete_view, ref_dir=None):
    """F-dm.7 + gate G-flags. complete_view = r2_core.inventory's verified view (SCRATCH/view/complete); ref_dir = the R0
    dataset view (R1.VIEWS/new: {case}.npz + {case}_stats.json, pinned by G-data)."""
    t = time.time()
    ref_dir = Path(ref_dir or R1.VIEWS / "new")
    raw = Path(complete_view) / "chbmit"
    specs = [(c, str(raw / c), str(R0.summary_path(Path(complete_view), c)), str(ref_dir / f"{c}.npz"),
              str(ref_dir / f"{c}_stats.json")) for c in TRAIN]
    specs = sorted(specs, key=lambda s: -sum(p.stat().st_size for p in Path(s[1]).glob("*.edf")))
    with R0_pool(min(workers, len(specs))) as pool:
        res = {}
        for r in pool.imap_unordered(flags_job, specs):
            if r.get("error"):
                pool.terminate()
                raise SystemExit(f"flags {r['case']}: {r['error']}")
            res[r["case"]] = r
            log(f"flags {r['case']} done ({r['s']} s)")
    F = pd.DataFrame([x for c in TRAIN for x in res[c]["files"]])
    F.to_csv(out_dir() / "flags_files.csv", index=False)
    C = F.groupby("case")[["windows", "ictal", "ictal_flagged", "ictal_ok", "ictal_ok_flagged", "base", "base_flagged"]] \
        .sum().reindex(TRAIN).reset_index()
    rb = pd.read_csv(RB1C).set_index("case")
    rbc = []
    for r in C.itertuples():
        if r.case == "chb12":
            rbc.append(dict(case=r.case, rb1c_ictal=np.nan, rb1c_ictal_flagged=np.nan, rb1c_equal=None))
            continue
        ri = int(rb.loc[r.case, "ictal_windows"])
        rf = int(round(float(rb.loc[r.case, "ictal_over_record_threshold"]) * ri))
        rbc.append(dict(case=r.case, rb1c_ictal=ri, rb1c_ictal_flagged=rf, rb1c_equal=bool(ri == r.ictal and rf == r.ictal_flagged)))
    C = C.merge(pd.DataFrame(rbc), on="case")
    C["refused_files"] = [";".join(res[c]["refused"]) for c in C.case]
    C.to_csv(out_dir() / "flags.csv", index=False)
    mm = {c: res[c]["mismatch"] for c in TRAIN}
    bad = {c: m for c, m in mm.items() if m["windows"] or m["is_ictal"] or m["is_buffer"] or m["is_flag5sd"]
           or m["missing_files"] or m["extra_not_refused"]}
    rb_bad = [r["case"] for r in rbc if r["rb1c_equal"] is False]
    rec = dict(gate="G-flags", status="PASS" if not bad and not rb_bad else "FAIL", mismatch=bad, rb1c_differ=rb_bad,
               refused={c: res[c]["refused"] for c in TRAIN if res[c]["refused"]}, files=int(len(F)),
               summary=f"{len(F)} files of the 12 training patients: windows, is_ictal, is_buffer, is_flag5sd = the R0 "
                       f"dataset; seizure-window flag counts = RB1c for {sum(r['rb1c_equal'] is True for r in rbc)} of 11")
    R1.phase("flags", t)
    R1.gate(rec)
    return C


@contextlib.contextmanager
def R0_pool(n):
    import multiprocessing as mp
    with mp.get_context("spawn").Pool(n, initializer=R1._init_worker, initargs=(R1._env(),), maxtasksperchild=1) as p:
        yield p


# ============================================================================ RP5: channel ranking
def _cmp_tables(a_dir, b_dir, names):
    out = {}
    for f in names:
        a = (Path(a_dir) / f).read_text().replace("\r\n", "\n")
        b = (Path(b_dir) / f).read_text().replace("\r\n", "\n")
        out[f] = a == b
    return out


def run_eval7(S, nw, outdir):
    """attribution_pipeline.cmd_eval7 unchanged, fed with S as attribution_v8.main feeds it (scores in memory, the labels'
    window counts replaced by the scored windows); returns its printed log."""
    orig = (AP.load_scores, AP.load_labels7, AP.OUT7)

    def labels_v2():
        lab = orig[1]()
        for k in lab:
            lab[k]["nw"] = nw[k]
        return lab
    AP.load_scores = lambda seed=None, agg=None: S
    AP.load_labels7 = labels_v2
    AP.OUT7 = Path(outdir)
    Path(outdir).mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            AP.cmd_eval7(None)
    finally:
        AP.load_scores, AP.load_labels7, AP.OUT7 = orig
    (Path(outdir) / "eval7.log").write_text(buf.getvalue(), encoding="utf-8")
    return buf.getvalue()


def rp5(scratch):
    """RS-attr gates, then cmd_eval7 once per path-2 seed as the primary seed (the record's primary key 42 = that seed;
    the other three take the keys 1, 2, 3 of the record's descriptive seed panels)."""
    t = time.time()
    o = out_dir() / "rp5"
    o.mkdir(parents=True, exist_ok=True)
    AV8.TESTSET = R1.VIEWS / "new"
    AV8.P2TEST = Path(scratch) / "p2test"
    AV8.SEEDS = [SEED_N[t_] for t_ in TAGS]
    rows, spans = AV8.align()
    S, nw = AV8.scores(spans)
    for r in rows:
        r["n_windows_scored"] = nw[(r["subject"], r["seizure_idx"])]
    AP.write_csv(o / "alignment.csv", rows)
    mine = pd.read_csv(o / "alignment.csv")
    ref = pd.read_csv(ATTR8 / "alignment.csv")
    al_ok = list(mine.columns) == list(ref.columns) and mine.astype(str).equals(ref.astype(str))
    AP.write_csv(o / "attribution_scores.csv",
                 [dict(seed=k[0], agg=k[1], subject=k[2], seizure_idx=k[3], ch_idx=i, ch_name=AP.CH[i],
                       score=round(float(v[i]), 6)) for k, v in sorted(S.items()) for i in range(18)])
    S_ref = {}
    for r in csv.DictReader(open(ATTR8 / "attribution_scores.csv")):
        S_ref.setdefault((int(r["seed"]), r["agg"], r["subject"], int(r["seizure_idx"])), np.zeros(18))[int(r["ch_idx"])] = \
            float(r["score"])
    nw_ref = {(r["subject"], int(r["seizure_idx"])): int(r["n_windows_scored"]) for r in csv.DictReader(open(ATTR8 / "alignment.csv"))}
    tmp = Path(scratch) / "rp5_codepath"
    run_eval7(S_ref, nw_ref, tmp)
    names = ("attribution_perseizure.csv", "attribution_summary.csv", "attribution_tests.csv")
    eq = _cmp_tables(tmp, ATTR8, names)
    R1.gate(dict(gate="RS-attr", status="PASS" if al_ok and all(eq.values()) else "FAIL", alignment_equal=al_ok,
                 codepath_tables_equal=eq, seizures=int(len(rows)),
                 summary=f"alignment of {len(rows)} test seizures = attribution_v8 ({al_ok}); cmd_eval7 on the committed "
                         f"attribution_v8 scores reproduces its tables ({all(eq.values())})"))
    seeds = [SEED_N[t_] for t_ in TAGS]
    smap = {}
    for p in seeds:
        others = [s for s in seeds if s != p]
        key = {p: 42, **{s: j + 1 for j, s in enumerate(others)}}
        smap[f"primary_seed{p}"] = {f"path2_seed{s}": f"record_key{k}" for s, k in key.items()}
        Sp = {(key[k[0]], k[1], k[2], k[3]): v for k, v in S.items()}
        run_eval7(Sp, nw, o / f"seed{p}")
    _jdump(o / "seed_map.json", smap)
    R1.phase("rp5", t)


# ============================================================================ summary
def summary_md():
    L = [f"# RP_SERIES — gates and timing (no research number; mode {RP.STATE['mode']})\n", "| gate | status | summary |",
         "|---|---|---|"]
    L += [f"| {g['gate']} | {g['status']} | {g.get('summary', '')} |" for g in R1.STATE["gates"]]
    L += ["", f"Phases (s): {jdumps(R1.STATE['phases'])}", "", "Tables: `python src/r2_rps_aggregate.py --series "
          "results/r2/r1_system/rp_series` (committed before this run)."]
    (out_dir() / "SUMMARY.md").write_text("\n".join(L) + "\n")
    return "\n".join(L)


def timing(res):
    pd.DataFrame([dict(case=c, set=r["set"], windows=r["n_windows"], dumped=r["n_dumped"], s=r["s"])
                  for c, r in res.items()]).to_csv(out_dir() / "timing.csv", index=False)
