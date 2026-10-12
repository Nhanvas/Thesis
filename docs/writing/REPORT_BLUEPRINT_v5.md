# Report blueprint v5 — section tree, exhibits, budget

**Role:** the plan for Step C. It applies the handoff's add/remove table and adds what a reader of the
final system needs (marked **NEW**). For exhibit numbers and caption titles this file supersedes
`EXHIBIT_SET_v5.md`; data sources and drawing specs stay in `EXHIBIT_SET_v5.md`.
Rules: `AUTHOR_REQUIREMENTS.md` (AR), `REVIEWER_RULES.md` (R), `RUBRIC_MAP.md`, `SAMPLE_PATTERNS.md`.

## 0 · Decisions for the author (approve or change before Step C)

| D | Proposal | Why |
|---|---|---|
| D1 | AR 2: research framework at the end of Ch1, pipeline figure at the head of Ch2 after the data section | Both samples; the sentence in the list is incomplete |
| D2 | **NEW** Section 1.2.3 "Threshold calibration and baseline drift" | The registration form names these as the literature focus, and the final system answers both (per-patient alarm budget, per-file drift correction); v4 has no section on them |
| D3 | **NEW** Table 1 "Current approaches and research gaps" closing Section 1.2 (qualitative: approach, label use, output, evaluation, gap) | Rubric criterion 1 (15 pts) asks for a comparison table first; Table 16 in Ch4 stays numeric |
| D4 | Keep a component-contribution table (Table 9) in Results, framed as an ablation of the final system on training and validation patients | Rubric criterion 6 rewards ablations; it is a result of the final method, not process history (AR 21) |
| D5 | **NEW** Section 4.3 "Designs that did not improve detection": one compact section, 4–5 tried designs, each with its mechanism | AR 21 puts tried-and-failed designs in Discussion; it shows where the limits are |
| D6 | Deployment matrix criteria: patient data protection (societal), cost to the hospital (economic), hardware and energy (environmental), processing time for review (technical), maintenance and scaling (global) | AR 18 resolution: decision-driving criteria that still satisfy rubric criterion 4 |
| D7 | Borrowed figure candidate: "Event-based scoring [n]" from the SzCORE paper in 2.8.1 | Event-level scoring is the least familiar idea for the committee; verify the figure exists in the PDF first, otherwise drop |

## 1 · Budget (body ≤ 50 pages; target ≤ 48)

| Chapter | v4 words | v5 target words | v4 pages | v5 target pages |
|---|---|---|---|---|
| 1 Introduction | 2,448 | 2,100 | 9 | 8 |
| 2 Methodology | 3,657 | 3,700 | 15 | 15 |
| 3 Results | 2,945 | 2,000 | 15 | 12 |
| 4 Discussion | 2,305 | 2,600 | 8 | 10 |
| 5 Conclusion | 646 | 450 | 2 | 1 |
| **Body** | **12,001** | **10,850** | **49** | **46** |

v4 counts are prose only (tables and equations excluded). Pages are measured by building the document in Step D.

## 2 · Section tree and content

### Chapter 1 Introduction
- **1.1.1 Epilepsy and the burden of EEG review** — keep, trim; economic/social burden lives here (samples).
- **1.1.2 Seizures in scalp EEG** — explain EEG, montage, ictal pattern, onset and offset for non-experts (AR 11). Fig 1.
- **1.2 Analysis of current solutions** — five categories, each ending on what it leaves unsolved:
  1.2.1 Supervised and patient-specific detection · 1.2.2 Unsupervised and graph-based anomaly detection
  (channel-level explanation in two sentences at its end) · **1.2.3 Threshold calibration and baseline drift
  (NEW, D2)** · 1.2.4 Onset and offset localization · 1.2.5 Evaluation on continuous recordings.
  Closing paragraph = the gap as a synthesis; Table 1 (D3).
- **1.3 Proposed solution** — the system in one paragraph; 3–4 contributions, each answered later by a Ch3 result (AR 8, R1); Table 2 design requirements as constraints (no old app numbers).
- **1.4 Project goals** — Goals 1–2 verbatim from the registration form, with one qualifying sentence for "spatial-temporal features"; Goal 3 channel-level explanation; Goal 4 review application.
- **1.5 Timeline** — Table 3 (actual timeline).
- **1.6 Research framework** — Fig 2; last sentence maps the stages to Chapters 2–4. *(v4 1.7 removed, AR 7.)*

