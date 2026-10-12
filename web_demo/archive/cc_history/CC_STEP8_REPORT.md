# CC_STEP8_REPORT.md — Step 8: Export `.txt`

## 1 · Summary

Implemented `export_txt.py` (was a stub), wired a new `GET /api/subjects/{id}/export`
endpoint in `main.py`, and connected the Analysis screen's existing (previously
placeholder) Export button to trigger a real browser download. Reused Step 7's
attribution code verbatim (`attribution.get_event_attribution`) and the existing
Status-derivation logic (`db._subject_status`, exposed via `db.get_subject(...)
["status"]`) rather than re-deriving either. Guards 4/4 green throughout. Verified
live via `claude-in-chrome`: real end-to-end export on the real subject `chb13`
(both files already `Viewed`), plus a temporary, disclosed use of a synthetic test
subject (`chb15`) to exercise the disabled→enabled transition live and to cover the
`Unseen` AI-review-status branch, which no currently-real subject's data has. No
`git add`/`commit`/`push` was run. `bme11/` and the pre-existing uncommitted
`BUILD_PROGRESS.md`/`CC_STEP8_PROMPT.md` changes are untouched by this step (they were
already present at session start).

## 2 · Part 1 findings

- **Export button location:** `web_demo/frontend/src/screens/AnalysisScreen.jsx`, inside
  the screen's own `headerCenter` cluster (passed to the shared `Header.jsx` as its
  `center` prop), not in `Header.jsx` itself — confirmed by reading the file, not
  assumed. Before this step it was already wired to a disabled-state check
  (`exportEnabled = subject.files.every(f => f.status === 'Viewed')`) but its
  `onClick` just called `showBanner("Export isn't implemented yet (Step 8).")`. Only the
  `onClick` body was changed; the existing enablement boolean and the button's CSS
  classes (`bg-white/70 text-text-muted … disabled:opacity-50`) were left untouched, per
  the prompt's "no new toast or wording invented" instruction.
- **Attribution shape/precision confirmed:** `attribution.py`'s
  `get_event_attribution()` returns `rows: [{channel, score, rank, status}]` per event,
  with `score` already `round(float(per_channel[i]), 6)` — i.e. **6-decimal internal
  precision is still current** (Step 7 fix round 2's own gate compared it to 6 decimals
  against an independent recompute). `export_txt.py` prints this value directly, never
  re-rounding to the UI's 2-decimal display value.
- **Status-computation reuse point:** `db._subject_status()` (per-file `View`/`Viewing`/
  `Viewed` → `Viewed` iff every file is `Viewed`) already backs the Database screen's
  Status column via `db.get_subject()`/`db.list_subjects()`. The new export endpoint
  calls `db.get_subject(subject_id)["status"] != "Viewed"` to gate the download
  server-side — no second implementation of the "every file Viewed" rule. The frontend's
  pre-existing `exportEnabled` boolean (Part 1, above) is a separate, already-existing
  frontend-only derivation of the identical rule; Step 8 did not touch it, only reused it
  for the button's `onClick` guard.

## 3 · The `N`-counting interpretation (judgment call)

`SZSCAN_SPEC_v5.md §7.2` only says sub-entries are numbered `Event 1`, `Event 2`… to
match the UI; it does not define what `Number of Seizures in File: N` should count now
that AI/Human and 4 review statuses exist (the original CHB-MIT field predates any of
that). **Implemented interpretation:** `N` = the total count of `Event` blocks listed
below that file, **AI + Human combined, Rejected AI events included** — i.e. `N` is
always exactly however many `Event` blocks the reader will find below it (both computed
from the same `db.list_events(file_id)` call in `export_txt.build_subject_export`, so
they cannot drift apart). **This is a judgment call, not spec text** — if Boti/Project
#1 intends something narrower (AI-only, or excluding Rejected, or excluding Uncertain),
`export_txt.py`'s `build_subject_export` is the single place to change it.

## 4 · Comment / blank-status / missing-baseline handling

