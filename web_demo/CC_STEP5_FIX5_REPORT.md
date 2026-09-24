# CC_STEP5_FIX5_REPORT.md — Step 5 fix round 5

Both items investigated live (Chrome, via the `claude-in-chrome` extension) with concrete evidence —
network request payloads, a full-byte canvas pixel diff (not a sparse sample), and the backend route
signature itself, not assertions. **Neither item was a bug; no code was changed this round.** Backend
(`uvicorn main:app`, port 8000) and frontend (`npm run dev`, port 5173) were both started fresh this
round (neither was left running from round 4) and are left running now. Screenshots referenced below
are saved under `web_demo/CC_STEP5_FIX5_SCREENSHOTS/`.

---

## 1 · The `⊲▷ [X] hr` window-length control — works correctly; "does nothing" is explained by every
file in this demo being ≤ 1 hour long

**Root cause is data, not code.** `waveform_serving.usable_duration_seconds()` returns the cached
window count × 4 s per file, and its own docstring already states the bound: *"<= 900 [windows] for
the longest file in the current allowlist, one hour."* Confirmed directly in the UI: expanding `chb13`
on the subject list shows both `chb13_02.edf` and `chb13_03.edf` at exactly `01:00:00` each (the
`02:00:00` "Duration" shown at the subject row is the two files' *sum*, not one file's length).

**The waveform-fetch effect in `AnalysisScreen.jsx` (lines 278–298) is unchanged in its clamping logic
since round 3** — `git log --oneline -- web_demo/frontend/src/screens/AnalysisScreen.jsx` shows a
single commit (`996807f`, pre-Step-5) touching this file; every round-2-through-5 edit described in
the FIX*_REPORT.md history has been living in the uncommitted working tree, so there is no git-blame
boundary between "round 3's version" and now to diff against — but reading the effect itself: whenever
the selected `windowSec` is **≥ the file's `usable_duration_seconds`**, `maxStart = Math.max(0,
duration - windowSec)` evaluates to `0`, so `clampedStart` is always `0` and `endSec =
Math.min(0 + windowSec, duration) = duration`. Every option from `24 hr` down to `01 hr` satisfies
`windowSec >= 3600` for a 3600 s file, so **all eight of them fetch and render the identical
[0, duration] range** — this is correct, deliberate clamping (the endpoint cannot serve time that
doesn't exist), not a stuck state.

**Live-verified on `chb13_03.edf` (3600 s file)**, network request payloads captured directly (not
inferred):

| Selected | Waveform request | Screenshot |
|---|---|---|
| `1 min` (baseline, start=0) | `GET /waveform?start_sec=0&end_sec=60&width_px=849` | `item1_before_1min_start0.jpg` |
| `24 hr` | `GET /waveform?start_sec=0&end_sec=3600&width_px=849` | `item1_after_24hr_fullfile.jpg`, x-axis: `item1_after_24hr_xaxis_labels.jpg` |
| `04 hr` | `GET /waveform?start_sec=0&end_sec=3600&width_px=849` (identical to `24 hr`) | — |
| `30 min` | `GET /waveform?start_sec=0&end_sec=1800&width_px=849` (genuinely narrower) | — |

**The control is not "non-functional" — the canvas and time-axis labels visibly, verifiably change**
on every selection: switching from `1 min` to `24 hr` moved the x-axis from a 1-minute span to
`17:43:20 … 18:43:20` (the file's full extent, confirmed by scrolling to the axis row —
`item1_after_24hr_xaxis_labels.jpg`) and the canvas went from the busy 1-min envelope to a mostly-flat,
full-file envelope (the same "full-file window compressed to ~850 px is a dense min/max envelope"
effect `CC_STEP4_FIX_REPORT.md`'s addendum already documented for amplitude). Selecting `30 min`
produced a genuinely different, narrower request (`0–1800` vs `0–3600`), proving the control responds
correctly below the file-duration boundary too.

**Verdict: not a round-3 regression, and not a bug at all.** It's a pre-existing gap in
`WINDOW_OPTIONS` (`24 hr` down through `01 hr`, eight of the fourteen entries) never actually mattering
for this demo's data, because `SZSCAN_SPEC_v5.md §6.4`'s option list was written independent of any
per-file duration constraint, while every held-out-subject file is capped at ≤ 1 hour by Phase A's own
cache. Round 1 tested `10 min`/`5 min` only (`CC_STEP5_FIX_REPORT.md §5`) — both below the 1-hour
boundary — so it never exercised the region where this became visible. **No code was changed**: the
clamping behavior is the only behavior that could exist given the endpoint's contract (`get_waveform`
never serves past `usable_duration_seconds`), and changing `WINDOW_OPTIONS` itself (e.g. dropping the
now-redundant ≥ 1 hr entries) is a product decision for Boti, not something this prompt asked to be
changed.

---

## 2 · Filter-toggle pixel-difference re-check — round 4's finding holds under a full-byte diff;
architecturally, it cannot be otherwise

**Method upgrade per the prompt:** captured the **entire** base-canvas pixel buffer
(`ctx.getImageData(0, 0, canvas.width, canvas.height)`, all 2,322,864 bytes at the tested canvas size —
every byte, not every 97th) for all four states, with the time window and playhead held completely
fixed throughout (window pinned at `start_sec=3172, end_sec=3232` via the fixed-position slider input,
`chb13_03.edf`'s calmest segment per round 4's own score-based pick; `100 µV` amplitude so the trace is
legible; playback never started). Confirmed via `read_network_requests` that **zero** `/waveform`
requests fired during the entire toggle sequence — the window genuinely never moved between
screenshots, closing round 4's own caveat about window/playhead drift contaminating the comparison.

**Full-byte diff results** (every pair of the four states, all 2,322,864 bytes compared):

| Pair | Differing bytes | % different |
|---|---|---|
| (a) all off → (b) `lff` only | 867,727 | **37.36%** |
| (b) `lff` only → (c) `lff`+`hff` | 0 | **0.0000%** |
| (c) `lff`+`hff` → (d) `lff`+`hff`+`60` | 0 | **0.0000%** |
| (b) → (d) | 0 | **0.0000%** |
| (a) → (c), (a) → (d) | 867,727 | 37.36% (same as a→b) |

Screenshots: `item2a_all_off.jpg`, `item2b_lff_only.jpg`, `item2c_lff_hff.jpg`,
`item2d_lff_hff_notch.jpg`.

**(a) is genuinely, substantially different from (b)/(c)/(d)** — over a third of the canvas's pixels
change when the first filter is switched on (raw → filtered, exactly as `EegPanel.jsx`'s
`anyFilterOn` gate is coded to do). **(b), (c), and (d) are not just "coarsely similar" — they are
byte-for-byte identical, zero differing pixels across the full buffer.** This directly answers the
prompt's concern that a sparse 1-in-97-byte sample might have missed a real, small, localized
difference: it did not miss anything, because there is nothing there to miss.

**Backend/frontend contract check — is any request filter-combination-aware?** No.
`frontend/src/api.js`'s `getWaveform()` sends only `start_sec`, `end_sec`, `width_px` — never any
filter state. More decisively, the backend route itself has no such parameter:

```python
# backend/main.py
@app.get("/api/files/{file_id}/waveform")
def get_waveform(file_id: int, start_sec: float, end_sec: float, width_px: int, request: Request):
    """... Amplitude-scale changes are pure frontend and never reach this endpoint at all."""
