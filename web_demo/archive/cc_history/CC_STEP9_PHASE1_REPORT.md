# CC_STEP9_PHASE1_REPORT.md — Step 9, phase 1: inventory + cleanup

## 1 · Summary

All 3 parts of `CC_STEP9_PROMPT.md` done, in order. Every real-vs-synthetic determination below is
based on a byte-for-byte SHA-256 comparison against the actual file on disk in
`F:/Study/Thesis/Dataset/CHB-MIT/{subject}/` — not filename inference, not the DB's own stored
duration field. **Key findings:**

- Only `chb13` currently has genuinely real, fully-processed, cached data in the DB.
- `chb14`, `chb15`, `chb16` (all three, not just some) held synthetic data — truncated,
  re-encoded ~9.5–9.7 MB clips named `chb15_NN_short.edf`, byte-different from every real EDF on
  disk (confirmed, not merely inferred from the `_short` suffix) — filed under 3 different subject
  ids, including under `chb15` itself. All three subject rows were deleted, DB rows and on-disk
  cache both, via the app's real Delete flow plus manual cache-directory cleanup (the Delete
  endpoint alone does not remove `uploads/{subject}/` — see §2.2).
- `chb06`'s "18-file, full Progress" state that the prompt describes from Boti's own screenshots
  **is not what's in the DB right now** — `chb06` has **no subject row at all**. It does have an
  orphaned, never-finalized partial upload on disk (1 real, byte-identical `chb06_01.edf` +
  Phase-A/raw cache, no score/PELT output, no DB row) — see §1.1 below for the direct evidence and a
  plausible explanation.
- `chb03` similarly has an orphaned partial upload (2 real, byte-identical files, Phase-A cache
  only) but zero DB row.
- `chb17`/`chb18` have no data anywhere — never touched by any upload.
- **A real time-estimate gap found and flagged, not glossed over:** the `9.76 s/hour` figure
  (`CLAUDE.md`) measures only `pipeline_demo.process_file` — Phase A (open/filter/window) + Phase B
  (adjacency/GAE/gamma/ensemble). It **never calls `cpd_pipeline_v14.detect_events`** (PELT). The
  real app's "Process" step is a **separate** stage (`pipeline_worker.py`'s `_run_process_events`,
  confirmed by reading the code) that runs PELT **6 times** per subject (once per
  `pen_mult` in `DEFAULT_PENS = [0.3, 0.5, 1.0, 2.0, 5.0, 10.0]`, for the operating-point grid
  search) over the subject's whole concatenated timeline — exactly the step
  `SZSCAN_SPEC_v5.md §1.7` itself calls "the most time-consuming part." No isolated PELT timing has
  ever been recorded anywhere in this repo. §4 below gives the Phase-A+B estimate from the real
  `9.76 s/hour` figure as a **lower bound only** and recommends measuring PELT directly on the
  smallest missing subject before committing to a long unattended run.

Guards 4/4 green throughout. No `git add`/`commit`/`push` was run. **Phase 2 was not started.**

## 1.1 · How the `chb06`/`chb03` finding was reached (evidence, not inference)

```
$ SELECT DISTINCT subject_id FROM files;
chb13, chb15, chb14, chb16          -- no chb06, no chb03, before Part 2's deletions
```

But `web_demo/backend/uploads/` (on disk, outside the DB) has:

```
uploads/chb03/chb03_24.edf              42,399,744 bytes  (Phase A only: .filtered.npy present)
uploads/chb03/chb03_25.edf              42,399,744 bytes  (Phase A only: .filtered.npy present)
uploads/chb06/chb06_01.edf             169,898,496 bytes  (Phase A + raw: .filtered.npy, .raw.npy)
```

Both `chb03` files and the `chb06` file are **SHA-256-identical** to the real dataset originals
(`F:/Study/Thesis/Dataset/CHB-MIT/chb03/chb03_24.edf` etc.) — genuinely real data, not synthetic.
But neither has `.score.npy`, `.pernode.npy`, or `pernode_baseline.npy`, and neither has **any**
row in `subjects`/`files` — meaning the pipeline's "Process" (PELT) stage never ran and
`_finalize_draft_dir` never committed a DB row for either. This is an **orphaned, incomplete
upload** left over from a past session (mtimes: `chb03` Sep 16 07:31, `chb06` Sep 16
11:37–Sep 17 08:08) — not the "18-file, full Progress `chb06`" Boti described seeing live this
session. The most likely explanation: that screenshot was from a different point in time /
different DB state (this demo's DB has been reset or modified between sessions before — e.g. the
`chb15` file-status discrepancy noted in §2.1 below), or from `chb06`'s cache existing on disk
without ever having gone through this exact DB. Stated as a finding, not resolved further — not
in scope for phase 1 to investigate why, only to report the DB's actual current state.

