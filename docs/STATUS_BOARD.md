# STATUS_BOARD — DEFENSE phase (rev 39, 2026-11-02 evening, chat D10-plan: full project reset, two parallel tracks)

**Read this first in every chat.** Rev 39 replaces rev 36–38 in full. It carries every fact and decision up to 02/11
evening, so no earlier chat needs to be re-read. Two chats now run **in parallel** (possibly on two accounts with no
shared memory): **Track A = defense preparation**, **Track B = method fix** (design in `V10_PLAN.md`).

---

## 0 · Practical facts (02/11)

| item | value |
|---|---|
| Defense date | cô (02/11 17:16): **"almost certainly" moved**; new date not announced. Likely **Mon 09/11 afternoon** (cô Lụa, 02/11: "Chiều thứ 2 tuần sau kẹt hội đồng thesis") — unconfirmed until the faculty announces it. **Fallback = 05/11, 08:00** (6 students × 30 min, **Boti last, ≈ 10:30**) → aim to finish both tracks **before 05/11** |
| Format | **13 min talk + 3 min demo (right after the Conclusion) + 15 min Q&A**. The Q&A checks that the student understands his own work and did not hand it to AI |
| Slide submission | fallback **04/11, 16:00** (moves with the date) |
| Rehearsal with cô | **03/11, 09:00 — kept** |
| Results review | cô asked **anh Trí** to review the results with Boti — **02/11, 21:00**. cô: *is the kNN implemented correctly? is the gain due to good features?* Anh Trí: *why kNN, why not SVM or trees?* (answers: `V10_PLAN.md` §1–§2) |
| Report | **not read by the committee yet**; revised after the defense (`REPORT_REVISION_NOTES.md`); constrains the slides only through the registered title and objectives |

**Committee.**
- **Chair: PGS. TS. Nguyễn Thị Hiệp** — Dean, School of BME, IU; biomaterials / regenerative medicine. Not EEG/ML → plain words, clinical meaning.
- **PGS. TS. Hà Thị Thanh Hương** (supervisor) — head of the Brain Health Lab; AI for brain health (MRI, EEG); Stanford neuroscience PhD (incl. network deficits in epilepsy); 2026 ASEAN-US Science Prize for Women (AI + neuro). Wants the thesis to grow into a **real product with IP → accuracy and reliability, fewer false alarms**. Expect clinical/neuro questions.
- **TS. Ngô Thị Lụa** (reviewer) — AI (author 02/11). Her 12 points of 26/10 → `V9_RESULTS_SUMMARY.md` §0. Expect ML questions (why GAE, why Mahalanobis, why kNN, CV design, overfitting, threshold).
- **TS. Tô (Thị) Ngọc Hân** — Dept. of Tissue Engineering & Regenerative Medicine. Not EEG/ML.

**Mentor anh Trí (02/11), paraphrased:** do not be nervous; the work is broad and deep. Results need not beat other
studies — a little lower is fine. Grading = **how you present, whether you understand your method, how you set up the
experiments**, and the effort; the analysis beyond plain numbers is what sets the work apart.

---

## 1 · Chat protocol (parallel phase)

1. Two tracks run at once; each works only on its own items (§5). **A track never rewrites this board.**
2. **End of a track:** it delivers (a) `TRACK_A_HANDBACK.md` / `TRACK_B_HANDBACK.md` (done, decisions, numbers with
   sources, open items); (b) changed files with exact local paths; (c) append-only additions to `NUMBERS_LOCK_S18.md` as
   a separate block.
3. The author uploads deliverables once per finished track. **The next single chat merges both handbacks into rev 40.**
4. Deliveries: **one zip (files at their local paths) + one list** of project actions (add / replace / delete / paste);
   the author installs locally and updates the project by hand (author 02/11).
5. Conversation in Vietnamese; slide text and script in English (IELTS 5.5); no internal labels on slides; every number
   from `NUMBERS_LOCK.md` + `NUMBERS_LOCK_S18.md` or a committed file; computed values labelled.
6. Heavy laptop jobs: one at a time, Git Bash, browsers/MATLAB/Cursor closed → Track B's long runs go **overnight**.

---

## 2 · Author decisions (binding; R1–R70 of earlier boards stand unless replaced here)

