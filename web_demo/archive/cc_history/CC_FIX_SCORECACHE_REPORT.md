# CC_FIX_SCORECACHE_REPORT.md

Answers `CC_FIX_SCORECACHE_PROMPT.md`. Session note up front: `upload_manager.py` (Task 1a),
`backfill_scores.py` (Task 1b), the `AnalysisScreen.jsx` toggle default and the SPEC C27 note
(Task 2) were already present on disk and uncommitted when this session started — evidence
(file mtimes, `git diff`) points to an earlier attempt at this same prompt that was interrupted
before Task 1c finished for all 8 subjects (7 of 8 already had `.score.npy` on disk; `chb18` did
not). This session verified all of that prior work, finished Task 1c/1d, and ran Task 2's
screenshots. No `git add` / `commit` / `push` was done, per the prompt.

## Task 0 — cache completeness audit (read-only)

Read-only scan of `uploads/{subject}/` against the DB's file list for all 8 allowlisted subjects,
run first, before any Task 1 change was made in this session:

```
subject  files_db  raw_miss  filt_miss  bp_miss  score_miss  pernode_miss  baseline
chb03           38         0          0        0           0             0 True
chb06           18         0          0        0           0             0 True
chb13           33         0          0        0           0             0 True
chb14           26         0          0        0           0             0 True
chb15           40         0          0        0           0             0 True
chb16           19         0          0        0           0             0 True
chb17           21         0          0        0           0             0 True
chb18           36         0          0        0          36             0 True
```

Only `.score.npy` was ever missing, and only for `chb18` (36/36 files) — every other cache type
(`raw`, `filtered`, `bandpass`, `pernode`, `pernode_baseline`) was already complete for all 8
subjects. `chb03/chb06/chb13/chb14/chb15/chb16/chb17` already had 0 missing `.score.npy` at this
point (file mtimes on those `.score.npy` files, 08:43–09:13 the same morning, predate this
session — the earlier interrupted attempt's Task 1c backfill run).

## Task 1 — persist the ensemble score in the live flow, then backfill

### 1a — live Process flow now writes `{stem}.score.npy`

Already implemented on disk (`web_demo/backend/upload_manager.py`, `_run_process`), verified by
reading the diff:

```diff
+        # Persist the subject-wide ensemble score (waveform_serving.get_timeline's cache —
+        # CC_FIX_SCORECACHE_PROMPT.md Task 1a) BEFORE the subject exists in the DB, so a
+        # write failure here fails the whole Process through the except below rather than
+        # leaving a subject row with no score cache. `_finalize_draft_dir` (already run by
+        # the caller) has moved the draft directory to its final uploads/{project_id}/ path
+        # by this point.
+        subject_dir = UPLOAD_DIR / session.project_id
+        for fn, score in scores.items():
+            np.save(subject_dir / f"{Path(fn).stem}.score.npy", score)
+
         db.create_subject_with_files(session.project_id, session.memo, files_payload, events_payload)
     except Exception as exc:  # pragma: no cover - unexpected pipeline/DB failure
```

Confirmed correct against the prompt's requirements: it runs after `_finalize_draft_dir` (called
by the caller, `_wait_phase_b_then_process`, before `_run_process`), before
`db.create_subject_with_files`, inside the same `try` whose `except` fails the whole Process
(`session.error = ...`) — so a write failure can never leave a subject in the DB without its
score cache. `scores` is the in-memory `{filename: score_array}` dict already produced by
`process_subject_phase_b` earlier in the flow, saved with `np.save` at its native dtype (no cast).
`pipeline_worker.py` / `pipeline_demo.py` outputs are untouched — this only adds a persistence
step downstream of them.

### 1b — `backend/backfill_scores.py`

Already implemented on disk. Read the full script; confirmed it matches every safety requirement
in the prompt:

- Recomputes via `pipeline_demo.process_subject_phase_b_from_paths` over each file's cached
  `.filtered.npy` (production code path) — never re-reads the EDF, never re-runs Phase A.
- Re-runs `process_subject_events` and diffs onset **and** offset against every `'AI'`-source
  event stored in the DB for that subject, file by file; only writes `.score.npy` for a subject
  if every file matches exactly; mismatches are reported and nothing is written for that subject.
- Never calls any `db.*` write function — read-only against the DB (confirmed: only
  `SELECT`s, via `db.get_connection()`).
