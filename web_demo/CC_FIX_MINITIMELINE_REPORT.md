# CC_FIX_MINITIMELINE_REPORT.md

Fixes `MiniTimeline.jsx` (SZSCAN_SPEC_v5.md §6.3) for files longer than 1 h. Guards 4/4.

## 1 · What changed

`web_demo/frontend/src/components/MiniTimeline.jsx`:

- Replaced the hardcoded `DOMAIN_SEC = 3600` (an implicit single page starting at file-time 0)
  with a `PAGE_WIDTH_SEC = 3600` constant plus per-render page bounds:
  ```js
  const pageStart = playheadSec != null ? Math.floor(playheadSec / PAGE_WIDTH_SEC) * PAGE_WIDTH_SEC : 0
  const fileDurationSec = fileMeta?.usable_duration_seconds ?? (pageStart + PAGE_WIDTH_SEC)
  const pageEnd = Math.min(pageStart + PAGE_WIDTH_SEC, fileDurationSec)
  ```
- Score polyline: only plots points with `pageStart <= t <= pageEnd`, x = `(t - pageStart) /
  PAGE_WIDTH_SEC`.
- Detections row: an event is skipped if it doesn't overlap `[pageStart, pageEnd)`
  (`offset_sec <= pageStart || onset_sec >= pageEnd`), otherwise its onset/offset are clamped to
  the page edges before converting to a percentage — this is the "clip straddling events to the
  page edge" requirement.
- Playhead fraction: `(playheadSec - pageStart) / PAGE_WIDTH_SEC`.
- Column-boundary ticks: `sec = pageStart + (i / N_COLUMNS) * PAGE_WIDTH_SEC`, still formatted
  with `formatFileTimeMinutes` (file-relative wall-clock, unchanged from before).
- Every page keeps the same fixed 6×10-min grid width (`PAGE_WIDTH_SEC`, not `pageEnd -
  pageStart`) — a trailing partial page (last page of a file whose duration isn't an exact
  multiple of 1 h) still draws all 6 columns, just with data ending partway through, exactly like
  a `<= 1 h` file already did before this fix.
- Y-axis P1–P99 scaling (`useMemo` on `score`) is untouched — still computed over the whole
  file's score array, never re-scoped to the visible page.
- No new props, no click handler added — `MiniTimeline` still receives the same
  `fileMeta/score/scoreWindowSec/events/playheadSec/selectedEventId` from `AnalysisScreen.jsx`
  and pagination is derived entirely from `playheadSec` + `fileMeta.usable_duration_seconds`,
  both of which were already being passed in.

For `pageStart = 0` (any file whose current playhead is in the first hour — which is always true
for a `<= 1 h` file, since the playhead can never exceed `usable_duration_seconds`), every formula
above reduces exactly to the pre-fix formula (`t / DOMAIN_SEC`, `ev.onset_sec/offset_sec` compared
against `0`/`DOMAIN_SEC`, etc.), so `<= 1 h` files are pixel-identical to before.

`web_demo/SZSCAN_SPEC_v5.md` §6.3: added a dated note, **C26, 2026-09-28**, documenting the paging
behaviour (page formula, fixed-grid-per-page rule, no new controls/interaction, Y-axis still
whole-file P1–P99).

Nothing else was touched — no prop signature change, no other component edited.

## 2 · Guards

`pytest backend/tests/test_guards.py -q` → **4 passed**. Frontend-only change; no guarded code
path touched.

## 3 · Build / lint

- `npx oxlint src/components/MiniTimeline.jsx` → clean, exit 0.
- `npm run build` → succeeded (`vite build`, 34 modules, no errors).

## 4 · Live verification (claude-in-chrome)

Connected fine. Ran both dev servers locally (`uvicorn main:app --port 8000`,
`npm run dev -- --port 5173`), logged in as `AdminSzScan`.

**`chb06_01.edf` (~4 h file, `chb06`, currently 0 alerts) and `chb06_02.edf`
(~4 h file, `chb06`, 1 alert, `Event 1` onset `01:05:10`):**

1. Opened `chb06_02.edf`. Mini-timeline correctly rendered **page 1** (ticks `23:09…00:09`,
   matching the file's own start time `Recording 2, 23:09:34`), playhead at the left edge.
2. Clicked the Event Panel row for **Event 1** (onset `01:05:10`, i.e. `pageStart = 3600`). The
   mini-timeline **flipped to page 2** (ticks `00:09…01:09`), the playhead jumped into that page,
   and the Detections block for Event 1 rendered at the correct relative position near the page's
   right edge. Confirms Event-Panel-row-click paging.
3. Dragged the scrub bar to `playheadSec = 7300` (`pageStart = 7200`). Mini-timeline showed
   **page 3** (ticks `01:09…02:09`), playhead near the left edge, consistent with the formula.
   Confirms scrub-bar paging.
4. Set the scrub bar to `3595` (5 s before the 1 h boundary), set playback speed to `8x`, and
   pressed Play. Watched the mini-timeline live: it stayed on page 1 while the playhead approached
   the right edge, then **flipped to page 2 the moment the playhead crossed 3600 s**, playhead
   reappearing at the page's left edge with Event 1's block now visible near the right edge.
   Confirms automatic page-flip during playback across an hour boundary.
5. No console errors at any point (`read_console_messages`, `onlyErrors: true`, checked after
   each of the above).

**`chb16_01.edf` (`chb16`, exactly `01:00:00` duration, 7 alerts) — no-regression check:**

6. Opened it. Mini-timeline rendered the full 6-column grid (`16:39…17:39`, matching file start
   `Recording 1, 16:39:42`) with all 7 Detections blocks in their correct positions, playhead at
   the left edge — `pageStart` stays `0` for the whole file since the playhead can never exceed
   `usable_duration_seconds` (~3600 s). This is the same rendering the component produced before
   this fix (single fixed 1 h page).
7. Clicked an Event Panel row (`Event 5`, onset `17:22:42`) — playhead and the selected-event
   outline moved correctly within the same single page, no page flip, as expected for a `<= 1 h`
   file.

**One pre-existing environment gap found, unrelated to this fix:** `GET
/api/files/{id}/timeline` 404s for every file checked (`chb06_01`, `chb06_02`, `chb16_01`) —
`backend/uploads/**/*.score.npy` does not exist anywhere in this dev checkout, so the Seizure
Detection Score line never draws (row stays blank) regardless of this fix. This matches
`waveform_serving.get_timeline`'s own `FileNotFoundError` path ("This file's ensemble score was
never persisted — see CC_STEP5_REPORT.md") and `BUILD_PROGRESS.md`'s open item "an Analysis-screen
check on the long `chb06` files" — it is a missing score-cache backfill, not something this prompt's
scope (page wiring) touches. The Detections row, grid, ticks and playhead — everything this fix
actually changes — all verified correctly above independent of the score line.

## 5 · Scope check

Touched only `MiniTimeline.jsx` (the paging logic) and `SZSCAN_SPEC_v5.md` (the C26 note). No
other component, no backend file, no prop signature changed.
