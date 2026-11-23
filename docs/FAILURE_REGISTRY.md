# Failure registry and research-question ledger — V5 system

Track F, milestone M2, stream K, item K1 (chat F2-01, 23/11/2026). Plan: `docs/FUTURE_RESEARCH_PLAN.md` §15.

This file lists the known ways in which the frozen V5 system fails (Part A table, Part B details) and the
research questions those failures raise (Part C). It contains no new measurement. Every number is copied from a
committed file and cited by path. The file is public, so it holds no patient-identifying information and no
content from the hospital recordings.

---

## Part 0 · Scope and conventions

**The system (V5).** Per-window graphs (CAR, wPLI + AEC, top 20 % of edges) → graph autoencoder (node input 30,
3,964 parameters) → per patient and per channel, a Ledoit–Wolf Mahalanobis distance of the 16-d latent → robust z →
6th / 9th / 12th largest + channel mean, each minus a ±15-min running median per file → patient percentiles → one
ensemble score → smoothing (5 windows), per-patient label-free alarm budget clip(q_i(k), 0.5 %, 2 %), merge 90 s →
kernel change point detection (2 change points, ± 60 s) for onset and offset. Seeds 42, 1, 2, 3; k = 4.0677
(`docs/PROJECT_INSTRUCTIONS.md` @ `937b6b5`, section "Results"). V5 is the frozen baseline of milestone M2.

**Sets.** Development = 15 CHB-MIT patients (12 training + 3 validation); test = 8 CHB-MIT patients (76 seizures);
chb24 = one more CHB-MIT case; Siena = 14 adults (47 seizures), external. Development includes the training
patients, so its numbers are optimistic. Test, chb24 and Siena are descriptive: the test patients have been looked at
many times (see FM-24).

**Which model a number comes from.** Most numbers come from the V5 checkpoints. Some come from other models of the
same recipe, and each such row says so:
- **path-2**: the thesis system re-run on the complete CHB-MIT copy, seeds 1–4;
- **CV models**: the 4-fold / six-partition model comparison on 24 cases;
- **R0**: the thesis recipe retrained on Kaggle CPU (PC1, PC7), the control of every retraining ablation.

**Citations.** A source is written `path @ commit`, where the commit is the last one that changed the file. Numbers
are copied as printed in the source. Numbers taken from a csv file are rounded to the precision shown here and marked
"(csv)". Intervals are 95 % patient-bootstrap intervals unless the source says otherwise. "No measurable difference"
means the interval contains 0.

**Status** describes the *mechanism* of a failure. The observation itself is always measured.
- **measured**: the mechanism has been tested and the result is committed with numbers.
- **hypothesis**: an explanation has been stated with its check, but the check has not been run.
- **open**: no explanation has been tested, or the evidence conflicts.

Process faults that were found and fixed are marked "measured (fixed)".

**M2 item** refers to `docs/FUTURE_RESEARCH_PLAN.md` §15.4: V1 recall against review share, L1–L3 label-free
per-recording baseline, X1 SzCORE open benchmark, G1 core decision, N1–N2 artifact context, T1 TUSZ, H1
reader-study protocol, F5b offset rule. "Parked" refers to §14.22.

---

## Part A · Summary

| ID | family | failure (one line) | status | M2 item |
|---|---|---|---|---|
| FM-01 | missed seizures | Missed seizures have low amplitude relative to the patient's own background and are short, in every model and within patients | hypothesis | V1, T1 |
| FM-02 | missed seizures | The patient's own high-amplitude non-seizure activity outranks the missed seizures | measured | N1, V1 |
| FM-03 | missed seizures | Seizures shorter than 20 s almost never reach the threshold; the time grid is not the cause | hypothesis | T1 (weak events later) |
| FM-04 | false alarms | About 29 false alarms per day on test and 41 on Siena; precision about 0.1, so triage only | measured | V1, H1 |
| FM-05 | false alarms | False alarms are concentrated in windows the patient's 5-SD amplitude flag marks | measured | N1 |
| FM-06 | false alarms | The 5-SD flag is not a rare-event marker, and the record z-score statistic is dominated by a few windows | measured | L2 |
| FM-07 | false alarms | What the flagged non-seizure events are (artifact, physiological, non-epileptiform) is unknown | open | N1, N2 |
| FM-08 | false alarms | The GAE gives more false alarms than an MLP autoencoder or K-means for the same seizures | measured | G1 |
| FM-09 | false alarms | Every input or preprocessing change that adds false alarms does it by fragmentation | hypothesis | G1, L2 |
| FM-10 | false alarms | File-level drift as a cause of false alarms is weakly supported | open | L2 |
| FM-11 | false alarms | Blind artifact removal (ASR) lowers detection | measured | N2 |
| FM-12 | boundaries | The detector's onset is late; the change point localizer corrects it | measured | — |
| FM-13 | boundaries | The localizer places offsets later than the annotation, at the end of a post-ictal elevation | measured | F5b, H1 |
| FM-14 | channel ranking | Channel ranking agrees with annotated channels only slightly above chance and below an anatomical prior | measured | parked |
| FM-15 | generalisation | Sensitivity drops from development to test | open | X1, T1 |
| FM-16 | generalisation | V5 sits at the top of the retraining distribution; the validation loss does not pick the better detector | measured | G1, X1 |
| FM-17 | generalisation | The seven amplitude features suffice for the training patients but not for new ones; the connectivity row restores sensitivity on unseen CHB-MIT patients, not on Siena | hypothesis | T1, X1 |
| FM-18 | generalisation | The learned encoder adds no measurable gain on development | measured | G1 |
| FM-19 | generalisation | Detection depends on each patient's whole recording as the reference | measured | L2 |
| FM-20 | generalisation | Siena differs from test through the false-alarm rate and the seizure mix | hypothesis | X1, L2 |
| FM-22 | label use | The z-score statistics excluded annotated seizure windows | measured | L2, L3 |
| FM-23 | label use | The per-patient budget of the final system was chosen after looks at the test set | measured | L2, L3 |
| FM-24 | evaluation | CHB-MIT has no untouched confirmatory set left | open | X1, T1 |
| FM-25 | deployment | The review application (SzScan) scores lower than V5 on the same patients; the cause is not recorded | open | L1 |
| FM-26 | reproducibility | Kaggle machine types train with different arithmetic under the same library versions | measured | X1 |
| FM-27 | reproducibility | ASR output is not bit-reproducible across computers in about one file in six | measured | N2 |
| FM-28 | reproducibility | Rebuilding features from the raw EDF moves numbers at the third decimal | measured | L3, X1 |
| FM-29 | reproducibility | Pool workers ran an older module than the notebook embedded | measured (fixed) | — |
| FM-30 | reproducibility | The model-comparison seizure table has 185 rows per model, but 186 seizures are counted | open | unassigned |

