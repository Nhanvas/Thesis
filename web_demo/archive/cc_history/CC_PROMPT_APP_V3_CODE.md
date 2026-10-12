# CC_PROMPT_APP_V3_CODE.md — application v3, code changes only

Bound by `web_demo/CLAUDE.md`. Edit only inside `web_demo/`. **Code and tests only: do not upload,
process or score any recording, and do not start the backend on real data.** A thesis evaluation job
may be running on this machine; keep CPU and memory use to what the tests need.

## Why

The thesis evaluation on the continuous timeline added one data-quality rule (Amendment A2 in
`docs/CC_PROMPT_CONTINUOUS_EVAL.md`) and will select a new operating point and event-merge gap on the
validation patients. The application must carry the same rule, and must accept the selected values as
constants, before it is rerun on the test patients.

## Changes

1. **Signal-loss rule, mirrored exactly from the thesis code.** Read Amendment A2 and the Scope W path
   of `src/continuous_eval.py` (read only; do not import it into the application) and implement the
   same rule in `pipeline_demo.py`: a window is flagged when the standard deviation of its raw
   (unfiltered) signal is below 1e-10 V on every one of the 18 channels. Flagged windows are excluded
   from every subject-wide fit exactly where Scope W excludes them (z-score statistics if Scope W
   excludes them there, LedoitWolf, per-branch robust-z median and MAD, the CPD penalty variance and
   magnitude background, and the per-channel attribution baseline); they keep their place on the
   timeline with fused score 0. Quote, in the step report, the Scope W lines you mirrored and the
   application lines you changed, side by side.
2. **Constants.** `FIXED_MAG_PCT`, `FIXED_PEN_MULT` and a new `FIXED_MERGE_S` (default 90) in one
   place, passed to the single `detect_events` call. Leave the current values 50 / 2.0 / 90; the new
   values come in a later instruction. Leave `MIN_MAG_PCT` untouched.
3. **A headless entry point** `process_subject_headless(edf_paths) -> {filename: fused score}` that
   runs Phase A and Phase B through the same functions the live flow uses, with no database and no
   HTTP, so the thesis side can run the application's own computation on the validation patients.
   It must not read any annotation.

## Tests (add to `web_demo/backend/tests/`, run all, including `test_guards.py`)

- synthetic recording with a flat segment: flagged windows get score 0 and are absent from every fit;
- a recording with no flat window gives bit-identical scores before and after this change
  (max abs diff 0 on the fused score) — run on a short synthetic signal, not a real EDF;
- `detect_events` receives the three constants;
- `process_subject_headless` gives the same scores as the live Phase A + Phase B path on a synthetic
  two-file subject;
- the existing label guards still pass unchanged.

## Finish

Commit only the changed files under `web_demo/`, explicit paths, inside `bash -e`, message
`App v3 code: signal-loss rule, merge constant, headless entry (no rerun yet)`. Do not tag. Report
the side-by-side quote, the test results, and the commit hash. Expected time: 30–45 minutes.
