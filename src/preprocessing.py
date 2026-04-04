import re
import numpy as np
import mne
from pathlib import Path
from graph_construction import build_adjacency

mne.set_log_level("WARNING")

FS = 256
WIN_S = 4
WIN_SAMPLES = FS * WIN_S          # 1024
BUFFER_S = 4 * 3600               # 4 hours post-seizure
ARTIFACT_THRESHOLD_UV = 500e-6    # 500 µV in Volts (MNE uses Volts)

# 18 common channels across all CHB-MIT subjects
COMMON_CHANNELS = [
    "FP1-F7", "F7-T7", "T7-P7", "P7-O1",
    "FP1-F3", "F3-C3", "C3-P3", "P3-O1",
    "FP2-F4", "F4-C4", "C4-P4", "P4-O2",
    "FP2-F8", "F8-T8", "T8-P8", "P8-O2",
    "FZ-CZ",  "CZ-PZ"
]

N_CH  = 18
N_SMP = 1024   # samples per window


# ── 1. Parse summary file ─────────────────────────────────────────────────────

def parse_summary(summary_path):
    """
    Parse chbXX-summary.txt.
    Returns: dict {filename: [(onset_s, offset_s), ...]}
    """
    seizures = {}
    current_file = None
    onset = None

    with open(summary_path, "r") as f:
        for line in f:
            line = line.strip()

            if line.startswith("File Name:"):
                current_file = line.split(":")[1].strip()
                seizures[current_file] = []

            elif "Seizure" in line and "Start Time:" in line:
                match = re.search(r"(\d+)\s*seconds", line)
                if match:
                    onset = int(match.group(1))

            elif "Seizure" in line and "End Time:" in line:
                match = re.search(r"(\d+)\s*seconds", line)
                if match and onset is not None and current_file is not None:
                    offset = int(match.group(1))
                    seizures[current_file].append((onset, offset))
                    onset = None

    return seizures


# ── 2. Open EDF — NO full load into RAM ──────────────────────────────────────

def open_edf(edf_path):
    """
    Open EDF and pick 18 channels WITHOUT loading data into RAM.
    Data is read per-window via raw.get_data(start, stop).
    """
    raw = mne.io.read_raw_edf(edf_path, preload=False, verbose=False)

    raw.rename_channels({ch: ch.upper().strip() for ch in raw.ch_names})

    # Handle CHB-MIT duplicate T8-P8
    rename_map = {}
    seen = {}
    for ch in raw.ch_names:
        base = ch.rsplit('-', 1)
        if len(base) == 2 and base[1].isdigit():
            original = base[0]
            if original not in seen:
                seen[original] = ch
                rename_map[ch] = original
    if rename_map:
        raw.rename_channels(rename_map)

    available = set(raw.ch_names)
    missing = set(COMMON_CHANNELS) - available
    if missing:
        print(f"  [SKIP] {Path(edf_path).name} missing channels: {missing}")
        return None

    raw.pick_channels(COMMON_CHANNELS)
    raw.reorder_channels(COMMON_CHANNELS)
    return raw


# ── 3. Label and buffer mask ──────────────────────────────────────────────────

def build_labels(n_seconds, seizure_list):
    labels = np.zeros(n_seconds, dtype=np.int8)
    for onset, offset in seizure_list:
        onset  = max(0, onset)
        offset = min(n_seconds, offset)
        labels[onset:offset] = 1
    return labels


def build_buffer_mask(n_seconds, seizure_list):
    mask = np.zeros(n_seconds, dtype=bool)
    for _, offset in seizure_list:
        buffer_end = min(n_seconds, offset + BUFFER_S)
        mask[offset:buffer_end] = True
    return mask


# ── 4. Artifact rejection ─────────────────────────────────────────────────────

def is_artifact(window):
    return np.abs(window).max() > ARTIFACT_THRESHOLD_UV


# ── 5. Count windows (pass 1) ─────────────────────────────────────────────────

def count_windows(subject_id, raw_dir, seizure_map):
    """
    First pass: count how many interictal and ictal windows will be saved.
    Required to pre-allocate memmap arrays on disk before writing.
    Does NOT store any signal data.
    """
    raw_dir   = Path(raw_dir)
    n_inter   = 0
    n_ictal   = 0
    n_rejected = 0

    edf_files = sorted((raw_dir / subject_id).glob("*.edf"))

    for edf_path in edf_files:
        fname        = edf_path.name
        seizure_list = seizure_map.get(fname, [])

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

            window = raw.get_data(start=start, stop=end)

            if is_artifact(window):
                n_rejected += 1
                continue

            window_label    = labels[start_s:end_s].max()
            window_buffered = buffer_mask[start_s:end_s].any()

            if window_label == 1:
                n_ictal += 1
            elif not window_buffered:
                n_inter += 1

        del raw

    return n_inter, n_ictal, n_rejected


# ── 6. Process one subject (two-pass, memmap write) ───────────────────────────

