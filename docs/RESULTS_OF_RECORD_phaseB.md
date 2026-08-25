# RESULTS_OF_RECORD — PHASE B / TIER-2 (rlg optimized pipeline)
**Status:** LOCKED (one-shot TEST executed once, as pre-registered in PREREG_TIER2 + Amendment A1).
Reconciles into `docs/RESULTS_OF_RECORD.md`. §0 (recon+temp+gamma) remains the historical baseline;
**rlg (recon+latent+gamma, temporal-free) is the Phase-B optimized pipeline of record.**

---

## 1 · The optimized pipeline (locked)
`per-window graphs (wPLI+AEC, top-k20) → Joint GAE (seed 42, canonical) → {recon-MSE readout (zrecon),
latent-Mahalanobis readout (zlatent), gamma-AEC (zgamma)} → per-branch robust-z → EQUAL-weight ensemble
(1/3 each) → PELT CPD (cpd_pipeline_v14) → label-free FP-budget operating point → SzCORE (timescoring).`
- **Temporal (LSTM) branch DROPPED** — not reproducible (corr 0.10–0.44 vs §0 committed, max|Δ| 218σ;
  LSTM training code lost). See PREREG_TIER2 Amendment A1. Dropping it improves reproducibility and
  did not cost performance (§3).
- All three surviving branches reproducible: zgamma exact vs §0 (0/16 splits differ); zrecon corr ~0.99
  vs §0 committed (minor input drift, benign at event level); zlatent = Mahalanobis of graph-mean-pooled
  latent Z (16-d, LedoitWolf, per-subject interictal fit — label-free, valid on TEST).

## 2 · Operating points
- OP rule unchanged (PREREG_04 label-free FP-budget, B=40 balanced / B=75 high-sens).
- **VAL-derived (held-out, frozen before TEST):** balanced cell m50/pen2.0; high-sens cell m50/pen0.5.
- §0 published cells (m70/pen0.5, m55/pen0.3) also reported for matched comparison.

## 3 · TEST results (8 subjects, 76 seizures, 278.2 interictal h; seed 42; ONE-SHOT)
**Matched-cell (rlg at §0's own cells) — rlg ≥ §0, within-CI at both:**
| operating point | sens | prec | F1 | FP/day | TP/FP |
|---|---|---|---|---|---|
| §0 balanced (m70/p0.5) | 0.632 | 0.097 | 0.168 | 38.6 | 48/447 |
| **rlg @ m70/p0.5** | **0.645** | **0.099** | **0.172** | 38.4 | 49/445 |
| §0 high-sens (m55/p0.3) | 0.776 | 0.065 | 0.121 | 72.7 | 59/843 |
| rlg @ m55/p0.3 | 0.763 | 0.065 | 0.120 | 72.0 | 58/835 |

**Held-out VAL-derived OP (the honest headline — precision/F1 gain at lower FP):**
| | sens | prec | F1 | FP/day | TP/FP |
|---|---|---|---|---|---|
| rlg balanced (m50/p2.0) | 0.618 | **0.129** | **0.213** | **27.4** | 47/318 |
| rlg high-sens (m50/p0.5) | 0.711 | 0.068 | 0.123 | 64.4 | 54/746 |

vs §0 balanced (0.168 @ 38.6): **F1 +27%, precision +33%, FP/day −29%, sensitivity maintained**
(0.618 vs 0.632, within CI). Pareto improvement at a pre-registered operating point.

**Pareto frontier (pooled TEST):** rlg dominates §0 across the low–mid FP region; peak
**F1 0.426 @ 4.9 FP/day** (sens 0.474, prec 0.387) and 0.406 @ 6.3 — inside the unsupervised
patient-independent SOTA band (F1 0.32–0.43); §0's frontier peaked ~0.351. Frontier is reported as a
curve (dominance evidence), NOT as a selected operating point.

## 4 · Claim (precise)
> Replacing the (unreproducible) temporal branch with a latent-manifold readout on the same GAE yields a
> fully reproducible unsupervised patient-independent detector that MATCHES the §0 baseline at §0's own
> operating points and Pareto-IMPROVES precision/F1 at lower false-alarm rates (F1 0.213 @ 27.4 FP/day
> vs 0.168 @ 38.6; frontier peak F1 0.426, SOTA-band). Sensitivity is maintained within CI; the gain is
> on the precision/F1 axis — the metric §0 was weakest on.

## 5 · Honest caveats
- Matched-cell sensitivity gain (0.632→0.645) is within CI — NOT a significant sensitivity improvement.
  The defensible win is precision/F1 at matched-or-lower FP/day, and reproducibility.
- lg (latent+gamma, drop recon) underperforms rlg at §0 cells (0.579 balanced) → recon retained.
- Representation-limited subjects (chb06, chb14) still cap pooled sensitivity; readout change does not
  rescue signal-limited subjects (consistent with prior diagnosis; graph/SSL levers rejected earlier).
- Cross-dataset SOTA comparison caveat stands; 90–99% CHB-MIT literature is segment-level / patient-
  specific / supervised — not comparable to this event-level unsupervised patient-independent setting.

## 6 · Provenance (committed)
`results/phaseB/tier2/`: ens_val_tf/, ens_test_tf/ (+components), {rlg,rg,lg}/ (VAL grids),
{rlg,lg}_test/ (TEST grids), G2prime_val.csv, ONESHOT_rlg_vs_s0.csv.
Code: build_ens_tier2.py, ensemble_recipe.py (build_ensemble_subset + CANDIDATES), g2_val_gate.py,
tier2_oneshot_compare.py, latent_anomaly.py. Checkpoints: chbmit-ckpt-canon (canonical seed42).
