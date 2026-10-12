# REPORT_HANDBACK.md — SzScan web demo, report handback to Project 2

**Note on referenced documents:** `REPORT_REQUEST_TO_PROJECT2.md` and `REPORT_REPLY_TO_PROJECT2_OP.md`
(both cited by `CC_REPORT_HANDBACK_PART0_PROMPT.md` as required reading, and the source of this file's
template in the request's Part 5) do not exist anywhere in this repository — checked by filename search
across the whole tree, not just `web_demo/`. Only `web_demo/REPORT_REPLY_TO_PROJECT2_2.md` was found and
has been read in full; its content is reflected below and was used to fill in context the missing
documents would otherwise have supplied. This section is therefore built directly from the explicit
instructions in `CC_REPORT_HANDBACK_PART0_PROMPT.md` rather than the request's own Part 5 template
structure. If `REPORT_REQUEST_TO_PROJECT2.md` exists outside this repo snapshot, please add it (or paste
its Part 5 template) so later parts (1/3/4) and this section's heading structure can be corrected to
match it exactly.

## 0. Frozen build

**Tag:** `szscan-frozen-v2` (supersedes `szscan-frozen-v1`, `66f7c89c4d9931c0895c5efb739289859293af16` —
that tag's partial Tier 2 run, described lower in this section and in §3's superseded subsection, was
discarded in full: the database was emptied of all 8 subjects, including the one (`chb03`) that had
fully finished under v1, and every subject was reprocessed from scratch under v2.)
**Commit:** `0ffd99b0a301515e1251bece77d236d838632ab0`

**Reason for the new tag:** two out-of-memory failures on `chb06` under v1 (`_PHASE_A_MAX_CONCURRENCY
= 4`) — the second on a freshly rebooted, otherwise-idle machine — made this a reproducible build
defect on the target laptop, not a load problem (Decision by Boti, 2026-09-29, `CC_PART3_RERUN_V2_
PROMPT.md`). Fix: `web_demo/backend/upload_manager.py:44`, `_PHASE_A_MAX_CONCURRENCY = 4` → `= 2`.
Nothing else changed in that commit.

### Guard tests (`web_demo/backend/tests/test_guards.py -v`, run on the tagged commit)

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\Dell Latitude 3590\AppData\Local\Programs\Python\Python311\python.exe
cachedir: .pytest_cache
rootdir: F:\Study\Thesis\Code
plugins: anyio-4.15.1
collecting ... collected 4 items

web_demo/backend/tests/test_guards.py::test_guard_no_build_timeline_masked PASSED [ 25%]
web_demo/backend/tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED [ 50%]
web_demo/backend/tests/test_guards.py::test_guard_no_labeled_npy PASSED  [ 75%]
web_demo/backend/tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED [100%]

============================== 4 passed in 6.98s ==============================
```

Re-confirmed 4/4 again after the full Tier 2 v2 run below (`4 passed in 4.88s`) — unchanged, as expected
since this run touched no source, only `web_demo/backend/uploads/` and `web_demo/report_handback/`.

### Provenance (`python src/verify_provenance.py`)

```
canonical : data\models_retrain\gae_joint_seed42.pt
  size    : 15258 B
  sha256  : dea06cb533df1c7d0520ae21c4cbb1b8a938297f937366bc9915b040726ea108
  bias_fp : 1.1597   (module constant BIAS_FP_CANONICAL = 1.1597)
  worst corr = 1.0000000 over 4 array(s), missing=0
VERDICT: PASS — checkpoint is canonical
```

Checkpoint identity, as loaded by the demo (`web_demo/backend/pipeline_demo.py:85-86`, confirmed
identical at the tagged commit via `git show szscan-frozen-v2:web_demo/backend/pipeline_demo.py`):

```python
CHECKPOINT_PATH = REPO_ROOT / "data" / "models_retrain" / "gae_joint_seed42.pt"
CHECKPOINT_SHA256 = "dea06cb533df1c7d0520ae21c4cbb1b8a938297f937366bc9915b040726ea108"
```

Both checks passed on the first run at the tagged commit — no fix-and-reverify cycle was needed, so
the tag above stands as created.

### Fixes since the last tag

- `score.npy` was never persisted by the live Process flow, so `waveform_serving.get_timeline` fell
  into its own error path for any subject processed through the UI — found by reading
  `upload_manager.py` against that error path, not by a symptom report.
- `MiniTimeline.jsx` was hardcoded to a 1-hour domain — found by reading the component after `chb06`,
  a subject with files longer than 1 hour, was added to the DB.
- The filter toolbar was collapsed from 3 buttons to 1 — found because 2 of the 3 buttons toggled the
  same cached array, and the measured difference between the two real filter stages was negligible.
- The delete endpoint was not removing `uploads/{id}/` on disk, and Phase-A upload concurrency was
  unbounded — both found by code review, not by any subject's output.
- `chb13` was short 31 of its 33 real files — found by a file-count audit against the dataset
  directory.
- The operating point was switched to the fixed validation point `mag_pct=50`, `pen_mult=2.0`
  (`web_demo/backend/pipeline_demo.py:109-110`) — Project 1's methodological decision, not a bug.
  `calibrate_operating_point()` is confirmed not called anywhere on the live path (`process_file` /
  `process_subject_events` / `upload_manager.py` / `pipeline_worker.py`) — the only remaining call is
  the dev-only `__main__` CLI smoke-test block at `web_demo/backend/pipeline_demo.py:681` (confirmed
  by grep across `pipeline_demo.py`, `upload_manager.py`, `pipeline_worker.py`). Full detail in
  `CC_FIX_OPPOINT_REPORT.md`.
- `_PHASE_A_MAX_CONCURRENCY` (`web_demo/backend/upload_manager.py:44`) was `4`, and `chb06` — the
  subject with the largest individual real files — ran out of memory processing it twice under v1,
  once on a freshly rebooted machine, ruling out background load as the cause. Lowered to `2`; this is
  the only source change in the v2 tag (see above). Not re-investigated further per instruction (§3's
  v1 subsection below has the original OOM diagnostics); v2's own run completed `chb06` clean at a
  measured peak of ~10.2 GB combined backend+worker RSS (§3), comfortably under this machine's ~16.7 GB.

### chb06 diagnostic

No defect found, no change made. (Per `REPORT_REPLY_TO_PROJECT2_2.md` §1: accepted as reported; the
measured channel-score/signal-amplitude correlation from that diagnostic is not in the record and is
not cited in the report.)

---

## 1. As built

All claims below are read from the code at the frozen tag `szscan-frozen-v1`
(`66f7c89c4d9931c0895c5efb739289859293af16`), not from `SZSCAN_SPEC_v5.md`'s prose, except where a
spec quote is itself the fastest way to point at the same evidence the code shows.

### 1.1 Detection path

#### 1.1.1 Divergences (a), (b), (c): implemented as stated? file:function for each

**(a) Normalization statistics, covariance, and robust-z fit on the whole recording; no artifact
rejection.** Implemented exactly as stated, and yes — the fit is per subject, over every window of
every file of the subject.
- z-score mean/std: `pipeline_demo.process_subject_phase_b()`, `web_demo/backend/pipeline_demo.py:342-389`
  — `filenames_sorted = sorted(filtered_by_filename.keys())` (line 342) is every file currently in the
  subject's upload session (`upload_manager.py:387-388`: `scores = {fn: f.score for fn, f in
  session.files.items()}`), and `ch_mean`/`ch_std` are accumulated across all of them before any file is
  z-scored (line 402).
- LedoitWolf fit for `zlatent`: same function, `pipeline_demo.py:466-470` — `LedoitWolf().fit(all_graph_z)`
  where `all_graph_z` is the concatenation of every file's graph-level Z (line 467).
- Robust-z (median/MAD) per branch: same function, `pipeline_demo.py:472-491` — fit on
  `all_zrecon`/`all_zlatent`/`all_zgamma`, each the subject-wide concatenation (lines 475-480).
- Artifact rejection: **not implemented, by omission** — `pipeline_demo.py` never imports or calls
  `preprocessing.ARTIFACT_SD_MULTIPLIER` or the 5 SD check that `preprocessing.count_windows()` /
  `write_windows()` apply (`src/dataprep/preprocessing.py:317-325, 386-391`); confirmed by grep, those
  two names appear only inside `preprocessing.py` itself.

**(b) No four-hour post-seizure buffer.** Implemented exactly as stated, by omission — `pipeline_demo.py`
never calls `preprocessing.build_buffer_mask()` (`src/dataprep/preprocessing.py:194-198`,
`BUFFER_S = 4 * 3600` at line 55); that function is only called from `preprocessing.py`'s own
`compute_subject_stats`/`count_windows`/`write_windows` (lines 236, 301, 361), none of which
`pipeline_demo.py` uses. With no mask to exclude anything, the whole post-ictal segment passes straight
into `process_subject_events()`'s PELT call.

**(c) Change-point penalty and magnitude threshold estimated over the whole recording.** Implemented
exactly as stated. `pipeline_demo.process_subject_events()` calls `cpd_pipeline_v14.detect_events()`
(`web_demo/backend/pipeline_demo.py:597-599`) with no `inter_mask` argument, so it defaults to `None`.
Inside `cpd_pipeline_v14.detect_changepoints()` (`src/cpd_pipeline_v14.py:121-148`): the PELT penalty's
variance comes from `_robust_variance(smoothed, inter_mask)` (line 129), whose `mask is None` branch
uses `ref = signal` — the whole recording (`src/cpd_pipeline_v14.py:81-88`); the magnitude-filter
threshold's background sample is `bg = list(mags.values())` when `inter_mask` is `None`
(`src/cpd_pipeline_v14.py:138-142`) — again the whole recording, not an interictal-only subset.

#### 1.1.2 Every other difference from the thesis pipeline

One difference found, otherwise none after checking the full list below.

- **Filtering — difference found.** Filter coefficients are identical (0.5–60 Hz 4th-order
  Butterworth `_BP_SOS`, 60 Hz notch Q=30 `_NOTCH_B`/`_NOTCH_A`, both zero-phase — shared constants,
  `src/dataprep/preprocessing.py:78,81`, imported unmodified by `pipeline_demo.py:236-237`). But the
  thesis's per-window `preprocessing.filter_window()` (`src/dataprep/preprocessing.py:163-182`) reads
  each window plus 3 s (768-sample) padding on each side (`FILTER_PAD = 3 * FS`, line 56) and crops back
  to the window after filtering, whereas `pipeline_demo.process_file_phase_a()`
  (`web_demo/backend/pipeline_demo.py:230-248`) runs bandpass+notch **once, continuously, over the
  file's entire recording**, then cuts the result into windows — no `filter_window()` call, no 3 s
  padding, because there are no per-window boundaries to pad against. This is a real difference in
  method (whole-file single pass vs. per-window padded pass), not just of degree; it is already
  explained in `pipeline_demo.py`'s own comment (lines 230-234: "both faster and slightly more correct —
  edge effects only at the true file start/end") but is not listed as a divergence item in
  `SZSCAN_SPEC_v5.md` §1.3/§1.6, which describes this step only as "same as the thesis."
- Channel selection and the duplicate T8-P8: no difference — `pipeline_demo.py:213` calls
  `preprocessing.open_edf()` unmodified (`src/dataprep/preprocessing.py:132-158`); the duplicate-channel
  rename/pick logic (lines 140-158) is the identical code path for both.
- Common average reference inside the adjacency builders: no difference — `graph_construction.apply_car()`
  (`src/dataprep/graph_construction.py:84-90`) is called per window before wPLI/AEC at
  `pipeline_demo.py:409`, the same placement as the thesis's own `build_adjacency()`
  (`graph_construction.py:259-260`).
- wPLI and AEC with α = 0.5: no difference — `pipeline_demo.py:410-412` calls
  `combine_adjacency(wpli, aec, alpha=graph_construction.DEFAULT_ALPHA)`, and
  `DEFAULT_ALPHA = 0.5` (`graph_construction.py:70`).
- Top-20% sparsification: no difference — `pipeline_demo.py:413` calls
  `apply_topk_threshold(A, keep_ratio=graph_construction.DEFAULT_KEEP_RATIO)`, and
  `DEFAULT_KEEP_RATIO = 0.20` (`graph_construction.py:72`).
- Band powers (Welch, 2 s segments, 50% overlap): no difference — `pipeline_demo.py:415` calls
  `feature_extraction.compute_band_powers()` unmodified; `welch(window, fs=256, nperseg=fs*2,
  noverlap=fs, axis=1)` (`src/dataprep/feature_extraction.py:32`) is 512-sample (2 s) segments with
  256-sample (50%) overlap.
- The three scores: no difference — `zrecon` (GAE reconstruction, `pipeline_demo.py:426`), `zlatent`
  (LedoitWolf Mahalanobis distance, `pipeline_demo.py:468-470`), `zgamma` (gamma-band AEC,
  `pipeline_demo.py:444-451`) match the locked headline subset `ensemble_recipe.CANDIDATES["rlg"]`
  (`src/ensemble_recipe.py:85`, `("zrecon", "zlatent", "zgamma")`) — no LSTM/temporal branch, matching
  `CLAUDE.md` "Model identity".
- Equal-weight fusion: no difference — `pipeline_demo.py:487-490` calls
  `ensemble_recipe.build_ensemble_subset(..., subset=CANDIDATES["rlg"])` with no `weights` argument, so
  it defaults to equal weights (`weights = [1.0 / len(subset)] * len(subset)`,
  `src/ensemble_recipe.py:91,101`) — the same default the script that produced the locked "rlg" Tier-2
  results used (`src/phaseB/build_ens_tier2.py:124-125`, which records `weights="equal"` in its own run
  metadata at lines 232-233).
- Smoothing (15-window centered moving average): no difference — same shared function,
  `cpd_pipeline_v14.SMOOTH_WIN = 15` (`src/cpd_pipeline_v14.py:50`), `_smooth()`
  (`src/cpd_pipeline_v14.py:70-78`).
- PELT at 20 s resolution, minimum segment of 3 windows: no difference — same shared function,
  `PELT_JUMP = 5` → 5 windows × 4 s = 20 s, `PELT_MIN_SIZE = 3` (`src/cpd_pipeline_v14.py:51-52,131`).
- The magnitude filter (mechanism): no difference — same shared code
  (`src/cpd_pipeline_v14.py:135-143`). The *value* passed for `min_mag_pct` differs from this file's own
  keyword default of 60 — see 1.1.4.
- Merge gap of 90 s: no difference — `detect_events(..., merge_s=90)` default
  (`src/cpd_pipeline_v14.py:151-152`), not overridden by `pipeline_demo.py:597-599`.

#### 1.1.3 Multiple files per subject

PELT is run **once, on the concatenated subject-wide timeline**, never per file. In
`process_subject_events()` (`web_demo/backend/pipeline_demo.py:569-622`), every file's Phase B score
array is concatenated in filename order (line 595: `global_score = np.concatenate(...)`), and
`cpd_pipeline_v14.detect_events()` is called exactly once on that array (lines 597-599).

Event times **are** reported relative to each file. The same function converts each global event back
to file-relative seconds by cumulative offset (lines 587-620), returning
`FileEvent(onset_sec=local_onset, offset_sec=local_offset)` (line 619) — `local_onset`/`local_offset`
are seconds from the start of that specific file, not the subject-wide timeline. This is what
`upload_manager.py` persists per file (`events_payload[fn] = [{"onset_sec": onset, "offset_sec":
offset}, ...]`, `web_demo/backend/upload_manager.py:423-426`) and what `attribution.py`'s
`_event_windows()` consumes, assuming window `i` spans `[4i, 4i+4)` **within that file**
(`web_demo/backend/attribution.py:50-61`).

#### 1.1.4 Operating point parameters, with file:line

- `mag_pct` (passed as `min_mag_pct`): `FIXED_MAG_PCT = 50` — `web_demo/backend/pipeline_demo.py:109`.
- `pen_mult`: `FIXED_PEN_MULT = 2.0` — `web_demo/backend/pipeline_demo.py:110`.
- Both are used at the single call site, `web_demo/backend/pipeline_demo.py:597-599`:
  `cpd_pipeline_v14.detect_events(global_score, FIXED_PEN_MULT, min_mag_pct=FIXED_MAG_PCT)`.
- No other detection parameter is chosen per run or per subject. The remaining `detect_events` keyword
  arguments are left at their shared, un-overridden defaults — `local_win=15`, `win_sec=4`,
  `merge_s=90` (`src/cpd_pipeline_v14.py:151-152`) — these are fixed algorithm-mechanism constants
  covered under 1.1.2 (smoothing/PELT resolution/merge gap), not per-run operating-point knobs.

These are exactly the values this request states as validation-derived (`mag_pct = 50`,
`pen_mult = 2.0`) — **the application does not use anything else.** Until 2026-09-29 the live path
instead called `calibrate_operating_point()` (`pipeline_demo.py:536-560`), a per-subject grid search
over `PEN_MULT_GRID` targeting `fp_budget_operating_point.BUDGETS["balanced"]`; that function is kept in
the file (not deleted) but confirmed not called anywhere in the live path
(`process_file`/`process_subject_events`/`upload_manager.py`/`pipeline_worker.py`) — the only remaining
call is the dev-only `__main__` CLI block at `pipeline_demo.py:681`. Full change record:
`CC_FIX_OPPOINT_REPORT.md`, and §0 above.

### 1.2 Channel panel

#### 1.2.1 Implementation, quoted with surrounding lines

Step 7 round 2 is done; the panel shows exactly the decided definition. From
`web_demo/backend/attribution.py:80-91`:

```python
    pernode = np.load(pernode_path, mmap_mode="r")  # [n_windows, 18] float32
    n_windows = pernode.shape[0]
    lo, hi = _event_windows(event["onset_sec"], event["offset_sec"], n_windows)
    window_scores = np.asarray(pernode[lo : hi + 1]).astype(np.float64)  # [k, 18]

    baseline = np.load(baseline_path).astype(np.float64)  # [2, 18]: row 0 = median, row 1 = MAD
    med, mad = baseline[0], baseline[1]
    z = np.abs((window_scores - med) / mad)  # [k, 18], per window per channel
    per_channel = np.percentile(z, 95, axis=0)  # items 2-3: p95 |robust-z|, event-level score
    order = np.argsort(-per_channel)  # item 3: rank = position by score, highest first
```

The absolute-value line is `z = np.abs((window_scores - med) / mad)` (line 87); the percentile line is
line 88. `med`/`mad` come from the subject-wide baseline (`pipeline_demo.compute_pernode_baseline()`,
`pipeline_demo.py:140-155`), not an interictal-only one.

#### 1.2.2 Panel title

Exactly `Channel-level reconstruction anomaly — Event N`:
`web_demo/frontend/src/components/AttributionPanel.jsx:110`:
`` const title = `Channel-level reconstruction anomaly — ${event.name}` ``, where `event.name` is
generated as `f"Event {index + 1}"` (`web_demo/backend/db.py:308`) — e.g. "Event 1", "Event 2". The
score itself is displayed with two decimals: `r.score.toFixed(2)`
(`web_demo/frontend/src/components/AttributionPanel.jsx:218`).

#### 1.2.3 Baseline recomputed when

Only when the subject is processed (Phase B) — **never** on an attribution read. The baseline is
computed once by `pipeline_demo.compute_pernode_baseline()` (`pipeline_demo.py:140-155`) during Phase B
and written to `{subject}/pernode_baseline.npy` by `pipeline_worker.py:_run_phase_b`
(`web_demo/backend/pipeline_worker.py:27-54`, the save itself at line 54). `attribution.
get_event_attribution()` only ever loads that file from disk (`attribution.py:85`,
`np.load(baseline_path)`) — it is never recomputed on read, including when an event's onset/offset is
edited (a Human event's range change re-reads the same persisted baseline, per the module's own
docstring, `attribution.py:4-8`).

### 1.3 Architecture

#### 1.3.1 Components and versions

- **Frontend:** React 19.2.8 + React DOM 19.2.8, built/dev-served by Vite 8.2.2, styled with Tailwind
  CSS 3.4.19 (`web_demo/frontend/package.json`; versions confirmed as installed, not just the `^`-range
  in the manifest). No routing library is used — screen switching is local `useState`, by the app's own
  design note: "no router in this app" (`web_demo/frontend/src/App.jsx:10-11`).
- **Backend:** FastAPI 0.141.1 on Uvicorn 0.52.4 (`web_demo/backend/main.py:20-21,42`), Python 3.11.9.
- **Database:** SQLite via Python's stdlib `sqlite3` module (module version 2.6.0, bundled SQLite
  library 3.45.1), one file, `web_demo/backend/szscan.db` (`web_demo/backend/db.py:14`, connect at
  line 64, schema init at line 70).
- **Background processing:** Phase A (per-file open/filter/window) runs on a
  `concurrent.futures.ThreadPoolExecutor` inside the main backend process
  (`web_demo/backend/upload_manager.py:23,45`, submitted at line 194). Phase B (subject-wide
  normalization + GAE/gamma scoring) and the Process/PELT stage run in a genuinely separate OS process,
  launched with `subprocess.run` against `pipeline_worker.py`
  (`web_demo/backend/upload_manager.py:18,286-299`) rather than
  `concurrent.futures.ProcessPoolExecutor` — the comment at lines 49-59 records that
  `ProcessPoolExecutor` was found to hang indefinitely on this Windows dev machine.
- **File storage:** local filesystem only, under `web_demo/backend/uploads/{subject_id}/`
  (`web_demo/backend/upload_manager.py:33`); no cloud or object storage.
- **Authentication:** one fixed admin account read from `web_demo/backend/.env`
  (`ADMIN_USER`/`ADMIN_PASS`, `main.py:35-36`), checked with constant-time comparison
  (`secrets.compare_digest`, `main.py:82-83`). Session is an in-memory random token
  (`secrets.token_urlsafe(32)`, `main.py:86-87`) keyed to the username, carried in an HttpOnly,
  non-secure, `SameSite=Lax` cookie (`main.py:88-90`). The module's own docstring states this is
  explicitly not a real security mechanism — no password hashing, no expiry, no CSRF protection
  (`main.py:8-11`).

#### 1.3.2 Outbound network requests at runtime

- **Fonts:** bundled locally as `.woff2` files under `web_demo/frontend/public/fonts/` (Inter, IBM Plex
  Mono), loaded via `@font-face` in `web_demo/frontend/src/index.css:6-41`. No `<link>` to Google Fonts
  or any other font service in `index.html`.
- **CDN references:** none found in `index.html` or any `.css`/`.jsx` file — checked by grepping the
  whole frontend `src/` tree for `http://`/`https://`. The only match is the XML namespace URI inside
  the default, unmodified Vite logo `src/assets/vite.svg`, which is not fetched at runtime — that file
  is never imported anywhere in `src/` or referenced by `index.html`.
- **Telemetry / update checks:** none found — grepped the backend for any HTTP client usage (`requests`,
  `httpx`, `urllib`, `http.client`) with zero matches. The frontend's only network calls are `fetch()`
  calls in `src/api.js` to the backend's own `/api/...` routes.
- **Cross-origin config:** the backend's CORS allowlist is restricted to `http://localhost:5173` and
  `http://127.0.0.1:5173` (`main.py:46-52`) — the Vite dev server's own origin, not an external service.
- **How checked:** code read (grep across `web_demo/frontend/src` and `web_demo/backend` for
  `http(s)://`, CDN/font hostnames, and HTTP-client imports), for everything above.
- **Flag — network-off run not confirmed done.** This prompt's own instructions describe "the
  network-off run already done 2026-09-28" as an available source of evidence. `web_demo/BUILD_PROGRESS.md`'s
  own open-items list (§14, itself last edited 2026-09-28) states as item 3: "Network-off run (Boti, by
  hand): ... Not done yet." No report file in the repo documents a completed network-off run. Per this
  request's own ground rule 2, this handback records only the code-read evidence above and reports the
  network-off run itself as **not measured**, pending Boti's confirmation of whether it was actually run
  after that `BUILD_PROGRESS.md` entry was written.

