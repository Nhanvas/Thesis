# ATTRIBUTION_SPEC — Channel Attribution (v3, EXECUTED)

> **Single source for the channel-attribution study.** Supersedes v2 (Vietnamese) and, before it, the
> dominant-channel + MAP@K framework. Self-contained: a later session can execute or defend this
> chapter from this file alone, without re-deriving context.
>
> **Status 2026-09-02 (rev. B):** problem / method / metrics **LOCKED**. Machinery validation **COMPLETE and
> label-free** (not provisional). Results against labels are **PROVISIONAL** and, more importantly,
> **answer a narrower question than §3.2 specifies** — the label file on disk is a *dominant-channel*
> annotation (1–2 channels per seizure), not the full ictal-channel set. See §3.3 and §9.3.
>
> **Framing, non-negotiable:** this is **XAI for the GAE reconstruction branch**. It is NOT seizure
> localization, NOT SOZ identification, NOT onset-channel detection.

---

## 0. TL;DR

- **Question.** For each seizure the GAE produces 18 per-channel anomaly scores. Do the channels a
  reader marked as ictal score higher than the ones they did not? → per-channel binary classification.
- **Score.** Per-node GAE reconstruction error → robust-z against the subject's own interictal
  baseline → one vector `s ∈ ℝ¹⁸` per seizure. No retraining, no new model.
- **Headline metrics.** macro-AUROC + macro-AUPRC across seizures, bootstrap CI, permutation null.
- **Verified.** The scoring machinery is provably correct: synthetic injection with exact ground truth
  gives a clean null (0.4912) and a clean ceiling (0.9818), monotone in between.
- **Measured.** macro-AUROC 0.6497 [0.5663, 0.7390], p_perm = 0.001, on the 36 seizures that carry a
  channel annotation.
- **Caveat that governs the whole chapter.** Those annotations name **1–2 dominant channels**, not the
  ictal-channel set §3.2 asks for (mean |S| = 1.31; 25 seizures with 1 channel, 11 with 2, 40 with none).
  The question actually scored is *"does the GAE rank the reader's lead channel first?"* — the retired
  dominant-channel framing, not per-channel binary classification.
- **Blocked.** Those labels are near-constant within a subject (Jaccard 0.8879) — a mechanical
  consequence of naming 1–2 channels from one anatomical focus. Per-seizure attribution therefore
  cannot be separated from a subject-level channel prior.
- **Negative.** The spread (entropy) metric for focal-vs-generalized does not work. Reported honestly.

---

## 1. PROBLEM (locked)

For **every one of the 76 TEST seizures** (see D3 — not conditioned on detector success), rank the 18
bipolar scalp channels by GAE anomaly and test whether that ranking separates reader-marked ictal
channels from the rest.

Framing is **post-hoc review support** — indicating which channels carry an ictal-looking pattern so a
clinician can review faster. It is not surgical localization.

**Comparator framework:** EEG-CGS (Ho & Armanfard, AAAI 2023) — unsupervised GNN-autoencoder anomalous
**channel** detection, scored per channel against dataset channel labels. We differ in three ways:
(a) the score is the plain reconstruction-z of our detector's GAE, with no contrastive head;
(b) the dataset is CHB-MIT, which has **no** channel labels, so we construct them;
(c) labels come from a reading pass, not from a pre-annotated corpus.

**Scientific contribution.** CHB-MIT provides onset/offset **times** only. Most interpretability work on
CHB-MIT validates qualitatively ("the saliency looks like the known focus"). This study contributes
(i) a channel-level ictal annotation set over CHB-MIT and (ii) a **quantitative** per-channel attribution
evaluation with a permutation null and a synthetic upper bound — alongside EEG-CGS (quantitative but on
pre-labelled TUSZ) and SZTrack/DeepSOZ (supervised localization against clinical SOZ).

---

## 2. SCORE

