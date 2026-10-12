# STATUS_BOARD — thesis report phase (rev 1, 2026-10-12)

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

## 2 · Where things stand (12/10, 15:00)

| track | state | next |
|---|---|---|
| Performance | **closed** (tag `perf-p3-closed`); numbers in `PERF_PHASE_RECORD.md` rev R | none |
| External validation | done (`results/x1_external/`); Siena hours question **open** (A4) | PN14 header check (section 7) |
| Channel attribution | closed (A4, A5) | none |
| Demo backend | rebuilt on the final system, commit `936b8e0`, tags `szscan-frozen-v3`, `demo-final-v1`; tests 11/11 green; **identity gate PASS** on chb03 (`results/t1_demo/GATE.md`); timing median **21.68 s per hour of EEG**, chb16, 3 runs (`results/t1_demo/TIMING.md`) | — |
| Demo remaining | timeline-row decision, `web_demo/` doc update and tidy-up, real-UI smoke test, freeze tag, **application run on the 8 test subjects**, new screenshots, network-off check, push | **Claude Code tonight**: `Code/docs/prompts/CC_DEMO_FINISH.md` |
| Report | draft sent to supervisor 11/10 (`Reports/submitted/2026-10-11_draft_to_supervisor.*`, built by the author from v6). Supervisor feedback 12/10, section 3. **v8 restarts from v5** (chapter files in the Claude project) | outline v8 (next chat) |
| Local files | inventory 12/10; tidy-up command delivered with this board | author runs it once |
| Git | `main` 4 commits ahead of `origin` (pushed by the demo prompt at the end) | — |

## 3 · Supervisor feedback on the 11/10 draft (12/10) → what v8 does

| # | feedback (paraphrased) | v8 answer |
|---|---|---|
| F1 | cut too much to fit 50 pages | the draft body was ~45 pages, with Methods ~21 and Results ~7: rebalance (Methods ~15–16, Results ~15–16) and move detail to an appendix (outside the 50) |
| F2 | results not detailed | Results restores the v5 tables (held-out vs final, per patient, onset/offset per set, external, channel) plus the new items below |
| F3 | also show methods tried that did not work | a results table of the designs evaluated on the 15 development patients (number, reference, one-line reason); full list in the appendix; mechanisms discussed in Chapter 4. No internal names, no chronology; the numbers are labelled "development patients" (optimistic, rule 19) |
| F4 | external validation too thin | its own section: per-patient Siena table, chb24, seed spread, bootstrap interval, precision/F1 beside DynaSD, adult vs child, false-alarm drivers (PN06, PN07, PN16), onset/offset, one example figure, data accounting |
| F5 | add figures of detected seizures | a figure set with raw EEG + score + detector and localizer events: well-detected (CHB-MIT test), near miss (chb15), missed short seizure (chb16), a false alarm, one Siena seizure |

Also found in the 11/10 draft (fix in v8): Figure 14 shows the **earlier** application's screens (to be
retaken); Table 6 puts a pooled count (37 detected) and a subject-mean sensitivity (0.577) in one row;
the Siena-hours sentence reads like an internal note. The chb03 application checks (7/7 with 22 false
alarms; 6/7 with 20) and the 21.68 s/h timing **are** sourced (`results/t1_demo/`).

## 4 · Approvals pending (author answers at the start of the next chat)

| # | question | proposal (Claude, as researcher) |
|---|---|---|
| A1 | base text of v8 | v5 chapters + from the 11/10 draft: the supervisor's papers in Ch1/Ch4, Table 1 (research gaps), the single 33-item reference list, the figures that are already right |
| A2 | appendix (reverses the 30/09 "no appendix" decision) | yes, ~8–12 pages, outside the 50: A data accounting (CHB-MIT split per case; Siena per patient), B settings of the final system, C all development designs with numbers, D per-patient results (test, all seeds; Siena; chb24), E channel annotation protocol and per-seizure values, F application: guards, tests, timing per stage. Main text keeps the summary tables |
| A3 | tried designs in Results | yes, as a results table (development patients) — Report format: Results = "what you obtained or failed to obtain"; offline protocol stays one paragraph (record 10.1) |
| A4 | Siena hours (141.0 h scored vs "about 128 h" on PhysioNet) | finding below; wording: "The PhysioNet summary table lists about 128 h; the EDF files of the 14 patients contain 141.0 h, which is the time scored here (false alarms per day use it). For PN03, PN10 and PN12 the summary table is shorter than the registration times in the patients' own seizure lists, which agree with the files." Per-patient table in Appendix A. PN14 checked first (section 7) |
| A5 | application run on 8 patients | reported as its own row ("review application, label-free statistics"), beside the system's result, never merged; the difference is explained by the one divergence (z-score statistics), measured on chb03 (7/7 vs 6/7) |
| A6 | page budget | body ≤ 50 measured: Ch1 ~8, Ch2 ~15–16, Ch3 ~15–16, Ch4 ~8–9, Ch5 ~1–2 |
| A7 | `Code/bme11/` (BME11 paper, untracked in the thesis repo) | leave in place, add to `.gitignore` (done by the tidy-up); move out after the defense |

