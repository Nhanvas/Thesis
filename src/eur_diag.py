#!/usr/bin/env python
"""
eur_diag.py -- EUR_DIAG: the diagnostics D1 and EV of the Euréka roadmap on the V5 model (Track F, chat D31-F; design
results/eureka_d31f/STEP1_DESIGN.md §4 and ROADMAP_LOGBOOK.md, approved 19/11/2026 20:35 / 20:39). Inference only, no
selection. Written before any output.

Inputs: the record features (earlier .npz, external lf .npz), the four committed V5 checkpoints, and the raw EDF of
CHB-MIT (23 thesis cases + chb24) and Siena (14) verified by sha256 against PhysioNet in the session (r2_core.inventory).
V5's distances, scalar, budget, events and scores come from the record code through r2_r1.r10 (gates R1.0 / GE / G-k).

D1 -- can a finer time grid bring short seizures within the budget? (upper bound of a 2 s hop)
  For every reference seizure shorter than 20 s (p2_scalars.short_refs) the 4-s windows are rebuilt from the raw EDF on
  grids shifted by 0, +1, +2, +3 s around it (+-40 s), with the record filter (whole-file zero-phase, as
  continuous_eval.filter_file / x1_external.filter_windows), the patient's own z-score statistics (CHB-MIT thesis cases:
  the committed stats.json; chb24 and Siena: x1_external.labelfree_stats, as their features were built), the record
  features (c1b_build_trainset.graph_and_bp, .f7) and the V5 encoder (p2_dump_seeds23.run_model). Each shifted window is
  scored against the patient's UNSHIFTED V5 quantities: the per-channel Ledoit-Wolf fit of the latent, the per-channel
  robust z, the +-15 min running median of each member and the member's percentile ranks; the four percentiles are
  averaged and smoothed over 5 windows of the shifted grid. A seizure is within budget at a shift when its peak smoothed
  value exceeds the patient's V5 threshold (quantile 1 - top of the unshifted smoothed scalar; top = clip(q, 0.5 %, 2 %)).
  Rule (design §4.1, fixed 19/11 20:35): the 2 s-hop experiment is worth its cost only if, at the best shift, >= 3 more
  short seizures (4-seed mean, test8 + chb24 + Siena) are within budget than at shift 0. The best shift is chosen
  after seeing each seizure, so it is an upper bound (a 2 s hop samples only the 0 and +2 s phases, and doubles the
  background windows); development is reported descriptively.
  Gate G-s0 (redefined 20/11 08:30 after the first run stopped at the 0.02 tolerance; plan §12): (1) the STORED inputs
  of the shift-0 windows through this scoring path give the stored V5 scalar (max |difference| <= 1e-9: the path is
  the record's); (2) shift-0 windows whose rebuilt features are bit-identical to the stored ones give the stored scalar
  (<= 1e-9). Reported, not gated: how many shift-0 windows have rebuilt features that differ (the documented rebuild
  difference of the CHB-MIT features, R0 G-feat), their largest scalar difference, the smoothed difference and the
  number of seizure-seeds whose within-budget decision differs. D1 compares every shift with the REBUILT shift 0.

EV -- which properties of a flagged event separate a seizure from the patient's own non-seizure activity?
  Events = V5's own events (arm L2f, stage cpd: p2_scalars.d1_events + p3_levers.localize), every seed; an event is a
  seizure event if it overlaps [onset - 30 s, offset + 60 s] of a reference seizure (p2_scalars.caught's rule), otherwise
  a false-alarm event; missed seizures = references caught by no event. Gate G-ev: the events reproduce the r10 rows
  (PS.score tp / fp) for every case and seed.
  Features of each 4-s window (filtered, z-scored; the six channels of largest line length = 'top 6'), each as a robust
  z against 300 background windows of the same patient (ok, not ictal, not buffer, >= 60 s from any event; rng 0):
    rhythm     autocorrelation peak at lags 0.1-1 s; spectral-peak share (power within +-1 Hz of the 1-20 Hz peak / 1-20 Hz)
    waveform   line length; Hjorth mobility and complexity; crest factor (max |x| / RMS)
    field      channels involved (line-length robust z > 2 against each channel's background); single-channel dominance
               (max / sum of line length); contiguity (share of involved channels with an involved neighbour in the
               bipolar chain)
    artifact   high-frequency share (30-60 Hz / 1-60 Hz); frontopolar share of line length (FP1-F7, FP1-F3, FP2-F4,
               FP2-F8); flat-run fraction of the unfiltered signal (clipping); step size (max |first difference| / its MAD)
  Event value = median over the event's windows (line length also max); evolution over the event (thirds; first vs last
  window if shorter than 3 windows): |change of the dominant 1-20 Hz frequency| and log ratio of line length; duration.
  Rule (fixed 19/11 20:35, ROADMAP EV): a feature enters O1 only if its development event AUROC (seizure events vs
  false-alarm events; 4-seed mean), oriented by its pooled direction, has a patient-cluster bootstrap 95 % lower bound
  >= 0.80 (B = 2,000, rng 0, chb01 + chb21 one unit) and points the same way in >= 10 of the 15 development patients.
  Test, chb24 and Siena are descriptive; missed seizures vs false alarms descriptive.

Outputs (WORK/eureka/diag/, small files only): run_meta.json, gates.json, inventory/, r10/, d1_rows.csv, d1_seizures.csv,
D1.md, ev_events.csv, ev_auroc.csv, ev_patients.csv, EV.md, jobs.csv, SUMMARY.md.
  python src/eur_diag.py [--workers N]
Test mode (synthetic world, build container only): R2_TEST=1 (see src/eur_diag_synthetic_test.py).
"""
import hashlib
import json
import os
import platform
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

if platform.system() == "Windows" and "resource" not in sys.modules:
    import types
    _r = types.ModuleType("resource")
    _r.RUSAGE_SELF, _r.RUSAGE_CHILDREN = 0, -1
    _r.getrusage = lambda *_: types.SimpleNamespace(ru_maxrss=0)
    sys.modules["resource"] = _r

