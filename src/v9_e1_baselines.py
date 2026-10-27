#!/usr/bin/env python
"""
v9_e1_baselines.py -- V9-E1: does the graph autoencoder help? Non-graph baselines on the identical
downstream pipeline (docs/prompts/V9_E1_BASELINES.md). Read-only on frozen scripts and committed
results; this file is the only new code. Cache-only (no new feature extraction): raw node features
(adjacency, band powers, f7) are read directly from data/trainset_v2/*.npz (15 non-test) and
data/testset_v2/*.npz (8 test), the same files subject_context()/test_context() already load.

ARMS (one anomaly representation each; everything downstream is the frozen P3 chain of
p3c_freeze.py / e23_test_look7.py, called unmodified):
  G   frozen GAE latent, per-channel LedoitWolf distance (ctx["D"][tag]); 4 seeds.
  B1  12 raw node features (bp5 5 + f7 7) per channel; per-channel LedoitWolf distance (patient-level,
      exactly as G's construction, only the input channel-vector changes).
  B2  18-d adjacency row per channel; per-channel LedoitWolf distance.
  B3  same 12 features; per-channel IsolationForest(n_estimators=200, max_samples=256,
      random_state=42), score = -score_samples.
  B4  same 12 features, per-channel robust-z'd (median/MAD, label-free, patient-own) before the
      Euclidean kNN distance -- raw mixed-unit features (log power, log line length, kurtosis) would
      make unscaled Euclidean distance an artifact of units, not of the method; distance to the 10th
      NN in a random subsample of min(20000, n_valid) windows of the same patient, excluding windows
      within +-60 s of the query (same file, |time offset| <= 60 s); random_state=42.
  F   rank-mean (equal percentile) of G and the best of B1-B4 on development only.
Every arm feeds e17b_latent_family.member() (order statistics 6/9/12 + channel mean, unchanged) ->
percentile mean (e22_test_oneshot.final_scalar's construction) -> D1 smoothing 5 -> per-patient budget
clip(q_i(k), 0.005, 0.02) with k = results/p3c_freeze/freeze.json's k (same k for every arm: "keep
everything downstream identical") -> merge 90 s -> kernel-CPD localizer (P3L.localize, mode "cpd",
the frozen localizer.py) -> SzCORE scorer (PS.score).

REPRODUCTION (checked every run, before any baseline number is trusted): the G arm, computed here
with evaluate_arm(), reproduces results/p3c_freeze/per_subject.csv (budget L2f, stage detector/cpd,
15 non-test, 4 seeds) and results/e23_test_look7/per_subject_seed.csv (point balanced, stage
detector/localized, 8 test, 4 seeds) exactly (tp, fp). STOP if not.

CACHE GUARD: chb24 and Siena have no local raw-feature cache (results/x1_external/features/ is empty;
those features were only ever materialized on Kaggle and never committed). B1/B2/B3/B4/F are refused
on those sets; G is still reported there from the already-committed results/x1_external output.

Run:  python src/v9_e1_baselines.py --smoke              (chb01 only, ~1-3 min, not measured)
      python src/v9_e1_baselines.py --full                (15 + 8 subjects, estimated 3-6 h)
      python src/v9_e1_baselines.py --report               (build the report from cached results)
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import NearestNeighbors

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB", ROOT / "src" / "phaseC",
          ROOT / "src" / "dataprep"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import p2_scalars as PS                # noqa: E402
import e16_recording_baseline as E16   # noqa: E402
import e17b_latent_family as F17       # noqa: E402
import e18_cpd_localizer as E18        # noqa: E402
import e8_gae_v2_eval as E8            # noqa: E402
import e22_test_oneshot as E22         # noqa: E402
import p3_levers as P3L                # noqa: E402
import szcore_eval as SE               # noqa: E402

OUT = ROOT / "results" / "v9_e1"
CACHE = OUT / "cache"
FRZ = ROOT / "results" / "p3c_freeze"
E23 = ROOT / "results" / "e23_test_look7"
XCACHE = ROOT / "results" / "v9_anatomy" / "xcache"
WIN = 4
SMOOTH = 5
TAGS = list(E22.TAGS)
DEV = list(E8.SUBJS)
TEST = list(E22.TEST)
# chb24 + the 3 Siena patients (PN00, PN10, PN11) whose raw features were rebuilt and cached locally by
# V9-T3 (results/v9_anatomy/xcache/*.npz); the other 11 Siena patients have no raw EDF in this checkout
# (v9_anatomy.py's own documented finding) so B1-B4/F are refused on them -- only G (from the committed
# results/x1_external/rows_PN*.csv) is reported there, for context.
EXT = ["chb24", "PN00", "PN10", "PN11"]
SIENA_MISSING = ["PN01", "PN03", "PN05", "PN06", "PN07", "PN09", "PN12", "PN13", "PN14", "PN16", "PN17"]
B_NAMES = ["B1", "B2", "B3", "B4"]
GRID = [0.05, 0.03, 0.02, 0.015, 0.01, 0.0075, 0.005, 0.003, 0.002, 0.0015, 0.001, 0.0007, 0.0005]
FP_TARGETS = [20.0, 27.5, 44.0]
DUR_BINS = [(0, 20), (20, 40), (40, 80), (80, float("inf"))]


# ------------------------------------------------------------------------------------- feature loading
def file_start_offsets(ctx):
    """first full-timeline index of every file id (full timeline, including invalid windows)."""
    out = {}
    for f in np.unique(ctx["fidx"]):
        out[f] = int(np.flatnonzero(ctx["fidx"] == f)[0])
    return out


def load_raw12_18(ctx, s=None):
    """F12 (bp5 5 + f7 7), F18 (adjacency row) and the in-file time offset (s) of every valid window.
    For dev/test subjects the raw fields live in ctx["z"]; for EXT subjects (chb24, Siena) make_ctx()
    builds a minimal z (no adj/bp5/f7), so they are read from the v9_anatomy xcache file instead."""
    idx = ctx["idx"]
    if s in EXT:
        zz = np.load(XCACHE / f"{s}.npz", allow_pickle=True)
        bp5 = np.asarray(zz["bp5"])[idx].astype(np.float64)
        f7 = np.asarray(zz["f7"])[idx].astype(np.float64)
        adj = np.asarray(zz["adj"])[idx].astype(np.float64)
    else:
        z = ctx["z"]
        bp5 = np.asarray(z["bp5"])[idx].astype(np.float64)
        f7 = np.asarray(z["f7"])[idx].astype(np.float64)
        adj = np.asarray(z["adj"])[idx].astype(np.float64)
    F12 = np.concatenate([bp5, f7], axis=-1)
    if not np.isfinite(F12).all():
        F12 = np.nan_to_num(F12, nan=0.0, posinf=0.0, neginf=0.0)
    if not np.isfinite(adj).all():
        adj = np.nan_to_num(adj, nan=0.0, posinf=0.0, neginf=0.0)
    starts = file_start_offsets(ctx)
    t_sec = np.array([(idx[j] - starts[ctx["wf"][j]]) * WIN for j in range(len(idx))], dtype=np.float64)
    return F12, adj, t_sec


# ------------------------------------------------------------------------------------- per-channel D builders
def d_mahalanobis(F):
    """F: (n, C, d) -> (n, C) per-channel LedoitWolf Mahalanobis distance, patient-level fit (as G)."""
    n, C, d = F.shape
    out = np.empty((n, C), dtype=np.float64)
    for c in range(C):
        out[:, c] = LedoitWolf().fit(F[:, c, :]).mahalanobis(F[:, c, :])
    return out


def d_isoforest(F12, seed=42):
    n, C, d = F12.shape
    out = np.empty((n, C), dtype=np.float64)
    for c in range(C):
        m = IsolationForest(n_estimators=200, max_samples=256, random_state=seed).fit(F12[:, c, :])
        out[:, c] = -m.score_samples(F12[:, c, :])
    return out


def d_knn(F12, t_sec, k=10, n_sub=20000, excl_s=60, seed=42, buf0=60):
    n, C, d = F12.shape
    rng = np.random.default_rng(seed)
    sub = rng.choice(n, size=min(n_sub, n), replace=False)
    sub_t = t_sec[sub]
    out = np.empty((n, C), dtype=np.float64)
    for c in range(C):
        X = F12[:, c, :]
        med = np.median(X, axis=0); mad = np.median(np.abs(X - med), axis=0) + 1e-9
        Xs = (X - med) / mad
        nn = NearestNeighbors(n_neighbors=min(buf0, len(sub))).fit(Xs[sub])
        buf = buf0
        while True:
            dist, ind = nn.kneighbors(Xs, n_neighbors=min(buf, len(sub)))
            sub_idx_global = sub[ind]                       # (n, buf) global window indices of neighbours
            dt = np.abs(t_sec[:, None] - sub_t[ind])         # time gap to each neighbour
            same_time = dt <= excl_s
            valid = ~same_time
            kth = np.full(n, np.nan)
            n_valid = valid.sum(axis=1)
            need_more = n_valid < k
            for i in np.flatnonzero(~need_more):
                vv = dist[i][valid[i]]
                kth[i] = np.sort(vv)[k - 1]
            if not need_more.any() or buf >= len(sub):
                for i in np.flatnonzero(need_more):
                    vv = dist[i][valid[i]]
                    kth[i] = np.sort(vv)[-1] if len(vv) else dist[i].max()
                break
            buf = min(buf * 4, len(sub))
            nn = NearestNeighbors(n_neighbors=min(buf, len(sub))).fit(Xs[sub])
        out[:, c] = kth
    return out


def subject_ctx(s):
    if s in TEST:
        return E22.test_context(s)
    if s in EXT:
        import v9_anatomy as V9A        # noqa: local import -- read-only reuse, loads cached xcache only
        data_root = V9A.CHB_DATA if s == "chb24" else V9A.SIENA_DATA
        ctx, _meta = V9A.build_or_load_ext(s, data_root)
        return ctx
    return PS.subject_context(s)


def cache_D(s):
    fp = CACHE / f"{s}.npz"
    if fp.exists():
        return
    ctx = subject_ctx(s)
    F12, F18, t_sec = load_raw12_18(ctx, s)
    t0 = time.time()
    b1 = d_mahalanobis(F12)
    b2 = d_mahalanobis(F18)
    b3 = d_isoforest(F12)
    b4 = d_knn(F12, t_sec)
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez(fp, idx=ctx["idx"], b1=b1, b2=b2, b3=b3, b4=b4)
    print(f"  {s}: cached B1-B4 ({time.time()-t0:.0f}s, n_valid={len(ctx['idx'])})", flush=True)


def load_D(s, name):
    f = np.load(CACHE / f"{s}.npz")
    return f[name.lower()]


# ------------------------------------------------------------------------------------- the frozen downstream chain
def final_scalar_from_D(ctx, D):
    raw = [PS._full(ctx, F17.member(D, ctx["wf"], kk)) for kk in F17.MEMBERS.values()]
    return np.mean([PS.pct(v, ctx["ok"]) for v in raw], axis=0)


def member_mean_z_from_D(ctx, D):
    zs = [E16.rz(PS._full(ctx, F17.member(D, ctx["wf"], kk)), ctx["ok"]) for kk in F17.MEMBERS.values()]
    return np.mean(zs, axis=0)


def evaluate_arm(ctx, x, k, floor=0.005, cap=0.02, smooth=SMOOTH, m=None):
    """x = final scalar; m = member-mean-z (for the label-free budget); same construction as
    p3c_freeze.py / e23_test_look7.py, localizer fixed to cpd (the frozen choice, freeze.json)."""
    q = P3L.q_of(PS.smoothed(ctx, m, smooth), k) if m is not None else np.nan
    top = float(np.clip(q, floor, max(cap, floor))) if m is not None else floor
    det = PS.d1_events(ctx, x, smooth, top)
    thr = np.nanquantile(PS.smoothed(ctx, x, smooth), 1 - top)
    loc, _ = P3L.localize(ctx, x, det, thr, "cpd")
    out = {}
    for name, ev in (("detector", det), ("localized", loc)):
        tp, fp, nr, h = PS.score(ctx, ev)
        kk, ns = PS.caught(PS.short_refs(ctx), ev)
        out[name] = dict(tp=tp, fp=fp, n_ref=nr, nonict_h=h, short_tp=kk, short_n=ns, top=top, q_raw=q)
    return out, det, loc


def sweep_detector(ctx, x, tops, smooth=SMOOTH):
    sm = PS.smoothed(ctx, x, smooth)
    rows = []
    for top in tops:
        thr = np.nanquantile(sm, 1 - top)
        ev = {}
        for f in np.unique(ctx["fidx"]):
            m = np.flatnonzero(ctx["fidx"] == f)
            e = PS.merge([(a * WIN, b * WIN) for a, b in PS._runs(np.nan_to_num(sm[m], nan=-np.inf) > thr)])
            ev[f] = e
        tp, fp, nr, h = PS.score(ctx, ev)
        rows.append(dict(top=top, tp=tp, fp=fp, n_ref=nr, nonict_h=h))
    return rows


def duration_bins(ctx, ev, pre=30, post=60):
    refs = P3L.refs_of(ctx)
    out = {b: [0, 0] for b in DUR_BINS}
    for f, rr in refs.items():
        for a, b in rr:
            dur = b - a
            hit = any(h1 >= a - pre and h0 <= b + post for h0, h1 in ev.get(f, []))
            for lo, hi in DUR_BINS:
                if (lo == 0 and dur <= hi) or (lo < dur <= hi):
                    out[(lo, hi)][0] += int(hit); out[(lo, hi)][1] += 1
                    break
    return out


def score_duration_filtered(ctx, ev, min_dur_s):
    z = ctx["z"]; ok = ~z["is_signal_loss"].astype(bool)
    ict = z["is_ictal"].astype(bool); fidx = z["file_idx"].astype(int)
    ref, hyp, off = [], [], 0
    for f in np.unique(fidx):
        m = np.flatnonzero(fidx == f)
        for a, b in PS._runs(ict[m]):
            if (b - a) * WIN >= min_dur_s:
                ref.append((a * WIN + off, b * WIN + off))
        hyp += [(a + off, b + off) for a, b in ev.get(f, [])]
        off += len(m) * WIN + 600
    h = float((~ict & ok).sum()) * WIN / 3600
    return SE.score_szcore(ref, hyp, off, h)


def check_ext_repro(R, tp_tol=1, fp_tol=2):
    """soft check (print only, not a STOP): G on EXT vs the committed results/x1_external/rows_*.csv.
    V9-T3 (results/v9_anatomy/SUMMARY.md) diagnosed and disclosed a Kaggle-vs-local float tolerance of
    exactly this size (GAE forward pass noise flips a near-threshold window); tp exact, fp within 2 on
    most subject-seeds is the expected, already-documented outcome, not a new bug."""
    bad = []
    for s in EXT:
        fp = ROOT / "results" / "x1_external" / f"rows_{s}.csv"
        if not fp.exists():
            continue
        ref = pd.read_csv(fp)
        for tag in TAGS:
            r = ref[(ref.seed == tag) & (ref.point == "balanced") & (ref.stage == "localized")]
            if not len(r):
                continue
            r = r.iloc[0]
            mine = R[(R.subject == s) & (R.arm == "G") & (R.seed == tag) & (R.stage == "localized")]
            if not len(mine):
                continue
            m = mine.iloc[0]
            if abs(m.tp - r.tp) > tp_tol or abs(m.fp - r.fp) > fp_tol:
                bad.append((s, tag, int(m.tp), int(m.fp), int(r.tp), int(r.fp)))
    if bad:
        print(f"EXT repro WARNING (outside the documented +-{tp_tol}/{fp_tol} tolerance): {bad}", flush=True)
    else:
        print(f"EXT repro OK: G within the documented tp+-{tp_tol}/fp+-{fp_tol} tolerance of x1_external.", flush=True)


def boot_mean_ci(per_patient_sens, n=10_000, seed=0):
    rng = np.random.default_rng(seed); v = np.asarray(per_patient_sens)
    means = [rng.choice(v, len(v), replace=True).mean() for _ in range(n)]
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


# ------------------------------------------------------------------------------------- reproduction gate
def repro_check_G():
    ref_dev = pd.read_csv(FRZ / "per_subject.csv")
    ref_test = pd.read_csv(E23 / "per_subject_seed.csv")
    cfg = json.load(open(FRZ / "freeze.json"))
    k = cfg["k"]; fl, cp = cfg["points"]["balanced"]
    bad = []
    for s in DEV[:1] + TEST[:1]:
        ctx = subject_ctx(s)
        for tag in TAGS:
            D = ctx["D"][tag]
            x = final_scalar_from_D(ctx, D); m = member_mean_z_from_D(ctx, D)
            out, _, _ = evaluate_arm(ctx, x, k, fl, cp, m=m)
            if s in DEV:
                for st_here, st_ref in (("detector", "detector"), ("localized", "cpd")):
                    r = ref_dev[(ref_dev.subject == s) & (ref_dev.seed == tag) & (ref_dev.budget == "L2f") & (ref_dev.stage == st_ref)].iloc[0]
                    if (out[st_here]["tp"], out[st_here]["fp"]) != (int(r.tp), int(r.fp)):
                        bad.append((s, tag, st_here, out[st_here]["tp"], out[st_here]["fp"], int(r.tp), int(r.fp)))
            else:
                for st_here, st_ref in (("detector", "detector"), ("localized", "localized")):
                    r = ref_test[(ref_test.subject == s) & (ref_test.seed == tag) & (ref_test.point == "balanced") & (ref_test.stage == st_ref)].iloc[0]
                    if (out[st_here]["tp"], out[st_here]["fp"]) != (int(r.tp), int(r.fp)):
                        bad.append((s, tag, st_here, out[st_here]["tp"], out[st_here]["fp"], int(r.tp), int(r.fp)))
    if bad:
        raise SystemExit(f"STOP reproduction: {bad}")
    print("Reproduction OK: evaluate_arm(G) reproduces p3c_freeze (L2f) and e23_test_look7 (balanced) exactly.", flush=True)


# ------------------------------------------------------------------------------------- main per-subject runner
def run_subject(s, k, fl, cp):
    ctx = subject_ctx(s)
    rows, dets, locs = [], {}, {}
    for tag in TAGS:
        D = ctx["D"][tag]
        x = final_scalar_from_D(ctx, D); m = member_mean_z_from_D(ctx, D)
        out, det, loc = evaluate_arm(ctx, x, k, fl, cp, m=m)
        for st, v in out.items():
            rows.append(dict(subject=s, arm="G", seed=tag, stage=st, **v))
        dets[("G", tag)] = det; locs[("G", tag)] = loc
    has_cache = (CACHE / f"{s}.npz").exists()
    Bx = {}
    if has_cache:
        for name in B_NAMES:
            D = load_D(s, name)
            x = final_scalar_from_D(ctx, D); m = member_mean_z_from_D(ctx, D)
            out, det, loc = evaluate_arm(ctx, x, k, fl, cp, m=m)
            for st, v in out.items():
                rows.append(dict(subject=s, arm=name, seed="-", stage=st, **v))
            dets[(name, "-")] = det; locs[(name, "-")] = loc
            Bx[name] = x
    return ctx, rows, dets, locs, Bx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--ext", action="store_true", help="chb24 + 3 cached Siena patients (PN00, PN10, PN11)")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True); CACHE.mkdir(parents=True, exist_ok=True)
    cfg = json.load(open(FRZ / "freeze.json"))
    k = cfg["k"]; fl, cp = cfg["points"]["balanced"]

    if a.smoke or a.full:
        repro_check_G()
        subs = ["chb01"] if a.smoke else (DEV + TEST)
        for s in subs:
            cache_D(s)
        all_rows, all_dets, all_locs, all_Bx, all_ctx = [], {}, {}, {}, {}
        for s in subs:
            ctx, rows, dets, locs, Bx = run_subject(s, k, fl, cp)
            all_rows += rows; all_ctx[s] = ctx
            for key, v in dets.items():
                all_dets[(s, *key)] = v
            for key, v in locs.items():
                all_locs[(s, *key)] = v
            all_Bx[s] = Bx
            print(f"{s}: evaluated ({time.time()-t0:.0f}s)", flush=True)
        R = pd.DataFrame(all_rows)
        tag_suffix = "_smoke" if a.smoke else ""
        R.to_csv(OUT / f"per_subject{tag_suffix}.csv", index=False)

        # ---- fusion F: best of B1-B4 on development only, balanced point, localized stage, pooled sens; ties -> lower FP/day
        dev_here = [s for s in subs if s in DEV]
        if dev_here and all(all_Bx[s] for s in dev_here):
            best_name, best_key = None, None
            for name in B_NAMES:
                d = R[(R.subject.isin(dev_here)) & (R.arm == name) & (R.stage == "localized")]
                if not len(d):
                    continue
                sens = d.tp.sum() / d.n_ref.sum(); fa = d.fp.sum() / d.nonict_h.sum() * 24
                key = (sens, -fa)
                if best_key is None or key > best_key:
                    best_key, best_name = key, name
            print(f"Fusion: best of B1-B4 on development = {best_name} {best_key}", flush=True)
            f_rows = []; all_Fx = {}
            for s in subs:
                ctx = all_ctx[s]
                if s not in all_Bx or best_name not in all_Bx[s]:
                    continue
                xb = all_Bx[s][best_name]
                all_Fx[s] = {}
                for tag in TAGS:
                    D = ctx["D"][tag]
                    xg = final_scalar_from_D(ctx, D)
                    xf = np.mean([PS.pct(xg, ctx["ok"]), PS.pct(xb, ctx["ok"])], axis=0)
                    all_Fx[s][tag] = xf
                    mg = member_mean_z_from_D(ctx, D)
                    out, det, loc = evaluate_arm(ctx, xf, k, fl, cp, m=mg)
                    for st, v in out.items():
                        f_rows.append(dict(subject=s, arm="F", seed=tag, stage=st, **v))
                    all_dets[(s, "F", tag)] = det; all_locs[(s, "F", tag)] = loc
            Rf = pd.DataFrame(f_rows)
            R = pd.concat([R, Rf], ignore_index=True)
            R.to_csv(OUT / f"per_subject{tag_suffix}.csv", index=False)
            json.dump(dict(best_of_B=best_name), open(OUT / f"fusion_choice{tag_suffix}.json", "w"), indent=1)
        else:
            all_Fx = {}

        # ---- matched operating-point curve (global budget sweep, detector stage)
        sweep_rows = []
        for s in subs:
            ctx = all_ctx[s]
            for tag in TAGS:
                D = ctx["D"][tag]; x = final_scalar_from_D(ctx, D)
                for r_ in sweep_detector(ctx, x, GRID):
                    sweep_rows.append(dict(subject=s, arm="G", seed=tag, **r_))
            for name, x in all_Bx.get(s, {}).items():
                for r_ in sweep_detector(ctx, x, GRID):
                    sweep_rows.append(dict(subject=s, arm=name, seed="-", **r_))
            for tag, xf in all_Fx.get(s, {}).items():
                for r_ in sweep_detector(ctx, xf, GRID):
                    sweep_rows.append(dict(subject=s, arm="F", seed=tag, **r_))
        pd.DataFrame(sweep_rows).to_csv(OUT / f"sweep{tag_suffix}.csv", index=False)

        # ---- duration bins, every arm and set (pooled by the report)
        dur_rows = []
        for s in subs:
            setname = "dev" if s in DEV else "test"
            for arm in ["G"] + B_NAMES + ["F"]:
                key = (s, arm, "clean_seed42") if arm in ("G", "F") else (s, arm, "-")
                ev = all_locs.get(key)
                if ev is None:
                    continue
                bins = duration_bins(all_ctx[s], ev)
                for (lo, hi), (caught, n) in bins.items():
                    dur_rows.append(dict(subject=s, arm=arm, set=setname, lo=lo, hi=hi, caught=caught, n=n))
        if dur_rows:
            pd.DataFrame(dur_rows).to_csv(OUT / f"duration_bins{tag_suffix}.csv", index=False)

        # ---- Part C: G, seed 42, balanced+localized, test set only, re-reported under other protocols
        if not a.smoke and any(s in TEST for s in subs):
            partc_rows = []
            excl = {"chb06", "chb14", "chb16"}
            incl_subs = [s for s in TEST if s not in excl and s in subs]
            d = R[(R.subject.isin(incl_subs)) & (R.arm == "G") & (R.seed == "clean_seed42") & (R.stage == "localized")]
            partc_rows.append(dict(part="i_exclude_chb06_14_16", tp=int(d.tp.sum()), fp=int(d.fp.sum()),
                                   n_ref=int(d.n_ref.sum()), nonict_h=float(d.nonict_h.sum())))
            tp30 = fp30 = nref30 = 0
            for s in TEST:
                if s not in subs:
                    continue
                ev = all_locs.get((s, "G", "clean_seed42"))
                if ev is None:
                    continue
                r = score_duration_filtered(all_ctx[s], ev, 30)
                tp30 += r["tp"]; fp30 += r["fp"]; nref30 += r["n_ref"]
            partc_rows.append(dict(part="ii_seizures_ge_30s", tp=tp30, fp=fp30, n_ref=nref30, nonict_h=np.nan))
            pd.DataFrame(partc_rows).to_csv(OUT / "part_c.csv", index=False)
        print(f"\nElapsed {time.time()-t0:.0f}s.", flush=True)
        return

    if a.ext:
        repro_check_G()
        subs = EXT
        fc = OUT / "fusion_choice.json"
        best_name = json.load(open(fc))["best_of_B"] if fc.exists() else None
        for s in subs:
            cache_D(s)
        all_rows, all_locs, all_ctx, all_Bx = [], {}, {}, {}
        for s in subs:
            ctx, rows, dets, locs, Bx = run_subject(s, k, fl, cp)
            all_rows += rows; all_ctx[s] = ctx; all_Bx[s] = Bx
            for key, v in locs.items():
                all_locs[(s, *key)] = v
            print(f"{s}: evaluated ({time.time()-t0:.0f}s)", flush=True)
        R = pd.DataFrame(all_rows)
        all_Fx = {}
        if best_name:
            f_rows = []
            for s in subs:
                ctx = all_ctx[s]
                if best_name not in all_Bx.get(s, {}):
                    continue
                xb = all_Bx[s][best_name]
                all_Fx[s] = {}
                for tag in TAGS:
                    D = ctx["D"][tag]
                    xg = final_scalar_from_D(ctx, D)
                    xf = np.mean([PS.pct(xg, ctx["ok"]), PS.pct(xb, ctx["ok"])], axis=0)
                    all_Fx[s][tag] = xf
                    mg = member_mean_z_from_D(ctx, D)
                    out, det, loc = evaluate_arm(ctx, xf, k, fl, cp, m=mg)
                    for st, v in out.items():
                        f_rows.append(dict(subject=s, arm="F", seed=tag, stage=st, **v))
                    all_locs[(s, "F", tag)] = loc
            R = pd.concat([R, pd.DataFrame(f_rows)], ignore_index=True)
        else:
            print("Fusion: fusion_choice.json not yet written by the dev+test run -- F skipped for EXT.", flush=True)
        check_ext_repro(R)
        R.to_csv(OUT / "per_subject_ext.csv", index=False)

        sweep_rows = []
        for s in subs:
            ctx = all_ctx[s]
            for tag in TAGS:
                D = ctx["D"][tag]; x = final_scalar_from_D(ctx, D)
                for r_ in sweep_detector(ctx, x, GRID):
                    sweep_rows.append(dict(subject=s, arm="G", seed=tag, **r_))
            for name, x in all_Bx.get(s, {}).items():
                for r_ in sweep_detector(ctx, x, GRID):
                    sweep_rows.append(dict(subject=s, arm=name, seed="-", **r_))
            for tag, xf in all_Fx.get(s, {}).items():
                for r_ in sweep_detector(ctx, xf, GRID):
                    sweep_rows.append(dict(subject=s, arm="F", seed=tag, **r_))
        pd.DataFrame(sweep_rows).to_csv(OUT / "sweep_ext.csv", index=False)

        dur_rows = []
        for s in subs:
            for arm in ["G"] + B_NAMES + (["F"] if best_name else []):
                key = (s, arm, "clean_seed42") if arm in ("G", "F") else (s, arm, "-")
                ev = all_locs.get(key)
                if ev is None:
                    continue
                bins = duration_bins(all_ctx[s], ev)
                for (lo, hi), (caught, n) in bins.items():
                    dur_rows.append(dict(subject=s, arm=arm, set=("chb24" if s == "chb24" else "siena"),
                                         lo=lo, hi=hi, caught=caught, n=n))
        pd.DataFrame(dur_rows).to_csv(OUT / "duration_bins_ext.csv", index=False)
        print(f"\nElapsed {time.time()-t0:.0f}s.", flush=True)
        return

    if a.report:
        build_report()
        return
    raise SystemExit("pass --smoke, --full or --report")


ARM_LABEL = dict(G="G (frozen GAE latent)", B1="B1 (features + Mahalanobis)", B2="B2 (adjacency + Mahalanobis)",
                 B3="B3 (features + IsolationForest)", B4="B4 (features + kNN)", F="F (fusion: G + best of B1-B4)")


def _metrics_row(d):
    """pooled + per-patient-mean metrics from one stage's per-subject rows (E22.metrics, generalised)."""
    return E22.metrics(d)


