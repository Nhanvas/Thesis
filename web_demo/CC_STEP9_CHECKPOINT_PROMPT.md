# CC_STEP9_CHECKPOINT_PROMPT.md — Step 9 checkpoint: record phase 1 + 1b, before phase 2

Read first: `web_demo/CC_STEP9_PHASE1_REPORT.md`, `web_demo/CC_STEP9_PHASE1B_REPORT.md` (both already
on disk from this session), `web_demo/SZSCAN_SPEC_v5.md §1.7`.

This is a **documentation-only checkpoint** — no pipeline code touched, no new uploads, no DB change.
Step 9 is **not finished**: phase 1 (inventory + cleanup) and phase 1b (real PELT/Phase-A+B timing on
`chb16`) are done, but phase 2 (uploading and processing the other 6 real subjects — `chb03`, `chb06`,
`chb14`, `chb15`, `chb17`, `chb18`) has not started. This prompt exists so the written record matches
that reality before the work continues in a new chat session. Guards unchanged: `test_guards.py` must
stay 4/4 green, no write outside `web_demo/`, no `git add`/`commit`/`push`.

---

## 1 · Record the PELT-cost correction in `SZSCAN_SPEC_v5.md §1.7`

Add a dated **C23** note (matching the style of the existing C17–C22 notes) next to §1.7's existing
claim that the Process/PELT step is "the most time-consuming part," recording:

- Measured on `chb16` (19 real files, 19.0 h, via the real Create-New→Process flow,
  `CC_STEP9_PHASE1B_REPORT.md`): PELT alone = **3.58 s/hour of EEG**, only **~25%** of Phase A+B's own
  wall-clock (**14.29 s/hour**, real upload flow) — PELT is **not** the dominant cost; the original
  claim was written against the older, component-level cost figures, not a real end-to-end
  measurement.
- Real Phase A+B wall-clock (14.29 s/hour, real HTTP upload flow) runs **~46% higher** than the old
  `9.76 s/hour` serial-CLI figure still quoted in `CLAUDE.md` — explained by genuine upload-transfer
  overhead plus unbounded per-file Phase A thread concurrency (up to 19 concurrent threads observed on
  a 4-physical/8-logical-core machine). Record the concurrency finding as an **open item, not fixed** —
  don't imply it's been resolved.
- Cite `CC_STEP9_PHASE1B_REPORT.md` as the source; a short summary + pointer, not every number
  retyped, matching the terse style of the existing C-notes.
- Do **not** delete or rewrite the original sentence(s) in §1.7 — append the note, per precedent (the
  same pattern C18–C22 already follow in this file).

## 2 · Update `BUILD_PROGRESS.md`

Add a **"Step 9 — detail"** section, explicitly **in progress, not done**, covering phase 1 (`chb14`/
`chb15`/`chb16` deleted as confirmed-synthetic; `chb03`/`chb06` found as orphaned real-partial uploads
on disk with no DB row; `chb17`/`chb18` empty) and phase 1b (`chb16` fully and genuinely processed
through the real flow, kept in the DB deliberately; the PELT/Phase-A+B timing findings). Specifically:

- Status table row 9: change from "not started" to **"IN PROGRESS — phase 1 & 1b done; phase 2
  (`chb03`/`chb06`/`chb14`/`chb15`/`chb17`/`chb18` still need a real upload+process) not started."**
- "Where to resume": **Step 9 phase 2**.
- Note the one loose end from phase 1b plainly: `chb16`'s upload session is sitting `done: true`,
  **unacknowledged** — someone needs to open the app and click through the "Processing complete" panel
  before a new Create-New session (needed for phase 2) can start, per the one-subject-in-flight rule.
  This is a manual UI action for Boti, not something for a future prompt to script around.
- Open items section: add the two still-open decisions from this session — (a) file-count-per-subject
  scope for the 6 remaining subjects (full real file set vs. a representative subset, per the `chb13`
  precedent), still Boti's call; (b) the `DELETE /api/subjects/{id}` endpoint not cleaning up
  `uploads/{subject_id}/` on disk, deliberately deferred to a final cleanup pass before the demo is
  considered complete, per Boti's own decision — not treated as an active bug needing a fix now.
- Reference both `CC_STEP9_PHASE1_REPORT.md` and `CC_STEP9_PHASE1B_REPORT.md` as the sources for this
  section, the same way earlier step-detail sections cite their own `CC_STEP*_REPORT.md` files.

---

## Report

Write `web_demo/CC_STEP9_CHECKPOINT_REPORT.md`: the exact text/diff added to `SZSCAN_SPEC_v5.md §1.7`
(item 1), the exact section added to `BUILD_PROGRESS.md` (item 2), raw `pytest -v`, `git status`,
`git diff --stat`.

Then **stop. Do not run `git add`/`commit`/`push`. Do not start phase 2 or touch any pipeline, upload,
or DB state** — this prompt only edits two markdown files.
