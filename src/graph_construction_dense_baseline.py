"""
graph_construction.py
=====================
Graph construction pipeline for one 4s EEG window.
CAR applied before connectivity computation.

Equations implemented (thesis §2.2):
  Eq (2): wPLI_xy = |mean(imag(C_xy))| / mean(|imag(C_xy)|)
  Eq (3): AEC_xy  = corr(|hilbert(x)|, |hilbert(y)|)
  Eq (4): A = alpha * A_wPLI + (1 - alpha) * A_AEC

Default configuration (E_main):
  alpha = 0.5 — combined wPLI + AEC with equal weight.

Band-specific wPLI (ablation experiment):
  freq_low / freq_high parameters restrict wPLI computation to a
  specific frequency band (e.g. theta 4-8 Hz, alpha 8-13 Hz).
  AEC is always computed broadband (envelope is wideband by nature).
  When freq_low / freq_high are both None, broadband FFT is used
  (original E_main behaviour — fully backward compatible).

Why wPLI:
  Measures phase-based coupling using only the imaginary component of
  the cross-spectrum, suppressing zero-lag volume conduction artifacts
  (Vinck et al. 2011). During seizures, ictal activity propagates with
  lagged phase synchrony from the seizure focus to neighbouring
  electrodes.

Why AEC:
  Measures amplitude-based coupling between channel pairs. Complements
  wPLI: wPLI captures phase coupling, AEC captures amplitude coupling.
  Both types of coupling change during seizures. Excluding AEC a priori
  discards potentially useful signal without model-level evidence.

Ablation (wPLI-only vs combined):
  Will be run as a separate experiment after E_main results are
  reviewed with mentor. alpha is passed as a parameter so the same
  pipeline supports both runs.

Fixed threshold vs top-k%:
  Top-k% forces identical edge counts across all windows, eliminating
  the absolute connectivity strength difference between ictal and
  interictal states. Fixed threshold 0.05 preserves this difference.
"""

import numpy as np
from scipy.signal import hilbert

DEFAULT_ALPHA   = 0.5    # combined wPLI + AEC — E_main default
FIXED_THRESHOLD = 0.05

# Available frequency bands for band-specific wPLI ablation
BAND_RANGES = {
    "broadband": (None,  None),
    "theta":     (4.0,   8.0),
    "alpha":     (8.0,  13.0),
    "beta":      (13.0, 30.0),
    "gamma":     (30.0, 60.0),
}


def apply_car(eeg_window: np.ndarray) -> np.ndarray:
    """
    Common Average Reference: subtract mean across channels at each time point.
    Suppresses common-mode noise and reduces volume conduction zero-lag bias.
    Must be applied before wPLI computation.
    """
    return eeg_window - np.mean(eeg_window, axis=0, keepdims=True)


# -- Eq (2): wPLI -------------------------------------------------------------

def compute_wpli(eeg_window: np.ndarray, fs: int = 256,
                 freq_low: float = None,
                 freq_high: float = None) -> np.ndarray:
    """
    Weighted Phase Lag Index for one window.
    Uses imaginary component of cross-spectrum — resistant to
    zero-lag volume conduction artifacts (Vinck et al. 2011).

    wPLI_xy = |mean(imag(C_xy))| / mean(|imag(C_xy)|)

    Parameters
    ----------
    freq_low : float or None
        Lower frequency bound (Hz) for band-specific wPLI.
        If None, full broadband FFT is used (original behaviour).
    freq_high : float or None
        Upper frequency bound (Hz) for band-specific wPLI.
        If None, full broadband FFT is used (original behaviour).
    """
    n_channels = eeg_window.shape[0]
    n_samples  = eeg_window.shape[1]
    wpli       = np.zeros((n_channels, n_channels), dtype=np.float64)
    fft_data   = np.fft.rfft(eeg_window, axis=1)

    # Band mask — only applied when both limits are specified
    if freq_low is not None and freq_high is not None:
        freqs     = np.fft.rfftfreq(n_samples, d=1.0 / fs)
        band_mask = (freqs >= freq_low) & (freqs <= freq_high)
        fft_data  = fft_data[:, band_mask]

    for i in range(n_channels):
        for j in range(i + 1, n_channels):
            cross       = fft_data[i] * np.conj(fft_data[j])
            imag_cross  = np.imag(cross)
            numerator   = np.abs(np.mean(imag_cross))
            denominator = np.mean(np.abs(imag_cross)) + 1e-8
            val         = numerator / denominator
            wpli[i, j]  = val
            wpli[j, i]  = val

    return wpli


# -- Eq (3): AEC --------------------------------------------------------------

def compute_aec(eeg_window: np.ndarray) -> np.ndarray:
    """
    Amplitude Envelope Correlation for one window.
    Amplitude-based coupling — complements phase-based wPLI.
    Always computed broadband (envelope is a wideband measure).
    """
    envelopes = np.abs(hilbert(eeg_window, axis=1))
    aec = np.corrcoef(envelopes)
    np.fill_diagonal(aec, 0.0)
    aec = np.abs(aec)
    return np.nan_to_num(aec, nan=0.0)


# -- Eq (4): Combined adjacency -----------------------------------------------

def combine_adjacency(wpli: np.ndarray, aec: np.ndarray,
                      alpha: float = DEFAULT_ALPHA) -> np.ndarray:
    """A = alpha * A_wPLI + (1 - alpha) * A_AEC"""
    return alpha * wpli + (1 - alpha) * aec


# -- Fixed minimum threshold --------------------------------------------------

def apply_fixed_threshold(A: np.ndarray,
                          threshold: float = FIXED_THRESHOLD) -> np.ndarray:
    """
    Retain edges >= threshold. Preserves absolute connectivity strength values.
    Ictal windows naturally have stronger edges, yielding higher Frobenius
    anomaly score after reconstruction.
    """
    A_thresh = np.where(A >= threshold, A, 0.0)
    np.fill_diagonal(A_thresh, 0.0)
    return A_thresh


# -- Full pipeline for one window ---------------------------------------------

def build_adjacency(eeg_window: np.ndarray,
                    alpha: float = DEFAULT_ALPHA,
                    fs: int = 256,
                    freq_low: float = None,
                    freq_high: float = None) -> np.ndarray:
    """
    Full graph construction for one 4s EEG window.

    Steps:
      1. CAR
      2. wPLI [18x18] — broadband or band-specific depending on freq_low/freq_high
      3. AEC  [18x18]  (skipped only when alpha == 1.0; always broadband)
      4. A = alpha * wPLI + (1 - alpha) * AEC
      5. Fixed threshold >= 0.05

    Parameters
    ----------
    freq_low : float or None
        Lower frequency bound (Hz) for band-specific wPLI.
        None = broadband (E_main default, fully backward compatible).
    freq_high : float or None
        Upper frequency bound (Hz) for band-specific wPLI.
        None = broadband (E_main default, fully backward compatible).

    Returns: A in R^{18x18}, float32, thresholded, values in [0, 1].
    """
    eeg_window = eeg_window.astype(np.float64)
    eeg_window = apply_car(eeg_window)

    wpli = compute_wpli(eeg_window, fs=fs,
                        freq_low=freq_low, freq_high=freq_high)

    if alpha < 1.0:
        aec = compute_aec(eeg_window)
    else:
        aec = np.zeros_like(wpli)

    A = combine_adjacency(wpli, aec, alpha=alpha)
    A = apply_fixed_threshold(A, threshold=FIXED_THRESHOLD)

    return A.astype(np.float32)