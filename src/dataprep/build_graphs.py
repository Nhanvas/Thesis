"""
build_graphs.py
===============
Compute adjacency matrices (wPLI + AEC combined) from preprocessed EEG windows.
Run once after preprocessing.py completes and before train_pipeline.py.

For each subject, reads:
  {subject_id}_interictal.npy   shape [N, 18, 1024]
  {subject_id}_ictal.npy        shape [M, 18, 1024]

Writes:
  {subject_id}_interictal_adjs{out_suffix}.npy   shape [N, 18, 18]
  {subject_id}_ictal_adjs{out_suffix}.npy        shape [M, 18, 18]

Default alpha=0.5 (combined wPLI + AEC) — E_main configuration.
Set alpha=1.0 only for the wPLI-only ablation experiment.

Usage:
  # E_main (default — broadband wPLI + AEC)
  python src/build_graphs.py

  # wPLI-only ablation
  python src/build_graphs.py --alpha 1.0 --out_suffix _wpli_only

  # Band-specific wPLI ablation — theta only (test subjects first)
  python src/build_graphs.py --band theta --out_suffix _theta \
      --subjects chb03 chb06 chb13 chb14 chb15 chb16 chb17 chb18

  # Band-specific wPLI ablation — alpha band
  python src/build_graphs.py --band alpha --out_suffix _alphaband \
      --subjects chb03 chb06 chb13 chb14 chb15 chb16 chb17 chb18

  # Option B — Multiband wPLI (all 5 bands, weighted by spectral diagnostic)
  python src/build_graphs.py --multiband --out_suffix _multiband

  # Option B — verify with 1 subject first before running all 23
  python src/build_graphs.py --multiband --out_suffix _multiband \
      --subjects chb22
"""

import sys
import argparse
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from graph_construction import (
    build_adjacency,
    build_adjacency_multiband,
    DEFAULT_ALPHA,
    BAND_RANGES,
    MULTIBAND_WEIGHTS,
)


