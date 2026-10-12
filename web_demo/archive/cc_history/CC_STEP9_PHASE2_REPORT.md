# CC_STEP9_PHASE2_REPORT.md — Step 9 phase 2: upload + process the 6 remaining real subjects

All 6 subjects (`chb17`, `chb14`, `chb18`, `chb03`, `chb15`, `chb06`) are now real, fully processed,
cached subjects in the DB — the demo's 8-subject allowlist is complete. Driven entirely via the real
HTTP flow (`requests`, no `claude-in-chrome`), replaying `web_demo/frontend/src/api.js`'s own request
shapes exactly the way `CC_STEP9_PHASE1B_REPORT.md` did for `chb16`. Guards 4/4 green throughout and at
completion. No `git add`/`commit`/`push` run at any point. This report folds in
`CC_STEP9_PHASE2_PROGRESS.md`'s per-subject checkpoint log and covers everything from the original
prompt plus the two resume prompts this session needed.

**This session ran across three prompts** (`CC_STEP9_PHASE2_PROMPT.md`, then
`CC_STEP9_PHASE2_RESUME_PROMPT.md` twice, after two conversation interruptions mid-run) plus a
mid-session, user-directed real bug fix (§5) after `chb06` hit a genuine pipeline defect, not just
another interruption. Everything below is the consolidated, final account.

---

## 1 · `BUILD_PROGRESS.md` §1 doc edit

Per the original prompt's §1, replacing the stale `chb16`/"Processing complete" sentence in the
"Where to resume" note. **Was this already applied when the resume prompts ran?** No — checked both
times per the resume prompts' own instruction ("don't edit twice"): the first resume session found the
old sentence still present and applied the edit once; the second resume session re-checked and found
the (now-correct) replacement already there, so it was **not** edited again. Exact diff (as it stands
now, against the committed baseline):

```diff
 **Where to resume:** Step 9 phase 2 — upload + process the 6 remaining real subjects
 (`chb03`/`chb06`/`chb14`/`chb15`/`chb17`/`chb18`) through the real Create-New→Process flow. Before
-drafting that prompt: `chb16`'s upload session is sitting `done: true`, unacknowledged — someone
-needs to open the app and click through the "Processing complete" panel first (one-subject-in-flight
-rule), and §14 below has two open decisions (file-count-per-subject scope; the `DELETE` endpoint's
-on-disk cleanup) that are Boti's call, not something to assume an answer to. Also still read §10.4
-below (one open item from Step 7 not yet resolved) and `STEP8_9_PREDEFENSE_CHECKLIST.md` (uploaded
-alongside this file — report needs + the fixed Tier 2 rules for Step 9, agreed with Project #1
-2026-09-25). Don't assume anything on that checklist is already done just because it's listed there.
+drafting that prompt: `chb16`'s upload-session lock had already cleared on its own by the time of the
+Step 9 checkpoint fix (a backend restart reset the in-memory lock; confirmed via a live
+`GET /api/uploads/current` returning no session — see `CC_STEP9_CHECKPOINT_FIX_REPORT.md` §2). No
+manual dismissal was needed. §14 below has one open decision left (the `DELETE` endpoint's on-disk
+cleanup) — file-count-per-subject scope was decided 2026-09-26: full real file set for every
+subject, not a representative subset. Also still read §10.4 below (one open item from Step 7 not yet
+resolved) and `STEP8_9_PREDEFENSE_CHECKLIST.md` (uploaded alongside this file — report needs + the
+fixed Tier 2 rules for Step 9, agreed with Project #1 2026-09-25). Don't assume anything on that
+checklist is already done just because it's listed there.
```

## 2 · Preflight findings

