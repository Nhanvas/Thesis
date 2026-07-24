"""
run_main.py
===========
E_main experiment entry point.

Usage (from project root with venv activated):
    python run_main.py

Prerequisites:
  1. src/create_splits.py has been run once -> data/splits/split_main.json exists
  2. build_graphs pipeline has been run for all 23 subjects with alpha=0.5
     -> data/processed/{subj}_interictal_adjs.npy and _features.npy exist
     (Delete old cached .npy files if they were built with alpha=1.0)

What this does:
  - Loads the fixed 15-train / 8-test split (seed=42)
  - Trains GAE on interictal windows from 15 training subjects, 200 epochs
  - Evaluates on 8 held-out test subjects
  - Saves: loss curves, model weights, per-subject metrics to results/
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from train_pipeline import run

SPLIT_PATH  = Path("./data/splits/split_main.json")
CONFIG_PATH = "./src/configs/defaults.yaml"


if __name__ == "__main__":
    if not SPLIT_PATH.exists():
        raise FileNotFoundError(
            f"Split file not found: {SPLIT_PATH}\n"
            f"Run first: python src/create_splits.py"
        )

    split = json.loads(SPLIT_PATH.read_text())

    print("=" * 60)
    print("E_main: Full pipeline — wPLI+AEC combined, alpha=0.5")
    print(f"Train subjects ({split['n_train']}): {split['train']}")
    print(f"Test  subjects ({split['n_test']}):  {split['test']}")
    print(f"Seed: {split['seed']}")
    print("=" * 60)

    metrics = run(
        config_path=CONFIG_PATH,
        experiment_id="E_main",
        train_subjects=split["train"],
        test_subjects=split["test"],
    )

    print("\n" + "=" * 60)
    print("E_main FINAL RESULTS:")
    print(f"  AUROC:       {metrics.get('auroc', 'N/A'):.4f}")
    print(f"  Sensitivity: {metrics.get('sensitivity', 'N/A'):.4f}")
    print(f"  FDR/h:       {metrics.get('fdr_per_hour', 'N/A'):.2f}")
    print("=" * 60)