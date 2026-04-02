import numpy as np
import pandas as pd
import torch
from pathlib import Path
from datetime import datetime
from torch_geometric.data import Data, Batch
from shared.models.metrics import MetricHandler


def run_evaluation(model, subject_ids, splits_dir, processed_dir,
                   experiment_id, fold_id, hyperparams, results_log_path,
                   threshold_percentile=95, device="cpu", notes=""):
    """
    Full evaluation for one LTSO fold.
    1. Calibrate threshold on interictal validation split
    2. Score all ictal + interictal test windows
    3. Compute metrics
    4. Append to results_log.csv
    """
    model.eval()
    model.to(device)
    metric_handler = MetricHandler(threshold_percentile=threshold_percentile)

    # ── Load splits ───────────────────────────────────────────────────────────
    splits_dir = Path(splits_dir)
    val_subjects = np.load(splits_dir / f"{fold_id}_val_subjects.npy", allow_pickle=True)
    test_subjects = subject_ids  # held-out subjects for this fold

    # ── Calibrate threshold on interictal VAL split ───────────────────────────
    val_scores = []
    for subj in val_subjects:
        adjs = np.load(Path(processed_dir) / f"{subj}_interictal_adjs.npy")
        scores = _score_windows(model, adjs, device)
        val_scores.extend(scores)

    threshold = metric_handler.calibrate_threshold(np.array(val_scores))

    # ── Score TEST fold (ictal + interictal) ──────────────────────────────────
    all_scores, all_labels = [], []
    total_interictal_s = 0

    for subj in test_subjects:
        # Interictal
        adjs_i = np.load(Path(processed_dir) / f"{subj}_interictal_adjs.npy")
        scores_i = _score_windows(model, adjs_i, device)
        all_scores.extend(scores_i)
        all_labels.extend([0] * len(scores_i))
        total_interictal_s += len(scores_i) * 4  # 4s per window

        # Ictal
        adjs_s = np.load(Path(processed_dir) / f"{subj}_ictal_adjs.npy")
        scores_s = _score_windows(model, adjs_s, device)
        all_scores.extend(scores_s)
        all_labels.extend([1] * len(scores_s))

    all_scores = np.array(all_scores)
    all_labels = np.array(all_labels)
    total_hours = total_interictal_s / 3600

    metrics = metric_handler.compute_all(all_scores, all_labels, total_hours)

    # ── Append to results_log.csv ─────────────────────────────────────────────
    _append_results(
        results_log_path=results_log_path,
        experiment_id=experiment_id,
        fold_id=fold_id,
        metrics=metrics,
        hyperparams=hyperparams,
        notes=notes
    )

    print(f"[{experiment_id} | {fold_id}] "
          f"AUROC={metrics['auroc']:.4f} | "
          f"Sens={metrics['sensitivity']:.4f} | "
          f"FDR/h={metrics['fdr_per_hour']:.2f}")

    return metrics


def _score_windows(model, adjs, device):
    """Compute anomaly score for each window in adjs [N, 18, 18]."""
    scores = []
    with torch.no_grad():
        for A_np in adjs:
            A = torch.tensor(A_np, dtype=torch.float32).to(device)
            x = A.clone()
            from torch_geometric.utils import dense_to_sparse
            edge_index, edge_weight = dense_to_sparse(A)
            _, A_hat = model(x, edge_index, edge_weight)
            score = model.anomaly_score(A, A_hat)
            scores.append(score)
    return scores


def _append_results(results_log_path, experiment_id, fold_id,
                    metrics, hyperparams, notes):
    """Append one row to results_log.csv (create with header if not exists)."""
    import json
    row = {
        "experiment_id":       experiment_id,
        "timestamp":           datetime.now().isoformat(),
        "fold_id":             fold_id,
        "sensitivity":         metrics["sensitivity"],
        "specificity":         metrics["specificity"],
        "auroc":               metrics["auroc"],
        "fdr_per_hour":        metrics["fdr_per_hour"],
        "hyperparams_json":    json.dumps(hyperparams),
        "notes":               notes
    }
    path = Path(results_log_path)
    df_new = pd.DataFrame([row])
    if path.exists():
        df_new.to_csv(path, mode="a", header=False, index=False)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        df_new.to_csv(path, mode="w", header=True, index=False)