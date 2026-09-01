# PROPOSED SOLUTION — the locked method (rlg)

**Unsupervised Epileptic Seizure Temporal Localization in Scalp EEG using Graph Autoencoder and
Change Point Detection**
Student: Nguyen Quoc Trung Nhan (BEBEIU22184) · Supervisor: Assoc. Prof. Hà Thị Thanh Hương
International University, VNU-HCM · Registration signed 10 June 2026

---

## DOCUMENT STATUS

**This is the single canonical description of the METHOD.** It replaces
`docs/archive/Proposed_solution_updated_v5.md`, which described the pre-rebuild pipeline
(recon + **temporal-LSTM** + gamma) and is retained only as history.

**On any number conflict, `docs/RESULTS_OF_RECORD_phaseB.md` WINS over this file.** This document
describes *what the system does and why*; the RoR holds *what it scored*.

| Section | Provenance |
|---|---|
| §I–§II, §III.1–III.2, §III.5 (PELT), §VI (DM1–DM6) | Carried over verbatim-in-substance from `Proposed_solution_updated_v5.md` (still correct — these stages never changed) |
| §III.3 (GAE) | Verified against `gae_joint.py` + `PREREG_01` §1/§3 (checkpoint-verified architecture) |
| §III.4 (latent-Mahalanobis) | **NEW** — verified against `latent_anomaly.py` + `PREREG_TIER2_latent_ensemble.md` + Amendment A1 |
| §III.6 (ensemble) | Verified against `ensemble_recipe.py` (`ENS_WEIGHTS`, `CANDIDATES`) |
| §IV, §V | `szcore_eval.py`, `PREREG_04/05/06/07`, `RESULTS_OF_RECORD_phaseB.md` |

**What changed from v5 (the two substantive edits):**
1. The **temporal LSTM branch is DROPPED** — its training code was unrecoverable and its arrays could
   not be reproduced (PREREG_TIER2 **Amendment A1**). It is replaced by a **latent-Mahalanobis readout**
   on the *same* GAE. This is the core Phase-B contribution.
2. Ensemble weights are **equal (1/3 each)**, not 0.35/0.30/0.35 — re-derived on non-TEST data under
   PREREG_03, which found the weight surface flat (24 triples within 0.005 of the argmax) and adopted
   equal weights as the anti-overfit choice.

---

## I. DATASET

CHB-MIT Scalp EEG (PhysioNet), 18-channel bipolar montage, 256 Hz.

**Splits (LOCKED, seed 42, `data/splits/split_main.json`) — never violated:**

| Split | Subjects | Use |
|---|---|---|
| TRAIN (12) | chb01, 02, 04, 05, 07, 08, 09, 12, 19, 20, 21, 23 | GAE training (interictal windows only) |
| VAL (3) | chb10, 11, 22 | every design decision, gate, operating point |
| **TEST (8, ONE-SHOT)** | chb03, 06, 13, 14, 15, 16, 17, 18 | **76 seizures, 278.2 interictal h — touched once** |

The model never sees a TEST window, and never sees *any* ictal window during training. Every script
carries a TEST guard that aborts on a TEST subject (see `latent_anomaly.py`: `INTEGRITY ABORT`).

---

## II. APPLICATION SCOPE

**Post-hoc EEG review triage, not a real-time alarm.** Given a completed multi-hour recording, the
system returns timestamps where seizure-related connectivity transitions occur; clinicians review those
candidate segments instead of the whole recording.

This framing is mandatory for interpreting every metric:

- **FP/day is a review-burden quantity, not an alarm-quality quantity.** At the reported balanced point
  (27.4 FP/day ≈ 1.1 flags/hour) the system is usable for review triage. A real-time clinical alarm
  needs a far lower false-alarm rate, which is infeasible here without collapsing sensitivity.
- **FP/day replaces specificity** throughout: true-negative *events* cannot be defined in an event-based
  protocol. This is structural to label-free anomaly detection and is reported as a limitation.
- Detection latency is a quality indicator, not a constraint. No pre-ictal lead is claimed.
- The clinical question is *"when did a seizure start?"*, not *"is this 4-second window anomalous?"* —
  which is why change-point detection, not thresholding, is the final stage.

---

## III. METHODOLOGY

