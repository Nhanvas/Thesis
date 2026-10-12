# STATUS_BOARD — thesis report phase (rev 3, 2026-10-12, end of chat 1+2)

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

## 2 · Where things stand (12/10, 23:00)

| track | state | next |
|---|---|---|
| Performance | **closed** (tag `perf-p3-closed`); numbers in `PERF_PHASE_RECORD.md` rev R | none |
| External validation | done (`results/x1_external/`); **Siena hours resolved** (A4 + PN14, section 4) | wording O3 |
| Channel attribution | closed (A4, A5) | none |
| Demo | **finished** (Claude Code, 12/10): build commit `8aabf4d`, tag `szscan-frozen-v4.1`; tests 15/15; identity gate PASS (chb03); timing 21.68 s/h (chb16, 3 runs); **application run on the 8 test patients: 33/76 (0.434) @ 27.86 FP/day pooled, per-patient mean 0.528 @ 26.92** (`results/application_eval_v4/`); new screenshots in `Reports/v8/figures/app_screens/`; handback `web_demo/report_handback/DEMO_FINAL_HANDBACK.md` | report use: O1 |
| Report | **outline v8 APPROVED** (rev 2; O1–O6 approved 12/10). **Exhibits:** `src/figures_v8/make_v8_exhibits.py` (gated) produced Figures 8, 9, 11, 13, 16, 17, Tables 4, 10–17, Appendix A1, D1–D3 in `Reports/v8/`; Figure 12 and Figure 14 wait for Claude Code (`docs/prompts/CC_FIGURES_V8.md`, plot scripts ready) | Claude Code run; author answers O7–O8; then chat 3 |
| Git | `main` pushed by Claude Code (12/10) | commit of chat 1 files (command in the chat) |

## 3 · Supervisor feedback on the 11/10 draft (12/10) → where the outline answers it

| # | feedback (paraphrased) | v8 answer (outline section) |
|---|---|---|
| F1 | cut too much to fit 50 pages | Ch2 ~15.5 pp, Ch3 ~15 pp; detail to Appendix A–F (outline §2, §4) |
| F2 | results not detailed | Ch3 Tables 9–17, Figures 11–15; answer sentence per section (§3 Ch3) |
| F3 | show methods that did not work | Table 10 (14 designs with numbers, development patients), Appendix C, Discussion 4.2 (mechanisms) |
| F4 | external validation too thin | Section 3.4: Tables 14–15, false-alarm drivers, onset/offset, children → adults, Figure 14 (e) |
| F5 | figures of detected seizures | Figure 14 gallery (5 panels), Figures 12–13 |

## 4 · Approvals

**Approved 12/10 (author):** A1 (base text v5 + parts of the 11/10 draft; critique done first, outline §0),
A2 (appendix A–F, outside the 50), A3 (tried designs as results), A4 (Siena-hours wording, PN14 checked),
A5 (application run as its own row), A6 (page budget), A7 (`Code/bme11/` stays, gitignored).
Also (author, 12/10): Table 3 "Thesis timeline" keeps the weeks of the 11/10 draft.

**Approved 12/10 (author): O1–O6** (outline §9). Chat 2 was done in the same chat as chat 1 (author's choice).

**Pending:**

| # | question | proposal (outline §9) |
|---|---|---|
| O7 | Table 4 hours | print the hours listed in the CHB-MIT summary files (566.43 / 115.82 / 279.39) with a note on the hours scored (562.40 / 111.82 / 279.38): chb12 three files without the 18 derivations; chb11_12–15 and one chb21 file absent from the local dataset copy, none with a seizure |
| O8 | Siena EDF location (Figure 14 e) and timing processor | answered by the check command of chat 2 |

**PN14 finding (12/10, measured by the author on Kaggle).** EDF hours PN14-1 2.1856, PN14-2 2.5458,
PN14-3 11.6653, PN14-4 4.0672 → 20.464 h (computed) = the 20.4622 h scored. PhysioNet's table (23.47 h)
and PN14's seizure list (23.46 h) are both ~3.0 h longer than the files, all in PN14-3 (11.67 h in the
file vs 14.67 h from its registration times). PN14's 4 seizures are among the 47 scored references.