#### 1.3.3 Differences from Figure 2.6

The actual figure was not sent with this request, so this can only be checked against the description
given in it. Against that description — no difference found: the application recomputes scores on the
continuous recording (`pipeline_demo.py` Phase A/B), keeps every window with none ever dropped
(`SZSCAN_SPEC_v5.md` §1.6 item 1 — no artifact rejection; confirmed absent from `pipeline_demo.py`
above), and never reads annotations, builds a label-based timeline, or loads the pre-split
interictal/ictal arrays — enforced by `web_demo/backend/tests/test_guards.py`, 4/4 passing at the
frozen tag (§0 above). Project 1's offered visual check against the actual Figure 2.6 is still needed to
confirm this in the diagram itself, not just in the description.

### 1.4 Functions

- **Sign-in:** one fixed admin account read from `.env`; username/password are checked with
  constant-time comparison, and on success an HttpOnly session cookie is set
  (`main.py:79-91`). A reviewer who is not logged in gets `401` from every other endpoint
  (`main.py:72-76`). No registration, no password reset — a symbolic access gate, not a real security
  boundary (`SZSCAN_SPEC_v5.md` §0).
- **Recording import and processing:** from the Create New panel, the reviewer uploads one or more EDF
  files for one subject. Each file shows a spinning-circle status icon while Phase A (open, filter,
  window) runs in the background (`upload_manager.py:45,194`), then flips to an uploaded/ready state
  once Phase A finishes (`pipeline_demo.py:11-15`). Once every file of the subject has reached that
  state, the reviewer clicks Process (`POST /api/uploads/current/process`, `main.py:469`), which runs
  Phase B and Stage 2 as one background job in a separate process (`upload_manager.py:286-299`); the
  panel shows a processing indicator for this step but no algorithm-internal progress breakdown.
