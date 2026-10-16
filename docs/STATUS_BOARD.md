# STATUS_BOARD — DEFENSE phase (rev 16, 2026-10-16, end of chat D4)

**Read this first in every chat.** It says what is done, what is open, what the author still has to
give or approve, where every file lives, and what the next chat does. At the end of every chat the board
is rewritten as a whole file (new rev number) and delivered with the project file list.

Defense **05–06/11/2026** (English; 12–15 min of speaking **including the demo**; questions after, length
not yet known). Reviewer: **TS. Ngô Thị Lụa**; chair on the report's approval page: Assoc. Prof. Nguyễn Thị
Hiệp. Supervisor meetings Thursdays 08:00 (22/10, 29/10).

Report-phase history: board rev 9 (chat 8, 2026-10-13) in git. **The report is locked when it is submitted to the
faculty on 17/10/2026** (the version of sha256 `fe9c56ea…` was the feedback copy for cô and staff, not the lock).

---

## 1 · Chat protocol (binding)

1. One task per chat from section 5, unless the author decides otherwise.
2. Start: read this board → the files named for the task → nothing else unless the task needs it.
3. End: (a) this board rewritten (rev + 1); (b) **one** list for the author (project files add / replace /
   delete, with local paths); (c) the start prompt of the next chat.
4. Defense material lives in `F:/Study/Thesis/Defense/` (private, outside the repository). The repository
   (public) holds only this board and the instructions; cloud chats clone it to read code, results and
   `web_demo/`. Cloud chats cannot open the author's local folders: a local file a chat needs is attached.
5. Every number on a slide, in the script or in an answer matches the final report **and**
   `Defense/notes/NUMBERS_LOCK.md`. A number not in that file goes to the author.
6. **No script before the slide freeze** (anh Trí: script rewritten after every slide change falls apart).
7. **Questions come from the slides and the talk, not the report** (author, 16/10): every number on a main
   slide has an answer in `qa/QA_BANK.md` or an appendix slide.

## 2 · Where things stand (16/10, end of D4)

| track | state | next |
|---|---|---|
| Report | **faculty-submission draft checked 16/10** (`Thesis_NguyenQuocTrungNhan_BEBEIU22184_Report.docx`, sha256 `9df985819bea39d2…` at check time): every headline number identical, no forbidden number, Σ present in Eq 3, 9–11 (the 15/10 text export lost them), Figure 12 axis already "whole 4 s windows", one Mazurek 2026 entry, Dani & Liebe 2026. Author fixes: R1 (abstract "over four seeds"); R2, R3, R6 declined; R4, R5, R7 no action needed | **author submits to the faculty 17/10**, then re-exports `Thesis_Final_Report.md` (command in chat D4) and replaces the project file |
| Numbers (D1a) | `notes/NUMBERS_LOCK.md`; **N1–N9 approved 16/10** (N5: Figure 1 = `fig1_background_ictal.py` on EDF chb11_82); P5 equal-weight totals in §12 | closed |
| Figures (D1b) | `notes/FIGURE_PROVENANCE.md` (internal) | closed (P2 dropped: answer C8-1 only) |
| Study guide (D2) | `content/STUDY_GUIDE_part1_vi.md`, `part2_vi.md` | author studies |
| Q&A bank (D3) | `qa/QA_BANK.md`: 79 questions, 21 appendix slides; **updated 16/10** (C3-4, C4-1, C8-1, C8-2, C8-3, C8-4, C8-7, C8-10, §12) | author rehearses the [PB] list, C8-2 included |
| **Slide outline (D4)** | `outline/SLIDE_OUTLINE.md`: 20 main slides, 13:20 planned incl. 1:45 demo slot; title, minutes, English slide text, numbers (NL§1–11, three labels), figure source, word estimate, rubric criterion and Q&A link per slide; References p.21–22; appendix index p.23, A# on page 23 + #; text-density check; rubric coverage (Table 8 on slide 16 → criterion 4; objective-by-objective table on slide 19 → criterion 5); 10 figures for Claude Code — **done 16/10**: `slides/figs/*.png`, all gates OK (`slides/figs/HANDBACK.md`) | **author builds slides v1** |
| App (D1c) | `notes/APP_FACTS.md`; on slides: 16 (architecture + Table 8), 17 (demo slot + application run) | demo checklist in D8 |
| Repository | public; `web_demo/` code identical to tag `szscan-frozen-v4.1` | read only |
| Defense rubric | not given by the faculty yet; working rubric = `RUBRIC_MAP.md` | re-run SLIDE_OUTLINE §6 when known |
| Time, committee | 12–15 min including demo; Q&A length unknown | author adds committee info (P1) |
| Slide template | none required; outline §0 proposes 16:9, title `Section \| message`, body ≥ 18 pt | author decides |

