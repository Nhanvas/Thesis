# FUTURE_RESEARCH_PLAN — independent research track: rerun on complete data, then Track F (rev 2, 2026-11-06, chat D13-F; §12 updated D14-F: 06/11 13:25, 18:40; 07/11 06:10; D14b-F: 07/11 12:49, 14:26, 15:48; D15-F: 07/11 16:40, 18:55; D16-F: 08/11 07:40, 09:30; D17-F: 08/11 19:10, 09/11 21:15; D18-F: 10/11 11:50; D19-F: 11/11 10:15; PU1: 11/11 14:50; D20-F: 11/11 23:10, 12/11 09:00)

*Repo: `docs/FUTURE_RESEARCH_PLAN.md` + project file. **Rev 2 replaces rev 1 in full** (author decisions 06/11, 09:12 –
10:38). The F1/F2 design of rev 1 is kept unchanged as §7. Rev 1's run on the earlier data copy stays as a record
(§11). From now on, every change is logged in §12 **before** any result is seen. Nothing in this file has been run
yet unless §11 or §12 says so.*

---

## 0 · Status, scope and way of working

**Status from 11/11 (PU1; board rev 43, R141–R157).** The defense is done (09/11). The track is **no longer
independent of the thesis**: the final report reports one model, the thesis system re-run on the complete data, so the
track's next job is **stage RP** (§7b), the numbers and figures of the final report. R4 and later stages follow RP.
- Before 11/11 the defense, slides and Q&A used only the locked numbers (`NUMBERS_LOCK.md`, `NUMBERS_LOCK_S18.md`);
  those files are now history.
- Committed results are still never overwritten; new results go under `results/r2/`.

**What it does, in order:**
1. **Stage R — rerun from raw EEG on complete data:** R0 data, R1 thesis system, R2 four-fold CV with the six
   models, R3 repeated random partitions (F1/F2).
2. **Track F analyses on the rerun:** F5 offset, F3 mechanism, then F4 graph insights and F6 features for weak
   seizures.

The reason is §1: every earlier run used a CHB-MIT copy that missed five files.

**Way of working (author 05–06/11):**
- Research is an iterative try-and-fix loop. A result is believed only after it has run and passed verification.
- Every new analysis or fix is proposed to the author first and runs only after approval.
- Kaggle only; the laptop runs nothing in this track.
- Standard: public data, committed code, gates that stop the run, measured runtime, every change logged before
  results are seen.
- **Choosing a method or parameter:** run the full grid on selection data only, and measure the choice on data not
  used to make it (nested CV). The reason is that tuning and reporting on the same data inflates the result (Varma &
  Simon 2006, BMC Bioinformatics 7:91; Cawley & Talbot 2010, JMLR 11:2079; Leeflang et al. 2008, Clin Chem 54:729).
- **No pass/fail thresholds fixed before a run.** Paired differences are reported with patient-bootstrap CIs, and the
  author decides.
- **Mechanism tests are read across the whole parameter grid,** never at one chosen point.
- **Rules already pre-registered stay as they were** (e.g. the F2 count rule), so that the rerun stays comparable
  with the record.

## 1 · Finding 06/11 — every earlier run used an incomplete CHB-MIT copy

The local copy of CHB-MIT lacked **five seizure-free files** listed in the summaries:
- `chb11_12`, `chb11_13`, `chb11_14`, `chb11_15` (4.0 h; chb11 = validation patient of the thesis split);
- `chb21_11` (1.0 h; chb21 = training patient).

Sources: `src/continuous_eval.py` (`list_files` docstring); `Thesis_Final_Report.md` Appendix A; earlier
`docs/writing/REPORT_OUTLINE_v8.md`. The `.npz` feature files on Kaggle (`v9-x3-fold1…4`) were built from that copy.

**Which results are affected:**

| result | effect |
|---|---|
| thesis system (GAE v2, seeds 42/1/2/3) | 1 h of chb21 missing from training (and from its z-score statistics); 4 h of chb11 missing from development scoring and from the label-free calibration of k |
| 4-fold CV of the GAE (`results/v9_x3`), six-model comparison (`results/model_cmp`), F1/F2 (`results/f1_repcv`) | chb11 and chb21 lack these hours both as training cases and as held-out cases; their z-score statistics and ±5 SD thresholds come from the incomplete file set. Gate D0 of these runs checked identity **with** the earlier copy, so it could not detect the gap |

**Which results are not affected:**
- the 8 test patients are complete (≤ 0.01 h per case, Appendix A);
- chb24 in the CV is complete: 21.14 h non-ictal, equal to the x1 Kaggle run with all 22 files;
- the 3 skipped chb12 files (`chb12_27`–`29`) are skipped **by design** (a derivation is missing), not by a data gap.

**Effect size:** unknown until measured. Five hours are about 0.5 % of the 983 h, but they are 11 % of chb11's
recording, and they change chb11's and chb21's z-score statistics and ±5 SD thresholds.

**Decisions (author 06/11):**
- **D1 — rerun means re-execution of the frozen design.** Label-free calibrations (the f7 constants, k) are
  recomputed by their recorded rules on the new data. No parameter is re-tuned. The design history (development
  decisions, test looks) is unchanged and stays disclosed.
- **D2 — storage.**
  - New results go in `results/r2/<stage>/` with tags `r2-<stage>`.
  - Committed results are never overwritten, because the thesis record and the locks point to them.
  - The local gitignored caches stay on the laptop until the author declares the project finished (author 11/11;
    previously "archived after 09/11"). There is no `Archive/` folder any more (`LOCAL_LAYOUT.md`).
  - The rerun runs on Kaggle and does not need the local caches.

## 2 · What we already know (verified; do not rediscover)

| fact | source |
|---|---|
| everything in rev 1 §1 (GAE CV, seeds share one split, six-model result, both autoencoders rebuild the graph, measured Kaggle times, tensor loop = PyG loop bit for bit, CPU not slower) | rev 1 §1 (kept in git) |
| thesis training recipe: `train_gae_v2.py`, variant clean, 12 training patients, f7 constants from the training windows, Adam 1e-3, cosine T_max 200, batch 32, 200 epochs, last epoch saved; validation loss on chb10/11/22 is logged only | `src/retrain/train_gae_v2.py` |
| k = 4.0677: calibrated once on the 15 development patients, seed 42, label-free, so that the median q_i(k) = 0.005 | `src/p3_levers.py` (`calibrate`), `results/p3_levers/calibration.json` |
| chb24 has two feature conventions: thesis convention for the CV (`v9_x3_build_chb24.py`: stats from its own interictal windows without the 4 h buffer, then the c1b construction); label-free convention for external validation (`x1_external.py`: stats from every 10th window of the whole recording). chb24's CV stats file was never committed | `src/v9_x3_build_chb24.py`, `src/x1_external.py`, git |
| the x1 external run (chb24 + Siena 14) ran on **Kaggle CPU** reading a combined dataset in place; the author identifies it as `bonesclarke26/combined-siena-scalp-and-chb-mit-eeg-datasets` (folders `chbmit`, `siena`) | `x1_external.py` docstring; author 06/11 |
| cross-platform tolerance for the external rows: \|Δtp\| ≤ 1, \|Δfp\| ≤ 2 per row (isolated borderline windows; measured) | `src/v9_anatomy.py` (`check_repro_ext`), `results/v9_anatomy/siena14/gate.csv` |
| **the hybrid (L6) boundary errors are already committed for every set**: development `p3c_freeze/errors.csv`, final test `e23_test_look7/errors.csv`, chb24 and Siena `x1_external/errors_*.csv`; median \|onset\|/\|offset\| (s), CPD vs hybrid: dev 4/16 vs 8/12; test 12/24 vs 12/16; chb24 4/4 vs 4/4; Siena 20/28 vs 20/20 | those files' SUMMARY.md (record) |
| **L6 "hybrid", as coded** (`p3_levers.localize`): onset = CPD onset when CPD is accepted, else the detector's; offset = the contiguous above-threshold run containing the event peak; events longer than 300 s keep the detector's boundaries; events are re-merged at 90 s. Detection is **not** unchanged by construction (dev: hybrid 0.676 vs CPD 0.670, pooled, record) | `src/p3_levers.py`, `results/p3c_freeze/SUMMARY.md` |
| SzCORE tolerances: 30 s before onset, 60 s after offset, merge < 90 s, split > 5 min; the authors call exact seizure boundaries notoriously difficult to annotate | Dan et al. 2024, arXiv 2402.13005 |
| offsets are harder than onsets in other work: post-ictal slowing resembles other slowing (von Weltin et al., arXiv 1801.02470); seizure end vs post-ictal stage is hard to define (Sanz-García et al. 2017, Entropy 19:81); a post-processing model locates offsets less accurately than onsets (ScoreNet, bioRxiv 10.1101/2020.12.21.423728); readers agree less on duration (62 %) than on any overlap (70 %) (Tu et al. 2017, Epilepsia Open 2:67) | literature, read 06/11 |
| F1/F2 on the earlier copy: GAE CV 0.736 ± 0.012 over 6 partitions; MLP-AE ΔF1 > 0 in 6/6, +0.075 [+0.034, +0.121] | S18 §18.8 (record; §11) |

## 3 · Data source and shared datasets

**Raw EEG:** Kaggle `bonesclarke26/combined-siena-scalp-and-chb-mit-eeg-datasets`.
- Its identity is proven per file by **sha256 against PhysioNet's `SHA256SUMS.txt`** (CHB-MIT 1.0.0, Siena Scalp EEG
  1.0.0), downloaded inside the notebook (internet on).
- A listed file that is absent or differs is downloaded from PhysioNet (open access) into the session and hashed the
  same way.
- If any file cannot be obtained, the run stops and the author is asked.

**Feature datasets** (public, owner Nhân2mm, shared by the four accounts; author 06/11):

| dataset | content | convention |
|---|---|---|
| `thesis-r2-chbmit-features` | 24 cases (chb01–chb24): `{case}.npz` + `{case}_stats.json` + `inventory.csv` | thesis convention (stats from interictal windows without the 4 h buffer; c1b construction) |
| `thesis-r2-external-features` | chb24 + Siena PN00…PN17 (14): `{case}_lf.npz` (x1 save format + `meta` incl. the label-free statistics) + `inventory.csv` (§12, 06/11 D14-F) | x1 convention (label-free stats, every 10th window; Siena 18 bipolar from the referential montage, 512 → 256 Hz, notch 50 Hz) |

- Each dataset description cites the sources. Siena: Detti 2020, PhysioNet, DOI 10.13026/5d4a-j060, licence
  CC BY 4.0 (checked 06/11). CHB-MIT's licence is checked before publishing.
- Checkpoints (≈ 20 KB each) and every result table are committed under `results/r2/`. EEG and `.npz` files are
  never committed.

## 4 · Stage R0 — data rebuild (Kaggle CPU)

**R0.1 Inventory.** For every case:
- list files listed in the summary vs files present;
- sha256 of every EDF compared with `SHA256SUMS.txt`;
- parse the seizures with the record's parsers (CHB-MIT summaries; Siena with the vendored SzCORE converter of
  `x1_external.py`);
- compute hours.

Report: per case files listed / present / hashed-equal / skipped by design, seizures, hours. Expected from the record
(to check, not to tune):
- 198 CHB-MIT seizures listed over the 24 cases (93 + 13 + 76 + 16);
- 47 Siena seizures;
- 141.0 h Siena;
- the five files of §1 present after this step.

**R0.2 Identity gates (STOP on failure)** — run before anything new, to prove that the Kaggle data and code equal the
record:
- **G-stats:** `preprocessing.compute_subject_stats` (then `count_windows`, i.e. `process_subject` without its write
  pass) on the **earlier file set** reproduces the committed `data/processed/{subj}_stats.json` for the 23 thesis
  cases (float values relative ≤ 1e-6; window counts and ratio exact — §12, 06/11 D14-F). chb24 has no committed
  stats file; its statistics are proven by its G-feat.
- **G-feat:** with those stats, the c1b construction (`c1b_build_trainset` / `c1t_build_testset` / the chb24 builder)
  on the earlier file set reproduces the earlier `.npz` (`v9-x3-fold1` + `v9-x3-fold3` = all 24 cases) for every case:
  - flags (`is_ictal`, `is_buffer`, `is_flag5sd`, `is_signal_loss`) and `file_idx` exact (all windows);
  - `f7` and `bp5` max |diff| ≤ 1e-3;
  - adjacency entries differing ≤ 0.5 % (the x1 R-feat tolerance);
  - since §12 07/11 12:49: these three tolerances are read on the windows the chain uses (not `is_signal_loss`); the
    all-window reading (the one pre-registered here) and the signal-loss windows are reported beside it;
  - file list and skipped-file list exact; `zgamma_raw` compared descriptively (not used by the frozen system).

  For the 22 cases without a gap this rebuild **is** the new data.

