# CC_STEP7_PROMPT.md — Step 7: Channel Attribution Panel (+ pre-steps A and B)

**Prerequisite:** Step 6 is closed (`CC_STEP6_REPORT.md`, `CC_STEP6_FIX_REPORT.md`,
`CC_STEP6_FIX2_REPORT.md`; `BUILD_PROGRESS.md §9`). Run `pytest web_demo/backend/tests/test_guards.py -v`
first and confirm 4 passed before doing anything else.

You will work through **pre-steps A and B** (small, both approved by Boti), then **Step 7 itself**
(Parts 1–5). Work autonomously inside the step, **stop at the end**. Do not start Step 8.

`SZSCAN_SPEC_v5.md` already contains note **C19** (the Step 6 gap-fill decisions), recorded by Boti
before this step. Do not add it again; your spec note in Part 5 is **C20**.

## Standing rules (all apply)

- **Do not run any `git add` / `git commit` / `git push`.** Boti commits himself.
- Do not touch anything outside `web_demo/`. Never edit `src/` (read-only, single-source with the
  thesis). New demo logic lives in `web_demo/backend/`.
- The three hard guards and the write guard stay in force (`CLAUDE.md`): no `build_timeline_masked`, no
  seizure fields from `chb*-summary.md`, never load `{subj}_interictal.npy` / `{subj}_ictal.npy`. If a
  guard fires, fix the code — never weaken the test.
- No fake data. Everything shown must come from the real model output.
- Use `claude-in-chrome` for all live verification **from the start**. If it is not connected, say so
  immediately and stop — do not fall back to Playwright/curl for visual checks.
- Never put scratch files into `web_demo/UI/`. Mockup copies and crops go to a scratch folder outside the
  repo or into `web_demo/CC_STEP7_SCREENSHOTS/`.
- Visual fidelity means **position and colour**, checked by literal screenshot comparison against the
  mockup, not "the right elements exist somewhere". Compare **proportions**, not absolute pixels (mockups
  are a different resolution from the live app).
- If a mockup and a written doc disagree on something visible, the mockup wins; report the disagreement.
- Wording is a scientific constraint here (`THESIS_CONTEXT_FOR_DEMO.md §5`), not a UI preference.
- Report: write `web_demo/CC_STEP7_REPORT.md` as a file. **Put the human-readable summary first** (what
  changed per file, decisions, measured values, anything flagged) and the raw command output **last**.

## Read first, in this order

1. `web_demo/SZSCAN_SPEC_v5.md` §6.7 (Channel Attribution Panel), §6.5 (Event Panel), §5.3, §7.3.
2. `web_demo/THESIS_CONTEXT_FOR_DEMO.md` §5 (attribution constraints).
3. `web_demo/SZSCAN_DESIGN_v2.md` §4 (teal scale) and §2 (axes).
4. `docs/ATTRIBUTION_SPEC.md` **§9 only** (read-only; `CLAUDE.md` names it as relevant to the demo).
5. Mockup `UI/B2a*.png` (copy to scratch first, then view). It is the only mockup of this panel.
6. `web_demo/BUILD_PROGRESS.md` §1, §9.
7. `backend/pipeline_demo.py`, `backend/pipeline_worker.py`, `backend/db.py`, `backend/main.py`,
   `src/retrain/gae_joint.py` (read-only: `joint_score(..., per_node=True)`, `score_windows(...,
   per_node=True)`, `build_batch`).

---

## Pre-step A — provenance dump, then delete the Human test events

Boti decided (2026-09-24) that the Human test events are removed.

1. **Provenance dump first.** Read the `events` table (read-only) for the `chb13` subject and write it
   into the report as a table: `id, file, source, onset_sec, offset_sec, review_status`, plus any
   timestamp/created column that exists. This documents which events came from the pipeline's CPD run
   (`source='AI'`) and which were drawn by hand (`source='Human'`).
2. **Delete only the Human events of `chb13_02.edf` and `chb13_03.edf`**, through the real app API
   (`DELETE /api/events/{id}`), not raw SQL. Expected: `chb13_03.edf` three Human events
   (≈1153.4–2323.7 s, ≈2561.2–2620.9 s, ≈3473.9–3571.4 s), `chb13_02.edf` two
   (≈19.4–41.8 s, ≈1372.3–1416.8 s). If the table shows something different, delete only rows with
   `source='Human'` on those two files and report the difference.
