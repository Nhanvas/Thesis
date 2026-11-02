# MODEL_COMPARISON_PLAN — where the GAE stands among other models (rev 1, 2026-11-02 22:30, chat D10-plan)

*Repo: `docs/MODEL_COMPARISON_PLAN.md` + project file. The only experiment running in parallel with the rehearsal prep
(board rev 40, R93). Fixed before any run; any change is logged in §9 with its reason **before** results are seen.*

---

## 0 · Purpose (why we compare at all)

The committee will ask **"why a graph autoencoder?"** and **"why not SVM / trees / CNN / RNN / Transformer / another
GNN?"** (anh Trí 02/11). This comparison answers three questions, and **only** these:

| # | question | compared |
|---|---|---|
| **Q1** | Is a **graph** model the right family for this signal, compared with non-graph deep models that see the same windows? | graph autoencoders vs non-graph autoencoders (MLP, LSTM, TCN, Transformer) |
| **Q2** | Does the **choice of graph layer** matter, or is the simplest (GCN) enough? | GCN vs GAT, GraphSAGE, GIN, ChebNet |
| **Q3** | What would **labels** buy? (= "why not SVM or trees") | label-free GAE vs supervised classifiers (SVM, Random Forest, gradient-boosted trees) |

**Not the purpose:** picking a new system before the defense, or beating the GAE. **The thesis system does not change
before the defense** whatever the outcome (R93). No ensembles, no combined models — **single models only** (R89).

## 1 · Fixed protocol (same for every model)

- **Split:** the thesis split — training 12 patients, validation 3, test 8 (76 seizures). **No cross-validation** here
  (the GAE's 24-case CV stays the only CV, author 02/11).
- **Input:** the cached per-window data already used by the GAE: `data/trainset_v2/*.npz`, `data/testset_v2/*.npz`
  (per 4 s window: `adj` 18 × 18 = CAR → wPLI + AEC → top 20 %; `bp5` 18 × 5; `f7` 18 × 7; flags). **No new EEG
  reading tonight** → models on the raw signal (raw-EEG CNN / Transformer) are out of scope (future work, say so).
- **Seed 42 only** for every new model (one seed; label it). The frozen GAE (seed 42) is the reference row.
- **Unsupervised models = "only the encoder changes":** same node input (30 = adjacency row 18 + band powers 5 + f7 7,
  same scaling constants as `src/retrain/train_gae_v2.py`), same training windows (variant of the frozen GAE —
  verify in the code, expected `clean`), same latent size (16 per channel), same decoders and loss
  (inner-product adjacency reconstruction + 0.1 × MLP feature reconstruction of 12 features), same optimiser
  (Adam 1e-3, cosine, batch 32). **Equal training budget for every trained model** (epochs and window subsample fixed
  after the smoke, logged in §9), **including a GCN retrained under that same budget** ("GAE, same budget" row) so the
  budget is not a confound; the frozen 200-epoch GAE is shown as a separate reference row.
- **Scoring of unsupervised models = the frozen chain, unchanged:** per-channel 16-d latent → Ledoit–Wolf Mahalanobis per
  patient per channel → robust z → members 6/9/12 + mean → ±15-min drift → percentile mean → smoothing 5 → per-patient
  budget clip(q_i(k), 0.005, 0.02) with **k calibrated on the 15 development patients for each model by the GAE's rule**
  (median q_i = 0.005) → merge 90 s → kernel CPD → SzCORE (`src/szcore_eval.py`). Reuse `src/v9_e1_baselines.py`
  (`final_scalar_from_D`, `member_mean_z_from_D`, `evaluate_arm`) — the only new input is the per-channel distance D.
- **Supervised models (Q3):** trained on the 12 training patients' labelled windows (seizure vs non-seizure; 4 h
  post-ictal buffer and signal-loss windows excluded), class-weighted; one fixed configuration each, chosen before the
  run; a small setting check on the **3 validation patients only**, never on test. Window input = the 18 × 12 node
  features (band powers + f7) flattened (216). Output probability per window → per-patient percentile → smoothing 5 →
  the same per-patient budget rule (k calibrated on development) → merge 90 s → kernel CPD → SzCORE.
- **Labels never enter an unsupervised model** (except the GAE's existing exclusion of seizure windows from training,
  disclosed).

## 2 · Models (priority order; count chosen for one night)