**R0.3 Complete rebuild.** chb11 and chb21 on **all** their files (stats recomputed, then features). Diff report:
- windows added;
- change of every stats value;
- change of the clean-window count;
- seizure windows identical.

**R0.4 External features.** chb24 + Siena 14 with the x1 convention. Feature identity cannot be checked here (the x1
features were never committed); it is proven downstream by gate GE (§5).

**Outputs:** the two datasets (§3); `results/r2/r0_data/<smoke|chb|ext>/` (one folder per notebook: `inventory.csv`,
`inventory_cases.csv`, `checks.json`, PhysioNet `SHA256SUMS` copies, `gates.json`, `diff_chb11_chb21.{md,json}`,
`stats_earlier/`, `external_cases.csv`, `projection.json`, `run_meta.json` with measured runtime, `logs/`).

**Runtime:** the laptop measured 16 s per hour of EEG with 2 processes (chb24, REPRODUCE check 2b). That gives
≈ 5 h for ≈ 1,145 h of EEG (computed estimate). The smoke measures Kaggle (chb11 whole earlier set for G-stats, its
first 2 files for G-feat, one more file per worker in parallel, Siena PN00); if the projection exceeds 10.5 h, R0 is
split into notebooks by case.

## 5 · Stage R1 — the thesis system on complete data (Kaggle CPU)

