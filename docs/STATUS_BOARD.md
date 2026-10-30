# STATUS_BOARD — DEFENSE phase (rev 35, 2026-10-31, end of chat V9 part 2: verification closed, project refreshed)

**Read this first in every chat, then `Defense/notes/V9_RESULTS_SUMMARY.md` (rev 2).** This board says what is done,
what is open and what the next chats do. At the end of every chat it is rewritten as a whole file (new rev number).

**Practical facts.**
- Defense **05–06/11/2026**, in English: **12 min talk + 3 min demo (right after the Conclusion) + 10 min Q&A**; the Q&A
  checks that the student did the work himself.
- **Mock defense with cô and the mentor: 02/11.** Supervisor meetings Thursdays 08:00.
- Reviewer: **TS. Ngô Thị Lụa** (12 points of 26/10 → `V9_RESULTS_SUMMARY.md` §0).
- **Cô 30/10 on the D9 deck:** too long for 12 min; result slides too dense; no illustration of a detected seizure
  (→ DECK_BRIEF A50–A52, L26–L27).
- After the defense: one round of report corrections (`REPORT_REVISION_NOTES.md`).

**Report.** Locked at the faculty submission (17/10/2026) until the committee's comments.

---

## 1 · Chat protocol (binding)

1. One task per chat from section 5, unless the author decides otherwise.
2. **Start:** read this board → the files named for the task.
3. **End:** (a) this board rewritten (rev + 1); (b) **one** list for the author (project files add / replace / delete,
   with local paths); (c) the start prompt of the next chat.
4. Defense material lives in `F:/Study/Thesis/Defense/` (private). The repository (public) holds this board.
5. Every number on a slide, in the script or in an answer matches the report **and** `NUMBERS_LOCK.md`
   (§16 spoken only; **§17 rev 2 allowed on slides, labelled "after the review"**; §17b = D9 figure counts, re-check).
6. **Order of work:** key messages approved → slides → script to a word budget (100–120 words/min) → author approves
   → **one** timed read.
7. **Main pages fit 12 minutes** (A50): one message per result page, details in the appendix with a pointer.
8. **Claude writes the script** (IELTS 5.5); the author reads, adapts and rephrases.
9. **Guidance goes directly in the chat**, short and detailed; files are records.
10. Every author request about slides is logged in `DECK_BRIEF.md` §1.
11. A review item quotes the text as it is now on the page.
12. **Changes go out as one zip + one `.sh`** that checks its base first.
13. **Research is an iterative loop**; nothing is locked by default; weigh each change against the time left.
14. **Claims about data, difficulty, false alarms, Siena, hospital data are backed by real EEG**, rule-selected.
15. **Never "low because unsupervised"**; never reuse a conclusion listed in summary §9.
16. **A result enters a slide only after verification** (L27): committed, number-checked, and for explanations of
    failure, checked on more than one detector.
17. Heavy laptop jobs run **one at a time**, from Git Bash (not Cursor), browsers and MATLAB closed; never preload a
    whole EDF.

## 2 · Where things stand (31/10)

