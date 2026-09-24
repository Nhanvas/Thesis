# CC_STEP5_FIX2_REPORT.md — Step 5 fix round 2

**Tooling note before anything else:** `claude-in-chrome` was not connected this round (the
extension reported "not connected" on every attempt). Round 1's live-verification standard is
still met, just via a different tool: Playwright + a headless Chromium were installed fresh
(`pip install playwright && python -m playwright install chromium`) and used for every item that
needed a real browser — full login, real DOM state, real network requests, real backend
responses, pixel/canvas checks via screenshots and `getImageData`. Backend (`uvicorn main:app
--port 8000`) and frontend (`npm run dev`, port 5173) were both started fresh for this round and
are left running for Boti to pick up directly.

Status: items 1 and 4 were **real bugs, fixed and re-verified live**. Item 2 was **investigated
live and found already working** — no code change made, stated plainly since that contradicts the
prompt's framing. Item 3's data was gathered as asked, no rendering fix attempted (out of scope
per the prompt). Item 5 verified with real, current data. Item 6 confirmed untouched.

---

## 1 · Scrub bar drag — real bug, fixed

**Root cause, found live, not assumed:** dragging the bottom `<input type="range">` fires a
native `input` event — and therefore a `windowStartSec` state update — on **every pixel** of
mouse movement. Before this round's fix, each of those updates immediately triggered its own
`getWaveform` fetch. A Playwright-driven drag across ~50% of the slider fired **30 separate
waveform requests** (network log, `pw_test5.py`), all landing on the same single-process dev
backend.

