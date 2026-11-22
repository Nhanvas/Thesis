# DESIGN_PC8B — which input block keeps the detection on unseen patients (Track F, chat D37-F, 22/11/2026)

Approved by the author 22/11 13:22 (arms P8d, P8e; the 11 unseen patients as the primary set). Written and committed
**before any run**; nothing below is a result of PC8b.

## 1 · Question and why it matters

PC8 (`results/eureka_d37f/pc8/T_PC8.md`, read 22/11) found that the GAE retrained on the seven absolute features alone
(arm P8c: node input 7, no connectivity row, no relative band powers) is level with the full input on development
(sensitivity +0.013 [−0.091, +0.114]) but loses on the test patients (−0.176 [−0.374, −0.031], descriptive in PC8). The
development set holds the 12 training patients, on which the encoder was fitted, and the 3 validation patients. A split
by patient group computed after the PC8 reading (descriptive): training 12 P8c 0.815 vs R0 0.767; validation 3 0.817 vs
0.946; test 8 0.347 vs 0.523. **Premise check (computed 22/11, before this design was approved for running, from the
committed PC8 rows with the reader below):** on the 11 patients not used for training (3 validation + 8 test), P8c − R0
sensitivity is −0.163 [−0.323, −0.043] — the gap is measurable on the set this design reads. Siena (an external set) shows
no difference for P8c (−0.015, PC8).

So the extra 23 node-input columns of the full model matter for patients the encoder has not seen. The council may ask
why the node input has 30 values and what the connectivity row and the relative band powers add. PC8b asks which of the
two blocks carries that benefit.

- **Q1** Does adding the connectivity row (18) to the seven absolute features bring the detection on unseen patients back
  to the full input's level?
- **Q2** Does adding the relative band powers (5) to the seven absolute features do so?

## 2 · Arms (retrained; leave one group out of the full input = add one group to P8c)

| arm | node input kept | reconstruction target kept | parameters (computed) | relation |
|---|---|---|---|---|
| **R0** (control) | all 30 | all 12 | 3,964 | PC7's 16 new seeds (rows read, not retrained) |
| **P8d** | 25: connectivity row (0–17) + the 7 absolute (23–29) — without the relative band powers (18–22) | 7: the absolute (5–11) | 3,479 | R0 without the relative band powers = P8c + connectivity row |
| **P8e** | 12: relative band powers (18–22) + the 7 absolute (23–29) — without the connectivity row (0–17) | 12: all | 2,812 | R0 without the connectivity row = P8c + relative band powers |
| P8c (PC8, reference) | 7: the absolute (23–29) | 7 | 2,327 | the PC8 run, rows read |
| 10a (PC1, reference) | 23: without the 7 absolute | 5 | 3,285 | PC1, 4 seeds |

As in PC1 / PC8: a column removed from the input is removed from the reconstruction target if it is a target column (the
connectivity row is not; the graph is still reconstructed by the edge decoder in every arm, and message passing still uses
the record graph). Parameters = 64·in + 64 + 64·16 + 16 + 16·32 + 32 + 32·out + out. Everything else is PC8's recipe:
the 12 training patients' clean windows (270,190 windows; validation loss on the 3 validation patients), V5's feature
constants, Adam 1e-3, cosine, batch 32, **200 epochs, last epoch**, `eur_abl.train_masked`; the arm's columns cut from the
same 30-value node input at training and at inference; then V5's chain unchanged with **k recalibrated per arm on seed
42**.

**Seeds:** 42, 1–7 per arm (8; seed 42 carries k). **Control R0 = the 16 new seeds of PC7** (both machine types), read
from their committed rows; each PC8b notebook rescored V0 and PC1's R0 seed 42 to prove its chain is that chain.
**P8c = the PC8 run `results/eureka_d37f/pc8_c`** (8 seeds, same notebook frame), read from its rows.

## 3 · Hypotheses (fixed before the run)

- **H8d (connectivity):** the connectivity row carries the benefit on unseen patients: P8d − R0 on unseen closer to 0
  than P8c − R0, and P8d − P8c on unseen above 0.
- **H8e (relative band powers):** the relative band powers carry it: same statements for P8e.
- The two are not exclusive (each block may recover part, or the benefit may need both). No pass / fail threshold; the
  differences with their intervals are reported and the author decides how to use them. **No arm can replace V5** in the
  Euréka files (the deliverables keep V5; results serve the Q&A of 11/12), so R214 is not evaluated.
- **Limitation (stated before the run):** the gap that motivates PC8b was seen on the same 11 patients that PC8b reads, so
  PC8b explains a mechanism on these patients; it is not an independent confirmation. Siena (external, never used in
  any choice) is read as the independent descriptive check.

## 4 · Reading rule (written before the run; `src/eur_pc8b_read.py`, committed first)

All metrics: per-patient mean, own label-free point, after the change point localizer (as PC1 / PC7 / PC8). A seed's
value on a set = the mean over that set's patients. **Unseen = the 3 validation + 8 test patients (11) — primary**;
development (15) secondary; validation (3), test (8), chb24 and Siena descriptive. The split is read from
`src/retrain/train_gae_v2.py` (TRAIN, VAL), not typed again.

- **R1** arm − R0 for P8d, P8e (P8c and 10a for reference) per set and metric (sensitivity, F1, FP/day): the two-level
  bootstrap of PC7 Q5 / PC8 (patient units, chb01 + chb21 one unit; seeds resampled within each group; B = 10,000; the
  patient draw and the control-seed draw shared by every arm in a draw). **Wording:** sensitivity / F1 "loses" if the
  interval is below 0, "gains" if above, else "no measurable difference"; FP/day "more" / "fewer false alarms" / "no
  measurable difference".
