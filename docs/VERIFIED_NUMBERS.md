# Verified Numbers — audit record

Every value below was read from a file or recomputed from one during the verification session
of 2026-09-06. Nothing here comes from a planning document, a summary, or memory. Where a
value could not be traced, that is stated.

**How to use this.** When reviewing a chapter, a number that appears here has already been
traced and can be checked against this table directly. A number that does *not* appear here
still has to be traced to its own source file before it can be accepted.

`docs/RESULTS_OF_RECORD_phaseB.md` remains the authority. Where this file and the results of
record disagree, the disagreement is written out explicitly below rather than resolved
silently.

---

# Part 1 · Detection results

## 1.1 Operating points, held-out set

Source: `results/phaseB/tier2/rlg_test/final_eval_seed42.csv`, pooled independently across the
eight subjects. Cross-checked against `results/phaseB/tier2/ONESHOT_rlg_vs_s0.csv` and
`results/phaseB/tier2/FINAL_report.csv`, and reproduced end to end from the ensemble arrays by
`src/phaseB/extract_latency_rlg.py` (all four points matched exactly).

| Operating point | Cell | Sensitivity | Precision | F1 | FP/day | TP | FP |
|---|---|---|---|---|---|---|---|
| Earlier configuration, its own balanced point | m70/p0.5 | 0.632 | 0.097 | 0.168 | 38.6 | 48 | 447 |
| Final system, same cell | m70/p0.5 | 0.645 | 0.099 | 0.172 | 38.4 | 49 | 445 |
| **Final system, validation-derived — the headline** | **m50/p2.0** | **0.618** | **0.129** | **0.213** | **27.4** | **47** | **318** |
| Final system, high sensitivity | m50/p0.5 | 0.711 | 0.068 | 0.123 | 64.4 | 54 | 746 |
| Final system, low false-alarm budget | m75/p10.0 | 0.342 | 0.382 | 0.361 | 3.6 | 26 | 42 |
| Earlier configuration, its own high-sensitivity point | m55/p0.3 | 0.776 | 0.065 | 0.121 | 72.7 | 59 | 843 |
| Final system, same cell | m55/p0.3 | 0.763 | 0.065 | 0.120 | 72.0 | 58 | 835 |

Held-out totals: **8 subjects, 76 seizures, 278.22 interictal hours**, grid of 8 magnitude
percentiles x 6 penalty multipliers = 48 cells per subject, 384 rows, seed 42.

**Best point on the trade-off curve** (m80/p5.0): sensitivity 0.474, precision 0.387, F1 0.426,
4.9 FP/day. Second best (m75/p5.0): F1 0.406 at 6.3 FP/day. Located by scanning the committed
grid. This is a property of the curve, not a selected operating point, and must never be
presented as the system's result — the cell was found by looking at the held-out data.

## 1.2 Window tier, held-out set

Source: `results/phaseB/tier2/ens_test_tf/rlg/window_auroc_seed42.json`, and the constant
`window_auroc` column of the grid file. Macro recomputed as the unweighted mean.

| chb03 | chb06 | chb13 | chb14 | chb15 | chb16 | chb17 | chb18 | macro |
|---|---|---|---|---|---|---|---|---|
| 0.9643 | 0.5011 | 0.8223 | 0.6982 | 0.8785 | 0.8763 | 0.7815 | 0.9201 | **0.8053** |

Reported to three decimals: **0.805**. chb06 sits at chance; chb14 is the second weakest.

## 1.3 Window tier, validation set

Source: `results/phaseB/tier2/ens_val_tf/rlg/window_auroc_seed42.json` and
`results/phaseC/reencode/seed{1,2,3}/rlg/window_auroc_seed{N}.json`.

| Model | chb10 | chb11 | chb22 | macro |
|---|---|---|---|---|
| seed 42 | 0.8500 | 0.9564 | 0.9786 | 0.9283 |
| seed 1 | 0.8523 | 0.9601 | 0.9740 | 0.9288 |
| seed 2 | 0.8388 | 0.9620 | 0.9754 | 0.9254 |
| seed 3 | 0.8544 | 0.9601 | 0.9799 | 0.9315 |

