"""
dataset.py
==========
Dataset for GAE training.

Node feature design (Kipf & Welling 2016 + domain extension):
    X = concat(A_row_normalized, band_powers_normalized)  [18, 23]

Rationale:
    - X = A_row gives encoder direct access to graph topology.
      Without this, GCNConv has no structural signal in input —
      only edge_weight, which gives very weak gradient.
    - Band powers add per-channel spectral context (5 features).
    - Both normalized to [0,1] range before concat for scale parity.

Input dims: 18 (adjacency row) + 5 (band powers) = 23
"""

import numpy as np
import torch
from torch.utils.data import Dataset


class EEGGraphDataset(Dataset):
    """
    Returns (A, X) where:
        A: [18, 18] weighted adjacency (wPLI, fixed threshold)
        X: [18, 23] node features = concat(A_row_norm, band_power_norm)
    """

    def __init__(self, adjs_path: str, features_path: str):
        self.adjs     = np.load(adjs_path,     mmap_mode="r")
        self.features = np.load(features_path, mmap_mode="r")
        assert len(self.adjs) == len(self.features), (
            f"Length mismatch: {adjs_path} has {len(self.adjs)} "
            f"but {features_path} has {len(self.features)}"
        )

    def __len__(self) -> int:
        return len(self.adjs)

    def __getitem__(self, idx):
        A = self.adjs[idx].astype(np.float32)      # [18, 18]
        B = self.features[idx].astype(np.float32)  # [18, 5]  band powers

        # Normalize A rows to [0, 1] — preserves relative weight, removes
        # subject-level scale differences
        A_max = A.max()
        A_norm = A / (A_max + 1e-8)                # [18, 18]

        # Normalize band powers per window to [0, 1]
        B_min  = B.min(axis=0, keepdims=True)
        B_max  = B.max(axis=0, keepdims=True)
        B_norm = (B - B_min) / (B_max - B_min + 1e-8)  # [18, 5]

        # Concat: each node gets its adjacency row + its band powers
        X = np.concatenate([A_norm, B_norm], axis=1)  # [18, 23]

        return (
            torch.tensor(A,     dtype=torch.float32),
            torch.tensor(X,     dtype=torch.float32),
        )