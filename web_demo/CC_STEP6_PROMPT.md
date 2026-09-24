# CC_STEP6_PROMPT.md — Step 6: Select Range (manual event creation)

**Prerequisite:** Step 5 is fully closed (`web_demo/CC_STEP5_REPORT.md` + all 7
`CC_STEP5_FIX*_REPORT.md` files, `BUILD_PROGRESS.md §8` has the full account). Confirm
`pytest web_demo/backend/tests/test_guards.py -v` is green before doing anything else.

`chb13_03.edf`'s 4 AI events are currently left at Event1=Accept/Event2=Reject/
Event3=Uncertain/Event4=Unseen (Alert=2) — **do not reset this**. It's a useful fixture for this
step: creating a manual event on this file lets you test that it inserts at the correct
chronological position relative to existing AI events, not just into an empty list.

Read in this order before writing any code:
1. `web_demo/SZSCAN_SPEC_v5.md` §6.6 (Select Range) and §6.5 (Event Panel — specifically the
   "expanded User-added event" bullet) — in full. §6.6 is short; read the note at its end about
   the mockup's gray coloring too.
2. `web_demo/SZSCAN_DESIGN_v2.md` §1 ("Blue `#2563EB` is reserved exclusively for... Human-sourced
   events") and §2 (source/status/interaction axes — a Human event only ever carries the source
   axis and the interaction axis; it has no review-status axis, since it self-confirms on
   creation) — in full.
3. View the mockups (copy to scratch first): `UI/B3a*.png`, `UI/B3b*.png`, `UI/B3c*.png`.

**Wording/reading flag from `SZSCAN_SPEC_v5.md §6.6`:** the gray shown in `UI/B3a` is the
**Unseen** label on a nearby AI event, not a dimming effect applied because event-creation mode is
active. Don't build a "dim everything while marking" behavior based on misreading that pixel.

## Scope boundary

**In scope** (`SZSCAN_SPEC_v5.md §6.6` + the relevant part of §6.5):

1. **Enabling marking mode.** The `Select Range` toolbar button (currently present but inert/
   disabled-looking since Step 4) becomes clickable and toggles marking mode on.
2. **Onset click.** Clicking a point on the EEG grid while marking mode is active sets the onset
   and shows a vertical marker line at that point.
3. **Live drag preview.** Moving the mouse right after the onset click stretches a rectangle
   following the cursor in the "Event Time" row, live (`UI/B3a`).
4. **Offset click.** A second click locks in the offset (`UI/B3b`) and ends marking mode for that
   event.
5. **Insert-in-place, not appended.** The new event must be inserted into the Panel Event list at
   its correct chronological position by onset time — verify this explicitly against `chb13_03`'s
   existing 4 AI events, not just on an empty list.
6. **Event identity.** Person icon (not AI icon), auto-computed Onset/Offset/Duration from the two
   clicks, no Accept/Reject/Uncertain (per DESIGN's axis rule — a Human event has no review-status
   axis at all, not just a hidden/default one).
7. **Mini-timeline block.** A new block appears on the mini-timeline at the matching position,
   styled with the Human source color (`#2563EB`), visually distinct from an AI block. This should
   mostly fall out of `eventStyle.js`'s existing shared `blockStyle()`/`dimOpacity` helpers from
   Step 5 if the new event object correctly carries `source: "Human"` — verify live, since no real
   Human event has ever existed to exercise this path before.
8. **Alert +1, both places.** The header's `(<N> alerts to check)` and the Database screen's Alert
   column for this subject both increment by 1 immediately (per `SZSCAN_SPEC_v5.md §5.3`'s formula
   — User-added events always count).
9. **Expanding the new event.** Per §6.5: Onset / Offset / Duration + **Delete / Edit** + Comment +
   Save, no Accept/Reject/Uncertain. This is `PanelEvent.jsx`'s `HumanExpand` component, built in
   Step 5 but never live-tested — this is the first real exercise of it. Verify it live, don't just
   confirm it renders from a code read.
10. **Delete.** Removes the event, Alert decrements by 1 in both places, its mini-timeline block
    disappears.
