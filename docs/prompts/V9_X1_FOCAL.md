# V9-X1 — Why focal seizures are missed, and a focal-aware ensemble member (Claude Code, laptop)

Estimated runtime: Part 0 ≈ 15 min, Part A 1–2 h (estimated, not measured). Cache-based (`results/v9_e1/cache/`, `results/p2_test/`, X1 caches); single worker; smoke first; resumable.

## Why (verified in the cloud chat from committed files, 30/10)
Using the author's blind channel annotation (`results/attribution_v7/labels/ictal_channels_FINAL.csv`) and the frozen detector of `results/p3_anatomy/seizures.csv` (seed 42, test): **missed focal seizures involve fewer annotated channels than caught ones — median 3 vs 6, Mann–Whitney p = 0.0001; no caught focal seizure had fewer than 4 channels.** chb15 (median 2 channels) 0/20 at that stage. The thesis ensemble uses the 6th, 9th and 12th largest channel scores + the channel mean, so by construction a seizure confined to ≤ 3 channels cannot raise most members. In the 18-channel double banana every electrode appears in at most 2 bipolar pairs, so the **3rd-largest** channel is immune to any single-electrode artifact while still reaching 3-channel seizures.

## Part 0 — reproduce and show the mechanism (no new model)
1. Reproduce the annotation analysis above at two stages: `p3_anatomy` detector and the final system after the localizer (seed 42; `results/e23_test_look7/`). Report counts, medians, Mann–Whitney, and the table "annotated channels ≤ 3 vs ≥ 4 × caught / missed". Note how chb06 (generalized, 18 channels, 12–20 s) differs.
2. Mechanism: for every test seizure, the peak over its windows of the r-th largest channel robust-z (r = 1, 2, 3, 6, 9, 12, after the ±15-min correction) expressed as a within-patient percentile of the same member; plot by annotated channel count (≤ 3 vs ≥ 4) and caught/missed. Expected if the hypothesis holds: missed focal seizures are high on r = 1–3 and low on r ≥ 6.
3. Check whether the node features are computed on the bipolar signal or after CAR (open `c1b_build_trainset.py` / graph code); state it, because CAR would spread a single-electrode artifact.
Write `results/v9_x1/part0/` and commit.

## Part A — one pre-registered change per arm
- Ensemble members **{3rd, 6th, 9th, 12th largest, channel mean}** (each with the same ±15-min correction, patient percentiles, equal mean), for G and for F (the B4 part of F gets the same member set). Everything else frozen.
- k recalibrated with `p3_levers.calibrate()` unchanged on the 15 development patients (label-free). The development set contains focal hard cases (chb12, chb21), so it is a fair selection set.
- Secondary, descriptive only (not eligible for adoption): the same with the 2nd largest instead of the 3rd.
- Evaluate once on development, CHB-MIT test, chb24, Siena 14: tp/ref, FP, sens, prec, F1, FP/day (pooled, per-patient mean), 4 seeds for G and F; system-stage matched-FP curve (20 / 27.5 / 44); paired patient bootstrap vs the same arm without the change; detections by annotated channel count (test, ≤ 3 vs ≥ 4); onset/offset error; false-alarm types (same rule as `results/v9_v1/` Part 4).
- **Adoption rule (fixed now):** adopted for an arm if on development the paired difference at 27.5 FP/day has point estimate > 0 and 95 % CI lower bound ≥ −0.02. Test, chb24 and Siena are reported whatever the verdict.
- EEG: draw (convention of `src/v9_eeg_samples.py`, slide + full versions) every test seizure that the change newly catches and every one it newly loses (up to 6 each, shortest first), with the member scores r = 1, 3, 9 as strips.

## Rules
Read-only on frozen scripts and committed results; new code `src/v9_x1_focal.py`; outputs `results/v9_x1/`, figures `F:/Study/Thesis/Defense/slides/figs/eeg_evidence/x1/`; commit only these paths. Do not touch `web_demo/`.

## Return format
Full report to `F:/Study/Thesis/Agent/inbox/V9_X1_REPORT.md`.
