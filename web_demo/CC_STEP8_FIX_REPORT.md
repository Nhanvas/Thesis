# CC_STEP8_FIX_REPORT.md — Step 8 fix round 1

## 1 · Summary

All four items from `CC_STEP8_FIX_PROMPT.md`, done in order:

1. **Score formatting:** `export_txt.py`'s `_attribution_rows` now prints each channel
   score as a fixed `f"{row['score']:.6f}"` string instead of the bare rounded float —
   print-format only, the underlying stored/computed precision (`attribution.py`'s
   `round(float(per_channel[i]), 6)`, unchanged since Step 7 fix round 2) was not
   touched.
2. **File order verified, not just claimed:** `db.list_files_by_filename`'s query
   already reads `"... ORDER BY filename"` — genuinely sorts by file-name string, not
   `meas_date`. No fix was needed here; confirmed by quoting the line directly (§2
   below) and by checking every subject currently in the DB for a file-name-vs-
   Recording-N ordering difference — none exists in the current DB.
3. **Guard-2 workaround comment added:** a 3-line comment immediately above
   `_SEIZURE_COUNT_LABEL`'s definition in `export_txt.py`, referencing this fix round
   and the original report section without spelling out the guarded phrase. Guards
   re-run after adding it: still 4/4 (§4 below, raw output).
4. **`N`-interpretation locked in the spec:** added a dated `C22` parenthetical to
   `SZSCAN_SPEC_v5.md §7.2`'s existing "In the export file:" bullet, recording the
   author-confirmed reading (AI incl. Rejected + Human, combined) as settled, not a
   placeholder — no other wording in §7.2/§7.3 touched.

Guards 4/4 green throughout. No `git add`/`commit`/`push` was run.

## 2 · Item 2 — file order, quoted verbatim

`web_demo/backend/db.py`, `list_files_by_filename` (the function `export_txt.py`'s
`build_subject_export` calls to get a subject's files):

```python
def list_files_by_filename(subject_id: str) -> list[dict]:
    """File order for the .txt export (SZSCAN_SPEC_v5.md §7.1): file-NAME order, the
    original CHB-MIT convention -- deliberately NOT `_subject_dict`'s meas_date/
    start_time order (C17), which only drives the UI's 'Recording N' display and
    Previous/Next."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, subject_id, filename, start_time, duration_seconds, status "
        "FROM files WHERE subject_id = ? ORDER BY filename",
        (subject_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
```

The exact `ORDER BY` clause is **`ORDER BY filename`** — a genuine SQL sort on the
file-name string column, not `start_time`/`meas_date` and not DB insertion/row order.
This was already correct before this fix round; **no code change was needed for item
2**, only the verification below.

**Differing-order-subject check** — every subject currently in the DB, file-name order
vs. `meas_date`/Recording-N order, listed directly (not guessed):

```
chb13 Recording-N order (by meas_date): ['chb13_02.edf', 'chb13_03.edf']
chb13 file-name order (sorted):         ['chb13_02.edf', 'chb13_03.edf']
chb13 same

chb15 Recording-N order (by meas_date): ['chb15_01_short.edf', 'chb15_02_short.edf']
chb15 file-name order (sorted):         ['chb15_01_short.edf', 'chb15_02_short.edf']
chb15 same

chb14 Recording-N order (by meas_date): ['chb15_01_short.edf', 'chb15_02_short.edf', 'chb15_03_short.edf', 'chb15_04_short.edf', 'chb15_05_short.edf', 'chb15_06_short.edf']
chb14 file-name order (sorted):         ['chb15_01_short.edf', 'chb15_02_short.edf', 'chb15_03_short.edf', 'chb15_04_short.edf', 'chb15_05_short.edf', 'chb15_06_short.edf']
chb14 same

chb16 Recording-N order (by meas_date): ['chb15_01_short.edf', 'chb15_02_short.edf', 'chb15_03_short.edf', 'chb15_04_short.edf', 'chb15_05_short.edf', 'chb15_06_short.edf', 'chb15_07_short.edf', 'chb15_08_short.edf', 'chb15_09_short.edf', 'chb15_10_short.edf', 'chb15_11_short.edf', 'chb15_12_short.edf']
chb16 file-name order (sorted):         ['chb15_01_short.edf', 'chb15_02_short.edf', 'chb15_03_short.edf', 'chb15_04_short.edf', 'chb15_05_short.edf', 'chb15_06_short.edf', 'chb15_07_short.edf', 'chb15_08_short.edf', 'chb15_09_short.edf', 'chb15_10_short.edf', 'chb15_11_short.edf', 'chb15_12_short.edf']
chb16 same
```

**No subject currently in the DB (the 4 present — `chb13`, `chb14`, `chb15`, `chb16` —
covering both the real allowlist entries and the known synthetic test subjects) has
files whose file-name order and Recording-N order actually differ.** Stated plainly, not
fabricated: I did not create or rename a file to force a difference. Per the prompt's own
fallback, the `ORDER BY filename` line quoted above is sufficient evidence on its own
that the export follows file-name order, independent of whether any current subject's
data happens to exercise the distinction.

## 3 · Item 1 — before/after score formatting

Regenerated the `chb13` export and located the exact two scores the original report
flagged:

| Score | Before (original report, `CC_STEP8_REPORT.md §6.1`) | After (this fix) |
|---|---|---|
| Event 4, rank 8, `FZ-CZ` | `1.27291` (5 digits after the point) | `1.272910` |
| Event 4, rank 18, `FP2-F4` | `0.050504` (already 6 digits) | `0.050504` (unchanged, confirmed) |

Raw lines from the regenerated export:

```
      8  FZ-CZ  1.272910  Unreviewed
      18  FP2-F4  0.050504  Unreviewed
```

Every score in the Channel Attribution tables now has exactly 6 digits after the
decimal point, regardless of trailing zeros.

## 4 · Item 3 — comment text added + guard re-run

Added immediately above `_SEIZURE_COUNT_LABEL`'s definition in `export_txt.py`:

```python
# String deliberately split across two literals -- see CC_STEP8_REPORT.md §5.4 / this
# file's fix-round-1 item 3 for why the whole phrase must never appear as one literal
# in this tree.
_SEIZURE_COUNT_LABEL = "Number of " + "Seizures in File"
```

Guard re-run after adding it (raw output):

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

============================== 4 passed in 4.96s ==============================
```

`test_guard_no_seizure_fields_at_runtime` staying green confirms the added comment did
not reintroduce the guarded phrase as one literal anywhere in the tree.

## 5 · Item 4 — exact diff added to `SZSCAN_SPEC_v5.md §7.2`

```diff
--- a/web_demo/SZSCAN_SPEC_v5.md
+++ b/web_demo/SZSCAN_SPEC_v5.md
@@ -651,7 +651,10 @@ file).
 - **In the export file:** the line `Number of Seizures in File: N` is kept exactly per the original
   CHB-MIT convention (for machine cross-referencing), but sub-entries are still numbered `Event 1`,
   `Event 2`… matching exactly the numbering the clinician already saw on the UI. Both naming schemes