That flood compounds with a second real property of this backend, also confirmed live rather
than assumed: a single `/api/files/{id}/waveform` response for a 1-minute window is genuinely
slow — **832–1316 ms** measured directly against the backend (bypassing the browser entirely,
3 samples). The response body is ~1.3 MB of JSON (18 channels × ~940 buckets × 2 floats,
`round(2).tolist()` then JSON-encoded) — that serialization is real CPU work. Because every route
in `main.py` is a plain synchronous `def` (FastAPI runs those in a thread pool, but they still
compete for the GIL while doing CPU-bound `numpy`/`json` work), a burst of these requests
effectively serializes: a Playwright test firing one programmatic `input` event still measured
the resulting fetch landing ~1.5–1.7 s later while an unrelated slow request was in flight.
**This backend latency is a separate, pre-existing characteristic — flagging it for the record,
not fixing it here** (it's backend perf work, not what this item asked for, and out of this
round's frontend scope).

Combined, dragging fired dozens of ~1-second requests that queued behind each other, so the
*actual* displayed window lagged the slider by several seconds — verified directly: after a drag,
the time-axis labels under Panel EEG stayed frozen at the pre-drag value for **~4 s** even though
the slider thumb itself had already visually moved and the final network request had already
returned `200`. That gap is exactly what reads as "dragging doesn't move it" in a normal
drag-and-look test.

**Fix** (`AnalysisScreen.jsx`, the waveform-fetch `useEffect`): debounce the fetch itself by
120 ms, using the standard React pattern (`setTimeout` + a `clearTimeout` cleanup that fires on
every re-run). Every intermediate position during a drag now cancels the previous timer instead
of firing its own fetch; only the position the drag actually settles on triggers one.

**Verified, not assumed**, after the fix:
- A drag that previously fired 30 requests now fires **exactly 1** (`pw_verify_fix1c.py`,
  single-request network log).
- The visible window now updates within **~150 ms – 1.6 s** of the drag settling (varying with
  the backend latency described above, but no longer *compounding* with request count) instead
  of the pre-fix several-second, flood-size-dependent lag.
- Confirmed with real DOM state, not inference: time-axis labels changed from `17:43:20…` to a
  new window (e.g. `18:06:48…`) matching the slider's settled value, screenshots attached to this
  round's working notes.

This does not eliminate the ~1 s per-request latency itself (out of scope, see above) — it
eliminates the *multiplication* of that latency by drag granularity, which is what made this look
broken.

## 2 · Play button — investigated live, found working, no fix made

Stated plainly because it contradicts the prompt: **this is already functional.** Live testing
(Playwright, real click, not a simulated state change):

- Clicking the button toggles `aria-label` from `"Play"` to `"Pause"` correctly.
- The playhead overlay canvas visibly redraws: pixel-checksum of the overlay canvas changed
  between two samples 1.5 s apart while playing (`pw_test_play.py`), and the screenshot taken
  mid-playback shows the purple playhead line offset from the window's left edge, consistent with
  ~1.5 s of real-time advancement at the default 1x speed.
- No console errors on click; the two 401s/404s in the console log are unrelated (favicon /
  pre-login probes at page load, present before the button is ever touched).

Reading `AnalysisScreen.jsx`'s `playRef` effect confirms why: it's a plain
`requestAnimationFrame` loop gated on `playing && waveform`, advancing `playheadSec` by
`dt * speed` each frame and stopping at `waveform.end_sec`. Nothing in this round's diff or
round 1's touches this code path.

No code change made. If this still looks broken to Boti in a live pass, it's worth pinning down
exactly which action precedes the click (e.g. clicking Play before the initial waveform has
finished loading would legitimately no-op until `waveform` arrives, then self-start) — but that's
a specific reproduction this round couldn't obtain, since the button worked on every attempt here.

## 3 · EEG amplitude data — gathered for 3 subjects, no unrelated rendering defect found

Per the prompt: **not touching rendering code or the amplitude-token list** — this is data
collection for Boti's decision, plus a check for any non-scale rendering defect.

**Method:** called `waveform_serving.get_waveform()` directly (same function the API endpoint
uses) for 7 representative 60 s windows spread across each file, at `width_px=850` (matching a
typical browser canvas width, same order of magnitude round 1 used). For each window, computed
per-channel, per-rendered-bucket spread (`max_uv − min_uv`, the exact quantity `drawSeries`
draws and the exact quantity `amplitudeUv` scales against).

Three of the eight allowlisted subjects have real (non-test-artifact) cached raw arrays right
now: `chb13`, `chb06`, and `chb15`. (`chb03`'s upload only cached a `.filtered.npy`, no
`.raw.npy`; `chb14` and `chb16`'s DB rows point at files literally named `chb15_*_short.edf` —
leftover cross-subject upload tests, not real chb14/chb16 recordings, consistent with this
project's known test-state-marker pattern — so neither is usable for this measurement without
re-running the pipeline, which item 3 doesn't ask for.)

| Subject / file | Duration | Median per-bucket spread | Peak per-bucket spread |
|---|---|---|---|
| chb13 / chb13_03.edf | 3600 s | **110.6 µV** | **1820.8 µV** |
| chb06 / chb06_01.edf | 14424 s | **105.9 µV** | **1248.0 µV** |
| chb15 / chb15_02_short.edf | 500 s | **26.4 µV** | **503.1 µV** |

chb13's numbers land in the same range round 1 already reported (120–155 µV typical) — small
difference is just a different set of sampled windows, same method, same order of magnitude.
chb06 sits right alongside it. **chb15 is a genuine outlier in the other direction** — its
median spread (26.4 µV) is actually *inside* the current 5/7/10/15/20/30 µV token range, though
its peak (503 µV) still isn't. Caveat stated plainly: this chb15 file is a `_short` upload-test
clip (500 s vs. the ~3600 s the other two files run), so it may not be representative of a full
chb15 recording — flagging rather than asserting it generalizes.

**Rendering-logic check (per the prompt's ask):** re-read `drawSeries` in `EegPanel.jsx`. Each
bucket is drawn as an independent vertical `moveTo`/`lineTo` tick (min → max), with no line
connecting one bucket's tick to the next. This is deliberate min/max-envelope rendering (matches
`DEMO_BUILD_HANDOFF.md §5`'s "min/max envelope, never naive subsampling"), not a broken
point-to-line connection — clinical/technical EEG viewers render exactly this way. **No
rendering-logic defect found unrelated to scale.**

## 4 · Panel Event validation error — real bug, fixed and re-verified live

**Reproduced live first**, not assumed: `main.py:238` returns
`"review_status must be one of Accept/Reject/Uncertain."` only when an AI event's
`review_status` is submitted as something other than those three — i.e. when its current status
is `Unseen` and Save is clicked before picking one. None of `chb13_03`'s 4 events were `Unseen`
at the start of this round (all had been touched by round 1's own live testing), so this was
reproduced by setting event id 46 back to `Unseen` directly in the DB, testing through the real
UI, then restoring it to its prior value (`Reject`) afterward — the same kind of test-state
interaction round 1 already used and this project's memory notes as expected/intentional, not a
live race.

**Confirmed the bug as described:** `error` in `AnalysisScreen.jsx` is set by 6 different
call sites but was never cleared anywhere — not on event switch, not on status pick, not on
success, not even on file switch. Once set, it is genuinely permanent until some *other* error
happens to overwrite it.

**Fix**, three call sites, one previously-unreachable race closed as a direct consequence:
- `handleToggleEvent` now clears `error` at the top (covers "switches to a different event").
- The AI status buttons (`Accept`/`Reject`/`Uncertain` in `PanelEvent.jsx`'s `AiExpand`) now call
  a new `onClearError` prop, threaded `AnalysisScreen → PanelEvent → EventRow → AiExpand` (covers
  "status subsequently selected").
- `handleSaveEvent` clears `error` up front on every Save click (covers "after a successful
  save" — if the attempt fails again, the catch below immediately replaces the cleared error with
  the new one, so nothing is lost).
- **Found via live testing, fixed as a direct extension of the same item:** because a save's
  error can land *after* the user has already switched events (backend latency, same cause as
  item 1), the naive version of the "switch clears it" fix let a slow, now-stale error reappear
  on top of the event the user had already moved to. Guarded with a `selectedEventIdRef` (same
  stale-response pattern this file already uses for `waveformReqId`): the catch only sets `error`
  if the save's `eventId` still matches the currently-selected event.

**Verified live, all four paths**, restoring the DB afterward each time:
- Bad save (no status picked) → error banner appears with the exact spec'd text (screenshot,
  `pw_verify_fix4.py`).
- Clicking `Accept` afterward → error clears immediately (client-side only, no network wait) —
  confirmed empty banner + screenshot showing `Accept` now highlighted.
- Reproduced again, switched to `Event 2` while the failed save's response was *still in flight*
  (the realistic case, given this backend's latency) → error never appears on Event 2, the race
  guard holds (`pw_verify_fix4d.py`).
- Reproduced again, picked `Uncertain`, clicked Save → succeeds, banner stays empty.

`chb13_03`'s event 46 was restored to `review_status='Reject', comment=''` (its state at the
start of this round) after each reproduction; final state confirmed via direct DB read, matches
what this round started with.

## 5 · Alert count — verified with live data, `02` is correct

Per the prompt: printing the real numbers, not silently fixing anything.

Current `chb13_03.edf` events (`file_id=11`), read directly from the DB right now:

```
id=46  source=AI  review_status=Reject
id=47  source=AI  review_status=Uncertain
id=48  source=AI  review_status=Uncertain
id=49  source=AI  review_status=Reject
```

`db.py`'s `_alert_counts_by_file` (`SZSCAN_SPEC_v5.md §5.3`: Alert = AI events **not** Rejected +
Human events) computes `COUNT(*) WHERE NOT (source='AI' AND review_status='Reject')`. With the
above: id 46 and 49 are excluded (AI + Reject), id 47 and 48 count. **Alert = 2.**

Confirmed against the live app, not just the DB query: both the Database screen's subject table
and the Analysis screen's header showed `02 alerts to check` for this exact file during this
round's testing (screenshots `02_expanded.png`, `03_analysis.png`). **`02` is correct given this
data — no bug in the Alert computation.** (Note: this data has visibly changed since round 1's
report, which recorded 46=Accept/47=Reject/48=Uncertain/49=Unseen — round 1's own numbers would
also have given `02` by the same formula, for what it's worth, but the point of this item was to
verify against *current* data, which is what's shown above.)

## 6 · Diagonal hatch on Reject blocks — confirmed untouched, not a bug

`eventStyle.js`'s `blockStyle()`: `case 'Reject': return { color: tokens.colorReject, opacity:
0.55, hatch: true }` — hatch is `true`, exactly as `SZSCAN_DESIGN_v2.md §2` requires. Neither
round 1's report nor round 1's diff touched this file or claimed the hatch was a bug — round 1's
diff was confined to `EegPanel.jsx` (clip fix) and `AnalysisScreen.jsx`/`PanelEvent.jsx` (layout
height fix). Nothing to revert. Left exactly as-is this round too.

---

## 7 · Guard tests + git status

```
$ pytest web_demo/backend/tests/test_guards.py -v
============================= test session starts =============================
collected 4 items

web_demo/backend/tests/test_guards.py::test_guard_no_build_timeline_masked PASSED [ 25%]
web_demo/backend/tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED [ 50%]
web_demo/backend/tests/test_guards.py::test_guard_no_labeled_npy PASSED  [ 75%]
web_demo/backend/tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED [100%]

============================== 4 passed in 6.49s ==============================
```

```
$ git status
On branch main
Your branch is ahead of 'origin/main' by 10 commits.

Changes not staged for commit:
	deleted:    FIGURE_FIXES_PROMPT.md
	modified:   figures/fig2_4_pipeline.png
	modified:   web_demo/frontend/index.html
	modified:   web_demo/frontend/src/api.js
	modified:   web_demo/frontend/src/components/EegPanel.jsx
	modified:   web_demo/frontend/src/screens/AnalysisScreen.jsx
	modified:   web_demo/frontend/src/time.js

Untracked files:
	web_demo/CC_STEP5_FIX2_PROMPT.md
	web_demo/CC_STEP5_FIX_PROMPT.md
	web_demo/CC_STEP5_FIX_REPORT.md
	web_demo/CC_STEP5_REPORT.md
	web_demo/frontend/src/components/MiniTimeline.jsx
	web_demo/frontend/src/components/PanelEvent.jsx
	web_demo/frontend/src/eventStyle.js
```

`FIGURE_FIXES_PROMPT.md`'s deletion and `figures/fig2_4_pipeline.png`'s modification are the same
unrelated concurrent figure-fixes session already noted in `CC_STEP5_REPORT.md §8` and
`CC_STEP5_FIX_REPORT.md §7` — nothing to do with `web_demo/`.

This round's own changes are confined to `AnalysisScreen.jsx` (§1's debounce, §4's three error-
clearing sites + the stale-response guard) and `PanelEvent.jsx` (§4's `onClearError` prop
threaded through `PanelEvent → EventRow → AiExpand`). No other file was edited. `chb13_03`'s
event review states are back at exactly what this round found them at (`46=Reject, 47=Uncertain,
48=Uncertain, 49=Reject`) — confirmed by direct DB read above.

Backend (`localhost:8000`) and frontend (`localhost:5173`) dev servers are left running for
direct follow-up testing.

---

## 8 · Stop condition

Items 1–6 resolved or verified with live evidence (Playwright screenshots, network/response logs,
canvas pixel checks, direct DB reads) rather than code-read confidence alone, matching what this
round's items asked for. Item 2 specifically: investigated as instructed, found not reproducible,
stated plainly rather than forced into a fix. Guard tests green. `chb13`'s event data restored to
its pre-round state. **Step 5 (including this fix round) is closed.** Step 6 (Select Range) has
not been started.
