"""
preprocessing.py
================
CHB-MIT EEG preprocessing pipeline — aligned with thesis_plan_final.md §3.

Pipeline (6 steps, mandatory order):
  Step 1: Bandpass filter 0.5–60 Hz (Butterworth 4th order, zero-phase)
  Step 2: Notch filter 60 Hz (IIR notch, Q=30, zero-phase)
  Step 3: CAR — applied in graph_construction.py before wPLI
  Step 4: Amplitude artifact rejection — drop windows where any sample
          exceeds 5 × per-channel SD (threshold computed from interictal)
  Step 5: Z-score normalization — per channel, per subject
          Stats (mean, std) computed from filtered interictal windows.
          Applied to BOTH interictal and ictal windows.
  Step 6: 4s non-overlapping windows (1024 samples at 256 Hz)

Additional design decisions:
  - 4h post-seizure buffer: interictal windows within 4h after any seizure
    end are excluded from training. This removes peri-ictal contamination.
    Ictal windows are still extracted from these files for evaluation.
  - Ictal windows: NOT artifact-rejected. Seizure EEG has naturally high
    amplitude — rejecting ictal would systematically underestimate sensitivity.
  - Two-pass + stats-pass memmap strategy: peak RAM ≈ one window = 0.15 MB.
    No intermediate list of windows is held in RAM.

Outputs per subject:
  {subj}_interictal.npy   [N, 18, 1024]  float32  z-scored, artifact-clean
  {subj}_ictal.npy        [M, 18, 1024]  float32  z-scored, NOT artifact-rejected
  {subj}_stats.json       preprocessing statistics

References:
  - Bandpass + notch: standard EEG clinical preprocessing
  - 5 SD artifact threshold: Shyu et al. 2023, Salafian et al. 2023
  - Z-score per subject: removes inter-subject amplitude scale differences
"""

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning,
                        message=".*Channel names are not unique.*")

import json
import re
import numpy as np
import mne
from pathlib import Path
from scipy.signal import butter, sosfiltfilt, iirnotch, filtfilt

mne.set_log_level("WARNING")

# ── Constants ─────────────────────────────────────────────────────────────────

FS          = 256
WIN_S       = 4
WIN_SAMPLES = FS * WIN_S        # 1024
BUFFER_S    = 4 * 3600          # 4h post-seizure exclusion
FILTER_PAD  = 3 * FS            # 768 samples padding per side

N_CH  = 18
N_SMP = WIN_SAMPLES

# Artifact threshold multiplier (plan §3 Step 4)
ARTIFACT_SD_MULTIPLIER = 5.0

# Subsample rate for stats collection (every Nth interictal window)
STATS_SUBSAMPLE = 10

COMMON_CHANNELS = [
    "FP1-F7", "F7-T7", "T7-P7", "P7-O1",
    "FP1-F3", "F3-C3", "C3-P3", "P3-O1",
    "FP2-F4", "F4-C4", "C4-P4", "P4-O2",
    "FP2-F8", "F8-T8", "T8-P8", "P8-O2",
    "FZ-CZ",  "CZ-PZ",
]

# ── Build filters once at module load ─────────────────────────────────────────

# Step 1: Bandpass 0.5–60 Hz, 4th-order Butterworth, zero-phase (sosfiltfilt)
_BP_SOS = butter(4, [0.5, 60.0], btype="bandpass", fs=FS, output="sos")

# Step 2: Notch at 60 Hz, Q=30
_NOTCH_B, _NOTCH_A = iirnotch(60.0, Q=30, fs=FS)


# ── 1. Parse summary file ─────────────────────────────────────────────────────

