# Running-example recording — Fig 2.10 · Fig 3.4 · Fig 3.10

**Status: resolved. Chosen recording: `chb13/chb13_62.edf`. One file suffices for all
three figures.**

## What changed since the previous version of this file

The previous version of this file reported the running example as blocked: at the
substituted-timeline operating point (`m50/p2.0`, scored via
`szcore_eval.build_timeline_masked`), no chb13 file had both a matched seizure and a
false positive, and every false positive fell in a seizure-free file. That was read as
"a real structural property of the chb13 detections."

`docs/diagnostic_q_chb13.md` and `docs/FIGURE_ROUND4.md` §1 disproved that reading: the
committed background score array for chb13 (`ens_seed42_chb13_inter.npy`, 12,452
entries) is exhausted by global window 12,451 — inside `chb13_15.edf`, 41.9% of the way
through the concatenated 33-file timeline. Every window after that point, in every file
regardless of seizure content, receives a bootstrap-resampled score and is excluded from
`real_inter`. The eight seizure-containing files all happen to sit after that exhaustion
point in file order, so "no seizure-containing file produces a false positive" was an
artefact of the substituted timeline, not a property of the detector. That conclusion is
withdrawn and must not be cited.

`docs/FIGURE_ROUND4.md` §3 approved a deviation for these three figures only: recompute
the anomaly score on every window of one continuous recording (no artifact rejection, no
`build_timeline_masked`), using the study's fitted checkpoint, calibration and covariance.
See `src/figures/continuous_rescore.py`.

## Recording selection (R4 §3.2)

Candidates were tried in the order R4 prefers: files with several seizures first.
`chb13_62.edf` (3 annotated seizures) was tried first and satisfied both conditions
immediately — **no second file was needed**.

Recomputed at the reported operating point (`min_mag_pct=50`, `pen_mult=2.0`,
`cpd_pipeline_v14.detect_events`, label-free — `inter_mask=None`, since a single
continuous file needs no multi-file buffer mask and `build_timeline_masked` is forbidden
for these three scripts):

| | |
|---|---|
| Detected intervals | `(760,764)`, `(960,1064)`, `(1660,1684)`, `(1860,1864)`, `(2120,2204)` s |
| Annotated seizures | `(851,916)`, `(1626,1691)`, `(2664,2721)` s |
| Matched against annotation (`szcore_eval.score_szcore`, SzCORE tolerance) | **tp=2, fp=3**, n_ref=3, n_hyp=5 |

Both conditions are met on this single file: at least one correctly detected seizure
(2) and at least one false positive (3). Per R4 §3.2, all three figures use it.

## Acceptance gate (R4 §3.3)

Ictal windows are never artifact-rejected, so the committed
`results/phaseB/tier2/ens_test_tf/rlg/ens_seed42_chb13_ictal.npy` array is complete and
rows follow seizure order (`results/attribution_v6/ictal_row_to_seizure.csv` gives the
row → file/window mapping). The recomputed fused score was aligned at `chb13_62.edf`'s
three seizures (global rows 95–143) against the corresponding committed rows:

| Seizure (global index) | n windows | Pearson r |
|---|---|---|
| 9 | 17 | 0.999610 |
| 10 | 17 | 1.000000 |
| 11 | 15 | 0.999775 |
| **Pooled (49 windows)** | | **0.999861** |

**Gate: pooled correlation ≥ 0.99 → PASS.** The recomputation reproduces the study's own
pipeline. (The same calibration was independently checked component-by-component before
this gate: recomputing `zrecon`/`zlatent`/`zgamma` on the committed ictal
adjacency/feature/gamma arrays and comparing to the committed
`results/phaseB/tier2/ens_test_tf/components/{zrecon,zlatent,zgamma}_chb13_ictal.npy`
files gives correlations of 0.9999999999, 0.9999999999, and 1.0 respectively — the
end-to-end pipeline, not just the final fused score, matches.)

## What each figure shows

- **Fig 2.10** — fused score vs. time (minutes) for the full `chb13_62.edf`, 12 raw
  change points, all three annotated seizures shaded.
- **Fig 3.4** — the three component scores (`zrecon`, `zlatent`, `zgamma`), the fused
  score, detected intervals (green) and annotated seizures (red), stacked on a shared
  axis.
- **Fig 3.10** — the false-positive interval `[2120, 2204]` s (chosen as the FP interval
  with the largest separation from any annotated seizure's tolerance window), fused score
  above and the raw six-channel EEG below, ±60 s context. No annotated seizure overlaps
  `[2120, 2204]` s — confirmed directly from the summary file (nearest seizure ends at
  1691 s / next begins at 2664 s).

Caption text (printed by each script, not baked into the PNG): *"Scores were recomputed
on the continuous recording with every window retained (no artifact rejection), using
the study's fitted checkpoint, z-score statistics, robust-z calibration and latent-space
covariance; they are not the source of any reported number."*
