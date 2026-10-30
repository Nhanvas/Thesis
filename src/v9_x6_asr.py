#!/usr/bin/env python
"""
v9_x6_asr.py -- V9-X6 (docs/prompts/V9_X6_ASR.md): does preprocessing artifact removal (ASR)
delete seizure activity?

SCOPE (fixed by the author before this ran, 2026-10-30, after the full-scope cost was measured
on one real file and projected far past the prompt's own unmeasured 1.5-4h estimate):
  - Measure 1 (what ASR removes) + the EEG panels only. Measure 2 (effect on B4 detection,
    no retraining) is SKIPPED -- it needed seizure-free matched files and the whole B4/kNN/
    SzCORE chain; dropping it removes most of the runtime and all of that machinery.
  - Files: every seizure-containing file of the 8 CHB-MIT TEST patients + chb24 (70 files;
    58 test + 12 chb24). NO development patients, NO seizure-free matched files (only needed
    by the now-skipped Measure 2).
  - cutoff=20 (the fixed default) run on every one of the 70 files FIRST; cutoff=5 (aggressive)
    on the same files afterward, only as time allows.
  - Hard stop at 4.5 h wall time inside --run. Resumable: one part file per (file, cutoff);
    an already-done combination is skipped on restart, so an interrupted run picks up where it
    left off without recomputing finished files.
  - ONE (file, cutoff) PER OS PROCESS (found necessary, not a style choice): a validation run of
    4 sequential ASR fit+transform calls inside ONE long-lived python process grew RSS from
    ~1.4 GB to ~6.4 GB and drove this machine's free RAM down to ~1.25 GB of 16.7 GB total before
    the process exited (RAM recovered to ~7.6 GB immediately on exit -- a per-process leak inside
    asrpy/mne's internal state across repeated ASR objects, not a true system-wide leak, but fatal
    for a 140-call (70 files x 2 cutoffs) single process regardless). --run therefore shells out
    one `--process-one SUBJ FILE CUTOFF` subprocess per unit of work (python's own interpreter,
    `subprocess.run`); --panels shells out one `--extract-trace` subprocess per DISTINCT
    (subject, file, cutoff) it needs (deduplicated, so two panel picks from the same file only
    pay the ASR cost once) and reads the small cached trace back. Both give the OS a clean
    process exit to reclaim memory after every ASR call, same mitigation this codebase already
    uses elsewhere for exactly this class of problem (v9_e4_knn24.py, v9_e1b_calibrate.py: "ONE
    SUBJECT PER PROCESS").
  - FOUND A SECOND PROBLEM live during the real run (not a style choice either): asrpy's
    asr.transform() -> asr_process() -> ma_filter() builds an (n_samples_in_chunk,
    n_channels**2) intermediate array sized by its own `mem_splits` parameter (asrpy's default
    is 3); CHB-MIT files are not all ~1h, several test-patient files run 4h+, and a 4h file at
    the default split count tried to allocate 5.94 GiB and crashed with ArrayMemoryError.
    run_asr() now scales mem_splits by the file's own duration (MEM_SPLIT_CHUNK_S, ~1 min target
    per internal chunk). That alone wasn't sufficient either: two 4h files succeeded at ~1.8-1.9
    GB subprocess RSS each, but the THIRD one triggered an OS-level low-memory kill of the whole
    --run process (not a Python exception -- psutil showed only ~7.4 GB "available" of 17 GB
    total on this machine even at baseline, 9.6 GB already used by other processes). --run now
    also checks psutil.virtual_memory().available before every subprocess spawn and pauses
    (_wait_for_memory, MIN_AVAILABLE_GB) rather than launching into another likely kill.

MEASURED (one real file, chb01_03.edf, 3600 s, before this run's scope was fixed): cutoff=20
fit 73 s + transform 62 s = 135 s; cutoff=5 fit 55 s + transform 55 s = 110 s. Projected for the
70-file cutoff=20 pass alone: ~2.6 h; cutoff=5 afterward on the same 70 files: ~2.1 h more (~4.7 h
combined, so the 4.5 h stop is a real possibility for cutoff=5, not just a nominal safety net --
--run logs exactly how many files each cutoff reached if it stops early).

ASR: pip install asrpy (0.0.8), applied per recording file to the 18 bipolar channels AFTER the
pipeline band-pass (0.5-60 Hz, 4th-order Butterworth, sosfiltfilt) + notch (60 Hz, filtfilt) --
preprocessing.py's own filters, applied whole-file in one pass (continuous_eval.filter_file's own
convention, the same one c1b_build_trainset.py used to build every committed B4/GAE feature).
Calibration = asrpy's own built-in clean-window selection on the file's own data (asrpy.asr.
clean_windows, called inside ASR.fit) -- no labels read anywhere in this file except to pick which
seizures/windows to measure and to report sensitivity-irrelevant descriptive splits.

ASRPY NUMPY>=2.0 PATCH (runtime monkeypatch of the third-party asrpy PACKAGE, not a repo file
edit): asrpy 0.0.8's asr_utils.fit_eeg_distribution does `int(np.round(n * max_width))` and
`(opt_lu[1]-opt_lu[0]) / np.diff(opt_bounds)` where max_width/np.diff(opt_bounds) are 1-element
arrays; numpy>=2.0 removed the implicit ndim>0 -> scalar conversion those relied on ("only
0-dimensional arrays can be converted to Python scalars"). patch_asrpy() below re-defines the
function with `[0]` on those two lines (verified exact-match on the two target lines before
patching; STOPs loudly instead of silently diverging if a different asrpy version is installed).

WHY (reviewer question; see docs/prompts/V9_X6_ASR.md and NUMBERS_LOCK): literature plus indirect
evidence already in this repo (results/e4_artifact_rejection/: a model trained on non-seizure
high-amplitude windows calls 81.5% of seizure windows "artifact"; results/raw_eeg_view/: muscle-
band share is higher in seizure than background windows, AUROC 0.65) suggested seizure activity
resembles the kind of artifact ASR is built to remove. This measures that overlap directly and
label-free, with a standard method, instead of only by proxy.

MEASURE 1 -- share of signal power ASR removes (1 - power_after/power_before), computed on the
file's own whole-file-filtered signal before ASR vs the same file after ASR:
  - inside every reference seizure's own [onset, offset) span (exact seconds, not window-rounded)
  - the 60 s immediately before each seizure's onset (clipped to the file start)
  - label-free high-amplitude (any of the 18 channels' peak |filtered sample| in the window over
    its OWN committed 5xSD threshold -- data/processed/{subj}_stats.json for test patients,
    5.0 * results/v9_anatomy/xcache/chb24.npz's own label-free sd for chb24) non-seizure,
    non-buffer 4 s windows
  - ordinary background (non-ictal, non-buffer, not high-amplitude) 4 s windows
Reported per patient and pooled; by annotated channel count (TEST seizures only, matched on
subject+file+onset_s against results/attribution_v7/labels/ictal_channels_FINAL.csv; chb24 has no
such label and is reported separately, not given a channel count); by duration bin (same 4 bins
as V9-E1: <=20s, 21-40s, 41-80s, >80s).

MEASURE 3 -- EEG panels: the 3 seizures and 3 high-amplitude non-seizure windows with the largest
power removed AT CUTOFF 20 (pooled over test+chb24; cutoff=5 may not finish inside the time
budget, so selection never depends on it), before vs after ASR, one shared uV scale across the
whole figure set. Traces are the SAME whole-file band-pass+notch signal measured above (no new
filtering code); only ASR is new here.

OUTPUT: results/v9_x6/ (CSVs + SUMMARY.md); figures F:/Study/Thesis/Defense/slides/figs/
eeg_evidence/x6/. Return format: F:/Study/Thesis/Agent/inbox/V9_X6_REPORT.md.
Rules: read-only on frozen scripts and committed results; the only new code is this file.

Run:  python src/v9_x6_asr.py --smoke                  (1 file, both cutoffs, in-process; timing
                                                           + sanity only -- --run never does this)
      python src/v9_x6_asr.py --run                    (the 70-file batch; cutoff20 pass over all
                                                           70 files, then cutoff5 over the same 70;
                                                           one subprocess per (file, cutoff);
                                                           4.5h wall-clock stop; resumable)
      python src/v9_x6_asr.py --process-one SUBJ FNAME CUTOFF   (one file, one cutoff, one
                                                           process -- what --run shells out to)
      python src/v9_x6_asr.py --aggregate               (part files -> results/v9_x6/*.csv)
      python src/v9_x6_asr.py --panels                  (EEG before/after figures; shells out to
                                                           --extract-trace per distinct file+cutoff)
      python src/v9_x6_asr.py --report                  (SUMMARY.md + inbox report)
"""
import argparse
import importlib.metadata as ilm
import inspect
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import sosfiltfilt, filtfilt

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src", ROOT / "src" / "dataprep"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import preprocessing as P              # noqa: E402

