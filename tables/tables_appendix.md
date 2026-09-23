# Tables Pack — Appendices

Revision 4 (2026-09-23). Every appendix table, filled from committed sources, in document order. Each
block ends with a `Source:` line naming the file the values were read from.

Authority: `docs/RESULTS_OF_RECORD_phaseB.md` and `docs/VERIFIED_NUMBERS.md` for every number,
`docs/EXHIBIT_SET_FINAL.md` (revision 3) for the exhibit list, `tables/CAPTIONS.md` (revision 7) for the
captions.

Changes from revision 1: Table A.2 rebuilt from the final annotation (the machine-generated draft is
retired); Table A.3 source wording corrected; Table A.4 interpretation tied to the final result; Table
A.5 versions confirmed against the running environment. Revision 3 cut Table A.6 (pre-registration index): the report presents results, not the internal
process that produced them. Revision 4 adds the rank columns to Table A.2 and renumbers the appendix
for the exhibits moved out of Chapters 1 to 4 (see `EXHIBIT_RENUMBER_MAP.md`).

## Rules applied throughout

1. Three decimals for discrimination, sensitivity, precision and F1; one decimal for false alarms
   per day.
2. No internal shorthand in a table cell or heading: no lever codes, no phase names, no branch
   nicknames, no document names.
3. A cell whose value has not been read from a file is written `— not measured`, never left blank and
   never estimated.
4. Patient identifiers keep the corpus form (chb03, chb06, …) so the tables agree with the figures.

---

## Table A.1 — Corpus metadata for all 23 subjects

| Patient | Set | Recordings | Recorded hours (h) | Seizures | Total seizure duration (s) |
|---|---|---|---|---|---|
| chb01 | training | 42 | 40.55 | 7 | 442 |
| chb02 | training | 36 | 35.27 | 3 | 172 |
| chb03 | test | 38 | 38.0 | 7 | 402 |
| chb04 | training | 42 | 156.06 | 4 | 378 |
| chb05 | training | 39 | 39.0 | 5 | 558 |
| chb06 | test | 18 | 66.73 | 10 | 153 |
| chb07 | training | 19 | 67.05 | 3 | 325 |
| chb08 | training | 20 | 20.01 | 5 | 919 |
| chb09 | training | 19 | 67.87 | 4 | 276 |
| chb10 | validation | 25 | 50.02 | 7 | 447 |
| chb11 | validation | 35 | 34.79 | 3 | 806 |
| chb12 | training | 24 | 23.69 | 40 | 1475 |
| chb13 | test | 33 | 33.0 | 12 | 535 |
| chb14 | test | 26 | 26.0 | 8 | 169 |
| chb15 | test | 40 | 40.01 | 20 | 1992 |
| chb16 | test | 19 | 19.0 | 10 | 84 |
| chb17 | test | 21 | 21.01 | 3 | 293 |
| chb18 | test | 36 | 35.63 | 6 | 317 |
| chb19 | training | 30 | 29.93 | 3 | 236 |
| chb20 | training | 29 | 27.6 | 8 | 294 |
| chb21 | training | 33 | 32.83 | 4 | 199 |
| chb22 | validation | 31 | 31.0 | 3 | 204 |
| chb23 | training | 9 | 26.56 | 7 | 424 |

23 rows, one per subject. Per-set totals agree with Table 2.2 (342 / 91 / 231 recordings; 93 / 13 / 76
seizures); hours summed from the rounded rows differ from Table 2.2 by at most 0.01 h.

*Source: `data/summaries/*.txt`, parsed by `evaluation_protocol.parse_summary_edf_list` and the
`data/splits/split_main.json` set assignment; emitted and rendered by `src/figures/emit_tables.py`
(`tables/csv/table_A1_corpus_metadata.csv`), self-checked against `docs/VERIFIED_NUMBERS.md`
Part 3.*

## Table A.2 — Channel annotation for all 76 test seizures, with the model's ranking

