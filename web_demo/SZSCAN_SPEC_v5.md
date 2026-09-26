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
see the note after §6.7 and §1.6).

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

There are **three divergence items**, matching the thesis report's own enumeration, sharing the same
root cause: a new patient has no labels. *(Restructured from two lettered groups into these three
numbered items in Step 7 fix round 2, 2026-09-25, C21 — the same facts and evidence, re-grouped, not
rewritten.)*

#### 1. Normalization statistics, covariance, and robust-z fit on the whole recording, with no artifact rejection

A new patient has no interictal array. The demo fits all of the following on the subject's **entire set
of windows** instead:

| Step | Thesis fits on | Demo fits on |
|---|---|---|
| z-score stats (mean/std per channel) | interictal | entire window set |
| 5 SD artifact threshold | interictal | **dropped entirely** (no window discarded — time position must be preserved) |
| `LedoitWolf().fit(Zi)` for `zlatent` | interictal's latent | the entire window set's latent |
| ~~robust-z median/MAD per branch~~ | **entire window set** | **entire window set** — *not a divergence* |
| Channel Attribution Panel's robust-z baseline (`med`/`mad`, C20/C21) | interictal (`{subj}_interictal_pernode.npy`) | whole-subject (every window of every file belonging to the subject, from `.pernode.npy`) |

**robust-z is not a divergence.** `retrain_io.robust_z(raw_i, raw_c)` lines 56–60 already fit median/MAD
on `np.concatenate([raw_i, raw_c])` — i.e. the entire window set. The demo does exactly what the thesis
does. This row is kept struck through in the table above so a future session doesn't go re-check it.

**Justification:** the fraction of ictal windows is extremely low — measured on chb06: 45 / (19826 +
45) = **0.23%**. Not enough to meaningfully skew the covariance, median, or MAD.

**VERIFIED BY MEASUREMENT — 2026-09-03. No need to rerun.**

Criterion set before running: PASS if Spearman ≥ 0.98 **and** |ΔAUROC| ≤ 0.02 on both subjects.

| subject | AUROC (fit on interictal — thesis) | AUROC (fit on entire set — demo) | Spearman | n_int / n_ict |
|---|---|---|---|---|
| chb06 | 0.6066 | 0.6051 | **1.0000** | 19826 / 45 |
| chb13 | 0.6493 | 0.6408 | **0.9999** | 12452 / 144 |

→ **PASS.** Changing how LedoitWolf is fit barely changes `zlatent` (rank order is nearly identical,
ΔAUROC 0.0015 / 0.0085). Item 1 is measurement-harmless (for the `zlatent` component measured).

⚠️ This measurement **only** covers `zlatent`. The other three — z-score stats, dropping artifact
filtering, and **item 2 below** — need continuous preprocessing straight from the EDF, so they can only
be observed at build step 1. The Channel Attribution Panel's baseline row (added C20/C21) has not been
separately re-measured against this AUROC/Spearman check — it is grouped into item 1 because it is the
same statistical operation (median/MAD baseline fit on the entire window set instead of interictal-only),
not because it was part of the 2026-09-03 measurement.

#### 2. No post-ictal buffer exclusion

`preprocessing.py` excludes **4 hours after every seizure** from the thesis's interictal array
(`BUFFER_H`). The demo doesn't know where a seizure is, so it **can't exclude anything** — the entire
post-ictal segment goes straight through PELT.

Post-ictal EEG is genuinely abnormal (focal slowing, amplitude suppression, altered functional
connectivity). The demo is quite likely to **flag those segments**, while the thesis never scored them
at all.

In magnitude, this is a much larger source of difference than item 1: 4 hours × the number of
seizures, compared with 0.23% of windows for ictal.

**This is not a bug.** Within the post-hoc review triage framing, surfacing the post-ictal segment for a
clinician to see is clinically reasonable behavior — a clinician would still want to see it. But it must
be:
1. **observed at build step 1** (run 1 subject, see where events land relative to known seizures —
   *purely a human sanity check by eye, absolutely no labels going into the code*);
2. **stated out loud at the defense**, not left for the committee to discover on its own.

#### 3. Background statistics for the PELT penalty and the CPD threshold, estimated on the whole recording