REPO = Path(os.environ.get("THESIS_REPO", Path(__file__).resolve().parents[1]))
for _p in ("src", "src/dataprep", "src/retrain", "src/phaseB", "src/phaseC"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import eur_abl as A                      # noqa: E402  (imports r2_r1 and its guard)

R1, R0, PS, P3L, P3C, E22, X1, PD, F17, E16 = A.R1, A.R0, A.PS, A.P3L, A.P3C, A.E22, A.X1, A.PD, A.F17, A.E16
log = R1.log
TAGS, DEV, TEST, EXT = A.TAGS, A.DEV, A.TEST, A.EXT
WIN, FS, NS = 4, 256, 1024
SHIFTS = (0, 1, 2, 3)
MARGIN_S = 40
N_BG = 300
B_EV = 2000
TOL_S0 = 0.02
UNIT = {"chb21": "chb01"}
CHAINS = [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11], [12, 13, 14, 15], [16, 17]]
FRONTOPOLAR = [0, 4, 8, 12]
TEST_MODE = A.TEST_MODE
STATE = R1.STATE
WIN_FEATS = ["acf_peak", "spec_peak_share", "line_length", "hjorth_mob", "hjorth_comp", "crest", "n_involved",
             "dominance", "contiguity", "hf_share", "frontopolar", "flat_frac", "step"]
EV_FEATS = ([f"{f}_med" for f in WIN_FEATS] + ["line_length_max", "evo_dfreq", "evo_amp", "duration"])


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def code_shas():
    import preprocessing as P
    import continuous_eval as CE
    import c1b_build_trainset as C1B
    return {n: sha16(p) for n, p in (("eur_diag", __file__), ("eur_abl", A.__file__), ("r2_r1", R1.__file__),
                                     ("r2_core", R0.__file__), ("preprocessing", P.__file__),
                                     ("continuous_eval", CE.__file__), ("c1b_build_trainset", C1B.__file__),
                                     ("x1_external", X1.__file__))}


def src_of(case):
    return "ext" if case in EXT else "earlier"


def set_of(case):
    return "development" if case in DEV else "test" if case in TEST else ("chb24" if case == "chb24" else "siena")


# ============================================================================ signal path (record functions)
def file_paths(case):
    """{file name: verified path} of the files the case's features were built from."""
    if case in EXT:
        root = R0.SCRATCH / "view" / "complete" / ("chbmit" if case.startswith("chb") else "siena")
        files, meta = X1.subject_files(root, case)
        return {p.name: p for p, _ in files}, files, meta
    d = R0.SCRATCH / "view" / "earlier" / "chbmit" / case
    return {p.name: p for p in sorted(d.glob("*.edf"))}, None, None


def stats_of(case, xfiles, xmeta):
    if case in EXT:
        mu, sd = X1.labelfree_stats(xfiles, xmeta["kind"], xmeta["notch"])
        return np.asarray(mu, np.float64), np.asarray(sd, np.float64)
    st = R0.committed_stats(case)
    return np.asarray(st["ch_mean_uV"], np.float64) * 1e-6, np.asarray(st["ch_std_uV"], np.float64) * 1e-6


def read_filtered(case, path, xmeta):
    """(unfiltered 18 x samples, filtered 18 x samples): the record's whole-file zero-phase filter."""
    from scipy.signal import filtfilt, sosfiltfilt
    import preprocessing as P
    if case in EXT:
        data = X1.load_18(path, xmeta["kind"])
        sos, b, a = X1.filters(xmeta["notch"])
        return data, filtfilt(b, a, sosfiltfilt(sos, data, axis=1), axis=1)
    raw = P.open_edf(path)
    data = raw.get_data()
    return data, filtfilt(P._NOTCH_B, P._NOTCH_A, sosfiltfilt(P._BP_SOS, data, axis=1), axis=1)


def windows_at(sig, starts):
    return np.stack([sig[:, s:s + NS] for s in starts]).astype(np.float32)


def graph_inputs(zw):
    """record features of z-scored windows -> model inputs (x1_external.model_outputs' conversion)."""
    import c1b_build_trainset as C1B
    adj, bp5 = C1B.graph_and_bp(zw)
    f7 = C1B.f7(zw)
    adj = adj.astype(np.float32)
    adj[~np.isfinite(adj).all(axis=(1, 2))] = 0.0
    bp5 = bp5.astype(np.float32)
    bp5[~np.isfinite(bp5)] = 0.0
    xn = (bp5 - bp5.min(axis=1, keepdims=True)) / (bp5.max(axis=1, keepdims=True) - bp5.min(axis=1, keepdims=True) + 1e-8)
    return adj, xn, f7.astype(np.float64)


