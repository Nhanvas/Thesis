# ATTRIBUTION — REPORT WRITING PACK (v2, 2026-09-18)
### Everything needed to write the channel-attribution material. All numbers FINAL (2026-09-19).

**Purpose.** A later session should be able to rewrite the attribution material of Chapters 1–5 and the
front matter **from this file alone**, without re-deriving a framing decision. Method and claims are
locked in `docs/ATTRIBUTION_SPEC.md` v4, Amendment A4. Numbers of record: `docs/RESULTS_OF_RECORD_phaseB.md` §10.

**Provenance.** GAE checkpoint `data/models_retrain/gae_joint_seed42.pt`, sha256 `dea06cb5…`, bias
1.1597, chb13 recon AUROC 0.8319. Label-free CSVs: `results/attribution_v6/`. Final annotation and every
label-scored CSV: `results/attribution_v7/`.

**What changed from v1.** The machine-generated dominant-channel draft is **retired**. Ground truth is
now a human annotation, blind to the model, approved by the supervisor, listing every ictal channel.
Every v1 label-scored number (0.6497, 0.3095, 0.7758, 0.8879, +0.3578, 0.2672, p = 0.984, …) is retired
and must disappear from the report. The words "provisional", "draft annotation", "language model",
"narrower than intended" and "dominant channel" disappear with it — except in the one history sentence
of PART 2 §2.4.

---

# PART 0 — THE SIX SENTENCES

1. The GAE's per-node reconstruction error yields, for each seizure, a ranking of the 18 channels by how
   anomalous each looks relative to that patient's own interictal baseline.
2. The ranking machinery is verified against synthetic ground truth: chance with nothing injected
   (0.4912), near-perfect with a strong anomaly (0.9818), monotone in between, permutation null
   0.4990–0.5013 across all 50 cells.
3. The ranking is stable across GAE random seeds (Spearman 0.970 ± 0.026).
4. Against a blind, supervisor-approved annotation of every ictal channel in 62 focal test seizures,
   the ranking is only weakly above chance (macro-AUROC 0.5694 [0.5097, 0.6321], permutation p =
   0.001), and the agreement rests on one patient: without chb15 it is 0.5011 (p = 0.49).
5. A rule that ignores the EEG and ranks channels by how often they are ictal in other patients reaches
   0.7387; the model is 0.1694 below it (95 % CI −0.2553 to −0.0804).
6. Within a patient, a seizure's own map fits its own annotation no better than a sibling seizure's map
   does (mean difference +0.0064, Holm-adjusted p = 0.68).

**Verdict: a pre-registered negative at L2 and L3.** The scoring machinery detects injected anomalies
(sentence 2), but the anomaly the model sees in real seizures is not where a reader sees the discharge.
Never soften this into "above chance, therefore informative".

---

# PART 1 — WHERE EACH PIECE GOES (exhibit numbering unchanged, `EXHIBIT_SET_FINAL.md` rev 3)

