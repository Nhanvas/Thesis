# Phase B — negative results (rationale for the report)

All VAL (chb10/11/22), seed 42. Baseline GAE-recon branch macro AUROC = 0.592 (chb10 inverted 0.268).

## S5 multiband GAE — REVERT
Retrained GAE on multiband adjacency (delta/theta/alpha/beta/gamma weighted, top-k20).
VAL macro AUROC 0.581 (< 0.592); AUPRC 0.021 (< 0.050); chb11 0.852→0.709.
Verdict: multiband adjacency does not beat single-band top-k20.

## S2 learned graph (GSL) — REJECTED
- Residual-gated GSL: gate g→0.0000 by epoch 40 → model reduced to baseline (macro 0.5921 ≈ 0.5920).
  (Side-benefit: proved the dense-GCN reimplementation equals the baseline at g=0.)
- Forced learned graph (g=1): recon worse (train 0.028 vs 0.016); chb10 still inverted 0.269; macro 0.579.
Verdict: graph STRUCTURE is not the lever. Recon-loss (interictal-only) gives no signal to learn a
discriminative graph; the chb10 inversion is an objective/nonstationarity effect, not graph capacity.

## S3 compactness (Deep-SVDD retrain) — NEGATIVE
Baseline GAE + compactness term (auto-balanced, warmup-frozen center c). 200 epochs.
Latent readout after retrain: macro AUROC 0.686 (< 0.731 baseline-GAE latent); chb11 0.531.
Compactness term stayed ~0.0005 flat → interictal manifold was already compact; nothing to gain.
Verdict: stop GAE model upgrades; keep the latent readout on the baseline GAE (the WIN).

## Conclusion (report narrative)
Two independent upgrade axes (graph structure, latent-shaping objective) tested and rejected. The lever
was the READOUT: reconstruction-MSE anomaly inverts under ictal hypersynchrony; a latent-manifold
(Mahalanobis) readout on the SAME GAE fixes it (chb10 0.268→0.816, VAL macro 0.592→0.731) and lifts the
ensemble (recon+temp+gamma 0.866 → recon+latent+temp+gamma 0.918 / latent+temp+gamma 0.931).