# ============================================================================ per-patient V5 quantities
class Patient:
    """V5's quantities of one patient and seed from the record path (stored r10 distances) + the latent fit."""

    def __init__(self, case):
        self.case, self.src = case, src_of(case)
        self.ctx, _ = R1.ctx_from_store(case, self.src, "r10")
        self.ext = self.src == "ext"
        z, _ = R1.load_case(case, self.src)
        self.idx, self.adj, self.xn, self.f7 = A.model_inputs(z)
        self.files = [str(x) for x in (z["files"] if "files" in getattr(z, "files", z) else [])]
        self.row_of = np.full(self.ctx["n"], -1, np.int64)
        self.row_of[self.idx] = np.arange(len(self.idx))
        self.seed = {}

    def fit(self, tag):
        """latent of every window, per-channel LW fit, the stored D (G-D check), member internals, smoothed x."""
        from sklearn.covariance import LedoitWolf
        _, Z = PD.run_model(tag, self.adj, self.xn, self.f7)
        lws, D = [], []
        for c in range(Z.shape[1]):
            lw = LedoitWolf().fit(Z[:, c, :].astype(np.float64))
            lws.append(lw)
            D.append(lw.mahalanobis(Z[:, c, :].astype(np.float64)))
        D = A.conv(np.column_stack(D).astype(np.float64), self.ext)
        if not np.array_equal(D, np.asarray(self.ctx["D"][tag], np.float64)):
            raise SystemExit(f"{self.case} {tag}: recomputed distances differ from the stored r10 distances")
        ctx, wf = self.ctx, self.ctx["wf"]
        med = np.median(D, axis=0)
        mad = np.median(np.abs(D - med), axis=0) + 1e-9
        Zc = (D - med) / mad
        mem = {}
        for kk in F17.MEMBERS.values():
            v = Zc.mean(axis=1) if kk == "mean" else -np.sort(-Zc, axis=1)[:, kk - 1]
            rm = np.empty_like(v)
            for f in np.unique(wf):
                w = np.flatnonzero(wf == f)
                rm[w] = pd.Series(v[w]).rolling(451, min_periods=1, center=True).median().values
            full = PS._full(ctx, v - rm)
            mem[kk] = dict(rm=rm, sorted=np.sort(full[ctx["ok"]]), n=int(ctx["ok"].sum()))
        x = E22.final_scalar(ctx, tag)
        sm = PS.smoothed(ctx, x, P3C.SMOOTH)
        q = P3L.q_of(PS.smoothed(ctx, P3L.member_mean_z(ctx, tag), P3C.SMOOTH), A.K_RECORD)
        top = P3C.budget(q, *A.ARMS["own"])
        thr = float(np.nanquantile(sm, 1 - top))
        self.seed[tag] = dict(lws=lws, med=med, mad=mad, mem=mem, x=x, sm=sm, top=top,
                              thr=thr, smv=np.sort(sm[np.isfinite(sm)]))
        return self.seed[tag]

    def score_windows(self, tag, Zs, rows):
        """x of new windows (latents Zs) against the unshifted V5 quantities; rows = unshifted idx rows for the drift."""
        S = self.seed[tag]
        X = Zs.astype(np.float64)
        D = np.column_stack([lw.mahalanobis(X[:, c, :]) for c, lw in enumerate(S["lws"])])  # the stored D's numerics
        D = A.conv(D, self.ext)
        Zc = (D - S["med"]) / S["mad"]
        pcts = []
        for kk in F17.MEMBERS.values():
            v = Zc.mean(axis=1) if kk == "mean" else -np.sort(-Zc, axis=1)[:, kk - 1]
            m = S["mem"][kk]
            u = v - m["rm"][rows]
            lo = np.searchsorted(m["sorted"], u, "left")
            hi = np.searchsorted(m["sorted"], u, "right")
            pcts.append((lo + hi) / 2.0 / m["n"])
        return np.mean(pcts, axis=0)

    def need_q(self, tag, peak):
        S = self.seed[tag]
        return float(1.0 - np.searchsorted(S["smv"], peak, "left") / len(S["smv"]))


def nearest_row(P, f, w):
    """unshifted idx row of window w of file f (nearest ok window of the same file)."""
    m = np.flatnonzero(P.ctx["fidx"] == f)
    w = int(np.clip(w, 0, len(m) - 1))
    g = m[w]
    if P.row_of[g] >= 0:
        return int(P.row_of[g])
    ok = m[P.row_of[m] >= 0]
    return int(P.row_of[ok[np.argmin(np.abs(ok - g))]])


# ============================================================================ window features (EV)
def win_feats(W, R, bg_ll=None):
    """W [n,18,1024] filtered z-scored, R [n,18,1024] unfiltered (V). Returns dict of arrays [n] (+ ll per channel)."""
    n = len(W)
    d = np.diff(W, axis=2)
    ll = np.abs(d).mean(axis=2)                                   # [n,18]
    top = np.argsort(-ll, axis=1)[:, :6]
    sel = lambda A_: np.take_along_axis(A_, top[:, :, None], axis=1)  # noqa: E731
    Wt = sel(W) - sel(W).mean(axis=2, keepdims=True)
    F = np.fft.rfft(Wt * np.hanning(NS)[None, None], axis=2)
    Pw = np.abs(F) ** 2
    fr = np.fft.rfftfreq(NS, 1 / FS)
    b120 = (fr >= 1) & (fr <= 20)
    b160 = (fr >= 1) & (fr <= 60)
    b3060 = (fr >= 30) & (fr <= 60)
    pk = fr[b120][np.argmax(Pw[:, :, b120], axis=2)]              # [n,6]
    near = np.abs(fr[None, None, :] - pk[:, :, None]) <= 1.0
    share = (Pw * (near & b120[None, None])).sum(2) / (Pw[:, :, b120].sum(2) + 1e-30)
    Fa = np.fft.rfft(Wt, n=2 * NS, axis=2)
    ac = np.fft.irfft(np.abs(Fa) ** 2, axis=2)[:, :, :NS]
    ac = ac / (ac[:, :, :1] + 1e-30)
    acp = ac[:, :, 26:257].max(axis=2)
    dW = np.diff(Wt, axis=2)
    ddW = np.diff(dW, axis=2)
    mob = np.sqrt(dW.var(axis=2) / (Wt.var(axis=2) + 1e-30))
    comp = np.sqrt(ddW.var(axis=2) / (dW.var(axis=2) + 1e-30)) / (mob + 1e-30)
    crest = np.abs(Wt).max(axis=2) / (np.sqrt((Wt ** 2).mean(axis=2)) + 1e-30)
    meanspec = Pw.mean(axis=1)
    dom = fr[b120][np.argmax(meanspec[:, b120], axis=1)]
    out = dict(acf_peak=acp.mean(1), spec_peak_share=share.mean(1), line_length=sel(ll[:, :, None])[:, :, 0].mean(1),
               hjorth_mob=mob.mean(1), hjorth_comp=comp.mean(1), crest=crest.mean(1),
               hf_share=(Pw[:, :, b3060].sum(2) / (Pw[:, :, b160].sum(2) + 1e-30)).mean(1),
               dominance=ll.max(1) / (ll.sum(1) + 1e-30), frontopolar=ll[:, FRONTOPOLAR].sum(1) / (ll.sum(1) + 1e-30))
    dr = np.diff(R, axis=2)
    flat = np.abs(dr) < 1e-12
    runs = flat[:, :, 2:] & flat[:, :, 1:-1] & flat[:, :, :-2]
    out["flat_frac"] = runs.mean(axis=2).max(axis=1)
    mad = np.median(np.abs(dr - np.median(dr, axis=2, keepdims=True)), axis=2) + 1e-15
    out["step"] = np.log((np.abs(dr).max(axis=2) / mad).max(axis=1))
    if bg_ll is not None:
        med = np.median(bg_ll, axis=0)
        mad_ = np.median(np.abs(bg_ll - med), axis=0) + 1e-12
        inv = ((ll - med) / mad_) > 2
        out["n_involved"] = inv.sum(1).astype(float)
        nb = np.zeros_like(inv)
        for ch in CHAINS:
            for i, c in enumerate(ch):
                nbrs = [ch[j] for j in (i - 1, i + 1) if 0 <= j < len(ch)]
                nb[:, c] = inv[:, c] & inv[:, nbrs].any(axis=1) if nbrs else False
        out["contiguity"] = np.where(inv.sum(1) > 0, nb.sum(1) / np.maximum(inv.sum(1), 1), 0.0)
    out["_ll"], out["_dom"] = ll, dom
    return out


