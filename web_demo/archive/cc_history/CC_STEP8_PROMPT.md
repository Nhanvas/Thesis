# CC_STEP8_PROMPT.md — Step 8: Export `.txt`

Read first: `web_demo/CLAUDE.md`, `web_demo/SZSCAN_SPEC_v5.md` §6.1 (Export button rule) and §7 in full
(scope, wording rule, exact structure), `web_demo/BUILD_PROGRESS.md` §10 (Step 7 — what the attribution
endpoint already returns), `UI/` for how the Export button appears (grey/disabled state).

This is `DEMO_BUILD_HANDOFF.md §6` row 8. `export_txt.py` currently exists only as a stub — this step
fills it in and wires it to the UI.

Guards that still apply: 4/4 green at the end, no `git add/commit/push`, no write outside `web_demo/`.
Export code must not read the seizure fields from `chb*-summary.md`, must not call
`build_timeline_masked`, must not load `{subj}_interictal.npy`/`{subj}_ictal.npy` — it only reads what's
already in the DB (events, attribution_status) and the already-cached per-subject arrays (`.pernode.npy`,
`pernode_baseline.npy`) via the existing `attribution.py` functions. Don't re-derive attribution scoring
logic a second time — call into the Step 7 code, don't duplicate it.

**Two new hard rules for this step, on top of the four guards:**
- **No calendar date may ever appear in the exported file.** `File Start Time`/`File End Time` come from
  `meas_date`'s clock-time portion only (`HH:MM:SS`), the same source already used for "Recording N,
  HH:MM:SS" elsewhere (C17) — never the date/year part (CHB-MIT's shifted year, ~2057–2075, must never
  leak into an exported file any more than it leaks into the UI).
- **`Number of Seizures in File: N` and `File Start/End Time` must be self-consistent with what actually
  follows them** — see Part 2 below for exactly what N counts.

---

## Part 1 — Locate the pieces already there

Before writing anything, confirm and report:
- Where the Export button currently renders (which `.jsx` file — likely inside `AnalysisScreen.jsx`'s own
  header cluster, not the shared `Header.jsx`; confirm rather than assume) and its current disabled/grey
  state.
- The exact shape `attribution.py`'s endpoint already returns for one event (rank/channel/score/status),
  and its internal rounding (the fix2 report noted 6 decimals — confirm this is still true).
- Where per-subject "all files Viewed" status is already computed (§5.2's file/subject Status rules —
  this logic should already exist for the Database screen's Status column; reuse it, don't recompute a
  second version).

## Part 2 — `export_txt.py`

Build the subject-level `.txt` exactly per `SZSCAN_SPEC_v5.md §7.3`'s structure, in **file-name order**
(the original CHB-MIT convention — not the `meas_date` "Recording N" display order used elsewhere).

**Header (once, subject-level):**
```
Data Sampling Rate: 256 Hz
Channels in EDF Files:
Channel 1: FP1-F7
...
Channel 18: CZ-PZ
```
Read the sample rate and the 18-channel list from `preprocessing.FS`/`preprocessing.COMMON_CHANNELS`
(read-only import — do not hardcode a second copy that could drift from the real pipeline).

**Per file:**
```
File Name: chb06_06.edf
File Start Time: 15:10:23
File End Time: 16:10:23
Number of Seizures in File: N
```
- `File Start Time`/`File End Time`: clock time only, from `meas_date`, no date. `File End Time` =
  start + duration.
- `N` = **the total count of Event entries listed below this file** (AI + Human combined) — i.e. N
  always equals exactly how many `Event` blocks follow. This is a judgment call, not explicit in the
  spec (the field is named "Seizures" but the spec only says sub-entries are numbered to match the UI) —
  **state this interpretation plainly in the report** so Boti/Project #1 can correct it if the field is
  meant to mean something narrower (e.g. AI-only, or excluding Rejected).