**Application-run finding (12/10).** Same system, label-free normalisation statistics: 33/76 vs 37/76
(seed 42) — one seizure fewer in chb03, chb06, chb15, chb16; false alarms 323 vs 318. "21.0 s/h" in the
handback is total time / total hours (5,862 s / 279.39 h), not a median (median of per-patient rates
20.69, computed).

## 5 · Layout (unchanged since the 12/10 tidy-up)

```
F:/Study/Thesis/
  Code/                         git repo (github.com/Nhanvas/Thesis, main)
    docs/                       documents of record + STATUS_BOARD.md + PROJECT_INSTRUCTIONS.md
      writing/                  report rules + REPORT_OUTLINE_v8.md (REPORT_BLUEPRINT_v5 superseded once O1–O6 approved)
      prompts/                  Claude Code prompts (CC_DEMO_FINISH.md done; CC_FIGURES_V8.md from chat 2)
      prereg/  archive/         pre-registrations; superseded docs (never cite)
    src/  results/  data/       code, committed results (now + application_eval_v4/), inputs
    web_demo/                   SzScan; report_handback/ (DEMO_FINAL_HANDBACK.md, tier2_v4/)
  Reports/
    v8/  chapters/ figures/ tables/ appendix/    ← the only place where v8 is written
    v8/figures/app_screens/     a_import.png, b_analysis.png, c_panel_review.png (1600×1000)
    v8/figures_inherited/       figures of the 11/10 draft (check each before reuse)
    submitted/                  what was sent to the supervisor (dated)
    Sample report/              VBPH, Tri, Tuong, Hien (style samples)
  Agent/inbox/                  hand-over tray only (empty at the end of every chat)
  Archive/2026-10-12/           superseded material; MOVES.csv + UNDO.sh
  Dataset/  Papers/             unchanged
```

## 6 · Plan of chats (one task each)

| # | when | chat / tool | task | output |
|---|---|---|---|---|
| 0 | 12/10 | thesis chat | inventory, tidy-up, board, instructions, demo prompt | done |
| D | 12/10 | Claude Code | `CC_DEMO_FINISH.md` | done (handback, application_eval_v4, screenshots) |
| 1 | 12/10 | thesis chat "Outline v8" | critique + outline | **done**: outline approved (O1–O6) |
| 2 | 12/10 | same chat as 1 | §8.2 checks; gated exhibit script; CC prompt | **done** except Figures 12, 14 (Claude Code) |
| 2b | 12–13/10 night | **Claude Code** (laptop) | `docs/prompts/CC_FIGURES_V8.md` (est. 25–50 min) | `results/figures_v8_data/`, `Reports/v8/figures/fig12_duration.png`, `fig14_gallery.png`, handback |
| 3 | 13/10 | thesis chat **"Write Ch2–Ch3 + Appendix"** | from the approved outline and the chat-2 exhibits | chapter files in `Reports/v8/chapters/`, appendix in `Reports/v8/appendix/` |
| 4 | 13–14/10 | thesis chat **"Write Ch4, Ch1, Ch5, front matter"** | from the outline + Ch2–3 | chapter files |
| 5 | 14/10 morning | thesis chat **"Check and assemble"** + accounts `xanh` (numbers vs files, outline §6), `en` (English), `hồng` (references) | page count measured (cut order outline §2), number check, polish | v8 for the supervisor |
| 6 | 14–15/10 | thesis chat **"Final revision"** | supervisor comments → submission | submitted report |

**Start prompt of chat 3 (copy):**
> Chat 3 — Write Ch2–Ch3 + Appendix. Đọc `STATUS_BOARD.md` (rev 3) và `REPORT_OUTLINE_v8.md` (rev 2), làm task #3.
> Trả lời O7–O8: [điền]. Claude Code figures: [đính kèm `CC_FIGURES_V8_HANDBACK.md`, hoặc "chưa xong"].
> Đính kèm: thư mục `Reports/v8/tables/` (zip) và các hình inherited đã kiểm (1, 2, 4, 5, 7) nếu có thay đổi.

