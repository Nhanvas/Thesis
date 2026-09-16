# Thesis Outline — locked

**Unsupervised Epileptic Seizure Temporal Localization in Scalp EEG using Graph Autoencoder and
Change Point Detection**

Nguyen Quoc Trung Nhan · BEBEIU22184 · Supervisor: Assoc. Prof. Ha Thi Thanh Huong
School of Biomedical Engineering, International University, VNU-HCM

Each bullet is one paragraph in the written report. Figures and tables are named where they appear;
their specification, build status and file paths are in `FIGURES_TABLES_LIST.md`.

---

## Front matter

Title page · Approval page · Acknowledgments · Table of Contents · List of Tables · List of Figures ·
List of Abbreviations

## Abstract

- Long-term EEG review is manual and slow; supervised detectors need labelled seizures from the same patient.
- Unsupervised methods stop at window-level scoring; none couple a learned connectivity representation with
  formal change point localization.
- What was built, named specifically.
- Validated on held-out patients under an event-level scoring standard.
- Headline numbers: window tier, the reported operating point, the best achievable region.
- One finding beyond the metric: reconstruction error inverts under ictal hypersynchrony, and a
  latent-distance readout resolves it.
- One limitation: post-hoc review triage, with the false-alarm rate as its cost.
- Keywords.

---

# Chapter 1: Introduction

## 1.1 Introduction to the biomedical problem

### 1.1.1 Epilepsy and drug-resistant seizures
- Definition, global prevalence, the proportion not controlled by medication, and the treatment gap in
  low- and middle-income settings.
- Why seizure count, timing and duration drive medication changes and surgical evaluation.

### 1.1.2 Long-term EEG monitoring and manual review
- Hours to days of continuous multi-channel recording per patient, with seizures occupying a very small
  fraction of the total.
- A trained reader scrolls the whole recording to mark onset and offset; the time cost and the
  disagreement between readers.
- The task addressed here: flagging the intervals worth reading in an already-recorded file.

### 1.1.3 Seizure activity in scalp EEG
- Interictal and ictal states, the rhythmic discharge and its spread across electrodes.
  **Fig 1.1 — Stages of the EEG signal in epilepsy**
- Seizures as a change in coordination between channels rather than in single-channel amplitude alone.
  **Fig 1.2 — Connectivity during interictal and ictal windows**
- Ictal hypersynchrony: during many seizures the network becomes more regular, not less.
- Gamma-band amplitude coupling as a marker of hyperexcitable networks.

## 1.2 Analysis of current solutions

**Table 1.1 — Representative seizure detection approaches**

### 1.2.1 Patient-specific supervised detection
- High reported accuracy, and the dominant approach in this literature.
- Requires labelled seizures from the same patient, and is usually scored per short segment.

### 1.2.2 Unsupervised anomaly detection
- Autoencoder-family methods trained on non-seizure data, and the closest comparable scalp result.
- Window-level scores only, splitting often not patient-independent, and no step that converts a score
  into seizure times.

### 1.2.3 Graph neural networks on EEG
- Electrodes as nodes and coupling as edges, in supervised and self-supervised models.
- Graph density controls what such a network can learn and is rarely examined.

### 1.2.4 Change point detection
- Applications to EEG and to connectivity series, and what they offer that thresholding does not.
- Applied only to hand-designed signals.

### 1.2.5 Evaluation standards
- Three sources of non-comparability: scoring level, patient split, and supervision.
- The scoring framework adopted here, and the event-level range that patient-independent systems reach
  under it.

### 1.2.6 Channel-level explanation
- The corpus provides seizure times only; no channel-level ground truth exists.
- How other work validates channel-level claims, and the closest comparator in both task shape and
  label-free regime.

### 1.2.7 Identified gaps
- Detection: no published system combines a representation learned from seizure-free EEG with a temporal
  localization stage and event-level scoring on patient-independent data.
- Explanation: channel-level attribution for unsupervised graph models is reported as illustration rather
  than evaluated against a null model and an upper bound.

## 1.3 Constraints of label-free seizure detection