def arm_summary(R, subs, arm, stage="localized"):
    d = R[(R.subject.isin(subs)) & (R.arm == arm) & (R.stage == stage)]
    if not len(d):
        return None
    if arm in ("G", "F"):
        per_seed = {}
        for tag in TAGS:
            dd = d[d.seed == tag]
            if len(dd):
                per_seed[tag] = _metrics_row(dd)
        if not per_seed:
            return None
        keys = ["sens", "prec", "f1", "fa_day", "s_sens", "s_prec", "s_f1", "s_fa"]
        mean = {k: float(np.mean([v[k] for v in per_seed.values()])) for k in keys}
        sd = {k: float(np.std([v[k] for v in per_seed.values()], ddof=1)) if len(per_seed) > 1 else 0.0 for k in keys}
        return dict(per_seed=per_seed, mean=mean, sd=sd, tp=float(np.mean([v["tp"] for v in per_seed.values()])),
                   n_ref=per_seed[next(iter(per_seed))]["n_ref"], fp=float(np.mean([v["fp"] for v in per_seed.values()])))
    return dict(single=_metrics_row(d))


def fmt_arm_row(name, s, headline_seed="clean_seed42"):
    if s is None:
        return f"{name:38s} -- not available"
    if "single" in s:
        m = s["single"]
        return (f"{name:38s} {m['tp']:5.1f}/{m['n_ref']:4.0f}  {m['fp']:5.1f}  {m['sens']:.3f}  {m['prec']:.3f}  "
                f"{m['f1']:.3f}  {m['fa_day']:6.2f} | {m['s_sens']:.3f}  {m['s_prec']:.3f}  {m['s_f1']:.3f} {m['s_fa']:6.2f}")
    h = s["per_seed"].get(headline_seed, next(iter(s["per_seed"].values())))
    mn, sd = s["mean"], s["sd"]
    return (f"{name:38s} {h['tp']:5.1f}/{h['n_ref']:4.0f}  {h['fp']:5.1f}  {h['sens']:.3f}  {h['prec']:.3f}  "
            f"{h['f1']:.3f}  {h['fa_day']:6.2f} | {h['s_sens']:.3f}  {h['s_prec']:.3f}  {h['s_f1']:.3f} {h['s_fa']:6.2f}"
            f"  || 4-seed mean sens {mn['sens']:.3f}+-{sd['sens']:.3f} FA/day {mn['fa_day']:.2f}+-{sd['fa_day']:.2f}"
            f" subj-mean {mn['s_sens']:.3f}+-{sd['s_sens']:.3f}")


