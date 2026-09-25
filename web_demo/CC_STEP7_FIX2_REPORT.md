# CC_STEP7_FIX2_REPORT.md — Step 7, fix round 2: attribution scoring definition

Executed `CC_STEP7_FIX2_PROMPT.md` in full, in order, live-verified via `claude-in-chrome` (confirmed
connected before starting). No `git add`/`commit`/`push` run. No Save clicked on any real `chb13` event
or its attribution status; no event created/edited/deleted on `chb13` this round. Guards 4/4 green
throughout (baseline, after Parts 1–2, and after all live testing).

---

## 1 · Summary

Closed both PROVISIONAL defaults from `CC_STEP7_REPORT.md` §3 (aggregation + score shown): the panel now
shows `score = percentile(|robust-z|, 95, axis=0)`, robust-z computed per channel against a **persisted,
whole-subject** median/MAD baseline — the exact formula in `src/attribution_pipeline.py`'s `cmd_score`
(confirmed line 519 does `np.abs(...)` before the p95 at line 520), differing only in baseline scope
(whole-subject recording, not interictal-only — the same divergence already in `SZSCAN_SPEC_v5.md`
§1.6, now item 1, not a new one).

**Files changed this round:** `web_demo/backend/attribution.py`, `pipeline_demo.py`,
`pipeline_worker.py`, `backfill_pernode.py`, `web_demo/SZSCAN_SPEC_v5.md`, `web_demo/CLAUDE.md`,
`web_demo/THESIS_CONTEXT_FOR_DEMO.md`, `web_demo/PROJECT2_SETUP.md`, and (per Part 3's one permitted
exception) `web_demo/frontend/src/components/AttributionPanel.jsx` — one formatting call only
(`.toFixed(5)` → `.toFixed(2)`), nothing else in that file. No other file in the "do not touch" list was
edited (confirmed by `git diff --stat`, §8, and by the fact `AttributionPanel.jsx`'s diff is a single
line — see §4).

**One out-of-scope observation, not acted on:** `chb13_03.edf` now has a 5th event (id 86, Human,
onset≈1077.0 s / offset≈2247.3 s, non-integer seconds — evidently drawn live via Select Range by someone
since `CC_STEP7_FIX_REPORT.md` was written) that neither prior report mentions. It renumbers as `Event 2`
in onset order. Not touched, not counted in any gate below (gates use the 4 real AI events, ids 46–49, as
the prompt specifies) — flagged here only because it's a change in DB state neither of us made.

---

## 2 · Formula + baseline file format chosen

**Formula**, implemented exactly as specified in `attribution.py`'s `get_event_attribution`:

```python
med, mad = baseline[0], baseline[1]              # persisted, whole-subject
z = np.abs((window_scores - med) / mad)          # [k, 18], per window per channel
per_channel = np.percentile(z, 95, axis=0)       # [18], event-level score
order = np.argsort(-per_channel)                 # rank from the UNROUNDED score
```

`med`/`mad` are computed by the new `pipeline_demo.compute_pernode_baseline()`:
`med = median(base, axis=0)`, `mad = median(|base-med|, axis=0) + 1e-9` (no 1.4826 factor), where `base`
is the concatenation of every window of every `.pernode.npy` array passed in.

**Baseline scope — where "every file belonging to the subject" comes from.** Rather than gathering files
from the DB at read time, the baseline is fit inside `process_subject_phase_b` from exactly the same
`filenames_sorted` set already used there for the existing subject-wide z-score/LedoitWolf/robust-z fits
(Part 1's "don't special-case attribution"). This is correct for this codebase because
`SZSCAN_SPEC_v5.md §5.5` — "**There is no Edit mode.** To make a change → delete the whole subject and
re-create it" — means a subject's Phase B session always contains *every* file that will ever belong to
that subject's final on-disk set; there is no incremental-add path whose omission this round needed to
special-case.

**On-disk layout chosen:** stacked `[2, 18]` float32, one file per subject — `row 0 = median`,
`row 1 = MAD (already +1e-9)` — named `pernode_baseline.npy` (constant
`pipeline_demo.PERNODE_BASELINE_FILENAME`), persisted at `uploads/{subject_id}/pernode_baseline.npy`,
next to `.filtered.npy`/`.raw.npy`/`.score.npy`/`.pernode.npy`.

**Naming deviation from the prompt's illustrative `{subj}.pernode_baseline.npy`, stated plainly:** the
file itself carries no subject prefix — it's a fixed literal name, `pernode_baseline.npy`. Reason: at the
point `pipeline_worker.py`'s `_run_phase_b` writes it (inside the still-draft, session-id-keyed
directory), the subject id (Project ID) is not yet known — it stays editable until `start_process`
locks it in (`upload_manager.py`, out of scope this round). This is the *exact same reason*
`.pernode.npy`/`.filtered.npy` don't embed the subject name either: the file rides along when
`_finalize_draft_dir` (upload_manager.py, untouched) moves the whole draft directory to
`uploads/{subject_id}/`, and the subject identity comes from that directory, not the filename. Kept the
`{subj}/` **directory** as the namespacing exactly like every other per-file cache — just not repeated a
second time inside the filename.

