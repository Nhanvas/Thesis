# Unsupervised Epileptic Seizure Temporal Localization in Scalp EEG
### using Graph Autoencoder and Change Point Detection

**Student:** Nguyen Quoc Trung Nhan (BEBEIU22184) · **Supervisor:** Hà Thị Thanh Hương (Assoc. Prof.)

**Status:** Phase A + A.5 + B **CLOSED and locked**. Mentor-feedback round (#16–#18), weight change
(#19–#20), weight-consistency pass (#21–#22) **CLOSED**. **Decision #23/#24 (post-hoc CUSUM FP
persistence filter) — TESTED and REJECTED; the detection pipeline is UNCHANGED.** No open
detection-science experiments remain. Active phase = report writing + Phase-C web demo over locked
results. The repo self-reproduces both locked operating points from committed components
(`python src/thesis_repro_lock.py`).

> For current numbers: `docs/RESULTS_OF_RECORD.md`. For current status/next steps:
> `docs/PLAN_AND_STATUS.md`. Full provenance chain: `docs/PROVENANCE_MAP.md`. Per-script map:
> `src/README.md`. If this README ever disagrees with `RESULTS_OF_RECORD.md` on a number, **it wins.**

---

## ⚠️ Read before touching any code

1. **The ensemble weight lives in exactly ONE place: `src/ensemble_recipe.py` (`ENS_WEIGHTS`).**
   Never redefine it inline. Current value: `(0.40, 0.35, 0.25)` (Decision #19).
2. **Never read a persistent ensemble score cache.** The old-weight GPU cache
   (`results/cpd/scores/*_ens_*.npy`) is quarantined to `results/history_superseded/oldweight_ens_scores/`
   — it reproduces the **superseded** 0.35/0.30/0.35 numbers. Always build fresh from per-component
   z-scores via `ensemble_recipe.build_ensemble(...)`.
3. **The detection algorithm lives in exactly ONE place: `src/cpd_pipeline_v14.py`**
   (`detect_changepoints` / `detect_events`). Evaluation and the Phase-C export both call it. Do not
   re-implement PELT logic elsewhere.
4. **Authoritative scorer is `timescoring`.** Before trusting any new harness, confirm it reproduces
   the locked balanced point: **sensitivity 0.750 (57/76), FP/day 39.77** at mag60/pen1.0.
   `python src/thesis_repro_lock.py` does exactly this end-to-end.
5. **Seed `np.random(0)` immediately before every `build_timeline_masked(...)` call** — a past bug
   (§13.2 in `RESULTS_OF_RECORD.md`) came from a shared RNG not being reseeded per-call inside a loop.
6. **Decision #23/#24 (CUSUM FP persistence filter) was TESTED and REJECTED.** It removed FP but at a
   short-seizure cost that breached the pre-registered ≤2-loss bar (discrete cliff at P=34;
   chb06/chb16 first to lose true positives — `RESULTS_OF_RECORD.md` §15). It is **NOT part of the
   pipeline.** `results/phaseB/fp_filter_*` are the rejection record only — never cite them as a
   result or wire the filter into `cpd_pipeline_v14.py`. Duration-adaptive window = future work.
7. **GPU (Kaggle) is not bit-reproducible.** Any GPU re-export will not bit-reconstruct a
   previously-locked ensemble. Use one self-consistent component set per analysis; relative deltas
   (ablations) stay valid across drift, absolute numbers do not.

---

## Two environments

Hard split between **CPU analysis** (this repo — evaluation, statistics, attribution, the CPD
algorithm) and **GPU training/export** (Kaggle notebooks in `notebooks/kaggle_gpu/` that produce the
GAE/LSTM/gamma component scores this repo consumes).

| Environment | Installs from | Used for |
|---|---|---|
| **CPU (local / Cursor)** | `requirements.txt` | Everything in `src/`: PELT detection, SzCORE scoring, statistical validation, attribution, Phase-C backend |
| **GPU (Kaggle)** | `requirements-kaggle.txt` | GAE + LSTM + gamma-AEC inference and per-window component z-score export only (`notebooks/kaggle_gpu/`) |

The CPU side never needs `torch`. If a script in `src/` suddenly needs it, GPU-only code leaked into
the wrong layer — stop and check.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# run everything from the repo ROOT so imports + data/ paths resolve:
python src/thesis_repro_lock.py    # should print: LOCKED HEADLINE REPRODUCES
```

> **Run rule:** always invoke scripts from the repo root as `python src/<name>.py`. The active modules
> live flat in `src/` and import each other by bare name; running from root keeps both the sibling
> imports and the relative `data/` / `results/` paths correct.

---

## Repository layout

```
.
├── src/                         # ACTIVE code (flat; run as `python src/<name>.py` from root)
│   ├── ensemble_recipe.py       #   SINGLE SOURCE: ensemble weight + build_ensemble()
│   ├── cpd_pipeline_v14.py      #   SINGLE SOURCE: detection (PELT + magnitude filter)
│   ├── szcore_eval.py           #   event-tier SzCORE scoring (timescoring)
│   ├── evaluation_protocol.py   #   shared stats + EDF summary parser
│   ├── window_tier_newweight.py #   window tier (new weight)
│   ├── thesis_repro_lock.py     #   reproduces both locked points bit-exact from components
│   ├── stat_validation.py · duration_stratified_sensitivity.py · event_ablation.py
│   ├── mag_pen_grid_sweep_v2.py · rebuild_ensemble_new_weight.py · weight_*.py   # (provenance one-offs)
│   ├── eval_multiseed.py · window_event_gap.py · consolidate_outputs.py · diagnose_fp_mechanism.py
│   ├── attribution_gae_pernode.py · attribution_v3.py · attribution_tpfp.py · attribution_headmap.py
│   ├── visualize_channel_attribution.py · visualize_chb06_inversion.py
│   ├── fig5_eight_subjects.py · fig_A_three_scores.py · fig_B_raw_eeg_pelt.py   # figure scaffolds
│   ├── dataprep/                #   upstream data prep (produces the cached Kaggle inputs)
│   ├── fp_reduction_prior/      #   CUSUM/EMA prior-art (efix, efix_v2) — for the #24 filter, now future work
│   └── README.md                #   per-script map (status: active / provenance / etc.)
│
├── docs/                        # governance + reference (authoritative)
│   ├── RESULTS_OF_RECORD.md     #   ★ locked numbers (§1–§15; §15 = Decision #24 rejected)
│   ├── PLAN_AND_STATUS.md       #   ★ phase, decision log, open items — read first each session
│   ├── PROVENANCE_MAP.md        #   full upstream→locked chain + model provenance
│   ├── Proposed_solution_updated_v5.md   #   methodology master (Ch.2/3 source; DM1–DM6, DM6 = 4C)
│   ├── PHASE_C_PLAN_v2.md       #   demo plan (confidence = continuous magnitude; split-screen)
│   └── PHASE_A_AUDIT_handoff.md · PHASE_B_AUDIT_handoff.md
│
├── notebooks/kaggle_gpu/        # GPU notebooks (thesis-cpd-final = components+pernode; threshold = rejected baseline)
├── demo/                        # Phase-C: wireframe, AI-Studio brief, mock JSON, PRD
├── archive/                     # superseded code (cpd_history, rejected, scaffolding, probes_old, attribution_superseded)
├── data/                        # models/joint model, processed/components/, pernode/, splits/ (small, committed);
│                                #   34 GB graphs are gitignored
├── results/
│   ├── locked/                  #   locked event results (locked_phaseA_event_results.csv)
│   ├── phaseA_appendix/         #   corrected mag×pen grid, duration, weight-round evidence, new_decision19 event CSVs
│   ├── phaseB_newweight/        #   new-weight event ablation
│   ├── attribution/ · attribution_v3/   #   per-node (primary) + preregistered redesign
│   ├── phaseB/fp_filter_*       #   Decision #24 REJECTION RECORD (not adopted)
│   └── history_superseded/      #   old-weight caches, buggy pre-v2 grid, rejected topology — DO NOT cite
│
├── requirements.txt · requirements-kaggle.txt · README.md
```

---

## Locked headline numbers (verify against `docs/RESULTS_OF_RECORD.md` before citing)

- **Ensemble weight:** `(recon, temporal, gamma) = (0.40, 0.35, 0.25)`
- **Balanced (primary):** sensitivity **0.750** [0.642, 0.834], FP/day **39.77** [36.22, 43.57]
- **High-sensitivity:** sensitivity **0.829** [0.729, 0.897], FP/day **71.25** [66.48, 76.28]
- **Window-tier macro AUROC:** **0.791**
- **FP filter (Decision #24):** tested, **REJECTED** — FP/day unchanged, an accepted limitation.
- **Baselines:** Yildiz 2022 unsupervised CHB-MIT scalp AUROC = **0.68** (not 0.76). The 0.765/40.6
  SzCORE Transformer figure is a **TUH** result — never cite it as CHB-MIT.

---

## Where to start in a new session

1. Read `docs/PLAN_AND_STATUS.md` (current phase + next steps).
2. Read `docs/RESULTS_OF_RECORD.md` (numbers) and `src/README.md` (what each script does).
3. For demo work, read `docs/PHASE_C_PLAN_v2.md`.
4. Do not re-run or re-derive locked results unless asked — everything is post-hoc on cached
   components (CPU-only); no retraining is needed for evaluation/analysis.
