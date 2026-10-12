# Claude Code task — scorer: events that run past the end of their file

**Owner:** Project 1 (thesis report). **Written:** 2026-09-30. **Runs at:** repo root `F:/Study/Thesis/Code`.
Edits only `src/eval_application_events.py`. Never writes `web_demo/`.

## Background (from Project 2, read from `web_demo/backend/pipeline_demo.py`, `process_subject_events()`)

- The application runs change point detection once per subject, on all files concatenated in plain
  sorted file-name order (`filenames_sorted = sorted(...)`), with no gap between files.
- Each event belongs to the file that holds its **onset**, in file-relative seconds. `offset_s` is
  `onset + event length` and is **not** clipped. It can therefore exceed the file's length when the
  event continues into the next file, or when merging within 90 s joined a candidate at the end of one
  file with one at the start of the next.
- The last file of a subject cannot overflow.
- The length of a file on the application's timeline is `n_windows × 4` s (from `files.csv`). It can
  differ from the header `duration_s` by up to 4 s.

Today the scorer stops on any event with `offset_s > duration_s`. That must change, by a rule fixed now,
before any real export exists.

## Step 1 — decide the rule by reading the offline scoring, not by any result

Read how the offline evaluation scored events: `src/szcore_eval.py` and the timeline builders it
uses in `src/evaluation_protocol.py`. Answer with file:line:

- Was each test subject scored as **one timeline with its files concatenated**, so that a detection and
  the SzCORE tolerances could run across the boundary between two files? Or was each file scored
  separately?

The rule follows from that answer, so the two evaluations use the same convention:

- **Concatenated offline → split.** The part of an event beyond `L = n_windows × 4` of its file is
  carried to the next file in sorted file-name order, starting at 0 s. Repeat if it also passes the end
  of that file.
- **Per file offline → clip.** The event is cut at `L` and the rest is dropped.

State which rule applies and why, then implement only that rule. Do not implement both, and do not
compare their results.

## Step 2 — implement

- `onset_s` must lie in `[0, L)` of its own file; otherwise stop with `ScorerInputError`, as now.
- `offset_s > L` is allowed only when a next file exists for the subject in `files.csv`; otherwise stop
  with `ScorerInputError`.
- File order for carrying is `sorted()` on `file_name`, the same order the application uses. State that
  it matches.
- The split or clip happens before scoring. The SzCORE merge of detections within 90 s still applies
  inside each file, through the imported `SZ_PARAM`, unchanged.
- Seizure time and the false-alarm denominator are unchanged: they use `duration_s` and the annotation.
- Add to `SUMMARY.md` and print: the number of events that crossed a boundary, per subject, and the total
  seconds moved or dropped.

## Step 3 — smoke tests

Keep the five existing tests. Add a sixth, built from the real annotation of one test subject with a
seizure in the first minutes of a file that is not the subject's first file:

- **Boundary**: one AI event whose onset is 20 s before the end (`L`) of the *previous* file in sorted
  order, and whose `offset_s = onset_s + 20 + (seizure offset)`, so that after carrying it covers that
  seizure.
  - Under split, the expected result is one TP for that seizure.
  - Under clip, the expected result is no TP for that seizure, and the clipped 20 s stub counts as
    one false alarm unless it lies within tolerance of a seizure in the previous file. Check that it
    does not, and choose a pair of files where it does not.
- Also a failing case: an event whose `offset_s > L` in the subject's **last** file must raise
  `ScorerInputError`.

Run `python src/eval_application_events.py --smoke` and paste every verdict line. All tests must pass.

## Step 4 — commit and report

Commit `src/eval_application_events.py` alone. Message:
`Scorer: events crossing a file boundary (<split|clip>, matching the offline convention)`.

Write the report to `F:/Study/Thesis/Agent/cc_reports/SCORER_BOUNDARY.md` and print its path. It must give
the Step 1 answer with file:line, the rule chosen, the smoke-test verdicts and the commit hash.
