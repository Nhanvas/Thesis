#!/usr/bin/env python
"""
r2_rpsdevx_timing.py -- research track, stage RP, path 2: the diagnosis test of the slow RP_SERIES pass A (plan §12 15/11
10:30, D27-F). Build container, 1 process. TIMING ONLY: nothing scored here is read as a result.

Input: the RPS_DEVX export (results/r2/r1_system/rps_devx/scores_dev/<case>.csv.gz: the path-2 final scalar of the
development patients, seeds 1-4, and the window masks the detectors read). For each case and seed it times, separately and
in the order RP_SERIES runs them, the value-dependent components of the development branch (r2_rps.table7_patient and the
D1b grid), and records what explains their cost:
  locked PELT (cpd_pipeline_v14.detect_events, 2 points): seconds, timeline length n, PELT points (n / jump), change
     points found (cpd_pipeline_v14.detect_changepoints) -> H1 (pure-Python ruptures ~ quadratic when few change points);
  E7 D2 exact (r2_e7exact through E7's d2_grid, incl. scoring): seconds, calls, exact recomputations, the slowest call
     -> H2 (too many candidates recomputed exactly);
  E10 D1 + K, D1b grid: seconds -> H3.
The e16 arms are not value dependent (Ledoit-Wolf fits of fixed sizes; measured in results/r2/r1_system/rps_fixb/).
Rows are appended to <out>/devx_timing.csv as each component finishes, so a partial run is usable.
  python src/r2_rpsdevx_timing.py --cases chb23 chb01 chb10 --seeds 1 [--out results/r2/r1_system/rps_devx/timing_container]
"""
import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import e1_normal_definition as E1        # noqa: E402
import e10_kernel_cpd as E10             # noqa: E402
import e7_ensemble_cpd as E7             # noqa: E402
import e8_gae_v2_eval as E8              # noqa: E402
import cpd_pipeline_v14 as V14           # noqa: E402
import p3b_diag as P3B                   # noqa: E402
import r2_e7exact as E7X                 # noqa: E402

DEVX = ROOT / "results" / "r2" / "r1_system" / "rps_devx" / "scores_dev"
E16_GRID = ([1, 3, 5, 15], [0.05, 0.02, 0.01, 0.005, 0.002, 0.001])
D1B_GRID = (list(P3B.SMOOTHS), list(P3B.FINE))
PELT_POINTS = ((50.0, 2.0, 90), (75.0, 5.0, 300))


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


class Z(dict):
    files = ("is_ictal", "is_buffer", "is_flag5sd", "is_signal_loss", "file_idx")


def load(case, devx=DEVX):
    s = pd.read_csv(Path(devx) / f"{case}.csv.gz", float_precision="round_trip")
    z = Z(is_ictal=s.ictal.values.astype(bool), is_buffer=s.buffer.values.astype(bool),
          is_flag5sd=s.flag5sd.values.astype(bool), is_signal_loss=~s.ok.values.astype(bool),
          file_idx=s.file_idx.values.astype(int))
    return z, {k: s[f"x_s{k}"].values.astype(np.float64) for k in (1, 2, 3, 4)}


def grid(d, x, smooths, tops):
    old = (E1.SMOOTH, E1.TOPS)
    E1.SMOOTH, E1.TOPS = list(smooths), list(tops)
    try:
        return E1.event_grid(d, x)
    finally:
        E1.SMOOTH, E1.TOPS = old


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", nargs="+", required=True)
    ap.add_argument("--seeds", nargs="+", type=int, default=[1])
    ap.add_argument("--out", default=str(ROOT / "results" / "r2" / "r1_system" / "rps_devx" / "timing_container"))
    ap.add_argument("--skip", nargs="*", default=[], help="components to skip: pelt e7 e10 d1b")
    ap.add_argument("--devx", default=str(DEVX), help="folder of the RPS_DEVX export (scores_dev)")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    f = out / "devx_timing.csv"
    D2 = E7X.d2_grid_exact(E7)

    def put(row):
        pd.DataFrame([row]).to_csv(f, mode="a", header=not f.exists(), index=False)
        log(row)
    for case in a.cases:
        z, X = load(case, a.devx)
        d = E8.d_for_grid(z)
        ict, buf, art, sl = z["is_ictal"], z["is_buffer"], z["is_flag5sd"], z["is_signal_loss"]
        inter = (~ict) & (~buf) & (~art) & (~sl)
        n = len(ict)
        for k in a.seeds:
            x = X[k]
            base = dict(case=case, seed=k, windows=n, files=int(np.unique(z["file_idx"]).size), cpu=os.cpu_count())
            if "pelt" not in a.skip:
                for mag, pen, ms in PELT_POINTS:
                    t = time.perf_counter()
                    cps, _ = V14.detect_changepoints(x, pen, mag, 15, inter)
                    tc = time.perf_counter() - t
                    put(dict(base, component=f"pelt_locked_{int(mag)}_{pen}", seconds=round(tc, 2),
                             pelt_points=n // V14.PELT_JUMP, changepoints=len(cps), inter_windows=int(inter.sum())))
            if "e7" not in a.skip:
                E7X.reset_stats()
                t = time.perf_counter()
                old = (E1.SMOOTH, E1.TOPS)
                E1.SMOOTH, E1.TOPS = list(E16_GRID[0]), list(E16_GRID[1])
                try:
                    D2(d, x)
                finally:
                    E1.SMOOTH, E1.TOPS = old
                put(dict(base, component="e7_d2_exact", seconds=round(time.perf_counter() - t, 2), **E7X.STATS))
            if "e10" not in a.skip:
                t = time.perf_counter()
                for top in E10.TOPS:
                    E10.score_events(z, E10.d1_events(z, x, top))
                t1 = time.perf_counter()
                for pen in E10.PENS:
                    segs = E10.k_segments(z, x, pen)
                    allprom = np.array([pr for sg in segs.values() for (a_, b_, pr) in sg if pr > 0 and (b_ - a_) * E10.WIN <= E10.MAXDUR])
                    for p in E10.PS:
                        thr = np.quantile(allprom, 1 - p) if len(allprom) else np.inf
                        ev = {f_: E10.merge([(a_ * E10.WIN, b_ * E10.WIN) for a_, b_, pr in sg
                                             if pr > 0 and pr >= thr and (b_ - a_) * E10.WIN <= E10.MAXDUR]) for f_, sg in segs.items()}
                        E10.score_events(z, ev)
                put(dict(base, component="e10_d1", seconds=round(t1 - t, 2)))
                put(dict(base, component="e10_k", seconds=round(time.perf_counter() - t1, 2)))
            if "d1b" not in a.skip:
                t = time.perf_counter()
                grid(d, x, *D1B_GRID)
                put(dict(base, component="d1b_grid", seconds=round(time.perf_counter() - t, 2)))


if __name__ == "__main__":
    main()