| Patient | Seizure | Recording | Onset (s) | Type | Channels | Annotated ictal channels | Median rank | Best rank | AUROC |
|---|---|---|---|---|---|---|---|---|---|
| chb03 | 1 | chb03_01 | 362 | focal | 8 | FP1-F7, F7-T7, T7-P7, FP1-F3, F3-C3, FP2-F8, F8-T8, T8-P8 | 8.5 | 1 | 0.613 |
| chb03 | 2 | chb03_02 | 731 | focal | 9 | FP1-F7, F7-T7, T7-P7, FP1-F3, F3-C3, FP2-F4, FP2-F8, F8-T8, T8-P8 | 11.0 | 2 | 0.432 |
| chb03 | 3 | chb03_03 | 432 | focal | 8 | FP1-F7, F7-T7, T7-P7, FP1-F3, F3-C3, FP2-F8, F8-T8, T8-P8 | 10.5 | 4 | 0.400 |
| chb03 | 4 | chb03_04 | 2162 | focal | 8 | FP1-F7, F7-T7, T7-P7, FP1-F3, F3-C3, FP2-F8, F8-T8, T8-P8 | 9.5 | 1 | 0.525 |
| chb03 | 5 | chb03_34 | 1982 | generalized | 18 | all 18 | — | — | — |
| chb03 | 6 | chb03_35 | 2592 | generalized | 18 | all 18 | — | — | — |
| chb03 | 7 | chb03_36 | 1725 | generalized | 18 | all 18 | — | — | — |
| chb06 | 1 | chb06_01 | 1724 | generalized | 18 | all 18 | — | — | — |
| chb06 | 2 | chb06_01 | 7461 | generalized | 18 | all 18 | — | — | — |
| chb06 | 3 | chb06_01 | 13525 | generalized | 18 | all 18 | — | — | — |
| chb06 | 4 | chb06_04 | 327 | generalized | 18 | all 18 | — | — | — |
| chb06 | 5 | chb06_04 | 6211 | generalized | 18 | all 18 | — | — | — |
| chb06 | 6 | chb06_09 | 12500 | generalized | 18 | all 18 | — | — | — |
| chb06 | 7 | chb06_10 | 10833 | generalized | 18 | all 18 | — | — | — |
| chb06 | 8 | chb06_13 | 506 | generalized | 18 | all 18 | — | — | — |
| chb06 | 9 | chb06_18 | 7799 | generalized | 18 | all 18 | — | — | — |
| chb06 | 10 | chb06_24 | 9387 | generalized | 18 | all 18 | — | — | — |
| chb13 | 1 | chb13_19 | 2077 | focal | 6 | FP1-F7, F7-T7, T7-P7, FP2-F8, F8-T8, T8-P8 | 8.0 | 1 | 0.611 |
| chb13 | 2 | chb13_21 | 934 | focal | 6 | FP1-F7, F7-T7, T7-P7, FP2-F8, F8-T8, T8-P8 | 12.0 | 1 | 0.403 |
| chb13 | 3 | chb13_40 | 142 | focal | 3 | FP1-F7, F7-T7, FP1-F3 | 2.0 | 1 | 0.956 |
| chb13 | 4 | chb13_40 | 530 | focal | 3 | FP1-F7, F7-T7, FP1-F3 | 3.0 | 1 | 0.956 |
| chb13 | 5 | chb13_55 | 458 | focal | 6 | FP1-F7, F7-T7, T7-P7, FP2-F8, F8-T8, T8-P8 | 7.5 | 2 | 0.583 |
| chb13 | 6 | chb13_55 | 2436 | focal | 6 | FP1-F7, F7-T7, FP1-F3, F3-C3, FP2-F4, FP2-F8 | 10.0 | 1 | 0.514 |
| chb13 | 7 | chb13_58 | 2474 | focal | 6 | FP1-F7, F7-T7, FP1-F3, F3-C3, FP2-F4, FP2-F8 | 5.0 | 1 | 0.625 |
| chb13 | 8 | chb13_59 | 3339 | focal | 6 | FP1-F7, F7-T7, FP1-F3, F3-C3, FP2-F4, F4-C4 | 4.0 | 1 | 0.764 |
| chb13 | 9 | chb13_60 | 638 | focal | 6 | FP1-F7, F7-T7, FP1-F3, F3-C3, FP2-F4, F4-C4 | 6.5 | 3 | 0.681 |
| chb13 | 10 | chb13_62 | 851 | focal | 6 | FP1-F7, F7-T7, FP1-F3, F3-C3, FP2-F4, F4-C4 | 4.5 | 1 | 0.764 |
| chb13 | 11 | chb13_62 | 1626 | generalized | 18 | all 18 | — | — | — |
| chb13 | 12 | chb13_62 | 2664 | focal | 6 | FP1-F7, F7-T7, FP1-F3, F3-C3, FP2-F4, F4-C4 | 9.0 | 2 | 0.583 |
| chb14 | 1 | chb14_03 | 1986 | focal | 10 | FP1-F7, F7-T7, T7-P7, P7-O1, FP1-F3, FP2-F4, FP2-F8, F8-T8, T8-P8, P8-O2 | 9.5 | 1 | 0.562 |
| chb14 | 2 | chb14_04 | 1372 | focal | 5 | FP1-F7, P7-O1, FP1-F3, FP2-F4, FP2-F8 | 4.0 | 1 | 0.815 |
| chb14 | 3 | chb14_04 | 2817 | focal | 4 | FP1-F7, FP1-F3, FP2-F4, FP2-F8 | 7.0 | 1 | 0.696 |
| chb14 | 4 | chb14_06 | 1911 | focal | 8 | FP1-F7, F7-T7, T7-P7, FP1-F3, FP2-F4, FP2-F8, F8-T8, T8-P8 | 14.5 | 4 | 0.138 |
| chb14 | 5 | chb14_11 | 1838 | focal | 4 | FP1-F7, FP1-F3, FP2-F4, FP2-F8 | 5.5 | 3 | 0.679 |
| chb14 | 6 | chb14_17 | 3239 | focal | 4 | FP1-F7, FP1-F3, FP2-F4, FP2-F8 | 9.5 | 2 | 0.500 |
| chb14 | 7 | chb14_18 | 1039 | focal | 6 | FP1-F7, F7-T7, T7-P7, FP1-F3, FP2-F4, FP2-F8 | 7.5 | 2 | 0.597 |
| chb14 | 8 | chb14_27 | 2833 | focal | 5 | FP1-F7, F7-T7, FP1-F3, FP2-F4, FP2-F8 | 4.0 | 2 | 0.738 |
| chb15 | 1 | chb15_06 | 272 | focal | 4 | T7-P7, P7-O1, FP2-F4, FP2-F8 | 7.0 | 3 | 0.571 |
| chb15 | 2 | chb15_10 | 1082 | focal | 5 | T7-P7, FP2-F4, F4-C4, FP2-F8, F8-T8 | 4.0 | 1 | 0.923 |
| chb15 | 3 | chb15_15 | 1591 | focal | 2 | T7-P7, P7-O1 | 5.5 | 1 | 0.750 |
| chb15 | 4 | chb15_17 | 1925 | focal | 3 | T7-P7, FP2-F4, F4-C4 | 16.0 | 1 | 0.356 |
| chb15 | 5 | chb15_20 | 607 | focal | 2 | T7-P7, T8-P8 | 5.0 | 2 | 0.781 |
| chb15 | 6 | chb15_22 | 760 | focal | 3 | T7-P7, P3-O1, T8-P8 | 7.0 | 4 | 0.578 |
| chb15 | 7 | chb15_28 | 876 | focal | 2 | T7-P7, P7-O1 | 5.5 | 4 | 0.750 |
| chb15 | 8 | chb15_31 | 1751 | focal | 2 | T7-P7, P3-O1 | 2.0 | 1 | 0.969 |
| chb15 | 9 | chb15_40 | 834 | focal | 1 | T7-P7 | 4.0 | 4 | 0.824 |
| chb15 | 10 | chb15_40 | 2378 | focal | 2 | T7-P7, P7-O1 | 4.0 | 2 | 0.844 |
| chb15 | 11 | chb15_40 | 3362 | focal | 1 | T7-P7 | 4.0 | 4 | 0.824 |
| chb15 | 12 | chb15_46 | 3322 | focal | 2 | T7-P7, P3-O1 | 2.5 | 1 | 0.938 |
| chb15 | 13 | chb15_49 | 1108 | focal | 3 | T7-P7, P3-O1, T8-P8 | 13.0 | 8 | 0.311 |
| chb15 | 14 | chb15_52 | 778 | focal | 2 | T7-P7, P3-O1 | 8.5 | 3 | 0.562 |
| chb15 | 15 | chb15_54 | 263 | focal | 2 | T7-P7, P3-O1 | 2.0 | 1 | 0.969 |
| chb15 | 16 | chb15_54 | 843 | focal | 2 | T7-P7, P3-O1 | 5.0 | 1 | 0.781 |
| chb15 | 17 | chb15_54 | 1524 | focal | 3 | FP1-F7, F7-T7, T7-P7 | 9.0 | 2 | 0.511 |
| chb15 | 18 | chb15_54 | 2179 | focal | 2 | T7-P7, P3-O1 | 5.0 | 1 | 0.781 |
| chb15 | 19 | chb15_54 | 3428 | focal | 1 | T7-P7 | 13.0 | 13 | 0.294 |
| chb15 | 20 | chb15_62 | 751 | focal | 2 | T7-P7, P3-O1 | 2.5 | 1 | 0.938 |
| chb16 | 1 | chb16_10 | 2290 | focal | 6 | T7-P7, P7-O1, FP2-F4, FP2-F8, F8-T8, T8-P8 | 12.5 | 7 | 0.208 |
| chb16 | 2 | chb16_11 | 1120 | focal | 6 | FP1-F7, F7-T7, T7-P7, FP2-F4, FP2-F8, F8-T8 | 12.5 | 6 | 0.306 |
| chb16 | 3 | chb16_14 | 1854 | focal | 6 | FP1-F7, F7-T7, T7-P7, FP2-F4, F8-T8, T8-P8 | 12.5 | 6 | 0.264 |
| chb16 | 4 | chb16_16 | 1214 | focal | 7 | F7-T7, T7-P7, FP1-F3, FP2-F4, FP2-F8, F8-T8, T8-P8 | 11.0 | 6 | 0.273 |
| chb16 | 5 | chb16_17 | 227 | focal | 5 | T7-P7, FP2-F4, FP2-F8, F8-T8, T8-P8 | 11.0 | 6 | 0.292 |
| chb16 | 6 | chb16_17 | 1694 | focal | 6 | FP1-F7, T7-P7, P7-O1, FP2-F4, F8-T8, T8-P8 | 15.5 | 9 | 0.097 |
| chb16 | 7 | chb16_17 | 2162 | focal | 5 | T7-P7, P7-O1, FP2-F4, F8-T8, T8-P8 | 11.0 | 7 | 0.385 |
| chb16 | 8 | chb16_17 | 3290 | focal | 4 | T7-P7, FP2-F4, F8-T8, T8-P8 | 10.0 | 8 | 0.357 |
| chb16 | 9 | chb16_18 | 627 | focal | 5 | T7-P7, FP2-F4, FP2-F8, F8-T8, T8-P8 | 14.0 | 8 | 0.231 |
| chb16 | 10 | chb16_18 | 1909 | focal | 5 | F7-T7, T7-P7, FP2-F4, F8-T8, T8-P8 | 14.0 | 9 | 0.185 |
| chb17 | 1 | chb17a_03 | 2282 | focal | 4 | F7-T7, T7-P7, F8-T8, T8-P8 | 6.5 | 2 | 0.732 |
| chb17 | 2 | chb17a_04 | 3025 | focal | 4 | F7-T7, T7-P7, F8-T8, T8-P8 | 3.0 | 1 | 0.946 |
| chb17 | 3 | chb17b_63 | 3136 | focal | 5 | FP1-F7, FP1-F3, FP2-F4, F8-T8, T8-P8 | 10.0 | 5 | 0.446 |
| chb18 | 1 | chb18_29 | 3477 | focal | 7 | FP1-F3, F3-C3, FP2-F4, F4-C4, FP2-F8, F8-T8, T8-P8 | 10.0 | 4 | 0.416 |
| chb18 | 2 | chb18_30 | 541 | focal | 3 | FP2-F8, F8-T8, T8-P8 | 7.0 | 1 | 0.778 |
| chb18 | 3 | chb18_31 | 2087 | focal | 5 | T7-P7, P7-O1, FP2-F8, F8-T8, T8-P8 | 9.0 | 7 | 0.354 |
| chb18 | 4 | chb18_32 | 1908 | focal | 4 | F7-T7, T7-P7, FP2-F4, FP2-F8 | 13.0 | 4 | 0.321 |
| chb18 | 5 | chb18_35 | 2196 | focal | 4 | FP1-F7, FP1-F3, FP2-F4, FP2-F8 | 14.0 | 9 | 0.196 |
| chb18 | 6 | chb18_36 | 463 | focal | 6 | F7-T7, T7-P7, FP2-F4, FP2-F8, F8-T8, T8-P8 | 14.0 | 10 | 0.125 |

