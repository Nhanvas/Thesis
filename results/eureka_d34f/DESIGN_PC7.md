# DESIGN_PC7 — seed variance of the training recipe (Track F, chat D34-F, 21/11/2026)

Approved by the author 21/11 01:26 ("duyệt"; 20 seeds, two notebooks on verified accounts 1–2, the reading rule
below). Written and committed **before any run**; nothing below is a result.

## 1 · Question and why it matters

PC1 (`results/eureka_d32f/pc1/`) retrained the GAE with the thesis recipe on Kaggle CPU (arm R0, seeds 42 / 1 / 2 / 3).
The four validation losses were equal to within 0.6 % (0.02121–0.02133), yet seed 2 found clearly fewer seizures on
development (per-patient mean sensitivity 0.680 against 0.817–0.841; `pc1/diag/DIAG_PC1.md` §3), and R0's test mean
was 0.494 against V5's 0.567. V5's "± over seeds" describes only its own four trainings. Three questions follow:

- **Q1** How much do the detection results vary between trainings of the same recipe on the same platform, and how much
  of it is shared by every patient (a seed effect) rather than patient-specific?
- **Q2** Does the validation reconstruction loss (the label-free rule that chose the demo model, R146) pick the better
  detector?
- **Q3** How many seeds does a retraining comparison (PC1, PC8, PC6) need to detect a given difference?

Descriptive, from the same runs: **Q4** where V5's four trainings lie in the distribution of the recipe; **Q5** the PC1
reading with the training variance included (plan §14 row 83); **Q6** whether a per-seed k (instead of the k of seed 42)
changes the seed variation (diagnosis of the candidate explanation "k fitted on seed 42 does not suit the other seeds'
latent scale", instructions §1 item 18).

## 2 · Runs

R0 = PC1's arm R0 exactly: the 12 training patients' clean windows of the record data (270,190 windows), V5's feature
constants, `eur_abl.train_masked` with every column (= `f1_core.train`, gate G-pc1vec), 200 epochs, last epoch, Adam 1e-3,
cosine, batch 32; then V5's chain (per-channel Ledoit–Wolf Mahalanobis → members → drift → ensemble → smoothing → budget →
localizer) on every set.

| notebook | account | seeds trained (200 epochs) | seeds reused (committed PC1 checkpoints, not retrained) |
|---|---|---|---|
| `EUR_PC7_A` | verified 1 | 4, 5, 6, 7, 8, 9, 10, 11 | 42, 1, 2, 3 |
| `EUR_PC7_B` | verified 2 | 12, 13, 14, 15, 16, 17, 18, 19 | 42, 1, 2, 3 |

Total R0 seeds: 4 (PC1) + 16 = **20**. The reused checkpoints (`results/eureka_d32f/pc1_r0/models/R0/`) are scored again
in both notebooks: this reproduces PC1's R0 rows (gate G-pc7r0) and gives seed 42 for k.

**Variants scored:** V0 (the four V5 checkpoints; record gates and the M0 check), **R0** (k of seed 42 for every seed —
V5's rule, as in PC1; primary) and **R0s** (the same latents, k recalibrated on each seed's own development scores by the
same label-free rule; secondary, Q6).

