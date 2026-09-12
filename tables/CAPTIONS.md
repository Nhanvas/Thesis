# Captions

The final caption for every exhibit. Captions written independently would drift, and the mandatory
wording several of them carry would be lost.

**Revision 5.** One terminology change throughout, on top of the four corrections made in revision 4.
The numbering settled in revision 3 is unchanged and remains final: figures and tables run
consecutively within each chapter, in order of first reference. The old-to-new map is at the end of
this file, together with the commands that rename the image files to match.

Superseded: revisions 2, 3 and 4. The exhibit set itself is `docs/EXHIBIT_SET_FINAL.md`; the
reasoning behind each cut stays in `docs/EXHIBIT_TRIAGE.md` and is not edited.

## How to use this file

Use the caption text as written. It may be shortened for space, but **the sentences marked mandatory
may not be cut, softened or paraphrased**, because leaving one out would make the exhibit say
something that is not true.

Figure captions go **below** the figure, table captions **above** the table.

## The mandatory sentences, in one place

- Every exhibit **scored against the draft channel annotation** carries the word **provisional** and
  states that the annotation was **generated automatically and has not been clinically reviewed**:
  Figures 3.9 and 3.10, Tables 3.7, 3.8 and A.2.
- Figure 1.1 states that the preictal and postictal regions are **fixed windows, not annotations**.
- Figures 3.3 and 3.7 state that the scores were **recomputed on the continuous recording** and are
  **not the source of any reported number**.
- Table A.3 states that the **direction of the resulting bias is not established**.
- Table 2.4 states that the **separation** measurement characterises the choice rather than having
  driven it. The density measurement was available when the choice was made and is not covered by
  this sentence.
- Figure 3.6 and Table 3.3 state that chb06's F1 is **undefined, not zero**.
- Table 3.2, Figure 3.5 and Figure 4.1 state that the best point on the curve was **located after the
  test set was scored**.
- Figure 2.7 states that **specificity is not defined at event level**.

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

**Figure 1.3.** Research framework. The lower row is the processing path from the corpus to the
detected events and their channel-level interpretation; the upper row is the theoretical work that
informs the design and interprets the outcome. No path runs from a result back to the model: the
operating point is fixed on the validation patients and the test set is scored once.

**Table 1.1.** Representative seizure detection approaches. Rates reported per hour in the source are
converted to per day; both forms are given. Studies differ in corpus, supervision, patient split and
scoring level, and those four differences are what make most published figures on this corpus
incomparable with the present work.

**Table 1.2.** Design requirements and targets. These are design properties rather than accuracy
thresholds, because the test data are scored once.

**Table 1.3.** Thesis timeline.

**Table 1.4.** Specific task carried out in each week.

---

# Chapter 2

**Figure 2.1.** The eighteen bipolar derivations used throughout this work, drawn on the international
10-20 electrode schematic. Each line connects the two electrodes of one derivation, in the order the
derivation is named. The four outer chains form the arc pattern known clinically as the double banana.
Montage per the clinical montage guideline; electrode placement per the corpus documentation.

**Figure 2.2.** One segment of recording before and after preprocessing, patient chb10. Panels (a) and
(b) show six derivations on a common time axis; the vertical scales differ because the preprocessed
signal is standardised. Panel (c) shows the power spectrum of one derivation before and after,
normalised for comparison: the mains peak at 60 Hz is removed and content above the analysis band is
attenuated.

**Figure 2.3.** Construction of a connectivity graph from one analysis window, patient chb11. (a) the
four-second segment across all derivations; (b) the five log band powers per derivation; (c) the
weighted adjacency before sparsification; (d) the graph after retaining the strongest twenty percent
of edges, thirty edges of a possible one hundred and fifty-three.

**Figure 2.4.** The complete processing pipeline, from the corpus to the two evaluation tiers. The
graph autoencoder is trained on background windows only; the latent representation feeds the
Mahalanobis readout and the two decoders feed the reconstruction readout, while the gamma-band readout
is computed directly from the signal and does not pass through the model. The decision point is gated
on the validation patients, and alternatives that fail the gate are reported rather than discarded.

**Figure 2.5.** Distribution of the reconstruction readout for two validation patients, chb11 and
chb10, with background and seizure windows overlaid. The horizontal axis is the standardised
reconstruction score and the vertical axis the density of windows; the dashed lines mark the mean of
each group. For chb11 the seizure windows sit to the right of the background, for chb10 to the left,
so the same readout separates the two states in opposite directions on different patients. The
latent readout is unaffected by the reversal, which is why the two are combined.

