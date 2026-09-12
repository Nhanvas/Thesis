# Captions

The final caption for every exhibit. Five accounts write chapters in parallel, so captions written
independently would drift, and the mandatory wording carried by several of them would be lost.

**Revision 2.** Updated after the exhibit set was reduced and four structural changes were made:
Figure 1.3 and Figure 2.11 were cut, Figure 2.7 was merged into the pipeline figure, and the
application architecture was split back into two figures. See `docs/EXHIBIT_SET_FINAL.md`.

## How to use this file

Use the caption text as written. It may be shortened for space, but **the sentences marked mandatory
may not be cut, softened or paraphrased** — each exists because leaving it out would make the exhibit
say something that is not true.

Figure captions go **below** the figure, table captions **above** the table. The numbers here are the
numbers as the exhibits currently stand. Renumbering to close the gaps left by the cuts is a separate
pass, done once across filenames, this file, and the cross-references in the five table files.

## The mandatory sentences, in one place

- Every attribution exhibit carries the word **provisional** and states that the annotation was
  **generated automatically and has not been clinically reviewed**: Figures 3.11, 3.13, 3.15 and
  Tables 3.9, 3.10, A.2, A.4.
- Figure 1.1 states that the preictal and postictal regions are **fixed windows, not annotations**.
- Figures 3.4 and 3.10 state that the scores were **recomputed on the continuous recording** and are
  **not the source of any reported number**.
- Figure 2.13 states that the **direction of the resulting bias is not established**.
- Table 2.6 states that the density measurement **characterises the choice rather than having driven
  it**. Figure 2.5 carried this too and was cut, so Table 2.6 is now its only home.
- Figure 3.8 and Table 3.4 state that chb06's F1 is **undefined, not zero**. Figure 3.7 carried this
  too and was cut.
- Table 3.3, Figure 3.6 and Figure 4.1 state that the best point on the curve was **located after the
  held-out set was scored**.

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

**Figure 1.4.** Research framework. The lower row is the processing path from the corpus to the
detected events and their channel-level interpretation; the upper row is the theoretical work that
informs the design and interprets the outcome. No path runs from a result back to the model: the
operating point is fixed on the validation patients and the held-out set is scored once.

**Table 1.1.** Representative seizure detection approaches. Rates reported per hour in the source are
converted to per day; both forms are given. Studies differ in corpus, supervision, patient split and
scoring level, and those four differences are what make most published figures on this corpus
incomparable with the present work.

**Table 1.2.** Design requirements and targets. These are design properties rather than accuracy
thresholds, because the held-out data are scored once.

**Table 1.3.** Project timeline.

---

# Chapter 2

**Figure 2.1.** The eighteen bipolar derivations used throughout this work, drawn on the international
10-20 electrode schematic. Each line connects the two electrodes of one derivation, in the order the
derivation is named. The four outer chains form the arc pattern known clinically as the double banana.
Montage per the clinical montage guideline; electrode placement per the corpus documentation.

**Figure 2.3.** One segment of recording before and after preprocessing, patient chb10. Panels (a) and
(b) show six derivations on a common time axis; the vertical scales differ because the preprocessed
signal is standardised. Panel (c) shows the power spectrum of one derivation before and after,
normalised for comparison: the mains peak at 60 Hz is removed and content above the analysis band is
attenuated.

**Figure 2.4.** Construction of a connectivity graph from one analysis window, patient chb11. (a) the
four-second segment across all derivations; (b) the five log band powers per derivation; (c) the
weighted adjacency before sparsification; (d) the graph after retaining the strongest twenty percent
of edges, thirty edges of a possible one hundred and fifty-three.

**Figure 2.6.** The complete processing pipeline, from the corpus to the two evaluation tiers. The
graph autoencoder is trained on background windows only; the latent representation feeds the
Mahalanobis readout and the two decoders feed the reconstruction readout, while the gamma-band readout
is computed directly from the signal and does not pass through the model. The decision point is gated
on the validation patients, and alternatives that fail the gate are reported rather than discarded.

**Figure 2.8.** Reconstruction error against seizure state. [The Chapter 2 writer describes the axes
from the figure itself. This exhibit predates the caption sheet and its axes are not described in the
exhibit record; do not accept a guessed description.]

