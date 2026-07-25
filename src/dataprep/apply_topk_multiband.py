"""
apply_topk_multiband.py
=======================
Apply top-k% thresholding to *_adjs_multiband.npy files.
Produces *_adjs_multiband_topk20.npy files.

Usage:
    python apply_topk_multiband.py

No arguments needed — paths are hardcoded.
"""

import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))
from graph_construction import apply_topk_threshold

PROCESSED_DIR = Path("F:/Study/Thesis/Code/data/processed")
KEEP_RATIO    = 0.20
IN_SUFFIX     = "_multiband"
OUT_SUFFIX    = "_multiband_topk20"

ALL_SUBJECTS = [f"chb{i:02d}" for i in range(1, 24)]

def apply_topk_to_file(in_path: Path, out_path: Path, keep_ratio: float) -> dict:
    """
    Load dense adjacency file, apply topk threshold window-by-window,
    save sparse result.

    Returns dict with density stats.
    """
    adjs = np.load(str(in_path), mmap_mode="r")
    N    = adjs.shape[0]

    mm = np.lib.format.open_memmap(
        str(out_path), mode="w+", dtype=np.float32, shape=(N, 18, 18)
    )

    densities = []
    for i in range(N):
        A_sparse  = apply_topk_threshold(adjs[i], keep_ratio=keep_ratio)
        mm[i]     = A_sparse
        densities.append(float((A_sparse > 0).mean()))
        if (i + 1) % 5000 == 0:
            print(f"    {i+1}/{N}", end="\r")

    del mm
    return {
        "n_windows":   N,
        "mean_density": float(np.mean(densities)),
        "min_density":  float(np.min(densities)),
        "max_density":  float(np.max(densities)),
    }


print("=" * 65)
print(f"Applying top-k% threshold (keep_ratio={KEEP_RATIO}) to multiband adjs")
print(f"  Input  suffix : {IN_SUFFIX}")
print(f"  Output suffix : {OUT_SUFFIX}")
print(f"  Processed dir : {PROCESSED_DIR}")
print("=" * 65)

missing  = []
failed   = []
n_done   = 0

for subj in ALL_SUBJECTS:
    for window_type in ["interictal", "ictal"]:
        in_name  = f"{subj}_{window_type}_adjs{IN_SUFFIX}.npy"
        out_name = f"{subj}_{window_type}_adjs{OUT_SUFFIX}.npy"
        in_path  = PROCESSED_DIR / in_name
        out_path = PROCESSED_DIR / out_name

        if not in_path.exists():
            missing.append(in_name)
            print(f"  [SKIP] {in_name} not found")
            continue

        if out_path.exists():
            print(f"  [SKIP] {out_name} already exists — use --overwrite to regenerate")
            n_done += 1
            continue

        print(f"\n  {subj} {window_type}: {in_path.name} -> {out_path.name}")
        try:
            stats = apply_topk_to_file(in_path, out_path, KEEP_RATIO)
            print(f"    n={stats['n_windows']:,}  "
                  f"density: mean={stats['mean_density']:.3f}  "
                  f"min={stats['min_density']:.3f}  "
                  f"max={stats['max_density']:.3f}")
            n_done += 1
        except Exception as e:
            print(f"  [ERROR] {subj} {window_type}: {e}")
            failed.append(f"{subj}_{window_type}")

print("\n" + "=" * 65)
print(f"Done: {n_done} files processed.")

if missing:
    print(f"  Missing source files ({len(missing)}): {missing[:5]}{'...' if len(missing)>5 else ''}")
if failed:
    print(f"  Errors ({len(failed)}): {failed}")
if not missing and not failed:
    print("  ✅ All multiband topk20 files created successfully.")

# Quick density check on test subjects
print("\nDensity spot-check (test subjects, interictal):")
test_subjs = ["chb03","chb06","chb13","chb14","chb15","chb16","chb17","chb18"]
for s in test_subjs:
    p = PROCESSED_DIR / f"{s}_interictal_adjs{OUT_SUFFIX}.npy"
    if p.exists():
        a   = np.load(str(p), mmap_mode="r")
        den = (a > 0).mean()
        print(f"  {s}: {len(a):,} windows, mean_density={den:.3f} "
              f"({'OK' if 0.15 <= den <= 0.25 else '⚠ check'})")
    else:
        print(f"  {s}: ❌ not found")

print("=" * 65)