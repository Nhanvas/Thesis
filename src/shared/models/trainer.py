"""
trainer.py
==========
Plain PyTorch training loop for GAE with node features.
"""

import torch
import numpy as np
from pathlib import Path
from torch_geometric.utils import dense_to_sparse


class Trainer:
    def __init__(self, max_epochs: int = 100,
                 checkpoint_dir: str = "./checkpoints/",
                 patience: int = 10,
                 **kwargs):
        self.max_epochs = max_epochs
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.patience = patience

    def _compute_batch_loss(self, model, batch, loss_handler, device):
        """
        batch: tuple (A_batch, X_batch)
            A_batch: [B, 18, 18]  weighted adjacency
            X_batch: [B, 18, 23]  node features = concat(A_row_norm, band_powers_norm)
        """
        A_batch, X_batch = batch
        total_loss = 0.0
        B = A_batch.shape[0]
        for i in range(B):
            A = A_batch[i].to(device)
            X = X_batch[i].to(device)
            edge_index, edge_weight = dense_to_sparse(A)
            _, A_hat = model(X, edge_index, edge_weight)
            # Train on weighted adjacency — preserves connectivity strength signal
            # Binary targets lose ictal/interictal difference after top-k threshold
            total_loss = total_loss + loss_handler(A_hat, A)
        return total_loss / B

    def train(self, model, train_loader, val_loader,
              loss_handler, optimizer_handler,
              device: str = "cpu") -> dict:
        model.to(device)
        optimizer = optimizer_handler.get_optimizer(model.parameters())
        scheduler = optimizer_handler.get_scheduler(optimizer)

        best_val_loss = float("inf")
        best_ckpt_path = self.checkpoint_dir / "best_model.pt"
        no_improve = 0

        for epoch in range(self.max_epochs):
            # ── Train ─────────────────────────────────────────────────────────
            model.train()
            train_losses = []
            for batch in train_loader:
                optimizer.zero_grad()
                loss = self._compute_batch_loss(model, batch, loss_handler, device)
                loss.backward()
                optimizer.step()
                train_losses.append(loss.item())

            # ── Validate ──────────────────────────────────────────────────────
            model.eval()
            val_losses = []
            with torch.no_grad():
                for batch in val_loader:
                    loss = self._compute_batch_loss(model, batch, loss_handler, device)
                    val_losses.append(loss.item())

            train_loss = float(np.mean(train_losses))
            val_loss = float(np.mean(val_losses))

            if (epoch + 1) % 10 == 0 or epoch == 0:
                print(f"  Epoch {epoch+1:3d}/{self.max_epochs} | "
                      f"train_loss={train_loss:.4f} | val_loss={val_loss:.4f}")

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                torch.save(model.state_dict(), str(best_ckpt_path))
                no_improve = 0
            else:
                no_improve += 1

            if scheduler is not None:
                if isinstance(scheduler, torch.optim.lr_scheduler.ReduceLROnPlateau):
                    scheduler.step(val_loss)
                else:
                    scheduler.step()

            if self.patience > 0 and no_improve >= self.patience:
                print(f"  Early stopping at epoch {epoch+1}")
                break

        model.load_state_dict(torch.load(str(best_ckpt_path), map_location=device))
        print(f"  Best val_loss={best_val_loss:.4f} loaded.")

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

        return {"val_scores": val_scores, "best_val_loss": best_val_loss}