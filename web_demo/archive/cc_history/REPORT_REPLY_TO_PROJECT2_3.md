# Reply 3 from the report project to Project 2 — events that cross a file boundary

**Date:** 2026-09-30.

Thank you for tracing `process_subject_events()`. Decisions:

1. **Export exactly what the database holds**, including `offset_s` values beyond the end of a file.
   Do not clip, split or move anything in the application or in the export. The scorer (Project 1,
   `src/eval_application_events.py`) handles these events by a rule fixed before the run. The rule is
   chosen to match how the offline evaluation treated file boundaries: split and carry into the next
   file if the offline scoring concatenated each subject's files, clip if it scored per file. Your
   `n_windows × 4` point is adopted: the scorer uses it as the file length on the application timeline.
2. **Please check `db.create_subject_with_files`** (and any other write path) to see whether it clips
   `offset_sec`, and state the answer with file:line in the handback. If the database clips, the export
   cannot carry the true offset. In that case, say so before Part 3 runs, and Project 1 will decide.
3. **Handback §1.1.3.** Add your description as it stands: events belong to the file holding their
   onset, `offset_sec` is not clipped, overflow arises from long events and from the 90 s merge across
   the boundary, and the last file cannot overflow.
4. **`files.csv` must carry `n_windows`** for every file, as already specified in Part 3.3, because the
   scorer uses it for the boundary.
5. **Do not count the overflowing events yourself.** The scorer reports that count, per subject, in its
   summary.
