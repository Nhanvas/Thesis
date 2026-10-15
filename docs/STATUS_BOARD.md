# STATUS_BOARD — DEFENSE phase (rev 13, 2026-10-16, end of chat D3)

**Read this first in every chat.** It says what is done, what is open, what the author still has to
give or approve, where every file lives, and what the next chat does. At the end of every chat the board
is rewritten as a whole file (new rev number) and delivered with the project file list.

Defense **05–06/11/2026** (English; 12–15 min of speaking **including the demo**; questions after, length
not yet known). Reviewer: **TS. Ngô Thị Lụa**; chair on the report's approval page: Assoc. Prof. Nguyễn Thị
Hiệp. Supervisor meetings Thursdays 08:00 (22/10, 29/10).

The report phase is closed. Its last board was rev 9 (chat 8, 2026-10-13); its history is in git.

---

## 1 · Chat protocol (binding)

1. One task per chat from section 5, unless the author decides otherwise.
2. Start: read this board → the files named for the task → nothing else unless the task needs it.
3. End: (a) this board rewritten (rev + 1); (b) **one** list for the author (project files add / replace /
   delete, with local paths); (c) the start prompt of the next chat.
4. Defense material lives in `F:/Study/Thesis/Defense/` (private, outside the repository). The repository
   (public) holds only this board and the instructions; cloud chats clone it to read code, results and
   `web_demo/`.
5. Every number on a slide, in the script or in an answer matches the final report **and**
   `Defense/notes/NUMBERS_LOCK.md`. A number not in that file goes to the author.
6. **No script before the slide freeze** (anh Trí: script rewritten after every slide change falls apart).

## 2 · Where things stand (16/10, end of D3)

