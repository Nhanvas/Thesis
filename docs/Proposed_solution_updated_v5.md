# PROPOSED SOLUTION — FINAL PLAN (v3)
## Unsupervised Epileptic Seizure Temporal Localization in Scalp EEG using Graph Autoencoder and Change Point Detection
## Student: Nguyen Quoc Trung Nhan | BEBEIU22184
## Supervisor: Hà Thị Thanh Hương (Associate Professor)
## Registration form signed and submitted: June 10, 2026
## Last updated: June 22, 2026 (supersedes June 6, 2026 v2)

---

## DOCUMENT STATUS

**Phase: PHASE A CLOSED (evaluation rigor + CPD optimization complete). Next = Phase B (spatial localization + write-up).**
**This is v4 (supersedes v3 of June 22, 2026). Methodology core (preprocessing, graph, GAE, LSTM, gamma, ensemble) is unchanged and LOCKED. The CPD stage and the entire evaluation framework were revised and re-locked in Phase A; all result numbers below are the SzCORE-protocol locked results (the old onset-match "DR / FCP-h" numbers from v3 are superseded).**

All core pipeline decisions (architecture, graph construction, ensemble weights) are locked from v2.
Phase A added two algorithm-level CPD improvements (seed-independent PELT penalty + magnitude filter,
both label-free), adopted the SzCORE (Dan et al., *Epilepsia* 2024) evaluation framework, fixed an
evaluation bug, selected operating points, consolidated the detection algorithm into a single source
(`cpd_pipeline_v14.py`), and statistically validated the event-tier results. Writing is deferred per
supervisor instruction — the 50-page report will be produced in the final 2-week sprint.

> **Authoritative numbers live in `RESULTS_OF_RECORD.md`; status/plan in `PLAN_AND_STATUS.md`.** This file is the methodology master (Chapter-2/3 source); its result tables mirror the locked record.

| Milestone | Date |
|-----------|------|
| Registration form submitted | June 10, 2026 |
| Official topic/advisor assignment | July 6, 2026 |
| **Technical lock (all experiments complete)** | **~October 1, 2026** |
| **Writing sprint (2 weeks)** | **October 1–15, 2026** |
| Thesis submission to department | October 15, 2026 |
| Progress check (mid-period) | August 17–29, 2026 |
| Reviewer evaluation | October 19–24, 2026 |
| Defense | November 2–3, 2026 |

**Hard copy deadline:** Submit spring-bound copies at least 10 business days before defense
(~October 19, 2026). Three copies on cotton bond paper, original committee signatures required.

---

## CHANGELOG FROM v2 (June 6, 2026)

| Item | v2 | v3 | Reason |
|------|----|----|--------|
| Title | "Unsupervised Epileptic Seizure Localization via Graph Autoencoder and Change Point Detection on Dynamic EEG Functional Connectivity" | **"Unsupervised Epileptic Seizure Temporal Localization in Scalp EEG using Graph Autoencoder and Change Point Detection"** | Corrected to match signed registration form (June 10, 2026) |
| Phase | "WRITING PHASE — all experiments complete" | **"OPTIMIZATION PHASE — experiments continuing"** | Supervisor (Associate Professor) confirmed writing can be deferred to 2-week sprint; priority is publication-grade results |
| Timeline | Proposal deadline June 13 (7 days away) | **Technical lock ~Oct 1; writing Oct 1–15** | Proposal already submitted; revised per actual syllabus dates |
| Threshold baseline | Flagged as "pending confirmatory run" | **Locked with full event-level metrics** | Threshold pipeline finalized and confirmed (see Section XI) |
| Open optimization items | Not present | **Added Section XII** | Defines the work remaining in the optimization phase |

---

## I. DATASET

**Dataset:** CHB-MIT Scalp EEG Database (PhysioNet)

- 23 pediatric subjects (chb01–chb23)
- 18 common channels (10-20 system): FP1-F7, F7-T7, T7-P7, P7-O1, FP1-F3, F3-C3, C3-P3,
  P3-O1, FP2-F4, F4-C4, C4-P4, P4-O2, FP2-F8, F8-T8, T8-P8, P8-O2, FZ-CZ, CZ-PZ
- Sampling rate: 256 Hz
- Approximately 200 annotated seizures across all subjects
- Annotations (onset/offset timestamps) used FOR EVALUATION ONLY — never seen during training

**Fixed split (seed=42, PERMANENT — never changes):**

```
Inner train (12): chb01, chb02, chb04, chb05, chb07, chb08,
                  chb09, chb12, chb19, chb20, chb21, chb23
Val         (3):  chb10, chb11, chb22
Test        (8):  chb03, chb06, chb13, chb14, chb15, chb16, chb17, chb18
```

Val subjects serve two purposes (both fully unsupervised):
1. Best checkpoint selection during training (lowest val MSE — no ictal labels)
2. P95 threshold calibration for the locked threshold baseline (no ictal labels)

**Note on subjects with mid-recording channel changes (chb11, chb12, chb13, chb14,
chb15, chb16, chb17, chb18, chb19):** Only EDF files containing all 18 common channels
are used. Files missing any of the 18 channels are skipped silently during loading.

---

## II. APPLICATION SCOPE

This system is designed for **post-hoc EEG review assistance**, not real-time alarm.
Given a completed multi-hour EEG recording, the system outputs a set of timestamps
indicating where seizure-related connectivity transitions occur. Clinicians review these
candidate segments rather than the entire recording.

This framing is mandatory for all metric interpretation:
- FP/day of ~38–49 at the reported operating points is acceptable for post-hoc review assistance
  (~1.6–2.0 flags/hour). It is NOT a real-time alarm system (clinical real-time alarm requires
  a far lower false-alarm rate, shown infeasible here without collapsing sensitivity).
- Detection latency is a quality indicator, not a hard constraint. Detection occurs at/near
  clinical onset (no consistent pre-ictal lead is claimed).
- The clinically correct question is "when did a seizure start?", not "is this 4-second
  window anomalous?" — which is why CPD is the primary evaluation framework.

---

## III. METHODOLOGY

### 1. Preprocessing (LOCKED)

Processing is applied to 100% of the raw EEG data. Steps are applied in the following
mandatory order:

| Step | Operation | Implementation detail |
|------|-----------|----------------------|
| 1 | Bandpass filter 0.5–60 Hz | 4th-order Butterworth, zero-phase (sosfiltfilt), 3s padding per side |
| 2 | Notch filter 60 Hz | IIR notch Q=30, zero-phase (filtfilt) — removes powerline noise |
| 3 | CAR (Common Average Reference) | Applied before wPLI computation; suppresses zero-lag volume conduction |
| 4 | Amplitude artifact rejection | Drop windows where any sample exceeds 5× per-channel standard deviation. Applied to interictal windows only. |
| 5 | Z-score normalization | Per channel, per subject. Statistics computed from subsampled interictal windows (every 10th). |
| 6 | Windowing | 4-second non-overlapping windows (1024 samples at 256 Hz) |

