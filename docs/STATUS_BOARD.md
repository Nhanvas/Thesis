# STATUS_BOARD — DEFENSE phase (rev 36, 2026-10-31, chat D9b: deck restructured to 12 minutes, 94 pages)

**Read this first in every chat, then `Defense/notes/V9_RESULTS_SUMMARY.md` (rev 2).** This board says what is done,
what is open and what the next steps are. It is rewritten as a whole file when a task ends (new rev number).

**Practical facts.**
- Defense **05–06/11/2026**, in English: **12 min talk + 3 min demo (right after the Conclusion) + 10 min Q&A**; the Q&A
  checks that the student did the work himself.
- **Mock defense with cô and the mentor: 02/11.** Supervisor meetings Thursdays 08:00.
- Reviewer: **TS. Ngô Thị Lụa** (12 points of 26/10 → `V9_RESULTS_SUMMARY.md` §0).
- Cô 30/10 on the D9 deck (too long, dense, no detected-seizure illustration) → **answered in D9b**: 22 main pages
  (18 content), 705 s = 11:45 at 110 words/min, p14 = real EEG of a detected seizure.
- After the defense: one round of report corrections (`REPORT_REVISION_NOTES.md`).

**Report.** Locked at the faculty submission (17/10/2026) until the committee's comments.

---

## 1 · Chat protocol (binding)

1. One task per chat from section 5 — **exception (author 31/10): chat D9b continues** through slides, answers, script
   and Q&A until the author is satisfied, so the context is not re-sent.
2. **Start:** read this board → the files named for the task.
3. **End of a task:** (a) this board rewritten (rev + 1); (b) **one** list for the author (project files add / replace /
   delete, with local paths); (c) the exact commands to install what was delivered.
4. Defense material lives in `F:/Study/Thesis/Defense/` (private). The repository (public) holds this board.
5. Every number on a slide, in the script or in an answer matches the report **and** `NUMBERS_LOCK.md`
   (§16 spoken only; §17 rev 2 + §17c allowed on slides, labelled "after the review").
6. **Order of work:** key messages ✔ → slides ✔ (D9b, page map rev 10) → **author: Canva v7** → **script to the page
   budgets** (SLIDE_OUTLINE rev 10 §1) → author approves → **one** timed read.
7. **Main pages fit 12 minutes** (A50): no new main page unless another goes (L26); Method keeps Data, Preprocessing,
   Evaluation (L31).
8. **Claude writes the script** (IELTS 5.5); the author reads, adapts and rephrases.
9. **Guidance goes directly in the chat**, short and detailed; files are records.
10. Every author request about slides is logged in `DECK_BRIEF.md` §1 (now A1–A72).
11. A review item quotes the text as it is now on the page.
12. **Changes go out as one zip + one `.sh`** that checks its base first.
13. **Research is an iterative loop**; experiments are closed (author 30/10).
14. **Claims about data, difficulty, false alarms, Siena, hospital data are backed by real EEG**, rule-selected.
15. **Never "low because unsupervised"**; never reuse a conclusion listed in summary §9 (DECK_BRIEF §3.12).
16. **A result enters a slide only after verification** (L27).
17. Heavy laptop jobs run **one at a time**, from Git Bash (not Cursor), browsers and MATLAB closed.
18. The word **"Appendix" is retired**: pages after Thank you are **Backup Slides** (A59).

## 2 · Where things stand (31/10, D9b)

| track | state | next |
|---|---|---|
| Experiments | **closed** (author 30/10); tag `v9-final` | none |
| Key messages | **K1–K5 approved** (A53) | script follows them |
| Deck | **page map rev 10 approved** (A65): Canva v7 = 94 pages, 22 main (18 content, 705 s), Backup Slides 23–94; Slides artifact = all 94 pages (link DECK_BRIEF §6); `D9B_CANVA_CHANGES.md` page by page + 31-item audit of old sentences | **author:** Canva v7 edits + PDF |
| Figures | p14 `figs/final/item1`, p16 `item5`, p17/p18 `figs/d9b/fig17`, `fig18` (gated); `d9_hard_patients.png` withdrawn; `figs/final/model_comparison.png` and `hard_patients_amp_ratio.png` not for slides (L29) | author inserts in Canva; open "Insert in Canva" boxes: F4 (3 panels), G4 (2), I3, I5 (2), I6, I7, I11, I12, I13 |
| Numbers | NUMBERS_LOCK §17 rev 2 + **§17c (D9b)** appended by the install script | `xanh` check of Canva v7 |
| Author's 70 questions | answered: `notes/STUDY_GUIDE_part3_vi.md` (new) | study guide parts 1–2 → rev 2 (outdated answers) |
| Q&A | `QA_V9.md` (16); `QA_BANK.md`; `QA_PAGE_MAP.md` v5 (old pages) | QA page map for v7 pages (this chat) |
| Script | `SCRIPT_v2.md` = Canva v5 (obsolete) | **SCRIPT_v3** to the budgets (this chat) |
| Demo | login fixed; start/stop scripts; chb24 allowed | **author:** ingest chb24 (≈ 8 min), two cold-start runs, fallback video |
| Report | `REPORT_REVISION_NOTES.md` | after the defense |

