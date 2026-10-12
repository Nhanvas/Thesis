# CC_FIX_DELETE_CONCURRENCY_REPORT.md — two independent backend fixes

Scope: `web_demo/backend/main.py` (fix 1) and `web_demo/backend/upload_manager.py` (fix 2).
`src/*.py` untouched. Guards (`test_guards.py`) confirmed 4/4 green after both.

## Fix 1 — DELETE /api/subjects/{id} now also removes uploads/{id}/

**Before:** `main.delete_subject` called only `db.delete_subject(subject_id)` — the DB row
went away but `uploads/{subject_id}/` (raw EDFs, filtered/raw caches, score caches) was left
on disk forever.

**After** (`main.py`): after the DB delete, resolve `uploads/{subject_id}` and:
- if the resolved path is not strictly under the resolved `uploads/` root (defends against a
  `subject_id` like `..`, even though in practice it always comes from an existing DB row) —
  refuse and log a warning, DB row still gets deleted.
- if the directory doesn't exist — log "already gone" and return normally (no error).
- otherwise `shutil.rmtree` it and log what was removed.

Added a module-level `logger = logging.getLogger(__name__)` (with `logging.basicConfig` since
nothing configured logging before) since nothing in the backend logged anything previously.

**Live verification** (`FakeRequest` stub + the real `main.delete_subject` function, no
mocking of the delete logic itself — see console output below): seeded a throwaway DB row
`zz_cc_fix_delete_verify` and a matching `uploads/zz_cc_fix_delete_verify/` dir with a dummy
file and a `cache/` subdir, called the endpoint function directly, confirmed both the DB row
and the whole directory tree were gone afterward, and confirmed all 8 real allowlisted
subjects (`chb03/06/13/14/15/16/17/18`) and their DB rows were untouched:

```
INFO:main:Removed uploads directory for subject zz_cc_fix_delete_verify: F:\Study\Thesis\Code\web_demo\backend\uploads\zz_cc_fix_delete_verify
before delete:
  dir exists: True
delete_subject() returned: {'ok': True}
after delete:
  db row present: False
  dir exists: False
OK: both DB row and uploads/ directory are gone
```

uploads/ and subjects table after the run — only the 8 real subjects remain:
```
uploads/: _draft_545c391fc73f7447  _draft_5f624f60c5908183  _work  chb03  chb06  chb13  chb14  chb15  chb16  chb17  chb18
subjects table: chb03 chb06 chb13 chb14 chb15 chb16 chb17 chb18
```

## Fix 2 — bounded Phase-A concurrency (upload_manager.py)

**Before:** `add_file()` did `threading.Thread(target=_run_phase_a, ...).start()` per file, no
cap. Each Phase A thread holds a full `mne` Raw load + scipy filtering pass in memory; an
18-file/66h subject spawned 18 of these simultaneously and OOM-killed the process.

**After:** a module-level `ThreadPoolExecutor(max_workers=4, thread_name_prefix="phase_a")`
(`_phase_a_executor`); `add_file()` now does `_phase_a_executor.submit(_run_phase_a, session,
entry)` instead of spawning an unbounded thread. Everything downstream of `_run_phase_a`
(cancel flag, `session.lock`, `_maybe_run_phase_b` trigger) is unchanged — the executor is a
drop-in swap for "run this in the background," not a redesign of the pipeline.

**Cap chosen: 4.** Rationale: this is a CPU-only dev machine (CLAUDE.md); 4 concurrent Raw
loads is a compromise between throughput and memory headroom — low enough to comfortably
avoid recreating the OOM that 18-at-once caused, high enough that a typical multi-file subject
still pipelines instead of serializing to one file at a time. No profiling data on
per-file peak memory was available to tune this further; if OOM recurs at 4, lower it.

**Live verification**: monkeypatched `pipeline_demo.process_file_phase_a` with a dummy that
increments/decrements a locked counter and sleeps, then ran 12 files through the *real*
`upload_manager.add_file()` path (same code the upload endpoint calls) back to back:

```
cap configured: 4
peak concurrent Phase A workers observed: 4
files processed: 12 / 12
OK: peak stayed within the configured cap
```

Peak observed concurrency was exactly 4 (never exceeded), and all 12 files still completed —
confirming the pool bounds concurrency without dropping or starving any file.

## test_guards.py — raw output (after both fixes)

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

============================== 4 passed in 6.69s ==============================
```

4/4 green.