```
raw EEG
 → preprocessing (§III.1)
 → per-window graphs: wPLI + AEC, top-k 20%  +  band-power node features (§III.2)
 → Joint GAE, seed 42 (§III.3)
      ├── zrecon  : reconstruction MSE
      └── zlatent : Mahalanobis distance to the interictal latent manifold (§III.4)
 → zgamma : gamma-band AEC (§III.2.4)
 → per-branch robust-z → EQUAL-weight ensemble, 1/3 each (§III.6)
 → PELT change-point detection + magnitude filter (§III.5)
 → label-free per-subject FP-budget operating point (§IV.2)
 → SzCORE event scoring (§IV.1)
```

### III.1 Preprocessing (LOCKED)

Applied to 100% of the raw data, in this mandatory order:

| # | Operation | Implementation |
|---|---|---|
| 1 | Bandpass 0.5–60 Hz | 4th-order Butterworth, zero-phase (`sosfiltfilt`), 3 s padding per side |
| 2 | Notch 60 Hz | IIR notch, Q = 30, zero-phase (`filtfilt`) — powerline removal |
| 3 | CAR (common average reference) | applied before wPLI; suppresses zero-lag volume conduction |
| 4 | Amplitude artifact rejection | drop windows where any sample exceeds 5× per-channel SD — **interictal only** |
| 5 | Z-score normalisation | per channel, per subject; statistics from subsampled interictal windows (every 10th) |
| 6 | Windowing | 4 s non-overlapping windows (1024 samples @ 256 Hz) |

**Note the deliberate asymmetry in step 4:** interictal windows are artifact-rejected, ictal windows are
**not**. Rejecting on amplitude during a seizure would remove the very high-amplitude activity being
detected. This is disclosed in Methods rather than silently applied.

### III.2 Feature extraction (LOCKED)

#### III.2.1 Node features — spectral band powers

Five band powers per channel via Welch PSD → `X ∈ R^{18×5}` per window; log-normalised then z-scored
per window.

| Band | Range | Physiological rationale |
|---|---|---|
| Delta | 0.5–4 Hz | dominant in seizure discharge activity |
| Theta | 4–8 Hz | temporal-lobe involvement in focal seizures |
| Alpha | 8–13 Hz | suppressed during ictal activity (confirmed in 7/8 TEST subjects) |
| Beta | 13–30 Hz | motor-cortex involvement |
| Gamma | 30–60 Hz | high-frequency ictal oscillations |

#### III.2.2 Adjacency — broadband wPLI + AEC

```
A = 0.5 · A_wPLI + 0.5 · A_AEC
```

**wPLI (weighted phase-lag index)** — phase-based coupling that suppresses zero-lag volume conduction:

```
wPLI_xy = | E[ Im(C_xy) ] | / E[ | Im(C_xy) | ]
```

where `C_xy` is the cross-spectrum between channels *x* and *y*.

**AEC (amplitude-envelope correlation)** — amplitude-based coupling, complementary to wPLI.

**α = 0.5** confirmed by ablation (α ∈ {0.3, 0.5, 0.7}; ΔAUROC < 0.01 across values → the equal-weight
choice is adopted as the non-arbitrary one).

#### III.2.3 Edge sparsification — top-k 20% (a primary contribution)

`apply_topk_threshold(A, keep_ratio = 0.20)` keeps the strongest 20% of undirected edges per window =
**30 of 153 possible edges** for 18 channels; mean density ≈ 0.185.

**Why top-k% and not a fixed threshold.** A fixed threshold t = 0.05 produced graph density 0.92–0.97.
GCN message passing on a near-fully-connected graph degenerates into weighted global mean pooling,
destroying the topological advantage that motivates using a graph model at all. After switching to
top-k%, the Frobenius distance between mean-ictal and mean-interictal adjacency matrices improved
**88–411%** across subjects. *Graph density is a critical but widely overlooked hyper-parameter in
GAE-based EEG analysis* — this is a primary novel contribution of the thesis (DM1).

#### III.2.4 Gamma AEC — the third ensemble signal

Computed independently from raw windows (`src/dataprep/compute_gamma_aec.py`):

