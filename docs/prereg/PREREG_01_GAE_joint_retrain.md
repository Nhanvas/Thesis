# PRE-REGISTRATION 01 — GAE-joint retrain (PHA 1, step 1)

**Status:** DRAFT for supervisor/author review. No training code is written until this is approved.
**Author role:** research director (proposes); Boti is final decision-maker (approves, executes on Kaggle).
**Why this exists:** the joint-GAE *training loop* was never retained (only the trained checkpoint + the
inference/scoring code in `thesis-cpd-final.ipynb`). To make the pipeline reproducible end-to-end and to
enable LOSO + multi-seed, we reconstruct the training loop. This document fixes the design and the
**falsifiable acceptance criteria BEFORE any run**, so we cannot rationalise a bad reconstruction after
seeing numbers.

---

## 0. Scope and non-negotiables

- Retrain **GAE-joint only** in this step. LSTM is a separate pre-registration (PREREG 02).
- **Nothing here is tuned on the 8 test subjects.** Architecture, loss, optimiser, epochs, and the
  train/val split are fixed from recovered artefacts; test subjects are touched only at final scoring.
- The retrained GAE becomes **system-of-record** *iff* it passes Gate R-GAE (§6). If it fails, the code is
  wrong — we debug the code, we do not lower the bar.
- The existing checkpoint `best_model_joint_lambda01.pt` is **kept and archived**, never deleted. It is the
  corroboration target, not something we discard.

---

## 1. Architecture (VERIFIED — not reconstructed)

Recovered from notebook cell 4 and confirmed against the checkpoint `state_dict` keys/shapes:

```
Encoder:  GCNConv(23 -> 64) -> ReLU -> GCNConv(64 -> 16)      # conv*.lin.weight (64,23),(16,64)
Decoder A: Â = clamp(Z Zᵀ, 0, 1)                              # inner product, no sigmoid, clamped linear
Decoder X: MLP 16 -> 32 -> 5   (Linear, ReLU, Linear)         # x_decoder.net.0 (32,16), net.2 (5,32)
Nodes: 18 channels. Latent dim 16. Band features: 5.
```

Checkpoint fingerprint (for load-verification, NOT a training target):
`encoder.conv1.bias.abs().max() ≈ 0.8676`.

---

## 2. Data contract (VERIFIED)

- **Graphs:** per-window `{subj}_{split}_adjs{SUFFIX}.npy` (shape `[n_win, 18, 18]`) and
  `{subj}_{split}_features.npy` (shape `[n_win, 18, 5]`), top-k 20% connectivity (wPLI+AEC).
  `SUFFIX` = the exact top-k suffix used by the notebook — **CONFIRM before coding** (grep the notebook
  header, cells 0–3, for `ADJS_SUFFIX`). Train and inference MUST use the identical graph tensors.
- **Split:** `data/splits/split_main.json`, `seed 42`, permanent. 15 train subjects / 8 test.
  Pre-run assertion: `set(split["test"]) == {chb03,chb06,chb13,chb14,chb15,chb16,chb17,chb18}`.
  If this assertion fails, STOP.
- **Training data:** interictal windows of the **15 train subjects only**. The model never sees any window
  (ictal or interictal) from the 8 test subjects, and never sees any ictal window at all. Unsupervised.

---

## 3. Input construction (VERIFIED — must match inference exactly)

Per window, on device, identical to notebook cells 5/7 (any deviation breaks Gate R):

```
A   = adjs   (raw, [18,18])
Xt  = feats  (raw, [18,5])
An  = A / (A.amax() + 1e-8)                                   # per-window global max over 18x18
Xn  = (Xt - Xt.amin(dim=0)) / (Xt.amax(dim=0) - Xt.amin(dim=0) + 1e-8)   # per-window, per-band min-max over channels
x_node        = concat([An, Xn], dim=-1)                     # [18, 23]
edge_index, edge_attr = dense_to_sparse(A)                   # from RAW A, not An
```

**Note the deliberate asymmetry (replicate, do not "fix"):** node features use `An`/`Xn`; the A-reconstruction
target is **raw A**; the X-reconstruction target is **Xn**. This is what the checkpoint does.

---

## 4. Training procedure

Reconstructed by extending the A-only harness (`archive/scaffolding/train_pipeline.py` +
`defaults.yaml`) to the joint objective. Fixed values below come from `defaults.yaml`; items marked
*(reconstruction choice)* are not documented anywhere and are pinned here to be adjudicated by Gate R.

| Item | Value | Source |
|---|---|---|
| Loss | `MSE(A_raw, Â) + 0.1 · MSE(Xn, X̂)`, both `.mean` over the matrix | joint score in cells 5/7 (λ verified = 0.1) |
| Optimiser | Adam, lr `1e-3` | defaults.yaml |
| Scheduler | Cosine, `T_max = max_epochs` | defaults.yaml |
| Epochs | 200 fixed, **no early stopping** | defaults.yaml + train_pipeline plan |
| Batch size | 32 | defaults.yaml |
| Seed (canonical) | 42 | defaults.yaml / experiment_gae.yaml |
| Train/val split | 80/20 random_split, `torch.Generator().manual_seed(seed)` | train_pipeline.py |
| Checkpoint selected | **final epoch** *(reconstruction choice)* | A-only plan = fixed epochs; `loss_curves_joint.npz` shows val was tracked but selection rule unknown |
| Val use | monitor + save loss curves; NOT used for early stop | train_pipeline.py |
| p95 threshold | **NOT part of the pipeline** — the CPD stage is threshold-free; compute only as a logged diagnostic | — |

