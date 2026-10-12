# CC_STEP3_REPORT.md — Step 3: Create new → upload → Process → subject appears in the table

Scope built: `DEMO_BUILD_HANDOFF.md §6` row 3, per `CC_STEP3_PROMPT.md`. Full create→upload→process→
appears-in-table cycle works end to end, verified repeatedly via direct API calls against the real
pipeline on real CHB-MIT files (chb06, chb13) — 1, 2, 3, and 4 files per subject, in one and multiple
`curl` sessions. Frontend builds cleanly (`npm run build`); I did not visually pixel-compare it against
`UI/A1a`–`A4b` myself — that comparison is explicitly yours to do, not something to describe in text.

---

## 1. Phase A/B split (§1 of the prompt)

Implemented exactly as the prompt resolved it, in `pipeline_demo.py`:

- **Phase A** (`process_file_phase_a`): open the 18 common channels, bandpass+notch filter the whole
  recording once, cut into 4 s windows. No z-scoring, no adjacency, no model. Runs the moment one file's
  upload lands, per file, in a background thread. Cheap — a ~1 h file takes ~3.5 s, a 4 h file ~15-20 s
  (dominated by `mne`/`scipy`, no `torch`).
- **Phase B** (`process_subject_phase_b`): runs once all currently-listed files have finished Phase A.
  Concatenates every file's raw filtered windows, fits z-score mean/std **and** the `LedoitWolf` cov for
  `zlatent` on that combined set, then runs CAR → adjacency → band powers → GAE → zrecon/zlatent/zgamma
  **per file** using those subject-wide stats. Robust-z: per SPEC §1.6a's own table this is *not* a
  divergence (thesis already fits it on the whole available window set) — so its median/MAD is *also*
  fit subject-wide (on the concatenated per-branch raw arrays) and then applied per file, before the
  per-file ensemble sum. Both `# TODO(step3)` markers are gone; the comments at each step explain why
  the fit happens there.

Both TODOs removed, replaced with the reasoning above inline.

## 2. Operating-point calibration (§2) — O1

- Target read live from `src/retrain/fp_budget_operating_point.py`: `BUDGETS["balanced"] = 40.0` FP/day.
  Never hardcoded.
- Grid reused, not invented: `src/retrain/final_eval.py`'s `DEFAULT_PENS = [0.3, 0.5, 1.0, 2.0, 5.0, 10.0]`
  (the same grid `fp_budget_operating_point.py` itself depends on via `final_eval as FE`).
- `min_mag_pct` left at `cpd_pipeline_v14.detect_events`'s own default (60) — untouched, no reason found
  to change it.
- For each `pen_mult` in the grid: run `detect_events()` on the subject's whole concatenated timeline,
  compute `events/24h` over the subject's total recorded hours (label-free, whole-recording-as-denominator
  approximation — same reasoning SPEC §1.6a already uses for the low-prevalence argument), pick the
  `pen_mult` whose rate is closest to 40/day.

**Measured results** (real pipeline, real CHB-MIT files, this run):

| Subject | Files | Total windows | Chosen `pen_mult` | Resulting rate |
|---|---|---|---|---|
| chb06 | chb06_16, chb06_17 (2 files, ~4.85 h) | 4357 | 2.0 | 34.7 FP/day |
| chb13 | chb13_05, chb13_06, chb13_07 (3 files, 3 h) | 2700 | 5.0 | 48.0 FP/day |

Both land within ~20% of the 40/day target on a small sample (a few hours) — reasonable given how few
windows a 3-5 hour recording gives the label-free rate estimator to work with. Neither produced zero
events on any grid value, satisfying HANDOFF §8's "must not produce nonsense" check for this step. I did
not run every one of the 8 allowlisted subjects end-to-end (would take a while for the demo's real 15-20+
file subjects) — worth doing once as a batch before the defense, per SPEC §1.7's cache-building step
(still Step 9, not this one).

## 3. Where uploaded files live

