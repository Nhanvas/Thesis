"""
ensemble_recipe.py — SINGLE SOURCE OF TRUTH for the ensemble anomaly score.

The ensemble is a weighted sum of the three per-view robust-z-normalised component
scores (recon = GAE reconstruction error, temporal = LSTM prediction error,
gamma = gamma-band AEC). The CPD stage (cpd_pipeline_v14) is scale-adaptive, so no
further renormalisation is applied after the weighted sum: the weighted sum of the
stored component z-scores IS the ensemble that reproduces the locked numbers
(verified — event_ablation full(3-view)=0.750, duration_stratified ALL=0.750/0.829,
both build from components with this exact recipe and the canonical seed).

WHY THIS FILE EXISTS
  The ensemble weight (Decision #19) must live in exactly ONE place. Previously it was
  duplicated inline across scripts, and a stale GPU ens cache (old weight) plus a
  seeding-bug grid caused the reported numbers to drift (RESULTS_OF_RECORD §13).
  Anything needing an ensemble score — evaluation, analysis, and the Phase C demo
  export — imports ENS_WEIGHTS + build_ensemble from here. No script re-defines the
  weight; NO persistent ensemble cache is created (always build fresh from components).
"""
import os
import numpy as np

# Decision #19 (RESULTS_OF_RECORD §13.1). Order: (recon/GAE, temporal/LSTM, gamma AEC).
ENS_WEIGHTS = (0.40, 0.35, 0.25)
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