**Convergence check (not a gate, a sanity anchor):** compare the retrained train/val loss curve shape and
final magnitude against the recovered `loss_curves_joint.npz`. Large divergence is a debug signal.

---

## 5. Inference / component generation (VERIFIED — reuse cells 5/7/8 verbatim)

After training, for each of the 8 test subjects, both splits:

1. **Scalar recon score** per window = `MSE(A,Â) + 0.1·MSE(Xn,X̂)` → `raw_recon_{subj}_{split}` (cell 7).
2. **Per-node recon** = same, error kept per node `[n_win, 18]` (cell 8). Self-check: node-mean must equal
   the scalar to `< 1e-5`.
3. `zrecon` component = robust-z of the raw recon score (shared normalisation defined in the export module;
   pinned when PREREG for the ensemble/export step is written). **Gate R-GAE below is AUROC-based and does
   NOT depend on the z-normalisation** (AUROC is rank-invariant), so this step does not block acceptance.

---

## 6. Gate R-GAE — pre-registered acceptance criteria (falsifiable)

The retrained GAE is accepted as system-of-record **iff ALL hold**. Per-subject recon AUROC is compared
against the locked reference (from `auroc_verification.csv` / window-tier run):

Locked reference (recon standalone AUROC): chb03 0.659 · chb06 0.300 · chb13 0.836 · chb14 0.662 ·
chb15 0.790 · chb16 0.647 · chb17 0.601 · chb18 0.871 · **macro 0.671**.

- **G1 (sanity):** chb13 recon AUROC ≥ 0.78 on the canonical seed.
- **G2 (macro):** macro recon AUROC across seeds has mean ∈ [0.64, 0.70]; **and** the locked 0.671 lies
  within [mean − 2·SD, mean + 2·SD].
- **G3 (structural stability):** for every test subject except chb06, |AUROC_retrain − AUROC_locked| ≤ 0.10.
  chb06 is exempt (already below chance / inverted) but must remain ≤ 0.45.
- **G4 (self-consistency):** per-node mean reproduces scalar recon to < 1e-5 (cell-8 self-check).

If any of G1–G4 fails on the canonical seed / seed distribution → **the training reconstruction is wrong**;
debug (input construction, loss, split) before proceeding. Do not adopt, do not re-tune to pass.

**On GPU non-determinism:** we do NOT expect bit-exact reproduction of the old checkpoint (documented:
Kaggle GPU is not bit-reproducible). Gate R-GAE is a *distributional* equivalence test, which is the correct
standard for "the training procedure is faithful," not "the RNG matched."

---

## 7. Multi-seed plan (solves rubric mean±SD + Decision-#19 robustness at the training tier)

- Seeds: **{42, 1, 2, 3, 4}** (5 runs). Seed sets `torch.manual_seed`, `np.random.seed`,
  `torch.backends.cudnn.deterministic=True`, and the val `random_split` generator.
- Canonical model for the headline pipeline = **seed 42**.
- The other 4 seeds produce 4 additional recon-component sets → training-tier variance. When combined with
  the LSTM multi-seed (PREREG 02), the full pipeline reports **mean ± SD** over seeds — the meaningful
  variance (training), superseding the earlier eval-bootstrap-only SD, and directly testing whether the
  weight/operating-point choice is robust (the thin +3 TP margin of #19).
- Cost note: 5 × (GAE train ~200 epochs on interictal of 15 subjects). Confirm Kaggle GPU-hours budget
  before launching all 5; a 3-seed minimum {42,1,2} is acceptable if time-constrained.

---

## 8. Outputs & provenance

Written to a fresh, versioned location (old artefacts archived, not overwritten):

```
data/models_retrain/gae_joint_seed{S}.pt            # 5 checkpoints
data/processed/components_retrain/zrecon_{subj}_{split}.npy   # per seed (seed42 canonical)
data/pernode_retrain/{subj}_{split}_pernode.npy
results/retrain/gae_gate_report.csv                 # per-subject + macro recon AUROC, all seeds, PASS/FAIL vs G1–G4
results/retrain/gae_loss_curves_seed{S}.npz
```

Provenance line to add to `PROVENANCE_MAP.md`: "GAE-joint training loop reconstructed (PREREG 01) after the
original training notebook was found unrecoverable; validated against the retained checkpoint via Gate R-GAE."

---

## 9. Known risks / honest unknowns

- **Checkpoint-selection rule** (final vs best-val) is unknown → pinned to final-epoch; Gate R adjudicates.
  If G1–G3 fail narrowly, best-val selection is the first thing to try (documented as a deviation).
- **`SUFFIX` / exact graph version** must be confirmed from the notebook header before coding.
- The A-only scaffolding `EEGGraphDataset` may build node features differently from §3; we will **not** reuse
  its feature construction blindly — §3 (the inference-verified construction) is authoritative for both train
  and inference.
- If the retrained macro recon AUROC lands systematically *above* the band, that is NOT "better" to be
  celebrated — it means the reconstruction diverged from the artefact and must be understood before adopting.

---

## 10. Approval gate

Boti confirms: (a) architecture/data/input/loss as fixed above; (b) seed set for multi-seed;
(c) Gate R-GAE thresholds G1–G4. On approval, next deliverable = the training script (Cursor), smoke-tested
on a 1-subject synthetic/tiny run before the full Kaggle launch.
