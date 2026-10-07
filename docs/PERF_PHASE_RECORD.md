# PERF_PHASE_RECORD — performance phase (re-opened 2026-10-05)

**Rev. H, 2026-10-07** (rev. B–G same day, rev. A 2026-10-06). Single source for the performance phase. Supersedes
`HANDOVER_PERF_2026-10-06.md` (archived) and the chat audits `audit_1`–`audit_7`.
Stage **P1** (E1–E10) is CLOSED. Stage **P2** (E11 onward) is running; its log and queue are in §6.
Rev. B: §6 rewritten with E11–E14; wording on flagged windows corrected (§6.0). Rev. C: E15, author decisions on the ensemble and CPD. Rev. D: binding rules (§6.2), designs E16–E20 (§6.3). Rev. E: designs approved with four
clarifications (order E19 before E18, short events in E18, branch ledger §6.4, single-readout framing, runtimes).
Rev. F: E16 arms a–d (4 seeds) and the drift mechanism. Rev. G: E16 e, f; E17 (Eb chosen); E16g proposed; E19 ready. Rev. H: E16g arms dt, h; E19 stop
(threshold rule fixed to match event_grid); E18 ready; grid-resolution observation (§6.4).

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

## 6 · Stage P2 — log and queue

### 6.0 Wording
A ±5 SD flag means **high amplitude**, not artifact (46 % of training interictal windows are flagged,
~90 % of seizure windows). "Flagged window" below never means "noise". Mechanisms such as "muscle gives
high gamma" or "eye artifacts sit on frontal-polar channels" are unmeasured hypotheses.

### 6.1 Log (15 non-test subjects, cache-based unless stated; every gate fixed in the docstring first)

