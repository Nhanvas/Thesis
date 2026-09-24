# CC_STEP6_REPORT.md — Step 6: Select Range (manual event creation)

## 0 · Pre-flight

`pytest web_demo/backend/tests/test_guards.py -v` was green before any code was touched and green
again at the end (raw output in §16). Confirmed `chb13_03.edf`'s 4 AI events were still exactly
Event1=Reject/Event2=Reject/Event3=Uncertain/Event4=Reject (subject `chb13` Alert=1 for the file, 2 for
the subject) before making any change — matches `BUILD_PROGRESS.md §8`'s account (the memo string
`A2 concurrency test` on the `chb13` row is a pre-existing, intentional DB fixture, unrelated to this
step).

Read `SZSCAN_SPEC_v5.md §6.6`/§6.5, `SZSCAN_DESIGN_v2.md §1`/§2, and `UI/B3a-c` in full before writing
code, per the prompt's reading order. `claude-in-chrome` was used from the start for all live
verification below; the extension was not connected on the first `tabs_context_mcp` call (no
`learnings.md` exists in this repo to follow, despite the prompt assuming one) — flagged to Boti
immediately rather than falling back to a narrower check, per a re-check it connected on retry.

## 1 · Two gaps the prompt flagged, and what was built

### Gap 1 — no create/update/delete event endpoints existed

`DELETE /api/events/{id}` and `PATCH /api/events/{id}` (review_status/comment only) already existed
from Step 5, but nothing could create a Human event and nothing could change one's onset/offset. Added,
all under `web_demo/backend/`:

- `db.create_event(file_id, onset_sec, offset_sec)` — always inserts `source='Human'`,
  `review_status=NULL` (a Human event carries no review-status axis at all, not a hidden default —
  `SZSCAN_DESIGN_v2.md §2` Axis 1/2).
- `db.update_event_times(event_id, onset_sec, offset_sec)` — the Edit path (§2 below).
- `POST /api/files/{file_id}/events` — the only way a Human event is created. Sorts the two incoming
  points (`sorted((onset, offset))`) before writing, so a reversed drag never reaches the DB unsorted;
  422s on a non-positive duration.
- `PATCH /api/events/{event_id}` extended with optional `onset_sec`/`offset_sec` — 422s if the target
  isn't a Human event (an AI event's range is immutable per §6.5), 422s if only one of the pair is
  given, sorts and validates the same way as create.
- `api.js`: added `createEvent(fileId, onsetSec, offsetSec)`; the Edit path reuses the existing generic
  `updateEvent(eventId, payload)` with `{onset_sec, offset_sec}` — no new frontend API function needed
  for it.

### Gap 2 — "Event N" chronological ordering across all three views

This turned out to already be solved server-side, not something this step needed to newly design:
`db.py`'s `list_events`/`get_event` (written in Step 5) sort by `onset_sec ASC, id ASC` and derive
`name = f"Event {index + 1}"` from that position at *read* time — never stored, so there is no
renumbering bookkeeping to get wrong. Live-testing this against `chb13_03`'s 4 pre-existing AI events
(onsets 80s / 2420s / 2800s / 3440s) plus a newly-created Human event at onset 2561.2s confirmed it
renumbers **every** event on each read, not just the new one relative to its immediate neighbors: the
old Event3 (onset 2800s) and Event4 (onset 3440s) correctly became Event4/Event5 once the new event
took the Event3 slot (see §6 below for the exact before/after).

**The choice this step made:** full chronological resort on every read, applied uniformly. I called
this out explicitly because `UI/B3c` itself is *not* fully chronological — its own before/after shows
Event4 (onset 16:16:01) staying last even after a new event is inserted earlier in the file, even
though 16:16:01 is earlier than the Event2/Event3 it stays behind. That looks like the mockup's sample
data was never actually re-sorted when it was drawn, rather than a deliberate "partial reorder" rule —
nothing in `SZSCAN_SPEC_v5.md §6.6` step 5 asks for anything less than full chronological order
("inserts itself at the correct time position in the list"), and partial reordering would make the
Event Panel, Event Time row, and mini-timeline harder to reason about together, not easier. I did not
change the mockup-vs-doc precedence rule for anything *visible* (color/position) — this is purely the
numbering scheme, which the mockup's own sample data doesn't consistently demonstrate either way.