Mean 0.9285, SD 0.0025. The results of record quote **0.929 +/- 0.002**; consistent.

## 1.4 Detection latency

Source: `results/phaseB/tier2/latency/latency_summary.csv`, produced by
`src/phaseB/extract_latency_rlg.py` after the reproduction check passed at all four points.

| Operating point | Matched | Pooled mean latency | Subjects with negative mean | Subjects with no match |
|---|---|---|---|---|
| Headline (m50/p2.0) | 48 / 76 | +5.1 s | chb03, chb13, chb18 | chb06 |
| Matched cell (m70/p0.5) | 50 / 76 | +9.7 s | chb03, chb13 | chb06 |
| High sensitivity (m50/p0.5) | 55 / 76 | +10.5 s | chb03, chb13 | chb06 |
| Earlier high-sensitivity cell (m55/p0.3) | 59 / 76 | +7.1 s | chb03, chb06, chb13 | — |

**Two things must travel with these numbers.**

1. The latency matcher is a separate implementation from the scoring framework's own matcher.
   It allows a detected interval starting up to 30 s before the annotation, and ending up to
   60 s after, to count as matched. Its match count exceeds the true-positive count by exactly
   one at every operating point (48 against 47, 50 against 49, 55 against 54, 59 against 58).
   Any figure or table built on it states which count it uses.
2. Negative latency reflects that 30 s tolerance and the 4 s window quantisation. It is not
   evidence of detection before onset and must not be written as such.

---

# Part 2 · Model and training

## 2.1 Parameter count and layer shapes

Source: `torch.load` on `data/models_retrain/gae_joint_seed42.pt`, summed over the state dict.

**Total: 3,285 parameters.**

| Tensor | Shape | Parameters |
|---|---|---|
| encoder.conv1.lin.weight | (64, 23) | 1,472 |
| encoder.conv1.bias | (64,) | 64 |
| encoder.conv2.lin.weight | (16, 64) | 1,024 |
| encoder.conv2.bias | (16,) | 16 |
| x_decoder.net.0.weight | (32, 16) | 512 |
| x_decoder.net.0.bias | (32,) | 32 |
| x_decoder.net.2.weight | (5, 32) | 160 |
| x_decoder.net.2.bias | (5,) | 5 |

The figure "approximately 8.7k parameters" that circulates in this project's notes is wrong and
is inconsistent with the checkpoint's own file size. Do not use it.

## 2.2 Objective and training configuration

Source: `src/retrain/gae_joint.py` lines 31 and 101, `src/retrain/train_gae_joint.py`
lines 104, 105, 152 to 155.

- Objective: mean squared error on the adjacency reconstruction plus **0.1** times the mean
  squared error on the node-feature reconstruction.
- Optimiser Adam, learning rate 1e-3, cosine annealing with T_max equal to the epoch count.
- 200 epochs, batch size 32, no early stopping, final epoch retained.
- Trained on interictal windows of the twelve training subjects only.
- Input dimensions 23 -> 64 -> 16; node features are the 18 adjacency-row entries concatenated
  with 5 band powers.

## 2.3 Data partition

Source: `data/splits/split_main.json`.

| Set | Subjects | Count |
|---|---|---|
| Training | chb01, chb02, chb04, chb05, chb07, chb08, chb09, chb12, chb19, chb20, chb21, chb23 | 12 |
| Validation | chb10, chb11, chb22 | 3 |
| Held-out | chb03, chb06, chb13, chb14, chb15, chb16, chb17, chb18 | 8 |

**Trap.** The file's `train` key holds **fifteen** subjects, because it includes the three
validation subjects, and `n_train` reads 15. The twelve-subject training set is the
`inner_train` key. A chapter that reports fifteen training subjects has read the wrong key.

---

# Part 3 · Corpus

Source: the 23 per-recording summary files, parsed for file start and end times, seizure counts
and seizure start and end times.

