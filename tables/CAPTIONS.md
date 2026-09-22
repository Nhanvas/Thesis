# Captions — every figure and table

**Revision 8 (2026-09-22).** Every body caption below is copied verbatim from the finished chapters
(`Chapter_1` … `Chapter_4`, v2, 2026-09-21), so a caption here cannot disagree with the report. The
appendix captions are new in this revision and match `tables/tables_appendix.md` revision 2.

What changed from revision 6: the attribution captions (Figures 3.9 and 3.10, Tables 3.7 and 3.8) now
describe the final, human, model-blind, supervisor-approved annotation and its result; Figure 3.4
describes the 48 latency matches and the single tolerance line; Tables 1.1 and 4.1 carry the corrected
comparator rows; the Table A.2 caption no longer describes a machine-generated annotation; the Table
A.3 caption attributes the missing windows to preprocessing, not to artifact rejection alone.
Revision 8 also swaps Tables 3.7 and 3.8 into order of first reference, cuts Table A.6, and
removes internal process wording from the Table 3.4 caption. Revisions 2 to 7 are superseded and remain in the git history.

Numbering is unchanged from `docs/EXHIBIT_SET_FINAL.md` revision 3: 21 figures plus Figure 3.11
pending, and 28 tables (4 / 8 / 9 / 2 / 5). Figure captions go below the figure, table captions above
the table.

**Figure 3.11** is pending the web application and has no caption yet.

---

# Figures


## Chapter 1

**Figure 1.1.** Phases of the EEG signal around a seizure, patient chb11 [10]. The upper panel shows
one derivation over the full segment with the four regions shaded; the lower panels show ten-second
excerpts from each region across four derivations of the left temporal chain, drawn to a common
amplitude scale. The ictal excerpt shows the rhythmic high-amplitude activity that distinguishes a
seizure from background. *The corpus annotates seizure onset and offset only; the preictal and
postictal regions are fixed sixty-second windows defined for this illustration and are not annotated
states.*

**Figure 1.2.** Mean connectivity during background and seizure windows, patient chb11, shown before
sparsification and on a shared color scale. Coupling is broadly stronger during the seizure, which is
the observation the graph representation is built on.

**Figure 1.3.** Research framework. The lower row is the processing path from the corpus to the
detected events; the channel attribution and the web application both take those events as input. The
upper row is the theoretical work that informs the design and interprets the outcome. No path runs from
a result back to the model: the operating point is fixed on the validation patients and the test set is
scored once.


## Chapter 2

**Figure 2.1.** The eighteen bipolar derivations used throughout this work, drawn on the international
10-20 electrode schematic [42]. Each line connects the two electrodes of one derivation, in the order
the derivation is named. The four outer chains form the arc pattern known clinically as the double
banana.

**Figure 2.2.** One segment of recording before and after preprocessing, patient chb10. Panels (a) and
(b) show six derivations on a common time axis; the vertical scales differ because the preprocessed
signal is standardized. Panel (c) shows the power spectrum of one derivation before and after,
normalized for comparison: the mains peak at 60 Hz is removed and content above the analysis band is
attenuated.

**Figure 2.3.** Construction of a connectivity graph from one analysis window, patient chb11. (a) the
four-second segment across all derivations; (b) the five log band powers per derivation; (c) the
weighted adjacency before sparsification; (d) the graph after retaining the strongest twenty percent
of edges, thirty edges of a possible one hundred and fifty-three.

**Figure 2.4.** The complete processing pipeline, from the corpus to the two evaluation tiers. The
graph autoencoder is trained on background windows only; the latent representation feeds the
Mahalanobis readout and the two decoders feed the reconstruction readout, while the gamma-band readout
is computed directly from the signal and does not pass through the model. Design decisions are made on the
validation patients, and alternatives that fail are reported rather than discarded.

