# DESIGN_PC8 — decomposition of the 7 absolute features (Track F, chat D37-F, 21/11/2026)

Approved by the author 21/11 12:42 (arms as below; the third arm read as "the 7 absolute features only", the reading
chosen by the chat at the author's request). Written and committed **before any run**; nothing below is a result.

## 1 · Question and why it matters

PC1 (`results/eureka_d32f/pc1/`) removed the seven absolute, amplitude-preserving features from the GAE's node input
(arm 10a) and lost most of the detection; with the training variance included (PC7 Q5, 16 R0 seeds) 10a − R0 on
development is sensitivity −0.290 [−0.415, −0.174], F1 −0.164, FP/day +27.1. The seven features are, in this order
(`src/retrain/train_gae_v2.py`, `c1b_build_trainset.py`): log band power delta, theta, alpha, beta, gamma (input columns
23–27, target 5–9), log line length (28 / 10) and signed-log kurtosis (29 / 11), each standardised with the training
constants and clipped. Five log band powers and line length scale with the signal amplitude; kurtosis does not (a shape
statistic). So each partial removal below still leaves an amplitude carrier in the input.

The council may ask which of the seven features carry the detection, and whether amplitude alone is enough. PC8 answers
with the thesis model and recipe only.

- **Q1** Which part of the seven features carries the detection: the log band powers, or line length + kurtosis?
- **Q2** Do the seven features alone (no connectivity row, no relative band powers in the node input; the graph still
  propagates and is still reconstructed) keep the detection of the full input?

## 2 · Arms (one factor each; retrained)

| arm | node input kept | reconstruction target kept | parameters (computed) | type |
|---|---|---|---|---|
| **R0** (control) | all 30 | all 12 | 3,964 | PC7's 16 new seeds (rows read, not retrained) |
| **P8a** | 25: without the 5 log band powers (23–27) | 7: without 5–9 | 3,479 | leave one group out |
| **P8b** | 28: without log line length + kurtosis (28–29) | 10: without 10–11 | 3,770 | leave one group out |
| **P8c** | 7: the absolute features only (23–29) | 7: the absolute features (5–11) | 2,327 | leave one group in |
| 10a (PC1, reference) | 23: without the 7 (23–29) | 5 | 3,285 | leave the whole group out |

A column removed from the input is removed from the reconstruction target too (as PC1). Parameters = 64·in + 64 +
64·16 + 16 + 16·32 + 32 + 32·out + out (two GCN layers 64 → 16, decoder 16 → 32 → out). Everything else is PC1's recipe:
the 12 training patients' clean windows of the defense-time data (270,190 windows; validation loss on the 3 validation
patients), V5's feature constants, Adam 1e-3, cosine, batch 32, **200 epochs, last epoch**, `eur_abl.train_masked`
(= `f1_core.train` with every column, gate G-pc1vec); the arm's columns are cut from the same 30-value node input at
training and at inference; then V5's chain unchanged (per-channel Ledoit–Wolf Mahalanobis → members → drift →
ensemble → smoothing 5 → label-free budget with **k recalibrated per arm on seed 42** → change point localizer).

