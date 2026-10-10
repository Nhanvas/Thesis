# CLAUDE.md — SzScan web demo

Read this before writing any code in `web_demo/`.

**Rev. 2026-10-10 (final system).** The demo is being rebuilt on the final thesis system (git tag
`p3-frozen`). Anything in `web_demo/` that still describes the earlier system (V1: reconstruction +
graph-mean latent + gamma-AEC, equal 1/3 weights, PELT, fixed operating point) is stale until the docs are
updated; this file wins over those.

## What this is

SzScan is the web demo for an undergraduate biomedical-engineering thesis on unsupervised seizure
temporal localization in scalp EEG. It is a **proof-of-concept for a thesis defense**, not a clinical
product. Framing everywhere: **post-hoc EEG review triage**, never real-time alarm.

## Authority order

1. `UI/` — locked PNG mockups. **They win on anything visible.** Do not redesign.
2. `SZSCAN_SPEC_v5.md` — behaviour, logic, data boundaries (parts describing V1 are stale; see below).
3. `SZSCAN_DESIGN_v2.md` — colour/type/spacing tokens (measured from the PNGs, not guessed).
4. `DEMO_BUILD_HANDOFF.md` — stack, folder layout, build order.

For what the pipeline IS (final system), authority is, in this order: `docs/HANDOFF_T1_DEMO_REBUILD.md` §2
and §6 > `docs/DEMO_REBUILD_BRIEF.md` > `web_demo/THESIS_CONTEXT_FOR_DEMO.md` (rev 2026-10-10) >
`docs/PROVENANCE_V2.md` > the frozen code itself (tag `p3-frozen`).
Never quote a number that is not in a committed result file.

Read `SZSCAN_SPEC_v5.md §1` for the reasoning behind the label-free continuous architecture, but treat its
V1 parameters (three readouts, PELT, fixed operating point) as superseded by the handoff above.

## Three hard guards — non-negotiable

The demo is presented as **label-free**: it must never see the ground-truth seizure annotations.

1. **Never import-and-call `szcore_eval.build_timeline_masked()`** or any function that reconstructs a
   timeline from labels.
2. **Never read the seizure fields** (`Seizure Start Time`, `Seizure End Time`, `Number of Seizures`)
   from `chb*-summary.md` at runtime. Reading file names, start/end times and durations **is** allowed.
3. **Never load `{subj}_interictal.npy` or `{subj}_ictal.npy`.** Those arrays were split *using the
   labels*. The demo computes its own continuous, label-free arrays.

Plus a write guard: demo code **must not write** to `results/`, `data/models_retrain/`, `data/models_v2/`,
`data/processed/`, `data/trainset_v2/`, `data/testset_v2/`, or `docs/`. It reads the locked checkpoint and
writes only inside `web_demo/`.

**Thesis functions that read labels — importing their modules is fine, CALLING these from demo code is
forbidden** (they belong to the thesis scoring side): `e22_test_oneshot.test_context` / `.evaluate`,
`e23_test_look7.evaluate`, `p2_scalars.subject_context` / `.score` / `.short_refs` / `.caught`,
`e18_cpd_localizer.match_errors`, `p3_levers.refs_of`, `x1_external.subject_files` / `.chb_subject` /
`.siena_subject` / `.build_subject`, `c1b_build_trainset.build`, anything in `szcore_eval.py`,
`eval_application_events.py`, `t1_demo_gate.py`, `t1_app_tier.py`, `attribution_pipeline.py`.

`backend/tests/test_guards.py` enforces the four source-scan guards and must stay green. If a guard
fires, fix the code — never weaken the test. A runtime test must also prove the label-reading functions
above are never called by the pipeline.

## Model identity

The only checkpoint the demo may load (identified by sha256, never by filename):

```
data/models_v2/gae_v2_clean_seed42.pt     sha256 6e310307b046407a18d839273b84c74b2905457ec6ace892b674c6972dac590f
data/models_v2/gae_v2_clean_seed42.json   sha256 d1e2eee9924b9c23aedf1d8da0e2d289e88d2f790ff90c34958aa850870f06c5
```

Verify both hashes before loading. Never `gae_v2_all_*`, never seeds 1/2/3, never anything under
`data/models_retrain/` or `archive/pre_rebuild_s0/` (V1).

