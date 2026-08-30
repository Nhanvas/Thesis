# PRE-REGISTRATION 07 — Per-subject label-free FP-budget operating point (Phase-B · primary event leg)

**Status:** COMMITTED before touching test. **Position (mine, for cô):** this is the *stronger primary*
than any shared point (RESELECT/PREREG_06 showed a single global threshold derived on 3 VAL subjects
cannot match SOTA on all axes on held-out subjects of differing difficulty). Per-subject calibration
removes that compromise and directly targets the decision-limited subjects (chb16/chb17, per T3).

## 0. Label-free claim (why this is NOT test-tuning)
`mag_pct` in `cpd_pipeline_v14._mag_filter` is a **percentile threshold computed over each subject's
interictal windows** (`real_inter`). Choosing a subject's operating point to hit a false-positive budget
uses **only** interictal quantities (`fp`, `n_inter_h`) — never seizure timing, sensitivity, or TP. In
deployment you have interictal EEG to calibrate per patient without any seizure labels. Sensitivity/TP are
**read off after** selection, never used in it (asserted in code). This is the sanctioned PREREG_04
approach ("label-free per-subject FP-budget"), which §0 already reports as "calibrated alongside".

## 1. Budgets (pre-registered, external — not chosen from test)
Per-subject target FP/day **B ∈ {5, 10, 20}**; **primary B = 10** (clinical review-triage tolerance).
B is fixed a priori; it is NOT tuned to the resulting sensitivity.

## 2. Selection rule (COMMITTED, per subject, from interictal only)
For each test subject independently, over its 48 grid cells:
1. Restrict to cells with interictal FP/day ≤ B.
2. If that set is empty (even the tightest cell exceeds B): take the single cell with min FP/day.
3. Else choose the cell with **max interictal FP/day** (spend the alarm budget — the label-free surrogate
   for maximal detection). Tie-break: lower `mag_pct`, then lower `pen_mult`.
Selection reads only {mag_pct, pen_mult, fp, n_inter_h}. TP/sensitivity are not consulted.

## 3. Apply + report (one shot)
Apply each subject's chosen (mag,pen); read off per-subject TP/FP/sens/prec. Pool across the 8 subjects:
sens = ΣTP/Σref, prec = ΣTP/(ΣTP+ΣFP), F1, FP/day = ΣFP/ΣH·24, with Wilson (sens/prec) & Poisson (FP/day)
95% CIs. Report per-subject table + pooled vector at B = 5, 10, 20. Correct SzCORE ref-event denominator.

## 4. Success criterion (the mandate: all metrics up, not F1 alone)
At the budget B whose pooled FP/day is ≤ the shared mag80/pen5 point (5.6 FP/day), the per-subject vector
must be **Pareto-superior** to the shared point: pooled **sensitivity ≥ 0.395 AND precision ≥ 0.316 AND
F1 ≥ 0.351** (i.e. no axis worse, at least one strictly better), OR clearly better sens+F1 at equal/lower
FP/day. Any lopsided trade (one metric up, another below the shared point) = **not** a win.

## 5. Falsification / honesty
- If per-subject is Pareto-superior at matched FP/day → it becomes the reported primary; shared point kept
  as secondary/robustness.
- If it is not → report as-is; the shared mag80/pen5 stays the SOTA-comparison headline. A per-subject
  approach failing to beat the shared point is reported as a negative result, not reframed.

## 6. Refinement (optional, `.npy`, later)
The grid discretizes `mag` to {40,50,55,60,65,70,75,80}. A continuous per-subject interictal-percentile
threshold (from `ens_seed42_{subj}_inter.npy`) can hit B exactly. Only run if the grid version's pooled
FP/day misses B badly; otherwise the grid version is the reportable number.

*End PREREG_07. Next: run `per_subject_fp_budget.py` (label-free selection → one-shot test at B=5,10,20).*