- **Detection timeline:** `MiniTimeline.jsx` draws the subject's AI-detected events as markers along a
  timeline sized to the file's real duration; clicking an event or scrubbing the timeline moves the
  synchronized EEG view (`EegPanel.jsx`) to that point. Navigation includes pan/zoom and a selectable
  playback speed of 1×, 2×, 4× or 8× that scales how fast the EEG view advances during playback
  (`AnalysisScreen.jsx:72,133,780-804`, `SPEED_OPTIONS = [8, 4, 2, 1]`).
- **Event review:** each AI event can be marked Accept, Reject or Uncertain from the event panel
  (`PanelEvent.jsx:39`, persisted via `PATCH /api/events/{event_id}`, `main.py:294-315`); `Unseen` is
  the unreviewed default and is not a value this control can set back to. A reviewer adds a Human event
  by a two-click Select Range drag directly on the EEG view (`POST /api/files/{file_id}/events`,
  `main.py:271-284`); it is auto-confirmed on creation and carries no review status, only an optional
  comment and an editable onset/offset (`main.py:296-301`).
- **Channel panel:** for a selected event, ranks the 18 EEG channels by a per-channel
  reconstruction-anomaly score (95th-percentile |robust-z| over the event's windows, against the
  subject's whole-recording baseline), each shown to two decimals, with an Accept/Reject control per
  channel independent of the event's own review status (§1.2 above).
- **Export:** once every file of a subject has been marked Viewed, `GET
  /api/subjects/{subject_id}/export` downloads one `.txt` summary of that subject's events
  (`main.py:145-166`, `export_txt.py`); the endpoint returns `409` and the export stays disabled in the
  UI until that condition holds.

**Specified but not built:** per-subject label-free operating-point calibration
(`calibrate_operating_point()`, `pipeline_demo.py:536-560`) was implemented but is not used on the live
path as of this tag — kept as a documented, code-complete alternative that is intentionally not shipped,
per Project 1's methodological decision (§0's fixes list, `CC_FIX_OPPOINT_REPORT.md`); recorded as
future work for thesis Chapter 4 §4.5.

