# CC_STEP8_FIX2_REPORT.md — Step 8 fix round 2

## 1 · Summary

All three items from `CC_STEP8_FIX2_PROMPT.md`, done in order:

1. **Export button styling — real bug, fixed.** The enabled and disabled states shared identical
   base classes (`bg-white/70 text-text-muted`); only `disabled:opacity-50` (which only ever applies
   while the HTML `disabled` attribute is actually set) distinguished them. So the genuinely-enabled
   button still rendered at full opacity with the same muted 70%-white background / grey text as its
   disabled state, instead of the solid white / near-black styling every sibling button
   (`Previous`/`Next`/`Viewed`) uses. Fixed in `AnalysisScreen.jsx`: the button's className is now
   conditional on `exportEnabled`, matching its siblings exactly when enabled and keeping the
   original muted look, unchanged, when disabled. Verified live via computed style on 2 subjects.
2. **`.6f` score-format regression — false alarm, confirmed, no code change.** The fix was still on
   disk exactly as fix round 1 left it. Root cause: the running backend process predated that edit
   being saved and was never reloaded (no `--reload` flag) — stale bytecode. Restarted the backend;
   a fresh export confirmed every score is correctly `.6f`-formatted.
3. **`BUILD_PROGRESS.md` updated** — new §11 "Step 8 — detail" inserted, Status table/", Where to
   resume"/Open items updated, sections renumbered (§11→§14 below).

Guards 4/4 green throughout. No `git add`/`commit`/`push` was run.

## 2 · Item 1 — Export button computed-style difference, fix, and re-verification

### 2.1 The exact computed difference found

Read via the DOM (`getComputedStyle`, not by eye) on `chb13_03.edf`'s Analysis screen (Progress
`02/2`, genuinely enabled) **before** touching any code:

```json
{
  "exportBtn": {
    "disabled": false,
    "backgroundColor": "rgba(255, 255, 255, 0.7)",
    "color": "rgb(100, 116, 139)",
    "opacity": "1"
  },
  "viewedBtn": {
    "disabled": false,
    "backgroundColor": "rgb(255, 255, 255)",
    "color": "rgb(15, 23, 42)",
    "opacity": "1"
  }
}
```

Both buttons are equally *not* disabled (`opacity: 1` on both — `disabled:opacity-50` correctly
never applied), but the Export button's own resting-state classes (`bg-white/70 text-text-muted`)
never changed based on `exportEnabled` at all, only its `disabled` attribute did. So an enabled
Export button still computed `rgba(255,255,255,0.7)` background / `rgb(100,116,139)` (`#64748B`,
the `text-muted` token) text — genuinely, measurably different from the sibling `Viewed` button's
`rgb(255,255,255)` / `rgb(15,23,42)` (`#0F172A`, the `text` token) — **not** a JPEG-compression
illusion, confirmed by reading `web_demo/frontend/src/index.css`'s own token definitions
(`--color-text: #0F172A`, `--color-text-muted: #64748B`) against the computed values above.

### 2.2 Fix

`web_demo/frontend/src/screens/AnalysisScreen.jsx`, the Export `<button>`'s `className`:

```diff
-          className="bg-white/70 text-text-muted rounded-control px-3 py-1.5 text-xs font-medium disabled:opacity-50 shrink-0"
+          className={`rounded-control px-3 py-1.5 text-xs font-medium shrink-0 ${
+            exportEnabled ? 'bg-white text-text' : 'bg-white/70 text-text-muted opacity-50'
+          }`}
```

Only the resting-state styling changed — `onClick`, the enablement boolean (`exportEnabled`), the
`disabled` attribute, and every other button were untouched. `opacity-50` is now applied via the
conditional (not the `disabled:` variant) so the disabled look is pixel-identical to before.

### 2.3 Re-verification, 2 subjects, computed style + screenshots

**`chb13_03.edf`** (real data, `Viewed`/`Viewed`, Progress `02/2`) — after the fix:

```json
{
  "exportBtn": {"disabled": false, "backgroundColor": "rgb(255, 255, 255)", "color": "rgb(15, 23, 42)", "opacity": "1"},
  "viewedBtn":  {"disabled": false, "backgroundColor": "rgb(255, 255, 255)", "color": "rgb(15, 23, 42)", "opacity": "1"},
  "prevBtn":    {"disabled": false, "backgroundColor": "rgb(255, 255, 255)", "color": "rgb(15, 23, 42)", "opacity": "1"}
}
```