1. Bandpass 30–60 Hz (4th-order Butterworth, `filtfilt`)
2. Hilbert transform → amplitude envelope
3. Log-transform `log(env + 1e-10)`, zero-mean per channel per window
4. Pearson correlation matrix `[N, 18, 18]`
5. Score = mean of the top-20% (30 pairs) AEC values per window
6. Z-normalise over all windows pooled (no ictal-label dependency)

**Why gamma specifically.** Band-direction analysis showed gamma AEC increases ictal-vs-interictal in
7/8 TEST subjects — **including chb06**, the inverted-wPLI subject, where it is the only band with the
correct direction. Delta and theta AEC simultaneously invert chb06 and chb17. Gamma AEC standalone
window AUROC = 0.7546.

### III.3 Graph autoencoder — joint reconstruction (LOCKED)

Architecture verified against the checkpoint `state_dict` shapes (PREREG_01 §1):

```
Encoder :  GCNConv(23 → 64) → ReLU → GCNConv(64 → 16)      ⇒  Z ∈ R^{18×16}
Decoder A:  Â = clamp(Z Zᵀ, 0, 1)                           (inner product, clamped linear, no sigmoid)
Decoder X:  X̂ = MLP(16 → 32 → 5)                            (Linear, ReLU, Linear)
Loss    :  L = MSE(A, Â) + λ · MSE(X_norm, X̂),   λ = 0.1
```

≈ 8.7k parameters. **Node input** (`x ∈ R^{18×23}`) is the concatenation of the normalised adjacency row
and the normalised band powers:

```
An = A / (max(A) + 1e-8)                                     # per-window global max
Xn = (X − min_ch X) / (max_ch X − min_ch X + 1e-8)           # per-window, per-band, over channels
x  = concat([An (18), Xn (5)], dim = −1)                     # [18, 23]
edge_index, edge_attr = dense_to_sparse(A)                   # from RAW A, not An
```

**Deliberate asymmetry (replicated, not "fixed"):** node features use `An`/`Xn`, but the A-reconstruction
target is **raw A** while the X-reconstruction target is `Xn`. This is what the original checkpoint does;
changing it would break comparability with the locked baseline.

**Training.** Interictal windows of the 12 TRAIN subjects only. Adam lr 1e-3, cosine schedule, 200 epochs
(no early stopping), batch 32, canonical seed 42, 80/20 internal train/val split.

**Honest disclosure for Methods:** the original training loop was lost; it was **reconstructed** under
PREREG_01 and validated against the retained checkpoint by **Gate R-GAE** — a *distributional*
equivalence test (per-subject recon AUROC within tolerance; macro 0.669 vs locked 0.671), not a
bit-exactness test, since Kaggle GPU training is not bit-reproducible.

#### III.3.1 Readout 1 — reconstruction error (`zrecon`)

```
raw_recon(t) = MSE(A_t, Â_t) + 0.1 · MSE(Xn_t, X̂_t)
```

Per-node variant (used for channel attribution, §VII) keeps the error per node, `[n_win, 18]`; its
node-mean reproduces the scalar score to < 1e-5.

### III.4 Readout 2 — latent-Mahalanobis (`zlatent`) — **replaces the LSTM branch**

**Motivation (a measured failure, not a preference).** Reconstruction MSE assumes *ictal reconstructs
worse*. In subjects with ictal hypersynchrony the graph becomes **more** regular, so the seizure
reconstructs **better** and `zrecon` inverts polarity (chb06 recon AUROC 0.300 — well below chance;
chb10 shows the same effect on VAL). A distance-based readout in the same latent space does not depend
on error magnitude and therefore does not invert.

**Definition** (verified against `latent_anomaly.py`):

```
e_t   = mean over the 18 nodes of Z_t                       ⇒ graph-level embedding, e_t ∈ R^16
Σ̂, μ̂  = LedoitWolf shrinkage covariance + mean, fitted on that SUBJECT'S INTERICTAL windows only
raw_latent(t) = (e_t − μ̂)ᵀ Σ̂⁻¹ (e_t − μ̂)                    # squared Mahalanobis distance
```

**Why this is label-free and valid on TEST.** The fit uses only the subject's *interictal* (seizure-free)
data — no seizure timing, no counts, no sensitivity. This mirrors clinical deployment, where a baseline
recording is available before any seizure occurs. LedoitWolf shrinkage is required because a raw
covariance in 16-D on limited windows is ill-conditioned; a degenerate `dim ≫ n` fit produces a spurious
AUROC of 1.0, which is why the null check (null AUROC ≈ 0.5) is mandatory.