**G-data (added §12 07/11 16:40; STOP on failure).** The attached feature datasets are R0's outputs: every file
present and hashed (`data_sha256.csv`; from R1_RUN on, pinned to R1_SMOKE's); statistics and window counts equal R0's
committed outputs (`stats_earlier/`, `diff_chb11_chb21.json`, `external_cases.csv`); flags, `file_idx` and file lists of
the 22 gap-free cases equal the earlier `.npz`; R0's G-feat re-read (chain scope) on the cases a notebook reads.
**G-const / G-count:** `train_gae_v2.norm_constants` on the earlier training windows = the committed checkpoints'
constants (relative 1e-9); clean training and validation window counts = the committed metas, exactly.

**R1.0 Code-path gates on the earlier data (STOP on failure).** The committed checkpoints
`data/models_v2/gae_v2_clean_seed{42,1,2,3}.pt` + the earlier `.npz` must reproduce, exactly:
- `results/p3c_freeze/per_subject.csv` (every recorded arm: frozen, L2, L2f, S; stages detector, cpd, hybrid; 15 cases ×
  4 seeds) and `errors.csv`;
- `results/e23_test_look7/per_subject_seed.csv` and `errors.csv` (points balanced and sensitivity; 8 cases × 4 seeds),
  `results/e22_test_oneshot/per_subject_seed.csv` (look 6), and `p3c_freeze.run_budget` on the test cases = those rows;
- **G-k:** `p3_levers.calibrate` (15 development cases, seed 42) = `calibration.json` within 1e-6 relative.

**GE:** the same checkpoints on the R0.4 features reproduce `results/x1_external/rows_*.csv` within the measured
tolerance (|Δtp| ≤ 1, |Δfp| ≤ 2 per row).

**R1.1 Training.**
- `train_gae_v2.py` recipe unchanged (§2), seeds 42/1/2/3, on the new `.npz` of the 12 training patients.
- f7 constants recomputed from these windows.
- Run with the tensor loop of `src/f1_core.py`, which equals the PyG loop bit for bit; gate G-vec on the thesis recipe
  (2,000 real windows, 2 epochs).
- Per seed: training-window count, parameters 3,964, last-epoch loss < first, loss curves.

**R1.2 Calibration.** k recomputed by `p3_levers.calibrate` (15 development cases, seed 42, median q_i = 0.005,
label-free).

**R1.3 Scoring**, 4 seeds, the frozen chain (one code path for every set: `p3c_freeze.run_budget`, whose detector
and CPD rows equal `e23_test_look7.evaluate`'s, proven in R1.0):
- development 15 and test 8 at every recorded arm — frozen 0.005 (the held-out system of look 6), L2, L2f (the final
  system), S — stages detector, CPD, hybrid; onset/offset errors;
- chb24 + Siena 14 on the R0.4 features (the x1 bookkeeping), same arms and stages.

**Counterfactual (added §12 07/11 18:55; descriptive, scoring only):** the committed checkpoints on the new data,
k recomputed (`cf`) and at the record's k (`cf_krec`), so that rerun − record splits into data (`cf_krec` − record),
k (`cf` − `cf_krec`) and new models (rerun − `cf`: training on complete data + retraining randomness, read beside
the record's across-seed spread).

**Reading (descriptive; `src/r2_r1_aggregate.py`, committed before R1_RUN):**
- gate A0: the per-patient metric reproduces the locked numbers from the record files; gate A1: complete run files,
  `n_ref` = the record's;
- per-patient means (SzCORE aggregate), 4 seeds, paired subject bootstrap (B = 10,000) for each step;
- one table "rerun vs record" for every row of `p3c_freeze`, `e23`, `e22` (look 6), `x1`;
- every difference explained (chb11 / chb21 data, k, retraining randomness) through the counterfactual;
- no row replaces a locked number of the thesis.

## 6 · Stage R2 — four-fold CV and the six-model comparison on complete data (Kaggle CPU)

**Setup:**
- `results/v9_x3/folds.json` unchanged; check that the seizure counts per case are identical.
- Fold manifests rebuilt from the new data.
- Models and recipes unchanged:
  - GAE fold models seed 42 (`v9_x3_train_fold.py` recipe, via the tensor loop);
  - MLP-AE;
  - Isolation Forest, linear SVM, gradient-boosted trees, 1-D CNN (`MODEL_COMPARISON_PLAN.md` rev 2 §1–§2).
- Same chain, own label-free k per fold.

**Gates (STOP on failure):**
- **D0′:** n_ref identical for all 24 cases; non-ictal hours identical for the 22 cases without a gap; chb11 / chb21
  larger only by the added files' non-ictal hours.
- **G-const:** recomputed per fold.
- The per-job gates of the comparison plan §3.
- **G-data** and **R2.0** (added §12 08/11 09:30): the new `.npz` hashes = R1_SMOKE's pinned hashes; the record's code
  paths reproduce the record on the earlier data with the committed models (GAE folds, Isolation Forest, trees 4 folds,
  linear SVM fold 1 exactly; MLP-AE and CNN checkpoints, trained and scored on a GPU in the record, within |Δtp| ≤ 1,
  |Δfp| ≤ 2 per row). **R2.0-cnn runs first inside `R2_C`** (added §12 08/11 19:10: the smoke cloned a commit without
  the CNN checkpoints, so the CNN code path was not gated there): all four checkpoints present (sha256 recorded), same
  tolerance; STOP before any CNN training.

**Counterfactual (added §12 08/11 09:30; descriptive, scoring only):** the committed GAE, MLP-AE and CNN fold models on
the new data, k recomputed, so that rerun − record splits into data (cf − record) and new models (rerun − cf); Isolation
Forest has no training and trees / SVM train deterministically, so for them rerun − record is the data effect.

**Reading:** the comparison plan's pre-registered analyses A–F and reading rules (§4 there) applied unchanged, plus
one table "rerun vs record". The GAE and MLP-AE rows are **partition 0** of R3.

**Device:** CPU. The CNN ran on GPU before, so its CPU speed is measured by the smoke; GPU is used only if CPU
cannot finish within a session.

## 7 · Stage R3 — F1 + F2, repeated random patient partitions, on complete data

**The design of rev 1 §3 is applied unchanged to the R0 data:**
- partitions: `results/f1_repcv/partitions.json` (committed `905212a`, before any training; folds sha
  `f945b4f2…`); partitions 1–5 with seeds 1–5; partition 0 = R2;
- models: GAE + MLP-AE, the thesis fold recipe, 200 epochs, last epoch kept;
- training loop: tensor loop (G-vec);
- chain: the frozen chain, k per fold;
- gates: D0′, G-const, G-vec, G-mlp, per job, aggregate; added at implementation (§12 10/11 11:50): G-data,
  R3-projection, G-const-p and **R3.0** (the committed F1 checkpoints on the earlier data = the F1 record rows within
  |Δtp| ≤ 1, |Δfp| ≤ 2 per row), all before any training; counterfactual (F1 checkpoints on the new data).

**Pre-registered reading** (unchanged, so the rerun is comparable with the record):
- **F1:** across-partition mean ± SD and range, with the SD called sensitivity to partition + seed, **not**
  uncertainty; paired-subject bootstrap CI of the mean.
- **F2:** "stable advantage" iff ΔF1 > 0 in ≥ 5 of 6 partitions AND the CI's lower bound > 0. Secondary readings as
  in rev 1.

**Added (descriptive):** per partition, rerun vs earlier copy.

**Device:** CPU (decision P4, §10). The rev 1 rule chose GPU by speed only. The smoke of 05/11 measured CPU 7.02 h vs
GPU 7.38 h per partition notebook. CPU uses no GPU quota and is bit-deterministic. No R3 smoke (author 09/11 21:11): the
CPU speed on complete data was measured by R2_A (partition 0, 7.68 h), and each R3 notebook gates itself before training.

## 7b · Stage RP — numbers and figures for the final report (added 11/11, PU1; runs before R4)

Design approved by the author 11/11 (board rev 43 R141–R149; `REPORT_REVISION_PLAN.md` §1–§2, §4). Each step is proposed
in detail, approved, gated and logged in §12 before its results are seen, as in R0–R3.

| # | step | note |
|---|---|---|
| RP1 | train **seed 4** on the complete data with the R1 recipe (replaces seed 42 for the report; seeds 1–4) | `f1_core.train`, 200 epochs; same split; Kaggle CPU |
| RP2 | **k per seed**: `p3_levers.calibrate` (median q_i = 0.005 over the 15 development cases) on each seed's own model; rescore development / test / chb24 / Siena, arms frozen 0.005 (held-out) and L2f (final), stages detector / CPD / hybrid | a design correction decided **after** R1 results were seen (§12 11/11 14:50) — reported as such in the report |
| RP3 | demo model = the seed (1–4) with the lowest validation loss on the 3 validation patients | rule fixed in §12 11/11 23:10 before RP_RUN: `final_val` of the checkpoint json (the recipe's loss on the clean windows of chb10 / chb11 / chb22; no test data); ties within 1e-9 relative → the smaller seed |
| RP4 | missed-seizure / false-alarm analysis on the 8 test patients on the RP2 scores (definitions of `V9_RESULTS_SUMMARY.md`) | 4 seeds |
| RP5 | channel attribution (pre-registered A5 rules) on the RP2 models | 4-seed mean + per seed |
| RP6 | ASR contrast on the new scores | — |
| RP7 | web demo switched to the RP3 model (Claude Code, laptop), chb03 identity check, app run on the 8 test patients, timing | laptop |
| RP8 | hospital EEG with the RP3 model (laptop only; private data) | qualitative |
| RP9 | real-EEG figures with rules written before drawing (`REPORT_REVISION_PLAN.md` §4) | laptop |
| RP10 | `REPORT_NUMBERS.md`: every report number with its source file | after RP1–RP8 |

R2 (6 models) and R3 (6 partitions) are used as they are (one seed per model / partition, k per fold).

## 8 · Stage R4 — Track F analyses on the rerun

All analyses below use the R1 / R2 / R3 checkpoints and data. Scoring from a checkpoint takes ≈ 90 s per job
(`fit.json` score_s 86.8), so R4 needs no training.

### 8.1 F5a — offset: verification and diagnosis (first)

**Verification**, on every set: CV 6 partitions × GAE and MLP-AE out-of-fold; thesis system development / test /
chb24 / Siena, 4 seeds.
- Within the same run: SzCORE counts and onset/offset errors for detector, CPD and L6 hybrid boundaries.
- Paired differences hybrid − CPD with patient-bootstrap CIs (unit = subject, B = 10,000):
  - per-patient sensitivity, FP/day, F1;
  - seizures lost / gained and false alarms changed (counts);
  - median |onset| and |offset| error (pairs resampled by subject).
- No pass/fail threshold. Stated plainly: the hybrid's error medians were already seen on every set of the record
  (§2); what is new is complete data, the CV models, detection counts and CIs.

**Error definition:** `E18.match_errors` (reference seizures matched by detector events; the same pairs for every
boundary set), as in the record; split references (SzCORE > 300 s) reported beside it.

**Diagnosis (drives F5b):**
- **D1 — bias:** signed onset and offset errors per method and set (median, IQR, share late).
- **D2 — where the error comes from:** errors by event type:
  - CPD accepted vs fallback;
  - event > 300 s;
  - detector event made of ≥ 2 runs merged at 90 s;
  - reference duration < 20 s / 20–60 s / > 60 s;
  - reference > 300 s.
- **D3 — post-ictal profile.** For every caught seizure: the unsmoothed final score and the member-mean robust-z from
  −120 to +180 s around the **annotated offset** (and around the onset, as control), relative to the patient's
  pre-onset level (median of −300 … −60 s). Per patient: median curve; the time after the annotated offset until the
  score returns inside the pre-onset IQR ("return time").
- **D4 — where CPD puts the offset.** Position of CPD's second change point relative to the annotated offset and to
  the return time of D3. Does CPD end at the seizure's end or at the end of the post-ictal change?
- **Figures:** each is drawn from committed result files. Real-EEG panels are selected by a rule written in the figure
  script before drawing (e.g. per set: the seizure with the median offset error and the one with the largest late
  error).

### 8.2 F5b — fixing the offset (after F5a; families approved by the author before running)

- **Families** are chosen from the F5a diagnosis and put to the author with the evidence. Examples, not decided:
  - kernel CPD with an extra post-ictal segment, i.e. one method for onset and offset with the right number of
    states (author 06/11: one method for both boundaries is preferred when the diagnosis supports it);
  - a penalty-selected number of change points;
  - CPD on the 18-channel trajectory with the long-event guard (best offset on development in the record, E20a, but it
    lost sensitivity);
  - a hysteresis rule.
- **Selection by nested CV:**
  - for each partition and outer fold, every candidate configuration (full grid) is scored on the **training cases**
    of that fold (inner), and the best is chosen by median |offset| error under the constraint "no seizure lost in
    the inner cases";
  - the chosen configuration is applied to the **held-out cases** (outer);
  - repeated over the 6 partitions (GAE and MLP-AE).
- **Report:** outer-fold paired differences vs CPD and vs the hybrid, with CIs.
- **One final external check** on Siena (+ chb24) with the configuration chosen on all CHB-MIT cases.
- **Adoption** into a system version is the author's decision after the thesis is complete.

### 8.3 F3 — why message passing adds false alarms

**Hypothesis.** The score uses the 6th / 9th / 12th-largest channel distances, so it rises only when many channels rise
together. Neighbour mixing in the GCN could spread a local (1–2 channel) event to its graph neighbours and raise those
order statistics.

**Why the MLP-AE serves as the local reference:** each channel's MLP-AE latent depends only on that channel's 30 inputs
(`model_cmp_core.mlp_D`). Data: R2 + R3 out-of-fold, 6 partitions, both models.

**Definitions:**
- per-channel robust-z Zc = `E16.rz` of D, exactly as in `e17b_latent_family.member`;
- recruitment R_X(t; τ) = number of channels with Zc ≥ τ;
- a background window is non-ictal, non-buffer, valid;
- a **focal** window: the MLP-AE's top channel Zc ≥ φ, and R_MLP(t; 2) ≤ 2;
- **neighbours** = channels with a nonzero entry in that window's top-k adjacency;
- a false-alarm event = a detector event at the own point that hits no reference (the record's PRE/POST rule);
- a GAE-only false alarm = one that overlaps no MLP-AE detector event.

**F3-A (exact identity, descriptive).** FA = T·(1 − s)/L, where:
- T = total detector event time;
- s = share of that time inside true events;
- L = mean false-alarm event length.

log(FA_GAE / FA_MLP) is split into a budget term, a seizure-share term and a fragmentation term, at the own point and
at the fixed 0.005 point (where the budget term is zero).

**F3-B (mechanism; full grid τ ∈ {1.5, 2, 3} × φ ∈ {3, 4, 5}):**
- **H1 spread:** on focal background windows, R_GAE − R_MLP > 0.
- **H2 along edges:** channels recruited by the GAE only are graph neighbours of the focal channel more often than
  channels not recruited, and more often than the input-level control (channels with 1 ≤ Zc_MLP < τ).
- **H3 consequence:** peaks of GAE-only false alarms fall in focal windows more often than background windows do.

Each statistic gets a subject-bootstrap CI per grid cell and per partition. **Reading:**
- "consistent support" if every grid cell's CI lies on the predicted side for H1–H3;
- "partial" if H1–H2 hold but not H3;
- otherwise "not supported".

**F3-C (descriptive).** Per-patient table of the 8 thesis test patients (the D12-F observation that the MLP-AE's
per-patient sensitivity is lower there).

### 8.4 Later

- **F4 graph insights** (rev 1 §5: I1 edge reconstruction map, I2 learned network vs anatomy, I3 spread, on both
  autoencoders).
- **F6 features for weak, short seizures** (rev 1 §7).
- Partitions 6–10 optional, not planned.

## 9 · Notebooks, code and order (all Kaggle CPU; smoke first; atomic resumable jobs; gates STOP)

| # | notebook | needs | does | runtime |
|---|---|---|---|---|
| 1 | `R0_SMOKE` | raw dataset + `v9-x3-fold1`/`3` | inventory + hashes of all files; G-stats on chb11 (whole earlier set), G-feat on its first 2 files + 1 file per worker in parallel; PN00 (x1); speed → projection | measured |
| 2 | `R0_CHB` (split by case if > 10.5 h) | 1 (+ `v9-x3-fold1`/`3`) | G-stats / G-feat all cases; complete chb11 / chb21; dataset `thesis-r2-chbmit-features` | ≈ 4–5 h est. |
| 3 | `R0_EXT` | 1 | chb24 + Siena features (x1 convention); dataset `thesis-r2-external-features` | ≈ 1 h est. |
| 2a | `R0_DIAG17` | 2 (v2 STOP) | diagnosis of the v2 STOP at chb17 (rebuild, localization, raw evidence, conditioning, scan of the 24 references); descriptive (§12 07/11 12:49) | ≈ 0.3–0.5 h est. |
| 4 | `R1_SMOKE` | 2, 3 | G-data, G-const, G-count; R1.0 gates on chb01 + chb03 and GE on PN00; G-vec on the thesis recipe; 2-epoch job per seed on the full training data (speed under load); R1.3 code path once on the 2-epoch models (not read); projection | measured (≈ 0.7–1.5 h est.) |
| 5 | `R1_RUN` | 4 (+ its committed output: hashes pinned) | G-data (pinned), G-const, G-count; R1.0 full + G-k + GE; G-vec; 4 seeds training (4 workers, resumable); k; scoring of all sets; counterfactual (committed checkpoints on the new data) | **measured 4.64 h** (07/11; §12 08/11 07:40) |
| 6 | `R2_SMOKE` | 2 (+ the CNN checkpoints committed) | G-data, D0′, G-const, G-vec, G-mlp; **R2.0** code-path gates on the earlier data; step timing (GAE, MLP-AE, CNN) with 4 concurrent workers; a small job per model type and one counterfactual job on the new data (not read); projection of R2_A / R2_B / R2_C | **measured 1.49 h** (08/11; §12 08/11 19:10; R2.0-cnn n/a, moved to `R2_C`) |
| 7 | `R2_A` / `R2_B` / `R2_C` | 6 (+ its committed output: projection) | GAE + MLP-AE folds (= R3 partition 0); IF + SVM + trees + counterfactual GAE / MLP-AE; **R2.0-cnn first**, then CNN + counterfactual CNN (≤ 2 workers); workers of R2_A / R2_B from the smoke's measured memory; resumable; cloned at commit `652ab62` | **measured R2_A 7.68 h, R2_B 5.29 h, R2_C 0.47 h** (08/11; §12 09/11 21:15) |
| 8 | `R3_p1` … `R3_p5` | 7 | one partition × both models (8 jobs, 4 workers); design proposed 09/11 (handback Part 10 §10.4), approved by the author 09/11 21:11 (R3-a no separate smoke, R3-b R3.0 gate + counterfactual, R3-c five notebooks in parallel); **built 10/11** (`src/r2_r3.py` sha `7dc1697c`, cloned at `fa69497`; every gate and R3.0 before any training; §12 10/11 11:50) | **measured p1 7.80 h, p2 8.20 h, p3 6.76 h, p4 6.93 h, p5 6.50 h** (10/11; §12 11/11 10:15); computed estimate was 8.7–9.0 h (R2_A's slowest measured CPU ms per step × each partition's training windows × 1.10, + 0.3 h) |
| RP | `RP_RUN` | 5 (committed R1_RUN output + R1_SMOKE's pinned hashes) | RP1–RP3: G-data (pinned), G-const-new, versions → mode, **RP.0** (R1 checkpoints reproduce `r13/run`), G-vec, G-val; seed 4 training (1 worker); k per seed + scoring of every set, 5 seeds; per-window scores (test, chb24, Siena); demo model; resumable; clone `c91719f` | **measured 3.02 h** (12/11; estimate was ≈ 4.5 h) |
| 9 | `R4_F35` | 5, 8 | F5a verification + diagnosis; F3-A, F3-B, F3-C | ≈ 1–2 h est. |
| 10 | `R4_F5B_*` | 9 + approval | nested CV of the approved families; Siena check | measured |

**Code:**
- new files are `src/r2_*.py` (core, notebooks builder, aggregate); stage R1: `src/r2_r1.py`, `src/r2_r1_make_notebooks.py`,
  `src/r2_r1_synthetic_test.py`, `src/r2_r1_aggregate.py`; stage R2: `src/r2_r2.py`, `src/r2_r2_make_notebooks.py`,
  `src/r2_r2_synthetic_test.py`, `src/r2_r2_aggregate.py`; stage R3: `src/r2_r3.py`, `src/r2_r3_make_notebooks.py`,
  `src/r2_r3_synthetic_test.py`, `src/r2_r3_aggregate.py`; stage RP (RP1–RP3): `src/r2_rp.py`, `src/r2_rp_make_notebooks.py`,
  `src/r2_rp_synthetic_test.py`, `src/r2_rp_aggregate.py` (`r2_core.py` stays as it was: the dataset descriptions cite
  its sha `902d15ad`);
- frozen and closed modules are imported read-only, never edited;
- every aggregate script is written and committed **before** its stage's results exist;
- each stage commits `results/r2/<stage>/` and gets tag `r2-<stage>`.

**Kaggle:** 4 accounts; CPU sessions ≤ 12 h; the author checks quota before each batch.

## 10 · Decisions

| # | decision | date |
|---|---|---|
| O1–O10 | rev 1 §8 decisions stand: R = 5 now; rule "rank blocks of 4"; seed r; GAE + MLP-AE only; checkpoints committed; Q&A use only after verification; secondary readings; packing one partition per notebook | 05/11 |
| D1 | rerun = re-execution of the frozen design; calibrations recomputed by their rules; no re-tuning | 06/11 |
| D2 | `results/r2/`, tags `r2-*`; committed results untouched; local caches archived after 09/11 | 06/11 |
| P1 | F5 = verification + diagnosis (F5a), then a fix chosen by nested CV (F5b); one method for both boundaries preferred when supported | 06/11 |
| P2 | no pass/fail decision thresholds fixed before a run; paired differences with CIs; full grids on selection data only | 06/11 |
| P3 | F3 read across the whole (τ, φ) grid | 06/11 |
| P4 | Kaggle CPU for the rerun (quota; bit-deterministic) unless a smoke shows a job cannot finish in a session | 06/11 |
| P5 | feature datasets public, owner Nhân2mm, shared by the four accounts | 06/11 |
| P6 | independent track until the thesis is complete; then the project is updated so it becomes the main work | 06/11 (replaced 11/11 by P7) |
| P7 | the track produces the final report's numbers (stage RP, §7b) before R4; one model in the report; seeds 1–4 without a main seed; k per seed; demo model by lowest validation loss; caches kept until the project ends | 11/11 |

## 11 · Record — rev 1 run on the earlier data copy (verified 06/11, chat D12-F)

Five notebooks, 40/40 jobs, GPU T4 x2, every gate PASS. GAE CV over 6 partitions:
- 0.736 ± 0.012 at 27.3 ± 1.1 FP/day;
- 8 test patients 0.575 ± 0.013.

MLP-AE − GAE: ΔF1 > 0 in 6/6, +0.075 [+0.034, +0.121]; Δsensitivity −0.009 [−0.086, +0.062]; ΔFP/day −8.1
[−11.0, −5.3].

Source: `results/f1_repcv/`, S18 §18.8. These numbers remain the verified Q&A numbers until R3 is verified (R3 verified 11/11, §12: same verdicts; GAE 0.733 ± 0.011, ΔF1 +0.077 [+0.038, +0.120], 6/6 — research numbers, not Q&A numbers unless the author decides). They are
not deleted when R3 replaces them for research.

## 12 · Change log

| when | change | reason | seen results? |
|---|---|---|---|
| 05/11 08:45 | rev 0 draft | author: future research track; cô 04/11 | no |
| 05/11 12:30 | rev 1 fixed (see git) | chat D12-F | no |
| 05/11 13:30 | device GPU T4 x2 by the rev 1 rule (CPU 4.9 % faster < 10 %) | smoke timing | no |
| 06/11 07:40 | F1/F2 results read on the earlier copy; verdict F2 "stable advantage of the MLP-AE" | runs finished | yes (record, §11) |
| **06/11 10:38** | **rev 2:** independent track; Stage R (R0–R3) on complete data before Track F; D1, D2, P1–P6; F5 split into F5a / F5b with nested CV; no pre-fixed decision thresholds; F3 grid reading; device CPU for the rerun; §2 corrections below | five files missing from every earlier run (§1); author decisions 06/11 | no new result; the hybrid medians of §2 were already in the record |
| 06/11 13:25 | **R0 implementation (D14-F, `src/r2_core.py`):** (a) the record code is called verbatim (`compute_subject_stats`, `count_windows`, `c1b.build`, `v9_x3_build_chb24.build`, `x1_external.build_subject`); only their path globals are pointed, inside each worker, at two symlink views of the verified files (`complete`; `earlier` = complete minus the five files); (b) G-stats also checks the window counts and ratio of `stats.json` exactly; chb24 (no committed stats) is proven by G-feat; (c) G-feat reference = `v9-x3-fold1` + `v9-x3-fold3`; file and skipped-file lists exact; `zgamma_raw` descriptive; (d) the chb11 / chb21 complete builds are queued in the same worker pool after the gate jobs; they are written and reported only after every gate passed; (e) external files named `{case}_lf.npz` (x1's `chb03_lf` convention), because a second `chb24.npz` would be matched by name by `model_cmp_core.locate_all` / `locate_earlier`; their `meta` adds the label-free mean / SD; (f) `r0_data/` gets one sub-folder per notebook; (g) smoke scope as in §4 Runtime; (h) summaries: chb01–23 from the committed `data/summaries` (what the record read), checked equal to PhysioNet's; chb24 from the verified copy; (i) Siena workers per subject 4, or 2 when a file is longer than 6 h (memory only; results do not depend on it); (j) inventory checks against the record are reported (PASS / DIFF); only the five files of §1 are required (STOP) | implementation of §4 on the actual code paths; name collision found while reading `model_cmp_core.py` | no (synthetic test data only) |
| 06/11 18:40 | **R0_SMOKE read + bug fix (D14-F):** smoke (`r2_core` sha `634dc095`) — every R0.1 check and every gate PASS (G-stats chb11 difference 0, counts exact; G-feat chb11 6 files: flags exact, f7 ≤ 4.8e-7, bp5 ≤ 1.8e-7, adjacency 0.04 %; PN00 hours and non-ictal hours = x1 record); one chb02 EDF absent from the Kaggle copy, taken from PhysioNet (sha256 equal); the five files present on Kaggle; projection R0_CHB 7.37 h / R0_EXT 0.71 h (computed) → R0_CHB not split (rule §4). **Bug:** `projection()` produced numpy booleans (parallel slowdown 1.3 > 1 made every term a numpy scalar) and its log line raised `TypeError`, so the END cell (measured runtime) did not run; `projection.json` was written with `"False"` as a string. Fix (sha `7191ad11`): one JSON encoder for numpy scalars in every dump and log line; the parallel rate stored as `float`; synthetic test extended with slowdown > 1. No gate, feature or statistic changes; the smoke is not rerun | bug found by the author in the smoke log | yes: smoke outputs (data preparation only, no research result) |
| 07/11 06:10 | **R0_EXT read; R0_CHB v1 STOP and fix (D14-F):** R0_EXT (`7191ad11`) complete: 15 cases, every check PASS, hours and non-ictal hours = x1 record for 15/15 (Siena 141.0056 h), measured 0.563 h. R0_CHB v1 stopped after 94.5 min at chb07: G-stats chb06 and chb07 difference 0, G-feat chb06 PASS; the comparison code raised `KeyError` because the earlier `chb07.npz` (record file, copied unchanged by `v9_x3_stage_uploads.py`) has no `skipped_files` entry although every committed `c1b` version writes it (cause not known; to check on the laptop with `docs/PROVENANCE_V2.md`). Not a gate failure. **Changes (sha `01c068f8`):** (a) G-feat compares the skipped-file list only when the reference holds it; otherwise it is reported n/a with the new list, and the file list (exact) carries the check; keys present in only one file are reported; (b) **reference preflight** before any build: every earlier `.npz` located, the required keys (`files`, `file_idx`, the four flags, `f7`, `bp5`, `adj`) present (STOP otherwise), sha256 compared with `docs/PROVENANCE_V2.md` (reported, not a stop; chb24 has no committed sha); (c) **resumable R0_CHB:** a finished job whose gates passed is kept in `r2/r0_jobs/` (npz + stats + sha256, pinned commit, build version); a later version with that output attached reuses it and recomputes its gates with the current code; job folders are removed once the dataset is written; (d) synthetic test: reference without `skipped_files`, provenance report, resume after a STOP, preflight STOP; the test harness now re-imports `r2_core` per notebook (before, a notebook run after a deliberate STOP wrote into the previous run's folder, so the old "no dataset written" check was weaker than stated). No tolerance changed. R0_CHB is rerun in full (v1 kept no job). (e) Datasets are created on Kaggle from the notebook's output (no upload from the laptop), so each dataset also holds that notebook's `r2/r0_data/<tag>/` provenance folder beside the files of §3; R0_CHB's job folders are removed before the dataset is made. (f) the outputs received so far are committed: `results/r2/r0_data/smoke/` (the files the author downloaded; runtime 28.5 min read from the last log line, END cell not run), `ext/` (complete), `chb_v1_stop/` (record of the stop) | crash found by the author in the R0_CHB log | yes: R0_EXT outputs and R0_CHB v1 gates for chb06 / chb07 (data preparation only) |
| 07/11 12:49 | **R0_CHB v2 STOP at chb17 → G-feat read on the chain windows (author decision, D14b-F), fixed before the chb17 diagnosis is seen.** v2 (`01c068f8`) stopped at chb17: G-stats PASS (difference 0); file list, window count, the four flags and `file_idx` exact; f7 one finiteness flip (max \|diff\| inf), bp5 3.84, adjacency 0.92 % (tolerances 1e-3, 1e-3, 0.5 %); the 20 cases that finished before passed both gates. Evidence before the diagnosis: chb17 has 534 signal-loss windows (record `results/continuous_eval/loss_decomposition/categories.csv`); `chb17b_69.edf` is flat-lined (raw constant; filtered ≈ 1e-22 V; record `results/continuous_eval/chb17b_69_inspect.txt`: values there are numerically undefined and hardware-dependent); the v2 log warns of catastrophic cancellation in the kurtosis at that file; `c1b_build_trainset` refuses non-finite f7 only outside signal-loss windows; every downstream path drops signal-loss windows (`train_gae_v2` clean mask, `p2_scalars` / `e16` `ok` mask with median fill, `model_cmp_core.make_ctx`, `v9_x3_cv_eval`). **Decision:** the f7 / bp5 / adjacency tolerances (unchanged) are read on the windows the chain uses (not `is_signal_loss`); file list, window count, skipped files, the four flags and `file_idx` stay exact on **all** windows; the all-window reading (pre-registered, §4) and the signal-loss windows are reported beside it in `gates.json`; applies to all 24 cases (the gates of the 20 reused jobs are recomputed). Any difference beyond tolerance outside the signal-loss windows fails the gate (STOP) and goes back to the author. Not chosen: keep all windows (chb17 cannot pass on a machine other than the one that built the record; R0 blocked); NaN in signal-loss windows (changes the record format, against D1). **Code (`r2_core` sha `902d15ad`, `r2_diag` sha `21c1d572`):** (a) `compare_features` reads three window sets (all / chain / signal_loss) from one per-window difference table; the all-window keys keep the v2 names and values (unit-tested equal to the v2 code); status = `GFEAT_SCOPE = "chain"`; (b) **bug fix found while preparing the resume:** `locate_earlier` accepted any `{case}.npz` under the inputs except `thesis-r2` paths; with a previous output attached, the job copy `r2/r0_jobs/<case>_earlier/<case>.npz` sits beside the reference and, being of equal size when the keys match, could be taken as the reference (a build compared with itself). Now only files inside a `v9-x3-fold*` input and never under `r0_jobs` (v2 attached no previous output, so its gates are not affected); (c) one-case inventory: the `committed_summary_equal` column is created as object (pandas 3 refused a bool into a float column; values unchanged); (d) new `src/r2_diag.py` + notebook `R0_DIAG17` (descriptive: rebuild of chb17 with the record code and the committed stats, per-window localization, every non-finite cell, raw evidence, conditioning test — raw × (1 + 2⁻⁴⁰) after replicating the record filter bit-equal —, scan of the 24 references); (e) synthetic test extended (a reference differing only inside signal-loss windows → all-window FAIL, chain PASS, R0_CHB PASS; the diagnosis localizes exactly those windows and the non-finite cell; a difference outside → STOP; a resumed run compares with the fold reference) — ALL PASS. No tolerance changed; record code unchanged (pinned `235682a`); builds unchanged (`r0-build-1`), so v3 reuses the 20 jobs of v2 | v2 STOP at chb17 | yes: v2 gates (data preparation only); the chb17 diagnosis not yet run |
| 07/11 14:26 | **R0_DIAG17 read (D14b-F; commit `09b976a`; measured 0.22 h):** chb17 rebuilt with the record code and the committed stats; every f7 / bp5 difference beyond 1e-3 (528 / 527 windows) lies in the 534 signal-loss windows, all in `chb17b_69.edf`; outside them f7 ≤ 9.5e-7, bp5 ≤ 3.6e-7, adjacency 0.045 % (the 20 passed cases 0.033–0.046 %) → G-feat all windows FAIL, chain windows PASS. Signal-loss windows: raw SD ≈ 5e-23 V, filtered ≈ 5e-22 V; record filter replicated bit-equal; raw × (1 + 2⁻⁴⁰) moves their features by O(1) (f7 median 28.6) vs ≤ 1e-6 elsewhere → their values are set by rounding. The non-finite cell: window 374 of `chb17b_69`, channel 10, kurtosis (record NaN, Kaggle −0.945). Reference scan: signal-loss windows also in chb01 (1), chb04 (2), chb07 (4), chb09 (3) (passed v2 on all windows) and chb12 (1, still to run). The diagnostic's per-window label `beyond_tolerance` counts any differing adjacency entry (2,697 windows outside signal loss); the gate's adjacency tolerance is a fraction over the case, so 0 windows outside are beyond tolerance — label stated, output not changed. **Condition of the 12:49 decision holds → R0_CHB v3 runs unchanged (r2_core `902d15ad`)** | diagnosis output | yes: R0_DIAG17 (data preparation only) |
| 07/11 15:48 | **R0_CHB v3 read; stage R0 complete (D14b-F; commit `8262810`; `r2_core` `902d15ad`; measured 1.02 h on 4 workers: inventory 126 s, reference preflight 87 s, jobs 3,471 s; 54.0 s per hour of EEG per worker):** 20 jobs of v2 reused, every reference a `v9-x3-fold*` path (24/24); 6 jobs run (chb08, chb12, chb16, chb17 earlier; chb11, chb21 complete). G-stats PASS for the 23 cases with a committed stats file (chb24 n/a); **G-feat PASS 24/24 under the chain scope**; the all-window reading PASS 23/24, FAIL only chb17 (its 534 signal-loss windows, row 14:26). Chain readings over the 24 cases: f7 ≤ 2.3e-5, bp5 ≤ 9.5e-7, adjacency 0.033–0.046 %. Signal-loss windows: chb01 1, chb04 2, chb07 4, chb09 3, chb12 1, chb17 534. R0.3 (descriptive): chb11 31 → 35 files, 27,713 → 31,313 windows, ictal windows 204 identical, clean windows 14,228 → 16,067, channel SD change −4.0 … +9.3 % (median −3.3 %); chb21 32 → 33 files, 28,646 → 29,546 windows, ictal windows 53 identical, clean 11,051 → 11,619, channel SD −0.8 … +3.2 % (median +1.4 %); channel means change < 0.07 % of the SD. Dataset folder `thesis-r2-chbmit-features` written (24 `{case}.npz` + `{case}_stats.json` + `inventory.csv`; chb11 / chb21 = complete builds, the other 22 = the gated builds). Next: publish the dataset (P5), tag `r2-r0`, then R1 | v3 output | yes: R0 data preparation (no research number) |
| 07/11 16:40 | **R1 implementation (D15-F, `src/r2_r1.py`; written and tested on synthetic data before any R1 result):** (a) new files `src/r2_r1.py`, `src/r2_r1_make_notebooks.py`, `src/r2_r1_synthetic_test.py`; `r2_core.py` is imported unchanged (sha `902d15ad`, cited by the dataset descriptions); (b) R1_SMOKE clones tag `r2-r0` (`1b83b03`: the record code is identical to `235682a`, plus R0's committed outputs); R1_RUN will clone the commit holding R1_SMOKE's output and pin the data hashes to it; (c) **new gate G-data**, because R0 recorded no hash of the dataset files it wrote: every file of both datasets present and hashed (`data_sha256.csv`), statistics and window counts = R0's committed outputs, flags / `file_idx` / file lists of the 22 gap-free cases = the earlier `.npz`, R0's G-feat re-read (chain scope) on the cases a notebook reads; STOP on any difference; (d) **distances** from `x1_external.model_outputs` verbatim (`p2_dump_seeds23.run_model`, PyG per-window batches; its checkpoint folder pointed per worker), with the record's convention per set: CHB-MIT D stored float32 and read as float64 (the e14 / p2_seeds / p2_test dumps), external float64 (the x1 run); (e) **bookkeeping:** CHB-MIT = the fields of `e22_test_oneshot.test_context` built from the `.npz` and the stored D (no dump file); external = `x1_external.make_ctx` verbatim; the CHB-MIT bookkeeping was proven equal to `p2_scalars.subject_context` and `test_context` on synthetic caches (every field, and identical `run_budget` rows), and is proven on real data by R1.0; (f) **one scoring path for every set:** `p3c_freeze.run_budget` for the 4 recorded arms (frozen 0.005; L2 0.0025–0.02; L2f 0.005–0.02; S 0.0075–0.02, 0.0075 read from `freeze.json`, not re-selected), stages detector / cpd / hybrid, because `e23.evaluate` and the x1 path give no hybrid counts; R1.0 checks that its detector / cpd rows on test equal e23 (L2f, S) and look 6 (frozen); (g) **R1.0 scope** wider than §5 named (stricter): every arm of `p3c_freeze`, both e23 points, look 6 (`e22`), G-k (1e-6 relative: library versions, model-comparison precedent); integers exact, float columns relative 1e-9, error pairs exact and in order; GE as pre-registered (|Δtp| ≤ 1, |Δfp| ≤ 2; exact rows counted); G-const 1e-9 relative, G-count exact; (h) **smoke scope:** chb01 (development) added to chb03 + PN00 — the only way to exercise the development rows before the full run (e23's own R1 gate used chb01); the 2-epoch job runs on the full training data, 4 seeds in parallel, to measure speed under load; the R1.3 code path runs once on those 2-epoch models (chb01 + chb10 for k, chb03, PN00), written under `r13/path_check`, never read; (i) **G-vec reference** = `train_gae_v2.main` with its own `--smoke` (chb01, first 2,000 clean windows, 2 epochs, constants from the 12 training patients, validation loss logged), called in the same process (same threads) on the view of the new dataset, vs `f1_core.train` on the same windows; (j) **training:** `f1_core.train` (closed) unchanged, one spawned worker per seed, 1 thread, CPU; f7 constants by `train_gae_v2.norm_constants` on the new data; expected training windows = committed counts with chb21 from the R0 diff (11,619), total 270,758 (computed), STOP otherwise; **validation loss computed once after the last epoch** (the record computed it every epoch, logged only; `f1_core.train` has no per-epoch hook); `train_gae_v2.sanity_auroc` verbatim; checkpoint in the record format (`gae_v2_clean_seed{s}.pt` + `.json`; the loss curve as CSV, not the record's `_loss.npz`, because `.npz` files are never committed) + `_DONE.json` (checkpoint sha256, code sha); (k) **resume:** finished seeds of an attached previous R1_RUN output are reused when the code sha and the checkpoint hash match; (l) **guard:** every record module must be imported from the pinned repository, STOP otherwise (the synthetic test found a spawned worker importing `x1_external` from another tree, which reads another `freeze.json`); (m) R1.3 rows are only written; they are read by an aggregate script committed before R1_RUN runs (next chat); (n) projection of R1_RUN = computed estimate from the smoke (largest per-case rate, the measured per-task worker start, slowest training job), split rule 10.5 h as in R0 | implementation of §5 on the actual code paths | no (synthetic data only) |
| 07/11 18:55 | **R1_SMOKE read (D15-F; output commit `f21d233`; `r2_r1` `b865507a`; clone `1b83b03`; Kaggle CPU 4 cores, torch 2.11.0+cpu, numpy 2.1.3, sklearn 1.6.1; measured 0.143 h):** every gate PASS — G-data (63 files hashed: 24 × 2 CHB-MIT + 15 external; statistics and counts = R0's outputs; R0's G-feat re-read on 13 cases: f7 ≤ 2.3e-5, bp5 ≤ 9.5e-7, adjacency 0.033–0.046 %); G-const (relative difference 0); G-count; **R1.0-dev** chb01 48 `p3c_freeze` rows + 112 error pairs, 0 differ; **R1.0-test** chb03 16 e23 rows + 55 error pairs, 8 look-6 rows, run_budget consistency, 0 differ; **GE** PN00 16/16 rows exact; **G-vec** maximum weight difference 0; 2-epoch jobs, 4 seeds: training windows 270,758 (= expected), 3,964 parameters, G2 PASS, 8.17 ms per step with 4 concurrent full-size jobs, load 9 s, validation + sanity 42 s, peak ≈ 3.2 GB per worker. Distances ≈ 1 s per hour of EEG per seed set (chb01 40.6 h: 37.8 s for 4 seeds); per-task worker start 24 s. **Projection of R1_RUN (computed): 4.62 h** (training 3.85 h, R1.0 0.25 h, R1.3 0.26 h) → one notebook. The R1.3 path check on the 2-epoch models wrote its files (not read) | smoke output | yes: R1_SMOKE (code-path gates and timing; no research number) |
| 07/11 18:55 | **Before R1_RUN (D15-F, `r2_r1` `76cbe51f`):** (a) **counterfactual added** (descriptive, scoring only): the committed checkpoints `data/models_v2` on the new data (CHB-MIT complete `.npz`, external R0.4 features), k recomputed by `p3_levers.calibrate` (`r13/cf`) and at the record's k (`r13/cf_krec`, same distances); reason: §5 asks that every difference be explained (chb11 / chb21 data, k, retraining randomness), which rerun vs record alone cannot separate; it runs after R1.3 and is skipped (noted) if less than 1 h of session is left; only functions added to `r2_r1.py` (`rescore`, `counterfactual`), no gated path changed since the smoke's `b865507a`; (b) **`src/r2_r1_aggregate.py`** written and tested before R1_RUN exists: gate **A0** — the per-patient metric (`e22_test_oneshot.metrics`) reproduces 23 locked numbers from the record files (held-out, final, Siena, chb24, development; PASS on the committed files, STOP on one changed count); gate **A1** — (15 + 8 + 15) × 4 × 4 × 3 rows per system, `n_ref` = the record's; self-check record − record = 0; tables: rows vs record (mapping e23 / x1 balanced → L2f, sensitivity → S, look 6 → frozen, localized → cpd), per-patient means per seed and 4-seed mean ± SD, paired subject bootstrap (B = 10,000, rng seed 0, subject's 4-seed mean) for rerun − record, data, k, new models (sensitivity, F1, FP/day), attribution beside the record's across-seed SD, per subject (role, data_changed), boundary errors; no threshold (P2); (c) R1_RUN built with its clone pinned at `f21d233` (holds the smoke's `data_sha256.csv`, so the data hashes are pinned); the notebook builder now builds each notebook only on request (`--smoke`, `--run COMMIT`): the committed R1_SMOKE notebook (`b865507a`) stays the record of what ran | §5 reading needs the split; aggregate before results (§9) | yes: R1_SMOKE gates and timing only |
| 08/11 07:40 | **R1_RUN read; stage R1 complete (D16-F; output commit `84c2a87`; `r2_r1` `76cbe51f`, clone `f21d233`; Kaggle CPU 4 cores, torch 2.11.0+cpu, numpy 2.1.3, sklearn 1.6.1; measured 4.64 h: training 3.90 h, distances + scoring 0.42 h (R1.0, run), counterfactual 0.26 h; smoke projection 4.62 h without the counterfactual).** Gates: G-data PASS (63 hashes = the smoke's; G-feat re-read on 21 cases); G-const relative 0; G-count; **R1.0-dev** 720 `p3c_freeze` rows + 987 error pairs, **R1.0-test** 128 e23 rows + 296 pairs, 64 look-6 rows, run_budget consistency: **0 differ**; **G-k** relative 0; **GE** 240 rows, 148 exact, max \|Δtp\| 1, \|Δfp\| 2 (the record's own cross-platform level, `results/v9_anatomy/siena14/gate.csv`); G-vec 0; training 4 seeds × 200 epochs, 270,758 windows, 3,964 parameters, G2 PASS (last training loss 0.01584–0.01590 vs record 0.01583–0.01586; validation loss 0.0208 vs 0.0212, the validation set changed with chb11). **Aggregate** (`src/r2_r1_aggregate.py`, unchanged, run in the chat container with numpy 2.5.3 / pandas 3.0.5): **A0 PASS** (23 locked numbers reproduced from the record files), **A1 PASS**, self-check PASS; 1,152 record rows matched; output `results/r2/r1_system/run/aggregate/`. **k:** rerun 3.7852 vs record 4.0677; cf (committed models on the new data) 4.0660 → the data change barely moves k, the drop comes from the new seed-42 model. At the new k the other three new seeds have median q_i 0.0056–0.0065 on development (record seeds at the record k: 0.0045–0.0053, computed from `q.csv` and `calibration.json`) → seed 42 is the lightest-tailed of the four new models, and k (calibrated on seed 42 only, by design) passes that to all seeds. **Per-patient means, CPD stage, 4 seeds, rerun vs record:** development frozen 0.811 @ 19.4 vs 0.822 @ 19.2 FP/day, L2f 0.827 @ 26.0 vs 0.832 @ 23.2; test frozen (held-out system) 0.475 ± 0.013 @ 25.7 ± 1.0 vs 0.498 ± 0.010 @ 23.8 ± 1.3 (seed 42: 23/76, 0.460 @ 26.3 vs 26/76, 0.508 @ 21.8); test L2f (final system) 0.575 ± 0.017 @ 32.3 ± 1.9 vs 0.567 ± 0.019 @ 28.7 ± 1.3 (seed 42: 36/76, 0.560 @ 31.0 vs 37/76, 0.577 @ 26.8); F1 −0.016 on both test arms; chb24 L2f 0.875 @ 32.4 vs 0.828 @ 28.4; Siena L2f 0.699 ± 0.057 @ 46.1 vs 0.633 ± 0.079 @ 41.0, F1 0.226 = 0.226. **Split (paired subject bootstrap, B = 10,000, CPD stage):** *data* (cf_krec − record) = complete chb11 / chb21 **plus** the float-level rebuild of every other case, which flips borderline windows as in GE: \|Δsensitivity\| ≤ 0.016 and \|ΔFP/day\| ≤ 0.6 on every set and both arms, CIs touching 0; *k* (cf − cf_krec): 0 except one development subject; *new models* (rerun − cf) = chb21's 568 added training windows and its new statistics + CPU tensor-loop training vs the record's GPU training + retraining randomness (at L2f also the new model's own k): frozen arm (k-free) development Δsensitivity −0.003 [−0.022, +0.018], ΔFP/day +0.08 [−0.71, +1.02]; test Δsensitivity −0.019 [−0.053, +0.005], ΔFP/day +1.91 [+1.30, +2.47], ΔF1 −0.014 [−0.025, −0.004]; Siena Δsensitivity +0.046 [−0.032, +0.143], ΔFP/day +0.03; L2f arm ΔFP/day +2.5 (development), +3.5 (test), +4.5 (chb24), +5.5 (Siena), Δsensitivity +0.003 … +0.054 (CIs include 0), ΔF1 −0.020 … −0.007. Scale of retraining alone (computed: the record's across-seed SD × √(2/4) for a difference of two 4-seed means): test frozen sensitivity ≈ 0.007, FP/day ≈ 0.95 → the test new-model steps are ≈ 2–3 times that scale. The bootstrap resamples patients, not training runs, so a CI that excludes 0 does not show a difference beyond retraining randomness; one rerun of 4 seeds cannot separate the training-data change from platform and retraining. **Per subject:** chb21 (training patient whose data changed) sensitivity 0.44 → 0.31 (data) → 0.25 (new models), 4-seed means; chb11 frozen FP/day 14.1 → 16.0 (data); seed-42 held-out −3 seizures = chb03, chb06, chb14 −1 each (new models), chb16 −1 (data), chb13 +1. **Boundaries** (median \|onset\| / \|offset\|, s): test L2f CPD 12 / 24 (record 12 / 24), hybrid 12 / 16 (= record); development L2f CPD 8 / 16 (record 4 / 16); Siena L2f CPD 20 / 32 (record 20 / 28), hybrid 20 / 20 (= record); chb24 unchanged. **Reading (descriptive, P2):** re-executing the frozen thesis system on complete data gives the same picture: sensitivity changes −0.023 … +0.066, more false alarms (+0.2 … +5.1 FP/day), F1 within 0.018, boundary errors unchanged; the completed data alone moves sensitivity by ≤ 0.016, so the five missing files drive no thesis result. Design observation (not data): k is calibrated on the seed-42 model only and applied to all four seeds, so how typical seed 42 is sets the other seeds' budgets; noted for the system design after the thesis, nothing changed now. No number replaces a locked number (R93, R98) | R1_RUN output | yes: R1 results |
| 08/11 09:30 | **R2 implementation (D16-F; author approved 08/11 07:54: R2-a SVM code-path gate on fold 1 only, R2-b CNN checkpoints committed and gated, R2-c counterfactual, R2-d R2_SMOKE → R2_A ∥ R2_B ∥ R2_C on Kaggle CPU; written and tested on synthetic data before any R2 result):** (a) new files `src/r2_r2.py`, `src/r2_r2_make_notebooks.py`, `src/r2_r2_synthetic_test.py`, `src/r2_r2_aggregate.py`; `model_cmp_core.py`, `f1_core.py`, `r2_core.py` imported unchanged; a guard stops if any of them comes from outside the pinned repository; (b) **views**: symlink folders `earlier` (the record `.npz`, `r2_core.locate_earlier`) and `new` (`thesis-r2-chbmit-features`); `model_cmp_core`'s npz registry is pointed at one view per job (`locate_all` on the view; its cache cleared); (c) **fold constants**: the comparison's recorded rule is "the fold's own training constants"; on the new data they are recomputed by `f1_core.fold_constants` (= `v9_x3_train_fold`) and handed to the closed code through `model_cmp_core.fold_meta` for the duration of a job (`patched_meta`), so `node_input`, `sup_train`, `sup_score` and `if_D` run unchanged; Isolation Forest therefore uses the new fold-1 constants (affine standardisation; the forest is affine-invariant); (d) **expected counts**: the committed fold metas with chb11 16,067 and chb21 11,619 (R0 diff); folds 1–3 train on +2,407 windows, fold 4 (chb11 and chb21 held out) on the same 356,641; (e) **gates**: G-data = the 24 new `.npz` sha256 equal to R1_SMOKE's pinned `data_sha256.csv`; D0′ as §6 (gap cases: added file names and window count = the R0 diff, no ictal window in them, non-ictal hours = record + their non-signal-loss windows; clean windows = expected for all 24); G-const, G-vec, G-mlp = `f1_core` gates on the earlier data; **R2.0** on the earlier data with the committed models: GAE = `f1_core.gate_GG0` (exact), Isolation Forest 4 folds, trees retrained 4 folds, linear SVM retrained fold 1 = `results/model_cmp` rows exactly (tp, fp, n_ref per subject / point / stage; own-point k within 1e-6 relative; the record ran on Kaggle CPU with the same library versions), committed MLP-AE and CNN checkpoints scored on CPU within \|Δtp\| ≤ 1, \|Δfp\| ≤ 2 per row (GE's tolerance; those models were trained and scored on a GPU), exact rows counted; CNN reported n/a if its checkpoints are absent; (f) **jobs**: atomic, one spawned process each (fresh memory, measured peak), DONE.json last, reused from an attached previous output when the code sha matches; GAE / MLP-AE = `f1_core.train` + `f1_core.run_fold` (200 epochs, seed 42; windows = expected, 3,964 parameters, G2); IF / trees / SVM / CNN = `model_cmp_core.run_fold` with `sup_train` / `if_D` unchanged; outputs merged into `model_cmp/` in the comparison's format; (g) **counterfactual** (R2-c): committed GAE, MLP-AE, CNN fold models with their committed constants on the new data, k recomputed (`cf/`); (h) **R2_SMOKE** clones the tag `r2-r2-code` (author: delivery + CNN checkpoints committed, then tagged); timing of the three trained networks with 4 concurrent workers; small jobs of every model and one counterfactual fold on the new data (written, not read); projection: autoencoders from ms/step × steps, SVM / trees from the measured fold-1 / R2.0 seconds × the record's fold ratios × the new training sizes, CNN from ms/step, workers of R2_B / R2_C from the measured peak memory (0.8 × RAM / peak); R2_A / R2_B / R2_C are built afterwards, cloned at the commit holding the smoke output; (i) **aggregate** `src/r2_r2_aggregate.py`: A0 = the closed `model_cmp_aggregate.py` run unchanged on `results/model_cmp/raw` reproduces the committed summary, paired_bootstrap, matched_rate, complementarity and transfer tables (relative 1e-9; checked in the container: PASS) and the S18 §18.6 numbers; A1 = 6 models × 24 cases × 2 points × 2 stages, n_ref = record, counterfactual complete; then the pre-registered A–F run unchanged on the rerun, model − GAE (record beside rerun), rerun vs record and its split with the paired subject bootstrap (B = 10,000, rng 0, chb01 + chb21 one unit), per subject (chb11 / chb21 flagged; thesis test patients marked), own-point k per fold, seizures caught record vs rerun; no threshold (P2); analysis D keeps the record's seizure descriptors (earlier copy; stated); (j) **synthetic test** (container, 1110 s, ALL PASS): A0 on the real record; N1 the counterfactual path on the new view reproduces the generated record exactly on fold 4 (gap-free training: same k, gap-free held-out rows equal); N2 `patched_meta` in force inside a job and restored after; R2_SMOKE every gate PASS; negative paths STOP (one IF record tp + 1 → R2.0-if; one MLP record fp + 3 → R2.0-mlp; a pinned hash → G-data; a record n_ref → D0′); R2_A / R2_B / R2_C complete; R2_A resumed reuses 8 jobs with byte-identical rows; the aggregate's A0 / A1 PASS and every table written | approved R2 design (handback §7.5–7.6) | no (synthetic data only) |
| 08/11 19:10 | **R2_SMOKE read; R2.0-cnn moved into R2_C (D17-F; output commit `652ab62`; `r2_r2` `542968bb`; Kaggle CPU 4 cores, 33.7 GB, torch 2.11.0+cpu, numpy 2.1.3, sklearn 1.6.1; measured 1.491 h):** (a) **clone:** the smoke cloned the tag `r2-r2-code` while it pointed to `e2f9540` (before the R2 commit `0267485`); `run_meta.json` records `e2f9540`. Between `e2f9540` and `652ab62` only new files changed (`src/r2_r2*.py`, `R2_SMOKE.ipynb`, the four CNN checkpoints, this plan), so every closed module the smoke ran is the one the R2 runs use; the author re-pointed the tag to `0267485` on 08/11 18:54; from now on run notebooks pin a commit hash, never a tag. (b) **gates** (against handback §8.4): G-data PASS (24 hashes = R1_SMOKE's); D0′ PASS (chb11 + 4 files, 31,313 windows, 0 ictal, non-ictal 30.57 → 34.57 h; chb21 + 1 file, 29,546 windows, 0 ictal, 31.77 → 32.77 h; clean windows = expected for 24); new fold constants: folds 1–3 move ≤ 0.20 % (relative), fold 4 ≤ 8.6e-12, training windows 280,187 / 366,878 / 329,383 / 356,641 = expected; G-const difference 0; G-vec and G-mlp exact 0; **R2.0**: GAE GG0 PASS (48 rows + 185 flags), Isolation Forest 96/96 rows exact (k 0), trees 96/96 (k ≤ 2.4e-11), linear SVM fold 1 20/20 (k 0), MLP-AE 96/96 exact (CPU = the GPU record), **CNN n/a** (checkpoints absent in the clone). (c) **measured:** ms per step with 4 concurrent workers GAE 8.61, MLP-AE 4.06, CNN 15.76 (the four workers' CNN times agree to the clock's resolution, an oddity of that measurement; the R2_C estimate has a wide margin either way); R2.0 seconds: SVM fold 1 4,558 (peak 9.3 GB), trees 908–1,037 (≤ 5.2 GB), IF 1,161, GAE GG0 580, MLP-AE 71–83 per fold; projection (computed): R2_A 9.0 h (4 workers), R2_B 6.4 h (2 workers), R2_C 1.0 h (4 workers, from a formula, not a measurement: the CNN peak memory was never measured, `peak_gb.cnn` = 0). (d) **change before any R2 result (author's proposal, accepted):** `R2_C` runs **R2.0-cnn first** — the four committed CNN checkpoints must be in the pinned repository (else STOP; sha256 written to the gate), scored on the earlier data by `r2_r2`'s own path (`r20_specs` cnn jobs, `_compare` with the 09:30 tolerance |Δtp| ≤ 1, |Δfp| ≤ 2 per row, n_ref exact, exact rows counted); any failure STOPs the notebook before a CNN training job exists; R2_A and R2_B do not depend on it and run in parallel. (e) **R2_C on at most 2 workers** (estimated CNN training peak ≈ 6–7 GB from the trees' measured 5.2 GB plus the CNN's two extra copies of X; 4 workers would leave almost no margin, and a worker killed for memory makes the pool wait to the session limit); a job runs alone in its process on one thread, so its result does not depend on the worker count; computed R2_C estimate ≈ 1.8 h. (f) `src/r2_r2.py` **unchanged** (sha `542968bb` = the smoke's); changed: `src/r2_r2_make_notebooks.py` (R2_C gate cell, worker cap, runtime text from the smoke's projection), `src/r2_r2_aggregate.py` (A1 also requires counterfactual CNN rows, G-data and D0′ PASS and no failed gate in every run folder, and R2.0-cnn PASS in the folder holding the CNN rows), `src/r2_r2_synthetic_test.py` (R2_C gate first, 2 workers; negative paths: CNN record fp + 3 → STOP, `cnn_fold3.pt` absent → STOP, no CNN training job; aggregate without R2.0-cnn → STOP A1). (g) `R2_A`, `R2_B`, `R2_C` built with `--runs 652ab62` | R2_SMOKE output; author's proposal for the CNN gate | no (gates and timing only; no R2 research number) |
| 09/11 21:15 | **R2_A / R2_B / R2_C read; stage R2 complete (D17-F; outputs `871bcf5`, `b5cbbe1`; clone `652ab62`, `r2_r2` `542968bb` in all three; Kaggle CPU 4 cores, torch 2.11.0+cpu, numpy 2.1.3, sklearn 1.6.1):** (a) **gates:** G-data and D0′ PASS in all three; G-const, G-vec, G-mlp PASS (R2_A); **R2.0-cnn PASS: 96 rows, 96 exact, max \|Δtp\| 0, \|Δfp\| 0, own-point k relative 1.4e-7; the four checkpoint sha256 in the gate = the committed `results/model_cmp/ckpt/cnn_fold1–4.pt`** (checked in the clone); 33 jobs done, 0 failed (R2_A 8 trainings; R2_B Isolation Forest, 4 trees, 4 SVM, 8 counterfactual; R2_C 4 R2.0, 4 CNN, 4 counterfactual); every training: expected windows (GAE / MLP-AE 280,187 / 366,878 / 329,383 / 356,641; CNN 547,722 / 648,671 / 577,882 / 613,701), parameters 3,964 / 6,081, G2 PASS, full epochs. (b) **measured:** R2_A 7.68 h (GAE 4.2–5.6 h, MLP-AE 1.9–2.8 h per fold, 8.64–8.69 and 3.86–4.31 ms per step), R2_B 5.29 h (SVM 1.6–2.9 h per fold, peak 11.1 GB; trees 11–14 min, 5.4 GB), R2_C 0.47 h (CNN 10.9–12.9 min per fold, 9.6 ms per step at batch 256, peak 4.6 GB — below the 6–7 GB estimate of 08/11 19:10; the smoke's 15.76 ms was measured under 4-way load). (c) **aggregate** (`src/r2_r2_aggregate.py` unchanged since `8c870fc`; container numpy 2.5.3, pandas 3.0.5; 36 s): **A0 PASS, A1 PASS** (counterfactual for cnn, gae, mlp; R2.0-cnn PASS in the folder with the CNN rows). Output `results/r2/r2_cv/aggregate/` (22 files). (d) **reading** (per-case means, own label-free point, after CPD; record → rerun): GAE 0.735 / 0.203 @ 28.4 → 0.737 / 0.208 @ 27.8 (sensitivity / F1 @ FP/day); MLP-AE 0.711 / 0.273 @ 20.2 → 0.735 / 0.284 @ 20.0; Isolation Forest 0.680 / 0.212 @ 24.1 → 0.688 / 0.213 @ 24.1; linear SVM 0.626 / 0.163 @ 33.7 → 0.632 / 0.162 @ 32.8; trees 0.755 / 0.221 @ 35.2 → 0.736 / 0.200 @ 36.6; CNN 0.777 / 0.218 @ 35.1 → 0.754 / 0.218 @ 33.4. **Analysis B (pre-registered, model − GAE, paired subject bootstrap, 23 units):** MLP-AE F1 +0.070 [+0.026, +0.117] → **+0.076 [+0.036, +0.122]** (18 wins / 6 losses; without chb05 +0.061), sensitivity −0.002 [−0.064, +0.063]; linear SVM sensitivity −0.109 [−0.207, −0.024] → −0.105 [−0.179, −0.040], F1 −0.041 [−0.087, +0.004] → −0.047 [−0.094, −0.003] (the upper bound now just below 0; same direction as the record, read as unchanged, not as a new finding); Isolation Forest, trees, CNN: every CI includes 0, as in the record. Seizures (scorer counts, sum of tp): GAE 115 → 115, MLP-AE 115 → 120; false alarms GAE 1,129 → 1,143, MLP-AE 827 → 813. Analysis C (sensitivity at the GAE's FP/day): MLP-AE 0.787 in both. Analysis D: the seizures every model misses keep amplitude ratio ≈ 1.26–1.30 and ≈ 26–32 s. **Split (counterfactual, paired bootstrap):** data effect on the GAE sensitivity −0.010 [−0.029, 0.000], MLP-AE +0.008 [0.000, +0.026], CNN 0.000; the largest change, trees F1 −0.021 [−0.038, −0.006], is a data effect (trees are deterministic and reproduced the record exactly on the earlier data, R2.0), from the +2,407 training windows of chb11 / chb21 in folds 1–3 and the float-level rebuild; trees − GAE F1 moves +0.018 → −0.008, both CIs include 0. **Descriptive, not pre-registered:** on the 8 thesis test patients MLP-AE sensitivity 0.505 → 0.553 vs GAE 0.581 → 0.575 (the F1 observation of 06/11, smaller; for F3). Own-point k per fold: GAE 4.08 / 3.86 / 3.51 / 3.82 → 3.92 / 3.94 / 3.96 / 3.54. Seizure table definition: `seizures.csv` matches 185 annotated seizures (GAE 114 caught in the record, as in the record's own table) while the scorer's tp sums to 115 of n_ref 186; counts above are the scorer's (rule 18). **Reading:** the six-model comparison re-executed on complete data gives the same pre-registered conclusions; no locked number changes; nothing enters the thesis material (R93, R98). The GAE and MLP-AE rows are partition 0 of R3. (e) R3 design proposed (handback Part 10 §10.4); **approved by the author 09/11 21:11**: R3-a no separate smoke (gates and R3.0 first in each notebook), R3-b R3.0 gate + counterfactual with the committed F1 checkpoints, R3-c five notebooks on Kaggle CPU in parallel; not built | R2_A / R2_B / R2_C outputs; aggregate committed before them | **yes** |
| 10/11 11:50 | **R3 implementation (D18-F; design approved 09/11 21:11: R3-a no separate smoke, R3-b R3.0 gate + counterfactual with the committed F1 checkpoints, R3-c five notebooks in parallel; written and tested on synthetic data before any R3 output):** (a) new files `src/r2_r3.py` (sha `7dc1697c`), `src/r2_r3_make_notebooks.py`, `src/r2_r3_synthetic_test.py`, `src/r2_r3_aggregate.py`; `f1_core.py`, `model_cmp_core.py`, `r2_core.py`, `r2_r2.py` imported unchanged (r2_r2 sha `542968bb` checked, STOP otherwise; the one runtime pointer set is `r2_r2.OUT_ROOT` → `r2/r3_repcv`, so r2_r2's gate and run-metadata helpers write into this stage's folder); (b) **design = rev 1 §3 unchanged** on the R0 data: partition r ∈ 1–5 of `partitions.json`, seed r, GAE + MLP-AE by `f1_core.train` (200 epochs, the thesis fold recipe), fold constants recomputed on the new data by `f1_core.fold_constants`, expected training windows = the committed clean counts with chb11 16,067 / chb21 11,619 (R0 diff), the frozen chain with each fold's own k (`f1_core.run_fold`); partition 0 = R2_A, not rerun; (c) **gates, all before any training** (STOP): G-data and D0′ (r2_r2, unchanged); **R3-projection** (computed wall time from R2_A's measured CPU times + elapsed ≤ 10.5 h, the split rule); G-const, G-vec, G-mlp (`f1_core`, unchanged, partition 0); **G-const-p** (this partition's constants recomputed on the earlier data = the committed F1 checkpoint metas, relative 1e-9; cases and seed identical; the F1 json's `n_train` holds the **total** clean-window count because `f1_core.job` lets the training info overwrite the meta's per-case dict — found by the synthetic test, compared as a total); **R3.0** (the 8 committed F1 checkpoints of the partition — GPU-trained, scored on CPU in the record — scored on the earlier data by r2_r3's path = `results/f1_repcv/raw/p{r}/per_subject.csv` on (model, fold, subject, point, stage) within |Δtp| ≤ 1, |Δfp| ≤ 2 per row, n_ref exact, 96 rows per model, nothing missing; exact rows, own-point k vs the record's fit.json and caught flags reported; checkpoint sha256 recorded); (d) **jobs**: atomic, one spawned process each, DONE.json last, reusable from an attached previous output with the same code sha; LPT order on 4 workers; a job is not started when its projected end passes 11.3 h, checked before the pool and again in the worker at its start (stricter than R2, which checked only before); `jobs/{model}_fold{f}` (training + chain, F1 format with the partition column), `cfjobs/cf_{model}_fold{f}` (the F1 checkpoint with its own constants on the new data, k recomputed), `r30/`; outputs `results/r2/r3_repcv/p{r}/` in the layout of `results/f1_repcv/raw/p{r}/` (run_meta with partition, seed, core_sha, partitions_sha, epochs) so the closed reading reads them; (e) **aggregate** `src/r2_r3_aggregate.py`: **A0** = the closed `src/f1_aggregate.py`, run unchanged on `results/f1_repcv/raw`, reproduces the 7 committed tables (relative 1e-9) and VERDICT.json, and the S18 §18.8 numbers (29 rounded values + 6/6) — **PASS on the real record in the container (71 s)**; **A1** = partitions 1–5 once each, one r2_r3 sha, r2_r2 sha, epochs 200, every R3 gate PASS, 8 training jobs (G2, 3,964 parameters, seed = partition, windows = expected) + 8 counterfactual jobs, rows complete for run and counterfactual, each case in its fold, partition 0 = R2_A (gates, 8 jobs) + R2_B's counterfactual, n_ref = record, non-ictal hours equal across partitions and = record except chb11 / chb21; **A2** = the pre-registered F1 / F2 reading by `f1_aggregate.py` unchanged on the rerun (its `ROOT` pointed at a staging folder that holds R2_A's GAE / MLP-AE rows as partition 0, and its required-gate set replaced by the R3 gate names; nothing else changed); A3 record vs rerun per partition and the two verdicts; A4 paired subject bootstrap (B = 10,000, rng 0, chb01 + chb21 one unit) of rerun − record, data (cf − record), new models (rerun − cf), per partition and across, and ΔF1 (MLP-AE − GAE) of record / cf / rerun; A5 per subject, k per fold, seizures, the 8 thesis test patients (descriptive, not pre-registered), the R3.0 summaries; no threshold (P2); (f) **synthetic test** (container, 1360 s, ALL PASS): A0 on the real record; the F1 record generated by `f1_core.job` itself; N1 R3.0 reproduces f1_core.job's rows exactly (96 per model, k, caught flags) in 5 partitions; N2 the gap-free fold 2 of partitions 1, 2, 5: constants unchanged, rerun weights = the F1 checkpoint bit for bit, k equal, gap-free held-out rows identical (run and counterfactual); N3 session guard; negative paths STOP before any training (F1 record fp + 3 → R3.0-mlp; F1 checkpoint absent → R3.0-jobs; F1 constant × (1 + 1e-7) → G-const-p; pinned hash → G-data); R3_p1 … R3_p5 PASS; R3_p1 resumed reuses 24 jobs with byte-identical rows; the aggregate's A1 PASS, every table written, A1 STOPs without R3.0-mlp or with a missing training job; (g) `R3_p1` … `R3_p5` built with `--runs fa69497760f889519fab38aabd9a1930a61bfe8b` (main after stage R2: holds the F1 checkpoints, R2_A / R2_B outputs, the pinned data hashes and r2_r2 `542968bb`; `r2_r3.py` is embedded); computed estimate ≈ 8.9–9.2 h per notebook | approved R3 design (handback §10.4–10.5) | no (synthetic data only) |
| 11/11 10:15 | **R3_p1 … R3_p5 read; stage R3 complete (D19-F; outputs `95902b9`, `1f53cad`, `8a9cae1`, `f2d6210`, `fa06a02`; clone `fa69497` in all five, `r2_r3` `7dc1697c`, `r2_r2` `542968bb`; Kaggle CPU 4 cores, 33.7 GB, torch 2.11.0+cpu, numpy 2.1.3, sklearn 1.6.1; measured p1 7.80 h, p2 8.20 h, p3 6.76 h, p4 6.93 h, p5 6.50 h vs computed 8.7–9.0 h):** (a) **gates** (against handback §11.6): G-data, D0′, R3-projection, G-const, G-vec, G-mlp, G-const-p (max relative 0) PASS in all five; **R3.0-gae and R3.0-mlp: 96/96 rows exact in every partition, max \|Δtp\| 0, \|Δfp\| 0, own-point k relative 0, caught flags differing 0/185** (the GPU-trained F1 checkpoints reproduce the F1 record exactly on CPU; the tolerance was not needed); the 40 checkpoint sha256 in the gates = the committed `results/f1_repcv/raw/p*/jobs/*/*.pt` (checked in the clone). 40 trainings + 40 counterfactual jobs done, 0 failed, 0 reused; every training 200 epochs, seed = partition, 3,964 parameters, G2 PASS; training windows = the F1 record's count + 2,407 (chb11 1,839 + chb21 568) for the cases in training, checked independently for all 20 folds; GAE 3.4–6.3 h, MLP-AE 1.5–3.1 h per fold, peak ≤ 4.2 GB per job; counterfactual 69–154 s per job. Cosmetic: each notebook's `SUMMARY.md` is titled "R2 p<r>" (r2_r2's helper title); not changed. (b) **aggregate** (`src/r2_r3_aggregate.py` unchanged since `a935944`; container numpy 2.5.3, pandas 3.0.5; 108 s): **A0 PASS** (the closed `f1_aggregate.py` reproduces the 7 record tables and VERDICT.json, and the 29 S18 §18.8 values + 6/6), **A1 PASS**; output `results/r2/r3_repcv/aggregate/` (14 files + `f1_reading/` 9 files). Independent cross-check in the container from the raw `per_subject.csv` (own code, not the aggregate): GAE sensitivity across the 6 partitions 0.7334 ± 0.0113, ΔF1 per partition and n_pos 6 identical; leave-one-subject-out of the mean ΔF1 0.062–0.082 (most influential chb05, as in R2). (c) **pre-registered reading** (`f1_reading/`, record → rerun): **F1** GAE CV over 6 partitions 0.736 ± 0.012 (0.723–0.753) @ 27.3 ± 1.1 FP/day → **0.733 ± 0.011 (0.713–0.745) @ 27.4 ± 0.7**; F1 0.210 ± 0.009 → 0.211 ± 0.008; subject-bootstrap CI of the mean [0.612, 0.854] → [0.608, 0.851]; 8 thesis test patients 0.575 ± 0.013 → 0.565 ± 0.013; other 16 cases 0.817 ± 0.016 → 0.818 ± 0.013. MLP-AE 0.726 ± 0.018 @ 19.2 → 0.739 ± 0.016 @ 19.3. **F2** ΔF1 > 0 in 6/6 → **6/6**, mean +0.075 [+0.034, +0.121] → **+0.077 [+0.038, +0.120]** → verdict unchanged: "stable advantage of the MLP-AE (without message passing)"; ΔF1 per partition +0.057 … +0.091; Δsensitivity −0.009 [−0.086, +0.062] → +0.006 [−0.053, +0.059]; ΔFP/day −8.1 [−11.0, −5.3] → −8.0 [−10.9, −5.0]; ΔAUROC +0.082 → +0.084 [+0.060, +0.112]; secondary ΔF1 at the fixed 0.005 point +0.060 [−0.012, +0.127] → +0.071 [+0.008, +0.130] (the lower bound now just above 0; a secondary reading, read as unchanged, as the SVM bound in R2). Seizures caught (scorer tp, of 186): MLP-AE ≥ GAE in 6/6 partitions (equal in partition 5); false alarms 765–813 vs 1,066–1,143. (d) **rerun vs record** (paired subject bootstrap, across partitions, own point, after CPD): GAE Δsensitivity −0.003 [−0.013, +0.008], ΔF1 +0.001, ΔFP/day +0.02 [−0.70, +0.84]; MLP-AE +0.013 [−0.007, +0.036], +0.002, +0.15; data part (cf − record) ≤ 0.002 in sensitivity for both; per partition GAE sensitivity moves −0.018 … +0.022 and the across-partition mean does not. 6 of 108 per-partition cells (2 models × 6 partitions × 3 steps × 3 metrics) have a CI excluding 0 (about what 95 % intervals give by chance). At the fixed 0.005 point the GAE rerun − record is −0.014 [−0.028, −0.001] in sensitivity and +0.55 [+0.10, +1.02] FP/day (the same direction as R1's new models). (e) **Descriptive, not pre-registered (for F3-C):** on the 8 thesis test patients MLP-AE − GAE per-patient sensitivity was −0.042 on average in the record (negative in 5/6 partitions) and is −0.009 in the rerun (−0.069 … +0.055, negative in 4/6); seizures caught there MLP-AE − GAE −1 … +4 (5/6 partitions ≥ +1). The D12-F observation ("MLP-AE lower on the test patients") does not hold as a stable pattern; F3-C reports it as such. **Reading:** F1 and F2 re-executed on complete data give the same pre-registered verdicts as on the earlier copy; the five missing files and CPU retraining change no conclusion. No locked number changes; S18 §18.8 stays the Q&A number; nothing enters the thesis material (R93, R98). (f) R4 proposed (handback Part 12 §12.4–12.6: F5a + F3 in one notebook, R4.0 gate, F5a definitions, F3 controls for selection / regression to the mean); not approved yet | R3 outputs; aggregate committed before them | **yes** |
| 11/11 14:50 | **Stage RP added; track now serves the final report (chat PU1, board rev 43).** Author decisions 11/11: (a) the final report reports one model, the R1 re-execution on complete data (R141); (b) main model = fixed thesis split, seeds 1–4 without a main seed — seed 42 replaced by a new seed 4 (R142); (c) **k calibrated per seed** on each seed's own model with the recorded rule (R143) — this changes the frozen design (k was calibrated on seed 42 only and applied to all seeds); it is decided **after** the R1 results were seen (the observation of row 08/11 07:40 that seed 42 was the lightest-tailed model and set the other seeds' budgets), on the principle that no seed is privileged, and the report states it; (d) demo model = lowest validation loss among seeds 1–4 (R146); (e) every analysis on the earlier model is re-run on the new one before the report uses it (R148); (f) R2 and R3 used unchanged; (g) R4 deferred until RP is done; D19-F's questions R4-a … R4-e stay open (R154); (h) local caches kept until the project ends, no `Archive/` folder (R156). No code written yet; RP1–RP3 are designed in the next track chat | author decisions after the defense | yes: R1–R3 results (decision (c) was taken after seeing R1) |
| 11/11 23:10 | **RP1–RP3 implementation (D20-F; author approved RP-a … RP-f 11/11 21:50; written and tested on synthetic data before any RP output):** (a) new files `src/r2_rp.py` (sha `5281446e`), `src/r2_rp_make_notebooks.py`, `src/r2_rp_synthetic_test.py`, `src/r2_rp_aggregate.py`; `r2_r1.py` (sha `76cbe51f`) and every record module imported unchanged; the module-level `TAGS` lists of `r2_r1` and `x1_external` are pointed per process (as `PD.CKPT`), no record file edited; (b) **one notebook `RP_RUN`** (RP-a), clone `c91719f` (holds the R1_RUN output and R1_SMOKE's pinned hashes); seeds 1, 2, 3 (and 42) = the committed R1 checkpoints, only seed 4 is trained; output `results/r2/r1_system/rp/`; (c) **gates before training** (RP-b): G-data = the 63 dataset files' sha256 equal R1_SMOKE's pinned `data_sha256.csv` (no earlier `.npz` needed); G-const-new = `norm_constants` on the new data and the expected window counts equal the 4 R1 checkpoint jsons; **mode** = exact if numpy / scipy / sklearn / pandas / torch / torch_geometric / ruptures / python equal R1_RUN's `run_meta`, else tolerance; **RP.0** = the R1 checkpoints on the new data, scored by this stage's per-seed-k function with every k = R1's k (3.785202…), reproduce `r13/run` per_subject + errors + q and k (exact: integers equal, floats 1e-9 relative, error pairs equal in order, k 1e-12; tolerance: |Δtp| ≤ 1, |Δfp| ≤ 2 per row, n_ref and non-ictal hours equal, k 1e-6); G-vec (`r2_r1.gate_vec` unchanged); **G-val** = validation loss of the 4 R1 checkpoints recomputed with `train_job`'s code equals their json `final_val` (exact / 1e-6), so seed 4's value is comparable; (d) **RP1** = `r2_r1.train_seeds([4])` unchanged (train_job: constants, 270,758 windows, 3,964 parameters, G2, validation loss, sanity AUROC), 1 worker, 1 thread as seeds 1–3, step time measured on 1 worker for the session guard; resumable by `r2_r1.import_models`; (e) **RP2** = k_s = `p3_levers.calibrate` on the 15 development cases with seed s's own smoothed member mean, every set scored with `p3c_freeze.run_budget` (4 arms × 3 stages) for seeds 1–4 and 42 (RP-c: 42 descriptive; its own k = R1's k, so its rows must equal R1's; the frozen arm does not use k, so seeds 1–3 frozen rows must equal R1's); external sets use each seed's k; per-window scores of seeds 1–4 (final scalar x, smoothed xs, ok, ictal, file and time) for test, chb24 and Siena as `rp2/scores/{case}.csv.gz` plus `thresholds.csv` (RP-d: committed if ≤ 20 MB measured); (f) **RP3 rule** (RP-e, fixed here before seed 4 exists): demo model = the seed of 1–4 with the lowest `final_val` (the recipe's loss on the clean windows of the 3 validation patients; no test data; the values of seeds 1–3 are in the committed R1 jsons), ties within 1e-9 relative → the smaller seed; written to `demo_model.json` with checkpoint, sha256, constants and k; (g) **aggregate** `src/r2_rp_aggregate.py` (before any output): A0 = `e22_test_oneshot.metrics` on R1's `r13/run` reproduces R1's `aggregate/summary_per_seed.csv` (**PASS on the real files**, 192 rows); A1 = every RP gate PASS, rows complete, n_ref = R1's, seed 42 and frozen rows = R1's by the run's mode, k of seed 42 = R1's, `demo_model.json` = the rule; tables (seeds 1–4): per seed, 4-seed mean ± SD with a patient-bootstrap 95 % CI of the per-patient mean (B = 10,000, rng 0, chb01 + chb21 one unit: RP-f), per subject, final − held-out (paired), k per seed and the correction (seeds 1–3, own k − R1's k, paired), onset / offset errors, review fraction, demo; no threshold (P2); (h) **synthetic test** (container, ALL PASS): the real R1_RUN notebook on the R1 synthetic world produces the "committed" R1 output; N2 = RP views + `train_job` reproduce R1's seed-1 checkpoint bit for bit; RP_RUN mode exact with RP.0 1,248 / 1,248 rows exact; negative paths STOP (one R1 row tp + 1 → RP.0, one pinned hash → G-data, one R1 `final_val` → G-val, `demo_model.json` seed → aggregate A1); R1 versions changed → mode tolerance, PASS; resumed run reuses seed 4 with byte-identical rows | approved RP design (chat D20-F) | no (synthetic data only) |
| 12/11 09:00 | **RP_RUN read; RP1–RP3 complete (D20-F; output commit `f7f2e51`; clone `c91719f`, `r2_rp` `5281446e`; Kaggle CPU, versions = R1_RUN's → mode exact; measured 3.02 h: training 2.55 h at 5.03 ms per step on 1 worker, RP.0 0.24 h, RP2 0.18 h; estimate was ≈ 4.5 h from R1's 4-worker step time).** Gates: G-data (63 = pin), G-const-new (relative 0; 270,758 windows), **RP.0 1,824 / 1,824 rows exact, 2,210 error pairs equal, q equal, k relative 0**, G-vec 0, G-val (relative 0), training (seed 4: 270,758 windows, 3,964 parameters, G2), RP2 2,280 rows, scores 23 cases (15 MB → committed), RP3. **Aggregate** (`src/r2_rp_aggregate.py` unchanged since `dc2204f`; container): A0 PASS (192 rows), A1 PASS (seed 42 and frozen rows of seeds 1–3 = R1 exactly). **k per seed:** 42 3.785 (= R1), 1 4.131, 2 3.945, 3 4.038, 4 4.009. **Demo model (RP3 rule): seed 3** (validation loss 0.020768; seeds 1 / 2 / 4: 0.020844 / 0.020849 / 0.020801). **Main model, 4 seeds, per-patient means, CPD stage** (mean ± SD [patient-bootstrap 95 % CI]): test held-out 0.466 ± 0.028 [0.217, 0.729] @ 25.3 ± 1.0 FP/day, F1 0.144; test final 0.541 ± 0.032 [0.312, 0.770] @ 30.2 ± 1.6 FP/day, F1 0.166, precision 0.101; development final 0.817 @ 23.7; chb24 final 0.859 @ 28.4; Siena final 0.654 ± 0.068 [0.482, 0.805] @ 43.0, F1 0.219 (held-out 0.478 @ 19.8). Final − held-out on test: sensitivity +0.075 [0.000, +0.209], FP/day +5.0 [+0.2, +11.9]. **k correction** (seeds 1–3, own k − R1's k, final arm): test sensitivity −0.023 [−0.047, −0.006], FP/day −2.0 [−4.1, −0.4], F1 +0.006; Siena −0.054 / −4.4 FP/day; development −0.003 / −2.7. Boundaries (median |onset| / |offset|, s, final): test CPD 16 / 24, hybrid 16 / 16; Siena CPD 20 / 32, hybrid 20 / 20. Output `results/r2/r1_system/rp/aggregate/`. Descriptive (P2); these are the report numbers of the main model (R141–R144) | RP_RUN output; aggregate committed before it | **yes** |

## 13 · Corrections to rev 1 found in this revision (06/11)

| rev 1 statement | correction |
|---|---|
| "F5 needs a recomputation; no committed score arrays" | the hybrid's boundary errors are committed for every set (§2); a recomputation is still needed for the hybrid's detection counts on test / chb24 / Siena, for CIs and for the CV models |
| "onset from CPD, offset from the contiguous-run rule; detections unchanged by construction" | L6 as coded keeps the detector's boundaries for events > 300 s and when CPD falls back; detection changes (dev 0.676 vs 0.670, pooled) |
| Siena on Kaggle "used in the original runs" | consistent with `x1_external.py` ("combined dataset", Kaggle CPU); its identity is proven by sha256 against PhysioNet and gate GE, not assumed |
| D0 = data identity | D0 checked identity with an **incomplete** copy (§1); replaced by R0.1 (hashes against PhysioNet) + D0′ |
