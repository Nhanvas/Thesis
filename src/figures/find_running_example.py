"""
find_running_example.py -- Task A, Figure Brief Round 2.

Locks the single chb13 recording used by Fig 2.10, Fig 3.4 and Fig 3.10. All
three must show the SAME recording, so this script finds one chb13 EDF file
that, at the headline operating point (m50/p2.0), contains at least one
correctly detected seizure (a true positive under SzCORE tolerance matching)
and at least one false positive.

Nothing here re-implements the detection algorithm: change points come from
`cpd_pipeline_v14.detect_changepoints` with its locked defaults (mirrors
extract_latency_rlg.py's canonical path: seed 0, inter_mask=real_inter, the
committed rlg ensemble arrays). The only new code is bookkeeping that maps
window indices in the concatenated per-subject timeline (built by
`szcore_eval.build_timeline_masked`) back to the EDF file each window came
from, and a same-tolerance (30 s pre / 60 s post) overlap match between
reference seizures and detected intervals, mirroring
`szcore_eval.fast_event_match` -- used here only to attribute TP/FP to a
file, not to produce the headline counts (those remain the committed grid's).

USAGE
    python src/figures/find_running_example.py
"""
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
_src = _os.path.dirname(_here)
for _p in (_here, _src):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from pathlib import Path
import numpy as np

import szcore_eval as SE
import evaluation_protocol as E
import cpd_pipeline_v14 as V14

SUBJ = "chb13"
ENS_DIR = Path("results/phaseB/tier2/ens_test_tf/rlg")
SUMMARY_DIR = Path("data/summaries")
MAG_PCT, PEN_MULT = 50, 2.0
TOL_START, TOL_END = 30, 60
CANONICAL_SEED = 0


def file_window_ranges(subj, summary_dir):
    """Deterministic (no RNG) per-file window boundaries in the SAME order
    build_timeline_masked iterates edfs, using the identical n_win = dur //
    WIN_SEC rule. Returns list of (fname, w_start, w_end, n_seizures_in_file)."""
    edfs = E.parse_summary_edf_list(Path(summary_dir) / f"{subj}-summary.txt")
    out = []
    cum = 0
    for edf in edfs:
        n_win = edf["duration_s"] // SE.WIN_SEC
        out.append((edf["fname"], cum, cum + n_win, len(edf["seizures"])))
        cum += n_win
    return out


def which_file(w_idx, ranges):
    for fname, w0, w1, _ in ranges:
        if w0 <= w_idx < w1:
            return fname
    return None


def main():
    ei = np.load(ENS_DIR / f"ens_seed42_{SUBJ}_inter.npy")
    ec = np.load(ENS_DIR / f"ens_seed42_{SUBJ}_ictal.npy")

    np.random.seed(CANONICAL_SEED)
    signal, is_ictal, is_buffer, real_inter, sz_ranges, n_inter_h = \
        SE.build_timeline_masked(SUBJ, ei, ec, str(SUMMARY_DIR))

    cps, _ = V14.detect_changepoints(signal, PEN_MULT, min_mag_pct=MAG_PCT,
                                      local_win=15, inter_mask=real_inter)
    hyp_iv = SE.cps_to_events(cps, is_buffer, len(signal), sz_ranges=sz_ranges)
    ref_iv = [(s * SE.WIN_SEC, e * SE.WIN_SEC) for (s, e) in sz_ranges]

    ranges = file_window_ranges(SUBJ, SUMMARY_DIR)
    total_win = ranges[-1][2] if ranges else 0
    print(f"[{SUBJ}] {len(ranges)} EDF files, {total_win} windows in the "
          f"reconstructed timeline, {len(signal)} windows in build_timeline_masked "
          f"output (should match)")
    if total_win != len(signal):
        print("  [WARNING] window-count mismatch between file bookkeeping and "
              "build_timeline_masked -- boundaries below are not trustworthy")

    print(f"[{SUBJ}] m{MAG_PCT}/p{PEN_MULT}: {len(ref_iv)} reference seizures, "
          f"{len(hyp_iv)} raw hypothesis (per-change-point) intervals before "
          "per-file SzCORE scoring")

    # Authoritative per-file TP/FP: for each file, take the SAME raw hyp_iv
    # and ref_iv the committed grid was scored from, restrict to that file's
    # window range, shift to file-local time, and score with the identical
    # `szcore_eval.score_szcore` (timescoring) call used everywhere else in
    # this project -- so the merge/overlap/tolerance rules are the real ones,
    # not a re-implementation.
    per_file = {}
    for fname, w0, w1, nsz in ranges:
        t0, t1 = w0 * SE.WIN_SEC, w1 * SE.WIN_SEC
        ref_local = [(r0 - t0, r1 - t0) for (r0, r1) in ref_iv if t0 <= r0 < t1]
        hyp_local = [(h0 - t0, h1 - t0) for (h0, h1) in hyp_iv if t0 <= h0 < t1]
        sc = SE.score_szcore(ref_local, hyp_local, t1 - t0, n_inter_h=1.0)
        per_file[fname] = dict(n_seizures=nsz, tp=sc["tp"], fp=sc["fp"])

    print(f"\n{'file':<16}{'n_seizures':>12}{'tp':>6}{'fp':>6}   candidate?")
    candidates = []
    for fname, w0, w1, nsz in ranges:
        d = per_file[fname]
        ok = d["tp"] >= 1 and d["fp"] >= 1
        if ok:
            candidates.append(fname)
        print(f"{fname:<16}{nsz:>12}{d['tp']:>6}{d['fp']:>6}   {'YES' if ok else ''}")

    print()
    if not candidates:
        print("NO chb13 EDF file has both >=1 matched seizure and >=1 false positive "
              "at m50/p2.0. STOP -- do not relax a condition or switch patient "
              "(brief §2). Report this as a blocker.")
        return

    chosen = candidates[0]
    d = per_file[chosen]
    print(f"CHOSEN: {chosen}  (tp={d['tp']}, fp={d['fp']}, n_seizures_in_file={d['n_seizures']})")


if __name__ == "__main__":
    main()
