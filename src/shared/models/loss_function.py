"""
loss_function.py
================
Graph reconstruction loss cho GAE — Eq (8).

Vấn đề với plain BCELoss trên sparse graph:
  Sau top-k% thresholding, adjacency có ~70% zeros.
  Plain BCELoss → model học predict ~0.5 mọi entry
  → loss stuck near log(2) = 0.693, không học được gì.

Fix (Kipf & Welling 2016 GAE paper):
  pos_weight = n_negative / n_positive
  → penalise missed edges nhiều hơn
  → model buộc phải học phân biệt edge vs non-edge
"""

import torch
import torch.nn as nn


class GraphBCELoss:
    """
    Weighted BCE loss cho sparse graph reconstruction.
    pos_weight tự động tính từ adjacency matrix của mỗi graph.
    """

    def __call__(self, A_hat: torch.Tensor,
                 A: torch.Tensor) -> torch.Tensor:
        """
        Args:
            A_hat: reconstructed adjacency [18, 18], values in (0,1)
            A:     target adjacency [18, 18]
        """
        n_pos      = (A > 0).sum().float()
        n_neg      = A.numel() - n_pos
        pos_weight = n_neg / (n_pos + 1e-8)

        weight  = torch.where(A > 0,
                              pos_weight * torch.ones_like(A),
                              torch.ones_like(A))
        loss_fn = nn.BCELoss(weight=weight)
        return loss_fn(A_hat, A)


class LossHandler:
    """
    Loss handler — entry point cho train_pipeline.
    """

    def __init__(self, loss_type: str = "graph_bce"):
        self.loss_type = loss_type
        if loss_type == "graph_bce":
            self.loss_fn = GraphBCELoss()
        elif loss_type == "mse":
            self.loss_fn = nn.MSELoss()
        else:
            raise ValueError(f"Unknown loss type: {loss_type}")

    def __call__(self, A_hat: torch.Tensor,
                 A: torch.Tensor) -> torch.Tensor:
        return self.loss_fn(A_hat, A)