**Input.** `data/pernode_v2/seed{N}/{subj}_{interictal|ictal}_pernode.npy`, shape `[n_win, 18]` —
per-window per-node GAE reconstruction error `r_i(w)`. Regenerate with
`python src/attribution_pipeline.py dump --seed 42`.

**Robust-z against the subject's own interictal baseline:**
```
med_i     = median_w r_i(w)                 over interictal
mad_i     = median_w |r_i(w) − med_i| + 1e-9  over interictal
zwin_i(w) = (r_i(w) − med_i) / mad_i
```

**Aggregation over the windows of one seizure:**
- **PRIMARY (pre-registered):** `s_i = p95_w |zwin_i(w)|` — ictal involvement is a *peak* effect; a
  channel need only be ictal for part of the seizure.
- **Sensitivity:** `s_i = mean_w |zwin_i(w)|`.

**Channel order (fixed, index 0..17):**
```
 0 FP1-F7   1 F7-T7   2 T7-P7   3 P7-O1     left temporal
 4 FP1-F3   5 F3-C3   6 C3-P3   7 P3-O1     left central
 8 FP2-F4   9 F4-C4  10 C4-P4  11 P4-O2     right central
12 FP2-F8  13 F8-T8  14 T8-P8  15 P8-O2     right temporal
16 FZ-CZ   17 CZ-PZ                          midline
HEMI = L×8, R×8, M×2
```

**Test-set discipline.** The score comes from the canonical seed-42 GAE. No threshold or aggregation is
selected on the 8 TEST subjects. Aggregation (p95) is pre-registered. Operating-point thresholds, if
used, are fixed on VAL.

---

## 3. LABELS

### 3.1 Convention
For each seizure, list every channel carrying a **clear, strong** ictal discharge (rhythmic evolution,
sharp-and-slow, evolving low-voltage fast) at any point in the seizure.
- **Counts:** genuine rhythmic ictal evolution, even if it joins late.
- **Does not automatically count:** attenuation/suppression only, artifact, or a single coincident
  transient → `uncertain` or omitted.
- No seizure may be 18/18, otherwise AUROC is undefined.
- `early_ictal` is optional metadata for lateralisation. **It is not SOZ.**

### 3.2 Schema — `results/attribution_v6/labels/ictal_channels_FINAL.csv`
```
subject, seizure_idx, onset_s, ictal_channels, uncertain_channels, flags, focal_generalized
```
`ictal_channels` uses `|` as separator in the current DRAFT file. `uncertain_channels` and
`flags: artifact:*` channels are masked out of both `y` and `s` before scoring.

### 3.3 Current label file — DRAFT, PROVISIONAL, and NOT the §3.2 schema

`results/attribution_v6/labels/ictal_channels_DRAFT.csv`, produced by
`python src/attribution_pipeline.py labels`. It is a **deterministic, verbatim conversion** of
`results/attribution_v5/labels/labels_ALL_FINAL.csv` (the v5 reader pass): the channel set is copied
unchanged, and an empty entry whose note reads DIFFUSE becomes `generalized`. No new labelling was
performed and nothing was reconstructed from memory or chat history.

Alignment gate: all 76 rows matched `seizure_blocks.csv` on (`edf_file`, `onset_s`).

> ⚠️ **SCHEMA MISMATCH — read this before interpreting any label-scored number.**
> The source column in the v5 file is named **`dominant_ch`**. The reader recorded the *leading*
> channel(s), not every channel carrying ictal discharge. Measured distribution over 76 seizures:
>
> | channels labelled | 0 (DIFFUSE) | 1 | 2 |
> |---|---|---|---|
> | seizures | 40 | 25 | 11 |
>
> Mean |S| over the 36 labelled seizures = **1.31** (prevalence 0.073). No seizure has more than 2.
>
> This is **not** the §3.2 ictal-set schema. The AI-draft described in earlier versions of this spec
> (~13 channels per seizure for chb03, etc.) **never existed on disk** — it was a plan, not a file, and
> was correctly never reconstructed from memory.
>
> **Consequence.** Everything scored against this file answers *"does the GAE rank the reader's
> dominant channel first?"* — the framing this spec formally **retired** in §10. AUROC remains
> well-defined (1–2 positives against 16–17 negatives) and the numbers in §9.3 are correct, but they
> do not answer the §3.2 question. Say so wherever they appear.

