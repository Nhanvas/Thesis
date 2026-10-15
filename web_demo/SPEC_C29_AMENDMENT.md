# SPEC_C29_AMENDMENT.md

Rev. 2026-10-09. Dated amendment for task T1 (pipeline rebuilt on the final thesis system). Save to
`F:\Study\Thesis\Code\web_demo\SPEC_C29_AMENDMENT.md`. Whole-file rewrites of SPEC / DESIGN / HANDOFF follow
after the build settles; until then this file **overrides** the sections it names. Authority: UI mockups >
SPEC v5 **as amended here** > DESIGN > HANDOFF.

Items marked `PROPOSED` need Boti's decision. Items marked `CONFIRM` depend on Project #1 / the thesis code.

---

## A · SZSCAN_SPEC_v5.md — amendment C29

### C29.1 · Pipeline (replaces §1.3)

The backend computes the final thesis system (tag `p3-frozen`, GAE v2 seed 42) from the raw EDF, label-free:

1. Per 4 s window: CAR → wPLI + AEC → strongest 20 % of edges → node input 30 (adjacency row 18, band powers 5,
   7 added features), scaled with the training constants saved beside the checkpoint, clip ±4 → [0,1].
2. GAE v2 encoder → 16-d node latent per channel.
3. Per subject, per channel: LedoitWolf Mahalanobis distance of the latent (fitted on non-signal-loss windows)
   → robust-z (median/MAD).
4. Members: 6th, 9th, 12th largest of 18 channels and the channel mean. Each minus a centred ±15-min
   (451-window) running median inside the file; each converted to a subject percentile; the equal mean is the
   ensemble anomaly score.
5. Detector: per-file centred 5-window moving average (signal loss = NaN, min_periods 1); per-patient budget
   p_i = clip(q_i, lo, hi); threshold = (1 − p_i) quantile of the subject's smoothed score; contiguous runs;
   merge ≤ 90 s.
6. Localizer: kernel CPD on the unsmoothed score over each event ± 15 windows inside the file; accept the middle
   segment if ≥ 2 windows and its mean exceeds both outer segments, else keep detector boundaries; merge again.

All constants (k, lo, hi, smoothing, merge, CPD settings) are read at runtime from `results/p3c_freeze/freeze.json`
and the thesis modules. **No constant is written in this spec or in demo code.** PELT, the reconstruction / gamma /
graph-mean readouts, the 1/3 weights and the fixed 50 / 2.0 / 90 operating point no longer exist.

### C29.2 · Events (replaces §1.5)

Events live **inside one file**: detection, smoothing, the running median and the localizer all operate per file.
The offset assignment and cross-file event logic of §1.5 are obsolete. `CONFIRM`: the 90 s merge never joins
runs across a file boundary (check `p2_scalars.d1_events`).

Because the running median, the percentiles and the budget are subject-level, **events become final only after
the whole subject has been processed.** Per-file results shown before then must be labelled provisional or not
shown; the existing subject-level status handling stays.

### C29.3 · Divergence from thesis output (replaces §1.6)

The demo differs from the thesis offline output by construction:

- z-score statistics are taken from every 10th window of the **whole recording**, label-free. The thesis
  CHB-MIT runs excluded annotated seizure and buffer windows.
- Per-subject fits (LedoitWolf, robust-z, percentiles, budget q_i) use all non-signal-loss windows of the
  uploaded subject, with no post-ictal buffer exclusion.
- Non-causal by design (±15-min median, subject-level fits): post-hoc review only.

The old AUROC / Spearman measurement of §1.6 is not transferable and is retired. Its replacement is the
**identity gate** (CLAUDE.md): same statistics → the demo chain reproduces the thesis code path on chb03 (max
absolute difference of the per-window score, event-list diff), then label-free statistics → compare with the
label-free chb03 row of the external pipeline. This is a correctness check, never tuning.

### C29.4 · Timing (replaces §1.7)

All earlier timing and memory figures belong to the earlier system and are void. New figures come only from M3
(median of ≥ 3 runs, hardware named) and M4. Unmeasured figures are not quoted anywhere, including UI copy.

