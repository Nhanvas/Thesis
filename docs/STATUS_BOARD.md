# STATUS_BOARD — DEFENSE phase (rev 28, 2026-10-21, end of chat D5: review of Canva deck v3)

**Read this first in every chat.** It says what is done, what is open, what the author still has to give or approve,
where every file lives and what the next chat does. At the end of every chat the board is rewritten as a whole file
(new rev number) and delivered with the project file list.

**Practical facts.**
- Defense **05–06/11/2026**, in English; 12–15 min of speaking **including the demo**; questions after.
- Reviewer: **TS. Ngô Thị Lụa** (expected to focus on performance: why the metrics are low, other models, novelty).
  Chair on the report's approval page: Assoc. Prof. Nguyễn Thị Hiệp.
- Supervisor meetings Thursdays 08:00 (22/10, 29/10).
- **Schedule is tight (author 21/10):** feedback from cô and anh Trí still to come, and the author writes and studies the
  script **himself**. The plan in §5 is compressed accordingly.

**Report.** Locked at the faculty submission (17/10/2026). Report-phase history: board rev 9 in git.

**For any slide work, read `DECK_BRIEF.md` rev 3.6 (requests A1–A36, lessons L1–L19, §8 speaking and Q&A),
`SLIDE_OUTLINE.md` rev 6 (page map 1–62 of Canva deck v3) and `Defense/review/D5_REVIEW.md` before anything else.**

---

## 1 · Chat protocol (binding)

1. One task per chat from section 5, unless the author decides otherwise.
2. **Start:** read this board → the files named for the task → nothing else unless the task needs it.
3. **End:** (a) this board rewritten (rev + 1); (b) **one** list for the author (project files add / replace / delete,
   with local paths); (c) the start prompt of the next chat.
4. Defense material lives in `F:/Study/Thesis/Defense/` (private). The repository (public) holds this board; cloud
   chats clone it to read code and results. A local file a chat needs is attached.
5. Every number on a slide, in the script or in an answer matches the final report **and** `NUMBERS_LOCK.md`.
6. **No script before the slide freeze.** The script is the author's own work (A36); Claude helps only when asked.
7. Every number on a main slide has an answer in `QA_BANK.md` or an appendix page (`qa/QA_PAGE_MAP.md`).
8. Requests are not repeated: every author request about slides is logged in `DECK_BRIEF.md` §1.
9. **Before sending anything for approval, render and look at every changed slide** (A24).
10. **A review item quotes the text as it is now on the rendered page** of the file under review (L19).

## 2 · Where things stand (21/10, end of D5)

| track | state | next |
|---|---|---|
| Report | submitted 17/10 | — |
| Numbers | `notes/NUMBERS_LOCK.md` §1–§15; **D5: every number of Canva deck v3 checked: all match** | D6: changed pages only |
| Study guide (D2) | `content/STUDY_GUIDE_part1_vi.md`, `part2_vi.md` | author studies |
| Q&A bank (D3) | `qa/QA_BANK.md` + §14 C9; **`qa/QA_PAGE_MAP.md`** (every question → page of deck v3; 3 gaps) | author rehearses with the page map |
| Slide design | `outline/DECK_BRIEF.md` **rev 3.6**, `outline/SLIDE_OUTLINE.md` **rev 6** | — |
| **Deck** | **Canva deck v3** (`Thesis - Defense slide.pdf`, 62 pages: main 1–25, References 26–27, Thank you 28, appendix A1–H2 29–62). Artifact https://claude.ai/artifact/RQNQLEV2gmfjrcrZUuzid9 (v108) is the source of v3; **the Canva file is now the deck of record** | **author:** D5 group A (8 items, ~10 min) and B before sending to cô; export v4 |
| Review (D5) | `review/D5_REVIEW.md`: groups A / B / C, number check, rubric, prompts `xanh` `en` `boti`, summary for cô | author applies; sends v4 to cô (22/10) and anh Trí |
| App (D1c) | `notes/APP_FACTS.md` | — |
| Demo prep (A22) | `Defense/demo/CC_DEMO_PREP.md`; video on p60 (G3) | **author:** check the video plays offline; mp4 on laptop + USB |
| Repository | public; `web_demo/` = tag `szscan-frozen-v4.1`; figures read at `45a17e2` | read only |
| Defense rubric | not given; working rubric = `RUBRIC_MAP.md` (coverage in D5_REVIEW §F) | re-run when known |
| Committee | — | author adds info (P1) |

