# Tables — Chapter 1

Four tables for Chapter 1. Tables 1.1 through 1.4.

## Rules applied throughout

1. Three decimals for discrimination, sensitivity, precision and F1; one decimal for false alarms per
   day. Same rule in tables and figures.
2. No confidence intervals on any detection table. Intervals appear only on Table 3.7.
3. No internal shorthand: no lever codes, no file names, no phase names, no branch nicknames in a
   table cell or heading.
4. A cell whose value has not been read from a source is written `— not reported` and never left
   blank and never estimated.
5. Patient identifiers keep the corpus form (chb03, chb06, …) so the tables agree with the figures.
6. Every table ends with a source line naming the file or paper its values were read from.

`docs/VERIFIED_NUMBERS.md` is the authority for this study's numbers. Every published figure below was
read from its source paper.

---

## Table 1.1 — Representative seizure detection approaches

This is Table 4.1 without the two rows for this study and without the comparison paragraphs that
follow it there. Chapter 1 presents the landscape; Chapter 4 adds this work to the same table and
draws the comparison. **Keep the column order and the wording of every cell identical between the
two**, so a reader turning back finds the same table with two rows added.

Rates reported per hour in the source are converted to per day, and both forms are given so a reader
can check the conversion.

| Study | Method | Corpus | Supervision | Patient split | Scoring level | Sensitivity | False alarms / day | Other reported figures |
|---|---|---|---|---|---|---|---|---|
| Ali et al., 2024 (5-fold) | Handcrafted features, sliding-window event estimation | CHB-MIT, 24 patients | Supervised | Patient-independent | Event | 0.726 | 127.7 (5.32 /h) | — |
| Ali et al., 2024 (leave-one-out) | As above | CHB-MIT, 24 patients | Supervised | Patient-independent | Event | 0.753 | 115.0 (4.79 /h) | — |
| Ingolfsson et al., 2024 | Gradient-boosted trees with an artifact stage, reduced channel count | CHB-MIT, 23 patients, 182 seizures | Supervised | Patient-specific | Segment, hourly false-alarm rate | 0.653 | 15.6 (0.65 /h) | Specificity 0.999; 16 of 23 patients with no false positives |
| Chung et al., 2024 | Convolutional detector, 18 channels | CHB-MIT, 13 patients | Supervised | Patient-specific | Event | 1.000 | 7.2 (0.30 /h) | Segment sensitivity 0.987; latency 2.1 s |
| Aboyeji et al., 2024 | Cascaded convolutional autoencoder, reconstruction error | CHB-MIT, 10 patients | Unsupervised, trained on interictal only | Patient-specific | Segment | 0.949 | 0.1 (0.0044 /h) | Specificity 0.996; precision 0.799 |
| Zhu et al., 2024 (patient-specific) | Squeeze-excitation temporal convolution with a recurrent head | CHB-MIT | Supervised | Patient-specific | Segment | 0.959 | — not reported | Accuracy 0.988; specificity 0.994; F1 0.968 |
| Zhu et al., 2024 (cross-patient) | As above | CHB-MIT | Supervised | Patient-independent | Segment | 0.933 | — not reported | Accuracy 0.938; specificity 0.927; F1 0.856 |
| Yildiz et al., 2022 | Variational autoencoder | CHB-MIT | Unsupervised | Folds partition windows, not patients | Window | 0.640 | — not reported | Precision 0.54; accuracy 0.68; discrimination 0.68 |
| Tang et al., 2022 | Diffusion-convolutional recurrent graph network | TUSZ | Self-supervised pre-training, supervised fine-tuning | Patient-independent | Window | — | — not reported | Discrimination 0.875 |
| Bomela et al., 2020 | Algebraic connectivity of a dynamic graph, no learning | Scalp EEG, private | None | — | Event | 0.936 | 3.8 (0.16 /h) | — |
| Community challenge, 2025 (winner) | Best of 28 submitted algorithms | Private, 65 patients, 4360 h, 398 seizures | Supervised | Patient-independent | Event | 0.370 | 1.34 | F1 0.430; precision 0.450 |

**Three values that must not be misused.**

Yildiz's 0.68 is its accuracy and its discrimination, not its sensitivity — the sensitivity is 0.640.

A sensitivity of 0.765 at 40.6 false alarms per day circulates in this project's notes as a CHB-MIT
result. It is not one, and the paper it is attributed to contains no CHB-MIT benchmark at all.

A commercial system reached an F1 of 0.441. That figure is quoted by the 2025 challenge report from a
separate 2021 evaluation on different data; it is **not** a result of the challenge itself, and any
sentence using it must attribute it that way.

**The point the chapter should draw from this table**, before Chapter 4 makes the comparison: the
highest sensitivities here are patient-specific, several rows report no false-alarm rate at all and
therefore cannot be placed on a sensitivity-against-false-alarms plane, and one row partitions its
folds by window rather than by patient so windows of the same patient appear in both training and
test. Where the same corpus is evaluated at event level across patients — the first two rows — the
published sensitivity is 0.726 to 0.753 at over a hundred false alarms per day, not the 0.90 to 0.99
the corpus is usually associated with.

*Source: the five source papers, read on 2026-09-07; `docs/VERIFIED_NUMBERS.md` Part 7b for the
entries verified earlier; `docs/LOCKED_DOCS_ADDENDUM.md` §1.6 to §1.8.*

---

## Table 1.2 — Design requirements and targets

These are design properties, not accuracy thresholds. The test data are scored once, so a
numerical accuracy target set in advance could not have been checked without spending that one
evaluation, and setting one afterwards would be writing the target around the result.