**Figure 2.6.** Architecture of the review application. The application recomputes anomaly scores on
the continuous recording, retaining every window. It never reads the seizure annotations, any timeline
rebuilt from them, or the pre-split background and seizure arrays, all three of which would make a
label-free claim false. Table A.3 gives the measurement that forces this design.

**Figure 2.7.** Event-based scoring. (a) A detected interval is matched to an annotated seizure by any
overlap, after the annotation is extended by 30 s before onset and 60 s after offset; the detection
shown begins after the seizure has ended and still counts. (b) Detections separated by less than 90 s
are merged into one interval before scoring. (c) A detection outside the tolerance window is a false
alarm. Detections longer than five minutes are split, which is not shown. The signal is synthetic and
illustrative; the scoring depends only on the interval endpoints. *Mandatory:* specificity is not
defined at event level, because a true-negative event has no meaning once a timeline is expressed as
events; false alarms per day replaces it.

**Table 2.1.** Candidate public scalp EEG seizure corpora.

**Table 2.2.** Assignment of patients to the training, validation and test sets. Assignment is by
patient, so no recording from a test patient contributes to training or to any tuning decision.

**Table 2.3.** Preprocessing steps and their parameters.

**Table 2.4.** Decision matrix for edge sparsification. *Mandatory:* the separation measurement was
made after the pipeline was fixed and characterises the choice rather than having driven it.

**Table 2.5.** Model and training configuration.

**Table 2.6.** Decision matrix for the detection stage.

**Table 2.7.** Design of the synthetic validation grid for channel attribution. The multiplier is
applied to the chosen channels within the block only; every other channel, and every window outside
the block, is left unchanged.

**Table 2.8.** Weighted decision matrix for deployment strategy. The weights are an engineering
judgement rather than a measurement.

---

# Chapter 3

**Figure 3.1.** Separation between background and seizure windows on the test patients.

**Figure 3.2.** Receiver-operating and precision-recall curves, per patient and across patients.

**Figure 3.3.** Detection output on one full recording, patient chb13, recording chb13_62. The three
component scores and the fused score are shown on a shared time axis with detected intervals and
annotated seizures shaded. Two of the three annotated seizures are matched and three detections are
false positives. *Mandatory:* scores were recomputed on the continuous recording with every window
retained; they are not the source of any reported number.

**Figure 3.4.** Detection latency relative to annotated onset, with the two matching tolerances marked.

**Figure 3.5.** Sensitivity against false alarms per day across the parameter grid, with the reported
operating point and the best point on the curve marked. *Mandatory:* the best point was located after
the test set was scored and is a property of the curve, not a result.

**Figure 3.6.** Window-level discrimination against event-level F1, one point per test patient, with
reference lines at the across-patient discrimination and the pooled event F1. *Mandatory:* chb06 is
drawn at zero because its F1 is undefined, not because it scored zero.

**Figure 3.7.** One false positive with the concurrent recording, patient chb13, recording chb13_62.
The detected interval coincides with high-amplitude transient activity visible across all displayed
derivations. The signal panel shows the raw recording, unfiltered. *Mandatory:* scores were recomputed
on the continuous recording; they are not the source of any reported number.

**Figure 3.8.** Channel attribution performance against injection strength on the synthetic grid, where
the affected channels are known exactly. This panel is label-free: it depends on no annotation, and
the results shown are not provisional.

**Figure 3.9.** Provisional per-seizure channel ranking. *Mandatory:* scored against a draft annotation
generated automatically and not clinically reviewed.

**Figure 3.10.** Provisional diffuseness against the number of annotated channels. The synthetic line is
U-shaped in the number of injected channels, and on the real annotations the generalized group sits
lower than the focal group, which is the opposite of the expected direction. The measure is therefore
reported as a methodological negative and is not used to classify. The synthetic grid used a different
set of injected-channel counts from the discrimination experiment.

**Figure 3.11.** [Application screenshot. Caption pending the build: one screen showing the detection
timeline together with the channel view.]

**Table 3.1.** Window-level discrimination per test patient. The across-patient value is the
unweighted mean.

**Table 3.2.** Event-level detection results at each operating point. *Mandatory:* the best point on the
curve was located after the test set was scored.

**Table 3.3.** Event-level performance per test patient at the reported operating point.
*Mandatory:* chb06's F1 is undefined, not zero.

**Table 3.4.** Results across four independently trained models on the validation patients. The two
spreads are the noise floors of this study.

**Table 3.5.** Component ablations and design alternatives, on the validation patients.

**Table 3.6.** Synthetic validation criteria and outcomes.