The final system has **one** per-channel quantity: the per-patient LedoitWolf Mahalanobis distance of the
16-d node latent, fused into one ensemble anomaly score (order statistics 6/9/12 + channel mean, drift
correction, patient percentile, equal mean), alarm budget p_i, threshold detector, kernel-CPD localizer.
Exact table: `docs/HANDOFF_T1_DEMO_REBUILD.md` §2. **No** reconstruction/gamma/graph-mean readouts, **no**
1/3 ensemble, **no** PELT, **no** LSTM. Text describing them as current is stale — do not implement it.

## Numbers and parameters

Never hardcode a threshold, budget, k, smoothing, floor/cap or weight from memory or from a doc's prose.
Read them at runtime from `results/p3c_freeze/freeze.json` (point `"balanced"`) and from the checkpoint's
`.json`. If a value cannot be found, stop and ask — do not invent a plausible one.

Do not display any evaluation metric or pipeline parameter in the UI (sensitivity, FP/day, AUROC,
precision, alarm budget, k). Those belong to the thesis.

Timing figures of the earlier system (9.76, 10.83, 21.9, 12.3 s/hour) do **not** apply to the final system.
No timing figure is quoted until `results/t1_demo/TIMING.md` exists.

## Reusing thesis code

Everything in `src/` is **single-source, shared with the thesis: read-only.** Import it; never edit it,
never copy it into `web_demo/`. Defining modules of the final system: `x1_external.py`,
`c1b_build_trainset.py`, `p2_dump_seeds23.py`, `p2_scalars.py`, `e16_recording_baseline.py`,
`e17b_latent_family.py`, `e22_test_oneshot.py`, `p3_levers.py`, `e18_cpd_localizer.py`, `e23_test_look7.py`,
`attribution_v8.py`, plus `dataprep/preprocessing.py`, `dataprep/graph_construction.py`,
`dataprep/feature_extraction.py`, `retrain/gae_joint.py`, `edf_order.py`.
V1-only modules (`ensemble_recipe.py`, `cpd_pipeline_v14.py`, `fp_budget_operating_point.py`,
`latent_anomaly.py`, `retrain_io.py`, `compute_gamma_aec.py`) are no longer part of the demo's path.

New demo logic lives in `web_demo/backend/pipeline_demo.py` (and its worker/export helpers).

## UI

The UI is frozen. The only text change in this rebuild is the Channel Attribution panel title:
`Channel-level latent anomaly — Event N`. The timeline row's score is now a patient percentile in [0, 1]
(not a robust z-score); its zero line may fall outside the box — leave it until the author decides.
No causal or localizing language anywhere ("channel causing", "focus", "origin", "source"); no attribution
metric on screen.

## Working rhythm

Within one task, work autonomously — create files, run tests, fix your own errors. **At the end of each
task, stop** and report with raw output so the author can verify. The author (Boti) is the final
decision-maker on every substantive choice. Propose, then let him decide. He catches path errors and stale
reasoning regularly — treat his corrections as signal, and say plainly when you were wrong.

Freeze procedure: any change that affects pipeline output → guards green → commit `web_demo/` paths only
(explicit paths, never `git add .`) → new tag → back up `szscan.db` and `*.score.npy` → wipe via the real
Delete endpoint → re-run **all 8 subjects**. UI-only changes need no re-run but are tagged separately and
not described as the evaluated build. Last evaluated build of the earlier system: tag `szscan-frozen-v2`.

## Environment

- Windows, Git Bash, Cursor. Repo root `F:/Study/Thesis/Code`, branch `main`.
- Dataset outside the repo: `F:/Study/Thesis/Dataset/CHB-MIT/` — EDFs in `chbNN/`, summaries in
  `CHB info/summary/chbNN-summary.md` (**`.md`, not `.txt`**).
- CPU only, no GPU locally. Phase A runs at most 2 files at once (`_PHASE_A_MAX_CONCURRENCY`); peak memory
  on `chb06` was 10.2 GB in the earlier build — never run another heavy job while the demo processes real
  data. Pagefile and `TMP/TEMP/TMPDIR` on `F:`.
- `rm` in Git Bash does not use the Recycle Bin. `ls`/`du` before any `rm -rf`.
- Admin credentials go in `backend/.env` (gitignored), never in frontend code.
- Bundle fonts locally; the defense machine may have no internet.
- Every new script needs an explicit `sys.path` block; imports across `src/` are flat.

## Subject allowlist

The demo serves exactly these eight held-out test subjects:

```
chb03 chb06 chb13 chb14 chb15 chb16 chb17 chb18
```

Anything else is rejected with `This demo is restricted to the held-out test subjects.` Do not relax this
— serving a training subject would mean demoing on training data.
