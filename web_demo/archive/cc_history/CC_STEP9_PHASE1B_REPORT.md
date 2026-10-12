# CC_STEP9_PHASE1B_REPORT.md — Step 9, phase 1b: measuring the real "Process" (PELT) cost

## 0 · How this was actually driven (read before the numbers)

`CC_STEP9_PHASE1B_PROMPT.md` asks for the **genuine Create-New → Upload → Process flow in the
running app — the real UI flow, not a CLI shortcut**. Literal browser automation
(`claude-in-chrome`'s `file_upload` tool) turned out to be infeasible for this specific task: that
tool caps a single call's combined attachments at **10 MB** and only accepts files from a folder
already shared with the session — chb16's 19 real EDF files are **~915 MB combined** and live in
`F:/Study/Thesis/Dataset/CHB-MIT/chb16/`, outside any shared folder. Neither limit can be worked
around without altering the real files (not an option — Tier-2 requires byte-identical originals).

Instead, `web_demo/frontend/src/api.js` was read directly and replayed **exactly**: the same
`POST /api/uploads/current` → 19× `POST /api/uploads/current/files` (one real EDF per call,
`multipart/form-data`, field name `file`, sent **sequentially, awaiting each response** — the same
`for (const file of files) { await addUploadFile(file) }` loop `CreateNewPanel.jsx` runs, not sent
in parallel) → `POST /api/uploads/current/process`, using the app's real cookie-session login
(`AdminSzScan`, from `backend/.env`). This exercises the actual, unmodified server: the same global
`UploadSession` state machine in `upload_manager.py`, the same per-file `_run_phase_a` background
thread, the same `pipeline_worker.py` subprocess for Phase B and for Process/PELT — nothing about
the pipeline was called directly or bypassed. The only thing skipped is literal mouse/keyboard
interaction with a rendered page, which does no EDF processing of its own. A parallel poller
(logged in as the same admin, independent of the upload session) hit `GET /api/uploads/current`
every ~0.1 s throughout and logged every state transition with wall-clock timestamps — this is what
the numbers below are built from. Full raw JSONL timeline available on request; not attached here
to keep this report readable.

**No source file in `web_demo/` was modified to take this measurement** — everything below comes
from external HTTP polling of the app's existing, unmodified `/api/uploads/current` endpoint.

## 1 · The two timings, for `chb16` (19 real files, 19.00 h total, confirmed SHA-256-identical to
the dataset originals — spot-checked `chb16_01.edf`)

| Stage | Window measured | Wall-clock |
|---|---|---|
| **Phase A + B** (upload transfer + per-file `process_file_phase_a` + the one subject-wide Phase B subprocess run) | first upload `POST` sent → `phase_b_done` flips true | **271.56 s** (4.53 min) |
| **Process / PELT alone** (`_run_process_events` → `calibrate_operating_point` → `detect_events` × 6 `pen_mult` passes, `_finalize_draft_dir`'s directory move riding along) | Process button clicked (only *after* confirming `phase_b_done` was already true, so this window is uncontaminated by any Phase B wait) → `done` flips true | **68.03 s** (1.13 min) |
| **Sum — genuine end-to-end Create-New→Process** | first upload `POST` → `done` | **339.59 s** (5.66 min) |

Clicking Process was deliberately timed to happen only once `phase_b_done` was already observed
true (it was, by the time of the click — see §3 on why Phase B took as long as it did), specifically
so the Process-click-to-done window is **pure PELT + the cheap directory move**, not contaminated by
any leftover Phase B wait. This is the one deliberate scheduling choice made in an otherwise
un-intervened run; a real user could click Process earlier (as soon as `ready_to_process` goes true,
which only requires Phase A, not Phase B), and would then wait out the *rest* of Phase B behind the
Process spinner instead of the upload spinner — same total wall-clock, different bucketing.

### 1.1 Sanity check against the existing `9.76 s/hour` figure

The prompt asks for a **sum across all 19 files** as the figure to compare against `9.76 s/hour`
(`CLAUDE.md`) — that original number came from `pipeline_demo.process_file` run **serially, one file
at a time, no HTTP layer**, direct off local disk. The real app does not do that: `CreateNewPanel.jsx`
uploads files one at a time, but each file's Phase A begins in its **own background thread**, the
instant its own upload completes — it does **not** wait for the previous file's Phase A to finish.
So the naive per-file sum and the real wall-clock diverge, and both are reported:

- **Naive per-file sum** (each file's own upload-start → its own `status: uploaded` timestamp,
  summed across all 19, plus the one Phase B window): **295.01 s** (Phase A component) **+ 213.15 s**
  (Phase B component) **= 508.17 s** → **26.75 s/hour** — **2.74×** the `9.76 s/hour` figure.
- **Real wall-clock** (what the subject actually took, overlap included): **271.56 s** →
  **14.29 s/hour** — **1.46×** the `9.76 s/hour` figure.

Neither matches the original figure's ballpark, and the gap is explained plainly in §3, not
smoothed over — it is not a measurement error, it is two genuine differences between how Step 1
measured Phase A+B and how the real app runs it.

## 2 · Derived PELT rate and revised total-time estimate

**PELT rate: 68.03 s ÷ 19.00 h = 3.58 s per hour of EEG.**

The prompt's ask is specifically to replace phase 1's "+ an unknown, unmeasured PELT cost on top"
caveat with this real number, added to phase 1's existing Phase A+B lower bound (`9.76 s/hour`, the
same rate phase 1 already used). That version first, then a second, more defensible version using
this run's own real Phase A+B rate instead — both shown, since §1.1 found phase 1's lower bound
itself to now be a demonstrated underestimate for the real app's actual behavior.

