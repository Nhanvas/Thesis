# Qualitative Tables

The eight tables that could not be filled from the verification record, because their content is
judgement, external documentation, or work not yet done rather than a measured number.

Same rules as the rest of the pack: three decimals for discrimination, sensitivity, precision and
F1; one decimal for false alarms per day; no internal shorthand in any cell; a cell whose value has
not been read from a file is written `— not measured` and never left blank and never estimated.

**Status.** Four are complete below. Two are structures with the cells only Boti or the supervisor
can fill. Two genuinely wait on work that has not happened.

| Complete | Structure only | Waiting |
|---|---|---|
| 1.2 · 2.8 · 2.10 · 4.2 | 2.1 · 2.11 | 3.11 · 3.12 |

---

## Table 1.2 — Design requirements and targets

These are design properties, not accuracy thresholds. The held-out data are scored once, so a
numerical accuracy target set in advance could not have been checked without spending that one
evaluation, and setting one afterwards would be writing the target around the result.

| # | Requirement | Target |
|---|---|---|
| 1 | No seizure annotation during model fitting | Every parameter of the model is estimated from background activity only |
| 2 | No annotation at the decision stage | The operating rule is derived from each patient's own score distribution, not from labels |
| 3 | One model for every patient | A single set of weights is applied unchanged to patients whose recordings were never seen |
| 4 | The operating point is fixed before the held-out data are scored | The threshold is chosen on the validation patients and not revisited |
| 5 | The detection stage does not depend on a fixed score cut | Detection responds to a change in the score, in either direction, rather than to crossing a level |
| 6 | A channel-level explanation from the same model | The per-channel quantity is read from the model already trained, with no second model and no additional labels |
| 7 | Inference on ordinary hospital computing | A general-purpose processor, no dedicated accelerator at deployment |
| 8 | Faster than reviewing the recording | Processing time for one hour of recording is a small fraction of one hour |
| 9 | Recordings stay inside the institution | No component requires sending a recording to an external service |
| 10 | Every reported number is traceable | Each figure and table cites the committed file its values were read from |

A paragraph walking these row by row belongs after the table. Requirements 1, 2 and 4 together are
what the word "unsupervised" means in this thesis, and the paragraph should say so explicitly rather
than leaving a reader to assemble it.

*Source: the four goals in the outline's objectives section, and the scope statement following it.*

---

## Table 2.8 — Decision matrix for the detection stage

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
score-scale property stated with Table 2.12.*

---

## Table 2.10 — Decision matrix for deployment strategy

Weighted matrix. Scores are 1 to 5, higher is better. **The weights are an engineering judgement and
Boti sets them** — the values below are a proposal, not a result, and the accompanying paragraph must
say that the weighting is a judgement rather than a measurement.

| Criterion | Weight | Cloud service | On-premise server | Bedside device |
|---|---|---|---|---|
| Patient data remains within the institution | 0.30 | 1 | 5 | 5 |
| No specialised hardware required | 0.20 | 4 | 5 | 2 |
| One installation serves every patient | 0.20 | 5 | 5 | 1 |
| Cost to a hospital in a low-resource setting | 0.15 | 2 | 4 | 2 |
| Energy and hardware footprint | 0.10 | 3 | 4 | 4 |
| Maintenance burden on the institution | 0.05 | 5 | 3 | 2 |
| **Weighted total** | **1.00** | **2.85** | **4.65** | **3.15** |
| **Adopted** | | | **✔** | |

Three numbered reasons for the verdict. Inference runs on a general-purpose processor, so no
specialised hardware is required and an ordinary server suffices. The recordings are paediatric and
should not leave the hospital network, which rules out the cloud option regardless of its other
merits. And because no per-patient training is needed, one installation serves every patient, which a
bedside device cannot match.

The paragraph closes by stating that this is an engineering judgement built from measured properties
of the system, not a costed procurement analysis, and that the weights would differ at another
institution.

**Check the arithmetic before use.** The totals above follow from the weights and scores as given; if
Boti changes any weight or score, recompute rather than adjusting the total.

*Source: the outline's deployment section; the measured processing cost in Table 4.2; the
single-model property in Table 1.2 row 3.*

---

## Table 4.2 — Computational and deployment cost profile

Two columns only. There is no speculative column for other systems: the comparison is made in prose
where a published figure exists, and inventing one where it does not is worse than leaving it out.

| Property | This system |
|---|---|
| Trainable parameters | 3,285 |
| Stored model size | 15,258 bytes |
| Processing time per analysis window | 16.9 ms on the development processor |
| Processing time per hour of recording | approximately 15 s on the same processor |
| Accelerator required at inference | None |
| Accelerator required for training | One consumer graphics processor, once, for the shared model |
| Per-patient training | None — the same weights serve every patient |
| Per-patient calibration | Background statistics estimated from the patient's own recording, no annotation |
| Peak memory at inference | — not measured |
| Energy per hour of recording | — not measured |

