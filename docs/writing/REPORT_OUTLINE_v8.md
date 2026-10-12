# REPORT_OUTLINE_v8 — outline of the thesis report (rev 2, 2026-10-12)

**Status: APPROVED (author, 12/10, O1–O6 as proposed).** Plan of record for the writing chats; supersedes
`REPORT_BLUEPRINT_v5.md`. Rev 2 (chat 2, figures): open checks of §8.2 resolved against the committed
repository (§8.1), exhibits produced (§5 status column), two data-accounting facts added (§8.1).

Inputs read for this outline: Chapters v5 + front matter v5; the 11/10 draft; PERF_PHASE_RECORD rev R;
HANDOFF_REPORT rev 2; STATUS_BOARD rev 1; `x1_SUMMARY.md`, `e23_SUMMARY.md`, `p3c_SUMMARY.md`,
`p2_ledger.csv`, `GATE.md`, `TIMING.md`, `DEMO_FINAL_HANDBACK.md` (application run, 12/10); writing rules
(AUTHOR_REQUIREMENTS, REVIEWER_RULES, RUBRIC_MAP, SAMPLE_PATTERNS, Report format, registration form);
the four sample theses (VBPH, Tri, Tuong, Hien) and the supervisor's papers (Yıldız 2022 [C2], SAnoDDPM
2024 [C7], IRENE 2026 [G9], EGDN-KL 2026 [N4], Dani & Liebe [N5]; N1–N3 title only, see 8.3).

Rules that bind every line below: numbers only from the files named beside them ("computed" when derived
from file values); report rules of instructions section 5 (no process, no internal names, captions are
short titles, integer numbering, "Section", numeric citations); AR 1–22 except AR 3 (appendix now
allowed, A2) and AR 21 (tried designs are results, A3).

---

## 0 · Critique of v5 and the 11/10 draft (against the samples and the supervisor's papers)

### 0.1 Writing

| # | Weakness | Evidence in v5 / draft | Pattern in samples and papers | v8 fix |
|---|---|---|---|---|
| W1 | Results far thinner than Methods | v5: Ch2 3,898 words / 18 pp vs Ch3 1,044 words / 6 pp; draft ~21 pp vs ~7 pp | Tri: Results 14 pp beside Methods 23 pp; VBPH 8 vs 14; supervisor's papers spend about half the text on experiments | Ch2 ~15 pp, Ch3 ~15 pp; settings table, annotation protocol, data accounting move to the appendix (Section 2) |
| W2 | Designs that failed are shown without numbers | v5 4.3: prose, 2 numbers; draft 4.3: no number at all | VBPH Tables 8–10 report rejected inputs and choose with a decision matrix; Tri reports the 46 % model in the abstract, a full results table and a Discussion section on why; EGDN-KL ablation: "omitting X drops F1 by Y" | Table 10 (designs evaluated on the development patients, with numbers) + Discussion 4.2 (mechanism of each) + Appendix C (every gated design) |
| W3 | Result paragraphs bury the finding under qualifiers; readings mixed | draft Table 6 puts a pooled count (37) beside a subject-mean sensitivity (0.577) and subject-mean FP/day (26.8); draft abstract "0.577 at 26.8"; v5 Siena sentence mixes seed-42 pooled 44.0 with 4-seed subject-mean 41.0 | IRENE: each result subsection ends with "key observations (1)…(4)"; SAnoDDPM: one table per reading | Text gives one reading per sentence (rule in Section 7); tables carry the rest; every Ch3 section ends with an "answer" sentence written in Section 3 below |
| W4 | Defensive repetition | draft repeats "not an independent estimate" in the abstract, 2.2, 2.8.2, 3.1, 4.1 (twice), 4.5 and Ch5 | Yıldız states each limit once and moves on | Disclosure once in 2.8.2; afterwards the one-word label "test-informed"; the clean evidence (held-out, external, application) gets the space |
| W5 | External validation and application compressed to one table / one patient | v5 3.4: one table; draft 3.5: chb03 only | Tri: UI walkthrough + in-app result table + cost; SAnoDDPM: per-patient tables and latency figure | 3.4 with per-patient Siena table, false-alarm drivers, onset/offset; 3.6 with the 8-patient application run |
| W6 | One example figure for the whole system | v5 Fig 11 (chb03) only | Yıldız Fig 3 (example windows); IRENE graph visualisations; SAnoDDPM per-patient latency | Figure 14 gallery (detected, near miss, missed short, false alarm, Siena), Figure 12 duration, Figure 13 boundary errors |
| W7 | Literature numbers absent from the gap table | v5 Table 1 qualitative only | Tri Table 1: author / method / performance / pros / cons; supervisor's papers cite numbers with protocol | Table 1 gets a column "representative result (protocol)" |
| W8 | Terms drift between versions | "subject-mean" / "mean patient sensitivity" / "averaged over patients"; "held-out" / "first evaluation"; "training and validation patients" / "15 development cases from 14 individuals"; "Objective" / "Goal" | Samples keep one term per concept | Fixed glossary, Section 7 |
| W9 | Statements that are now out of date | v5 3.6 pending; v5 4.5 "effect not measured" (normalisation) and "application not evaluated"; v5/draft Siena-hours sentence; draft Fig 14 shows the earlier application | — | 3.6 and 4.5 rewritten from the application run; A4 wording; new screenshots |

**Keep (strengths both reviewers would credit):** the review-triage framing; Table 1 gap synthesis; the
three decision matrices with enumerated verdicts; held-out and final evaluation side by side (v5
Table 10); per-patient failure mechanisms (v5 4.2); the channel-level negative tested against an
anatomical prior; equations with "where" lines.

### 0.2 The chain gap → contribution → result

| # | Break in the chain | Evidence | Fix in v8 |
|---|---|---|---|
| C-1 | Three parallel lists that do not align: the closing gap paragraph (4 links), contributions 1–4, goals 1–4 | v5 1.2 end, 1.3, 1.4 | Gaps numbered G1–G5 in Table 1; contributions C1–C5 each name their gap and the section that tests it; objectives map onto contributions (Section 1 table) |
| C-2 | Contribution 1 (patient-own reference) answers a gap Ch1 never states | v5 1.2.2–1.2.3 mention fitting on the first minutes only through DynaSD | G1 "reference of normal activity" stated in 1.2.2 with DynaSD [K4], foundation-model adaptation [N5] and cross-patient drops [A4, A6] |
| C-3 | Contribution 2 bundles a strongly supported element with a weakly supported one | drift correction: 0.612 → 0.681 on the development patients at similar FP/day; per-patient budget: +0.010 at +3.8 FP/day there, test gain = chb15 alone, test-informed | C2 states both with their own evidence; the budget is written as test-informed; Discussion 4.2 weighs each |
| C-4 | Contribution 4 bundles evaluation, external validation and the channel test | v5 1.3 item 4 | C4 = evaluation and external validation; C5 = channel-level explanation |
| C-5 | Contributions phrased as components, not claims | "A label-free, per-patient readout of a graph autoencoder: …" | Each contribution = what + measured effect + section (IRENE, Yıldız pattern) |
| C-6 | Novelty implicit | no "to our knowledge" sentence; the strongest quantified gap (4 of 108 unsupervised studies address localization [I4]) sits mid-paragraph | Novelty sentence at the end of 1.2 (Section 3, Ch1); I4 leads the localization gap |
| C-7 | Results organised by pipeline stage, without answers | v5 3.1–3.5 open with "Objective n" but close without a verdict | Each Ch3 section opens with its question and ends with an answer sentence (texts in Section 3) |
| C-8 | Discussion compares performance but never weighs each contribution | v5 4.1 vs 4.3 | New 4.2 "What each design choice contributed" (contribution + rejected alternatives + mechanism) |
| C-9 | Conclusion closes Objectives 1–2 only (v5); Goals 3–4 open | v5 Ch5 | Ch5 closes all four goals and C1–C5 |
| C-10 | Hypotheses absent although the design rests on three testable ones (format allows "Hypotheses") | — | H1–H3 in 1.3, each tested on the development patients before the test patients were scored (record §6) |

