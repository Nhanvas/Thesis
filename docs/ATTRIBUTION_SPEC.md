# ATTRIBUTION_SPEC — Channel Attribution (v4 rev. B, 2026-09-19 — method LOCKED, results FINAL)

> **Single source for the channel-attribution study.** Supersedes v3 rev. B (2026-09-02). Self-contained:
> a later session can execute or defend this chapter from this file alone.
>
> **Status 2026-09-18 (v4):**
> - **Ground truth is FINAL.** A human annotation of every TEST seizure, made from the raw 18-channel EEG
>   **blind to every model output**, listing every channel with clear ictal discharge (§3). Reviewed and
>   approved by the supervisor, who also fixed this labelling protocol. It replaces the earlier
>   machine-generated dominant-channel draft, which is retired and never scored again (§3.5).
> - **Method is LOCKED by Amendment A4 (§10), written before any label-scored number was produced.**
> - **Machinery validation (§9.1–§9.2) is label-free, FINAL, and unchanged.**
> - **Label-scored results (§9.3) are FINAL (run 2026-09-19, `git tag attribution-v7-results`).**
>   Verdict (§4.7): **L1 PASS (weak), L2 FAIL, L3 FAIL.** Every number from the retired draft labels
>   (0.6497, 0.3095, 0.7758, 0.8879, p = 0.984, …) is **retired** and must not be quoted anywhere.
>
> **Framing, non-negotiable:** this is **XAI for the GAE reconstruction branch**. It is NOT seizure
> localization, NOT SOZ identification, NOT onset-channel detection. Agreement with one reader is
> **concordance**, never accuracy.

---

## 0. TL;DR

- **Question.** For each seizure the GAE produces 18 per-channel anomaly scores. Do the channels the
  reader marked as ictal score higher than the ones they did not — and higher than a fixed anatomical
  rule would place them?
- **Score.** Per-node GAE reconstruction error → robust-z against the subject's own interictal
  baseline → p95 over the seizure's windows → one vector `s ∈ ℝ¹⁸` per seizure. Unchanged since v3.
- **Ground truth.** 76 seizures: **62 focal** (1–10 ictal channels, mean |S| = 4.55, prevalence 0.253)
  and **14 generalized** (all 18 channels ictal). AUROC is undefined when every channel is positive, so
  the 14 are excluded from every channel metric by construction, not by choice.
- **Three pre-registered claims, tested in order.**
  L1 above chance (permutation null) → L2 above an anatomical prior (LOSO channel frequency) →
  L3 seizure-specific (matched vs swapped within subject).
- **Why L2 is mandatory.** A rule that never looks at the EEG — rank channels by how often they are
  ictal in *other* patients — already reaches macro-AUROC **0.7387** on these labels (label-only
  measurement, §3.4). An attribution that does not beat it has no triage value beyond that rule.
- **Verified label-free.** Synthetic null 0.4912, ceiling 0.9818, monotone; seed Spearman 0.970 ± 0.026.
- **Negative, kept.** Normalised entropy (spread) does not measure localisation (synthetic U-shape).
- **RESULT (§9.3).** macro-AUROC **0.5694** [0.5097, 0.6321], p = 0.001 over 62 focal seizures —
  above chance, but **0.1694 below the anatomical prior** (CI [−0.2553, −0.0804]) and with **no
  seizure-specific information** (L3 p_holm = 0.6753). Without chb15 it is **0.5011** (p = 0.49).
  The channel-level reconstruction anomaly does not track where a blind reader sees ictal discharge,
  beyond a patient-specific agreement in a minority of patients.

---

## 1. PROBLEM (locked)

For the **62 focal TEST seizures** (all 76 are scored; the 14 generalized ones have no defined channel
metric, §3.4), rank the 18 bipolar scalp channels by GAE anomaly and test whether that ranking
separates reader-marked ictal channels from the rest. Not conditioned on detector success (D3).

Framing is **post-hoc review support** — indicating which channels carry an ictal-looking pattern so a
reviewer can look there first. It is not surgical localization.

