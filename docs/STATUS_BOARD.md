# STATUS_BOARD — DEFENSE phase (rev 33, 2026-10-28, end of chat V9: reviewer feedback → experiments, EEG evidence, demo fix)

**Read this first in every chat, then `Defense/notes/V9_RESULTS_SUMMARY.md`.** This board says what is done, what is
open and what the next chats do. At the end of every chat it is rewritten as a whole file (new rev number).

**Practical facts.**
- Defense **05–06/11/2026**, in English. **Reviewer's format (26/10): 12 min talk + 3 min demo + 10 min Q&A**; the
  longer Q&A checks that the student did the work himself.
- **Mock defense with cô and the mentor: 02/11.** Supervisor meetings Thursdays 08:00 (29/10).
- Reviewer: **TS. Ngô Thị Lụa** (feedback 26/10: 12 points, answered in `V9_RESULTS_SUMMARY.md` §0).
- After the defense there is one round of report corrections before the final submission (V9 results go in then).

**Report.** Locked at the faculty submission (17/10/2026) until the committee's comments.

**For any slide or script work, read `DECK_BRIEF.md` rev 3.9 (A1–A41, L1–L24, §8; A42–A48 to add, see summary §9),
`SLIDE_OUTLINE.md` rev 8 (§0c), `QA_PAGE_MAP.md` (v5), `script/SCRIPT_v2.md` and `V9_RESULTS_SUMMARY.md`.**

---

## 1 · Chat protocol (binding)

1. One task per chat from section 5, unless the author decides otherwise.
2. **Start:** read this board → the files named for the task.
3. **End:** (a) this board rewritten (rev + 1); (b) **one** list for the author (project files add / replace / delete,
   with local paths); (c) the start prompt of the next chat.
4. Defense material lives in `F:/Study/Thesis/Defense/` (private). The repository (public) holds this board.
5. Every number on a slide, in the script or in an answer matches the final report **and** `NUMBERS_LOCK.md`
   (post-submission: §16 spoken only; **§17 allowed on slides, labelled "after the review"**).
6. **Order of work (A41, L23):** slides fixed → script written to a word budget (100–120 words/min) → author approves
   the script → **one** timed read.
7. **Main slides carry the full reported information** (A41, L24); the appendix adds detail, never hides.
8. **Claude writes the script** (A37), IELTS 5.5 English; the author reads, adapts and rephrases.
9. **Guidance goes directly in the chat**, short and detailed; files are records, not reading assignments (A37).
10. Every author request about slides is logged in `DECK_BRIEF.md` §1.
11. A review item quotes the text as it is now on the page (L19).
12. **Changes go out as one zip + one `.sh`** that checks its base first and stops without changing anything if a file
    differs (L16).
13. **(author 27/10) Research is an iterative loop** (question → experiment → result → analysis → repeat). No
    "look #" bookkeeping in reasoning or text; nothing is locked by default; weigh each change against the time left
    before the defense and the rehearsal.
14. **(reviewer 26/10, author 28/10) A claim about data, difficulty, false alarms or Siena is backed by real EEG**,
    selected by a rule fixed before drawing, not only by words and numbers.
15. Heavy laptop jobs run **one at a time**; never preload a whole EDF (Siena files reach 12–15 GB in memory).

## 2 · Where things stand (28/10)

| track | state | next |
|---|---|---|
| Deck | Canva v5 PDF (24/10, 62 pages) = deck of record, **before** the reviewer's feedback | **D9:** integrate V9 (summary §9: A42–A48) |
| V9 experiments | **done** (tag `v9-results`, index `docs/V9_RESULTS_INDEX.md`): Siena verified on 14 patients; model comparison (GAE + kNN +0.047 [+0.013, +0.086] at matched FA on test); kNN on all 24 cases; hard = focal, low-amplitude seizures; artifact veto and short-seizure branch negative | none planned before the defense |
| EEG evidence | done, rule-selected: `Defense/slides/figs/eeg_samples/`, `eeg_evidence/part1–6/`, `Defense/clinical/run/` | choose figures in D9 |
| Hospital EEG | ran on both files (qualitative): 4.8 % of 13.2 h flagged; 0 events on 27 marked activation/spike segments | one slide in D9 |
| Numbers | NUMBERS_LOCK §17 added (post-review, slide-allowed) | D9 checks every new slide number |
| Script | `script/SCRIPT_v2.md` matches Canva v5; **must be rewritten after D9** (12 min talk) | D10 |
| Demo | login fixed (7c10842); `web_demo/start_demo.sh` / `stop_demo.sh` (a05eff1), backend up in 26 s; chb24 allowed | **author:** ingest chb24 (≈ 8 min), two cold-start runs, fallback video |
| Q&A | `QA_BANK.md`, `QA_PAGE_MAP.md` (v5) — need V9 answers (model choice, unsupervised, artifacts, Siena, hard patients, hospital data) | D10 |
| Literature | papers to read: summary §8 (author reads them himself) | author, before D10 |
| Git | V9 commits are **local**: push needed | author: `git push && git push --tags` |

