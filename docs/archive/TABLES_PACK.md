# Tables Pack

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

## Status of each table

| Ready to drop in | Needs one emit run | Needs an input only Boti has |
|---|---|---|
| 1.1 · 2.2 · 2.3 · 2.4 · 2.5 · 2.6 · 2.7 · 2.9 · 2.12 · 3.1 · 3.2 · 3.3 · 3.5 · 3.6 · 3.7 · 3.8 · 3.9 · 3.10 · 4.1 · A.4 · A.5 · A.6 | 3.4 · A.1 · A.2 · A.3 | 1.2 · 1.3 · 2.1 · 2.8 · 2.10 · 2.11 · 3.11 · 3.12 · 4.2 |

---

# Chapter 2

## Table 2.2 — Characteristics of the selected corpus

| Property | Value |
|---|---|
| Subjects | 23 |
| Recordings | 664 |
| Total recorded time | 961.6 h |
| Annotated seizures | 182 |
| Channels analysed | 18 bipolar derivations |
| Sampling rate | 256 Hz |
| Annotation content | Seizure start and end time per recording; no channel-level annotation |
| Seizure duration, held-out subset | 6 s minimum, 45 s median, 51.9 s mean, 205 s maximum |

Every corpus figure comes from this project's own parse of the 23 recording summary files, never
from a corpus description quoted out of a cited paper. Published descriptions of this corpus give
23 subjects in some places and 24 in others.

*Source: `docs/VERIFIED_NUMBERS.md` Part 3. Recording count is the sum of the per-set file counts
(342 + 91 + 231).*

## Table 2.3 — Patient assignment to the three sets

| Set | Patients | Count | Recordings | Recorded hours | Seizures |
|---|---|---|---|---|---|
| Training | chb01, chb02, chb04, chb05, chb07, chb08, chb09, chb12, chb19, chb20, chb21, chb23 | 12 | 342 | 566.43 | 93 |
| Validation | chb10, chb11, chb22 | 3 | 91 | 115.82 | 13 |
| Held-out | chb03, chb06, chb13, chb14, chb15, chb16, chb17, chb18 | 8 | 231 | 279.39 | 76 |

Assignment is by patient, so no recording from a held-out patient contributes to training or to
any tuning decision. The held-out set was scored once.

**Writer's trap.** The split file's first key holds fifteen patients because it includes the three
validation patients. The training set is **twelve**. A chapter reporting fifteen has read the
wrong key.

*Source: `data/splits/split_main.json` (`inner_train` / `val` / `test`) and
`docs/VERIFIED_NUMBERS.md` Parts 2.3 and 3.*

## Table 2.4 — Preprocessing steps

| # | Step | Parameters | Rationale |
|---|---|---|---|
| 1 | Band-pass filter | Fourth-order Butterworth, 0.5–60 Hz, zero-phase, 3 s padding each side | Removes drift below the physiological range and content above the analysis band without phase distortion |
| 2 | Notch filter | IIR notch at 60 Hz, quality factor 30, zero-phase | Suppresses mains interference, which falls inside the retained band |
| 3 | Segmentation | 4 s non-overlapping windows, 1024 samples at 256 Hz | Fixes the analysis unit; non-overlapping windows keep successive windows statistically independent |
| 4 | Artifact rejection | Window discarded if any channel exceeds 5 standard deviations of that channel's interictal distribution | Removes gross movement and electrode artifacts from the background set |
| 5 | Post-seizure exclusion | 4 h after each annotated seizure end excluded from the background set | Prevents post-ictal activity from being treated as normal background |
| 6 | Normalisation | Per-patient, per-channel z-score | Removes between-patient amplitude differences so one model serves every patient |

Two properties of this stage matter later. Artifact rejection is applied to the background set
only; seizure windows are deliberately kept, because rejecting them would remove exactly the
activity the system must detect. And because rejection drops windows, the retained background
windows no longer sit at their original positions in recording time.

**Writer's trap.** Step 5 governs which windows enter the background set. It is **not** applied to
the false-alarm denominator, which is total recorded time minus seizure time. A sentence saying a
post-seizure buffer was excluded from the false-alarm rate would be wrong.

