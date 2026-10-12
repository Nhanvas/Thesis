# CC_STEP9_CHECKPOINT_FIX_REPORT.md — small checkpoint fix: wording + `chb16` session-lock check

Both items of `CC_STEP9_CHECKPOINT_FIX_PROMPT.md` done. No `git add`/`commit`/`push` run. Guards
4/4 green.

**Housekeeping note, unrelated to either item:** since the prior checkpoint session, a new commit
`f34db2c` ("Step 9 phase 1 + 1b: DB cleaned to real data only (chb13, chb16); real PELT/Phase A+B
timing measured; C23 added") landed on `main` — made outside this session, not by this fix. That's
why `git status`/`git diff` below are small and isolated to this fix's own two edits, not a stale
carry-over from the earlier Step 8/9 work (see §3).

## 1 · Concurrency-finding wording — both passages

Added the same short clause to both, matching each file's own terse style; nothing else in either
passage was reworded.

### 1.1 `SZSCAN_SPEC_v5.md` (C23 note, end of §1.7)

```diff
@@ -262,7 +262,9 @@ EDF reading, gamma-AEC, GAE forward — all much smaller).
 > `9.76 s/hour` serial-CLI figure still quoted in `CLAUDE.md` — explained by genuine upload-transfer
 > overhead plus unbounded per-file Phase A thread concurrency (up to 19 concurrent threads observed on
 > a 4-physical/8-logical-core dev machine). The concurrency finding is recorded as an **open item, not
-> fixed**.
+> fixed** — deliberately deferred, since phase 1b's own measured total time is already comfortable
+> without a fix; revisit (cap concurrent Phase A threads) before the defense if timing margin ever
+> becomes a real concern.
```

### 1.2 `BUILD_PROGRESS.md` (§15.2, phase 1b detail)

```diff
@@ -949,7 +949,9 @@ measurement.
   and unbounded per-file Phase A thread concurrency (`upload_manager.py` spawns one background thread
   per file the instant its bytes land, not waiting for the previous file — up to 19 concurrent threads
   observed on this dev machine's 4-physical/8-logical-core CPU). The concurrency finding is an **open
-  item, not fixed** (§14).
+  item, not fixed** (§14) — deliberately deferred, since the measured total time above is already
+  comfortable without a fix; revisit (cap concurrent Phase A threads) before the defense if timing
+  margin ever becomes a real concern.
```

(Note: `BUILD_PROGRESS.md` doesn't have a separate concurrency bullet inside §14's own Open Items
list — the only place either file states the exact "open item, not fixed" phrase is the §15.2 passage
above, which already parenthetically points back to §14. That is the passage this item targeted.)

## 2 · `chb16` upload-session lock — checked live, not inferred

### 2.1 What was found

The backend was **not running** when this fix started (confirmed: a plain TCP connect to
`127.0.0.1:8000` — the port `vite.config.js` proxies `/api` to — was refused, and a port scan of the
other common dev ports found nothing listening). Starting a fresh instance of my own then failed to
bind port 8000 ("only one usage of each socket address... normally permitted") — meaning a **separate,
already-running instance** (most likely Boti's own, matching his account of having just looked at the
Database screen) came up on that port in the interim. All checks below went through **that** live,
already-running instance — a genuine external process, not one this fix spun up — via the same
cookie-session login flow (`AdminSzScan`, credentials read from `backend/.env`) phase 1b used, over
plain HTTP, no DB/state edit attempted beyond the login itself:

```
POST /api/login            → 200
GET  /api/uploads/current  → 404 {"detail":"No Create New session in progress."}
```

Repeated a second time (independent script run) for confidence, same result both times. As a
read-only sanity check that this was genuinely the real app and not some other stray process, also
read `GET /api/subjects` on the same authenticated session:

```
chb13  Viewed   "A2 concurrency test"
chb16  View     "CC_STEP9_PHASE1B timing run"
```

— exactly the two subjects and memos phase 1/1b left behind, confirming this is the real, live
backend serving the real DB, not a fresh/empty one.

### 2.2 Which outcome actually happened

**Outcome (4) from the prompt: no session was found at all.** `GET /api/uploads/current` returned a
plain 404 "no session in progress," not a `done: true`/unacknowledged snapshot. No acknowledge call
was needed or made — there was nothing to dismiss. Per the prompt's own instruction, no action was
invented to "fix" this.

**Why, plainly:** `upload_manager.py`'s own docstring and code confirm the session lock is **pure
in-process Python memory** — a single module-level `_current` slot (`_current: Optional[UploadSession]
= None` at import time), "surviv[ing] across HTTP requests as plain Python process memory," never
written to the DB or to disk. Whatever server process was running at the end of phase 1b (the one
that left the session `done: true`, unacknowledged) is not the same process now answering requests —
it was restarted at some point in between (consistent with the backend being found not-running at the
start of this fix, and a different instance now up on the same port). A fresh process's `_current`
starts `None` by construction, which is exactly what was observed — the lock cleared itself as a
side effect of the process restarting, not because anyone clicked through the panel or called
`acknowledge`.

### 2.3 Item 3 (fresh Create-New not blocked) — not attempted, by design

The prompt's item 3 ("if feasible... also confirm a fresh Create-New attempt is no longer blocked")
was explicitly conditional and would have meant calling `POST /api/uploads/current` (start a session)
against this **live, currently-running instance that isn't this session's own** — plausibly the same
one Boti is actively looking at right now. That write was not attempted: starting (even a
throwaway, immediately-discarded) session on a shared, already-running server this fix didn't launch
risks colliding with Boti's own live use, and the environment's own permission layer independently
declined an attempt to do exactly this (a combined start+discard probe), tagging it a shared-resource
modification. Given item 1 already found **no session at all**, a fresh Create-New being unblocked
follows directly from the code path read in `main.py`/`upload_manager.py` (`_require_session` /
`start_session` only reject with a 409 when `um.get_current()` is not `None`) — not re-verified live,
per the prompt's own "if feasible" wording and in favor of not touching someone else's possibly-live
session.

**Cleanup:** this fix's own attempt to start a *second* uvicorn instance on port 8000 (before
realizing another instance already held it) failed to bind and exited immediately
(`exited with code 3`, clean shutdown logged) — nothing was left running by this fix. The
already-running instance found above was not started, stopped, or otherwise touched by this session,
beyond the read-only login/`GET` calls in §2.1.

## 3 · Raw command output

### 3.1 `pytest -v`

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

============================== 4 passed in 5.50s ==============================
```

### 3.2 `git status`

```
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   web_demo/BUILD_PROGRESS.md
	modified:   web_demo/SZSCAN_SPEC_v5.md

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	bme11/
	web_demo/CC_STEP9_CHECKPOINT_FIX_PROMPT.md

no changes added to commit (use "git add" and/or "git commit -a")
```

(`bme11/` is Boti's own, unrelated, pre-existing untracked directory — same as every prior report has
noted. The prior checkpoint's own report/prompt files and the earlier Step 8/9 modified backend/
frontend files are no longer listed here because commit `f34db2c` (§0) already absorbed them — not
because this fix touched them.)

### 3.3 `git diff --stat`

```
 web_demo/BUILD_PROGRESS.md | 4 +++-
 web_demo/SZSCAN_SPEC_v5.md | 4 +++-
 2 files changed, 6 insertions(+), 2 deletions(-)
```

Exactly this fix's two edits (§1.1/§1.2) — nothing else in either file changed.

---

**Stopping here per the prompt. No `git add`/`commit`/`push` was run.**