76 rows. Seizures are numbered from 1 within each patient, in recording order. Onset is the annotated
onset in seconds from the start of that recording file. Channels are listed in montage order; one
seizure (chb15, seizure 17) is stored in the source file in reading order and is reordered here, with
the same three channels. "Median rank" and "best rank" are the positions the annotated channels hold in
the model's ranking of the eighteen channels, where rank 1 is the most anomalous; a random ranking gives
a median of 9.5. AUROC is the per-seizure agreement of §3.6.3. A generalized seizure involves all
eighteen channels, carries no channel contrast, and is excluded from the channel metrics (§2.5.2).

Summary, recomputed from the rows: 62 focal and 14 generalized (chb06 ×10, chb03 ×3, chb13 ×1); focal
seizures carry 1 to 10 channels, mean 4.55 (25.3 % of the montage). Every per-patient count and mean
agrees with Table A.13 (the annotation composition moved out of Chapter 3). Over the 62 focal seizures the median of the per-seizure median ranks is 8.2,
the top-ranked channel is annotated in 24 of them, and 32.0 % of the |S| highest-ranked channels are
annotated, against an annotated prevalence of 25.3 %.

*Source: `results/attribution_v7/labels/ictal_channels_FINAL.csv` (label source
`human_blind_supervisor_approved_2026-09` on all 76 rows), parsed from
`results/attribution_v7/labels/source/Channel_label_approved.md`; rank columns from
`results/attribution_v7/rank_readout_perseizure.csv`, produced by `rank_readout.py`, which reproduced
the per-seizure AUROC of `attribution_perseizure.csv` on all 62 focal seizures before writing.*