### 2. Feature Extraction (LOCKED)

#### 2.1 Node Features

- 5 spectral band powers computed per channel via Welch PSD
- Output: X ∈ R^{18×5} per window
- Log-normalized then z-scored per window

| Band | Range | Physiological rationale |
|------|-------|------------------------|
| Delta | 0.5–4 Hz | Dominant in seizure discharge activity |
| Theta | 4–8 Hz | Temporal lobe involvement in focal seizures |
| Alpha | 8–13 Hz | Suppressed during ictal activity (confirmed in 7/8 test subjects) |
| Beta | 13–30 Hz | Motor cortex involvement |
| Gamma | 30–60 Hz | High-frequency ictal oscillations |

#### 2.2 Adjacency Matrix (Broadband wPLI + AEC)

Combined adjacency: `A = 0.5 × A_wPLI + 0.5 × A_AEC`

**wPLI (weighted Phase Lag Index):** Phase-based coupling, suppresses zero-lag volume
conduction artifacts. Formula: `wPLI_xy = |mean(imag(C_xy))| / mean(|imag(C_xy)|)`

**AEC (Amplitude Envelope Correlation):** Amplitude-based coupling; complements wPLI.

**Alpha = 0.5:** Confirmed optimal in v4 ablation (alpha=0.3/0.5/0.7 tested; AUROC
difference < 0.01 between values).

**Edge thresholding: top-k 20% (LOCKED)**

`apply_topk_threshold(A, keep_ratio=0.20)` retains the top 20% of undirected edge weights
per window = 30 edges out of 153 possible for 18 channels. Mean density: ~0.185.

**Why top-k% not fixed threshold:** Fixed threshold t=0.05 produced graph density 0.92–0.97
across subjects. GCN message passing on near-fully-connected graph degenerates to weighted
global mean pooling, eliminating GCN's topological advantage. Frobenius distance between
mean ictal and mean interictal adjacency matrices improved 88–411% after switching to top-k%.
This finding — that graph density is a critical but overlooked hyperparameter in GAE-based
EEG analysis — is a primary novel contribution.

#### 2.3 Node Input to Encoder

`x = concat(A_row_normalized [18], band_powers_normalized [5]) → [18, 23]`

#### 2.4 Gamma AEC (Third Ensemble Signal)

Computed independently from raw windows using `src/compute_gamma_aec.py`:
- Bandpass filter 30–60 Hz (4th-order Butterworth, filtfilt)
- Hilbert transform → amplitude envelope
- Log-transform: `log(env + 1e-10)`, zero-mean per channel per window
- Pearson correlation matrix [N, 18, 18]
- Score = mean of top-20% (30 pairs) AEC values per window
- Z-normalize using all-windows pooled (no ictal label dependency)

**Why Gamma AEC:** Band direction analysis confirmed gamma AEC increases in ictal vs
interictal for 7/8 test subjects, including chb06 (the only band with correct direction
for this inverted-wPLI subject). Delta and theta AEC simultaneously invert chb06 and
chb17. Gamma AEC standalone AUROC = 0.7546.

### 3. Graph Autoencoder (GAE) — Joint Reconstruction (LOCKED)

```
Encoder: GCNConv(23 → 64) + ReLU → GCNConv(64 → 16) → Z ∈ R^{18×16}
A Decoder: clamp(Z @ Z^T, 0, 1)
X Decoder: MLP(16 → 32 → 5)
Loss:  MSE(A, A_hat) + 0.1 × MSE(X_norm, X_hat)
Score: MSE(A, A_hat) + 0.1 × MSE(X_norm, X_hat) per window
```

Trained on interictal windows from 12 inner train subjects only.
Best val MSE: ~0.01329. Model file: best_model_joint_lambda01.pt.

### 4. Temporal LSTM (LOCKED)

- Input: z_pool(t) = mean(Z(t)) ∈ R^{16} per window
- LSTM(input=16, hidden=64, layers=2)
- Lookback: K=15 windows (60s context)
- Predicts z_pool(t) from [z(t−K), ..., z(t−1)]
- Boundary detection: cosine_sim < 0.3 → reset context
- Score: MSE(z_actual(t), z_predicted(t)) per window

### 5. Ensemble Score (LOCKED)

Three signals are z-normalized (all windows pooled, no ictal label dependency) and combined:

```
z_ensemble(t) = 0.35 × z_recon(t) + 0.30 × z_temporal(t) + 0.35 × z_gamma(t)
```

Z-normalization formula (all-windows pooled — methodologically clean):
```python
all_s = np.concatenate([scores_inter, scores_ictal])
med   = np.median(all_s)
mad   = np.median(np.abs(all_s - med)) + 1e-9
z_i   = (scores_inter - med) / mad
z_c   = (scores_ictal  - med) / mad
```
Rationale: ictal windows ≈ 0.18% of total → median and MAD virtually identical to
interictal-only statistics. No ictal timestamps used. Fully unsupervised.

### 6. PELT Change Point Detection (LOCKED — Final Detection Stage)

PELT (Killick et al. 2012) minimizes:

```
V(τ, n) = Σ_{k=1}^{K+1} [C(y_{τ_{k-1}+1:τ_k}) + β]
```

where C is the L2 cost function and β is the BIC penalty.

**Configuration (all LOCKED):**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Cost function | model="l2" (Least-Squares) | Optimal for detecting mean shifts in 1D z-normalized signal |
| Variance estimator | MAD-based: s² = (1.4826 × MAD)², **computed from interictal/background only** | Robust to multi-session baseline drift (chb17); **makes the penalty seed-independent** (the bootstrap-padded buffers no longer perturb s², so detection is deterministic) |
| Search grid | jump=5 (20-second resolution) | Within clinical tolerance; 2.5× faster than jump=2 |
| Penalty | β = pen_mult × s² × log(n) | Data-driven BIC; no ictal labels required |
| Penalty sweep | pen_mult ∈ {0.3, 0.5, 1.0, 2.0, 5.0, 10.0} | Generates the sensitivity–FP/day trade-off curve |
| **Magnitude filter (NEW)** | **keep a change point only if its local \|mean shift\| ≥ the `min_mag_pct`-th percentile of interictal change-point magnitudes** (local window = 15 each side; `min_mag_pct` = 60 or 70 at the locked operating points) | **Removes the small-shift change points that caused systemic over-segmentation; label-free (calibrated on interictal magnitudes); direction-agnostic** |
| Buffer padding | Bootstrap resampling from inter_scores | Preserves σ²; prevents synthetic-zero dilution |
| Smoothing | 1-min centered MA (window=15) | Attenuates transient noise; preserves seizure elevation |

