# L1 — what SzScan computes today, and why its run gives 0.528 against V5's 0.567

Track F, milestone M2, stream L, chat F2-03 (23/11/2026). Read-only: code and committed results at `main` = `912b166`;
no run. Answers `docs/FAILURE_REGISTRY.md` FM-25. Every number below is copied from the file cited; values marked
*computed* were derived here from those files.

## 1. What the application computes

Code: `web_demo/backend/pipeline_demo.py` (tag `szscan-frozen-v4.1`, build `8aabf4d`), `upload_manager.py`, `db.py`.

| step | what the application does | where |
|---|---|---|
| unit | **the patient**: Phase B (statistics → features → GAE → distances → ensemble score) starts only when every uploaded file of the subject has finished Phase A; every per-subject quantity is fitted on all windows of all files of the subject | `upload_manager._maybe_run_phase_b`, `pipeline_demo.process_subject_phase_b` |
| accepted input | subject id in `db.ALLOWED_SUBJECTS` (chb03, chb06, chb13–chb18, chb24); the 18 CHB-MIT bipolar channel names (`preprocessing.open_edf`, otherwise rejected); 256 Hz; header start time required | `db.py` l. 19; `process_file_phase_a` |
| filtering | whole-file zero-phase band-pass + 60 Hz notch (= `x1_external.filter_windows` = the record's `continuous_eval.filter_file`) | `process_file_phase_a` |
| z-score statistics | **label-free**: every 10th 4-s window of the whole recording (files in filename order, one counter over the subject), each window filtered with 3 s padding (= `x1_external.labelfree_stats` / `preprocessing.filter_window`); mean and SD (ddof 1) in float64 from stored per-window moments | `labelfree_zscore_stats` |
| features, model | `c1b_build_trainset.graph_and_bp` and `f7` on the z-scored windows (signal-loss windows skipped); GAE v2 **seed 42 only** (checkpoint verified by sha256) | `file_features`, `run_gae` |
| reference | per channel LedoitWolf Mahalanobis of the 16-d latent, fitted on every valid window of the subject | `channel_distances` |
| score | `e22_test_oneshot.final_scalar`: members 6th / 9th / 12th largest and channel mean, each minus its ±15-min running median **per file**, patient percentile, mean | `ensemble_score` |
| budget | `p3_levers.q_of` on the smoothed member-mean robust z with **k = 4.0677** (`results/p3c_freeze/freeze.json`, calibrated on the development patients with the record statistics); top = clip(q, 0.005, 0.02) **per patient** | `process_subject_events` |
| events | `p2_scalars.d1_events` (5-window smoothing, merge ≤ 90 s) and `p3_levers.localize(mode="cpd")`, inside each file | same |

Labels are never read (`web_demo/backend/tests/test_guards.py`). The chain after the statistics is V5's own code: with
the thesis statistics fed in (`stats_override`), the identity gate on chb03 reproduces V5's seed-42 rows exactly —
detector 7 / 23, localized 7 / 22, budget 0.005175, per-channel distance within 1.34e-6 relative
(`results/t1_demo/GATE.md`).

The evaluation of the application run is `src/eval_application_events.py` (SzCORE scoring with the project's
`SZ_PARAM`, per file, counts summed per subject; false alarms per day over the recorded time of the processed files
minus seizure time). V5's denominator is the non-ictal hours with signal (`p2_scalars.score`); the two differ slightly.

## 2. Why 0.528 and not 0.567

Per-patient mean sensitivity after the change point localizer, 8 test patients, per-patient budget, 76 seizures:

| system | seeds | sensitivity | detected | FP/day | source |
|---|---|---|---|---|---|
| V5 | 42, 1, 2, 3 (mean) | 0.567 | 36.25 / 76 | 28.7 | `results/eureka_d31f/9a/aggregate/T9A.md` |
| V5 | 42 | 0.577 | 37 / 76 | 26.8 | `results/e23_test_look7/summary_per_seed.csv` (balanced, localized) |
| features rebuilt from the verified EDF, record statistics (REBUILD) | 42 | 0.565 | 36 / 76 | 26.8 | `results/eureka_d31f/9a/aggregate/summary_per_seed.csv` (test, own, cpd) |
| label-free statistics, record k (EUR_9A, LF_krec) | 42 | 0.534 | 34 / 76 | 26.9 | same |
| application | 42 | 0.528 | 33 / 76 | 26.9 | `results/application_eval_v4/SUMMARY.md` |

Per patient (computed from `results/e23_test_look7/per_subject_seed.csv`, `results/eureka_d31f/9a/r13/lf_krec/per_subject.csv`
budget L2f stage cpd, `results/application_eval_v4/per_subject.csv`; detected seizures, seed 42):

| patient | V5 | EUR_9A LF_krec | application |
|---|---|---|---|
| chb03 | 7 | 6 | 6 |
| chb06 | 2 | 1 | 1 |
| chb13 | 1 | 1 | 1 |
| chb14 | 6 | 6 | 6 |
| chb15 | 11 | 11 | 10 |
| chb16 | 2 | 1 | 1 |
| chb17 | 3 | 3 | 3 |
| chb18 | 5 | 5 | 5 |

Reading:
1. **Seed.** The application uses seed 42 only; seed 42 alone (0.577) is above the 4-seed mean (0.567).
2. **Label-free z-score statistics** — the application's one designed divergence (`web_demo/SZSCAN_SPEC_v5.md` §1.6) —
   cost three seizures on seed 42 (chb03, chb06, chb16; 0.577 → 0.534). Part of it is the numerical difference of
   rebuilding the features from the raw EDF (REBUILD loses one seizure, 0.577 → 0.565; FM-28).
3. **One more seizure in chb15** (11 → 10; chb15's budget sits at the 2 % cap in both runs) separates the application
   from EUR_9A's label-free run, although both follow the same statistics rule. *Hypothesis:* a numerical difference
   between the two implementations of that rule (EUR_9A: `preprocessing.compute_subject_stats` with an empty seizure
   map, Welford in float64, stored as float32 µV; the application: float64 moments; different machines and library
   versions). *Check (not run; it changes no decision):* the application's headless path on chb15 with
   `stats_override` = EUR_9A's committed `results/eureka_d31f/9a/stats_lf/chb15_stats.json` (laptop, about 10 min) — equal
   events to EUR_9A's chb15 rows would confirm it.

So the gap is the label-free statistics (with the rebuild difference inside it), partly offset by the choice of seed;
the unit (patient), the reference, the budget rule and k are V5's.

## 3. Consequence for the SzCORE open benchmark (X1)

The open benchmark (`github.com/esl-epfl/szcore`, read 23/11: `config/template.Dockerfile`, `tests/data/*.edf`,
`.github/workflows/1-pr-check.yml`) runs a container **once per EDF file**
(`docker run -e INPUT=<file>.edf -e OUTPUT=<file>.tsv`), offline. The test EDF holds **19 electrodes referenced to the
common average** (`Fp1-Avg`, …, `T6-Avg`) at 256 Hz, and the output is a TSV with the header
`onset duration eventType confidence channels dateTime recordingDuration`. The application cannot be submitted as it
is: (a) its unit is the patient, not one recording; (b) `open_edf` rejects files without the CHB-MIT bipolar names (the
18 derivations can be formed exactly by subtraction from the 19 average-referenced electrodes); (c) the notch is fixed at
60 Hz. Stream L (L2, L3) defines and scores a protocol that estimates everything from one recording.
