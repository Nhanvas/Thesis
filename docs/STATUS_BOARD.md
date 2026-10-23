# STATUS_BOARD — DEFENSE phase (rev 31, 2026-10-23, end of chat D6: slides from mentor feedback, script v1, demo script)

**Read this first in every chat, then `Defense/notes/D5_HANDOFF.md`.** This board says what is done, what is open and
what the next chats do. At the end of every chat it is rewritten as a whole file (new rev number).

**Practical facts.**
- Defense **05–06/11/2026**, in English; 12–15 min of speaking **including the demo**; questions after.
- Reviewer: **TS. Ngô Thị Lụa** (expected to focus on performance: why the metrics are low, other models, novelty).
  Chair on the report's approval page: Assoc. Prof. Nguyễn Thị Hiệp.
- Supervisor meetings Thursdays 08:00 (29/10 next: run-through). Mentor (anh Trí) is sending feedback in parts.
- After the defense there is one round of report corrections before the final submission.

**Report.** Locked at the faculty submission (17/10/2026) until the committee's comments.

**For any slide or script work, read `DECK_BRIEF.md` rev 3.8 (A1–A40, L1–L22, §8), `SLIDE_OUTLINE.md` rev 7 (§0b),
`D5_HANDOFF.md`, `QA_PAGE_MAP.md`, and `script/SCRIPT_v1.md`.**

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
    text as it is now on the page (L19). (The cloud chat cannot render the deck: say so and ask the author to check.)
11. **Repository changes go out as one zip + one `.sh`** that checks the base commit first and stops without changing
    anything if a file differs.
12. **Main-slide text = short key phrases like the sample** (A39); details go to the appendix. **Diagrams for Canva are
    built from editable elements, never a flat PNG** (L21). **Scripts are written to a word budget and counted** (L22).

## 2 · Where things stand (23/10)

| track | state | next |
|---|---|---|
| Numbers | NUMBERS_LOCK §1–§16 (§16 = R1, post-submission). Every number in the D6 slides and script is in it | D7: `xanh` check of the changed Canva pages |
| Deck | **Slides artifact (version 115) = target for Canva v5**: p4–p26 rebuilt (M1–M6, text cuts), H3 new. The author edits Canva v4 → v5 page by page | **Author: Canva v5** (list in section 2c) |
| Mentor feedback | M1–M6 done (M2 redrawn; M6 = p26, to confirm); rest to come | new feedback → D7 |
| Script | **`script/SCRIPT_v1.md`**: 26 slides, 1,212 spoken words = 10:06 at 120 wpm + demo 2:00 = **12:06** (14:07 at 100 wpm, measured word count, speed assumed) | author adapts; D7 timed read with a recording |
| Demo | **`script/DEMO_SCRIPT.md`**: 2:00 path, checklist, fallback (video on p61), Q&A lines. Event number from `demo/DEMO_EVENT.md` still to fill in | D8: rehearsal + `DEMO_CHECKLIST.md` |
| Q&A | `qa/QA_BANK.md` (C6-7 rewritten with R1), `qa/QA_PAGE_MAP.md` (**pages of v4: appendix pages now +1**, H3 = 64) | D7: page map to v5 |
| Reproducibility | R1 done; one line → **Appendix H3 (p64)** + QA C6-7 + NL §16 | — |
| Optimization | allowed, limited (D5_HANDOFF §5); cheapest candidate: hybrid localizer | O1 (optional), only if D7 is on track |
| Repository | public; README = final system; `web_demo/` = tag `szscan-frozen-v4.1` | — |
| Committee | — | author adds info (P1) |

## 2b · R1 — what was checked (record: `docs/REPRODUCE.md`)

| # | check | result |
|---|---|---|
| 1 | every report table and result figure redrawn from committed results (cloud, fresh clone) | **PASS** |
| 2 | external rerun from raw EDF, 4 patients, committed checkpoints (laptop, fresh clone) | **FAIL** 44/64 (chb24 input file missing; PN10 one seizure in seeds 2 and 3) |
| 2b | chb24 again with all 22 files, same code and criterion | **PASS** 16/16 |
| 3 | retrain one seed | not done (author 23/10) |

