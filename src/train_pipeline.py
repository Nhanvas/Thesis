"""
train_pipeline.py
=================
Train GAE on interictal adjacency matrices of training subjects.
Evaluate on held-out LTSO test subjects.

Usage (smoke test):
    cd src
    python train_pipeline.py
"""

import sys
import torch
import numpy as np
from pathlib import Path
from torch.utils.data import DataLoader, random_split, ConcatDataset

sys.path.insert(0, str(Path(__file__).parent))

from configs.config import ConfigReader
from shared.models.logger import ExperimentLogger
from shared.models.loss_function import LossHandler
from shared.models.optimization import OptimizerHandler
from shared.models.trainer import Trainer
from shared.models.metrics import MetricHandler
from shared.services.data.dataset import EEGGraphDataset
from shared.services.models_hub.gae.model import GAEModel
from evaluate import run_evaluation


def set_seed(seed: int = 42):
    torch.manual_seed(seed)
    np.random.seed(seed)
    torch.backends.cudnn.deterministic = True


def run(config_path: str = "./configs/defaults.yaml",
        experiment_path: str = None,
        experiment_id: str = "E5_proposed_gae",
        fold_id: str = "fold_1",
        train_subjects: list = None,
        test_subjects: list = None) -> dict:
    """
    Train GAE on interictal windows of train_subjects.
    Evaluate on test_subjects (held-out LTSO fold).
    """
    config = ConfigReader.merge(config_path, experiment_path)
    set_seed(config.training.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    logger = ExperimentLogger(log_dir=config.training.log_dir)
    logger.log_message(
        f"Start: {experiment_id} | {fold_id} | device={device}")

    processed_dir = Path(config.data.processed_dir)

    # ── Build dataset từ training subjects ───────────────────────────────────
    datasets = []
    for subj in train_subjects:
        adjs_path = processed_dir / f"{subj}_interictal_adjs.npy"
        if not adjs_path.exists():
            raise FileNotFoundError(
                f"Missing: {adjs_path}\n"
                f"Run build_graphs.py first.")
        datasets.append(EEGGraphDataset(str(adjs_path)))

    full_dataset = ConcatDataset(datasets)
    n_total = len(full_dataset)
    n_val   = max(1, int(0.2 * n_total))
    n_train = n_total - n_val

    logger.log_message(
        f"Dataset: {n_total} windows | train={n_train} | val={n_val}")

    train_ds, val_ds = random_split(
        full_dataset, [n_train, n_val],
        generator=torch.Generator().manual_seed(config.training.seed))

    train_loader = DataLoader(
        train_ds, batch_size=config.data.batch_size,
        shuffle=True, num_workers=0, pin_memory=False)
    val_loader = DataLoader(
        val_ds, batch_size=config.data.batch_size,
        shuffle=False, num_workers=0, pin_memory=False)

    # ── Model ─────────────────────────────────────────────────────────────────
    model = GAEModel(
        in_channels=config.data.n_channels,
        hidden_dim=config.model.hidden_dim,
        latent_dim=config.model.latent_dim)
    model.summary()
    logger.log_model_info(model)

    # ── Train ─────────────────────────────────────────────────────────────────
    loss_handler = LossHandler(loss_type="graph_bce")

    optimizer_handler = OptimizerHandler(
        optimizer_type=config.training.optimizer,
        lr=config.training.lr,
        scheduler_type=config.training.scheduler,
        T_max=config.training.max_epochs)

    checkpoint_dir = (Path(config.training.checkpoint_dir)
                      / experiment_id / fold_id)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    trainer = Trainer(
        max_epochs=config.training.max_epochs,
        checkpoint_dir=str(checkpoint_dir),
        patience=10)

    train_result = trainer.train(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        loss_handler=loss_handler,
        optimizer_handler=optimizer_handler,
        device=device)

    # Save final weights
    weights_path = checkpoint_dir / "model_weights.pt"
    torch.save(model.state_dict(), str(weights_path))
    logger.log_message(f"Weights saved: {weights_path}")

    # ── Calibrate threshold từ val scores ────────────────────────────────────
    metric_handler = MetricHandler(
        threshold_percentile=config.anomaly.threshold_percentile)
    threshold = metric_handler.calibrate_threshold(
        np.array(train_result["val_scores"]))
    logger.log_message(f"Threshold (95th pct): {threshold:.4f}")

    # ── Evaluate ──────────────────────────────────────────────────────────────
    hyperparams = {
        "hidden_dim": config.model.hidden_dim,
        "latent_dim": config.model.latent_dim,
        "lr":         config.training.lr,
        "alpha":      config.graph.alpha,
        "top_k":      config.graph.top_k_percent,
        "seed":       config.training.seed,
        "threshold":  round(threshold, 4),
    }

    metrics = run_evaluation(
        model=model,
        subject_ids=test_subjects,
        processed_dir=str(processed_dir),
        threshold=threshold,
        experiment_id=experiment_id,
        fold_id=fold_id,
        hyperparams=hyperparams,
        results_log_path=config.evaluation.results_log,
        device=device,
        notes=f"train={train_subjects}")

    logger.log_results(metrics)
    logger.log_message(f"Done: {experiment_id} | {fold_id}")
    return metrics


if __name__ == "__main__":
    # Within-subject smoke test: train + test trên chb01
    # Mục đích: verify model học được signal thật (AUROC > 0.5)
    # trước khi chạy cross-subject LTSO
    run(
        config_path="./configs/defaults.yaml",
        experiment_id="E5_within_subject_smoke",
        fold_id="smoke_chb01",
        train_subjects=["chb01"],
        test_subjects=["chb01"])