**Comparator framework:** EEG-CGS (Ho & Armanfard, AAAI 2023) — unsupervised GNN-autoencoder anomalous
**channel** detection. We differ in three ways: (a) the score is the plain reconstruction-z of our
detector's GAE, with no contrastive head; (b) CHB-MIT has **no** channel labels, so we construct them;
(c) the labels come from one blind reading pass, not a pre-annotated corpus. Framing and scale only,
never a head-to-head comparison.

**Scientific contribution.** CHB-MIT provides onset/offset **times** only. This study contributes
(i) a blind, supervisor-approved, channel-level ictal annotation of the 76 CHB-MIT test seizures and
(ii) a **quantitative** per-channel attribution evaluation with a permutation null, a synthetic upper
bound, an anatomical-prior baseline and a within-patient specificity test.

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

### 3.1 Convention (unchanged since v2, fixed by the supervisor)
For each seizure, list every channel carrying a **clear, strong** ictal discharge (rhythmic evolution,
sharp-and-slow, evolving low-voltage fast) at any point in the seizure.
- **Counts:** genuine rhythmic ictal evolution, even if it joins late.
- **Does not automatically count:** attenuation/suppression only, artifact, or a single coincident
  transient → omitted.
- A seizure whose discharge involves all 18 channels is recorded as **generalized** ("Diffuse (18
  channels)"). It carries no channel contrast, so it is excluded from every channel metric (§3.4).
- **Not SOZ, not onset.** The convention covers involvement at any time, which matches the p95
  aggregation of §2 (peak involvement over the whole seizure).

### 3.2 Schema — `results/attribution_v7/labels/ictal_channels_FINAL.csv`
```
subject, seizure_idx, edf_file, onset_s, n_ictal, ictal_channels, focal_generalized, label_source
```
`ictal_channels` uses `|` as separator, channel names exactly as §2. `label_source` =
`human_blind_supervisor_approved_2026-09`. `uncertain_channels` and `flags` columns of v3 are dropped:
the final annotation uses neither, so no masking is applied.

### 3.3 The final annotation — provenance
- **Source file:** `Channel label.md` (Markdown, one block per subject, one line per seizure), copied
  verbatim to `results/attribution_v7/labels/source/Channel_label_approved.md` with its SHA-256 in
  `results/attribution_v7/labels/source/SHA256.txt`. The source is never edited; the parser corrects
  in code and logs every correction.
- **Reader and blinding:** annotated by the thesis author from the raw 18-channel EEG of each seizure,
  **without viewing any model output** (no score, rank, heat map or top-channel table). Reviewed and
  approved by the supervisor as the ground truth of record.
- **Known source defect, handled by the parser:** chb15 seizure 0 lists `P7-O1` twice → de-duplicated
  (set semantics), |S| = 4. Logged.
- **Index alignment:** `seizure k` of subject X is the k-th seizure of X in `seizure_blocks.csv` order.
  Verified by gate G-L1 (§8) before any scoring.

### 3.4 Composition (label-only measurement, 2026-09-18, to be reproduced by `labels` / `labeldiv`)

| subject | chb03 | chb06 | chb13 | chb14 | chb15 | chb16 | chb17 | chb18 | total |
|---|---|---|---|---|---|---|---|---|---|
| seizures | 7 | 10 | 12 | 8 | 20 | 10 | 3 | 6 | **76** |
| generalized (18/18) | 3 | **10** | 1 | 0 | 0 | 0 | 0 | 0 | **14** |
| focal (scored) | 4 | **0** | 11 | 8 | 20 | 10 | 3 | 6 | **62** |

- |S| over the 62 focal seizures: 1–10, mean **4.55**, macro prevalence **0.253**.
  Counts by |S|: 1→3, 2→11, 3→7, 4→9, 5→9, 6→15, 7→2, 8→4, 9→1, 10→1.