DATASET_DIR = Path("F:/Study/Thesis/Dataset/CHB-MIT")
SUMMARY_DIR = ROOT / "data" / "summaries"
PROCESSED_DIR = ROOT / "data" / "processed"
XCACHE_CHB24 = ROOT / "results" / "v9_anatomy" / "xcache" / "chb24.npz"
ICTAL_CH_CSV = ROOT / "results" / "attribution_v7" / "labels" / "ictal_channels_FINAL.csv"

OUT = ROOT / "results" / "v9_x6"
PARTS = OUT / "_parts"
FIGOUT = Path("F:/Study/Thesis/Defense/slides/figs/eeg_evidence/x6")

FS = P.FS                               # 256
WIN_S = P.WIN_S                         # 4
WIN_SAMPLES = P.WIN_SAMPLES             # 1024
CH = list(P.COMMON_CHANNELS)

TEST = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
CUTOFFS = [20, 5]                       # cutoff20 pass over every file BEFORE any cutoff5 work
DUR_BINS = [(0, 20), (20, 40), (40, 80), (80, float("inf"))]   # same bins as V9-E1
PREICTAL_S = 60.0
BUDGET_S = 4.5 * 3600


# ============================================================================ asrpy numpy>=2 patch
_ASR_PATCHED = False


def patch_asrpy():
    global _ASR_PATCHED
    if _ASR_PATCHED:
        return
    import asrpy.asr as AM
    import asrpy.asr_utils as AU
    src = inspect.getsource(AU.fit_eeg_distribution)
    fixes = [("max_width = np.diff(quants)", "max_width = np.diff(quants)[0]"),
             ("alpha = (opt_lu[1] - opt_lu[0]) / np.diff(opt_bounds)",
              "alpha = (opt_lu[1] - opt_lu[0]) / np.diff(opt_bounds)[0]")]
    for old, new in fixes:
        if src.count(old) != 1:
            raise SystemExit(f"asrpy numpy2 patch: expected exactly one occurrence of {old!r} in "
                              f"asrpy.asr_utils.fit_eeg_distribution (asrpy version changed?) -- "
                              f"found {src.count(old)}; STOPPING rather than silently diverging")
        src = src.replace(old, new)
    ns = dict(AU.__dict__)
    exec(compile(src, "<asrpy_numpy2_patch>", "exec"), ns)
    AU.fit_eeg_distribution = ns["fit_eeg_distribution"]
    AM.fit_eeg_distribution = ns["fit_eeg_distribution"]
    _ASR_PATCHED = True
    print(f"asrpy {ilm.version('asrpy')}: numpy>=2.0 compatibility patch applied (runtime "
          "monkeypatch of asr_utils.fit_eeg_distribution, not a library file edit)", flush=True)


# ============================================================================ file listing
def _files_with_seizures(subj, summary_path, data_dir):
    szm = P.parse_summary(summary_path)
    present = {p.name for p in data_dir.glob("*.edf")}
    return [(fname, szm[fname]) for fname in sorted(szm) if szm[fname] and fname in present]


def build_file_list():
    """[(subject, fname, [(onset,offset),...]), ...], 58 test + 12 chb24 = 70 files."""
    out = []
    for subj in TEST:
        for fname, sz in _files_with_seizures(subj, SUMMARY_DIR / f"{subj}-summary.txt",
                                              DATASET_DIR / subj):
            out.append((subj, fname, sz))
    for fname, sz in _files_with_seizures("chb24", DATASET_DIR / "chb24" / "chb24-summary.txt",
                                          DATASET_DIR / "chb24"):
        out.append(("chb24", fname, sz))
    return out


def subject_threshold(subj):
    """[18] Volts, the committed 5xSD artifact threshold (label-free for chb24)."""
    if subj == "chb24":
        z = np.load(XCACHE_CHB24, allow_pickle=True)
        return 5.0 * np.asarray(z["sd"], dtype=np.float64)
    st = json.loads((PROCESSED_DIR / f"{subj}_stats.json").read_text())
    return np.asarray(st["artifact_thresh_uV"], dtype=np.float64) * 1e-6


# ============================================================================ signal path
def whole_file_filtered(path):
    """preprocessing.open_edf + the pipeline's own band-pass+notch, applied whole-file in one
    pass (continuous_eval.filter_file's convention). Returns (X [18, n_total] float64 Volts,
    n_total). Raises if the file is missing one of the 18 common channels (shouldn't happen --
    every file here is already known to carry seizures in the committed summaries)."""
    raw = P.open_edf(path)
    if raw is None:
        raise RuntimeError(f"{path}: missing one of the 18 common channels")
    n_total = int(raw.n_times)
    data = raw.get_data()
    del raw
    bp = sosfiltfilt(P._BP_SOS, data, axis=1)
    del data
    notched = filtfilt(P._NOTCH_B, P._NOTCH_A, bp, axis=1)
    del bp
    return notched, n_total


