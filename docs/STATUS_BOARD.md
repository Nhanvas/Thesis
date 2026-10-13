# STATUS_BOARD — thesis report phase (rev 9, 2026-10-13, end of chat 8)

**Read this first in every chat.** It says what is done, what is open, what the author still has to
approve, where every file lives, and what the next chat does. At the end of every chat the board is
rewritten as a whole file (new rev number) and delivered with the project file list.

Deadlines: send v8 to the supervisor **14/10 (afternoon)** · submission (draft) **15/10** · defense
**05–06/11** · final copy after the committee's comments.

---

## 1 · Chat protocol (binding)

1. One task per chat from section 6, unless the author decides otherwise.
2. Start: read this board → the files named for the task → nothing else unless the task needs it.
3. End: (a) this board rewritten (rev + 1); (b) **one** list for the author (project files add / replace /
   delete, with local paths); (c) the start prompt of the next chat. Nothing is left only in the chat.
4. Files go to their place in the layout of section 5. `Agent/inbox/` is a hand-over tray only.
5. Long runs go to Claude Code on the laptop; every prompt states its estimated runtime.
6. **Verification standard (author, 13/10):** every claim is checked against its primary source. Record in
   `docs/writing/CLAIM_AUDIT_v8.md`. Checks the author has already run are trusted and not asked again.
7. **The report is built, not pasted.** The chapter markdown files are the report of record; the Word
   document is produced from them by `src/report_build/build_v8.py` and checked by
   `src/report_build/check_v8.py`. Edits made only in Word are lost at the next build. **Zotero citations
   are inserted after the last build** (a rebuild removes them).
8. No PDF is produced by the chats; a LibreOffice render is used only to measure pages.

## 2 · Where things stand (13/10, end of chat 8)

| track | state | next |
|---|---|---|
| Performance, external, attribution, demo | closed / finished (unchanged) | none |
| Report text | chat-7 text + `en` polish (accepted after a word-level diff; numbers, [n], references, tables, equations, Notes unchanged) + 1 fix (comma splice in 4.1) + Table 18 moved to the end of 4.1 (layout) | supervisor comments (chat 9) |
| Built document | `Reports/v8/build/Thesis_v8_NguyenQuocTrungNhan.docx` (chat 8, sha256 `3b5848f424a5928d…`): 26 tables, 16 figures, 12 equations, 67 references; margins left 1.5 in, others 1 in; every table 12 pt; Tables 12, 18, 22 on landscape pages | author: Word F9, Zotero, send |
| Pages (LibreOffice, measured) | **Chapters 1–5: 60 pages** (Ch1 11, Ch2 21, Ch3 17, Ch4 9, Ch5 2); front matter 9 (i–ix); references 6; appendix 13; total 88. **Count of Report format.md** (total minus list of tables, list of figures, appendices, references): **67 pages**. Word measured about 2 pages less than LibreOffice on earlier builds | over the limit by the author's choice (section 4) |
| Checks (chat 8, `check_v8.py`, PASS) | captions in sequence, every exhibit cited, every reference resolves, 67 references in first-appearance order, no forbidden number or internal label, abstract 299 words, all tables 12 pt, margins on every section; numbers and citations identical to the chat-7 docx except one "4s" (wording "4s for both") | repeat after every rebuild |
| References | numbering unchanged from chat 7 (`reference_map.json` identical); `CITATION_MAP_v8.md` (67) still valid | Zotero after the last build |

## 3 · Supervisor feedback on the 11/10 draft (12/10) → v8

| # | feedback | v8 answer | state |
|---|---|---|---|
| F1 | cut too much | full Ch2–Ch3, detail in Appendix A–F | done |
| F2 | results not detailed | Ch3 Tables 9–17, Figures 11–15 | done |
| F3 | show methods that did not work | Table 10, Appendix C Table 22 (40 decisions), Discussion 4.2 | done |
| F4 | external validation too thin | Section 3.4, Table 18 | done |
| F5 | figures of detected seizures | Figure 14, Figures 12–13 | done |

Supervisor comments on v8: **not yet received** (v8 goes out 14/10 afternoon).

## 4 · Approvals

**Approved earlier:** A1–A7; O1–O8; A-1 to A-4; P-1 to P-6; P-8, P-9; C4/novelty wording; author feedback 1–10.