## Table A.3 — Composition of the reconstructed evaluation timeline

| Patient | Timeline positions | Stored scores | Windows removed | Removed | Array exhausted at | Substituted |
|---|---|---|---|---|---|---|
| chb03 | 30,395 | 17,204 | 13,191 | 43.4% | 58.1% | 49.4% |
| chb06 | 47,523 | 19,826 | 27,697 | 58.3% | 43.7% | 66.9% |
| chb13 | 25,224 | 12,452 | 12,772 | 50.6% | 41.9% | 57.6% |
| chb14 | 20,651 | 13,983 | 6,668 | 32.3% | 70.7% | 40.0% |
| chb15 | 27,374 | 17,026 | 10,348 | 37.8% | 59.9% | 51.3% |
| chb16 | 13,530 | 6,428 | 7,102 | 52.5% | 37.6% | 62.3% |
| chb17 | 18,310 | 9,304 | 9,006 | 49.2% | 52.4% | 50.4% |
| chb18 | 29,668 | 14,853 | 14,815 | 49.9% | 46.3% | 53.4% |
| **Mean** | | | | **46.8%** | **51.3%** | **53.9%** |

"Substituted" is the share of all timeline positions that carry a resampled score: the positions left
after the stored array is exhausted, together with the post-seizure positions inside each seizure's
recording file. The substituted fraction averages 53.9 % and ranges from 40.0 % for chb14 to 66.9 % for
chb06. The false-alarm rate reported in Chapter 3 is measured on these timelines, and the direction of
the resulting bias is not established.

