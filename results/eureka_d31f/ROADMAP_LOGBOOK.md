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
| **L2** missed seizures that are low in amplitude and short (chb06, chb13, chb16) | Sections 4.3.1, 4.3.2 | D1, EV, O1, O5, C2 |
| **L3** offsets not improved by the localizer | Table 10, Section 4.2 | E (7a, 7b), O2 |
| **L4** the graph adds no detection value (MLP-AE and K-means better) | Sections 3.4, 4.3.5 | E (8a), O3, C4 |
| **L5** CHB-MIT z-score statistics use labels | Sections 2.1.3, 3.6 | E9A |
| **L6** the per-patient budget is test-informed and its gain is chb15 only | Sections 2.7.2, 4.1 | E (6a) |
| **L7** small paediatric training data; no artifact labels | Section 4.5 | C3 (after 11/12, CNCL) |

## 2 · Roadmap

### Phase A — evidence and diagnostics (code tonight 19/11; runs 20/11)

| ID | type | question | where, cost | rule | status |
|---|---|---|---|---|---|
| **EUR_ABL** | E | contribution of each V5 component: 1a, 1b, 4a, 4b, 4c, 2a, 2b, 3a, 3m, 3c, 3g, 3r, 5a, 6a, 7a, 7b, 8a | laptop smoke 10–20 min → Kaggle account 1, 1.5–2.5 h (computed) | `STEP1_DESIGN.md` §2.3; a variant passing the R214 rule (e.g. 5a = 9 windows) is handed to Phase B | approved 19/11 20:35 |
| **EUR_9A** | E | V5 with label-free z-score statistics, 4 seeds, k recalibrated | Kaggle account 2, 4–5 h (computed) | paired difference with V0, no threshold | approved 19/11 20:35 |
| **D1** | D | can a finer time grid bring short seizures within the budget? (best of the +1, +2 and +3 s shifts = upper bound of a 2 s hop) | laptop, 20–40 min | ≥ 3 more short seizures (test8 + chb24 + Siena, 4-seed mean) within their patient's budget → O5 may run | approved 19/11 20:35 |
| **EV** (extends D2) | D | which properties of a flagged event tell a seizure from the patient's own non-seizure activity? Event level, measured relative to the patient's own background: **rhythm** (autocorrelation peak at 0.1–1 s, spectral-peak share), **evolution** (change of dominant frequency and amplitude within the event), **waveform** (line length, sharpness, Hjorth), **field** (number and contiguity of involved channels, single-channel dominance), **artifact signatures** (high-frequency share, frontopolar dominance, clipping, step jumps), duration | laptop, raw EDF of the V5 events and missed seizures; development for the decision, test descriptive; 30–60 min | a feature enters O1 only if its event AUROC (detected seizure vs false alarm, development) has a patient-cluster bootstrap lower bound ≥ 0.80 and points the same way in ≥ 10 of 15 patients | proposed (D2 was approved; EV adds the other feature groups) |

### Phase B — optimisations, selected on development (20/11 evening → 22/11)

