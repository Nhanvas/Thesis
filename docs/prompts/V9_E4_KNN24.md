# V9-E4 — kNN baseline (B4) on every CHB-MIT case (Claude Code, laptop)

Estimated runtime: 1–2 h (estimated, not measured). One patient at a time, single worker. Smoke on one patient, report the projected total.

## Why
B4 (12 per-channel node features → per-patient kNN distance) has **no trained component**: every fit is per patient and label-free. Only its budget constant `k_B4` came from the development patients. It can therefore be evaluated on all CHB-MIT cases, giving a larger sample than the 8 test patients and a per-patient picture of which patients are hard.

## Steps
1. Cases: chb01–chb24, same file rules as the thesis (files missing one of the 18 channels skipped, e.g. chb12_27/28/29). **chb21 is the same subject as chb01** (recorded 1.5 years later): report 24 cases, and also the aggregate with chb21 removed (23 subjects).
2. Calibration without in-sample bias: **leave-one-case-out k** — for each case, `k_B4` = `p3_levers.calibrate()` unchanged on all other cases (chb01/chb21 never calibrate each other). Also report results with the fixed development `k_B4 = 11.618333` for reference.
3. Same chain as V9_E1b (clip 0.005/0.02, smoothing 5, merge 90 s, CPD, SzCORE scorer, label-free statistics everywhere).
4. Report: per case tp/ref, FP, sensitivity, precision, F1, FP/day, number of seizures, median seizure duration, mean seizure duration; aggregate pooled and per-patient mean with patient bootstrap 95% CI; the same for the former development and test groups separately; duration bins; system-stage matched-FP curve (20 / 27.5 / 44).
5. "Hard patient" table (definition fixed now, from the literature exclusion rule): mean seizure duration < 30 s. List which cases meet it and their sensitivity vs the others (Mann–Whitney on per-patient sensitivity, descriptive).

## Rules
Read-only on frozen scripts and committed results. New code `src/v9_e4_knn24.py`; outputs `results/v9_e4/`. Commit only these paths. Do not touch `web_demo/`.

## Return format
Full report to `F:/Study/Thesis/Agent/inbox/V9_E4_REPORT.md`.
