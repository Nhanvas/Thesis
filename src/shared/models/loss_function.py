import torch
import torch.nn as nn


class GraphBCELoss:
    """
    Graph reconstruction loss — Eq (8).
    L = BCE(A, Â) = -[A·log(Â) + (1-A)·log(1-Â)]

    Note: A is sparse (~70% zeros after top-k thresholding).
    pos_weight compensates for edge imbalance within each graph.
    """
    def __init__(self, pos_weight=None):
        self.pos_weight = pos_weight

    def __call__(self, A, A_hat):
        if self.pos_weight is not None:
            loss_fn = nn.BCELoss(weight=self.pos_weight)
        else:
            loss_fn = nn.BCELoss()
        return loss_fn(A_hat, A)


class LossHandler:
    """
    Loss handler — supports graph BCE and standard losses.
    """
    def __init__(self, loss_type="graph_bce", class_weights=None):
        self.loss_type = loss_type

        if loss_type == "graph_bce":
            self.loss_fn = GraphBCELoss(pos_weight=class_weights)
        elif loss_type == "bce":
            self.loss_fn = nn.BCEWithLogitsLoss()
        elif loss_type == "mse":
            self.loss_fn = nn.MSELoss()
        else:
            raise ValueError(f"Unknown loss type: {loss_type}")

    def __call__(self, pred, target):
        return self.loss_fn(pred, target)