| ID | limit | idea | basis | design (summary) | where, cost | rule |
|---|---|---|---|---|---|---|
| **O1** | L1, L2 | **event re-ranking with budget refill.** Candidate events are taken at a larger budget (e.g. 2×). Each is scored by the EV features that passed. Events are kept in that order until the patient's V5 budget is full again, so time freed from vetoed events goes to the next candidates | ACNS 2021 electrographic seizure definition (evolution; ≥ 10 s); V9-E2 showed that a veto *without* refill only trades detections for false alarms | rule-based score (no trained classifier); 1–2 thresholds by leave-one-patient-out on development | laptop (raw features of candidate events) + scoring in the container; about 1–2 h | R214, after EV |
| **O2** | L3 | **offset rule selected on development**: CPD, the run rule (7b), or multichannel CPD (E20a: offset 8 s on development) | V5 Section 4.5 future work | leave-one-patient-out choice on development; sensitivity must not drop | in `EUR_ABL` + container | R214 |
| **O3** | L1, L4 | **GAE + K-means rank fusion**: the mean of the two percentile scores, both label-free | outlier-ensemble theory (Aggarwal & Sathe 2015); K-means beat the GAE in 6 of 6 partitions (V5 3.4); GAE + kNN fusion beat the GAE in cross-validation (V9-X3, provisional) | K-means per patient and channel as F-A1.6; k recalibrated; evaluated as one arm | Kaggle account 3, about 1–1.5 h (K-means fits measured at 39 min for 24 cases) | R214; **the author decides the narrative** (the system then contains a non-graph member; the title stays true) |
| **O4** | L2 | smoothing 9 windows | P3-B on development: 0.697 vs 0.668 (micro) | from `EUR_ABL` 5a | — | R214 |
| **O5** | L2 | 2 s hop (overlapping windows) | Pale et al. 2023: a smaller step raises false alarms | only if D1 passes; features rebuilt at 2 s, model unchanged, k recalibrated | Kaggle, 2 accounts, about 3 h each (computed) | ablation only (development has 3 short seizures) |

### Phase C — not before the freeze (Q&A 11/12 or later; the author decides)

| ID | limit | experiment | cost | note |
|---|---|---|---|---|
| C1 | L2, L4 | retraining 10a / 10b (without the 7 absolute features / without gamma powers) | about 4.6 h per variant, 1 account each | can start after 22/11 for the Q&A |
| C2 | L2 | **rhythm and waveform features in the node input** (V5 Section 4.5) — only if EV shows a separating feature | feature rebuild + 4 trainings, about 10 h | after EV |
| C3 | L1, L7 | **artifact detector trained on an annotated artifact corpus** (TUH Artifact Corpus), marked time returned to the budget | needs data access (registration, not checked) and a training pipeline; days | after 11/12 (CNCL) |
| C4 | L4 | GAE retrained on a time-stable graph per patient (plan §14 row 37) | 4 trainings per partition | after 11/12 |
| C5 | — | F-A1.5 (ASR in the preprocessing, retrained) | 2 data notebooks + 1 training, about 18 h | after 11/12 |
| C6 | L1, L2 | 11a / 11b (wPLI only / AEC only) | graph rebuild + training, about 10 h | after 11/12 |

## 3 · Schedule and accounts

| day | Kaggle account 1 | account 2 | account 3 | account 4 | laptop (Claude Code) | this chat |
|---|---|---|---|---|---|---|
| 19/11 night | — | — | — | — | — | code, synthetic tests, aggregates, smoke prompt for `EUR_ABL` / `EUR_9A` / D1 / EV |
| 20/11 | `EUR_ABL` | `EUR_9A` | `EUR_OPT` (O3 K-means) | spare (rerun after a STOP) | smoke → D1 → EV | read the smoke; design O1 from EV |
| 21/11 | O-arms if needed | — | — | — | O1 features | read all; O1 / O2 / O3 / O4 selection on development; combination check |
| 22/11 | — | — | — | (C1 may start, for the Q&A) | — | the chosen arm scored once on test / chb24 / Siena; T2 table; hand-off to C1 / C2 before the freeze |

## 4 · Logbook

| date, time | entry |
|---|---|
| 19/11 (before 20:25) | Step 0: table T collated (`T_past_ablations.md`), read only. Approved by the author 20:25, with instructions: re-run past ablations on the current model; be selective; small check first; 4 Kaggle accounts; literature before every proposal |
| 19/11 (before 20:35) | Step 1 design (`STEP1_DESIGN.md`). Approved 20:35: `EUR_ABL` ∥ `EUR_9A`, D1 and D2 on the laptop, no retraining before the freeze |
| 19/11 (after 20:35) | Roadmap (this file) proposed: EV extends D2 to waveform, evolution, field and artifact signatures; Phase B optimisations O1–O5 under R214; Phase C after the freeze |