The two unmeasured rows stay in the table with that wording. A cost profile that quietly omits the
quantities nobody measured reads as complete when it is not.

**Two figures to confirm before this table is final.** The per-window and per-hour times are recorded
in the application specification and were measured on one processor; state which processor in the
caption. The parameter count and model size come from the checkpoint itself and are already verified.

*Source: `docs/VERIFIED_NUMBERS.md` Parts 2.1 and 2.2 for the model; the application specification
for the timing.*

---

## Table 2.1 — Candidate public scalp EEG seizure corpora — STRUCTURE ONLY

Columns, per the exhibit list: corpus · subjects · hours · seizures · channels · sampling rate ·
annotation type · availability.

Only the adopted row can be filled from this project's own record. **Every other row needs that
corpus's own documentation opened and cited**, and no cell may be filled from recollection — that
failure has already happened once in this project, on a citation I supplied from memory and Boti
correctly rejected.

| Corpus | Subjects | Hours | Seizures | Channels | Rate | Annotation | Availability |
|---|---|---|---|---|---|---|---|
| CHB-MIT | 23 | 961.6 | 182 | 18 bipolar derivations | 256 Hz | Seizure onset and offset per recording; no channel-level annotation | Open, PhysioNet |
| TUH Seizure Corpus | | | | | | | |
| Siena Scalp EEG | | | | | | | |
| Helsinki neonatal | | | | | | | |

Suggested rows are those four; add or drop as Chapter 2 requires. For each added row, open the
corpus's description paper or dataset page, fill the cells from it, and add the citation to the
reference sheet with a **VERIFIED FROM SOURCE** marker, exactly as was done for the four dataset
citations.

The verdict paragraph after the table gives the reason for the choice: seizure onset and offset are
annotated, the corpus is open and widely used so results are comparable, the montage is consistent
across patients, and the recordings are continuous and long enough for a false-alarm rate per day to
be meaningful. The absence of channel-level annotation is stated here as a known limitation, because
it is the reason the channel attribution work is scored against a draft annotation rather than a
clinical one.

*Source: the CHB-MIT row from `docs/VERIFIED_NUMBERS.md` Part 3. Remaining rows: not yet sourced.*

---

## Table 2.11 — Application processing stages — STRUCTURE ONLY

Columns: stage · input · output.

The content comes from the application specification, which is not attached to this project. The
stages below follow from the locked pipeline and the application's data boundary, and should be
checked against that specification before use rather than accepted from here.

| Stage | Input | Output |
|---|---|---|
| Ingest | Uploaded recording file | Channel-ordered signal at the analysis sampling rate |
| Preprocess | Signal | Fixed-length windows, filtered and normalised, **every window retained** |
| Graph construction | Windows | One weighted graph per window |
| Encode | Graphs and node features | Latent node representations |
| Score | Latent representations and reconstructions | Three per-window anomaly values |
| Standardise and fuse | Three values per window | One fused score per window |
| Segment | Fused score series | Detected intervals with start and end times |
| Attribute | Per-node reconstruction error | Per-channel values for the displayed interval |
| Present | Intervals and per-channel values | Reviewer interface |

**The row that matters most is the second.** The application retains every window, where the study
drops artifact windows. That is what gives the application a real time axis, and it is a deliberate
divergence from the study pipeline that must be reported to the supervisor rather than smoothed over.
The consequence — that the application's numbers will differ from the thesis's numbers, and must not
be made to match — belongs in the paragraph after this table.

*Source: the locked pipeline; the application's data boundary. Stage boundaries not yet confirmed
against the application specification.*

---

## Table 3.11 — Processing time per stage — WAITING

Waits on the application build. Nothing here can be filled by estimation; a timing table with
invented rows is worse than an absent one.

When the application runs, measure each stage of Table 2.11 on one recording of known length and
report time per hour of recording, on a named processor.

---

## Table 3.12 — Objectives and requirements achieved — WAITING

Written last, from the finished Chapters 2 and 3. Its structure is fixed by the exhibit list: the four
goals as the first rows, then each of the ten design requirements from Table 1.2, each with the
outcome achieved.

Two rows will have to record partial outcomes, and they should be written plainly rather than softened.
Goal 3, the channel-level explanation, is validated on synthetic injections but only provisionally
compared against a draft annotation that has not been clinically reviewed. Goal 4, the application,
is complete only if the build finishes before the deadline; if it does not, the row records that it
was designed and specified but not delivered, and the timeline figure drops its corresponding task.

A table of objectives where every row reads "achieved" invites the question of what the objectives
were for.
