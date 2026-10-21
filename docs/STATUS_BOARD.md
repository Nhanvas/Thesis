# STATUS_BOARD — DEFENSE phase (rev 29, 2026-10-21 night, end of chat D5: hand-off to D6, R1, O1)

**Read this first in every chat, then `Defense/notes/D5_HANDOFF.md`.** This board says what is done, what is open and
what the next chats do. At the end of every chat it is rewritten as a whole file (new rev number).

**Practical facts.**
- Defense **05–06/11/2026**, in English; 12–15 min of speaking **including the demo**; questions after.
- Reviewer: **TS. Ngô Thị Lụa** (expected to focus on performance: why the metrics are low, other models, novelty).
  Chair on the report's approval page: Assoc. Prof. Nguyễn Thị Hiệp.
- Supervisor meetings Thursdays 08:00 (22/10, 29/10). Mentor (anh Trí) is sending feedback in parts.
- After the defense there is one round of report corrections before the final submission.

**Report.** Locked at the faculty submission (17/10/2026) until the committee's comments.

**For any slide or script work, read `DECK_BRIEF.md` rev 3.7 (A1–A38, L1–L19, §8), `SLIDE_OUTLINE.md` rev 6,
`D5_HANDOFF.md` and `QA_PAGE_MAP.md`.**

---

## 1 · Chat protocol (binding)

1. One task per chat from section 5, unless the author decides otherwise.
2. **Start:** read this board → `D5_HANDOFF.md` → the files named for the task.
3. **End:** (a) this board rewritten (rev + 1); (b) **one** list for the author (project files add / replace / delete,
   with local paths); (c) the start prompt of the next chat.
4. Defense material lives in `F:/Study/Thesis/Defense/` (private). The repository (public) holds this board.
5. Every number on a slide, in the script or in an answer matches the final report **and** `NUMBERS_LOCK.md`
   (a post-submission number needs NUMBERS_LOCK §16 and its label).
6. **No freeze** (A37): slides stay editable; every change → re-check the numbers on the changed pages.
7. **Claude writes the script** (A37), IELTS 5.5 English; the author reads, adapts and rephrases.
8. **Guidance goes directly in the chat**, short and detailed; files are records, not reading assignments (A37).
9. Every author request about slides is logged in `DECK_BRIEF.md` §1.
10. Before sending anything for approval, render and look at every changed slide (A24); a review item quotes the
    text as it is now on the page (L19).

## 2 · Where things stand (21/10 night)

| track | state | next |
|---|---|---|
| Numbers | `notes/NUMBERS_LOCK.md` §1–§15; Canva deck v3 checked: all match | D6: changed pages only |
| Deck | **Canva v4** (sent to the mentor 21/10; 62 pages, same page numbers as v3). Leftovers the author fixes himself: D5_HANDOFF §2 | D6: mentor feedback M1–M6 + script-driven changes |
| Mentor feedback | partial (M1–M6), in `D5_HANDOFF.md` §3; rest to come | D6 proposes, author approves |
| Script | not started; rules and time budget in D5_HANDOFF §4 | **D6: Claude writes `script/SCRIPT_v1.md` + `DEMO_SCRIPT.md`** |
| Q&A | `qa/QA_BANK.md` (+ §14 C9), `qa/QA_PAGE_MAP.md` (pages of v3/v4) | D8: mock committee in chat; page map updated when pages move |
| Reproducibility | **README.md describes the old system** (v3.1 rebuild, PELT, 0.632 @ 38.6) | **R1:** new README + clean-clone checks, step by step |
| Optimization | allowed again, limited (D5_HANDOFF §5); cheapest candidate: hybrid localizer (change-point onset + contiguous-run offset), chosen on development | **O1 (optional)** after D6 |
| Demo | `demo/CC_DEMO_PREP.md`; video on p60 | D6: demo script; D8: checklist, offline video check |
| Study material | `content/STUDY_GUIDE_part1_vi.md`, `part2_vi.md`; `inputs/Kangabu_defense_tips.md` | used inside D6 / D8, not as reading assignments |
| Repository | public; `web_demo/` = tag `szscan-frozen-v4.1` | R1 edits README and docs only |
| Committee | — | author adds info (P1) |

