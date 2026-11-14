#!/usr/bin/env python
"""
r2_rps_timing.py -- research track, stage RP, path 2 (fix B of RP_SERIES; docs/FUTURE_RESEARCH_PLAN.md §12 14/11 18:30
(d), D27-F): measures every pass-A component of RP_SERIES (src/r2_rps.py series_job) in the build container, on the
longest real committed series, and computes the runtime per case against the 12-h Kaggle session. TIMING ONLY: nothing
here is scored for the report or read as a result.

Series. The committed path-2 final scores of the test patients (results/r2/r1_system/rp/rp2/scores; x of seeds 1-4,
ok, ictal, file_idx). chb06 is the longest (60,060 windows, 18 files of up to 3,606 windows = the 4-h files of the
development cases chb04, chb07, chb09). Components that need the latent / distance arrays (not committed) run on random
arrays of the real shapes (n_ok x 18 and n_ok x 18 x 16, float32): their cost depends on the sizes, not on the values.
The window masks the components read (buffer, 5-SD flag) are not in the scores file: buffer = 4 h after each seizure in
its file (the record rule), flag = a random 40 % of the other windows (the measured share is 28-60 %).

Components (as series_job runs them, 4 seeds): T_test = final_scalar + q_of + run_budget (4 arms) + the score
comparison + the p2test save; T_e16 = e16_patient (S9 base + arms a-e, e16 grid, mechanism, diagnostics); T_d1b = the
D1b grid; T7 parts = locked PELT (2 points), E7 D2 (exact segmentation, src/r2_e7exact.py, incl. its scoring loop),
E10 D1, E10 K. Distances and latents (model_outputs_z) are not run here (torch is not in the container): their Kaggle rate
is measured in R1_SMOKE (37.8 s for chb01, 40.6 h, 4 seeds = 0.93 s per hour of EEG).

Kaggle factor. The first RP_SERIES run measured chb06 (test) at 105 s on Kaggle with 4 workers. Subtracting its
distances (0.93 s/h x 66.7 h = 62 s) leaves 43 s for the test path; the factor Kaggle / container = 43 s / T_test(chb06).
The projection uses max(that factor, 2.5) (2.5 = the earlier chb10 ratio, plan §12 14/11 18:30 (b)).

Per case: every component is measured on chb06 and on a concatenation of real test series to chb04's length (140,453
windows) cut into chb04's own file lengths (R0 inventory); a power law through the two sizes (exponent >= 1) gives the
other cases, so the growth with length is measured, not assumed (the locked PELT of Table 7, pure-Python ruptures on the
whole patient timeline, grows ~ n^1.6). Phases after pass A (A-latent fits and scoring, the raw-EEG flag pass, RP5,
setup and gates) are added as computed allowances (RB1C_SURVEY measured 1.08 h for 1,120 h of raw EEG on 4 processes).
  python src/r2_rps_timing.py --out results/r2/r1_system/rps_fixb
"""
import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import e16_recording_baseline as E16      # noqa: E402
import e17b_latent_family as F17          # noqa: E402,F401
import e8_gae_v2_eval as E8               # noqa: E402
import e1_normal_definition as E1         # noqa: E402
import e10_kernel_cpd as E10              # noqa: E402
import e7_ensemble_cpd as E7              # noqa: E402
import e11_tail_anatomy as E11            # noqa: E402
import cpd_pipeline_v14 as V14            # noqa: E402
import szcore_eval as SE                  # noqa: E402
import p3b_diag as P3B                    # noqa: E402
import p3_levers as P3L                   # noqa: E402
import p3c_freeze as P3C                  # noqa: E402
import p2_scalars as PS                   # noqa: E402
import e22_test_oneshot as E22            # noqa: E402
import r2_e7exact as E7X                  # noqa: E402