**Composition: 36 with a dominant channel / 40 DIFFUSE.** Per subject — the AUROC-eligible set:

| subject | chb03 | chb06 | chb13 | chb14 | chb15 | chb16 | chb17 | chb18 | total |
|---|---|---|---|---|---|---|---|---|---|
| labelled seizures | 6 | **0** | **0** | 3 | **20** | 1 | 3 | 3 | **36** |

### 3.4 focal vs generalized
`generalized` when the reader recorded no localisable lead channel (DIFFUSE), else `focal`. The v2 rule
"generalized if |S| ≥ 12" was never reachable: no seizure has |S| ≥ 3 under the current schema.
Note that "focal" here means *a lead channel was identifiable*, not *the seizure was anatomically
focal* — under a §3.2-conformant relabelling many of these seizures would carry large channel sets.

---

## 4. METRICS (locked)

Per seizure: `y ∈ {0,1}¹⁸`, `s ∈ ℝ¹⁸`. Mask `uncertain` and `flags: artifact:*` from both.

### 4.1 PRIMARY — threshold-free
macro-AUROC and macro-AUPRC **averaged across seizures** (never pooled over channel×seizure — z scales
differ per seizure). Chance = 0.5 and prevalence respectively. Mean ± bootstrap CI (1000 resamples over
seizures).

### 4.2 Operating point (secondary, for the EEG-CGS comparison)
τ fixed on VAL pseudo-seizure blocks at Specificity = 0.90, then applied unchanged. Comparator bar
(EEG-CGS Table 4, TUSZ, unsupervised): Precision 0.70 · F1 0.55 · Sensitivity 0.43 · Specificity 0.78 —
for scale only, not a like-for-like comparison. **Not yet computed:** blocked behind label freeze, since
an operating point on near-constant labels would not mean anything (§9.3).

### 4.3 Ranking (secondary) — Recall@|S| and MAP.

### 4.4 Null (mandatory)
Permute `s` across channels within each seizure, keeping `y`; 1000 iterations; report null mean and
p-value. This is stronger evidence than comparing to 0.5.

### 4.5 Stratification (mandatory)
By focal/generalized; per subject with **chb06 excluded from the headline**; AUROC vs |S| scatter.
For generalized seizures, localization is not forced — the intended measure was `spread`
(normalised entropy of `s`). **See §9.4: this measure does not work.**

### 4.6 Synthetic sanity check — run before any real label is scored.

### 4.7 Secondary internal validity
C1 consistency (within- vs across-subject ranking similarity) and lateralisation index. The old
eigencentrality-convergence framework is retired.

---

## 5. WEB DEMO (SzScan) tie-in
Per seizure: timeline (WHEN, from PELT) + 18-channel heat map (WHERE, from `s`). Guardrails from
`docs/demo/WEB_DEMO_SPEC_v4.md`: PROVISIONAL, no real-time claim, no SOZ claim, 8 TEST subjects only,
precomputed. Given §9.3, the demo must label the channel view **"channels with ictal-like reconstruction
anomaly"** and must not imply per-seizure localisation.

---

## 6. COMPARATORS
- **EEG-CGS** — Ho & Armanfard, AAAI 2023. Framework and metrics follow this paper. Bar 0.70/0.55/0.43/0.78.
- **SZTrack** — Craley et al., PLOS One 2022. Channel-wise CNN+BLSTM, scalp seizure tracking.
- **DeepSOZ** — MICCAI 2023. Supervised transformer + attention-MIL SOZ localization.
- **Wong et al.**, BSPC 2025 — channel-annotated DL + DeepSHAP (Sen 0.59).
- **Grattarola et al.**, ESWA 2022 — attention-GNN iEEG, AP@K vs SOZ.
- **Tang et al.**, ICLR 2022 — self-supervised DCRNN on TUSZ, occlusion localization.
- **AR2 (Le et al.)** — inter-reader agreement on onset localization is low (ICC 0.15–0.26): the basis
  for framing this as concordance/plausibility rather than accuracy.