| step | result | reading |
|---|---|---|
| **E11** tail anatomy by readout (`results/e11_tail_anatomy/`) | top-2 % tail of the frozen ensemble: 95–96 % flagged (base rate of flagged windows ≈ 46 % in training interictal). Owner of the tail (largest mean z): **gamma** in 12/15 (both seeds). Seizure-vs-flagged AUROC: gamma 0.762, recon 0.527–0.534, **latent 0.966**. Mean z in tail vs in seizures: gamma 6.2–6.3 vs 3.29; recon 1.90 vs 0.68–0.71; latent 1.50–1.59 vs 3.15–3.50 | rule R3: gamma dominates the tail because its z is heavy-tailed (it still ranks seizures above flagged windows on average); recon is near chance against flagged windows; the v2 latent is the readout that separates. Adapting the GAE alone would not touch gamma |
| **E12** latent-only readout L vs frozen ensemble E (`results/e12_readout_composition/`) | reproduction of E8 exact. L 0.553 @ 23.8 vs E 0.489 @ 19.8 (≤ 15: 0.511 vs 0.378; ≤ 10: 0.426 vs 0.277); validation 0.867 vs 0.733; 9/15 subjects; subject-mean 0.676 vs 0.651. Tail flagged share 0.96 → 0.87 | **NOT adopted** (G1 +0.064 < +0.10). Without chb12 (26 of 94 seizures) L ≈ E at ≤ 25 (45.5/68 vs 45/68, computed from the per-subject table) |
| **E13** recon trained on flagged windows (`all`) vs not (`clean`), 12 training subjects (`results/e13_recon_seen_artifacts/`) | recon seizure-vs-flagged ΔAUROC median −0.007, positive 4/12; latent 0.946 → 0.936 | rule B. **Scope:** a pooled 12-patient model, recon readout only — a diluted proxy, NOT patient-specific fine-tuning. Reading: "no support from this proxy", not "adaptation fails". Adaptation is **postponed, not tested** (author decision 2026-10-07) |
| **E14** spatial-recruitment readout S9 = 9th largest of 18 per-channel latent anomalies (per-channel LedoitWolf on the v2 node latent, per patient) (`results/e14_spatial_recruitment/`) | reproduction exact. **S9 0.622 @ 24.6** (≤ 15: 0.521; ≤ 10: 0.426); validation 0.867; 12/15 subjects ≥ E; subject-mean 0.747 @ 25.4 FP/day (E 0.651 @ 20.8); short seizures 1/3. Characterisation: S12 0.617, channel mean 0.601, S6 0.543, S3 0.537, max 0.457. **Tail flagged share 0.95** (L 0.87) | G1–G3 pass; the pre-registered **mechanism check FAILED** (tail not cleaner). The script printed "ADOPTED" because the mechanism condition was not wired into its decision (coding error, corrected in the reading here). Reading: an empirical gain at ≤ 25 FA/day, not explained by the spread hypothesis; the per-channel modelling (mean 0.601 ≈ S9) seems to carry it. vs L: +0.069 at ≤ 25, +0.010 at ≤ 15, 0 at ≤ 10. Without chb12: S9 50.5/68, L 45.5/68, E 45/68 (computed). **Status: best candidate, not frozen, no test look** |
| **E15** patient-specific fine-tuning of v2 (all windows of the patient, no labels; Adam 1e-4, batch 32, 2,000 steps) + S9 (`results/e15_patient_adaptation/`) | reproduction gates exact (E8 mean latent, E14 distances). S9-adapted 0.628 @ 24.5 vs S9 base 0.622 @ 24.6; per seed 0.617/0.638 vs 0.617/0.628; subject-mean 0.758 vs 0.747; without chb12 0.757 vs 0.743; validation 0.867 = 0.867; 13/15 subjects; seizure z 4.90 → 5.32, flagged z −0.00 → 0.11, tail flagged 0.95 → 0.96. Analysis only: 0/15 patients and 10/425 files have a seizure in their first 10 min | **Not selected in this configuration** (one configuration: lr 1e-4, 2,000 steps, all parameters, whole recording; G1 +0.006 < +0.05). Mechanism not seen: seizure z rose slightly, flagged z did not fall. This is not "fine-tuning does not work". Open hypothesis: the per-patient LedoitWolf fit of S9 already gives each patient its own normal at the readout level. Freeze rule → candidate = **S9 base**. Re-opening fine-tuning needs a different design with a mechanism argument (e.g. decoder-only, per-file) and is not a reason to hold E16–E18 |
| **E16** per-recording baseline, 4 seeds (`results/e16_recording_baseline/`); reference S9 base 4-seed 0.612 @ 24.6 (seeds 0.617/0.628/0.564/0.606), ≤ 15 0.513, ≤ 10 0.423, val 0.867, subject-mean 0.742 @ 25.7 | a (first 10 min of each file) 0.191; c (30 min) 0.295; d (causal sliding 30 min) 0.487; **b (patient covariance + per-file median/MAD) 0.582 @ 22.5, ≤ 15 0.548, ≤ 10 0.444, val 0.800, subject-mean 0.735 @ 22.7, seizure z 4.72 → 4.08**. Drift under S9 base: per-file median IQR / patient MAD 0.85; **84.5 % of the top-2 % non-ictal windows lie in the patient's top-quartile files** | none adopted (all fail G1). Mechanism: short baselines fit one state (fit-noise ratio 0.62, self-scoring −0.92 z), so everything else looks anomalous — longer baselines are monotonically better. File-level drift is real and owns the false-alarm tail; b (location + scale) helps at strict FA but lowers seizure z. Next (proposed): location-only corrections e, f |
| **E16 e, f** location-only drift correction of S9 (same gate) | **e (minus ±15 min running median inside each file): 0.628 @ 22.3; ≤ 15 0.614; ≤ 10 0.487; val 0.867; without chb12 0.783; subject-mean 0.766 @ 22.2; every seed above its S9 (0.649/0.638/0.596/0.638 vs 0.617/0.628/0.564/0.606); 11/15 subjects; seizure z 4.62**. f (minus file median) 0.559. Drift diagnostics under S9 base: top-quartile files contain a seizure in 8.3 %; flagged share 0.459 in top files = 0.459 elsewhere | e: G1 FAIL only (+0.016 at ≤ 25); G2–G5 and M pass. The correction shifts the whole curve left (+0.10 at ≤ 15). The drift is a file-level shift of the latent readout, not more high-amplitude activity and not seizure files. Candidate C stays S9 base (rule) |
| **E17** rank ensemble, C = S9 base | Ea (C+recon+gamma) 0.535, inferior; **Eb (C+L+gamma) 0.617 @ 22.8, ≤ 15 0.545, ≤ 10 0.441, val 0.800, without chb12 0.824, subject-mean 0.791 @ 24.3**, non-inferior; Ec (C+L) 0.572, inferior. Percentile AUROC seizure-vs-flagged: C 0.908, L 0.858, gamma 0.651, recon 0.445 | **Eb chosen** (only non-inferior combination). Final scalar = rank ensemble of three readouts: per-channel latent order statistic, graph-level latent, gamma-AEC |
| **E16g** drift correction with the ensemble (reference Eb) | dt (detrend the final scalar): 0.529, seizure z 2.89 → 2.48, NOT adopted. h (detrend only the S9 component inside the ensemble): 0.598 @ 15.2 (cell 15/0.01), ≤ 15 0.471, ≤ 10 0.471, val 0.867, without chb12 0.801, subject-mean 0.775 @ 14.8, 11/15 subjects, seizure z 2.85 | neither adopted; candidate = **Eb**. dt hurts (the running median of the bounded percentile mix absorbs seizure elevation). h moves the operating point to much lower FA (subject-mean FP/day 24.3 → 14.8 at similar sensitivity) but its next grid step exceeds 25 FA/day |

