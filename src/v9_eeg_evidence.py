#!/usr/bin/env python
"""
v9_eeg_evidence.py -- V9-V1 (docs/prompts/V9_V1_EEG_EVIDENCE.md): real-EEG evidence for every claim
the committee questioned. Read-only on every frozen script and committed result; new output only
under results/v9_v1/ (numbers) and F:/Study/Thesis/Defense/slides/figs/eeg_evidence/<part>/ (figures).

DRAWING CONVENTION (fixed, exactly src/v9_eeg_samples.py; no AI drawing, no extra smoothing): 18
bipolar channels (preprocessing.COMMON_CHANNELS order, or the top-8-by-score subset for the slide
version), real pipeline-filtered signal (raw_eeg_view.read_segment for CHB-MIT, v9_eeg_samples.
ext_read_segment for chb24/Siena -- never reimplemented), one common uV scale per figure, grey
shading = reference annotation, teal shading = the system's own event span, a score strip (or two,
Part 5) under the traces of the unsmoothed ensemble score per 4 s window, time axis in seconds from
the event's own onset. PNG at 200 dpi. Slide version: 16:9, >=14 pt labels, 8 channels max (highest
per-channel RMS during the event, or highest attribution score for Part 6), named on the axis; the
full 18-channel version is kept as backup.

SELECTION RULES (every one fixed here, BEFORE any panel is drawn; also written to each part's own
selection.csv -- see each part's own docstring section below for the exact rule).

READ-ONLY REUSE (every number/event below comes from a frozen script's own output or its own
functions, called generically -- nothing here recomputes a score, a threshold or a localizer):
  v9_anatomy.py        -- final_events/per_seizure_rows/chb_exceed_window/ext_exceed_window/
                           chb_thresh_v/build_or_load_ext/test_ctx/_RAW cache (Parts 1,2,3,4,5).
  v9_eeg_samples.py     -- ext_read_segment, draw_panel, spacing_for (drawing primitives, Parts 2-6).
  v9_e1b_calibrate.py   -- one_pass/x_of/m_of/f_signals/calibration.json (arm F, Part 5).
  v9_e1_baselines.py    -- subject_ctx/cache_D/load_D (arm F's own B4 member, Part 5).
  p2_scalars / p3_levers-- _runs/score/caught/refs_of/localize (generic scoring, never retyped).
  eval_application_events.py / szcore_eval.py -- discover_export_paths/load_files_csv/load_events_csv/
                           load_annotation/check_files_known_to_annotation/split_boundary_events/
                           per_interval_match (Part 3 -- the SAME scorer as the committed application
                           tier, reading the per-hyp-event match mask instead of only its aggregate).
  results/v9_e2/events_all.csv -- f1-f5 per event, arm G seed clean_seed42 (Part 4; not recomputed).
  results/attribution_v8/ + results/attribution_v7/labels/source/Channel_label_approved.md -- per-
                           channel latent-anomaly scores and the author's channel labels (Part 6).

Run (one part at a time; each is independently resumable):
  python src/v9_eeg_evidence.py --smoke         (touches every part on 1-2 subjects; no real figures)
  python src/v9_eeg_evidence.py --part1
  python src/v9_eeg_evidence.py --part2
  python src/v9_eeg_evidence.py --part3
  python src/v9_eeg_evidence.py --part4
  python src/v9_eeg_evidence.py --part5
  python src/v9_eeg_evidence.py --part6
"""
import argparse
import gc
import json
import math
import sys
import threading
import time
from pathlib import Path

import numpy as np
import pandas as pd
import psutil
from scipy.signal import filtfilt, resample_poly, sosfiltfilt, welch

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402
from matplotlib.gridspec import GridSpec              # noqa: E402
import matplotlib.cm as cm                            # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB", ROOT / "src" / "phaseC",
          ROOT / "src" / "dataprep"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import v9_anatomy as V9A                # noqa: E402
import v9_eeg_samples as V9S            # noqa: E402
import v9_e1_baselines as V9E1          # noqa: E402
import v9_e1b_calibrate as V9E1B        # noqa: E402
import p2_scalars as PS                 # noqa: E402
import p3_levers as P3L                 # noqa: E402
import raw_eeg_view as RV               # noqa: E402
import x1_external as X1                # noqa: E402
import preprocessing as P               # noqa: E402
import eval_application_events as EAE   # noqa: E402
import szcore_eval as SE                # noqa: E402

OUT = ROOT / "results" / "v9_v1"
FIGROOT = Path("F:/Study/Thesis/Defense/slides/figs/eeg_evidence")
CH = list(P.COMMON_CHANNELS)
WIN = 4
FS = P.FS
RNG0 = np.random.RandomState(0)

# ============================================================================ memory discipline (V9-V1-RESUME)
# V9_V1_RESUME.md binding rule: one recording open at a time, del+gc.collect after each, stop if
# peak RSS of this process passes 8 GB. x1_external.load_18 (chb24/Siena) has no window support --
# it always reads the WHOLE file -- and v9_eeg_samples.ext_read_segment calls it with no caching of
# its own, so Part 1/2/4 (many seizures per Siena/chb24 file) were re-loading entire recordings from
# disk on every single seizure. That is the freeze. Fix here, without editing the frozen file: a
# single-slot cache on X1.load_18 itself (same return value, same callers, no new computation) so a
# given file is loaded at most once per process, with the previous array dropped (del + gc.collect)
# before the next one is read in.
RAM_LIMIT_BYTES = 8 * 1024 ** 3
_PROC = psutil.Process()


def peak_rss_mb():
    return _PROC.memory_info().rss / 1e6


class RamWatch:
    """Background sampler: tracks this process's peak RSS and hard-stops it if RAM_LIMIT_BYTES is
    crossed (checked every 2s -- fast enough to catch a runaway before the OS starts swapping)."""

    def __init__(self, label, limit_bytes=RAM_LIMIT_BYTES, interval_s=2.0):
        self.label = label
        self.limit = limit_bytes
        self.interval = interval_s
        self.peak = 0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        while not self._stop.is_set():
            rss = _PROC.memory_info().rss
            self.peak = max(self.peak, rss)
            if rss > self.limit:
                print(f"STOP: {self.label} peak RSS {rss/1e9:.2f} GB passed the 8 GB limit -- "
                      f"halting this process now (V9_V1_RESUME.md binding rule).", flush=True)
                import os
                os._exit(99)
            self._stop.wait(self.interval)

    def __enter__(self):
        self.peak = _PROC.memory_info().rss
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self._thread.join(timeout=5)
        print(f"  [{self.label}] peak RSS this process: {self.peak/1e9:.2f} GB", flush=True)
        return False


_LOAD18_SLOT = {"key": None, "data": None}


def _cached_load_18(path, kind):
    key = (str(path), kind)
    if _LOAD18_SLOT["key"] == key:
        return _LOAD18_SLOT["data"]
    if _LOAD18_SLOT["key"] is not None:
        _LOAD18_SLOT["data"] = None
        gc.collect()
    t0 = time.time()
    data = X1._load_18_uncached(path, kind)
    print(f"  [load_18] {Path(path).name} loaded in {time.time()-t0:.0f}s "
          f"({peak_rss_mb():.0f} MB RSS now)", flush=True)
    _LOAD18_SLOT["key"], _LOAD18_SLOT["data"] = key, data
    return data


X1._load_18_uncached = X1.load_18
X1.load_18 = _cached_load_18


def _outdir(part):
    d = FIGROOT / part
    d.mkdir(parents=True, exist_ok=True)
    return d


def _resout():
    OUT.mkdir(parents=True, exist_ok=True)
    return OUT


# ============================================================================ shared raw-EEG access
# V9_V1_RESUME.md binding rule, discovered live: several Siena recordings are a SINGLE continuous
# file many hours long (PN01-1.edf = 13.5 h, PN14-3.edf = 11.7 h, ...). x1_external.load_18 (frozen,
# read-only) has no window support -- it always does raw.get_data() for the WHOLE file -- so
# v9_eeg_samples.ext_read_segment (also frozen) crashed the 8 GB watchdog on PN01 (X alone is ~7 GB
# float64, plus the bipolar-diff build transiently held alongside it). Fixed here, in new code only,
# with a true windowed reader: read just [t0_s-margin, t1_s+margin) of the ORIGINAL file via
# mne.io.read_raw_edf(path, preload=False) + raw.get_data(start=, stop=), then the SAME bipolar
# differencing (x1_external.BIPOLAR/SIENA_MAP, read-only constants) + resample + filters
# (x1_external.filters, read-only) + FILTER_PAD that ext_read_segment itself uses -- never a new
# filter. Verified below (verify_siena_windowed_reader) against the frozen full-file path on PN00
# (small enough to load whole): max-abs difference printed once, at import.
_SIENA_RESAMPLE_MARGIN_S = 10.0   # native-rate padding either side so resample_poly's edge taper
                                  # (short, decaying) never reaches the FILTER_PAD'd span we keep


