"""
metrics.py
==========
Evaluation metrics for unsupervised seizure detection.

Accuracy is intentionally excluded:
  0.18% seizure prevalence => 99.82% accuracy by predicting all-normal.
  This is a misleading metric that examiners will flag immediately.

Primary metrics: sensitivity, specificity, AUROC, FDR/h.

FDR/h uses EVENT-LEVEL counting (30s merge window), not window-level.
Rationale: consecutive positive windows within 30s represent one clinical
false alarm event, not multiple independent detections.
"""

import numpy as np
import torch
from torchmetrics.functional import auroc as torchmetrics_auroc


class MetricHandler:
    """
    Compute evaluation metrics for one LTSO fold.
    Threshold calibrated externally (from val interictal scores).
    """

    def __init__(self, threshold_percentile: int = 95):
        self.threshold_percentile = threshold_percentile
        self.threshold: float | None = None

    def calibrate_threshold(self, interictal_scores: np.ndarray) -> float:
        """
        Set detection threshold at Nth percentile of interictal
        reconstruction errors. No ictal labels involved — no leakage.
        """
        self.threshold = float(
            np.percentile(interictal_scores, self.threshold_percentile))
        return self.threshold

    def get_auroc(self, scores: np.ndarray,
                  labels: np.ndarray) -> float:
        scores_t = torch.tensor(scores, dtype=torch.float32)
        labels_t = torch.tensor(labels, dtype=torch.long)
        return float(torchmetrics_auroc(
            scores_t, labels_t, task="binary"))

    def get_sensitivity_specificity(
            self, scores: np.ndarray,
            labels: np.ndarray) -> tuple[float, float]:
        assert self.threshold is not None, \
            "Call calibrate_threshold() before compute_all()"

        preds = (scores >= self.threshold).astype(int)
        tp = int(((preds == 1) & (labels == 1)).sum())
        fn = int(((preds == 0) & (labels == 1)).sum())
        tn = int(((preds == 0) & (labels == 0)).sum())
        fp = int(((preds == 1) & (labels == 0)).sum())

        sensitivity = tp / (tp + fn + 1e-8)
        specificity = tn / (tn + fp + 1e-8)
        return float(sensitivity), float(specificity)

    def get_fdr_per_hour(self, scores: np.ndarray,
                         labels: np.ndarray,
                         total_hours: float,
                         merge_window_s: int = 30,
                         window_s: int = 4) -> float:
        """
        False Detection Rate per hour — EVENT-LEVEL (not window-level).

        Consecutive false-positive windows within 30s are merged into
        one false detection event. This matches clinical alarm counting:
        a burst of false alarms lasting 20s is one event, not 5 events.

        merge_window_s: gap in seconds before a new event is counted.
        window_s:       size of each EEG window (4s non-overlapping).
        """
        assert self.threshold is not None

        interictal_mask = labels == 0
        fp_flags = (scores[interictal_mask] >= self.threshold).astype(int)

        merge_gap_windows = merge_window_s // window_s  # 7 windows = 28s

        events = 0
        in_event = False
        gap_count = 0

        for flag in fp_flags:
            if flag == 1:
                if not in_event:
                    events += 1
                    in_event = True
                gap_count = 0
            else:
                if in_event:
                    gap_count += 1
                    if gap_count >= merge_gap_windows:
                        in_event = False
                        gap_count = 0

        return float(events) / max(total_hours, 1e-8)

    def compute_all(self, scores: np.ndarray,
                    labels: np.ndarray,
                    total_hours: float) -> dict:
        """
        Requires calibrate_threshold() to have been called first.
        """
        auroc_val                = self.get_auroc(scores, labels)
        sensitivity, specificity = self.get_sensitivity_specificity(
            scores, labels)
        fdr = self.get_fdr_per_hour(scores, labels, total_hours)

        return {
            "sensitivity": round(sensitivity, 4),
            "specificity": round(specificity, 4),
            "auroc":       round(auroc_val,   4),
            "fdr_per_hour": round(fdr,        2),
        }