# src/compute_gamma_aec.py
"""
P2.2: Compute gamma AEC (30-60 Hz) anomaly scores for all subjects.

Gamma band amplitude envelope correlation increases during seizures in 7/8
subjects including chb06 (where wPLI/AEC reconstruction is inverted).
HFO-related gamma amplitude coupling provides complementary signal to phase-
based connectivity.

Outputs per subject:
  gamma_aec_{subj}_inter.npy  [N_inter] float32 — z-normalized scores
  gamma_aec_{subj}_ictal.npy  [N_ictal] float32 — z-normalized scores

No GPU needed. All computation from existing raw windows.
"""
import numpy as np
from scipy.signal import butter, filtfilt, hilbert
from pathlib import Path
import argparse

FS         = 256
WIN_SAMP   = 1024
GAMMA_LOW  = 30.0
GAMMA_HIGH = 60.0
KEEP_RATIO = 0.20    # top-20% AEC pairs for score
BATCH_SIZE = 256     # windows per batch for memory efficiency

ALL_SUBJS = [f"chb{i:02d}" for i in range(1, 24)]


def make_gamma_filter(fs=FS, order=4):
    nyq = fs / 2.0
    b, a = butter(order, [GAMMA_LOW / nyq, GAMMA_HIGH / nyq], btype='band')
    return b, a


def compute_gamma_scores_batch(windows: np.ndarray,
                                b, a,
                                keep_ratio: float = KEEP_RATIO) -> np.ndarray:
    """
    Vectorized gamma AEC scoring for a batch of windows.

    Parameters
    ----------
    windows : [N, 18, 1024] float32
    b, a    : IIR filter coefficients

    Returns
    -------
    scores : [N] float32 — mean of top-k% gamma AEC values
    """
    N, n_ch, T = windows.shape
    k = max(1, int(n_ch * (n_ch - 1) // 2 * keep_ratio))  # top-k of 153 pairs

    # Bandpass filter: reshape to [N*18, T] for filtfilt
    flat = windows.reshape(N * n_ch, T)
    filt = filtfilt(b, a, flat, axis=-1).reshape(N, n_ch, T)

    # Amplitude envelope via Hilbert, log-transform
    env = np.abs(hilbert(filt, axis=-1))          # [N, 18, T]
    env = np.log(env + 1e-10)

    # Zero-mean, unit-std per channel per window (for Pearson)
    mu  = env.mean(axis=-1, keepdims=True)        # [N, 18, 1]
    sig = env.std(axis=-1, keepdims=True) + 1e-10
    env_n = (env - mu) / sig                      # [N, 18, T]

    # Pearson correlation matrix via einsum: [N, 18, 18]
    corr = np.einsum('nit,njt->nij', env_n, env_n) / T

    # Upper triangle values: [N, 153]
    triu_r, triu_c = np.triu_indices(n_ch, k=1)
    triu_vals = corr[:, triu_r, triu_c]           # [N, 153]
    triu_vals = np.nan_to_num(triu_vals, nan=0.0)

    # Mean of top-k% per window
    scores = np.sort(triu_vals, axis=1)[:, -k:].mean(axis=1)  # [N]
    return scores.astype(np.float32)


def process_subject(subj: str, data_dir: Path, out_dir: Path):
    b, a = make_gamma_filter()

    for split in ['interictal', 'ictal']:
        raw_path = data_dir / f"{subj}_{split}.npy"
        out_path = out_dir  / f"gamma_aec_{subj}_{split[:5]}.npy"

        if not raw_path.exists():
            print(f"  [{subj}] {split}: raw file not found — skip")
            continue

        windows = np.load(str(raw_path), mmap_mode='r')
        N = len(windows)
        raw_scores = np.zeros(N, dtype=np.float32)

        for s in range(0, N, BATCH_SIZE):
            e = min(s + BATCH_SIZE, N)
            batch = windows[s:e].astype(np.float32)
            raw_scores[s:e] = compute_gamma_scores_batch(batch, b, a)

        # Z-normalize using interictal statistics
        # (computed from interictal, applied to both)
        if split == 'interictal':
            inter_raw = raw_scores.copy()
            med = np.median(inter_raw)
            mad = np.median(np.abs(inter_raw - med)) + 1e-9
            z_scores = (inter_raw - med) / mad
            # Save calibration stats for ictal normalization
            _med, _mad = med, mad
        else:
            z_scores = (raw_scores - _med) / _mad

        np.save(str(out_path), z_scores)
        mzi = float(np.median(z_scores)) if split == 'ictal' else float(np.median(z_scores))
        direction = "correct ↑" if (split == 'ictal' and mzi > 0) else \
                    ("INVERTED ↓" if split == 'ictal' else "")
        print(f"  [{subj}] {split:10s}: N={N:6d}  mzi={mzi:+.4f}  {direction}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', default='data/processed')
    parser.add_argument('--out_dir',  default='data/processed')
    parser.add_argument('--subjs',    nargs='+', default=ALL_SUBJS)
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    out_dir  = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Computing gamma AEC ({GAMMA_LOW}-{GAMMA_HIGH} Hz) for {len(args.subjs)} subjects")
    print(f"Data: {data_dir}  →  Output: {out_dir}\n")

    for subj in args.subjs:
        print(f"{subj}:")
        process_subject(subj, data_dir, out_dir)