(FM-21 is not used: during drafting it was merged into FM-15 and FM-24.)

---

## Part B · Details

### Missed seizures

**FM-01 — Missed seizures have low amplitude relative to the patient's own background and are short.**
- *Observation.* In the model comparison (CV models, 24 cases), every model misses the same seizures. Seizures
  missed by both the GAE and another model have a median amplitude ratio against the patient's own background of
  1.27–1.29× and a median duration of 28–32 s. Seizures caught by both have 2.3–2.6× and 68–72 s
  (`results/model_cmp/ANALYSIS.md` @ `1e653fa`, §4 item 4).
- *Measured.*
  - The amplitude association holds within patients, not only between easy and hard patients (path-2, 23 patients =
    test + chb24 + Siena). The within-patient coefficient of log amplitude ratio is positive in all 8 fits
    (+0.82 … +1.60), and its interval excludes 0 in 6 of 8. The within − between differences all contain 0
    (`results/r2/r1_system/rp/rp4/bw/SUMMARY.md` @ `b5ade00`).
  - On V5, 4 of 18 short test seizures are detected at most (detector stage, per seed:
    `results/e23_test_look7/SUMMARY.md` @ `c266efd`, column "short").
- *Explanations contradicted.* Event shape. No property of the flagged events (rhythm, waveform, spread, artifact
  signatures) reaches the rule for separating seizures from false alarms. The best is duration, with development AUROC
  0.778 [0.715, 0.846] and within-patient 0.795 [0.734, 0.862] (`results/eureka_d31f/diag/EV.md` @ `fa43c38`;
  `results/eureka_d32f/diag_check/CHECK.md` @ `198817e`).
- *Still open.*
  - (a) A distance score cannot rank a low-amplitude seizure above the patient's high-amplitude background (FM-02).
  - (b) The 4-s feature window and the alarm budget set the ceiling, whatever the model family (hypothesis in
    `results/model_cmp/ANALYSIS.md` §4 item 4).
  - (c) Seizure type or localisation (focal, extratemporal), which CHB-MIT does not annotate.
- *Status.* hypothesis. *M2.* V1 (c) lists the seizures still missed at 5 % / 10 % review; T1 tests by seizure type.

**FM-02 — The patient's own high-amplitude non-seizure activity outranks the missed seizures.**
- *Observation.* Part B of the oracle bound uses e = the share of equally long non-ictal spans whose smoothed maximum
  is at least the seizure's peak. The score here is the cached score of the earlier continuous-evaluation system, a
  predecessor of V5 (`src/oracle_gate_bound.py` docstring). On test, the median e is 0.304 (long seizures), 0.182 (mid)
  and 0.539 (short) with 5-window smoothing. It falls to 0.000 / 0.005 / 0.003 when an oracle sets the flagged (±5 SD)
  non-ictal windows to the patient's background median (series oracleV1; `results/oracle_gate_bound/summary.md`
  @ `8301132`). Ictal windows are never touched, so this is an upper bound no label-free gate can reach.
- *Measured.* The same activity is what carries detection: removing the seven absolute amplitude features changes
  development sensitivity by −0.277 [−0.393, −0.163] (R0 retrained; `results/eureka_d32f/pc1/T_PC1.md`
  @ `f460b4b`). So missed seizures and false alarms share one root cause: amplitude relative to
  the patient's own background.
- *Explanations contradicted.* Smoothing. Short-seizure ranking hardly depends on the smoothing length, since the
  median e of short test seizures is 0.369–0.539 for 1–15 windows (`results/oracle_gate_bound/summary.md`).
- *Still open.* Whether a label-free signal (artifact class, event context) can lower the background's rank without
  the oracle.
- *Status.* measured. *M2.* N1 (premise check), V1.

**FM-03 — Seizures shorter than 20 s almost never reach the threshold; the time grid is not the cause.**
- *Observation.* Of 18 test seizures shorter than 20 s, on average 1.0 has a smoothed peak above the patient's V5
  threshold. This holds both on the original grid and at the best of four grid shifts (`results/eureka_d31f/diag/D1.md`
  @ `fa43c38`).
- *Explanations contradicted.* Time resolution. Shifting the 4-s grid by 1–3 s adds 1.25 short seizures over test +
  chb24 + Siena, below the rule of 3 written before the run (same file).
- *Still open.* (a) A 4-s window dilutes a 10–20-s seizure into a small number of windows, which then fall below the
  budget (hypothesis). (b) The per-seizure rows of `D1.md` list chb06 seven times and chb16 ten times among the
  18 short test seizures, so this may be a patient effect.
- *Status.* hypothesis. *M2.* T1 (seizure-type and duration subgroups); weak-event features after T1 (§14.22 row 111).

### False alarms

