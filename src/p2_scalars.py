#!/usr/bin/env python
"""
p2_scalars.py -- shared builder of the stage-P2 scalar scores (no evaluation, no labels used).

subject_context(s)  loads one non-test subject (window flags, file ids, cached readouts for 4 seeds).
ensemble_scalar(ctx, tag, parts, c_arm="S9base", c_k=9, detrend=False)
    percentile rank ensemble (E17 construction): each readout -> its percentile over the patient's
    non-signal-loss windows (signal-loss windows 0.5), equal mean of `parts` among
    {"C", "L", "gamma", "gamma_dt", "recon"}. C = E16 arm `c_arm` with order statistic c_k.
    detrend=True subtracts the centred running median over 451 windows (+-15 min) inside each file
    (the E16e location-only drift correction), applied to the final scalar.
d1_events(ctx, sc, smooth, top, keep_max_s=None)  D1 events per file (seconds), identical to
    e1_normal_definition.event_grid: signal-loss windows set to NaN, per-file centred rolling mean
    (min_periods 1), threshold = (1 - top) quantile of every non-NaN smoothed value, contiguous
    supra-threshold runs, merge gaps <= 90 s. (Fixed 2026-10-07: the threshold was taken over
    non-signal-loss positions only, which changed fp by 1 on chb04 seed 2 and stopped E19.)
score(ctx, per_file)  SzCORE counts via e10_kernel_cpd.score_events (tp, fp, n_ref, non-ictal hours).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.covariance import LedoitWolf

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB", ROOT / "src" / "phaseC"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import e8_gae_v2_eval as E8            # noqa: E402
import e16_recording_baseline as E16   # noqa: E402

TEST = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}
TAGS = E16.TAGS
WIN = 4
MERGE_S = 90


def subject_context(s):
    if s in TEST or s not in E8.SUBJS:
        raise SystemExit(f"TEST GUARD: {s}")
    z = np.load(E8.DATA / f"{s}.npz", allow_pickle=True)
    idx, D, Z = E16.load_subject(s)
    c8 = np.load(E8.OUT / "scores" / f"{s}.npz")
    p2 = np.load(ROOT / "results" / "p2_seeds" / f"{s}.npz")
    n = len(z["is_ictal"]); ok = ~z["is_signal_loss"].astype(bool)
    fidx = z["file_idx"].astype(int)
    ict = z["is_ictal"].astype(bool)
    return dict(s=s, z=z, idx=idx, D=D, Z=Z, c8=c8, p2=p2, n=n, ok=ok, fidx=fidx, wf=fidx[idx],
                ict=ict, ict_ok=ict & ok, fl5=z["is_flag5sd"].astype(bool),
                nonict=~ict & ~z["is_buffer"].astype(bool) & ok,
                nh=float((~ict & ok).sum()) * WIN / 3600)


def _full(ctx, v):
    o = np.full(ctx["n"], np.nan); o[ctx["idx"]] = v; o[~ctx["ok"]] = np.nanmedian(v); return o


def pct(v, ok):
    out = np.full(len(v), 0.5)
    out[ok] = (rankdata(v[ok]) - 0.5) / ok.sum()
    return out


def detrend_file(ctx, v, width=451):
    out = v.copy()
    for f in np.unique(ctx["fidx"]):
        m = np.flatnonzero(ctx["fidx"] == f)
        x = np.where(ctx["ok"][m], v[m], np.nan)
        out[m] = v[m] - pd.Series(x).rolling(width, min_periods=1, center=True).median().fillna(0.0).values
    return out


def readout(ctx, tag, name, c_arm="S9base", c_k=9):
    src = ctx["c8"] if tag in ("clean_seed42", "clean_seed1") else ctx["p2"]
    if name == "recon":
        return _full(ctx, src[f"{tag}_recon"].astype(float))
    if name == "L":
        lat = src[f"{tag}_lat"].astype(np.float64)
        return _full(ctx, LedoitWolf().fit(lat).mahalanobis(lat))
    if name == "gamma":
        return _full(ctx, ctx["z"]["zgamma_raw"][ctx["idx"]].astype(float))
    if name == "gamma_dt":                     # E21b: gamma minus its +-15 min running median per file
        return detrend_file(ctx, _full(ctx, ctx["z"]["zgamma_raw"][ctx["idx"]].astype(float)))
    if name == "C":
        if c_k == 9:
            v, _ = E16.c_scalar(c_arm, ctx["D"][tag], ctx["Z"][tag], ctx["wf"])
        else:
            if c_arm != "S9base":
                raise SystemExit("order statistic other than 9 is defined on S9base only")
            okk = np.ones(len(ctx["D"][tag]), bool)
            Zc = np.column_stack([E16.rz(ctx["D"][tag][:, j], okk) for j in range(18)])
            v = -np.sort(-Zc, axis=1)[:, c_k - 1]
        return _full(ctx, v)
    raise SystemExit(f"unknown readout {name}")


def ensemble_scalar(ctx, tag, parts, c_arm="S9base", c_k=9, detrend=False):
    v = np.mean([pct(readout(ctx, tag, p, c_arm, c_k), ctx["ok"]) for p in parts], axis=0)
    return detrend_file(ctx, v) if detrend else v


def _runs(mask):
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


def merge(ev):
    out = []
    for a, b in sorted(ev):
        if out and a - out[-1][1] <= MERGE_S:
            out[-1] = (out[-1][0], max(b, out[-1][1]))
        else:
            out.append((a, b))
    return out


def smoothed(ctx, sc, smooth):
    sm = np.full(len(sc), np.nan)
    for f in np.unique(ctx["fidx"]):
        m = ctx["fidx"] == f
        sm[m] = pd.Series(np.where(ctx["ok"][m], sc[m], np.nan)).rolling(smooth, min_periods=1, center=True).mean().values
    return sm


def d1_events(ctx, sc, smooth, top, keep_max_s=None, merge_events=True):
    sm = smoothed(ctx, sc, smooth)
    thr = np.nanquantile(sm, 1 - top)          # as e1_normal_definition.event_grid: every non-NaN smoothed value
    ev = {}
    for f in np.unique(ctx["fidx"]):
        m = np.flatnonzero(ctx["fidx"] == f)
        e = [(a * WIN, b * WIN) for a, b in _runs(np.nan_to_num(sm[m], nan=-np.inf) > thr)]
        e = merge(e) if merge_events else e
        ev[f] = [x for x in e if keep_max_s is None or x[1] - x[0] <= keep_max_s]
    return ev


def score(ctx, per_file):
    import e10_kernel_cpd as E10
    tp, fp, nr, h, durs = E10.score_events(ctx["z"], per_file)
    return tp, fp, nr, h


def short_refs(ctx, max_s=20):
    """reference seizures shorter than max_s, per file, in seconds within the file."""
    out = {}
    for f in np.unique(ctx["fidx"]):
        m = np.flatnonzero(ctx["fidx"] == f)
        out[f] = [(a * WIN, b * WIN) for a, b in _runs(ctx["ict"][m]) if (b - a) * WIN < max_s]
    return out


def caught(refs, per_file, pre=30, post=60):
    """approximate detection of each reference event: any hypothesis overlapping [onset-30 s, offset+60 s]."""
    n = k = 0
    for f, rr in refs.items():
        for a, b in rr:
            n += 1
            if any(h1 >= a - pre and h0 <= b + post for h0, h1 in per_file.get(f, [])):   # E1 overlap rule
                k += 1
    return k, n
