# STATUS_BOARD — DEFENSE phase (rev 42, 2026-11-05 10:30, chat D11-M: merge of `MODEL_CMP_HANDBACK` + `TRACK_A_HANDBACK` (D11-A, 03/11) incl. its S18 rows and QA patch; Track F opened)

**Read this first in every chat.** Rev 42 replaces rev 40 and the unpublished rev 41 in full. It carries every fact and
decision up to 05/11, 09:30, including the Track A handback of chat D11-A (03/11, 01:00–02:00) and a check of the
**submitted deck** (59 pages) against the locks (§3). **Now:** Track A (defense preparation for **09/11**) **plus one
parallel research track: Track F** (`FUTURE_RESEARCH_PLAN.md`, Kaggle only). Rehearsal 03/11 feedback other than cô's
04/11 comment is not recorded here; Track A adds it to its next handback.

---

## 0 · Practical facts (05/11)

| item | value |
|---|---|
| Defense date | **Mon 09/11** (moved; author 05/11). Exact time and order: to be confirmed by the faculty |
| Format | **13 min talk + 3 min demo (right after the Conclusion) + 15 min Q&A**. The Q&A checks that the student understands his own work and did not hand it to AI |
| Slides | **submitted 04/11** (project file `BEBEIU22184_NguyenQuocTrungNhan.pdf`, 59 pages: 32 main incl. References and Thank you, 27 backup). Content changes now only if the author decides; numbers stay under the locks; issues still in the submitted file: §3 |
| Rehearsal with cô | held 03/11 09:00. Known feedback (cô 04/11): internal validation should average over several random patient splits, not rely on one fixed set → Track F1 |
| Results review | anh Trí 02/11 21:00 → R88–R95 |
| Report | not read by the committee yet; revised after the defense (`REPORT_REVISION_NOTES.md`) |
| Kaggle | 4 accounts (Nhân2mm, nhannguyen26, Nhancoding, Norn Creades), 30 GPU h per week each; datasets `v9-x3-fold1…4` public |

**Committee.**
- **Chair: PGS. TS. Nguyễn Thị Hiệp** — Dean, School of BME, IU; biomaterials / regenerative medicine. Not EEG/ML → plain words, clinical meaning.
- **PGS. TS. Hà Thị Thanh Hương** (supervisor) — head of the Brain Health Lab; AI for brain health (MRI, EEG); network deficits in epilepsy. Wants a **real product with IP → accuracy and reliability, fewer false alarms**.
- **TS. Ngô Thị Lụa** (reviewer) — AI. Her 12 points of 26/10 → `V9_RESULTS_SUMMARY.md` §0. Expect ML questions (why GAE, why not other models, CV design, overfitting, threshold).
- **TS. Tô (Thị) Ngọc Hân** — Tissue Engineering & Regenerative Medicine. Not EEG/ML.

**Mentor anh Trí (02/11), paraphrased:** make it solid; grading = presentation, understanding of the method, experiment
design; kNN means nothing → dropped; compare real trained models for a stated purpose; single models only; show the
GAE's value through post-hoc graph insights; one Contribution slide.

---

## 1 · Chat protocol

1. Now: **Track A** (defense prep, account 1) and **Track F** (future research, account 2). Each works only on its own
   items (§5). **A chat never rewrites this board**; it ends with a handback; a single merge chat writes rev + 1.
2. End of a chat: (a) `TRACK_A_HANDBACK.md` / `TRACK_F_HANDBACK.md`; (b) changed files with exact local paths;
   (c) S18 additions **as the whole new `NUMBERS_LOCK_S18.md`**, not as a paste-block.
3. Deliveries: one zip (files at their local paths) + install `.sh` + **one complete list** of project actions;
   **every changed project file is delivered whole, ready to replace** (author 04/11).
4. Conversation in Vietnamese; slide text and script in English (IELTS 5.5); no internal labels on slides; every number
   from `NUMBERS_LOCK.md` + `NUMBERS_LOCK_S18.md` or a committed file; computed values labelled.
5. Heavy jobs on Kaggle (complete notebooks, smoke first, measured runtime); the laptop stays free for the defense prep.

---

## 2 · Author decisions (binding; R1–R70 of earlier boards stand unless replaced here)

