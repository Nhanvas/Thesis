# `results/` — what each result is, and which `RESULTS_OF_RECORD.md` section cites it

Rule for this folder: **default is KEEP + label.** Only files proven superseded live under
`history_superseded/`; everything else is either CITED (an authoritative number in the thesis) or
kept as a record. When a number here disagrees with `docs/RESULTS_OF_RECORD.md` (ROR), **ROR wins.**

## CITED — authoritative (these back the thesis numbers)

| path | ROR § | what it is |
|---|---|---|
| `locked/locked_phaseA_event_results.csv` | §1 | pooled event results — the two locked operating points (0.750/39.77 · 0.829/71.25) |
| `phaseA_appendix/szcore_event_level_new_decision19_mag60.csv` · `…_mag50.csv` | §1 | per-subject event TP/FP at the two points |
| `phaseA_appendix/mag_pen_grid_v2_pooled.csv` · `…_persubject.csv` | §1 | seeding-fixed mag×pen Pareto grid (source of the locked points) |
| `phaseA_appendix/duration_bucket_summary.csv` · `duration_hit_persubject.csv` | §4 | sensitivity stratified by seizure duration |
| `cpd/evaluation/eval_window_level_newweight.csv` | §2 | per-subject window AUROC (new weight; macro 0.791) |
| `cpd/evaluation/eval_stat_tests_newweight.csv` | §2 | window-tier significance tests |
| `cpd/evaluation/window_component_auroc_newweight.csv` | §2 | recon/temporal/gamma standalone AUROC |
| `phaseB_newweight/event_ablation_pooled.csv` · `…_persubject.csv` | §8 | leave-one-view-out event ablation |
| `cpd/evaluation/multiseed/*` | §(robustness) | multi-seed robustness evidence |
| `attribution/attribution_pernode_summary.csv` (+ `attribution_*`) | §7 | per-node GAE attribution (primary) |
| `attribution_v3/*` (+ `tpfp_*`) | §7 | preregistered attribution redesign (Test A concentration, Test D TP-vs-FP) |

## RECORD — kept for provenance, not a headline number

| path | what it is |
|---|---|
| `phaseB/fp_diagnosis/*` · `phaseB/cross_view_consensus/*` | FP-mechanism diagnostics that motivated the #23 filter experiment |
| `phaseB/fp_filter_step1_events.csv` · `fp_filter_step2*_*.csv` | **Decision #24 REJECTION RECORD** — the CUSUM persistence filter was tested and NOT adopted (ROR §15). Never cite as a result; never wire into the pipeline. |
| `phaseB/auroc_verification.csv` | component AUROCs valid; its ensemble column is old-weight — use §2 instead |

## DO NOT CITE — superseded / quarantined

- `history_superseded/` (all of it): old-weight caches, buggy pre-v2 grid, old pipeline lineage
  (cpd_results v3–v12, tolerance sweep, window_metrics), old eval tiers, old baselines (ce_*, znorm_*),
  old event-level generations, rejected topology. Kept only for auditability.

> Reproduce the CITED headline numbers from committed components with `python src/thesis_repro_lock.py`.