**Figure 2.5.** Distribution of the reconstruction readout for two validation patients, chb11 and
chb10, with background and seizure windows overlaid. The horizontal axis is the standardized
reconstruction score and the vertical axis the density of windows; the dashed lines mark the mean of
each group. For chb11 the seizure windows sit to the right of the background, for chb10 to the left,
so the same readout separates the two states in opposite directions on different patients. The latent
readout is unaffected by the reversal, which is why the two are combined.

**Figure 2.6.** Architecture of the review application. The application recomputes anomaly scores on
the continuous recording, retaining every window. It never reads the seizure annotations, any timeline
reconstructed from them, or the pre-split background and seizure arrays, all three of which would make a
label-free claim false. Table A.3 gives the measurement that forces this design.

**Figure 2.7.** Event-based scoring. (a) A detected interval is matched to an annotated seizure by any
overlap, after the annotation is extended by 30 s before onset and 60 s after offset; the detection
shown begins after the seizure has ended and still counts. (b) Detections separated by less than 90 s
are merged into one interval before scoring. (c) A detection outside the tolerance window is a false
alarm. Detections longer than five minutes are split, which is not shown. The signal is synthetic and
illustrative; the scoring depends only on the interval endpoints. *Specificity is not defined at event
level, because a true-negative event has no meaning once a timeline is expressed as events; false
alarms per day replaces it.*


## Chapter 3

**Figure 3.1.** Change in the separation between background and seizure connectivity under the
proportional rule relative to the fixed threshold, one bar per test patient. (a) relative Frobenius
distance; (b) cosine distance.

**Figure 3.2.** Receiver-operating and precision-recall curves, per patient and across patients.

**Figure 3.3.** Detection output on one full recording, patient chb13, recording chb13_62. The three
component scores and the fused score are shown on a shared time axis with detected intervals and
annotated seizures shaded. Two of the three annotated seizures are matched and three detections are
false positives. *Scores were recomputed on the continuous recording with every window retained; they
are not the source of any reported number.*

**Figure 3.4.** Detection latency relative to annotated onset for the 48 seizures matched by the
latency procedure, with the pre-onset matching tolerance marked. The latency match is computed
separately from the scoring framework's event matcher and counts one more match than the 47 true
positives at the reported operating point. The post-offset tolerance is measured from seizure end and
cannot be drawn on this axis.

**Figure 3.5.** Sensitivity against false alarms per day across the parameter grid, with the reported
operating point and the best point on the curve marked. *The best point was located after the test set
was scored and is a property of the curve, not a result.*

**Figure 3.6.** Window-level discrimination against event-level F1, one point per test patient, with
reference lines at the across-patient discrimination and the pooled event F1. *chb06 is drawn at zero
because its F1 is undefined, not because it scored zero.*

**Figure 3.7.** One false positive with the concurrent recording, patient chb13, recording chb13_62.
The detected interval coincides with high-amplitude transient activity visible across all displayed
derivations. The signal panel shows the raw recording, unfiltered. *Scores were recomputed on the
continuous recording; they are not the source of any reported number.*

**Figure 3.8.** Channel attribution performance against injection strength on the synthetic grid, where
the affected channels are known exactly. This panel is label-free and depends on no annotation.

**Figure 3.9.** Per-seizure channel ranking for the 76 test seizures, grouped by patient, with the
annotated ictal channels marked by white dots. Generalized seizures, labeled "gen.", are shown but carry
no channel contrast.

**Figure 3.10.** Diffuseness of the attribution map against the number of injected channels on the
synthetic grid. The measure is U-shaped, so it cannot separate focal from generalized seizures and is
reported as a methodological negative.


## Chapter 4

**Figure 4.1.** This work's achievable trade-off curve against published results, on a logarithmic
false-alarm axis. Only results scored at event level, on a patient-independent split, and reporting a
false-alarm rate can be placed on this plane; three published results qualify. *The best point on the
curve was located after the test set was scored.*


---

# Tables


## Chapter 1

