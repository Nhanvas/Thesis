# CC_STEP7_REPORT.md — Step 7: Channel Attribution Panel (+ pre-steps A and B)

Executed `CC_STEP7_PROMPT.md` in full, in order, live-verified throughout via `claude-in-chrome`
(confirmed connected before starting). No `git add`/`commit`/`push` run. Guards 4/4 green throughout.

---

## 1 · Summary

### 1.1 Pre-step A — provenance dump, then delete the Human test events

Provenance table (read-only dump, **before** deletion) — `events` table for `chb13`. The schema
(`web_demo/backend/db.py`) has **no timestamp/created column on `events`** (only `subjects.created_at`
exists), so that column is omitted:

| id | file | source | onset_sec | offset_sec | review_status |
|---|---|---|---|---|---|
| 78 | chb13_02.edf | Human | 19.434629 | 41.837456 | (none — Human carries no review axis) |
| 80 | chb13_02.edf | Human | 1372.299293 | 1416.822261 | (none) |
| 46 | chb13_03.edf | AI | 80.0 | 164.0 | Reject |
| 81 | chb13_03.edf | Human | 1153.356890 | 2323.674912 | (none) |
| 47 | chb13_03.edf | AI | 2420.0 | 2424.0 | Reject (comment `fsfsf`) |
| 76 | chb13_03.edf | Human | 2561.201413 | 2620.918728 | (none) |
| 48 | chb13_03.edf | AI | 2800.0 | 2804.0 | Uncertain |
| 49 | chb13_03.edf | AI | 3440.0 | 3444.0 | Reject (comment, 116×`x`) |
| 82 | chb13_03.edf | Human | 3473.851590 | 3571.378092 | (none) |

Matches `BUILD_PROGRESS.md §9.5` exactly: 4 AI events from the real CPD run (ids 46–49, Reject/Reject/
Uncertain/Reject) and 3 Human events on `chb13_03.edf` (ids 81/76/82) plus 2 on `chb13_02.edf` (ids
78/80).

No Human events exist on any other file (`chb14`/`chb15`/`chb16` synthetic test files) — checked, zero
rows.

**Deletion** — via the real API, `DELETE /api/events/{id}` for ids `78, 80, 81, 76, 82` (the 5 Human
events on `chb13_02.edf`/`chb13_03.edf`). **This is an irreversible action; Claude Code's auto-mode
classifier flagged it and paused for explicit user confirmation before proceeding** (the prompt
pre-authorizes it, but the classifier does not read that file) — user confirmed, then all 5 deletions
returned `200 {"ok": true}`.

**Result, verified live in both the Analysis header and the Database screen:**

| | before | after | expected |
|---|---|---|---|
| `chb13_03.edf` Alert | 4 | **1** | 1 ✓ |
| `chb13_02.edf` Alert | 2 | **0** | 0 ✓ |
| `chb13` subject Alert | 6 | **1** | 1 ✓ |

Header showed `CHB13_03 (01 alerts to check)`; Event Panel filter `All` showed exactly the 4 remaining
AI events (Reject/Reject/Uncertain/Reject, matching the untouched review states). No AI event or its
review state was touched.

### 1.2 Pre-step B — Accept colour, live

Authorized (irreversible, synthetic data only). Picked **event id 54**, `chb16` / `chb15_12_short.edf`,
AI, `Unseen`, onset 460.0 s / offset 464.0 s (4 s, single window) — a *synthetic* test file, never
`chb13`. Accepted through the real UI (Accept button → Save). Sampled via computed style (no event
selected, i.e. not the temporary violet selection-ring case):

| location | `background-color` | opacity | hatch |
|---|---|---|---|
| Mini-timeline Detections block | `rgb(22, 163, 74)` = `#16A34A` | 1 | none |
| Event Time strip block | `rgb(22, 163, 74)` = `#16A34A` | 1 | none |
| Event Panel row left bar (`border-left-color`) + light bg `rgb(240,253,244)` = `#F0FDF4` | `#16A34A` | 1 | none |

Exact match to the design token, full opacity, no hatch, in all three locations. Screenshots:
`CC_STEP7_SCREENSHOTS/prestepB_accept_expanded_row.jpg`,
`CC_STEP7_SCREENSHOTS/prestepB_accept_eventtime_strip.jpg`. This event is left **Accepted** (cannot be
returned to Unseen, as authorized) — it is on a synthetic file, not counted in any real-subject
cleanliness check.