### Chapter 2 Methodology
- **2.1 Data** — 2.1.1 CHB-MIT and patient split (Fig 3, Table 4 with chb24/Siena line; chb01 = chb21 same person, both in training, R7) · 2.1.2 External data: chb24 and Siena (origin, licence, montage mapping, 256 Hz resampling, 50 Hz notch, R5, R27) · 2.1.3 Preprocessing (filters, 4 s windows, per-subject z-score with the label-use disclosure; Fig 4).
- **2.2 Pipeline overview** — Fig 5; what is trained once on training patients vs fitted label-free per patient.
- **2.3 Graph construction** — 2.3.1 Connectivity graphs (CAR, wPLI, AEC, top-k 20 %; Fig 6; R3, R4) · 2.3.2 Node features (30 = adjacency row 18 + band powers 5 + 7 amplitude-preserving; why amplitude matters) · 2.3.3 Decision matrix for edge sparsification (Table 5).
- **2.4 Graph autoencoder** — architecture, loss, training on interictal windows of the training patients, parameter count, 4 seeds.
- **2.5 Ensemble anomaly score (Objective 1)** — 2.5.1 Channel-level latent anomaly (Ledoit–Wolf Mahalanobis distance, robust z; plain explanation) · 2.5.2 Baseline drift correction (±15-min running median per file; Fig 7) · 2.5.3 Ensemble score (order statistics 6/9/12 + mean → patient percentiles → equal mean).
- **2.6 Detection and localization (Objective 2)** — 2.6.1 Decision matrix for detection and localization (Table 6; change-point detection as detector in one sentence) · 2.6.2 Per-patient alarm budget (smoothing, budget, merge) · 2.6.3 Kernel change point localization · Table 7 settings (what is fitted where).
- **2.7 Channel-level explanation** — per-event channel ranking from the latent anomaly; blind every-channel annotation; the three tests in plain words. The v4 synthetic-injection validation is dropped unless the final-system attribution includes it (not in the numbers pack).
- **2.8 Evaluation** — 2.8.1 Event-based scoring (SzCORE: tolerances, merge/split, sensitivity, precision, F1, FP/day, onset/offset error; pooled and subject-mean; Fig 8, D7) · 2.8.2 Held-out and final evaluations (seeds, patient bootstrap, disclosure that the last design choice used test information; one paragraph on why the earlier offline protocol overestimated).
- **2.9 Review application** — 2.9.1 Decision matrix for deployment (Table 8, D6) · 2.9.2 Architecture and label-free operation (local, label-free recomputation, guards, non-causal per-patient fitting by design; Fig 9 pending the rebuild).

### Chapter 3 Results (mirrors Chapter 2; no interpretation)
- **3.1 Connectivity graphs** — Fig 10.
- **3.2 Ensemble anomaly score (Objective 1)** — Table 9 (D4).
- **3.3 Detection and localization on the test patients (Objective 2)** — Table 10 (held-out evaluation and final system side by side: seed 42, 4-seed mean ± SD, bootstrap interval, pooled and subject-mean, TP/FN/FP counts); Table 11 per patient; Fig 11 (chb03); Table 12 onset and offset error. One operating point only (the frozen budget).
- **3.4 External validation** — Table 13 (chb24, Siena, DynaSD benchmark row on the same Siena data).
- **3.5 Channel-level explanation** — Table 14 (both readouts; the anatomical-prior test failed).
- **3.6 Review application** — pending the rebuild (Fig 12, Table 15). *(v4 3.6 objectives section removed, AR 4.)*

### Chapter 4 Discussion (one section per finding)
- **4.1 Detection performance in context** — Table 16, Fig 13; DynaSD on the same Siena data; Ali et al. 2024 with its protocol note; protocol rows that exclude patients or tune per patient only beside the full result; the drop from non-test to test; the gap between held-out and final results and where it comes from.
- **4.2 Where the system fails** — chb06, chb13, chb16; Fig 14; short seizures (state which count: by annotation or by whole windows); file-level drift.
- **4.3 Designs that did not improve detection (NEW, D5)** — e.g. cross-patient normal model, per-patient fine-tuning, change-point detection as the detector, reconstruction-based readouts; one mechanism each; the localizer roughly halves the onset error, while on offset a simple contiguous-run rule is as good.
- **4.4 Channel-level explanation** — the negative for both readouts; concordance is not localization.
- **4.5 Limitations and future work** — supervised component, TUH artifacts, prospective use.
- **4.6 Economic, social and global impacts** — rubric criterion 7, right before Ch5.

