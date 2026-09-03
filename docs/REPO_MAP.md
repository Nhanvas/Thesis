# REPO_MAP — repository structure, post-cleanup, rev. 2026-09-03

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
**Tags:** `pre-cleanup` (safety snapshot) · `phase-c-final` (locked rlg thesis, restore point) ·
`demo-spec-v5` (web-demo spec set locked) · `repo-deps-fixed` (two canonical deps restored — see §7.7)

---

## 1 · Top level

```
Code/
├── src/          code — 7 canonical modules + 6 role-scoped folders
├── docs/         governance and specifications (the only citable docs)
├── web_demo/     SzScan web demo — spec set, locked UI, backend/frontend (see §3b)
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
| `evaluation_protocol.py` | Shared constants + summary parsing (`parse_summary_edf_list`). Imported by `szcore_eval`, `figures/attribution_headmap`, `figures/visualize_chb06_inversion`, `phaseC/align_check{,2}`. **Restored to `src/` on 2026-09-03 — see §7.7.** |
| `stat_validation.py` | **SINGLE SOURCE** for Wilson / Poisson confidence intervals. Imported by `retrain/final_eval` → `retrain/fp_budget_operating_point`. **Restored to `src/` on 2026-09-03 — see §7.7.** |
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

`figures/attribution_figures.py` — report figures for the attribution chapter. Reads **only** the
committed CSVs in `results/attribution_v6/`; recomputes nothing, so a figure can never disagree with
the tables in `ATTRIBUTION_SPEC.md` §9. Run: `python src/figures/attribution_figures.py`.
Outputs to `figures/attribution/`:

| output | status | rubric |
|---|---|---|
| `attribution_fig1_synthetic.png` | ✅ label-free, final | #6, #8 — machinery-correctness exhibit |
| `attribution_fig2_seed_robustness.png` | ✅ label-free, final | #6 |
| `attribution_fig3_rank_heatmap.png` | ✅ label-free, final | #7, #8 — per-seizure channel ranking, 76 × 18 |
| `attribution_fig4_persubject_forest.png` | ❌ PROVISIONAL (labels) | #7 — rerun if labels are frozen |
| `attribution_top3_channels.csv` | ✅ label-free, final | report appendix |

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
| `THESIS_REPORT_WRITING_GUIDE.md` | governs report writing. Moved out of `docs/demo/` on 2026-09-03 — it is a thesis doc, not a demo doc. |
| `ATTRIBUTION_REPORT_PACK.md` | attribution chapter material for the report. Same move, same reason. |
| `demo/` | **EMPTY as of 2026-09-03.** All four `WEB_DEMO_*` docs → `archive/demo_v4/`; `edf_order.py` → `web_demo/backend/`; the two report guides → `docs/` top level. Demo authority now lives in `web_demo/` (§3b). |
| `archive/` (25 files) | ⚠️ **DO NOT CITE — see §7.3.** Superseded handoffs, the old `RESULTS_OF_RECORD.md`, `TIEU_CHI_LABEL_dominant_channel_v2.md` (retired label criteria), `WEB_DEMO_SPEC.md`, and the `Spatial_Localization…md` field survey. |
| `archive/demo_v4/` (4 files) | ⚠️ **DO NOT CITE.** `WEB_DEMO_SPEC_v4.md`, `WEB_DEMO_DESIGN_SYSTEM.md`, `WEB_DEMO_CONTEXT_BOUNDARY.md`, `WEB_DEMO_CODE_MIGRATION_NOTES.md` — all superseded 2026-09-03 by the `web_demo/` set. The v4 spec still describes an LSTM branch and a cache-replay architecture; both are wrong. |

---

## 3b · `web_demo/` — SzScan (spec set locked 2026-09-03, build not started)

**Authority inside demo scope:** `UI/` (locked PNGs — wins on anything visible) >
`SZSCAN_SPEC_v5.md` > `SZSCAN_DESIGN_v2.md` > `DEMO_BUILD_HANDOFF.md`.
Scientific authority (`RESULTS_OF_RECORD_phaseB.md` etc.) still governs any number.

| path | role |
|---|---|
| `SZSCAN_SPEC_v5.md` | **WINS on any demo behaviour/logic conflict.** Supersedes `WEB_DEMO_SPEC_v4.md` + `WEB_DEMO_CONTEXT_BOUNDARY.md`. §1 carries the data-architecture proof — read it in full before writing backend code. |
| `SZSCAN_DESIGN_v2.md` | visual tokens, **measured by pixel-sampling the locked PNGs**, not guessed. Supersedes `WEB_DEMO_DESIGN_SYSTEM.md`. |
| `DEMO_BUILD_HANDOFF.md` | stack, folder layout, build order, risks. Absorbs `WEB_DEMO_CODE_MIGRATION_NOTES.md`. |
| `CLAUDE.md` | rules for Claude Code when building the demo. Carries the three hard guards. |
| `PROJECT2_SETUP.md` | how to stand up the second Claude project + which files to upload. |
| `UI/` | 29 locked PNG mockups + `UI (figma).fig`. **Author-designed and frozen — never propose a redesign.** |
| `backend/edf_order.py` | orders EDFs by header time for UI display, which differs from the by-filename order used for processing. Moved here 2026-09-03; demo-only, not shared with the thesis. |
| `backend/` · `frontend/` · `cache/` | created when coding starts. `cache/` is gitignored. |

**Three hard guards (SPEC §1.2) — the demo is presented as label-free:** never call
`szcore_eval.build_timeline_masked()`; never read the seizure fields from `chb*-summary.md` at runtime;
never load `{subj}_{interictal,ictal}.npy`. Plus: demo code writes only inside `web_demo/`.

**Why:** the committed `ens_seed42_*` arrays are segment-ordered with no window→second index, and
`build_timeline_masked()` rebuilds a timeline *from the annotations*, bootstrap-filling gaps. Positional
information was destroyed at preprocessing. The demo therefore recomputes label-free on the continuous
recording (measured 16.9 ms/window ⇒ ~15 s per hour of EEG on the dev CPU).

**`edf_index.py` does not exist and is not needed.** It belonged to the retired v3 architecture and was
deleted. Under v5 each file's score array has length equal to that file's window count, so per-file
offsets follow by construction — no lookup table, no summary parsing.

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
| `attribution_v6/` | **attribution results** — see `ATTRIBUTION_SPEC.md` §8 for the file-by-file table. `labels/ictal_channels_DRAFT.csv` is PROVISIONAL **and is dominant-channel, not the §3.2 ictal set** (see §7.6). |
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

### 7.6 The label file is not the schema the spec asks for
`results/attribution_v6/labels/ictal_channels_DRAFT.csv` records the reader's **dominant channel(s),
1–2 per seizure** (40 DIFFUSE / 25 one-channel / 11 two-channel). `ATTRIBUTION_SPEC.md` §3.2 asks for
every channel with clear ictal discharge. Any label-scored attribution number therefore answers a
narrower question than the spec poses, and the near-constant labels make the D7 control uninformative.
Detail: `ATTRIBUTION_SPEC.md` §3.3 and §9.3.

### 7.7 Two canonical modules were archived while still imported (fixed 2026-09-03)
The 2026-09-01/02 cleanup moved `evaluation_protocol.py` → `archive/src_superseded/utils/` and
`stat_validation.py` → `archive/src_superseded/phaseAB_oneoff/` **without checking who imported them.**
Both were live dependencies:

- `src/szcore_eval.py` → `evaluation_protocol` — SzCORE event scoring could not be re-run at all.
- `src/retrain/fp_budget_operating_point.py` → `final_eval` → `stat_validation` — the PREREG_04
  operating point could not be re-run.

Committed results were unaffected (they predate the cleanup); the ability to **reproduce** them was not.
Both files are now back in `src/` (tag `repo-deps-fixed`). A third file, `edf_index.py`, was deleted in
the same pass; the v5 demo architecture does not need it.

**Standing check — run after any file move, before committing:**
```bash
python - <<'EOF'
import ast, pathlib, sys
roots=['src','src/dataprep','src/retrain','src/phaseB','src/phaseC','src/figures','src/labeling']
avail={p.stem for r in roots if pathlib.Path(r).exists() for p in pathlib.Path(r).glob('*.py')}
std=set(sys.stdlib_module_names)
third={'numpy','pandas','scipy','torch','torch_geometric','sklearn','matplotlib','mne','ruptures',
       'timescoring','tqdm','seaborn','networkx','joblib','yaml','PIL','statsmodels','h5py','numba'}