---

## 1 · The chain of record (internal; drives every chapter)

| Gap (1.2, Table 1) | Contribution (1.3) | Hypothesis | Objective / goal | Method | Result (exhibit) | Discussion | Conclusion |
|---|---|---|---|---|---|---|---|
| **G1** Normal reference: unsupervised detectors define normal from other patients or from the first minutes of a recording; a new patient's own unusual but normal activity scores as anomalous | **C1** Label-free, patient-adapted readout: per-channel latent distance to the patient's own recording | H1 | Objective 1 | 2.5.1 (Table 6), 2.5.2 | Table 9 rows 2→3; Table 10 reference rows | 4.2 (reference) | Ch5 ¶2 |
| **G2** Threshold and baseline drift set with labels or ignored | **C2** Drift correction per file (level only) and a per-patient alarm budget from the score itself | H2 (drift); budget test-informed | Objective 1 (drift) · Objective 2 (threshold) | 2.5.3, 2.6.2 | Table 9 rows 3→4, 5; Table 10 drift and budget rows; Table 12 budgets | 4.2 (drift, budget) | Ch5 ¶2–3 |
| **G3** No onset/offset on a learned anomaly score; CPD not applied to one; localization rarely studied | **C3** Kernel change point localizer on the ensemble score | H3 | Objective 2 | 2.6.1 (Table 7), 2.6.3 | Table 13, Figure 13 | 4.1 (latency), 4.2 (localizer) | Ch5 ¶3 |
| **G4** Results not comparable: segment-level, within-patient, exclusions | **C4** Continuous-recording, event-level evaluation (SzCORE), held-out + final + external, same-data comparison with the only unsupervised benchmark entry | — | Evaluation requirement of the registration form | 2.8 | Tables 11, 12, 14, 15; Figure 14 | 4.1 | Ch5 ¶3 |
| **G5** Channel explanations checked against chance or per-channel corpora; CHB-MIT has none | **C5** Blind expert annotation and an anatomical-prior test | — | Goal 3 | 2.7 | Table 16 | 4.4 | Ch5 ¶4 |
| Requirement (Table 2: label-free at use, hospital computer, data on site) | Review application | — | Goal 4 | 2.9 | Table 17, Figure 15 | 4.5, 4.6 | Ch5 ¶4 |

**Hypotheses (1.3 wording, to approve with O2):**
- **H1** A reference of normal activity fitted on the patient's own recording separates seizures from
  that patient's high-amplitude non-seizure activity better than a reference learned from other
  patients or from the first minutes of a recording.
- **H2** Most of the highest non-seizure scores come from slow shifts of the score between recording
  files, and removing each file's level, without labels, lowers them while keeping seizures.
- **H3** Kernel change point detection on the unsmoothed score places event boundaries closer to the
  annotation than the smoothed detector's boundaries.
The per-patient budget is not stated as a hypothesis: it was designed after the held-out evaluation and
is reported as test-informed.

**Contributions (1.3 wording, claims with evidence; numbers checked in Section 6):**
1. **C1 (G1)** A label-free readout of a graph autoencoder that measures each channel's latent distance
   from the patient's own recording; on the development patients it raised pooled sensitivity from
   0.489 to 0.612 at a similar false-alarm rate (Section 3.2).
2. **C2 (G2)** Baseline-drift correction and threshold calibration without labels: removing each file's
   running level raised development sensitivity to 0.681 at the same false-alarm rate, and a per-patient
   alarm budget derived from the score redistributes review time between patients (Sections 3.2, 3.3).
3. **C3 (G3)** Kernel change point detection as the onset and offset localizer on the ensemble anomaly
   score, which cut the median onset error on the test patients from 32 s to 12 s (Section 3.3).
4. **C4 (G4)** An evaluation on continuous recordings under the SzCORE standard with a held-out and a
   final result side by side, external validation on a further case and an adult corpus, and a
   same-data comparison with the only unsupervised benchmark entry (Sections 3.3, 3.4).
5. **C5 (G5)** A test of the channel-level explanation against a blind expert annotation and an
   anatomical prior (Section 3.5).

**Novelty sentence (end of 1.2):** "To our knowledge, no published method turns a learned EEG anomaly
score into seizure events with onsets and offsets without using seizure labels at any step — model,
reference, threshold or drift correction — and evaluates it on continuous recordings of unseen patients
under a shared event-based standard."

---

## 2 · Page budget (body ≤ 50, measured by building the document)

| Chapter | Prose words | Figures | Tables | Equations | Target pages | v5 (measured) |
|---|---|---|---|---|---|---|
| 1 Introduction | 2,000 | 3 (1–3) | 3 (1–3) | 0 | 8.0 | 11 |
| 2 Methodology | 2,900 | 7 (4–10) | 5 (4–8) | 12 | 15.5 | 18 |
| 3 Results | 2,300 | 5 (11–15) | 9 (9–17) | 0 | 15.0 | 6 |
| 4 Discussion | 2,100 | 2 (16–17) | 1 (18) | 0 | 8.0 | 8 |
| 5 Conclusion | 400 | 0 | 0 | 0 | 1.2 | — |
| **Body** | **9,700** | **17** | **18** | **12** | **47.7** | — |

Appendix (outside the 50): about 10 pages, Section 4. Front matter, lists and references outside the 50.

**Cut order if the built body exceeds 50 pages** (each saves about 0.5 page; stop when ≤ 50):
1. Figure 5 (EEG before and after preprocessing) → Appendix A.
2. Figure 9 (scoring rules) → one sentence + Appendix F.
3. Table 13 (onset/offset) folded into Figure 13 (values in the text).
4. Ch1 1.1.2 second paragraph shortened to two sentences (keep Figure 2).
5. Table 10 to its 8 most informative rows; the rest only in Appendix C.

---

## 3 · Chapter outline

Notation: **N** = number with its source; **X** = exhibit with data source and owner (S2 = script in chat 2
reading committed results; CC = Claude Code on the laptop; INH = inherited from `Reports/v8/figures_inherited/`,
check before reuse; NEW-T = table written in chat 3 from the named file).

### Front matter (outside the 50)
Title page (registered title verbatim, AR 5) · approval page · acknowledgements (v5 text) · ToC · list of
tables · list of figures · abbreviations (add CAR, EDF, CPD; remove unused) · **Abstract ≤ 300 words**, one
paragraph, moves: problem → gap → system → data and protocol → held-out and final result → localization →
external + DynaSD → fully label-free application run → channel negative → framing. Numbers: 26/76 (0.342;
subject-mean 0.508) @ 22.2; 37/76 (0.487; 0.577) @ 27.5 test-informed; onset 12 s; chb24 14/16; Siena
subject-mean 0.633 @ 41.0 vs DynaSD 0.664 @ 77.7; application 33/76 @ 27.9 (O1); channel 0.547 vs prior
0.739. Keywords ≤ 10 words: seizure detection; scalp EEG; graph autoencoder; change point detection;
unsupervised (v5).

### Chapter 1 Introduction (8 pp)

**1.1 Introduction to the biomedical problem** (~700 words)
- 1.1.1 Epilepsy and the burden of EEG review — v5 text (WHO [I1]; drug resistance [C6/I1]; EMU volume
  [B10]; readers disagree [F6]); review-triage framing; new patient without marked seizures.
- 1.1.2 Seizures in scalp EEG — 10–20, bipolar derivations, interictal/ictal, onset/offset;
  connectivity changes; direction can differ [E3].
- X: **Figure 1** EEG of one channel around a seizure (INH, draft Fig 1; confirm the record and file it
  was drawn from). **Figure 2** Connectivity in background and seizure windows (INH, chb11).

**1.2 Analysis of current solutions** (~900 words + Table 1)
- 1.2.1 Supervised detection — patient-specific 96 % @ 2/day [M8], per-case thresholds [D2];
  cross-patient drops [A4: F1 69.34 → 37.31 %; A6]; event-level cross-patient 0.753 @ ≈115/day [F2].
  Ends: labels of the new patient are needed.