**A4 finding (12/10, measured).** Scored hours = 4-s windows × 4 s of the actual EDF signal
(`x1_external.build_subject`). PhysioNet `subject_info.csv` sums to 7,704 min = 128.4 h. Per patient
(ours vs table): PN03 24.23 vs 12.53 h; PN10 18.72 vs 16.70; PN12 6.10 vs 4.10; PN14 20.46 vs 23.47;
the other ten agree within 0.2 h. The registration start/end times in `Seizures-list-PN03/PN10/PN12.txt`
add up to 24.22 h, 18.72 h and 6.10 h — equal to ours, so the summary table is the outlier for those
three. PN14: its seizure list adds up to 23.46 h but our files hold 20.46 h (−3.0 h) — unexplained until
the EDF headers are read (section 7).

## 5 · Layout (after the 12/10 tidy-up)

```
F:/Study/Thesis/
  Code/                         git repo (github.com/Nhanvas/Thesis, main)
    docs/                       documents of record + STATUS_BOARD.md + PROJECT_INSTRUCTIONS.md
      writing/                  report rules (AUTHOR_REQUIREMENTS, REVIEWER_RULES, RUBRIC_MAP, SAMPLE_PATTERNS,
                                REPORT_BLUEPRINT_v5) — the outline v8 will be added here
      prompts/                  Claude Code prompts (CC_DEMO_FINISH.md, …)
      prereg/  archive/         pre-registrations; superseded docs (never cite)
    src/  results/  data/       code, committed results, inputs (large caches gitignored)
    web_demo/                   SzScan (owned by the demo work; CLAUDE.md inside)
  Reports/
    v8/  chapters/ figures/ tables/ appendix/    ← the only place where v8 is written
    v8/figures_inherited/       figures of the 11/10 draft (starting point, to be regenerated)
    submitted/                  what was sent to the supervisor (dated)
    Sample report/              VBPH, Tri, … (style samples)
  Agent/inbox/                  hand-over tray only (empty at the end of every chat)
  Archive/2026-10-12/           everything superseded: old Agent staging, old Reports notes, Threshold,
                                untracked duplicates; MOVES.csv + UNDO.sh
  Dataset/  Papers/             unchanged
```

## 6 · Plan of chats (one task each)

| # | when | chat / tool | task | output |
|---|---|---|---|---|
| 0 | 12/10 | this chat | inventory, tidy-up, board, instructions, demo prompt | done |
| D | 12/10 night | **Claude Code** (laptop) | `docs/prompts/CC_DEMO_FINISH.md` | `web_demo/report_handback/DEMO_FINAL_HANDBACK.md`, `results/application_eval_v4/`, screenshots in `Reports/v8/figures/app_screens/` |
| 1 | 13/10 morning | thesis chat **"Outline v8"** | approvals A1–A7; outline of the whole report: every section → content, numbers (with source file), figure/table (with data source), main vs appendix, page budget | `docs/writing/REPORT_OUTLINE_v8.md`, approved |
| 2 | 13/10 | thesis chat **"Figures v8"** + Claude Code | scripts that read committed results (rule 13) for every new figure/table; gallery figures need EDF + score caches → run by Claude Code | `src/figures_v8/*.py`, PNG in `Reports/v8/figures/`, table CSV/MD |
| 3 | 13/10 | thesis chat **"Write Ch2–Ch3 + Appendix"** | from the approved outline | chapter files in `Reports/v8/chapters/` |
| 4 | 13–14/10 | thesis chat **"Write Ch4, Ch1, Ch5, front matter"** | from the outline + Ch2–3 | chapter files |
| 5 | 14/10 morning | thesis chat **"Check and assemble"** + accounts `xanh` (numbers vs files), `en` (English), `hồng` (references) | page count measured, number check, polish | v8 for the supervisor |
| 6 | 14–15/10 | thesis chat **"Final revision"** | supervisor comments → submission | submitted report |