- **chb06 contributes no focal seizure** (all ten generalized) and is absent from every channel metric.
  **chb15 supplies 20 of 62 (32 %).**
- **Within-subject label similarity:** pooled pairwise Jaccard **0.5144** (mean over seizure pairs,
  the same definition as the retired 0.8879). Per subject: chb03 0.944 · chb13 0.524 · chb14 0.671 ·
  chb15 0.454 · chb16 0.653 · chb17 0.524 · chb18 0.365.
- **Channel frequency across the 62 focal seizures:** T7-P7 45 · FP2-F4 33 · FP2-F8 30 · FP1-F7 29 ·
  F7-T7 28 · T8-P8 28 · F8-T8 27 · FP1-F3 24 · F3-C3 11 · P7-O1 10 · P3-O1 9 · F4-C4 7 · P8-O2 1 ·
  **C3-P3, C4-P4, P4-O2, FZ-CZ, CZ-PZ: 0.** The four frontopolar channels carry ≈ 41 % of all labels.
- **Anatomical prior (L2 baseline), label-only:** macro-AUROC **0.7387**, macro-AUPRC 0.5065.
- **Oracle within-subject label prior** (other seizures' *labels*, same subject, leave-one-out):
  macro-AUROC 0.925. Not a baseline — it uses labels — but it shows the labels are still strongly
  patient-consistent, which is why D7 alone cannot settle the per-seizure question (§4.4).

Generalized ≡ the reader recorded all 18 channels. Focal ≡ any proper subset. This replaces the v3
definition ("no localisable lead channel"), which belonged to the retired draft.

### 3.5 Retired: the machine-generated dominant-channel draft
`results/attribution_v6/labels/ictal_channels_DRAFT.csv` (from `attribution_v5/labels/labels_ALL_FINAL.csv`)
was an automatically generated annotation of 1–2 **dominant** channels per seizure (40 DIFFUSE / 25 /
11), never reviewed by a human reader. It answered a narrower question than §3.1 and is **retired**:
it is not scored, and none of its numbers appear in the report. It stays on disk as provenance
(`attribution_v5/labels/labels_*_FINAL.csv` remains irreplaceable — never delete). The report states
the history in one sentence (§7 of the report pack); it does not report the old numbers.

---

## 4. METRICS (locked by A4)

Per focal seizure: `y ∈ {0,1}¹⁸`, `s ∈ ℝ¹⁸` (seed 42, p95). No masking.

### 4.1 L1 — PRIMARY: does the ranking beat chance?
macro-AUROC **averaged across the 62 focal seizures** (never pooled over channel × seizure — z scales
differ per seizure). 95 % CI: percentile bootstrap over seizures, 1000 resamples, RNG 42.
**Null:** permute `s` across channels within each seizure, keep `y`; 1000 iterations; p = (1 + #{null ≥
obs}) / 1001. **Claim if p < 0.05.**

### 4.2 L2 — does it beat an anatomical prior?
For seizure k of subject u: `prior_c` = number of focal seizures of the **other seven TEST subjects**
whose label contains channel c (leave-one-subject-out; label-only; ties by average rank).
Statistic Δ_prior = macro-AUROC(s) − macro-AUROC(prior) over the same 62 seizures.
95 % CI by **paired** bootstrap over seizures (1000, RNG 42). **Claim if the CI excludes 0 and Δ > 0.**
Precedent: the "center" baseline of the pointing game (Zhang et al., IJCV 2018) — an attribution map is
judged against a map that ignores the input.

### 4.3 L3 — is the map specific to the seizure?
Within each subject with ≥ 2 focal seizures (all seven with focal seizures qualify):
`matched_k = AUROC(s_k, y_k)`, `swapped_k = mean_{j≠k, same subject} AUROC(s_j, y_k)`.
Statistic T = mean over the 62 seizures of (matched_k − swapped_k).
**Null:** within each subject, randomly permute which score vector is paired with which label vector;
recompute T; 1000 iterations; one-sided p. **Claim if p < 0.05.**
Why this test and not D7 alone: `swapped` uses single other seizures, so it has no noise-averaging
advantage; it asks directly whether seizure k's map fits seizure k's label better than a sibling
seizure's map does. Seizures of one subject with identical labels make T conservative, not liberal.