### 1.3.1 Label availability
- No seizure labels exist for the patient being analysed, and the constraint extends to threshold
  selection, where unsupervised methods commonly leak information.

### 1.3.2 Inter-patient variability
- One configuration must serve patients whose EEG changes in opposite directions during a seizure, and
  no per-patient tuning is permitted.

### 1.3.3 False alarms
- Under post-hoc review a false alarm costs reading time rather than patient safety, and this determines
  which operating points are defensible.

### 1.3.4 Absence of channel-level ground truth
- The corpus records when a seizure occurred but not which electrodes were involved, so any channel-level
  claim needs a validation route that does not depend on channel labels.

## 1.4 Proposed solutions

- Per-window connectivity graphs from phase-based and amplitude-based coupling.
- A graph autoencoder trained only on seizure-free EEG from other patients.
- Three complementary anomaly scores fused without labels.
- Change point detection converting the score series into onset and offset times.
- Label-free operating points, and event-level scoring under a published standard.
- A channel-level explanation indicating which electrodes drive each flagged interval.
- A web application running the same detection routine on a complete recording.
  **Fig 1.3 — Overview of the proposed pipeline**
- Contributions, numbered:
  1. Graph density treated as a design parameter rather than an implementation detail.
  2. Direction-agnostic change point detection resolving a structural failure of thresholding.
  3. A dual-readout autoencoder that diagnoses and corrects a reconstruction-polarity failure.
  4. One implementation shared by the offline evaluation and the deployed application.
  5. A channel-level explanation evaluated against a null model and a synthetic upper bound.

## 1.5 Project goals

- *Goal 1* — an unsupervised anomaly-scoring framework for multi-channel scalp EEG that combines spatial
  and spectral features to detect deviations from normal brain connectivity.
- *Goal 2* — temporal seizure localization by non-parametric change point detection on the fused
  anomaly score series.
- *Goal 3* — a validated channel-level explanation of the anomaly score.
- *Goal 4* — a web application demonstrating deployability under ordinary hospital computing.

## 1.6 Specifications and requirements

- The design requirements the system must satisfy, covering both the algorithm and the application.
  **Table 1.2 — Design requirements and targets**
- A paragraph walking the table row by row.
- These are design properties rather than accuracy thresholds, because the held-out data are scored once.
- Scope: scalp EEG only; one paediatric single-centre corpus; inference on a general-purpose processor;
  leave-one-patient-out and external validation not attempted; a directed-connectivity extension
  investigated separately and not adopted.

## 1.7 Timeline

- The schedule by phase, the dependencies between phases, and which phases were time-boxed.
  **Table 1.3 — Work schedule by phase** · **Fig 1.4 — Project timeline**

## 1.8 Research framework

- The stages of the study and the order in which they were carried out.
  **Fig 1.5 — Research framework**
- The discipline applied throughout: every design decision was registered with a pass criterion before it
  was measured, and decisions that failed are reported.

---

# Chapter 2: Methodology

## 2.1 Dataset

### 2.1.1 CHB-MIT scalp EEG database
- The public corpora considered and what each offers.
  **Table 2.1 — Candidate public scalp EEG seizure corpora**
- Reasons for the selection: continuous long-term recordings rather than pre-cut segments, expert onset
  and offset annotation, benchmark status, and free availability.
- Recording and cohort characteristics, and the fact that the annotation contains times only.
  **Table 2.2 — Characteristics of the selected corpus** · **Fig 2.1 — Bipolar montage used**
- Channel count and labelling differ across recordings; standardisation to the eighteen bipolar channels
  present in every file used.
- The distribution of annotated seizure durations, which bounds what a fixed analysis window can resolve.
  **Fig 2.2 — Distribution of annotated seizure durations**
- A paediatric single-centre cohort.

### 2.1.2 Data partitioning
- The three-way patient-independent split and the permitted use of each part.
  **Table 2.3 — Patient assignment to the three sets**
- The held-out patients are scored once, after every choice is frozen, with the restriction implemented
  as a check in the code.

## 2.2 Data engineering