**FM-04 — About 29 false alarms per day on test and 41 on Siena; precision about 0.1, so triage only.**
- *Observation.*
  - Test final system: 0.567 ± 0.019 sensitivity at 28.7 FP/day (`results/eureka_d31f/abl/aggregate/T2.md` @ `2c0a7ca`,
    row V0).
  - Per-seed per-patient precision after the localizer: 0.118, 0.110, 0.104, 0.113 (`results/e23_test_look7/SUMMARY.md`
    @ `c266efd`).
  - Siena: 0.633 ± 0.079 at 41.0 FP/day, precision 0.160 (`docs/PERF_PHASE_RECORD.md` @ `67ab0ba`).
- *Measured.* The ceiling comes from FM-02 and FM-05. A fewer-alarm setting exists: a latent averaged over 3 windows
  gives development F1 +0.052 [+0.021, +0.085] and FP/day −6.9 [−9.6, −3.9] at sensitivity −0.006 [−0.072, +0.053]
  (`results/eureka_d32f/opt/aggregate/T2.md` @ `efdf2eb`, row O7; an ablation, not adopted).
- *Still open.* How many seizures a reader sees for a given share of the recording reviewed (the clinically relevant
  quantity), and whether a reader accepts this load.
- *Status.* measured. *M2.* V1, H1.

**FM-05 — False alarms are concentrated in windows the patient's 5-SD amplitude flag marks.**
- *Observation.* On V5 seed 42 test, the share of flagged windows among each patient's top 0.5 % of non-seizure
  windows is 62.3 % for chb03, 29.9 % for chb06, 89.3 % for chb13, 84.0 % for chb14, 78.5 % for chb15, 90.7 % for
  chb16, 90.0 % for chb17 and 61.8 % for chb18 (`results/p3b_diag/tail.csv` @ `ece0198` (csv), tier `top0.5%`).
- *Measured* (path-2, same flag, same windows). The flag share of false-alarm windows minus the base rate over valid
  non-seizure windows is +0.33 [+0.17, +0.43] per patient, 4-seed mean. False-alarm windows are 0.73 flagged against a
  base of 0.40 (`results/r2/r1_system/rp/rp4/fa_summary.csv` @ `b5ade00` (csv), arm L2f). chb06 is the exception.
  The matching V5 base rate is not in a committed file.
- *Still open.* See FM-06 and FM-07.
- *Status.* measured (association). *M2.* N1.

**FM-06 — The 5-SD flag is not a rare-event marker, and the record z-score statistic is dominated by a few windows.**
- *Observation.* The record 5-SD flag marks between 27.8 % (chb10) and 58.8 % (chb21) of the non-ictal windows of every
  CHB-MIT case. "High-amplitude" therefore means "above 5 SD of the patient's own sampled background", not a rare
  artifact (`results/r2/r0_data/rb1c/cases.csv` @ `38a9207` (csv), column `flagged_record_share`).
- *Measured.* The record SD is dominated by a small share of windows. The top 1 % of sampled windows holds a
  median-channel share of the squared deviation of up to 37.5 % (chb04), and MAD / SD is as low as 0.26
  (`results/r2/r0_data/rb1c/SUMMARY.md` @ `38a9207`).
- *Still open.* Whether a robust statistic (MAD, IQR, SD without clipped windows) changes detection. This has not
  been measured.
- *Status.* measured (the statistic's behaviour); its effect on detection is a hypothesis. *M2.* L2 (record vs robust
  statistic, chosen on development by a rule written before).

**FM-07 — What the flagged non-seizure events are is unknown.**
- *Observation.* False alarms are high-amplitude windows (FM-05), but whether they are artifacts, physiological
  activity (sleep transients, arousal) or non-epileptiform abnormalities has never been labelled.
- *Explanations contradicted.* Handcrafted signatures separate them: no event property, artifact signatures
  included, reaches the separation rule (`results/eureka_d31f/diag/EV.md` @ `fa43c38`).
- *Still open.*
  - (a) Artifact classes that a detector trained on annotated artifacts can recognise (Ingolfsson et al. 2024).
  - (b) Non-epileptiform abnormalities, which were the main false-positive class in Saab et al. 2024.
  - (c) The patient's normal high-amplitude physiology, which no artifact label would cover.
- *Status.* open. *M2.* N1 tests (a) on the development patients; N2 only if N1 passes.

**FM-08 — The GAE gives more false alarms than an MLP autoencoder or K-means for the same seizures.**
- *Observation* (CV models, partition 0). The GAE, MLP-AE and K-means catch 115, 115 and 117 of 186 seizures with
  1,129, 827 and 786 false alarms (`results/fa16/SUMMARY.md` @ `6f23509`). Over six partitions, K-means − GAE F1 is
  above 0 in 6 of 6 (`results/fa16/repl/SUMMARY.md` @ `f0c2497`).
- *Measured* (`results/fa14_v2/aggregate/interventions.csv` and `results/fa14_v2/aggregate/SUMMARY.md` @ `f36a6d6`; six partitions, 24 cases).
  - MLP-AE − GAE: −8.1 [−11.0, −5.3] FP/day (csv).
  - Removing all edges at inference: −2.0 [−4.3, +0.3] FP/day (csv). At the fixed 0.5 % point this removes a share of
    0.35 [0.14, 0.52] of the excess.
  - One time-stable graph per patient: −0.4 [−2.5, +1.9] FP/day (csv).
  - The GAE's background score varies more between consecutive windows (lag-1 autocorrelation difference −0.1295
    [−0.1410, −0.1176]).
- *Explanations contradicted.*
  - Instability of the per-window edges (the time-stable graph leaves the gap unchanged).
  - The alarm budget (the gap is as large at the fixed 0.5 % point).
- *Still open.* The remaining three quarters lie in the trained GAE itself. Weights cannot be separated from
  training-with-propagation without a retraining test (parked, §14 row 37).
- *Status.* measured. *M2.* G1 (GAE, MLP-AE, K-means, no-encoder chain inside the label-free protocol, on independent
  data).

