# CC_STEP5_FIX7_PROMPT.md — Step 5 fix round 7

Three items. Two are investigate-and-diagnose (don't assume the cause), one is a real gap to fix.

## 1 · Solid black vertical bar in Panel EEG on `chb15_01_short.edf`

Boti saw a full-height, solid-black vertical stripe cutting across all 18 channels around 18:26–18:27
on this file — visibly different from normal waveform texture on either side of it.

This file is a known synthetic test artifact from Step 3 (`BUILD_PROGRESS.md §1`/`§6.2 round 5`):
built by concatenating short real `chb15` clips, not a genuine full-length upload. Before assuming
that explains it, verify:

- Read the raw/filtered `.npy` arrays directly at the exact sample range under that visual position.
  Is there a NaN, a zero-run, an extreme-value spike, or a genuine discontinuity in the underlying
  data there (consistent with a seam between two concatenated source clips)? Or does the data look
  normal and the black bar is purely a rendering artifact (e.g. a decimation bug drawing a filled
  block instead of an envelope for that bucket)?
- Check whether the same thing happens anywhere in `chb13_02.edf`, `chb13_03.edf`, or `chb06_01.edf`
  (the genuinely real files) — a quick scan for any bucket with an anomalously large `max_uv - min_uv`
  spread relative to its neighbors, or any NaN, across each file's full duration.
- State plainly: is this specific to the known-synthetic `chb15_01_short.edf` construction, or could it
  happen on a real upload too? If it's a genuine gap-handling gap in the rendering/decimation code
  (not just bad test data), that needs fixing regardless of which file exposed it.

## 2 · Play doesn't work on `chb15_01_short.edf`

Test in this order so the two items can be told apart:

- First, re-confirm Play still works correctly on `chb13_03.edf` (round 3's original test file) — same
  three-screenshot time-axis-advancing check as round 3 used. If it's broken there too, this round
  introduced a regression, separate from item 1.
- Then reproduce the failure on `chb15_01_short.edf` specifically and investigate the root cause. Check
  whether it's related to item 1's data issue (e.g. a `NaN`/`Infinity` in the tick-advance calculation
  when the playhead's fetch window includes the problem region, or an edge case from this file's short
  total duration interacting with the end-of-file/`usable_duration_seconds` logic).
- Fix if it's a real bug in the general playback logic. If it's specific to this one known-synthetic
  test file's malformed data and does not reproduce on the real files, say so plainly and don't force a
  fix onto data that won't exist in the real demo.

## 3 · Sync the bottom scrub bar's position to the file-wide timeline

The bottom scrub bar (with the play/pause button and speed dropdown) represents the file's **entire**
duration, but its handle position currently does not reliably reflect where the currently-displayed
EEG window actually sits within that full duration — it should. This needs to hold in both directions:

- When the displayed window changes for **any** reason — manual drag-to-seek (already wired per round
  2), Play auto-advancing the window (round 3), or clicking an Event Panel row jumping to an
  onset/offset (Step 5's original 3-panel sync) — the scrub bar's handle must move to
  `(window_start_sec / file_duration_sec)` along the bar, not stay wherever it was.
- Dragging the scrub bar handle must continue to move the EEG window (already working per round 2) —
  don't break that while fixing the position-reflection direction.

Verify with evidence, not a visual glance: at 2–3 known window positions (e.g. window start = 0%, ~40%,
~90% of the file), read the scrub handle's actual rendered position (CSS `left`/slider `value`, not a
screenshot guess) and confirm it matches the expected fraction of `file_duration_sec` within a small
tolerance. Test at least one case reached via clicking an Event Panel row, not just manual dragging or
Play.

## Report

Write to `web_demo/CC_STEP5_FIX7_REPORT.md`. Run `pytest web_demo/backend/tests/test_guards.py -v` and
`git status` again at the end, raw output included.

## Stop condition

Stop once all three items are diagnosed/fixed with evidence and the report is written. Do not start the
next build step (Select Range, `DEMO_BUILD_HANDOFF.md §6` row 6).
