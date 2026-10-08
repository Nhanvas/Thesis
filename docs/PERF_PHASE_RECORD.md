# PERF_PHASE_RECORD — performance phase (re-opened 2026-10-05)

**Rev. R, 2026-10-08** (rev. P–Q 2026-10-07) (rev. B–O same day, rev. A 2026-10-06). **Performance phase CLOSED (P1–P3, X1); report phase since 2026-10-08 (rev. R, section 10).** Single source for the performance phase. Supersedes
`HANDOVER_PERF_2026-10-06.md` (archived) and the chat audits `audit_1`–`audit_7`.
Stages **P1** (E1–E10), **P2** (E11–E22) and **P3** (section 9) are CLOSED; external validation X1 in 9.9; report-phase decisions and the final-system attribution (A5) in section 10.
Rev. B: §6 rewritten with E11–E14; wording on flagged windows corrected (§6.0). Rev. C: E15, author decisions on the ensemble and CPD. Rev. D: binding rules (§6.2), designs E16–E20 (§6.3). Rev. E: designs approved with four
clarifications (order E19 before E18, short events in E18, branch ledger §6.4, single-readout framing, runtimes).
Rev. F: E16 arms a–d (4 seeds) and the drift mechanism. Rev. G: E16 e, f; E17 (Eb chosen); E16g proposed; E19 ready. Rev. H: E16g arms dt, h; E19 stop
(threshold rule fixed to match event_grid); E18 ready; grid-resolution observation (§6.4). Rev. I: E19 on Eb;
E21 design (finer grid, gates unchanged); E18 no-CPD control; freeze plan and test-look pre-registration (§6.5).
Rev. J: validation definitions; E19 reading; E19b rule (author, 2026-10-07). Rev. K: E21, E19b,
E21b design, freeze sequence and bootstrap script. Rev. L: E21b, E18, bootstrap results; open items before the freeze. Rev. M: the three open items
approved by the author and scripted (E17b, E18d, matched-budget bootstrap after CPD); literature lead on
onset/offset latency (unverified). Rev. N: E17b adopted (final scalar), E18/E18d on it,
matched-budget bootstrap; freeze candidate written down (§6.6), test look not yet run. Rev. O: reviewer
points (E17b choice, CPD wording, decision count, headline seed), E20a and diagnostics, test-look scripts.
Rev. P: E18 diagnostics, E20a, look #6 on test, author decision (not approved; phase 3, target pooled
sensitivity ≥ 0.50); handoff in `docs/HANDOFF_P3.md`. Rev. Q: stage P3 opened -- checks of the burden table and the 4-seed bootstrap, test-information
policy (two tiers), hypotheses H6-H8, P3-A anatomy script, decision table (section 9). Rev. R (2026-10-08): look-#6 subject-mean by seed (0.508 seed 42, 0.498 4 seeds); X1 hours; section 7 resolved; section 10 (report phase, A5).

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

| 6 | P2 frozen system (tag `p2-frozen`), `e22_test_oneshot.py`, 2026-10-07 | seed 42 after the localizer **26/76 (0.342) @ 22.2 FP/day**, precision 0.092, F1 0.145; 4 seeds 0.336 ± 0.008 @ 23.9 ± 1.2; subject-mean 0.508 (seed 42; 4 seeds 0.498 ± 0.010); short 4/18. E on the same look 3/76 @ 24.1 (reproduces E9 exactly) |
| P3-T | 2026-10-07, stage P3, test **information** (not a look at results): (a) `p3_seizure_burden.py` read the test summaries (counts, durations, ictal minutes); (b) `p3_anatomy.py --include-test`: tier T-A (label-free test EEG and model outputs) and tier T-B (per-seizure anatomy joined to test annotations), section 9 | any P3 design motivated by (b) makes look #7 test-informed; it is reported as such |
| 7 | P3 frozen system (tag `p3-frozen`), `e23_test_look7.py`, 2026-10-07 — **TEST-INFORMED** (record 9.2) | balanced point, seed 42 after the localizer **37/76 (0.487) @ 27.5 FP/day**, precision 0.104, F1 0.172, subject-mean 0.577; 4 seeds 0.477 ± 0.022 @ 29.2 ± 1.3, subject-mean 0.567; detector stage 38/76 (0.500) @ 28.4. Look #6 reproduced exactly (R2). No look #8 |
| X1 | 2026-10-07, external validation of the P3 frozen system on data never used by the thesis: chb24 and Siena (14 patients), `x1_external.py` (tags `x1-prereg`, `x1-prereg-v2`), one run, no tuning | chb24 seed 42 14/16 @ 29.5 FP/day; Siena seed 42 33/47 (0.702) @ 44.0, subject-mean 0.748; 4 seeds Siena pooled 0.617, subject-mean 0.633 @ 41.0. Not a look at the CHB-MIT test set |
| A5 | 2026-10-08, channel attribution of the final system (`src/attribution_v8.py`, tags `attribution-a5-prereg`, `attribution-a5-results`): per-channel latent anomaly against the 76 test channel annotations already used by A4; no event metric | section 10.2 |