def siena_windowed_read(path, notch, t0_s, t1_s):
    """Windowed analogue of v9_eeg_samples.ext_read_segment for Siena ONLY (chb24/CHB-MIT files are
    short enough that the frozen full-file readers are already safe -- untouched). Returns
    (filt_uV, raw_uV, actual_t0, actual_t1) or None, same contract as ext_read_segment."""
    import mne
    raw = mne.io.read_raw_edf(str(path), preload=False, verbose=False)
    names = {}
    for ch in raw.ch_names:
        n = ch.upper().replace("EEG", "").strip().replace(" ", "")
        names[X1.SIENA_MAP.get(n, n)] = ch
    need = sorted({e for pair in X1.BIPOLAR for e in pair})
    if any(e not in names for e in need):
        return None
    raw.pick([names[e] for e in need])
    fs_native = float(raw.info["sfreq"])
    n_native = int(raw.n_times)
    pad_s = _SIENA_RESAMPLE_MARGIN_S + P.FILTER_PAD / P.FS + 1.0
    s_native = max(0, int(math.floor((t0_s - pad_s) * fs_native)))
    e_native = min(n_native, int(math.ceil((t1_s + pad_s) * fs_native)))
    if e_native <= s_native:
        return None
    X = raw.get_data(start=s_native, stop=e_native).astype(np.float64)
    del raw
    local_t0 = s_native / fs_native
    pos = {e: i for i, e in enumerate(need)}
    bip = np.stack([X[pos[a]] - X[pos[b]] for a, b in X1.BIPOLAR])
    del X
    fs_int = int(round(fs_native))
    if fs_int != P.FS:
        g = math.gcd(fs_int, P.FS)
        bip = resample_poly(bip, P.FS // g, fs_int // g, axis=1)
    n_local = bip.shape[1]
    s = int(round((t0_s - local_t0) * P.FS))
    e = int(round((t1_s - local_t0) * P.FS))
    ps, pe = max(0, s - P.FILTER_PAD), min(n_local, e + P.FILTER_PAD)
    if pe <= ps:
        return None
    seg = bip[:, ps:pe]
    sos, b, aa = X1.filters(notch)
    bp = sosfiltfilt(sos, seg, axis=1)
    notched = filtfilt(b, aa, bp, axis=1)
    off = s - ps
    e_clip = min(e, ps + seg.shape[1])
    filt = notched[:, off:off + (e_clip - s)] * 1e6
    rawf = seg[:, off:off + (e_clip - s)] * 1e6
    return filt, rawf, local_t0 + s / P.FS, local_t0 + e_clip / P.FS


def verify_siena_windowed_reader():
    """V9_V1_RESUME.md binding rule: 'verify on one segment that the result equals the pipeline
    filter (max-abs difference reported)'. PN00 is the only Siena-14 recording small enough (~1.7 GB
    total) to still run the frozen full-file path for comparison -- do that once, report, move on."""
    path = V9A.SIENA_DATA / "PN00" / "PN00-1.edf"
    t0_s, t1_s = 1100.0, 1250.0
    full = V9S.ext_read_segment(path, "siena", 50.0, t0_s, t1_s)
    win = siena_windowed_read(path, 50.0, t0_s, t1_s)
    if full is None or win is None:
        print("  [verify] siena windowed reader: SKIPPED (PN00-1.edf read failed)", flush=True)
        return
    f_full, _r1, a1, b1 = full
    f_win, _r2, a2, b2 = win
    n = min(f_full.shape[1], f_win.shape[1])
    maxdiff = float(np.max(np.abs(f_full[:, :n] - f_win[:, :n])))
    print(f"  [verify] siena windowed reader vs frozen full-file ext_read_segment on PN00-1.edf "
          f"[{t0_s},{t1_s})s: max-abs diff = {maxdiff:.6g} uV (t0 {a1:.3f}/{a2:.3f}, "
          f"t1 {b1:.3f}/{b2:.3f})", flush=True)


def read_window(subj, setname, fname, t0_s, t1_s):
    """[t0_s, t1_s) filtered uV, clipped to the file; (filt, actual_t0, actual_t1) or None.
    CHB-MIT (development/chb-test): raw_eeg_view.read_segment. chb24: v9_eeg_samples.
    ext_read_segment (frozen; chb24 is one ~1h file, already safe). Siena-14: siena_windowed_read
    (above) -- several Siena files are many hours long and the frozen full-file reader is not safe
    for those; never used for development/chb-test/chb24, which stay on the frozen path."""
    if setname in ("development", "chb-test"):
        out = RV.read_segment(subj, fname, t0_s, t1_s)
    elif subj == "chb24":
        out = V9S.ext_read_segment(V9A.CHB_DATA / subj / fname, "chb", 60.0, t0_s, t1_s)
    else:
        out = siena_windowed_read(V9A.SIENA_DATA / subj / fname, 50.0, t0_s, t1_s)
    if out is None:
        return None
    filt, _raw, a, b = out
    return filt, a, b


def thresh_v_for(subj, setname):
    """+-5 SD per-channel threshold, Volts. CHB-MIT (development/chb-test): the committed per-subject
    stats (data/processed/{subj}_stats.json, v9_anatomy.chb_thresh_v). chb24/siena-14: label-free,
    from the subject's own cached x1_external build (v9_anatomy.build_or_load_ext meta['sd'])."""
    if setname in ("development", "chb-test"):
        return V9A.chb_thresh_v(subj)
    data_root = V9A.CHB_DATA if subj == "chb24" else V9A.SIENA_DATA
    _ctx, meta = V9A.build_or_load_ext(subj, data_root)
    return 5.0 * meta["sd"]


def exceed_fn_for(subj, setname):
    if setname in ("development", "chb-test"):
        return lambda s, fn, w, t: V9A.chb_exceed_window(s, fn, w, t)
    kind_, notch = ("chb", 60.0) if subj == "chb24" else ("siena", 50.0)
    data_root = V9A.CHB_DATA if subj == "chb24" else V9A.SIENA_DATA
    return lambda s, fn, w, t: V9A.ext_exceed_window(s, kind_, notch, data_root / s / fn, w, t)


# ============================================================================ ctx/score cache (G, frozen final system)
_CTX_CACHE = {}


def ctx_and_res_G(subj, setname):
    key = (subj, setname)
    if key in _CTX_CACHE:
        return _CTX_CACHE[key]
    if setname == "development":
        ctx = V9A.dev_ctx(subj)
    elif setname == "chb-test":
        ctx = V9A.test_ctx(subj)
    else:
        data_root = V9A.CHB_DATA if subj == "chb24" else V9A.SIENA_DATA
        ctx, _ = V9A.build_or_load_ext(subj, data_root)
    res = V9A.final_events(ctx, V9A.HEAD)
    _CTX_CACHE[key] = (ctx, res)
    return ctx, res


def score_strip(ctx, res, file_id, w0, w1):
    m = np.flatnonzero(ctx["fidx"] == file_id)
    w0, w1 = max(0, w0), min(len(m), w1)
    g = m[w0:w1]
    x = res["x"][g].copy()
    x[~ctx["ok"][g]] = np.nan
    return x, w0, w1


def event_peak_score(ctx, res, file_id, onset_s, offset_s):
    """peak of the unsmoothed frozen final scalar over an event's own windows (same construction
    as v9_anatomy.false_alarm_rows's peak_score)."""
    m = np.flatnonzero(ctx["fidx"] == file_id)
    L = len(m)
    aw = max(0, min(int(onset_s // WIN), L - 1))
    bw = max(aw + 1, min(int(np.ceil(offset_s / WIN)), L))
    g = m[aw:bw]
    x = res["x"][g]
    ok = ctx["ok"][g]
    if not ok.any():
        return np.nan
    return float(np.nanmax(np.where(ok, x, np.nan)))


def file_index(ctx, fname):
    files = ctx["z"]["files"]
    m = np.flatnonzero(files == fname)
    return int(m[0]) if len(m) else None


# ============================================================================ generic EEG panel (0, 1 or 2 score strips)
def top_k_channels(filt, chan_names, k=8):
    rms = np.sqrt(np.mean(filt.astype(np.float64) ** 2, axis=1))
    order = np.argsort(-rms)[:k]
    order = np.sort(order)
    return list(order), [chan_names[i] for i in order]


def draw_eeg(ax_eeg, score_axes, filt, chan_idx, chan_names, t0, t1, title, refs, loc, event_onset,
             spacing_uV, score_specs, fontsize=6, big=False):
    """score_specs: list of (vals, score_t0, label) drawn one per ax in score_axes, in order."""
    fs_lbl = 14 if big else fontsize
    fs_tick = 11 if big else fontsize
    n = filt.shape[1]
    t = t0 - event_onset + np.arange(n) / FS
    offs = np.arange(len(chan_idx))[::-1] * spacing_uV
    lim = 1.2 * spacing_uV
    for row, ci in enumerate(chan_idx):
        y = np.clip(filt[ci], -lim, lim)
        ax_eeg.plot(t, y + offs[row], lw=0.4 if big else 0.35, color="#111111")
    ax_eeg.set_yticks(offs); ax_eeg.set_yticklabels(chan_names, fontsize=fs_tick)
    ax_eeg.set_xlim(t0 - event_onset, t1 - event_onset)
    ax_eeg.set_ylim(-1.4 * spacing_uV, offs[0] + 1.4 * spacing_uV)
    for a, b in refs:
        if b >= t0 and a <= t1:
            ax_eeg.axvspan(a - event_onset, b - event_onset, color="#808080", alpha=0.18, lw=0)
    for a, b in loc:
        if b >= t0 and a <= t1:
            ax_eeg.axvspan(a - event_onset, b - event_onset, color="#008080", alpha=0.18, lw=0)
    ax_eeg.set_title(title, fontsize=fs_lbl, loc="left")
    ax_eeg.tick_params(axis="x", labelsize=fs_tick)
    for s in ("top", "right"):
        ax_eeg.spines[s].set_visible(False)
    xb = (t0 - event_onset) + 0.012 * (t1 - t0)
    yb = -1.25 * spacing_uV
    ax_eeg.plot([xb, xb], [yb, yb + spacing_uV], color="#1f77b4", lw=1.8, solid_capstyle="butt")
    ax_eeg.text(xb + 0.008 * (t1 - t0), yb + spacing_uV * 0.5, f"{spacing_uV:g} uV", fontsize=fs_tick,
               color="#1f77b4", va="center", ha="left")

    for ax_score, (score_vals, score_t0, label) in zip(score_axes, score_specs):
        nb = len(score_vals)
        if nb:
            tb = (score_t0 - event_onset) + WIN * (np.arange(nb) + 0.5)
            ax_score.bar(tb, np.nan_to_num(score_vals, nan=0.0), width=WIN * 0.95, color="#555555")
        ax_score.set_xlim(t0 - event_onset, t1 - event_onset)
        ax_score.set_ylabel(label, fontsize=fs_tick)
        ax_score.tick_params(labelsize=fs_tick)
        for s in ("top", "right"):
            ax_score.spines[s].set_visible(False)
    (score_axes[-1] if score_axes else ax_eeg).set_xlabel("time from event onset (s)", fontsize=fs_lbl)


def spacing_for(segments):
    return V9S.spacing_for(segments)


def event_done(outdir, tag):
    """V9_V1_RESUME.md per-item resumability for the drawing loops (Parts 2/3/4/5/6): the rendered
    full18 PNG IS the per-item cache marker -- if it is already on disk, skip the (expensive) read
    + render for that item on the next run instead of redoing it."""
    return (outdir / f"{tag}_full18.png").exists()


def render_event(outdir, tag, filt, t0, t1, title, refs, loc, onset, score_specs_full, spacing=None,
                  score_label="score"):
    """Full 18-channel figure + a 16:9 slide version (top-8-RMS channels, >=14pt labels). Returns
    (full_path, slide_path)."""
    if spacing is None:
        spacing = spacing_for([filt])
    n_scores = len(score_specs_full)
    hr = [4.2] + [1.0] * n_scores
    fig = plt.figure(figsize=(8.5, 6.2 if n_scores <= 1 else 6.2 + 1.0 * (n_scores - 1)), dpi=200)
    gs = GridSpec(1 + n_scores, 1, height_ratios=hr, hspace=0.30, left=0.09, right=0.98, top=0.93, bottom=0.08)
    ax_eeg = fig.add_subplot(gs[0])
    score_axes = [fig.add_subplot(gs[1 + i]) for i in range(n_scores)]
    draw_eeg(ax_eeg, score_axes, filt, list(range(len(CH))), CH, t0, t1, title, refs, loc, onset,
             spacing, score_specs_full)
    full_path = outdir / f"{tag}_full18.png"
    fig.savefig(full_path)
    plt.close(fig)

    chan_idx, chan_names = top_k_channels(filt, CH, k=8)
    fig2 = plt.figure(figsize=(12.8, 7.2), dpi=150)
    gs2 = GridSpec(1 + n_scores, 1, height_ratios=hr, hspace=0.32, left=0.08, right=0.98, top=0.92, bottom=0.10)
    ax_eeg2 = fig2.add_subplot(gs2[0])
    score_axes2 = [fig2.add_subplot(gs2[1 + i]) for i in range(n_scores)]
    draw_eeg(ax_eeg2, score_axes2, filt, chan_idx, chan_names, t0, t1, title, refs, loc, onset,
             spacing, score_specs_full, big=True)
    slide_path = outdir / f"{tag}_slide.png"
    fig2.savefig(slide_path)
    plt.close(fig2)
    return full_path, slide_path


# ============================================================================ Part 1/2 descriptors
def seizure_descriptors(subj, setname, fname, onset_s, dur_s):
    """Measured descriptors for one annotated seizure (Common rules; no AI drawing, no extra
    smoothing -- just RMS/Welch on the pipeline-filtered signal, read once per seizure):
      amplitude ratio = median channel RMS during the seizure / RMS of the 60 s before onset
      spatial extent  = n channels with that per-channel RMS ratio > 2
      dominant freq   = peak of the median-channel Welch PSD, 1-30 Hz, during the seizure
      background busyness = share of the (up to) 10 min before onset in +-5 SD high-amplitude
        windows (v9_anatomy's own committed/label-free exceed functions, reused verbatim)."""
    out = read_window(subj, setname, fname, max(0.0, onset_s - 600.0), onset_s + dur_s)
    if out is None:
        return None
    filt, a, b = out

    def seg(t0_, t1_):
        i0 = max(0, int(round((t0_ - a) * FS)))
        i1 = min(filt.shape[1], int(round((t1_ - a) * FS)))
        return filt[:, i0:i1] if i1 > i0 else None

    ict = seg(onset_s, onset_s + dur_s)
    pre60 = seg(max(a, onset_s - 60.0), onset_s)
    if ict is None or pre60 is None or ict.shape[1] < 2 or pre60.shape[1] < 2:
        return None
    rms_ict = np.sqrt(np.mean(ict.astype(np.float64) ** 2, axis=1))
    rms_pre = np.sqrt(np.mean(pre60.astype(np.float64) ** 2, axis=1)) + 1e-9
    ratio = rms_ict / rms_pre
    amp_ratio = float(np.median(ratio))
    spatial_extent = int(np.sum(ratio > 2.0))

    nper = int(min(ict.shape[1], 4 * FS))
    nper = max(nper, 32)
    freqs, pxx = welch(ict.astype(np.float64), fs=FS, nperseg=nper, axis=1)
    med_pxx = np.median(pxx, axis=0)
    band = (freqs >= 1.0) & (freqs <= 30.0)
    dom_freq = float(freqs[band][np.argmax(med_pxx[band])]) if band.any() else np.nan

    thr_v = thresh_v_for(subj, setname)
    avail_pre_s = max(0.0, onset_s - a)
    n_win_target = int(round(600.0 / WIN))
    n_win_avail = min(n_win_target, int(avail_pre_s // WIN))
    n_hi, n_checked = 0, 0
    if setname == "siena":
        # V9_V1_RESUME.md: the frozen exceed path (exceed_fn_for -> v9_anatomy.ext_exceed_window ->
        # x1_external.load_18) re-loads the WHOLE Siena file -- the exact hazard siena_windowed_read
        # exists to avoid. Reuse the filtered span already fetched above instead (same +-5 SD rule,
        # same thr_v, just sourced from the bounded read rather than a second full-file load).
        thr_uV = thr_v * 1e6
        for wi in range(n_win_avail):
            w_end_s, w_start_s = onset_s - wi * WIN, onset_s - (wi + 1) * WIN
            if w_start_s < a:
                continue
            i0, i1 = int(round((w_start_s - a) * FS)), int(round((w_end_s - a) * FS))
            if i1 <= i0 or i1 > filt.shape[1]:
                continue
            n_checked += 1
            if np.any(np.abs(filt[:, i0:i1]) > thr_uV[:, None]):
                n_hi += 1
    else:
        exceed = exceed_fn_for(subj, setname)
        for wi in range(n_win_avail):
            local_win = int(onset_s // WIN) - 1 - wi
            if local_win < 0:
                continue
            exc = exceed(subj, fname, local_win, thr_v)
            if exc is None:
                continue
            n_checked += 1
            if exc.any():
                n_hi += 1
    busyness = (n_hi / n_checked) if n_checked > 0 else np.nan

    return dict(amp_ratio=round(amp_ratio, 4), spatial_extent=spatial_extent,
               dom_freq_hz=round(dom_freq, 2) if dom_freq == dom_freq else np.nan,
               busyness=round(busyness, 4) if busyness == busyness else np.nan,
               n_busy_windows_checked=n_checked)


def _combined_per_seizure():
    """development/chb-test/chb24 from results/v9_anatomy/per_seizure.csv (V9-T3); Siena from
    results/v9_anatomy/siena14/per_seizure.csv (V9-T4, all 14 patients -- supersedes the 3/14
    restriction V9-T3 had to use; set relabelled 'siena' here for V9-V1's own output)."""
    base = ROOT / "results" / "v9_anatomy"
    pf, ff = base / "per_seizure.csv", base / "false_alarms.csv"
    if not pf.exists() or not ff.exists():
        raise SystemExit("STOP: results/v9_anatomy/per_seizure.csv missing -- run src/v9_anatomy.py first")
    seiz = pd.read_csv(pf)
    seiz = seiz[seiz.set.isin(["development", "chb-test", "chb24"])].copy()
    p14 = base / "siena14" / "per_seizure.csv"
    if not p14.exists():
        raise SystemExit("STOP: results/v9_anatomy/siena14/per_seizure.csv missing -- run "
                         "src/v9_anatomy.py --siena-full first")
    s14 = pd.read_csv(p14)
    s14["set"] = "siena"
    seiz = pd.concat([seiz, s14], ignore_index=True)
    return seiz


LOW_CASES_SENS_LT_035 = ["chb06", "chb12", "chb13", "chb15", "chb16", "chb21"]


def part1_lowcase_check(D, res):
    """V9_V1_RESUME.md: V9-E4 showed 'mean seizure duration < 30 s' (chb06/14/16) does not separate
    the hard CHB-MIT cases well -- chb14 is 8/8 while chb13/15/12/21 fail. Mark, for every CHB-MIT
    case (development + chb-test + chb24; chb24 is also one of the 24 CHB-MIT subjects B4 was run
    on), the per-case sensitivity of B4 leave-one-case-out k (results/v9_e4/per_subject.csv, arm
    'loo', stage 'localized', tp/n_ref -- read only, not recomputed) and report the Part-1 measured
    descriptors of the six low cases (sensitivity < 0.35) against the rest. Descriptive only: no
    new metric, no claim of separability."""
    e4_path = ROOT / "results" / "v9_e4" / "per_subject.csv"
    if not e4_path.exists():
        print(f"  Part 1 lowcase check SKIPPED: {e4_path} missing", flush=True)
        return
    e4 = pd.read_csv(e4_path)
    e4 = e4[(e4.arm == "loo") & (e4.stage == "localized")].copy()
    e4["sensitivity"] = e4.tp / e4.n_ref
    sens = e4.set_index("subject")["sensitivity"].to_dict()

    chb = D[D.set.isin(["development", "chb-test", "chb24"])].copy()
    chb["b4_loo_sensitivity"] = chb.subject.map(sens)
    chb["low_case"] = chb.subject.isin(LOW_CASES_SENS_LT_035)
    chb.to_csv(res / "part1_lowcase_per_seizure.csv", index=False)

    desc_cols = ["duration_s", "amp_ratio", "spatial_extent", "dom_freq_hz", "busyness"]
    grp = chb.groupby("low_case")[desc_cols].agg(["mean", "median", "count"])
    grp.to_csv(res / "part1_lowcase_vs_rest.csv")
    print("Part 1 (also, before Part 1): B4 leave-one-case-out per-case sensitivity "
          f"(results/v9_e4/per_subject.csv) -- low cases (sens<0.35) = {LOW_CASES_SENS_LT_035}, "
          f"found in Part 1 data: {sorted(set(chb[chb.low_case].subject))}. Measured descriptors, "
          f"low (n={int(chb.low_case.sum())} seizures) vs rest (n={int((~chb.low_case).sum())}) "
          f"-> {res / 'part1_lowcase_vs_rest.csv'}:", flush=True)
    print(grp.to_string(), flush=True)


def part1(smoke=False):
    t0 = time.time()
    res = _resout()
    outdir = _outdir("part1")
    seiz = _combined_per_seizure()
    if smoke:
        seiz = pd.concat([seiz[seiz.set == "development"].head(2),
                          seiz[seiz.set == "chb-test"].head(2),
                          seiz[seiz.set == "chb24"].head(1),
                          seiz[seiz.set == "siena"].head(1)], ignore_index=True)
    print(f"Part 1 selection rule: every annotated seizure in development/chb-test/chb24/siena "
          f"(frozen system G, seed 42, after the localizer -- results/v9_anatomy/per_seizure.csv + "
          f"siena14/per_seizure.csv); descriptors computed fresh here, no hand-picking. "
          f"{len(seiz)} seizures{' (SMOKE subset)' if smoke else ''}.", flush=True)

    # ---- per-item resumable cache (V9_V1_RESUME.md: results/v9_v1/_parts/) ----
    # keyed by (set, subject, file, onset_s); a crash mid-run loses at most the one seizure being
    # read when it happened -- every seizure already described stays described on the next run.
    parts_dir = OUT / "_parts"
    parts_dir.mkdir(parents=True, exist_ok=True)
    cache_path = parts_dir / ("part1_items_smoke.csv" if smoke else "part1_items.csv")
    key_cols = ["set", "subject", "file", "onset_s"]
    row_cols = key_cols + ["duration_s", "caught", "amp_ratio", "spatial_extent", "dom_freq_hz",
                           "busyness", "n_busy_windows_checked"]
    cached_by_key = {}
    if cache_path.exists():
        prev = pd.read_csv(cache_path)
        for r in prev.itertuples():
            cached_by_key[(r.set, r.subject, r.file, int(r.onset_s))] = {c: getattr(r, c) for c in row_cols}
        print(f"  resume: {len(cached_by_key)} seizure(s) already cached in {cache_path.name}", flush=True)

    rows, n_reused, n_new = [], 0, 0
    cache_fh = open(cache_path, "a" if cache_path.exists() else "w", newline="")
    if cache_fh.tell() == 0:
        cache_fh.write(",".join(row_cols) + "\n")
    try:
        for i, r in enumerate(seiz.itertuples()):
            key = (r.set, r.subject, r.file, int(r.onset_s))
            cached = cached_by_key.get(key)
            if cached is not None:
                rows.append(cached)
                n_reused += 1
            else:
                d = seizure_descriptors(r.subject, r.set, r.file, int(r.onset_s), int(r.duration_s))
                row = dict(set=r.set, subject=r.subject, file=r.file, onset_s=r.onset_s,
                          duration_s=r.duration_s, caught=r.caught)
                row.update(d if d is not None else dict(amp_ratio=np.nan, spatial_extent=np.nan,
                                                         dom_freq_hz=np.nan, busyness=np.nan,
                                                         n_busy_windows_checked=0))
                rows.append(row)
                cache_fh.write(pd.DataFrame([row])[row_cols].to_csv(header=False, index=False))
                cache_fh.flush()
                n_new += 1
            if (i + 1) % 20 == 0:
                print(f"  {i+1}/{len(seiz)} seizures described ({n_reused} reused, {n_new} new, "
                      f"{time.time()-t0:.0f}s, {peak_rss_mb():.0f} MB RSS)", flush=True)
    finally:
        cache_fh.close()
    D = pd.DataFrame(rows)
    D.to_csv(res / "part1_descriptors.csv", index=False)
    print(f"Part 1: {len(D)} seizures described ({n_reused} reused from cache, {n_new} freshly computed) "
          f"-> {res / 'part1_descriptors.csv'} ({time.time()-t0:.0f}s)", flush=True)

    # ---- also, before Part 1 (V9_V1_RESUME.md): B4 leave-one-case-out per-case sensitivity vs the
    # measured descriptors, the six low cases (sensitivity < 0.35) against the rest -- descriptive only
    part1_lowcase_check(D, res)

    if smoke:
        print("Part 1 SMOKE done (no figures).", flush=True)
        return

    # ---- figure: each descriptor by set, caught vs missed ----
    desc_cols = ["duration_s", "amp_ratio", "spatial_extent", "dom_freq_hz", "busyness"]
    desc_labels = ["duration (s)", "amplitude ratio (ictal/pre RMS)", "spatial extent (n ch RMS>2)",
                  "dominant frequency (Hz, 1-30)", "background busyness (share of 10 min pre-onset)"]
    sets_order = ["development", "chb-test", "chb24", "siena"]
    fig, axes = plt.subplots(1, 5, figsize=(22, 4.2), dpi=150)
    for ax, col, lab in zip(axes, desc_cols, desc_labels):
        xs, ys, cs = [], [], []
        for si, s in enumerate(sets_order):
            d = D[D.set == s]
            jitter = (np.random.RandomState(42).rand(len(d)) - 0.5) * 0.3
            xs += list(si + jitter)
            ys += list(d[col])
            cs += ["#1f77b4" if c else "#d62728" for c in d.caught]
        ax.scatter(xs, ys, c=cs, s=10, alpha=0.7, linewidths=0)
        ax.set_xticks(range(len(sets_order))); ax.set_xticklabels(sets_order, fontsize=8, rotation=20)
        ax.set_title(lab, fontsize=9)
        ax.tick_params(labelsize=7)
    axes[0].scatter([], [], c="#1f77b4", label="caught")
    axes[0].scatter([], [], c="#d62728", label="missed")
    axes[0].legend(fontsize=7, loc="upper left")
    fig.suptitle("V9-V1 Part 1 -- measured hard-patient descriptors, caught vs missed (seed 42, frozen G)",
                fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(outdir / "descriptors_by_set.png")
    plt.close(fig)
    fig.set_size_inches(16, 9)
    for ax in axes:
        ax.title.set_fontsize(14); ax.tick_params(labelsize=12)
    fig.savefig(outdir / "descriptors_by_set_slide.png")
    plt.close(fig)

    # ---- gallery: median-duration seizure of every CHB-MIT patient (dev vs test, same scale) ----
    def pick_median(df, s):
        d = df[df.subject == s]
        if not len(d):
            return None
        med = d.duration_s.median()
        return d.loc[(d.duration_s - med).abs().idxmin()]

    picks = []
    for s in sorted(V9E1.DEV):
        r = pick_median(D[D.set == "development"], s)
        if r is not None:
            picks.append(dict(group="dev", subject=s, file=r.file, onset_s=int(r.onset_s),
                              duration_s=int(r.duration_s)))
    for s in sorted(V9E1.TEST):
        r = pick_median(D[D.set == "chb-test"], s)
        if r is not None:
            picks.append(dict(group="test", subject=s, file=r.file, onset_s=int(r.onset_s),
                              duration_s=int(r.duration_s)))
    pd.DataFrame(picks).to_csv(outdir / "gallery_selection.csv", index=False)
    print(f"Part 1 gallery selection rule: the seizure closest to each CHB-MIT patient's OWN median "
          f"reference-seizure duration, dev (15) and test (8) separately -> "
          f"{outdir / 'gallery_selection.csv'}", flush=True)

    segs = []
    for pk in picks:
        setname = "development" if pk["group"] == "dev" else "chb-test"
        out = read_window(pk["subject"], setname, pk["file"], max(0, pk["onset_s"] - 30),
                          pk["onset_s"] + pk["duration_s"] + 30)
        if out is None:
            continue
        filt, a, b = out
        segs.append(dict(pk=pk, filt=filt, t0=a, t1=b))
    spacing = spacing_for([s["filt"] for s in segs]) if segs else 100.0
    for group, tag in (("dev", "gallery_dev"), ("test", "gallery_test")):
        gsegs = [s for s in segs if s["pk"]["group"] == group]
        if not gsegs:
            continue
        ncols = 3
        nrows = int(np.ceil(len(gsegs) / ncols))
        fig = plt.figure(figsize=(ncols * 5.2, nrows * 2.6), dpi=130)
        gs = GridSpec(nrows, ncols, hspace=0.55, wspace=0.25, left=0.06, right=0.98, top=0.95, bottom=0.07)
        for k, sgm in enumerate(gsegs):
            r, c = divmod(k, ncols)
            ax = fig.add_subplot(gs[r, c])
            pk = sgm["pk"]
            title = f"{pk['subject']}  dur {pk['duration_s']} s (patient median)"
            draw_eeg(ax, [], sgm["filt"], list(range(len(CH))), CH, sgm["t0"], sgm["t1"], title,
                    [], [], pk["onset_s"], spacing, [])
        fig.suptitle(f"V9-V1 Part 1 -- median-duration seizure, every {group} patient (same uV scale)",
                    fontsize=10)
        fig.savefig(outdir / f"{tag}.png")
        plt.close(fig)
    print(f"Part 1 done in {time.time()-t0:.0f}s -> {outdir}", flush=True)


# ============================================================================ Part 2
def part2(smoke=False):
    t0 = time.time()
    res = _resout()
    outdir = _outdir("part2")
    dpath = res / "part1_descriptors.csv"
    if not dpath.exists():
        raise SystemExit("STOP: results/v9_v1/part1_descriptors.csv missing -- run --part1 first")
    D = pd.read_csv(dpath)
    sets = [("chb-test", "chb-test"), ("siena", "siena")]
    picks = []
    for setname, lab in sets:
        d = D[D.set == setname].dropna(subset=["duration_s", "amp_ratio"])
        if not len(d):
            continue
        med_dur, med_amp = d.duration_s.median(), d.amp_ratio.median()
        r_dur = d.loc[(d.duration_s - med_dur).abs().idxmin()]
        r_amp = d.loc[(d.amp_ratio - med_amp).abs().idxmin()]
        picks.append(dict(set=lab, kind="median-duration", subject=r_dur.subject, file=r_dur.file,
                          onset_s=int(r_dur.onset_s), duration_s=int(r_dur.duration_s)))
        picks.append(dict(set=lab, kind="median-amp-ratio", subject=r_amp.subject, file=r_amp.file,
                          onset_s=int(r_amp.onset_s), duration_s=int(r_amp.duration_s)))
    pd.DataFrame(picks).to_csv(outdir / "selection.csv", index=False)
    print(f"Part 2 selection rule (fixed before drawing): per set (chb-test, siena), the seizure "
          f"closest to that set's median duration, and the one closest to that set's median "
          f"amplitude ratio -> {outdir / 'selection.csv'}", flush=True)
    if smoke:
        picks = picks[:1]

    written = []
    for pk in picks:
        subj, setname, fname = pk["subject"], pk["set"], pk["file"]
        ctx, resG = ctx_and_res_G(subj, setname)
        fid = file_index(ctx, fname)
        if fid is None:
            print(f"  SKIP {subj} {fname}: file not found", flush=True)
            continue
        onset, dur = pk["onset_s"], pk["duration_s"]
        tag = f"{setname}_{subj}_{pk['kind']}_{onset}"
        if event_done(outdir, tag):
            written.append(str(outdir / f"{tag}_full18.png")); continue
        margin = V9S.margin_for(dur)
        t0_, t1_ = onset - margin, onset + dur + margin
        out = read_window(subj, setname, fname, t0_, t1_)
        if out is None:
            continue
        filt, a, b = out
        refs, loc = V9S.refs_and_loc(ctx, resG, fid)
        w0, w1 = int(a // WIN), int(np.ceil(b / WIN))
        svals, sw0, _ = score_strip(ctx, resG, fid, w0, w1)
        title = f"{subj}  {fname}  {pk['kind']}  duration {dur} s"
        fp, sp = render_event(outdir, tag, filt, a, b, title, refs, loc, onset,
                              [(svals, sw0 * WIN, "score")])
        written.append(str(fp))
        print(f"  {tag} -> {fp.name}", flush=True)
    print(f"Part 2 done in {time.time()-t0:.0f}s, {len(written)} panels -> {outdir}", flush=True)


# ============================================================================ Part 3
TIER2_DIR = ROOT / "web_demo" / "report_handback" / "tier2_v4"
APP_EVAL_REF = ROOT / "results" / "application_eval_v4" / "pooled.json"


def part3_load_labelled_events():
    """Loads the committed application-tier export (tier2_v4, the manifest's own hashes), labels
    every AI event TP/FP with the SAME scorer the application tier itself was scored with
    (szcore_eval.per_interval_match -- reads the SzCORE EventScoring object's own match mask, the
    identical computation score_szcore's aggregate tp/fp come from; never a re-implementation),
    after the SAME file-boundary split eval_application_events.py applies. STOPs if the aggregate
    TP count does not reproduce results/application_eval_v4/pooled.json."""
    files_csv_path, event_csv_paths = EAE.discover_export_paths(TIER2_DIR)
    files_df = EAE.load_files_csv(files_csv_path)
    events_df = pd.concat([EAE.load_events_csv(p, files_df) for p in event_csv_paths], ignore_index=True)
    annotation_by_subject = {s: EAE.load_annotation(s) for s in files_df["subject"].unique()}
    EAE.check_files_known_to_annotation(files_df, annotation_by_subject)
    events_df, _bstats = EAE.split_boundary_events(events_df, files_df)
    ai = events_df[events_df["source"] == "AI"].copy()

    rows = []
    for frow in files_df.itertuples():
        subject, fname, dur = frow.subject, frow.file_name, float(frow.duration_s)
        ann = annotation_by_subject.get(subject, {}).get(fname)
        ref_iv = list(ann["seizures"]) if ann is not None else []
        hyp_rows = ai[(ai.subject == subject) & (ai.file_name == fname)].sort_values("onset_s")
        if not len(hyp_rows):
            continue
        hyp_iv = [(float(r.onset_s), float(r.offset_s)) for r in hyp_rows.itertuples()]
        matches = SE.per_interval_match(ref_iv, hyp_iv, total_dur_s=dur)
        for r, m in zip(hyp_rows.itertuples(), matches):
            rows.append(dict(subject=subject, file_name=fname, event_id=r.event_id,
                             onset_s=m["onset_s"], offset_s=m["end_s"],
                             label="TP" if m["matched"] else "FP"))
    EV = pd.DataFrame(rows)
    ref = json.loads(APP_EVAL_REF.read_text())
    ref_tp = int(ref["pooled"]["tp"])
    n_tp = int((EV.label == "TP").sum())
    if n_tp != ref_tp:
        raise SystemExit(f"STOP: re-scored TP count {n_tp} != results/application_eval_v4/pooled.json "
                         f"pooled.tp={ref_tp} -- the application tier's own scorer must be "
                         "reproduced before any event here is trusted.")
    print(f"Part 3 gate OK: {len(EV)} AI events re-labelled with szcore_eval.per_interval_match, "
          f"{n_tp} TP (reproduces results/application_eval_v4/pooled.json pooled.tp={ref_tp})",
          flush=True)
    return EV


def part3(smoke=False):
    t0 = time.time()
    res = _resout()
    outdir = _outdir("part3")
    EV = part3_load_labelled_events()
    EV.to_csv(res / "part3_events_labelled.csv", index=False)
    print(f"Part 3 selection rule (fixed before drawing): draw every TP (expected 33); per patient, "
          f"the highest-(ensemble-score) FP plus 2 random FPs (numpy RandomState(0)); one contact "
          f"sheet per patient with every event of that patient (backup).", flush=True)

    subjects = sorted(EV.subject.unique())
    if smoke:
        subjects = subjects[:1]
    picks = []
    for subj in subjects:
        ctx, resG = ctx_and_res_G(subj, "chb-test")
        d = EV[EV.subject == subj].copy()
        scores = []
        for r in d.itertuples():
            fid = file_index(ctx, r.file_name)
            scores.append(event_peak_score(ctx, resG, fid, r.onset_s, r.offset_s) if fid is not None else np.nan)
        d["peak_score"] = scores
        tp = d[d.label == "TP"]
        fp = d[d.label == "FP"].dropna(subset=["peak_score"])
        for r in tp.itertuples():
            picks.append(dict(subject=subj, kind="TP", file=r.file_name, onset_s=r.onset_s,
                              offset_s=r.offset_s, rule="every TP"))
        if len(fp):
            top = fp.loc[fp.peak_score.idxmax()]
            picks.append(dict(subject=subj, kind="FP-top", file=top.file_name, onset_s=top.onset_s,
                              offset_s=top.offset_s, rule="highest ensemble peak score"))
            rest = fp.drop(top.name) if len(fp) > 1 else fp.iloc[0:0]
            if len(rest):
                n = min(2, len(rest))
                idx = RNG0.choice(rest.index.values, size=n, replace=False)
                for j in idx:
                    rr = rest.loc[j]
                    picks.append(dict(subject=subj, kind="FP-random", file=rr.file_name,
                                      onset_s=rr.onset_s, offset_s=rr.offset_s,
                                      rule="random FP, RandomState(0)"))
    PK = pd.DataFrame(picks)
    PK.to_csv(outdir / "selection.csv", index=False)
    if smoke:
        PK = PK.head(2)
    print(f"Part 3: {len(PK)} panels to draw ({int((PK.kind=='TP').sum())} TP) across "
          f"{len(subjects)} patient(s)", flush=True)

    written = []
    per_patient_segs = {s: [] for s in subjects}
    for pk in PK.itertuples():
        subj, fname = pk.subject, pk.file
        tag = f"{subj}_{fname.replace('.edf','')}_{pk.kind}_{int(pk.onset_s)}"
        if event_done(outdir, tag):
            written.append(str(outdir / f"{tag}_full18.png")); continue
        ctx, resG = ctx_and_res_G(subj, "chb-test")
        fid = file_index(ctx, fname)
        if fid is None:
            continue
        dur = pk.offset_s - pk.onset_s
        margin = V9S.margin_for(dur)
        t0_, t1_ = pk.onset_s - margin, pk.offset_s + margin
        out = read_window(subj, "chb-test", fname, t0_, t1_)
        if out is None:
            continue
        filt, a, b = out
        refs, _loc = V9S.refs_and_loc(ctx, resG, fid)
        w0, w1 = int(a // WIN), int(np.ceil(b / WIN))
        svals, sw0, _ = score_strip(ctx, resG, fid, w0, w1)
        loc_app = [(pk.onset_s, pk.offset_s)]   # the application's OWN exported event span (teal)
        title = f"{subj}  {fname}  {pk.kind}  app event [{pk.onset_s:.0f},{pk.offset_s:.0f}]s"
        fp, sp = render_event(outdir, tag, filt, a, b, title, refs, loc_app, pk.onset_s,
                              [(svals, sw0 * WIN, "score")])
        written.append(str(fp))
        per_patient_segs[subj].append(dict(filt=filt, t0=a, t1=b, onset=pk.onset_s, title=title,
                                           refs=refs, loc=loc_app, score_vals=svals, score_t0=sw0 * WIN))
    print(f"Part 3: {len(written)} panels drawn", flush=True)

    # ---- contact sheet per patient, every event of that patient (backup) ----
    for subj in subjects:
        if (outdir / f"contact_sheet_{subj}.png").exists():
            continue
        ctx, resG = ctx_and_res_G(subj, "chb-test")
        d = EV[EV.subject == subj]
        segs = []
        for r in d.itertuples():
            fid = file_index(ctx, r.file_name)
            if fid is None:
                continue
            dur = r.offset_s - r.onset_s
            margin = V9S.margin_for(dur)
            out = read_window(subj, "chb-test", r.file_name, r.onset_s - margin, r.offset_s + margin)
            if out is None:
                continue
            filt, a, b = out
            refs, _loc = V9S.refs_and_loc(ctx, resG, fid)
            w0, w1 = int(a // WIN), int(np.ceil(b / WIN))
            svals, sw0, _ = score_strip(ctx, resG, fid, w0, w1)
            segs.append(dict(filt=filt, t0=a, t1=b, onset=r.onset_s,
                             title=f"{subj} {r.file_name} {r.label} [{r.onset_s:.0f},{r.offset_s:.0f}]s",
                             refs=refs, loc=[(r.onset_s, r.offset_s)], score_vals=svals, score_t0=sw0*WIN))
        if not segs:
            continue
        spacing = spacing_for([s["filt"] for s in segs])
        ncols = 3
        nrows = int(np.ceil(len(segs) / ncols))
        fig = plt.figure(figsize=(ncols * 6.0, nrows * 3.4), dpi=110)
        gs = GridSpec(nrows * 2, ncols, height_ratios=[4.2, 1.0] * nrows, hspace=0.5, wspace=0.25,
                     left=0.05, right=0.98, top=0.96, bottom=0.04)
        for k, sg in enumerate(segs):
            r, c = divmod(k, ncols)
            ax_eeg = fig.add_subplot(gs[2 * r, c]); ax_sc = fig.add_subplot(gs[2 * r + 1, c])
            draw_eeg(ax_eeg, [ax_sc], sg["filt"], list(range(len(CH))), CH, sg["t0"], sg["t1"],
                    sg["title"], sg["refs"], sg["loc"], sg["onset"], spacing,
                    [(sg["score_vals"], sg["score_t0"], "score")])
        fig.savefig(outdir / f"contact_sheet_{subj}.png")
        plt.close(fig)
    print(f"Part 3 done in {time.time()-t0:.0f}s -> {outdir}", flush=True)


# ============================================================================ Part 4
FEATS4 = ["f1", "f2", "f3", "f4"]
FEAT_LABEL = dict(f1="f1 high-frequency share", f2="f2 spatial extent",
                  f3="f3 frontal-polar dominance", f4="f4 single-channel dominance")


def _ev_ctx_setname(subj):
    return "chb-test" if subj in V9E1.TEST else ("chb24" if subj == "chb24" else "siena")


def pct_rank(ref_sorted, v):
    """fraction of ref_sorted <= v (ECDF), ref_sorted must already be sorted ascending."""
    if not np.isfinite(v) or not len(ref_sorted):
        return np.nan
    return float(np.searchsorted(ref_sorted, v, side="right") / len(ref_sorted))


def part4(smoke=False):
    t0 = time.time()
    res = _resout()
    outdir = _outdir("part4")
    ev_path = ROOT / "results" / "v9_e2" / "events_all.csv"
    if not ev_path.exists():
        raise SystemExit("STOP: results/v9_e2/events_all.csv missing -- run src/v9_e2_veto.py first")
    EV = pd.read_csv(ev_path)
    EV = EV[(EV.arm == "G") & (EV.seed == "clean_seed42")]
    dev_tp = EV[(EV.set == "dev") & (EV.label == "TP")]
    ref = {f: np.sort(dev_tp[f].dropna().values) for f in FEATS4}
    print(f"Part 4 typing rule (fixed before assignment): per FP (arm G, seed clean_seed42, test+siena14), "
          f"percentile of {FEATS4} against the development-TP distribution ({len(dev_tp)} rows); "
          f"assign to the feature with the HIGHEST percentile if > 0.90, else 'unassigned'.", flush=True)

    fp = EV[(EV.set.isin(["test", "siena14"])) & (EV.label == "FP")].copy()
    if smoke:
        fp = fp.groupby("subject", group_keys=False).head(2)
    for f in FEATS4:
        fp[f"{f}_pct"] = [pct_rank(ref[f], v) for v in fp[f]]
    pct_cols = [f"{f}_pct" for f in FEATS4]
    fp["best_feat"] = fp[pct_cols].idxmax(axis=1).str.replace("_pct", "", regex=False)
    fp["best_pct"] = fp[pct_cols].max(axis=1)
    fp["fp_type"] = np.where(fp["best_pct"] > 0.90, fp["best_feat"], "unassigned")
    fp.to_csv(res / "part4_fp_types.csv", index=False)

    share = fp.groupby("fp_type").size().rename("n").reset_index()
    share["share"] = share.n / len(fp)
    share.to_csv(res / "part4_fp_type_shares.csv", index=False)
    print(share.to_string(index=False), flush=True)
    if smoke:
        print("Part 4 SMOKE done (no figures).", flush=True)
        return

    # ---- two panels per type: most extreme + median member ----
    written = []
    for typ in sorted(fp.fp_type.unique()):
        d = fp[fp.fp_type == typ]
        if typ == "unassigned":
            key = d["best_pct"]
            r_extreme = d.loc[key.idxmin()]   # least extreme on any axis -- the "most unassigned" one
        else:
            key = d[f"{typ}_pct"]
            r_extreme = d.loc[key.idxmax()]
        med = key.median()
        r_median = d.loc[(key - med).abs().idxmin()]
        for tag_kind, r in (("extreme", r_extreme), ("median", r_median)):
            tag = f"{typ}_{tag_kind}_{r.subject}_{int(r.onset_s)}"
            if event_done(outdir, tag):
                written.append(str(outdir / f"{tag}_full18.png")); continue
            setname = _ev_ctx_setname(r.subject)
            ctx, resG = ctx_and_res_G(r.subject, setname)
            files = ctx["z"]["files"]
            fid = int(r.file)
            fname = str(files[fid])
            dur = r.offset_s - r.onset_s
            margin = V9S.margin_for(dur)
            out = read_window(r.subject, setname, fname, r.onset_s - margin, r.offset_s + margin)
            if out is None:
                print(f"  SKIP {r.subject} {fname}: read failed", flush=True)
                continue
            filt, a, b = out
            refs, _loc = V9S.refs_and_loc(ctx, resG, fid)
            w0, w1 = int(a // WIN), int(np.ceil(b / WIN))
            svals, sw0, _ = score_strip(ctx, resG, fid, w0, w1)
            title = (f"{r.subject}  {fname}  FP  type={typ} ({tag_kind})  "
                    f"pct={r.get(f'{typ}_pct', r.best_pct):.2f}")
            fpth, _sp = render_event(outdir, tag, filt, a, b, title, refs, [(r.onset_s, r.offset_s)],
                                     r.onset_s, [(svals, sw0 * WIN, "score")])
            written.append(str(fpth))
    print(f"Part 4: {len(written)} type panels drawn", flush=True)

    # ---- look-alike pairs: 4 test patients with the most FPs (measured, ties alphabetical) ----
    test_fp_counts = fp[fp.set == "test"].groupby("subject").size().sort_values(ascending=False)
    top4 = sorted(test_fp_counts.index[:4].tolist())
    print(f"Part 4 look-alike rule: the 4 chb-test patients with the most FPs (G, seed42) -> {top4} "
          f"(counts {dict(test_fp_counts)})", flush=True)
    pairs = []
    for subj in top4:
        ctx, resG = ctx_and_res_G(subj, "chb-test")
        dtp = EV[(EV.set == "test") & (EV.subject == subj) & (EV.label == "TP")]
        dfp = fp[(fp.set == "test") & (fp.subject == subj)]
        if not len(dtp) or not len(dfp):
            continue
        files = ctx["z"]["files"]

        def peak_of(row):
            fid = int(row.file)
            return event_peak_score(ctx, resG, fid, row.onset_s, row.offset_s), fid, str(files[fid])

        tp_scores = [(peak_of(r), r) for r in dtp.itertuples()]
        fp_scores = [(peak_of(r), r) for r in dfp.itertuples()]
        best = None
        for (ptp, fidtp, fntp), rtp in tp_scores:
            for (pfp, fidfp, fnfp), rfp in fp_scores:
                if not (np.isfinite(ptp) and np.isfinite(pfp)):
                    continue
                dist = abs(ptp - pfp)
                if best is None or dist < best[0]:
                    best = (dist, rtp, fidtp, fntp, ptp, rfp, fidfp, fnfp, pfp)
        if best is None:
            continue
        _dist, rtp, fidtp, fntp, ptp, rfp, fidfp, fnfp, pfp = best
        pairs.append(dict(subject=subj, tp_file=fntp, tp_onset=rtp.onset_s, tp_offset=rtp.offset_s,
                          tp_peak=ptp, fp_file=fnfp, fp_onset=rfp.onset_s, fp_offset=rfp.offset_s,
                          fp_peak=pfp, abs_diff=_dist))
    PR = pd.DataFrame(pairs)
    PR.to_csv(res / "part4_lookalike_pairs.csv", index=False)
    for pr in PR.itertuples():
        if (outdir / f"lookalike_{pr.subject}.png").exists():
            continue
        ctx, resG = ctx_and_res_G(pr.subject, "chb-test")
        segs = []
        for kind, fname, onset, offset in (("TP", pr.tp_file, pr.tp_onset, pr.tp_offset),
                                           ("FP", pr.fp_file, pr.fp_onset, pr.fp_offset)):
            fid = file_index(ctx, fname)
            margin = V9S.margin_for(offset - onset)
            out = read_window(pr.subject, "chb-test", fname, onset - margin, offset + margin)
            if out is None:
                continue
            filt, a, b = out
            refs, _loc = V9S.refs_and_loc(ctx, resG, fid)
            w0, w1 = int(a // WIN), int(np.ceil(b / WIN))
            svals, sw0, _ = score_strip(ctx, resG, fid, w0, w1)
            peak = pr.tp_peak if kind == "TP" else pr.fp_peak
            segs.append(dict(kind=kind, filt=filt, t0=a, t1=b, onset=onset, refs=refs,
                             loc=[(onset, offset)], score_vals=svals, score_t0=sw0 * WIN,
                             title=f"{pr.subject} {fname} {kind} peak={peak:.3f}"))
        if len(segs) != 2:
            continue
        spacing = spacing_for([s["filt"] for s in segs])
        fig = plt.figure(figsize=(8.5, 7.4), dpi=180)
        gs = GridSpec(4, 1, height_ratios=[4.2, 1.0, 4.2, 1.0], hspace=0.45, left=0.09, right=0.98,
                     top=0.94, bottom=0.07)
        for i, sg in enumerate(segs):
            ax_eeg = fig.add_subplot(gs[2 * i]); ax_sc = fig.add_subplot(gs[2 * i + 1])
            draw_eeg(ax_eeg, [ax_sc], sg["filt"], list(range(len(CH))), CH, sg["t0"], sg["t1"],
                    sg["title"], sg["refs"], sg["loc"], sg["onset"], spacing,
                    [(sg["score_vals"], sg["score_t0"], "score")])
        fig.suptitle(f"V9-V1 Part 4 look-alike: {pr.subject} TP vs FP, closest peak score "
                    f"(|diff|={pr.abs_diff:.3f})", fontsize=9)
        fig.savefig(outdir / f"lookalike_{pr.subject}.png")
        plt.close(fig)
    print(f"Part 4 done in {time.time()-t0:.0f}s -> {outdir}", flush=True)


# ============================================================================ Part 5
def part5(smoke=False):
    t0 = time.time()
    res = _resout()
    outdir = _outdir("part5")
    cal_path = ROOT / "results" / "v9_e1b" / "calibration.json"
    g_path = ROOT / "results" / "v9_anatomy" / "per_seizure.csv"
    if not cal_path.exists() or not g_path.exists():
        raise SystemExit("STOP: results/v9_e1b/calibration.json or results/v9_anatomy/per_seizure.csv "
                         "missing -- run src/v9_e1b_calibrate.py --calibrate and src/v9_anatomy.py first")
    cal = json.loads(cal_path.read_text())
    k_f = cal["k_F"]
    Gseiz = pd.read_csv(g_path)
    Gseiz = Gseiz[Gseiz.set == "chb-test"][["subject", "file", "onset_s", "duration_s", "caught"]]
    Gseiz = Gseiz.rename(columns={"caught": "caught_G"})

    subs = V9E1.TEST[:2] if smoke else V9E1.TEST
    frows = []
    for s in subs:
        ctx = V9E1.subject_ctx(s)
        V9E1.cache_D(s)
        Dg = ctx["D"][V9E1B.HEAD]
        Db = V9E1.load_D(s, "B4")
        xf, mf = V9E1B.f_signals(ctx, Dg, Db)
        _out, _det, loc_f, _errs = V9E1B.one_pass(ctx, xf, k_f, mf, P3L.refs_of(ctx))
        res_f = dict(x=xf, loc=loc_f)
        frows += V9A.per_seizure_rows(ctx, s, "chb-test", res_f, None, None, want_amp=False)
        print(f"  {s}: F arm scored ({time.time()-t0:.0f}s)", flush=True)
    Fseiz = pd.DataFrame(frows)[["subject", "file", "onset_s", "duration_s", "caught"]]
    Fseiz = Fseiz.rename(columns={"caught": "caught_F"})

    M = Gseiz.merge(Fseiz, on=["subject", "file", "onset_s", "duration_s"], how="inner")
    M.to_csv(res / "part5_g_vs_f_seizures.csv", index=False)
    f_only = M[M.caught_F & ~M.caught_G].sort_values("duration_s")
    g_only = M[M.caught_G & ~M.caught_F].sort_values("duration_s")
    print(f"Part 5 selection rule (fixed before drawing): on {len(M)} matched reference seizures "
          f"(chb-test, seed 42, each arm at its own results/v9_e1b/calibration.json point), every "
          f"seizure caught by F but missed by G ({len(f_only)}) and vice versa ({len(g_only)}); "
          f"draw up to 3 of each, shortest first, both arms' score strips.", flush=True)
    if smoke:
        print(f"Part 5 SMOKE done: {len(f_only)} F-only, {len(g_only)} G-only on {subs}.", flush=True)
        return

    written = []
    for tag, d in (("F_only", f_only.head(3)), ("G_only", g_only.head(3))):
        for r in d.itertuples():
            subj, fname = r.subject, r.file
            onset0 = int(r.onset_s)
            tagname0 = f"{tag}_{subj}_{onset0}"
            if event_done(outdir, tagname0):
                written.append(str(outdir / f"{tagname0}_full18.png")); continue
            ctxG, resG = ctx_and_res_G(subj, "chb-test")
            ctx = V9E1.subject_ctx(subj)
            V9E1.cache_D(subj)
            Dg = ctx["D"][V9E1B.HEAD]
            Db = V9E1.load_D(subj, "B4")
            xf, mf = V9E1B.f_signals(ctx, Dg, Db)
            _out, _det, loc_f, _errs = V9E1B.one_pass(ctx, xf, k_f, mf, P3L.refs_of(ctx))
            fid = file_index(ctxG, fname)
            if fid is None:
                continue
            onset, dur = int(r.onset_s), int(r.duration_s)
            margin = V9S.margin_for(dur)
            t0_, t1_ = onset - margin, onset + dur + margin
            out = read_window(subj, "chb-test", fname, t0_, t1_)
            if out is None:
                continue
            filt, a, b = out
            refsG, locG = V9S.refs_and_loc(ctxG, resG, fid)
            w0, w1 = int(a // WIN), int(np.ceil(b / WIN))
            svalsG, swG, _ = score_strip(ctxG, resG, fid, w0, w1)
            m = np.flatnonzero(ctx["fidx"] == fid)
            svalsF = xf[m[w0:min(w1, len(m))]]
            locF_this = [(x0, x1) for x0, x1 in loc_f.get(fid, []) if x1 >= onset - 30 and x0 <= onset + dur + 60]
            title = f"{subj}  {fname}  {tag.replace('_',' ')}  duration {dur} s"
            tagname = f"{tag}_{subj}_{onset}"
            fp, sp = render_event(outdir, tagname, filt, a, b, title, refsG, locG + locF_this, onset,
                                  [(svalsG, swG * WIN, "score G"), (svalsF, w0 * WIN, "score F")])
            written.append(str(fp))
    print(f"Part 5 done in {time.time()-t0:.0f}s, {len(written)} panels -> {outdir}", flush=True)


# ============================================================================ Part 6
def _parse_channel_labels():
    """subject -> seizure_idx -> ('diffuse'|list[str]) from the author's approved labels
    (results/attribution_v7/labels/source/Channel_label_approved.md, read-only, never edited)."""
    path = ROOT / "results" / "attribution_v7" / "labels" / "source" / "Channel_label_approved.md"
    out = {}
    subj = None
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith("chb"):
            subj = line.lower()
            out[subj] = {}
            continue
        if line.startswith("-") and subj is not None:
            import re
            m = re.match(r"-\s*\*\*seizure\s+(\d+)\*?\*?:?\*?\*?\s*:?\s*(.+)", line, re.IGNORECASE)
            if not m:
                continue
            idx = int(m.group(1))
            rest = m.group(2).strip().rstrip("*").strip()
            if rest.lower().startswith("diffuse"):
                out[subj][idx] = "diffuse"
            else:
                chans = [c.strip() for c in rest.split("|") if c.strip()]
                out[subj][idx] = chans
    return out


def part6(smoke=False):
    t0 = time.time()
    res = _resout()
    outdir = _outdir("part6")
    pps_path = ROOT / "results" / "attribution_v8" / "attribution_perseizure.csv"
    scores_path = ROOT / "results" / "attribution_v8" / "attribution_scores.csv"
    blocks_path = ROOT / "results" / "attribution_v6" / "seizure_blocks.csv"
    if not pps_path.exists() or not scores_path.exists() or not blocks_path.exists():
        raise SystemExit("STOP: results/attribution_v8/ or results/attribution_v6/seizure_blocks.csv "
                         "missing -- these are frozen, read-only inputs; see the module docstring.")
    PPS = pd.read_csv(pps_path)        # focal seizures only (62 rows), AUROC defined
    SCORES = pd.read_csv(scores_path)
    SCORES = SCORES[(SCORES.seed == 42) & (SCORES["agg"] == "p95")]   # the primary L1 construction
    BLOCKS = pd.read_csv(blocks_path)
    labels = _parse_channel_labels()

    focal_best = PPS.loc[PPS.AUROC.idxmax()]
    focal_worst = PPS.loc[PPS.AUROC.idxmin()]

    diffuse_rows = []
    for subj, seizmap in labels.items():
        for idx, val in seizmap.items():
            if val == "diffuse":
                b = BLOCKS[(BLOCKS.subject == subj) & (BLOCKS.seizure_idx == idx)]
                if len(b):
                    diffuse_rows.append(dict(subject=subj, seizure_idx=idx, n_windows=int(b.iloc[0].n_windows)))
    DIF = pd.DataFrame(diffuse_rows)
    generalized = DIF.loc[DIF.n_windows.idxmax()] if len(DIF) else None

    picks = [dict(kind="focal_match", subject=focal_best.subject, seizure_idx=int(focal_best.seizure_idx),
                 rule=f"highest AUROC among focal seizures ({focal_best.AUROC:.4f})"),
             dict(kind="focal_mismatch", subject=focal_worst.subject, seizure_idx=int(focal_worst.seizure_idx),
                 rule=f"lowest AUROC among focal seizures ({focal_worst.AUROC:.4f})")]
    if generalized is not None:
        picks.append(dict(kind="generalized", subject=generalized.subject,
                          seizure_idx=int(generalized.seizure_idx),
                          rule=f"most windows among diffuse-labelled seizures ({int(generalized.n_windows)})"))
    PK = pd.DataFrame(picks)
    PK.to_csv(outdir / "selection.csv", index=False)
    print(f"Part 6 selection rule (fixed before drawing): focal_match = highest AUROC (channel "
          f"concordance) among the 62 focal seizures; focal_mismatch = lowest AUROC; generalized = "
          f"the diffuse-labelled seizure with the most windows -> {outdir / 'selection.csv'}", flush=True)
    if smoke:
        PK = PK.head(1)

    written = []
    for pk in PK.itertuples():
        subj, idx = pk.subject, pk.seizure_idx
        if (outdir / f"{pk.kind}_{subj}_s{idx}_full18.png").exists():
            written.append(str(outdir / f"{pk.kind}_{subj}_s{idx}_full18.png")); continue
        b = BLOCKS[(BLOCKS.subject == subj) & (BLOCKS.seizure_idx == idx)].iloc[0]
        onset_s, offset_s, fname = float(b.onset_s), float(b.offset_s), b.edf_file
        margin = V9S.margin_for(offset_s - onset_s)
        out = read_window(subj, "chb-test", fname, onset_s - margin, offset_s + margin)
        if out is None:
            print(f"  SKIP {subj} seizure {idx}: read failed", flush=True)
            continue
        filt, a, b_ = out
        sc = SCORES[(SCORES.subject == subj) & (SCORES.seizure_idx == idx)]
        ch_score = {r.ch_name: r.score for r in sc.itertuples()}
        scores18 = np.array([ch_score.get(c, np.nan) for c in CH])
        annotated = labels.get(subj, {}).get(idx, [])
        annotated_set = set(CH) if annotated == "diffuse" else set(annotated)

        spacing = spacing_for([filt])
        fig = plt.figure(figsize=(9.5, 6.4), dpi=200)
        gs = GridSpec(1, 2, width_ratios=[20, 1], wspace=0.04, left=0.11, right=0.90, top=0.92, bottom=0.08)
        ax = fig.add_subplot(gs[0, 0])
        title = f"{subj}  seizure {idx}  {pk.kind}  ({fname})"
        draw_eeg(ax, [], filt, list(range(len(CH))), CH, a, b_, title, [(onset_s, offset_s)], [],
                onset_s, spacing, [])
        for lbl in ax.get_yticklabels():
            if lbl.get_text() in annotated_set:
                lbl.set_color("#d62728"); lbl.set_fontweight("bold")
        ax_heat = fig.add_subplot(gs[0, 1])
        finite = scores18[np.isfinite(scores18)]
        vmin, vmax = (float(finite.min()), float(finite.max())) if len(finite) else (0.0, 1.0)
        vmax = vmax if vmax > vmin else vmin + 1.0
        norm_scores = np.clip((scores18 - vmin) / (vmax - vmin), 0, 1)
        offs = np.arange(len(CH))[::-1] * spacing
        for row, sv in enumerate(norm_scores):
            color = cm.get_cmap("Reds")(sv) if sv == sv else (0.9, 0.9, 0.9, 1.0)
            ax_heat.barh(offs[row], 1.0, height=spacing * 0.9, color=color)
        ax_heat.set_ylim(ax.get_ylim()); ax_heat.set_xlim(0, 1); ax_heat.set_xticks([])
        ax_heat.set_yticks([]); ax_heat.set_title("latent\nanomaly", fontsize=6)
        for s in ("top", "right", "left"):
            ax_heat.spines[s].set_visible(False)
        fig.text(0.5, 0.955, "XAI concordance, not localization", ha="center", fontsize=8, style="italic")
        path_full = outdir / f"{pk.kind}_{subj}_s{idx}_full18.png"
        fig.savefig(path_full)
        plt.close(fig)
        written.append(str(path_full))
        print(f"  {pk.kind}: {subj} seizure {idx} -> {path_full.name}", flush=True)
    print(f"Part 6 done in {time.time()-t0:.0f}s, {len(written)} panels -> {outdir}", flush=True)


# ============================================================================ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--part1", action="store_true")
    ap.add_argument("--part2", action="store_true")
    ap.add_argument("--part3", action="store_true")
    ap.add_argument("--part4", action="store_true")
    ap.add_argument("--part5", action="store_true")
    ap.add_argument("--part6", action="store_true")
    a = ap.parse_args()
    parts = [n for n in (1, 2, 3, 4, 5, 6) if getattr(a, f"part{n}")]
    if a.smoke and not parts:
        parts = [1, 2, 3, 4, 5, 6]
    if not parts:
        raise SystemExit("pass --part1 .. --part6 (optionally --smoke), or --smoke alone for all parts")
    if any(n in (1, 2, 4) for n in parts):
        verify_siena_windowed_reader()
    fns = {1: part1, 2: part2, 3: part3, 4: part4, 5: part5, 6: part6}
    for n in parts:
        print(f"\n==== V9-V1 Part {n} {'(SMOKE)' if a.smoke else ''} ====", flush=True)
        with RamWatch(f"Part {n}{' (smoke)' if a.smoke else ''}"):
            fns[n](smoke=a.smoke)


if __name__ == "__main__":
    main()