## 3 · Feedback and rules in force

R1–R33 stand (rev 24–27; details DECK_BRIEF A1–A35, L1–L18). Added in D5 (DECK_BRIEF A36, L19):

| # | source | rule |
|---|---|---|
| R34 | author 21/10 | Units written attached to the number on slides (20s, 4s, 0.5%) are intentional: keep, do not flag |
| R35 | author 21/10 | References may take **two pages** (26–27) when one page cannot hold them; R32 (only works cited on main slides) still holds |
| R36 | author 21/10 | Text the author removed in Canva (for space or because it is not needed) is not re-added; a review flags a removal only when it leaves a claim without its source or a source without its claim |
| R37 | author 21/10 | The author writes and studies the script himself; Claude does not write D7 |

## 4 · Decisions

- Earlier decisions D0–D4g and P-D1…P-D11: rev 22–27 (in git).
- **D5 (21/10):**
  - Review of Canva deck v3 done; every number matches NUMBERS_LOCK; the v2 transcription errors are fixed in v3.
  - Open for the author (D5_REVIEW): group A (p17 aggregate label, p18 takeaway, p4 cite vs content, p8 cite line,
    E7 shading text, F2 sub-line, C5 claim, p24 "7 of 8 patients"), group B (wording, format), group C (3 optional
    appendix lines: D3 disclosure, E2 38 → 37, E7 PN10 rebuild).
  - "d i" on p8 closed (not on the page; it came from the text layer of the older PDF) (L19).
  - Main deck has 25 content pages: accepted by the author (A26, A34); timing risk handled in rehearsal.
- **Open (author):** P1 committee research fields → `Defense/inputs/committee.md`; feedback of cô (22/10) and anh Trí.

## 5 · Plan of chats (compressed, 21/10)

| # | date | task | output |
|---|---|---|---|
| D0–D4g | 15–21/10 ✔ | plan, numbers, study guide, Q&A, design, figures, deck v5 | rev 22–27 |
| **D5** | **21/10 ✔** | review of Canva deck v3: numbers, English, rubric, images, QA page map | `review/D5_REVIEW.md`, `qa/QA_PAGE_MAP.md` |
| — | 21/10 evening | **author:** D5 group A + B in Canva → export `Thesis_final_slide_v4.pdf`; send to cô and anh Trí | deck v4 |
| — | 22–23/10 | **cô (22/10 08:00) and anh Trí:** feedback; author notes it in `Defense/inputs/feedback_2210.md` | feedback notes |
| D6 | 23–24/10 | apply the feedback (proposals, author approves) → verify changed pages → **slide freeze** | `slides/Thesis_final_slide_FROZEN.pdf`; QA_PAGE_MAP final |
| — | 24–29/10 | **author:** writes and studies the script himself (DECK_BRIEF §8.1–8.5 as guidance); optional `en` check | `script/` |
| — | 29/10 | cô: run-through | — |
| D8 | 30/10–04/11 | rehearsal support on request: mock committee ([PB] questions with QA_PAGE_MAP), timing, demo checklist and fallback video, DECK_BRIEF §8.8–8.9 | `demo/DEMO_CHECKLIST.md` |

**Start prompt of chat D6 (copy):**
> Chat D6 — Apply feedback and freeze the slides. Read `STATUS_BOARD.md` (rev 28), the instructions, `DECK_BRIEF.md`
> (rev 3.6: A1–A36, L1–L19, §8), `SLIDE_OUTLINE.md` (rev 6: page map 1–62), `D5_REVIEW.md`, `NUMBERS_LOCK.md` (§1–§15)
> and `QA_PAGE_MAP.md`. Attached: `Thesis_final_slide_v4.pdf` (Canva, after the D5 fixes) and `feedback_2210.md` (cô and
> anh Trí). 1. Confirm which D5 items (groups A, B, C) are applied, quoting the current text of each page. 2. For each
> feedback point: one proposal (page · current text · exact change), with its reason; wait for my approval; do not
> re-add text I removed (R36). 3. After my approval, check every number on the changed pages against NUMBERS_LOCK with
> its label. 4. Freeze: final page map, QA_PAGE_MAP updated to the frozen page numbers, list of files to keep in three
> places (laptop, USB, cloud). End: board rev 29, file list, start prompt of chat D8 (rehearsal).

