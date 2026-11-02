# STATUS_BOARD — DEFENSE phase (rev 40, 2026-11-02 22:30, chat D10-plan: after the meeting with anh Trí)

**Read this first in every chat.** Rev 40 replaces rev 39 in full. It carries every fact and decision up to 02/11,
22:30. **Now:** Track A (defense preparation for the rehearsal 03/11 09:00) **plus one parallel run only: the model
comparison** (`MODEL_COMPARISON_PLAN.md`). Track B of `V10_PLAN.md` (kNN fix, scorer study) is **suspended** (R90);
what comes after the rehearsal is decided then.

---

## 0 · Practical facts (02/11)

| item | value |
|---|---|
| Defense date | cô (02/11 17:16): **"almost certainly" moved**; new date not announced. Likely **Mon 09/11 afternoon** (cô Lụa, 02/11: "Chiều thứ 2 tuần sau kẹt hội đồng thesis") — unconfirmed until the faculty announces it. **Fallback = 05/11, 08:00** (6 students × 30 min, **Boti last, ≈ 10:30**) |
| Format | **13 min talk + 3 min demo (right after the Conclusion) + 15 min Q&A**. The Q&A checks that the student understands his own work and did not hand it to AI |
| Slide submission | fallback **04/11, 16:00** (moves with the date) |
| Rehearsal with cô | **03/11, 09:00 — kept**; ask cô for the new date |
| Results review | done with **anh Trí, 02/11 21:00** → R88–R95 |
| Report | **not read by the committee yet**; revised after the defense (`REPORT_REVISION_NOTES.md`) |

**Committee.**
- **Chair: PGS. TS. Nguyễn Thị Hiệp** — Dean, School of BME, IU; biomaterials / regenerative medicine. Not EEG/ML → plain words, clinical meaning.
- **PGS. TS. Hà Thị Thanh Hương** (supervisor) — head of the Brain Health Lab; AI for brain health (MRI, EEG); Stanford neuroscience PhD (incl. network deficits in epilepsy); 2026 ASEAN-US Science Prize for Women (AI + neuro). Wants the thesis to grow into a **real product with IP → accuracy and reliability, fewer false alarms**. Expect clinical/neuro questions.
- **TS. Ngô Thị Lụa** (reviewer) — AI. Her 12 points of 26/10 → `V9_RESULTS_SUMMARY.md` §0. Expect ML questions (why GAE, why not other models, CV design, overfitting, threshold).
- **TS. Tô (Thị) Ngọc Hân** — Dept. of Tissue Engineering & Regenerative Medicine. Not EEG/ML.

**Mentor anh Trí (02/11, two talks), paraphrased:**
- Do not be nervous; the work is broad and deep, about the level of a Q3 journal paper — **make it solid first**.
  Results need not beat other studies. Grading = **how you present, whether you understand your method, how you set up
  the experiments**; analysis beyond plain numbers sets the work apart.
- **kNN:** a memory-based score that learns nothing; a high number from it means nothing for the thesis → drop it.
  Compare with **real models that are trained and tested** (CNN, RNN, Transformer, SVM, trees, other GNNs…), designed to
  fit the problem — but first decide **what the comparison is for**, and compare only that.
- **GAE + kNN:** combining two scores to get a higher number proves nothing → **single models only**.
- **Why GAE:** show what the graph lets us see that other models cannot — links between brain regions (nodes, edges),
  graph reconstruction — through **deeper post-hoc analyses and insights**, not through ablation tables of system parts.
  Whatever channel attribution contributes, say it as it is.
- Add **one Contribution slide** that gathers these (channel attribution is now in Backup).

---

## 1 · Chat protocol

1. Now: **chat D11-A** (Track A, account 1) and **chat D11-M** (model comparison, account 2). Each works only on its
   own items (§5). **A chat never rewrites this board.**