*Source: `src/dataprep/preprocessing.py` lines 8, 11, 27–28, 52–65, 78–81. Denominator
reconciliation in `docs/VERIFIED_NUMBERS.md` Part 3.*

## Table 2.5 — Spectral bands used as node features

| Band | Range | Physiological basis |
|---|---|---|
| Delta | 0.5–4 Hz | Deep sleep and pathological slowing; rises in post-ictal suppression |
| Theta | 4–8 Hz | Drowsiness and focal slowing; a common interictal correlate of focal disturbance |
| Alpha | 8–13 Hz | Posterior resting rhythm; attenuates when cortex is activated |
| Beta | 13–30 Hz | Alert cortical activity and the fast component of some seizure onsets |
| Gamma | 30–60 Hz | High-frequency activity associated with local synchronisation during seizures |

Each band power is computed by Welch's method with a 2 s segment and 1 s overlap, then
log-transformed, giving five values per channel per window.

*Source: `src/dataprep/feature_extraction.py` lines 14–19, 32, 37–38.*

## Table 2.6 — Decision matrix for edge sparsification

| Criterion | Fixed correlation threshold | Retain the strongest 20 % of edges |
|---|---|---|
| Density across patients | 0.921 to 0.973, varies by patient | 0.196, identical for every patient |
| Density across states | 0.921–0.973 interictal, 0.949–0.974 ictal | 0.196 in both states |
| Effect on message passing | Graph is almost complete; neighbourhood averaging approaches a global mean and topology carries little information | Sparse neighbourhoods preserve topological structure |
| Comparability between patients | Absent — the same threshold yields a different graph density for each patient | Present by construction |
| Separation between ictal and interictal connectivity, scale-comparable measures | Reference | Higher on 8 of 8 held-out patients under both relative Frobenius distance and cosine distance |
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

## Table 2.7 — Model and training configuration

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

## Table 2.9 — Synthetic validation grid

| Dimension | Values |
|---|---|
| Injection strength (multiplier on the affected channels) | 1.00, 1.25, 1.50, 2.00, 3.00 |
| Number of injected channels | 1, 2, 4, 8, 12 |
| Replicates per cell | 200 |
| Cells per panel | 25 |
| Panels | Validation and held-out, 50 cells in total |
| Pseudo-seizure construction | A contiguous interictal block whose length is drawn from the distribution of the 76 real seizure durations |
| Baseline | Robust standardisation computed on interictal data excluding the injected block |
| Aggregation | 95th percentile over the windows of the block |
| Random seed | 42 |

The injected channels are known exactly, so this grid has ground truth that the corpus itself does
not provide. It tests the scoring machinery, not the clinical claim.

*Source: `docs/ATTRIBUTION_SPEC.md` §9.1; `results/attribution_v6/synthetic_sanity.csv`.*

## Table 2.12 — Reported metrics and their definitions

| Tier | Metric | Definition |
|---|---|---|
| Window | Discrimination (AUROC) | Area under the receiver-operating curve over all windows of one patient; reported as the unweighted mean across patients |
| Window | Precision–recall area (AUPRC) | Area under the precision–recall curve for one patient; reported as the unweighted mean across patients |
| Event | Sensitivity | Annotated seizures with at least one overlapping detected interval, divided by the number of annotated seizures |
| Event | Precision | Detected intervals overlapping an annotated seizure, divided by the number of detected intervals |
| Event | F1 | Harmonic mean of event sensitivity and event precision |
| Event | False alarms per day | Detected intervals overlapping no annotated seizure, divided by the scored recording time, expressed per 24 h |

Three conventions travel with this table. Matching is by any overlap, with a tolerance of 30 s
before an annotated onset and 60 s after an annotated offset; detections closer than 90 s are
merged. Specificity is not reported, because a true-negative event cannot be defined once the
timeline is expressed as events rather than samples; false alarms per day replaces it, and this is
a structural property of event-level scoring rather than a choice. And only the across-patient
means of the two window metrics are comparable between patients: a threshold-dependent pooled
window metric is not, because the per-patient score scales are unbounded.

