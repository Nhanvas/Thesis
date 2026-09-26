# CC_STEP9_CHECKPOINT_REPORT.md — Step 9 checkpoint: record phase 1 + 1b, before phase 2

Both items of `CC_STEP9_CHECKPOINT_PROMPT.md` done. **Documentation-only** — no pipeline code
touched, no upload, no DB state changed. No `git add`/`commit`/`push` run. Phase 2 was not started.

## 1 · `SZSCAN_SPEC_v5.md §1.7` — C23 note added

Original sentence(s) left untouched; the note was appended right after the existing bullet list, per
precedent (C18–C22). Exact diff:

```diff
@@ -253,6 +253,17 @@ EDF reading, gamma-AEC, GAE forward — all much smaller).
   scenario should pick the subject with **the fewest files**; the exact number is measured when building
   the cache.

+> **PELT-cost correction (C23, 2026-09-26):** measured on `chb16` (19 real files, 19.0 h, via the real
+> Create-New→Process flow, `CC_STEP9_PHASE1B_REPORT.md`): PELT alone = **3.58 s/hour of EEG**, only
+> **~25%** of Phase A+B's own wall-clock (**14.29 s/hour**, real upload flow) for the same subject —
+> PELT is **not** the dominant cost; the bullet above was written against the older, component-level
+> cost figures at the top of this section, not a real end-to-end measurement. Real Phase A+B
+> wall-clock (14.29 s/hour, real HTTP upload flow) also runs **~46% higher** than the old
+> `9.76 s/hour` serial-CLI figure still quoted in `CLAUDE.md` — explained by genuine upload-transfer
+> overhead plus unbounded per-file Phase A thread concurrency (up to 19 concurrent threads observed on
+> a 4-physical/8-logical-core dev machine). The concurrency finding is recorded as an **open item, not
+> fixed**.
+
 ---

 ## 2 · DATA SCOPE
```

**Note:** `git diff` on this file also shows a second hunk (the C22 parenthetical on §7.2's
`Number of Seizures` bullet). That hunk predates this session — `SZSCAN_SPEC_v5.md` was already
listed as modified in `git status` before this checkpoint started (Step 8 fix round 1 work) — and was
not touched here.

## 2 · `BUILD_PROGRESS.md` — Step 9 status updated + new §15

### 2.1 Status table, row 9 — changed from "not started" to:

```
| 9 — cache 8 subjects + pick live-upload subject | **IN PROGRESS** — phase 1 & 1b done; phase 2 (`chb03`/`chb06`/`chb14`/`chb15`/`chb17`/`chb18` still need a real upload+process) not started | see §15 below |
```

### 2.2 "Where to resume" — changed to:

```
**Where to resume:** Step 9 phase 2 — upload + process the 6 remaining real subjects
(`chb03`/`chb06`/`chb14`/`chb15`/`chb17`/`chb18`) through the real Create-New→Process flow. Before
drafting that prompt: `chb16`'s upload session is sitting `done: true`, unacknowledged — someone
needs to open the app and click through the "Processing complete" panel first (one-subject-in-flight
rule), and §14 below has two open decisions (file-count-per-subject scope; the `DELETE` endpoint's
on-disk cleanup) that are Boti's call, not something to assume an answer to. Also still read §10.4
below (one open item from Step 7 not yet resolved) and `STEP8_9_PREDEFENSE_CHECKLIST.md` (uploaded
alongside this file — report needs + the fixed Tier 2 rules for Step 9, agreed with Project #1
2026-09-25). Don't assume anything on that checklist is already done just because it's listed there.
```

(Caught and fixed one drafting error before finalizing: this paragraph first read "§14a below" — a
section that doesn't exist. Corrected to "§14" (the existing Open items section) since that's where
the two decisions actually live; the status-table row (§2.1 above) already correctly pointed to §15.)

### 2.3 Open items (§14) — two new items added, under a new "New from Step 9 phase 1/1b" heading:

```
**New from Step 9 phase 1/1b, decisions needed before phase 2 (both Boti's call, see §15):**

- [ ] **File-count-per-subject scope** for the 6 remaining subjects (`chb03`/`chb06`/`chb14`/`chb15`/
      `chb17`/`chb18`) — full real file set (246.39 h combined) vs. a representative subset, per the
      `chb13` precedent (2 of its 33 real files were used, not the full subject).
- [ ] `DELETE /api/subjects/{id}` doesn't clean up `uploads/{subject_id}/` on disk (only the DB rows) —
      confirmed by reading `main.py` directly. Deliberately deferred to a final cleanup pass before the
      demo is considered complete, per Boti's own decision — **not** an active bug needing a fix now.
```