### 2.2.1 Filtering and referencing
- Band-pass filtering, powerline notch filtering and common average referencing, with their parameters
  and the ordering requirement relative to connectivity estimation.
  **Fig 2.3 — Raw and preprocessed EEG for the same segment**

### 2.2.2 Artifact rejection
- The amplitude-based rejection rule and its purpose.
- Seizure windows are exempt, because rejecting on amplitude during a seizure removes the activity being
  detected.

### 2.2.3 Windowing and normalisation
- Window length with its justification, and the scope over which normalisation statistics are computed.
  **Table 2.4 — Preprocessing steps**

### 2.2.4 Node features
- Five spectral bands as per-electrode features, each with its physiological basis.
  **Table 2.5 — Spectral bands used as node features**

### 2.2.5 Connectivity graphs
- The phase-based and amplitude-based coupling measures, with their equations.
- Why the phase-based measure was chosen for its insensitivity to volume conduction.
- The fixed combination weight, and the ablation showing the result is insensitive to it.
  **Fig 2.4 — Construction of a connectivity graph from one window**

### 2.2.6 Decision matrix for edge sparsification
- A fixed correlation threshold against retaining a fixed proportion of the strongest edges.
  **Table 2.6 — Decision matrix for edge sparsification** ·
  **Fig 2.5 — Adjacency and graph density under two sparsification rules**
- Verdict with numbered reasons: a fixed threshold leaves graphs almost fully connected; message passing
  on such graphs collapses toward global averaging; the proportional rule produces a measured gain in the
  separation between ictal and interictal connectivity.

### 2.2.7 Gamma band coupling
- Computation of the gamma coupling score and why this band in particular.

## 2.3 Model

### 2.3.1 Graph autoencoder
- Encoder, dual decoder, the joint objective and its balancing term, and the parameter count.
  **Fig 2.6 — Graph autoencoder architecture**
- A cross-entropy objective on the adjacency scores below chance, so a joint objective with a small
  feature-reconstruction term is adopted.

### 2.3.2 Training and verification of the trained model
- Optimiser, schedule and epochs, with training restricted to interictal windows of the training patients.
  **Table 2.7 — Model and training configuration**
- The normalisation applied to the encoder input differs from the reconstruction target, and is
  replicated deliberately to match the verified model rather than corrected.
- The original training script was rebuilt, and equivalence was established against distributional
  criteria fixed in advance rather than bit-for-bit, since exact reproduction is not achievable for this
  kind of training.
- The single trained model used for every reported number was verified by regenerating the stored score
  arrays from it and comparing them against the committed originals.

### 2.3.3 Reconstruction error
- The score and the assumption it rests on.
- The measured failure in which seizures reconstruct better than background, so the score points the
  wrong way, with the mechanism that produces it. This diagnosis is what motivates the second readout.
  **Fig 2.8 — Reconstruction error in two patients**

### 2.3.4 Latent distance
- The graph-level embedding, the shrinkage-estimated covariance fitted on the patient's own seizure-free
  windows, and the resulting distance.
- Why this is label-free, and why shrinkage is required.

### 2.3.5 Score fusion
- Median-based normalisation, and why not the mean and standard deviation.
- Why pooling all windows for the normalisation statistics remains label-free at the observed prevalence.
- Equal weighting, justified by the measured flatness of the weight surface on non-test data.
  **Fig 2.7 — The three anomaly readouts from one shared encoder** · **Fig 2.9 — Ensemble weight surface**

## 2.4 Temporal localization

### 2.4.1 Decision matrix for the detection stage
- Thresholding against change point detection on the fused score.
  **Table 2.8 — Decision matrix for the detection stage**
- Verdict with numbered reasons: a threshold calibrated on seizure-free data detects only upward shifts
  and therefore fails patients whose score falls; a threshold set for an acceptable false-alarm rate
  drives sensitivity toward zero; change point detection is threshold-free, direction-agnostic, and
  answers the question of when the state changed.

### 2.4.2 Change point detection
- The optimisation the algorithm solves, the cost function, and why it suits mean shifts in a normalised
  one-dimensional signal.
