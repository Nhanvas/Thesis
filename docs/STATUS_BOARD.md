# STATUS_BOARD — thesis report phase (rev 4, 2026-10-12, end of chat 3)

**Read this first in every chat.** It says what is done, what is open, what the author still has to
approve, where every file lives, and what the next chat does. At the end of every chat the board is
rewritten as a whole file (new rev number) and delivered with the project file list.

Deadlines: send v8 to the supervisor **14/10 (afternoon)** · submission **15/10** · defense **05–06/11**.

---

## 1 · Chat protocol (binding)

1. One chat = one task from section 6. Don't take on work from another task, even if it looks quick.
2. Start: read this board → the files named for the task → nothing else unless the task needs it.
3. End: (a) this board rewritten (rev + 1): state, decisions, new paths; (b) **one** list for the author
   (project files add / replace / delete, with local paths); (c) the start prompt of the next chat
   (section 6). Nothing is left only in the chat.
4. Files go to their place in the layout of section 5. `Agent/inbox/` is only a hand-over tray and is
   emptied at the end of every chat.
5. Long runs go to Claude Code on the laptop (prompt files in `Code/docs/prompts/`); every prompt states
   its estimated runtime.

## 2 · Where things stand (12/10, 23:30)

| track | state | next |
|---|---|---|
| Performance | **closed** (tag `perf-p3-closed`); numbers in `PERF_PHASE_RECORD.md` rev R | none |
| External validation | done; Siena hours resolved (A4 + PN14); per-patient table in Appendix A (Table 20) | none |
| Channel attribution | closed (A4, A5) | none |
| Demo | **finished** (`szscan-frozen-v4.1`, commit `8aabf4d`); application run 33/76 @ 27.86 (pooled), per-patient mean 0.528 @ 26.92 | none |
| Report | outline v8 approved (O1–O6); **O7 approved, O8 answered (chat 3)**. **Chapter 2, Chapter 3 and the Appendix v8 written** (`Reports/v8/chapters/`, `Reports/v8/appendix/`). Two FILL-CC markers in Ch3 (3.3.3, 3.3.5) wait for the Claude Code handback | Claude Code `CC_FIGURES_V8.md`; chat 4 |
| Figures | done: 8, 9, 11, 13, 16, 17, 15 (screens); inherited checked by the author: 1, 2, 4, 5, 7; **6 and 10 = the 11/10 draft drawings, checked in chat 3: both show the final system → reuse as is**; **3 (research framework) does not show design → held-out → final → external: redraw in chat 4** (Ch1); 12 and 14 wait for Claude Code | CC run tonight |
| Git | `main` pushed (chat 2 files); board rev 4 to commit (command in the chat-3 reply) | — |

## 3 · Supervisor feedback on the 11/10 draft (12/10) → where v8 answers it

| # | feedback (paraphrased) | v8 answer | state |
|---|---|---|---|
| F1 | cut too much to fit 50 pages | Ch2 and Ch3 written in full; detail moved to Appendix A–F | Ch2–3 written |
| F2 | results not detailed | Ch3: Tables 9–17, Figures 11–15, answer sentence per section | written |
| F3 | show methods that did not work | Table 10 (15 designs) + Appendix C Table 22 (all 40 gated decisions) + Discussion 4.2 (chat 4) | Ch3 + App done |
| F4 | external validation too thin | Section 3.4: Tables 14–15, false-alarm drivers, onset/offset, children → adults; Fig 14 (e) if PN10 runs | written |
| F5 | figures of detected seizures | Figure 14 gallery (CC), Figures 12–13 | waits for CC |

## 4 · Approvals

**Approved 12/10 (author):** A1–A7; Table 3 keeps the draft's weeks; O1–O6.