Used on Appendix H3 (p64) and QA C6-7, labelled post-submission (NL §16).

## 2c · Canva v5 — what the author changes (deck artifact version 115 = the target layout)

- **p4** Protocol cells: "Reads the whole recording before the report" · "Marks onset, offset and channels of each seizure".
- **p6** four "→" lines shortened; requirements without "Settings fixed before testing" and "Every number traceable…".
- **p9** four steps, one line each. **p13** Detection 3 bullets, Localization 2 bullets. **p14** two bullets shortened.
- **p15–p24** (done by the author 22/10: M1, M3, M5, text cuts); **p21** paste the editable diagram from the artifact;
  arrow heads at the end of the line.
- **p25** Conclusion = answer box + Summary of findings (left) + Goal and objectives (right).
- **p26 new** Contributions and Next Steps. **References** without Ali 2024. **Appendix +1**; **H3 Reproducibility
  (p64) new**.
- From reading the script (D6): **p3** remove "Up to 70% could be seizure-free…" (not said) or say it; **p9** red
  line → "(measured: Appendix G2, p60)"; **p25** never "did not work" — use "did not match the seizure channels".
- If the timed read in D7 runs over 13:30: first candidate is to move p16 to the appendix (its gains are not on p25),
  second to merge p15 into p11.

## 3 · Feedback and rules in force

R1–R41 stand (rev 24–30; DECK_BRIEF A1–A38). Added 22–23/10 (DECK_BRIEF A39–A40):

| # | source | rule |
|---|---|---|
| R42 | mentor + author 22/10 | Results/Discussion findings summarized on **half of the Conclusion slide** (not a separate slide) |
| R43 | author 22/10 | Main-slide text = short key phrases like the sample; keep only what is reported; details in the appendix |
| R44 | author 22/10 | Diagrams for Canva are editable elements; no flat PNG |

## 4 · Decisions

- Earlier: rev 22–30 (in git).
- **22–23/10 (D6):** M1 (loss → C1), M2 (diagram redrawn, scikit-learn logo whole, no NumPy logo on Cache), M3 (one
  "→" line per result/discussion slide; p24 under the table), M4 (Summary of findings in the left half of p25), M5
  (p20 line), text cuts p4–p24 (A40); R1 line → Appendix H3; script v1 and demo script written.
- **Open (author):** **M6 — keep p26 Contributions and Next Steps, or fold it back into p25?** (Claude: keep; the
  table answers "novelty" for the reviewer); event number for the demo (`demo/DEMO_EVENT.md`); P1 committee fields.

## 5 · Plan of chats (from 24/10)

| # | date | task | output |
|---|---|---|---|
| D6 | 22–23/10 ✔ | slides from mentor feedback, script v1, demo script, R1 line | SCRIPT_v1, DEMO_SCRIPT, deck v115, board rev 31 |
| **D7** | 24–28/10 | Canva v5 check (numbers on changed pages, `xanh`), QA_PAGE_MAP to v5, new mentor feedback, **first timed read** (author records; Claude marks over-long slides and hard words) → `SCRIPT_v2.md` | page map v5, script v2 |
| O1 | optional | hybrid localizer on development, one disclosed test look | NL §16 if adopted |
| — | 29/10 | cô: run-through | — |
| D8 | 30/10–04/11 | rehearsal: mock committee in chat ([PB] questions with QA_PAGE_MAP), Kangabu checklist, demo fallback test | `demo/DEMO_CHECKLIST.md` |

**Start prompt of chat D7 (copy):**
> Chat D7 — Canva v5 check + page map + first timed read. Read `STATUS_BOARD.md` (rev 31: sections 2c and 4),
> `DECK_BRIEF.md` (rev 3.8), `SLIDE_OUTLINE.md` (rev 7, §0b), `NUMBERS_LOCK.md` (§1–§16), `QA_PAGE_MAP.md`,
> `script/SCRIPT_v1.md` and `DEMO_SCRIPT.md`. Attached: my Canva v5 PDF, my recording or measured time of one read of
> SCRIPT_v1 (per slide if possible), and any new mentor feedback. Guide me directly in the chat, short and detailed.
> 1. Check every changed page of v5 against the deck artifact and NUMBERS_LOCK (quote the text as it is on the page).
> 2. Update QA_PAGE_MAP to the v5 pages (appendix +1, H3 = 64, p26 new). 3. From my timing, cut or merge to stay under
> 13:30 with the demo; write `SCRIPT_v2.md`. 4. One proposal per new mentor comment, wait for my approval. My answer on
> M6 (keep p26 or not): [write it here]. End: board rev 32, file list, start prompt of the next chat.

