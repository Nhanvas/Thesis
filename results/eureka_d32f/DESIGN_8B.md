# D32-F — ablation 8b on the V5 model: no encoder (design, 20/11/2026; approved by the author 13:04)

*Written before any 8b output. Chat D32-F, Track F (Euréka support). Builds on `results/eureka_d31f/STEP1_DESIGN.md`
(the suite EUR_ABL, approved 19/11 20:35); everything not stated here is as in that design (§2.2–§2.5).*

## 0 · Why this experiment, for Euréka

- **Purpose of Track F until 11/12:** give Track C verified evidence for the claims of the deliverables and the
  answers of the Q&A (criterion K3: the novelty proven, not only argued), under R214; no change of the system's
  direction (author 20/11 12:58: the GAE stays; optimisations only on the GAE basis).
- **The question the council will ask** (`EUREKA_PLAN.md` §6, question 1): the AE without message passing and K-means
  did better than the GAE in the seven-model comparison (V5 Section 3.4) — what does the GAE contribute? The
  seven-model comparison answers it outside V5's chain (4-fold CV, seed 42, each model at its own point). The suite
  EUR_ABL measured V5's own components (distance 1a / 1b, reference 4a–4c, drift 2a / 2b, members, smoothing, budget,
  boundaries, edges at inference 8a) but not the learned representation itself.
- **8b closes that gap inside V5:** the same chain, the same patients, the same seeds and budget rule, with the
  learned encoder removed. It replaces option O3 (GAE + K-means rank fusion), which the author did not approve
  (20/11 12:58): K-means had been picked after the seven-model results, which include the test patients, and a fusion
  would answer "what do two scorers give together", not "what does the GAE give" (plan §14.15).

## 1 · Literature (read 20/11)

- Rippel, Mertens & Merhof (2021), *Modeling the distribution of normal data in pre-trained deep features for anomaly
  detection*, ICPR 2020, 6726–6733, DOI 10.1109/ICPR48806.2021.9412109 (arXiv 2005.14140): a multivariate Gaussian with
  the Mahalanobis distance fitted on normal data; its quality depends on the representation it is fitted on — the
  representation is the factor that ablations isolate.
- Defard et al. (2021), *PaDiM*, ICPR Workshops, LNCS 12664, 475–489, DOI 10.1007/978-3-030-68799-1_35: the same
  construction per location (here: per channel) — the design of V5's distance.
- Han et al. (2022), *ADBench: Anomaly Detection Benchmark*, NeurIPS 35 (Datasets and Benchmarks), arXiv 2206.09426:
  30 algorithms on 57 datasets; no unsupervised algorithm was statistically better than the others, deep methods
  included — a learned representation is not better by default and must be shown by an ablation.
- Bouman, Bukhsh & Heskes (2024), *Unsupervised anomaly detection algorithms on real-world data: how many do we
  need?*, JMLR 25, https://jmlr.org/papers/v25/23-0570.html: a benchmark of unsupervised detectors on real-world data (already cited for F-A1.6).
- Tang et al. (2023), *Modeling multivariate biosignals with graph neural networks and structured state space models*,
  CHIL 2023, PMLR 209:50–71 (arXiv 2211.11176): EEG seizure detection with an ablation that removes the graph layers — the
  standard way to show what a graph component adds.
- Peer-reviewed work that removes the encoder of a graph autoencoder inside an EEG anomaly-scoring chain was not found;
  8b follows the generic component-ablation practice above.

## 2 · Variant

| ID | change from V5 | everything else |
|---|---|---|
| **8b** | per channel, LedoitWolf Mahalanobis distance on the **30-value node input** the encoder receives (normalised adjacency row 18 + relative band powers 5 + the 7 clipped absolute features with the checkpoint's constants), instead of the 16-value latent | record code: robust z, members 6th / 9th / 12th + mean, ±15-min drift correction, percentile ensemble, smoothing 5, budget clip(q, 0.5 %, 2 %) with **k recalibrated** by V5's rule (development, seed 42), merge, kernel CPD |

- Code: `src/eur_abl.py` gains `node_x` (the record construction of the encoder input, line for line) and the variant
  8b; `encode` builds its graphs from `node_x`, so the existing gate **G-enc** (the encoder with the window graph =
  `p2_dump_seeds23.run_model`, exactly) also proves that `node_x` is the record input. The 4 seeds differ only through
  the checkpoint constants of the 7 absolute features (reported).
- What 8b removes: the learned encoder (two graph convolutions and the compression to 16 values). What it keeps: the
  connectivity row as input values. So 8b is "no encoder", not "no graph".
- The run: notebook `EUR_ABL8B` = EUR_ABL with `EUR_VARIANTS=V0,8b`, `EUR_TAG=abl8b`; V0 is recomputed in the same run
  (gates R1.0, GE, G-k, G-kv0, G-D0, G-x0, G-eng, G-enc, G-worker as in EUR_ABL; the 4a reference pass is skipped).

## 3 · Hypotheses and rules (fixed before the run)

- **H8b (prediction):** inside V5's chain the latent adds no measurable detection gain over its own input —
  development Δsensitivity (8b − V0) with an interval that includes 0 or favours 8b, and FP/day not higher. Basis: K-means
  on the same input matched or beat the GAE (F-A1.6, six partitions); message passing added false alarms (F-A1.4).
- **Alternative:** the latent helps (Δsensitivity interval below 0), e.g. because the 30-value input has near-constant
  columns and the 16-value latent gives a better-conditioned covariance.
- **Readings:** as `STEP1_DESIGN.md` §2.3 — primary: development, own label-free point after the localizer, 4-seed
  per-patient means, paired patient bootstrap of 8b − V0 (B = 10,000, rng 0, chb01 + chb21 one unit); secondary: fixed
  0.5 % and matched FP/day 20 / 28.7; descriptive: test, chb24, Siena; onset / offset errors. Aggregate:
  `src/eur_abl_aggregate.py`, unchanged (committed 19/11).
- **R214:** 8b is an **ablation only**. It is never a replacement candidate, whatever its numbers (author 20/11: the
  system keeps the GAE); if the aggregate prints it as a "candidate", that line is not a decision.
- **Wording limits, written before the result:**
  - if 8b ≈ or > V0: "inside this chain, the learned latent of the GAE adds no measurable detection gain over its input;
    the gains come from the scoring framework (per-channel Mahalanobis on the patient's own recording, drift correction,
    label-free budget)" — consistent with V5 Sections 3.4 and 4.3.5; never "the GAE is useless" outside this chain;
  - if 8b < V0: "removing the encoder lowers sensitivity by X [CI] on development; the GAE latent contributes inside the
    chain";
  - the development reading includes the 12 training patients (optimistic for V0: their windows trained the encoder).

## 4 · Cost and order

- Synthetic test (container) before delivery: the notebook end to end with V0 + 8b, every gate PASS; `node_x` equals an
  independent float32 construction; 8b distances = LedoitWolf on that input; the aggregate A1 and T2 with the 8b row; an
  edited module stops the notebook.
- Kaggle: one verified account, ≈ 0.5–0.9 h (computed from EUR_ABL's measured 0.868 h for 17 variants: V0's distances
  and scoring dominate); the smoke writes the projection. Reading and hand-off the same day, before the freeze (22/11
  evening).
