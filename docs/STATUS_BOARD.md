# STATUS_BOARD — thesis report phase (rev 8, 2026-10-13, end of chat 7)

**Read this first in every chat.** It says what is done, what is open, what the author still has to
approve, where every file lives, and what the next chat does. At the end of every chat the board is
rewritten as a whole file (new rev number) and delivered with the project file list.

Deadlines: send v8 to the supervisor **14/10 (afternoon)** · submission **15/10** · defense **05–06/11**.

---

## 1 · Chat protocol (binding)

1. One task per chat from section 6, unless the author decides otherwise (13/10: chat 7 continued in the
   chat-6 session to keep context, by the author's choice).
2. Start: read this board → the files named for the task → nothing else unless the task needs it.
3. End: (a) this board rewritten (rev + 1); (b) **one** list for the author (project files add / replace /
   delete, with local paths); (c) the start prompt of the next chat. Nothing is left only in the chat.
4. Files go to their place in the layout of section 5. `Agent/inbox/` is a hand-over tray only.
5. Long runs go to Claude Code on the laptop; every prompt states its estimated runtime.
6. **Verification standard (author, 13/10):** every claim is checked against its primary source. Record in
   `docs/writing/CLAIM_AUDIT_v8.md`. Checks the author has already run (commands, PDFs) are trusted and not
   asked again (author, 13/10).
7. **The report is built, not pasted.** The chapter markdown files are the report of record; the Word
   document is produced from them by `src/report_build/build_v8.py`. Edits made only in Word are lost at the
   next build. **Zotero citations are inserted after the last build** (a rebuild removes them).
8. No PDF is produced by the chats; a LibreOffice render is used only to measure pages.

## 2 · Where things stand (13/10, end of chat 7)

| track | state | next |
|---|---|---|
| Performance, external, attribution, demo | closed / finished (unchanged) | none |
| Report text | rewritten in chat 7 from the author's feedback on v8 (10 points): literature review with one study per row (Table 1), Section 1.3 = proposed solution only (no hypotheses, no contributions, no G/H/C codes), Table 18 at one level (Siena benchmark, 11 entries not trained on Siena), old Figure 16 removed, Tables 14 and 16 simplified, Chapter 5 shorter, appendix trimmed (26 tables), units without a space, no "@", N1 removed, P-9 applied | `en` → chat 8 |
| Built document | `Reports/v8/build/Thesis_v8_NguyenQuocTrungNhan.docx` (chat 7): 26 tables, 16 figures (Figure 15 in 2 + 1 layout), 12 equations, 67 references, template margins | rebuilt in chat 8 after `en` |
| Pages (LibreOffice, measured) | **body 62 pages** (Ch1 12, Ch2 24, Ch3 15, Ch4 9, Ch5 2); references 6; appendix 13. Word measured about 2 pages less on the chat-6 build | supervisor question 1–2 (section 6); plan `docs/writing/CUT_PLAN_50p.md` (not applied) |
| Checks (chat 7, script over the build) | captions in sequence, every cross-reference resolves and every exhibit cited, no forbidden number, no G/H/C label, no "@", abstract 298 words; prose numbers of all chapters searched in the committed sources (`CLAIM_AUDIT_v8.md` section 7) | repeat after `en` |
| References | renumbered by first appearance (Table 1 now first in Chapter 1); `CITATION_MAP_v8.md` regenerated (67) | Zotero after the chat-8 build |

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

**Approved earlier:** A1–A7; O1–O8; A-1 to A-4; P-1 to P-6; C4/novelty wording (chat 6).

**13/10, chat 7 (closed):** P-8 closed (E9 App. A confirmed; Tang card = E9, benchmark implementation on
TUH; M3 confirmed; G2 unchanged; N1 removed; N2/N3 abstract level). P-9 applied ("between a third and a
half"). Author feedback 1–10 applied (CLAIM_AUDIT section 7). Figure 15 in 2 + 1. Template margins kept.
Table 10/22 row 2 kept (0.096 and 0.351 are sourced: `results/e4_artifact_rejection/SUMMARY.md`).

**Pending:**

| # | item | who |
|---|---|---|
| P-7 | Page limit: 62 pages (LibreOffice). Ask the supervisor (section 6); apply `CUT_PLAN_50p.md` only if the limit is hard | supervisor → author |
| P-10 | Appendix choices of chat 7 (old Tables 25, 27, 29 → sentences; Table 22 kept whole) — revert any on request | author |

## 5 · Layout

```
F:/Study/Thesis/
  Code/
    docs/STATUS_BOARD.md  docs/writing/CLAIM_AUDIT_v8.md  docs/writing/CITATION_MAP_v8.md
    docs/writing/CUT_PLAN_50p.md (new)  docs/prompts/EN_POLISH_v8.md (new)
    docs/writing/REPORT_OUTLINE_v8.md
    src/report_build/ build_v8.py (chat 7: Figure 15 2 + 1, Figure 16 = budget figure, note styles),
                      render_pdf.py, pagemap.py
  Reports/v8/
    chapters/   Front_matter_v8.md, Chapter_1 … Chapter_5 (chat 7)
    appendix/   Appendix_v8.md (chat 7)
    figures/  figures_inherited/  tables/  Template.docx
    build/      Thesis_v8_NguyenQuocTrungNhan.docx, figure_sources.txt, reference_map.json
  Archive/2026-10-13/chat6_v8/   chapters, appendix and build of chat 6 (superseded)
```

Cloud build layout: `/home/claude/in/` = unzipped `Reports/v8/`, `/home/claude/work/{chapters,appendix}` =
the chapter files, `/home/claude/repo/` = repository clone.

## 6 · Plan of chats

| # | when | who | task | output |
|---|---|---|---|---|
| 0–7 | 12–13/10 | thesis chats | inventory → outline → exhibits → chapters → build → revisions | done |
| — | 13/10 evening | author | place the chat-7 files; run `en` with `docs/prompts/EN_POLISH_v8.md` | `en` files |
| 8 | 13/10 night or 14/10 morning | thesis chat **"en check and final build"** | number check of the `en` files against the chat-7 files, rebuild, checks, page count | final docx for Word |
| — | 14/10 | author | Word: F9, Zotero (67 references, `CITATION_MAP_v8.md`), read once, send to the supervisor with the 5 questions below | v8 sent |
| 9 | 14–15/10 | thesis chat "Final revision" | supervisor comments → chapter files → rebuild → submission | submitted report |

**Five questions for the supervisor (with the 14/10 email):**
1. Does the 50-page limit count Chapters 1–5 only (now about 60 pages in Word) or everything except the
   lists, appendices and references?
2. How strict is the limit — is about 60 pages acceptable for this content?
3. Margins: those of `Template.docx` (top and bottom 1.5 in) or those written in `Report format.md` (left
   1.5 in, others 1 in)?
4. May wide tables use a 10 pt font?
5. Is the 15/10 submission the draft (spiral-bound, with the committee chair's form) or the final copy?

**Start prompt of chat 8 (copy):**
> Chat 8 — en check and final build. Đọc `STATUS_BOARD.md` (rev 8). Đính kèm: 7 file `en` trả về (chương +
> phụ lục) và danh sách câu `en` đã đổi nghĩa (nếu có). [Nếu là chat mới: thêm zip `Reports/v8/`.]
> So số liệu, [n], tham chiếu với bản chat 7, sửa chỗ lệch, build lại bằng `src/report_build/`, đo trang.
> Không tạo PDF.

## 7 · Where the numbers are

| content | file |
|---|---|
| every number of the final system, decisions | `docs/PERF_PHASE_RECORD.md` (rev R) — authority |
| numbers as written, with sources | "Notes — not part of the report" of each chapter file |
| what was verified and how | `docs/writing/CLAIM_AUDIT_v8.md` |
| benchmark entries on Siena | `docs/BENCHMARK_CHECK_szcore_c57da2f.md`; `esl-epfl/szcore` c57da2f |
| tables and figures (gated) | `Reports/v8/tables/`, `Reports/v8/figures/` |
| references: working → global → DOI | `docs/writing/CITATION_MAP_v8.md` |

## 8 · Numbering of exhibits (chat 7)

Figures 1–3 Ch1 · 4–10 Ch2 · 11–15 Ch3 · 16 Ch4. Tables 1–3 Ch1 · 4–8 Ch2 · 9–17 Ch3 · 18 Ch4 · 19–26
Appendix. Equations 1–12 in Ch2. References [1]–[67] (global, first appearance).

## 9 · Decisions log

- 2026-10-08: record 10.1. 2026-10-10: one reference list; supervisor's papers in Ch1/Ch4.
- 2026-10-12: one-task chats; outline v8; exhibits; Ch2, Ch3, App v8.
- 2026-10-13 (chats 3–5): code and source audit; all chapters v8; build from the chapter files; 58 pages.
- 2026-10-13 (chat 6): P-3 corrections; "no seizure label of the patient under review"; template margins.
- 2026-10-13 (chat 7): author feedback 1–10 applied (literature review per study, no G/H/C codes, Section 1.3
  as proposed solution, one-level Siena comparison, Figure 16 removed, simpler Tables 14 and 16, units
  without a space, no "@", shorter Chapter 5, appendix trimmed); N1 removed; P-8 closed; P-9 applied;
  cut plan prepared, not applied; body 62 pages (LibreOffice).