**13/10, chat 8 (author's answers to the five page/format questions):**
1. The 50-page limit counts the whole thesis except the lists of tables and figures, appendices and
   references (Report format.md). The report stays over it: content is kept, the deduction is accepted
   (no forced cut that would repeat the 12/10 "cut too much"). `CUT_PLAN_50p.md` is **not applied**.
2. How strict the limit is: the author asks the supervisor later; keep the present length (cut only where
   quality does not suffer).
3. Margins: left 1.5 in, top/bottom/right 1 in (Report format.md and the template's own text). **Supersedes
   P-5** (the template file's section had top/bottom 1.5 in). Applied.
4. Tables: no 10-pt font; every table at 12 pt, fitted by column widths and, where it cannot fit, a
   landscape page. Applied (Tables 12, 18, 22 landscape).
5. 15/10 is the draft; the committee's comments after the defense go into the final copy. The template may
   be outdated; follow it only for margins and tables.

**Pending:**

| # | item | who |
|---|---|---|
| P-10 | Appendix choices of chat 7 (old Tables 25, 27, 29 → sentences; Table 22 kept whole) — revert any on request | author |
| P-11 | Left open by `en`: (a) Acknowledgements keep "I" / "my" (style spec allows it there)? (b) "pediatric", "localize" (US) beside "colour", "labelled" (UK) — keep, or unify? (c) the chapter-roadmap sentence at the end of Section 1.6 — keep or drop? Chat 8 left all three as written | author |
| P-12 | Page-limit strictness (question 2) | author → supervisor |

## 5 · Layout

```
F:/Study/Thesis/
  Code/
    docs/STATUS_BOARD.md  docs/writing/CLAIM_AUDIT_v8.md (section 8 new)  docs/writing/CITATION_MAP_v8.md
    docs/writing/CUT_PLAN_50p.md (not applied)  docs/prompts/EN_POLISH_v8.md
    docs/writing/REPORT_OUTLINE_v8.md
    src/report_build/ build_v8.py (chat 8: margins, 12-pt tables, column widths, landscape sections),
                      check_v8.py (new), render_pdf.py, pagemap.py
  Reports/v8/
    chapters/   Front_matter_v8.md, Chapter_1 … Chapter_5 (chat 8 = `en` + Ch4 fixes)
    appendix/   Appendix_v8.md (chat 8 = `en`)
    figures/  figures_inherited/  tables/  Template.docx
    build/      Thesis_v8_NguyenQuocTrungNhan.docx, figure_sources.txt, reference_map.json (chat 8)
  Archive/2026-10-13/chat7_v8/   chapters, appendix and build of chat 7 (superseded)
  Archive/2026-10-13/chat6_v8/   chat 6 (superseded)
```

Cloud build layout: `/home/claude/in/` = unzipped `Reports/v8/`, `/home/claude/work/{chapters,appendix}` =
the chapter files, `/home/claude/repo/` = repository clone. Build: `python3 repo/src/report_build/build_v8.py`;
check: `python3 repo/src/report_build/check_v8.py build/out/Thesis_v8_NguyenQuocTrungNhan.docx`; measure:
`render_pdf.py` then `pagemap.py`.

## 6 · Plan of chats

| # | when | who | task | output |
|---|---|---|---|---|
| 0–8 | 12–13/10 | thesis chats | inventory → outline → exhibits → chapters → build → revisions → `en` check and final build | done |
| — | 14/10 | author | Word: open the docx, F9 (fields: contents, lists, captions); Zotero (67 references, `CITATION_MAP_v8.md`); check the three landscape pages print the right way round; read once; answer P-11; send to the supervisor | v8 sent |
| 9 | 14–15/10 | thesis chat "Final revision" | supervisor comments and P-11 → chapter files → rebuild → check → submission | submitted draft |

**Start prompt of chat 9 (copy):**
> Chat 9 — Final revision. Đọc `STATUS_BOARD.md` (rev 9). Đính kèm: nhận xét của cô về v8 (nếu có), trả lời
> P-11 (Acknowledgements "I/my"; chính tả US/UK; câu roadmap cuối Section 1.6). [Nếu là chat mới: thêm zip
> `Reports/v8/`.] Sửa file chương theo nhận xét, build lại bằng `src/report_build/`, chạy `check_v8.py`, đo
> trang. Không tạo PDF.

## 7 · Where the numbers are

| content | file |
|---|---|
| every number of the final system, decisions | `docs/PERF_PHASE_RECORD.md` (rev R) — authority |
| numbers as written, with sources | "Notes — not part of the report" of each chapter file |
| what was verified and how | `docs/writing/CLAIM_AUDIT_v8.md` |
| benchmark entries on Siena | `docs/BENCHMARK_CHECK_szcore_c57da2f.md`; `esl-epfl/szcore` c57da2f |
| tables and figures (gated) | `Reports/v8/tables/`, `Reports/v8/figures/` |
| references: working → global → DOI | `docs/writing/CITATION_MAP_v8.md` |

## 8 · Numbering of exhibits (unchanged from chat 7)

Figures 1–3 Ch1 · 4–10 Ch2 · 11–15 Ch3 · 16 Ch4. Tables 1–3 Ch1 · 4–8 Ch2 · 9–17 Ch3 · 18 Ch4 · 19–26
Appendix. Equations 1–12 in Ch2. References [1]–[67] (global, first appearance).

## 9 · Decisions log

- 2026-10-08: record 10.1. 2026-10-10: one reference list; supervisor's papers in Ch1/Ch4.
- 2026-10-12: one-task chats; outline v8; exhibits; Ch2, Ch3, App v8.
- 2026-10-13 (chats 3–5): code and source audit; all chapters v8; build from the chapter files; 58 pages.
- 2026-10-13 (chat 6): P-3 corrections; "no seizure label of the patient under review"; template margins.
- 2026-10-13 (chat 7): author feedback 1–10 applied; N1 removed; P-8 closed; P-9 applied; cut plan
  prepared, not applied; body 62 pages (LibreOffice).
- 2026-10-13 (chat 8): `en` accepted after diff; comma splice fixed; Table 18 to the end of 4.1; margins
  left 1.5 / others 1 in (supersedes P-5); every table 12 pt with landscape pages for Tables 12, 18, 22;
  template cell margins and table grid fixed; `check_v8.py` added; page limit exceeded by choice (cut plan not
  applied); Chapters 1–5 60 pages, Report-format count 67 (LibreOffice).