**Table 3.7.** Provisional attribution agreement with the draft annotation. *Mandatory:* the annotation
was generated automatically by a language model reading rendered segments of the recordings, and has
not been reviewed by a clinician. The rendering read the recordings only and never the model's own
output, so the comparison is not circular; the annotations were not produced blind.

**Table 3.8.** Within-patient similarity of the draft annotations. The pooled value is the mean over
seizure pairs, not over patients. Provisional, against the same draft annotation.

**Table 3.9.** Objectives and design requirements, with the outcome achieved for each.

---

# Chapter 4

**Figure 4.1.** This work's achievable trade-off curve against published results, on a logarithmic
false-alarm axis. Only results scored at event level, on a patient-independent split, and reporting a
false-alarm rate can be placed on this plane; three published results qualify. *Mandatory:* the best
point on the curve was located after the test set was scored.

**Table 4.1.** Comparison with published work, including this study. Only the first two rows are matched
to this work on corpus, scoring level, patient split and the reporting of a false-alarm rate.

**Table 4.2.** Computational and deployment cost profile. Two quantities were not measured and are
marked as such.

---

# Appendices

**Table A.1.** Corpus metadata for all twenty-three patients.

**Table A.2.** Channel annotation for every test seizure. *Mandatory:* the annotation was generated
automatically by a language model and has not been reviewed by a clinician; it records the leading one
or two channels of each seizure, not every channel involved.

**Table A.3.** Composition of the reconstructed evaluation timeline, per test patient. Artifact
rejection removes background windows without recording their positions, so a stored score array holds
fewer values than the timeline it has to fill: for chb13, 12,452 scores for 25,224 positions. A
reconstructed timeline shifts the surviving scores out of their original positions and, once the array
is exhausted, fills the remainder by resampling from that patient's own background. The resampling
preserves the marginal distribution of the background but not its temporal autocorrelation.
*Mandatory:* the false-alarm rate is measured on these timelines, and the direction of the resulting
bias is not established.

**Table A.4.** Concentration of the top-ranked channel against a random null, per patient. Computed
from the model's own channel rankings against a combinatorial null; it uses no annotation and is not
provisional.

**Table A.5.** Software and library versions.

**Table A.6.** Index of pre-registrations.

---

# What changed in revision 5

**The three sets are named training, validation and test.** Earlier revisions called the eight
patients scored once the *held-out* set. The report now uses *test* everywhere, matching the split
file's own key names and the ordinary reading of the term. Every caption, every table heading and
every table cell follows the same naming; the same change applies to the five files in `tables/`.
Nothing about the split itself changes, and the sentences stating that the set is scored once and
that no recording from it reaches training or tuning are kept exactly where they were.

---

# What changed in revision 4

**Table 2.4's mandatory sentence named the wrong measurement.** The summary list said the *density*
measurement characterises the choice rather than having driven it. The caption itself, and the table
in `tables/tables_ch2.md`, both say *separation*, and separation is correct: the density measurement
was available when the rule was chosen and is the design-time reason for it, while the separation
measurement was made after the pipeline was fixed. Marking the density measurement as after the fact
would have discarded the strongest reason in the verdict paragraph.

**Figure 2.5 has a caption.** Revision 3 left an instruction in its place because the axes were not in
the exhibit record. They have now been read from the figure.

**Table 3.7 old has its own row in the moved-into-prose table.** It shared a row with Figure 3.14 old
and the shared wording was too brief to reconstruct what the cut table carried. The four values it
held are now written out, because Chapter 3 §3.5.2 and Chapter 4 §4.3 both depend on them and no
exhibit carries them any more.

**The fivefold timing variation was attached to the wrong measurement.** Revision 3 read as though the
end-to-end figure itself varied fivefold. `web_demo/BUILD_PROGRESS.md` §4 records the variation on the
adjacency and band power stage, 22 to 110 s on identical code and the same file, attributed to
background load. The end-to-end figure of 9.76 s per hour is a single measurement on one recording.

---

# What changed in revision 3

## Four corrections

**The weight surface is not flat.** Revision 2's moved-into-prose table instructed the writer to state
that "the weight surface is flat across the region explored". `LOCKED_DOCS_ADDENDUM.md` §1.3 and
`VERIFIED_NUMBERS.md` Part 5 record the opposite: the best point found reaches 0.9405, equal weighting
reaches 0.9283, the gap of 0.0122 exceeds the spread across independently trained models, and equal
weighting is not among the twenty-nine points within 0.005 of the optimum. Chapter 2 and Chapter 4 both
already state this correctly, so following revision 2 would have put three parts of the report in
conflict. The corrected statement is in the table below.

