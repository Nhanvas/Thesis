# CC_STEP7_FIX_PROMPT.md — Step 7, fix round 1

Read first: `web_demo/CLAUDE.md`, `web_demo/CC_STEP7_REPORT.md`, and `UI/B2a - Choose an event.png`
(copy it to a scratch folder before viewing; never write scratch files into `UI/`).

Rules that still apply: guards 4/4 green at the end (raw `pytest` output in the report), no
`git add/commit/push`, nothing outside `web_demo/` changes, no change to detection, scoring or
attribution numbers. Use `claude-in-chrome` for all live verification; if it is not connected, stop and
say so. **Do not click Save (attribution or event review) on any real `chb13` event, and do not create,
edit or delete events.** Expanding rows, selecting events, hovering and scrolling are fine.

Boti tested Step 7 live and found two defects. Both are in scope; nothing else is, except Part C
(read-only) and the small spec correction in Part D.

---

## Part A — Bottom scrub bar cannot reach 100 %

**Symptom.** Dragging the bottom scrub bar fully to the right leaves the handle short of the end of the
track, with an unfilled grey remainder to its right (1 min window on a 1 h file: handle sits at ≈ 97–98 %).

**Hypothesis to confirm by reading the code before changing anything.** Since Step 5 fix round 7 the
`<input type="range">` has `max = usable_duration_seconds` while its `value` is `windowStartSec`, whose
largest reachable value is `usable_duration − windowLength`. The handle can therefore never pass
`(duration − windowLength) / duration`. If the code says something different, report what it actually
says and fix the real cause.

**Required behaviour.**
- Handle at exactly 0 % when `windowStartSec = 0`, exactly 100 % when `windowStartSec = maxStart`, where
  `maxStart = max(0, usable_duration − windowLength)`; linear in between (standard scrollbar convention:
  position = `windowStartSec / maxStart`). Set the input's `max` to `maxStart`.
- When `maxStart = 0` (window ≥ file): disable the input, handle at 0, no division by zero, no NaN.
- This deliberately supersedes the round-7 formula `window_start / duration`. The difference is at most
  `windowLength / duration` and is exactly what removes the gap.
- Everything round 7 fixed must keep working: handle follows an Event Panel row click, playback
  advancing, window-length changes, Previous/Next file changes; the 120 ms drag debounce is unchanged;
  the purple fill follows the handle.

**Verify (live, on `chb13_03.edf`):** read the input's `value`/`max` and the handle's bounding box at
start, middle and end, for window lengths 1 min, 10 min (or the nearest option), 30 min, and 1 hr
(expect disabled). At the end position, the unfilled track to the right of the handle must be 0 px
(compare thumb rect to track rect). Click the Event Panel row of the last event and confirm the handle
lands ≤ 100 % and is consistent. Play to the end: playback stops with the handle at 100 %.

---

## Part B — Event Panel and Attribution Panel are in the wrong place

**Root cause (ours, not a coding slip).** `CC_STEP7_PROMPT.md` Part 3 told you to put the attribution
panel in a second row below the EEG row, at natural height with no internal scrollbar ("do not squeeze
panels into one viewport"). That contradicted `UI/B2a`. The UI wins over the prompt. **That instruction
is withdrawn.** The design doc's "Analysis screen may scroll vertically" applies to the page, not to
these two panels.

**Target (from `UI/B2a`):** the right column holds the Event Panel on top and the Attribution Panel below
it, stacked, and **the column's total height equals the height of the EEG card** (toolbar + canvas + Event
Time row + scrub bar). Each panel scrolls **inside itself** when its content is longer. There is no
second row and no blank band under the EEG card.

Measure from the mockup at its native resolution, as fractions of the EEG card's height (so it is
resolution-independent): Event Panel height, Attribution Panel height, and the gap between them. As a
cross-check, my reading is two roughly equal halves (≈ 0.49 / 0.49) with a small gap (≈ 0.013). Use your
measurement, not mine.

**Structure to build.**
1. Remove the Step 7 second row and its flex-1 spacer from `AnalysisScreen.jsx`. Put the Attribution
   Panel in the right column directly under the Event Panel.
2. The right column must **not contribute to the row's height** — the EEG card alone defines it. A
   reliable technique: right column `relative`, inner wrapper `absolute inset-0 flex flex-col` with the
   gap; each panel `flex-1 basis-0 min-h-0` with its own `overflow-y-auto` region. No hardcoded pixel
   height or `maxHeight` (that was the Step 5 round-1 mistake).
