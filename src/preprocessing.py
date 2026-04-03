import os
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


# ── 1. Parse summary file ─────────────────────────────────────────────────────

def parse_summary(summary_path):
    """
    Parse chbXX-summary.txt.
    Returns: dict {filename: [(onset_s, offset_s), ...]}
    """
    seizures = {}
    current_file = None
    n_seizures = 0
    seizure_count = 0

    with open(summary_path, "r") as f:
        for line in f:
            line = line.strip()

            if line.startswith("File Name:"):
                current_file = line.split(":")[1].strip()
                seizures[current_file] = []
                seizure_count = 0

            elif line.startswith("Number of Seizures in File:"):
                n_seizures = int(line.split(":")[1].strip())

            elif "Seizure" in line and "Start Time:" in line:
                onset = int(re.search(r"(\d+)\s*seconds", line).group(1))
                seizure_count += 1

            elif "Seizure" in line and "End Time:" in line:
                offset = int(re.search(r"(\d+)\s*seconds", line).group(1))
                if current_file is not None:
                    seizures[current_file].append((onset, offset))

    return seizures


# ── 2. Load single EDF file ───────────────────────────────────────────────────

def load_edf(edf_path):
    """
    Load EDF, pick 18 common channels.
    Handles duplicate channel names (e.g. T8-P8 appears twice in CHB-MIT).
    """
    raw = mne.io.read_raw_edf(edf_path, preload=True, verbose=False)

    # Normalize channel names to uppercase
    raw.rename_channels({ch: ch.upper().strip() for ch in raw.ch_names})

    # Handle duplicates: MNE renames T8-P8 → T8-P8-0, T8-P8-1
    # Keep first occurrence, rename back to original
    rename_map = {}
    seen = {}
    for ch in raw.ch_names:
        # Check if this is a MNE-generated duplicate (ends with -0, -1, etc.)
        base = ch.rsplit('-', 1)
        if len(base) == 2 and base[1].isdigit():
            original = base[0]
            if original not in seen:
                seen[original] = ch
                rename_map[ch] = original  # rename T8-P8-0 → T8-P8
            # T8-P8-1 and beyond: leave as is, will be dropped

    if rename_map:
        raw.rename_channels(rename_map)

    available = set(raw.ch_names)
    missing = set(COMMON_CHANNELS) - available
    if missing:
        print(f"  [SKIP] {Path(edf_path).name} missing channels: {missing}")
        return None

    raw.pick_channels(COMMON_CHANNELS)
    raw.reorder_channels(COMMON_CHANNELS)

    # Bandpass 0.5–40 Hz
    raw.filter(0.5, 40.0, fir_design="firwin")

    return raw


# ── 3. Build per-file label arrays ───────────────────────────────────────────

def build_labels(n_seconds, seizure_list):
    """
    Binary label array at 1s resolution.
    1 = ictal, 0 = interictal.
    """
    labels = np.zeros(n_seconds, dtype=np.int8)
    for onset, offset in seizure_list:
        onset = max(0, onset)
        offset = min(n_seconds, offset)
        labels[onset:offset] = 1
    return labels


def build_buffer_mask(n_seconds, seizure_list):
    """
    True where window is within 4h after a seizure end.
    These windows are excluded from interictal training set.
    """
    mask = np.zeros(n_seconds, dtype=bool)
    for _, offset in seizure_list:
        buffer_end = min(n_seconds, offset + BUFFER_S)
        mask[offset:buffer_end] = True
    return mask


# ── 4. Artifact rejection ─────────────────────────────────────────────────────

def is_artifact(window):
    """
    window: [18, 1024] in Volts.
    Reject if any channel exceeds ±500 µV.
    """
    return np.abs(window).max() > ARTIFACT_THRESHOLD_UV


# ── 5. Process one subject ────────────────────────────────────────────────────

def process_subject(subject_id, raw_dir, processed_dir,
                    alpha=0.5, top_k_percent=30):
    """
    Full preprocessing pipeline for one CHB-MIT subject.

    Outputs (saved to processed_dir):
      {subject_id}_interictal_windows.npy  [N, 18, 1024]
      {subject_id}_interictal_adjs.npy     [N, 18, 18]
      {subject_id}_ictal_windows.npy       [M, 18, 1024]
      {subject_id}_ictal_adjs.npy          [M, 18, 18]
      {subject_id}_metadata.npy            dict saved as .npy
    """
    raw_dir = Path(raw_dir)
    processed_dir = Path(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)

    summary_path = raw_dir / "CHB info" / "summary" / f"{subject_id}-summary.txt"
    seizure_map = parse_summary(summary_path)

    interictal_windows, interictal_adjs = [], []
    ictal_windows, ictal_adjs = [], []
    n_artifact_rejected = 0

    edf_files = sorted((raw_dir / subject_id).glob("*.edf"))

    for edf_path in edf_files:
        fname = edf_path.name
        seizure_list = seizure_map.get(fname, [])

        raw = load_edf(edf_path)
        if raw is None:
            continue

        data = raw.get_data()           # [18, n_samples] in Volts
        n_samples = data.shape[1]
        n_seconds = n_samples // FS

        labels = build_labels(n_seconds, seizure_list)
        buffer_mask = build_buffer_mask(n_seconds, seizure_list)

        n_windows = n_samples // WIN_SAMPLES

        for i in range(n_windows):
            start = i * WIN_SAMPLES
            end = start + WIN_SAMPLES
            start_s = i * WIN_S
            end_s = start_s + WIN_S

            window = data[:, start:end]  # [18, 1024]

            # Artifact rejection
            if is_artifact(window):
                n_artifact_rejected += 1
                continue

            window_label = labels[start_s:end_s].max()
            window_buffered = buffer_mask[start_s:end_s].any()

            # Build graph
            A = build_adjacency(window, alpha=alpha, top_k_percent=top_k_percent)

            if window_label == 1:
                ictal_windows.append(window)
                ictal_adjs.append(A)
            elif not window_buffered:
                interictal_windows.append(window)
                interictal_adjs.append(A)

    # Save
    prefix = processed_dir / subject_id
    np.save(f"{prefix}_interictal_windows.npy", np.array(interictal_windows, dtype=np.float32))
    np.save(f"{prefix}_interictal_adjs.npy",   np.array(interictal_adjs,   dtype=np.float32))
    np.save(f"{prefix}_ictal_windows.npy",      np.array(ictal_windows,     dtype=np.float32))
    np.save(f"{prefix}_ictal_adjs.npy",         np.array(ictal_adjs,        dtype=np.float32))

    metadata = {
        "subject_id":          subject_id,
        "n_interictal":        len(interictal_windows),
        "n_ictal":             len(ictal_windows),
        "n_artifact_rejected": n_artifact_rejected,
        "imbalance_ratio":     len(interictal_windows) / max(len(ictal_windows), 1),
    }
    np.save(f"{prefix}_metadata.npy", metadata)

    print(f"[{subject_id}] interictal={len(interictal_windows)} | "
          f"ictal={len(ictal_windows)} | rejected={n_artifact_rejected}")
    return metadata


# ── 6. Run all subjects ───────────────────────────────────────────────────────

if __name__ == "__main__":
    RAW_DIR = "F:/Study/Thesis/Dataset/CHB-MIT"          # Change to the actual path
    PROCESSED_DIR = "../data/processed"

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