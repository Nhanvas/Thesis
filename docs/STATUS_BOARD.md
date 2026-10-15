# STATUS_BOARD — DEFENSE phase (rev 10, 2026-10-15, end of chat D0)

**Read this first in every chat.** It says what is done, what is open, what the author still has to
give or approve, where every file lives, and what the next chat does. At the end of every chat the board
is rewritten as a whole file (new rev number) and delivered with the project file list.

Defense **05–06/11/2026** (English; 12–15 min of speaking **including the demo**; questions after, length
not yet known). Reviewer: **TS. Ngô Thị Lụa**. Supervisor meetings Thursdays 08:00 (22/10, 29/10).

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
5. Every number on a slide, in the script or in an answer matches the final report **and** its source
   (after D1: `Defense/notes/NUMBERS_LOCK.md`). A mismatch goes to the author.
6. **No script before the slide freeze** (anh Trí: script rewritten after every slide change falls apart).

## 2 · Where things stand (15/10, end of D0)

| track | state | next |
|---|---|---|
| Report | submitted; the author's own revision after chat 8 (style edits, audit file kept by him); Grammarly 1% plagiarism, 11% AI; cô: "overall fairly good — understand every plot and check the results are correct" | none before the committee |
| Report of record | `Reports/final/Thesis_NguyenQuocTrungNhan_BEBEIU2284_Report.docx` (sha256 `fe9c56ea47f2cc45…`), text export `Thesis_Final_Report.md` (pandoc, figures not embedded). 16 figures, Appendices A–E | D1 compares its numbers with the v8 chapters and the record |
| Repository | public; `web_demo/` committed (tag `szscan-frozen-v4.1`, commit `8aabf4d`); chat-8 work (`check_v8.py`, board rev 9) pushed in D0 by the author's command | read only |
| Defense rubric | **not given by the faculty yet**; working rubric = `RUBRIC_MAP.md` (report rubric, 8 criteria, 100 points) | author updates when known |
| Time, committee | 12–15 min including demo (author's recollection); Q&A length unknown; reviewer TS. Ngô Thị Lụa; rest of the committee unknown | author updates when known |
| Slide template | none required (free design) | — |
| Lab seniors' slides | author may obtain some | `Defense/inputs/lab_slides/` |
| Midterm slides | old pipeline; author can send | reuse context, dataset, motivation, style only |

## 3 · Feedback and rules in force

| # | source | rule | where it lands |
|---|---|---|---|
| R1 | anh Trí | slides matter more than the report; finish early (feedback + rehearsal take time) | plan, section 5 |
| R2 | anh Trí | app on slides briefly: technology per layer, which does what; a demo that runs is enough | D1 APP_FACTS → D4 one slide |
| R3 | anh Trí / cô | slide figures only from repository scripts on committed results, or hand-drawn in Figma | D1 FIGURE_PROVENANCE (internal only) |
| R4 | cô 15/10 | understand every plot; check results are correct | D1, D2 |
| R5 | lab notes | answer from the rubric, not only the thesis | D3 |
| R6 | lab notes | novelty and creativity versus previous research | D2, D4 |
| R7 | lab notes | appendix slides after References, page numbers | D3 → D4 |
| R8 | lab notes | not too little, not too much text | D4, D5 |
| R9 | lab notes | slide title = section + main message of the slide | D4 |
| R10 | lab notes | ≤ 20 slides (12–15 min) | D4 |
| R11 | lab notes | check every rubric item has scorable content | D4, D5 |
| R12 | lab notes | look at seniors' slides | D4 (if received) |
| R13 | lab notes | demo prepared carefully: patient ingested beforehand, video fallback | D8, demo checklist |

## 4 · Decisions (D0)

- D0-1 Plan of chats D0–D8 approved (section 5), with three changes the author accepted: Q&A as its own
  chat before the outline; slide freeze before the script; demo fallback video and pre-ingested patient.
- D0-2 The figure-provenance check is **internal only**: not on slides, not committed to the public repository.
- D0-3 `web_demo/` is read from the public repository clone (no zip).
- D0-4 Project knowledge switches from the v8 chapter files to the final report text (list in the D0 reply).
- D0-5 Until the faculty gives a defense form, `RUBRIC_MAP.md` is the working rubric.

## 5 · Plan of chats

| # | target date | task | output (in `F:/Study/Thesis/Defense/`) |
|---|---|---|---|
| D0 | 15/10 | plan, project switch to the defense phase | this board, instructions rev 2026-10-15d |
| **D1** | 16–17/10 | (a) numbers of the final report vs v8 chapters, record and result files; (b) provenance of the 16 report figures: script → input result file → regenerate command, plus which are hand-drawn; (c) app facts from `web_demo/` (stack per layer, what runs where, data flow, label-free guards, timing) | `notes/NUMBERS_LOCK.md`, `notes/FIGURE_PROVENANCE.md`, `notes/APP_FACTS.md` |
| D2a | 17–18/10 | study guide (Vietnamese, deeper than the report): problem, data, graph, GAE, score, drift, budget, CPD, evaluation — every parameter with its reason; every figure explained | `content/STUDY_GUIDE_part1_vi.md` |
| D2b | 18–19/10 | study guide: results, designs not adopted, external, attribution negative, limitations, app, novelty vs prior work | `content/STUDY_GUIDE_part2_vi.md` |
| D3 | 19/10 | committee Q&A mapped to the rubric (reviewer's likely angles first): Vietnamese answer + one English answer line; list of appendix slides | `qa/QA_BANK.md` |
| D4 | 20/10 | slide outline: ≤ 20 main slides, minutes per part, title (section + message), figure source per slide, words per slide, demo slot, appendix slides, rubric coverage check | `outline/SLIDE_OUTLINE.md` |
| — | 20–22/10 | **author builds slides v1** (Figma for hand-drawn parts) | `slides/` |
| D5 | 22/10 | slide review: numbers, titles, figure sources, rubric coverage, text density → send to cô (22/10 meeting) and anh Trí | review list |
| D6 | ≈ 26–27/10 | apply feedback → **slide freeze** | `slides/…_FROZEN` |
| D7 | 28–30/10 | English script per slide, word count per slide fitted to the time; author reads and times it; adjust to the measured time | `script/` |
| D8 | 30/10–04/11 | rehearsal: mock committee in English, timing, demo checklist, fallback video | `demo/DEMO_CHECKLIST.md` |

**Start prompt of chat D1 (copy):**
> Chat D1 — Numbers, figure provenance, app facts. Đọc `STATUS_BOARD.md` (rev 10) và instruction rev
> 2026-10-15d. Clone `github.com/Nhanvas/Thesis`. Làm 3 việc, mỗi việc một file trong `Defense/notes/`:
> (a) `NUMBERS_LOCK.md`: mọi con số trong `Thesis_Final_Report.md`, đối chiếu với các chương v8 trong repo
> history / `PERF_PHASE_RECORD.md` / file kết quả; liệt kê chỗ lệch để tôi duyệt;
> (b) `FIGURE_PROVENANCE.md`: 16 hình của report → script nào, đọc file kết quả nào, lệnh sinh lại, hình nào
> vẽ tay; hình nào không truy được nguồn thì đánh dấu (nội bộ, không public);
> (c) `APP_FACTS.md`: chỉ lấy từ `web_demo/` — công nghệ từng lớp (frontend, backend, pipeline, DB), lớp nào
> làm gì, luồng dữ liệu, các guard label-free, thời gian xử lý. Không đoán.
> Kết thúc: board rev 11, danh sách file project, prompt chat D2a.

## 6 · Layout

```
F:/Study/Thesis/
  Code/                       repository (public): docs/STATUS_BOARD.md, docs/PROJECT_INSTRUCTIONS.md,
                              results/, src/, web_demo/
  Reports/final/              Thesis_NguyenQuocTrungNhan_BEBEIU2284_Report.docx (submitted),
                              Thesis_Final_Report.md (text export)
  Reports/v8/                 report-phase build (superseded by Reports/final/; kept, not cited)
  Defense/                    private, not committed
    inputs/   rubric, committee info, lab_slides/, midterm slides
    notes/    D1: NUMBERS_LOCK.md, FIGURE_PROVENANCE.md, APP_FACTS.md
    content/  D2 study guide (Vietnamese)
    qa/       D3 QA_BANK.md
    outline/  D4 SLIDE_OUTLINE.md
    slides/   author's slide versions
    script/   D7
    demo/     checklist, fallback video
```

## 7 · Where the numbers are

| content | file |
|---|---|
| every number of the final system, decisions | `docs/PERF_PHASE_RECORD.md` (rev R) — authority |
| what the committee read | `Thesis_Final_Report.md` |
| numbers allowed on slides (after D1) | `Defense/notes/NUMBERS_LOCK.md` |
| how each report claim was verified | `docs/writing/CLAIM_AUDIT_v8.md` |
| benchmark entries on Siena | `docs/BENCHMARK_CHECK_szcore_c57da2f.md` |
| demo numbers | `DEMO_FINAL_HANDBACK.md`, `results/t1_demo/`, `results/application_eval_v4/` |

## 8 · Decisions log

- Report phase (2026-10-08 → 13): see board rev 9 in git.
- 2026-10-15: report submitted after the author's own revision; anh Trí's slide feedback; defense phase opened (D0).