Because `PanelEvent.jsx`, `EegPanel.jsx`'s Event Time row, and `MiniTimeline.jsx`'s tooltip all already
read `ev.name` off the same API response (Step 5), this ordering choice needed zero propagation work on
the frontend — it was already consistent everywhere by construction. Verified live in §6.

## 2 · Edit — the spec gap and the reading used

`SZSCAN_SPEC_v5.md` doesn't say what Edit does; `UI/B3c` shows a Human event's expanded state with a
`Delete` / `Edit` button pair but not what clicking Edit produces. Reading used, exactly per the
prompt's suggested interpretation: **Edit re-enters Select Range-style marking mode**, scoped to
overwrite that event's onset/offset instead of creating a new one, once both clicks land. This mirrors
the AI "Reject-and-redraw" asymmetry in §6.5 — a Human event, being fully editable, gets a direct
2-click redraw instead of delete-and-recreate.

Implementation (`AnalysisScreen.jsx`): clicking Edit sets `editingEventId` and enters the same
`selectRangeActive`/`markingOnsetSec` state machine Select Range uses. The Event Time row's toolbar
button and cursor affordance are identical for create vs. edit; the only different visible cue is that
the being-edited event's expand panel swaps its Delete/Edit buttons for a one-line hint ("Click two
points on the EEG grid to redraw this event") while marking is in progress, so the two controls that
would corrupt the in-flight edit (Delete, a second Edit click) are hidden rather than merely relying on
the user not clicking them. On completion, `PATCH /api/events/{id}` is called with the new
`onset_sec`/`offset_sec`; the event keeps its DB id (its `Event N` label may shift if the edit moves it
across another event's onset — not tested live since the redraw in §6 didn't cross a neighbor, but the
same full-resort read path in Gap 2 handles it identically to a fresh create).

## 3 · Cancel — no mockup affordance, reading used

Not shown in any mockup. Implemented: clicking the `Select Range` toolbar button again while a mark is
in progress (onset already clicked, offset not yet clicked) cancels cleanly — `selectRangeActive`,
`markingOnsetSec`, and `editingEventId` all reset, no partial event is ever written (the only place that
calls `createEvent`/`updateEvent` is the completion branch of the second click, which cancel never
reaches). The same button doubles as "Cancel" for both the create flow and an in-progress Edit redraw,
since both share the same marking state machine. The button's own label switches to `Click onset…` /
`Click offset…` while active (with a `Click to cancel` tooltip) so this is discoverable rather than a
hidden shortcut.

## 4 · Live drag preview and onset marker — visual choices

- **Onset marker**: reuses the exact playhead visual (violet vertical line + triangle,
  `tokens.colorInteraction`) rather than a new style. `DESIGN §2`'s interaction axis ("currently
  interacting" = violet) already covers an in-progress mark, and `UI/B3a`'s onset line is visually
  indistinguishable from a playhead in the mockup itself — confirmed by re-reading the mockup rather
  than guessing.
- **Live preview rectangle**: Human blue (`#2563EB`) at 35% opacity with a dashed border in the Event
  Time row, direction-agnostic (computed with `min`/`max` of onset and live cursor position) so it
  never visually "goes negative" during a right-to-left drag either. Deliberately not the same solid
  style as a committed block, so it reads as provisional.

## 5 · Direction-agnostic drag (item 13)

Handled once, in `handleGridClick` (`AnalysisScreen.jsx`): `onset = Math.min(...)`,
`offset = Math.max(...)` regardless of click order, before either `createEvent` or `updateEvent` is
called. The backend independently re-sorts the same way (`sorted((payload.onset_sec,
payload.offset_sec))`) as defense-in-depth at the API boundary, since Select Range is the only call
site but the endpoint itself shouldn't trust order from any future caller either.

## 6 · Live verification (claude-in-chrome, real UI, real backend)

