#!/usr/bin/env python
"""
v9_x3_knn_b4.py -- V9-X3 (docs/prompts/V9_X3_CV_PREP.md), step 5 support: the kNN baseline (B4)
on IDENTICAL per-case inputs to the GAE-CV scoring in v9_x3_cv_eval.py -- same ctx construction
(v9_x3_cv_eval.case_ctx, in particular the SAME results/v9_x3/chb24.npz for chb24, not the
label-free xcache v9_e1_baselines.subject_ctx's EXT path uses for chb24), so the paired GAE-vs-
kNN comparison is not confounded by chb24 having a different window set / different raw
bp5+f7 features under the two methods.

B4 construction is UNCHANGED (v9_e1_baselines.d_knn / load_raw12_18, v9_e4_knn24.py's own
leave-one-case-out calibration pattern, read-only reuse): 12 raw per-channel features (bp5 5 +
f7 7), robust-z'd per channel per patient (label-free), Euclidean distance to the 10th nearest
neighbour in a random 20,000-window subsample of the same patient (|time offset| > 60 s
excluded), random_state=42. Only the ctx each case's features/window-set come from differs from
v9_e4_knn24.py (that script's chb24 goes through v9_e1_baselines.subject_ctx's EXT/xcache path).

Two things are computed here:
  1. B4 LEAVE-ONE-CASE-OUT (standalone kNN baseline, all 24 cases): for case s, k_B4(s) =
     p3_levers.calibrate() on the smoothed m(t) of every OTHER case (chb01/chb21 mutually
     excluded, same patient) -- v9_e4_knn24.calibrate()'s own rule, reproduced on this script's
     own (consistent) ctx/D. This is the "results/v9_e4/ leave-one-case-out" comparison point
     the prompt's step 5 asks for, recomputed so chb24 uses the same inputs as GAE-CV.
  2. GAE+kNN fusion ("F" arm) PER FOLD: v9_e1b_calibrate.f_signals(ctx, D_gae, D_b4) (percentile-
     mean final scalar, robust-z-mean budget signal -- unchanged), k_F calibrated ONCE PER FOLD
     on that fold's own training cases (label-free), exactly as v9_x3_cv_eval.py calibrates k_G --
     the prompt's own step 4 rule ("GAE + kNN uses the B4 recipe of results/v9_e1b/ with its k
     recalibrated the same way"). D_gae is read from v9_x3_cv_eval.py's cache
     (results/v9_x3/dumps/fold{k}_seed{seed}/{case}_D.npy) -- run v9_x3_cv_eval.py --calibrate/
     --score for every fold FIRST so every case's D_gae exists.

Run:
  python src/v9_x3_knn_b4.py --prep-all                 (B4 D + smoothed m for all 24 cases, cached)
  python src/v9_x3_knn_b4.py --loo                      (leave-one-case-out calibrate + score, 24 cases)
  python src/v9_x3_knn_b4.py --fuse --fold K --ckpt_dir DIR --seed 42   (F arm, one fold)
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB", ROOT / "src" / "phaseC",
          ROOT / "src" / "dataprep"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import p2_scalars as PS                # noqa: E402
import p3_levers as P3L                # noqa: E402
import v9_e1_baselines as V9E1         # noqa: E402
import v9_e1b_calibrate as V9E1B       # noqa: E402
import v9_x3_cv_eval as X3             # noqa: E402

OUT = ROOT / "results" / "v9_x3"
B4_D_DIR = OUT / "b4_cache"
SMOOTH, FLOOR, CAP = 5, 0.005, 0.02
ALL24 = [f"chb{i:02d}" for i in range(1, 25)]
SAME_SUBJECT = {"chb01", "chb21"}


def b4_D(case):
    """B4's per-channel kNN distance, cached once (fold-independent, label-free, patient-own).
    For the 23 thesis-split cases, case_ctx(case) IS v9_e1_baselines.subject_ctx(case) --
    IDENTICAL window set to what V9-E1 already cached in results/v9_e1/cache/{case}.npz (b4
    field; verified: same idx array). Reusing it avoids redoing ~20 NearestNeighbors fits/case.
    Only chb24 is recomputed from scratch here, since its V9-E1 cache used a different ctx
    (v9_e1_baselines.subject_ctx's EXT/xcache path, label-free stats -- see v9_x3_cv_eval.py's
    case_ctx / chb24_ctx docstrings) -- the one case this script's whole point is to fix."""
    fp = B4_D_DIR / f"{case}.npy"
    if fp.exists():
        return np.load(fp)
    if case != "chb24":
        old_cache = ROOT / "results" / "v9_e1" / "cache" / f"{case}.npz"
        z = np.load(old_cache)
        ctx_idx = X3.case_ctx(case)["idx"]
        if np.array_equal(z["idx"], ctx_idx):
            D = z["b4"].astype(np.float32)
            B4_D_DIR.mkdir(parents=True, exist_ok=True)
            np.save(fp, D)
            return D
        print(f"  {case}: V9-E1 cache idx differs from case_ctx -- recomputing B4 from scratch "
              f"(unexpected; investigate before trusting this case's B4 number)", flush=True)
    ctx = X3.case_ctx(case)
    F12, _, t_sec = V9E1.load_raw12_18(ctx)        # s=None -> always reads ctx["z"] (never the EXT/xcache branch)
    D = V9E1.d_knn(F12, t_sec)
    B4_D_DIR.mkdir(parents=True, exist_ok=True)
    np.save(fp, D.astype(np.float32))
    return D