### 2.4 New `## 15 · Step 9 — detail (phase 1 + phase 1b; phase 2 not started)` section

Added after §14 (Open items), rather than inserted between §11 (Step 8) and §12 (Integrity incident),
to avoid renumbering every downstream cross-reference (§10.4, §11.3, §12, §13, §14 all cite each
other by number). Full text added:

```
## 15 · Step 9 — detail (phase 1 + phase 1b; phase 2 not started)

**Scope so far:** Step 9 is **cache 8 subjects + pick live-upload subject** per
`DEMO_BUILD_HANDOFF.md §6` row 9. Only the first two of its three planned phases have run. **Reports:**
`CC_STEP9_PROMPT.md`/`CC_STEP9_PHASE1_REPORT.md` (phase 1), `CC_STEP9_PHASE1B_PROMPT.md`/
`CC_STEP9_PHASE1B_REPORT.md` (phase 1b), `CC_STEP9_CHECKPOINT_PROMPT.md` (this section's own source).
Guards 4/4 green throughout both phases. No `git add`/`commit`/`push` run in either.

### 15.1 Phase 1 — 8-subject inventory + synthetic-data cleanup

Every real-vs-synthetic call was made by **SHA-256 comparison against the actual dataset file on
disk**, not filename inference or the DB's own stored duration:

- **`chb14`, `chb15`, `chb16`** (all three) held synthetic data — truncated, re-encoded
  `chb15_NN_short.edf` clips filed under 3 different subject ids, byte-different from every real EDF.
  Deleted via the app's real Delete flow (DB rows) plus manual cache-directory cleanup — the
  `DELETE /api/subjects/{id}` endpoint itself never touches `uploads/{subject_id}/` on disk (read
  directly in `main.py`; now tracked as an open item in §14, deliberately deferred, not a bug to fix
  now).
- **`chb06`** has **no subject row at all** in the DB — the "18-file, full Progress" state Boti's own
  screenshots showed is not the DB's current state. It does have an orphaned, never-finalized partial
  upload on disk: 1 real, byte-identical `chb06_01.edf` (Phase A + raw cache, no score/PELT, no DB
  row). Left in place, not deleted, for phase 2 to possibly reuse.
- **`chb03`** similarly has an orphaned partial upload (2 real, byte-identical files, Phase A cache
  only), zero DB row. Also left in place.
- **`chb17`/`chb18`** have no data anywhere — never touched by any upload.
- **`chb13`** is the only subject with genuinely real, fully-processed, cached data (2 of its 33 real
  files, matching the precedent noted in §14).
- Real file count / total duration on disk, read from each EDF's own header (not the DB, not
  estimated): `chb03` 38 files/38.00 h, `chb06` 18/66.74 h, `chb13` 33/33.00 h (2 already uploaded),
  `chb14` 26/26.00 h, `chb15` 40/40.01 h, `chb16` 19/19.00 h, `chb17` 21/21.01 h, `chb18` 36/35.64 h —
  **246.39 h total across the 7 subjects still needing a real upload+process at the time** (before
  phase 1b processed `chb16`).
- A time-estimate gap was flagged, not glossed over: the existing `9.76 s/hour` figure (`CLAUDE.md`)
  measures only Phase A+B (`pipeline_demo.process_file`) — it never calls
  `cpd_pipeline_v14.detect_events` (PELT), which the real app's Create-New flow runs as a **separate**
  stage, 6 times per subject (once per `pen_mult` in `DEFAULT_PENS`). No isolated PELT timing existed
  anywhere in the repo at the start of phase 1 — resolved in phase 1b (§15.2).

### 15.2 Phase 1b — real PELT / Phase A+B timing, measured on `chb16`

Driven by literally replaying `web_demo/frontend/src/api.js`'s own upload sequence against the running,
unmodified server (real cookie-session login, real `POST /api/uploads/current` →
19× `POST /api/uploads/current/files` sequential → `POST /api/uploads/current/process`) — not a CLI
shortcut, because `claude-in-chrome`'s `file_upload` tool caps combined attachments at 10 MB, far
below `chb16`'s ~915 MB of real EDFs. A parallel poller logged every state transition's wall-clock
timestamp from `GET /api/uploads/current`; no source file in `web_demo/` was modified to take the
measurement.

- **Phase A+B real wall-clock:** 271.56 s for 19.00 h → **14.29 s/hour** — **1.46×** the existing
  `9.76 s/hour` figure. Two real causes, not a bug: genuine upload-transfer overhead (~58.4 s total),
  and unbounded per-file Phase A thread concurrency (`upload_manager.py` spawns one background thread
  per file the instant its bytes land, not waiting for the previous file — up to 19 concurrent threads
  observed on this dev machine's 4-physical/8-logical-core CPU). The concurrency finding is an **open
  item, not fixed** (§14).
- **Process/PELT alone:** 68.03 s for 19.00 h → **3.58 s/hour** — only **~25%** of Phase A+B's own
  wall-clock for the same subject. Recorded in `SZSCAN_SPEC_v5.md §1.7` as **C23** (this checkpoint):
  PELT is **not** the dominant cost, contradicting §1.7's own prior text.
- **Revised total-time estimate for the 6 subjects still needing upload** (`chb03`/`chb06`/`chb14`/
  `chb15`/`chb17`/`chb18`, 227.3 h combined): **~50.5 min** using phase 1's `9.76 s/h` lower bound +
  real PELT, or **~67.7 min** using this run's own real `14.29 s/h` rate + real PELT — either way,
  comfortably inside one working session, not the "long unattended run" phase 1 flagged as a risk.
- No crash, no retry, no error at this scale; `chb16`'s operating point converged normally
  (`pen_mult = 1.0`).
- **`chb16` kept in the DB deliberately** (memo `"CC_STEP9_PHASE1B timing run"`), fully and genuinely
  processed through the real flow — all 19 real files SHA-256-confirmed, 41 events recorded. This is
  `chb16` done for phase 2 already, not throwaway work. One loose end, left deliberately: the in-memory
  upload session is still `done: true`, **unacknowledged** — the exact state a real user leaves it in
  before clicking through the "Processing complete" panel. This blocks starting a **new** Create-New
  session system-wide (one-subject-in-flight rule) until someone opens the app and dismisses it; it is
  a manual UI action for Boti, not something for a future prompt to script around, and does not affect
  `chb16`'s own already-committed DB row.

### 15.3 Not yet done — phase 2

Uploading and processing the other 6 real subjects (`chb03`, `chb06`, `chb14`, `chb15`, `chb17`,
`chb18`) has **not started**. Blocked on: (a) `chb16`'s unacknowledged upload session being dismissed
in the app first, (b) Boti's decision on file-count-per-subject scope (§14). No pipeline, upload, or
DB state was touched writing this section — documentation only.
```

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