### 4.4 D7 — subject-constant control (pre-registered 2026-09-01, reported as registered)
`s_LOO` = mean `s` over the other focal seizures of the same subject; scored with the same metrics.
Δ_D7 = AUROC(s) − AUROC(s_LOO). Registered reading: Δ_D7 ≤ 0 ⇒ no evidence of seizure-specific
information beyond a subject-level channel prior. **A4 addition:** the v3 exemption (control
"uninformative") is **not** re-used — Jaccard is now 0.514, below the §9.5 target of 0.6. If D7 and L3
disagree, both are reported, and the per-seizure claim follows L3, because averaging still favours the
control while labels remain patient-consistent (oracle 0.925, §3.4).

### 4.5 Multiplicity
L1 is the gatekeeper. L2 and L3 are interpreted only if L1 passes, with **Holm** correction over
{L2, L3} at α = 0.05. Everything else in §4.6 is descriptive.

### 4.6 Secondary / descriptive (no claims)
macro-AUPRC with macro prevalence (0.253) and their ratio; Recall@|S|; per-subject table (n, AUROC, CI,
prior AUROC); panel without chb15 (D8); panel without seizures of < 3 windows (D5); mean
aggregation; seeds 1/2/3 (D4).

### 4.7 Pre-registered interpretation

| outcome | sentence the report uses |
|---|---|
| L1 fails | Channel-level reconstruction anomaly does not track reader-marked ictal channels. Reported as a negative. |
| L1 passes, L2 fails | The anomaly map concentrates on ictal channels **at the level of an anatomical prior**; no triage value beyond "look at the temporal and frontopolar chains first" is shown. |
| L1, L2 pass, L3 fails | The map carries **patient-level** information beyond the anatomical prior, but no evidence of seizure-specific information. |
| L1, L2, L3 pass | The map carries seizure-specific channel information beyond both the prior and the patient's own pattern. Strongest claim available; still concordance, not accuracy. |
| L1, L3 pass, L2 fails | Seizure-specific information exists, but on average the map does not rank channels better than the anatomical prior. Both stated. |

### 4.8 Dropped in v4 (with reason)
- **Operating point τ / EEG-CGS P-F1-Sens-Spec (v3 §4.2).** VAL has no channel labels, and the
  comparison is not like-for-like anyway. EEG-CGS stays as framing only.
- **Spread on real labels (v3 §4.5).** The synthetic grid already shows the measure is invalid (§9.4).
  Only the label-free synthetic negative is reported; Figure 3.10 becomes synthetic-only.
- **Any measure for the 14 generalized seizures.** None is defined; they are counted and shown on the
  rank heat map, nothing more. Precedent: SZTrack evaluated localization on focal patients only and
  excluded patients with indeterminate onset (Craley et al., PLOS One 2022).
- **MAP, C1 consistency, lateralisation index** — not needed for any claim.

### 4.9 Synthetic sanity check — done (§9.1). Not rerun: it does not depend on labels.

---

## 5. WEB DEMO (SzScan) tie-in
Per detected event: 18-channel view from `s`, titled **`Channel-level reconstruction anomaly — Event N`**
(decided 2026-09-03). No attribution metric appears in the UI; no SOZ or localization claim. The §9.3
result decides only the wording of the thesis, not the UI.

---

## 6. COMPARATORS
- **EEG-CGS** — Ho & Armanfard, AAAI 2023. Framework and scale only. Bar 0.70/0.55/0.43/0.78 (TUSZ).
- **SZTrack** — Craley et al., PLOS One 2022. Scalp, channel-wise; localization evaluated on focal
  patients only (generalized epilepsy and indeterminate-onset patients excluded); localization clipped
  to −15…+30 s around onset to reduce eye and muscle confounds.
