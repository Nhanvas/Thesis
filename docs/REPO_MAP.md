# REPO_MAP — repository structure, post-cleanup 2026-09-02

> **Before quoting any number or loading any checkpoint, run the session gate:**
> ```bash
> python src/verify_provenance.py      # ~20 s, must print "VERDICT: PASS"
> ```
> It re-derives the canonical GAE checkpoint identity by measurement, against the committed one-shot
> TEST components. Filenames are **not** identity evidence — see §7 Traps.

**Authority order on conflict:**
`docs/RESULTS_OF_RECORD_phaseB.md` (numbers) > `docs/PROVENANCE.md` (artifact identity) >
this file (paths) > project instructions > memory.

**Repo:** `F:/Study/Thesis/Code` · github.com/Nhanvas/Thesis · branch `main`
**Tags:** `pre-cleanup` (safety snapshot) · `phase-c-final` (locked rlg thesis, restore point)

---

## 1 · Top level

```
Code/
├── src/          code — 6 canonical modules + 6 role-scoped folders
├── docs/         governance and specifications (the only citable docs)
├── data/         inputs, checkpoints, per-node dumps  (processed/ ~30 GB, gitignored)
├── results/      all committed outputs
├── archive/      superseded code and artifacts — DO NOT CITE, DO NOT RUN
├── figures/      rendered report figures
├── notebooks/    Kaggle GPU notebooks
├── logs/         preprocessing run logs (2026-04)
├── _project_audit/   local audit tooling (untracked, not part of the pipeline)
├── venv/         gitignored
├── README.md · requirements.txt · pip_freeze.txt · .gitignore
```

---

## 2 · `src/` — code

### 2.1 Canonical modules (top level; do NOT move — `sys.path` blocks across the repo point here)

| file | purpose |
|---|---|
| `cpd_pipeline_v14.py` | **LOCKED** production CPD algorithm. Single source of truth for change-point detection. `detect_events()` is the entry point. |
| `ensemble_recipe.py` | **SINGLE SOURCE** for the ensemble anomaly score. `build_ensemble_subset()` + `CANDIDATES`. Equal weights 1/3 each (PREREG_03). |
| `szcore_eval.py` | SzCORE-exact event scoring via `timescoring`. `build_timeline_masked()`. |
| `verify_provenance.py` | **Session gate.** Machine-verified checkpoint identity; `--full` regenerates `docs/PROVENANCE.md`. |
| `attribution_pipeline.py` | **SINGLE SOURCE** for channel attribution. Sub-commands: `dump · blocks · labels · score · diag · synth · spread · eval · labeldiv · all`. Replaced nine separate scripts on 2026-09-02 (outputs verified byte-identical). |
| `README.md` | legacy `src` notes (2026-07). |

### 2.2 `src/dataprep/` — preprocessing → graphs → features (11 files)

| file | purpose |
|---|---|
| `preprocessing.py` | CHB-MIT pipeline: bandpass 0.5–60 Hz → 60 Hz notch → per-subject z-score → 4 s non-overlapping windows. Also the source of `parse_summary` / `open_edf` / `build_labels` / `FS` / `WIN_S` / `WIN_SAMPLES`, reused by `attribution_pipeline blocks`. |
| `graph_construction.py` | wPLI + AEC per 4 s window; CAR before connectivity. Thesis §2.2 equations. |
| `build_graphs.py` | Batch driver for `graph_construction` over all subjects. |
| `build_topk_from_dense.py` | Post-hoc top-k% sparsification of dense adjacencies. |
| `feature_extraction.py` | 5 spectral band powers per channel → `[N, 18, 5]`. |
| `compute_gamma_aec.py` | Gamma-band (30–60 Hz) AEC anomaly score — the `zgamma` branch input. |
| `build_te_adj.py` | Transfer-Entropy directed adjacency (Phase-C C4-full R2 relation). **Phase-C negative.** |
| `apply_topk_multiband.py` | top-k for multiband adjacencies (Phase-C). |
| `verify_preprocessing.py` | Output sanity check across all 23 subjects. |
| `plot_raw_vs_preprocessed.py` | Report figure: raw vs preprocessed segment. |
| `create_splits.py` | ⚠️ **TRAP — see §7.1.** Generates the old **E_main 15/8** split, NOT the locked 12/3/8 split. |

### 2.3 `src/retrain/` — Phase-B rebuild (18 files)