- **CHB-MIT** (Shoeb) — onset/offset times only, no channel or SOZ labels.

> Citations are from the project's reference sheet, not from a live search. Verify each before the report.

---

## 7. LIMITATIONS
1. Labels are an AI draft, not blind, not supervisor-frozen. Authority rests with the supervisor.
2. Inter-reader agreement on localization is low → concordance, never "accuracy".
3. CHB-MIT has no channel/SOZ ground truth; these labels annotate scalp involvement.
4. chb06 (and partly chb16) are signal-limited: noisy background, symmetric spread. chb06 contributes
   0 focal seizures and is excluded from the headline.
5. p95 aggregation and τ are pre-registered choices; sensitivity with mean aggregation is reported.
6. **chb15 supplies 20 of 36 focal seizures (56%).** No headline over the focal set is a balanced
   8-subject result.
7. **The label file uses a narrower schema than §3.2** — 1–2 dominant channels, not the ictal-channel
   set (§3.3). Every label-scored number answers the dominant-channel question, not per-channel binary
   classification. This is the single most important caveat in the chapter.
8. **The labels cannot test per-seizure attribution at all** (§9.3) — a mechanical consequence of #7.
9. The spread metric for focal/generalized is a methodological negative (§9.4).

---

## 8. EXECUTION — how to reproduce

All steps are sub-commands of the single module `src/attribution_pipeline.py`.

```bash
python src/verify_provenance.py                     # MANDATORY session gate, ~20 s, must print PASS
python src/attribution_pipeline.py dump --seed 42   # and --seed 1 / 2 / 3
python src/attribution_pipeline.py blocks \
    --edf_root    "F:/Study/Thesis/Dataset/CHB-MIT" \
    --summary_dir "F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary"
python src/attribution_pipeline.py labels
python src/attribution_pipeline.py all              # score, diag, synth, spread, eval, labeldiv
```

Outputs, all in `results/attribution_v6/`:

| file | content |
|---|---|
| `seizure_blocks.csv` | 89 seizures (76 TEST + 13 VAL): edf, onset, offset, n_windows, row range |
| `ictal_row_to_seizure.csv` | 1420 rows: exact ictal-array row → seizure map |
| `labels/ictal_channels_DRAFT.csv` | 76 labels, §3.2 schema, PROVISIONAL |
| `attribution_scores.csv` | 10944 rows = 4 seeds × 76 seizures × 2 aggregations × 18 channels |
| `attribution_diagnostics.csv` | per-subject top-1 concentration vs random null |
| `synthetic_sanity.csv` | 50 cells × 2 panels: G-S1/G-S2/G-S3 |
| `synthetic_spread.csv` | G-S4' after the D6.1 construction fix |
| `attribution_perseizure.csv` | per-seizure AUROC / AUPRC / Recall@\|S\| / spread / control |
| `attribution_summary.csv` | all panels with CIs, control, null, p-values |
| `label_diversity.csv` | within-subject label Jaccard — the limitation evidence |

**Report figures** — `python src/figures/attribution_figures.py` → `figures/attribution/`.
Reads the committed CSVs only; recomputes nothing, so a figure cannot disagree with the tables above.

| output | label-free? |
|---|---|
| `attribution_fig1_synthetic.png` — macro-AUROC vs α, VAL + TEST | ✅ final |
| `attribution_fig2_seed_robustness.png` — ranking agreement across GAE seeds | ✅ final |
| `attribution_fig3_rank_heatmap.png` — per-seizure channel rank, 76 × 18 | ✅ final |
| `attribution_fig4_per_subject_forest.png` — per-subject AUROC ± CI vs macro and control | ❌ PROVISIONAL |
| `attribution_top3_channels.csv` — appendix, top-3 channels per seizure | ✅ final |