- **Pointing game** — Zhang et al., IJCV 2018 (ECCV 2016): the attribution-vs-center-baseline precedent
  for L2. Rebuffi et al., CVPR 2020 report Grad-CAM below the center baseline at most layers.
- **DeepSOZ** — MICCAI 2023. Supervised SOZ localization (framing only).
- **Wong et al.**, BSPC 2025 · **Grattarola et al.**, ESWA 2022 · **Tang et al.**, ICLR 2022 — framing.
- **Le et al. (AR2)** — low inter-reader agreement on onset localization (ICC 0.15–0.26): the basis for
  "concordance, not accuracy".
- **CHB-MIT** (Shoeb) — onset/offset times only, no channel or SOZ labels.

> EEG-CGS, SZTrack and the pointing-game papers were checked against the source on 2026-09-18. Verify
> the rest before citing.

---

## 7. LIMITATIONS
1. **One reader.** Blind to the model and approved by the supervisor, but a single read; inter-reader
   agreement on localization is low → concordance, never accuracy.
2. **Scalp involvement, not SOZ.** CHB-MIT has no channel or SOZ ground truth.
3. **Frontopolar channels carry ≈ 41 % of labels** and are the most artifact-prone; ictal windows are
   not artifact-rejected (by design, detection pipeline). Reader and model may both respond to
   eye/muscle activity there. Not corrected; stated.
4. **Five channels are never labelled** (C3-P3, C4-P4, P4-O2, FZ-CZ, CZ-PZ). Part of any AUROC comes
   from ranking these low — exactly what L2 controls for.
5. **chb06 is untested** (all generalized); chb15 supplies 32 % of the focal set.
6. p95 aggregation is pre-registered; mean aggregation is reported as sensitivity.
7. The spread metric is a methodological negative (§9.4).
8. Reconstruction anomaly relative to interictal is not the same as ictal activity; artifact and state
   changes also raise it.

---

## 8. EXECUTION — how to reproduce

```bash
python src/verify_provenance.py                          # MANDATORY session gate, must print PASS
python src/attribution_pipeline.py labels --source md    # parser + gate G-L1 → results/attribution_v7/labels/
python src/attribution_pipeline.py eval  --labels v7     # L1/L2/L3/D7 + descriptive → results/attribution_v7/
python src/attribution_pipeline.py labeldiv --labels v7  # composition + Jaccard → results/attribution_v7/
python src/figures/attribution_figures.py                # regenerates Fig 3.9 (labels overlaid), Fig 3.10 (synthetic only)
```
Exact flags are fixed when the code is delivered (step 3). **Not rerun:** `dump`, `blocks`, `score`,
`diag`, `synth`, `spread` — label-free, outputs in `results/attribution_v6/` are final.

**Gate G-L1 (index alignment), must pass before `eval`:**
1. per-subject seizure counts equal `seizure_blocks.csv` (7/10/12/8/20/10/3/6) — hard stop otherwise;
2. every channel name is one of the 18 in §2 — hard stop otherwise;
3. the parser prints all 76 rows as (subject, idx, edf_file, onset_s, duration_s, |S|, channels), and
   the author confirms that the order is the order in which the seizures were read (chronological, as
   in the CHB-MIT summary files). **This confirmation is the gate**; it is recorded in `parse_log.txt`;
4. diagnostic only, not pass/fail: containment of the retired draft's dominant channel(s) in the final
   set at the same index, over the 36 seizures where the draft named one. The two annotations are
   independent, so a miss is not an error; a subject where containment is near zero *and* a shifted
   index fits much better would indicate an ordering fault and is investigated before `eval`.

**Outputs (`results/attribution_v7/`):** `labels/ictal_channels_FINAL.csv` · `labels/source/` ·
`labels/parse_log.txt` · `attribution_perseizure.csv` (per seizure: AUROC, AUPRC, R@|S|, prior AUROC,
matched, swapped, D7 control) · `attribution_summary.csv` (all panels, CIs, p-values) ·
`label_diversity.csv`.

