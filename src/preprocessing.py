"""
preprocessing.py
================
CHB-MIT EEG preprocessing pipeline.

Design decisions (thesis §2.1):
  - Bandpass: 0.5–40 Hz, 4th-order Butterworth, zero-phase (sosfiltfilt)
    with 3s padding per side to avoid edge artifacts
  - Artifact rejection: ±500 µV threshold applied to INTERICTAL windows only
    Ictal windows are NOT artifact-rejected — seizure EEG has high amplitude
    by nature (838–1622 µV observed in CHB-MIT). Rejecting ictal windows
    would cause systematic underestimation of sensitivity.
  - Window: 4s non-overlapping (1024 samples at 256 Hz)
  - Interictal training set: excludes 4h post-seizure buffer per file
  - Adjacency matrices: computed separately in graph_construction.py
"""
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning,
                        message=".*Channel names are not unique.*")
                        
import json
import re
import numpy as np
import mne
from pathlib import Path
from scipy.signal import butter, sosfiltfilt

mne.set_log_level("WARNING")

# ── Constants ─────────────────────────────────────────────────────────────────

FS          = 256
WIN_S       = 4
WIN_SAMPLES = FS * WIN_S        # 1024
BUFFER_S    = 4 * 3600          # 4h post-seizure exclusion
ART_THRESH  = 500e-6            # 500 µV in Volts — interictal only
FILTER_PAD  = 3 * FS            # 768 samples padding each side

N_CH  = 18
N_SMP = WIN_SAMPLES

COMMON_CHANNELS = [
    "FP1-F7", "F7-T7", "T7-P7", "P7-O1",
    "FP1-F3", "F3-C3", "C3-P3", "P3-O1",
    "FP2-F4", "F4-C4", "C4-P4", "P4-O2",
    "FP2-F8", "F8-T8", "T8-P8", "P8-O2",
    "FZ-CZ",  "CZ-PZ",
]

# Build filter once at module load
_SOS = butter(4, [0.5, 40.0], btype="bandpass", fs=FS, output="sos")


# ── 1. Parse summary file ─────────────────────────────────────────────────────

