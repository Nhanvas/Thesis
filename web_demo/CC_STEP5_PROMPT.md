# CC_STEP5_PROMPT.md — Step 5: Mini-timeline + Panel Event + 3-panel sync

**Prerequisite:** Step 4 is fully closed (`web_demo/CC_STEP4_REPORT.md` + `CC_STEP4_FIX_REPORT.md`,
addenda included). Confirm `pytest web_demo/backend/tests/test_guards.py -v` is green before doing
anything else, and confirm `chb13`/`chb16` are back at a clean `View` state (they were reset at the
end of the Step 4 fix round).

Read in this order before writing any code:
1. `web_demo/SZSCAN_SPEC_v5.md` §6.3 (mini-timeline) and §6.5 (Panel Event) — in full.
2. `web_demo/SZSCAN_DESIGN_v2.md` §2 (the three independent color axes: source / review-status /
   interaction) and §8 (wording lookup table) — in full. §2's combination rule matters most: three axes
   always show simultaneously, none ever overwrites another (e.g. an Accepted event that is also the
   currently-selected event keeps its green status bar **and** gains a violet selection border — the
   border is additive, not a replacement).
3. View the mockups (copy to scratch first): `UI/B2a*.png`–`UI/B2d*.png`.

**Wording flag, read before building the mini-timeline's second row:** `SZSCAN_DESIGN_v2.md §8` states
the row must be labeled **`Detections`**, explicitly not `Seizure Detections` — this is a deliberate
anti-overclaiming rule, not a styling choice, and it exists precisely because a static mockup PNG can't
itself carry this kind of semantic distinction. If `UI/B2a`/`B2d` show `Seizure Detections` as literal
pixel text, that is the mockup lagging the wording table, not the wording table being wrong — follow
§8 for this specific label and flag the discrepancy in your report rather than silently copying the
mockup's text. (Row 1, `Seizure Detection Score`, is explicitly allowed to keep "Seizure" per
`SZSCAN_SPEC_v5.md §7.2` — only row 2 is affected.)

## Data source — nothing new to compute

The AI-detected events for the existing test subjects were already computed and stored during Step 3's
Process step (SPEC §5.5 stage 2). This step is a **read/display/review UI** on top of that existing
data — it does not call `cpd_pipeline_v14`, `pipeline_demo.process_subject`, or anything in the
detection path again. If an existing subject's events are missing or look wrong in the DB, stop and say
so rather than re-running detection to "fix" it.

## Scope boundary

**In scope:**
- **Mini-timeline** (SPEC §6.3): scoped to the **currently-open file only**, not the whole subject.
  Default 1-hour view, 6 columns of 10 min each. Two rows:
  - `Seizure Detection Score` — line chart of the file's ensemble score. Y-axis shows **no numbers**,
    just a zero-line and relative height, auto-scaled to the current file's own P1-P99 percentile (not
    a fixed scale, not shared across files).
  - `Detections` — rectangular blocks sized to each event's duration, colored per the three-axis rules
    in DESIGN §2 (source/status/interaction, never conflated).
  - A playhead (▼) synced one-way from Panel EEG (scrubbing/clicking Panel EEG moves the mini-timeline's
    playhead). The mini-timeline itself is **view-only** — clicking on it must do nothing; only Panel
    EEG is interactive, per spec.
- **Panel Event** (SPEC §6.5): two-tier filter — tier 1 `All / Human / AI`, tier 2 (only when `AI` is
  selected) `Accept / Reject / Uncertain / Unseen`. Count format is `x` for All/Human, `x/y` for an AI
  sub-filter (x = matches, y = total AI events in file). Each row: event name, onset, type icon
  (AI vs. person), expand arrow. Expanding an **AI** event shows read-only Onset/Offset/Duration plus
  Accept/Reject/Uncertain (mutually exclusive) + Comment + Save. Expanding a **Human** event shows
  Onset/Offset/Duration + Delete/Edit + Comment + Save, no Accept/Reject/Uncertain. **Note:** no Human
  event can exist yet (Select Range is Step 6) — implement both UI paths per spec since the data model
  should already support it, but you won't be able to test the Human-event path live this step; say so
  plainly rather than fabricating one to test with.
- **3-panel sync, Panel Event is the primary control source** (SPEC's own wording): clicking an event
  row jumps Panel EEG to that event's onset→offset **and** updates the mini-timeline's playhead.
- **Dimming rule** (DESIGN §2): once an event is selected/being viewed, all other events in both the
  mini-timeline and the Event Time row drop to ~40% opacity (color unchanged) — the selected one stays
  full-strength with its violet border.
- Saving an Accept/Reject/Uncertain change must update the file's Alert count live (SPEC §5.3 formula:
  AI events not-yet-Rejected + user-added events), reflected in both the Analysis header and the
  Database screen afterward.
- Empty state for a file with zero AI events: `No detected events in this file. You can still add an
  event manually with Select Range.` — even though Select Range isn't wired up yet.

**Out of scope, still:** Select Range's actual event-creation behavior (Step 6), Channel Attribution
panel (Step 7), Export (Step 8). Don't touch Panel EEG/toolbar internals from Step 4 except what's
strictly needed to wire the sync.

## Standing rules (apply as always)

- No fake data, no invented events — everything rendered must come from what Step 3 actually stored.
- Use `claude-in-chrome` from the start, not reactively.
- If a mockup and a written doc disagree on something other than the wording-table case flagged above,
  stop and say so rather than silently picking one.
- Nothing this step should touch anything outside `web_demo/` — after the Step 4 incident, treat that as
  a standing reminder, not a one-off.

## Verification required before writing your report

1. Open a file with real stored events (e.g. `chb13_03` or `chb06`) — mini-timeline renders the score
   line + correctly colored/sized Detections blocks matching the stored events.
2. Confirm the score row's Y-axis shows no numbers, just a zero-line, and that it auto-scales per-file
   (compare two files with different score ranges).
3. Confirm the mini-timeline is not clickable (nothing happens on click) and that its playhead follows
   Panel EEG's scrubbing.
4. Panel Event: two-tier filter and count format (`x` vs `x/y`) both correct.
5. Click an event row → confirm both Panel EEG (jumps to onset→offset) and the mini-timeline playhead
   update together.
6. Expand an AI event, change its status, Save → confirm the Alert count updates in the header, and
   separately on the Database screen afterward.
7. Confirm the dimming rule: with one event selected, verify (via computed style, not just eyeballing)
   that other events are at ~40% opacity and the selected one is not.
8. Confirm the literal row-2 label reads `Detections`, not `Seizure Detections`.
9. Empty-state wording exact-match check, on a file with zero events if one of the 5 existing subjects
   has one — note if none do.
10. `pytest web_demo/backend/tests/test_guards.py -v` and `git status` — raw output.

Write your report to `web_demo/CC_STEP5_REPORT.md`.

## Stop condition

Do not start Step 6 (Select Range). Stop once the mini-timeline and Panel Event both render real stored
data, the 3-panel sync and dimming rule work, the wording checks pass, and the report is written.
