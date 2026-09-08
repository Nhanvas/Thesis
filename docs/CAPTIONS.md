# Captions

The final caption for every exhibit. Five accounts write chapters in parallel, so captions written
independently would drift, and the mandatory wording carried by several of them would be lost.

## How to use this file

Use the caption text exactly as written. It may be shortened for space, but **the sentences marked
mandatory may not be cut, softened or paraphrased** — each one exists because leaving it out would
make the exhibit say something that is not true.

Figure captions go **below** the figure, table captions **above** the table, per the report format.
Numbering follows the exhibit list. Where a caption names a source, that source is already in the
reference sheet.

## The mandatory sentences, in one place

So that a reviewer can check them without reading the whole file:

- Every attribution exhibit carries the word **provisional**, and states that the annotation was
  **generated automatically and has not been clinically reviewed**. Exhibits: Fig 3.11, 3.13, 3.14,
  3.15, Table 3.9, Table 3.10, Table A.2, Table A.7.
- Fig 1.1 states that the preictal and postictal regions are **fixed windows, not annotations**.
- Fig 2.10, 3.4 and 3.10 state that the scores were **recomputed on the continuous recording** and
  are **not the source of any reported number**.
- Fig 2.13 states that the **direction of the resulting bias is not established**.
- Fig 2.5 and Table 2.6 state that the density measurement **characterises the choice rather than
  having driven it**.
- Fig 3.8 and Table 3.4 state that chb06's F1 is **undefined, not zero**.
- Fig 4.1 and Table 4.1 state that the best point on the curve was **located after the held-out set
  was scored**.

---

# Chapter 1

**Figure 1.1.** Phases of the EEG signal around a seizure, patient chb11. The upper panel shows one
derivation over the full segment with the four regions shaded; the lower panels show ten-second
excerpts from each region across four derivations of the left temporal chain, drawn to a common
amplitude scale. The ictal excerpt shows the rhythmic high-amplitude activity that distinguishes a
seizure from background. *Mandatory:* the corpus annotates seizure onset and offset only; the
preictal and postictal regions are fixed sixty-second windows defined for this illustration and are
not annotated states.

**Figure 1.2.** Mean connectivity during background and seizure windows, patient chb11, shown before
sparsification and on a shared colour scale. Coupling is broadly stronger during the seizure, which
is the observation the graph representation is built on.

**Figure 1.3.** Overview of the processing pipeline, from the recording to the intervals presented for
review. No seizure annotation is used at any stage of this path.

**Figure 1.4.** Project timeline over twelve weeks. Drawn from Table 1.3.

**Figure 1.5.** Research framework: each objective with the method that addresses it and the output it
produces. The four lines are parallel rather than sequential.

**Table 1.1.** Representative seizure detection approaches. Rates reported per hour in the source are
converted to per day; both forms are given. Studies differ in corpus, supervision, patient split and
scoring level, and those four differences are what make most published figures on this corpus
incomparable with the present work.

**Table 1.2.** Design requirements and targets. These are design properties rather than accuracy
thresholds, because the held-out data are scored once.

**Table 1.3.** Project timeline. Drawn as Figure 1.4.

---

# Chapter 2

**Figure 2.1.** The eighteen bipolar derivations used throughout this work, drawn on the international
10–20 electrode schematic. The four outer chains form the arc pattern known clinically as the double
banana. Montage per the clinical montage guideline; electrode placement per the corpus documentation.

**Figure 2.2.** Distribution of annotated seizure durations across the corpus, on a logarithmic axis,
with the held-out subset distinguished. The four-second analysis window is marked: twenty-three of the
seventy-six held-out seizures are shorter than twenty seconds, and the shortest is barely longer than
one and a half windows.

**Figure 2.3.** One segment of recording before and after preprocessing, patient chb10. Panels (a) and
(b) show six derivations on a common time axis; the vertical scales differ because the preprocessed
signal is standardised. Panel (c) shows the power spectrum of one derivation before and after,
normalised for comparison: the mains peak at 60 Hz is removed and content above the analysis band is
attenuated.

**Figure 2.4.** Construction of a connectivity graph from one analysis window, patient chb11. (a) the
four-second segment across all derivations; (b) the five log band powers per derivation; (c) the
weighted adjacency before sparsification; (d) the graph after retaining the strongest twenty percent
of edges, thirty edges of a possible one hundred and fifty-three.

**Figure 2.5.** Adjacency and resulting graph under the two sparsification rules, patient chb11. The
density printed on each panel is that of the window shown. The fixed threshold leaves the graph almost
complete and its density varies between patients; the proportional rule holds density constant by
construction. *Mandatory:* the density comparison was measured after the pipeline was fixed, so it
characterises the choice rather than having driven it.

