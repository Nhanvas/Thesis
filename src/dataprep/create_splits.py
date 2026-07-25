"""
create_splits.py
================
Generate a single fixed 15-train / 8-test subject split for E_main.

Rules (proposed_solution_updated.md §I):
  - 23 subjects total: chb01 through chb23
  - 15 randomly selected for training (interictal windows only)
  - 8 held out for testing (never touched during training or threshold calibration)
  - Seed = 42, fixed permanently
  - Split is written once to split_main.json and NEVER regenerated

Output: data/splits/split_main.json

IMPORTANT: Run this script exactly ONCE before E_main.
Do not re-run after the experiment has started.
"""

import json
import random
from pathlib import Path

SUBJECTS   = [f"chb{i:02d}" for i in range(1, 24)]   # chb01..chb23
SEED       = 42
N_TEST     = 8
SPLITS_DIR = Path("../data/splits")
OUTPUT     = SPLITS_DIR / "split_main.json"


def main():
    # Guard: do not overwrite existing split
    if OUTPUT.exists():
        existing = json.loads(OUTPUT.read_text())
        print(f"[INFO] {OUTPUT} already exists. Not overwriting.")
        print(f"  Train ({existing['n_train']}): {existing['train']}")
        print(f"  Test  ({existing['n_test']}):  {existing['test']}")
        print("Delete the file manually if you need to regenerate.")
        return

    SPLITS_DIR.mkdir(parents=True, exist_ok=True)

    rng = random.Random(SEED)
    subjects_shuffled = SUBJECTS.copy()
    rng.shuffle(subjects_shuffled)

    test_subjects  = sorted(subjects_shuffled[:N_TEST])
    train_subjects = sorted(subjects_shuffled[N_TEST:])

    assert len(train_subjects) == 15, f"Expected 15 train, got {len(train_subjects)}"
    assert len(test_subjects)  == 8,  f"Expected 8 test, got {len(test_subjects)}"
    assert set(train_subjects) | set(test_subjects) == set(SUBJECTS)
    assert set(train_subjects) & set(test_subjects) == set()

    split = {
        "seed":    SEED,
        "train":   train_subjects,
        "test":    test_subjects,
        "n_train": len(train_subjects),
        "n_test":  len(test_subjects),
    }

    OUTPUT.write_text(json.dumps(split, indent=2))

    print(f"Split saved: {OUTPUT.resolve()}")
    print(f"Train ({len(train_subjects)}): {train_subjects}")
    print(f"Test  ({len(test_subjects)}):  {test_subjects}")
    print()
    print("IMPORTANT: This split is now fixed. Do not re-run this script.")


if __name__ == "__main__":
    main()