*Source: `results/diagnostics/timeline_composition.csv` (columns `eligible_windows`,
`committed_inter_windows`, `dropped_windows`, `dropped_fraction`, `exhaustion_point_fraction`,
`substituted_fraction`), produced by `src/dataprep/timeline_composition_diagnostic.py`. Removed =
positions − stored, checked for all eight rows.*

## Table A.4 — Concentration of the top-ranked channel against a random null

| Patient | Seizures | Distinct top-ranked channels | Largest share | Null 95th percentile | Outcome |
|---|---|---|---|---|---|
| chb03 | 7 | 5 | 0.429 | 0.429 | within the null |
| chb06 | 10 | 7 | 0.300 | 0.300 | within the null |
| chb13 | 12 | 6 | 0.417 | 0.333 | **concentrated** |
| chb14 | 8 | 5 | 0.250 | 0.375 | within the null |
| chb15 | 20 | 9 | 0.500 | 0.250 | **concentrated** |
| chb16 | 10 | 4 | 0.500 | 0.300 | **concentrated** |
| chb17 | 3 | 3 | 0.333 | 0.667 | within the null |
| chb18 | 6 | 5 | 0.333 | 0.500 | within the null |

Three of eight patients repeat their top-ranked channel more often than chance allows. This agrees with
the comparison against the annotation, in which a patient's average map scores higher than the map of
the individual seizure (Table 3.5): within a patient, the ranking behaves partly as a patient-level
channel pattern, not a per-seizure one. The table uses no annotation; the null is 2,000 random draws of
a top-ranked channel per seizure.

