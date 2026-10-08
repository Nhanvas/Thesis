# Verified Corrections — writing phase

Every entry below was settled by opening a file or running a command during the report-writing sessions
of 2026-09-12. Each one **supersedes** a statement that is still carried, at the time of writing, by the
project instructions, an older revision of a caption sheet or table pack, or a drawn figure. This file
exists so that none of them is re-litigated a fifth time.

Authority is unchanged: `RESULTS_OF_RECORD_phaseB.md` for numbers, `PROVENANCE.md` for artifact
identity, `REPO_MAP.md` for paths. This file records where a *derived* statement went wrong, and what
the evidence says instead.

---

## 1 · Common average reference exists and is part of the pipeline

**Wrong statement, now retired:** CAR does not exist in this project's code, so the two paragraphs
describing it were cut from Chapter 2.

**Evidence.** `apply_car` is defined at `src/dataprep/graph_construction.py:84` and called inside the
adjacency builders at lines 260 and 380. It subtracts the across-channel mean at each time point, on
each analysis window, before wPLI and AEC are computed. Its own docstring states that it must be
applied before wPLI. Every figure generator that builds an adjacency calls it.

**How the error happened.** The confirming grep covered `preprocessing.py` and `build_graphs.py` only.
It returned nothing, and the empty result was read as proof of absence. `graph_construction.py`, where
the function actually lives, was not in the search path.

**What follows.**
- CAR is a graph-construction step, not a preprocessing step. It is correctly absent from the
  preprocessing table, and the stored signals in `data/processed/` are not CAR-referenced.
- Chapter 2 §2.2.1 and §2.2.5 describe it. Both were restored.
- **Do not credit CAR with resistance to volume conduction.** That is wPLI's own property, since wPLI
  uses only the imaginary part of the cross-spectrum, and the chapter says so two paragraphs later. AEC
  is the branch that benefits. The defensible claim is that the reference alters estimated inter-channel
  relationships, so it is applied where those relationships are computed and nowhere else.
- Applying CAR on an already bipolar montage is unusual and is the likeliest question at the defense.
  There is no ablation for this step; the honest answer is that it was in the locked pipeline.

---

## 2 · Preprocessing step order: post-seizure exclusion precedes artifact rejection

**Wrong statement, now retired:** artifact rejection is step 4 and the post-seizure exclusion step 5.

**Evidence.** In `src/dataprep/preprocessing.py`, `compute_subject_stats` builds the post-seizure
buffer mask and skips every ictal or buffered window before accumulating the per-channel mean and
standard deviation. The artifact threshold is five times that standard deviation. The exclusion
therefore has to come first: the threshold is derived from statistics the exclusion has already
filtered.

**How the error happened.** The file's opening docstring numbers amplitude artifact rejection as
"Step 4". A table was numbered from the docstring rather than from the executed order.

**What follows.**
- `tables/tables_ch2.md` Table 2.3: corrected, and both writer's traps are recorded in the block.
- Chapter 2 §2.2.2 and Table 2.3: corrected, and the dependency between the two steps is now stated.
- **Figure 2.4 is drawn with the two boxes the wrong way round and needs redrawing.** This is the only
  outstanding artefact.

---

## 3 · The background statistics are subsampled, at a stride whose value is unread

**Two wrong statements, one in each direction.** First, that the statistics come from a fixed
one-in-ten subsample, asserted from `PROPOSED_SOLUTION.md`, a planning document. Then, on seeing
Welford's online algorithm named in the code, that there is no subsample at all.

**Evidence.** `compute_subject_stats` skips every ictal or buffered window, then advances a counter and
processes only every `STATS_SUBSAMPLE`-th surviving window. The stride is real. Welford's algorithm and
a stride are not alternatives; the algorithm streams whatever the loop feeds it.

**What follows.** Chapter 2 §2.2.2 says "a fixed subsample taken at a regular stride", which is true
whatever the constant turns out to be. To name the ratio:
`grep -n "STATS_SUBSAMPLE" src/dataprep/preprocessing.py`. The same output also confirms entry 2, since
the ictal-and-buffered skip sits above the subsample counter in the same loop.

**Worth noting.** The second error was mine, and it was the same mistake as the first in reverse:
inferring absence from a partial view instead of reading the loop.

---

## 4 · The ensemble weight surface is not flat

**Wrong statement, now retired, and this is its fifth appearance:** the weight surface is flat, so equal
weighting falls within tolerance.

**Evidence.** `VERIFIED_NUMBERS.md` Part 5 and `LOCKED_DOCS_ADDENDUM.md` §1.3: the optimum is 0.9405 at
(0.10, 0.45, 0.45) against 0.9283 at equal weights, a gap of 0.0122 on a cross-model spread of 0.0025,
and equal weighting is **not** among the 29 points within tolerance of the optimum.

