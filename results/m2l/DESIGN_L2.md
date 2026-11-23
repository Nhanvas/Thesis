# DESIGN L2 / L3 — the label-free per-recording protocol (SzScan 1.0 baseline)

Track F, milestone M2, stream L, chat F2-03. Written 23/11/2026 before any code or output of L2 / L3; outline approved
by the author 23/11 14:07. **Status: draft for the author's approval.** Base: `main` = `912b166`. Plan
`docs/FUTURE_RESEARCH_PLAN.md` §15.4 items L2, L3; failure modes `docs/FAILURE_REGISTRY.md` FM-06, FM-19, FM-22, FM-23,
FM-25, FM-28; L1 = `results/m2l/L1_SZSCAN_TODAY.md`.

## 1. Question

V5 estimates its z-score statistics (with labels on CHB-MIT), its per-channel latent reference, its percentiles and its
alarm budget over **all recordings of a patient**. An independent benchmark (SzCORE, X1) and a real review tool receive
**one EDF at a time**. **Question:** with the V5 checkpoints unchanged, how much detection remains when every quantity
is estimated label-free from the single recording being reviewed, and which of three estimation choices (scale of the
z-score, covariance of the reference, floor of the budget) works best on the development patients?

**Expectation (hypothesis, not a pass threshold).** A recording holds less background than a patient (CHB-MIT median
1 h against 19–156 h per patient) and a larger share of seizure (1–3 % of windows instead of about 0.1 %), so the
reference is noisier and more contaminated (FM-19: a reference other than the patient's own recording costs
sensitivity). Robust estimates of scale and covariance should recover part of the loss. Measured as paired differences
with intervals; the author judges them.

## 2. What stays V5