| Exhibit / section | Before | After |
|---|---|---|
| Ch.2 §2.5.2 Reference annotation | machine draft, dominant channels | rewrite from PART 2 §2.4 |
| Ch.2 §2.7.4 Attribution metrics | L1 + D7 | add L2, L3, Holm; D7 kept as registered |
| Table 2.7 synthetic grid | — | unchanged |
| Ch.3 §3.6.1 + Table 3.6 + Figure 3.8 | synthetic | unchanged (label-free) |
| Ch.3 §3.6.2 + Figure 3.9 rank heat map | draft labels overlaid | regenerate with final labels overlaid; caption loses "provisional" |
| Ch.3 §3.6.3 + **Table 3.7** | provisional agreement with draft | **L1/L2/L3 + D7 table**, from `attribution_v7/attribution_summary.csv` |
| **Table 3.8** | draft Jaccard | **final annotation composition and within-patient similarity** (|S| distribution, Jaccard per subject) |
| Ch.3 §3.6.4 + **Figure 3.10** | synthetic + real spread | **synthetic only**; real-label panel removed |
| Table 3.9 rows "3 (beyond registration)" and "6." | "provisional against a draft" | outcome per §4.7 row |
| Ch.4 §4.4 Channel attribution | control uninformative, draft limits | rewrite from PART 4 |
| Ch.4 §4.8 / §4.9 validity, limitations | draft-label limitations | PART 4 §4.4 |
| Ch.1 lines ~276–305, Week 10 row (~489) | "draft channel annotation" | "blind channel annotation, supervisor-approved" |
| Ch.5 lines ~42–74 | draft, prior indistinguishable | one paragraph from PART 0 sentences 4–6 |
| Front matter abstract (~26) and AI-use statement (~74) | annotation by a language model | annotation by the author, blind; delete the language-model clause for the annotation |
| `tables/CAPTIONS.md` 3.9, 3.10, 3.7, 3.8 | provisional/draft wording | new captions (PART 3) |
| `RUBRIC_TRACKING.md` | draft-era attribution rows | update after the run |

---

# PART 2 — METHODS (ready to adapt)

## 2.1 What the method is, and what it is not
Unchanged from v1: explainability for the reconstruction branch; not localization, not SOZ.

## 2.2 The score
Unchanged: per-node error → robust-z against the patient's interictal median/MAD → p95 over the seizure's
windows (Equation 8). p95 is pre-registered; mean aggregation is a reported sensitivity.
**New sentence worth adding:** the annotation convention counts a channel if it carries clear ictal
discharge *at any point* of the seizure, which is what a peak statistic over the whole seizure measures.

## 2.3 Scope
All 76 test seizures are scored and none is conditioned on detection. Channel metrics are defined for the
**62 focal** seizures; the 14 annotated as involving all 18 channels have no channel contrast (AUROC is
undefined when every channel is positive) and are excluded by construction. This follows common practice
in scalp localization studies, which evaluate on focal cases only (e.g. SZTrack excluded generalized
epilepsy and indeterminate-onset patients).

## 2.4 The annotation — write this plainly (replaces §2.5.2)
> No public channel-level ground truth exists for CHB-MIT, which records only onset and offset times.
> A per-seizure channel annotation was therefore produced for the 76 test seizures. For each seizure,
> the author inspected the raw 18-channel bipolar EEG and listed every channel carrying a clear ictal
> discharge — rhythmic evolution, sharp-and-slow activity or evolving low-voltage fast activity — at any
> point during the seizure; attenuation alone, artifact and isolated transients were not counted. A
> seizure involving all eighteen channels was recorded as generalized. The annotation was made without
> access to any output of the model (no score, ranking or channel map), and the protocol and the
> resulting annotation were reviewed and approved by the supervisor.
>
> Of the 76 seizures, 14 were annotated as generalized (all ten of chb06, three of chb03 and one of
> chb13) and 62 as focal, with between one and ten ictal channels (mean 4.55, i.e. 25.3 % of channels).

**History sentence (one, mandatory, no numbers):**
> An earlier, automatically generated annotation recorded only the one or two dominant channels per
> seizure; it was superseded by the annotation above before the final evaluation and is not reported.

## 2.5 Metrics (replaces §2.7.4)
- **L1 (primary):** macro-AUROC over the 62 focal seizures, bootstrap 95 % CI, within-seizure
  permutation null (1000).
- **L2:** the same metric for an anatomical prior — each channel scored by how often it is ictal in the
  *other seven* patients — and the paired-bootstrap difference. Justify in one sentence: an attribution
  map is only informative if it beats a map that ignores the input, the logic of the centre baseline in
  the pointing game (Zhang et al.).
- **L3:** within each patient, agreement of a seizure's own map with its own annotation versus the maps
  of the patient's other seizures; permutation of map-to-seizure assignment within patient.
