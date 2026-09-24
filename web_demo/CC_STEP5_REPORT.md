# CC_STEP5_REPORT.md — Step 5: Mini-timeline + Panel Event + 3-panel sync

Status: **done**, per the stop condition in `CC_STEP5_PROMPT.md`. Step 6 (Select Range) not started.

This report covers a verification pass resumed mid-step after the Chrome extension had to be
reinstalled to fix a stale account pairing. The implementation (`MiniTimeline.jsx`, `PanelEvent.jsx`,
`eventStyle.js`, plus wiring in `AnalysisScreen.jsx`/`EegPanel.jsx`/`api.js`/`time.js`) already existed
going into this pass; what follows is what was actually exercised live in the browser against
`chb13`, plus one real bug found and fixed along the way.

---

## 0 · Prerequisite check

`pytest web_demo/backend/tests/test_guards.py -v` was green at the start of this pass and green again
at the end (raw output in §8). `chb13` and `chb16` were both at a clean `View` state when this pass
started, as required.

---

## 1 · A real bug found and fixed: Chrome auto-translate crashes React

Early in this pass, expanding a row on the Database screen threw a reproducible React error
(`NotFoundError: Failed to execute 'insertBefore' on 'Node': The node before which the new node is to
be inserted is not a child of this node`), crashing the page to blank. Console inspection showed
`document.documentElement.className === "translated-ltr"` and `lang: "vi"` — this was Chrome's own
page-translate feature silently translating the UI to Vietnamese (triggered by the browser/OS locale),
which rewrites live DOM text nodes and then collides with React's reconciler on the next re-render.
Not an app logic bug, but a real one: this will hit anyone using the app with a non-English Chrome
locale and auto-translate on, and translation could also silently clobber the precise wording this step
cares about (§2 below).

**Fix:** added `<meta name="google" content="notranslate">` to `web_demo/frontend/index.html`. Verified
after the fix: reloading and re-expanding the same row no longer triggers Chrome translate
(`document.documentElement.lang` stays `"en"`, no `translated-ltr` class) and the crash did not
recur across the rest of this pass.

---

## 2 · Wording check

`MiniTimeline.jsx`'s Detections row is labeled exactly `Detections`, not `Seizure Detections` — confirmed
both in source and in the live DOM. Row 1 keeps `Seizure Detection Score` per SPEC §7.2. Empty-state
text on `chb13_02.edf` (0 stored events) is an exact match: *"No detected events in this file. You can
still add an event manually with Select Range."*

---

## 3 · Verification checklist (live, against `chb13_03.edf`, 4 stored AI events)

1. **Mini-timeline renders real stored data.** Opened `chb13_03.edf` — score line renders, Detections
   row shows 4 blocks aligned to the 4 stored events' actual onset/offset (one event was 4 seconds
   long and rendered as a thin sliver, correctly reflecting its short duration, not a rendering bug).
2. **Y-axis has no numbers; auto-scale is per-file.** Confirmed visually (zero-line only, no tick
   labels) and in code (`MiniTimeline.jsx` computes P1/P99 off the `score` prop passed in for the
   currently-open file only — `useMemo` keyed on `score`, nothing shared or hardcoded). Compared
   `chb13_02.edf` (flatter trace) against `chb13_03.edf` (busier trace); both fill the same vertical
   envelope, as expected from per-file auto-scaling.
3. **Mini-timeline is view-only; playhead follows Panel EEG.** Clicking directly on the mini-timeline
   chart produced no change (also confirmed in code — no `onClick` anywhere in `MiniTimeline.jsx`).
   Scrubbing Panel EEG to a new position and reading the playhead `<div>`'s inline `left` style
   confirmed an exact match: click landed at ~42.05s into the file, playhead reported
   `left: 1.16804%` of the 3600s domain = 42.05s.
4. **Two-tier filter + count format.** Tier 1 (`All`/`Human`/`AI`) and tier 2 (`Accept`/`Reject`/
   `Uncertain`/`Unseen`, shown only under `AI`) both present and correct. Count format: `All` → bare
   `4`; `AI → Unseen` → `4/4` initially, dropping to `3/4` after accepting one event — correct `x/y`
   (matches, over total AI events) vs. bare-`x` behavior.
