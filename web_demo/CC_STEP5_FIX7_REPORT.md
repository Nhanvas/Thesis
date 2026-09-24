# CC_STEP5_FIX7_REPORT.md — Step 5 fix round 7

Three items: two investigate-and-diagnose, one real fix. Backend (`uvicorn main:app`, port 8000)
and frontend (`npm run dev`, port 5173) were already running from round 6 and reused as-is;
verified live via Chrome (`claude-in-chrome`). Screenshots referenced below are saved under
`web_demo/CC_STEP5_FIX7_SCREENSHOTS/`.

---

## 1 · Solid black vertical bar in Panel EEG on `chb15_01_short.edf` — genuine data, not a bug

**Read the raw `.npy` array directly** (`backend/uploads/chb15/chb15_01_short.raw.npy`, bypassing
`pipeline_demo.py`/`waveform_serving.py` entirely — `np.load(..., mmap_mode='r')`, `.transpose(1,0,2)`
to reconstruct the continuous per-channel signal, values ×1e6 for µV):

- **No NaN, no Inf, anywhere in the file** (`np.isnan(uv).any()` / `np.isinf(uv).any()` both `False`
  over the full 600 s × 18-channel array).
- **No zero-run.** The suspect region is not flat/silent — it's the opposite: enormous excursions.
- Scanning per-second `max(abs(value))` across all 18 channels, the file's single largest event is at
  **t≈247.36–264.63 s relative to file start** (600 s file, 150 windows) — wall-clock
  **18:27:20–18:27:41** (`start_time` 18:23:13 + 247…264 s), amplitudes **3000–5500 µV** (several
  *milli*volts) simultaneously across essentially **all 18 channels** — not 1–2 outlier channels.
  This is squarely inside the range Boti described ("around 18:26–18:27") — the highlighted
  **Event 1** (onset 18:26:53, offset 18:28:17, per the pipeline's own detection) brackets it exactly.
- **Checked for a splice/seam signature (an instantaneous jump between two unrelated sample values,
  the fingerprint of naive concatenation) vs. genuine physiological/movement-artifact dynamics (a
  smooth ramp up and back down over tens of samples).** Inspected raw sample-by-sample values at the
  onset of the burst (channel 0, samples around 63319–63338, i.e. t≈247.34–247.41 s): the signal ramps
  smoothly from ~90 µV down to a local extreme and back, over multiple consecutive 1/256 s samples —
  **not** a single-sample cliff. Same smooth-ramp shape confirmed at an earlier, smaller excursion
  (channel 3, t≈221.29 s, min −1157 µV) that Round 5's construction notes would put near this file's
  interior, not a documented clip boundary. Nothing in either region looks like "two unrelated
  waveforms glued together" — it reads as one continuous (if extreme) physiological signal throughout.
- **Verified the same phenomenon exists in the genuinely real, non-synthetic files** (`chb13_02.edf`,
  `chb13_03.edf` — both confirmed exactly 1 hour at the raw-header level in round 6 —  and
  `chb06_01.edf`, ~4 hours, also real, never uploaded through the demo flow but its cache is genuine).
  Per-second max-abs scan, same method:

  | File | Top events found (µV) | Median per-second max-abs |
  |---|---|---|
  | `chb13_02.edf` | up to **1397.8** (several distinct seconds >1000) | 331.3 |
  | `chb13_03.edf` | up to **1972.9** (several distinct seconds >1000) | 376.8 |
  | `chb06_01.edf` | up to **1283.7** (several distinct seconds >1000) | 419.4 |

  All three real files have the same *kind* of occasional large, broadband excursion (hundreds to
  ~2000 µV) — `chb15_01_short.edf`'s ~247 s event is simply a larger instance of the same thing
  (3000–5500 µV instead of ~1000–2000 µV), consistent with it being built from a real, more dramatic
  segment of chb15 source data (movement/muscle artifact is common and often large in pediatric scalp
  EEG — CHB-MIT's subjects are children).

**Conclusion, stated plainly:** this is real (if extreme) amplitude data — most likely a broadband
movement/muscle artifact — not a NaN, not a zero-run, not a decimation bug, and not a concatenation
seam. `EegPanel.jsx`'s existing per-channel-clipped (not clamped) rendering — deliberately chosen in
an earlier round specifically so a real high-amplitude excursion draws as a busy/saturated trace
rather than a flattened lie — is doing exactly what it was built to do: at a sensitive amplitude
setting (default 75 µV), an excursion of several thousand µV fills its channel's entire row for the
buckets it touches, and because 18/18 channels are affected in this burst (not the more common
3–8/18 seen elsewhere in this same file), the result is a near-solid vertical band. **This can and
will happen on a real full-length upload too** — the three real files above already show smaller
examples of the identical rendering behavior; a large enough real movement artifact would look the
same. No fix applied — there is nothing to fix; forcibly clamping it would recreate the earlier,
already-rejected "flattens into a misleading solid block" bug this same code's comments warn against.

Evidence: `CC_STEP5_FIX7_SCREENSHOTS/item1_black_bar.jpg` (`chb15_01_short.edf`, Event 1 selected,
18:26:47–18:27:4x visible, all 18 channels shown solid through 18:27:20–18:27:39).

---

## 2 · Play on `chb15_01_short.edf` — logic verified correct; could not get a clean live repro

**Round 3's original regression check re-run first, on `chb13_03.edf`:** clicked Play at 1x, three
screenshots ~3 s apart — playhead visibly advanced left→right and the time axis stayed consistent.
**No regression.** (Same file, same check as round 3.)

**On `chb15_01_short.edf`:** clicking Play and watching short, closely-spaced screenshots also showed
correct advance at first (playhead moving, e.g. 18:26:54 → 18:27:00 → 18:27:23 across three ~3–10 s
gaps, matching real elapsed time at 1x). Longer unattended waits, however, repeatedly appeared to
"freeze" — the playhead stopped advancing and the scrub bar stopped moving for many seconds at a
stretch, at several different points (not always the same one), which superficially matches Boti's
report.

**Investigated the freeze directly rather than assuming a cause**, by reading the live React state off
the DOM (`AnalysisScreen`'s fiber, via `__reactFiber$...`) and instrumenting `requestAnimationFrame`,
`setTimeout`, and `window.fetch`:

- Every observed "freeze" coincided **exactly** with `document.hidden === true` / `document.
  visibilityState === "hidden"` for the automation tab, and **zero** `requestAnimationFrame` callbacks
  firing for 5–10+ s stretches (confirmed by wrapping `requestAnimationFrame` and counting calls: `0`
  during a frozen period). This is standard Chrome behavior for a backgrounded/occluded tab — it
  throttles or fully suspends `requestAnimationFrame` (and, after longer stretches, `setTimeout`) to
  save power, independent of any web app's own code.
- **Proved the app's own playback logic is correct once frames actually run**, by replacing
  `window.requestAnimationFrame`/`cancelAnimationFrame` with a `setTimeout`-based polyfill that fires
  regardless of tab visibility, then restarting Play. Under the forced scheduler, `playheadSec`
  advanced correctly and a real window-shift boundary crossing completed cleanly and correctly
  (`windowStartSec`/`waveform` moved `[454,514] → [514,574]`, refetching and updating in sync,
  matching `chb13_03.edf`'s already-confirmed-working mechanism). This is the same window-shift-on-
  boundary code path added in round 3 (`CC_STEP5_FIX3_PROMPT.md` item 1) — nothing file-specific to
  `chb15_01_short.edf` in it.
- Checked explicitly for a connection to item 1's data: the freezes occurred at multiple different
  points across the file, including well before and well after the 18:27:20–18:27:41 burst — **not**
  correlated with entering the high-amplitude region. The playhead-position/window-shift math only
  ever touches *times* (`playheadSec`, `waveform.start_sec`/`end_sec`), never the waveform's amplitude
  values, so a large µV excursion cannot itself produce a `NaN`/`Infinity` in that calculation — and
  none was ever observed in any state read.
- Also found (and want to flag plainly rather than bury): while poking at this with rapid synthetic
  drags to reproduce a boundary case for item 3 below, a fetch response could occasionally apply to
  the canvas later than a subsequent request's response, visible as `waveform` briefly showing a
  slightly stale window after several rapid, closely-timed state changes. This surfaced only under
  automation-driven rapid/artificial event dispatch while the tab was backgrounded (JS timer/microtask
  processing for a hidden tab is not real-time-ordered) and never reproduced under a single, normal
  user-paced action. Not chased further as a code fix — it doesn't match anything in Boti's report and
  I could not separate it from the same environmental throttling from the rest of this item.

**Honest bottom line:** I could not get this automation session's browser tab to behave as a normal,
foregrounded/visible tab (`document.hidden` was `true` persistently, seemingly because the automated
Chrome window itself isn't the OS-focused window in this environment) — and a real user reviewing a
file keeps that tab open and visible. Every freeze I could instrument traced cleanly to zero animation
frames running while hidden, never to file data or to logic that behaves differently between
`chb15_01_short.edf` and the already-confirmed-working `chb13_03.edf`. I'm not able to certify from
inside this session that this fully explains what Boti saw live — only that (a) the code itself,
inspected and exercised via forced, non-throttled ticks, is correct and file-agnostic, and (b) I could
not find any chb15-specific or data-dependent cause. **No code change made for this item** — flagging
for Boti to re-check live (tab focused, not backgrounded) and report back if it still reproduces; if it
does, it isn't explained by anything found here and needs a fresh look with that ruled out.

---

## 3 · Bottom scrub bar sync to file-wide timeline — fixed

**Root cause, found by reading the control's actual DOM attributes, not guessing:** the scrub bar is a
native `<input type="range">` bound to `windowStartSec` in seconds. Its rendered handle position is
always `(value − min) / (max − min)`. Before this fix, `max` was `maxStart` (i.e.
`usable_duration_seconds − windowSec` — the *last reachable* window-start value), not the file's full
duration. `value` itself (`windowStartSec`) was already being set correctly by all three paths (manual
drag — round 2; Play's window-shift — round 3; Event Panel click — Step 5 original), so the bar's
*content* was right but its *scale* wasn't: the handle read **100% whenever the window was merely at
its last reachable start**, not when it was actually at the file's end. For a small window on a long
file the effect is negligible (chb13_03.edf, 1 min window / 3600 s file: 540 s off out of 3540, a
sub-2-point discrepancy near the far end) — but for this round's own test file
(`chb15_01_short.edf`, 1 min window / 600 s file) it's a full **10 percentage point** error at the
reachable end, and worse for larger windows.

**Fix** (`AnalysisScreen.jsx`, the scrub `<input>`): changed `max` from `Math.max(maxStart, 0.001)` to
`Math.max(fileMeta.usable_duration_seconds, 0.001)`. `value`, `min`, `step`, and `onChange` all
untouched. `windowStartSec` itself still never legitimately exceeds `maxStart` (the existing
waveform-fetch effect clamps it back down if a drag pushes it past that point), so this only ever
leaves inert track space to the right of the handle's maximum reachable position when `windowSec` is a
non-trivial fraction of the file — the physically correct behavior for "where does the visible window
sit in the whole recording," not a new dead zone that wasn't already implied by the file being shorter
than the window could reach.

**Verified with evidence (DOM `value`/`max`, not a screenshot guess), 3 positions on
`chb15_01_short.edf` (`usable_duration_seconds = 600`, `windowSec = 60`):**

| Case | How reached | `value` | `max` | Rendered fraction | Expected (`window_start/duration`) |
|---|---|---|---|---|---|
| Start | fresh file load | `0` | `600` | 0% | 0% |
| ~40% | **clicking Event 1 in the Event Panel** (onset 18:26:53, pre-roll applied) | `214` | `600` | **35.67%** | `214/600 = 35.67%` — exact match |
| ~90% | dragging the handle past its reachable end (auto-clamped) / "Jump to end" button | `540` | `600` | **90.00%** | `540/600 = 90.00%` — exact match |

All three match the spec'd formula exactly (not just "close"). The ~40% case was reached via an Event
Panel row click, satisfying the "at least one case via Event Panel" requirement. Screenshot evidence:
`CC_STEP5_FIX7_SCREENSHOTS/item3_scrub_90pct.jpg` (handle visibly short of the track's right edge,
matching the 90%/10%-remaining math, on the "Jump to end" / Event 2 window).

**Confirmed not broken:** dragging the handle still moves the EEG window (tested via synthetic
`input` events at several values — 214→300→450→540(clamped) — each correctly re-fetched the matching
waveform window), matching round 2's already-working behavior. Re-checked `chb13_03.edf` after the
change: fresh load shows `value=0`, `max=3600` (previously `3540`) — same 0%-at-start correctness,
generalizes to the long-file case.

---

## 4 · Guard tests + git status

```
$ pytest web_demo/backend/tests/test_guards.py -v
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
collected 4 items

web_demo/backend/tests/test_guards.py::test_guard_no_build_timeline_masked PASSED [ 25%]
web_demo/backend/tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED [ 50%]
web_demo/backend/tests/test_guards.py::test_guard_no_labeled_npy PASSED  [ 75%]
web_demo/backend/tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED [100%]

============================== 4 passed in 5.03s ==============================
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
	rank_readout.py
	results/attribution_v7/rank_readout_perseizure.csv
	results/attribution_v7/rank_readout_summary.txt
	web_demo/CC_STEP5_FIX2_PROMPT.md
	web_demo/CC_STEP5_FIX2_REPORT.md
	web_demo/CC_STEP5_FIX3_PROMPT.md
	web_demo/CC_STEP5_FIX3_REPORT.md
	web_demo/CC_STEP5_FIX3_SCREENSHOTS/
	web_demo/CC_STEP5_FIX4_PROMPT.md
	web_demo/CC_STEP5_FIX4_REPORT.md
	web_demo/CC_STEP5_FIX4_SCREENSHOTS/
	web_demo/CC_STEP5_FIX5_PROMPT.md
	web_demo/CC_STEP5_FIX5_REPORT.md
	web_demo/CC_STEP5_FIX5_SCREENSHOTS/
	web_demo/CC_STEP5_FIX6_PROMPT.md
	web_demo/CC_STEP5_FIX6_REPORT.md
	web_demo/CC_STEP5_FIX6_SCREENSHOTS/
	web_demo/CC_STEP5_FIX7_PROMPT.md
	web_demo/CC_STEP5_FIX7_SCREENSHOTS/
	web_demo/CC_STEP5_FIX_PROMPT.md
	web_demo/CC_STEP5_FIX_REPORT.md
	web_demo/CC_STEP5_REPORT.md
	web_demo/frontend/src/components/MiniTimeline.jsx
	web_demo/frontend/src/components/PanelEvent.jsx
	web_demo/frontend/src/eventStyle.js
	web_demo/spec_docs_diff.md

no changes added to commit (use "git add" and/or "git commit -a")
```

This round's only code edit is `AnalysisScreen.jsx` (the scrub `<input>`'s `max`, item 3). Items 1 and
2 were read-only investigation — raw `.npy` reads via `numpy` (mmap, never materializing a full file),
live DOM/React-state inspection and `requestAnimationFrame`/`fetch` instrumentation via
`claude-in-chrome`'s `javascript_tool` — no other files written, no database rows changed. `rank_
readout.py` and `results/attribution_v7/*` are pre-existing untracked files from unrelated thesis work
outside `web_demo/`, not touched this round. No Save/Accept/Reject/Select Range actions were taken
during live verification. No restoration needed.

---

## 5 · Stop condition

- Item 1: diagnosed with direct `.npy` evidence (no NaN/zero-run, smooth not step-discontinuous
  excursions, same phenomenon present at smaller scale in three genuinely real files). Stated plainly:
  specific to this file's data being unusually extreme, not to it being synthetic-by-construction, and
  the same rendering would occur on a real upload with a comparably large artifact. No fix applied —
  none needed.
- Item 2: root-caused every reproduced freeze to this automation session's tab being backgrounded
  (`document.hidden`, zero `requestAnimationFrame` calls); proved the underlying play/window-shift/
  fetch logic is correct via a forced non-throttled scheduler. Could not obtain a clean live repro of
  Boti's exact report from inside this session and said so plainly rather than claiming a fix that
  wasn't verified — flagged for his own live re-check.
- Item 3: fixed structurally (the `<input>`'s `max`, not a value/formula patched elsewhere), verified
  against the exact formula at 3 positions via DOM `value`/`max` (not a screenshot guess), including
  one reached via an Event Panel click, plus confirmed drag-to-seek and the long-file (`chb13_03.edf`)
  case both still correct.

Guard tests green. Backend and frontend dev servers left running. **Step 6 (the SPEC's Select Range
step) has not been started.**