SC = ROOT / "results" / "r2" / "r1_system" / "rp" / "rp2" / "scores"
INV = ROOT / "results" / "r2" / "r0_data" / "chb" / "inventory.csv"
CASES_H = ROOT / "results" / "r2" / "r0_data" / "chb" / "inventory_cases.csv"
TAGS = ["clean_seed1", "clean_seed2", "clean_seed3", "clean_seed4"]
E16_GRID = ([1, 3, 5, 15], [0.05, 0.02, 0.01, 0.005, 0.002, 0.001])
D1B_GRID = (list(P3B.SMOOTHS), list(P3B.FINE))
PELT_POINTS = ((50.0, 2.0, 90), (75.0, 5.0, 300))
ARMS = {"frozen": (0.005, 0.005), "L2": (P3L.P_MIN, P3C.CAP), "L2f": (0.005, P3C.CAP), "S": (0.0075, P3C.CAP)}
DEV = list(E8.SUBJS)
TEST = list(E22.TEST)
D_RATE = 37.8 / 40.6                      # s per hour of EEG, 4 seeds, Kaggle (R1_SMOKE)
KAGGLE_CHB06_TOTAL = 105.0                 # s, first RP_SERIES run (log)
WIN = 4


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def world(x_by_seed, ict, fidx, ok, seed=0):
    """an npz world with the fields the components read (see the docstring for buffer / flag) + random D / Z."""
    rng = np.random.default_rng(seed)
    n = len(ict)
    buf = np.zeros(n, bool)
    for f in np.unique(fidx):
        m = np.flatnonzero(fidx == f)
        on = np.flatnonzero(np.diff(np.r_[0, ict[m].astype(int)]) == -1)      # first window after a seizure
        for e in on:
            buf[m[e:e + 3600]] = True
    buf &= ~ict
    fl5 = (rng.random(n) < 0.4) & ~ict & ~buf
    tmp = Path(tempfile.mkdtemp()) / "w.npz"
    np.savez(tmp, is_ictal=ict, is_buffer=buf, is_flag5sd=fl5, is_signal_loss=~ok, file_idx=fidx,
             files=np.array([f"f{i}.edf" for i in range(int(fidx.max()) + 1)]))
    z = np.load(tmp, allow_pickle=True)
    idx = np.flatnonzero(ok)
    D = {t: rng.gamma(4.0, 1.0, size=(len(idx), 18)) for t in TAGS}
    Z = {t: rng.normal(size=(len(idx), 18, 16)).astype(np.float32) for t in TAGS}
    ctx = dict(s="timing", z=z, idx=idx, D=D, Z={t: None for t in TAGS}, c8={}, p2={}, n=n, ok=ok, fidx=fidx,
               wf=fidx[idx], ict=ict, ict_ok=ict & ok, fl5=fl5, nonict=~ict & ~buf & ok,
               nh=float((~ict & ok).sum()) * WIN / 3600)
    return z, idx, ctx, D, Z


def grid(d, score, smooths, tops):
    old = (E1.SMOOTH, E1.TOPS)
    E1.SMOOTH, E1.TOPS = list(smooths), list(tops)
    try:
        return E1.event_grid(d, score)
    finally:
        E1.SMOOTH, E1.TOPS = old


def t_test(ctx, z, idx, D, kmap):
    t = time.perf_counter()
    for tag in TAGS:
        x = E22.final_scalar(ctx, tag)
        q = P3L.q_of(PS.smoothed(ctx, P3L.member_mean_z(ctx, tag), P3C.SMOOTH), kmap)
        rows, errs = [], []
        for name, (fl, cp) in ARMS.items():
            P3C.run_budget(ctx, "timing", tag, x, q, fl, cp, name, rows, errs)
        PS.smoothed(ctx, x, P3C.SMOOTH)
    with tempfile.TemporaryDirectory() as td:
        np.savez(Path(td) / "p2.npz", idx=idx, **{f"{t}_d": D[t].astype(np.float32) for t in TAGS})
    return time.perf_counter() - t


def t_e16(case, z, idx, ctx, Z):
    """e16_patient of src/r2_rps.py (its loop body; S9 base + arms a-e, grid, mechanism, diagnostics), 4 seeds."""
    t = time.perf_counter()
    d = E8.d_for_grid(z)
    n = len(d["is_ictal"]); ok = ~d["is_signal_loss"]
    fidx = z["file_idx"].astype(int); wf = fidx[idx]
    fl5 = z["is_flag5sd"].astype(bool); ict = z["is_ictal"].astype(bool) & ok
    nonict = ~z["is_ictal"].astype(bool) & ~z["is_buffer"].astype(bool) & ok

    def full(v):
        o = np.full(n, np.nan); o[idx] = v; o[~ok] = np.nanmedian(v); return o
    for tag in TAGS:
        D = ctx["D"][tag]
        scores = {"S9base": (E16.rz(full(E16.s_from_d(D)), ok), None)}
        for arm in ("a", "b", "c", "d", "e"):
            v_, extra_ = E16.c_scalar(arm, D, Z[tag], wf)
            scores[f"E16{arm}"] = (E16.rz(full(v_), ok), extra_)
        for kind, (v, extra) in scores.items():
            grid(d, v, *E16_GRID)
            float(np.nanmedian(v[ict])); float(np.nanmedian(v[nonict & fl5]))
            if kind == "S9base":
                sm = E11.smooth(v, ok, fidx)
                T = (sm > np.nanquantile(sm[ok], 0.98)) & nonict
                meds = pd.Series(v[nonict]).groupby(fidx[nonict]).median()
                topf = meds[meds >= meds.quantile(0.75)].index
                np.isin(fidx[T], topf).mean()
            elif extra is not None and extra[1].any():
                Da, bm = extra
                np.median(Da[bm].std(axis=0) / (Da[~bm & nonict[idx]].std(axis=0) + 1e-9))
    return time.perf_counter() - t