F1 carries no interval because it is a function of the two quantities above it. No detection
metric in this report carries an interval.

*Source: `src/szcore_eval.py`; `src/evaluation_protocol.py`; scoring convention from the
event-scoring framework paper; `docs/LOCKED_DOCS_ADDENDUM.md` §2.1.*

---

# Chapter 3

## Table 3.1 — Graph density under each sparsification rule

| Rule | Interictal density | Ictal density | Edges retained of 153 |
|---|---|---|---|
| Fixed correlation threshold, 0.05 | 0.921 to 0.973 | 0.949 to 0.974 | 141 to 149 |
| Retain the strongest 20 % of edges | 0.196 for every patient | 0.196 for every patient | 30 |

The proportional rule holds density constant across every patient and both states. The fixed
threshold leaves the graph almost complete, and its density varies from patient to patient.

**Exception.** Under the proportional rule chb17 gives an interictal density of 0.224 rather than
0.196, and the computation raised a divide-by-zero warning for that patient, indicating a channel
with zero variance in its mean adjacency. One sentence of explanation belongs wherever this
appears.

*Source: `results/diagnostics/density_frobenius_v2/`, regenerated at the committed stride;
`docs/VERIFIED_NUMBERS.md` Part 4.1. Edge counts follow from the density and the 153 undirected
pairs of 18 channels.*

## Table 3.2 — Window-level discrimination per patient

| Patient | Discrimination |
|---|---|
| chb03 | 0.964 |
| chb06 | 0.501 |
| chb13 | 0.822 |
| chb14 | 0.698 |
| chb15 | 0.879 |
| chb16 | 0.876 |
| chb17 | 0.782 |
| chb18 | 0.920 |
| **Across patients** | **0.805** |

chb06 sits at chance; chb14 is the second weakest. The across-patient value is the unweighted mean,
not a pooled value, for the reason given with Table 2.12.

*Source: `results/phaseB/tier2/ens_test_tf/rlg/window_auroc_seed42.json`;
`docs/VERIFIED_NUMBERS.md` Part 1.2.*

## Table 3.3 — Event-level detection results

| Configuration | Operating point | Sensitivity | Precision | F1 | False alarms / day |
|---|---|---|---|---|---|
| Earlier configuration, at its own balanced point | m70/p0.5 | 0.632 | 0.097 | 0.168 | 38.6 |
| Final system, at that same point | m70/p0.5 | 0.645 | 0.099 | 0.172 | 38.4 |
| **Final system, at the validation-derived point** | **m50/p2.0** | **0.618** | **0.129** | **0.213** | **27.4** |
| Final system, at a high-sensitivity point | m50/p0.5 | 0.711 | 0.068 | 0.123 | 64.4 |
| Final system, at the low false-alarm budget | m75/p10.0 | 0.342 | 0.382 | 0.361 | 3.6 |

Row 3 is the reported result of this system: its threshold was fixed on the validation patients
before any held-out patient was scored. Row 5 is included because every design alternative in
Table 3.6 was gated at that false-alarm budget.

The best point available on the trade-off curve reaches F1 0.426 at 4.9 false alarms per day, with
sensitivity 0.474 and precision 0.387. It was located by scanning the grid after the held-out set
had been scored, and is reported as a property of the curve, never as the system's result.

**Operating-point notation.** `m` is the change-point magnitude percentile and `p` the penalty
multiplier. If the chapter prefers plain language, define both once and then use the words; do not
mix the two forms.

*Source: `results/phaseB/tier2/rlg_test/final_eval_seed42.csv`, cross-checked against
`ONESHOT_rlg_vs_s0.csv` and `FINAL_report.csv`, and reproduced end to end from the ensemble arrays;
`docs/VERIFIED_NUMBERS.md` Part 1.1; `docs/LOCKED_DOCS_ADDENDUM.md` §2.2.*

## Table 3.4 — Event-level performance per patient