- **D7:** the patient-constant control, reported as registered.
- L1 gates L2 and L3; Holm correction over {L2, L3}.
- Descriptive: AUPRC against prevalence 0.253, Recall@|S|, per patient, without chb15, mean aggregation,
  seeds.

## 2.6 Synthetic validation
Unchanged (Table 2.7, §2.5.3).

---

# PART 3 — RESULTS

## 3.1 Label-free — FINAL (unchanged from v1)
Table 3.6 and Figure 3.8: synthetic grid, gates G-S1/2/3/G-S4′ PASS, null 0.4912, ceiling 0.9818,
permutation null 0.4990–0.5013, +25 % anomaly detected at AUROC ≈ 0.70. **No p-value on the G-S4′ row**
(8.9e-11 is untraced). Seeds: Spearman 0.970 ± 0.026, top-1 agreement 0.873. No global channel bias
(most frequent top-1 P3-O1, 14/76). Within-subject rank Spearman 0.265 vs across −0.012.

## 3.2 Annotation composition — label-only, measured 2026-09-18 (reproduce from `label_diversity.csv`)
Focal seizures by patient: chb03 4 · chb06 0 · chb13 11 · chb14 8 · chb15 20 · chb16 10 · chb17 3 ·
chb18 6. Pooled within-patient Jaccard 0.5144 (mean over seizure pairs). Frontopolar channels ≈ 41 % of
labels; five channels never labelled. Anatomical prior macro-AUROC 0.7387.

## 3.3 Against the annotation — FINAL
All values: spec §9.3 (copied from `results/attribution_v7/`). Table 3.7 = the four-test table plus the
per-subject rows. Headline values: L1 0.5694 [0.5097, 0.6321] p 0.001 · L2 −0.1694 [−0.2553, −0.0804]
· L3 +0.0064 p_holm 0.6753 · D7 −0.0737 · excl. chb15 0.5011 · seeds 0.5755/0.5767/0.5723 · mean agg
0.5854 · AUPRC 0.4500 at prevalence 0.253. Per subject: chb15 0.7127, chb13 0.6763, chb17 0.7082
(n = 3), chb14 0.5908, chb03 0.4924, chb18 0.3650, chb16 0.2597.
Spec §9.3b is exploratory and is **not** quoted with numbers until folded into a committed file; it
may be described qualitatively in Chapter 4 (patient-specific agreement; chb16 inversion).

## 3.4 Spread — synthetic negative only
U-shape in |S| (0.9644 → 0.9441 minimum at |S| = 4 → 0.9755). No real-label result.

## 3.5 Captions to replace (draft text, finalise after the run)
- **Figure 3.9.** Per-seizure channel ranking for the 76 test seizures, grouped by patient, with the
  annotated ictal channels marked. Generalized seizures are shown but carry no channel contrast.
- **Figure 3.10.** Diffuseness of the attribution map against the number of injected channels on the
  synthetic grid. The measure is U-shaped, so it cannot separate focal from generalized seizures and is
  reported as a methodological negative.
- **Table 3.7.** Agreement between the channel ranking and the blind channel annotation, over 62 focal
  test seizures, with the anatomical-prior and within-patient controls. *Mandatory:* single annotator,
  blind to the model, approved by the supervisor; agreement is concordance, not accuracy.
- **Table 3.8.** Composition of the channel annotation and within-patient similarity. The pooled value
  is the mean over seizure pairs.

---

# PART 4 — DISCUSSION (arguments, pre-made)

## 4.1 Contribution
1. **A blind, supervisor-approved, every-ictal-channel annotation of the 76 CHB-MIT test seizures** —
   the corpus has none; most CHB-MIT interpretability work validates qualitatively.
2. **A quantitative attribution evaluation with four references**: a permutation null, a synthetic upper
   bound, an anatomical prior, and a within-patient specificity test. The prior is the reference most
   attribution studies omit, and on this corpus it is strong (0.7387).
