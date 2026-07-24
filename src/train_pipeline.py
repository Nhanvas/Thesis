"""
train_pipeline.py
=================
Train GAE on interictal data — E_main pipeline.

Split  : 15 subjects for training, 8 subjects held out for testing.
Epochs : 200 fixed, no early stopping.
Threshold: 95th percentile of interictal validation scores.
"""

import sys
import json
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
        experiment_id: str = "E_main",
        train_subjects: list = None,
        test_subjects: list = None,
        seed_override: int = None) -> dict:
    """
    Full training and evaluation pipeline.

    Parameters
    ----------
    train_subjects : list[str]
        Subject IDs used for training (interictal windows only).
        Model never sees any data from test_subjects.
    test_subjects : list[str]
        Subject IDs held out for final evaluation.
    """
    if train_subjects is None or test_subjects is None:
        raise ValueError("train_subjects and test_subjects must be provided.")

    config = ConfigReader.merge(config_path, experiment_path)
    seed   = seed_override if seed_override is not None else config.training.seed
    set_seed(seed)

    device = "cuda" if torch.cuda.is_available() else "cpu"

    logger = ExperimentLogger(log_dir=config.training.log_dir)
    logger.log_message(f"Experiment: {experiment_id} | device={device} | seed={seed}")
    logger.log_message(f"Train ({len(train_subjects)}): {train_subjects}")
    logger.log_message(f"Test  ({len(test_subjects)}):  {test_subjects}")

    processed_dir = Path(config.data.processed_dir)

    # -- Build dataset from interictal windows of training subjects -----------
    datasets = []
    for subj in train_subjects:
        adjs_path  = processed_dir / f"{subj}_interictal_adjs.npy"
        feats_path = processed_dir / f"{subj}_interictal_features.npy"
        if not adjs_path.exists() or not feats_path.exists():
            raise FileNotFoundError(
                f"Missing cached data for {subj}.\n"
                f"Expected: {adjs_path}\n"
                f"Run build_graphs pipeline first."
            )
        datasets.append(EEGGraphDataset(str(adjs_path), str(feats_path)))

    full_dataset = ConcatDataset(datasets)
    n_total = len(full_dataset)
    n_val   = max(1, int(0.2 * n_total))
    n_train = n_total - n_val

    logger.log_message(
        f"Interictal windows: total={n_total} | train={n_train} | val={n_val}"
    )

    train_ds, val_ds = random_split(
        full_dataset, [n_train, n_val],
        generator=torch.Generator().manual_seed(seed)
    )

    train_loader = DataLoader(
        train_ds, batch_size=config.data.batch_size,
        shuffle=True, num_workers=0, pin_memory=False
    )
    val_loader = DataLoader(
        val_ds, batch_size=config.data.batch_size,
        shuffle=False, num_workers=0, pin_memory=False
    )

    # -- Model ----------------------------------------------------------------
    model = GAEModel(
        input_dim=23,
        hidden_dim=config.model.hidden_dim,
        latent_dim=config.model.latent_dim,
    )
    model.summary()
    logger.log_model_info(model)

    # -- Training -------------------------------------------------------------
    loss_handler = LossHandler(loss_type="graph_mse")

    optimizer_handler = OptimizerHandler(
        optimizer_type=config.training.optimizer,
        lr=config.training.lr,
        scheduler_type=config.training.scheduler,
        T_max=config.training.max_epochs
    )

    checkpoint_dir = Path(config.training.checkpoint_dir) / experiment_id
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    trainer = Trainer(
        max_epochs=config.training.max_epochs,
        checkpoint_dir=str(checkpoint_dir),
        patience=0        # No early stopping — fixed epochs per plan
    )

    train_result = trainer.train(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        loss_handler=loss_handler,
        optimizer_handler=optimizer_handler,
        device=device
    )

    # Save model weights
    weights_path = checkpoint_dir / "model_weights.pt"
    torch.save(model.state_dict(), str(weights_path))
    logger.log_message(f"Weights saved: {weights_path}")

    # Save loss curves (needed for Goal 1 deliverable)
    curves_path = checkpoint_dir / "loss_curves.npz"
    np.savez(
        str(curves_path),
        train=np.array(train_result["train_loss_curve"]),
        val=np.array(train_result["val_loss_curve"])
    )
    logger.log_message(f"Loss curves saved: {curves_path}")

    # -- Threshold calibration from val interictal scores --------------------
    metric_handler = MetricHandler(
        threshold_percentile=config.anomaly.threshold_percentile
    )
    threshold = metric_handler.calibrate_threshold(
        np.array(train_result["val_scores"])
    )
    logger.log_message(
        f"Threshold ({config.anomaly.threshold_percentile}th percentile "
        f"of interictal val scores): {threshold:.4f}"
    )

    # -- Evaluation on held-out test subjects --------------------------------
    hyperparams = {
        "hidden_dim":  config.model.hidden_dim,
        "latent_dim":  config.model.latent_dim,
        "lr":          config.training.lr,
        "alpha":       config.graph.alpha,
        "loss":        "graph_mse",
        "seed":        seed,
        "threshold":   round(threshold, 4),
        "max_epochs":  config.training.max_epochs,
        "patience":    0,
    }

    metrics = run_evaluation(
        model=model,
        subject_ids=test_subjects,
        processed_dir=str(processed_dir),
        threshold=threshold,
        experiment_id=experiment_id,
        fold_id="main",
        hyperparams=hyperparams,
        results_log_path=config.evaluation.results_log,
        device=device,
        notes=f"train={train_subjects}"
    )

    logger.log_results(metrics)
    logger.log_message(f"Finished: {experiment_id}")
    return metrics


if __name__ == "__main__":
    split_path = Path("../data/splits/split_main.json")
    if not split_path.exists():
        raise FileNotFoundError(
            f"Split not found: {split_path}\n"
            f"Run src/create_splits.py first."
        )
    split = json.loads(split_path.read_text())
    run(
        experiment_id="E_main",
        train_subjects=split["train"],
        test_subjects=split["test"],
    )