# STATUS_BOARD — DEFENSE phase (rev 11, 2026-10-16, end of chat D1)

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
5. Every number on a slide, in the script or in an answer matches the final report **and**
   `Defense/notes/NUMBERS_LOCK.md` (written in D1). A number not in that file goes to the author.
6. **No script before the slide freeze** (anh Trí: script rewritten after every slide change falls apart).

## 2 · Where things stand (16/10, end of D1)

| track | state | next |
|---|---|---|
| Report | submitted; report of record = `Reports/final/…Report.docx` (sha256 `fe9c56ea47f2cc45…`), text `Thesis_Final_Report.md` | none before the committee |
| **Numbers (D1a)** | `notes/NUMBERS_LOCK.md` written: every number of the report traced to the record, a committed result file, a computation or an external source. `make_v8_exhibits.py` re-run on a clean clone: all gates pass; Tables 11–17, 19, 22–24 identical. **No content mismatch.** 9 points N1–N9 for approval (rounding, labels, one wording) | author approves N1–N9 |
| **Figures (D1b)** | `notes/FIGURE_PROVENANCE.md` (internal): 8, 9, 11–14, 16 regenerated in the cloud from committed results; 1, 2, 5, 7 from repository scripts on EEG (laptop); 15 real screenshots; 4 hand-drawn (draw.io); **3, 6, 10 have no source in the repository** | author: who drew 3, 6, 10; run the docx-hash command (FIGURE_PROVENANCE §3) |
| **App (D1c)** | `notes/APP_FACTS.md`: stack per layer, data flow, the 15 label-free/identity tests, timing, demo-day notes — from `web_demo/` at the frozen build only | D4 uses it for one slide + Figma architecture |
| Repository | public; HEAD `9765c4d`; `web_demo/` code identical to tag `szscan-frozen-v4.1` (only `report_handback/` and docs changed after it) | read only |
| Defense rubric | not given by the faculty yet; working rubric = `RUBRIC_MAP.md` | author updates when known |
| Time, committee | 12–15 min including demo; Q&A length unknown; reviewer TS. Ngô Thị Lụa | author updates when known |
| Slide template | none required | — |

## 3 · Feedback and rules in force

| # | source | rule | where it lands |
|---|---|---|---|
| R1 | anh Trí | slides matter more than the report; finish early | plan, section 5 |
| R2 | anh Trí | app on slides briefly: technology per layer, which does what; a demo that runs is enough | APP_FACTS §1–2 → D4 one slide |
| R3 | anh Trí / cô | slide figures only from repository scripts on committed results, or hand-drawn in Figma | FIGURE_PROVENANCE (internal); 3, 6, 10 → Figma |
| R4 | cô 15/10 | understand every plot; check results are correct | D1 done (numbers); D2 explains every plot |
| R5 | lab notes | answer from the rubric, not only the thesis | D3 |
| R6 | lab notes | novelty and contribution versus previous research | D2b, D4 |
| R7 | lab notes | appendix slides after References, page numbers | D3 → D4 |
| R8 | lab notes | not too little, not too much text | D4, D5 |
| R9 | lab notes | slide title = section + main message | D4 |
| R10 | lab notes | ≤ 20 main slides (12–15 min) | D4 |
| R11 | lab notes | every rubric item has scorable content | D4, D5 |
| R12 | lab notes | look at seniors' slides | D4 (if received) |
| R13 | lab notes | demo prepared carefully: patient ingested beforehand, video fallback | APP_FACTS §5 → D8 |

## 4 · Decisions

- D0-1 … D0-5 (15/10): plan D0–D8; figure provenance internal only; `web_demo/` read from the public clone;
  project knowledge = final report text; `RUBRIC_MAP.md` = working rubric.
- **D1 (16/10), proposed, waiting for the author:**
  - N1–N9 of NUMBERS_LOCK §0 (most important: N2 network wording; N3/N4 "median over 4 seeds" label on
    onset/offset; N5 which Figure 1 is in the docx).
  - Figures 3, 6, 10 → redraw in Figma for slides (whoever drew them), from HANDOFF §1 and APP_FACTS §2.
  - Result figures on slides → regenerated by Claude Code at slide size from the same scripts (D4/D5).

## 5 · Plan of chats