Caution (rule 19 and multiple looks): the 15 non-test subjects have now been used for E1–E17 and E16g; seizure
peaks are out-ranked by ~4–5 % of non-ictal spans there vs 20–50 % on test. A pass on this set is not a
test expectation.

### 6.2 Binding rules for the rest of P2 (author, 2026-10-07)

1. **No early verdict of failure.** When a result misses its gate or a problem is identified: measure the
   mechanism, state a fix hypothesis, pre-register its gate, run it. "Failed" is written only after the
   evidence-backed fixes have been tried. Gates stay fixed; the construction is redesigned once the
   mechanism is known. Every design carries an "if not met" section (diagnostic + next fix).
2. **Four seeds** (v2 clean 42, 1, 2, 3) for E16 onward; seeds 2 and 3 are dumped on the 15 non-test
   subjects by `src/p2_dump_seeds23.py`. G1 becomes: 4-seed mean ≥ reference + 0.05 **and** ≥ 3/4 seeds
   not lower than the reference of the same seed. The test look reports all four seeds.
3. **Detector cell.** For every score the D1 cell is re-selected by the same rule: highest 4-seed-mean
   pooled sensitivity at ≤ 25 FA/day on the 15 non-test subjects. All other figures are read at that cell.
4. **Reporting.** Pooled and official subject-mean; validation-only and without-chb12 beside every number.
5. **Freeze only when no evidence-backed improvement of event-level performance remains**; then one
   test look (#6): 4 seeds, pooled and subject-mean, onset/offset error with n, short seizures caught.
6. **Expectation for the test look, written now:** at best a moderate improvement over E9. The main P1
   bottleneck is not solved (top-2 % tail still 95 % flagged under S9) and the non-test set is easier
   (rule 19). This is not a reason to stop.
7. Report, demo, attribution and the LiNDDA comparator wait until the system is frozen.

### 6.3 Pre-registered designs (approved 2026-10-07; reference = candidate C)

**Order:** E16 → E17 → **E19 → E18** → (E20). E19 runs before E18 so that the localizer is designed on
the final event set, short events included.

**E16 — per-recording baseline at the readout level.** Per file, per channel, LedoitWolf of the node
latent fitted on the first min(150, n_file/2) non-signal-loss windows of that file (10 min; files with
< 40 such windows use the patient-level fit); distances for every window of the file; per-channel
robust-z over the patient (as S9); 9th largest of 18; robust-z. Only the covariance anchor changes vs S9.
Gate vs S9 base: G1 (4-seed rule), G2 subject-mean ≥, G3 without chb12 ≥, G4 validation ≥, G5 ≥ 9/15
subjects, M seizure z not more than 10 % lower. Always reported (mechanism): (a) drift under S9 base —
spread of per-file medians of non-ictal scores relative to the patient MAD, and the share of top-2 %
non-ictal windows that sit in the patient's top-quartile files; (b) fit noise — distance variance inside
vs outside the baseline; (c) self-scoring bias — median z of baseline windows vs the rest.
*If not met:* run, each with the same gate, (E16b) patient-level covariance + per-file median/MAD
normalisation of the per-channel distances (drift in location/scale only), (E16c) baseline 30 min (450
windows), (E16d) causal sliding baseline (refit every 15 min on the previous 30 min of the same file;
the first 30 min use the patient-level fit). The best arm that passes becomes C; if none passes,
C = S9 base and the diagnostics are recorded.

**E17 — rank ensemble to one scalar.** Per patient, each readout → its percentile; equal mean.
Combinations scored (all three, pre-listed, not a sweep): (a) C + recon + gamma, (b) C + L + gamma,
(c) C + L. Non-inferiority vs C: pooled ≥ C − 0.02, subject-mean ≥ C − 0.02, validation ≥ C − 0.067.
Choice: highest pooled sensitivity at ≤ 25 FA/day among the combinations that pass; ties within 0.02
go to a combination containing gamma (independent, physiologically grounded readout). Always reported:
percentile AUROC seizure-vs-flagged and tail ownership per component.
*If none passes:* (E17b) rank ensemble of the latent family {S6, S9, S12, channel mean, L} (several
spatial scales of the same GAE latent), same non-inferiority gate; if that fails, the author decides.

**E18 — kernel CPD on the scalar as the onset/offset localizer.** For every D1 event, the unsmoothed
scalar on the event ± 15 windows (60 s) inside the file; ruptures KernelCPD (rbf), exactly 2 change
points (onset, offset), min segment 2 windows; no penalty to tune. **E18 cannot raise sensitivity or
lower FA/day** (it only moves boundaries; SzCORE tolerates 30 s / 60 s); its detection gate (pooled
sensitivity ≥ D1 − 0.02, FA/day ≤ D1 + 1) only guards against damage. Its value is the new metric —
onset and offset error (s) on true positives, reported with n — and a measured role for CPD
(Objective 2). Short events: the CPD segment is always the event ± 15 windows, so it holds at least 31 windows even
for a 1-window event; when the two change points enclose < 2 windows or the inner segment is not above
both outer segments (no bump), the detector's own boundaries are kept (fallback). The fallback rate is
reported overall and for short-branch events separately; onset/offset errors are reported separately
for events ≤ 30 s and longer ones. Adopted if the median onset and offset errors are each not worse
than the raw detector boundaries by more than 4 s and at least one improves. *If not met:* error by seizure duration and
bias sign; then (E18b) CPD on the D1-smoothed score, (E18c) margin ± 30 windows.
Note: the final structure is D1 detection + CPD localisation, not PELT + FP-budget; Chapter 2 Table 5
must be rewritten (Decision #4, §7). chb06 stays inverted under every model (limitation).

**E16g — drift correction of the final scalar (proposed after E16/E17, approval pending).** Eb minus
its ±15 min running median inside each file; reference Eb; the E16 gate; Eb reproduction check.

**E19 — short-seizure branch.** 23/76 test seizures last < 20 s (E9: 0/18 detected); the non-test set
has 3, so the benefit cannot be gated there. Second detector on the same scalar: smoothing 3 windows,
patient top-p_s, only events ≤ 30 s kept, union with the main D1 events (merge 90 s). p_s = the largest
of {0.001, 0.002, 0.005} whose added FA/day (4-seed mean, non-test) is ≤ 3. Adopted if pooled
sensitivity is not lower and the FA increase is ≤ 3/day; short seizures caught are reported
descriptively (non-test and test). *If no p_s fits the budget:* describe the short false events
(flagged share, duration); fix to test: the short branch scored with a broader spatial requirement
(S12), same budget rule.

**E20 — extension: multivariate kernel CPD on the trajectory of the percentile readouts.** Non-test
only, own pre-registered gate, no separate test look. Designed after E18.

### 6.4 Branch ledger, single-readout framing, runtimes

**Ledger.** Every arm, adopted or not, is one row of `results/p2_ledger.csv` (written by the scripts from
E16 on). Gates are identical for every arm of a step. The number of arms tried is reported with the
chosen result as a measure of its optimism. Arms evaluated on the 15 non-test subjects before E16
(selection arms with a gate; characterisation readouts counted separately):

| step | gated arms | verdict | characterisation only |
|---|---|---|---|
| E11 | 0 (descriptive) | rule R3 | — |
| E12 | 1 (L) | not adopted | RL, LG, L2 |
| E13 | 0 (proxy rule) | rule B | — |
| E14 | 1 (S9) | gates passed, mechanism check failed → not adopted as written | S1, S3, S6, S12, mean |
| E15 | 1 (S9 adapted, 2,000 steps) | not selected | 500 and 1,000 steps |
| E16 | 6 (a–f) | none adopted (e: G1 only) | — |
| E17 | 3 (Ea, Eb, Ec; non-inferiority) | Eb chosen | — |
| E16g | 2 (dt, h) | none adopted | — |

Together with P1 (E1–E10) the non-test set has carried about 15 gated decisions before E16 and about
24 after E17. From E16 on, `results/p2_ledger.csv` is the complete list.

**If E17 leaves C alone** (every cross-readout ensemble inferior, E17b included): the final score is
C, described as an ensemble over channels — the 9th order statistic of 18 per-channel anomaly scores of
the GAE latent. The report states plainly that ensembles across readouts (recon, gamma, graph-level
latent) were tested and were inferior, with their numbers.

**Grid-resolution observation (2026-10-07).** The top-p grid {0.001, 0.002, 0.005, 0.01, 0.02, 0.05}
moves FA/day in factor-2 steps, so an arm that lowers FA cannot spend the 25 FA/day budget when its
next step jumps past it (E16g-h: best cell 15.2 FA/day, next step > 25; E16e: 22.3). Verdicts already
given stand. Any use of a finer grid needs a pre-registered decision by the author (proposed: E21).

**E19 stop (2026-10-07).** The D1 rebuilt in `p2_scalars.py` took the threshold over non-signal-loss
positions; `event_grid` takes it over every non-NaN smoothed value (signal-loss positions inherit their
neighbours' mean). Effect: fp 121 vs 122 on chb04 seed 2; the reproduction check stopped the run before
any result. Fixed; nothing was reported from the stopped run.

**Runtimes for 4 seeds** (estimated, not measured; based on the measured E12, E14 and E15 evaluation
times of ~8–16 s per score through the D1 grid, plus the LedoitWolf fits):

| step | content | estimate |
|---|---|---|
| seed 2/3 dump | done | — |
| E16 arm a | 4 seeds × (S9 base + arm a), ~1,700 per-file × 18-channel fits | 10–30 min |
| E16 arms b, c, d | only if a fails; 4 seeds × 3 arms; d refits every 15 min | 30–90 min |
| E17 | 3 combinations (+ E17b if needed) × 4 seeds | 10–30 min (+10–20) |
| E19 | short branch, 3 p_s values × 4 seeds | 10–25 min |
| E18 | CPD on the events only, 4 seeds | 5–15 min |

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
`e9_test_oneshot`, `e10_kernel_cpd`, P2: `e11_tail_anatomy`, `e12_readout_composition`,
`e13_recon_seen_artifacts`, `e14_spatial_recruitment`, `e15_patient_adaptation`
(node latents `{tag}_s0_Z`, `_s2000_Z`), `p2_seeds` (seeds 2, 3: recon, latents, distances) (per-node dump in `results/e14_spatial_recruitment/pernode/`, not committed). data: `trainset_v2/` (15 npz), `testset_v2/` (8 npz), `models_v2/`
(clean 42, 1, 2, 3; all 42, 1; identity in `docs/PROVENANCE_V2.md`). results: `diag_detector_ceiling`,
`e1_*` … `e7_*`, `e8_gae_v2` (+ `diag/`), `e9_test_oneshot` (tag `e9-test-oneshot`), `e10_kernel_cpd`.
Kaggle: `Agent/gae_v2_train.ipynb`, dataset `nhn2mm/gae-v2`, GPU T4×2, ~3.3–3.8 h per seed (clean).
