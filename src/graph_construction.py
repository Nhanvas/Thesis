"""
graph_construction.py
=====================
Graph construction pipeline for one 4s EEG window.
CAR applied before connectivity computation.

Equations implemented (thesis §2.2):
  Eq (2): wPLI_xy = |mean(imag(C_xy))| / mean(|imag(C_xy)|)
  Eq (3): AEC_xy  = corr(|hilbert(x)|, |hilbert(y)|)
  Eq (4): A = alpha * A_wPLI + (1 - alpha) * A_AEC

Design decision — alpha=1.0 (wPLI-only) as default:
  E8 ablation (alpha sweep on chb01) showed:
    wPLI-only (alpha=1.0): Oracle AUROC=0.896
    AEC-only  (alpha=0.0): Oracle AUROC=0.423 (WRONG DIRECTION)
    Combined  (alpha=0.5): Oracle AUROC=0.640
    Combined  (alpha=0.8): Oracle AUROC=0.849

  Physiological rationale: wPLI increases during seizures because
  ictal activity propagates with lagged phase synchrony from the
  seizure focus. AEC decreases during focal seizures because
  amplitude envelopes are dominated by the focal ictal discharge
  while other regions show relative suppression — opposite direction
  to wPLI. Including AEC dilutes and inverts the wPLI signal.

  alpha=1.0 confirmed as E8 ablation winner. AEC preserved for
  ablation reporting in thesis §3.2 (used when alpha < 1.0).

Fixed threshold vs top-k%:
  Top-k% forces identical edge counts across all windows, eliminating
  the absolute connectivity strength difference between ictal and
  interictal. Fixed threshold 0.05 preserves this difference.
"""

import numpy as np
from scipy.signal import hilbert

DEFAULT_ALPHA   = 1.0    # wPLI-only: confirmed by E8 ablation
FIXED_THRESHOLD = 0.05


def apply_car(eeg_window: np.ndarray) -> np.ndarray:
    """
    Common Average Reference: subtract mean across channels at each time point.
    Suppresses common-mode noise and reduces volume conduction zero-lag bias.
    Must be applied before wPLI computation.
    """
    return eeg_window - np.mean(eeg_window, axis=0, keepdims=True)


# ── Eq (2): wPLI ─────────────────────────────────────────────────────────────

def compute_wpli(eeg_window: np.ndarray, fs: int = 256) -> np.ndarray:
    """
    Weighted Phase Lag Index for one window.
    Uses imaginary component of cross-spectrum — resistant to
    zero-lag volume conduction artifacts (Vinck et al. 2011).

    wPLI_xy = |mean(imag(C_xy))| / mean(|imag(C_xy)|)

    Increases during seizures: ictal activity propagates with lagged
    phase synchrony from the seizure focus to neighbouring electrodes.
    """
    n_channels = eeg_window.shape[0]
    wpli = np.zeros((n_channels, n_channels), dtype=np.float64)
    fft_data = np.fft.rfft(eeg_window, axis=1)

    for i in range(n_channels):
        for j in range(i + 1, n_channels):
            cross       = fft_data[i] * np.conj(fft_data[j])
            imag_cross  = np.imag(cross)
            numerator   = np.abs(np.mean(imag_cross))
            denominator = np.mean(np.abs(imag_cross)) + 1e-8
            val = numerator / denominator
            wpli[i, j] = val
            wpli[j, i] = val

    return wpli


# ── Eq (3): AEC ──────────────────────────────────────────────────────────────

def compute_aec(eeg_window: np.ndarray) -> np.ndarray:
    """
    Amplitude Envelope Correlation for one window.
    Computed only when alpha < 1.0 (ablation E8).

    NOTE: AEC shows wrong direction for seizure detection on CHB-MIT
    (Oracle AUROC=0.42). Not used in default pipeline (alpha=1.0).
    """
    envelopes = np.abs(hilbert(eeg_window, axis=1))
    aec = np.corrcoef(envelopes)
    np.fill_diagonal(aec, 0.0)
    aec = np.abs(aec)
    return np.nan_to_num(aec, nan=0.0)


# ── Eq (4): Combined adjacency ────────────────────────────────────────────────

def combine_adjacency(wpli: np.ndarray, aec: np.ndarray,
                      alpha: float = DEFAULT_ALPHA) -> np.ndarray:
    """A = alpha * A_wPLI + (1 - alpha) * A_AEC"""
    return alpha * wpli + (1 - alpha) * aec


# ── Fixed minimum threshold ───────────────────────────────────────────────────

def apply_fixed_threshold(A: np.ndarray,
                          threshold: float = FIXED_THRESHOLD) -> np.ndarray:
    """
    Retain edges >= threshold. Preserves absolute wPLI strength values.
    Ictal windows naturally have stronger edges → higher Frobenius anomaly score.
    """
    A_thresh = np.where(A >= threshold, A, 0.0)
    np.fill_diagonal(A_thresh, 0.0)
    return A_thresh


# ── Full pipeline for one window ──────────────────────────────────────────────

def build_adjacency(eeg_window: np.ndarray,
                    alpha: float = DEFAULT_ALPHA,
                    top_k_percent: float = 30,
                    fs: int = 256) -> np.ndarray:
    """
    Full graph construction for one 4s EEG window.

    Steps:
      1. CAR
      2. wPLI [18x18]
      3. AEC  [18x18] — only computed when alpha < 1.0
      4. A = alpha*wPLI + (1-alpha)*AEC
      5. Fixed threshold >= 0.05

    top_k_percent accepted but ignored (backward compatibility).
    """
    eeg_window = eeg_window.astype(np.float64)
    eeg_window = apply_car(eeg_window)

    wpli = compute_wpli(eeg_window, fs=fs)

    if alpha < 1.0:
        aec = compute_aec(eeg_window)
    else:
        aec = np.zeros_like(wpli)

    A = combine_adjacency(wpli, aec, alpha=alpha)
    A = apply_fixed_threshold(A, threshold=FIXED_THRESHOLD)

    return A.astype(np.float32)