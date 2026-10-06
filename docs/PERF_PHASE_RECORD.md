# PERF_PHASE_RECORD — performance phase (re-opened 2026-10-05)

**Rev. A, 2026-10-06.** Single source for the performance phase. Supersedes
`HANDOVER_PERF_2026-10-06.md` (archived) and the chat audits `audit_1`–`audit_7`.
Stage **P1** (E1–E10) is CLOSED. Stage **P2** (E11 onward) is planned in §6 and starts in a new chat.

Authority: for every number in this file the primary source is the `SUMMARY.md` / CSV named beside it.
`RESULTS_OF_RECORD_phaseB.md` stays authoritative for the **offline-protocol** numbers of the locked
system (rlg, "V1"); this file is authoritative for **continuous-timeline** numbers and for every
decision taken in the performance phase. On a conflict about the current state, this file wins over
`PROJECT_STATUS.md` (rev F, 2026-09-28), which predates the phase.

Naming: the performance-phase experiments are `E1`–`E10` (`src/eN_*.py`) and continue as `E11`, `E12`, …
They are unrelated to the Phase-B readout experiments also once called "E1/E2" in `PROJECT_STATUS.md` §1.
"V1" = the locked rlg GAE (`gae_joint_seed42.pt`, 3,285 parameters). "v2" = the GAE retrained in P1.

---

## 0 · Constraints that bound every decision

- **Registration form (signed, fixed).** Title: *Unsupervised Epileptic Seizure Temporal Localization in
  Scalp EEG using Graph Autoencoder and Change Point Detection*. Goal: unsupervised framework for
  temporal seizure localization (onset and offset) in multi-channel scalp EEG. Objective 1: unsupervised
  anomaly scoring with spatial-temporal features. Objective 2: temporal localization with
  **non-parametric** change point detection on the ensemble anomaly score. Literature focus: threshold
  calibration and baseline drifts. Evaluation: event level on CHB-MIT.
  ⇒ no seizure labels anywhere in the system; the GAE stays the centre (author decision 2026-10-06);
  CPD must keep a real role in temporal localization.
- **Selection only on the 15 non-test subjects** (12 training + 3 validation). The 8 test subjects are
  scored only after a freeze, and every look is logged in §3.
- **One pre-registered configuration and gate per experiment**, written in the script docstring before
  the run. A failed gate is recorded as failed; the construction is fixed, never the threshold.
- **Not pursued:** TUH artifact corpus (no time; Future Work); any supervised component (contrary to the
  title); a feature-only system without the GAE (author decision).

## 1 · Evaluation protocols — which number means what

| protocol | how the timeline is built | where its numbers live |
|---|---|---|
| **Offline (thesis of record)** | `szcore_eval.build_timeline_masked` rebuilds a timeline **from the seizure annotations** and fills gaps with **bootstrap-resampled interictal scores drawn from artifact-rejected (±5 SD) windows** | `RESULTS_OF_RECORD_phaseB.md` (F1 0.213, 27.4 FP/day, ...) |
| **Continuous** | every 4 s window of every file, in time order, no rejection, label-free | this file, `results/continuous_eval/`, `results/e8_*`–`e10_*` |
| **Application** | the web application's own detections, continuous, whole-recording statistics | `web_demo/` run records; summary in §3 |

The offline protocol removes, by construction, the high-amplitude non-seizure windows that cause most
false alarms on the real timeline (§2, diag and raw view). Its numbers are correct for that protocol but
are **not** an estimate of performance on a continuous recording. How the report presents the two is an
open decision for the supervisor (§7).

**Official SzCORE scorer, read from source 2026-10-06** (`esl-epfl/szcore-evaluation`,
`evaluate.py`; `esl-epfl/timescoring`, `scoring.py`):
- each recording is scored separately; TP/FP/ref counts are **summed within a subject**; with the
  default `avg_per_subject=True` the dataset value is the **mean of per-subject metrics** (`nanmean`);
