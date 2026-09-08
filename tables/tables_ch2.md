# Tables Pack — Chapter 2

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

This file holds Tables 2.2 through 2.12. See `tables/README.md` for what lives in the other three
chapter files and for which tables are still unfilled.

---

## Table 2.2 — Characteristics of the selected corpus

| Property | Value |
|---|---|
| Subjects | 23 |
| Recordings | 664 |
| Total recorded time | 961.6 h |
| Annotated seizures | 182 |
| Channels analysed | 18 bipolar derivations |
| Sampling rate | 256 Hz |
| Annotation content | Seizure start and end time per recording; no channel-level annotation |
| Seizure duration, held-out subset | 6 s minimum, 45 s median, 51.9 s mean, 205 s maximum |

Every corpus figure comes from this project's own parse of the 23 recording summary files, never
from a corpus description quoted out of a cited paper. Published descriptions of this corpus give
23 subjects in some places and 24 in others.

*Source: `docs/VERIFIED_NUMBERS.md` Part 3. Recording count is the sum of the per-set file counts
(342 + 91 + 231).*

## Table 2.3 — Patient assignment to the three sets

| Set | Patients | Count | Recordings | Recorded hours | Seizures |
|---|---|---|---|---|---|
| Training | chb01, chb02, chb04, chb05, chb07, chb08, chb09, chb12, chb19, chb20, chb21, chb23 | 12 | 342 | 566.43 | 93 |
| Validation | chb10, chb11, chb22 | 3 | 91 | 115.82 | 13 |
| Held-out | chb03, chb06, chb13, chb14, chb15, chb16, chb17, chb18 | 8 | 231 | 279.39 | 76 |

Assignment is by patient, so no recording from a held-out patient contributes to training or to
any tuning decision. The held-out set was scored once.

**Writer's trap.** The split file's first key holds fifteen patients because it includes the three
validation patients. The training set is **twelve**. A chapter reporting fifteen has read the
wrong key.

*Source: `data/splits/split_main.json` (`inner_train` / `val` / `test`) and
`docs/VERIFIED_NUMBERS.md` Parts 2.3 and 3.*

## Table 2.4 — Preprocessing steps

| # | Step | Parameters | Rationale |
|---|---|---|---|
| 1 | Band-pass filter | Fourth-order Butterworth, 0.5–60 Hz, zero-phase, 3 s padding each side | Removes drift below the physiological range and content above the analysis band without phase distortion |
| 2 | Notch filter | IIR notch at 60 Hz, quality factor 30, zero-phase | Suppresses mains interference, which falls inside the retained band |
| 3 | Segmentation | 4 s non-overlapping windows, 1024 samples at 256 Hz | Fixes the analysis unit; non-overlapping windows keep successive windows statistically independent |
| 4 | Artifact rejection | Window discarded if any channel exceeds 5 standard deviations of that channel's interictal distribution | Removes gross movement and electrode artifacts from the background set |
| 5 | Post-seizure exclusion | 4 h after each annotated seizure end excluded from the background set | Prevents post-ictal activity from being treated as normal background |
| 6 | Normalisation | Per-patient, per-channel z-score | Removes between-patient amplitude differences so one model serves every patient |

Two properties of this stage matter later. Artifact rejection is applied to the background set
only; seizure windows are deliberately kept, because rejecting them would remove exactly the
activity the system must detect. And because rejection drops windows, the retained background
windows no longer sit at their original positions in recording time.

**Writer's trap.** Step 5 governs which windows enter the background set. It is **not** applied to
the false-alarm denominator, which is total recorded time minus seizure time. A sentence saying a
post-seizure buffer was excluded from the false-alarm rate would be wrong.

*Source: `src/dataprep/preprocessing.py` lines 8, 11, 27–28, 52–65, 78–81. Denominator
reconciliation in `docs/VERIFIED_NUMBERS.md` Part 3.*

## Table 2.5 — Spectral bands used as node features

| Band | Range | Physiological basis |
|---|---|---|
| Delta | 0.5–4 Hz | Deep sleep and pathological slowing; rises in post-ictal suppression |
| Theta | 4–8 Hz | Drowsiness and focal slowing; a common interictal correlate of focal disturbance |
| Alpha | 8–13 Hz | Posterior resting rhythm; attenuates when cortex is activated |
| Beta | 13–30 Hz | Alert cortical activity and the fast component of some seizure onsets |
| Gamma | 30–60 Hz | High-frequency activity associated with local synchronisation during seizures |

Each band power is computed by Welch's method with a 2 s segment and 1 s overlap, then
log-transformed, giving five values per channel per window.

*Source: `src/dataprep/feature_extraction.py` lines 14–19, 32, 37–38.*

## Table 2.6 — Decision matrix for edge sparsification

