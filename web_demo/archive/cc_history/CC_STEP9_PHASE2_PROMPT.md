# CC_STEP9_PHASE2_PROMPT.md — upload + process the 6 remaining real TEST subjects (Step 9 phase 2)

Read first: `web_demo/BUILD_PROGRESS.md` §14 ("Open items going into Step 9") and §15 ("Step 9 —
detail"), `web_demo/SZSCAN_SPEC_v5.md` §1.7 (C23) and §5.5 (concurrency limit / Create-New flow),
`web_demo/CLAUDE.md`, `web_demo/STEP8_9_PREDEFENSE_CHECKLIST.md`, and `web_demo/CC_STEP9_PHASE1B_PROMPT.md`
+ `web_demo/CC_STEP9_PHASE1B_REPORT.md` — phase 1b is the exact method to repeat 6 more times, don't
re-derive it from scratch.

Guards unchanged: `pytest web_demo/backend/tests/test_guards.py -v` must stay 4/4 green throughout.
No write outside `web_demo/`. **No `git add`/`commit`/`push`.**

## 0 · Two small decisions already made — apply them without asking again

1. **Full real file set for every subject** — not a representative subset. Applies to all 6 subjects
   below (confirmed by Boti, 2026-09-26).
2. **Phase A upload-thread concurrency stays unfixed** for this step (already documented in
   `SZSCAN_SPEC_v5.md` §1.7 / `BUILD_PROGRESS.md` §15.2 as deliberately deferred). Don't fix it as a
   side effect of this step even if it looks convenient to.

## 1 · Housekeeping — fix one stale line in `BUILD_PROGRESS.md` before starting

The "Where to resume" note near the top of `BUILD_PROGRESS.md` §1 still says:

> *"Before drafting that prompt: `chb16`'s upload session is sitting `done: true`, unacknowledged —
> someone needs to open the app and click through the "Processing complete" panel first
> (one-subject-in-flight rule), and §14 below has two open decisions (file-count-per-subject scope;
> the `DELETE` endpoint's on-disk cleanup) that are Boti's call, not something to assume an answer
> to."*

This is now stale — `CC_STEP9_CHECKPOINT_FIX_REPORT.md` §2 found no session in progress at all
(`GET /api/uploads/current` → 404), so nothing needed dismissing; the in-memory lock had already
cleared itself when the backend process was restarted. Replace that sentence with:

> *"Before drafting that prompt: `chb16`'s upload-session lock had already cleared on its own by the
> time of the Step 9 checkpoint fix (a backend restart reset the in-memory lock; confirmed via a live
> `GET /api/uploads/current` returning no session — see `CC_STEP9_CHECKPOINT_FIX_REPORT.md` §2). No
> manual dismissal was needed. §14 below has one open decision left (the `DELETE` endpoint's on-disk
> cleanup) — file-count-per-subject scope was decided 2026-09-26: full real file set for every
> subject, not a representative subset."*

Don't touch anything else in that note or in §14 itself.

## 2 · Preflight — before touching any subject

1. Confirm the backend is up and `GET /api/uploads/current` currently shows no session (re-confirm,
   don't assume the checkpoint fix's finding still holds).
2. Read `BUILD_PROGRESS.md` §15.1 for the orphaned partial uploads already on disk for `chb03` (2 real
   files, Phase A cache only, no DB row) and `chb06` (1 real file, same). The app has no
   partial-resume mechanism (`SZSCAN_SPEC_v5.md` §5.5: "no Edit mode... edit = re-create"), so reusing
   1–2 already-cached files out of 18–38 saves negligible time and adds resume-state risk. **Default:
   locate and remove those two orphaned draft directories**, then do a fully fresh Create-New for both
   subjects. Report exactly what you found and removed before proceeding.
3. Spot-check that each of the 6 subjects' real file count on disk still matches the phase 1 inventory
   (`BUILD_PROGRESS.md` §15.1): `chb03` 38, `chb06` 18, `chb14` 26, `chb15` 40, `chb17` 21, `chb18` 36.
   Flag any mismatch before uploading that subject — don't proceed on a silent discrepancy.

## 3 · Process the 6 subjects, one at a time, in this order

```
chb17 (21 files, 21.01 h) -> chb14 (26 files, 26.00 h) -> chb18 (36 files, 35.64 h)
-> chb03 (38 files, 38.00 h) -> chb15 (40 files, 40.01 h) -> chb06 (18 files, 66.74 h)
```

Ascending by duration — cheapest subject first, so a real problem surfaces early rather than after an
hour of upload on the largest subject. The backend enforces exactly one subject processing at a time
system-wide (`SZSCAN_SPEC_v5.md` §5.5) — don't parallelize across subjects, and don't start subject
N+1 until subject N is fully finalized (appears in the Database table, Status `View`).

Use the same method as `CC_STEP9_PHASE1B_PROMPT.md` — driving the real HTTP flow directly (login,
`POST /api/uploads/current`, sequential `POST /api/uploads/current/files`, `POST
/api/uploads/current/process`, poll `GET /api/uploads/current` for state transitions) — **not**
`claude-in-chrome`: its `file_upload` tool caps combined attachments at 10 MB, far below any of these
subjects' real EDF sizes. Read `web_demo/frontend/src/api.js` for the exact request shapes if unsure;
don't invent an endpoint from memory.

For each subject:
1. Log in (credentials from `backend/.env`, same as phase 1b).
2. `project_id` = the subject id exactly (e.g. `chb03`); memo = `"Step 9 phase 2 - full real dataset"`.
3. Upload every real `.edf` file for that subject from
   `F:/Study/Thesis/Dataset/CHB-MIT/{subject}/`, sequentially.
4. Once every file is uploaded, call Process.
5. Poll until done, logging the wall-clock timestamp at each state transition (same method as phase
   1b) so Phase A+B and Process/PELT can be timed separately, same as `CC_STEP9_PHASE1B_REPORT.md`
   §2 did for `chb16`.
6. Confirm the subject appears in the Database table, Status `View`, file count and duration matching
   the inventory in §2.3 above.
7. Run `pytest web_demo/backend/tests/test_guards.py -v` — must still be 4/4. If it ever isn't, stop
   immediately and report before continuing to the next subject.

If any subject's upload or processing fails outright (not just runs slow), stop and report the
failure rather than retrying silently or skipping to the next subject.

## 4 · After all 6 are done

1. Confirm the Database table now lists exactly 8 subjects — the full TEST allowlist (`chb03, chb06,
   chb13, chb14, chb15, chb16, chb17, chb18`) — no more, no fewer, no synthetic subject left in.
2. Final `pytest -v` (4/4).
3. Build a small comparison table (file count, hours, real measured Phase A+B time, real measured
   Process/PELT time, converged `pen_mult`) for all 8 subjects — this directly informs
   `SZSCAN_SPEC_v5.md` open item **O4** ("which subject to use for the live-upload scenario — chosen
   by real file count"). Don't pick the subject yourself; just surface the numbers.

## Report

Write `web_demo/CC_STEP9_PHASE2_REPORT.md`: the §1 doc diff applied, §2's preflight findings (what
was found/removed for `chb03`/`chb06`, any file-count mismatches), the per-subject timing table from
§4.3, any anomaly encountered and how it was handled, raw `pytest -v`, `git status`, `git diff --stat`.

This step will likely run for **~50–70 minutes of real wall-clock** across all 6 subjects (per the
phase 1b measured rate, extrapolated to 227.3 h of EEG) — let it run to completion rather than
checking in partway.

Then **stop. Do not run `git add`/`commit`/`push`.**
