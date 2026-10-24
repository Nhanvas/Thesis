# STATUS_BOARD — DEFENSE phase (rev 32, 2026-10-24, end of chat D7: Canva v5 checked, page map v5, script v2)

**Read this first in every chat, then `Defense/notes/D5_HANDOFF.md`.** This board says what is done, what is open and
what the next chats do. At the end of every chat it is rewritten as a whole file (new rev number).

**Practical facts.**
- Defense **05–06/11/2026**, in English; 12–15 min of speaking **including the demo**; questions after.
- Reviewer: **TS. Ngô Thị Lụa** (expected to focus on performance: why the metrics are low, other models, novelty).
  Chair on the report's approval page: Assoc. Prof. Nguyễn Thị Hiệp.
- Supervisor meetings Thursdays 08:00 (29/10 next: run-through). Mentor (anh Trí) is sending feedback in parts.
- After the defense there is one round of report corrections before the final submission.

**Report.** Locked at the faculty submission (17/10/2026) until the committee's comments.

**For any slide or script work, read `DECK_BRIEF.md` rev 3.9 (A1–A41, L1–L24, §8), `SLIDE_OUTLINE.md` rev 8 (§0c),
`QA_PAGE_MAP.md` (v5) and `script/SCRIPT_v2.md`.**

---

## 1 · Chat protocol (binding)

1. One task per chat from section 5, unless the author decides otherwise.
2. **Start:** read this board → the files named for the task.
3. **End:** (a) this board rewritten (rev + 1); (b) **one** list for the author (project files add / replace / delete,
   with local paths); (c) the start prompt of the next chat.
4. Defense material lives in `F:/Study/Thesis/Defense/` (private). The repository (public) holds this board.
5. Every number on a slide, in the script or in an answer matches the final report **and** `NUMBERS_LOCK.md`
   (a post-submission number needs NUMBERS_LOCK §16 and its label).
6. **Order of work (A41, L23):** slides fixed → script written to a word budget that fits 100–120 words/min → author
   approves the script → **one** timed read. Never ask for timing on slides or a script that are still changing.
7. **Main slides carry the full reported information** (A41, L24): a cut happens in what is *said*, never by moving
   reported information to the appendix. The appendix adds detail; it never hides.
8. **Claude writes the script** (A37), IELTS 5.5 English; the author reads, adapts and rephrases.
9. **Guidance goes directly in the chat**, short and detailed; files are records, not reading assignments (A37).
10. Every author request about slides is logged in `DECK_BRIEF.md` §1.
11. A review item quotes the text as it is now on the page (L19).
12. **Changes go out as one zip + one `.sh`** that checks its base first and stops without changing anything if a file
    differs (L16).

## 2 · Where things stand (24/10)

| track | state | next |
|---|---|---|
| Deck | **Canva v5 PDF (24/10, 62 pages) = deck of record.** Main 1–25 · References 26–27 · Thank you 28 · Appendix 29–62 (= D5 page map). p26 Contributions merged into p25 (M6). No H3 (author). The Slides artifact is a layout source only (its s25b, s26, aH3 are not in the deck) | author: five optional text fixes (section 2c) |
| Numbers | every number on main pages 1–25 of v5 checked against NUMBERS_LOCK §1–§15 in D7: **all match** | — |
| Mentor feedback | M1–M6 done. **M7** (findings after Results and after Discussion): **kept as now** (findings on half of p25), author 24/10 | revisit only if the mentor insists |
| Script | **`script/SCRIPT_v2.md`**: 25 slides, **1,168 spoken words** (measured) = 10:37 at 110 wpm; with demo 12:37 (11:44 at 120 wpm, 13:41 at 100 wpm; speeds assumed) | **author: approve / reword v2** → one timed read |
| Demo | `script/DEMO_SCRIPT.md`: fallback video now **page 60** (G3). Event number from `demo/DEMO_EVENT.md` still to fill in | D8 |
| Q&A | `qa/QA_BANK.md`, **`qa/QA_PAGE_MAP.md` (v5)**: C6-7 reproducibility = spoken answer (no slide); p24 figures = Fig 11, Fig 12 | D8 mock committee |
| Reproducibility | R1 done (`docs/REPRODUCE.md`); used only in the spoken answer C6-7 (NL §16) | — |
| Optimization | allowed, limited (D5_HANDOFF §5) | O1 optional, only if D8 is on track |
| Committee | — | author adds info (P1) |

