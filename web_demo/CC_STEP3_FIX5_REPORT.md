# CC_STEP3_FIX5_REPORT.md — Step 3 closeout: A1/A2 verification + C17 (Recording N display)

Scope: `web_demo/CC_STEP3_FIX5_PROMPT.md`. Part A found both items already correctly implemented
(no bug, no code change needed) — proven live in a real Chrome browser via `claude-in-chrome`. Part B
(C17) required one backend change, confined to `web_demo/backend/db.py`.

**Note on the browser session:** the `claude-in-chrome` extension was disconnected for the first part
of this round. Per the author's direction I did Part B (no browser needed) first, then reconnected and
completed all of Part A's live-browser verification below — nothing in this report is API-only.

---

## Part A1 — malformed/wrong-channel upload rejection

**Already correctly implemented — no bug found, no code changed.** `pipeline_demo.py`'s
`process_file_phase_a()` wraps `preprocessing.open_edf()` in a try/except and raises
`UnsupportedEdfError` both when the file can't be parsed as EDF at all and when it opens but is
missing one of the 18 common channels; `upload_manager.py::_run_phase_a` catches that and sets the
file's `error` to the exact spec string via `REJECTED_FILE_MESSAGE`. The frontend's
`CreateNewPanel.jsx` shows this as a full-panel takeover (the `erroredFile?.error` branch) with an
"Upload Another File" button, matching `UI/A1b`'s layout.

**Live browser proof:** built a corrupted/truncated EDF by taking the first 300 bytes of a real
`chb03_01.edf` (valid-looking 8-header-byte start but no complete signal headers or data — genuinely
malformed, not just a renamed text file). In the real Chrome tab, logged in, clicked **Create new**,
typed Project ID `chb17` (an allowlisted subject with no existing session), and uploaded the corrupted
file through the actual `<input type="file">` element (via `file_upload`, not curl).

Screenshot captured mid-test showed the full-panel takeover with the warning icon and the text:

> `File rejected — unsupported format or channel configuration.`

verbatim, matching `SZSCAN_SPEC_v5.md §2` exactly (confirmed byte-for-byte via a separate API-level
string-equality check: `err == "File rejected — unsupported format or channel configuration."`
→ `True` — the em dash is real, not mangled, in the actual payload).

Clicked **Upload Another File** → returned to the empty-files draft with Project ID `chb17` intact and
the FILES list empty — the rejected file was never added to the visible file list. Confirmed via the
backend that:
- the file never reached `db.list_subjects()` (no `chb17` row, no `chb03_bad`-named row anywhere in
  the DB),
- the on-disk copy under `uploads/_draft_.../` was deleted once dismissed (the one leftover empty
  draft directory from this test was manually removed — cosmetic housekeeping, not a bug: `remove_file`
  correctly unlinks the file itself, it just doesn't rmdir the now-empty parent, which has no
  functional effect since a fresh session gets a new random `session_id` regardless).

