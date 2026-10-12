# PREREG_TIER2 — AMENDMENT A1: temporal branch dropped; pivot to recon+latent+gamma
**Status:** binding amendment to `PREREG_TIER2_latent_ensemble.md`. Made BEFORE any Tier-2 TEST
performance was examined for the new pipeline — this is a REPRODUCIBILITY decision, not a
performance-driven branch selection. Requires supervisor (cô) awareness before it touches the report.

---

## A1.1 — Triggering finding (provenance audit, this session)
Reproducing the §0 ensemble from the committed GAE checkpoint + gamma file, then diffing the per-branch
robust-z components against §0's committed `data/processed/components/` (8 TEST subjects × 2 splits):

| branch | corr vs §0 committed | max\|Δ\| (robust-z) | verdict |
|---|---|---|---|
| `zgamma` | 1.000 (0/16 splits differ) | ~0 | **reproduces exactly** |
| `zrecon` (GAE) | ~0.99 | 2–5 | reproduces up to minor input drift |
| `ztemp` (LSTM) | **0.10–0.44** | **up to 218σ** | **NOT reproducible** |

The temporal branch as currently regenerable is essentially uncorrelated with §0's committed `ztemp`
and carries 70σ+ outliers. Root cause (project history): the LSTM training code/config was lost; only
§0's frozen output arrays survive, and VAL `ztemp` was never committed → the branch cannot be
regenerated or back-computed. `zgamma` is exact; `zrecon` reproduces up to a small (~0.99) input drift.

## A1.2 — Consequence for the Phase-B window WIN
The E1/E2 window numbers that INCLUDED temporal (`recon+temp+gamma` 0.866, `recon+latent+temp+gamma`
0.918, `latent+temp+gamma` 0.931) were computed with a temporal branch that is now shown to be
non-representative noise. They are therefore **not trustworthy as reported** and are retired from the
Tier-2 decision. Only the **temporal-free** result survives the audit: `recon+latent+gamma` (rlg) VAL
macro AUROC 0.928 / AUPRC 0.329, and its components (recon, latent, gamma) are all reproducible.

## A1.3 — Decision (binding)
1. **Drop the temporal branch from Tier-2.** The optimized Tier-2 pipeline is **`recon + latent + gamma`
   (rlg)** — temporal-free, fully reproducible from `{gae_joint_seed42.pt}` + gamma file + adjacency/
   features. Equal weights (1/3 each). This IMPROVES reproducibility (no lost-LSTM dependency), a
   methodological gain, not merely a workaround.
2. **Headline candidate = rlg** (GAE dual-readout recon+latent, + gamma). Pre-designated on the
   temporal-free E1 evidence (highest AUPRC 0.329), BEFORE any new TEST exposure. `latent+gamma` (lg)
   is a pre-declared lean secondary (disclosure, not TEST-selection).
3. **§0 stays the baseline to beat, unchanged:** balanced 0.632 @ 38.6, high-sens 0.776 @ 72.7. §0 is a
   FROZEN, committed, published artifact computed with its (then-working) temporal branch; we compare
   Tier-2 against those frozen event numbers. We do NOT need to regenerate §0's temporal branch to do so.
4. **Frozen (unchanged from PREREG_TIER2):** OP rule = PREREG_04 FP-budget (B=40 / B=75); CPD =
   cpd_pipeline_v14; scorer = timescoring; VAL gates, TEST one-shot; seed 42.

## A1.4 — New VAL gate (replaces G2; temporal-free, clean)
- **G2′ latent-lift:** rlg VAL event F1 @ B=40 ≥ `rg` (recon+gamma) VAL event F1 @ B=40, same harness,
  same run. Confirms the latent branch adds event-level value on the temporal-free base.
- **STOP:** if rlg does not beat rg on VAL, latent adds nothing at event level → do not spend the
  one-shot; report negative.

## A1.5 — Primary endpoint + falsification (unchanged in spirit, temporal-free)
- **Primary:** TEST pooled event sensitivity + precision/F1 at the frozen balanced cell (Pareto framing:
  sens AND precision/F1 up-left vs §0 at matched FP/day).
- **Success:** rlg Pareto-dominates or matches §0 (point estimate sens > 0.632 at FP/day ≤ ~38.6, with
  precision/F1 not worse).
- **Falsification:** rlg TEST ≤ §0 at matched FP/day → the temporal-free latent pivot did not beat the
  temporal baseline. Reported honestly; then (and only then) reconsider **Path A** = recover/retrain a
  temporal branch (heavy) rather than pivot. No reframing of a negative.

## A1.6 — Provenance note (bounded, disclosed)
rlg's recon+latent branches are computed from the canonical GAE checkpoint on the current Kaggle
adjacency/features, which reproduce §0's committed `zrecon` at corr ~0.99 (minor input drift, benign at
event level). recon+latent are mutually consistent (same GAE state); gamma is exact §0. This ~0.99 is
documented, not assumed away; a sensitivity check (rlg with §0-committed recon vs freshly-computed recon)
may be run if the TEST margin is thin.