**Seeds:** 42, 1, 2, 3, 4, 5, 6, 7 per arm (8; seed 42 carries k, as V5's rule). PC7 Q3: with 8 seeds per arm against
16 control seeds the smallest detectable development sensitivity difference is ≈ 0.024 (computed from PC7's variance
components, 95 %; a lower bound — the arm × patient interaction adds variance: PC1's 10b interval was ±0.034).

**Control R0 = the 16 new seeds of PC7** (`results/eureka_d34f/pc7_A`, `pc7_B`, seeds 4–19, both Kaggle machine types),
read from their committed rows: the same code, data, chain and k (R0's k of seed 42 = PC1's). Each PC8 notebook rescored
V0 and PC1's R0 checkpoint of seed 42 to prove that its chain is that chain (gates below); R0 is not retrained.

## 3 · Hypotheses (fixed before the run)

- **H8a / H8b (redundancy):** the amplitude information is held by both groups, so each partial removal loses much less
  than 10a: development P8a − R0 and P8b − R0 in sensitivity closer to 0 than 10a − R0 (share of 10a's loss well below 1).
- **H8c (sufficiency):** the seven features alone keep most of the full input's detection: P8c − R0 in sensitivity
  much closer to 0 than 10a − R0.
- No pass / fail threshold; the differences with their intervals are reported and the author decides how to use them.
  **No arm can replace V5** in the Euréka files (the deliverables keep V5; results serve the Q&A of 11/12), so R214 is not
  evaluated; an arm better than R0 on development is logged for after 11/12.

## 4 · Reading rule (written before the run; `src/eur_pc8_read.py`, committed first)

All metrics: per-patient mean, own label-free point, after the change point localizer (as PC1 / PC7). A seed's value on
a set = the mean over that set's patients. Development (15 patients) primary; test, chb24, Siena descriptive.

- **R1** arm − R0 for P8a, P8b, P8c (and 10a with PC1's 4 seeds, for reference) per set and metric (sensitivity, F1,
  FP/day): the two-level bootstrap of PC7 Q5 (patient units, chb01 + chb21 one unit; seeds resampled within each group;
  B = 10,000; the patient draw and the control-seed draw shared by every arm in a draw). **Wording** (development):
  sensitivity / F1 "loses" if the interval is below 0, "gains" if above, else "no measurable difference (smallest
  detectable ≈ 0.024)"; FP/day "more" / "fewer false alarms" / "no measurable difference".
- **R2** share of 10a's loss = (arm − R0) / (10a − R0) on development, with the interval of the ratio over the same
  draws (descriptive).
- **R3** per seed: validation and training loss, parameters, ms per step, the machine (CPU model, G-pc7rep), development
  and test metrics.
- **R4** events at each budget (CPD stage; per-seed means of the set sums): events, seizures found, false alarms,
  seconds per event, flagged time, windows flagged — to see whether a loss comes with fragmentation, as for 10a.
- Means ± SD over seeds per set and variant (V0, R0, 10a, P8a–c).

**Reader gates (STOP):** M-gates (every run gate PASS; G-pc7plat / G-pc7rep recorded), M0 (V0 rows identical in the
three PC8 runs, the two control runs and pc1_r0), M1 (R0 seed-42 rows of every PC8 run = pc1_r0's; R0 k of every PC8 run
and control run = pc1_r0's), M2 (completeness), M4 (10a − R0 development point estimates = PC7's `q5.csv`), one run per
arm.

## 5 · Runs and gates

| notebook | arm | seeds trained | reused | runtime (computed) |
|---|---|---|---|---|
| `EUR_PC8_a` | P8a | 42, 1–7 (two chunks of 4) | R0 seed 42 (PC1) | ≈ 5.5–8.2 h |
| `EUR_PC8_b` | P8b | 42, 1–7 | R0 seed 42 | ≈ 5.5–8.2 h |
| `EUR_PC8_c` | P8c | 42, 1–7 | R0 seed 42 | ≈ 5.5–8.2 h |

Runtime from PC7's measured 5.94 h (machine type A, 5.1–5.7 ms per step) and 8.39 h (type B, 7.9–8.1 ms per step) for 8
trainings + scoring of 4 V0 + 12 R0 seeds; PC8 scores fewer seeds (4 V0 + 1 R0 + 8 arm), and the arms have no more
columns than R0. Three verified Kaggle accounts in parallel (Internet: clone, pip).

| gate | what it checks | on failure |
|---|---|---|
| record gates | G-self, G-data, G-pc1const, G-pc1vec, SMOKE, R1.0-dev / -test, GE, G-k, G-kv0, G-D0, G-enc, G-x0, G-eng, G-worker | STOP |
| **G-pc8cols** | the dropped columns of each arm, by name, = §2 (input and target); seed 42 among the arm's seeds | STOP |
| G-pc7reuse | PC1's R0 seed-42 checkpoint copied, sha256 recorded, json columns / epochs / G2 | STOP |
| G-pc7plat | library versions = PC1 | recorded |
| G-pc7rep | R0 seed 42, 1 epoch: epoch-1 loss = PC1's log exactly (PASS = the arithmetic of PC1's machine) | recorded |
| G-guard | the second chunk only if elapsed + chunk + 4,500 s ≤ 11.3 h; skipped seeds listed | recorded |
| G-pc7k | R0's k = PC1's (relative ≤ 1e-6) | STOP |
| G-pc7r0 | R0 seed-42 rows = PC1's exactly | STOP |
| run_meta | CPU model (`/proc/cpuinfo`), seeds and reuse of every arm | — |

**Limitation (stated):** each arm trains on the machine its notebook gets, so arm and machine type are confounded within
an arm; the control holds both machine types, and PC7's machine check found no difference between them (smallest
permutation p 0.098). The CPU model and G-pc7rep of each run are reported beside the result.

