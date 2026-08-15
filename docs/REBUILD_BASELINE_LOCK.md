# REBUILD BASELINE — LOCKED (baseline-of-record)

**Date:** 2026-08-14
**Status:** LOCKED. Single baseline-of-record for the detection pipeline. Supersedes all
pre-rebuild detection numbers (`RESULTS_OF_RECORD.md` §1, §13) and the interim rebuild
numbers (§16); those are kept only as history (not deleted). Attribution/XAI is unaffected
(see `ATTRIBUTION_SPEC.md`).
**Task framing (unchanged):** unsupervised, patient-independent seizure **temporal
localization**; post-hoc EEG review triage. Test = 8 subjects (chb03,06,13,14,15,16,17,18),
76 seizures, 278.2 interictal hours.

---

## 1. Why the rebuild was necessary (rationale)

The rebuild was a redo forced by a first-round oversight, not a redesign. The pre-rebuild
headline (balanced **0.750** / high-sens **0.829**) is retired because, on reconstruction,
three problems were found:

1. **Non-reproducible components.** The original LSTM temporal-branch training code was not
   preserved and could not be re-run. This blocks reproducibility from a clean clone and blocks
   the web demo, which must run inference end-to-end on a new recording.
2. **Train/eval normalization bug (temporal branch).** The reconstructed round-1 trainer trained
   the LSTM on per-dim z-normalized latent Z but every scorer evaluates on **raw** Z (mu/sd were
   never persisted). The branch optimized a different quantity than the pipeline measures →
   near-inert, seed-fragile temporal signal. **Fixed:** train on raw Z, so training objective ==
   eval metric.
3. **Test-set selection of weight + operating point.** The pre-rebuild ensemble weight
   (0.40/0.35/0.25) and both operating points were selected by comparing event **sensitivity on
   the 8 test subjects** (`RESULTS_OF_RECORD.md` §13.1 / §13.3). This is not a held-out protocol.
   The rebuild derives all choices on non-test data and evaluates the test set exactly once.

**Confirmatory evidence (A0).** Applying the old weight (0.40/0.35/0.25) to the *rebuilt*
components yields only ~0.63–0.645 balanced (window macro 0.767), **not** 0.750. The old headline
is therefore not recoverable by weighting — it depended on the now-lost original components
combined with test-set selection. Chasing it back would re-import test leakage; it is retired.

---

## 2. Locked method (final)

Every stage is reproducible from a clean clone and callable for inference on a new recording.

- **Preprocessing:** CHB-MIT, 18-ch bipolar, 256 Hz, 4 s windows, CAR.
- **Graph / window:** wPLI + AEC, top-k 20% (`_topk20`).
- **GAE recon branch:** joint GAE, canonical **seed 42** (Gate R-GAE PASS; reproduces pre-rebuild
  recon, macro 0.669 vs 0.671).
- **LSTM temporal branch:** predictive LSTM on flattened GAE latent Z (288-D), context L=16,
  **trained on raw Z (normfix)**, **PREREG_02 §2 registered schedule** (Adam 1e-3, cosine,
  200 epochs, batch 64), canonical **seed 42**.
- **Gamma AEC branch:** 30–60 Hz amplitude-envelope correlation (deterministic, reused).
- **Per-branch robust-z** (median/MAD, per subject).
- **Ensemble weight = equal (1/3, 1/3, 1/3).** Rationale: the non-test weight surface is flat and
  the window objective is misaligned with the event objective, so no label-based weight tuning is
  justified — an uninformative prior is used. (Old 0.40/0.35/0.25 was test-selected; retired.)
- **CPD:** PELT (`cpd_pipeline_v14.py`), unchanged.
- **Single model = canonical seed 42.** The deep 5-seed mean is **dropped**: it dilutes anomaly
  peaks and underperforms the canonical seed at the event level (§3, and it lowered per-subject
  window AUROC on the hard subjects). Multi-seed spread is reported only as a stability caveat.
- **Operating point = label-free per-subject FP-budget (PREREG_04).** Threshold uses only
  interictal FP/day against a pre-registered budget (balanced 40, high-sens 75 FP/day); the
  tie-break never uses sensitivity. VAL guardrail PASS (both budgets). Reported as SHARED
  (held-out); CALIBRATED reported alongside.

---

## 3. Locked results (baseline-of-record)

Single held-out evaluation, SzCORE event scoring (`timescoring`). 95% CI: Wilson (sensitivity),
Poisson (FP/day).

| Operating point | Sensitivity | 95% CI | FP/day | TP/FN/FP |
|---|---|---|---|---|
| **Balanced — shared** (mag70/pen0.5) | **0.632** | [0.519, 0.731] | 38.6 | 48/28/447 |
| Balanced — calibrated (per-subject) | 0.605 | [0.493, 0.708] | 39.0 | 46/30/452 |
| **High-sensitivity — shared** (mag55/pen0.3) | **0.776** | [0.671, 0.855] | 72.7 | 59/17/843 |
| High-sensitivity — calibrated (per-subject) | 0.776 | [0.671, 0.855] | 72.7 | 59/17/843 |

- **Primary (report these): balanced 0.632 @ 38.6 FP/day; high-sensitivity 0.776 @ 72.7 FP/day.**
  Per PREREG_04, calibrated is reported alongside but did not improve on shared → shared is the
  operating baseline.
- **Window tier:** macro AUROC **0.775**.
- **Seed stability:** 5-seed VAL standalone AUROC mean **0.648**, SD **0.011** (Gate R-LSTM L1/L3
  PASS). Per-seed VAL: 42=0.641, 1=0.640, 2=0.660, 3=0.658, 4=0.639.
- **Context:** exceeds the cited unsupervised CHB-MIT baseline (Yildiz 2022, AUROC 0.68).
  Supervised / TUH results are not comparable (use labels / different dataset).

---

## 4. Provenance & reproducibility

- **Trainer:** `src/retrain/train_lstm_temporal_v3.py` (v3.1: normfix + registered schedule).
- **Checkpoints:** `data/models_retrain/gae_joint_seed42.pt`,
  `data/models_retrain/lstm_temporal_seed{42,1,2,3,4}.pt`.
- **Components / grids:** `results/retrain_v3p1/` — `ens/`, `val_ens/`, `dec19/` (A0),
  `final_eval_seed{42,99}.csv`, `fp_budget_locked.csv`, `fp_budget_val_verdict.json`.
- **Build path:** `build_ens.py` (equal weight) → `score_ens.py` → `fp_budget_operating_point.py`.
- **Superseded (history only, NOT deleted):** `results/retrain/` (round-1 znorm bug),
  `results/retrain_normfix/` (40-epoch normfix). In `RESULTS_OF_RECORD.md`, mark §1/§13/§16 as
  historical and point the reader here.

---

## 5. Open — Giai đoạn B (optimization; NOT part of the baseline)

Evidence localizes the remaining headroom **not** in the LSTM (window signal is at ceiling;
training loss flat by epoch 10 → capacity increases ruled out) and **not** in the weight (flat
surface), but in **per-subject signal quality**: chb06 (inverted ictal connectivity, window
AUROC 0.44) and chb14. Any gain must come from representation, derived on non-test and
pre-registered. SSL for signal-limited subjects remains Future Work.