## 3 · Feedback and rules in force

R1–R36 stand (rev 24–28; DECK_BRIEF A1–A36). Changed or added 21/10 night (DECK_BRIEF A37–A38):

| # | source | rule |
|---|---|---|
| R37 | author 21/10 night | **Replaced:** Claude writes the script (IELTS 5.5) and the demo script; the author adapts it |
| R38 | author 21/10 night | No slide freeze; slides change whenever an issue or feedback appears |
| R39 | author 21/10 night | Guidance directly in the chat, short and detailed; code-documentation work given step by step |
| R40 | author 21/10 night | Optimization may run in parallel with practice if there is capacity; any change is disclosed with how it was chosen |
| R41 | mentor 21/10 | Each result and discussion slide ends with one closing "→" line; one summary slide closes results/discussion; no loss figure in results |

## 4 · Decisions

- Earlier: rev 22–28 (in git).
- **21/10 night:** A37 (no freeze; Claude writes the script; guidance in chat; optimization allowed, limited);
  A38 (mentor feedback M1–M6, partial). README found outdated → R1.
- **Open (author):** which error the mentor meant in the app diagram (M2); M6 (split Contributions/Limits) is the
  mentor's 50/50 call; P1 committee fields.

## 5 · Plan of chats (from 22/10)

| # | date | task | output |
|---|---|---|---|
| D5 | 21/10 ✔ | review of Canva deck v3; hand-off | D5_REVIEW, QA_PAGE_MAP, D5_HANDOFF |
| **D6** | 22–24/10 | slide changes M1–M6 (proposals → approval) + **script v1** (IELTS 5.5, timed) + **demo script**; may split into D6a (slides 1–14) and D6b (15–end + demo) | `script/SCRIPT_v1.md`, `script/DEMO_SCRIPT.md`, slide change list |
| **R1** | 22/10 → (parallel) | reproducibility: new README for the final system, clean-clone checks (cloud, then laptop with Claude Code), external rerun vs committed results | README in repo; `docs/REPRODUCE.md`; check report |
| O1 | after D6 (optional) | optimization: hybrid localizer on development, one disclosed test look | NUMBERS_LOCK §16 if adopted |
| — | 29/10 | cô: run-through | — |
| D8 | 30/10–04/11 | rehearsal: timed read-through, mock committee in chat ([PB] questions with QA_PAGE_MAP), Kangabu checklist, demo fallback | `demo/DEMO_CHECKLIST.md` |

**Start prompt of chat D6 (copy):**
> Chat D6 — Slides from mentor feedback + script + demo script. Read `STATUS_BOARD.md` (rev 29), `D5_HANDOFF.md`
> (all), the instructions, `DECK_BRIEF.md` (rev 3.7, §8), `SLIDE_OUTLINE.md` (rev 6), `NUMBERS_LOCK.md`, `APP_FACTS.md`,
> `CC_DEMO_PREP.md`, `SAMPLE_BME11_oral.pdf` (summary-slide layout) and `Kangabu_defense_tips.md`. Attached: my latest
> Canva PDF (and any new mentor feedback). Guide me directly in the chat, short and detailed. 1. For M1–M6 and any new
> feedback: one proposal each (page · current text · exact new text), wait for my approval. 2. Write the script v1 in
> English at IELTS 5.5 level (short sentences, common words), per slide: message · where to look · 1–3 sentences ·
> transition, with a target time; full sentences only for the opening and the ending; every number with its label and
> in NUMBERS_LOCK. 3. Write the demo script (what to show, what to say, ~2 min, fallback). 4. From reading the script,
> list slides that should change. End: board rev 30, file list, start prompt of the next chat.