-  coexisting is **deliberate**, not a bug.
+  coexisting is **deliberate**, not a bug. (**C22, 2026-09-25:** `N` = the count of every `Event` block
+  listed below that file — AI (including Rejected) + Human, combined — confirmed by the author as the
+  settled reading, not a placeholder; was an open judgment call in `CC_STEP8_REPORT.md §3`, closed in
+  `CC_STEP8_FIX_REPORT.md §5`.)
 
 ### 7.3 Structure
```

Nothing else in §7.2/§7.3 was touched. `C22` is the next unused note number (the file's
highest prior note was `C21`, in the Step 7 fix round 2 material).

## 6 · Raw command output

### 6.1 `pytest -v` (final)

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

============================== 4 passed in 5.27s ==============================
```

### 6.2 `git status`

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
	web_demo/CC_STEP8_FIX_PROMPT.md
	web_demo/CC_STEP8_PROMPT.md
	web_demo/CC_STEP8_REPORT.md

no changes added to commit (use "git add" and/or "git commit -a")
```

`BUILD_PROGRESS.md`'s modification, `bme11/`, and the `CC_STEP8_PROMPT.md`/
`CC_STEP8_REPORT.md` files predate this fix round (Step 8 itself and earlier) — this
round only touched `export_txt.py` and `SZSCAN_SPEC_v5.md`, plus adds this report and
`CC_STEP8_FIX_PROMPT.md` (the prompt file itself, not created by me) as untracked.

### 6.3 `git diff --stat`

Repo-wide (nothing has been committed since before Step 8, so this stat spans Step 8's
original implementation plus this fix round together — there is no earlier commit
boundary to diff against for "this round alone"):

```
 web_demo/SZSCAN_SPEC_v5.md     |   5 +-
 web_demo/backend/export_txt.py | 142 ++++++++++++++++++++++++++++++++++++++++-
 2 files changed, 145 insertions(+), 2 deletions(-)
```

This fix round's own edits to `export_txt.py` were: (a) `.6f` formatting in
`_attribution_rows`'s return line, (b) an expanded docstring sentence on the same
function noting the fixed-width fix, and (c) the 3-line comment above
`_SEIZURE_COUNT_LABEL` (item 3). Everything else in the file's `+142` count is Step 8's
original (previously reported, unchanged this round) implementation.

---

**Stopping here per the prompt. No `git add`/`commit`/`push` was run.**
