import os
import torch
import numpy as np
from pathlib import Path
from torch.utils.data import DataLoader, random_split

from configs import ConfigReader
from shared.models import (
    LossHandler,
    OptimizerHandler,
    Trainer,
    ExperimentLogger
)
from shared.services.data import EEGWindowDataset, collate_eeg_graphs
from shared.services.models_hub.gae import GAEModel
from evaluate import run_evaluation


def set_seed(seed=42):
    torch.manual_seed(seed)
    np.random.seed(seed)
    torch.backends.cudnn.deterministic = True


def run(config_path="./configs/defaults.yaml",
        experiment_path=None,
        experiment_id="E5_proposed_gae",
        fold_id="fold_1",
        train_subjects=None,
        test_subjects=None):
    """
    Train GAE on interictal windows of train_subjects.
    Evaluate on test_subjects (held-out LTSO fold).

    Args:
        train_subjects: list of subject IDs for training
        test_subjects:  list of 2 subject IDs held out
    """
    # ── Config ────────────────────────────────────────────────────────────────
    config = ConfigReader.merge(config_path, experiment_path)
    set_seed(config.training.seed)

    logger = ExperimentLogger(log_dir=config.training.log_dir)
    logger.log_config(config_path)
    logger.log_message(f"Starting {experiment_id} | {fold_id}")

    # ── Build dataset from train_subjects ─────────────────────────────────────
    processed_dir = Path(config.data.processed_dir)

    all_windows, all_adjs = [], []
    for subj in train_subjects:
        w = np.load(processed_dir / f"{subj}_interictal_windows.npy")
        a = np.load(processed_dir / f"{subj}_interictal_adjs.npy")
        all_windows.append(w)
        all_adjs.append(a)

    all_windows = np.concatenate(all_windows, axis=0)
    all_adjs    = np.concatenate(all_adjs,    axis=0)

    # Save merged temp files for dataset
    tmp_w = processed_dir / "_tmp_train_windows.npy"
    tmp_a = processed_dir / "_tmp_train_adjs.npy"
    np.save(tmp_w, all_windows)
    np.save(tmp_a, all_adjs)

    full_dataset = EEGWindowDataset(tmp_w, tmp_a)

    # 80/20 train/val split (interictal only — no labels)
    n_val   = int(0.2 * len(full_dataset))
    n_train = len(full_dataset) - n_val
    train_dataset, val_dataset = random_split(
        full_dataset, [n_train, n_val],
        generator=torch.Generator().manual_seed(config.training.seed)
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=config.data.batch_size,
        shuffle=True,
        num_workers=config.data.num_workers,
        collate_fn=collate_eeg_graphs,
        pin_memory=torch.cuda.is_available()
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=config.data.batch_size,
        shuffle=False,
        num_workers=config.data.num_workers,
        collate_fn=collate_eeg_graphs,
        pin_memory=torch.cuda.is_available()
    )

    # ── Model ─────────────────────────────────────────────────────────────────
    model = GAEModel(
        in_channels=config.data.n_channels,
        hidden_dim=config.model.hidden_dim,
        latent_dim=config.model.latent_dim
    )
    model.summary()
    logger.log_model_info(model)

    # ── Handlers ──────────────────────────────────────────────────────────────
    loss_handler = LossHandler(loss_type="graph_bce")

    from shared.models.optimization import OptimizerHandler
    optimizer_handler = OptimizerHandler(
        optimizer_type=config.training.optimizer,
        lr=config.training.lr,
        scheduler_type=config.training.scheduler,
        T_max=config.training.max_epochs
    )

    # ── Train ─────────────────────────────────────────────────────────────────
    checkpoint_dir = Path(config.training.checkpoint_dir) / experiment_id / fold_id
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    trainer = Trainer(
        max_epochs=config.training.max_epochs,
        checkpoint_dir=str(checkpoint_dir),
        experiment_dir=logger.get_experiment_dir()
    )
    lightning_model = trainer.train(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        loss_handler=loss_handler,
        optimizer_handler=optimizer_handler
    )

    # Save weights
    weights_path = checkpoint_dir / "model_weights.pt"
    model.save(str(weights_path))
    logger.log_message(f"Weights saved: {weights_path}")

    # ── Evaluate on held-out test fold ────────────────────────────────────────
    hyperparams = {
        "encoder_layers": config.model.encoder_layers,
        "hidden_dim":     config.model.hidden_dim,
        "latent_dim":     config.model.latent_dim,
        "lr":             config.training.lr,
        "alpha":          config.graph.alpha,
        "top_k_percent":  config.graph.top_k_percent,
        "seed":           config.training.seed
    }

    metrics = run_evaluation(
        model=model,
        subject_ids=test_subjects,
        splits_dir=config.data.splits_dir,
        processed_dir=config.data.processed_dir,
        experiment_id=experiment_id,
        fold_id=fold_id,
        hyperparams=hyperparams,
        results_log_path=config.evaluation.results_log,
        notes=f"train_subjects={train_subjects}"
    )

    logger.log_results(metrics)
    logger.log_message(f"Completed {experiment_id} | {fold_id}")

    # Cleanup tmp files
    tmp_w.unlink(missing_ok=True)
    tmp_a.unlink(missing_ok=True)

    return metrics


if __name__ == "__main__":
    # Smoke test: fold_1 — chb01 + chb02 held out
    TRAIN_SUBJECTS = [f"chb{i:02d}" for i in range(3, 24)]
    TEST_SUBJECTS  = ["chb01", "chb02"]

    run(
        config_path="./configs/defaults.yaml",
        experiment_id="E5_proposed_gae",
        fold_id="fold_1_held_out_chb01_chb02",
        train_subjects=TRAIN_SUBJECTS,
        test_subjects=TEST_SUBJECTS
    )