These 2 orphaned directories were **not deleted** — Part 2 only mandates removing confirmed-**synthetic**
data, and this is confirmed-**real** data (byte-identical), just incomplete. Deleting it would only
cost phase 2 more re-upload time for no integrity benefit. Left in place for Boti to decide (reuse
via a fresh Create-New, since the app has no "resume a draft" UI once a draft's session id is gone —
`uploads/_draft_5f624f60c5908183` and `uploads/_work` are both empty leftover session-scratch
directories, harmless, from the same or an unrelated interrupted session).

## 2 · Part 1 — Full 8-subject inventory

| Subject | DB row? | Files (DB) | Real or synthetic? | Review states | Cache (real, complete) |
|---|---|---|---|---|---|
| `chb03` | **No** | — | n/a — no DB row. **Orphaned partial upload on disk**: 2/38 real files, SHA-256-identical to dataset, Phase A only | n/a | Partial: `.filtered.npy` only, no raw/score/pernode |
| `chb06` | **No** | — | n/a — no DB row. **Orphaned partial upload on disk**: 1/18 real files, SHA-256-identical, Phase A + raw | n/a | Partial: `.filtered.npy` + `.raw.npy`, no score/pernode (PELT never ran) |
| `chb13` | **Yes** | 2 (`chb13_02.edf`, `chb13_03.edf`) | **Real** — both SHA-256-identical to the dataset originals | Both `Viewed` | **Complete and real**: `.filtered.npy`, `.raw.npy`, `.pernode.npy`, `.score.npy`, `pernode_baseline.npy` all present for both files |
| `chb14` | ~~Yes~~ **deleted this session** | ~~6~~ | **Synthetic** — files named `chb15_01…06_short.edf` (not a real `chb14` filename at all), ~9.5–9.7 MB each, byte-different from every real EDF checked | 2 `Viewing`, 4 `View` (at time of deletion) | Was present (filtered/raw/pernode/score/baseline) but synthetic throughout |
| `chb15` | ~~Yes~~ **deleted this session** | ~~2~~ | **Synthetic** — `chb15_01_short.edf`/`chb15_02_short.edf` are **not** the real `chb15_01.edf`/`chb15_02.edf` (9.5 MB vs. 57.2 MB; not even a byte-prefix match against the real file — re-encoded/re-windowed, not a raw truncation) | Both `Viewed` (see note below) | Was present (filtered/raw/pernode/score/baseline) but synthetic throughout |
| `chb16` | ~~Yes~~ **deleted this session** | ~~12~~ | **Synthetic** — same `chb15_01…12_short.edf` clips as `chb14`, filed under a third subject id | 1 `Viewing`, 10 `View`, 1 `Viewing` (at time of deletion) | Was present (filtered/raw/pernode/score/baseline) but synthetic throughout |
| `chb17` | **No** | — | n/a — no DB row, no `uploads/chb17/` directory at all | n/a | None |
| `chb18` | **No** | — | n/a — no DB row, no `uploads/chb18/` directory at all | n/a | None |