**Window-count sanity (must match).** Ictal windows per subject:
chb03 106 · chb06 45 · chb13 144 · chb14 49 · chb15 515 · chb16 28 · chb17 74 · chb18 83 (TEST = 1044);
chb10 117 · chb11 204 · chb22 55 (VAL = 376). Total 1420.
TEST windows per seizure: min 2, p25 5, median 12, max 52; 3 seizures have < 3 windows.

---

## 9. RESULTS

> **Provenance for every number below.** Checkpoint `data/models_retrain/gae_joint_seed42.pt`,
> sha256 `dea06cb533df1c7d0520ae21c4cbb1b8a938297f937366bc9915b040726ea108`, bias fingerprint 1.1597,
> chb13 recon AUROC 0.8319, verified corr = 1.0000000 on 16/16 committed TEST zrecon arrays.
> **Never identify this checkpoint by filename or by the constants 0.8676 / 0.836** — those are the
> pre-rebuild §0 model, quarantined in `archive/pre_rebuild_s0/`, which correlates 0.987–0.999 with the
> canonical output and is therefore close enough to pass a careless check and be wrong.

### 9.1 Machinery validation — label-free, NOT provisional

Synthetic injection: pseudo-seizure = contiguous interictal block, length drawn from the real
76-seizure length distribution; `r_i ← α·r_i` on |S| random channels; robust-z baseline computed on
interictal **excluding** the block; p95 aggregation; RNG seed 42; R = 200 per cell.

macro-AUROC, **VAL** panel (gate):

| α \\ \|S\| | 1 | 2 | 4 | 8 | 12 |
|---|---|---|---|---|---|
| 1.00 | **0.4912** | — | 0.5087 | 0.4911 | 0.5257 |
| 1.25 | 0.6962 | 0.6942 | 0.7079 | 0.6973 | 0.6924 |
| 1.50 | 0.8247 | 0.8367 | 0.8279 | 0.8362 | 0.8260 |
| 2.00 | 0.9547 | 0.9291 | 0.9472 | 0.9409 | 0.9504 |
| 3.00 | **0.9818** | 0.9917 | 0.9835 | 0.9828 | 0.9881 |

TEST panel (confirmatory, nothing selected on it) reproduces this within ~0.03 at every cell.

**Pre-registered gates:**

| gate | criterion | measured | verdict |
|---|---|---|---|
| G-S1 negative control | α=1.0, \|S\|=1 → AUROC ∈ [0.45, 0.55] | 0.4912 | **PASS** |
| G-S2 upper bound | α=3.0, \|S\|=1 → AUROC ≥ 0.95 | 0.9818 | **PASS** |
| G-S3 monotone in α | at every \|S\| | holds | **PASS** |
| G-S4' spread (after D6.1) | spread(\|S\|=18) > spread(\|S\|=1), p < 0.05 | 0.9755 vs 0.9644, p = 8.9e-11 | **PASS** |

**Permutation null mean stayed within 0.4990–0.5013 across all 50 cells.** The machinery invents no
signal. Sensitivity: a +25 % reconstruction-error increase is already detected at AUROC ≈ 0.70.

**Seed robustness (D4).** Across GAE seeds {42, 1, 2, 3}: channel-ranking Spearman **0.970 ± 0.026**;
top-1 channel agreement 0.873; all three other seeds agree with seed 42 on 74 % of seizures.

### 9.2 Label-free diagnostics

**No global channel bias.** Top-1 frequency over 76 seizures (seed 42, p95) spreads over all 18 channels;
the most frequent is P3-O1 at 14/76 (18 %; random expectation 4.2). Across-subject mean pairwise
Spearman = **−0.012**.

**Subject-level concentration** (top-1 share vs a 2000-draw random null):