**Known defects at the frozen tag:** none found. Two entries on `BUILD_PROGRESS.md`'s own open-items
list (§14, last edited 2026-09-28) are stale as of this tag and should not be read as current defects:
(1) item 2's claim that `MiniTimeline.jsx`'s `DOMAIN_SEC` is still hardcoded to 3600 — that identifier no
longer exists in the file (fixed; §0's fixes list); (2) the "redundant PELT pass" and "duplicated
`MIN_MAG_PCT` literal" entries under "Low priority / known" — both describe the old
`calibrate_operating_point()` code path, which no longer runs on the live `process_subject_events()`
(§1.1.4 above), so neither has any live effect. Two items remain genuinely open but are process items,
not application defects: the network-off run (§1.3.2 above, not measured) and a pending small edit to
the repo's own copy of `SZSCAN_SPEC_v5.md` (§14 item 1), partly superseded by this handback's own O1
edit for the fixed operating point.

---

*Part 1 above was produced by `CC_REPORT_HANDBACK_PART1_PROMPT.md`, which covered Part 1 only.
Parts 2 and 4 are added below by `CC_PART2_PART4_PROMPT.md`, on the `szscan-frozen-v2` checkout
(confirmed unchanged against the tag before this run — empty `git diff szscan-frozen-v2..HEAD
--stat -- web_demo/`; the only untracked additions are `.md`/`.log` files and
`report_handback/`, both explicitly exempted by that prompt).*

---

## 2. Screenshots (Figure 3.6 application screens)

Captured with Playwright (not `claude-in-chrome` — same reason as §3's driver: real file
sizes), against this checkout's own dev backend (`127.0.0.1:8000`) and frontend
(`localhost:5173`): viewport 1600×1000 CSS px, device scale factor 2, light color scheme
(the app has no dark theme), headless (no browser chrome, no cursor). Output directory
`web_demo/report_handback/`.

| PNG | Recording | Event | Onset (file-relative s) | Offset (file-relative s) |
|---|---|---|---|---|
| `fig3_6a_import.png` | `chb13_05.edf` — a throwaway one-file draft session (Project ID `chb13`), discarded via the app's own Close/Discard flow before Process was ever clicked; not part of the Tier 2 evaluation data | n/a (import screen, no event) | n/a | n/a |
| `fig3_6b_timeline.png` | `chb13_62.edf` | Event 2 | 1060.0 | 1064.0 |
| `fig3_6c_channel_panel.png` | `chb13_62.edf` | Event 2 | 1060.0 | 1064.0 |
| `fig3_6d_review.png` | `chb13_62.edf` | Event 2 | 1060.0 | 1064.0 |

**Event selection (label-free, per instruction):** `chb13_62.edf` has 3 AI events (ids 814,
815, 816 in `szscan.db`, onsets 960.0/1060.0/1660.0 s). Event 2 (onset 1060.0, offset 1064.0)
was picked as the one with the highest **max fused anomaly score within its own onset–offset
window**, read straight from `chb13_62.score.npy` (window = 4 s, `WIN_S`): windows 240–241
(Event 1) peak 1.461; windows 265–266 (**Event 2**) peak **2.160**; windows 415–416 (Event 3)
peak 1.740. No label was read to make this choice.

**Throwaway upload (`fig3_6a_import.png`), how it was kept clean:** a new draft session
(Project ID `chb13`, one file, `chb13_05.edf` — chosen only because every real `chb13_*.edf`
is the same ~40 MB size) was started, screenshotted the moment its per-file "uploading" spinner
appeared (`button[aria-label^="Stop uploading"]`, confirming Phase A was genuinely in
progress), then closed via the panel's own × → "Discard this draft?" → Yes — never reaching
`ready_to_process`, PROCESS was never clickable. Verified clean afterward: `szscan.db`
unchanged (8 subjects, `chb13` still exactly 33 files, no new row), and the draft's upload
directory (`uploads/_draft_ad9fdc59bf5f05aa/`) — left orphaned on disk by the discard, the
same known behavior already documented in §3's false-starts account — was deleted directly
(plain directory delete, the same precedent used there), not left behind as clutter from this
task's own scratch work.

**Side effect on real evaluation data, disclosed:** opening `chb13_62.edf` in the Analysis
screen for panels (b)/(c)/(d) runs the app's own `markFileViewing` on that file, per
`SZSCAN_SPEC_v5.md`'s normal navigation behavior — this is unavoidable if the screen is to be
shown at all, and is not a review action (no event was Accepted/Rejected/marked Uncertain, no
comment saved, `PATCH /api/events` was never called). Effect: `chb13_62.edf`'s own file
`status` changed from `View` to `Viewing` in `szscan.db` (confirmed: `chb13` is now 32 files at
`View` + 1 at `Viewing`; every other of the 231 processed files across all 8 subjects is
untouched, still `View`). §3's own claim — "no event was reviewed... every subject's file
`status` is `View`, never `Viewed`" — still holds exactly as written (`Viewing` is not
`Viewed`, and this table already only ever claimed the *files*, not this later screenshot
session, stayed `View`); noted here rather than silently left inconsistent with §3.

