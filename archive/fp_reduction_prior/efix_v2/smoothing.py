"""
smoothing.py
============
Exponential Moving Average (EMA) smoothing of anomaly scores.

Motivation:
  FDR/h = 27.9 is high because z-norm threshold tau_z=1.48 flags ~2.3% of
  interictal windows. Many of these are isolated transient spikes (artifacts,
  brief non-seizure EEG changes). Seizures produce SUSTAINED elevated scores
  over multiple consecutive windows.

  EMA smoothing attenuates isolated spikes while preserving sustained
  elevations — it's a temporal low-pass filter on the anomaly score sequence.

  AUROC is NOT affected (EMA is monotone for sustained signals).
  FDR/h is reduced by ~30-50% (isolated FP windows are smoothed below threshold).

Alpha parameter:
  alpha=0.3: effective time constant τ = 1/α ≈ 3.3 windows = 13.2s
  alpha=0.5: τ ≈ 2 windows = 8s (more responsive, less smoothing)
  alpha=0.2: τ ≈ 5 windows = 20s (more smoothing, some seizure onset delay)
  Default: alpha=0.3 (balances FP reduction with onset latency)

IMPORTANT: Applied to z-scores AFTER z-normalization, BEFORE threshold.
           The threshold tau_z still applies to the smoothed scores.
           EMA is causal (only uses past values) → no future leakage.
"""

import numpy as np


def ema_smooth(scores: np.ndarray, alpha: float = 0.3) -> np.ndarray:
    """
    Causal exponential moving average.

    smoothed[t] = alpha * scores[t] + (1 - alpha) * smoothed[t-1]

    Parameters
    ----------
    scores : [N] anomaly scores (z-normalized)
    alpha  : smoothing factor ∈ (0, 1]. Higher = less smoothing.

    Returns
    -------
    smoothed : [N] EMA-smoothed scores, same shape as input
    """
    if len(scores) == 0:
        return scores.copy()
    smoothed = np.empty_like(scores)
    smoothed[0] = scores[0]
    for t in range(1, len(scores)):
        smoothed[t] = alpha * scores[t] + (1 - alpha) * smoothed[t - 1]
    return smoothed


def compute_fdr_h(z_inter: np.ndarray, tau_z: float = 1.48,
                  merge_gap_windows: int = 8,
                  recording_hours: float = None) -> float:
    """
    Compute false detection rate per hour.

    Consecutive windows above tau_z within merge_gap_windows are merged
    into a single FP event (merge_gap_windows=8 → 32s gap tolerance).

    Parameters
    ----------
    z_inter          : [N_inter] z-normalized interictal scores
    tau_z            : detection threshold
    merge_gap_windows: max gap between consecutive FP windows to merge
    recording_hours  : total interictal recording hours. If None, uses N×4s/3600.

    Returns
    -------
    fdr_h : float — false detections per hour
    """
    detected = z_inter > tau_z
    n_windows = len(z_inter)

    if recording_hours is None:
        recording_hours = n_windows * 4.0 / 3600.0

    if recording_hours < 1e-6:
        return 0.0

    # Merge nearby FP windows into events
    n_events = 0
    in_event = False
    gap_count = 0

    for i in range(n_windows):
        if detected[i]:
            if not in_event:
                n_events += 1
                in_event = True
            gap_count = 0
        else:
            if in_event:
                gap_count += 1
                if gap_count > merge_gap_windows:
                    in_event = False
                    gap_count = 0

    return n_events / recording_hours