def parse_summary(summary_path: Path) -> dict:
    """
    Parse chbXX-summary.txt.
    Returns dict: filename → list of (onset_s, offset_s).

    Parser is index-agnostic on Start/End lines to handle CHB-MIT typo:
        'Seizure 2 Start Time: ...'
        'Seizure 1 End Time: ...'   ← wrong index in chb09_08
    """
    seizures: dict = {}
    current_file: str | None = None
    pending_onset: int | None = None

    with open(summary_path, "r") as f:
        for line in f:
            line = line.strip()

            if line.startswith("File Name:"):
                if pending_onset is not None:
                    print(f"  [WARN] dangling onset {pending_onset}s "
                          f"in {current_file} — no End Time found")
                    pending_onset = None
                current_file = line.split(":", 1)[1].strip()
                seizures[current_file] = []

            elif "Start Time:" in line and current_file is not None:
                m = re.search(r"(\d+)\s*seconds", line)
                if m:
                    pending_onset = int(m.group(1))

            elif "End Time:" in line and current_file is not None:
                m = re.search(r"(\d+)\s*seconds", line)
                if m and pending_onset is not None:
                    offset = int(m.group(1))
                    if offset > pending_onset:
                        seizures[current_file].append((pending_onset, offset))
                    else:
                        print(f"  [WARN] invalid interval "
                              f"({pending_onset}–{offset}) in {current_file}")
                    pending_onset = None

    return seizures


# ── 2. Open EDF ───────────────────────────────────────────────────────────────

def open_edf(edf_path: Path):
    """
    Open EDF, normalise channel names, pick 18 common channels.
    Returns None if any common channel is missing.
    """
    raw = mne.io.read_raw_edf(str(edf_path), preload=False, verbose=False)
    raw.rename_channels({ch: ch.upper().strip() for ch in raw.ch_names})

    rename_map: dict = {}
    seen: set = set()
    for ch in raw.ch_names:
        m = re.match(r"^(.*)-(\d+)$", ch)
        if m:
            base = m.group(1)
            if base not in seen:
                rename_map[ch] = base
                seen.add(base)
    if rename_map:
        raw.rename_channels(rename_map)

    missing = set(COMMON_CHANNELS) - set(raw.ch_names)
    if missing:
        return None

    raw.pick(COMMON_CHANNELS)
    raw.reorder_channels(COMMON_CHANNELS)
    return raw


# ── 3. Filter one window (Steps 1 + 2) ───────────────────────────────────────

def filter_window(raw, start: int, end: int) -> np.ndarray:
    """
    Read [start-pad, end+pad), apply bandpass then notch, return centre.
    Both filters applied zero-phase (sosfiltfilt / filtfilt).
    Returns [N_CH, WIN_SAMPLES] float64.
    """
    n_total   = int(raw.n_times)
    pad_start = max(0, start - FILTER_PAD)
    pad_end   = min(n_total, end + FILTER_PAD)

    segment = raw.get_data(start=pad_start, stop=pad_end)  # [18, L]

    # Step 1: Bandpass
    bp = sosfiltfilt(_BP_SOS, segment, axis=1)

    # Step 2: Notch at 60 Hz
    notched = filtfilt(_NOTCH_B, _NOTCH_A, bp, axis=1)

    offset = start - pad_start
    return notched[:, offset : offset + WIN_SAMPLES]


# ── 4. Label and buffer arrays ────────────────────────────────────────────────

def build_labels(n_seconds: int, seizure_list: list) -> np.ndarray:
    labels = np.zeros(n_seconds, dtype=np.int8)
    for onset, offset in seizure_list:
        labels[max(0, onset) : min(n_seconds, offset)] = 1
    return labels


def build_buffer_mask(n_seconds: int, seizure_list: list) -> np.ndarray:
    """4h post-seizure exclusion mask for interictal windows."""
    mask = np.zeros(n_seconds, dtype=bool)
    for _, offset in seizure_list:
        mask[offset : min(n_seconds, offset + BUFFER_S)] = True
    return mask


# ── 5. Stats pass — compute per-channel mean/std from filtered interictal ─────