def event_values(F, bg):
    """F: window features of one event (dict of arrays); bg: dict feature -> (median, MAD) of the background."""
    rz = {k: (F[k] - bg[k][0]) / bg[k][1] for k in WIN_FEATS}
    v = {f"{k}_med": float(np.median(rz[k])) for k in WIN_FEATS}
    v["line_length_max"] = float(np.max(rz["line_length"]))
    n = len(F["line_length"])
    k3 = max(1, n // 3)
    a, b = slice(0, k3), slice(n - k3, n)
    v["evo_dfreq"] = float(abs(np.median(F["_dom"][b]) - np.median(F["_dom"][a])))
    v["evo_amp"] = float(np.log((np.mean(F["line_length"][b]) + 1e-12) / (np.mean(F["line_length"][a]) + 1e-12)))
    return v


# ============================================================================ the per-patient job
def case_job(a):
    case, logdir = a
    t = time.time()
    try:
        R0._limit_threads()
        PS_ = Patient(case)
        ctx = PS_.ctx
        pmap, xfiles, xmeta = file_paths(case)
        fname = {i: PS_.files[i] for i in range(len(PS_.files))} if PS_.files else {}
        mu, sd = stats_of(case, xfiles, xmeta)
        stats_rel = None
        if case in EXT:                               # R0.4 kept the statistics it used in the .npz meta
            _, meta = R1.load_case(case, "ext")
            mm = np.asarray(meta["labelfree_mean_uV"], float) * 1e-6
            ss = np.asarray(meta["labelfree_std_uV"], float) * 1e-6
            stats_rel = float(max(np.max(np.abs(mu - mm) / np.maximum(np.abs(mm), 1e-30)),
                                  np.max(np.abs(sd - ss) / ss)))
        refs = P3L.refs_of(ctx)
        shorts = PS.short_refs(ctx)
        d1_rows, ev_rows, gev, s0dev, s0path, s0feat = [], [], [], [], [], []
        events = {}                                             # (file, a, b) -> {tag: label}
        for tag in TAGS:
            S = PS_.fit(tag)
            det = PS.d1_events(ctx, S["x"], P3C.SMOOTH, S["top"])
            loc, _ = P3L.localize(ctx, S["x"], det, S["thr"], "cpd")
            tp, fp, nr, h = PS.score(ctx, loc)
            gev.append(dict(case=case, seed=tag, tp=int(tp), fp=int(fp), n_ref=int(nr)))
            for f, evs in loc.items():
                for e0, e1 in evs:
                    lab = any(e1 >= r0 - 30 and e0 <= r1 + 60 for r0, r1 in refs.get(f, []))
                    events.setdefault((int(f), int(e0), int(e1)), {})[tag] = "seizure" if lab else "false_alarm"
            for f, rr in refs.items():
                for r0, r1 in rr:
                    if not any(e1 >= r0 - 30 and e0 <= r1 + 60 for e0, e1 in loc.get(f, [])):
                        events.setdefault((int(f), int(r0), int(r1)), {})[tag] = "missed"
        # ---- background windows (ok, not ictal, not buffer, >= 60 s from any event of any seed)
        rng = np.random.default_rng(0)
        z = ctx["z"]
        buf = np.asarray(z["is_buffer"], bool) if "is_buffer" in (z.files if hasattr(z, "files") else z) else \
            np.zeros(ctx["n"], bool)
        cand = ctx["ok"] & ~ctx["ict"] & ~buf
        fidx = ctx["fidx"]
        starts_in_file = np.concatenate([np.arange((fidx == f).sum()) for f in np.unique(fidx)]) if ctx["n"] else []
        for (f, e0, e1) in events:
            m = (fidx == f) & (starts_in_file * WIN >= e0 - 60) & (starts_in_file * WIN <= e1 + 60)
            cand &= ~m
        bg_idx = np.sort(rng.choice(np.flatnonzero(cand), size=min(N_BG, int(cand.sum())), replace=False))
        # ---- per file: raw windows for background, events, short seizures (shifts)
        need = {}
        for g in bg_idx:
            need.setdefault(int(fidx[g]), {"bg": [], "ev": [], "d1": []})["bg"].append(int(starts_in_file[g]))
        for key in events:
            need.setdefault(key[0], {"bg": [], "ev": [], "d1": []})["ev"].append(key)
        for f, rr in shorts.items():
            for r in rr:
                need.setdefault(int(f), {"bg": [], "ev": [], "d1": []})["d1"].append(r)
        sig = {}

        def load(f):
            if f not in sig:
                name = fname.get(f)
                if name is None or name not in pmap:
                    raise SystemExit(f"{case}: file {f} ({name}) not in the verified view")
                sig.clear()
                sig[f] = read_filtered(case, pmap[name], xmeta)
            return sig[f]

        def zwin(f, starts):
            raw_, flt = load(f)
            W = windows_at(flt, starts)
            return (W.astype(np.float64) - mu[None, :, None]) / sd[None, :, None], windows_at(raw_, starts)

        # one pass over the files: background and event window features (field features after the background is
        # known: they need only the per-channel line length), and the D1 shifted grids
        bgF, evF = [], {}
        for f in sorted(need):
            n_f = int((fidx == f).sum())
            if need[f]["bg"]:
                Wz, Rw = zwin(f, [w * NS for w in need[f]["bg"]])
                bgF.append(win_feats(Wz, Rw))
            for key in need[f]["ev"]:
                _, e0, e1 = key
                ws = list(range(e0 // WIN, min(-(-e1 // WIN), n_f)))
                if ws:
                    Wz, Rw = zwin(f, [w * NS for w in ws])
                    evF[key] = win_feats(Wz, Rw)
            for (r0, r1) in need[f]["d1"]:
                raw_, flt = load(f)
                n_samp = flt.shape[1]
                for s in SHIFTS:
                    lo = max(0, (r0 - MARGIN_S) // WIN) * WIN + s
                    st_s = [t for t in range(lo, r1 + MARGIN_S, WIN) if t * FS + NS <= n_samp and t // WIN < n_f]
                    if not st_s:
                        continue
                    Wz, Rw = zwin(f, [t * FS for t in st_s])
                    flat = np.all(Rw.std(axis=2) < 1e-10, axis=1)
                    adj, xn, f7 = graph_inputs(Wz)
                    rows = np.array([nearest_row(PS_, f, t // WIN) for t in st_s])
                    ov = np.array([(t < r1) and (t + WIN > r0) for t in st_s])
                    for tag in TAGS:
                        _, Zs = PD.run_model(tag, adj, xn, f7)
                        x = np.where(flat, np.nan, PS_.score_windows(tag, Zs, rows))
                        sm = pd.Series(x).rolling(P3C.SMOOTH, min_periods=1, center=True).mean().values
                        peak = float(np.nanmax(sm[ov])) if ov.any() and np.isfinite(sm[ov]).any() else np.nan
                        S = PS_.seed[tag]
                        peak_rec = np.nan
                        if s == 0:
                            gw = np.flatnonzero(fidx == f)[[t // WIN for t in st_s]]
                            inner = np.zeros(len(st_s), bool)       # smoothing is truncated at a segment edge
                            inner[2:len(st_s) - 2] = True           # (not at a file edge): compare inside only
                            if st_s[0] // WIN == 0:
                                inner[:2] = True
                            if st_s[-1] // WIN == n_f - 1:
                                inner[-2:] = True
                            dev = np.where(inner, np.abs(sm - S["sm"][gw]), np.nan)
                            s0dev.append(float(np.nanmax(dev)) if np.isfinite(dev).any() else 0.0)
                            peak_rec = float(np.nanmax(S["sm"][gw][ov])) if ov.any() else np.nan
                            # path check: the STORED inputs of the same windows through this scoring path must give
                            # the stored scalar exactly; the rest of the shift-0 difference is then the features
                            rr_ = PS_.row_of[gw]
                            okw = rr_ >= 0
                            if okw.any():
                                _, Zst = PD.run_model(tag, PS_.adj[rr_[okw]], PS_.xn[rr_[okw]], PS_.f7[rr_[okw]])
                                xst = PS_.score_windows(tag, Zst, rr_[okw])
                                s0path.append(float(np.max(np.abs(xst - S["x"][gw[okw]]))))
                                aeq = np.all(adj[okw] == PS_.adj[rr_[okw]], axis=(1, 2))
                                same = lambda u, v: (u == v).reshape(len(u), -1).all(axis=1)  # noqa: E731
                                feq = aeq & same(f7[okw], PS_.f7[rr_[okw]]) & same(xn[okw], PS_.xn[rr_[okw]])
                                dx = np.abs(np.where(flat, np.nan, x)[okw] - S["x"][gw[okw]])
                                s0feat.append(dict(windows=int(okw.sum()), adj_differs=int((~aeq).sum()),
                                                   feat_differs=int((~feq).sum()),
                                                   max_dx_equal_feat=float(np.nanmax(dx[feq])) if feq.any() else 0.0,
                                                   max_dx_diff_feat=float(np.nanmax(dx[~feq])) if (~feq).any() else 0.0))
                        d1_rows.append(dict(set=set_of(case), subject=case, file=f, onset_s=r0, offset_s=r1,
                                            dur_s=r1 - r0, seed=tag, shift_s=s, peak=peak, peak_record_s0=peak_rec,
                                            thr=S["thr"], top=S["top"], within=bool(peak > S["thr"]),
                                            need_q=PS_.need_q(tag, peak) if np.isfinite(peak) else np.nan))
        sig.clear()
        bg_ll = np.concatenate([b["_ll"] for b in bgF])
        bgF = [dict(b, **win_feats_bg_fields(b, bg_ll)) for b in bgF]
        bgstat = {}
        for k in WIN_FEATS:
            v = np.concatenate([b[k] for b in bgF])
            m = float(np.median(v))
            bgstat[k] = (m, float(np.median(np.abs(v - m))) + 1e-9)
        for key, F in evF.items():
            _, e0, e1 = key
            v = event_values(dict(F, **win_feats_bg_fields(F, bg_ll)), bgstat)
            v.update(duration=float(e1 - e0))
            for tag, lab in events[key].items():
                ev_rows.append(dict(set=set_of(case), subject=case, seed=tag, file=key[0], start_s=e0, end_s=e1,
                                    label=lab, **v))
        return dict(case=case, job="case", s=round(time.time() - t, 1), d1=d1_rows, ev=ev_rows, gev=gev,
                    s0dev=max(s0dev) if s0dev else 0.0, s0path=max(s0path) if s0path else 0.0,
                    s0feat=dict(windows=sum(d["windows"] for d in s0feat), adj_differs=sum(d["adj_differs"] for d in s0feat),
                                feat_differs=sum(d["feat_differs"] for d in s0feat),
                                max_dx_equal_feat=max([d["max_dx_equal_feat"] for d in s0feat], default=0.0),
                                max_dx_diff_feat=max([d["max_dx_diff_feat"] for d in s0feat], default=0.0)), n_bg=int(len(bg_idx)), n_events=len(events), stats_rel=stats_rel,
                    shas=code_shas(), peak_rss_mb=round(__import__("resource").getrusage(0).ru_maxrss / 1024, 1))
    except SystemExit as e:
        return dict(case=case, job="case", error=f"STOP: {e}")
    except Exception:                    # noqa: BLE001
        return dict(case=case, job="case", error=traceback.format_exc()[-3000:])


def win_feats_bg_fields(b, bg_ll):
    """field features of background windows against the pooled background line length (same definition)."""
    med = np.median(bg_ll, axis=0)
    mad_ = np.median(np.abs(bg_ll - med), axis=0) + 1e-12
    inv = ((b["_ll"] - med) / mad_) > 2
    nb = np.zeros_like(inv)
    for ch in CHAINS:
        for i, c in enumerate(ch):
            nbrs = [ch[j] for j in (i - 1, i + 1) if 0 <= j < len(ch)]
            nb[:, c] = inv[:, c] & inv[:, nbrs].any(axis=1) if nbrs else False
    return dict(n_involved=inv.sum(1).astype(float),
                contiguity=np.where(inv.sum(1) > 0, nb.sum(1) / np.maximum(inv.sum(1), 1), 0.0))


# ============================================================================ readings
def d1_reading(D):
    if not len(D):
        return pd.DataFrame(), {}
    g = D.groupby(["set", "subject", "file", "onset_s", "offset_s", "dur_s", "shift_s"]).within.mean().unstack("shift_s")
    g.columns = [f"within_s{c}" for c in g.columns]
    g["within_best"] = g[[c for c in g.columns if c.startswith("within_s")]].max(axis=1)
    per_seed = D.pivot_table(index=["set", "subject", "file", "onset_s", "seed"], columns="shift_s", values="within",
                             aggfunc="max")
    best = per_seed.max(axis=1).groupby(level=[0, 1, 2, 3]).mean()
    s0 = per_seed[0].groupby(level=[0, 1, 2, 3]).mean()
    g = g.reset_index()
    key = pd.MultiIndex.from_frame(g[["set", "subject", "file", "onset_s"]])
    g["within_best_per_seed_mean"] = best.reindex(key).values
    g["within_s0_mean"] = s0.reindex(key).values
    g["gain"] = g.within_best_per_seed_mean - g.within_s0_mean
    rule_sets = ("test", "chb24", "siena")
    gain = float(g[g["set"].isin(rule_sets)].gain.sum())
    summ = dict(short_seizures=int(len(g)), by_set=g.groupby("set").size().to_dict(),
                within_s0=g.groupby("set").within_s0_mean.sum().round(2).to_dict(),
                within_best=g.groupby("set").within_best_per_seed_mean.sum().round(2).to_dict(),
                gain_rule_sets=round(gain, 2), rule="gain >= 3 on test8 + chb24 + Siena (4-seed mean)",
                rule_met=bool(gain >= 3))
    return g, summ


def auroc(y, s):
    """Mann-Whitney AUROC (ties averaged = sklearn.metrics.roc_auc_score); events with a non-finite value dropped."""
    from scipy.stats import rankdata
    y, s = np.asarray(y, bool), np.asarray(s, float)
    k = np.isfinite(s)
    y, s = y[k], s[k]
    n1 = int(y.sum())
    n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return np.nan
    r = rankdata(s)
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def ev_reading(E):
    out, pat = [], []
    sets = ["development", "test", "chb24", "siena"]
    for st in sets:
        g = E[(E["set"] == st) & E.label.isin(["seizure", "false_alarm"])].reset_index(drop=True)
        if not len(g):
            continue
        y = (g.label == "seizure").values
        seeds = {t: np.flatnonzero(g.seed.values == t) for t in sorted(g.seed.unique())}
        base = {f: np.nanmean([auroc(y[i], g[f].values[i]) for i in seeds.values()]) for f in EV_FEATS}
        boots = None
        if st == "development":
            # patient-cluster bootstrap: one resample of units serves every feature (B_EV draws, rng 0)
            rng = np.random.default_rng(0)
            unit = g.subject.map(lambda s: UNIT.get(s, s)).values
            units = sorted(set(unit))
            rows_of = {u: np.flatnonzero(unit == u) for u in units}
            boots = {f: [] for f in EV_FEATS}
            X = {f: g[f].values for f in EV_FEATS}
            sv = g.seed.values
            for _ in range(B_EV):
                pick = np.concatenate([rows_of[u] for u in rng.choice(units, size=len(units), replace=True)])
                yy, ss = y[pick], sv[pick]
                for f in EV_FEATS:
                    xx = X[f][pick]
                    boots[f].append(np.nanmean([auroc(yy[ss == t], xx[ss == t]) for t in seeds]))
        for f in EV_FEATS:
            a = base[f]
            orient = 1 if a >= 0.5 else -1
            r = dict(set=st, feature=f, comparison="seizure vs false alarm", auroc=a,
                     oriented_auroc=a if orient > 0 else 1 - a,
                     direction="higher in seizures" if orient > 0 else "lower in seizures",
                     events_seizure=int(y.sum()), events_fa=int((~y).sum()))
            if boots is not None:
                bs = np.asarray(boots[f]) if orient > 0 else 1 - np.asarray(boots[f])
                r["ci_lo"], r["ci_hi"] = float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))
                same, both = 0, 0
                for s, h in g.groupby("subject"):
                    v = auroc((h.label == "seizure").values, h[f].values)
                    pat.append(dict(feature=f, subject=s, auroc=v))
                    if np.isfinite(v):
                        both += 1
                        same += int((v - 0.5) * orient > 0)
                r["patients_same_direction"], r["patients_with_both"] = same, both
                r["rule_met"] = bool(r["ci_lo"] >= 0.80 and same >= 10)
            out.append(r)
        m = E[(E["set"] == st) & E.label.isin(["missed", "false_alarm"])]
        for f in EV_FEATS:
            a = np.nanmean([auroc((h.label == "missed").values, h[f].values) for _, h in m.groupby("seed")]) \
                if len(m) else np.nan
            out.append(dict(set=st, feature=f, comparison="missed vs false alarm (descriptive)", auroc=a,
                            events_missed=int((m.label == "missed").sum())))
    return pd.DataFrame(out), pd.DataFrame(pat)


def ev_md(R):
    d = R[(R["set"] == "development") & (R.comparison == "seizure vs false alarm")].sort_values("oriented_auroc",
                                                                                                 ascending=False)
    L = ["# EV — event properties of V5's flagged events (EUR_DIAG)", "",
         "Development: seizure events vs false-alarm events of V5 (arm L2f, after the localizer, 4 seeds); features as "
         "robust z against the patient's own background. Oriented AUROC (4-seed mean) with its patient-cluster bootstrap "
         "interval; rule: lower bound ≥ 0.80 and the same direction in ≥ 10 of 15 patients. Test, chb24 and Siena: "
         "AUROC, descriptive.", "",
         "| feature | direction | dev AUROC [95 % interval] | patients same direction | rule | test | chb24 | Siena |",
         "|---|---|---|---|---|---|---|---|"]
    for r in d.itertuples():
        oth = {st: R[(R["set"] == st) & (R.feature == r.feature) & (R.comparison == "seizure vs false alarm")]
               for st in ("test", "chb24", "siena")}
        cell = lambda st: "—" if not len(oth[st]) else f"{oth[st].oriented_auroc.iloc[0]:.2f}"  # noqa: E731
        L.append(f"| {r.feature} | {r.direction} | {r.oriented_auroc:.3f} [{r.ci_lo:.3f}, {r.ci_hi:.3f}] | "
                 f"{int(r.patients_same_direction)} of {int(r.patients_with_both)} | {'met' if r.rule_met else 'not met'} | "
                 f"{cell('test')} | {cell('chb24')} | {cell('siena')} |")
    return "\n".join(L) + "\n"


def d1_md(g, summ):
    L = ["# D1 — shifted grids for the short seizures (EUR_DIAG)", "",
         "Short seizures (< 20 s). 'within' = the peak smoothed V5 scalar of the seizure exceeds the patient's V5 "
         "threshold (arm L2f), 4-seed mean. Best shift = the best of 0, +1, +2, +3 s per seizure and seed (an upper "
         "bound of a 2 s hop).", "", f"Rule: {summ.get('rule')} → gain {summ.get('gain_rule_sets')}: "
         f"**{'met' if summ.get('rule_met') else 'not met'}**.", "",
         "| set | short seizures | within at shift 0 | within at best shift |", "|---|---|---|---|"]
    for st in ("development", "test", "chb24", "siena"):
        if st in summ.get("by_set", {}):
            L.append(f"| {st} | {summ['by_set'][st]} | {summ['within_s0'].get(st, 0)} | {summ['within_best'].get(st, 0)} |")
    L += ["", "| set | subject | onset (s) | duration (s) | within s0 | s+1 | s+2 | s+3 | best (4-seed mean) |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in g.itertuples():
        L.append(f"| {r.set} | {r.subject} | {r.onset_s} | {r.dur_s} | {getattr(r, 'within_s0', 0):.2f} | "
                 f"{getattr(r, 'within_s1', 0):.2f} | {getattr(r, 'within_s2', 0):.2f} | {getattr(r, 'within_s3', 0):.2f} "
                 f"| {r.within_best_per_seed_mean:.2f} |")
    return "\n".join(L) + "\n"


# ============================================================================ main
def _run(fn, specs, workers, what):
    out = []
    if workers <= 1:
        R1._init_worker(R1._env())
        it, pool = map(fn, specs), None
    else:
        pool = R1._pool(min(workers, len(specs)))
        it = pool.imap_unordered(fn, specs)
    try:
        for r in it:
            if r.get("error"):
                raise SystemExit(f"{what} {r['case']}: {r['error']}")
            out.append(r)
            log(f"{what} {r['case']} done ({r['s']} s)")
    finally:
        if pool is not None:
            pool.terminate()
    return out


def main(notebook="EUR_DIAG", repo_commit="local", workers=None, cases=None):
    R1.OUT_ROOT = R1.WORK / "eureka"
    workers = int(workers or os.environ.get("EUR_WORKERS") or R1.n_workers())
    meta = R1.run_meta("diag", notebook, repo_commit)
    meta.update(eur_diag_sha=sha16(__file__), code_shas=code_shas(), workers=workers)
    R1._jdump(R1.out_dir() / "run_meta.json", meta)
    R0.R0 = R1.out_dir()
    R0.STATE["tag"] = "inventory"
    inv, cases_df, _, _ = R0.inventory({"chbmit": DEV + TEST + [c for c in EXT if c.startswith("chb")],
                                        "siena": [c for c in EXT if c.startswith("PN")] or None})
    chk = {c["check"]: c["status"] for c in json.loads((R0.out_dir() / "checks.json").read_text())}
    need = ("committed data/summaries = PhysioNet summaries", "CHB-MIT chb01-23: every EDF listed in its summary")
    bad = [n for n in need if chk.get(n) != "PASS"]
    edf = inv[inv.file.str.endswith(".edf")]
    R1.gate(dict(gate="G-raw", status="PASS" if not bad else "FAIL", files=int(len(edf)), failed_checks=bad,
                 from_physionet=int(edf.source.str.startswith("physionet").sum()),
                 summary=f"{len(edf)} EDF verified by sha256 against PhysioNet"))
    src = A.build_views(DEV, TEST, EXT)
    A.gate_data(src)
    t = time.time()
    R1.r10(DEV, TEST, EXT, workers=workers, with_k=True)
    R1.phase("r10", t)
    cs = list(cases or (DEV + TEST + EXT))
    t = time.time()
    order = sorted(cs, key=lambda c: -A._size(c, src_of(c)))
    res = _run(case_job, [(c, str(R1.out_dir())) for c in order], workers, "case")
    R1.phase("cases", t)
    D = pd.DataFrame([r for x in res for r in x["d1"]])
    E = pd.DataFrame([r for x in res for r in x["ev"]])
    # outputs first, so that a gate that stops the run leaves its evidence for the diagnosis
    o = R1.out_dir()
    D.to_csv(o / "d1_rows.csv", index=False)
    E.to_csv(o / "ev_events.csv", index=False)
    g, summ = d1_reading(D)
    g.to_csv(o / "d1_seizures.csv", index=False)
    R1._jdump(o / "d1_summary.json", summ)
    (o / "D1.md").write_text(d1_md(g, summ))
    if len(E):
        Rv, Pt = ev_reading(E)
        Rv.to_csv(o / "ev_auroc.csv", index=False)
        Pt.to_csv(o / "ev_patients.csv", index=False)
        (o / "EV.md").write_text(ev_md(Rv))
    pd.DataFrame([{k: v for k, v in r.items() if k not in ("d1", "ev", "gev", "shas", "s0feat")} for r in res]).to_csv(
        o / "jobs.csv", index=False)
    gev = pd.DataFrame([r for x in res for r in x["gev"]])
    rec = pd.concat([pd.read_csv(R1.out_dir() / "r10" / f) for f in ("dev_per_subject.csv", "test_run_budget.csv")
                     if (R1.out_dir() / "r10" / f).exists()], ignore_index=True)
    rec = rec[(rec.budget == "L2f") & (rec.stage == "cpd")][["subject", "seed", "tp", "fp"]]
    xr = R1.out_dir() / "r10" / "ext_x1_rows.csv"
    mg = gev.merge(rec, left_on=["case", "seed"], right_on=["subject", "seed"], how="left", suffixes=("", "_rec"))
    chb = mg[mg.tp_rec.notna()]
    diff = chb[(chb.tp != chb.tp_rec) | (chb.fp != chb.fp_rec)]
    R1.gate(dict(gate="G-ev", status="PASS" if not len(diff) and len(chb) == len([c for c in cs if c not in EXT]) * 4
                 else "FAIL", rows=int(len(chb)), differ=diff[["case", "seed"]].values.tolist()[:20],
                 external_rows=int(len(mg) - len(chb)), x1_rows=str(xr.name),
                 summary=f"V5 events (L2f, cpd) reproduce the r10 rows for {len(chb)} CHB-MIT case-seeds; "
                         f"{len(diff)} differ (external: same functions on the r10 distances, GE-gated)"))
    s0 = max(r["s0dev"] for r in res)
    path = max(r["s0path"] for r in res)
    eqf = max(r["s0feat"]["max_dx_equal_feat"] for r in res)
    tot = {k: sum(r["s0feat"][k] for r in res) for k in ("windows", "adj_differs", "feat_differs")}
    dec = D[(D.shift_s == 0) & D.peak_record_s0.notna()] if len(D) else D
    flips = int(((dec.peak_record_s0 > dec.thr) != dec.within).sum()) if len(dec) else 0
    R1.gate(dict(gate="G-s0", status="PASS" if path <= 1e-9 and eqf <= 1e-9 else "FAIL", path_max_abs=path,
                 max_dx_where_features_equal=eqf, **tot,
                 max_dx_where_features_differ=max(r["s0feat"]["max_dx_diff_feat"] for r in res),
                 smoothed_max_abs=s0, decisions_differing=flips, decisions=int(len(dec)),
                 per_case={r["case"]: dict(smoothed=r["s0dev"], path=r["s0path"], **r["s0feat"]) for r in res},
                 summary=f"stored inputs through this path = stored scalar (max {path:.1e}); windows whose rebuilt "
                         f"features equal the stored ones give the stored scalar (max {eqf:.1e}); "
                         f"{tot['feat_differs']} of {tot['windows']} shift-0 windows have rebuilt features that differ "
                         f"(adjacency {tot['adj_differs']}); smoothed max |difference| {s0:.4f}; within-budget decision "
                         f"differs for {flips} of {len(dec)} seizure-seeds"))
    xs = {r["case"]: r["stats_rel"] for r in res if r["stats_rel"] is not None}
    R1.gate(dict(gate="G-extstats", status="PASS" if all(v <= 1e-6 for v in xs.values()) else "FAIL", per_case=xs,
                 summary=f"label-free statistics recomputed for {len(xs)} external cases = those R0.4 used (.npz meta; "
                         f"max relative {max(xs.values()) if xs else 0:.1e})"))
    parent = code_shas()
    badw = [r["case"] for r in res if r["shas"] != parent]
    R1.gate(dict(gate="G-worker", status="PASS" if not badw else "FAIL", jobs=len(res), differ=badw,
                 summary=f"{len(res)} jobs ran the parent's modules"))
    R1.finish_meta(dict(d1=summ))
    (o / "SUMMARY.md").write_text(f"# EUR_DIAG run ({notebook}, commit {repo_commit})\n\nEvery gate PASS (gates.json). "
                                  "D1: D1.md, d1_seizures.csv, d1_rows.csv. EV: EV.md, ev_auroc.csv, ev_events.csv.\n")
    log("EUR_DIAG done")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int)
    a = ap.parse_args()
    main(workers=a.workers)