| track | state | next |
|---|---|---|
| Experiments | **closed** (author 30/10): V9 + X1, X3 (24-case CV on Kaggle), X6 (ASR), V1-FIX, FINAL verification; 0 number mismatches; pushed (`4bcfb60`, tag `v9-final` after the install script) | none |
| Key findings | see summary §3–§4: graph adds no detection value over channel features (kNN ≥ GAE, F1 significant); GAE + kNN improves the GAE, ties kNN; misses = low-amplitude, short seizures (3 detectors); test patients harder than CHB-MIT overall; ASR removes seizure contrast | slides |
| Deck | Canva v5 (62 p) + D9 plan for v6 (78 p, 29 main) — **too long/dense per cô 30/10**; D9 texts and figures partly use superseded readings | **D9b:** restructure main pages to 12 min |
| Figures | slide pack `Defense/slides/figs/final/` + `FIGURE_INDEX.md` (rule-selected); older folders as backups; `figs/d9/` to re-check | D9b |
| Numbers | NUMBERS_LOCK §17 **rev 2** (installed by this chat's script); §17b (D9) to re-check | D9b |
| Q&A | `QA_V9.md` (16 questions, new); `QA_BANK.md`, `QA_PAGE_MAP.md` v5 (old pages) | D10: page map v6 |
| Script | `SCRIPT_v2.md` = Canva v5 (obsolete after D9b) | D10 |
| Demo | login fixed; start/stop scripts; chb24 allowed | **author:** ingest chb24 (≈ 8 min), two cold-start runs, fallback video |
| Report | `REPORT_REVISION_NOTES.md` (new) | after the defense |

## 3 · Feedback and rules in force

R1–R57 stand. Added 30–31/10:

| # | source | rule |
|---|---|---|
| R58 | cô 30/10 (A50) | Main pages fit 12 minutes; one message per result page; a real-EEG illustration of a detected seizure in Results |
| R59 | mentor, author 31/10 (A51) | Each finding = result + meaning on the same page; one summary-of-findings page; no long results→discussion chain |
| R60 | author 31/10 (A52) | Key messages (≤ 5) approved before building slides; AI must select, not include everything |
| R61 | V9 part 2 (L27) | A result enters a slide only after verification |

## 4 · Decisions

- Earlier: rev 22–34 (in git or the project).
- **30/10:** experiments stop after X3 (author); X7 dropped; 4-fold CV design approved (no VAL subset).
- **31/10 (this chat):** NUMBERS_LOCK §17 rev 2; V9 summary rev 2; slides keep the report's Siena 0.633 / 0.160
  (recompute 0.635 / 0.161 within tolerance) — **author to confirm (P-V9b)**.
- **Open (author):**
  - **P-V9a — framing of the model comparison.** Recommended: GAE system stays the thesis system and headline (report,
    demo); slides state honestly that a training-free kNN on the same channel features matches its sensitivity with
    fewer false alarms, and that GAE + kNN improves the GAE but ties kNN; "GAE + kNN = the improvement" leaves the main
    message.
  - P-V9b (above); chb24 ingest and demo rehearsal; demo event number; P1 committee fields; papers (summary §13).

## 5 · Plan of chats (from 31/10)

| # | date | task | output |
|---|---|---|---|
| V9-2 | 30–31/10 ✔ | X1, X3, X6, V1-FIX, FINAL; project refresh | summary rev 2, NL §17 rev 2, QA_V9, REPORT_REVISION_NOTES, rev 35 |
| D9b | 31/10 | **slides for 12 min** (A50–A52): key messages → main page map → Slides artifact + Canva list; figures from `figs/final/`; re-check D9 pages and figures against summary rev 2 | artifact update, Canva list, DECK_BRIEF 4.2, SLIDE_OUTLINE 10 |
| — | 31/10–01/11 | **author:** Canva edits + PDF | Canva v7 |
| D10 | 01/11 | script v3 (12 min) + QA page map v6 + demo path | SCRIPT_v3, QA_PAGE_MAP v6 |
| — | 02/11 | **mock defense** | feedback |
| D11 | 02–04/11 | fixes, timed read, demo cold-start checklist | final deck |

**Start prompt of chat D9b (copy):**
> Chat D9b — make the deck fit 12 minutes after cô's feedback (30/10: too long, result slides too dense, no illustration
> of a detected seizure). Read `STATUS_BOARD.md` (rev 35), `DECK_BRIEF.md` (rev 4.1: §0b, A50–A52, L26–L27),
> `V9_RESULTS_SUMMARY.md` (rev 2, all), `NUMBERS_LOCK.md` §17 rev 2, `FIGURE_INDEX.md`, `QA_V9.md`, `SLIDE_OUTLINE.md`
> (rev 9) and `D9_CANVA_CHANGES.md`, and the Slides artifact. Attached: my current Canva PDF. Tasks: 1. Ask me P-V9a and
> P-V9b. 2. Propose the ≤ 5 key messages of the talk and wait for my approval. 3. Propose a main page map that fits
> 12:00 at 110 words/min (target ≤ 16 content pages after Title and ToC; one message, one figure, ≤ 3 short lines per
> result page; result and meaning on the same page; a detected-seizure EEG figure from `figs/final/`), with every
> removed item mapped to an appendix page; wait for approval. 4. Re-read every old sentence and every D9 figure
> (`figs/d9/`) against summary rev 2 §9 and list what must change. 5. Update the Slides artifact (same link) and give
> the Canva change list page by page. End: board rev 36, file list, start prompt of D10.