| # | decision |
|---|---|
| R71 | **The author's own deck is the base** of all slide work; earlier outlines and artifacts retired |
| R72 | **Per-patient mean only** (SzCORE aggregate) on slides, script, answers and the revised report; counts stay as counts; record files keep pooled columns as record only |
| R73 | **Minimal slides:** no header text or callout unless needed; main idea only |
| R74 | **No cross-dataset comparison at one matched FP/day.** Same-dataset method comparisons: curve + each method's own label-free point + paired F1 bootstrap |
| R75 | Report revised after the defense; it constrains slides only via title/objectives |
| R77 | **The author writes the script himself**; Claude checks numbers, figures, overclaims and timing |
| R78 | cô's rule: **what the author is not yet solid on is not presented** — Backup, said only if asked |
| R79 | Q&A prepares an honest answer to **"how did you use AI tools?"** |
| R80 | cô's product goal → **reliability = fewer false alarms at the same sensitivity** |
| R81 | **Look for weaknesses in protocol and method, never blame the data** |
| R86 | Q&A files are corrected by Track A, including every kNN / GAE + kNN answer |
| R88 | **kNN is dropped from the story**; if asked: "a baseline that only measures rarity inside the same recording; it learns nothing; we compare trained models instead" |
| R89 | **No combined models**; comparisons use single models only |
| R90 | `V10_PLAN.md` is suspended; **superseded by `FUTURE_RESEARCH_PLAN.md`** (R100) |
| R91 | **Value of the GAE = what the graph lets us see**, shown by post-hoc graph insight analyses, not by ablations of system parts |
| R92 | **One Contribution slide** gathers the contributions (honest wording, §4) |
| R93 | **The thesis system and the demo do not change before the defense** |
| R95 | **The thesis system (GAE) is the headline**; the GAE 24-case CV is kept (0.735 @ 28.4 FP/day per-case mean) |
| **R96** | **Model comparison closed (04/11, verified):** six single models on the 4-fold CV (`MODEL_CMP_ANALYSIS.md`, S18 §18.6). Only the MLP autoencoder (GAE without message passing) differs from the GAE in F1 (+0.070 [+0.026, +0.117]; same 115 seizures, 27 % fewer false alarms); labels (SVM, trees, CNN) give no clear gain; all models miss the same weak, short seizures. → never claim that the graph improves detection |
| **R97** | Slides submitted 04/11; **defense 09/11** |
| **R98** | **Track F** (`FUTURE_RESEARCH_PLAN.md`) runs in parallel on Kaggle; its results enter **Q&A answers only after verification** and never the submitted slides; otherwise they are future work and go into the revised report |
| **R99** | cô 04/11: repeated random patient partitions (training and testing on several random splits, averaged) → Track F1/F2; LOSO stays future work |
| **R100** | `V10_PLAN.md` B2 (offset rule), B3 (features for weak seizures), B4 (loss weight) move to `FUTURE_RESEARCH_PLAN.md` (F5, F6; B4 dropped unless F3 points to it); B0/B1 (kNN) stay dropped |
| **R101** | Changed project files are delivered whole, never as paste-blocks |
| **R102** | **Chung's protocol (secondary analysis) is said as the count "27/48"** (the 0.562 is pooled = 27/48; R72) — Track A finding 03/11 |
| **R103** | Track A structure (D11-A §3) as applied by the author in the submitted deck: Siena SzCORE comparison on a main page (p28), six-model comparison (p26), Contributions and Limits → future work together on the Conclusion page (p30); Onset/Offset stayed in backup (p33) (`DECK_BRIEF.md` A97–A99) |
| **R104** | If the committee opens a backup page with a number or claim listed in §3 as not allowed, the author says the allowed number or reading instead (prepared in Track A) — the submitted file is not changed unless the faculty allows a final version |

---

## 3 · The submitted deck (04/11) — checked 05/11 against the locks and the Track A handback

**Main pages (1–32):** the Track A structure is in (R103); kNN and GAE + kNN are gone from the main pages; Contributions and
limits (p30), the six-model comparison (p26) and the Siena SzCORE table (p28) are present. Remaining small items: p26
caption "24 ca" → "24 cases", "Senstivity", "modelss"; p19 "patientt"; p9/p16 "Kernel CDP" → "CPD"; p13 "Cut Seizure
label out the recording" (only training patients' seizure windows are left out of training; z-score statistics of
CHB-MIT exclude seizures — disclosed); p19 and p21 put a per-patient mean beside a count (0.508 (26/76), 0.748 (33/47))
— say "per-patient mean; 26 of 76 seizures".

