# CC_STEP5_FIX5_PROMPT.md — Step 5 fix round 5

Two things need investigating, both touching the same code round 3 changed. Don't assume either is
fixed or broken — verify with evidence.

## 1 · The `⊲▷ [X] hr` window-length control appears to do nothing

Boti selected `24 hr` from the window-length popover, but Panel EEG kept showing only a 1-hour range.
Round 1's report claimed this control was already confirmed working (masked earlier by the
near-black-canvas bug, per that round's own account) — but round 3 rewrote the same window-fetch
`useEffect` in `AnalysisScreen.jsx` (the `fileMetaRef` mirror + window-shifting logic added for the
playback-advance fix). Check via `git log -p` / `git blame` on that effect whether round 3's change
altered how the window-length selection is applied, or introduced a state-update ordering issue where
selecting a new length gets silently overridden by something else (e.g. the playback effect
re-asserting `windowStartSec`/window size, or a stale `fileMetaRef` read).

Reproduce live: open a file, select `24 hr` from the popover, confirm whether Panel EEG's displayed
range and the x-axis time labels actually change. Then try a few other values (`4 hr`, `1 hr`, `1 min`)
to see if only the extreme end is broken or if the control is non-functional across the board. Fix
whatever is actually wrong, and say plainly whether this was a round-3 regression or a pre-existing gap
round 1 never actually tested at the 24 hr extreme.

## 2 · Re-verify the filter-toggle pixel-difference claim — the coarse fingerprint may have missed a real difference

Round 4 concluded `(b)`/`(c)`/`(d)` (different combinations of `lff`/`hff`/`60` all on) are
"pixel-for-pixel identical," using a fingerprint that sums only every 97th byte of the canvas buffer.
Boti toggled the buttons live himself and reports a real, small, visible difference in the waveform
shape between states — which a sparse 1-in-97-byte sample could easily miss if the true difference is
small and localized (exactly what a narrow-band 60 Hz notch filter's effect would look like).

Do this properly this time:
- Redo the comparison with a **full** pixel diff (every byte of the canvas buffer, or a proper
  perceptual diff), not a sparse sample, across the same four states: all off, `lff` only, `lff`+`hff`,
  `lff`+`hff`+`60`.
- **Hold the time window and playhead completely fixed** while doing this — pause playback, do not let
  any auto-advance happen between screenshots, since round 3 added window-auto-scroll logic this round
  and a shifted window would itself produce a pixel difference unrelated to the filter.
- Separately, compare the underlying `filtered_uv` byte arrays returned by the backend for the *same*
  time window under different filter-toggle combinations, if the frontend requests are actually
  filter-combination-aware. If the backend only ever returns one combined `filtered_uv` regardless of
  which of the three buttons are on (as round 4's report claims), state that explicitly with the request
  payloads shown. If instead different combinations do return different data, round 4's architectural
  claim was wrong — say so and correct the record.
- Report definitively: is there a real difference between `hff`/`60` toggle states, or was what Boti saw
  an artifact of the window/playhead shifting between his screenshots?

## Report

Write to `web_demo/CC_STEP5_FIX5_REPORT.md`. Run `pytest web_demo/backend/tests/test_guards.py -v` and
`git status` again at the end, raw output included.

## Stop condition

Stop once both items are resolved or definitively diagnosed with evidence, and the report is written.
Do not start Step 6, and do not change `AMPLITUDE_OPTIONS` — that list is still Boti's decision, pending
his reply on the recommended range.