*(Event-matching tolerances, merge gap, and post-ictal handling are NOT algorithm parameters — they belong to the SzCORE evaluation protocol in Section IV.)*

**Single source of truth:** the detection algorithm (seed-independent PELT penalty + magnitude filter,
label-free) is implemented once in `cpd_pipeline_v14.py` as `detect_changepoints` / `detect_events`.
Both the evaluation and the future web demo call it, so the reported algorithm and the deployed
algorithm are guaranteed identical. Locking CHB-MIT numbers passes the interictal mask for exact
reproducibility; the demo runs label-free (whole-signal statistics, verified ≈identical at the
~0.2% seizure prevalence).

**Why CPD instead of threshold (mandatory in Chapter 2 Decision Matrix):**
- P95 val interictal: fully unsupervised but conservative; detects upward shifts only
- Youden's J: requires val ictal labels → violates unsupervised claim
- FDR-driven (≤2.0/h): requires tau_z=5.8 → sensitivity ≈ 0 (shown infeasible)
- CPD is threshold-free, data-driven (BIC penalty), direction-agnostic
- CPD answers the clinical question: "when did the distribution change?" not "is this window anomalous?"
- chb06 (inverted connectivity) remains the hardest case: even direction-agnostic CPD detects only
  2–4/10 seizures (the ictal connectivity shift is too weak to place change points near most seizures) —
  documented as a genuine limitation, not a success (Section VIII).

---

## IV. EVALUATION FRAMEWORK