| Set | Subjects | Files | Recorded hours | Seizures |
|---|---|---|---|---|
| Training | 12 | 342 | 566.43 | 93 |
| Validation | 3 | 91 | 115.82 | 13 |
| Held-out | 8 | 231 | 279.39 | 76 |

Per subject:

| Subject | Set | Files | Hours | Seizures |
|---|---|---|---|---|
| chb01 | train | 42 | 40.55 | 7 |
| chb02 | train | 36 | 35.27 | 3 |
| chb03 | held-out | 38 | 38.00 | 7 |
| chb04 | train | 42 | 156.06 | 4 |
| chb05 | train | 39 | 39.00 | 5 |
| chb06 | held-out | 18 | 66.73 | 10 |
| chb07 | train | 19 | 67.05 | 3 |
| chb08 | train | 20 | 20.01 | 5 |
| chb09 | train | 19 | 67.87 | 4 |
| chb10 | validation | 25 | 50.02 | 7 |
| chb11 | validation | 35 | 34.79 | 3 |
| chb12 | train | 24 | 23.69 | 40 |
| chb13 | held-out | 33 | 33.00 | 12 |
| chb14 | held-out | 26 | 26.00 | 8 |
| chb15 | held-out | 40 | 40.01 | 20 |
| chb16 | held-out | 19 | 19.00 | 10 |
| chb17 | held-out | 21 | 21.01 | 3 |
| chb18 | held-out | 36 | 35.63 | 6 |
| chb19 | train | 30 | 29.93 | 3 |
| chb20 | train | 29 | 27.60 | 8 |
| chb21 | train | 33 | 32.83 | 4 |
| chb22 | validation | 31 | 31.00 | 3 |
| chb23 | train | 9 | 26.56 | 7 |

**Seizure durations, held-out set** (n = 76): minimum 6 s, median 45 s, mean 51.9 s,
maximum 205 s. **23 of 76 are shorter than 20 s**; 31 are shorter than 30 s. With a 4 s
analysis window, a 6 s seizure spans one or two windows. This is the quantitative support for
the limitation about short seizures.

**Reconciling 279.39 with 278.22.** Total recorded time for the eight held-out subjects is
279.39 h. The scored interictal figure is 278.22 h. The difference of about 1.1 h equals the
total seizure duration (76 x 51.9 s = 1.10 h). The false-alarm denominator is therefore total
recorded time minus ictal time, with no post-ictal exclusion. Any description of a post-seizure
buffer applied to this denominator would be incorrect.

**Only 23 subjects are used, and the report does not discuss the twenty-fourth.** The corpus
directory contains a `chb24` folder, but no summary file for it exists anywhere in the release
copy, and the preprocessing stage requires that file to segment recordings and locate seizures.
The original study behind this corpus used 23 cases; the twenty-fourth was added to the archive
afterwards. The decision, taken 2026-09-06, is to use 23 and to say nothing about the exclusion
in the body.

That decision carries one obligation. **Every corpus figure in the report is taken from this
project's own parse of the 23 summary files** — 23 subjects, 182 seizures, 961.6 recorded hours,
and the per-set and per-subject figures above — and never from a corpus description quoted out
of a cited paper. Published descriptions of this corpus give 23 in some places and 24 in others;
copying one into a chapter whose tables say 23 is an internal contradiction inside a single
chapter. A one-sentence oral answer should be prepared for the defence, but it does not belong
in the text.

---

# Part 4 · Graph construction

Source: `results/diagnostics/density_frobenius_v2/`, regenerated 2026-09-06 with two
scale-comparable separation measures added.

## 4.1 Graph density

| Rule | Interictal | Ictal |
|---|---|---|
| Fixed correlation threshold 0.05 | 0.921 to 0.973 across subjects | 0.949 to 0.974 |
| Retain the strongest 20 percent of edges | **0.196 for every subject** | **0.196 for every subject** |

The fixed threshold leaves the graph almost fully connected, and its density varies from patient
to patient. The proportional rule gives an identical density for every patient and both states.
For a patient-independent system this comparability is a stronger design argument than any
separation figure, and it is not currently claimed in the outline.

