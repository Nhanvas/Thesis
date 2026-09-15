# Tables Pack — Chapter 2

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

This file holds Tables 2.1 through 2.8. Every table in this file is complete. See
`tables/README.md` for what lives in the other chapter files.

---

## Table 2.1 — Candidate public scalp EEG seizure corpora

Columns, per the exhibit list: corpus · subjects · hours · seizures · channels · sampling rate ·
annotation type · availability. The Helsinki neonatal corpus was dropped: neonatal data, a different
montage, a different task.

| Corpus | Subjects | Hours | Seizures | Channels | Rate | Annotation | Availability |
|---|---|---|---|---|---|---|---|
| CHB-MIT [39], [43] | 23 | 961.6 | 182 | 18 bipolar derivations analysed, up to 28 recorded in individual files | 256 Hz | Seizure onset and offset per recording; no channel-level annotation | Open, PhysioNet |
| Siena [40], [41] | 14 | 128.4 | 47 | 29 for thirteen subjects, 21 for one | 512 Hz | Seizure onset and offset, with the electrode list, per subject; seizures classified to ILAE criteria | Open, PhysioNet |
| TUH Seizure Corpus [42] | 315 | Over 504, of which about 36 are seizure | Not reported as a count; 280 of 822 sessions contain seizures | Variable per recording; 19 EEG channels and two supplementary channels used during annotation | Not stated in the corpus report | Seizure onset, offset and type, in both term-based and channel-based files | Open; no data-sharing or ethics agreement required |

Three cells are not simple copies. **Siena's hours and seizure count are sums over that paper's own
Table 1**, which reports registration time in minutes and seizures per patient: 7,704 minutes and 47
seizures across fourteen patients. The paper prints neither total. **TUSZ does not print a seizure
count**; it reports seizure types as a histogram and gives 280 seizure-containing sessions of 822.
**TUSZ does not state a sampling rate** in its corpus report.

The verdict paragraph after the table gives the reason for the choice: seizure onset and offset are
annotated, the corpus is open and widely used so results are comparable, the montage is consistent
across patients, and the recordings are continuous and long enough for a false-alarm rate per day to
be meaningful.

One column records a cost of that choice rather than a benefit. **TUSZ annotates seizures on a
per-channel basis as well as a per-recording one; CHB-MIT does not, and neither does Siena.** That
absence is the direct reason the channel attribution of §2.5 is validated against synthetic
injections and scored against a draft annotation rather than a clinical reference, and it is the same
fact Chapter 1 §1.2.6 uses to state the explanation gap.

*Source: the CHB-MIT row from `docs/VERIFIED_NUMBERS.md` Part 3. The Siena row from [41] §2.1 and
Table 1, **VERIFIED FROM SOURCE**. The TUH row from [42], Results and Discussion, **VERIFIED FROM
SOURCE**.*

## Table 2.2 — Patient assignment to the three sets

| Set | Patients | Count | Recordings | Recorded hours | Seizures |
|---|---|---|---|---|---|
| Training | chb01, chb02, chb04, chb05, chb07, chb08, chb09, chb12, chb19, chb20, chb21, chb23 | 12 | 342 | 566.43 | 93 |
| Validation | chb10, chb11, chb22 | 3 | 91 | 115.82 | 13 |
| Test | chb03, chb06, chb13, chb14, chb15, chb16, chb17, chb18 | 8 | 231 | 279.39 | 76 |

Assignment is by patient, so no recording from a test patient contributes to training or to
any tuning decision. The test set was scored once.

**Writer's trap.** The split file's first key holds fifteen patients because it includes the three
validation patients. The training set is **twelve**. A chapter reporting fifteen has read the
wrong key.

*Source: `data/splits/split_main.json` (`inner_train` / `val` / `test`) and
`docs/VERIFIED_NUMBERS.md` Parts 2.3 and 3.*

## Table 2.3 — Preprocessing steps

| # | Step | Parameters | Rationale |
|---|---|---|---|
| 1 | Band-pass filter | Fourth-order Butterworth, 0.5–60 Hz, zero-phase, 3 s padding each side | Removes drift below the physiological range and content above the analysis band without phase distortion |
| 2 | Notch filter | IIR notch at 60 Hz, quality factor 30, zero-phase | Suppresses mains interference, which falls inside the retained band |
| 3 | Segmentation | 4 s non-overlapping windows, 1024 samples at 256 Hz | Fixes the analysis unit; non-overlapping windows keep successive windows statistically independent |
| 4 | Post-seizure exclusion | 4 h after each annotated seizure end excluded from the background set, before any background statistic is computed | Prevents post-ictal activity from being treated as normal background, and from entering the statistics that set step 5 |
| 5 | Artifact rejection | Window discarded if any channel exceeds 5 standard deviations of that channel's background distribution, estimated from the windows surviving step 4 | Removes gross movement and electrode artifacts from the background set |
| 6 | Normalisation | Per-patient, per-channel z-score | Removes between-patient amplitude differences so one model serves every patient |

Two properties of this stage matter later. Artifact rejection is applied to the background set
only; seizure windows are deliberately kept, because rejecting them would remove exactly the
activity the system must detect. And because rejection drops windows, the retained background
windows no longer sit at their original positions in recording time.

**Writer's trap, one.** Step 4 governs which windows enter the background set. It is **not** applied
to the false-alarm denominator, which is total recorded time minus seizure time. A sentence saying a
post-seizure buffer was excluded from the false-alarm rate would be wrong.

**Writer's trap, two.** The file's opening docstring numbers artifact rejection as *Step 4*. The
executed order is the reverse: `compute_subject_stats` builds the post-seizure buffer mask and skips
every ictal or buffered window before accumulating the per-channel mean and standard deviation, and
the artifact threshold is five times that standard deviation. Numbering this table from the docstring
puts the two steps the wrong way round, which is what an earlier revision did.

