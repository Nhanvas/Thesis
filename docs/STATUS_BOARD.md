# STATUS_BOARD — thesis report phase (rev 2, 2026-10-12, end of chat 1)

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

## 2 · Where things stand (12/10, 21:30)

| track | state | next |
|---|---|---|
| Performance | **closed** (tag `perf-p3-closed`); numbers in `PERF_PHASE_RECORD.md` rev R | none |
| External validation | done (`results/x1_external/`); **Siena hours resolved** (A4 + PN14, section 4) | wording O3 |
| Channel attribution | closed (A4, A5) | none |
| Demo | **finished** (Claude Code, 12/10): build commit `8aabf4d`, tag `szscan-frozen-v4.1`; tests 15/15; identity gate PASS (chb03); timing 21.68 s/h (chb16, 3 runs); **application run on the 8 test patients: 33/76 (0.434) @ 27.86 FP/day pooled, per-patient mean 0.528 @ 26.92** (`results/application_eval_v4/`); new screenshots in `Reports/v8/figures/app_screens/`; handback `web_demo/report_handback/DEMO_FINAL_HANDBACK.md` | report use: O1 |
| Report | **outline v8 delivered** (`docs/writing/REPORT_OUTLINE_v8.md`, rev 1: critique of v5, chain G→C→result, chapter outline with numbers and sources, appendix A–F, exhibit and number registers, open checks) | **author approves O1–O6** → chat 2 |
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

**Pending (answer at the start of chat 2, or by reply in chat 1):**

| # | question | proposal (outline §9) |
|---|---|---|
| O1 (A8) | use of the application run | Results Table 17 beside the final system per patient; one clause in the Abstract; Limitations replaces "effect not measured" with the measured −4 seizures / +5 false alarms; timing = 21.68 s/h (controlled) + 5,862 s for 279.39 h (21.0 s/h overall, **not** a median) |
| O2 (A9) | chain structure | gaps G1–G5 (Table 1), hypotheses H1–H3, contributions C1–C5 with evidence, answer sentence per Ch3 section, new Discussion 4.2 |
| O3 (A10) | Siena hours sentence | A4 wording + PN14 clause (outline §9 O3) |
| O4 (A11) | new Table 6 "Decision matrix for the normal reference" | yes |
| O5 (A12) | appendix numbering | integer numbering continues; "Appendix A: …", cited as [Appendix A] |
| O6 (A13) | Table 3 row labels | keep (default) or rename three labels, weeks unchanged |

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
| 1 | 12/10 | thesis chat "Outline v8" | critique + outline | **done**: `REPORT_OUTLINE_v8.md` rev 1; approvals O1–O6 pending |
| 2 | 13/10 morning | thesis chat **"Figures v8"** + Claude Code | resolve outline §8.2 checks 1–13 (one command each); S2 scripts `src/figures_v8/*.py` that read committed results (rule 13) for Figures 3, 6, 9, 10, 12, 13, 16, 17 and Table 10; `docs/prompts/CC_FIGURES_V8.md` for Claude Code: Figure 8 (drift), Figure 14 (gallery, 5 panels; EDF + score caches), with estimated runtime | PNG in `Reports/v8/figures/`, table CSV/MD in `Reports/v8/tables/`, check results written into the outline (rev 2) |
| 3 | 13/10 | thesis chat **"Write Ch2–Ch3 + Appendix"** | from the approved outline and the chat-2 exhibits | chapter files in `Reports/v8/chapters/`, appendix in `Reports/v8/appendix/` |
| 4 | 13–14/10 | thesis chat **"Write Ch4, Ch1, Ch5, front matter"** | from the outline + Ch2–3 | chapter files |
| 5 | 14/10 morning | thesis chat **"Check and assemble"** + accounts `xanh` (numbers vs files, outline §6), `en` (English), `hồng` (references) | page count measured (cut order outline §2), number check, polish | v8 for the supervisor |
| 6 | 14–15/10 | thesis chat **"Final revision"** | supervisor comments → submission | submitted report |

**Start prompt of chat 2 (copy):**
> Chat 2 — Figures v8. Đọc `STATUS_BOARD.md` (rev 2) và `REPORT_OUTLINE_v8.md`, làm task #2. Duyệt O1–O6:
> [điền]. Bắt đầu bằng các check ở outline §8.2 (mỗi check một lệnh), rồi viết script hình/bảng và prompt
> Claude Code cho Figure 8 và Figure 14. [Nếu có: dán abstract của 3 paper N1–N3.]

Files chat 2 needs (project): this board, `REPORT_OUTLINE_v8.md`, `PERF_PHASE_RECORD.md`,
`HANDOFF_REPORT.md`, `e23_SUMMARY.md`, `x1_SUMMARY.md`, `p3c_SUMMARY.md`, `p2_ledger.csv`,
`DEMO_FINAL_HANDBACK.md`, `GATE.md`, `TIMING.md`, `Thesis_Reference_Sheet.md`, `Chapter_3_Results_v5.md`.

## 7 · Open checks (small, any time)

- Outline §8.2, items 1–13 (chat 2).
- Abstracts of N1 (10.1016/j.compbiomed.2025.110168), N2 (10.1016/j.bspc.2023.105464), N3
  (10.1016/j.knosys.2025.114199): not readable from the cloud session (paywall, HTTP 429 on 09/10 and
  12/10). The author pastes them if he can open them; otherwise they stay title-only citations.
- The author mentioned "timeline thực tế" and "ghi chú" for chat 1; they did not arrive. Table 3 keeps the
  draft's weeks by the author's decision; any other note goes to chat 2.

## 8 · Where the numbers are (for the outline and the writing chats)

| content | file |
|---|---|
| every number of the final system, held-out/final evaluations, external, decisions | `docs/PERF_PHASE_RECORD.md` (rev R) — authority |
| what the report says, disclosures, translations of internal names | `docs/HANDOFF_REPORT.md` (rev 2; its section 0 is superseded by this board) |
| **numbers chosen for each section, with their source and reading** | `docs/writing/REPORT_OUTLINE_v8.md` §3 and §6 |
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