**Values below are transcribed from the figure script's own printed self-check and must be
regenerated as a file before use** — see the emit task in the figure brief. They are given here so
the emitted file can be checked against them rather than accepted on trust.

| Patient | Seizures | Sensitivity | Precision | F1 | False alarms / day |
|---|---|---|---|---|---|
| chb03 | 7 | 1.000 | 0.152 | 0.264 | 24.7 |
| chb06 | 10 | 0.000 | 0.000 | undefined | 19.4 |
| chb13 | 12 | 0.750 | 0.220 | 0.340 | 23.4 |
| chb14 | 8 | 0.375 | 0.049 | 0.087 | 53.6 |
| chb15 | 20 | 0.900 | 0.286 | 0.434 | 27.4 |
| chb16 | 10 | 0.200 | 0.105 | 0.138 | 21.5 |
| chb17 | 3 | 1.000 | 0.115 | 0.207 | 26.4 |
| chb18 | 6 | 0.833 | 0.091 | 0.164 | 33.8 |

At the reported operating point no seizure of chb06 is detected, so its F1 is **undefined**, not
zero. Sensitivity and precision are zero; the harmonic mean of two zeros has no value. Write it
that way in the text and in the figure caption.

*Source: `results/phaseB/tier2/rlg_test/final_eval_seed42.csv` at m50/p2.0, printed by
`src/figures/plot_event_level.py`. Seizure counts from `docs/VERIFIED_NUMBERS.md` Part 3.*

## Table 3.5 — Results across four independently trained models

Validation patients, 13 seizures, at the low false-alarm budget.

| Model | Window discrimination | Event sensitivity | Event precision | Event F1 | False alarms / day |
|---|---|---|---|---|---|
| Seed 42 | 0.928 | 0.846 | 0.333 | 0.478 | 4.6 |
| Seed 1 | 0.929 | 1.000 | 0.361 | 0.531 | 4.8 |
| Seed 2 | 0.925 | 0.923 | 0.333 | 0.490 | 5.0 |
| Seed 3 | 0.932 | 0.846 | 0.306 | 0.449 | 5.2 |
| **Mean** | **0.929** | — | — | **0.487** | — |
| **Spread (standard deviation)** | **0.002** | — | — | **0.034** | — |

These two spreads are the noise floors of this study. A change smaller than 0.002 at the window
tier, or smaller than 0.034 at the event tier, is not distinguishable from the effect of
reinitialising the same model.

The event spread is wide because it is measured on three patients and thirteen seizures. That is a
property of the validation set, and stating it is what makes the threshold meaningful rather than
arbitrary.

*Source: window values from `results/phaseB/tier2/ens_val_tf/rlg/window_auroc_seed42.json` and
`results/phaseC/reencode/seed{1,2,3}/rlg/window_auroc_seed{N}.json`; event values from
`results/phaseB/tier2/alternatives/`; `docs/VERIFIED_NUMBERS.md` Parts 1.3 and 6.4. The event
spread is the sample standard deviation over 0.4783, 0.5306, 0.4898 and 0.4490, which is 0.0338.*

## Table 3.6 — Component ablations and design alternatives

All rows are measured on the three validation patients and thirteen seizures, at the low
false-alarm budget, with the final system as the reference. The held-out set was not used for any
of them.

| Variant | Type | Layer changed | Sensitivity | Precision | F1 | FP / day | Δ F1 | Outcome |
|---|---|---|---|---|---|---|---|---|
| Final system | reference | — | 0.846 | 0.333 | 0.478 | 4.6 | 0.000 | reference |
| Remove the reconstruction readout | ablation | ensemble | 0.923 | 0.333 | 0.490 | 5.0 | +0.012 | within the noise band |
| Remove the latent readout | ablation | ensemble | 0.692 | 0.257 | 0.375 | 5.4 | −0.103 | clearly worse |
| Directed connectivity, at the score level | alternative | decision | 0.769 | 0.312 | 0.444 | 4.6 | −0.034 | on the boundary of the noise band |
| Directed connectivity, at the representation level | alternative | representation | — | — | — | — | — | evaluated at the window tier only; see Table 3.7 |
| Alternative smoothing, median over 9 windows | alternative | decision | 0.615 | 0.250 | 0.356 | 5.0 | −0.123 | clearly worse |
| Alternative smoothing, median over 15 windows | alternative | decision | 0.692 | 0.281 | 0.400 | 4.8 | −0.078 | clearly worse |
| Onset-slope change-point filtering | alternative | decision | 0.846 | 0.324 | 0.468 | 4.8 | −0.010 | within the noise band |
| Artifact gate, isolated spikes only | alternative | signal | 0.923 | 0.324 | 0.480 | 5.2 | +0.002 | within the noise band |
| Artifact gate, every window | alternative | signal | 0.000 | 0.000 | undefined | 4.6 | undefined | no detections produced |