_MNE_INFO = None


MEM_SPLIT_CHUNK_S = 60.0                # target ~1 min of data per asr.transform() internal chunk
                                         # (300s still let a subprocess reach ~1.8-1.9GB RSS on a
                                         # 4h file; with only ~7.4 GB "available" on this machine
                                         # at baseline -- psutil.virtual_memory(), 9.6 GB already
                                         # used by other processes -- that was tight enough that
                                         # the OS killed the whole --run as a low-memory measure
                                         # mid-file. 60s trades more asr_process loop iterations
                                         # for a ~5x smaller peak chunk array.)
MIN_AVAILABLE_GB = 4.5                  # V9-FINAL Part A: raised from 3.0 after a live low-memory
                                         # kill at ~7 GB available (the pre-flight check only bounds
                                         # memory AT SPAWN TIME, not growth during a subprocess's own
                                         # run -- more headroom at spawn gives more room for that
                                         # growth before the OS's own threshold is reached)
                                         # --run pauses before spawning a subprocess if the system
                                         # has less than this much available RAM (psutil), instead
                                         # of launching into a likely OOM/low-memory kill


def run_asr(X, cutoff):
    """X: [18, n_total] float64 Volts, already pipeline-filtered. Returns the ASR-cleaned array
    of the same shape. asrpy's own built-in clean-window calibration (asrpy.ASR.fit), no labels.

    mem_splits: asrpy.ASR.transform's own knob for exactly this problem -- its asr_process ->
    ma_filter builds an (n_samples_in_chunk, n_channels**2) intermediate array, and asrpy's
    default mem_splits=3 OOM'd (ArrayMemoryError, 5.94 GiB) on chb06_01.edf, a 4h recording
    (CHB-MIT files are not all ~1h; some run several hours). Scaled here by the file's own
    duration so every chunk stays near MEM_SPLIT_CHUNK_S regardless of file length."""
    global _MNE_INFO
    patch_asrpy()
    import asrpy
    import mne
    mne.set_log_level("ERROR")
    if _MNE_INFO is None:
        _MNE_INFO = mne.create_info(CH, FS, ch_types="eeg")
    mem_splits = max(3, int(np.ceil(X.shape[1] / (MEM_SPLIT_CHUNK_S * FS))))
    asr = asrpy.ASR(sfreq=FS, cutoff=cutoff)
    asr.fit(mne.io.RawArray(X.copy(), _MNE_INFO, verbose=False))
    cleaned = asr.transform(mne.io.RawArray(X.copy(), _MNE_INFO, verbose=False), mem_splits=mem_splits)
    return cleaned.get_data().astype(np.float64)


# ============================================================================ measures
def span_power_ratio(X_raw, X_clean, a, b, n_total):
    a, b = max(0, int(round(a))), min(n_total, int(round(b)))
    if b <= a:
        return float("nan")
    pb = float(np.mean(X_raw[:, a:b] ** 2))
    if pb <= 0:
        return float("nan")
    pa = float(np.mean(X_clean[:, a:b] ** 2))
    return 1.0 - pa / pb


def window_shares(X_raw, X_clean, n_windows):
    usable = n_windows * WIN_SAMPLES
    Wr = X_raw[:, :usable].reshape(18, n_windows, WIN_SAMPLES)
    Wc = X_clean[:, :usable].reshape(18, n_windows, WIN_SAMPLES)
    pb = (Wr ** 2).mean(axis=(0, 2))
    pa = (Wc ** 2).mean(axis=(0, 2))
    with np.errstate(invalid="ignore", divide="ignore"):
        share = 1.0 - pa / pb
    share[pb <= 0] = np.nan
    return share, Wr