3. **Never touch any AI event or its review state.** If Human events exist on other files (the synthetic
   test files under `chb14`/`chb15`/`chb16`), do **not** delete them; just list them in the report.
4. After deleting, confirm and report: `chb13_03.edf` Alert, `chb13_02.edf` Alert, `chb13` subject Alert
   (expected 1 / 0 / 1 given the four AI events are Reject/Reject/Uncertain/Reject — report the real
   numbers), in both the Analysis header and the Database screen.

## Pre-step B — verify the Accept colour live (authorized, irreversible, synthetic data only)

The Accept fill (`#16A34A`) was never seen live after the solid-block change. Boti authorizes this once:

- Find an AI event with `review_status = Unseen` on one of the **synthetic test files**
  (`chb14`/`chb15`/`chb16`). Never use anything under `chb13`.
- Accept it through the real UI (Accept + Save). It cannot be returned to Unseen afterwards; leave it
  Accepted.
- Sample the fill of its block on the mini-timeline and the Event Time strip (computed style / pixel
  sample, no event selected): expect solid `#16A34A`, opacity 1, no hatch. Also check its Event Panel row
  bar. Screenshot each. Report which event you accepted (file, id, onset).

---

# Step 7 — Channel Attribution Panel

## What the panel is (scientific framing — mandatory)

Per `THESIS_CONTEXT_FOR_DEMO.md §5` and `SZSCAN_SPEC_v5.md §6.7`: **XAI for the GAE reconstruction
branch.** It shows which channels the autoencoder reconstructs worst during an event. It is **not**
localization and **not** seizure onset zone. The label-scored evaluation is PROVISIONAL.

- Panel title exactly: `Channel-level reconstruction anomaly — Event N` (N = the event's current display
  name number).
- **Forbidden wording anywhere in this panel:** causing, cause, seizure focus, focus, origin, source (as
  in "source of seizure"), localization/localizes, onset zone, SOZ, "contributes". No evaluation metric
  on screen (no AUROC, CI, p-value, accuracy of any kind).
- Blue is reserved for Human events; red/yellow/green heat scales are forbidden here. Teal only.

## Part 1 — Backend: per-window, per-channel reconstruction scores (the main risk of the step)

`BUILD_PROGRESS.md` records that the demo cache holds only the ensemble score per file. Verify that by
reading the code. The attribution panel needs the **per-node** (per-channel) joint reconstruction score
for every window: `gae_joint.joint_score(model, pg, A, Xn, B, per_node=True)` → `[B, 18]`, computed on
the same adjacency + band-power tensors that the demo pipeline already builds for the recon branch.

1. In `backend/pipeline_demo.py` (Phase A, per file), compute the per-node score in the same pass and
   save it next to the existing cache files as `{stem}.pernode.npy`, shape `[n_windows, 18]`, float32,
   channel order identical to the pipeline's 18-channel list. Row `i` ↔ window `i` ↔ seconds
   `[4i, 4i+4)`. **No window may be dropped** (same rule as the ensemble score).
2. **Do not change any existing output.** The existing `{stem}.score.npy` (and every other current cache
   file) must be byte-identical after your change. Record sha256 of each existing cache file for
   `chb13_02` and `chb13_03` *before* and *after*.
3. Write a **backfill script** in `backend/` (Phase A only) to produce `.pernode.npy` for every file that
   currently exists in the DB (`chb13_02`, `chb13_03`, and the synthetic test files). Never run CPD or
   Phase B in the backfill — that would rewrite events and lose review states. If a file's source EDF is
   no longer on disk, skip it, list it in the report, and make the API return a clear "attribution not
   available for this file" state (Part 2).
4. **Consistency gate — do this before any UI work.** For at least one real file (`chb13_03`), verify:
   - `pernode.mean(axis=1)` equals the scalar per-window raw recon score (`score_windows` without
     `per_node`) to within `1e-5` — this is the thesis code's own "cell-8" self-check;
   - the ensemble score array is unchanged (sha256 match, item 2).
   If either fails, **stop and write the finding into the report** — do not continue to the UI.
5. Measure and report the added Phase A cost per hour of EEG.

## Part 2 — Attribution definition, API and persistence

### 2.1 Definition (read it, do not invent it)