**Approved / answered in chat 3 (12/10):**
- **O7 approved.** Table 4 prints the hours listed in the CHB-MIT summary files (566.43 / 115.82 / 279.39)
  with a note on the hours scored (562.40 / 111.82 / 279.38). The five files absent from the local copy are
  **chb11_12–15 and chb21_11** (author's check), all seizure-free, all in development patients (5.0 of
  682.25 listed development hours, 0.7 %, computed). **Not re-downloaded, not re-run** (chat-3 reasoning,
  author's condition "if not feasible, approve O7"): test, external and application numbers are
  unaffected; adding chb21_11 changes the autoencoder's training set → retraining → every number changes,
  and re-scoring the test patients would be a further look at a used-up test set (forbidden); effect on
  development numbers not measured, stated once in Appendix A.
- **O8 answered.** Timing processor: Intel Core i5-8250U @ 1.60 GHz (author). Siena EDF files: not on the
  laptop (Kaggle only). Chat 3 proposed downloading **only PN10** (6 EDF + seizure list, ≈ 2.96 GB from the
  PhysioNet listing; download time not measured) into `F:/Study/Thesis/Dataset/siena/PN10/` for panel (e);
  if the download fails or takes > 1 h, panel (e) is skipped (Ch3 text works both ways).

**Pending (author, small):**

| # | question | proposal |
|---|---|---|
| A-1 | Siena sexes and ages: v5 wrote "9 men aged 36–71 and 5 women aged 20–58" (originating paper [K2]); PhysioNet's `subject_info.csv` (read 12/10) lists 8 men (25–71) and 6 women (20–58) for the same 14 patients (PN10 male, 25) | v8 Ch2 writes only "14 adult patients aged 20 to 71 years" (true under both); approve or give the wording |
| A-2 | Laptop memory "16 GB" in Ch3 3.6 comes from the project instructions §8 (Dell Latitude 3590) | confirm it is the machine of `TIMING.md` |
| A-3 | Appendix E protocol wording ("fixed bipolar display"; "approved before any comparison") taken from the draft and instructions | confirm or edit |
| A-4 | Appendix F Table 28 column "Loading and filtering" = `phase_a_s` of `TIMING.md` | confirm the stage name |

## 5 · Layout (unchanged since the 12/10 tidy-up)

```
F:/Study/Thesis/
  Code/                         git repo (github.com/Nhanvas/Thesis, main)
    docs/                       documents of record + STATUS_BOARD.md + PROJECT_INSTRUCTIONS.md
      writing/                  report rules + REPORT_OUTLINE_v8.md (rev 2, approved)
      prompts/                  CC_FIGURES_V8.md (to run); CC_DEMO_FINISH.md done
    src/  results/  data/       code, committed results, inputs
    web_demo/                   SzScan; report_handback/
  Reports/
    v8/chapters/                Chapter_2_Methodology_v8.md, Chapter_3_Results_v8.md   ← chat 3
    v8/appendix/                Appendix_v8.md                                         ← chat 3
    v8/figures/ tables/         exhibits (chat 2) + app_screens/
    v8/figures_inherited/       figures of the 11/10 draft (1, 2, 4, 5, 6, 7, 10 reused; 3 redrawn in chat 4)
    submitted/                  what was sent to the supervisor (dated)
  Agent/inbox/                  hand-over tray only (empty at the end of every chat)
  Archive/2026-10-12/           superseded material
  Dataset/                      + siena/PN10/ if downloaded for Figure 14 (e)
```

## 6 · Plan of chats (one task each)

| # | when | chat / tool | task | output |
|---|---|---|---|---|
| 0–2 | 12/10 | thesis chats | inventory, outline, exhibits | done |
| D | 12/10 | Claude Code | demo finish | done |
| 2b | 12–13/10 night | **Claude Code** (laptop) | `docs/prompts/CC_FIGURES_V8.md` with `<SIENA_DIR>` = `F:/Study/Thesis/Dataset/siena` if PN10 was downloaded (est. 25–50 min, not measured) | `results/figures_v8_data/`, `fig12_duration.png`, `fig14_gallery.png`, `CC_FIGURES_V8_HANDBACK.md` |
| 3 | 12/10 | thesis chat "Write Ch2–Ch3 + Appendix" | **done** | `Reports/v8/chapters/Chapter_2_Methodology_v8.md`, `Chapter_3_Results_v8.md`, `Reports/v8/appendix/Appendix_v8.md` |
| 4 | 13/10 | thesis chat **"Write Ch4, Ch1, Ch5, front matter"** | from the outline (§3 Ch1, Ch4, Ch5, front matter) + Ch2–3 v8 + App v8; Figure 3 redraw; Table 1 (gap table with G-codes and numbers), Table 2, Table 18; Discussion 4.2 must agree with Table 10 / Table 22 | chapter files + front matter in `Reports/v8/chapters/` |
| 5 | 14/10 morning | thesis chat **"Check and assemble"** + accounts `xanh`, `en`, `hồng` | fill FILL-CC markers from the CC handback; build the document and measure pages (cut order outline §2; see note below); number check vs outline §6 and the chapter notes; polish | v8 for the supervisor |
| 6 | 14–15/10 | thesis chat **"Final revision"** | supervisor comments → submission | submitted report |

**Length note (chat 3, measured by script on the markdown; tables, equations, headings excluded):** Ch2
about 4,300 prose words (v5 3,898 by its own count; outline target 2,900 was below v5 for the same content),
Ch3 about 2,600 (target 2,300), Appendix about 1,050 + 11 tables. Ch2 may exceed its 15.5-page budget by
2–3 pages. If the built body exceeds 50 pages, apply the outline §2 cut order first, then in Ch2: shorten
2.1.3 first paragraph (filter details are in Appendix B), the training paragraph of 2.4 (also in
Appendix B), and the Goal-1 qualifier of 2.2 to one sentence.

**Start prompt of chat 4 (copy):**
> Chat 4 — Write Ch4, Ch1, Ch5, front matter. Đọc `STATUS_BOARD.md` (rev 4) và `REPORT_OUTLINE_v8.md`
> (rev 2), làm task #4. Trả lời A-1 đến A-4: [điền]. Claude Code figures: [đính kèm
> `CC_FIGURES_V8_HANDBACK.md`, hoặc "chưa xong"]. Đính kèm: `Reports/v8/chapters/` + `Reports/v8/appendix/`
> (zip) nếu có chỉnh sửa so với bản chat 3.