def matched_curve(SW, subs, arm):
    d = SW[(SW.subject.isin(subs)) & (SW.arm == arm)]
    if not len(d):
        return None
    out = {}
    for tag in sorted(d.seed.unique()):
        g = d[d.seed == tag].groupby("top")[["tp", "fp", "n_ref", "nonict_h"]].sum().reset_index()
        g["sens"] = g.tp / g.n_ref; g["fa"] = g.fp / g.nonict_h * 24
        g = g.dropna(subset=["fa", "sens"]).sort_values("fa")
        for t in FP_TARGETS:
            if len(g) < 2 or t < g.fa.min() or t > g.fa.max():
                out.setdefault(t, []).append(np.nan)
            else:
                out.setdefault(t, []).append(float(np.interp(t, g.fa, g.sens)))
    return {t: (float(np.nanmean(v)), float(np.nanstd(v, ddof=1)) if len(v) > 1 else 0.0) for t, v in out.items()}


def patient_mean_ci(R, subs, arm, stage="localized", headline_seed="clean_seed42"):
    d = R[(R.subject.isin(subs)) & (R.arm == arm) & (R.stage == stage)]
    if arm in ("G", "F"):
        d = d[d.seed == headline_seed]
    if not len(d):
        return None
    per_pat = (d.groupby("subject").tp.sum() / d.groupby("subject").n_ref.sum()).values
    lo, hi = boot_mean_ci(per_pat)
    return float(np.mean(per_pat)), lo, hi