## 3 · Feedback and rules in force

R1–R61 stand. Added 31/10 (D9b):

| # | source | rule |
|---|---|---|
| R62 | author (A54) | P-V9a: GAE = thesis system and headline; p17 states kNN ≥ GAE honestly; never "GAE + kNN is the improvement" |
| R63 | author (A55) | P-V9b: Siena 0.633 / 0.160 (report numbers) on slides |
| R64 | author (A56) | Objective 3 = one line on p12 and p20; EEG panels on F4 |
| R65 | D9b (L28, L29, L33) | Every table row's label checked against its NUMBERS_LOCK line (detector named); figures for main pages checked for internal labels and palette; times read from the label file |
| R66 | author (A62) | chb24 = "one more unseen CHB-MIT patient" (not external); Siena = only external dataset; not merged into the 8 test patients |
| R67 | author (A63) | Result pages show the **per-patient mean** only; pooled on E11 and in answers |
| R68 | author (A59–A61) | "Backup Slides", never "Appendix"; no old backup page deleted; Method keeps Data, Preprocessing, Evaluation |
| R69 | author (A64) | wPLI/AEC weights: answer "fixed at 0.5/0.5 before any test, not tuned; testing them is future work" — no new run |
| R70 | author (A66) | Script says early: the GAE learns only from seizure-free windows; "normal" = the patient's whole recording; the task is review triage, not a real-time alarm, because long-term EEG is read after recording |

## 4 · Decisions

- Earlier: rev 22–35 (in git or the project).
- **31/10 (D9b):** P-V9a = GAE headline, honest page; P-V9b = keep 0.633 / 0.160; K1–K5 approved; Objective 3 → F4 +
  one line; chb24 separate, reworded; per-patient mean only on result pages; 18 content pages (Data, Preprocessing,
  Evaluation restored); no wPLI/AEC run; page map rev 10 (94 pages) "Approve, build it"; "Backup Slides".
- **Open (author):** Canva v7; chb24 ingest and demo rehearsal; demo event number; P1 committee fields; papers (summary
  §13); check the Mullen 2015 DOI before printing References.

## 5 · Plan (from 31/10)

| # | date | task | output |
|---|---|---|---|
| D9b | 31/10 ✔ | slides for 12 min: key messages, page map rev 10, artifact (94 p), Canva list, audit, 70 answers | DECK_BRIEF 4.2, SLIDE_OUTLINE 10, D9B_CANVA_CHANGES, NL §17c, figs/d9b, STUDY_GUIDE_part3, rev 36 |
| — | 31/10–01/11 | **author:** install bundle; Canva v7 edits + PDF (`D9B_CANVA_CHANGES.md`) | Canva v7 PDF |
| D9b (cont.) | 01/11 | **same chat:** check Canva v7 PDF; **SCRIPT_v3** (≈ 1,290 words to the page budgets) + demo path; **QA_PAGE_MAP v7**; STUDY_GUIDE parts 1–2 rev 2; rehearsal list | SCRIPT_v3, QA_PAGE_MAP v7, study guides, rev 37 |
| — | 02/11 | **mock defense** | feedback |
| D11 | 02–04/11 | fixes, timed read, demo cold-start checklist | final deck |

**If a new chat is ever needed (fallback start prompt):**
> Continue the defense work of chat D9b. Read `STATUS_BOARD.md` (rev 36), `DECK_BRIEF.md` (rev 4.2: §0b, §3.12, §8,
> A50–A72, L22–L33), `SLIDE_OUTLINE.md` (rev 10), `V9_RESULTS_SUMMARY.md` (rev 2, §9, §12), `NUMBERS_LOCK.md` (§1, §8,
> §17 rev 2, §17c), `STUDY_GUIDE_part3_vi.md`, `QA_V9.md`, `QA_BANK.md`, `QA_PAGE_MAP.md`, `DEMO_SCRIPT.md`,
> `Kangabu_defense_tips.md`, and the speaker notes of the Slides artifact (DECK_BRIEF §6). Attached: my Canva v7 PDF.
> Tasks: check the PDF against `D9B_CANVA_CHANGES.md`; write `SCRIPT_v3.md` (IELTS 5.5, 110 words/min, per page:
> message · eye path · transition; count words); `QA_PAGE_MAP.md` v7; correct `STUDY_GUIDE_part1/2_vi.md` (rev 2).