5. **Click event row → Panel EEG + mini-timeline playhead sync.** Clicking Event 1 (onset 17:44:40)
   opened a Panel EEG window starting at 17:44:34 (a few seconds of pre-onset context, landing on the
   event) and put a violet selection outline on the matching mini-timeline block. Panel Event is
   confirmed as the drive source per the code comment in `PanelEvent.jsx` ("Panel Event là nguồn điều
   khiển chính").
6. **Save → Alert count updates live.** Accepting Event 1 left the header at `04 alerts to check`
   (correct: SPEC §5.3's formula is not-yet-Rejected, and Accept doesn't remove that). Rejecting
   Event 2 dropped it to `03 alerts to check` immediately in the header, and the Database screen's
   `chb13` row showed the same `3` after navigating back — both updates confirmed.
7. **Dimming rule, verified via computed style (not eyeballing).** With Event 1 selected: its block
   computed `opacity: 1` with `outline: rgb(124, 58, 237) solid 2px`; Events 2-4 computed
   `opacity: 0.4` with the same underlying `background-color` (unchanged) — i.e. dimming and
   selection-border are additive, exactly as DESIGN §2 requires, not a color override.
8. **Row-2 label.** Confirmed `Detections`, not `Seizure Detections` (see §2 above).
9. **Empty-state wording.** Confirmed exact match on `chb13_02.edf`, the one file among the 5 existing
   subjects with 0 events (see §2).
10. **Guard test + git status.** See §8.

**Extra checks done beyond the required list, since they were cheap given what was already open:**
- All four review-status colors distinct and correctly applied, read via computed style:
  `Unseen` → slate `rgb(51,65,85)` solid; `Accept` → green `rgb(22,163,74)` solid; `Reject` → red
  `rgb(220,38,38)` with a diagonal hatch (`repeating-linear-gradient`); `Uncertain` → amber
  `rgb(217,119,6)` solid. Matches `eventStyle.js`'s `blockStyle()`.
- The EEG panel's own "Event Time" strip (SPEC §6.4, technically Step-4-adjacent but wired up this
  step) reuses the exact same `blockStyle`/`dimOpacity` helpers as the mini-timeline, confirmed by
  reading `EegPanel.jsx` — the two views structurally cannot disagree on an event's color.

---

## 4 · Human-event path: implemented, not live-testable

`PanelEvent.jsx`'s `HumanExpand` component exists and matches spec: Onset/Offset/Duration (read-only),
Delete + a disabled Edit button (correctly scoped to Step 6, with a title explaining why), Comment,
Save — no Accept/Reject/Uncertain. Confirmed by reading the code; as flagged in the prompt, no Human
event can exist yet (Select Range is Step 6), so this path was not exercised live. Saying so plainly
rather than fabricating a Human event to test with.

---

## 5 · Scope discipline

Nothing outside `web_demo/` was touched. The only file changed by this pass itself is
`web_demo/frontend/index.html` (the `notranslate` fix, §1) — the rest of the diff (`MiniTimeline.jsx`,
`PanelEvent.jsx`, `eventStyle.js`, and the `AnalysisScreen.jsx`/`EegPanel.jsx`/`api.js`/`time.js`
wiring) predates this pass and was verified, not rewritten.

---

## 6 · Known limitation already flagged in code

`MiniTimeline.jsx` hardcodes `DOMAIN_SEC = 3600` (SPEC §6.3's stated 1-hour default) with a comment
noting none of the current allowlist's files exceed 1h, so there's no pan/zoom case exercised yet.
Carrying this flag forward rather than silently signing off on it as tested.

---

## 7 · Test-state note

Verifying item 6 (Save → Alert count) required real Accept/Reject/Uncertain saves. `chb13_03.edf` was
left with: Event 1 = Accept, Event 2 = Reject, Event 3 = Uncertain, Event 4 = Unseen. `chb13`'s subject
row now reads `Viewing (0/2)` with Alert `3`, not the clean `View` state it was in at the start of this
pass. Same precedent as Step 3/4's `chb13` "A2 concurrency test" memo note — reset yourself if you'd
rather start Step 6 from a clean slate.

---

## 8 · Guard test + git status (raw output)

```
$ pytest web_demo/backend/tests/test_guards.py -v
============================= test session starts =============================
collected 4 items

web_demo/backend/tests/test_guards.py::test_guard_no_build_timeline_masked PASSED [ 25%]
web_demo/backend/tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED [ 50%]
web_demo/backend/tests/test_guards.py::test_guard_no_labeled_npy PASSED  [ 75%]
web_demo/backend/tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED [100%]

============================== 4 passed in 4.71s ==============================
```

```
$ git status
On branch main
Your branch is ahead of 'origin/main' by 4 commits.

Changes not staged for commit:
	modified:   figures/fig3_4_detection_latency.png
	modified:   src/figures/plot_latency.py
	modified:   web_demo/frontend/index.html
	modified:   web_demo/frontend/src/api.js
	modified:   web_demo/frontend/src/components/EegPanel.jsx
	modified:   web_demo/frontend/src/screens/AnalysisScreen.jsx
	modified:   web_demo/frontend/src/time.js

Untracked files:
	web_demo/frontend/src/components/MiniTimeline.jsx
	web_demo/frontend/src/components/PanelEvent.jsx
	web_demo/frontend/src/eventStyle.js
```

`figures/fig3_4_detection_latency.png` and `src/figures/plot_latency.py` are from an unrelated,
concurrent figure-fixes task in another session on this same working tree (confirmed with that
session directly) — nothing to do with `web_demo/`.

---

## 9 · How to run it

Backend (from `web_demo/backend/`):
```
python -m uvicorn main:app --port 8000 --reload
```
Frontend (from `web_demo/frontend/`):
```
npm run dev
```
Then open `http://localhost:5173/`, log in with the admin credentials in `web_demo/backend/.env`, open
a subject/file, and click an event row in the Panel Event list on the right.

---

## 10 · Stop condition

Per `CC_STEP5_PROMPT.md`: the mini-timeline and Panel Event both render real stored data, the 3-panel
sync and dimming rule work (verified via computed style, not just eyeballing), the wording checks pass,
and this report is written. **Step 6 (Select Range) has not been started.**