## 6 · Which file for what

| File | Use it to | When |
|---|---|---|
| **`script/SCRIPT_v1.md`** | what to say on each slide, where to point, time per slide | practice, D7 |
| **`script/DEMO_SCRIPT.md`** | demo path (2:00), before-session checks, fallback, demo questions | D8, defense day |
| `notes/D5_HANDOFF.md` | decisions of 21/10 night, mentor feedback M1–M6, optimization plan | D7, O1 |
| `docs/REPRODUCE.md` (repo) | what was reproduced, how, criterion and result | Q&A C6-7 |
| `outline/DECK_BRIEF.md` (rev 3.8) | author requests A1–A40, lessons L1–L22, §8 speaking and Q&A | slide or script work |
| `outline/SLIDE_OUTLINE.md` (rev 7) | page map; §0b = v5 changes | slide changes |
| `qa/QA_PAGE_MAP.md`, `qa/QA_BANK.md` | question → page; answers | D7, D8 |
| `notes/NUMBERS_LOCK.md` | every allowed number (§16 post-submission) | always |
| `notes/APP_FACTS.md`, `demo/CC_DEMO_PREP.md` | app and demo facts | D8 |

## 7 · Layout

```
F:/Study/Thesis/
  Code/                       repository (public): README.md, docs/STATUS_BOARD.md, docs/REPRODUCE.md, results/, src/, web_demo/
  repro_R1/                   clean clone + venv of check 2 (can be deleted after the defense)
  Reports/final/              submitted report (.docx) + Thesis_Final_Report.md
  Defense/
    inputs/      rubric, committee (P1), Kangabu_defense_tips.md, mentor_2110_app_diagram.png, lab_slides/
    notes/       NUMBERS_LOCK.md (§1–§16), D5_HANDOFF.md, FIGURE_PROVENANCE.md, APP_FACTS.md
    content/     study guide (Vietnamese)
    qa/          QA_BANK.md, QA_PAGE_MAP.md
    review/      D5_REVIEW.md
    outline/     DECK_BRIEF.md (rev 3.8), SLIDE_OUTLINE.md (rev 7)
    slides/      Canva PDFs; figs/; gen/
    script/      SCRIPT_v1.md, DEMO_SCRIPT.md
    demo/        CC_DEMO_PREP.md, DEMO_EVENT.md, then DEMO_CHECKLIST.md, fallback video
  Agent/inbox/                hand-over tray (D6_bundle.zip)
  Archive/2026-10-23/         DECK_BRIEF rev 3.7, SLIDE_OUTLINE rev 6, QA_BANK and NUMBERS_LOCK before D6 (backups by the D6 script)
```

## 8 · Where the numbers are

| content | file |
|---|---|
| every number of the final system | `docs/PERF_PHASE_RECORD.md` (rev R) |
| what the committee read | `Thesis_Final_Report.md` |
| numbers allowed on slides | `Defense/notes/NUMBERS_LOCK.md` (§1–§15; §16 post-submission) |
| reproducibility checks | `docs/REPRODUCE.md`, `results/r1_repro/`, `results/r1_repro_2b/` |

## 9 · Decisions log

- 2026-10-15 → 21: defense phase; D1–D5 (rev 22–29 in git).
- 2026-10-22/23 (R1): README for the final system; checks 1 PASS, 2 FAIL (missing input file), 2b PASS; rev 30.
- 2026-10-22/23 (D6): M1–M5 done, M6 proposed (p26); main-slide text cut to key phrases (A39–A40); app diagram
  redrawn as editable elements; Appendix H3 Reproducibility; NL §16; QA C6-7; SCRIPT_v1 (12:06 with demo, measured
  words) and DEMO_SCRIPT; rev 31.
