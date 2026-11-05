# Model comparison — verified results and reading (chat D11-M, rev 3, 04/11/2026 12:30)

*Plan: `docs/MODEL_COMPARISON_PLAN.md` rev 2 + §9 rows 03/11 08:00, 03/11 22:30, 04/11 07:50. CHB-MIT, 4-fold
patient-wise CV (`results/v9_x3/folds.json`), 24 cases / 23 subjects (chb01 + chb21 one subject), seed 42, one run
per model. Every number is read from the files in this folder; "post-hoc" marks what was not pre-registered.*

## 0 · Verification

| check | result |
|---|---|
| code | repo `6c5d4d8` (frozen chain); notebook A core `e95d74c4…`, B `8fd1a265…`, MLP notebooks `179b9127…` (each version differs from the others only by added lines: GG tolerance, MLP functions) |
| D0 data identity | PASS in all four notebooks |
| G-mini (GAE fold 1 chb12 = committed 7/32, 7/29) | PASS in all four |
| GG (GAE row = committed CV: k × 4 within 1e-6, tp/fp 48/48, 185 caught flags) | PASS |
| G2 training | CNN and MLP-AE: last-epoch loss < first, every fold; MLP-AE training windows per fold = the GAE fold model's (277,780 / 364,471 / 326,976 / 356,641) |
| completeness | 24 cases × 6 models × 2 points × 2 stages; no case without detections; no NaN AUROC |
| no early stopping | GAE and MLP-AE 200 epochs (last kept), CNN 30, trees 200 iterations, SVM to convergence |
| granularity gap | SzCORE 186 reference events vs 185 per-seizure rows (chb11, chb12), same for every model |
| runtime (measured) | A 7.39 h · B 0.23 h · MLP folds 1–2 2.52 h · folds 3–4 2.71 h (MLP 1.06–1.40 h per fold vs GAE 3.05–3.94 h) |

## 1 · Main table (pre-registered A; per-case means, own label-free point, after CPD)

| family | model | sensitivity | precision | F1 | FP/day | window AUROC |
|---|---|---|---|---|---|---|
| graph autoencoder, label-free | **GAE (thesis)** | 0.735 | 0.128 | 0.203 | 28.4 | 0.802 |
| autoencoder without graph, label-free | MLP autoencoder | 0.711 | 0.189 | **0.273** | **20.2** | 0.890 |
| classical anomaly detection, label-free | Isolation Forest | 0.680 | 0.141 | 0.212 | 24.1 | 0.852 |
| supervised, kernel | Linear SVM | 0.626 | 0.099 | 0.163 | 33.7 | 0.810 |
| supervised, tree ensemble | Gradient-boosted trees | 0.755 | 0.145 | 0.221 | 35.2 | 0.870 |
| supervised, deep | 1-D CNN | 0.777 | 0.143 | 0.218 | 35.1 | 0.843 |

## 2 · Pre-registered tests (B, C, E)

Paired subject bootstrap, model − GAE, own point (23 units, B = 10,000):

| model | ΔF1 [95 % CI] | Δsensitivity [95 % CI] | F1 wins / losses | most influential subject (ΔF1 without it) |
|---|---|---|---|---|
| **MLP autoencoder** | **+0.070 [+0.026, +0.117]** | −0.024 [−0.115, +0.061] | 18 / 6 | chb05 (+0.059) |
| Isolation Forest | +0.008 [−0.030, +0.047] | −0.055 [−0.124, +0.011] | 14 / 10 | chb08 (−0.001) |
| Linear SVM | −0.041 [−0.087, +0.004] | **−0.109 [−0.207, −0.024]** | 10 / 14 | chb01 (−0.051) |
| Gradient-boosted trees | +0.018 [−0.035, +0.065] | +0.020 [−0.086, +0.115] | 12 / 11 | chb01 (+0.007) |
| 1-D CNN | +0.014 [−0.032, +0.056] | +0.042 [−0.045, +0.124] | 15 / 9 | chb05 (+0.025) |

C · sensitivity on each detector curve at the GAE's own 28.4 FP/day: GAE 0.703 · **MLP-AE 0.787** · IF 0.704 ·
SVM 0.618 · trees 0.747 · CNN 0.753 (descriptive, no CI).

MLP-AE vs GAE in counts: **the same 115 seizures caught; 827 vs 1,129 false alarms** (−27 %); budget at the floor in
11 cases for both, at the cap in 0 vs 1 → not a budget effect.

**By the fixed reading rules:** (1) the MLP autoencoder — the GAE without message passing — has a **higher event F1**
than the GAE, by fewer false alarms at the same sensitivity; not carried by one subject. The pre-registered statement
"the graph structure adds detection value" is therefore **not supported**; the measured direction is the opposite.
(2) No other model differs from the GAE in F1. (3) The linear SVM has lower sensitivity.