*Source: `src/dataprep/preprocessing.py`, verified 2026-09-12 against `compute_subject_stats` and
`count_windows`. Denominator reconciliation in `docs/VERIFIED_NUMBERS.md` Part 3.*

## Table 2.4 — Decision matrix for edge sparsification

| Criterion | Fixed correlation threshold | Retain the strongest 20 % of edges |
|---|---|---|
| Density across patients | 0.921 to 0.973, varies by patient | 0.196, identical for every patient |
| Density across states | 0.921–0.973 interictal, 0.949–0.974 ictal | 0.196 in both states |
| Effect on message passing | Graph is almost complete; neighbourhood averaging approaches a global mean and topology carries little information | Sparse neighbourhoods preserve topological structure |
| Comparability between patients | Absent — the same threshold yields a different graph density for each patient | Present by construction |
| Separation between ictal and interictal connectivity, scale-comparable measures | Reference | Higher on 8 of 8 test patients under both relative Frobenius distance and cosine distance |
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

## Table 2.5 — Model and training configuration

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

## Table 2.6 — Decision matrix for the detection stage

| Criterion | Threshold on the fused score | Change point detection |
|---|---|---|
| Requires a score level to be chosen | Yes — and the level has no patient-independent value | No |
| Direction of response | Detects upward departures only | Detects a change in either direction |
| Behaviour when a patient's score falls during a seizure | Fails to detect | Detects the change |
| Calibration data required | Seizure-free data, to set the level | None beyond the score series itself |
| Effect of setting the level for an acceptable false-alarm rate | Sensitivity falls toward zero | Not applicable |
| Question the stage answers | Is the score high now? | When did the state change? |
| Transfers between patients without adjustment | No — score scales are unbounded and differ per patient | Yes |
| **Adopted** | | **✔** |

The verdict paragraph should give three numbered reasons and no more. First, a threshold calibrated
on seizure-free data detects only upward shifts, and so fails any patient whose score falls during a
seizure. Second, a threshold set to an acceptable false-alarm rate drives sensitivity toward zero,
because the per-patient score scales are unbounded and a level tolerable for one patient is far too
high for another. Third, change point detection is threshold-free and direction-agnostic, and it
answers the question the task actually poses, which is when the state changed rather than whether the
score is currently large.

A registered comparison against a window-level threshold as an alternative decision rule was carried
out and is reported as a considered and rejected alternative.

*Source: the locked decision record; the registered window-threshold comparison; the per-patient
score-scale property stated in §2.7.2.*

## Table 2.7 — Synthetic validation grid

| Dimension | Values |
|---|---|
| Injection strength (multiplier on the affected channels) | 1.00, 1.25, 1.50, 2.00, 3.00 |
| Number of injected channels | 1, 2, 4, 8, 12 |
| Replicates per cell | 200 |
| Cells per panel | 25 |
| Panels | Validation and test, 50 cells in total |
| Pseudo-seizure construction | A contiguous interictal block whose length is drawn from the distribution of the 76 real seizure durations |
| Baseline | Robust standardisation computed on interictal data excluding the injected block |
| Aggregation | 95th percentile over the windows of the block |
| Random seed | 42 |

The injected channels are known exactly, so this grid has ground truth that the corpus itself does
not provide. It tests the scoring machinery, not the clinical claim.

*Source: `docs/ATTRIBUTION_SPEC.md` §9.1; `results/attribution_v6/synthetic_sanity.csv`.*

## Table 2.8 — Decision matrix for deployment strategy

Weighted matrix. Scores are 1 to 5, higher is better. The criteria are the four the outline requires at
§2.6.1: economic, societal, environmental, and global reach and scalability. **The weights are an
engineering judgement and Boti sets them.** The accompanying paragraph must say that the weighting is a
judgement rather than a measurement.

| Criterion | Weight | Cloud service | On-premise server | Bedside device |
|---|---|---|---|---|
| Economic | 0.30 | 2 | 4 | 3 |
| Societal | 0.30 | 1 | 5 | 4 |
| Environmental | 0.20 | 2 | 4 | 3 |
| Global reach and scalability | 0.20 | 4 | 3 | 2 |
| **Weighted total** | **1.00** | **2.1** | **4.1** | **3.1** |
| **Adopted** | | | **✔** | |

Four numbered reasons for the verdict, one per criterion. Economically, an on-premise server is a
one-time infrastructure cost with no recurring usage fee, which suits an inference design that needs no
specialised hardware, whereas a cloud service adds a recurring cost for storing and transferring
multi-hour recordings. Societally, the recordings are paediatric, and this is the only option under
which a raw recording never leaves the site that collected it. Environmentally, inference confined to a
general-purpose processor avoids the continuous power draw a shared cloud accelerator or per-bed
hardware would add. On global reach, the method is patient-independent, so one installation serves
every patient a hospital admits; this option scores below the cloud alternative on that one criterion,
because each hospital still needs its own installation.

The paragraph closes by stating that this is an engineering judgement built from measured properties of
the system, not a costed procurement analysis, and that the weights would differ at another
institution.

**Check the arithmetic before use.** The totals above follow from the weights and scores as given; if
Boti changes any weight or score, recompute rather than adjusting the total.

*Source: the criteria set required by `docs/THESIS_OUTLINE_FINAL.md` §2.6.1; the measured processing
cost in Table 4.2; the single-model property in Table 1.2 row 3. Supersedes the six-criterion version
carried by earlier revisions of this file, which did not match the outline.*
