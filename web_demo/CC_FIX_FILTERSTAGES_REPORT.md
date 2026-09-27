# CC_FIX_FILTERSTAGES_REPORT.md — collapse EEG Panel's 3 filter toggles to 2 real ones

Scope: `web_demo/backend/pipeline_demo.py`, `web_demo/backend/waveform_serving.py`,
`web_demo/frontend/src/components/EegPanel.jsx`, `web_demo/frontend/src/screens/AnalysisScreen.jsx`.
Plus a new one-time maintenance script, `web_demo/backend/backfill_bandpass.py`, needed because
every already-processed subject's Phase A cache predates the new intermediate array. `src/*.py`
untouched. Guards (`test_guards.py`) confirmed 4/4 green after all changes.

## Why

`pipeline_demo.process_file_phase_a` only ever runs two filter stages, always in this order and
never independently:

```
bp      = sosfiltfilt(preprocessing._BP_SOS, data, axis=1)                          # bandpass 0.5-60 Hz
notched = filtfilt(preprocessing._NOTCH_B, preprocessing._NOTCH_A, bp, axis=1)      # notch 60 Hz
```

The old toolbar had 3 buttons ("lff" 0.5 Hz, "hff" 60 Hz, "60") all wired to toggle the SAME
cached `filtered` (bandpass+notch) array — there was never a real "highpass-only" or
"lowpass-only" signal to show. That's a UI lie: 3 independently-clickable controls implying 3
independent filters, backed by exactly one combined array. Fixed by exposing the real
intermediate state (bandpass output, pre-notch) as its own cached array and collapsing the
toolbar to 2 controls that actually correspond to the pipeline's 2 real stages.

## Backend

### 1. `pipeline_demo.py` — cache the bandpass-only intermediate

In `process_file_phase_a`, added one array between the existing `bp = sosfiltfilt(...)` and
`notched = filtfilt(...)` lines: `bandpass_windows`, windowed from `bp` (not `notched`) the
exact same way `filtered`/`raw_windows` already are (reshape → transpose → `ascontiguousarray`),
then cast to float32 and — when `cache_dir` is given — saved to `{cache_dir}/{stem}.bandpass.npy`
alongside the existing `.raw.npy`/`.filtered.npy`. Added `bandpass_path: Optional[Path] = None`
to `PhaseAResult`, set from the new save path.

Pure addition, verified two ways:
- `filtered`'s and `notched`'s own code lines are untouched — the new array is read from `bp`
  before the notch line, so it cannot perturb the existing computation.
- The backfill script (below) re-runs this function on already-processed files and asserts the
  re-emitted `.raw.npy`/`.filtered.npy` bytes are identical to what was already on disk before
  computing `.bandpass.npy` — confirmed bit-identical on every file backfilled so far (chb16's
  full 19 files, chb03's full 38, chb06 in progress at time of writing).

### 2. `waveform_serving.py` — serve the third series

`_cache_paths` now returns 3 paths (`raw`, `filtered`, `bandpass`); `get_waveform` loads and
decimates all 3 and adds `"bandpass_uv"` to the response dict alongside the existing
`"raw_uv"`/`"filtered_uv"`. One round trip still returns everything the frontend needs for any
of the 3 reachable states — unchanged from the existing "never a second round trip on a
filter-toggle click" design.

### 3. `backfill_bandpass.py` (new) — backfill for subjects processed before this change

Every subject already in the DB (`chb03/06/13/14/15/16/17/18`) has `.raw.npy`/`.filtered.npy`
from before this change but no `.bandpass.npy` — and `get_waveform` now unconditionally reads
all 3, so without a backfill this change would 500 the waveform endpoint for every existing
subject, not just add a feature for new ones.

Same pattern as the existing `backfill_pernode.py`: for each file missing `.bandpass.npy` whose
source `.edf` is still present under `uploads/{subject_id}/`, re-runs the real
`pipeline_demo.process_file_phase_a(edf_path, cache_dir=...)` — the exact production code path,
not a reimplementation — and asserts the re-written `.raw.npy`/`.filtered.npy` are byte-identical
to what was already cached before trusting the run. Run via `python backfill_bandpass.py
[subject_id ...]` (no args = every subject).

Run to completion for **all 8 allowlisted subjects** — chb03 (38), chb06 (18), chb13 (2), chb14
(26), chb15 (40), chb16 (19), chb17 (21), chb18 (36) — **200/200 files, 0 skipped, every
raw/filtered byte-identity assertion passed.** Every subject's `uploads/{subject}/` now has a
`.bandpass.npy` for every `.edf`, confirmed by a final `.bandpass.npy` vs `.edf` count match
across all 8 directories.

## Frontend

### `EegPanel.jsx`

Replaced the `anyFilterOn` boolean prop with `filterMode: 'raw' | 'bandpass' | 'notch'`:
- `'raw'` — no overlay, raw drawn at full opacity (SPEC §6.4 "raw is never fully hidden" —
  unchanged).
- `'bandpass'` — `waveform.bandpass_uv` drawn prominent, raw dimmed to 0.5 opacity underneath.
- `'notch'` — `waveform.filtered_uv` (bandpass+notch) drawn prominent, raw dimmed underneath.

### `AnalysisScreen.jsx`

- `filters` state: `{ lff, hff, notch }` → `{ bpf, notch }`, both default `false` (unchanged
  "genuinely raw on load" behavior from CC_STEP5_FIX4).
- `filterMode = !filters.bpf ? 'raw' : filters.notch ? 'notch' : 'bandpass'`.
- `toggleFilter('notch')` is a no-op while `filters.bpf` is false (belt-and-suspenders — the
  button is also `disabled`).
- Toolbar: `bpf` badge/label "bpf" / "0.5-60 Hz"; `60` badge unchanged, now with
  `disabled={!filters.bpf}` — a real `<button disabled>`, not just a dimmed style, so no click
  handler fires while raw-only is showing. `FilterToggle` gained a `disabled` prop (opacity-40 +
  `cursor-not-allowed` styling, native `disabled` attribute).
- Notch's own boolean is preserved across a bpf on/off/on cycle (only its *effect* is gated by
  bpf), matching how a real EEG viewer's notch checkbox behaves.