**Table 1.1.** Representative seizure detection approaches. Rates reported per hour in the source are
converted to per day; both forms are given. Studies differ in corpus, supervision, patient split and
scoring level, and those four differences are what make most published figures on this corpus
incomparable with the present work.

**Table 1.2.** Design requirements and targets. These are design properties rather than accuracy
thresholds, because the test data are scored once.

**Table 1.3.** Thesis timeline.

**Table 1.4.** Specific task carried out in each week.


## Chapter 2

**Table 2.1.** Candidate public scalp EEG seizure corpora.

**Table 2.2.** Assignment of patients to the training, validation and test sets. Assignment is by
patient, so no recording from a test patient contributes to training or to any tuning decision.

**Table 2.3.** Preprocessing steps and their parameters.

**Table 2.4.** Decision matrix for edge sparsification. *The separation measurement was made after the
pipeline was fixed and characterizes the choice rather than having driven it.*

**Table 2.5.** Model and training configuration.

**Table 2.6.** Decision matrix for the detection stage.

**Table 2.7.** Design of the synthetic validation grid for channel attribution. The multiplier is
applied to the chosen channels within the block only; every other channel, and every window outside
the block, is left unchanged.

**Table 2.8.** Weighted decision matrix for deployment strategy. The weights are an engineering
judgment rather than a measurement.


## Chapter 3

**Table 3.1.** Window-level discrimination per test patient. The across-patient value is the unweighted
mean.

**Table 3.2.** Event-level detection results at each operating point. *The best point on the curve was
located after the test set was scored.*

**Table 3.3.** Event-level performance per test patient at the reported operating point. *chb06's F1 is
undefined, not zero.*

**Table 3.4.** Results across four independently trained models on the validation patients. A difference smaller than
the spread is not treated as real.

**Table 3.5.** Component ablations and design alternatives, on the validation patients.

**Table 3.6.** Synthetic validation criteria and outcomes.

**Table 3.7.** Composition of the channel annotation and within-patient similarity. Similarity is the
Jaccard index between the annotated channel sets of two focal seizures of the same patient, averaged
over seizure pairs.

**Table 3.8.** Agreement between the channel ranking and the blind channel annotation, over 62 focal
test seizures. *Single annotator, blind to the model, approved by the supervisor; agreement is
concordance, not accuracy.*

**Table 3.9.** Objectives and design requirements, with the outcome achieved for each.


## Chapter 4

**Table 4.1.** Comparison with published work, including this study. Rates reported per hour in the
source are converted to per day; both forms are given. Only the first two rows are matched to this work
on corpus, scoring level, patient split and the reporting of a false-alarm rate. *The best point on
this study's curve was located after the test set was scored.*

**Table 4.2.** Computational and deployment cost profile. Two quantities were not measured and are
marked as such.


## Appendix

**Table A.1.** Corpus metadata for all twenty-three patients, with the set to which each is assigned.

**Table A.2.** Channel annotation for every test seizure. The annotation was made by the author from
the raw 18-channel EEG, blind to every model output, and lists every channel carrying a clear ictal
discharge; the protocol and the annotation were approved by the supervisor. A generalized seizure
involves all eighteen channels.

**Table A.3.** Composition of the reconstructed evaluation timeline, per test patient. Preprocessing
removes background windows, through artifact rejection and the post-seizure exclusion, without
recording their positions, so a stored score array holds fewer values than the timeline it has to fill:
for chb13, 12,452 scores for 25,224 positions. The reconstruction shifts the surviving scores out of
their original positions and, once the array is exhausted, fills the remainder by resampling from that
patient's own background, which preserves the distribution of the background but not its order in
time. *The false-alarm rate is measured on these timelines, and the direction of the resulting bias is
not established.*

**Table A.4.** Concentration of the top-ranked channel against a random null, per test patient.
Computed from the model's own channel rankings; it uses no annotation.

**Table A.5.** Software and library versions.