## 2c · Canva v5 — five optional text fixes found in D7 (none moves a page or changes the script)

| page | on the page now | proposed |
|---|---|---|
| p25 | "Objective 1: localization without labels → Achieved" (same words as the Goal line) | "Objective 1: anomaly score → Achieved" |
| p25 | "New hospital: Siena 0.633 at 41.0 FA/day (4 seeds)" | add "per-patient mean" |
| p22 | cite line "… Shyu et al., 2023 · Ali et al., 2024 · …" (neither is on p22) | drop both from the line; Ali 2024 then out of References p26 |
| p22 | "SzCORE challenge leader: 37% at ~1 FA/day (Dan, 2026)" | add "(private corpus)" |
| p23 | "Sites without labels, GPU or cloud (nearly 80% of people with epilepsy)" | "Low- and middle-income settings without GPU or cloud (where nearly 80% of people with epilepsy live)" |

Decided by the author 24/10 (not changes): p3 keeps "Up to 70% …"; p17 keeps precision and F1; no H3.

## 3 · Feedback and rules in force

R1–R44 stand (DECK_BRIEF A1–A40). Added 24/10 (A41):

| # | source | rule |
|---|---|---|
| R45 | author 24/10 | Slides decide what is reported; the script follows the slides; timing comes after both are approved |
| R46 | author 24/10 | Main slides show the full reported information (p17 precision and F1 stay); appendix = more detail, not hiding |
| R47 | author 24/10 | Post-hoc material (e.g. reproducibility) is shown as a capability, never as a sequence of internal checks ("2", "2b") |

## 4 · Decisions

- Earlier: rev 22–31 (in git or the project).
- **24/10 (D7):** M6 = p26 removed, merged into p25 (separate slide too empty). M7 = keep the current slides. H3 not
  added. p3 and p17 unchanged. SCRIPT_v2 on Canva v5. QA_PAGE_MAP v5. DEMO_SCRIPT fallback page 60.
- **Open (author):** approve SCRIPT_v2; the five optional fixes (2c); event number for the demo (`demo/DEMO_EVENT.md`);
  P1 committee fields.

## 5 · Plan of chats (from 25/10)

| # | date | task | output |
|---|---|---|---|
| D7 | 24/10 ✔ | Canva v5 check, page map v5, script v2 | SCRIPT_v2, QA_PAGE_MAP v5, rev 32 |
| — | 25–27/10 | **author:** read SCRIPT_v2, reword it in his own English, one timed read (lap per slide) | lap times |
| D8 | 28/10–04/11 | rehearsal: timed-read review (only slides above budget), mock committee ([PB] with QA_PAGE_MAP), demo fallback test, Kangabu checklist | `script/SCRIPT_v3.md` if needed, `demo/DEMO_CHECKLIST.md` |
| — | 29/10 | cô: run-through | — |
| O1 | optional | hybrid localizer on development, one disclosed test look | NL §16 if adopted |

**Start prompt of chat D8 (copy):**
> Chat D8 — rehearsal. Read `STATUS_BOARD.md` (rev 32), `DECK_BRIEF.md` (rev 3.9, §8), `script/SCRIPT_v2.md`,
> `DEMO_SCRIPT.md`, `QA_PAGE_MAP.md` (v5) and `QA_BANK.md`. Attached: my lap time per slide of one read of SCRIPT_v2
> (and my reworded script if I changed it), the Canva PDF if I changed a page, any new feedback from cô or the mentor.
> 1. From my lap times, shorten only the slides above their budget (target ≤ 13:30 with the demo); do not touch the
> slides. 2. Mock committee: ask me the [PB] questions one by one, as TS. Ngô Thị Lụa would, and grade each answer
> (direct answer first, page to open, no invented number). 3. Demo: walk me through the fallback test (page 60).
> End: board rev 33, file list, start prompt of the next chat.