def compute_subject_stats(subject_id: str, raw_dir: Path,
                          seizure_map: dict) -> tuple[np.ndarray, np.ndarray]:
    """
    Subsample interictal windows (every STATS_SUBSAMPLE-th), filter them,
    compute per-channel mean and std using Welford's online algorithm.

    Returns:
        ch_mean: [18]  per-channel mean of filtered interictal signal
        ch_std:  [18]  per-channel std of filtered interictal signal

    These are used for:
      - Artifact threshold: 5 × ch_std (per channel)
      - Z-score normalization (Step 5)
    """
    # Welford accumulators: one value per channel (mean across all samples)
    n_count  = np.zeros(N_CH, dtype=np.float64)
    ch_mean  = np.zeros(N_CH, dtype=np.float64)
    ch_M2    = np.zeros(N_CH, dtype=np.float64)

    window_counter = 0

    for edf_path in sorted((raw_dir / subject_id).glob("*.edf")):
        seizure_list = seizure_map.get(edf_path.name, [])
        raw = open_edf(edf_path)
        if raw is None:
            continue

        n_samples = int(raw.n_times)
        n_seconds = n_samples // FS
        n_windows = n_samples // WIN_SAMPLES

        labels      = build_labels(n_seconds, seizure_list)
        buffer_mask = build_buffer_mask(n_seconds, seizure_list)

        for i in range(n_windows):
            start_s = i * WIN_S
            end_s   = start_s + WIN_S

            win_label    = int(labels[start_s:end_s].max())
            win_buffered = bool(buffer_mask[start_s:end_s].any())

            if win_label == 1 or win_buffered:
                continue

            # Subsample: only process every STATS_SUBSAMPLE-th window
            window_counter += 1
            if window_counter % STATS_SUBSAMPLE != 0:
                continue

            start  = i * WIN_SAMPLES
            end    = start + WIN_SAMPLES
            window = filter_window(raw, start, end)  # [18, 1024]

            # Welford update — per channel, across all time samples
            for ch in range(N_CH):
                for sample_val in window[ch]:
                    n_count[ch]  += 1
                    delta         = sample_val - ch_mean[ch]
                    ch_mean[ch]  += delta / n_count[ch]
                    ch_M2[ch]    += delta * (sample_val - ch_mean[ch])

        del raw

    # Avoid division by zero
    with np.errstate(invalid="ignore"):
        ch_std = np.sqrt(ch_M2 / np.maximum(n_count - 1, 1))

    ch_std = np.where(ch_std > 0, ch_std, 1.0)  # fallback to 1.0 if flat

    return ch_mean.astype(np.float32), ch_std.astype(np.float32)


# ── 6. Count pass ─────────────────────────────────────────────────────────────

def count_windows(subject_id: str, raw_dir: Path,
                  seizure_map: dict,
                  artifact_threshold: np.ndarray) -> tuple[int, int, int]:
    """
    Count valid windows.
    artifact_threshold: [18] per-channel threshold in Volts.
    Artifact rejection applied to interictal ONLY.
    """
    n_inter    = 0
    n_ictal    = 0
    n_rejected = 0

    for edf_path in sorted((raw_dir / subject_id).glob("*.edf")):
        seizure_list = seizure_map.get(edf_path.name, [])
        raw = open_edf(edf_path)
        if raw is None:
            continue

        n_samples = int(raw.n_times)
        n_seconds = n_samples // FS
        n_windows = n_samples // WIN_SAMPLES

        labels      = build_labels(n_seconds, seizure_list)
        buffer_mask = build_buffer_mask(n_seconds, seizure_list)

        for i in range(n_windows):
            start_s = i * WIN_S
            end_s   = start_s + WIN_S

            win_label    = int(labels[start_s:end_s].max())
            win_buffered = bool(buffer_mask[start_s:end_s].any())

            if win_label == 1:
                n_ictal += 1
            elif not win_buffered:
                start  = i * WIN_SAMPLES
                end    = start + WIN_SAMPLES
                window = filter_window(raw, start, end)

                # Step 4: artifact rejection — 5 SD per channel
                is_artifact = False
                for ch in range(N_CH):
                    if np.abs(window[ch]).max() > artifact_threshold[ch]:
                        is_artifact = True
                        break

                if is_artifact:
                    n_rejected += 1
                else:
                    n_inter += 1

        del raw

    return n_inter, n_ictal, n_rejected


