# PHASE C PLAN — Clinical Review Demo (ACTIVE, IN PROGRESS)
**Status: SPEC + 1 core module written. The former blocking prerequisite (attribution
re-run on the new ensemble weight) is RESOLVED — see §5. Backend/frontend work can
start once the UX/UI design step (§7) is complete. This file is a living plan, not a
locked decision record — update it as work progresses, the same way PLAN_AND_STATUS.md
is used for Phase A/B.**

**Last updated: 2026-07 (this session) — changes made:**
1. §5 blocking prerequisite RESOLVED: per-node GAE reconstruction-error attribution
   is weight-invariant (confirmed in `ATTRIBUTION_PREREGISTRATION_v3_1.md` §1.3) —
   no re-run needed before building the attribution layer. The existing
   `attribution_pernode_summary.csv` / per-window `pernode.npy` files can be used
   as-is. Formal validation (Test A / Test D from the v3.1 pre-registration) is a
   separate, optional track and does NOT gate the demo — see §5.1.
2. §7 timeline replaced with a concrete 9-week calendar (27/8–27/9) aligned to the
   real constraint: a supervisor review sometime in 17/8–29/8, then a 2-week
   writing sprint (deadline 15/10). Explicit steps added that were previously
   missing: a dedicated **UX/UI design week before any frontend code**, a
   dedicated **testing week** (end-to-end + numeric-consistency check against
   `RESULTS_OF_RECORD.md`), and a genuine **buffer week** (not conflated with
   polish work). If the buffer isn't needed, move straight to writing — finishing
   early is preferred over using the full 9 weeks.
3. §2 (staged scope) gets one clarifying line: UX/UI design is its own step,
   not folded silently into "Stage 1 code."
4. §8 open question #1 (attribution re-verification scope) marked RESOLVED,
   pointing to the v3.1 pre-registration's answer.

---

## 0. WHY PHASE C CHANGED FROM OPTIONAL TO MANDATORY (2026-07/08)

