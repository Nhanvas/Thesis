# PREREG_05 — Channel Attribution vs. a Manual EEG Channel Reference Standard

**Status:** DRAFT — not frozen. No agreement number is computed on held-out subjects until the
supervisor signs off (§6.1 split + §7 thresholds are the gate).
**Thesis:** Unsupervised Epileptic Seizure Temporal Localization in Scalp EEG using GAE + CPD.
**Student:** Nguyen Quoc Trung Nhan (BEBEIU22184). **Supervisor:** Hà Thị Thanh Hương (Assoc. Prof.).
**Test set:** CHB-MIT, 18-ch bipolar, 256 Hz. 8 subjects (chb03,06,13,14,15,16,17,18), **76 seizures**
(03=7,06=10,13=12,14=8,15=20,16=10,17=3,18=6). *(Corrects the "97" in MASTER_HANDOFF_v2 — counted.)*
**Date drafted:** 2026-08-07 · **v2** (onset/dominant schema + hit@k metric) · **Frozen:** ___ · **Signed:** ___

---

## 0. Scope
Channel attribution ONLY. NO SOZ claim (CHB-MIT has none). NO focal-vs-generalized classification.
We build a **manual channel reference standard** (a qualified reader marks the involved channels from
raw EEG, exactly as a clinician does) and test whether the model's **per-node GAE reconstruction-error
attribution** points at those channels.

**Reference standard authority.** DRAFT labels are produced with AI assistance (reading the raw-EEG
renders) to save time. They are NOT the reference until the **supervisor (a qualified EEG reader)
reviews each seizure independently and corrects them**. The frozen, supervisor-approved labels are the
reference standard. This is stated as a limitation: the reference is a trained-reader visual judgment,
not board-certified epileptologist consensus, and CHB-MIT has no channel ground truth.

## 1. Objective & hypotheses
**Primary question.** Does the per-node attribution rank the reader-identified **onset** channel(s)
within its top channels, above chance?
- **H1 (confirmatory):** pooled held-out **hit@3 for onset_ch** exceeds the per-seizure chance rate
  (one-sided test, §7).
- **H0 (falsification):** hit@3 not above chance → attribution is an **unvalidated visual display**;
  the pre-specified candidate menu (§4.2) is examined on DEV only (§6).
Positive, weak, or null results are all reported as-is. A clean null is a valid outcome.

## 2. Manual reference standard — annotation protocol
**2.1 Unit.** The 18 bipolar derivations (CH_NAMES order), selected BY NAME (montage order varies
across CHB-MIT files; mne renames the duplicate T8-P8 → T8-P8-0/-1; we take the first, T8-P8-0).

**2.2 Two fields per seizure** (chb17 showed these are NOT the same and must be separated):
- **onset_ch** — derivation(s) with the EARLIEST clear ictal change (1–2). *Primary target.*
- **dominant_ch** — derivation(s) with the most prominent/sustained discharge (1–2). *Secondary target.*
- **confidence** (high/medium/low), **diffuse** (Y = no channel stands out; excluded from hit metric,
  counted), **notes**.

**2.3 Reading aids (raw-EEG only — no computed features, to keep the reference independent of the
model).** Each seizure is rendered as three raw-EEG panels: baseline reference | **onset-zoom
(±~8s, expanded)** for onset_ch | full-seizure for dominant_ch. The supervisor may additionally open an
interactive viewer (mne) to scroll/zoom for the authoritative onset call. Display-only band-pass
(~1–70 Hz) + 60 Hz notch. We deliberately do NOT use line-length / band-power / spectrogram / any
model-adjacent feature to set labels: doing so would make the reference partly circular with the
per-node signal.

**2.4 Blindness.** Labels are made from raw EEG only; the labeling render shows NO model output. All 76
seizures are labeled before any held-out agreement number is computed. The AI drafter does NOT view the
per-node output of any held-out subject until its labels are supervisor-frozen.

**2.5 Storage & review.** One `labels_{subj}.csv` per subject (filled) is the single source of truth.
A `--review` render highlights onset_ch (blue) + dominant_ch (red) on the raw EEG so the supervisor can
approve/correct each seizure. Supervisor reviews all 8 subjects in one batch; frozen on sign-off.

## 3. Node-to-channel map (frozen)
`{subj}_{ictal,interictal}_pernode.npy` = `[n_windows, 18]`; column i ↔ CH_NAMES[i]. Provenance check
(logged): confirm per-node column order == graph-construction node order == CH_NAMES.

## 4. Attribution signals (pre-specified; no retraining, CPU)
Per seizure, an 18-channel attribution vector is built from that seizure's ictal windows vs interictal.
Ictal-window segmentation replicates evaluation_protocol (WIN_SEC=4; assert Σ per-seizure windows ==
len(ictal array)). chb17 verified: 3 seizures → 74 windows.