**Figure 2.6.** Architecture of the graph autoencoder. The encoder maps twenty-three input features per
node to a sixteen-dimensional latent representation; the decoder reconstructs the adjacency by inner
product and the node features through two fully connected layers. The model has 3,285 trainable
parameters.

**Figure 2.7.** Three anomaly readouts from one shared encoder, each standardised against the patient's
own background before equal-weight fusion. The background distribution is fitted per patient without
using any annotation.

**Figure 2.8.** Reconstruction error against seizure state. [Caption to be completed by the Chapter 2
writer from the figure's own content; the exhibit predates this caption sheet and its axes should be
described directly.]

**Figure 2.9.** Ensemble weight surface on the validation patients. The surface is flat across the
region explored, which is why equal weighting was adopted rather than an optimised set.

**Figure 2.10.** Change point detection on a fused anomaly score series, patient chb13, recording
chb13_62, shown as a five-minute window around one annotated seizure. Detected change points are drawn
as vertical lines and the annotated seizure is shaded. *Mandatory:* scores were recomputed on the
continuous recording with every window retained, using the study's fitted parameters; they are not the
source of any reported number.

**Figure 2.11.** Channel attribution: (a) how a per-channel score is formed from the per-node
reconstruction error; (b) the synthetic injection scheme used to validate it, where the affected
channels are known exactly. The diffuseness experiment used a different set of injected-channel counts
from the one shown; see Figure 3.15.

**Figure 2.12.** Architecture of the review application. The paths marked on the right are never read
at runtime: the application recomputes scores on the continuous recording rather than replaying stored
ones.

**Figure 2.13.** Why stored scores cannot be replayed on a time axis. Artifact rejection removes
windows without recording their positions, so the stored array is ordered by segment; rebuilding a
timeline from it shifts the surviving scores and, once the array is exhausted, fills the remainder by
resampling. Across the eight held-out patients an average of 53.9 percent of each reconstructed
timeline carries a resampled score, ranging from 40.0 to 66.9 percent. *Mandatory:* the false-alarm
rate is measured on these timelines, and the direction of the resulting bias is not established.

**Figure 2.14.** Event-based scoring. A detected interval is matched to an annotated seizure by any
overlap after a thirty-second tolerance before onset and sixty seconds after offset; detections closer
than ninety seconds are merged. *Mandatory:* specificity is not defined at event level, because a
true-negative event has no meaning once a timeline is expressed as events; false alarms per day
replaces it.

**Table 2.1.** Candidate public scalp EEG seizure corpora.

**Table 2.2.** Characteristics of the selected corpus. Figures are this project's own parse of the
recording summary files.

**Table 2.3.** Assignment of patients to the training, validation and held-out sets. Assignment is by
patient, so no recording from a held-out patient contributes to training or to any tuning decision.

**Table 2.4.** Preprocessing steps and their parameters.

**Table 2.5.** Spectral bands used as node features.

**Table 2.6.** Decision matrix for edge sparsification. *Mandatory:* the separation measurement was
made after the pipeline was fixed and characterises the choice rather than having driven it.

**Table 2.7.** Model and training configuration.

**Table 2.8.** Decision matrix for the detection stage.

**Table 2.9.** Design of the synthetic validation grid for channel attribution.

**Table 2.10.** Weighted decision matrix for deployment strategy. The weights are an engineering
judgement rather than a measurement.

**Table 2.11.** Processing stages of the review application. Every window is retained, which is a
deliberate divergence from the study pipeline.

**Table 2.12.** Reported metrics and their definitions.

---

# Chapter 3

**Figure 3.1.** Separation between background and seizure windows on the held-out patients.

**Figure 3.2.** Distribution of fused anomaly scores by state.

**Figure 3.3.** Receiver-operating and precision–recall curves, per patient and across patients.

**Figure 3.4.** Detection output on one full recording, patient chb13, recording chb13_62. The three
component scores and the fused score are shown on a shared time axis with detected intervals and
annotated seizures shaded. Two of the three annotated seizures are matched and three detections are
false positives. *Mandatory:* scores were recomputed on the continuous recording with every window
retained; they are not the source of any reported number.

**Figure 3.5.** Detection latency relative to annotated onset, with the two matching tolerances marked.

**Figure 3.6.** Sensitivity against false alarms per day across the parameter grid, with the reported
operating point and the best point on the curve marked. *Mandatory:* the best point was located after
the held-out set was scored and is a property of the curve, not a result.

**Figure 3.7.** Event-level performance per patient at the reported operating point. *Mandatory:*
chb06 produces no detections at this operating point, so its F1 is undefined rather than zero.