**Why it legitimately replaces the LSTM.** The original temporal branch was a black box: no class, no
training code, no config, in the repo or on Kaggle. It could not be run on a new recording, which blocks
external validation and any clinical use, and it carried a 15-window warm-up fill baked into every array.
A principled, reproducible readout on the same GAE fixes both defects. The claim made in the thesis is
**"a latent-manifold readout of this family"**, never "the original branch recovered".

### III.5 PELT change-point detection (LOCKED — final detection stage)

PELT (Killick et al., 2012) minimises

```
V(τ, n) = Σ_{k=1}^{K+1} [ C(y_{τ_{k−1}+1 : τ_k}) + β ]
```

with `C` the L2 (least-squares) cost and `β` the BIC penalty. Configuration (single source:
`src/cpd_pipeline_v14.py`):

| Parameter | Value | Rationale |
|---|---|---|
| Cost | `model="l2"` | optimal for mean shifts in a 1-D z-normalised signal |
| Variance estimator | MAD-based, `s² = (1.4826 · MAD)²`, **from interictal/background only** | robust to multi-session baseline drift (chb17); makes the penalty **seed-independent** → deterministic detection |
| Search grid | `jump = 5` (20 s resolution) | within clinical tolerance; 2.5× faster than `jump = 2` |
| Penalty | `β = pen_mult · s² · log(n)` | data-driven BIC; no ictal labels |
| Penalty sweep | `pen_mult ∈ {0.3, 0.5, 1, 2, 5, 10}` | generates the sensitivity–FP/day trade-off curve |
| **Magnitude filter** | keep a change point only if its local \|mean shift\| ≥ the `min_mag_pct`-th percentile of **interictal** change-point magnitudes (local window = 15 each side) | removes small-shift change points causing systemic over-segmentation; **label-free** (calibrated on interictal), direction-agnostic |
| Magnitude sweep | `mag_pct ∈ {40, 50, 55, 60, 65, 70, 75, 80}` | second axis of the operating-point grid |
| Buffer padding | bootstrap resampling from interictal scores | preserves σ²; prevents synthetic-zero dilution |
| Smoothing | 1-min centred moving average (window = 15) | attenuates transient noise, preserves seizure elevation |

Event-matching tolerance, merge gap and post-ictal handling are **not** algorithm parameters — they
belong to the SzCORE protocol (§IV.1).

**Single source of truth.** `detect_changepoints` / `detect_events` in `cpd_pipeline_v14.py` are called
by both the evaluation harness and the web demo, so the reported algorithm and the deployed algorithm
are guaranteed identical. Locking CHB-MIT numbers passes the interictal mask for exact reproducibility;
the demo runs fully label-free (whole-signal statistics, verified ≈ identical at the ~0.2% seizure
prevalence).

**Why CPD instead of a threshold (DM4).** P95-on-interictal is unsupervised but conservative and detects
upward shifts only; Youden's J needs validation ictal labels and would violate the unsupervised claim;
an FDR-driven threshold (≤ 2.0/h) requires τ_z = 5.8 → sensitivity ≈ 0. CPD is threshold-free,
data-driven via the BIC penalty, **direction-agnostic** (it detects *a distribution change*, which is
what rescues polarity-inverted subjects), and answers the clinical question directly.

### III.6 Ensemble (LOCKED — equal weights)

Each branch is converted to a robust z-score, then combined with **equal weights**:

```python
all_s = np.concatenate([scores_inter, scores_ictal])
med   = np.median(all_s)
mad   = np.median(np.abs(all_s - med)) + 1e-9
z     = (scores - med) / mad                       # robust-z, per subject, per branch
```

```
z_ens(t) = (1/3) · zrecon(t) + (1/3) · zlatent(t) + (1/3) · zgamma(t)
```

Implemented once in `src/ensemble_recipe.py` (`ENS_WEIGHTS`, `build_ensemble_subset`, `CANDIDATES`).

**Why robust-z (median/MAD) over mean/SD:** the score distributions are heavy-tailed; MAD is not
dragged by the extreme values the detector is meant to find.