| Subject | Hours (phase 1 §4.2) | Phase A+B — 9.76 s/h (phase 1's lower bound) | Phase A+B — 14.29 s/h (this run's real rate) | PELT — 3.58 s/h (this run's real rate) | Total (9.76 s/h + PELT) | Total (14.29 s/h + PELT) |
|---|---|---|---|---|---|---|
| `chb03` | 38.0 h | 371.0 s | 543.1 s | 136.1 s | 507.1 s (8.45 min) | 679.2 s (11.32 min) |
| `chb06` | 66.7 h | 651.0 s | 953.3 s | 238.8 s | 889.8 s (14.83 min) | 1192.1 s (19.87 min) |
| `chb14` | 26.0 h | 253.8 s | 371.6 s | 93.1 s | 346.9 s (5.78 min) | 464.7 s (7.74 min) |
| `chb15` | 40.0 h | 390.4 s | 571.7 s | 143.2 s | 533.6 s (8.89 min) | 714.9 s (11.92 min) |
| `chb17` | 21.0 h | 205.0 s | 300.1 s | 75.2 s | 280.2 s (4.67 min) | 375.3 s (6.26 min) |
| `chb18` | 35.6 h | 347.5 s | 508.8 s | 127.5 s | 475.0 s (7.92 min) | 636.3 s (10.60 min) |
| **Combined (227.3 h)** | | **2,218.4 s (36.97 min)** | **3,248.7 s (54.15 min)** | **813.8 s (13.56 min)** | **3,032.2 s ≈ 50.5 min ≈ 0.84 h** | **4,062.5 s ≈ 67.7 min ≈ 1.13 h** |

Arithmetic: each cell is `rate × subject's real hours` from phase 1's own §4.2 table (measured off
each EDF's own header, not estimated). Combined = sum of the 6 per-subject cells (equivalently,
`227.3 h × rate`).

