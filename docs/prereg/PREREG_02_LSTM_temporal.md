# PRE-REGISTRATION 02 — Temporal branch (LSTM) redesign (PHA 1, step 2)

**Status:** DRAFT for review while GAE multi-seed trains. No LSTM code until approved.
**Context:** the original temporal branch (the `temporal-zscores` arrays, ensemble weight 0.35) is
**unrecoverable** — no class, no training code, no inference code, no config, in the repo or on Kaggle.
We therefore do NOT attempt to clone it. We **redefine the temporal branch from principles**, pre-register
the design here, tune hyper-parameters on VAL subjects only, and evaluate the full ensemble on the 8 test
subjects exactly once. This is the honest response to a lost black box: a clean, reproducible replacement.

---

## 0. Non-negotiables (same discipline as PREREG 01)

- Trained on **interictal windows of the 12 TRAIN subjects only**; hyper-parameters chosen on the **3 VAL
  subjects** (chb10, chb11, chb22); the **8 TEST subjects are never seen** until the single final evaluation.
- The old `ztemp` arrays are used **only as convergent corroboration**, never as a training target and never
  as a selection criterion — otherwise we would re-import the black box we are trying to eliminate.
- One pre-registered design → trained → reported as-is (multi-seed mean±SD). No design re-spins to chase a
  number on test.

---

## 1. Why a new design is legitimate (and better)

The old branch had two documented defects we do NOT want to reproduce:
- a **15-window warm-up fill** baked into every component array (per-array, confirmed), which contaminates
  the window-tier temporal AUROC (harmless at event tier — proven ΔTP=0, but still a defect);
- **zero reproducibility** — it cannot be run on a new recording, which blocks external validation and any
  clinical use.

A principled, reproducible temporal branch fixes both and is the defensible choice for a Q3 paper and a
clinical PoC.

---

## 2. Design (pre-registered, primary)

**Paradigm — predictive LSTM on the graph latent sequence.** The GAE gives, per window `t`, a latent
`Z_t ∈ R^{18×16}`. Pool over the 18 nodes (mean) → a 16-D window embedding `e_t`. A causal LSTM predicts the
current embedding from its recent history; the **temporal anomaly is the prediction error**:

```
input sequence : e_{t-L+1}, ..., e_{t-1}      (L-1 = 15 past windows)
prediction     : ê_t = LSTM(e_{t-L+1..t-1})
raw_temp[t]     = || e_t - ê_t ||²            (mean-squared prediction error)
```

Rationale: (i) reuses the graph representation → coherent with the pipeline; (ii) captures the temporal
dynamics the per-window GAE cannot see; (iii) an abrupt, hard-to-predict graph-state shift is a clean
operational definition of an ictal transition; (iv) it is **independent of the per-window reconstruction
magnitude**, matching the low `corr(ztemp, zrecon)` (0.005–0.225) we measured — i.e. it should stay
complementary, as the ablation requires.

**Sequence length `L = 16`** (context = 15 past + current). Evidence-based: the old branch's warm-up was
exactly 15 windows ⇒ context 16. Also a sensible ~16 s temporal receptive field. Validatable on VAL.

**Sequence contiguity (R2 — hard requirement, must be verified before coding).** A predictive LSTM is only
valid over **temporally contiguous** windows. A subject's interictal windows span multiple EDF files with
time gaps; feeding the concatenated interictal array as one sequence (what the old branch apparently did →
a single warm-up block) predicts *across* gaps and is wrong. The new branch MUST:
  - reconstruct the chronological window→(EDF, time) mapping using `evaluation_protocol.parse_summary_edf_list`
    / `edf_index.EdfIndex` (the exact convention behind every locked result — no new parser);
  - form sequences **only within contiguous runs** (per EDF, and split at seizure/interictal boundaries);
  - mask the first `L-1` windows of **each contiguous run** (excluded from z-norm statistics), not zero-filled.
  Ictal windows of a seizure are contiguous → they get real predictions (no fill), fixing the old defect.
  **Prerequisite to verify first:** the exact windowing convention (length/step, whether the stored
  `{subj}_{split}_adjs` arrays preserve chronological order) — pinned from `dataprep/preprocessing.py` +
  `build_graphs.py` before any LSTM code. If order/contiguity cannot be reconstructed, the design is revised
  (documented) rather than run on an invalid assumption.

**Architecture defaults (tunable on VAL only):** 1-layer LSTM, hidden 64, linear head 64→16, MSE loss,
Adam lr 1e-3, cosine, 200 epochs, batch (sequence) 64. These mirror the GAE optimiser choices for
consistency; hidden size / layers may be adjusted **only** if a VAL-subject check requires it, and any such
change is logged.