def t_t7(z, x_by_tag):
    """table7_patient parts, 4 seeds: locked PELT (2 points), E7 D2 exact (+ its scoring), E10 D1, E10 K."""
    d = E8.d_for_grid(z)
    D2 = E7X.d2_grid_exact(E7)
    ict = z["is_ictal"].astype(bool); buf = z["is_buffer"].astype(bool)
    art = z["is_flag5sd"].astype(bool); sl = z["is_signal_loss"].astype(bool)
    inter = (~ict) & (~buf) & (~art) & (~sl)
    out = dict(pelt=0.0, e7=0.0, e10d1=0.0, e10k=0.0, e7_calls=0, e7_exact_costs=0)
    for tag, x in x_by_tag.items():
        t = time.perf_counter()
        for mag, pen, ms in PELT_POINTS:
            V14.detect_events(x, pen, min_mag_pct=mag, local_win=15, inter_mask=inter, merge_s=ms)
        out["pelt"] += time.perf_counter() - t
        E7X.reset_stats()
        t = time.perf_counter()
        old = (E1.SMOOTH, E1.TOPS)
        E1.SMOOTH, E1.TOPS = list(E16_GRID[0]), list(E16_GRID[1])
        try:
            D2(d, x)
        finally:
            E1.SMOOTH, E1.TOPS = old
        out["e7"] += time.perf_counter() - t
        out["e7_calls"] += E7X.STATS["calls"]; out["e7_exact_costs"] += E7X.STATS["exact_costs"]
        t = time.perf_counter()
        for top in E10.TOPS:
            E10.score_events(z, E10.d1_events(z, x, top))
        out["e10d1"] += time.perf_counter() - t
        t = time.perf_counter()
        for pen in E10.PENS:
            segs = E10.k_segments(z, x, pen)
            allprom = np.array([pr for sg in segs.values() for (a, b, pr) in sg if pr > 0 and (b - a) * E10.WIN <= E10.MAXDUR])
            for p in E10.PS:
                thr = np.quantile(allprom, 1 - p) if len(allprom) else np.inf
                ev = {f: E10.merge([(a * E10.WIN, b * E10.WIN) for a, b, pr in sg
                                    if pr > 0 and pr >= thr and (b - a) * E10.WIN <= E10.MAXDUR]) for f, sg in segs.items()}
                E10.score_events(z, ev)
        out["e10k"] += time.perf_counter() - t
    return out


def t_d1b(z, x_by_tag):
    d = E8.d_for_grid(z)
    t = time.perf_counter()
    for x in x_by_tag.values():
        grid(d, x, *D1B_GRID)
    return time.perf_counter() - t


def load_scores(case):
    s = pd.read_csv(SC / f"{case}.csv.gz")
    return ({t: s[f"x_s{int(t[-1])}"].values.astype(np.float64) for t in TAGS}, s.ictal.values.astype(bool),
            s.file_idx.values.astype(int), s.ok.values.astype(bool))


def long_series(n_target, lengths):
    """real test series concatenated (chb06, chb15, chb03, chb18, chb13, chb14, chb17, chb16) and cut into the given file
    lengths (chb04's, from the R0 inventory) -> a series of chb04's length and file structure with real values."""
    xs = {t: [] for t in TAGS}; ic, ok = [], []
    for c in ("chb06", "chb15", "chb03", "chb18", "chb13", "chb14", "chb17", "chb16"):
        x, i, _, o = load_scores(c)
        for t in TAGS:
            xs[t].append(x[t])
        ic.append(i); ok.append(o)
    xs = {t: np.concatenate(v)[:n_target] for t, v in xs.items()}
    ic, ok = np.concatenate(ic)[:n_target], np.concatenate(ok)[:n_target]
    fidx = np.repeat(np.arange(len(lengths)), lengths)[:n_target]
    return xs, ic, fidx, ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "results" / "r2" / "r1_system" / "rps_fixb"))
    ap.add_argument("--project-only", action="store_true", help="recompute the projection from timing_components.csv")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.project_only:
        project(out)
        return
    rows = []
    kmap = 4.0
    # chb06: the longest real committed series
    x, ict, fidx, ok = load_scores("chb06")
    z, idx, ctx, D, Z = world(x, ict, fidx, ok)
    tt = t_test(ctx, z, idx, D, kmap)
    log(f"chb06 T_test {tt:.1f} s")
    te = t_e16("chb06", z, idx, ctx, Z)
    log(f"chb06 T_e16 {te:.1f} s")
    td = t_d1b(z, x)
    log(f"chb06 T_d1b {td:.1f} s")
    t7 = t_t7(z, x)
    log(f"chb06 T7 {t7}")
    rows.append(dict(series="chb06 (real)", windows=len(x["clean_seed1"]), files=int(fidx.max()) + 1, T_test=tt, T_e16=te,
                     T_d1b=td, **{f"T7_{k}": v for k, v in t7.items()}))
    # chb04-shaped series of real values
    inv = pd.read_csv(INV)
    lens = inv[(inv.case == "chb04") & inv.windows_4s.notna() & (inv.skipped_by_design != True)].windows_4s.astype(int).values  # noqa: E712
    n04 = int(lens.sum())
    x4, i4, f4, o4 = long_series(n04, lens)
    z4, idx4, ctx4, D4, Z4 = world(x4, i4, f4, o4, seed=1)
    t74 = t_t7(z4, x4)
    log(f"chb04-shaped T7 {t74}")
    td4 = t_d1b(z4, x4)
    te4 = t_e16("chb04", z4, idx4, ctx4, Z4)
    tt4 = t_test(ctx4, z4, idx4, D4, kmap)
    log(f"chb04-shaped T_test {tt4:.1f} T_e16 {te4:.1f} T_d1b {td4:.1f}")
    rows.append(dict(series="chb04-shaped (real values of 8 test series)", windows=n04, files=len(lens), T_test=tt4,
                     T_e16=te4, T_d1b=td4, **{f"T7_{k}": v for k, v in t74.items()}))
    comp = pd.DataFrame(rows)
    comp.to_csv(out / "timing_components.csv", index=False)
    project(out)


