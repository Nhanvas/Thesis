# STATUS_BOARD — thesis report phase (rev 5, 2026-10-13, end of chat 4)

**Read this first in every chat.** It says what is done, what is open, what the author still has to
approve, where every file lives, and what the next chat does. At the end of every chat the board is
rewritten as a whole file (new rev number) and delivered with the project file list.

Deadlines: send v8 to the supervisor **14/10 (afternoon)** · submission **15/10** · defense **05–06/11**.

---

## 1 · Chat protocol (binding)

1. One task per chat from section 6, unless the author decides otherwise (13/10: chats 3 and 4 were done in
   one chat, by the author's choice, for continuity between chapters).
2. Start: read this board → the files named for the task → nothing else unless the task needs it.
3. End: (a) this board rewritten (rev + 1); (b) **one** list for the author (project files add / replace /
   delete, with local paths); (c) the start prompt of the next chat. Nothing is left only in the chat.
4. Files go to their place in the layout of section 5. `Agent/inbox/` is a hand-over tray only.
5. Long runs go to Claude Code on the laptop; every prompt states its estimated runtime.
6. **Verification standard (author, 13/10):** every claim is checked against its primary source — result
   files for numbers, the running code for methods, the raw data/PhysioNet/WHO pages for dataset facts, the
   reference sheet's verified quotes for literature. Record in `docs/writing/CLAIM_AUDIT_v8.md`.

## 2 · Where things stand (13/10, 02:00)

| track | state | next |
|---|---|---|
| Performance, external, attribution, demo | closed / finished (unchanged) | none |
| Figures | all v8 figures exist: 1, 2, 4, 5, 7 inherited (checked); 6, 10 draft drawings (final system); **3 new** (`Reports/v8/figures/fig03_framework.png`, chat 4); 8, 9, 11, 13, 16, 17 (chat 2); **12, 14 (Claude Code, 12–13/10; Fig 14 four panels, panel e skipped by its gate: PN10 rebuilt on the laptop gave fp 17 vs committed 18)**; 15 screens | author: look at Fig 14 panel d |
| Report | **all chapters v8 written**: Ch1, Ch2, Ch3, Ch4, Ch5, front matter, Appendix A–F (`Reports/v8/chapters/`, `Reports/v8/appendix/`). Ch2–3 corrected after the 13/10 code and source audit (`CLAIM_AUDIT_v8.md` §2) | chat 5: assemble, build, check |
| Git | board rev 4 + CC figures committed (`51ddf6e`); board rev 5 + `CLAIM_AUDIT_v8.md` to commit (command in the chat reply) | — |

## 3 · Supervisor feedback on the 11/10 draft (12/10) → v8

| # | feedback | v8 answer | state |
|---|---|---|---|
| F1 | cut too much | full Ch2–Ch3, detail in Appendix A–F | done |
| F2 | results not detailed | Ch3 Tables 9–17, Figures 11–15, answer sentences | done |
| F3 | show methods that did not work | Table 10 (15 designs), Appendix C Table 22 (40 decisions), Discussion 4.2 (mechanism per choice) | done |
| F4 | external validation too thin | Section 3.4 (Tables 14–15, false-alarm drivers, boundaries, children → adults); Fig 14 panel e not possible (gate) | done |
| F5 | figures of detected seizures | Figure 14 (4 panels), Figures 12–13 | done |

## 4 · Approvals

**Approved earlier:** A1–A7; Table 3 keeps the draft's weeks; O1–O7; O8 answered.

**13/10 (author):**
- A-1 resolved by audit: Siena sexes from the per-patient table (8 men 25–71, 6 women 20–58); the
  disagreement with PhysioNet's prose and the paper (9/5) noted in Appendix A.
- A-2 confirmed: 16 GB laptop = the timing machine.
- A-3 provisionally approved (Appendix E protocol wording); author reads later.
- A-4 resolved from code: first timing stage = reading, filtering and windowing (`process_file_phase_a`).
- **Page budget:** if the built body exceeds 50 pages, the excess is accepted when the content is needed;
  cuts only where nothing is lost (outline §2 cut order as a menu, not an obligation).
- Chats 3 and 4 done in one chat (continuity).

**Pending (author):**

| # | item | where |
|---|---|---|
| P-1 | Figure 14 panel (d): one clause on what the EEG shows (CHECK marker) | Ch3 3.3.5 |
| P-2 | Table 3: paste the 11/10 draft's table unchanged (row labels and week shading) | Ch1 1.5 |
| P-3 | Hypotheses H1–H3 and contributions C1–C5 wording (outline §1, approved with O2) read once in context | Ch1 1.3 |

## 5 · Layout

```
F:/Study/Thesis/
  Code/
    docs/STATUS_BOARD.md  docs/writing/CLAIM_AUDIT_v8.md (new)  docs/writing/REPORT_OUTLINE_v8.md
    docs/prompts/CC_FIGURES_V8.md, CC_FIGURES_V8_HANDBACK.md (done)
    src/figures_v8/  results/figures_v8_data/ (per-seizure file, gallery a–d)
  Reports/v8/
    chapters/   Front_matter_v8.md, Chapter_1_Introduction_v8.md … Chapter_5_Conclusion_v8.md
    appendix/   Appendix_v8.md
    figures/    fig03_framework.png (new), fig08, fig09, fig11, fig12, fig13, fig14, fig16, fig17, app_screens/
    figures_inherited/   1, 2, 4, 5, 6, 7, 10 used as is
    tables/     chat-2 tables (source of Ch3 and Appendix tables)
  Dataset/siena/PN10/   (Figure 14 attempt; can stay)
```

## 6 · Plan of chats

| # | when | chat | task | output |
|---|---|---|---|---|
| 0–4 | 12–13/10 | thesis chats + Claude Code | inventory → outline → exhibits → all chapters v8 | done |
| 5 | 13/10 | thesis chat **"Check and assemble"** (new chat, or this one if the author prefers) + accounts `xanh`, `en`, `hồng` | (1) close P-1–P-3; (2) build one .docx from the chapter files with figures, tables, numbered equations, captions and the reference list (Zotero); (3) measure pages; (4) `xanh` number check vs chapter notes; `hồng` references incl. N1–N3, N5; `en` English polish; (5) CLAIM_AUDIT §4 closed | v8 for the supervisor (14/10 afternoon) |
| 6 | 14–15/10 | thesis chat **"Final revision"** | supervisor comments → submission | submitted report |

**Length (script, prose words; tables, equations, headings excluded):** Ch1 ~2,350 · Ch2 ~4,370 ·
Ch3 ~2,640 · Ch4 ~2,840 · Ch5 ~510 → ~12,700 (outline 9,700). Pages not yet measured: build first.

**Start prompt of chat 5 (copy):**
> Chat 5 — Check and assemble. Đọc `STATUS_BOARD.md` (rev 5) và `CLAIM_AUDIT_v8.md`, làm task #5. P-1 (panel d
> Fig 14): [điền]. P-2 Table 3: [đã dán / chưa]. Đính kèm: `Reports/v8/` (zip: chapters, appendix, figures,
> tables) và file Word template nếu có.

