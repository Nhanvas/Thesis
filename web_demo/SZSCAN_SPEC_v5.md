# SZSCAN_SPEC_v5.md — locked for BUILD

**Status: LOCKED.** This file **fully replaces** `WEB_DEMO_SPEC_v4.md` and
`WEB_DEMO_CONTEXT_BOUNDARY.md`. Both files have moved to `docs/archive/demo_v4/`, **do not use them for
code**.

**Authority order for everything related to the web demo:**
`UI/` (locked PNGs — wins on everything visible) > this file (behavior/logic/data boundaries) >
`SZSCAN_DESIGN_v2.md` (color/type/spacing tokens) > `DEMO_BUILD_HANDOFF.md` (stack/process).

For scientific decisions (not demo ones), authority remains
`docs/RESULTS_OF_RECORD_phaseB.md` > `docs/PROVENANCE.md` > `docs/REPO_MAP.md`.

**History:** v5 = v4 + 11 UI lock-in points (2026-09 audit session) + 13 fix points M1–M13 (this
session) + continuous label-free architecture (new, measurement-based — see §1) + **C17** (2026-09,
after the audit report: the Start date column changed from an absolute date to `Recording N,
HH:MM:SS` — see §5.1) + **C18** (2026-09-21, after Step 5 fix round 2: the Panel EEG amplitude scale
extended per real measured data — see §6.4) + **C19** (2026-09-24, after Step 6: five Select Range /
header behaviours the spec did not describe are recorded — see the note after §6.6; the same pass also
corrects a stale `edf_index.locate_range()` reference in §5.5) + **C20** (2026-09-24, after Step 7: the
Channel Attribution Panel's window/aggregation/score definition, gradient mapping and per-channel
status persistence are recorded — see the note after §6.7) + **C21** (2026-09-25, after Step 7 fix
round 2: C20 items 2-3's PROVISIONAL aggregation/score closed to the final p95-|robust-z| formula
against a persisted whole-subject baseline, and §1.6 restructured into 3 numbered divergence items —
see the note after §6.7 and §1.6). + **C26-C28** (2026-09-28 → 10-02: mini-timeline paging past 1 h, Preprocessed toggle ON by default, Phase A cap 2 with the two timing figures; the signal-loss rule and two related points are recorded after §1.6 item 3).

---

## 0 · SCOPE AND FRAMING

This is a **thesis-defense demo**, not a clinical product. Mandatory framing: **post-hoc EEG review
triage** — supports a clinician reviewing a recording they already have, **NOT a real-time alarm**.

Anti-staging principle: never add any algorithm/processing step that isn't in the real pipeline. Better
to be missing a button than to have a button that reflects nothing real.

**Anti-overclaiming guardrail — CHANGED FROM v4:** v4 banned displaying this on the UI. **Now it's
shown persistently** in the footer of every screen (except Log in, which is a pre-app screen):

> `SzScan is an AI-assisted tool designed to support clinicians, not replace them.`