## 3 · Feedback and rules in force

| # | source | rule | where it lands |
|---|---|---|---|
| R1 | anh Trí | slides matter more than the report; finish early | plan, section 5 |
| R2 | anh Trí | app on slides briefly: technology per layer, which does what; a demo that runs is enough | **outline slides 16–17** |
| R3 | anh Trí / cô | slide figures only from repository scripts on committed results, or hand-drawn in Figma | **outline §7** (F1–F10, Figma list) |
| R4 | cô 15/10 | understand every plot; check results are correct | D1, D2 done |
| R5 | lab notes | answer from the rubric, not only the thesis | D3 done |
| R6 | lab notes | novelty and contribution versus previous research | **outline slides 3, 20** |
| R7 | lab notes | appendix slides after References, page numbers | **outline §4** (p.23–44) |
| R8 | lab notes | not too little, not too much text | **outline §5** (3 dense slides with cut options) |
| R9 | lab notes | slide title = section + main message | **outline §2** |
| R10 | lab notes | ≤ 20 main slides (12–15 min) | **outline: 20 slides, 13:20** |
| R11 | lab notes | every rubric item has scorable content | **outline §6** (all 8 ✔) |
| R12 | lab notes | look at seniors' slides | D5 (author attaches the PDFs in that chat) |
| R13 | lab notes | demo prepared carefully: patient ingested beforehand, video fallback | outline slide 17 → D8 |

## 4 · Decisions

- D0–D3: see rev 13 (plan; provenance internal; Q&A bank; draft frame).
- **D4 (16/10):**
  - D4-1 Outline of 20 main slides replaces the QA_BANK §0 frame: Eval merged into Data (slide 5), Limits merged
    into Impact (slide 18), App split (16 design + Table 8, 17 demo + application run), Contributions split
    (19 objective by objective, 20 contributions). Mapping table in outline §1.
  - D4-2 Demo slot 1:30 inside slide 17 on **chb03 ingested the evening before**; fallback screen recording of the
    same path; switch to the video if the app does not respond within 10 s.
  - D4-3 Defaults while points are open: N3/N4 label "4 seeds" on slides 12, 19, 20; nothing about network blocking
    on slides (N2); Figure 1 only if Claude Code confirms it matches the .docx (N5), else Figure 14a; the benchmark
    scatter not in the report (`fig16_sens_fa`) is not used.
  - D4-4 A19 (earlier protocol) raised to priority 1: the midterm slides used the earlier pipeline (P6 resolved by
    that fact; the PDF can still be attached in D5).
- **Author, 16/10:** questions come from the slides and the talk (rule 1.7). P4 closed: the 50-page overrun was
  accepted earlier by the author; Dani & Liebe is 2026 (Zotero defaulted to 2027, fixed by hand); the duplicated
  Mazurek entry (two identical list items 2026a/2026b, cited in 2.9.1 and twice in 4.6) is fixed in the final copy.
  Figures 3, 6, 10: drawn by the author in Figma, first for the earlier pipeline, redrawn with Claude's guidance
  (exact sentence = P2, drafted in chat D4, waiting for confirmation).
