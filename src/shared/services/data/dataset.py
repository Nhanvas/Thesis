"""
dataset.py
==========
Dataset cho GAE training.

EEGGraphDataset trả về adjacency matrix [18, 18] cho mỗi window.
DataLoader dùng default collate → batch shape [B, 18, 18].
Không dùng PyG Batch — tránh phức tạp hoá việc decode per-graph.
"""

import numpy as np
import torch
from torch.utils.data import Dataset


class EEGGraphDataset(Dataset):
    """
    Load adjacency matrices từ file .npy đã precompute.

    Args:
        adjs_path: path tới chbXX_interictal_adjs.npy  [N, 18, 18]

    Returns per item:
        A: torch.FloatTensor [18, 18]  — adjacency matrix
    """

    def __init__(self, adjs_path: str):
        self.adjs = np.load(adjs_path, mmap_mode="r")  # [N, 18, 18]

    def __len__(self) -> int:
        return len(self.adjs)

    def __getitem__(self, idx) -> torch.Tensor:
        return torch.tensor(
            self.adjs[idx].astype(np.float32))          # [18, 18]