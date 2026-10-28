# V9-E3 — Short-seizure branch (multi-scale score) (Claude Code, laptop)

Estimated runtime: Part A 1–2 h; Part B: measure first (estimated, not measured). Run **after** `V9_E2` Part A has finished (RAM). One patient at a time, single worker. Smoke first.

## Why
Seizures ≤ 20 s are the main miss: CHB-MIT test 7/24 caught (G, seed 42), similar for B4 and F (`results/v9_e2/`). Likely causes inside the system: 4-s windows and the 5-window (20 s) moving average dilute a 8–16 s burst before the per-patient budget ranks it. The development patients contain only 3 seizures ≤ 20 s, so a short-seizure lever **cannot be tuned on development**: every configuration below is fixed now from the mechanism, not selected; development is only used for the label-free budget calibration and as a non-inferiority check.

## Part A — S1: two time scales on the existing 4-s scores (cheap, cached)
For each arm G and F (the frozen ensemble score per window, before smoothing):
- long branch = the frozen path (smoothing 5 windows);
- short branch = the same score smoothed over **2 windows** (8 s);
- each branch converted to within-patient percentiles exactly as the frozen chain does; final score = **max(long, short)** per window;
- per-patient budget: k recalibrated with `p3_levers.calibrate()` **unchanged** on development (label-free, as in V9_E1b), same clip (0.005, 0.02), merge 90 s, CPD localizer.
If the frozen code smooths at a different stage than described, follow the code and say exactly where the branch splits.
Evaluate once on development, CHB-MIT test, chb24, Siena 14: tp/ref, FP, sens, prec, F1, FP/day (pooled and per-patient mean), 4 seeds for G and F, duration bins at seed 42, onset/offset error, system-stage matched-FP curve (20 / 27.5 / 44), paired bootstrap vs the same arm without the short branch (difference in per-patient-mean sensitivity at matched FP/day, and in F1 at own point).
If `V9_E2` Part A adopted a veto, also report "S1 + veto" with the veto threshold unchanged.

Adoption rule (fixed now): S1 is adopted for an arm if on development the paired difference at 27.5 FP/day has a 95% CI lower bound ≥ −0.05 (non-inferior) **and** on the pooled external + test sets the ≤ 20 s detections increase. Report the verdict whatever it is.

## Part B — S2: 2-s windows, feature branch only (only if time allows)
Short branch computed from the 12 per-channel node features (5 band powers + 7 amplitude features; no graph — connectivity is unreliable on 2 s) on 2-s windows with 1-s hop, scored with the B4 kNN recipe, then the same max fusion and calibration as S1.
First measure the feature-extraction + kNN time on one development patient and one test patient, project the total, and **stop and report** before running all. Run only if the author approves.

## Rules
Read-only on frozen scripts and committed results. New code `src/v9_e3_short.py`; outputs `results/v9_e3/`. Commit only these paths. Do not touch `web_demo/`.

## Return format
Full report to `F:/Study/Thesis/Agent/inbox/V9_E3_REPORT.md` (Part A results + verdict; Part B projected runtime or results).
