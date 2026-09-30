# CC_PROMPT_GAP_DIAGNOSTIC.md — why the application scores 0.211 / 52.4 where the thesis scores 0.618 / 27.4

Owner: thesis side (this reads the annotation, so everything lives in `src/` and `results/`, never in
`web_demo/`). Run from the repo root `F:/Study/Thesis/Code`. Read-only diagnostic: **nothing is tuned,
no setting of the application or the thesis pipeline is changed, the application is not re-run.** The
test patients are used only to explain an already-scored result; no number produced here may be used
to choose a parameter.

## Ground rules

1. Gate first: `python src/verify_provenance.py | grep -a -i verdict` must print `VERDICT: PASS`.
2. Read before you build. Open and read, in full, the code paths named below before writing anything:
   `src/szcore_eval.py` (`build_timeline_masked`, lines ~90–125), `src/dataprep/preprocessing.py`
   (`build_buffer_mask`, `compute_subject_stats`, `count_windows`, `write_windows`, `build_labels`,
   `ARTIFACT_SD_MULTIPLIER`, `STATS_SUBSAMPLE`), `src/cpd_pipeline_v14.py` (`detect_events`,
   `detect_changepoints`, `_robust_variance`), and the script that produced
   `results/phaseB/tier2/rlg_test/final_eval_seed42.csv` (find it with grep; do not guess).
   **Reuse these functions. Do not re-implement a rule from memory or from this prompt.**
3. Application inputs: `web_demo/backend/uploads/{subj}/{stem}.score.npy` (fused score, one value per
   4 s window, window i = [4i, 4i+4) s of its file, confirmed in `APP_WINDOW_DIAG` Step 1),
   `web_demo/report_handback/tier2/{subj}_events.csv`, `web_demo/report_handback/tier2/files.csv`.
   Offline inputs: the committed `ens_seed42_{subj}_{inter,ictal}.npy` arrays (locate via
   `docs/REPO_MAP.md`).
4. New script: `src/diag_application_gap.py`, with the usual `sys.path` block and a comment stating it
   is a post-hoc diagnostic on already-scored test output. Outputs to
   `results/application_eval/gap_diagnostic/`. Fail fast with a diagnostic message.
5. Tolerances match the precision of what is compared (instructions §6 rule 19).
6. Commit only `src/diag_application_gap.py` and `results/application_eval/gap_diagnostic/`, explicit
   paths, inside `bash -e <<'EOF' … EOF`. Message: `Diagnostic: application vs offline gap`.

## D0 — reproduce, then reconcile the offline timeline length

a. Re-run the offline scoring path on the committed offline arrays at `mag_pct = 50`, `pen_mult = 2.0`
   and confirm it reproduces the pooled row exactly: TP 47, FN 29, FP 318, sensitivity 0.618,
   precision 0.129, F1 0.213, 27.4 FA/day. **Stop and report if it does not.**
b. For each test patient report: number of timeline positions built by `build_timeline_masked`, the
   number of real 4 s windows in the patient's EDFs (sum over files of floor(n_samples / 1024)), and
   the hours used as the FA/day denominator. `results/diagnostics/timeline_composition.csv` gives
   212,675 positions in total (236.3 h) against 251,445 real windows (279.4 h), while the denominator is
   278.2 h. Explain from the code which windows the timeline leaves out, and whether false alarms can
   occur in the time the timeline does not contain. Report FA/day recomputed with the timeline's own
   duration minus seizure time as the denominator, beside the reported value.

## D1 — is the application computing the same scores at the same times? (defect check)

For each test patient, using the thesis's own `build_labels` rule for which windows are ictal:
a. Count the ictal windows in the application's continuous scores (files in the offline file order).
   The count must equal `len(ens_seed42_{subj}_ictal.npy)`. Report both.
b. Spearman correlation between the application's fused scores at those ictal windows and the offline
   ictal array, in order, at lags k = −15 … +15 windows (shift the application side within each file).
c. Using `build_buffer_mask` and the artifact rule exactly as preprocessing applies them, reconstruct
   the retained interictal windows on the application side; their count must equal
   `len(ens_seed42_{subj}_inter.npy)`. Report both, and the Spearman correlation in order at k = 0.

**Pre-registered criterion.** D1 passes if, for every patient, both counts match and the ictal Spearman
peaks at k = 0 with ρ ≥ 0.80. Fused scores are not expected to be identical, because the application
standardizes over the whole recording; they are expected to rank alike. If D1 fails for any patient,
**stop after D1** and report it as a possible application defect.

## D2 — window discrimination on the same windows as the offline evaluation

Per patient, AUROC of the application's fused score with ictal windows as positives and, as negatives:
(i) every non-ictal window (reproduces `APP_WINDOW_DIAG`, macro 0.633); (ii) only the retained
interictal windows of D1c (the offline negative set); (iii) every non-ictal window except the
post-seizure buffer; (iv) every non-ictal window except artifact-rejected ones. Report the macro over
the eight patients for each, beside the offline 0.805.

**Pre-registered reading.** If (ii) is within 0.05 of 0.805, the window-level gap is explained by which
windows are counted, not by the application's scores.

## D3 — the application's own scores through the offline harness

Build `inter` and `ictal` arrays from the application's scores exactly as D1 defined them (retained
interictal windows in order, ictal windows in order) and run them through the **same** offline path as
D0a, at `mag_pct = 50`, `pen_mult = 2.0`, same seed for the resampling. Report per patient and pooled:
TP, FN, FP, sensitivity, precision, F1, FA/day. Beside it, the application's continuous result
(`results/application_eval/per_subject.csv`) and the offline result.

**Pre-registered reading.** If D3 pooled sensitivity ≥ 0.50 and FA/day ≤ 35, the gap between Table 9
and Table 13 is produced by the evaluation timeline, not by the application.

## D4 — where the offline detections happen on the reconstructed timeline

For the offline run of D0a, locate on each patient's timeline the point where the stored interictal
array is exhausted (everything after it is resampled). Report, pooled and per patient: seizures before
and after that point with the number detected in each; false alarms before and after it, per hour of
timeline in each part; and the fraction of each seizure's surrounding ±15 minutes that is resampled.
Also report the standard deviation of the 15-window smoothed score over (a) runs of real stored
interictal scores and (b) runs of resampled scores, per patient.

## Output

`results/application_eval/gap_diagnostic/SUMMARY.md` with one table per step, the D0a reproduction
line first, and a closing line per step stating whether its pre-registered criterion was met. No
interpretation beyond those lines. Also `d0.csv … d4.csv`.
Report computation time. Do not open, edit or commit anything in `web_demo/`.