| subject | n | distinct top-1 | max share | null p95 | verdict |
|---|---|---|---|---|---|
| chb03 | 7 | 5 | 0.429 | 0.429 | ok |
| chb06 | 10 | 7 | 0.300 | 0.300 | ok |
| chb13 | 12 | 6 | 0.417 | 0.333 | **CONCENTRATED** |
| chb14 | 8 | 5 | 0.250 | 0.375 | ok |
| chb15 | 20 | 9 | 0.500 | 0.250 | **CONCENTRATED** |
| chb16 | 10 | 4 | 0.500 | 0.300 | **CONCENTRATED** |
| chb17 | 3 | 3 | 0.333 | 0.667 | ok |
| chb18 | 6 | 5 | 0.333 | 0.500 | ok |

**C1 consistency.** Within-subject mean pairwise Spearman 0.265 (413 pairs) vs across-subject −0.012
(3000 sampled pairs), Δ = +0.277. Rankings are subject-typical but **not** degenerate — 0.265 leaves
substantial per-seizure variation.

### 9.3 Against real labels — PROVISIONAL, and narrower than intended

> **Read §3.3 first.** These labels are dominant-channel (1–2 per seizure, mean 1.31), not the §3.2
> ictal set. The question actually scored is "does the GAE rank the reader's leading channel first?".

36 labelled seizures, seed 42, p95 aggregation. Δ = macro-AUROC − subject-constant control (D7).

| panel | n | macro-AUROC [95% CI] | AUPRC | R@\|S\| | control | Δ | p_perm |
|---|---|---|---|---|---|---|---|
| **all labelled (primary)** | 36 | **0.6497** [0.5663, 0.7390] | 0.3095 | 0.1389 | 0.7758 | −0.1261 | 0.0010 |
| excl. chb15 (D8) | 16 | 0.6267 [0.4912, 0.7545] | 0.3432 | 0.2188 | 0.6248 | +0.0020 | 0.0380 |
| chb15 only (D8) | 20 | 0.6681 [0.5368, 0.7934] | 0.2826 | 0.0750 | 0.8967 | −0.2286 | 0.0040 |
| n_windows ≥ 3 (D5) | 36 | 0.6497 [0.5478, 0.7384] | 0.3095 | 0.1389 | 0.7758 | −0.1261 | 0.0020 |
| mean aggregation | 36 | 0.6733 [0.5755, 0.7634] | 0.3856 | 0.1944 | 0.7887 | −0.1154 | 0.0010 |
| seed 1 / 2 / 3 | 36 | 0.6600 / 0.6491 / 0.6515 | — | — | — | −0.101 … −0.122 | ≤ 0.003 |

D5 note: all 36 labelled seizures have ≥ 3 windows, so the secondary panel coincides with the primary.

Per subject:

| subject | n | macro-AUROC [95% CI] | AUPRC | control | Δ | p_perm |
|---|---|---|---|---|---|---|
| chb03 | 6 | 0.8333 [0.6956, 0.9706] | 0.5840 | 1.0000 | −0.1667 | 0.0020 |
| chb14 | 3 | **0.2672** [0.1562, 0.4688] | 0.1565 | 0.3229 | −0.0558 | 0.9391 |
| chb15 | 20 | 0.6681 [0.5323, 0.7840] | 0.2826 | 0.8967 | −0.2286 | 0.0030 |
| chb16 | 1 | 0.4688 (no CI) | — | — | — | — |
| chb17 | 3 | 0.6042 [0.4062, 0.7812] | 0.2168 | 0.6250 | −0.0208 | 0.2358 |
| chb18 | 3 | 0.6483 [0.4062, 0.8824] | 0.2407 | 0.2904 | +0.3578 | 0.1838 |

**What is established.** Ranking the reader's dominant channel is above chance — AUROC 0.6497 with
p_perm = 0.001, AUPRC 0.3095 against a prevalence of 0.073 (4.2×), stable across four GAE seeds and
both aggregations. chb14 sits **below** chance (0.2672, p = 0.94).

**What is NOT established, and why.** The subject-constant control (0.7758) beats the per-seizure score
(0.6497), Δ = −0.126. That reads as "no per-seizure information", but the labels cannot support the
reading:

| subject | n labelled | distinct label sets | mean Jaccard | union size |
|---|---|---|---|---|
| chb03 | 6 | 2 | 0.8333 | 2 |
| chb14 | 3 | 2 | 0.6667 | 2 |
| chb15 | 20 | **2** | 0.9053 | 2 |
| chb16 | 1 | — | — | 2 |
| chb17 | 3 | **1** | **1.0000** | 2 |
| chb18 | 3 | 3 | 0.1667 | 4 |

**Pooled within-subject Jaccard = 0.8879.** This is now mechanistically explained rather than
surprising: a 1–2 channel dominant label drawn from a patient's fixed anatomical focus is **almost
forced** to be constant within a subject. With `y` near-constant, averaging 19 other seizures wins on
noise reduction alone, whatever the per-seizure score contains. Corroborating: corr(y − ȳ, s − s̄) on
chb15 = **+0.089**, with only 2 distinct label sets across 20 seizures.

⇒ **With these labels, per-seizure attribution and a subject-level channel prior are not
distinguishable, and the §3.2 question is not tested at all.** State both; report neither reading as
the finding.

Figure 3 (`figures/attribution/attribution_fig3_rank_heatmap.png`) makes the subject-level prior
visible directly: the P3-O1 column is near-continuously top-ranked across all 20 chb15 seizures.

### 9.4 Methodological negative — spread does not measure localisation

`§4.5` proposed normalised entropy of `s` as the focal-vs-generalized measure. It fails twice:

- **Synthetic:** spread is **U-shaped in |S|** — 0.9644 (\|S\|=1) → 0.9567 → **0.9441 (\|S\|=4, minimum)**
  → 0.9503 (\|S\|=12) → 0.9755 (\|S\|=18). The α=1.0 no-injection cell has the highest spread of all
  (0.978). Entropy measures **uniformity**, not localisation: one high channel among 17 flat ones is
  still fairly uniform, whereas four high channels are maximally bimodal.
- **Real labels:** focal 0.9693 > generalized 0.9594, one-sided p = **0.984** — opposite to the hypothesis.

G-S4' passes only because it compares the two extremes (all-18 vs 1). For real seizures with
|S| ∈ [3, 12] the measure is not monotone and cannot classify. **Do not use spread for
focal/generalized.** Report as a methodological negative; the generalized branch of §4.5 needs a
different measure.

### 9.5 What to request from the supervisor (evidence-backed)

1. **The §3.2 schema, not dominant channels.** The current file lists 1–2 leading channels
   (mean |S| = 1.31, never more than 2). §3.2 asks for **every** channel carrying clear ictal
   discharge. This is the single change that would let the intended question be answered.
2. **Labels that differ between seizures of the same patient** — target within-subject Jaccard < 0.6.
   The current file is at 0.8879, which is a direct consequence of item 1.
3. **A verdict for chb06 and chb13.** Both are currently 100 % DIFFUSE and contribute **0** labelled
   seizures, so neither enters any headline. Either label them under §3.2 or confirm they are
   genuinely non-localisable on scalp.
4. **Acknowledgement of chb15 dominance** — it supplies 20 of 36 labelled seizures.

Until item 1 is met, the attribution chapter reports the label-free half as the result and the
label-scored half as a PROVISIONAL, narrower secondary analysis.

---

## 10. AMENDMENTS — pre-registered decisions

All of the following were written down **before** the corresponding numbers were seen.

### A2 (2026-09-01)
- **D1 — Regenerate, do not trust legacy dumps.** All `*_pernode.npy` predating this amendment are
  provenance-unknown. Per-node error is regenerated from the canonical checkpoint with a SHA-256
  manifest. *Outcome:* the legacy `data/pernode/` dumps were shown to come from the pre-rebuild §0
  model and are quarantined in `archive/pre_rebuild_s0/pernode/`.