- precision = tp / (tp + fp); F1 = 2tp / (2tp + fp + (ref − tp)); FP rate per day of recorded time;
- event defaults: 30 s start tolerance, 60 s end tolerance, events closer than 90 s merged, events
  longer than 300 s split.
The P1 scripts report **pooled** counts (sum over subjects). From P2 on, every result reports both the
pooled value and the official subject-mean value.

## 2 · Stage P1 — experiment log (all on the 15 non-test subjects unless marked TEST)

| step | result | what it established |
|---|---|---|
| `diag_detector_ceiling` (val) | PELT alarms on rising **and** falling change points; removing flagged non-ictal windows (oracle) cuts FP ~85–90 % with seizures kept (633 → 68 FP, 11/15 kept) | high-amplitude non-seizure windows drive the false alarms |
| `raw_eeg_view` | the ±5 SD rule flags **46 %** of training interictal windows (one sample on one channel suffices) and ~90 % of seizure windows; separators of seizure vs flagged: spatial spread of amplitude rise (AUROC 0.76 pooled, 0.85–0.92 val), relative theta, kurtosis | the flag means "high amplitude", not "artifact" |
| E1 feature GMM, cross-patient, clean vs all-non-ictal "normal" | FAIL (sens@≤25 FA/day 0.340 vs 0.372); 8 vs 32 components equal | redefining "normal" **across patients** does nothing; more capacity does nothing |
| E3 supervised HGB, LOSO | 0.702 at 20.5 FA/day | reference for what labels buy; never part of the system |
| E4 artifact model trained on ±5 SD flags | FAIL: 81.5 % of seizure windows called artifact | design error predictable from the 90 % figure above |
| E5 per-patient feature density (transductive, label-free) | event 0.340 → **0.596**; val 15/15 (window gate K2 missed by 0.001) | a density fitted on the patient's **own** recording separates seizures from that patient's artifacts, when the input carries amplitude |
| E6 per-patient density on V1 GAE outputs | FAIL; V1 + threshold detector D1 = 0.479 (subset) | V1's representation lacks the information |
| code reading | V1 node features erase amplitude **and** window spectral shape (band powers z-scored within each window, then min-max per band across channels within each window) | root cause of E5 vs E6 |
| E7 | 4-branch ensemble + F < F alone; PELT as segmenter (D2) 0.213 < D1 0.479 (D2 grid reached 100 FA/day, so the comparison is fair) | — |
| C1/C1b | 7 added node features: log band power ×5, log line length, signed-log kurtosis; training-set z, clip ±4 → [0, 1]; `data/trainset_v2/` 15 subjects, all files (chb12_27/28/29 skipped: missing a common channel, as in the thesis pipeline) | information present (single-feature val AUROC 0.87–0.999) |
| GAE v2 (Kaggle) | node input 30, decoder output 12, **3,964 parameters** (computed from layer sizes); variants clean / all; seeds 42, 1 (+ clean 2, 3) | losses converge, no overfit; `all` loss higher as expected |
| **E8**, full recordings | V1 0.330 @ 23.7 → **v2 clean V2_LW 0.489 @ 19.8** (2 seeds, SD 0.030); val 7/15 → 11/15; gains in 8 subjects, none lost; rule V chose clean over all (0.495, lower on val) | **rule C passed (+0.159); v2 ADOPTED** |
| E8 diag | v2 raises seizure scores (median 1.40 → 2.31, p90 3.77 → 5.16); flagged non-ictal unchanged (1.02 / 3.01 → 1.02 / 3.09); v2 recon-branch sanity AUROC 0.26 (chb10), ~0.52 (chb22) | v2 lifts seizures, does **not** lower the patient's own high-amplitude states |
| **E9, TEST, one shot** (frozen: v2 clean, V2_LW, D1 smooth 15 windows, top 2 %, merge 90 s) | seed 42 **3/76, 24.1 FA/day**; 4 seeds 0.043 ± 0.007 @ 24.8 ± 0.7; V1 2/76 @ 24.2; window macro AUROC V1 0.640 → v2 0.680 (6/8 patients up); short seizures 0/18; top 5 %: v2 27/76 @ 60.6, V1 24/76 @ 62.1 | the window-level gain transferred, the event-level gain did **not** |
| E10 kernel-CPD bump detector K (ruptures KernelCPD rbf, segment above both neighbours, ≤ 300 s, patient top-p prominence) | **FAIL**: best ≤25 FA/day 0.250 @ 5.8 vs D1 0.489 @ 19.8; val 0.300 vs 0.733; 3/15 subjects ≥ D1. D1c (D1 minus events > 300 s) 0.436 @ 15.5, on the D1 curve | — |

