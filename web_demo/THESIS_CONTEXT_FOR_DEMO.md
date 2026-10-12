# THESIS_CONTEXT_FOR_DEMO.md

**Rev. 2026-10-10 (final system).** Written by the thesis project (`PROJECT2_SETUP.md` §9.2(B): the thesis
changed what the demo depends on — the pipeline, the checkpoint and the attribution readout). Replaces the
rev that described the earlier system (V1, "rlg"). The work plan that goes with it is
`docs/HANDOFF_T1_DEMO_REBUILD.md`.

**Purpose.** Everything the demo build needs to know about the thesis — and nothing more. The scientific
documents govern the thesis; this file governs what the demo may assume about it.

**Authority.** A summary, not a source of truth. If it disagrees with `docs/DEMO_REBUILD_BRIEF.md`,
`docs/PROVENANCE_V2.md` or the frozen code (tag `p3-frozen`), those win and this file must be fixed. For
demo behaviour, `web_demo/SZSCAN_SPEC_v5.md` wins over this file.

---

## 1 · What the thesis does

Unsupervised temporal localization (onset and offset) of epileptic seizures in scalp EEG: a graph
autoencoder over per-window functional-connectivity graphs gives one ensemble anomaly score; a
per-patient alarm budget turns it into events; kernel change-point detection refines each event's
boundaries.

**Framing, which the product must match: post-hoc EEG review triage.** A clinician already has the
recording; the system points at segments worth a second look. Not a real-time alarm, not a validated
clinical device.

**Data.** CHB-MIT scalp EEG, 18-channel bipolar montage, 4-s non-overlapping windows at 256 Hz,
band-pass 0.5–60 Hz plus 60 Hz notch, per-subject z-scored.

**Splits (locked).**

| split | subjects |
|---|---|
| training (12) | chb01, 02, 04, 05, 07, 08, 09, 12, 19, 20, 21, 23 |
| validation (3) | chb10, 11, 22 |
| **test (8)** | **chb03, 06, 13, 14, 15, 16, 17, 18** |

The demo serves **only the 8 test subjects**. Serving a training subject would demonstrate on training data.

---

## 2 · The pipeline the demo re-implements (the final system, tag `p3-frozen`)

```
per file:     18 channels → band-pass + notch (whole file) → 4-s windows → signal-loss flags
per subject:  z-score statistics, label-free (every 10th window of the whole recording)
per window:   CAR → wPLI + AEC → top 20 % edges ; band powers (5) ; 7 added node features
              → GAE v2 clean seed 42 (node input 30 = adjacency row 18 + band powers 5 + 7 features)
              → 16-d latent per channel
per subject:  per channel, LedoitWolf Mahalanobis distance of the latent (all signal windows)
              → per-channel robust-z → order statistics 6, 9, 12 + channel mean
              → each minus its ±15-min running median inside each file → patient percentile
              → equal mean = ONE ensemble anomaly score per window
              → alarm budget p_i = clip(q_i(k), 0.005, 0.02)        (k etc. from freeze.json)
per file:     detector: 5-window smoothing, (1 − p_i) quantile threshold, runs, merge ≤ 90 s
              → kernel change-point localizer (2 change points around each event)
```

Defining code (read-only; import, never copy or edit): `x1_external.py` (label-free statistics, the
template for a recording the thesis never saw), `c1b_build_trainset.py` (graph, features),
`p2_dump_seeds23.py` (GAE forward pass), `e22_test_oneshot.final_scalar` (ensemble score),
`p3_levers.py` (budget, localizer), `p2_scalars.py` (detector), `e18_cpd_localizer.py`,
`results/p3c_freeze/freeze.json` (parameters). Exact table: `docs/HANDOFF_T1_DEMO_REBUILD.md` §2.