*Source: `results/attribution_v6/attribution_diagnostics.csv` (label-free, seed 42, 95th-percentile
aggregation); `docs/ATTRIBUTION_SPEC.md` §9.2; `docs/VERIFIED_NUMBERS.md` Part 6.4c.*

## Table A.5 — Software and libraries

| Package | Version | Role |
|---|---|---|
| Python | 3.11.9 | Runtime |
| numpy | 2.4.4 | Array computation throughout |
| scipy | 1.17.1 | Filtering, spectral estimation, statistical tests |
| pandas | 3.0.3 | Result tables and grid files |
| mne | 1.12.1 | Reading the recording files |
| torch | 2.12.0 | Model definition and training |
| torch-geometric | 2.7.0 | Graph convolution layers |
| scikit-learn | 1.8.0 | Shrinkage covariance estimation and discrimination measures |
| ruptures | 1.1.10 | Change-point detection |
| timescoring | 0.0.7 | Event-level scoring |
| matplotlib | 3.10.8 | Figures |
| networkx | 3.6.1 | Graph handling |
| tqdm | 4.67.3 | Progress reporting |

The remaining entries of the environment snapshot are transitive dependencies and are not listed.

*Source: `docs/requirements_snapshot.txt`. Every row, including the Python version, was confirmed
against the running environment on 2026-09-22 (`python --version` and `importlib.metadata`); all
thirteen agree with the snapshot.*

---

## Still to be added to this pack (assembly step)

The page cut of 2026-09-23 moved exhibits out of Chapters 1 to 4. They keep their content unchanged and
take appendix numbers, listed in `EXHIBIT_RENUMBER_MAP.md`:

- **Figures A.1 to A.9**, from Chapters 1 to 3 (seizure phases, raw against preprocessed, reconstruction
  inversion, event scoring, detection latency, window against event, false-positive EEG, synthetic
  attribution grid, diffuseness).
- **Tables A.6 to A.14**: task per week (was 1.4), preprocessing steps (was 2.3), synthetic grid design
  (was 2.7), candidate corpora (was 2.1), model and training configuration (was 2.5), per-patient event
  results (was 3.3), synthetic criteria (was 3.6), annotation composition (was 3.7), cost profile
  (was 4.2).

Each is already cited from the body at the point where it used to sit, so only the moves themselves
remain.