def prep_all():
    t0 = time.time()
    for s in ALL24:
        tc = time.time()
        D = b4_D(s)
        print(f"  {s}: B4 D cached, shape {D.shape} ({time.time()-tc:.0f}s, total {time.time()-t0:.0f}s)",
              flush=True)


# ============================================================================ 1. B4 leave-one-case-out
def loo_calibrate():
    t0 = time.time()
    ms = {}
    for s in ALL24:
        ctx = X3.case_ctx(s)
        D = b4_D(s)
        m = PS.smoothed(ctx, V9E1.member_mean_z_from_D(ctx, D), SMOOTH)
        ms[s] = m
    k_loo = {}
    for s in ALL24:
        excl = {s} | (SAME_SUBJECT if s in SAME_SUBJECT else set())
        calib_set = [ms[t] for t in ALL24 if t not in excl]
        k_loo[s] = P3L.calibrate(calib_set)
        print(f"  k_B4(loo, {s}) = {k_loo[s]:.6f} ({len(calib_set)} other cases)", flush=True)
    cal = dict(k_loo=k_loo, floor=FLOOR, cap=CAP, smooth=SMOOTH, elapsed_s=time.time() - t0)
    (OUT / "b4_loo_calibration.json").write_text(json.dumps(cal, indent=1))
    print(f"wrote {OUT / 'b4_loo_calibration.json'} ({time.time()-t0:.0f}s)", flush=True)
    return k_loo


def loo_score():
    cal = json.loads((OUT / "b4_loo_calibration.json").read_text())
    k_loo = cal["k_loo"]
    rows, errs, dur_rows = [], [], []
    t0 = time.time()
    for s in ALL24:
        ctx = X3.case_ctx(s)
        D = b4_D(s)
        x = V9E1.final_scalar_from_D(ctx, D)
        m = V9E1.member_mean_z_from_D(ctx, D)
        out, ev, bins = X3.evaluate_full(ctx, x, m, k_loo[s])
        for stage, v in out.items():
            rows.append(dict(subject=s, stage=stage, **v))
        errs += [dict(subject=s, **e) for e in ev]
        for (lo, hi), (caught, n) in bins.items():
            dur_rows.append(dict(subject=s, lo=lo, hi=hi, caught=caught, n=n))
        print(f"  {s}: detector tp={out['detector']['tp']} fp={out['detector']['fp']}, "
              f"localized tp={out['localized']['tp']} fp={out['localized']['fp']} "
              f"({time.time()-t0:.0f}s)", flush=True)
    pd.DataFrame(rows).to_csv(OUT / "b4_loo_per_subject.csv", index=False)
    pd.DataFrame(errs).to_csv(OUT / "b4_loo_errors.csv", index=False)
    pd.DataFrame(dur_rows).to_csv(OUT / "b4_loo_duration_bins.csv", index=False)
    print(f"wrote {OUT / 'b4_loo_per_subject.csv'} (+ errors.csv, duration_bins.csv)")


