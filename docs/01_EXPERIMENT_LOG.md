# 01 · EXPERIMENT LOG (prior chat) — DO NOT REPEAT; reuse numbers/files

All below are DECISION-LAYER / diagnostic experiments (no pipeline change). Reuse results; do not rerun.
Files live in the prior chat's outputs; scripts read `test_grid.csv` = `results/retrain_v3p1/final_eval_seed42.csv`
(384 rows, 8 test subj × 8 mag × 6 pen) and VAL grid = `results/retrain_v3p1/val/final_eval_seed42.csv`
(144 rows, chb10/11/22).

## T1 — VAL-derived operating point (PREREG_05, argmax-F1)
VAL argmax-F1 → **mag80/pen10**; one-shot test: **sens 0.276 / prec 0.362 / F1 0.313 / 3.19 FP·d⁻¹**,
TP/FN/FP 21/55/37. H1 (F1≥0.30) confirmed. This is the cleanest headline (chosen before any test exposure).
Files: `PREREG_05_operating_point_T1.md`, `t1_derive_operating_point.py`, `T1_RESULT.md`, `t1_*.csv`.

## Full TEST Pareto frontier (pooled, from T1)
mag80/pen10 0.276/0.313@3.2 · mag70/pen10 0.289/0.293@4.5 · **mag80/pen5 0.395/0.351@5.6** ·
mag75/pen5 0.421/0.340@6.9 · mag70/pen5 0.434/0.328@7.9 · mag65/pen5 0.461/0.318@9.4 ·
mag80/pen2 0.487/0.314@10.6 · … · mag70/pen0.5 0.632/0.168@38.6 · mag55/pen0.3 0.776/0.121@72.7 ·
mag40/pen0.3 0.816/0.100@94.5. (sens/F1@FP·d⁻¹)

## RESELECT (PREREG_06, knob-free balance + FP-budget)
min|sens−prec| and argmax-F1 BOTH pick mag80/pen10 (lopsided on test). Only the ~10 FP/day budget rule
→ **mag80/pen5: sens 0.395 / prec 0.316 / F1 0.351 / 5.6 FP·d⁻¹** (SOTA-band on all 4 axes).
**Finding:** a single global VAL-derived threshold can't match SOTA on all axes (VAL easy → prefers high
penalty; hard test subj collapse there). Files: `PREREG_06_*`, `reselect_balanced_op.py`, `RESELECT_RESULT.md`.

## T3 — per-subject grid-oracle ceiling (diagnostic; peeks labels)
chb06 oracle-F1 **0.087**, chb14 **0.083** → REPRESENTATION-limited (no OP rescues). chb17 0.444, chb16
0.265, chb13 0.367, chb15 0.727 → decision-limited. chb03 0.737, chb18 0.471 → near ceiling at mag80/pen10.
Files: `t3_oracle_ceiling.py`, `T3_RESULT.md`, `t3_oracle_ceiling.csv`.

## Per-subject label-free FP-budget (PREREG_07) — NEGATIVE
B=5: 0.316/0.316/0.316@4.5 · B=10: 0.329/0.188/0.239@9.3 · B=20: 0.513/0.154/0.237@18.5.
Does NOT beat shared mag80/pen5. chb17 recovers 0→sens 0.667 label-free (cell mag50/pen10); chb06/14 never
fire. Files: `PREREG_07_*`, `per_subject_fp_budget.py`, `persubj_fp_budget_B{5,10,20}.csv`.

## Selective hybrid (loosen under-firing subj) — NEGATIVE
base mag80/pen5 → hybrid F1 **0.351→0.301** (mis-loosens efficient chb15, −7 TP). **Label-free cannot
distinguish "strangled" (chb17) from "efficient at low FP" (chb15)** → selective recovery not bankable
without leakage. (computed inline; no file.)

## Duration filter (PREREG_09) — REJECTED (structural)
Scoring path (`szcore_eval.cps_to_events`) emits 4 s events, no merge (merge only in `detect_events`,
web-demo path). D≤4 no-op, D≥8 wipes all → no exploitable short-FP/long-TP separation. Script fidelity
gap: self-check 0.382 vs grid 0.395 (~1 TP; missing `np.random.seed` before `build_timeline_masked`).
Files: `PREREG_09_*`, `duration_filter_sweep.py`.