Files chat 5 needs (project): this board, `CLAIM_AUDIT_v8.md`, all v8 chapter files + `Appendix_v8.md`,
`REPORT_OUTLINE_v8.md`, `Report format.md`, `AUTHOR_REQUIREMENTS.md`, `PROSE_STYLE_SPEC.md`,
`Thesis_Reference_Sheet.md`, `CC_FIGURES_V8_HANDBACK.md`.

## 7 · Where the numbers are

| content | file |
|---|---|
| every number of the final system, decisions | `docs/PERF_PHASE_RECORD.md` (rev R) — authority |
| numbers as written, with sources and computed values | "Notes — not part of the report" at the end of each v8 chapter file |
| what was verified and how; open checks | `docs/writing/CLAIM_AUDIT_v8.md` |
| tables and figures (gated) | `Reports/v8/tables/`, `Reports/v8/figures/`; `src/figures_v8/` |
| per-seizure detection (final, held-out, 4 seeds) | `results/figures_v8_data/perseizure_final.csv` |
| development designs (report form) | Appendix C, Table 22 |
| references and DOIs | `docs/Thesis_Reference_Sheet.md`; [n] → DOI table at the end of each chapter file |

## 8 · Numbering of exhibits (v8, fixed)

Figures 1–3 Ch1 · 4–10 Ch2 · 11–15 Ch3 · 16–17 Ch4. Tables 1–3 Ch1 · 4–8 Ch2 · 9–17 Ch3 · 18 Ch4 ·
19–29 Appendix. Equations 1–12 in Ch2.

## 9 · Decisions log

- 2026-10-08: record 10.1. 2026-10-10: one reference list; supervisor's papers in Ch1/Ch4.
- 2026-10-12: one-task chats; outline v8 (O1–O6); exhibits; O7 approved without re-run; Ch2, Ch3, App v8.
- 2026-10-13 (author): continue in one chat for continuity; verification standard (section 1.6); A-1 by
  the per-patient table; A-2 confirmed; A-3 provisional; A-4 from code; page excess accepted when needed.
- 2026-10-13 (chat 3–4): code and source audit of Ch2 (14 corrections, `CLAIM_AUDIT_v8.md`); Ch3 3.3.3 and
  3.3.5 filled from the CC handback; Ch1, Ch4, Ch5, front matter v8 written; Figure 3 redrawn.