**Where it's computed — "Phase B" vs. writer location:** the actual median/MAD arithmetic runs inside
`pipeline_demo.process_subject_phase_b` (a new `pernode_baseline_out` optional dict, populated right
after the per-file loop that already builds `pernode_out`, mirroring `zrecon_out`'s pattern) — genuinely
in Phase B, not deferred to a later step. `pipeline_worker.py`'s `_run_phase_b` then writes it to disk in
the same call that writes each file's `.pernode.npy`. `upload_manager.py` (the file that actually knows
the subject id, via `_finalize_draft_dir`) was **not** touched — it wasn't on the editable list this
round, and wasn't needed: the directory-rename mechanism it already has for `.pernode.npy` carries the
baseline file along automatically, with no changes to that file required.

**Never recomputed on read:** `attribution.py` only ever `np.load`s the persisted file; there is no code
path that computes med/mad from a live event request.

---

## 3 · Backfill output

Ran `python backfill_pernode.py --baseline` (the new, separate `backfill_baselines()` function — does
not touch `main()`'s existing per-node backfill). Read only already-cached `.pernode.npy` files; no
model call, no EDF read, no CPD, no `events` table write.

```
  wrote chb13\pernode_baseline.npy  shape=(2, 18)  dtype=float32  (from 2 files)
  wrote chb14\pernode_baseline.npy  shape=(2, 18)  dtype=float32  (from 6 files)
  wrote chb15\pernode_baseline.npy  shape=(2, 18)  dtype=float32  (from 2 files)
  wrote chb16\pernode_baseline.npy  shape=(2, 18)  dtype=float32  (from 12 files)

=== backfill_baselines summary ===
produced (4):
  chb13\pernode_baseline.npy
  chb14\pernode_baseline.npy
  chb15\pernode_baseline.npy
  chb16\pernode_baseline.npy
skipped (0):
```

All 4 subjects currently in the DB got a baseline (matches the prompt's expectation exactly:
`chb13`/`chb14`/`chb15`/`chb16`), 0 skipped — every file already had a cached `.pernode.npy` from the
original Step 7 backfill (22/22, confirmed present before running).

---

## 4 · Part 3 finding — frontend touched?

**Yes, touched — the one permitted exception, exactly as anticipated.** The 5-decimal formatting was
hardcoded in `AttributionPanel.jsx` (`{r.score.toFixed(5)}`, table `<td>`), not applied at the API layer
— `attribution.py` already returns `round(float(per_channel[i]), 6)`, a 6-decimal internal value the
frontend was truncating for display. Changed only that one call to `.toFixed(2)`. Nothing else in
`AttributionPanel.jsx` was touched (no layout, no colour, no structure) — confirmed by the file's diff
being exactly this one line (the file is untracked/new since Step 7, so `git diff` doesn't show it by
name in `--stat`, but the edit tool's own change record is one `old_string`/`new_string` pair, and a
fresh read of the file shows only that line differs from before this round).

Live-confirmed: the rendered table for event 46 shows `FP1-F7 3.35`, `T8-P8 2.72`, `P3-O1 2.72`, etc. —
2 decimal places, `|z|` already non-negative so no sign-formatting issue (screenshot,
`CC_STEP7_FIX2_SCREENSHOTS/event46_table_2decimal.png`).

---

## 5 · Gate results

All five run against the **live app** (`http://localhost:5173` / backend `:8000`), `chb13_03.edf`, the 4
real AI events (ids 46–49).

### 1 · Independent recompute

Read-only Python script, loading `uploads/chb13/chb13_03.pernode.npy` and
`uploads/chb13/pernode_baseline.npy` directly, applying the exact formula in §2, for all four events:

| event | window range | independent top-3 (channel, score) |
|---|---|---|
| 46 | [20, 40] (n=21) | FP1-F7 3.350886, T8-P8 2.724104, P3-O1 2.717306 |
| 47 | [605, 605] (n=1) | P3-O1 6.643456, C3-P3 4.042337, F4-C4 1.943111 |
| 48 | [700, 700] (n=1) | P4-O2 2.812184, CZ-PZ 2.683548, FP2-F8 2.389792 |
| 49 | [860, 860] (n=1) | T8-P8 3.705338, FP2-F4 2.244753, F7-T7 1.981768 |

Live API (`fetch('/api/events/{id}/attribution')`, authenticated session) for the same four events
returned, top-3, **exactly**: 46 → `FP1-F7 3.350886 / T8-P8 2.724104 / P3-O1 2.717306`; 47 →
`P3-O1 6.643456 / C3-P3 4.042337 / F4-C4 1.943111`; 48 → `P4-O2 2.812184 / CZ-PZ 2.683548 /
FP2-F8 2.389792`; 49 → `T8-P8 3.705338 / FP2-F4 2.244753 / F7-T7 1.981768`. **Exact match on all four
events**, well inside the ≤0.005 (2-decimal-display) tolerance — in fact identical to 6 decimals, since
both sides run the same numpy operations on the same on-disk arrays.

### 2 · sha256 (three checkpoints)

`.filtered.npy`/`.raw.npy`/`.score.npy` under `web_demo/backend/uploads/` — 70 files, same set as Step 7:

- **Checkpoint 1** (before Part 1/2): `CC_STEP7_FIX2_SCREENSHOTS/sha256_before.txt`
- **Checkpoint 2** (after Part 1/2 code + backfill): `CC_STEP7_FIX2_SCREENSHOTS/sha256_after_part1_2.txt`
- **Checkpoint 3** (after all live testing, including the temporary baseline-file move/restore for the
  unavailable-state test): `CC_STEP7_FIX2_SCREENSHOTS/sha256_final.txt`

`diff` clean across all three — **byte-identical throughout**. (The new `pernode_baseline.npy` files
themselves are not in this guarded set — by design, same as `.pernode.npy` — but the temporary
move/restore of `uploads/chb13/pernode_baseline.npy` used for the unavailable-state test was itself
sha256-verified unchanged before/after: `a34d7037d39219dafaa4773134f7b1ef35650f3ce3cd5d33b8e923bd2ca95fa0`.)

### 3 · Guard tests

4/4 green — raw output in §8, run at baseline, after code changes, and as the final check.

### 4 · Ranking genuinely changed

| event | old top-3 (mean-of-raw, `CC_STEP7_REPORT.md`/`CC_STEP7_FIX_REPORT.md`) | new top-3 (p95 \|robust-z\|, this round) |
|---|---|---|
| 46 | FP2-F8, FP1-F7, FP2-F4 | **FP1-F7, T8-P8, P3-O1** — only FP1-F7 survives, reordered |
| 47 | P3-O1, C3-P3, P4-O2 | **P3-O1, C3-P3, F4-C4** — rank 1–2 hold, rank 3 channel changes |

Event 46 (used for item 1 above) and event 47 (second event, as required) both show a real change from
raw-score to p95-|z| ranking — most visibly on 46, where 2 of the old top-3 channels drop out entirely.
Not just claimed: both rows are the same independently-recomputed/API-matched values from item 1.

### 5 · Display-collapse check

Full 18-row API response for all four events, grouped by 2-decimal display value:

- **Event 46:** 2 collision pairs — `T8-P8 2.724104` / `P3-O1 2.717306` (both display `2.72`, unrounded
  gap 0.0068) and `C3-P3 1.944977` / `F4-C4 1.940478` (both display `1.94`, gap 0.0045). Both pairs are
  **genuinely close internally** (gaps ≪ the event's overall spread, e.g. rank 1's 3.35 vs rank 18's
  ~1.0) — not an over-rounding artifact hiding a larger real difference.
- **Events 47, 48, 49:** **zero** 2-decimal collisions among their 18 rows each.

No case of two channels displaying the same 2-decimal number while their unrounded scores were actually
far apart.

---

## 6 · Spec-doc diffs

**`SZSCAN_SPEC_v5.md`:**
- History line: added **C21** entry recording this round's closure + §1.6 restructure.
- §6.7's intro sentence ("The label-scored result is currently PROVISIONAL") changed to "closed
  (2026-09-25): blind human-reader labels, approved, result negative" — this is the same fact Part 7
  closes in the other two docs; leaving it stale here would have contradicted them, so it was corrected
  as part of this file's own edit rather than left inconsistent (a small addition beyond Part 5's literal
  item list, flagged here rather than silently done).
