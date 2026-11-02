> **SUSPENDED 02/11/2026 22:30 (board rev 40, R88–R90) — nothing in this plan was run.** After the meeting with anh
> Trí: kNN is dropped from the story (R88), combined scores are not used (R89), B0/B1/B3/B4 are suspended (R90). The
> parallel run is now `MODEL_COMPARISON_PLAN.md` (R93). Kept for the record; B2 (offset rule) and the graph insight
> analyses (board §4) are candidates after the rehearsal. Change log: §8.

# V10_PLAN — Track B: method fix after the method review (pre-registered 02/11/2026, chat D10-plan)

**Status:** design fixed by the author on 02/11 before any run. Change only with the author's explicit approval
(e.g. after the 21:00 meeting with anh Trí, 02/11) and log the change in §8 with date and reason.
Local: `F:/Study/Thesis/Code/docs/V10_PLAN.md` (repository) + project file.

---

## 0 · Why (one paragraph)

The thesis system scores each channel of each 4 s window by the **LedoitWolf Mahalanobis distance** of its 16-d GAE
latent to the patient's whole recording. Mahalanobis assumes **one Gaussian "normal" state per channel**. A long EEG has
many normal states (sleep, wake, movement, recurring high-amplitude bursts); a single Gaussian scores the rare-but-normal
states as anomalies — exactly the false alarms seen on real EEG (bursts of the patient's own high-amplitude activity).
A kNN distance measures **local** density: a state that recurs elsewhere in the recording has neighbours and scores low.
Author framing (02/11): **look for the weakness in protocol and method, not in the data.** kNN here is a **scoring
rule** (no training), so replacing the Mahalanobis step keeps the pipeline GAE → score → detector → CPD and the
registered title ("using Graph Autoencoder and Change Point Detection") stays correct.

## 1 · Evidence already in hand (computed 02/11 from committed files; `NUMBERS_LOCK_S18.md`)

| contrast (CHB-MIT test, detector stage, one global budget, per-patient sensitivity at per-patient 27.5 FP/day) | value |
|---|---|
| same 12 channel features, **Mahalanobis** vs **kNN** | **0.299 vs 0.588** |
| GAE latent + Mahalanobis (thesis) vs channel features + Mahalanobis | 0.504 vs 0.299 → the latent has value under the same scorer |
| connectivity only (adjacency + Mahalanobis) | 0.102 (weakest) |
| 24-case CV, each arm at its own label-free point (per-case mean): GAE 0.735 @ 28.4 FP/day · kNN 0.763 @ 17.7 · GAE + kNN 0.791 @ 22.7 | kNN ≈ 38 % fewer false alarms than GAE (computed) — **pending the B0 fix** |
| **never tested** | kNN on the GAE latent; Gaussian mixture; One-Class SVM; kNN without the time exclusion |

**How the kNN baseline was chosen (honest history).** After the reviewer asked "why GAE, did you compare other
models?", four label-free scorers were run on the identical chain and the same 12 channel features the GAE receives
(5 relative band powers + 7 absolute features): one Gaussian (Mahalanobis), tree ensemble (Isolation Forest), distance /
local density (kNN), and connectivity only. Supervised SVM / trees were not candidates (they need the patient's seizure
labels; a supervised reference already exists: gradient-boosted trees, leave one patient out, development 0.702 @ 20.5,
pooled, report 4.1). One-Class SVM, Gaussian mixture and LOF were never tested.

**cô's question "is it the features?" (02/11).** Partly. The features (amplitude-preserving ones) carry the signal —
connectivity alone is 0.102 — but **the scorer decides how much of it is used** (0.299 vs 0.588 on the same features).

## 2 · B0 — kNN implementation audit (code read 02/11) and fix

Files: `src/v9_e1_baselines.py` (`d_knn`, `load_raw12_18`, `file_start_offsets`), `src/v9_x3_knn_b4.py`,
`src/v9_e4_knn24.py`.

| check | finding |
|---|---|
| labels in scoring | none: per-patient per-channel robust z over all windows; random 20,000-window reference subsample (seed 42) ✔ |
| inputs | `F12 = bp5 + f7` of the same windows the GAE scores ✔ (scaling: per-patient robust z, vs the GAE's training mean/SD — both label-free) |
| **±60 s exclusion — FLAW** | `t_sec = (idx − file start) × 4 s` is the **offset inside the file**; `d_knn` compares it **without the file id** → it also drops reference windows of **every other file** at the same minute (≈ 3 % of the reference set per window). The intended same-file exclusion does work. Effect expected small, **unmeasured** |
| **calibration asymmetry** | 24-case comparison: kNN budget k calibrated **leave-one-case-out on 23 cases**; GAE k **per fold on 17–19 training cases** → kNN gets more calibration data |
| confound (B1 resolves) | kNN excludes the window's own ±60 s; Mahalanobis is fitted on all windows, including the seizure itself. The kNN gain may come from **locality** (many normal states) or from **the exclusion** |

**B0 procedure (Claude Code prompt `docs/prompts/V10_B0_KNN_FIX.md`):**
1. **Gate:** the unchanged code reproduces committed B4 rows on 2 cases (thesis split `results/v9_e1/`, 24 cases
   `results/v9_e4/` and `results/v9_x3/`). Mismatch → stop.
2. **Fix:** exclusion on **(file id, in-file time)**: a reference window is excluded only if it is in the **same file**
   and within ±60 s. Nothing else changes (k = 10 neighbours, 20,000 subsample, seed 42, robust z).
3. **Equalise calibration:** kNN budget k calibrated **per fold on the fold's training cases** (same rule as the GAE).
4. Rerun kNN (fixed) on the 24-case CV and the thesis split; per-patient mean sensitivity, precision, F1, FP/day at the
   own point; paired patient bootstrap vs the old kNN and vs GAE.
5. **Pre-registered reading:** "kNN ≥ GAE" survives if GAE − kNN F1 95 % CI upper bound < 0.

## 3 · B1 — scorer × representation study (pre-registered)

- **Representations:** **R1** = 12 channel features (as kNN uses) · **R2** = GAE 16-d latent (as the thesis uses).
- **Scorers** (label-free, per patient per channel; same-file ±60 s exclusion where it applies):
  S1 Mahalanobis (one Gaussian; current) · **S2 Gaussian mixture** (components by BIC over 1–8, per patient per channel;
  tests "many normal states") · S3 kNN (k = 10, as fixed in B0) · **S4 kNN without exclusion** (tests the exclusion) ·
  S5 Isolation Forest (tree family) · **S6 One-Class SVM** (RBF, ν = 0.01, γ = "scale", 20,000-window subsample; the
  label-free SVM — answers "why not SVM").
- **Frozen downstream:** members 6/9/12 + mean, ±15-min drift, percentile ensemble, smoothing 5, per-patient budget
  clip(q_i(k), 0.005, 0.02) with k calibrated per fold on training cases for every arm, merge 90 s, kernel CPD.
- **Sets:** 24-case patient-wise CV (committed `results/v9_x3/folds.json` and fold checkpoints, seed 42) = **primary**;
  thesis split (development calibration, test once); chb24; Siena only where caches exist — never estimated.
- **Metrics:** per-patient mean F1, sensitivity, precision, FP/day at each arm's own label-free point; per-patient
  sensitivity–FP curves; paired patient bootstrap (B = 10,000). **No single matched FP/day level** (board R74).
- **Hypotheses (fixed now):**
  - **H1** R2·S3 (GAE latent + kNN) − R2·S1 (current GAE): F1 CI lower bound > 0.
  - **H2** R2·S3 − R1·S3 (does the latent add value under a good scorer?): F1 CI lower bound > −0.03 (non-inferiority).
  - **H3** (mechanism) S2 − S1 on both representations: F1 CI lower bound > 0 → "many normal states" confirmed.
  - **H4** (exclusion) S3 − S4: reported, no threshold.
- **Decision rule:**
  - H1 & H2 → **R2·S3 becomes the main scoring** ("GAE latent + kNN scoring"); title unchanged.
  - H1 only → main = the best R1/R2 arm by the **development-only** rule (thesis-split development, ties → lower
    FP/day), stated honestly.
  - H1 fails → no change to the system; insight page uses the evidence of §1.
  - Every other cell is characterisation only — never selected on test.
- **Stop rules:** smoke runtime extrapolated > 10 h for the CV → run S1–S3 first and report; any gate mismatch → stop.
- **Demo:** unchanged (SzScan v1, thesis system) until the new system is final and verified; the app update is a
  separate, later Claude Code task.

## 4 · B2 — offset rule (container, any time)

Onset from CPD (12 s, final, 4 seeds), offset from the contiguous-run rule (16 s vs CPD 24 s). Recompute from saved
events (development, test 4 seeds, chb24, Siena where available); report median absolute errors; confirm detections and
false alarms are unchanged. Adopt for the next version if offset error is lower on development and test with counts
unchanged.

## 5 · B3 / B4 — only if the new defense date allows (designed and pre-registered later)

- **B3 features for low-amplitude seizures:** all three detectors miss seizures that barely rise above the patient's
  background (amplitude ratio 1.29× vs 2.29×) and are shorter (32 vs 68 s) → the feature set is power/amplitude-driven.
  Rhythm/morphology features (e.g. periodicity, spectral peak stability) designed after B1.
- **B4 GAE loss:** MSE(A) + 0.1·MSE(X) may tilt the latent towards connectivity (the weakest signal). Hypothesis only;
  retrain with a higher X weight (Kaggle, 3.5–5 h per fold) only if B1 shows the latent matters under a good scorer.

## 6 · Not weaknesses (do not re-open)

0.5–2 % budget (deliberate review-time bound) · members 6/9/12 (channel count does not separate after the budget) ·
smoothing 20 s (shorter adds noise peaks) · drift correction (0.612 → 0.681) · ASR / artifact veto / short-seizure branch
/ more training patients (all tested, negative with mechanism; `V9_RESULTS_SUMMARY.md` §5).

## 7 · Timeline (target: done before 05/11, the fallback defense date)

| when | step |
|---|---|
| 02/11 before 21:00 (container) | B0 prompt written; audit table (§2) ready for the meeting with anh Trí |
| 02/11 21:00 | meeting with anh Trí: audit + B1 design; his changes logged in §8 **before** anything runs |
| 02/11 night | B0 smoke + run on the laptop (overnight; laptop free) |
| 03/11 | B0 result → B1 prompt → smoke → run overnight 03→04/11 |
| 04/11 | B1 verification (numbers, per-subject table, paired bootstrap), decision rule, B2 → `TRACK_B_HANDBACK.md` |
| 04/11 | if adopted and verified: 1–2 slide texts + figure for Track A; otherwise an insight page |

If the defense stays on 05/11 and B1 is not verified by the slide submission, the slides keep the thesis system and say
"a kNN scoring test is under way" only if asked.

## 8 · Change log

- 02/11 (D10-plan): design fixed (B0, B1 H1–H4, B2; B3/B4 conditional).
- 02/11 22:30 (D10-plan): **plan suspended** (R88–R90), replaced for now by `MODEL_COMPARISON_PLAN.md`. Reason: meeting with
  anh Trí — kNN carries no meaning for the thesis; compare trained single models for a stated purpose. Results seen: none
  (nothing was run).