def project(out):
    """per case, from the two measured sizes: each component c(n) = c(chb06) x (n / n_chb06)^a, a fitted on the two
    sizes (power law; a >= 1 enforced, so a component is never projected cheaper per window on a smaller case); the
    distances from R1_SMOKE's Kaggle rate; Kaggle seconds = container seconds x the factor (docstring)."""
    comp = pd.read_csv(out / "timing_components.csv")
    r6, r4 = comp.iloc[0], comp.iloc[1]
    fac = (KAGGLE_CHB06_TOTAL - D_RATE * 66.7333) / float(r6.T_test)
    use = max(fac, 2.5)
    hours = pd.read_csv(CASES_H).set_index("case").hours_used_windows
    cols = {"test": "T_test", "e16": "T_e16", "d1b": "T_d1b", "pelt": "T7_pelt", "e7": "T7_e7", "e10": None}
    expo = {}
    for k, c in cols.items():
        a6 = float(r6[c]) if c else float(r6.T7_e10d1 + r6.T7_e10k)
        a4 = float(r4[c]) if c else float(r4.T7_e10d1 + r4.T7_e10k)
        expo[k] = (a6, max(1.0, float(np.log(a4 / a6) / np.log(r4.windows / r6.windows))))
    proj = []
    for c in DEV + TEST:
        n = float(hours[c]) * 900
        dev = c in DEV
        parts = {k: (expo[k][0] * (n / r6.windows) ** expo[k][1] if (dev or k == "test") else 0.0) for k in cols}
        parts["distances"] = D_RATE * float(hours[c]) / use
        cont = sum(parts.values())
        proj.append(dict(case=c, set="development" if dev else "test", hours=float(hours[c]), windows=int(n),
                         **{f"container_{k}_s": round(v, 1) for k, v in parts.items()}, container_s=round(cont, 1),
                         kaggle_s=round(cont * use, 0)))
    P = pd.DataFrame(proj).sort_values("kaggle_s", ascending=False)
    P.to_csv(out / "projection.csv", index=False)
    load = [0.0] * 4
    for s_ in P.kaggle_s:                                  # pass A: 4 workers, largest case first (R1._size order)
        load[int(np.argmin(load))] += s_
    other = dict(pass_b_c_h=0.3, flags_h=0.6, rp5_h=0.1, setup_gates_h=0.3)   # computed: see SUMMARY.md
    wall = max(load) / 3600 + sum(other.values())
    meta = dict(factor_measured=round(fac, 2), factor_used=round(use, 2), kaggle_chb06_total_s=KAGGLE_CHB06_TOTAL,
                distance_rate_s_per_h=round(D_RATE, 4), exponents={k: round(v[1], 2) for k, v in expo.items()},
                pass_a_wall_h_4_workers=round(max(load) / 3600, 2), pass_a_cpu_h=round(P.kaggle_s.sum() / 3600, 2),
                largest_case=P.iloc[0].case, largest_case_h=round(P.iloc[0].kaggle_s / 3600, 2), other_phases_h=other,
                notebook_wall_h=round(wall, 2), session_h=12, cpu=os.cpu_count(), numpy=np.__version__)
    (out / "projection.json").write_text(json.dumps(meta, indent=1))
    log(json.dumps(meta))
    print(P.to_string(index=False))


if __name__ == "__main__":
    main()