- **C20 items 2–3** rewritten from "PROVISIONAL DEFAULTS: arithmetic mean, unscaled raw score" to the
  closed p95-|robust-z| formula, citing `src/attribution_pipeline.py` lines ~514–520 and the §1.6 item 1
  divergence.
- **C20 item 4** (not explicitly requested by Part 5, but the item 2–3 rewrite made its old wording —
  "computed fresh from this array... never cached" — read as if only `.pernode.npy` mattered)
  extended to also describe `pernode_baseline.npy`'s persistence, once-per-subject computation, and the
  missing-baseline fallback. Flagged as a judgment call, not a literal Part 5 ask.
- **§1.6** restructured from two lettered groups, (a)/(b), into **exactly three numbered items**:
  1. Normalization statistics, covariance (LedoitWolf), and robust-z fit on the whole recording, no
     artifact rejection — the Channel Attribution Panel's baseline (this round) added as a table row
     under this same item, per the prompt's instruction.
  2. No post-ictal buffer exclusion (unchanged content, renumbered from (b)).
  3. **New item, not previously its own numbered entry in §1.6**: background statistics for the PELT
     penalty and the CPD threshold, estimated on the whole recording. Sourced from
     `src/cpd_pipeline_v14.py`'s own header docstring (penalty variance "from the interictal/background";
     threshold "calibrated from background CP magnitudes"; and explicitly, for the no-mask/label-free
     case, "PELT variance and the magnitude threshold from the WHOLE recording") plus §1.5's existing
     "needs enough background to estimate stably" line. This item was **not** separately measured against
     an AUROC/Spearman-style criterion the way item 1's `zlatent` row was — the report says so plainly
     rather than implying it was checked.
  All existing evidence (the chb06/chb13 AUROC/Spearman table, the post-ictal justification, the prepared
  committee answer) kept verbatim — this was re-grouping, not a rewrite, per the prompt's instruction.
  Two stale cross-references (`§1.6a`, `§1.6b`) elsewhere in the file — in this round's own new C20 item 4
  text, and in the pre-existing §8 table row O4b — were updated to point at the new item numbers.