## 2c · Canva v5 — five optional text fixes found in D7 (still open)

| page | on the page now | proposed |
|---|---|---|
| p25 | "Objective 1: localization without labels → Achieved" | "Objective 1: anomaly score → Achieved" |
| p25 | "New hospital: Siena 0.633 at 41.0 FA/day (4 seeds)" | add "per-patient mean" |
| p22 | cite line "… Shyu et al., 2023 · Ali et al., 2024 · …" | drop both from the line |
| p22 | "SzCORE challenge leader: 37% at ~1 FA/day (Dan, 2026)" | add "(private corpus)" |
| p23 | "Sites without labels, GPU or cloud (nearly 80% of people with epilepsy)" | "Low- and middle-income settings without GPU or cloud (where nearly 80% of people with epilepsy live)" |

## 3 · Feedback and rules in force

R1–R47 stand. Added 26–28/10:

| # | source | rule |
|---|---|---|
| R48 | reviewer 26/10 | 12 min talk + 3 min demo + 10 min Q&A |
| R49 | reviewer 26/10 | Show other models on the same problem; unsupervised can be improved — "low because unsupervised" is removed everywhere |
| R50 | reviewer 26/10 | Real EEG for right and wrong detections, web-demo events, Siena and hard patients |
| R51 | reviewer 26/10 | Comparison table includes high-performing studies, the criteria of "same problem", pros and cons |
| R52 | reviewer 26/10 | Answer "why no artifact removal" with evidence |
| R53 | author 27/10 | Tool/app diagram at the end of Method; Results only results; channel attribution in Method and Results |
| R54 | author 28/10 | GAE stays the thesis system and headline; GAE + kNN shown as the improvement, kNN as the strongest baseline; demo unchanged |

## 4 · Decisions

- Earlier: rev 22–32 (in git or the project).
- **27–28/10 (V9):** research loop reopened (R13); Siena checked on 14 patients; R54; artifact veto and short-seizure
  branch not adopted (fixed rules); "hard patients" defined by measured EEG descriptors, not by duration; hospital EEG
  shown as qualitative; demo login fixed + start scripts + chb24; local cleanup done (Archive/2026-10-28/CLEANUP_LOG.md).
- **Open (author):** git push; chb24 ingest and demo rehearsal; the five optional fixes (2c); event number for the demo
  (`demo/DEMO_EVENT.md`); P1 committee fields; read the papers (summary §8).

## 5 · Plan of chats (from 28/10)

| # | date | task | output |
|---|---|---|---|
| V9 | 27–28/10 ✔ | reviewer feedback → research, experiments, EEG evidence, demo fix | V9 summary, NL §17, rev 33 |
| D9 | 28–30/10 | **slides:** integrate A42–A48 into the deck (new/changed pages, figures from §6 of the summary, comparison table, cut to 12 min) | Slides artifact update + Canva list, DECK_BRIEF rev 4.0, SLIDE_OUTLINE rev 9 |
| — | 29/10 | cô: run-through (Canva v5 + spoken V9 answers, or the D9 draft if ready) | feedback |
| D10 | 30/10–01/11 | script v3 (12 min) + Q&A update (V9 questions) + page map v6 | SCRIPT_v3, QA_BANK, QA_PAGE_MAP v6 |
| — | 02/11 | **mock defense** (cô + mentor) | feedback |
| D11 | 02–04/11 | fixes after the mock, timed read, demo cold-start checklist | final deck, DEMO_CHECKLIST |

