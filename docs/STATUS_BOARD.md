# STATUS_BOARD — DEFENSE phase (rev 23, 2026-10-19, end of chat D4f: deck rev 3)

**Read this first in every chat.** It says what is done, what is open, what the author still has to give or approve,
where every file lives and what the next chat does. At the end of every chat the board is rewritten as a whole file
(new rev number) and delivered with the project file list.

**Practical facts.**
- Defense **05–06/11/2026**, in English; 12–15 min of speaking **including the demo**; questions after.
- Reviewer: **TS. Ngô Thị Lụa** (expected to focus on performance: why the metrics are low, other models, novelty).
  Chair on the report's approval page: Assoc. Prof. Nguyễn Thị Hiệp.
- Supervisor meetings Thursdays 08:00 (22/10, 29/10).

**Report.** Locked at the faculty submission (17/10/2026). Report-phase history: board rev 9 in git.

**For any slide work, read `DECK_BRIEF.md` rev 3 (requests A1–A30 and the lessons L1–L10 of D4f) and
`SLIDE_OUTLINE.md` rev 3 (slide map, backups, figure scripts, rubric) before anything else.**

---

## 1 · Chat protocol (binding)

1. One task per chat from section 5, unless the author decides otherwise.
2. **Start:** read this board → the files named for the task → nothing else unless the task needs it.
3. **End:** (a) this board rewritten (rev + 1); (b) **one** list for the author (project files add / replace / delete,
   with local paths); (c) the start prompt of the next chat.
4. Defense material lives in `F:/Study/Thesis/Defense/` (private). The repository (public) holds this board; cloud
   chats clone it to read code and results. A local file a chat needs is attached.
5. Every number on a slide, in the script or in an answer matches the final report **and** `NUMBERS_LOCK.md`.
6. **No script before the slide freeze.**
7. Every number on a main slide has an answer in `QA_BANK.md` or a backup slide.
8. Requests are not repeated: every author request about slides is logged in `DECK_BRIEF.md` §1.
9. **Before sending anything for approval, render and look at every changed slide** (A24): overflow, legibility of
   every image, image ↔ text agreement (L1–L10).

## 2 · Where things stand (19/10, end of D4f)

| track | state | next |
|---|---|---|
| Report | submitted 17/10 | — |
| Numbers | `notes/NUMBERS_LOCK.md` §1–§13; **§14 added (D4f)**: Table 13 rows, worked example, gallery facts; **P-D9, P-D10 pending** | author approves P-D9, P-D10 |
| Study guide (D2) | `content/STUDY_GUIDE_part1_vi.md`, `part2_vi.md` | author studies |
| Q&A bank (D3) | `qa/QA_BANK.md` + **§14 C9 (performance and model choice, 14 questions for TS. Lụa)**, slide pages updated to rev 3 | D5 maps every B# to its question |
| Slide design | `outline/DECK_BRIEF.md` **rev 3**, `outline/SLIDE_OUTLINE.md` **rev 3** | — |
| **Deck (artifact)** | https://claude.ai/artifact/RQNQLEV2gmfjrcrZUuzid9 **version 45 (19/10)**. **Rev 3:** 28 pages main (title, outline, 23 content, 2 references, thank you) + **23 backups (pages 29–51)**. Method rebuilt in pipeline order with self-drawn detailed diagrams **D10** (graph and node features, +7 absolute features), **D11** (GAE with true matrix sizes and parameters), **D12** (anomaly score with real chb03 member and E(t)); background images replaced (GBD 2016 map, BioRender focal and generalized); conclusion as 4 goal cards; preprocessing steps with reasons; backups rebuilt, each = question + answer line + figure/diagram (all result figures gated: ALL GATES PASSED) | author: approve P-D9 to P-D11; .pptx → Canva; then **D5** |
| App (D1c) | `notes/APP_FACTS.md` | slide 21, B20, B21 |
| **Demo prep (A22)** | `Defense/demo/CC_DEMO_PREP.md` for Claude Code on the laptop | author runs it; video goes into B23 in Canva |
| Repository | public; `web_demo/` = tag `szscan-frozen-v4.1`; figures read at `45a17e2` | read only |
| Defense rubric | not given; working rubric = `RUBRIC_MAP.md` (coverage in SLIDE_OUTLINE rev 3 §4) | re-run when known |
| Committee | — | author adds info (P1) |

## 3 · Feedback and rules in force