**Exception:** chb17 interictal under the proportional rule is 0.224 rather than 0.196, and the
computation raised a divide-by-zero warning for that subject, indicating a channel with zero
variance in its mean adjacency. One sentence of explanation is needed wherever this appears.

## 4.2 Separation between ictal and interictal connectivity

The raw Frobenius norm of the difference between the mean ictal and mean interictal adjacency
**is not comparable between the two rules**: the proportional rule removes about eighty percent
of the entries the norm sums over, so it shrinks for arithmetic reasons regardless of what
happens to separation. On the raw measure the proportional rule appears worse for six of eight
subjects. That reading is an artefact.

Two normalised measures, both independent of how many edges survive:

| Subject | Relative Frobenius, change | Cosine distance, change |
|---|---|---|
| chb03 | +107 % | +881 % |
| chb06 | +98 % | +806 % |
| chb13 | +82 % | +801 % |
| chb14 | +129 % | +729 % |
| chb15 | +48 % | +545 % |
| chb16 | +75 % | +903 % |
| chb17 | +196 % | +871 % |
| chb18 | +60 % | +767 % |

The proportional rule increases separation on **eight of eight subjects** under both measures.

**Do not cite the figures "+88 % to +411 %"** that appear in the graph construction module's
docstring and in the earlier solution document. The per-subject output behind them was never
committed, and the diagnostic script itself states that it is a fresh measurement rather than a
reproduction of that run.

---

# Part 5 · Ensemble weighting

Source: `results/phaseB/tier2/weights_rlg/`, produced 2026-09-06 by
`src/phaseB/derive_weights_rlg.py`, which repeats the pre-registered weight-derivation
procedure for the branch set actually in use.

| | Weights | Validation macro AUROC |
|---|---|---|
| Best point on the simplex | (0.10, 0.45, 0.45) | 0.9405 |
| Equal weighting, as used | (1/3, 1/3, 1/3) | 0.9283 |
| Nearest lattice point to equal | (0.30, 0.35, 0.35) | 0.9325 |
| What the tie-break would adopt | (0.25, 0.35, 0.40) | within 0.005 of best |

- Gap between the best point and equal weighting: **0.0122**, against a window-tier spread
  across models of 0.0025. Equal weighting lies **outside** the 0.005 tolerance band, which
  contains 29 of the 231 grid points.
- The equal-weight value of 0.9283 agrees with three independent sources: the branch-ablation
  table, the committed per-subject validation AUROC file, and the results of record.

**Two limits on what this shows.** The original procedure also required a cross-check on the
twelve training subjects, with a documented fallback to equal weights if the two disagreed. The
training-subject components are not committed, so that step could not be run and its fallback
cannot be evaluated; this result is the validation half only. And the surface is scored at the
window tier, where differences in this project have repeatedly failed to reach the event tier —
the same optimum reduces the reconstruction weight to 0.10, which is the same direction as
removing that branch entirely, and removing it is known to lose at the event tier.

The defensible statement is that equal weighting was inherited rather than derived for this
branch set, that a post-hoc sweep places the window-tier optimum elsewhere by an amount above
the noise threshold, and that the weights were not re-derived because doing so after the
held-out set had been scored would be selection on the final result.

---

# Part 6 · Component ablations and design alternatives

## 6.1 Branch ablations, window tier, validation set

Source: `results/phaseB/E1_ablation_val.csv`. Rows containing the removed recurrent branch are
excluded here, as they are excluded from the report.

| Branch set | Macro AUROC | Macro AUPRC | chb10 | chb11 | chb22 |
|---|---|---|---|---|---|
| latent + gamma | **0.9386** | 0.2880 | 0.931 | 0.925 | 0.960 |
| reconstruction + latent + gamma (final) | 0.9283 | **0.3290** | 0.850 | 0.956 | 0.979 |
| gamma | 0.9060 | 0.2643 | 0.822 | 0.931 | 0.965 |
| reconstruction + gamma | 0.8652 | 0.3221 | 0.651 | 0.963 | 0.982 |
| reconstruction + latent | 0.7572 | 0.0550 | 0.668 | 0.831 | 0.772 |
| latent | 0.7309 | 0.0592 | 0.816 | 0.641 | 0.736 |
| reconstruction | 0.5920 | 0.0504 | 0.268 | 0.852 | 0.656 |

