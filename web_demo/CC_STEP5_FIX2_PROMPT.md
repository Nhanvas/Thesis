# CC_STEP5_FIX2_PROMPT.md — Step 5 fix round 2

`CC_STEP5_FIX_REPORT.md` exists from round 1, but Boti found more real problems by using the app live,
plus one thing that needs verifying with data (not assumed) and one thing that must NOT be changed.
Read `CC_STEP5_FIX_REPORT.md` first so you know what round 1 already claims to have fixed, then handle
the following.

## 1 · Real bugs to fix

1. **Dragging the bottom scrub bar does not move Panel EEG's displayed position.** Only clicking an
   event row moves the view. Check whether drag-to-seek on the scrub control was ever wired to update
   the displayed time range, independent of event clicks. Fix it so dragging the scrub bar seeks Panel
   EEG (and the mini-timeline playhead follows, per the existing one-way sync).
2. **The play button (▶) does nothing.** Per `SZSCAN_SPEC_v5.md §6.4`, the scrub bar has a speed
   dropdown (1x/2x/4x/8x) — clicking play should auto-advance the playhead through the file at the
   selected speed. Confirm whether this was ever implemented, and implement/fix it.
3. **EEG waveform still looks dense/busy after round 1's clip fix.** Round 1's own report already
   diagnosed why: `chb13`'s real per-channel envelope spread (120–155 µV typical, peaks to ±1000 µV)
   exceeds every available amplitude token (max 30 µV), so a channel can stay visually busy even with
   the cross-channel bleed fixed. Round 1's pixel-sampled evidence for the clip fix itself looks solid,
   so treat this as a **scale mismatch, not a rendering bug**, unless you find concrete evidence
   otherwise. Do NOT write more rendering code or add new amplitude tokens yourself — that's a
   design-token decision for Boti, not yours to make. Instead, gather the data he needs to decide: for
   3 of the 8 allowlisted subjects, report the typical (median) and peak per-channel envelope spread
   across a handful of representative windows, so he can see how far the real range sits above
   `SZSCAN_DESIGN_v2.md`'s current 5/7/10/15/20/30 µV list. If, separately, you spot an actual
   rendering-logic defect unrelated to scale (e.g. a broken point-to-line connection independent of
   amplitude), fix that and say so explicitly — but don't let that search turn into more scale-clipping
   analysis re-litigated as a "bug."
4. **The inline validation error ("review_status must be one of Accept/Reject/Uncertain.") shown when
   Save is clicked with no status selected stays on screen indefinitely** — it doesn't clear when a
   status is subsequently selected, when the user switches to a different event, or after a successful
   save. Fix so it clears on any of those, whichever is the more natural behavior given the rest of the
   Panel Event component's state handling.

## 2 · Verify with data, don't assume

5. **Alert count.** The header showed `02 alerts to check` for `chb13_03.edf` while the Event panel
   lists 4 AI events. Per `SZSCAN_SPEC_v5.md §5.3`, Alert = (AI events NOT yet Rejected) + user-added
   events — it is not a count of events shown. Print the actual `review_status` of all 4 stored events
   for this file right now, show the arithmetic, and state plainly whether `02` is correct given that
   data or whether the Alert computation itself has a bug. Do not silently "fix" anything here without
   first showing the numbers.

## 3 · Do NOT change this

6. **The diagonal hatch on Reject-status blocks is spec-mandated, not a bug.**
   `SZSCAN_DESIGN_v2.md §2` explicitly requires it: *"Reject = red opacity ~55% + gạch chéo nhẹ (để
   không chỉ dựa vào màu)"* — solid fill is only for AI-unreviewed (charcoal) and Human (blue) blocks.
   Leave this exactly as it is. If your round 1 report claimed this was a bug or changed it, say so and
   revert.

## Report

Write to `web_demo/CC_STEP5_FIX2_REPORT.md`. Run `pytest web_demo/backend/tests/test_guards.py -v` and
`git status` again at the end, raw output included.

## Stop condition

Stop once items 1–6 are resolved/verified with evidence and the report is written. Do not start Step 6.