**Figure 3.8.** Window-level discrimination against event-level F1, one point per held-out patient,
with reference lines at the across-patient discrimination and the pooled event F1. *Mandatory:* chb06
is drawn at zero because its F1 is undefined, not because it scored zero.

**Figure 3.9.** Effect of each design alternative relative to the adopted system, on the validation
patients, with the seed-to-seed noise band marked. Changes inside that band are not distinguishable
from the effect of retraining the same model.

**Figure 3.10.** One false positive with the concurrent recording, patient chb13, recording chb13_62.
The detected interval coincides with high-amplitude transient activity visible across all displayed
derivations. The signal panel shows the raw recording, unfiltered. *Mandatory:* scores were recomputed
on the continuous recording; they are not the source of any reported number.

**Figure 3.11.** Provisional channel attribution performance against injection strength on the
synthetic grid, where the affected channels are known exactly. This panel is label-free and does not
depend on any annotation.

**Figure 3.12.** Stability of the channel ranking across four independently trained models.

**Figure 3.13.** Provisional per-seizure channel ranking. *Mandatory:* scored against a draft
annotation generated automatically and not clinically reviewed.

**Figure 3.14.** Provisional agreement with the draft annotation, per patient. *Mandatory:* the
annotation was generated automatically and has not been clinically reviewed; every value shown is
provisional.

**Figure 3.15.** Provisional diffuseness against the number of annotated channels. The synthetic line
is U-shaped in the number of injected channels, and on the real annotations the generalized group
sits lower than the focal group, which is the opposite of the expected direction. The measure is
therefore reported as a methodological negative and is not used to classify. The synthetic grid used a
different set of injected-channel counts from the discrimination experiment.

**Figures 3.16 to 3.18.** [Application screenshots — captions pending the build.]

**Table 3.1.** Graph density under each sparsification rule.

**Table 3.2.** Window-level discrimination per held-out patient. The across-patient value is the
unweighted mean.

**Table 3.3.** Event-level detection results at each operating point. *Mandatory:* the best point on
the curve was located after the held-out set was scored.

**Table 3.4.** Event-level performance per held-out patient at the reported operating point.
*Mandatory:* chb06's F1 is undefined, not zero.

**Table 3.5.** Results across four independently trained models on the validation patients. The two
spreads are the noise floors of this study.

**Table 3.6.** Component ablations and design alternatives, on the validation patients.

**Table 3.7.** Per-patient effect of adding directed connectivity at the representation level.

**Table 3.8.** Synthetic validation criteria and outcomes.

**Table 3.9.** Provisional attribution agreement with the draft annotation. *Mandatory:* the
annotation was generated automatically by a language model reading rendered segments of the
recordings, and has not been reviewed by a clinician. The rendering read the recordings only and never
the model's own output, so the comparison is not circular; the annotations were not produced blind.

**Table 3.10.** Within-patient similarity of the draft annotations. The pooled value is the mean over
seizure pairs, not over patients.

**Table 3.11.** Processing time per stage. [Pending the application build.]

**Table 3.12.** Objectives and design requirements, with the outcome achieved for each.

---

# Chapter 4

**Figure 4.1.** This work's achievable trade-off curve against published results, on a logarithmic
false-alarm axis. Only results scored at event level, on a patient-independent split, and reporting a
false-alarm rate can be placed on this plane; three published results qualify. *Mandatory:* the best
point on the curve was located after the held-out set was scored.

**Table 4.1.** Comparison with published work, including this study. Only the first two rows are
matched to this work on corpus, scoring level, patient split and the reporting of a false-alarm rate.

**Table 4.2.** Computational and deployment cost profile. Two quantities were not measured and are
marked as such.

---

# Appendices

**Table A.1.** Corpus metadata for all twenty-three patients.

**Table A.2.** Channel annotation for every held-out seizure. *Mandatory:* the annotation was
generated automatically and has not been clinically reviewed; the source column is carried through
from the annotation file.

**Table A.3.** Full parameter grid on the held-out set, all 384 cells.

**Table A.4.** Concentration of the top-ranked channel against a random null, per patient.

**Table A.5.** Software and library versions.

**Table A.6.** Index of pre-registrations.

**Table A.7.** Provisional top-ranked channels per seizure. *Mandatory:* scored against a draft
annotation generated automatically and not clinically reviewed.

---

# Two captions this file cannot write

**Figure 2.8** predates this caption sheet and its axes are not described anywhere in the exhibit
record. The Chapter 2 writer should describe it from the figure itself rather than accept a guess.

**Figures 3.16 to 3.18 and Table 3.11** wait on the application build.
