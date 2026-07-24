"""
graph_construction.py
=====================
Graph construction pipeline for one 4s EEG window.
CAR applied before connectivity computation.

Equations implemented (thesis §2.2):
  Eq (2): wPLI_xy = |mean(imag(C_xy))| / mean(|imag(C_xy)|)
  Eq (3): AEC_xy  = corr(|hilbert(x)|, |hilbert(y)|)
  Eq (4): A = alpha * A_wPLI + (1 - alpha) * A_AEC
  Eq (5): Top-k% threshold — retain top keep_ratio fraction of edge weights

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
  wPLI/AEC absolute values differ substantially across subjects due to
  EEG baseline heterogeneity (electrode impedance, recording conditions,
  patient physiology). At fixed t=0.05, graph density ranges from 0.92
  to 0.97 across subjects — near-fully-connected. GCN message passing
  over a near-complete graph reduces to weighted global mean pooling,
  destroying any topological signal.

  Top-k% ensures consistent density across all subjects (~0.20 = 30/153
  edges for 18 channels), enabling the model to learn a universal
  interictal connectivity structure independent of subject-specific
  EEG baseline. Edge weights are retained at their original values
  (not rescaled) so both topology changes and weight magnitude changes
  contribute to the anomaly score.

  Diagnostic evidence (E_sparse): Frobenius distance between ictal
  and interictal mean adjacency improves +88% to +411% across 8 test
  subjects when switching from fixed t=0.05 to top-k 20%.
"""

import numpy as np
from scipy.signal import hilbert

DEFAULT_ALPHA    = 0.5    # combined wPLI + AEC — E_main default
FIXED_THRESHOLD  = 0.05   # used only in baseline dense pipeline
DEFAULT_KEEP_RATIO = 0.20  # top-k%: 30 edges for 18-channel EEG

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


# -- Fixed minimum threshold (baseline dense pipeline) ------------------------

def apply_fixed_threshold(A: np.ndarray,
                          threshold: float = FIXED_THRESHOLD) -> np.ndarray:
    """
    Retain edges with weight >= threshold.

    Note: produces graph density 0.92–0.97 at t=0.05 for CHB-MIT EEG,
    which is too dense for meaningful GCN topology learning. This function
    is retained for the baseline dense pipeline only.
    For E_sparse and all subsequent experiments, use apply_topk_threshold().
    """
    A_thresh = np.where(A >= threshold, A, 0.0)
    np.fill_diagonal(A_thresh, 0.0)
    return A_thresh


# -- Eq (5): Top-k% threshold (E_sparse pipeline) ----------------------------

def apply_topk_threshold(A: np.ndarray,
                         keep_ratio: float = DEFAULT_KEEP_RATIO) -> np.ndarray:
    """
    Retain the top keep_ratio fraction of undirected edge weights per window.

    Cutoff is computed from upper-triangle values (avoids diagonal self-loops).
    Original weight values are retained for kept edges — NOT rescaled.
    Result is symmetric: A[i,j] and A[j,i] are kept or removed together.

    Why top-k% (not fixed threshold):
      Fixed threshold produces heterogeneous density across subjects
      (0.14 to 0.97 at t=0.05 for CHB-MIT). A single model cannot learn
      a universal interictal connectivity pattern when 'connected' means
      different things per subject. Top-k% ensures all subjects contribute
      graphs of equal density (~0.20), making the learning problem consistent.

    Why retain original weight values (not rescale):
      Two anomaly detection mechanisms depend on original weights:
      (1) Topology change: which electrode pairs appear in top-k during
          seizure differs from interictal — GAE sees unfamiliar structure.
      (2) Weight magnitude: ictal top-k edges are stronger than interictal
          top-k edges. GAE trained on interictal weights predicts lower
          values → higher MSE reconstruction error.
      Rescaling to [0,1] per-window would eliminate mechanism (2).

    Note on ties: if multiple edges share the cutoff value, all are retained.
    Actual density may slightly exceed keep_ratio in such cases (~1–2 edges).

    Parameters
    ----------
    A : np.ndarray, shape [n, n]
        Symmetric adjacency matrix with values in [0, 1].
    keep_ratio : float
        Fraction of undirected edges to retain.
        Default 0.20 → 30 edges for 18-channel EEG (153 undirected pairs).

    Returns
    -------
    np.ndarray, shape [n, n], float64
        Sparse symmetric adjacency. ~keep_ratio of edges non-zero.
    """
    n = A.shape[0]
    n_edges = n * (n - 1) // 2          # 153 for n=18, computed dynamically
    k = max(1, int(n_edges * keep_ratio))

    triu_idx  = np.triu_indices(n, k=1)  # upper triangle, no diagonal
    triu_vals = A[triu_idx]              # 153 values for n=18

    sorted_vals = np.sort(triu_vals)     # ascending
    cutoff      = sorted_vals[-k]        # k-th largest value

    result = np.where(A >= cutoff, A, 0.0)
    np.fill_diagonal(result, 0.0)        # ensure no self-loops
    return result


# -- Full pipeline for one window (baseline dense, reads raw EEG) -------------

