"""
gae_model.py
============
Graph Autoencoder for unsupervised seizure detection — Eq (5)-(9).

Architecture:
    Encoder: 2-layer GCNConv  X,A → Z ∈ R^{18 × d_latent}   Eq (6)
    Decoder: inner product    Z   → Â ∈ R^{18 × 18}          Eq (7)
    Loss:    MSE(A, Â)                                         Eq (8)
    Score:   ||A - Â||_F  (Frobenius norm)                    Eq (9)

Node features (input_dim=23):
    X = concat(A_row_normalized [18], band_powers_normalized [5])
    Kipf & Welling (2016): using adjacency rows as node features gives
    encoder direct structural signal. Band powers add spectral context.
"""

import torch
import torch.nn as nn
from torch_geometric.nn import GCNConv
from torch_geometric.utils import dense_to_sparse


class GAEEncoder(nn.Module):
    def __init__(self, input_dim: int = 23,
                 hidden_dim: int = 64,
                 latent_dim: int = 16):
        super().__init__()
        self.conv1 = GCNConv(input_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, latent_dim)
        self.relu  = nn.ReLU()

    def forward(self, x, edge_index, edge_weight=None):
        """
        GCN propagation — Eq (6):
            H^(l+1) = σ( D̃^{-1/2} Ã D̃^{-1/2} H^(l) W^(l) )
        """
        h = self.relu(self.conv1(x, edge_index, edge_weight))
        z = self.conv2(h, edge_index, edge_weight)
        return z


class GAEModel(nn.Module):
    def __init__(self, input_dim: int = 23,
                 hidden_dim: int = 64,
                 latent_dim: int = 16):
        super().__init__()
        self.encoder = GAEEncoder(input_dim, hidden_dim, latent_dim)
        # No sigmoid — use clamped linear decoder to avoid vanishing gradients.
        # sigmoid(ZZ^T) squashes gradients when outputs are near 0/1,
        # causing loss to plateau at the mean-prediction solution.

    def forward(self, x, edge_index, edge_weight=None):
        z     = self.encoder(x, edge_index, edge_weight)
        # Linear inner product decoder — Eq (7)
        # Clamp to [0,1] to match adjacency value range
        A_hat = torch.clamp(torch.mm(z, z.t()), 0.0, 1.0)
        return z, A_hat

    def anomaly_score(self, A, A_hat):
        """Frobenius norm — Eq (9). s(G) = ||A - Â||_F"""
        return torch.norm(A - A_hat, p='fro').item()

    def summary(self):
        print(self)
        total     = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters()
                        if p.requires_grad)
        print(f"Total parameters: {total:,} | Trainable: {trainable:,}")