V5 checkpoints `data/models_v2/gae_v2_clean_seed{42,1,2,3}.pt` (sha256 as in `docs/PROVENANCE_V2.md`), inference only;
whole-file band-pass 0.5–60 Hz + notch (60 Hz CHB-MIT, 50 Hz Siena); 4-s windows; graphs and node features
(`c1b_build_trainset.graph_and_bp`, `f7`); the checkpoint's input constants; members 6th / 9th / 12th largest and
channel mean, each minus its ±15-min running median (`e17b_latent_family.member`), percentile, mean
(`e22_test_oneshot.final_scalar`); robust z of the member mean (`p3_levers.member_mean_z`); 5-window smoothing,
detector and 90-s merge (`p2_scalars.d1_events`); kernel CPD localizer (`p3_levers.localize`, mode `cpd`); scoring
`p2_scalars.score` (SzCORE `timescoring`, the project's parameters), per-patient means. Record modules are imported
read-only; new code only in `src/m2l_*`.

## 3. The recording unit

- **Recording** = one EDF file as distributed (CHB-MIT: one file of the defense-time file set; Siena: one file; chb24:
  one file). Every quantity below is computed from that file alone; nothing is carried between files of a patient.
- **Input:** the 18 bipolar derivations of the thesis. CHB-MIT files are bipolar (`preprocessing.open_edf`); Siena files
  are referential and are subtracted to the 18 derivations and resampled to 256 Hz by `x1_external.load_18`. The same
  subtraction applies to SzCORE's 19 average-referenced electrodes (the common reference cancels); proving that adapter
  on SzCORE's converted files is X1's task.
- **Statistics sampling:** every 10th 4-s window of the recording, counted from its first window (windows `i` with
  `(i + 1) % 10 == 0`), each filtered with 3 s of padding (`x1_external.window_padded`) — the record and application
  rule, restarted per recording. No label anywhere.
- **Signal-loss windows** (raw SD < 1e-10 V on all 18 channels) are not scored and not used in any fit, as in V5.
- **Minimum length:** see §6 (chosen on development).
- Detector, merge and localizer already work inside each file; the ±15-min running median is per file in V5 already.
  So the per-recording protocol is the V5 chain run on a one-file context, with the four per-patient fits moved to the
  file.

## 4. The eight arms (options chosen on development)

| option | values | why |
|---|---|---|
| **S — z-score scale** | **R** record: mean and SD (ddof 1) of the sampled samples · **B** robust: median and `IQR / 1.349` of the same samples, multiplied per channel by `c_ch` | RB1c: the record SD is dominated by a few windows in most cases (top 1 % of sampled windows 4.6–37.5 % of the squared deviation); a seizure in a 1-h recording weighs far more than in a patient's 40 h. `c_ch` keeps the robust scale on the scale the GAE was trained on: the 7 absolute features carry most of the detection and depend on the scale (PC1, PC8), so an uncalibrated robust scale would confound "robust" with "input shift" |
| **C — reference covariance** | **LW** LedoitWolf (V5) · **MCD** reweighted Minimum Covariance Determinant, `sklearn.covariance.MinCovDet(support_fraction=0.75, random_state=0)`, squared Mahalanobis distance as V5 | seizure windows (1–3 % of a recording) enter the per-channel fit; MCD with h = 0.75 n is the usual compromise between breakdown (25 %) and efficiency (Hubert et al. 2018) |
| **F — budget floor** | **F** top = clip(q, 0.005, 0.02) per recording (V5's rule) · **N** top = min(q, 0.02); top = 0 → no event | with one recording at a time, the floor forces at least one alarm in every recording, also a seizure-free one; FM-23: the budget rule was chosen after test looks — here it is chosen on development only |

Arms: R-LW-F (= **P0**, the arm closest to V5), R-LW-N, R-MCD-F, R-MCD-N, B-LW-F, B-LW-N, B-MCD-F, B-MCD-N.

**`c_ch`** (computed 23/11 from `results/r2/r0_data/rb1c/channels.csv`: per channel, the median over the 12 training
patients of `sd_record_uV / iqr_uV`, where `iqr_uV` is already IQR / 1.349; gate G-c recomputes them):

| FP1-F7 | F7-T7 | T7-P7 | P7-O1 | FP1-F3 | F3-C3 | C3-P3 | P3-O1 | FP2-F4 |
|---|---|---|---|---|---|---|---|---|
| 2.041 | 1.624 | 1.475 | 1.422 | 1.794 | 1.594 | 1.485 | 1.470 | 1.818 |

| F4-C4 | C4-P4 | P4-O2 | FP2-F8 | F8-T8 | T8-P8 | P8-O2 | FZ-CZ | CZ-PZ |
|---|---|---|---|---|---|---|---|---|
| 1.467 | 1.572 | 1.488 | 2.058 | 1.599 | 1.495 | 1.418 | 1.668 | 1.546 |

(The values used by the code are the unrounded medians written by G-c to `c_ch.json`.)

**k per (S, C)** — V5's rule `p3_levers.calibrate` on seed 42: k such that the median over the 15 development patients
of q_i(k) = 0.005, where q_i is computed on the patient's per-recording smoothed member-mean series (each recording's
series computed on its own, then concatenated per patient). F and N arms of one (S, C) share k (k does not depend on
the floor). Patient-weighted like V5.

## 5. Evaluation of the arms (L2, development only)

- **Sets:** the 15 development patients (12 training + 3 validation; defense-time file set; 428 files) — no test,
  chb24 or Siena file is read in L2.
- **Scoring:** each recording is scored on its own (`p2_scalars.score` on the one-file context with the record's
  `is_ictal`, `is_buffer` slices — labels enter only here); counts summed per patient; per-patient sensitivity,
  precision, F1 from counts, FP/day over non-ictal hours (V5's definition); 4 seeds; per-patient means, then mean over
  seeds. Stage after the localizer (cpd) is primary; detector-stage and onset / offset errors (`e18` match) are reported.
- **Budget arms reported:** each arm's own label-free point (primary) and a fixed 0.5 % per recording (descriptive).
- **References on development:** V5 (R1.0 rows, reproduced in the notebook) and **L0** = the same chain with
  patient-level label-free statistics (EUR_9A `LF`, committed `results/eureka_d31f/9a/`: sensitivity 0.838, F1 0.227,
  22.7 FP/day) — L0 − V5 isolates "label-free", arm − L0 isolates "per recording" (both descriptive; L0 rows from another
  Kaggle session, rebuild difference FM-28).
- **Paired patient bootstrap** of 4-seed means (B = 10,000, seed 0; chb01 + chb21 one unit → 14 units), 95 %
  percentile intervals, for every arm − P0, arm − V5, arm − L0 (sensitivity, F1, FP/day).
- **Also reported per arm:** share of recordings with no event; windows flagged; mean events per recording and event
  duration (fragmentation, FM-09); recordings below the provisional length guard (§6).

## 6. Rules written before the runs

**Selection of the arm (after L2).** Among the arms whose development F1 − P0 interval lies entirely above 0 **and**
whose development sensitivity − P0 point estimate is ≥ −0.03, choose the one with the highest development F1; if none,
choose **P0**. Ties (equal F1 to 3 decimals) → the arm with fewer changes from V5 (order of simplicity: F before N, LW
before MCD, R before B). The reader `src/m2l_read.py` (committed before the outputs) applies the rule and writes
`results/m2l/l2/selection.json` (arm, its k, the inputs of the rule).

**Minimum recording length (after L3-short, before L3-eval).** For the chosen arm, development recordings are cut into
segments of L = 5, 10, 20, 30 min (§7) and each segment is scored as a recording. With F1_full and Sens_full the chosen
arm's development values on whole recordings: the minimum length is the **smallest L with F1_L ≥ F1_full − 0.02 and
Sens_L ≥ Sens_full − 0.03**; if no L qualifies, 30 min. A recording shorter than the minimum gets no event (its
seizures count as missed); the number of such recordings and seizures is reported per set. (0.02 in F1 ≈ PC7's
smallest detectable F1 difference with 4 seeds, 0.016–0.019; 0.03 in sensitivity ≈ 3 of 94 development seizures.)
*Provisional guard for L2 only:* a recording with fewer than 76 valid windows (5 min) is not scored (MCD needs
n > 16; development has none below 150 windows: chb01_27, 150 windows, no seizure — from
`results/eureka_d31f/9a/inventory/inventory.csv`).

These rules are fixed here; any change after a result is logged with what had been seen (plan §12).

## 7. L3 (after the selection and the minimum length)

- **L3-short (development, descriptive + the minimum-length rule):** each development recording cut into consecutive
  non-overlapping segments of L minutes from its start; a remainder shorter than L / 2 joins the previous segment,
  otherwise it is a segment; a cut that falls inside an annotated seizure moves to that seizure's offset (labels place
  the cuts of this analysis only, never the protocol), so no seizure is split. Chosen arm, k from `selection.json`, the
  length guard off. Two notebooks: L = 5 and 10 min; L = 20 and 30 min.
- **L3-eval (scored once):** the chosen arm with its k and the minimum length on the 8 test patients, chb24 and the 14
  Siena patients; 4 seeds; per-patient means; V5 control in the same session (R1.0 test rows = `e23_test_look7`, GE for
  chb24 / Siena = V0 from the rebuilt external features, as every EUR run); paired patient bootstrap of L3 − V5 on test
  (8 units) and Siena (14 units), chb24 descriptive; L3 − L0 on test (L0 = EUR_9A LF test rows; for chb24 / Siena V0
  is already patient-level label-free, so L3 − V0 there is the per-recording effect alone). Also the fixed 0.5 % per
  recording, onset / offset errors and the share of recordings with no event. These are the **SzScan 1.0 baseline
  numbers**; test is descriptive (it has entered earlier decisions, FM-24), Siena is the independent external set.

## 8. Gates (STOP unless PASS; outputs written before the gates read them)

| gate | notebook | check |
|---|---|---|
| G-mod / G-worker | all | every embedded or cloned module = the reviewed sha; every pool job reports the sha of the modules it ran (notebook pin rule, R205) |
| G-raw | all | every EDF used verified by sha256 against PhysioNet's SHA256SUMS in the session (`r2_core.inventory`) |
| G-data | all | the earlier `.npz` = `docs/PROVENANCE_V2.md` (`eur_abl.gate_data`) |
| R1.0 | all | V5's committed rows reproduced (development in L2 / L3-short; test + GE in L3-eval; `r2_r1.r10`) |
| G-chain | L2 | the m2l context builder and scorer, run at the **patient** unit on the committed record features with V5's distances, give V5's development rows exactly (proves the new code path) |
| G-split | L2 | on the record features, the one-file contexts concatenated per patient give the same windows, labels, `is_buffer`, `file_idx` and the same SzCORE counts for a fixed event list as the patient context (bookkeeping of the unit change) |
| G-stats1 | L2 smoke | the m2l statistics of chb08 computed (a) per recording and (b) pooled with one counter over the patient = (a) an independent loop over `x1_external.window_padded`, relative ≤ 1e-9; (b) EUR_9A's committed `stats_lf/chb08_stats.json`, relative ≤ 1e-6 |
| G-feat1 | L2 smoke | the m2l feature builder with the committed record statistics of chb08 on its first 2 files = the earlier `.npz` (`r2_core.compare_features`, R0's tolerances) |
| G-c | L2-ROB (and L3 if S = B) | `c_ch` recomputed from the committed RB1c file = the table above to its 3 decimals; the unrounded values are used and written to `c_ch.json` |
| G-struct | L2, L3 | per recording: window count, `is_ictal`, `is_buffer`, signal-loss flags = the matching slice of the earlier `.npz` (CHB-MIT) or the external features (Siena, chb24) — exact |
| G-sel | L3 | `results/m2l/l2/selection.json` (and for L3-eval `results/m2l/l3short/minlen.json`) exist at the pinned commit and were committed before the notebook's first output |
| PROJ | all | projected wall time from the smoke's measured rates; STOP if > 10.5 h |

## 9. Notebooks, accounts, inputs, cost

| notebook | account | Kaggle inputs (exact slugs) | does | runtime (computed) |
|---|---|---|---|---|
| `M2L_L2_REC` | `nhn2mm` | `combined-siena-scalp-and-chb-mit-eeg-datasets`, `v9-x3-fold1`, `v9-x3-fold3` | development, S = R: arms R-LW-F, R-LW-N, R-MCD-F, R-MCD-N | ≈ 3–3.5 h |
| `M2L_L2_ROB` | `nhannguyen26` | `combined-siena-scalp-and-chb-mit-eeg-datasets`, `v9-x3-fold1`, `v9-x3-fold3` | development, S = B: arms B-LW-F, B-LW-N, B-MCD-F, B-MCD-N | ≈ 3–3.5 h |
| `M2L_L3_SHORT_A` | `nhn2mm` | `combined-siena-scalp-and-chb-mit-eeg-datasets`, `v9-x3-fold1`, `v9-x3-fold3` | development segments L = 5, 10 min, chosen arm | ≈ 4–5 h |
| `M2L_L3_SHORT_B` | `nhannguyen26` | `combined-siena-scalp-and-chb-mit-eeg-datasets`, `v9-x3-fold1`, `v9-x3-fold3` | development segments L = 20, 30 min, chosen arm | ≈ 3–4 h |
| `M2L_L3_EVAL` | `nhn2mm` | `combined-siena-scalp-and-chb-mit-eeg-datasets`, `v9-x3-fold1`, `v9-x3-fold3`, `thesis-r2-external-features` | test, chb24, Siena, chosen arm and minimum length; V5 control | ≈ 2–2.5 h |

All CPU, Internet ON (pip, clone, PhysioNet checksums). Order: L2_REC ∥ L2_ROB → reading and selection (laptop,
`src/m2l_read.py`) → L3_SHORT_A ∥ L3_SHORT_B → minimum length (laptop, reader) → L3_EVAL → reading.
*Basis of the estimates:* EUR_9A's measured rates, 12.0 s (statistics) + 18.35 s (features) per hour of EEG per worker
(`results/eureka_d31f/9a/projection.json`), 677 h of development EEG (inventory), 4 workers → ≈ 1.4 h per feature
build; MCD 0.52 s per fit of 900 × 16, 1.03 s of 3,600 × 16 and 0.03 s up to 450 × 16 (sklearn's exact small-sample path; timed in the build container), ≈ 30,800 fits per
development notebook (428 recordings × 18 channels × 4 seeds) → ≈ 1.3 h on 4 workers; scoring and R1.0 ≈ 0.4 h (EUR_9A
0.21 h + 0.18 h measured); L3-short: one feature build per segment length. The notebooks measure and print their own runtime.

## 10. Code and tests (committed before any run)

`src/m2l_core.py` (statistics R / B per recording, per-recording features, distances LW / MCD, one-file contexts, k
calibration, arms, scoring, segments for L3-short), `src/m2l_run.py` (notebook entry: gates, smoke, build, score,
outputs), `src/m2l_make_notebooks.py`, `src/m2l_read.py` (merge, bootstrap, selection rule, minimum-length rule,
tables), `src/m2l_synthetic_test.py`. `src/eur_*` are read only (owned by F2-02).

Synthetic test (build container, before the commit): every gate PASS on a synthetic world (CHB-MIT-like bipolar files,
a Siena-like referential file at 512 Hz, planted seizures and a planted high-amplitude stretch); statistics R / B = an
independent re-implementation; `c_ch` × robust scale = SD on Gaussian data within 1 % after the per-channel factor is
removed; MCD distances = an independent `MinCovDet` call; the patient-unit path = the record chain (G-chain on synthetic
record features); the one-file contexts reproduce the patient context's bookkeeping (G-split); top = 0 gives no event;
k per (S, C) = an independent bisection; segment cuts never split a seizure and cover the recording; the selection and
minimum-length rules on hand-made tables give the expected arm / length (including "none → P0" and "none → 30 min");
failure paths STOP at G-mod, G-raw (corrupted byte), G-data, R1.0 (edited row), G-chain (perturbed distance), G-stats1,
G-feat1, G-c (edited constant), G-struct (shifted label), G-sel (missing selection file), PROJ. Not covered by the test:
real amplitudes, runtime and memory on Kaggle (the smoke measures them).

## 11. Outputs and wording limits

Outputs (small files only; no EEG, no `.npz`): `results/m2l/l2_rec/`, `results/m2l/l2_rob/`, `results/m2l/l2/`
(merge, `SELECTION.md`, `selection.json`), `results/m2l/l3short_a/`, `…_b/`, `results/m2l/l3short/` (`minlen.json`),
`results/m2l/l3eval/`, `results/m2l/l3/` (`T_L3.md`): per recording × arm × seed rows (tp, fp, n_ref, nonict_h, q, top,
events, review time), per patient rows, errors, `k.json`, statistics per recording (mean / scale per channel), gates,
runtimes, run_meta.

Wording limits: one model family (the V5 checkpoints); development includes the 12 training patients (optimistic);
test is descriptive; the protocol is fully label-free at inference but k was calibrated on development patients and
the GAE was trained on them (a fixed model, as every submitted algorithm in SzCORE); "per recording" = one EDF of these
datasets — SzCORE's converted files may be split differently (checked in X1); numbers from rebuilt features carry the
rebuild tolerance (FM-28); the robust scale is calibrated to the training scale, so it does not answer RB1c's
"retrain with a robust statistic" (G1 / later).

## 12. Literature (item 14)

Peer-reviewed:
- Hubert, M., Debruyne, M., & Rousseeuw, P. J. (2018). Minimum covariance determinant and extensions. *WIREs
  Computational Statistics, 10*(1), e1421. https://doi.org/10.1002/wics.1421 — MCD; h ≈ 0.75 n as a robustness /
  efficiency compromise; reweighting.
- Rousseeuw, P. J., & Hubert, M. (2018). Anomaly detection by robust statistics. *WIREs Data Mining and Knowledge
  Discovery, 8*(2), e1236. https://doi.org/10.1002/widm.1236 — masking of outliers by classical mean / covariance.
- Ledoit, O., & Wolf, M. (2004). A well-conditioned estimator for large-dimensional covariance matrices. *Journal of
  Multivariate Analysis, 88*(2), 365–411. https://doi.org/10.1016/S0047-259X(03)00096-4 — V5's estimator.
- Bigdely-Shamlo, N., et al. (2015). The PREP pipeline. *Frontiers in Neuroinformatics, 9*, 16.
  https://doi.org/10.3389/fninf.2015.00016 — robust SD = IQR / 1.349 for EEG channel statistics.
- Leys, C., et al. (2013). Detecting outliers: do not use standard deviation around the mean, use absolute deviation
  around the median. *Journal of Experimental Social Psychology, 49*(4), 764–766. https://doi.org/10.1016/j.jesp.2013.03.013
- Logesparan, L., Rodríguez-Villegas, E., & Casson, A. J. (2015). The impact of signal normalization on seizure detection
  using line length features. *Medical & Biological Engineering & Computing, 53*, 929–942.
  https://doi.org/10.1007/s11517-015-1303-x — normalization choice changes seizure-detection AUC by up to 52 %.
- Dan, J., Shahbazinia, A., Kechris, C., & Atienza, D. (2026). Quantifying the generalization gap in seizure detection: a
  large-scale empirical benchmark via the SzCORE challenge. *PMLR 306* (ICML 2026), 22743–22757.
  https://proceedings.mlr.press/v306/dan26a.html — 28 algorithms on 65 private subjects (4,360 h); event F1 ranking.

Preprints and code:
- Dan, J., et al. (2024). SzCORE. arXiv 2402.13005. https://doi.org/10.48550/arXiv.2402.13005 — scoring this project uses.
- `github.com/esl-epfl/szcore` (read 23/11): one EDF per container run, 19 average-referenced electrodes at 256 Hz, TSV
  output; DynaSD (`algorithms/dynasd.yaml`) is an unsupervised per-recording method (a model trained on the beginning of
  each clip; event results CHB-MIT 0.61 at 23.2 FP/day, Dianalund 0.55 at 37.1, `results/ghcr-io-wojemann-dynasd-competition-latest/`)
  — the closest precedent: the reference is estimated from the recording itself.
- Test-time adaptation for EEG models (e.g. arXiv 2604.16926, a systematic benchmark, preprint) adapts network
  parameters to unlabeled target data; here no parameter of the network changes — only the reference statistics, which
  is the lighter, source-free form (re-estimating normalisation and reference on the target recording).

No peer-reviewed study was found that compares per-recording with per-patient reference estimation for an anomaly score
on long scalp EEG; the comparison is stated within this protocol.

## 13. Options not chosen (→ plan §14)

Retraining with a robust statistic (RB1c; G1 / later); a causal or sliding reference (real time is out of scope);
pooling all recordings of a patient when the benchmark allows (that is V5's unit, kept as the reference); other MCD
support fractions; Tyler's M-estimator or MRCD instead of MCD; a fixed technical minimum length (replaced by the
development rule of §6, because the 10-min segments of L3-short would fall under a 160-window guard).
