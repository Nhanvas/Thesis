"""waveform_serving.py — Panel EEG waveform endpoint support (Step 4, CC_STEP4_PROMPT.md).

Serves decimated min/max envelopes of the currently-viewed time window from Phase A's
per-file cache (`{stem}.raw.npy` / `{stem}.filtered.npy`, both [n_windows, 18, WIN_SAMPLES]
float32, in Volts — see pipeline_demo.process_file_phase_a). Never sends a raw/lightly-
sampled array to the browser (18 ch x 256 Hz x 1 h ~= 16.6M points/file — DEMO_BUILD_HANDOFF.md
§5). Both raw and filtered are always decimated and returned together in one response so a
filter-toggle click never needs a second round trip — the frontend already holds both once a
window is fetched and switches which is drawn prominent purely client-side (SPEC §6.4).

Reuses pipeline_demo's already-configured `preprocessing` import (same sys.path wiring to
src/dataprep) rather than re-importing it separately.
"""
from pathlib import Path

import numpy as np

import pipeline_demo as pd

FS = pd.preprocessing.FS                      # 256 Hz
WIN_SAMPLES = pd.preprocessing.WIN_SAMPLES     # 1024 (4 s windows)
CHANNELS = pd.preprocessing.COMMON_CHANNELS    # 18 fixed channel names, pipeline order


def _cache_paths(subject_id: str, filename: str, upload_dir: Path) -> tuple[Path, Path]:
    stem = Path(filename).stem
    base = Path(upload_dir) / subject_id
    return base / f"{stem}.raw.npy", base / f"{stem}.filtered.npy"


def _score_path(subject_id: str, filename: str, upload_dir: Path) -> Path:
    stem = Path(filename).stem
    return Path(upload_dir) / subject_id / f"{stem}.score.npy"


def usable_duration_seconds(raw_path: Path) -> float:
    """Total seconds actually covered by the cached windows. May be up to WIN_S (4 s)
    shorter than the EDF header's true duration — Phase A drops the trailing partial
    window (pipeline_demo.process_file_phase_a's own `n_windows = n_times // WIN_SAMPLES`),
    so this is the real, authoritative bound for what the waveform endpoint can serve."""
    mm = np.load(raw_path, mmap_mode="r")
    n_windows = mm.shape[0]
    return n_windows * WIN_SAMPLES / FS


def _load_window(npy_path: Path, start_sec: float, end_sec: float) -> np.ndarray:
    """Load exactly the requested [start_sec, end_sec) range from the on-disk cache via
    mmap — never materializes the whole file's array in RAM regardless of file length.
    Returns [18, n_samples] float64, in Volts (the cache's native unit)."""
    mm = np.load(npy_path, mmap_mode="r")  # [n_windows, 18, WIN_SAMPLES]
    n_windows = mm.shape[0]
    total_samples = n_windows * WIN_SAMPLES

    start_sample = max(0, int(round(start_sec * FS)))
    end_sample = min(total_samples, int(round(end_sec * FS)))
    if end_sample <= start_sample:
        return np.zeros((len(CHANNELS), 0), dtype=np.float64)

    win_lo = start_sample // WIN_SAMPLES
    win_hi = (end_sample - 1) // WIN_SAMPLES + 1
    chunk = np.asarray(mm[win_lo:win_hi])  # copies only the needed windows out of the mmap
    continuous = chunk.transpose(1, 0, 2).reshape(len(CHANNELS), -1)  # [18, k*WIN_SAMPLES]

    lo_in_chunk = start_sample - win_lo * WIN_SAMPLES
    hi_in_chunk = end_sample - win_lo * WIN_SAMPLES
    return continuous[:, lo_in_chunk:hi_in_chunk].astype(np.float64)


def _decimate_envelope(data: np.ndarray, n_buckets: int) -> np.ndarray:
    """[18, n_samples] -> [18, n_buckets, 2] (min, max) per bucket. One bucket per pixel
    column of canvas width (DEMO_BUILD_HANDOFF.md §5's "~2-4 points per pixel, min/max
    envelope, never naive subsampling" — naive subsampling would flatten real spikes)."""
    n_ch, n_samples = data.shape
    if n_samples == 0 or n_buckets <= 0:
        return np.zeros((n_ch, max(n_buckets, 0), 2), dtype=np.float32)
    edges = np.round(np.linspace(0, n_samples, n_buckets + 1)).astype(np.int64)
    out = np.empty((n_ch, n_buckets, 2), dtype=np.float32)
    for b in range(n_buckets):
        lo = edges[b]
        hi = min(max(edges[b + 1], lo + 1), n_samples)
        chunk = data[:, lo:hi]
        out[:, b, 0] = chunk.min(axis=1)
        out[:, b, 1] = chunk.max(axis=1)
    return out


def get_waveform(
    subject_id: str,
    filename: str,
    upload_dir: Path,
    start_sec: float,
    end_sec: float,
    width_px: int,
) -> dict:
    """Single endpoint backing Panel EEG (SPEC §6.4): one call returns both raw and
    filtered decimated envelopes for [start_sec, end_sec), clamped to the file's usable
    duration. Values are in µV (the toolbar's `[X] uV` amplitude control's unit)."""
    raw_path, filtered_path = _cache_paths(subject_id, filename, upload_dir)
    duration = usable_duration_seconds(raw_path)
    start_sec = max(0.0, min(start_sec, duration))
    end_sec = max(start_sec, min(end_sec, duration))

    raw_v = _load_window(raw_path, start_sec, end_sec)
    filt_v = _load_window(filtered_path, start_sec, end_sec)

    n_buckets = max(1, int(width_px))
    raw_uv = _decimate_envelope(raw_v * 1e6, n_buckets)
    filt_uv = _decimate_envelope(filt_v * 1e6, n_buckets)

    return {
        "channels": CHANNELS,
        "start_sec": start_sec,
        "end_sec": end_sec,
        "usable_duration_seconds": duration,
        "n_buckets": n_buckets,
        "raw_uv": raw_uv.round(2).tolist(),
        "filtered_uv": filt_uv.round(2).tolist(),
    }


def get_timeline(subject_id: str, filename: str, upload_dir: Path) -> dict:
    """Mini-timeline's 'Seizure Detection Score' row (SPEC §6.3): the whole file's per-
    window ensemble score, read from the `{stem}.score.npy` cache (Step 5 backfill —
    CC_STEP5_REPORT.md — for the subjects already in the DB before this array was
    persisted; written going forward by whatever step wires it into the live Process
    flow). Window count for a single file (<= 900 for the longest file in the current
    allowlist, one hour of 4 s windows) is small enough to return whole, no decimation —
    unlike the waveform endpoint, there is no 18-channel/256 Hz volume problem here."""
    score_path = _score_path(subject_id, filename, upload_dir)
    if not score_path.exists():
        raise FileNotFoundError(
            f"No cached score array for {subject_id}/{filename} ({score_path}). "
            "This file's ensemble score was never persisted — see CC_STEP5_REPORT.md."
        )
    score = np.load(score_path)
    return {
        "score": score.round(4).tolist(),
        "window_sec": WIN_SAMPLES / FS,
    }