1. **Backend confirmed up, no live session** (re-checked fresh each time this session picked up work,
   per the resume prompts' own "don't assume the prior finding still holds" instruction) — every check
   was a live `GET /api/uploads/current`, not an assumption.
2. **`chb03`/`chb06` orphaned partial-upload directories** (`BUILD_PROGRESS.md` §15.1: `chb03` 2/38
   real files, Phase A cache only; `chb06` 1/18 real files, Phase A + raw cache; neither had a DB row).
   Both removed before starting: `uploads/chb03/` (208 M) and `uploads/chb06/` (670 M) deleted, then
   both subjects were uploaded completely fresh through Create-New (no reuse of the stale cache).
3. **File-count spot-check against `BUILD_PROGRESS.md` §15.1's inventory** — read directly off each
   real dataset directory (`Glob`, not the DB): `chb03` 38, `chb06` 18, `chb14` 26, `chb15` 40, `chb17`
   21 (note: `chb17`'s real files are named `chb17a_NN.edf`/`chb17b_NN.edf`/`chb17c_NN.edf`, not
   `chb17_NN.edf` — a genuine CHB-MIT multi-session naming quirk for this one subject, not a mismatch),
   `chb18` 36. **All 6 matched the §15.1 inventory exactly — no mismatch found, nothing flagged before
   uploading.**

## 3 · Per-subject results (order: `chb17` → `chb14` → `chb18` → `chb03` → `chb15` → `chb06`)

| Subject | Files | Hours (real) | Phase A+B (s) | rate (s/h) | Process/PELT (s) | rate (s/h) | `pen_mult` | events/day |
|---|---|---|---|---|---|---|---|---|
| `chb17` | 21 | 21.007 | 572.84 | 27.27 | 166.82 | 7.94 | 2.0 | 41.13 |
| `chb14` | 26 | 26.000 | 607.01 | 23.35 | 171.87 | 6.61 | 5.0 | 29.54 |
| `chb18` | 36 | 35.635 | 813.95 | 22.84 | 389.86 | 10.94 | 2.0 | 30.98 |
| `chb03` | 38 | 38.002 | 462.70 | 12.18 | 138.79 | 3.65 | 2.0 | 34.74 |
| `chb15` | 40 | 40.010 | 562.69 | 14.06 | 127.65 | 3.19 | 5.0 | 44.39 |
| `chb06` | 18 | 66.735 | 726.05 | 10.88 | 293.48 | 4.40 | 2.0 | 29.13 |

Every row: real upload, real Create-New→Process flow, full real file set (no subset), DB-confirmed
`Status: View` afterward with file count and duration matching §2 item 3 above. Guards 4/4 green after
every single subject (checked and re-confirmed before moving to the next one each time, per the
original prompt's step 3.7).

**Rate variance, stated plainly, not smoothed over:** `chb16`'s own phase-1b rate (14.29 s/h Phase A+B,
3.58 s/h PELT) was **not** reproduced consistently — `chb17`/`chb14`/`chb18` ran 23–27 s/h (Phase A+B)
and 6.6–11 s/h (PELT), noticeably higher; `chb03`/`chb15`/`chb06` came back down to 11–14 s/h (Phase
A+B) and 3.2–4.4 s/h (PELT), close to `chb16`'s original figures. This is exactly the kind of run-to-run
variance `CLAUDE.md` already documents ("~5× run-to-run variance... attributed to dev-machine background
load") — this session's own driver process, other subjects' leftover OS-level effects, and (for `chb17`/
`chb18`/`chb03`) the interruption/resume mechanics themselves (see §4) are all plausible contributors.
No single rate figure here should be treated as *the* number for `SZSCAN_SPEC_v5.md §1.7`'s "smallest
subject" recommendation — the full spread is given so Boti can judge, not this report.

## 4 · Anomalies encountered, and how each was handled

### 4.1 Three conversation interruptions, all resumed cleanly (no data lost, no re-upload of already-
uploaded files)

- **`chb17`** was interrupted mid-upload (15/21 files at the point of interruption, per
  `CC_STEP9_PHASE2_RESUME_PROMPT.md`'s own account; by the time this session re-checked live, the
  server-side session had actually continued autonomously to 21/21 uploaded, since Phase A's
  background threads and the upload HTTP handling live in the **backend server process**, not this
  session's own driver script — only the driver's own polling died, not the pipeline). Resumed:
  detected the live session, uploaded nothing further (already complete), waited for `phase_b_done`,
  clicked Process, waited for `done`. **Phase A+B timing for this one subject uses a timestamp
  recovered from the interrupted run's own poller log** (`t_first_upload_post = 2026-09-26T17:35:31.651`,
  the log's first entry — accurate to ~2 s, not the true in-process variable, which was lost with the
  old process) rather than a fresh, artificially-late resume-time start.
- **`chb18`** was interrupted after all 36 files were uploaded and Process had *already been clicked*
  (`phase_b_done: true`, `processing: true` on live re-check). Resumed straight into the done-wait —
  recovered **three** timestamps from the interrupted run's own timeline log
  (`t_first_upload_post = 2026-09-26T18:02:43.036`, `t_phase_b_done = 2026-09-26T18:16:16.984`,
  `t_process_click = 2026-09-26T18:16:18.007`) so both Phase A+B and PELT timing stayed genuine
  end-to-end measurements, not resume-time placeholders.
