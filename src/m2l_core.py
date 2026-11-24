#!/usr/bin/env python
"""
m2l_core.py -- milestone M2, stream L (chat F2-03): the label-free PER-RECORDING protocol (SzScan 1.0 baseline).
Design: results/m2l/DESIGN_L2.md (approved by the author 23/11/2026 14:19). Written before any L2 / L3 output.

The V5 chain is run on a ONE-FILE context: the four quantities V5 fits per patient (z-score statistics, per-channel latent
reference, percentiles, alarm budget) are fitted on the recording itself; everything else is the record code, imported
read only (through eur_abl -> r2_r1, whose import guard requires every record module to come from this repository):
  signal path      x1_external.load_18 (CHB-MIT bipolar; Siena referential -> 18 derivations, 256 Hz),
                   x1_external.filter_windows (= continuous_eval.filter_file), x1_external.window_padded (statistics
                   samples, = preprocessing.filter_window), c1b_build_trainset.graph_and_bp / f7
  model            p2_dump_seeds23.run_model (the four V5 checkpoints), inputs as eur_abl.model_inputs
  reference        per channel LedoitWolf (V5) or reweighted MCD (sklearn MinCovDet, support 0.75), squared Mahalanobis
  score            e22_test_oneshot.final_scalar, p3_levers.member_mean_z / q_of / calibrate, p2_scalars.smoothed
  detection        p2_scalars.d1_events, p3_levers.localize (cpd, hybrid), p3c_freeze.budget
  scoring          p2_scalars.score on the PATIENT context (SzCORE timescoring, files 600 s apart, V5's counts);
                   p2_scalars.short_refs / caught; e18_cpd_localizer.match_errors
Arms: S (z-score scale) in {R record mean/SD, B median and IQR/1.349 x c_ch}, C (covariance) in {LW, MCD}, F (budget) in
{F clip(q, 0.005, 0.02), N clip(q, 0, 0.02), FX fixed 0.005 (descriptive)}; k per (S, C) by p3_levers.calibrate on seed
42 over the development patients (each patient's per-recording series concatenated).
"""
import hashlib
import json
import os
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(os.environ.get("THESIS_REPO", Path(__file__).resolve().parents[1]))
for _p in ("src", "src/dataprep", "src/retrain", "src/phaseB", "src/phaseC"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import eur_abl as A                      # noqa: E402  (read only; owned by F2-02)
import e18_cpd_localizer as E18          # noqa: E402
import preprocessing as P                # noqa: E402
import continuous_eval as CE             # noqa: E402
import c1b_build_trainset as C1B         # noqa: E402

R1, R0, PS, P3L, P3C, E22, X1, PD = A.R1, A.R0, A.PS, A.P3L, A.P3C, A.E22, A.X1, A.PD
_OUT = [m.__name__ for m in (E18, P, CE, C1B) if (REPO / "src") not in Path(m.__file__).resolve().parents]
if _OUT:
    raise SystemExit(f"STOP: record modules imported from outside {REPO / 'src'}: {_OUT}")
log = R1.log

TAGS, DEV, TEST, TRAIN, EXT = A.TAGS, list(A.DEV), list(A.TEST), list(A.TRAIN), list(A.EXT)
K_RECORD = A.K_RECORD
WS, WIN = P.WIN_SAMPLES, P.WIN_S                     # 1024 samples, 4 s
SUB = P.STATS_SUBSAMPLE                              # every 10th window
S_KINDS, COVS = ("R", "B"), ("LW", "MCD")
FLOORS = {"F": (0.005, P3C.CAP), "N": (0.0, P3C.CAP), "FX": (0.005, 0.005)}
SELECT_FLOORS = ("F", "N")                           # FX is descriptive
MCD_SUPPORT = 0.75
MIN_GUARD = 76                                       # L2 provisional guard (valid windows); DESIGN §6
SEG_MIN = (5, 10, 20, 30)                            # L3-short segment lengths (min)
IQR_NORM = 1.349
CC_DESIGN = [2.041, 1.624, 1.475, 1.422, 1.794, 1.594, 1.485, 1.470, 1.818,
             1.467, 1.572, 1.488, 2.058, 1.599, 1.495, 1.418, 1.668, 1.546]   # DESIGN §4 (3 decimals)
RB1C = REPO / "results" / "r2" / "r0_data" / "rb1c" / "channels.csv"
SCR = R1.SCRATCH / "m2l"
TEST_MODE = bool(os.environ.get("R2_TEST"))


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def code_shas():
    import x1_external
    import p2_scalars
    import p3_levers
    import e22_test_oneshot
    import p2_dump_seeds23
    mods = dict(m2l_core=__file__, eur_abl=A.__file__, r2_r1=R1.__file__, r2_core=R0.__file__,
                preprocessing=P.__file__, continuous_eval=CE.__file__, c1b_build_trainset=C1B.__file__,
                x1_external=x1_external.__file__, p2_scalars=p2_scalars.__file__, p3_levers=p3_levers.__file__,
                e22_test_oneshot=e22_test_oneshot.__file__, p2_dump_seeds23=p2_dump_seeds23.__file__,
                e18_cpd_localizer=E18.__file__)
    return {n: sha16(p) for n, p in mods.items()}


def arm(s, c, f):
    return f"{s}-{c}-{f}"


# ============================================================================ c_ch (DESIGN §4)
def c_table(path=RB1C):
    """per channel: the median over the 12 training patients of sd_record_uV / iqr_uV (iqr_uV = IQR / 1.349)."""
    c = pd.read_csv(path)
    t = c[c.case.isin(TRAIN)].copy()
    if sorted(t.case.unique()) != sorted(TRAIN):
        raise SystemExit(f"STOP G-c: RB1c rows for the training patients incomplete: {sorted(t.case.unique())}")
    t["r"] = t.sd_record_uV / t.iqr_uV
    g = t.groupby("channel").r.median()
    return np.array([float(g[ch]) for ch in P.COMMON_CHANNELS])


def gate_c():
    cc = c_table()
    dev = float(np.max(np.abs(np.round(cc, 3) - np.asarray(CC_DESIGN))))
    R1._jdump(R1.out_dir() / "c_ch.json", dict(channels=list(P.COMMON_CHANNELS), c=cc.tolist(), source=str(RB1C.relative_to(REPO)),
                                               rule="median over the 12 training patients of sd_record_uV / iqr_uV"))
    R1.gate(dict(gate="G-c", status="PASS" if dev == 0.0 else "FAIL", max_abs_dev_3dec=dev, c=cc.tolist(),
                 summary=f"c_ch recomputed from RB1c = the design table to 3 decimals (max deviation {dev:.0e})"))
    return cc


# ============================================================================ statistics of one recording
def sample_index(n):
    """windows i with (i + 1) % 10 == 0: every 10th window counted from the recording's first (DESIGN §3)."""
    return np.flatnonzero((np.arange(n) + 1) % SUB == 0)


def sampled(data, notch, n):
    idx = sample_index(n)
    if not len(idx):
        raise ValueError("fewer than 10 windows: no statistics sample")
    return np.concatenate([X1.window_padded(data, int(i), notch) for i in idx], axis=1)


def stats_of(X, kind, cc=None):
    """X [18, samples] -> (centre, scale) in volts, float64; scale <= 0 -> 1 (as the record)."""
    if kind == "R":
        mu, sd = X.mean(axis=1), X.std(axis=1, ddof=1)
    elif kind == "B":
        q75, q25 = np.percentile(X, [75, 25], axis=1)
        mu, sd = np.median(X, axis=1), (q75 - q25) / IQR_NORM * np.asarray(cc, float)
    else:
        raise ValueError(kind)
    sd = np.where(sd > 0, sd, 1.0)
    return mu.astype(np.float64), sd.astype(np.float64)


def pooled_record_stats(datas, notch):
    """G-stats1 (b): x1_external.labelfree_stats' rule over several recordings with ONE counter (patient level)."""
    acc, cnt = [], 0
    for data in datas:
        for i in range(data.shape[1] // WS):
            cnt += 1
            if cnt % SUB == 0:
                acc.append(X1.window_padded(data, i, notch))
    X = np.concatenate(acc, axis=1)
    sd = X.std(axis=1, ddof=1)
    sd[sd <= 0] = 1.0
    return X.mean(axis=1), sd


# ============================================================================ one recording -> features
def features(data, notch, seizures, stats, buffer=True, flag_thr=None):
    """the x1_external.file_features construction with given statistics (every window built); labels for the scorer
    only. flag_thr (smoke only): the c1b 5-SD flag, so that the .npz compares with the earlier one (G-feat1)."""
    filt, n = X1.filter_windows(data, notch)
    seg = data[:, :n * WS].reshape(data.shape[0], n, WS)
    sl = np.all(seg.std(axis=2) < 1e-10, axis=0)
    secs = n * WIN
    lab = P.build_labels(secs, seizures).reshape(n, WIN).max(axis=1) == 1
    buf = P.build_buffer_mask(secs, seizures).reshape(n, WIN).any(axis=1) if buffer else np.zeros(n, bool)
    mu, sd = stats
    adj, bp5, f7 = [], [], []
    for s in range(0, n, CE.CHUNK_WINDOWS):
        zw = (filt[s:s + CE.CHUNK_WINDOWS].astype(np.float64) - mu[None, :, None]) / sd[None, :, None]
        a_, b_ = C1B.graph_and_bp(zw)
        adj.append(a_); bp5.append(b_); f7.append(C1B.f7(zw))
    if flag_thr is None:
        flag = np.zeros(n, bool)
    else:
        flag = (np.abs(filt.astype(np.float64)).max(axis=2) > np.asarray(flag_thr)[None, :]).any(axis=1) & ~lab & ~buf
    return dict(adj=np.concatenate(adj), bp5=np.concatenate(bp5), f7=np.concatenate(f7), is_ictal=lab, is_buffer=buf,
                is_signal_loss=sl, is_flag5sd=flag, n=n)


def chb_files(case, view_root):
    """the record's file list of a CHB-MIT case (continuous_eval.list_files on the view; files without the 18
    channels skipped, as c1b_build_trainset.build)."""
    CE.DATASET_DIR = Path(view_root) / "chbmit"
    out = []
    for e in CE.list_files(case):
        out.append((CE.edf_path(case, e["fname"]), [tuple(s) for s in e["seizures"]], "chb", 60.0))
    return out


def ext_files(case, complete_root):
    files, meta = X1.subject_files(str(complete_root), case)
    return [(p, [tuple(s) for s in sz], meta["kind"], meta["notch"]) for p, sz in files]


# ============================================================================ latent, reference, one-file series
def latents(rec, tags=None):
    idx, adj, xn, f7 = A.model_inputs(rec)
    return idx, {t: PD.run_model(t, adj, xn, f7)[1] for t in (tags or TAGS)}


def distances(Z, cov):
    from sklearn.covariance import LedoitWolf, MinCovDet
    out = []
    for c in range(Z.shape[1]):
        X = Z[:, c, :].astype(np.float64)
        est = LedoitWolf() if cov == "LW" else MinCovDet(support_fraction=MCD_SUPPORT, random_state=0)
        out.append(est.fit(X).mahalanobis(X))
    return np.column_stack(out).astype(np.float64)


def onefile_ctx(n, ok, D=None):
    ok = np.asarray(ok, bool)
    idx = np.flatnonzero(ok)
    return dict(n=int(n), ok=ok, idx=idx, fidx=np.zeros(int(n), int), wf=np.zeros(len(idx), int), D=D or {})


def series(ctx, tag):
    x = E22.final_scalar(ctx, tag)
    smm = PS.smoothed(ctx, P3L.member_mean_z(ctx, tag), P3C.SMOOTH)
    return x, smm


def detect(ctx, x, q, floor, cap):
    """p3c_freeze.run_budget's detection lines; top = 0 -> no event."""
    top = P3C.budget(q, floor, cap)
    empty = {f: [] for f in np.unique(ctx["fidx"])}
    if not top > 0:
        return top, {"detector": dict(empty), "cpd": dict(empty), "hybrid": dict(empty)}, {"cpd": {}, "hybrid": {}}
    det = PS.d1_events(ctx, x, P3C.SMOOTH, top)
    thr = np.nanquantile(PS.smoothed(ctx, x, P3C.SMOOTH), 1 - top)
    stages, pairs = {"detector": det}, {}
    for mode in ("cpd", "hybrid"):
        stages[mode], pairs[mode] = P3L.localize(ctx, x, det, thr, mode)
    return top, stages, pairs


# ============================================================================ patient context and scoring
def patient_ctx(z):
    """the scoring bookkeeping of a patient from per-recording arrays concatenated (file_idx = recording order)."""
    ok = ~np.asarray(z["is_signal_loss"], bool)
    ict = np.asarray(z["is_ictal"], bool)
    fidx = np.asarray(z["file_idx"], int)
    zz = dict(is_ictal=ict, is_signal_loss=~ok, file_idx=fidx, is_buffer=np.asarray(z["is_buffer"], bool))
    return dict(z=zz, n=len(ict), ok=ok, fidx=fidx, ict=ict)


def score_rows(pctx, subject, tag, name, tops, stages, pairs, rows, errs, extra=None):
    """rows in p3c_freeze.run_budget's format from events keyed by the patient's file index."""
    rec_s = pctx["n"] * PS.WIN
    shorts = PS.short_refs(pctx)
    for st in ("detector", "cpd", "hybrid"):
        ev = stages[st]
        tp, fp, nr, h = PS.score(pctx, ev)
        k, ns = PS.caught(shorts, ev)
        rows.append(dict(subject=subject, seed=tag, budget=name, stage=st, top=tops, tp=tp, fp=fp, n_ref=nr,
                         nonict_h=h, short_tp=k, short_n=ns,
                         review_s=float(sum(b - a for v in ev.values() for a, b in v)), rec_s=rec_s, **(extra or {})))
    for f, ra, rb, h0, h1 in E18.match_errors(P3L.refs_of(pctx), stages["detector"]):
        c0, c1 = pairs["cpd"][(f, h0, h1)]
        y0, y1 = pairs["hybrid"][(f, h0, h1)]
        errs.append(dict(subject=subject, seed=tag, budget=name, det_on=h0 - ra, det_off=h1 - rb, cpd_on=c0 - ra,
                         cpd_off=c1 - rb, hyb_on=y0 - ra, hyb_off=y1 - rb, **(extra or {})))


# ============================================================================ segments (L3-short; DESIGN §7)
def segment_cuts(n, seizures, minutes):
    """consecutive segments of `minutes` from the start; a remainder < L/2 joins the previous segment; a cut inside an
    annotated seizure moves to that seizure's offset (window units; seizures in seconds)."""
    L = int(minutes * 60 // WIN)
    sz_w = [(int(a // WIN), int(-(-b // WIN))) for a, b in seizures]
    cuts, a = [], 0
    while a < n:
        b = min(n, a + L)
        moved = True
        while moved:
            moved = False
            for s0, s1 in sz_w:
                if s0 < b < s1:
                    b, moved = min(n, s1), True
        if n - b < L / 2:
            b = n
        cuts.append((a, b))
        a = b
    return cuts


def seg_seizures(seizures, a_w, b_w):
    """seizures (s) inside segment [a_w, b_w) windows, shifted to the segment start (cuts never split a seizure)."""
    a_s, b_s = a_w * WIN, b_w * WIN
    return [(s0 - a_s, s1 - a_s) for s0, s1 in seizures if s0 >= a_s and s1 <= b_s + WIN]


# ============================================================================ per-recording job (pool)
def rec_job(a):
    """one recording (or one segment of it): statistics of kind S on the recording, features, latents of the 4 V5
    seeds, distances LW and MCD, the one-file series x / smm per (cov, seed); saved to SCRATCH; returns metadata.
    a = (case, fi, path, kind, notch, seizures, S, cc, seg, out_npz, guard, covs)  seg = None | (a_w, b_w);
    guard = dict(min_valid, min_n): fewer valid windows or fewer windows -> no latent, no series (no event)"""
    case, fi, path, kind, notch, seizures, S, cc, seg, out_npz, guard, covs = a
    t = time.time()
    try:
        R0._limit_threads()
        data = X1.load_18(Path(path), kind)
        if data is None:
            return dict(case=case, fi=fi, file=Path(path).name, skipped=True, s=round(time.time() - t, 1),
                        shas=code_shas())
        buf_full = None
        if seg is not None:
            n_full = data.shape[1] // WS
            buf_full = P.build_buffer_mask(n_full * WIN, seizures).reshape(n_full, WIN).any(axis=1)
            data = data[:, seg[0] * WS:seg[1] * WS]
            seizures = seg_seizures(seizures, *seg)
        n = data.shape[1] // WS
        mu, sd = stats_of(sampled(data, notch, n), S, cc)
        rec = features(data, notch, seizures, (mu, sd), buffer=(kind == "chb"))
        if buf_full is not None:
            rec["is_buffer"] = buf_full[seg[0]:seg[1]]
        del data
        ok = ~rec["is_signal_loss"]
        nvalid = int(ok.sum())
        arrays = dict(n=np.int64(n), is_ictal=rec["is_ictal"], is_buffer=rec["is_buffer"],
                      is_signal_loss=rec["is_signal_loss"], mu=mu, sd=sd)
        short = nvalid < max(int(guard["min_valid"]), 17) or n < int(guard["min_n"])
        timing = {}
        if not short:
            t1 = time.time()
            idx, Z = latents(rec)
            timing["gae_s"] = round(time.time() - t1, 1)
            for cov in covs:
                t1 = time.time()
                D = {tag: distances(Z[tag], cov) for tag in TAGS}
                timing[f"{cov}_s"] = round(time.time() - t1, 1)
                ctx = onefile_ctx(n, ok, D)
                for tag in TAGS:
                    x, smm = series(ctx, tag)
                    arrays[f"x_{cov}_{tag}"], arrays[f"smm_{cov}_{tag}"] = x, smm
        Path(out_npz).parent.mkdir(parents=True, exist_ok=True)
        np.savez(str(out_npz) + ".tmp.npz", **arrays)
        Path(str(out_npz) + ".tmp.npz").replace(out_npz)
        return dict(case=case, fi=fi, file=Path(path).name, seg=None if seg is None else list(seg), skipped=False,
                    n=n, valid=nvalid, short=bool(short), hours=n * WIN / 3600, npz=str(out_npz),
                    s=round(time.time() - t, 1), shas=code_shas(), **timing,
                    peak_rss_mb=round(__import__("resource").getrusage(0).ru_maxrss / 1024, 1))
    except SystemExit as e:
        return dict(case=case, fi=fi, file=Path(path).name, error=f"STOP: {e}")
    except Exception:                    # noqa: BLE001
        return dict(case=case, fi=fi, file=Path(path).name, error=traceback.format_exc()[-3000:])


def _one_segment(data, kind, notch, seizures, S, cc, guard, covs, out_npz, buf):
    """rec_job's per-recording body on an array already loaded (L3-short: one EDF read for all its segments)."""
    n = data.shape[1] // WS
    mu, sd = stats_of(sampled(data, notch, n), S, cc)
    rec = features(data, notch, seizures, (mu, sd), buffer=False)
    rec["is_buffer"] = buf
    ok = ~rec["is_signal_loss"]
    nvalid = int(ok.sum())
    arrays = dict(n=np.int64(n), is_ictal=rec["is_ictal"], is_buffer=rec["is_buffer"],
                  is_signal_loss=rec["is_signal_loss"], mu=mu, sd=sd)
    short = nvalid < max(int(guard["min_valid"]), 17) or n < int(guard["min_n"])
    timing = {}
    if not short:
        t1 = time.time()
        idx, Z = latents(rec)
        timing["gae_s"] = round(time.time() - t1, 1)
        for cov in covs:
            t1 = time.time()
            D = {tag: distances(Z[tag], cov) for tag in TAGS}
            timing[f"{cov}_s"] = round(time.time() - t1, 1)
            ctx = onefile_ctx(n, ok, D)
            for tag in TAGS:
                x, smm = series(ctx, tag)
                arrays[f"x_{cov}_{tag}"], arrays[f"smm_{cov}_{tag}"] = x, smm
    Path(out_npz).parent.mkdir(parents=True, exist_ok=True)
    np.savez(str(out_npz) + ".tmp.npz", **arrays)
    Path(str(out_npz) + ".tmp.npz").replace(out_npz)
    return dict(n=n, valid=nvalid, short=bool(short), hours=n * WIN / 3600, npz=str(out_npz), **timing)


def rec_job_multi(a):
    """L3-short (added 24/11, before any L3 output): ONE job per EDF for all its segments of every length, so that the
    file is read once and one process serves many short segments (one process per segment would cost about 10 h of
    start-up alone). Each segment is processed exactly as rec_job processes a recording.
    a = (case, fi, path, kind, notch, seizures, S, cc, segs, guard, covs); segs = [(label, (a_w, b_w), out_npz)]."""
    case, fi, path, kind, notch, seizures, S, cc, segs, guard, covs = a
    t = time.time()
    try:
        R0._limit_threads()
        data_full = X1.load_18(Path(path), kind)
        if data_full is None:
            return dict(case=case, fi=fi, file=Path(path).name, multi=[
                dict(case=lab, fi=fi, file=Path(path).name, seg=list(sg), skipped=True, s=0.0, shas=code_shas())
                for lab, sg, _ in segs], s=round(time.time() - t, 1), shas=code_shas())
        n_full = data_full.shape[1] // WS
        buf_full = P.build_buffer_mask(n_full * WIN, seizures).reshape(n_full, WIN).any(axis=1)
        out, sh = [], code_shas()
        for lab, sg, out_npz in segs:
            t0 = time.time()
            r = _one_segment(data_full[:, sg[0] * WS:sg[1] * WS], kind, notch, seg_seizures(seizures, *sg), S, cc,
                             guard, covs, out_npz, buf_full[sg[0]:sg[1]])
            out.append(dict(case=lab, fi=fi, file=Path(path).name, seg=list(sg), skipped=False,
                            s=round(time.time() - t0, 1), shas=sh, **r))
        return dict(case=case, fi=fi, file=Path(path).name, multi=out, s=round(time.time() - t, 1), shas=sh,
                    hours=n_full * WIN / 3600,
                    peak_rss_mb=round(__import__("resource").getrusage(0).ru_maxrss / 1024, 1))
    except SystemExit as e:
        return dict(case=case, fi=fi, file=Path(path).name, error=f"STOP: {e}")
    except Exception:                    # noqa: BLE001
        return dict(case=case, fi=fi, file=Path(path).name, error=traceback.format_exc()[-3000:])


def load_recs(jobs_of_case):
    """the per-recording arrays of one patient in recording order -> (patient z, list of npz dicts)."""
    js = sorted([j for j in jobs_of_case if not j["skipped"]], key=lambda j: (j["fi"], (j.get("seg") or [0])[0]))
    recs = [dict(np.load(j["npz"])) for j in js]
    z = {k: np.concatenate([np.asarray(r[k]) for r in recs]) for k in ("is_ictal", "is_buffer", "is_signal_loss")}
    z["file_idx"] = np.concatenate([np.full(int(r["n"]), i, np.int16) for i, r in enumerate(recs)])
    return z, recs, js


def smm_patient(recs, cov, tag="clean_seed42"):
    """the patient's per-recording smoothed member-mean series concatenated (k calibration, DESIGN §4)."""
    return np.concatenate([np.asarray(r[f"smm_{cov}_{tag}"]) for r in recs if f"smm_{cov}_{tag}" in r])


def score_job(a):
    """one patient: every (cov, seed, floor) on the per-recording series; rows on the patient context.
    a = (case, set_name, S, ks {cov: k}, job metadata of the case, floors, covs)"""
    case, set_name, S, ks, jobs, floors, covs = a
    t = time.time()
    try:
        z, recs, js = load_recs(jobs)
        pctx = patient_ctx(z)
        rows, errs, frows = [], [], []
        for cov in covs:
            for tag in TAGS:
                for fl in floors:
                    floor, cap = FLOORS[fl]
                    name = arm(S, cov, fl)
                    stages = {"detector": {}, "cpd": {}, "hybrid": {}}
                    pairs = {"cpd": {}, "hybrid": {}}
                    tops = []
                    for i, (r, j) in enumerate(zip(recs, js)):
                        n, ok = int(r["n"]), ~np.asarray(r["is_signal_loss"], bool)
                        key = f"x_{cov}_{tag}"
                        if key not in r:                     # under the length guard: no event
                            q, top, st, pr = float("nan"), 0.0, {s_: {0: []} for s_ in stages}, {"cpd": {}, "hybrid": {}}
                        else:
                            q = P3L.q_of(np.asarray(r[f"smm_{cov}_{tag}"]), ks[cov])
                            top, st, pr = detect(onefile_ctx(n, ok), np.asarray(r[key]), q, floor, cap)
                        tops.append(top)
                        for s_ in stages:
                            stages[s_][i] = list(st[s_].get(0, []))
                        for m in ("cpd", "hybrid"):
                            for (f0, e0, e1), v in pr[m].items():
                                pairs[m][(i, e0, e1)] = v
                        fz = dict(is_ictal=r["is_ictal"], is_signal_loss=r["is_signal_loss"],
                                  file_idx=np.zeros(n, np.int16), is_buffer=r["is_buffer"])
                        ftp, ffp, fnr, fh = PS.score(dict(z=fz), {0: stages["cpd"][i]})
                        frows.append(dict(set=set_name, subject=case, file=j["file"], seg=json.dumps(j.get("seg")),
                                          seed=tag, budget=name, q=q, top=top, short=j["short"], valid=j["valid"],
                                          n=n, events=len(stages["cpd"][i]), tp=ftp, fp=ffp, n_ref=fnr, nonict_h=fh,
                                          review_s=float(sum(b - a_ for a_, b in stages["cpd"][i]))))
                    score_rows(pctx, case, tag, name, float(np.mean(tops)) if tops else float("nan"), stages, pairs,
                               rows, errs, dict(set=set_name))
        return dict(case=case, rows=rows, errs=errs, frows=frows, s=round(time.time() - t, 1), shas=code_shas())
    except SystemExit as e:
        return dict(case=case, error=f"STOP: {e}")
    except Exception:                    # noqa: BLE001
        return dict(case=case, error=traceback.format_exc()[-3000:])
