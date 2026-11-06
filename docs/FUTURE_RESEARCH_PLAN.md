# FUTURE_RESEARCH_PLAN — independent research track: rerun on complete data, then Track F (rev 2, 2026-11-06, chat D13-F; §12 updated 06/11 D14-F)

*Repo: `docs/FUTURE_RESEARCH_PLAN.md` + project file. **Rev 2 replaces rev 1 in full** (author decisions 06/11, 09:12 –
10:38). The F1/F2 design of rev 1 is kept unchanged as §7. Rev 1's run on the earlier data copy stays as a record
(§11). From now on, every change is logged in §12 **before** any result is seen. Nothing in this file has been run
yet unless §11 or §12 says so.*

---

## 0 · Status, scope and way of working

**Independent track.** This track is independent of the thesis until the thesis is complete:
- the thesis ends with the defense (**09/11**) and then the final report submission (no deadline yet);
- the defense, slides, script, Q&A answers, report and demo use **only the locked numbers** (`NUMBERS_LOCK.md` +
  `NUMBERS_LOCK_S18.md`), and nothing produced here changes them (R93, R98);
- once the final report is submitted, the project is updated so this track becomes the main work (author 06/11).

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
  - The local gitignored caches are archived to `F:/Study/Thesis/Archive/<date>/` **after 09/11**, because the demo
    still needs some of them.
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
  - flags (`is_ictal`, `is_buffer`, `is_flag5sd`, `is_signal_loss`) and `file_idx` exact;
  - `f7` and `bp5` max |diff| ≤ 1e-3;
  - adjacency entries differing ≤ 0.5 % (the x1 R-feat tolerance);
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

**R1.0 Code-path gates on the earlier data (STOP on failure).** The committed checkpoints
`data/models_v2/gae_v2_clean_seed{42,1,2,3}.pt` + the earlier `.npz` must reproduce, exactly:
- `results/p3c_freeze/per_subject.csv` (budgets frozen and L2f; stages detector, cpd, hybrid; 15 cases × 4 seeds) and
  `errors.csv`;
- `results/e23_test_look7/per_subject_seed.csv` and `errors.csv` (point balanced; 8 cases × 4 seeds).

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

**R1.3 Scoring**, 4 seeds, the frozen chain (`e23_test_look7.evaluate` construction):
- development 15 and test 8 at both recorded budgets: frozen 0.005 (the held-out system of look 6) and L2f (the final
  system); stages detector, CPD, hybrid; onset/offset errors;
- chb24 + Siena 14 on the R0.4 features (the x1 path).

**Reading (descriptive):**
- per-patient means (SzCORE aggregate), 4 seeds, patient bootstrap;
- one table "rerun vs record" for every row of `p3c_freeze`, `e23`, `x1`;
- every difference explained (chb11 / chb21 data, k, retraining randomness);
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
- gates: D0′, G-const, G-vec, G-mlp, per job, aggregate.

**Pre-registered reading** (unchanged, so the rerun is comparable with the record):
- **F1:** across-partition mean ± SD and range, with the SD called sensitivity to partition + seed, **not**
  uncertainty; paired-subject bootstrap CI of the mean.
- **F2:** "stable advantage" iff ΔF1 > 0 in ≥ 5 of 6 partitions AND the CI's lower bound > 0. Secondary readings as
  in rev 1.

**Added (descriptive):** per partition, rerun vs earlier copy.

**Device:** CPU (decision P4, §10). The rev 1 rule chose GPU by speed only. The smoke of 05/11 measured CPU 7.02 h vs
GPU 7.38 h per partition notebook. CPU uses no GPU quota and is bit-deterministic. Kaggle's CPU speed is re-measured by
the R3 smoke.

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
| 4 | `R1_SMOKE` | 2, 3 | R1.0 gates on chb03 + PN00; G-vec on the thesis recipe; 2-epoch job; speed | measured |
| 5 | `R1_RUN` | 4 | R1.0 full; 4 seeds training (4 workers); k; scoring of all sets | measured (≈ 4–7 h est.) |
| 6 | `R2_SMOKE` | 2 | D0′, G-const, G-vec, G-mlp; one job per model type; CNN CPU speed | measured |
| 7 | `R2_A` / `R2_B` / `R2_C` | 6 | GAE + MLP-AE folds; IF + SVM + trees; CNN | measured |
| 8 | `R3_p1` … `R3_p5` | 7 | one partition × both models (8 jobs, 4 workers) | ≈ 7 h each (05/11 smoke) |
| 9 | `R4_F35` | 5, 8 | F5a verification + diagnosis; F3-A, F3-B, F3-C | ≈ 1–2 h est. |
| 10 | `R4_F5B_*` | 9 + approval | nested CV of the approved families; Siena check | measured |

**Code:**
- new files are `src/r2_*.py` (core, notebooks builder, aggregate);
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
| P6 | independent track until the thesis is complete; then the project is updated so it becomes the main work | 06/11 |

## 11 · Record — rev 1 run on the earlier data copy (verified 06/11, chat D12-F)

Five notebooks, 40/40 jobs, GPU T4 x2, every gate PASS. GAE CV over 6 partitions:
- 0.736 ± 0.012 at 27.3 ± 1.1 FP/day;
- 8 test patients 0.575 ± 0.013.

MLP-AE − GAE: ΔF1 > 0 in 6/6, +0.075 [+0.034, +0.121]; Δsensitivity −0.009 [−0.086, +0.062]; ΔFP/day −8.1
[−11.0, −5.3].

Source: `results/f1_repcv/`, S18 §18.8. These numbers remain the verified Q&A numbers until R3 is verified. They are
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

## 13 · Corrections to rev 1 found in this revision (06/11)

| rev 1 statement | correction |
|---|---|
| "F5 needs a recomputation; no committed score arrays" | the hybrid's boundary errors are committed for every set (§2); a recomputation is still needed for the hybrid's detection counts on test / chb24 / Siena, for CIs and for the CV models |
| "onset from CPD, offset from the contiguous-run rule; detections unchanged by construction" | L6 as coded keeps the detector's boundaries for events > 300 s and when CPD falls back; detection changes (dev 0.676 vs 0.670, pooled) |
| Siena on Kaggle "used in the original runs" | consistent with `x1_external.py` ("combined dataset", Kaggle CPU); its identity is proven by sha256 against PhysioNet and gate GE, not assumed |
| D0 = data identity | D0 checked identity with an **incomplete** copy (§1); replaced by R0.1 (hashes against PhysioNet) + D0′ |