**The processing figure is not fifteen seconds per hour.** Revision 2 instructed the writer to carry
"about 15 s per hour of recording". `REPO_MAP.md` §3b records, dated 2026-09-10, that this was a
component benchmark covering adjacency construction and band powers only, never the full pipeline. The
measured end-to-end figure is 9.76 s per hour on one four-hour recording, processor only
(`web_demo/BUILD_PROGRESS.md` §4). The same record notes run-to-run variation of roughly fivefold, 22
to 110 s, on identical code and the same file; that variation was observed on the adjacency and band
power stage and is attributed to background load on the development machine. Report the figure as
indicative and state the variation, and do not attach the fivefold range to the end-to-end number as
though it had been measured there.

**Figure 3.8 is not provisional.** Revision 2's caption opened with the word and then said in its own
next sentence that the panel is label-free and depends on no annotation. `VERIFIED_NUMBERS.md` §7.1 is
explicit that the label-free half of the attribution work is unaffected and not provisional. The word
now appears only on exhibits scored against the draft annotation, which is the distinction the whole
attribution argument rests on: applying it everywhere would erase it.

**Table A.4 is not scored against the annotation.** Revision 2 marked it "provisional, against the same
draft annotation". It is neither. It reports how often each patient's top-ranked channel repeats,
against a combinatorial null, and it covers all eight test patients including chb06 and chb13,
which contribute no annotated seizure at all.

## Two exhibits added

**Table 1.4**, the week-by-week detail of the timeline, following the reference thesis, which presents
its schedule as a calendar grid and a task table rather than as a chart.

**Table A.3**, the timeline composition. Figure 2.13 was cut and its evidence would otherwise have been
lost: the 53.9 percent average, the 40.0 to 66.9 percent range, and the mandatory sentence about the
direction of the bias. The table restores all three, and the numbers become checkable per patient
rather than quoted as a pair of summary figures.

## Content that moved into the prose

Eleven figures and eleven tables were cut across P3. In every case the content survives elsewhere.
These are the statements the text must now carry because the exhibit that carried them is gone.

| Cut exhibit | What the prose must now carry |
|---|---|
| Figure 1.3, pipeline overview | Nothing. Figure 2.4 carries it, in the chapter where its terms are defined |
| Figure 2.2, seizure durations | Test seizure durations: minimum 6 s, median 45 s, mean 51.9 s, maximum 205 s, and 23 of 76 shorter than 20 s |
| Figure 2.5 old, sparsification rules, and Table 3.1 old, density | The two densities: 0.921 to 0.973 under the fixed threshold, 0.196 under the proportional rule, and chb17's exception at 0.224 |
| Figure 2.9 old, weight simplex | The best point found reaches 0.9405 and equal weighting 0.9283, a gap of 0.0122; twenty-nine points lie within 0.005 of the optimum and equal weighting is not among them. The surface is **not** flat at the point this study uses |
| Figure 2.10 old, change point detection | Nothing. Figure 3.3 shows the same recording with more context |
| Figure 2.11 old, attribution and injection | The multiplier is applied to the chosen channels within the block only; every other channel, and every window outside the block, is unchanged. Now carried by Table 2.7's caption |
| Figure 2.13 old, timeline replay | Now Table A.3 |
| Figure 3.2 old, score distributions | Nothing. Table 3.1 and Figure 3.2 carry it |
| Figure 3.7 old, per-patient event | Nothing. Table 3.3 carries it row for row |
| Figure 3.9 old, alternatives effect | Nothing. Table 3.5 carries the effects and the noise band |
| Figure 3.12 old, seed stability | Channel-ranking agreement across four models: 0.970 plus or minus 0.026, and agreement on the single most anomalous channel in 87.3 percent of seizures |
| Figure 3.14 old | The per-patient agreement values, named in the text |
| Table 3.7 old | The relation's own discriminative check, 0.710, 0.674 and 0.888 against a null near 0.500, and the per-patient change at the representation level: chb22 +0.137, chb11 +0.052, chb10 −0.059, ensemble 0.928 to 0.909 |
| Table 2.2 old, corpus characteristics | The corpus is paediatric; the montage is 18 bipolar derivations at 256 Hz |
| Table 2.5 old, spectral bands | The five bands and their ranges |
| Table 2.11 and Table 3.11 old, processing stages and timing | The one measured figure: 9.76 s per hour of recording, measured end to end on one four-hour recording on a general-purpose processor. The figure is indicative: identical code on the same file varied by roughly fivefold on one stage, which is attributed to background load on that machine |
| Table 2.12 old, metric definitions | The matching rule, and why specificity is absent |
| Table A.3 and A.7 old, parameter grid and top-three channels | Pointers to the committed files in `tables/csv/` |