### Chapter 5 Conclusion (≤ 1 page, no new numbers or citations)
Restate the problem → Objective 1 and Objective 2 each with its headline number → main limitation → secondary contributions (external validation, channel-level negative, application) → future work and significance.

### Front matter
Abstract ≤ 300 words (eight moves, headline numbers per the headline rule) · keywords ≤ 10 words · acknowledgements (unchanged) · list of abbreviations (remove terms no longer used, e.g. PELT, MSE).

## 3 · Exhibits (short titles, AR 22)

| No. | Sec | Title | vs EXHIBIT_SET_v5 | Status |
|---|---|---|---|---|
| Fig 1 | 1.1.2 | Connectivity in background and seizure windows | F1 | unchanged |
| Fig 2 | 1.6 | Research framework | F2 | redraw |
| Fig 3 | 2.1.1 | Bipolar montage | F3 | unchanged |
| Fig 4 | 2.1.3 | EEG before and after preprocessing | F4 | unchanged |
| Fig 5 | 2.2 | Processing pipeline | F6 (moved up) | redraw |
| Fig 6 | 2.3.1 | Connectivity graph construction | F5 | unchanged |
| Fig 7 | 2.5.2 | Baseline drift correction | F7 | export needed |
| Fig 8 | 2.8.1 | Event-based scoring [n] | **NEW (D7)** | borrowed, verify |
| Fig 9 | 2.9.2 | Review application architecture | F8 | after rebuild |
| Fig 10 | 3.1 | Separation by sparsification rule | F9 | unchanged |
| Fig 11 | 3.3 | Detection and localization on one recording | F10 | export needed |
| Fig 12 | 3.6 | Review application screens | F11 | after rebuild |
| Fig 13 | 4.1 | Sensitivity versus false alarms | F12 | redraw |
| Fig 14 | 4.2 | Patient time above the seizure peak | F13 | committed |
| Table 1 | 1.2 | Current approaches and research gaps | **NEW (D3)** | write |
| Table 2 | 1.3 | Design requirements | T1 | edit |
| Table 3 | 1.5 | Thesis timeline | T2 | edit |
| Table 4 | 2.1.1 | Patient split | T3 | +1 line |
| Table 5 | 2.3.3 | Decision matrix for edge sparsification | T4 | unchanged |
| Table 6 | 2.6.1 | Decision matrix for detection and localization | T5 | edit |
| Table 7 | 2.6 | Settings of the final system | T7 | committed |
| Table 8 | 2.9.1 | Decision matrix for deployment | T6 | **criteria revised (D6)** |
| Table 9 | 3.2 | Contribution of each component | T8 | committed |
| Table 10 | 3.3 | Detection on the test patients | T9 | committed |
| Table 11 | 3.3 | Detection per test patient | T10 | committed |
| Table 12 | 3.3 | Onset and offset error | T11 | committed |
| Table 13 | 3.4 | External validation | T12 | committed |
| Table 14 | 3.5 | Channel ranking against expert annotation | T13 | edit |
| Table 15 | 3.6 | Application detection on the test patients | T14 | after rebuild |
| Table 16 | 4.1 | Comparison with published studies | T16 | edit |
| — | — | Objectives and design requirements achieved | T15 | **removed (AR 4)** |

## 4 · Open items for Step C
1. **Siena hours:** PhysioNet describes about 128 h; the per-subject `hours` column of the external-validation summary sums to 141.0 h (computed). Describe the dataset with PhysioNet's figure and give the scored hours as our measurement after checking what the column counts.
2. **Siena notch:** 50 Hz, confirmed in the pre-registered external-validation code.
3. **Attribution synthetic validation:** no synthetic result for the final system in the numbers pack → not reported, unless HANDOFF_REPORT section 3 says otherwise.
4. **Missing from this project's knowledge:** `docs/HANDOFF_REPORT.md`, `docs/PERF_PHASE_RECORD.md`, `docs/VERIFIED_CORRECTIONS.md`, `docs/ATTRIBUTION_SPEC.md`, `Thesis_Reference_Sheet.md` (needed for every DOI, AR 9). Step C cannot start without them.
5. Application (Fig 9, Fig 12, Table 15): fallback after 12/10 per HANDOFF_REPORT section 0.