## Window suite (W1, PREREG_08) — MEASUREMENT (baseline numbers, keep)
macro AUROC 0.775 (gate PASS), macro AUPRC 0.097 (lift 13.6×), pooled AUROC 0.817 / AUPRC 0.051.
Per-subject AUPRC: chb03 .171 / chb06 .004 / chb13 .038 / chb14 .021 / chb15 .218 / chb16 .104 /
chb17 .016 / chb18 .201. Window prec/rec/F1 @ VAL t*=4.85: macro 0.131/0.152/0.104.
Files: `PREREG_08_*`, `window_metric_suite.py`, `w1_window_suite.json`.

## T4 — chb06/chb14 branch sign probe (diagnostic; CLOSED)
Per-branch AUROC — chb06: zrecon **0.300 (inverted)**, ztemp 0.488, zgamma 0.578, ens 0.437.
chb14: zrecon 0.662, ztemp 0.823, zgamma **0.401 (inverted)**, ens 0.626. chb03: zrecon 0.659 (fine).
**No global sign bug** (zrecon fine for chb03/14) → chb06/14 inversions are SUBJECT-SPECIFIC → a flip
needs test labels = LEAKAGE. **chb06/14 = representation-limited.** Different branch fails per subject
(chb06→GAE recon, chb14→gamma) → motivates learned/adaptive graph. Note: `t4_chb06_probe.py` auto-gate
said "free fix" — WRONG (didn't check leakage); `t4_globality_check.py` overrides.
Files: `t4_chb06_probe.py`, `t4_globality_check.py`, `WINDOW_SUITE_AND_T4_CLOSE.md`.

## Evaluation bug caught (keep in mind)
SzCORE splits seizures >5 min into multiple ref-events. **VAL chb11: 3 summary seizures → 5 ref-events.**
Pool sensitivity by Σ(scorer refTrue), NOT Σ n_seizures. ALL 8 TEST subj clean (n_seizures==ref, 0/48
mismatch) → test headlines unaffected; T1 selection invariant under fix.

## KEY REPO FILES / DATA (for the upgrades)
Model `gae_joint.py` = GAEEncoder 2×GCNConv (23→64→16) on **FIXED top-k20 adjacency**, XDecoder 16→32→5,
5 bands, 18 ch. `lstm_temporal.py`, `ensemble_recipe.py` (equal 1/3), `cpd_pipeline_v14.py`,
`szcore_eval.py`, `evaluation_protocol.py`, `retrain_io.py`, `train_lstm_temporal_v3.py`.
Data: Kaggle `nhn2mm/chbmit-topk20` adjacency `.npy` (`_topk20` suffix); features `.npy` (n_win,18,5);
ensemble scores `results/retrain_v3p1/{ens,val_ens}/ens_seed42_{subj}_{inter,ictal}.npy`; branch components
`data/processed/components/{zrecon,ztemp,zgamma}_{subj}_{inter,ictal}.npy`; grids as above. summary_dir =
CHB-MIT `*-summary.txt`. 6 seed checkpoints (seed 42 canonical).

## E2 latent-manifold readout — WIN
GAE latent Mahalanobis (pooled Z 16-d, LedoitWolf, per-subject interictal fit).
VAL macro AUROC 0.731 vs recon 0.592; chb10 0.268→0.816 (lật inversion do ictal hypersync).
Ensemble: latent+temp+gamma 0.931 / recon+latent+temp+gamma 0.918 (AUPRC 0.280) vs recon+temp+gamma 0.866.
→ latent-readout khoá làm nhánh GAE. File: latent_anomaly.py, dump_val_components.py, branch_ablation.py.

## S2 learned graph — REJECTED
multiband 0.581 / GSL-gated NULL (g→0, ==baseline) / GSL-forced 0.579 (chb10 vẫn đảo). Graph không phải đòn bẩy.

## S3 compactness (Deep-SVDD) — NEGATIVE
retrained latent macro 0.686 < 0.731; comp ~0.0005 (manifold đã compact). Dừng upgrade GAE. Không làm SSL.