**Calendar-date / clock-time check (CC_PROMPT_FIG3_6.md Part B), OCR unavailable:**
`pytesseract` is not installed in this environment, so the described OCR search (4-digit
years, month names, `hh:mm:ss` patterns) could not be run mechanically. By code review
instead: every on-screen time in this app (`web_demo/frontend/src/time.js:formatFileTime` /
`formatFileTimeMinutes`) reads only the UTC hour/minute/second of `fileMeta.start_time` — it
never calls `getUTCFullYear()`/`getUTCMonth()`/`getUTCDate()`, so the real anonymization-
shifted calendar date (2057–2075) cannot reach the screen through this code path, confirmed by
reading the function, not by inspecting pixels. What **does** appear, by design
(`SZSCAN_SPEC_v5.md §6.2`), is `HH:MM:SS`-shaped file-relative pseudo-time everywhere a time
axis exists: the "Start date" column in `fig3_6a_import.png` (e.g. `Recording 1, 16:43:14`),
the mini-timeline ticks and Onset/Offset labels in `fig3_6b_timeline.png`, and the Onset/Offset
lines in `fig3_6c_channel_panel.png`/`fig3_6d_review.png`. **Flagged for Boti's own visual
check, per the OCR-unavailable fallback this prompt specifies:** confirm none of these
`HH:MM:SS` strings is a real calendar date/time (none carry a year, month name or day count
that isn't the file's own relative `dN` prefix) before this figure goes in the report. No
evaluation metric (sensitivity/precision/F1/AUROC/FP-per-day/operating-point) or patient
identifier other than the CHB-MIT subject/file name appears anywhere in any of the four
screenshots. The channel panel title reads exactly `Channel-level reconstruction anomaly —
Event 2` (`fig3_6c_channel_panel.png`), matching `SZSCAN_SPEC_v5.md`'s required format.

---

## 3. Tier 2 run

**Status: complete.** All 8 subjects reprocessed from an empty database on `szscan-frozen-v2`
(`_PHASE_A_MAX_CONCURRENCY = 2`), memo `frozen build szscan-frozen-v2`, in the order chb06, chb03,
chb13, chb14, chb15, chb16, chb17, chb18. No subject failed, no file failed, no OOM. No event was
reviewed and no Human event was added anywhere during this run (every subject's file `status` is
`View`, never `Viewed`, at the time of this report).

**Runtime environment:** Windows, pagefile on `F:` (`F:\pagefile.sys`), `TMP`/`TEMP` on `F:/tmp` — same
machine state as the resumed v1 session below. Backend: `python -m uvicorn main:app --port 8000` from
`web_demo/backend/`, already running at session start (started immediately after the `szscan-frozen-v2`
commit/tag, before this task picked up) and left running throughout and after. Driven via the real HTTP
flow (login, sequential per-file upload POSTs, Process, poll, acknowledge) from a driver script, not
`claude-in-chrome` (real file sizes exceed its attachment cap).

**Step C (empty the database):** the DB already had 0 subjects when this task started (confirmed `GET
/api/subjects` → `[]`) — presumably already done as part of the same v2 setup that started the backend.
No `DELETE /api/subjects/{id}` call was blocked or needed for `chb03` specifically; it was not a case of
a blocked permission check, simply already absent. Three orphaned draft directories were found on disk
with no live session behind them and deleted: `uploads/_draft_1ce25dd8a7bbbbec/` (11 GB — the partial
`chb06` draft carried over from the discarded v1 run, referenced in the superseded section below),
`uploads/_draft_545c391fc73f7447/` (12 generic test `.edf` files, unrelated to any real subject), and
`uploads/_draft_5f624f60c5908183/` (empty). Since `chb03` was already absent rather than blocked, it was
processed in step D (not skipped).