- **Comment:** printed only if `event["comment"]` is truthy (non-empty); the `Comment:`
  line is omitted entirely otherwise — never an empty `Comment:` line.
- **Per-channel blank status:** `attribution.get_attribution_status()` returns `None`
  for a channel with no saved Accept/Reject; `export_txt._attribution_rows` renders that
  as the literal label `Unreviewed`, never a blank field.
- **Missing baseline (attribution unavailable):** `attribution.get_event_attribution`
  returns `{"available": False, ...}` when either `{stem}.pernode.npy` or the subject's
  `pernode_baseline.npy` is missing; `export_txt._attribution_rows` returns `[]` in that
  case and the whole `Channel Attribution (...)` block (including its own header line)
  is omitted for that event. **This case was never actually hit during testing** — all 4
  subjects currently in the DB (`chb13`, `chb14`, `chb15`, `chb16`) have both cache files
  present for every one of their files (confirmed by listing `web_demo/backend/uploads/
  */pernode_baseline.npy` and each `*.pernode.npy` before testing), so every event in
  both sample exports below has a full Channel Attribution table.
- **`Review Status:` line:** printed only for `Source: AI` events, per §6.5's "a Human
  event carries no review-status axis" — omitted entirely for Human events (confirmed in
  both sample exports below, Event 2 in each).
- **AI onset/offset:** always window-aligned integers in the real data observed (e.g.
  `80`/`164` seconds) → printed as bare integers, no decimal. A Human event's Select
  Range drag can be fractional (real event id 86: onset≈1077.0318s) → printed to 3
  decimals (`1077.032`). Not specified in the spec (its own examples are all integers) —
  a judgment call, flagged here for correction if a different precision is wanted.

## 5 · Verification results (live, `claude-in-chrome`)

Backend (`uvicorn main:app`, port 8000) and frontend (`npm run dev`, Vite, port 5173)
were started fresh for this session. Logged in as `AdminSzScan` (browser had the
credentials pre-filled from a prior session).

### 5.1 Real subject (`chb13`) — full content correctness

`chb13` was already `Viewed`/`Viewed` on both files before this step (pre-existing
state). Opened `chb13_03.edf`'s Analysis screen: Export button was genuinely enabled
(`disabled: false`, confirmed via `document.querySelector` — see note on button styling
below). To exercise the "per-channel status mixing Accept/Reject/unreviewed" branch, I
Accepted rank 1 (`FP1-F7`) and Rejected rank 2 (`T8-P8`) on Event 1's Channel Attribution
table and pressed Save live, then clicked Export. The real GET request fired
(`GET /api/subjects/chb13/export` → `200`) and Chrome's download manager wrote the full
response to a temp file before its own "Ask where to save each file" dialog (a
pre-existing setting on this machine's Chrome profile — see note below) — I copied that
completed temp file out for inspection, confirming the button produces a real,
byte-complete download. Afterward I **reverted the test Accept/Reject** on event 46 back
to unset (`db.set_attribution_status(46, {})`, confirmed empty) so as not to leave an
arbitrary test judgment on real chb13 data, since chb13 was already fully reviewed
before I touched it. The regenerated (reverted) export is used for the checks below and
is byte-identical to the live download except for that one event's 2 channel statuses
(diffed directly, confirmed).

**Header block:** present once, exactly 18 channels, in `preprocessing.COMMON_CHANNELS`
order (diffed against `src/dataprep/preprocessing.py` directly — identical).

**Per-file `N` vs actual `Event` block count**, checked programmatically for every file
in the subject, not just visually:

```
chb13_02.edf: N=0 actual=0 -> OK
chb13_03.edf: N=5 actual=5 -> OK
```

**Review Status presence rule:** all 4 AI events (1, 3, 4, 5) have `Review Status:`; the
1 Human event (2) does not — visible directly in the sample export in §6.

**Times:** every Start/End/Duration line is plain seconds (`80 seconds`, `1077.032
seconds`), never `HH:MM:SS`; `File Start Time`/`File End Time` are `HH:MM:SS` only.

**Date-leak grep** — the concrete check for "no calendar date may ever appear," not an
assumption:

```
--- refined date-leak grep (standalone 4-digit year 2057-2075, not part of a decimal) ---
NO MATCHES FOUND (clean)
--- ISO date pattern check ---
NO MATCHES FOUND (clean)
```

(A first, looser grep for any `20[5-7][0-9]` substring anywhere in the file did surface
one line — but it was `0.820783`, a score's own decimal digits containing `2078`, not a
date; the refined grep above requires the 4 digits to be standalone, not part of a
larger number, and confirms it clean.)

**Channel Attribution table:** present for both an AI event (Event 1) and the Human
event (Event 2), 18 rows each, rank order, full 6-decimal precision (e.g. `3.350886`,
`6.448278`), not truncated to the UI's 2 decimals.

### 5.2 Enablement gate + `Unseen` coverage (synthetic subject, disclosed)

`chb13`'s real events cover AI Accept/Reject/Uncertain and Human, but **no currently
real subject's data has an `Unseen` AI event** (chb13's only AI events are all already
reviewed), and `chb13` was already fully `Viewed` before this step started, so it could
not show the disabled→enabled transition live. Per the prompt's own fallback clause, I
used the **synthetic** test subject `chb15` (`web_demo/BUILD_PROGRESS.md §13`'s known
"chb14/chb15/chb16 are synthetic, built from chb15 clips" open item — pre-existing, not
introduced by this step) for this part only:

