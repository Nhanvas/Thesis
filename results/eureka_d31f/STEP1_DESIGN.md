# D31-F Step 1 — design of the Euréka ablation suite on the V5 model, and of diagnostics D1 and D2 (approved by the author 19/11/2026 20:35)

*Nothing here has run. Once approved, this text becomes a row in `FUTURE_RESEARCH_PLAN.md` §12, written before any output.
Inputs: table T (`T_past_ablations.md`), the author's instructions of 19/11 20:25, `EUREKA_PLAN.md` §10, and the
code read at `a136a3b`.*

## 0 · Author's instructions of 19/11 20:25 and what follows from them

1. **Every component claim comes from the current model.** All past ablations that a deliverable relies on are re-run on
   the V5 model and the V5 chain. Older versions appear only as history (table T).
2. **Be selective.** A variant is included only if it (a) supports a claim in the report, the slides or the Q&A, or answers
   a judge's comment, and (b) costs no new training. Everything else is logged in plan §14.
3. **Small check first.** A local smoke run on the laptop (Claude Code, minutes) comes before the Kaggle run. Long runs
   go to Kaggle, one notebook per account, in parallel. **Four Kaggle accounts** (author 19/11).
4. **Literature before every proposal**; no claim without a test; the plan itself is reviewed critically (§6).

## 1 · Facts in the code that make the suite cheap (read at `a136a3b`)

- The V5 checkpoints are committed: `data/models_v2/gae_v2_clean_seed{42,1,2,3}.pt`.
- Every stage of V5 is a separate record function:
  - latent: `p2_dump_seeds23.run_model` → Z (n × 18 × 16) and the reconstruction;
  - distance: per-channel `LedoitWolf().mahalanobis`;
  - members, robust z and the ±15-min drift correction: `e17b_latent_family.member` (rolling median of 451 windows);
  - ensemble: `v9_e1_baselines.final_scalar_from_D`;
  - budget signal: `member_mean_z_from_D`;
  - k: `p3_levers.calibrate`;
  - detection, budget and localizer: `v9_e1_baselines.evaluate_arm` → `p3_levers.localize`, mode `cpd` or `hybrid`;
  - per-file baselines: `e16_recording_baseline.arm_distances`;
  - gamma and reconstruction readouts: `p2_scalars.readout`.

  So every variant swaps one function and leaves the rest of the chain as the record code.
- **Proven on Kaggle (R1_SMOKE, R1_RUN):** the committed checkpoints on the earlier data copy (`v9-x3-fold1`, `v9-x3-fold3`)
  reproduce the V5 rows exactly. That is 720 development rows, 128 test rows and k = 4.067744 to the last digit.
  External rows match within the tolerance gate GE: 148 of 240 exact, at most |Δtp| 1 and |Δfp| 2, because the external
  features were rebuilt at float level.
- R1_RUN measured 0.43 h to compute the distances and scores of all sets for 4 seeds (4 workers).

## 2 · Main notebook `EUR_ABL` (inference only, Kaggle CPU, one verified account)

**Research question.** Which components of V5 carry its detection performance? The answer is measured on the
development patients, with per-patient means, four seeds and paired patient-bootstrap intervals. Every variant is also
reported descriptively on the test patients, chb24 and Siena.

### 2.1 Variants (one factor each; IDs from `EUREKA_PLAN.md` §10)

