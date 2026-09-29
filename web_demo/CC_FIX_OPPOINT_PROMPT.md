# CC_FIX_OPPOINT_PROMPT.md — fixed validation operating point (mag_pct=50, pen_mult=2.0)

Per Project 1's methodological decision (REPORT_REPLY_TO_PROJECT2_OP.md, confirmed by the
author): the application uses ONE fixed operating point for every patient, both as the shipped
default and for the Tier 2 run: mag_pct = 50, pen_mult = 2.0. The per-subject label-free
calibration (`calibrate_operating_point()`, grid search, MIN_MAG_PCT = 60) must no longer run on
the live processing path.

In pipeline_demo.py:
1. Add two named constants near the existing MIN_MAG_PCT/TARGET_FP_PER_DAY block:
   FIXED_MAG_PCT = 50 and FIXED_PEN_MULT = 2.0, with a comment citing
   REPORT_REPLY_TO_PROJECT2_OP.md section 1 as the source (validation-derived, fixed on the three
   VAL patients before any test patient was scored -- not read from the patient being processed).
2. In process_subject_events(): replace the call to calibrate_operating_point(global_score,
   total_hours) and the subsequent detect_events(global_score, op.pen_mult,
   min_mag_pct=MIN_MAG_PCT) with a single detect_events(global_score, FIXED_PEN_MULT,
   min_mag_pct=FIXED_MAG_PCT) call. Keep returning an OperatingPointResult-shaped value (whatever
   upload_manager.py's session snapshot already expects) but with pen_mult=FIXED_PEN_MULT and
   event_rate_per_day computed from the resulting event count / total_hours * 24 -- state exactly
   what you did with the `grid` field.
3. Do NOT delete calibrate_operating_point(), MIN_MAG_PCT, PEN_MULT_GRID or TARGET_FP_PER_DAY --
   Project 1 is keeping the per-subject label-free calibration as a documented "not built"
   alternative (future work, thesis Chapter 4 section 4.5). Add a comment above
   calibrate_operating_point() stating it is no longer called on the live path, kept for
   reference only.
4. Confirm with grep that calibrate_operating_point is no longer called anywhere in
   process_file / process_subject_events / upload_manager.py's call chain (the __main__ CLI
   smoke-test block at the bottom of pipeline_demo.py may still call it for dev-only comparison --
   note if it does).
5. Add a dated SPEC 8 (O1) note recording the change: fixed mag_pct=50/pen_mult=2.0 for every
   patient, superseding the per-subject label-free calibration description.

Do NOT reprocess any subject in this prompt -- that happens later, once per Part 3 of
REPORT_REQUEST_TO_PROJECT2.md (clean DB, full reprocess of all 8 on the frozen build). Existing
DB events will not match the new code until then; do not "fix" that here.

Guards must stay 4/4 (paste raw pytest -v). No git add/commit/push. Do not touch src/*.py.

Report to CC_FIX_OPPOINT_REPORT.md: exact file:line for both new constants, exact file:line of
the changed call in process_subject_events, and the grep confirmation from step 4.