| track | state | next |
|---|---|---|
| Report | submitted; report of record = `Reports/final/…Report.docx` (sha256 `fe9c56ea47f2cc45…`), text `Thesis_Final_Report.md` | none before the committee; format risks P4 checked by the author in the .docx |
| Numbers (D1a) | `notes/NUMBERS_LOCK.md`; no content mismatch; §3b and §12 added in D2 | author approves N1–N9 (= P8) |
| Figures (D1b) | `notes/FIGURE_PROVENANCE.md` (internal); 3, 6, 10 hand-drawn in Figma, edited with Claude | author writes the exact AI-help sentence (P2) |
| Study guide (D2) | `content/STUDY_GUIDE_part1_vi.md`, `part2_vi.md` | author studies |
| **Q&A bank (D3)** | `qa/QA_BANK.md`: 79 questions under the 8 rubric criteria (C1 7, C2 6, C3 14, C4 6, C5 14, C6 12, C7 9, C8 11); reviewer-first list of 14; 14 traps indexed; every answer ≤ 4 Vietnamese sentences + one English line + numbers tagged NL§1–11 / NL§12 + supporting slide; 21 appendix slides A1–A21 (14 priority 1); rubric coverage check; points P1–P8. Every number token checked against NUMBERS_LOCK (only P5's computed equal-weight totals are outside it, pending approval) | author rehearses the [PB] list; answers P1–P8; D4 uses §0, §10, §11 |
| App (D1c) | `notes/APP_FACTS.md` | D4 one slide + Figma architecture |
| Repository | public; `web_demo/` code identical to tag `szscan-frozen-v4.1` | read only |
| Defense rubric | not given by the faculty yet; working rubric = `RUBRIC_MAP.md` | re-run QA_BANK §11 when known |
| Time, committee | 12–15 min including demo; Q&A length unknown | author adds committee info (P1) |
| Slide template | none required | — |

## 3 · Feedback and rules in force

| # | source | rule | where it lands |
|---|---|---|---|
| R1 | anh Trí | slides matter more than the report; finish early | plan, section 5 |
| R2 | anh Trí | app on slides briefly: technology per layer, which does what; a demo that runs is enough | APP_FACTS §1–2 → D4 one slide |
| R3 | anh Trí / cô | slide figures only from repository scripts on committed results, or hand-drawn in Figma | FIGURE_PROVENANCE (internal) |
| R4 | cô 15/10 | understand every plot; check results are correct | D1, D2 done |
| R5 | lab notes | answer from the rubric, not only the thesis | **D3 done** (QA_BANK by criterion) |
| R6 | lab notes | novelty and contribution versus previous research | QA C1-4, C7-7; D4 `M:Contrib` |
| R7 | lab notes | appendix slides after References, page numbers | **QA_BANK §10 (A1–A21)** → D4 |
| R8 | lab notes | not too little, not too much text | D4, D5 |
| R9 | lab notes | slide title = section + main message | D4 (appendix titles drafted in QA §10) |
| R10 | lab notes | ≤ 20 main slides (12–15 min) | D4 (draft frame in QA §0) |
| R11 | lab notes | every rubric item has scorable content | **QA_BANK §11** → D4 |
| R12 | lab notes | look at seniors' slides | D4 (if received) |
| R13 | lab notes | demo prepared carefully: patient ingested beforehand, video fallback | APP_FACTS §5 → D8 |

## 4 · Decisions

- D0-1 … D0-5 (15/10): plan D0–D8; figure provenance internal only; `web_demo/` read from the public clone;
  project knowledge = final report text; `RUBRIC_MAP.md` = working rubric.
- D1, D2 (16/10): see rev 12 (NUMBERS_LOCK §3b, §12; figure notes for Fig 12, 13).
- **D3 (16/10):** Q&A bank written. Proposed slide frame of 20 main slides (`M:Title … M:Contrib`) is a
  cross-reference for D4, not a decision. Two rubric risks for D4: criterion 4 needs Table 8 (compact) on a
  main slide; criterion 5 needs an objective-by-objective verdict on the conclusion slide.
- **Waiting for the author (QA_BANK §12):**
  - P1 committee research fields / known question habits → `Defense/inputs/committee.md`.
  - P2 exact, truthful sentence on AI help for Figures 3, 6, 10 (answer C8-1).
  - P3 truthful wording on AI use in code and report (answer C8-2), checked against university policy.
  - P4 format risks seen in the text export, to check in the .docx: Mazurek 2026 listed twice; Dani & Liebe
    2026 in text vs 2027 in the list; Σ missing in Eq 9–11 (maybe export only); List of Tables page numbers;
    body Ch1 p. 1 → Ch5 p. 58 vs the 50-page limit. Report stays locked; answers only.
  - P5 add the equal-weight deployment totals (computed from Table 8: 4.0 / 3.4 / 2.6) to NUMBERS_LOCK §12?
  - P6 midterm slides into `Defense/inputs/` (if they showed earlier-protocol numbers, A19 becomes priority 1).
  - P7 framing of "is the GAE needed?" (0.596 feature density vs 0.612 channel latent, not a controlled ablation).
  - P8 = NUMBERS_LOCK N1–N9 (N2 network wording, N3/N4 "4 seeds" label, N5 Figure 1 version).

## 5 · Plan of chats

| # | target date | task | output (in `F:/Study/Thesis/Defense/`) |
|---|---|---|---|
| D0 | 15/10 ✔ | plan, project switch to the defense phase | board rev 10, instructions rev 2026-10-15d |
| D1 | 16/10 ✔ | numbers, figure provenance, app facts | `notes/NUMBERS_LOCK.md`, `notes/FIGURE_PROVENANCE.md`, `notes/APP_FACTS.md` |
| D2a/b | 16/10 ✔ | study guide, two parts | `content/STUDY_GUIDE_part1_vi.md`, `part2_vi.md` |
| D3 | 16/10 ✔ | Q&A bank by rubric criterion, reviewer first; appendix slide list; rubric coverage check | `qa/QA_BANK.md` |
| **D4** | 20/10 | slide outline: ≤ 20 main slides, minutes per part, title (section + message), figure source per slide, words per slide, demo slot, appendix slides with page numbers, rubric coverage check, list of figures for Claude Code to redraw at slide size | `outline/SLIDE_OUTLINE.md` |
| — | 20–22/10 | **author builds slides v1** (Figma for hand-drawn parts) | `slides/` |
| D5 | 22/10 | slide review: numbers vs NUMBERS_LOCK, titles, figure sources, rubric coverage, text density → cô (22/10) and anh Trí | review list |
| D6 | ≈ 26–27/10 | apply feedback → **slide freeze** | `slides/…_FROZEN` |
| D7 | 28–30/10 | English script per slide, timed | `script/` |
| D8 | 30/10–04/11 | rehearsal: mock committee in English (QA_BANK [PB] list first), timing, demo checklist, fallback video | `demo/DEMO_CHECKLIST.md` |

**Start prompt of chat D4 (copy):**
> Chat D4 — Slide outline. Đọc `STATUS_BOARD.md` (rev 13) và instruction rev 2026-10-15d, rồi `QA_BANK.md`
> (§0 khung 20 slide đề xuất, §10 appendix A1–A21, §11 kiểm tra phủ rubric, §12 các điểm P đã được duyệt),
> `NUMBERS_LOCK.md`, `APP_FACTS.md`, `RUBRIC_MAP.md`, `STUDY_GUIDE_part2_vi.md` §13 (đóng góp). Viết
> `Defense/outline/SLIDE_OUTLINE.md`: ≤ 20 slide chính cho 12–15 phút kể cả demo; mỗi slide: tiêu đề tiếng Anh
> (section + main message), số phút, nội dung (số chỉ từ NUMBERS_LOCK mục 1–11, đủ 3 nhãn), hình và nguồn
> (script repo / Figma / ảnh chụp app), số chữ ước tính, tiêu chí rubric chấm được; khe demo (bệnh nhân nạp
> trước, video dự phòng); slide References; appendix A1–A21 có số trang; kiểm tra phủ rubric (Table 8 thu nhỏ
> trên slide chính cho tiêu chí 4; bảng đối chiếu từng mục tiêu cho tiêu chí 5) và mật độ chữ; danh sách hình cần
> Claude Code vẽ lại ở kích thước slide. Kết thúc: board rev 14, danh sách file project, prompt cho bước tác giả
> làm slide / chat D5.

## 6 · Layout

```
F:/Study/Thesis/
  Code/                       repository (public): docs/STATUS_BOARD.md, docs/PROJECT_INSTRUCTIONS.md,
                              results/, src/, web_demo/
  Reports/final/              Thesis_NguyenQuocTrungNhan_BEBEIU2284_Report.docx (submitted),
                              Thesis_Final_Report.md (text export)
  Reports/v8/                 report-phase build (kept, not cited)
  Defense/                    private, not committed
    inputs/   rubric, committee info (P1), lab_slides/, midterm slides (P6)
    notes/    NUMBERS_LOCK.md, FIGURE_PROVENANCE.md, APP_FACTS.md
    content/  D2 study guide (Vietnamese)
    qa/       D3 QA_BANK.md
    outline/  D4 SLIDE_OUTLINE.md
    slides/   author's slide versions; slides/figs/ regenerated or Figma figures
    script/   D7
    demo/     checklist, fallback video
```

## 7 · Where the numbers are

| content | file |
|---|---|
| every number of the final system, decisions | `docs/PERF_PHASE_RECORD.md` (rev R) — authority |
| what the committee read | `Thesis_Final_Report.md` |
| **numbers allowed on slides** | `Defense/notes/NUMBERS_LOCK.md` |
| figure sources (internal) | `Defense/notes/FIGURE_PROVENANCE.md` |
| application facts | `Defense/notes/APP_FACTS.md` |
| answers to committee questions | `Defense/qa/QA_BANK.md` |
| how each report claim was verified | `docs/writing/CLAIM_AUDIT_v8.md` |
| benchmark entries on Siena | `docs/BENCHMARK_CHECK_szcore_c57da2f.md` |

## 8 · Decisions log

- Report phase (2026-10-08 → 13): see board rev 9 in git.
- 2026-10-15: report submitted after the author's own revision; anh Trí's slide feedback; defense phase opened (D0).
- 2026-10-16: D1 done — numbers locked (no content mismatch), figure provenance, app facts from the frozen build.
- 2026-10-16: D2a + D2b done in the same chat — two-part study guide; NUMBERS_LOCK §3b and §12 added.
- 2026-10-16: D3 done — Q&A bank by rubric criterion, 21 appendix slides, coverage check; P1–P8 to the author.