## 6 · Which file for what

| File | Use it to | When |
|---|---|---|
| **`script/SCRIPT_v2.md`** | what to say on each slide, where to point, word count per slide | practice, D8 |
| `script/DEMO_SCRIPT.md` | demo path (2:00), before-session checks, fallback (page 60), demo questions | D8, defense day |
| `qa/QA_PAGE_MAP.md` (v5), `qa/QA_BANK.md` | question → page; answers | D8 |
| `outline/DECK_BRIEF.md` (rev 3.9) | author requests A1–A41, lessons L1–L24, §8 speaking and Q&A | slide or script work |
| `outline/SLIDE_OUTLINE.md` (rev 8) | page map; §0c = Canva v5 of record | slide changes |
| `notes/NUMBERS_LOCK.md` | every allowed number (§16 post-submission, spoken only) | always |
| `notes/D5_HANDOFF.md` | mentor feedback M1–M6, optimization plan | O1 |
| `docs/REPRODUCE.md` (repo) | what was reproduced, how, criterion and result | Q&A C6-7 |
| `notes/APP_FACTS.md`, `demo/CC_DEMO_PREP.md` | app and demo facts | D8 |

## 7 · Layout

```
F:/Study/Thesis/
  Code/                       repository (public): README.md, docs/STATUS_BOARD.md, docs/REPRODUCE.md, results/, src/, web_demo/
  Reports/final/              submitted report (.docx) + Thesis_Final_Report.md
  Defense/
    inputs/      rubric, committee (P1), Kangabu_defense_tips.md, lab_slides/
    notes/       NUMBERS_LOCK.md (§1–§16), D5_HANDOFF.md, FIGURE_PROVENANCE.md, APP_FACTS.md
    content/     study guide (Vietnamese)
    qa/          QA_BANK.md, QA_PAGE_MAP.md (v5)
    review/      D5_REVIEW.md
    outline/     DECK_BRIEF.md (rev 3.9), SLIDE_OUTLINE.md (rev 8)
    slides/      Canva PDFs (v5 = deck of record); figs/; gen/
    script/      SCRIPT_v2.md, DEMO_SCRIPT.md
    demo/        CC_DEMO_PREP.md, DEMO_EVENT.md, then DEMO_CHECKLIST.md, fallback video
  Agent/inbox/                hand-over tray (D7_bundle.zip)
  Archive/2026-10-24/         SCRIPT_v1, QA_PAGE_MAP (v3), DECK_BRIEF rev 3.8, SLIDE_OUTLINE rev 7, DEMO_SCRIPT,
                              NUMBERS_LOCK, QA_BANK before D7 (backups by the D7 script)
```

## 8 · Where the numbers are

| content | file |
|---|---|
| every number of the final system | `docs/PERF_PHASE_RECORD.md` (rev R) |
| what the committee read | `Thesis_Final_Report.md` |
| numbers allowed on slides | `Defense/notes/NUMBERS_LOCK.md` (§1–§15; §16 post-submission, spoken only) |
| reproducibility checks | `docs/REPRODUCE.md`, `results/r1_repro/`, `results/r1_repro_2b/` |

## 9 · Decisions log

- 2026-10-15 → 21: defense phase; D1–D5 (rev 22–29 in git).
- 2026-10-22/23 (R1): reproducibility checks; rev 30.
- 2026-10-22/23 (D6): M1–M5, app diagram, script v1, demo script; rev 31.
- 2026-10-24 (D7): Canva v5 = deck of record (numbers all match); M6 merged; M7 kept as now; no H3; p3 and p17 kept;
  SCRIPT_v2 (1,168 measured words); QA_PAGE_MAP v5; demo fallback page 60; A41, L23–L24; rev 32.
