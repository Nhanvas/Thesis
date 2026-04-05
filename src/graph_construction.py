"""
graph_construction.py
=====================
Graph construction pipeline for one 4s EEG window.

Equations implemented (thesis §2.2):
  Eq (2): wPLI_xy = |mean(imag(C_xy))| / mean(|imag(C_xy)|)
  Eq (3): AEC_xy  = corr(|hilbert(x)|, |hilbert(y)|)
  Eq (4): A = alpha * A_wPLI + (1 - alpha) * A_AEC

Design notes:
  - wPLI uses rfft (positive frequencies only) to avoid cancellation
    from symmetric negative-frequency bins in real signals
  - AEC uses broadband envelope (signal already bandpass filtered
    at 0.5-40Hz in preprocessing.py)
  - Both metrics are naturally in [0, 1] — no additional normalisation needed
  - Top-k% threshold retains strongest edges, ensuring consistent
    graph density across windows regardless of overall connectivity level
"""

import numpy as np
from scipy.signal import hilbert


# ── Eq (2): wPLI ──────────────────────────────────────────────────────────────

def compute_wpli(eeg_window: np.ndarray, fs: int = 256) -> np.ndarray:
    """
    Weighted Phase Lag Index for one window.

    Uses rfft (positive frequencies only). For real signals,
    negative-frequency bins are complex conjugates of positive ones,
    so their imaginary parts cancel in the wPLI numerator if included.

    Input:  eeg_window [18, 1024]
    Output: wpli [18, 18], values in [0, 1]
    """
    n_channels = eeg_window.shape[0]
    wpli = np.zeros((n_channels, n_channels), dtype=np.float64)

    # rfft: positive frequencies only → [18, 513]
    fft_data = np.fft.rfft(eeg_window, axis=1)

    for i in range(n_channels):
        for j in range(i + 1, n_channels):
            cross      = fft_data[i] * np.conj(fft_data[j])
            imag_cross = np.imag(cross)
            numerator   = np.abs(np.mean(imag_cross))
            denominator = np.mean(np.abs(imag_cross)) + 1e-8
            val = numerator / denominator
            wpli[i, j] = val
            wpli[j, i] = val

    return wpli


# ── Eq (3): AEC ───────────────────────────────────────────────────────────────

def compute_aec(eeg_window: np.ndarray) -> np.ndarray:
    """
    Amplitude Envelope Correlation for one window.

    Input:  eeg_window [18, 1024]
    Output: aec [18, 18], values in [0, 1]
    """
    envelopes = np.abs(hilbert(eeg_window, axis=1))  # [18, 1024]

    # corrcoef handles NaN-safe computation; abs ensures non-negative
    aec = np.corrcoef(envelopes)                      # [18, 18]
    np.fill_diagonal(aec, 0.0)
    aec = np.abs(aec)

    return aec


# ── Eq (4): Combined adjacency ────────────────────────────────────────────────

def combine_adjacency(wpli: np.ndarray, aec: np.ndarray,
                      alpha: float = 0.5) -> np.ndarray:
    """A = alpha * A_wPLI + (1 - alpha) * A_AEC"""
    return alpha * wpli + (1 - alpha) * aec


# ── Top-k% threshold ──────────────────────────────────────────────────────────

def apply_top_k_threshold(A: np.ndarray, top_k_percent: float = 30) -> np.ndarray:
    """
    Retain only the top-k% strongest edges (upper triangle).
    Ensures consistent graph density across all windows.
    """
    n = A.shape[0]
    n_upper = n * (n - 1) // 2
    n_keep  = max(1, int(n_upper * top_k_percent / 100))

    triu_idx = np.triu_indices(n, k=1)
    values   = A[triu_idx]

    # Threshold = value at the n_keep-th largest position
    threshold = np.partition(values, -n_keep)[-n_keep]

    A_thresh = np.where(A >= threshold, A, 0.0)
    np.fill_diagonal(A_thresh, 0.0)
    return A_thresh


# ── Full pipeline for one window ──────────────────────────────────────────────

def build_adjacency(eeg_window: np.ndarray,
                    alpha: float = 0.5,
                    top_k_percent: float = 30,
                    fs: int = 256) -> np.ndarray:
    """
    Full graph construction for one 4s EEG window.

    Input:  eeg_window [18, 1024]  float32 or float64
    Output: A [18, 18]             float32, thresholded adjacency
    """
    wpli = compute_wpli(eeg_window.astype(np.float64), fs=fs)
    aec  = compute_aec(eeg_window.astype(np.float64))
    A    = combine_adjacency(wpli, aec, alpha=alpha)
    A    = apply_top_k_threshold(A, top_k_percent=top_k_percent)
    return A.astype(np.float32)