R1–R21 of rev 22 stand (anh Trí, cô, lab notes, author 17/10). Added in D4f (details DECK_BRIEF A23–A30):

| # | source | rule |
|---|---|---|
| R22 | author 18/10 | Methodology follows the pipeline (data → preprocessing → graph/features → GAE → score → detection → **evaluation last**); Results in the same order; comparison after results; limits → what they limit → future work |
| R23 | author 18/10 | Background images are real, sourced and licensed; thesis parts use the thesis's own figures or detailed self-drawn diagrams; **never another model's figure for ours** (A29) |
| R24 | author 18/10 | Text short but complete in meaning; no useless information; no animation; slightly over 22 content slides is acceptable |
| R25 | author 18/10 | Anything said only when asked needs a backup slide; reviewer will press on performance (QA §14) |
| R26 | author 18/10 | Visualize what can be visualized, but small tables are allowed where clearer (A26 corrects A14) |
| R27 | author 19/10 | Claude must hold its own view, check its output several times and finish without waiting to be told each fix |

## 4 · Decisions

- Earlier decisions D0–D4e and P-D1…P-D8: rev 22 (in git).
- **D4f (18–19/10):**
  - Structure Introduction (4) → Methodology (8) → Results (7) → Discussion (3) → Conclusion approved (A26: 22 slides OK).
  - Small metric table on slide 17 and a loss curve on slide 15 approved (A26).
  - AUROC left to Claude (A27): window AUROC appears only as a mechanism check (0.966 vs 0.53, slide 15); why events
    and not window AUROC is B5.
  - Slides 3, 4, 10, 11, 12 approved provisionally (A30) after the diagrams D10–D12 and the new background images.
- **Open (author):**
  - **P-D9** Timpte 2023: "1 in 3 first seizures appeared only after 24 h of video-EEG" (6 of 19, 31.6 %) on slide 4 — approve or remove.
  - **P-D10** Koren 2018 quote "CEEG review is very demanding and time consuming." on slide 4 — approve or remove.
  - **P-D11** Keep "Deployment and Impact" (slide 23, rubric criterion 4 = 10 points) as a main slide (23 content slides) or move it to backup (22). Recommendation: keep.
  - P1 committee research fields → `Defense/inputs/committee.md`.
  - Optional: a high-resolution Timpte Fig. 2B if the author wants the curve on slide 4.

## 5 · Plan of chats

| # | date | task | output |
|---|---|---|---|
| D0–D4e | 15–17/10 ✔ | plan, numbers, study guide, Q&A, design, figures, deck v4 | rev 22 |
| **D4f** | **18–19/10 ✔** | deck rev 3: structure by pipeline, background images, self-drawn method diagrams D10–D12, conclusion cards, 23 new backups (B1–B23), QA §14 for the reviewer | artifact v45; DECK_BRIEF rev 3; SLIDE_OUTLINE rev 3; NL §14; QA §14; `slides/gen/` + `figs/rev3/` |
| — | 20–21/10 | author: P-D9…P-D11; .pptx → Canva; insert demo video in B23 | `slides/Defense_slides_rev3.pdf` |
| **D5** | 21/10 | review: numbers vs NUMBERS_LOCK (`xanh`), English (`en`), rubric, text density, image legibility, DECK_BRIEF A1–A30 and L1–L10; map B1–B23 to QA → cô 22/10 08:00, anh Trí | review list; fixes in the same artifact |
| D6 | ≈ 26–27/10 | apply feedback → **slide freeze** | `slides/…_FROZEN` |
| D7 | 28–30/10 | English script per slide, timed | `script/` |
| D8 | 30/10–04/11 | rehearsal: mock committee, timing, demo checklist, fallback video | `demo/DEMO_CHECKLIST.md` |

**Start prompt of chat D5 (copy):**
> Chat D5 — Review of deck rev 3. Read `STATUS_BOARD.md` (rev 23) and the instructions, then `DECK_BRIEF.md` (rev 3:
> A1–A30, lessons L1–L10), `SLIDE_OUTLINE.md` (rev 3), `NUMBERS_LOCK.md` (§1–§14), `QA_BANK.md` (§14), `RUBRIC_MAP.md`.
> Input: the deck artifact https://claude.ai/artifact/RQNQLEV2gmfjrcrZUuzid9 (version ≥ 45) and, if made, my Canva
> PDF. My decisions on P-D9, P-D10, P-D11: [write them here].
> 1. Apply P-D9…P-D11. 2. Check every number on pages 1–51 against NUMBERS_LOCK (set · seed · aggregate). 3. Check
> titles, takeaways, text density, repeated ideas, English, image legibility and image ↔ text agreement (L1–L10),
> rubric coverage (SLIDE_OUTLINE §4). 4. Map B1–B23 to QA_BANK questions. 5. One review list (slide · problem · fix),
> apply the agreed fixes to the same artifact, prepare questions for cô (22/10) and anh Trí.
> End: board rev 24, project file list, prompt of chat D6.