2. End of a chat: (a) `TRACK_A_HANDBACK.md` / `MODEL_CMP_HANDBACK.md` (done, decisions, numbers with sources, open
   items); (b) changed files with exact local paths; (c) append-only additions to `NUMBERS_LOCK_S18.md` as a separate
   block. The next single chat merges them into rev 41.
3. Deliveries: **one zip (files at their local paths) + one list** of project actions; the author installs locally and
   updates the project by hand.
4. Conversation in Vietnamese; slide text and script in English (IELTS 5.5); no internal labels on slides; every number
   from `NUMBERS_LOCK.md` + `NUMBERS_LOCK_S18.md` or a committed file; computed values labelled.
5. Heavy laptop jobs: one at a time, Git Bash, browsers/MATLAB/Cursor closed; long runs overnight.

---

## 2 · Author decisions (binding; R1–R70 of earlier boards stand unless replaced here)

| # | decision |
|---|---|
| R71 | **The author's own deck is the base** (`BEBEIU22184_NguyenQuocTrungNhan_Slide Thesis_HD.pdf`, project file, 54 pages). All slide work follows **its** order, style and rules. Page map rev 10, `SLIDE_OUTLINE.md`, `D9B_CANVA_CHANGES.md`, the Slides artifact and `SCRIPT_v2.md` are retired. Format, page numbers, layout and unreviewed backup pages are left to the author unless asked |
| R72 | **Per-patient mean only** (SzCORE aggregate) on slides, script, answers and the revised report. Counts (26/76, 37/76, 33/76) stay as counts. Record files keep pooled columns as record only |
| R73 | **Minimal slides:** no header text or callout unless needed; main idea only |
| R74 | **No cross-dataset comparison at one matched FP/day.** Method comparisons on the same dataset: curve + each method's own label-free point + paired F1 bootstrap; no "@27.5" lists on main pages |
| R75 | Report revised after the defense; it constrains slides only via title/objectives |
| R77 | **The author writes the script himself**; Claude checks numbers, figures, overclaims and timing |
| R78 | cô's rule: **what the author is not yet solid on is not presented** — Backup, said only if asked |
| R79 | Q&A prepares an honest answer to **"how did you use AI tools?"** |
| R80 | cô's product goal → **reliability = fewer false alarms at the same sensitivity** |
| R81 | **Look for weaknesses in protocol and method, never blame the data** |
| R86 | Study guides updated (part 2 replaced; parts 1 and 3 patched); **Q&A files are corrected by Track A** as it finds issues — including every kNN / GAE + kNN answer (R88, R89) |
| R87 | Rehearsal 03/11 09:00 kept; 05/11 fallback date |
| **R88** | **kNN is dropped from the story** (slides, script, answers). If asked "did you try kNN?": "yes, as a baseline; kNN only measures how rare a window is inside the same recording — it learns nothing and gives no representation, so it does not answer the thesis question; we compare trained models instead". The kNN audit (B0) is **not run**; kNN numbers are not used anywhere. Replaces R83, R84 |
| **R89** | **No combined models:** GAE + kNN is removed from slides, script and answers; comparisons use **single models only** |
| **R90** | **Track B of `V10_PLAN.md` (B0, B1, B3, B4) is suspended.** After the rehearsal the author decides what comes next (candidates: the GAE insight analyses of §4, the offset rule B2). Replaces R76, R82 |
| **R91** | **Value of the GAE = what the graph lets us see**, shown by **post-hoc analyses and insights** on the graph (links between regions, nodes and edges, graph reconstruction) — **not** by ablations of system parts (latent vs reconstruction error, feature vs feature). Candidate analyses in §4; run after the rehearsal |
| **R92** | **One Contribution slide** on the main pages gathers the contributions, including channel attribution stated as what it contributes (honest wording, §4) |
| **R93** | **Model comparison** = the only run in parallel with Track A, design fixed in `MODEL_COMPARISON_PLAN.md` (purpose Q1–Q3; thesis split, no CV; single models; seed 42). **The thesis system does not change before the defense**; results enter slides only after verification |
| **R94** | **Track A first** (rehearsal 03/11), then the model comparison results; nothing else runs in parallel |
| **R95** | **The thesis system (GAE) is the headline** again (P-V9a restored; replaces R85). The GAE 24-case CV is kept (GAE only: 0.735 @ 28.4 FP/day per-case mean; trained on 17–19 patients it still finds 37/76) |

