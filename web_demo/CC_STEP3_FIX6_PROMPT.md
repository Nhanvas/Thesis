# CC_STEP3_FIX6_PROMPT.md — Step 3 closeout: logout dropdown hidden/unclickable

**Context:** This is the last known loose end before Step 3 fully closes. Rounds 1–5 are all confirmed
fixed/verified. Test subjects from round 5 (`chb03`, `chb13`, `chb15`, `chb14`, `chb16`) are intentionally
kept in the DB for Step 4 use — do not delete them this round.

**Bug reported by the author:** on the Database screen, clicking the avatar (top-right, per `UI/A0b`)
opens a dropdown, but it renders **hidden behind something else** — no visible "Log out" button appears
to click, even though the dropdown mechanism itself seems to trigger.

## Investigate before patching

This could be either a pre-existing Step 2 bug (the original Step 2 report only confirmed the dropdown
*visually matched the mockup* — it's not clear it was ever actually clicked and functionally tested) or
a regression from one of Step 3's five rounds of layout/z-index changes (round 1 in particular changed
`main` from a flex container to `position: relative`, and introduced `CreateNewPanel` as an
`absolute`-positioned overlay at `z-30`).

**Isolate which, with two tests, before assuming a cause:**
1. On a completely fresh page load, **never having opened Create New at all this session**, click the
   avatar. Does the dropdown/Log out button appear and work?
2. After opening and closing (or minimizing) Create New at least once, click the avatar again. Does
   behavior change between test 1 and test 2?

If both tests show the same broken behavior, this is unrelated to Step 3's panel work — say so plainly,
and look at `Header.jsx`/whatever renders the avatar dropdown on its own terms (z-index relative to
`main`'s new stacking context is still a reasonable first thing to check, but don't assume the panel
code is the cause without confirming test 1 also fails).

Use `claude-in-chrome` — reproduce it live, don't reason about it purely by reading CSS. Check actual
computed z-index / stacking context of the dropdown element vs whatever it's rendering behind (browser
devtools-equivalent inspection, e.g. `getComputedStyle` + `getBoundingClientRect` on both elements to
confirm which one is actually on top and why).

## Fix

Once you've found the actual cause, fix it so the dropdown reliably renders on top and "Log out" is
clickable, in both scenarios above. Re-verify the full login → Database → avatar → Log out → back to
Login screen cycle actually works end-to-end by clicking through it for real.

## Verification

1. Both isolation tests above, live.
2. Full logout cycle works end-to-end (lands back on Login screen).
3. Quick regression check: Create New panel overlay (round 1's fix) still doesn't push/resize the table.
4. `pytest web_demo/backend/tests/test_guards.py -v` and `git status` — paste raw output.
5. Confirm the round-5 test subjects (`chb03`, `chb13`, `chb15`, `chb14`, `chb16`) are still present and
   untouched — this round should not need to touch the DB at all.

**Write your report to `web_demo/CC_STEP3_FIX6_REPORT.md`.**

## Stop condition

Do not proceed to Step 4. Stop once the logout dropdown is reliably clickable and the full login-out
cycle is verified end-to-end in a real browser.