---

# Old-to-new map

| Old | New | | Old | New |
|---|---|---|---|---|
| Figure 1.1 | Figure 1.1 | | Table 1.1 | Table 1.1 |
| Figure 1.2 | Figure 1.2 | | Table 1.2 | Table 1.2 |
| Figure 1.4 | **Figure 1.3** | | Table 1.3 | Table 1.3 |
| Figure 2.1 | Figure 2.1 | | *new* | **Table 1.4** |
| Figure 2.3 | **Figure 2.2** | | Table 2.1 | Table 2.1 |
| Figure 2.4 | **Figure 2.3** | | Table 2.3 | **Table 2.2** |
| Figure 2.6 | **Figure 2.4** | | Table 2.4 | **Table 2.3** |
| Figure 2.8 | **Figure 2.5** | | Table 2.6 | **Table 2.4** |
| Figure 2.12 | **Figure 2.6** | | Table 2.7 | **Table 2.5** |
| Figure 2.14 | **Figure 2.7** | | Table 2.8 | **Table 2.6** |
| Figure 3.1 | Figure 3.1 | | Table 2.9 | **Table 2.7** |
| Figure 3.3 | **Figure 3.2** | | Table 2.10 | **Table 2.8** |
| Figure 3.4 | **Figure 3.3** | | Table 3.2 | **Table 3.1** |
| Figure 3.5 | **Figure 3.4** | | Table 3.3 | **Table 3.2** |
| Figure 3.6 | **Figure 3.5** | | Table 3.4 | **Table 3.3** |
| Figure 3.8 | **Figure 3.6** | | Table 3.5 | **Table 3.4** |
| Figure 3.10 | **Figure 3.7** | | Table 3.6 | **Table 3.5** |
| Figure 3.11 | **Figure 3.8** | | Table 3.8 | **Table 3.6** |
| Figure 3.13 | **Figure 3.9** | | Table 3.9 | **Table 3.7** |
| Figure 3.15 | **Figure 3.10** | | Table 3.10 | **Table 3.8** |
| Figure 3.16 | **Figure 3.11** | | Table 3.12 | **Table 3.9** |
| Figure 4.1 | Figure 4.1 | | Tables 4.1, 4.2 | unchanged |
| | | | Tables A.1, A.2 | unchanged |
| | | | *new* | **Table A.3** |
| | | | Tables A.4, A.5, A.6 | unchanged |

## Renaming the image files

Run in order. Each target name is free by the time its command runs.

```bash
cd /f/Study/Thesis/Code/figures
git mv fig1_4_research_framework.png          fig1_3_research_framework.png
git mv fig2_3_raw_vs_preprocessed.png         fig2_2_raw_vs_preprocessed.png
git mv fig2_4_graph_construction.png          fig2_3_graph_construction.png
git mv fig2_6_pipeline.png                    fig2_4_pipeline.png
git mv fig2_8_reconstruction_inversion.png    fig2_5_reconstruction_inversion.png
git mv fig2_12_application_architecture.png   fig2_6_application_architecture.png
git mv fig2_14_event_scoring.png              fig2_7_event_scoring.png
git mv fig3_3_roc_pr_curves.png               fig3_2_roc_pr_curves.png
git mv fig3_4_detection_output.png            fig3_3_detection_output.png
git mv fig3_5_detection_latency.png           fig3_4_detection_latency.png
git mv fig3_6_operating_curve.png             fig3_5_operating_curve.png
git mv fig3_8_window_vs_event.png             fig3_6_window_vs_event.png
git mv fig3_10_false_positive_eeg.png         fig3_7_false_positive_eeg.png
git mv fig3_11_attribution_synthetic.png      fig3_8_attribution_synthetic.png
git mv fig3_13_attribution_rank_heatmap.png   fig3_9_attribution_rank_heatmap.png
git mv fig3_15_diffuseness.png                fig3_10_diffuseness.png
cd ..
ls figures/*.png | sort
```

Eighteen of the twenty-one generators write their own output filename, so a re-run would recreate the
old names beside the new ones. Find every line that needs changing:

```bash
grep -rn "fig[0-9]_[0-9]*_" src/figures/*.py | grep -i "png\|savefig\|OUT\|PATH"
```

Then update each output path to the new name in the same commit as the rename. The three hand-drawn
figures, now 1.3, 2.1 and 2.4, have no generator.