---

## 3 · Corrections on the author's deck (02/11) — Track A applies with the author

Pages as numbered in the author's PDF (may still change). Verified sources in brackets.

**Main pages**
| page | now | fix |
|---|---|---|
| p5 | "Data pipleine" | typo |
| p6 | "Patient-split: 12/3/8/**1 external**" | chb24 = "+1 unseen patient" (R66) |
| p6 | CHB-MIT "0.32 % recording" | lock: 0.33 % (23 original cases, §17c.1); 0.32 % with chb24 is not in the lock |
| p6 | Siena "0.62 % recording" | lock **0.59 %** (2,988 s / 141.0 h, §17c.1) |
| p6 | Hospital "7 technician-marked spikes" | correct, but part of **27 marked segments** (4 eyes-closed, 4 eyes-open, 2 hyperventilation, 10 photic, 7 spikes) [V9 summary §6.4] |
| p7 | "Loss: MSE between (A,A') and (X,X')" | "MSE(A) + 0.1·MSE(X); the X decoder rebuilds 12 of the 30 features" |
| p10 | "External validation: Unseen Child (chb24)" | chb24 not external (R66) |
| p12 | 4 seeds "…at **23.9** ± 1.2" / "…at **29.2** ± 1.3" (pooled FP/day) | **23.8 ± 1.3** / **28.7 ± 1.3** (per-patient, computed — S18.1) |
| p12 | "Aannotated" | typo |
| p13–17 | table header "External data" over chb24 and the review app | e.g. "Beyond the test set" |
| p13–17 | Hospital "Record 2: 6.6 % flagged (~5 min)" | verified: 3 events, 6.60 % [V9 summary §6.4]; "≈ 5 min" = 0.066 × 75 min (computed) |
| **p16** | "Detected **seizure** of patient 1" | **forbidden** → "Flagged event (no annotation)" |
| **p17** | "Detected **spike** of patient 2" | "Technician-marked spike" |
| **p18** | two lists "same FA/day (27.5)"; "kNN **matches** GAE … (F1: −0.076)"; CV curve with kNN and GAE + kNN | **remove kNN and GAE + kNN** (R88, R89) and both lists (R74). Keep the GAE CV result: 0.735 @ 28.4 FP/day (per-case mean, 24 cases, 4 folds by patient) and "trained on 17–19 patients it still finds 37/76 → not over-fitting". Later this page (or the next) takes the model comparison once verified (R93) |
| p20 | "0.508 at **22.2** FA/day" | **21.8** (per-patient) |
| p20 | "within 12 seconds" | "median onset error 12 s (4 seeds)" |
| p20 | "Missed seizures are **caused by** low amplitude, not by model design" | "Missed seizures are low-amplitude and short in all three detectors" (association) |
| p20 | "**Validated** on … Vietnamese hospital data" | "qualitative run on hospital EEG" |
| p20 | "graph connectivity adds no detection value (kNN matches GAE)" | **remove** (R88) |
| new | — | **Contribution slide** (R92, §4) before the Conclusion |
| Discussion table | "This work: 26/76 at 22.2/day" | "0.508 at 21.8/day (held-out, per-patient)" |
| Limits table | "held-out 0.342 vs final 0.487" | **0.508 vs 0.577** |
| Limits table | "Connectivity alone 0.106 vs GAE 0.342" | **0.102 vs 0.504** (per-patient, computed — S18.2) or drop |
| Limits table | "Offsets: median error 24 s (**better than onset**)" | wrong → "CPD does not improve offset (20 → 24 s); a run rule gives 16 s" |
| Limits table | "False alarms 22–44/day" (pooled) | per-patient 21.8 – 41.5 |