**Per event**, in onset order (the same order that produces `Event N` numbering on the UI — reuse that
existing derivation, don't recompute a separate order):
```
Event N
    Source: AI
    Review Status: Accept
    Start Time: 1230 seconds
    End Time: 1265 seconds
    Duration: 35 seconds
    Comment: (only if non-empty — omit the whole line if there is no comment)
    Channel Attribution (rank/channel/score/status):
      1  FP1-F7  3.350886  Accept
      2  T8-P8   2.724104  Reject
      ...
```
- `Review Status:` line appears **only for `Source: AI`** — a Human event has no review-status axis
  (§6.5) and this line is omitted entirely for it, matching the spec's own Event-2/Human example.
- Start/End Time in **seconds from the start of the file** (not `HH:MM:SS`) — read directly from the
  stored `onset_sec`/`offset_sec`, no conversion.
- Comment: print the real text if the event has one; **omit the `Comment:` line entirely if empty** — do
  not print an empty field.
- Channel Attribution: call the existing attribution logic (same function `attribution.py`'s endpoint
  uses) for **every** event, AI or Human — §6.7 already establishes attribution works for user-created
  events too. Print all 18 rows, rank order, using the score's existing internal precision (do not
  re-round to the UI's 2 decimals — this is a technical file for further processing, per the spec's own
  §7.3 closing line). Per-channel Status: `Accept`/`Reject` if saved, or a clear `Unreviewed` label if not
  — don't leave it blank.
- If a subject's baseline file is missing (attribution unavailable): omit the Channel Attribution block
  for that event's entries and note in the report if this case was ever actually hit during testing (it
  shouldn't be, for the 4 subjects currently in the DB).

## Part 3 — Wiring

- Backend: an export endpoint (e.g. `GET /api/subjects/{id}/export`) that calls `export_txt.py` and
  returns the `.txt` for download. Suggested filename `{subject_id}-summary.txt`, matching the original
  CHB-MIT naming — confirm this is reasonable, don't invent something stranger.
- Frontend: wire the existing Export button (wherever Part 1 found it) to call this endpoint and trigger
  a real browser download. **Enablement rule (§6.1): only enabled once every file of the subject is
  `Viewed`** — reuse the existing Status computation (Part 1), don't write a second one. When disabled,
  it should look and behave exactly as the locked mockups show (grey, non-interactive) — no new toast or
  wording invented for this state unless the mockup shows one.

## Part 4 — Verification (live, `claude-in-chrome`)

- Pick a subject/file with a genuine mix to exercise every branch: at least one AI event per review
  status (Accept/Reject/Uncertain/Unseen), at least one Human event, at least one event with a Comment
  and one without, and per-channel attribution status mixing Accept/Reject/unreviewed. If no currently
  real subject has enough variety, it's fine to temporarily mark a **synthetic** test subject's files as
  Viewed to exercise the enablement gate and the full export end-to-end — say plainly if you did this,
  and don't leave that subject's state looking like it belongs among the real 8 TEST subjects (per the
  standing rule that synthetic subjects must be removed before any real demo run).
- Confirm the button is disabled/non-functional until every file is genuinely `Viewed` (click the real
  `Viewed` button live, don't fake the DB state) — then confirm it becomes enabled and produces a real
  download.
- Open the downloaded file and check, concretely, not by eye alone:
  - Header block present once, exactly 18 channels, matches `preprocessing.COMMON_CHANNELS` order.
  - Every file block's `Number of Seizures in File: N` equals the count of `Event` blocks that follow it
    — check this programmatically for every file in the test subject, not just visually for one.
  - Every AI event has `Review Status:`; every Human event does not.
  - Times are plain seconds, never `HH:MM:SS`, never a date.
  - **grep the whole file for any 4-digit year matching CHB-MIT's shifted range (2057–2075) or any
    other date-shaped string** — must find nothing. This is the concrete check for the "no calendar
    date" rule above, not just an assumption that HH:MM:SS-only formatting makes it safe.
  - Channel Attribution table present for both an AI and a Human event, 18 rows, rank order, scores at
    full existing precision (not 2-decimal-truncated).
- `pytest web_demo/backend/tests/test_guards.py -v` → 4/4, raw output.

---

## Report

Write `web_demo/CC_STEP8_REPORT.md`: 1 summary; 2 Part 1 findings (button location, attribution
precision confirmed, Status-computation reuse point); 3 the `N`-counting interpretation, stated plainly
as a judgment call; 4 the Comment/blank-status/missing-baseline handling actually implemented; 5 full
verification results incl. the per-file N-vs-Event-count check and the date-leak grep, both with actual
output shown, not just "passed"; 6 a full sample export (at least one real subject) pasted into the
report or attached as a file for Boti to read directly; 7 raw `pytest -v`, `git status`, `git diff
--stat`. Then **stop. Do not run git add/commit/push. Do not start Step 9.**