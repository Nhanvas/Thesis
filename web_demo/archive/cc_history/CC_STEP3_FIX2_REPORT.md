# CC_STEP3_FIX2_REPORT.md — Step 3 fix round 2: PROCESS button never enables

Scope: `web_demo/CC_STEP3_FIX2_PROMPT.md`. Round 1's two bugs (panel auto-closing, overlay-vs-push
layout) were not re-touched — quick regression check at the end confirms both still hold.

---

## Root cause

`web_demo/backend/upload_manager.py`, `UploadSession.snapshot()` (the only place `ready_to_process`
is computed — the frontend just renders `disabled={!session?.ready_to_process}` in
`CreateNewPanel.jsx:253` verbatim):

```python
"ready_to_process": (
    len(self.files) > 0
    and self.phase_b_done          # <-- this line
    and all(f.status == "uploaded" for f in self.files.values())
    and not self.processing
),
```

`self.phase_b_done` is Phase B — the subject-wide z-score/`LedoitWolf` fit and per-file GAE scoring
that has to run once before PELT, an internal computation-ordering requirement from
`CC_STEP3_PROMPT.md §1`/SPEC §1.6a, not something SPEC §5.5 ever says should gate the button. SPEC
§5.5 literally says "Disabled cho tới khi mọi file đã tải xong" — disabled until every file has
finished *uploading*. Phase A (per-file filtering, flips a file to `status: "uploaded"`, i.e. the ✕
icon) and Phase B (subject-wide, only starts once every file is `uploaded`, takes longer — it has
to wait for and then process the *whole* concatenated recording) are two different moments in time;
this line was conflating them, so with a small, fast subject Phase B usually raced ahead of the
user noticing, but for anything where Phase B takes a real amount of time (more files, longer
recordings) the button visibly sits disabled after every file already shows ✕ — exactly what the
author saw.

