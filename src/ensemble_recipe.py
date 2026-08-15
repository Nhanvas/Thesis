"""
ensemble_recipe.py — SINGLE SOURCE OF TRUTH for the ensemble anomaly score.

The ensemble is a weighted sum of the three per-view robust-z-normalised component
scores (recon = GAE reconstruction error, temporal = LSTM prediction error,
gamma = gamma-band AEC). The CPD stage (cpd_pipeline_v14) is scale-adaptive, so no
further renormalisation is applied after the weighted sum: the weighted sum of the
component z-scores IS the ensemble.

WEIGHTS — Decision #26 (RESULTS_OF_RECORD §16), rebuilt pipeline:
  EQUAL weights (1/3, 1/3, 1/3). Derived on NON-TEST (PREREG 03): the VAL macro-AUROC
  surface was flat (24 weight triples within 0.005 of the argmax (0.10,0.35,0.55));
  equal weights were adopted as the anti-overfit, TRAIN-consistent tie-break (repairs
  the fragile margin of the old Decision #19). The tuple below is (0.3334,0.3333,0.3333)
  — the exact strings used to produce the locked §16 numbers; the 0.0001 asymmetry is a
  CLI rounding artifact (sum = 1.0) and is numerically negligible (CPD is scale-adaptive).
  Use (1/3, 1/3, 1/3) if re-deriving from scratch.

  SUPERSEDED: the old Decision #19 weight (0.40, 0.35, 0.25) and the pre-that
  (0.35, 0.30, 0.35) belong to the frozen-component pipeline (ROR §1-§15), which is
  historical only - do not use.

PRODUCTION MODEL - the reported system of record is the DEEP SEED-ENSEMBLE: the ensemble
  score is the mean over 5 training seeds {42,1,2,3,4} (variance reduction; GAE + gamma
  are deterministic, the LSTM was the sole seed-variance source). See build_seed_ensemble.py
  (seed-tag 99). This module builds the per-seed ensemble; seed-averaging happens upstream.

NO persistent ensemble cache is ever created (always build fresh from components).
"""
import os
import numpy as np

# Decision #26 (RESULTS_OF_RECORD §16). Order: (recon/GAE, temporal/LSTM, gamma AEC).
# Equal weights; tuple matches the exact strings used for the locked §16 run.
ENS_WEIGHTS = (0.3334, 0.3333, 0.3333)
COMPONENT_KEYS = ("zrecon", "ztemp", "zgamma")   # on-disk file prefixes


def build_ensemble(zrecon, ztemp, zgamma, weights=ENS_WEIGHTS):
    """Weighted sum of the three per-view z-score arrays -> ensemble anomaly score.
    Arrays are truncated to a common length first (defensive; the three views can
    occasionally differ by one window). No post-hoc renorm (CPD is scale-adaptive)."""
    wr, wt, wg = weights
    n = min(len(zrecon), len(ztemp), len(zgamma))
    return (wr * np.asarray(zrecon[:n], dtype=np.float64)
            + wt * np.asarray(ztemp[:n], dtype=np.float64)
            + wg * np.asarray(zgamma[:n], dtype=np.float64))


def load_components(comp_dir, subj, split):
    """Load (zrecon, ztemp, zgamma) for one subject/split from comp_dir.
    Files expected: {key}_{subj}_{split}.npy. Raises FileNotFoundError if any missing."""
    out = []
    for k in COMPONENT_KEYS:
        p = os.path.join(comp_dir, f"{k}_{subj}_{split}.npy")
        if not os.path.exists(p):
            raise FileNotFoundError(p)
        out.append(np.load(p).astype(np.float64))
    return tuple(out)


def ensemble_for_subject(comp_dir, subj, weights=ENS_WEIGHTS):
    """Convenience: (ens_inter, ens_ictal) built from components for one subject."""
    zi = load_components(comp_dir, subj, "inter")
    zc = load_components(comp_dir, subj, "ictal")
    return build_ensemble(*zi, weights=weights), build_ensemble(*zc, weights=weights)