**Window-count sanity (unchanged).** chb03 106 · chb06 45 · chb13 144 · chb14 49 · chb15 515 · chb16 28 ·
chb17 74 · chb18 83 (TEST = 1044).

---

## 9. RESULTS

> **Provenance for every number below.** Checkpoint `data/models_retrain/gae_joint_seed42.pt`,
> sha256 `dea06cb533df1c7d0520ae21c4cbb1b8a938297f937366bc9915b040726ea108`, bias fingerprint 1.1597,
> chb13 recon AUROC 0.8319, verified corr = 1.0000000 on 16/16 committed TEST zrecon arrays.
> **Never identify this checkpoint by filename or by the constants 0.8676 / 0.836** — those are the
> pre-rebuild §0 model.

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
| G-S4' spread (after D6.1) | spread(\|S\|=18) > spread(\|S\|=1), p < 0.05 | 0.9755 vs 0.9644 (see note) | **PASS** |

> **Note on G-S4′.** A p-value of 8.9e-11 once accompanied this row. It has no traced source in a
> committed file and was removed on 2026-09-12 (`VERIFIED_CORRECTIONS.md`, Table 3.6). The criterion
> passes on the comparison the row states. Do not quote the p-value.

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


### 9.3 Against the final annotation — FINAL (2026-09-19)

Source: `results/attribution_v7/{attribution_tests,attribution_summary,attribution_perseizure}.csv`,
written by `attribution_pipeline.py eval` after gate G-L1 (order confirmed by the author, logged in
`labels/parse_log.txt`). Regression: `eval --labels v6` reproduced every v6 CSV byte-identically.
Channel alignment: `ch_name == CH[ch_idx]` on 10944/10944 rows of `attribution_scores.csv`.

**Pre-registered tests (seed 42, p95, 62 focal seizures):**

| test | statistic | value [95% CI] | reference | p | p (Holm) | verdict |
|---|---|---|---|---|---|---|
| **L1** chance | macro-AUROC | **0.5694** [0.5097, 0.6321] | null 0.5004 | 0.001 | — | **PASS** |
| **L2** anatomical prior | AUROC − AUROC_prior | **−0.1694** [−0.2553, −0.0804] | prior 0.7387 | 1.0 | 1.0 | **FAIL** (significantly *below*) |
| **L3** matched vs swapped | mean(matched − swapped) | **+0.0064** | null 0.0001 | 0.3377 | 0.6753 | **FAIL** |
| D7 subject-constant | AUROC − AUROC_ctrl | −0.0737 | control 0.6431 | — | — | control higher (as registered: no evidence beyond a subject prior) |

**Descriptive panels:**

| panel | n | macro-AUROC [95% CI] | p_perm | macro-AUPRC (prev.) | R@\|S\| | prior |
|---|---|---|---|---|---|---|
| **all focal (primary)** | 62 | **0.5694** [0.5097, 0.6321] | 0.001 | 0.4500 (0.253) | 0.3202 | 0.7387 |
| excl. chb15 (D8) | 42 | 0.5011 [0.4311, 0.5741] | 0.4915 | 0.4458 (0.312) | 0.3188 | 0.8164 |
| n_windows ≥ 3 (D5) | 59 | 0.5889 [0.5299, 0.6454] | 0.001 | 0.4602 (0.249) | 0.3317 | 0.7328 |
| mean aggregation | 62 | 0.5854 [0.5197, 0.6506] | 0.001 | 0.4783 | 0.3680 | 0.7387 |
| seed 1 / 2 / 3 | 62 | 0.5755 / 0.5767 / 0.5723 | ≤ 0.002 | 0.4694 / 0.4663 / 0.4484 | — | 0.7387 |

**Per subject (seed 42, p95):**