```

There is no code path, on either side, by which a filter-toggle combination could reach the backend or
change which bytes come back — this isn't a missing wire that happens not to be used, the endpoint's
signature has no slot for it. `pipeline_demo.py`'s Phase-A caching writes exactly one
`{stem}.filtered.npy` per file (`bp = sosfiltfilt(...)` then `notched = filtfilt(...)` applied together,
once, at cache-build time — lines 193–194), so there is exactly one filtered series to ever serve.
Fetched directly to confirm raw and filtered are genuinely different arrays (not the same data twice):
`ch0_raw_sample = [[-212.36, -64.66], ...]` vs `ch0_filtered_sample = [[-190.14, -79.31], ...]`,
`identical: false` — filtering is real, it just isn't separable into three toggleable stages.

**Verdict: round 4's finding is confirmed, not overturned — this time with a rigorous method.** There
is no real difference between `hff`/`60` toggle states; what Boti saw was necessarily either (a) the
one real, large raw→filtered transition (turning the *first* filter on from an all-off state) attributed
to whichever specific button he pressed at that moment, or (b) a window/playhead shift between his two
glances (round 3's auto-scroll during playback, or simply re-opening the file/popover between checks) —
not a `hff`/notch-specific rendering effect, which this round's fixed-window, full-byte, zero-diff
result rules out at the pixel level. Whether to invest in separate cacheable filter stages so the three
buttons become independently meaningful remains Boti's call, per round 4's own framing — not repeated
here since nothing about that recommendation changed.

---

## 3 · Guard tests + git status

```
$ pytest web_demo/backend/tests/test_guards.py -v
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
collected 4 items