**What follows.** Equal weights remain what the system uses. They are justified as an inherited choice
that a later, more targeted search did not confirm, never as a measured flat surface. The four values
belong to Chapter 3 §3.5.4; Chapter 2 §2.3.5 states the relation without numbers, because Chapter 2
reports no measurement.

---

## 5 · Parameter count is 3,285

**Wrong statement, now retired:** approximately 8.7k trainable parameters.

**Evidence.** `VERIFIED_NUMBERS.md` Parts 2.1 and 2.2, read from the checkpoint state dictionary. The
figure is also inconsistent with the checkpoint's own file size of 15,258 bytes. Figure 2.4 prints
3,285.

---

## 6 · Processing time is 9.76 s per hour, and the variance belongs to one stage

> **Superseded (2026-10-08):** the end-to-end figure of record became 10.83 s/h (earlier demo, median of 5 runs); neither applies to the final system (section 14).

**Wrong statements, now retired:** 16.9 ms per analysis window; approximately 15 s per hour of EEG; and
a fivefold run-to-run variation on the end-to-end figure.

**Evidence.** `REPO_MAP.md` §3b, dated 2026-09-10, records that 16.9 ms was a component benchmark
covering adjacency construction and band powers only, never the full pipeline.
`web_demo/BUILD_PROGRESS.md` §4 records the end-to-end figure as **9.76 s per hour of EEG** on
`chb06_01.edf`, CPU only, after `filter_window()` was changed to filter the whole recording once rather
than per window. The same record notes run-to-run variation of roughly fivefold, **22 to 110 s on the
adjacency and band-power stage**, on identical code and the same file, attributed to background load.

**What follows.** The end-to-end figure was measured once. Report it as indicative, state the
variation, and do not attach the fivefold range to the end-to-end number as though it had been measured
there. The per-window figure appears nowhere in the report.

---

## 7 · Demo normalisation scope is per subject

**Unresolved state, now decided:** the code fits z-score statistics and the Ledoit-Wolf covariance per
file, carrying two open `# TODO(step3)` markers, while `SZSCAN_SPEC_v5` intends per subject.

**Decision (Boti, 2026-09-12): per subject.** The thesis normalises per subject at step 6 of the
preprocessing table, so a per-subject fit is the faithful mirror of the offline pipeline; a per-file fit
gives each file its own baseline and loses comparability between the files of one patient. Chapter 2
§2.6.3 is written per subject. The per-file code is build debt to close in Step 3, not the design.

---

## 8 · The three sets are training, validation and test

**Retired term:** *held-out*. The report uses **test** everywhere, matching the split file's own key
names. Applied across `CAPTIONS.md` revision 5 and all five files in `tables/`. Nothing about the split
itself changes: it is still scored once, and no recording from it reaches training or tuning.

---

## 9 · Table 2.8 uses the four criteria the outline requires

**Superseded:** the six-criterion deployment matrix.

**Evidence.** `THESIS_OUTLINE_FINAL.md` §2.6.1 requires cloud, on-premise and bedside scored against
weighted **economic, societal, environmental and scalability** criteria. `tables/tables_ch2.md` has been
replaced with that form, matching Chapter 2 §2.6.1.

---

## 10 · Outstanding artefacts

The queue that held them, `docs/FIX_QUEUE.md`, was worked through on 2026-09-12 and 2026-09-16 and
then deleted, as it was written to be. What it closed is recorded in `docs/EXHIBIT_SET_FINAL.md`
revision 3 under "Closed since revision 2", and what remains open is in the section after it.

---

## 11 · Method of record

Four of the ten entries above were caused by the same thing: a statement inferred from a filename, a
docstring, a planning document or an empty grep, rather than read from the code that runs. The command
that settles a question is almost always one line. Prefer the command.

---

## 12 · The channel annotation is final, human and blind; the draft-label results are retired (2026-09-18)

**Wrong statements, now retired:** "attribution against labels is provisional"; "the labels are
dominant-channel, 1–2 per seizure"; "the D7 control is uninformative because within-subject Jaccard is
0.8879"; "chb06 and chb13 contribute no labelled seizure"; every number scored against the draft
(0.6497, 0.3095, 0.7758, 0.8879, −0.1261, 0.2672, +0.3578, p = 0.984).

**Evidence.** The final annotation (`results/attribution_v7/labels/source/Channel_label_approved.md`)
was made by the author from the raw 18-channel EEG, blind to every model output, listing every channel
with clear ictal discharge, and was approved by the supervisor. Parsed from that file on 2026-09-18:
76 seizures, 62 focal (|S| 1–10, mean 4.55) and 14 generalized (all 18 channels), within-subject
pairwise Jaccard 0.5144. The draft it replaces was machine-generated (`VERIFIED_NUMBERS.md` Part 7.1).

