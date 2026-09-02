# ATTRIBUTION — REPORT WRITING PACK
### Everything needed to write the channel-attribution material. Numbers are final; do not recompute.

**Purpose.** A later session writing the thesis report should be able to draft the attribution Methods,
Results and Discussion **from this file alone**, without opening CSVs, re-deriving anything, or making
a framing judgement that has already been made. Every number here is copied from a committed file and
is safe to put in the report as-is.

**Provenance of every number below.** GAE checkpoint `data/models_retrain/gae_joint_seed42.pt`,
sha256 `dea06cb5…`, bias fingerprint 1.1597, chb13 recon AUROC 0.8319, verified corr = 1.0000000 on
16/16 committed TEST `zrecon` arrays. Source CSVs: `results/attribution_v6/`. Spec:
`docs/ATTRIBUTION_SPEC.md` v3 rev. B. Summary of record: `docs/RESULTS_OF_RECORD_phaseB.md` §10.

**Status.** Machinery validation is FINAL and label-free. Everything scored against labels is
**PROVISIONAL** (draft labels, not supervisor-frozen) **and narrower than intended** (the labels are
dominant-channel, not the full ictal set). Both qualifiers must appear wherever those numbers appear.

---

# PART 0 — THE FIVE SENTENCES

If the report says nothing else about attribution, it must say these, in this order:

1. The GAE's per-node reconstruction error yields, for each seizure, a ranking of the 18 channels by
   how anomalous each looks relative to that patient's own interictal baseline.
2. That ranking machinery is verified against synthetic ground truth: it is exactly at chance when
   nothing is injected (0.4912) and near-perfect when a strong anomaly is injected (0.9818), rising
   monotonically in between, with a permutation null of 0.4990–0.5013 across all 50 test cells.
3. The ranking is stable across GAE random seeds (Spearman 0.970 ± 0.026).
4. Against reader labels it is above chance (macro-AUROC 0.6497, p = 0.001; AUPRC 0.3095 = 4.2×
   prevalence), but those labels record only the reader's *dominant* channel (1–2 per seizure), so
   this answers a narrower question than intended.
5. Because those labels are near-constant within a patient (Jaccard 0.8879), per-seizure attribution
   and a subject-level channel prior **cannot be distinguished** with them. This is a limitation of
   the labels, not a finding about the method.

**The single most dangerous mis-write.** The subject-constant control scores 0.7758 against
attribution's 0.6497. Writing "the control outperforms attribution, so attribution carries no
per-seizure information" is wrong and will not survive a viva question. See PART 4 §4.3 for the
correct wording and the mechanism.

---

# PART 1 — WHERE EACH PIECE GOES

| Report section | Content | Approx. length |
|---|---|---|
| Ch.2/3 Methods — new subsection "Channel attribution" | PART 2 of this file | 500–700 words + 1 equation block |
| Ch.4 Results — subsection "Attribution machinery validation" | PART 3 §3.1–§3.2 + Fig 1, Fig 2 | 300–400 words + 2 figures |
| Ch.4 Results — subsection "Channel attribution against reader labels" | PART 3 §3.3–§3.5 + Fig 3, Fig 4 + Tables A/B/C | 400–500 words + 2 figures + 3 tables |
| Ch.5 Discussion — "Explainability of the graph autoencoder" | PART 4 §4.1–§4.2 | 300–400 words |
| Ch.5 Discussion — Limitations | PART 4 §4.3–§4.5 | 250–350 words |
| Ch.5 Future Work | PART 4 §4.6 | 100 words |
| Appendix | `figures/attribution/attribution_top3_channels.csv` (76 rows) | table |

**Rubric mapping** (`docs/RUBRIC_TRACKING.md`): criterion #6 (validity/reliability) is served by the
synthetic validation and the seed robustness; criterion #7 (significance/applicability) by the XAI
framing and the honest limitations; criterion #8 (graphics/statistics) by Figures 1–4.

---

# PART 2 — METHODS (ready to adapt)

## 2.1 What the method is, and what it is not

State this explicitly and early, because reviewers will otherwise assume localization:

> Channel attribution here is **explainability for the reconstruction branch of the graph
> autoencoder**. It asks which channels the model finds anomalous during a seizure. It is **not**
> seizure localization and **not** seizure-onset-zone identification: no intracranial reference, no
> surgical outcome, and no clinician-confirmed onset zone exists for CHB-MIT.

## 2.2 The score

Per window `w` and channel `i`, the joint GAE produces a per-node reconstruction error `r_i(w)`
(the same quantity that, averaged over channels, forms the `zrecon` branch of the detection ensemble —
so attribution explains the deployed model, not a separate one).

Robust-z against the patient's own interictal baseline:

```
med_i     = median_w  r_i(w)                    over that subject's interictal windows
mad_i     = median_w |r_i(w) − med_i| + 1e-9    over the same windows
zwin_i(w) = (r_i(w) − med_i) / mad_i
```

Aggregated over the windows of one seizure:

```
PRIMARY      s_i = p95_w |zwin_i(w)|      (pre-registered)
SENSITIVITY  s_i = mean_w |zwin_i(w)|
```

**Justify p95 in the text:** ictal involvement is a peak phenomenon — a channel may participate for
only part of the seizure, so the 95th percentile captures involvement that a mean would dilute. State
that this was pre-registered before any result was seen, and that the mean-aggregation sensitivity
analysis is reported (it gives 0.6733 vs 0.6497, i.e. the conclusion does not depend on the choice).

Montage order (fixed): left temporal FP1-F7, F7-T7, T7-P7, P7-O1 · left central FP1-F3, F3-C3, C3-P3,
P3-O1 · right central FP2-F4, F4-C4, C4-P4, P4-O2 · right temporal FP2-F8, F8-T8, T8-P8, P8-O2 ·
midline FZ-CZ, CZ-PZ.

## 2.3 Scope

All **76 seizures** of the 8 held-out TEST subjects, **not conditioned on whether the detector found
them** — attribution explains the GAE branch and is independent of the change-point stage, so
conditioning on detection would introduce selection bias. Seizure boundaries come from an exact
row→seizure map verified against the CHB-MIT summaries on all 76 seizures
(`results/attribution_v6/seizure_blocks.csv`). Window counts per seizure: min 2, median 12, max 52.

## 2.4 The labels — write this honestly

> Channel-level ground truth does not exist for CHB-MIT: the corpus provides seizure onset and offset
> times only. A reading pass over rendered EEG segments therefore produced, for each seizure, the
> channel or channels carrying the visually dominant ictal discharge. Of the 76 TEST seizures, 40 were
> judged diffuse with no identifiable leading channel, 25 had one dominant channel and 11 had two
> (mean 1.31 labelled channels per seizure; prevalence 1.31/18 = 0.073). The 36 seizures with an
> identified dominant channel form the evaluable set.

Then state the consequence, once, plainly:

> These labels record the *leading* channel rather than every channel carrying ictal discharge. The
> evaluation therefore tests whether the model ranks the reader's dominant channel highly, which is a
> narrower question than whether it recovers the full ictal field.

## 2.5 Metrics

- **Primary:** macro-AUROC and macro-AUPRC, averaged **across seizures** (never pooled across
  channel × seizure — the robust-z scale differs per seizure). 95 % CIs by bootstrap over seizures
  (1000 resamples).
- **Null:** within each seizure, permute the 18 scores while keeping the labels; 1000 iterations;
  report the null mean and an empirical p-value. This is a stronger reference than comparing to 0.5.
- **Secondary:** Recall@|S|; per-subject stratification; sensitivity to aggregation and to GAE seed.
- **Control (pre-registered, D7):** for each seizure, replace its score vector with the mean score
  vector of the *other* seizures of the same patient (leave-one-out) and score that with the same
  labels and metrics. This asks whether per-seizure information exists beyond a patient-level prior.

## 2.6 Synthetic validation (report this as a method, not an afterthought)

