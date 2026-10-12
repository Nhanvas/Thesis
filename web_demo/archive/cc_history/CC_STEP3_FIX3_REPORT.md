# CC_STEP3_FIX3_REPORT.md — Step 3 fix round 3: unlock Project ID / Memo until PROCESS

Scope: `web_demo/CC_STEP3_FIX3_PROMPT.md`. This is a deliberate UX decision change, not a bug fix.
Rounds 1–2 were not re-touched except where this round's design genuinely required it (see the
architecture decision below — `start_process`'s signature and the upload storage path had to
change; nothing else from rounds 1–2 was modified). Quick regression check at the end confirms
both rounds still hold.

---

## What was coupling Project ID to upload/storage time

1. **`CreateNewPanel.jsx`** — both inputs were `disabled={Boolean(session)}`, and their `value`
   read from `session.project_id`/`session.memo` once a session existed, `projectId`/`memo` (local
   state) only before. So the instant the first file was added and a backend session existed, the
   fields became read-only and permanently reflected whatever value was used to create the session.
2. **`upload_manager.py`** — `UploadSession.project_id` was set once at `start_session()` and never
   read again from anywhere else, **except** `add_file()`, which used it directly as the on-disk
   storage directory name: `dest_dir = UPLOAD_DIR / session.project_id`. So the literal Project ID
   text was baked into the filesystem path of every uploaded file and its `.filtered.npy` Phase A
   cache the moment the first file landed — there was no way to let the ID change afterward without
   either silently orphaning already-uploaded files under a stale directory name, or doing a
   filesystem rename keyed by a value the user could still edit at any moment (a moving target).
