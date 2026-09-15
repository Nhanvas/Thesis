# CC_STEP3_FIX2_PROMPT.md — Step 3 fix round 2: PROCESS button never enables

**Context:** Round 1 (`CC_STEP3_FIX_PROMPT.md`) fixed the panel auto-closing and the overlay-vs-push
layout. Both are confirmed fixed by the author's own live testing (screenshots reviewed: panel stays
open through scroll/wait, editing works, overlay sits correctly on top of the table). Do not re-touch
that ground unless this round's fix genuinely requires it — if it does, explain why.

**New bug found in that same live session:** after uploading exactly one file (`chb06_01.edf`, a valid
allowlisted subject `chb06`) and the file's icon transitioning to `✕` (meaning, per
`SZSCAN_SPEC_v5.md` §5.5, "already uploaded"), the **PROCESS button stays disabled indefinitely** —
screenshot shows it rendered gray/disabled with the file clearly showing `✕`, not the spinner.

## Required behavior — read SPEC §5.5 literally, don't infer a different gate

> "Nút đen Process + 1 dòng ghi chú nhỏ bên dưới. **Disabled cho tới khi mọi file đã tải xong.**"

This says the gate is **upload completion** (every listed file shows `✕`), not "backend Phase A/B
processing complete for every file." The Phase A/B split from the original `CC_STEP3_PROMPT.md` §1 is
an internal computation-ordering decision (needed because z-score/LedoitWolf stats must fit on the
whole subject, per §1.6a) — it was never meant to gate the PROCESS button's enabled state. Clicking
PROCESS is what should trigger (or wait on, if still running) Phase A/B completion, concatenation, and
PELT — shown via the existing full-panel "Processing subject — combining files and detecting change
points..." loading state, not via keeping the button itself disabled.

**Find and fix the actual wiring**, don't blind-patch:
1. Locate whatever frontend state currently gates the PROCESS button's `disabled` prop. Determine
   whether it's incorrectly tied to a Phase A/B completion signal (a poll, a websocket, a backend status
   field) instead of the simple "all files show `✕`" condition.
2. **Check specifically whether this is a regression from round 1's Bug 1 fix** — that fix changed a
   session-polling `useEffect` to gate on `hasSession` instead of `panelMode`. If any part of the
   "file(s) ready to Process" detection depended on that same poll loop running under the old
   `panelMode` condition, re-gating it to `hasSession` may have silently broken it. Confirm or rule this
   out explicitly in your report — don't just say "fixed," show what the actual coupling was (or wasn't).
3. If Phase A/B genuinely isn't finished for a file when its upload transitions to `✕` (i.e. upload and
   Phase A/B completion are visibly two different moments in time), that's fine — the icon only needs to
   represent upload status per the mockup. PROCESS should still enable at that point; if Phase A/B is
   still running in the background when the user clicks PROCESS, the existing full-panel loading state
   is the correct place to wait for it, not the button's disabled state.

## Verification required before writing your report

Use `claude-in-chrome` (already connected) for all of this — actually click through it, don't just
check API responses.

1. Upload exactly one real allowlisted file (`chb06_01.edf` or similar) — confirm PROCESS becomes
   clickable as soon as the icon shows `✕`, without an extra unexplained wait.
2. Upload 2–3 real files for the same subject — confirm PROCESS only enables once **all** of them show
   `✕`, not before.
3. Actually click PROCESS after step 1 or 2 — confirm the full-panel `Processing subject — combining
   files and detecting change points...` state appears, and that it eventually resolves with the
   subject appearing in the Database table with correct columns (this closes the loop on the very
   first end-to-end create→upload→process cycle a human has watched happen in the browser — treat this
   as the real closing verification for Step 3, not a formality).
4. Re-run `pytest web_demo/backend/tests/test_guards.py -v` and `git status` — paste raw output.
5. Confirm Bug 1 and Bug 2 from round 1 still hold (quick re-check only, not a full re-test) — i.e. this
   round's fix didn't reintroduce either.

**Write your report to `web_demo/CC_STEP3_FIX2_REPORT.md`.** State the actual root cause (the specific
line/mechanism that was gating PROCESS incorrectly), whether it was connected to round 1's `hasSession`
change, and the five verification results above.

## Stop condition

Do not proceed to Step 4. Stop once PROCESS reliably enables on upload completion, a full
create→upload→process cycle has been watched succeed in a real browser, and all five verification
steps pass.
