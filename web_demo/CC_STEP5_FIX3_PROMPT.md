# CC_STEP5_FIX3_PROMPT.md — Step 5 fix round 3

Two real problems Boti found by using the app live. Round 2's "Play already works" finding was too
narrow — retest more carefully this time, with the specific evidence asked for below, not a repeat of
the same check.

## 0 · Read the updated spec first

`SZSCAN_SPEC_v5.md`, `SZSCAN_DESIGN_v2.md`, and `DEMO_BUILD_HANDOFF.md` were just replaced with English
translations (content-identical to the Vietnamese versions you worked from before, plus one real change:
`SZSCAN_SPEC_v5.md §6.4`'s amplitude-token list, C18). Re-read `SZSCAN_SPEC_v5.md §6.4` before starting
item 2 below.

## 1 · Playback doesn't advance past the current window

The Play button does something (round 2 confirmed this), but the displayed EEG window stays fixed at
whatever time range was showing when Play was clicked — playback does not scroll the view forward once
the playhead reaches the edge of that range. This is different from "Play does nothing": the playhead
may move within the static frame, but the visible window never advances, so playback is not actually
usable for reviewing the recording.

Fix so that during playback, once the playhead approaches/reaches the right edge of the currently
displayed window, the window itself advances (shifts forward and fetches the next segment, per
`DEMO_BUILD_HANDOFF.md §5`'s decimated-window-fetch architecture) so playback continues showing
subsequent time rather than freezing at the boundary.

**Verify with evidence that would have caught round 2's miss:** take three screenshots — at the moment
Play is clicked, ~10 seconds of playback later, and ~20 seconds later — and confirm the visible time-axis
labels below Panel EEG actually change between them (not just that the playhead line moved within one
static frame). Include all three screenshots in the report.

## 2 · Implement the new amplitude-token range, then re-check legibility

`SZSCAN_SPEC_v5.md §6.4` now specifies the amplitude dropdown as
**5/7/10/15/20/30/50/75/100/150/250/500 µV** (extended from the old 5/7/10/15/20/30 max-30 list, per the
real signal-amplitude data your own round-2 report gathered). Update the actual frontend dropdown to
match this exactly.

Then, on the same window used for round 2's measurement (`chb13_03.edf`), take screenshots at **100 µV**
and **250 µV** and compare against the current 5 µV screenshot Boti has (near-solid black/white
clipping). If the waveform becomes a legible, connected undulating line at one of these higher settings,
that confirms round 2's scale-mismatch diagnosis was correct and this is resolved. If it is *still*
dense/near-solid at 250 µV, do not attribute that to scale again — treat it as a genuine rendering-logic
defect (e.g. a broken point-to-line connection or decimation bug) and investigate separately.

## Report

Write to `web_demo/CC_STEP5_FIX3_REPORT.md`, with all screenshots described in items 1 and 2. Run
`pytest web_demo/backend/tests/test_guards.py -v` and `git status` again at the end, raw output included.

## Stop condition

Stop once both items are resolved or clearly diagnosed with evidence, and the report is written. Do not
start Step 6.