**Was this a regression from round 1's `hasSession` fix?** No — traced explicitly, not assumed.
`ready_to_process` is computed entirely inside `upload_manager.py` (backend), independent of
anything in `DatabaseScreen.jsx`. Round 1 changed only *when the frontend polls*
(`GET /api/uploads/current`, gated on `hasSession` instead of `panelMode`); it never touched what
that endpoint returns, and `poll_tick` → `_maybe_run_phase_b` (the Phase B trigger safety net) runs
identically either way once a session exists — `_require_session` 404s before `poll_tick` is ever
reached when there's no session, so the old `panelMode`-gated polling never actually reached
`poll_tick` any more often than the new `hasSession`-gated one does once a real session exists. The
`phase_b_done` coupling in `ready_to_process` predates round 1 entirely (it was in the original
Step 3 build, `CC_STEP3_REPORT.md §7` "Process button gating" describes it as an intentional, if
wrong, choice: *"a strictly stronger condition than the mockup's literal wording, intentionally,
since Process needs Phase B's scores to exist"*). That reasoning is what this round corrects: Phase
B's scores being needed to *run* PELT doesn't mean the button must stay disabled until they exist —
clicking PROCESS is what should wait for them, behind the loading screen, not the button itself.

## Fix

`web_demo/backend/upload_manager.py`:

1. **`snapshot()`** — `ready_to_process` no longer checks `phase_b_done`; it's now "files exist, all
   of them are `uploaded`, not currently processing, not already done." This is the actual SPEC
   §5.5 condition.
2. **`start_process()` / new `_wait_phase_b_then_process()`** — clicking PROCESS while Phase B is
   still running can no longer fall through to the old "Not all files have finished uploading yet."
   409 (that check now only looks at upload status, which is already satisfied). Instead:
   `start_process()` validates upload status, sets `session.processing = True` immediately (which is
   what flips the frontend to the existing full-panel "Processing subject — combining files and
   detecting change points..." state — no frontend change needed, `CreateNewPanel.jsx`'s
   `session?.processing` branch already existed), and hands off to a new background thread,
   `_wait_phase_b_then_process`, which nudges `_maybe_run_phase_b` (idempotent — the same safety net
   `poll_tick` already uses) and polls `session.phase_b_done` every 0.3 s. Once Phase B finishes (or
   immediately, if it already had), it calls the existing `_run_process` exactly as before. If Phase
   B itself fails (`session.error` set), the wait loop clears `processing` and returns without
   attempting PELT, so the frontend's error takeover screen still renders correctly.

No frontend file was changed this round — the fix is entirely in what the backend reports and does
around Phase B/Process sequencing.

---

## Verification (`claude-in-chrome`, real browser + backend, both actually clicked through)

**1. Single file, PROCESS enables as soon as the icon shows ✕.** Started a session for `chb06`,
uploaded `chb06_01.edf`. Reopened the panel in the browser: file already showed the plain ✕ icon and
PROCESS was solid black (enabled) — confirmed via the backend snapshot at that exact moment showing
`"ready_to_process": true` (Phase B for a single ~1 h file finishes fast, so this alone doesn't prove
decoupling — see test 2 for the conclusive case).

**2. 2–3 files, PROCESS only enables once all show ✕ — and specifically caught the
files-uploaded-but-Phase-B-still-running window.** Started a fresh session, uploaded
`chb06_02/03/04.edf` (three ~1 h files) back-to-back. Screenshotted the panel once all three showed
✕: PROCESS was enabled (solid black), and the backend snapshot at that same instant read:
```json
{"files": [... all "uploaded" ...], "phase_b_done": false, "ready_to_process": true, "processing": false, ...}
```
`ready_to_process: true` while `phase_b_done: false` is the direct proof the button is no longer
tied to Phase B completion.

**3. Clicked PROCESS, watched the full cycle resolve, subject appears correctly.** Clicked PROCESS
in the browser from that exact state (Phase B not yet done). The full-panel "Processing subject —
combining files and detecting change points..." loading screen appeared immediately (screenshotted).
Backend polling showed `processing: true` continuously — `phase_b_done` flipped `false → true`
partway through while `processing` stayed `true` the whole time (proving `_wait_phase_b_then_process`
genuinely waited, then ran PELT, inside the same processing window the user sees) — then
`done: true` with a real operating point (`pen_mult: 2.0`, `28.76` events/day). Clicked "Done" in
the browser: the panel closed and the Database table now shows:

| ID | No. files | Start date | Duration | Alert | Status | Memo |
|---|---|---|---|---|---|---|
| chb06 | 3 files | 2060.01.26 23:09:34 | 11:41:01 | 14 | ○ View | round2 multi-file test |

This is the first complete create→upload→process→appears-in-table cycle watched end-to-end in a
real browser for this build. Deleted this test subject afterward (`DELETE /api/subjects/chb06`) and
cleared `uploads/` so the DB is empty again, same convention as round 1.

**4. Guards + git status.**
```
pytest web_demo/backend/tests/test_guards.py -v
web_demo/backend/tests/test_guards.py::test_guard_no_build_timeline_masked PASSED
web_demo/backend/tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED
web_demo/backend/tests/test_guards.py::test_guard_no_labeled_npy PASSED
web_demo/backend/tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED
4 passed in 2.69s
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
?? web_demo/CC_STEP3_FIX_PROMPT.md
?? web_demo/CC_STEP3_FIX_REPORT.md
?? web_demo/CC_STEP3_REPORT.md
?? web_demo/backend/pipeline_worker.py
?? web_demo/backend/upload_manager.py
?? web_demo/frontend/src/components/ConfirmDialog.jsx
?? web_demo/frontend/src/screens/CreateNewPanel.jsx
```
This round's only actual edit (`start_process`/`snapshot`/new `_wait_phase_b_then_process`) is
inside `web_demo/backend/upload_manager.py` — an already-untracked (never-committed) file from the
original Step 3 build, so it doesn't show as a new `M` line above; everything else in this listing
predates this round (the `M`/`??` files from round 1 and before — `tables_ch2.md` and
`docs/VERIFIED_CORRECTIONS.md` predate Step 3 entirely per `CC_STEP3_REPORT.md`).

**5. Round 1 regression re-check.** Bug 2 (overlay): `document.querySelector('main > div')`'s
`getBoundingClientRect().width` measured identical (1318 px) with the panel open and closed. Bug 1
(auto-close): reopened the panel, typed a Project ID, scrolled, waited 8 s — stayed open with the
value intact. Both hold; this round's backend-only fix didn't touch either code path.

## Stop condition

Per the prompt: not proceeding to Step 4. PROCESS now enables on upload completion regardless of
Phase B timing, a full create→upload→process cycle was watched succeed end-to-end in a real
browser, and all five verification steps pass.