**Why pooling inter+ictal for the statistics is still unsupervised:** ictal windows are ≈ 0.18% of the
total, so the median and MAD are numerically indistinguishable from interictal-only statistics. **No
ictal timestamp is used** — only the concatenated score array.

**Why equal weights (PREREG_03).** Weights were derived on non-TEST data by grid search over the simplex
(step 0.05) maximising VAL macro window AUROC, with an anti-overfit tie-break toward (1/3, 1/3, 1/3).
The surface came out **flat** — 24 triples within 0.005 AUROC of the argmax — so equal weights were
adopted as the regularised, non-cherry-picked choice. Later sweeping of this surface is therefore
fishing, and is forbidden.

---

## IV. EVALUATION FRAMEWORK

### IV.1 SzCORE event scoring (the primary tier)

Scoring follows **SzCORE** (Dan et al., *Epilepsia* 2024) via the `timescoring` library
(`src/szcore_eval.py`). Any-overlap event matching. The merge rule is applied **symmetrically** to both
reference and hypothesis (empirically it never triggers on this dataset).

Reported together, never in isolation: **sensitivity · precision · F1 · FP/day**, with Wilson 95% CIs
for sensitivity/precision and Poisson (Garwood) 95% CIs for FP/day.

**Window tier (secondary).** Only **macro AUROC / AUPRC** are valid across subjects, because they are
rank-based. Threshold-dependent pooled window metrics are invalid here: the per-subject robust-z scales
are unbounded, so pooling them mixes incomparable units.

### IV.2 Operating-point selection (label-free)

The CPD stage exposes two knobs (`mag_pct`, `pen_mult`). Selecting them by peeking at TEST sensitivity
would be test-selection, so every reported point is derived without seizure labels:

- **VAL-derived shared point** — the rule is fixed on the 3 VAL subjects and applied to TEST once
  (PREREG_05/06). The balanced objective is knob-free: `argmin |sensitivity − precision|` on the VAL
  Pareto frontier.
- **Per-subject FP-budget point** (PREREG_04/07) — for each subject independently, choose the grid cell
  whose **interictal** FP/day is closest to a pre-specified budget *B*. Selection reads only
  `{mag_pct, pen_mult, fp, n_inter_h}`; tie-breaks are explicitly forbidden from using sensitivity or TP.

**Integrity framing (state verbatim in the thesis).** The *detection model* stays fully
patient-independent — it never trains on a TEST subject and never sees a TEST seizure. What is added is
a **per-patient false-alarm-rate calibration on seizure-free data**: a threshold calibration, not model
personalisation, using **no seizure labels**. It uses strictly *less* label information than a shared
point chosen from the pooled sensitivity-vs-FP frontier. Both the shared and calibrated numbers are
always reported — never one silently replacing the other.

---

## V. RESULTS (headline only — full record in `RESULTS_OF_RECORD_phaseB.md`)

TEST = 8 subjects, 76 seizures, 278.2 interictal h, seed 42, one-shot.

| operating point | sens | prec | F1 | FP/day |
|---|---|---|---|---|
| rlg @ §0 balanced cell (m70/p0.5) | 0.645 | 0.099 | 0.172 | 38.4 |
| **rlg VAL-derived balanced (m50/p2.0) — honest headline** | 0.618 | 0.129 | **0.213** | **27.4** |
| Pooled TEST Pareto **peak** (curve, not a selected point) | 0.474 | 0.387 | **0.426** | **4.9** |

**Window macro AUROC (TEST) = 0.805** (VAL 0.928). Per-subject: chb03 0.964 · chb06 0.501 · chb13 0.822 ·
chb14 0.698 · chb15 0.879 · chb16 0.876 · chb17 0.782 · chb18 0.920.

**GAE seed-stability** (VAL, 4 seeds): window macro **0.929 ± 0.002**; event F1 @ 3.6 FP/day
**0.51 ± 0.034**. These SDs are the **noise floors** — any claimed improvement smaller than these is
noise, and this is enforced as a standing gate.

**The precise claim.** Replacing the unreproducible temporal branch with a latent-manifold readout on
the same GAE yields a **fully reproducible** unsupervised patient-independent detector that **matches**
the baseline at the baseline's own operating points and **Pareto-improves precision/F1 at lower
false-alarm rates**. The sensitivity difference (0.632 → 0.645) is within CI and is **not** claimed as an
improvement; the defensible wins are precision/F1 at matched-or-lower FP/day, and reproducibility.

