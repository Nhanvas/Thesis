"""
CUSUM post-processing for seizure detection anomaly scores.

Reduces FDR/h by requiring sustained elevation above threshold
rather than single-window exceedance.

Key insight: artifacts are transient (1-2 windows), seizures are sustained
(typically 3-30+ windows). CUSUM accumulates evidence and resets
when score drops sufficiently, filtering transient spikes.

Usage: apply AFTER z-normalization, replacing hard threshold tau_z.
"""

import numpy as np


def cusum_detect(scores: np.ndarray,
                 h: float = 4.0,
                 k: float = 1.0,
                 reset_val: float = 0.0) -> np.ndarray:
    """
    Page's CUSUM for one-sided upward shift detection.

    Parameters
    ----------
    scores   : [N] array of z-normalized anomaly scores per window
    h        : decision threshold (alarm when CUSUM > h)
    k        : reference/allowance value (drift below k is reset)
                Typical: set k = tau_z / 2 = 0.74 (half of Youden threshold)
    reset_val: value CUSUM resets to after alarm (default 0 = hard reset)

    Returns
    -------
    alarms   : [N] boolean array, True = seizure detection
    cusum    : [N] CUSUM statistic values (for diagnostics)

    Algorithm
    ---------
    S[0] = 0
    S[t] = max(0, S[t-1] + (score[t] - k))
    alarm[t] = S[t] > h
    If alarm[t]: S[t] = reset_val  (reset after alarm)
    """
    N = len(scores)
    S = np.zeros(N, dtype=np.float32)
    alarms = np.zeros(N, dtype=bool)

    s_prev = 0.0
    for t in range(N):
        s_curr = max(0.0, s_prev + (scores[t] - k))
        if s_curr > h:
            alarms[t] = True
            s_prev = reset_val
        else:
            s_prev = s_curr
        S[t] = s_curr

    return alarms, S


def cusum_sweep(z_inter: np.ndarray,
                z_ictal: np.ndarray,
                h_values: list,
                k: float = 0.74,
                win_sec: float = 4.0,
                inter_hours: float = None) -> list:
    """
    Sweep CUSUM threshold h, compute AUROC + FDR/h + event sensitivity.

    Parameters
    ----------
    z_inter     : z-normalized scores for interictal windows
    z_ictal     : z-normalized scores for ictal windows
    h_values    : list of h values to test
    k           : CUSUM reference (default = Youden_tau_z / 2 = 1.48/2)
    win_sec     : window duration in seconds
    inter_hours : total interictal recording hours (for FDR/h computation)

    Returns
    -------
    results : list of dicts with keys: h, sensitivity_w, specificity_w,
              fdr_h, n_fp_events, auroc
    """
    from sklearn.metrics import roc_auc_score

    if inter_hours is None:
        inter_hours = len(z_inter) * win_sec / 3600.0

    # AUROC is threshold-independent — compute once
    y = np.concatenate([np.zeros(len(z_inter)), np.ones(len(z_ictal))])
    scores_all = np.concatenate([z_inter, z_ictal])
    auroc = roc_auc_score(y, scores_all)

    results = []
    for h in h_values:
        alarms_inter, _ = cusum_detect(z_inter, h=h, k=k)
        alarms_ictal, _ = cusum_detect(z_ictal, h=h, k=k)

        sens_w = alarms_ictal.mean()
        spec_w = 1.0 - alarms_inter.mean()

        # Count distinct FP events (consecutive alarms merged)
        fp_events = _count_events(alarms_inter, merge_gap_windows=8)  # 30s
        fdr_h = fp_events / inter_hours if inter_hours > 0 else 0.0

        results.append({
            'h': h,
            'auroc': auroc,
            'sensitivity_w': round(float(sens_w), 4),
            'specificity_w': round(float(spec_w), 4),
            'fdr_h': round(float(fdr_h), 2),
            'n_fp_events': int(fp_events),
        })

    return results


def _count_events(alarms: np.ndarray, merge_gap_windows: int = 8) -> int:
    """Count distinct alarm events, merging alarms within merge_gap_windows."""
    if not alarms.any():
        return 0

    events = 0
    in_event = False
    gap_count = 0

    for alarm in alarms:
        if alarm:
            if not in_event:
                events += 1
                in_event = True
            gap_count = 0
        else:
            if in_event:
                gap_count += 1
                if gap_count > merge_gap_windows:
                    in_event = False
                    gap_count = 0

    return events