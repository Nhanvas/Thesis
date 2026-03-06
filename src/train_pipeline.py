# Training pipeline.
# Modify for your task.

import torch
from torch.utils.data import DataLoader
import pandas as pd
from configs import ConfigReader
from shared.models import (
    LossHandler,
    MetricHandler,
    OptimizerHandler,
    Trainer,
    ExperimentLogger,
    plot_training_curves
)
from shared.services.data import BaseDataset, Transformer
from shared.services.models_hub import UNet


def run(config_path="./configs/defaults.yml", experiment_path=None):
    # Load config
    config = ConfigReader.merge(config_path, experiment_path)
    
    # Setup logger
    logger = ExperimentLogger(log_dir=config.training.log_dir)
    logger.log_config(config_path)
    logger.log_message("Training started")
    
    # Transform
    transform = Transformer(
        target_size=tuple(config.transform.target_size),
        do_augmentation=config.transform.do_augmentation
    )
    val_transform = Transformer(
        target_size=tuple(config.transform.target_size),
        do_augmentation=False
    )
    
    # Dataset
    train_dataset = BaseDataset(data_dir=config.data.train_dir, transform=transform)
    val_dataset = BaseDataset(data_dir=config.data.val_dir, transform=val_transform)
    
    # DataLoader
    train_loader = DataLoader(
        dataset=train_dataset,
        batch_size=config.data.batch_size,
        shuffle=True,
        num_workers=config.data.num_workers,
        pin_memory=torch.cuda.is_available()
    )
    val_loader = DataLoader(
        dataset=val_dataset,
        batch_size=config.data.batch_size,
        shuffle=False,
        num_workers=config.data.num_workers,
        pin_memory=torch.cuda.is_available()
    )
    
    # Model
    model = UNet(
        n_channels=config.model.n_channels,
        n_classes=config.model.n_classes
    )
    model.summary()
    logger.log_model_info(model)
    
    # Handlers
    loss_handler = LossHandler(loss_type=config.loss.type)
    metric_handler = MetricHandler(
        task=config.metrics.task,
        num_classes=config.metrics.num_classes
    )
    optimizer_handler = OptimizerHandler(
        optimizer_type=config.training.optimizer,
        lr=config.training.lr,
        scheduler_type=config.training.scheduler,
        T_max=config.training.max_epochs
    )
    
    # Train
    trainer = Trainer(
        max_epochs=config.training.max_epochs,
        checkpoint_dir=config.training.checkpoint_dir,
        experiment_dir=logger.get_experiment_dir()
    )
    lightning_model = trainer.train(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        loss_handler=loss_handler,
        metric_handler=metric_handler,
        optimizer_handler=optimizer_handler
    )
    
    # Save model weights
    model.save(config.training.checkpoint_dir + "model_weights.pt")
    
    # Log results
    metrics = pd.read_csv(logger.get_experiment_dir() + "/metrics.csv")
    best_idx = metrics["val_loss"].dropna().idxmin()
    logger.log_results({
        "best_val_loss": float(metrics.loc[best_idx, "val_loss"]),
        "val_acc_at_best": float(metrics.loc[best_idx, "val_acc"])
    })
    logger.log_message("Training completed")
    
    # Plot training curves
    plot_training_curves(
        log_dir=logger.get_experiment_dir(),
        save_dir=logger.get_experiment_dir()
    )


if __name__ == "__main__":
    run(config_path="./configs/defaults.yml")