**Three readings that must not be got wrong.**

Removing the reconstruction readout gains 0.012, which is **below** the 0.034 spread across
independently trained models and is therefore a tie, not an improvement. On the held-out set at
the matched cell the same variant loses outright, F1 0.162 against 0.172, and its sensitivity falls
from 0.645 to 0.579.

Directed connectivity at −0.0339 sits on the **boundary** of the 0.0338 band, outside it by one
ten-thousandth. It is not a clean rejection and must not be written as one. That reading fits the
conclusion already reached about this lever better than a decisive failure would.

The per-window artifact gate produces no detections at all, because it suppresses the great
majority of seizure windows. This is a real outcome with a known mechanism, not a missing value.

**Count of alternatives.** Seven were registered; **six were measured**. The seventh, additional
per-channel time-domain features, was never built and belongs in future work, not in the count of
falsified alternatives.

*Source: `results/phaseB/tier2/alternatives/alternatives_vs_incumbent.csv`;
`docs/VERIFIED_NUMBERS.md` Part 6.3 and 6.6; `docs/LOCKED_DOCS_ADDENDUM.md` §1.4 and §2.5. The
held-out comparison for the reconstruction ablation is from `ONESHOT_rlg_vs_s0.csv`.*

## Table 3.7 — Directed connectivity: per-patient effect at the representation level

Validation patients, window tier.

| Patient | Latent readout, final system | Latent readout, with the added relation | Change |
|---|---|---|---|
| chb10 | 0.816 | 0.757 | −0.059 |
| chb11 | 0.641 | 0.693 | +0.052 |
| chb22 | 0.736 | 0.873 | **+0.137** |
| Full system, across patients | 0.928 | 0.909 | −0.019 |

The added relation is not noise: on its own discriminative check it reaches 0.710, 0.674 and 0.888
against a null near 0.500. It carries signal on every patient and still costs accuracy overall.
One patient is rescued and one is harmed, and the loss on the second exceeds the gain on the first
when the readouts are combined. Of nine pre-registered acceptance checks, four passed.

*Source: `results/phaseC/c4full/{stage0_verdict_seed42.json, stage0_lg_variant_seed42.json,
rlg_lg_diagnostic_seed42.json}`; `docs/VERIFIED_NUMBERS.md` Part 6.4b.*

## Table 3.8 — Synthetic validation criteria and outcomes

| Criterion | Expected | Observed | Outcome |
|---|---|---|---|
| Negative control: no injection, one channel marked | Discrimination between 0.45 and 0.55 | 0.491 | pass |
| Upper bound: strongest injection, one channel | Discrimination at least 0.95 | 0.982 | pass |
| Monotonicity in injection strength, at every number of injected channels | Non-decreasing | Holds at every level | pass |
| Diffuseness separates many injected channels from one | Diffuseness higher for eighteen channels than for one, p < 0.05 | 0.976 against 0.964, p = 8.9×10⁻¹¹ | pass |
| Permutation null across all 50 cells | Centred on 0.50 | Mean stayed within 0.499 to 0.501 | pass |
| Detection threshold | — | Discrimination reaches 0.696 at a 25 % increase | — |

The fourth criterion was reformulated once, after the version originally registered failed. The
failure and the reformulation are both reported; the criterion was rewritten, the measurement was
not.

