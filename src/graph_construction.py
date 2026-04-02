import numpy as np
from scipy.signal import hilbert


def compute_wpli(eeg_window, fs=256):
    """
    Weighted Phase Lag Index — Eq (2).
    wPLI_xy = |mean(imag(C_xy))| / mean(|imag(C_xy)|)
    Resistant to zero-lag volume conduction artifacts.

    Input:  eeg_window [18, 1024]
    Output: wpli_matrix [18, 18]
    """
    n_channels, n_samples = eeg_window.shape
    wpli = np.zeros((n_channels, n_channels))

    # Compute cross-spectrum via FFT
    fft_data = np.fft.fft(eeg_window, axis=1)

    for i in range(n_channels):
        for j in range(i + 1, n_channels):
            cross = fft_data[i] * np.conj(fft_data[j])
            imag_cross = np.imag(cross)
            numerator = np.abs(np.mean(imag_cross))
            denominator = np.mean(np.abs(imag_cross)) + 1e-8
            val = numerator / denominator
            wpli[i, j] = val
            wpli[j, i] = val

    return wpli


def compute_aec(eeg_window):
    """
    Amplitude Envelope Correlation — Eq (3).
    AEC_xy = corr(|hilbert(x)|, |hilbert(y)|)

    Input:  eeg_window [18, 1024]
    Output: aec_matrix [18, 18]
    """
    n_channels = eeg_window.shape[0]
    envelopes = np.abs(hilbert(eeg_window, axis=1))  # [18, 1024]
    aec = np.corrcoef(envelopes)                      # [18, 18]
    np.fill_diagonal(aec, 0)
    aec = np.abs(aec)  # ensure non-negative
    return aec


def combine_adjacency(wpli, aec, alpha=0.5):
    """
    Combined adjacency — Eq (4).
    A = alpha * A_wPLI + (1 - alpha) * A_AEC
    """
    return alpha * wpli + (1 - alpha) * aec


def apply_top_k_threshold(A, top_k_percent=30):
    """
    Retain only top-k% strongest edges. Set rest to 0.
    Ensures consistent graph density across windows.
    """
    n = A.shape[0]
    n_edges = int(n * (n - 1) / 2 * top_k_percent / 100)

    # Get upper triangle values
    triu_idx = np.triu_indices(n, k=1)
    values = A[triu_idx]

    # Find threshold
    if n_edges == 0:
        return np.zeros_like(A)
    threshold = np.sort(values)[-n_edges]

    # Apply
    A_thresh = np.where(A >= threshold, A, 0.0)
    np.fill_diagonal(A_thresh, 0)
    return A_thresh


def build_adjacency(eeg_window, alpha=0.5, top_k_percent=30, fs=256):
    """
    Full graph construction pipeline for one 4s window.

    Input:  eeg_window [18, 1024]
    Output: A [18, 18] — thresholded adjacency matrix
    """
    wpli = compute_wpli(eeg_window, fs=fs)
    aec = compute_aec(eeg_window)
    A = combine_adjacency(wpli, aec, alpha=alpha)
    A = apply_top_k_threshold(A, top_k_percent=top_k_percent)
    return A.astype(np.float32)