| prio | family | model | where | answers |
|---|---|---|---|---|
| P1 | supervised | Random Forest · gradient-boosted trees (HistGradientBoosting) · linear SVM (or RBF SVM on a fixed subsample) | Kaggle (CPU notebook) | Q3 |
| P2 | graph AE | GCN (same budget) · **GAT** · **GraphSAGE** · **GIN** · **ChebNet** (K = 3) — encoder in → 64 → 16, two layers | Kaggle (4 accounts in parallel) | Q2, Q1 |
| P3 | non-graph AE | **MLP-AE** (per channel, no message passing) · **LSTM-AE** and **TCN-AE** per channel over the last 8 windows (32 s, causal) | Kaggle | Q1 |
| P4 (only if time) | non-graph AE | Transformer-AE per channel (same sequence) | Kaggle | Q1 |
| out | — | raw-signal CNN / Transformer; supervised GNNs; ensembles | — | future / not a question here |

If the smoke shows the night is too short: run P1 + GCN (same budget) + GAT + GIN + MLP-AE; drop the rest and say so.

## 3 · Gates (stop on any mismatch)

1. **Chain gate:** the frozen GAE's latent through the reused chain reproduces the committed test counts
   (`results/e22_test_oneshot/`, `results/e23_test_look7/` seed 42, tp and fp exactly).
2. **Training gate:** each new model's training loss falls and its validation loss is finite; a model that does not
   train is reported as "did not train", never tuned on test.
3. **Smoke:** chb01 + one test patient end-to-end for one model of each family; measured runtime → budget fixed (§9).

## 4 · Metrics and reading

- Per model: **per-patient mean** sensitivity, precision, F1, FP/day at its **own label-free point** (R72); per-patient
  window AUROC (mean); the per-patient sensitivity–FP/day curve (detector stage, same budget grid for all).
- **Paired patient bootstrap** (B = 10,000, 8 test patients) of F1: each model − frozen GAE, and each model − GAE
  (same budget).
- **Reading (fixed now):**
  - Q2: "the graph layer does not matter" if every GNN's F1 difference vs GCN (same budget) has a CI containing 0.
  - Q1: report graph AEs vs non-graph AEs (mean F1 and CIs); no threshold — 8 test patients, one seed.
  - Q3: report the supervised − GAE gap with its CI; the supervised models need labels of other patients — outside
    the registered unsupervised problem; they are a reference ceiling, never the system.
- One seed and 8 patients: every statement says "on the 8 test patients, one seed".

## 5 · Outputs

`results/model_cmp/` (committed): `per_subject.csv` (model, subject, tp, fp, n_ref, nonict_h, stage), `summary.csv`
(per-patient means), `curves.csv`, `paired_bootstrap.csv`, `training_log.csv` (epochs, windows, runtime per model),
`SUMMARY.md`; checkpoints of new models under `data/models_cmp/` (gitignored); full report
`F:/Study/Thesis/Agent/inbox/MODEL_CMP_REPORT.md`.

## 6 · Running — **Kaggle only; the laptop stays free** (author 02/11 22:20)

The author needs the laptop (Chrome, Canva, the demo) for the rehearsal. Therefore:
- **All training and all scoring run on Kaggle** as committed notebooks ("Save Version → Save & Run All (Commit)"),
  which keep running after the browser tab is closed. Use the 4 Kaggle accounts in parallel (one notebook each).
- Code comes from the public repo (`git clone` inside the notebook, internet on); data from **Kaggle datasets**
  (check first which datasets already exist from the GAE training and the CV — e.g. `trainset_v2`, `testset_v2`,
  `models_v2`; upload only what is missing, through the Kaggle web page).
- **The laptop does no heavy work:** allowed = uploading a dataset in the browser, `git pull`, reading results. Not
  allowed = training, latent dumps, scoring, anything that needs Chrome closed. If a step cannot run on Kaggle, it waits
  until after the rehearsal and the chat says so.
- Each notebook writes its outputs (`per_subject.csv`, `training_log.csv`, …) to `/kaggle/working/`; the author
  downloads them later; the chat checks them and they are committed to `results/model_cmp/`.
- Notebooks are written in full by the chat (no blanks for the author to fill), smoke cell first, then the run, with
  measured runtime printed.
- Order: one notebook for P1 (supervised, CPU), and one per graph encoder for P2, then P3 if accounts are free.

## 7 · Use of the results

- Rehearsal 03/11: **no numbers** (not verified yet) — say what is being compared and why.
- Before the defense: verified rows (gates passed, per-subject table, bootstrap) → one main page "GAE among other
  models" (table: family · model · F1 · sensitivity · FP/day, per-patient) + one backup with curves. Wording follows
  §4; no "best" claim unless the CI says so.

## 8 · Not weaknesses / honest limits to state

One seed per new model; 8 test patients; equal but reduced training budget; feature-level inputs (not raw EEG);
supervised models see other patients' labels.

## 9 · Change log

| when | change | reason | seen results? |
|---|---|---|---|
| 02/11 22:30 | created | R93 | no |
| 02/11 22:20+ | everything runs on Kaggle; the laptop stays free for the rehearsal (§6) | author: the run must not disturb the rehearsal prep | no |