3. **`start_process()`** took no `project_id`/`memo` arguments at all — it wrote
   `session.project_id`/`session.memo` (whatever they'd been since session creation) straight to
   `db.create_subject_with_files()` with no re-validation at that point.

The early allowlist check in `start_session()` (unchanged, still fires the first time a file is
added under an obviously-invalid ID) was never the problem this round is about — it only gates
*session creation*, and doesn't prevent editing the field afterward. The prompt explicitly allows
keeping it as a UX nicety, so it's untouched.

## Architecture decision (prompt's point 3)

Upload storage is now keyed by a new internal `UploadSession.session_id` (`secrets.token_hex(8)`,
generated once at session creation, immutable for the session's lifetime) instead of the mutable
Project ID text:

- `add_file()` now writes into `UPLOAD_DIR / f"_draft_{session.session_id}"` (via a new `_draft_dir()`
  helper) — completely decoupled from whatever the Project ID field currently says.
- **Project ID is bound for good only inside `start_process()`**, which now takes `project_id`/`memo`
  as arguments (whatever the frontend sends at the exact instant PROCESS is clicked) instead of
  reading them off the session. It validates against `db.ALLOWED_SUBJECTS` first; only on success
  does it write `session.project_id = project_id` / `session.memo = memo` and set
  `session.processing = True`. On failure, nothing is touched — no rename, no lock, session keeps
  whatever it had, files stay listed, caller gets `REJECTED_SUBJECT_MESSAGE` (422) and can retry.
- A new `_finalize_draft_dir()` relocates `_draft_{session_id}/` to the conventional
  `uploads/{project_id}/` path (the layout `CC_STEP3_REPORT.md §3` already documented as what
  Step 4+ will expect) once — and only once — `phase_b_done` is confirmed inside
  `_wait_phase_b_then_process` (added in round 2), i.e. only after the Phase B worker subprocess
  has fully finished reading every file under the draft directory, so the move can never race a
  still-open file handle. Nothing downstream of that point (`_run_process`, the PELT worker, the DB
  write) reads file paths off disk again — verified by reading `_run_process`: it only uses
  in-memory `scores` arrays and `phase_a.start_time`/`duration_seconds` metadata, never a path — so
  no other code needed updating for the rename.

This was not a forced/fragile patch — the existing round-2 `_wait_phase_b_then_process` wait point
was already the one place guaranteed to run after all file I/O for the draft had settled, which is
exactly what a safe rename needs.

**Frontend side:** `CreateNewPanel.jsx`'s Project ID/Memo inputs now always read/write local
`projectId`/`memo` state (never `session.project_id`), with `disabled` removed entirely. A
`hydratedRef`-guarded `useEffect` seeds that local state from `session.project_id`/`memo` exactly
once, the first time a session becomes visible (needed only to restore a session correctly after a
page reload — `DatabaseScreen`'s existing restore-on-mount path — since otherwise a reload would
show an empty field even though a real draft with files exists). After that one-time seed, the
poll's session snapshots never touch the input again, so nothing overwrites what the user types.
`handleProcess()` now calls `processUpload(projectId.trim(), memo)`, sending exactly what's in the
fields at click time; `api.js`'s `processUpload` and `main.py`'s `/api/uploads/current/process`
were extended to carry that payload through to `um.start_process`.

---

## Verification (`claude-in-chrome`, real browser + backend)

**1. Editable throughout, including while Phase A/B ran in the background.** Started a session for
`chb06` (via the backend, then restored into the browser the same way rounds 1–2 did — the
CHB-MIT files are ~170 MB each, too large for the browser tool's own file-picker upload path, so
the actual bytes were POSTed directly to the same endpoint the browser's file input calls; the
browser then drove and observed every subsequent step), uploaded `chb06_01.edf`. Reopened the panel
in the browser: field showed the hydrated `chb06`/memo, file already `✕`. Triple-clicked the
Project ID field and retyped `chb99typo` — it accepted the edit and **held it through 3+ seconds of
the background poll** (two full 1.5 s poll cycles) without being reverted. Confirms the field is
genuinely live-editable, not just visually unlocked.

**2. Changed to an invalid ID, clicked PROCESS, confirmed rejection.** With `chb06_01.edf` already
`✕` and Project ID showing `chb99typo`, clicked PROCESS. Got the exact full-panel toast:
> This demo is restricted to the held-out test subjects.

Backend snapshot immediately after: `{"project_id": "chb06", ..., "ready_to_process": true, ...}` —
unchanged from before the click (the rejected value was never bound), and `GET /api/subjects`
returned `[]` — no subject created. Clicked "Back": returned to the normal form, file still listed,
PROCESS still enabled, and the Project ID field still showed the invalid `chb99typo` text (local
state untouched by the rejection) so it could be fixed in place.

**3. Fixed the ID and clicked PROCESS again — full success.** Retyped `chb06`, clicked PROCESS: the
full-panel "Processing subject — combining files and detecting change points..." state appeared,
resolved to "Upload Complete!", and the Database table showed:

| ID | No. files | Start date | Duration | Alert | Status | Memo |
|---|---|---|---|---|---|---|
| chb06 | 1 files | 2060.01.26 19:08:32 | 04:00:27 | 7 | ○ View | round3 editability test |

— correctly under the *corrected* `chb06`, not the rejected `chb99typo`. Confirmed on disk too:
`web_demo/backend/uploads/` contained only `chb06/` and `_work/` afterward — no leftover
`_draft_<hex>` directory, no `chb99typo` directory. Deleted the test subject and cleared `uploads/`
afterward (same convention as rounds 1–2).

**4. Rounds 1–2 regression re-check (not a full re-test).**
- Bug 1 (auto-close): opened a fresh draft, typed a Project ID, scrolled, waited 8 s — stayed open,
  value intact.
- Bug 2 (overlay): `document.querySelector('main > div').getBoundingClientRect().width` measured
  identical (1318 px) with the panel open and closed.
- Round 2 (PROCESS gates on upload completion, not Phase B): unchanged code path — `snapshot()`'s
  `ready_to_process` condition and `_wait_phase_b_then_process`'s wait-then-run structure were not
  touched this round (only wrapped with the new validation/rename steps described above), and this
  round's own tests 1–3 already exercised a real click-through PROCESS cycle successfully, so the
  mechanism is confirmed still working end-to-end.

**5. Guards + git status.**
```
pytest web_demo/backend/tests/test_guards.py -v
web_demo/backend/tests/test_guards.py::test_guard_no_build_timeline_masked PASSED
web_demo/backend/tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED
web_demo/backend/tests/test_guards.py::test_guard_no_labeled_npy PASSED
web_demo/backend/tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED
4 passed in 2.37s
```
```
git status --short
 M .gitignore
 M tables/tables_ch2.md
 M web_demo/backend/db.py
 M web_demo/backend/main.py
 M web_demo/backend/pipeline_demo.py
 M web_demo/frontend/src/api.js
 M web_demo/frontend/src/components/icons.jsx
 M web_demo/frontend/src/screens/DatabaseScreen.jsx
?? docs/VERIFIED_CORRECTIONS.md
?? web_demo/CC_STEP3_FIX2_PROMPT.md
?? web_demo/CC_STEP3_FIX2_REPORT.md
?? web_demo/CC_STEP3_FIX3_PROMPT.md
?? web_demo/CC_STEP3_FIX_PROMPT.md
?? web_demo/CC_STEP3_FIX_REPORT.md
?? web_demo/CC_STEP3_REPORT.md
?? web_demo/backend/pipeline_worker.py
?? web_demo/backend/upload_manager.py
?? web_demo/frontend/src/components/ConfirmDialog.jsx
?? web_demo/frontend/src/screens/CreateNewPanel.jsx
```
This round's actual edits: `web_demo/backend/upload_manager.py` (session_id, `_draft_dir`,
`start_process` signature + validation, `_finalize_draft_dir`) and `web_demo/backend/main.py`
(`ProcessRequest` body model) — both already-untracked files from Step 3, so neither shows as a new
`M` line; and `web_demo/frontend/src/screens/CreateNewPanel.jsx` + `web_demo/frontend/src/api.js`,
which do show as `M`/already-tracked-modified from prior rounds. Nothing outside `web_demo/backend`
and `web_demo/frontend` was touched.

## Stop condition

Per the prompt: not proceeding to Step 4. Project ID/Memo are editable for the panel's entire open
lifetime, the allowlist check is authoritative only at PROCESS-click time (verified with both a
rejection and a subsequent successful correction under the same files), and rounds 1–2 still hold.
