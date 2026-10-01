# CC_PROMPT_CONTINUOUS_EVAL.md — evaluate the thesis pipeline on the true continuous timeline

**Start condition (amended 2026-09-30, after the gap diagnostic's D1).** Run only in the single Claude
Code session, after the gap-diagnostic run has been stopped and its D0/D1 output committed. D1 found
every ictal and interictal window count equal and the correlation peaking at lag 0 on all eight test
patients (no timing offset), but chb13 missed the pre-registered ictal criterion (ρ = 0.787 < 0.80).
That failure stands as recorded. Gates G1 and G2 below are the test that locates it: G2 compares the
thesis-scope continuous scores with the committed offline arrays, so if G2 passes for chb13 the lower
correlation comes from the declared whole-recording fit, and if G2 fails the computation itself differs
and this run stops there.

Pre-registered 2026-09-30, before any result of this evaluation exists. Thesis side: reads the
annotation, so code goes in `src/`, outputs in `results/continuous_eval/`, nothing in `web_demo/`.

## Why

The offline event evaluation (Table 9: 0.618 / 0.129 / 0.213 / 27.4) was scored on a timeline rebuilt
from the annotation, in which artifact and post-seizure windows are removed and about half of all
positions carry resampled interictal scores. The application (Table 13) was scored on the real continuous
recording. The two differ in the timeline **and** in the fitting scope of the statistics, so their
difference cannot be attributed. This evaluation removes the first difference: the locked thesis
pipeline, unchanged, is run on the real continuous timeline, keeping every window, with two fitting
scopes. Nothing is tuned on the test patients.

## Ground rules

Gate `python src/verify_provenance.py` → PASS. Read and reuse the existing code paths
(`src/dataprep/preprocessing.py`, `graph_construction.py`, `feature_extraction.py`,
`compute_gamma_aec.py`, the GAE scoring used for the committed arrays, `ensemble_recipe.py`,
`cpd_pipeline_v14.py`, `szcore_eval.py` scoring only, `evaluation_protocol.parse_summary_edf_list`).
`web_demo/backend/pipeline_demo.py` may be **read** to see how the continuous computation was done;
it is not edited. Never call `build_timeline_masked`. Smoke first: one validation file, then one
validation patient, then all. Cache every expensive intermediate so the second scope does not recompute
connectivity. Commit only explicit paths.

## Execution rules (added after review of the plan)

1. **Order:** Step 0 first. Write `results/continuous_eval/step0.csv` and print its pooled line, then
   continue without waiting for a reply.
2. **Checkpoint to disk, per patient and per step.** Scores per scope per file (`.npy`), gate results,
   the change points per penalty, and every scored grid row go to `results/continuous_eval/cache/` and
   `results/continuous_eval/*.csv` as soon as each patient finishes. On restart, skip whatever is already
   on disk. Nothing is kept only in memory.
3. **Grid cost:** PELT depends only on the penalty. Per patient and scope, run PELT once per penalty
   multiplier (6 runs), store the change points, then apply the 8 magnitude percentiles and the 2 merge
   gaps as post-processing on those stored change points. Verify on one validation patient that this
   gives the same events as calling `detect_events` directly, before using it.
4. **Log:** all progress to `results/continuous_eval/run.log` with `flush=True`, one line per patient per
   step, prefixed `[S0]`, `[G1]`, `[G2]`, `[A]`, `[B]`, `[C]`, so progress can be followed with `grep`.
5. Print an estimated finish time after the first validation patient.

## Step 0 — exact correction of the committed offline result (no new scores, minutes)

Code review 2026-09-30 found that `szcore_eval.cps_to_events` drops every change point at a position
with `is_buffer = True` unless it is within tolerance of a seizure, and that `build_timeline_masked`
sets `is_buffer = True` both on the 4 h post-seizure buffer **and on every position after the stored
interictal array is exhausted** (53.9 % of positions on average), while `n_inter_h` counts all
non-ictal positions. False alarms can therefore only be counted in the real-interictal part of the
timeline, but are divided by the whole. For the committed offline run at 50 / 2.0 (seed as in D0a),
report per patient and pooled: FP, hours of `real_inter` positions, hours of all non-ictal positions,
FA/day on each denominator, and the number of change points that were dropped by the `is_buffer` rule
(away from seizures). An estimate from the committed CSV and `timeline_composition.csv` gives 61.5 FA/day
pooled on the real part against the reported 27.4; this step replaces the estimate with the exact value.

## Fitting scopes

- **Scope T (thesis):** per-subject z-score statistics, LedoitWolf covariance, per-branch median/MAD and
  the CPD penalty variance and magnitude-filter background are fitted on the windows the thesis uses as
  background: not ictal, not within the post-seizure buffer, not artifact-rejected, using the thesis's
  own functions. **Every window stays on the timeline and is scored**; the mask only decides what is
  fitted, and is passed to `detect_events` as `inter_mask`.
- **Scope W (application):** the same, fitted on every window (no mask), `inter_mask = None`.

Timeline per patient: files in file-name order, concatenated, window i = [4i, 4i+4) s of its file,
exactly as the application does.

## Gates before any test number

G1. Scope W continuous fused scores reproduce the application's `{stem}.score.npy` on all 231 test
files: Pearson ≥ 0.999 per file. Stop and report if not.
G2. Scope T scores at the retained interictal and ictal windows rank-match the committed offline arrays
`ens_seed42_{subj}_{inter,ictal}.npy` (Spearman ≥ 0.99 per patient, counts equal). Stop and report if
not.

## Step A — validation patients chb10, chb11, chb22 (operating point)

For each scope, run the 48-point grid (8 magnitude percentiles × 6 penalty multipliers, the same grid as
the thesis) crossed with two event-merge gaps, `merge_s` ∈ {90, 300} (pre-registered here; 300 s lets the
post-ictal return of the score join the seizure's own event instead of becoming a separate alarm, and
stays within SzCORE's 5-minute split), on the continuous timeline, score every detection with SzCORE
(no position is exempt from false alarms), and select the operating point by **the same rule as the
thesis**: pooled sensitivity and precision closest to equal. Also report the best point with FA/day ≤ 25,
if any, for information only. Record the selected point per
scope. Also report both scopes at 50 / 2.0. Denominator: recorded time minus seizure time.

## Step B — test patients, once per scope

At the scope's own validation-selected operating point (including its `merge_s`), and separately at 50 / 2.0 with `merge_s` 90, score the eight test
patients: per patient and pooled TP, FN, FP, sensitivity, precision, F1, FA/day, and window-level macro
AUROC over every window. Denominator: recorded time of the 231 files minus seizure time. No other grid
point on the test patients is reported, and no parameter is changed after Step B is seen.

## Step C — results of record for the report (Scope T is the thesis result, Scope W the application)

These continuous results replace the reconstructed-timeline event results as the thesis's event-level
results. Write, for Scope T at its validation-selected point and for Scope W at its own:
per-patient table (seizures, detected, false alarms, sensitivity, precision, F1, FA/day), pooled row,
latency distribution of matched seizures, window-level macro AUROC over every window. For the
operating-curve figure only, also compute the full test grid for Scope T and mark in the file that it
is post-hoc and was not used for any selection (as the thesis already does for its curve). Save
everything under `results/continuous_eval/` with a `README.md` naming the producing script.

## Pre-registered expectations (written before the run)

E1. Scope T continuous sensitivity is below 0.618 and FA/day above 27.4.
E2. The Scope T − Scope W difference is small compared with the gap between the offline and application
results, i.e. most of that gap comes from the timeline, not from the label-free fitting.
Either expectation failing is reported as such, not explained away.

## Output

`results/continuous_eval/SUMMARY.md`: gates G1, G2; Step A table with the selected point per scope;
Step B table: rows = offline reconstructed (Table 9, copied), Scope T continuous, Scope W continuous
(its 50 / 2.0 row must equal the application's Table 13: stop and report if not); columns as above.
Closing lines: E1 met or not, E2 met or not. No other interpretation. Report wall-clock time.

## Amendment A1 (2026-09-30, before Step A)

G2 gates Scope T; G1 gates Scope W only. If G2 passes and G1 fails, Steps A, B and C run for Scope T
in full; Scope W is still computed and reported in a separate table marked "G1 failed — not used to
set the application's operating point", and no Scope W operating point is proposed. G1 results are
reported per file, with the files grouped by subject.

## Correction C1 (2026-10-01, before Step A)

"Fitting scopes" defines Scope T as the locked thesis pipeline, unchanged. The locked pipeline filters
every window independently with preprocessing.filter_window (4 s window plus FILTER_PAD on each side,
as in write_windows). Scope T must use exactly that for the scored signal; Scope W keeps whole-file
filtering (the application's convention).

## Amendment A2 (2026-10-01, before Step A)

Signal-loss rule: a window is flagged as signal loss when the standard deviation of the raw
(unfiltered) signal is below 1e-10 V on every one of the 18 channels; the threshold is fixed, not
tuned (real EEG ~1e-5 V, flat ~1e-22 V). It uses no annotation. In both scopes, flagged windows (a)
are excluded from every fit — robust-z median and MAD, LedoitWolf covariance, CPD penalty variance
and magnitude-filter background; (b) keep their place on the timeline with fused score set to 0, the
robust-z median, so they cannot create change points on their own; (c) are excluded from the FA/day
denominator, with the excluded hours reported per subject. Scope T's per-subject z-score statistics
stay those committed in data/processed. G2 is evaluated on windows not flagged, since the score of a
flagged window is numerically undefined in both computations; the per-subject number of flagged
windows is reported beside G2. Thresholds of G1 and G2 unchanged. The same rule will be added to the
application before its next run.

## Amendment A3 (before Step A; reorders and drops, changes no computation of the thesis result)

Scope W is computed through G1 only; Scope W Steps A, B and C are dropped, because the application's
operating point will be selected on the application's own output for the validation patients, and its
test result comes from the application's own rerun. Order after the gates: Step A for Scope T; then
Step B for Scope T at its selected point and at 50 / 2.0 with merge 90, running PELT only for the
penalties those two points need; then write SUMMARY.md immediately; then Step C, with the full Scope T
test grid for the curve as the last task.