- **`chb03`** was interrupted with all 38 files uploaded, `phase_b_done` still false. Resumed the same
  way. **A drafting mistake happened here and was caught, not silently shipped:** the
  `--recovered-start-iso` value passed to the resume script was a guess, not read from
  `chb03_timeline.jsonl` — it turned out to be *later* than the run's own `t_last_upload_response`,
  which is impossible. Caught before finalizing, corrected against the timeline log's real first entry
  (`2026-09-26T18:23:44.607`), and `phase_ab_wallclock_s`/`total_wallclock_s` recomputed against the
  corrected value (**462.70 s**, not the wrong first-written **103.92 s** — the table in §3 already has
  the corrected number).

### 4.2 One client-side `ReadTimeout`, no pipeline failure (`chb03`)

While waiting for `chb03`'s `phase_b_done`, this session's own polling script hit
`requests.exceptions.ReadTimeout` (15 s) — the server was slow to answer a plain `GET` while many
concurrent Phase A threads (per-file, `upload_manager.py`'s existing, deliberately-unfixed concurrency —
see §5.2) saturated this dev machine's CPU. Confirmed live immediately after (a fresh `GET` succeeded
within 30 s, `error: null`, all 38 files genuinely `uploaded`) that the **pipeline itself never
crashed** — this was purely the driver script's own transport timeout being too tight. Fixed generally
(not `chb03`-specific): the driver's polling now retries transient timeouts with a longer, 60 s budget
(`safe_get_current()`) instead of crashing the whole run.

### 4.3 Scratchpad working directory disappeared mid-session