- The penalty derived from a robust estimate of background variance, which makes detection deterministic.
- Search resolution, magnitude filtering and temporal smoothing, each with its label-free rule.
  **Fig 2.10 — Change point detection on an anomaly score series**

### 2.4.3 Operating point selection
- Two rules: one fixed on the validation patients and applied unchanged, and one calibrating each patient
  to a target false-alarm rate using only seizure-free data.
- The detection model remains patient-independent; what is added is a false-alarm calibration, which uses
  strictly less label information than selecting a shared point from a pooled sensitivity curve.
- Both are always reported together.

## 2.5 Channel attribution

### 2.5.1 Per-channel scores
- Scope: the analysis identifies which channels the model finds anomalous; it is neither seizure
  localization nor identification of a seizure-onset zone.
- The per-electrode error, its normalisation against the patient's own background, and the aggregation
  rule, with the physiological reason for that choice.

### 2.5.2 Reference annotation
- How the annotation was produced, given that no channel-level ground truth exists for this corpus.
- What it records, and therefore the question that any comparison against it can answer.

### 2.5.3 Synthetic validation
- Injection of known per-channel anomalies into seizure-free data, the injection grid, and the
  permutation null.
  **Fig 2.11 — Channel attribution: scoring and synthetic validation design** ·
  **Table 2.9 — Synthetic validation grid**
- The pass criteria registered before running: chance performance without injection, near-perfect
  performance with a strong injection, and monotonic behaviour in between.

## 2.6 Web application

### 2.6.1 Decision matrix for deployment
- Cloud service, on-premise server and bedside device, against weighted economic, societal, environmental
  and scalability criteria.
  **Table 2.10 — Decision matrix for deployment strategy**
- Verdict with numbered reasons: inference runs on a general-purpose processor, so no specialised
  hardware is required; the recordings are paediatric and should not leave the hospital network; no
  per-patient training means one installation serves every patient.
- This is an engineering judgement built from measured properties of the system, not a costed
  health-economics study.

### 2.6.2 System architecture
- The measurement that fixes the architecture: the archived score arrays are ordered by segment with no
  mapping back to recording time, and the offline scoring harness rebuilds a timeline from the
  annotations themselves, so replaying stored scores in a label-free product is impossible.
  **Fig 2.13 — Why stored research scores cannot be replayed on a time axis**
- The application therefore recomputes from the raw recording and keeps every window, so position follows
  by construction.
- Each component in turn, stated as what it does, which constraint fixed the choice, and how it is
  configured.
  **Fig 2.12 — Application architecture and data flow** · **Table 2.11 — Application processing stages**
- The detection routine is the same code called by the offline evaluation.

### 2.6.3 Label-free operation
- The three prohibitions the application must satisfy, and the automated tests that fail the build if any
  is violated.
- Two approved divergences: the fitting steps that use the seizure-free subset offline must instead use
  all windows, justified by the measured seizure prevalence; and the post-seizure exclusion cannot be
  reproduced without labels.
- Outputs of the application will therefore differ from offline outputs, and are not tuned to match.

## 2.7 Evaluation metrics

### 2.7.1 Event-level scoring
- The scoring framework, the event-matching rule, and the four metrics always reported together.
  **Fig 2.14 — Event-based scoring rules** · **Table 2.12 — Reported metrics and their definitions**
- Why true-negative events are undefinable, so false alarms per day replaces specificity.
- The interval methods used for proportions and for rates.

### 2.7.2 Window-level metrics
- Only rank-based measures are valid across patients, because the normalised per-patient score scales are
  unbounded; which measures exist for the held-out set and which do not.
- Reporting only rank-based measures at this tier is a deliberate deviation from the dual-reporting
  recommendation of the scoring standard, and the reason is stated.

### 2.7.3 Robustness tests
- Repeating the pipeline with independently initialised models, with the resulting spread treated as the
  threshold below which a difference is not a result.
- Removing each anomaly score in turn.
- The acceptance rule fixed in advance for any design change: it must improve the event-level result, on
  a majority of validation patients, across a majority of initialisations.

### 2.7.4 Attribution metrics
- Threshold-free metrics averaged across seizures, why they are not pooled across channel and seizure,
  and the within-seizure permutation null used as the reference.
