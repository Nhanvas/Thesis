# MODEL_COMPARISON_PLAN — where the GAE stands among other models (rev 2, 2026-11-03 01:00, chat D11-M; §9 up to 04/11 07:50)

*Repo: `docs/MODEL_COMPARISON_PLAN.md` + project file. Replaces rev 1 in full (author decisions 03/11 00:39).
The only experiment running in parallel with the rehearsal prep (board rev 40, R93). Fixed before any run; any
change is logged in §9 with its reason **before** results are seen.*

---

## 0 · Purpose

The committee will ask **"why a graph autoencoder? why not SVM / trees / CNN?"** (anh Trí 02/11, reviewer). This
comparison places the thesis GAE among **single, ordinary models of other families** on the same windows and the
same evaluation — no ablations, no combined models (mentor 02/11; R89). It answers two questions only:

| # | question | rows |
|---|---|---|
| **Q1** | Does a learned graph representation do better than a classical label-free detector on the same input? | GAE vs Isolation Forest |
| **Q2** | What would **labels** of other patients buy? (= "why not SVM / trees / CNN") | GAE vs linear SVM, gradient-boosted trees, 1-D CNN |
| **Q3** (added 04/11, §9) | Does propagating along the graph (message passing) help, with everything else equal? | GAE vs MLP autoencoder |

**Not the purpose:** choosing a system. **The thesis system does not change before the defense** whatever the
outcome (R93, R95). Supervised rows are a reference ceiling — they need labels, outside the registered unsupervised
problem — never the system.

## 1 · Fixed protocol (same for every model)

- **Cross-validation:** the existing 4-fold patient-wise CV (`results/v9_x3/folds.json`): 24 CHB-MIT cases,
  deterministic rule (groups sorted by seizure count, serpentine assignment, no random seed), committed before any
  training; **chb01 + chb21 = one subject, always in the same fold**. Same folds for every model.
  LOSO: not now (cost; the GAE's CV is already on slides) — a leave-one-**subject**-out run of the GAE (23 folds,
  chb01 + chb21 together) is future work for the revised report (author 03/11).
- **Input:** one 4 s window = 18 channels × the GAE's 30-d node input (adjacency row / max 18, band powers per-window
  min–max 5, f7 standardised with the fold's own training constants, clipped ±4, mapped to [0, 1] 7). Raw-EEG CNN:
  future work (needs a raw-signal pipeline).
- **Seed 42.** No early stopping anywhere.
- **Downstream chain = the frozen one, unchanged** (`v9_e1_baselines.evaluate_arm`, the call behind
  `results/v9_x3`): percentile scalar → smoothing 5 → per-patient budget clip(q_i(k), 0.005, 0.02) with k calibrated
  **per fold on that fold's training cases** (median q_i = 0.005, label-free) → merge 90 s → kernel CPD → SzCORE.
  Label-free models: per-channel distance D → members 6/9/12 + mean with ±15 min drift → percentile mean / robust-z
  member mean (budget). Supervised: P(seizure) → percentile; the probability is the budget signal.

## 2 · Models (five, one per family; fixed configuration)

| row | family | model | training |
|---|---|---|---|
| GAE | graph autoencoder, label-free | thesis GAE per fold (`results/v9_x3/models/fold{k}`, 200 epochs, committed) | **not retrained** |
| IF | classical anomaly detection, label-free | Isolation Forest per patient per channel, 200 trees, 256 samples (as V9-E1), on the node input (f7 standardised, unclipped; IF is affine-invariant) | none (per patient) |
| SVM | supervised, kernel | linear SVM, C = 1, class-balanced, standardised 540-d input, to convergence (max 10,000 iterations); score = logistic of the decision value | other 3 folds |
| Trees | supervised, ensemble | HistGradientBoosting, 200 iterations, lr 0.1, 31 leaves, class-balanced, **no early stopping** | other 3 folds |
| CNN | supervised, deep | 1-D CNN over the 18 montage channels (30 input channels → 32 → 32, kernel 3, ReLU, global mean + max pooling, linear), BCE with pos_weight = n_neg/n_pos, Adam 1e-3, cosine, batch 256, **30 epochs, last epoch kept** | other 3 folds |
| MLP-AE (added 04/11) | autoencoder without graph, label-free | the GAE with message passing removed: Linear 30 → 64 → 16 per channel, same decoders, loss, 3,964 parameters | GAE fold recipe, 200 epochs, last kept |

Training windows of the supervised models: every window of the fold's training cases except signal loss and the
4 h post-ictal buffer; label = annotated seizure.

## 3 · Gates (stop on any mismatch)

1. **D0 data identity:** n_ref and non-ictal hours of all 24 cases = `results/v9_x3/fold*_seed42_per_subject.csv`;
   clean training-window counts = each fold model's json.
2. **G-mini (smoke, both notebooks):** GAE fold 1 on chb12 with the committed fold-1 k → committed tp/fp.
3. **GG (full):** the GAE row reproduces `results/v9_x3` — k of each fold within 1e-6 relative (float tolerance across
   library versions, §9 03/11 08:00), tp/fp of all 24 cases × 2 stages and the 185 per-seizure caught flags of
   `results/v9_final/hard/gae_cv_seizures.csv` **exactly**.
4. **CNN training:** last-epoch loss < first-epoch loss; otherwise "did not train", never tuned.

## 4 · Outputs and pre-registered analysis (`src/model_cmp_aggregate.py`, written before any result)