| # | Requirement | Target |
|---|---|---|
| 1 | No seizure annotation during model fitting | Every parameter of the model is estimated from background activity only |
| 2 | No annotation at the decision stage | The operating rule is derived from each patient's own score distribution, not from labels |
| 3 | One model for every patient | A single set of weights is applied unchanged to patients whose recordings were never seen |
| 4 | The operating point is fixed before the test data are scored | The threshold is chosen on the validation patients and not revisited |
| 5 | The detection stage does not depend on a fixed score cut | Detection responds to a change in the score, in either direction, rather than to crossing a level |
| 6 | A channel-level explanation from the same model | The per-channel quantity is read from the model already trained, with no second model and no additional labels |
| 7 | Inference on ordinary hospital computing | A general-purpose processor, no dedicated accelerator at deployment |
| 8 | Faster than reviewing the recording | Processing time for one hour of recording is a small fraction of one hour |
| 9 | Recordings stay inside the institution | No component requires sending a recording to an external service |
| 10 | Every reported number is traceable | Each figure and table cites the committed file its values were read from |

A paragraph walking these row by row belongs after the table. Requirements 1, 2 and 4 together are
what the word "unsupervised" means in this thesis, and the paragraph should say so explicitly rather
than leaving a reader to assemble it.

Every row of this table reappears in Table 3.9 with the outcome achieved, so the wording must not
drift between the two.

*Source: the four goals in the outline's objectives section, and the scope statement following it.*

---

## Table 1.3 — Thesis timeline

Twelve weeks, nine tasks. The schedule is presented as two tables rather than a chart, following the
reference thesis: this table is the calendar grid, Table 1.4 the week-by-week detail. In the report,
shade the marked cells rather than printing a symbol; the header row spans "Period (weeks)".

| No | Task | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Literature review and problem definition | ■ | ■ | ■ | | | | | | | | | |
| 2 | Data preparation and preprocessing | | ■ | ■ | ■ | | | | | | | | |
| 3 | Graph construction and model development | | | | ■ | ■ | ■ | | | | | | |
| 4 | Validation experiments and design selection | | | | | | ■ | ■ | ■ | | | | |
| 5 | Test-set evaluation | | | | | | | | ■ | ■ | | | |
| 6 | Channel attribution study | | | | | | | | | ■ | ■ | | |
| 7 | Web application prototype | | | | | | | | | | ■ | ■ | |
| 8 | Report writing | | | | | | | | | ■ | ■ | ■ | ■ |
| 9 | Thesis defense | | | | | | | | | | | | ■ |

Row 7 stays. The application is past its first build stage with a working file-level pipeline, so the
report lists it.

*Source: project schedule; the defense date is 5–6 November.*

## Table 1.4 — Specific task carried out in each week

The phases and their week spans come from Table 1.3. The allocation of a task to a week inside a phase
is a record of how the work ran, confirmed by the author.

| Phase | Week | Task |
|---|---|---|
| **Literature review and problem definition** (Weeks 1–3) | Week 1 | Define the task as post-hoc review triage of an already-recorded file, and separate it from real-time alarm and seizure prediction |
| | Week 2 | Survey supervised detection on scalp EEG; identify supervision level, patient split and scoring granularity as the three axes on which published results diverge |
| | Week 3 | Survey unsupervised anomaly detection, graph neural networks on EEG and change point detection; adopt the community event-based scoring standard and assemble the comparison table |
| **Data preparation and preprocessing** (Weeks 2–4) | Week 2 | Parse the corpus summary files; fix the eighteen bipolar derivations common to every recording and assign patients to the training, validation and test sets |
| | Week 3 | Implement filtering, windowing, per-subject normalisation, artifact rejection and the post-seizure exclusion buffer |
| | Week 4 | Compute the spectral node features and the two coupling measures; compare the two edge-sparsification rules and select the proportional rule |
| **Graph construction and model development** (Weeks 4–6) | Week 4 | Build a connectivity graph per analysis window from the selected sparsification rule |
| | Week 5 | Implement and train the graph autoencoder on seizure-free windows of the training patients only |
| | Week 6 | Add the latent-distance and gamma-band coupling readouts and fuse the three scores into one series per patient |
| **Validation experiments and design selection** (Weeks 6–8) | Week 6 | Diagnose the reconstruction-polarity inversion on a validation patient and confirm that the latent-distance readout is unaffected by it |
| | Week 7 | Implement change point detection; fix the smoothing width, the penalty rule and the merge width on the validation patients |
| | Week 8 | Pre-register and evaluate the design alternatives; fix both operating-point rules |
| **Test-set evaluation** (Weeks 8–9) | Week 8 | Freeze the model weights, the ensemble and every detection parameter; verify the trained checkpoint against the committed score arrays |
| | Week 9 | Score the eight test patients once under the event-based framework and record the result as obtained |
| **Channel attribution study** (Weeks 9–10) | Week 9 | Implement per-channel scoring; run the synthetic injection grid and the permutation null before any real annotation is used |
| | Week 10 | Produce the draft channel annotation and score the channel ranking against it, alongside the subject-constant control |
| **Web application prototype** (Weeks 10–11) | Week 10 | Establish that stored scores cannot be replayed on a time axis; specify the recompute architecture and the label-free guards |
| | Week 11 | Build and time the ingest-to-fusion stages of the processing pipeline |
| **Report writing** (Weeks 9–12) | Week 9 | Write the introduction, background and literature review |
| | Week 10 | Write the methodology; prepare the figures and tables |
| | Week 11 | Write the results and discussion |
| | Week 12 | Review and revise the report |
| **Thesis defense** (Week 12) | Week 12 | Prepare the presentation slides and rehearse the anticipated questions |

*Source: project schedule.*
