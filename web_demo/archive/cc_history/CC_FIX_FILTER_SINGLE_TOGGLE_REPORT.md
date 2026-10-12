# CC_FIX_FILTER_SINGLE_TOGGLE_REPORT.md — collapse the EEG Panel filter toggle from 2 buttons to 1

Scope: `web_demo/frontend/src/screens/AnalysisScreen.jsx`, `web_demo/frontend/src/components/EegPanel.jsx`,
`web_demo/backend/waveform_serving.py`, `web_demo/SZSCAN_SPEC_v5.md` §6.4. Backend's `.bandpass.npy`
caching (`pipeline_demo.py`) and `backfill_bandpass.py` left untouched per the prompt — harmless sunk
cost, already run for all 8 subjects (`CC_FIX_FILTERSTAGES_REPORT.md`). Guards (`test_guards.py`)
confirmed 4/4 green after all changes.

## Why

`CC_FIX_FILTERSTAGES_REPORT.md` (the immediately preceding change) collapsed the old, never-real
3-button toolbar (`lff`/`hff`/`60`, all three toggling the same cached array) down to 2 buttons —
`bpf 0.5-60 Hz` (bandpass-only) and `60` (notch on top) — on the theory that bandpass-only was a real,
distinct intermediate worth exposing. That report's own measurement undercuts that theory:

```
max|raw - bandpass|      = 127.92 uV
max|bandpass - filtered| =   2.91 uV
```

A ~2.91 µV difference is invisible at every amplitude scale the toolbar offers (75-500 µV, SPEC §6.4
C18) — it's ~2-4% of even the *most sensitive* (75 µV) division. And no real downstream pipeline stage
(subject-wide z-score, adjacency/CAR/wPLI/AEC, GAE) ever consumes the bandpass-only array on its own;
`process_subject_phase_b` always operates on `filtered` (bandpass+notch). The bandpass-only toggle was
exposing an intermediate nobody's eye can distinguish from the final state and the pipeline never uses
independently — so it's removed, back to the single toggle that actually matters: **raw vs. the real
preprocessed signal.**

## Frontend

### `AnalysisScreen.jsx`

- `filters: { bpf, notch }` state → single `preprocessedOn` boolean, default `false` (unchanged
  "genuinely raw on load" behavior, CC_STEP5_FIX4).
- `filterMode = preprocessedOn ? 'preprocessed' : 'raw'` (was the 3-way `!bpf ? 'raw' : notch ? 'notch'
  : 'bandpass'`).
- `toggleFilter()` is now a plain boolean flip — the old `if (key === 'notch' && !filters.bpf) return`
  no-op guard is gone along with the state it was guarding.
- `FilterToggle` component: dropped the `disabled` prop and its opacity/cursor styling entirely — with
  only one toggle there's nothing to disable.
- Toolbar: one `<FilterToggle badge="pp" label="Preprocessed (0.5-60 Hz + 60 Hz notch)" .../>` replaces
  the old `bpf`/`60` pair. Label states both real steps combined, honestly, rather than the old vague
  bare "60" or "filtered".

### `EegPanel.jsx`

- `filterMode` prop: `'raw' | 'bandpass' | 'notch'` → `'raw' | 'preprocessed'`.
- Draw logic: `overlayUv` is unconditionally `waveform.filtered_uv` now (was a ternary picking between
  `bandpass_uv` and `filtered_uv`); `anyFilterOn = filterMode === 'preprocessed'`.
- `waveform` prop's documented shape dropped `bandpass_uv` (endpoint no longer sends it — see below).
- SPEC §6.4's "raw is never fully hidden" behavior is unchanged: raw always draws, dimmed to 0.5 alpha
  under the preprocessed overlay when the toggle is on, full alpha alone when it's off.

## Backend (optional cleanup, done)

`waveform_serving.py`'s `get_waveform` no longer loads, decimates, or returns `bandpass_uv` — the
frontend never requested it, so this is a pure trim, not a behavior change for any existing caller.
`_cache_paths` still returns 3 paths (`raw`, `filtered`, `bandpass`) since `pipeline_demo.py` still
writes `.bandpass.npy` and `main.py`'s `_file_detail` still unpacks all 3 (`raw_path, _, _ = ...`) —
left as-is per the prompt, since undoing the cache write wasn't asked for and the file is harmless sunk
cost.

Response shape, confirmed via a live API call after the change:
```
GET /api/files/36/waveform?start_sec=0&end_sec=10&width_px=20
keys: ['channels', 'end_sec', 'filtered_uv', 'n_buckets', 'raw_uv', 'start_sec', 'usable_duration_seconds']
```
No `bandpass_uv` key — matches the frontend, which no longer reads it.

## Docs — SZSCAN_SPEC_v5.md §6.4 (C24)

The toolbar table's filter row still read `lff 0.5 Hz` · `hff 60 Hz` · `60` from the *original* design —
`CC_FIX_FILTERSTAGES_REPORT.md`'s 2-button change was never reflected in this document, so it was stale
twice over by the time this task started. Updated the table row to describe the single `pp Preprocessed
(0.5-60 Hz + 60 Hz notch)` toggle, and added a dated changelog note (**C24, 2026-09-27**) right after the
"Filter toggle" paragraph, in the same blockquote style as C18/C19/C23, explaining both the original
staleness and the reason for landing on one toggle (the 2.91 µV vs 127.92 µV measurement, and no real
downstream consumer of the bandpass-only intermediate).

## Verification

`test_guards.py`, after all changes:

```
============================= test session starts =============================
tests/test_guards.py::test_guard_no_build_timeline_masked PASSED         [ 25%]
tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED     [ 50%]
tests/test_guards.py::test_guard_no_labeled_npy PASSED                   [ 75%]
tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED       [100%]
============================== 4 passed in 3.01s ==============================
```

4/4 green.

**Live browser verification (claude-in-chrome) — completed.** The extension connected this time (no
repeat of the earlier connectivity gap noted in `CC_FIX_FILTERSTAGES_REPORT.md`). Logged in, opened
subject **chb16 / chb16_02.edf** at `http://localhost:5173`, and ran the exact sequence the prompt asked
for:

1. **Fresh load — raw.** Toggle shows `pp Preprocessed (0.5-60 Hz + 60 Hz notch)` with a grey/off dot.
   Waveform: single full-opacity raw trace.
2. **Clicked the toggle on.** Dot turned green. Waveform: raw dimmed underneath, a bold second trace
   (the real preprocessed signal) drawn on top — a plainly visible difference at this amplitude scale
   (75 µV), consistent with the ~127.92 µV raw-vs-preprocessed measurement (over an order of magnitude
   larger than the display's own division width).
3. **Clicked the toggle off.** Dot turned grey, waveform reverted to the single raw trace exactly as in
   step 1.

No console errors at any point in the sequence (checked via `read_console_messages` with
`onlyErrors: true`). Confirmed via a direct API call (above) that the `/waveform` endpoint's response no
longer carries `bandpass_uv`, matching the trimmed frontend.

No bugs found this time — unlike the previous filter-toggle report, this pass introduced no regression
requiring a fix.