## 6 · Which file for what

| File | Use it to | When |
|---|---|---|
| `notes/V9_RESULTS_SUMMARY.md` (rev 2) | every post-review result, its evidence and limits; overturned conclusions §9 | always |
| `notes/NUMBERS_LOCK.md` (§1–§17 rev 2, §17b) | every allowed number | always |
| `slides/figs/final/FIGURE_INDEX.md` | slide figure pack and selection rules | D9b |
| `qa/QA_V9.md` | answers to post-review questions | D10, rehearsal |
| `notes/REPORT_REVISION_NOTES.md` | what the final report must change | after the defense |
| `outline/DECK_BRIEF.md` (rev 4.1) | author requests A1–A52, lessons L1–L27 | slide or script work |
| `outline/SLIDE_OUTLINE.md` (rev 9), `outline/D9_CANVA_CHANGES.md` | D9 plan (78 p) — **to be replaced in D9b** | D9b |
| `script/SCRIPT_v2.md`, `script/DEMO_SCRIPT.md` | old script; demo path | D10 |
| `qa/QA_BANK.md`, `qa/QA_PAGE_MAP.md` | answers about the reported system; page map v5 | D10 |
| `Defense/v9_reports/` | full V9 reports (incl. X1, X3, X6, FINAL) | detail |
| `docs/V9_RESULTS_INDEX.md` (repo) | task → script → results → commit | provenance |

## 7 · Layout

```
F:/Study/Thesis/
  Code/                       repository (public): docs/STATUS_BOARD.md, docs/V9_RESULTS_INDEX.md, docs/prompts/V9_*.md,
                              results/v9_* (incl. v9_x1, v9_x3, v9_x6, v9_final), src/v9_*.py, web_demo/
  Reports/final/              submitted report (.docx) + Thesis_Final_Report.md
  Dataset/                    CHB-MIT, siena (14/14), clinical (2 EDF; names in file names, never in the repo)
  Defense/
    notes/       NUMBERS_LOCK.md, V9_RESULTS_SUMMARY.md, REPORT_REVISION_NOTES.md, D5_HANDOFF.md, APP_FACTS.md, ...
    qa/          QA_BANK.md, QA_PAGE_MAP.md, QA_V9.md
    outline/     DECK_BRIEF.md (4.1), SLIDE_OUTLINE.md (9), D9_CANVA_CHANGES.md
    slides/      Canva PDFs; figs/ (final/, d9/, eeg_samples/, eeg_evidence/part1–6, x1, x6); gen/
    v9_reports/ · clinical/ · script/ · demo/ · content/ · inputs/ · review/
  Agent/inbox/                hand-over tray (V9_close2/ install bundle)
  Archive/2026-10-31/         backups made by the V9 part-2 install script
```

## 8 · Where the numbers are

| content | file |
|---|---|
| every number of the thesis system | `docs/PERF_PHASE_RECORD.md` (rev R) |
| what the committee read | `Thesis_Final_Report.md` |
| numbers allowed on slides | `NUMBERS_LOCK.md` (§1–§15; §16 spoken only; §17 rev 2 post-review) |
| post-review results | `V9_RESULTS_SUMMARY.md` rev 2; `results/v9_*`; `results/v9_final/NUMBERS_CHECK.md` |

## 9 · Decisions log

- 2026-10-15 → 24: defense phase D1–D7 (rev 22–32).
- 2026-10-26: reviewer's feedback (12 points).
- 2026-10-27/28 (V9): research loop; Siena 14/14; model comparison; hospital EEG; EEG evidence; demo fixed; rev 33.
- 2026-10-30 (D9): page map v6 (78 p); rev 34.
- 2026-10-30/31 (V9 part 2): X1 (channel member, negligible), X3 (24-case CV: kNN ≥ GAE, GAE + kNN ties kNN, test
  patients harder), X6 (ASR removes seizure contrast), V1-FIX, FINAL verification (3-detector hard-patient analysis,
  Siena gap, figure pack, number check); three earlier conclusions withdrawn; cô's slide feedback; rev 35.
