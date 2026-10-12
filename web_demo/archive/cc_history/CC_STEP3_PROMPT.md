# CC_STEP3_PROMPT.md — Step 3: Create new → upload → Process → subject appears in the table

**Prerequisite:** Step 2 is done and closed (see `web_demo/BUILD_PROGRESS.md §5` for what exists and
the lessons from that step — read it, especially §5.3: a file existing at the expected path does not
mean its content is correct; verify content, not just presence). Confirm
`pytest web_demo/backend/tests/test_guards.py -v` is currently green before doing anything else.

Read in this order before writing any code:
1. `web_demo/CLAUDE.md`
2. `web_demo/SZSCAN_SPEC_v5.md` §1.5, §1.6, §2, §5.1, §5.4, §5.5, §5.6, §5.7, §8 (O1, O2) — in full,
   not skimmed. This step has more subtlety than Step 2; guessing from partial reading will cost more
   rebuild cycles than reading carefully now.
3. `web_demo/DEMO_BUILD_HANDOFF.md` §4 (the `process_file`/`process_subject` pseudocode) and §6 row 3.
4. View the actual mockups (copy to scratch first, never open `web_demo/UI/` directly):
   `UI/A1a*.png` (Create new panel), `A1b*.png` (file error), `A1c*.png` (upload in progress),
   `A1d*.png` (both variants — "file uploaded" state AND "processing another subject, blocked" state
   share this prefix, look at both), `A2a*.png` (processing spinner), `A2b*.png` (done), `A2c*.png`
   (delete while processing), `A3a*.png`/`A3b*.png` (minimize states), `A4a*.png` (Database, full data),
   `A4b*.png` (click subject / delete subject).

## Scope boundary

In scope: Create New panel, file upload with validation, the two-stage pipeline execution described
below, minimize-to-toast, single-subject concurrency lock, Delete (subject-level only), Search
(deferred from Step 2 — real data exists now, wire it up), Database table now showing real rows.

**Out of scope, still**: Analysis screen, Panel Event, mini-timeline, channel attribution, Select
Range, Export. The "Open" button (§5.7) should select+highlight a row correctly, but its navigation
target (the Analysis screen) doesn't exist yet — a stub/TODO for the actual navigation is fine, say so
explicitly in your report rather than silently leaving it broken.

---

## 1. Architectural decision — resolving the two `# TODO(step3)` markers

`pipeline_demo.py`'s `process_file()` currently fits z-score stats and `LedoitWolf` per-file (Step 1
built it this way because only one file existed to test with). SPEC §1.6(a) requires these fit on the
**whole subject's** windows, not per file. But §5.5 also says stage 1 runs "as soon as one file finishes
uploading" — before sibling files of the same subject may even be uploaded yet. These two requirements
are in tension; resolve it this way:

- **Split `process_file()`'s current work into two phases:**
  - **Phase A (runs immediately per file, on upload completion):** read the 18 channels, bandpass +
    notch filter, cut into 4s windows. Cheap, needs nothing from sibling files. This is what flips the
    file's status icon from the spinning circle to `✕` (uploaded) in the mockup.
  - **Phase B (runs once, when the *last* file of the subject finishes uploading):** concatenate the
    raw windows from every file uploaded so far for this subject, compute the z-score mean/std and the
    `LedoitWolf` fit on that combined set (satisfying §1.6a), then run the rest of the pipeline (CAR →
    adjacency → band powers → GAE → zrecon/zlatent/zgamma → robust-z → ensemble) **per file**, using
    those subject-wide statistics. This produces the per-file continuous ensemble score arrays that
    stage 2 (Process button) will concatenate.
- Update `pipeline_demo.py` accordingly and remove both `# TODO(step3)` comments once resolved — replace
  them with a short comment explaining the phase split, so a future reader doesn't wonder why fitting
  happens where it does.
- This is a real design decision, not a guess — if you see a reason this split is wrong or unworkable
  once you're in the code, stop and explain why rather than silently doing something else.

## 2. Operating point (O1) — the part that actually determines detection quality

**Do not hardcode a `pen_mult` value from this prompt or from memory.** Here's the situation and what
to implement:

- `cpd_pipeline_v14.detect_events(score_timeline, pen_mult, min_mag_pct=60, local_win=15, win_sec=4,
  inter_mask=None, merge_s=90)` has no default for `pen_mult` — every other parameter (PELT model/
  min_size/jump, magnitude filter percentile, merge gap) already has a sensible built-in default in that
  locked module. `pen_mult` is the one knob demo-time processing must supply.
- `fp_budget_operating_point.py` defines `BUDGETS = {"balanced": 40.0, "high-sensitivity": 75.0}` — read
  this constant directly from the file at runtime, don't copy the number into new code from this prompt.
  Use `"balanced"` (40 FP/day) as the demo's target — there's no UI control for choosing a profile
  (matches CLAUDE.md's "no evaluation metric in the UI" — a clinician shouldn't have to pick an FP
  budget), so pick one canonical target and use it consistently.
- **The live subject has no ground truth**, so "FP/day" for a new upload can't be computed the way the
  thesis's locked CSVs computed it (those required labels). Implement a **label-free, per-subject,
  demo-time calibration** instead: for the subject's own concatenated global score timeline (after
  Phase B / before final event assignment), try a small grid of `pen_mult` values, run
  `detect_events()` for each, compute the resulting event rate (events per 24h of the subject's total
  recording duration — treating the whole recording as the interictal-equivalent denominator, consistent
  with the label-free approximation already justified in SPEC §1.6a for the low-prevalence assumption),
  and pick the `pen_mult` whose resulting rate is closest to the 40/day target.
  - Pick a reasonable grid (e.g. a handful of log-spaced values spanning what you observe in
    `cpd_pipeline_v14.py`'s own self-test / typical usage, or check if `fp_budget_operating_point.py`'s
    `FE.MAG_PCTS` / `DEFAULT_PENS`-equivalent grid values are referenced anywhere importable and reuse
    them rather than inventing a new grid from scratch).
  - Report in your final write-up: the grid you used, the chosen `pen_mult` for whichever test subject
    you validate with, and the resulting event rate — so this can be sanity-checked against expectations
    (HANDOFF §8's known risk: "if the label-free pipeline produces nonsense — e.g. zero events on every
    subject — this must be caught now, not after 5 more screens are built").
- `min_mag_pct` stays at `cpd_pipeline_v14.py`'s own default (60) unless you find a documented reason to
  change it — don't touch it without a reason recorded in your report.

## 3. Subject identity — "Project ID" field vs. uploaded filenames

The mockup's Create New panel has a free-text "Project ID" field, but the allowlist check (SPEC §2, only
`chb03/06/13/14/15/16/17/18`) needs *something* to check against. Resolve it this way unless you find
evidence in the mockups/spec that contradicts it: **treat the typed "Project ID" value as the subject ID
directly** — it's what gets validated against the 8-subject allowlist and what appears in the Database
table's `ID` column. Uploaded EDF filenames are used separately for parsing `File Start Time`/duration
per file (SPEC §5.1) and are not required to textually match the typed Project ID, but if you find it
easy to also warn when they clearly don't match (e.g. typed `chb06` but uploaded `chb13_01.edf`), a
lightweight sanity check is welcome — not required, don't over-build it.

If mid-implementation you find something in the mockups that makes this reading wrong, say so in your
report rather than silently picking a different interpretation.

## 4. Upload flow and validation (SPEC §5.5, §2)

- Backend needs a real multipart file upload endpoint. Store uploaded EDFs somewhere under
  `web_demo/backend/` (gitignored — pick a clear location, e.g. `backend/uploads/{project_id}/`, and say
  which one you used in your report; this is your call, not spec-mandated).
- Reject non-allowlisted subjects with the exact toast: `This demo is restricted to the held-out test
  subjects.` (SPEC §2). Reject malformed files / wrong channel config with the exact toast:
  `File rejected — unsupported format or channel configuration.`
