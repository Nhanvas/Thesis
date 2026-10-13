# STATUS_BOARD — thesis report phase (rev 7, 2026-10-13, end of chat 6)

**Read this first in every chat.** It says what is done, what is open, what the author still has to
approve, where every file lives, and what the next chat does. At the end of every chat the board is
rewritten as a whole file (new rev number) and delivered with the project file list.

Deadlines: send v8 to the supervisor **14/10 (afternoon)** · submission **15/10** · defense **05–06/11**.

---

## 1 · Chat protocol (binding)

1. One task per chat from section 6, unless the author decides otherwise.
2. Start: read this board → the files named for the task → nothing else unless the task needs it.
3. End: (a) this board rewritten (rev + 1); (b) **one** list for the author (project files add / replace /
   delete, with local paths); (c) the start prompt of the next chat. Nothing is left only in the chat.
4. Files go to their place in the layout of section 5. `Agent/inbox/` is a hand-over tray only.
5. Long runs go to Claude Code on the laptop; every prompt states its estimated runtime.
6. **Verification standard (author, 13/10):** every claim is checked against its primary source — result
   files for numbers, the running code for methods, the raw data/PhysioNet/WHO pages for dataset facts, the
   reference sheet's verified quotes for literature. Record in `docs/writing/CLAIM_AUDIT_v8.md`.
7. **The report is built, not pasted.** The chapter markdown files are the report of record; the Word
   document is produced from them by `src/report_build/build_v8.py`. A change to the text is made in the
   chapter file and the document is rebuilt; edits made only in Word are lost at the next build.
8. **Citations (author, 13/10):** the author inserts the citations with Zotero in the built document; the
   build keeps the numeric [n] and the reference list as the checkable reference (`CITATION_MAP_v8.md`). No
   PDF is produced by the chats; a LibreOffice render is used only to measure pages.

## 2 · Where things stand (13/10, end of chat 6)

| track | state | next |
|---|---|---|
| Performance, external, attribution, demo | closed / finished (unchanged) | none |
| Report text | all chapters v8 + appendix, revised in chat 6 from the P-3 reading, `xanh`, `hồng` and a cross-review (23 corrections, `CLAIM_AUDIT_v8.md` section 6); Table 9 rows 1–2 corrected to the three-readout ensemble, new row 0.553 | supervisor comments (chat 7) |
| Built document | `Reports/v8/build/Thesis_v8_NguyenQuocTrungNhan.docx` rebuilt 13/10 (chat 6): all 17 figures (no placeholder), margins of the template file (P-5), tall figures bounded to fit the page with their caption | author: open in Word, update fields (F9), insert citations with Zotero, send to the supervisor |
| Figures | 1, 2, 4, 5, 7 from `figures_inherited/`, byte-identical to the repository copies; 6 and 10 from `figures_inherited/`, checked: final system; others unchanged | — |
| Pages (LibreOffice, measured) | **body 65 pages** (Ch1 11, Ch2 24, Ch3 18, Ch4 10, Ch5 2); front matter x; references 6; appendix 14. With the earlier margins the same text is 61 pages: the template margins cost 4 pages, Figures 6 and 10 and the chat-6 text about 3. Word may differ by about ±2 | P-7 |
| Checks (chat 6, script over the build) | captions 29 + 17 beside their exhibits; every Section/Table/Figure reference resolves, every exhibit cited; 12 equations; 69 references, none unmapped; forbidden numbers none; no "expert", no "at any step"; abstract 299 words, one page | `en` not yet run |
| References | global numbers changed for three entries (E11 [28], N5 [29], K4 [30]); `CITATION_MAP_v8.md` regenerated from the build | Zotero metadata list in `CLAIM_AUDIT_v8.md` section 4 |
| Git | board rev 7, `CLAIM_AUDIT_v8.md`, `CITATION_MAP_v8.md`, `src/report_build/build_v8.py` to commit (command in the chat reply) | — |

## 3 · Supervisor feedback on the 11/10 draft (12/10) → v8