- **D2 — Label source.** Results scored against the draft carry a PROVISIONAL banner. Official numbers
  require the supervisor's freeze. Draft labels must exist on disk with provenance; they are never
  reconstructed from memory or transcripts. *Outcome:* the on-disk file was found to be a
  **dominant-channel** annotation (1–2 channels), not the §3.2 ictal-channel set — see §3.3. The
  full-field draft described in v2 §3.3 did not exist on disk and was correctly **not** reconstructed;
  the cost of that discipline is that the label-scored half answers a narrower question, which is
  stated rather than hidden.
- **D3 — Seizure scope (amends §1).** PRIMARY = all 76 TEST seizures, not conditioned on CPD detection
  (attribution is XAI of the GAE branch, independent of the detector → avoids selection bias).
  SECONDARY = detected vs missed stratification.
- **D4 — Multi-seed.** Report seed 42 (primary) and seeds {1,2,3} (robustness), per RoR §7 precedent.
- **D5 — min_windows.** PRIMARY = all 76, no exclusion by window count; excluding after seeing the
  numbers is selection bias. SECONDARY = exclude the 3 seizures with `n_windows < 3`.
  *Outcome:* all 36 focal seizures have ≥ 3 windows, so the panels coincide.
- **D6 — Synthetic sanity check.** Design and gates G-S1…G-S4 as in §9.1. VAL is the gate; TEST is
  confirmatory only.
- **D6.1 — After G-S4 FAILED, recorded honestly.** G-S4 as originally written failed
  (spread(\|S\|=12) = 0.9548 < spread(\|S\|=1) = 0.9660, p = 1.00). Diagnosis: **|S|=12 is not a model
  of a generalized seizure** — the 6 remaining baseline channels make `s` bimodal and *lower* the
  entropy. Internal evidence: the α=1.0 no-injection cell has the highest spread in the table (0.978).
  Fix applied to the **synthetic construction only** — metric and threshold unchanged: generalized ≡
  |S| = 18, focal ≡ |S| ∈ {1,2}. Re-registered as G-S4'. G-S1/2/3 were unaffected and remained PASS.
- **D7 — Subject-constant baseline control.** For each seizure, compute `s_LOO` = mean `s` over the
  *other* seizures of the same subject, and score it with the same labels and metrics.
  Pre-registered reading: Δ ≤ 0 ⇒ report as a subject-level channel prior, not per-seizure attribution.
  *Outcome:* Δ = −0.126, **but the control turned out to be uninformative** — see §9.3. The
  pre-registered reading is therefore **not** applied, and the reason is stated rather than the
  conclusion being quietly changed.
- **D8 — chb15 dominance.** Report (a) all 36 focal, (b) excluding chb15, (c) full per-subject table.

### A3 (2026-09-02) — code consolidation
The nine scripts written on 2026-09-01 were merged into `src/attribution_pipeline.py` with
sub-commands. Verified byte-identical outputs on all 7 result CSVs before the old scripts were removed.
The originals remain recoverable at `git tag phase-c-final` and in the commit history.

---

## 11. FILE OPERATIONS — state as of 2026-09-02

**Canonical:**
- `src/attribution_pipeline.py` — the only attribution code.
- `src/verify_provenance.py` — session gate; regenerates `docs/PROVENANCE.md`.
- `src/labeling/label_eeg_pilot.py` — the EEG viewer that renders labelling images.
- `results/attribution_v6/` — all results.
- `results/attribution_v5/labels/labels_*_FINAL.csv` — **the reader labels. Irreplaceable. Never delete.**

**Archived (do not cite, do not run):**
- `archive/src_superseded/attribution_v5/` — the dominant-channel/MAP@K era scripts.
- `archive/attribution_superseded/attribution_c{1,2,3}.py` — the retired eigencentrality framework.
- `archive/pre_rebuild_s0/` — §0 model and its per-node dumps. Correlates 0.987–0.999 with canonical
  output; see the README there.
- `results/history_superseded/` — pre-rebuild attribution outputs.

**Retired numbers — never quote:** the dominant-channel MAP@K figures 0.262 / 0.303 belong to a
different problem formulation.
