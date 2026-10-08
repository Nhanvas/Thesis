# PROJECT STATUS — where the thesis stands (rev G, 2026-10-08)

Replaces rev E2/F in full (they described the earlier system as the thesis of record and predate the
performance phase; they remain in git history). This file is a short pointer; numbers live in:
`docs/PERF_PHASE_RECORD.md` (rev R; wins on any conflict) and `docs/HANDOFF_REPORT.md` (rev 2; the
entry point for report and demo work).

## Deadlines

IELTS 09/10/2026 · **report submission 15/10/2026** · defense 05–06/11/2026 (author-confirmed).

## Phase timeline (one line each)

- Phase A, rebuild, Phase B/C/D, attribution A4 (Sept 2026): earlier system V1 (rlg). Retired as the
  thesis system; its offline-protocol numbers stay in `RESULTS_OF_RECORD_phaseB.md` and appear in the
  report only in one paragraph on the evaluation protocol (author, 2026-10-08).
- 05/10: performance work re-opened after the continuous-timeline numbers (V1 23/76 @ 73.3 FP/day).
- P1 (E1–E10): diagnosis; GAE v2 adopted. P2 (E11–E22): per-patient per-channel latent readout, drift
  correction, latent-family ensemble, kernel-CPD localizer; look #6. P3: per-patient alarm budget; look
  #7 (test-informed). X1: external validation on chb24 and Siena. Closed: tag `perf-p3-closed`.
- 08/10: supervisor reviewed the briefing (`docs/BRIEFING_2026-10-08_vi.md`) and asked for the report
  with the current numbers. Attribution of the final system (A5) run and recorded. **Report phase.**

## The thesis system

The P3 frozen system (tag `p3-frozen`), described in `HANDOFF_REPORT.md` section 1. Headline model GAE
v2 clean seed 42 (`data/models_v2/`, identity `PROVENANCE_V2.md`). The earlier checkpoint
`data/models_retrain/gae_joint_seed42.pt` (V1) is kept for the baseline rows and the A4 attribution;
`python src/verify_provenance.py` still guards it.

## What is left (order: `HANDOFF_REPORT.md` section 0)

1. Web demo rebuilt on the final system and its application tier re-run (Project 2;
   `docs/DEMO_REBUILD_BRIEF.md`).
2. Exhibit set v5, then Chapters 1–5 and front matter rewritten (chapters v4 describe V1).
3. Figures and tables from committed results only.
4. Checks: Grammarly, rubric, paper-review protocol, 50-page body measured.
5. Slides and defense preparation.

## Integrity (binding; full list in the project instructions §6)

Numbers only from committed files; test looks disclosed; demo never touches labels; identify artifacts
by hash; archive, don't delete; figures read committed results.
