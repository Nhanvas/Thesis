# D31-F roadmap and logbook — experiments for the Euréka final (started 19/11/2026)

*One file for the whole Euréka phase of Track F. Part 1 is the roadmap: which limit of V5 each experiment addresses, its
type, cost and decision rule. Part 2 is the logbook: one dated line per event (approval, run, result, decision). The
detailed designs are in `STEP1_DESIGN.md` and later design files. The full text of each decision goes to
`FUTURE_RESEARCH_PLAN.md` §12. Parked options go to §14.*

## 0 · Rules that frame every experiment

- **Types.** **E** = evidence (ablation of V5, for the report, slides and Q&A). **D** = diagnostic (tests the premise of
  an experiment before it is paid for). **O** = optimisation (may improve V5 or remove a limit).
- **"Best but correct" (R214).** An O-experiment can replace V5 only if:
  - it is selected on the 15 development patients by a rule written before its run;
  - its parameters are chosen by leave-one-patient-out on those patients (nested), never on test;
  - its test, chb24 and Siena rows are read only after that choice.

  If several O-experiments pass, their combination must pass the same rule once more (as for the P3 levers).
- **Unsupervised claim.** An O-experiment may not train on seizure labels. Rules from the literature (e.g. the ACNS
  criteria) with one or two thresholds chosen on development have the same status as k and the budget limits in V5.
  A classifier trained on seizure labels would turn the system into a supervised one, so it is excluded (it is the
  supervised comparison models of V5 Section 3.4).
- **Number freeze: evening of 22/11.** Whatever finishes later goes to the Q&A of 11/12.
- **Where it runs.** Quick checks on the laptop (Claude Code from a committed script). Long runs on Kaggle, one notebook
  per account, 4 accounts in parallel. Hospital data never leave the laptop.
- **Honest prior.** The development patients over-predict the test patients. Seizure peaks are exceeded by about 4 % of
  equally long non-seizure stretches on validation, against 20–50 % on test (record §3). Earlier gains chosen on
  development often did not transfer (E9; the per-patient budget L2). Expected gains on test are therefore modest. Every
  O-result is reported with its test row, whatever it is.

## 1 · Limits of V5 (measured) and the experiments that address them

| limit | evidence in V5 | experiments |
|---|---|---|
| **L1** false alarms from the patient's own high-amplitude non-seizure activity (precision ≈ 0.1) | Sections 4.3.1, 4.3.3; Figure 18 | EV, O1, O3 |
| **L2** missed seizures that are low in amplitude and short (chb06, chb13, chb16) | Sections 4.3.1, 4.3.2 | D1, EV, O1, O5, PC2 |
| **L3** offsets not improved by the localizer | Table 10, Section 4.2 | E (7a, 7b), O2 |
| **L4** the graph adds no detection value (MLP-AE and K-means better) | Sections 3.4, 4.3.5 | E (8a), O3, PC4 |
| **L5** CHB-MIT z-score statistics use labels | Sections 2.1.3, 3.6 | E9A |
| **L6** the per-patient budget is test-informed and its gain is chb15 only | Sections 2.7.2, 4.1 | E (6a) |
| **L7** small paediatric training data; no artifact labels | Section 4.5 | PC3 (after 11/12, CNCL) |

## 2 · Roadmap

### Phase A — evidence and diagnostics (code tonight 19/11; runs 20/11)