**Headline: PELT itself is cheap — 13.56 minutes total across all 6 remaining subjects, not the
long pole phase 1 worried it might be.** Even the more conservative combined estimate (§2, right
column, using this run's real Phase A+B rate) comes to **~68 minutes** for all 6 remaining subjects
combined — comfortably inside a single working session, not the "long unattended run" phase 1
flagged as a risk to sequence carefully.

## 3 · Anomalies — stated plainly

1. **PELT is not "the most time-consuming part" — `SZSCAN_SPEC_v5.md §1.7`'s own characterization is
   contradicted by this measurement.** PELT (68.03 s) was **25%** of Phase A+B's wall-clock (271.56 s)
   for the same subject, not the dominant cost. Plausible reason: §1.7's claim was written against
   the stale `~15 s/hour` component estimate (`build_adjacency` + `compute_band_powers` only, per
   phase 1's own finding), not against a real, measured end-to-end Phase A+B figure — and PELT's 6
   passes run over an already-compact, precomputed 1-D global score array per node, which is
   inherently much cheaper than the file I/O + filtering + adjacency + GAE forward pass work Phase
   A+B does per raw file. Flagging for Boti's decision, not editing `SZSCAN_SPEC_v5.md` myself (out
   of this phase's scope) — but this is a real, reproducible finding, not a one-off.

2. **Real Phase A+B ran 46% slower (wall-clock) than the `9.76 s/hour` figure predicts, and the
   naive per-file sum overshoots it by 2.74×.** Two separate, identifiable causes, both real:
   - **Upload transfer overhead** (58.4 s total across 19 files, ~48 MB each over local HTTP) — the
     original `9.76 s/hour` figure never paid this cost; it read an already-local file directly.
     This is exactly the "per-file upload overhead" item 1 of the prompt asked to fold in — it is
     not a bug, it is a genuine cost a real defense-day upload will also pay.
   - **CPU contention from unbounded Phase A concurrency.** `CreateNewPanel.jsx` uploads files one
     at a time, but `upload_manager.py`'s `add_file()` spawns a **new background thread per file**
     the instant that file's bytes land — it does not wait for the previous file's Phase A to
     finish. Because the 19 uploads complete in quick succession (each taking only 1–8 s), **up to
     19 CPU-bound Phase A threads end up running concurrently** on this dev machine's **4 physical /
     8 logical cores** (confirmed via `wmic cpu`). Individual per-file Phase A durations measured
     6.1–23.8 s (vs. an expected ~1 s/file-hour × ~1 h/file if run in isolation, serially) — a
     visible slowdown from contention, not from any one file being unusually large or malformed.
     This is the same category of effect `CLAUDE.md` already calls out for the component-level
     figure ("~5× run-to-run variance... attributed to dev-machine background load") — this run
     reproduces that variance from **self-induced concurrency** rather than external load, which is
     new information: an unbounded fan-out of Phase A threads is itself a load source worth knowing
     about before scaling up to `chb06`'s 18 files.
   - No fix attempted here (out of phase 1b's scope — a measurement task, not a performance-tuning
     one); flagged for Boti to decide whether Phase A concurrency should be capped before phase 2's
     larger subjects.

3. **No crash, no retry, no error at this scale.** The worker subprocess exited cleanly for both the
   Phase B run and the 6-pass PELT run; `chb16`'s operating point converged normally
   (`pen_mult = 1.0`, `event_rate_per_day ≈ 51.79`) and all 19 files finalized to `View` status with
   41 events recorded in the DB. Nothing here suggests PELT itself has a scaling problem going into
   the larger remaining subjects (`chb06` at 66.7 h is only 3.5× `chb16`'s 19.0 h) — the 6-pass grid
   search is linear-ish in timeline length by construction (`cpd_pipeline_v14.detect_events` runs
   once per `pen_mult` over the same concatenated array each time), and this run gives no evidence
   against that.

## 4 · `chb16` left in the DB, as instructed

Not deleted. Confirmed via direct DB read after the run: `subjects` has `chb16` (memo
`"CC_STEP9_PHASE1B timing run"`), `files` has all 19 real `chb16_*.edf` rows at `status = 'View'`,
41 rows in `events`. `uploads/chb16/chb16_01.edf` spot-checked SHA-256-identical to
`F:/Study/Thesis/Dataset/CHB-MIT/chb16/chb16_01.edf` (both
`e28c0399a018f609cb4baeb0d1f73c105f23af2743610abfb074f68db4e9a95e`) — genuinely real, genuinely
cached, through the genuine flow. This is `chb16` done for phase 2 already, not throwaway work.

One loose end, left deliberately: the in-memory upload session is still sitting at
`done: true` / `operating_point` populated, **unacknowledged** — confirmed live via a fresh
`GET /api/uploads/current` just now. That is exactly the state a real user leaves it in if they
haven't yet clicked through the "Processing complete" panel (`acknowledgeUpload()` in
`DatabaseScreen.jsx` only fires on that click, never automatically). Nothing was faked to reach
"done" faster — this is that same real, momentarily-unacknowledged state, not touched further since
dismissing it wasn't part of this prompt's task. It only blocks starting a **new** Create-New session
system-wide (SPEC's one-subject-in-flight rule) until someone opens the app and dismisses it — it does
not affect `chb16`'s own DB row, which is already fully committed.

## 5 · Raw command output

### 5.1 `pytest -v`

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

============================== 4 passed in 2.95s ==============================
```

### 5.2 `git status`

```
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   web_demo/BUILD_PROGRESS.md
	modified:   web_demo/SZSCAN_SPEC_v5.md
	modified:   web_demo/backend/db.py
	modified:   web_demo/backend/export_txt.py
	modified:   web_demo/backend/main.py
	modified:   web_demo/frontend/src/api.js
	modified:   web_demo/frontend/src/screens/AnalysisScreen.jsx

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	bme11/
	web_demo/CC_STEP8_FIX2_PROMPT.md
	web_demo/CC_STEP8_FIX2_REPORT.md
	web_demo/CC_STEP8_FIX_PROMPT.md
	web_demo/CC_STEP8_FIX_REPORT.md
	web_demo/CC_STEP8_PROMPT.md
	web_demo/CC_STEP8_REPORT.md
	web_demo/CC_STEP9_PHASE1B_PROMPT.md
	web_demo/CC_STEP9_PHASE1_REPORT.md
	web_demo/CC_STEP9_PROMPT.md

no changes added to commit (use "git add" and/or "git commit -a")
```

Unchanged from phase 1's own baseline — this measurement run touched only `szscan.db` and
`uploads/chb16/` (both gitignored, `.gitignore` lines 55–56) and this report file itself (untracked,
not shown above since `git status` was run before writing it). No file under `web_demo/` was edited
to take this measurement (see §0).

---

**Stopping here per the prompt. No `git add`/`commit`/`push` was run. The other 6 subjects were not
uploaded** — that is phase 2 proper, a separate prompt once this real number is known and reviewed.
