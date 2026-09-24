# CC_STEP5_FIX4_REPORT.md — Step 5 fix round 4

Both follow-up questions verified live with concrete evidence — screenshots, direct network
responses, and pixel-level canvas checks, not assertions. One real bug was found and fixed
(item 2's default). Screenshots referenced below are saved under
`web_demo/CC_STEP5_FIX4_SCREENSHOTS/`. Backend (port 8000) and frontend (port 5173) dev servers
were already running from the prior round; both reused as-is.

---

## 1 · Do the low amplitude levels (5/7/10/15/20/30 µV) still serve a purpose?

**Segment selection, not arbitrary:** read `chb13_03.edf`'s stored events directly from the DB —
`80–164s`, `2420–2424s`, `2800–2804s`, `3440–3444s` (all `AI`, `Reject`/`Uncertain`). Rather than
just picking a time a few minutes from those (which I also did, as a sanity check — see below),
I went one step further and used the file's own mini-timeline ensemble score (`GET
/api/files/11/timeline`) to find the actual calmest stretch: scanning every 60 s window at least
180 s from every stored event's onset/offset, the window with the lowest mean |score| is
**3172–3232 s** (mean |score| ≈ 0.33, close to the zero line — genuinely the flattest,
least-anomalous part of this file by the model's own signal, not just "away from a label").

**Quantitative check before screenshotting anything** (via `waveform_serving`'s own
`max_uv − min_uv` per rendered bucket, the exact quantity `drawSeries` draws and `amplitudeUv`
scales against — same method round 2/3 used):

| Window | Median spread | P95 spread | Peak spread |
|---|---|---|---|
| Round 3's busy test window (`0–60s`) | 123.9 µV | 361.8 µV | 1820.8 µV |
| Arbitrary "far from events" pick (`1200–1260s`) | 102.8 µV | 303.6 µV | 1471.5 µV |
| **Lowest-score window (`3172–3232s`, used for the screenshots below)** | **102.0 µV** | 301.2 µV | 1201.5 µV |

The calmest 60 s stretch in the whole file still has a median per-channel spread of ~102 µV —
essentially the same order of magnitude as the busy window round 3 tested (123.9 µV), not
meaningfully lower. This matters directly for the question asked: "quiet" in this data (by
detection score) does not mean "low physiological amplitude" — normal background scalp EEG here
runs ~100 µV regardless.

**Screenshots, same calm window (3172–3232s):**

| Amplitude | Screenshot | Result |
|---|---|---|
| 10 µV | `item1_lowestscore_10uV.jpg` | Near-solid black/white clipping — same character as round 3's 5 µV shot on the busy window |
| 20 µV | `item1_lowestscore_20uV.jpg` | Still near-solid clipping, no real improvement over 10 µV |
| 100 µV | `item1_lowestscore_100uV.jpg` | Legible, connected, undulating waveform — each channel readable |

(The earlier, arbitrary "few minutes from events" pick at `1200–1260s` was screenshotted first
and shows the identical pattern — `item1_calm_arbitrary_10uV.jpg` / `_20uV.jpg` / `_100uV.jpg` —
kept in the evidence folder as a cross-check, superseded by the score-based pick above as the
more rigorously justified "calm" segment.)

**Finding: the low levels do not earn their place, even on the calmest segment in this file.**
10 µV and 20 µV are illegible (near-solid clipping) on both the busy window round 3 tested and
the genuinely calmest window in `chb13_03.edf`, found by the model's own score rather than by
eye. SPEC §6.4/C18's stated reasoning for keeping the 6 old levels was "for flat (interictal)
signal segments" — but the flattest segment measured here is still ~100 µV median, i.e. the same
regime the new 50–500 µV levels were added to cover. **Recommendation: prune 5/7/10/15/20/30 µV**
(or at minimum reconsider whether they should stay) — but this is a recommendation, not a change
made. Nothing was pruned; `AMPLITUDE_OPTIONS` is untouched this round. Boti decides.

---

## 2 · Is Panel EEG showing raw or already-filtered data by default?

### What the green dot means, and what the default was

Read `AnalysisScreen.jsx`'s `FilterToggle` component and the `filters` state directly (not
inferred from appearance):

```js
const [filters, setFilters] = useState({ lff: true, hff: true, notch: true })   // BEFORE this round
...
<span className={... ${active ? 'bg-accept' : 'bg-unseen'} }/>   // FilterToggle's dot
```

**The green dot means on/active — not "available."** `active` is passed straight from
`filters.lff` / `.hff` / `.notch`; the dot is `bg-accept` (green) only when that specific filter
is currently toggled on, `bg-unseen` (gray) when it's off. There's no third "available but
inactive" state — the button is always clickable, the dot only ever reflects on/off.

**The default, before this round, was all three `true`.** On a completely fresh page load, all
three toggles started lit green — i.e. **already on**, not an unselected default a user then
opts into.

### Confirming which series was actually drawn, via network response + pixels (not a guess)

`EegPanel.jsx`'s draw logic:
```js
drawSeries(waveform.raw_uv, ..., anyFilterOn ? 0.5 : 1)      // raw: dimmed once any filter is on
if (anyFilterOn) drawSeries(waveform.filtered_uv, ..., 1)    // filtered: only drawn, and full-opacity, when on
```
With the old default (`anyFilterOn = true` from the moment the page loads), the **filtered**
series was the one drawn prominent (alpha 1) and raw was already the dimmed background (alpha
0.5) — on the very first render, before the user touches anything.

**Verified directly against the live network response**, not assumed from the code:
```js
GET /api/files/11/waveform?start_sec=1200&end_sec=1260&width_px=850
→ 200, keys: ["channels","start_sec","end_sec","usable_duration_seconds","n_buckets","raw_uv","filtered_uv"]
ch0_raw_sample:      [[-132.65, 69.74], [-165.47, 106.47], [-186.57, -50.21], ...]
ch0_filtered_sample: [[-112.74, 71.24], [-136.56, 125.39], [-159.11, -55.53], ...]
identical: false
```
Confirms `DEMO_BUILD_HANDOFF.md §5`: one response always carries both series, genuinely
different arrays (not the same data duplicated under two keys) — so which one is *drawn*
prominent is purely a frontend state decision, which is exactly what was wrong.

**Pixel-level confirmation of which one paints the canvas**, via `getImageData` on the live base
canvas (channel-row color, not a screenshot guess): with the old all-true default, the sampled
row color was `rgb(15,23,42)` = `#0F172A` — `SZSCAN_DESIGN_v2.md §3`'s **Filtered EEG** token,
at 100% opacity — exactly on a fresh load, no filter explicitly touched yet.

### Fix applied

`AnalysisScreen.jsx`, one state initializer:
```diff
- const [filters, setFilters] = useState({ lff: true, hff: true, notch: true })
+ const [filters, setFilters] = useState({ lff: false, hff: false, notch: false })
```
Each toggle was already independently switchable (three separate booleans, `toggleFilter(key)`
flips one at a time) — the only bug was the starting values.

**Re-verified after the fix**, same live checks:
- Fresh load: all three dots gray (`item2_default_filter_dots_gray.png`, zoomed).
- Pixel sample on the base canvas at load: `rgb(100,116,139)` = `#64748B` at alpha 255 — SPEC's
  **Raw EEG** token, full opacity. `#0F172A` (filtered) does not appear anywhere in the sampled
  row. Confirms the default view is genuinely raw, not filtered-by-default.

### Progressive filter screenshots (same calm segment as item 1, 100 µV so the effect is legible)

| Step | Screenshot | Canvas pixel-sum hash* |
|---|---|---|
| (a) All filters off — raw only | `item2a_all_off_raw_only.jpg` | **4902074** |
| (b) `lff` only on | `item2b_lff_only.jpg` | 4226167 |
| (c) `lff` + `hff` on | `item2c_lff_hff.jpg` | 4226167 |
| (d) `lff` + `hff` + `60` (notch) on | `item2d_lff_hff_notch.jpg` | 4226167 |

*Sum of every 97th byte of the base canvas's raw pixel buffer (`getImageData`), a cheap exact
content fingerprint — not a visual guess.

**(a) is genuinely different from (b)/(c)/(d)** — confirms the fix: turning any filter on
switches the prominent line from raw to filtered, visibly (thinner gray/raw vs. thicker
dark/filtered in the screenshots) and at the pixel level. **(b), (c), and (d) are pixel-for-pixel
identical to each other** — turning `hff` or `60` on/off after `lff` is already on changes
nothing on screen. This is not a new problem introduced by this round; it's the same,
already-documented architectural fact from an earlier round's own code comment in
`AnalysisScreen.jsx` (`FilterToggle`'s note: "all gate the SAME real filtered series... there is
no real 'highpass-only' or 'lowpass-only' signal to show"): `pipeline_demo`'s bandpass+notch is
one combined, non-separable filter stage (matches `preprocessing.py`'s actual steps, which are
applied together, not as three independently-cacheable outputs), so the backend only ever has
**one** `filtered_uv` array to serve — there is no distinct "bandpass-only" vs.
"bandpass+notch" series to draw even in principle without new backend work. Stating this
plainly per the prompt's instruction rather than presenting (b)/(c)/(d) as if they showed a real
progressive effect: **the three buttons are independently clickable, but not independently
wired to different data.** Whether that's worth adding backend-side (separate cached filter
stages) is a decision for Boti — not made here.

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

============================== 4 passed in 2.10s ==============================
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
	web_demo/CC_STEP5_FIX4_SCREENSHOTS/
	web_demo/CC_STEP5_FIX_PROMPT.md
	web_demo/CC_STEP5_FIX_REPORT.md
	web_demo/CC_STEP5_REPORT.md
	web_demo/frontend/src/components/MiniTimeline.jsx
	web_demo/frontend/src/components/PanelEvent.jsx
	web_demo/frontend/src/eventStyle.js
	web_demo/spec_docs_diff.md
```

This round's only code change: `AnalysisScreen.jsx`'s `filters` initial state (item 2's fix).
`bme11/` and the `SZSCAN_*`/`DEMO_BUILD_HANDOFF.md` modifications predate this round (unrelated /
prior-round work, as noted in round 3's report). No database or event-review state was touched —
item 1 was read-only (DB query for events, network calls for score/waveform), item 2's live
testing only toggled UI-only filter/amplitude/window state, never Save/Accept/Reject/Select
Range. No restoration needed.

---

## 4 · Stop condition

Both items answered with concrete evidence:
- Item 1: the low amplitude levels (5–30 µV) are illegible even on the file's own
  score-identified calmest segment (median spread ~102 µV there vs. ~124 µV on round 3's busy
  window — not a meaningfully different regime). Recommend pruning; not pruned. Boti decides.
- Item 2: confirmed a real bug (all three filters defaulted to on, so the default view was
  already-filtered data drawn prominent) via code, a live network response, and pixel-level
  canvas sampling; fixed the default to all-off; re-verified raw is genuinely primary by
  default via the same pixel check. The four-step progression screenshots show a real (a)→(b)
  change and an honestly-reported non-change across (b)/(c)/(d), traced to the backend serving
  one combined filtered array rather than three separable stages — not fabricated as if the
  toggles produced three distinct signals.

Guard tests green. Backend and frontend dev servers left running. **Step 6 has not been
started.**