- 1.2.2 Unsupervised, self-supervised and graph-based anomaly detection — two paragraphs.
  (a) reconstruction/generative: VAE AUC 0.68 window-level, folds over windows [C2]; DDPM segment-level
  per patient [C7]; cascaded AE with adaptive window threshold [E12]; SincVAE [E14]; sub-sequence
  anomalies, up to 99.38 % sensitivity, protocol not stated in the abstract [N1, abstract only]; extreme events [M4]. (b) graph and self-supervised: graph-deviation network on
  motor-imagery EEG, labels from a supervised classifier, Youden threshold [N4]; IRENE learned graphs
  sparse (0.16 vs 0.72) with a label-relevance term [G9]; self-supervised detectors with labelled heads
  [E9; N2 SLAM, CHB-MIT patient-dependent and cross-patient; N3 MCAN, cross-domain, AUROC 0.914 and F1 0.709 —
  abstract only, no event-level protocol stated]; foundation-model adaptation with unlabelled target data 46.9 → 83.1 % AUROC but
  labelled probe and 2 test patients [N5]; DynaSD fits the first minutes of each recording [K4].
  **Ends with G1** (reference) and **G5** (explanations checked against chance or per-channel corpora
  [E11, E13]; CHB-MIT has none).
- 1.2.3 Threshold calibration and baseline drift — thresholds from labels [D2, M1, N4, K4]; adaptive
  window threshold [E12]; drift between recordings rarely treated. **Ends with G2.**
- 1.2.4 Onset and offset localization — **lead with [I4]: 4 of 108 unsupervised studies address
  localization**; CPD [L3, L2]; network disruption with fixed threshold [E7]; GNN + CPD outside EEG [F1];
  onset/offset reported by supervised patient-specific methods [M8, M6, M7]. **Ends with G3.**
- 1.2.5 Evaluation on continuous recordings — protocol conflation [F2]; SzCORE [D4, G1]; challenge
  leader 37 % [D5]; exclusions [M2, M3]. **Ends with G4.**
- Closing paragraph: the chain G1–G5 as one synthesis + **novelty sentence** (Section 1).
- X: **Table 1** Current approaches and research gaps — columns: approach [refs] | labels needed |
  output | representative result (protocol) | gap (G-code). Rows: patient-specific supervised;
  cross-patient supervised; unsupervised reconstruction/generative; graph and self-supervised;
  label-free per-patient detector (DynaSD); change point detection. NEW-T from the reference sheet.

**1.3 Proposed solution** (~450 words + Table 2)
- System in one paragraph (v5 1.3 ¶1). Hypotheses H1–H3 (Section 1). Contributions C1–C5 (Section 1).
- X: **Table 2** Design requirements (v5 Table 2, eight rows; row 6 "general-purpose processor"
  unchanged).

**1.4 Project goals** (~180 words) — Goals 1–2 verbatim from the registration form + the one-sentence
qualifier for "spatial-temporal features"; Goal 3 channel-level explanation; Goal 4 review application.

