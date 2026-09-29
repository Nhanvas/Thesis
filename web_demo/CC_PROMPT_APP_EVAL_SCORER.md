# Claude Code task — score the application's exported detections against the annotation

**Owner:** Project 1 (thesis report). **Written:** 2026-09-29. **Runs at:** repo root `F:/Study/Thesis/Code`.
Read `CLAUDE.md` at the repo root if it exists. This task writes **only** under `src/` and
`results/application_eval/`, never under `web_demo/`.

## Why this exists

The report evaluates the SzScan application's own detections on the eight test patients against the
seizure annotation, with the same event-based scorer as the offline results (report §3.5.2, Table 3.7).
The application itself never reads the annotation. The comparison happens here, outside it, on the
intervals it exports. Rules fixed before the run (project instructions §11.5):

1. Every AI event the application produced counts, before review. Rows with `source == "Human"` are
   dropped; `review_status` is ignored.
2. The false-alarm denominator is the recorded time of the processed files minus the seizure time in
   those files. It is **not** the 278.2 background hours of the offline evaluation.
3. The result is never merged with the offline numbers.
4. The run is one-shot. If a defect is found after scoring, the whole application run is repeated with a
   fixed build and scored again; no single subject is re-scored selectively.

## Inputs

- `web_demo/report_handback/tier2/{subject}_events.csv`, one per test subject, columns
  `subject,file_name,event_id,onset_s,offset_s,source,review_status`. `onset_s` and `offset_s` are
  seconds relative to the start of that EDF file.
- `web_demo/report_handback/tier2/files.csv`, columns `subject,file_name,duration_s,n_windows,status`.
- The seizure annotation: `F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary/chbNN-summary.md`. Note the
  extension is `.md`, not `.txt`.
- Test subjects only: chb03, chb06, chb13, chb14, chb15, chb16, chb17, chb18.

## Step 1 — read before writing

- Read `src/szcore_eval.py` in full. Find:
  - the function that parses seizure onsets and offsets per file from a summary file;
  - the `timescoring` event-scoring call and its parameters (tolerances of 30 s before onset and 60 s
    after offset, merging of detections within 90 s, splitting of events longer than 5 min).
  **Reuse them by import. Do not retype the parameters.** If the parser or the parameters are not
  importable as they stand, stop and report which lines would need to change. Do not change
  `szcore_eval.py` yourself.
- Do **not** use `build_timeline_masked()`. It reconstructs a timeline for the offline arrays and has no
  place here.
- Read `docs/REPO_MAP.md` §7 (Traps) and report anything that bears on this task.

## Step 2 — write `src/eval_application_events.py`

- Include the explicit `sys.path` block used by other scripts in `src/`, and a TEST guard: refuse any
  subject outside the eight test subjects.
- Score **per file**: the reference is that file's annotated seizures in file-relative seconds, and the
  hypothesis is that file's AI events. Accumulate TP, FP and the number of reference seizures across
  files and subjects. Report per subject and pooled over all eight:
  - sensitivity = matched seizures / annotated seizures;
  - precision = TP / (TP + FP);
  - F1;
  - false alarms per day = FP / ((Σ duration_s − Σ seizure seconds) / 86400).
  When precision and sensitivity are both zero, F1 is "undefined", not 0.
- Coverage checks, printed and written to the summary:
  - list every EDF in `F:/Study/Thesis/Dataset/CHB-MIT/{subject}/` against `files.csv`, and flag any
    file on disk that was not processed, and any `status` other than success;
  - count the annotated seizures in processed files per subject. The full test set holds
    7, 10, 12, 8, 20, 10, 3, 6 (76 in total) for chb03, chb06, chb13, chb14, chb15, chb16, chb17, chb18.
    Flag any shortfall and name the file that holds the missing seizure;
  - total processed hours against the 279.39 recorded hours of the test set (report Table 2.1).
- Fail fast, with a clear message, on: missing columns, `offset_s <= onset_s`, an event outside
  `[0, duration_s]` of its file, a `file_name` absent from `files.csv`, or any calendar date in the exports.
- Outputs:
  - `results/application_eval/per_subject.csv`: subject, files, hours, seizures, detected, false alarms,
    sensitivity, precision, F1, false alarms per day;
  - `results/application_eval/pooled.json`;
  - `results/application_eval/SUMMARY.md`, holding the table, the coverage checks, the input file hashes
    (sha256 of each export) and the git commit of the application build if `REPORT_HANDBACK.md` states it.
  If `results/application_eval/` already holds results, stop and ask. Never overwrite silently.

## Step 3 — prove the scorer before real data (smoke first)

Build synthetic exports in a temporary directory, never in `web_demo/`, from the annotation and
`files.csv`, and run the scorer on each:

| Synthetic export | Expected |
|---|---|
| Oracle: one AI event per annotated seizure, exactly its onset and offset | sensitivity 1.000, precision 1.000, false alarms 0 |
| Empty: no events | sensitivity 0.000, false alarms 0, F1 undefined |
| Displaced: each oracle event moved into a seizure-free stretch of the same file, at least 10 min from any seizure | sensitivity 0.000, false alarms = number of events |
| Human-only: oracle events with `source = Human` | identical to Empty |

All four must pass before the real exports are scored. Report the four results. If `files.csv` does not
exist yet, build a synthetic one from the EDF headers (duration only) for this step and say so.

## Step 4 — real run, only when the real exports exist

Run once on the real exports. Print the per-subject table and the pooled row. Do **not** compare them
with the offline numbers or comment on them; that belongs to the report.

## Step 5 — commit

In one `bash -e` block, stage explicit paths only: `src/eval_application_events.py` and, after the real
run, `results/application_eval/`. Never `git add .`. The working tree holds unrelated `web_demo/` edits.
Commit message: `Scorer for application detections; results` (or `…; smoke tests only` before the real
run).

## Report back

A short report with: the reused functions and parameters (file:line); the four smoke-test results; the
coverage checks; the per-subject table and pooled row; the commit hash.
