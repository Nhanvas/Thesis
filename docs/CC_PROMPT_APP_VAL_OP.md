# CC_PROMPT_APP_VAL_OP.md — application v3 on the validation patients: operating point

Thesis side (reads validation annotations): code in `src/`, outputs in `results/app_eval_v3/`, nothing
written inside `web_demo/`. **Validation patients only: chb10, chb11, chb22. The script carries a TEST
guard that aborts if any test subject (chb03, 06, 13, 14, 15, 16, 17, 18) is requested.**

Can run while the continuous-evaluation Step C is running: Phase A at most 2 workers, one subject at a
time, cache on F: (TMP/TEMP on F:), bounded memory. Expected time 50–70 minutes.

## Steps

1. Gate: `python src/verify_provenance.py` → PASS. Record `git rev-parse HEAD` and confirm
   `web_demo/backend/pipeline_demo.py` is at commit `3336bd7` (App v3 code); stop if not.
2. For each validation subject, call `web_demo/backend/pipeline_demo.process_subject_headless` on all
   its EDFs (import read-only; do not edit any `web_demo/` file), with a cache directory under
   `results/app_eval_v3/cache/{subj}/`. Keep the per-file fused scores and signal-loss flags.
3. Event grid, exactly as the application builds events: files concatenated in file-name order,
   `cpd_pipeline_v14.detect_events(global_score, pen_mult, min_mag_pct=mag_pct, inter_mask=~flags,
   merge_s=merge_s)`, the same 8 magnitude percentiles × 6 penalty multipliers as the thesis grid, ×
   `merge_s` ∈ {90, 300}. PELT once per penalty per subject; magnitude and merge as post-processing
   on the stored change points, verified on one subject against a direct `detect_events` call
   (identical events) before use. Events mapped to files as `process_subject_events` does.
4. Score every grid point against the validation annotations with the same SzCORE scorer used for
   the application's test evaluation; FA/day denominator = recorded time minus seizure time minus
   signal-loss time.
5. Select, and report both:
   - **Amendment A8 rule (reported result):** maximize pooled validation sensitivity subject to
     pooled validation FA/day ≤ 25; ties by lower FA/day, then lower penalty.
   - Step A rule (information): sensitivity and precision closest to equal.
6. Write `results/app_eval_v3/val_grid.csv`, `results/app_eval_v3/SELECTED.md` (both selections,
   pooled and per subject, commit hashes, wall-clock time), and commit `src/<script>.py` and
   `results/app_eval_v3/` (not the cache) with explicit paths inside `bash -e`. Do not change any
   application constant: the selected values go to Project 2 in a separate instruction.