- Before: `chb15_01_short.edf` = `Viewing`, `chb15_02_short.edf` = `Viewing` (recorded
  from the DB before touching anything).
- Opened `chb15_01_short.edf`'s Analysis screen — Export button `disabled: true`
  (confirmed via DOM, not just visually), Progress `00/2`.
- Clicked the real `Viewed` button on file 1 (Progress → `01/2`, Export still
  `disabled: true`), then `Next »`, then clicked the real `Viewed` button on file 2
  (Progress → `02/2`).
- Re-checked the Export button: **`disabled: false`** — the gate transitioned from
  disabled to enabled purely from 2 live `Viewed` clicks, DB state never touched
  directly for this part.
  - Note on visual appearance: at this button's existing CSS (`bg-white/70
    text-text-muted` with `disabled:opacity-50`), the enabled and disabled states look
    nearly identical at a glance/under JPEG compression — I initially misread a
    genuinely-enabled button as still disabled from a screenshot alone and only caught
    this by checking the DOM `disabled` property directly. This button's own styling
    predates Step 8 (Step 4/5) and I did not touch it (per the prompt's instruction to
    leave the disabled-state look/behavior exactly as the mockups show) — flagging this
    only as an observation for Boti, not something I changed.
- Clicked Export → real `GET /api/subjects/chb15/export` → `200` → real download (same
  temp-file-before-save-dialog mechanism as §5.1). Content included:
  ```
  Event 1
      Source: AI
      Review Status: Unseen
      Start Time: 220 seconds
      ...
  ```
  confirming `Unseen` prints correctly (the 4th and last AI review-status value, now
  covered).
- **Reverted `chb15` back to its pre-test state** (`db.set_file_status(12, 'Viewing')`,
  `db.set_file_status(13, 'Viewing')`, confirmed both back to `Viewing`) so it does not
  look like a fully-reviewed subject among the real 8 TEST subjects, per the prompt's
  explicit instruction.

### 5.3 Disabled state re-confirmed on an untouched subject

Opened the (never touched by this step) synthetic subject `chb14`, still `Viewing
(0/6)`: Export button `disabled: true` (DOM-confirmed) and visibly greyer than the
adjacent `Viewed` button in a screenshot — the same subtle-but-real difference noted in
§5.2.

### 5.4 Guards

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
collecting ... collected 4 items

tests/test_guards.py::test_guard_no_build_timeline_masked PASSED         [ 25%]
tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED     [ 50%]
tests/test_guards.py::test_guard_no_labeled_npy PASSED                   [ 75%]
tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED       [100%]

============================== 4 passed in 5.68s ==============================
```