Originally Phase C (web demo) was optional/deferred (see PHASE_B_AUDIT_handoff.md
§6, PLAN_AND_STATUS.md Decision #19-era note: "Phase C (web demo) deferred by
decision"). This changed based on mentor feedback:

1. **Mentor sees clinical potential** and wants to arrange a real neurologist to
   review the tool and give feedback/testing on it — this raises the credibility
   bar for the demo beyond "illustrative prototype."
2. **Student (Boti) wants a portfolio-grade artifact** — separate motivation from
   (1), with different quality expectations (polished UI/UX, potentially public
   deployment later).
3. Mentor also encourages (but does not require) writing this thesis into a
   paper before the defense — noted here for completeness, tracked separately
   in PLAN_AND_STATUS.md, not part of Phase C's scope.

**Net effect: Phase C is now MANDATORY**, scoped initially to serve (1) — the
neurologist review — with (2) — portfolio polish — folded in from the start
since both want "done properly," but with an explicit staging strategy (§2) so
neither goal blocks the other or inflates the 3.5-month budget unnecessarily.

---

## 1. WHAT THE DEMO IS FOR (locked)

- **User:** a neurologist doing post-hoc EEG review — not an ML engineer. No
  ML jargon shown directly (no "AUROC," no "z-score ensemble" in the UI).
- **Task:** given a long multi-hour EEG recording, quickly identify which
  segments are worth reviewing, confirm/reject by looking at the raw EEG at
  that segment, and understand roughly why the model flagged it (which
  channels drove the anomaly).
- **Success criterion:** less time spent than reviewing the full recording;
  no missed seizures; the clinician trusts the tool enough to use it as an
  assistive aid (not a replacement for their judgment).
- **Framing (must stay consistent with the thesis's own framing, see
  Proposed_solution_updated_v4.md §II):** post-hoc review assistance, NOT
  real-time alarm. The demo must not imply real-time capability it doesn't
  have.

---

## 2. STAGED SCOPE (locked)

### Stage 1 — MANDATORY, this thesis cycle
- Data: the 8 already-evaluated CHB-MIT test subjects (chb03, 06, 13, 14, 15,
  16, 17, 18) — clinician reviews EEG they can compare against the model's
  flagged segments. This is a **valid, meaningful clinical review task**
  even though the data is not novel to the researcher: the neurologist is
  independently assessing whether the flagged segments correspond to real
  electrographic events, which is exactly the post-hoc review use case the
  thesis targets.
- Architecture: FastAPI backend (CPU-only, no GPU needed at request time) +
  React frontend (SPA).
- Access: **local only** — run on a laptop/workstation, demo in person to
  the clinician and to the mentor. No public deployment, no hosting/security
  concerns for this stage.
- Portfolio polish (UI/UX quality) is folded into Stage 1 from the start
  (this was an explicit choice — see §0.3), since the same codebase serves
  both purposes; it does NOT mean adding scope beyond the 3 layers in §4.
- **UX/UI design is its own step, done BEFORE any frontend code is written**
  — not silently folded into "coding the frontend." Concretely: wireframes/
  layout decisions + the clinician's click-through flow for all 3 layers
  (§4) must be settled first (see §7's Week 2), then React components are
  built directly against that settled design. Designing and coding at the
  same time is what causes rework; this is why the two are sequenced as
  separate weeks in §7 rather than merged into one "build frontend" block.

### Stage 2 — DEFERRED, no committed timeline
- Accepting a genuinely new EEG recording (upload .edf) and running the FULL
  pipeline (preprocessing → wPLI/AEC → GAE → LSTM → gamma → ensemble → CPD)
  on the lab workstation GPU. This is a real productionization effort
  (refactoring Kaggle-notebook-cell code into a callable service) and is
  explicitly NOT committed to any date.
- Real hospital data: explicitly OUT OF SCOPE for now. Would require IRB/
  ethics approval (outside Claude's technical purview) and is not assumed
  to happen before the thesis defense. If it becomes relevant, Stage 2's
  architecture should already support it (same GPU pipeline, different
  input source) — but this is not being built preemptively.
- Public deployment (Vercel/Render, etc.) for portfolio use — deferred to
  after the defense if it adds pressure to the pre-defense timeline (per
  Boti's own stated flexibility on this point).

---

## 3. ARCHITECTURE (locked)

```
┌─────────────┐     GET /subjects              ┌──────────────────┐
│   Frontend   │ ──────────────────────────────▶│  FastAPI backend │
│  (React SPA) │     GET /subjects/{id}/timeline│  (Python, CPU)   │
│              │◀──────────────────────────────  │                  │
│              │     GET /subjects/{id}/eeg      │  Wraps:          │
│              │     ?start_s=&end_s=            │  cpd_pipeline_v14│
│              │◀──────────────────────────────  │  + cached scores │
│              │     GET /subjects/{id}/segments │  + cached        │
│              │       /{seg_id}/attribution     │    attribution   │
│              │◀──────────────────────────────  │  + raw .edf      │
└─────────────┘                                  └──────────────────┘
```

**Key property:** the backend does NOT need GPU to serve the demo. Every
ensemble score and attribution value is pre-computed offline (Kaggle/lab
workstation, one-time) and cached as `.npy`. At request time, the backend
only: (a) runs `cpd_pipeline_v14.detect_events` (CPU, fast, label-free path)
on cached scores, (b) slices the corresponding raw `.edf` segment via
`pyedflib`, (c) looks up cached per-window attribution values. GPU is only
needed OFFLINE, once, to (re-)generate the cached `.npy` files themselves.

**Backend stack:** FastAPI (chosen for auto-generated docs + type checking +
easy reuse of existing Python functions from `cpd_pipeline_v14.py`,
`szcore_eval.py`, `evaluation_protocol.py`).

**Frontend stack:** React SPA (chosen over static HTML for portfolio quality
and because Stage 1 already folds in UI/UX polish, see §2).

**EDF reading library: `pyedflib`** (not `mne`) — chosen because it can read
an arbitrary time-slice of a large `.edf` file without loading the whole
file into memory, which matters when a clinician is scrubbing through
different segments of an 18+ hour recording quickly.

### 3.1 Proposed folder structure

```
demo/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, router mount
│   │   ├── routers/
│   │   │   ├── subjects.py      # GET /subjects, /subjects/{id}/timeline
│   │   │   ├── eeg.py           # GET /subjects/{id}/eeg
│   │   │   └── attribution.py   # GET /subjects/{id}/segments/{seg_id}/attribution
│   │   ├── services/
│   │   │   ├── cpd_service.py   # wraps cpd_pipeline_v14.detect_events
│   │   │   ├── edf_index.py     # WRITTEN — window/time -> (edf file, offset) lookup
│   │   │   ├── edf_reader.py    # NOT STARTED — pyedflib-based sample decoding
│   │   │   └── data_paths.py    # single source of truth for where cached files live
│   │   └── models.py            # Pydantic response schemas (matches §4's data contract)
│   ├── data/                    # symlink or copy: cached scores + attribution + .edf files
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── SubjectPicker.tsx
    │   │   ├── SuspicionTimeline.tsx    # Layer 1
    │   │   ├── EegViewer.tsx            # Layer 2
    │   │   └── AttributionHeatmap.tsx   # Layer 3
    │   ├── api/client.ts          # typed fetch wrappers matching backend schema
    │   └── App.tsx
    ├── package.json
    └── vite.config.ts
```

**Status vs. this structure:** only `backend/app/services/edf_index.py` exists
(untested against real data, see §6). Every other file/folder above is
planned but not yet created.

---

## 4. THE 3 LAYERS (locked, content) / DATA CONTRACT (locked, schema)

### Layer 1 — Timeline of suspicion
Whole-recording overview; clinician picks a segment to inspect.
```
GET /api/subjects
→ [{ "id": "chb15", "duration_h": 18.7, "n_flagged": 5 }, ...]

GET /api/subjects/{id}/timeline
→ {
    "duration_s": 67320,
    "window_sec": 4,
    "score_series": [0.2, 0.3, ...],   // downsampled anomaly score, ~1 point/min
    "segments": [
      { "id": 0, "start_s": 400, "end_s": 420, "magnitude": 0.83,
        "top_channels": ["F7-T7", "T7-P7"] }
    ]
  }
```
**Schema decision (locked 2026-07, replaces the earlier "confidence": "high"/"moderate"
string field shown in an earlier wireframe draft):** the segment field is
**`magnitude: number` (continuous, roughly 0–1 normalized)**, not a discrete confidence
tier. Rationale: the system produces no calibrated probability of seizure — only a
relative CPD change-point magnitude / ensemble z-score. Labeling that "high confidence"
implies a validated clinical threshold that does not exist, which is exactly the kind of
overclaim `ATTRIBUTION_PREREGISTRATION_v3_1.md` §6 forbids for the attribution layer
("claim highlighting only... never claim... localization accuracy"). The same discipline
must apply here for consistency — a thesis that is rigorous about overclaiming in one
layer (attribution) and loose about it in another (detection confidence) is an internal
contradiction a reviewer will catch. The frontend renders `magnitude` as a continuous
color/opacity ramp (see the wireframe) with an explicit caption: *"shade reflects the
magnitude of the detected connectivity shift, not a calibrated probability of seizure."*
This is also the schema already used in `demo/ai_studio_brief.md`'s mock JSON — this
edit brings the plan document back in sync with it.

### Layer 2 — Raw EEG waveform for a chosen segment
```
GET /api/subjects/{id}/eeg?start_s=&end_s=
→ { "channels": ["FP1-F7", ...], "fs": 256, "data": [[...], [...], ...] }
```
Backed by `edf_index.py` (window→file mapping, ALREADY WRITTEN, see §6) +
a not-yet-written `edf_reader.py` (actual sample decoding via `pyedflib`).

### Layer 3 — Per-channel attribution heatmap for a chosen segment
```
GET /api/subjects/{id}/segments/{seg_id}/attribution
→ { "channels": [...], "z_scores": [...] }
```
Source: per-window GAE reconstruction-error z-scores, from the
`{subj}_{split}_pernode.npy` files (shape `[n_win, 18]`) already produced in
Phase B — NOT the per-seizure-averaged summary CSVs
(`attribution_pernode_summary.csv`/`profile.csv`), which are too coarse for
"show me the attribution at exactly this flagged segment." **This decision
is locked** (there is no other granularity available that would answer the
demo's actual question).

---

## 5. ATTRIBUTION PREREQUISITE — ✅ RESOLVED (was: blocking; no longer blocks anything)

**Original concern (2026-07/08):** Decision #19 changed the ensemble weight
from (0.35, 0.30, 0.35) to (0.40, 0.35, 0.25) for the main event-level
results (Phase A). At the time it was unclear whether Layer 3 (attribution)
would silently use a stale, old-weight cache while Layer 1 (timeline/CPD)
used the new weight — exactly the class of stale-cache bug this project has
hit before (see `RESULTS_OF_RECORD.md` §13–14). The plan at the time was to
re-run the GPU attribution-dump step on the new weight before building
anything.

**Resolution (confirmed in `ATTRIBUTION_PREREGISTRATION_v3_1.md` §1.3):**
per-node GAE reconstruction-error attribution is derived **only** from the
GAE's own reconstruction score — it does not pass through the ensemble
mixing weights at all. Quoting the pre-registration directly: *"Test A uses
per-node GAE reconstruction error only; ensemble mixing weights do not
enter. Weight-invariant — no re-run required."* This is the same reasoning
already used to mark §7 of `RESULTS_OF_RECORD.md` weight-invariant under
Decision #22 — it is not a new argument invented for the demo, it is the
existing one applied here.

**Practical consequence: there is no GPU re-run to wait for.** The demo's
attribution layer can be built directly from the artifacts that already
exist (`attribution_pernode_summary.csv`, and the per-window
`{subj}_{split}_pernode.npy` files referenced in §4's Layer 3). Backend/
frontend coding is blocked only by the UX/UI design step (§7), not by any
attribution recomputation.

**Claim-scope reminder for the demo UI (per `ATTRIBUTION_PREREGISTRATION_v3_1.md`
§6):** the permitted framing is *"the attribution surfaces seizure-associated
channels to support human EEG review"* — never localization, SOZ, or
epileptogenic-focus language. This applies regardless of which validation
track (§5.1) the attribution numbers come from.

### 5.1 Separate, non-blocking track: formal attribution validation (v3.1 Test A / Test D)
`ATTRIBUTION_PREREGISTRATION_v3_1.md` specifies two pre-registered statistical
tests (Test A — concentration vs. a length-matched null; Test D — TP-vs-FP
triage value) that would strengthen the *scientific* claim made about
attribution in the thesis body. **This track is independent of the demo:**
- The demo uses the existing per-node reconstruction error as an
  **illustrative "suspicion" visual**, with the claim-scope language above —
  it does not depend on Test A/Test D having been run.
- Running Test A/Test D (`attribution_v3.py`, `attribution_tpfp.py` per the
  pre-registration's §7 execution plan) is optional, separate work that can
  happen in parallel with or after Phase C, and only matters for how
  strongly Chapter 3/4 can characterize the attribution (distributed vs.
  concentrated; useful for FP triage or not) — it does not gate any Phase C
  deliverable.

---

## 6. WHAT HAS ACTUALLY BEEN BUILT SO FAR

| File | Status | Purpose |
|---|---|---|
| `demo/backend/app/services/edf_index.py` | **Written, NOT yet tested against real data** | Maps a subject's global chronological window/second offset to (edf filename, local offset), reusing `evaluation_protocol.parse_summary_edf_list` (no new parsing logic). Smoke-testing on real CHB-MIT summary files not yet done. |
| `edf_reader.py` | Not started | Will use `pyedflib` to actually decode EEG samples for a given (fname, local_start_s, local_end_s) from `edf_index.locate_range()`. |
| FastAPI app (`main.py`, routers, models) | Not started | — |
| React frontend (any component) | Not started | Only a static wireframe mockup was shown in-chat (not committed code) for the Layer-1 timeline view. |

**Honest summary: Phase C is at the very beginning of implementation.** The
architecture and data contract are locked; almost no code exists yet beyond
one untested utility module.

**Cross-reference (not a Phase C artifact, but affects it):**
`mag_pen_grid_sweep_v2.py` (in the main thesis codebase, not `demo/`) was
written to fix the seeding bug described in §8 item 3 and re-verify the
Pareto-optimal operating points. Its output determines which sensitivity/
FP-day figures the demo's Layer-1 confidence thresholds should ultimately
reference — check its results before finalizing §8 item 2.

---

## 7. TIMELINE — 9-WEEK CALENDAR (27/8–27/9), THEN 2-WEEK WRITING SPRINT

**Real constraint driving this plan:** a supervisor review ("phản biện")
happens on one day sometime in 17/8–29/8; after that there are 9 weeks
(27/8–27/9) before a mandatory 2-week writing sprint that must end by the
15/10 submission deadline. Phase C is the active priority within those 9
weeks; the thesis chapters that don't depend on the demo (Intro,
Methodology, Literature Review) can and should be drafted in parallel from
week 1, not after Phase C finishes.

**Explicit principle: finishing early is preferred over using the full 9
weeks.** The buffer week (Week 6 below) exists to absorb slippage — if it
isn't needed, move straight to writing rather than adding scope to fill
time.

| Week | Dates (approx.) | Focus | Notes |
|---|---|---|---|
| 1 | 27/8–2/9 | Supervisor review meeting (1 day within this window) | In parallel: smoke-test `edf_index.py` against real CHB-MIT summary files (cheap, unblocks everything downstream, not yet done — see §6) |
| 2 | 3/9–9/9 | **UX/UI design** (before any frontend code) | Wireframes + the clinician's click-through flow for all 3 layers (§4); settle layout/information-placement decisions here so React components in Week 4 are built once, not iterated on mid-build. Can compress to a few days if the design is simple and already clear in the researcher's head — this is the easiest week to shorten if time is tight. |
| 3 | 10/9–16/9 | **Backend** (FastAPI, 3 endpoints) | `edf_reader.py` (pyedflib decoding), `cpd_service.py` wrapping `cpd_pipeline_v14.detect_events`, the attribution route reading the existing per-node files (§5 — no GPU re-run needed). Unit tests written alongside, not deferred. |
| 4 | 17/9–23/9 | **Frontend** (3 React components) | Built directly against the Week 2 design — no re-designing mid-build. `SuspicionTimeline`, `EegViewer`, `AttributionHeatmap`. |
| 5 | 24/9–27/9 (spills slightly past the nominal 9-week mark if needed) | **Testing** — explicit, not an afterthought | Two distinct checks: (a) end-to-end run across all 8 test subjects, not just 1–2 demo subjects; (b) **numeric-consistency check** — every number the demo displays (sensitivity, FP/day, operating point) must match `RESULTS_OF_RECORD.md` exactly, confirming the demo builds the ensemble via `ensemble_recipe.build_ensemble` under the current weight and never reads the quarantined old-weight cache (`results/history_superseded/oldweight_ens_scores/`). This is the same class of bug that has bitten this project before (§13–14 of `RESULTS_OF_RECORD.md`) — treat it as a real risk, not a formality. |
| **Checkpoint** | end of Week 5 | **Go/no-go** | If the demo is not running end-to-end on all 8 subjects by here, cut scope immediately (see below) rather than letting the buffer week absorb new work. |
| 6 (buffer) | — | **Genuine buffer, not polish-with-a-different-name** | Used ONLY if Weeks 2–5 slipped. No new features started here. If not needed, skip straight to the writing sprint — this is where "finishing early" actually happens. |
| 7–9 | — | **Writing sprint (2 weeks, hard deadline 15/10)** | Demo becomes source material (screenshots/figures for Ch.3, Discussion, Clinical applicability). Intro/Methodology should already be well underway from Week 1, not starting here. |

**If Week 5's checkpoint fails, cut in this order** (cheapest-to-restore-
credibility first): (1) drop React polish, keep functionality — a plain
HTML frontend calling the same FastAPI backend still satisfies "the
neurologist can review flagged segments"; (2) drop Layer 3 (attribution
heatmap) and demo only Layers 1–2 — the core clinical review task (spot a
flagged segment, look at the raw EEG) survives without it; (3) reduce the
demo subject set from 8 to a smaller representative subset (e.g. 3–4
subjects spanning strong/weak/structural-failure cases) rather than all 8 —
document this explicitly as a scope reduction, not a silent omission.
Never cut the numeric-consistency check (5b) — a demo showing wrong numbers
is worse than a smaller demo.

---

## 8. OPEN QUESTIONS (must be resolved, in roughly this order)

1. **[RESOLVED — see §5]** Attribution re-verification scope: does
   re-computing attribution on the new weight require re-running the full
   C1-C3 validity battery, or can it inherit the existing methodology's
   validity since only the weight changed? — **Resolved: no re-computation
   is needed at all.** Per-node GAE reconstruction-error attribution never
   passes through the ensemble weight (`ATTRIBUTION_PREREGISTRATION_v3_1.md`
   §1.3, "Weight-invariant — no re-run required"), so the question of
   re-running C1-C3 on a *new weight* doesn't arise — there is no
   weight-dependence to re-verify. Formal validation (Test A/Test D from
   v3.1) remains a separate, optional, non-blocking track — see §5.1.
2. **[RESOLVED — see §4]** Confidence-level thresholds for Layer 1's segment
   coloring — **resolved as: no discrete thresholds.** The field is
   `magnitude: number` (continuous), rendered as a color/opacity ramp, not
   binned into "high"/"moderate"/"low" tiers. This was a deliberate reversal
   of an earlier wireframe draft that used discrete `confidence` strings —
   see §4's schema-decision note for the full rationale (no calibrated
   probability exists; discrete tiers would overclaim). `demo/ai_studio_brief.md`
   already uses this schema; this plan document is now consistent with it.
3. **[RESOLVED]** The seeding bug in the original `mag_pen_grid_sweep.py`
   (per-mag_pct results depended on loop order because `np.random` wasn't
   reseeded between calls) is fully fixed and closed — see
   `RESULTS_OF_RECORD.md` §13 for the full postmortem and Decision #20 for
   the re-derived high-sensitivity operating point (`mag50/pen0.5`, adopted
   and locked). The demo's Layer-1 magnitude ramp (item 2 above, now a
   continuous field rather than discrete tiers) should still be normalized/
   anchored with reference to the CURRENT locked operating points —
   balanced (mag60/pen1.0) and high-sensitivity (mag50/pen0.5) — not any
   value from before Decision #20.
4. **Whether the neurologist review happens on THIS local-demo build, or
   whether the mentor has a different/more specific format in mind** — not
   yet confirmed with the mentor directly; recommend confirming before
   investing in Stage 1's UI polish specifically for that meeting.

---

## 9. WHAT TO DO WHEN RESUMING THIS IN A NEW CHAT

1. Decision #19's reproducibility check is resolved (§8 item 3) — no action
   needed here; `RESULTS_OF_RECORD.md` / `PLAN_AND_STATUS.md` are current.
2. The attribution prerequisite (§5) is resolved — no GPU re-run is needed;
   per-node reconstruction-error attribution is weight-invariant. Backend/
   frontend work is gated only by the UX/UI design step (§7, Week 2), not
   by attribution.
3. `edf_index.py` exists but has NOT been smoke-tested against real CHB-MIT
   summary files yet — do that before building anything on top of it.
4. No FastAPI or React code exists yet beyond the plan in this document.

---

*This is a living planning document, not a locked decision record. Update
it as Phase C progresses, the same way PLAN_AND_STATUS.md tracks Phase A/B.*