| ID | type | question | where, cost | rule | status |
|---|---|---|---|---|---|
| **EUR_ABL** | E | contribution of each V5 component: 1a, 1b, 4a, 4b, 4c, 2a, 2b, 3a, 3m, 3c, 3g, 3r, 5a, 6a, 7a, 7b, 8a | laptop smoke 10–20 min → Kaggle account 1, 1.5–2.5 h (computed) | `STEP1_DESIGN.md` §2.3; a variant passing the R214 rule (e.g. 5a = 9 windows) is handed to Phase B | approved 19/11 20:35 |
| **EUR_9A** | E | V5 with label-free z-score statistics, 4 seeds, k recalibrated | Kaggle account 2, 4–5 h (computed) | paired difference with V0, no threshold | approved 19/11 20:35 |
| **D1** | D | can a finer time grid bring short seizures within the budget? (best of the +1, +2 and +3 s shifts = upper bound of a 2 s hop) | laptop, 20–40 min | ≥ 3 more short seizures (test8 + chb24 + Siena, 4-seed mean) within their patient's budget → O5 may run | approved 19/11 20:35 |
| **EV** (extends D2) | D | which properties of a flagged event tell a seizure from the patient's own non-seizure activity? Event level, measured relative to the patient's own background: **rhythm** (autocorrelation peak at 0.1–1 s, spectral-peak share), **evolution** (change of dominant frequency and amplitude within the event), **waveform** (line length, sharpness, Hjorth), **field** (number and contiguity of involved channels, single-channel dominance), **artifact signatures** (high-frequency share, frontopolar dominance, clipping, step jumps), duration | laptop, raw EDF of the V5 events and missed seizures; development for the decision, test descriptive; 30–60 min | a feature enters O1 only if its event AUROC (detected seizure vs false alarm, development) has a patient-cluster bootstrap lower bound ≥ 0.80 and points the same way in ≥ 10 of 15 patients | proposed (D2 was approved; EV adds the other feature groups) |

*Status 20/11 09:30:* EUR_ABL **done** (Kaggle account 1, measured 0.868 h; no R214 candidate); EUR_9A **done** (account 2, measured 3.2 h); D1 and EV run in one Kaggle notebook `EUR_DIAG` (moved from the laptop, logbook 19/11 22:20): first run stopped at G-s0, corrected, **rerun 20/11**.

### Phase B — optimisations, selected on development (20/11 evening → 22/11)

| ID | limit | idea | basis | design (summary) | where, cost | rule |
|---|---|---|---|---|---|---|
| **O1** | L1, L2 | **event re-ranking with budget refill.** Candidate events are taken at a larger budget (e.g. 2×). Each is scored by the EV features that passed. Events are kept in that order until the patient's V5 budget is full again, so time freed from vetoed events goes to the next candidates | ACNS 2021 electrographic seizure definition (evolution; ≥ 10 s); V9-E2 showed that a veto *without* refill only trades detections for false alarms | rule-based score (no trained classifier); 1–2 thresholds by leave-one-patient-out on development | laptop (raw features of candidate events) + scoring in the container; about 1–2 h | R214, after EV |
| **O2** | L3 | **offset rule selected on development**: CPD, the run rule (7b), or multichannel CPD (E20a: offset 8 s on development) | V5 Section 4.5 future work | leave-one-patient-out choice on development; sensitivity must not drop | in `EUR_ABL` + container | R214 |
| **O3** | L1, L4 | **GAE + K-means rank fusion**: the mean of the two percentile scores, both label-free | outlier-ensemble theory (Aggarwal & Sathe 2015); K-means beat the GAE in 6 of 6 partitions (V5 3.4); GAE + kNN fusion beat the GAE in cross-validation (V9-X3, provisional) | K-means per patient and channel as F-A1.6; k recalibrated; evaluated as one arm | Kaggle account 3, about 1–1.5 h (K-means fits measured at 39 min for 24 cases) | R214; **the author decides the narrative** (the system then contains a non-graph member; the title stays true) |
| **O4** | L2 | smoothing 9 windows | P3-B on development: 0.697 vs 0.668 (micro) | from `EUR_ABL` 5a | — | R214 |
| **O5** | L2 | 2 s hop (overlapping windows) | Pale et al. 2023: a smaller step raises false alarms | only if D1 passes; features rebuilt at 2 s, model unchanged, k recalibrated | Kaggle, 2 accounts, about 3 h each (computed) | ablation only (development has 3 short seizures) |

### Phase C — not before the freeze (Q&A 11/12 or later; the author decides)