def build_adjacency(eeg_window: np.ndarray,
                    alpha: float = DEFAULT_ALPHA,
                    fs: int = 256,
                    freq_low: float = None,
                    freq_high: float = None) -> np.ndarray:
    """
    Full graph construction for one 4s EEG window.
    Used by build_graphs.py when raw preprocessed windows are available.

    For top-k% pipeline (E_sparse), use build_topk_from_dense.py instead,
    which post-processes existing dense adjacency files without raw windows.

    Steps:
      1. CAR
      2. wPLI [18x18] — broadband or band-specific
      3. AEC  [18x18] (skipped only when alpha == 1.0; always broadband)
      4. A = alpha * wPLI + (1 - alpha) * AEC
      5. Fixed threshold >= 0.05  (baseline dense pipeline only)

    Returns: A in R^{18x18}, float32, fixed-threshold, values in [0, 1].
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

# ═══════════════════════════════════════════════════════════════════════════════
# OPTION B — Multiband wPLI (paste này vào CUỐI file graph_construction.py,
#             sau hàm build_adjacency() hiện tại)
# ═══════════════════════════════════════════════════════════════════════════════

# Band weights derived from spectral diagnostic (check_spectral_all.py output).
# Alpha dominates: sign-flip suppression confirmed in 7/8 test subjects.
# Beta shows significant increase in chb15 (+194%) and chb16.
# Delta and gamma show minimal change across subjects.
MULTIBAND_WEIGHTS = {
    "delta": 0.05,
    "theta": 0.10,
    "alpha": 0.50,
    "beta":  0.25,
    "gamma": 0.10,
}

# Band frequency ranges (Hz) — same as BAND_RANGES but explicit for multiband
_MULTIBAND_DEFS = [
    ("delta", 0.5,  4.0),
    ("theta", 4.0,  8.0),
    ("alpha", 8.0, 13.0),
    ("beta",  13.0, 30.0),
    ("gamma", 30.0, 60.0),
]


def compute_wpli_multiband(eeg_window: np.ndarray,
                           fs: int = 256,
                           weights: dict = None) -> np.ndarray:
    """
    Weighted combination of band-specific wPLI matrices.

    Replaces broadband wPLI with a weighted sum over 5 frequency bands.
    Weights are derived from the spectral diagnostic showing which bands
    carry the most discriminative signal between interictal and ictal EEG.

    Equation:
        A_wpli_multi = Σ_b  w_b × wPLI(band_b)

    where w_b are the MULTIBAND_WEIGHTS and wPLI(band_b) is the weighted
    Phase Lag Index restricted to frequency band b.

    Parameters
    ----------
    eeg_window : np.ndarray  [18, 1024]  pre-filtered, z-scored EEG window
    fs         : int         sampling rate (Hz)
    weights    : dict or None  band name → weight. Default: MULTIBAND_WEIGHTS.

    Returns
    -------
    A_wpli_multi : np.ndarray  [18, 18]  float64, values in [0, 1]
    """
    if weights is None:
        weights = MULTIBAND_WEIGHTS

    n_ch = eeg_window.shape[0]
    A_combined = np.zeros((n_ch, n_ch), dtype=np.float64)

    for band_name, fl, fh in _MULTIBAND_DEFS:
        w = weights[band_name]
        if w == 0.0:
            continue
        A_band = compute_wpli(eeg_window, fs=fs, freq_low=fl, freq_high=fh)
        A_combined += w * A_band

    return A_combined


def build_adjacency_multiband(eeg_window: np.ndarray,
                              alpha: float = DEFAULT_ALPHA,
                              fs: int = 256,
                              weights: dict = None) -> np.ndarray:
    """
    Full graph construction for one 4s EEG window — multiband wPLI variant.

    Used by build_graphs.py --multiband flag.

    Differences from build_adjacency():
      - wPLI is computed as weighted combination of 5 band-specific matrices
        instead of broadband wPLI. Weights: MULTIBAND_WEIGHTS.
      - AEC is unchanged (always broadband — envelope is a wideband measure).
      - Fixed threshold 0.05 applied (same as original pipeline).
        Caller is expected to apply apply_topk_threshold() afterwards via
        build_topk_from_dense.py.

    Steps:
      1. CAR (common average reference)
      2. Multiband wPLI [18x18] — weighted sum over 5 bands
      3. AEC [18x18] — broadband (skipped if alpha == 1.0)
      4. A = alpha * A_wpli_multi + (1 - alpha) * A_aec
      5. Fixed threshold >= 0.05

    Parameters
    ----------
    eeg_window : np.ndarray  [18, 1024]  raw preprocessed EEG window
    alpha      : float       wPLI weight in combined adjacency (default 0.5)
    fs         : int         sampling rate (Hz)
    weights    : dict or None  band weights. Default: MULTIBAND_WEIGHTS.

    Returns
    -------
    A : np.ndarray  [18, 18]  float32
    """
    eeg_window = eeg_window.astype(np.float64)
    eeg_window = apply_car(eeg_window)

    wpli = compute_wpli_multiband(eeg_window, fs=fs, weights=weights)

    if alpha < 1.0:
        aec = compute_aec(eeg_window)
    else:
        aec = np.zeros_like(wpli)

    A = combine_adjacency(wpli, aec, alpha=alpha)
    A = apply_fixed_threshold(A, threshold=FIXED_THRESHOLD)

    return A.astype(np.float32)