**`CLAUDE.md`:** replaced "~16.9 ms per 4 s window ⇒ ~15 s per hour of EEG" with the true end-to-end
figure, **9.76 s/hour of EEG** (measured on `chb06_01.edf`, CPU, Step 1, `BUILD_PROGRESS.md`), kept the
**~5×** run-to-run variance caveat (traced to `BUILD_PROGRESS.md`'s original Step-1 note: "22–110 s on the
adjacency + band-power stage on identical code, same file"), and kept the 13.2 ms + 3.7 ms = 16.9 ms/
window component breakdown but relabeled it explicitly as component-level (from `SZSCAN_SPEC_v5.md
§1.7`), not the end-to-end figure.

**`THESIS_CONTEXT_FOR_DEMO.md` §5 + `PROJECT2_SETUP.md` §9.2(B):** both changed from "PROVISIONAL" /
a forward-looking "if PROVISIONAL is removed" conditional to a plain statement that the attribution
evaluation is closed, blind-reader-labeled, approved, and negative. No numeric evaluation figure was
present in either file to remove (checked by grep for AUROC/accuracy/percentage terms near both
sections) — only the PROVISIONAL wording itself needed correcting. The panel's own UI wording (title,
no-metric-on-screen rule) is untouched in both files, as required.

---

## 7 · Manual pre-step confirmation

Per Part 8: Boti clears event 46's 18 `attribution_status` rows by hand before this round runs — **not
this session's job, and not done by this session.** Confirmed live (before any Part 1/2 code ran, and
again at the end): `SELECT event_id, COUNT(*) FROM attribution_status GROUP BY event_id` returns **zero
rows, DB-wide** — event 46 already had no saved statuses when this round started, consistent with the
manual pre-step having been carried out (or the table simply being empty going in). No attribution-status
Save was clicked on any real `chb13` event this round.

---

## 8 · Raw command output

### Guard tests (final run)
```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
collected 4 items

tests/test_guards.py::test_guard_no_build_timeline_masked PASSED         [ 25%]
tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED     [ 50%]
tests/test_guards.py::test_guard_no_labeled_npy PASSED                   [ 75%]
tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED       [100%]

============================== 4 passed in 2.23s ==============================
```