## Verification

`test_guards.py`, after all changes:

```
============================= test session starts =============================
tests/test_guards.py::test_guard_no_build_timeline_masked PASSED         [ 25%]
tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED     [ 50%]
tests/test_guards.py::test_guard_no_labeled_npy PASSED                   [ 75%]
tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED       [100%]
============================== 4 passed in 15.41s ==============================
```

4/4 green.

**API-level verification (chb16, file id 35, `chb16_01.edf`)**, direct HTTP calls against the
real running backend after logging in as the admin user:

```
GET /api/files/35/waveform?start_sec=0&end_sec=60&width_px=200
shapes: raw (18, 200, 2)  bandpass (18, 200, 2)  filtered (18, 200, 2)
raw vs bandpass identical?    False
bandpass vs filtered identical? False
raw vs filtered identical?    False
max|raw - bandpass|   = 127.92 uV
max|bandpass - filtered| = 2.91 uV
```

Confirms the 3 series are genuinely distinct arrays (not the old bug where "hff"/"lff" both
drove the same cached array) and that the notch stage's effect on top of bandpass is real but
small (2.91 uV max, as expected for a narrow 60 Hz notch vs. the much larger bandpass-vs-raw
difference).

**Live browser verification (claude-in-chrome) — completed**, once the extension reconnected
(it was not connected earlier in this session; picked back up in a later autonomous check).
Logged in, opened subject **chb16 / chb16_02.edf** (`http://localhost:5173`) and ran the full
toggle sequence:

1. **Fresh load — raw.** `bpf` grey/off, `60` visibly greyed out (opacity-40) and already
   disabled. Waveform: single full-opacity trace.
2. Clicked the disabled `60` — **no change** (dot stayed grey, waveform untouched). Confirms
   `disabled` is a real, effective HTML attribute here, not just a style.
3. Clicked `bpf` on — dot turned green, `60` badge un-greyed (enabled). Waveform: raw now
   dimmed underneath, a second bold trace (bandpass-only) drawn on top — visually distinct from
   raw, matching the ~128 µV max difference measured earlier via the API.
4. Clicked `60` on — dot turned green. Waveform: overlay still bold-on-top-of-dimmed-raw; the
   bandpass-vs-bandpass+notch difference is small (~2.9 µV max, measured earlier) so the two
   overlay states look nearly identical at a glance — expected, not a bug (a narrow 60 Hz notch
   is a small perturbation next to the much larger bandpass-vs-raw difference).
5. Clicked `bpf` off — dot turned grey, waveform reverted to single raw trace. `60`'s own dot
   **stayed green** (its boolean is preserved) but the badge greyed out and went inert again —
   confirms `toggleFilter('notch')` while `bpf` is off is a true no-op, not just hidden.
6. Clicked `bpf` on again (without touching `60`) — `60`'s dot was already green, and the
   bandpass+notch overlay reappeared immediately, with no extra click needed — confirms the
   "preserve notch's boolean across a bpf on/off/on cycle" behavior described in
   `AnalysisScreen.jsx`'s comment actually works as designed.

No console errors during any of this sequence.

**Bug found and fixed during this verification**: `main.py`'s `_file_detail()` (used by `GET
/api/files/{id}`, `POST /api/files/{id}/viewing`, `POST /api/files/{id}/viewed` — i.e. every
"open a file" call) still did `raw_path, _ = ws._cache_paths(...)`, a 2-value unpack, left over
from before `_cache_paths` was changed to return 3 paths. This 500'd on the very first attempt
to open a file after this change (`ValueError: too many values to unpack (expected 2)`) — a real
regression that had nothing to do with the browser-connectivity delay; it would have hit any
caller, not just the live-verify step. Fixed to `raw_path, _, _ = ws._cache_paths(...)`
(`main.py`), matching the only other call site (`waveform_serving.get_waveform`, already
correct). Re-ran `test_guards.py` (4/4 green, unchanged) and repeated the full live toggle
sequence above against the fix — no further errors.