**FM-09 — Every input or preprocessing change that adds false alarms does it by fragmentation.**
- *Observation* (fixed 0.5 % budget, development). The "events" and "s per event" columns of each source give:

  | change | model | events | s per event | source |
  |---|---|---|---|---|
  | without the 7 absolute features (10a) | R0 retrained | 4,745 against R0's 2,628 | 42.0 against 56.0 | `results/eureka_d32f/pc1/diag/DIAG_PC1.md` @ `f460b4b` |
  | wPLI-only graph (11a) | R0 retrained | 947 against 618 | 44.4 against 56.4 | `results/eureka_d37f/pc6/T_PC6.md` @ `4baf6e1` |
  | ASR in the preprocessing | path-2 recipe | 62.1 against 41.5 per patient-seed (csv) | 44.8 against 56.0 | `results/fa15/reading/diag_events.csv` @ `a16df8a` |

  The same holds for the GAE against the MLP-AE (FM-08).
- *Measured.* In 10a the share of windows flagged barely changes (development 0.62 % against R0's 0.59 %), so the
  extra false alarms are not a larger budget (`DIAG_PC1.md`).
- *Still open.* (a) The score's window-to-window variance rises (measured only for the GAE, FM-08) and splits one
  high-amplitude stretch into several events. (b) Weaker inputs give more, smaller local maxima. Why fragmentation
  is common has not been tested across arms.
- *Status.* hypothesis. *M2.* G1 and L2 (temporal integration of the latent, as O7, inside the label-free protocol).

**FM-10 — File-level drift as a cause of false alarms is weakly supported.**
- *Observation* (path-2, arm L2f).
  - 44.5 % of false alarms fall in file-edge zones, which cover 41.3 % of the time.
  - Per patient, the false-alarm rate per hour at the edges minus the rate in the middle is +0.23 [+0.03, +0.42]; in
    the frozen arm it is +0.20 [−0.01, +0.39] (`results/r2/r1_system/rp/rp4/fa_summary.csv` @ `b5ade00` (csv)).
- *Measured.* Turning the drift correction off changes development sensitivity by −0.126 [−0.216, −0.043] and FP/day
  by −7.2 [−11.2, −3.4] (`results/eureka_d31f/abl/aggregate/T2.md` @ `2c0a7ca`, row 2a): the correction buys
  sensitivity at the cost of alarms.
- *Still open.* Whether residual drift (beyond the ±15-min median) produces part of the false alarms.
- *Status.* open. *M2.* L2 (drift estimated from the recording itself).

**FM-11 — Blind artifact removal (ASR) lowers detection.**
- *Observation.* ASR (cutoff 20, per-file calibration) removes a median of 54.2 % of seizure-span power, 41.2 % of
  high-amplitude non-seizure power and 0.0 % of ordinary background (`results/v9_x6/SUMMARY.md` @ `5c3d1ef`).
- *Measured* (path-2 recipe retrained, 8 seeds per arm; `results/fa15/reading/T_PC5.md` @ `a16df8a`). With ASR in the
  preprocessing, development final sensitivity goes from 0.819 ± 0.016 to 0.727 ± 0.022, a change of −0.092
  [−0.164, −0.017]. FP/day changes by +11.1 [6.5, 15.8].
- *Still open.* The effect includes the stricter 5-SD flag of the cleaned signal, which was not separated. Only one
  ASR setting was tested.
- *Status.* measured. *M2.* N2 (artifact information as context; the signal is never removed).

### Boundaries

**FM-12 — The detector's onset is late; the change point localizer corrects it.**
- *Measured.* Localizer − detector median |onset| is −12 [−12, −4] s on development, −20 [−28, −8] s on test final and
  −16 [−24, −4] s on Siena (`results/r4_f5a/READING_F5A.md` @ `6d338b8`). The detector's onset is late because of the
  5-window smoothing and the high threshold, while the score rises abruptly at seizure onset.
- *Status.* measured. *M2.* — (resolved by the design).

**FM-13 — The localizer places offsets later than the annotation, at the end of a post-ictal elevation.**
- *Observation.* The change in median |offset| is not measurable on any set, e.g. +4 [−4, +16] s on test final.
  The signed offset moves later: +16 [+8, +36] s on test final, with a share of late offsets of 0.72 against 0.44 for
  the detector (same file).
- *Measured.* After the annotated offset the score keeps 59 % (development), 62 % (test) and 81 % (Siena) of its
  seizure level. The EEG's δ power, with no model involved, shows the same post-ictal change. The same holds for the
  48 CV checkpoints of both the GAE and the MLP-AE, so it is not a message-passing effect (same file).
- *Explanations contradicted.*
  - Seizures fading out gradually: the score falls as fast as it rises.
  - Three states with two change points: a third change point makes the offset worse.
- *Still open.* Whether the annotated end or the score's return to background is the clinically right end. Only
  one annotation per seizure exists, and offsets are where experts agree least (Halford et al. 2015).
- *Status.* measured (mechanism); the clinical reference is open. *M2.* F5b (offset rule, after T1), H1 (expert
  judgement).

### Channel ranking

**FM-14 — Channel ranking agrees with annotated channels only slightly above chance and below an anatomical prior.**
- *Observation.* On 62 focal test seizures (seed 42), macro AUROC is 0.5473 [0.4992, 0.5971]. Against the anatomical
  prior (AUROC 0.7387) the difference is −0.1914 [−0.2618, −0.1182] (`results/attribution_v8/SUMMARY.md` @ `043a145`,
  tests L1, L2).
- *Status.* measured. In the application it is shown only as "channel anomaly", never as localisation. *M2.* parked
  (§14.22 row 113).

### Generalisation to new patients and datasets

**FM-15 — Sensitivity drops from development to test.**
- *Observation.* V5 development 0.832 ± 0.014 at 23.2 FP/day, test 0.567 ± 0.019 at 28.7 FP/day
  (`results/eureka_d31f/abl/aggregate/T2.md` @ `2c0a7ca`). The development set includes the 12 training patients.
- *Still open.*
  - (a) Patient heterogeneity in a small test set (8 patients, 76 seizures). The variance component "patient × seed"
    dominates: on test, the SD shared by every seed is 0.033 against 0.100 for patient × seed
    (`results/eureka_d34f/pc7/T_PC7.md` @ `2d54544`).
  - (b) Optimism from training patients in development (FM-17).
  - (c) A seizure mix that is harder in test (FM-01, FM-03).
- *Status.* open. *M2.* X1 (data nobody in this project has seen), T1.

**FM-16 — V5 sits at the top of the retraining distribution; the validation loss does not pick the better detector.**
- *Measured* (R0, 16 new seeds; `results/eureka_d34f/pc7/T_PC7.md` @ `2d54544`).
  - The retrained recipe gives development sensitivity 0.803 ± 0.029 and test 0.523 ± 0.048.
  - V5 lies at the 100th percentile of 4-seed means on development (0.832 against a central 95 % of 0.777–0.820) and at
    the 99th on test (0.567 against 0.481–0.562).
  - Spearman ρ between validation loss and development sensitivity is +0.23 [−0.30, +0.67].
- *Still open.* Luck and machine type cannot be separated, because V5 was trained on another machine (FM-26).
- *Status.* measured. *M2.* G1 and X1 report the method's distribution over retrainings, not one model.

**FM-17 — The seven amplitude features suffice for the training patients but not for new ones.**
- *Observation.*
  - The seven absolute features alone (P8c) show no measurable difference from the full input on development:
    +0.013 [−0.091, +0.114] (`results/eureka_d37f/pc8/T_PC8.md` @ `839bc12`).
  - On the 11 unseen patients (3 validation + 8 test), P8c − R0 is −0.163 [−0.323, −0.043]
    (`results/eureka_d37f/pc8b/T_PC8B.md` @ `cc1010b`).
- *Measured* (same file).
  - Adding the connectivity row recovers the loss: P8d − P8c +0.150 [+0.058, +0.264], at P8d − R0 +7.2 [+2.2, +13.1]
    FP/day.
  - The relative band powers do not recover it: P8e − R0 −0.123 [−0.235, −0.020].
  - On Siena the connectivity result is not repeated: P8d − R0 −0.146 [−0.324, +0.007], descriptive.
- *Still open.* The gap was seen on the same 11 patients, so this explains a mechanism rather than confirming it
  independently.
- *Status.* hypothesis (independent confirmation pending). *M2.* T1 (§14 row 103), X1.

**FM-18 — The learned encoder adds no measurable gain on development.**
- *Measured.* The same chain on the 30-value node input, without the encoder (8b), gives development sensitivity
  −0.023 [−0.115, +0.092], F1 +0.088 [+0.020, +0.171] and FP/day −5.6 [−9.6, −1.5]. On test it reaches 0.448 against
  0.567, descriptive (`results/eureka_d32f/abl8b/aggregate/T2.md` @ `698e54d`).
- *Status.* measured. *M2.* G1.

**FM-19 — Detection depends on each patient's whole recording as the reference.**
- *Measured* (`results/eureka_d31f/abl/aggregate/T2.md` @ `2c0a7ca`). The table compares each reference with V5's own
  reference:

  | reference | development Δ sensitivity | test (descriptive) | Siena (descriptive) |
  |---|---|---|---|
  | training patients' clean windows (row 4a) | −0.079 [−0.158, +0.016] | 0.426 against 0.567 | 0.394 against 0.645 |
  | first 10 min of each file (row 4b) | −0.425 | — | — |
  | first 30 min of each file (row 4c) | −0.314 | — | — |

- *Still open.* The minimum recording length for a reliable per-recording reference has not been measured. This
  matters for an application that receives one EDF at a time.
- *Status.* measured (dependence); minimum length open. *M2.* L2 (minimum length as an option chosen on development).

**FM-20 — Siena differs from test through the false-alarm rate and the seizure mix.**
- *Observation.* Siena 0.633 ± 0.079 at 41.0 FP/day (`docs/PERF_PHASE_RECORD.md` @ `67ab0ba`). A fixed 0.5 % budget
  changes Siena sensitivity by −0.227 [−0.364, −0.102] (`results/eureka_d31f/abl/aggregate/T2.md`, row 6a).
- *Measured* (seed 42, pooled; `results/v9_final/siena_gap/SUMMARY.md` @ `a1c28ab`). Reweighting test's per-bin
  detection rates to Siena's mix explains a share of the test-to-Siena gap of:
  - 1.087 [−2.290, 4.787] by the amplitude-ratio mix;
  - 0.376 [−1.880, 3.534] by the duration mix.
- *Still open.* The intervals are too wide to attribute the difference.
- *Status.* hypothesis. *M2.* X1, L2.

### Label use and evaluation integrity

**FM-22 — The z-score statistics excluded annotated seizure windows.**
- *Measured.* With label-free statistics, development sensitivity changes by +0.006 [+0.000, +0.015] and test by
  −0.032 [−0.055, −0.009]. Of the test change, −0.008 [−0.018, +0.000] is the numerical rebuild difference
  (`results/eureka_d31f/9a/aggregate/T9A.md` @ `0071a14`).
- *Status.* measured; disclosed. *M2.* L2, L3 (fully label-free protocol).

**FM-23 — The per-patient budget of the final system was chosen after looks at the test set.**
- *Observation.* The final system is "look #7 (TEST-INFORMED, record 9.2)" (`results/e23_test_look7/SUMMARY.md`
  @ `c266efd`).
  - Held-out system: 0.498 ± 0.010 at 23.8 FP/day.
  - Final system: 0.567 ± 0.019 at 28.7.
  - Final − held-out: +0.070 [0.000, 0.201] (`docs/PROJECT_INSTRUCTIONS.md` @ `937b6b5`).
- *Status.* measured; disclosed. *M2.* L2 (budget rule chosen on development only), L3.

**FM-24 — CHB-MIT has no untouched confirmatory set left.**
- *Observation.* The 8 test patients entered several decisions (FM-23) and every ablation was also scored on them
  descriptively. A new confirmatory claim needs data not used for any choice (`docs/FUTURE_RESEARCH_PLAN.md`
  @ `254d8fc`, §15.2 "Locked evaluation").
- *Status.* open. *M2.* X1 (SzCORE open benchmark, including a private expert-annotated set), T1 (TUSZ evaluation split).

**FM-25 — The review application scores lower than V5 on the same patients; the cause is not recorded.**
- *Observation.* The application run on the 8 test patients gives subject-mean sensitivity 0.528, precision 0.108 and
  26.92 FP/day (`results/application_eval_v4/SUMMARY.md` @ `9f64036`), against V5's 0.567 at 28.7.
- *Still open.* (a) File vs patient as the scoring unit. (b) Statistics or reference computed differently. (c) Seed
  and budget. L1 records which.
- *Status.* open. *M2.* L1.

### Reproducibility across machines

**FM-26 — Kaggle machine types train with different arithmetic under the same library versions.**
- *Measured.* One machine type failed the reproduction gate (G-pc7rep DIFF; slower CPU, 7.87–8.12 ms per step against
  5.14–5.74). Seed groups of the two machine types did not differ; the smallest permutation p is 0.098, on Siena FP/day
  (`results/eureka_d34f/pc7/platform.md` @ `0211e7c`).
- *Still open.* Whether a fixed container removes the difference.
- *Status.* measured. *M2.* X1 (container, one image for every run).

**FM-27 — ASR output is not bit-reproducible across computers in about one file in six.**
- *Measured.*
  - A relative input change of 9.095e-13 moves ASR's output beyond 1e-9 in 12 of 70 files (`results/fa15/perturb/SUMMARY.md`
    @ `3bf99f9`).
  - The laptop reproduces the record exactly where Kaggle differs (`results/fa15/diag_laptop/SUMMARY.md` @ `2d4580a`).
