"""
optimization.py
===============
Optimizer and learning rate scheduler.
"""

import torch
import torch.optim as optim


class OptimizerHandler:
    """
    Builds optimizer and scheduler from config strings.

    Supported optimizers: adam, adamw, sgd
    Supported schedulers: cosine, plateau, None
    """

    def __init__(self, optimizer_type: str = "adam",
                 lr: float = 1e-3,
                 weight_decay: float = 0.0,
                 scheduler_type: str = None,
                 **scheduler_kwargs):
        self.optimizer_type  = optimizer_type
        self.lr              = lr
        self.weight_decay    = weight_decay
        self.scheduler_type  = scheduler_type
        self.scheduler_kwargs = scheduler_kwargs

    def get_optimizer(self, model_parameters) -> optim.Optimizer:
        if self.optimizer_type == "adam":
            return optim.Adam(
                model_parameters, lr=self.lr,
                weight_decay=self.weight_decay)
        elif self.optimizer_type == "adamw":
            return optim.AdamW(
                model_parameters, lr=self.lr,
                weight_decay=self.weight_decay)
        elif self.optimizer_type == "sgd":
            return optim.SGD(
                model_parameters, lr=self.lr,
                momentum=0.9,
                weight_decay=self.weight_decay)
        else:
            raise ValueError(
                f"Unknown optimizer: {self.optimizer_type}. "
                f"Use 'adam', 'adamw', or 'sgd'.")

    def get_scheduler(self, optimizer: optim.Optimizer):
        if self.scheduler_type is None:
            return None
        elif self.scheduler_type == "cosine":
            T_max = self.scheduler_kwargs.get("T_max", 100)
            return optim.lr_scheduler.CosineAnnealingLR(
                optimizer, T_max=T_max)
        elif self.scheduler_type == "plateau":
            patience = self.scheduler_kwargs.get("patience", 5)
            return optim.lr_scheduler.ReduceLROnPlateau(
                optimizer, mode="min", patience=patience)
        else:
            raise ValueError(
                f"Unknown scheduler: {self.scheduler_type}. "
                f"Use 'cosine', 'plateau', or None.")