### C29.5 · Mini-timeline score row (modifies §6.3) — `PROPOSED`, Boti decides

The score row plots the **ensemble anomaly score** (a [0,1] percentile mean), not a z-score:

- smoothed score (the series the detector thresholds);
- y-axis fixed by the P1–P99 of the subject, no numbers shown on screen;
- a thin reference line at the subject median;
- signal-loss windows drawn as gaps;
- no threshold line, no budget, no operating-point numbers (no metric on screen).

If Boti rejects this, the fallback is to keep the row geometry and plot the unsmoothed ensemble score.

### C29.6 · Attribution panel (modifies §6.7)

- Title: **`Channel-level latent anomaly — Event N`** (was the reconstruction wording).
- Definition: p95 of |per-channel robust-z of the latent distance| over the event's windows. Computed before the
  order statistic and the drift correction.
- `{stem}.pernode.npy` now stores the per-channel robust-z; `pernode_baseline.npy` is obsolete and removed from
  the data model.
- Same for user-created events (any window range).
- Wording limits unchanged: XAI for the GAE per-channel readout, **not localization, not seizure onset zone**; no
  causal or localizing words; no attribution metric on screen.

### C29.7 · Open items (§8)

O1, O2, O5, O6 are closed or obsolete (they concerned the per-subject operating point, the earlier timing and
the earlier baseline file). Remaining open items live in `BUILD_PROGRESS.md` §19.

### C29.8 · UI scope of T1

UI changes are limited to (a) the attribution title string and (b) the score row of C29.5. Nothing else in `UI/`
changes. Any other visible difference is a defect.

---

## B · SZSCAN_DESIGN_v2.md

§8, attribution-title row: replace the old title with `Channel-level latent anomaly — Event N`. No token changes.

## C · DEMO_BUILD_HANDOFF.md

- §4 (pipeline) is superseded by C29.1 and `DEMO_REBUILD_BRIEF.md`.
- §6 (nine build steps) is superseded by task T1 (`HANDOFF_T1_DEMO_REBUILD.md`); the steps are history.
- §8 timing belongs to the earlier system.

## D · PROJECT2_SETUP.md — project knowledge changes

- Add: `DEMO_REBUILD_BRIEF.md`, `HANDOFF_T1_DEMO_REBUILD.md`, `SPEC_C29_AMENDMENT.md`.
- Remove (Project #1 history, outside this project's scope): `PERF_PHASE_RECORD.md`, `HANDOFF_REPORT.md`.
- Replace with the new versions: `PROJECT2_INSTRUCTIONS.md` (paste into the Instructions box), `CLAUDE.md`,
  `THESIS_CONTEXT_FOR_DEMO.md`.
- After G3, refresh the stale code copies (`pipeline_demo.py`, `pipeline_worker.py`, `attribution.py`,
  `waveform_serving.py`, `MiniTimeline.jsx`, tests) and drop `cpd_pipeline_v14.py`, `ensemble_recipe.py`,
  `latent_anomaly.py`, `fp_budget_operating_point.py`, `gae_joint.py`, `compute_gamma_aec.py` if they are no longer
  imported by the demo. Keep them until the new pipeline is verified.

## E · BUILD_PROGRESS.md — append §19

> **§19 · Pipeline replaced (2026-10-09).**
> Performance work on the thesis side is closed and frozen (thesis tag `p3-frozen`). The earlier evaluated build
> remains tag `szscan-frozen-v2`, kept for history only. Old `szscan.db` and `*.score.npy` backed up outside
> `web_demo/`, then wiped through the real Delete endpoint. The defense build becomes tag `demo-final-p3`
> with its pre-built 8-subject database (live-upload subject chb16, backup chb03). Obsolete from this point:
> PELT / `cpd_pipeline_v14`, the reconstruction / gamma / graph-mean readouts, 1/3 weights, the 50 / 2.0 / 90
> operating point, `pernode_baseline.npy`, the timing figures 21.9 / 12.3 / 10.83 / 9.76 s/h, tests bound to the
> earlier pipeline, and the `fp_budget_operating_point` / `final_eval` imports. Fill in the outcome of each gate
> G0-G6 here as it is reached.