**`chb15`** — the prompt's own example (`chb06_06.edf`, 18/18) could not be reproduced: `chb06` is
not currently uploaded into the demo DB (`SELECT DISTINCT subject_id FROM files` returns only
`chb13`/`chb14`/`chb15`/`chb16`), and processing a fresh ~4-hour, 18-file subject was out of scope
for a one-line styling fix. Used the synthetic test subject `chb15` as the second live subject
instead (same disclosed-substitution pattern the original Step 8 report used in its own §5.2):

- Recorded `chb15`'s pre-test state first: files 12/13 both `Viewing` (`chb15_01_short.edf`,
  `chb15_02_short.edf`).
- Opened `chb15_01_short.edf` (Progress `00/2`): Export `disabled: true`, `backgroundColor:
  rgba(255, 255, 255, 0.7)`, `color: rgb(100, 116, 139)`, `opacity: 0.5` — disabled look confirmed
  unchanged by the fix.
- Clicked the real `Viewed` button (→ `01/2`, Export still `disabled: true`), then `Next »`, then
  the real `Viewed` button on file 2 (→ `02/2`).
- Re-read the Export button: `disabled: false`, `backgroundColor: rgb(255, 255, 255)`, `color: rgb(15,
  23, 42)`, `opacity: 1` — identical to the `Viewed` button on the same screen.
- **Reverted `chb15` back to its pre-test state** (`UPDATE files SET status='Viewing' WHERE id IN
  (12,13)`, confirmed both rows back to `Viewing`) so it does not look like a reviewed subject.

Both subjects, at genuine full progress, now render the Export button identically to its siblings —
both by computed style and visually (screenshots taken of both header clusters, e.g. `⇩ Export`
rendering solid white/dark-text next to `Previous`/`Next`/`Viewed`, no longer visually distinct).

## 3 · Item 2 — `.6f` score-format: stale server, not a regression

### 3.1 The `.6f` line, confirmed still on disk

`web_demo/backend/export_txt.py`, `_attribution_rows`:

```python
    return [
        f"      {row['rank']}  {row['channel']}  {row['score']:.6f}  {row['status'] or 'Unreviewed'}"
        for row in payload["rows"]
    ]
```

Unchanged since fix round 1 — exactly the line `CC_STEP8_FIX_REPORT.md §3` reported adding.

### 3.2 Root cause: a stale, un-reloaded backend process

The running backend was started **without** `--reload`:

```
CommandLine = "python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000
CreationDate = 2026-09-25 13:19:23 (local)
```

`export_txt.py`'s on-disk mtime at the time this fix round started: `2026-09-25 14:21:44` (local,
same day) — **over an hour after** the backend process had already started and loaded its Python
bytecode into memory. With no `--reload` flag, a process started before an edit is saved keeps
serving the pre-edit code indefinitely until it is restarted — fully explaining Boti's un-fixed
`chb13-summary.txt` download (`8  FZ-CZ  1.27291`) without any code being wrong. This is exactly the
stale-process scenario the prompt's item 2 anticipated.

The backend was restarted (old process on port 8000 killed, a fresh `uvicorn main:app --host
127.0.0.1 --port 8000` started from `web_demo/backend`, confirmed listening and answering `200` on
`/docs` before proceeding).

### 3.3 Fresh export, confirmed correct

Triggered through the live app (real `GET /api/subjects/chb13/export` request, `200`, fired by
clicking the real, now-correctly-styled Export button on `chb13_03.edf`), then re-fetched the same
endpoint directly (`fetch('/api/subjects/chb13/export', {credentials:'include'})`, same authenticated
session) to inspect the full byte content:

```
Total score lines checked: 90
Lines not exactly 6 decimal digits: 0
```

The exact previously-flagged line, from the fresh export:

```
      8  FZ-CZ  1.272910  Unreviewed
```

**No code change was needed for item 2** — Boti's uploaded file was a download from before this
session's own backend restart, not a regression.

## 4 · Item 3 — `BUILD_PROGRESS.md` update

Inserted a new **`## 11 · Step 8 — detail`** section (subsections 11.1 initial build, 11.2 fix round
1, 11.3 this fix round), in the same style/detail level as the existing §7–§10 step-detail sections,
placed immediately after §10 (Step 7) and before the Integrity-incident section — sourced from
`CC_STEP8_REPORT.md`, `CC_STEP8_FIX_REPORT.md`, and this round's own findings above.