web_demo/backend/tests/test_guards.py::test_guard_no_build_timeline_masked PASSED [ 25%]
web_demo/backend/tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED [ 50%]
web_demo/backend/tests/test_guards.py::test_guard_no_labeled_npy PASSED  [ 75%]
web_demo/backend/tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED [100%]

============================== 4 passed in 7.16s ==============================
```

```
$ git status
On branch main
Your branch is ahead of 'origin/main' by 12 commits.

Changes not staged for commit:
	modified:   web_demo/DEMO_BUILD_HANDOFF.md
	modified:   web_demo/SZSCAN_DESIGN_v2.md
	modified:   web_demo/SZSCAN_SPEC_v5.md
	modified:   web_demo/frontend/index.html
	modified:   web_demo/frontend/src/api.js
	modified:   web_demo/frontend/src/components/EegPanel.jsx
	modified:   web_demo/frontend/src/screens/AnalysisScreen.jsx
	modified:   web_demo/frontend/src/time.js

Untracked files:
	bme11/
	web_demo/CC_STEP5_FIX2_PROMPT.md
	web_demo/CC_STEP5_FIX2_REPORT.md
	web_demo/CC_STEP5_FIX3_PROMPT.md
	web_demo/CC_STEP5_FIX3_REPORT.md
	web_demo/CC_STEP5_FIX3_SCREENSHOTS/
	web_demo/CC_STEP5_FIX4_PROMPT.md
	web_demo/CC_STEP5_FIX4_REPORT.md
	web_demo/CC_STEP5_FIX4_SCREENSHOTS/
	web_demo/CC_STEP5_FIX5_PROMPT.md
	web_demo/CC_STEP5_FIX5_SCREENSHOTS/
	web_demo/CC_STEP5_FIX_PROMPT.md
	web_demo/CC_STEP5_FIX_REPORT.md
	web_demo/CC_STEP5_REPORT.md
	web_demo/frontend/src/components/MiniTimeline.jsx
	web_demo/frontend/src/components/PanelEvent.jsx
	web_demo/frontend/src/eventStyle.js
	web_demo/spec_docs_diff.md

no changes added to commit (use "git add" and/or "git commit -a")
```

**No source file was edited this round.** `AnalysisScreen.jsx` does not appear as newly modified
relative to before this round started — both investigations concluded the existing behavior is
correct, so nothing needed fixing. The only new artifacts are this report and
`web_demo/CC_STEP5_FIX5_SCREENSHOTS/`. No database/event-review state was touched (no Save/Accept/
Reject/Select Range actions) — only UI-only state (window length, amplitude, filter toggles, scrub
position) was exercised, all non-persisted. No restoration needed.

---

## 4 · Stop condition

Both items resolved with live evidence, and neither required a code change:

- Item 1: the window-length control works correctly at every value tested (`1 min`, `30 min`,
  `04 hr`, `24 hr`) — verified via actual network request payloads and the rendered time-axis labels.
  The perception that `24 hr` "does nothing" is fully explained by every file in the held-out
  allowlist being capped at ≤ 1 hour (`waveform_serving.py`'s own docstring confirms this bound):
  every option ≥ 1 hour collapses, correctly, to the same full-file view. Not a round-3 regression;
  a pre-existing gap in the option list that round 1 never tested at the extreme.
- Item 2: redone with a full-byte canvas diff (2,322,864/2,322,864 bytes compared, not a 1-in-97
  sample) on a window pinned fixed for the entire sequence (zero `/waveform` requests fired during
  toggling, confirmed via network log). Result: `(a)` all-off differs from `(b)/(c)/(d)` by 37.36% of
  pixels (the real raw→filtered switch); `(b)`, `(c)`, and `(d)` are exactly, provably identical —
  0 differing bytes. Confirmed architecturally at the backend route signature itself
  (`get_waveform(file_id, start_sec, end_sec, width_px, request)` — no filter parameter exists) that
  no request is or could be filter-combination-aware. Round 4's finding stands, now on rigorous
  evidence rather than a coarse fingerprint.

Guard tests green. Backend and frontend dev servers left running. **Step 6 has not been started, and
`AMPLITUDE_OPTIONS` was not touched** — both per the prompt's stop condition.