def window_flags(Wr, thr, n_windows, seizures, n_total):
    secs = min(n_windows * WIN_S, n_total // FS)
    ict = P.build_labels(secs, seizures).reshape(-1, WIN_S).max(axis=1) == 1 if secs else np.zeros(0, bool)
    buf = P.build_buffer_mask(secs, seizures).reshape(-1, WIN_S).any(axis=1) if secs else np.zeros(0, bool)
    if len(ict) < n_windows:                              # last partial second-group, pad False
        pad = n_windows - len(ict)
        ict = np.concatenate([ict, np.zeros(pad, bool)])
        buf = np.concatenate([buf, np.zeros(pad, bool)])
    peak = np.abs(Wr).max(axis=2).T                        # [n_windows, 18]
    highamp = (peak > thr[None, :]).any(axis=1) & ~ict & ~buf
    background = ~ict & ~buf & ~highamp
    return highamp, background


def median_channel_rms(X, a, b):
    """[V9-FINAL Part A item 2] median across the 18 channels of each channel's own RMS over
    sample span [a, b)."""
    a, b = max(0, int(round(a))), min(X.shape[1], int(round(b)))
    if b <= a:
        return float("nan")
    return float(np.median(np.sqrt(np.mean(X[:, a:b].astype(np.float64) ** 2, axis=1))))


def window_median_rms(X, n_windows):
    """median-channel RMS of EACH 4 s window -- [n_windows]."""
    usable = n_windows * WIN_SAMPLES
    W = X[:, :usable].reshape(18, n_windows, WIN_SAMPLES).astype(np.float64)
    rms = np.sqrt(np.mean(W ** 2, axis=2))          # [18, n_windows]
    return np.median(rms, axis=0)                    # [n_windows]


def preceding_median_rms(X, n_windows, precede_win):
    """median-channel RMS of the `precede_win` windows immediately BEFORE each window (NaN where
    fewer than `precede_win` windows precede it) -- vectorised prefix-sum, same technique as
    src/v9_v1_fix.py's whole-file background scan."""
    sq = X.astype(np.float64) ** 2
    cum = np.concatenate([np.zeros((sq.shape[0], 1)), np.cumsum(sq, axis=1)], axis=1)
    bounds = np.arange(0, n_windows + 1) * WIN_SAMPLES
    out = np.full(n_windows, np.nan)
    if n_windows <= precede_win:
        return out
    ws = np.arange(precede_win, n_windows)
    s = cum[:, bounds[ws]] - cum[:, bounds[ws - precede_win]]     # [18, len(ws)]
    rms = np.sqrt(s / (precede_win * WIN_SAMPLES))
    out[ws] = np.median(rms, axis=0)
    return out


def process_one(subj, fname, seizures, cutoff, thr):
    t0 = time.time()
    path = DATASET_DIR / subj / fname
    X_raw, n_total = whole_file_filtered(path)
    n_windows = n_total // WIN_SAMPLES
    X_clean = run_asr(X_raw, cutoff)

    share_w, Wr = window_shares(X_raw, X_clean, n_windows)
    highamp, background = window_flags(Wr, thr, n_windows, seizures, n_total)

    sz_rows = []
    for i, (onset, offset) in enumerate(seizures):
        share_sz = span_power_ratio(X_raw, X_clean, onset * FS, offset * FS, n_total)
        share_pre = span_power_ratio(X_raw, X_clean, (onset - PREICTAL_S) * FS, onset * FS, n_total)
        c_sz_raw = median_channel_rms(X_raw, onset * FS, offset * FS)
        c_pre_raw = median_channel_rms(X_raw, (onset - PREICTAL_S) * FS, onset * FS)
        c_sz_clean = median_channel_rms(X_clean, onset * FS, offset * FS)
        c_pre_clean = median_channel_rms(X_clean, (onset - PREICTAL_S) * FS, onset * FS)
        sz_rows.append(dict(seizure_idx=i, onset_s=onset, offset_s=offset,
                            duration_s=offset - onset, share_seizure=share_sz,
                            share_preictal60=share_pre,
                            contrast_before=(c_sz_raw / c_pre_raw) if c_pre_raw else float("nan"),
                            contrast_after=(c_sz_clean / c_pre_clean) if c_pre_clean else float("nan")))

    # highamp windows: contrast = that window's own median-channel RMS / the preceding 60 s
    # (PREICTAL_S / WIN_S windows), raw and clean, same PREICTAL_S rule as the seizure spans above
    precede_win = int(PREICTAL_S // WIN_S)
    wrms_raw = window_median_rms(X_raw, n_windows)
    wrms_clean = window_median_rms(X_clean, n_windows)
    prms_raw = preceding_median_rms(X_raw, n_windows, precede_win)
    prms_clean = preceding_median_rms(X_clean, n_windows, precede_win)
    with np.errstate(invalid="ignore", divide="ignore"):
        contrast_before_w = wrms_raw / prms_raw
        contrast_after_w = wrms_clean / prms_clean

    hi_idx = np.flatnonzero(highamp)
    payload = dict(subject=subj, file=fname, cutoff=cutoff, n_windows=int(n_windows),
                  seizures=sz_rows,
                  highamp=dict(win_idx=hi_idx.tolist(), share=share_w[hi_idx].tolist(),
                               contrast_before=contrast_before_w[hi_idx].tolist(),
                               contrast_after=contrast_after_w[hi_idx].tolist()),
                  background=dict(share=share_w[background].tolist()),
                  elapsed_s=time.time() - t0)
    PARTS.mkdir(parents=True, exist_ok=True)
    part_path(subj, fname, cutoff).write_text(json.dumps(payload), encoding="utf-8")
    print(f"{subj}/{fname} cutoff={cutoff}: {n_windows} windows, {len(seizures)} seizure(s), "
          f"{len(hi_idx)} high-amp windows, {time.time()-t0:.0f}s", flush=True)


def part_path(subj, fname, cutoff):
    return PARTS / f"{subj}__{fname.replace('.edf', '')}__c{cutoff}.json"


def _subprocess_one(subj, fname, cutoff):
    """One (file, cutoff) unit of work in its OWN python process -- see the module docstring's
    ONE (file, cutoff) PER OS PROCESS note for why (measured ~5 GB RSS growth per 4 in-process
    ASR calls)."""
    cmd = [sys.executable, str(Path(__file__).resolve()), "--process-one", subj, fname, str(cutoff)]
    r = subprocess.run(cmd, cwd=str(ROOT))
    return r.returncode == 0


def process_one_cli(subj, fname, cutoff):
    """What --process-one runs: looks up this file's own seizure list from the fixed file
    universe (never re-derives it ad hoc) and does the single-file measurement."""
    files = build_file_list()
    match = [(s, f, sz) for s, f, sz in files if s == subj and f == fname]
    if not match:
        raise SystemExit(f"{subj}/{fname} is not in the V9-X6 file universe (build_file_list())")
    _, _, seizures = match[0]
    thr = subject_threshold(subj)
    process_one(subj, fname, seizures, cutoff, thr)


# ============================================================================ run (resumable, time-budgeted)
def _wait_for_memory(t_start, budget_s, max_wait_s=600.0):
    """Pre-flight check before spawning the next subprocess: this run's own subprocess
    isolation only bounds ONE subprocess's own RSS -- it does nothing about memory already
    used by OTHER processes on this machine, and a previous --run was killed outright by the
    OS's low-memory protection mid-file (psutil showed only ~7.4 GB "available" of 17 GB total
    at the time, 9.6 GB already used by other processes). Polls psutil; waits up to
    max_wait_s before giving up and proceeding anyway (logged either way)."""
    import psutil
    t0 = time.time()
    waited = False
    while True:
        avail_gb = psutil.virtual_memory().available / 1e9
        if avail_gb >= MIN_AVAILABLE_GB:
            if waited:
                print(f"  memory recovered: {avail_gb:.1f} GB available, proceeding "
                      f"(waited {time.time()-t0:.0f}s)", flush=True)
            return
        if time.time() - t0 > max_wait_s:
            print(f"  WARNING: still only {avail_gb:.1f} GB available after waiting "
                  f"{max_wait_s:.0f}s (< {MIN_AVAILABLE_GB:.1f} GB target) -- proceeding anyway, "
                  f"risk of another low-memory kill", flush=True)
            return
        if time.time() - t_start > budget_s:
            return                                   # let the caller's own budget check STOP
        if not waited:
            print(f"  only {avail_gb:.1f} GB available (< {MIN_AVAILABLE_GB:.1f} GB target) -- "
                  f"pausing before the next subprocess", flush=True)
            waited = True
        time.sleep(15)


def _part_has_contrast(fp):
    """V9-FINAL Part A item 2: a part file written before the contrast measure existed lacks
    'contrast_before' in its highamp block -- treated as NOT done so it gets recomputed (the
    prompt's own instruction: 'recompute the 47 done if the cleaned signal was not kept')."""
    if not fp.exists():
        return False
    try:
        d = json.loads(fp.read_text())
    except (json.JSONDecodeError, OSError):
        return False
    return "contrast_before" in d.get("highamp", {})


def run_all(budget_s=BUDGET_S, cutoffs=None, require_contrast=False):
    """V9-FINAL Part A (docs/prompts/V9_FINAL_VERIFY.md): cutoffs=[20] finishes the cutoff=20 pass
    only and never touches cutoff=5 (dropped per that prompt -- reported as not done, not silently
    skipped); the module's own CUTOFFS default is unchanged for any earlier caller.
    require_contrast=True additionally reprocesses any already-done file whose cached part JSON
    predates the contrast measure (item 2 of Part A) -- one combined ASR pass per file does both
    measures at once instead of two separate 70-file passes."""
    cutoffs = CUTOFFS if cutoffs is None else cutoffs
    t_start = time.time()
    files = build_file_list()
    print(f"V9-X6: {len(files)} files (every seizure file of the 8 test patients + chb24), "
          f"cutoffs {cutoffs} -- one subprocess per (file, cutoff); {budget_s/3600:.2f}h wall-clock "
          f"stop; require_contrast={require_contrast}", flush=True)
    for cutoff in cutoffs:
        done = skipped = failed = 0
        for subj, fname, _seizures in files:
            if time.time() - t_start > budget_s:
                print(f"STOP: {budget_s/3600:.2f}h wall-clock budget reached before "
                      f"{subj}/{fname} cutoff={cutoff} ({done} done this cutoff, "
                      f"{skipped} already cached, {failed} failed)", flush=True)
                return
            fp = part_path(subj, fname, cutoff)
            if fp.exists() and (not require_contrast or _part_has_contrast(fp)):
                skipped += 1
                continue
            _wait_for_memory(t_start, budget_s)
            ok = _subprocess_one(subj, fname, cutoff)
            if ok:
                done += 1
            else:
                failed += 1
                print(f"FAILED: {subj}/{fname} cutoff={cutoff} (subprocess exit != 0, "
                      f"no part file written -- will retry on the next --run)", flush=True)
        print(f"cutoff={cutoff}: {done} file(s) processed this run, {skipped} already cached, "
              f"{failed} failed ({time.time()-t_start:.0f}s elapsed total)", flush=True)
    print(f"V9-X6 --run done, {time.time()-t_start:.0f}s total", flush=True)


# ============================================================================ aggregate
def aggregate():
    files = build_file_list()
    ictal_ch = pd.read_csv(ICTAL_CH_CSV) if ICTAL_CH_CSV.exists() else pd.DataFrame()
    sz_rows, hi_rows, bg_rows = [], [], []
    coverage = []
    for cutoff in CUTOFFS:
        n_done = 0
        for subj, fname, _ in files:
            fp = part_path(subj, fname, cutoff)
            if not fp.exists():
                continue
            n_done += 1
            d = json.loads(fp.read_text())
            for r in d["seizures"]:
                sz_rows.append(dict(subject=subj, file=fname, cutoff=cutoff, **r))
            cb_list = d["highamp"].get("contrast_before", [None] * len(d["highamp"]["win_idx"]))
            ca_list = d["highamp"].get("contrast_after", [None] * len(d["highamp"]["win_idx"]))
            for wi, sh, cb, ca in zip(d["highamp"]["win_idx"], d["highamp"]["share"], cb_list, ca_list):
                hi_rows.append(dict(subject=subj, file=fname, cutoff=cutoff, win_idx=wi, share=sh,
                                    contrast_before=cb, contrast_after=ca))
            for sh in d["background"]["share"]:
                bg_rows.append(dict(subject=subj, file=fname, cutoff=cutoff, share=sh))
        coverage.append(dict(cutoff=cutoff, files_done=n_done, files_total=len(files)))

    SZ = pd.DataFrame(sz_rows)
    if len(SZ) and len(ictal_ch):
        ic = ictal_ch.rename(columns={"edf_file": "file", "onset_s": "onset_s"})
        SZ = SZ.merge(ic[["subject", "file", "onset_s", "n_ictal", "ictal_channels", "focal_generalized"]],
                      on=["subject", "file", "onset_s"], how="left")
    HI = pd.DataFrame(hi_rows)
    BG = pd.DataFrame(bg_rows)
    OUT.mkdir(parents=True, exist_ok=True)
    SZ.to_csv(OUT / "seizures.csv", index=False)
    HI.to_csv(OUT / "highamp_windows.csv", index=False)
    BG.to_csv(OUT / "background_windows.csv", index=False)
    pd.DataFrame(coverage).to_csv(OUT / "coverage.csv", index=False)
    print(f"aggregate: {len(SZ)} seizure rows, {len(HI)} high-amp window rows, {len(BG)} "
          f"background window rows -> {OUT}", flush=True)
    for c in coverage:
        print(f"  cutoff={c['cutoff']}: {c['files_done']}/{c['files_total']} files done", flush=True)
    return SZ, HI, BG, coverage


# ============================================================================ report
def _stats_line(label, v):
    v = pd.Series(v).dropna()
    if not len(v):
        return f"{label:28s} n=0"
    return f"{label:28s} n={len(v):4d}  mean {v.mean():+.3f}  median {v.median():+.3f}  " \
           f"p10 {v.quantile(.1):+.3f}  p90 {v.quantile(.9):+.3f}"


def _patient_boot_contrast(df, subs, col_before, col_after, B=2000, seed=42):
    """V9-FINAL Part A item 2: patient-cluster bootstrap (resample patients with replacement,
    percentile 95% CI) of the pooled mean contrast before/after ASR and their difference
    (after - before; negative = ASR LOWERS the seizure/window contrast)."""
    d = df[df.subject.isin(subs)].dropna(subset=[col_before, col_after])
    if not len(d):
        return None
    rng = np.random.RandomState(seed)
    diffs, befs, afts = [], [], []
    for _ in range(B):
        pick = rng.choice(subs, size=len(subs), replace=True)
        bd = pd.concat([d[d.subject == p] for p in pick], ignore_index=True)
        if not len(bd):
            continue
        befs.append(bd[col_before].mean())
        afts.append(bd[col_after].mean())
        diffs.append(bd[col_after].mean() - bd[col_before].mean())
    return dict(n=len(d), mean_before=float(d[col_before].mean()), mean_after=float(d[col_after].mean()),
               mean_diff=float(np.mean(diffs)), ci_diff=(float(np.percentile(diffs, 2.5)),
               float(np.percentile(diffs, 97.5))), ci_before=(float(np.percentile(befs, 2.5)),
               float(np.percentile(befs, 97.5))), ci_after=(float(np.percentile(afts, 2.5)),
               float(np.percentile(afts, 97.5))))


def contrast_section(SZ, HI, cutoff):
    s = SZ[SZ.cutoff == cutoff]
    hi = HI[HI.cutoff == cutoff]
    subs = TEST + ["chb24"]
    L = [f"\n### Contrast (median-channel RMS of the span / RMS of the preceding 60 s), before vs "
         f"after ASR, cutoff={cutoff} (patient bootstrap, B=2000)\n"]
    if "contrast_before" not in s.columns or not s.contrast_before.notna().any():
        L.append("(contrast measure not available for this cutoff -- see coverage above)")
        return L
    sz_r = _patient_boot_contrast(s, subs, "contrast_before", "contrast_after")
    hi_r = _patient_boot_contrast(hi, subs, "contrast_before", "contrast_after")
    L.append("```")
    if sz_r:
        L.append(f"seizure span       n={sz_r['n']:4d}  before {sz_r['mean_before']:.3f}  "
                 f"after {sz_r['mean_after']:.3f}  diff {sz_r['mean_diff']:+.3f} "
                 f"[{sz_r['ci_diff'][0]:+.3f}, {sz_r['ci_diff'][1]:+.3f}]")
    if hi_r:
        L.append(f"high-amp windows   n={hi_r['n']:4d}  before {hi_r['mean_before']:.3f}  "
                 f"after {hi_r['mean_after']:.3f}  diff {hi_r['mean_diff']:+.3f} "
                 f"[{hi_r['ci_diff'][0]:+.3f}, {hi_r['ci_diff'][1]:+.3f}]")
    L.append("```")
    L.append("\nPer patient:\n```")
    for subj in subs:
        ss = s[(s.subject == subj)].dropna(subset=["contrast_before", "contrast_after"])
        hh = hi[(hi.subject == subj)].dropna(subset=["contrast_before", "contrast_after"])
        if len(ss) or len(hh):
            sb = f"{ss.contrast_before.mean():.3f}->{ss.contrast_after.mean():.3f}" if len(ss) else "n/a"
            hb = f"{hh.contrast_before.mean():.3f}->{hh.contrast_after.mean():.3f}" if len(hh) else "n/a"
            L.append(f"{subj:7s} seizure n={len(ss):3d} {sb:18s} | high-amp n={len(hh):4d} {hb}")
    L.append("```")
    L.append("\nNegative diff = ASR LOWERS the seizure/window contrast (removes what a detector "
             "needs); CI excluding 0 is the evidence that matters here, not the point estimate alone.")
    return L


def build_report(SZ, HI, BG, coverage):
    L = ["# V9-X6 -- does ASR delete seizure activity?\n",
         "**Reduced scope (fixed by the author 2026-10-30, before this ran):** Measure 1 (what "
         "ASR removes) + the EEG panels only; Measure 2 (effect on B4 detection) was skipped. "
         "Files: every seizure-containing file of the 8 CHB-MIT test patients + chb24 (58 + 12 = "
         "70 files), no development patients, no seizure-free matched files. cutoff=20 run over "
         "every file first, cutoff=5 afterward as time allowed; 4.5h wall-clock stop.\n",
         "Full tables: `results/v9_x6/*.csv`. Code: `src/v9_x6_asr.py` (new).\n",
         "## Coverage\n```"]
    for c in coverage:
        L.append(f"cutoff={c['cutoff']:3d}  {c['files_done']:3d}/{c['files_total']} files")
    L.append("```")

    for cutoff in CUTOFFS:
        L.append(f"\n## cutoff = {cutoff}\n")
        s = SZ[SZ.cutoff == cutoff]
        hi = HI[HI.cutoff == cutoff]
        bg = BG[BG.cutoff == cutoff]
        if not len(s) and not len(hi):
            L.append("(no files completed at this cutoff)")
            continue
        L += ["### Pooled share of power removed (1 - after/before)\n```",
             _stats_line("seizure span", s.share_seizure),
             _stats_line("60s pre-seizure", s.share_preictal60),
             _stats_line("high-amplitude (label-free) windows", hi.share),
             _stats_line("ordinary background windows", bg.share), "```"]

        L.append("\n### Per patient (seizure-span share removed; test patients + chb24)\n```")
        for subj in TEST + ["chb24"]:
            ss = s[s.subject == subj].share_seizure
            hh = hi[hi.subject == subj].share
            bb = bg[bg.subject == subj].share
            L.append(f"{subj:7s} seizure n={len(ss):3d} mean {ss.mean():+.3f}  |  "
                     f"high-amp n={len(hh):4d} mean {hh.mean():+.3f}  |  "
                     f"background n={len(bb):5d} mean {bb.mean():+.3f}")
        L.append("```")

        L.append("\n### Seizure-span share removed, by duration bin\n```")
        for lo, hi_ in DUR_BINS:
            d = s[(s.duration_s > lo) & (s.duration_s <= hi_)] if hi_ < float("inf") else s[s.duration_s > lo]
            lbl = f"{lo:.0f}-{hi_:.0f}s" if hi_ < float("inf") else f">{lo:.0f}s"
            L.append(f"{lbl:10s} n={len(d):3d}  mean {d.share_seizure.mean():+.3f}" if len(d)
                     else f"{lbl:10s} n=0")
        L.append("```")

        if "n_ictal" in s.columns and s.n_ictal.notna().any():
            st = s[s.n_ictal.notna()].copy()
            rho = st[["n_ictal", "share_seizure"]].corr(method="spearman").iloc[0, 1]
            L.append(f"\n### Seizure-span share removed vs annotated channel count (TEST seizures "
                     f"only, `results/attribution_v7/labels/ictal_channels_FINAL.csv`; "
                     f"n={len(st)}, Spearman rho = {rho:.3f})\n```")
            for lo, hi_ in [(0, 3), (3, 6), (6, 10), (10, 100)]:
                d = st[(st.n_ictal > lo) & (st.n_ictal <= hi_)]
                L.append(f"n_ictal {lo+1}-{hi_ if hi_<100 else 'max'}: n={len(d):3d}  "
                         f"mean share {d.share_seizure.mean():+.3f}" if len(d) else
                         f"n_ictal {lo+1}-{hi_ if hi_<100 else 'max'}: n=0")
            L.append("```")

        L += contrast_section(SZ, HI, cutoff)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "SUMMARY.md").write_text("\n".join(L), encoding="utf-8")
    inbox = ROOT.parent / "Agent" / "inbox" / "V9_X6_REPORT.md"
    inbox.parent.mkdir(parents=True, exist_ok=True)
    inbox.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))
    print(f"\nWrote results/v9_x6/SUMMARY.md and {inbox}")


