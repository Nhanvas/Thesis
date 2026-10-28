# V9-E1b — Give the winning arms their own fair operating point, then evaluate once (Claude Code, laptop)

Estimated runtime: 2–4 h (estimated, not measured). Run **after** `V9_T4` has finished (RAM). Smoke first, report the projected total.

## Why
`V9_E1` showed that B4 (12 node features + kNN) and F (rank-mean of GAE + B4) beat the GAE at **matched FP/day** (global budget, detector stage) on development and on CHB-MIT test. But at the "balanced" point every baseline ran at ~55–60 FP/day, because the per-patient budget `k = 4.0677` was calibrated for the GAE score, not for theirs. A system comparison needs each arm calibrated **the same way, on development only**.

## Steps
1. Find the exact procedure that produced `k = 4.0677` and the clip `(0.005, 0.02)` (P3-L2 / P3-L2f in `src/p3_levers.py`, `src/p3c_freeze.py`). Apply **the same procedure, unchanged**, to B4 and to F, using **development patients only** (train + validation). Report the new `k` for each. Nothing on CHB-MIT test, chb24 or Siena may influence it.
2. Evaluate G, B4 and F at their own calibrated point, after the CPD localizer, once, on: development, CHB-MIT test (8), chb24, Siena 14 (needs the raw-feature cache for all 14 patients — build it with `v9_e1_baselines.py --ext` now that `V9_T4` has the EDFs; same 1 worker at a time).
3. Report per set: tp/ref, FP, sensitivity, precision, F1, FP/day (pooled and per-patient mean), 4-seed mean ± SD for G and F (B4 is deterministic), patient bootstrap 95% CI, duration bins, onset/offset |error| (median) of the localizer.
4. System-stage curve: sweep `k` (characterisation only) for G, B4, F and plot per-patient-mean sensitivity against FP/day per set, after the localizer; read off 20 / 27.5 / 44 FP/day.
5. Do not change the demo, the frozen scripts or the committed results. New code `src/v9_e1b_calibrate.py`, outputs `results/v9_e1b/`. Commit only these paths.

## Return format
Full report to `F:/Study/Thesis/Agent/inbox/V9_E1B_REPORT.md`: calibrated `k` per arm (from development), one table per set, the system-stage matched-FP table, runtime measured.