Read `docs/ATTRIBUTION_SPEC.md §9` and look (read-only, e.g. `grep -rn per_node src/`) for how the thesis
aggregates per-window scores and what "score" means. In the report add a section **"Attribution
definition"** stating, for each of the three items, **where it came from** (file + line/section) or
**that it is a fallback**:

1. *Windows of an event:* the windows whose 4 s span overlaps `[onset_sec, offset_sec]`; always at least
   the window containing the onset; clamp to the file's usable windows.
2. *Aggregation across those windows:* **fallback = arithmetic mean per channel** of the per-node score.
3. *Score shown per channel:* **fallback = that aggregated raw per-node reconstruction score**, unscaled
   (do not rescale or normalize it to look like the mockup's illustrative numbers). Choose a number
   format that keeps the 18 values distinguishable. Rank = position by score, highest first.

If §9 or the thesis code defines any of these differently, **implement the thesis definition** and say so.
If you use a fallback, mark it clearly `PROVISIONAL DEFAULT — Boti to confirm` in the report. Do not
block on it; Boti will confirm or swap it in the next chat.

### 2.2 Endpoints and storage

- `GET /api/events/{event_id}/attribution` → event id, current display name, the window range used, and 18
  rows `{channel, score, rank, status}` sorted by rank (highest score first). Works for **AI and Human
  events** identically. If the file has no `.pernode.npy`, return a clear "not available" payload.
  Attribution is computed on read from the per-node array — never cached in the DB — so an edited Human
  event (its range changes) gets fresh scores.
- Per-channel review status (`Accept` | `Reject` | unset): new table, e.g.
  `attribution_status(event_id, channel, status, PRIMARY KEY(event_id, channel))`. Deleting an event
  must delete its rows (do it explicitly; do not rely on an FK pragma). Keyed by **channel name**, so an
  edited event keeps its channel judgments.
- `PUT /api/events/{event_id}/attribution-status` = **Save** (body: the full set of statuses shown;
  replaces the stored set). **Clear all** = clears the selections in the panel; it persists only when
  Save is pressed — the same Save-persists pattern as the AI event review. Record this as a gap-fill
  decision in the report.
- Step 8 (Export) will read rank/channel/score/status from here — keep the shape simple and complete.
- No attribution status ever changes Alert counts or the event's own review status.

## Part 3 — Frontend: the panel

Build to `UI/B2a`. Establish from the mockup, and state in the report, where the panel sits relative to
the other panels, and what its default status state is (if the mockup shows one; otherwise the default is
**unset** — flag it).

- **Title:** `Channel-level reconstruction anomaly — Event N`.
- **Head diagram:** a simple circle plus the 10-20 electrode positions, as a background. Draw **18
  straight lines, one per bipolar channel, connecting its two electrodes** (e.g. `FP1-F7` = FP1↔F7).
  **No dots standing in for channels** — CHB-MIT is bipolar. (Note for the report: the 18 channels use 19
  distinct electrodes; `SZSCAN_SPEC_v5.md §6.7` says "18 electrode positions" loosely — small labelled
  electrode markers as a background reference are fine, the data marks are the 18 lines.) Take electrode
  positions from the mockup's proportions.
- **Colour:** teal scale from `SZSCAN_DESIGN_v2.md §4` — low `#CBD5E1`, mid `#2DD4BF`, high `#0F766E`, with
  the colorbar `linear-gradient(to right, #CBD5E1, #2DD4BF, #0F766E)` above the diagram. Map each
  channel's score to the gradient by min–max across the event's 18 scores (min → low end, max → high
  end; all-equal → low). This is the implementation reading of the design; record it in the report. Use
  tokens from the single source of truth (`index.css` `:root` / `design-tokens.js`), no second hex.
- **Rejected channel:** keeps its line at ~35 % opacity (DESIGN §4). **Hovered/selected** = violet
  (`--color-interaction`). Two-way hover between table row and line is **optional**: build it only if it
  is cheap and does not risk the required parts; say in the report whether you did.
- **Table below:** columns `Rank / Channel / Score / Status`. Rank is fixed by score; the user cannot
  reorder. Channel names in IBM Plex Mono. Status is a **segmented control `Accept | Reject`**, mutually
  exclusive like a radio button.
- **Buttons:** `Save` and `Clear all` at the bottom of the table (Save persists; see 2.2).
- **Sync:** the panel follows the currently selected event (Event Panel is the primary control source),
  **including a Human event**, and re-fetches when the selected event's range changes (Edit) or when
  renumbering changes its name.
- **Empty state:** no event selected → placeholder `Select an event to view attribution`. **Never**
  auto-select the first event.
- **Unavailable state:** file without `.pernode.npy` → a short neutral message
  (`Attribution is not available for this file.`), no error toast.
- The Analysis screen is allowed to grow long and scroll vertically; do not squeeze panels into one
  viewport.

## Part 4 — Verification (live, with evidence — not code-read confidence)

Screenshots into `web_demo/CC_STEP7_SCREENSHOTS/`. Put the numbers in the report.

1. Consistency gate results from Part 1 (item 4), sha256 before/after table, added Phase A cost.
2. **Independent recomputation:** in a throw-away Python check (scratch, not in the app), recompute one
   event's 18 scores directly from `{stem}.pernode.npy` using the definition in 2.1 and compare with the
   API response — they must match exactly. Do it for one AI event and one Human event.
3. Empty state text is exactly `Select an event to view attribution` on first load; nothing preselected.
4. Select an AI event: title is `Channel-level reconstruction anomaly — Event N` with the correct N;
   count the head-diagram data marks in the DOM = **18 lines**, each connecting the right electrode pair;
   table has 18 rows sorted by score descending with rank 1…18; table values equal the API.
5. Colours: sample the line colours (pixel or computed style) for the highest- and lowest-scoring channel;
   confirm they sit at the gradient's high/low ends and come from the tokens. Confirm **no red/yellow/
   green, no blue** in the panel (blue is Human-only).
6. Create one **disposable Human event** with Select Range, select it: the panel shows its attribution
   (values match the independent recompute); use **Edit** to move its range and confirm the values
   change accordingly; then delete it and confirm the panel returns to the empty state.
7. Segmented control: Accept/Reject mutually exclusive; the Rejected channel's line drops to ~35 %
   opacity; `Save` persists (reload the page, reselect the event → statuses are back); `Clear all` empties
   the selections and, after `Save`, the stored set is empty. Rank order never changes with status.
8. Deleting an event removes its attribution rows (check the table directly).
9. **Wording scan:** grep the frontend attribution component(s) and API strings for the forbidden words in
   the framing section — zero hits in user-visible text. Confirm no metric on screen.
10. **Literal screenshot comparison** with `UI/B2a`: position of the panel, head diagram, colorbar, table,
    buttons; colours. List every remaining difference honestly.
11. Regression (quick): Select Range create/delete still works and Alert moves +1/−1; Event Panel
    filtering, mini-timeline blocks, dimming rule and header title unchanged.
12. **Cleanup — leave a clean state:** no disposable events, no attribution statuses left behind on any
    real event (Clear all + Save to reset them). Confirm the final state: `chb13_03.edf` / `chb13_02.edf`
    have **zero Human events** and their AI events' review states are exactly as you found them after
    Pre-step A.
13. `pytest web_demo/backend/tests/test_guards.py -v`, `git status`, `git diff --stat` — raw output pasted
    at the end of the report. Confirm nothing outside `web_demo/` changed.

## Part 5 — Record what you implemented in the spec (docs only)

After the panel works, add a short dated note **C20** to `SZSCAN_SPEC_v5.md §6.7` (English, minimal
edit, no reformatting) stating: how the windows of an event are chosen; the aggregation and the score
shown (and whether each came from the thesis definition or is a provisional default); the gradient
mapping; that per-channel statuses are stored per event by channel name and persist on Save; what
`Clear all` does; where `.pernode.npy` lives. Mention `C20` in the history line at the top (next to the existing `C19`).

## Report must contain (checklist)

- Summary of changes per file; the "Attribution definition" section with provenance of each item.
- Pre-step results: the provenance table of `chb13` events; which Human events were
  deleted and the resulting Alert values; the Accept check (which event, measured colour).
- Consistency-gate numbers, sha256 before/after, added Phase A cost, backfill list and any skipped file.
- Every gap-fill decision (Clear all semantics, default status, gradient mapping, hover, unavailable
  state) and every mockup-vs-live difference.
- Test-state note: what remains in the DB for `chb13_02`/`chb13_03` and on the synthetic files.
- Raw command output last.

## Stop condition

Do not start Step 8 (Export). Stop once pre-steps A and B are done, the panel works with everything above
verified live, the report is written, and the DB is left clean as described in Part 4 item 12.
