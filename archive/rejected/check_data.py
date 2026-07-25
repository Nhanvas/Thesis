"""
check_data.py
=============
Verify preprocessed data integrity before running any model.
Run this before smoke test. Reports:
  - Which files exist / missing
  - Shapes of arrays
  - Adjacency matrix stats (mean, std, sparsity)
  - Whether _features.npy files exist yet
"""

import sys
import numpy as np
from pathlib import Path

PROCESSED_DIR = Path("F:/Study/Thesis/Code/data/processed")
SUBJECTS = [f"chb{i:02d}" for i in range(1, 24)]


def check_subject(subj: str) -> dict:
    result = {"subject": subj}

    files = {
        "inter_windows":  f"{subj}_interictal.npy",
        "ictal_windows":  f"{subj}_ictal.npy",
        "inter_adjs":     f"{subj}_interictal_adjs.npy",
        "ictal_adjs":     f"{subj}_ictal_adjs.npy",
        "inter_features": f"{subj}_interictal_features.npy",
        "ictal_features": f"{subj}_ictal_features.npy",
    }

    for key, fname in files.items():
        path = PROCESSED_DIR / fname
        if path.exists():
            try:
                arr = np.load(str(path), mmap_mode="r")
                result[key] = f"OK  shape={arr.shape}"
                if key == "inter_adjs":
                    # Check adjacency quality
                    sample = arr[:min(100, len(arr))]
                    sparsity = (sample == 0).mean()
                    result["adj_sparsity"] = f"{sparsity:.2%}"
                    result["adj_mean_nonzero"] = (
                        f"{sample[sample > 0].mean():.4f}" 
                        if (sample > 0).any() else "all_zero_WARNING"
                    )
            except Exception as e:
                result[key] = f"ERROR: {e}"
        else:
            result[key] = "MISSING"

    return result


def main():
    print(f"Checking {PROCESSED_DIR}\n")
    print(f"{'Subject':<10} {'inter_win':<20} {'ictal_win':<20} "
          f"{'inter_adjs':<25} {'inter_feat':<25} {'adj_sparsity':<15}")
    print("-" * 115)

    missing_features = []
    missing_adjs = []

    for subj in SUBJECTS:
        r = check_subject(subj)

        inter_win  = r.get("inter_windows", "MISSING")[:18]
        ictal_win  = r.get("ictal_windows",  "MISSING")[:18]
        inter_adj  = r.get("inter_adjs",     "MISSING")[:23]
        inter_feat = r.get("inter_features", "MISSING")[:23]
        sparsity   = r.get("adj_sparsity",   "N/A")

        print(f"{subj:<10} {inter_win:<20} {ictal_win:<20} "
              f"{inter_adj:<25} {inter_feat:<25} {sparsity:<15}")

        if "MISSING" in r.get("inter_features", "MISSING"):
            missing_features.append(subj)
        if "MISSING" in r.get("inter_adjs", "MISSING"):
            missing_adjs.append(subj)

    print("\n" + "="*60)
    print(f"Missing _features.npy : {missing_features if missing_features else 'NONE — all present'}")
    print(f"Missing _adjs.npy     : {missing_adjs if missing_adjs else 'NONE — all present'}")

    if missing_features:
        print("\n[ACTION] Run feature_extraction.py first.")
    if missing_adjs:
        print("[ACTION] Run build_graphs.py for missing subjects.")

    # Check adjacency CAR quality for chb01 specifically
    adj_path = PROCESSED_DIR / "chb01_interictal_adjs.npy"
    if adj_path.exists():
        adjs = np.load(str(adj_path), mmap_mode="r")
        sample_idx = len(adjs) // 2
        A = adjs[sample_idx]
        print(f"\nchb01 adjacency sample [idx={sample_idx}]:")
        print(f"  min={A.min():.4f}  max={A.max():.4f}  "
              f"mean_nonzero={A[A>0].mean() if (A>0).any() else 0:.4f}  "
              f"n_edges={int((A>0).sum())}")

        # Symmetry check
        is_symmetric = np.allclose(A, A.T, atol=1e-5)
        print(f"  symmetric: {is_symmetric}")

        # All-zero warning
        if A.max() == 0:
            print("  WARNING: adjacency matrix is all zeros — CAR or "
                  "wPLI computation may have failed.")


if __name__ == "__main__":
    main()