- **Approved 16/10 (author):** N1–N9 (N5 resolved, chb11_82); P5 (equal weights 4.0 / 3.4 / 2.6, Q&A only);
  P7 (answer C3-4); P2 dropped (figures: answer C8-1 only, nothing on slides or in the report); P3 answer C8-2 —
  the author used an AI assistant as a working tool across the thesis; every decision, experiment run and approval is
  his; the answer says so plainly and leads to what he decided and how every number can be checked.
- **Report (16/10):** the 15/10 copy was for feedback; the faculty copy (17/10) is the lock. Author applied R1; declined
  R2 (Ch5 seed label), R3 (2.9.2 network wording — answer C4-4 covers it), R6 (Bruns name format).
- **Open:** P1 committee research fields / question habits → `Defense/inputs/committee.md` (when known).

## 5 · Plan of chats

| # | target date | task | output (in `F:/Study/Thesis/Defense/`) |
|---|---|---|---|
| D0 | 15/10 ✔ | plan, project switch to the defense phase | board rev 10, instructions rev 2026-10-15d |
| D1 | 16/10 ✔ | numbers, figure provenance, app facts | `notes/NUMBERS_LOCK.md`, `FIGURE_PROVENANCE.md`, `APP_FACTS.md` |
| D2a/b | 16/10 ✔ | study guide, two parts | `content/STUDY_GUIDE_part1_vi.md`, `part2_vi.md` |
| D3 | 16/10 ✔ | Q&A bank, appendix list, rubric coverage | `qa/QA_BANK.md` |
| D4 | 16/10 ✔ | slide outline | `outline/SLIDE_OUTLINE.md` |
| — | **17–21/10** | **author builds slides v1** (outline §8); Claude Code redraws figures (outline §7, est. 15–30 min, not measured) | `slides/Defense_slides_v1.*`, `slides/figs/` |
| D5 | 21/10 | slide review: numbers vs NUMBERS_LOCK (`xanh`), titles, figure sources, rubric coverage, text density, English (`en`), seniors' slides for comparison → cô 22/10 08:00 and anh Trí | review list |
| D6 | ≈ 26–27/10 | apply feedback → **slide freeze** | `slides/…_FROZEN` |
| D7 | 28–30/10 | English script per slide, timed | `script/` |
| D8 | 30/10–04/11 | rehearsal: mock committee in English (QA_BANK [PB] list first), timing, demo checklist, fallback video | `demo/DEMO_CHECKLIST.md` |

**Start prompt of chat D5 (copy):**
> Chat D5 — Slide review. Đọc `STATUS_BOARD.md` (rev 16) và instruction rev 2026-10-15d, rồi `SLIDE_OUTLINE.md`,
> `NUMBERS_LOCK.md`, `QA_BANK.md` (§10, §11), `RUBRIC_MAP.md`. Tôi đính kèm: slide v1 (PDF xuất từ bản dựng)
> và (nếu có) slide của các anh chị khoá trên. Hình đã có nguồn trong `slides/figs/HANDBACK.md` (gate OK 16/10). Việc: (1) đối chiếu từng con
> số trên slide với NUMBERS_LOCK và 3 nhãn; (2) tiêu đề = section + thông điệp; (3) nguồn mỗi hình đúng outline §7;
> (4) phủ rubric và mật độ chữ (outline §5, §6); (5) tiếng Anh trên slide; (6) so sánh nhanh với slide khoá trên.
> Kết quả: một danh sách sửa theo thứ tự ưu tiên để mang tới cô 22/10. Kết thúc: board rev 17, danh sách file project,
> prompt chat D6.

## 6 · Which file for what (defense material, `F:/Study/Thesis/Defense/`)

