"""
pipeline_demo.py -- SzScan's label-free, continuous re-implementation of the FINAL thesis system
(git tag `p3-frozen`; brief `docs/DEMO_REBUILD_BRIEF.md`). Replaces the earlier V1 path (rlg:
recon + latent + gamma, PELT), which is archived under `web_demo/archive/backend_v1/`.

Every scientific step is IMPORTED from the frozen thesis code (read-only, single source) -- this
file only wires the steps to the upload flow and keeps every fit label-free:

  stage                         thesis code called here
  ----------------------------  ------------------------------------------------------------------
  filtering (whole file)        same ops as x1_external.filter_windows (band-pass + 60 Hz notch)
  z-score statistics            x1_external.window_padded on every 10th window of the WHOLE
                                recording (the x1_external.labelfree_stats rule; no label anywhere)
  graph + node features         c1b_build_trainset.graph_and_bp, c1b_build_trainset.f7
  GAE v2 (seed 42) node latent  p2_dump_seeds23.run_model (checkpoint verified by sha256 first)
  per-channel distance          LedoitWolf Mahalanobis per channel over all non-signal-loss
                                windows of the subject (as x1_external.model_outputs)
  ensemble anomaly score        e22_test_oneshot.final_scalar (members 6/9/12/mean of e17b, each
                                minus its +-15 min running median per file, patient percentile)
  per-patient alarm budget      p3_levers.member_mean_z + q_of, k and clip from freeze.json
  detector                      p2_scalars.d1_events (5-window smoothing, merge <= 90 s)
  onset/offset localizer        p3_levers.localize(mode = freeze.json "localizer" = "cpd")
  channel panel                 |robust-z| of the per-channel distance, p95 over the event
                                (attribution_v8's quantity; computed on read in attribution.py)

The detector/localizer lines in `process_subject_events` are the same six lines as
e23_test_look7.evaluate, minus its scoring (which needs labels); src/t1_demo_gate.py checks the
demo's events against the thesis's own look-#7 counts for chb03 with the thesis statistics.

Approved divergence (project instructions 11.3, DEMO_REBUILD_BRIEF 2): every per-subject quantity
(z-score statistics, the 18 LedoitWolf fits, robust-z, percentiles, the budget q_i) is fitted on
ALL windows of the uploaded subject. Non-causal by design: the +-15 min median and the
patient-level fits need the whole recording before any event is final (post-hoc review).

Flow (unchanged shape, see upload_manager.py):
  Phase A  per file, on upload: open, filter, window, signal-loss flags, and per-window first/second
           moments of the 3-s-padded filtered window (for the label-free statistics).
  Phase B  once per subject, when every file is uploaded: statistics -> features -> GAE ->
           per-channel distances -> ensemble score (timeline) + panel arrays.
  Stage 2  on Process: alarm budget -> detector -> localizer -> events per file.
"""
import argparse
import hashlib
import json
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
from scipy.signal import filtfilt, iirnotch, sosfiltfilt
from sklearn.covariance import LedoitWolf

