"""
evaluate.py
===========
Evaluation for one LTSO fold.

Threshold passed in from train_pipeline (calibrated on val interictal).
No label leakage: threshold never touches ictal data.
"""

import json
import numpy as np
import pandas as pd
import torch
from pathlib import Path
from datetime import datetime
from torch_geometric.utils import dense_to_sparse

from shared.models.metrics import MetricHandler


def run_evaluation(model, subject_ids: list,
                   processed_dir: str,
                   threshold: float,
                   experiment_id: str,
                   fold_id: str,
                   hyperparams: dict,
                   results_log_path: str,
                   notes: str = "",
                   device: str = "cpu") -> dict:
    """
    Score all windows in test fold and compute metrics.

    Args:
        threshold: calibrated on val interictal in train_pipeline.
                   Passed in directly — no ictal data used here.
    """
    model.eval()
    model.to(device)

    metric_handler = MetricHandler()
    metric_handler.threshold = threshold   # set directly, no re-calibration

    processed_dir = Path(processed_dir)
    all_scores, all_labels = [], []
    total_interictal_s = 0.0

    for subj in subject_ids:
        # ── Interictal ────────────────────────────────────────────────────────
        inter_path = processed_dir / f"{subj}_interictal_adjs.npy"
        if not inter_path.exists():
            raise FileNotFoundError(
                f"Missing: {inter_path}\nRun build_graphs.py first.")

        adjs_inter = np.load(str(inter_path), mmap_mode="r")
        scores_inter = _score_windows(model, adjs_inter, device)
        all_scores.extend(scores_inter)
        all_labels.extend([0] * len(scores_inter))
        total_interictal_s += len(scores_inter) * 4.0   # 4s per window

        # ── Ictal ─────────────────────────────────────────────────────────────
        ictal_path = processed_dir / f"{subj}_ictal_adjs.npy"
        if ictal_path.exists():
            adjs_ictal = np.load(str(ictal_path), mmap_mode="r")
            scores_ictal = _score_windows(model, adjs_ictal, device)
            all_scores.extend(scores_ictal)
            all_labels.extend([1] * len(scores_ictal))
        else:
            print(f"  [WARN] {subj}: no ictal adjs — sensitivity=0 for this subject")

    all_scores = np.array(all_scores, dtype=np.float32)
    all_labels = np.array(all_labels, dtype=np.int32)
    total_hours = total_interictal_s / 3600.0

    metrics = metric_handler.compute_all(all_scores, all_labels, total_hours)
    metrics["n_ictal_windows"]       = int((all_labels == 1).sum())
    metrics["n_interictal_windows"]  = int((all_labels == 0).sum())
    metrics["total_interictal_hours"] = round(total_hours, 2)

    _append_results(results_log_path, experiment_id, fold_id,
                    metrics, hyperparams, notes)

    print(f"[{experiment_id} | {fold_id}]  "
          f"AUROC={metrics['auroc']:.4f} | "
          f"Sensitivity={metrics['sensitivity']:.4f} | "
          f"FDR/h={metrics['fdr_per_hour']:.2f} | "
          f"ictal_windows={metrics['n_ictal_windows']}")
    return metrics


def _score_windows(model, adjs: np.ndarray, device: str) -> list:
    """
    Compute anomaly score for each window in adjs [N, 18, 18].
    Returns list of float scores.
    """
    scores = []
    with torch.no_grad():
        for A_np in adjs:
            A = torch.tensor(
                A_np.astype(np.float32), dtype=torch.float32).to(device)
            x = A.clone()
            edge_index, edge_weight = dense_to_sparse(A)
            _, A_hat = model(x, edge_index, edge_weight)
            scores.append(model.anomaly_score(A, A_hat))
    return scores


def _append_results(results_log_path: str, experiment_id: str,
                    fold_id: str, metrics: dict,
                    hyperparams: dict, notes: str) -> None:
    """Append one row to results_log.csv (create with header if absent)."""
    row = {
        "experiment_id":    experiment_id,
        "timestamp":        datetime.now().isoformat(),
        "fold_id":          fold_id,
        "sensitivity":      metrics["sensitivity"],
        "specificity":      metrics["specificity"],
        "auroc":            metrics["auroc"],
        "fdr_per_hour":     metrics["fdr_per_hour"],
        "hyperparams_json": json.dumps(hyperparams),
        "notes":            notes,
    }
    path = Path(results_log_path)
    df   = pd.DataFrame([row])
    if path.exists():
        df.to_csv(path, mode="a", header=False, index=False)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, mode="w", header=True, index=False)