E9 sanity: V1 at top 5 % (24/76 @ 62) agrees with the independent earlier continuous evaluation
(23/76 @ 73); non-ictal hours 277.6 vs offline 278.2.

**E9 precision/F1 columns are INVALID** (a hand-written formula, not SzCORE's). Recomputed with the
timescoring formula from the E9 per-patient counts (seed 42 / V1): pooled precision 0.0106 / 0.0071,
pooled F1 0.0168 / 0.0112; official subject-mean sensitivity 0.0387 / 0.0335, precision 0.0114 /
0.0078, F1 0.0175 / 0.0125, FP/day 26.9 / 26.4 (FP/day mean computed from the one-decimal per-patient
column). The E9 script must be patched to write these from the scorer before any of them is reported.

**E10 reading notes (not a reinterpretation of the gate).** K's grid at penalty 4 stops at 5.8 FA/day
(p ≤ 0.2 of candidates), so the ≤ 25 comparison is partly a grid ceiling; in the low-FA region K
(0.250 @ 5.8) sits between D1's 0.165 @ 3.5 and 0.277 @ 7.6, i.e. on D1's curve, not above it.
D1c ≈ D1 along the curve: long plateaus are not the main false-alarm source on the non-test set.
A local-contrast detector does not rescue missed seizures here.

## 3 · Log of every look at the TEST set (to be disclosed in the report)

| # | when / what | result |
|---|---|---|
| 1 | Phase B tier 2, pre-registered one-shot, offline protocol | `RESULTS_OF_RECORD_phaseB.md` |
| 2 | continuous evaluation of V1 + PELT (`results/continuous_eval/`) | cell 50/2.0/90: 23/76 @ 73.3; cell A8: 0.079 @ 19.2 |
| 3 | application tier, built app on the 8 subjects | 0.211 @ 52.4 |
| 4 | veto screen, one-shot (commit 90a4dae, `results/veto_screen*`), plus the oracle bound Part B (`results/oracle_gate_bound/`) | 6/76, FA 19.2 → 17.9: did not transfer. Part B: test seizure peaks exceeded by 20–50 % of same-length non-ictal spans (4 % on val); 0.1–1 % once flagged windows are removed |
| 5 | E9, frozen v2 (tag `e9-test-oneshot`; seeds 2, 3 added later, config unchanged) | §2 |

Looks 2–4 informed the P1 diagnosis. Any P2 test look is #6 and is disclosed as such.

## 4 · Diagnosis at the close of P1 (corrects HANDOVER §3)

1. **The bottleneck on test is the tail of the score, not its average.** A threshold that allows ~2 %
   of a patient's time needs seizure windows above that patient's 98th percentile; window AUROC
   0.65–0.87 (chb03 0.87 → 1/7, chb18 0.84 → 0/6) is far from that.
2. **What owns that tail is the patient's own high-amplitude non-seizure activity.** Part B on test:
   removing flagged windows drops the fraction of non-ictal spans that out-rank a seizure peak from
   20–50 % to 0.1–1 %. The handover attributed the collapse mainly to the detection stage; E10 (local
   contrast) and D1c (no long events) do not support that. The detection stage matters for short
   seizures (point 4), not for the main collapse.
3. **v2 fixed the input, not the reference.** It lifts seizures but leaves flagged windows where they
   were (E8 diag), because "normal" is still defined by other patients' clean EEG. E1 (cross-patient
   normal) failed; E5 (patient-own normal) worked. The GAE has never been given the patient-own normal.