**Backup pages still carrying numbers or claims that are not allowed (say the allowed version if shown, R104):**
| page | in the file | say instead |
|---|---|---|
| p37 Missed seizure / false alarm | "This confirms why removing artifacts (like ASR) destroys seizures" | drop the sentence; ASR evidence is p36 |
| p39 Comparison with other studies | "This work … 26/76 at 22.2/day (held-out)" | 26/76, 0.508 at 21.8 FP/day (held-out, per-patient) |
| p43 Graphs & latent distance | "Graph captures how channels interact during a seizure"; AUROC 0.527 / 0.966; 0.622 vs 0.553 | only what is measured; never "the graph improves detection" (R96) |
| p46 Siena validation | "Duration mix" reason; "41.0 vs 27.5 FA/day" | reasons: higher FA rate (41.0 vs 26.8 per-patient) and 6 of 14 patients with 1–2 seizures (0.633 → 0.530) |
| p47 Test patients per seed | Total row 22.2 / 27.5 FA/day; pooled 0.336 ± 0.008 / 0.477 ± 0.022 | per-patient 21.8 / 26.8; 4 seeds 0.498 ± 0.010 / 0.567 ± 0.019 |
| p51 Evaluation timeline | Development "0.670 at 23.3 FA/day" (pooled) | development 0.832 (per-patient, 4 seeds) |
| p53 Seeds & Intervals | figure drawn from pooled values (Track A finding 3) | per-patient: held-out 0.498 [0.226, 0.770]; final − held-out +0.070 [0.000, 0.201]; redrawn figure `Defense/slides/figs/d11a/backup_seeds_intervals_perpatient.png` |
| p55 Data difficulty | "Even an untrained kNN shows a massive gap … 86.6 % vs 56.5 %"; "chb14 … found 8/8" | kNN not used (R88); the GAE finds chb14 6/8; "test patients are harder" via the GAE CV: 8 test patients 0.581 vs other 16 cases 0.812 |
| p56 External validation in full | "At 27.5 FA/day: Siena 0.534 vs CHB-MIT 0.355 — Proof"; "duration mix … 0.576" | withdrawn (R74); same answer as p46 |
| p58 Evolution | "Held-out: sens 0.342 (26/76) at 22.2 FA/day"; "73.3 to 22.2" | held-out 0.508 (26/76) at 21.8 FP/day per-patient; earlier system 23/76 at 73.3 is pooled, record only |
| p59 Models evaluated | "Development result" column pooled (0.670 @ 23.3, 0.702 @ 20.5) | label "pooled, development history" if asked |

**Track A findings 03/11 not visible in the text (author confirms):** p20 EEG panels (chb03_35 / chb15_54 / chb14_26) vs
the rule-selected pack of `FIGURE_INDEX.md` (chb03 / chb06_18 / chb14_29) — which rule drew them; script items "42 h"
(= axis length → 40.6 h), "overlapping" windows (they are non-overlapping), "1 external" (chb24 is one more unseen
CHB-MIT patient).

---

## 4 · Why GAE — contribution and graph insights (R91, R92, R96)

