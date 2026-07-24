# src/cpd_eval.py
"""
Change Point Detection on ensemble anomaly score timeline.
No threshold required. Detects both upward and downward changes.
"""
import numpy as np
import ruptures as rpt
from pathlib import Path


def compute_bic_penalty(signal):
    """
    BIC-based penalty for PELT: β = σ² * log(n)
    σ estimated from 80th percentile of scores (interictal-dominated region)
    without using any labels.
    """
    cutoff = np.percentile(signal, 80)
    baseline = signal[signal <= cutoff]
    sigma2 = np.var(baseline) if len(baseline) > 1 else np.var(signal)
    n = len(signal)
    return float(sigma2 * np.log(n))


def detect_change_points(timeline, penalty=None):
    """
    PELT with RBF cost on anomaly score timeline.
    Returns list of change point window indices.
    """
    signal = timeline.reshape(-1, 1)
    if penalty is None:
        penalty = compute_bic_penalty(timeline)
    algo = rpt.Pelt(model="rbf", min_size=3, jump=1).fit(signal)
    # predict returns indices of change points (last index = len(signal))
    cps = algo.predict(pen=penalty)
    return [cp for cp in cps if cp < len(timeline)]   # exclude end sentinel


def evaluate_cpd(change_points, seizure_times, times_s, tolerance_s=30):
    """
    Match change points to seizure onsets.
    
    TP: change point within ±tolerance_s seconds of a seizure onset
    FP: change point not matched to any seizure
    FDR/h: false change points per interictal recording hour

    Key advantage over threshold: detects BOTH upward AND downward changes.
    chb06 (inverted signal) benefits from this.
    """
    WIN_S = 4
    tp, fn = 0, 0
    latencies = []
    matched_cps = set()

    for onset_s, offset_s in seizure_times:
        # Find change points within tolerance of this seizure onset
        tol_win = tolerance_s // WIN_S
        # Convert onset time to window index
        onset_idx = np.searchsorted(times_s, onset_s)
        candidates = [cp for cp in change_points
                      if abs(cp - onset_idx) <= tol_win]
        if candidates:
            tp += 1
            best = min(candidates, key=lambda cp: abs(cp - onset_idx))
            latency_s = (best - onset_idx) * WIN_S
            latencies.append(latency_s)
            matched_cps.add(best)
        else:
            fn += 1

    # False change points (not matched to any seizure)
    fp_cps = [cp for cp in change_points if cp not in matched_cps]
    n_inter_h = sum(1 for lbl in labels if lbl == 0) * WIN_S / 3600.0
    fcp_h = len(fp_cps) / max(n_inter_h, 1e-6)

    det_rate = tp / max(tp + fn, 1)
    mean_lat = float(np.mean(latencies)) if latencies else float('nan')
    return det_rate, fcp_h, mean_lat, tp, fn, len(fp_cps)