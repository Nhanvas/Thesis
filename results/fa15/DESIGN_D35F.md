# F-A1.5 (PC5) — gate decisions after the smoke (chat D35-F, 21/11/2026)

Project verification outside the report (board R204, R222). Design of record: `docs/FUTURE_RESEARCH_PLAN.md` §12 15/11 12:40,
13:20, 18:10. This file is written and committed **before any data notebook runs**; it changes two gates and adds three,
nothing in ASR, the data, the control arm or the reading.

## 1 · What the smoke showed (`results/fa15/smoke/`, clone `6c99bab`, fa15_asr `132d6179a1c77723`)

- **G-asr FAIL:** pre-ictal 60-s share 3.9e-3 and contrast after 1.05e-3 against `results/v9_x6/` (tolerance 1e-3).
- **G-conv FAIL:** PN00 relative SD difference 1.32e-3 (tolerance 1e-3); chb17 2.1e-4, mean 1.3e-4 SD, counted rejected
  windows 9 007 vs 9 006.

## 2 · Diagnosis (chat D35-F, from committed files, the asrpy source and a container test; no new Kaggle run)

**G-asr: asrpy's output depends on its chunking (`mem_splits`), and V9-X6 changed its chunking during its own run.**
- Per seizure row (smoke vs record): the four 1-h files (chb17a_03, chb17a_04, chb17b_63, chb24_01) agree to ≈ 1e-14,
  including chb17 where ASR removes 60–80 % of the power → laptop (V9-X6) and Kaggle give the same ASR output; the
  "library build" hypothesis of 15/11 18:10 is not supported. Only chb06_01 (the 4-h file) differs, at one seizure
  (onset 7461 s: pre-ictal share 0.0039 here, 0 in the record; seizure share 4.0e-5).
- asrpy 0.0.8 `asr_process` restarts its update grid (`update_at`, stepsize 32 samples) in every chunk, so the cleaned
  signal depends on `mem_splits`. The header of `src/v9_x6_asr.py` records that the chunking changed twice during the
  resumable run (default 3 → out of memory on chb06_01; 300-s chunks → two 4-h files done, the third killed; then 60-s
  chunks). Files finished before a change kept their parts. Hypothesis: chb06_01 in the record = 300-s chunks
  (`mem_splits` 49), the smoke = 60-s chunks (241); chb03's files (processed before the first crash) = `mem_splits` 3.
- Container test (synthetic 1-h, 18 channels, sparse bursts): the same chunking twice → bit-identical; 60 s vs 300 s →
  0.15 % of samples differ, a 60-s span share by up to 1.05e-3.