## 6 · Code

- `src/eur_abl.py` (owner D37-F): arms P8a–P8c in `PC1_ARMS` and `VARIANTS`; per-arm seeds and reuse
  (`EUR_ARM_SEEDS_<ARM>`, `EUR_ARM_REUSE_<ARM>`; unset = PC1 / PC7 behaviour); gate G-pc8cols; the CPU model in
  `run_meta`.
- `src/eur_make_notebooks.py --only EUR_PC8` → `EUR_PC8_a`, `_b`, `_c` (clone, sha assert of every module, worker-sha
  gate).
- `src/eur_pc8_read.py` (new): the reading of §4 → `results/eureka_d37f/pc8/`.
- `src/eur_pc8_synthetic_test.py` (new): the three notebooks end to end on synthetic data (2 epochs, 3 seeds per arm, two
  chunks), with a PC1-like reference and PC7-like control runs, the reader, non-circular checks and negative paths; the
  PC1 and PC7 synthetic tests re-run on the changed `eur_abl.py` (behaviour unchanged). All from a frozen copy of the
  repository.

## 7 · Literature

- Au, Q., Herbinger, J., Stachl, C., Bischl, B., & Casalicchio, G. (2022). Grouped feature importance and combined
  features effect plot. *Data Mining and Knowledge Discovery, 36*, 1401–1450. https://doi.org/10.1007/s10618-022-00840-5
  — group importance by refitting: leave one group out (LOGO) and leave one group in (LOGI); with correlated groups the
  two answer different questions, so both are needed. Applied: P8a / P8b (LOGO within the seven), P8c (LOGI), 10a (LOGO of
  the whole group).
- Hooker, G., Mentch, L., & Zhou, S. (2021). Unrestricted permutation forces extrapolation: variable importance requires
  at least one more model. *Statistics and Computing, 31*, 82. https://doi.org/10.1007/s11222-021-10057-z — permuting
  correlated features misleads; refit without the features instead. Applied: every arm is retrained.
- Williamson, B. D., Gilbert, P. B., Simon, N. R., & Carone, M. (2023). A general framework for inference on
  algorithm-agnostic variable importance. *Journal of the American Statistical Association, 118*(543), 1645–1658.
  https://doi.org/10.1080/01621459.2021.2003200 — importance as the loss of predictiveness of the refitted model without the
  features, with interval estimates. Applied: arm − R0 with a bootstrap interval.
- Hooker, S., Erhan, D., Kindermans, P.-J., & Kim, B. (2019). A benchmark for interpretability methods in deep neural
  networks. *NeurIPS 32*. arXiv:1806.10758 — remove and retrain, repeated over seeds (as PC1).
- Bouthillier, X., et al. (2021). Accounting for variance in machine learning benchmarks. *MLSys 3*.
  https://doi.org/10.48550/arXiv.2103.03098 — compare under the same sources of variation; the training variance enters
  the interval (two-level bootstrap, PC7).

## 8 · What this design does not do

No new feature, no change of the architecture or the chain; no seed ensemble; no single-feature arms (21 combinations of
the seven would be needed for a full decomposition; the two groups are the frequency-domain and the time-domain features
of the seven, as the PC1 reading named them). The
deliverables keep V5's numbers; the result serves the Q&A of 11/12.