4. **Short seizures are erased by 60 s smoothing** (0/18 on test, chb16 all ten short); the selection set
   holds only 3 short seizures, so this cannot be tuned without test data.
5. **The selection set over-predicts test.** 12 of its 15 subjects trained the GAE, and its seizures are
   easier (Part B 4 % vs 20–50 %). Gates on it protect honesty, not transfer.
6. **chb06 is inverted** under every model (window AUROC 0.25–0.38).

## 5 · Comparators under the identical protocol (verified 2026-10-06)

Source: `github.com/esl-epfl/szcore`, `results/<algorithm>/chbmit.json` (repo HEAD 2026-09-06),
algorithm metadata in `algorithms/*.yaml`. Official scorer, BIDS CHB-MIT (all subjects), event level,
**mean over subjects**. Not the same 8 patients as ours.

| algorithm | label use / training | sens | prec | F1 | FP/day |
|---|---|---|---|---|---|
| **DynaSD** (Ojemann, UPenn, 2025) | unsupervised per recording: a deep autoregressive model is **trained on the beginning of each continuous clip** to learn its baseline; prediction error, threshold optimized on annotated iEEG, hyper-parameters tuned on a CHB-MIT subset, 15 s smoothing, ≥ 9 of 18 channels required | 0.608 | 0.199 | 0.218 | 23.2 |
| Gotman 1982 | rule-based, no CHB-MIT training | 0.913 | 0.027 | 0.051 | 237.5 |
| CA-EEGWaveNet | supervised, trained on CHB-MIT + Siena | 0.368 | 0.356 | 0.265 | 5.0 |
| MV-AFA v1.3.0 | supervised, trained on CHB-MIT + Siena + TUSZ | 0.749 | 0.463 | 0.520 | 12.8 |
| He random forest, EEGWaveNet 2021 | supervised, trained on CHB-MIT itself | not comparable | | | |

Several submissions show 0 sensitivity on CHB-MIT (failed runs); they are not comparators. Perplexity's
"ESL_RF 34.1 % / 1.08 FP/day" row is not in the repository and is not cited. DynaSD is the only
unsupervised method among them, and its key design — **a baseline model fitted on the patient's own
recording** — is the mechanism P2 tests on the GAE.

## 6 · Stage P2 — plan (to be finalized in the P2 chat after reading the code)