| File | Use it to | When |
|---|---|---|
| `outline/SLIDE_OUTLINE.md` | build every slide: title, English text, numbers, figure, appendix pages | **now** (slides v1) |
| `notes/NUMBERS_LOCK.md` | check any number before it goes on a slide or into an answer | every slide, every answer |
| `content/STUDY_GUIDE_part1_vi.md` | understand data, preprocessing, graphs, GAE, score, detector, CPD, evaluation (Ch1–2) | study, before rehearsal |
| `content/STUDY_GUIDE_part2_vi.md` | understand every result, figure, failure, comparison, contribution (Ch3–5) | study, before rehearsal |
| `qa/QA_BANK.md` | rehearse answers: §1 the 14 reviewer questions first, §13 the traps | daily from now to 05/11 |
| `notes/APP_FACTS.md` | what each layer of the app is and does; demo facts | slides 16–17, demo prep (D8) |
| `notes/FIGURE_PROVENANCE.md` | internal proof of where every figure came from | only if asked; never on slides |
| `slides/figs/*.png` + `HANDBACK.md` | slide-size figures (F1–F10) and their sources | now (slides v1) |
| `docs/STATUS_BOARD.md` (repo) | state, plan, next prompt | start of every chat |

## 7 · Layout

```
F:/Study/Thesis/
  Code/                       repository (public): docs/STATUS_BOARD.md, docs/PROJECT_INSTRUCTIONS.md,
                              results/, src/, web_demo/
  Reports/final/              Thesis_NguyenQuocTrungNhan_BEBEIU2284_Report.docx (submitted),
                              Thesis_Final_Report.md (text export)
  Reports/v8/                 report-phase build (kept, not cited); figures/app_screens/ = final-build screenshots
  Defense/                    private, not committed
    inputs/   rubric, committee info (P1), lab_slides/, midterm slides
    notes/    NUMBERS_LOCK.md, FIGURE_PROVENANCE.md, APP_FACTS.md
    content/  D2 study guide (Vietnamese)
    qa/       D3 QA_BANK.md
    outline/  D4 SLIDE_OUTLINE.md
    slides/   author's slide versions; slides/figs/ regenerated figures + make_slide_figs.py + HANDBACK.md
    script/   D7
    demo/     checklist, fallback video
```

## 8 · Where the numbers are

| content | file |
|---|---|
| every number of the final system, decisions | `docs/PERF_PHASE_RECORD.md` (rev R) — authority |
| what the committee read | `Thesis_Final_Report.md` |
| **numbers allowed on slides** | `Defense/notes/NUMBERS_LOCK.md` |
| **slide by slide: text, numbers, figures** | `Defense/outline/SLIDE_OUTLINE.md` |
| figure sources (internal) | `Defense/notes/FIGURE_PROVENANCE.md` |
| application facts | `Defense/notes/APP_FACTS.md` |
| answers to committee questions | `Defense/qa/QA_BANK.md` |
| how each report claim was verified | `docs/writing/CLAIM_AUDIT_v8.md` |
| benchmark entries on Siena | `docs/BENCHMARK_CHECK_szcore_c57da2f.md` |

## 9 · Decisions log

- Report phase (2026-10-08 → 13): see board rev 9 in git.
- 2026-10-15: report submitted after the author's own revision; anh Trí's slide feedback; defense phase opened (D0).
- 2026-10-16: D1 done — numbers locked (no content mismatch), figure provenance, app facts from the frozen build.
- 2026-10-16: D2a + D2b done — two-part study guide; NUMBERS_LOCK §3b and §12 added.
- 2026-10-16: D3 done — Q&A bank by rubric criterion, 21 appendix slides, coverage check; P1–P8 to the author.
- 2026-10-16: D4 done — slide outline (20 main slides, 13:20 incl. demo), figure redraw prompt; P4 and P6 closed;
  questions come from the slides (author).
- 2026-10-16: approvals recorded (rev 15–16) — N1–N9, P5, P7; P2 dropped; P3 answer written; reference list fixed;
  slide figures done; faculty-submission draft checked (numbers identical); report locks at the faculty submission 17/10.