**Backup pages**
| page | fix |
|---|---|
| Five Representations | remove the kNN and GAE + kNN bars (R88, R89). If kept, only "same score, different inputs": GAE 0.504 · features 0.299 · Isolation Forest 0.466 · connectivity only 0.102 (per-patient, computed — S18.2); author decides keep or drop |
| Test patients per seed | Total row FA/day → 21.8 / 26.8; footnote per-patient 0.498 / 0.567 (4 seeds) |
| Seeds & Intervals | held-out 0.498 [0.226, 0.770]; final − held-out +0.070 [0.000, 0.201] → "not significant; the gain is chb15 alone" |
| Evaluation timeline | Development "0.670 at 23.3" (pooled) → per-patient 0.832 |
| Evolution / Models evaluated | record holds pooled only → label "pooled, development history" or drop the numbers |
| External validation in full | panel (a) and the "Proof" lines withdrawn (R74). "Why Siena higher": higher FA rate (41.0 vs 26.8 per-patient) and 6 of 14 patients with 1–2 seizures |
| Siena validation | "41.0 vs **27.5** FA/day" → 26.8 |
| Artifact removal | "max case (chb03) 96 %" verified (0.963) |
| Missed seizure / FA on EEG | drop "This confirms why removing artifacts destroys seizures" |
| Channel attribution | "does not map to the anatomical onset zone" → "does not match the annotated ictal channels better than a simple anatomical prior" (not SOZ) |
| Graphs & latent distance | "Graph captures how channels interact during a seizure" → keep only what an insight analysis (§4) shows |

---

## 4 · Why GAE — contribution and graph insights (R91, R92)

**Contribution slide (draft, the author edits the words):**
1. A label-free pipeline from long scalp EEG to a short list of seizure events with onset and offset (kernel CPD:
   median onset error 32 → 12 s, final, 4 seeds).
2. Each 4 s window as a brain network (CAR → wPLI + AEC, 18 channels): the GAE learns one latent per channel that
   carries the channel's own signal **and its links to other regions**; the network itself separates seizure from
   background more than the fixed-threshold graph (8 of 8 test patients, report Table 5).
3. Trained on 12 children (CHB-MIT), it runs on adults (Siena) without retraining: 0.633 @ 41.0 FP/day (4 seeds) vs
   DynaSD 0.664 @ 77.7.
4. Channel-level output: a per-channel panel for the reviewer; a blind, every-channel annotation of the 76 test seizures
   (282 labels, supervisor-approved) and a pre-registered test — the ranking is above chance (0.547, p = 0.018) but not
   better than a simple anatomical prior (0.739).
5. Measured lessons for the field: an offline timeline overestimates (rebuilt from labels); file-level drift drives
   most false alarms; artifact removal (ASR) removes seizure power too; missed seizures are low-amplitude and short.
6. A working local review tool (SzScan), label-free, ≈ 22 s per hour of EEG.

**Graph insight analyses (after the rehearsal, R90/R91; none is a result yet).** Each needs a fixed rule before
drawing, real EEG, and a number:
- **I1 · Edge reconstruction map:** the GAE rebuilds the connectivity graph (inner-product decoder, `train_gae_v2.py`).
  Which links between regions it fails to rebuild during a seizure → a network picture of each seizure (focal vs
  generalized).
- **I2 · Learned network:** Z·Zᵀ (the reconstructed graph) in background vs seizure; does it follow anatomy
  (hemisphere, lobe)?
- **I3 · Spread over the graph:** during a detected seizure, when each channel becomes anomalous — onset channels →
  graph neighbours over time.
- **I4 · Connectivity change** already measured (report Table 5): stronger seizure–background separation on 8 of 8 test
  patients (relative Frobenius +48 % to +196 %).
- **I5 · Channel attribution** as it stands (§7 of the instructions; wording above).

---

## 5 · Plan (03/11 rehearsal first)

