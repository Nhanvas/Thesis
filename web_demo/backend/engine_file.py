"""engine_file.py — C5 Step 2 (DESIGN_STEP2.md C2, C3): the "each file on its own" engine of SzScan.

The label-free per-recording arm chosen by chat F2-03 (results/m2l/l2/SELECTION.md: B-MCD-F) with its minimum
recording length (results/m2l/l3short/minlen.json), run with the demo checkpoint (GAE v2, seed 42). Every scientific
step is imported read only from src/m2l_core.py (owner F2-03) or from pipeline_demo (the app's own wiring of the
record code); this module only connects them per file:

  z-score statistics    m2l_core.stats_of(sample, S, c_ch) on the file's every-10th, 3-s-padded windows
                        (stored by Phase A as {stem}.fsamp.npy = m2l_core.sampled, line for line)
  node features         pipeline_demo.file_features (c1b_build_trainset.graph_and_bp / f7)
  latent                pipeline_demo.run_gae (checkpoint verified by sha256)
  per-channel distance  m2l_core.distances(Z, cov) (reweighted MCD, support 0.75)
  score, budget, events m2l_core.onefile_ctx / series / detect; q = p3_levers.q_of(smm, k); the localizer of
                        freeze.json ("cpd"), as the session engine
  minimum length        fewer than min_n windows (30 min) or 17 valid windows -> no event (m2l_run's L3 guard)

k, the arm and the minimum length are read from the committed files, never typed. Gate G2 compares this engine's
events with F2-03's committed L3 rows (seed 42) once they exist.
"""
from __future__ import annotations

import json

import numpy as np

import pipeline_demo as pd

REPO = pd.REPO_ROOT
SELECTION_PATH = REPO / "results" / "m2l" / "l2" / "selection.json"
MINLEN_PATH = REPO / "results" / "m2l" / "l3short" / "minlen.json"
TAG = pd.MODEL_TAG                       # clean_seed42
_M = None


def _m2l():
    global _M
    if _M is None:
        import m2l_core as M             # heavy import (eur_abl, torch); only inside the worker process
        _M = M
    return _M


def settings() -> dict:
    sel = json.loads(SELECTION_PATH.read_text())
    ml = json.loads(MINLEN_PATH.read_text())
    if sel.get("arm") != "B-MCD-F" or ml.get("arm") != sel.get("arm"):
        raise RuntimeError(f"unexpected per-recording selection {sel.get('arm')!r} / minimum length {ml.get('arm')!r}; "
                           "the file engine must be re-checked against the new selection before use")
    return dict(arm=sel["arm"], S=sel["S"], cov=sel["cov"], floor=sel["floor"], k=float(sel["k"]),
                min_minutes=int(ml["minutes"]), min_n=int(ml["minutes"] * 60 // pd.WIN_S), min_valid=17)


def describe() -> str:
    s = settings()
    return (f"each file: per-recording arm {s['arm']} (label-free), GAE v2 seed 42, k {s['k']:.4f}, "
            f"minimum {s['min_minutes']} min")


def run_file(filtered: np.ndarray, flag: np.ndarray, fsamp: np.ndarray) -> dict:
    """One file -> score [n], per-channel distance [n, 18] (NaN at signal loss), events [(onset_s, offset_s)],
    q, top and `short` (True: below the minimum length, no event)."""
    M = _m2l()
    s = settings()
    flag = np.asarray(flag, bool)
    n = len(flag)
    ok = ~flag
    nvalid = int(ok.sum())
    floor, cap = M.FLOORS[s["floor"]]
    if n < s["min_n"] or nvalid < max(s["min_valid"], 17) or fsamp.shape[1] == 0:
        return dict(score=np.zeros(n), dist=np.full((n, pd.N_CH), np.nan), events=[], q=float("nan"), top=0.0,
                    short=True)
    mu, sd = M.stats_of(np.asarray(fsamp, np.float64), s["S"], M.c_table())
    adj, bp5, f7 = pd.file_features(filtered, flag, mu, sd)
    Z = pd.run_gae(adj, bp5, f7)
    D = M.distances(Z, s["cov"])
    ctx = M.onefile_ctx(n, ok, {TAG: D})
    x, smm = M.series(ctx, TAG)
    q = M.P3L.q_of(np.asarray(smm), s["k"])
    top, stages, _ = M.detect(M.onefile_ctx(n, ok), np.asarray(x), q, floor, cap)
    ev = stages[pd.FREEZE["localizer"]].get(0, [])
    dist = np.full((n, pd.N_CH), np.nan)
    dist[ok] = D
    score = np.nan_to_num(np.asarray(x, float), nan=0.0)
    return dict(score=score, dist=dist, events=[(float(a), float(b)) for a, b in ev], q=float(q), top=float(top),
                short=False)