*Source: `results/attribution_v6/synthetic_sanity.csv` and `synthetic_spread.csv`;
`docs/ATTRIBUTION_SPEC.md` §9.1; `docs/VERIFIED_NUMBERS.md` Part 7.2.*

## Table 3.9 — Attribution agreement with the draft annotation

**Provisional throughout.** The annotation these rows are scored against was generated
automatically and has not been reviewed by a clinician. Every row states a preliminary agreement
against a draft annotation, not a clinical validation.

| Analysis panel | Seizures | Agreement | Interval | Precision–recall area | Patient-constant control | Difference | Permutation p |
|---|---|---|---|---|---|---|---|
| All annotated seizures (provisional) | 36 | 0.650 | [0.566, 0.739] | 0.310 | 0.776 | −0.126 | 0.001 |
| Excluding the dominant patient (provisional) | 16 | 0.627 | [0.491, 0.755] | 0.343 | 0.625 | +0.002 | 0.038 |
| Dominant patient only (provisional) | 20 | 0.668 | [0.537, 0.793] | 0.283 | 0.897 | −0.229 | 0.004 |
| Across four models (provisional) | 36 | 0.660 / 0.649 / 0.652 | — | — | — | — | — |
| Alternative aggregation (provisional) | 36 | 0.673 | — | — | — | — | — |

Prevalence of annotated channels is 0.073, so the precision–recall area of 0.310 is about 4.2 times
the rate expected by chance.

The control is a single channel set held constant within each patient. It scores higher than the
per-seizure attribution. The correct reading is not that attribution failed: a one-or-two channel
annotation drawn from a patient's fixed focus is almost forced to be constant within that patient,
so the constant control wins by averaging alone. With these annotations, per-seizure attribution
and a patient-level channel prior cannot be told apart.

*Source: `results/attribution_v6/attribution_summary.csv`; `docs/VERIFIED_NUMBERS.md` Part 7.3;
wording constraint from `docs/LOCKED_DOCS_ADDENDUM.md` §1.5.*

## Table 3.10 — Within-patient similarity of the draft annotations

| Patient | Annotated seizures | Distinct channel sets | Mean similarity |
|---|---|---|---|
| chb03 | 6 | 2 | 0.833 |
| chb14 | 3 | 2 | 0.667 |
| chb15 | 20 | 2 | 0.905 |
| chb17 | 3 | 1 | 1.000 |
| chb18 | 3 | 3 | 0.167 |
| **Pooled over all 214 seizure pairs** | 35 | — | **0.888** |

The pooled value is the mean over all within-patient seizure pairs. It is **not** the mean over
patients, which is 0.714, nor the seizure-weighted mean, which is 0.817. State which one is meant
wherever it appears.

chb18 is the one patient whose annotations vary, and it is also the one patient where attribution
exceeds its control. Those two facts are the same fact.

*Source: `results/attribution_v6/label_diversity.csv`; `docs/VERIFIED_NUMBERS.md` Part 7.4.*

---

# Appendices

## Table A.4 — Concentration of the top-ranked channel against a random null

| Patient | Seizures | Distinct top-ranked channels | Largest share | Null 95th percentile | Verdict |
|---|---|---|---|---|---|
| chb03 | 7 | 5 | 0.429 | 0.429 | within the null |
| chb06 | 10 | 7 | 0.300 | 0.300 | within the null |
| chb13 | 12 | 6 | 0.417 | 0.333 | **concentrated** |
| chb14 | 8 | 5 | 0.250 | 0.375 | within the null |
| chb15 | 20 | 9 | 0.500 | 0.250 | **concentrated** |
| chb16 | 10 | 4 | 0.500 | 0.300 | **concentrated** |
| chb17 | 3 | 3 | 0.333 | 0.667 | within the null |
| chb18 | 6 | 5 | 0.333 | 0.500 | within the null |

Three of eight patients repeat their top-ranked channel more often than chance allows. This is
independent evidence for the limitation the annotation comparison raises: within a patient, the
method behaves partly as a patient-level channel prior rather than a per-seizure one. It
strengthens that limitation rather than weakening the method.