# ============================================================================ panels (Measure 3)
def pick_panel_events(SZ, HI, k=3):
    s20 = SZ[SZ.cutoff == 20].dropna(subset=["share_seizure"]).sort_values("share_seizure", ascending=False)
    h20 = HI[HI.cutoff == 20].dropna(subset=["share"]).sort_values("share", ascending=False)
    sz_picks = s20.head(k).to_dict("records")
    hi_picks = h20.head(k).to_dict("records")
    return sz_picks, hi_picks


def spacing_for(segments):
    q = float(np.median([np.percentile(np.abs(s), 99.0) for s in segments]))
    target = 2.0 * q * 1e6                                 # V -> uV
    for v in (25, 50, 75, 100, 150, 200, 250, 300, 400, 500, 600, 800, 1000, 1500, 2000, 3000, 4000, 5000):
        if v >= target:
            return float(v)
    return float(np.ceil(target / 1000.0) * 1000)


def draw_before_after(ax_b, ax_a, X_raw, X_clean, t0, t1, span, spacing_uV, title):
    n = X_raw.shape[1]
    t = t0 + np.arange(n) / FS
    offs = np.arange(len(CH))[::-1] * spacing_uV
    lim = 1.2 * spacing_uV
    for ax, X, lbl in ((ax_b, X_raw, "before ASR"), (ax_a, X_clean, "after ASR")):
        for ci in range(len(CH)):
            y = np.clip(X[ci] * 1e6, -lim, lim)
            ax.plot(t, y + offs[ci], lw=0.35, color="#111111")
        ax.set_yticks(offs); ax.set_yticklabels(CH, fontsize=6)
        ax.set_xlim(t0, t1)
        ax.set_ylim(-1.4 * spacing_uV, offs[0] + 1.4 * spacing_uV)
        a, b = span
        ax.axvspan(a, b, color="#808080", alpha=0.18, lw=0)
        ax.set_title(f"{title}  [{lbl}]", fontsize=7.5, loc="left")
        ax.tick_params(axis="x", labelsize=6)
        ax.set_xlabel("time (s)", fontsize=6)
        for s_ in ("top", "right"):
            ax.spines[s_].set_visible(False)