def parse_summary(summary_path: Path) -> dict:
    """
    Parse chbXX-summary.txt.
    Returns dict: filename → list of (onset_s, offset_s).

    Parser is index-agnostic on Start/End lines to handle CHB-MIT typo:
        'Seizure 2 Start Time: ...'
        'Seizure 1 End Time: ...'   ← wrong index, present in chb09_08
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


# ── 2. Open EDF — no full RAM load ───────────────────────────────────────────

def open_edf(edf_path: Path):
    """
    Open EDF, normalise channel names, pick 18 common channels.
    Returns None if any common channel is missing (file skipped silently).
    """
    raw = mne.io.read_raw_edf(str(edf_path), preload=False, verbose=False)

    raw.rename_channels({ch: ch.upper().strip() for ch in raw.ch_names})

    # CHB-MIT duplicate T8-P8: MNE appends "-0"/"-1".
    # Strip numeric suffix to recover original name for the first occurrence.
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


# ── 3. Filter one window with context padding ─────────────────────────────────

def filter_window(raw, start: int, end: int) -> np.ndarray:
    """
    Read [start-pad, end+pad), apply sosfiltfilt, return centre [start, end).
    Zero-phase — no group delay introduced.
    Returns [N_CH, WIN_SAMPLES] float64.
    """
    n_total   = int(raw.n_times)
    pad_start = max(0, start - FILTER_PAD)
    pad_end   = min(n_total, end + FILTER_PAD)

    segment  = raw.get_data(start=pad_start, stop=pad_end)  # [18, L]
    filtered = sosfiltfilt(_SOS, segment, axis=1)

    offset = start - pad_start
    return filtered[:, offset : offset + WIN_SAMPLES]


# ── 4. Label and buffer arrays ────────────────────────────────────────────────

def build_labels(n_seconds: int, seizure_list: list) -> np.ndarray:
    labels = np.zeros(n_seconds, dtype=np.int8)
    for onset, offset in seizure_list:
        labels[max(0, onset) : min(n_seconds, offset)] = 1
    return labels


def build_buffer_mask(n_seconds: int, seizure_list: list) -> np.ndarray:
    mask = np.zeros(n_seconds, dtype=bool)
    for _, offset in seizure_list:
        mask[offset : min(n_seconds, offset + BUFFER_S)] = True
    return mask


# ── 5. Artifact check (interictal only) ──────────────────────────────────────

def is_artifact(window: np.ndarray) -> bool:
    """True if any sample exceeds ±500 µV. Applied to interictal only."""
    return bool(np.abs(window).max() > ART_THRESH)


# ── 6. Count windows — Pass 1 ─────────────────────────────────────────────────

def count_windows(subject_id: str, raw_dir: Path,
                  seizure_map: dict) -> tuple[int, int, int]:
    """
    Count valid windows without storing data.
    Artifact rejection applied to interictal only — NOT to ictal.
    """
    n_inter    = 0
    n_ictal    = 0
    n_rejected = 0  # interictal artifact rejections only

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
                # Ictal: count all — no artifact rejection
                n_ictal += 1

            elif not win_buffered:
                # Interictal: artifact rejection applies
                start = i * WIN_SAMPLES
                end   = start + WIN_SAMPLES
                window = filter_window(raw, start, end)
                if is_artifact(window):
                    n_rejected += 1
                else:
                    n_inter += 1

        del raw

    return n_inter, n_ictal, n_rejected


# ── 7. Process one subject — two-pass memmap write ────────────────────────────

def process_subject(subject_id: str, raw_dir: Path,
                    processed_dir: Path) -> dict:
    """
    Two-pass strategy:
      Pass 1 — count valid windows (no data stored in RAM)
      Allocate memmap on disk
      Pass 2 — filter + write directly to memmap

    Peak RAM ≈ one window = 18 × 1024 × 8 B ≈ 0.15 MB

    Outputs:
      {subject_id}_interictal.npy   [N, 18, 1024]  float32
      {subject_id}_ictal.npy        [M, 18, 1024]  float32
      {subject_id}_stats.json
    """
    processed_dir.mkdir(parents=True, exist_ok=True)

    summary_path = (raw_dir / "CHB info" / "summary" /
                    f"{subject_id}-summary.txt")
    seizure_map = parse_summary(summary_path)

    # ── Pass 1 ────────────────────────────────────────────────────────────────
    print(f"  [pass 1] counting windows...")
    n_inter, n_ictal, n_rejected = count_windows(
        subject_id, raw_dir, seizure_map)
    print(f"  [pass 1] interictal={n_inter} | ictal={n_ictal} "
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

    # ── Pass 2 ────────────────────────────────────────────────────────────────
    print(f"  [pass 2] writing windows to disk...")
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
            start   = i * WIN_SAMPLES
            end     = start + WIN_SAMPLES
            start_s = i * WIN_S
            end_s   = start_s + WIN_S

            win_label    = int(labels[start_s:end_s].max())
            win_buffered = bool(buffer_mask[start_s:end_s].any())

            if win_label == 1:
                # Ictal: filter and save — no artifact rejection
                if idx_ictal < n_ictal:
                    window = filter_window(raw, start, end)
                    mm_ictal[idx_ictal] = window.astype(np.float32)
                    idx_ictal += 1

            elif not win_buffered:
                # Interictal: filter, artifact check, then save
                window = filter_window(raw, start, end)
                if not is_artifact(window) and idx_inter < n_inter:
                    mm_inter[idx_inter] = window.astype(np.float32)
                    idx_inter += 1

        del raw

    del mm_inter, mm_ictal

    # ── Stats ─────────────────────────────────────────────────────────────────
    stats = {
        "subject_id":   subject_id,
        "n_interictal": n_inter,
        "n_ictal":      n_ictal,
        "n_rejected":   n_rejected,
        "ratio":        round(n_inter / max(n_ictal, 1), 1),
    }
    with open(f"{prefix}_stats.json", "w") as fout:
        json.dump(stats, fout, indent=2)

    print(f"[{subject_id}] interictal={n_inter} | ictal={n_ictal} "
          f"| rejected={n_rejected} | ratio={stats['ratio']}:1")
    return stats


# ── 8. Run all subjects ───────────────────────────────────────────────────────

if __name__ == "__main__":
    RAW_DIR       = Path("F:/Study/Thesis/Dataset/CHB-MIT")
    PROCESSED_DIR = Path("F:/Study/Thesis/Code/data/processed")

    SUBJECTS = [f"chb{i:02d}" for i in range(1, 24)]

    all_stats = []
    for subj in SUBJECTS:
        print(f"\nProcessing {subj}...")
        try:
            stats = process_subject(subj, RAW_DIR, PROCESSED_DIR)
            all_stats.append(stats)
        except Exception as e:
            print(f"  [ERROR] {subj}: {e}")

    print("\n=== PREPROCESSING COMPLETE ===")
    for s in all_stats:
        print(f"{s['subject_id']}: {s['n_interictal']} interictal | "
              f"{s['n_ictal']} ictal | ratio {s['ratio']}:1")