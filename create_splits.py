"""
create_splits.py
================
Tạo 11 LTSO fold index files cho 23 subjects CHB-MIT.
Pairing: (chb01,chb02), (chb03,chb04), ..., (chb21,chb22), (chb23 solo)
Output: data/splits/fold_01_train.json, fold_01_test.json, ...
"""
import json
from pathlib import Path

SUBJECTS = [f"chb{i:02d}" for i in range(1, 24)]
SPLITS_DIR = Path("data/splits")
SPLITS_DIR.mkdir(parents=True, exist_ok=True)

# 11 folds: 10 pairs + 1 solo
test_groups = [
    ["chb01", "chb02"],
    ["chb03", "chb04"],
    ["chb05", "chb06"],
    ["chb07", "chb08"],
    ["chb09", "chb10"],
    ["chb11", "chb12"],
    ["chb13", "chb14"],
    ["chb15", "chb16"],
    ["chb17", "chb18"],
    ["chb19", "chb20"],
    ["chb21", "chb22", "chb23"],
]

for fold_num, test_subjs in enumerate(test_groups, start=1):
    train_subjs = [s for s in SUBJECTS if s not in test_subjs]
    fold_id = f"fold_{fold_num:02d}"
    
    (SPLITS_DIR / f"{fold_id}_test.json").write_text(
        json.dumps(test_subjs, indent=2))
    (SPLITS_DIR / f"{fold_id}_train.json").write_text(
        json.dumps(train_subjs, indent=2))
    
    print(f"{fold_id}: test={test_subjs} | train={len(train_subjs)} subjects")

print(f"\nDone. {len(test_groups)} folds saved to {SPLITS_DIR}/")