| file | purpose |
|---|---|
| `gae_joint.py` | **Joint-GAE model class + verified scoring.** `GAEModel`, `load_checkpoint`, `score_windows(per_node=…)`. Everything downstream imports this. |
| `train_gae_joint.py` | Reconstructed training loop (PREREG_01 recipe). |
| `retrain_io.py` | Shared helpers: `robust_z`, `window_auroc`. |
| `derive_weights.py` | PREREG_03 §2 — ensemble weights derived on non-TEST data. |
| `build_ens.py` | Kaggle GPU: build per-subject ensemble arrays. |
| `build_seed_ensemble.py` | CPU: average per-seed ensembles (variance reduction). |
| `score_ens.py` | CPU: mag × pen grid scoring (the slow half). |
| `final_eval.py` | PREREG_03 §3–4 — the one end-to-end TEST evaluation. |
| `eval_local.py` | Local full-grid run with full logging. |
| `aggregate_final.py` | Per-seed grids → Pareto frontier + operating points + CIs. |
| `fp_budget_operating_point.py` | **PREREG_04** label-free per-subject FP-budget operating point. |
| `gae_gate_report.py` | Gate R-GAE acceptance for each retrained checkpoint. |
| `window_event_gap_new.py` | Window↔event gap diagnostic. |
| `lstm_temporal.py` · `train_lstm_temporal.py` · `train_lstm_temporal_v3.py` · `lstm_gate_full.py` · `lstm_forensic.py` | ⚠️ **TRAP — see §7.2.** The temporal branch, **DROPPED** by PREREG_TIER2 Amendment A1. Kept as provenance of that decision. **DO NOT USE.** |

### 2.4 `src/phaseB/` — Tier-2 latent branch and the one-shot TEST (9 + archive 3)

| file | purpose |
|---|---|
| `latent_anomaly.py` | **E2** — latent-Mahalanobis readout (`latent_pool`). The branch that replaced LSTM. |
| `build_ens_tier2.py` | Kaggle GPU — builds robust-z components including `zlatent`. |
| `dump_val_components.py` | Kaggle GPU — per-branch VAL components. |
| `branch_ablation.py` | **E1** — scores every equal-weight branch subset. |
| `val_gate.py` | VAL-only representation gate for any GAE upgrade. |
| `g2_val_gate.py` | VAL guardrail G2 + VAL operating-point cells. **The VAL-gate pattern to reuse.** |
| `tier2_oneshot_compare.py` | **THE one-shot TEST comparison** (Amendment A1). VAL-derived cell, applied once. |
| `tier2_final_report.py` | Full reporting suite from frozen Tier-2 artifacts. No new TEST exposure. |
| `per_subject_op_check.py` | Per-subject label-free FP budget on rlg. |
| `archive/gae_joint_gsl.py` · `train_gae_gsl.py` · `train_gae_compact.py` | S2 (learned graph structure) and S3 (Deep-SVDD) — **negatives**, settled, do not re-propose. |

### 2.5 `src/phaseC/` — Phase-C levers, all negative (19 files)

Directed connectivity (`connectivity_probe`, `build_te_branch`, `build_te_adj`, `gae_joint_multirel`,
`train_gae_multirel`, `encode_multirel_val`, `stage0_lg_variant`, `rlg_lg_diagnostic`),
CPD smoothing (`run_c1_grid`, `c1_lowfp_compare`), onset slope-gate (`c_onset_probe`,
`run_slopegate_grid`, `seed_check_slopegate`), artifact gate (`artifact_fp_diagnostic`,
`artifact_gate`, `compare_gate`), alignment checks (`align_check`, `align_check2`),
plus `check_ckpts.py` and `place_seeds.py`.
**Phase C is CLOSED (RoR §9). Do not re-run as optimization; cite as documented negatives.**

### 2.6 `src/figures/` (6) and `src/labeling/` (1)

`fig5_eight_subjects.py` (8-subject detection overview) · `fig_B_raw_eeg_pelt.py` (preprocessed EEG with
PELT change points) · `plot_event_level.py` (E1/E2 event-level figures) ·
`visualize_channel_attribution.py` · `visualize_chb06_inversion.py` · `attribution_headmap.py`
(display-only per-channel heat map).
`labeling/label_eeg_pilot.py` — blind channel-labelling EEG viewer; renders the `*_onset.png` images
the reading pass scored. Run this if the supervisor asks for a new labelling round.

> `fig_A_three_scores.py` was **deleted 2026-09-02**: it plotted `z_recon / z_temporal / z_gamma`, and
> `z_temporal` no longer exists. Recover with `git show phase-c-final:src/fig_A_three_scores.py` and
> retarget to `zrecon/zlatent/zgamma` if that figure is wanted.

---

## 3 · `docs/` — the only citable documentation