> Because no gold standard exists, the scoring machinery was validated against synthetic ground truth
> before any real label was scored. A pseudo-seizure was defined as a contiguous block of interictal
> windows, its length drawn from the empirical distribution of the 76 real seizures. Reconstruction
> error was multiplied by α on |S| randomly chosen channels within the block, the robust-z baseline
> was computed on interictal windows **excluding** that block, and the resulting ranking was scored
> against the known injected set. The grid was α ∈ {1.0, 1.25, 1.5, 2.0, 3.0} × |S| ∈ {1, 2, 4, 8, 12},
> 200 replicates per cell, on the validation subjects (gate) and repeated on the test subjects
> (confirmatory). Pass criteria were registered in advance: chance performance at α = 1.0, ≥ 0.95 at
> α = 3.0 with |S| = 1, and monotonicity in α.

---

# PART 3 — RESULTS (all numbers final)

## 3.1 Synthetic validation — LABEL-FREE, NOT PROVISIONAL

**Figure 1 — `figures/attribution/attribution_fig1_synthetic.png`**
Caption: *Macro-AUROC of the channel-attribution score against synthetic ground truth, as a function
of injected anomaly strength α, for validation (left, pre-registered gate) and test (right,
confirmatory) subjects. Each point averages 200 pseudo-seizures. The dashed line is chance; the
permutation null stayed within 0.4990–0.5013 across all 50 cells.*

**Table — macro-AUROC, validation subjects:**

| α | \|S\|=1 | \|S\|=2 | \|S\|=4 | \|S\|=8 | \|S\|=12 |
|---|---|---|---|---|---|
| 1.00 | **0.4912** | 0.4873 | 0.5087 | 0.4911 | 0.5257 |
| 1.25 | 0.6962 | 0.6942 | 0.7079 | 0.6973 | 0.6924 |
| 1.50 | 0.8247 | 0.8367 | 0.8279 | 0.8362 | 0.8260 |
| 2.00 | 0.9547 | 0.9291 | 0.9472 | 0.9409 | 0.9504 |
| 3.00 | **0.9818** | 0.9917 | 0.9835 | 0.9828 | 0.9881 |

> **Anticipate one reviewer question about the α = 1.0 row.** Two of the ten no-injection cells have
> p_perm < 0.05 (validation |S| = 12: AUROC 0.5257, p = 0.008; test |S| = 8: AUROC 0.5199, p = 0.022).
> The effect sizes are negligible — every α = 1.0 cell lies within [0.4694, 0.5257], i.e. inside the
> pre-registered [0.45, 0.55] band — but the permutation null is very tight at 200 replicates, so a
> deviation of 0.02 can reach nominal significance. Report the negative control by **effect size**
> (AUROC ≈ 0.5), not by p-value, and say so in one clause. No multiple-comparison correction was
> pre-registered across the 50 cells; note that rather than applying one after the fact.

Test-panel confirmation (same grid): 0.5191 / 0.4694 / 0.5038 / 0.5199 / 0.4976 at α = 1.0, rising to
0.9791 / 0.9798 / 0.9847 / 0.9832 / 0.9822 at α = 3.0 — reproducing the validation panel to within
about 0.03 everywhere.

**Pre-registered gates, all PASS:**

| gate | criterion | measured |
|---|---|---|
| negative control | α = 1.0, \|S\| = 1 → AUROC ∈ [0.45, 0.55] | 0.4912 |
| upper bound | α = 3.0, \|S\| = 1 → AUROC ≥ 0.95 | 0.9818 |
| monotonicity | AUROC increases with α at every \|S\| | holds |
| diffuseness contrast | spread(\|S\|=18) > spread(\|S\|=1) at α = 2.0 | 0.9755 vs 0.9644, p = 8.9e-11 |

**Sentence for the text:** a 25 % increase in a channel's reconstruction error is already detected at
AUROC ≈ 0.70, which sets the sensitivity scale for interpreting the real-label result.

## 3.2 Seed robustness — LABEL-FREE, NOT PROVISIONAL

**Figure 2 — `figures/attribution/attribution_fig2_seed_robustness.png`**
Caption: *Stability of the channel ranking across four independently seeded GAE checkpoints. Left:
Spearman correlation between the seed-42 ranking and each of seeds 1, 2, 3, over all 76 seizures.
Right: agreement on the single most anomalous channel.*