- Per-file status icons per the mockup (`UI/A1c`): spinning circle while uploading (with a stop button
  in the middle of the circle — clicking it cancels that file's upload only), `✕` once uploaded
  (clicking removes it from the list).
- "Process" button stays disabled until every listed file has finished uploading (no fake progress %,
  per `SZSCAN_DESIGN_v2.md §8`'s wording table).

## 5. Two-stage processing or­chestration (SPEC §5.5)

- Stage 1 (Phase A+B from §1 above) happens automatically as files upload, finishing at the last file.
- Clicking "Process" (button enabled once stage 1's per-file scores all exist): concatenate the
  per-file ensemble scores **in filename order** (not upload order — SPEC is explicit about this), run
  the operating-point calibration from §2, then `cpd_pipeline_v14.detect_events()` once on the whole
  concatenated timeline, then assign each returned event back to its file using the cumulative-offset
  method from SPEC §1.5 (`offsets[f] = running total of len(score[f'])` for files before `f`, in
  filename order) — **do not** look for or invent an `edf_index`/`locate_range()` module, it doesn't
  exist and shouldn't (SPEC §1.5, §3 already explain why).
- Full-panel loading state while either stage runs: spinner + simple progress bar, not distinguishing
  the two stages, no fake percentage — copy: `Processing subject — combining files and detecting change
  points...` (from `SZSCAN_DESIGN_v2.md §8`).
- On completion: Database gets the new subject row + all child file rows at once (SPEC §5.1 — a subject
  being processed must not appear in the table at all until fully done), Status = `View` for the subject
  and every child file (nothing has been "Viewed" yet — that requires the Analysis screen, Step 4+).
- Alert column (SPEC §5.3): `(AI events not yet Rejected) + (user-added events)`. At this step there are
  no user-added events yet (that's Step 6), so Alert = count of AI-detected events assigned to that
  file/subject, all currently un-reviewed (SPEC says Uncertain/Unseen still count — since nothing has
  been reviewed yet, every AI event counts toward Alert). Store enough in the DB schema now
  (event onset/offset/file/source at minimum) that Steps 5-7 can build the review UI on top without a
  schema migration.

## 6. Minimize + concurrency lock (SPEC §5.5)

- Minimize ("−" button) doesn't cancel anything — it collapses the panel to a bottom-right toast:
  `Create New (draft)` while still uploading, `Processing...` while Process is running (`UI/A3a`/`A3b`).
  Clicking the toast re-opens the panel. Work keeps running in the background either way.
- **Exactly one subject may be mid-pipeline system-wide**, even if minimized. Clicking "Create new"
  while another subject is processing must block, with the message from `UI/A1d`
  ("Processing another subject. Please wait before creating a new one") rather than opening a second
  panel.

## 7. Delete (SPEC §5.6)

- Subject-level only. Selecting a child file row and clicking Delete does nothing (no error, just no
  response, per spec).
- One confirmation dialog, same wording regardless of whether the subject is mid-processing or already
  done — don't build two separate messages.

## 8. Search (deferred from Step 2, SPEC §5.4) — wire it up now that real data exists

- Filters by filename or subject name, case-insensitive, partial match, only on clicking the search
  button (not on every keystroke).
- Matching a child filename → table narrows to that subject only, auto-expanded, showing only the
  matched file (siblings hidden until search is cleared).
- Matching a subject name → shows that subject with all children, collapsed.
- No match → `No results for '...'` (different wording from the plain empty-database state, which stays
  `No data`).

## 9. Guard check + report

- Run `pytest web_demo/backend/tests/test_guards.py -v` — this step touches the actual pipeline
  execution path for the first time since Step 1 (file uploads, `process_subject`, event storage), so
  don't assume it's a trivial pass this time — actually think about whether anything here risks the
  guards (it shouldn't, since none of this touches labels or the forbidden arrays, but check).
- Run `git status` — confirm nothing under `web_demo/UI/` shows modified, and that nothing outside
  `web_demo/` changed.
- **Write your full report to `web_demo/CC_STEP3_REPORT.md`** (this worked well last round — don't
  revert to printing a long report to the terminal, it gets truncated in scrollback). Cover: the
  Phase A/B split you implemented, the operating-point grid and calibration result on at least one test
  subject, where uploaded files are stored, the Project-ID-as-subject-ID decision (confirm you followed
  it or explain why not), and the standard guard/git-status output.
- Give Boti the exact start commands for backend + frontend (same pattern as Step 2), and remind him the
  visual comparison against `UI/A1a`–`A4b` is his to do, not something to describe in text.

## Stop condition

Do not start Step 4 (Analysis screen). Stop once a full create→upload→process→appears-in-table cycle
works end to end for at least one real allowlisted test subject, and the report file above is written.