**1.5 Timeline** — X: **Table 3** Thesis timeline: copied unchanged from the 11/10 draft (Table 2 there:
12 week columns, 9 rows; the author's week shading). Optional (O6): row labels "First test evaluation",
"Channel attribution study", "Web application prototype" → "Held-out test evaluation", "Channel-level
explanation study", "Review application"; weeks unchanged.

**1.6 Research framework** (~150 words) — X: **Figure 3** Research framework (redraw, S2 or author):
corpus → graphs → autoencoder → score → detector/localizer, design on development patients, held-out then
final evaluation, external validation, channel study and application; literature row on top. Last
sentence maps stages to Chapters 2–4.

### Chapter 2 Methodology (15.5 pp)

**2.1 Data** (~650 words)
- 2.1.1 CHB-MIT database and patient split — v5 text; cases vs individuals (chb01 = chb21, both
  training); 18 derivations; chb12 three files skipped (13 seizures); licence and de-identification
  (draft). N: test 76 seizures, 6–205 s, median 45 s, 23 < 20 s by annotation (`results/p3_seizure_burden/burden.txt`).
  X: **Figure 4** Bipolar montage (INH). **Table 4** Patient split (566.43 / 115.82 / 279.39 h listed in the CHB-MIT summary files;
  93 / 13 / 76 seizures; chb24 21.3 h, 16; Siena 141.0 h, 47; table note: hours scored 562.40 / 111.82 / 279.38 —
  chb12 three files without the 18 derivations, chb11 four files and chb21 one file absent from the local copy,
  none with a seizure; O7). Per-case table → Appendix A1 (`tables/appA1_chbmit_accounting`).
- 2.1.2 External data — chb24 (every present file, 21.3 h, 16 seizures); Siena: 14 adults (9 men 36–71,
  5 women 20–58) [K1, K2], referential 512 Hz → 18 bipolar derivations, 256 Hz, 50 Hz notch; annotations by
  the benchmark's converter [K5]; licence. **Hours sentence = A4 wording + PN14 clause (O3).** Per-patient
  accounting → Appendix A.
- 2.1.3 Preprocessing — filters, 4 s windows, signal-loss windows, per-patient z-score with the
  label-use disclosure (CHB-MIT statistics exclude seizures and the 4-h buffer; external sets and the
  application use every tenth window of the whole recording); ±5 SD flag = high amplitude (46 % of
  training non-seizure windows, ~90 % of seizure windows; record §2). X: **Figure 5** EEG before and
  after preprocessing (INH; first in the cut order).

**2.2 Pipeline overview** (~300 words) — what is fitted once (weights, input scaling, k) vs per patient
without labels (covariances, robust scaling, percentiles, budget); seizures 0.4 % of test time
(computed, v5 note); post-hoc review, not real time; Goal 1 qualifier. X: **Figure 6** Processing pipeline
(redraw from HANDOFF §1).

**2.3 Graph construction** (~550 words)
- 2.3.1 Connectivity graphs — CAR before coupling (VERIFIED_CORRECTIONS 1; no volume-conduction claim for
  CAR), wPLI (Eq 1) [E4], AEC (Eq 2) [E1], equal weights, strongest 20 % = 30 edges; edges are statistical
  coupling between derivations, not anatomical links (R4). X: **Figure 7** Connectivity graph
  construction (INH).
- 2.3.2 Node features — 18 + 5 (Eq 3) + 7 amplitude-preserving; why amplitude matters.
- 2.3.3 Decision matrix for edge sparsification — X: **Table 5** (v5 Table 5) + verdict (3 reasons).

**2.4 Graph autoencoder** (~300 words) — Eq 4, Eq 5, 3,964 parameters, training windows, Adam,
200 epochs, seeds 42/1/2/3, headline seed 42 [E6, X4, B1, X5].

**2.5 Ensemble anomaly score** (~700 words)
- 2.5.1 **Decision matrix for the normal reference (NEW, O4)** — X: **Table 6**: options A reference
  learned from other patients · B baseline from the first minutes of each file (as [K4]) · C the patient's
  whole recording. Criteria: labels needed (none / none / none); separates the patient's own
  high-amplitude states; covers every state of the patient; real-time capable (yes / yes / **no**);
  result on the development patients — A: feature-level cross-patient model 0.340 (record §2, E1);
  B: first 10 min 0.191, first 30 min 0.295, causal 30 min 0.487 (ledger E16 a, c, d); C: 0.612 latent
  (record §6.1, S9 base), 0.596 feature-level (E5). Adopted C. Verdict: three reasons (separation,
  every state, review setting accepts non-causal fitting).
- 2.5.2 Channel-level latent anomaly — Eq 6 [L1, L6], Eq 7 [L4].
- 2.5.3 Spatial members and baseline drift correction — members 6/9/12 + mean; drift motivation: about
  85 % (84.5 %) of the top-2 % non-seizure windows lie in the quarter of each patient's files with the
  highest median, and 8 % (8.3 %) of those files hold a seizure (record §6.1 E16); Eq 8; level only.
  X: **Figure 8** Baseline drift correction (DONE: `fig08_drift.png`, chb03, three consecutive files, seed 42,
  from committed `results/figures_v6_data/`; label-free signal, seizures shaded for orientation).
- 2.5.4 Ensemble score — percentile ranks, Eq 9.

**2.6 Detection and localization** (~650 words)
- 2.6.1 Decision matrix for detection and localization — X: **Table 7** (v5 Table 6) + verdict.
- 2.6.2 Per-patient alarm budget — smoothing 5 windows, Eq 10, k = 4.0677 (median q = 0.005 on the
  15 development patients, seed 42), floor 0.005, cap 0.02 (largest development budget 0.011, so the cap
  was untested before the final evaluation), merge 90 s.
- 2.6.3 Kernel change point localization — ±60 s, two change points, Eq 11 [L2, L3], acceptance rule,
  fallback. Full settings → **Appendix B** (v5 Table 7).

**2.7 Channel-level explanation** (~250 words) — per-seizure ranking by p95 of |robust z|; blind,
every-channel annotation by the author, supervisor-approved; 62 focal + 14 generalized; three tests in
plain words (chance, anatomical prior from the other seven patients, seizure specificity); method fixed
before comparison; the earlier reconstruction readout tested the same way. Protocol detail → Appendix E.

**2.8 Evaluation** (~650 words)
- 2.8.1 Event-based scoring — SzCORE [D4, G1]: tolerances 30/60 s, merge 90 s, split 300 s; per recording,
  counts summed per patient; sensitivity, precision, F1, FP/day (Eq 12); pooled and per-patient mean
  (official); onset/offset error. X: **Figure 9** Event-based scoring rules (draw own from the SzCORE
  definitions, cite [D4]; no borrowed image).
- 2.8.2 Development, held-out and final evaluations — design on the 15 development patients; held-out
  evaluation once with one budget 0.005; final system = per-patient budget designed after it →
  **test-informed** (the only place the disclosure is argued); earlier versions scored on the test
  patients during development (not untouched in the strict sense); about 40 gated design decisions on the
  development patients (record §6.4); 4 seeds; patient bootstrap 10,000 [L5]; offline-protocol paragraph
  (0.618 @ 27.4 → 23/76 (0.303) @ 73.3; HANDOFF §4).
- 2.8.3 External and application evaluations (NEW, ~150 words) — external sets run once, no change;
  application run: frozen build, clean database with the 8 test patients, every event exported before
  any review, scored outside the application with the same scorer, false-alarm time = recorded time
  minus seizure time (instructions §11.5).

**2.9 Review application** (~500 words)
- 2.9.1 Decision matrix for deployment — X: **Table 8** (v5 Table 8; totals 3.15 / 4.20 / 2.75 computed) +
  verdict (four reasons) [C4, C3, B11].
- 2.9.2 Architecture and label-free operation — browser + local server + SQLite + per-file cache; full
  pipeline recomputed from the raw signal, never replayed; three automated guards; the one divergence
  (z-score statistics, handback R6 wording); no network access during the run (handback R7).
  X: **Figure 10** Review application architecture (redraw from handback R5 / `CC_T1_RUN_REPORT.md` 1.7).

### Chapter 3 Results (15 pp)
Each section opens with its question (one sentence) and ends with the **answer** sentence given here.

**3.1 Connectivity graphs (Objective 1)** (~200 words) — v5 3.1 numbers: fixed threshold density
0.921–0.973 (background), 0.949–0.974 (seizure); proportional 0.196 (chb17 background 0.224); separation
up on 8/8 test patients, relative Frobenius +48 % (chb15) to +196 % (chb17), cosine +545 % to +903 %.
Source `results/diagnostics/density_frobenius_v2/` (8.1). X: **Figure 11** Separation by sparsification rule (DONE).
Answer: "Keeping the strongest fifth of the edges gave every patient the same graph density and a larger
seizure–background difference than a fixed threshold."

**3.2 Anomaly score on the development patients (Objective 1)** (~650 words)
- 3.2.1 Contribution of each component — X: **Table 9** (v5 Table 9, 7 rows, 4-seed means unless marked):
  0.330 @ 23.7 (seed 42) → 0.489 @ 20.1 → 0.612 @ 24.6 (0.742) → 0.681 @ 24.3 (0.821) → 0.668 @ 20.0 (0.828)
  → 0.678 @ 23.8 (0.842) → 0.670 @ 23.3 (0.832). Sources: record §2 E8, bootstrap (0.489 @ 20.06), E16
  reference, ledger E21-1, E17b, `p3c_SUMMARY.md`. Rows 3 and 4 are on the same grid (S9 base
  re-scored on the fine grid: 0.612, 8.1). Short seizures of this set: 2.0 of 3 (ensemble)
  vs 1.5 (single member).
- 3.2.2 **Designs evaluated and not adopted (NEW, F3)** — X: **Table 10** (DONE as `tables/table10_designs.md`, 15 rows) columns: stage | design |
  development result (pooled sensitivity @ FP/day, 4 seeds unless marked) | reference under the same rule |
  why not adopted (one line). Rows (sources: record §2, §6.1, §9.7, ledger):
  1. Reference from other patients (feature model) — 0.340 | patient-own feature density 0.596 | does not separate the patient's high-amplitude states (E1, E5)
  2. Artifact model trained on the ±5 SD flags — calls 81.5 % of seizure windows artifact | — | the flag marks amplitude, not artifact (E4)
  3. Baseline from the first 10 / 30 min of each file; causal 30 min — 0.191 / 0.295 / 0.487 | whole recording 0.612 | fits one state of the patient (E16 a, c, d)
  4. Per-patient fine-tuning of the autoencoder — 0.628 (2 seeds) | 0.622 | seizure scores rose, non-seizure scores did not fall (E15)
  5. Graph-level latent distance alone — 0.553 @ 23.8 (2 seeds) | channel-level 0.622 (2 seeds) | below the required gain (E12, E14)
  6. Adding reconstruction error and gamma-band coupling (best combination) — 0.636 | channel score alone 0.681 | inferior on pooled sensitivity (E21 stage 2; E21b 0.609)
  7. Drift correction of level and spread per file — 0.596 | level only 0.681 | lowers seizure scores, z 4.72 → 4.08 (E16b, E21-1)
  8. Per-file median instead of a running median — 0.559 | 0.628 | (E16f vs E16e, coarse grid)
  9. Change point detection as the detector — penalised segmentation 0.213 vs threshold 0.479; kernel bump detector 0.250 @ 5.8 vs 0.489 @ 19.8 | — | marks falling changes; on the threshold curve, not above it (E7, E10)
  10. Second detector for short seizures — +0.000 | — | short-seizure peaks below any affordable threshold (E19b)
  11. Uniform 2 % budget — 0.803 @ 95.1 | per-patient budget 0.678 @ 23.8 | four times the review load (record §9.7)
  12. Budget floor 0.0025 — 0.657 @ 20.5; chb21 1.75 → 0.50 seizures | floor 0.005: 0.678 @ 23.8 | cut patients below the held-out budget (P3 L2, L2f)
  13. Multichannel kernel CPD localizer — 0.657, offset 8 s | 1-D CPD 0.662, offset 16 s | lost sensitivity (E20a)
  14. Hybrid localizer (CPD onset, contiguous-run offset) — onset 8 s, offset 12 s | CPD onset 4 s, offset 16 s | worse onset (P3c)
  Text below the table: total gated decisions (about 40) and that these numbers describe the patients
  the design was tuned on (optimistic, rule 19; held-out sensitivity was about half). Full list → Appendix C.
- Answer: "Without any seizure label, the components raised pooled sensitivity on the development
  patients from 0.330 to 0.670 at about 23 false alarms per day; the largest steps were the
  amplitude-preserving features, the patient-own channel reference and the drift correction."

**3.3 Detection and localization on the test patients (Objective 2)** (~800 words)
- 3.3.1 Held-out and final evaluation — X: **Table 11** (v5 Table 10 restored, columns held-out | final,
  rows: seed-42 TP/FN/FP (26/50/257; 37/39/318); sensitivity pooled / per-patient mean (0.342/0.508;
  0.487/0.577); precision (0.092/0.108; 0.104/0.118); F1 (0.145/0.174; 0.172/0.190); FP/day (22.2/21.8;
  27.5/26.8); 4 seeds (0.336 ± 0.008 / 0.498 ± 0.010; 0.477 ± 0.022 / 0.567 ± 0.019; FP/day 23.9 ± 1.2;
  29.2 ± 1.3); bootstrap (held-out pooled [0.133, 0.670], mean [0.226, 0.770]; final − held-out pooled
  +0.141 [0.000, 0.333], mean +0.070 [0.000, 0.201], FP/day +5.3 [+0.4, +13.6])). Sources: `e23_SUMMARY.md`,
  `results/e22_test_oneshot/BOOTSTRAP.md`. FN counts computed (76 − TP).
- 3.3.2 Per patient — X: **Table 12** (v5 Table 11 + FP counts): budgets, detected, FP/day per patient
  held-out | final (`e23_SUMMARY.md` per subject). Text: four largely detected (chb03, chb14, chb17,
  chb18), three largely missed (chb06, chb13, chb16), chb15 0 → 11/20 at the cap (8.5 → 32.3 FP/day);
  every other budget-0.005 patient identical.
- 3.3.3 Detection by seizure duration (NEW) — 4 of the 18 seizures shorter than five whole windows
  detected in both evaluations; detection rate by duration bin. X: **Figure 12** Detection by seizure
  duration (script ready; data = Claude Code `CC_FIGURES_V8.md` step 1, gated 37/76 and 26/76).
- 3.3.4 Onset and offset — X: **Table 13** (v5 Table 12: development 16/24 → 4/16 computed, n = 247;
  held-out 28/16 → 8/20, n = 103; final 32/20 → 12/24, n = 146; chb24 12/8 → 4/4, n = 53; Siena 36/28 →
  20/28, n = 116); offset bias +16 s; contiguous-run offset 16 s (final). **Figure 13** Onset and offset
  error (DONE). Table 13 adds the localizer bias (median signed error): development +4/+4, held-out +4/+16, final +8/+16,
  chb24 +4/0, Siena +20/+20 s. Review share of
  detected events 2.2 % of recorded time (0.0215; `e23_SUMMARY.md`).
- 3.3.5 Detection examples (NEW, F5) — X: **Figure 14** Detected and missed seizures (plot script ready and smoke-tested; data = Claude Code step 2; 18-channel EEG +
  ensemble score + threshold + detector event + localized event + annotation; panels: (a) chb03 detected,
  (b) chb15 seizure detected only under the per-patient budget, (c) chb16 short seizure missed, (d) a
  high-amplitude false alarm, (e) one Siena seizure). Panel (e) only if the Siena EDF files are on the laptop (O8).
- Answer: "The held-out evaluation detected 26 of 76 seizures (per-patient mean 0.508) at 22.2 false
  alarms per day; the final, test-informed system 37 of 76 (0.577) at 27.5, the difference being one
  patient; the localizer placed onsets within a median of 12 s but did not improve offsets."

**3.4 External validation** (~650 words, F4)
- 3.4.1 Overall — X: **Table 14** columns per set: seed 42 TP/n, FP, sensitivity pooled / per-patient
  mean, precision, F1, FP/day; 4-seed mean ± SD; bootstrap. chb24: 14/16, 26 FP, 0.875, 0.350, 0.500,
  29.5; 4 seeds 0.828 ± 0.060 @ 28.4. Siena: 33/47, 257 FP, 0.702 / 0.748, precision 0.114, F1 0.196
  (pooled), 44.0 (pooled) / 41.5 (mean); 4 seeds pooled 0.617 ± 0.060 @ 43.8; per-patient mean 0.633 ±
  0.079, precision 0.160, F1 0.226, 41.0; bootstrap mean [0.477, 0.777], FP/day [32.3, 53.9] (computed,
  record 9.9). Benchmark row on the same data: DynaSD 0.664, 0.126, 0.170, 77.7 [K3]. Sources:
  `x1_SUMMARY.md`, record 9.9.
- 3.4.2 Per Siena patient — X: **Table 15** (NEW): patient, recorded hours, seizures, detected, false
  alarms, FP/day, alarm budget (seed 42, `x1_SUMMARY.md`): PN00 5/5 … PN17 2/2. Text: PN05 0/3; PN09 1/3;
  PN13 1/3; > 70 FP/day in PN06 (76.1), PN07 (90.9), PN16 (79.8).
- 3.4.3 What drives the false alarms — the seven patients whose label-free budget exceeded 1.7 % (PN03,
  PN06, PN07, PN11, PN14, PN16, PN17) produced 197 of the 257 false alarms (computed); five reached the 2 %
  cap; short recordings inflate FP/day (PN11 2.41 h: 3 false alarms = 30.1 per day).
- 3.4.4 Onset/offset — chb24 4/4 s; Siena 20/28 s (detector 36/28; contiguous-run offset 20 s).
- 3.4.5 Children to adults — the autoencoder was trained on pediatric recordings; the Siena per-patient
  mean (0.633, 4 seeds) is higher than the CHB-MIT held-out mean (0.498, 4 seeds).
- Answer: "On data never used in design, the system detected 14 of 16 seizures of a further CHB-MIT case
  and reached a per-patient mean sensitivity of 0.633 at 41.0 false alarms per day on the adult Siena
  corpus, against 0.664 at 77.7 for the only unsupervised benchmark entry."

**3.5 Channel-level explanation (Goal 3)** (~200 words) — X: **Table 16** (v5 Table 14): final readout
0.547 [0.499, 0.597], p = 0.018; Δ prior −0.191 [−0.262, −0.118] (prior 0.739); specificity p = 0.53;
without chb15 0.486; earlier readout 0.569 [0.510, 0.632], p = 0.001; −0.169 [−0.255, −0.080];
p = 0.34 (Holm 0.68); the table prints both, final readout p = 0.53 (Holm 1.00); without chb15 0.501; seeds 1/2/3 0.543 /
0.588 / 0.545 (HANDOFF §3; `results/attribution_v8/`, `results/attribution_v7/`). Answer: "The ranking
agreed with the blind annotation slightly above chance and clearly below a rule that ignores the EEG."

**3.6 Review application (Goal 4)** (~450 words)
- X: **Figure 15** Review application screens (three PNGs in `Reports/v8/figures/app_screens/`:
  a import, b analysis of chb03 with event 1, c channel panel with Accept/Reject/Uncertain); prose
  walkthrough (Tri pattern); channel panel = model output only.
- Identity with the evaluation: chb03 with the evaluation's statistics 7/7 with 22 false alarms (= final
  system); with label-free statistics 6/7 with 20 (`GATE.md`).