- *Status.* measured (platform arithmetic amplified by ASR's discontinuous steps). *M2.* N2: any ASR-based component
  needs a reproducibility gate.

**FM-28 — Rebuilding features from the raw EDF moves numbers at the third decimal.**
- *Measured.*
  - Siena from the rebuilt external features: V0 0.645 ± 0.092 at 40.6 FP/day (`results/eureka_d31f/abl/aggregate/T2.md`),
    against the record's 0.633 ± 0.079 at 41.0.
  - Test rebuild difference: −0.008 [−0.018, +0.000] (`results/eureka_d31f/9a/aggregate/T9A.md`).
- *Status.* measured. *M2.* L3 and X1 state the rebuild tolerance with every number.

**FM-29 — Pool workers ran an older module than the notebook embedded.**
- *Measured (fixed).* When the pinned clone held an older copy of a module, Kaggle pool workers loaded that copy.
  The rule now: every embedded file equals the repository file at the pinned commit, and a gate checks the sha of
  the modules each worker ran (`docs/FUTURE_RESEARCH_PLAN.md` @ `254d8fc`, §12 row 15/11 16:00; §0).
- *M2.* — (standard of every notebook).

**FM-30 — The model-comparison seizure table has 185 rows per model, but 186 seizures are counted.**
- *Observation.* `results/model_cmp/seizures.csv` holds 185 rows per model while `summary.csv` / `ANALYSIS.md`
  count 186 (`docs/FUTURE_RESEARCH_PLAN.md` @ `254d8fc`, §14 row 29). The between–within table on the same cases
  also uses 185 (`results/r2/r1_system/rp/rp4/bw/SUMMARY.md`, set r2_24cases).
- *Still open.* A merge or split by the scorer, or a dropped row. Not checked.
- *Status.* open. *M2.* unassigned: a read-only check; the author decides whether and where.

---

## Part C · Research Question Ledger

Each entry lists: the observation; why it matters; a hypothesis and an alternative; evidence for and against
(internal sources by FM-ID, literature by title and DOI or link); the smallest experiment that would decide it; and
the decision. **The decision (pursue / hold / reject) is the author's and is left blank.** "Pursue" means it enters a
Track F chat; "hold" means it waits; "reject" means it is closed with its reason.

**RQ-01 — Do V5's false alarms belong to recognisable non-seizure event classes?**
- *Observation.* FM-05, FM-07, FM-11.
- *Why it matters.* If a detector trained on annotated artifacts separates false-alarm events from seizure events,
  artifact context can down-rank alarms without removing signal. If not, the artifact branch is closed early.
- *Hypothesis.* A share of V5's false alarms is muscle, electrode or eye-movement artifact recognisable by a detector
  trained on TUAR.
- *Alternative.* Most false alarms are the patient's normal high-amplitude physiology or non-epileptiform
  abnormalities, which no artifact class covers.
- *For.*
  - Artifact detection reduced false alarms in a wearable seizure detector: Ingolfsson et al. (2024), *Minimizing
    artifact-induced false-alarms for seizure detection in wearable EEG devices with gradient-boosted tree
    classifiers*, Sci Rep 14, 2980, DOI 10.1038/s41598-024-52551-0.
  - Artifacts are a known false-alarm source: Baumgartner & Koren (2018), *Seizure detection using scalp-EEG*,
    Epilepsia 59(S1), 14–22, DOI 10.1111/epi.14052.
  - Corpus: Hamid et al. (2020), *The Temple University Artifact Corpus: An annotated corpus of EEG artifacts*, IEEE
    SPMB, https://par.nsf.gov/biblio/10199675.
- *Against.*
  - Handcrafted artifact signatures did not separate V5's events (EV, FM-07).
  - False positives concentrated in non-epileptiform abnormalities, not artifacts: Saab et al. (2024), *Towards
    trustworthy seizure onset detection using workflow notes*, npj Digit Med 7, 42, DOI 10.1038/s41746-024-01008-9.
- *Smallest experiment.* N1. Train the detector on TUAR, apply it to V5's development events, and compute the AUROC of
  artifact probability for false-alarm events against seizure events, with a go / no-go rule written before the run.
- *Decision.* ______

**RQ-02 — Why do false-alarm increases always come as fragmentation, and does temporal integration fix it without losing short seizures?**
- *Observation.* FM-09, FM-08.
- *Why it matters.* One mechanism behind every false-alarm increase would give one lever for every variant.
- *Hypothesis.* Fragmentation follows from the score's window-to-window variance. Integrating the latent over
  neighbouring windows lowers it.
- *Alternative.* Fragmentation follows from weaker inputs producing more local maxima, which integration cannot
  repair.
- *For.* The GAE's lag-1 autocorrelation is lower (FM-08). O7 (3-window latent) gives −6.9 FP/day at no measurable
  sensitivity change on development (FM-04).
- *Against.* O7 lowers test sensitivity to 0.521 (descriptive, `results/eureka_d32f/opt/aggregate/T2.md`), and short
  seizures already fail (FM-03). No peer-reviewed study on fragmentation as a false-alarm mechanism was found. SzCORE's
  90-s merge rule acts on the same quantity: Dan et al. (2024), *SzCORE*, arXiv 2402.13005,
  DOI 10.48550/arXiv.2402.13005 (framework, not a mechanism test).
- *Smallest experiment.* No run: from the committed per-arm event tables, the association between the score's lag-1
  variance and events per hour across arms. Then O7-type integration as an option of L2, chosen on development.
- *Decision.* ______

**RQ-03 — Can a fully label-free per-recording protocol match V5?**
- *Observation.* FM-22, FM-23, FM-06, FM-19, FM-25.
- *Why it matters.* A system that receives one EDF needs every statistic, reference and budget estimated from that
  recording, without labels or test looks. It is also what an independent benchmark accepts.
- *Hypothesis.* Such a protocol loses little (the label-free statistics cost −0.032 on test).
- *Alternative.* The losses add up: label-free statistics, a development-only budget rule and the reference length
  together cost more than each alone.
- *For.* FM-22 (−0.032), FM-19 (a whole-recording reference works).
- *Against.* The first 10 / 30 minutes as reference lose −0.425 / −0.314 (FM-19). The fixed budget hurts Siena (FM-20).
  Label-free calibration in EEG: test-time adaptation is reported mostly for BCI decoding, e.g. Wimpff et al. (2024),
  *Calibration-free online test-time adaptation for electroencephalography motor imagery decoding*, arXiv 2311.18520
  (preprint). No peer-reviewed seizure-detection study of per-recording label-free calibration was found.
- *Smallest experiment.* L2 (design written before, options chosen on the 15 development patients), then L3 scored
  once on test, chb24 and Siena.
- *Decision.* ______

**RQ-04 — Does the development-to-test gap persist on data nobody in this project has seen?**
- *Observation.* FM-15, FM-16, FM-20, FM-24.
- *Why it matters.* CHB-MIT can no longer confirm anything (FM-24). The method's real performance is needed before
  a method is chosen for the next system.
- *Hypothesis.* Performance on independent data lies near the retrained recipe's test level (about 0.52), not V5's.
- *Alternative.* Independent data differ through recording conditions, so performance falls further.
- *For.* PC7 (FM-16). The generalisation gap is large across submitted algorithms: Dan et al. (2026), *Quantifying the
  generalization gap in seizure detection: a large-scale empirical benchmark via the SzCORE challenge*, PMLR 306,
  https://proceedings.mlr.press/v306/dan26a.html.
- *Against.* Siena, the only external set, scored higher than test (FM-20).
- *Smallest experiment.* X1: the L3 protocol in a container, submitted to the SzCORE open benchmark.
- *Decision.* ______

**RQ-05 — Is the learned GAE latent worth its cost against simpler cores?**
- *Observation.* FM-08, FM-18, FM-17.
- *Why it matters.* The core decision for the next system. The old core stays as benchmark.
- *Hypothesis.* Inside a label-free protocol on independent data, a simpler core (MLP-AE, K-means or no encoder)
  matches the GAE's sensitivity with fewer false alarms.
- *Alternative.* The GAE's higher unseen-patient sensitivity (8b: 0.567 against 0.448 on test, descriptive) holds on
  independent data.
- *For.* FM-08 (K-means and MLP-AE fewer false alarms in 6 of 6 partitions). Simple detectors are often competitive
  in unsupervised anomaly detection: Bouman, Bukhsh & Heskes (2024), *Unsupervised anomaly detection algorithms on
  real-world data: how many do we need?*, JMLR 25, https://jmlr.org/papers/v25/23-0570.html.
- *Against.* FM-17 (graph-derived connectivity row helps unseen CHB-MIT patients). The 8b test difference is
  −0.119 [−0.402, +0.095] (descriptive; `results/eureka_d32f/abl8b/aggregate/bootstrap.csv` @ `698e54d` (csv)).
- *Smallest experiment.* G1: the candidates retrained inside the L protocol, decision criterion written before, all
  submitted side by side in X1.
- *Decision.* ______

**RQ-06 — Are missed seizures a seizure-type phenomenon?**
- *Observation.* FM-01, FM-03.
- *Why it matters.* If misses are concentrated in a seizure type (focal, short, extratemporal), the remedy is
  type-specific features. If not, it is the score.
- *Hypothesis.* Misses concentrate in focal seizures with low amplitude and short duration.
- *Alternative.* Misses are a patient effect (two test patients hold 17 of the 18 short test seizures, FM-03).
- *For.* Short, low-amplitude, circumscribed focal patterns are generally hard to detect (Baumgartner & Koren 2018,
  DOI 10.1111/epi.14052).
- *Against.* CHB-MIT gives no seizure types, so this cannot be tested on the current data.
- *Smallest experiment.* T1: TUSZ evaluation split with seizure types, failure analysis by type and age; V1 (c) lists
  the CHB-MIT seizures still missed at 5 % / 10 % review.
- *Decision.* ______

**RQ-07 — How many seizures does the reader see for a given share of the recording reviewed?**
- *Observation.* FM-04.
- *Why it matters.* Sensitivity at one operating point does not describe the value of triage. Review share is the
  reader's cost.
- *Hypothesis.* A modest review share (5–10 %) puts most seizures in front of the reader.
- *Alternative.* The missed seizures of FM-01 / FM-02 stay missed up to large review shares.
- *For.* Commercial detection with sampled review: Reus, Visser & Cox (2020), *Using sampled visual EEG review in
  combination with automated detection software at the EMU*, Seizure 80, 96–99, DOI 10.1016/j.seizure.2020.06.002.
- *Against.* Automated detection below technician performance: Reus et al. (2022), *Automated seizure detection in an
  EMU setting: are software packages ready for implementation?*, Seizure 96, 13–17, DOI 10.1016/j.seizure.2022.01.009.
  Review-time reference: Koren et al. (2018), Front Neurol 9, 454, DOI 10.3389/fneur.2018.00454.
- *Smallest experiment.* V1 (inference only on the V5 checkpoints).
- *Decision.* ______

**RQ-08 — Which offset does an expert accept: the annotation or the score's return to background?**
- *Observation.* FM-13.
- *Why it matters.* An offset rule (F5b) needs a reference. Fitting the annotation may fit a convention, not the EEG.
- *Hypothesis.* Experts place the end of the clinically relevant change after the annotated offset, within the
  post-ictal elevation.
- *Alternative.* Experts agree with the annotation, and the localizer's late offset is an error to correct.
- *For.* Post-ictal δ slowing is a known EEG state: So & Blume (2010), *The postictal EEG*, Epilepsy Behav 19(2),
  121–126, DOI 10.1016/j.yebeh.2010.06.033.
- *Against / caution.* Expert agreement on seizure boundaries is moderate: Halford et al. (2015), *Inter-rater
  agreement on identification of electrographic seizures and periodic discharges in ICU EEG recordings*, Clin
  Neurophysiol 126(9), 1661–1669, DOI 10.1016/j.clinph.2014.11.008.
- *Smallest experiment.* An H1 protocol item: blinded expert marking of the end on a sample of seizures with both
  candidate ends shown. F5b only after that.
- *Decision.* ______

**RQ-09 — Does the connectivity row's benefit on unseen patients hold on independent data?**
- *Observation.* FM-17.
- *Why it matters.* It is the only evidence that graph-derived information helps generalisation, and it was seen on
  the same patients that raised the question.
- *Hypothesis.* The connectivity row (AEC part, FM-17 with PC6) restores sensitivity on new patients in general.
- *Alternative.* It is specific to the 11 CHB-MIT patients. Siena already does not repeat it.
- *For.* PC8b on the 11 unseen patients (FM-17). AEC alone carries the graph's contribution (PC6: AEC-only − R0
  development −0.030 [−0.087, +0.026]; `results/eureka_d37f/pc6/T_PC6.md` @ `4baf6e1`).