3. **Event Panel:** the filter row + count stay fixed at the top; the event list scrolls inside. An
   expanded row with a long comment must scroll inside the panel and must not change the column height.
4. **Attribution Panel:** one scroll region containing colorbar → head diagram → title row → table
   (including its `Rank / Channel / Score / Status` header row), and a **pinned footer** with
   `Save | Clear all` that is always visible without any scrolling, as in `UI/B2a`.
5. **Title position:** in `UI/B2a` the title sits between the head diagram and the table, not above the
   colorbar. Move it there. The string stays exactly `Channel-level reconstruction anomaly — Event N`
   (spec §6.7; wrapping onto two lines is fine). Do not change any other wording, colour, table content,
   status controls or the empty-state text.
6. Keep two-way hover, per-channel Accept/Reject, Save/Clear all logic exactly as they are.

**Verify (live, literal comparison, not code reading):**
- Viewport 1366×768 (the real defense machine) and a 1440-wide layout (force the CSS box width if the
  window cannot be resized). For each, in three states: (a) no event selected, (b) an AI event selected
  with its row expanded (use the event whose comment is 116 characters long), (c) any other event.
- With `getBoundingClientRect`, report: EEG card top/bottom; Event Panel and Attribution Panel
  top/bottom/height; right-column bottom minus EEG-card bottom (must be within 1 px); the measured
  fractions vs the mockup's fractions; page scrollHeight before vs after this fix.
- Confirm by DOM that the Event list and the attribution scroll region each have their own scrollbar
  (`scrollHeight > clientHeight`) when content is long, and that `Save | Clear all` is fully inside the
  viewport with no scrolling.
- Save side-by-side screenshots (live vs `UI/B2a`, same crop) into `CC_STEP7_FIX_SCREENSHOTS/`.
- **Regression:** click an Event Panel row → Panel EEG jumps, mini-timeline playhead moves, attribution
  updates; dimming rule (selected block opacity 1, others 0.4); Select Range still marks and previews
  correctly; the header, mini-timeline and EEG card are pixel-unchanged relative to before this fix.

**One extra check while you are in there.** Boti's screenshot showed most Status rows already on green
`Accept`. Your report (§4) says every row starts unset. Confirm `attribution_status` has 0 rows
(read-only SQLite), open a never-touched event, and report exactly what the Status column shows on first
load. If it shows anything other than unset, that contradicts your report: say so and fix it only if it
is a wrong initial state; otherwise report and stop.

---

## Part C — Read-only measurement (report only, change nothing)

Purpose: decide whether ranking channels by the raw per-node reconstruction score mostly reflects each
channel's own baseline error level. **Do not modify `attribution.py` or any app file. Do not write any
file** — run it as an inline `python - <<'EOF'` script that only reads.

Data: `web_demo/backend/uploads/chb13/chb13_03.pernode.npy` (`[900, 18]`) and the four AI events
(ids 46–49) read from the SQLite DB opened read-only (`file:...?mode=ro`). Use the same overlapping-window
rule as `attribution.py`. This uses no label data: the baseline comes from the whole file's own scores,
the same convention as spec §1.6(a).

For channel `c`: `b_c` = median over all 900 windows of the raw score; `m_c` = `median(|x − b_c|) + 1e-9`
(the pinned `retrain_io.robust_z` recipe, no 1.4826 factor). Alternative score for a window:
`z_c(w) = (raw_c(w) − b_c) / m_c`, aggregated by per-channel mean over the event's windows.

Report, per event and as a small table: (1) Spearman between the current raw ranking and `b_c`;
(2) Spearman between the raw ranking and the `z`-based ranking; (3) top-3 channels under raw vs under `z`;
(4) how many channels appear in the top 5 of all four events under each definition. Add one line stating
the sample size (1 file, 4 events) so nobody over-reads it. **No recommendation, no code change.**

---

## Part D — Spec note correction

In `SZSCAN_SPEC_v5.md`, read note **C20**. If it says the Attribution Panel is a second row, natural
height, or has no internal scroll, replace that with one English sentence describing the new layout
(stacked under the Event Panel, column height = EEG card height, each panel scrolls internally, Save /
Clear all pinned). Minimal edit; do not touch other sections.

---

## Report

Write `web_demo/CC_STEP7_FIX_REPORT.md` with: 1 summary; 2 Part A confirmed root cause (file + line) and
before/after numbers; 3 Part B measurements table and screenshot list; 4 first-load Status finding;
5 Part C output; 6 Part D diff; 7 raw `pytest web_demo/backend/tests/test_guards.py -v`, `git status`,
`git diff --stat`. Then **stop. Do not start Step 8.**
