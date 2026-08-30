# REPO_MAP -- F:/Study/Thesis/Code (post-cleanup 2026-08-30)

SINGLE SOURCE OF TRUTH for "which folder holds what".
On any number conflict, docs/RESULTS_OF_RECORD_phaseB.md WINS over this file and memory.

STATUS: Phase C CLOSED. Final thesis pipeline = rlg (recon + latent-Mahalanobis + gamma, equal 1/3, temporal-free).
Phase D = Future Work (docs/PHASE_D_HANDOFF.md). Restore point: git tag phase-c-final.

## A. LOCKED PIPELINE (rlg) -- canonical inference chain
raw windows -> graphs (wPLI+AEC top-k20) -> Joint GAE (seed42)
 -> 3 readouts [zrecon, zlatent, zgamma] -> equal 1/3 ensemble
 -> PELT (cpd_pipeline_v14) -> label-free FP-budget OP -> SzCORE (timescoring)

Code (run `python src/<...>.py` from repo root; flat imports):
  dataprep : src/dataprep/{preprocessing,graph_construction,feature_extraction,compute_gamma_aec,create_splits}.py
  GAE      : src/retrain/{gae_joint,train_gae_joint,retrain_io}.py
  readouts : src/phaseB/latent_anomaly.py (zlatent) ; gamma via dataprep/compute_gamma_aec
  ensemble : src/ensemble_recipe.py (ENS_WEIGHTS equal 1/3; CANDIDATES) ; src/phaseB/build_ens_tier2.py
  CPD      : src/cpd_pipeline_v14.py
  OP       : src/retrain/fp_budget_operating_point.py
  scoring  : src/retrain/score_ens.py ; src/szcore_eval.py ; src/evaluation_protocol.py ; src/stat_validation.py
  VAL-gate : src/phaseB/g2_val_gate.py ; src/phaseB/tier2_oneshot_compare.py

Models (TRACKED, small):
  data/models_retrain/gae_joint_seed42.pt        = canonical GAE (rlg)
  data/models_retrain/gae_joint_seed{1,2,3}.pt   = seed-robustness (window AUROC 0.929 +/- 0.002)
  data/models_retrain/gae_multirel_seed42.pt     = Phase C C4-full (negative; provenance)
  data/models/best_model_joint_lambda01.pt       = original joint GAE
  data/models_retrain/_archive/                  = superseded zips/dirs + dropped LSTM (gitignored)

## B. LOCKED NUMBERS -> docs/RESULTS_OF_RECORD_phaseB.md (sections 0-9)
  rlg VAL-derived balanced : F1 0.213 @ 27.4 FP/day
  rlg Pareto peak          : F1 0.426 @ 4.9 FP/day
  window macro AUROC       : 0.805
  WARN: do NOT cite 0.750/0.829 (pre-rebuild, unreproducible -> docs/archive/RESULTS_OF_RECORD.md)
  WARN: RUBRIC_TRACKING.md still holds old numbers -> fix during report.

## C. data/ (mostly gitignored; regen from raw or Kaggle)
  processed/ canonical inputs (gitignored, on disk/Kaggle):
    {subj}_{interictal,ictal}.npy (raw z) ; _adjs_topk20.npy ; _features.npy ;
    gamma_aec_{subj}_{inter,ictal}.npy ; {subj}_stats.json   [8 TEST + 3 VAL + 12 TRAIN]
  pernode/ TRACKED = attribution per-node arrays (8 TEST)
  splits/  TRACKED = split_main.json (LOCKED seed42)

## D. results/
  phaseB/tier2/       = rlg CANONICAL: ens_{val,test}_tf/rlg/*.npy + grids + ONESHOT + FINAL_report
  phaseB/             = E1_ablation_val, E2_latent_val, S2_S3_negatives
  retrain_v3p1/       = baseline grids/OP (final_eval_seed42, fp_budget_locked, t1_*, report_metrics)
  phaseC/             = Phase C negatives (c4lite, c4full, c1, c_onset, artifact_gate, reencode)
  attribution_v6/     = current attribution (labels_*.csv ; *.png gitignored) ; v5 = prior
  history_superseded/ = ARCHIVE, do NOT cite (pre_rebuild_detection, rebuild_round1, ...)

## E. docs/
  CANONICAL (top): RESULTS_OF_RECORD_phaseB, REPO_MAP, PHASE_C_FINAL_HANDOFF, PHASE_C_CLOSEOUT_provenance,
    PHASE_D_HANDOFF, REBUILD_BASELINE_LOCK, ATTRIBUTION_SPEC, Spatial_Localization..., TIEU_CHI_LABEL_v2,
    Proposed_solution_updated_v5, RUBRIC_TRACKING, PLAN_AND_STATUS, PROVENANCE_MAP
  prereg/ = PREREG_01..09 + C0 + TIER2 (+ amendment_A1)
  demo/   = WEB_DEMO_SPEC_v4 (WINS on demo) + design/migration/context + THESIS_REPORT_WRITING_GUIDE
  archive/ = superseded handoffs/plans -- do NOT cite

## F. src/ namespaces
  core (flat): ensemble_recipe, cpd_pipeline_v14, szcore_eval, evaluation_protocol, stat_validation, edf_index
  dataprep/, retrain/ = pipeline (see A)
  phaseB/ = Tier-2 rlg (latent_anomaly, build_ens_tier2, g2_val_gate, ...)
  phaseC/ = Phase C R&D (connectivity_probe, build_te_branch, gae_joint_multirel, ...) -- mostly negative, provenance
  attribution: attribution_gae_pernode, attribution_headmap, attribution_tpfp, compare_labels_pernode,
    validate_dominant_hitk_FINAL, visualize_*
  figures: fig5_eight_subjects, fig_A_three_scores, fig_B_raw_eeg_pelt, plot_event_level
  experimental/one-off (NOT in rlg path): mag_pen_grid_sweep_v2, weight_*_sweep, duration_stratified_sensitivity,
    event_ablation, window_*, rebuild_ensemble_new_weight, diagnose_fp_mechanism, eval_multiseed
  archive/diagnostics/ = prior-chat diagnostic scripts (t1/t3/t4/...)

## G. EXTERNAL (outside repo, NOT tracked)
  F:/Study/Thesis/Dataset/CHB-MIT/           = EDF + "CHB info/summary/chb*-summary.txt" (score_ens --summary_dir)
  F:/Study/Thesis/{Papers,Reports,Web demo,Agent,Threshold}/ = papers/PDFs, thesis reports, SzScan frontend,
                                               Claude-project doc store, threshold side-analysis
  Kaggle (nhn2mm, norncreades)               = graphs/features/gamma/checkpoints for GPU

## H. TAGS
  pre-cleanup   = safety snapshot before 2026-08-30 cleanup
  phase-c-final = LOCKED rlg thesis pipeline (restore point)