**Removing the reconstruction branch raises the ranking measure but lowers the precision-recall
measure** (0.9386 against 0.9283; 0.2880 against 0.3290). At the low seizure prevalence of this
data the second measure is the informative one. This is a stronger argument for retaining the
branch than the event-tier comparison alone, and it is not currently used anywhere.

## 6.2 Reconstruction polarity, validation set

Source: `results/phaseB/E2_latent_val.csv`.

| Subject | Reconstruction AUROC | Latent AUROC | Latent AUPRC | Interictal windows | Ictal windows |
|---|---|---|---|---|---|
| chb10 | **0.2680** | 0.8156 | 0.1097 | 28,526 | 117 |
| chb11 | 0.8517 | 0.6410 | 0.0254 | 14,231 | 204 |
| chb22 | 0.6563 | 0.7361 | 0.0426 | 11,476 | 55 |
| macro | 0.5920 | 0.7309 | 0.0592 | | |

The figure illustrating the polarity inversion should use **chb11 against chb10**: one subject
where the score behaves as expected and one where it inverts, both from the validation set.
Using a held-out subject to illustrate a design decision invites an avoidable question about
what informed the design.

## 6.3 Alternatives at the event tier, validation set

Source: `results/phaseB/tier2/alternatives/`, produced 2026-09-06 by
`src/phaseB/score_alternatives.py`, which imports the pre-registered per-subject false-alarm
budget rule unchanged. Three subjects, 13 seizures, budget target 5 false alarms per day.

| Variant | Sensitivity | Precision | F1 | FP/day | Difference in F1 |
|---|---|---|---|---|---|
| Final system | 0.846 | 0.333 | 0.478 | 4.6 | — |
| Remove the reconstruction readout | 0.923 | 0.333 | 0.490 | 5.0 | +0.012 |
| Remove the latent readout | 0.692 | 0.257 | 0.375 | 5.4 | −0.103 |
| Directed connectivity at the score level | 0.769 | 0.312 | 0.444 | 4.6 | −0.034 |
| Alternative smoothing, median 9 | 0.615 | 0.250 | 0.356 | 5.0 | −0.123 |
| Alternative smoothing, median 15 | 0.692 | 0.281 | 0.400 | 4.8 | −0.078 |
| Onset-slope change-point filtering | 0.846 | 0.324 | 0.468 | 4.8 | −0.010 |
| Artifact gate, isolated spikes only | 0.923 | 0.324 | 0.480 | 5.2 | +0.002 |
| Artifact gate, every window | 0.000 | 0.000 | undefined | 4.6 | undefined |

**Three readings that must not be got wrong.**

1. Removing the reconstruction readout gains 0.012, which is **below the 0.034 spread across
   models** and is therefore a tie, not an improvement. On the held-out set at the matched cell
   it loses outright: F1 0.162 against 0.172.
2. The per-window artifact gate produces no detections at all, because it suppresses the great
   majority of ictal windows. This is a real outcome with a known mechanism, not a missing
   value. The F1 cell reads undefined and carries an explanation.
3. Everything in this table is measured on three validation subjects and 13 seizures. The small
   sample is precisely why the noise threshold is as wide as it is, so stating it strengthens
   rather than weakens the argument.

**The value 0.579 in the results of record is a sensitivity, not an F1.** It is the sensitivity
of the reconstruction-free ensemble at the earlier configuration's balanced cell on the held-out
set, where the F1 is 0.162 at 36.5 false alarms per day.

## 6.4 Spread across independently trained models

Same source, same budget, four models of the final system:

| Model | Sensitivity | Precision | F1 | FP/day |
|---|---|---|---|---|
| seed 42 | 0.846 | 0.333 | 0.478 | 4.6 |
| seed 1 | 1.000 | 0.361 | 0.531 | 4.8 |
| seed 2 | 0.923 | 0.333 | 0.490 | 5.0 |
| seed 3 | 0.846 | 0.306 | 0.449 | 5.2 |

Standard deviation of F1: **0.0345**. The results of record quote 0.034; reproduced.

The rows for the final system and for seed 42 are identical, as they must be — they are the
same configuration reached by two different file paths. This is a consistency check on the
scoring script, and it passed.

## 6.4b Directed connectivity at the representation level

Source: `results/phaseC/c4full/{stage0_verdict_seed42.json, stage0_lg_variant_seed42.json,
rlg_lg_diagnostic_seed42.json}`. Validation subjects, window tier.

| Subject | Latent readout, final system | Latent readout, multi-relational | Change |
|---|---|---|---|
| chb10 | 0.8156 | 0.7568 | −0.0588 |
| chb11 | 0.6410 | 0.6931 | +0.0521 |
| chb22 | 0.7361 | 0.8729 | **+0.1368** |

Macro across the full ensemble falls from **0.928 to 0.909**. The two-branch comparison is the
same story: 0.9386 without the added relation against 0.9260 with it.

The added relation is not noise — its own discriminative check gives 0.7098, 0.6740 and 0.8879
against a null near 0.50. It carries signal and still costs accuracy overall. Of nine
pre-registered acceptance checks, four passed. This is the cleanest statement of
complementary-but-insufficient in the project.

## 6.4c Concentration of the top-ranked channel

Source: `results/attribution_v6/attribution_diagnostics.csv`. Held-out subjects.

| Subject | Seizures | Distinct top-1 channels | Largest share | Null 95th percentile | Verdict |
|---|---|---|---|---|---|
| chb03 | 7 | 5 | 0.429 | 0.429 | within null |
| chb06 | 10 | 7 | 0.300 | 0.300 | within null |
| chb13 | 12 | 6 | 0.417 | 0.333 | **concentrated** |
| chb14 | 8 | 5 | 0.250 | 0.375 | within null |
| chb15 | 20 | 9 | 0.500 | 0.250 | **concentrated** |
| chb16 | 10 | 4 | 0.500 | 0.300 | **concentrated** |
| chb17 | 3 | 3 | 0.333 | 0.667 | within null |
| chb18 | 6 | 5 | 0.333 | 0.500 | within null |

Three of eight subjects repeat their top-ranked channel more than chance allows. This is
independent evidence for the same limitation the annotation comparison raises: within a
patient, the method behaves partly as a subject-level channel prior rather than a per-seizure
one. It strengthens that limitation rather than weakening the method.

## 6.5 Pre-registered validation gates

Source: `results/phaseC/c4lite/G2prime_te_verdict.csv` and `results/phaseC/c1/G2_c1_verdict.csv`.
At the 40 false-alarm budget on the validation subjects:

| Variant | Cell | Sensitivity | Precision | F1 | FP/day | Gate |
|---|---|---|---|---|---|---|
| Final system | m50/p2.0 | 0.933 | 0.068 | 0.126 | 40.1 | reference |
| Directed connectivity, score level | m40/p2.0 | 0.933 | 0.070 | 0.130 | 38.9 | pass |
| Alternative smoothing, median 9 | m80/p0.5 | 0.933 | 0.070 | 0.130 | 38.9 | pass |
| Alternative smoothing, median 15 | m75/p0.5 | 0.867 | 0.063 | 0.118 | 39.9 | fail |

Both passing variants gained 0.004 at this budget and then lost at the headline budget. This is
the window-to-event transfer failure appearing inside the gating procedure itself.

## 6.6 How many alternatives were actually evaluated

