# RESULTS_OF_RECORD — PHASE B / TIER-2 (rlg optimized pipeline)
**Status:** LOCKED (one-shot TEST executed once, as pre-registered in PREREG_TIER2 + Amendment A1).
Reconciles into `docs/RESULTS_OF_RECORD.md`. §0 (recon+temp+gamma) remains the historical baseline;
**rlg (recon+latent+gamma, temporal-free) is the Phase-B optimized pipeline of record.**
**§1–§6 are LOCKED (unchanged). §7 (GAE seed-stability) and §8 (Phase-C negatives) added 2026-08 after the
Phase-C optimization round; they do NOT alter the locked TEST numbers — rlg remains system-of-record.**

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

---

## 7 · GAE seed-stability (added 2026-08 — NEW report-worthy result)
The Phase-B headline rested on a single canonical GAE (seed 42). To quantify sensitivity to GAE
initialization, three additional GAE seeds {1,2,3} were trained with the identical PREREG_01 recipe
(Adam 1e-3, cosine, 200 epochs, batch 32, 12 train subjects' interictal, final-epoch), and the rlg VAL
ensemble was rebuilt per seed. **rlg is highly seed-stable:**

| metric (VAL) | seed 42 | seed 1 | seed 2 | seed 3 | mean ± SD |
|---|---|---|---|---|---|
| window macro AUROC | 0.928 | 0.929 | 0.925 | 0.932 | **0.929 ± 0.002** |
| chb13 recon AUROC (Gate R-GAE G1) | 0.836 | 0.835 | 0.833 | 0.834 | **0.835 ± 0.001** |
| rlg event F1 @ 3.6 FP/day | 0.489 | 0.565 | 0.522 | 0.478 | **0.51 ± 0.034** |

- All four seeds pass Gate R-GAE G1 (chb13 ≥ 0.78) with a tight cluster.
- **The event-level seed-SD (≈0.034 F1) is the noise floor**: any Phase-C challenger must beat rlg by
  MORE than this, on a MAJORITY of seeds, to count as a real improvement (this is now a standing gate).
- Provenance: `data/models_retrain/gae_joint_seed{1,2,3}.pt`;
  `results/phaseB/tier2/ens_val_tf/rlg/ens_seed{1,2,3}_*.npy`. Caveat: seed42 ens built on Kaggle GPU;
  seeds 1/2/3 re-encoded locally on CPU (float noise max|Δ|≈8.6e-5 vs GPU, corr = 1.000000 — faithful).

## 8 · Phase-C optimization round — negatives (added 2026-08)
Phase C sought to Pareto-improve rlg by upgrading the front-end representation. Four levers were
VAL-gated; **none earned the one-shot TEST — rlg stands.** These are reported as negative contributions.

| lever | what it changed | VAL result | verdict |
|---|---|---|---|
| **C4-lite (TE branch)** | add directed-TE anomaly branch (rltg_te = 0.75·rlg + 0.25·zTE) | passed B=40 by +0.004 F1 but **−0.070 F1 @ B=3.6 headline** | rejected as lever; kept as mechanism finding (C0: TE rescues symmetric-inverted subjects — chb06 0.37→0.73, chb22 0.22→0.83 — but benefit is per-subject and net-washes at event) |
| **C1 (median pre-CPD smoother)** | median15 / median9 vs locked MA-15 | median15 −sens; median9 +0.004 @ B=40 but harmed headline; coincided exactly with rltg_te (VAL@B=40 quantization-saturated) | rejected |
| **slope-gate (C-onset)** | reject high-level interictal PLATEAU change-points, keep rising onsets (MIN_SLOPE_PCT=75) | real WINDOW headroom (slope AUROC 0.918 vs level 0.823) but **seed42-specific**: seed42 +0.023 F1 (< seed-SD 0.034); seeds 1/2/3 all FAIL (ΔF1 −0.039…−0.065, sens −0.133 each) | rejected — a false-positive that multi-seed caught before burning one-shot |
| **line-length / Hjorth features** | add per-channel scalar time-domain node features | not built | rejected a priori — same class as existing band-powers; does not address the directed-relationship failure mode; weak to defend |

**Unifying diagnosis:** window/representation gains repeatedly die at the CPD-transfer (PELT detects
sustained level shifts / onset sharpness, not rank separation), and per-subject rescue levers net-wash
(each hard subject fails on a different mechanism; ceiling subjects chb06/chb14 sit in TEST).
Decision-layer, smoothing, and per-channel-feature levers are exhausted **with evidence**.

Phase C-final (RESOLVED — negative, see §9). C4-full (multi-relational GAE) was built, trained, and VAL-gated; it did not beat rlg. Phase-C optimization is closed.

## 9 · Phase-C optimization — CLOSED (added 2026-08)

Phase C is closed. Seven independent levers across the decision, representation, ensemble, and signal-quality layers were evaluated (pre-registered, VAL-gated); none Pareto-improved rlg at the event headline (F1 0.361 @ 3.6 FP/day). rlg is the ceiling and stays system-of-record. This is a convergent, evidence-based negative — not an untested closure.

### 9.1 C4-full — multi-relational GAE (representation layer)

Joint R-GCN-style autoencoder fusing symmetric R1 (wPLI+AEC top-k20) + directed R2 (TE top-k20), NON-SHARED per-relation encoder weights, per-relation decoders (R1 inner-product, R2 asymmetric bilinear), node features identical to rlg. Trained seed42, PREREG_01 recipe, 270,187 interictal windows. No collapse (gate_R2 = ‖grad R2‖/‖grad R1‖ held 1.01–1.03 all 200 epochs — R2 fully used, cf. the S2 residual-gate→0 failure it was designed to detect; converged r2_recon 0.069→0.051). VAL window-macro AUROC (seed42):

front-end	window macro AUROC	vs rlg-full 0.928
rlg-full (recon+latent+gamma) — incumbent	0.928	—
C4-full 3-branch (recon-mr+latent-mr+gamma)	0.909	−0.019 (recon-mr anti-discriminative, 0.439 < 0.5, drags ensemble)
C4-full 2-branch (latent-mr+gamma, drop anti-disc. recon)	0.926	−0.002 = tie within seed-SD (0.002)
rlg-lg diagnostic (rlg latent+gamma, NO TE)	0.9386	matched-ablation control

Verdict: NO-GO (pre-registered). The 2-branch tie (0.926 vs 0.928) is within the measured window seed-SD → multi-seed cannot rescue a noise-floor tie. Diagnostic: rlg-lg (0.9386) > C4-full-lg (0.926) → plain latent+gamma without TE already beats the directed variant at 2-branch → adding the directed relation is net-negative overall despite a real per-subject win.

Mechanism finding (report-worthy positive): directed connectivity genuinely rescues the symmetric-inverted subject at the representation level — chb22 latent-mr 0.736→0.873 (+0.137), ablation-confirmed (zeroing R2 messages: ΔR2(chb22) = +0.126). But it is per-subject and net-washes: ΔR2(chb11) = −0.049 (TE hurts the symmetric-good subject), and the joint 2-relation encoder loses chb10 latent (0.816→0.757, shared-capacity cost, not caused by R2: ΔR2(chb10) = +0.040). This is the same directed-connectivity trade-off C0/C4-lite showed at the decision layer, now confirmed at the representation layer — the strongest evidence in the thesis that TE is complementary-but-insufficient.

Self-correction (integrity note): the Stage-0 input-fidelity band [0.78, 0.88] for chb22 zTE was mis-specified too tightly; measured 0.888 (0.83 ± 0.058), which REPRODUCES C0's direction more strongly, not a failure. Recorded so the 4a flag is not misread as an R2-input bug.

### 9.2 Ensemble reweight / drop-recon (ensemble layer) — DEAD ON RECORD, not re-run

The window-macro observation (rlg-lg 0.9386 > rlg-full 0.928) suggested dropping recon. But this was already measured at the event tier and rejected: §5 — "lg (latent+gamma, drop recon) underperforms rlg at §0 cells (0.579 balanced) → recon retained" (VAL grids in lg/, TEST grids in lg_test/). And PREREG_03 already found the weight surface flat (24 triples within 0.005 of argmax; equal weights adopted as anti-overfit). Window≠event again: drop-recon helps window-macro, hurts the event headline. Not re-run — the record already answers it.

### 9.3 Artifact / signal-quality gate (signal layer)

Pre-condition diagnostic (label-free): rlg's FP-prone interictal windows ARE artifact-associated (best-AUROC 0.78–0.80 across all 3 VAL subjects; null ~0.51; grad_max = max first-difference dominant → sudden jumps/pops that the ±5-SD amplitude preproc rejection lets through). A per-window grad_max score-suppression gate flagged 85% of ictal windows (seizures share high gradient) → unusable. A duration/isolation gate (suppress only isolated ≤2-window spikes, spare sustained seizures) reduced ictal-flag to 3.5% macro and produced a VAL Pareto win — but only at 5 FP/day, driven entirely by one subject (chb11), with the headline 3.6 FP/day unchanged. A 1-subject/1-budget effect at n=3 is a noise signature (cf. slope-gate); rejected without seed-check (per the hard-limit rule: a win must be at the 3.6 headline, ≥2/3 subjects, ≥3/4 seeds). Signal-quality FP-reduction is thus addressed (partly already in preprocessing) and does not lift the headline.

### 9.4 Unifying conclusion

rlg is the performance ceiling for this dataset/split. Every lever — directed connectivity (C4-lite decision, C4-full representation), temporal smoothing (C1), plateau/slope gating, ensemble reweighting (measured), and artifact gating — net-washes at the event headline. The mechanism is understood: (a) window/representation gains die at the CPD-transfer (PELT keys on sustained level shifts, not rank separation); (b) per-subject rescue levers net-wash (each hard subject fails on a different mechanism); (c) the representation-limited ceiling subjects (chb06/chb14, oracle F1 ≤ 0.09) sit in the locked TEST set and cannot be addressed without label leakage. The negative is convergent across four layers and pre-registered throughout.