missing={}
for f in sorted(pathlib.Path('src').rglob('*.py')):
    try: tree=ast.parse(f.read_text(encoding='utf-8',errors='ignore'))
    except SyntaxError: continue
    for n in ast.walk(tree):
        mods=[]
        if isinstance(n,ast.Import): mods=[a.name.split('.')[0] for a in n.names]
        elif isinstance(n,ast.ImportFrom) and n.level==0 and n.module: mods=[n.module.split('.')[0]]
        for m in mods:
            if m in std or m in avail or m in third: continue
            missing.setdefault(m,set()).add(str(f))
for m,fs in sorted(missing.items()): print(f'{m}  <-  {", ".join(sorted(fs))}')
print('TOTAL UNRESOLVED LOCAL IMPORTS:', len(missing))
EOF
```
Expected output after the fix: exactly two entries, both harmless —
`gae_joint_gsl` (rejected S2 experiment under `phaseB/archive/`) and `attribution_v3`
(← `src/figures/attribution_headmap.py`, a leftover from before the nine attribution scripts were merged
into `attribution_pipeline.py`; **that figure script is broken and is not in the current figure path**,
which is `src/figures/attribution_figures.py`). Anything else is a real break.

---

## 8 · Outside the repo (not tracked)

| path | content |
|---|---|
| `F:/Study/Thesis/Dataset/CHB-MIT/` | EDF recordings in `chb03/`, `chb06/`, … |
| `F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary/` | `chbNN-summary.md` — onset/offset times. **`.md`, not `.txt`.** |
| `F:/Study/Thesis/Papers/` · `Reports/` · `Agent/` · `Threshold/` | literature, report drafts, Claude-project doc store, threshold side-analysis |

> The old external `F:/Study/Thesis/Web demo/` folder is **gone** — superseded by in-repo `web_demo/`.

**Environments.** Local: Windows + Git Bash + Cursor, CPU. Kaggle: notebooks (cells, not bash), GPU,
4 accounts; datasets mount at nested paths — auto-discover with `rglob`, never hardcode; Kaggle is
disposable compute, every output is downloaded and committed the same day; uploaded `.pt` files unpack
into directories and need re-zipping for `torch.load` (this is the mechanism behind §7.5).

**`rm` in Git Bash does not use the Recycle Bin.** Always `ls`/`du` a path before `rm -rf`.
