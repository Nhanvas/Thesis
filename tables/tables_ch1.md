# Tables — Chapter 1

Three tables. Same rules as the rest of the pack: three decimals for sensitivity, precision, F1 and
discrimination; one decimal for false alarms per day; no internal shorthand in any cell; a cell whose
value has not been read from a source is written `— not reported` and never left blank and never
estimated.

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

Every row of this table reappears in Table 3.12 with the outcome achieved, so the wording must not
drift between the two.

*Source: the four goals in the outline's objectives section, and the scope statement following it.*

---

## Table 1.3 — Project timeline

Twelve weeks. **Fig 1.4 is this table drawn as bars** — same nine rows, same names, same order, same
filled weeks. A reader comparing the two must find them identical.

| # | Task | Weeks |
|---|---|---|
| 1 | Literature review and problem definition | 1–3 |
| 2 | Data preparation and preprocessing | 2–4 |
| 3 | Graph construction and model development | 4–6 |
| 4 | Validation experiments and design selection | 6–8 |
| 5 | Held-out evaluation | 8–9 |
| 6 | Channel attribution study | 9–10 |
| 7 | Web application prototype | 10–11 |
| 8 | Report writing | 9–12 |
| 9 | Thesis defense | 12 |

**One decision still open.** Row 7 commits the report to a working application. If the application is
not running by the report deadline, remove row 7 from **both** this table and Fig 1.4 and move the
application to future work. A timeline listing work that was not done is the first thing a committee
asks about.
