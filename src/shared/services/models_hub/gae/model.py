import torch
import torch.nn as nn
from torch_geometric.nn import GCNConv
from shared.services.models_hub.base import ModelManager


class GAEEncoder(nn.Module):
    """
    2-layer GCNConv encoder.
    Eq (6) in thesis: H^(l+1) = σ(D̃^{-1/2} Ã D̃^{-1/2} H^(l) W^(l))
    """
    def __init__(self, in_channels, hidden_dim, latent_dim):
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, latent_dim)
        self.relu = nn.ReLU()

    def forward(self, x, edge_index, edge_weight=None):
        z = self.relu(self.conv1(x, edge_index, edge_weight))
        z = self.conv2(z, edge_index, edge_weight)
        return z  # [N_nodes, latent_dim]


class GAEModel(nn.Module, ModelManager):
    """
    Graph Autoencoder for unsupervised seizure detection.

    Encoder: 2-layer GCNConv
    Decoder: inner product  Â_ij = σ(z_i^T z_j)  — Eq (7)
    Loss:    BCE(A, Â)                             — Eq (8)
    Score:   ||A - Â||_F                           — Eq (9)
    """
    def __init__(self, in_channels, hidden_dim=64, latent_dim=16):
        super().__init__()
        self.encoder = GAEEncoder(in_channels, hidden_dim, latent_dim)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x, edge_index, edge_weight=None):
        z = self.encoder(x, edge_index, edge_weight)
        A_hat = self.decode(z)
        return z, A_hat

    def decode(self, z):
        """
        Inner product decoder.
        Â = σ(Z Z^T)  →  [N_nodes, N_nodes]
        """
        return self.sigmoid(torch.mm(z, z.t()))

    def anomaly_score(self, A, A_hat):
        """
        Frobenius norm reconstruction error — Eq (9).
        s(G) = ||A - Â||_F
        """
        return torch.norm(A - A_hat, p='fro').item()

    def summary(self):
        print(self)
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        print(f"Total parameters: {total:,} | Trainable: {trainable:,}")