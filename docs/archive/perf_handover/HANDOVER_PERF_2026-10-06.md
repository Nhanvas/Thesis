# HANDOVER — performance-improvement phase (chat of 2026-10-05/06)
Written 2026-10-06 ~19:30. Supersedes nothing in docs/; it records a phase that the canonical docs
(RESULTS_OF_RECORD, PROJECT_STATUS, project instructions §5 "optimization is over") do NOT yet reflect.
Boti decided on 2026-10-05 to re-open performance work. Every number below was read from a run output.

## 0. Working rules agreed in this chat (keep them)
- Understand raw EEG and the failure mechanism first; test before proposing; explain simply; Boti approves.
- One pre-registered configuration and gate per experiment, written in the script docstring BEFORE running.
- Decisions on the 15 non-test subjects (12 train + 3 val); the test set is looked at only after a freeze.
- Give whole files with target paths, commands with runtime estimates, commit explicit paths.
- Registration form (signed, fixed): title "Unsupervised Epileptic Seizure Temporal Localization in Scalp EEG
  using Graph Autoencoder and Change Point Detection". Objective 1: unsupervised anomaly scoring with
  spatial-temporal features. Objective 2: temporal localization with **non-parametric** change point
  detection on the ensemble anomaly score. Lit-review focus: **threshold calibration and baseline drifts**.
  Evaluation: event-level on CHB-MIT. => no supervised component; CPD must remain the localization step.

## 1. Starting point (continuous-timeline evaluation, before this chat)
Locked rlg + PELT on the real continuous timeline, TEST: sens 0.303 at 73.3 FA/day (cell 50/2.0/90);
cell A8: 0.079 at 19.2 FA/day; application: 0.211 at 52.4. The offline headline (F1 0.213, 27.4 FA/day)
came from a timeline rebuilt from labels with bootstrapped interictal scores (szcore_eval.build_timeline_masked).

## 2. What was measured in this chat (scripts in src/, outputs in results/)
| step | result | established |
|---|---|---|
| diag_detector_ceiling (val) | PELT alarms on falling CPs too; removing flagged non-ictal windows (oracle) cuts FP ~85–90 % | high-amplitude non-seizure windows drive FPs |
| raw_eeg_view | ±5 SD rule flags 46 % of training interictal; ictal ~90 % flagged; separators: spatial spread, theta, kurtosis | the flag is "high amplitude", not "artifact" |
| E1 feature GMM, cross-patient, clean vs all | FAIL (0.340 vs 0.372) ; k 8 vs 32 same | redefining "normal" across patients does nothing |
| E3 supervised HGB, LOSO | 0.702 at 20.5 FA/day | reference only (labels) |
| E4 artifact model on ±5 SD labels | FAIL, 81.5 % of seizure windows called artifact | predictable design error |
| E5 per-patient feature GMM | event 0.340 → 0.596 (window gate K2 missed by 0.001) | patient-own density works when the input carries the information |
| E6 per-patient density on v1 GAE outputs | FAIL; v1 + threshold detector D1 = 0.479 (subset) | v1 representation lacks it |
| code reading | v1 node features lose amplitude AND window spectral shape (per-window z-score, then per-window min-max per band) | root cause of E5 vs E6 |
| E7 | ensemble+F < F; PELT used as segmenter (D2) < D1 (grid covered 100 FA/day) | — |
| C1 / C1b | 7 added node features (log band power ×5, log line length, signed-log kurtosis), training-set z, clip ±4 → [0,1]; data/trainset_v2 (15 subj, all files; chb12_27/28/29 skipped: missing channel) | — |
| GAE v2 (Kaggle) | node input 30, decoder output 12, 3,964 parameters (v1 3,285; both computed from layer sizes); clean & all × seeds 42,1; then clean seeds 2,3 | loss converged, no overfit |
| **E8** full recordings, 15 non-test | V1 0.330 @23.7 → **v2 clean V2_LW 0.489 @19.8** (2 seeds, SD 0.030); val 7/15 → 11/15; gains in 8 subjects, none lost | rule C passed (+0.159); v2 ADOPTED |
| E8 diag | v2 raises seizure scores (median 1.40→2.31, p90 3.77→5.16), flagged unchanged | — |
| **E9 one-shot TEST** (frozen v2 clean V2_LW, D1 smooth 15, top 2 %) | **v2 3/76 (0.039) @24.1; 4 seeds 0.043 ± 0.007 @24.8; V1 2/76 @24.2**; window macro AUROC V1 0.640 → v2 0.680 (6/8 patients up); short seizures 0/18; top 5 %: v2 27/76 @60.6, V1 24/76 @62.1 | event level did NOT transfer |