Subject `chb13`, file `chb13_03.edf` (2-hr window not needed — file is 1 h). Window set to 5 min then
1 min for precise clicking; onset/offset read from the expanded panel after each action, not eyeballed.

1. **Marking mode activates** — clicked `Select Range`: button turned solid brand-purple, label became
   `Click onset…`, cursor became a crosshair over the grid. ✅
2. **Onset click** — clicked the grid at a point between the existing AI events (target ~18:26:00):
   a violet vertical marker appeared at exactly that x position, button label became `Click offset…`. ✅
3. **Live drag preview** — moved the mouse right without clicking: a semi-transparent blue rectangle in
   the Event Time row grew from the onset marker to the live cursor position, confirmed at two
   different cursor positions (stretched further the second time). ✅
4. **Offset click** — clicked a second point: rectangle locked, button reverted to `Select Range`,
   marking mode ended. ✅
5. **Onset/Offset/Duration match** — new event read back as **Onset 18:26:01, Offset 18:27:00,
   Duration 1:00** (DB: `onset_sec=2561.201413427562, offset_sec=2620.9187279151943`, file start
   17:43:20 + 2561.2s = 18:26:01.2, matching the two clicked points to sub-second precision). ✅
6. **Insert-in-place, chronological** — before: Event1=17:44:40(AI)/Event2=18:23:40(AI)/
   Event3=18:30:00(AI)/Event4=18:40:40(AI). After creating the new event at 18:26:01: it became
   **Event 3**, and the old Event3/Event4 correctly shifted to **Event4/Event5** — confirmed in the
   Event Panel list, and confirmed this survived a full page reload (re-opened the file from the
   Database screen; ordering and numbering were identical, proving it's derived server-side on every
   read, not a client-side artifact of the single session). ✅
7. **Person icon, no review controls** — new row shows the person icon (not "AI"), and its expanded
   state shows only Onset/Offset/Duration + Delete/Edit + Comment/Save — no Accept/Reject/Uncertain
   anywhere. ✅ (`CC_STEP6_SCREENSHOTS/item10_expanded_human_event.jpg`)
8. **Mini-timeline block** — a new solid blue block appeared at the matching position on the
   Detections row, visually distinct from the adjacent red-hatched (Reject) and amber (Uncertain) AI
   blocks; zoomed screenshot confirms the exact hex reads as Human blue, not AI charcoal.
   (`CC_STEP6_SCREENSHOTS/item8_minitimeline_human_block.png`) ✅
9. **Alert +1, both places, immediately** — Analysis header went `01 alerts to check` →
   `02 alerts to check` with no page reload. Navigated back to the Database screen: `chb13_03.edf`'s
   own row and the `chb13` subject row both read Alert `2` (up from `1`), confirmed via screenshot.
   (`CC_STEP6_SCREENSHOTS/item9_database_alert.jpg`) ✅
10. **Expand shows the right fields** — Onset/Offset/Duration, Delete, Edit, Comment textarea, Save
    button, explicit absence of Accept/Reject/Uncertain — confirmed live (not just a code read; this is
    `HumanExpand`'s first real exercise against a real Human event, as `BUILD_PROGRESS.md §11` flagged
    it would be). ✅
11. **Delete** — created a second, disposable test event (onset ~18:26:09, used for items 12/14 below),
    then deleted it: it disappeared from the list (count 6→5), Alert dropped back `03`→`02` in the
    header, its mini-timeline block disappeared. Verified against the DB directly (row gone). ✅
12. **Edit** — on that same disposable event, clicked Edit: expand panel swapped to the
    "Click two points on the EEG grid to redraw this event" hint, Delete/Edit buttons hidden, toolbar
    button became `Click onset…`. Drew two new points: the event's Onset/Offset/Duration updated in
    place (18:26:08→18:26:16 onset, 18:26:37→18:26:30 offset) with the same event id, count unchanged
    (6, not 7 — confirms this is an update, not an accidental second create). ✅