Files chat 3 needs (project): this board, `REPORT_OUTLINE_v8.md`, `Chapter_2_Methodology_v5.md`,
`Chapter_3_Results_v5.md`, `2026-10-11_draft_to_supervisor.md`, `PERF_PHASE_RECORD.md`, `HANDOFF_REPORT.md`,
`AUTHOR_REQUIREMENTS.md`, `PROSE_STYLE_SPEC.md`, `Thesis_Reference_Sheet.md`, `DEMO_FINAL_HANDBACK.md`.
The chat can also clone the public repository `github.com/Nhanvas/Thesis` to read any committed result.

## 7 · Open checks (small, any time)

- O7–O8 (section 4) — one command in the chat 2 reply.
- Inherited Figures 1, 2, 4, 5, 7 (`Reports/v8/figures_inherited/`): author checks they are the draft's final versions;
  diagrams 3, 6, 10: reuse the draft's drawings if they show the final system, else chat 3 redraws them.
- `figures/fig2_7_event_scoring.png` in the repo is regenerated by the scoring-figure script; the v8 copy is
  `Reports/v8/figures/fig09_event_scoring.png`.

## 8 · Where the numbers are (for the outline and the writing chats)

| content | file |
|---|---|
| every number of the final system, held-out/final evaluations, external, decisions | `docs/PERF_PHASE_RECORD.md` (rev R) — authority |
| what the report says, disclosures, translations of internal names | `docs/HANDOFF_REPORT.md` (rev 2; its section 0 is superseded by this board) |
| **numbers chosen for each section, with their source and reading** | `docs/writing/REPORT_OUTLINE_v8.md` §3 and §6 |
| **tables and figures of v8 (gated)** | `Reports/v8/tables/`, `Reports/v8/figures/`; script `src/figures_v8/make_v8_exhibits.py` |
| development designs, one row per gated arm | `results/p2_ledger.csv` (`verdict` = step gate, not the final choice) + record §2, §6.1, §9.7 |
| held-out / final per patient, seeds, onset/offset | `results/e22_test_oneshot/`, `results/e23_test_look7/SUMMARY.md` |
| external per patient, per seed, onset/offset | `results/x1_external/SUMMARY.md` |
| seizure-level failure anatomy (p_need) | `results/p3_anatomy/` (record 9.6) |
| channel attribution | `results/attribution_v8/`, `results/attribution_v7/`, `docs/ATTRIBUTION_SPEC.md` |
| demo identity gate, timing | `results/t1_demo/GATE.md`, `gate.json`, `TIMING.md` |
| **application run on 8 patients** | `results/application_eval_v4/` (SUMMARY, per_subject, pooled, ingest_timing), `web_demo/report_handback/DEMO_FINAL_HANDBACK.md` |
| references and DOIs | `docs/Thesis_Reference_Sheet.md` (groups K–N) |

## 9 · Decisions log

- 2026-10-08: record 10.1 (offline protocol one paragraph; label-free per-patient fitting is part of the
  system; CPD = localizer; held-out and final side by side; pooled + per-patient mean; seed 42 headline).
- 2026-10-10: one shared reference list; supervisor's papers in Ch1 and Ch4; held-out evaluation kept.
- 2026-10-12 (author, chat 0): one-task chats with this board as the hand-over; outline before writing;
  demo finished overnight; v8 restarts from v5.
- 2026-10-12 (author, chat 1): A1–A7 approved; Table 3 keeps the draft's weeks; PN14 durations measured.
- 2026-10-12 (chat 1): outline v8 rev 1 delivered; O1–O6 put to the author.
- 2026-10-12 (author): O1–O6 approved; chat 2 continued in the same chat; N1–N3 cited at abstract level.
- 2026-10-12 (chat 2): outline rev 2; exhibits produced from committed results with gates; CC_FIGURES_V8 prompt; O7–O8 put to the author.