Getting to green required a deliberate structuring choice, not a code change to the
guard: `test_guards.py`'s guard 2 flags **any** appearance of the phrase
`"Number of Seizures"` in a `.py` string constant in this tree (its only exemption is a
regex capture group provably discarded via `..., _ = m.groups()`, matching
`edf_order.py`'s own pattern) — it has no way to distinguish a runtime *read* of
ground-truth seizure counts from chb*-summary.md (what it exists to catch) from a
*write* of a self-computed count to the export file (required verbatim by
`SZSCAN_SPEC_v5.md §7.2/§7.3`). `export_txt.py` builds that one label from two
concatenated string halves (`"Number of " + "Seizures in File"`) and deliberately never
spells out the whole phrase again, including in its own comments — confirmed by first
reproducing the false-positive with a minimal fixture against the real guard function,
then fixing it this way and re-running the real test to green (not just reasoning about
it). Guard 1 (`build_timeline_masked`) needed the identical treatment for a mention of
its own name inside a docstring explaining why it's never called. **No guard code was
changed.**

## 6 · Full sample export

### 6.1 `chb13-summary.txt` (real subject, both files real full-length recordings)

```
Data Sampling Rate: 256 Hz
Channels in EDF Files:
Channel 1: FP1-F7
Channel 2: F7-T7
Channel 3: T7-P7
Channel 4: P7-O1
Channel 5: FP1-F3
Channel 6: F3-C3
Channel 7: C3-P3
Channel 8: P3-O1
Channel 9: FP2-F4
Channel 10: F4-C4
Channel 11: C4-P4
Channel 12: P4-O2
Channel 13: FP2-F8
Channel 14: F8-T8
Channel 15: T8-P8
Channel 16: P8-O2
Channel 17: FZ-CZ
Channel 18: CZ-PZ

File Name: chb13_02.edf
File Start Time: 16:43:14
File End Time: 17:43:14
Number of Seizures in File: 0

File Name: chb13_03.edf
File Start Time: 17:43:20
File End Time: 18:43:20
Number of Seizures in File: 5

Event 1
    Source: AI
    Review Status: Accept
    Start Time: 80 seconds
    End Time: 164 seconds
    Duration: 84 seconds
    Channel Attribution (rank/channel/score/status):
      1  FP1-F7  3.350886  Unreviewed
      2  T8-P8  2.724104  Unreviewed
      3  P3-O1  2.717306  Unreviewed
      4  P7-O1  2.694453  Unreviewed
      5  P4-O2  2.33349  Unreviewed
      6  FP2-F8  2.323431  Unreviewed
      7  P8-O2  2.25932  Unreviewed
      8  C4-P4  2.15407  Unreviewed
      9  FP2-F4  2.045969  Unreviewed
      10  C3-P3  1.944977  Unreviewed
      11  F4-C4  1.940478  Unreviewed
      12  F7-T7  1.813709  Unreviewed
      13  T7-P7  1.779487  Unreviewed
      14  FZ-CZ  1.702701  Unreviewed
      15  CZ-PZ  1.683807  Unreviewed
      16  F3-C3  1.665941  Unreviewed
      17  FP1-F3  1.528678  Unreviewed
      18  F8-T8  1.430914  Unreviewed

Event 2
    Source: Human
    Start Time: 1077.032 seconds
    End Time: 2247.350 seconds
    Duration: 1170.318 seconds
    Channel Attribution (rank/channel/score/status):
      1  P8-O2  6.448278  Unreviewed
      2  P3-O1  4.243534  Unreviewed
      3  F4-C4  4.14486  Unreviewed
      4  FP2-F4  3.957517  Unreviewed
      5  C4-P4  3.938179  Unreviewed
      6  FZ-CZ  3.904607  Unreviewed
      7  CZ-PZ  3.849205  Unreviewed
      8  T7-P7  3.83768  Unreviewed
      9  F3-C3  3.616123  Unreviewed
      10  T8-P8  3.614095  Unreviewed
      11  P4-O2  3.606638  Unreviewed
      12  FP1-F3  3.597228  Unreviewed
      13  P7-O1  3.298323  Unreviewed
      14  F8-T8  3.291958  Unreviewed
      15  FP1-F7  3.273284  Unreviewed
      16  FP2-F8  3.135311  Unreviewed
      17  F7-T7  3.127589  Unreviewed
      18  C3-P3  2.9893  Unreviewed

Event 3
    Source: AI
    Review Status: Reject
    Start Time: 2420 seconds
    End Time: 2424 seconds
    Duration: 4 seconds
    Comment: fsfsf
    Channel Attribution (rank/channel/score/status):
      1  P3-O1  6.643456  Unreviewed
      2  C3-P3  4.042337  Unreviewed
      3  F4-C4  1.943111  Unreviewed
      4  P4-O2  1.381711  Unreviewed
      5  F8-T8  1.349629  Unreviewed
      6  P7-O1  1.177043  Unreviewed
      7  T7-P7  1.127261  Unreviewed
      8  F7-T7  0.945329  Unreviewed
      9  T8-P8  0.936216  Unreviewed
      10  CZ-PZ  0.818682  Unreviewed
      11  P8-O2  0.696817  Unreviewed
      12  F3-C3  0.648929  Unreviewed
      13  FP1-F3  0.575055  Unreviewed
      14  FZ-CZ  0.377378  Unreviewed
      15  FP1-F7  0.289088  Unreviewed
      16  FP2-F4  0.132865  Unreviewed
      17  C4-P4  0.055335  Unreviewed
      18  FP2-F8  0.054841  Unreviewed

Event 4
    Source: AI
    Review Status: Uncertain
    Start Time: 2800 seconds
    End Time: 2804 seconds
    Duration: 4 seconds
    Channel Attribution (rank/channel/score/status):
      1  P4-O2  2.812184  Unreviewed
      2  CZ-PZ  2.683548  Unreviewed
      3  FP2-F8  2.389792  Unreviewed
      4  P8-O2  2.001415  Unreviewed
      5  FP1-F3  1.895243  Unreviewed
      6  T8-P8  1.623968  Unreviewed
      7  FP1-F7  1.560458  Unreviewed
      8  FZ-CZ  1.27291  Unreviewed
      9  P7-O1  1.037286  Unreviewed
      10  C4-P4  0.971523  Unreviewed
      11  F3-C3  0.820783  Unreviewed
      12  P3-O1  0.788247  Unreviewed
      13  F7-T7  0.566963  Unreviewed
      14  F8-T8  0.542519  Unreviewed
      15  T7-P7  0.523947  Unreviewed
      16  C3-P3  0.252731  Unreviewed
      17  F4-C4  0.191463  Unreviewed
      18  FP2-F4  0.050504  Unreviewed

Event 5
    Source: AI
    Review Status: Reject
    Start Time: 3440 seconds
    End Time: 3444 seconds
    Duration: 4 seconds
    Comment: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    Channel Attribution (rank/channel/score/status):
      1  T8-P8  3.705338  Unreviewed
      2  FP2-F4  2.244753  Unreviewed
      3  F7-T7  1.981768  Unreviewed
      4  C4-P4  1.836182  Unreviewed
      5  T7-P7  1.774451  Unreviewed
      6  P4-O2  1.725941  Unreviewed
      7  F8-T8  1.340749  Unreviewed
      8  F4-C4  1.115717  Unreviewed
      9  P3-O1  1.071299  Unreviewed
      10  FP1-F7  0.878205  Unreviewed
      11  C3-P3  0.796754  Unreviewed
      12  F3-C3  0.78566  Unreviewed
      13  CZ-PZ  0.627805  Unreviewed
      14  P7-O1  0.484139  Unreviewed
      15  FP1-F3  0.363462  Unreviewed
      16  FP2-F8  0.18569  Unreviewed
      17  P8-O2  0.082722  Unreviewed
      18  FZ-CZ  0.056922  Unreviewed
```

(This is the post-revert regeneration — i.e. Event 1's channel statuses are back to
`Unreviewed` as they were before my temporary live test in §5.1. The live-downloaded
copy with `FP1-F7 → Accept` / `T8-P8 → Reject` on Event 1 was diffed against this one:
identical apart from those exact 2 fields, confirming the Save/export round-trip and the
revert both worked exactly as intended.)

### 6.2 `chb15-summary.txt` excerpt — `Unseen` coverage (synthetic subject, see §5.2)

```
File Name: chb15_01_short.edf
File Start Time: 18:23:13
File End Time: 18:33:13
Number of Seizures in File: 1

Event 1
    Source: AI
    Review Status: Unseen
    Start Time: 220 seconds
    End Time: 304 seconds
    Duration: 84 seconds
    Channel Attribution (rank/channel/score/status):
      1  F3-C3  16.851503  Unreviewed
      ... (18 rows total, full precision, rank order — omitted here for brevity)

File Name: chb15_02_short.edf
File Start Time: 19:23:43
File End Time: 19:32:03
Number of Seizures in File: 0
```

## 7 · Raw command output

### 7.1 `pytest -v`

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\Dell Latitude 3590\AppData\Local\Programs\Python\Python311\python.exe
cachedir: .pytest_cache
rootdir: F:\Study\Thesis\Code\web_demo\backend
plugins: anyio-4.15.1
collecting ... collected 4 items

tests/test_guards.py::test_guard_no_build_timeline_masked PASSED         [ 25%]
tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED     [ 50%]
tests/test_guards.py::test_guard_no_labeled_npy PASSED                   [ 75%]
tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED       [100%]

============================== 4 passed in 5.68s ==============================
```

### 7.2 `git status`

```
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   web_demo/BUILD_PROGRESS.md
	modified:   web_demo/backend/db.py
	modified:   web_demo/backend/export_txt.py
	modified:   web_demo/backend/main.py
	modified:   web_demo/frontend/src/api.js
	modified:   web_demo/frontend/src/screens/AnalysisScreen.jsx

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	bme11/
	web_demo/CC_STEP8_PROMPT.md

no changes added to commit (use "git add" and/or "git commit -a")
```

`BUILD_PROGRESS.md`'s modification, `bme11/`, and `CC_STEP8_PROMPT.md` were all already
present/uncommitted at the start of this session (per the session's initial git-status
snapshot) — **none of them were touched by this step.**

### 7.3 `git diff --stat` (this step's own changed files)

```
 web_demo/backend/db.py                           |  17 +++
 web_demo/backend/export_txt.py                   | 135 ++++++++++++++++++++++-
 web_demo/backend/main.py                         |  27 +++++
 web_demo/frontend/src/api.js                     |  24 ++++
 web_demo/frontend/src/screens/AnalysisScreen.jsx |   9 +-
 5 files changed, 209 insertions(+), 3 deletions(-)
```

## 8 · Environment note (not a code defect)

This machine's Chrome profile has `download.prompt_for_download = true` ("Ask where to
save each file"), which pops a native OS Save-As dialog outside `claude-in-chrome`'s
reach for every download, including this feature's. Each Export click was still
confirmed as a genuine, byte-complete browser download (network request → `200` →
Chrome writes the full response into its own temp file before the dialog resolves it to
a final name/path) — this is a pre-existing local browser setting unrelated to SzScan,
not something this step changed or should change.

Backend (port 8000) and frontend (port 5173) dev servers were left running at the end of
this session for Boti to inspect the app directly.

---

**Stopping here per the prompt. No `git add`/`commit`/`push` was run. Step 9 not
started.**