- The control that tests whether the explanation carries seizure-specific information beyond a
  patient-level tendency.

---

# Chapter 3: Results

## 3.1 Data engineering results
- Graph density under each sparsification rule.
  **Table 3.1 — Graph density under each sparsification rule**
- The resulting change in separation between ictal and interictal connectivity, per patient.
  **Fig 3.1 — Separation between ictal and interictal connectivity, per patient**

## 3.2 Window-level results
- Discrimination overall and per patient, with the patients approaching chance identified.
  **Table 3.2 — Window-level discrimination per patient**
- The shape of the separation behind those values, and the effect of the low seizure prevalence on
  precision at every threshold.
  **Fig 3.2 — Fused anomaly score distributions per patient** ·
  **Fig 3.3 — Per-patient discrimination curves**

## 3.3 Event-level results

### 3.3.1 Detection performance
- Results at four operating points: the earlier configuration at its own balanced point, the final system
  at that same point, the final system at the point fixed on the validation patients, and the final
  system at a high-sensitivity point. All four metrics with their intervals.
  **Table 3.3 — Event-level detection results**
- The detection output on one complete recording, with the three component scores and the fused score
  shown together.
  **Fig 3.4 — Detection output on one full recording**
- Detection latency relative to annotated onset, with no pre-onset prediction claimed.
  **Fig 3.5 — Detection latency relative to annotated onset**
- What improved, and what lies within the interval and is therefore not claimed.

### 3.3.2 Sensitivity–false alarm trade-off
- The trade-off curve across operating conditions, with the reported point and the best achievable point
  marked.
  **Fig 3.6 — Sensitivity against false alarms per day**

### 3.3.3 Per-patient performance
- The four metrics for each held-out patient.
  **Table 3.4 — Event-level performance per patient** ·
  **Fig 3.7 — Event-level performance per patient**
- Patients whose signal never separates, and patients that separate at window level but not at event
  level.
  **Fig 3.8 — Window-level against event-level performance per patient**

## 3.4 Robustness across model initialisations
- The spread of results at both tiers across four independently trained models.
  **Table 3.5 — Results across four independently trained models**
- The resulting threshold below which a difference between two configurations is not a result.

## 3.5 Component ablations and design alternatives
- Every variant was registered with a pass criterion fixed in advance, and every outcome is reported. The
  final system is the reference against which all of them are measured.
  **Table 3.6 — Component ablations and design alternatives, referenced to the final system** ·
  **Fig 3.9 — Effect of each variant relative to the final system**

### 3.5.1 Removing each anomaly readout
- The effect of removing each of the three scores, including the case where removal improves the
  window-level measure while harming the event-level result.

### 3.5.2 Directed connectivity
- Results as an additional score and as a second graph relation: the patient it rescues, the patient
  harmed by the relation's own content, and the patient harmed by splitting a fixed encoder capacity
  across two relations.
  **Table 3.7 — Directed connectivity: per-patient effect**

### 3.5.3 Smoothing and gating
- Results, including one rule that succeeded with a single initialisation and failed with the others.

### 3.5.4 Ensemble and false-positive filtering
- Averaging across initialisations, which dilutes anomaly peaks, and a persistence filter for which no
  parameter value both preserved detections and reduced false alarms sufficiently.

### 3.5.5 Artifact suppression
- False alarms are associated with transient artifacts, but seizures share the same signature, so a
  per-window gate cannot separate them.
  **Fig 3.10 — A false positive detection with the concurrent EEG**

## 3.6 Channel attribution results

### 3.6.1 Synthetic validation
- Performance across injection strengths, the null result without injection, the permutation null, and
  the smallest anomaly that is reliably detected.
  **Fig 3.11 — Attribution performance against injected anomaly strength** ·
  **Table 3.8 — Synthetic validation criteria and outcomes**

### 3.6.2 Ranking stability
- Rank agreement and top-channel agreement across independently trained models.
  **Fig 3.12 — Channel ranking stability across independently trained models**
- No global channel bias; rankings typical of a patient without being identical across that patient's
  seizures.
  **Fig 3.13 — Per-seizure channel ranking**