- **R5** arm − P8c for P8d, P8e (and R0 − P8c): what each block adds to the seven absolute features; same bootstrap with
  P8c as the reference group.
- **R6** share of P8c's gap recovered = (arm − P8c) / (R0 − P8c) in the same draws as R5 (unseen and development;
  descriptive; unstable when R0 − P8c is near 0, so on development it is shown only for completeness).
- **R1m** arm − R0 with the control restricted to the control runs whose G-pc7rep status equals the arm run's (secondary;
  as PC8 §9).
- **R3** per seed: losses, parameters, ms per step, machine; unseen, development and Siena metrics. **R4** events at each
  budget (CPD stage; per-seed means of the set sums) on unseen, development and Siena. Means ± SD over seeds.

**Reader gates (STOP):** M-gates (every gate of the two PC8b runs and the P8c run PASS; G-pc7plat / G-pc7rep recorded),
M0 (V0 rows identical in all runs and pc1_r0), M1 (R0 seed-42 rows and k = pc1_r0's), M2 (completeness), M4 (10a − R0
development = PC7's `q5.csv`), **M5** (development rows = TRAIN + VAL of the training script; test = 8 patients; unseen =
11), **M6** (P8c rows read here = the PC8 reading's P8c rows; float columns to a relative 1e-12 because pandas' default csv
parser is not bit-exact on a round trip — measured on the real rows: ≤ 3.6e-15 in 96 of 1,824 rows), **M7** (P8c − R0
point estimates = the PC8 reading's `r1.csv`), one run per arm, `--p8c` must be the P8c run.

## 5 · Runs and gates

| notebook | arm | seeds trained | reused | inputs (Kaggle slugs) | runtime |
|---|---|---|---|---|---|
| `EUR_PC8_d` | P8d | 42, 1–7 (two chunks of 4) | R0 seed 42 (PC1) | `v9-x3-fold1`, `v9-x3-fold3`, `thesis-r2-external-features` | ≈ 9.5–10 h |
| `EUR_PC8_e` | P8e | 42, 1–7 | R0 seed 42 | `v9-x3-fold1`, `v9-x3-fold3`, `thesis-r2-external-features` | ≈ 9.5–10 h |

Runtime from PC8's measured 9.42–9.56 h (same notebook frame, same machine type; the arms have no more columns than R0).
Two Kaggle accounts in parallel; CPU, Internet ON. Gates as PC8 §5 (record gates, G-pc8cols, G-pc7reuse, G-pc7plat,
G-pc7rep, G-guard, G-pc7k, G-pc7r0; CPU model in `run_meta`). Same machine limitation as PC8 (arm and machine type
confounded within an arm; R1m reported beside R1).

## 6 · Code

- `src/eur_abl.py` (owner D37-F): arms P8d, P8e in `PC1_ARMS`, `VARIANTS` and `PC8_DROP` (gate G-pc8cols unchanged).
- `src/eur_make_notebooks.py --only EUR_PC8B` → `EUR_PC8_d`, `EUR_PC8_e` (PC8's notebook frame; only the description
  differs).
- `src/eur_pc8b_read.py` (new): the reading of §4 → `results/eureka_d37f/pc8b/`. Checked on the real committed PC8 runs
  before this design was approved for running, with P8a / P8b standing in for P8d / P8e (gates M-gates, M0, M1, M2, M4,
  M5, M6, M7 PASS; that check produced the premise number of §1 and nothing else is used).
- `src/eur_pc8b_synthetic_test.py` (new): PC8's synthetic test first (regression), then the two notebooks end to end in
  the same world, non-circular checks, the reader and negative paths; the PC1, PC7 and PC6 synthetic tests re-run on the
  changed `eur_abl.py`. All from a frozen copy of the repository.

## 7 · Literature

- Au, Q., Herbinger, J., Stachl, C., Bischl, B., & Casalicchio, G. (2022). Grouped feature importance and combined
  features effect plot. *Data Mining and Knowledge Discovery, 36*, 1401–1450. https://doi.org/10.1007/s10618-022-00840-5
  — leave one group out (LOGO) and leave one group in (LOGI) answer different questions with correlated groups. Applied:
  P8d / P8e are LOGO of the full input and at the same time "add one group" to the LOGI arm P8c, so R1 and R5 read both
  directions.
- Hooker, G., Mentch, L., & Zhou, S. (2021). Unrestricted permutation forces extrapolation: variable importance requires
  at least one more model. *Statistics and Computing, 31*, 82. https://doi.org/10.1007/s11222-021-10057-z — refit
  without the features instead of permuting them. Applied: every arm retrained.
- Williamson, B. D., Gilbert, P. B., Simon, N. R., & Carone, M. (2023). A general framework for inference on
  algorithm-agnostic variable importance. *Journal of the American Statistical Association, 118*(543), 1645–1658.
  https://doi.org/10.1080/01621459.2021.2003200 — importance as the loss of the refitted model, with intervals.
- Craley, J., Johnson, E., Jouny, C., & Venkataraman, A. (2021). Automated inter-patient seizure detection using
  multichannel convolutional and recurrent neural networks. *Biomedical Signal Processing and Control, 64*, 102360.
  https://doi.org/10.1016/j.bspc.2020.102360 — detection on patients not used for training (leave one patient out) is the
  clinically relevant setting and is harder than within-patient evaluation. Applied: the primary set is the patients the
  encoder was not trained on.

## 8 · What this design does not do

No new feature, no change of the architecture, graph or chain; no single-feature arms; no arm with the relative band
powers or the connectivity row alone (without the seven absolute features: PC1's 10a already shows that removing the
seven loses most of the detection). The deliverables keep V5's numbers; the result serves the Q&A of 11/12.