`web_demo/backend/uploads/{project_id}/{filename}.edf` (real filenames, not renamed), plus a sibling
`{filename}.filtered.npy` cache (Phase A's output — see §5 below for why) and a `_work/` subfolder for
short-lived worker I/O files. All gitignored (added `web_demo/backend/uploads/` to the root `.gitignore` —
the one file this step touched outside `web_demo/`, and it's a one-line addition to an existing
web_demo-specific block, not new unrelated content). Files are **not** deleted after Process — kept for
Steps 4+ (Analysis screen needs the real EDFs to render waveforms).

## 4. Project ID = subject ID (§3)

Followed as resolved: the typed Project ID is validated directly against the 8-subject allowlist and
becomes the DB's `subjects.id`. Uploaded filenames are independent — no textual match is enforced or
warned about (I judged the "lightweight sanity check" as unnecessary complexity for this step; easy to
add later if wanted).

## 5. A finding that changes how file order/dates are derived — flagging per the prompt's request

The prompt's §3 assumed `edf_order.py` would be relevant for **display** ordering. Once real uploaded
EDF binaries are involved (not just `chb*-summary.md` text), I found something that changes this:

`raw.info['meas_date']` (MNE's parsed EDF header field) gives a **full datetime**, not just a
time-of-day — confirmed on real files:

```
chb03_24.edf 2075-09-03 16:39:05+00:00
chb03_25.edf 2075-09-03 15:38:57+00:00   <- earlier real timestamp, later filename number
```

This is exactly the chb03_24/25 clock anomaly `edf_order.py`'s docstring cites as its reason to exist —
but `edf_order.py` was built to work around the *text-only* `chb*-summary.md`, which has no date field
(only `HH:MM:SS`), forcing its "swap only if the gap is small" heuristic. The real EDF header has no such
gap: sorting files directly by `meas_date` handles chb03_24/25 correctly with zero heuristics and zero
dependency on the external summary directory at runtime.

**What I did:** `process_file_phase_a` reads `start_time` straight from `raw.info['meas_date']`; `db.py`
stores it as the file's ISO datetime and sorts a subject's child rows by it directly. `edf_order.py` is
untouched and unused by this step's code path — it satisfies HANDOFF §3's "keep it, don't rewrite it,"
but nothing calls it yet.

**This is a real deviation from what the prompt assumed, flagged rather than silently decided:** if you'd
rather every date/ordering decision in the demo visibly route through `edf_order.py` (e.g. for
consistency, or because the module's heuristic is wanted as a deliberate second line of defense even
though the raw header already has the date), say so and I'll wire it in instead — it's a straightforward
swap, not a redesign, since `db.py` only needs *a* per-file start timestamp to sort and display.

## 6. Upload/processing architecture — the actual hard problem this step ran into

Not anticipated by the prompt, and the majority of this step's debugging time: **running the GAE/PELT
pipeline from inside the FastAPI/uvicorn process reliably hangs at 0% CPU on this Windows dev machine.**
Reproduced with both a plain `threading.Thread` and a `concurrent.futures.ProcessPoolExecutor` worker —
both hang indefinitely, no exception, no CPU use, only when launched from inside the uvicorn-hosted
process. The identical call in a plain, non-uvicorn Python process (a `python script.py` run directly)
never hangs, including a `ProcessPoolExecutor` there.

**Fix:** Phase B and stage-2 Process now run via `subprocess.Popen` (see `pipeline_worker.py`), launching
a genuinely separate, independently-created OS process — not something `multiprocessing`'s spawn
bootstrap or `asyncio`'s loop machinery ever touches. This has been reliable across every test since.
Phase A (no `torch`, just `mne`/`scipy`) never showed the hang and stays a plain background thread, which
is also what keeps its cooperative "stop this upload" cancel flag possible (a subprocess wouldn't share
that memory).

Large arrays never cross a process boundary directly — Phase A writes its filtered windows to a sibling
`.npy` file and the subprocess is handed the *path*, not the array (an earlier attempt passing the array
through `ProcessPoolExecutor`'s call queue directly did not by itself explain the hang — that hung even
with a single small file — but keeping the IPC payload to paths and a few floats/JSON is also just
good hygiene here and rules out a second, unrelated known Windows multiprocessing pitfall).

**One remaining intermittent symptom, mitigated but root cause not fully confirmed:** rarely, a file
finishing Phase A did not itself trigger the Phase B launch check even though every file was already
`uploaded` — no exception logged, and manually re-running the exact same check immediately proceeded
correctly. I added a cheap safety net: `GET /api/uploads/current` (which the frontend already polls every
~1.5 s) re-runs the same idempotent, lock-guarded trigger check on every poll (`upload_manager.poll_tick`).
This bounds the worst case to one poll interval regardless of the root cause, verified against the exact
scenario that failed without it. I'm flagging this the way Step 1's UI-file mystery was flagged in
`BUILD_PROGRESS.md §6`: mitigated and holding up under repeated testing, cause not fully nailed down.

## 7. Everything else in scope

- **Allowlist rejection**: `This demo is restricted to the held-out test subjects.` — verified via curl
  (`chb01` → 422 with this exact text; `chb06` → 200).
- **File rejection**: `File rejected — unsupported format or channel configuration.` — verified with a
  non-`.edf` file. A real EDF missing the 18 common channels hits the same message via
  `preprocessing.open_edf` returning `None` (code path reviewed, not separately re-tested with a
  malformed real EDF on hand).
- **Per-file icons**: spinner-with-stop-square while Phase A runs, ✕ once uploaded — both wired to the
  same `DELETE /api/uploads/current/files/{filename}` endpoint (cancel vs. remove, based on current
  status), per the prompt's reading of SPEC §5.5.
- **Process button gating**: disabled until every listed file is `uploaded` **and** Phase B has finished
  (`ready_to_process`) — a strictly stronger condition than the mockup's literal wording, intentionally,
  since Process needs Phase B's scores to exist.
- **Full-panel loading copy**: exact `SZSCAN_DESIGN_v2.md §8` wording — "Processing subject — combining
  files and detecting change points..." — not the mockup's illustrative "Please wait for processing…"
  placeholder text (the mockup's copy is UI-visual-locked for layout, not this specific string; the
  design doc's wording table is the more specific authority for exact copy per that same doc's own
  stated purpose).
- **Minimize-to-toast**: "Create New (draft)" / "Processing..." labels, backend work is a module-level
  singleton so it runs regardless of what the frontend shows — verified by leaving a session running and
  polling with the panel logically "closed."
- **Single-subject concurrency lock**: verified — starting a second session while one is active returns
  409 with the exact SPEC §5.5 message; discarding an idle draft frees the lock immediately.
- **Delete**: subject-level only (`DELETE /api/subjects/{id}`); selecting a file row and clicking Delete
  is a no-op in the frontend (checked in `handleDeleteClick`), never reaches the backend. One confirmation
  dialog, same wording (`Are you sure you want to delete this process?`) regardless of subject state.
- **Search**: implemented client-side against the already-fetched subject list (each subject now arrives
  with its child files embedded, from `db.py`'s `list_subjects()` — no extra endpoint needed). Filename
  match → that subject only, force-expanded, siblings hidden. Subject-name match → full subject,
  force-expanded. No match → `No results for '...'`. Only runs on submit (button click or Enter), not per
  keystroke.
- **Open**: selects+highlights the row correctly; clicking it shows a small inline note
  ("Opening the Analysis screen isn't implemented yet (Step 4)") instead of navigating — **explicit
  stub, Analysis screen is Step 4+ scope, not built.**
- **DB schema**: `events` stores `file_id`, `source`, `onset_sec`, `offset_sec`, `review_status`
  (`'Unseen'` for every AI event created here, matching SPEC §5.3 — nothing has been reviewed yet),
  `comment`. Alert is computed live from this table (`NOT (source='AI' AND review_status='Reject')`),
  Status derived from `files.status` per SPEC §5.2. No migration should be needed for Steps 5-7's review
  UI.

## 8. Deviations / calls made that weren't fully spec'd (flagging, not hiding)

- **Closing the Create New panel (× button) while idle discards the draft** (uploaded-but-unprocessed
  files and their Phase A work) without a confirmation dialog. SPEC only specifies a confirmation for
  deleting an already-*created* subject (§5.6); it's silent on discarding an in-progress draft. If you'd
  rather this ask for confirmation too, easy to add.
- **The "Upload Complete!" screen after Process finishes** (matching `UI/A2b`'s literal checkmark +
  progress-bar visual) requires an explicit "Done" click to close and refresh the table, rather than
  auto-dismissing. SPEC's prose doesn't describe this intermediate screen at all (it jumps straight from
  "Process finishes" to "Database shows the new subject"); `UI/A2b` shows it, so I kept it as a locked
  visual but made it require a click since nothing pins its duration.
- **Project ID and Memo lock (become read-only) once the first file starts uploading.** Not specified
  either way; simplest and avoids a mismatch between what's typed and what's already committed to the
  backend session.

## 9. Guard check + git status

```
pytest web_demo/backend/tests/test_guards.py -v
```
→ **4 passed**, both before any Step 3 edits and again after (ran three times across this session, most
recently right before writing this report). This step touches real pipeline execution and event storage
for the first time — reviewed deliberately: no labels, no `build_timeline_masked`, no forbidden `.npy`
arrays, no writes outside `web_demo/` (uploads live under `web_demo/backend/uploads/`).

`git status`: nothing under `web_demo/UI/` shows modified. Outside `web_demo/`, only the root
`.gitignore` changed (one line, `web_demo/backend/uploads/`, inside its existing web_demo block) — no
other files outside `web_demo/` were touched by this step. (`tables/tables_ch2.md` and
`docs/VERIFIED_CORRECTIONS.md` showing in `git status` predate this session — Project #1's work, not
mine.)

New/changed files, all under `web_demo/`:
```
backend/pipeline_demo.py       rewritten: phase A/B split, operating-point calibration, stage-2 events
backend/pipeline_worker.py     new: subprocess CLI entry points for Phase B / Process
backend/upload_manager.py      new: the Create New panel's server-side session/state machine
backend/db.py                  extended: create-subject-with-files, events, real Alert/Status, search-
                                friendly embedded files, delete
backend/main.py                extended: upload/process endpoints, subject delete
frontend/src/api.js            extended: upload/process client calls
frontend/src/screens/CreateNewPanel.jsx   new
frontend/src/components/ConfirmDialog.jsx new
frontend/src/screens/DatabaseScreen.jsx   rewritten: real table, search, selection, Create New wiring
frontend/src/components/icons.jsx         extended: chevrons, upload/stop/file/warning/status icons
.gitignore                     +1 line: web_demo/backend/uploads/
```

`npm run build` in `web_demo/frontend` succeeds cleanly (213 KB JS bundle, no errors).

## 10. Start commands

```
# backend (from repo root)
cd web_demo/backend
uvicorn main:app --reload --port 8000

# frontend (separate terminal, from repo root)
cd web_demo/frontend
npm run dev
```
Open the printed Vite URL (typically `http://localhost:5173`), log in with the existing dev credentials
in `web_demo/backend/.env`. The DB is currently empty (`szscan.db` and `uploads/` were reset after my own
testing) so you'll see the real `UI/A0a`-style empty state and can run a full create→upload→process cycle
yourself. `chb06` and `chb13` are known-good from this session's testing (a few files each is enough to
see the cycle; the full subject upload will take longer — Phase A is a few seconds per file, Phase B is
roughly the ~15-20 s/hour-of-EEG rate from Step 1, run once per subject).

## Stop condition

Per the prompt: not starting Step 4 (Analysis screen). The `Open` button is a confirmed stub. Please
compare the running app against `UI/A1a`–`A4b` before we move on.
