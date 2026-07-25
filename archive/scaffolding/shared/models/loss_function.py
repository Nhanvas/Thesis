"""
loss_function.py
================
Graph reconstruction loss for GAE — Eq (8).

Two loss options:
  graph_bce: Weighted BCE (Kipf & Welling 2016).
             Works when adjacency is binary (0/1).
             BROKEN for weighted adjacency: pos_weight becomes ~1.0
             for weighted values 0.1-0.4, model predicts mean everywhere.

  graph_mse: Mean Squared Error on weighted adjacency values.
             Works when adjacency retains continuous wPLI+AEC weights.
             Penalises deviation from true connectivity strength directly.
             Use this when top-k thresholding is removed.

Current plan: graph_mse with fixed-threshold weighted adjacency.
"""

import torch
import torch.nn as nn


class GraphBCELoss:
    """
    Weighted BCE loss for sparse binary graph reconstruction.
    pos_weight = n_negative / n_positive (Kipf & Welling 2016).

    Only use when adjacency target is binary (0 or 1).
    Do NOT use with weighted adjacency — pos_weight loses meaning.
    """

    def __call__(self, A_hat: torch.Tensor,
                 A: torch.Tensor) -> torch.Tensor:
        """
        Args:
            A_hat: reconstructed adjacency [18, 18], values in (0, 1)
            A:     target adjacency [18, 18], binary (0 or 1)
        """
        n_pos      = (A > 0).sum().float()
        n_neg      = A.numel() - n_pos
        pos_weight = n_neg / (n_pos + 1e-8)

        weight  = torch.where(A > 0,
                              pos_weight * torch.ones_like(A),
                              torch.ones_like(A))
        loss_fn = nn.BCELoss(weight=weight)
        return loss_fn(A_hat, A)


class GraphMSELoss:
    """
    MSE loss for weighted graph reconstruction.

    Directly penalises deviation in connectivity strength values.
    When ictal connectivity differs from interictal (wPLI+AEC values
    change), MSE loss captures this as increased reconstruction error.

    This is the correct loss when:
      - Adjacency values are continuous (wPLI+AEC combined, 0.0-1.0)
      - Fixed minimum threshold is used (not top-k%)
      - Signal is in the strength of connections, not just presence/absence
    """

    def __init__(self):
        self.loss_fn = nn.MSELoss()

    def __call__(self, A_hat: torch.Tensor,
                 A: torch.Tensor) -> torch.Tensor:
        """
        Args:
            A_hat: reconstructed adjacency [18, 18], values in (0, 1)
            A:     target weighted adjacency [18, 18], values in [0, 1]
        """
        return self.loss_fn(A_hat, A)


class LossHandler:
    """
    Loss handler — entry point for train_pipeline.

    loss_type options:
      "graph_mse": MSE on weighted adjacency (default, use with fixed threshold)
      "graph_bce": Weighted BCE (use only with binary adjacency)
      "mse":       Plain MSE (alias for graph_mse)
    """

    def __init__(self, loss_type: str = "graph_mse"):
        self.loss_type = loss_type
        if loss_type in ("graph_mse", "mse"):
            self.loss_fn = GraphMSELoss()
        elif loss_type == "graph_bce":
            self.loss_fn = GraphBCELoss()
        else:
            raise ValueError(
                f"Unknown loss type: {loss_type}. "
                f"Use 'graph_mse' or 'graph_bce'."
            )

    def __call__(self, A_hat: torch.Tensor,
                 A: torch.Tensor) -> torch.Tensor:
        return self.loss_fn(A_hat, A)