# Tables Pack — Appendices

Every table the report needs, filled from committed sources. One block per exhibit, in document
order. Each block ends with a `Source:` line naming the file the values were read from, so a
reviewer can trace any cell without asking.

Authority: `docs/VERIFIED_NUMBERS.md` for every number, `docs/LOCKED_DOCS_ADDENDUM.md` where it
supersedes the exhibit list, `FIGURES_TABLES_LIST.md` for what each table must contain.

## Rules applied throughout

1. Three decimals for discrimination, sensitivity, precision and F1; one decimal for false alarms
   per day. Same rule in tables and figures.
2. No confidence intervals on any detection table. Intervals appear only on Table 3.9.
3. No internal shorthand: no lever codes, no file names, no phase names, no branch nicknames in a
   table cell or heading.
4. A cell whose value has not been read from a file is written `— not measured` and never left
   blank and never estimated. Two tables below are deliberately incomplete for this reason and say
   so at the top of the block.
5. Patient identifiers keep the corpus form (chb03, chb06, …) so the tables agree with the figures.

This file holds Tables A.1 through A.7. See `tables/README.md` for what lives in the other three
chapter files and for which tables are still unfilled.

---

## Table A.1 — Corpus metadata for all 23 subjects

| Patient | Set | Recordings | Recorded hours (h) | Seizures | Total seizure duration (s) |
|---|---|---|---|---|---|
| chb01 | train | 42 | 40.55 | 7 | 442 |
| chb02 | train | 36 | 35.27 | 3 | 172 |
| chb03 | held-out | 38 | 38.0 | 7 | 402 |
| chb04 | train | 42 | 156.06 | 4 | 378 |
| chb05 | train | 39 | 39.0 | 5 | 558 |
| chb06 | held-out | 18 | 66.73 | 10 | 153 |
| chb07 | train | 19 | 67.05 | 3 | 325 |
| chb08 | train | 20 | 20.01 | 5 | 919 |
| chb09 | train | 19 | 67.87 | 4 | 276 |
| chb10 | validation | 25 | 50.02 | 7 | 447 |
| chb11 | validation | 35 | 34.79 | 3 | 806 |
| chb12 | train | 24 | 23.69 | 40 | 1475 |
| chb13 | held-out | 33 | 33.0 | 12 | 535 |
| chb14 | held-out | 26 | 26.0 | 8 | 169 |
| chb15 | held-out | 40 | 40.01 | 20 | 1992 |
| chb16 | held-out | 19 | 19.0 | 10 | 84 |
| chb17 | held-out | 21 | 21.01 | 3 | 293 |
| chb18 | held-out | 36 | 35.63 | 6 | 317 |
| chb19 | train | 30 | 29.93 | 3 | 236 |
| chb20 | train | 29 | 27.6 | 8 | 294 |
| chb21 | train | 33 | 32.83 | 4 | 199 |
| chb22 | validation | 31 | 31.0 | 3 | 204 |
| chb23 | train | 9 | 26.56 | 7 | 424 |

23 rows, one per subject. Per-set totals (recordings, hours, seizures) are cross-checked in
`docs/VERIFIED_NUMBERS.md` Part 3 and reproduced by this table's own emission self-check.

*Source: `data/summaries/*.txt`, parsed by `evaluation_protocol.parse_summary_edf_list` and the
`data/splits/split_main.json` set assignment; emitted and rendered by `src/figures/emit_tables.py`
(`tables/csv/table_A1_corpus_metadata.csv`), self-checked against `docs/VERIFIED_NUMBERS.md`
Part 3.*

## Table A.2 — Channel annotation for all 76 held-out seizures

