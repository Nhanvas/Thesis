# V9-T4 — Siena: complete the verification on all 14 patients (Claude Code, laptop)

Estimated runtime: download unknown (measure the size first and tell the author before downloading); processing 1–3 h (estimated, not measured). Measure one patient and report the projected total before running all.

## Why
`V9_T3` could only use 3 of 14 Siena patients (PN00, PN10, PN11): the other EDFs were processed on Kaggle and are not on this laptop. The supervisor finds the higher Siena result "strange"; the matched-operating-point answer must cover all 14 patients before it goes on a slide.

## Steps
1. Find where `src/x1_external.py` expects the Siena EDFs (its path constant). Check free disk space. Get the dataset size from PhysioNet (`siena-scalp-eeg/1.0.0`) **before** downloading and report it.
2. Download only what is missing (resumable: `wget -r -N -c -np https://physionet.org/files/siena-scalp-eeg/1.0.0/` or `aws s3 sync --no-sign-request s3://physionet-open/siena-scalp-eeg/1.0.0/ <dir>`). Outside the repo; never commit data.
3. Gate first: for every patient, the recomputed tp must equal `results/x1_external/rows_PN*.csv` (seed 42, balanced, localized) and fp within the tolerance already documented in `src/v9_anatomy.py`. If a patient fails the gate, stop and report.
4. Re-run the Siena parts of `src/v9_anatomy.py` on all 14 patients (`siena-14`): per-seizure table, duration bins, matched operating point (sens at 20 / 27.5 / 44 FP/day, pooled and per-patient mean), false-alarm anatomy.
5. Add: Siena **event F1 and precision, pooled and per-patient mean**, from the scorer's counts (SzCORE aggregates per subject), seed 42 and 4-seed mean, at the frozen operating point.
6. Re-draw the Siena EEG panels with the original rule (4 patients with the most seizures + the shortest seizure) now that all patients are available; keep the 3-patient set as is.

## Rules
Same as `V9_T3`: read-only on frozen scripts and committed results; new outputs under `results/v9_anatomy/siena14/` and `F:/Study/Thesis/Defense/slides/figs/eeg_samples/siena14/`; commit only your own new paths; no retraining.

## Return format
Write the full report to `F:/Study/Thesis/Agent/inbox/V9_T4_REPORT.md`: gate result per patient, the matched-operating-point table (chb-test, chb24, siena-14), duration bins, F1/precision table, false-alarm anatomy summary, figure list.
