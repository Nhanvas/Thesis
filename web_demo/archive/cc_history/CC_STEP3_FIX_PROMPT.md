# CC_STEP3_FIX_PROMPT.md — Step 3 fix round 1: Create New panel closes itself + wrong overlay layout

**Context:** Step 3's initial build (`web_demo/CC_STEP3_REPORT.md`) passed guards and curl-based API
tests, but the author's first live browser test surfaced two real UI bugs that no automated check in
the previous round could have caught. Fix both before Step 3 can close. Do not touch backend logic,
the pipeline, or anything already-verified (Phase A/B, operating-point calibration, guards) unless you
find a genuine reason it's implicated.

Read `web_demo/SZSCAN_SPEC_v5.md` §5.5 again before touching any code. Copy `web_demo/UI/A1a*.png` to
scratch to compare against (never open `web_demo/UI/` directly, never write to it).

---

## Bug 1 — Create New panel closes itself after a few seconds / on scroll

**Reproduced by the author:** open "Create new" → panel appears correctly → type into Project ID
and/or Memo → scroll the page (or just wait) → the panel disappears entirely, with no × click.

**Required behavior (SPEC §5.5):** the panel stays open indefinitely until the user explicitly clicks
**×** (discard the draft — already agreed: no confirmation needed for this) or **−** (minimize to
toast). Nothing else may close it — not a timer, not a scroll event, not an unrelated re-render.

Find the actual root cause before patching. Do not guess-and-patch blindly. Likely areas to check
first (not prescriptive — verify, don't assume):
- Any `useEffect` whose cleanup or a `setTimeout`/`setInterval` inside it could be firing unintentionally.
- Any scroll listener (on `window` or a parent container) wired to a "click outside to close" handler
  that a scroll event is incorrectly satisfying.
- Whether the panel's mount/visibility condition depends on anything viewport-derived (an
  `IntersectionObserver`, a sticky-position recalculation, a resize observer) that a scroll could
  perturb.
- Whether the ~1.5 s polling added in the original Step 3 build (`GET /api/uploads/current`, the Phase
  B trigger safety net) is somehow also driving panel-visibility state, not just backend trigger logic
  — a bad response or a race there could plausibly cause an unrelated unmount.

## Bug 2 — Panel pushes/resizes the Database table instead of overlaying it

**Required behavior (SPEC §5.5, `UI/A1a`):** the Create New panel is an **overlay** — it floats on top
of the existing Database view from the right edge, highest z-index. The Database table underneath
keeps its own full layout; it must not be squeezed into a narrower flex/grid column to make room for
the panel.

**Current behavior:** the panel and the table appear to share a flex/grid row, each taking a fraction
of the viewport width — the table's own width visibly changes when the panel opens. Compare directly
against `UI/A1a` (pixel-crop, not eyeballing): the panel there sits as a bounded card, but the important
part is that it's an overlay, not a shared-width layout partner. Fix the CSS/positioning so opening or
closing the panel never changes the Database table's own width or column layout.

---

## Verification required before writing your report — do all of these yourself, don't just claim them

1. Open Create New, type into both fields, **scroll the page and wait at least 15 seconds**. Panel must
   still be open, untouched, with the typed values intact.
2. Upload one real EDF (e.g. `chb06_01.edf`) and **visually confirm** — not just check the API response
   — that the spinner-to-✕ status icon transition actually renders and stays visible long enough for a
   human to see it change.
3. Re-run `pytest web_demo/backend/tests/test_guards.py -v` — expect no change (this should be a
   frontend-only fix); confirm anyway and paste the raw result.
4. Run `git status` — confirm changes are confined to `web_demo/frontend/...` unless you find a genuine
   reason the backend needs touching, in which case explain why in your report.
5. Pixel-compare the panel's overlay behavior against `UI/A1a` directly and state plainly in your report
   whether it now matches.

**Write your report to `web_demo/CC_STEP3_FIX_REPORT.md`** (not the terminal). Cover: the actual root
cause you found for Bug 1 (not just "added a fix"), what changed for Bug 2, and the five verification
results above.

## Stop condition

Do not proceed to Step 4. Stop once both bugs are fixed and every verification step above passes.