### 3.6.3 Agreement with the reference annotation
- Results overall and per patient, with the provisional status stated, and with the patient contributing
  the largest number of annotated seizures reported both included and excluded.
  **Table 3.9 — Attribution agreement with the reference annotation** ·
  **Fig 3.14 — Attribution against the reference annotation, per patient**
- Stability across models and across the two aggregation rules; the patients contributing no annotated
  seizures; the patient scoring below chance.
- The result of the control, and the similarity of the annotations within each patient.
  **Table 3.10 — Within-patient similarity of the reference annotations**
- Whether a threshold-based operating-point table was computed, stated explicitly.

### 3.6.4 Diffuseness measure
- Behaviour on synthetic data and on the real annotations, in the direction opposite to the hypothesis.
  **Fig 3.15 — Diffuseness measure against the number of annotated channels**

## 3.7 Web application results

### 3.7.1 User interface
- Importing and processing a recording.
  **Fig 3.16 — Application: importing and processing a recording**
- Reviewing the flagged intervals.
  **Fig 3.17 — Application: reviewing flagged intervals**
- The channel-level panel.
  **Fig 3.18 — Application: channel-level panel**

### 3.7.2 Processing time and cost
- Measured processing time per hour of recording, by stage.
  **Table 3.11 — Processing time per stage, per hour of recording**
- The resulting cost position: no graphics hardware, no per-patient training, no recurring service fee.
- No detection performance metric of the application is reported, and the reason.

## 3.8 Objectives and requirements achieved
- Each of the four goals with the outcome achieved, followed by each design requirement with its outcome,
  and a paragraph on the rows not fully met.
  **Table 3.12 — Objectives and requirements achieved**

---

# Chapter 4: Discussion

## 4.1 Detection performance
- This work placed alongside published results.
  **Table 4.1 — Comparison with published work, including this study** ·
  **Fig 4.1 — Position on the sensitivity–false alarm plane**
- Which comparisons are fair, and why the frequently quoted high accuracies on this corpus describe a
  different and easier task.
- Where this result sits relative to systems scored the same way on patient-independent data.
- An earlier informal analysis suggested detection before onset; under event-level scoring the latency
  sits at or after onset, and that claim is withdrawn.

## 4.2 Patient-level failure modes
- Two failure modes separated by evidence: no separation at window level, and separation lost at the
  detection stage.
- The mechanism for the first, linking the inversion of reconstruction error to ictal hypersynchrony.
- Why these patients cap the pooled result, and why correcting them per patient would require exactly the
  labels the method is not allowed to use.

## 4.3 Window to event transfer
- The central negative finding: improvements in the representation repeatedly failed to reach the
  event-level result.
- The mechanism: the detection stage responds to sustained level shifts, not to improved ranking.
- Why a set of independent failures across several layers of the system constitutes convergent evidence
  of a ceiling rather than an incomplete search, with the count taken from the alternatives table.

## 4.4 Channel attribution
- Two contributions: a channel-level annotation over a corpus that provides only seizure times, and an
  evaluation carrying both a null model and a synthetic upper bound.
- What the numbers support: reconstruction error from a model trained only on normal connectivity carries
  channel-level information consistent with a human reader, without ever seeing a label.
- The limitation that decides the interpretation: the control scores higher, and this follows from the
  annotations rather than from the method, because a one- or two-channel label drawn from a patient's
  fixed focus is nearly constant within that patient, so averaging wins by noise reduction alone. With
  these annotations, per-seizure attribution and a patient-level channel prior cannot be distinguished.
- The patient whose annotations do vary, and where attribution accordingly exceeds the control.
- The closest published work on anomalous-channel detection, cited for scale, with the reasons a direct
  comparison is not valid.

## 4.5 Web application
- What the application demonstrates that offline evaluation cannot: the method runs end to end on a
  complete recording with no labels, within ordinary computing limits.
- The two divergences from the offline pipeline and their expected direction of effect.
- Why no performance metric of the application is reported.

## 4.6 Perspective
- Against patient-specific supervised detectors: they perform better, and cannot be applied to a newly
  admitted patient.