# ── 7. Write pass ─────────────────────────────────────────────────────────────

def write_windows(subject_id: str, raw_dir: Path,
                  seizure_map: dict,
                  artifact_threshold: np.ndarray,
                  ch_mean: np.ndarray,
                  ch_std: np.ndarray,
                  mm_inter, mm_ictal,
                  n_inter_max: int,
                  n_ictal_max: int) -> None:
    """
    Filter + artifact reject + z-score normalize + write to memmap.
    """
    idx_inter = 0
    idx_ictal = 0

    for edf_path in sorted((raw_dir / subject_id).glob("*.edf")):
        seizure_list = seizure_map.get(edf_path.name, [])
        raw = open_edf(edf_path)
        if raw is None:
            continue

        n_samples = int(raw.n_times)
        n_seconds = n_samples // FS
        n_windows = n_samples // WIN_SAMPLES

        labels      = build_labels(n_seconds, seizure_list)
        buffer_mask = build_buffer_mask(n_seconds, seizure_list)

        for i in range(n_windows):
            start_s = i * WIN_S
            end_s   = start_s + WIN_S

            win_label    = int(labels[start_s:end_s].max())
            win_buffered = bool(buffer_mask[start_s:end_s].any())

            if win_label == 1:
                if idx_ictal < n_ictal_max:
                    start  = i * WIN_SAMPLES
                    end    = start + WIN_SAMPLES
                    window = filter_window(raw, start, end)

                    # Step 5: z-score (ictal gets same normalization params)
                    window_norm = (window - ch_mean[:, None]) / ch_std[:, None]
                    mm_ictal[idx_ictal] = window_norm.astype(np.float32)
                    idx_ictal += 1

            elif not win_buffered:
                start  = i * WIN_SAMPLES
                end    = start + WIN_SAMPLES
                window = filter_window(raw, start, end)

                # Step 4: artifact rejection
                is_artifact = False
                for ch in range(N_CH):
                    if np.abs(window[ch]).max() > artifact_threshold[ch]:
                        is_artifact = True
                        break

                if not is_artifact and idx_inter < n_inter_max:
                    # Step 5: z-score
                    window_norm = (window - ch_mean[:, None]) / ch_std[:, None]
                    mm_inter[idx_inter] = window_norm.astype(np.float32)
                    idx_inter += 1

        del raw


# ── 8. Main: process one subject ─────────────────────────────────────────────

