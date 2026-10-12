# CC_STEP6_FIX2_PROMPT.md — Step 6, fix round 2: header title placement + stray file cleanup

**Context:** Fix round 1 was reviewed and accepted by Boti (header sizing, button-group placement, solid
event blocks, Uncertain `#FFE262` all confirmed OK live). This round is two small items. Do **not**
touch Select Range behaviour, event blocks, colours, or the Progress bar.

**Prerequisite:** `pytest web_demo/backend/tests/test_guards.py -v` green before you start.

**Do not run any `git add` / `git commit` / `git push`.** Do not touch anything outside `web_demo/`.
Do not change the stored review states or test events of `chb13_03.edf`.

Use `claude-in-chrome` from the start. If it is not connected, say so immediately and stop.

## Read first

1. `UI/B1a*.png`, `UI/B2a*.png` — copy to a scratch location **outside `web_demo/UI/`** before viewing.
2. `web_demo/SZSCAN_SPEC_v5.md` §6.1 (Analysis header).
3. `frontend/src/components/Header.jsx` and the Analysis header markup in
   `frontend/src/screens/AnalysisScreen.jsx`.

## Item 1 — Move the title next to `Previous`

Currently the title `<ID> (<N> alerts to check)` sits at the left, right after the logo + wordmark, far
from the buttons. In the mockup the title sits **immediately to the left of `Previous`**, forming one
right-hand cluster:

`[logo + SzScan]  ……space……  [title] [« Previous] [Next »] | [Viewed] [Export] [file dropdown] [avatar]`

Do this:
- Logo + wordmark stay at the far left. Flexible space between the logo group and the right cluster.
- The title moves into the right cluster, directly left of `Previous`, with the same gap rhythm the
  mockup uses between title and button.
- Title text, font, size and content stay exactly as they are now (`<ID> (<N> alerts to check)`).
  `N` remains the live Alert of the currently viewed file, synced to the latest review state — do not
  change how it is computed.
- Do not change button behaviour, the divider, the file dropdown, the avatar, or the Progress bar.

**Responsiveness:** check the header at viewport widths **1280 px and 1920 px** (resize the browser
window). At both widths nothing may overlap, wrap onto a second line, or truncate. If the cluster does
not fit at 1280 px, report it with a screenshot and propose the smallest fix — do not restructure the
header on your own.

`Header.jsx` is shared across screens. This item only concerns the **Analysis** header; the Database
header must remain as it is now. Confirm that with a screenshot.

## Item 2 — Stray file in `UI/`

`web_demo/UI/uncertain_pill_zoom.png` (untracked) was created inside the locked mockup folder during fix
round 1. `UI/` must contain only the author's locked mockups.

- `ls` the file first.
- Move it to `web_demo/CC_STEP6_FIX_SCREENSHOTS/` (do not delete it).
- Confirm with `git status --short web_demo/UI` that there is no untracked or modified file left under
  `web_demo/UI/`.
- From now on: any scratch crop or copy of a mockup goes to `/tmp` or a `CC_*_SCREENSHOTS/` folder,
  never into `UI/`.

## Verification (screenshots and measured values, saved to `web_demo/CC_STEP6_FIX2_SCREENSHOTS/`)

1. Before/after screenshot of the Analysis header at 1920 px width, next to the `UI/B1a` / `B2a` header.
2. After screenshot at 1280 px width: no overlap, no wrap, no truncation. Include the measured
   `getBoundingClientRect()` left/right edges of: title, `Previous`, file dropdown, avatar.
3. The `(N alerts to check)` number still equals the file's Alert: create one disposable manual event
   with Select Range, confirm the number goes up by 1, delete it, confirm it returns to the previous value.
4. Database screen header screenshot — unchanged from before this round.
5. `git status --short web_demo/UI` output (must be empty).
6. `pytest web_demo/backend/tests/test_guards.py -v`, `git status`, `git diff --stat` — **raw output**
   pasted into the report. Confirm nothing outside `web_demo/` changed.

## Report

Write `web_demo/CC_STEP6_FIX2_REPORT.md` (a file, not terminal output). Put the human-readable summary
(what changed per file, measured values, any issue found) **first**, and the raw command output last.
Note the test-state of `chb13_03.edf` afterwards.

## Stop condition

Do not start Step 7. Stop once both items are done, verified live with evidence, and the report is written.