### 1.3 Step 7 — files changed

| File | What changed |
|---|---|
| `web_demo/backend/pipeline_demo.py` | `process_subject_phase_b` gained two **optional, default-`None`** parameters, `pernode_out` and `zrecon_out` — when a caller passes a dict, the per-file loop also computes the per-node score (`gae_joint.joint_score(..., per_node=True)`, a *second, independent* call alongside the existing unmodified scalar call) and/or exposes the raw scalar recon score, and stores them into the caller's dict. Default behaviour (no dict passed) is **byte-identical** to before — verified (§2). `process_subject_phase_b_from_paths` passes `pernode_out` through. |
| `web_demo/backend/pipeline_worker.py` | `_run_phase_b` now also collects `pernode_out` and saves `{stem}.pernode.npy` next to the already-written `{stem}.filtered.npy` in the (still-draft) upload directory, so every **future** live Process run produces attribution data automatically (rides along when `_finalize_draft_dir` moves the whole directory). |
| `web_demo/backend/db.py` | New table `attribution_status(event_id, channel, status, PRIMARY KEY(event_id, channel))`. `_event_row`/`list_events` now include `file_id` (needed by the new endpoint to locate the file). `delete_event` explicitly deletes `attribution_status` rows first (not left to the FK pragma). New `get_attribution_status`/`set_attribution_status`. |
| `web_demo/backend/attribution.py` **(new)** | `get_event_attribution(event, file_row, upload_dir)` — computes the 18-channel attribution for one event from `{stem}.pernode.npy`, on read, never cached. |
| `web_demo/backend/backfill_pernode.py` **(new)** | One-off backfill script — produces `.pernode.npy` for every file already in the DB, reusing each file's already-cached `.filtered.npy` (never re-reads the raw EDF, never calls CPD/Stage 2). See §2 for why "Phase A only" as literally written isn't what this does. |
| `web_demo/backend/main.py` | Two new endpoints: `GET /api/events/{id}/attribution`, `PUT /api/events/{id}/attribution-status`. |
| `web_demo/frontend/src/attributionStyle.js` **(new)** | Electrode layout (19 positions, 0..200 viewBox), the 18 channel→electrode-pair table (pipeline order), and the 3-stop teal gradient interpolation (`design-tokens.js`'s `colorAttrLow/Mid/High`, no second hex). |
| `web_demo/frontend/src/components/AttributionPanel.jsx` **(new)** | The panel itself — title, colorbar, head-diagram SVG (18 lines + 19 reference electrode markers), table, Save/Clear all, two-way hover. |
| `web_demo/frontend/src/api.js` | `getAttribution(eventId)`, `saveAttributionStatus(eventId, statuses)`. |
| `web_demo/frontend/src/screens/AnalysisScreen.jsx` | New second row below the existing EEG/Event-Panel row, rendering `<AttributionPanel event={...}/>` under an empty flex-1 spacer so it aligns under the 340px Event Panel column. The Event-Panel row itself (`items-stretch`, Step 5/6) is untouched. |
| `web_demo/SZSCAN_SPEC_v5.md` | Spec note **C20** added after §6.7 (Part 5) + history line updated. |

**Not changed:** any file outside `web_demo/`, any existing cache file's bytes (§2), `PanelEvent.jsx`,
`eventStyle.js`, `MiniTimeline.jsx`, `EegPanel.jsx`, `db.py`'s existing event/subject functions beyond
the two additive lines noted above.

---

## 2 · Part 1 — per-window, per-channel reconstruction scores

**Reading of "Phase A, per file" (Part 1 item 1) vs. the actual architecture — flagged explicitly.** The
per-node reconstruction score requires a GAE model forward pass. In this codebase's Phase A/Phase B
split (`pipeline_demo.py`'s own docstring), Phase A is *open → filter → window only*, no model, no
adjacency; the model runs in **Phase B** (`process_subject_phase_b`). Computing per-node scores in
"Phase A" as literally written is not possible with the current architecture. What was implemented
instead: the per-node call sits in Phase B's existing per-file loop, in the same pass as the existing
scalar `zrecon_raw` call, reusing the exact same `pg`/`A_batch`/`Xn_batch` inputs — i.e. the closest
correct reading of "compute it in the same pass, don't add a separate pipeline run." The backfill script
is similarly "Phase B's model-scoring step reusing cached Phase A output," not literally "Phase A only"
— see its own docstring for the same note. **This does not touch Stage 2/CPD or the events table** at
any point, which is the actual hazard the prompt's wording is protecting against ("never run CPD... that
would rewrite events and lose review states") — confirmed by code inspection and by the DB dump in §5
showing every real event's review state unchanged after the backfill ran.

**Item 2 — no existing output changed.** sha256 of every `.npy` cache file under `web_demo/backend/
uploads/` (70 files: `.filtered`/`.raw`/`.score` × every file in the DB), recorded before Part 1 and
again after Part 1 + the backfill + all live testing (including a temporary rename used for the
"unavailable" test in Part 4, restored): **identical, byte-for-byte, both times** — see raw output.

**Item 3 — backfill.** `backend/backfill_pernode.py`, run once: produced `.pernode.npy` for **all 22**
files currently in the DB (`chb13_02`, `chb13_03`, and all 20 synthetic test files under `chb14`/
`chb15`/`chb16`); **0 skipped** — every file already had a cached `.filtered.npy` to reuse. Shapes:
`chb13_02`/`chb13_03` → `[900, 18]` (900 windows × 4 s = 3600 s = 1 h, matches); the 500 s synthetic
files → `[125, 18]`; the 600 s one → `[150, 18]`. All float32.

**Item 4 — consistency gate, run before any UI work.** For `chb13_03` (and `chb13_02`, checked too):
recomputed both the scalar raw recon score (`per_node=False`) and the per-node array (`per_node=True`)
fresh, from the exact cached `.filtered.npy` inputs, in the same process:

| file | max\|pernode.mean(axis=1) − zrecon_raw\| | verdict (< 1e-5) |
|---|---|---|
| chb13_02 | 5.59e-09 | **PASS** |
| chb13_03 | 3.73e-09 | **PASS** |

Ensemble score array unchanged: sha256 match (item 2). Both gates pass — proceeded to the UI.

**Item 5 — added cost.** Isolated the *new* computation (the extra `joint_score(..., per_node=True)`
forward pass) from the unchanged adjacency/band-power loop that dominates Phase B's wall-clock: on
`chb13_03`'s 900 windows (1 h), 5 repeats, CPU —

- scalar (`per_node=False`) call: 74.9 ms
- per-node (`per_node=True`) call: 80.9 ms
- **added cost: ≈ 0.081 s per hour of EEG** (one extra small forward pass through a 2-layer GCN encoder
  + tiny MLP decoder; negligible next to `CLAUDE.md`'s ~15 s/hour baseline, which is dominated by the
  Python adjacency/CAR/WPLI/AEC loop that Part 1 does not touch).

A whole-Phase-B before/after timing (§ raw output) was noisy (±4 s run-to-run on a ~44 s total, i.e. the
adjacency loop's own variance swamps the ~0.07 s/file the isolated measurement above found) — the
isolated per-call measurement is the trustworthy number.

---

## 3 · Attribution definition — provenance of each item

1. **Windows of an event.** Implemented: the windows whose 4 s span `[4i, 4i+4)` overlap `[onset_sec,
   offset_sec]`, always at least the window containing the onset, clamped to the file's window count.
   **This is the thesis definition, not a fallback** — `src/attribution_pipeline.py`, `_blocks_for_
   subject` (line 315, overlap test at lines 342–351: `if int(labels[s0:s1].max()) == 1`), uses the same
   overlap criterion for the thesis's labeled seizures. The demo applies it directly from the event's
   own onset/offset (already known, AI or Human) instead of via a label-derived per-second array — the
   label-free adaptation the demo's architecture requires throughout (`SZSCAN_SPEC_v5.md §1`), not a
   change to the criterion itself.
2. **Aggregation across those windows.** Implemented: arithmetic mean per channel.
   **`PROVISIONAL DEFAULT — Boti to confirm.`** The thesis's own primary aggregation
   (`src/attribution_pipeline.py`, `cmd_score`, line 495, specifically line 520:
   `[("p95", np.percentile(z, 95, axis=0)), ("mean", z.mean(axis=0))]`) is p95 of a **robust z-score**
   computed per channel against an interictal median/MAD baseline (`med`/`mad` at lines 514–515, fit on
   `{subj}_interictal_pernode.npy`). Mean is present in the thesis code too — as the registered
   **secondary/sensitivity** aggregation (`docs/ATTRIBUTION_SPEC.md §9.3`'s "mean aggregation" row, not
   invented for the demo) — but the *primary* p95-robust-z aggregation cannot be reproduced here: its
   baseline is fit on the labeled ictal/interictal split (`{subj}_interictal.npy`/`{subj}_ictal.npy`),
   which `CLAUDE.md`'s guard 3 forbids the demo from ever loading.
3. **Score shown per channel.** Implemented: that aggregated raw per-node reconstruction score,
   unscaled. **`PROVISIONAL DEFAULT — Boti to confirm.`** Same reasoning as item 2 — the thesis's score
   is the robust z-score, not the raw MSE-like value; the raw value is used here because the
   normalization baseline is off-limits. Rank = position by score, highest first (unaffected by status)
   — this part matches the thesis's own `rank[order] = np.arange(1, NCH + 1)` (line 522–523) exactly.

Number format: 5 decimal places (e.g. `0.02584`) — chosen after checking a live event's actual spread
(`0.00730`–`0.02584` on one 4-window event; values within ~1e-4 of each other elsewhere in other
events), where 4 decimals would have collapsed some distinct scores to the same displayed value.

---

## 4 · Part 3 gap-fill decisions

- **Panel position:** a second row below the existing EEG-panel/Event-Panel row, in the same 340px-wide
  right column, natural height (no internal scrollbar) — per Part 3's explicit "don't squeeze panels
  into one viewport." The mockup (`UI/B2a`) shows the panel in its own bounded, internally-scrolled box;
  this is a deliberate, prompt-mandated deviation from the mockup's literal scroll behaviour, not an
  oversight.
- **Default status state:** unset (neither Accept nor Reject) for every channel until Save — the mockup
  shows a mixed sample state (some Accept, some Reject, some neither) that reads as illustrative sample
  data, not a documented default; §6.7 doesn't specify one. Flagged per the prompt's instruction.
- **Gradient mapping:** continuous min–max scaling across the event's own 18 scores per Part 3's
  explicit formula (all-equal → low end) — a continuous 3-stop `attrColorAt(t)` interpolation, not a
  bucketed/discrete 3-level mapping, even though the design doc names exactly 3 levels (low/mid/high)
  as anchor points on the gradient.
- **Two-way hover:** implemented (table row ↔ line), built cheaply on top of one `hoveredChannel` state
  variable shared by both the SVG and the table — did not risk any required part. Verified live (§6).
- **Unavailable state:** `{"available": false, ...}` returned with HTTP 200 (not 404) from `GET .../
  attribution`, so the frontend can distinguish "no data for this file" (neutral message) from a real
  request failure (error text) — 404 is reserved for "the event/file id itself doesn't exist."
- **Head diagram electrode count:** 19 distinct electrodes for CHB-MIT's 18 bipolar channels (FP1, FP2,
  F7, F3, FZ, F4, F8, T7, C3, CZ, C4, T8, P7, P3, PZ, P4, P8, O1, O2) — `SZSCAN_SPEC_v5.md §6.7`'s "18
  electrode positions" is read loosely per the prompt's own note; small labelled circles mark them as a
  background reference only, the 18 **lines** are the data marks.
- **Electrode layout:** a simplified 5-row schematic (not a true stereographic 10-20 projection) —
  matches the mockup's own style, which uses the same row-grid layout rather than a precise angular
  projection.

---

## 5 · Part 4 — live verification, with evidence

All items below were exercised live via `claude-in-chrome` against the running app
(`http://localhost:5173` / backend `:8000`), not inferred from code reading alone, except where noted.

1. **Consistency gate** — §2 above (sha256 before/after table, added-cost numbers, backfill list).
2. **Independent recomputation**, done for one AI event and one disposable Human event, both matching
   the live API exactly:
   - AI event 46 (`chb13_03`, onset 80–164 s): window range `[20, 40]`; top 3 —
     `FP2-F8 0.019047`, `FP1-F7 0.018311`, `FP2-F4 0.01799` — **API and independent Python recompute
     from `.pernode.npy` agree exactly.**
   - Disposable Human event (created for this test, see item 6): window range `[29, 31]` at its first
     range, top 3 `FZ-CZ 0.016351 / FP2-F4 0.014963 / C4-P4 0.014425` — **exact match**; after Edit
     (range moved), window range `[21, 24]`, top 3 `P4-O2 0.02584 / FP2-F8 0.024594 / FP2-F4 0.023642`
     — **exact match again.**
3. **Empty state:** on first opening `chb13_03.edf`, panel text is exactly `Select an event to view
   attribution`, no event preselected (confirmed via DOM query, not just visually).
4. **AI event select:** title `Channel-level reconstruction anomaly — Event 1` with correct N; DOM count
   of `<line>` elements in the head diagram = **18**, each verified programmatically to connect the
   exact electrode-pair coordinates for its channel name (all 18 matched, 0 mismatches); table 18 rows,
   rank 1…18 descending by score; table values equal the API response exactly.
5. **Colours:** sampled `stroke`/`stroke-opacity` of all 18 `<line>` elements — highest-scoring channel
   (`FP2-F8`, rank 1) = `#0f766e` (exact high-end token); full set of 18 stroke colours spans
   `#0f766e`…`#cbd5e1`-family hex values only — **zero** red/yellow/green/blue anywhere in the panel
   (grep of the rendered set confirmed no `#DC2626`/`#FFE262`/`#16A34A`/`#2563EB`-family value present).
6. **Disposable Human event** created via Select Range on `chb13_03.edf` (onset ≈116.05 s, offset
   ≈126.65 s) — Alert went `1 → 2` in the header (matches SPEC §6.6). Selected it: panel showed
   attribution matching the independent recompute (item 2). Used **Edit** to redraw its range (onset
   ≈87.78 s, offset ≈98.38 s via the real 2-click Select Range flow) — panel **re-fetched automatically**
   (title stayed `Event 2`, table/diagram updated to the new window `[21,24]`, matching a fresh
   independent recompute). Deleted it — Alert went `2 → 1`, panel returned to the exact empty-state text,
   and (checked directly in SQLite) both the `events` row and its `attribution_status` row for that event
   id were gone.
7. **Segmented control:** set `P4-O2` (rank 1) → Reject, `FP2-F8` (rank 2) → Accept. Reject dropped that
   line's rendered opacity to exactly `0.35` (DOM-verified: one `<line>` at `stroke-opacity="0.35"`,
   stroke `#0f766e`, the rest at `1`) while keeping its score colour. **Save** → confirmed via API the
   stored set now has exactly those two entries → **reloaded the whole page**, re-navigated, reselected
   the event → statuses were back (`P4-O2: Reject`, `FP2-F8: Accept`, both buttons showing the correct
   active colour). **Clear all** (no Save yet) → confirmed via API the stored set was **still** the old
   two entries (Clear all is local-only until Save, per spec) → **Save** → confirmed via API the stored
   set is now empty, and rank order (1…18) was unchanged by any of this throughout.
8. **Deleting an event removes its attribution rows** — checked directly in the SQLite `attribution_
   status` table (not just via the API) before and after: 1 row → 0 rows, exact match to the deleted
   event id. Also checked the whole table is empty DB-wide at final cleanup (§7).
9. **Wording scan:** grepped `AttributionPanel.jsx`, `attributionStyle.js`, `attribution.py`, `main.py`
   for causing/cause/seizure focus/focus/origin/source of seizure/localiz\*/onset zone/SOZ/contributes
   and for AUROC/p-value/confidence interval/accuracy — **zero hits in any user-visible string.** The
   only match was a code *comment* in `AttributionPanel.jsx` explicitly stating "NOT localization, NOT
   SOZ" (the negation, not a violation) and unrelated CORS-`origin` matches in `main.py`.
10. **Literal screenshot comparison** with `UI/B2a` — see `CC_STEP7_SCREENSHOTS/panel_ai_event_full.jpg`
    vs. the mockup crop. Matches: panel position (right column, below Event Panel), colorbar above the
    head diagram, table columns (Rank/Channel/Score/Status), Save+Clear all at the bottom. **Differences,
    listed honestly:**
    - Title is one combined string (`Channel-level reconstruction anomaly — Event N`) vs. the mockup's
      two-part header (`Channel contribute to ... | Event N`) — **required by spec §6.7**, not a build
      choice.
    - Head-diagram connecting lines are straight in the build; the mockup's lines read as slightly
      curved/arced polylines along the scalp perimeter — **required by SZSCAN_SPEC_v5.md §6.7 /
      CC_STEP7_PROMPT.md Part 3's explicit "18 straight lines"** wording, a deliberate scientific
      correction (bipolar data), not a rendering gap.
    - Status buttons are rectangular rounded-control buttons (reusing the same button style as
      `PanelEvent.jsx`'s existing AI-review Accept/Reject/Uncertain buttons) rather than the mockup's
      fully-rounded pill shape — a minor, unflagged-in-spec styling choice made for visual consistency
      with the rest of the app rather than mockup-for-mockup's-sake; not required by any written doc.
    - The panel does not internally scroll (mockup does) — **required by Part 3**, see §4 above.
11. **Regression (quick, live):**
    - Select Range create/delete still works, Alert +1/−1 exactly as before (item 6, reused as the
      regression check — same underlying code path, untouched by this step).
    - Mini-timeline dimming rule: with an event selected, DOM-checked block opacities — exactly the
      selected event's blocks at `opacity: 1`, every other block at `opacity: 0.4` (2 vs 3 in a 5-block
      file, matching the file's own 5 events) — unchanged from Step 6.
    - Header title format unchanged (`CHB13_03 (0N alerts to check)`), Event Panel filter/count
      (`Filter: All`, bare count) unchanged, mini-timeline blocks (red/yellow solid, no hatch) unchanged.
    - No code in `PanelEvent.jsx`, `eventStyle.js`, `MiniTimeline.jsx`, `EegPanel.jsx` was touched this
      step (git diff confirms), so these are true regression checks, not just re-reading unmodified code.
12. **Unavailable state — genuine live gap, not just code review.** Temporarily moved
    `uploads/chb16/chb15_01_short.pernode.npy` aside, reloaded the app, selected the event on that file:
    panel showed exactly `Attribution is not available for this file.` with the title still correct
    (`Event 1`), confirmed both via the raw API response (`{"available": false, ...}`) and in the
    rendered DOM. Restored the file immediately after (sha256-verified unchanged from before the move —
    see §2's "both times" sha256 check) and confirmed attribution became available again.
13. **Cleanup — final state, verified:**
    - `chb13_03.edf` / `chb13_02.edf`: **zero** Human events (DB query: `SELECT COUNT(*) FROM events
      WHERE source='Human'` → **0**, checked DB-wide, not just for chb13).
    - The 4 real AI events on `chb13_03.edf` (ids 46–49): review states exactly
      `Reject/Reject/Uncertain/Reject` — unchanged from the Pre-step A dump.
    - `attribution_status` table: **0 rows DB-wide** (the test statuses set on event 46 during backend
      endpoint testing, and on the disposable Human event, were both cleared/deleted in the course of
      testing — verified by direct SQLite query, not inferred).
    - `chb13` subject Alert back to **1**, `chb13_02.edf` Alert **0**, `chb13_03.edf` Alert **1** —
      confirmed live in the Database screen after a fresh page load.
    - Pre-step B's Accepted synthetic event (chb16/id 54) intentionally left Accepted, as authorized —
      not part of this cleanliness check (synthetic file, irreversible by design).

---

## 6 · Test-state note (end of Step 7)

- `chb13_02.edf` (file 10): 0 events.
- `chb13_03.edf` (file 11): 4 AI events, ids 46–49, review states `Reject/Reject/Uncertain/Reject`
  (identical to Pre-step A's dump — untouched throughout Step 7). 0 Human events. Alert 1.
- `chb13` subject Alert: 1.
- Synthetic test files (`chb14`/`chb15`/`chb16`): unchanged except one deliberate, authorized, permanent
  change — event id 54 (`chb16`/`chb15_12_short.edf`) is now `Accept` (was `Unseen`), per Pre-step B.
  Every other AI event's review state on those files is unchanged.
- `attribution_status` table: empty, DB-wide.
- Every file in the DB now has a `.pernode.npy` cache (22/22); no existing cache file's bytes changed at
  any point (verified sha256-identical at the start, after Part 1, and again after all live testing —
  three checkpoints, all identical).
- `bme11/`, `rank_readout.py`, `results/attribution_v7/rank_readout_perseizure.csv`,
  `results/attribution_v7/rank_readout_summary.txt` are **pre-existing untracked files from before this
  session** (present in the initial `git status` this session was handed) — not created or touched by
  Step 7.

---

## 7 · Raw command output

### Guard tests (final run)
```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
collected 4 items

web_demo/backend/tests/test_guards.py::test_guard_no_build_timeline_masked PASSED [ 25%]
web_demo/backend/tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED [ 50%]
web_demo/backend/tests/test_guards.py::test_guard_no_labeled_npy PASSED  [ 75%]
web_demo/backend/tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED [100%]

============================== 4 passed in 2.14s ==============================
```

### git status (final)
```
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
	modified:   web_demo/SZSCAN_SPEC_v5.md
	modified:   web_demo/backend/db.py
	modified:   web_demo/backend/main.py
	modified:   web_demo/backend/pipeline_demo.py
	modified:   web_demo/backend/pipeline_worker.py
	modified:   web_demo/frontend/src/api.js
	modified:   web_demo/frontend/src/screens/AnalysisScreen.jsx

Untracked files:
	bme11/                                                      <- pre-existing, not from Step 7
	rank_readout.py                                             <- pre-existing, not from Step 7
	results/attribution_v7/rank_readout_perseizure.csv          <- pre-existing, not from Step 7
	results/attribution_v7/rank_readout_summary.txt             <- pre-existing, not from Step 7
	web_demo/CC_STEP7_SCREENSHOTS/
	web_demo/backend/attribution.py
	web_demo/backend/backfill_pernode.py
	web_demo/frontend/src/attributionStyle.js
	web_demo/frontend/src/components/AttributionPanel.jsx
```

### git diff --stat (final)
```
 web_demo/SZSCAN_SPEC_v5.md                       | 40 ++++++++++++++++++++-
 web_demo/backend/db.py                           | 45 +++++++++++++++++++++++-
 web_demo/backend/main.py                         | 39 ++++++++++++++++++++
 web_demo/backend/pipeline_demo.py                | 28 +++++++++++++--
 web_demo/backend/pipeline_worker.py              | 14 +++++++-
 web_demo/frontend/src/api.js                     | 10 ++++++
 web_demo/frontend/src/screens/AnalysisScreen.jsx | 16 +++++++++
 7 files changed, 186 insertions(+), 6 deletions(-)
```
Confirms **nothing outside `web_demo/` changed**.

### Backfill script output
```
[chb13] running Phase B model-scoring for ['chb13_02.edf', 'chb13_03.edf'] (pernode only — ensemble score result discarded, never written)
  wrote chb13\chb13_02.pernode.npy  shape=(900, 18)  dtype=float32
  wrote chb13\chb13_03.pernode.npy  shape=(900, 18)  dtype=float32
[chb14] running Phase B model-scoring for 6 files (pernode only — ensemble score result discarded, never written)
  wrote chb14\chb15_0{1..6}_short.pernode.npy  shape=(150 or 125, 18)  dtype=float32
[chb15] running Phase B model-scoring for 2 files
  wrote chb15\chb15_01_short.pernode.npy  shape=(150, 18)
  wrote chb15\chb15_02_short.pernode.npy  shape=(125, 18)
[chb16] running Phase B model-scoring for 12 files
  wrote chb16\chb15_0{1..9}_short.pernode.npy / chb15_1{0..2}_short.pernode.npy  shape=(150 or 125, 18)

=== backfill_pernode summary ===
produced (22): [listed — chb13×2, chb14×6, chb15×2, chb16×12]
skipped (0):
```

### sha256 before/after (Part 1) and final (after all live testing)
`CC_STEP7_SCREENSHOTS/sha256_before.txt`, `sha256_after.txt`, `sha256_final.txt` — all three `diff`
clean against each other (70 cache files: every `.filtered.npy`/`.raw.npy`/`.score.npy` under
`web_demo/backend/uploads/`).

### Consistency gate
```
chb13_02.edf max|pernode.mean(axis=1) - zrecon_raw| = 5.587935447692871e-09 (expect < 1e-5)
  matches on-disk backfilled .pernode.npy exactly: True
chb13_03.edf max|pernode.mean(axis=1) - zrecon_raw| = 3.725290298461914e-09 (expect < 1e-5)
  matches on-disk backfilled .pernode.npy exactly: True
```

### Added-cost isolation
```
n_windows=900  hours=1.0000
scalar per_node=False call: 74.9 ms
pernode per_node=True call: 80.9 ms
added cost per file: 80.9 ms -> 0.081 s/hour of EEG
```