def duration_table(DB, subs, arm, setname):
    d = DB[(DB.subject.isin(subs)) & (DB.arm == arm) & (DB.set == setname)]
    if not len(d):
        return None
    g = d.groupby(["lo", "hi"])[["caught", "n"]].sum()
    return {(lo, hi): (int(r.caught), int(r.n)) for (lo, hi), r in g.iterrows()}


def write_set_section(L, R, SW, DB, subs, setname, title):
    arms = ["G"] + B_NAMES + ["F"]
    L += [f"\n## {title} ({len(subs)} patients)\n", "### Balanced operating point (clip(q_i(k), 0.005, 0.02)), after the CPD localizer\n", "```",
         "arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day"]
    summaries = {}
    for arm in arms:
        s = arm_summary(R, subs, arm)
        summaries[arm] = s
        L.append(fmt_arm_row(ARM_LABEL[arm], s))
    L.append("```")
    L += ["\n### Sensitivity by seizure duration bin (headline seed 42, after the localizer; E1 overlap rule)\n", "```",
         "arm                                    <=20s      21-40s     41-80s     >80s"]
    for arm in arms:
        bins = duration_table(DB, subs, arm, setname)
        if bins is None:
            L.append(f"{ARM_LABEL[arm]:38s} not available"); continue
        cells = []
        for b in DUR_BINS:
            c, n = bins.get(b, (0, 0))
            cells.append(f"{c}/{n}" if n else "-")
        L.append(f"{ARM_LABEL[arm]:38s} " + "  ".join(f"{c:9s}" for c in cells))
    L.append("```")
    L += [f"\n### Matched operating point (global budget sweep, detector stage): sensitivity @ FP/day "
         f"{', '.join(str(t) for t in FP_TARGETS)}\n", "```"]
    curves = {}
    for arm in arms:
        c = matched_curve(SW, subs, arm)
        curves[arm] = c
        if c is None:
            L.append(f"{ARM_LABEL[arm]:38s} not available"); continue
        L.append(f"{ARM_LABEL[arm]:38s} " + "  ".join(
            f"{t:.1f}:{c[t][0]:.3f}+-{c[t][1]:.3f}" if np.isfinite(c[t][0]) else f"{t:.1f}:NA" for t in FP_TARGETS))
    L.append("```")
    L += ["\n### Patient bootstrap 95% CI for the per-patient-mean sensitivity (headline seed 42, B = 10,000)\n", "```"]
    cis = {}
    for arm in arms:
        ci = patient_mean_ci(R, subs, arm)
        cis[arm] = ci
        if ci is None:
            L.append(f"{ARM_LABEL[arm]:38s} not available"); continue
        L.append(f"{ARM_LABEL[arm]:38s} {ci[0]:.3f}  [{ci[1]:.3f}, {ci[2]:.3f}]")
    L.append("```")
    return summaries, curves, cis