The evaluation follows the **SzCORE framework (Dan et al., *Epilepsia* 2024)**, the community
standard for EEG seizure-detection validation. CHB-MIT is explicitly exempted by SzCORE from the
19-channel unipolar requirement ("provides only bipolar channels … analyzed with the original
bipolar montage"), so the thesis's 18-channel bipolar montage is SzCORE-compliant as-is. Scoring
uses the official `timescoring` library as the authoritative scorer.

### Two-Tier Evaluation (LOCKED)

**Tier 1 — Sample/window level (threshold-independent):**
- **Subject-wise AUROC** (ictal vs interictal window ranking) with DeLong 95% CI.
- AUC-PR (reported as lift-over-chance, given ~0.2% prevalence) with bootstrap CI; Mann-Whitney U with effect size r.

**Tier 2 — Event level (SzCORE, the clinically meaningful tier):**
- **Matching:** any-overlap, with **30 s pre-ictal / 60 s post-ictal tolerance**; predicted events **merged if < 90 s apart**; events **split if > 5 min**.
- **Sensitivity** = TP/(TP+FN) — fraction of reference seizures detected.
- **Precision** = TP/(TP+FP).
- **F1** = harmonic mean of sensitivity and precision.
- **False positives per day (FP/day)** — the primary false-alarm metric (denominator = interictal hours).
- **Latency** = predicted-onset − reference-onset for matched events (reported, not optimized).

The pipeline is a transition detector, so each change point is represented as a minimal event interval
and the SzCORE rules above are applied by `timescoring`. The post-ictal period is treated as a SzCORE
"don't-care" region (a change point near a seizure is always credited; only change points deep in the
post-ictal buffer and far from any seizure are excluded — they count as neither TP nor FP). This is an
evaluation-time, label-aware step and is NOT part of the detection algorithm.

**Why not accuracy/specificity/F1-as-primary:** SzCORE explicitly excludes TN-based metrics
(specificity, accuracy) because non-seizure samples vastly outnumber seizure samples (~0.2% prevalence),
inflating them with no clinical meaning. Window-level sensitivity also understates clinical utility:
detecting any window within a seizure is a clinical TP, which is why the event tier is primary.

**Seed robustness:** detection rate is stable to ±2–3 % across 8 bootstrap-padding seeds; the
seed-independent PELT penalty (Section III.6) removes the padding dependence.

---

## V. FINAL LOCKED CPD RESULTS (SzCORE protocol)

**Window-level macro AUROC (threshold-independent):** ≈ 0.80 (per-subject in `eval_window_level.csv`).

**Event-level operating points (timescoring authoritative; 8 test subjects, 76 seizures, 278.2 interictal h):**

| Operating point | mag% | pen | Sensitivity (95% CI) | Sens macro±SD | Precision (CI) | F1 | FP/day (CI) |
|---|---|---|---|---|---|---|---|
| **Balanced (primary)** | 60 | 1.0 | **0.750** [0.642, 0.834] | 0.748 ± 0.262 | 0.114 [0.089, 0.145] | 0.199 | **38.0** [34.6, 41.8] |
| **High-sensitivity** | 70 | 0.3 | **0.816** [0.714, 0.887] | 0.804 ± 0.196 | 0.099 [0.078, 0.125] | 0.177 | **48.6** [44.7, 52.8] |
| Low-FP (secondary) | 70 | 2.0 | 0.611 | — | 0.168 | — | 18.8 |

Pooled (micro) aggregation = SzCORE-correct. CIs: Wilson (proportions), exact Poisson (FP/day).
Balanced: TP 57 / FN 19 / FP 441. High-sens: TP 62 / FN 14 / FP 564.

**Latency:** macro ≈ 0 to +7 s (mildly post-onset); per-subject mixed (some negative, most positive).
The system detects **at/near clinical onset**; it does NOT demonstrate a consistent pre-ictal lead
(the v3 "negative latency / pre-ictal" claim was an artifact of the old scoring and is withdrawn).

**Per-subject event sensitivity (high-sensitivity point, mag70 / pen 0.3):**

| Subject | Window AUROC | Event sens | Precision | FP/day | Latency (s) | Notes |
|---|---|---|---|---|---|---|
| chb03 | 0.96 | 7/7 = 1.00 | 0.082 | 49.4 | −6.9 | Strong gamma + reconstruction |
| chb06 | 0.44 | 4/10 = 0.40 | 0.037 | 37.1 | +3.0 | **Inverted connectivity — genuine limitation** |
| chb13 | 0.82 | 10/12 = 0.83 | 0.154 | 40.2 | −2.4 | Reconstruction dominant |
| chb14 | 0.73 | 8/8 = 1.00 | 0.078 | 87.9 | +5.0 | LSTM + reconstruction |
| chb15 | 0.82 | 18/20 = 0.90 | 0.191 | 46.3 | +14.7 | Strong reconstruction |
| chb16 | 0.91 | 8/10 = 0.80 | 0.186 | 44.3 | +6.0 | Gamma dominant (recovered by buffer-fix) |
| chb17 | 0.77 | 2/3 = 0.67 | 0.050 | 43.6 | −12.0 | Multi-session non-stationarity |
| chb18 | 0.92 | 5/6 = 0.83 | 0.056 | 56.7 | 0.0 | Strong reconstruction + gamma |

*(Balanced point mag60/pen1.0 per-subject: chb03 7/7, chb06 2/10, chb13 10/12, chb14 8/8, chb15 17/20, chb16 6/10, chb17 2/3, chb18 5/6.)*

---

## VI. KEY SCIENTIFIC FINDINGS

**Finding 1 — Graph density is a critical but overlooked hyperparameter:**
Fixed threshold t=0.05 → density 0.92–0.97 → GCN degenerates to global mean pooling.
Top-k 20% thresholding increases Frobenius distance between ictal and interictal mean
adjacency matrices by 88–411% across subjects. No prior EEG-GAE paper documents this.

**Finding 2 — Three complementary seizure detection signals:**
Reconstruction anomaly (phase coupling change), temporal transition (LSTM), and Gamma AEC
(HFO amplitude coupling) are mechanistically complementary. No subject fails all three
simultaneously (except chb06, partially recovered by gamma).

| Mechanism | Best subjects | Weakest subjects |
|-----------|--------------|-----------------|
| Reconstruction anomaly | chb13, chb15, chb18 (long seizures) | chb06 (brief/inhibitory), chb16 |
| Temporal transition (LSTM) | chb14, chb16 (abrupt onset, short) | chb15, chb18 (long fills lookback) |
| Gamma AEC (HFO) | chb03, chb06, chb16, chb17 | chb13 (marginal) |

**Finding 3 — Direction-agnostic CPD partially captures inhibitory seizure mechanisms, but chb06 remains a genuine limitation:**
chb06 has inverted wPLI (ictal connectivity LOWER than interictal at all thresholds), so any
fixed threshold structurally fails. CPD is direction-agnostic and recovers some of these via the
downward transition, but only **2–4/10 seizures** are detected (the ictal connectivity shift is too
weak/brief to place change points near most chb06 seizures). This is reported honestly as a
limitation of the connectivity representation for inhibitory/brief focal seizures, not as a success.

**Finding 4 — Detection occurs at/near clinical onset (no consistent pre-ictal lead):**
Under the SzCORE protocol, matched-event latency is macro ≈ 0 to +7 s and per-subject mixed
(some negative, most positive). The system reliably localizes seizures **at or near** the clinical
annotation; it does **not** demonstrate a systematic pre-ictal lead. (The v3 claim of negative
latency / pre-ictal detection was an artifact of the previous onset-only scoring and is withdrawn —
this more conservative statement is the defensible one.)

**Finding 5 — Novelty confirmed:**
Literature search (Perplexity AI, June 2026) found no peer-reviewed papers (2023–2026)
combining GAE anomaly scoring with PELT change point detection for unsupervised seizure
localization on CHB-MIT.

---

## VII. LITERATURE COMPARISON

*(Numbers below are placeholders/partial. A full, verified 2023–2026 comparison table — real links, exact metrics, protocol-comparability flags — is an OPEN Phase-B task; see `PLAN_AND_STATUS.md`.)*

| System | Method | Supervised? | Protocol | Event Sens | Precision | FP/day |
|--------|--------|-------------|----------|-----------|-----------|--------|
| Yildiz 2022 | Unsupervised AE | No | window AUROC | AUROC **0.68** (corrected) | — | — |
| SzCORE RF (Dan 2024) | RF + AZC | Yes | patient-indep, event | 0.37 | 0.65 | 1.66 |
| SzCORE Transformer (Dan 2024) | Vision-Transformer | Yes | patient-indep, event | 0.765 | 0.54 | 40.6 |
| SzCORE XGBoost (Dan 2024) | XGBoost + DWT | Yes | patient-indep, event | 0.671 | 0.75 | 2.09 |
| **This work (balanced)** | **GAE+LSTM+AEC + PELT** | **No** | **patient-indep, event (SzCORE)** | **0.750** | 0.114 | 38.0 |
| **This work (high-sens)** | **GAE+LSTM+AEC + PELT** | **No** | **patient-indep, event (SzCORE)** | **0.816** | 0.099 | 48.6 |

**Framing note (mandatory for Chapter 4):** Supervised patient-specific methods require prior labeled
seizures from the same patient — impossible for a newly monitored patient. This work is **unsupervised
and patient-independent**, yet its event sensitivity (0.75–0.82) is **comparable to or above the
SzCORE supervised subject-independent baselines** (0.37–0.765), at the cost of lower precision / higher
FP/day — the expected unsupervised trade-off, acceptable under the post-hoc review framing. Window AUROC
≈ 0.80 exceeds the corrected Yildiz 2022 baseline (0.68). The previous "pre-ictal detection" claim is
withdrawn (see Finding 4).

---

## VIII. KNOWN LIMITATIONS

All of the following must be acknowledged in Chapter 1.4 and Chapter 4.5
("Clinical and broader applicability"):

1. **Inverted connectivity mechanism (chb06):** wPLI/AEC connectivity DECREASES during
   ictal for this subject. Direction-agnostic CPD detects only **2–4/10** seizures; the
   ictal shift is too weak/brief to place change points near most seizures. Genuine limitation.

2. **Multi-session non-stationarity (chb17):** Three recording sessions with large between-session
   baseline drift; only 3 seizures total, so per-subject metrics are noisy. Session-boundary
   suppression is listed as future work.

3. **FP/day ≈ 38–49 at the reported operating points:** Acceptable for post-hoc review triage
   (~1.6–2.0 flags/hour); incompatible with real-time alarm. This is stated wherever FP/day appears.

4. **Brief focal seizures:** chb06 and chb16 (6–14 s). The magnitude filter + buffer-fix recovered
   chb16 (to ~8/10) but chb06 remains limited. Connectivity propagation within a 4 s window is the
   bottleneck for the briefest events.

5. **Latency interpretation:** Detection is at/near clinical onset (macro ≈ 0 to +7 s), not pre-ictal.
   Non-overlapping 4 s windows set a 4 s floor on temporal resolution.

6. **Pediatric refractory cohort only:** CHB-MIT is pediatric drug-resistant epilepsy.
   May not generalize to adult, ambulatory, or drug-responsive populations.

7. **Alpha ablation not re-validated on sparse pipeline:** alpha=0.5 was confirmed on the
   dense pipeline (v4 ablation). wPLI and AEC are stored as combined adjacency only.

8. **Timeline reconstruction alignment assumption:** bootstrap-padding algorithm assumes
   inter_scores arrays are stored in the same chronological order as EDF files processed
   by preprocessing.py (confirmed via `sorted(glob(...))`, but must be preserved in any
   future preprocessing rerun).

---

## IX. DECISIONS LOG (COMPLETE, LOCKED)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Problem framing | Temporal localization (CPD) | Clinically correct; threshold-free; direction-agnostic |
| Edge threshold | top-k 20% | Dense graph eliminates GCN topology; Frobenius diagnostic +88–411% |
| Loss function | Joint MSE (λ=0.1) | Continuous adj [0,1]; BCE worse (0.449); joint captures spectral signal |
| Decoder | Clamped inner product | Sigmoid saturates; MLP decoder worse; tanh (sPLI) overall worse |
| Anomaly score | Standard MSE over 324 elements | Captures topology + weight change; masked MSE removes topology signal |
| Alpha (wPLI/AEC) | 0.5 | Validated v4 ablation; components not stored separately |
| Z-normalization | ALL windows pooled (median/MAD) | No ictal label dependency; ictal 0.18% → robust |
| Gamma AEC | 30–60 Hz band, top-20% pairs | Correct direction 7/8 subjects; partial recovery of chb06 |
| Delta/Theta AEC | Rejected | Simultaneously inverts chb06 and chb17 |
| Ensemble weights | 0.35/0.30/0.35 | Fine sweep confirmed |
| TTA | Dropped | interictal_adjs.npy built with seizure timestamps → label leakage |
| Youden's J | Dropped | Requires val ictal labels → violates unsupervised claim |
| Threshold-based detection | Abandoned as primary | CPD replaces entirely; threshold retained only as comparison baseline |
| CPD cost function | L2 (model="l2") | 1D z-normalized signal; mean shift is primary mechanism; RBF is O(n²) |
| CPD variance estimator | MAD-based (1.4826 × MAD)² | Robust to multi-session baseline drift (chb17); breakdown point 50% |
| CPD jump | 5 (20s resolution) | Within clinical tolerance ±30s; 2.5× faster than jump=2 |
| Bootstrap padding | Bootstrap from inter_scores | Preserves σ²; prevents synthetic zero dilution and artificial boundaries |
| Smoothing | 1-min centered MA (window=15) | Attenuates transient noise; preserves sustained seizure elevation |
| Overlapping windows (P3.1) | Permanently cancelled | AUROC 0.801 > 0.76 trigger threshold |
| LSTM K sweep | Cancelled | Larger K degrades chb15/chb18 by design |
| VGAE | Rejected | KL diverges with inner product decoder |
| CE classifier | Negative result | Z-space cross-subject generalization fails |
| sPLI (E_DIRECTED) | Negative result | Macro AUROC −0.024; chb14 regressed to inverted |
| Architecture B2 (128/32) | Negative result | ΔAUROC = −0.0003 |
| Majority vote | Rejected | Detection rate drops 22% at mc=2 |
| Second dataset (Siena) | Deferred | Adult vs pediatric population shift |
| EMA (AUROC claim) | Rejected | Methodological artifact from separate array processing |
| EMA (FDR/h contribution) | Valid but secondary | −37% FDR/h on interictal array only; not primary result |
| **Evaluation framework (Phase A)** | **SzCORE (Dan 2024)** | Community standard; CHB-MIT bipolar is SzCORE-exempt/compliant; drop TN-based metrics; FP/day primary |
| **CPD penalty variance (Phase A)** | **interictal-only s² (seed-independent)** | Removes bootstrap-padding seed dependence → deterministic detection |
| **CPD magnitude filter (Phase A)** | **prune CPs below `min_mag_pct` percentile of interictal CP magnitudes** | Fixes systemic over-segmentation; label-free; the key precision fix |
| **Post-ictal buffer (Phase A)** | **SzCORE "don't-care" (eval-only)** | Keep CPs near a seizure; drop only deep-buffer non-aligned CPs; fixed the bug that zeroed chb16 |
| **Operating points (Phase A)** | **mag60/pen1.0 (balanced), mag70/pen0.3 (high-sens)** | Pareto-frontier selection, confirmed by timescoring |
| **Single-source algorithm (Phase A)** | **`cpd_pipeline_v14.py`** | One detection algorithm shared by evaluation and the future demo |
| **Week-4 extra FP interventions** | **Skipped** | Magnitude filter already met the FP-reduction goal; chb17/chb06 → future work |

---

## X. REJECTED EXPERIMENTS (for Chapter 3/4 summary table)

| Experiment | Macro AUROC | Reason for rejection |
|-----------|-------------|----------------------|
| BCE loss | 0.449 | Wrong for continuous adjacency [0,1]; reconstructs both states equally well |
| Masked MSE | 0.665 | Removes topology-change signal; chb13 −0.044, chb14 −0.049 |
| Max anomaly score | 0.626 | Single worst-case edge is noisier than mean over 30 edges |
| Architecture B2 (128/32) | 0.656 | ΔAUROC = −0.0003; capacity not the bottleneck |
| VGAE | 0.677 | KL diverges with clamped inner-product decoder (large ‖Z‖ vs N(0,I) conflict) |
| CE classifier | 0.653 | Z-space ictal signature fails cross-subject generalization |
| sPLI (signed PLI) | 0.663 | chb14 regresses to inverted; chb06 still inverted; macro −0.024 |
| Multiband wPLI | 0.618 | 0.47× Frobenius signal vs broadband (fewer freq bins → less stable wPLI) |
| Majority vote (mc=2) | — | Event sensitivity drops 22%; kills short-seizure subjects |
| TTA (Test-Time Adaptation) | +0.016 AUROC | Label leakage: interictal_adjs.npy built using ictal timestamps |
| Youden's J threshold | — | Semi-supervised: requires val ictal labels |
| FDR-driven threshold | — | Requires tau_z=5.8 → sensitivity ≈ 0 |
| Multivariate PELT (3D input) | — | n_cps explodes >1000; channel noise multiplies instead of averages |
| ROI-guided PELT | — | Global P90 gating too aggressive; subtle seizures excluded |
| L1-cost PELT | — | Blind to smooth ramps produced by temporal smoothing |

---

## XI. LOCKED THRESHOLD BASELINE

This is the single locked threshold pipeline retained for comparison against CPD in
Chapter 3 and Chapter 4. It uses the same 3-signal ensemble (no TTA) as the CPD
pipeline, making the comparison methodologically fair.

**Configuration:**
- Signal: 3-signal ensemble (z_recon + z_temporal + z_gamma), NO TTA
- Z-normalization: all-windows pooled (no ictal label dependency)
- Threshold: P95 of val interictal z-scores
- Tau_z (P95 val interictal): **2.9218**
- This is the only fully unsupervised threshold variant (no ictal labels at any step)

**Locked Threshold Baseline — Final Results:**

| Metric | Value |
|--------|-------|
| Macro AUROC (threshold-independent) | 0.7955 |
| Window Sensitivity | 0.382 |
| Window Specificity | 0.945 |
| Event Sensitivity | 62/76 = **81.6%** |
| FCP/h (macro avg) | **15.9** |
| Mean Detection Latency | **+11.0s** (always positive — structurally post-ictal) |
| chb06 performance | 2/10 (structural failure at any tau) |

**Per-subject event-level breakdown (tau_z = 2.9218, P95):**

| Subject | GT | TP | FN | Ev Sensitivity | FCP/h | Latency (s) |
|---------|----|----|----|----------------|-------|-------------|
| chb03 | 7 | 7 | 0 | 100.0% | 18.52 | +6.9 |
| chb06 | 10 | 2 | 8 | 20.0% | 10.08 | +10.0 |
| chb13 | 12 | 11 | 1 | 91.7% | 14.82 | +11.3 |
| chb14 | 8 | 6 | 2 | 75.0% | 6.44 | +10.0 |
| chb15 | 20 | 19 | 1 | 95.0% | 20.19 | +17.9 |
| chb16 | 10 | 9 | 1 | 90.0% | 26.04 | +4.9 |
| chb17 | 3 | 3 | 0 | 100.0% | 14.41 | +18.7 |
| chb18 | 6 | 5 | 1 | 83.3% | 16.85 | +8.0 |
| **Macro** | **76** | **62** | **14** | **81.6%** | **15.9** | **+11.0s** |

Note: chb06 is the structural failure case (inverted connectivity) — 2/10 detection
holds regardless of how tau_z is varied, because the median ictal z-score is below the
interictal median (mzi = −0.068). chb17 detects all 3 seizures but at high latency (+18.7s)
due to multi-session baseline drift generating slow-rising false-positive clusters before the
true onset exceeds threshold.

**Threshold tau sweep (full operating curve, for Chapter 3 table):**

| tau_z | Event Sensitivity | FCP/h | Mean Latency |
|-------|-------------------|-------|-------------|
| 1.0 | 97.4% | 22.5 | +5.4s |
| 1.5 | 94.7% | 27.2 | +5.7s |
| 2.0 | 89.5% | 24.7 | +7.9s |
| 2.5 | 85.5% | 20.3 | +9.8s |
| 3.0 | 81.6% | 15.22 | +11.1s |

*Primary results above use tau_z = 2.9218 (exact P95 of val interictal z-scores), which falls
between tau=2.5 and tau=3.0 in this sweep. At tau=2.9218: FCP/h=15.9, latency=+11.0s.
At tau=3.0: FCP/h=15.22, latency=+11.1s. Event sensitivity (62/76=81.6%) is identical at
both values because no additional seizures are caught between these two tau levels.*

**Why simpler threshold variants were rejected (for Chapter 2 Decision Matrix):**

| Variant | Status | Reason |
|---------|--------|--------|
| tau_z=2.0 (sensitivity-maximizing) | Rejected as primary | Chosen by sensitivity maximization, not principled |
| Youden's J (tau_z=1.48) | Semi-supervised only | Requires val ictal labels to compute Sensitivity |
| Platt scaling (P=0.5 sigmoid) | Semi-supervised only | MLE fit requires val ictal labels |
| FDR-driven (≤2.0/h target) | Infeasible | Requires tau_z=5.8; sensitivity ≈ 0 |
| **P95 val interictal (tau_z=2.9218)** | **✅ Locked baseline** | **Fully unsupervised; no ictal labels at any step** |

**Threshold vs CPD — head-to-head (⚠️ computed under the PREVIOUS onset-match protocol, NOT SzCORE):**

> The threshold baseline below was scored with the old onset-match protocol (FCP/h, ±30 s onset
> matching) and is NOT directly comparable to the locked SzCORE event results in Section V. It is
> retained as a development-record comparison showing CPD's qualitative advantages (no calibration,
> direction-agnostic). The CPD column here uses superseded numbers; for current CPD performance use
> Section V. Re-scoring the threshold baseline under SzCORE is optional future work.