**Note on `chb15`'s review state:** at the start of this phase-1 session, `chb15`'s 2 files were
`Viewing`/`Viewing` — the state Step 8 fix round 2 deliberately reverted them to after its own live
test. By the time Part 2 began, both had become `Viewed`/`Viewed` again (confirmed via a fresh DB
read immediately before deletion, and visible live in the app's own subject list). Nobody in this
session touched `chb15`'s file statuses before that point. Most likely explanation: Boti himself
live-testing the app between sessions (same category as the pre-existing "A2 concurrency test"
memo on `chb13` — a leftover test-state marker, not a live bug). Moot now since the whole subject
was confirmed synthetic and deleted regardless; flagged here only for completeness, not
investigated further.

**Resolves the 2 standing open items from `BUILD_PROGRESS.md`'s open-items section directly:**

1. `chb06` is **not** the real ~4-hour, full-file-count subject Boti's screenshots suggested — the
   DB currently has no `chb06` row at all (§1.1).
2. **All three** of `chb14`/`chb15`/`chb16` were synthetic (not just "some") — confirmed by hash,
   not by filename — and `chb03`/`chb17`/`chb18` are the three real subjects (of the 8) with zero
   data in the DB, `chb03` having an unfinished real-data upload attempt sitting on disk.

## 3 · Part 2 — Synthetic data removed

Deleted via the app's real Delete flow (`claude-in-chrome`, logged in as `AdminSzScan`), one at a
time, each with its own "Are you sure you want to delete this process?" confirmation:

1. `chb15` — confirmed via the UI's own subject list disappearing from the table after confirming.
2. `chb14` — same.
3. `chb16` — same.

### 3.1 DB-level confirmation (cascading delete)

```
subjects: [{'id': 'chb13', 'memo': 'A2 concurrency test', ...}]
files:    [{'id': 10, 'subject_id': 'chb13', 'filename': 'chb13_02.edf', 'status': 'Viewed'},
           {'id': 11, 'subject_id': 'chb13', 'filename': 'chb13_03.edf', 'status': 'Viewed'}]
events count: 5
attribution_status count: 0
```

Only `chb13` remains anywhere in `subjects`/`files`/`events`/`attribution_status` — the schema's
`ON DELETE CASCADE` (confirmed `PRAGMA foreign_keys = ON` on every connection, `db.py`) removed the
deleted subjects' `files`/`events`/`attribution_status` rows automatically; no orphaned rows
verified by direct query.

### 3.2 Cache-file cleanup — the part the app's own Delete endpoint doesn't do

Read `main.py`'s `DELETE /api/subjects/{subject_id}` directly: it calls only `db.delete_subject()`
(the DB rows above) — **it never touches `uploads/{subject_id}/` on disk.** Confirmed live: all
three directories (`uploads/chb14/`, `uploads/chb15/`, `uploads/chb16/`) were still present,
full of the synthetic `.edf`/`.filtered.npy`/`.raw.npy`/`.pernode.npy`/`.score.npy`/
`pernode_baseline.npy` files, immediately after the 3 UI deletions completed. Per the prompt's own
"DB-level delete plus matching cache-file cleanup" fallback, removed manually:

```
uploads/chb14  (165 M)  — deleted
uploads/chb15  ( 58 M)  — deleted
uploads/chb16  (327 M)  — deleted
```

### 3.3 Confirmed clean afterward

```
$ find uploads -iname "*short*"
(no matches)
$ find uploads -maxdepth 1 -type d
uploads
uploads/chb03
uploads/chb06
uploads/chb13
uploads/_draft_5f624f60c5908183   (empty, harmless, pre-existing)
uploads/_work                     (empty, harmless, pre-existing)
```

**No trace of synthetic data remains, in the DB or on disk.** The DB contains exactly one subject
(`chb13`, real, verified) and no row anywhere holds synthetic data under a real subject's name.

## 4 · Part 3.3/3.4 — Ready vs. needs upload, and a rough time estimate

### 4.1 The split

| Status | Subjects |
|---|---|
| **Ready** (real, uploaded, processed, cached) | `chb13` only |
| **Needs a real upload** through Create-New before phase 2 can build cache | `chb03`, `chb06`, `chb14`, `chb15`, `chb16`, `chb17`, `chb18` (**7 of 8**) |

`chb03` and `chb06` have a head start (real EDF bytes already on disk, `chb03` through Phase A,
`chb06` through Phase A + raw) but **no DB row** — from the app's own perspective (and Tier 2's
"processed from real EDF files through the correct Create-new → Process flow" requirement) they
still need a genuine Create-New → Process run to become real subjects; whether that run can reuse
the existing cache files or needs a fresh upload is an implementation detail for phase 2, not
resolved here.

### 4.2 Real file count / total duration on disk, per subject (measured, not estimated)

Read directly from each real EDF's own header (`number of data records × record duration`, not the
DB's stored value, not inferred from file size):