### Track A — defense preparation (account 1, chat "D11-A")
| when | step | output |
|---|---|---|
| 02/11 night | author's script (`SCRIPT_v3`) on his deck, **Intro + Method first** | draft |
| 02/11 night | chat checks the script against the deck and the locks (numbers, figures, overclaims, §3, R71–R95); words → minutes (13:00 limit, aim 12:00–12:30 at ≈ 110 words/min) | marked script |
| 02/11 night | **hard fixes only** in Canva (§3, incl. removing kNN / GAE + kNN); Contribution slide draft (§4) | — |
| 02/11 night | **method drill** (10 questions below), aloud, ≤ 30 s each; shaky item → Backup (R78) | — |
| 03/11 09:00 | **rehearsal with cô**; ask for the new date; say the model comparison is running (no numbers) | feedback |
| 03/11 → | Q&A files corrected (R86); "how did you use AI" (R79); demo cold start + fallback video | `TRACK_A_HANDBACK.md` |

**Method drill (own words, ≤ 30 s, no slides):** (1) one 4 s window → one number, step by step; (2) what wPLI and AEC
measure, why CAR first; (3) what the GAE learns from (nodes, edges, two decoders) and why the latent distance is the
score; (4) why "normal" = the patient's whole recording, and the cost (no real time); (5) Mahalanobis + robust z, and
its limit (one Gaussian per channel); (6) why the 6th/9th/12th largest channel, not the maximum; (7) what drift
correction fixes (0.612 → 0.681, development, pooled history); (8) how the alarm budget is set without labels, why the
final system is test-informed; (9) what CPD does, why onset improves and offset not; (10) **why a graph model — what
the graph lets us see that other models cannot**, and what the model comparison asks.

### Model comparison (account 2, chat "D11-M") — the only parallel run (R93)
Design: **`MODEL_COMPARISON_PLAN.md`** (purpose Q1–Q3, protocol, models P1–P4, gates, reading). **Runs on Kaggle only;
the laptop stays free for the rehearsal** (plan §6). Deliverables: full Kaggle notebooks, committed `results/model_cmp/`, report
`F:/Study/Thesis/Agent/inbox/MODEL_CMP_REPORT.md`, `MODEL_CMP_HANDBACK.md`, an S18 append block. No numbers on slides
before verification.

---

## 6 · Start prompts

**Track A (account 1):**
> Defense track A (D11-A). Read `STATUS_BOARD.md` rev 40 (all), `DECK_BRIEF.md` (rev 5 + A90–A96), `NUMBERS_LOCK.md`
> (header, §1, §8, §17, §17c), `NUMBERS_LOCK_S18.md`, `V9_RESULTS_SUMMARY.md` rev 3, `STUDY_GUIDE_part1_vi.md` +
> `STUDY_GUIDE_part2_vi.md` rev 2, `QA_V9.md`, `Kangabu_defense_tips.md`, and my deck PDF in the project (the base — R71).
> Attached: my script draft. Tasks for the rehearsal 03/11 09:00: check the script against the deck and the locks
> (numbers, figures, overclaims, §3 list, R71–R95 — kNN and GAE + kNN removed); count words → minutes for 13:00; list
> the Canva fixes still open; draft the Contribution slide with me (§4); drill me on the 10 method questions in
> Vietnamese. Do not touch the model comparison. End with `TRACK_A_HANDBACK.md`.