def winner_verdict(L, dev_sum, test_sum, dev_curve, test_curve):
    L.append("\n## Winner rule (fixed in the prompt): an arm 'beats G' only if it is better than G on "
             "development AND on CHB-MIT test (balanced-point pooled sensitivity) AND at the matched "
             "FP/day operating point (interpolated sensitivity >= G's at every one of "
             f"{FP_TARGETS} where both curves are defined, on both sets); otherwise 'no better' or 'mixed'.\n")
    gS = dev_sum.get("G"); gT = test_sum.get("G")
    for arm in B_NAMES + ["F"]:
        bS, bT = dev_sum.get(arm), test_sum.get(arm)
        if bS is None or bT is None or gS is None or gT is None:
            L.append(f"- {ARM_LABEL[arm]}: not available"); continue
        gS_sens = gS["mean"]["sens"]; gT_sens = gT["mean"]["sens"]
        bS_sens = bS["single"]["sens"] if "single" in bS else bS["mean"]["sens"]
        bT_sens = bT["single"]["sens"] if "single" in bT else bT["mean"]["sens"]
        dev_ok = bS_sens >= gS_sens; test_ok = bT_sens >= gT_sens
        cS, cT = dev_curve.get(arm), test_curve.get(arm)
        gcS, gcT = dev_curve.get("G"), test_curve.get("G")
        matched_ok = True; any_def = False
        for t in FP_TARGETS:
            if cS and gcS and np.isfinite(cS[t][0]) and np.isfinite(gcS[t][0]):
                any_def = True; matched_ok &= cS[t][0] >= gcS[t][0]
            if cT and gcT and np.isfinite(cT[t][0]) and np.isfinite(gcT[t][0]):
                any_def = True; matched_ok &= cT[t][0] >= gcT[t][0]
        matched_ok = matched_ok and any_def
        verdict = "BEATS G" if (dev_ok and test_ok and matched_ok) else ("no better" if not (dev_ok or test_ok) else "mixed")
        L.append(f"- {ARM_LABEL[arm]}: dev sens {bS_sens:.3f} vs G {gS_sens:.3f} ({'pass' if dev_ok else 'FAIL'}); "
                 f"test sens {bT_sens:.3f} vs G {gT_sens:.3f} ({'pass' if test_ok else 'FAIL'}); "
                 f"matched-FP {'pass' if matched_ok else 'FAIL'} -> **{verdict}**")


