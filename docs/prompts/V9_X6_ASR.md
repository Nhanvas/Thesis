# V9-X6 — Does preprocessing artifact removal delete seizure activity? (Claude Code, laptop)

Estimated runtime: measure on one file first; projected 1.5–4 h (estimated, not measured). Run after V9-X1 (one heavy job at a time). Single worker; windowed reads only (never preload a whole EDF); smoke first; resumable.

## Why
The reviewer asked why the pipeline has no artifact-removal step. The current answer rests on literature and on indirect evidence from our data (an artifact model trained on non-seizure high-amplitude windows called 81.5 % of seizure windows artifact, `results/e4_artifact_rejection/`; muscle-band share is higher in seizure than in background windows, AUROC 0.65, `results/raw_eeg_view/`). This task measures it directly with a standard, label-free preprocessing method.

## Method (fixed now)
- **Artifact Subspace Reconstruction** (`pip install asrpy`, version printed), applied per recording file to the 18 bipolar channels after the pipeline band-pass/notch, 256 Hz, default cutoff 20 and a second run at cutoff 5 (aggressive), calibration on the file's own data with asrpy's built-in clean-window selection (no labels).
- Files: every seizure-containing file of the development and test patients (CHB-MIT), plus chb24; same number of seizure-free files per patient chosen with `random.Random(42)`.

## Measures
1. **What ASR removes:** for every annotated seizure, share of signal power removed (1 − power after / power before) inside the seizure, in the 60 s before it, and in label-free high-amplitude (±5 SD) non-seizure windows and ordinary background windows; per patient and pooled; by annotated channel count (test seizures, `results/attribution_v7/labels/ictal_channels_FINAL.csv`) and by duration bin.
2. **Effect on detection (kNN only, no retraining):** recompute the 12 per-channel node features on the ASR-cleaned files and run B4 (the V9-E1b chain, fixed `k_B4` from `results/v9_e1b/calibration.json`) on the test patients and chb24, with the same files uncleaned as the reference; report sensitivity, false alarms and per-seizure caught/lost.
3. EEG panels (slide + full version, convention of `src/v9_eeg_samples.py`): 3 seizures with the largest power removed and 3 high-amplitude non-seizure windows with the largest power removed, before vs after ASR, same scale.

## Rules
Read-only on frozen scripts and committed results; new code `src/v9_x6_asr.py`; outputs `results/v9_x6/`, figures `F:/Study/Thesis/Defense/slides/figs/eeg_evidence/x6/`; commit only these paths.

## Return format
Full report to `F:/Study/Thesis/Agent/inbox/V9_X6_REPORT.md`.
