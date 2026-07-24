"""
verify_preprocessing.py
=======================
Kiểm tra output của preprocessing.py cho tất cả 23 subjects.
Chạy: python verify_preprocessing.py

Checks:
  1. Cả 2 file (_interictal.npy, _ictal.npy) tồn tại
  2. Shape đúng: [N, 18, 1024]
  3. Không có NaN hoặc Inf trong sample windows
  4. In tổng số windows và dung lượng
"""

import numpy as np
from pathlib import Path

PROCESSED_DIR = Path("F:/Study/Thesis/Code/data/processed")
ALL_SUBJECTS  = [f"chb{i:02d}" for i in range(1, 24)]

TRAIN_SUBJS = ["chb01","chb02","chb04","chb05","chb07","chb08",
               "chb09","chb12","chb19","chb20","chb21","chb23"]
VAL_SUBJS   = ["chb10","chb11","chb22"]
TEST_SUBJS  = ["chb03","chb06","chb13","chb14","chb15","chb16","chb17","chb18"]

def get_role(subj):
    if subj in TRAIN_SUBJS: return "train"
    if subj in VAL_SUBJS:   return "val"
    if subj in TEST_SUBJS:  return "test"
    return "?"

print("=" * 90)
print(f"{'Subject':<8} {'Role':<6} {'Inter windows':>14} {'Ictal windows':>13} "
      f"{'Inter MB':>9} {'Ictal MB':>9} {'NaN?':>6} {'Status':>8}")
print("-" * 90)

missing     = []
shape_errors = []
nan_errors   = []
total_inter  = 0
total_ictal  = 0

for subj in ALL_SUBJECTS:
    inter_path = PROCESSED_DIR / f"{subj}_interictal.npy"
    ictal_path = PROCESSED_DIR / f"{subj}_ictal.npy"
    role       = get_role(subj)

    if not inter_path.exists() or not ictal_path.exists():
        missing.append(subj)
        print(f"{subj:<8} {role:<6} {'MISSING FILE':<14} {'':>13} "
              f"{'':>9} {'':>9} {'':>6} {'❌ MISS':>8}")
        continue

    inter = np.load(str(inter_path), mmap_mode="r")
    ictal = np.load(str(ictal_path), mmap_mode="r")

    # Shape check
    inter_ok = (inter.ndim == 3 and inter.shape[1] == 18 and inter.shape[2] == 1024)
    ictal_ok = (ictal.ndim == 3 and ictal.shape[1] == 18 and ictal.shape[2] == 1024)
    if not (inter_ok and ictal_ok):
        shape_errors.append(subj)

    # NaN/Inf check on sample (first + last window to keep it fast)
    sample_inter = inter[[0, -1]].astype(np.float32)
    sample_ictal = ictal[[0, -1]].astype(np.float32) if len(ictal) > 0 else np.zeros((1,18,1024))
    has_nan = bool(np.any(~np.isfinite(sample_inter)) or np.any(~np.isfinite(sample_ictal)))
    if has_nan:
        nan_errors.append(subj)

    inter_mb = inter.nbytes / 1e6
    ictal_mb = ictal.nbytes / 1e6
    total_inter += len(inter)
    total_ictal += len(ictal)

    status = "✓ OK" if (inter_ok and ictal_ok and not has_nan) else "⚠ ERROR"
    nan_flag = "YES" if has_nan else "no"

    print(f"{subj:<8} {role:<6} {len(inter):>14,} {len(ictal):>13,} "
          f"{inter_mb:>9.1f} {ictal_mb:>9.1f} {nan_flag:>6} {status:>8}")

print("=" * 90)
print(f"{'TOTAL':<8} {'':6} {total_inter:>14,} {total_ictal:>13,}")
print()

# Summary
if missing:
    print(f"❌ MISSING subjects ({len(missing)}): {missing}")
else:
    print(f"✓  All 23 subjects present.")

if shape_errors:
    print(f"❌ SHAPE ERRORS: {shape_errors}")
else:
    print(f"✓  All shapes correct [N, 18, 1024].")

if nan_errors:
    print(f"❌ NaN/Inf in sample windows: {nan_errors}")
else:
    print(f"✓  No NaN/Inf detected in sampled windows.")

# Disk usage check
total_npy = list(PROCESSED_DIR.glob("*.npy"))
raw_npy   = [f for f in total_npy if "_inter" in f.name or "_ictal" in f.name
             and "adjs" not in f.name and "features" not in f.name]
total_gb  = sum(f.stat().st_size for f in raw_npy) / 1e9
print(f"\n  Raw window files (.npy) in processed/: {len(raw_npy)} files, {total_gb:.1f} GB")

if not missing and not shape_errors and not nan_errors:
    print("\n✅ PREPROCESSING VERIFIED — ready to run build_graphs.py --multiband")
else:
    print("\n⚠  Fix errors above before running build_graphs.py")