# V9-FINAL — Close every open verification before the slides (Claude Code, laptop)

Estimated runtime: Parts B–F 1–2 h (light); Part A 2.5–4 h (heavy, run last, overnight). All estimated, not measured. One job at a time; single worker; smoke first; resumable; windowed EDF reads only.
**Before starting:** close Chrome/Edge/MATLAB (Task Manager → MathWorks Service Host too) and run Claude Code from **Git Bash, not from Cursor** (Cursor costs ≈ 1 GB).
Order: B → C → D → E → F (push) → A. Write one report at the end; if A is stopped by memory, report what is done.

---

## Part B — "Hard patients": verify the explanation with three detectors and all cases
The earlier explanation changed twice (short seizures → few channels → low amplitude). Settle it with committed data only:
1. Per seizure (development, CHB-MIT test, chb24 — 185+ seizures; Siena separately): amplitude ratio (ictal/pre RMS, `results/v9_v1/part1_descriptors.csv` or recompute with the same code), duration, annotated channel count (test only, `results/attribution_v7/labels/ictal_channels_FINAL.csv`).
2. Caught/missed for three detectors: the thesis system (seed 42, after the localizer: `results/p3c_freeze/` for development, `results/e23_test_look7/` for test, `results/x1_external/` for chb24/Siena), kNN leave-one-case-out (`results/v9_e4/`, regenerate per-seizure matches if the parts were cleaned), GAE-CV (`results/v9_x3/`).
3. For each detector: Mann–Whitney caught vs missed for amplitude ratio, duration and channel count; a logistic regression `caught ~ log(amp ratio) + log(duration)` with patient-cluster bootstrap CIs (B = 2,000). Report which descriptor survives in all three detectors.
4. Figure (slide version, 16:9, large fonts, no internal labels): amplitude ratio caught vs missed, one panel per detector, CHB-MIT all cases; note with n and p.
Output `results/v9_final/hard/`.

## Part C — Siena gap decomposition, formally
Reweight CHB-MIT-test per-bin detection rates (bins ≤20, 21–40, 41–80, >80 s; thesis system seed 42 after the localizer, same overlap rule for both sets) to Siena's duration mix; patient bootstrap CI of the reweighted sensitivity and of the share of the gap explained. Same for the amplitude-ratio mix (quartile bins of the pooled distribution). Output `results/v9_final/siena_gap/`.

## Part D — Slide figure pack (supervisor 30/10: "no illustration of a detected seizure"; results slides too dense)
One clean style for all: 16:9, ≥ 16 pt labels, **8 channels** (the 8 with the highest channel score in that event, names on the axis), real filtered EEG, grey band = annotated seizure, teal band = system event, thin score trace below with the alarm threshold line, onset/offset of the localizer as two vertical ticks, time in seconds, title = what it shows in plain words (e.g. "Detected seizure — patient chb03"), no file paths, no internal labels. Also a full 18-channel version for backup. Every pick by a rule written in `FIGURE_INDEX.md` **before** drawing.
1. Detected seizure, CHB-MIT test: the thesis-system true detection whose onset error is closest to the median onset error (rule), plus chb03's first seizure.
2. Missed seizure: the missed test seizure with amplitude ratio closest to the median of missed seizures.
3. False alarm: the highest-score false alarm of the median-false-alarm test patient.
4. Siena: one detected seizure (closest to the median onset error) and one missed.
5. Web demo: the retaken SzScan screenshot of chb03 (500 µV) next to the same event drawn in this style.
6. Hospital EEG: clin02 score timeline with the annotated activation segments (eyes, hyperventilation, photic, spikes) and the 3 system events; one clin01 event panel. Captions neutral ("segment flagged for review"); no artifact/seizure claim. Privacy rules of `V9_C1` apply.
7. Model comparison (internal, a figure is allowed): matched-FP system-stage curves of GAE, kNN and GAE + kNN on the 24-case cross-validation (`results/v9_x3/sys_sweep.csv`), per-case mean sensitivity vs FP/day.
8. ASR (after Part A): one seizure at the **median** share removed and one at the maximum, before/after, same scale.
Write `F:/Study/Thesis/Defense/slides/figs/final/` + `FIGURE_INDEX.md` (file · what it shows · selection rule · numbers in it with their source file · proposed caption).

## Part E — Number check of every post-review number
Recompute from committed files and print match / mismatch for each line of `F:/Study/Thesis/Defense/notes/NUMBERS_LOCK.md` §17, plus these (state the file and the exact value found):
- Siena matched-FP 0.481 / 0.534 / 0.673; CHB-MIT test 0.318 / 0.355 / 0.366; chb24 0.626 / 0.875 / 0.875.
- Siena per-patient mean 0.633 → 0.530 without patients with ≤ 2 seizures.
- E1b matched 27.5 FP/day test: 0.554 / 0.601 / 0.607; paired F − G +0.047 [+0.013, +0.086].
- E4 kNN 24 cases 0.763 [0.619, 0.888] at 17.7.
- X3: GAE-CV 0.735, kNN 0.763, GAE+kNN 0.791 (24 cases, own points); matched 27.5: 0.733 / 0.800 / 0.800; paired GAE − kNN −0.066 [−0.140, +0.001]; F1 GAE − kNN −0.076 [−0.125, −0.031]; GAE+kNN − GAE F1 +0.045 [+0.018, +0.077]; original test subset GAE-CV 37/76 at 31.55; development subset 0.807 (seed 42 thesis in-sample development per-patient mean for comparison: 0.847).
- X1: channel count caught vs missed after the localizer p = 0.792; before the budget p = 1.2e-4.
- V1-FIX: amplitude ratio caught vs missed (focal, test, after the localizer) p = 0.013.
- Hospital: 35 events, 2,272 s of 47,508 s = 4.78 %; clin02 3 events, 0 overlap with 27 marked segments.
- X6 (after Part A): pooled share removed in seizures vs high-amplitude vs background.
Output `results/v9_final/NUMBERS_CHECK.md`.

## Part F — Commit and push
Commit `src/v9_final_*.py`, `results/v9_final/` (explicit paths; no clinical data, no names), then `git push && git push --tags` so the cloud chat can verify.

## Part A — Finish the ASR measurement (heavy; last)
1. Complete cutoff 20 on the 23 remaining seizure files (chb16 3, chb17 3, chb18 6, chb24 11). One file per OS process; free memory after each. Drop cutoff 5 (report it as not done).
2. Add the detection-relevant measure for **all 70 files** (recompute the 47 done if the cleaned signal was not kept): per seizure, the **contrast** = median-channel RMS of the seizure / RMS of the 60 s before, before vs after ASR; and the same for high-amplitude non-seizure windows. If ASR lowers the seizure contrast, it removes what a detector needs. Report pooled and per patient, with patient bootstrap CIs.
3. Then draw Part D item 8.
Outputs to `results/v9_x6/` (append), figures to `.../eeg_evidence/x6/` and `.../figs/final/`. Commit and push again.

## Rules
Read-only on frozen scripts, models and committed results; new code `src/v9_final_*.py` (Part A may extend `src/v9_x6_asr.py`); never touch `web_demo/`; no clinical data or names in the repository.

## Return format
Full report to `F:/Study/Thesis/Agent/inbox/V9_FINAL_REPORT.md`, plus `FIGURE_INDEX.md` and `NUMBERS_CHECK.md` attached by the author.