- Channel-ranking Spearman ρ = **0.970 ± 0.026** (seed 42 vs seeds 1/2/3).
- Top-1 channel agreement **0.873**; all three other seeds agree with seed 42 on **74 %** of seizures,
  partial agreement on 25 %, no agreement on 1 %.
- Macro-AUROC against labels by seed: 0.6497 (42), 0.6600 (1), 0.6491 (2), 0.6515 (3).

## 3.3 Channel-ranking structure — LABEL-FREE

**Figure 3 — `figures/attribution/attribution_fig3_rank_heatmap.png`**
Caption: *Per-seizure channel ranking (1 = most anomalous) for all 76 test seizures, grouped by
subject. Rank is scale-free, so seizures are directly comparable. The near-continuous top ranking of
P3-O1 across all twenty chb15 seizures is the patient-level channel prior discussed in §5.x.*

This is the most informative figure in the chapter — it shows the subject-level prior directly rather
than through a statistic.

- **No global channel bias.** Top-1 frequency over 76 seizures spreads across all 18 channels; the most
  frequent is P3-O1 at 14/76 (18 %; random expectation 4.2). Mean pairwise Spearman between seizures
  of *different* subjects is **−0.012**.
- **Subject-typical but not degenerate.** Mean pairwise Spearman *within* a subject is **0.265**
  (413 pairs) vs −0.012 across subjects (3000 sampled pairs), Δ = +0.277.
- **Three subjects concentrate more than chance** (top-1 share vs a random null): chb13 0.417 (null
  p95 0.333), chb15 0.500 (0.250), chb16 0.500 (0.300). chb03, chb06, chb14, chb17, chb18 are within
  the null.

## 3.4 Against reader labels — PROVISIONAL

**Figure 4 — `figures/attribution/attribution_fig4_persubject_forest.png`**
Caption: *Attribution performance against the reader's dominant-channel labels, overall and by
subject, with bootstrap 95 % confidence intervals. Open diamonds mark the subject-constant control.
The control lies to the right of the per-seizure estimate for most subjects, but the two coincide once
chb15 is removed (Δ = +0.002) — see §5.x.*

**Table A — main panels (seed 42, p95 aggregation).** Δ = AUROC − subject-constant control.

| panel | n | macro-AUROC [95 % CI] | AUPRC | Recall@\|S\| | control | Δ | p_perm |
|---|---|---|---|---|---|---|---|
| all labelled | 36 | **0.6497** [0.5663, 0.7390] | 0.3095 | 0.1389 | 0.7758 | −0.1261 | 0.0010 |
| excluding chb15 | 16 | 0.6267 [0.4912, 0.7545] | 0.3432 | 0.2188 | 0.6248 | **+0.0020** | 0.0380 |
| chb15 only | 20 | 0.6681 [0.5368, 0.7934] | 0.2826 | 0.0750 | 0.8967 | −0.2286 | 0.0040 |
| mean aggregation | 36 | 0.6733 [0.5755, 0.7634] | 0.3856 | 0.1944 | 0.7887 | −0.1154 | 0.0010 |

Prevalence = 0.073, so AUPRC 0.3095 is **4.2× prevalence**. Quote that ratio, not the bare AUPRC.

**Table B — per subject.**

| subject | n | macro-AUROC [95 % CI] | AUPRC | control | Δ | p_perm |
|---|---|---|---|---|---|---|
| chb03 | 6 | 0.8333 [0.6956, 0.9706] | 0.5840 | **1.0000** | −0.1667 | 0.0020 |
| chb14 | 3 | **0.2672** [0.1562, 0.4688] | 0.1565 | 0.3229 | −0.0558 | 0.9391 |
| chb15 | 20 | 0.6681 [0.5323, 0.7840] | 0.2826 | 0.8967 | −0.2286 | 0.0030 |
| chb16 | 1 | 0.4688 (no CI) | — | — | — | — |
| chb17 | 3 | 0.6042 [0.4062, 0.7812] | 0.2168 | 0.6250 | −0.0208 | 0.2358 |
| chb18 | 3 | 0.6483 [0.4062, 0.8824] | 0.2407 | 0.2904 | **+0.3578** | 0.1838 |