def process_subject(subject_id: str, raw_dir: Path,
                    processed_dir: Path) -> dict:
    """
    Three-pass strategy:
      Stats pass : compute per-channel mean/std from subsampled interictal
      Count pass : count valid windows with 5 SD artifact rejection
      Write pass : filter + z-normalize + write to memmap

    Peak RAM ≈ one window = 18 × 1024 × 8 B ≈ 0.15 MB
    """
    processed_dir.mkdir(parents=True, exist_ok=True)

    summary_path = (raw_dir / "CHB info" / "summary" /
                    f"{subject_id}-summary.txt")
    seizure_map = parse_summary(summary_path)

    # ── Stats pass ────────────────────────────────────────────────────────────
    print(f"  [stats] computing per-channel mean/std "
          f"(subsampling 1/{STATS_SUBSAMPLE})...")
    ch_mean, ch_std = compute_subject_stats(subject_id, raw_dir, seizure_map)

    # Artifact threshold: 5 × per-channel SD (in Volts)
    artifact_threshold = ARTIFACT_SD_MULTIPLIER * ch_std
    print(f"  [stats] artifact threshold (mean across ch): "
          f"{artifact_threshold.mean()*1e6:.1f} µV")

    # ── Count pass ────────────────────────────────────────────────────────────
    print(f"  [count] counting windows with 5 SD artifact rejection...")
    n_inter, n_ictal, n_rejected = count_windows(
        subject_id, raw_dir, seizure_map, artifact_threshold)
    print(f"  [count] interictal={n_inter} | ictal={n_ictal} "
          f"| rejected={n_rejected}")

    if n_inter == 0:
        raise RuntimeError(
            f"{subject_id}: zero interictal windows — check data path")

    # ── Allocate memmap ───────────────────────────────────────────────────────
    prefix = processed_dir / subject_id

    mm_inter = np.lib.format.open_memmap(
        f"{prefix}_interictal.npy", mode="w+",
        dtype=np.float32, shape=(n_inter, N_CH, N_SMP))
    mm_ictal = np.lib.format.open_memmap(
        f"{prefix}_ictal.npy", mode="w+",
        dtype=np.float32, shape=(max(n_ictal, 1), N_CH, N_SMP))

    # ── Write pass ────────────────────────────────────────────────────────────
    print(f"  [write] filtering + z-normalizing + writing to disk...")
    write_windows(
        subject_id, raw_dir, seizure_map,
        artifact_threshold, ch_mean, ch_std,
        mm_inter, mm_ictal, n_inter, n_ictal
    )
    del mm_inter, mm_ictal

    # ── Save normalization stats ──────────────────────────────────────────────
    stats = {
        "subject_id":         subject_id,
        "n_interictal":       n_inter,
        "n_ictal":            n_ictal,
        "n_rejected":         n_rejected,
        "ratio":              round(n_inter / max(n_ictal, 1), 1),
        "ch_mean_uV":         (ch_mean * 1e6).tolist(),
        "ch_std_uV":          (ch_std  * 1e6).tolist(),
        "artifact_thresh_uV": (artifact_threshold * 1e6).tolist(),
    }
    with open(f"{prefix}_stats.json", "w") as fout:
        json.dump(stats, fout, indent=2)

    print(f"[{subject_id}] DONE — interictal={n_inter} | ictal={n_ictal} "
          f"| rejected={n_rejected} | ratio={stats['ratio']}:1")
    return stats


# ── 9. Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--subjects", nargs="+",
        default=[f"chb{i:02d}" for i in range(1, 24)],
        help="Subject IDs to process. Default: all 23."
    )
    args = parser.parse_args()

    RAW_DIR       = Path("F:/Study/Thesis/Dataset/CHB-MIT")
    PROCESSED_DIR = Path("F:/Study/Thesis/Code/data/processed")

    all_stats = []
    for subj in args.subjects:
        print(f"\n{'='*60}")
        print(f"Processing {subj}...")
        print(f"{'='*60}")
        try:
            stats = process_subject(subj, RAW_DIR, PROCESSED_DIR)
            all_stats.append(stats)
        except Exception as e:
            print(f"  [ERROR] {subj}: {e}")

    print("\n=== PREPROCESSING COMPLETE ===")
    total_inter = sum(s["n_interictal"] for s in all_stats)
    total_ictal = sum(s["n_ictal"] for s in all_stats)
    total_rej   = sum(s["n_rejected"] for s in all_stats)
    print(f"Total interictal: {total_inter:,}")
    print(f"Total ictal:      {total_ictal:,}")
    print(f"Total rejected:   {total_rej:,}")
    for s in all_stats:
        print(f"  {s['subject_id']}: {s['n_interictal']:6d} inter | "
              f"{s['n_ictal']:4d} ictal | "
              f"{s['n_rejected']:5d} rejected | ratio {s['ratio']}:1")