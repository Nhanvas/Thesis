"""
trainer.py
==========
Plain PyTorch training loop cho GAE unsupervised.

Tại sao không dùng PyG Batch:
  Inner product decoder Z·Z^T phải được tính PER GRAPH.
  Với PyG Batch, Z có shape [B*18, latent_dim] — decoder sẽ tính
  cross-graph similarities, đây là sai về mặt kỹ thuật.
  Giải pháp sạch nhất: iterate qua từng graph trong batch.

Training loop:
  - Mỗi epoch: iterate over batches [B, 18, 18]
  - Mỗi batch: iterate qua B graphs, compute loss per graph
  - Save checkpoint tại epoch có val_loss thấp nhất
"""

import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
from torch_geometric.utils import dense_to_sparse


class Trainer:
    """
    Plain PyTorch trainer cho GAE.

    Args:
        max_epochs:      số epochs training
        checkpoint_dir:  thư mục lưu best model weights
        patience:        early stopping patience (0 = disable)
    """

    def __init__(self, max_epochs: int = 100,
                 checkpoint_dir: str = "./checkpoints/",
                 patience: int = 10,
                 **kwargs):          # absorb extra kwargs from config
        self.max_epochs     = max_epochs
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.patience       = patience

    def _compute_batch_loss(self, model, A_batch, loss_fn, device):
        """
        Compute mean loss over one batch of adjacency matrices.
        Processes each graph independently to ensure correct
        per-graph inner product decoding.

        Args:
            A_batch: [B, 18, 18] float tensor
        Returns:
            scalar loss tensor
        """
        total_loss = torch.tensor(0.0, device=device,
                                  requires_grad=True)
        B = A_batch.shape[0]
        for i in range(B):
            A = A_batch[i].to(device)           # [18, 18]
            x = A.clone()                        # node features = adjacency row
            edge_index, edge_weight = dense_to_sparse(A)
            _, A_hat = model(x, edge_index, edge_weight)
            total_loss = total_loss + loss_fn(A_hat, A)

        return total_loss / B

    def train(self, model, train_loader, val_loader,
              loss_handler, optimizer_handler,
              device: str = "cpu") -> dict:
        """
        Train GAE and return val_scores from best epoch
        for threshold calibration.

        Returns:
            dict with keys: 'val_scores' (list of anomaly scores
            from final val pass), 'best_val_loss'
        """
        model.to(device)
        optimizer = optimizer_handler.get_optimizer(model.parameters())
        scheduler = optimizer_handler.get_scheduler(optimizer)

        best_val_loss  = float("inf")
        best_ckpt_path = self.checkpoint_dir / "best_model.pt"
        no_improve     = 0

        loss_fn = nn.BCELoss()   # BCELoss(prediction, target)

        for epoch in range(self.max_epochs):
            # ── Train ─────────────────────────────────────────────────────────
            model.train()
            train_losses = []
            for A_batch in train_loader:
                optimizer.zero_grad()
                loss = self._compute_batch_loss(
                    model, A_batch, loss_fn, device)
                loss.backward()
                optimizer.step()
                train_losses.append(loss.item())

            # ── Validate ──────────────────────────────────────────────────────
            model.eval()
            val_losses = []
            with torch.no_grad():
                for A_batch in val_loader:
                    loss = self._compute_batch_loss(
                        model, A_batch, loss_fn, device)
                    val_losses.append(loss.item())

            train_loss = float(np.mean(train_losses))
            val_loss   = float(np.mean(val_losses))

            if (epoch + 1) % 10 == 0 or epoch == 0:
                print(f"  Epoch {epoch+1:3d}/{self.max_epochs} | "
                      f"train_loss={train_loss:.4f} | "
                      f"val_loss={val_loss:.4f}")

            # ── Checkpoint ────────────────────────────────────────────────────
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                torch.save(model.state_dict(), str(best_ckpt_path))
                no_improve = 0
            else:
                no_improve += 1

            # ── Scheduler ─────────────────────────────────────────────────────
            if scheduler is not None:
                if hasattr(scheduler, "step"):
                    scheduler.step()

            # ── Early stopping ────────────────────────────────────────────────
            if self.patience > 0 and no_improve >= self.patience:
                print(f"  Early stopping at epoch {epoch+1} "
                      f"(no improvement for {self.patience} epochs)")
                break

        # Load best weights
        model.load_state_dict(
            torch.load(str(best_ckpt_path), map_location=device))
        print(f"  Best val_loss={best_val_loss:.4f} — "
              f"weights loaded from {best_ckpt_path.name}")

        # Collect val scores from best model for threshold calibration
        model.eval()
        val_scores = []
        with torch.no_grad():
            for A_batch in val_loader:
                for i in range(A_batch.shape[0]):
                    A = A_batch[i].to(device)
                    x = A.clone()
                    edge_index, edge_weight = dense_to_sparse(A)
                    _, A_hat = model(x, edge_index, edge_weight)
                    score = model.anomaly_score(A, A_hat)
                    val_scores.append(score)

        return {
            "val_scores":    val_scores,
            "best_val_loss": best_val_loss,
        }