| Metric (old onset-match protocol) | Threshold P95 | CPD pen=0.3 (superseded) | Note |
|--------|--------------|------------|--------|
| Event Sensitivity | 81.6% | 84.2% | comparable |
| FCP/h | 15.9 | 30.8 | threshold lower (old metric) |
| chb06 detection | 2/10 | (old 6/10; **now 2–4/10 under SzCORE**) | see Section V |
| Calibration needed | P95 from val data | None (BIC data-driven) | **CPD** |
| Direction-agnostic | No | Yes | **CPD** |

**CPD's irreducible advantage:** no calibration (data-driven BIC penalty) and direction-agnostic
detection of inhibitory connectivity changes — architecturally impossible for a fixed threshold.
(The earlier "pre-ictal / negative latency" advantage is withdrawn; see Section V/Finding 4.)

---

## XII. OPTIMIZATION ITEMS — STATUS (Phase A closed)

These were the open items at the start of the optimization phase. **Phase A is now closed**;
the primary item is resolved. Current plan/status lives in `PLAN_AND_STATUS.md`.

### 12.1 PRIMARY: Reduce CPD false alarms without sacrificing sensitivity — ✅ RESOLVED

**Resolved in Phase A.** The framing changed from "FCP/h" to the SzCORE **FP/day**, and the
over-segmentation (the real cause of false alarms) was fixed by the **magnitude filter** plus the
**buffer don't-care** correction. At the locked operating points the system reaches event sensitivity
0.75 (FP/day 38) and 0.816 (FP/day 48.6) — competitive with the SzCORE **supervised** Transformer
baseline (0.765 / 40.6). The originally-listed candidate tweaks below were therefore NOT needed
(superseded by the magnitude filter), and are kept only as a record:
- Subject-specific smoothing window (1-min MA is fixed; adaptive window based on local
  signal variance may reduce false peaks without blunting seizure ramps)