Between two of this session's steps, the entire scratchpad directory holding the driver script and every
subject's raw timeline/result JSON files vanished (most likely purged during the low-memory episode in
§5.1, or an unrelated host cleanup — not confirmed which). **No repo file or DB state was affected** —
this only cost the raw per-subject JSON/timeline logs, not anything in `web_demo/` itself.
`CC_STEP9_PHASE2_PROGRESS.md` (checkpointed after every subject, in the real repo, per the resume
prompt's own §2 instruction) already had every number needed, so nothing had to be re-derived; the
driver script was rewritten from the same design before continuing with `chb06`.

## 5 · `chb06` — a genuine pipeline bug, found, fixed, and verified (not a `chb06`-only patch)

### 5.1 What happened

`chb06`'s first attempt uploaded all 18 real files cleanly, but the driver process was **OOM-killed by
the host three separate times** during and immediately after the upload phase (`"the system is running
low on memory"`, reported by the environment, not something this session could inspect directly).
Backend and DB state survived every kill (server-side session state lives in the FastAPI process, not
this session's driver — confirmed live each time via a fresh `GET`). After the third resume, all 18
files were confirmed uploaded and Phase B was reached — and **Phase B itself then hit a hard, real
crash**, confirmed via a direct `GET /api/uploads/current` read of the session's own `error` field:

```
Processing error: phase_b worker failed: ... numpy._core._exceptions._ArrayMemoryError:
Unable to allocate 6.88 GiB for an array with shape (50121, 18, 1024) and data type float64
```

This is deterministic, not transient — `chb06` has by far the most total EEG hours of any allowlisted
subject (66.74 h) packed into the fewest files (18, averaging ~3.7 h/file vs. ~1 h/file for every other
subject in this phase), so the array `pipeline_demo.py`'s `process_subject_phase_b()` was trying to
build — the whole-subject concatenation of every file's filtered windows, upcast to float64, just to
compute per-channel mean/std — was uniquely large for this one subject. No amount of retrying or waiting
would have changed the outcome; the fix had to be a real code change.

### 5.2 The fix — `pipeline_demo.py`'s `process_subject_phase_b()`, generalized, not `chb06`-specific

`pipeline_demo.py` is **not** on `CLAUDE.md`'s read-only thesis-code list (`src/cpd_pipeline_v14.py`,
`src/ensemble_recipe.py`, `src/szcore_eval.py`, `src/edf_index.py`, `src/edf_order.py`,
`src/retrain/gae_joint.py`) — it is explicitly "New demo logic lives in
`web_demo/backend/pipeline_demo.py`," so this was the right file to edit, not a boundary violation.

**Root cause:** lines 300–307 (before the fix) built one array of shape
`(n_windows_total, 18, 1024)` in float64 — for the whole subject at once — purely to compute
`ch_mean = arr.mean(axis=(0, 2))` and `ch_std = arr.std(axis=(0, 2))`. Peak memory for this single step
scaled with the subject's **total** duration, not any individual file's size.

**Fix:** compute the same two reductions one file at a time, never materializing a whole-subject array.
Verified **bit-identical** to the original single-shot computation, not an approximation, by proving
(empirically, at realistic array scales, and by the underlying reduction semantics) that:

1. `arr.sum(axis=(0, 2))` decomposes exactly into `arr.sum(axis=2).sum(axis=0)` — numpy reduces the
   1024-sample axis (2) before the window axis (0) internally.
2. Axis-2 reduction is independent per window/row — reducing it file-by-file and concatenating the
   (now tiny, since the 1024-sample axis is already collapsed) per-file results produces an identical
   `(n_windows_total, 18)` intermediate to reducing the full concatenated array's axis 2 in one shot.
3. `mean == sum / count` and `std == sqrt(mean((x - mean) ** 2))` exactly (numpy's own definitions,
   confirmed, not assumed).

So: reduce axis 2 per file (only one file's float64 temp array ever exists at a time — for `chb06`'s
biggest single file, a few GB at most, not ~6.9 GiB for the whole subject), concatenate the small
per-file `(n_i, 18)` results, then do the final axis-0 sum with one ordinary `numpy` call over that
already-tiny intermediate. Same two-pass structure for variance (need the global mean first, then a
second per-file pass for squared deviations) — same decomposition, same guarantee.

**Verified, not assumed:**
- A standalone script reproduced both the old (single-shot) and new (chunked) code paths side-by-side
  on synthetic data at realistic multi-file scales and confirmed `np.array_equal()` — exact, not
  "close" — for both mean and std.
- `pytest web_demo/backend/tests/test_guards.py -v` — 4/4 passed after the edit.
- `chb06` was then discarded (the errored session; its `_draft_*` cache directory, 9.9 GB of the
  first attempt's partial output, was also removed — same "no resume a draft" precedent phase 1
  already established) and **retried completely from scratch — all 18 real files, no subset** — per
  the explicit instruction not to shortcut this. It completed cleanly this time: no error, no OOM,
  4/4 guards after, DB row confirmed (`View`, 18 files, `2d:18:44:06` ≈ 66.735 h, matching the real
  inventory exactly).

### 5.3 The likely connection to Phase A's already-known, still-deferred concurrency issue — flagged,
not silently absorbed into one fix

Both `SZSCAN_SPEC_v5.md §1.7`'s C23 note and `BUILD_PROGRESS.md §15.2` already record, as a **deliberately
deferred** open item, that `upload_manager.py` spawns one unbounded background Phase A thread per file
the instant its upload completes — up to 19 concurrent threads were observed for `chb16` (19 files) on
this machine's 4-physical/8-logical-core CPU. `chb06`'s first attempt reproduced the **same symptom, one
level worse**: the driver process was OOM-killed three separate times purely from upload-phase memory
pressure, before Phase B's own (now-fixed) bug even ran. `chb06`'s 18 files are individually much larger
than any other subject's (up to ~170 MB EDF → ~266 MB each for `.filtered.npy`/`.raw.npy`), so up to 18
of those concurrently-running Phase A threads each holding a large in-memory array is a plausible,
compounding contributor to the same memory pressure that (separately) caused Phase B's hard crash. **This
report does not claim the concurrency issue is now fixed — it isn't, and wasn't touched**, per the
original prompt's own item 0.2 ("Phase A upload-thread concurrency stays unfixed for this step... don't
fix it as a side effect"). Both are flagged here for the record as **two separate, only-partially-fixed
memory issues**: Phase B's whole-subject-array bug (now fixed, generalized, bit-identical) and Phase A's
unbounded concurrency (still open, still deferred, still worth capping before the defense if an even
larger subject or a slower/more memory-constrained machine is ever used).

## 6 · Completion checks (original prompt §4)

1. **Database table lists exactly 8 subjects** — the full TEST allowlist, no more, no fewer, no
   synthetic subject:

   ```
   chb03 | View   | 38 files | 1d:14:00:06
   chb06 | View   | 18 files | 2d:18:44:06
   chb13 | Viewed | 2  files | 02:00:00
   chb14 | View   | 26 files | 1d:02:00:00
   chb15 | View   | 40 files | 1d:16:00:36
   chb16 | View   | 19 files | 19:00:00
   chb17 | View   | 21 files | 21:00:24
   chb18 | View   | 36 files | 1d:11:38:05
   ```

2. **Final `pytest -v`: 4/4** (raw output, §7.1).

3. **Comparison table, all 8 subjects** — for `SZSCAN_SPEC_v5.md` open item **O4** ("which subject to
   use for the live-upload scenario — chosen by real file count"). Numbers only; **no subject is picked
   here**, that stays Boti's call:

   | Subject | Files | Hours (real) | Phase A+B (s) | rate (s/h) | Process/PELT (s) | rate (s/h) | `pen_mult` | events/day |
   |---|---|---|---|---|---|---|---|---|
   | `chb13` | 2  | 2.000  | *(not measured this way — built in Step 3, before this timing method existed)* | | | | | |
   | `chb16` | 19 | 19.000 | 271.56 | 14.29 | 68.03  | 3.58  | 1.0 | 51.79 |
   | `chb17` | 21 | 21.007 | 572.84 | 27.27 | 166.82 | 7.94  | 2.0 | 41.13 |
   | `chb14` | 26 | 26.000 | 607.01 | 23.35 | 171.87 | 6.61  | 5.0 | 29.54 |
   | `chb18` | 36 | 35.635 | 813.95 | 22.84 | 389.86 | 10.94 | 2.0 | 30.98 |
   | `chb03` | 38 | 38.002 | 462.70 | 12.18 | 138.79 | 3.65  | 2.0 | 34.74 |
   | `chb15` | 40 | 40.010 | 562.69 | 14.06 | 127.65 | 3.19  | 5.0 | 44.39 |
   | `chb06` | 18 | 66.735 | 726.05 | 10.88 | 293.48 | 4.40  | 2.0 | 29.13 |

   `chb13`'s row is left honestly blank rather than backfilled with an estimate — it was built through
   the original Step 3 flow, before this Create-New→Process-timing measurement method existed, and only
   has 2 of its 33 real files (the `chb13` precedent noted throughout `BUILD_PROGRESS.md`), so it isn't
   comparable to the other 7 rows' full-file-set figures anyway.

## 7 · Raw command output

### 7.1 Final `pytest -v`

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

============================== 4 passed in 2.42s ==============================
```

Guards were also re-run and confirmed 4/4 **after every individual subject** (per the original prompt's
step 3.7), not just at the very end — each of the 6 per-subject runs above included its own green
4/4 check before moving to the next subject.

### 7.2 `git status`

```
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   web_demo/BUILD_PROGRESS.md
	modified:   web_demo/backend/pipeline_demo.py

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	bme11/
	web_demo/CC_STEP9_PHASE2_PROGRESS.md
	web_demo/CC_STEP9_PHASE2_PROMPT.md
	web_demo/CC_STEP9_PHASE2_RESUME_PROMPT.md
```

A commit (`864d170`, made outside this session, between two of this session's own steps) already
absorbed the earlier checkpoint/checkpoint-fix work — `SZSCAN_SPEC_v5.md` and the other previously-
modified backend/frontend files from Step 8/9 phase 1/1b no longer show here as a result, not because
this phase 2 session touched them. `bme11/` is Boti's own, unrelated, pre-existing untracked directory
(noted in every prior report). This report itself and `CC_STEP9_PHASE2_REPORT.md` are not yet shown
above since `git status` was run before writing them.

### 7.3 `git diff --stat`

```
 web_demo/BUILD_PROGRESS.md        | 16 +++++++------
 web_demo/backend/pipeline_demo.py | 48 ++++++++++++++++++++++++++++++++++-----
 2 files changed, 51 insertions(+), 13 deletions(-)
```

Exactly this session's own two edits: the §1 doc note (§1 above) and the `pipeline_demo.py` memory fix
(§5.2 above). All DB/upload state changes (the 6 new real subjects) live in `szscan.db` and
`uploads/`, both gitignored, so they don't appear in a text diff.

---

**Stopping here. No `git add`/`commit`/`push` was run.** Phase 2 (Step 9's remaining scope) is complete
— all 8 allowlisted subjects are real, fully processed, cached subjects in the DB. Open items still
carried forward, not resolved by this report: `SZSCAN_SPEC_v5.md` O4 (which subject to actually use for
the live-upload defense scenario — numbers are now available in §6.3 above, the choice is still Boti's),
the `DELETE` endpoint's on-disk cleanup (`BUILD_PROGRESS.md §14`), and Phase A's unbounded upload-thread
concurrency (§5.3 above — still open, now with stronger evidence it can matter, not just for timing but
for genuine memory pressure on large subjects).