**Figure 2.12.** Architecture of the review application. The application recomputes anomaly scores on
the continuous recording, retaining every window. It never reads the seizure annotations, any timeline
rebuilt from them, or the pre-split background and seizure arrays, all three of which would make a
label-free claim false. Figure 2.13 gives the measurement that forces this design.

**Figure 2.13.** Why a stored score array cannot be replayed on a time axis. Artifact rejection removes
about half the background windows of chb13 without recording their positions, so the stored array holds
12,452 scores for 25,224 timeline positions. A reconstructed timeline shifts the surviving scores out
of their original positions and, once the array is exhausted at about forty percent of the recording,
fills the remainder by resampling. Across the eight held-out patients 53.9 percent of each
reconstructed timeline carries a resampled score on average, ranging from 40.0 to 66.9 percent. The
resampling preserves the marginal distribution of each patient's own background but not its temporal
autocorrelation. *Mandatory:* the false-alarm rate is measured on these timelines, and the direction of
the resulting bias is not established.

**Figure 2.14.** Event-based scoring. (a) A detected interval is matched to an annotated seizure by any
overlap, after the annotation is extended by 30 s before onset and 60 s after offset; the detection
shown begins after the seizure has ended and still counts. (b) Detections separated by less than 90 s
are merged into one interval before scoring. (c) A detection outside the tolerance window is a false
alarm. Detections longer than five minutes are split, which is not shown. The signal is synthetic and
illustrative; the scoring depends only on the interval endpoints. *Mandatory:* specificity is not
defined at event level, because a true-negative event has no meaning once a timeline is expressed as
events; false alarms per day replaces it.

**Table 2.1.** Candidate public scalp EEG seizure corpora.

**Table 2.3.** Assignment of patients to the training, validation and held-out sets. Assignment is by
patient, so no recording from a held-out patient contributes to training or to any tuning decision.

**Table 2.4.** Preprocessing steps and their parameters.

**Table 2.6.** Decision matrix for edge sparsification. *Mandatory:* the separation measurement was
made after the pipeline was fixed and characterises the choice rather than having driven it.

**Table 2.7.** Model and training configuration.

**Table 2.8.** Decision matrix for the detection stage.

**Table 2.9.** Design of the synthetic validation grid for channel attribution. The multiplier is
applied to the chosen channels within the block only; every other channel, and every window outside
the block, is left unchanged.

**Table 2.10.** Weighted decision matrix for deployment strategy. The weights are an engineering
judgement rather than a measurement.

---

# Chapter 3

**Figure 3.1.** Separation between background and seizure windows on the held-out patients.

**Figure 3.3.** Receiver-operating and precision-recall curves, per patient and across patients.

**Figure 3.4.** Detection output on one full recording, patient chb13, recording chb13_62. The three
component scores and the fused score are shown on a shared time axis with detected intervals and
annotated seizures shaded. Two of the three annotated seizures are matched and three detections are
false positives. *Mandatory:* scores were recomputed on the continuous recording with every window
retained; they are not the source of any reported number.

**Figure 3.5.** Detection latency relative to annotated onset, with the two matching tolerances marked.

**Figure 3.6.** Sensitivity against false alarms per day across the parameter grid, with the reported
operating point and the best point on the curve marked. *Mandatory:* the best point was located after
the held-out set was scored and is a property of the curve, not a result.

**Figure 3.8.** Window-level discrimination against event-level F1, one point per held-out patient, with
reference lines at the across-patient discrimination and the pooled event F1. *Mandatory:* chb06 is
drawn at zero because its F1 is undefined, not because it scored zero.

**Figure 3.10.** One false positive with the concurrent recording, patient chb13, recording chb13_62.
The detected interval coincides with high-amplitude transient activity visible across all displayed
derivations. The signal panel shows the raw recording, unfiltered. *Mandatory:* scores were recomputed
on the continuous recording; they are not the source of any reported number.

**Figure 3.11.** Provisional channel attribution performance against injection strength on the synthetic
grid, where the affected channels are known exactly. This panel is label-free and does not depend on
any annotation.

**Figure 3.13.** Provisional per-seizure channel ranking. *Mandatory:* scored against a draft annotation
generated automatically and not clinically reviewed.

