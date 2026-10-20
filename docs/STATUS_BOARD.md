# STATUS_BOARD — DEFENSE phase (rev 24, 2026-10-20, end of chat D4f: author's Canva deck + D4g brief)

**Read this first in every chat.** It says what is done, what is open, what the author still has to give or approve,
where every file lives and what the next chat does. At the end of every chat the board is rewritten as a whole file
(new rev number) and delivered with the project file list.

**Practical facts.**
- Defense **05–06/11/2026**, in English; 12–15 min of speaking **including the demo**; questions after.
- Reviewer: **TS. Ngô Thị Lụa** (expected to focus on performance: why the metrics are low, other models, novelty).
  Chair on the report's approval page: Assoc. Prof. Nguyễn Thị Hiệp.
- Supervisor meetings Thursdays 08:00 (22/10, 29/10).

**Report.** Locked at the faculty submission (17/10/2026). Report-phase history: board rev 9 in git.

**For any slide work, read `DECK_BRIEF.md` rev 3.1 (requests A1–A31, lessons L1–L13), `D4g_BRIEF.md` (the author's
Canva deck = content baseline, the 5 fixes, the appendix plan) and `SLIDE_OUTLINE.md` rev 3.1 before anything else.**

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
| Numbers | `notes/NUMBERS_LOCK.md` §1–§14 | §15 in D4g for new background sources (slide 4) and appendix numbers |
| Study guide (D2) | `content/STUDY_GUIDE_part1_vi.md`, `part2_vi.md` | author studies |
| Q&A bank (D3) | `qa/QA_BANK.md` + **§14 C9 (performance and model choice, 14 questions for TS. Lụa)**, slide pages updated to rev 3 | D5 maps every B# to its question |
| Slide design | `outline/DECK_BRIEF.md` **rev 3**, `outline/SLIDE_OUTLINE.md` **rev 3** | — |
| **Deck** | **Content baseline = the author's Canva deck `Defense/slides/Thesis_final_slide.pdf` (46 pages, 20/10)**: 25 main pages + 2 references + thank you + 18 appendix pages (page map: D4g_BRIEF §0). The artifact https://claude.ai/artifact/RQNQLEV2gmfjrcrZUuzid9 (v45) stays the build tool for new or changed slides (author copies them into Canva) | **D4g**: 5 fixes (ToC, slide 3 chart, slide 4 clinical workflow, conclusion framing + limits, page 44 → report Fig 10) and a documented appendix (D4g_BRIEF §2.1) |
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
  - P-D9 (Timpte 2023 line): kept by the author on page 4 for now; re-decided with the slide-4 rework in D4g (citation must be on the slide).
  - P-D10 (Koren quote): removed by the author in Canva — closed.
  - P-D11: Deployment and Impact kept as a main slide (page 23) — closed.
  - **D4g opening decisions:** ToC lines, slide-3 chart (found image vs coded stat chart vs none), slide-4 one or two slides, conclusion labels (D4g_BRIEF §1).
  - P1 committee research fields → `Defense/inputs/committee.md`.
  - Optional: a high-resolution Timpte Fig. 2B if the author wants the curve on slide 4.

## 5 · Plan of chats

| # | date | task | output |
|---|---|---|---|
| D0–D4e | 15–17/10 ✔ | plan, numbers, study guide, Q&A, design, figures, deck v4 | rev 22 |
| **D4f** | **18–19/10 ✔** | deck rev 3: structure by pipeline, background images, self-drawn method diagrams D10–D12, conclusion cards, 23 new backups (B1–B23), QA §14 for the reviewer | artifact v45; DECK_BRIEF rev 3; SLIDE_OUTLINE rev 3; NL §14; QA §14; `slides/gen/` + `figs/rev3/` |
| ✔ | 20/10 | author: Canva deck, kept ~80 % (A31) | `slides/Thesis_final_slide.pdf` |
| **D4g** | 20–22/10 | 5 fixes + documented appendix (A31; D4g_BRIEF) in the same artifact → author copies into Canva | new / changed slides; NL §15 |
| **D5** | 22–23/10 | review of the Canva deck after D4g: numbers vs NUMBERS_LOCK (`xanh`), English (`en`), rubric, image legibility, DECK_BRIEF A1–A31 and L1–L13 → cô, anh Trí | review list |
| D6 | ≈ 26–27/10 | apply feedback → **slide freeze** | `slides/…_FROZEN` |
| D7 | 28–30/10 | English script per slide, timed | `script/` |
| D8 | 30/10–04/11 | rehearsal: mock committee, timing, demo checklist, fallback video | `demo/DEMO_CHECKLIST.md` |

**Start prompt of chat D4g (copy):**
> Chat D4g — Fix 5 points of my Canva deck and build a documented appendix. Read `STATUS_BOARD.md` (rev 24), the
> instructions, `DECK_BRIEF.md` (rev 3.1: A1–A31, L1–L13), **`D4g_BRIEF.md`** (Canva page map, your proposals for the
> 5 fixes, appendix plan §2.1, start commands §3), `SLIDE_OUTLINE.md` (rev 3.1), `NUMBERS_LOCK.md`, `QA_BANK.md` §14.
> Attached: my Canva deck `Thesis_final_slide.pdf`, the report figures (Fig 1–16), the HD4 sample PDF [and images for
> slide 4 if I have them].
> 1. Run the start commands of D4g_BRIEF §3 and read the report sections and record files it names, so you know the
>    whole thesis again. 2. Put your 5-fix proposals (D4g_BRIEF §1) to me in one short list and wait for my answer.
> 3. Build the fixed slides and the appendix (D4g_BRIEF §2.1, finalised with me) in the same artifact; every number
>    from NUMBERS_LOCK or a committed file (add §15); render and look at every slide before sending.
> End: board rev 25, DECK_BRIEF / SLIDE_OUTLINE updates, project file list, prompt of chat D5 (review).

## 6 · Which file for what

| File | Use it to | When |
|---|---|---|
| **`outline/DECK_BRIEF.md` (rev 3.1)** | every author request (A1–A31), lessons L1–L13, presentation rules, design system | before any slide work |
| **`outline/D4g_BRIEF.md`** | Canva page map, the 5 fixes with proposals, appendix plan, start commands | D4g |
| **`outline/SLIDE_OUTLINE.md` (rev 3.1)** | rev 3 slide map, figure scripts, rubric coverage | D4g–D7 |
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
- 2026-10-20: the author reviewed rev 3 in Canva (`Thesis_final_slide.pdf`, 46 pages): ~80 % kept, some slides merged
  or dropped; feedback A31 (ToC, slide 3 chart, slide 4 clinical workflow, conclusion framing + limits, page 44 →
  report Fig 10) and a new reading of the appendix: complete documentation of the thesis, not Q&A. No slide edited in
  this chat; `D4g_BRIEF.md` prepared for chat D4g.