| subject | n focal | macro-AUROC [95% CI] | p_perm | prior | T (L3, descriptive) |
|---|---|---|---|---|---|
| chb03 | 4 | 0.4924 [0.4160, 0.5688] | 0.5385 | 0.9032 | −0.0030 |
| chb06 | 0 | — (10/10 generalized) | — | — | — |
| chb13 | 11 | **0.6763** [0.5846, 0.7755] | 0.001 | 0.7525 | −0.0105 |
| chb14 | 8 | 0.5908 [0.4415, 0.7050] | 0.0509 | 0.8074 | +0.0118 |
| chb15 | 20 | **0.7127** [0.6177, 0.8008] | 0.001 | 0.5757 | +0.0313 |
| chb16 | 10 | **0.2597** [0.2082, 0.3038] | 1.0 | 0.8458 | −0.0380 |
| chb17 | 3 | 0.7082 [0.4462, 0.9464] | 0.017 | 0.8313 | +0.1020 |
| chb18 | 6 | 0.3650 [0.2196, 0.5380] | 0.984 | 0.8309 | −0.0205 |

chb15 is the only subject above its own anatomical prior (0.7127 vs 0.5757). chb16 and chb18 are
below chance; chb16's ten seizures last 6–14 s (`parse_log.txt`), i.e. only a few 4-s windows each.

**Verdict (§4.7):** row "L1 passes, L2 fails", with L3 failing. Written without softening: the
anomaly map agrees with the blind annotation only weakly, the agreement rests on one patient, it ranks
annotated channels significantly **worse** than a fixed anatomical rule, and it carries no
seizure-specific information.

### 9.3b Exploratory diagnosis — post hoc, NOT a claim (2026-09-19)
Run once, after the verdict, to explain the failure (rule: record the failure and the diagnosis;
never re-score). Printed by an inline command, not yet a committed file — fold into the pipeline
before any of it is quoted as a number in the report.
- Mean GAE rank per channel over the 62 focal seizures is nearly flat (7.1 for P3-O1 to 12.2 for
  F4-C4, uniform expectation 9.5), and its Spearman correlation with how often a channel is annotated
  is **+0.095**: the model's channel preference is essentially unrelated to where the reader sees
  ictal discharge.
- The agreement is patient-specific. chb15: model top channels P3-O1, P7-O1, T7-P7 coincide with the
  annotation (T7-P7 in 20/20, P3-O1 in 11/20). chb16: model top channels P4-O2 and FZ-CZ are never
  annotated, while the annotated T8-P8 and T7-P7 rank near the bottom — the inversion behind 0.2597.
- Generalized seizures: highest anomaly on central-parietal channels (C4-P4, C3-P3, F3-C3), lowest on
  the frontopolar and temporal chains.
- Reading: per-node reconstruction error reflects a change in each node's connectivity pattern, which
  need not sit where the scalp discharge is visible. Hypothesis only; not tested.

### 9.4 Methodological negative — spread does not measure localisation (label-free, final)

`§4.5` of v2/v3 proposed normalised entropy of `s` as a focal-vs-generalized measure. On synthetic
injections it is **U-shaped in |S|** — 0.9644 (\|S\|=1) → 0.9567 → **0.9441 (\|S\|=4, minimum)** →
0.9503 (\|S\|=12) → 0.9755 (\|S\|=18) — and the α = 1.0 no-injection cell has the highest spread of all
(0.978). Entropy measures **uniformity**, not localisation, so a flat map ("nothing anomalous") and a
diffuse map ("everything anomalous") look alike. G-S4′ passes only because it compares the two
extremes. **Do not use spread for focal/generalized.** The v3 real-label comparison (p = 0.984) was
computed on the retired draft and is retired with it; it is not rerun (§4.8).

### 9.5 The v3 supervisor requests — resolved by the final annotation
1. §3.2 schema, every ictal channel → **done** (mean |S| 4.55 vs 1.31).
2. Within-subject Jaccard < 0.6 → **met** (0.5144 vs 0.8879).
3. Verdict for chb06 and chb13 → chb06 generalized 10/10; chb13 focal 11/12.
4. chb15 dominance → reduced from 56 % to 32 %; D8 panel kept.

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