`src/cpd_pipeline_v14.py` fits the PELT penalty's variance and the change-point magnitude threshold from
a background sample — the interictal segment, when a label mask is available (see that file's own
header: penalty variance "from the interictal/background" and a magnitude "threshold calibrated from
background CP magnitudes"). The demo has no such mask, so both statistics are estimated from **the
whole recording** instead — the same file's header states this explicitly for the label-free case
("PELT variance and the magnitude threshold from the WHOLE recording"). §1.5's PELT step already notes
the practical side of this ("the algorithm needs enough background to estimate stably, no splitting
into separate short-file runs"); this item records the statistical side — it is the same
"interictal-only, in the thesis, becomes whole-recording, in the demo" pattern as item 1, applied to
Stage 2's PELT/threshold calibration instead of Phase B's per-window normalization. Kept as its own
item, matching the thesis report's own separate enumeration, rather than folded into item 1.

Not separately measured against an AUROC/Spearman-style criterion the way item 1's `zlatent` row was —
flagged here as a gap, not silently treated as harmless.

**Mandatory consequences to record (for all three items):**
- **The demo's numbers WILL differ from the thesis's numbers.** They must never be forced to match,
  never adjusted to match.
- The demo **does not** display any evaluation metric (sensitivity, FP/day, AUROC, operating-point
  mag_pct/pen_mult). Those numbers belong to the thesis, not the product.
- This divergence must be **reported to the advisor** (Assoc. Prof. Hà Thị Thanh Hương) because it's a
  methodological decision.

**Prepared answer for the committee** — *"why does the demo find different events than the table in the
report?"*:
> The report evaluates on an interictal segment that has been noise-filtered, has the 4-hour post-ictal
> window excluded, and has labels, following the SzCORE protocol. The demo runs completely label-free on
> the intact continuous recording — including the post-ictal segment — because that's what a new
> patient's situation actually looks like. Same model, same weights, two different input conditions, so
> the two result sets not matching is expected, not anomalous. Specifically, the demo may flag the
> post-ictal segment that the report never scored at all; within a post-hoc review framing, that's
> reasonable behavior, not a false positive.

### 1.7 Cost — measured, decided to run live

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
> fixed**.

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
  - Row 1's name **must not** use the word "Probability": the ensemble score is a robust z-score, which
    can be negative or positive, not a [0,1] probability.
  - Y-axis: **shows no numbers** at either end. Only draws a **zero line** + relative height,
    auto-scaled to the P1–P99 percentile of **the currently viewed file itself** (avoids one outlier
    stretching the axis). Reason for dropping numbers: this box is small, a quick-glance role; and a
    z-score has no absolute clinical meaning worth reading as a number.
- Has a playhead (▼) synced with Panel EEG.
- **View-only, no interaction.** Clicks only work on Panel EEG.

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
| `lff 0.5 Hz` · `hff 60 Hz` · `60` | 3 filters matching the real preprocessing steps exactly |

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

- **Panel title:** `Channel-level reconstruction anomaly — Event N`
  *(revised from "Channel contribute to ..." in the mockup — the old phrasing implies a causal/
  localizing relationship.)*
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
| O1 | **The demo's operating point** (the event-detection threshold). The FP-budget procedure is label-free so it's usable, but the **specific budget value** must be **read from a file** (`src/retrain/fp_budget_operating_point.py` + `docs/RESULTS_OF_RECORD_phaseB.md`) at build time — **absolutely never type it from memory** | read the file |
| O2 | **PELT parameters** (penalty, model, min_size) — take them exactly from `src/cpd_pipeline_v14.py`, don't re-choose them | read the file |
| ~~O3~~ | ~~what the demo's robust-z fits on~~ — **CLOSED 2026-09-03**: `retrain_io.robust_z` already fits on the entire window set (lines 56–60). Not a divergence, nothing to handle | closed |
| O4 | **Which subject to use for the live-upload scenario** — chosen by real file count, measured while building the cache | measure |
| O4b | **The extent of post-ictal flagging** (§1.6 item 2) — observed at step 1, decide whether to call it out separately in the defense slides. No adjusting the model, no adjusting the threshold to "fix" it | observe |
| O5 | **Gamma-AEC in the continuous path** — `dataprep/compute_gamma_aec.py` currently runs on the already-split array; a continuous version is needed | write new code in `pipeline_demo.py` |
| O6 | **`evaluation_protocol.py` and `stat_validation.py` were just restored to `src/`** (2026-09-03, tag `repo-deps-fixed`) after being mistakenly archived while still being imported. `fp_budget_operating_point.py` depends on this chain — verify the `import` runs before pulling parameters for O1 | 1 command |

None of these items block starting to build the frontend.

---

*End of SZSCAN_SPEC_v5.md. Fully replaces `WEB_DEMO_SPEC_v4.md` and `WEB_DEMO_CONTEXT_BOUNDARY.md`.*