| # | target date | task | output (in `F:/Study/Thesis/Defense/`) |
|---|---|---|---|
| D0 | 15/10 | plan, project switch to the defense phase | board rev 10, instructions rev 2026-10-15d |
| D1 | 16/10 ✔ | numbers, figure provenance, app facts | `notes/NUMBERS_LOCK.md`, `notes/FIGURE_PROVENANCE.md`, `notes/APP_FACTS.md` |
| **D2a** | 17–18/10 | study guide (Vietnamese, deeper than the report): problem, data, graph, GAE, score, drift, budget, CPD, evaluation — every parameter with its reason; every figure of Chapters 1–2 explained (how to read it, what it shows, what it does not show) | `content/STUDY_GUIDE_part1_vi.md` |
| D2b | 18–19/10 | study guide: results, designs not adopted, external, channel-explanation negative, limitations, app, novelty vs prior work; every figure of Chapters 3–4 explained | `content/STUDY_GUIDE_part2_vi.md` |
| D3 | 19/10 | committee Q&A mapped to the rubric (reviewer's likely angles first): Vietnamese answer + one English answer line; list of appendix slides | `qa/QA_BANK.md` |
| D4 | 20/10 | slide outline: ≤ 20 main slides, minutes per part, title (section + message), figure source per slide, words per slide, demo slot, appendix slides, rubric coverage check | `outline/SLIDE_OUTLINE.md` |
| — | 20–22/10 | **author builds slides v1** (Figma for hand-drawn parts) | `slides/` |
| D5 | 22/10 | slide review: numbers vs NUMBERS_LOCK, titles, figure sources, rubric coverage, text density → cô (22/10) and anh Trí | review list |
| D6 | ≈ 26–27/10 | apply feedback → **slide freeze** | `slides/…_FROZEN` |
| D7 | 28–30/10 | English script per slide, timed | `script/` |
| D8 | 30/10–04/11 | rehearsal: mock committee in English, timing, demo checklist, fallback video | `demo/DEMO_CHECKLIST.md` |

**Start prompt of chat D2a (copy):**
> Chat D2a — Study guide part 1 (Chương 1–2). Đọc `STATUS_BOARD.md` (rev 11) và instruction rev 2026-10-15d,
> rồi `Thesis_Final_Report.md` Chương 1–2 + Appendix B, `NUMBERS_LOCK.md` (mục 2–4), `VERIFIED_CORRECTIONS.md`,
> `HANDOFF_REPORT.md` §1. Clone `github.com/Nhanvas/Thesis` khi cần mở code (`src/dataprep/*`,
> `c1b_build_trainset.py`, `retrain/train_gae_v2.py`, `p2_scalars.py`, `e16_recording_baseline.py`,
> `e17b_latent_family.py`, `p3_levers.py`, `e18_cpd_localizer.py`, `szcore_eval.py`). Viết
> `Defense/content/STUDY_GUIDE_part1_vi.md` bằng tiếng Việt, thuật ngữ tiếng Anh bên cạnh: bài toán và vì sao
> là triage hậu kiểm; dữ liệu và chia bệnh nhân; tiền xử lý; đồ thị (CAR, wPLI, AEC, top-20 %); node features
> (3 khối, vì sao thêm 7 feature biên độ); GAE (từng lớp, loss, vì sao 3,964 tham số); điểm (Mahalanobis,
> Ledoit–Wolf, robust z, 4 thành viên, drift ±15 phút, percentile); detector + ngân sách cảnh báo (k, sàn, trần);
> CPD (vì sao kernel, vì sao 2 change point, vì sao là localizer chứ không là detector); SzCORE (tolerance, merge,
> pooled vs per-patient mean, FP/day). Mỗi tham số: giá trị — lý do — bằng chứng (số trong NUMBERS_LOCK).
> Mỗi hình 1–10: đọc thế nào, cho thấy gì, KHÔNG cho thấy gì, câu hỏi hội đồng có thể hỏi. Mỗi mục kết thúc
> bằng 3 câu "nếu bị hỏi…" (một dòng trả lời tiếng Anh). Không số nào ngoài NUMBERS_LOCK.
> Kết thúc: board rev 12, danh sách file project, prompt chat D2b.

## 6 · Layout

```
F:/Study/Thesis/
  Code/                       repository (public): docs/STATUS_BOARD.md, docs/PROJECT_INSTRUCTIONS.md,
                              results/, src/, web_demo/
  Reports/final/              Thesis_NguyenQuocTrungNhan_BEBEIU2284_Report.docx (submitted),
                              Thesis_Final_Report.md (text export)
  Reports/v8/                 report-phase build (figures, figures_inherited, app_screens; kept, not cited)
  Defense/                    private, not committed
    inputs/   rubric, committee info, lab_slides/, midterm slides
    notes/    NUMBERS_LOCK.md, FIGURE_PROVENANCE.md, APP_FACTS.md, docx_media_hashes.txt (after the command)
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
| how each report claim was verified | `docs/writing/CLAIM_AUDIT_v8.md` |
| benchmark entries on Siena | `docs/BENCHMARK_CHECK_szcore_c57da2f.md` |

## 8 · Decisions log

- Report phase (2026-10-08 → 13): see board rev 9 in git.
- 2026-10-15: report submitted after the author's own revision; anh Trí's slide feedback; defense phase opened (D0).
- 2026-10-16: D1 done — numbers locked (no content mismatch), figure provenance (3 diagrams without a repository
  source), app facts from the frozen build.