11. **Edit.** `SZSCAN_SPEC_v5.md` doesn't spell out exactly what Edit does; `UI/B3c` may show this
    state directly — check it first. If the mockup doesn't make it unambiguous, the reasonable
    reading is: Edit re-enters Select Range-style marking mode pre-populated with this event's
    existing onset/offset, letting the user redraw them (matching the "AI events can't be edited,
    only Rejected-and-redrawn" asymmetry already established in §6.5 — but User-added events, being
    fully editable, get a direct edit path instead of delete-and-redraw). Make a reasonable choice,
    implement it, and **state plainly in the report which reading you went with and why**, since
    this is filling a real spec gap, not following an explicit instruction.
12. **Cancelling mid-mark.** Not explicitly specified. Check the mockups for a cancel affordance
    (e.g. clicking `Select Range` again while marking is in progress, or an Escape-key handler). If
    none is shown, implement a reasonable one (clicking the toggle button again while only the
    onset is set should cancel cleanly, no partial event created) and say so in the report.
13. **Direction-agnostic drag.** If the user's second click lands before the first (right-to-left
    drag), the resulting event should still have `onset < offset` — auto-sort the two points rather
    than either rejecting the drag or creating a negative-duration event.

**Out of scope, still:** Channel Attribution panel (Step 7), Export (Step 8).

## Standing rules (apply as always)

- No fake data — everything created must be a real row in the `events` table via the real
  create-event flow, not a mocked/hardcoded list item.
- Use `claude-in-chrome` from the start, not reactively. If it's not connected, say so immediately
  and follow the account-pairing / reconnect steps in `learnings.md` before proceeding, rather than
  quietly falling back to a narrower check.
- If a mockup and a written doc disagree on something other than the §6.6 wording note already
  flagged above, stop and say so rather than silently picking one.
- Visual fidelity to the mockups means position **and** color, checked by literal screenshot
  comparison against `UI/B3a-c`, not just "the right elements exist somewhere on the page." This
  has been a recurring theme through Step 5's fix rounds — hold the same bar here from the start.
- Nothing this step should touch anything outside `web_demo/`.

## Verification required before writing your report

1. Click `Select Range`, confirm marking mode visibly activates (button state change, and/or
   cursor/canvas affordance).
2. Click an onset point on `chb13_03.edf`'s EEG grid — confirm the vertical marker appears at
   that exact time.
3. Move the mouse right — confirm the rectangle in the Event Time row stretches live, following
   the cursor, before the second click.
4. Click an offset point — confirm the rectangle locks, marking mode ends.
5. Confirm the new event's Onset/Offset/Duration in the Panel Event list match what was drawn
   (read the actual values, don't eyeball).
6. Pick an onset time that falls **between** two of `chb13_03`'s existing AI events — confirm the
   new row is inserted at the correct chronological position in the list, not appended at the end.
7. Confirm the new row shows a person icon, no Accept/Reject/Uncertain controls.
8. Confirm a new block appears on the mini-timeline at the matching position, in the Human blue
   token, visibly distinct from the AI/review-status colors already on screen.
9. Confirm Alert increments by 1 in the Analysis header immediately, and — after navigating back —
   on the Database screen's row for this subject too.
10. Expand the new event — confirm Onset/Offset/Duration (read-only or editable, per your Edit
    reading), Delete, Edit, Comment field, Save button, and the explicit absence of
    Accept/Reject/Uncertain.
11. Test Delete on a second, disposable test event — confirm removal, Alert −1 in both places, its
    mini-timeline block gone.
12. Test whatever Edit behavior you implemented — confirm it works as described in item 11 of the
    scope section above.
13. Test cancelling mid-mark (per item 12 of the scope section) — confirm no partial/broken event
    is left behind.
14. Test a right-to-left drag (offset clicked before onset) — confirm the resulting event still has
    a sane, positive-duration onset/offset pair.
15. Click the newly created event's row after deselecting it — confirm the 3-panel sync (Panel EEG
    jump, mini-timeline playhead) still works for a Human event exactly as it does for an AI event.
16. `pytest web_demo/backend/tests/test_guards.py -v` and `git status` — raw output.

Write your report to `web_demo/CC_STEP6_REPORT.md`. Note in it exactly what test event(s) were left
in `chb13_03.edf` afterward (onset/offset, and whether deleted or left in place), matching the
test-state-note convention every prior step's report has used.

## Stop condition

Do not start Step 7 (Channel Attribution). Stop once Select Range can create, display, sync,
delete, and (per your Edit reading) edit a manual event correctly, all items above are verified
live with evidence — not code-read confidence — and the report is written.