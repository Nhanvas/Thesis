# Tables Pack — Appendices

Every table the report needs, filled from committed sources. One block per exhibit, in document
order. Each block ends with a `Source:` line naming the file the values were read from, so a
reviewer can trace any cell without asking.

Authority: `docs/VERIFIED_NUMBERS.md` for every number, `docs/LOCKED_DOCS_ADDENDUM.md` where it
supersedes the exhibit list, `FIGURES_TABLES_LIST.md` for what each table must contain.

## Rules applied throughout

1. Three decimals for discrimination, sensitivity, precision and F1; one decimal for false alarms
   per day. Same rule in tables and figures.
2. No confidence intervals on any detection table. Intervals appear only on Table 3.7.
3. No internal shorthand: no lever codes, no file names, no phase names, no branch nicknames in a
   table cell or heading.
4. A cell whose value has not been read from a file is written `— not measured` and never left
   blank and never estimated.
5. Patient identifiers keep the corpus form (chb03, chb06, …) so the tables agree with the figures.

This file holds Tables A.1 through A.6. See `tables/README.md` for what lives in the other four
chapter files.

---

## Table A.1 — Corpus metadata for all 23 subjects

| Patient | Set | Recordings | Recorded hours (h) | Seizures | Total seizure duration (s) |
|---|---|---|---|---|---|
| chb01 | train | 42 | 40.55 | 7 | 442 |
| chb02 | train | 36 | 35.27 | 3 | 172 |
| chb03 | test | 38 | 38.0 | 7 | 402 |
| chb04 | train | 42 | 156.06 | 4 | 378 |
| chb05 | train | 39 | 39.0 | 5 | 558 |
| chb06 | test | 18 | 66.73 | 10 | 153 |
| chb07 | train | 19 | 67.05 | 3 | 325 |
| chb08 | train | 20 | 20.01 | 5 | 919 |
| chb09 | train | 19 | 67.87 | 4 | 276 |
| chb10 | validation | 25 | 50.02 | 7 | 447 |
| chb11 | validation | 35 | 34.79 | 3 | 806 |
| chb12 | train | 24 | 23.69 | 40 | 1475 |
| chb13 | test | 33 | 33.0 | 12 | 535 |
| chb14 | test | 26 | 26.0 | 8 | 169 |
| chb15 | test | 40 | 40.01 | 20 | 1992 |
| chb16 | test | 19 | 19.0 | 10 | 84 |
| chb17 | test | 21 | 21.01 | 3 | 293 |
| chb18 | test | 36 | 35.63 | 6 | 317 |
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

## Table A.2 — Channel annotation for all 76 test seizures

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

76 rows, one per test seizure. `nan` marks a seizure with no annotated channel (40 of the 76 —
see `docs/VERIFIED_NUMBERS.md` Part 7.5); it is left as the literal parsed value, not written as
"— not measured", because the absence of a focal annotation is itself the recorded fact, not a
missing measurement. The `label_source` column is carried through **verbatim**: every one of the
76 rows reads the same AI-draft banner. These annotations are a machine-generated draft, not a
clinician's reading, and the report must not describe agreement against them as clinical
validation (`docs/VERIFIED_NUMBERS.md` §7.1; `docs/ATTRIBUTION_SPEC.md` §7).

*Source: `results/attribution_v6/labels/ictal_channels_DRAFT.csv`; emitted and rendered by
`src/figures/emit_tables.py` (`tables/csv/table_A2_channel_annotation.csv`), self-checked for row
count and label-source uniformity.*

## Table A.3 — Composition of the reconstructed evaluation timeline

Artifact rejection removes background windows without recording their positions, so a stored score
array holds fewer values than the timeline it has to fill. A reconstructed timeline shifts the
surviving scores out of their original positions and, once the array is exhausted, fills the remainder
by resampling from that patient's own background. The resampling preserves the marginal distribution
of the background but not its temporal autocorrelation.

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

The substituted fraction averages 53.9% and ranges from 40.0% for chb14 to 66.9% for chb06. **The
false-alarm rate reported in Chapter 3 is measured on these timelines, and the direction of the
resulting bias is not established.** That sentence is mandatory wherever this table is discussed.

*Source: `results/diagnostics/timeline_composition.csv`.*

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
| 01 | Retraining the graph autoencoder jointly on adjacency and node features | The model configuration in Table 2.5 and every result derived from it |
| 02 | A recurrent temporal readout | Withdrawn; the branch was dropped and replaced, and does not appear in the reported system |
| 03 | Derivation of the ensemble weights | The weighting discussion in Chapter 2 |
| 04 | A label-free per-patient false-alarm budget as the operating rule | The operating points in Table 3.2 and every gated comparison in Table 3.5 |
| 05 | Validation-derived operating points | The reported operating point, row 3 of Table 3.2 |
| 06 | A balanced operating point | Row 1 and row 2 of Table 3.2 |
| 07 | Per-patient rather than pooled budgeting | The operating rule applied in Table 3.3 |
| 08 | A window-level threshold as an alternative decision rule | Reported as a considered and rejected decision rule |
| 09 | A minimum event duration | The interval construction in Chapter 2 |
| — | Replacement of the recurrent readout by the latent readout | The three-readout design and its ablation, Table 3.5 |
| — | A directed-connectivity probe | §3.5.2 and the corresponding row of Table 3.5 |

Each entry fixed its hypothesis, its falsification criterion and its stopping condition before the
measurement was made. Where a criterion failed, the failure is reported and the construction was
revised; no criterion was revised after its result was seen, with the single exception recorded
with Table 3.6, where the criterion was reformulated and the reformulation is stated.

*Source: `docs/prereg/PREREG_01` through `PREREG_09`, `docs/PREREG_TIER2_amendment_A1.md`,
`docs/PREREG_TIER2_latent_ensemble.md`, `docs/PREREG_C0_connectivity_probe.md`. Titles above are
paraphrased for the reader; the appendix should give each document's own title.*