### A4 (2026-09-18) — final annotation and v4 method. Written before any label-scored number.
- **A4.1 — Ground truth.** The supervisor-approved human annotation (§3.3) replaces the retired
  machine-generated draft. The draft is not scored again (§3.5). Scored set: the 62 focal seizures;
  the 14 generalized seizures have undefined AUROC and are excluded by construction (§3.4).
- **A4.2 — Added L2 (anatomical prior, LOSO).** Motivated by a label-only measurement made before any
  score was read: the prior alone reaches 0.7387. Claim rule: paired-bootstrap CI of Δ_prior excludes 0.
- **A4.3 — Added L3 (matched vs swapped within subject).** Motivated by the label-only oracle (0.925):
  labels remain patient-consistent, so D7 can still win by averaging. L3 has no averaging advantage.
- **A4.4 — D7 reading.** Reported exactly as registered in A2 D7; the v3 exemption is not re-used. If
  D7 and L3 disagree, both are reported; the per-seizure claim follows L3 (§4.4).
- **A4.5 — Multiplicity.** L1 gatekeeper; Holm over {L2, L3} at 0.05 (§4.5).
- **A4.6 — Dropped:** operating point / EEG-CGS P-F1 comparison; spread on real labels; any measure for
  generalized seizures; MAP, C1, lateralisation (§4.8).
- **A4.7 — Unchanged:** score, p95 aggregation, robust-z baseline, seed-42 primary, D3, D4, D5, D8,
  synthetic gates, permutation null (1000), bootstrap (1000), RNG 42.
- **A4.8 — Index gate G-L1** (§8) must pass before `eval`; its log is committed with the results.
- **A4.9 — Nothing is tuned on these labels.** No aggregation, threshold, channel subset or panel is
  selected after the scores are seen. A result that fails is reported as it stands.
- **A4.10 — Operational note, fixed in code before the run (2026-09-19).** Holm needs a p-value for L2:
  it is the one-sided paired-bootstrap p, (1 + #{Δ* ≤ 0}) / (1 + 1000). L2 passes only if its Holm
  p < 0.05 **and** its 95 % CI lies above 0. D7 in the per-seizure table uses the other *focal*
  seizures of the subject (§4.4). The label CSV carries `n_ictal`; `n_windows` is read from
  `seizure_blocks.csv`.

---

## 11. FILE OPERATIONS — state as of 2026-09-18

**Canonical:**
- `src/attribution_pipeline.py` — the only attribution code (v7 label path added in step 3).
- `src/verify_provenance.py` — session gate.
- `results/attribution_v6/` — **label-free** results, final (`seizure_blocks.csv`,
  `ictal_row_to_seizure.csv`, `attribution_scores.csv`, `attribution_diagnostics.csv`,
  `synthetic_sanity.csv`, `synthetic_spread.csv`).
- `results/attribution_v7/` — final annotation and every label-scored result.
- `results/attribution_v5/labels/labels_*_FINAL.csv` — the retired draft's source. **Irreplaceable
  provenance. Never delete.**

**Superseded (keep, do not cite):** `results/attribution_v6/labels/ictal_channels_DRAFT.csv`,
`results/attribution_v6/{attribution_perseizure,attribution_summary,label_diversity}.csv` — scored
against the retired draft. Restore point for the v3 state: `git tag attribution-v6-draft`.

**Archived (do not cite, do not run):** `archive/src_superseded/attribution_v5/` ·
`archive/attribution_superseded/attribution_c{1,2,3}.py` · `archive/pre_rebuild_s0/` ·
`results/history_superseded/`.

**Retired numbers — never quote:** 0.6497 · 0.3095 · 0.7758 · 0.8879 · −0.1261 · 0.6267 · 0.6681 ·
0.2672 · +0.3578 · p = 0.984 (draft labels) · 0.262 / 0.303 (MAP@K era) · p = 8.9e-11 (untraced).
