# CC_FIX_OPPOINT_REPORT.md — fixed validation operating point (mag_pct=50, pen_mult=2.0)

## What changed

All edits are in `web_demo/backend/pipeline_demo.py` (plus one dated SPEC note); nothing under
`src/*.py` was touched, and no `git add`/commit/push was run.

**Note on the cited source doc:** `REPORT_REPLY_TO_PROJECT2_OP.md` does not exist anywhere in the
repo (checked via grep across the whole tree — only this prompt file references it). I cited it
in the new comments/SPEC note exactly as instructed, on the assumption it exists outside this
repo snapshot or is forthcoming; flagging this in case that's not expected.

### 1. Two new named constants — `pipeline_demo.py:109-110`

```
web_demo/backend/pipeline_demo.py:109   FIXED_MAG_PCT = 50
web_demo/backend/pipeline_demo.py:110   FIXED_PEN_MULT = 2.0
```

Added directly below the existing `MIN_MAG_PCT = 60` line, with a comment (lines 103-108) citing
`REPORT_REPLY_TO_PROJECT2_OP.md` section 1 as the source: validation-derived, fixed on the three
VAL patients before any test patient was scored, not read from the patient being processed.

### 2. `process_subject_events()` — changed call at `pipeline_demo.py:597-599`

Old:
```python
op = calibrate_operating_point(global_score, total_hours)
events_global = cpd_pipeline_v14.detect_events(global_score, op.pen_mult, min_mag_pct=MIN_MAG_PCT)
```

New:
```python
events_global = cpd_pipeline_v14.detect_events(
    global_score, FIXED_PEN_MULT, min_mag_pct=FIXED_MAG_PCT
)
event_rate_per_day = (len(events_global) / total_hours * 24.0) if total_hours > 0 else 0.0
op = OperatingPointResult(
    pen_mult=FIXED_PEN_MULT,
    event_rate_per_day=event_rate_per_day,
    grid=[(FIXED_PEN_MULT, len(events_global), event_rate_per_day)],
)
```
(`pipeline_demo.py:597-604`)

**What I did with `grid`:** it's no longer a search result (there is no grid search on this path
any more), so I did not leave it empty or fabricate the old 6-point grid. Instead it holds exactly
one tuple — `(FIXED_PEN_MULT, n_events, event_rate_per_day)` for the single point actually used —
keeping the same `list[tuple[float, int, float]]` shape `pipeline_worker.py`'s
`_run_process_events()` already serializes to JSON (`result["grid"]`), so nothing downstream
breaks. Confirmed `upload_manager.py` never reads `result["grid"]` (only `pen_mult` and
`event_rate_per_day`, at `upload_manager.py:409-410`), so this is purely informational.

`OperatingPointResult` itself is untouched — still returns the same dataclass shape
`upload_manager.py`'s session snapshot expects.

Also updated the Stage 2 description in the module docstring (`pipeline_demo.py:29-35`) and the
`timing` docstring in `process_subject_events()` (`pipeline_demo.py:566-570`), which both
previously said Stage 2 "calibrates a label-free per-subject operating point" — that's no longer
true and would have been misleading left as-is.

### 3. `calibrate_operating_point()` kept, marked reference-only — `pipeline_demo.py:530-534`

Not deleted, per the prompt. Added a comment immediately above the function:

```python
# No longer called on the live processing path (see FIXED_MAG_PCT/FIXED_PEN_MULT above) --
# kept for reference only, as a documented "not built" alternative (future work, thesis
# Chapter 4 section 4.5). The __main__ CLI smoke-test block at the bottom of this file still
# calls it for dev-only comparison against the fixed operating point.
def calibrate_operating_point(...):
```

`MIN_MAG_PCT`, `PEN_MULT_GRID`, `TARGET_FP_PER_DAY` are all untouched.

### 4. Grep confirmation (step 4)

```
$ grep -n "calibrate_operating_point" backend/pipeline_demo.py backend/upload_manager.py \
    backend/pipeline_worker.py backend/backfill_scores.py backend/measure_stage_timing.py \
    backend/backfill_pernode.py

backend/pipeline_demo.py:32:    calibrate_operating_point()), runs cpd_pipeline_v14.detect_events() once on the whole
backend/pipeline_demo.py:103:# Per-subject label-free calibration (calibrate_operating_point() below) is no longer run on
backend/pipeline_demo.py:535:def calibrate_operating_point(global_score: np.ndarray, total_hours: float) -> OperatingPointResult:
backend/pipeline_demo.py:680:    op = calibrate_operating_point(score, total_hours)
backend/measure_stage_timing.py:48:    "cpd": "Stage 2: calibrate_operating_point + detect_events",
```

- Line 32 and 103 are prose comments (module docstring / reference-only note), not calls.
- Line 535 is the `def` itself.
- **Line 680 is the only remaining call**, inside the `if __name__ == "__main__":` CLI
  smoke-test block at the bottom of the file (dev-only comparison print, not on the
  `process_file` / `process_subject_events` / `upload_manager.py` live path) — matches what the
  prompt anticipated in step 4.
- `measure_stage_timing.py:48` is just a stale string label for a timing bucket display (not a
  call); left as-is since it's outside this prompt's scope (only `pipeline_demo.py` was in
  scope) and doesn't affect correctness — flagging it in case Project 1 wants it relabeled later
  since Stage 2 no longer calibrates.
- Confirmed via grep that `upload_manager.py` and `pipeline_worker.py` never call
  `calibrate_operating_point` directly — they only call `process_subject_events()`.

### 5. Dated SPEC 8 (O1) note

Added a "**SUPERSEDED 2026-09-29**" clause to the existing O1 row in
`web_demo/SZSCAN_SPEC_v5.md` §8, recording: fixed `mag_pct=50`/`pen_mult=2.0` for every patient
(shipped default + Tier 2 run), citing `REPORT_REPLY_TO_PROJECT2_OP.md` §1, and noting
`calibrate_operating_point()` no longer runs on the live path but stays as a documented
not-built alternative (thesis Ch.4 §4.5). Original RECORDED text for the old grid-search
description left in place (struck through row, as the doc's own convention already uses `~~O1~~`
for closed/updated items).

## Guards

```
backend/tests/test_guards.py::test_guard_no_build_timeline_masked PASSED
backend/tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED
backend/tests/test_guards.py::test_guard_no_labeled_npy PASSED
backend/tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED
4 passed in 2.86s
```
(Also ran and confirmed 4/4 green before making any changes, as a baseline.)

## Explicitly NOT done (per prompt)

- No subject reprocessing — existing DB events still reflect the old per-subject calibration and
  will not match this code until the full reprocess in Part 3 of `REPORT_REQUEST_TO_PROJECT2.md`.
- No `git add`/commit/push.
- No edits under `src/*.py`.