| file | role |
|---|---|
| `RESULTS_OF_RECORD_phaseB.md` | **ALL NUMBERS.** §1–§6 locked TEST results · §7 seed stability + errata · §8–§9 Phase-C negatives · §10 attribution summary. |
| `PROVENANCE.md` | **MACHINE-GENERATED.** Checkpoint identity, SHA-256, verification result. Regenerate, never hand-edit. |
| `REPO_MAP.md` | this file — paths and purposes. |
| `PROJECT_STATUS.md` | status, deadlines, remaining work. |
| `RUBRIC_TRACKING.md` | v3 report checklist, 8 criteria / 100 pts. |
| `ATTRIBUTION_SPEC.md` | v3 — the complete attribution study: problem, method, labels, metrics, results, amendments. |
| `PHASE_C_FINAL_HANDOFF.md` · `PHASE_C_CLOSEOUT_provenance.md` · `PHASE_C_FULL_AUDIT.md` | Phase-C closure record. |
| `PHASE_D_HANDOFF.md` | Future Work design (deliberately not executed). Defense material. |
| `Thesis_Reference_Sheet.md` | citations for report writing. |
| `PROPOSED_SOLUTION.md` | original method proposal. |
| `PREREG_TIER2_amendment_A1.md` | **the LSTM-drop decision.** |
| `PREREG_TIER2_latent_ensemble.md` · `PREREG_C0_connectivity_probe.md` | Tier-2 / Phase-C pre-registrations. |
| `prereg/PREREG_01…09` | 01 GAE retrain · 02 LSTM (superseded by A1) · 03 weights · 04 FP-budget OP · 05 OP T1 · 06 balanced OP · 07 per-subject FP · 08 window threshold · 09 min event duration. |
| `demo/WEB_DEMO_SPEC_v4.md` | **WINS on any demo conflict.** |
| `demo/WEB_DEMO_CONTEXT_BOUNDARY.md` · `WEB_DEMO_DESIGN_SYSTEM.md` · `WEB_DEMO_CODE_MIGRATION_NOTES.md` · `demo/edf_order.py` | demo supporting material; `edf_order.py` orders EDFs by header time for the backend. |
| `demo/THESIS_REPORT_WRITING_GUIDE.md` | governs report writing. |
| `archive/` (21 files) | ⚠️ **DO NOT CITE — see §7.3.** Contains superseded handoffs, the old `RESULTS_OF_RECORD.md`, `TIEU_CHI_LABEL_dominant_channel_v2.md` (retired label criteria), `WEB_DEMO_SPEC.md` (superseded by v4), and the `Spatial_Localization…md` field survey. |

---

## 4 · `data/`

| path | content |
|---|---|
| `processed/` | **~30 GB, gitignored but present.** 207 files: `{subj}_{interictal,ictal}.npy` (raw windows), `_adjs_topk20.npy`, `_features.npy`, `gamma_aec_*.npy`, `{subj}_stats.json`. The six canonical rlg input types. |
| `models_retrain/gae_joint_seed42.pt` | **THE canonical GAE.** 15258 B, sha256 `dea06cb5…`, bias fingerprint 1.1597, chb13 recon AUROC 0.8319. |
| `models_retrain/gae_joint_seed{1,2,3}.pt` | seed-robustness set (RoR §7). bias 1.3705 / 1.5801 / 1.6370. |
| `models_retrain/gae_multirel_seed42.pt` | Phase-C C4-full negative, kept for provenance. Does not load with the standard `GAEModel`. |
| `models_retrain/_archive/*.zip` | original Kaggle checkpoint zips, including 5 LSTM checkpoints (dropped branch). |
| `pernode_v2/seed{42,1,2,3}/` | per-node reconstruction error, `[n_win, 18]` float32, 22 arrays + `MANIFEST.json` each. Regenerate: `attribution_pipeline.py dump --seed N`. |
| `splits/split_main.json` | ⚠️ old E_main split — see §7.1. |

**Locked splits (never violate).** TRAIN 12: chb01,02,04,05,07,08,09,12,19,20,21,23 ·
VAL 3: chb10,11,22 · TEST 8 (ONE-SHOT): chb03,06,13,14,15,16,17,18 — 76 seizures, 278.2 interictal h.

---

## 5 · `results/`