---

## 3. Component output (VERIFIED shared recipe)

`raw_temp` per window → **`robust_z_norm`** (median/MAD over inter+ictal pooled, per subject, per signal;
recipe pinned from notebook cell 14) → `ztemp_{subj}_{split}.npy`. Identical normalisation to `zrecon` and
`zgamma`. This is the only step between the LSTM and the ensemble.

---

## 4. Pre-registered input forensic (corroboration, on Kaggle; NOT a gate, NOT test-tuning)

Before locking, one exploration to increase confidence the chosen input is the right family. Using the
**existing validated GAE checkpoint** (or the adopted retrained one), compute pooled-Z embeddings for the
VAL subjects and check that a predictive LSTM on `e_t` yields a temporal signal that is (a) discriminative on
VAL and (b) reasonably correlated with the old `ztemp` on the test subjects **as a sanity cross-check only**.
If Z-based input fails the VAL discriminative check, the **pre-registered fallback** is the raw band-power
sequence `x_t ∈ R^{18×5}` (pooled/flattened) as LSTM input — decided on VAL, before any test evaluation.

---

## 5. Gate R-LSTM — acceptance (DIFFERENT from GAE: there is no faithful target)

Because the old branch is unrecoverable, we cannot ask "does it match?" We ask "is it a good, stable,
complementary temporal detector?" — judged on **VAL**, then the ensemble is scored once on **TEST**.

- **L0 (input choice, R1):** the pooling of Z — mean-pool (18×16→16) vs flatten (→288) — is decided on the
  **mean VAL standalone AUROC**, before any test contact. Whichever wins on VAL is locked.
- **L1 (discriminative on VAL, R4):** temporal-branch standalone window-AUROC, reported **per VAL subject**
  (3 subjects → noisy) with the **mean ≥ 0.60** as the bar (the old branch's standalone was 0.647 on test;
  we require comparable quality on held-out VAL). No single-subject value is used as the criterion.
- **L2 (complementary on VAL):** adding the temporal branch to a recon+gamma ensemble improves VAL
  event-sensitivity (or VAL macro-AUROC) — i.e. it is not redundant.
- **L3 (stability):** across seeds {42,1,2,3,4}, VAL standalone AUROC SD ≤ 0.05.
- **L4 (no leakage):** assert the LSTM never saw test/ictal; warm-up masking verified (no fill in ictal).

If L1–L4 pass → temporal branch accepted. The **full ensemble weights are then re-derived on VAL/train**
(PREREG 03, patient-independent, never on test — this also repairs the thin +3 TP margin of Decision #19),
and the final pipeline is evaluated **once** on the 8 test subjects. Whatever it gives is the headline.

If L1 fails → try the pre-registered fallback input (§4). If still failing → escalate: the temporal branch
may be dropped to a documented 2-view (recon+gamma) system with honest lower sensitivity (last resort).

---

## 6. Multi-seed & outputs

- Seeds {42,1,2,3,4}; seed 42 canonical (aligned with the GAE canonical seed).
- Outputs (fresh, versioned; nothing overwritten):
  `data/models_retrain/lstm_temporal_seed{S}.pt`,
  `data/processed/components_retrain/ztemp_{subj}_{split}.npy` (seed 42 canonical + per-seed for SD),
  `results/retrain/lstm_gate_report.csv`.

---

## 7. Dependencies & honest unknowns

- **Depends on the adopted GAE** (for the Z embeddings). If Gate R-GAE says "adopt retrained seed-42", the
  LSTM input uses that model's Z; if the GAE is instead kept as-is, the LSTM uses the current checkpoint's Z.
  Either way the LSTM *design* is unchanged — only the numerical Z differs. So this document is safe to
  approve now, in parallel with GAE training.
- The predictive-LSTM choice is a **principled reconstruction, not a recovery** — stated plainly in Methods.
  We claim "a temporal branch of this family," not "the original branch."
- Pooling Z over nodes (mean) discards per-node temporal detail; if VAL says that hurts, flattening
  (18×16→288) is the pre-registered richer alternative (decided on VAL).

---

## 8. Approval gate

Boti confirms: (a) predictive-LSTM-on-Z design + L=16; (b) VAL-based acceptance L1–L4 (no test tuning);
(c) weights re-derived on non-test (PREREG 03 to follow); (d) 2-view fallback as last resort only.
On approval, sequence: input forensic (Kaggle) → LSTM training script (smoke → 5-seed) → Gate R-LSTM →
PREREG 03 (weights) → single end-to-end test evaluation → re-lock.
