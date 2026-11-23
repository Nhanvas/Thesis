#!/usr/bin/env python
"""
eur_v1.py -- milestone M2, item V1 (Track F, chat F2-02; design results/m2_v1/DESIGN_V1.md, approved by the author
23/11/2026 13:39). How many seizures does the V5 system put in front of the reader for a given share of the recording
reviewed? Inference only: the four committed V5 checkpoints data/models_v2/gae_v2_clean_seed{42,1,2,3}.pt on the
defense-time data copy (v9-x3-fold1/3) and the external features (thesis-r2-external-features). Written before any
output. The record modules and src/eur_abl.py are imported READ ONLY (no record code is changed).

Per case and seed (x = e22_test_oneshot.final_scalar, the V5 ensemble score; m = p3_levers.member_mean_z; k = V5's
label-free rule p3_levers.calibrate on the 15 development patients, seed 42):
  own      V5's own label-free point: eur_abl.run_budget_s, arms own (clip(q, 0.5 %, 2 %)) and fixed (0.5 %), stages
           detector / cpd / hybrid -- the rows of EUR_ABL's V0 (gate G-v5own)
  grid (a) a budget `top` = share of windows flagged, the same for every patient (p2_scalars.d1_events, smoothing 5,
           merge 90 s), GRID 0.1 % ... 20 %; stage detector and stage cpd (p3_levers.localize, mode cpd); per row tp, fp,
           n_ref, non-ictal hours, review_s (event time actually opened), n_events; per reference seizure caught or
           not (exact replica of the SzCORE scorer loop, gate G-score: = p2_scalars.score on every grid row)
  null     chance reference: x circularly shifted within each file over its valid windows (NSHIFT shifts, rng fixed by
           case, seed and shift; the multiset of values per file is unchanged, so every budget flags the same windows'
           count); stage detector, every top of GRID
  rank (b) b1 = V5's own events (cpd stage, own budget) ranked by peak smoothed score per patient; the reader stops
           after N = min(ceil(r * H), n_events) events, r in RATES events per hour of EEG, H = recorded hours of the
           patient; "all" = every V5 event (gate G-b1all: = the own cpd row)
           b2 = peak-centred 120-s clips by non-maximum suppression on the smoothed score (windows i-15 ... i+14; no two
           clip centres within NMS_RADIUS windows, so two clips are always > 90 s apart and the scorer never merges
           them); N = min(ceil(r * H), n_candidates)
Gates (STOP unless PASS): G-self-v1 (synthetic: shift = permutation of each file's valid values, NMS spacing and order,
scorer replica = timescoring on random intervals), G-data, SMOKE (chb01, chb03, chb24 end to end; projection STOP if
> 10.5 h), R1.0-dev / R1.0-test / GE / G-k (r2_r1.r10 unchanged), G-kv1 (k = EUR_ABL's V0 k, relative 1e-6), G-v5own
(own rows and onset / offset errors = results/eureka_d31f/abl V0 rows: development and test exactly -- integers equal,
floats relative 1e-12 -- external within the GE tolerance |dtp| <= 1, |dfp| <= 2, non-ictal hours and recorded seconds exact), G-curve (grid detector rows at the six
committed tops = results/eureka_d31f/abl/curve.csv V0, same rule), G-score and G-b1all (inside each job), G-worker (every
pool job ran the same eur_v1.py / eur_abl.py / record modules as the parent, sha256).
Outputs: WORK/eureka/v1/ (run_meta.json, gates.json, data_sha256.csv, r10/, own_rows.csv, own_errors.csv, grid.csv,
null.csv, rank.csv, seizures.csv, k.csv, jobs.csv, projection.json, smoke/, SUMMARY.md). The reading is
src/eur_v1_read.py (committed before the run).
  python src/eur_v1.py [--workers N] [--smoke-only]
Test mode (synthetic world): R2_TEST=1 (src/eur_v1_synthetic_test.py).
"""
import hashlib
import json
import math
import os
import platform
import sys
import time
import traceback
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

if platform.system() == "Windows" and "resource" not in sys.modules:      # r2_r1 logs peak memory with `resource`
    import types
    _r = types.ModuleType("resource")
    _r.RUSAGE_SELF, _r.RUSAGE_CHILDREN = 0, -1
    _r.getrusage = lambda *_: types.SimpleNamespace(ru_maxrss=0)
    sys.modules["resource"] = _r