**What follows.**
- Method re-locked as `ATTRIBUTION_SPEC.md` v4, Amendment A4, before any label-scored number.
- The 14 generalized seizures are excluded from channel metrics by construction: AUROC is undefined
  when every channel is positive.
- A fixed anatomical prior already reaches macro-AUROC 0.7387 on these labels, so beating chance is no
  longer enough; the claim ladder is L1 chance → L2 prior → L3 within-patient specificity.
- **Do not describe the final annotation as provisional, draft, or machine-generated**, and do not
  reuse the D7 "uninformative" exemption: its precondition (Jaccard ≥ 0.6) no longer holds.
- Report text written before 2026-09-18 (Chapters 1–5, front matter, `tables/CAPTIONS.md`,
  `tables/tables_ch3.md`, `RUBRIC_TRACKING.md`) still carries the retired framing until step 5 of the
  rerun rewrites it. Where those files disagree with this entry, this entry wins.

<!-- perf-p1-close 2026-10-06 -->
## 13 · Performance phase, stage P1 (2026-10-06)

Settled by code reading and runs during the performance phase; full log in `PERF_PHASE_RECORD.md`.

- **The offline timeline is not a continuous-recording estimate.** `szcore_eval.build_timeline_masked`
  rebuilds it from the annotations and fills gaps with bootstrapped scores of artifact-rejected interictal
  windows (`src/szcore_eval.py:98–109`). On the real continuous timeline V1 + PELT scores 23/76 at
  73.3 FA/day (`results/continuous_eval/`). Replaces: "F1 0.213 @ 27.4 is the honest headline".
- **The ±5 SD flag means high amplitude, not artifact.** One sample on one channel above 5 SD flags the
  window; it flags 46 % of training interictal windows and ~90 % of seizure windows
  (`results/raw_eeg_view/`). Using it as an artifact label (E4) calls 81.5 % of seizure windows artifact.
- **V1's node features erase amplitude and window spectral shape**: band powers are z-scored within each
  window (`feature_extraction.compute_band_powers`) and min-maxed per band across channels within each
  window (`train_gae_joint.make_window_data`).
- **PELT on the anomaly score alarms on falling change points as well as rising ones**
  (`results/diag_detector_ceiling/`).
- **Precision and F1 come from the scorer's counts.** timescoring: precision = tp/(tp+fp),
  F1 = 2tp/(2tp+fp+(ref−tp)) (read from `timescoring/scoring.py`). The E9 hand formula gave negative
  precision; its precision/F1 columns are invalid.
- **SzCORE's official aggregate is the mean of per-subject metrics** (`szcore-evaluation`,
  `evaluate_dataset(avg_per_subject=True)` by default, `nanmean` over subjects; counts summed within a
  subject; each recording scored separately). The P1 scripts pool counts; both are reported from P2 on.
- **The selection set over-predicts test.** v2: 0.489 @ 19.8 on the 15 non-test subjects (E8), 3/76 @ 24.1
  on test (E9); test seizure peaks are out-ranked by 20–50 % of same-length non-ictal spans vs 4 % on
  validation (`results/oracle_gate_bound/`).
- **The test collapse is not mainly a detection-stage problem** (corrects HANDOVER_PERF §3): a
  local-contrast kernel-CPD detector (E10) and removing long events (D1c) do not raise sensitivity, while
  removing flagged windows (oracle) does.
- **Benchmark rows are read from `esl-epfl/szcore/results/*/chbmit.json`.** A Perplexity row
  "ESL_RF 34.1 % / 1.08 FP/day" is not in that repository and is not cited.

## Stage P2 findings (2026-10-07; details in PERF_PHASE_RECORD rev. P–Q)