============================== 4 passed in 2.19s ==============================
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
	web_demo/CC_STEP9_CHECKPOINT_PROMPT.md
	web_demo/CC_STEP9_PHASE1B_PROMPT.md
	web_demo/CC_STEP9_PHASE1B_REPORT.md
	web_demo/CC_STEP9_PHASE1_REPORT.md
	web_demo/CC_STEP9_PROMPT.md

no changes added to commit (use "git add" and/or "git commit -a")
```

`web_demo/BUILD_PROGRESS.md` and `web_demo/SZSCAN_SPEC_v5.md` were already listed as modified before
this checkpoint started (prior Step 8 session work, per the conversation's own initial git status) —
this checkpoint added further edits on top of those, not a fresh diff from a clean baseline. The other
5 modified files (`db.py`, `export_txt.py`, `main.py`, `api.js`, `AnalysisScreen.jsx`) and the
untracked files above were **not touched** by this checkpoint at all.

### 3.3 `git diff --stat`

```
 web_demo/BUILD_PROGRESS.md                       | 632 +++++++++++++++++++----
 web_demo/SZSCAN_SPEC_v5.md                       |  16 +-
 web_demo/backend/db.py                           |  17 +
 web_demo/backend/export_txt.py                   | 142 ++++-
 web_demo/backend/main.py                         |  27 +
 web_demo/frontend/src/api.js                     |  24 +
 web_demo/frontend/src/screens/AnalysisScreen.jsx |  13 +-
 7 files changed, 766 insertions(+), 105 deletions(-)
```

This is the full working-tree diff (includes the pre-existing Step 8 changes to `BUILD_PROGRESS.md`
and `SZSCAN_SPEC_v5.md`, plus the 5 untouched-by-this-checkpoint files above). This checkpoint's own
edits are exactly the two diffs/additions quoted in §1 and §2.

---

**Stopping here per the prompt. No `git add`/`commit`/`push` was run. Phase 2 was not started; no
pipeline, upload, or DB state was touched.**
