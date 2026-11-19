# Table T — past ablations and design comparisons, collated with their conditions (D31-F, Step 0, 19/11/2026)

*Read-only collation from the repository at `a136a3b` (no run, no new number). Every value is copied from the source named
in its row; nothing is recomputed. Purpose: one table that tells C1 / C2 / C6 which component has already been tested,
on which data and with which metric, and tells D31-F which ablations of `EUREKA_PLAN.md` §10 already exist in some form.*

## How to read the columns

| column | meaning |
|---|---|
| **set** | `dev15` = the 15 development patients (12 training + 3 validation); `val3` = the 3 validation patients only; `test8` = the 8 test patients; `CV24` = 4-fold patient-wise cross-validation over the 24 CHB-MIT cases (each case scored by the fold that held it out); `ext` = chb24 and / or Siena (14) |
| **agg.** | `micro` = counts pooled over patients (the design criterion of V5, Section 2.7.1); `macro` = per-patient mean (SzCORE's aggregate, every V5 result) |
| **OP** | operating point: `≤25` = the best detector cell at ≤ 25 FP/day on dev15 (cell re-selected per arm; the P2 rule); `own` = each arm's own label-free point (budget with its own k); `V5` = the final chain (L2f budget, k = 4.0677, CPD); `0.5 %` = fixed budget |
| **model** | `V1` = the locked Phase-B GAE (3,285 parameters, node input 23); `v2` = the GAE of V5 (3,964 parameters, node input 30, "clean" training windows). **The V5 checkpoints are the v2 clean seeds 42, 1, 2, 3** (`data/models_v2/`, `docs/PROVENANCE_V2.md`), the same models used by E14–E21 and P3 |
| **seeds** | number of trained models averaged (seed 42 alone = 1) |
| **stage** | `det` = detector boundaries (before the localizer); `cpd` = after the kernel CPD localizer |
| **status** | what was decided at the time; "char." = characterisation only, not gated |

Earlier-protocol rows (Phase B / C, "offline" timeline rebuilt from annotations) are kept apart in Part H: their numbers
are not comparable with any continuous-timeline row and are never reused (`EUREKA_PLAN.md` Appendix D.4).

---

## A. Input and representation

| # | component / question | variant → reference | set | agg. | OP | model, seeds | stage | result | status | source |
|---|---|---|---|---|---|---|---|---|---|---|
| A1 | the 7 absolute node features (amplitude-preserving) | V1 (node input 23, no absolute features) → v2 (+7 absolute features) | dev15 | micro | ≤25 (top 2 %, smoothing 15) | V1 1 / v2 2 | det | 0.330 @ 23.7 → **0.489 @ 19.8** (+0.159); val 7/15 → 11/15 | v2 adopted (rule C) | `results/e8_gae_v2/SUMMARY.md`; record §2 E8 |
| A2 | same, on test | V1 → v2, same frozen chain | test8 | micro | top 2 % | 1 / 1 (4 seeds for v2: 0.043) | det | 2/76 → 3/76; window macro AUROC 0.640 → 0.680 | window gain transferred, event gain not (look #5) | `results/e9_test_oneshot/`; record §2 E9 |
| A3 | training windows: clean vs all (flagged windows included) | v2 all → v2 clean | dev15 | micro | ≤25 | 2 / 2 | det | 0.468 vs **0.489** | clean kept | `results/e8_gae_v2/SUMMARY.md` |
| A4 | reconstruction branch trained on flagged windows | recon (all) vs recon (clean), 12 training patients | dev (12) | window AUROC | — | 2 | — | seizure-vs-flagged ΔAUROC median −0.007 (positive 4 / 12) | no support (proxy, not patient fine-tuning) | `results/e13_recon_seen_artifacts/`; record §6.1 E13 |
| A5 | patient-specific fine-tuning of the GAE (no labels) | S9-adapted (2,000 steps) → S9 base | dev15 | micro | ≤25 | 2 | det | 0.628 @ 24.5 vs 0.622 @ 24.6 (+0.006; G1 needs +0.05) | not selected (one configuration) | `results/e15_patient_adaptation/`; record §6.1 E15 |
| A6 | same, test-time adaptation, 4 seeds | E15 TTA → E16e | dev15 | micro | ≤25 (fine grid) | 4 | det | 0.617 (G1 fail) | negative in this configuration | `results/e21_fine_grid/SUMMARY.md` |
| A7 | **message passing at inference (no edges)** — the closest existing form of **8a** | I-self (GAE with all edges removed) → GAE | CV24 × 6 partitions | macro | own | 1 per partition (seed = partition) | cpd | GAE FP/day −2.0 [−4.3, +0.3]; ≈ ¼ of the GAE − MLP-AE gap (35 % [14, 52] at the fixed 0.5 % point); sensitivity −0.015 [−0.076, +0.039] | V5 Section 4.3.5 | `results/fa14_v2/aggregate/`; `TRACKS_PROGRESS.md` "[F-A1.4]" |
| A8 | time-stable graph at inference | I-fix (one graph per patient) → GAE | CV24 × 6 | macro | own | 1 per partition | cpd | −0.4 [−2.5, +1.9] FP/day | edge instability not the source | same |
| A9 | edge sparsification | fixed weight threshold → strongest 20 % | **test8** (measured after the choice) | per patient | — | — | — | seizure–background connectivity distance larger in 8 / 8 patients (+48 % to +196 %) | top 20 % kept (V5 Table 5) | V5 Table 5 |
| A10 | ASR in preprocessing (signal level, no retraining) | after ASR → before | test8 + chb24, 70 seizure files | per seizure (median) | — | — (model-free) | — | seizure power removed 54.2 % vs high-amplitude non-seizure 41.2 %; seizure contrast 2.09 → 1.41 | ASR not used; effect on detection with retraining not measured (F-A1.5 paused) | `results/v9_x6/SUMMARY.md`; V5 4.3.4 |
| A11 | artifact model trained on the 5-SD flags | E4 → — | dev15 | window | — | — | — | 81.5 % of seizure windows called artifact | fail (design error) | `results/e4_artifact_rejection/`; record §2 |

## B. Normal reference and readout (score)

| # | component / question | variant → reference | set | agg. | OP | model, seeds | stage | result | status | source |
|---|---|---|---|---|---|---|---|---|---|---|
| B1 | normal defined across patients (feature GMM) — **V5 Table 6, column A** | cross-patient GMM (clean vs all non-ictal; 8 vs 32 components) | dev15 | micro | ≤25 | — (no GAE) | det | **0.340** (vs 0.372); capacity no effect | fail | `results/e1_normal_definition/`; V5 Table 6 |
| B2 | normal = the patient's own recording (feature density) | per-patient density → cross-patient | dev15 | micro | ≤25 | — | det | 0.340 → **0.596** (V5 Table 6 C on features) | mechanism established | `results/e5_patient_density/` |
| B3 | per-patient density on V1 GAE outputs | E6 | dev15 | micro | ≤25 | V1, 1 | det | V1 + D1 0.479 (subset); density fail | V1 lacks the information | `results/e6_gae_patient_density/` |
| B4 | **reference = first minutes / short baselines of each file** (V5 Table 6, column B) | 10 min (a) / 30 min (c) / causal sliding 30 min (d) → whole recording (S9 base) | dev15 | micro | ≤25 | 4 | det | a **0.191**, c **0.295**, d **0.487** vs **0.612** | none adopted; longer baseline monotonically better | `results/e16_recording_baseline/SUMMARY_a.md`, `_bcd.md` |
| B5 | readout: graph-level latent L vs the earlier 3-readout ensemble E | L → E (recon + latent + gamma) | dev15 | micro / macro | ≤25 | 2 | det | 0.553 @ 23.8 vs 0.489 @ 19.8; macro 0.676 vs 0.651 | not adopted (G1 +0.064 < +0.10) | `results/e12_readout_composition/` |
| B6 | readout: **per-channel latent Mahalanobis, order statistics** (before drift correction) | S9 / S12 / mean / S6 / S3 / max, each alone | dev15 | micro | ≤25 | 2 | det | S9 **0.622** @ 24.6; S12 0.617; mean 0.601; S6 0.543; S3 0.537; max 0.457; macro S9 0.747 vs E 0.651 | S9 = best candidate (mechanism check failed) | `results/e14_spatial_recruitment/`; record §6.1 E14 |
| B7 | readout per channel vs readouts across levels (rank ensembles) | Ea C+recon+gamma / **Eb C+L+gamma** / Ec C+L → C (S9 base) | dev15 | micro | ≤25 | 4 | det | Ea 0.535, **Eb 0.617**, Ec 0.572 vs C 0.612 | Eb chosen then superseded | `results/e17_rank_ensemble/` |
| B8 | gamma-coupling score in the ensemble (judge 2's question) | C(E16e) + L + gamma → C (E16e) | dev15 | micro | ≤25 (fine) | 4 | det | Eb 0.636 vs C 0.681 (inferior, floor 0.661) | removed | `results/e21_fine_grid/SUMMARY.md` (stage 2) |
| B9 | gamma with its own drift correction | C + L + gamma_dt → C | dev15 | micro | ≤25 (fine) | 4 | det | 0.609 @ 17.0 vs 0.681 @ 24.3; macro 0.768 vs 0.821 | inferior | `results/e21b_gamma_detrend/` |
| B10 | **spatial members of the final ensemble** — closest existing form of **3a / 3c** | each member alone (E16e-corrected) → E17b (6/9/12/mean) | dev15 | micro | ≤25 (fine) | 4 | det | S9e (= C) **0.681 @ 24.25**, S6e 0.665, S12e 0.686, Smean_e 0.686 (char.) vs **E17b 0.668 @ 19.98**; macro C 0.821 @ 24.1 vs E17b 0.828 @ 19.5; val 0.900 vs 0.983; short 1.5 vs 2.0 / 3 | E17b adopted by non-inferiority (deliberate) | `results/e17b_latent_family/`; record §6.1 E17b |
| B11 | focal member (3rd largest) added | members 3/6/9/12/mean → 6/9/12/mean, own k | dev15 / test8 / ext | micro | V5-like (own k 3.971) | 1 (seed 42) | cpd | dev 0.681 @ 23.4 vs 0.681 @ 23.5; paired Δ at 27.5 FP/day dev −0.004 [−0.015, +0.004], test −0.030 [−0.065, 0.000] | not adopted | `results/v9_x1/SUMMARY.md` (Part A) |
| B12 | focal members on test (anatomy, test-informed T-B) | S1e / S3e vs frozen | test8 | seizures with p_need ≤ 0.5 % | — | 4 | — | S3e rescues 1.5, loses 5.25; S1e 19.25 vs frozen 25.75 | H6 not supported | record §9.6 |
| B13 | trimmed covariance fit (5 %) | refit without the 5 % most distant windows | dev15 | seizures rescued / lost | — | 4 | — | rescues 0.25, loses 2.0 | not triggered (§14 row 15) | record §9.6 |
| B14 | **non-graph scores on the same chain** (V9-E1; scorer swapped, chain fixed) | B1 features + Mahalanobis / B2 adjacency + Mahalanobis / B3 features + IF / B4 features + kNN / F = rank-mean(G, B4) → G (GAE latent) | dev15 | micro (macro) | V5 chain, G's k | 1 (B) / 4 (G, F) | cpd | G 0.681 @ 23.5; B4 0.989 @ 58.1 (k not refitted); with own k (E1b): **B4 0.745 @ 15.9, F 0.713 @ 19.3** (macro G 0.847, B4 0.866, F 0.899) | not in V5; kNN numbers provisional (±60 s exclusion ignored the file id, plan §14 row 8) | `results/v9_e1/`, `results/v9_e1b/` |
| B15 | same in CV | kNN-LOO / GAE+kNN-CV → GAE-CV | CV24 | micro / macro | own | 1 | cpd | kNN 0.624 @ 18.1 (macro 0.763), fusion 0.651 @ 22.9 (0.791); fusion − GAE macro +0.056 [+0.001, +0.134] | not in V5 (provisional, as B14) | `results/v9_x3/SUMMARY.md` |
| B16 | **seven models, same windows and chain** (V5 Table 12) | MLP-AE (no message passing), IF, K-means, SVM, trees, 1D CNN → GAE | CV24 | macro | own | 1 (seed 42) | cpd | GAE 0.735 / F1 0.203 / 28.4; MLP-AE 0.711 / 0.273 / 20.2; IF 0.680 / 0.212 / 24.1; K-means 0.768 / 0.248 / 20.7; SVM 0.626 / 0.163 / 33.7; trees 0.755 / 0.221 / 35.2; CNN 0.777 / 0.218 / 35.1 | reported as is (V5 3.4) | `results/model_cmp/`, `results/fa16/` |
| B17 | stability over 6 partitions | MLP-AE, K-means → GAE | CV24 × 6 | macro | own | 1 per partition | cpd | MLP-AE ΔF1 +0.075 [+0.034, +0.121], 6 / 6; K-means ΔF1 +0.038 [+0.008, +0.073], 6 / 6 | stable advantage of both over the GAE | `results/f1_repcv/`, `results/fa16/repl/` |

## C. Drift correction

| # | component / question | variant → reference | set | agg. | OP | model, seeds | stage | result | status | source |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | **drift correction off vs level only** — closest existing form of **2a** | S9 base (no correction) → E16e (minus ±15-min running median) | dev15 | micro | ≤25 (fine) | 4 | det | **0.612 → 0.681** (≤15: 0.513 → 0.614); macro 0.742 → 0.821; every seed up | E16e adopted (V5 Section 4.2) | `results/e21_fine_grid/SUMMARY.md`; `results/e16_recording_baseline/SUMMARY_ef.md` |
| C2 | **level + spread** (per-file median / MAD) — closest form of **2b** | E16b → S9 base / E16e | dev15 | micro | ≤25 / fine | 4 | det | 0.582 @ 22.5 (coarse), 0.596 (fine) vs 0.681; seizure z 4.62 (level) → 4.08 (level + spread) | not adopted | `results/e16_recording_baseline/SUMMARY_bcd.md`, `_ef.md`; V5 2.4.3 |
| C3 | file median instead of running median | E16f → S9 base | dev15 | micro | ≤25 | 4 | det | 0.559 | not adopted | `SUMMARY_ef.md` |
| C4 | correction of the final scalar instead of the members | E16g dt / h → Eb | dev15 | micro | ≤25 | 4 | det | dt 0.529; h 0.598 @ 15.2 | not adopted | `results/e16g_final_detrend/` |
| C5 | correction removed, final ensemble, test (T-B anatomy) | without → with ±15-min correction | test8 / dev15 | seizures with p_need ≤ 0.5 % | — | 4 | — | test 13.0 vs 25.75; dev 47.25 vs 60.5 | H8 not supported (correction helps) | record §9.6 |
| C6 | drift diagnostics | — | dev15 | — | — | 4 | — | 84.5 % of top-2 % non-ictal windows in the top-quartile files; 8.3 % of those files contain a seizure; flagged share 0.459 = 0.459 | mechanism (V5 2.4.3) | `SUMMARY_bcd.md`, `SUMMARY_ef.md` |

## D. Detection: budget, smoothing, short-seizure branch, veto

| # | component / question | variant → reference | set | agg. | OP | model, seeds | stage | result | status | source |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 | **fixed budget 0.5 % vs per-patient budget** — **6a** on test | held-out (0.5 % for all) → final (L2f) | test8 | macro (and micro) | 0.5 % / V5 | 4 | cpd | **0.498 ± 0.010 @ 23.8 → 0.567 ± 0.019 @ 28.7**; gain = chb15 only; Δ macro +0.070 [0.000, +0.201], ΔFP/day +4.9 [+0.6, +12.0] | both reported (V5 Table 9) | `results/e22_test_oneshot/`, `results/e23_test_look7/`, `results/a1_final_bootstrap/` |
| D2 | same on development | frozen detector (0.5 %) → L2 / **L2f** | dev15 | micro (macro) | budget | 4 | det | 0.668 @ 20.0 → L2 0.657 @ 20.5 → **L2f 0.678 @ 23.8** (macro 0.842); on the frozen detector's own curve | L2f adopted (no measured gain on dev) | `results/p3_levers/`, `results/p3c_freeze/` |
| D3 | uniform 2 % budget | top 2 % for all → L2f | dev15 | micro | — | 4 | det | 0.803 @ **95.1** FP/day | unaffordable (V5 4.2) | `results/p3b_diag/SUMMARY.md` (D1b) |
| D4 | **smoothing length** — closest existing form of **5a** | 1 / 2 / 3 / 5 / 9 windows (best cell ≤ 25 FP/day) | dev15 | micro | ≤25 (fixed top-p grid) | 4 | det | **0.519 / 0.535 / 0.500 / 0.668 / 0.697** (@ 16.3 / 11.2 / 8.6 / 20.0 / 19.9) | 5 kept (dev and test disagree, rule 19) | `results/p3b_diag/SUMMARY.md` (D1b) |
| D5 | smoothing vs seizure rank, final scalar (**premise of D1**) | p_need by smoothing 1 / 2 / 3 / 5 / 9 | test8 / dev15 | seizures with p_need ≤ 0.5 % | — | 4 | — | test 22.75 / 20.25 / 22.0 / 25.75 / 18.25 of 76; dev 61.75 / 61.25 / 62.25 / 60.5 / 58.5 of 93; chb15 median p_need 0.0234 (s1) vs 0.0191 (s5) | H9 not supported | `results/p3b_diag/SUMMARY.md` (D1a) |
| D6 | short-seizure visibility vs smoothing (earlier score) | e = share of equal-length non-ictal spans above the seizure peak, k = 1 … 15 | test8 / val3 | median e per class | — | V1-era score | — | test short (≤ 4 windows) 0.37–0.54 for every k; val long 0.04–0.08 | descriptive | `results/oracle_gate_bound/summary.md` (Part B) |
| D7 | short-seizure branch (union with a 3-window detector) | E19 (on Eb) / **E19b** (on C) → main only | dev15 | micro | ≤25, cap 25 | 4 | det | E19 +0.011 (adopted, superseded); E19b +0.000 (not adopted); short-seizure peaks at the 0.81–0.995 percentile | short seizures reported descriptively | `results/e19_short_branch/`; record §6.1 |
| D8 | multi-scale max score S1 = max(smooth 5, smooth 2) | S1 → G | dev15 / test8 / ext | micro (macro) | V5 chain | 4 | cpd | dev 0.681 @ 28.5 vs 0.681 @ 23.5; test 0.408 @ 34.9; dev paired Δ CI lower bound −0.089 | not adopted (rule) | `results/v9_e3/SUMMARY.md` |
| D9 | event veto by duration (feature f5), no budget refill | veto → none | dev15 / test8 / ext | micro | V5 chain | 4 | cpd | f5 dev AUROC 0.78–0.80 (test + Siena 0.63–0.66); fewer detections and fewer false alarms (S1 + veto dev 0.649 @ 18.9) | a trade, not a gain | `results/v9_e2/`, `results/v9_e3/` |
| D10 | veto screen on test (look #4, V1 era) | veto → none | test8 | micro | — | V1 | — | 6 / 76, FP/day 19.2 → 17.9 | did not transfer | `results/veto_screen*`; record §3 |
| D11 | oracle removal of flagged non-ictal windows | flagged windows removed (labels) → all | val3 / test8 | events / span exceedance | — | V1 | — | val FP 633 → 68 (11 / 15 kept); test exceedance 20–50 % → 0.1–1 % | upper bound, not a method | `results/diag_detector_ceiling/`, `results/oracle_gate_bound/` |

## E. Change points: detector vs localizer, offset rules

| # | component / question | variant → reference | set | agg. | OP | model, seeds | stage | result | status | source |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 | **change points as the detector** (PELT segmenter D2) — V5 Table 7 A | D2 → threshold detector D1 | dev15 | micro | ≤25 | V1-era score | det | **0.213 vs 0.479** | D1 kept | `results/e7_ensemble_cpd/SUMMARY.md`; V5 Table 7 |
| E2 | kernel CPD bump detector | K → D1 | dev15 | micro | ≤25 (grid ends at 5.8) | v2, 2 | det | 0.250 @ 5.8 vs 0.489 @ 19.8 (on D1's curve) | fail | `results/e10_kernel_cpd/` |
| E3 | **localizer vs detector boundaries vs run rules** — **7a / 7b** | CPD → detector / control 1 (unsmoothed above threshold) / control 2 (contiguous run) | dev15 | median \|error\| (s), matched pairs | ≤25 | 4 | cpd vs det | E17b: onset det 16 → CPD 8 (control 1: 8; control 2: 12); offset det 20 → CPD 16 (control 1: 40; control 2: **12**) | CPD adopted for onset; offset not better than control 2 | `results/e18_cpd_localizer/`; record §6.1 E18 diagnostics |
| E4 | same, V5 sets | localizer → detector boundaries | dev15 / test8 / ext | median \|error\| | V5 | 4 | — | test final onset 32 → 12 s, offset 20 → 24 s; run-rule offset 16 s (test), 20 s vs 28 s (Siena); development 16 / 24 → 4 / 16 s; chb24 12 / 8 → 4 / 4 s | V5 Table 10 | V5 Table 10; `results/e23_test_look7/` |
| E5 | hybrid localizer L6 (CPD onset + run-rule offset) | L6 → CPD | dev15 | micro + errors | L2f | 4 | cpd | onset 8 vs 4 s (hybrid worse on L2f); offset 12 vs 16 s | CPD kept (rule) | `results/p3c_freeze/`; record §9.7b |
| E6 | multivariate kernel CPD (18-channel trajectory) | E20a → E18 | dev15 | micro + errors | ≤25 | 4 | cpd | sensitivity 0.657 vs 0.662; onset 8 = 8 s; **offset 8 vs 16 s** | not adopted (sensitivity) | `results/e18_cpd_localizer/` (multi); record §6.1 E20a |
| E7 | detection loss from the localizer | after CPD → detector | test8 | seed 42 | V5 | 1 | — | 38 / 76 (det) → 37 / 76 (cpd) | V5 reports cpd | record §9.8 |

## F. Normalisation statistics (label use) — **9a**

| # | component / question | variant → reference | set | agg. | OP | model, seeds | stage | result | status | source |
|---|---|---|---|---|---|---|---|---|---|---|
| F1 | z-score statistics without labels (whole recording) | review application (label-free statistics) → final system (statistics without seizures + 4 h) | test8 | macro | V5 (seed 42 budget) | **1 (seed 42)** | cpd | **33 / 76, 0.528 @ 26.9** vs 37 / 76; one seizure fewer in chb03, chb06, chb15, chb16; FP 323 vs 318 | V5 3.6 (measured effect of label use) | V5 3.6; `results/application_eval_v4/SUMMARY.md` |
| F2 | same statistics, 5-SD flag robustness | record SD vs SD without clipped windows / MAD / IQR | all 38 cases | descriptive | — | — | — | top 1 % of sampled windows hold 4.6–37.5 % of the squared deviation; flag marks 28–60 % of non-ictal windows | postponed (plan §14 row 1) | `results/r2/r0_data/rb1c/` |

## G. Data and protocol (not component ablations; for the Q&A)

| # | question | comparison | set | agg. | result | source |
|---|---|---|---|---|---|---|
| G1 | five missing seizure-free files | complete data → earlier copy, models retrained (4 seeds) | test8 | macro | held-out 0.475 vs 0.498; final 0.575 vs 0.567; data alone moves sensitivity ≤ 0.016 | `results/r2/r1_system/run/aggregate/`; V5 2.1.1 |
| G2 | same for the CV comparison | rerun → record | CV24 | macro | MLP-AE − GAE F1 +0.076 [+0.036, +0.122] (record +0.070) | `results/r2/r2_cv/aggregate/` |
| G3 | development vs test difficulty | same GAE in CV | CV24 | macro | 8 test patients 0.581 vs other 16 cases 0.812 | V5 3.4 |
| G4 | supervised reference (labels of other patients) | HGB, leave-one-subject-out | dev15 | micro | 0.702 @ 20.5 | `results/e3_supervised_loso/` |

## H. Earlier protocol (Phase B / C, V1, offline timeline rebuilt from annotations) — not comparable, never reused

| # | lever | set | result (offline protocol) | source |
|---|---|---|---|---|
| H1 | semi-final report Table 4 (2 configurations, 3 validation patients / 13 seizures; "−0.103 F1 without the latent Mahalanobis score") | val3 | value only in the semi-final report on the laptop (`F:/Study/Thesis/Eureka/`); **not located in the repository**, not re-verified here | semi-final report (V1) |
| H2 | directed transfer-entropy branch (C4-lite), slope gate, ensemble reweighting, artifact (gradient) gate | val3, 4 seeds | none Pareto-improved rlg at the headline (e.g. TE −0.070 F1 at 3.6 FP/day; slope gate seed-42-specific) | `docs/RESULTS_OF_RECORD_phaseB.md` |

## I. A rhythm feature has been measured once (relevant to D2)

| # | question | set | result | source |
|---|---|---|---|---|
| I1 | rhythmicity = share of 0.5–60 Hz power within ±1.5 Hz of the spectral peak (per channel, 4 s window, median / max over channels), seizure vs flagged non-seizure windows | dev15 windows (labels only for scoring) | pooled AUROC: rhythmicity_max **0.473** (seizures < 20 s: 0.353), rhythmicity_med **0.495**; per validation patient 0.25–0.58 (max) | `results/raw_eeg_view/SUMMARY.md` Part 3 |
| I2 | for comparison, same table | dev15 | spatial spread `frac_ch_sd_gt3med` 0.756; relative theta 0.675 | same |

---

## What T shows for the Euréka suite (`EUREKA_PLAN.md` §10)

1. **Most of 1a–9a already exist in some form, on the same models.** The V5 checkpoints are the v2 seeds 42 / 1 / 2 / 3
   used in E14–E21 and P3. Members alone (3a / 3c ≈ B10), drift off and level + spread (2a / 2b ≈ C1, C2), smoothing (5a ≈
   D4), fixed budget (6a ≈ D1, D2), boundaries (7a / 7b ≈ E3–E5) and label-free statistics (9a ≈ F1, seed 42 only) were
   measured. **What does not exist:** the same variants scored through V5's final chain (per-patient budget with k
   recalibrated per variant, CPD) with **per-patient means, the 4-seed spread and paired patient-bootstrap intervals**, on
   development *and* descriptively on test, chb24 and Siena. The past rows are micro-averaged, at the detector stage, with
   the cell re-selected per arm — the conditions judge 1 criticised at the semi-final ("ablation on 3 patients", "no
   confidence interval").
2. **New in substance:** 1a / 1b (diagonal / Euclidean instead of Mahalanobis) — never tested; 4a (other-patient
   reference on the *latent*) — only on features (B1, 0.340) or as the graph-level readout of an earlier ensemble (B5);
   8a on the fixed split with the V5 checkpoints — only in the CV setting (A7); 9a with four seeds and on development.
3. **D1 premise:** the smoothing analysis on the final scalar exists (D5) but is not stratified by seizure duration; the
   duration-stratified exceedance exists only on the earlier V1 score (D6). Neither can say whether a 2 s hop adds
   information, because both vary smoothing in 4 s steps of non-overlapping windows.
4. **D2 premise:** one rhythm feature (spectral-peak share) did not separate seizure from flagged non-seizure windows on
   development (pooled AUROC 0.47–0.50, 0.35 for short seizures; I1). D2 must say what it adds to this negative
   (autocorrelation, per-patient reference, event level) before it can justify 3b.