- Rolling MAD variance (re-estimate s² on a sliding window rather than global signal)
- Session-boundary CP suppression for chb17 (detect session transitions from timestamp
  gaps in summary files, then suppress CPs at those boundaries — no ictal labels needed)
- Post-hoc CP merging: increase merge gap from 32s if sustained FCP clusters appear
  (must be validated not to merge true seizures)

### 12.2 SECONDARY: Improve window-level sensitivity

**Current state:** Window sensitivity at P95 threshold = 0.382 (38.2% of ictal windows
correctly flagged). CPD does not have a direct window-level equivalent metric.

**Target:** Increase to ≥0.50 without degrading specificity below 0.90.

**Note:** A reviewer will compare AUROC (0.7957) to Yildiz 2022 (~0.76) and ask why
window sensitivity is still moderate at 38.2% despite higher AUROC. The answer is that
the threshold is set conservatively (P95, fully unsupervised) and CPD doesn't optimize
window-level sensitivity directly. This needs to be explicitly framed in Chapter 4.

### 12.3 SECONDARY: Statistical validation for publication

**Required for Q2/Q3 submission:**
- Mann-Whitney U test: ictal vs interictal ensemble scores per subject (provide p-values)
- AUROC confidence intervals: either bootstrap (1000 iterations, 95% CI) or DeLong method
- FCP/h confidence intervals: Poisson rate estimation per subject
- Cross-subject variance: mean ± SD for each metric across the 8 test subjects