⚠ **Forbidden numbers:** 0.750 / 0.829 / 0.791 / 39.77 / 71.25 are pre-rebuild figures that were never
reproduced (they depended on lost components plus test-selection). They must never be cited.

---

## VI. DECISION MATRICES (ABET PI 4C — mandatory in Chapter 2)

All six appear in Chapter 2 under the exact title format *"Decision Matrix for [aim]"*.

| Matrix | Options evaluated | Winner | Key evidence |
|---|---|---|---|
| **DM1** Edge threshold | fixed t = 0.05 vs top-k 20% | **top-k 20%** | Frobenius +88–411%; GCN topology degrades at density > 0.90 |
| **DM2** Loss function | MSE vs BCE vs joint MSE | **joint MSE (λ = 0.1)** | chb14 mzi 0.661 → 1.490 → 1.633; BCE AUROC 0.449 |
| **DM3** Anomaly score | standard MSE vs masked MSE vs max | **standard MSE (324 elements)** | masked MSE removes topology signal (chb13 −0.044, chb14 −0.049) |
| **DM4** Detection method | threshold (P95) vs CPD (PELT) | **CPD (PELT)** | threshold has positive latency and structurally fails chb06; CPD is direction-agnostic |
| **DM5** Signal components | wPLI only vs AEC only vs gamma only vs combined | **combined 3-signal ensemble** | no subject fails all three; ensemble beats the best single signal (gamma standalone 0.7546) |
| **DM6** Deployment strategy | cloud API vs on-premise server vs edge device | **on-premise hospital server** | weighted 4.1 vs 3.1 (edge) vs 2.1 (cloud) — see §VI.1 |

### VI.1 DM6 — Decision Matrix for Deployment Strategy

DM1–DM5 resolve *technical* design questions. ABET PI 4C additionally requires at least one decision
that explicitly weighs **global, economic, environmental and societal** impact. DM6 fills that gap:
given the locked technical pipeline, **where and how should it be deployed?**

**Decision context.** The system is a post-hoc review-triage tool (§II) and is **CPU-only at inference**
(`cpd_pipeline_v14.py` uses no GPU; only offline component export needs one). That constraint is what
makes this matrix technically grounded rather than a generic CSR exercise.

| Option | Description |
|---|---|
| A — Cloud API | hospital uploads EEG to a central server; inference remote; results via API |
| B — On-premise server | CPU-only inference server inside the hospital's own network |
| C — Edge device | compact local-inference device (Jetson-class) at the bedside |

**Criteria and weights** (mapped onto the four PI 4C dimensions):

| Criterion | Weight | Why this weight |
|---|---|---|
| Economic — infrastructure + operating cost | 30% | determines whether lower-resource hospitals can adopt at all; ties directly to the "reduce review burden, don't add cost" framing |
| Societal — data accessibility + patient privacy | 30% | CHB-MIT is a **pediatric** cohort; pediatric EEG leaving a hospital network is a genuine privacy concern, and equitable access is the real-world motivation |
| Environmental — power/carbon of continuous operation | 20% | the CPU-only inference design is a real, quantifiable point of comparison, not a token entry |
| Global/scalability — deployability across hospitals | 20% | the method is patient-independent (no per-patient fine-tuning) — a genuine scalability advantage |

| Criterion | A: Cloud | B: On-premise | C: Edge |
|---|:---:|:---:|:---:|
| Economic (30%) | 2 — recurring storage/bandwidth for multi-hour, multi-channel EEG | 4 — one-time cost, no usage fee; matches CPU-only design | 3 — per-bed hardware, but no network infrastructure |
| Societal (30%) | 1 — pediatric EEG leaves the hospital network; highest exposure | 5 — data never leaves the internal network | 4 — data stays on device, but harder to audit centrally |
| Environmental (20%) | 2 — shared-datacenter inference; energy hidden in shared infrastructure | 4 — CPU-only, no continuous GPU draw; reuses existing hospital IT | 3 — efficient per device, but replicates per bed |
| Global/scalability (20%) | 4 — scales horizontally, minimal per-site setup | 3 — each hospital needs its own install | 2 — cost/maintenance scale linearly with devices |

