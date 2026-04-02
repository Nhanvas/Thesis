import torch
import numpy as np
from torchmetrics.functional import auroc


class MetricHandler:
    """
    Metrics for unsupervised seizure detection.
    NOTE: accuracy is intentionally excluded (0.33% prevalence makes it meaningless).
    Primary metrics: sensitivity, specificity, AUROC, FDR/h — per locked decisions.
    """
    def __init__(self, threshold_percentile=95):
        self.threshold_percentile = threshold_percentile
        self.threshold = None

    def calibrate_threshold(self, interictal_scores):
        """
        Set detection threshold at Nth percentile of interictal
        validation reconstruction errors. No label leakage.
        """
        self.threshold = np.percentile(interictal_scores, self.threshold_percentile)
        return self.threshold

    def get_auroc(self, scores, labels):
        """
        scores: np.array of anomaly scores (higher = more anomalous)
        labels: np.array binary (1=ictal, 0=interictal)
        """
        scores_t = torch.tensor(scores, dtype=torch.float32)
        labels_t = torch.tensor(labels, dtype=torch.long)
        return auroc(scores_t, labels_t, task="binary").item()

    def get_sensitivity_specificity(self, scores, labels):
        """
        Apply calibrated threshold and compute TP/FP/TN/FN.
        """
        assert self.threshold is not None, "Call calibrate_threshold() first."
        preds = (scores >= self.threshold).astype(int)

        tp = ((preds == 1) & (labels == 1)).sum()
        fn = ((preds == 0) & (labels == 1)).sum()
        tn = ((preds == 0) & (labels == 0)).sum()
        fp = ((preds == 1) & (labels == 0)).sum()

        sensitivity = tp / (tp + fn + 1e-8)
        specificity = tn / (tn + fp + 1e-8)
        return float(sensitivity), float(specificity)

    def get_fdr_per_hour(self, scores, labels, total_hours):
        """
        False detection rate per hour on continuous interictal data.
        """
        assert self.threshold is not None
        interictal_mask = labels == 0
        fp = ((scores[interictal_mask]) >= self.threshold).sum()
        return float(fp) / total_hours

    def compute_all(self, scores, labels, total_hours):
        auroc_val = self.get_auroc(scores, labels)
        sensitivity, specificity = self.get_sensitivity_specificity(scores, labels)
        fdr = self.get_fdr_per_hour(scores, labels, total_hours)
        return {
            "sensitivity": round(sensitivity, 4),
            "specificity": round(specificity, 4),
            "auroc": round(auroc_val, 4),
            "fdr_per_hour": round(fdr, 2)
        }