## 6 · Which file for what

| File | Use it to | When |
|---|---|---|
| **`outline/DECK_BRIEF.md` (rev 3.6)** | every author request (A1–A36), lessons L1–L19, §8 speaking and Q&A, design system | before any slide work |
| **`outline/SLIDE_OUTLINE.md` (rev 6)** | page map 1–62 of Canva deck v3 (§0), what deck v5 changed (§1–§2), rubric coverage | D6 |
| **`review/D5_REVIEW.md`** | the open fixes (A, B, C), number check, prompts `xanh` `en` `boti`, summary for cô | D6 |
| **`qa/QA_PAGE_MAP.md`** | which page answers which question | rehearsal, defense |
| deck artifact (link in §2) | source of deck v5 (v108); no longer the deck of record | only to recover a page |
| `slides/gen/v5/`, `slides/gen/d4g/` | scripts of deck v5 and the D4g pages | only if a page must be rebuilt |
| `notes/NUMBERS_LOCK.md` | check any number (§15 = D4g) | every slide, every answer |
| `qa/QA_BANK.md` (§14 C9) | rehearse answers | daily to 05/11 |
| `content/STUDY_GUIDE_part1_vi.md`, `part2_vi.md` | understand methods and results | study |
| `notes/APP_FACTS.md` | app layers, demo facts | slide 21, D8 |

## 7 · Layout

```
F:/Study/Thesis/
  Code/                       repository (public): docs/STATUS_BOARD.md, results/, src/, web_demo/
  Reports/final/              submitted report (.docx) + Thesis_Final_Report.md
  Defense/                    private, not committed
    inputs/      rubric, committee (P1), feedback_2210.md (to add), lab_slides/ (SAMPLE_BME11_oral.pdf, HD4 deck), images/
    notes/       NUMBERS_LOCK.md (§15 D4g), FIGURE_PROVENANCE.md, APP_FACTS.md
    content/     study guide (Vietnamese)
    qa/          QA_BANK.md (§14 C9), QA_PAGE_MAP.md (D5)
    review/      D5_REVIEW.md
    outline/     DECK_BRIEF.md (rev 3.6), SLIDE_OUTLINE.md (rev 6)
    slides/      Thesis_final_slide*.pdf (Canva); figs/ (D1b, D4c, rev3/, d4g/); gen/ (v4, rev 3, d4g/, v5/)
    script/      (author)
    demo/        CC_DEMO_PREP.md, then DEMO_CHECKLIST.md, demo_fallback_chb03.mp4, DEMO_PREP_HANDBACK.md
  Agent/inbox/                hand-over tray (D5_bundle.zip)
  Archive/2026-10-20/         DECK_BRIEF rev 3.1–3.2, SLIDE_OUTLINE rev 3.1, D4g_BRIEF.md
  Archive/2026-10-21/         DECK_BRIEF rev 3.3–3.5, SLIDE_OUTLINE rev 4–5.1
```

## 8 · Where the numbers are

| content | file |
|---|---|
| every number of the final system | `docs/PERF_PHASE_RECORD.md` (rev R) |
| what the committee read | `Thesis_Final_Report.md` |
| numbers allowed on slides | `Defense/notes/NUMBERS_LOCK.md` (§1–§15) |
| benchmark entries on Siena | `docs/BENCHMARK_CHECK_szcore_c57da2f.md` |

## 9 · Decisions log

- 2026-10-15 → 19: defense phase opened; D1–D4f (rev 22–24 in git).
- 2026-10-20 → 21 (D4g): Canva deck reviewed; appendix A–H documented; deck v5 rebuilt (artifact v107–v108); speaking
  and Q&A rules → DECK_BRIEF §8 (A35). Rev 25–27.
- 2026-10-21 (D4g, end): earlier review list of the Canva copy (groups A, B, C) given; author applied it in Canva.
- 2026-10-21 (D5): Canva deck v3 (62 pages) reviewed page by page. All numbers match NUMBERS_LOCK. Author: units attached
  to numbers are intentional; References on two pages; removed text stays removed; the author writes the script himself
  (A36). 8 group-A items, 12 group-B items, 3 optional group-C lines → D5_REVIEW. QA_BANK mapped to pages (3 gaps, each
  closed by one optional line). Plan compressed: freeze 24/10.
