# Tables Pack — Chapter 4

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

This file holds Table 4.1, Table 1.1 and the Figure 4.1 plotting note. See `tables/README.md` for
what lives in the other three chapter files and for which tables are still unfilled.

---

## Table 4.1 — Comparison with published work, including this study

Every row was read from the source paper. Rates originally reported per hour are converted to
per day and both forms are given, because the report's own unit is per day and a reader must be
able to check the conversion.

| Study | Method | Corpus | Supervision | Patient split | Scoring level | Sensitivity | False alarms / day | Other reported figures |
|---|---|---|---|---|---|---|---|---|
| Ali et al., 2024 (5-fold) | Handcrafted features, sliding-window event estimation | CHB-MIT, 24 patients | Supervised | Patient-independent | Event | 0.726 | **127.7** (5.32 /h) | — |
| Ali et al., 2024 (leave-one-out) | As above | CHB-MIT, 24 patients | Supervised | Patient-independent | Event | 0.753 | **115.0** (4.79 /h) | — |
| Ingolfsson et al., 2024 | Gradient-boosted trees with an artifact stage, reduced channel count | CHB-MIT, 23 patients, 182 seizures | Supervised | Patient-specific | Segment, hourly false-alarm rate | 0.653 | 15.6 (0.65 /h) | Specificity 0.999; 16 of 23 patients with no false positives |
| Chung et al., 2024 | Convolutional detector, 18 channels | CHB-MIT, 13 patients | Supervised | Patient-specific | Event | 1.000 | 7.2 (0.30 /h) | Segment sensitivity 0.987; latency 2.1 s |
| Aboyeji et al., 2024 | Cascaded convolutional autoencoder, reconstruction error | CHB-MIT, 10 patients | Unsupervised, trained on interictal only | Patient-specific | Segment | 0.949 | 0.1 (0.0044 /h) | Specificity 0.996; precision 0.799 |
| Zhu et al., 2024 (patient-specific) | Squeeze-excitation temporal convolution with a recurrent head | CHB-MIT | Supervised | Patient-specific | Segment | 0.959 | — not reported | Accuracy 0.988; specificity 0.994; F1 0.968 |
| Zhu et al., 2024 (cross-patient) | As above | CHB-MIT | Supervised | Patient-independent | Segment | 0.933 | — not reported | Accuracy 0.938; specificity 0.927; F1 0.856 |
| Yildiz et al., 2022 | Variational autoencoder | CHB-MIT | Unsupervised | Folds partition windows, not patients | Window | 0.640 | — not reported | Precision 0.54; accuracy 0.68; discrimination 0.68 |
| Tang et al., 2022 | Diffusion-convolutional recurrent graph network | TUSZ | Self-supervised pre-training, supervised fine-tuning | Patient-independent | Window | — | — not reported | Discrimination 0.875 |
| Bomela et al., 2020 | Algebraic connectivity of a dynamic graph, no learning | Scalp EEG, private | None | — | Event | 0.936 | 3.8 (0.16 /h) | — |
| Community challenge, 2025 (winner) | Best of 28 submitted algorithms | Private, 65 patients, 4360 h, 398 seizures | Supervised | Patient-independent | Event | 0.370 | **1.34** | F1 0.430; precision 0.450 |
| **This study (reported point)** | **Graph autoencoder with three anomaly readouts and change-point detection** | **CHB-MIT, 8 held-out patients, 76 seizures** | **Unsupervised, patient-independent** | **Patient-independent** | **Event** | **0.618** | **27.4** | **F1 0.213; precision 0.129** |
| **This study (best point on the curve)** | As above, threshold located after scoring | As above | As above | Patient-independent | Event | 0.474 | 4.9 | F1 0.426; precision 0.387 |

### The one row that carries the comparison

Only the first two rows are matched to this work on all four axes that matter: **same corpus,
event-level scoring, patient-independent split, and a reported false-alarm rate**. Against them,
this system produces four to five times fewer false alarms at a sensitivity about eleven points
lower, and does so without using any seizure label during training. That comparison needs no
caveat about differing datasets, which is what makes it the one worth making.

Four properties of that comparator still travel with the sentence: it is supervised, it uses
twenty-four patients rather than twenty-three, it segments at five seconds rather than four, and
its event-matching rule is its own rather than the scoring framework adopted here.

### The band, and where this work sits in it

The 2025 challenge is the realistic patient-independent ceiling: its top five submissions span
sensitivity 0.37 to 0.58 at precision 0.27 to 0.45, producing between 1.34 and 14 false alarms per
day. Those results are on a private corpus of a different recording protocol, so the comparison is
of magnitude, not of rank. The reported point here sits below that band on false alarms; the best
point on the curve reaches an F1 of 0.426, matching the winning submission's F1, but at nearly
four times its false-alarm rate and at a threshold located after the held-out set was scored.

**A commercial system reached an F1 of 0.441.** That figure is quoted by the challenge report from
a separate 2021 evaluation on different data; it is **not** a result of the challenge itself. Any
sentence using it must attribute it that way.

### Why the high figures in this literature are not comparable

Three rows above make the point concretely, and are more persuasive than the assertion alone.

The strongest sensitivities in the table — 0.949 and 0.959 — are both **patient-specific**: one
model per patient, so nothing is asked of the method that this thesis asks of its own. The same
architecture evaluated across patients in the same paper falls from 0.959 to 0.933 at the segment
tier, with specificity dropping from 0.994 to 0.927; at the seizure prevalence of a continuous
recording, a specificity of 0.927 at the segment tier corresponds to a false-alarm rate that the
paper does not report and that would be far outside the range of any row here.

Two of the highest-scoring rows report **no false-alarm rate at all**, so they cannot be placed on
a sensitivity-against-false-alarms plane, and one of them partitions its folds by window rather
than by patient, so windows of the same patient appear in both training and test.

And where the same corpus is evaluated the way this thesis evaluates it — event level, across
patients — the published sensitivity is 0.726 to 0.753 at over a hundred false alarms per day, not
the 0.90 to 0.99 that the corpus is usually associated with.

*Source: the five source papers, read on 2026-09-07; `docs/VERIFIED_NUMBERS.md` Part 7b for the
entries verified earlier; `docs/LOCKED_DOCS_ADDENDUM.md` §1.6 to §1.8.*

## Table 1.1 — Representative seizure detection approaches

Table 1.1 is Table 4.1 without the two rows for this study and without the final comparison
paragraphs. Chapter 1 presents it as the landscape; Chapter 4 adds this work to it and draws the
comparison. Keep the column order and the wording of the cells identical between the two, so a
reader turning back finds the same table with one row added.

## Figure 4.1 — which points may be plotted

The figure plane is sensitivity against false alarms per day. A study qualifies only if it is
scored at **event level**, on a **patient-independent** split, and reports a **false-alarm rate**.
Three published points qualify:

| Point | Sensitivity | False alarms / day | Corpus |
|---|---|---|---|
| Ali et al., 2024, 5-fold | 0.726 | 127.7 | CHB-MIT |
| Ali et al., 2024, leave-one-out | 0.753 | 115.0 | CHB-MIT |
| Community challenge, 2025, winner | 0.370 | 1.34 | Private |

Every other row of Table 4.1 fails at least one of the three conditions and belongs in the table
only. The horizontal axis has to reach past 128, which spreads this work's own curve into the
left-hand quarter of the plane — that shape is itself the argument and should not be corrected by
clipping the axis. Each point is labelled with its corpus, and the caption states that the
challenge point is on different data.

Nothing may be added to the plane to make it look fuller.