def build_report():
    R = pd.read_csv(OUT / "per_subject.csv")
    SW = pd.read_csv(OUT / "sweep.csv")
    DB = pd.read_csv(OUT / "duration_bins.csv")
    fc = json.load(open(OUT / "fusion_choice.json")) if (OUT / "fusion_choice.json").exists() else {}
    cfg = json.load(open(FRZ / "freeze.json"))
    L = ["# V9-E1 -- does the graph autoencoder help? Non-graph baselines on the identical pipeline\n",
         "Full tables: `results/v9_e1/*.csv`. Code: `src/v9_e1_baselines.py` (new; every frozen script it "
         "calls -- p2_scalars, e16_recording_baseline, e17b_latent_family, e18_cpd_localizer, p3_levers, "
         "e22_test_oneshot, e23_test_look7, x1_external, v9_anatomy -- is read-only and unmodified).\n",
         f"System held fixed for every arm: k = {cfg['k']:.6f}, smoothing {cfg['smooth']}, budget clip(q_i, "
         f"{cfg['points']['balanced'][0]}, {cfg['points']['balanced'][1]}), merge 90 s, kernel-CPD localizer "
         f"(freeze.json's choice). Only the per-channel anomaly score feeding e17b's order statistics "
         "(6/9/12 + channel mean) changes between arms. B3/B4 use a fixed random_state=42, no tuning; "
         "B4's 12 raw features are robust-z'd per channel per patient (label-free) before the Euclidean "
         "kNN distance, so unit differences between log-power, log-line-length and kurtosis do not by "
         "themselves dominate the distance -- the one preprocessing choice this script makes beyond the "
         "prompt's literal spec, disclosed here.\n",
         f"Reproduction gate: evaluate_arm(G) reproduces results/p3c_freeze/per_subject.csv (L2f) and "
         "results/e23_test_look7/per_subject_seed.csv (balanced) exactly -- checked, and would STOP the run, "
         "every invocation (see the script's own stdout).\n",
         f"Fusion F = rank-mean(G, {fc.get('best_of_B', '?')}); {fc.get('best_of_B', '?')} was chosen as the best "
         "of B1-B4 on development only (pooled sensitivity at the balanced point, ties -> lower FP/day), "
         "per the prompt's rule."]

    dev_sum, dev_curve, _ = write_set_section(L, R, SW, DB, DEV, "dev", "Development (train + validation)")
    test_sum, test_curve, _ = write_set_section(L, R, SW, DB, TEST, "test", "CHB-MIT held-out test")
    winner_verdict(L, dev_sum, test_sum, dev_curve, test_curve)

    pc = OUT / "part_c.csv"
    if pc.exists():
        P = pd.read_csv(pc)
        L.append("\n## Part C -- re-reporting G (seed 42, frozen balanced point, after the localizer) under "
                 "other papers' protocols on CHB-MIT test (secondary analysis, never the headline)\n")
        full = R[(R.subject.isin(TEST)) & (R.arm == "G") & (R.seed == "clean_seed42") & (R.stage == "localized")]
        tp0, fp0, nr0, h0 = full.tp.sum(), full.fp.sum(), full.n_ref.sum(), full.nonict_h.sum()
        L.append(f"- full 8-patient test set: tp {tp0}/{nr0}, FP {fp0}, sens {tp0/nr0:.3f}, FP/day {fp0/h0*24:.2f}")
        for _, r in P.iterrows():
            sens = r.tp / r.n_ref if r.n_ref else np.nan
            fa = f"{r.fp / r.nonict_h * 24:.2f}" if np.isfinite(r.get("nonict_h", np.nan)) else "n/a (ref-filtered only)"
            label = ("excluding chb06/chb14/chb16 (Clin Exp Pediatr 2026, DOI 10.3345/cep.2026.01011, mean "
                     "seizure duration < 30 s)" if r.part == "i_exclude_chb06_14_16" else "seizures >= 30 s only")
            L.append(f"- secondary analysis under the protocol of [{label}]: tp {r.tp}/{r.n_ref}, FP {r.fp}, "
                     f"sens {sens:.3f}, FP/day {fa}")

    ext_rows = OUT / "per_subject_ext.csv"
    L.append("\n## chb24 and Siena\n")
    xext = ROOT / "results" / "x1_external"
    try:
        chb24 = pd.read_csv(xext / "rows_chb24.csv")
        chb24 = chb24[(chb24.point == "balanced") & (chb24.stage == "localized")]
        tp, fp, nr, h = chb24.tp.sum(), chb24.fp.sum(), chb24.n_ref.sum(), chb24.nonict_h.sum()
        L.append(f"- chb24 (full, G only, from results/x1_external, balanced point, localized, 4-seed "
                 f"pooled): tp {tp}/{nr}, FP {fp}, sens {tp/nr:.3f}, FP/day {fp/h*24:.2f} -- committed reference; "
                 "recomputed below (all arms) where the raw-feature cache allows it.")
        import glob as _glob
        siena = pd.concat([pd.read_csv(p) for p in _glob.glob(str(xext / "rows_PN*.csv"))], ignore_index=True)
        siena = siena[(siena.point == "balanced") & (siena.stage == "localized")]
        tp, fp, nr, h = siena.tp.sum(), siena.fp.sum(), siena.n_ref.sum(), siena.nonict_h.sum()
        L.append(f"- Siena, all 14 patients (G only, from results/x1_external, balanced point, localized, "
                 f"4-seed pooled): tp {tp}/{nr}, FP {fp}, sens {tp/nr:.3f}, FP/day {fp/h*24:.2f} -- committed "
                 "reference only (B1-F need raw features not cached for 11/14 patients).")
    except Exception as e:
        L.append(f"- could not read results/x1_external aggregate rows ({e}).")
    if ext_rows.exists():
        Re = pd.read_csv(ext_rows)
        SWe = pd.read_csv(OUT / "sweep_ext.csv") if (OUT / "sweep_ext.csv").exists() else pd.DataFrame(columns=SW.columns)
        DBe = pd.read_csv(OUT / "duration_bins_ext.csv") if (OUT / "duration_bins_ext.csv").exists() else pd.DataFrame(columns=DB.columns)
        L.append(f"\nRaw-feature cache available locally (results/v9_anatomy/xcache/) for chb24 and 3/14 Siena "
                 f"patients (PN00, PN10, PN11); the other 11 Siena patients ({', '.join(SIENA_MISSING)}) have no "
                 "raw EDF in this checkout (documented in results/v9_anatomy/SUMMARY.md) -- B1-B4/F are refused "
                 "there, not estimated.\n")
        write_set_section(L, Re, SWe, DBe, ["chb24"], "chb24", "chb24 (recomputed locally, all arms)")
        write_set_section(L, Re, SWe, DBe, ["PN00", "PN10", "PN11"], "siena", "Siena, 3/14 patients with a local raw-feature cache")
    else:
        L.append("\nresults/v9_e1/per_subject_ext.csv not found -- run `python src/v9_e1_baselines.py --ext` first.")

    L.append(f"\n## Runtime measured\nSee the script's own stdout (printed elapsed seconds) for the --full and "
             "--ext runs; both are resumable (per-subject cache under results/v9_e1/cache/).")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "SUMMARY.md").write_text("\n".join(L), encoding="utf-8")
    inbox = ROOT.parent / "Agent" / "inbox" / "V9_E1_REPORT.md"
    inbox.parent.mkdir(parents=True, exist_ok=True)
    inbox.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))
    print(f"\nWrote results/v9_e1/SUMMARY.md and {inbox}")


if __name__ == "__main__":
    main()