chb06 and chb13 contribute **0** labelled seizures — every one of their seizures was read as diffuse.
Say so; do not leave them silently absent.

**Table C — label diversity (the evidence for the limitation).**

| subject | n labelled | distinct label sets | mean Jaccard | union size |
|---|---|---|---|---|
| chb03 | 6 | 2 | 0.8333 | 2 |
| chb14 | 3 | 2 | 0.6667 | 2 |
| chb15 | 20 | **2** | 0.9053 | 2 |
| chb16 | 1 | — | — | 2 |
| chb17 | 3 | **1** | **1.0000** | 2 |
| chb18 | 3 | 3 | **0.1667** | 4 |
| **pooled** | 36 | — | **0.8879** | — |

Also: corr(y − ȳ, s − s̄) within chb15 = **+0.089**, computed over 20 seizures that carry only 2
distinct label sets.

## 3.5 The spread metric — a methodological negative

Normalised entropy of the score vector was proposed as a focal-versus-generalized measure. It fails in
both directions and is reported as a negative result:

- **Synthetic:** spread is **U-shaped** in the number of injected channels — 0.9644 (|S|=1) → 0.9567
  (2) → **0.9441 (4, minimum)** → 0.9503 (12) → 0.9755 (18). The no-injection cell has the *highest*
  spread of all (0.978).
- **Real labels:** focal 0.9693 > generalized 0.9594, one-sided p = **0.984** — the opposite of the
  hypothesis.

Mechanism, one sentence: entropy measures **uniformity**, not localisation — one elevated channel among
seventeen flat ones is still fairly uniform, whereas four elevated channels are maximally bimodal.
Consequence: the metric separates only the two extremes and cannot classify real seizures, which fall
in the middle. Do not use it anywhere else in the report.

---

# PART 4 — DISCUSSION (arguments, pre-made)

## 4.1 What this contributes

Two contributions, both defensible:

1. **A channel-level annotation over CHB-MIT.** The corpus provides onset/offset times only. Most
   interpretability work on CHB-MIT validates qualitatively ("the saliency resembles the known
   focus"). This work adds an explicit reading pass and evaluates against it numerically.
2. **A quantitative attribution evaluation with a null and a synthetic upper bound.** The synthetic
   injection experiment establishes what the machinery *can* detect (a +25 % anomaly at AUROC ≈ 0.70)
   before asking what it *does* detect. That upper bound is what makes the real-label number
   interpretable rather than a bare figure.

Frame relative to **EEG-CGS** (Ho & Armanfard, AAAI 2023) — unsupervised GNN-autoencoder anomalous
*channel* detection, reference bar 0.70 / 0.55 / 0.43 / 0.78 on TUSZ. Cite it for framing and scale
only. It is **not** a like-for-like comparison: different corpus, pre-existing channel labels, and a
contrastive objective rather than a plain reconstruction readout. Say that explicitly; a reviewer who
spots an implied head-to-head comparison will discount the whole section.

## 4.2 What the numbers support

Above chance, robustly: macro-AUROC 0.6497 with p_perm = 0.001, AUPRC at 4.2× prevalence, stable
across four GAE seeds (0.6491–0.6600) and across both aggregation choices. The reconstruction error of
a model trained only to reconstruct interictal connectivity carries channel-level information that
aligns with a human reader's judgement of which channel leads the discharge — without ever seeing a
label.

## 4.3 The limitation that decides the chapter — write it exactly like this

The subject-constant control (0.7758) outscores the per-seizure estimate (0.6497). The correct reading:

> A subject-constant baseline — the average score vector of the patient's *other* seizures — was
> pre-registered as a control for whether attribution carries seizure-specific information. It scored
> higher than the per-seizure estimate (0.7758 vs 0.6497). This does not establish that per-seizure
> attribution is uninformative, because the labels cannot support that inference: within a patient the
> labelled channel set is nearly constant (mean Jaccard 0.8879; one subject has a single label set
> across all three of its seizures, and chb15 has two across twenty). A one- or two-channel dominant
> label drawn from a patient's fixed anatomical focus is almost forced to be invariant, so averaging
> the other seizures wins by noise reduction alone, independently of what the per-seizure score
> contains. With these labels, per-seizure attribution and a patient-level channel prior are not
> distinguishable.

Two supporting observations worth including — both are visible in Figure 4 and both come from the
committed numbers:

- Removing chb15 makes the gap vanish (Δ = **+0.002**, control 0.6248 vs 0.6267). The apparent control
  advantage is produced by one subject, which is also the subject with the most concentrated ranking
  (top-1 share 0.500 against a null of 0.250) and 20 of the 36 labelled seizures.
- chb18 is the only subject where attribution clearly beats the control (Δ = **+0.358**), and it is
  also the only subject whose labels genuinely vary between seizures (Jaccard **0.1667**, three
  distinct label sets across three seizures). The exception has the mechanism the argument predicts.

## 4.4 Other limitations (list them; do not bury them)

1. Labels are a draft reading pass, not supervisor-frozen and not blind. Every label-scored number is
   provisional.
2. The label schema is dominant-channel, not the full ictal field, so the intended per-channel binary
   question is not answered.
3. chb15 supplies 20 of 36 labelled seizures; no result over the labelled set is a balanced
   eight-subject result.
4. chb06 and chb13 contribute zero labelled seizures — every seizure was read as diffuse. Attribution
   is untested on them.
5. chb14 scores **below** chance (0.2672, p = 0.94) on three seizures. Report it; do not omit it. It is
   consistent with chb14 being representation-limited in the detection results.
6. Inter-reader agreement on seizure localisation is known to be low, so agreement with a single
   reader is *concordance*, not accuracy.
7. Attribution measures reconstruction anomaly relative to interictal, which is not the same as ictal
   activity; artefact and state changes can also raise it.

## 4.5 Honest framing of the negative results

The chapter contains two negatives — the spread metric and the uninformative control. Present both as
outcomes of a pre-registered design rather than as failures: the spread hypothesis was registered with
a falsification criterion, failed it, was diagnosed (U-shape in |S|), the *construction* was corrected
while the metric and threshold were left untouched, and the corrected version was re-registered before
being run. That sequence is itself evidence of method quality and is worth points under rubric #6.

## 4.6 Future work

Re-run against supervisor-frozen labels under the full ictal-set schema — the single change that would
make the intended per-channel evaluation possible. Target within-subject label Jaccard below 0.6 so
that the subject-constant control becomes informative. Obtain a verdict for chb06 and chb13. A
diffuseness measure that is monotone in the number of involved channels, replacing normalised entropy.

---

# PART 5 — GUARDRAILS

**Never write:**
- "localization", "seizure onset zone", "SOZ", or "the model localizes the seizure"
- any label-scored number without "provisional"
- "the control outperforms attribution, so attribution failed" (see §4.3)
- a claim that per-channel binary classification over the full ictal field was evaluated
- the spread metric as a working focal/generalized classifier
- a head-to-head comparison with EEG-CGS
- the constants 0.8676 or 0.836 as the canonical checkpoint's fingerprint — those are the pre-rebuild
  §0 model (canonical is bias 1.1597, chb13 0.8319)

**Always write:**
- "explainability of the reconstruction branch" or "channels with ictal-like reconstruction anomaly"
- AUPRC as a multiple of prevalence (4.2×), not as a bare number
- the synthetic upper bound alongside the real-label result, so the reader can calibrate 0.6497
- chb14's below-chance result and chb06/chb13's absence

**If a number is needed that is not in this file:** it is in `results/attribution_v6/`
(`attribution_summary.csv` for panels, `attribution_perseizure.csv` for per-seizure values,
`synthetic_sanity.csv` and `synthetic_spread.csv` for the synthetic grid, `label_diversity.csv` for
Jaccard, `attribution_scores.csv` for the raw 10944-row score/rank table). Read it from the CSV. Do
not estimate, and do not carry a number over from a chat transcript.

**To regenerate everything:**
```bash
python src/verify_provenance.py                  # must print PASS
python src/attribution_pipeline.py all           # all result CSVs
python src/figures/attribution_figures.py        # all four figures + appendix CSV
```