- **Application run on the 8 test patients (O1)** — X: **Table 17** (NEW): per patient application |
  final system (seed 42): chb03 6/7, 20 FP | 7/7, 22; chb06 1/10, 97 | 2/10, 90; chb13 1/12, 41 | 1/12, 40;
  chb14 6/8, 33 | 6/8, 34; chb15 10/20, 59 | 11/20, 53; chb16 1/10, 16 | 2/10, 16; chb17 3/3, 27 | 3/3, 25;
  chb18 5/6, 30 | 5/6, 38; total 33/76, 323 | 37/76, 318; pooled sensitivity 0.434, precision 0.093, F1
  0.153, 27.86 FP/day; per-patient mean 0.528, 0.108, 0.175, 26.92 (`results/application_eval_v4/`,
  handback R3). Coverage 76/76 seizures in 279.39 h.
- Processing time (O1): median 21.68 s per hour of EEG on chb16 (19.0 h, 3 runs, range 21.60–24.41;
  feature stage 266.1 s of 410–464 s, `TIMING.md`); the full 8-patient run took 5,862 s for 279.39 h
  (21.0 s per hour overall, computed as total/total; per-patient rates 11.8–25.4 s/h under varying
  background load) → one day of EEG in about 9 minutes (computed 21.68 × 24 = 520 s). Processor model from the author's check (O8).