| Criterion | Fixed correlation threshold | Retain the strongest 20 % of edges |
|---|---|---|
| Density across patients | 0.921 to 0.973, varies by patient | 0.196, identical for every patient |
| Density across states | 0.921–0.973 interictal, 0.949–0.974 ictal | 0.196 in both states |
| Effect on message passing | Graph is almost complete; neighbourhood averaging approaches a global mean and topology carries little information | Sparse neighbourhoods preserve topological structure |
| Comparability between patients | Absent — the same threshold yields a different graph density for each patient | Present by construction |
| Separation between ictal and interictal connectivity, scale-comparable measures | Reference | Higher on 8 of 8 held-out patients under both relative Frobenius distance and cosine distance |
| Free parameter | An absolute threshold that has no patient-independent value | A proportion, which transfers unchanged between patients |
| **Adopted** | | **✔** |

Two notes the verdict paragraph must carry. The raw Frobenius distance is **not** comparable
between the two rules, because the proportional rule removes about eighty percent of the entries
the norm sums over and so shrinks arithmetically whatever happens to separation; on that measure
the proportional rule appears worse on six of eight patients, and that appearance is an artefact.
And the separation measurement was made after the pipeline was fixed, so it characterises the
choice rather than having driven it.

**Do not cite** the range "+88 % to +411 %" that appears in the graph-construction module's
docstring. Its per-subject output was never committed and it has not been reproduced.

*Source: `docs/VERIFIED_NUMBERS.md` Part 4; `docs/LOCKED_DOCS_ADDENDUM.md` §1.2;
`src/dataprep/graph_construction.py` lines 70–72.*

## Table 2.7 — Model and training configuration

| Setting | Value |
|---|---|
| Encoder | Two graph convolution layers, 23 → 64 → 16 |
| Node feature vector | 18 adjacency-row entries concatenated with 5 log band powers |
| Decoder, node features | Two fully connected layers, 16 → 32 → 5 |
| Decoder, adjacency | Inner product of the latent node representations |
| Total trainable parameters | **3,285** |
| Objective | Mean squared error on the adjacency reconstruction plus 0.1 times the mean squared error on the node-feature reconstruction |
| Optimiser | Adam, learning rate 1×10⁻³ |
| Learning-rate schedule | Cosine annealing, period equal to the epoch count |
| Epochs | 200 |
| Batch size | 32 |
| Early stopping | None; the final epoch is retained |
| Training data | Interictal windows of the twelve training patients only |
| Initialisation | Seed 42 for the reported system; seeds 1, 2 and 3 retrained for the stability check |

**Writer's trap.** The figure "approximately 8.7k parameters" circulates in this project's notes,
is wrong, and is inconsistent with the checkpoint's own file size. The training script's opening
docstring also repeats two values belonging to a superseded model; neither may reach the report.

*Source: `docs/VERIFIED_NUMBERS.md` Parts 2.1 and 2.2, read from the checkpoint state dictionary
and from `src/retrain/gae_joint.py` and `src/retrain/train_gae_joint.py`.*

## Table 2.9 — Synthetic validation grid

| Dimension | Values |
|---|---|
| Injection strength (multiplier on the affected channels) | 1.00, 1.25, 1.50, 2.00, 3.00 |
| Number of injected channels | 1, 2, 4, 8, 12 |
| Replicates per cell | 200 |
| Cells per panel | 25 |
| Panels | Validation and held-out, 50 cells in total |
| Pseudo-seizure construction | A contiguous interictal block whose length is drawn from the distribution of the 76 real seizure durations |
| Baseline | Robust standardisation computed on interictal data excluding the injected block |
| Aggregation | 95th percentile over the windows of the block |
| Random seed | 42 |

The injected channels are known exactly, so this grid has ground truth that the corpus itself does
not provide. It tests the scoring machinery, not the clinical claim.

*Source: `docs/ATTRIBUTION_SPEC.md` §9.1; `results/attribution_v6/synthetic_sanity.csv`.*

## Table 2.12 — Reported metrics and their definitions

| Tier | Metric | Definition |
|---|---|---|
| Window | Discrimination (AUROC) | Area under the receiver-operating curve over all windows of one patient; reported as the unweighted mean across patients |
| Window | Precision–recall area (AUPRC) | Area under the precision–recall curve for one patient; reported as the unweighted mean across patients |
| Event | Sensitivity | Annotated seizures with at least one overlapping detected interval, divided by the number of annotated seizures |
| Event | Precision | Detected intervals overlapping an annotated seizure, divided by the number of detected intervals |
| Event | F1 | Harmonic mean of event sensitivity and event precision |
| Event | False alarms per day | Detected intervals overlapping no annotated seizure, divided by the scored recording time, expressed per 24 h |

Three conventions travel with this table. Matching is by any overlap, with a tolerance of 30 s
before an annotated onset and 60 s after an annotated offset; detections closer than 90 s are
merged. Specificity is not reported, because a true-negative event cannot be defined once the
timeline is expressed as events rather than samples; false alarms per day replaces it, and this is
a structural property of event-level scoring rather than a choice. And only the across-patient
means of the two window metrics are comparable between patients: a threshold-dependent pooled
window metric is not, because the per-patient score scales are unbounded.

F1 carries no interval because it is a function of the two quantities above it. No detection
metric in this report carries an interval.

*Source: `src/szcore_eval.py`; `src/evaluation_protocol.py`; scoring convention from the
event-scoring framework paper; `docs/LOCKED_DOCS_ADDENDUM.md` §2.1.*
