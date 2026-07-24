"""
trainer.py
==========
Plain PyTorch training loop for GAE with node features.

Training runs for exactly max_epochs epochs (no early stopping).
Best checkpoint is saved throughout and loaded at end of training.
Loss curves are returned for Goal 1 visualization.
"""

import torch
import numpy as np
from pathlib import Path
from torch_geometric.utils import dense_to_sparse


class Trainer:
    def __init__(self, max_epochs: int = 200,
                 checkpoint_dir: str = "./checkpoints/",
                 patience: int = 0):
        """
        Parameters
        ----------
        patience : int
            0 = early stopping disabled (required for E_main).
            > 0 = stop if val_loss does not improve for `patience` epochs.
        """
        self.max_epochs     = max_epochs
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.patience       = patience

    def _compute_batch_loss(self, model, batch, loss_handler, device):
        """
        batch: (A_batch [B,18,18], X_batch [B,18,23])
        Returns mean loss over the batch.
        """
        A_batch, X_batch = batch
        total_loss = 0.0
        B = A_batch.shape[0]
        for i in range(B):
            A = A_batch[i].to(device)
            X = X_batch[i].to(device)
            edge_index, edge_weight = dense_to_sparse(A)
            _, A_hat = model(X, edge_index, edge_weight)
            total_loss = total_loss + loss_handler(A_hat, A)
        return total_loss / B

    def train(self, model, train_loader, val_loader,
              loss_handler, optimizer_handler,
              device: str = "cpu") -> dict:
        model.to(device)
        optimizer = optimizer_handler.get_optimizer(model.parameters())
        scheduler = optimizer_handler.get_scheduler(optimizer)

        best_val_loss  = float("inf")
        best_ckpt_path = self.checkpoint_dir / "best_model.pt"
        no_improve     = 0

        train_loss_curve = []
        val_loss_curve   = []

        for epoch in range(self.max_epochs):
            # -- Train --------------------------------------------------------
            model.train()
            train_losses = []
            for batch in train_loader:
                optimizer.zero_grad()
                loss = self._compute_batch_loss(
                    model, batch, loss_handler, device
                )
                loss.backward()
                optimizer.step()
                train_losses.append(loss.item())

            # -- Validate -----------------------------------------------------
            model.eval()
            val_losses = []
            with torch.no_grad():
                for batch in val_loader:
                    loss = self._compute_batch_loss(
                        model, batch, loss_handler, device
                    )
                    val_losses.append(loss.item())

            train_loss = float(np.mean(train_losses))
            val_loss   = float(np.mean(val_losses))

            train_loss_curve.append(train_loss)
            val_loss_curve.append(val_loss)

            if (epoch + 1) % 10 == 0 or epoch == 0:
                print(f"  Epoch {epoch+1:3d}/{self.max_epochs} | "
                      f"train={train_loss:.4f} | val={val_loss:.4f}")

            # Save best checkpoint
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                torch.save(model.state_dict(), str(best_ckpt_path))
                no_improve = 0
            else:
                no_improve += 1

            # Early stopping — only active when patience > 0
            if self.patience > 0 and no_improve >= self.patience:
                print(f"  Early stopping at epoch {epoch+1}.")
                break

            if scheduler is not None:
                if isinstance(
                    scheduler,
                    torch.optim.lr_scheduler.ReduceLROnPlateau
                ):
                    scheduler.step(val_loss)
                else:
                    scheduler.step()

        # Load best checkpoint at end of training
        model.load_state_dict(
            torch.load(str(best_ckpt_path), map_location=device)
        )
        print(f"  Training complete. Best val_loss={best_val_loss:.4f} loaded.")

        # Collect validation scores for threshold calibration
        model.eval()
        val_scores = []
        with torch.no_grad():
            for batch in val_loader:
                A_batch, X_batch = batch
                for i in range(A_batch.shape[0]):
                    A = A_batch[i].to(device)
                    X = X_batch[i].to(device)
                    edge_index, edge_weight = dense_to_sparse(A)
                    _, A_hat = model(X, edge_index, edge_weight)
                    val_scores.append(model.anomaly_score(A, A_hat))

        return {
            "val_scores":       val_scores,
            "best_val_loss":    best_val_loss,
            "train_loss_curve": train_loss_curve,
            "val_loss_curve":   val_loss_curve,
        }