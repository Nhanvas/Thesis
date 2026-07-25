# PROVENANCE MAP — Unsupervised Seizure Localization (GAE + CPD)

**Purpose.** One page that lets a second researcher (or a reviewer, or you in a year)
trace every locked number back to the exact file that produced it, and tells them
which artifacts are authoritative vs. superseded. Companion to `RESULTS_OF_RECORD.md`
(numbers) and `PLAN_AND_STATUS.md` (status). When this file and `RESULTS_OF_RECORD.md`
disagree on a NUMBER, `RESULTS_OF_RECORD.md` wins.

Last updated: 2026-07-25. Verified by end-to-end reproduction on the author's machine
(`thesis_repro_lock.py`): both locked operating points reproduce **bit-exact**
(per-subject TP/FP and pooled) from `data/processed/components/` via the Decision #19
weight — no ensemble cache read. See "Reproduction" below.

---

## 1. Locked headline (cite these)

| Operating point | mag/pen | Sensitivity | FP/day | TP/FN/FP |
|---|---|---|---|---|
| Balanced (primary) | mag60 / pen1.0 | 0.750 [0.642, 0.834] | 39.77 [36.22, 43.57] | 57/19/461 |
| High-sensitivity | mag50 / pen0.5 | 0.829 [0.729, 0.897] | 71.25 [66.48, 76.28] | 63/13/826 |