# ============================================================================ 2. GAE + kNN fusion, per fold
def fuse_fold(fold, ckpt_dir, seed=42):
    man = X3.fold_manifest(fold)
    ck, meta = X3.load_fold_ckpt(ckpt_dir, fold, seed)
    t0 = time.time()
    mf_list = []
    for s in man["train_cases"]:
        ctx = X3.case_ctx(s)
        Dg = X3.dump_D(ctx, ck, meta, cache_key=f"fold{fold}_seed{seed}/{s}")
        Db = b4_D(s)
        _, mf = V9E1B.f_signals(ctx, Dg, Db)
        mf_list.append(PS.smoothed(ctx, mf, SMOOTH))
        print(f"  calibrate: {s} fused ({time.time()-t0:.0f}s)", flush=True)
    k_f = P3L.calibrate(mf_list)
    print(f"fold {fold} seed {seed}: k_F = {k_f:.6f} (median q_i = 0.005 over "
          f"{len(man['train_cases'])} training cases)", flush=True)

    rows, errs, dur_rows = [], [], []
    for s in man["held_out_cases"]:
        ctx = X3.case_ctx(s)
        Dg = X3.dump_D(ctx, ck, meta, cache_key=f"fold{fold}_seed{seed}/{s}")
        Db = b4_D(s)
        xf, mf = V9E1B.f_signals(ctx, Dg, Db)
        out, ev, bins = X3.evaluate_full(ctx, xf, mf, k_f)
        for stage, v in out.items():
            rows.append(dict(fold=fold, seed=seed, subject=s, stage=stage, **v))
        errs += [dict(fold=fold, seed=seed, subject=s, **e) for e in ev]
        for (lo, hi), (caught, n) in bins.items():
            dur_rows.append(dict(fold=fold, seed=seed, subject=s, lo=lo, hi=hi, caught=caught, n=n))
        print(f"  score: {s} detector tp={out['detector']['tp']} fp={out['detector']['fp']}, "
              f"localized tp={out['localized']['tp']} fp={out['localized']['fp']} "
              f"({time.time()-t0:.0f}s)", flush=True)
    (OUT / f"fold{fold}_seed{seed}_F_calibration.json").write_text(
        json.dumps(dict(fold=fold, seed=seed, k_F=k_f, train_cases=man["train_cases"]), indent=1))
    pd.DataFrame(rows).to_csv(OUT / f"fold{fold}_seed{seed}_F_per_subject.csv", index=False)
    pd.DataFrame(errs).to_csv(OUT / f"fold{fold}_seed{seed}_F_errors.csv", index=False)
    pd.DataFrame(dur_rows).to_csv(OUT / f"fold{fold}_seed{seed}_F_duration_bins.csv", index=False)
    print(f"wrote {OUT / f'fold{fold}_seed{seed}_F_per_subject.csv'} (+ errors.csv, duration_bins.csv)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prep-all", action="store_true")
    ap.add_argument("--loo", action="store_true")
    ap.add_argument("--fuse", action="store_true")
    ap.add_argument("--fold", type=int, choices=[1, 2, 3, 4])
    ap.add_argument("--ckpt_dir")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    if a.prep_all:
        prep_all()
    if a.loo:
        loo_calibrate()
        loo_score()
    if a.fuse:
        if not (a.fold and a.ckpt_dir):
            raise SystemExit("--fuse needs --fold and --ckpt_dir")
        fuse_fold(a.fold, a.ckpt_dir, a.seed)


if __name__ == "__main__":
    main()