**Figure 3.15.** Provisional diffuseness against the number of annotated channels. The synthetic line is
U-shaped in the number of injected channels, and on the real annotations the generalized group sits
lower than the focal group, which is the opposite of the expected direction. The measure is therefore
reported as a methodological negative and is not used to classify. The synthetic grid used a different
set of injected-channel counts from the discrimination experiment.

**Figure 3.16.** [Application screenshot. Caption pending the build: one screen showing the detection
timeline together with the channel view.]

**Table 3.2.** Window-level discrimination per held-out patient. The across-patient value is the
unweighted mean.

**Table 3.3.** Event-level detection results at each operating point. *Mandatory:* the best point on the
curve was located after the held-out set was scored.

**Table 3.4.** Event-level performance per held-out patient at the reported operating point.
*Mandatory:* chb06's F1 is undefined, not zero.

**Table 3.5.** Results across four independently trained models on the validation patients. The two
spreads are the noise floors of this study.

**Table 3.6.** Component ablations and design alternatives, on the validation patients.

**Table 3.8.** Synthetic validation criteria and outcomes.

**Table 3.9.** Provisional attribution agreement with the draft annotation. *Mandatory:* the annotation
was generated automatically by a language model reading rendered segments of the recordings, and has
not been reviewed by a clinician. The rendering read the recordings only and never the model's own
output, so the comparison is not circular; the annotations were not produced blind.

**Table 3.10.** Within-patient similarity of the draft annotations. The pooled value is the mean over
seizure pairs, not over patients. Provisional, against the same draft annotation.

**Table 3.12.** Objectives and design requirements, with the outcome achieved for each.

---

# Chapter 4

**Figure 4.1.** This work's achievable trade-off curve against published results, on a logarithmic
false-alarm axis. Only results scored at event level, on a patient-independent split, and reporting a
false-alarm rate can be placed on this plane; three published results qualify. *Mandatory:* the best
point on the curve was located after the held-out set was scored.

**Table 4.1.** Comparison with published work, including this study. Only the first two rows are matched
to this work on corpus, scoring level, patient split and the reporting of a false-alarm rate.

**Table 4.2.** Computational and deployment cost profile. Two quantities were not measured and are
marked as such.

---

# Appendices

**Table A.1.** Corpus metadata for all twenty-three patients.

**Table A.2.** Channel annotation for every held-out seizure. *Mandatory:* the annotation was generated
automatically and has not been clinically reviewed; the source column is carried through from the
annotation file.

**Table A.4.** Concentration of the top-ranked channel against a random null, per patient. Provisional,
against the same draft annotation.

**Table A.5.** Software and library versions.

**Table A.6.** Index of pre-registrations.

---

# Content that moved into the prose

Nine figures and nine tables were cut. In every case the content survives elsewhere, and these are the
statements the text must now carry because the exhibit that carried them is gone.

| Cut exhibit | What the prose must now carry |
|---|---|
| Figure 2.2 | Held-out seizure durations: minimum 6 s, median 45 s, mean 51.9 s, maximum 205 s, 23 of 76 shorter than 20 s |
| Figure 2.5 and Table 3.1 | The two densities: 0.921 to 0.973 under the fixed threshold, 0.196 under the proportional rule, and chb17's exception at 0.224 |
| Figure 2.9 | The weight surface is flat across the region explored |
| Figure 2.11 | The multiplier is applied to the chosen channels within the block only; every other channel, and every window outside the block, is unchanged |
| Figure 3.2 | Nothing. Table 3.2 and Figure 3.3 carry it |
| Figure 3.7 | Nothing. Table 3.4 carries it row for row |
| Figure 3.9 | Nothing. Table 3.6 carries the effects and the noise band |
| Figure 3.12 | Channel-ranking agreement across four models: 0.970 plus or minus 0.026 |
| Figure 3.14 and Table 3.7 | The per-patient values, named in the text |
| Table 2.2 | The corpus is paediatric; the montage is 18 bipolar derivations at 256 Hz |
| Table 2.5 | The five bands and their ranges |
| Table 2.11 and Table 3.11 | The one measured timing figure: about 15 s per hour of recording |
| Table 2.12 | The matching rule, and why specificity is absent |
| Table A.3 and Table A.7 | Pointers to the committed files in `tables/csv/` |
