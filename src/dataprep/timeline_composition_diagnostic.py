"""
timeline_composition_diagnostic.py -- Figure Round 4 §1.

The chb13 investigation (docs/diagnostic_q_chb13.md) established that the committed background
score array `ens_seed42_{subj}_inter.npy` runs out partway through the reconstructed timeline
(`szcore_eval.build_timeline_masked`), and every position after that exhaustion point receives a
bootstrap-resampled score instead of a real one. For chb13: 12,452 entries against 25,224 eligible
positions, exhausting at 41.9% of the recording.

This script quantifies the same thing for all eight held-out subjects -- the false-alarm rate of
the study is measured on these timelines, so the report has to state what fraction of each is
substituted rather than measured. It changes no committed result; it only characterises a property
of the evaluation that was already in place when the results were produced.

`eligible_windows` and the exhaustion point are computed directly from the summary files and the
committed score-array lengths -- the SAME construction `szcore_eval.build_timeline_masked` uses
internally, not a re-implementation of the detection or scoring logic.

Outputs -> results/diagnostics/timeline_composition.csv
    subject, eligible_windows, committed_inter_windows, dropped_windows, dropped_fraction,
    exhaustion_point_fraction, substituted_fraction, ictal_windows

USAGE
    python src/dataprep/timeline_composition_diagnostic.py
"""
import os as _os, sys as _sys
from pathlib import Path
_here = _os.path.dirname(_os.path.abspath(__file__))
_src = _os.path.dirname(_here)
for _p in (_here, _src):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import numpy as np
import pandas as pd

import evaluation_protocol as E
import szcore_eval as SE

ROOT = Path(_src).parent
SUMMARY_DIR = ROOT / "data" / "summaries"
ENS_DIR = ROOT / "results" / "phaseB" / "tier2" / "ens_test_tf" / "rlg"
PROC_DIR = ROOT / "data" / "processed"
OUT = ROOT / "results" / "diagnostics" / "timeline_composition.csv"

CANONICAL_SEED = 0


def eligible_and_ictal_counts(subj, summary_dir):
    """(eligible_windows, ictal_windows): eligible = not ictal, outside the 4h post-seizure
    buffer -- the SAME per-window classification build_timeline_masked applies (its lines
    93-104), computed directly from the summary files, independent of any score array's
    length so it isn't distorted by exhaustion."""
    edfs = E.parse_summary_edf_list(Path(summary_dir) / f"{subj}-summary.txt")
    eligible = 0
    ictal = 0
    for edf in edfs:
        dur = edf['duration_s']
        n_win = dur // SE.WIN_SEC
        labels = np.zeros(dur, dtype=np.int8)
        buf = np.zeros(dur, dtype=bool)
        for (on, off) in edf['seizures']:
            on = min(on, dur); off = min(off, dur)
            labels[on:off] = 1
            buf[off:min(dur, off + SE.BUFFER_H * 3600)] = True
        tl = n_win * SE.WIN_SEC
        wl = labels[:tl].reshape(n_win, SE.WIN_SEC).max(axis=1)
        wb = buf[:tl].reshape(n_win, SE.WIN_SEC).any(axis=1)
        ictal += int((wl == 1).sum())
        eligible += int(((wl == 0) & (~wb)).sum())
    return eligible, ictal


def main():
    rows = []
    for subj in SE.TEST_SUBJS:
        ei = np.load(ENS_DIR / f"ens_seed42_{subj}_inter.npy")
        ec = np.load(ENS_DIR / f"ens_seed42_{subj}_ictal.npy")
        committed_inter = len(ei)

        eligible, ictal_w = eligible_and_ictal_counts(subj, SUMMARY_DIR)

        np.random.seed(CANONICAL_SEED)
        signal, is_ictal, is_buffer, real_inter, sz_ranges, n_inter_h = \
            SE.build_timeline_masked(subj, ei, ec, str(SUMMARY_DIR))
        total_positions = len(signal)

        dropped = eligible - committed_inter
        dropped_fraction = dropped / eligible if eligible else float("nan")

        # Exhaustion point: the first global window index at which inter_ptr would have
        # consumed all `committed_inter` real scores (mirrors build_timeline_masked's own
        # sequential inter_ptr, but only needs to COUNT real_inter slots, not touch scores).
        ptr = 0
        exhaustion_idx = None
        for w in range(total_positions):
            if real_inter[w]:
                ptr += 1
                if ptr == committed_inter:
                    exhaustion_idx = w
                    break
        exhaustion_point_fraction = ((exhaustion_idx + 1) / total_positions
                                     if exhaustion_idx is not None else float("nan"))

        # substituted_fraction: share of ALL timeline positions carrying a bootstrap-
        # resampled score. That is exactly the fallback branch of build_timeline_masked --
        # is_buffer=True positions that are NOT genuine 4h-post-seizure buffer, PLUS the
        # (rare) case of a subject whose inter array is exhausted precisely at the end with
        # no true excess. Genuine buffer windows have a real bootstrap-resampled score too
        # (build_timeline_masked line 112 draws from bootstrap_pool for every is_buffer=True
        # slot, buffer or exhaustion alike) -- so "substituted" here means every position NOT
        # covered by a genuine committed interictal or ictal score, i.e. is_buffer=True.
        substituted = int(is_buffer.sum())
        substituted_fraction = substituted / total_positions if total_positions else float("nan")

        # cross-check against data/processed/{subj}_interictal.npy
        proc_path = PROC_DIR / f"{subj}_interictal.npy"
        proc_n = int(np.load(proc_path, mmap_mode="r").shape[0]) if proc_path.exists() else None
        agrees = (proc_n == committed_inter)

        rows.append(dict(subject=subj, eligible_windows=eligible,
                         committed_inter_windows=committed_inter, dropped_windows=dropped,
                         dropped_fraction=round(dropped_fraction, 4),
                         exhaustion_point_fraction=round(exhaustion_point_fraction, 4)
                         if not np.isnan(exhaustion_point_fraction) else None,
                         substituted_fraction=round(substituted_fraction, 4),
                         ictal_windows=ictal_w))

        print(f"[{subj}] eligible={eligible} committed_inter={committed_inter} "
             f"dropped={dropped} ({dropped_fraction:.4f}) "
             f"exhaustion_at={exhaustion_point_fraction:.4f} "
             f"substituted_fraction={substituted_fraction:.4f} ictal={ictal_w}  "
             f"data/processed/{subj}_interictal.npy len={proc_n} "
             f"({'MATCH' if agrees else 'DISAGREE -- report this'})")
        if not agrees:
            print(f"  [DISAGREEMENT] committed_inter_windows={committed_inter} but "
                 f"data/processed/{subj}_interictal.npy has {proc_n} rows")

    out = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"\n[saved] {OUT.resolve()}")

    mean_sub = out.substituted_fraction.mean()
    lo, hi = out.substituted_fraction.min(), out.substituted_fraction.max()
    print(f"\n[ANSWER] substituted_fraction across the eight held-out subjects: "
         f"mean={mean_sub:.4f}, range=[{lo:.4f}, {hi:.4f}]")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
