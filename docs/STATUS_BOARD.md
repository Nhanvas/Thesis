# STATUS_BOARD — thesis report phase (rev 6, 2026-10-13, end of chat 5)

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
7. **The report is built, not pasted (13/10, chat 5).** The chapter markdown files stay the report of record;
   the Word document is produced from them by `src/report_build/build_v8.py` (pandoc + post-processing) and
   rendered by `render_pdf.py`. A change to the text is made in the chapter file and the document is rebuilt;
   edits made only in Word are lost at the next build.

## 2 · Where things stand (13/10, end of chat 5)

| track | state | next |
|---|---|---|
| Performance, external, attribution, demo | closed / finished (unchanged) | none |
| Report text | all chapters v8 + appendix; P-1 (Fig 14 panel d sentence) and P-2 (Table 3) closed in chat 5; abbreviations AUC, CI, CNN, F1 added | P-3 read by the author |
| Built document | `Reports/v8/build/Thesis_v8_NguyenQuocTrungNhan.docx` + `Thesis_v8_preview.pdf` (LibreOffice render): school template (title page, approval page, header logo), Times New Roman 12, 1.5 spacing, first-line indent 0.5 in, justified, margins left 1.5 in / others 1 in, ToC + list of tables + list of figures as Word fields, 29 table and 17 figure captions as SEQ fields, 12 numbered equations (Word equations), front matter roman, body arabic from Chapter 1, one reference list of 69 entries by first appearance | Figures 6 and 10 (see below); open in Word, update fields, measure pages |
| Figures in the build | 3, 8, 9, 11–17 from `Reports/v8/figures/` (15 = the three screens stacked as a, b, c); **1, 2, 4, 5, 7 provisional** = repository copies `figures/fig1_1…, fig1_2…, fig2_1…, fig2_2…, fig2_3…` (sha256 in `figure_sources.txt`), to be checked against `Reports/v8/figures_inherited/`; **6 and 10 = labelled placeholders** (the repository copies `fig2_4_pipeline.png` and `fig2_6_application_architecture.png` show the earlier system — PELT, three readouts — and must not be used) | author attaches `figures_inherited/` → rebuild |
| Pages (LibreOffice, measured) | **body 58 pages** (Ch1 11, Ch2 19, Ch3 17, Ch4 9, Ch5 2); front matter ix; references 6; appendix 13. Word may differ by about ±2 | author decision P-4 |
| Checks | gated tables 11, 13, 16, 17, 23, 24, 25 identical to `Reports/v8/tables/`; 4, 12, 14, 15, 19 same values (layout/rounding only); every Section/Table/Figure/Equation/Appendix reference resolves and every exhibit is cited; forbidden-number scan clean; abstract 299 words, keywords 10 words | `xanh` prose numbers, `en`, `hồng` (section 4 of the audit) |
| Git | board rev 6, `CLAIM_AUDIT_v8.md`, `CITATION_MAP_v8.md`, `src/report_build/` to commit (command in the chat reply) | — |

## 3 · Supervisor feedback on the 11/10 draft (12/10) → v8

| # | feedback | v8 answer | state |
|---|---|---|---|
| F1 | cut too much | full Ch2–Ch3, detail in Appendix A–F | done |
| F2 | results not detailed | Ch3 Tables 9–17, Figures 11–15, answer sentences | done |
| F3 | show methods that did not work | Table 10 (15 designs), Appendix C Table 22 (40 decisions), Discussion 4.2 (mechanism per choice) | done |
| F4 | external validation too thin | Section 3.4 (Tables 14–15, false-alarm drivers, boundaries, children → adults); Fig 14 panel e not possible (gate) | done |
| F5 | figures of detected seizures | Figure 14 (4 panels), Figures 12–13 | done |

## 4 · Approvals

**Approved earlier:** A1–A7; Table 3 keeps the draft's weeks; O1–O7; O8 answered; A-1 to A-4 (13/10);
page excess accepted when the content is needed (13/10).

**13/10, chat 5 (closed):**
- P-1: Figure 14 panel (d) sentence written from the author's reading (sustained high-amplitude activity
  on most channels from about the start of the event, no clearly spreading discharge, score above the
  threshold for most of the event; the figure does not show the cause). No cause and no saturation claim.
- P-2: Table 3 as pasted by the author; ■ rendered as shaded week cells.

**Pending (author):**

| # | item | where |
|---|---|---|
| P-3 | Hypotheses H1–H3 and contributions C1–C5 read once in context | built document, Section 1.3 |
| P-4 | Page count: body 58 pages (LibreOffice). The outline's cut menu (Figure 5 → Appendix A, Figure 9 → one sentence + appendix, Table 13 folded into Figure 13, 1.1.2 shortened, Table 10 to 8 rows) saves about 2–3 pages (estimated, not measured) and still leaves the body above 50; reaching 50 would need removing results the supervisor asked for (F1–F3). Recommendation: accept the excess, apply no cut | this board |
| P-5 | Margins: the build follows the written rule of `Report format.md` (left 1.5 in; top, bottom, right 1 in), not the margins of the template file (top and bottom 1.5 in, left and right 1 in) | built document |
| P-6 | `Reports/v8/figures_inherited/` (7 files) attached to the chat → rebuild with Figures 6 and 10 and a hash check of 1, 2, 4, 5, 7 | chat 5 (same chat) or chat 6 start |

## 5 · Layout

