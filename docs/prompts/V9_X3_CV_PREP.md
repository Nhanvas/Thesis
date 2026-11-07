# V9-X3 — Patient-wise 4-fold cross-validation of the GAE over all CHB-MIT cases (Claude Code, laptop + Kaggle)

**Rev. 2 (30/10, replaces rev. 1: 4 folds, fold rule fixed below).**
Estimated runtime: preparation here 1–2 h; Kaggle training ≈ 3.3–3.8 h per fold (record: `docs/PERF_PHASE_RECORD.md`, `Agent/gae_v2_train.ipynb`), 4 folds in parallel on 4 accounts; scoring afterwards 1–3 h on the laptop. All estimated, not measured.

## Question (fixed now)
Does the GAE system, trained on more patients and evaluated on every CHB-MIT case it did not see, reach the level of the training-free kNN baseline (per-case mean 0.763 over 24 cases, `results/v9_e4/`), and does GAE + kNN still add to it?

## Design (pre-registered; the rule wins over any list)
1. **Unit = subject, not window or file.** chb21 is chb01 recorded 1.5 years later: the two cases form one group and are always in the same fold. 23 subjects, 24 cases.
2. **4 folds, stratified by seizure count (stratified group k-fold).** Rule: count annotated seizures per group from the summary files (same file rules as the thesis: chb12_27/28/29 skipped); sort groups by seizure count descending, ties by case id ascending; assign in serpentine order to folds 1,2,3,4,4,3,2,1,1,2,… . No random element; nothing about model output is used. Expected result of the rule (verify; if your recount differs, the rule wins — report the difference):
   - fold 1: chb12, chb14, chb20, chb04, chb09 (51 seizures)
   - fold 2: chb15, chb16, chb03, chb08, chb02, chb22 (48)
   - fold 3: chb24, chb06, chb10, chb05, chb07, chb19 (44)
   - fold 4: chb13, chb01 + chb21, chb23, chb18, chb11, chb17 (42)
   Write `results/v9_x3/folds.json` (rule, counts, assignment, commit hash) and **commit it before any training**. Report, without changing anything, the per-fold median seizure duration and number of test-set patients of the thesis split, as a balance check.
3. **Training per fold:** the GAE is trained on the interictal training windows of the other three folds exactly as `retrain/train_gae_v2.py` builds and trains the thesis model (same feature construction, same exclusion of seizure and buffer windows from training data, same hyperparameters, seed 42, last epoch kept). Normalisation constants recomputed per fold from that fold's training subjects only (as the script does). No hyperparameter is tuned.
4. **Scoring per fold:** latent dumps for the held-out fold's cases; the frozen chain (members, ±15-min correction, smoothing, merge, CPD, SzCORE scorer) unchanged; the budget constant k recalibrated per fold with `p3_levers.calibrate()` unchanged on that fold's **training** cases (label-free); GAE + kNN uses the B4 recipe of `results/v9_e1b/` with its k recalibrated the same way. Per-patient statistics label-free (as the external runs and the demo), and the thesis variant (excluding annotated seizures from the z-score statistics) reported second.
5. **Reporting:** per case and per fold; per-case mean over 24 cases and over 23 subjects (chb21 out), patient bootstrap 95 % CI; paired bootstrap GAE-CV vs kNN (`results/v9_e4/` leave-one-case-out) and GAE+kNN-CV vs GAE-CV on the same cases; the 8 original test patients and the 15 original development patients as separate subsets; duration bins; onset/offset error.
6. **Disclosures to print in SUMMARY.md:** (a) the architecture and post-processing were designed on the 15 original development patients (and the per-patient budget cap partly with the test set), so CV numbers on those patients may be mildly optimistic; the 8 original test patients are reported separately; (b) one seed per fold; (c) chb24 is in a fold here, so this analysis is separate from the external evaluation of the thesis model, which is unchanged.

## What to do now (preparation only)
1. Open `retrain/train_gae_v2.py`, `c1b_build_trainset.py`, `Agent/gae_v2_train.ipynb` and the inputs used before (`data/trainset_v2/`, `data/testset_v2/`, the chb24 cache); find how per-subject training arrays are stored. Build per-fold training inputs **from the existing per-subject arrays** (no EEG re-extraction if avoidable); measure their size.
2. Build `results/v9_x3/folds.json` and commit it (step 2 above) before anything is uploaded.
3. Make one Kaggle notebook per fold (`Agent/v9_x3_fold{1..4}.ipynb`), each reading one Kaggle dataset `v9-x3-fold{k}` and writing `gae_fold{k}_seed42.pt` + its normalisation constants + training log. Smoke each locally (`--smoke`, 2 epochs, CPU) and print the parameter count (must be 3,964).
4. Write `src/v9_x3_cv_eval.py` (dump + score). Gate: given the **original** thesis model and the original split, it must reproduce the frozen result on chb03 (seed 42) before it is trusted.
5. Write for the author, in Vietnamese, step by step: which folder to zip, the Kaggle dataset name per fold, which account runs which notebook, accelerator (GPU T4×2), how to check the run is training (log lines), what to download after and the exact local path to put each model.
6. Stop. Report.

## Rules
Read-only on frozen scripts, models and committed results; new code `src/v9_x3_*.py`; outputs `results/v9_x3/`; never overwrite `data/models_v2/` or the thesis model files; commit only these paths. Do not touch `web_demo/`.

## Return format
Full report to `F:/Study/Thesis/Agent/inbox/V9_X3_PREP_REPORT.md`.
