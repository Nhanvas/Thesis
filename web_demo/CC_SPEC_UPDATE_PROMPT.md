Update the repo copy of web_demo/SZSCAN_SPEC_v5.md (it already carries C24 - keep every
other section untouched):

1. Section 8, O1: record the operating-point procedure exactly as implemented in
   web_demo/backend/pipeline_demo.py calibrate_operating_point(): target =
   fp_budget_operating_point.BUDGETS["balanced"]; candidate grid = final_eval.DEFAULT_PENS;
   min_mag_pct = pipeline_demo.MIN_MAG_PCT; rate = events / total recording hours * 24
   (whole recording as denominator, no labels); chosen pen_mult = rate closest to target.
   READ the numeric values from the source files at edit time and print them - never type
   them from memory. Mark O1 as recorded.
2. Section 8, O4: close it - live-upload subject = chb16, chosen by measured end-to-end
   time (~5.7 min, the fastest of the 8), not by file count.
3. Section 1.7, the C23 note: it says Phase A concurrency is an open item, not fixed. Add a
   dated C25 (2026-09-28) stating it is now capped at 4 workers (ThreadPoolExecutor in
   upload_manager.py). Keep the original measurement text intact.
4. Section 5.6 (Delete): add one sentence that deleting a subject also removes
   uploads/{subject_id}/ from disk.

English only. Show the git diff of the file. No git add/commit/push.