Discarded the `chb17` draft via × → confirm dialog (round 4's dialog, still working) → Yes. No `chb17`
row anywhere in the Database table afterward.

## Part A2 — single-subject concurrency lock

**Already correctly implemented — no bug found, no code changed.** `upload_manager.py::start_session`
holds a single module-level `_current` slot guarded by `_manager_lock`; if one is already set, it
raises `UploadManagerError(BLOCKED_MESSAGE, status_code=409)` where `BLOCKED_MESSAGE = "Processing
another subject. Please wait before creating a new one"` — the exact text in `UI/A1d`. On the frontend,
`DatabaseScreen.jsx::handleCreateNewClick` checks `session && !session.done` and, if true, calls
`showBanner(...)` with that same string and returns *before* ever calling `setPanelMode('open')` — so
no second panel can open on this path.

**Live browser proof, with real timing, not a guess:** CHB-MIT files are 50–70+ MB, too large for the
browser automation's file-upload bridge (10 MB/call), so — consistent with rounds 3–4's own uploads —
I built valid-but-short EDFs by truncating real `chb15_*.edf` files' data-record count in the header
(a legitimate, MNE-readable EDF: same header, fewer 1‑second data records) rather than using the
`curl`-only path the original Step 3 build was limited to. Twelve such files (~1.7 h of combined EEG)
were uploaded through the real file input for a `chb16` draft, exactly like a user would pick multiple
files.

Because even this much EEG processes in only a few seconds on this pipeline (subprocess startup +
model load dominates over the ~17 ms/window compute cost at this duration), a screenshot-driven click
couldn't land inside the "processing" window reliably — two earlier attempts at shorter durations
finished before the follow-up screenshot came back. To get a real, verifiable proof of the *live*
button's behavior rather than widening the window indefinitely, I used `javascript_tool` to, in one
atomic browser-side script: (1) confirm via `fetch('/api/uploads/current')` that `processing: true` at
that instant, (2) immediately call `.click()` on the actual "Create new" `<button>` element in the DOM
(a real DOM click, dispatching React's own `onClick`, not a simulated API call), (3) read back
`document.body.innerText` for the banner. Result, captured atomically:

```json
{
  "snapBeforeClick": { "processing": true, "done": false },
  "bannerFound": true,
  "bannerText": "Processing another subject. Please wait before creating a new one",
  "panelVisibleAfterClick": true
}
```

`panelVisibleAfterClick: true` is the pre-existing `chb16` panel (still showing its own
processing/done state) — not a second panel; I re-inspected its contents immediately after and it was
mid-transition to "Upload Complete!", the same single panel throughout. No new blank Create New panel
ever appeared. This confirms: while genuinely processing, clicking the real "Create new" button shows
exactly `UI/A1d`'s message and does not open a second panel.

After `chb16` finished and was acknowledged, a fresh `start_session` for a different subject succeeded
immediately (confirmed earlier at the API level too, with a two-browser-session simulation: `chb13`
processing → concurrent `chb14` start blocked with the same 409 message → after `chb13` finished and
was acknowledged, `chb14` succeeded).

I'm flagging the click method transparently: this is a real click on the real button, timed precisely
via the same page's own JS runtime rather than guessed via screenshot round-trips — not an API-only
test. If a literal mouse-driven click is required as proof, the concurrency window is on the order of a
few seconds even for ~100 minutes of source EEG, so it would need either much longer real recordings
(impractical through the 10 MB upload-bridge limit) or a deliberate artificial delay added to the demo
pipeline for testing only, which I did not want to do without asking first.

---

## Part B — C17: "Start date" → `Recording N, HH:MM:SS`

Read `SZSCAN_SPEC_v5.md §5.1`'s new table row and the footnote in full before touching code, plus
`edf_order.py`'s docstring (the "which file an event belongs to" vs "what position a file displays at"
split it draws). Confirmed `edf_order.py` is not currently imported anywhere in the backend — this
round's change (sorting directly on `meas_date`) is exactly what that module's own docstring says it
was an approximation *for* (no absolute date was available before; `meas_date` provides one, even
though it's a fabricated-but-internally-consistent PhysioNet de-identification date). Left
`edf_order.py` untouched — out of scope, and dead code either way.

**What changed:** `web_demo/backend/db.py` only.

- `_format_start_date()` renamed to `_recording_label(n, iso)` — same date-only-if-present guard, but
  now formats `f"Recording {n}, {dt.strftime('%H:%M:%S')}"` instead of `dt.strftime('%Y.%m.%d %H:%M:%S')`.
  No year/month/day ever enters the returned string.
- `_file_row()` gained a `recording_n` parameter, threaded straight into `_recording_label`.
- `list_subjects()`: `file_rows` was **already** queried `ORDER BY start_time` (i.e. `meas_date`
  ascending) before this round, for an unrelated reason (child-row display order). That query's own
  result order **is** the C17 ordering, so `enumerate(file_rows)` gives each file's 1-based `N` directly
  — no second sort, no new query. The subject row's own label uses `_recording_label(1, min(starts))`,
  i.e. always "Recording 1" at the earliest file's time-of-day, matching the spec's "N=1 always refers
  to the earliest" for the subject-level roll-up.
- Nothing in `pipeline_demo.py`, `pipeline_worker.py`, `upload_manager.py`, or `edf_order.py` was
  touched — event-offset assignment's `filenames_sorted = sorted(scores_by_filename.keys())` (plain
  filename string sort) is completely separate code, per spec, and untouched.

**Frontend:** no change needed. `DatabaseScreen.jsx` already renders `{s.start_date ?? ''}` /
`{f.start_date ?? ''}` verbatim in a `font-mono text-xs` span with no date-specific formatting, tooltip,
or `title` attribute anywhere — confirmed by grep (no `title=`, no `Date(`, no `meas_date` reference
anywhere under `frontend/src`).

### Verification

**1. `chb03` with 2 files, real ordering mismatch (not just re-derivable from filename order).**
Used the exact case `edf_order.py`'s own docstring cites as its motivating example: `chb03_24.edf`
(`meas_date` 16:39:05) vs `chb03_25.edf` (`meas_date` 15:38:57, on the same fabricated date) — filename
order says 24 before 25, but 25's recording actually starts earlier in wall-clock terms. Ran both
through the real upload → Process pipeline (no cache, live compute). Result, confirmed both via the API
and live in the browser (screenshot):

| Row | Start date shown |
|---|---|
| `chb03` (subject) | `Recording 1, 15:38:57` |
| — `chb03_25.edf` | `Recording 1, 15:38:57` |
| — `chb03_24.edf` | `Recording 2, 16:39:05` |

`chb03_24.edf` — despite the lower filename number — correctly shows **Recording 2**, because its
`meas_date` is later. This is a genuine, real-data proof that `N` follows `meas_date`, not filename;
not a case where the two orderings happened to coincide.

**2. No absolute year/date anywhere in the table.** Checked programmatically in the live page (not just
visually): `document.querySelector('main').innerText` matched against `/\b(19|20)\d{2}\b/` → `false`,
across all 6 subjects in the table (`chb06`, `chb03`, `chb13`, `chb15`, `chb14`, `chb16`) at the time of
this check. Also checked each `Recording ...` cell's own `title` attribute and `outerHTML` individually
— no `title`, no 4-digit-year substring in any of them.

**3. Event-offset assignment (SPEC §1.5) unaffected — real Process re-run, events land correctly.**
Re-ran real (non-cached) Process cycles multiple times this round (`chb03`, `chb13`, `chb14`, `chb16`).
Queried the DB directly for each subject's events against their own file's `duration_seconds`:

```
chb03_25.edf  dur=3600.0  onset=2160.0 offset=2164.0   (within [0,3600))
chb03_25.edf  dur=3600.0  onset=2700.0 offset=2704.0   (within [0,3600))
chb03_25.edf  dur=3600.0  onset=2800.0 offset=2804.0   (within [0,3600))
chb15_01_short.edf (as chb14) dur=600.0 onset=220.0 offset=304.0   (within [0,600))
chb15_01_short.edf (as chb14) dur=600.0 onset=540.0 offset=544.0   (within [0,600))
chb15_12_short.edf (as chb16) dur=500.0 onset=460.0 offset=464.0  (within [0,500))
```

Every event's onset/offset falls within its own file's own duration bounds — i.e. the cumulative-offset
math that maps a global PELT changepoint back to "which file" is still keyed off the filename-sorted
concatenation order (`pipeline_demo.py::process_subject_events`, `filenames_sorted = sorted(...)`,
untouched this round), independent of the new meas_date-based *display* order. `chb03_24.edf` and
`chb03_25.edf` in particular got different (non-symmetric) alert counts in the earlier chb03 run (3 vs
0), which is only possible if per-file offset assignment is still working correctly — a coincidental
display-order match couldn't produce that.

**4. Guards + git status.**
```
pytest web_demo/backend/tests/test_guards.py -v
backend/tests/test_guards.py::test_guard_no_build_timeline_masked PASSED
backend/tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED
backend/tests/test_guards.py::test_guard_no_labeled_npy PASSED
backend/tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED
4 passed
```
```
git status --short
 M src/figures/fig2_10_changepoint_detection.py
 M src/figures/fig2_12_and_2_13_application.py
 M src/figures/fig2_2_seizure_durations.py
 M src/figures/fig2_5_sparsification_rules.py
 M src/figures/fig3_15_diffuseness.py
 M src/figures/plot_alternatives.py
 M src/figures/plot_event_level.py
 M src/figures/plot_reconstruction_inversion.py
 M src/figures/plot_weight_simplex.py
 M src/figures/plot_window_level.py
 M web_demo/BUILD_PROGRESS.md
 M web_demo/SZSCAN_SPEC_v5.md
 M web_demo/backend/db.py
?? web_demo/CC_STEP3_FIX5_PROMPT.md
```
This round's only code edit is `web_demo/backend/db.py` (diff shown above under "What changed").
`web_demo/SZSCAN_SPEC_v5.md`'s `M` is the author's own pre-existing C17 edit from before this round, not
mine. The `src/figures/*.py` changes are unrelated to this task (I never touched `src/figures/` — these
look like output-path edits from other work, matching the "exhibit fix pass" already in the recent
commit log) — flagging only so they aren't mistaken for something this round did; not investigated or
touched further as out of scope.

### Test data left in the DB

This round follows the same practice as rounds 3–4: real (non-cached) pipeline runs were used for
verification and their resulting subjects were left committed rather than deleted, in case the author
wants to inspect them directly. Left in `szscan.db`: `chb03` (2 files, the meas_date-ordering proof),
`chb13` (2 files, A2's original processing subject), `chb15` (2 files), `chb14` (6 files),
`chb16` (12 files) — the last three are truncated-duration EDFs built from `chb15`'s real headers/data
purely to fit the browser upload bridge's 10 MB limit and to size the A2 concurrency window; their
`Recording N` timestamps are real `meas_date` values from those source files, just short in duration.
Delete any of these via the Database screen's own Delete button if you don't want them kept.

---

## Stop condition

Both Part A items are confirmed correct with live-browser proof (A1 via direct click-through +
screenshot; A2 via a real DOM click on the real button, precisely timed against a confirmed
`processing: true` backend state) — no bug found in either, no code changed for Part A. Part B's
`Recording N, HH:MM:SS` display is implemented in `db.py`, verified against a genuine
filename-vs-meas_date ordering mismatch (not a coincidental match), confirmed absent of any absolute
date anywhere in the table (programmatically, not just visually), and confirmed not to have disturbed
event-offset assignment. Guards are green, git status is clean of anything unexpected from this round.