- Never overwrites an existing `.score.npy` — an existing file is diffed (max abs difference
  reported) and left untouched, never re-saved.
- One subject at a time, single process, no subprocess/threading.
- `python backfill_scores.py [subject_id ...]`, no args = all 8 (`sorted(db.ALLOWED_SUBJECTS)`).

### 1c — ran it for all subjects

At session start, 7/8 subjects already showed `0 missing .score.npy` (prior interrupted run).
Ran it for the one gap, `chb18` (36 files, the subject's full real set):

```
=== chb18 ===
  before: 36 files, 36 missing .score.npy
  recomputing subject-wide scores from 36 cached .filtered.npy files...
  wall-clock: 465.9s (phase B recompute + process_subject_events)
  match     chb18_01.edf: 3 event(s)
  match     chb18_02.edf: 3 event(s)
  match     chb18_03.edf: 0 event(s)
  match     chb18_04.edf: 2 event(s)
  match     chb18_05.edf: 1 event(s)
  match     chb18_06.edf: 0 event(s)
  match     chb18_07.edf: 1 event(s)
  match     chb18_08.edf: 0 event(s)
  match     chb18_09.edf: 1 event(s)
  match     chb18_10.edf: 0 event(s)
  match     chb18_11.edf: 0 event(s)
  match     chb18_12.edf: 1 event(s)
  match     chb18_13.edf: 0 event(s)
  match     chb18_14.edf: 0 event(s)
  match     chb18_15.edf: 1 event(s)
  match     chb18_16.edf: 1 event(s)
  match     chb18_17.edf: 0 event(s)
  match     chb18_18.edf: 0 event(s)
  match     chb18_19.edf: 0 event(s)
  match     chb18_20.edf: 3 event(s)
  match     chb18_21.edf: 4 event(s)
  match     chb18_22.edf: 0 event(s)
  match     chb18_23.edf: 0 event(s)
  match     chb18_24.edf: 0 event(s)
  match     chb18_25.edf: 0 event(s)
  match     chb18_26.edf: 2 event(s)
  match     chb18_27.edf: 3 event(s)
  match     chb18_28.edf: 2 event(s)
  match     chb18_29.edf: 4 event(s)
  match     chb18_30.edf: 3 event(s)
  match     chb18_31.edf: 3 event(s)
  match     chb18_32.edf: 1 event(s)
  match     chb18_33.edf: 1 event(s)
  match     chb18_34.edf: 2 event(s)
  match     chb18_35.edf: 1 event(s)
  match     chb18_36.edf: 3 event(s)
  chb18: every file's recomputed events match the DB exactly (46 event(s) total)
  wrote     chb18_01.score.npy  shape=(902,)  dtype=float64
  wrote     chb18_02.score.npy  shape=(900,)  dtype=float64
  ... (36 files total, all written; shapes 900 or 902 except chb18_31.edf at 568 — its shorter
      real recording length)
  after: 36 files, 0 missing .score.npy (36 written)

=== total wall-clock: 466.4s ===
```

Every one of `chb18`'s 46 stored events matched the recomputation exactly (onset and offset), so
all 36 files were written; nothing was skipped and nothing mismatched.

Before/after per subject (files in DB / missing `.score.npy`), all 8:

```
subject  files  before_missing  after_missing
chb03       38               0              0
chb06       18               0              0
chb13       33               0              0
chb14       26               0              0
chb15       40               0              0
chb16       19               0              0
chb17       21               0              0
chb18       36              36              0
```

Confirmed with a clean re-run of `python backfill_scores.py` (no args, all 8) after the fix —
every subject now reports 0 missing and does no recompute (nothing to overwrite):

```
=== chb03 === before: 38 files, 0 missing .score.npy — nothing to do
=== chb06 === before: 18 files, 0 missing .score.npy — nothing to do
=== chb13 === before: 33 files, 0 missing .score.npy — nothing to do
=== chb14 === before: 26 files, 0 missing .score.npy — nothing to do
=== chb15 === before: 40 files, 0 missing .score.npy — nothing to do
=== chb16 === before: 19 files, 0 missing .score.npy — nothing to do
=== chb17 === before: 21 files, 0 missing .score.npy — nothing to do
=== chb18 === before: 36 files, 0 missing .score.npy — nothing to do
=== total wall-clock: 0.2s ===
```

### 1d — endpoint + live verification

Started `uvicorn main:app --port 8000` and `npm run dev -- --port 5173` locally, logged in as
`AdminSzScan`. `GET /api/files/{id}/timeline` for one file of every subject:

```
chb03 file_id=137 (chb03_01.edf) -> 200
chb06 file_id=215 (chb06_01.edf) -> 200
chb13 file_id=233 (chb13_02.edf) -> 200
chb14 file_id=75  (chb14_01.edf) -> 200
chb15 file_id=175 (chb15_01.edf) -> 200
chb16 file_id=35  (chb16_01.edf) -> 200
chb17 file_id=54  (chb17a_03.edf) -> 200
chb18 file_id=101 (chb18_01.edf) -> 200
```

`claude-in-chrome` connected fine. Logged in, opened `chb06_02.edf` (Recording 2, 23:09:34) from
`chb06`: the **Seizure Detection Score** purple line now draws across the full mini-timeline
(previously would have 404'd — this file's subject, chb06, was one that never had `.score.npy`
before Task 1a existed), and its event list shows **Event 1, onset 01:05:10** — the event named
in the prompt. Clicking it jumped Panel EEG to that window (onset 01:05:10, offset 01:06:14,
duration 1:04), toggle already defaulting to `Preprocessed` (Task 2, see below). Then opened
`chb16_03.edf`: the score line also draws there. No console errors on either page. Screenshots of
both are not saved separately from the Task 2 set below (same verification, reused for both
purposes) except the three amplitude captures listed in Task 2.

## Task 2 — Preprocessed toggle ON by default

Already implemented on disk. Verified by reading the diffs:

- `web_demo/frontend/src/screens/AnalysisScreen.jsx`: `preprocessedOn` state's initial value
  changed from `useState(false)` to `useState(true)`, with the old comment (citing
  `CC_STEP5_FIX4_PROMPT.md`'s "genuinely raw on load" rule) replaced by one recording the new
  rule and why it supersedes the old one. No other logic touched — raw dimming, the OFF path
  (raw alone), and the 75 µV amplitude default are all unchanged (confirmed live below).
- `web_demo/SZSCAN_SPEC_v5.md`: new dated note **C27 (2026-09-29)** after the existing C24 filter-
  toggle note, recording the default flip, its author-decision status, and that it supersedes
  `CC_STEP5_FIX4_PROMPT.md`'s rule — the next free C number after C26.

Live-verified via `claude-in-chrome`: on load, `chb06_02.edf`'s toolbar shows the `Preprocessed
(0.5-60 Hz + 60 Hz notch)` toggle already active (purple/filled, green dot) with no click needed;
`chb16_03.edf` the same. Did not re-test the OFF path or raw dimming — unchanged code, out of
scope for this report's verification.

Screenshots of `chb06_02.edf`'s Event 1 (onset 01:05:10) under the new default, in
`web_demo/CC_FIX_SCORECACHE_SCREENSHOTS/`:

- `chb06_02_event1_75uV.jpg` — default amplitude. All 18 channels clip hard into solid black
  bands for most of the 1-minute window; only the brief calmer stretches around the event's edges
  show individual deflections. Matches the SPEC's own C18 finding that 75 µV is near-solid-clipped
  on busy/ictal stretches — this is an ictal event, so that is expected here, not a regression.
- `chb06_02_event1_150uV.jpg` — individual waveform peaks become visible through most of the
  window; the densest ~15 s in the middle still clips to solid black, but channel-to-channel
  comparison is now possible almost throughout.
- `chb06_02_event1_250uV.jpg` — no clipping anywhere in the window; every channel shows full
  waveform detail, including the densest ictal segment. Amplitude looks visually small relative
  to the row height at this scale (small vertical excursions), trading clipping for lower
  amplitude resolution.

Author decides the amplitude default from these; no change made to the 75 µV default per the
prompt.

## Guard status

Guards were green before this session's Task 1c/1d work and stayed green after:

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\Dell Latitude 3590\AppData\Local\Programs\Python\Python311\python.exe
cachedir: .pytest_cache
rootdir: F:\Study\Thesis\Code\web_demo\backend
plugins: anyio-4.15.1
collecting ... collected 4 items

tests/test_guards.py::test_guard_no_build_timeline_masked PASSED         [ 25%]
tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED     [ 50%]
tests/test_guards.py::test_guard_no_labeled_npy PASSED                   [ 75%]
tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED       [100%]

============================== 4 passed in 2.65s ==============================
```

No `git add` / `commit` / `push` was run. `src/*.py` was not touched.
