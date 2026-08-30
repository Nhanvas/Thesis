# 03 · OPTIMIZATION PLAN v2 — end-to-end pipeline upgrades (ROI-ordered)

**Principle:** every item CHANGES a pipeline component and is RETRAINED/re-run; gate on VAL (macro AUROC +
AUPRC + branch AUROC + event metrics) before the single final test. Keep the locked baseline as reference.
**Diagnostic anchor (from prior chat):** the weak link is REPRESENTATION — chb06/chb14 have oracle-F1 ≤0.09
and per-subject branch inversions under a FIXED top-k20 graph (chb06→GAE-recon, chb14→gamma). Fixed graph
+ shallow encoder + single-band branch cannot adapt per subject. So graph + features + objective are the
levers, not thresholds.

## Pipeline map (current) & per-stage weakness
`features(18ch×5band→node 23-d) → graph(wPLI+AEC top-k20 FIXED) → GAE(2×GCNConv 23→64→16, decode 5-band)
→ predictive LSTM on Z → gamma-AEC branch → robust-z per branch → equal-weight ensemble → PELT CPD → SzCORE`
Weak: FIXED graph (no per-subject adapt), shallow GCN, single-band gamma branch, equal weights, plain global z.

---

## S2 · Learned / adaptive graph structure  ★ HIGHEST ROI — start here
- **Hypothesis:** replacing the fixed top-k20 adjacency with a learned graph fixes chb06/chb14 (and lifts
  macro AUROC), because their fixed connectivity mis-encodes ictal vs interictal.
- **Methods (rank):** (1) **GSL layer** — learnable edge weights/attention or Gumbel-softmax sparse mask on
  top of wPLI+AEC, trained by the existing reconstruction loss (label-free); (2) **self-expressive / IB
  graph** (IRENE/GTS-style); (3) **multi-view graph** — add PLV, coherence, Granger → multi-graph encoder;
  (4) **dynamic per-window graph**.
- **POC first (cheap, gated):** implement (1), retrain on VAL+train, dump VAL window AUROC per subject.
  **Gate:** chb06 & chb14 VAL AUROC > 0.5 (chance), macro VAL AUROC ↑ vs 0.775-equivalent VAL. Fail → try (2).
- **Needs:** GAE training script + adjacency-build code (upload). GPU (Kaggle).

## S1 · Richer node features
- 5 bands → add sub-bands (δ θ α β low-γ high-γ), differential entropy, Hjorth, spectral-edge; +
  graph-derived node features (strength, clustering). Reconstruction target can stay 5-band or expand.
- **Gate:** VAL AUROC/AUPRC ↑. Cheap; compounds with S2.

## S3 · GAE encoder/decoder + objective  ★ high ROI
- **Encoder:** 2-layer GCN → GAT / GraphSAGE / deeper+residual, or spatiotemporal (GraphS4mer).
- **Objective:** joint A+X recon → add **masked-node reconstruction** + **contrastive** (EEG-CGS generative
  +contrastive, the unsupervised graph-anomaly SOTA comparator) and/or **VGAE** for calibrated anomaly.
- **Gate:** VAL AUROC/AUPRC ↑ and ictal-vs-interictal separation ↑; branch = new GAE-recon score.

## S5 · Frequency branch: gamma-AEC → multi-band
- chb14's gamma branch inverted → single band fragile. Use multi-band AEC / learned band weighting.
- **Gate:** this branch's VAL AUROC ↑, chb14 recovers.

## S4 · Temporal branch
- Predictive LSTM on Z → TCN / S4 / small transformer; longer context; multi-step. Target subjects where
  ztemp is weak (chb06 ztemp 0.488). **Gate:** ztemp-branch VAL AUROC ↑.

## S6 · Ensemble combination (still label-free)
- Equal 1/3 → robust/rank-based or VAL-precision-weighted or unsupervised meta-combiner; **add new branches**
  (SSL/contrastive score from S3). **Gate:** ensemble VAL AUROC/AUPRC ↑ vs equal (must not overfit 3 VAL subj —
  prefer rank/robust over learned weights on small VAL).

## S7 · Normalization / artifact pre-processing
- Global robust-z → **rolling/local z on the continuous timeline** (tests whether per-subject inversions are
  nonstationarity, not representation) — needs time-interleaved scores/raw. + signal-quality gate if raw
  interictal available. **Gate:** per-subject AUROC ↑ and/or FP↓ at fixed sens.

## S8 · CPD / operating point (LAST, once)
- Keep `cpd_pipeline_v14` locked. After the model is upgraded, **re-derive the operating point once on VAL**
  (PREREG), one-shot test, report full Pareto + triage + balanced. Do NOT iterate here for gains.

---

## EXECUTION ORDER
1. **S2 POC** (learned graph, gate chb06/14 AUROC>0.5) — the decisive lever.
2. **S1 + S5** (features + multi-band) — cheap, compounding.
3. **S3** (contrastive/masked SSL / VGAE objective) — representation depth.
4. **S4 + S6** (temporal + ensemble) — refine.
5. **S7** (normalization/artifact) — FP reduction.
6. **Final integrate → re-derive OP once → one-shot test → full metric table vs baseline + SOTA.**

## PER-CYCLE PROTOCOL (each item)
1. State hypothesis + VAL gate + which metric(s) it should move. 2. I write the training/eval code (Kaggle).
3. You run; paste VAL metric table only. 4. Gate: beats baseline on VAL? keep : revert (log negative).
5. Integrate; re-measure full VAL metric suite. 6. Never touch test until the final integrated model.

## DEFINITION OF DONE
Integrated upgraded pipeline with **macro window AUROC & AUPRC and all event metrics ≥ baseline**, no metric
lopsided, competitive with same-problem SOTA (cross-dataset caveat stated), reproducible bit-exact, full
Pareto + both operating points reported, ablations documenting each stage's contribution.