```
F:/Study/Thesis/
  Code/
    docs/STATUS_BOARD.md  docs/writing/CLAIM_AUDIT_v8.md  docs/writing/CITATION_MAP_v8.md (new)
    docs/writing/REPORT_OUTLINE_v8.md  docs/prompts/CC_FIGURES_V8*.md
    src/report_build/ build_v8.py, render_pdf.py, pagemap.py (new; run in a cloud chat: pandoc 3,
                      LibreOffice with Math, python-lxml, Pillow)
    src/figures_v8/  results/figures_v8_data/
  Reports/v8/
    chapters/   Front_matter_v8.md, Chapter_1_Introduction_v8.md … Chapter_5_Conclusion_v8.md
    appendix/   Appendix_v8.md
    figures/    fig03, fig08, fig09, fig11–fig14, fig16, fig17, app_screens/
    figures_inherited/   1, 2, 4, 5, 6, 7, 10 used as is
    tables/     chat-2 tables (source of Ch3 and Appendix tables)
    build/      Thesis_v8_NguyenQuocTrungNhan.docx, Thesis_v8_preview.pdf (new)
    Template.docx
  Dataset/siena/PN10/   (Figure 14 attempt; can stay)
```

## 6 · Plan of chats

| # | when | chat | task | output |
|---|---|---|---|---|
| 0–4 | 12–13/10 | thesis chats + Claude Code | inventory → outline → exhibits → all chapters v8 | done |
| 5 | 13/10 | "Check and assemble" | P-1, P-2 closed; document built; pages measured; tables, references, cross-references, abbreviations checked | done, except Figures 6 and 10 (P-6) |
| 5b | 13–14/10 morning | same chat if the author attaches `figures_inherited/`; otherwise first step of chat 6 | rebuild with all figures; author opens in Word, updates fields, reads P-3; accounts `xanh` (prose numbers vs chapter notes), `en` (English, `PROSE_STYLE_SPEC.md`), `hồng` (references vs `CITATION_MAP_v8.md`) | v8 to the supervisor 14/10 afternoon |
| 6 | 14–15/10 | thesis chat **"Final revision"** | supervisor comments → edit chapter files → rebuild → submission | submitted report |

**Length (script, prose words):** Ch1 ~2,350 · Ch2 ~4,370 · Ch3 ~2,640 · Ch4 ~2,840 · Ch5 ~510.

**Start prompt of chat 6 (copy):**
> Chat 6 — Final revision. Đọc `STATUS_BOARD.md` (rev 6) và `CLAIM_AUDIT_v8.md`. Nhận xét của cô: [dán / đính
> kèm]. Kết quả `xanh` / `en` / `hồng`: [dán hoặc "chưa có"]. P-3: [ok / sửa: …]. P-4: [chấp nhận 58 trang / cắt
> mục …]. P-5: [lề theo quy định / theo file template]. Đính kèm: `Reports/v8/` (zip: chapters, appendix, figures,
> figures_inherited, tables, Template.docx). Sửa vào file chương rồi build lại bằng `src/report_build/`.

Files chat 6 needs (project): this board, `CLAIM_AUDIT_v8.md`, `CITATION_MAP_v8.md`, all v8 chapter files +
`Appendix_v8.md`, `REPORT_OUTLINE_v8.md`, `Report format.md`, `PROSE_STYLE_SPEC.md`, `Thesis_Reference_Sheet.md`.

## 7 · Where the numbers are

| content | file |
|---|---|
| every number of the final system, decisions | `docs/PERF_PHASE_RECORD.md` (rev R) — authority |
| numbers as written, with sources and computed values | "Notes — not part of the report" at the end of each v8 chapter file |
| what was verified and how; open checks | `docs/writing/CLAIM_AUDIT_v8.md` |
| tables and figures (gated) | `Reports/v8/tables/`, `Reports/v8/figures/`; `src/figures_v8/` |
| per-seizure detection (final, held-out, 4 seeds) | `results/figures_v8_data/perseizure_final.csv` |
| development designs (report form) | Appendix C, Table 22 |
| references: working numbers per chapter → global numbers of the built document → DOI | `docs/writing/CITATION_MAP_v8.md`; sheet `docs/Thesis_Reference_Sheet.md` |

## 8 · Numbering of exhibits (v8, fixed)

Figures 1–3 Ch1 · 4–10 Ch2 · 11–15 Ch3 · 16–17 Ch4. Tables 1–3 Ch1 · 4–8 Ch2 · 9–17 Ch3 · 18 Ch4 ·
19–29 Appendix. Equations 1–12 in Ch2. References [1]–[69] in the built document (global, first appearance).

## 9 · Decisions log

- 2026-10-08: record 10.1. 2026-10-10: one reference list; supervisor's papers in Ch1/Ch4.
- 2026-10-12: one-task chats; outline v8 (O1–O6); exhibits; O7 approved without re-run; Ch2, Ch3, App v8.
- 2026-10-13 (author): continue in one chat for continuity; verification standard (section 1.6); A-1 by
  the per-patient table; A-2 confirmed; A-3 provisional; A-4 from code; page excess accepted when needed.
- 2026-10-13 (chat 3–4): code and source audit of Ch2 (14 corrections, `CLAIM_AUDIT_v8.md`); Ch3 3.3.3 and
  3.3.5 filled from the CC handback; Ch1, Ch4, Ch5, front matter v8 written; Figure 3 redrawn.
- 2026-10-13 (chat 5): P-1 and P-2 closed; the report is built from the chapter files (section 1.7); one
  global reference list by first appearance; N2, N3, N5 metadata resolved (Crossref, OpenAlex); body measured
  at 58 pages (LibreOffice); Figures 6 and 10 of the repository found to show the earlier system and kept out.