| Patient | Seizure index | Annotated channels | Label source |
|---|---|---|---|
| chb03 | 0 | T7-P7\|P7-O1 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb03 | 1 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb03 | 2 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb03 | 3 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb03 | 4 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb03 | 5 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb03 | 6 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb06 | 0 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb06 | 1 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb06 | 2 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb06 | 3 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb06 | 4 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb06 | 5 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb06 | 6 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb06 | 7 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb06 | 8 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb06 | 9 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb13 | 0 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb13 | 1 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb13 | 2 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb13 | 3 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb13 | 4 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb13 | 5 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb13 | 6 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb13 | 7 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb13 | 8 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb13 | 9 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb13 | 10 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb13 | 11 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb14 | 0 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb14 | 1 | T7-P7\|P7-O1 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb14 | 2 | T7-P7\|P7-O1 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb14 | 3 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb14 | 4 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb14 | 5 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb14 | 6 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb14 | 7 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb15 | 0 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb15 | 1 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb15 | 2 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb15 | 3 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb15 | 4 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb15 | 5 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb15 | 6 | T7-P7\|P7-O1 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb15 | 7 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb15 | 8 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb15 | 9 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb15 | 10 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb15 | 11 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb15 | 12 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb15 | 13 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb15 | 14 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb15 | 15 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb15 | 16 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb15 | 17 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb15 | 18 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb15 | 19 | T7-P7\|P7-O1 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb16 | 0 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb16 | 1 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb16 | 2 | F8-T8\|T8-P8 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb16 | 3 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb16 | 4 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb16 | 5 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb16 | 6 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb16 | 7 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb16 | 8 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb16 | 9 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb17 | 0 | F8-T8\|T8-P8 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb17 | 1 | F8-T8\|T8-P8 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb17 | 2 | T8-P8\|F8-T8 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb18 | 0 | F8-T8\|T8-P8 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb18 | 1 | T7-P7 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb18 | 2 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb18 | 3 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb18 | 4 | T7-P7\|P7-O1 | AI-DRAFT (attribution_v5 reader pass, verbatim) |
| chb18 | 5 | nan | AI-DRAFT (attribution_v5 reader pass, verbatim) |

76 rows, one per held-out seizure. `nan` marks a seizure with no annotated channel (40 of the 76 —
see `docs/VERIFIED_NUMBERS.md` Part 7.5); it is left as the literal parsed value, not written as
"— not measured", because the absence of a focal annotation is itself the recorded fact, not a
missing measurement. The `label_source` column is carried through **verbatim**: every one of the
76 rows reads the same AI-draft banner. These annotations are a machine-generated draft, not a
clinician's reading, and the report must not describe agreement against them as clinical
validation (`docs/VERIFIED_NUMBERS.md` §7.1; `docs/ATTRIBUTION_SPEC.md` §7).

*Source: `results/attribution_v6/labels/ictal_channels_DRAFT.csv`; emitted and rendered by
`src/figures/emit_tables.py` (`tables/csv/table_A2_channel_annotation.csv`), self-checked for row
count and label-source uniformity.*

## Table A.3 — Full 384-row parameter grid

**Not rendered to markdown** (384 rows; docs/FIGURE_ROUND6.md §3). This table goes into the report
as a CSV attachment or a long appendix listing rather than an inline markdown table.

See `tables/csv/table_A3_full_grid.csv`: 384 rows, 8 held-out patients × 48 cells each (8 change-
point magnitude percentiles × 6 penalty multipliers), the same grid Table 3.3 and Table 3.4 are
drawn from.

*Source: `results/phaseB/tier2/rlg_test/final_eval_seed42.csv`, pass-through; emitted by
`src/figures/emit_tables.py`.*

## Table A.4 — Concentration of the top-ranked channel against a random null

| Patient | Seizures | Distinct top-ranked channels | Largest share | Null 95th percentile | Verdict |
|---|---|---|---|---|---|
| chb03 | 7 | 5 | 0.429 | 0.429 | within the null |
| chb06 | 10 | 7 | 0.300 | 0.300 | within the null |
| chb13 | 12 | 6 | 0.417 | 0.333 | **concentrated** |
| chb14 | 8 | 5 | 0.250 | 0.375 | within the null |
| chb15 | 20 | 9 | 0.500 | 0.250 | **concentrated** |
| chb16 | 10 | 4 | 0.500 | 0.300 | **concentrated** |
| chb17 | 3 | 3 | 0.333 | 0.667 | within the null |
| chb18 | 6 | 5 | 0.333 | 0.500 | within the null |

Three of eight patients repeat their top-ranked channel more often than chance allows. This is
independent evidence for the limitation the annotation comparison raises: within a patient, the
method behaves partly as a patient-level channel prior rather than a per-seizure one. It
strengthens that limitation rather than weakening the method.

*Source: `results/attribution_v6/attribution_diagnostics.csv`; `docs/VERIFIED_NUMBERS.md`
Part 6.4c.*

## Table A.5 — Software and libraries

| Package | Version | Role |
|---|---|---|
| Python | 3.11 | Runtime |
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

*Source: `docs/requirements_snapshot.txt`. The Python version is stated by the interpreter path in
the session log and should be confirmed with `python --version` before the table is final.*

## Table A.6 — Pre-registration index

