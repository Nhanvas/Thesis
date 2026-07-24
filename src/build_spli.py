# src/build_spli.py
"""
Build signed PLI adjacency matrices from raw EEG windows.

sPLI[i,j] = E[Im(C_ij)] / E[|Im(C_ij)|]
          ∈ [-1, 1], antisymmetric (sPLI[i,j] = -sPLI[j,i])

Key difference from wPLI: no absolute value on numerator.
Sign captures direction of phase lag between electrode pairs.
"""
import numpy as np
from pathlib import Path
from scipy.signal import welch
import argparse

FS = 256
WIN_SAMP = 1024  # 4s × 256Hz
N_CH = 18
KEEP_RATIO = 0.20
N_EDGES = 18 * 17 // 2  # 153 undirected pairs

def compute_spli_window(window: np.ndarray) -> np.ndarray:
    """
    Compute 18×18 signed PLI matrix from one 4s window.
    window: [18, 1024] float32, already z-scored
    Returns: [18, 18] float32, antisymmetric, values in [-1, 1]
    """
    n_ch = window.shape[0]
    # FFT for all channels at once
    fft_all = np.fft.rfft(window, axis=1)  # [18, 513]
    # Keep only 0.5–60 Hz bins
    freqs = np.fft.rfftfreq(WIN_SAMP, d=1.0/FS)
    mask = (freqs >= 0.5) & (freqs <= 60.0)
    fft_all = fft_all[:, mask]  # [18, ~240]
    
    A = np.zeros((n_ch, n_ch), dtype=np.float32)
    for i in range(n_ch):
        for j in range(i + 1, n_ch):
            C_ij = fft_all[i] * np.conj(fft_all[j])
            im_C = np.imag(C_ij)
            denom = np.mean(np.abs(im_C))
            if denom < 1e-10:
                val = 0.0
            else:
                val = float(np.mean(im_C) / denom)  # sPLI — NO abs on numerator
            A[i, j] =  val
            A[j, i] = -val  # antisymmetric
    return A

def apply_topk_signed(A: np.ndarray, keep_ratio: float = KEEP_RATIO) -> np.ndarray:
    """
    Keep top-k% edges by |sPLI| magnitude. Preserve sign.
    """
    k = max(1, int(N_EDGES * keep_ratio))
    triu_idx = np.triu_indices(18, k=1)
    magnitudes = np.abs(A[triu_idx])
    if magnitudes.max() < 1e-10:
        return np.zeros_like(A)
    cutoff = np.sort(magnitudes)[-k]
    mask = np.abs(A) >= cutoff
    return (A * mask).astype(np.float32)

def build_spli_for_subject(raw_path: str, out_path: str):
    """Build sPLI adjacency for all windows in one raw .npy file."""
    windows = np.load(raw_path, mmap_mode='r')  # [N, 18, 1024]
    N = len(windows)
    adjs = np.zeros((N, 18, 18), dtype=np.float32)
    for i in range(N):
        A = compute_spli_window(windows[i])
        adjs[i] = apply_topk_signed(A)
        if (i + 1) % 500 == 0:
            print(f"  {i+1}/{N}", end="\r")
    np.save(out_path, adjs)
    print(f"  Saved {N} windows → {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--subj", required=True)
    parser.add_argument("--data_dir", default="data/processed")
    parser.add_argument("--out_dir",  default="data/processed")
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    out_dir  = Path(args.out_dir)
    
    for split in ["interictal", "ictal"]:
        raw_path = str(data_dir / f"{args.subj}_{split}.npy")
        out_path = str(out_dir  / f"{args.subj}_{split}_adjs_spli_topk20.npy")
        if not Path(raw_path).exists():
            print(f"SKIP {raw_path} (not found)")
            continue
        print(f"\n{args.subj} {split}...")
        build_spli_for_subject(raw_path, out_path)