**None of these require new experiments** — they are statistical post-processing on
the existing cpd_results_v12_combined.csv and the threshold results.

### 12.4 TERTIARY: Latency interpretation — ✅ RESOLVED (claim withdrawn)

**Resolved.** Under SzCORE scoring, matched-event latency is macro ≈ 0 to +7 s (per-subject mixed),
i.e. detection at/near clinical onset with no consistent pre-ictal lead. The earlier "pre-ictal /
negative latency" framing was an artifact of the old onset-only scoring and is withdrawn. Chapter 4
should state the conservative position (reliable near-onset localization) rather than a pre-ictal claim.

### 12.5 TERTIARY: chb06 partial improvement strategy

**Current state:** **2/10 (balanced) to 4/10 (high-sens) under SzCORE** — the weakest test subject.
Gamma AEC only provides ~+9% ictal vs interictal margin for this subject. Documented as a genuine
limitation (Section VIII); the items below are optional future work, not required for the thesis.

**Candidates (low-cost, no retraining):**
- Explore whether topology-standalone features (spectral radius, Fiedler value) can be
  added as a 4th ensemble component for all subjects without hurting the 7/8 who already
  work well. Note: prior experiment showed topology improves chb06 but hurts chb17.
  Requires a principled argument for why it is valid to add it without per-subject
  detection of "inverted mechanism" (which would require ictal labels).

### 12.6 TERTIARY: Evaluation protocol documentation

For journal submission, the evaluation protocol needs to be written with enough detail
that it is reproducible by an independent reviewer:
- Exact algorithm for timeline reconstruction (EDF chronological ordering, buffer padding)
- Exact TP matching criterion (±30s, first-CP-to-onset latency, group matching logic)
- Exact FP counting rule (merged groups not matching any seizure / interictal hours)
- Confirmation that numpy.random.seed(42) is set before any bootstrap sampling
- Sanity check: total seizures evaluated = 76 (per-subject: 7+10+12+8+20+10+3+6)

---

## XIII. SIX DECISION MATRICES (ABET PI 4C — Mandatory for Chapter 2)

All five must appear in Chapter 2 under the exact title format
"Decision Matrix for [aim]" as required by the ABET PI 4C rubric criterion.

| Matrix | Options evaluated | Winner | Key evidence |
|--------|------------------|--------|--------------|
| DM1: Edge threshold | Fixed t=0.05 vs Top-k 20% | **Top-k 20%** | Frobenius +88–411%; GCN topology degradation at density >0.90 |
| DM2: Loss function | MSE vs BCE vs Joint MSE | **Joint MSE (λ=0.1)** | chb14 mzi: 0.661→1.490→1.633; BCE AUROC 0.449 |
| DM3: Anomaly score | Standard MSE vs Masked MSE vs Max score | **Standard MSE (324 elements)** | Masked MSE removes topology signal (chb13 −0.044, chb14 −0.049) |
| DM4: Detection method | Threshold (P95) vs CPD (PELT) | **CPD (PELT)** | Threshold always positive latency; structurally fails chb06; CPD pre-ictal and direction-agnostic |
| DM5: Signal components | wPLI only vs AEC only vs Gamma only vs Combined | **Combined 3-signal ensemble** | No subject fails all three; ensemble AUROC 0.7957 vs best single-signal 0.7546 |
| DM6: Deployment strategy | Cloud API vs On-premise hospital server vs Edge device (bedside) | **On-premise hospital server** | Weighted score 4.1 vs 3.1 (edge) vs 2.1 (cloud); driven by societal (patient-data privacy, pediatric cohort) and economic (CPU-only, no per-inference cloud cost) criteria — see §13.1 below |

---

### 13.1 DM6 — Decision Matrix for Deployment Strategy

DM1–DM5 above resolve the *technical* design questions (loss, edge sparsification, anomaly
score, detection method, signal components). ABET PI 4C also requires that at least one
decision explicitly weighs **global, economic, environmental, and societal** impact — a
distinct question from technical performance, and one DM1–DM5 do not address. DM6 fills
this gap: given the locked technical pipeline, **where and how should it be deployed?**

**Decision context.** The system is framed as a post-hoc review-triage tool (Section II),
not a real-time alarm, and is built to be **CPU-only at inference time** (`cpd_pipeline_v14.py`
runs no GPU; only offline component export needs GPU). This constrains which deployment
options are realistic and gives the matrix genuine technical grounding rather than a
generic CSR exercise.

**Options evaluated:**

| Option | Description |
|--------|-------------|
| A — Cloud API | Hospital uploads EEG to a central server (AWS/GCP-style); inference runs remotely; results returned via API |
| B — On-premise hospital server | Inference server (CPU-only, per the locked label-free design) installed inside the hospital's own network |
| C — Edge device at bedside | Compact local-inference device (e.g. Jetson-class) attached directly to the EEG acquisition unit |

**Criteria and weights** (chosen to map onto the four PI 4C dimensions, not generic
categories):

| Criterion | Weight | Rationale for weight |
|-----------|--------|----------------------|
| Economic — infrastructure + operating cost | 30% | Determines whether lower-resource hospitals can adopt the tool at all — directly tied to the thesis's "reduce review burden, don't add cost" framing (Section XII, item 12.4 FP/day → review-burden reframe) |
| Societal — data accessibility + patient privacy | 30% | CHB-MIT is a **pediatric** cohort; pediatric EEG leaving a hospital network is a genuine privacy concern, and equitable access for lower-resource settings is the direct real-world motivation behind this line of work |
| Environmental — power/carbon of continuous operation | 20% | The system's CPU-only inference design (no GPU needed at deployment) is a real, quantifiable point of comparison across options, not a token entry |
| Global/scalability — deployability across many hospitals | 20% | The method is patient-independent (no per-patient fine-tuning), which is a genuine scalability advantage worth scoring explicitly |

**Scored table** (1–5, justified from the locked design):