**Contribution slide (the author's words decide; constraint from R96):**
1. A label-free pipeline from long scalp EEG to a short list of seizure events with onset and offset (kernel CPD: median
   onset error 32 → 12 s, final, 4 seeds).
2. Each 4 s window as a brain network (CAR → wPLI + AEC); the GAE learns one latent per channel from the channel's own
   signal and its connectivity row. **Not:** "the graph improves detection" — a same-input autoencoder without graph
   propagation found the same seizures with fewer false alarms (R96).
3. Trained on 12 children (CHB-MIT), it runs on adults (Siena) without retraining: 0.633 @ 41.0 FP/day (4 seeds) vs
   DynaSD 0.664 @ 77.7.
4. Channel-level output and a blind, every-channel annotation of the 76 test seizures with a pre-registered test: above
   chance (0.547, p = 0.018), not better than a simple anatomical prior (0.739).
5. Measured lessons: an offline timeline overestimates; file-level drift drives most false alarms; ASR removes seizure
   power too; missed seizures are low-amplitude and short — **in all six compared models**, supervised included.
6. A working local review tool (SzScan), label-free, ≈ 22 s per hour of EEG.

**Honest answer "why a graph?" (Q&A):** "In our cross-validation an autoencoder with the same input but without graph
propagation found the same seizures with fewer false alarms. So the graph does not improve detection; we keep the GAE
as the thesis system and study what the graph shows as future work." (`MODEL_CMP_ANALYSIS.md` §6.)

**Graph insight analyses:** now Track F4 (I1 edge reconstruction map, I2 learned network vs anatomy, I3 spread), run on
**both** autoencoders because both rebuild the graph; only what differs is attributed to message passing.

---

## 5 · Plan to 09/11

### Track A — defense preparation (account 1)
| when | step |
|---|---|
| 05–07/11 | script (author) on the submitted deck, from `Defense/script/SCRIPT_v3_marked.md` (D11-A: 1,371 spoken words = 12.5 min at 110 wpm, 13.7 min at 100 wpm → author measures his own pace once; first cuts if slow: p2 line, preprocessing sentence); [NEW] parts rewritten in his own words (A99); timed read ≤ 13:00 |
| 05–07/11 | answers for every backup issue of §3 (R104) |
| 05–07/11 | Q&A corrections incl. the new questions: "why a graph?", "why not SVM / trees / CNN?", "why is CV 0.735 higher than test 0.508 / 0.577?" (CV on the 8 test patients = 0.581, 37/76), "why not repeated random splits?" (Track F1, future work), "how did you use AI?" |
| 07–08/11 | method drill (`Defense/notes/METHOD_DRILL_D11A_vi.md`, + "why a graph" with R96); Q20 "how did you use AI" rewritten by the author so it is exactly true; demo cold start + fallback video |
| 09/11 | defense |

### Track F — future research (account 2; `FUTURE_RESEARCH_PLAN.md`)
| when | step |
|---|---|
| 05/11 (chat F1) | verify plan rev 0 in the code; decide O1–O7 with the author; partitions committed; notebooks written and tested on synthetic data; plan rev 1 fixed |
| 05–08/11 | F1/F2 Kaggle runs (GAE + MLP-AE on R random partitions); F5 offset analysis in the container meanwhile |
| after the runs | verification (gates, per-subject tables, bootstrap) → `TRACK_F_HANDBACK.md`; verified rows may enter Q&A answers (R98) |
| after 09/11 | F3 mechanism, F4 graph insights, F6 new features; report revision |

---

## 6 · Start prompts

**Track A (account 1):**
> Defense track A (D12-A). Read `STATUS_BOARD.md` rev 42 (all, especially §3), `MODEL_CMP_ANALYSIS.md` §4 and §6,
> `NUMBERS_LOCK.md` (header, §1, §8, §17, §17c), `NUMBERS_LOCK_S18.md` (rev d), `DECK_BRIEF.md` rev 6, `QA_V9.md` (rev 2,
> already merged), `QA_BANK.md`, and the submitted deck PDF. Attached: my script, `SCRIPT_v3_marked.md`,
> `METHOD_DRILL_D11A_vi.md`. Defense 09/11. Tasks: check my script against the submitted deck and the locks (numbers,
> overclaims, R96 — no "the graph improves detection"); time it; write the answers for every backup issue of board §3
> (R104) and the new questions of §5, correcting `QA_V9.md` rev 2 and `QA_BANK.md` where needed; drill me in Vietnamese. Do not touch
> Track F. End with `TRACK_A_HANDBACK.md` and every changed file whole.

**Track F (account 2):**
> Future research F1 (D12-F). Read `STATUS_BOARD.md` rev 42 (§0, §2, §4, §5), **`FUTURE_RESEARCH_PLAN.md` rev 0 (draft)**,
> `MODEL_CMP_ANALYSIS.md`, `MODEL_COMPARISON_PLAN.md` §9, `NUMBERS_LOCK_S18.md` (rev d) §18.4 and §18.6. Clone
> github.com/Nhanvas/Thesis (it must contain `results/model_cmp/` and `src/model_cmp_*.py`; if not, ask me to push) and
> read `src/v9_x3_build_folds.py`, `src/v9_x3_train_fold.py`, `src/v9_x3_cv_eval.py`, `src/model_cmp_core.py`,
> `src/model_cmp_run.py`, `src/model_cmp_aggregate.py`. Step 1: verify every assumption of the plan in the code and
> list what is wrong or missing; step 2: put the open items O1–O7 to me (one message, with your recommendation);
> step 3: only after my answers, fix plan rev 1 (§9 log), generate and commit the random partitions, write the complete
> Kaggle notebooks (smoke first, measured runtime, atomic jobs, gates) tested on synthetic data, and tell me click by
> click how to start them. Everything on Kaggle; my laptop stays free for the defense. No result enters a slide; verified
> results may enter Q&A answers only. End with `TRACK_F_HANDBACK.md` and every changed project file whole.

---

## 7 · Files (project) and where they live locally

| file | role | local path |
|---|---|---|
| submitted deck PDF `BEBEIU22184_NguyenQuocTrungNhan.pdf` | base of all slide work (R71) | `F:/Study/Thesis/Defense/slides/` |
| `STATUS_BOARD.md` (rev 42) | this board | `Code/docs/` (repo) |
| `FUTURE_RESEARCH_PLAN.md` (rev 0 draft) | Track F design | `Code/docs/` (repo) |
| `MODEL_COMPARISON_PLAN.md`, `MODEL_CMP_ANALYSIS.md`, `MODEL_CMP_HANDBACK.md` | closed model comparison (design, verified reading, handback) | `Code/docs/`, `Code/results/model_cmp/ANALYSIS.md`, `Defense/notes/` |
| `NUMBERS_LOCK.md` · `NUMBERS_LOCK_S18.md` (rev d: §18.6 model comparison, §18.7 Track A rows of 03/11) | allowed numbers | `Defense/notes/` |
| `DECK_BRIEF.md` (rev 6), `FIGURE_INDEX.md` | slide rules (A1–A103), figures | `Defense/outline/` |
| `TRACK_A_HANDBACK.md` (D11-A, 03/11) + its files: `CANVA_FIXES_D11A.md`, `SCRIPT_v3_marked.md`, `METHOD_DRILL_D11A_vi.md`, `QA_V9_PATCH_D11A.md` (merged into `QA_V9.md` rev 2), `NUMBERS_LOCK_S18_append_D11A.md` (merged into S18 rev d as §18.7), `WORKFLOW_D11A_vi.md`, figures `slides/figs/d11a/` | merged into this board; local only (attach to the Track A chat) | `Defense/notes/`, `Defense/outline/`, `Defense/script/`, `Defense/qa/`, `Defense/slides/` |
| `QA_V9.md` (rev 2, 05/11: D11-A patch + six-model results + Q21–Q23) | post-review answers | `Defense/qa/` |
| `V9_RESULTS_SUMMARY.md` (rev 3), study guides, `QA_BANK.md`, demo files | defense material (Track A corrects) | `Defense/notes/`, `Defense/qa/`, `Defense/script/` |
| `VERIFIED_CORRECTIONS.md` | findings not to rediscover | `Code/docs/` |
| record files (PERF_PHASE_RECORD, HANDOFF_REPORT, PROVENANCE, PROVENANCE_V2, RESULTS_OF_RECORD_phaseB, ATTRIBUTION_SPEC, Thesis_Reference_Sheet, CLAIM_AUDIT_v8, Thesis_Final_Report, Registration Form, p2_ledger.csv, REPRODUCE, RUBRIC_MAP, Kangabu tips, THESIS_REPORT_WRITING_GUIDE) | unchanged | as before |
| `V10_PLAN.md` | superseded (R90, R100); **kept in the repo only, removed from the project** | `Code/docs/` |

## 8 · Decisions log
- rev 22–39: see git. rev 40 (02/11 22:30): R88–R95.
- rev 41 (05/11 08:45, not published): model comparison closed with six models (R96); slides submitted, defense 09/11
  (R97); Track F opened (R98–R100); whole-file deliveries (R101); `V10_PLAN.md` superseded by `FUTURE_RESEARCH_PLAN.md`.
- **rev 42 (05/11 09:30):** Track A handback D11-A merged (R102 Chung 27/48, R103 structure, R104 backup answers);
  submitted deck checked page by page (§3); `DECK_BRIEF.md` rev 6 (A97–A103).
- **rev 42, 10:30 (same rev, before publication):** D11-A S18 rows merged as `NUMBERS_LOCK_S18.md` rev d §18.7; D11-A QA patch
  merged with the six-model results into whole `QA_V9.md` rev 2 (Q1, Q5, Q6 chb14 6/8, Q10 27/48, Q18, Q21–Q23).
