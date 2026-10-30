#!/usr/bin/env python
"""
v9_x3_stage_uploads.py -- V9-X3 prep, step 5 support: stages one folder per fold under
F:/Study/Thesis/Agent/kaggle_upload/fold{k}/ containing exactly that fold's training-case .npz
files (results/v9_x3/fold_manifests.json), ready for the author to zip and upload as the Kaggle
dataset v9-x3-fold{k}. Uses os.link (hardlink, same NTFS volume, instant, no extra disk) --
falls back to a real copy if hardlinking fails (e.g. a different volume).
Outside this task's committed paths by design (F:/Study/Thesis/Agent is not part of this git
repo) -- nothing here is committed.
Run: python src/v9_x3_stage_uploads.py
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAN = json.loads((ROOT / "results" / "v9_x3" / "fold_manifests.json").read_text())
STAGE = Path("F:/Study/Thesis/Agent/kaggle_upload")


def main():
    for k, man in MAN.items():
        d = STAGE / f"fold{k}"
        d.mkdir(parents=True, exist_ok=True)
        n, total = 0, 0.0
        for case, src in man["train_sources"].items():
            src_path = ROOT / src.split(" ")[0]
            dst = d / f"{case}.npz"
            if dst.exists():
                n += 1; total += dst.stat().st_size / 1e6
                continue
            if not src_path.exists():
                print(f"  fold {k} {case}: MISSING source {src_path}"); continue
            try:
                import os
                os.link(src_path, dst)
            except OSError:
                shutil.copy2(src_path, dst)
            n += 1; total += dst.stat().st_size / 1e6
        print(f"fold {k}: staged {n}/{len(man['train_sources'])} files, {total:.0f} MB at {d}")


if __name__ == "__main__":
    main()