- Against unsupervised window-level detection: the same training assumption, but this work produces
  seizure times and is scored at event level.
- Against supervised graph models: the same representation family, the opposite label assumption.
- Against threshold-based detection: why a change point stage rescues patients a threshold structurally
  cannot.

## 4.7 Economic, social and global impacts
- Economic: reduced reading effort per recording, ordinary hardware with no accelerator, and no
  per-patient training cost, supported by the measured processing time.
  **Table 4.2 — Computational and deployment cost profile**
- Clinical and social: who benefits and through what mechanism; a flagged interval arriving with the
  channels that drove it, so the reader can judge it quickly; false alarms translating into reading time
  rather than patient harm under the review-triage framing; paediatric recordings remaining inside the
  hospital network.
- Global: patient-independence means one installation serves any patient, which matters most where
  trained EEG readers are scarce, and the infrastructure requirement is lower than for methods needing
  accelerators or per-site retraining.
- A proof of concept, not a validated clinical device.

## 4.8 Validity and reliability
- Scoring follows a published framework using its reference implementation, and every event metric is
  reported with an interval.
- The whole pipeline was repeated with independently initialised models, and the resulting spread is used
  as the threshold below which a difference is not treated as a result.
- One design change passed on a single initialisation and failed on the others; the acceptance rule fixed
  in advance caught it before the held-out set was spent.
- The attribution machinery was validated against synthetic ground truth with a clean null before any
  real annotation was scored.
- The trained model behind every reported number was verified by regenerating the committed score arrays
  from it.
- Weights and operating points in an earlier configuration were selected on the held-out patients; they
  were re-derived on non-test data under a rule fixed in advance, and the corrected result, which is
  lower, is the one reported.
- A per-patient correction for one patient was rejected because determining its direction required that
  patient's own seizure labels.
- The earlier temporal branch could not be reproduced from its retained outputs and was removed rather
  than repaired.

## 4.9 Limitations
- The false-alarm rate is structural to label-free anomaly detection and is defensible only under the
  review-triage framing.
- Specificity is not reportable at event level.
- Two patients are limited by the representation itself.
- Window-level gains do not transfer through the detection stage.
- Short seizures are disadvantaged by a fixed analysis window.
- The channel explanation is not localization, and its reference annotation is narrower than intended and
  provisional.
- One corpus, one centre, a paediatric cohort, with no external validation and no leave-one-patient-out
  protocol.
- The training procedure was reconstructed and validated distributionally rather than reproduced exactly.
- Three planned event-tier analyses were not re-run before submission, named explicitly.

## 4.10 Future development
- Increasing the capacity of the representation, the direction the evidence points to.
- External validation on an independent corpus, and a leave-one-patient-out protocol.
- Channel annotations recording every involved electrode rather than the leading one.
- A diffuseness measure that behaves monotonically with the number of involved channels.
- Signal variants scoped but not evaluated.
- The three outstanding event-tier analyses.

---

# Chapter 5: Conclusion

- What was built.
- The result quantified against each of the objectives, with the false-alarm rate stated in the same
  sentence as the detection result.
- The principal limitation, as the boundary of the claim.
- Secondary contributions: the validated channel explanation, the documented programme of falsified
  design alternatives, the channel-level annotation, and the working application.
- Future work, in one sentence.
- Responsibility: paediatric data handling, the provisional status of the explanation layer, the fact
  that this is a proof of concept rather than a validated device, and the division of responsibility
  between an automated flagging tool and the clinician who reads the recording.
- A closing sentence returning to the reading burden described at the opening of Chapter 1.

---

# References

# Appendices

- **Table A.1** — Corpus metadata for all subjects
- **Table A.2** — Channel annotation for every seizure in the held-out set
- **Table A.3** — Full per-patient results and the complete parameter grid
- **Table A.4** — Concentration of top-ranked channels against the random null
- **Table A.5** — Software and libraries used, with their role
- **Table A.6** — Pre-registration index
- **Table A.7** — Top three attributed channels for each held-out seizure
- **Fig A.1** — Application interface flow
