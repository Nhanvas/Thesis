"""
run_ltso.py
===========
Full LTSO sweep — 11 folds for E5 proposed GAE model.

Usage:
    python run_ltso.py                         # all 11 folds, seed 42
    python run_ltso.py --folds 1               # fold 1 only
    python run_ltso.py --folds 1 2 3           # folds 1, 2, 3
    python run_ltso.py --seeds 42 0 123        # 3 seeds (E5 requires 3)
    python run_ltso.py --folds 1 --seeds 42 0 123
    python run_ltso.py --folds 1 --cpu_test    # CPU test: only 3 train subjects

NOTE:
    --cpu_test flag limits training to 3 subjects for pipeline verification
    on laptop CPU. Remove this flag when running on RTX 5090.
"""

import sys
import json
import argparse
import numpy as np
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "src"))
from train_pipeline import run


SPLITS_DIR    = Path("data/splits")
RESULTS_DIR   = Path("results")
EXPERIMENT_ID = "E5_proposed_gae"
CONFIG_PATH   = str(Path(__file__).parent / "src" / "configs" / "defaults.yaml")


def run_fold(fold_num: int, seed: int, cpu_test: bool = False) -> dict:
    fold_id = f"fold_{fold_num:02d}"

    train_subjects = json.loads(
        (SPLITS_DIR / f"{fold_id}_train.json").read_text())
    test_subjects = json.loads(
        (SPLITS_DIR / f"{fold_id}_test.json").read_text())

    # CPU test mode: limit training data to verify pipeline only
    # Remove --cpu_test flag when running on RTX 5090
    if cpu_test:
        train_subjects = train_subjects[:3]
        print(f"  [CPU TEST MODE] Training limited to: {train_subjects}")

    exp_id = f"{EXPERIMENT_ID}_seed{seed}"

    print(f"\n{'='*65}")
    print(f"FOLD {fold_num:02d} | seed={seed} | "
          f"test={test_subjects} | train={len(train_subjects)} subjects")
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*65}")

    metrics = run(
        config_path=CONFIG_PATH,
        experiment_id=exp_id,
        fold_id=fold_id,
        train_subjects=train_subjects,
        test_subjects=test_subjects,
        seed_override=seed,
    )

    print(f"\n[RESULT] fold={fold_num:02d} seed={seed} | "
          f"AUROC={metrics['auroc']:.4f} | "
          f"Sensitivity={metrics['sensitivity']:.4f} | "
          f"Specificity={metrics['specificity']:.4f} | "
          f"FDR/h={metrics['fdr_per_hour']:.2f}")

    return metrics


def summarize(all_results: list):
    from collections import defaultdict

    by_seed = defaultdict(list)
    for r in all_results:
        by_seed[r["seed"]].append(r["metrics"])

    print(f"\n{'='*65}")
    print("SUMMARY")
    print(f"{'='*65}")

    for seed, results in sorted(by_seed.items()):
        aurocs = [r["auroc"] for r in results]
        senss  = [r["sensitivity"] for r in results]
        fdrs   = [r["fdr_per_hour"] for r in results]
        print(f"\nSeed {seed} ({len(results)} folds):")
        print(f"  AUROC       : {np.mean(aurocs):.4f} ± {np.std(aurocs):.4f}")
        print(f"  Sensitivity : {np.mean(senss):.4f}  ± {np.std(senss):.4f}")
        print(f"  FDR/h       : {np.mean(fdrs):.2f}   ± {np.std(fdrs):.2f}")

    if len(by_seed) > 1:
        all_aurocs = [r["metrics"]["auroc"] for r in all_results]
        all_senss  = [r["metrics"]["sensitivity"] for r in all_results]
        all_fdrs   = [r["metrics"]["fdr_per_hour"] for r in all_results]
        print(f"\nGrand mean (all seeds × folds):")
        print(f"  AUROC       : {np.mean(all_aurocs):.4f} ± {np.std(all_aurocs):.4f}")
        print(f"  Sensitivity : {np.mean(all_senss):.4f}  ± {np.std(all_senss):.4f}")
        print(f"  FDR/h       : {np.mean(all_fdrs):.2f}   ± {np.std(all_fdrs):.2f}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folds", nargs="+", type=int,
                        default=list(range(1, 12)),
                        help="Fold numbers to run. Default: 1-11")
    parser.add_argument("--seeds", nargs="+", type=int,
                        default=[42],
                        help="Random seeds. Default: 42. Use 42 0 123 for E5.")
    parser.add_argument("--cpu_test", action="store_true",
                        help="CPU test mode: limit train to 3 subjects only. "
                             "Use for pipeline verification on laptop. "
                             "Remove when running on RTX 5090.")
    args = parser.parse_args()

    if args.cpu_test:
        print("\n[CPU TEST MODE] Training limited to 3 subjects per fold.")
        print("This is for pipeline verification only, not final results.\n")

    print(f"LTSO sweep: folds={args.folds}  seeds={args.seeds}")
    print(f"Total runs: {len(args.folds) * len(args.seeds)}\n")

    all_results = []
    for seed in args.seeds:
        for fold_num in args.folds:
            metrics = run_fold(fold_num, seed, cpu_test=args.cpu_test)
            all_results.append({
                "fold":    fold_num,
                "seed":    seed,
                "metrics": metrics,
            })

    summarize(all_results)


if __name__ == "__main__":
    main()