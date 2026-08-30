# 04 · MODEL INTERNALS — distilled from graph_construction / feature_extraction / train_gae_joint
(so these 3 code files need NOT be re-uploaded; enough to design/patch S1/S2/S5)

## Node input & loss (from train_gae_joint.py — VERBATIM, this is the contract)
```python
# per interictal window -> one PyG Data
A  = tensor(A_np)                 # [18,18] RAW top-k20 adjacency
Xt = tensor(X_np)                 # [18,5]  raw band powers
An = A / (A.amax()+1e-8)                                  # normalized adjacency ROWS
Xn = (Xt - Xt.amin(0)) / (Xt.amax(0)-Xt.amin(0)+1e-8)    # per-band min-max
ei, ew = dense_to_sparse(A)       # edges = top-k20 sparse (message passing)
x  = cat([An, Xn], dim=1)         # [18,23]  <-- NODE FEATURE = 18 adj-row + 5 band
# targets: A (raw top-k), Xn
```
```python
def batch_loss(model, batch):
    z  = model.encoder(batch.x, batch.edge_index, batch.edge_attr)  # [B*18,16]
    Ah = clamp(bmm(z, z.transpose)) # inner-product A-decoder, clamp[0,1]
    Xh = model.x_decoder(z)         # 16->32->5
    return (mse_A + LAMBDA*mse_X).mean()   # anomaly score = this loss
```
- Encoder = GCNConv(23->64) relu GCNConv(64->16). Decoders: A=inner-product(z), X=MLP(16->32->5).
- **Train:** interictal-only, 12 TRAIN / 3 VAL subj (subject-level), 200 ep, Adam 1e-3 cosine, seeds
  {42,1,2,3,4}, seed42 canonical, save final epoch, NEVER touch ictal/8-TEST. Sanity: chb13 AUROC ~0.836.
- **Data:** `{subj}_interictal_adjs_topk20.npy` + `{subj}_interictal_features.npy`;
  Kaggle `nhn2mm/chbmit-topk20` (adj) + `nhn2mm/chbmit-processed` (feat). suffix `_topk20`.
  CLI: `--adj_dir --feat_dir --suffix --seeds --smoke`. Smoke = 1 subj/2 ep/2000 win.

## Graph construction (graph_construction.py)
- `A = 0.5·wPLI + 0.5·AEC` (broadband) → `apply_topk_threshold(keep_ratio=0.20)` = 30/153 edges, RAW
  weights kept. wPLI = |mean(imag(cross))|/mean(|imag(cross)|); AEC = |corr(hilbert envelopes)|; CAR first.
- **Already built (reuse for S5):** `build_adjacency_multiband` + `MULTIBAND_WEIGHTS`
  = {delta .05, theta .10, alpha .50, beta .25, gamma .10}; data `{subj}_{split}_adjs_multiband_topk20.npy`.
- Intermediate DENSE `_adjs` (pre-threshold) exists but gitignored (32.9 GB) → recompute or reuse An rows.

## Features (feature_extraction.py)
- 5 log band powers (δ.5-4 θ4-8 α8-13 β13-30 γ30-60) per channel via Welch, z-scored per window
  across ch×band → `[N,18,5]`.

## CONCRETE EDIT POINTS
- **S2 learned graph** (top priority): message-passing edges come from FIXED top-k (`dense_to_sparse(A)`).
  Make edges learnable — options: (a) GAT / attention edge-weights over a denser candidate set;
  (b) Gumbel-softmax / self-expressive sparse mask learned from the connectivity (the dense profile is
  already present as `An` node rows, so no separate dense file strictly needed); (c) learnable low-rank
  adjacency. Edit `make_window_data` (feed candidate graph) + `GAEEncoder` (insert GSL layer) + optionally
  the A-recon target. Retrain via `train_gae_joint.py`. Gate: chb06/chb14 VAL AUROC > 0.5, macro ↑.
- **S1 richer features:** extend `feature_extraction.py` (more bands / DE / Hjorth) and/or enrich `An`.
  Note node-feature dim 23 must change consistently with `GCNConv(in_dim=...)`.
- **S5 multi-band:** cheapest first win — retrain on existing `_multiband_topk20` adjacency
  (`--suffix _multiband_topk20`), compare VAL. No new code.
- **S3 objective:** add masked-node recon / contrastive (EEG-CGS-style) / VGAE to `batch_loss`.

## Anomaly-score = reconstruction loss (higher = more seizure-like)
chb06's inversion (zrecon AUROC 0.300) means: for chb06 the GAE reconstructs ICTAL better than interictal
under the fixed graph → the fixed top-k graph mis-encodes chb06. This is exactly what S2 targets.