**Start prompt of chat R1 (copy):**
> Chat R1 — Reproducibility and code documentation. Read `STATUS_BOARD.md` (rev 29), `D5_HANDOFF.md` §6, the
> instructions §8–§9, and clone `github.com/Nhanvas/Thesis`. The README still describes the old system. Guide me step by
> step in the chat (one step at a time; each step = one command or one Claude Code prompt, with its expected runtime):
> 1. a new README for the final system (environment, data download, configurable paths, ordered scripts, report
> table/figure → result file → command), old material moved to a History section; 2. a clean-clone check on the cloud
> (redraw tables and figures from committed results); 3. a Claude Code prompt for my laptop: clean clone + new
> environment, rerun the external validation (chb24 and 2–3 Siena patients) with the committed checkpoint and compare
> with `results/x1_external/` against a criterion fixed before running; 4. optional: retrain one seed from scratch.
> End: board rev (next), file list, start prompt of the next chat.

## 6 · Which file for what

| File | Use it to | When |
|---|---|---|
| **`notes/D5_HANDOFF.md`** | every decision of 21/10 night, mentor feedback, script and demo frame, optimization and R1 plans | D6, R1, O1 |
| `outline/DECK_BRIEF.md` (rev 3.7) | author requests A1–A38, lessons L1–L19, §8 speaking and Q&A | slide or script work |
| `outline/SLIDE_OUTLINE.md` (rev 6) | page map 1–62 | slide changes |
| `review/D5_REVIEW.md` | number check, prompts `xanh` `en` `boti` | re-checks |
| `qa/QA_PAGE_MAP.md`, `qa/QA_BANK.md` | question → page; answers | D8, defense |
| `inputs/Kangabu_defense_tips.md` | the defense-practice article (10 rules + checklist) | D6, D8 |
| `notes/NUMBERS_LOCK.md` | every allowed number | always |
| `notes/APP_FACTS.md`, `demo/CC_DEMO_PREP.md` | app and demo facts | demo script, D8 |

## 7 · Layout

```
F:/Study/Thesis/
  Code/                       repository (public): README.md (to rewrite, R1), docs/STATUS_BOARD.md, results/, src/, web_demo/
  Reports/final/              submitted report (.docx) + Thesis_Final_Report.md
  Defense/
    inputs/      rubric, committee (P1), Kangabu_defense_tips.md, mentor_2110_app_diagram.png, lab_slides/
    notes/       NUMBERS_LOCK.md, D5_HANDOFF.md, FIGURE_PROVENANCE.md, APP_FACTS.md
    content/     study guide (Vietnamese)
    qa/          QA_BANK.md, QA_PAGE_MAP.md
    review/      D5_REVIEW.md
    outline/     DECK_BRIEF.md (rev 3.7), SLIDE_OUTLINE.md (rev 6)
    slides/      Canva PDFs; figs/; gen/
    script/      SCRIPT_v1.md, DEMO_SCRIPT.md (D6)
    demo/        CC_DEMO_PREP.md, then DEMO_CHECKLIST.md, fallback video
  Agent/inbox/                hand-over tray (D5b_bundle.zip)
  Archive/2026-10-21/         DECK_BRIEF rev 3.3–3.6, SLIDE_OUTLINE rev 4–5.1
```

## 8 · Where the numbers are

| content | file |
|---|---|
| every number of the final system | `docs/PERF_PHASE_RECORD.md` (rev R) |
| what the committee read | `Thesis_Final_Report.md` |
| numbers allowed on slides | `Defense/notes/NUMBERS_LOCK.md` (§1–§15; §16 for post-submission numbers, if any) |

## 9 · Decisions log

- 2026-10-15 → 21: defense phase; D1–D5 (rev 22–28 in git).
- 2026-10-21 (D5): Canva deck v3 reviewed (all numbers match); review list, QA page map.
- 2026-10-21 night (D5, end): author fixed most of group A and sent v4 to the mentor; mentor's first comments (M1–M6);
  author: no freeze, Claude writes the script at IELTS 5.5, guidance in chat, optimization allowed if capacity;
  README found outdated (describes the v3.1 system) → R1. Hand-off written (`D5_HANDOFF.md`).