E9 sanity: V1 top-5 % 24/76 @62 matches the independent earlier continuous eval (23/76 @73); non-ictal hours
277.6 vs offline 278.2. E9 precision/F1 columns are INVALID (own formula; SzCORE splits events > 5 min, so its
FP count exceeds the hypothesis count) — recompute from SzCORE outputs before reporting.

## 3. Diagnosis after E9 (the part not yet fixed)
The artifact-confusion fix is real at window level (test AUROC up on 6/8) but too small for the extreme tail.
The event-level collapse on test comes from the DETECTION stage, i.e. exactly the form's "threshold calibration
and baseline drifts":
1. D1 thresholds the global level (patient's top-p): long elevated states (sleep, sustained artefact) own that
   tail; test seizures are not globally extreme (Part B oracle: test seizure peaks exceeded by 20–50 % of
   non-ictal spans vs 4 % on validation; e.g. chb15 AUROC 0.70, 0/20).
2. Long plateaus are split by SzCORE into several FPs.
3. 60 s smoothing erases short seizures (18/76 on test, only 3 in the selection set — the selection set could not
   see this risk).
4. The 15-subject selection set over-predicted test (also because 12 of them are GAE training patients).

## 4. Running now / next
- **E10 `src/e10_kernel_cpd.py`** (cache-only, ~30–90 min est.): non-parametric kernel CPD (ruptures KernelCPD,
  rbf, min_size 8 s, pen {2,4,8}) on the unsmoothed v2 score; alarm = segment that rises above BOTH neighbours
  (onset+offset change point), duration ≤ 300 s, prominence in the patient's own top p of candidates.
  Compared with D1 and D1c (D1 minus events > 300 s). Gate in the docstring (≥ D1 + 0.10 at ≤ 25 FA/day,
  validation not lower, ≥ 9 subjects not worse). If adopted → second test look, disclosed as such.
- Decision log: v2 stays the adopted model (rule C). PELT-with-l2 is parametric; the form asks for
  non-parametric CPD — kernel CPD fits the form better.
- Still open for the supervisor (8/10): how to present offline vs continuous evaluation; test looked at more than
  once (veto screen one-shot, E9, possibly E10) — must be disclosed; demo/report rework if v2 + new detector.
- Not pursued (time): TUH artifact corpus (future work); supervised (title); test-time adaptation of the GAE on
  each patient's own recording (label-free, plausible, no evidence yet).

## 5. SzCORE tooling to check (Perplexity prompt, English)
"For the SzCORE framework (Dan et al., Epilepsia 2024; https://epilepsybenchmarks.com): what do the tools
epilepsy2bids, timescoring, szcore-evaluation, sz-validation-framework and the szcore benchmark repository each
do? Does the benchmark publish per-dataset results (CHB-MIT in particular, BIDS version on Zenodo, 18-channel
double-banana) for named algorithms, with event-based sensitivity, precision, F1 and FP/day? List those algorithms,
whether they are supervised or not, and their CHB-MIT numbers with the source page. How does szcore-evaluation
aggregate across recordings and subjects (sum of counts vs mean of per-subject scores)?"
Use: comparators under the identical protocol and an official, recording-wise scorer for the final numbers.

## 6. Files of this phase
src: diag_detector_ceiling, e1_normal_definition, e3_supervised_loso, e4_artifact_rejection, e5_patient_density,
e6_dump_gae, e6_gae_patient_density, e7_ensemble_cpd, c1_nodefeat, c1b_build_trainset, c1t_build_testset,
retrain/train_gae_v2, e8_gae_v2_eval, e8_diagnostics, e9_test_oneshot, e10_kernel_cpd.
data: trainset_v2/ (15 npz), testset_v2/ (8 npz), models_v2/ (clean 42,1,2,3; all 42,1).
results: diag_detector_ceiling, e1…e7, e8_gae_v2 (+diag), e9_test_oneshot (tag e9-test-oneshot), e10_kernel_cpd.
Kaggle notebook: Agent/gae_v2_train.ipynb (dataset nhn2mm/gae-v2).