Reason for the reversal: transparency through the product beats transparency through spoken words, and
the defense session may not have enough time to say it out loud. (Author's decision, 2026-09.)

**Login — CHANGED FROM v4:** v4 said it wasn't needed. **Now there is** 1 Log in screen, 1 fixed admin
account. No registration, no forgot/change password. Reason: accessing patient data should have 1
blocking step; this is a symbolic step to match the product's real shape, **not a real security
mechanism**.

---

## 1 · PROCESSING ARCHITECTURE — READ BEFORE WRITING ANY BACKEND CODE

### 1.1 Why the thesis's locked results can't be replayed

Measured on 2026-09-03, from the actual code in the repo:

| # | Measured fact | Source |
|---|---|---|
| F1 | `results/phaseB/tier2/ens_test_tf/rlg/ens_seed42_{subj}_{inter,ictal}.npy` is an array **by segment**, not by time. No window→second index exists | directory listing |
| F2 | `szcore_eval.build_timeline_masked()` rebuilds the timeline **using ground-truth annotation** — reads `edf['seizures']` then places the ictal score at exactly the label's position | `src/szcore_eval.py:98–109` |
| F3 | Windows inside the 4h buffer and missing interictal windows are **filled by bootstrap resampling** from the interictal distribution — a synthetic value, not the real score at that position | `src/szcore_eval.py:90, 111–113, 120–123` |
| F4 | `preprocessing.py` Step 4 **discards** windows beyond ±5 SD from `{subj}_interictal.npy`; the `inter_ptr` pointer runs sequentially → the real interictal score's **time position drifts** by exactly `n_rejected` | `preprocessing.py` Step 4 + `szcore_eval.py:117–119` |

**Consequence:** time-position information was already lost at the preprocessing step. There is no way
to recover it with more code. Every "cache the thesis result then draw it on a time axis" approach is
**wrong at the data level**.

### 1.2 Absolute prohibitions

**The demo MUST NOT:**
1. call `szcore_eval.build_timeline_masked()` or any function that builds a timeline from labels;
2. read the `seizures` / `Seizure Start Time` / `Seizure End Time` fields from `chb*-summary.md` at
   runtime;
3. use `{subj}_interictal.npy` / `{subj}_ictal.npy` (these two arrays were split **using labels**);
4. write to `results/`, `data/models_retrain/`, `docs/`, or any locked thesis artifact.

Points 1–3 are not a style convention. Violating them = leaking ground truth into a product presented as
label-free. That's an integrity failure, and it's the first question a sharp committee will ask.

`chb*-summary.md` **is still readable** for: the file list, `File Start Time`, `File End Time`,
duration. Only the seizure field is forbidden.

### 1.3 Locked architecture: a real, label-free, continuous re-run

> **Superseded by the final system (2026-10-10), see `web_demo/CLAUDE.md` and
> `THESIS_CONTEXT_FOR_DEMO.md` §2.** The pipeline below (`gae_joint_seed42.pt`, reconstruction + graph-mean
> latent + gamma-AEC, 1/3 ensemble, PELT over the whole-subject concatenated timeline) is the **retired V1
> system**. The final system loads `data/models_v2/gae_v2_clean_seed42.pt` (verified by sha256, never by
> filename), has **one** per-channel quantity (LedoitWolf Mahalanobis distance of the 16-d node latent,
> fused into order statistics 6/9/12 + channel mean, drift-corrected, patient-percentile, equal mean), and
> computes events **per file** (no concatenated subject timeline, no PELT — the detector + kernel-CPD
> localizer of `HANDOFF_T1_DEMO_REBUILD.md` §2 run per file). The historical V1 description is kept below
> for the record; do not implement it.

The demo runs the **same locked model** (`data/models_retrain/gae_joint_seed42.pt`) on the **continuous
recording**, with no interictal/ictal split, no windows dropped, no labels used anywhere.

```
.edf file
 → read the 18 standard channels (drop EKG/EOG/Ref if the original file has them)
 → bandpass 0.5–60 Hz + notch 60 Hz          (same as the thesis)
 → cut into 4 s non-overlapping windows @256 Hz  (same as the thesis, do NOT drop any window)
 → z-score per-channel                        (⚠ see §1.6)
 → CAR → wPLI + AEC → top-k 20%
 → 5-band band-powers → node feat [adj-row 18 | bp 5]
 → Joint GAE seed42 → zrecon + zlatent (⚠ §1.6) ; gamma-AEC → zgamma
 → robust-z per branch (⚠ §1.6) → equal-weight 1/3 ensemble
 → [concatenate every file of the subject, sorted by FILE NAME]
 → PELT (cpd_pipeline_v14) runs ONCE on the concatenated timeline
 → label-free operating point (FP-budget)
 → assign each global event back to its file via cumulative offset (§1.5)
```

**No window is ever dropped** ⇒ window index ↔ seconds within a file is an exact 1-1 mapping:
`t_seconds = window_index × 4`. This is exactly what the thesis's processing path lost.

### 1.5 Assigning events back to files — no lookup module needed

> **Superseded by the final system (2026-10-10).** The final system's detector and kernel-CPD localizer
> run **per file** (`HANDOFF_T1_DEMO_REBUILD.md` §2); there is no subject-wide concatenated timeline and
> no global event to assign back to a file — "no event crosses a file" by construction. The
> global-offset bookkeeping below belonged to the retired V1 (PELT-over-concatenated-timeline)
> architecture and is kept for the record only.

Because each file's score array has a length **exactly equal to that file's own window count**, each
file's offset can be derived **by construction**:

```python
offsets, cur = {}, 0
for f in files_sorted_by_name:
    offsets[f] = cur
    cur += len(score[f])
# a global event (on, off) belongs to file f when  offsets[f] <= on < offsets[f] + len(score[f])
# local offset = on - offsets[f]
```

No file is parsed, no summary is read, no extra module is needed — **and this automatically satisfies
guard #2 in §1.2**, because it never reads `chb*-summary.md` at runtime.

⚠️ **`edf_index.py` does not exist in the repo and does not need to be rewritten.** It belonged to the
v3 architecture (when the score was a segment-indexed array, so a `global_offset → file` lookup table
was required) and has been deleted. The old `WEB_DEMO_CODE_MIGRATION_NOTES.md` describes it as an
available module — that document has been archived, don't use it.
`edf_order.py` **is still kept** (`web_demo/backend/edf_order.py`): a completely different concern — the
**display** order of files in the UI, by the real time in the EDF header, differs from the **processing**
order, by file name. **Note (2026-09, Step 3):** in practice, both the processing order (§1.5, by file
name) and the "Recording N" display order in §5.1 now read directly from `raw.info['meas_date']` (the
full date-time in the EDF header) instead of `edf_order.py`'s heuristic — that file is still in the repo,
unmodified, but is no longer in the actual call path, because `meas_date` solves the underlying problem
(the chb03_24/25 case) directly, without needing the swap heuristic.

### 1.6 Deliberate divergence from the thesis pipeline — APPROVED BY THE AUTHOR

> **Rewritten for the final system (2026-10-10), per `docs/HANDOFF_T1_DEMO_REBUILD.md` §4.** The earlier
> three-item divergence list below this note (normalization/robust-z fit scope, post-ictal buffer
> inclusion, PELT background statistics) is **closed**: items 1 and 2 are not a divergence any more
> because the final system itself fits its per-channel LedoitWolf distance, robust-z, percentiles and
> alarm budget `q_i` on the whole recording, label-free, **by design** (author decision 2026-10-08:
> label-free whole-recording per-patient fitting is part of the unsupervised system, not a demo
> workaround) — no window is dropped and post-ictal segments are scored in the thesis's own continuous
> protocol too; item 3 is gone because PELT and its background statistics no longer exist in the final
> system (the detector is a per-file smoothed-quantile threshold, read from
> `results/p3c_freeze/freeze.json`).

There is now **one** divergence item, matching `docs/HANDOFF_T1_DEMO_REBUILD.md` §4:

| item | thesis (CHB-MIT runs) | demo |
|---|---|---|
| per-subject z-score statistics | `data/processed/{subj}_stats.json`: computed **after excluding annotated seizure windows and the 4-h post-seizure buffer** (inherited preprocessing, a label-dependent step the thesis discloses) | every 10th window of the whole recording, label-free (the rule already used for the thesis's external validation) |

Size of the remaining divergence is **measured, not assumed**, by the identity gate on chb03 (thesis
statistics vs label-free statistics, same code): `results/t1_demo/GATE.md`. **Never tune the demo toward
the thesis numbers.**

**Mandatory consequences to record:**
- **The demo's numbers WILL differ from the thesis's numbers.** They must never be forced to match,
  never adjusted to match.
- The demo **does not** display any evaluation metric (sensitivity, FP/day, AUROC, alarm budget). Those
  numbers belong to the thesis, not the product.
- This divergence must be **reported to the advisor** (Assoc. Prof. Hà Thị Thanh Hương) because it's a
  methodological decision.

**Prepared answer for the committee** — *"why does the demo find different events than the table in the
report?"*:
> The report's per-patient z-score statistics exclude annotated seizure windows and a 4-hour post-ictal
> buffer — a label-dependent preprocessing step, disclosed in the report. The demo cannot see labels, so
> it uses every 10th window of the whole recording instead — the same rule the thesis already uses for
> its own external (non-CHB-MIT) validation. Every other step of the final system — the per-channel
> LedoitWolf fit, robust-z, percentiles and alarm budget — is fitted on the whole recording, label-free,
> in the thesis system itself, so this one item is the only source of divergence, and it is measured
> (not assumed) by the identity gate on chb03.

### 1.7 Cost — measured, decided to run live

> **Superseded by the final system.** Every timing figure below (15 s/hour, PELT 3.58 s/hour, Phase A+B
> 14.29 s/hour, 21.9 s/hour, ≈12.3 s/hour) was measured on the retired V1 pipeline and **does not apply**
> to the final system (`web_demo/CLAUDE.md` "Numbers and parameters"). The final system's measured figure
> is **median 21.68 s per hour of EEG** (range 21.60–24.41, chb16, 3 runs) — see `results/t1_demo/TIMING.md`
> for the per-stage breakdown. No timing figure is quoted until that file exists; it now does. The
> "Decided" bullets below (real pipeline, no simulation; insurance cache; fewest-files subject for the
> live scenario) still hold as decisions, independent of the stale numbers.

Measured on the dev machine (Dell Latitude 3590, CPU): `build_adjacency` **13.2 ms/window** +
`compute_band_powers` **3.7 ms/window** = **16.9 ms/window** → **~15 s for 1 hour of EEG** (not counting
EDF reading, gamma-AEC, GAE forward — all much smaller).

**Decided:**
- Upload → runs the **real** pipeline, no simulation, no replay. v4's "half cache / half live"
  contradiction disappears: both halves are now real.
- Still building **cache in advance for 8 subjects**, but only as **insurance** during the defense
  (machine trouble / committee doesn't want to wait). The cache holds the real output of the demo's own
  pipeline, just computed early.
- Cache is matched **by file name** (not checksum) — the fixed, known-in-advance 8-subject scope makes
  this safe.
- The "Process" step (PELT over the whole subject) is the most time-consuming part. The live demo
  scenario should pick the subject with **the fewest files**; the exact number is measured when building
  the cache.

> **PELT-cost correction (C23, 2026-09-26):** measured on `chb16` (19 real files, 19.0 h, via the real
> Create-New→Process flow, `CC_STEP9_PHASE1B_REPORT.md`): PELT alone = **3.58 s/hour of EEG**, only
> **~25%** of Phase A+B's own wall-clock (**14.29 s/hour**, real upload flow) for the same subject —
> PELT is **not** the dominant cost; the bullet above was written against the older, component-level
> cost figures at the top of this section, not a real end-to-end measurement. Real Phase A+B
> wall-clock (14.29 s/hour, real HTTP upload flow) also runs **~46% higher** than the old
> `9.76 s/hour` serial-CLI figure still quoted in `CLAUDE.md` — explained by genuine upload-transfer
> overhead plus unbounded per-file Phase A thread concurrency (up to 19 concurrent threads observed on
> a 4-physical/8-logical-core dev machine). The concurrency finding is recorded as an **open item, not
> fixed** — deliberately deferred, since phase 1b's own measured total time is already comfortable
> without a fix; revisit (cap concurrent Phase A threads) before the defense if timing margin ever
> becomes a real concern.

> **Concurrency cap (C25, 2026-09-28):** Phase A concurrency is now capped at **4 workers**
> (`ThreadPoolExecutor(max_workers=4)`, `upload_manager.py`), replacing the unbounded per-file
> concurrency C23 measured above.

> **Phase A cap and timing (C28, 2026-10-02):** the Phase A cap is now **2 workers**
> (`_PHASE_A_MAX_CONCURRENCY = 2`, `upload_manager.py`) — `chb06` ran out of memory twice at 4. Two timing
> figures are kept apart: **21.9 s per hour of EEG** = processing only, sequential (median of repeats on
> `chb06_01.edf`, range 21.5-22.6), and **≈ 12.3 s per hour** = the whole 8-subject run end to end including
> upload (57 min 27 s for 279.4 h, 231 files, peak memory 10.2 GB). Per-file timing of that run was not
> logged. The live-upload scenario subject is `chb16`.

---

## 2 · DATA SCOPE

- **Hard allowlist of 8 TEST subjects:** `chb03, chb06, chb13, chb14, chb15, chb16, chb17, chb18`.
- A file belonging to a subject outside the list → **rejected**, toast:
  `This demo is restricted to the held-out test subjects.`
- **Reason (important, must not be relaxed):** live compute can now run on any CHB-MIT file. Without
  this block, the committee uploading `chb01` means the demo is running on **training data** — walking
  straight into the hardest question the whole thesis carefully avoided. The mock table in `UI/A4a`
  showing chb01/02/04… is **illustrative data only**.
- A file with the wrong format / missing the standard channels → excluded from the pipeline and the
  Database, toast:
  `File rejected — unsupported format or channel configuration.`

---

## 3 · STRUCTURE — 3 SCREENS

1. **Log in** — 1 fixed admin account.
2. **Database** (home page) — subject/file list, create new, delete, open.
3. **Analysis** — view EEG, timeline, review events, channel attribution.

There is no 4th screen. Both Database and Analysis share one standard website shell; Analysis is just
longer and scrolls vertically normally, not a special layout.

---

## 4 · LOG IN SCREEN

- A single account, **ID and password set in the backend's `.env`** — not hardcoded in the frontend
  (readable via devtools). No registration, no forgot/change password.
- The password field **must be masked** (`type="password"`). The mockup showing plain text is purely
  illustrative.
- No footer disclaimer on this screen (a pre-app screen).
- Avatar in the header's top-right corner after login → **Log out** dropdown (see `UI/A0b`).
- This is **not** a real security mechanism. Nothing sensitive is stored; a simple session is enough.

---

## 5 · DATABASE SCREEN

### 5.1 Main table (tree form, expandable)

| Column | Meaning |
|---|---|
| ID | Subject name (e.g. `chb06`), click ▶ to expand into the list of child .edf files |
| No. files | The subject's total number of .edf files |
| Start date | **CHANGED FROM THE PREVIOUS VERSION — C17, 2026-09.** Displayed as `Recording N, HH:MM:SS`, **not an absolute date**. N = the recording's position within the subject's file sequence, sorted by `meas_date` **ascending** (N=1 is the earliest recording by real time in the EDF header — this is also the order `edf_order.py`'s heuristic used to aim for, now achieved directly and more accurately via the full date-time `meas_date`). HH:MM:SS = the time of day that exact recording started, read from `meas_date`. The subject row shows **Recording 1** (the subject's earliest recording). A child file row shows that file's own correct **Recording N**. **Derived automatically from the EDF header**, no manual entry field, no absolute year/date shown (see the note right below this table) |
| Duration | `HH:MM:SS` if < 24 h, `Nd:HH:MM:SS` if ≥ 24 h. Subject = the sum of every file's duration; file = its own end − start |
| Alert | The current total event count (see §5.3) |
| Status | `View` / `Viewing (x/N)` / `Viewed` (see §5.2) |
| Memo | Free text entered by the user (sex/age/notes). **Never auto-generated** by the model |

A child file row uses the same column structure; only its Status has no fraction.

> **Date note (C17):** CHB-MIT (distributed via PhysioNet) applies a fixed date shift to de-identify
> patients — the year/date recorded in the EDF header's `meas_date` is **not the real date**. The shift
> is **constant within a given subject**, so recording order, the time of day each recording starts, and
> the gap between recordings **remain accurate** — only the absolute year/date is meaningless and
> shouldn't appear on screen. This is why this column shows `Recording N, HH:MM:SS` instead of an
> absolute date: it keeps exactly the three things a viewer needs to know and drops exactly the one
> fabricated thing. This decision applies uniformly to both the Database UI and everywhere else that
> once intended to show an absolute date from `meas_date` — currently nowhere else does that (§6.2's
> time format on the Analysis screen is already relative, not an absolute date; §7.3's export also only
> records the time of day, with no year).

**While a subject is being processed (upload + pipeline + CPD), that subject does NOT appear in the
table.** Only once everything has finished running does the subject row + every child file row appear
at once. Any other subject already there beforehand still displays normally.

### 5.2 Status rules

**File level:** `View` (finished processing, waiting to be viewed) / `Viewing` (being viewed, progress
auto-saved) / `Viewed` (the "Viewed" button has been clicked on the Analysis screen).

**Subject level:** `View` if ALL files are `View`; `Viewed` if ALL are `Viewed`; otherwise
`Viewing (x/N)` where **x = the number of files that are `Viewed`**, N = total file count. The fraction
only appears at the subject level — to clearly distinguish it from the file level at a glance.

### 5.3 Alert formula

```
Alert = (number of AI-detected events NOT YET Rejected) + (number of User-added events)
```

- Rejecting 1 AI event → Alert drops by 1.
- `Uncertain` and `Unseen` **still count** toward Alert.
- Alert always reflects the latest review state; it is never locked to the original AI count.
- Displayed in a neutral color (no amber, no red) — see `SZSCAN_DESIGN_v2.md`.

### 5.4 Search box

- Filters by **file name or subject name**. Type, then click the **search button** — no auto-filter per
  keystroke.
- Matching a child file's name → the table narrows to the subject containing it, the subject
  **auto-expands**, and **only the matching file shows** (other files of that subject are temporarily
  hidden; clearing the search restores all of them).
- Matching a subject's name → shows that subject with all its child files, collapsed state.
- No match → the "No data" block, but with the text changed to `No results for '...'`.
- Case-insensitive, partial match allowed.

### 5.5 Creating a new subject ("Create new")

Right-side overlay panel (`UI/A1a`):
- **Project ID** (text input)
- **Memo** (text area, optional)
- Dashed drag-and-drop **Browse Files** zone — selects all of the subject's .edf files at once
- **No "Test date" field** — this value is derived from the EDF header and only appears in the
  `Start date` column of the Database table *(changed from v4, where it was still a field in the
  panel)*
- The list of selected files appears below, each with a status icon:
  - a spinning circle = uploading; **click the square inside the circle to STOP** that file's upload
  - an ✕ mark = finished uploading (click to remove it from the list)
- A black **Process** button + a small note line below it. **Disabled until every file has finished
  uploading.**

**Two processing stages:**

> **Superseded by the final system.** Step 2 below describes the retired V1 architecture (one
> concatenated subject timeline, PELT run once, global events assigned back to files). The final system's
> Phase B fits the per-subject statistics (LedoitWolf, robust-z, percentiles, alarm budget) across the
> whole subject, then the detector and kernel-CPD localizer run **per file** — there is no concatenated
> timeline and no global-offset assignment (`HANDOFF_T1_DEMO_REBUILD.md` §2). The two-stage shape (Phase A
> per file as it finishes uploading, then a second stage on Process) still holds.

1. **As soon as 1 file finishes uploading** (not waiting for Process to be clicked): the backend runs
   the §1.3 pipeline for that file alone, **stopping before CPD**, producing one continuous
   time-indexed ensemble score array for the file.
2. **Clicking Process:** concatenates every file's ensemble score, **in exact FILE NAME order**, into
   one continuous timeline → runs PELT **exactly once** over the whole timeline (the algorithm needs
   enough background to estimate stably, no splitting into separate short-file runs) → assigns
   each global event back to its correct file by cumulative offset (§1.5 — no lookup module is needed;
   `edf_index` does not exist).
3. While running: a full-panel loading state (spinner + a simple progress bar, **not** distinguishing
   the 2 sub-stages, **no** fake %).
4. Done → the Database shows the new subject + every child file, Status = `View`.

**Minimizing mid-way (the "−" button):** doesn't cancel anything. Collapses to a bottom-right toast —
`Create New (draft)` while uploading, `Processing...` while Process is running. Keeps running in the
background, click the toast to return to it.

**Concurrency limit:** system-wide, **only exactly 1 subject** may be processing at any one time, even
minimized. Clicking "Create new" while a subject is running → blocked, shows a message asking to wait
(`UI/A1d`).

**There is no Edit mode.** To make a change → delete the whole subject and re-create it. Reason: editing
would force CPD to rerun over the whole concatenated timeline, which loses all prior review; "edit =
re-create" is far simpler than designing a review-preserving mechanism.

### 5.6 Delete

- **Only the Subject level can be deleted.** Selecting a child file row and clicking Delete → no
  response.
- A confirmation screen exists. **The same single sentence is used for every delete case**
  (mid-processing or already complete) — not split into 2 messages *(the author's decision, different
  from v4)*.
- Deleting a subject also removes `uploads/{subject_id}/` from disk.

### 5.7 Other buttons

Selecting 1 row → highlights it. **Open** → goes to the Analysis screen for the selected subject/file.
**Cancel** → just deselects the row.

---

## 6 · ANALYSIS SCREEN

### 6.1 Header

| Component | Meaning |
|---|---|
| `<ID> (<N> alerts to check)` | N = the Alert of the **currently viewed file**, synced to the latest review state |
| Previous / Next | Moves to the previous/next **file** within the same subject (not the next event) |
| Viewed | Marks the currently viewed file as `Viewed` |
| Export | Exports a `.txt` report for the **entire subject**. **Only enabled once every file of the subject is `Viewed`** |
| File-select dropdown | Lists every .edf file of the subject, with the event count in parentheses: `chb06_06.edf (2)` |
| Progress | `x/N` = number of files `Viewed` / total file count |

### 6.2 Time format — a single rule

Applied **consistently to every file-level time axis** (the mini-timeline and the axis below Panel EEG):

- `HH:MM:SS` if the file is < 24 h
- `dN:HH:MM:SS` if ≥ 24 h

*(Removes v4's old exception, "the mini-timeline never uses dN.")* The mockup showing `d1 …` is just an
illustrative example for the ≥ 24 h case; `UI/B0b` illustrates the < 24 h case.

### 6.3 Timeline Panel (mini, at the top)

- **Only shows the range of the currently viewed file**, never the whole subject concatenated.
- Default 1 hour, split into 6 cells × 10 min each.
- Two rows: **Seizure Detection Score** (a line chart of the ensemble score) and **Detections**
  (rectangular blocks, long/short per each event's duration).
  - **Rewritten for the final system (2026-10-10), per `docs/HANDOFF_T1_DEMO_REBUILD.md` §3.4.** The
    ensemble score is now a **patient-percentile mean in [0, 1]**, not a robust z-score — it is no longer
    true that it "can be negative or positive". Row 1's name stays `Seizure Detection Score` regardless
    (never "Probability", even though the range happens to be [0, 1]).
  - Y-axis: **fixed range [0, 1]**, no reference line, no threshold line (the alarm budget / operating
    point is an internal parameter and must not appear in the product). The zero line may fall outside
    the auto-scale box — left as is. **Shows no numbers** at either end (unchanged from the earlier
    design: this box is small, a quick-glance role).
- Has a playhead (▼) synced with Panel EEG.
- **View-only, no interaction.** Clicks only work on Panel EEG.

> **Paging past 1 h (C26, 2026-09-28):** files can run well past the 1 h default (chb06 up to
> ~4 h). The mini-timeline pages in fixed 3600 s pages that follow the playhead:
> `pageStart = floor(playheadSec / 3600) * 3600`, `pageEnd = min(pageStart + 3600,
> usable_duration_seconds)`. The score line, Detections blocks, cell grid, time labels and
> playhead are all drawn for `[pageStart, pageEnd)`; an event straddling a page edge is clipped
> to it. The page automatically flips whenever the playhead crosses an hour boundary (playback,
> scrub-bar seeking and Event Panel row clicks all already move the playhead) — no new controls,
> still view-only. Every page keeps the same fixed 6-column, 10-min grid regardless of how much
> of it a trailing partial page actually fills, so a file <= 1 h (`pageStart` always `0`) renders
> pixel-identical to the pre-C26 single-page behaviour. The Y-axis auto-scale is unchanged: still
> P1–P99 of the whole file's score, never just the visible page.

### 6.4 EEG Panel

- **Fixed at exactly the 18 standard channels** of the pipeline. Filters out every extra channel
  (EKG/EOG/Ref) if the original file has them — e.g. chb13/14 have an extra EKG, chb15 has 8 extra
  FC/CP-Ref channels. Reason: everything shown must be data that genuinely went into the computation.

**Toolbar** (left → right, see `UI/B1a`):

| Button | Function |
|---|---|
| `⊲▷ [X] hr` | The length of the window shown on Panel EEG, **independent** of the mini-timeline's 1-hour zoom. Click the number → a vertical-slider popover from 24hr → 1min (`UI/B1b`) |
| `⇕ [X] uV` | Amplitude scale, a dropdown of fixed steps **500/250/150/100/75 µV** (⚠ **CHANGED — C18, 2026-09-21, floor set final in Step 5 fix round 6**, see the note right below this table). Frontend-only, doesn't touch the backend |
| `⏮⏭ Select Range` | Enables manual event-creation mode (§6.6) |
| `pp Preprocessed (0.5-60 Hz + 60 Hz notch)` | 1 toggle for the pipeline's only real filtered state — bandpass (0.5-60 Hz) then notch (60 Hz), always both, always in that order (⚠ **CHANGED — C24**, see the note below) |

> **Amplitude-scale note (C18, 2026-09-21; floor decided in Step 5 fix round 6):** the original
> 5/7/10/15/20/30 µV list was chosen before real data existed to check it against — reasonable at the
> time, but "locked" in this document has never meant "can't be revised once real build data shows a
> different picture"; it means once revised, it's re-locked, not never revised. Measured directly on
> real data during the build (`chb13_03.edf`, `chb06_01.edf` — Step 5 fix round 2, method:
> `max_uv − min_uv` per displayed bucket, the exact quantity `drawSeries` draws and `amplitudeUv` scales
> against) gives a per-channel amplitude of **median ~106–111 µV, peaks up to ~1200–1800 µV** on both
> subjects — far beyond the old range, which kept the waveform looking dense/busy at every old level,
> including the largest (30 µV). First extended (round 2) to 50/75/100/150/250/500 µV on top of the 6
> old small levels, keeping those "for flat (interictal) signal segments" — but round 4
> (`CC_STEP5_FIX4_REPORT.md §1`) tested that claim directly: even the file's own score-identified
> calmest 60 s stretch in `chb13_03.edf` (`3172–3232s`) still measured a median per-channel spread of
> ~102 µV, the same regime as a busy window, so 10/20 µV stayed near-solid-clipped there too — there is
> no flat/interictal regime in this data that the small levels actually serve. **Final list, decided:
> 500/250/150/100/75 µV — floor at 75 µV, 50/30/20/15/10/7/5 µV dropped entirely.** The dropdown still
> isn't stretched all the way to the absolute peak (~1800 µV): that large an amplitude is rare and would
> needlessly lengthen the list, and 500 µV already stops clipping most channels. (`chb15` gives a
> notably lower median — ~26 µV — but that was measured on 1 short, 500 s test file, not representative
> of a full recording, and round 4's calmest-segment measurement above already shows the real floor
> lands well above where a `chb15`-driven low end would sit.)

**Removed from the toolbar** (compared to the original Persyst/wireframe): the **All** button (channels
are fixed, not selectable) and the **ar** button (Artifact Reduction — the pipeline has no corresponding
step; keeping it just to "look like Persyst" would be a feature reflecting nothing real). Also removed
the toolbar's **Comment** button since Comment is already attached to each event.

**Filter toggle:** when on, the filtered wave is highlighted, the raw wave recedes into a dim background
— **raw is never fully hidden**.

> **Filter-toggle correction (C24, 2026-09-27):** this table's row used to read `lff 0.5 Hz` ·
> `hff 60 Hz` · `60` — 3 independently-toggleable filters that were never real.
> `pipeline_demo.process_file_phase_a` runs exactly one bandpass (0.5-60 Hz, `sosfiltfilt`) then
> exactly one notch (60 Hz, `filtfilt`), always both, always in that order — there was only ever
> one real filtered series, and all 3 old buttons toggled the same cached array
> (`CC_FIX_FILTERSTAGES_REPORT.md`). That report first collapsed the toolbar to 2 buttons (`bpf
> 0.5-60 Hz` + `60`, exposing the bandpass-only intermediate as its own toggleable state) — a fix
> this document was never updated to reflect, so the table above was stale twice over. Measured
> immediately after (same report, chb16): bandpass-vs-bandpass+notch differs by only **~2.91 µV**,
> against **~127.92 µV** for raw-vs-preprocessed — visually negligible at every amplitude scale
> this toolbar offers (75-500 µV, C18 above), and no real downstream stage (z-score, adjacency,
> GAE) ever consumes the bandpass-only intermediate on its own; only the fully preprocessed signal
> feeds the pipeline. `CC_FIX_FILTER_SINGLE_TOGGLE_REPORT.md` collapsed the toolbar to the single
> real toggle the table now describes: **OFF = raw, ON = preprocessed (bandpass+notch combined)**.
> The backend's `.bandpass.npy` cache file was left in place (harmless sunk cost) even though
> nothing reads it anymore.

> **Preprocessed-toggle default (C27, 2026-09-29, author decision, `CC_FIX_SCORECACHE_PROMPT.md`
> Task 2):** the toggle now defaults **ON** on a fresh Analysis-screen load, superseding
> CC_STEP5_FIX4_PROMPT.md's "genuinely raw on load" rule. That rule existed because the toggle
> used to be mislabeled as 3 independent filters (see C24 above) — defaulting to an
> already-filtered view under that mislabeling would have silently hidden which stages were
> applied. Now that the label reads plainly `pp Preprocessed (0.5-60 Hz + 60 Hz notch)`, and the
> preprocessed signal is what the model actually consumes, defaulting to it is the more
> representative first view. Everything else about the toggle is unchanged: raw stays drawn,
> dimmed, underneath ("raw is never fully hidden"), and turning the toggle OFF still shows raw
> alone. The amplitude default (C18 above, 75 µV) is also unchanged — screenshots of `chb06_02.edf`
> at 75/150/250 µV under this new default are in `CC_FIX_SCORECACHE_REPORT.md`, but the author
> keeps final say on that default.

**Playhead:** only clickable on Panel EEG. Clicking a point → the playhead jumps there, the mini-timeline
syncs.

**Bottom scrub bar:** has a playback-speed dropdown `1x / 2x / 4x / 8x`, default **1x** *(new compared to
v4, where the speed was fixed)*. Capped at 8x because beyond that the eye can no longer read the
waveform.

**The "Event Time" row** at the bottom of Panel EEG: blocks for the events in view, labeled `Event N`
(**never** `seizure N` — see §7.2).

### 6.5 Event Panel

- **Two nested filter tiers:** tier 1 `All / Human / AI`; tier 2 only appears when `AI` is selected —
  `Accept / Reject / Uncertain / Unseen`. (A Human event self-confirms when created, so it needs no
  review.)
- **Count format:** bare `x` when the filter is All or Human; `x/y` when the filter is an AI sub-label
  (x = matches, y = total AI events in the file). "All" combines Human + AI.
- Each row: `Event` (name) / `Onset` / `Type` (AI icon or person icon) / `▼` expand in place.
- **An expanded AI event:** read-only Onset / Offset / Duration + 3 choices `Accept / Reject /
  Uncertain` + a Comment field + a Save button. **An AI event's onset/offset cannot be edited** — to
  change it, Reject it and create a new event manually with Select Range.
- **An expanded User-added event:** Onset / Offset / Duration + **Delete / Edit** + Comment + Save. No
  Accept/Reject/Uncertain.
- **Clicking 1 event row** → instantly syncs the other 3 panels: Panel EEG jumps to onset→offset, the
  mini-timeline updates its playhead, the Attribution Panel shows that event's data.
  **The Event Panel is the primary control source.**
- **Empty state:** a file with no AI events at all → an empty panel, still allows adding an event
  manually (`UI/B0a`). Wording: `No detected events in this file. You can still add an event manually
  with Select Range.` — **never** `No seizure detected` (implies a medical conclusion).

### 6.6 Creating a manual event (Select Range)

1. Click **Select Range** → enables marking mode.
2. Click point 1 on the EEG grid → sets the **onset**, shows a vertical marker line.
3. Move the mouse right → a rectangle stretches following the cursor in the "Event Time" row (`UI/B3a`).
4. Click point 2 → locks in the **offset** (`UI/B3b`).
5. The new event **inserts itself at the correct time position** in the list (not appended at the end),
   with a person icon, auto-computed Onset/Offset/Duration, no Accept/Reject/Uncertain.
6. The mini-timeline adds a new block at the matching position, colored differently from an AI block.
7. The header's Alert + the Database **auto-increment by 1**.

*Note when reading the mockup:* the gray in `UI/B3a` is the **Unseen** label, not a dimming effect from
being in event-creation mode.

> **Step 6 gap-fill note (C19, 2026-09-24):** Step 6 implemented five behaviours that §6.1/§6.5/§6.6 did
> not describe. All were verified live in the running app and approved by the author.
>
> 1. **Edit** on a User-added event re-enters the Select Range marking mode scoped to that event: two
>    clicks on the EEG grid overwrite its onset/offset, and the event keeps its identity (same id). While
>    the redraw is in progress the expanded row's `Delete` / `Edit` buttons are replaced by a one-line
>    hint. This mirrors the AI "Reject and redraw" asymmetry of §6.5: a User-added event is fully
>    editable, an AI event's range is not.
> 2. **Cancel** while marking = click the `Select Range` toolbar button again after the onset click. No
>    partial event is ever written. The button label reads `Click onset…` / `Click offset…` while marking
>    is active. The same button cancels an in-progress Edit redraw.
> 3. **Direction-agnostic drag:** if the second click lands before the first, the two points are sorted so
>    that onset < offset. A non-positive duration is never stored.
> 4. **Numbering:** `Event N` is derived at read time from onset order (`onset ASC`, ties by id) and is
>    never stored. Inserting a User-added event therefore renumbers every later event, consistently in the
>    Event Panel, the Event Time row, the mini-timeline and (Step 8) the export, where `Event N` must match
>    the UI. `UI/B3c`'s sample data is not fully chronological (its Event 4 stays last); it is read as
>    un-resorted sample data, not as a rule.
> 5. **Header layout (§6.1):** the title `<ID> (<N> alerts to check)` sits directly to the left of
>    `Previous`, forming one right-hand cluster `[title] [Previous] [Next] | [Viewed] [Export]
>    [file dropdown]` as in `UI/B1a`/`B2a`. The author considered removing the title as redundant with the
>    file dropdown and decided to keep it.

### 6.7 Channel Attribution Panel

**Mandatory framing — this is a scientific constraint, not a UI choice.** Per
`docs/ATTRIBUTION_SPEC.md`, this is **XAI for the GAE's reconstruction branch**. It is **NOT**
localization and **NOT** SOZ. The label-scored evaluation is **closed** (2026-09-25): blind
human-reader labels, approved, result negative (does not support a localization/SOZ reading).
This does not change the panel's own wording above, which stays exactly as written.

> **Superseded by the final system (2026-10-10).** There is no reconstruction branch any more — the
> panel is XAI for the **per-channel latent** readout (LedoitWolf Mahalanobis distance of the 16-d node
> latent), per `THESIS_CONTEXT_FOR_DEMO.md` §5. The negative localization/SOZ finding and the panel's UI
> rules (no causal language, no attribution metric on screen) carry over unchanged to the new readout.

- **Panel title:** `Channel-level latent anomaly — Event N`
  *(revised from "Channel contribute to ..." in the mockup — the old phrasing implies a causal/
  localizing relationship; "reconstruction" → "latent" for the final system's readout.)*
- **Display:** a simple head diagram (circle + the 18 electrode positions of the 10-20 system) as the
  background, with **18 straight lines connecting the 2 electrodes of each bipolar channel** drawn over
  it (e.g. FP1↔F7 for channel `FP1-F7`), colored by Score.
  - **Connecting lines are mandatory, dots are not allowed**: CHB-MIT is **bipolar** data — each
    channel is the potential difference between 2 electrodes, not a value at 1 point. A dot
    misrepresents the nature of the data.
  - **Teal** color scale, never red/yellow/green — see `SZSCAN_DESIGN_v2.md` §4.
- **Table below:** `Rank / Channel / Score / Status`. Rank is fixed by Score, the user cannot reorder
  it. Status is a segmented control `Accept | Reject` (mutually exclusive, like a radio button).
- **Save** + **Clear all** buttons at the bottom of the table.
- Syncs to the currently selected event, **including a user-created event** — attribution is a
  per-window number computed by the model, aggregated over any time range, independent of whether that
  event was AI- or human-created.
- **Empty state:** no event selected yet → placeholder `Select an event to view attribution`, never
  auto-shows the first event.
- **Never** shows an attribution evaluation metric (AUROC, confidence interval, p-value) on the UI.

> **Step 7 gap-fill note (C20, 2026-09-24):** the panel's definition, mapping and persistence, none of
> which §6.7 spelled out:
>
> **Superseded by the final system (2026-10-10), see `web_demo/backend/attribution.py`'s own docstring.**
> Items 1, 3, 5 and 6 below (window-overlap rule, rank/display, gradient mapping, per-channel
> Accept/Reject persistence) are unchanged. Items 2 and 4 change what `D` (the quantity inside
> `{stem}.pernode.npy`) actually is: **`D` is now the per-channel LedoitWolf Mahalanobis distance of the
> GAE v2 node latent** (`src/attribution_v8.py`'s quantity), not the GAE v1 reconstruction-branch
> `joint_score(..., per_node=True)` output described in item 4 below — there is no `gae_joint`/
> `zrecon_raw` call any more. The formula is otherwise identical: `z = |(D - median)/MAD|` per window per
> channel (whole-subject baseline, no 1.4826 factor), `score = p95(z)` over the event's windows, taken
> **before** the final system's drift correction (the ±15-min running median) — i.e. the panel's quantity
> is one step upstream of the timeline's ensemble score, same as it was for the v1 branch. The one-item
> divergence of §1.6 (now the final system's single item) still applies to this baseline's scope.
>
> 1. **Windows of an event:** the windows whose 4 s span `[4i, 4i+4)` overlap `[onset_sec, offset_sec]`
>    — the same overlap rule `src/attribution_pipeline.py`'s `_blocks_for_subject` uses for the thesis's
>    labeled seizures, applied here directly from the event's own onset/offset (AI or Human) instead of
>    a label-derived array. Always at least the window containing the onset; clamped to the file's
>    per-node array length.
> 2. **Aggregation across those windows** and **3. the score shown per channel** — **CLOSED, no
>    longer PROVISIONAL (Step 7 fix round 2, 2026-09-25):** `score = percentile(|z|, 95, axis=0)`,
>    where `z = (window - med) / mad` is a per-channel, per-window robust z-score of the event's
>    own `.pernode.npy` windows against a **whole-subject baseline** — `med`/`mad` computed **once
>    per subject** (median/MAD over every window of every file belonging to that subject, from
>    `.pernode.npy`; no 1.4826 factor). This is the exact same formula as
>    `src/attribution_pipeline.py`'s `cmd_score` (lines ~514–520); the only difference is baseline
>    scope (whole-subject recording here vs. interictal-only there) — **the same divergence already
>    recorded in §1.6 item 1, not a new one.** Rank = position by the unrounded score, highest
>    first; unaffected by status. Displayed to 2 decimal places (`AttributionPanel.jsx`).
> 4. **`{stem}.pernode.npy`** (`[n_windows, 18]` float32, channel order = `preprocessing.COMMON_
>    CHANNELS`) is computed in Phase B's per-file model-scoring step (a second, independent
>    `gae_joint.joint_score(..., per_node=True)` call alongside the existing scalar `zrecon_raw` call,
>    same inputs) and cached at `uploads/{subject_id}/{stem}.pernode.npy`, next to `.filtered.npy`/
>    `.raw.npy`/`.score.npy`. **`{subject_id}/pernode_baseline.npy`** (stacked `[2, 18]` float32 —
>    row 0 median, row 1 MAD) is the item 2-3 baseline above, computed **once per subject in the
>    same Phase B run** (subject-wide, same rule as the z-score/LedoitWolf stats §1.6 item 1 already
>    describes) and persisted next to it — **never recomputed on a read.** Attribution itself
>    (the per-event score/rank) is still computed fresh on every `GET /api/events/{id}/attribution`
>    call from these two cached arrays, never cached in the DB, so an edited Human event's range
>    change is reflected immediately; if a subject's baseline file doesn't exist yet (not
>    backfilled), the endpoint returns the same `{"available": false, ...}` shape as a missing
>    `.pernode.npy` file rather than computing the baseline on the fly.
> 5. **Gradient mapping:** each channel's score is min–max scaled across that event's own 18 scores (all
>    equal → low end) and read off `linear-gradient(to right, --color-attr-low, --color-attr-mid,
>    --color-attr-high)` (`SZSCAN_DESIGN_v2.md` §4) as a continuous 3-stop interpolation, not a
>    3-bucket/discrete mapping.
> 6. **Per-channel status** (`attribution_status(event_id, channel, status)`, `Accept`/`Reject` only) is
>    stored per event **keyed by channel name**, so redrawing a Human event's range keeps its channel
>    judgments. `PUT .../attribution-status` replaces the full stored set — the same Save-persists
>    pattern as AI event review (§6.5): `Clear all` only clears the panel's own local selection, nothing
>    is deleted server-side until `Save` is pressed with the now-empty set. Deleting an event explicitly
>    deletes its `attribution_status` rows (not left to the FK pragma alone). No attribution status ever
>    changes Alert or the event's own review status.

---

## 7 · EXPORT

### 7.1 Scope

**A single `.txt` file for the entire subject**, combining every child .edf file — exactly matching the
original structure of CHB-MIT's `chbXX-summary.txt` (which itself combines multiple files in 1 text
file).

### 7.2 The "Event" vs "Seizure" wording rule

- **On the UI during review:** everything AI-detected is called an **Event** / **Alert**. A single
  detection is never called a "seizure".
- **Two labels are allowed to contain the word "Seizure" on the UI:** `Seizure Detection Score` and the
  EEG panel's title — because they are only the **system's output in general**, not a medical label
  assigned to one specific item.
- **In the export file:** the line `Number of Seizures in File: N` is kept exactly per the original
  CHB-MIT convention (for machine cross-referencing), but sub-entries are still numbered `Event 1`,
  `Event 2`… matching exactly the numbering the clinician already saw on the UI. Both naming schemes
  coexisting is **deliberate**, not a bug. (**C22, 2026-09-25:** `N` = the count of every `Event` block
  listed below that file — AI (including Rejected) + Human, combined — confirmed by the author as the
  settled reading, not a placeholder; was an open judgment call in `CC_STEP8_REPORT.md §3`, closed in
  `CC_STEP8_FIX_REPORT.md §5`.)

### 7.3 Structure

Keeps the original CHB-MIT frame, inserting new information right after each event (see
`UI/Annotaiton (format_ ID-summary.txt).png`):

```
Data Sampling Rate: 256 Hz
Channels in EDF Files:
Channel 1: FP1-F7
...
Channel 18: CZ-PZ

File Name: chb06_06.edf
File Start Time: 15:10:23
File End Time: 16:10:23
Number of Seizures in File: 2

Event 1
    Source: AI
    Review Status: Accept
    Start Time: 1230 seconds
    End Time: 1265 seconds
    Duration: 35 seconds
    Comment: (content if any)
    Channel Attribution (rank/channel/score/status):
      1  FP1-F7  3.5  Accept
      2  F7-T7   3.4  Reject
      ...

Event 2
    Source: Human
    Start Time: ...
```

**Time in the export uses seconds from the start of the FILE** (like the original CHB-MIT annotation),
**not** `HH:MM:SS` like the UI — this is a technical file meant for further processing, not optimized
for human reading.

---

## 8 · OPEN ITEMS — must be handled during the build, never guessed

| # | Item | How to handle |
|---|---|---|
| ~~O1~~ | ~~The demo's operating point~~ — **SUPERSEDED by the final system (2026-10-10):** there is no fixed `mag_pct`/`pen_mult` operating point any more. The alarm budget is `p_i = clip(q_i, 0.005, 0.02)`, `q_i` a label-free per-patient share computed from `results/p3c_freeze/freeze.json` (point `"balanced"`) — read at runtime, never typed in (`web_demo/CLAUDE.md` "Numbers and parameters"). All of V1's `fp_budget_operating_point`/`calibrate_operating_point`/`FIXED_MAG_PCT`/`FIXED_PEN_MULT` machinery described in this row is gone from the demo's path. | closed |
| ~~O2~~ | ~~PELT parameters~~ — **CLOSED, superseded:** PELT (`src/cpd_pipeline_v14.py`) is not part of the final system. The localizer is `ruptures.KernelCPD` (rbf, min_size 2, 2 change points), called per file via `src/e18_cpd_localizer.py` / `src/p3_levers.py`; its parameters are read from the same frozen code, nothing re-chosen. | closed |
| ~~O3~~ | ~~what the demo's robust-z fits on~~ — **CLOSED 2026-09-03**: `retrain_io.robust_z` already fits on the entire window set (lines 56–60). Not a divergence, nothing to handle | closed |
| ~~O4~~ | ~~Which subject to use for the live-upload scenario~~ — **CLOSED**: `chb16`, chosen by measured end-to-end time (~5.7 min, the fastest of the 8 allowlisted subjects), not by file count | closed |
| O4b | **The extent of post-ictal flagging** (§1.6 item 2) — observed at step 1, decide whether to call it out separately in the defense slides. No adjusting the model, no adjusting the threshold to "fix" it | observe |
| ~~O5~~ | ~~Gamma-AEC in the continuous path~~ — **CLOSED, superseded:** the gamma-AEC readout does not exist in the final system (`web_demo/CLAUDE.md`: "No reconstruction/gamma/graph-mean readouts"). `dataprep/compute_gamma_aec.py` is not imported by `pipeline_demo.py`. Nothing to write. | closed |
| O6 | **`evaluation_protocol.py` and `stat_validation.py` were just restored to `src/`** (2026-09-03, tag `repo-deps-fixed`) after being mistakenly archived while still being imported. `fp_budget_operating_point.py` depends on this chain — verify the `import` runs before pulling parameters for O1 | 1 command |

None of these items block starting to build the frontend.

---

*End of SZSCAN_SPEC_v5.md. Fully replaces `WEB_DEMO_SPEC_v4.md` and `WEB_DEMO_CONTEXT_BOUNDARY.md`.*