3. **A cautionary result.** Judged against chance alone, the attribution would have been reported as a
   success (p = 0.001). Judged against the prior and within patients, it fails. The contribution is the
   evaluation design and the honest negative, not a working channel explainer.

EEG-CGS remains framing and scale only, never head-to-head.

## 4.2 What the numbers support
One paragraph, in this order: (1) the machinery works on synthetic ground truth; (2) on real seizures
the per-channel reconstruction anomaly agrees only weakly with a blind reader, driven by chb15;
(3) a fixed anatomical rule does significantly better; (4) no seizure-specific information.
Interpretation, stated as hypothesis: per-node reconstruction error measures a change in a node's
connectivity pattern, which need not coincide with where the scalp discharge is visible; the anomaly
is patient-specific (it matches in chb15 and chb13, is inverted in chb16 and chb18).
Consequence for the application: the channel panel is a view of model anomaly, not a guide to ictal
channels, and the report says so where the panel is described.

## 4.3 Defense questions to prepare (answers already fixed)
- *"Why exclude the generalized seizures?"* AUROC is undefined with no negative channel; focal-only
  evaluation is standard (SZTrack).
- *"You labelled it yourself — isn't that biased?"* Blind to every model output; protocol fixed and
  result approved by the supervisor; L2 and L3 are robust to a reader's anatomical habits because the
  prior already absorbs them.
- *"Couldn't a fixed rule do as well?"* That is exactly L2; the prior is reported.
- *"Isn't the map just the patient's usual pattern?"* That is L3 (and D7).
- *"Frontopolar channels are artifact-prone."* Yes; stated as a limitation, not corrected.
- *"So the attribution failed — why keep the panel in the application?"* It is titled as a
  reconstruction-anomaly view and never claims localization; the thesis shows exactly how far it can be
  trusted. Removing it would hide a measured limitation rather than disclose it.
- *"Could another aggregation or seed rescue it?"* Mean aggregation 0.585 and three other seeds
  0.572–0.577 were pre-registered sensitivities; none changes the verdict. Nothing was tuned (A4.9).
- *"Why is chb16 below chance?"* Its annotated temporal channels rank lowest while never-annotated
  channels rank highest; its seizures last 6–14 s. Exploratory observation, not a claim.
- *"Why did the labels change?"* The first annotation was machine-generated and recorded only dominant
  channels; the protocol always asked for every ictal channel (spec §3.1, unchanged since v2). The schema
  mismatch was documented as the reason for relabelling on 2026-09-02 (spec v3 §3.3, §9.5), on grounds of
  schema, not of the score. The final annotation was made blind to the model and approved before any
  score was computed against it, and the method was locked (A4) before the run.

## 4.4 Limitations (list, do not bury)
Spec §7, items 1–8.

## 4.5 Future work
An attribution designed for channels rather than read off the reconstruction branch (e.g. gradient- or
perturbation-based attribution on the detection score), pre-registered against the same four
references; onset-window aggregation (as SZTrack); a second independent reader; an external corpus
with channel labels.

---

# PART 5 — GUARDRAILS

**Never write:** localization, SOZ, onset zone · accuracy (use concordance) · any retired number ·
"provisional", "draft annotation", "language model" for the final annotation · a p-value on G-S4′ ·
spread as a classifier · a head-to-head comparison with EEG-CGS · a result for chb06's channels.

**Always write:** blind, single annotator, supervisor-approved · 62 focal / 14 generalized · the prior
(0.7387) beside the model's AUROC · the synthetic ceiling beside the real value · chb15's 32 % share and
the 0.5011 without it · "pre-registered negative" for L2/L3.

**If a number is needed that is not here:** read it from `results/attribution_v7/` (label-scored) or
`results/attribution_v6/` (label-free). Never estimate, never carry one over from a chat transcript.
