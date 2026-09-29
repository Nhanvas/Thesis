# CC_FIX_SCORECACHE_PROMPT.md — persist the ensemble score, then default the filter toggle ON

Source: `CC_CHB06_DIAG_REPORT.md` §6 and `CC_FIX_MINITIMELINE_REPORT.md` §4 (both found
`GET /api/files/{id}/timeline` returning 404 for every file checked). Three tasks, in order; verify
each, then stop. Guards (`test_guards.py`) must stay 4/4 after each task; paste the raw
`pytest -v` output in the report. No `git add` / `commit` / `push`. Do not touch `src/*.py`.

NOTE for anything you read on screen: the Analysis-screen time axes show WALL-CLOCK time
(file `start_time` + offset), not elapsed seconds.

## Task 0 — cache completeness audit (read-only, do first)

For each of the 8 allowlisted subjects, and for every file the DB lists under it, check that
`uploads/{subject}/` contains `{stem}.raw.npy`, `.filtered.npy`, `.bandpass.npy`, `.score.npy`,
`.pernode.npy`, and that `uploads/{subject}/pernode_baseline.npy` exists. Print a table:
subject | files in DB | missing count per artifact type. Report only; fix nothing in this task.

## Task 1 — persist the ensemble score in the live flow, then backfill

Root cause: `{stem}.score.npy` is never written by the live Create-New / Process flow. Only an old
one-time backfill wrote it, for subjects that no longer exist. So
`waveform_serving.get_timeline()` raises `FileNotFoundError` for every subject processed live —
including chb16, the defense live-upload subject and chb13 (re-uploaded).

1a. In `upload_manager._run_process`: after `_finalize_draft_dir` has moved the draft directory
    to `uploads/{project_id}/`, and BEFORE `db.create_subject_with_files`, write each file's
    ensemble score (the `scores` dict already in memory) to
    `uploads/{project_id}/{Path(filename).stem}.score.npy` with `np.save`, keeping the dtype
    `process_subject_phase_b` returns. If a write fails, fail the Process through the existing
    error path — a subject must never appear in the DB without its score cache. Do not change
    what `pipeline_worker.py` or `pipeline_demo.py` output.

1b. New script `backend/backfill_scores.py [subject_id ...]` (no args = all 8). For each subject
    with any missing `.score.npy`:
      - recompute the subject-wide scores exactly as the earlier diagnostic did
        (`pipeline_demo.process_subject_phase_b_from_paths` over every file's `.filtered.npy`;
        the production code path);
      - re-run `process_subject_events` on them and compare with the events stored in the DB:
        every file, every event, onset AND offset must match exactly;
      - only if everything matches, write the missing `.score.npy` files. On any mismatch write
        nothing for that subject and report it.
    Never write to the DB or to any other cache file. Never overwrite an existing `.score.npy`
    (if one exists, compare it with the recomputed array and report the max abs difference).
    Run one subject at a time, single process.

1c. Run it for all subjects. Report before/after counts per subject, the per-subject event-match
    confirmation, and wall-clock.

1d. Verify `GET /api/files/{id}/timeline` returns 200 for at least one file of every subject.
    Then verify live via claude-in-chrome that the Seizure Detection Score line now draws in the
    mini-timeline on chb06_02.edf (the page that contains the event shown as 01:05:10) and on a
    chb16 file. If claude-in-chrome cannot connect, say so explicitly and give the closest
    alternative — never skip verification silently.

## Task 2 — Preprocessed toggle ON by default

Author decision. Change the default of the single Preprocessed toggle from OFF to ON in
`AnalysisScreen.jsx` (`preprocessedOn`). The old "genuinely raw on load" rule existed because the
toggle was mislabeled; the label is now honest, and a filtered view is what the model consumes.
Keep everything else: raw stays drawn, dimmed, underneath ("raw is never fully hidden"); turning
the toggle OFF still shows raw alone. Record a dated SPEC 6.4 note (next free C number) that this
supersedes the "raw on load" default.

Do NOT change the raw dimming or the default amplitude (75 uV). Instead capture screenshots of
chb06_02.edf on the event shown as 01:05:10, with the new default, at 75, 150 and 250 uV (save
under `web_demo/CC_FIX_SCORECACHE_SCREENSHOTS/`), and describe in the report how readable each
is — the author decides about the amplitude default from those.

## Report

Write `CC_FIX_SCORECACHE_REPORT.md`: one section per task with what changed (files and functions),
raw command output for the checks above, and the raw `pytest -v` output. Then stop.