**Two false starts, caught and corrected before any subject completed (recorded here for an accurate
process record, not hidden):**
1. A first launch of the driver script was reported as blocked, but had in fact already spawned; a
   retry launched a second, genuinely concurrent instance. Both wrote into the same global upload
   session for a few seconds (the backend holds exactly one session slot system-wide) before this was
   caught. Both processes were killed, the corrupted shared session was discarded, and the two orphaned
   draft directories that race left behind were deleted (after a short wait for the backend's own
   Phase-A thread-pool workers to release their file handles). No subject had reached Process at that
   point.

   **Which subject, and exact proof it was discarded and reprocessed clean:** the duplicate instance
   touched **`chb06`**'s upload session only — it was subject 1/8, the first thing either instance did
   (`scripts/v2_driver_log.txt` lines 1-9, both timestamps UTC): the first instance logged in and started
   the `chb06` session at `19:40:01`; the retry logged in again at `19:40:51`, found and discarded that
   still-open `chb06` session (`DELETE /api/uploads/current` → `200`, logged as "Discarded a leftover
   non-processing session (200)"), then started its own competing `chb06` session in the same second.
   Both instances were then killed by hand and the result discarded — `scripts/v2_driver_log.txt` line 10:
   `=== restart marker 2026-09-29T19:44:38Z: killed a duplicate racy driver instance, discarded corrupted
   shared session, removed 2 orphaned drafts it created, restarting clean ===`. No other subject's name
   appears anywhere in the log before this marker, so no other subject's session was ever touched by the
   race.

   Proof the reprocessing that actually stands in the DB and on disk today is from the clean restart, not
   the raced attempt: (1) `chb06` was re-uploaded twice more after the kill — a clean 18-file session at
   `19:44:43` that stalled on an unrelated readiness-check bug (fixed at the next restart marker,
   `19:51:07`), then the final clean 18-file session at `19:51:08` that ran through to completion; (2) the
   `.edf` files physically on disk under `web_demo/backend/uploads/chb06/` today are dated
   `2026-09-30 02:51:xx`-`02:53:xx` local (UTC+7) = `2026-09-29 19:51:xx`-`19:53:xx` UTC — inside the
   *third* (`19:51:08`) session's upload window only; none carry a timestamp from the `19:40` raced
   session or the `19:44` stalled session, so nothing from either earlier attempt survived onto disk;
   (3) `szscan.db`'s `subjects` table has exactly one `chb06` row, `created_at = '2026-09-29 20:05:09'`
   (matching the driver log's `chb06: DONE` at `20:05:11` UTC), and its `files` table has exactly 18 rows
   for `chb06` — one per real file, none stale, none duplicated — confirmed by direct query:
   `SELECT * FROM subjects WHERE id='chb06'` → one row; `SELECT COUNT(*) FROM files WHERE
   subject_id='chb06'` → `18`.
2. The relaunched single driver had its own bug: it checked `ready_to_process` exactly once,
   immediately after the last upload POST returned — but a `200` on that endpoint only means the file
   was *accepted*, not that Phase A (which runs in background threads, bounded by
   `_PHASE_A_MAX_CONCURRENCY = 2`) has finished it yet. `chb06` was wrongly recorded as `not_ready` with
   12 of 18 files still mid-Phase-A, and the driver moved on to `chb03` without ever calling Process.
   Caught from the log almost immediately; the driver was stopped, the (again orphaned) `chb06`/`chb03`
   draft directories were deleted the same way, and the script was fixed to poll until every file
   settles to `uploaded`/`error` before judging readiness (and to drop any per-file `error` from the
   session rather than blocking the whole subject on it). All 8 subjects below ran under this fixed
   version, from a clean restart at `chb06`.

**Files per subject, failures and skips — all 8 completed clean.** Re-verified independently for this
addendum, not just taken from the driver's own log: `.edf` counts by listing
`F:/Study/Thesis/Dataset/CHB-MIT/{subject}/*.edf` directly; "Processed OK" by `szscan.db` having exactly
one row per subject in `subjects` and the matching real-file count in `files` with no `error` status
row anywhere (`SELECT subject_id, status, COUNT(*) FROM files GROUP BY subject_id, status` — every
group is `('<subject>', 'View', <real file count>)`, no other status value appears for any subject):

| Subject | EDF on disk | Uploaded | Processed OK | Failed |
|---|---|---|---|---|
| `chb06` | 18 | 18 | Yes | 0 |
| `chb03` | 38 | 38 | Yes | 0 |
| `chb13` | 33 | 33 | Yes | 0 |
| `chb14` | 26 | 26 | Yes | 0 |
| `chb15` | 40 | 40 | Yes | 0 |
| `chb16` | 19 | 19 | Yes | 0 |
| `chb17` | 21 | 21 | Yes | 0 |
| `chb18` | 36 | 36 | Yes | 0 |

**Per-subject wall-clock (upload phase = all POSTs sent through every file settling in Phase A;
process phase = Process click through `done`; UTC throughout):**

| Subject | Upload (s) | Process (s) | Total (s) | Total (m:s) | Started | Done | `pen_mult` | `event_rate_per_day` |
|---|---|---|---|---|---|---|---|---|
| `chb06` | 307.1 | 536.2 | 843.4 | 14:03 | 19:51:08 | 20:05:11 | 2.0 | 37.40 |
| `chb03` | 165.2 | 295.4 | 460.6 | 7:41 | 20:05:12 | 20:12:52 | 2.0 | 44.21 |
| `chb13` | 130.8 | 255.3 | 386.2 | 6:26 | 20:12:53 | 20:19:19 | 2.0 | 48.00 |
| `chb14` | 113.1 | 200.3 | 313.4 | 5:13 | 20:19:19 | 20:24:32 | 2.0 | 94.15 |
| `chb15` | 192.6 | 320.7 | 513.3 | 8:33 | 20:24:33 | 20:33:06 | 2.0 | 88.78 |
| `chb16` | 78.6 | 165.3 | 243.9 | 4:04 | 20:33:06 | 20:37:10 | 2.0 | 31.58 |
| `chb17` | 90.1 | 160.2 | 250.3 | 4:10 | 20:37:10 | 20:41:20 | 2.0 | 53.70 |
| `chb18` | 158.9 | 275.3 | 434.2 | 7:14 | 20:41:21 | 20:48:35 | 2.0 | 40.41 |

Total wall clock for the clean 8-subject run: 19:51:08 → 20:48:35 = **57 min 27 s**. Estimate printed
after `chb06` (measured rate 12.64 s/hour-of-EEG, 213 h of EEG remaining across 7 subjects): finish by
20:50:03 UTC — the run actually finished slightly early, at 20:48:35.

**Peak memory per subject** (external `psutil` monitor, read-only, sampling backend + any
`pipeline_worker.py` subprocess every 5 s to `web_demo/report_handback/part3_v2_memory.csv`; no code or
setting changed to produce this; a sample is attributed to whichever subject the driver had most
recently marked current, so a sample right at a subject boundary can be attributed to either
neighbor — a labeling artifact of the monitor, not a memory-accounting error):

| Subject | Peak backend RSS (MB) | Peak combined (backend+worker) RSS (MB) |
|---|---|---|
| `chb06` | 7916.2 | 10203.9 |
| `chb03` | 7347.9 | 7347.9 |
| `chb13` | 3167.9 | 5403.4 |
| `chb14` | 3088.9 | 4504.1 |
| `chb15` | 3769.7 | 6363.4 |
| `chb16` | 2376.3 | 3540.9 |
| `chb17` | 2510.2 | 3778.8 |
| `chb18` | 3415.5 | 5805.4 |

`chb06` — the subject that OOM'd twice under v1 at concurrency 4 — peaked at ~10.2 GB combined under
v2's concurrency 2, comfortably under this machine's ~16.7 GB total. System-available memory never
dropped into single-digit-percent territory at any sample (spot-checked during the run: ~8 GB free
mid-run at concurrency 2, versus the ~1.4 GB and ~4.4 GB free readings recorded for `chb06` under v1
below).

**AI events per subject** (sanity figure only, from `db.list_events(...)` across each subject's files —
no other number about detection quality; matches the `alert` totals `GET /api/subjects` reports):

| Subject | AI events |
|---|---|
| `chb06` | 104 |
| `chb03` | 70 |
| `chb13` | 66 |
| `chb14` | 102 |
| `chb15` | 148 |
| `chb16` | 25 |
| `chb17` | 47 |
| `chb18` | 60 |

**Reviewed before export?** No. No event was reviewed and no Human event was added to any subject
during this run — confirmed by every file's `status` remaining `View` (never `Viewed`) in the final `GET
/api/subjects` response.

**Export paths:**
- `web_demo/report_handback/tier2/{subject}_events.csv` for each of the 8 subjects (columns:
  `subject,file_name,event_id,onset_s,offset_s,source,review_status`, straight from `db.list_events(...)`
  per file, no reformatting/clipping/splitting).
- `web_demo/report_handback/tier2/files.csv` (columns: `subject,file_name,duration_s,n_windows,status`;
  `n_windows` from `np.load(uploads/{subject}/{stem}.raw.npy, mmap_mode="r").shape[0]`, all 231 rows
  populated, none missing).
- `web_demo/report_handback/part3_v2_memory.csv` — the raw memory-monitor samples behind the peak table
  above.

**Guards:** 4/4, both before this run started and again after it finished (§0).

**State left in place, per instruction:** all 8 subjects' processed data and caches left on disk under
`web_demo/backend/uploads/{subject}/`, no git commit made, nothing deleted after the run.

**Addendum, this session:** checked for a live memory-monitor process to stop, per instruction. Found
none — `part3_v2_memory.csv` stopped growing at `2026-09-29T23:46:55` UTC (last row, no `BACKEND_GONE`
sentinel the monitor's own code writes when it notices the backend die on its own), and the backend PID
it was watching (`9268`, from the driver's own `backend_pid.txt`) is not running either — both were
already gone, apparently together, well before this task started; no process matching `python`,
`mem_monitor`, `driver.py` or `uvicorn` was found anywhere on the host (checked both sandboxed and with
the sandbox disabled). So the backend is **not** still running, contrary to the line above as it read
before this addendum — corrected here rather than left stale. Nothing was killed by this task because
nothing was left to kill. The driver and monitor scripts (`driver.py`, `mem_monitor.py`, and the
superseded `tier2_driver.py` from the discarded v1 second attempt below), plus their run logs, were
moved out of the ephemeral Claude scratchpad and into `web_demo/report_handback/scripts/` (as
`v2_driver.py`, `v2_mem_monitor.py`, `v2_driver_log.txt`, `v1_tier2_driver.py`,
`v1_tier2_driver_progress.log`) so they survive as a record of how this run was actually driven; nothing
was deleted. The scorer was not run.

---

### Superseded: v1 attempt (`szscan-frozen-v1`, discarded in full)

The database was fully emptied (all 8 subjects, including the one below that had finished, `chb03`) and
every subject reprocessed from scratch under `szscan-frozen-v2` above, per Boti's decision recorded in
`CC_PART3_RERUN_V2_PROMPT.md`. The narrative below is kept verbatim for the OOM diagnostics that
motivated the `_PHASE_A_MAX_CONCURRENCY` fix — none of its per-subject results (`chb03`'s DB row, the
partial `chb06` draft) exist anymore.

**Runtime environment (resumed session, 2026-09-29):** the host machine was rebooted between the
`chb06` out-of-memory kill recorded below and this resumption. Following that reboot, the pagefile
was moved: it now lives on `F:` (`F:\pagefile.sys`, 5540 MB allocated) and there is no pagefile on
`C:` at all. `TMP`/`TEMP`/`TMPDIR` were also repointed to `F:/tmp` (previously under `C:`). These are
OS/runtime settings made outside this task, not a build or code change — `web_demo/` itself was
re-verified byte-identical to the frozen tag before resuming (below). Recorded here because they
plausibly affect the out-of-memory risk this section documents for `chb06`.

**Status: interrupted, paused by instruction — not the finished Part 3 report.** Driven per
`CC_REPORT_HANDBACK_PART3_PROMPT.md` / `CC_VERIFY_AND_RUN_PART3_PROMPT.md` at `HEAD`
`4c07a99613f6ba240649cb6ad7ed197fdde18b4c` (`web_demo/` confirmed byte-identical to tag
`szscan-frozen-v1` `66f7c89c4d9931c0895c5efb739289859293af16` — empty `git diff
szscan-frozen-v1..HEAD --stat -- web_demo/`, and all 5 intervening commits touch only
`src/`/`figures/`). Guards were 4/4 immediately before this run started. Left exactly as it
stopped, on instruction — nothing further attempted, nothing deleted or restarted.

**Database emptied how:** `DELETE /api/subjects/{id}` (the real endpoint, which also removes
`uploads/{id}/` on disk) for each of the 8 subjects then in the DB — `chb16, chb17, chb14,
chb18, chb03, chb15, chb06, chb13`. Confirmed after: `GET /api/subjects` → `[]`, and none of
the 8 subject directories remained under `uploads/`.

**Files per subject, failures and skips:**

| Subject | Real `.edf` count on disk | Result |
|---|---|---|
| `chb03` | 38 | **Completed.** All 38 uploaded and processed; committed to the DB (`status: View`, memo `Tier 2 -- frozen build szscan-frozen-v1`). No file failed. |
| `chb06` | 18 | **Interrupted twice, still not in the DB.** First attempt (below): killed mid-Process by the host for low system memory. Second attempt, this resumed session (§"chb06 second attempt, resumed session" below): the driver's own HTTP connection was severed by a Windows socket resource-exhaustion error (`OSError 10055`, "system lacked sufficient buffer space") while uploading file 13 of 18 — a different failure signature from the first kill, but the same underlying low-memory condition, so treated as the same "stop and report" case per instruction. Stopped immediately on this second failure; nothing further attempted. |
| `chb13, chb14, chb15, chb16, chb17, chb18` | 33 / 26 / 40 / 19 / 21 / 36 | Not started. |

**Timing (`chb03`, the one subject that finished):**
- Upload phase (first upload POST → all 38 files `uploaded`): 12:15:12.449 → 12:18:07.360 UTC = **174.9 s**.
- Process phase (Process click → `done`): 12:18:07.371 → 12:30:53.093 UTC = **765.7 s**.
- Total: **940.6 s** (15 min 41 s). Operating point returned: `pen_mult = 2.0`,
  `event_rate_per_day ≈ 44.209`.

**The `chb06` out-of-memory failure:**
- All 18 real files uploaded: 12:30:53.165 → 12:35:39.013 UTC (285.8 s).
- `POST /api/uploads/current/process` sent at **12:35:39.090 UTC**.
- The backend process's last observed activity (`uvicorn.log`'s last line, a routine `GET
  /api/uploads/current` poll) was at **12:38:24.773 UTC** — about **165.7 s** into Process
  (Phase B / PELT running in the `pipeline_worker.py` subprocess) — after which both the
  backend server and this driver script were killed by the host environment with the reason
  "system is running low on memory." No exception, traceback, or `error` field was ever
  recorded by the app itself — the process was killed from outside it.
- **Free memory at the moment of failure: not measured** — this run did not log memory
  during processing, only before starting (not checked) and after the kill. Checked
  immediately after the kill (not the moment of failure — the host had already reclaimed
  memory from the killed processes by then): **11.5 GB free of 16.7 GB total**
  (`wmic OS get FreePhysicalMemory,TotalVisibleMemorySize`), i.e. already recovered, not
  informative about the peak that caused the kill.
- Plausible cause, not confirmed: `chb06` has the longest/largest individual real recordings
  of the 8 subjects (files up to ~170 MB raw EDF each; `CLAUDE.md`'s own reference recording,
  `chb06_01.edf`, is a 4-hour file); Phase A holds up to 4 such files fully in memory at once
  (`upload_manager.py`'s existing `_PHASE_A_MAX_CONCURRENCY = 4` cap), and Phase B's
  subprocess (torch model + adjacency arrays over the whole subject) was running concurrently
  with whatever else this host was doing at the time. **No code was changed and no
  concurrency setting was touched to investigate or work around this** — out of scope for
  this run per instruction.

**`chb06` second attempt, resumed session (2026-09-29, after the reboot in the runtime-environment
note above):**
- Confirmed before starting: `web_demo/` byte-identical to `szscan-frozen-v1` at HEAD `4c07a99`
  (empty `git diff szscan-frozen-v1..HEAD --stat -- web_demo/`; 5 intervening commits all outside
  `web_demo/`, confirmed per-commit via `git show --stat`).
- Found the first attempt's orphaned draft directory already gone under that name; in its place, a
  *different* orphaned draft (`uploads/_draft_5c18049aa2d06234/`, 16 GB, all 18 files through Phase A,
  timestamped ~20 minutes before this session started) with no live session or DB row behind it
  (`GET /api/uploads/current` → 404 at session start) — i.e. a second, independent interrupted attempt
  had already happened between the first kill and this resumption, most likely ended by the same
  reboot that moved the pagefile. Deleted it (plain directory delete; no session existed to close it
  through the API) before starting the driver.
- Started the backend (`uvicorn main:app --port 8000`) and a fresh driver script (same real-HTTP-flow
  method: login, sequential per-file upload POSTs, Process, poll, acknowledge) resuming from `chb06`.
- Uploaded 12 of 18 real files successfully (`chb06_01`–`chb06_10`, `chb06_12`, `chb06_13`; timings
  13:53:48–13:57:56 UTC) — each individually confirmed `status: "uploaded"` server-side, no per-file
  error.
- The 13th upload POST (for `chb06_14`) failed at **13:58:16 UTC**: `requests.exceptions.ConnectionError`
  wrapping `OSError(10055, "An operation on a socket could not be performed because the system lacked
  sufficient buffer space or because a queue was full")`. Free physical memory sampled ~4.5 minutes into
  the run (10 files in) was already down to **1.4 GB of 16.7 GB total**.
- **Unlike the first kill, the backend server itself survived** (`uvicorn` process, same PID, still
  answering requests immediately after) — only the driver's own outbound HTTP connection was severed.
  The live session for `chb06` is intact and resumable (`GET /api/uploads/current` still returns it,
  `ready_to_process: true` for the 12 files present, no `error` field set).
- **A consequence of the app's own existing design, not a bug introduced here:** because no file was
  mid-upload when the connection dropped, the backend's automatic Phase B trigger
  (`upload_manager._maybe_run_phase_b`, fires once every file currently in the session is `"uploaded"`)
  started Phase B on the **partial 12-file set** — `pipeline_worker.py phase_b` was found running
  (PID 5152, ~4.6 GB working set) immediately after the connection loss. This is expected, self-
  correcting behavior: `upload_manager.add_file` resets `phase_b_done = False` on every new file added,
  so resuming by uploading the remaining 6 files (`chb06_14, 15, 16, 17, 18, 24`) will invalidate this
  partial run and re-trigger a fresh Phase B over the full 18-file set before Process is even clicked.
  It was left running, untouched, on the same "stop and report" instruction — not killed, not worked
  around.
- Free memory immediately after the connection loss (Phase B on the partial set still running):
  **4.4 GB of 16.7 GB total**, with the `phase_b` subprocess alone holding ~4.6 GB working set / ~4.9 GB
  private bytes.
- **No code was changed and no concurrency setting was touched.** Left exactly as it stopped: the
  `chb06` session live with 12/18 files uploaded, the partial-set Phase B subprocess running unattended,
  the backend server still up. This second failure — occurring on the very first subject again, even
  after the reboot and pagefile move — is reported rather than retried, worked around, or diagnosed
  further, per instruction.

**Export paths:** none yet — Part 3.3's CSV export has not run; the reprocessing pass across
all 8 subjects is not complete.

**AI events per subject:** not counted yet — deferred to the completed run, so this figure is
reported once, from the final state, not accumulated piecemeal across a resumed run.

**Reviewed before export?** N/A yet — no review action and no Human event was added to
`chb03` or anywhere else during this run.

**Next step, on instruction (superseded by the second interruption above — this is now the
live state to resume from, not the original one):** the `chb06` session is live with 12/18
files uploaded and a partial-set Phase B computation running; resuming means uploading the
remaining 6 files (`chb06_14, 15, 16, 17, 18, 24`) to the *same* live session (do not discard
it and do not delete `uploads/_draft_1ce25dd8a7bbbbec/`), which will self-correct the partial
Phase B run, then Process as usual — `chb03` stays as already processed either way. This is
the second time the same out-of-memory-class failure has hit `chb06` specifically, now after a
reboot and pagefile move intended to address exactly this — stop and report again rather than
lowering `_PHASE_A_MAX_CONCURRENCY` or changing any other code — that would be a build
change requiring a new tag and a full re-run from an empty database, which is Boti's call.

---

## 4. Timing

Added by `CC_PART2_PART4_PROMPT.md`, on the same `szscan-frozen-v2` checkout as §2/§3 above
(no code changed for this section either).

### 4.1 Hardware and software (Part 4.1)

- **CPU:** Intel(R) Core(TM) i5-8250U CPU @ 1.60GHz — 4 physical cores, 8 logical processors
  (`Get-CimInstance Win32_Processor`).
- **RAM:** 17,069,273,088 bytes total (≈ 15.9 GiB / 17.07 GB, `Get-CimInstance
  Win32_ComputerSystem`).
- **OS:** Microsoft Windows 10 Pro, version 10.0.19045, 64-bit (build 19045,
  `Get-CimInstance Win32_OperatingSystem`).
- **Python:** 3.11.9. **PyTorch:** 2.12.0+cpu. **NumPy:** 2.4.4 (all three: the system
  Python install used throughout this project, `C:\Users\Dell Latitude
  3590\AppData\Local\Programs\Python\Python311\python.exe` — the repo's own `venv` lacks
  `ruptures`/other deps needed by `pipeline_demo.py`'s import chain).
- **Torch device:** CPU, confirmed `torch.cuda.is_available() == False` — matches
  `pipeline_demo.py`'s hardcoded `device: str = "cpu"` default at every call site (§1.1
  already confirmed no code path overrides this).
- **Runtime environment:** pagefile on `F:` (`F:\pagefile.sys`, 2432 MB allocated,
  `Get-CimInstance Win32_PageFileUsage`), `TMP`/`TEMP` = `F:\tmp` — same as §3's runtime
  environment.

### 4.2 Repeated timing on one reference recording (Part 4.2, 4.4)

**Reference recording:** `chb06_01.edf` — the four-hour recording behind `CLAUDE.md`'s
existing "9.76 s per hour of EEG" figure (`web_demo/BUILD_PROGRESS.md` §4 / §1: "9.76 s/hour
final measured timing on `chb06_01.edf`"). Measured here at 4.0075 h per run (`n_windows *
4 s`, identical every run since the same file is re-read each time).

Processed **5 times**, calling `pipeline_demo.py`'s own instrumented functions directly —
`process_file_phase_a()`, `process_subject_phase_b(..., timing=...)`,
`process_subject_events(..., timing=...)` — the same functions and the same `timing=` dicts
`measure_stage_timing.py` already uses (`CC_STAGE_TIMING_REPORT.md`), just pinned to this one
file instead of a whole subject, and using `process_subject_events()` (the live
`FIXED_PEN_MULT`/`FIXED_MAG_PCT` path) rather than the old, no-longer-live
`calibrate_operating_point()` grid search that script's default still runs. Never went through
the database or HTTP (`cache_dir=None` on `process_file_phase_a`, so nothing touched
`web_demo/backend/uploads/` either); the backend was not running at the time (§3's own addendum
already found it dead). Script: `web_demo/report_handback/scripts/measure_timing_chb06_01.py`
(written outside `web_demo/` proper during the run, copied here afterward as a record — no
`web_demo/` source file was added or changed).

**Command:**
```
"C:\Users\Dell Latitude 3590\AppData\Local\Programs\Python\Python311\python.exe" web_demo/report_handback/scripts/measure_timing_chb06_01.py
```

Raw per-run/per-stage seconds: `web_demo/report_handback/timing_repeated.csv` (columns
`run,stage,seconds,eeg_hours`, 5 runs × 7 stages). Sum-of-buckets vs. the independent outer
wall-clock total agreed to within 0.18% on every run (e.g. run 1: 85.95 s summed vs. 86.09 s
total) — no run flagged.

| Stage | Median (s/h) | Min (s/h) | Max (s/h) |
|---|---|---|---|
| Phase A: ingest + filter (`process_file_phase_a`) | 2.462 | 2.154 | 3.232 |
| Phase B: CAR/wPLI/AEC/top-k + band powers | 14.177 | 12.572 | 14.794 |
| Phase B: build_batch + GAE encoder + joint_score | 0.620 | 0.548 | 0.759 |
| Phase B: compute_gamma_scores_batch | 3.752 | 3.624 | 4.098 |
| Phase B: subject stats + checkpoint load + LedoitWolf + robust-z fits | 0.622 | 0.506 | 0.655 |
| Stage 2: `detect_events` (fixed operating point) | 0.312 | 0.266 | 0.380 |
| **Total (outer wall-clock)** | **21.908** | 21.483 | 22.550 |

Not compared against `CLAUDE.md`'s "9.76 s/hour" figure here — that comparison, if wanted,
belongs to the report, not this handback (per this section's own instruction not to editorialize);
recorded factually: this measurement runs at roughly 2.2× that figure on this machine today,
under `CLAUDE.md`'s own documented ~5× run-to-run variance caveat for exactly this kind of
number.

### 4.3 Per-file timing of the Tier 2 run (Part 4.3)

Checked `web_demo/backend/uvicorn.log` (6 lines, a startup banner from an unrelated session —
no per-request log lines at all), `szscan.db`'s schema (`files` table columns: `id,
subject_id, filename, start_time, duration_seconds, status` — no timing column), and the two
live call sites that matter (`web_demo/backend/pipeline_worker.py:31,60`,
`process_subject_phase_b_from_paths(...)` / `process_subject_events(scores)`) — neither passes
a `timing=` dict on the live path. **Per-file per-stage timing was not logged during the
`szscan-frozen-v2` Tier 2 run.** Written as instructed: `web_demo/report_handback/
timing_tier2.csv` contains the single line `not logged`.

**End-to-end rate, computed instead (no re-run):** total wall-clock across all 8 subjects,
upload through done, summed from §3's own per-subject table: 843.4 + 460.6 + 386.2 + 313.4 +
513.3 + 243.9 + 250.3 + 434.2 = **3445.3 s** (the same run's start-to-finish clock span,
19:51:08→20:48:35 UTC, is 3447 s — the 1.7 s gap is the acknowledge/next-subject-start
overhead between subjects, already visible in §3's own log). Total EEG hours, summed directly
from `web_demo/report_handback/tier2/files.csv`'s `duration_s` column over all 231 files:
**279.3881 h**.

**End-to-end rate, including upload: 3445.3 s / 279.3881 h ≈ 12.33 s per hour of EEG**
(12.34 s/hour using the 3447 s clock-span figure instead — same to 2 significant figures).
This sits *below* §4.2's single-file, processing-only rate (21.9 s/hour median) despite
including upload time on top of processing — consistent with `_PHASE_A_MAX_CONCURRENCY = 2`
letting Phase A overlap across files within a subject (§3), and with `CLAUDE.md`'s own
run-to-run variance caveat; not investigated further here, reported factually per instruction.
