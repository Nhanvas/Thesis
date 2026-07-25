# `src/` — code map

Every script here runs from the **repo root** as `python src/<name>.py` (flat layout so the
mutually-importing modules resolve each other; relative `data/` and `results/` paths resolve
against the root working directory). Sub-packages: `src/dataprep/` (upstream data prep, produces
the cached Kaggle inputs), `src/fp_reduction_prior/` (CUSUM/EMA prior-art for the #23 FP filter).

Authoritative numbers live in `docs/RESULTS_OF_RECORD.md`; provenance in `docs/PROVENANCE_MAP.md`.

Status legend: **CORE** (single source of truth) · **ACTIVE** (re-run for report / #23) ·
**PROVENANCE** (one-off that produced a locked number; kept for traceability, not re-run) ·
**SUPERSEDED** (candidate for `archive/`).

## Core (single source of truth)
| file | role |
|---|---|
| `ensemble_recipe.py` | **CORE** — ensemble weight `(0.40,0.35,0.25)` + `build_ensemble` from components. The ONLY place the weight is defined. |
| `cpd_pipeline_v14.py` | **CORE** — the ONE detection algorithm (seed-independent PELT + magnitude filter). |
| `szcore_eval.py` | **CORE** — SzCORE-exact event scoring (`evaluate_subject`, `score_szcore`, `build_timeline_masked`). |
| `evaluation_protocol.py` | **CORE** — shared parsing (`parse_summary_edf_list`), stats (DeLong CI, bootstrap), constants (`TEST_SUBJS`, `PEN_MULTS`). |
| `thesis_repro_lock.py` | **CORE** — reproduces both locked operating points bit-exact from components. Run to verify the repo self-reproduces. |

## Active analysis / evaluation (re-run for the report and #23)
| file | produces |
|---|---|
| `window_tier_newweight.py` | window tier §2: `eval_window_level_newweight.csv`, `eval_stat_tests_newweight.csv`, `window_component_auroc_newweight.csv` |
| `event_ablation.py` | leave-one-view-out event ablation → `results/phaseB_newweight/event_ablation_*` |
| `duration_stratified_sensitivity.py` | per-seizure hit/miss × duration → `results/phaseA_appendix/duration_*` |
| `stat_validation.py` | Wilson / Poisson CIs on the locked operating points |
| `mag_pen_grid_sweep_v2.py` | seeding-fixed mag×pen Pareto grid → `mag_pen_grid_v2_{pooled,persubject}.csv` (source of the two locked points) |
| `attribution_gae_pernode.py` | **primary** per-node GAE attribution battery → `attribution_pernode_*` |
| `attribution_v3.py` | preregistered attribution redesign, Test A concentration → `attribution_v3_*` |
| `attribution_tpfp.py` | attribution redesign Test D (TP-vs-FP triage) → `tpfp_*` |
| `attribution_headmap.py` | display-only per-channel head maps (UNVALIDATED DISPLAY watermark) |
| `visualize_channel_attribution.py` | montage attribution heatmaps for the report |
| `visualize_chb06_inversion.py` | chb06 inverted-connectivity illustration |
| `diagnose_fp_mechanism.py` | FP mechanism diagnostics → `results/phaseB/fp_diagnosis/*` (input to **#23**) |
| `consolidate_outputs.py` | housekeeping: copy scattered outputs into `results/` tree + `MANIFEST.txt` |

## Report figures (kept as scaffolding for the final report figures)
Kept for their working data-loading / seizure-alignment / PELT-overlay code, not their current
aesthetics. When producing the final report figures, rebuild on the core plumbing
(`szcore_eval.build_timeline_masked` + `evaluation_protocol.parse_summary_edf_list`) and then
retire these. Older redundant variants (`fig4_component_signals`, `fig_3scores_8subj`,
`fig6_raw_eeg`, `fig_raw_eeg_pelt_8subj`) were deleted (recoverable from git history).

| file | figure |
|---|---|
| `fig5_eight_subjects.py` | 8-subject ensemble-timeline overview |
| `fig_A_three_scores.py` | 3-score decomposition (z_recon / z_temporal / \|z_gamma\|), all 8 subjects |
| `fig_B_raw_eeg_pelt.py` | raw EEG + PELT change point at first TP, all 8 subjects |

## Provenance one-offs (kept for traceability — do NOT re-run, do NOT archive)
| file | produced |
|---|---|
| `rebuild_ensemble_new_weight.py` | the official Decision #19 numbers on the new weight |
| `eval_multiseed.py` | multi-seed robustness → `results/cpd/evaluation/multiseed/*` |
| `weight_sensitivity_sweep.py` | ensemble-weight sensitivity grid (verification) |
| `weight_seed_robustness_check.py` | is the weight-grid signal real vs seed-0 noise |
| `weight_candidate_crosscheck.py` | candidate weight cross-check across both operating points |
| `window_event_gap.py` | window↔event gap table — **STALE INPUT**: reads old-weight CSVs now in `history_superseded/`; re-run on new-weight inputs if used in the report |

## Archived (moved out of `src/` — see `archive/`)
| file | now at | why |
|---|---|---|
| `attribution_c1.py` / `c2.py` / `c3.py` | `archive/attribution_superseded/` | dropped eigencentrality attribution battery; superseded by `attribution_gae_pernode` → `attribution_v3` |
| `eval_gamma_aec.py` | `archive/rejected/` | v10-era gamma AUROC diagnostic, no saved output; superseded by `window_component_auroc_newweight.csv` |