| ID | change from V5 | claim or comment it serves | hypothesis (prediction) | literature |
|---|---|---|---|---|
| V0 | none (gate: V5 rows reproduced) | every number | — | — |
| **1a** | diagonal covariance (variance per latent dimension) | judge 1: Mahalanobis named as the novelty | lower: low-variance directions carry the anomaly | Rippel et al. 2021 |
| **1b** | Euclidean distance to the channel mean (no covariance) | same | lower than 1a | Rippel et al. 2021; Defard et al. 2021 |
| **4a** | reference = clean windows of the 12 training patients, per channel. A training patient's own windows are left out of its reference | V5 Table 6 column A, now on the latent | much lower (V5 Section 4.2) | DynaSD (Ojemann et al. 2026) for the per-recording idea |
| **4b** | reference = first 10 min of each file (E16 arm a) | V5 Table 6 column B | lower | same |
| **4c** | reference = first 30 min of each file (E16 arm c) | V5 Table 6 column B | between 4b and V0 | same |
| **2a** | drift correction off | V5 Section 4.2 (second gain) | lower, mostly through more false alarms | Logesparan et al. 2015 |
| **2b** | level + spread (per-file median / MAD, E16 arm b) | V5 Section 2.4.3 | lower | Leys et al. 2013 |
| **3a** | one member: 9th largest | ensemble design | small difference | — |
| **3m** | one member: channel mean (was "3b"; renamed, see §6.1) | same | small difference | — |
| **3c** | one member: largest | same | lower (one channel dominates) | — |
| **3g** | + gamma-AEC readout as a fifth member | judge 2: "the gamma score was not removed" | not higher | E21 record (history) |
| **3r** | + reconstruction-error readout | judge 1 described three scores | not higher | E17 record (history) |
| **5a** | smoothing 1 / 3 / 9 windows (V5: 5) | V5 Section 2.5.2 | 9 may be higher on development (as P3-B) | — |
| **6a** | fixed budget 0.5 % for every patient | per-patient budget (V5 Section 4.2) | on development: small difference | — |
| **7a** | detector boundaries (no change point localizer) | Goal 2 (CPD) | worse onset | Truong et al. 2020 |
| **7b** | CPD onset + run-rule offset (`localize` mode `hybrid`) | V5 Section 4.2 (offsets) | better offset | — |
| **8a** | no edges at inference: the GCN keeps only self-loops | council question 1 (why the graph) | fewer false alarms, as F-A1.4 found in cross-validation | Kipf & Welling 2017 |

### 2.2 Data and models

- Data: the defense-time data copy, the same as V5 (`v9-x3-fold1`, `v9-x3-fold3`), plus the external features
  (`thesis-r2-external-features`).
- Models: the four V5 checkpoints. No training.
- Sets: dev15, test8, chb24, Siena 14.

### 2.3 Rules (fixed before the run)

1. **k per variant**, recalibrated by V5's own rule: `p3_levers.calibrate` on the 15 development patients with seed 42,
   and the same k for all four seeds. The budget limits stay at 0.5–2 %. The budget signal is the mean robust z of the
   members the variant uses.
2. **Primary reading (development patients):** the variant's own label-free operating point, after the localizer.
   Reported: per-patient mean sensitivity, F1 and FP/day, as the 4-seed mean ± SD. Paired patient bootstrap of variant − V0
   with B = 10,000 and rng seed 0. Seeds are averaged within each patient before resampling, and chb01 and chb21 form one
   unit.
3. **Secondary readings, to remove the budget effect:**
   - (i) a fixed 0.5 % budget for every variant;
   - (ii) sensitivity at matched FP/day (20 and 28.7) on the curve of a global budget.
4. **Descriptive readings:** test8, chb24 and Siena with the same columns, plus onset and offset errors. No variant is
   chosen from these sets.
5. **No pass/fail threshold for the ablations.** All variants are reported with their intervals.
6. **Replacement rule (R214), written now.** A variant can replace V5 only if, on the development patients:
   - the 95 % interval of its ΔF1 (per-patient mean, own operating point) is above 0, and
   - its point Δsensitivity is ≥ 0.

   If so, the author decides. Its test row was computed in the same run but is read only after that decision. Expected:
   no removal variant passes. 5a with 9 windows is the one candidate the record makes possible.