Seven were registered. **Six were measured**: directed connectivity at the score level,
directed connectivity at the representation level, median smoothing, onset-slope filtering, the
artifact gate, and the ensemble reweighting. The seventh, additional per-channel time-domain
features, was **never built**, and belongs in future work rather than in the count of falsified
alternatives. Any sentence claiming seven falsified alternatives overstates the evidence.

---

# Part 7 · Channel attribution

## 7.1 The annotation is machine-generated

`results/attribution_v6/labels/ictal_channels_DRAFT.csv` carries a `label_source` column whose
value is, for **all 76 rows**, an automatically generated draft derived from the earlier
annotation pass. It was not produced by a human reader, and it has not been reviewed by the
supervising clinician.

The lineage is `results/attribution_v5/labels/labels_ALL_FINAL.csv` -> format conversion by the
attribution module -> the file above -> scoring. The word "DRAFT" in the filename refers to the
conversion step, not to a lower-quality version.

**Consequence for the report.** The claim that the model's channel ranking is consistent with a
human reader cannot be made. What the numbers support is narrower and still worth stating: the
ranking is not arbitrary with respect to visible discharge morphology. The label-free half of
the attribution work is unaffected and is not provisional.

## 7.2 Label-free results — final

Source: `results/attribution_v6/synthetic_sanity.csv`, 50 cells, 200 replicates each.

| Injection strength | 1.0 | 1.25 | 1.5 | 2.0 | 3.0 |
|---|---|---|---|---|---|
| Macro AUROC, one injected channel | **0.4912** | 0.6962 | 0.8247 | 0.9547 | 0.9818 |

Permutation null mean stayed within 0.4990 to 0.5013 across all 50 cells. Channel ranking
agreement across four independently trained models: Spearman **0.970 +/- 0.026**, top-channel
agreement 0.873.

## 7.3 Results against the draft annotation — provisional

Source: `results/attribution_v6/attribution_summary.csv`. Prevalence 0.073.

| Panel | n | Macro AUROC | Interval | Macro AUPRC | Subject-constant control | Difference | Permutation p |
|---|---|---|---|---|---|---|---|
| All annotated | 36 | 0.6497 | [0.5663, 0.7390] | 0.3095 | 0.7758 | −0.1261 | 0.001 |
| Excluding chb15 | 16 | 0.6267 | [0.4912, 0.7545] | 0.3432 | 0.6248 | +0.0020 | 0.038 |
| chb15 only | 20 | 0.6681 | [0.5368, 0.7934] | 0.2826 | 0.8967 | −0.2286 | 0.004 |

Across models: 0.6600, 0.6491, 0.6515. Under the alternative aggregation: 0.6733.

Per subject: chb03 0.8333 · chb14 **0.2672** (permutation p = 0.9391, below chance) ·
chb15 0.6681 · chb17 0.6042 · chb18 0.6483 with the control at 0.2904, the **only** subject
where attribution exceeds its control (+0.3578).

chb16 contributes a single annotated seizure and therefore has no per-subject row; a
per-subject figure will show five points, not six. chb06 and chb13 contribute none.

## 7.4 Annotation similarity

Source: `results/attribution_v6/label_diversity.csv`.

| Subject | Annotated seizures | Distinct label sets | Mean Jaccard |
|---|---|---|---|
| chb03 | 6 | 2 | 0.8333 |
| chb14 | 3 | 2 | 0.6667 |
| chb15 | 20 | 2 | 0.9053 |
| chb17 | 3 | 1 | 1.0000 |
| chb18 | 3 | 3 | 0.1667 |

The pooled figure of **0.8879** quoted in the results of record is the mean over all **214
seizure pairs**, not the mean over subjects, which is 0.714, nor the seizure-weighted mean,
which is 0.817. State which one is meant wherever it appears.

chb18 is the subject whose annotations vary, and it is also the only subject where attribution
beats the control. Those two facts are the same fact.

## 7.5 Annotation composition

76 seizures: 40 with no focal annotation, 25 with one channel, 11 with two. Mean set size
**1.31**. Focal annotations by subject: chb15 20, chb03 6, chb14 3, chb17 3, chb18 3, chb16 1.

