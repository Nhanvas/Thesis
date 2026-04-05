"""
build_graphs.py
===============
Compute adjacency matrices from preprocessed EEG windows.
Run once after preprocessing.py completes.

Input:  chbXX_interictal.npy  [N, 18, 1024]  float32
        chbXX_ictal.npy        [M, 18, 1024]  float32
Output: chbXX_interictal_adjs.npy  [N, 18, 18]  float32
        chbXX_ictal_adjs.npy       [M, 18, 18]  float32
"""

import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from graph_construction import build_adjacency


def build_subject_graphs(subject_id: str,
                         processed_dir: Path,
                         alpha: float = 0.5,
                         top_k_percent: float = 30) -> None:
    """
    Compute and save adjacency matrices for one subject.
    Uses memmap writes — peak RAM = one window = ~0.15 MB.
    """
    inter_in  = processed_dir / f"{subject_id}_interictal.npy"
    ictal_in  = processed_dir / f"{subject_id}_ictal.npy"
    inter_out = processed_dir / f"{subject_id}_interictal_adjs.npy"
    ictal_out = processed_dir / f"{subject_id}_ictal_adjs.npy"

    if not inter_in.exists():
        raise FileNotFoundError(
            f"Missing: {inter_in}\nRun preprocessing.py first.")

    # ── Interictal ────────────────────────────────────────────────────────────
    windows = np.load(str(inter_in), mmap_mode="r")  # [N, 18, 1024]
    N = windows.shape[0]
    print(f"  [{subject_id}] interictal adjs: {N} windows...")

    mm = np.lib.format.open_memmap(
        str(inter_out), mode="w+",
        dtype=np.float32, shape=(N, 18, 18))

    for i in range(N):
        mm[i] = build_adjacency(
            windows[i].astype(np.float64),
            alpha=alpha,
            top_k_percent=top_k_percent)
        if (i + 1) % 2000 == 0:
            print(f"    {i+1}/{N}", end="\r")

    del mm
    print(f"  [{subject_id}] interictal adjs saved.")

    # ── Ictal ─────────────────────────────────────────────────────────────────
    if not ictal_in.exists():
        print(f"  [{subject_id}] no ictal file — skipping")
        return

    windows = np.load(str(ictal_in), mmap_mode="r")  # [M, 18, 1024]
    M = windows.shape[0]
    print(f"  [{subject_id}] ictal adjs: {M} windows...")

    mm = np.lib.format.open_memmap(
        str(ictal_out), mode="w+",
        dtype=np.float32, shape=(M, 18, 18))

    for i in range(M):
        mm[i] = build_adjacency(
            windows[i].astype(np.float64),
            alpha=alpha,
            top_k_percent=top_k_percent)

    del mm
    print(f"  [{subject_id}] ictal adjs saved.")


if __name__ == "__main__":
    PROCESSED_DIR = Path("F:/Study/Thesis/Code/data/processed")
    SUBJECTS      = [f"chb{i:02d}" for i in range(1, 24)]

    for subj in SUBJECTS:
        if not (PROCESSED_DIR / f"{subj}_interictal.npy").exists():
            print(f"[SKIP] {subj} — not preprocessed yet")
            continue
        print(f"\nProcessing {subj}...")
        try:
            build_subject_graphs(subj, PROCESSED_DIR)
        except Exception as e:
            print(f"  [ERROR] {subj}: {e}")

    print("\n=== GRAPH CONSTRUCTION COMPLETE ===")