| # | Registered question | Gates |
|---|---|---|
| 01 | Retraining the graph autoencoder jointly on adjacency and node features | The model configuration in Table 2.7 and every result derived from it |
| 02 | A recurrent temporal readout | Withdrawn; the branch was dropped and replaced, and does not appear in the reported system |
| 03 | Derivation of the ensemble weights | The weighting discussion in Chapter 2 |
| 04 | A label-free per-patient false-alarm budget as the operating rule | The operating points in Table 3.3 and every gated comparison in Table 3.6 |
| 05 | Validation-derived operating points | The reported operating point, row 3 of Table 3.3 |
| 06 | A balanced operating point | Row 1 and row 2 of Table 3.3 |
| 07 | Per-patient rather than pooled budgeting | The operating rule applied in Table 3.4 |
| 08 | A window-level threshold as an alternative decision rule | Reported as a considered and rejected decision rule |
| 09 | A minimum event duration | The interval construction in Chapter 2 |
| — | Replacement of the recurrent readout by the latent readout | The three-readout design and its ablation, Table 3.6 |
| — | A directed-connectivity probe | Table 3.7 and the corresponding row of Table 3.6 |

Each entry fixed its hypothesis, its falsification criterion and its stopping condition before the
measurement was made. Where a criterion failed, the failure is reported and the construction was
revised; no criterion was revised after its result was seen, with the single exception recorded
with Table 3.8, where the criterion was reformulated and the reformulation is stated.

*Source: `docs/prereg/PREREG_01` through `PREREG_09`, `docs/PREREG_TIER2_amendment_A1.md`,
`docs/PREREG_TIER2_latent_ensemble.md`, `docs/PREREG_C0_connectivity_probe.md`. Titles above are
paraphrased for the reader; the appendix should give each document's own title.*

## Table A.7 — Top-3 ranked channels per seizure (label-free)

