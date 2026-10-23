# STATUS_BOARD — DEFENSE phase (rev 30, 2026-10-23, end of chat R1: reproducibility done)

**Read this first in every chat, then `Defense/notes/D5_HANDOFF.md`.** This board says what is done, what is open and
what the next chats do. At the end of every chat it is rewritten as a whole file (new rev number).

**Practical facts.**
- Defense **05–06/11/2026**, in English; 12–15 min of speaking **including the demo**; questions after.
- Reviewer: **TS. Ngô Thị Lụa** (expected to focus on performance: why the metrics are low, other models, novelty).
  Chair on the report's approval page: Assoc. Prof. Nguyễn Thị Hiệp.
- Supervisor meetings Thursdays 08:00 (29/10 next). Mentor (anh Trí) is sending feedback in parts.
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
11. **Repository changes go out as one zip + one `.sh`** that checks the base commit first and stops without changing
    anything if a file differs (R1 practice; a second run of a finished script stops harmlessly).

## 2 · Where things stand (23/10)

| track | state | next |
|---|---|---|
| Numbers | `notes/NUMBERS_LOCK.md` §1–§15; Canva deck v3 checked: all match | D6: changed pages only; R1 line → §16 if used |
| Deck | **Canva v4** (sent to the mentor 21/10; 62 pages). Leftovers the author fixes himself: D5_HANDOFF §2 | D6: mentor feedback M1–M6 + script-driven changes |
| Mentor feedback | partial (M1–M6), in `D5_HANDOFF.md` §3; rest to come | D6 proposes, author approves |
| Script | not started; rules and time budget in D5_HANDOFF §4 | **D6: Claude writes `script/SCRIPT_v1.md` + `DEMO_SCRIPT.md`** |
| Q&A | `qa/QA_BANK.md` (+ §14 C9), `qa/QA_PAGE_MAP.md` | D6/D8: answer C6-7 from section 2b below |
| **Reproducibility** | **R1 done (22–23/10).** New README (final system), `docs/REPRODUCE.md`, checks 1, 2, 2b (section 2b) | one line on a slide/backup + QA C6-7 (D6) |
| Optimization | allowed again, limited (D5_HANDOFF §5); cheapest candidate: hybrid localizer | **O1 (optional)** after D6 |
| Demo | `demo/CC_DEMO_PREP.md`; video on p60 | D6: demo script; D8: checklist, offline video check |
| Study material | `content/STUDY_GUIDE_part1_vi.md`, `part2_vi.md`; `inputs/Kangabu_defense_tips.md` | used inside D6 / D8 |
| Repository | public; README describes the final system; `web_demo/` = tag `szscan-frozen-v4.1` | — |
| Committee | — | author adds info (P1) |

## 2b · R1 — what was checked (record: `docs/REPRODUCE.md`; every criterion written before its run)

| # | check | where | result |
|---|---|---|---|
| 1 | every report table and result figure redrawn from committed result files (`make_v8_exhibits.py`, `fig14_gallery.py`), gates against the numbers of record | cloud, fresh clone `1638359`, numpy/pandas/matplotlib only | **PASS**: all gates; Tables 4, 11–17, 19, 22, 23 equal to the report (chb04 listed hours 156.065 h printed 156.06 by the script, 156.07 in the report: rounding only) |
| 2 | external rerun from raw EDF with the committed checkpoints, 4 patients (chb24, PN10, PN00, PN11); criterion: tp equal, \|fp diff\| ≤ 2, seizures/skipped equal, hours ± 0.01 h on all 16 rows per patient | laptop, fresh clone `5cf5fb2`, new environment from `requirements.txt` | **FAIL** (44/64 rows): PN00, PN11 16/16; PN10 12/16 (seeds 2 and 3 differ by one borderline seizure each, 4-seed total 24 = 24); chb24 0/16 because `chb24_08.edf` was missing from the input |
| 2b | chb24 again, complete input (22 files, all sha256 = PhysioNet), same code and criterion | laptop, `fe1fcc6` | **PASS** 16/16 (seed 42: 14 = 14 seizures, 26 vs 25 false alarms) |
| 3 | retrain one seed | — | not done (author 23/10: time before the defense) |

**Summary line (post-submission, for NUMBERS_LOCK §16 if used on a slide or in an answer):** *"Rerun from a clean
clone on another computer with the committed models: on the four external patients, seed 42 found the same
seizures (Siena PN00, PN10, PN11: 13 of 16, 22 false alarms in both; chb24: 14 of 16, 26 vs 25 false alarms); over
the other seeds, chb24 matched on every seed and two of nine Siena runs differed by one seizure each."* Disclose that the first attempt failed on a missing input file.

**Also found in R1.** Figure 8 is drawn by `src/figures_v6/fig_example_chb03.py`, which needs the test-score caches
of level 3 (not committed). Level 3 (rebuild of the CHB-MIT test results from EDF) is not done: the test scripts'
reproduction gates need caches of earlier stages. The README says both.

## 3 · Feedback and rules in force