- *Against.* Siena (FM-17). wPLI estimates on short windows are noisy: Vinck et al. (2011), *An improved index of
  phase-synchronization for electrophysiological data in the presence of volume-conduction, noise and sample-size
  bias*, NeuroImage 55(4), 1548–1565, DOI 10.1016/j.neuroimage.2011.01.055.
- *Smallest experiment.* T1 confirmation on a TUSZ split fixed before use (§14 row 103), or P8d / R0 side by side in X1.
- *Decision.* ______

**RQ-10 — Does a fixed container make results reproducible across machines, and how large is the platform effect?**
- *Observation.* FM-26, FM-27, FM-28, FM-29.
- *Why it matters.* An independent benchmark and a clinical product both require that the same input gives the same
  output.
- *Hypothesis.* One container image removes the inference differences. Training differences remain but are smaller
  than the seed variance.
- *Alternative.* Floating-point differences persist inside a container across CPU types (as in FM-26, under identical
  library versions).
- *For.* Variance from implementation-level nondeterminism is a known, measurable component: Pham et al. (2020),
  *Problems and opportunities in training deep learning software systems: an analysis of variance*, ASE '20,
  DOI 10.1145/3324884.3416545.
- *Against.* FM-26 occurred with identical library versions. Reporting standard: Kapoor et al. (2024), *REFORMS:
  Consensus-based recommendations for machine-learning-based science*, Sci Adv, DOI 10.1126/sciadv.adk3452.
- *Smallest experiment.* Part of X1: run the container on two machine types on the same EDF files and compare outputs
  (no new training).
- *Decision.* ______

**RQ-11 — Can channel-level anomaly be turned into localisation?**
- *Observation.* FM-14.
- *Why it matters.* A localisation claim would add clinical value. The current ranking does not support one.
- *Hypothesis.* A dedicated attribution method with clinician-marked channels on more patients beats the anatomical
  prior.
- *Alternative.* Per-channel latent anomaly reflects amplitude (FM-02), not the onset zone.
- *For.* None measured.
- *Against.* L2 test of `results/attribution_v8/SUMMARY.md` (−0.1914 against the prior). Parked in §14.22 row 113.
- *Smallest experiment.* None proposed in M2.
- *Decision.* ______

---

## Change log

| date | chat | change |
|---|---|---|
| 23/11/2026 | F2-01 | file created: 29 failure rows (FM-01 … FM-30, FM-21 unused), 11 research questions; no run, no new number |