**Hypothesis.** The GAE fails on test because its "normal" belongs to other patients. Adapting the GAE,
label-free, to each patient's own complete recording (test-time / transductive adaptation) makes that
patient's frequent high-amplitude states normal (they are ~40 % of the time) while seizures stay rare
(~0.2–0.7 %). Evidence for: E5 (+0.256 with patient-own density on features), E1 (cross-patient normal
fails), §4 point 2 (the test tail is owned by the patient's own flagged windows), DynaSD (§5).
Evidence against / risks: contamination (a patient with many similar seizures, chb15 has 20, may teach
the model its seizures); the gamma branch is a fixed feature that adaptation does not touch; the
selection set is easier than test.

**E11 — tail anatomy by branch (cache only, minutes, no test).** On the E8 cache of the 15 non-test
subjects, V1 and v2: for recon, latent, gamma and the ensemble — seizure vs flagged and seizure vs clean
AUROC per subject, the Part-B exceedance fraction per seizure, and which branch owns the top-2 %
non-ictal windows. Decides which readouts the adaptation must cover. Needs the cache format first.

**E12 — patient-specific adaptation of the GAE (the P2 lever).** Per patient: start from frozen v2 clean;
fine-tune on every window of that patient's recording with no labels and no flags, under a fixed budget;
re-derive the readouts (latent covariance refit on the adapted encoder; gamma as E11 dictates); D1
frozen; SzCORE. Seeds 42 and 1. Design items fixed in the docstring before the run: which parameters
adapt, epochs and learning rate (fixed a priori, not tuned), contamination guard (none vs trimmed loss),
the gate (proposal: ≥ v2 + 0.10 sensitivity at ≤ 25 FA/day pooled, validation not lower, ≥ 9/15 subjects
not worse, plus a required mechanism check: flagged non-ictal score median and seizure exceedance both
fall), and the measured CPU cost per patient, because the application must be able to run it.

**E13 — CPD as the localization step (cheap, after the detector is frozen).** Keep detection by the
patient-calibrated threshold; place onset and offset of each detected event with non-parametric kernel
CPD inside a fixed margin. Metric: onset/offset error on true positives vs the raw D1 boundaries, with
sensitivity and FA/day required unchanged. This gives Objective 2 a measured role instead of a nominal
one.

**Candidate readout, only if E11 shows the flagged tail is focal:** a spatial-recruitment score — how many
channels have a per-node v2 reconstruction error above the patient's own baseline — mirroring DynaSD's
"≥ 9 of 18 channels" rule and the raw-view spread separator (AUROC 0.85–0.92 on validation). It keeps the
GAE as the source of the score; it needs a per-node re-dump of the non-test subjects.

**Optional, only if time:** cross-fitted base GAEs so that every non-test subject is unseen (3 folds,
one night on 3 Kaggle accounts); running the public DynaSD container on our 8 test patients for a
same-patient comparator.

**Time box.** Supervisor meeting Thu 08/10 08:00 (P1 + this plan); IELTS 09/10 (`PROJECT_STATUS.md` §0);
P2 decision and at most one test look by **11/10**; 12–15/10 application and report. Whatever P2
returns, the report is written from the record as it stands on 11/10.

## 7 · Decisions open for the supervisor (08/10)

1. How the report presents the offline protocol vs the continuous timeline (and the application tier).
2. Disclosure of the test looks in §3.
3. Whether label-free patient-specific adaptation (transductive, whole recording) is acceptable under
   "unsupervised" and Objective 1. It uses no labels; it changes "patient-independent" to "adapted to
   each new patient without labels".
4. Role of CPD: PELT on the locked system; threshold detector D1 in P1; E13 proposes CPD as the
   onset/offset localizer.
5. Precision of the P1 numbers: pooled vs official subject-mean aggregation for the final tables.

## 8 · Files of the performance phase

src: `diag_detector_ceiling`, `e1_normal_definition`, `e3_supervised_loso`, `e4_artifact_rejection`,
`e5_patient_density`, `e6_dump_gae`, `e6_gae_patient_density`, `e7_ensemble_cpd`, `c1_nodefeat`,
`c1b_build_trainset`, `c1t_build_testset`, `retrain/train_gae_v2`, `e8_gae_v2_eval`, `e8_diagnostics`,
`e9_test_oneshot`, `e10_kernel_cpd`. data: `trainset_v2/` (15 npz), `testset_v2/` (8 npz), `models_v2/`
(clean 42, 1, 2, 3; all 42, 1; identity in `docs/PROVENANCE_V2.md`). results: `diag_detector_ceiling`,
`e1_*` … `e7_*`, `e8_gae_v2` (+ `diag/`), `e9_test_oneshot` (tag `e9-test-oneshot`), `e10_kernel_cpd`.
Kaggle: `Agent/gae_v2_train.ipynb`, dataset `nhn2mm/gae-v2`, GPU T4×2, ~3.3–3.8 h per seed (clean).
