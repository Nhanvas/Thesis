# Running-example recording — Task A, Figure Brief Round 2

**Status: blocked. No chb13 EDF file satisfies the brief's two conditions
simultaneously.** Per §2 rule ("If no single recording satisfies both
conditions, say so and stop; do not silently relax one of them or switch
patient") and rule 8 ("A refusal is a valid answer"), this is reported as a
blocker rather than resolved by relaxing a condition or using a different
patient. Fig 2.10, Fig 3.4 and Fig 3.10 cannot be built until this is
resolved by whoever owns the brief.

## What was checked

Patient **chb13** (locked by the brief; window-level discrimination 0.822,
close to the across-patient 0.805 — see `docs/VERIFIED_NUMBERS.md` §1.2).
Operating point **m50/p2.0** (`min_mag_pct=50, pen_mult=2.0`), the reported
headline (brief rule 6).

Method (`src/figures/find_running_example.py`):

1. Load the committed ensemble arrays
   `results/phaseB/tier2/ens_test_tf/rlg/ens_seed42_chb13_{inter,ictal}.npy`.
2. Reconstruct the per-subject timeline with `szcore_eval.build_timeline_masked`
   (seed 0, matching the canonical convention already used by
   `src/phaseB/extract_latency_rlg.py`), which concatenates chb13's 33 EDF
   files in filename order.
3. Detect change points with `cpd_pipeline_v14.detect_changepoints` at
   m50/p2.0 with `inter_mask=real_inter` — the same call the locked grid was
   produced from. No smoother or penalty logic was re-implemented.
4. Recover each EDF file's window range deterministically (`duration_s //
   4`, the same rule `build_timeline_masked` uses; no randomness involved),
   then, for each file, restrict the reference seizures and the raw
   per-change-point hypothesis intervals to that file's window range and
   score them with the SAME `szcore_eval.score_szcore` (timescoring,
   authoritative) call used everywhere else in this project — not a
   re-implementation of the matcher.
5. Summed over all 33 files this reproduces the committed grid exactly: 9
   TP / 12 seizures (sensitivity 0.750) and 9/(9+32) = 0.220 precision,
   matching `results/phaseB/tier2/rlg_test/final_eval_seed42.csv` and the
   brief's own self-check line for chb13 (`0.750 0.220 0.340 23.4`). This
   confirms the per-file split is not losing or double-counting events at
   the boundaries.

## Result — per file

| File | Seizures | TP | FP | Both present? |
|---|---|---|---|---|
| chb13_02.edf | 0 | 0 | 3 | no |
| chb13_03.edf | 0 | 0 | 4 | no |
| chb13_04.edf | 0 | 0 | 1 | no |
| chb13_05.edf | 0 | 0 | 2 | no |
| chb13_06.edf | 0 | 0 | 0 | no |
| chb13_07.edf | 0 | 0 | 1 | no |
| chb13_08.edf | 0 | 0 | 1 | no |
| chb13_09.edf | 0 | 0 | 1 | no |
| chb13_10.edf | 0 | 0 | 4 | no |
| chb13_11.edf | 0 | 0 | 0 | no |
| chb13_12.edf | 0 | 0 | 2 | no |
| chb13_13.edf | 0 | 0 | 3 | no |
| chb13_14.edf | 0 | 0 | 6 | no |
| chb13_15.edf | 0 | 0 | 4 | no |
| chb13_16.edf | 0 | 0 | 0 | no |
| chb13_18.edf | 0 | 0 | 0 | no |
| chb13_19.edf | 1 | 1 | 0 | no |
| chb13_21.edf | 1 | 1 | 0 | no |
| chb13_22.edf | 0 | 0 | 0 | no |
| chb13_24.edf | 0 | 0 | 0 | no |
| chb13_30.edf | 0 | 0 | 0 | no |
| chb13_36.edf | 0 | 0 | 0 | no |
| chb13_37.edf | 0 | 0 | 0 | no |
| chb13_38.edf | 0 | 0 | 0 | no |
| chb13_39.edf | 0 | 0 | 0 | no |
| chb13_40.edf | 2 | 0 | 0 | no |
| chb13_47.edf | 0 | 0 | 0 | no |
| chb13_55.edf | 2 | 2 | 0 | no |
| chb13_56.edf | 0 | 0 | 0 | no |
| chb13_58.edf | 1 | 1 | 0 | no |
| chb13_59.edf | 1 | 1 | 0 | no |
| chb13_60.edf | 1 | 0 | 0 | no |
| chb13_62.edf | 3 | 3 | 0 | no |

Totals: 12 seizures, 9 TP, 32 FP — no file has both a TP and an FP.

## Why this happens (not a bug)

Every false positive at this operating point falls in a file that contains
no seizure at all; every file that contains a seizure produces only matched
(TP) or entirely missed (chb13_40, chb13_60 — FN) detections, never an
extra unmatched change point. Files with a seizure are short, dominated by
the one ictal transition PELT is tuned to find; the false alarms cluster in
the longer seizure-free files. This is a real structural property of the
chb13 detections at m50/p2.0, not an artefact of the per-file bookkeeping —
the per-file split reproduces the committed pooled sensitivity (0.750) and
precision (0.220) for chb13 exactly.

## Consequence

Fig 2.10, Fig 3.4 and Fig 3.10 are **not built**. Building any of them would
require either relaxing a condition (e.g. allowing the false positive to be
drawn from a neighbouring file, or allowing the "one recording" to mean
something looser than one EDF file) or switching away from chb13 — both
forbidden by the brief. This is reported as a blocker per §7 of the brief.