def process_subject(subject_id, raw_dir, processed_dir,
                    alpha=0.5, top_k_percent=30):
    """
    Full preprocessing pipeline for one CHB-MIT subject.

    Two-pass strategy to avoid large RAM spike:
      Pass 1 — count_windows(): count N and M without storing data
      Allocate memmap files on disk sized exactly [N,18,1024] and [N,18,18]
      Pass 2 — write each window directly into the memmap file

    Peak RAM at any point = one 4s window = 18 x 1024 x 8 bytes = ~0.15 MB.
    No large intermediate list is held in memory.

    Outputs (saved to processed_dir):
      {subject_id}_interictal_windows.npy  [N, 18, 1024]  float32
      {subject_id}_interictal_adjs.npy     [N, 18, 18]    float32
      {subject_id}_ictal_windows.npy       [M, 18, 1024]  float32
      {subject_id}_ictal_adjs.npy          [M, 18, 18]    float32
      {subject_id}_metadata.npy            dict
    """
    raw_dir       = Path(raw_dir)
    processed_dir = Path(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)

    summary_path = (raw_dir / "CHB info" / "summary" /
                    f"{subject_id}-summary.txt")
    seizure_map = parse_summary(summary_path)

    # ── Pass 1: count windows ─────────────────────────────────────────────────
    print(f"  [pass 1] counting windows...")
    n_inter, n_ictal, n_rejected = count_windows(subject_id, raw_dir, seizure_map)
    print(f"  [pass 1] interictal={n_inter} | ictal={n_ictal} | rejected={n_rejected}")

    prefix = processed_dir / subject_id

    # ── Allocate memmap files on disk ─────────────────────────────────────────
    # np.lib.format.open_memmap creates a proper .npy file with header
    mm_iw = np.lib.format.open_memmap(
        f"{prefix}_interictal_windows.npy", mode='w+',
        dtype=np.float32, shape=(n_inter, N_CH, N_SMP))
    mm_ia = np.lib.format.open_memmap(
        f"{prefix}_interictal_adjs.npy", mode='w+',
        dtype=np.float32, shape=(n_inter, N_CH, N_CH))
    mm_cw = np.lib.format.open_memmap(
        f"{prefix}_ictal_windows.npy", mode='w+',
        dtype=np.float32, shape=(max(n_ictal, 1), N_CH, N_SMP))
    mm_ca = np.lib.format.open_memmap(
        f"{prefix}_ictal_adjs.npy", mode='w+',
        dtype=np.float32, shape=(max(n_ictal, 1), N_CH, N_CH))

    # ── Pass 2: write windows directly to disk ────────────────────────────────
    print(f"  [pass 2] writing windows to disk...")
    idx_inter = 0
    idx_ictal = 0
    edf_files = sorted((raw_dir / subject_id).glob("*.edf"))

    for edf_path in edf_files:
        fname        = edf_path.name
        seizure_list = seizure_map.get(fname, [])

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

            window = raw.get_data(start=start, stop=end)  # [18, 1024] float64

            if is_artifact(window):
                continue

            window_label    = labels[start_s:end_s].max()
            window_buffered = buffer_mask[start_s:end_s].any()

            A = build_adjacency(window, alpha=alpha,
                                top_k_percent=top_k_percent)

            if window_label == 1 and idx_ictal < n_ictal:
                mm_cw[idx_ictal] = window.astype(np.float32)
                mm_ca[idx_ictal] = A.astype(np.float32)
                idx_ictal += 1
            elif not window_buffered and idx_inter < n_inter:
                mm_iw[idx_inter] = window.astype(np.float32)
                mm_ia[idx_inter] = A.astype(np.float32)
                idx_inter += 1

        del raw

    # Flush memmap to disk
    del mm_iw, mm_ia, mm_cw, mm_ca

    # ── Save metadata ─────────────────────────────────────────────────────────
    metadata = {
        "subject_id":          subject_id,
        "n_interictal":        n_inter,
        "n_ictal":             n_ictal,
        "n_artifact_rejected": n_rejected,
        "imbalance_ratio":     n_inter / max(n_ictal, 1),
    }
    np.save(f"{prefix}_metadata.npy", metadata)

    print(f"[{subject_id}] interictal={n_inter} | "
          f"ictal={n_ictal} | rejected={n_rejected}")
    return metadata


# ── 7. Run all subjects ───────────────────────────────────────────────────────

if __name__ == "__main__":
    RAW_DIR       = "F:/Study/Thesis/Dataset/CHB-MIT"
    PROCESSED_DIR = "F:/Study/Thesis/Code/data/processed"

    SUBJECTS = [f"chb{i:02d}" for i in range(1, 24)]

    all_metadata = []
    for subj in SUBJECTS:
        print(f"\nProcessing {subj}...")
        try:
            meta = process_subject(subj, RAW_DIR, PROCESSED_DIR)
            all_metadata.append(meta)
        except Exception as e:
            print(f"  [ERROR] {subj}: {e}")

    print("\n=== PREPROCESSING COMPLETE ===")
    for m in all_metadata:
        print(f"{m['subject_id']}: {m['n_interictal']} interictal | "
              f"{m['n_ictal']} ictal | ratio {m['imbalance_ratio']:.1f}:1")