- Answer: "Running the whole system from the raw recordings, with no label at any step, the application
  flagged 33 of the 76 test seizures at 27.9 false alarms per day and processed an hour of EEG in about
  22 seconds on a laptop processor."

### Chapter 4 Discussion (8 pp)

**4.1 Detection performance in context** (~650 words) — X: **Table 18** Comparison with published studies
(v5 Table 16 rows + this work's fully label-free application row + Siena supervised entries trained on
TUH only — out-of-sample, confirmed in `docs/BENCHMARK_CHECK_szcore_c57da2f.md`: Zhu 2023 0.674 @ 15.30, EventNet 0.587 @ 8.21,
Tang 2021 0.824 @ 112.50 [K3]; rows in `src/figures_v8/comparison_rows.csv`); **Figure 16** Sensitivity
versus false alarms per day (DONE, two panels CHB-MIT / Siena). Content: only DynaSD on Siena is directly comparable
(similar sensitivity, about half the false alarms; own scorer implementation); supervised detectors
trained elsewhere reach Siena at 8–15 FP/day — the price of having no labels; CHB-MIT rows differ by
labels, exclusions or rule (Ali [F2], Chung [M2], Yin [M3], Mirzaei [M1], Shoeb [M8], SzCORE baselines
[K6]); with chb06 and chb16 removed: 33/56 final, 22/56 held-out (computed); window-level unsupervised
methods cannot be placed [C2, C7] (Yıldız pattern: state where weaker, why still useful); supervised
reference on the development patients 0.702 @ 20.5 (record §2 E3) — what labels buy; onset/offset vs
[M8, M7, M6] at 4 s resolution; precision ≈ 0.1 → triage, 2.2 % of recorded time ≈ 31 min per day of
recording (computed).

**4.2 What each design choice contributed (NEW; closes the chain)** (~650 words) — one paragraph each:
- **Reference (C1, H1 supported):** cross-patient and first-minutes references fail for the same reason —
  they fit one state; mechanism numbers: short baselines fit one state (fit-noise ratio 0.62,
  self-scoring −0.92 z; record §6.1 E16); fine-tuning raised seizure z 4.90 → 5.32 without lowering
  flagged windows (E15); consistent with DynaSD [K4] and foundation-model adaptation [N5].
- **Readout:** reconstruction error barely separates seizures from high-amplitude non-seizure windows
  (AUROC 0.527–0.534 vs latent 0.966, E11); gamma coupling drifts strongly between files (IQR/MAD 1.54,
  E21); hence the latent channel score alone.
- **Drift (C2, H2 supported):** the drift is a file-level shift of the readout, not more high-amplitude
  activity (flagged share 0.459 in top files = 0.459 elsewhere, E16); level-only correction helps, scale
  correction lowers seizure z.
- **Budget (C2, test-informed):** no gain on the development patients (+0.010 at +3.8 FP/day, on the
  same curve), the test gain is chb15 at the cap; a uniform raise costs 95 FP/day; the per-patient budget is
  a way to spend review time where the score says the recording is abnormal, not a tested improvement.
- **Localizer (C3, H3 supported for onset only):** onset halved relative to the detector; on offset a
  contiguous-run rule is as good (16 s vs 24 s on test; 12 vs 16 s development), and the multichannel
  localizer placed offsets best (8 s) at a small loss in sensitivity — the most direct route to better
  offsets.
- **Evaluation (C4):** development over-predicts test about 2× (0.670 → 0.336 held-out 4 seeds; test
  seizure peaks outranked by 20–50 % of same-length non-seizure spans vs 4 % on validation,
  `results/oracle_gate_bound/`); the offline protocol overestimated (one sentence, refer to 2.8.2).

**4.3 Where the system fails** (~450 words) — v5 4.2 text with ONE reading (8.1): seed 42, the reading of Figure 17 — median alarm budget needed chb06 4.2 %,
chb13 3.0 %, chb16 3.4 % (well-detected patients ≤ 0.25 %); channels with robust z > 3 at the seizure peak (4-seed mean):
chb06 1.4 vs 6.3–15.4 in the well-detected patients.
X: **Figure 17** Alarm budget needed per test seizure (DONE, `results/p3_anatomy/seizures.csv`, seed 42;
caption title only; text says it is a post-hoc analysis that uses the test annotations). Short
seizures: 23 by annotation / 18 by whole windows, 4 detected. False alarms: the highest non-seizure
scores are mostly high-amplitude windows and rarely near seizures (`results/p3b_diag/tail.csv`, 8.1).

**4.4 Channel-level explanation** (~250 words) — v5 4.4 (frontopolar channels 116 of 282 annotated channel labels = 41 %, computed; five channels never
annotated: C3-P3, C4-P4, P4-O2, FZ-CZ, CZ-PZ — `results/attribution_v7/label_composition.csv`; chb15 0.675).

**4.5 Limitations and future work** (~400 words) — eight test patients (wide intervals); test set used
during development; **label-dependent normalisation now measured: with label-free statistics the same
system found 33 instead of 37 of the 76 test seizures (one fewer in chb03, chb06, chb15 and chb16) at 5
more false alarms (O1)**; 4 s windows and 20 s smoothing; post-hoc only; FP 22–44 per day; own scorer
implementation; one annotator; no independent rerun yet. Future: shorter/overlapping windows; a readout
for seizures more regular than background; a representation separating seizures from the patient's own
high-amplitude states; multichannel localizer for offsets; prospective review study; new patients (the
CHB-MIT test set is used up).

**4.6 Economic, social and global impacts** (~350 words) — v5 4.6 + the application's measured
processing time and local operation.

### Chapter 5 Conclusion (1.2 pp, ~400 words, no new numbers or citations)
¶1 problem and system. ¶2 Goal 1 met: C1 + C2 drift (0.330 → 0.670 development). ¶3 Goal 2 met with a
measured role: held-out 26/76 @ 22.2, final 37/76 @ 27.5 test-informed, onset 12 s, offset not improved;
external chb24 14/16, Siena 0.633 @ 41.0 vs DynaSD. ¶4 Goal 3 not met as a localization aid (negative,
stated); Goal 4 met: fully label-free application 33/76, ~22 s per hour. ¶5 limits and next steps; the
one-sentence significance.

---

## 4 · Appendix (outside the 50; tables and figures continue the integer numbering, O5)

| App. | Title | Content | Source | Pages |
|---|---|---|---|---|
| A | Data accounting | A1 CHB-MIT per case: files used / skipped, recorded hours, seizures, set; A2 Siena per patient: EDF hours (ours) vs PhysioNet table vs seizure-list registration times, seizures; PN03/PN10/PN12/PN14 notes | `data/testset_v2/*.npz` (`files`, `skipped_files`), `data/trainset_v2/`, CHB-MIT summaries; `x1_SUMMARY.md` hours, `subject_info.csv`, `Seizures-list-PN*.txt`, PN14 EDF durations (chat 1) | 1.5 |
| B | Settings of the final system | v5 Table 7 (every setting, value, fitted on) + autoencoder layer sizes | v5 Table 7, HANDOFF §1, `results/p3c_freeze/freeze.json` | 1 |
| C | Development designs | every gated design: stage, design, result, reference, gate outcome, adopted or not; count of decisions | record §2, §6.1, §6.4, §9.7; `p2_ledger.csv` (verdict = step gate, record 10.3) | 2 |
| D | Per-patient results | D1 test: held-out and final, 4 seeds, per patient; D2 Siena per patient (seed 42; 4 seeds if per-seed file exists); D3 chb24 per seed | `results/e22_test_oneshot/`, `results/e23_test_look7/`, `results/x1_external/` | 2 |
| E | Channel annotation and per-seizure agreement | protocol (blind, every channel, approval); per-seizure AUROC (62 focal); per-patient summary | `results/attribution_v7/labels/source/` (read only), `results/attribution_v8/` | 1.5 |
| F | Review application checks | guards (3) and tests (15/15); identity gate table; timing per stage (chb16); application run timing per patient; coverage 76/76; no-network evidence | `GATE.md`, `TIMING.md`, `results/application_eval_v4/ingest_timing.csv`, handback | 1.5 |