| # | decision (02/11) |
|---|---|
| R71 | **The author's own deck is the base** (`BEBEIU22184_NguyenQuocTrungNhan_Slide_Thesis_HD.pdf`, 54 pages, ≈ 70–80 % done, built in the author's logic). All slide work follows **its** order, style and rules. Page map rev 10, `SLIDE_OUTLINE.md`, `D9B_CANVA_CHANGES.md`, the Slides artifact and `SCRIPT_v2.md` are **retired**. Format, page numbers, layout and unreviewed backup pages are left to the author — not commented on unless asked |
| R72 | **Per-patient mean only** (SzCORE aggregate = mean of per-subject sensitivity, precision, F1, FP/day) on slides, script, answers and the revised report. Pooled values are recomputed per-patient or removed. Counts (26/76, 37/76, 33/76) stay as counts. Record files keep their pooled columns as record only |
| R73 | **Minimal slides:** no header text or callout unless needed; main idea only |
| R74 | **No cross-dataset comparison at one matched FP/day.** Method comparisons on the same dataset: full curve + each method's own label-free operating point + paired F1 bootstrap; no "@27.5" lists on main pages |
| R75 | Report revised after the defense; it constrains slides only via title/objectives |
| R76 | **Research reopened for Track B only** (`V10_PLAN.md`); defense prep continues in Track A; a verified better result enters the slides before the defense, otherwise it becomes an insight / future-work page. Track A never waits for Track B |
| R77 | **The author writes the script himself** from his deck; Claude checks numbers, figures, overclaims and timing |
| R78 | cô's rule: **what the author is not yet solid on is not presented** — it goes to Backup and is said only if asked |
| R79 | Q&A prepares an honest answer to **"how did you use AI tools?"** (AI for code and drafting; design choices, failures and decisions are the author's — 2–3 concrete examples) |
| R80 | cô's product goal → **reliability = fewer false alarms at the same sensitivity** |
| R81 | **Look for weaknesses in protocol and method, never blame the data.** "The test patients are harder" stays a measured fact, not the explanation of choice |
| R82 | Date moving → **Track B is the priority**; Track A keeps the rehearsal and the method understanding, fixes hard errors only, and does not polish result pages until Track B decides |
| R83 | **Audit and fix the kNN implementation before using kNN results further** (cô 02/11) → B0 |
| R84 | "Why kNN, not other models?": supervised SVM/trees need the patient's labels (outside the problem; supervised reference exists); their **unsupervised** counterparts are compared on the same inputs (B1) |
| R85 | **P-V9a ("GAE is always the headline") is suspended** until B1's pre-registered decision rule decides |
| R86 | Study guides are updated now (part 2 replaced; part 1 and 3 patched); **Q&A files are corrected by Track A as it finds issues** (patch headers mark what is stale) |
| R87 | Rehearsal 03/11 09:00 is kept; 05/11 is the fallback date; both tracks aim to finish before 05/11 |

---

## 3 · Corrections on the author's deck (02/11) — Track A applies with the author

Pages as numbered in the author's PDF (may still change). Verified sources in brackets.

**Main pages**
| page | now | fix |
|---|---|---|
| p5 | "Data pipleine" | typo |
| p6 | "Patient-split: 12/3/8/**1 external**" | chb24 = "+1 unseen patient" (R66) |
| p6 | CHB-MIT "0.32 % recording" | lock: 0.33 % (23 original cases, §17c.1); 0.32 % with chb24 is not in the lock → use 0.33 % (23 cases) or give the source |
| p6 | Siena "0.62 % recording" | lock **0.59 %** (2,988 s / 141.0 h, §17c.1) |
| p6 | Hospital "7 technician-marked spikes" | correct, but part of **27 marked segments** (4 eyes-closed, 4 eyes-open, 2 hyperventilation, 10 photic, 7 spikes) [V9 summary §6.4] |
| p7 | "Loss: MSE between (A,A') and (X,X')" | "MSE(A) + 0.1·MSE(X); the X decoder rebuilds 12 of the 30 features" |
| p10 | "External validation: Unseen Child (chb24)" | chb24 not external (R66) |
| p12 | 4 seeds "…at **23.9** ± 1.2" / "…at **29.2** ± 1.3" (pooled FP/day) | **23.8 ± 1.3** / **28.7 ± 1.3** (per-patient, computed — S18.1) |
| p12 | "Aannotated" | typo |
| p13–17 | table header "External data" over chb24 and the review app | e.g. "Beyond the test set" |
| p13–17 | Hospital "Record 2: 6.6 % flagged (~5 min)" | verified: clin02 3 events, 6.60 % [V9 summary §6.4]; "≈ 5 min" = 0.066 × 75 min (computed) |
| **p16** | "Detected **seizure** of patient 1" | **forbidden** → "Flagged event (no annotation)" |
| **p17** | "Detected **spike** of patient 2" | "Technician-marked spike" |
| p18 | two lists "same FA/day (27.5)": 0.106 / 0.342 / 0.467 (pooled, detector stage) and 0.554 / 0.601 / 0.607 (per-patient, system stage) | **remove both** (R74); keep the CV curve + 2–3 lines. Wording of those lines waits for B0 (kNN numbers may change) |
| p18 | "kNN **matches** GAE … (F1: −0.076)" | understates: kNN has **higher** F1 (pending B0) |
| p20 | "0.508 at **22.2** FA/day" | **21.8** (per-patient) |
| p20 | "within 12 seconds" | "median onset error 12 s (4 seeds)" |
| p20 | "Missed seizures are **caused by** low amplitude, not by model design" | "Missed seizures are low-amplitude and short in all three detectors" (association, not proven cause) |
| p20 | "**Validated** on … Vietnamese hospital data" | "qualitative run on hospital EEG" |
| p20 | "graph connectivity adds no detection value (kNN matches GAE)" | pending B0/B1 — keep the wording neutral until then |
| Discussion table | "This work: 26/76 at 22.2/day" | "0.508 at 21.8/day (held-out, per-patient)" |
| Limits table | "held-out 0.342 vs final 0.487" | **0.508 vs 0.577** |
| Limits table | "Connectivity alone 0.106 vs GAE 0.342" | **0.102 vs 0.504** (per-patient, computed — S18.2) |
| Limits table | "Offsets: median error 24 s (**better than onset**)" | wrong → "CPD does not improve offset (20 → 24 s); a run rule gives 16 s" |
| Limits table | "False alarms 22–44/day" (pooled) | per-patient 21.8 – 41.5 |

**Backup pages**
| page | fix |
|---|---|
| Five Representations | per-patient bars (computed, S18.2): kNN 0.588 · GAE + kNN 0.552 · GAE 0.504 · Isolation Forest 0.466 · Mahalanobis 0.299 · connectivity only 0.102 (kNN rows pending B0) |
| Test patients per seed | Total row FA/day → 21.8 / 26.8; footnote per-patient 0.498 / 0.567 (4 seeds) |
| Seeds & Intervals | per-patient: held-out 0.498 [0.226, 0.770]; final − held-out +0.070 [0.000, 0.201]. "Lower bound zero means … driven by one patient" is a non sequitur → "not significant; the gain is chb15 alone" |
| Evaluation timeline | Development "0.670 at 23.3" (pooled) → per-patient 0.832 (per-patient FP/day: open, S18.5) |
| Evolution / Models evaluated | record holds pooled only → author chooses: label "pooled, development history" or drop the numbers |
| External validation in full | panel (a) and the "Proof" lines **withdrawn** (R74, S18.3). "Why Siena higher": higher FA rate (41.0 vs 26.8 per-patient) and 6 of 14 patients with 1–2 seizures |
| Siena validation | "41.0 vs **27.5** FA/day" → 26.8 |
| Artifact removal | "max case (chb03) 96 %" verified (0.963, V9 summary §6.2) |
| Missed seizure / FA on EEG | drop "This confirms why removing artifacts destroys seizures" (overclaim) |
| Channel attribution | "does not map to the anatomical onset zone" → "does not match the annotated ictal channels better than a simple anatomical prior" (not SOZ) |
| Graphs & latent distance | "Graph captures how channels interact during a seizure" → soften or drop |

---

## 4 · Method review (02/11) → Track B

Full design, evidence and pre-registered hypotheses: **`V10_PLAN.md`** (the single source for Track B). Summary:
- **Main weakness = the scorer:** Mahalanobis assumes one Gaussian "normal" state; same features, Mahalanobis 0.299 vs
  kNN 0.588 (per-patient, computed). kNN on the GAE latent never tested. kNN = scoring rule, title unchanged.
- **kNN audit (cô's question):** two real flaws — the ±60 s exclusion compares in-file time without the file id;
  calibration asymmetry (kNN 23 cases vs GAE 17–19). Fix first (B0).
- **B1** scorer × representation study (Mahalanobis, Gaussian mixture, kNN ± exclusion, Isolation Forest, One-Class SVM ×
  channel features / GAE latent) with H1–H4 and a decision rule. **B2** offset rule. **B3/B4** only if the date allows.
- **Siena vs CHB-MIT at one matched rate** is withdrawn (per-patient 0.540 vs 0.519).

---

## 5 · Plan — two parallel tracks

### Track A — defense preparation (account 1, chat "D10-A")
| when | step | output |
|---|---|---|
| 02/11 eve | author writes `SCRIPT_v3` on his deck, **Intro + Method first** (they will not change) | draft |
| 02/11 eve | chat checks the script against the deck and the locks (numbers, figures, overclaims, §3, R71–R87); word count → minutes (13:00 limit, aim 12:00–12:30 at ≈ 110 words/min) | marked script |
| 02/11 eve | **hard fixes only** in Canva (§3 main pages); no redesign of result pages | — |
| 02/11 | **method drill** (10 questions below), aloud, ≤ 30 s each; shaky item → Backup (R78) | — |
| 03/11 09:00 | **rehearsal with cô** on the current deck; ask cô for the new date | feedback |
| 03/11 → | Q&A files corrected as issues appear (R86); "how did you use AI" answer (R79); demo cold start + fallback video | `TRACK_A_HANDBACK.md` |
| 04/11 | add Track B result if verified (V10_PLAN §3 decision rule); `xanh` number check; timed read | deck |

**Method drill (own words, ≤ 30 s, no slides):** (1) one 4 s window → one number, step by step; (2) what wPLI and AEC
measure, why CAR first; (3) what the GAE learns from, why the latent and not the reconstruction error; (4) why "normal"
= the patient's whole recording, and the cost (no real time); (5) Mahalanobis + robust z — and why one Gaussian is the
weak point; (6) why the 6th/9th/12th largest channel, not the maximum; (7) what drift correction fixes (0.612 → 0.681);
(8) how the alarm budget is set without labels, why the final system is test-informed; (9) what CPD does, why onset
improves and offset not; (10) what "kNN ≥ GAE" says about the graph idea, and the honest answer.

### Track B — method fix (account 2, chat "D10-B") — priority (R82)
Steps, timeline, gates and decision rule: **`V10_PLAN.md` §2–§7**. Deliverables: `docs/prompts/V10_B0_KNN_FIX.md`,
`docs/prompts/V10_B1_SCORERS.md`, committed `results/v10_b0/`, `results/v10_b1/`, reports in
`F:/Study/Thesis/Agent/inbox/`, `TRACK_B_HANDBACK.md`, an S18 append block.

---

## 6 · Start prompts

**Track A (account 1):**
> Defense track A (D10-A). Read `STATUS_BOARD.md` rev 39 (all), `DECK_BRIEF.md` rev 5, `NUMBERS_LOCK.md` (header,
> §1, §8, §17, §17c), `NUMBERS_LOCK_S18.md`, `V9_RESULTS_SUMMARY.md` rev 3, `STUDY_GUIDE_part1_vi.md` +
> `STUDY_GUIDE_part2_vi.md` rev 2, `QA_V9.md`, `Kangabu_defense_tips.md`. Attached: my deck PDF (the base — R71) and my
> script draft. Tasks: check the script against the deck and the locks (numbers, figures, overclaims, §3 list,
> R71–R87); count words → minutes for 13:00; list the Canva fixes still open; drill me on the 10 method questions in
> Vietnamese. Do not touch Track B. End with `TRACK_A_HANDBACK.md`.

**Track B (account 2):**
> Method track B (D10-B). Read `STATUS_BOARD.md` rev 39 (§0, §2, §4), **`V10_PLAN.md`** (the pre-registered design — change it
> only with my approval and log it in its §8), `NUMBERS_LOCK_S18.md`, `V9_RESULTS_SUMMARY.md` rev 3 (§2–§5, §9),
> `VERIFIED_CORRECTIONS.md`. Clone github.com/Nhanvas/Thesis; read `src/v9_e1_baselines.py` (`d_knn`, `load_raw12_18`,
> `file_start_offsets`), `src/v9_e4_knn24.py`, `src/v9_x3_knn_b4.py`, `src/v9_x3_cv_eval.py` (`dump_D`, calibration),
> `src/v9_e1b_calibrate.py`, `src/v9_x3_sys_sweep.py`, `results/v9_x3/SUMMARY.md`. Tasks: confirm the B0 findings in the
> code; write `docs/prompts/V10_B0_KNN_FIX.md` for Claude Code on my laptop (gate first, smoke, resumable, single worker,
> measured runtime, report to `F:/Study/Thesis/Agent/inbox/V10_B0_REPORT.md`, commit `results/v10_b0/`); after B0, the B1
> prompt the same way; verify every result before it is used; B2 in the container. Do not touch Track A. End with
> `TRACK_B_HANDBACK.md` and an S18 append block.

---

## 7 · Files (project) and where they live locally

| file | role | local path |
|---|---|---|
| author's deck PDF | base of all slide work (R71) | `F:/Study/Thesis/Defense/slides/` |
| `STATUS_BOARD.md` (rev 39) | this board | `Code/docs/` (repo) |
| `V10_PLAN.md` | Track B pre-registered design | `Code/docs/` (repo) |
| `DECK_BRIEF.md` (rev 5) | slide rules on the author's deck | `Defense/outline/` |
| `NUMBERS_LOCK.md` (+ header R72) · `NUMBERS_LOCK_S18.md` | allowed numbers; per-patient recomputations | `Defense/notes/` |
| `V9_RESULTS_SUMMARY.md` (rev 3) | post-review results; §9 withdrawn conclusions | `Defense/notes/` |
| `STUDY_GUIDE_part1_vi.md` (+ patch header) · `STUDY_GUIDE_part2_vi.md` (rev 2) · `STUDY_GUIDE_part3_vi.md` (+ patch header) | study | `Defense/notes/` |
| `QA_V9.md`, `QA_BANK.md` (+ patch headers) | Q&A (Track A corrects) | `Defense/qa/` |
| `DEMO_SCRIPT.md` (+ patch header), `APP_FACTS.md`, `GATE.md`, `TIMING.md`, `DEMO_FINAL_HANDBACK.md` | demo | `Defense/script/`, `Defense/notes/` |
| `REPORT_REVISION_NOTES.md` (rewritten 02/11) | report changes after the defense | `Defense/notes/` |
| `VERIFIED_CORRECTIONS.md` (+ V10 block) | findings not to rediscover | `Code/docs/` |
| record files (PERF_PHASE_RECORD, HANDOFF_REPORT, PROVENANCE, PROVENANCE_V2, RESULTS_OF_RECORD_phaseB, ATTRIBUTION_SPEC, Thesis_Reference_Sheet, CLAIM_AUDIT_v8, Thesis_Final_Report, Registration Form, p2_ledger.csv, REPRODUCE, RUBRIC_MAP, FIGURE_INDEX, Kangabu tips, THESIS_REPORT_WRITING_GUIDE) | unchanged; pooled columns = record only (R72) | as before |
| retired (removed from the project; kept in `Archive/2026-11-02-d10/`) | SLIDE_OUTLINE, D9B_CANVA_CHANGES, SCRIPT_v2, QA_PAGE_MAP, D5_HANDOFF, BRIEFING_2026-10-08_vi, BME11 template | — |

## 8 · Decisions log
- rev 22–36: see git.
- **02/11 (rev 37–38, superseded):** format 13 + 3 + 15; committee; R71–R84; deck corrections; per-patient recomputations;
  Siena matched comparison withdrawn; method review; kNN audit; two tracks.
- **02/11 evening (rev 39):** full project reset (instructions, board, DECK_BRIEF rev 5, V9 summary rev 3, V10_PLAN,
  S18, study guide part 2 rev 2, patch headers, report notes); R85 P-V9a suspended; R86 study guides now, Q&A by Track A;
  R87 rehearsal kept, 05/11 fallback; deliveries = zip + list.