Window/sample tier: macro AUROC 0.791; component standalone AUROC recon 0.671,
temporal 0.647, gamma 0.755 (weight-independent). Ensemble weight (Decision #19):
`(recon, temporal, gamma) = (0.40, 0.35, 0.25)`.

---

## 2. The pipeline chain (upstream → locked number)

```
KAGGLE (GPU, cached datasets — nhn2mm/*)
  preprocessing            -> chbmit-processed        (band-power features, 18ch x 5band)
  graph wPLI+AEC, top-k20% -> chbmit-topk20           (per-window adjacency)
  GAE training [*]         -> gae-joint-model/best_model_joint_lambda01.pt
  LSTM training [*]        -> temporal-zscores         (temporal_{subj}_z{inter,ictal}.npy)
  gamma AEC [*]            -> gamma-aec-scores          (gamma_aec_{subj}_{inter,ictal}.npy)

thesis-cpd-final.ipynb  (GPU inference; notebooks/kaggle_gpu/)
  Sec 2 + cell 8   GAE recon scoring + PER-NODE dump
                   -> pernode/{subj}_{split}_pernode.npy   ==> local data/pernode/   [AUTHORITATIVE, weight-independent]
  Sec 3/4          load temporal + gamma (from cached datasets)
  Sec 5A           robust z-norm (median/MAD, all-window pooled) per view
  cell 16          export per-view z-scores
                   -> components/{zrecon,ztemp,zgamma}_{subj}_{split}.npy
                                                           ==> local data/processed/components/  [AUTHORITATIVE, weight-independent]
  Sec 5B/5C/5D     3-way ensemble with OLD weight (0.35/0.30/0.35) + ens cache + auroc_verification.csv
                                                           ==> SUPERSEDED  [see warning below]

LOCAL (CPU, Cursor repo)
  ensemble_recipe.build_ensemble   weight (0.40,0.35,0.25), Decision #19/#21
                                   builds ensemble FRESH from components (never a cache)
  cpd_pipeline_v14.detect_events   single-source detection (seed-indep PELT + magnitude filter)
  szcore_eval.py + timescoring     SzCORE event scoring
                                   ==> locked numbers (Section 1)
```

`[*]` = upstream generating code NOT yet in this repo (see "Gaps").

---

## 3. Authoritative artifacts — cite ONLY these

**Numbers**
- Pooled event: `results/locked/locked_phaseA_event_results.csv`
- Per-subject event: `szcore_event_level_new_decision19_mag{60,50}.csv` (in `results/phaseA_appendix/`)
- Grid / Pareto: `mag_pen_grid_v2_{pooled,persubject}.csv`
- Window tier (new weight): `eval_window_level_newweight.csv`, `eval_stat_tests_newweight.csv`,
  `window_component_auroc_newweight.csv`
- Event ablation (new weight): `results/phaseB_newweight/event_ablation_*`
- Duration: `results/phaseA_appendix/duration_*`
- Robustness: `weight_seed_robustness_*`, `weight_sensitivity_grid`, `results/cpd/evaluation/multiseed/*`
- Attribution: **pending §7 decision** — `results/attribution/attribution_pernode_*` (original) vs.
  `results/attribution_v3/*` (preregistered redesign, ATTRIBUTION_PREREGISTRATION_v3_1). Same signal
  (`data/pernode/`); v3 is the stronger, supervisor-aligned analysis. Confirm which is thesis §7 primary.

**Code (single sources of truth)**
- `ensemble_recipe.py` — the ONE ensemble weight + build-from-components
- `cpd_pipeline_v14.py` — the ONE detection algorithm
- `szcore_eval.py` / `evaluation_protocol.py` — event scoring + shared parsing
- `window_tier_newweight.py` — current window tier
- `mag_pen_grid_sweep_v2.py` — seeding-bug-fixed grid (produced the locked new_decision19 rows)

**Inputs (weight-independent, verified)**
- `data/processed/components/` — per-view z-scores (from cell 16)
- `data/pernode/` — per-node recon error (from cell 8)

---

## 4. Superseded / DO NOT cite

- **OLD-WEIGHT CACHE ORIGIN:** `thesis-cpd-final.ipynb` Sec 5B/5D produce the old-weight (0.35/0.30/0.35)
  ensemble + `ens_*.npy` cache. Local copy quarantined at
  `results/history_superseded/oldweight_ens_scores/`. **Never read the ens cache; never treat
  the notebook's Sec 5 ensemble/AUROC as current.** Only cell 8 (pernode) and cell 16 (components)
  from that notebook feed the current pipeline.
- `results/locked/{eval_window_level,eval_stat_tests,szcore_event_level_mag60/70,auroc_verification}.csv`
  — old-weight files sitting inside a folder named "locked" (misleading). Only
  `locked_phaseA_event_results.csv` in that folder is current.
- Event CSVs `*_newweight_*` (duplicate of new_decision19), `*_old_locked_*`, plain
  `szcore_event_level_mag60/70` — superseded generations.
- `results/{ablation,phaseB}/event_ablation_*` (old weight; use `phaseB_newweight`).
- `mag_pen_grid_v2_reproducibility_check.csv` — documents the OLD seeding bug (old-weight rows);
  NOT a statement about current numbers. Confirmed harmless; regenerate as new-vs-new if kept.
- Pre-`_v2` grid (`mag_pen_grid_{pooled,persubject}.csv`) — seeding bug.
- `cpd_pipeline_v2..v13`, `cpd_results_v*`, `cpd_tolerance_sweep`, `window_metrics` — old lineage.
- Topology (`topo_*`, `history_topology/*`) — rejected A.5 extension.
- **Baselines:** Yildiz unsupervised CHB-MIT AUROC = 0.68 (not 0.76). Transformer 0.765/40.6 is TUH,
  NOT a CHB-MIT baseline.

---

## 5. Gaps (upstream code not yet in repo)

For full reproducibility + the Methods chapter, these generating steps are still external:
- **GAE training** (produced `best_model_joint_lambda01.pt`). Architecture is documented in
  `thesis-cpd-final.ipynb` Sec 1 (GCNConv 23→64→16, X-decoder MLP 16→32→5, score = MSE(A) + 0.1·MSE(X),
  seed 42), but the training procedure (epochs/optimizer/loss/early-stop) needs the training notebook.
- **LSTM training** (produced `temporal-zscores`).
- **gamma AEC** — likely `src/compute_gamma_aec.py` (local); confirm it is the version that produced
  `gamma-aec-scores`.
- **graph construction** — likely `src/graph_construction.py` / `src/build_graphs.py` (local); confirm.

---

## 6. Reproduction

**Locked numbers from components (CPU, no GPU, no cache):**
`python thesis_repro_lock.py` — builds ensemble from `data/processed/components/` via
`ensemble_recipe` (weight 0.40/0.35/0.25), scores mag60/pen1.0 and mag50/pen0.5 with the same
functions the lock used, seeds `np.random.seed(0)` per subject. Verified bit-exact 2026-07-25.

**Components from Kaggle (GPU):** run `notebooks/kaggle_gpu/thesis-cpd-final.ipynb` on Kaggle with
the nhn2mm/* datasets mounted; use only cell 8 (pernode) + cell 16 (components) as handoff outputs.
Do NOT propagate Sec 5B/5D ensemble/cache.