## 7.6 The diffuseness measure

Source: `results/attribution_v6/synthetic_spread.csv` and the summary file. On real
annotations, focal 0.9693 against generalized 0.9594, one-sided p = 0.984 — the opposite of the
hypothesis. Reported as a methodological negative and never used to classify.

---

# Part 8 · Corrections to the locked documents

Each of these is a place where a locked planning document states something the data does not
support. They are listed so that a chapter written to the old wording is corrected rather than
merged.

1. **Detection latency.** The discussion outline says the latency sits at or after onset. It
   does not: three subjects have negative mean latency at the headline point. The pre-onset
   claim is still withdrawn, but for a different reason — the matching tolerance permits
   detections starting up to 30 s before the annotation, so negative values reflect the rule,
   not anticipation.
2. **Sparsification verdict.** The third numbered reason cites a measured gain in separation.
   The committed raw measure does not show one; the normalised measures do, on all eight
   subjects. The verdict stands but must cite the normalised measure, and should add the
   constant-density argument, which is stronger and currently unclaimed.
3. **Ensemble weighting.** The methodology outline attributes equal weighting to a measured
   flat weight surface. The surface is not flat for this branch set. Rewrite as inheritance
   plus a post-hoc measurement plus the reason it was not re-derived.
4. **Count of design alternatives.** Six were measured, not seven.
5. **Attribution wording.** No sentence may describe the annotation as expert or as a human
   reader's, or the agreement as clinical validation.
6. **Parameter count.** 3,285, not approximately 8.7k.
7. **Training subject count.** Twelve, not the fifteen the split file's first key implies.
8. **Five existing figures plot the earlier configuration, not the final system.** Checked
   2026-09-06 by opening the files. `E1_operating_curve.png` marks the balanced point at
   0.632 and 38.6; `E2_persubject_breakdown.png` uses the earlier configuration's two cells;
   `W1_roc_curves.png` shows per-subject values of 0.954, 0.437, 0.805, 0.626, 0.826, 0.871,
   0.747 and 0.938 for a macro of **0.775**, none of which match the final system, and it
   also draws a pooled curve that the figure specification forbids. `W2_pr_curves.png` comes
   from the same script family. `W3_score_distribution.png` could not be attributed from the
   image and has no generating script in the repository. All five must be rebuilt from the
   final system's committed grid and ensemble arrays before they enter any chapter.

   Two of the ten existing assets were checked and are correct: the synthetic-injection figure
   (the specification's warning about it was a false alarm; three cosmetic issues only) and the
   per-subject attribution forest plot, which carries the provisional qualifier and matches the
   summary file. The forest plot's title refers to a reader, which must change.

9. **Confidence intervals.** Dropped from the detection results by decision. Intervals remain
   only for the attribution agreement, where removing them would make a provisional result look
   settled. The interval column of the metrics table, the interval sentences in the methodology
   and validity sections, and the two interval references become unused; nothing is renumbered
   until consolidation.

---

# Part 9 · Values that must never appear

`0.750` · `0.829` · `0.791` · `39.77` · `71.25` · `0.8676` · `0.836`

Add **`0.775`** to what must be watched. It is the earlier configuration's macro window-tier value and it appears on an existing figure; the final system's value is 0.805.

Two live hazards remain in files a chapter writer has to open:
`src/retrain/train_gae_joint.py` repeats two of them in its opening docstring, and the graph
construction module's docstring carries the unreproduced separation range. The model module
itself has already been corrected.

---

# Part 10 · Still open

| Item | Status |
|---|---|
| Whether the machine-generated annotation is kept in the body, moved to an appendix, or deferred to a later publication | Decision pending; a fallback that does not depend on the answer is described in Part 7.1 |
| Training-subject components, which would complete the weight-derivation cross-check | Not committed |
| Five detection figures rebuilt from the final system | Build task; sources all present |
| Library versions for the software table | One command, not yet run |
| Published reference points for the comparison figure, checked against the source papers | Cannot be done without the papers |
| One docstring line in the training script | One-line edit |