**4.1 PRIMARY (the thesis model attribution).** **P0** — per-node recon-error robust-z, signed-elevated:
`z_i = (mean_ictal r_i − median_inter r_i)/(MAD_inter r_i + 1e-9)`, ranked by z descending.

**4.2 Pre-specified candidate menu (examined ONLY if P0 fails; DEV only).** A1 raw recon error
(baseline-subtracted, no MAD scaling — addresses low-MAD inflation); A2 recon ratio; A3 |z|; A4 onset-
window variant (first 3 ictal windows); A5 Δ node-strength (wPLI+AEC topk20); A6 Δ eigencentrality; A7
gamma-AEC node strength (if available). No signal outside this list is admissible without a logged
deviation.

## 5. Agreement metrics (frozen)  — top-k overlap, NOT AUC
Per seizure, the reader gives a small target set (onset_ch, or dominant_ch); the model gives an 18-channel
ranking of P0.
- **M1 — hit@k (PRIMARY):** fraction of seizures where ≥1 target channel is in the model's top-k.
  Report **hit@1, hit@3, hit@5**; primary = **hit@3**. Chance is computed per seizure from the target
  size L: P(hit) = 1 − C(18−L, k)/C(18, k) (e.g., L=1,k=3 → 0.167; L=2,k=3 → 0.314); the pooled expected-
  by-chance rate is reported alongside.
- **M2 — median rank** of the reader's first onset_ch in the model ranking (1 = top).
- **M3 — MRR** of that channel.
Computed **separately for onset_ch and dominant_ch**. Reported per subject and pooled. `diffuse=Y`
seizures excluded (no localized target), count disclosed.
*(AUC is NOT used: with 1–2 positives it only rescales rank, and it wrongly treats every unlabeled
channel as a clean negative even though seizures spread.)*

## 6. Analysis plan, split, selection rule (frozen)
**6.1 Subject split (by subject — patient-independent claim; same-patient seizures not independent).**
*Proposed, adjust before freezing:* **DEV** = chb17 (pilot), chb14, chb18 (17 seizures). **HELD-OUT** =
chb03, chb06, chb13, chb15, chb16 (59 seizures). chb06 stays in held-out (excluding it = cherry-picking).

**6.2 Protocol.** (1) Pilot chb17 (DEV): validated tool + protocol; provisional read done — per-node
tracks **onset** (hit-based read to be recomputed after supervisor freeze). (2) Confirmatory: run P0 hit@3
on onset_ch **once** on HELD-OUT. (3) If P0 fails: compute the menu (§4.2) on **DEV only**. (4) A switched
method is confirmed on HELD-OUT once, labeled "selected on dev," with pre- and post-switch numbers shown.

**6.3 Selection rule.** Default = keep P0. Switch only if an alternative beats P0 on DEV by
**Δhit@3 ≥ 0.15** and is principled. Named in a dated deviation before its held-out number is computed.

**6.4 Out of scope (Future Work).** A quantitative localization number against real channel labels would
need an external labeled dataset (TUSZ, Tang-style coverage/precision); deferred.

## 7. Decision thresholds (PROPOSED — supervisor ratifies before §6.2 runs)
On pooled held-out **onset_ch hit@3** (realistic ceiling: supervised channel-labeled DeepSHAP ≈ 0.59
sensitivity, so a moderate bar):
| Outcome | Interpretation |
|---|---|
| hit@3 not significantly > chance | **Not validated** → examine menu (§6) |
| hit@3 > chance but < 0.60 | **Weak/partial** concordance |
| hit@3 ≥ 0.60 | **Meaningful** concordance |
Supervisor may revise the 0.60 bar and the Δhit@3 = 0.15 switch margin. Fixed before step 6.2.

## 8. Anti-circularity safeguards
Blind labeling; every DOF (P0, menu, metric, thresholds, split) fixed here before looking; method
selection on DEV, held-out touched once; both pre/post-switch reported; reference set from raw-EEG
reading only (no model-adjacent features); AI drafter blind to held-out per-node until freeze;
archive-not-delete; deviations logged with dates.

## 9. Deviation log (append-only)
| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-08-07 | schema primary/secondary → **onset_ch/dominant_ch** | chb17: onset ≠ dominant | (pending) |
| 2026-08-07 | primary metric AUC → **hit@k** | AUC≈rank for 1–2 targets; treats spread channels as clean negatives | (pending) |
| | provenance: per-node column order vs CH_NAMES | | |

*End PREREG_05 v2 (draft). Freeze upon supervisor sign-off of §6.1 + §7.*