**Training order and session guard.** Trainings run 4 in parallel (Kaggle CPU, 4 cores): seeds 1–4 of the notebook's
list first, then the other four only if `elapsed + duration of the first chunk + 4,500 s (scoring reserve) ≤ 11.3 h`.
Seeds not trained are listed in gate G-guard and scored as not available; the seed list is fixed here, so a skipped
chunk depends on machine speed only, not on any result. Measured basis: 8,700 s (PC1 R0) to 14,860 s (PC1 10b) per chunk
of 4; scoring of V0 + 12 R0 seeds × 2 variants ≈ 0.7–1.1 h (computed from PC1's measured prep / score phases).
**Runtime ≈ 5.5–9.4 h per notebook (computed).**

## 3 · Gates

| gate | what it checks | on failure |
|---|---|---|
| record gates | G-self, G-data, G-pc1const, G-pc1vec, SMOKE, R1.0-dev / -test, GE, G-k, G-kv0, G-D0, G-enc, G-x0, G-eng, G-worker (as PC1) | STOP |
| **G-pc7reuse** | the four reused checkpoints and jsons are copied from the clone; their sha256 recorded; json = 30 / 12 columns, 200 epochs | STOP |
| **G-pc7plat** | python, numpy, scipy, sklearn, pandas, torch, torch_geometric versions = `pc1_r0/run_meta.json` | recorded, no stop |
| **G-pc7rep** | R0 seed 42 retrained for 1 epoch on the full training data: epoch-1 training loss = the committed `training_log_clean_seed42.csv` value exactly | recorded, no stop |
| **G-pc7k** | R0's k (seed 42) = `pc1_r0/k.csv` R0 (relative ≤ 1e-6, the record tolerance) | STOP |
| **G-pc7r0** | the R0 rows of seeds 42 / 1 / 2 / 3 (per_subject and errors, as sorted row sets after the CSV round trip) = `pc1_r0` exactly | STOP |
| G-guard | which seeds were trained; the guard's numbers | recorded |
| reader M0 / M1 | V0 rows identical in pc7_A, pc7_B and pc1_r0; reused-seed R0 rows identical in pc7_A and pc7_B | STOP |

**Pooling rule (written before the run).** If G-pc7plat and G-pc7rep PASS in both notebooks, the 20 seeds are pooled
(same platform, bit-identical training path). Otherwise the primary reading uses the 16 new seeds only and the four PC1
seeds are shown beside them, descriptively.

## 4 · Reading rule (written before the run; no pass / fail threshold)

All metrics: per-patient mean, own label-free point, after the change point localizer (as PC1). A seed's value on a set
= the mean over that set's patients of that seed's per-patient value. Development (15 patients) primary; test, chb24,
Siena descriptive.

- **Q1** For R0: mean, SD with its 95 % χ² interval, min, max and quartiles over the N seeds, per set and metric
  (sensitivity, F1, FP/day). Variance components on development by the two-way ANOVA without replication (patient ×
  seed; method of moments): σ²_seed = max(0, (MS_seed − MS_res) / P), σ²_res = MS_res, σ²_patient; reported with the seed
  share of the non-patient variance. Each seed's training loss, validation loss and development metrics in one table.
- **Q2** Spearman ρ between the final validation loss and development sensitivity (and F1) over the N seeds, 95 %
  interval by bootstrap over seeds (B = 10,000). Selection gain: over every subset of 4 seeds, the development value of
  the subset's lowest-validation-loss seed minus the subset mean; reported as the mean gain (interval by bootstrap over
  seeds, B = 2,000) and the share of subsets where the chosen seed is at or above the subset median. Training loss the
  same way (secondary). **Wording:** "the validation loss picks the better detector" only if ρ < 0 with its interval
  excluding 0 **and** the mean gain's interval above 0; otherwise "no evidence that the validation loss picks the
  better detector" (with N = 20, |ρ| ≈ 0.44 is the smallest correlation whose interval can exclude 0 — computed,
  Fisher z).
- **Q3** Minimal detectable difference of an arm − control comparison with n seeds per arm on development:
  (a) empirical — the pooled R0 seeds split at random into two disjoint groups of n (n = 4, 8, 10; 2,000 splits), each
  combined with a patient-bootstrap draw (chb01 + chb21 one unit); the half-width of the central 95 % of the null
  difference; (b) from the components — MDD95(n) = 1.96 · √(2σ²_seed / n + 2σ²_res / (nP)) and MDD80 with 2.80 instead
  of 1.96, for n = 4, 8, 12, 20. Both are lower bounds for a real arm (an arm × patient interaction adds variance);
  stated as such.
- **Q4** V5's 4-seed mean against the distribution of all 4-seed means of R0 (every subset of 4): its percentile, per
  set and metric. Descriptive: V5 was trained on another machine and library version (PC1 design §2).