def extract_trace_cli(subj, fname, cutoff, out_path):
    """What --extract-trace runs: one (file, cutoff) unit of work, one process (see the module
    docstring's ONE PER OS PROCESS note). Writes the whole-file raw+ASR-cleaned traces (float32)
    to out_path for the (lightweight, drawing-only) parent process to slice and plot."""
    path = DATASET_DIR / subj / fname
    X_raw, n_total = whole_file_filtered(path)
    X_clean = run_asr(X_raw, int(cutoff))
    np.savez_compressed(out_path, X_raw=X_raw.astype(np.float32), X_clean=X_clean.astype(np.float32),
                        n_total=n_total)


def _get_trace(subj, fname, cutoff, cache, tmp_dir):
    """Dedup across panel picks from the same file: shells out to --extract-trace once per
    distinct (subject, file, cutoff), in its OWN process, and caches the small result in RAM for
    the rest of this (lightweight) process."""
    key = (subj, fname, cutoff)
    if key in cache:
        return cache[key]
    out_path = tmp_dir / f"{subj}__{fname.replace('.edf', '')}__c{cutoff}_trace.npz"
    if not out_path.exists():
        cmd = [sys.executable, str(Path(__file__).resolve()), "--extract-trace", subj, fname,
              str(cutoff), str(out_path)]
        r = subprocess.run(cmd, cwd=str(ROOT))
        if r.returncode != 0:
            raise SystemExit(f"--extract-trace failed for {subj}/{fname} cutoff={cutoff}")
    z = np.load(out_path)
    cache[key] = (z["X_raw"].astype(np.float64), z["X_clean"].astype(np.float64), int(z["n_total"]))
    return cache[key]


