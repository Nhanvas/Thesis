# CC_STEP9_PHASE2_RESUME_PROMPT.md — resume Phase 2 after an interrupted session (generic, v2)

Read first: `web_demo/CC_STEP9_PHASE2_PROMPT.md` — task, order, and method, still authoritative.

**Context:** Phase 2 has now been interrupted more than once — mid-upload on `chb17` the first time,
mid-Process on `chb14` the second time. This replaces the earlier `chb17`-specific resume prompt with
a generic one, so the same trigger can be pasted again unchanged no matter which subject or which
stage a future interruption happens at. `BUILD_PROGRESS.md`'s §1 text edit is already applied — don't
touch it again.

## 1 · Figure out exactly where things stand — every time, don't assume from a screenshot alone

1. Read `web_demo/CC_STEP9_PHASE2_PROGRESS.md` if it exists. Every subject listed there is fully done
   (appeared in the Database table, Status `View`, already checkpointed) — skip those.
2. From the fixed order `chb17 -> chb14 -> chb18 -> chb03 -> chb15 -> chb06`, the first subject **not**
   yet in the checkpoint file is the one to resume or start.
3. `GET /api/uploads/current` for that subject and act on exactly one of these 4 cases:
   - **No live session** — check for an orphaned draft directory on disk for that subject (same check
     `CC_STEP9_PHASE2_PROMPT.md` §2 did for `chb03`/`chb06`); remove it if present, then start that
     subject completely fresh.
   - **Live session, files still uploading** — continue uploading the remaining files, then Process.
   - **Live session, all files uploaded but Process not yet called** — call Process now.
   - **Live session, Process already running (Phase B / PELT in progress)** — do **not** restart or
     re-upload anything. Just poll `GET /api/uploads/current` until it reports done. Restarting here
     would duplicate work and risk two concurrent runs on the same subject.
4. State plainly which of the 4 cases applied before continuing.

## 2 · Checkpoint after every subject — unchanged

Immediately after each subject finishes (Database table, Status `View`) — before moving to the next
subject, not batched at the end — append one line to `web_demo/CC_STEP9_PHASE2_PROGRESS.md` with:
subject id, file count, wall-clock Phase A+B time, wall-clock Process/PELT time, converged `pen_mult`.

## 3 · Continue through whatever subjects remain, in fixed order

`chb17 -> chb14 -> chb18 -> chb03 -> chb15 -> chb06` — skip any already in the checkpoint file.

## 4 · Completion + report — unchanged from the original prompt

Once every subject in the order is checkpointed, do `CC_STEP9_PHASE2_PROMPT.md` §4 in full and write
`web_demo/CC_STEP9_PHASE2_REPORT.md`. Note in the report any subject whose timing figures reflect an
interrupted-then-resumed run (e.g. `chb17`'s first run) rather than one continuous pass, so those
numbers aren't read as directly comparable to a clean run when picking O4.

If this session is also interrupted before finishing, that's fine — the same resume trigger can be
pasted again unchanged; §1 above figures out where to pick up every time.

Then **stop. Do not run `git add`/`commit`/`push`.**
