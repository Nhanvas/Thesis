# CC_STEP3_FIX6_REPORT.md — Step 3 closeout: logout dropdown hidden/unclickable

## Root cause

Confirmed live in the browser (not by reading CSS): this is a **pre-existing bug, unrelated to
`CreateNewPanel`**. It reproduces on a completely fresh page load, before Create New has ever been
opened.

`Header.jsx`'s avatar dropdown (`<div className="absolute right-0 mt-2 w-56 ...">`) had no explicit
`z-index` — it is `position: absolute` with `z-index: auto`. `DatabaseScreen.jsx`'s `<main className="p-6
relative">` and its child `<div className="relative border ...">` (added in round 1, to host
`CreateNewPanel`'s absolute overlay) are also positioned with `z-index: auto`.

Per CSS stacking rules, positioned elements with `z-index: auto` paint in **DOM order** within their
containing stacking context. `<Header>` renders before `<main>` in the JSX tree, so `main`'s positioned
subtree — despite being visually below the header on screen — paints *after*, and therefore *on top of*,
the header's dropdown wherever the two overlap on screen (the dropdown extends a few dozen pixels below
the header into the top of `main`'s content area). Before round 1, `main` wasn't positioned at all, so it
fell into a lower paint layer than the header's positioned dropdown and never covered it — that's why this
only became visible after round 1's layout change, even though the actual defect is in `Header.jsx`, not
in `CreateNewPanel.jsx` or the round-1 diff itself.

## Isolation tests (both done live via `claude-in-chrome`)

1. **Fresh load, Create New never opened**: clicked the avatar. Confirmed via
   `document.elementFromPoint()` at the "Log out" button's own coordinates that the topmost element there
   was `<div class="p-5 pb-4">` (the search box container inside `main`), not the Log out button —
   `isLogoutOnTop: false`. The button existed in the DOM, correctly positioned, just visually covered.
   **Fails identically to the reported bug, before `CreateNewPanel` is ever mounted.**
2. **After opening and closing Create New**: same failure, confirmed by direct comparison — behavior is
   identical to test 1.

Both tests showing the same broken behavior confirms this is a `Header.jsx` bug on its own terms, not a
Step 3 panel regression (worth checking the z-index relative to `main`'s new stacking context was still
the right first guess — it was — but the fix belongs in `Header.jsx`, not in undoing round 1's layout).

## Fix

One line, `web_demo/frontend/src/components/Header.jsx`:

```diff
-          <div className="absolute right-0 mt-2 w-56 bg-surface rounded-panel shadow-panel overflow-hidden border border-border">
+          <div className="absolute right-0 mt-2 w-56 z-50 bg-surface rounded-panel shadow-panel overflow-hidden border border-border">
```

Giving the dropdown an explicit positive `z-index` moves it into CSS's "positive z-index" paint layer,
which always renders above the "z-index:auto/0" layer regardless of DOM order — so it no longer depends on
`main` staying unpositioned. `z-50` also clears `CreateNewPanel`'s `z-30` overlay with headroom.

## Verification (all live, via `claude-in-chrome`)

1. **Both isolation tests re-run post-fix**: dropdown renders on top, "Log out" is visible and clickable,
   in both the fresh-load case and the after-Create-New case.
2. **Full logout cycle, end-to-end**: logged in as `AdminSzScan` → Database screen → avatar → Log out →
   landed back on the Login screen. Confirmed twice (once per isolation-test pass).
3. **Regression check — Create New overlay**: reopened Create New; the table underneath keeps its full
   width/column layout, unshifted, with the panel sitting on top as an absolute overlay — round 1's fix is
   intact.
4. **Guards + git status**:

```
$ python -m pytest web_demo/backend/tests/test_guards.py -v
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
collected 4 items

web_demo/backend/tests/test_guards.py::test_guard_no_build_timeline_masked PASSED [ 25%]
web_demo/backend/tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED [ 50%]
web_demo/backend/tests/test_guards.py::test_guard_no_labeled_npy PASSED  [ 75%]
web_demo/backend/tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED [100%]

============================== 4 passed in 2.22s ==============================

$ git status
On branch main
Your branch is ahead of 'origin/main' by 7 commits.

Changes not staged for commit:
	modified:   docs/EXHIBIT_SET_FINAL.md
	modified:   docs/PROJECT_STATUS.md
	modified:   docs/RUBRIC_TRACKING.md
	modified:   docs/VERIFIED_NUMBERS.md
	modified:   web_demo/frontend/src/components/Header.jsx

Untracked files:
	web_demo/CC_STEP3_FIX6_PROMPT.md

no changes added to commit (use "git add" and/or "git commit -a")
```

The four `docs/*.md` modifications predate this round (present in git status before I started; this
round never touches `docs/`, per the write guard). The only source change this round is `Header.jsx`.

5. **DB check — round-5 test subjects**: queried `szscan.db` directly (read-only, no writes made this
   round). Present: `chb06`, `chb13`, `chb15`, `chb14`, `chb16`. **`chb03` is not present** — it was
   already absent when this round started (I never touched the DB). Round 5's own report
   (`CC_STEP3_FIX5_REPORT.md`) recorded `chb03` as deliberately left in the DB at that round's close, and
   also told the author "Delete any of these via the Database screen's own Delete button if you don't
   want them kept" — so the likeliest explanation is the author deleted it between rounds. Flagging this
   as an observation rather than treating it as this round's problem, since this round's task and stop
   condition don't mention `chb03` and I made no DB writes.

## Stop condition

Per the prompt: not proceeding to Step 4. The logout dropdown is reliably clickable and the full
login → Database → avatar → Log out → Login cycle is verified end-to-end in a real browser, in both
isolation scenarios.
