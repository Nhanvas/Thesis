# V9-V1-FIX — Make the EEG figures slide-ready and fix two defects (Claude Code, laptop)

Estimated runtime: 30–60 min (estimated, not measured). Light job; run after V9-X1. Windowed reads only.

## Defects found by looking at the figures (cloud chat, 30/10)
1. **Part 4 selection bug:** for types f3 and f4 the "extreme" and "median" panels are the same event (`f3_*_chb03_2424`, `f4_*_chb03_3588`), although f4 has 176 members. Fix the median pick (median percentile of the type, excluding the extreme), redraw, and report the cause.
2. **SzScan screenshots unreadable:** at 75 µV the traces saturate into black; the crop shows 10 channels, a mouse cursor and a clock time. Retake (Playwright, read-only, no labelling, demo started with `web_demo/start_demo.sh`) for the same four events at a readable sensitivity (try 300 µV and 500 µV; keep the one where background and event are both visible), full 18-channel view, cursor outside the plot, and crop away the clock time if the UI shows one. Stop the demo after.
3. **Internal labels and forbidden claims in figure titles:** remove "V9-V1 Part …", "frozen G", "|diff| = 0.000" and file-system words from every slide version. Titles: patient · file · TP / missed / false alarm · duration (and "after the review" nowhere — that label goes on the slide, not the figure).

## Part 1 slide figure: redo
- The current `descriptors_by_set_slide.png` has overlapping titles, cut tick labels, and two weak descriptors: "dominant frequency" sits at the 1 Hz floor for most seizures, and "spatial extent (RMS > 2)" is 0 for many caught seizures.
- New slide figure, two panels, test seizures only, caught vs missed, from committed files:
  (a) **number of channels with ictal discharge from the author's blind annotation** (`results/attribution_v7/labels/ictal_channels_FINAL.csv`), focal vs generalized marked;
  (b) amplitude ratio (keep).
  Use the detection of the frozen system after the localizer (seed 42, `results/e23_test_look7/`) and also report the counts for `results/p3_anatomy/seizures.csv`. Print in the figure note: medians and the Mann–Whitney p for focal seizures (computed here, from committed files).
- Keep the 5-descriptor figure as a backup version with fixed layout.

## Part 1 extra check (chb06)
`chb06_01.edf` seizure at 1724 s: a large generalized rhythmic discharge is visible from about 1710 s, before the annotated onset, and the ensemble score stays low (≈ 0.2) during it. Measure for chb06: how many non-seizure 4-s windows have a generalized high-amplitude discharge of the same kind (≥ 12 channels with RMS ratio > 3 vs the preceding 60 s), and their ensemble percentiles; same for one easy patient (chb03). This tests whether chb06's own background contains frequent seizure-like generalized discharges that the per-patient normal absorbs.

## Rules
Read-only on frozen scripts and committed results; edit only `src/v9_eeg_evidence.py` (or a new `src/v9_v1_fix.py`); outputs `results/v9_v1/fix/` and the same figure folders (keep the old files with suffix `_old`). Commit only these paths.

## Return format
Full report to `F:/Study/Thesis/Agent/inbox/V9_V1_FIX_REPORT.md`.
