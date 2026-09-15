# CC_STEP3_FIX3_PROMPT.md — Step 3 fix round 3: unlock Project ID / Memo until PROCESS

**Context:** Rounds 1–2 (panel auto-close, overlay layout, PROCESS gating) are all confirmed fixed and
verified live — do not re-touch that work unless this round's change genuinely requires it, and explain
why if so.

**This round is a deliberate UX decision change from the author, not a bug fix.** The original Step 3
build made Project ID and Memo read-only once the first file starts uploading. The author has decided
against this: **both fields must stay editable for the entire time the Create New panel is open**, right
up until PROCESS is clicked. Only clicking PROCESS finalizes/locks anything.

## Required behavior

1. **Project ID and Memo inputs are editable at all times** the panel is open — before any file is
   added, while files are uploading, while Phase A/B is running in the background, all of it. Remove
   whatever read-only/disabled condition currently ties these fields to upload or session state.

2. **The 8-subject allowlist check's point of final authority moves to the moment PROCESS is clicked.**
   Read whatever Project ID value is actually in the field at that instant, validate it against the
   allowlist (`chb03/06/13/14/15/16/17/18`), and only proceed to Phase B-wait/PELT/DB-write if valid. If
   invalid, show the existing toast (`This demo is restricted to the held-out test subjects.`) and do
   **not** start processing — panel stays open, user fixes the ID and clicks PROCESS again.

3. **Investigate what currently depends on Project ID being fixed/known at upload time** — e.g. the
   upload storage path (`backend/uploads/{project_id}/` or similar), any early allowlist check gating
   file acceptance, anything keying the session by the literal Project ID string. Since the ID can now
   change after files are already uploaded, decide how to handle this:
   - An early, non-blocking allowlist check at upload time can stay as a UX nicety (immediate feedback
     for an obviously-invalid ID), **but it must not be the only enforcement point** — the ID can change
     afterward, so it is never authoritative on its own.
   - If session/file storage is currently keyed by the Project ID text directly, consider whether it
     should instead be keyed by an internal session id independent of the mutable Project ID, with the
     Project ID (→ subject_id used in the DB, storage path, everything downstream) bound only once, at
     the moment PROCESS is clicked and passes validation.
   This is a real design decision. If the current architecture makes this awkward or risky to change
   safely, **stop and explain the tension rather than forcing a fragile patch** — same standing
   instruction as every prior round.

4. Memo has no allowlist implications — it just needs to stay editable throughout, and whatever value is
   in the field at PROCESS click is what gets saved with the subject.

## Verification required — use `claude-in-chrome`, actually click through

1. Open Create New, type Project ID `chb06`, upload a real file. While Phase A/B is still running in
   the background (or after), confirm the Project ID field is still editable (type more, clear, retype).
2. With files already uploaded under a valid ID, **change Project ID to an invalid one** (e.g. `chb01`,
   a TRAIN subject, or `chb99`) and click PROCESS — confirm it's rejected with the exact allowlist
   toast, no subject gets created, panel stays open with the files still listed.
3. Fix the ID back to a valid allowlisted subject and click PROCESS again — confirm it proceeds
   normally and the subject appears correctly in the Database table under the corrected ID.
4. Quick re-check that rounds 1 and 2 still hold (panel doesn't auto-close, overlay layout intact,
   PROCESS still gates only on upload completion) — not a full re-test, just confirm no regression.
5. `pytest web_demo/backend/tests/test_guards.py -v` and `git status` — paste raw output in the report.

**Write your report to `web_demo/CC_STEP3_FIX3_REPORT.md`.** Cover: what you found currently coupling
Project ID to upload/storage, the architecture decision you made for point 3 above and why, and all
five verification results.

## Stop condition

Do not proceed to Step 4. Stop once Project ID/Memo are editable throughout, the allowlist check is
authoritative at PROCESS-click time (verified with both a rejection and a subsequent successful
correction), and rounds 1–2 still hold.