13. **Cancel mid-mark** — clicked `Select Range`, clicked once (onset marker appeared), clicked
    `Select Range` again: marker disappeared, button reverted, event count and Alert were unchanged
    (still 5 / `02`) — no partial event was created. ✅
14. **Direction-agnostic drag** — clicked a *later* point first, then an *earlier* point second
    (right-to-left). Resulting event was still `onset < offset` (DB: `onset_sec=2568.98…,
    offset_sec=2597.25…`, i.e. the earlier-clicked-second point became onset, the
    later-clicked-first point became offset) — confirmed both live in the UI and directly against the
    DB row. This was the same event later used for items 11/12 above before being deleted. ✅
15. **3-panel sync for a Human event** — clicked the persisted Event 3's row after deselecting: Panel
    EEG's window jumped to center it (with the usual pre-roll), the mini-timeline playhead moved to its
    position and the block gained the violet "selected" outline — identical behavior to clicking an AI
    event's row. ✅
16. **Guard tests + git status** — see below.

```
$ pytest web_demo/backend/tests/test_guards.py -v
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
collected 4 items

web_demo/backend/tests/test_guards.py::test_guard_no_build_timeline_masked PASSED [ 25%]
web_demo/backend/tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED [ 50%]
web_demo/backend/tests/test_guards.py::test_guard_no_labeled_npy PASSED  [ 75%]
web_demo/backend/tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED [100%]

============================== 4 passed in 2.85s ==============================

$ git status
On branch main
Your branch is ahead of 'origin/main' by 13 commits.
Changes not staged for commit:
	modified:   web_demo/BUILD_PROGRESS.md
	modified:   web_demo/DEMO_BUILD_HANDOFF.md
	modified:   web_demo/SZSCAN_DESIGN_v2.md
	modified:   web_demo/SZSCAN_SPEC_v5.md
	modified:   web_demo/backend/db.py
	modified:   web_demo/backend/main.py
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
	web_demo/CC_STEP5_FIX2_PROMPT.md  [... Step 5's own untracked fix-round files, unchanged ...]
	web_demo/CC_STEP5_REPORT.md
	web_demo/CC_STEP6_PROMPT.md
	web_demo/CC_STEP6_SCREENSHOTS/
	web_demo/frontend/src/components/MiniTimeline.jsx
	web_demo/frontend/src/components/PanelEvent.jsx
	web_demo/frontend/src/eventStyle.js
	web_demo/spec_docs_diff.md
```

`web_demo/backend/db.py`/`main.py` are the only backend files touched (Gap 1); `api.js`,
`EegPanel.jsx`, `AnalysisScreen.jsx`, `PanelEvent.jsx` are the frontend files touched. Nothing outside
`web_demo/` was written, matching the guard test's own confirmation.

## 7 · Test-state note (same convention as every prior step's report)

`chb13_03.edf`'s original 4 AI events are **unchanged**: Event1 (onset 80s/17:44:40) = Reject, Event2
(onset 2420s/18:23:40) = Reject, (now) Event4 (onset 2800s/18:30:00) = Uncertain, (now) Event5 (onset
3440s/18:40:40) = Reject — same review states as `BUILD_PROGRESS.md §8` recorded, just renumbered by
the new Human event's insertion (see §6 item 6).

One Human event was **left in place** as the fixture demonstrating this step's feature: **Event 3,
onset 18:26:01.2, offset 18:27:00.9** (DB `onset_sec=2561.201413427562`,
`offset_sec=2620.9187279151943`, id 76), comment empty, no review status. `chb13_03.edf`'s Alert now
reads **2** (was 1); subject `chb13`'s Alert now reads **2** (was 1) — `chb13_02.edf` still contributes
0.

A second, disposable Human event (created for the Delete/Edit/direction-agnostic-drag tests, items
11/12/14) was **deleted** before finishing — it does not appear in the final DB state (confirmed
directly: only ids 46-49 (AI) and 76 (Human) remain for this file).

Dev servers (backend on `:8000`, frontend on `:5173`) were left running for Boti to review live against
`UI/B3a-c` before the next step.

## 8 · Stop condition

Stopping here per the prompt. Step 7 (Channel Attribution) not started.