def render_panels(sz_picks, hi_picks, cutoff=20):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    events = []
    for r in sz_picks:
        events.append(dict(kind="seizure", **r))
    for r in hi_picks:
        onset_s = r["win_idx"] * WIN_S
        events.append(dict(kind="highamp", subject=r["subject"], file=r["file"], onset_s=onset_s,
                           duration_s=float(WIN_S), share_seizure=r["share"]))

    trace_cache, segs, loaded = {}, [], []
    tmp_dir = PARTS / "_trace_cache"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for ev in events:
        subj, fname = ev["subject"], ev["file"]
        X_raw, X_clean, n_total = _get_trace(subj, fname, cutoff, trace_cache, tmp_dir)
        onset, dur = float(ev["onset_s"]), float(ev["duration_s"])
        margin = 15.0 if dur >= 60.0 else max(15.0, (60.0 - dur) / 2.0)
        t0, t1 = max(0.0, onset - margin), min(n_total / FS, onset + dur + margin)
        a, b = int(round(t0 * FS)), int(round(t1 * FS))
        title = f"{subj}  {fname}  {ev['kind']}  dur {dur:.0f}s  share removed {ev['share_seizure']:+.3f}"
        loaded.append(dict(ev=ev, Xr=X_raw[:, a:b], Xc=X_clean[:, a:b], t0=t0, t1=t1,
                           span=(onset, onset + dur), title=title))
        segs.append(loaded[-1]["Xr"]); segs.append(loaded[-1]["Xc"])
        print(f"  panel ready: {title}", flush=True)

    if not loaded:
        print("render_panels: nothing to draw (no completed cutoff=20 rows yet)", flush=True)
        return
    spacing = spacing_for(segs)
    FIGOUT.mkdir(parents=True, exist_ok=True)
    sel_rows = []
    for i, d in enumerate(loaded):
        ev = d["ev"]
        fig = plt.figure(figsize=(14.0, 6.0), dpi=200)
        gs = GridSpec(1, 2, wspace=0.18, left=0.06, right=0.98, top=0.90, bottom=0.10)
        draw_before_after(fig.add_subplot(gs[0]), fig.add_subplot(gs[1]), d["Xr"], d["Xc"],
                          d["t0"], d["t1"], d["span"], spacing, d["title"])
        tag = f"{ev['kind']}_{ev['subject']}_{ev['file'].replace('.edf', '')}_{int(ev['onset_s'])}"
        p = FIGOUT / f"x6_{i:02d}_{tag}.png"
        fig.savefig(p); plt.close(fig)
        sel_rows.append(dict(kind=ev["kind"], subject=ev["subject"], file=ev["file"],
                             onset_s=ev["onset_s"], duration_s=ev["duration_s"],
                             share_removed_cutoff20=ev["share_seizure"], figure=p.name))
        print(f"  wrote {p}", flush=True)

    n = len(loaded)
    fig = plt.figure(figsize=(14.0, 6.0 * n), dpi=100)
    gs = GridSpec(n, 2, wspace=0.18, hspace=0.45, left=0.06, right=0.98, top=0.98, bottom=0.03)
    for i, d in enumerate(loaded):
        draw_before_after(fig.add_subplot(gs[i, 0]), fig.add_subplot(gs[i, 1]), d["Xr"], d["Xc"],
                          d["t0"], d["t1"], d["span"], spacing, d["title"])
    sheet = FIGOUT / "x6_contact_sheet.png"
    fig.savefig(sheet); plt.close(fig)
    pd.DataFrame(sel_rows).to_csv(FIGOUT / "selection.csv", index=False)
    print(f"render_panels: {n} panels + {sheet}", flush=True)


