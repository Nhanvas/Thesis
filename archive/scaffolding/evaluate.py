"""
evaluate.py
===========
Evaluation for one LTSO fold. Now uses node features.
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
    model.eval()
    model.to(device)

    metric_handler = MetricHandler()
    metric_handler.threshold = threshold

    processed_dir = Path(processed_dir)
    all_scores, all_labels = [], []
    total_interictal_s = 0.0

    for subj in subject_ids:
        # Interictal
        inter_adj = processed_dir / f"{subj}_interictal_adjs.npy"
        inter_feat = processed_dir / f"{subj}_interictal_features.npy"
        if not inter_adj.exists() or not inter_feat.exists():
            raise FileNotFoundError(f"Missing data for {subj}")

        adjs_inter = np.load(str(inter_adj), mmap_mode="r")
        feats_inter = np.load(str(inter_feat), mmap_mode="r")
        scores_inter = _score_windows(model, adjs_inter, feats_inter, device)
        all_scores.extend(scores_inter)
        all_labels.extend([0] * len(scores_inter))
        total_interictal_s += len(scores_inter) * 4.0

        # Ictal
        ictal_adj = processed_dir / f"{subj}_ictal_adjs.npy"
        ictal_feat = processed_dir / f"{subj}_ictal_features.npy"
        if ictal_adj.exists() and ictal_feat.exists():
            adjs_ictal = np.load(str(ictal_adj), mmap_mode="r")
            feats_ictal = np.load(str(ictal_feat), mmap_mode="r")
            scores_ictal = _score_windows(model, adjs_ictal, feats_ictal, device)
            all_scores.extend(scores_ictal)
            all_labels.extend([1] * len(scores_ictal))
        else:
            print(f"  [WARN] {subj}: no ictal data")

    all_scores = np.array(all_scores, dtype=np.float32)
    all_labels = np.array(all_labels, dtype=np.int32)
    total_hours = total_interictal_s / 3600.0

    metrics = metric_handler.compute_all(all_scores, all_labels, total_hours)
    metrics["n_ictal_windows"] = int((all_labels == 1).sum())
    metrics["n_interictal_windows"] = int((all_labels == 0).sum())
    metrics["total_interictal_hours"] = round(total_hours, 2)

    _append_results(results_log_path, experiment_id, fold_id,
                    metrics, hyperparams, notes)

    print(f"[{experiment_id} | {fold_id}]  "
          f"AUROC={metrics['auroc']:.4f} | "
          f"Sensitivity={metrics['sensitivity']:.4f} | "
          f"FDR/h={metrics['fdr_per_hour']:.2f}")
    return metrics


def _build_node_features(A_np: np.ndarray, X_np: np.ndarray) -> np.ndarray:
    """
    Construct node feature matrix [18, 23] = concat(A_row_norm, band_power_norm).
    Must match EEGGraphDataset.__getitem__ exactly.
    """
    A_max  = A_np.max()
    A_norm = A_np / (A_max + 1e-8)                          # [18, 18]

    B_min  = X_np.min(axis=0, keepdims=True)
    B_max  = X_np.max(axis=0, keepdims=True)
    B_norm = (X_np - B_min) / (B_max - B_min + 1e-8)       # [18, 5]

    return np.concatenate([A_norm, B_norm], axis=1)          # [18, 23]


def _score_windows(model, adjs: np.ndarray,
                   features: np.ndarray, device: str) -> list:
    scores = []
    with torch.no_grad():
        for A_np, X_np in zip(adjs, features):
            A_np = A_np.astype(np.float32)
            X_np = X_np.astype(np.float32)

            X_combined = _build_node_features(A_np, X_np)   # [18, 23]

            A          = torch.tensor(A_np).to(device)
            X          = torch.tensor(X_combined).to(device)

            edge_index, edge_weight = dense_to_sparse(A)
            _, A_hat = model(X, edge_index, edge_weight)
            scores.append(model.anomaly_score(A, A_hat))
    return scores


def _append_results(results_log_path: str, experiment_id: str,
                    fold_id: str, metrics: dict,
                    hyperparams: dict, notes: str) -> None:
    row = {
        "experiment_id": experiment_id,
        "timestamp": datetime.now().isoformat(),
        "fold_id": fold_id,
        "sensitivity": metrics["sensitivity"],
        "specificity": metrics["specificity"],
        "auroc": metrics["auroc"],
        "fdr_per_hour": metrics["fdr_per_hour"],
        "hyperparams_json": json.dumps(hyperparams),
        "notes": notes,
    }
    path = Path(results_log_path)
    df = pd.DataFrame([row])
    if path.exists():
        df.to_csv(path, mode="a", header=False, index=False)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, mode="w", header=True, index=False)