# CLAUDE.md — SzScan web demo

Read this before writing any code in `web_demo/`. Rev. 2026-10-09 (task T1: pipeline rebuilt on the final
thesis system).

## What this is

SzScan is the web demo for an undergraduate biomedical-engineering thesis on unsupervised seizure temporal
localization in scalp EEG. A **proof-of-concept for a thesis defense**, not a clinical product. Framing
everywhere: **post-hoc EEG review triage**, never a real-time alarm.

## Authority order

1. `UI/` — locked PNG mockups win on anything visible. Do not redesign.
2. `SZSCAN_SPEC_v5.md` (including amendment C29) — behaviour, logic, data boundaries.
3. `SZSCAN_DESIGN_v2.md` — tokens.
4. `DEMO_BUILD_HANDOFF.md` — stack, layout.

For **what the pipeline computes**: the thesis code in `src/` (read-only) > `docs/DEMO_REBUILD_BRIEF.md` >
`THESIS_CONTEXT_FOR_DEMO.md`. If the brief and the code disagree, stop and report; do not pick silently.
Task spec and return format: `HANDOFF_T1_DEMO_REBUILD.md`.

## Three hard guards — non-negotiable

The demo is presented as **label-free**:
1. Never import or call `szcore_eval.build_timeline_masked()` or any function that rebuilds a timeline from labels.
2. Never read the seizure fields (`Seizure Start Time`, `Seizure End Time`, `Number of Seizures`) of
   `chb*-summary.md` at runtime. File names, start/end times, durations are allowed.
3. Never load `{subj}_interictal.npy` or `{subj}_ictal.npy`.

Write guard: never write to `results/`, `data/`, `docs/`; only inside `web_demo/`.
`backend/tests/test_guards.py` enforces all four. If a guard fires, fix the code — never weaken the test.

**T1 extension.** You may *import* thesis functions, but never call one that reads annotation-derived data
(annotation files, `stats.json` computed excluding seizures, `trainset_v2`/`testset_v2` arrays, attribution
labels). If a needed function does, stop and ask. Never replay stored thesis scores — compute from the raw EDF.

## Model identity

Only checkpoint the demo may load: `data/models_v2/gae_v2_clean_seed42.pt`, verified by **sha256** (value in
`THESIS_CONTEXT_FOR_DEMO.md` §3; refuse to start on mismatch — keep `_verify_checkpoint`), together with the
training constants saved beside it. Never `data/models_retrain/gae_joint_seed42.pt` (earlier system), never
`archive/`, never other seeds or the `all` variants.

The final system has **no** reconstruction readout, **no** gamma-AEC, **no** graph-mean latent, **no**
PELT, **no** LSTM, **no** per-subject operating-point calibration. Delete the corresponding imports and
code paths; if you find docs describing them as live, they are stale.

## Numbers and parameters

Never hardcode a threshold, budget, smoothing length, k or merge gap from memory or prose. Read them at
runtime from `results/p3c_freeze/freeze.json` and from the thesis modules. If a value cannot be found, stop
and ask. Do not display any evaluation metric in the UI.

## Reusing thesis code

Read-only, single-source, shared with the thesis — import, never edit, never copy into `web_demo/`:
`src/retrain/train_gae_v2.py`, `src/c1b_build_trainset.py`, `src/p2_scalars.py`,
`src/e16_recording_baseline.py`, `src/e17b_latent_family.py`, `src/e18_cpd_localizer.py`,
`src/p3_levers.py`, `src/p3c_freeze.py`, `src/e23_test_look7.py`, `src/x1_external.py` (template),
`src/attribution_v8.py`, `src/dataprep/*`, `src/edf_order.py`, and `src/final_system.py` if Project #1
provides it. If a module cannot be imported without side effects, do not copy it: report to Boti, who asks
Project #1 for an importable wrapper.

New demo logic lives in `web_demo/backend/pipeline_demo.py`.

## Working rhythm for T1

Autonomous inside a gate; **stop at the end of each gate** (G0 clean start → G1 pipeline + identity gate on
chb03 → G2 guards + tests → G3 freeze/tag → G4 8-subject run + CSV export before review → G5/G6 are
Boti's). Report raw numbers, never summaries only. Identity gate: report max |Δ| of the per-window score
and the event-list diff between the demo chain and the thesis code path (same statistics first, then
label-free statistics). Tests tied to the old pipeline (bit-identical-to-v2, `detect_events` constants) are
rewritten or retired — never left failing. Boti is the final decision-maker; propose, then let him decide;
say plainly when you were wrong.

## Application run rules

Freeze (commit `web_demo/` paths only, new tag) → empty DB via the real Delete endpoint → upload every file
of the 8 subjects → export every AI event (subject, file, start s, end s) to CSV **before** any review →
Boti scores it outside the demo. The demo never reads annotations and never scores itself. Any defect ⇒ fix,
re-tag, repeat the whole run.

## Environment

- Windows, Git Bash, Cursor. Repo `F:/Study/Thesis/Code`, branch `main`.
- Dataset: `F:/Study/Thesis/Dataset/CHB-MIT/` — EDFs in `chbNN/`, summaries `CHB info/summary/chbNN-summary.md`
  (**`.md`, not `.txt`**).
- CPU only. Pagefile and `TMP/TEMP/TMPDIR` on `F:` (`F:/tmp`); Phase A concurrency 2
  (`_PHASE_A_MAX_CONCURRENCY`); chb06 needs ~10 GB — run nothing else heavy.
- Earlier timing figures (21.9, 12.3, 10.83, 9.76 s/h) belong to the earlier system. New timing is measured
  (M3: median of ≥ 3 runs, hardware named); never quote an unmeasured figure.
- `rm` in Git Bash skips the Recycle Bin: `ls`/`du` before `rm -rf`. Credentials in `backend/.env` only.
- Fonts bundled locally; the demo must run with the network off.

## Subject allowlist

`chb03 chb06 chb13 chb14 chb15 chb16 chb17 chb18` — anything else is rejected with
`This demo is restricted to the held-out test subjects.`