## 3 · Post-hoc checks (`posthoc_bootstrap.csv`; written after reading §1–2)

| model − GAE | ΔF1 @ fixed 0.005 | Δsens @ 0.005 | ΔFP/day @ 0.005 | Δwindow AUROC |
|---|---|---|---|---|
| MLP autoencoder | +0.064 [−0.012, +0.135] | −0.029 [−0.134, +0.069] | −6.8 [−10.0, −3.6] | +0.088 [+0.061, +0.116] (23/24 cases) |
| Isolation Forest | −0.005 [−0.049, +0.038] | −0.092 [−0.180, −0.009] | −5.4 [−8.0, −3.1] | +0.050 [+0.028, +0.073] |
| Linear SVM | −0.037 [−0.089, +0.013] | −0.108 [−0.211, −0.013] | −3.0 [−7.0, +1.0] | +0.008 [−0.065, +0.061] |
| Gradient-boosted trees | +0.093 [+0.004, +0.195] | +0.022 [−0.095, +0.134] | −4.9 [−10.1, +0.6] | +0.068 [+0.003, +0.121] |
| 1-D CNN | +0.061 [−0.018, +0.158] | +0.045 [−0.042, +0.127] | −3.1 [−7.8, +1.6] | +0.042 [−0.018, +0.088] |

## 4 · Reading

1. **Message passing over the connectivity graph does not help detection here; it costs false alarms.** The only
   difference between the MLP autoencoder and the GAE is that the GAE mixes each channel's features with its graph
   neighbours'. Without that mixing: same seizures, 27 % fewer false alarms, higher F1 (CI excludes 0), better window
   separation in 23 of 24 cases. The connectivity information is **still used by both** (each channel's adjacency
   row is part of the input, and both decoders rebuild the graph); what does not help is propagating along edges.
   *Mechanism (hypothesis, not tested):* the per-channel score is an order statistic over 18 channels (6th / 9th /
   12th largest); neighbour mixing spreads a local high-amplitude event into several channels' latents and pushes
   those order statistics up → more false alarms. A test would compare how many channels exceed a threshold in
   false-alarm windows for both models.
2. **Labels do not buy a clear gain at the system's own point** (trees, CNN: CIs contain 0; SVM lower sensitivity);
   at a fixed budget trees trend higher (post-hoc, CI just above 0).
3. **The GAE is on par with a classical detector** (Isolation Forest, F1 +0.008) and **below an autoencoder without
   the graph**. Its value cannot be argued from detection numbers; only from what the graph shows (R91).
4. **Every model misses the same seizures.** Missed by both the GAE and the other model: 54 (MLP-AE), 62 (IF), 61
   (SVM), 47 (trees), 47 (CNN); median amplitude ratio vs own background 1.27–1.29×, median 28–32 s, against
   2.3–2.6× and 68–72 s for seizures both catch → the shared input (4 s feature windows) and the alarm budget set the
   ceiling, not the model family (now six detectors, including supervised ones).
5. **Window separation does not predict event performance** (Spearman 0.42–0.56 between window AUROC and event F1,
   every model).

## 5 · Honest limits

One seed per model (the GAE's CV is seed 42 only; on the thesis split its seed SD is 0.019 in sensitivity, far
below the 0.070 F1 gap, but the MLP-AE has no seed check); 24 cases / 23 subjects; one configuration per model;
feature-level input; CNN without temporal context; supervised k calibrated on in-sample training cases; post-hoc rows
not pre-registered.

## 6 · Consequences for the defense (author decides; board R93: the thesis system does not change before the defense)

- **Do not claim** that the graph / message passing improves detection, that the GAE is the best model, or that it
  beats simpler models. Contribution item 2 of board §4 must not imply a detection gain from the graph.
- **Honest answer to "why a graph?":** *"In our cross-validation, an autoencoder with the same input but without
  graph propagation found the same seizures with fewer false alarms. So the graph does not improve detection; its
  value is in showing how channel networks change during a seizure."* — this needs the graph insight analyses
  (I1–I3) to be shown, otherwise say it as a limitation and future work.
- **Possible follow-ups (not run):** seeds 1–2 of the MLP-AE (≈ 5 h GPU per seed, two notebooks) to confirm the gap;
  the channel-spread test of §4.1; after the defense, consider the MLP-AE scorer for the next system version (would
  change the title's method → registration-form question, not for now).

Figure: `figures/fig_model_cmp_curves.png` / `.pdf` (detector curves, colour only).