## 6 · Which file for what

| File | Use it to | When |
|---|---|---|
| **`outline/DECK_BRIEF.md` (rev 3)** | every author request (A1–A30), lessons L1–L10, presentation rules, design system | before any slide work |
| **`outline/SLIDE_OUTLINE.md` (rev 3)** | slide map with pages, backups B1–B23, figure scripts, rubric coverage | D5–D7 |
| deck artifact (link in §2) | the deck; download .pptx for Canva | D5 onward |
| `slides/gen/build_rev3.py` + `diag_*.py`, `pipeline.py` | record of how rev 3 slides and diagrams were generated (cloud paths) | only if rebuilding |
| `slides/figs/rev3/figs_*.py` + PNGs | result figures of rev 3 (gated on committed results) | if a figure changes |
| `notes/NUMBERS_LOCK.md` | check any number | every slide, every answer |
| `qa/QA_BANK.md` (§14 C9) | rehearse answers; performance questions for the reviewer | daily to 05/11 |
| `content/STUDY_GUIDE_part1_vi.md`, `part2_vi.md` | understand methods and results | study |
| `notes/APP_FACTS.md` | app layers, demo facts | slide 21, D8 |

## 7 · Layout

```
F:/Study/Thesis/
  Code/                       repository (public): docs/STATUS_BOARD.md, results/, src/, web_demo/
  Reports/final/              submitted report (.docx) + Thesis_Final_Report.md
  Defense/                    private, not committed
    inputs/      rubric, committee (P1), lab_slides/ (SAMPLE_BME11_oral.pdf, HD4 deck), images/ (GBD, BioRender, Timpte)
    notes/       NUMBERS_LOCK.md (§14 D4f), FIGURE_PROVENANCE.md, APP_FACTS.md
    content/     study guide (Vietnamese)
    qa/          QA_BANK.md (§14 C9)
    outline/     DECK_BRIEF.md (rev 3), SLIDE_OUTLINE.md (rev 3)
    slides/      figs/ F1–F10, R1–R13 (D1b, D4c); figs/rev3/ (D4f scripts + PNGs)
                 gen/  diagrams.py, icons.py, build_v4.py, build_backups.py (v4); build_rev3.py, diag_*.py, pipeline.py (D4f)
    script/
    demo/        CC_DEMO_PREP.md, then DEMO_CHECKLIST.md, demo_fallback_chb03.mp4, DEMO_PREP_HANDBACK.md
  Agent/inbox/                hand-over tray (D4f_bundle.zip)
  Archive/2026-10-19/         DECK_BRIEF rev 2, SLIDE_OUTLINE rev 2.1
```

## 8 · Where the numbers are

| content | file |
|---|---|
| every number of the final system | `docs/PERF_PHASE_RECORD.md` (rev R) |
| what the committee read | `Thesis_Final_Report.md` |
| numbers allowed on slides | `Defense/notes/NUMBERS_LOCK.md` (§1–§14) |
| benchmark entries on Siena | `docs/BENCHMARK_CHECK_szcore_c57da2f.md` |

## 9 · Decisions log

- 2026-10-15 → 17: defense phase opened; D1–D4e (rev 22 in git).
- 2026-10-18 (evening): author feedback on deck v4 (A23–A26): method by pipeline, real background images, short but
  complete text, evaluation last, comparison after results, +7 features, backups for every rejected design, reviewer
  focus on performance. QA §14 (C9, 14 questions) written.
- 2026-10-19 (night): A27–A29: image ↔ content agreement, evidence on slide, connected pipeline (P07), self-drawn
  detailed diagrams from the thesis's own data (D10–D12), Kipf figure removed. Lessons L1–L10 recorded.
- 2026-10-19 (morning): A30 — slides approved provisionally; deck rev 3 completed: main slides reviewed (preprocessing
  steps, larger montage, conclusion cards, app diagram blob fixed, page numbers consistent with the Deployment slide),
  23 backups built from new and existing gated figures, references extended (34 works), artifact version 45.