**Start prompt of chat D9 (copy):**
> Chat D9 — slides after the reviewer's feedback. Read `STATUS_BOARD.md` (rev 33), `V9_RESULTS_SUMMARY.md` (all, esp.
> §0, §6, §9), `NUMBERS_LOCK.md` §17, `DECK_BRIEF.md` (rev 3.9), `SLIDE_OUTLINE.md` (rev 8), `QA_PAGE_MAP.md` (v5) and
> the Slides artifact of the deck. Attached: the Canva v5 PDF (and any slide I changed). Tasks: 1. Add A42–A48 to
> DECK_BRIEF §1. 2. Propose a new page map for 12 min of talk (+3 min demo): tool diagram to the end of Method;
> Results = system result, model comparison (matched false alarms), why patients are hard (EEG descriptors + one EEG
> panel), Siena explained, hospital EEG, channel attribution; comparison table with high-performing studies and the
> "same problem" criteria; optimization path incl. the two negative levers; backups for every V9 figure. Wait for my
> approval. 3. Then update the Slides artifact (same link) and give me the Canva change list page by page; I insert
> the EEG figures from `F:/Study/Thesis/Defense/slides/figs/`. Every number from NUMBERS_LOCK (§17 labelled "after the
> review"). End: board rev 34, file list, start prompt of D10.

## 6 · Which file for what

| File | Use it to | When |
|---|---|---|
| **`notes/V9_RESULTS_SUMMARY.md`** | reviewer points → answers, every V9 number, figure folders, papers to read, new slide requests | D9, D10, Q&A |
| `notes/NUMBERS_LOCK.md` (§1–§17) | every allowed number | always |
| `script/SCRIPT_v2.md` | script of Canva v5 (to be replaced by v3) | until D10 |
| `script/DEMO_SCRIPT.md` | demo path, fallback (page 60) | D11 |
| `qa/QA_PAGE_MAP.md` (v5), `qa/QA_BANK.md` | question → page; answers | D10 |
| `outline/DECK_BRIEF.md` (rev 3.9) | author requests A1–A41 (+A42–A48), lessons, §8 | D9 |
| `outline/SLIDE_OUTLINE.md` (rev 8) | page map; §0c = Canva v5 | D9 |
| `Defense/v9_reports/` | full V9 reports (T1–T4, C1, E1–E4, V1, cleanup) | when a detail is needed |
| `docs/V9_RESULTS_INDEX.md` (repo) | V9 task → script → results → commit | provenance questions |
| `web_demo/start_demo.sh`, `stop_demo.sh` (repo) | start/stop the demo | rehearsal, defense day |

## 7 · Layout

```
F:/Study/Thesis/
  Code/                       repository (public): docs/STATUS_BOARD.md, docs/V9_RESULTS_INDEX.md, docs/prompts/V9_*.md,
                              results/v9_*, src/v9_*.py, web_demo/ (start_demo.sh, stop_demo.sh)
  Reports/final/              submitted report (.docx) + Thesis_Final_Report.md
  Dataset/                    CHB-MIT, siena (14/14 verified), clinical (2 EDF; names in file names, never in the repo)
  Defense/
    notes/       NUMBERS_LOCK.md (§1–§17), V9_RESULTS_SUMMARY.md, D5_HANDOFF.md, FIGURE_PROVENANCE.md, APP_FACTS.md
    v9_reports/  11 V9 reports + cleanup report
    clinical/    clin0X_header.md, run/ (events, timelines, panels)
    slides/      Canva PDFs (v5 = deck of record); figs/ (eeg_samples/, eeg_samples/siena14/, eeg_evidence/part1–6/); gen/
    qa/ · outline/ · script/ · demo/ · content/ · inputs/ · review/
  Agent/inbox/                hand-over tray
  Archive/2026-10-28/         CLEANUP_LOG.md; board rev 32 and NUMBERS_LOCK before §17 (backups by the V9 script)
```

## 8 · Where the numbers are

| content | file |
|---|---|
| every number of the thesis system | `docs/PERF_PHASE_RECORD.md` (rev R) |
| what the committee read | `Thesis_Final_Report.md` |
| numbers allowed on slides | `Defense/notes/NUMBERS_LOCK.md` (§1–§15; §16 spoken only; §17 post-review, slide-allowed) |
| V9 results | `V9_RESULTS_SUMMARY.md`; `results/v9_*` (tag `v9-results`) |
| reproducibility checks | `docs/REPRODUCE.md`, `results/r1_repro/`, `results/r1_repro_2b/` |

## 9 · Decisions log

- 2026-10-15 → 21: defense phase; D1–D5 (rev 22–29 in git).
- 2026-10-22/23 (R1, D6): reproducibility checks; M1–M5, app diagram, script v1; rev 30–31.
- 2026-10-24 (D7): Canva v5 = deck of record; SCRIPT_v2; QA_PAGE_MAP v5; rev 32.
- 2026-10-26: reviewer's feedback (12 points).
- 2026-10-27/28 (V9): research loop reopened; Siena 14/14 verified; model comparison (R54); hard = focal, low amplitude;
  two negative levers; hospital EEG; EEG evidence parts 1–6; demo login fixed, start scripts, chb24 allowed; cleanup;
  NL §17; rev 33.
