# CC_STEP9_PHASE1B_PROMPT.md — Step 9, phase 1b: measure the real "Process" (PELT) cost

Read first: `web_demo/CC_STEP9_PHASE1_REPORT.md §4.3` (the timing gap this prompt exists to close),
`web_demo/SZSCAN_SPEC_v5.md §1.7`, `web_demo/backend/pipeline_worker.py`'s `_run_process_events`
(already identified by phase 1's report).

Phase 1 found that the only cost figure ever measured (`9.76 s/hour`, `CLAUDE.md`) covers
`pipeline_demo.process_file` (Phase A + B) only, and **never** includes the "Process" step — PELT run
**6 times** per subject (once per `pen_mult` in `DEFAULT_PENS`), over the subject's whole concatenated
timeline. No PELT wall-clock number exists anywhere in this repo, despite the spec itself calling this
"the most time-consuming part" (`SZSCAN_SPEC_v5.md §1.7`). Before committing to processing the 7
missing subjects (up to 246 h of EEG combined, per phase 1's own table), get this real number first, on
the smallest missing real subject only.

Guards unchanged: `test_guards.py` must stay 4/4 green, no write outside `web_demo/`, no
`git add`/`commit`/`push`.

---

## Task

1. Upload **`chb16`** (19 real files, ~19.0 h total, per phase 1's own measured figure — the smallest
   of the 7 missing subjects) through the **genuine** Create-New → Upload → Process flow in the running
   app — the real UI flow, not a CLI shortcut, so the timing reflects what an actual defense-day upload
   would take, including any per-file upload overhead.
2. Record wall-clock time for the two stages **separately**:
   - **Phase A + B** (per-file `process_file`, the stage Step 1 already timed) — sum across all 19
     files, and sanity-check the result against the existing `9.76 s/hour` figure (should be in the
     same ballpark; note plainly if it isn't, and why).
   - **The Process/PELT step alone** (`_run_process_events` → `calibrate_operating_point` →
     `detect_events`) — timed as its own wall-clock duration, start to finish, covering all 6
     `pen_mult` passes over the full 19-file concatenated timeline. This is the number that has never
     existed until now.
3. Report both numbers, their sum (genuine end-to-end Create-New→Process time for this one real
   subject), and a derived **PELT-seconds-per-hour-of-EEG rate**, so it can be extrapolated to the other
   6 missing subjects' real durations from phase 1's own table (`chb03` 38.0 h, `chb06` 66.7 h, `chb14`
   26.0 h, `chb15` 40.0 h, `chb17` 21.0 h, `chb18` 35.6 h).
4. Do **not** delete `chb16` afterward — leave it in the DB as the first genuinely real cached subject
   from this effort. This measurement run doubles as real progress toward phase 2's actual goal, not
   throwaway work.

## Report

Write `web_demo/CC_STEP9_PHASE1B_REPORT.md`:

1. The two timings (Phase A+B, PELT alone) and their sum, for `chb16`.
2. The derived PELT-seconds-per-hour rate, plus a revised total-time estimate for the 6 remaining
   subjects using this real rate instead of phase 1's lower-bound-only guess (show the arithmetic, per
   subject and combined).
3. Any anomaly found — e.g. PELT scaling non-linearly with timeline length, memory pressure, or a
   crash/retry at this scale — stated plainly, not smoothed over.
4. Raw `pytest -v`, `git status`.

Then **stop. Do not run `git add`/`commit`/`push`. Do not start uploading the other 6 subjects** —
that is phase 2 proper, a separate prompt once this real number is known and reviewed.