Files chat 4 needs (project): this board, `REPORT_OUTLINE_v8.md`, `Chapter_1_Introduction_v5.md`,
`Chapter_4_Discussion_v5.md`, `Chapter_5_Conclusion_v5.md`, `Front_matter_v5.md`,
`Chapter_2_Methodology_v8.md`, `Chapter_3_Results_v8.md`, `Appendix_v8.md`,
`2026-10-11_draft_to_supervisor.md`, `PERF_PHASE_RECORD.md`, `HANDOFF_REPORT.md`, `AUTHOR_REQUIREMENTS.md`,
`PROSE_STYLE_SPEC.md`, `Thesis_Reference_Sheet.md`, `Thesis Registration Form.md`. The chat can clone
`github.com/Nhanvas/Thesis` (read only) for committed results.

## 7 · Open checks (small, any time)

- A-1 to A-4 (section 4).
- Ch3 FILL-CC markers: 3.3.3 (detection share by duration bin) and 3.3.5 (one sentence per panel; delete
  panel (e) if skipped). Fill only from `CC_FIGURES_V8_HANDBACK.md`.
- Figure 3 redraw (chat 4): add "design on the development patients → held-out evaluation → final system
  (test-informed) → external validation → application run" to the framework.

## 8 · Where the numbers are (for the writing chats)

| content | file |
|---|---|
| every number of the final system, decisions | `docs/PERF_PHASE_RECORD.md` (rev R) — authority |
| what the report says, disclosures, translations of internal names | `docs/HANDOFF_REPORT.md` (rev 2) |
| numbers chosen for each section, with source | `docs/writing/REPORT_OUTLINE_v8.md` §3 and §6 |
| **numbers as written in Ch2–Ch3 and the Appendix, with sources and computed values** | "Notes — not part of the report" at the end of each v8 chapter file |
| tables and figures of v8 (gated) | `Reports/v8/tables/`, `Reports/v8/figures/`; `src/figures_v8/make_v8_exhibits.py` |
| every gated design decision (report form) | Appendix C, Table 22 (40 rows; from record §2, §6.1, §9.7, §9.7b and `p2_ledger.csv`) |
| Siena hours per patient (EDF vs PhysioNet table) | Appendix A, Table 20 (PhysioNet `subject_info.csv` read 12/10, sum 128.4 h) |
| held-out / final per patient, seeds, onset/offset | `results/e22_test_oneshot/`, `results/e23_test_look7/SUMMARY.md` |
| external per patient, per seed, onset/offset | `results/x1_external/SUMMARY.md` |
| channel attribution per patient / seizure | `results/attribution_v8/attribution_summary.csv`, `attribution_perseizure.csv` |
| application run | `results/application_eval_v4/`, `DEMO_FINAL_HANDBACK.md` |
| references and DOIs | `docs/Thesis_Reference_Sheet.md` (groups K–N) |

## 9 · Numbering of exhibits (v8, fixed)

Figures 1–3 Ch1 · 4–10 Ch2 · 11–15 Ch3 · 16–17 Ch4. Tables 1–3 Ch1 · 4–8 Ch2 · 9–17 Ch3 · 18 Ch4 ·
**19–29 Appendix** (19 CHB-MIT per case, 20 Siena per patient, 21 settings, 22 development designs, 23–25
per-seed results, 26 channel ranking per patient, 27 identity check, 28 timing chb16, 29 application run
per patient). Equations 1–12 in Ch2.

## 10 · Decisions log

- 2026-10-08: record 10.1 (offline protocol one paragraph; label-free per-patient fitting part of the
  system; CPD = localizer; held-out and final side by side; pooled + per-patient mean; seed 42 headline).
- 2026-10-10: one shared reference list; supervisor's papers in Ch1 and Ch4; held-out evaluation kept.
- 2026-10-12 (author, chat 0): one-task chats with this board as the hand-over; outline before writing.
- 2026-10-12 (author, chat 1): A1–A7; Table 3 keeps the draft's weeks; PN14 durations measured.
- 2026-10-12 (author): O1–O6 approved; chat 2 continued in the same chat; N1–N3 cited at abstract level.
- 2026-10-12 (chat 2): outline rev 2; exhibits from committed results with gates; CC_FIGURES_V8 prompt.
- 2026-10-12 (chat 3): O7 approved without re-download or re-run (reasons in section 4); O8 answered;
  Ch2, Ch3, Appendix v8 written; Figures 6 and 10 reused; Figure 3 to redraw; Siena ages written as a range
  pending A-1; appendix tables numbered 19–29.