| correct | what it replaces |
|---|---|
| E14 was **not adopted**: its pre-registered mechanism check failed; the "ADOPTED" line was a coding error (`results/e14_spatial_recruitment/ERRATUM.md`) | "S9 adopted at E14" |
| two validation quantities: `val` (cell re-selected on the 3 validation subjects; every gate G4) and `val_at_cell` (descriptive) — same Eb: 0.800 vs 0.933 | comparing the two as one number |
| the D1 threshold is the quantile over every non-NaN smoothed value (`event_grid`), not over non-signal-loss positions only | the first `p2_scalars` rebuild (stopped E19 by 1 FP) |
| file-level drift is a shift of the latent readout per file (top files carry no more flagged windows and rarely seizures); location-only correction helps, scale correction and short baselines hurt | "drift = more high-amplitude activity" |
| E15 patient fine-tuning is negative in **one** configuration (lr 1e-4, 2,000 steps, all parameters) | "fine-tuning does not work" |
| E19's +0.011 is about one seizure; it caught no extra short seizure | "the short branch works" |
| on E17b, CPD halves the **onset** error; on offset the contiguous-run control (12 s) and multivariate CPD (8 s) beat 1-D CPD (16 s) | "CPD improves both boundaries" |
| non-test: 93 annotated seizures, scorer 94 (chb11 split +2, a chb12 merge −1); the E18 table's 95 pieces lacked the merge | "one-piece mismatch unexplained" |
| "short" (< 20 s) is 23 test seizures by annotation, 18 by whole-window runs (`short_refs`) | mixing the two counts |
| a seizure is caught by one supra-threshold window, so ictal minutes above the top-p budget do not cap sensitivity by themselves (chb08 2.60, caught 5/5 by E) | "chb15 fails because its ictal time exceeds the budget" |
| cache-only steps took 44–317 s on 4 seeds | estimates of 10–70 min (3–10× too high) |

<!-- report-phase-2026-10-08 -->
## 14 · Report phase (2026-10-08; details in PERF_PHASE_RECORD rev. R, section 10)

| correct | what it replaces |
|---|---|
| look #6 subject-mean: seed 42 **0.508**, 4 seeds 0.498 ± 0.010 (`e22_test_oneshot/SUMMARY.md`) | "0.342 (seed 42), subject-mean 0.498" in the record, the instructions, HANDOFF rev 1 and the 08/10 briefing |
| the ledger `verdict` column is each step's gate outcome; E20a, E18 `_ovl` and P3-L6 say ADOPTED but were not chosen | reading the ledger as the final selection |
| the L2 floor 0.0025 cut chb21 (1.75 → 0.50) and chb20 (3.0 → 2.5) on non-test; L2f never lowers a budget below 0.005; the cap 0.02 binds only chb15, on test | "the per-patient budget helps generally" |
| chb24's summary lists only its seizure files; X1 scored every present file (21.3 h). Siena labels come from the SzCORE converter (`epilepsy2bids` d3fb175), which fixes the published typos; a first parser missed 6 seizures and read PN00-3 as 3,660 s | "chb24 = 12 files"; "Siena 40 seizures" |
| CHB-MIT z-score statistics (`stats.json`) exclude annotated seizure and buffer windows, test included; X1 and the demo use label-free statistics | "no label anywhere in the pipeline" |
| both GAE readouts fail the anatomical-prior test of channel attribution (A4 reconstruction 0.5694 / −0.1694; A5 latent 0.5473 / −0.1914) | "the negative is specific to the reconstruction readout" |
| processing time: 9.76 s/h (entry 6) was superseded by 10.83 s/h (earlier demo); the final system's time is measured on the rebuilt demo | quoting 9.76 or 10.83 s/h for the final system |

## 15 · Reference verification (2026-10-08; details in `Thesis_Reference_Sheet.md` groups K–M, flags 6–10)

- **Benchmark training data.** `datasets` in `esl-epfl/szcore` algorithm cards means training data. SeizureTransformer
  (0.685 @ 0.99 on Siena) declares Siena as training data — not "trained on other corpora" (record 9.9 and the
  08/10 briefing were wrong). Five more Siena entries are in-sample. DynaSD declares CHB-MIT (hyperparameters tuned
  on a subset), so its CHB-MIT row is not out-of-sample; its Siena row is.
- **DynaSD's paper** (Ojemann et al., medRxiv 2026, method NDD) reports no CHB-MIT, Siena or SzCORE number; its
  threshold is tuned on labelled intracranial data. Benchmark numbers are cited to the repository.
- **The "RF / Transformer / XGBoost CHB-MIT" rows** are Table 2 of the SzCORE arXiv preprint (v1–v3), not the
  Epilepsia paper; the Transformer 76.5 % / 40.6 FP/day is TUH.
- **Ingolfsson et al. 2024:** 22.9 → 1.0 FP/h is TUAR artifact data through the CHB-MIT-trained detector, not a
  CHB-MIT false-alarm reduction.
- **Ali et al. 2024** is supervised, leave-one-subject-out, Random Forest, ≥ 70 % coverage, events ≤ 10 s dropped,
  4.79 false detections/h (LOO).
- **Search-lead errors:** Karpov et al. is 2022; the ICASSP 2024 paper is Hassan et al.; the 2026 Frontiers paper
  excluded three cases (chb06, chb12, chb16); the ScoreNet Neural Networks DOI is an unrelated paper; IRBM 2019
  abstract gives 6.3 s / −1.17 s, not 3.9 s / 49.26 s; the CEP 2026 paper's title differs and it is supervised.
- **Siena hours:** PhysioNet states about 128 h; our X1 summary sums to about 140 h (open item).