REPO = Path(os.environ.get("THESIS_REPO", Path(__file__).resolve().parents[1]))
for _p in ("src", "src/dataprep", "src/retrain", "src/phaseB", "src/phaseC"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import eur_abl as A                      # noqa: E402  (read only: building blocks, record gates, pool)
import e10_kernel_cpd as E10             # noqa: E402
import szcore_eval as SE                 # noqa: E402

R1, PS, P3L, P3C, E22 = A.R1, A.PS, A.P3L, A.P3C, A.E22
_OUT = [m.__name__ for m in (A, E10, SE) if (REPO / "src") not in Path(m.__file__).resolve().parents]
if _OUT:
    raise SystemExit(f"STOP: modules imported from outside {REPO / 'src'}: {_OUT}")
log = R1.log

TAGS, DEV, TEST, EXT = list(R1.TAGS), list(R1.DEV), list(R1.TEST), list(R1.EXT)
WIN = PS.WIN
SMOOTH = P3C.SMOOTH                                        # 5 windows (V5)
GRID = (0.001, 0.002, 0.003, 0.004, 0.005, 0.0065, 0.0075, 0.01, 0.015, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20)
CURVE_TOPS = tuple(A.CURVE_TOPS)                          # the six tops of the committed curve.csv (all in GRID)
STAGES = ("detector", "cpd")
NSHIFT, SHIFT_SEED = 10, 20261123
RATES = (0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0)              # events reviewed per hour of EEG
CLIP_HALF = 15                                            # clip = windows i-15 ... i+14 = 120 s (Moura et al. 2014)
NMS_RADIUS = 53                                           # centres > 53 windows apart -> clip gap >= 23 windows = 92 s > 90 s
REFUSE_H = 10.5
ABL = Path("results") / "eureka_d31f" / "abl"             # the committed EUR_ABL run (V0 rows = the reference)
TAG = "v1"
TEST_MODE = bool(os.environ.get("R2_TEST"))
SEED_OF = {t: int(t.split("seed")[1]) for t in TAGS}


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


CODE_SHA = sha16(__file__)


def code_shas():
    d = dict(A.code_shas())
    d.update(eur_v1=CODE_SHA, e10=sha16(E10.__file__), szcore_eval=sha16(SE.__file__))
    return d


# ============================================================================ building blocks
def szcore_detail(ctx, per_file):
    """the SzCORE count of p2_scalars.score (= e10_kernel_cpd.score_events -> szcore_eval.score_szcore: files
    concatenated with 600-s gaps, timescoring EventScoring with SZ_PARAM) plus, for every annotated seizure, whether
    the scorer counted it: the library's own TP loop re-read event by event on its own (merged / split) reference
    events; an annotated seizure is caught if any scorer reference event overlapping it is a TP."""
    from timescoring import scoring
    from timescoring.annotations import Annotation
    z = ctx["z"]
    ok = ~np.asarray(z["is_signal_loss"]).astype(bool)
    ict = np.asarray(z["is_ictal"]).astype(bool)
    fidx = np.asarray(z["file_idx"]).astype(int)
    ref, hyp, rmap, off = [], [], [], 0
    for f in np.unique(fidx):
        m = np.flatnonzero(fidx == f)
        for a, b in E10.runs(ict[m]):
            ref.append((a * WIN + off, b * WIN + off))
            rmap.append((int(f), a * WIN, b * WIN))
        hyp += [(a + off, b + off) for a, b in per_file.get(f, [])]
        off += len(m) * WIN + 600
    h = float((~ict & ok).sum()) * WIN / 3600
    N = max(int(off), 1)
    P = SE.SZ_PARAM
    s = scoring.EventScoring(Annotation(list(ref), 1, N), Annotation(list(hyp), 1, N), P)
    ext = scoring.EventScoring._extendEvents(s.ref, P.toleranceStart, P.toleranceEnd)
    fs = s.fs
    flags = []
    for ev in ext.events:
        rel = (np.sum(s.hyp.mask[round(ev[0] * fs):round(ev[1] * fs)]) / fs) / (ev[1] - ev[0])
        flags.append(bool(rel > P.minOverlap + 1e-6))
    if sum(flags) != s.tp:
        raise SystemExit(f"scorer replica: {sum(flags)} TP flags != scorer tp {s.tp}")
    per_ref = [bool(any(fl for (e0, e1), fl in zip(s.ref.events, flags) if e0 < r1 and e1 > r0)) for r0, r1 in ref]
    return dict(tp=int(s.tp), fp=int(s.fp), n_ref=int(s.refTrue), h=h, per_ref=per_ref, rmap=rmap)


def n_events(per_file):
    return int(sum(len(v) for v in per_file.values()))


def review_s(per_file):
    return float(sum(b - a for v in per_file.values() for a, b in v))


def shift_scalar(ctx, x, rng):
    """x circularly shifted within each file over its valid (non-signal-loss) windows by an offset in 1 .. n_valid-1;
    signal-loss positions unchanged."""
    xs = np.array(x, dtype=np.float64, copy=True)
    for f in np.unique(ctx["fidx"]):
        m = np.flatnonzero((ctx["fidx"] == f) & ctx["ok"])
        if len(m) > 1:
            xs[m] = np.roll(np.asarray(x, np.float64)[m], int(rng.integers(1, len(m))))
    return xs


def shift_rng(case, tag, s):
    return np.random.default_rng([SHIFT_SEED, zlib.crc32(case.encode()), SEED_OF.get(tag, 0), s])


def file_bounds(fidx):
    """{file: (start, end)} of the window axis; STOP unless every file is one contiguous block."""
    out = {}
    for f in np.unique(fidx):
        w = np.flatnonzero(fidx == f)
        if w[-1] - w[0] + 1 != len(w):
            raise SystemExit(f"file {f} is not contiguous on the window axis")
        out[int(f)] = (int(w[0]), int(w[-1]) + 1)
    return out


def nms_candidates(sm, fidx, nmax):
    """peak-centred clips: windows in decreasing smoothed score (ties: earlier window first); a window is taken unless a
    taken centre of the same file lies within NMS_RADIUS windows; clip = windows [j-15, j+15) of its file (clipped at
    the file edges). Returns [(file, a_s, b_s, peak, centre_window)] in the order taken (= decreasing peak)."""
    bounds = file_bounds(fidx)
    v = np.where(np.isfinite(sm), sm, -np.inf)
    order = np.lexsort((np.arange(len(v)), -v))
    supp = np.zeros(len(v), bool)
    out = []
    for i in order:
        if len(out) >= nmax or not np.isfinite(v[i]):
            break
        if supp[i]:
            continue
        f = int(fidx[i])
        s0, s1 = bounds[f]
        j = i - s0
        a, b = max(0, j - CLIP_HALF), min(s1 - s0, j + CLIP_HALF)
        out.append((f, a * WIN, b * WIN, float(v[i]), int(i)))
        supp[max(s0, i - NMS_RADIUS): min(s1, i + NMS_RADIUS + 1)] = True
    return out


def as_per_file(evs):
    d = {}
    for f, a, b in sorted((e[0], e[1], e[2]) for e in evs):
        d.setdefault(f, []).append((a, b))
    return d


def event_peaks(ctx, sm, per_file):
    """[(file, a_s, b_s, peak)] with peak = the largest smoothed score inside the event (-inf if none is finite)."""
    out = []
    for f, evs in per_file.items():
        m = np.flatnonzero(ctx["fidx"] == f)
        for a, b in evs:
            seg = sm[m][a // WIN: max(a // WIN + 1, b // WIN)]
            seg = seg[np.isfinite(seg)]
            out.append((int(f), a, b, float(seg.max()) if len(seg) else -np.inf))
    return out


def n_of(rate, hours, avail):
    return int(min(avail, math.ceil(rate * hours - 1e-9)))


def self_checks():
    """G-self-v1 on synthetic arrays: shift, NMS, scorer replica."""
    rng = np.random.default_rng(0)
    bad = []
    n = 1200
    fidx = np.repeat([0, 1, 2], [500, 400, 300])
    ok = rng.random(n) > 0.05
    x = rng.random(n)
    ctx = dict(fidx=fidx, ok=ok)
    xs = shift_scalar(ctx, x, np.random.default_rng(1))
    for f in range(3):
        m = (fidx == f) & ok
        if not np.array_equal(np.sort(xs[m]), np.sort(x[m])) or np.array_equal(xs[m], x[m]):
            bad.append(f"shift file {f}")
    if not np.array_equal(xs[~ok], x[~ok]):
        bad.append("shift touched signal-loss windows")
    if not np.array_equal(shift_scalar(ctx, x, np.random.default_rng(1)), xs):
        bad.append("shift not reproducible")
    sm = pd.Series(x).rolling(5, min_periods=1, center=True).mean().to_numpy(copy=True)
    sm[~ok] = np.nan
    c = nms_candidates(sm, fidx, 10 ** 6)
    pk = [e[3] for e in c]
    if pk != sorted(pk, reverse=True):
        bad.append("nms order")
    for f in range(3):
        ce = sorted(e[4] for e in c if e[0] == f)
        if any(b - a <= NMS_RADIUS for a, b in zip(ce, ce[1:])):
            bad.append(f"nms spacing file {f}")
        evs = sorted((e[1], e[2]) for e in c if e[0] == f)
        if any(a2 - b1 <= 90 for (_, b1), (a2, _) in zip(evs, evs[1:])):
            bad.append(f"nms clip gap file {f}")
    if not all(e[2] - e[1] <= 2 * CLIP_HALF * WIN for e in c):
        bad.append("clip length")
    # scorer replica = timescoring on random intervals (merges, splits, long seizures included)
    for trial in range(20):
        T = 20000
        refs = sorted({(int(a), int(a + rng.integers(8, 700))) for a in rng.integers(0, T - 800, 6)})
        hyps = sorted({(int(a), int(a + rng.integers(4, 400))) for a in rng.integers(0, T - 500, 15)})
        ict = np.zeros(T // WIN, bool)
        for a, b in refs:
            ict[a // WIN: b // WIN] = True
        z = dict(is_signal_loss=np.zeros(T // WIN, bool), is_ictal=ict, file_idx=np.zeros(T // WIN, int))
        per = {0: [(a // WIN * WIN, b // WIN * WIN) for a, b in hyps if b // WIN > a // WIN]}
        d = szcore_detail(dict(z=z), per)
        tp, fp, nr, h, _ = E10.score_events(z, per)
        if (d["tp"], d["fp"], d["n_ref"]) != (tp, fp, nr) or abs(d["h"] - h) > 0:
            bad.append(f"scorer replica trial {trial}")
    R1.gate(dict(gate="G-self-v1", status="PASS" if not bad else "FAIL", bad=bad,
                 summary="shift = permutation of each file's valid values; NMS order / spacing / clip gap; scorer replica "
                         "= e10 score_events on 20 random worlds" if not bad else str(bad)))


# ============================================================================ pool jobs
def k_job(a):
    """development case: seed-42 smoothed member mean (V5's k rule)."""
    case, = a
    t = time.time()
    try:
        ctx, _ = R1.ctx_from_store(case, "earlier", "r10")
        smm = PS.smoothed(ctx, P3L.member_mean_z(ctx, "clean_seed42"), SMOOTH)
        return dict(case=case, smm=smm, s=round(time.time() - t, 1), shas=code_shas())
    except Exception:                    # noqa: BLE001
        return dict(case=case, error=traceback.format_exc()[-3000:])


def score_job(a):
    """one case, the four seeds: own rows, grid (a), null, rank (b), per-seizure flags."""
    case, src, k, set_name, nshift = a
    t0 = time.time()
    tm = dict(own=0.0, grid_det=0.0, grid_cpd=0.0, score=0.0, null=0.0, rank=0.0)
    try:
        ctx, _ = R1.ctx_from_store(case, src, "r10")
        zr, _ = R1.load_case(case, src)
        files = [str(f) for f in zr["files"]] if "files" in (zr.files if hasattr(zr, "files") else zr) else []
        file_bounds(ctx["fidx"])
        hours = ctx["n"] * WIN / 3600
        own, own_e, grid, null, rank, seiz = [], [], [], [], [], []
        score_bad = []
        for tag in TAGS:
            t = time.time()
            x = E22.final_scalar(ctx, tag)
            m = P3L.member_mean_z(ctx, tag)
            q = P3L.q_of(PS.smoothed(ctx, m, SMOOTH), k)
            r_, e_ = [], []
            for arm, (fl, cp) in A.ARMS.items():
                A.run_budget_s(ctx, case, tag, x, q, fl, cp, arm, r_, e_, SMOOTH)
            own += [dict(r, variant="V0", set=set_name, q_raw=q, k=k) for r in r_]
            own_e += [dict(e, variant="V0", set=set_name) for e in e_]
            sm = PS.smoothed(ctx, x, SMOOTH)
            tm["own"] += time.time() - t
            # ---- (a) grid
            for top in GRID:
                t = time.time()
                det = PS.d1_events(ctx, x, SMOOTH, top)
                tm["grid_det"] += time.time() - t
                t = time.time()
                thr = np.nanquantile(sm, 1 - top)
                cpd, _ = P3L.localize(ctx, x, det, thr, "cpd")
                tm["grid_cpd"] += time.time() - t
                for st, ev in (("detector", det), ("cpd", cpd)):
                    t = time.time()
                    d = szcore_detail(ctx, ev)
                    rec = PS.score(ctx, ev)
                    if (d["tp"], d["fp"], d["n_ref"]) != tuple(rec[:3]) or d["h"] != rec[3]:
                        score_bad.append((tag, top, st))
                    tm["score"] += time.time() - t
                    grid.append(dict(subject=case, seed=tag, set=set_name, stage=st, top=top, tp=d["tp"], fp=d["fp"],
                                     n_ref=d["n_ref"], nonict_h=d["h"], review_s=review_s(ev), rec_s=ctx["n"] * WIN,
                                     n_events=n_events(ev)))
                    for i, ((f, on, off), c) in enumerate(zip(d["rmap"], d["per_ref"])):
                        seiz.append(dict(subject=case, seed=tag, set=set_name, stage=st, top=top, ref_i=i, file_idx=f,
                                         file=files[f] if f < len(files) else "", on_s=on, off_s=off, caught=int(c)))
            # ---- chance reference (detector stage)
            t = time.time()
            for s in range(nshift):
                xs = shift_scalar(ctx, x, shift_rng(case, tag, s))
                for top in GRID:
                    det = PS.d1_events(ctx, xs, SMOOTH, top)
                    d = szcore_detail(ctx, det)
                    null.append(dict(subject=case, seed=tag, set=set_name, shift=s, top=top, tp=d["tp"], fp=d["fp"],
                                     n_ref=d["n_ref"], nonict_h=d["h"], review_s=review_s(det), rec_s=ctx["n"] * WIN,
                                     n_events=n_events(det)))
            tm["null"] += time.time() - t
            # ---- (b) ranked events
            t = time.time()
            top_own = P3C.budget(q, *A.ARMS["own"])
            det = PS.d1_events(ctx, x, SMOOTH, top_own)
            thr = np.nanquantile(sm, 1 - top_own)
            cpd, _ = P3L.localize(ctx, x, det, thr, "cpd")
            evs = sorted(event_peaks(ctx, sm, cpd), key=lambda e: (-e[3], e[0], e[1]))
            own_cpd = [r for r in r_ if r["budget"] == "own" and r["stage"] == "cpd"][0]
            for rate in RATES + ("all",):
                N = len(evs) if rate == "all" else n_of(rate, hours, len(evs))
                sub = as_per_file(evs[:N])
                d = szcore_detail(ctx, sub)
                if rate == "all" and (d["tp"], d["fp"], d["n_ref"]) != (own_cpd["tp"], own_cpd["fp"], own_cpd["n_ref"]):
                    raise SystemExit(f"G-b1all {case} {tag}: every V5 event ranked ({d['tp']}, {d['fp']}) != own cpd row "
                                     f"({own_cpd['tp']}, {own_cpd['fp']})")
                rank.append(dict(subject=case, seed=tag, set=set_name, method="b1", rate=rate, N=N, n_avail=len(evs),
                                 tp=d["tp"], fp=d["fp"], n_ref=d["n_ref"], nonict_h=d["h"], review_s=review_s(sub),
                                 rec_s=ctx["n"] * WIN, hours=hours))
            cands = nms_candidates(sm, ctx["fidx"], n_of(max(RATES), hours, 10 ** 9))
            for rate in RATES:
                N = n_of(rate, hours, len(cands))
                sub = as_per_file([(f, a_, b_) for f, a_, b_, _, _ in cands[:N]])
                d = szcore_detail(ctx, sub)
                rank.append(dict(subject=case, seed=tag, set=set_name, method="b2", rate=rate, N=N, n_avail=len(cands),
                                 tp=d["tp"], fp=d["fp"], n_ref=d["n_ref"], nonict_h=d["h"], review_s=review_s(sub),
                                 rec_s=ctx["n"] * WIN, hours=hours))
            tm["rank"] += time.time() - t
        if score_bad:
            raise SystemExit(f"G-score {case}: the scorer replica differs from p2_scalars.score in {score_bad[:5]}")
        import resource
        return dict(case=case, src=src, job="score", own=own, own_e=own_e, grid=grid, null=null, rank=rank, seiz=seiz,
                    shas=code_shas(), s=round(time.time() - t0, 1), hours=hours,
                    timing={k_: round(v, 1) for k_, v in tm.items()},
                    peak_rss_mb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1))
    except SystemExit as e:
        return dict(case=case, src=src, job="score", error=f"STOP: {e}")
    except Exception:                    # noqa: BLE001
        return dict(case=case, src=src, job="score", error=traceback.format_exc()[-3000:])


# ============================================================================ reference comparisons
INTS = ["tp", "fp", "n_ref", "short_tp", "short_n"]
FLOATS = ["top", "nonict_h", "review_s", "rec_s", "q_raw"]
EXT_FLOATS = ("nonict_h", "rec_s")                         # data-determined; the rest follows the counts


def _rel_eq(a, b, rel=1e-12):
    a, b = float(a), float(b)
    return a == b or abs(a - b) <= rel * max(abs(a), abs(b))


def compare_rows(mine, ref, keys, ints, floats, ext_cases):
    """rows of `mine` against `ref` on `keys`: development / test exactly (integers equal, floats relative 1e-12);
    external within the GE tolerance (|dtp| <= 1, |dfp| <= 2; other integers and floats as above)."""
    a = pd.DataFrame(mine)
    b = ref.copy()
    mg = a.merge(b, on=keys, how="outer", suffixes=("", "_ref"), indicator=True)
    miss = mg[mg._merge != "both"][keys].to_dict("records")
    bad, exact_ext, n_ext = [], 0, 0
    for _, r in mg[mg._merge == "both"].iterrows():
        ext = r["subject"] in ext_cases
        dif = []
        for c in ints:
            d = int(r[c]) - int(r[f"{c}_ref"])
            lim = {"tp": R1.TOL["ext_tp"], "fp": R1.TOL["ext_fp"]}.get(c, 0) if ext else 0
            if abs(d) > lim:
                dif.append((c, int(r[c]), int(r[f"{c}_ref"])))
        for c in floats:
            if ext and c not in EXT_FLOATS:
                continue                  # external: q_raw / top / review_s follow the counts (descriptive, as GE)
            if not _rel_eq(r[c], r[f"{c}_ref"]):
                dif.append((c, float(r[c]), float(r[f"{c}_ref"])))
        if ext:
            n_ext += 1
            exact_ext += int(all(int(r[c]) == int(r[f"{c}_ref"]) for c in ints))
        if dif:
            bad.append(dict({k: r[k] for k in keys}, diff=dif))
    return int((mg._merge == "both").sum()), miss, bad, exact_ext, n_ext


def gate_v5own(own, own_e, cases, label):
    ref = pd.read_csv(REPO / ABL / "per_subject.csv", float_precision="round_trip")
    ref = ref[(ref.variant == "V0") & ref.subject.isin(cases)]
    keys = ["subject", "seed", "budget", "stage"]
    ext = set(EXT)
    n, miss, bad, ex, ne = compare_rows(own, ref[keys + INTS + FLOATS], keys, INTS, FLOATS, ext)
    eref = pd.read_csv(REPO / ABL / "errors.csv", float_precision="round_trip")
    eref = eref[(eref.variant == "V0") & eref.subject.isin(cases)]
    ebad = []
    a = pd.DataFrame(own_e)
    for (s, sd, bu), g in (a.groupby(["subject", "seed", "budget"]) if len(a) else []):
        r = eref[(eref.subject == s) & (eref.seed == sd) & (eref.budget == bu)]
        if s in ext:
            continue                      # external errors descriptive only (as GE)
        if len(r) != len(g) or not np.array_equal(r[R1.ERR_COLS].to_numpy(float), g[R1.ERR_COLS].to_numpy(float)):
            ebad.append((s, sd, bu, len(g), len(r)))
    ok = not miss and not bad and not ebad and n == len(ref)
    R1.gate(dict(gate=f"G-v5own[{label}]", status="PASS" if ok else "FAIL", rows=n, ref_rows=int(len(ref)),
                 missing=miss[:20], mismatches=bad[:30], n_mismatch=len(bad), error_mismatches=ebad[:20],
                 external_exact=f"{ex}/{ne}",
                 summary=f"own point: {n} rows vs EUR_ABL V0 ({len(ref)}); {len(bad)} differ, {len(miss)} missing, "
                         f"{len(ebad)} error groups differ; external exact {ex}/{ne}"))


def gate_curve(grid, cases, label):
    ref = pd.read_csv(REPO / ABL / "curve.csv", float_precision="round_trip")
    ref = ref[(ref.variant == "V0") & ref.subject.isin(cases)]
    mine = [dict(subject=r["subject"], seed=r["seed"], top=r["top"], tp=r["tp"], fp=r["fp"], n_ref=r["n_ref"],
                 nonict_h=r["nonict_h"]) for r in grid if r["stage"] == "detector" and r["top"] in CURVE_TOPS]
    keys = ["subject", "seed", "top"]
    n, miss, bad, ex, ne = compare_rows(mine, ref[keys + ["tp", "fp", "n_ref", "nonict_h"]], keys, ["tp", "fp", "n_ref"],
                                        ["nonict_h"], set(EXT))
    ok = not miss and not bad and n == len(ref)
    R1.gate(dict(gate=f"G-curve[{label}]", status="PASS" if ok else "FAIL", rows=n, ref_rows=int(len(ref)),
                 missing=miss[:20], mismatches=bad[:30], n_mismatch=len(bad), external_exact=f"{ex}/{ne}",
                 summary=f"grid detector rows at {list(CURVE_TOPS)}: {n} vs committed curve.csv ({len(ref)}); "
                         f"{len(bad)} differ, {len(miss)} missing; external exact {ex}/{ne}"))


def k_reference():
    kr = pd.read_csv(REPO / ABL / "k.csv", float_precision="round_trip")
    return float(kr[kr.variant == "V0"].k.iloc[0])


# ============================================================================ phases
def set_of(case, src):
    return "external" if src == "ext" else ("development" if case in DEV else "test")


def score_pass(cases_src, k, workers, label, nshift):
    t = time.time()
    specs = sorted([(c, s, k, set_of(c, s), nshift) for c, s in cases_src], key=lambda a: -A._size(a[0], a[1]))
    res = A._run(score_job, specs, workers, f"score[{label}]")
    R1.phase(f"score_{label}", t)
    return res


def collect(res, key):
    return [r for x in res for r in x[key]]


def write_outputs(res, label=""):
    o = R1.out_dir()
    for key, name in (("own", "own_rows"), ("own_e", "own_errors"), ("grid", "grid"), ("null", "null"),
                      ("rank", "rank"), ("seiz", "seizures")):
        pd.DataFrame(collect(res, key)).to_csv(o / f"{name}{label}.csv", index=False)
    pd.DataFrame([dict(case=r["case"], s=r["s"], hours=r["hours"], peak_rss_mb=r["peak_rss_mb"], **r["timing"])
                  for r in res]).to_csv(o / f"jobs{label}.csv", index=False)


def gate_worker(results, label):
    want = code_shas()
    bad = sorted({r["case"] for r in results if r.get("shas") != want})
    R1.gate(dict(gate=f"G-worker[{label}]", status="PASS" if not bad else "FAIL", bad=bad, want=want,
                 summary=f"{len(results)} jobs ran eur_v1 {want['eur_v1']}, eur_abl {want['eur_abl']}"))


def main(notebook="EUR_V1", repo_commit="local", workers=None, smoke_only=False):
    R1.OUT_ROOT = R1.WORK / "eureka"
    workers = int(workers or os.environ.get("EUR_WORKERS") or R1.n_workers())
    nshift = int(os.environ.get("EUR_V1_NSHIFT", NSHIFT)) if TEST_MODE else NSHIFT
    meta = R1.run_meta(TAG, notebook, repo_commit)
    meta.update(eur_v1_sha=CODE_SHA, code_shas=code_shas(), grid=list(GRID), stages=list(STAGES), nshift=nshift,
                shift_seed=SHIFT_SEED, rates=list(RATES), clip_s=2 * CLIP_HALF * WIN, nms_radius_windows=NMS_RADIUS,
                workers=workers, **A.cpu_model())
    R1._jdump(R1.out_dir() / "run_meta.json", meta)
    k_ref = k_reference()
    self_checks()
    src = A.build_views(DEV, TEST, EXT)
    A.gate_data(src)
    # ---- SMOKE: chb01 + chb03 + first external case, end to end, measured
    t = time.time()
    s_dev, s_test, s_ext = [DEV[0]], [TEST[0]], EXT[:1]
    R1.STATE["tag"] = f"{TAG}/smoke"
    R1.r10(s_dev, s_test, s_ext, workers=min(workers, 3), with_k=False)
    cs = [(c, "earlier") for c in s_dev + s_test] + [(c, "ext") for c in s_ext]
    res = score_pass(cs, k_ref, min(workers, 3), "smoke", nshift)
    write_outputs(res)
    gate_v5own(collect(res, "own"), collect(res, "own_e"), s_dev + s_test + s_ext, "smoke")
    gate_curve(collect(res, "grid"), s_dev + s_test + s_ext, "smoke")
    gate_worker(res, "smoke")
    smoke_s = time.time() - t
    h_smoke = sum(r["hours"] for r in res)
    h_all = sum(float(np.load(R1.VIEWS / ("ext" if c in EXT else "earlier") / (f"{c}_lf.npz" if c in EXT else f"{c}.npz"),
                              allow_pickle=True)["is_ictal"].shape[0]) * WIN / 3600 for c in DEV + TEST + EXT)
    proj = dict(smoke_s=round(smoke_s, 1), smoke_eeg_h=round(h_smoke, 2), all_eeg_h=round(h_all, 1), workers=workers,
                note="computed: smoke seconds x (all hours / smoke hours) / workers x 1.2",
                projected_h=round(smoke_s * (h_all / max(h_smoke, 1e-9)) / max(workers, 1) * 1.2 / 3600, 2),
                timing_smoke=[dict(case=r["case"], **r["timing"]) for r in res])
    R1.STATE["tag"] = TAG
    R1._jdump(R1.out_dir() / "projection.json", proj)
    R1.gate(dict(gate="SMOKE", status="PASS" if proj["projected_h"] <= REFUSE_H else "FAIL",
                 **{k_: v for k_, v in proj.items() if k_ != "timing_smoke"},
                 summary=f"smoke {smoke_s:.0f} s on {h_smoke:.1f} h of EEG; full run projected {proj['projected_h']} h"))
    if smoke_only:
        return
    # ---- FULL
    t = time.time()
    R1.r10(DEV, TEST, EXT, workers=workers, with_k=True)
    R1.phase("r10_full", t)
    kres = A._run(k_job, [(c,) for c in DEV], workers, "k")
    k = float(P3L.calibrate([next(r["smm"] for r in kres if r["case"] == c) for c in DEV]))
    rel = abs(k - k_ref) / abs(k_ref)
    pd.DataFrame([dict(variant="V0", k=k, k_eur_abl=k_ref, rel=rel)]).to_csv(R1.out_dir() / "k.csv", index=False)
    R1.gate(dict(gate="G-kv1", status="PASS" if rel <= R1.TOL["k_rel"] else "FAIL", k=k, k_ref=k_ref, rel=rel,
                 summary=f"k {k:.9f} vs EUR_ABL V0 {k_ref:.9f} (relative {rel:.1e})"))
    cs = [(c, "earlier") for c in DEV + TEST] + [(c, "ext") for c in EXT]
    res = score_pass(cs, k, workers, "full", nshift)
    write_outputs(res)
    gate_v5own(collect(res, "own"), collect(res, "own_e"), DEV + TEST + EXT, "full")
    gate_curve(collect(res, "grid"), DEV + TEST + EXT, "full")
    gate_worker(res + kres, "full")
    R1.finish_meta(dict(k=k))
    (R1.out_dir() / "SUMMARY.md").write_text(
        f"# EUR_V1 run ({notebook}, commit {repo_commit})\n\nEvery gate PASS (gates.json). Rows: own_rows.csv, "
        "own_errors.csv, grid.csv, null.csv, rank.csv, seizures.csv; k.csv; jobs.csv.\n"
        "No reading here: src/eur_v1_read.py makes the tables (committed before this run).\n")
    log("EUR_V1 done")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int)
    ap.add_argument("--smoke-only", action="store_true")
    a_ = ap.parse_args()
    main(workers=a_.workers, smoke_only=a_.smoke_only)