| Criterion | A: Cloud API | B: On-premise | C: Edge device |
|-----------|:---:|:---:|:---:|
| Economic (30%) | 2 — recurring storage/bandwidth cost for multi-hour, multi-channel EEG | 4 — one-time cost, no usage-based fee; matches the CPU-only design | 3 — per-bed hardware cost, but no network infrastructure needed |
| Societal (30%) | 1 — pediatric EEG leaves the hospital network; highest privacy exposure | 5 — data never leaves the hospital's internal network; best fit for sensitive pediatric data | 4 — data never leaves the device, but harder to audit/maintain centrally |
| Environmental (20%) | 2 — inference in a shared datacenter; energy cost hidden inside shared infrastructure | 4 — CPU-only, no continuous GPU draw; reuses hospital IT infrastructure already in place | 3 — good per-device energy efficiency, but cost replicates per bed |
| Global/scalability (20%) | 4 — scales horizontally with minimal per-site setup | 3 — each hospital needs its own install/maintenance | 2 — cost and maintenance scale linearly with device count |

**Weighted scores:**
```
A (Cloud API):      0.30(2) + 0.30(1) + 0.20(2) + 0.20(4) = 2.1
B (On-premise):     0.30(4) + 0.30(5) + 0.20(4) + 0.20(3) = 4.1
C (Edge device):     0.30(3) + 0.30(4) + 0.20(3) + 0.20(2) = 3.1
```

**Winner: B — On-premise hospital server.** Margin over the runner-up (C) is 1.0 points —
well above the 10% under-differentiation threshold used elsewhere in this project's
decision matrices (DM1–DM5), so no criterion revision is triggered.

**Revision flag / honest scope limitation:** this matrix is a **design-grounded qualitative
argument**, built from the pipeline's already-locked technical properties (CPU-only,
patient-independent), not a costed health-economics study with real hospital procurement
data. It should be presented as such — a defensible engineering judgment under PI 4C, not
a claim of validated deployment economics.

---

## XIV. FILE INVENTORY

### Authoritative files (current state — keep all)

| File | Purpose | Status |
|------|---------|--------|
| `Proposed_solution_updated_v3.md` | **This document — master plan** | Current |
| `cpd_pipeline_v13.py` | Final CPD pipeline code | LOCKED |
| `cpd_results_v12_combined.csv` | **FINAL LOCKED CPD RESULTS** | LOCKED |
| `experiment_history_v11_to_v13.md` | Merged narrative: v11+v12+v13 decisions | Reference |
| `experiment_journey_appendix.md` | Merged narrative: v4–v10 mechanistic history | Reference |
| `chb01-summary.txt` through `chb23-summary.txt` | CHB-MIT dataset metadata | Permanent |
| `21_prompts.md` | Analysis prompts for writing support | Reference |
| `Registration_Form.pdf` | **Official registration (June 10, 2026)** | Permanent |
| `Rubric.pdf` | 8-criterion rubric with point values | Permanent |
| `Report_format.pdf` | Format specification (TNR 12pt, margins, etc.) | Permanent |
| `Syllabus.pdf` | Official dates and requirements | Permanent |

### Threshold baseline files (generated June 2026 — keep)

| File | Purpose |
|------|---------|
| threshold pipeline notebook | P95 pipeline, tau sweep, event-level evaluation |
| threshold results CSV | Per-subject event-level metrics at P95 |

---

## XV. THESIS CHAPTER STRUCTURE (for writing sprint Oct 1–15)

### Official Requirements from Registration Form

**Major:** Development/improvement of algorithms for image/signal/data processing
**Requirements (from signed form):**
1. Literature review — evaluating existing unsupervised and supervised methods for temporal
   seizure localization; focus on gaps related to threshold calibration and baseline drifts
2. Theoretical framework and modeling — mathematical models and flowcharts of the
   spatial-temporal anomaly scoring and change point detection pipeline
3. Implementation — complete preprocessing, scoring, and CPD pipeline using Python
4. Testing and Validation — empirical validation on CHB-MIT, event-level performance

### Chapter Map (50-page budget)

| Chapter | Title | Target (words/pages) | Status |
|---------|-------|---------------------|--------|
| Abstract | — | ~250 words / 0.6 pages | Blocked until results finalized |
| Ch.1 | Introduction | ~4,000 / 10 pages | Can draft now |
| Ch.2 | Methodology | ~6,000 / 15 pages | Can draft now (most sections) |
| Ch.3 | Results | ~3,000 / 7.5 pages | Blocked until optimization complete |
| Ch.4 | Discussion | ~4,000 / 10 pages | Partially draftable |
| Ch.5 | Conclusion | ~800 / 2 pages | Blocked until results finalized |

### Mandatory Section Titles (exact wording required for ABET compliance)

- Chapter 2: **"Decision Matrix for [title of study]"** — must appear exactly with 5 matrices,
  covering global, economic, environmental, and societal impacts (ABET PI 4C)
- Chapter 4: **"Clinical and broader applicability"** — must appear exactly, with specific
  deployment context, both positive and negative impacts, and concrete deployment requirements
  (ABET PI 4C)

---

## XVI. EXPERIMENT LOG

| ID | Description | Status | Best Result |
|----|-------------|--------|-------------|
| E0 | Preprocessing verification (all 23 subjects) | Complete | Correct |
| E_dense → E_sparse → E_joint | Pipeline development | Complete | AUROC 0.671 |
| E_ablations | MSE vs BCE; masked vs standard; max score; CE classifier; VGAE; B2; sPLI | Complete | All negative |
| E_temporal | Temporal LSTM (K=15) | Complete | Component of ensemble |
| P2.2_gamma | Gamma AEC band selection and computation | Complete | Standalone 0.7546 |
| 3way_ensemble | 3-signal ensemble (wPLI + LSTM + Gamma), weight sweep | Complete | AUROC 0.8012 (with TTA) / 0.7957 (clean) |
| CPD_v13 | PELT pipeline with Bootstrap padding, MAD variance, smoothing | **Complete — LOCKED** | DR 75–84%, FCP/h 24–31 |
| Threshold_baseline | P95 val interictal, event-level evaluation | **Complete — LOCKED** | DR 81.6%, FCP/h 15.9, latency +11.0s |
| **Optimization items** | **FCP/h reduction, statistical validation, evaluation protocol** | **IN PROGRESS** | — |

---

*End of Proposed_solution_updated_v3.md*
*Supersedes: Proposed_solution_updated_v2.md (June 6, 2026)*
*Official thesis title (from signed registration form, June 10, 2026):*
*"Unsupervised Epileptic Seizure Temporal Localization in Scalp EEG using Graph Autoencoder and Change Point Detection"*
*Supervisor: Hà Thị Thanh Hương (Associate Professor)*
*Phase: PHASE A CLOSED — technical lock ~October 1, 2026; writing sprint October 1–15, 2026*
*Primary CPD result (SzCORE): balanced mag60/pen1.0 → event sens 0.750, FP/day 38.0; high-sens mag70/pen0.3 → 0.816, FP/day 48.6; window AUROC ≈ 0.80*
*Threshold baseline (old onset-match protocol, not SzCORE-comparable): P95 → 81.6%, FCP/h 15.9*