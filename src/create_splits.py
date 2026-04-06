"""
create_splits.py
================
Generate LTSO (Leave-Two-Subjects-Out) fold indices for 23 CHB-MIT subjects.

11 folds:
  Fold 01: test = [chb01, chb02]
  Fold 02: test = [chb03, chb04]
  ...
  Fold 10: test = [chb19, chb20]
  Fold 11: test = [chb21, chb22, chb23]   ← 3 subjects (23 is odd)

Output: data/splits/fold_XX_test.json  (list of subject IDs held out)
        data/splits/fold_XX_train.json (list of subject IDs used for training)
        data/splits/splits_summary.json (overview of all folds)
"""

import json
from pathlib import Path

SUBJECTS = [f"chb{i:02d}" for i in range(1, 24)]  # chb01..chb23
SPLITS_DIR = Path("../data/splits")
SPLITS_DIR.mkdir(parents=True, exist_ok=True)

# Build 11 folds
folds = []
for i in range(10):
    test = [SUBJECTS[2*i], SUBJECTS[2*i + 1]]
    folds.append(test)
folds.append([SUBJECTS[20], SUBJECTS[21], SUBJECTS[22]])  # fold 11

# Write per-fold files + summary
summary = {}
for fold_idx, test_subjects in enumerate(folds, start=1):
    fold_id = f"fold_{fold_idx:02d}"
    train_subjects = [s for s in SUBJECTS if s not in test_subjects]

    test_path  = SPLITS_DIR / f"{fold_id}_test.json"
    train_path = SPLITS_DIR / f"{fold_id}_train.json"

    test_path.write_text(json.dumps(test_subjects, indent=2))
    train_path.write_text(json.dumps(train_subjects, indent=2))

    summary[fold_id] = {
        "test":  test_subjects,
        "train": train_subjects,
        "n_test":  len(test_subjects),
        "n_train": len(train_subjects),
    }
    print(f"[{fold_id}] test={test_subjects} | train={len(train_subjects)} subjects")

(SPLITS_DIR / "splits_summary.json").write_text(json.dumps(summary, indent=2))
print(f"\nSaved {len(folds)} folds to {SPLITS_DIR.resolve()}")