*Items renamed PC1–PC6 on 20/11 (their earlier names C1–C6 collided with Track C's chats C1 report and C2 slides).*

| ID | limit | experiment | cost | note |
|---|---|---|---|---|
| PC1 | L2, L4 | retraining 10a / 10b (without the 7 absolute features / without gamma powers) | about 4.6 h per variant, 1 account each | can start after 22/11 for the Q&A |
| PC2 | L2 | **rhythm and waveform features in the node input** (V5 Section 4.5) — only if EV shows a separating feature | feature rebuild + 4 trainings, about 10 h | after EV |
| PC3 | L1, L7 | **artifact detector trained on an annotated artifact corpus** (TUH Artifact Corpus), marked time returned to the budget | needs data access (registration, not checked) and a training pipeline; days | after 11/12 (CNCL) |
| PC4 | L4 | GAE retrained on a time-stable graph per patient (plan §14 row 37) | 4 trainings per partition | after 11/12 |
| PC5 | — | F-A1.5 (ASR in the preprocessing, retrained) | 2 data notebooks + 1 training, about 18 h | after 11/12 |
| PC6 | L1, L2 | 11a / 11b (wPLI only / AEC only) | graph rebuild + training, about 10 h | after 11/12 |

## 3 · Schedule and accounts

| day | Kaggle account 1 | account 2 | account 3 | account 4 | laptop (Claude Code) | this chat |
|---|---|---|---|---|---|---|
| 19/11 night | — | — | — | — | — | code, synthetic tests, aggregates, smoke prompt for `EUR_ABL` / `EUR_9A` / D1 / EV |
| 19/11 21:20 → 20/11 08:00 (ran) | `EUR_ABL` (0.87 h), then `EUR_DIAG` (stopped at G-s0) | `EUR_9A` (3.2 h) | — | — | — | code, tests, readings of EUR_ABL and EUR_9A |
| 20/11 (from 08:46) | `EUR_DIAG` rerun | free | `EUR_OPT` (O3) once designed and approved (D32-F) | spare | — | project update; then chat D32-F: read EUR_DIAG, design O1 / O2 / O3 |
| 21/11 | O-arms if needed | — | — | — | O1 features | read all; O1 / O2 / O3 / O4 selection on development; combination check |
| 22/11 | — | — | — | (PC1 may start, for the Q&A) | — | the chosen arm scored once on test / chb24 / Siena; hand-off to Track C's chats C1 (report) and C2 (slides) before the freeze |

## 4 · Logbook

| date, time | entry |
|---|---|
| 19/11 (before 20:25) | Step 0: table T collated (`T_past_ablations.md`), read only. Approved by the author 20:25, with instructions: re-run past ablations on the current model; be selective; small check first; 4 Kaggle accounts; literature before every proposal |
| 19/11 (before 20:35) | Step 1 design (`STEP1_DESIGN.md`). Approved 20:35: `EUR_ABL` ∥ `EUR_9A`, D1 and D2 on the laptop, no retraining before the freeze |
| 19/11 (after 20:35) | Roadmap (this file) proposed: EV extends D2 to waveform, evolution, field and artifact signatures; Phase B optimisations O1–O5 under R214; Phase C after the freeze |
| 19/11 20:39 | Roadmap approved by the author |
| 19/11 21:10 | `EUR_ABL` implemented and tested on synthetic data (every gate and the three STOP paths); plan §12 row 19/11 21:10; delivered D31F1, pushed `1acd7e2`; started on Kaggle account 1 at 21:20 |
| 19/11 22:05 | `EUR_9A` implemented (`src/eur_9a.py`, aggregate `src/eur_9a_aggregate.py`, synthetic test, notebook). Two choices against the design text, before any output: (a) the label-free statistics come from the record function `preprocessing.compute_subject_stats` with an empty seizure map (the only change to V5), not from `x1_external.labelfree_stats` (same rule, other code); (b) the numerical rebuild difference is read from the committed `r13/cf_krec` rows (21 cases with an unchanged file set) instead of a second rebuild. Runtime corrected from 4–5 h to 3–4 h (computed from R0's measured rates: statistics 13.7 s and features 22–24 s per hour of EEG per worker; chb04 is the longest job, about 1.6 h). Synthetic test ALL PASS (1,092 s) incl. a seizure-free case whose label-free statistics equal the record's exactly |
| 19/11 22:16 | `EUR_ABL` output pushed (`71c63bf`), measured 0.868 h on 4 CPU (the 1.5–2.5 h estimate was high). Every gate PASS (smoke and full: R1.0-dev / -test exact, GE 240 rows within tolerance, G-k, G-kv0, G-D0, G-x0, G-eng, G-enc, G-worker). Aggregate A0 / A1 PASS; table `abl/aggregate/T2.md`. R214 candidates: none (5a9 raises development F1 by +0.065 [+0.040, +0.091] but its sensitivity difference is −0.008, so by the rule written before the run it stays an ablation; its test sensitivity, descriptive, is 0.451 against 0.567). O4 closed by the rule |
| 19/11 22:20 | D1 and EV moved from the laptop to one Kaggle notebook `EUR_DIAG` (account 1, free): both need every patient's full V5 quantities (features, latents, distances) and the raw EDF of 38 patients, incl. chb24 and Siena, whose features exist only as the Kaggle dataset; the laptop is in daily use. Same design and rules; raw EDF verified against PhysioNet in the session |
| 19/11 23:05 | `EUR_DIAG` implemented (`src/eur_diag.py`, synthetic test, notebook). Gates: G-raw, G-data, R1.0 / GE / G-k, G-ev (V5 events reproduce the r10 rows), G-s0 (shift-0 windows rebuilt from the raw EDF reproduce the stored smoothed scalar within 0.02; compared away from the segment edges, where the segment's smoothing is truncated), G-extstats (external statistics = those R0.4 used), G-worker |
| 20/11 08:30 | `EUR_9A` output pushed (`01a1f8c`), measured 3.2 h (projection 2.63 h). Every gate PASS (G-raw 664 EDF, G-stats0 exact, G-feat0, R1.0, G-k, PROJ, G-struct 23/23, G-worker). Aggregate A0 / A1 PASS, `9a/aggregate/T9A.md`. k label-free 4.0978 (record 4.0677). Own operating point after the localizer: development 0.838 vs 0.832 (+0.006 [0.000, +0.015]), FP/day 22.7 vs 23.2; **test 0.536 vs 0.567 (−0.032 [−0.055, −0.009]; 34.0 vs 36.25 of 76 seizures), F1 0.175 vs 0.180 (−0.005 [−0.021, +0.010]), FP/day 27.9 vs 28.7**; the numerical rebuild difference alone (committed `cf_krec`, 21 cases) is −0.008 [−0.018, 0.000] on test. Test drop from chb03, chb06, chb14, chb16 (two of them partly rebuild) |
| 20/11 08:30 | `EUR_DIAG` stopped at G-s0 (output `eedc1db`): every other gate PASS (G-raw 727 EDF, R1.0, GE, G-k, G-ev 92/92), but the shift-0 rebuild differed from the stored smoothed scalar by up to 0.033 (tolerance 0.02). Pattern: > 0 only in the six CHB-MIT cases with short seizures (chb02, 06, 12, 14, 16, 21), ≤ 5e-5 in the external cases, whose features were built on Kaggle with the same library stack. Hypothesis: the documented rebuild difference of the CHB-MIT features (R0 G-feat: 0.03–0.05 % of adjacency entries differ in every case), not the scoring path (exact on synthetic data and on stored inputs). G-s0 was redefined to test this directly (stored inputs through the path = stored scalar; bit-identical rebuilt features = stored scalar; the rest reported with the number of differing windows and decisions); D1 compares shifts with the rebuilt shift 0. Outputs are now written before the gates. The tolerance was set without accounting for R0's documented difference — my error |
| 20/11 09:10 | The stricter G-s0 found a second, smaller cause on synthetic data: new windows were scored with `einsum` while the stored distances come from `LedoitWolf.mahalanobis`; the last-digit differences reorder near-ties, which moves a percentile by 1/n (≈ 1e-5 on real data: the external cases' 5e-5). Fixed: new windows are scored with the patient's fitted LedoitWolf objects. Synthetic test ALL PASS with the path exact (0.0) and every decision equal. The CHB-MIT 0.03 cannot come from this (1e-5 scale); the rerun tells whether it is the feature rebuild |
| 20/11 09:30 | Project update before chat D32-F (author 08:38 / 08:46): audit in `TRACK_F_HANDBACK.md` Part 25; `TRACKS_PROGRESS.md` row "Hand-off to C (Euréka)"; plan §0, §0a, §14.14; Phase C items renamed PC1–PC6 |