*Source: `results/attribution_v6/attribution_diagnostics.csv`; `docs/VERIFIED_NUMBERS.md`
Part 6.4c.*

## Table A.5 — Software and libraries

| Package | Version | Role |
|---|---|---|
| Python | 3.11 | Runtime |
| numpy | 2.4.4 | Array computation throughout |
| scipy | 1.17.1 | Filtering, spectral estimation, statistical tests |
| pandas | 3.0.3 | Result tables and grid files |
| mne | 1.12.1 | Reading the recording files |
| torch | 2.12.0 | Model definition and training |
| torch-geometric | 2.7.0 | Graph convolution layers |
| scikit-learn | 1.8.0 | Shrinkage covariance estimation and discrimination measures |
| ruptures | 1.1.10 | Change-point detection |
| timescoring | 0.0.7 | Event-level scoring |
| matplotlib | 3.10.8 | Figures |
| networkx | 3.6.1 | Graph handling |
| tqdm | 4.67.3 | Progress reporting |

The remaining entries of the environment snapshot are transitive dependencies and are not listed.

*Source: `docs/requirements_snapshot.txt`. The Python version is stated by the interpreter path in
the session log and should be confirmed with `python --version` before the table is final.*

## Table A.6 — Pre-registration index

| # | Registered question | Gates |
|---|---|---|
| 01 | Retraining the graph autoencoder jointly on adjacency and node features | The model configuration in Table 2.7 and every result derived from it |
| 02 | A recurrent temporal readout | Withdrawn; the branch was dropped and replaced, and does not appear in the reported system |
| 03 | Derivation of the ensemble weights | The weighting discussion in Chapter 2 |
| 04 | A label-free per-patient false-alarm budget as the operating rule | The operating points in Table 3.3 and every gated comparison in Table 3.6 |
| 05 | Validation-derived operating points | The reported operating point, row 3 of Table 3.3 |
| 06 | A balanced operating point | Row 1 and row 2 of Table 3.3 |
| 07 | Per-patient rather than pooled budgeting | The operating rule applied in Table 3.4 |
| 08 | A window-level threshold as an alternative decision rule | Reported as a considered and rejected decision rule |
| 09 | A minimum event duration | The interval construction in Chapter 2 |
| — | Replacement of the recurrent readout by the latent readout | The three-readout design and its ablation, Table 3.6 |
| — | A directed-connectivity probe | Table 3.7 and the corresponding row of Table 3.6 |

Each entry fixed its hypothesis, its falsification criterion and its stopping condition before the
measurement was made. Where a criterion failed, the failure is reported and the construction was
revised; no criterion was revised after its result was seen, with the single exception recorded
with Table 3.8, where the criterion was reformulated and the reformulation is stated.

*Source: `docs/prereg/PREREG_01` through `PREREG_09`, `docs/PREREG_TIER2_amendment_A1.md`,
`docs/PREREG_TIER2_latent_ensemble.md`, `docs/PREREG_C0_connectivity_probe.md`. Titles above are
paraphrased for the reader; the appendix should give each document's own title.*

---

# Chapter 4

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

---

# Tables not filled here, and why

| Table | What is missing |
|---|---|
| 1.2 | Design requirements and targets. Comes from the outline's requirements section, not from a result file. |
| 1.3, and the timeline figure | Calendar dates. Boti supplies. |
| 2.1 | Candidate corpora. Every cell needs the corpus's own documentation and a citation; none of it is in this repository. |
| 2.8, 2.10 | Decision matrices for the detection stage and the deployment strategy. Qualitative; the criteria come from the outline. |
| 2.11 | Application processing stages. Comes from the application specification, which is not attached to this project. |
| 3.11, 3.12 | Processing time per stage waits on the application build. The objectives table is written last, from the finished Chapters 2 and 3. |
| 4.2 | Cost profile. One measured value exists — 16.9 ms per window on the development processor, about 15 s per hour of recording — recorded in the application specification. The rest is not measured and must be marked so. |
| A.1, A.2, A.3 | Emitted from committed files by the script in the figure brief. |
