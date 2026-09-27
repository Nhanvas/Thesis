# CC_STEP9_CHB13_COMPLETE_PROMPT.md — complete `chb13` to its full real file set

**Context:** `chb13` currently has only 2 of its 33 real files in the DB — built early, in Step 3,
before Step 9 decided every subject should carry its full real file set. All other 7 allowlisted
subjects now have 100% of their real files. This closes that last remaining gap so the DB is
uniformly "every subject, full real file set" — a prerequisite `STEP8_9_PREDEFENSE_CHECKLIST.md §2`
will require anyway for the eventual Tier 2 run.

Read first: `BUILD_PROGRESS.md` §14/§15 (open items, Step 9's method), `SZSCAN_SPEC_v5.md` §5.5 (no
Edit mode — delete + recreate is the only way to change a subject), `CC_STEP9_PHASE2_PROMPT.md` (same
upload method to reuse).

Guards unchanged: `pytest web_demo/backend/tests/test_guards.py -v` must stay 4/4. No write outside
`web_demo/`. **No `git add`/`commit`/`push` — not even automatically via any tool/auto-mode default.**
If anything in your environment would normally run git commands on its own, suppress it for this
session; confirm in the report that nothing was committed.

## 1 · Before deleting anything — acknowledge what's being lost

`chb13` currently carries hand-built test state from Steps 5-8 (`BUILD_PROGRESS.md` §8.6, §9.5,
§10.4): AI event review statuses (Accept/Reject/Uncertain/Unseen), 5 Human events, per-channel
attribution Accept/Reject on at least one event, and one still-unexplained Human event (id 86,
§10.4). Deleting `chb13` destroys all of this — that's the intended outcome (fresh, full, untouched
data replacing partial test data), not an accident, but it is not recoverable once deleted. In the
final report, state plainly that this was deleted and that it closes `BUILD_PROGRESS.md` §10.4's open
item as **moot, not resolved** — the event's origin was never actually determined, it's just gone now
along with everything else.

## 2 · Delete and clean up

1. Delete the `chb13` subject via the app's real Delete flow (removes the DB rows).
2. The `DELETE` endpoint does not clean up `uploads/{subject_id}/` on disk (known gap,
   `BUILD_PROGRESS.md` §14) — manually remove `uploads/chb13/` afterward so no stale cache confuses
   the fresh upload.

## 3 · Upload + process, full real file set

Same method as `CC_STEP9_PHASE2_PROMPT.md` §3 — the real HTTP flow (login, sequential file POSTs,
Process, poll `GET /api/uploads/current`), not `claude-in-chrome` (real EDF sizes are far above its
10 MB combined-attachment cap). `project_id` = `chb13`; memo =
`"Step 9 completion - full real dataset"`. Upload all 33 real files from
`F:/Study/Thesis/Dataset/CHB-MIT/chb13/`, sequentially, then Process. Confirm the real file count on
disk is 33 before starting — don't proceed on a silent mismatch.

## 4 · Verify

1. Subject appears in the Database table, Status `View`, 33 files, duration ~33.00 h.
2. `pytest web_demo/backend/tests/test_guards.py -v` — 4/4.
3. `GET /api/subjects` still lists exactly the 8-subject allowlist, no more, no fewer, no synthetic
   subject.

## Report

Write `web_demo/CC_STEP9_CHB13_COMPLETE_REPORT.md`: confirmation that the old event/review/Human-
event/attribution-status data is gone, real timing (Phase A+B, Process/PELT — worth recording for
completeness even though `chb13` was never an O4 candidate), raw `pytest -v`, `git status`.

Then **stop. Do not run `git add`/`commit`/`push`.**
