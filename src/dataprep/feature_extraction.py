"""
feature_extraction.py
=====================
Compute 5 spectral band powers per channel for each 4s window.
Output shape: [N_windows, 18, 5]
Bands: Delta (0.5–4), Theta (4–8), Alpha (8–13), Beta (13–30), Gamma (30–60)
"""

import numpy as np
from scipy.signal import welch
from pathlib import Path

FS = 256
BANDS = {
    'delta': (0.5, 4),
    'theta': (4, 8),
    'alpha': (8, 13),
    'beta':  (13, 30),
    'gamma': (30, 60),
}

def compute_band_powers(window: np.ndarray, fs: int = FS) -> np.ndarray:
    """
    window: [18, 1024]
    returns: [18, 5] log-normalized band powers.
    Log transform compresses dynamic range and makes features
    compatible in scale with adjacency matrix values (0.1-0.5).
    """
    n_channels = window.shape[0]
    features = np.zeros((n_channels, len(BANDS)), dtype=np.float32)

    freqs, psd = welch(window, fs=fs, nperseg=fs*2, noverlap=fs, axis=1)

    for i, (band, (low, high)) in enumerate(BANDS.items()):
        idx = np.where((freqs >= low) & (freqs <= high))[0]
        raw_power = np.mean(psd[:, idx], axis=1)
        # Log transform: log(power + epsilon) to avoid log(0)
        features[:, i] = np.log(raw_power + 1e-30)

    # Z-score normalize per window across channels and bands
    mean = features.mean()
    std  = features.std() + 1e-8
    features = (features - mean) / std

    return features


def process_subject(subject_id: str, processed_dir: Path):
    inter_path = processed_dir / f"{subject_id}_interictal.npy"
    ictal_path = processed_dir / f"{subject_id}_ictal.npy"

    if not inter_path.exists():
        print(f"Missing {inter_path} – skipping {subject_id}")
        return

    for label, path in [('interictal', inter_path), ('ictal', ictal_path)]:
        if not path.exists():
            continue

        windows = np.load(path, mmap_mode='r')
        n_windows = windows.shape[0]
        out_path = processed_dir / f"{subject_id}_{label}_features.npy"

        print(f"  [{subject_id}] {label} features: {n_windows} windows...")
        mm = np.lib.format.open_memmap(
            str(out_path), mode='w+', dtype=np.float32,
            shape=(n_windows, 18, 5))

        for i in range(n_windows):
            mm[i] = compute_band_powers(windows[i].astype(np.float64))
            if (i + 1) % 2000 == 0:
                print(f"    {i+1}/{n_windows}", end='\r')
        del mm
        print(f"  Saved {out_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--subjects", nargs="+",
        default=[f"chb{i:02d}" for i in range(1, 24)],
        help="Subject IDs to process. Default: all 23."
    )
    args = parser.parse_args()

    PROCESSED_DIR = Path("F:/Study/Thesis/Code/data/processed")

    for subj in args.subjects:
        print(f"\nProcessing {subj}...")
        process_subject(subj, PROCESSED_DIR)

    print("\n=== FEATURE EXTRACTION COMPLETE ===")