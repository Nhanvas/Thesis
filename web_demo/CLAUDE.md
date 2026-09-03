# CLAUDE.md — SzScan web demo

Read this before writing any code in `web_demo/`.

## What this is

SzScan is the web demo for an undergraduate biomedical-engineering thesis on unsupervised seizure
temporal localization in scalp EEG. It is a **proof-of-concept for a thesis defense**, not a clinical
product. Framing everywhere: **post-hoc EEG review triage**, never real-time alarm.

## Authority order

1. `UI/` — locked PNG mockups. **They win on anything visible.** Do not redesign.
2. `SZSCAN_SPEC_v5.md` — behaviour, logic, data boundaries.
3. `SZSCAN_DESIGN_v2.md` — colour/type/spacing tokens (measured from the PNGs, not guessed).
4. `DEMO_BUILD_HANDOFF.md` — stack, folder layout, build order.

For anything scientific (not demo), authority is `docs/RESULTS_OF_RECORD_phaseB.md` >
`docs/PROVENANCE.md` > `docs/REPO_MAP.md`. Never quote a number that is not in one of those files.

Read `SZSCAN_SPEC_v5.md §1` in full before touching the backend. It explains why the thesis's saved
score arrays cannot be replayed on a real time axis, and what the demo does instead.

## Three hard guards — non-negotiable

The demo is presented as **label-free**: it must never see the ground-truth seizure annotations.

1. **Never import or call `szcore_eval.build_timeline_masked()`** or any function that reconstructs a
   timeline from labels.
2. **Never read the seizure fields** (`Seizure Start Time`, `Seizure End Time`, `Number of Seizures`)
   from `chb*-summary.md` at runtime. Reading file names, start/end times and durations from those
   summaries **is** allowed.
3. **Never load `{subj}_interictal.npy` or `{subj}_ictal.npy`.** Those two arrays were split *using the
   labels*. The demo computes its own continuous, label-free arrays.

Plus a write guard: demo code **must not write** to `results/`, `data/models_retrain/`, `data/processed/`,
or `docs/`. It reads the locked checkpoint and writes only inside `web_demo/`.

`backend/tests/test_guards.py` enforces all four by scanning the demo source tree. It must stay green.
If a guard fires, fix the code — never weaken the test.

## Model identity

The only checkpoint the demo may load:

```
data/models_retrain/gae_joint_seed42.pt
sha256 dea06cb533df1c7d0520ae21c4cbb1b8a938297f937366bc9915b040726ea108
```

Never `gae_multirel_seed42.pt` (a killed Phase-C experiment) and never anything under
`archive/pre_rebuild_s0/`. Identify checkpoints by hash, never by filename.

The final pipeline has **three** readouts: `zrecon`, `zlatent`, `zgamma`, combined at equal 1/3 weights.
There is **no LSTM / temporal branch** — it was dropped. If you find code or docs describing one, that
text is stale; do not implement it.

## Numbers and parameters

Never hardcode a threshold, penalty, weight or operating point from memory or from a doc's prose.
Read it from the source file at build time (`src/cpd_pipeline_v14.py`,
`src/retrain/fp_budget_operating_point.py`, `src/ensemble_recipe.py`). If a value cannot be found, stop
and ask — do not invent a plausible one.

Do not display any evaluation metric in the UI (sensitivity, FP/day, AUROC, precision, operating-point
parameters). Those belong to the thesis, not to the product.

## Reusing thesis code

`src/cpd_pipeline_v14.py`, `src/ensemble_recipe.py`, `src/szcore_eval.py`, `src/edf_index.py`,
`src/edf_order.py`, `src/retrain/gae_joint.py` are **single-source, shared with the thesis: read-only**.
Import them; never edit them, never copy them into `web_demo/`.

New demo logic lives in `web_demo/backend/pipeline_demo.py`.

## Working rhythm

Follow the build order in `DEMO_BUILD_HANDOFF.md §6`. Within one step, work autonomously — create files,
run the server, fix your own errors. **At the end of each step, stop** so the author can compare the real
app against the mockup in `UI/` before moving on.

The author (Boti) is the final decision-maker on every substantive choice. Propose, then let him decide.
He catches path errors and stale reasoning regularly — treat his corrections as signal, and say plainly
when you were wrong.

## Environment

- Windows, Git Bash, Cursor. Repo root `F:/Study/Thesis/Code`, branch `main`.
- Dataset outside the repo: `F:/Study/Thesis/Dataset/CHB-MIT/` — EDFs in `chbNN/`, summaries in
  `CHB info/summary/chbNN-summary.md` (**`.md`, not `.txt`**).
- CPU only, no GPU locally. Measured cost: ~16.9 ms per 4 s window ⇒ ~15 s per hour of EEG.
- `rm` in Git Bash does not use the Recycle Bin. `ls`/`du` before any `rm -rf`.
- Admin credentials go in `backend/.env` (gitignored), never in frontend code.
- Bundle fonts locally; the defense machine may have no internet.

## Subject allowlist

The demo serves exactly these eight held-out test subjects:

```
chb03 chb06 chb13 chb14 chb15 chb16 chb17 chb18
```

Anything else is rejected with `This demo is restricted to the held-out test subjects.` Do not relax this
— serving a training subject would mean demoing on training data.
