# Claude Code task — diagnostic: where does the application lose detections?

**Owner:** Project 1 (thesis report). **Written:** 2026-09-30. **Runs at:** repo root `F:/Study/Thesis/Code`.

This task is read-only on `web_demo/`. It writes only `src/diag_application_windows.py` and
`results/application_eval/window_diagnostic.*`. It changes no code or setting of the application and
does not re-run it.

## Why

The application's scored detections on the eight test patients (`results/application_eval/`, commit
`901657e`) are much weaker than the offline result:

| | Sensitivity | Precision | F1 | False alarms per day |
|---|---|---|---|---|
| Application | 0.211 | 0.026 | 0.046 | 52.4 |
| Offline | 0.618 | 0.129 | 0.213 | 27.4 |

Before the report explains this gap, one question must be settled: does the loss arise already at the
window level, or only at the detection stage? The answer also rules out a time-alignment defect. This
is a diagnosis of a result that has already been scored. Nothing is tuned and nothing is re-scored.

## Inputs

- Per-file fused anomaly scores the application computed and cached:
  `web_demo/backend/uploads/{subject}/{stem}.score.npy`.
  - First confirm from `web_demo/backend/pipeline_demo.py` that this array is the fused score, one
    value per 4 s window, with window `i` covering `[4i, 4i+4)` s of the file. Quote the lines.
  - If it is not the fused score, stop and report.
- Annotation: import `evaluation_protocol.parse_summary_edf_list` and read
  `F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary/{subject}-summary.md`.
- The eight test subjects only: chb03, chb06, chb13, chb14, chb15, chb16, chb17, chb18.

## Compute

1. **Window labels.** A window is ictal if its `[4i, 4i+4)` span overlaps an annotated seizure of that
   file. Every window counts. No window is excluded; this is the application's own setting, in which
   every window is kept.
2. **Discrimination per subject.** Compute the AUROC and AUPRC of the fused score against the window
   labels, over all windows of all files of the subject. Also report the macro mean over the eight
   subjects.
3. **Alignment check.** For each subject, recompute the AUROC with the labels shifted by
   k ∈ {−15, −10, −5, −2, −1, 0, +1, +2, +5, +10, +15} windows, where a positive k moves the labels
   later. Report the k that gives the highest AUROC.
   - If the best k is 0 or ±1 for every subject, alignment is correct.
   - Otherwise, flag it plainly as a possible time-alignment defect.
4. **Offline values, for comparison only.** Print them next to the application's values without
   comment. Window AUROC per subject from report Table 3.1: chb03 0.964, chb06 0.501, chb13 0.822,
   chb14 0.698, chb15 0.879, chb16 0.876, chb17 0.782, chb18 0.920; macro 0.805.

## Output and commit

- `results/application_eval/window_diagnostic.csv`, with columns
  `subject,n_windows,n_ictal_windows,auroc,auprc,best_shift_k,auroc_at_best_shift`.
- `results/application_eval/window_diagnostic.md`, containing the same table plus the macro AUROC.
- Commit `src/diag_application_windows.py` and the two result files by explicit path, message
  `Diagnostic: window-level discrimination and alignment of application scores`.
- Write the report to `F:/Study/Thesis/Agent/cc_reports/APP_WINDOW_DIAG.md` and print its path.

The report must also say how many seconds the whole computation took, and must not interpret the gap
beyond the alignment verdict.