R1–R41 stand (rev 24–29; DECK_BRIEF A1–A38). Nothing new in this chat.

## 4 · Decisions

- Earlier: rev 22–29 (in git).
- **22–23/10 (R1):** CHBMIT_DIR environment variable (default path unchanged); the 23 CHB-MIT z-score statistics
  files committed (sha256 in `docs/PROVENANCE_STATS.txt`); `requirements.txt` = the laptop's pinned list (old files in
  `archive/env/`); `results/README.md` replaced by an index (old in `archive/docs/`); check 2 data source: PhysioNet
  (PN00/PN11 downloaded by hand); check 2b decided after check 2 as a separate record (input error, criterion
  unchanged); retraining skipped.
- **Open (author):** M2 (which error in the app diagram); M6 (split Contributions/Limits); P1 committee fields.

## 5 · Plan of chats (from 23/10)

| # | date | task | output |
|---|---|---|---|
| R1 | 22–23/10 ✔ | reproducibility: README, clean-clone checks | README, `docs/REPRODUCE.md`, board rev 30 |
| **D6** | 23–25/10 | slide changes M1–M6 (proposals → approval) + **script v1** (IELTS 5.5, timed) + **demo script**; R1 line on a slide or backup; may split into D6a (slides 1–14) and D6b (15–end + demo) | `script/SCRIPT_v1.md`, `script/DEMO_SCRIPT.md`, slide change list |
| O1 | after D6 (optional) | optimization: hybrid localizer on development, one disclosed test look | NUMBERS_LOCK §16 if adopted |
| — | 29/10 | cô: run-through | — |
| D8 | 30/10–04/11 | rehearsal: timed read-through, mock committee in chat ([PB] questions with QA_PAGE_MAP), Kangabu checklist, demo fallback | `demo/DEMO_CHECKLIST.md` |

**Start prompt of chat D6 (copy):**
> Chat D6 — Slides from mentor feedback + script + demo script. Read `STATUS_BOARD.md` (rev 30), `D5_HANDOFF.md`
> (all), the instructions, `DECK_BRIEF.md` (rev 3.7, §8), `SLIDE_OUTLINE.md` (rev 6), `NUMBERS_LOCK.md`, `APP_FACTS.md`,
> `CC_DEMO_PREP.md`, `SAMPLE_BME11_oral.pdf` (summary-slide layout) and `Kangabu_defense_tips.md`. Attached: my latest
> Canva PDF (and any new mentor feedback). Guide me directly in the chat, short and detailed. 1. For M1–M6 and any new
> feedback: one proposal each (page · current text · exact new text), wait for my approval. 2. Write the script v1 in
> English at IELTS 5.5 level (short sentences, common words), per slide: message · where to look · 1–3 sentences ·
> transition, with a target time; full sentences only for the opening and the ending; every number with its label and
> in NUMBERS_LOCK. 3. Write the demo script (what to show, what to say, ~2 min, fallback). 4. Reproducibility (board
> §2b): propose where the one R1 line goes (a backup slide or the limitations slide), add it to NUMBERS_LOCK §16, and
> update QA C6-7. 5. From reading the script, list slides that should change. End: board rev 31, file list, start
> prompt of the next chat.

## 6 · Which file for what

| File | Use it to | When |
|---|---|---|
| **`notes/D5_HANDOFF.md`** | every decision of 21/10 night, mentor feedback, script and demo frame, optimization plan | D6, O1 |
| `docs/REPRODUCE.md` (repo) | what was reproduced, how, criterion and result | Q&A on reproducibility |
| `README.md` (repo) | how to reproduce; report exhibit → result file → command | Q&A, committee |
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
  Code/                       repository (public): README.md, docs/STATUS_BOARD.md, docs/REPRODUCE.md, results/, src/, web_demo/
  repro_R1/                   clean clone + venv of check 2 (can be deleted after the defense)
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
  Agent/inbox/                hand-over tray (R1_step*.zip, R1_check2_HANDBACK.md)
  Archive/2026-10-21/         DECK_BRIEF rev 3.3–3.6, SLIDE_OUTLINE rev 4–5.1
```

## 8 · Where the numbers are

| content | file |
|---|---|
| every number of the final system | `docs/PERF_PHASE_RECORD.md` (rev R) |
| what the committee read | `Thesis_Final_Report.md` |
| numbers allowed on slides | `Defense/notes/NUMBERS_LOCK.md` (§1–§15; §16 for post-submission numbers) |
| reproducibility checks | `docs/REPRODUCE.md`, `results/r1_repro/`, `results/r1_repro_2b/` |

## 9 · Decisions log

- 2026-10-15 → 21: defense phase; D1–D5 (rev 22–29 in git).
- 2026-10-22 (R1): README rewritten for the final system (history section for the old system); pinned requirements;
  CHBMIT_DIR; stats files committed; check 1 PASS (cloud).
- 2026-10-23 (R1): check 2 FAIL (missing chb24 file; PN10 one seizure in two seeds), record corrected (PN10 fails on
  tp, not hours); check 2b PASS; retraining skipped; board rev 30.