def build_subject_graphs(subject_id: str,
                         processed_dir: Path,
                         alpha: float = DEFAULT_ALPHA,
                         out_suffix: str = "",
                         freq_low: float = None,
                         freq_high: float = None,
                         multiband: bool = False) -> None:
    """
    Build and save adjacency matrices for one subject.

    Parameters
    ----------
    out_suffix : str
        Optional suffix appended to output filenames.
        Used to separate E_main files from ablation files.
        E.g., out_suffix="_multiband" -> chb01_interictal_adjs_multiband.npy
    freq_low : float or None
        Lower frequency bound (Hz) for band-specific wPLI.
        None = broadband (E_main default).
        Ignored when multiband=True.
    freq_high : float or None
        Upper frequency bound (Hz) for band-specific wPLI.
        None = broadband (E_main default).
        Ignored when multiband=True.
    multiband : bool
        If True, use weighted multiband wPLI (Option B).
        If False, use broadband or band-specific wPLI (E_main / ablation).
    """
    inter_in  = processed_dir / f"{subject_id}_interictal.npy"
    ictal_in  = processed_dir / f"{subject_id}_ictal.npy"
    inter_out = processed_dir / f"{subject_id}_interictal_adjs{out_suffix}.npy"
    ictal_out = processed_dir / f"{subject_id}_ictal_adjs{out_suffix}.npy"

    if not inter_in.exists():
        raise FileNotFoundError(
            f"Missing: {inter_in}\nRun preprocessing.py first."
        )

    def _build_one(window):
        """Build adjacency for one window using selected method."""
        if multiband:
            return build_adjacency_multiband(
                window.astype(np.float64),
                alpha=alpha
            )
        else:
            return build_adjacency(
                window.astype(np.float64),
                alpha=alpha,
                freq_low=freq_low,
                freq_high=freq_high
            )

    # -- Interictal -----------------------------------------------------------
    windows = np.load(str(inter_in), mmap_mode="r")
    N = windows.shape[0]
    print(f"  [{subject_id}] interictal: {N} windows -> {inter_out.name}")
    mm = np.lib.format.open_memmap(
        str(inter_out), mode="w+", dtype=np.float32, shape=(N, 18, 18)
    )
    for i in range(N):
        mm[i] = _build_one(windows[i])
        if (i + 1) % 2000 == 0:
            print(f"    {i+1}/{N}", end="\r")
    del mm
    print(f"  [{subject_id}] interictal adjs saved.")

    # -- Ictal ----------------------------------------------------------------
    if not ictal_in.exists():
        print(f"  [{subject_id}] no ictal file — skipping ictal adjs.")
        return

    windows = np.load(str(ictal_in), mmap_mode="r")
    M = windows.shape[0]
    print(f"  [{subject_id}] ictal: {M} windows -> {ictal_out.name}")
    mm = np.lib.format.open_memmap(
        str(ictal_out), mode="w+", dtype=np.float32, shape=(M, 18, 18)
    )
    for i in range(M):
        mm[i] = _build_one(windows[i])
    del mm
    print(f"  [{subject_id}] ictal adjs saved.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build adjacency matrices from preprocessed EEG windows."
    )
    parser.add_argument(
        "--subjects", nargs="+",
        default=[f"chb{i:02d}" for i in range(1, 24)],
        help="Subject IDs to process. Default: all 23."
    )
    parser.add_argument(
        "--alpha", type=float, default=DEFAULT_ALPHA,
        help=(
            f"Mixing weight for wPLI vs AEC: "
            f"A = alpha*wPLI + (1-alpha)*AEC. "
            f"Default: {DEFAULT_ALPHA} (E_main combined). "
            f"Use 1.0 for wPLI-only ablation."
        )
    )
    parser.add_argument(
        "--band", type=str, default="broadband",
        choices=list(BAND_RANGES.keys()),
        help=(
            "Frequency band for wPLI computation. "
            "Default: broadband (original E_main behaviour). "
            "Options: broadband, theta (4-8 Hz), alpha (8-13 Hz), "
            "beta (13-30 Hz), gamma (30-60 Hz). "
            "AEC is always computed broadband regardless of this setting. "
            "Ignored when --multiband is set."
        )
    )
    parser.add_argument(
        "--multiband",
        action="store_true",
        default=False,
        help=(
            "Use weighted multiband wPLI instead of broadband wPLI. "
            "Computes wPLI separately for each of 5 frequency bands and "
            "combines them with weights derived from spectral diagnostic: "
            f"delta={MULTIBAND_WEIGHTS['delta']}, "
            f"theta={MULTIBAND_WEIGHTS['theta']}, "
            f"alpha={MULTIBAND_WEIGHTS['alpha']}, "
            f"beta={MULTIBAND_WEIGHTS['beta']}, "
            f"gamma={MULTIBAND_WEIGHTS['gamma']}. "
            "Alpha dominates (sign-flip suppression in 7/8 test subjects). "
            "Requires --out_suffix to avoid overwriting E_main files."
        )
    )
    parser.add_argument(
        "--out_suffix", type=str, default="",
        help=(
            "Suffix appended to output filenames. "
            "Leave empty for E_main. "
            "Use '_multiband' for Option B to keep files separate."
        )
    )
    parser.add_argument(
        "--processed_dir", type=str,
        default="F:/Study/Thesis/Code/data/processed",
        help="Directory containing preprocessed .npy files."
    )
    args = parser.parse_args()

    PROCESSED_DIR = Path(args.processed_dir)
    freq_low, freq_high = BAND_RANGES[args.band]

    # --multiband overrides --band
    if args.multiband:
        freq_low  = None
        freq_high = None

    print("=" * 60)
    if args.multiband:
        print(f"Graph construction — MULTIBAND wPLI + AEC")
        print(f"  wPLI: weighted sum of 5 bands:")
        for b, w in MULTIBAND_WEIGHTS.items():
            print(f"    {b:<6}: weight={w}")
        print(f"  AEC weight  : {1-args.alpha:.2f} (broadband)")
    else:
        print(f"Graph construction — alpha={args.alpha} | band={args.band}")
        print(f"  wPLI weight : {args.alpha:.2f} | AEC weight: {1-args.alpha:.2f}")
        if freq_low is not None:
            print(f"  wPLI band   : {freq_low}-{freq_high} Hz")
        else:
            print(f"  wPLI band   : broadband (full spectrum)")
    print(f"  Output suffix: '{args.out_suffix}'")
    print(f"  Subjects     : {args.subjects}")
    print(f"  Output dir   : {PROCESSED_DIR}")
    print("=" * 60)

    # Safety guards
    if args.alpha == 1.0 and args.out_suffix == "" and not args.multiband:
        print(
            "[WARNING] alpha=1.0 with no suffix will overwrite E_main files.\n"
            "If this is the ablation run, add --out_suffix _wpli_only\n"
        )

    if args.band != "broadband" and args.out_suffix == "" and not args.multiband:
        print(
            f"[WARNING] --band {args.band} with no --out_suffix will overwrite "
            f"E_main adjacency files.\n"
            f"Add --out_suffix _{args.band} to keep files separate.\n"
        )

    if args.multiband and args.out_suffix == "":
        raise ValueError(
            "[ERROR] --multiband requires --out_suffix to avoid overwriting "
            "E_main adjacency files.\n"
            "Add --out_suffix _multiband and rerun."
        )

    failed = []
    for subj in args.subjects:
        raw_path = PROCESSED_DIR / f"{subj}_interictal.npy"
        if not raw_path.exists():
            print(f"[SKIP] {subj} — {raw_path.name} not found")
            continue
        print(f"\nProcessing {subj}...")
        try:
            build_subject_graphs(
                subj, PROCESSED_DIR,
                alpha=args.alpha,
                out_suffix=args.out_suffix,
                freq_low=freq_low,
                freq_high=freq_high,
                multiband=args.multiband,
            )
        except Exception as e:
            print(f"  [ERROR] {subj}: {e}")
            failed.append(subj)

    print("\n" + "=" * 60)
    if failed:
        print(f"[FAILED] {len(failed)} subjects: {failed}")
    else:
        print("GRAPH CONSTRUCTION COMPLETE — all subjects processed.")
    print("=" * 60)