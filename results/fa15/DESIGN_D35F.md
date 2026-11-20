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
