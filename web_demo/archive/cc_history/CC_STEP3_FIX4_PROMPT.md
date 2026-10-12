# CC_STEP3_FIX4_PROMPT.md — Step 3 fix round 4: minimize/restore bug + 2 author decisions + font check

**Context:** Rounds 1–3 (panel auto-close, overlay layout, PROCESS gating, editable Project ID/Memo) are
all confirmed fixed and verified live. Do not re-touch that work unless this round's fixes genuinely
require it — explain why if so.

This round has one confirmed bug and two explicit author decisions (both reversing or refining prior
guidance — treat them as authoritative, not open questions).

---

## Bug — minimize then restore reverts edited Project ID / Memo

**Reproduced by the author:** typed a corrected Project ID (`chb06test`) into an already-hydrated
session, clicked "−" to minimize, clicked the resulting toast to reopen — the field showed the
*original* session value (`chb06`), not the edit. This is exactly the risk flagged before round 3
shipped: `CreateNewPanel.jsx`'s `hydratedRef`-guarded seed effect runs again on every remount, and
minimizing/restoring currently unmounts/remounts the panel, so the one-time seed fires again and
clobbers whatever the user typed.

**Fix — do not seed from the session snapshot on every mount.** The cleanest approach: stop unmounting
`CreateNewPanel` when minimized. Keep it mounted the whole time the draft/session is alive; minimize
should only toggle a CSS/conditional-render *visibility* state (e.g. `display: none` or a parent
`hidden` class), not remove the component from the tree. That way React state (`projectId`, `memo`)
survives minimize/restore naturally with no re-hydration logic needed at all, and `hydratedRef` only
ever needs to fire once — on true first mount (fresh page load / session restored from a server
reload) — which is its original intended purpose.

If keeping it mounted turns out to be impractical for a reason you find in the code, explain why and
propose the next-best fix (e.g. lifting `projectId`/`memo` state up to `DatabaseScreen` so it survives
`CreateNewPanel` unmounting) — don't silently patch around the symptom.

Verify: type an edit, minimize, restore — value must be exactly what was typed, not the session's
original value. Test both with and without files already uploaded.

---

## Decision 1 — add a confirmation dialog to × (discard draft)

**This reverses the earlier decision ("no confirmation needed for ×").** The author now wants a
confirmation before discarding a draft with the × button, in the same visual style as the existing
delete-subject confirmation (`ConfirmDialog.jsx`, "Are you sure you want to delete this process?").

- Reuse the existing `ConfirmDialog.jsx` component rather than building a new one.
- Wording should fit the discard-draft context specifically (this isn't deleting a processed subject,
  it's abandoning an in-progress draft — nothing has been saved to the Database yet), not a verbatim
  copy of the delete-subject text. Write something reasonable in the same tone; state your exact
  wording choice in the report.
- **Only show the confirmation if there's actually something to lose** — i.e. Project ID or Memo is
  non-empty, or at least one file has been added/uploaded. If the panel is completely untouched (blank
  Project ID, blank Memo, no files), × should still close immediately with no dialog — there's nothing
  to confirm. If you find a reason this conditional reading is wrong, say so in your report and default
  to always confirming instead.
- Clicking "Yes"/confirm on this dialog behaves exactly as × did before this round (discards the draft,
  cleans up any uploaded files/session server-side). Clicking "No"/cancel returns to the panel with
  everything intact.

## Decision 2 — remove the progress bar entirely from Process/Upload states

**The author wants the progress bar element removed**, not made real. Per
`SZSCAN_DESIGN_v2.md §8` ("không hiện % giả" — no fake percentage), a bar that fills without a real,
trustworthy progress signal behind it misrepresents the pipeline, so the resolution is to remove the
bar rather than animate it.

- Remove the progress bar from **both** states that currently show one: the in-progress "Processing
  subject — combining files and detecting change points..." spinner screen, and the "Upload Complete!"
  completion screen. Keep the spinner + text for the in-progress state, and the checkmark + text +
  "Done" button for the completion state — just drop the bar element from both.
- While you're in this component, pixel-compare both states against `UI/A2a`/`A2b*.png` directly (copy
  to scratch first) and note in your report whether the mockups themselves show a progress bar at all —
  if they don't, this brings the build closer to the mockup as a side effect; if they do, note the
  discrepancy for the author's awareness but still remove it per this explicit instruction.

## Also check — font mismatch on Processing/Upload Complete panel

The author flagged that the text on this panel doesn't look like the rest of the app's typography.
Compare directly against `UI/A2a`/`A2b*.png`: confirm `font-family: Inter` (the bundled local font, not
a browser default/serif fallback) is actually applied to every text element in this specific panel
component. If it's inheriting from a parent that isn't setting `font-ui`/`Inter` correctly, or the
component has its own conflicting font rule, fix it. State what you found either way.

---

## Verification required — use `claude-in-chrome`, click through for real

1. Edit Project ID after files are uploaded, minimize, restore via the toast — value must be preserved
   exactly as typed. Repeat once with no files yet added (still mid-typing) to confirm that path too.
2. Trigger × with a non-empty Project ID or an uploaded file present — confirmation dialog appears with
   the wording you chose; "No" returns to the intact panel; "Yes" discards and returns to the Database
   screen cleanly (no orphaned session/files).
3. Trigger × with a completely blank, untouched panel — confirm it still closes immediately, no dialog.
4. Run a real upload → Process cycle and confirm no progress bar renders in either the "Processing
   subject..." state or the "Upload Complete!" state — only spinner+text, then checkmark+text+Done.
5. Screenshot the Processing/Upload-Complete states and state whether the font now matches `UI/A2a/A2b`.
6. Quick regression check: rounds 1–3 (no auto-close, overlay layout, PROCESS gates on upload only,
   Project ID/Memo editable pre-minimize) still hold.
7. `pytest web_demo/backend/tests/test_guards.py -v` and `git status` — paste raw output.

**Write your report to `web_demo/CC_STEP3_FIX4_REPORT.md`.**

## Stop condition

Do not proceed to Step 4. Stop once all four items above are fixed and every verification step passes.