- **Q5** PC1 re-read: 10a − R0 and 10b − R0 (the PC1 arms' 4 seeds against the pooled R0 seeds) with a two-level
  bootstrap (patient units and, within each arm, seeds resampled with replacement; B = 10,000); development primary.
  Compared with PC1's patient-only intervals.
- **Q6** R0s against R0: per-seed development sensitivity and the SD over seeds, side by side; descriptive (no
  mechanism claim beyond the numbers).

The hand-off to `TRACKS_PROGRESS.md` gives Q1's SD and components, Q2's ρ and wording, Q3's MDD table and Q4's
percentile, with these wording limits: development includes the 12 training patients; one platform (Kaggle CPU); V5 is
from another platform.

## 5 · Code

- `src/eur_abl.py` (owner D34-F): arm seeds separated from the four V0 seeds (`EUR_ARM_SEEDS`; default = the four, so
  PC1 runs unchanged); reuse of committed checkpoints (`EUR_ARM_REUSE`, `EUR_PC7_REF`); an arm's node input uses the
  constants of its own checkpoint json (equal to V5's, gate G-pc1const); variant R0s with per-seed k; the PC7 gates and
  the session guard.
- `src/eur_make_notebooks.py --only EUR_PC7` → `EUR_PC7_A`, `EUR_PC7_B` (clone + sha assert of every module).
- `src/eur_pc7_read.py` (new): M0 / M1 / completeness, pooling rule, Q1–Q6 → `results/eureka_d34f/pc7/`.
- `src/eur_pc7_synthetic_test.py` (new): both notebooks end to end on synthetic data (2 epochs, few seeds), the reader,
  non-circular checks and negative paths.
- `src/eur_abl_aggregate.py` is not used by the PC7 reading (its A1 gate assumes four seeds per variant) and is
  unchanged.

## 6 · Literature (peer-reviewed; no code repository applies)

- Bouthillier, X., et al. (2021). Accounting for variance in machine learning benchmarks. *MLSys 3*.
  https://doi.org/10.48550/arXiv.2103.03098 — initialisation and data order change results markedly; compare under the
  same sources of variation.
- Summers, C., & Dinneen, M. J. (2021). Nondeterminism and instability in neural network optimization. *ICML*, PMLR 139,
  9913–9922. https://proceedings.mlr.press/v139/summers21a.html — every source of nondeterminism has a similar effect on
  model diversity; training instability is the cause.
- Borra, D., Magosso, E., & Ravanelli, M. (2025). A protocol for trustworthy EEG decoding with neural networks. *Neural
  Networks, 182*, 106847. https://doi.org/10.1016/j.neunet.2024.106847 — EEG decoding is sensitive to initialisation;
  their protocol trains and evaluates with 10 random initialisations.
- Ma, M. Q., Zhao, Y., Zhang, X., & Akoglu, L. (2023). The need for unsupervised outlier model selection: A review and
  evaluation of internal evaluation strategies. *SIGKDD Explorations, 25*(1), 19–35. https://doi.org/10.1145/3606274.3606277
  — label-free (internal) criteria select outlier-detection models poorly (basis of Q2).
- Ding, X., Zhao, L., & Akoglu, L. (2022). Hyperparameter sensitivity in deep outlier detection: Analysis and a scalable
  hyper-ensemble solution. *NeurIPS 35*. https://doi.org/10.48550/arXiv.2206.07647 — deep outlier detectors are sensitive
  to their training configuration.
- Agarwal, R., et al. (2021). Deep reinforcement learning at the edge of the statistical precipice. *NeurIPS 34*.
  https://doi.org/10.48550/arXiv.2108.13264 — with few runs, report interval estimates over runs (stratified bootstrap).

## 7 · What this design does not do

No change of the recipe, the features or the chain; no seed ensemble (not approved, R146); R0s is a diagnosis, not a
candidate system. The deliverables keep V5's numbers (R214); the result serves the Q&A of 11/12 and the reading of PC8 /
PC6, which will use the pooled R0 seeds as their same-platform control.