| # | feedback | v8 answer | state |
|---|---|---|---|
| F1 | cut too much | full Ch2–Ch3, detail in Appendix A–F | done |
| F2 | results not detailed | Ch3 Tables 9–17, Figures 11–15, answer sentences | done |
| F3 | show methods that did not work | Table 10 (15 designs), Appendix C Table 22 (40 decisions), Discussion 4.2 | done |
| F4 | external validation too thin | Section 3.4 (Tables 14–15, false-alarm drivers, boundaries, children → adults) | done |
| F5 | figures of detected seizures | Figure 14 (4 panels), Figures 12–13 | done |

Supervisor comments on v8: **not yet received** (v8 goes out 14/10 afternoon).

## 4 · Approvals

**Approved earlier:** A1–A7; Table 3 keeps the draft's weeks; O1–O7; O8 answered; A-1 to A-4; page excess
accepted when the content is needed; P-1, P-2.

**13/10, chat 6 (closed):**
- P-3: H1–H3 and C1–C5 corrected as in the reviewer's reading (lead sentence "before the held-out
  evaluation"; C1 same readout with different reference fits; C2 drift separated from the test-informed
  budget; C3 offsets not improved; C5 with its result).
- C4 / novelty: "no seizure label of the patient under review" (author's choice), in the abstract, 1.2,
  C4, Table 2, 3.6, 4.1 and Chapter 5.
- P-4: 58 pages accepted, no cut (decided before P-5 added 4 pages: see P-7).
- P-5: margins of the template file (top and bottom 1.5 in, left and right 1 in, header and footer 0.5 in),
  read from `Template.docx` by the build.
- P-6: closed — `figures_inherited/` attached and used.

**Pending (author):**

| # | item | where |
|---|---|---|
| P-7 | Body now 65 pages (template margins + Figures 6 and 10). Keep, or switch back to the written rule of `Report format.md` (left 1.5 in, others 1 in) for 61 pages — one line in `build_v8.py`. Recommendation: keep the template, since the author chose it; no content cut | built document |
| P-8 | Optional checks before submission: E9 App. A (standardisation with training statistics); benchmark card "Self-GNN – Tang 2021" = E9; N1–N3 abstracts | `CLAIM_AUDIT_v8.md` section 4 |
| P-9 | Optional wording: Ch5 last sentence and 4.6 say "about half of the seizures"; held-out pooled 0.342, final 0.487, application 0.434, per-patient means 0.508–0.577. Keep, or "between a third and a half" | Ch5, 4.6 |

## 5 · Layout

```
F:/Study/Thesis/
  Code/
    docs/STATUS_BOARD.md  docs/writing/CLAIM_AUDIT_v8.md  docs/writing/CITATION_MAP_v8.md
    docs/writing/REPORT_OUTLINE_v8.md  docs/prompts/CC_FIGURES_V8*.md
    src/report_build/ build_v8.py (chat 6: inherited figures, template margins, figure height bound),
                      render_pdf.py, pagemap.py (run in a cloud chat: pandoc 3, LibreOffice, python-lxml, Pillow)
    src/figures_v8/  results/figures_v8_data/
  Reports/v8/
    chapters/   Front_matter_v8.md, Chapter_1_Introduction_v8.md … Chapter_5_Conclusion_v8.md
    appendix/   Appendix_v8.md
    figures/    fig03, fig08, fig09, fig11–fig14, fig16, fig17, app_screens/
    figures_inherited/   Fig01, Fig02, Fig04–Fig07, Fig10 used by the build (others unused)
    tables/     chat-2 tables (source of Ch3 and Appendix tables)
    build/      Thesis_v8_NguyenQuocTrungNhan.docx, figure_sources.txt, reference_map.json
    Template.docx
  Archive/2026-10-13/   v8 chapters and build of chat 5 (superseded)
```

Build layout in a cloud chat (as `build_v8.py` expects): `/home/claude/in/` = unzipped `Reports/v8/`,
`/home/claude/work/{chapters,appendix}` = copies of the chapter files being edited, `/home/claude/repo/` =
clone of the repository (reference sheet).

## 6 · Plan of chats

| # | when | chat | task | output |
|---|---|---|---|---|
| 0–5 | 12–13/10 | thesis chats + Claude Code | inventory → outline → exhibits → chapters v8 → build | done |
| 6 | 13/10 | "Revision before the supervisor" | P-3, `xanh`, `hồng`, cross-review applied; figures complete; template margins; rebuild | done |
| — | 14/10 morning | author | open the build in Word, F9, Zotero citations, read once, send v8 to the supervisor (afternoon); run `en` on the chat-6 chapter files if time allows | v8 sent |
| 7 | 14–15/10 | thesis chat **"Final revision"** | supervisor comments (+ `en` if any) → edit chapter files → rebuild → submission | submitted report |

**Start prompt of chat 7 (copy):**
> Chat 7 — Final revision. Đọc `STATUS_BOARD.md` (rev 7) và `CLAIM_AUDIT_v8.md`. Nhận xét của cô: [dán /
> đính kèm]. Kết quả `en`: [dán hoặc "chưa có"]. P-7: [giữ lề template / đổi về lề quy định]. P-8: [đã kiểm /
> bỏ qua]. P-9: [giữ / sửa]. Đính kèm: `Reports/v8/` (zip: chapters, appendix, figures, figures_inherited,
> tables, Template.docx). Sửa vào file chương rồi build lại bằng `src/report_build/`. Không tạo PDF.

Files chat 7 needs (project): this board, `CLAIM_AUDIT_v8.md`, `CITATION_MAP_v8.md`, all v8 chapter files +
`Appendix_v8.md`, `REPORT_OUTLINE_v8.md`, `Report format.md`, `PROSE_STYLE_SPEC.md`, `Thesis_Reference_Sheet.md`.

## 7 · Where the numbers are

| content | file |
|---|---|
| every number of the final system, decisions | `docs/PERF_PHASE_RECORD.md` (rev R) — authority |
| numbers as written, with sources and computed values | "Notes — not part of the report" at the end of each v8 chapter file |
| what was verified and how; open checks | `docs/writing/CLAIM_AUDIT_v8.md` |
| tables and figures (gated) | `Reports/v8/tables/`, `Reports/v8/figures/`; `src/figures_v8/` |
| per-seizure detection (final, held-out, 4 seeds) | `results/figures_v8_data/perseizure_final.csv` |
| failure analysis of Ch4 4.3 | `results/p3_anatomy/seizures.csv`, `results/p3b_diag/tail.csv` |
| development designs (report form) | Appendix C, Table 22 |
| references: working numbers per chapter → global numbers → DOI | `docs/writing/CITATION_MAP_v8.md`; sheet `docs/Thesis_Reference_Sheet.md` |

## 8 · Numbering of exhibits (v8, fixed)

Figures 1–3 Ch1 · 4–10 Ch2 · 11–15 Ch3 · 16–17 Ch4. Tables 1–3 Ch1 · 4–8 Ch2 · 9–17 Ch3 · 18 Ch4 ·
19–29 Appendix. Equations 1–12 in Ch2. References [1]–[69] in the built document (global, first appearance).

## 9 · Decisions log

- 2026-10-08: record 10.1. 2026-10-10: one reference list; supervisor's papers in Ch1/Ch4.
- 2026-10-12: one-task chats; outline v8 (O1–O6); exhibits; O7 approved without re-run; Ch2, Ch3, App v8.
- 2026-10-13 (author): continue in one chat for continuity; verification standard (section 1.6); A-1 by
  the per-patient table; A-2 confirmed; A-3 provisional; A-4 from code; page excess accepted when needed.
- 2026-10-13 (chat 3–4): code and source audit of Ch2 (14 corrections); Ch1, Ch4, Ch5, front matter v8.
- 2026-10-13 (chat 5): P-1 and P-2 closed; the report is built from the chapter files; one global
  reference list; body 58 pages; Figures 6 and 10 of the repository kept out (earlier system).
- 2026-10-13 (chat 6): P-3 closed with corrections; C4/novelty "no seizure label of the patient under
  review"; P-4 58 pages accepted; P-5 template margins; P-6 closed; Table 9 rows 1–2 = three-readout
  ensemble; literature claims narrowed to the sheet's verified statements; citations by Zotero (author);
  body 65 pages after P-5 (P-7).
