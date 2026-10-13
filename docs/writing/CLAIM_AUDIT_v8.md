# CLAIM_AUDIT_v8 — verification of the report's factual claims (13/10, chats 3–5)

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

## 4 · Open items after chat 5 (13/10)

| item | status | who | how |
|---|---|---|---|
| N1, N2, N3 (supervisor's papers): title-level sentences match the abstracts | **open** | `hồng` | publisher abstract (blocked for the container) |
| N2, N3 authors and years; N5 venue and DOI | **closed 13/10**: N2 = Xiao et al. 2024, *BSPC* 87, 105464 (Crossref); N3 = Hong et al. 2025, *Knowledge-Based Systems* 327, 114199 (OpenAlex; printed "et al." because the record repeats two names); N5 = Dani & Liebe 2026, MICCAI 2026, LNCS, pp. 449–458, DOI 10.1007/978-3-032-38239-9_43 (Crossref) | chat 5 | `CITATION_MAP_v8.md` |
| Figure 14 panel (d): what the EEG shows | **closed 13/10** from the author's reading (P-1) | author | Ch3 3.3.5 |
| Table 3 pasted unchanged from the 11/10 draft | **closed 13/10** (P-2) | author | Ch1 1.5 |
| abstract ≤ 300 words, one page | **closed**: 299 by `split()`; one page in the build (p. ix) | chat 5 | recount in Word optional |
| page count of the built body | **measured**: 58 pages (LibreOffice render); decision P-4 on the board | chat 5 / author | Word page count after updating fields |
| every number of Ch1–5 prose against the chapter notes and result files | **open** for prose; tables done (section 5) | `xanh` | outline §6 + chapter notes |
| Figures 1, 2, 4, 5, 7 in the build are the repository copies; identity with `Reports/v8/figures_inherited/` | **open** | chat 5b | sha256 against the inherited files |
| Figures 6 and 10: the repository copies show the earlier system | **open**: placeholders in the build | author → rebuild | attach `figures_inherited/` |

## 5 · Checks made in chat 5 (13/10)

| check | method | result |
|---|---|---|
| Ch3 and Appendix tables vs the gated table files (`Reports/v8/tables/`) | script: row-by-row and numeric-token comparison | Tables 11, 13, 16, 17, 23, 24, 25 identical; 12, 14, 15, 19 same values (column order, rounding 77.74 → 77.7, 6.1 → 6.10); Table 4 carries listed hours by approval O7, and its scored hours (562.40, 111.82, 279.38) match the file; Table 10 = the file without its source column |
| Table 9 values vs `PERF_PHASE_RECORD.md` | grep of every value | all present (E8, E16, E21, E17b, P3 rows) |
| cross-references | script over the built text | every "Section", "Table", "Figure", "Equation" and "Appendix" reference resolves; all 29 tables and 17 figures are cited in the text |
| forbidden numbers (instructions §4) | script | none; 0.498 appears only as the four-seed mean; 21.0 s/h only as "overall" beside the 21.68 s/h median; 0.500 only as the chb24 F1 |
| abbreviations | script: listed vs used | all listed ones used; AUC, CI, CNN, F1 used but unlisted → added |
| citations | script: every [n] of every chapter mapped to a sheet code through the chapter's Notes table, renumbered by first appearance | 69 references, no unmapped citation; working → global map in `CITATION_MAP_v8.md` |
| keywords | count | 10 words (limit 10) |
