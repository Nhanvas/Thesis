# CLAIM_AUDIT_v8 — verification of the report's factual claims (13/10, chat 3–4)

**Why.** The author asked (13/10) that every statement of the report be checked as a researcher would,
not only the result numbers: the data-accounting gap (chb11, chb21 files missing locally) showed that an
unchecked fact can survive into a submitted report. This file records what was checked, how, what changed,
and what is still open. It complements the "Notes — not part of the report" of each chapter file
(number-by-number sources) and is the checklist of chat 5.

## 1 · Method

| claim type | checked against | rule |
|---|---|---|
| result numbers (Ch3, Ch4, abstract, Ch5) | committed result files (gated tables of `make_v8_exhibits.py`, SUMMARY files, record) | a number not in a file is not written; computed values are labelled |
| method statements (Ch2, App B) | the code that runs (`src/dataprep/*`, `c1b_build_trainset.py`, `retrain/*`, `p2_scalars.py`, `e16_recording_baseline.py`, `web_demo/backend/pipeline_demo.py`) | read the function, not the docstring or a planning document |
| dataset facts (Ch1, Ch2, App A) | PhysioNet pages and raw files (CHB-MIT, Siena `subject_info.csv`), WHO fact sheet (live) | primary row-level source over prose summaries |
| literature claims (Ch1, Ch4) | `Thesis_Reference_Sheet.md` verified quotes; abstracts where reachable | a paper read only at title level is cited for its title claim only |

## 2 · Corrections made on 13/10 (all were also in v5 and the 11/10 draft)

| # | where | was | is now | evidence |
|---|---|---|---|---|
| 1 | Ch2 Eq 2 | AEC = corr(envelopes) | AEC = **|corr|** of the Hilbert envelopes | `graph_construction.compute_aec`: `np.abs(np.corrcoef(...))` |
| 2 | Ch2 2.3.1 | wPLI, expectation unspecified | broadband, mean over the frequency bins of one window's FFT | `compute_wpli` (rfft of the window, mean over bins) |
| 3 | Ch2 2.3.2 | band powers "rescaled within each window" | log band powers z-scored over the window's 90 values, then min-max per band across the 18 channels | `feature_extraction.compute_band_powers` + `train_gae_v2.bp_minmax` |
| 4 | Ch2 2.3.2 | "signed logarithm of the excess kurtosis" | sign(κ)·log(1 + |κ|) | `c1b_build_trainset.f7` |
| 5 | Ch2 2.1.1 | "the most widely used open corpus" | "a widely used open corpus" | no source for the superlative |
| 6 | Ch2 2.1.1 | test seizures "median 45 s" | removed | no committed per-seizure annotation file; whole-window median is 50 s |
| 7 | Ch2 2.1.2 | Siena "9 men 36–71, 5 women 20–58" | "8 men 25–71, 6 women 20–58, according to the per-patient table"; disagreement noted in App A | PhysioNet `subject_info.csv` (raw) vs PhysioNet prose (9/5, 25–71) vs paper (9/5, 36–71) |
| 8 | Ch2 2.1.2 | "referential 10–20 montage" | electrodes by the 10–20 system, 512 Hz; bipolar formed from the recorded referential channels | PhysioNet states 10–20 and 512 Hz, not the montage |
| 9 | Ch1 1.1.1 | "one third continue to have seizures ... monitoring advised [C6, D2]" | WHO: up to 70 % could become seizure-free; three quarters untreated in low-income countries | WHO live page (7 Feb 2024); C6/D2 do not support the sentence as cited |
| 10 | Ch1 1.2.2 | "self-supervised detectors train the seizure classifier with labels [E9, N2, N3]" | the label claim kept for E9 only | N2, N3 read at title level only |
| 11 | Ch4 4.1 | development → test drop "0.670 → 0.336" (outline) | 0.662 → 0.336 (the held-out system's own development value) | record §6.1 (E18 on E17b) and §3 look 6 |
| 12 | Ch4 4.3 | channels above z 3 at the peak "chb06 1.4" | chb06 and chb16 1.4 (both) vs 6.3–15.4 | `results/p3_anatomy/seizures.csv`, 4-seed mean of per-seed medians |
| 13 | App F Table 28 | column "Loading and filtering" | "Reading, filtering and windowing" | `pipeline_demo.process_file_phase_a` |
| 14 | Ch3 3.3.3 | duration bins unlabelled | durations in whole 4 s windows (the ≥ 120 s bin is 8 chb15 seizures) | `results/figures_v8_data/perseizure_final.csv` (multiples of 4 s) |

## 3 · Confirmed without change (13/10)

CHB-MIT: 23 cases / 22 subjects, chb21 = chb01 1.5 years later, 256 Hz 16-bit, surrogate PHI and dates,
ODC-By v1.0, chb24 added December 2010 (PhysioNet). Siena: 14 patients, 47 seizures, about 128 h, 512 Hz,
10–20, CC BY 4.0; per-patient minutes sum to 7,704 = 128.4 h (computed). Code: Butterworth design order 4
(sosfiltfilt), notch 60 Hz Q 30 (filtfilt), statistics every 10th window excluding seizures and 4 h after,
top-k int(153 × 0.2) = 30 with weights kept, adjacency row / max, GCN 30 → 64 → 16 and MLP 16 → 32 → 12,
λ 0.1, Adam 1e-3, cosine, 200 epochs, batch 32, 3,964 parameters (computed from layers), Ledoit–Wolf squared
Mahalanobis, MAD unscaled, running median 451 windows centred, percentile (rank − 0.5)/n. Fixed-threshold
density 0.921–0.973 (background) and 0.949–0.974 (seizure), chb17 0.224 (`density_per_subject.csv`).
Seizure share of test time 0.42 % (whole windows, computed). WHO: around 50 million; nearly 80 % in low-
and middle-income countries.

## 4 · Still open (chat 5)

| item | who | how |
|---|---|---|
| N1, N2, N3 (supervisor's papers): title-level sentences match the abstracts; authors and years in Zotero | `hồng` | publisher abstract (blocked for the container) |
| N5 DOI 10.1007/978-3-032-38239-9_43 (from the 11/10 draft) | `hồng` | Zotero / doi.org |
| Figure 14 panel (d): what the EEG shows (Ch3 3.3.5 CHECK marker) | author | look at `fig14_gallery.png` |
| every number of Ch1–5 against the chapter notes and result files | `xanh` | outline §6 + chapter notes |
| Table 3 pasted unchanged from the 11/10 draft | author | docx |
| abstract 299 words by `split()`; recount in Word | chat 5 | Word count |
| page count of the built body (author accepts > 50 if content is needed, 13/10) | chat 5 | build the document |