**Sections renumbered** (everything from the old Integrity-incident section onward shifted by +1):

| Before | After |
|---|---|
| `## 11 · Integrity incident …` | `## 12 · Integrity incident …` |
| `## 12 · Report material for Project #1 …` | `## 13 · Report material for Project #1 …` |
| `## 13 · Open items going into Step 8` | `## 14 · Open items going into Step 9` (title updated — Step 8 is now done) |

Every in-file cross-reference to the old `§11`/`§12`/`§13` numbers was updated to match (checked with
a repo-wide grep for `§1[0-4]` after editing, listed below) — 4 pre-existing `§13` references (Status
table intro, the "one open item" line, and 2 items in the old open-items section itself) now read
`§14`; no other renumbered section had pre-existing cross-references pointing at it.

**Also updated, directly Step-8-related and otherwise left stale:**

- Status table row 8 → **DONE**, short note (initial build + 2 fix rounds).
- "Where to resume" → now points at Step 9 (was still pointing at "Step 8, not yet planned").
- §2 repo map: `export_txt.py`'s "still a stub" line replaced with what it now does + a pointer to
  §11; `test_guards.py`'s "last raw-console check" pointer moved from `cf5ee88`'s pre-commit run to
  this round's own run; `SZSCAN_SPEC_v5.md`'s note-history line extended to mention `C22`;
  `AnalysisScreen.jsx`'s entry extended to mention the Step 8 Export wiring + this round's className
  fix; added `CC_STEP8*` to the tracked-files list (was missing, unlike every other step's own
  prompt/report files).
- §14 (old §13) Open items: added a new **"Handled in the Step 8 chats"** bullet list (matching the
  existing Step-7 precedent) checking off both of this round's findings; the "Deferred on purpose …
  not before Step 8" header text updated to "not before Step 9" (Step 8 is now done, so the old
  wording was stale) — **no other item in that section was touched**, since none of the pre-existing
  open items were about either of this round's two findings.

Full section-heading grep after editing, confirming no leftover old numbers:

```
## 11 · Step 8 — detail
## 12 · Integrity incident (from Step 1) — status: resolved, cause still unconfirmed
## 13 · Report material for Project #1 (per `PROJECT2_SETUP.md §9.2(D)`)
## 14 · Open items going into Step 9
```

## 5 · Raw command output

### 5.1 `pytest -v` (final, after the backend restart and all edits)

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

============================== 4 passed in 2.20s ==============================
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
	web_demo/CC_STEP8_FIX_PROMPT.md
	web_demo/CC_STEP8_FIX_REPORT.md
	web_demo/CC_STEP8_PROMPT.md
	web_demo/CC_STEP8_REPORT.md
	web_demo/CC_STEP9_PROMPT.md

no changes added to commit (use "git add" and/or "git commit -a")
```

`SZSCAN_SPEC_v5.md`/`backend/db.py`/`backend/main.py`/`frontend/src/api.js` and most of
`export_txt.py`'s diff predate this round (Step 8 initial build + fix round 1) — this round's own
edits are `AnalysisScreen.jsx` (the Export button className, §2.2) and `BUILD_PROGRESS.md` (§4).
`CC_STEP9_PROMPT.md` and `bme11/` predate this session (present at session start), untouched.

### 5.3 `git diff --stat` (repo-wide `web_demo/`, spans everything since the last commit — no
commit boundary exists between the original Step 8 build and this fix round to diff "this round
alone" against)

```
 web_demo/BUILD_PROGRESS.md                       | 537 ++++++++++++++++++-----
 web_demo/SZSCAN_SPEC_v5.md                       |   5 +-
 web_demo/backend/db.py                           |  17 +
 web_demo/backend/export_txt.py                   | 142 +++++-
 web_demo/backend/main.py                         |  27 ++
 web_demo/frontend/src/api.js                     |  24 +
 web_demo/frontend/src/screens/AnalysisScreen.jsx |  13 +-
 7 files changed, 660 insertions(+), 105 deletions(-)
```

This round's own edits, isolated: `AnalysisScreen.jsx`'s diff (§2.2 above, +5/−1 net for the
className hunk) and all of `BUILD_PROGRESS.md`'s changes (§4 above). Everything else in this stat is
Step 8's original build + fix round 1, previously reported, unchanged this round.

---

**Stopping here per the prompt. No `git add`/`commit`/`push` was run.**