---

## 5 · Exhibit register (consecutive, short titles; owner; source)

**Produced in chat 2** (`src/figures_v8/make_v8_exhibits.py`, gated; output `Reports/v8/figures|tables/`): Figures 8, 9,
11, 13, 16, 17; Tables 4 (totals), 10, 11, 12, 13, 14, 15, 16, 17; Appendix A1, D1–D3. **Waiting for Claude Code**
(`docs/prompts/CC_FIGURES_V8.md`): Figure 12 (per-seizure file), Figure 14 (gallery data). **Inherited, to check by the
author:** Figures 1, 2, 4, 5, 7. **To draw (diagram):** Figures 3, 6, 10 — reuse the draft's drawings if they show the
final system, else redraw (chat 3). Tables 1, 2, 3, 5–9, 18 are written in the chapter files.

| No. | Sec | Title | Owner | Source / status |
|---|---|---|---|---|
| Fig 1 | 1.1.2 | EEG of one channel around a seizure | INH | draft Fig 1; record and file to name |
| Fig 2 | 1.1.2 | Connectivity in background and seizure windows | INH | v5 Fig 1 (chb11) |
| Fig 3 | 1.6 | Research framework | S2/author | redraw |
| Fig 4 | 2.1.1 | Bipolar montage | INH | — |
| Fig 5 | 2.1.3 | EEG before and after preprocessing | INH | chb10 segment |
| Fig 6 | 2.2 | Processing pipeline | S2/author | redraw from HANDOFF §1 |
| Fig 7 | 2.3.1 | Connectivity graph construction | INH | chb11 window |
| Fig 8 | 2.5.3 | Baseline drift correction | CC | development patient, seed 42, E16 cache |
| Fig 9 | 2.8.1 | Event-based scoring rules | S2 | own drawing of SzCORE rules [D4] |
| Fig 10 | 2.9.2 | Review application architecture | S2/author | handback R5 |
| Fig 11 | 3.1 | Separation by sparsification rule | INH | data source to locate |
| Fig 12 | 3.3.3 | Detection by seizure duration | S2 | per-seizure file (8.2) |
| Fig 13 | 3.3.4 | Onset and offset error | S2 | matched-pair error file (8.2) |
| Fig 14 | 3.3.5 | Detected and missed seizures | CC | EDF + score caches (seed 42, final); Siena panel needs Siena EDF |
| Fig 15 | 3.6 | Review application screens | done | `Reports/v8/figures/app_screens/` (a, b, c) |
| Fig 16 | 4.1 | Sensitivity versus false alarms per day | S2 | Table 18 rows |
| Fig 17 | 4.3 | Alarm budget needed per test seizure | S2 | `results/p3_anatomy/seizures.csv` |
| Tab 1 | 1.2 | Current approaches and research gaps | chat 4 | reference sheet |
| Tab 2 | 1.3 | Design requirements | chat 4 | v5 Table 2 |
| Tab 3 | 1.5 | Thesis timeline | author | draft Table 2, unchanged weeks |
| Tab 4 | 2.1.1 | Patient split | chat 3 | v5 Table 4 |
| Tab 5 | 2.3.3 | Decision matrix for edge sparsification | chat 3 | v5 Table 5 |
| Tab 6 | 2.5.1 | Decision matrix for the normal reference | chat 3 | record §2, §6.1, ledger (NEW) |
| Tab 7 | 2.6.1 | Decision matrix for detection and localization | chat 3 | v5 Table 6 |
| Tab 8 | 2.9.1 | Decision matrix for deployment | chat 3 | v5 Table 8 |
| Tab 9 | 3.2.1 | Contribution of each component | chat 3 | v5 Table 9 |
| Tab 10 | 3.2.2 | Designs evaluated and not adopted | S2 table + chat 3 | record, ledger (NEW) |
| Tab 11 | 3.3.1 | Detection on the test patients | chat 3 | `e23_SUMMARY.md`, BOOTSTRAP |
| Tab 12 | 3.3.2 | Detection per test patient | chat 3 | `e23_SUMMARY.md` |
| Tab 13 | 3.3.4 | Onset and offset error | chat 3 | e22/e23/x1 summaries, freeze errors |
| Tab 14 | 3.4.1 | External validation | chat 3 | `x1_SUMMARY.md`, record 9.9, [K3] |
| Tab 15 | 3.4.2 | Detection per Siena patient | chat 3 | `x1_SUMMARY.md` (NEW) |
| Tab 16 | 3.5 | Channel ranking against expert annotation | chat 3 | attribution v7/v8 |
| Tab 17 | 3.6 | Review application on the test patients | chat 3 | `results/application_eval_v4/` (NEW) |
| Tab 18 | 4.1 | Comparison with published studies | chat 4 | v5 Table 16 + reference sheet K/M |
| Eq 1–12 | Ch2 | wPLI, AEC, band power, GCN encoder, loss, Mahalanobis, robust z, drift, ensemble, budget, kernel CPD, F1/FP-day | chat 3 | v5 |

---

## 6 · Number register (for the `xanh` check; label every use)

| Quantity | Value | Reading | Source |
|---|---|---|---|
| Development, final system | 0.670 @ 23.25; mean 0.832 | 4 seeds, pooled; per-patient mean | `p3c_SUMMARY.md` (L2f cpd) |
| Held-out | 26/76 = 0.342 @ 22.22; mean 0.508; prec 0.092/0.108; F1 0.145/0.174; mean FP/day 21.79 | seed 42 | `e23_SUMMARY.md` look #6 rows |
| Held-out, 4 seeds | 0.336 ± 0.008 @ 23.88 ± 1.19; mean 0.498 ± 0.010 | 4 seeds | `e23_SUMMARY.md` |
| Final | 37/76 = 0.487 @ 27.49; mean 0.577; prec 0.104/0.118; F1 0.172/0.190; mean FP/day 26.84 | seed 42, after localizer | `e23_SUMMARY.md` |
| Final, 4 seeds | 0.477 ± 0.022 @ 29.15 ± 1.26; mean 0.567 ± 0.019 | 4 seeds | `e23_SUMMARY.md` |
| Bootstraps | see 3.3.1 | 4-seed means, B = 10,000 | BOOTSTRAP.md, `e23_SUMMARY.md` |
| Onset/offset | see Table 13 | median |error|, 4 seeds pooled pairs | summaries; development values computed (v5 note) |
| chb24 | 14/16 @ 29.52; prec 0.350; F1 0.500; 4 seeds 0.828 ± 0.060 @ 28.4 | seed 42 / 4 seeds | `x1_SUMMARY.md`, record 9.9 |
| Siena | 33/47 = 0.702 @ 44.01 pooled; mean 0.748 @ 41.52; 4 seeds pooled 0.617 ± 0.060 @ 43.8; mean 0.633 ± 0.079, prec 0.160, F1 0.226 @ 41.0 | as labelled | `x1_SUMMARY.md`, record 9.9 |
| DynaSD on Siena | 0.664, 0.126, 0.170 @ 77.7 | per-patient mean | [K3] |
| Siena hours | 141.0 h scored (141.0055 computed); PhysioNet table 128.4 h | — | `x1_SUMMARY.md`; board A4 |
| PN14 | EDF 20.464 h (2.1856 + 2.5458 + 11.6653 + 4.0672, computed) = scored 20.4622; table 23.47; seizure list 23.46 (PN14-3: 11.67 h in the file, 14.67 h from its registration times) | — | author's Kaggle printout 12/10; `x1_SUMMARY.md`; board A4 |
| Channel | 0.5473 [0.4992, 0.5971] p 0.018; Δ −0.1914; prior 0.7387; without chb15 0.4864 | seed 42 | HANDOFF §3 |
| Application | 33/76 = 0.434, 323 FP, prec 0.093, F1 0.153, 27.86; mean 0.528, 0.108, 0.175, 26.92 | seed 42, label-free statistics, every event before review | `results/application_eval_v4/`, handback R3 |
| Identity gate | 7/7 with 22 FP (evaluation statistics); 6/7 with 20 (label-free) | chb03, localized | `GATE.md` |
| Timing | 21.68 s/h median (21.60–24.41), chb16 19.0 h, 3 runs | headless, CPU | `TIMING.md` |
| Full run | 5,862 s for 279.39 h; 21.0 s/h = total/total (not a median; median of per-patient rates 20.69, computed) | — | handback §3 |
| Review share | 0.0215 of recorded time (≈ 31 min per day, computed) | seed 42, final | `e23_SUMMARY.md` |