7. **Gates (STOP):**
   - G-data: dataset hashes;
   - G-repro: V0 equals the V5 rows of `p3c_freeze` (development) and `e23` (test) exactly, and the x1 external rows within
     the GE tolerance;
   - G-k: V0's k = 4.067744;
   - G-worker-sha;
   - G-var: each variant equals its definition on synthetic data (e.g. 1b with an identity covariance equals the
     Euclidean distance; 4b equals E16 arm a on the record's own function).
8. **Wording limits.**
   - 8a runs the trained GAE outside the conditions it was trained in (as in F-A1.4).
   - 4a and the development reading include the 12 training patients, whose latents were seen in training, so the
     development reading is optimistic. Stated beside every development number.

### 2.4 Outputs

- `results/eureka_d31f/abl/`: `per_subject.csv`, `summary.csv`, `bootstrap.csv`, `errors.csv`, `gates.json`, `timing.csv`.
- **Table T2**: one row per variant — development Δ with its interval, then the test, chb24 and Siena values. C1 and C2
  use it, together with T as history.

### 2.5 Cost and order

- Code, a synthetic test and the aggregate are committed before the run (this chat, tonight).
- **Local smoke** (Claude Code on the laptop): chb01, chb03 and PN00 with seed 42, every variant plus G-repro. Expected
  10–20 min, to be measured.
- **Kaggle run:** 1.5–2.5 h. This is a computed estimate: R1_RUN's measured 0.43 h, plus a second forward pass for 8a, plus
  about 20 variants × 38 cases × 4 seeds of scoring. The smoke measures it.

## 3 · Parallel notebook `EUR_9A` (label-free z-score statistics, 4 seeds) — recommended

- **Why.** V5's only label use in the input is the CHB-MIT z-score statistics. Its measured effect is seed 42 on test only
  (33 vs 37 seizures). With all four seeds, and k recalibrated on label-free development data, the project gets a
  completely label-free system number. That answers "is it really unsupervised?" with the same rigour as V5.
- **How.**
  - Features of dev15 and test8 (defense-time file set) are rebuilt from the raw EDF with `x1_external.labelfree_stats`
    (every 10th window of the whole recording, as the application and the external sets).
  - Every raw file is verified against PhysioNet inside the notebook.
  - Then the V0 chain runs with k recalibrated, and the result is compared with V0 by a paired patient bootstrap.
- **Cost.** About 4–5 h on one account (computed from R0's measured 54 s per hour of EEG per worker × about 960 h on
  4 workers, plus scoring). It runs at the same time as `EUR_ABL`.

## 4 · Diagnostics on the laptop (Claude Code; quick; hospital data not involved)

### 4.1 D1 redesigned — can a finer time grid bring short seizures within the budget?

- **Problem with D1 as planned.** The planned D1 (seizure rank against smoothing) already exists on the final scalar
  (T D5) and cannot answer the question. Smoothing changes in 4 s steps, so it says nothing about what a 2 s hop adds.
- **Diagnostic.** For every short seizure (≤ 20 s), take the 4 s windows shifted by +1, +2 and +3 s:
  - 3 in dev15, 18–23 in test8, 4 in chb24, 5 in Siena;
  - features built with the record code and the patient's own statistics;
  - V5 model with 4 seeds; D computed against the patient's own Ledoit–Wolf fit, robust z and drift baseline from the
    unshifted grid.
- **Reading.** The budget each short seizure needs, at its best shift against no shift. A 2 s hop samples exactly these
  phases, so the best shift is an **upper bound** of what the hop can gain in ranking. It is a necessary condition only:
  the hop also doubles the background windows.
- **Rule, fixed now.** The 2 s-hop experiment is worth its cost only if, at the best shift, at least 3 more short seizures
  (4-seed mean, test8 + chb24 + Siena) reach the budget of their patient in V5. Otherwise it goes to plan §14 with this
  evidence.
- **Disclosure.** This uses test annotations to decide whether to run an experiment. That is test-informed and disclosed.
  The experiment itself could only be an ablation (§6.3).
- **Literature.** Pale et al. 2023 (EMBC): with 4 s windows, a smaller step raises the false-positive count and lowers
  episode precision.
- **Cost.** About 20–40 min (computed).

### 4.2 D2 — rhythmicity (decides the rhythm re-ranking, now called "RR")

- **Prior evidence is negative** (T I1). The spectral-peak share did not separate seizure windows from high-amplitude
  non-seizure windows on development: AUROC 0.47–0.50, and 0.35 for seizures under 20 s. Duration (V9-E2), with an event
  AUROC of 0.79 on development, still gave only a trade-off as a veto.
- **What D2 adds.**
  - Event level instead of window level: V5's detected seizure events vs its false-alarm events on dev15, plus the missed
    seizures vs the false alarms that outrank them.
  - Two features with a published basis: the autocorrelation peak at lags of 0.1–1 s (the regularity idea of Shiau et
    al. 2010; Persyst's rhythmicity spectrogram is built on autocorrelation but is commercial, not peer-reviewed), and the
    spectral-peak share, kept for continuity.
  - Each feature taken relative to the patient's own background.
- **Rule, fixed now.** RR is designed only if a feature reaches an event-level AUROC with a patient-cluster bootstrap
  lower bound ≥ 0.80 on development (the level duration reached without a gain), in the same direction in at least 10 of
  the 15 patients. Otherwise RR goes to plan §14.
- **Cost.** About 30 min (computed).

## 5 · Not run before the 22/11 freeze (recommended; the author decides)

- **10a / 10b / 11a / 11b (retraining).** Each needs 4 trainings of about 4.6 h per notebook (R1_RUN measured 4.64 h).
  11a and 11b also need graphs rebuilt from the raw EEG (about 5 h).
  - Judge 2's comment is about the gamma-AEC *score*, which 3g answers without retraining.
  - 10b (gamma band powers in the node input) is a different question.
  - Recommendation: Q&A after 11/12 (plan §14); the run can start after the freeze if the author wants it for the Q&A.
- **The 2 s-hop experiment:** only if D1 passes its rule (§4.1).

## 6 · Critical review of the plan (`EUREKA_PLAN.md` §10)

1. **Name collision.** "3b" means both "one member: mean" and "rhythm re-ranking". Renamed to 3m and RR.
2. **D1 as planned cannot decide** the overlap question (§4.1); replaced by the shift upper bound.
3. **The overlap experiment cannot be selected on development**, which has only 3 short seizures. Under R214 it can
   only be an ablation, never the main system. This lowers its value for the submitted files.
4. **4a needs leave-self-out**; otherwise a training patient is scored against a reference that contains its own
   windows.
5. **A budget confound** hides in every comparison at each variant's own k (the F-A1.4 lesson). That is why reading (i)
   uses a fixed 0.5 % budget and reading (ii) uses matched FP/day.
6. **Development is optimistic** (12 of 15 patients trained the model). Test, chb24 and Siena are reported beside it,
   descriptively.
7. **External rows reproduce only within tolerance on Kaggle.** V0 is recomputed in the same run and every Δ is paired
   within that run, so the tolerance does not enter the differences.

## 7 · References

- Rippel, O., Mertens, P., & Merhof, D. (2021). Modeling the distribution of normal data in pre-trained deep features for
  anomaly detection. *ICPR 2020*, 6726–6733. arXiv DOI 10.48550/arXiv.2005.14140.
- Defard, T., Setkov, A., Loesch, A., & Audigier, R. (2021). PaDiM: A patch distribution modeling framework for anomaly
  detection and localization. *ICPR 2020 Workshops*, LNCS 12664, 475–489. arXiv DOI 10.48550/arXiv.2011.08785.
- Pale, U., Teijeiro, T., & Atienza, D. (2023). Importance of methodological choices in data manipulation for validating
  epileptic seizure detection models. *EMBC 2023*, 1–7. arXiv DOI 10.48550/arXiv.2302.10672.
- Shiau, D.-S., Halford, J. J., Kelly, K. M., et al. (2010). Signal regularity-based automated seizure detection system for
  scalp EEG monitoring. *Cybernetics and Systems Analysis*, 46(6), 922–935 (PMID 21188288).
- Logesparan, L., Rodríguez-Villegas, E., & Casson, A. J. (2015). *Med Biol Eng Comput*, 53, 929–942.
  DOI 10.1007/s11517-015-1303-x.
- Leys, C., et al. (2013). DOI 10.1016/j.jesp.2013.03.013.
- Ojemann, W. K. S., et al. (2026). medRxiv. DOI 10.64898/2026.02.15.26346325.
- Kipf, T. N., & Welling, M. (2017). arXiv:1609.02907.
- Truong, C., Oudre, L., & Vayatis, N. (2020). DOI 10.1016/j.sigpro.2019.107299.
