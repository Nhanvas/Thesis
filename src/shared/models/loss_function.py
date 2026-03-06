import torch.nn as nn

class LossHandler:
    """
    Loss function handler.
    Modify this for your task.
    """
    def __init__(self, loss_type="cross_entropy", class_weights=None):
        # Common losses:
        # cross_entropy  - classification
        # bce            - binary classification
        # mse            - regression
        self.loss_type = loss_type
        
        if loss_type == "cross_entropy":
            self.loss_fn = nn.CrossEntropyLoss(weight=class_weights)
        elif loss_type == "bce":
            self.loss_fn = nn.BCEWithLogitsLoss()
        elif loss_type == "mse":
            self.loss_fn = nn.MSELoss()
        else:
            raise ValueError(f"Unknown loss type: {loss_type}")
    
    def __call__(self, pred, target):
        return self.loss_fn(pred, target)