### git status (`web_demo/` only)
```
 M web_demo/CLAUDE.md
 M web_demo/PROJECT2_SETUP.md
 M web_demo/SZSCAN_SPEC_v5.md
 M web_demo/THESIS_CONTEXT_FOR_DEMO.md
 M web_demo/backend/db.py                       <- from EARLIER rounds, not this one
 M web_demo/backend/main.py                     <- from EARLIER rounds, not this one
 M web_demo/backend/pipeline_demo.py            <- Part 1 this round
 M web_demo/backend/pipeline_worker.py          <- Part 1 this round
 M web_demo/frontend/src/api.js                 <- from EARLIER rounds, not this one
 M web_demo/frontend/src/screens/AnalysisScreen.jsx   <- from EARLIER rounds, not this one

Untracked (unchanged set from earlier rounds, plus this round's own new files):
  web_demo/CC_STEP7_FIX2_PROMPT.md
  web_demo/CC_STEP7_FIX2_SCREENSHOTS/
  web_demo/backend/attribution.py                <- content edited this round (Part 1), file itself from Step 7
  web_demo/backend/backfill_pernode.py           <- content edited this round (Part 2), file itself from Step 7
  web_demo/frontend/src/components/AttributionPanel.jsx  <- 1 line edited this round (Part 3)
  (bme11/, rank_readout.py, results/attribution_v7/*, STEP8_9_PREDEFENSE_CHECKLIST.md,
   web_demo/CC_STEP7*_PROMPT.md/_REPORT.md, web_demo/CC_STEP7*_SCREENSHOTS/ — all pre-existing,
   not touched by this round)
```

### git diff --stat (tracked files only)
```
 web_demo/CLAUDE.md                               |  8 +-
 web_demo/PROJECT2_SETUP.md                       |  7 +-
 web_demo/SZSCAN_SPEC_v5.md                       | 99 +++++++++++++++++++++---
 web_demo/THESIS_CONTEXT_FOR_DEMO.md              |  8 +-
 web_demo/backend/db.py                           | 45 ++++++++++-
 web_demo/backend/main.py                         | 39 ++++++++++
 web_demo/backend/pipeline_demo.py                | 82 +++++++++++++++++++-
 web_demo/backend/pipeline_worker.py              | 27 ++++++-
 web_demo/frontend/src/api.js                     | 10 +++
 web_demo/frontend/src/screens/AnalysisScreen.jsx | 77 +++++++++++-------
 10 files changed, 348 insertions(+), 54 deletions(-)
```
`db.py` (45), `main.py` (39), `api.js` (10), `AnalysisScreen.jsx` (77) are **byte-identical diff sizes**
to `CC_STEP7_FIX_REPORT.md`'s own final numbers — confirming those four files were not touched this
round. Only `CLAUDE.md`, `PROJECT2_SETUP.md`, `SZSCAN_SPEC_v5.md`, `THESIS_CONTEXT_FOR_DEMO.md`,
`pipeline_demo.py`, `pipeline_worker.py` changed (tracked files), plus the untracked
`attribution.py`/`backfill_pernode.py`/`AttributionPanel.jsx` content edits noted above.

### Backfill baseline output
```
  wrote chb13\pernode_baseline.npy  shape=(2, 18)  dtype=float32  (from 2 files)
  wrote chb14\pernode_baseline.npy  shape=(2, 18)  dtype=float32  (from 6 files)
  wrote chb15\pernode_baseline.npy  shape=(2, 18)  dtype=float32  (from 2 files)
  wrote chb16\pernode_baseline.npy  shape=(2, 18)  dtype=float32  (from 12 files)

=== backfill_baselines summary ===
produced (4):
  chb13\pernode_baseline.npy
  chb14\pernode_baseline.npy
  chb15\pernode_baseline.npy
  chb16\pernode_baseline.npy
skipped (0):
```

### Independent recompute vs. live API (event 46, full precision)
```
independent: FP1-F7 3.350886, T8-P8 2.724104, P3-O1 2.717306, P7-O1 2.694453, P4-O2 2.33349, ...
live API:    FP1-F7 3.350886, T8-P8 2.724104, P3-O1 2.717306, P7-O1 2.694453, P4-O2 2.33349, ...
```

### sha256 — 70 files, 3 checkpoints, all identical
See `CC_STEP7_FIX2_SCREENSHOTS/sha256_before.txt`, `sha256_after_part1_2.txt`, `sha256_final.txt`.