```
A (Cloud API)   : 0.30(2) + 0.30(1) + 0.20(2) + 0.20(4) = 2.1
B (On-premise)  : 0.30(4) + 0.30(5) + 0.20(4) + 0.20(3) = 4.1
C (Edge device) : 0.30(3) + 0.30(4) + 0.20(3) + 0.20(2) = 3.1
```

**Winner: B — on-premise hospital server.** The 1.0-point margin over the runner-up is well above the
10% under-differentiation threshold used in DM1–DM5, so no criterion revision is triggered.

**Honest scope limitation:** DM6 is a *design-grounded qualitative argument* built from the pipeline's
already-locked properties (CPU-only, patient-independent) — **not** a costed health-economics study with
real procurement data. It must be presented as a defensible engineering judgment under PI 4C, not as
validated deployment economics.

---

## VII. CHANNEL ATTRIBUTION (XAI layer — PROVISIONAL)

Full specification: `docs/ATTRIBUTION_SPEC.md` (the single source; this is a pointer only).

Per seizure, the GAE emits 18 per-node reconstruction-error scores (robust-z vs interictal) → one vector
`s ∈ R^18`. The question asked is: *do the channels an expert marked ictal score higher than the ones
they did not?* — i.e. **per-channel binary classification**, evaluated by macro-AUROC + AUPRC with
focal/generalized stratification mandatory, and a synthetic sanity check before scoring against real
labels.

**Framing discipline: this is XAI for the GAE branch — it is NOT seizure localization and NOT SOZ
identification.** The map is a *novelty/anomaly* map; comparison with expert labels is concordance and
plausibility, not accuracy. Expert labels are drafted for all 76 seizures and remain **pending the
supervisor's freeze**, so all attribution results are reported as PROVISIONAL.

---

## VIII. KNOWN LIMITATIONS (report honestly — do not soften)

1. **FP/day is high for a real-time alarm** and is structural to label-free anomaly detection. Justified
   only under the post-hoc review-triage framing (§II).
2. **Specificity is not reportable** — true-negative events are undefinable in an event-based protocol;
   FP/day is used throughout instead.
3. **Representation-limited subjects.** chb06 (window AUROC 0.501 ≈ chance, inverted connectivity under
   ictal hypersynchrony) and chb14 (0.698) cap pooled sensitivity. Directed connectivity (transfer
   entropy) rescues them *per-subject* but net-washes across subjects — a clean negative with a
   documented mechanism, not an untested gap.
4. **Window ≠ event.** Representation-level gains repeatedly died at the CPD transfer, because PELT keys
   on sustained level shifts rather than rank separation. This is the single most important negative
   finding of the optimization program.
5. **Single dataset.** No external validation (Siena/TUSZ) and no LOSO — both are documented Future Work.
6. **The GAE training loop is a reconstruction** (PREREG_01), validated distributionally by Gate R-GAE,
   not a bit-exact recovery of the original run.
7. **Literature comparison caveat.** CHB-MIT figures of 90–99% in the literature are segment-level,
   patient-specific and/or supervised, and are **not** comparable to this event-level unsupervised
   patient-independent setting. Use Yildiz = 0.68 as the comparable anchor. Never cite the Transformer
   sensitivity 0.765 / 40.6 as CHB-MIT — that is a TUH result.

---

## IX. STATUS OF THE OPTIMIZATION PROGRAM

**Closed.** Phase C evaluated seven pre-registered, VAL-gated levers across the decision, representation,
ensemble and signal layers; **none Pareto-improved rlg at the event headline.** rlg is the ceiling for
this dataset/split and is the system of record. Details: `RESULTS_OF_RECORD_phaseB.md` §8–§9,
`PHASE_C_FULL_AUDIT.md`.

**Phase D was designed and pre-registered but deliberately not executed** — a time-boxed decision after
Phase C closed, documented in `PHASE_D_HANDOFF.md` as Future Work and defense material. Restore point:
`git tag phase-c-final`.

Rejected levers that must not be re-proposed: transfer entropy / directed connectivity (both decision
and representation layers), CPD smoothing variants, plateau/slope change-point gating, per-channel
scalar features of the same class as band powers, ensemble drop-recon or weight sweeps, artifact
gating, learned graph structure (GSL), Deep-SVDD/compactness, and CCM.
