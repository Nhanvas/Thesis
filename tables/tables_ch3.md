# Tables Pack — Chapter 3

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

This file holds Tables 3.1 through 3.12. See `tables/README.md` for what lives in the other
chapter files and for which tables are still unfilled.

---

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

<!-- docs/FIGURE_ROUND6.md §4: the table below is the rendered block from
     tables/csv/table_3_4_event_level_per_patient.md (docs/FIGURE_ROUND6.md §3), replacing the
     hand-transcribed table that previously stood here. The numbers are unchanged; this is the
     file the paragraph above asks for. -->

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