| path | content |
|---|---|
| `phaseB/tier2/` | **rlg CANONICAL.** `ens_test_tf/components/` = the committed one-shot TEST branch components (`zrecon_*`, `zlatent_*`, `zgamma_*`) — the ground truth for checkpoint verification. `ens_test_tf/{rlg,lg}/` = TEST ensembles · `ens_val_tf/` = VAL · `{rlg,lg,rg,ltg,rltg,baseline_rtg}/` = VAL grids · `{rlg,lg}_test/` = TEST grids · `ONESHOT_rlg_vs_s0.csv` · `G2prime_val.csv` · `FINAL_report.csv`. |
| `phaseB/` | `E1_ablation_val.csv`, `E2_latent_val.csv`, `S2_S3_negatives.md`. |
| `phaseC/` | Phase-C negatives: `artifact_gate/`, `artifact_probe/`, `c1/`, `c4full/`, `c4lite/`, `c_onset/`, `reencode/`. |
| `attribution_v6/` | **attribution results** — see `ATTRIBUTION_SPEC.md` §8 for the file-by-file table. `labels/ictal_channels_DRAFT.csv` is PROVISIONAL. |
| `attribution_v5/labels/` | ⚠️ **`labels_*_FINAL.csv` are the reader labels — IRREPLACEABLE, never delete.** The `*_onset.png` / `*_review.png` images are the views that were scored. |
| `label_material/` | labelling inputs: `seizure_segments/` (76 per-seizure renderings + meta + raw npy) and a README pointing at the label files. |
| `retrain_v3p1/` | §0 baseline grids and operating points (pre-Tier-2). Historical comparison only. |
| `history_topology/` | topology-feature probe (negative), with `topo_features/`. |
| `history_superseded/` | ⚠️ **DO NOT CITE — see §7.4.** Pre-rebuild detection results, old attribution outputs, old weight grids. |

---

## 6 · `archive/` — do not cite, do not run

`src_superseded/{attribution_v5, phaseAB_oneoff, utils, provenance_2026-09-01}` (scripts retired
2026-09-02) · `attribution_superseded/attribution_c{1,2,3}.py` (retired eigencentrality framework) ·
`pre_rebuild_s0/` (**§0 model + its per-node dumps — the trap, see §7.5**) · `cpd_history/` (CPD v1–v9) ·
`diagnostics/` (PREREG 05–09 one-off scripts) · `fp_reduction_prior/` (CUSUM / smoothing / session-norm
prior work) · `probes_old/`, `rejected/`, `priorchat_diagnostics/` · `kaggle_incoming/` (Kaggle result
zips, already unpacked into the repo) · `scaffolding/` (pre-thesis E_main pipeline; see its
`README_PRE_THESIS.md`) · `thesis_repro_lock.py`.

---

## 7 · TRAPS — each of these has caused or nearly caused a real error

### 7.1 `create_splits.py` and `data/splits/split_main.json` are the WRONG split
They encode the old **E_main 15 train / 8 test** design. The locked thesis split is **12 TRAIN / 3 VAL /
8 TEST**. Never regenerate splits from that script; the split is fixed and listed in §4.

### 7.2 Five LSTM files in `src/retrain/` belong to a dropped branch
The temporal branch was removed by **PREREG_TIER2 Amendment A1** — its training code was unrecoverable
and its pre-rebuild numbers depended on lost components plus test-selection. Never describe the temporal
branch as part of the final system. The files exist only as provenance of the decision.

### 7.3 `docs/archive/` contains a stale `RESULTS_OF_RECORD.md`
It carries pre-rebuild numbers. **Forbidden numbers — never cite: 0.750 / 0.829 / 0.791 / 39.77 / 71.25.**
They were never reproduced.

### 7.4 `results/history_superseded/` looks canonical and is not
It contains complete-looking attribution and detection outputs from before the rebuild. Directory names
mirror the live ones. Always check you are under `results/phaseB/tier2/` or `results/attribution_v6/`.

### 7.5 The §0 model correlates 0.99 with canonical — close enough to fool a spot check
`archive/pre_rebuild_s0/best_model_joint_lambda01.pt` (17481 B, bias fingerprint **0.8676**,
chb13 recon AUROC **0.8360**) reproduces the committed TEST components at corr 0.987–0.999. The canonical
checkpoint reproduces them at **1.0000000 on 16/16**. On 2026-09-01 this near-match caused the canonical
checkpoint to be briefly misidentified as corrupt, and would have caused the attribution chapter to
describe the wrong model.

**Identify checkpoints by measurement, never by filename or by the constants 0.8676 / 0.836** — those
are §0 values that still appear in old docs and old code comments. Run `src/verify_provenance.py`.

---

## 8 · Outside the repo (not tracked)

| path | content |
|---|---|
| `F:/Study/Thesis/Dataset/CHB-MIT/` | EDF recordings in `chb03/`, `chb06/`, … |
| `F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary/` | `chbNN-summary.md` — onset/offset times. **`.md`, not `.txt`.** |
| `F:/Study/Thesis/Papers/` · `Reports/` · `Web demo/` · `Agent/` · `Threshold/` | literature, report drafts, SzScan demo, tooling |

**Environments.** Local: Windows + Git Bash + Cursor, CPU. Kaggle: notebooks (cells, not bash), GPU,
4 accounts; datasets mount at nested paths — auto-discover with `rglob`, never hardcode; Kaggle is
disposable compute, every output is downloaded and committed the same day; uploaded `.pt` files unpack
into directories and need re-zipping for `torch.load` (this is the mechanism behind §7.5).

**`rm` in Git Bash does not use the Recycle Bin.** Always `ls`/`du` a path before `rm -rf`.