**Start prompt of chat 1 (copy):**
> Chat 1 — Outline v8. Đọc `STATUS_BOARD.md` (rev mới nhất) và làm task #1. Trả lời duyệt A1–A7 của tôi:
> [điền]. Kết quả demo đêm qua: [đính kèm `DEMO_FINAL_HANDBACK.md` và `results/application_eval_v4/SUMMARY.md`,
> hoặc ghi "chưa xong"].

Files chat 1 needs (project): this board, `Chapter_*_v5.md`, `Front_matter_v5.md`,
`2026-10-11_draft_to_supervisor.md`, `PERF_PHASE_RECORD.md`, `HANDOFF_REPORT.md`, `x1_SUMMARY.md`,
`e23_SUMMARY.md`, `p3c_SUMMARY.md`, `p2_ledger.csv`, `ATTRIBUTION_SPEC.md`, writing rules,
`Thesis_Reference_Sheet.md`, `GATE.md`, `TIMING.md`.

## 7 · Open checks (small, any time)

- **PN14 EDF durations** (A4). Kaggle notebook with the Siena dataset attached, one cell, ~1–2 min
  (estimated):
  ```python
  import glob, os, mne
  for p in sorted(glob.glob('/kaggle/input/**/PN*.edf', recursive=True)):
      r = mne.io.read_raw_edf(p, preload=False, verbose=False)
      print(os.path.basename(p), round(r.n_times / r.info['sfreq'] / 3600, 4))
  ```
  Paste the printout into chat 1. Expected from the seizure list: PN14-1 2.19 h, PN14-2 2.55 h, PN14-3
  14.67 h, PN14-4 4.07 h (computed from its registration times).
- Normalisation-statistics effect on CHB-MIT: measured on chb03 only (`results/t1_demo/gate.json`:
  label-free statistics 6/7 vs 7/7). The application run on 8 patients gives the full picture (A5).

## 8 · Where the numbers are (for the outline and the writing chats)

| content | file |
|---|---|
| every number of the final system, looks #6/#7, external, decisions | `docs/PERF_PHASE_RECORD.md` (rev R) — authority |
| what the report says, disclosures, translations of internal names | `docs/HANDOFF_REPORT.md` (rev 2; its section 0 order of work is superseded by this board) |
| development designs, one row per arm (P2/P3) | `results/p2_ledger.csv` (`verdict` = step gate, not the final choice) |
| P1 designs (cross-patient normal, per-patient density, v2 GAE, kernel CPD as detector, …) | record section 2 |
| look #6 / look #7 per patient, seeds, onset/offset | `results/e22_test_oneshot/SUMMARY.md`, `results/e23_test_look7/SUMMARY.md` |
| external per patient, per seed, onset/offset | `results/x1_external/SUMMARY.md` |
| seizure-level failure anatomy (p_need) | `results/p3_anatomy/` (record 9.6) |
| channel attribution | `results/attribution_v8/`, `results/attribution_v7/`, `docs/ATTRIBUTION_SPEC.md` |
| demo identity gate, timing | `results/t1_demo/GATE.md`, `gate.json`, `TIMING.md` |
| application run on 8 patients | `results/application_eval_v4/` (after tonight) |
| references and DOIs | `docs/Thesis_Reference_Sheet.md` (groups K–N) |

## 9 · Decisions log

- 2026-10-08: record 10.1 (offline protocol one paragraph; label-free per-patient fitting is part of the
  system; CPD = localizer; looks #6 and #7 side by side; pooled + subject-mean; seed 42 headline).
- 2026-10-10: one shared reference list; supervisor's papers in Ch1 and Ch4; look #6 kept.
- 2026-10-12 (author): work split into one-task chats with this board as the hand-over; outline before
  writing; demo must be finished (overnight runs allowed); appendix to be reconsidered (A2); unclear
  facts go to the author for approval first; v8 restarts from v5.