## 6 · Which file for what

| File | Use it to | When |
|---|---|---|
| `notes/V9_RESULTS_SUMMARY.md` (rev 2) | every post-review result, its evidence and limits; overturned conclusions §9 | always |
| `notes/NUMBERS_LOCK.md` (§1–§17 rev 2, §17b, §17c) | every allowed number | always |
| `outline/DECK_BRIEF.md` (rev 4.2) | author requests A1–A72, lessons L1–L33, design | slide or script work |
| `outline/SLIDE_OUTLINE.md` (rev 10) | key messages, page map 1–94, page budgets, 70 questions → pages | script, Q&A |
| `outline/D9B_CANVA_CHANGES.md` | Canva v6 → v7, page by page; audit of old sentences | author; PDF check |
| `notes/STUDY_GUIDE_part3_vi.md` | answers to the author's 70 questions | rehearsal |
| `slides/figs/final/FIGURE_INDEX.md`, `slides/figs/d9b/` | slide figures and selection rules | Canva |
| `qa/QA_V9.md`, `qa/QA_BANK.md`, `qa/QA_PAGE_MAP.md` | answers; page map (v5 → v7 next) | rehearsal |
| `script/SCRIPT_v2.md`, `script/DEMO_SCRIPT.md` | old script; demo path | script v3 |
| `notes/REPORT_REVISION_NOTES.md` | what the final report must change | after the defense |
| `Defense/v9_reports/` | full V9 reports | detail |
| `docs/V9_RESULTS_INDEX.md` (repo) | task → script → results → commit | provenance |

## 7 · Layout

```
F:/Study/Thesis/
  Code/                       repository (public): docs/STATUS_BOARD.md, docs/V9_RESULTS_INDEX.md, results/v9_*, src/v9_*.py, web_demo/
  Reports/final/              submitted report (.docx) + Thesis_Final_Report.md
  Dataset/                    CHB-MIT, siena (14/14), clinical (2 EDF; names in file names, never in the repo)
  Defense/
    notes/       NUMBERS_LOCK.md (+§17c), V9_RESULTS_SUMMARY.md, STUDY_GUIDE_part1-3_vi.md, REPORT_REVISION_NOTES.md, ...
    qa/          QA_BANK.md, QA_PAGE_MAP.md, QA_V9.md
    outline/     DECK_BRIEF.md (4.2), SLIDE_OUTLINE.md (10), D9B_CANVA_CHANGES.md
    slides/      Canva PDFs; figs/ (final/, d9b/, d9/, eeg_samples/, eeg_evidence/, x1, x6); gen/ (d9/, d9b/)
    v9_reports/ · clinical/ · script/ · demo/ · content/ · inputs/ · review/
  Agent/inbox/                hand-over tray (D9b2/ install bundle)
  Archive/2026-10-31-d9b/     backups made by the D9b install script (incl. D9_CANVA_CHANGES.md)
```

## 8 · Where the numbers are

| content | file |
|---|---|
| every number of the thesis system | `docs/PERF_PHASE_RECORD.md` (rev R) |
| what the committee read | `Thesis_Final_Report.md` |
| numbers allowed on slides | `NUMBERS_LOCK.md` (§1–§15; §16 spoken only; §17 rev 2 + §17c post-review and deck) |
| post-review results | `V9_RESULTS_SUMMARY.md` rev 2; `results/v9_*`; `results/v9_final/NUMBERS_CHECK.md` |

## 9 · Decisions log

- 2026-10-15 → 24: defense phase D1–D7 (rev 22–32).
- 2026-10-26: reviewer's feedback (12 points).
- 2026-10-27/28 (V9): research loop; rev 33.
- 2026-10-30 (D9): page map v6 (78 p); rev 34.
- 2026-10-30/31 (V9 part 2): X1, X3, X6, V1-FIX, FINAL; three conclusions withdrawn; cô's slide feedback; rev 35.
- 2026-10-31 (D9b): P-V9a, P-V9b, K1–K5; first 12-minute map (86 p, never installed) → author's 70 questions → page map
  rev 10 (94 p, 22 main, 705 s): Data, Preprocessing, Evaluation restored; per-patient mean only; chb24 reworded;
  "Backup Slides"; new backups A2, A3, A5, A6, B7–B9, D6, E13; 31 old sentences corrected (incl. a mislabelled row on
  v6 p24, the chb03 annotation times, the detector behind "chb14 8/8"); Slides artifact with all pages; rev 36.
