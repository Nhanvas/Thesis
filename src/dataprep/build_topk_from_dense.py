"""
build_topk_from_dense.py
========================
Apply top-k% threshold post-hoc to existing dense adjacency matrices.

WHY THIS SCRIPT EXISTS (not build_graphs.py):
  Raw preprocessed windows (*_interictal.npy, *_ictal.npy) were deleted
  in v6 cleanup to reclaim disk space (~30 GB). build_graphs.py reads
  those raw windows and cannot run without them.

  Top-k% thresholding is a post-processing step on the COMBINED adjacency
  matrix A = 0.5*wPLI + 0.5*AEC. The dense files (*_adjs.npy, t=0.05)
  already contain this combined matrix. Since density is 0.92–0.97 (>> 0.20),
  the top-30 selected from the dense file is identical to top-30 from the
  unthresholded combined matrix. No information is lost by post-processing.

SCIENTIFIC VALIDITY:
  build_graphs.py path:      raw EEG → wPLI → AEC → combine → topk%
  build_topk_from_dense path: dense_adjs (=combined after t=0.05) → topk%
  These are equivalent because at density 0.92, only ~12 of 153 edges are
  below 0.05 and would rank in the bottom 8% anyway — never in top-30.

USAGE:
  # Default: keep_ratio=0.20, all 23 subjects
  python src/build_topk_from_dense.py

  # Different ratio
  python src/build_topk_from_dense.py --keep_ratio 0.15

  # Specific subjects only
  python src/build_topk_from_dense.py --subjects chb03 chb06 chb13

OUTPUT:
  *_interictal_adjs_topk20.npy  — shape [N, 18, 18], float32
  *_ictal_adjs_topk20.npy       — shape [M, 18, 18], float32
  (46 files total for all 23 subjects)
"""

import sys
import argparse
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from graph_construction import apply_topk_threshold, DEFAULT_KEEP_RATIO

ALL_SUBJECTS = [f"chb{i:02d}" for i in range(1, 24)]


def build_topk_subject(subject_id: str,
                       processed_dir: Path,
                       keep_ratio: float,
                       out_suffix: str,
                       overwrite: bool = False) -> dict:
    """
    Apply top-k% threshold to dense adjs for one subject.
    Returns dict with processing stats for verification.
    """
    stats = {}

    for window_type in ['interictal', 'ictal']:
        in_path  = processed_dir / f"{subject_id}_{window_type}_adjs.npy"
        out_path = processed_dir / f"{subject_id}_{window_type}_adjs{out_suffix}.npy"

        if not in_path.exists():
            print(f"  [{subject_id}] {window_type}: source not found, skip")
            continue

        if out_path.exists() and not overwrite:
            print(f"  [{subject_id}] {window_type}: output exists, skip "
                  f"(use --overwrite to recompute)")
            continue

        data = np.load(str(in_path), mmap_mode='r')  # [N, 18, 18], read-only
        N = data.shape[0]
        print(f"  [{subject_id}] {window_type}: {N} windows → {out_path.name}")

        out = np.empty((N, 18, 18), dtype=np.float32)
        density_sum = 0.0

        for i in range(N):
            w = apply_topk_threshold(
                data[i].astype(np.float64), keep_ratio=keep_ratio
            )
            out[i] = w.astype(np.float32)
            density_sum += (w > 0).sum() / (18 * 18)
            if (i + 1) % 5000 == 0:
                print(f"    {i+1}/{N}", end="\r", flush=True)

        np.save(str(out_path), out)
        mean_density = density_sum / N
        stats[window_type] = {'n': N, 'mean_density': mean_density}
        print(f"  [{subject_id}] {window_type}: done. "
              f"Mean density = {mean_density:.4f} "
              f"(target ~{keep_ratio:.2f})")

    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Apply top-k% threshold to existing dense adjacency files."
    )
    parser.add_argument(
        '--keep_ratio', type=float, default=DEFAULT_KEEP_RATIO,
        help=f"Fraction of edges to retain. Default: {DEFAULT_KEEP_RATIO} "
             f"(30 edges for 18-channel EEG)."
    )
    parser.add_argument(
        '--subjects', nargs='+', default=ALL_SUBJECTS,
        help="Subject IDs to process. Default: all 23."
    )
    parser.add_argument(
        '--processed_dir', type=str,
        default="F:/Study/Thesis/Code/data/processed",
        help="Directory containing dense *_adjs.npy files."
    )
    parser.add_argument(
        '--overwrite', action='store_true',
        help="Overwrite existing topk output files."
    )
    args = parser.parse_args()

    pct        = int(args.keep_ratio * 100)
    out_suffix = f"_topk{pct}"
    PROC_DIR   = Path(args.processed_dir)

    n_edges_target = int(18 * 17 / 2 * args.keep_ratio)   # 30 for keep_ratio=0.20

    print("=" * 60)
    print(f"Top-k% post-processing from dense adjacency files")
    print(f"  keep_ratio : {args.keep_ratio} → ~{n_edges_target} edges / window "
          f"(density ~{args.keep_ratio:.2f})")
    print(f"  out_suffix : {out_suffix}")
    print(f"  subjects   : {len(args.subjects)} subjects")
    print(f"  source     : *_adjs.npy (dense, fixed t=0.05)")
    print(f"  output     : *_adjs{out_suffix}.npy")
    print(f"  overwrite  : {args.overwrite}")
    print("=" * 60)

    # Pre-flight: verify source files exist
    missing = [s for s in args.subjects
               if not (PROC_DIR / f"{s}_interictal_adjs.npy").exists()]
    if missing:
        print(f"\n[ERROR] Missing source files for: {missing}")
        print(f"Expected at: {PROC_DIR}")
        sys.exit(1)

    all_stats = {}
    failed    = []

    for subj in args.subjects:
        print(f"\nProcessing {subj}...")
        try:
            stats = build_topk_subject(
                subj, PROC_DIR, args.keep_ratio, out_suffix, args.overwrite
            )
            all_stats[subj] = stats
        except Exception as e:
            print(f"  [ERROR] {subj}: {e}")
            failed.append(subj)

    # Summary
    print("\n" + "=" * 60)
    if failed:
        print(f"[FAILED] {len(failed)} subjects: {failed}")
    else:
        print("TOP-K POST-PROCESSING COMPLETE")
        print(f"\nDensity verification (mean across windows):")
        print(f"  {'Subject':<10} {'Inter density':>14} {'Ictal density':>14}")
        print(f"  {'-'*10} {'-'*14} {'-'*14}")
        for subj, stats in all_stats.items():
            inter = stats.get('interictal', {}).get('mean_density', float('nan'))
            ictal = stats.get('ictal', {}).get('mean_density', float('nan'))
            flag  = " ← CHECK" if abs(inter - args.keep_ratio) > 0.05 else ""
            print(f"  {subj:<10} {inter:>14.4f} {ictal:>14.4f}{flag}")
        print(f"\n  Expected density: ~{args.keep_ratio:.2f} ± 0.02")
        print(f"  Files created: {len(all_stats) * 2} "
              f"(*_interictal_adjs{out_suffix}.npy + *_ictal_adjs{out_suffix}.npy)")
    print("=" * 60)