---

## 7 · Fixed terms (one word per concept, whole report)

| Use | Not |
|---|---|
| development patients (the 12 training + 3 validation patients) | non-test, selection set, 15 development cases from 14 individuals |
| held-out evaluation | first evaluation, look #6, clean test |
| final system; final evaluation (test-informed) | look #7, P3 |
| external validation | X1 |
| pooled sensitivity; per-patient mean sensitivity (the SzCORE aggregate) | subject-mean, mean patient sensitivity, averaged over patients |
| seed 42 (headline); mean ± SD over four seeds | 4-seed |
| false alarms per day (FP/day in tables) | FA/day |
| ensemble anomaly score; channel-level latent anomaly | scalar, final scalar, S9, E17b |
| per-patient alarm budget; baseline drift correction; kernel change point localizer | L2f, E16e, CPD localizer (CPD only after definition) |
| channel-level explanation | attribution (except in a citation's own term) |
| review application | demo, SzScan (product name only in Figure 15 if visible), web app |
| Goal 1–4 (Section 1.4 wording; Goals 1–2 = registered objectives) | mixing Objective / Goal |

Sentence rule (W3): one reading per sentence — "detected 37 of 76 seizures (pooled 0.487; per-patient
mean 0.577) at 27.5 false alarms per day (seed 42)"; four-seed and interval readings go to tables or a
separate sentence.

---

## 8 · Open checks

### 8.1 Resolved (chat 1 and chat 2; read from the committed repository, commit 9f64036)
- **PN14 (A4).** EDF 2.1856 + 2.5458 + 11.6653 + 4.0672 = 20.464 h (computed) = the 20.4622 h scored; PhysioNet's table
  (23.47 h) and PN14's seizure list (23.46 h) are ~3.0 h longer, all in PN14-3; PN14's 4 seizures are among the 47 scored.
- **(1) Development hours.** 566.43 / 115.82 / 279.39 h = start/end times of the CHB-MIT summary files (computed by
  `make_v8_exhibits.py`). Hours scored (`results/p3_anatomy/labelfree.csv`): 562.40 / 111.82 / 279.38. Differences:
  chb12 3.0 h (three files without the 18 derivations, known); **chb11 4.0 h (chb11_12–15) and chb21 1.0 h (one file)
  listed in the summaries but absent from the local dataset copy** (`continuous_eval.list_files` docstring for chb11);
  none of these five files holds a seizure. → O7.
- **(2) Sparsification.** `results/diagnostics/density_frobenius_v2/` (density and separation per test patient):
  relative Frobenius +47.9 % (chb15) to +195.9 % (chb17), cosine +545 % to +903 % — the v5 numbers.
- **(3) Table 9 rows 3–4** are on the same fine grid: S9 base 0.612 @ 24.64 (`results/e21_fine_grid/SUMMARY.md`).
- **(4) Per-seizure files.** `results/p3_anatomy/seizures.csv` (duration, pn_final, `caught` = held-out detector stage,
  4 seeds) feeds Figure 17; it has no final-system detection flag → Figure 12 needs the Claude Code export
  (`docs/prompts/CC_FIGURES_V8.md`, step 1). Matched-pair errors: `results/e23_test_look7/errors.csv`,
  `results/e22_test_oneshot/errors.csv`, `results/p3c_freeze/errors.csv` (budget L2f), `results/x1_external/errors_*.csv`.
- **(5) v5 vs draft (4.3).** Both were right under different readings: v5 2.7–3.5 % = 4-seed mean of the per-seed
  medians; draft 3.0–4.2 % = seed 42. v8 uses seed 42 (the reading of Figure 17): chb06 4.2 %, chb13 3.0 %, chb16 3.4 %.
- **(6) False-alarm anatomy:** `results/p3b_diag/tail.csv` (flagged, peri-ictal and in-tolerance shares of the top
  non-seizure windows, per patient and tier).
- **(7) Per-seed per-patient:** `results/e22_test_oneshot/per_subject_seed.csv`, `results/e23_test_look7/per_subject_seed.csv`,
  `results/x1_external/rows_*.csv` → Appendix D tables done.
- **(9) Siena benchmark entries:** Zhu 2023, EventNet 2024 and Tang 2021 declare TUH only → out-of-sample on Siena
  (`docs/BENCHMARK_CHECK_szcore_c57da2f.md`).
- **(11) Table 16:** both p printed: final readout specificity p = 0.53 (Holm 1.00); earlier readout p = 0.34 (Holm 0.68).
- **(12) 4.4 numbers:** frontopolar 116 of 282 annotated channel labels (41 %, computed); five channels never annotated.
- **(13) Figure 1:** `src/figures/fig1_1_seizure_phases.py`, chb11 (validation patient); author confirms it is the draft's Fig 1.
- **Figure 9** (scoring rules): `src/figures/fig2_14_event_scoring.py` reads the parameters from `src/szcore_eval.py`
  (synthetic waveform, own drawing) → `fig09_event_scoring.png`; first candidate in the cut order (full page).
- **N1–N3:** abstracts supplied by the author (12/10); cited at abstract level (§3, 1.2.2).

### 8.2 Still open (author, one command — O8)
- (8) Where the Siena EDF files are on the laptop (for Figure 14 e), if anywhere.
- (10) Processor model of the timing laptop.
- chb21: name of the file absent from the local copy (for Appendix A1).

## 9 · Approvals (O1–O6 approved by the author 12/10; O7–O8 pending)

| # | Question | Proposal |
|---|---|---|
| O1 (A8) | Application run (8 patients, label-free statistics) | Results 3.6 Table 17 beside the final system per patient; Abstract one clause ("a fully label-free run of the review application detected 33 of 76 at 27.9 false alarms per day"); Limitations 4.5 replaces "effect not measured" with the measured −4 seizures / +5 false alarms; timing written as 21.68 s/h (controlled) + 5,862 s for 279.39 h (21.0 s/h overall, not "median") |
| O2 (A9) | Chain structure | Gaps G1–G5 in Table 1; hypotheses H1–H3 and contributions C1–C5 in 1.3 (Section 1 wording); answer sentences closing every Ch3 section; new Discussion 4.2 |
| O3 (A10) | Siena hours wording (A4 + PN14) | "PhysioNet's summary table lists about 128 h; the EDF files of the 14 patients contain 141.0 h, which is the time scored here and the base of false alarms per day. The table is shorter than the files for PN03, PN10 and PN12, whose own seizure lists agree with the files, and longer for PN14, where both the table and the seizure list give about 3 h more than its four files contain." Per-patient table in Appendix A |
| O4 (A11) | New Table 6, decision matrix for the normal reference | Yes (it carries G1/H1/C1 into Methods with development evidence) |
| O5 (A12) | Appendix numbering | Tables and figures in the appendix continue the integer numbering (AR 1); appendices titled "Appendix A: Data accounting" etc., referred to as [Appendix A] |
| O6 (A13) | Table 3 row labels | Keep the draft's labels and weeks (default), or rename three labels to the report's terms with weeks unchanged |
| O7 | Table 4 hours | Print the hours listed in the CHB-MIT summary files (566.43 / 115.82 / 279.39) with a note giving the hours scored (562.40 / 111.82 / 279.38) and why (chb12 channels; five seizure-free files of chb11 and chb21 absent from the local copy); per case in Appendix A1 |
| O8 | Figure 14 panel (e) and timing laptop | Author's check command answers the Siena location and the processor model |