- Outside sources (not peer-reviewed): EEGLAB clean_rawdata also splits by available memory; M. Miyakoshi (eeglablist,
  18/3/2019) reports that this changes the result ("up to 0.3 % of jitter") and advises fixing the memory setting for
  replicability (https://sccn.ucsd.edu/pipermail/eeglablist/2019/013808.html). No peer-reviewed study found.
- Effect on the report's V9-X6 numbers: none material (seizure shares differ by ≤ 4e-5 where measured).

**G-conv: the 3-s padding of the record's statistics pass, nothing else.**
- In the record, the features and the 5-SD training flag (`c1b_build_trainset`, `continuous_eval.filter_file`) already
  use whole-file filtering; only the per-channel mean / SD (every 10th window) use 3-s padded per-window filtering.
  ASR needs the whole file, so in the ASR arm only the mean / SD change convention.
- Synthetic diagnosis of 15/11 13:20: padding 3 s → 0.75 % of window RMS, 10 s → 2e-6, 30 s → 1e-13 (slices aligned).
- Size against ASR in the same smoke: chb17 5-SD-flagged windows 9 006 → 12 176 with ASR (+35 %) vs 1 window by the
  convention. Whole-file filtering before epoching is the established practice (Widmann, Schröger & Maess 2015, *Digital
  filter design for electrophysiological data – a practical approach*, J Neurosci Methods 250:34–46,
  DOI 10.1016/j.jneumeth.2014.08.002).

## 3 · Decisions (author 21/11 01:28: "duyệt theo đề xuất")

1. **ASR arm:** 60-s chunks for every file (V9-X6's final chunking), unchanged.
2. **G-asr:** tolerance 1e-3 kept; a file beyond it is recomputed with V9-X6's earlier chunkings (300-s chunks; asrpy's
   default 3 only for files ≤ 2 h, since 3 ran out of memory on a 4-h file) and **passes only if one of them reproduces
   the record within 1e-9**; every file is classed exact (≤ 1e-9) / within tolerance / explained / beyond (= FAIL).
3. **G-asr-pre** (new, before any long work, in the notebook that holds chb06): chb06_01 with 300-s chunks = the record
   within 1e-9, else STOP — the decisive test of the chunking diagnosis on real EEG (≈ 3 min, computed from 167 s).
4. **G-conv:** option A — the whole-file convention is accepted; G-conv is reported for every case and STOPs only above
   1e-2 (gross error). Options not chosen: B (add the ASR correction to the record's padded windows), C (identity control
   arm, §14 row 40).
5. **G-conv-pad** (new, before any long work; per notebook one CHB-MIT case and one external case — FA15_DATA_A chb16 +
   PN00, FA15_DATA_B chb08 + PN16): the record's statistics with 30-s padding = whole-file slices within 1e-9 relative →
   proves on real EEG that the G-conv difference is the 3-s padding only and that the slices are aligned.
6. **G-worker-sha** (new, the notebook pin rule R205): every ASR subprocess and feature job reports the sha16 of the
   `fa15_asr.py` it ran; all must equal the main process's (the notebook asserts that sha on the pinned clone).

A pre-gate FAIL skips the run, writes the tables, archives and STOPs.

## 4 · Code and test

`src/fa15_asr.py` (sha16 `0f9843dcfa3162a7`), `src/fa15_make_notebooks.py` (`build_data`; pre-gates per part),
`src/fa15_synthetic_test.py`: **27 / 27 checks PASS** (666 s, build container, numpy 2.1.3 / scipy 1.16.3 / mne 1.12.1 /
asrpy 0.0.8). New checks: a V9-X6-style record of chb01_01 built with 300-s chunks is beyond 1e-3 at 60 s and explained
by the 300-s recomputation (`mem_splits` 3), chb24_01 exact; G-conv-pad 30 s 0.0 / 2.2e-14 vs 3 s 2.5e-3 / 1.8e-3;
G-asr-pre PASS; G-worker-sha 13 / 13 jobs. Failure paths: slices shifted one sample → G-conv-pad FAIL, run skipped;
chb01_01 record + 1e-6 → G-asr-pre FAIL, run skipped; chb24_01 record + 0.01 → G-asr FAIL (unexplained); reference SD
× 1.05 → G-conv FAIL; buffer flag flipped → G-lab, G-ident FAIL; ASR subprocess failing → G-done FAIL; a worker
reporting another sha → G-worker-sha FAIL. A data notebook built by `build_data` runs to the end with every gate PASS.
Not covered: real-EEG sizes, Kaggle speed and memory (measured by the runs).

## 5 · Unchanged

ASR settings (asrpy 0.0.8, cutoff 20, per-file calibration, V9-X6's numpy-2 patch, the one-sample block_covariance
guard), the data (R0's file set), statistics / flag / features recomputed on the cleaned signal, the control
(`results/r2/r1_system/run/`), the training and reading design of 15/11 12:40 (ASR − control, per-patient means, paired
patient bootstrap, no threshold). Noted for the reading (no decision now): ASR shrinks the statistics' SD, so the 5-SD
flag removes more windows (chb17 clean windows 8 769 → 5 600); the ASR − control difference also holds retraining
variation, which PC7 (chat D34-F) measures.

## 6 · After FA15_DATA_A and the stopped FA15_DATA_B (21/11 13:30; written before T1, T2, B1, B2 run)

**Seen.** FA15_DATA_A (`eb0d4f2`, measured 10.545 h; 19 / 19 cases; G-conv PASS in every case, worst 1.32e-3; G-lab,
G-done, G-worker-sha 402 / 402 PASS; G-conv-pad chb16 0 / PN00 3.4e-14 at 30 s, 1.5e-4 / 1.3e-3 at 3 s). **G-asr FAIL:**
of V9-X6's 57 files in part a, 48 equal the record within 1e-9 (bit-level); 9 differ — chb03_01, chb03_02, chb15_10,
chb15_20, chb15_62, chb16_11, chb16_16, chb16_18, chb24_14 — seizure shares by ≤ 0.017, contrasts by ≤ 0.024,
single high-amplitude window shares by up to 0.342; recomputing with 300-s chunks (12) or asrpy's default (3) did not
reproduce the record and moved further from it. FA15_DATA_B stopped at **G-asr-pre FAIL** (`b05c7d8`): chb06_01 with
300-s chunks (49) differs from the record by 5.8e-3 (pre-ictal share), with 60-s chunks (241, smoke) by 3.9e-3.
G-conv-pad PASS (chb08 0 / PN16 9.0e-14 at 30 s).

**The chunking diagnosis of §2 is refuted as the explanation of these files** (it was wrong; chunking does change the
output, but no documented chunking reproduces the record). The code path is shown to be V9-X6's by the 48 bit-level
files. **New hypothesis (not measured):** platform arithmetic — the record was made on the laptop (30/10), the data runs
on Kaggle machine types whose arithmetic differs even under the same library versions (handback Part 28.3) — amplified
by ASR's discontinuous steps (clean-window selection in the calibration; keep / reject of components). Literature:
Glatard et al. 2015, *Reproducibility of neuroimaging analyses across operating systems*, Front Neuroinform 9:12,
DOI 10.3389/fninf.2015.00012 (results differ by platform; fMRI ICA differed between operating systems in one third of
subjects); Kiar et al. 2021, *Numerical uncertainty in analytical pipelines lead to impactful variability in brain
networks*, PLoS One 16:e0250755, DOI 10.1371/journal.pone.0250755 (Monte Carlo arithmetic to measure sensitivity to
small numerical perturbations).

**Decisions (author 21/11 13:30, "duyệt").**
- **T1 (laptop, `src/fa15_diag_laptop.py`, Claude Code prompt `docs/prompts/FA15_DIAG_LAPTOP.md`):** V9-X6's own
  `process_one` (60-s chunks, unchanged) on the laptop for the 10 differing files and 2 bit-level controls (chb03_03,
  chb16_17), parts to `results/fa15/diag_laptop/parts/`. Reading per file (1e-9 = equal): laptop = record ≠ Kaggle →
  platform; laptop = Kaggle ≠ record → the record's software state does not reproduce; neither → both. Controls must
  equal the record. Computed ≈ 35 min.
- **T2 (Kaggle, `src/fa15_perturb.py`, notebook `FA15_PERTURB`):** the 70 V9-X6 files, ASR (as the data run) twice —
  as is and × (1 + 2⁻⁴⁰), the repository's conditioning test of R0_DIAG17 — Measure 1 of each; per file max |P1 − P0|,
  max |P0 − record|, max |P0 − the data run's committed Measure 1| (Kaggle vs Kaggle). Descriptive: the 2 × 2 table
  "differs from the record" × "moves under the perturbation". Machine (CPU model, AVX-512, BLAS) in `run_meta`.
  Computed ≈ 2 h (88.5 h of EEG, two passes, 4 processes, A's measured 146 s per hour per process).
- **B rerun as FA15_DATA_B1 / _B2** (the 19 cases of part b split in two by hours, ≈ 280 h of EEG each, computed ≈ 5.3 h
  each from A's measured rate), **without pre-gates** (G-asr-pre removed: its premise is refuted; G-conv-pad already
  passed on four cases); G-asr unchanged and reported as it is (a FAIL does not prevent the output from being saved,
  as in A). From now on every `run_meta` records the machine (`fa15_asr.machine_info`). The data do not depend on the
  outcome of T1 / T2 unless they point to an error in fa15's own code path; then B is rerun.
- **Training** is designed after the B data exist; PC7's seed variance (chat D34-F, hand-off item (7)) informs the
  number of seeds.
- **Code and test (21/11):** `src/fa15_asr.py` (sha16 `f9a548e45cfed9a6`: `machine_info`, input perturbation in the
  clean path), `src/fa15_perturb.py`, `src/fa15_diag_laptop.py`, `src/fa15_make_notebooks.py` (`--bsplit`,
  `--perturb`), `src/fa15_synthetic_test.py`: **35 / 35 checks PASS** (655 s). New: B1 + B2 hold exactly part b's 19
  cases, no pre-gates; FA15_PERTURB runs to the end with every gate PASS on chb01_01 + chb24_01 (record classes correct;
  machine recorded); the T1 script reads chb01_01 "record state" and chb24_01 "same" on the synthetic record, writes
  only to its own folder and resumes. Observed on the synthetic world (not evidence about real EEG): chb24_01 moved by
  5.7e-3 under the 2⁻⁴⁰ perturbation.

## 7 · Training and reading (author 21/11 19:13, option A; written before any training output)

**Seen before this design.** T1 (`results/fa15/diag_laptop/`, laptop, V9-X6's own code, 713 s): the 10 differing files
equal the record exactly on the laptop (max 0.0) and differ from Kaggle; the 2 controls equal both → **the G-asr
differences are the platform** (laptop vs Kaggle arithmetic; the laptop reproduces the record even with numpy 2.4.4 /
scipy 1.17.1). T2 (`results/fa15/perturb/`, 1.382 h, 70 / 70 files, every gate PASS): a relative input change of
9.1e-13 changes ASR's Measure 1 beyond 1e-9 in **12 of 70 files** (up to 0.34 in a window share); 10 of the 11 files
that differ from the record are among them; Kaggle P0 = the data run's Measure 1 in 58 / 58 files. B1 / B2 (3.756 h /
4.159 h; 10 + 9 cases; G-conv PASS, worst 2.86e-3; G-lab, G-done, G-worker-sha PASS; G-asr B2: chb06_01, chb18_31 differ —
platform (T1) and perturbation-sensitive (T2)). The ASR data of all 38 cases exist and are internally consistent; B1,
B2 and T2 ran on Intel Xeon 2.20 GHz without AVX-512.

**Arms (one factor: ASR in the preprocessing).** Both = the path-2 recipe (r2_r1.train_job unchanged, 200 epochs, 3,964
parameters), k per seed (p3_levers.calibrate on each seed's own model, 15 development cases), p3c_freeze.run_budget for
the 4 budget arms × 3 stages on every set. **Control** = R0's data: seeds 42, 1, 2, 3, 4 committed
(`results/r2/r1_system/rp`) + seeds 5, 6, 7 (notebook `FA15_RUN_CTRL`). **ASR** = the ASR datasets
(`nhn2mm/fa15-asr-features-a`, `nhn2mm/fa15-asr-features-b1`, `norncreades/fa15-asr-features-b2`): seeds 42, 1, 2, 3
(`FA15_RUN_ASR_A`) and 4, 5, 6, 7 (`FA15_RUN_ASR_B`). 8 seeds per arm: PC7's minimal detectable development
sensitivity difference ≈ 0.03 with 8 seeds per arm (≈ 0.04–0.05 with 4; handback Part 28.2). The ASR arm's 5-SD flags
and z-score statistics are those of the cleaned signal (approved 15/11); its expected training-window counts are counted
from the ASR files.

**Gates** (`src/fa15_run.py` docstring): G-mod (r2_r1 76cbe51f, r2_rp 5281446e = the control's code), mode, G-data,
**G-repro** (the control's committed seed-4 checkpoint rescored by this path with its k = its committed rp2 rows), ctrl
G-const-new, asr G-asr-data / G-asr-counts, G-vec, training, RUN-complete, G-worker-sha; machine in `run_meta`.

**Reading** (`src/fa15_aggregate.py`, committed before the runs; gate A0 already PASS on the real record, 240 / 240
per-seed rows): per-patient means after the localizer; sets development, test, chb24, Siena; held-out (0.5 %) and final
(per-patient budget); sensitivity, F1, FP/day, precision; control and ASR mean ± SD over seeds; **ASR − control with a
two-level bootstrap** (patients as units, chb01 + chb21 one unit; seeds resampled within each arm; B = 10,000) — the
patient bootstrap of seed means alone omits training variation (PC7); chb24 seeds only; per-seed and per-patient tables;
onset / offset median |error| (descriptive); training-window counts of both arms. No threshold, every set reported, no
primary set (no selection is made from this result; R214 does not apply — a project verification, R204).

**Not separated (information, plan §14):** the effect of the stricter 5-SD flag (fewer clean training windows) from
the signal change itself — an extra arm (ASR features with R0's training mask, 8 seeds) would separate them.
**Machine types:** recorded; PC7 found no difference between Kaggle's two types (permutation p 0.098).

**Code and test (21/11 evening):** `src/fa15_run.py` (sha16 `effcdf70588ae6b1`), `src/fa15_aggregate.py`
(`8933129c1c826ed7`), `src/fa15_make_notebooks.py` (`--train`), `src/fa15_run_synthetic_test.py`: **15 / 15 checks PASS**
(6,820 s, build container) on the synthetic R1 / RP world (the real R1_RUN and RP_RUN notebooks, 3 epochs, as the
control record; fake ASR datasets with perturbed features and ~10 % of the 5-SD flags flipped, split over three inputs):
the three notebooks run with every gate PASS in mode exact (G-repro every row exact; the ASR runs read only the ASR
inputs, train on the ASR counts — 3,352 vs R0's 3,696 windows — and score differently from the control); the aggregate
A0 / A1 / A2 PASS and writes every table (chb24 seeds-only bootstrap); A0 on the real record 240 / 240; negative paths
G-repro, G-asr-data, G-worker-sha, A1, A2 STOP; resume imports only the notebook's own previous seeds (a control output
attached to FA15_RUN_ASR_B is not imported). The test's `--reuse` / `--only-resume` options were added after that run;
`--only-resume` was run on the same world: 2 / 2 PASS (1,364 s). G-mod passes in the test by its switch (the synthetic
repository's shas differ); its comparison is checked on Kaggle by the notebook's own sha asserts.