**Model comparison (account 2):**
> Model comparison (D11-M). Read `STATUS_BOARD.md` rev 40 (§0, §2, §5), **`MODEL_COMPARISON_PLAN.md`** (fixed design —
> change it only with my approval and log it in its §9), `NUMBERS_LOCK_S18.md`, `VERIFIED_CORRECTIONS.md`. Clone
> github.com/Nhanvas/Thesis; read `src/retrain/train_gae_v2.py`, `src/gae_joint.py` (or where `G` is defined),
> `src/v9_e1_baselines.py` (`final_scalar_from_D`, `member_mean_z_from_D`, `evaluate_arm`), `src/v9_x3_cv_eval.py`
> (`dump_D`), `src/p3c_freeze.py`, `src/e22_test_oneshot.py`, `src/szcore_eval.py`. **Everything runs on Kaggle; my
> laptop must stay free for the rehearsal (Chrome open, no heavy job)** — plan §6. Tasks tonight: confirm the protocol in
> the code; find which inputs each step needs and which Kaggle datasets I already have (ask me, I will check on Kaggle);
> write the **complete** Kaggle notebooks (no blanks for me to fill; smoke cell first; measured runtime) for P1 and the
> P2 graph encoders, one per account, and tell me click by click how to start them as committed versions tonight.
> Verify every result before it is used. Do not touch Track A. End with `MODEL_CMP_HANDBACK.md` and an S18 append block.

---

## 7 · Files (project) and where they live locally

| file | role | local path |
|---|---|---|
| author's deck PDF | base of all slide work (R71) | `F:/Study/Thesis/Defense/slides/` |
| `STATUS_BOARD.md` (rev 40) | this board | `Code/docs/` (repo) |
| `MODEL_COMPARISON_PLAN.md` | the parallel run's fixed design | `Code/docs/` (repo) |
| `V10_PLAN.md` (suspended header) | kNN audit and scorer study — suspended (R90); kept for the record | `Code/docs/` (repo) |
| `DECK_BRIEF.md` (rev 5 + A90–A96) | slide rules on the author's deck | `Defense/outline/` |
| `NUMBERS_LOCK.md` (+ header R72) · `NUMBERS_LOCK_S18.md` | allowed numbers; per-patient recomputations (kNN rows unused, R88) | `Defense/notes/` |
| `V9_RESULTS_SUMMARY.md` (rev 3) | post-review results; §9 withdrawn conclusions (kNN parts unused, R88) | `Defense/notes/` |
| `STUDY_GUIDE_part1_vi.md` (+ patch) · `STUDY_GUIDE_part2_vi.md` (rev 2) · `STUDY_GUIDE_part3_vi.md` (+ patch) | study (kNN parts stale, R88) | `Defense/notes/` |
| `QA_V9.md`, `QA_BANK.md` (+ patch headers) | Q&A (Track A corrects) | `Defense/qa/` |
| `DEMO_SCRIPT.md` (+ patch), `APP_FACTS.md`, `GATE.md`, `TIMING.md`, `DEMO_FINAL_HANDBACK.md` | demo | `Defense/script/`, `Defense/notes/` |
| `REPORT_REVISION_NOTES.md` | report changes after the defense (kNN rows obsolete, R88) | `Defense/notes/` |
| `VERIFIED_CORRECTIONS.md` (+ V10 block) | findings not to rediscover | `Code/docs/` |
| record files (PERF_PHASE_RECORD, HANDOFF_REPORT, PROVENANCE, PROVENANCE_V2, RESULTS_OF_RECORD_phaseB, ATTRIBUTION_SPEC, Thesis_Reference_Sheet, CLAIM_AUDIT_v8, Thesis_Final_Report, Registration Form, p2_ledger.csv, REPRODUCE, RUBRIC_MAP, FIGURE_INDEX, Kangabu tips, THESIS_REPORT_WRITING_GUIDE) | unchanged; pooled = record only (R72) | as before |

## 8 · Decisions log
- rev 22–36: see git. rev 37–38 (02/11): format, committee, R71–R84, deck corrections, per-patient recomputations,
  method review, kNN audit, two tracks.
- rev 39 (02/11 evening): full project reset; R85–R87.
- **rev 40 (02/11 22:30):** meeting with anh Trí → R88 kNN dropped (replaces R83, R84), R89 single models only, R90 V10
  Track B suspended (replaces R76, R82), R91 GAE value via graph insight analyses, R92 Contribution slide, R93 model
  comparison as the only parallel run (`MODEL_COMPARISON_PLAN.md`), R94 Track A first, R95 GAE headline restored
  (replaces R85).