# ── Wire up imports to the read-only thesis modules (same sys.path convention as
#    src/x1_external.py: add the directories, then import bare module names) ──
REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (REPO_ROOT / "src", REPO_ROOT / "src" / "dataprep", REPO_ROOT / "src" / "retrain",
           REPO_ROOT / "src" / "phaseB", REPO_ROOT / "src" / "phaseC"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import preprocessing                   # src/dataprep/preprocessing.py   (constants, open_edf)
import x1_external as X1               # src/x1_external.py              (label-free statistics)
import c1b_build_trainset as C1B       # src/c1b_build_trainset.py       (graph, node features)
import p2_dump_seeds23 as PD           # src/p2_dump_seeds23.py          (GAE v2 forward pass)
import p2_scalars as PS                # src/p2_scalars.py               (smoothing, detector)
import e22_test_oneshot as E22         # src/e22_test_oneshot.py         (final ensemble score)
import p3_levers as P3L                # src/p3_levers.py                (budget, localizer)

N_CH = len(preprocessing.COMMON_CHANNELS)  # 18
WIN_S = preprocessing.WIN_S                # 4 s
WIN_SAMPLES = preprocessing.WIN_SAMPLES    # 1024

# ── Frozen configuration, read from the committed freeze file (never typed from memory) ──
FREEZE_PATH = REPO_ROOT / "results" / "p3c_freeze" / "freeze.json"
FREEZE = json.loads(FREEZE_PATH.read_text())
OPERATING_POINT = "balanced"               # the thesis headline point; no UI control
BUDGET_FLOOR, BUDGET_CAP = FREEZE["points"][OPERATING_POINT]

# ── Model identity: GAE v2 clean seed 42 (docs/PROVENANCE_V2.md). Identify by hash, never name.
MODEL_TAG = "clean_seed42"
CHECKPOINT_PATH = REPO_ROOT / "data" / "models_v2" / f"gae_v2_{MODEL_TAG}.pt"
CHECKPOINT_SHA256 = "6e310307b046407a18d839273b84c74b2905457ec6ace892b674c6972dac590f"
# The checkpoint's companion file holds the training-set constants of the 7 added node features
# (add_mean / add_std / clip) that run_model applies; pinned so a changed constant cannot pass.
CHECKPOINT_META_PATH = CHECKPOINT_PATH.with_suffix(".json")
CHECKPOINT_META_SHA256 = "d1e2eee9924b9c23aedf1d8da0e2d289e88d2f790ff90c34958aa850870f06c5"

# ── Signal path constants (CHB-MIT): mains notch at 60 Hz, as preprocessing.py builds it ──
NOTCH_HZ = 60.0
_b, _a = iirnotch(NOTCH_HZ, Q=30, fs=preprocessing.FS)
assert np.array_equal(_b, preprocessing._NOTCH_B) and np.array_equal(_a, preprocessing._NOTCH_A), \
    "NOTCH_HZ does not reproduce preprocessing._NOTCH_B/_A"
STATS_SUBSAMPLE = preprocessing.STATS_SUBSAMPLE   # every 10th window (x1_external.labelfree_stats)
FEATURE_CHUNK = 256                               # windows per feature batch (x1_external.file_features)

# Signal-loss rule (unchanged from the earlier demo and identical to x1_external.file_features):
# a window is signal loss when the raw signal's std is below 1e-10 V on every one of 18 channels.
SIGNAL_LOSS_STD_V = 1e-10

# Panel files (names kept from the earlier demo so attribution.py / export_txt.py keep working):
# `{stem}.pernode.npy` now holds the per-channel latent distance D [n_windows, 18] (NaN at
# signal-loss windows); `pernode_baseline.npy` holds its subject-wide median and MAD (+1e-9).
PERNODE_BASELINE_FILENAME = "pernode_baseline.npy"


def compute_signal_loss_flags(raw_windows: np.ndarray) -> np.ndarray:
    """[n, 18, WIN_SAMPLES] raw volts -> [n] bool (std < 1e-10 V on every channel)."""
    return np.all(raw_windows.std(axis=2) < SIGNAL_LOSS_STD_V, axis=1)


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_checkpoint() -> None:
    for path, want in ((CHECKPOINT_PATH, CHECKPOINT_SHA256), (CHECKPOINT_META_PATH, CHECKPOINT_META_SHA256)):
        if not path.exists():
            raise FileNotFoundError(f"Checkpoint file not found: {path}")
        got = _sha256(path)
        if got != want:
            raise RuntimeError(f"Hash mismatch for {path.name}: expected {want}, got {got}. "
                               "Refusing to load an unverified checkpoint (docs/PROVENANCE_V2.md).")


class UnsupportedEdfError(ValueError):
    """Unreadable EDF or one of the 18 common channels missing -> SPEC §2 rejection toast."""


class CancelledError(Exception):
    """Raised by process_file_phase_a when the caller's cancel_check fires mid-run."""


# ════════════════════════════════════════════════════════════════════════════ Phase A
@dataclass
class PhaseAResult:
    filename: str
    filtered: np.ndarray       # [n_windows, 18, WIN_SAMPLES] float32, filtered, NOT z-scored
    flag: np.ndarray           # [n_windows] bool, signal loss
    moments: np.ndarray        # [n_windows, 18, 2] float64: sum and sum of squares of the
    #                            3-s-padded filtered window (label-free statistics, Phase B)
    n_windows: int
    start_time: datetime       # EDF header (meas_date) -- never shown as a calendar date
    file_duration_seconds: float
    filtered_path: Optional[Path] = None
    raw_path: Optional[Path] = None        # unfiltered windows (EEG panel raw view)
    bandpass_path: Optional[Path] = None   # band-pass-only windows (EEG panel filter toggle)
    flag_path: Optional[Path] = None
    moments_path: Optional[Path] = None


def padded_window_moments(data: np.ndarray, n_windows: int) -> np.ndarray:
    """Per window: per-channel sum and sum of squares of x1_external.window_padded(data, i) --
    the window filtered with 3 s of padding on each side, exactly the signal x1_external.
    labelfree_stats samples. Stored for EVERY window because which windows are 'every 10th of
    the subject' depends on the files uploaded before this one (resolved in Phase B)."""
    out = np.empty((n_windows, data.shape[0], 2), dtype=np.float64)
    for i in range(n_windows):
        w = X1.window_padded(data, i, NOTCH_HZ)
        out[i, :, 0] = w.sum(axis=1)
        out[i, :, 1] = (w * w).sum(axis=1)
    return out


def process_file_phase_a(edf_path: str, cancel_check=None, cache_dir: Optional[Path] = None) -> PhaseAResult:
    """Open, filter and window ONE file; signal-loss flags; per-window moments. No z-score, no
    graph, no model -- those need subject-wide statistics (Phase B). With `cache_dir`, every
    array is also written to `{cache_dir}/{stem}.{filtered,raw,bandpass,flag,moments}.npy`."""
    def _check():
        if cancel_check is not None and cancel_check():
            raise CancelledError(edf_path)

    _check()
    try:
        raw = preprocessing.open_edf(edf_path)
    except Exception as exc:  # mne raises a variety of exceptions for non-EDF/corrupt input
        raise UnsupportedEdfError(f"{edf_path}: could not be read as EDF ({exc})") from exc
    if raw is None:
        raise UnsupportedEdfError(f"{edf_path}: missing one or more of the 18 common channels "
                                  f"({preprocessing.COMMON_CHANNELS}).")
    if int(round(raw.info["sfreq"])) != preprocessing.FS:
        raise UnsupportedEdfError(f"{edf_path}: sampling rate {raw.info['sfreq']} Hz, expected {preprocessing.FS}.")
    n_windows = int(raw.n_times) // WIN_SAMPLES
    if n_windows == 0:
        raise UnsupportedEdfError(f"{edf_path}: shorter than one 4 s window -- nothing to score.")
    start_time = raw.info["meas_date"]
    if start_time is None:
        raise UnsupportedEdfError(f"{edf_path}: EDF header has no start time (meas_date).")
    file_duration_seconds = float(raw.n_times) / float(raw.info["sfreq"])

    _check()
    data = raw.get_data().astype(np.float64)          # [18, n_samples], volts
    usable = n_windows * WIN_SAMPLES
    # Whole-file zero-phase filtering: band-pass then notch (= x1_external.filter_windows).
    bp = sosfiltfilt(preprocessing._BP_SOS, data, axis=1)
    notched = filtfilt(preprocessing._NOTCH_B, preprocessing._NOTCH_A, bp, axis=1)

    def _win(x):
        return np.ascontiguousarray(x[:, :usable].reshape(N_CH, n_windows, WIN_SAMPLES).transpose(1, 0, 2))

    filtered = _win(notched).astype(np.float32)
    bandpass_windows = _win(bp).astype(np.float32)
    raw64 = _win(data)
    flag = compute_signal_loss_flags(raw64)
    raw_windows = raw64.astype(np.float32)
    del raw64, bp, notched
    _check()
    moments = padded_window_moments(data, n_windows)
    _check()

    paths = {}
    if cache_dir is not None:
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(edf_path).stem
        for key, arr in (("filtered", filtered), ("raw", raw_windows), ("bandpass", bandpass_windows),
                         ("flag", flag), ("moments", moments)):
            p = cache_dir / f"{stem}.{key}.npy"
            np.save(p, arr)
            paths[key] = p

    return PhaseAResult(
        filename=Path(edf_path).name, filtered=filtered, flag=flag, moments=moments,
        n_windows=n_windows, start_time=start_time, file_duration_seconds=file_duration_seconds,
        filtered_path=paths.get("filtered"), raw_path=paths.get("raw"),
        bandpass_path=paths.get("bandpass"), flag_path=paths.get("flag"),
        moments_path=paths.get("moments"),
    )


# ════════════════════════════════════════════════════════════════════════════ Phase B
def labelfree_zscore_stats(moments_by_filename: dict) -> tuple[np.ndarray, np.ndarray]:
    """x1_external.labelfree_stats from stored moments: files in filename order, a counter over
    every window of the subject, windows with counter % 10 == 0 kept; per-channel mean and std
    (ddof = 1) over all their samples. Returns (mean, std) in volts, std <= 0 replaced by 1."""
    s1 = np.zeros(N_CH); s2 = np.zeros(N_CH); m = 0; cnt = 0
    for fn in sorted(moments_by_filename):
        mom = moments_by_filename[fn]
        n = mom.shape[0]
        pick = np.flatnonzero((cnt + 1 + np.arange(n)) % STATS_SUBSAMPLE == 0)
        cnt += n
        s1 += mom[pick, :, 0].sum(axis=0)
        s2 += mom[pick, :, 1].sum(axis=0)
        m += len(pick) * WIN_SAMPLES
    if m < 2:
        raise UnsupportedEdfError(f"Recording too short for the subject statistics "
                                  f"(fewer than {STATS_SUBSAMPLE} windows in total).")
    mean = s1 / m
    var = (s2 - m * mean * mean) / (m - 1)
    sd = np.sqrt(np.maximum(var, 0.0))
    sd[sd <= 0] = 1.0
    return mean, sd


def file_features(filtered: np.ndarray, flag: np.ndarray, mu: np.ndarray, sd: np.ndarray):
    """Graph, band powers and the 7 added node features of the NON-signal-loss windows of one
    file, z-scored with the subject statistics (= x1_external.file_features, which builds every
    window; signal-loss windows never reach the model, so they are skipped here)."""
    keep = np.flatnonzero(~flag)
    adj, bp5, f7 = [], [], []
    for s in range(0, len(keep), FEATURE_CHUNK):
        rows = keep[s:s + FEATURE_CHUNK]
        zw = (np.asarray(filtered[rows]).astype(np.float64) - mu[None, :, None]) / sd[None, :, None]
        a_, b_ = C1B.graph_and_bp(zw)
        adj.append(a_); bp5.append(b_); f7.append(C1B.f7(zw))
    if not adj:
        return (np.empty((0, N_CH, N_CH), np.float16), np.empty((0, N_CH, 5), np.float32),
                np.empty((0, N_CH, 7), np.float32))
    return np.concatenate(adj), np.concatenate(bp5), np.concatenate(f7)


def run_gae(adj: np.ndarray, bp5: np.ndarray, f7: np.ndarray) -> np.ndarray:
    """Node latents [n, 18, 16] of GAE v2 seed 42, inputs prepared as x1_external.model_outputs."""
    verify_checkpoint()
    adj = adj.astype(np.float32); adj[~np.isfinite(adj).all(axis=(1, 2))] = 0.0
    bp5 = bp5.astype(np.float32); bp5[~np.isfinite(bp5)] = 0.0
    f7 = f7.astype(np.float64)
    xn = (bp5 - bp5.min(axis=1, keepdims=True)) / (bp5.max(axis=1, keepdims=True) - bp5.min(axis=1, keepdims=True) + 1e-8)
    _, Z = PD.run_model(MODEL_TAG, adj, xn, f7)
    return Z


def channel_distances(Z: np.ndarray) -> np.ndarray:
    """Per channel: LedoitWolf Mahalanobis distance of the 16-d node latent, fitted on every
    window given (all non-signal-loss windows of the subject) -- x1_external.model_outputs."""
    return np.column_stack([LedoitWolf().fit(Z[:, c, :].astype(np.float64)).mahalanobis(Z[:, c, :].astype(np.float64))
                            for c in range(Z.shape[1])]).astype(np.float64)


def subject_context(flag_by_filename: dict, dist_rows_by_filename: dict) -> dict:
    """The label-free subset of the thesis's per-subject context (p2_scalars.subject_context /
    x1_external.make_ctx): window axis = files in filename order; no label field exists here."""
    names = sorted(flag_by_filename)
    ok = np.concatenate([~np.asarray(flag_by_filename[f], bool) for f in names])
    fidx = np.concatenate([np.full(len(flag_by_filename[f]), i, int) for i, f in enumerate(names)])
    idx = np.flatnonzero(ok)
    D = np.concatenate([dist_rows_by_filename[f] for f in names], axis=0)
    if len(D) != len(idx):
        raise RuntimeError(f"{len(D)} distance rows for {len(idx)} non-signal-loss windows")
    return dict(n=len(ok), ok=ok, fidx=fidx, idx=idx, wf=fidx[idx], D={MODEL_TAG: D}, names=names)


def ensemble_score(ctx: dict) -> np.ndarray:
    """ONE ensemble anomaly score per window (e22_test_oneshot.final_scalar, frozen)."""
    return E22.final_scalar(ctx, MODEL_TAG)


def pernode_baseline(D: np.ndarray) -> np.ndarray:
    """[2, 18]: median and MAD (+1e-9) of each channel's distance over the subject's
    non-signal-loss windows -- the robust-z of e16_recording_baseline.rz / attribution_v8.rz."""
    med = np.median(D, axis=0)
    mad = np.median(np.abs(D - med), axis=0) + 1e-9
    return np.stack([med, mad])


@dataclass
class PhaseBResult:
    scores: dict          # {filename: [n_windows] ensemble score}
    dists: dict           # {filename: [n_windows, 18] distance, NaN rows at signal loss}
    baseline: np.ndarray  # [2, 18]
    stats: tuple          # (mean, std) volts, the z-score statistics used


def process_subject_phase_b(filtered_by_filename: dict, flag_by_filename: dict, moments_by_filename: dict,
                            stats_override: Optional[tuple] = None, timing: Optional[dict] = None) -> PhaseBResult:
    """Subject statistics -> features -> GAE -> per-channel distances -> ensemble score.

    `filtered_by_filename` values may be memory-mapped arrays (np.load(..., mmap_mode='r')).
    `stats_override` = (mean, std) in volts is used ONLY by the thesis-side identity gate
    (src/t1_demo_gate.py) to feed the thesis's own statistics; the application never sets it."""
    t0 = time.perf_counter()
    names = sorted(filtered_by_filename)
    if not names:
        raise ValueError("no file")
    mu, sd = stats_override if stats_override is not None else labelfree_zscore_stats(
        {f: moments_by_filename[f] for f in names})
    t1 = time.perf_counter()
    feats = {f: file_features(filtered_by_filename[f], np.asarray(flag_by_filename[f], bool), mu, sd) for f in names}
    t2 = time.perf_counter()
    adj = np.concatenate([feats[f][0] for f in names]); bp5 = np.concatenate([feats[f][1] for f in names])
    f7 = np.concatenate([feats[f][2] for f in names])
    if len(adj) < 2:
        raise UnsupportedEdfError("Fewer than two windows with signal in this subject.")
    Z = run_gae(adj, bp5, f7)
    t3 = time.perf_counter()
    D = channel_distances(Z)
    rows, cur = {}, 0
    for f in names:
        k = len(feats[f][0]); rows[f] = D[cur:cur + k]; cur += k
    ctx = subject_context(flag_by_filename, rows)
    x = ensemble_score(ctx)
    scores, dists, cur = {}, {}, 0
    for i, f in enumerate(names):
        m = ctx["fidx"] == i
        scores[f] = x[m].astype(np.float64)
        full = np.full((int(m.sum()), N_CH), np.nan)
        full[ctx["ok"][m]] = rows[f]
        dists[f] = full
    t4 = time.perf_counter()
    if timing is not None:
        timing.update(stats=t1 - t0, features=t2 - t1, gae=t3 - t2, distances_and_score=t4 - t3)
    return PhaseBResult(scores=scores, dists=dists, baseline=pernode_baseline(D), stats=(mu, sd))


def process_subject_phase_b_from_paths(filtered_paths: dict, flag_paths: dict, moments_paths: dict,
                                       timing: Optional[dict] = None) -> PhaseBResult:
    """Worker-process entry point: arrays are read from disk inside the worker (memory-mapped
    for the filtered windows), never sent through a pipe."""
    return process_subject_phase_b(
        {fn: np.load(p, mmap_mode="r") for fn, p in filtered_paths.items()},
        {fn: np.load(p) for fn, p in flag_paths.items()},
        {fn: np.load(p) for fn, p in moments_paths.items()},
        timing=timing,
    )


# ════════════════════════════════════════════════════════════════════════════ Stage 2
@dataclass
class FileEvent:
    onset_sec: float
    offset_sec: float


@dataclass
class AlarmBudget:
    q: float      # label-free share of the patient's smoothed member-mean robust-z above k
    top: float    # p_i = clip(q, floor, cap): share of the patient's time the detector flags


def process_subject_events(scores_by_filename: dict, flag_by_filename: dict, dist_by_filename: dict,
                           timing: Optional[dict] = None, trace: Optional[dict] = None) -> tuple[dict, AlarmBudget]:
    """Alarm budget -> detector -> kernel-CPD localizer, per file. Events are in seconds from the
    start of their own file; the detector works inside each file, so no event crosses a file.
    `trace` (optional dict) receives the detector's events before the localizer, per filename --
    used only by the thesis-side identity gate; the application shows the localized events."""
    t0 = time.perf_counter()
    names = sorted(scores_by_filename)
    rows = {}
    for f in names:
        D = np.asarray(dist_by_filename[f], float)
        okr = np.isfinite(D).all(axis=1)
        if not np.array_equal(okr, ~np.asarray(flag_by_filename[f], bool)):
            raise RuntimeError(f"{f}: distance rows do not match the signal-loss flags")
        rows[f] = D[okr]
    ctx = subject_context({f: flag_by_filename[f] for f in names}, rows)
    x = ensemble_score(ctx)
    given = np.concatenate([np.asarray(scores_by_filename[f], float) for f in names])
    if given.shape != x.shape or not np.allclose(given, x, rtol=0, atol=1e-9):
        raise RuntimeError("Phase B scores do not match the distances they were built from")

    # ---- the same lines as e23_test_look7.evaluate (frozen system), without the scoring ----
    cfg = FREEZE
    floor, cap = BUDGET_FLOOR, BUDGET_CAP
    q = P3L.q_of(PS.smoothed(ctx, P3L.member_mean_z(ctx, MODEL_TAG), cfg["smooth"]), cfg["k"])
    top = float(np.clip(q, floor, max(cap, floor)))
    det = PS.d1_events(ctx, x, cfg["smooth"], top)
    thr = np.nanquantile(PS.smoothed(ctx, x, cfg["smooth"]), 1 - top)
    loc, _ = P3L.localize(ctx, x, det, thr, cfg["localizer"])
    # -----------------------------------------------------------------------------------------
    events = {f: [FileEvent(float(a), float(b)) for a, b in loc.get(i, [])] for i, f in enumerate(names)}
    if trace is not None:
        trace["detector"] = {f: [(float(a), float(b)) for a, b in det.get(i, [])] for i, f in enumerate(names)}
        trace["threshold"] = float(thr)
    if timing is not None:
        timing["events"] = time.perf_counter() - t0
    return events, AlarmBudget(q=float(q), top=top)


# ════════════════════════════════════════════════════════════════════════════ headless
DEFAULT_HEADLESS_CACHE_DIR = REPO_ROOT / "web_demo" / "backend" / "cache" / "headless"
HEADLESS_MAX_WORKERS = 2   # same cap as upload_manager's Phase A pool (memory)


def process_subject_headless(edf_paths: list, cache_dir: Optional[Path] = None,
                             max_workers: int = HEADLESS_MAX_WORKERS, stats_override: Optional[tuple] = None,
                             timing: Optional[dict] = None) -> dict:
    """Phase A -> Phase B -> Stage 2 through the same functions as the live flow, with no database
    and no HTTP (identity gate, timing). No annotation is read. Returns a dict with scores, flags,
    dists, baseline, stats, events ({filename: [(onset_s, offset_s)]}), budget and n_windows."""
    cache_dir = Path(cache_dir or DEFAULT_HEADLESS_CACHE_DIR)
    cache_dir.mkdir(parents=True, exist_ok=True)
    tm = timing if timing is not None else {}
    prev_tempdir = tempfile.tempdir
    tempfile.tempdir = str(cache_dir)
    try:
        t0 = time.perf_counter()
        res = {}
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futs = [ex.submit(process_file_phase_a, p, None, cache_dir) for p in edf_paths]
            for fut in as_completed(futs):
                r = fut.result()
                r.filtered = None       # read back memory-mapped below; keeps peak memory low
                res[r.filename] = r
        tm["phase_a"] = time.perf_counter() - t0
        filtered = {fn: np.load(r.filtered_path, mmap_mode="r") for fn, r in res.items()}
        flags = {fn: r.flag for fn, r in res.items()}
        moments = {fn: r.moments for fn, r in res.items()}
        t1 = time.perf_counter()
        b = process_subject_phase_b(filtered, flags, moments, stats_override=stats_override, timing=tm)
        tm["phase_b"] = time.perf_counter() - t1
        t2 = time.perf_counter()
        trace: dict = {}
        events, budget = process_subject_events(b.scores, flags, b.dists, timing=tm, trace=trace)
        tm["stage2"] = time.perf_counter() - t2
        tm["total"] = time.perf_counter() - t0
    finally:
        tempfile.tempdir = prev_tempdir
    return dict(scores=b.scores, flags=flags, dists=b.dists, baseline=b.baseline, stats=b.stats,
                events={f: [(e.onset_sec, e.offset_sec) for e in v] for f, v in events.items()},
                budget=budget, detector=trace["detector"], n_windows={fn: r.n_windows for fn, r in res.items()},
                durations={fn: r.file_duration_seconds for fn, r in res.items()})


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Dev CLI: one subject (or one file) through the demo "
                                             "pipeline headless. Prints events and timing; no metric.")
    ap.add_argument("edf_paths", nargs="+")
    ap.add_argument("--cache-dir", default=None)
    a = ap.parse_args()
    tm: dict = {}
    out = process_subject_headless(a.edf_paths, cache_dir=a.cache_dir, timing=tm)
    hours = sum(out["n_windows"].values()) * WIN_S / 3600
    print(f"files {len(a.edf_paths)}, {hours:.2f} h, alarm budget top {out['budget'].top:.4f} (q {out['budget'].q:.4f})")
    for f, ev in out["events"].items():
        print(f"  {f}: {len(ev)} events {ev[:5]}{' ...' if len(ev) > 5 else ''}")
    print("timing (s): " + ", ".join(f"{k} {v:.1f}" for k, v in tm.items()))
    print(f"{tm['total'] / max(hours, 1e-9):.2f} s per hour of EEG (end to end, this run)")