Per model × case: tp/fp at the own point and at fixed 0.005 (detector, localized), detector curve over the common
budget grid, window AUROC, per-seizure caught (record's overlap rule, joined to amplitude ratio and duration).

- **A** main table, per-case means (24 cases): sensitivity, precision, F1, FP/day, window AUROC.
- **B** paired **subject** bootstrap (23 units, B = 10,000) of F1 and sensitivity, each model − GAE.
- **C** curves; sensitivity of every model read at the GAE's own FP/day (same alarm rate).
- **D** per-seizure complementarity with the GAE: both / GAE only / model only / neither, with the amplitude ratio
  and duration of each group — do other models catch the low-amplitude, short seizures the GAE misses?
- **E** wins / ties / losses per case and the most influential subject (is a difference carried by one patient?).
- **F** window AUROC vs event F1 across cases (does window separation transfer to events?).

**Reading rules (fixed):** a difference is stated only if the 95 % CI of B excludes 0; otherwise "no difference
shown on 23 subjects, one seed". No "best" without that CI. A conclusion must hold in B and not be carried by one
subject (E). Supervised = ceiling with other patients' labels. Every statement: "4-fold CV, 24 cases, one seed".

## 5 · Running — Kaggle only; the laptop stays free

| notebook | account | accelerator | jobs |
|---|---|---|---|
| `MC2_A_label_free_and_classical` | 1 (Nhân2mm) | CPU | D0, G-mini, GAE (gate GG), Isolation Forest, linear SVM, trees |
| `MC2_B_cnn` | 2 (nhannguyen26) | GPU T4 x2 | D0, G-mini, CNN × 4 folds |
| `MC3_mlp_folds12`, `MC3_mlp_folds34` (04/11) | 3 (Nhancoding), 4 (Norn Creades) | GPU T4 x2 | D0, G-mini, MLP-AE folds 1–2 / 3–4, G2 |

Inputs: public datasets `v9-x3-fold1` + `v9-x3-fold3` (together: all 24 cases); code: the repository at the pinned
commit `6c5d4d8` (frozen chain, fold checkpoints, reference results; read only) + `src/model_cmp_core.py` and
`src/model_cmp_run.py` embedded verbatim in the notebook (sha256 printed and saved in `run_meta.json`). Each (model, fold) job is atomic and written as soon as it
ends; a job is not started after 10.5 h (listed in `jobs.json` for a next run).

## 6 · Use of the results

Rehearsal 03/11: no numbers. After verification (gates, completeness, B–F): one main page "GAE among other
models" (table: family · model · F1 · sensitivity · FP/day, per-case means) + one backup with curves and the
complementarity plot. kNN is not part of it (R88).

## 7 · Honest limits to state

One seed; 24 cases / 23 subjects; feature-level input (not raw EEG); supervised k calibrated on in-sample training
cases (label-free rule, optimistic scores there) — read with the curve (C), which needs no k; CNN without temporal
context (same single window as SVM and trees, by design).

## 9 · Change log

| when | change | reason | seen results? |
|---|---|---|---|
| 02/11 22:30 | rev 1 created | R93 | no |
| 02/11 22:20+ | Kaggle only; laptop free | author | no |
| 03/11 01:00 | **rev 2**: 4-fold CV (24 cases) instead of the thesis split; five models one per family (GAE, Isolation Forest, linear SVM, gradient-boosted trees, 1-D CNN); graph-encoder variants, autoencoder baselines, latency and reconstruction-error analyses dropped; no early stopping; pre-registered analysis A–F | author 03/11 00:39 (mentor: ordinary single models, no ablations; fewer models; more patients in the comparison) | no (nothing was run under rev 1) |
| 03/11 08:00 | Gate GG: k tolerance 1e-9 → **1e-6 relative**; tp/fp (48 rows) and the 185 caught flags stay exact. Notebook A re-run in full; notebook B (CNN) kept (its run never calls GG; its code differs only in this line) | first Kaggle run stopped at GG on k alone (rel. 1.4e-8 – 9.3e-8: numpy 2.1.3 / sklearn 1.6.1 on Kaggle vs 2.4.4 / 1.8.0 on the laptop); budgets top identical (max diff 0), tp/fp 48/48 and caught 185/185 identical. The tolerance was set too tight in chat D11-M | GAE row (= committed CV) and the CNN row were seen; Isolation Forest, SVM and trees **not run yet**; the change concerns a float tolerance only, no model, input, rule or reading |
| 03/11 22:30 | Post-hoc (after reading the registered A–F): paired subject bootstrap at the fixed 0.005 point and on window AUROC (`src/model_cmp_posthoc.py`, `results/model_cmp/posthoc_bootstrap.csv`); two figures (`src/model_cmp_figures.py`). Labelled post-hoc; never a headline | own-point budgets differ by model (supervised 34–35 FP/day, cap binds 4–9 / 24 cases vs 1 for the GAE), so own-point F1 mixes model and budget | yes — added after the registered analysis was read; the registered reading (§4) is unchanged |
| 04/11 07:50 | **Sixth model: MLP autoencoder** = the GAE with message passing removed (encoder Linear 30→64→16 per channel, same decoders and loss, 3,964 parameters), same fold recipe as the GAE (clean training windows, fold f7 constants, Adam 1e-3, cosine, batch 32, 200 epochs, last kept, seed 42, no early stopping), same chain. Two GPU notebooks (folds 1–2, 3–4); gates D0, G-mini, G2 (loss falls), training-window count = GAE fold model. **Reading fixed now:** 'the graph structure adds detection value' only if the CI of ΔF1 (GAE − MLP-AE, paired subject bootstrap, own point) excludes 0; otherwise 'no detection gain from message passing shown; the graph's value is in what it shows (R91)'. Same analyses A–F | the only missing comparison for 'why a graph?': a deep label-free autoencoder identical except for the graph (author 04/11 07:47) | yes — the five-model results were read; no rule or model of those five changes |