| Subject | Real files on disk | Total duration on disk |
|---|---|---|
| `chb03` | 38 | 38.00 h |
| `chb06` | 18 | 66.74 h |
| `chb13` (ready — 2 of these 33 already uploaded = exactly 2.00 h) | 33 | 33.00 h |
| `chb14` | 26 | 26.00 h |
| `chb15` | 40 | 40.01 h |
| `chb16` | 19 | 19.00 h |
| `chb17` | 21 | 21.01 h |
| `chb18` | 36 | 35.64 h |

**Total across the 7 missing subjects, every real file: 246.39 hours of EEG.**

### 4.3 Time estimate — and its real limitation, stated plainly

`SZSCAN_SPEC_v5.md §1.7`'s own text still reads the **stale** `~15 s for 1 hour of EEG` estimate
(never updated in that file). The actually-measured, current figure — read from `CLAUDE.md` at
build time as instructed, not retyped from memory — is:

> **9.76 s per hour of EEG**, measured on `chb06_01.edf` (Step 1), end-to-end
> **open → filter → adjacency → GAE → gamma → ensemble**, with an observed **~5× run-to-run
> variance** on this dev machine.

**This figure does not include the "Process" (PELT) step.** Verified by reading the code, not
assumed: `pipeline_demo.process_file` (the function Step 1 actually timed) calls only
`process_file_phase_a` and `process_subject_phase_b` — never `cpd_pipeline_v14.detect_events`. The
real app's Create-New flow runs PELT separately, in `pipeline_worker.py`'s
`_run_process_events` → `process_subject_events` → `calibrate_operating_point`, which calls
`detect_events()` **once per `pen_mult` in `DEFAULT_PENS = [0.3, 0.5, 1.0, 2.0, 5.0, 10.0]`** (6
full PELT passes over the subject's whole concatenated timeline, per subject) — exactly the stage
`SZSCAN_SPEC_v5.md §1.7` itself names as "the most time-consuming part." **No isolated PELT timing
has ever been recorded anywhere in this repo** (checked `BUILD_PROGRESS.md` and every `CC_STEP*`
report for a PELT-only wall-clock number — none exists; `DEMO_BUILD_HANDOFF.md §8`'s old "~17 files
≈ 6 minutes" risk-table entry predates the "run live, no simulation" decision and cannot be
confirmed as still accurate).

Given that, the honest estimate is a **lower bound only**:

```
246.39 h × 9.76 s/h  ≈  2,405 s  ≈  40 minutes      (Phase A + B only, all 7 subjects, every real file)
with the ~5× variance caveat: roughly 8 minutes to ~3.3 hours, Phase A+B alone
                                                       + an unknown, unmeasured PELT cost on top
```

**Recommendation for sequencing phase 2** (not a decision made here — Boti's call per the project's
standing convention): measure PELT's own wall-clock cost directly on the **smallest** missing
subject first (`chb16`, 19.0 h) before committing to a long unattended run on the **largest**
(`chb06`, 66.7 h) — matching `SZSCAN_SPEC_v5.md §1.7`'s own stated approach ("the exact number is
measured when building the cache"). Also worth weighing: `chb13` (the one already-ready subject)
used only 2 of its 33 real files (2 of 33 h), not the full dataset — if phase 2 follows that same
precedent for the other 7 subjects rather than uploading every real file, the true total would be a
small fraction of the 246.39 h worst-case figure above, and correspondingly faster. Both this
worst-case number and the file-count table in §4.2 are given so Boti can decide the actual
per-subject file selection himself, rather than this report assuming an answer.

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

============================== 4 passed in 5.06s ==============================
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
	web_demo/CC_STEP9_PROMPT.md

no changes added to commit (use "git add" and/or "git commit -a")
```

Unchanged from before this phase started — this phase's own work (subject deletion, cache-directory
cleanup) touched only `web_demo/backend/szscan.db` and `web_demo/backend/uploads/`, both gitignored
(`.gitignore` lines 55–56), so neither shows up here. `web_demo/CC_STEP9_PHASE1_REPORT.md` itself
(this file) is new/untracked, not shown above since `git status` was run before writing it.

---

**Stopping here per the prompt. No `git add`/`commit`/`push` was run. Phase 2 (running the pipeline
on the missing real subjects / building the insurance cache) was not started — that needs a
separate prompt once this report is reviewed.**
