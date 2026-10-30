#!/usr/bin/env python
"""
v9_x3_build_fold_manifest.py -- V9-X3 prep, step 3 (part 1): from results/v9_x3/folds.json, the
list of TRAINING subjects per fold (every case in the other three folds) and the HELD-OUT (test)
subjects of this fold, with the on-disk source of each subject's per-window array -- so the
author knows exactly which files to zip into each Kaggle dataset v9-x3-fold{k} (prompt step 5),
and v9_x3_train_fold.py knows which npz to read.
Sources: data/trainset_v2/{s}.npz (15), data/testset_v2/{s}.npz (8), results/v9_x3/chb24.npz
(built by v9_x3_build_chb24.py -- NOT results/v9_anatomy/xcache/chb24.npz, different z-scoring,
see that script's docstring).
Output: results/v9_x3/fold_manifests.json.
Run: python src/v9_x3_build_fold_manifest.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "v9_x3"
TRAIN_DIR = ROOT / "data" / "trainset_v2"
TEST_DIR = ROOT / "data" / "testset_v2"
CHB24_NPZ = OUT / "chb24.npz"


def source_of(case):
    for d in (TRAIN_DIR, TEST_DIR):
        p = d / f"{case}.npz"
        if p.exists():
            return str(p.relative_to(ROOT))
    if case == "chb24":
        return str(CHB24_NPZ.relative_to(ROOT)) + ("" if CHB24_NPZ.exists() else " (NOT YET BUILT)")
    return "MISSING"


def main():
    folds = json.loads((OUT / "folds.json").read_text())["folds"]
    manifests = {}
    for k, groups in folds.items():
        held_out_cases = [c for g in groups for c in g["cases"]]
        train_cases = [c for kk, gg in folds.items() if kk != k for g in gg for c in g["cases"]]
        manifests[k] = dict(
            held_out_cases=held_out_cases,
            train_cases=sorted(train_cases),
            train_sources={c: source_of(c) for c in sorted(train_cases)},
            held_out_sources={c: source_of(c) for c in held_out_cases},
        )
        n_bytes = 0
        for c, src in manifests[k]["train_sources"].items():
            p = ROOT / src.split(" ")[0]
            if p.exists():
                n_bytes += p.stat().st_size
        manifests[k]["train_total_mb"] = round(n_bytes / 1e6, 1)
        print(f"fold {k}: train {len(train_cases)} cases ({manifests[k]['train_total_mb']} MB), "
              f"held out {held_out_cases}")
    (OUT / "fold_manifests.json").write_text(json.dumps(manifests, indent=1))
    print(f"wrote {OUT / 'fold_manifests.json'}")


if __name__ == "__main__":
    main()
