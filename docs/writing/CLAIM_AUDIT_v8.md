# CLAIM_AUDIT_v8 — verification of the report's factual claims (13/10, chats 3–6)

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

## 4 · Open items after chat 6 (13/10)

| item | status | who | how |
|---|---|---|---|
| N1, N2, N3 (supervisor's papers): title-level sentences match the abstracts | **open** (`hồng` could not open them) | author | publisher abstract |
| E9 [25]: standardisation with training statistics "as in" Tang et al. App. A | **open** (cited from the `train_gae_v2.py` docstring; clip and [0, 1] mapping no longer attributed) | author | open App. A of arXiv:2104.08336 once |
| G2 [52]: direction of its "higher thresholds (70–85 %)" | **open, not load-bearing**: the text now cites G2 only for "thresholding changes GNN performance" | author (optional) | PDF arXiv:2211.08927 |
| M3 [43]: exclusion sentence joined from fragments | **open, paraphrased only** ("too short for its 4 s epochs") | author (optional) | PDF Section 4.1 |
| Benchmark "Self-GNN – Tang 2021" = E9 | **probable** (same title, arXiv 2021, ICLR 2022); cited as [25] in Table 18 | author | benchmark algorithm card, once |
| Zotero metadata: ICHI DOI for [24]; first-posted year of [3] (arXiv 2410 = 2024); LNCS volume of [29] (16894, from the 11/10 draft); DOIs of the pre-DOI-era entries E1 [50] and E2 [62] (Crossref by title, PII S0301-0082(00)00026-5); J4 [45] journal data; M1 [32] and M3 [43] DOIs; B1 [56] journal version; B11, A2, C4 volume/pages; [69] = preprint of [39] | **open** — Zotero does it when the DOIs are entered | author (Zotero) | `CITATION_MAP_v8.md` (regenerated chat 6) |
| WHO "nearly 80 %", "three quarters" | **closed** (live page 13/10, section 3) | — | — |
| `en` (English polish against `PROSE_STYLE_SPEC.md`) | **not received** in chat 6 | `en` | on the chat-6 chapter files |
| page count of the built body | **measured chat 6**: 65 pages with the template margins (P-5) and Figures 6 and 10; 61 with the earlier margins | author | board P-7 |

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

## 6 · Corrections and checks made in chat 6 (13/10)

Inputs: the P-3 reading of H1–H3 / C1–C5, `xanh` (Abstract, Ch4, Ch5), `hồng` (all chapters), and a
cross-review of the three. Every correction below was re-checked against its primary source in this chat.

| # | where | was | is now | evidence |
|---|---|---|---|---|
| 15 | Ch3 Table 9 rows 1–2, 3.2.1, 3.3.1; App C rows 6, 8 | "single graph-level distance" | three-readout ensemble (reconstruction error + graph-level latent distance + gamma coupling); new row "graph-level latent distance alone 0.553 (two seeds)" | `e22_test_oneshot.py` l. 174–176; record §2 E8, §6.1 E12 |
| 16 | Ch1 C1 | 0.489 → 0.612 (mixes two changes) | same readout, reference fit 0.612 vs 0.191 / 0.295 | Table 6; record E16 |
| 17 | Ch1 C2 | drift and budget as one claim | drift 0.612 → 0.681; budget test-informed, +0.010 dev, chb15 on test | Table 9; record §9.7 |
| 18 | Ch1 C3 | onset only | adds "offsets not improved (24 vs 20 s)" | Table 13 |
| 19 | Abstract, 1.2, C4, Table 2, 3.6, 4.1, Ch5 | "without seizure labels at any step" / "no label at any step" | "no seizure label of the patient under review / of the reviewed patients" (author decision 13/10) | `train_gae_v2.py` training mask; App C (dev labels); 2.1.3 (z-score) |
| 20 | Abstract, C5, Table 16, Ch5 | "blind expert annotation" | "blind channel annotation" (the author annotated, the supervisor approved) | App E |
| 21 | 1.3, 1.5, 1.6, 2.8.2 | "before the test patients were scored"; "every design decision on the development patients" | "before the held-out evaluation"; one test-informed change named | record §3 looks 1–7 |
| 22 | Abstract, 4.1, 4.2, 4.5, 4.6, Ch5 | unlabelled seed / aggregate | seed 42 / four-seed labels; "pooled" FP/day; 27.5 instead of "about 28"; 5 FA net (computed) | e23_SUMMARY, x1_SUMMARY (0.6335, 41.00 computed from per-seed values) |
| 23 | Ch4 4.1 | "a third or less" of the FA | 37 % and 20 % (computed) | 15.3/41.0, 8.2/41.0 |
| 24 | Ch4 4.2 | onset "halved on every set" | "by more than half except Siena (36 → 20 s)"; control 2 on look 6 (onset 20 s vs 8 s) added | Table 13; record §6.1 Look #6; `e18_cpd_localizer.py` control 2 definition |
| 25 | Ch4 4.2 | "spread of file medians 1.54" | IQR of file medians / MAD 1.54 vs 0.85 (S9) | record E21 |
| 26 | Ch4 4.3 | chb16 "one to four windows" | two to four whole windows (8–16 s) | `results/figures_v8_data/perseizure_final.csv` |
| 27 | Ch2 2.3.3 | "degeneracy reported for dense graphs [G2, B4]" | own reasoning; G2 = thresholding changes GNN performance; B4 = cost of dense graph construction | sheet G2, B4 |
| 28 | Ch2 2.5.2 | LW "as done for autoencoder embeddings [B1]" | LW used for the connectivity input of brain-network GAEs | sheet B1 |
| 29 | Ch2 2.7 | "SOZ, which scalp EEG cannot establish [E2]" | irritative zone ≠ ictal-onset area [E2] | sheet E2 |
| 30 | Ch2 2.9.1 | processor power draw [C3] | C3 only for "dedicated low-power hardware exists" | sheet C3 |
| 31 | Ch1 1.1.2, Ch4 4.3 | inhibitory restraint "makes the network more regular" [E3] | "can limit the spread"; effect on scalp coupling a hypothesis | sheet E3 |
| 32 | Ch1 1.2.2, Table 1 | EEG-CGS not discussed; "checked against chance" [E11, E13] | EEG-CGS: no seizure data in training, channel and clip output; E11/E13 for channel-annotated checks; [N2] added to Table 1 | sheet E11, E13 |
| 33 | Ch1 G1 | "no method fits ... without labels" | qualified for M4 (single-patient one-class, one-minute intervals, no onset/offset) | sheet M4 |
| 34 | Ch1, Ch4 | B10 "terabytes" (scalp implied); F6 inter-reader; F2 "supervision"; M2/M3 reasons; M6 values; M7 patient-specific; E14 unsupervised; L2 "no distributional assumption" | each narrowed to its verified statement | sheet B10, F6, F2 + U-F2, M2, M3, M6, M7, E14, L2 |
| 35 | Ch4 Table 18 | Ali "all subjects"; benchmark entries unnamed; DynaSD [1],[2] | 22-channel records (175/198 seizures); entries named; Tang entry cited with E9; DynaSD method [K4], numbers [K3] | U-F2; BENCHMARK_CHECK |
| 36 | Ch2 2.1.2 | Siena cited K1, K2 | K1, K2, J3 (PhysioNet citation request) + "[K2] reports 9 men and 5 women" | sheet K1, K2 |
| 37 | Ch2 2.3.2 | clip and scale "[E9]" | only standardisation with training statistics "as in [E9]" | `train_gae_v2.py` docstring |

Checks after the rebuild (script over the built document): 29 table and 17 figure captions in place, each
caption beside its table or figure; every Section/Table/Figure reference resolves and every exhibit is
cited; 12 numbered equations; 69 references, no unmapped citation; forbidden numbers none (0.498 only as a
four-seed mean); no "expert" in the report text except the title of a cited paper; no "at any step";
abstract 299 words, one page. Figures 1, 2, 4, 5, 7 byte-identical to the repository copies; 6 and 10 from
`figures_inherited/`, checked by eye (final system). `xanh` rows 8–11 (Ch4 4.3) verified against
`results/p3_anatomy/seizures.csv` and `results/p3b_diag/tail.csv` (all values confirmed except row 11).