**Gone from the final system:** the reconstruction readout, the graph-mean latent readout, the gamma-AEC
readout, the 1/3 ensemble, PELT (`cpd_pipeline_v14`) and the fixed operating point
(`fp_budget_operating_point`). Text that describes them as current is stale. There is still no LSTM.

**Non-causal by design.** The ±15-min median and every per-patient fit need the whole recording before an
event is final; the demo processes a subject's files, then scores. Matches post-hoc review.

---

## 3 · The one checkpoint the demo may load

```
data/models_v2/gae_v2_clean_seed42.pt     20021 bytes
sha256 6e310307b046407a18d839273b84c74b2905457ec6ace892b674c6972dac590f   (docs/PROVENANCE_V2.md)
data/models_v2/gae_v2_clean_seed42.json   (training constants of the 7 added features)
sha256 d1e2eee9924b9c23aedf1d8da0e2d289e88d2f790ff90c34958aa850870f06c5
```

Identify by hash, never by filename. `gae_v2_all_*`, seeds 1/2/3 and every V1 checkpoint
(`data/models_retrain/*`, `archive/pre_rebuild_s0/`) are **not** the demo's model.

---

## 4 · The demo's relationship to the thesis numbers

**The demo displays no evaluation metric** — no sensitivity, FP/day, AUROC, precision, alarm budget or
any parameter. Those belong to the report.

**One divergence only.** The thesis's CHB-MIT runs z-score each patient with statistics that exclude
annotated seizure windows and a 4-h post-seizure buffer (inherited preprocessing, disclosed in the
report). The demo cannot see labels, so it uses every 10th window of the whole recording (the rule the
thesis already used for its external validation). Everything else — the per-patient LedoitWolf fits,
robust-z, percentiles, the budget — is fitted on the whole recording **in the thesis system too**, and the
thesis also scores post-ictal segments. So the earlier three-item divergence list is closed.

How close the demo is: measured, not assumed. The identity gate feeds the demo the thesis statistics on
chb03 and requires the thesis's own event counts; then the label-free statistics are switched on and the
difference is reported (`results/t1_demo/GATE.md`). **Never tune the demo toward the thesis numbers.**

---

## 5 · Channel panel — the constraint that matters for the UI

The panel shows, per channel, the p95 over the event's windows of the absolute robust-z of that channel's
latent distance — the per-channel quantity the final system ranks. It is **neutral XAI**: which channels'
latent states are most unusual for this patient during the event.

**It is not localization and not seizure-onset zone.** The thesis tested this exact quantity against a
blind, supervisor-approved channel annotation (and the earlier reconstruction readout before it): both
gave the same pre-registered negative — the ranking does not follow where a reader sees the discharge.

UI consequences:
- Panel title: `Channel-level latent anomaly — Event N`.
- No causal or localizing language ("channel causing", "focus", "origin", "source").
- No attribution metric on screen.
- Works for user-created events exactly as for AI events (computed from the event's own range); windows
  with signal loss have no latent and are skipped.

---

## 6 · What is closed and must not be reopened

Performance work is closed. The model, the score, the budget rule, the detector and the localizer are
frozen. The demo never proposes a model change, a reweighting, a new feature, a threshold change or a
"small improvement". **There is no operating-point lever any more:** the budget is part of the frozen
system and is computed label-free per patient.

---

## 7 · Vocabulary

| Term | Meaning here |
|---|---|
| **window** | 4 s of EEG; `t_seconds = window_index × 4` within a file |
| **ensemble anomaly score** | the one per-window score (patient percentile mean, in [0, 1]); shown as `Seizure Detection Score` |
| **alarm budget** | the share of a patient's time the detector may flag, set label-free per patient; internal, never shown |
| **event** | a detector run after the change-point localizer; what the UI shows |
| **label-free** | uses no annotation at any step; the demo's central claim |
| **interictal / ictal** | thesis vocabulary, never surfaced in the UI |
| **SzCORE** | the event-scoring standard used by the thesis; never used inside the demo |
