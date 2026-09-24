# CC_STEP5_FIX_PROMPT.md — Step 5 fix round 1

**Status:** `CC_STEP5_REPORT.md` marked Step 5 "done," but that pass verified narrow things (computed
style for color/opacity/playhead position) while `claude-in-chrome` was down for most of it. Boti then
opened the real app and compared it against the mockups directly, and found real problems plus two
loose ends from before. Step 5 is **not closed**. Fix everything below, with visual evidence this time,
before reporting done again.

## Outstanding from before this round

1. `backfill_scores.py` (Phase A+B only — computes and persists the missing per-file continuous
   ensemble score arrays) was run earlier in Step 5 but never written up in `CC_STEP5_REPORT.md`. Add
   to the report, with evidence for each:
   - It never called `cpd_pipeline_v14`, `detect_events`, or any PELT function.
   - The exact path where `{stem}.score.npy` files were written, and whether that path is covered by
     `.gitignore`.
   - Each file's score array length exactly matches its own window count — show the actual numbers for
     at least one subject.
2. Check `UI/B2a*.png` and `UI/B2d*.png` directly: do they show literal pixel text **"Seizure
   Detections"** for the mini-timeline's row 2, or already **"Detections"**? State which, for the
   record — this matters because `SZSCAN_DESIGN_v2.md §8` mandates "Detections" regardless of what an
   older mockup render might still show.

## New bugs found by live visual comparison against the mockups

3. **EEG canvas renders near-black, not the design token's cream `#FEFBEF` background, and the
   waveform renders as dense illegible vertical noise rather than a legible trace** — seen at 1-minute
   window / 20 µV amplitude, i.e. not an extreme setting.
   - `git status` in this step's own report shows `EegPanel.jsx` was modified *this step*, even though
     `CC_STEP5_PROMPT.md` only authorized touching it for wiring the mini-timeline/playhead sync, not
     changing rendering internals.
   - Run `git diff` / `git log` on `EegPanel.jsx` to determine whether this step's sync-wiring edit
     regressed the background color and/or waveform rendering (e.g. drawing full-height spikes instead
     of a connected min/max-envelope trace), **or** whether this is a pre-existing gap that Step 4
     reported as fixed but never actually was. State which, with the diff as evidence, not an
     assertion.
   - To separate "real rendering bug" from "expected clipping at an aggressive amplitude setting" (a
     Step 4 precedent), also test at the largest amplitude token (30 µV) and report whether the trace
     becomes legible there. If it is still all-noise at max scale, that confirms a rendering bug.
   - Fix it.
4. **Toggling the `lff` / `hff` / `60` filter buttons produces no visible change** in the rendered
   waveform. Confirm whether the backend actually returns two distinct series (raw + filtered) per
   `DEMO_BUILD_HANDOFF.md §5`, and whether the frontend switches which one is drawn on top when
   toggled. Fix whichever side is broken.
5. **Changing the toolbar's window-length control (`⊲▷ [X]`) does not change what Panel EEG
   displays** — the view stays fixed regardless of the selected value. Confirm whether this control is
   wired to trigger a re-fetch/re-render at all, and fix it.
6. **Panel Event's column is too short** — it currently only spans the height of the mini-timeline, not
   the full height of the EEG panel below it. Per `UI/B1a*.png` and `UI/B2a*.png`, the Event panel
   should run alongside the full EEG panel. Compare the actual grid/flex structure against those
   mockups and correct the layout.

## How to verify this time

For items 3–6: **do not rely on curl or isolated computed-style checks alone.** Use `claude-in-chrome`
to take actual screenshots and compare them side by side against the relevant mockup PNGs. If the
extension connection is still down, say so explicitly in the report rather than silently falling back
to a narrower check and calling it verified.

## Report

Write findings and fixes to `web_demo/CC_STEP5_FIX_REPORT.md` (new file — keep the original
`CC_STEP5_REPORT.md` as the record of the first pass). Do not mark Step 5 as closed until items 3–6 are
confirmed fixed with visual (screenshot) evidence, not code-read confidence alone.

Run `pytest web_demo/backend/tests/test_guards.py -v` and `git status` again at the end (raw output in
the report, as always).

## Stop condition

Stop once items 1–6 above are all resolved and documented with evidence, guard tests are green, and
`CC_STEP5_FIX_REPORT.md` is written. Do not start Step 6.
