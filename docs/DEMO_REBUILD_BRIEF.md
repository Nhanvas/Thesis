# DEMO_REBUILD_BRIEF — SzScan on the final thesis system (2026-10-08)

From the thesis project to Project 2 (carried by Boti, per `PROJECT2_SETUP.md` 9.2 B: the thesis changed
something the demo depends on — the pipeline). Project 2 owns `web_demo/*` and decides how to build; this
brief only says WHAT the pipeline is, with the code that defines it. Nothing here is a performance number
for the UI: the product still shows no evaluation metric.

**Before starting:** commit the 5 modified `web_demo/*` files currently uncommitted in the repo
(`BUILD_PROGRESS.md`, `CLAUDE.md`, `DEMO_BUILD_HANDOFF.md`, `SZSCAN_SPEC_v5.md`, `THESIS_CONTEXT_FOR_DEMO.md`)
so the rebuild starts from a clean, tagged state (`szscan-frozen-v2` is the last demo tag).

## 1 · What changes

| stage | earlier demo (V1) | final system (tag `p3-frozen`) | defining code (read-only, `src/`) |
|---|---|---|---|
| model | `data/models_retrain/gae_joint_seed42.pt` (3,285 params, node input 23) | `data/models_v2/gae_v2_clean_seed42.pt` (3,964 params, node input 30); sha256 in `docs/PROVENANCE_V2.md` | `retrain/train_gae_v2.py`, `gae_joint.py` (v2 layer sizes) |
| node features | adjacency row 18 + band powers 5 | + 7: log band power ×5, log line length, signed-log kurtosis; normalised with the training-set constants, clip ±4 → [0, 1] | `c1b_build_trainset.f7`, `train_gae_v2.norm_constants` |
| readouts | recon + graph-mean latent + gamma-AEC, robust-z, equal weights | **none of those.** Per channel: LedoitWolf Mahalanobis distance of the 16-d node latent, fitted on all non-signal-loss windows of the subject | `p2_scalars`, `e16_recording_baseline` (`s_from_d`, `rz`) |
| score | 1/3 · (zrecon + zlatent + zgamma) | per-channel robust-z → order statistics 6, 9, 12 of 18 and the mean → each minus its centred running median over 451 windows (±15 min) inside each file → percentile within the subject → equal mean | `e17b_latent_family` (`member`, `MEMBERS`), `p2_scalars.pct`, `detrend_file` |
| detector | PELT (`cpd_pipeline_v14`) + FP-budget operating point | threshold detector: per-file centred moving average of 5 windows (signal-loss = NaN, min_periods 1); threshold = (1 − p_i) quantile of the smoothed values; contiguous runs; merge gaps ≤ 90 s | `p2_scalars.d1_events` |
| alarm budget | fixed operating point | **p_i = clip(q_i, 0.005, 0.02)**, q_i = share of the smoothed (5 windows) mean of the four members' robust-z above **k = 4.0677** (constant, from `results/p3c_freeze/freeze.json`) | `p3_levers.member_mean_z`, `q_of`; `p3c_freeze.budget` |
| boundaries | PELT segments | kernel CPD localizer per event: ruptures KernelCPD (rbf, min_size 2), exactly 2 change points on the unsmoothed score over the event ± 15 windows inside the file; accepted if the inner segment has ≥ 2 windows and a mean above both outer segments, else the detector's boundaries; events merged again (90 s) | `e18_cpd_localizer.cpd_event`, `p3_levers.localize(mode="cpd")` |
| channel panel | `Channel-level reconstruction anomaly — Event N` | `Channel-level latent anomaly — Event N`: per channel, p95 over the event's windows of the absolute per-channel robust-z (the quantity of the final system's attribution study) | `attribution_v8.py` (score definition) |

Reference implementation of the whole chain on a recording never seen by the thesis: `src/x1_external.py`
(it reproduced look #7 on chb03 within 3e-6 for 4 seeds). It is the closest template for a label-free,
upload-a-patient pipeline: it builds features with label-free z-score statistics and calls the frozen
evaluation code path.

## 2 · Constraints that do not change

- The three hard guards (`test_guards.py`): no label-based timeline builder, no seizure fields of the
  summaries at runtime, no `{subj}_interictal/_ictal.npy`. The attribution labels are off-limits.
- No evaluation metric in the product. Only the 8 test subjects. Frozen UI; only the panel title text
  changes (see the table).
- The approved divergence holds and widens: every statistic the system fits per subject (z-score, the 18
  per-channel LedoitWolf fits, robust-z, percentiles, q_i) is fitted on all windows of the uploaded
  subject, label-free. Note for the report: the thesis's CHB-MIT runs used z-score statistics that exclude
  annotated seizure and buffer windows (`stats.json`); the demo must not, so its numbers will differ.
- **Non-causal by design:** the ±15-min median and the patient-level fits need the whole recording of the
  subject before any event is final. The upload flow processes a subject's files, then scores; no
  streaming alarm. This matches the post-hoc review framing.

## 3 · To measure and report back (Project 2 → thesis project, via Boti)

1. Processing time per hour of EEG on the laptop CPU, end to end, median of 5 runs on one subject
   (the earlier 10.83 s/h belongs to the earlier system and is not reused).
2. Identity check: for one test subject, the demo's per-window score and its events must reproduce the
   thesis code path (`x1_external.py` / `e23_test_look7.evaluate`) when fed the same statistics; then the
   label-free statistics are switched on. Report the max absolute difference.
3. Application tier (instructions §11.5): frozen build (commit + tag), clean database with the 8 test
   subjects, every AI event exported before review, scored outside the demo with the same scorer; FA
   denominator = recorded time of the processed files minus seizure time. Any defect ⇒ the whole run is
   repeated. Return: per subject tp, n_ref, fp, hours; pooled and subject-mean sensitivity, FP/day,
   precision, F1 from the scorer's counts.