| Patient | Seizure index | Ictal windows | Rank-1 channel | Rank-1 score | Rank-2 channel | Rank-2 score | Rank-3 channel | Rank-3 score |
|---|---|---|---|---|---|---|---|---|
| chb03 | 0 | 14 | T7-P7 | 10.3073 | P7-O1 | 9.1051 | F3-C3 | 5.2172 |
| chb03 | 1 | 17 | C4-P4 | 8.8546 | FP1-F7 | 8.7019 | C3-P3 | 6.6263 |
| chb03 | 2 | 18 | FZ-CZ | 9.523 | P7-O1 | 8.6628 | C4-P4 | 7.1546 |
| chb03 | 3 | 14 | T7-P7 | 15.0526 | P7-O1 | 9.5816 | CZ-PZ | 7.6395 |
| chb03 | 4 | 13 | P4-O2 | 10.3839 | T7-P7 | 7.7327 | C4-P4 | 7.4587 |
| chb03 | 5 | 16 | P7-O1 | 7.1696 | FZ-CZ | 6.4531 | C3-P3 | 5.8664 |
| chb03 | 6 | 14 | T7-P7 | 10.8101 | C3-P3 | 7.6366 | FP1-F7 | 6.3834 |
| chb06 | 0 | 4 | F8-T8 | 3.844 | T8-P8 | 3.2864 | C4-P4 | 2.5355 |
| chb06 | 1 | 4 | P3-O1 | 9.3647 | P4-O2 | 8.2013 | C4-P4 | 7.1833 |
| chb06 | 2 | 4 | F3-C3 | 7.3177 | P4-O2 | 5.1231 | FZ-CZ | 5.0296 |
| chb06 | 3 | 6 | P4-O2 | 4.7161 | FP1-F3 | 4.3304 | F8-T8 | 3.929 |
| chb06 | 4 | 6 | F4-C4 | 3.53 | P3-O1 | 2.6117 | FP2-F4 | 2.0384 |
| chb06 | 5 | 4 | T8-P8 | 2.8274 | FP1-F3 | 2.4615 | CZ-PZ | 2.4398 |
| chb06 | 6 | 4 | FP2-F4 | 6.249 | T8-P8 | 6.2112 | F3-C3 | 5.1649 |
| chb06 | 7 | 4 | P3-O1 | 4.3307 | FP2-F4 | 2.9436 | FZ-CZ | 2.7754 |
| chb06 | 8 | 4 | P3-O1 | 4.4452 | P7-O1 | 3.0584 | C4-P4 | 2.8614 |
| chb06 | 9 | 5 | F3-C3 | 7.2738 | T7-P7 | 4.7922 | C4-P4 | 4.6819 |
| chb13 | 0 | 12 | FP1-F7 | 7.0926 | F8-T8 | 6.5624 | CZ-PZ | 6.4361 |
| chb13 | 1 | 18 | FP1-F7 | 9.0362 | CZ-PZ | 6.2876 | FP1-F3 | 4.8476 |
| chb13 | 2 | 9 | FP1-F7 | 9.8979 | FP1-F3 | 9.2388 | F3-C3 | 6.1838 |
| chb13 | 3 | 17 | FP1-F7 | 7.4148 | FZ-CZ | 7.1665 | F7-T7 | 7.1613 |
| chb13 | 4 | 6 | FP1-F3 | 6.6852 | F8-T8 | 6.1738 | F3-C3 | 5.931 |
| chb13 | 5 | 5 | FP2-F4 | 11.3686 | CZ-PZ | 10.9326 | C3-P3 | 9.771 |
| chb13 | 6 | 5 | F7-T7 | 8.1956 | FP1-F7 | 7.4285 | P3-O1 | 5.612 |
| chb13 | 7 | 17 | F7-T7 | 10.0741 | FP1-F7 | 8.6153 | FP1-F3 | 8.511 |
| chb13 | 8 | 6 | T8-P8 | 8.3557 | P3-O1 | 5.9927 | F4-C4 | 5.6581 |
| chb13 | 9 | 17 | FP1-F7 | 8.2861 | F7-T7 | 7.8573 | C3-P3 | 6.9877 |
| chb13 | 10 | 17 | F7-T7 | 9.9614 | C4-P4 | 8.9187 | P4-O2 | 7.3065 |
| chb13 | 11 | 15 | P3-O1 | 10.2418 | FP2-F4 | 8.398 | P8-O2 | 7.4714 |
| chb14 | 0 | 4 | P7-O1 | 4.8437 | F8-T8 | 4.1486 | F3-C3 | 2.4913 |
| chb14 | 1 | 5 | FP2-F8 | 15.2762 | FP2-F4 | 13.0127 | P4-O2 | 4.663 |
| chb14 | 2 | 6 | FP2-F8 | 6.8726 | P7-O1 | 6.8477 | FP1-F7 | 5.67 |
| chb14 | 3 | 5 | C3-P3 | 5.4856 | CZ-PZ | 5.4063 | C4-P4 | 4.6553 |
| chb14 | 4 | 11 | P7-O1 | 11.7649 | F8-T8 | 10.046 | FP1-F7 | 8.314 |
| chb14 | 5 | 6 | CZ-PZ | 6.4689 | FP2-F8 | 5.8768 | FP1-F7 | 5.3277 |
| chb14 | 6 | 7 | C3-P3 | 4.8656 | F7-T7 | 4.646 | FP2-F8 | 3.7812 |
| chb14 | 7 | 5 | P4-O2 | 7.5433 | F7-T7 | 4.3493 | FP1-F7 | 3.7114 |
| chb15 | 0 | 32 | FZ-CZ | 7.0563 | CZ-PZ | 6.5367 | P7-O1 | 5.496 |
| chb15 | 1 | 9 | F4-C4 | 9.6983 | T7-P7 | 7.2309 | FP1-F7 | 6.1393 |
| chb15 | 2 | 40 | P7-O1 | 9.5785 | F8-T8 | 7.3664 | FP1-F7 | 6.8583 |
| chb15 | 3 | 9 | T7-P7 | 8.0814 | P7-O1 | 6.5758 | P3-O1 | 6.09 |
| chb15 | 4 | 15 | FP1-F3 | 9.2554 | T8-P8 | 9.1707 | F8-T8 | 8.5301 |
| chb15 | 5 | 52 | F7-T7 | 10.6237 | FP2-F8 | 8.8336 | P8-O2 | 8.2842 |
| chb15 | 6 | 48 | F7-T7 | 10.9436 | F8-T8 | 9.6461 | FP2-F4 | 8.6838 |
| chb15 | 7 | 31 | P3-O1 | 8.7382 | P7-O1 | 7.9206 | T7-P7 | 7.6004 |
| chb15 | 8 | 16 | P3-O1 | 14.2142 | C3-P3 | 12.2898 | FP2-F8 | 10.7226 |
| chb15 | 9 | 31 | P3-O1 | 13.041 | T7-P7 | 10.4243 | F7-T7 | 8.7485 |
| chb15 | 10 | 17 | P3-O1 | 14.6308 | P4-O2 | 11.6461 | FP1-F7 | 9.899 |
| chb15 | 11 | 28 | P3-O1 | 10.8121 | FP2-F8 | 8.1152 | FP2-F4 | 7.5789 |
| chb15 | 12 | 35 | F7-T7 | 11.9001 | FP2-F8 | 9.3252 | FP1-F3 | 8.4169 |
| chb15 | 13 | 19 | F8-T8 | 19.0873 | F7-T7 | 17.6282 | P3-O1 | 10.9724 |
| chb15 | 14 | 15 | P3-O1 | 17.0773 | FP1-F3 | 8.5427 | T7-P7 | 8.0246 |
| chb15 | 15 | 45 | P3-O1 | 12.1687 | F3-C3 | 5.7284 | P7-O1 | 5.3845 |
| chb15 | 16 | 18 | P3-O1 | 14.4381 | T7-P7 | 9.7862 | P7-O1 | 8.5285 |
| chb15 | 17 | 19 | P3-O1 | 8.8585 | FP1-F7 | 7.4268 | P8-O2 | 7.1541 |
| chb15 | 18 | 8 | P4-O2 | 12.2087 | T8-P8 | 11.5361 | P3-O1 | 10.2817 |
| chb15 | 19 | 28 | P3-O1 | 13.3325 | P7-O1 | 11.1381 | F8-T8 | 8.3932 |
| chb16 | 0 | 3 | FZ-CZ | 11.1061 | F4-C4 | 10.753 | F3-C3 | 9.005 |
| chb16 | 1 | 3 | FZ-CZ | 12.8183 | P4-O2 | 12.731 | P3-O1 | 10.5924 |
| chb16 | 2 | 4 | P4-O2 | 7.5155 | C4-P4 | 7.4082 | FP2-F8 | 5.7133 |
| chb16 | 3 | 2 | FZ-CZ | 7.0821 | F3-C3 | 6.0791 | F4-C4 | 4.561 |
| chb16 | 4 | 3 | P4-O2 | 12.4876 | P8-O2 | 11.4046 | F3-C3 | 10.99 |
| chb16 | 5 | 2 | FZ-CZ | 12.5107 | P8-O2 | 11.6934 | P4-O2 | 11.458 |
| chb16 | 6 | 3 | P4-O2 | 10.3394 | FZ-CZ | 8.8825 | FP1-F3 | 8.1794 |
| chb16 | 7 | 3 | F3-C3 | 14.0253 | FZ-CZ | 13.3585 | P8-O2 | 11.2927 |
| chb16 | 8 | 3 | P8-O2 | 18.29 | FP1-F3 | 16.6714 | P4-O2 | 15.9912 |
| chb16 | 9 | 2 | FZ-CZ | 10.0715 | F3-C3 | 9.6786 | P3-O1 | 8.7398 |
| chb17 | 0 | 23 | P4-O2 | 6.109 | T7-P7 | 4.3869 | F4-C4 | 4.1715 |
| chb17 | 1 | 29 | T7-P7 | 4.6532 | F7-T7 | 4.3342 | FP2-F4 | 3.8061 |
| chb17 | 2 | 22 | CZ-PZ | 4.4862 | P4-O2 | 4.2387 | P7-O1 | 3.0577 |
| chb18 | 0 | 13 | P8-O2 | 8.9172 | P4-O2 | 8.304 | P3-O1 | 7.7708 |
| chb18 | 1 | 8 | F8-T8 | 5.6863 | P8-O2 | 5.2987 | T7-P7 | 5.1327 |
| chb18 | 2 | 18 | FP1-F7 | 9.7884 | P4-O2 | 7.9065 | C3-P3 | 7.5154 |
| chb18 | 3 | 14 | P4-O2 | 8.8501 | C3-P3 | 7.3537 | P8-O2 | 7.1145 |
| chb18 | 4 | 17 | C3-P3 | 17.9592 | P4-O2 | 12.0998 | P8-O2 | 10.7779 |
| chb18 | 5 | 13 | P4-O2 | 6.9872 | CZ-PZ | 6.2209 | P3-O1 | 6.0171 |

76 rows, one per held-out seizure (seed 42). Label-free: this table is derived only from the GAE's
own per-node reconstruction scores and does not depend on the draft channel annotation in
Table A.2.

*Source: `results/attribution_v6/` per-node score dumps (seed 42); emitted and rendered by
`src/figures/attribution_figures.py::table_top3` (`tables/csv/table_A7_top_channels.csv`).*