def panels():
    SZ, HI, BG, coverage = aggregate()
    sz_picks, hi_picks = pick_panel_events(SZ, HI)
    print(f"panel selection (cutoff=20, largest share removed): "
         f"{len(sz_picks)} seizures, {len(hi_picks)} high-amp windows", flush=True)
    render_panels(sz_picks, hi_picks)


# ============================================================================ V9-FINAL Part D item 8
FINAL_FIGOUT = Path("F:/Study/Thesis/Defense/slides/figs/final")


def item8_median_max():
    """V9-FINAL Part D item 8: one seizure at the MEDIAN share-removed, one at the MAXIMUM
    (cutoff=20, the only cutoff Part A completed), before/after ASR, same uV scale across both
    panels. Raw/clean traces are not cached (too large for 70 files) -- re-extracted here via
    --extract-trace, one subprocess per distinct file (same machinery as render_panels/panels)."""
    t0 = time.time()
    SZ, HI, _BG, _cov = aggregate()
    s20 = SZ[SZ.cutoff == 20].dropna(subset=["share_seizure"]).sort_values("share_seizure")
    if not len(s20):
        raise SystemExit("STOP: no cutoff=20 seizure rows -- run Part A first")
    med_idx = len(s20) // 2
    median_row = s20.iloc[med_idx].to_dict()
    max_row = s20.iloc[-1].to_dict()
    print(f"median share removed: {median_row['subject']}/{median_row['file']} "
         f"onset={median_row['onset_s']:.0f}s share={median_row['share_seizure']:+.3f} "
         f"(n={len(s20)}, median value {s20.share_seizure.median():+.3f})", flush=True)
    print(f"max share removed: {max_row['subject']}/{max_row['file']} "
         f"onset={max_row['onset_s']:.0f}s share={max_row['share_seizure']:+.3f}", flush=True)

    trace_cache, loaded, segs = {}, [], []
    tmp_dir = PARTS / "_trace_cache"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for kind, r in (("median", median_row), ("max", max_row)):
        subj, fname = r["subject"], r["file"]
        X_raw, X_clean, n_total = _get_trace(subj, fname, 20, trace_cache, tmp_dir)
        onset, dur = float(r["onset_s"]), float(r["duration_s"])
        margin = 15.0 if dur >= 60.0 else max(15.0, (60.0 - dur) / 2.0)
        t0_s, t1_s = max(0.0, onset - margin), min(n_total / FS, onset + dur + margin)
        a, b = int(round(t0_s * FS)), int(round(t1_s * FS))
        title = f"ASR before/after -- {kind} seizure (share removed {r['share_seizure']:+.3f})"
        loaded.append(dict(kind=kind, r=r, Xr=X_raw[:, a:b], Xc=X_clean[:, a:b], t0=t0_s, t1=t1_s,
                           span=(onset, onset + dur), title=title))
        segs += [loaded[-1]["Xr"], loaded[-1]["Xc"]]

    spacing = spacing_for(segs)   # SAME scale across both panels, per the prompt
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec
    for outdir in (FIGOUT, FINAL_FIGOUT):
        outdir.mkdir(parents=True, exist_ok=True)
        for d in loaded:
            fig = plt.figure(figsize=(14.0, 6.0), dpi=200)
            gs = GridSpec(1, 2, wspace=0.18, left=0.06, right=0.98, top=0.90, bottom=0.10)
            draw_before_after(fig.add_subplot(gs[0]), fig.add_subplot(gs[1]), d["Xr"], d["Xc"],
                              d["t0"], d["t1"], d["span"], spacing, d["title"])
            fig.savefig(outdir / f"item8_asr_{d['kind']}.png")
            plt.close(fig)
    sel = pd.DataFrame([dict(kind=d["kind"], subject=d["r"]["subject"], file=d["r"]["file"],
                             onset_s=d["r"]["onset_s"], duration_s=d["r"]["duration_s"],
                             share_removed=d["r"]["share_seizure"]) for d in loaded])
    sel.to_csv(FIGOUT / "item8_selection.csv", index=False)
    print(sel.to_string(index=False), flush=True)
    print(f"item8_median_max done in {time.time()-t0:.0f}s -> {FIGOUT} and {FINAL_FIGOUT}", flush=True)


# ============================================================================ smoke
def smoke():
    t0 = time.time()
    files = build_file_list()
    print(f"smoke: {len(files)} files in the V9-X6 universe (58 test + 12 chb24 expected)", flush=True)
    subj, fname, seizures = files[0]
    thr = subject_threshold(subj)
    print(f"smoke: processing {subj}/{fname} ({len(seizures)} seizure(s)) at both cutoffs "
         f"-- this alone takes ~4 min on a 1h file (measured), not the full run", flush=True)
    for cutoff in CUTOFFS:
        process_one(subj, fname, seizures, cutoff, thr)
    print(f"smoke done in {time.time()-t0:.0f}s", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--cutoff20-only", action="store_true",
                    help="V9-FINAL Part A: finish the cutoff=20 pass only, never start cutoff=5")
    ap.add_argument("--process-one", nargs=3, metavar=("SUBJ", "FNAME", "CUTOFF"))
    ap.add_argument("--extract-trace", nargs=4, metavar=("SUBJ", "FNAME", "CUTOFF", "OUT_NPZ"))
    ap.add_argument("--aggregate", action="store_true")
    ap.add_argument("--panels", action="store_true")
    ap.add_argument("--item8", action="store_true", help="V9-FINAL Part D item 8: median+max ASR before/after")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.smoke:
        smoke()
    elif a.process_one:
        subj, fname, cutoff = a.process_one
        process_one_cli(subj, fname, int(cutoff))
    elif a.extract_trace:
        subj, fname, cutoff, out = a.extract_trace
        extract_trace_cli(subj, fname, cutoff, out)
    elif a.cutoff20_only:
        run_all(cutoffs=[20], require_contrast=True)
    elif a.run:
        run_all()
    elif a.aggregate:
        aggregate()
    elif a.panels:
        panels()
    elif a.item8:
        item8_median_max()
    elif a.report:
        SZ = pd.read_csv(OUT / "seizures.csv") if (OUT / "seizures.csv").exists() else pd.DataFrame()
        HI = pd.read_csv(OUT / "highamp_windows.csv") if (OUT / "highamp_windows.csv").exists() else pd.DataFrame()
        BG = pd.read_csv(OUT / "background_windows.csv") if (OUT / "background_windows.csv").exists() else pd.DataFrame()
        coverage = pd.read_csv(OUT / "coverage.csv").to_dict("records") if (OUT / "coverage.csv").exists() else []
        build_report(SZ, HI, BG, coverage)
    else:
        raise SystemExit("pass --smoke, --run, --process-one SUBJ FNAME CUTOFF, --aggregate, "
                          "--panels or --report")


if __name__ == "__main__":
    main()
