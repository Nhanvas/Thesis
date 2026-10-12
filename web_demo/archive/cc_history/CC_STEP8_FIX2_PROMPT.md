# CC_STEP8_FIX2_PROMPT.md — Step 8 fix round 2

Read first: `web_demo/CC_STEP8_REPORT.md`, `web_demo/CC_STEP8_FIX_REPORT.md` (both prior reports for
this step), `web_demo/SZSCAN_SPEC_v5.md` §6.1 (Export button rule). Guards unchanged: `test_guards.py`
must stay 4/4 green at the end, no write outside `web_demo/`, no `git add`/`commit`/`push`.

Two items found by Boti testing the running app live, plus a documentation update.

---

## 1 · Export button doesn't visually switch to "enabled" consistently

`CC_STEP8_REPORT.md §5.2` already flagged this as an *observation*, not a fix, at the time: the
Export button's CSS (`bg-white/70 text-text-muted` with `disabled:opacity-50`) makes the enabled and
disabled states look nearly identical. Boti has now compared two live screenshots directly and
confirmed it's a real, visible problem, not just a JPEG-compression artifact:

- `chb13_03.edf`, Progress `02/2` (both files genuinely `Viewed`) — Export button still renders
  muted/faded, visually indistinguishable from the disabled state.
- `chb06_06.edf`, Progress `18/18` (genuinely fully `Viewed`) — Export button renders solid/opaque,
  matching the `Previous`/`Next`/`Viewed` buttons next to it, as it should.

Both cases are genuinely enabled (functionally — exporting already works on `chb13`, per the original
Step 8 verification), but they render differently. Investigate before fixing:

1. Open `chb13_03.edf`'s Analysis screen (progress 2/2). Read the Export button's actual **computed**
   CSS (background-color, opacity, color — not just its class list) via the DOM, not by eye.
2. Open `chb06_06.edf`'s Analysis screen (18/18). Read the same computed properties.
3. Compare directly and report the exact difference found. If there genuinely is none at the computed-
   style level (i.e. the visual impression was misleading), say so plainly rather than forcing a change.
4. If a real difference is found, fix it so the **enabled** state always renders with the same
   solid/opaque styling as the adjacent `Previous`/`Next`/`Viewed` buttons (matching `UI/`'s own
   mockups for an active button), on every subject, consistently — while the **disabled** state keeps
   its current muted/grey look, unchanged. Only touch the resting-state styling; don't change the
   button's click behavior, its enablement logic, or any other button.
5. Verify live on at least 2 different subjects/files at full progress (e.g. `chb13` 2/2 and `chb06`
   18/18 again after the fix), screenshot both, and confirm — visually and via computed style — that
   both now render identically to the sibling buttons.

## 2 · Re-confirm the `.6f` score-format fix is actually live

Boti's own export test this session (`chb13-summary.txt`) shows `8  FZ-CZ  1.27291` in Event 4's
Channel Attribution table — 5 digits after the decimal point, the **un-fixed** format originally
flagged in `CC_STEP8_REPORT.md`, not the `.6f`-fixed `1.272910` that `CC_STEP8_FIX_REPORT.md §3`
already confirmed working in a regenerated export during the previous round. Before assuming a
regression:

1. Confirm `export_txt.py`'s `_attribution_rows` still has the `f"{row['score']:.6f}"` formatting on
   disk (it should, per the prior round's diff) — quote the exact line.
2. Confirm the currently-running backend process was actually started/reloaded **after** that edit was
   saved (a stale, un-reloaded `uvicorn` process still serving pre-edit bytecode would fully explain
   this without any code being wrong).
3. Trigger a **fresh** Export click through the running app (any `Viewed` subject) and open the newly
   downloaded file. Confirm every score in every Channel Attribution table has exactly 6 digits after
   the decimal point.
4. If the fresh export is correctly formatted: state plainly that Boti's uploaded file was simply an
   old cached download from before the fix, not a regression — no code change needed for this item.
   If the fresh export is **still** not `.6f`-formatted: that's a real regression — find the actual
   cause (edit not saved, wrong file/function edited, server genuinely serving stale code some other
   way) and fix it, then re-verify with another fresh export.

## 3 · Update `BUILD_PROGRESS.md`

Add a proper "Step 8 — detail" section, in the same style and level of detail as the existing §7–§10
step-detail sections (scope, what was built, both fix rounds including this one, what's verified live
vs. what's still open), sourced from `CC_STEP8_REPORT.md`, `CC_STEP8_FIX_REPORT.md`, and this round's
own new report. Insert it in the correct place (after the Step 7 section, before "Integrity incident"),
renumbering the sections that follow exactly as earlier steps' additions have done. Update:

- The Status table: row 8 (`Export .txt`) → **DONE**, with a short note (initial build + 2 fix rounds).
- The "Where to resume" line at the top → point at Step 9.
- §13 ("Open items"): check off or update anything this step's two fix rounds resolved (the score-
  format false alarm if that's what it turns out to be, the Export-button styling item once fixed) —
  don't touch items unrelated to Step 8.

---

## Report

Write `web_demo/CC_STEP8_FIX2_REPORT.md`: 1 summary; 2 the exact computed-style difference found for
item 1 (or confirmation none existed), plus the fix and the 2-subject live re-verification; 3 item 2's
root-cause finding (stale server vs. genuine regression) and the fresh-export confirmation; 4 the exact
section added to `BUILD_PROGRESS.md` and which sections were renumbered; 5 raw `pytest -v`, `git
status`, `git diff --stat`. Then **stop. Do not run `git add`/`commit`/`push`.**