Looks 2–4 informed the P1 diagnosis; look 5 (E9) the P2 diagnosis. Look 6 was reported as is; the author did
not approve the result and opened stage P3 (target pooled sensitivity ≥ 0.50). Any P3 design that uses
test information (per-subject results of look 6, test seizure durations) must be listed here, and the next
look (#7) is then disclosed as test-informed.

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
| **E17** rank ensemble, C = S9 base | Ea (C+recon+gamma) 0.535, inferior; **Eb (C+L+gamma) 0.617 @ 22.8, ≤ 15 0.545, ≤ 10 0.441, val 0.800, without chb12 0.824, subject-mean 0.791 @ 24.3**, non-inferior; Ec (C+L) 0.572, inferior. Percentile AUROC seizure-vs-flagged: C 0.908, L 0.858, gamma 0.651, recon 0.445 | **Eb chosen** (only non-inferior combination; it passed the validation margin exactly at the floor, 0.800 = 0.867 − 0.067). Final scalar = rank ensemble of three readouts: per-channel latent order statistic, graph-level latent, gamma-AEC |
| **E16g** drift correction with the ensemble (reference Eb) | dt (detrend the final scalar): 0.529, seizure z 2.89 → 2.48, NOT adopted. h (detrend only the S9 component inside the ensemble): 0.598 @ 15.2 (cell 15/0.01), ≤ 15 0.471, ≤ 10 0.471, val 0.867, without chb12 0.801, subject-mean 0.775 @ 14.8, 11/15 subjects, seizure z 2.85 | neither adopted; candidate = **Eb**. dt hurts (the running median of the bounded percentile mix absorbs seizure elevation). h moves the operating point to much lower FA (subject-mean FP/day 24.3 → 14.8 at similar sensitivity) but its next grid step exceeds 25 FA/day |
| **E19** short-seizure branch on Eb (coarse grid; run before E21 by the author) | main D1 cell 15/0.02: 0.617 @ 22.84, val (at that cell) 0.933, short 1/3. Union p_s 0.001: 0.625 @ 23.99; **0.002: 0.628 @ 25.72 (+2.88 FA/day)**; 0.005: 0.649 @ 32.09. Short seizures caught unchanged (1/3) | ADOPTED under the rule as written (p_s 0.002). **+0.011 ≈ one seizure of 94; short seizures caught 1.00/3 at every p_s, even at +9 FA/day — the branch has not yet done what it is for.** Caveats: the union runs at 25.7 FA/day, above the 25 budget used everywhere else (the rule capped only the added FA); the +0.011 comes from non-short seizures on this set. To be re-run on the E21 final scalar (§6.5) |
| **E21** finer top-p grid (gates unchanged; grid changed after seeing E16e and Eb_h), 4 seeds (`results/e21_fine_grid/`) | Stage 1 vs S9 base 0.612: **E16e 0.681 @ 24.25 (cell 5/0.0075), ≤ 15 0.614, ≤ 10 0.561, val 0.900, without chb12 0.846, subject-mean 0.821 @ 24.1, seeds 0.691/0.691/0.660/0.681, 13/15 subjects, short 1.5/3 — all gates pass**; E16b 0.596 not adopted; E15 TTA (4 seeds) 0.617, G1 fail. Stage 2 (C' = E16e): Ea 0.548, Eb 0.636 (val 0.933, without chb12 0.853, subject-mean 0.815), Ec 0.628 — none non-inferior on pooled (floor 0.661) | **C' = E16e adopted; final scalar = C (E16e) alone, D1 5/0.0075.** E15 TTA: negative with 4 seeds in this configuration. Eb loses to C pooled (−0.045) but is higher without chb12 (+0.007) and on validation (+0.033): both are reported. Drift per component: gamma IQR/MAD 1.54 (L 0.69, S9 0.85, recon 0.74); 57.5 % of the final tail sits in gamma's top-quartile files (≈ 0.18 for the others); gamma's top files carry more flagged windows (0.660 vs 0.395) |
| **E19b** short branch on C (E16e), fine grid, total cap 25 | best eligible union = main cell, p_s 0.001, +0.000 FA, +0.000 sensitivity → NOT adopted. Short seizures (3 × 4 seeds): every miss of the short branch is "below threshold"; 3-window-smoothed peak percentiles chb02 0.97–0.99 (caught by main), chb21 0.98–0.995 (main 2/4 seeds), chb12 0.81–0.91 (never caught) | mechanism: short-seizure peaks sit at the 0.81–0.995 percentile, below a short-branch threshold of top 0.1–0.5 %; a lower threshold would cost FA unless a discriminating feature is added (inference, not measured). No evidence-backed fix on 12 seed-instances; short seizures reported descriptively. E19 on Eb (coarse grid) is superseded (Eb not final) |
| **E21b** C (E16e) + L + gamma_dt, fine grid | 0.609 @ 16.98 (cell 15/0.01), ≤ 15 0.559, ≤ 10 0.492, val 0.867, without chb12 0.812, subject-mean 0.768 @ 15.9. Tail share in gamma's top files: Eb 0.575 → E21b 0.387 (C alone 0.400); flagged share in the tail: Eb 0.945, E21b 0.900, **C 0.889** | inferior (pooled and subject-mean fail). Gamma's drift was removed (mechanism confirmed) but the ensemble is below C at every FA level. Final scalar = **C (E16e)**, D1 5/0.0075. First score whose top-2 % tail is below 0.95 flagged (base rate ≈ 0.46) |
| **E18** kernel CPD localizer on C, fine grid (`results/e18_cpd_localizer/`) | detector 0.681 @ 24.25; after CPD 0.662 @ 23.70 (guard −0.02 passed by 0.001). Matched pairs n = 249 (≈ 62 seizures × 4 seeds). Onset |error| median: detector 16 s, **CPD 8 s**, no-CPD control 12 s; offset: detector 24 s, **CPD 12 s**, control 40 s. Events ≤ 30 s (n = 69): onset 20 → 12 s, offset 12 → 8 s. Bias: onset +8 s (late), offset −4 s. CPD used on 96 % of matched events; fallback 14 % of all events | **ADOPTED as the onset/offset localizer** — halves both errors; beats the no-CPD control (so the gain is the change point detection itself, not only the unsmoothed score). Caveat: −0.019 sensitivity (≈ 1.8 seizures of 94) from boundaries moved off the detected seizure; mechanism not yet measured |
| **Bootstrap** final (C, 5/0.0075) − E (V2_LW, 15/0.02), subjects resampled, B = 10,000 (`results/p2_bootstrap/`) | E 4-seed 0.489 @ 20.06 (2-seed reproduction 0.489 @ 19.78 exact). Pooled sensitivity +0.191 [+0.095, +0.285]; subject-mean +0.171 [+0.063, +0.297]; FA/day +4.19 [−1.08, +8.18]. Without chb12: +0.184 [+0.065, +0.305]; FA +3.87 [−1.71, +7.98] | gain not carried by one subject. Confound: the final system spends ~4 more FA/day than E's coarse-grid cell; a matched-budget reference (E re-selected on the fine grid at ≤ 25) is still owed. Descriptive only: every choice was made on these 15 subjects |
| **E17b** latent-family rank ensemble {S6e, S9e, S12e, Smean_e} (E16e-corrected), fine grid | S9e reproduces C exactly. **E17b 0.668 @ 19.98 (cell 5/0.005), ≤ 15 0.622, ≤ 10 0.548, val 0.983 (at cell 0.967), without chb12 0.853, subject-mean 0.828 @ 19.5, seeds 0.681/0.660/0.660/0.670, short 2.0/3**; C 0.681 @ 24.25 (subject-mean 0.821 @ 24.1, val 0.900, short 1.5/3). Tail flagged share C 0.889 → E17b 0.834. Members alone (characterisation, not selectable): S6e 0.665, S12e 0.686, Smean_e 0.686 | **non-inferior → final scalar = E17b** (pre-registered rule; a deliberate choice: the author kept the non-inferiority rule although it trades up to 0.02 pooled sensitivity for the ensemble shape, and did not change it after seeing the result). C and S12e/Smean_e are reported beside E17b in the report. −0.013 pooled at ≤ 25 (≈ 1.2 seizures) but at 4.3 fewer FA/day, higher ≤ 15, subject-mean, validation and short seizures. S12e/Smean_e above C are post-hoc and are not used |
| **E18 / E18d** on E17b (cell 5/0.005) | detector 0.668 @ 19.98 → CPD 0.662 @ 19.55 (both arms). Onset |error| 16 → 8 s (no-CPD control 8 s), offset 20 → 16 s (control 40 s), n = 243; bias onset +4 s, offset +4 s; events ≤ 30 s (n = 84): onset 20 → 10 s, offset 12 → 12 s. Lost-seizure table (E1 overlap rule): 0 | E18 adopted (localization rule passes); E18d ties → E18 (rule). **Wording (reviewer):** on E17b the onset gain equals the no-CPD control (8 s = 8 s) and the offset gain over the detector is 4 s (one window); on C the onset gain over the control was one window (8 vs 12 s). The report states only that CPD reduces the error relative to the detector's boundaries; the share due to CPD itself versus less smoothing is not separated. Control 1 has a +32 s offset bias because it takes the last supra-threshold window in the ±60 s segment (no 90 s merge); a stronger control 2 (contiguous run containing the event peak) is added. The −0.006 cannot come from seizures losing overlap (0 lost); hypothesis, not measured: SzCORE splits references > 300 s (e.g. chb11: 5 scored references) and CPD returns one compact segment that covers fewer of the split pieces. The lost-seizure table must use the scorer's split references to test it |
| **Bootstrap** final (E17b, 5/0.005, after CPD) − E, B = 10,000 | final 0.662 @ 19.55 vs E 0.489 @ 20.06 — **matched FA budget** (E_fine re-selected on the fine grid = the same cell 15/0.02). Pooled +0.173 [+0.075, +0.287]; subject-mean +0.171 [+0.055, +0.303]; FA −0.51 [−6.80, +4.54]. Without chb12: pooled +0.184 [+0.050, +0.315], FA −0.99 [−7.62, +4.17] | the gain is not explained by a larger FA budget nor by chb12. Descriptive and optimistic: about 30 gated decisions were made on these 15 subjects |
| **E18 diagnostics** on E17b (re-run, no ledger row) | control 2 (contiguous run, no merge): onset 12 s, offset 12 s (bias +0 s) vs CPD 8 s / 16 s and detector 16 s / 20 s. Split references: 95 pieces vs scorer n_ref 94 per seed (rule nearly right; one-piece mismatch unexplained); pieces covered by the detector but lost after CPD: 1.2 per seed, 4 of 5 in the 756-s chb11 seizure (its last 156-s piece) | the −0.006 after CPD is the long chb11 seizure: CPD returns one compact segment that drops the last split piece. **On offset, control 2 (12 s) beats CPD (16 s)**: the CPD gain over the detector is on onset only. Wording in the report: CPD halves the onset error relative to the detector boundaries; offset is not improved over a simple contiguous-run rule |
| **E20a** multivariate kernel CPD (18-channel trajectory) as localizer | post-localizer sensitivity 0.657 (< E18 0.662 → FAIL); onset 8 s (= E18), **offset 8 s (E18 16 s)**, bias −4 s; CPD used on 98 % of matched events | **not adopted** by the pre-registered rule (sensitivity); its offset is the best of all localizers on non-test. Candidate for P3 together with a long-seizure fix |
| **Look #6** (test, single shot, frozen: E17b + D1 5/0.005 + kernel CPD) | see §3. Per subject (seed 42, after localizer \| E): chb03 7/7 \| 1/7, chb06 2/10 \| 0/10, chb13 1/12 \| 2/12, chb14 6/8 \| 0/8, **chb15 0/20** \| 0/20, chb16 2/10 \| 0/10, chb17 3/3 \| 0/3, chb18 5/6 \| 0/6. Onset/offset on test (n = 103 pairs): detector 28 / 16 s, CPD 8 / 20 s (offset bias +16 s), control 2 20 / 12 s. Patient-level bootstrap, seed 42, computed from this table: final − E pooled +0.303 [0.094, 0.630], subject-mean +0.470 [0.19, 0.75]; 4-seed version in `p2_test_bootstrap.py` | FP/day matched the pre-registered 23.5. Sensitivity rose ×8.7 over E but halved from non-test (0.662 → 0.336), as rule 19 predicts. Four subjects (chb06, chb13, chb15, chb16: 52 of 76 seizures) hold 5 TPs; without chb15 pooled is 0.464. To reach 0.50 pooled: +12 seizures (38/76) |

Caution (rule 19 and multiple looks): the 15 non-test subjects have now been used for E1–E21; seizure
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
| E19 | 1 (p_s rule on Eb) | adopted, superseded (Eb not final) | 3 p_s values |
| E21 | 3 stage 1 + 3 stage 2 (fine grid, decided after seeing E16e/Eb_h) | E16e adopted; final C | — |
| E19b | 1 (union vs re-selected main) | not adopted | 3 p_s × fine cells |
| E21b | 1 (C + L + gamma_dt, non-inferiority) | inferior | — |
| E18 | 1 (CPD localizer on C) | adopted | no-CPD control |
| E17b | 1 (latent family, non-inferiority) | adopted (final scalar) | 3 members alone |
| E18 / E18d on E17b | 2 | E18 (tie) | no-CPD control |
| E20a | 1 (multivariate localizer) | not adopted (sensitivity) | — |

Together with P1 (E1–E10) the non-test set has carried about 39 gated decisions by E17b/E18 (P1 ≈ 12,
P2 ≈ 27; reviewer's count from this table, 2026-10-07). From E16 on, `results/p2_ledger.csv` is the
complete list. The report states this count beside the selected result.

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

### 6.5 E21, freeze plan and test-look pre-registration (2026-10-07)

**E21 — finer top-p grid** (`src/e21_fine_grid.py`). Grid {0.05, 0.03, 0.02, 0.015, 0.01, 0.0075,
0.005, 0.002, 0.001} for every score; gates unchanged (G1 at ≤ 25 with the seed rule, G2–G5, M); no new
route through a gate; ≤ 15, ≤ 10, FA/day and subject-mean descriptive. Ledger note on every row:
"grid changed after seeing E16e and Eb_h". Stage 1 re-scores S9 base, E16e, E16b and E15 (TTA; gated
only if seeds 2 and 3 are adapted, `e15 adapt --tags clean_seed2 clean_seed3 --suffix _s23 --no-z`);
C' = best passing arm (exact ties → lower FA), else S9 base. Stage 2 re-runs the E17 construction with
C' (Eb_h is stage-2 Eb when C' = E16e; counted once). Diagnostics before any further drift arm: drift
per component (S9, L, gamma, recon) and its share of the final scalar's tail; per-subject check of the
0.459/0.459 flagged-share coincidence; share of top-quartile files with a seizure vs all files.
Consistency with the author's binding rules: E21 fixes a measured construction defect (threshold grid
resolution) with gates fixed, and keeps the short-seizure branch (requirement 2.6) in the pipeline.

**Validation — two quantities, one gate definition (author, 2026-10-07).** `val` = best D1 cell re-selected
on the 3 validation subjects alone at their own FA/day ≤ 25 — the definition of every gate G4 since E12
(E12, E14, E15, E16, E16g, E17, E21). `val_at_cell` = sensitivity of the 3 validation subjects at the cell
selected on all 15 subjects — descriptive only. Same Eb, cell 15/0.02: `val` 0.800 (E17, E16g), `val_at_cell`
0.933 (printed by E19 as "val sens"). Gates use `val` only; reports show both, labelled.

**E19b — re-run rule (author decisions 2026-10-07; `src/e19b_short_branch_fine.py`).** On the E21 final
scalar and fine grid: the main-only reference is re-selected on the same grid at ≤ 25; unions over every
main cell and p_s are eligible only with total FA/day ≤ 25 and ≤ 3 added over their own main cell; the
union is adopted only if its pooled sensitivity is strictly higher than the main-only reference. For the
3 short selection-set seizures: percentile of the 3-window-smoothed peak inside the patient, whether the
main detector catches it, and per p_s the reason (below threshold / run > 30 s / merged into > 30 s and
dropped / kept). The next fix of the short branch (e.g. S12) is chosen from these reasons.

**E21 per-subject note.** The median of "top files with seizure" (0.083 vs 0.158 all files) hides
disagreement: in chb01 (0.455 vs 0.167), chb12 (0.833 vs 0.476), chb20 (0.500 vs 0.207) and chb19
(0.250 vs 0.100) the high-score files are richer in seizures than the patient's average, so the
"drift" removed by E16e there may include peri-ictal state. The without-chb12 and per-subject numbers
are reported for that reason. Validation for Eb vs C uses `val` (gate) and `val_at_cell` (descriptive).

**E21b — gamma drift correction (author proposal 2026-10-07; `src/e21b_gamma_detrend.py`).** Rank
ensemble C (E16e) + L + gamma_dt (gamma minus its ±15 min running median inside each file). Reference
C alone. Gate = E17 stage-2 non-inferiority (pooled ≥ C − 0.02, subject-mean ≥ C − 0.02, `val` ≥
C − 0.067). If non-inferior it becomes the final scalar (E17 rule: a combination with gamma is
preferred within 0.02; it restores the ensemble of readouts); otherwise the final scalar stays C.
Mechanism reported: share of the tail in gamma's top files, before (Eb) and after (E21b).

**Measured runtimes (2026-10-07).** Cache-only steps on 4 seeds: E21b 124 s, E18 44 s, bootstrap 44 s,
E21 317 s, E19b 124 s. Earlier estimates (10–70 min) were 3–10× too high.

**Open before the freeze (proposed 2026-10-07, author decision pending).**
1. E17b was pre-registered for "no cross-readout combination passes" (§6.3) and that condition now
   holds (E21 stage 2, E21b): rank ensemble of the latent family {S6, S9, S12, channel mean} with the
   E16e correction, same non-inferiority gate vs C.
2. E18 sensitivity loss (−0.019): measure which seizures lose overlap after CPD; fix to test:
   accept a CPD segment only if it overlaps the detector event, else keep the detector boundaries.
3. Bootstrap at a matched FA budget: add E re-selected on the fine grid at ≤ 25 FA/day.

**Scripts for the open items (approved 2026-10-07).** `src/e17b_latent_family.py` (family {S6, S9,
S12, channel mean}, each E16e-corrected; S9e must reproduce C); `src/e18_cpd_localizer.py --overlap`
(E18d) plus a lost-seizure table in every E18 run (`lost_<arm>.csv`); `src/p2_bootstrap.py --cpd
plain|overlap` (final system scored after the localizer) with a second reference E_fine (E re-selected
on the fine grid at ≤ 25 FA/day). Order: E17b → E18 (plain, re-run for the diagnostic; the ledger then
holds a duplicate E18 row) → E18d → bootstrap with the chosen localizer.

**Literature lead (Perplexity, 2026-10-07; NOT verified, not citable yet).** Onset/offset latency is
rarely reported on scalp EEG; leads: Shoeb & Guttag ICML 2010 (CHB-MIT, onset mean 4.6 s / median 3 s,
patient-specific, 1-s epochs); "ScoreNet" (CHB-MIT onset/offset latency; the two Perplexity answers give
different venues, DOIs and values — must be checked against the PDF); an IRBM 2019 paper (onset 3.9 s,
offset 49.3 s); UPCON 2019 (onset ~3–6 s, offset ~4–8 s). All supervised and at 1–2 s resolution; our
windows are 4 s. doi.org and Crossref are not reachable from the container; verification needs the PDFs.

**Freeze plan (fixed now).** E21 (done) → E19b (done, not adopted) → E21b → E18 on the final scalar (C, or E21b if
adopted; fine grid) → subject-level bootstrap vs E (`src/p2_bootstrap.py`) → freeze → test look #6.
If E21b is adopted, E19b is not re-run (its mechanism — short peaks below any affordable threshold —
does not depend on the scalar). Total cap 25 approved by the author. E18 reports a
no-CPD control (unsmoothed score above the detector threshold) beside CPD and the raw detector.

**Test-look pre-registration (before the freeze).**
1. On the non-test set: subject-level bootstrap (resampling subjects, 4-seed mean) of the difference in
   pooled sensitivity at the frozen cells between the final system and E (E8/E9 V2_LW + D1 15/0.02),
   with and without chb12; reported as a 95 % interval.
2. Expected FA/day on test: about 1.2 × the non-test value of the frozen cell (E9: 19.8 non-test →
   24.1 test with the same cell). Expected sensitivity: a moderate improvement over E9 at most
   (§6.2 item 6).
3. The look reports: 4 seeds; pooled and subject-mean sensitivity, precision, F1 and FP/day from the
   scorer's counts; onset/offset error with n (detector, CPD, no-CPD control); short seizures caught;
   E (frozen P1 system) on the same look as reference. Logged as look #6 in §3.

### 6.6 Freeze candidate (written 2026-10-07, before any test look; author decision pending)

1. GAE v2 clean, seeds 42, 1, 2, 3 (`data/models_v2/`, identity in `PROVENANCE_V2.md`). **Headline
   model = seed 42** (as E9; the one the demo runs), reported with the 4-seed mean ± SD.
2. Readout per seed: per patient and channel, LedoitWolf Mahalanobis of the 16-d node latent fitted on
   all non-signal-loss windows of the patient (label-free); per-channel robust-z; order statistics
   k = 6, 9, 12 of 18 and the channel mean; each minus its centred ±15 min running median inside each
   file (non-causal: post-hoc review triage, not a real-time alarm); each → patient percentile; equal
   mean = the ensemble anomaly score (one scalar).
3. Detection: D1, per-file centred moving average of 5 windows (20 s), threshold = the patient's own
   top 0.5 % of time, contiguous supra-threshold runs, merge 90 s.
4. Localization: kernel CPD (ruptures KernelCPD, rbf, min_size 2, exactly 2 change points) on the
   unsmoothed score over each event ± 15 windows; accepted when the inner segment spans ≥ 2 windows and
   is above both outer segments, else the detector's boundaries.
5. Non-test reference (4 seeds): 0.662 @ 19.55 FA/day after CPD; subject-mean 0.828 @ 19.5 (detector);
   onset/offset |error| 8 s / 16 s. Expected on test (pre-registered): FA/day ≈ 1.2 × 19.6 ≈ 23.5;
   sensitivity a moderate improvement over E9 at most (§6.2 item 6).
6. Before the freeze (approved by author and reviewer 2026-10-07; no other new arm): E20a — kernel CPD
   on the 18-channel trajectory as localizer only (`e18_cpd_localizer.py --multi`), replaces E18 only
   if post-localizer sensitivity ≥ E18's on E17b (0.662) and the median onset and offset errors are each
   not worse, one better by ≥ 4 s; E20b (CPD as detector) is not run. Diagnostics in the same re-run:
   control 2 and the split-reference table (`--no-ledger`).
7. Test look: `src/p2_test_dump.py` (label-free per-node outputs of the 8 test subjects, 4 seeds;
   reproduction gate against the E9 cache), then `src/e22_test_oneshot.py --localizer kernel1d|multi`
   (R1 non-test reproduction of the exact code path, R2 E = E9 on test; refuses without the git tag
   `p2-frozen` and `--confirm-look-6`; records file hashes). Sequence: E20a + diagnostics → choose the
   localizer by the E20a rule → `--repro-only` → freeze, tag `p2-frozen` → test dump → look #6.
8. Timing of look #6 relative to the supervisor meeting (08/10 08:00): author decision. Points that the
   supervisor may comment on are §7 items 3 (label-free per-patient fitting under "unsupervised") and
   4 (role of CPD).

## 7 · Decisions for the supervisor meeting (08/10) — RESOLVED, see section 10.1

The list below is kept as it was asked.

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

## 9 · Stage P3 (opened 2026-10-07)

Target (author): pooled test sensitivity ≥ 0.50 (38/76, +12 seizures over look #6) at the best FP/day
achievable; sensitivity first. Thesis shape kept: GAE → one scalar ensemble anomaly score → non-parametric
CPD with a measured localization role.

### 9.1 Check of the two closing P2 results

**Burden table** (`results/p3_seizure_burden/burden.txt`; CHB-MIT summaries only, no model output).
- Counts reconcile with the scorer (computed): test 76 annotated = 76 references. Non-test 93 annotated →
  scorer 94 per seed: chb11's 752-s seizure is split into 3 pieces (+2) and two chb12 seizures less than
  90 s apart are merged (−1). This explains the "95 split pieces vs 94" of the E18 diagnostics (that table
  split but did not merge). chb12's summary lists 40 seizures; 13 lie in the skipped files chb12_27/28/29.
  The chb11 seizure is 752 s by annotation; "756 s" elsewhere is its 189 windows.
- Short seizures: < 20 s by annotation — test 23 (chb06 8, chb13 2, chb14 3, chb16 10), non-test 3. The
  scripts' count (`p2_scalars.short_refs`: run of ictal windows × 4 s < 20 s) gives 18 on test because a
  seizure is rounded up to whole windows. Both are reported, labelled.
- Ictal minutes / top-0.5 % budget: chb12 2.91, chb15 2.86, chb08 2.60, chb11 1.47, every other ≤ 0.97.
  H1 is **not confirmed by this table alone**: a seizure is caught by one supra-threshold window inside its
  tolerance span, so ictal time above the budget does not cap sensitivity by itself (chb08, ratio 2.60 with
  5 long seizures, was caught 5/5 even by E — E12 table). The two seizure-rich patients (chb12 26
  references, chb15 20) are the two that fail; budget vs ranking is measured per seizure in P3-A.

**Bootstrap of look #6, 4 seeds** (`results/e22_test_oneshot/BOOTSTRAP.md`): final pooled 0.336
[0.133, 0.670], subject-mean 0.498 [0.226, 0.770]; final − E pooled +0.293 [0.100, 0.609], subject-mean
+0.455 [0.187, 0.724], FP/day −0.95 [−12.0, +5.1]; without chb15 pooled 0.455 [0.240, 0.750].
Consistent with the seed-42 values of §6.1. Reading: with 8 patients the interval of the current system
already contains 0.50; chb15 (20) and chb13 (12) hold 42 % of the test seizures (computed), so the pooled
target is mostly a statement about two patients. The official SzCORE aggregate (subject-mean) of look #6 is 0.498 (4-seed mean; seed 42 0.508).

### 9.2 Test-information policy for P3 (author decision 2026-10-07)

The author asked to study the test EEG itself (not results), because the 8 test patients are markedly
harder (Part B: seizure peaks out-ranked by 20–50 % of non-ictal spans on test vs ~4 % on non-test).
Two tiers, both logged in §3:
- **T-A, label-free:** test EEG features and model outputs without annotations (input distribution vs the
  training set, flagged share, file drift, the channel owning the score tail). The system is label-free and
  fits each patient on its whole recording, so this is information the system itself sees; it is disclosed.
- **T-B, annotation-guided:** test seizure times joined to scores (per-seizure miss anatomy). Test-informed.

Not done: no sensitivity-vs-FA curve and no threshold choice on test; operating points and gates stay on
the 15 non-test subjects. Any design motivated by T-B makes look #7 test-informed. **Look #6 remains the
clean held-out result in the report; look #7 is reported beside it, labelled test-informed.**
Test facts already known from the attribution study (Chapter 3; the author's blind channel annotation of
the 76 test seizures), counted as T-B: all ten chb06 seizures were annotated generalized; chb15's twenty
are focal (focal test seizures carry 4.55 annotated channels on average), with V1's channel ranking
concentrated on P3-O1.

### 9.3 Hypotheses (extending HANDOFF_P3 §3; H1–H5 unchanged)

- **H6 spatial scale.** The frozen family uses order statistics 6, 9, 12 and the channel mean; a large
  value needs ≥ 6 anomalous channels. Focal seizures with few involved channels (chb15) may stay low.
  Non-test characterisation (E14, before drift correction): S3 0.537, max 0.457, below S9 — but the
  non-test seizures may be broader.
- **H7 input domain shift.** If a test patient's node features fall outside the training distribution,
  the training-set standardisation clips them at ±4 and information is lost.
- **H8 the drift correction absorbs clustered or long seizures.** The ±15 min running median may subtract
  part of a seizure when seizures cluster in time (chb15) or when a file is short.

### 9.4 P3-A — failure anatomy (`src/p3_anatomy.py`, descriptive, no gate)

Part A label-free (T-A) on all 23 subjects: f7 clip share and median shift in training-SD units
(constants recomputed as `train_gae_v2.norm_constants`), flagged share, file drift before/after the
correction, tail share in top-quartile files, channel owning the tail, files with an odd channel.
Part B per seizure (T-B on test): p_need = share of the patient's smoothed values ≥ the seizure's peak over
its SzCORE tolerance span (the top-p a threshold must reach to touch it), for the frozen scalar, the scalar
without the correction, each member and the focal members S1e, S3e; spatial extent; gap to the nearest
seizure; caught or not. Part C (non-test, H2): one LedoitWolf refit per channel without the 5 % most
distant windows. Reproduction gates R0 (scalar = e22), R2 (non-test detector = E17b grid), R3 (test
detector = look #6), R4 (untrimmed refit vs cached distances). Results: §9.6 (written after the run).

### 9.5 Decision table (fixed before any P3-A result)

One construction per lever; a lever runs only if its trigger holds. Counts are 4-seed means.

| lever | hyp. | trigger (from P3-A) | construction |
|---|---|---|---|
| L1 focal member | H6 | test: rescued by S3e at top 0.5 % minus lost ≥ 3 | rank ensemble {S3e, S6e, S9e, S12e, Smean_e}; S3 chosen over S1 a priori (one bad channel owns the max; 3 channels ≈ the mean focal extent) |
| L2 per-patient budget | H1, H3 | ≥ 3 missed test seizures with p_need in (0.005, 0.02] | top-p_i = clip(q_i, 0.0025, 0.02); q_i = share of the patient's smoothed windows where the mean robust-z of the four E16e-corrected members exceeds k; k calibrated once on the 15 non-test patients (seed 42) so that the median q_i = 0.005 — the frozen budget redistributed, not enlarged |
| L3 guarded correction | H8 | test: rescued without the correction minus lost ≥ 3 | running median over ±15 min that ignores values above the file's 90th percentile of that member |
| L4 trimmed fit | H2 | non-test: rescued minus lost ≥ 2, with ≥ 1 on chb12 | per-channel LedoitWolf refit without the 5 % most distant windows; needs a test dump of node latents (`p2_test_dump.py` + latents, est. 15–45 min CPU) |
| L5 per-patient input normalisation | H7 | a test patient with clip share > 5 % on a feature, or median shift > 2 training SD, beyond every training patient | retraining (Kaggle ≈ 3.5 h per seed, 4 accounts in parallel, then dumps); not feasible on 07/10; recorded as a finding, author decides |
| L6 localizer hybrid | H4 | always (non-test evidence exists) | CPD onset + control-2 offset (contiguous run; non-test offset 12 s vs CPD 16 s); events > 300 s keep the detector boundaries |

**Gate for L1–L4** (non-test, 4 seeds, fine grid, D1 cell re-selected at ≤ 25 FA/day; reference = P2
frozen detector E17b 0.668, subject-mean 0.828, `val` 0.983): non-inferiority — pooled ≥ 0.648,
subject-mean ≥ 0.808, `val` ≥ 0.916 — and FA/day ≤ 25. Reason: the non-test set is near its ceiling and
easier (rule 19); a lever aimed at the test failure mechanism can only be required not to damage it there.
L2 has no grid (its budget is the construction): FA/day ≤ 25 and the same non-inferiority. **L6 gate:**
post-localizer sensitivity ≥ detector − 0.005 and median onset/offset errors not worse, one better by ≥ 4 s.
**Combination:** passing levers are combined in table order and the combination re-passes the same gate
once. Then freeze (tag `p3-frozen`) → look #7: 4 seeds, the look-#6 report set, disclosed as
test-informed; expected FP/day ≈ 1.2 × non-test. If no lever triggers or passes, the P2 frozen system stands
(author: the best number is accepted).
**Time arithmetic (estimated, not measured):** P3-A 10–25 min; each cache-only lever 2–6 min; L4 adds a test
latent dump of 15–45 min; look #7 5–15 min. L5 is excluded on 07/10 by its retraining time.

### 9.6 P3-A results (`results/p3_anatomy/`, 436 s; gates R0, R2, R3, R4 passed)

**T-A, label-free.** f7 clip share ≤ 0.012 on every test patient (non-test up to 0.077, chb09); median
shift ≤ 1.56 training SD (chb14 1.562 vs the non-test maximum 1.540, chb10 — marginally above). Only the
7 added node features were checked, not the adjacency. No (file, channel) pair has a median per-channel
z > 3 anywhere. After the ±15 min correction the file drift is 0.02–0.05 MAD on every patient. **H7 not
supported by this check; L5 not triggered.** Two label-free clues (reviewer): after the correction the
tail still sits in top-quartile files in chb16 (0.706), chb03 (0.645) and chb06 (0.257 → 0.515; also
chb04 0.629, chb11 0.683 on non-test); the 4-seed mean index of the tail-owning channel is 14.5–16 in 5/8
test patients vs 3/15 non-test (a mean of indices; to be read per channel against the montage order, P3-B D3).

**T-B, per seizure** (p_need = top-p a threshold needs to touch the seizure; frozen budget 0.005):

| seizures with p_need ≤ | 0.005 | 0.01 | 0.02 | 0.05 | 0.10 |
|---|---|---|---|---|---|
| test (76) | 25.75 | 27.5 | 45.5 | 62.25 | 71.25 |
| non-test (93) | 60.5 | 66.5 | 74.25 | 85.25 | 90.0 |

An upper bound (no false alarms, no merging), not an operating curve. chb15: 0/20 at ≤ 0.01 but 10.5/20
at ≤ 0.02 (median p_need 0.019) — its seizures sit just below the budget, a near miss. Non-test analogue
chb12: 4.75 → 12.5 of 27 between 0.005 and 0.02. chb06, chb13, chb16: mostly 0.02–0.10 (chb16 in-seizure
peaks median 0.185: short seizures). Missed test seizures, seed 42: 16 near (0.005–0.02; chb15 11),
28 mid (0.02–0.10), 5 deep (> 0.10).

**Members.** Seizures at ≤ 0.005 (test / non-test): S9e 25.0 / 61.0, S12e 24.0 / 61.0, Smean_e 24.75 /
59.75, S6e 23.0 / 58.25, S3e 22.0 / 59.0, S1e 19.25 / 54.25. Focal members rescue 1.5 (S3e) and lose
5.25 on test; chb15's seizure peaks recruit 8 channels (median) with z > 3. **H6 not supported in this
configuration; L1 not triggered.** Without the ±15 min correction: 13.0 test / 47.25 non-test (vs 25.75 /
60.5) — removing the correction hurts; the guarded variant (L3) was not tested. **H8 not supported by this
check; L3 not triggered.** Trimmed refit, 5 % (non-test): rescues 0.25, loses 2.0. **H2 not supported in
this configuration; L4 not triggered.** chb15's channels with median z > 2 over the whole seizure: 0.5
(peaks 8) — bursty anomaly, possibly diluted by the 20-s smoothing (H9, P3-B D1); chb12 shows the same
pattern (5.25 / 0).

**Triggered (decision table 9.5): L2** (16 ≥ 3 near misses) **and L6** (always) → `src/p3_levers.py`
(gates as in 9.5, reproduction of the frozen detector and of E18 first). Look #7 script
`src/e23_test_look7.py` written before any P3 result on test; it runs only if p3_levers changes the
frozen configuration, after tag `p3-frozen`.

**Headline rule (fixed 2026-10-07, before look #7; reviewer audit 3).** Look #6 remains the clean held-out
result. The thesis's final system is the P3-frozen configuration chosen on the non-test gates before look
#7; look #7 reports it on test, labelled test-informed, at two operating points declared before the look:
**balanced** (D1 cell re-selected at ≤ 25 FA/day on non-test) and **sensitivity-priority** (≤ 40 FA/day on
non-test). No look #8. The headline is never chosen by a test result. Hard stop for P3: 23:30, 07/10.
`p3_levers.py --include-test` prints only the label-free budget p_i on test; `e23 --repro-only` reads
non-test chb01 only.

**P3-B (reviewer audit 3).** Diagnostics first (`src/p3b_diag.py`): D1 smoothing scales {1, 2, 3, 5, 9}
(per-seizure p_need, non-test operating curve, short-seizure proxy = first 3 windows of each non-test
seizure without tolerance); D2 where the top non-ictal windows lie relative to seizures (peri-ictal
share, flagged share, files); D3 tail-owning channel per channel index vs the montage. Then levers L7
(multi-scale smoothing union, only if D1 supports it), L8 (4-seed average of the scalar), L11 (±5 min
running median), each designed after D1–D3 and before its own result; every lever must also move its
mechanism on chb12 (non-test analogue), never on chb15 alone.

### 9.7 Levers, P3-B diagnostics, freeze step and stop plan (2026-10-07 evening)

**p3_levers (non-test, 4 seeds; reproduction of the frozen detector and E18 exact).** k = 4.0677.
L2 0.657 @ 20.53 FA/day, subject-mean 0.814, validation 0.983, chb12 TP 4.75 = frozen → gate passed (no
gain over the frozen 0.668 @ 19.98; non-inferior). L6 hybrid on L2: sensitivity 0.654 (detector 0.657), onset
8 s = CPD, offset 12 s vs CPD 16 s → adopted; on the frozen detector it failed only the margin (0.662 vs
0.663; CPD 0.662 as well). Label-free test budgets (T-A): chb15 0.0200 (cap) on all 4 seeds; chb06 and
chb17 at the 0.0025 floor; others 0.0028–0.0082.
**Measured harm of the L2 floor (non-test):** chb21 at 0.0025 TP 1.75 → 0.50; chb20 at 0.0041 3.0 → 2.5.
L2 passed only because other patients compensated. Fix → L2f (budget never below 0.005), `src/p3c_freeze.py`.

**D1 smoothing (H9).** Not supported: chb15 median p_need 0.0234 at 1 window vs 0.0191 at 5; test
seizures at p_need ≤ 0.005: 22.75 (1) / 25.75 (5) / 18.25 (9). Non-test curve at ≤ 25 FA/day: smoothing 5
0.668 @ 20.0, smoothing 9 0.697 @ 19.9 (top 0.0075) — the two sets disagree (rule 19); smoothing stays 5,
L7 is not run. A uniform 2 % budget costs 95.1 FA/day on non-test (sensitivity 0.803): only per-patient
budgets are affordable.
**D2.** The top non-ictal windows are mostly flagged (typically 0.45–1.0) and rarely peri-ictal (within 10 min,
outside the tolerance: mostly < 0.2; exceptions chb08 top 0.5 % 1.00, non-flagged — a post-ictal state that
still left 4.25/5 caught — and chb09 0.30); chb15 0.785 flagged, 0.05 peri-ictal. Exception chb06:
flagged 0.27–0.30 — its tail is not high-amplitude activity (its readout is inverted; limitation). The
`median_dist_min` column is void (np.median over NaN; script bug; `peri_10min` is unaffected).
**D3.** No dominant channel (top share typically 0.09–0.20, max 0.44 chb08). Montage order (code):
FP1-F7, F7-T7, T7-P7, P7-O1, FP1-F3, F3-C3, C3-P3, P3-O1, FP2-F4, F4-C4, C4-P4, P4-O2, FP2-F8, F8-T8,
T8-P8 (14), P8-O2 (15), FZ-CZ (16), CZ-PZ (17); T8-P8 is never dominant. No channel defect.

**Reading (the core).** The remaining test failure is a ranking problem: in chb06, chb13 and chb16 the
seizures sit at the 2–5 % level below the patient's own high-amplitude non-seizure states — the P1 core
(record §4) that the representation still carries. No cache-only lever measured tonight targets it; it
needs a representation change (Future Work). L8 (seed average) and L11 (±5 min median) are not run: no
measured mechanism points to them. chb15 is the one near miss a label-free budget can reach.

**Freeze step (p3c_freeze, before its result).** L2f gate = the L2 gate + monotonicity (every subject's TP ≥
frozen); L2f replaces L2 if it passes and its pooled ≥ L2's. Localizer by the L6 rule on the chosen budget.
Sensitivity-priority point: floor = the best smoothing-5 top-p at ≤ 40 FA/day on non-test, kept if ≤ 40.
`e23_test_look7.py` reads `results/p3c_freeze/freeze.json`.

**Stop plan.** No new arm after p3c_freeze. Sequence: p3c_freeze → author approval → tag `p3-frozen` →
look #7 (both points) → record 9.8 + handoff → performance work closed. 23:30 is reserved for fixing a
script error and re-running the same configuration, never for changing it.

### 9.7b Freeze step results and the rules for look #7 (fixed before the look)

**p3c_freeze (non-test, 4 seeds; reproductions of L2 and of the frozen detector exact; 76 s).**
L2f detector 0.678 @ 23.81 FA/day, subject-mean 0.842, validation 0.983, without chb12 0.868, every
subject's TP ≥ frozen (chb21 back to 1.75, chb20 to 3.0) → gate passed, pooled ≥ L2 (0.657) → **L2f
replaces L2**. L2f's +0.010 over the frozen detector costs +3.8 FA/day: it lies on the frozen detector's own
curve (0.668 @ 20.0 → 0.705 @ 32.3), so L2f wins nothing on non-test; its expected benefit on test is the
budget given to chb15. Localizer (L6 rule on L2f): hybrid onset 8 s vs CPD 4 s (worse: events > 300 s and
fallbacks keep detector onsets) → **CPD stays**. After CPD: 0.670 @ 23.25, subject-mean 0.832.
Sensitivity-priority point (floor 0.0075 = best smoothing-5 top-p at ≤ 40 FA/day): 0.697 @ 32.73 after CPD
→ kept, **descriptive only**. Review fraction (event time / recorded time) after CPD: L2f 0.0162, S 0.0219.
Label-free test budgets (balanced): chb15 0.0200 on all seeds (raw q 0.0231–0.0250, above the cap); chb14
0.0055–0.0065, chb18 0.0063–0.0082, chb03 0.0050–0.0052; chb06, chb13, chb16, chb17 at 0.0050 (raw q below 0.005).

**Disclosures.** (1) The cap 0.02 binds for chb15 (raw q above it on every seed) and for no non-test patient
(non-test maximum 0.011): the cap decides chb15's result and is untested on non-test. It was fixed in the
decision table (9.5) after look #6 and the burden table, before the per-seizure anatomy — test-informed in
the broad sense. (2) L2 / L2f have no measured benefit on non-test (chb12, the seizure-rich analogue, gets
0.0051 and stays at 4.75). (3) The label-free test budgets were seen before L2f was designed; the reason for
L2f is the non-test chb21/chb20 loss. (4) "A representation change is needed for chb06/chb13/chb16" is an
untested hypothesis, not a finding: patient fine-tuning (E15), more capacity (E1) and input normalisation
(H7) all lacked support.
**Correction (Claude 1).** The earlier forecast of 27–32 FA/day on test for the balanced point was too low.
Computed from the label-free test budgets: budget-weighted mean top-p ≈ 0.0076, which on the non-test
curve is ≈ 32 FA/day; × 1.2 ≈ 38. Expectation: balanced ≈ 35–40 FA/day, sensitivity point ≈ 45–50.

**Frozen P3 system (tag `p3-frozen`).** P2 frozen scalar and D1 (smoothing 5, merge 90 s) with top-p_i =
clip(q_i(k = 4.0677), 0.005, 0.02); kernel CPD localizer (E18). Second, descriptive operating point:
clip(q_i, 0.0075, 0.02). `results/p3c_freeze/freeze.json`, read by `src/e23_test_look7.py`.
**Reading rule for look #7.** The target (pooled ≥ 0.50; seed-42 headline with the 4-seed mean) is judged
on the balanced point only. Every result is reported as is: ≥ 0.50 → target reached; < 0.50 → not reached,
reported with the subject-mean and the bootstrap difference to look #6; balanced FP/day > 40 → flagged as
above the acceptable level. Look #6 stays the clean held-out result; look #7 is labelled test-informed.
No look #8. After look #7: record 9.8 and handoff; performance work closes.

### 9.8 Look #7 (test-informed) and the close of P3

**Balanced point (the target point), seed 42 after the CPD localizer: 37/76 = 0.487 @ 27.49 FP/day**, precision
0.104, F1 0.172, subject-mean 0.577. 4 seeds: 0.477 ± 0.022 @ 29.15 ± 1.26, subject-mean 0.567 ± 0.019.
Detector stage (before the localizer): seed 42 38/76 = 0.500 @ 28.35, 4 seeds 0.480 ± 0.025.
**By the reading rule (9.7b) the target is not reached:** the frozen system's output is after the localizer,
one seizure short on seed 42. FP/day stayed below the pre-registered expectation (35–40) and below 40.
Per subject (seed 42): **only chb15 changed (0 → 11/20)**; FP rose in chb15 (14 → 53), chb14 (27 → 34) and
chb18 (23 → 38); every other patient is identical to look #6 (budget 0.005). chb06 2/10, chb13 1/12,
chb16 2/10 unchanged (32 seizures, 5 caught).
Patient-level bootstrap vs look #6 (4-seed means, B = 10,000): pooled +0.141 [0.000, 0.333], subject-mean
+0.070 [0.000, 0.201], FP/day +5.27 [+0.37, +13.60]. The gain rests on one patient and on the cap 0.02,
which binds only on test (disclosure 9.7b).
Sensitivity-priority point (descriptive): seed 42 0.487 @ 36.83; 4 seeds 0.490 ± 0.022 @ 38.12 — about +9
FP/day for no material gain.
Localization (balanced, n = 146 matched pairs): onset |error| detector 32 s, CPD 12 s (bias +8), offset
detector 20 s, CPD 24 s (bias +16), contiguous-run (hybrid) offset 16 s. CPD's role on test is the onset
(32 → 12 s); its offset is late, as on non-test (9.7, 6.1). The hybrid was not adopted (non-test rule) and is
not switched after the look.

**How the report presents the test results (fixed).** Look #6 (P2 frozen, 0.342 @ 22.2, subject-mean 0.508 seed 42; 4 seeds 0.336 / 0.498) is the clean held-out evaluation. Look #7 (P3 frozen, 0.487 @ 27.5, subject-mean 0.577) is the
final system, labelled test-informed, with the bootstrap interval and the statement that its gain is
chb15 at a budget cap that binds only on test. Both are reported; neither replaces the other.

**What remains unsolved (Future Work, hypotheses, not findings).** chb06 (10 generalized seizures of
12–20 s; inverted readout; its non-ictal tail is not high-amplitude, flagged 0.27–0.30), chb16 (10 seizures
of 6–14 s, below the 4-s window with 20-s smoothing) and chb13 (12 seizures at the 2–5 % level under its own
high-amplitude states, flagged 0.89 in its tail). Candidate directions, none tested: shorter or overlapping
windows for short seizures (rebuild of graphs and retraining), a two-sided readout for seizures that are
more regular than the background, and a representation that separates seizures from the patient's own
high-amplitude states. Patient fine-tuning (E15), capacity (E1) and input normalisation (H7) lacked support.
Any test of these would need a new evaluation set; the CHB-MIT test set is used up (looks 1–7).

**P3 closed (tag `perf-p3-closed`).** Performance work stops here; next: report Chapters 2–5 and the demo
(`docs/HANDOFF_REPORT.md`).

### 9.9 External validation X1 (chb24 and Siena; clean, never used before)

**Design.** The P3 frozen system unchanged (code path = `e23_test_look7.evaluate`), run once on CHB-MIT chb24
(outside the 23-subject splits) and the Siena Scalp EEG database (14 adult patients, 47 seizures, ~141 h by the per-patient hours of the X1 summary),
pre-registered in `src/x1_external.py` before any of these recordings was processed. Declared, label-free
adaptations: z-score statistics from every 10th window of the whole recording; Siena: 18 bipolar channels
derived from the referential montage, 512 → 256 Hz, notch at 50 Hz. Label sources fixed after a label-only
inventory and before any scoring: chb24 every present file, 21.3 h (its summary lists only the 12 seizure files); Siena
annotations from the SzCORE benchmark's own converter (`esl-epfl/epilepsy2bids` d3fb175, verbatim), which
corrects the published typos (the first parser missed 6 seizures and read PN00-3 as 3,660 s). Gates before
scoring: R-feat (chb03 file rebuilt on Kaggle: f7/bp5 exact, 0.045 % adjacency entries differ) and R-model
(distances within 3e-6 relative; look #7 reproduced for chb03, 4 seeds). Runtime 29 min (Kaggle CPU).

**Results (balanced point, after the CPD localizer).**

| set | seed 42 | 4 seeds pooled | 4 seeds subject-mean (official) | onset / offset (CPD) |
|---|---|---|---|---|
| chb24 (16 seizures, 21.3 h) | 14/16 = 0.875 @ 29.5 FP/day, precision 0.350, F1 0.500 | 0.828 ± 0.060 @ 28.4 | (one subject) | 4 / 4 s (n = 53) |
| Siena (47 seizures, 140 h) | 33/47 = 0.702 @ 44.0, subject-mean 0.748 @ 41.5 | 0.617 ± 0.060 @ 43.8 | sens 0.633 ± 0.079, precision 0.160, F1 0.226, 41.0 FP/day | 20 / 28 s (n = 116) |

Siena subject-level bootstrap (4-seed means): subject-mean sensitivity [0.477, 0.777], pooled [0.495, 0.726],
FP/day [32.3, 53.9] (computed). The descriptive sensitivity point adds no seizure on chb24 (budget 0.0107 above
its floor) and +1 on Siena seed 42 at +2.7 FP/day. Siena per patient (seed 42): 0/3 PN05, 1/3 PN09, 1/3 PN13;
FP/day above 70 in PN06, PN07, PN16.

**Comparator on the same data (SzCORE benchmark, `esl-epfl/szcore` results/*/siena.json, commit c57da2f,
subject-mean).** DynaSD (the only unsupervised entry): sensitivity 0.664, precision 0.126, F1 0.170, 77.7
FP/day. Ours (4-seed mean): 0.633, 0.160, 0.226, 41.0 FP/day — similar sensitivity at about half the false
alarms. Supervised entries range from 0.29 to 1.00 sensitivity (e.g. Zhu 2023 0.674 / 15.3 FP/day; EventNet
0.587 / 8.2; SeizureTransformer 0.685 / 1.0, trained on other corpora). Caveats: same annotations and the
same scoring definitions, but our own scorer implementation and our own signal path (the benchmark feeds the
BIDS-converted recordings to each algorithm); not run inside the benchmark.

**Reading.** On data never seen during any design step, the frozen system detects 83 % of chb24's and 62–70 %
of Siena's seizures (adult patients; the GAE was trained on children), at 28 and 41–44 FP/day. The CHB-MIT
test patients are the hard case (look #6 0.342, look #7 0.487); the external sets indicate that the method
generalises, while the false-alarm rate on Siena is above the 40 FP/day level flagged for the test look.
This is the clean held-out evidence for the final system; it does not replace looks #6 and #7.

<!-- report-phase-2026-10-08 -->
## 10 · Report phase (opened 2026-10-08)

### 10.1 Author decisions (08/10; the supervisor reviewed the briefing and asked for the report with the current numbers)

1. **Offline protocol.** Not reported as a result (no table, no figure). One short paragraph (Methods,
   evaluation, or Discussion) states that an earlier evaluation rebuilt the timeline from the annotations
   and filled it with resampled windows from which high-amplitude windows had been removed, and that on
   the continuous recording the same earlier system at the same operating point fell from 0.618 @ 27.4
   FP/day to 23/76 (0.303) @ 73.3 FP/day. The continuous timeline is the protocol of record.
2. Label-free per-patient fitting on the whole recording is part of the unsupervised system (P2 decision;
   DynaSD as precedent).
3. Kernel CPD is the onset/offset localizer on the scalar ensemble anomaly score (decision 2026-10-07);
   the onset gain is measured, the offset is not better than a contiguous-run rule, and both are stated.
4. Test results: look #6 is the clean held-out evaluation, look #7 the final system labelled
   test-informed, side by side (9.8); X1 is the clean external evidence for the final system.
5. Aggregation: pooled and subject-mean side by side (subject-mean = SzCORE's official aggregate);
   headline seed 42 with the 4-seed mean ± SD and the patient-level bootstrap. Look #6 subject-mean:
   **seed 42 0.508, 4 seeds 0.498 ± 0.010** (`results/e22_test_oneshot/SUMMARY.md`); earlier text that
   paired 0.342 with 0.498 mixed the two.
6. The web demo is rebuilt on the final system (seed 42) and its application tier re-run:
   `docs/DEMO_REBUILD_BRIEF.md`.
7. Channel attribution re-run on the final system (A5, 10.2); A4 stays as the attribution of the earlier
   reconstruction readout.
Order of work and fallback: `docs/HANDOFF_REPORT.md` section 0.

### 10.2 Attribution A5 — final system (`src/attribution_v8.py`, `results/attribution_v8/`)

Pre-registered in `ATTRIBUTION_SPEC.md` A5 and committed with tag `attribution-a5-prereg` before scoring;
one run (70 s), gates G1 (alignment of the 76 annotations to the v2 test windows), G2 (cache), G3 (A4
order confirmation) passed. Score: per-channel robust-z of the per-channel latent distance (the system's
own per-channel quantity), p95 of |z| over the seizure. Method, labels and tests of A4.

| test | value | interval / p | verdict |
|---|---|---|---|
| L1 macro-AUROC, 62 focal | 0.5473 | [0.4992, 0.5971], permutation p 0.018 | pass (the registered criterion is the permutation p; the bootstrap lower bound touches 0.5) |
| L2 Δ vs anatomical prior (0.7387) | −0.1914 | [−0.2618, −0.1182] | fail, significantly below the prior |
| L3 matched − swapped | −0.0017 | p 0.53 | fail |
| D7 subject-constant control | −0.0754 | — | control higher |

Descriptive: without chb15 0.4864 (p 0.71); seeds 1/2/3 0.543 / 0.588 / 0.545; mean aggregation 0.556;
n_win ≥ 3 0.549; per subject only chb15 above chance (0.675, p 0.001). Reading (spec 4.7, "L1 passes,
L2 fails"): weak concentration on annotated channels, far below a fixed anatomical rule, no
seizure-specific information — the same pre-registered negative as A4 (0.5694, L2 −0.1694), now on a
second readout. The demo panel becomes `Channel-level latent anomaly — Event N`, neutral.

### 10.3 Ledger note

`results/p2_ledger.csv` `verdict` records the outcome of each step's own gate, not the final selection:
E20a, E18 (`_ovl`) and P3-L6 read "ADOPTED" but were not chosen (E20a lost on sensitivity, E18d tied →
E18, L6 was not adopted on L2f). This record (6.1, 9.7, 9.7b) is the selection of record.

### 10.4 Normalisation statistics (disclosure)

CHB-MIT inputs of the v2 system (`c1b_build_trainset`, `c1t_build_testset`) are z-scored with
`data/processed/{subj}_stats.json`, computed by the inherited preprocessing after excluding annotated
seizure windows and the 4-h post-seizure buffer — for every subject, test included. The detection
system uses no labels, but this normalisation step does. X1 and the web demo use label-free statistics
(every 10th window of the whole recording). Effect on CHB-MIT not measured; a descriptive comparison of
the two sets of statistics on the 8 test patients is an open item (HANDOFF section 9).

### 10.5 Repo state (08/10)

Commit `e13e629`: continuous-evaluation results (look #2 evidence) and the v2 checkpoints; v2 inputs and
large caches gitignored. `results/x1_external/SUMMARY.md` restored from git (it had been deleted in the
working tree). Look #4 evidence (`results/veto_screen*`, `results/oracle_gate_bound/`) committed by
`report_phase_sync` follow-up command. `web_demo/*` changes belong to Project 2.
