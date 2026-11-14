#!/usr/bin/env python
"""
r2_e7exact.py -- research track, stage RP, path 2: fix B of RP_SERIES (docs/FUTURE_RESEARCH_PLAN.md §12 14/11 18:30 (c),
(d); implementation D27-F). An exact, vectorised implementation of the segmentation that the D2 segmenter of
src/e7_ensemble_cpd.py (d2_grid) asks of ruptures 1.1.10:

    ruptures.Pelt(model="l2", min_size=2, jump=1).fit(X).predict(pen=pen),   X = x.reshape(-1, 1)

ruptures.detection.pelt.Pelt._seg (1.1.10, read 14/11) is a pure-Python recursion: at every end point it copies and sums a
dict per admissible start, so its cost grows ~ quadratically with the file length (6 / 20 / 88 s per file of 900 / 1,800 /
3,606 windows, one seed and one penalty; plan §12 14/11 18:30 (b)).

THE SAME RECURSION (pelt_l2), step by step as _seg:
  * end points b = 2, 3, ..., n - 1, n (`ind` for min_size 2, jump 1); at each b the point b - 2 joins the admissible set
    first; the point 1 never does (partitions[1] does not exist: at b = 3 it is appended last and dropped by `zip`);
  * the value of a new segment is v = cost(t, b) + pen, cost = X[t:b].var(axis=0).sum() * (b - t) (CostL2.error, the
    same numpy expression on the same array); the total of a candidate is sum(partitions[t].values()) + v. Those values
    are numpy float64 scalars after the integer 0 of (0, 0), so Python's sum() takes its generic path (no compensated
    summation) and the sum is a plain left-to-right fold; the total is therefore F(t) + v with F(t) = the total chosen at
    t, stored here as one float (FR). Exactly the same additions in the same order;
  * F(b) = the first minimum over the admissible set in increasing t (Python min over the list = first minimum);
  * t stays admissible iff its total <= F(b) + pen (same comparison);
  * the breakpoints are the ends of the optimal partition of x[0:n], ascending, n included.

VECTORISED, YET EXACT. The totals of all admissible starts are first computed together with costs from prefix sums of the
file-centred signal (cost is shift invariant), which differ from the numpy costs by rounding only, bounded by E (below).
A decision is taken from these approximate totals only when its margin exceeds E; otherwise (and always for the value
F(b) that is stored) the totals involved are recomputed with ruptures' own expression, so FR and every decision are
ruptures' to the bit:
  * minimiser: the starts whose approximate total is within 2E of the smallest are recomputed exactly; F(b) = the first
    minimum of the exact totals among them (no other start can be the minimum);
  * pruning: a start whose approximate total lies within E of F(b) + pen is recomputed exactly and compared exactly.
E = 2 * [4 g (P2 + max|xc| S1) + (log2 n + 8) u P2 + 4 u |T|], u = 2^-53, g = n u / (1 - n u), P2 = sum xc^2, S1 = sum |xc|,
xc = x - mean(x), T = the totals: the bound of a recursive (any-order) summation for the prefix sums, the effect on
s1^2 / m, the rounding of the centring, of ruptures' two-pass variance (pairwise) and of the final additions, times 2.
Gate RS-E7 (src/r2_rse7.py, its own Kaggle notebook) compares the breakpoints with ruptures.Pelt on every file of the
committed path-2 scores (rp2/scores: 8 test patients, chb24, Siena 14), seeds 1-4, the 3 penalties of E7.
check="all" recomputes every total exactly at every step (test mode: proves E never let a decision through wrongly).

d2_grid_exact(E7) returns E7's own d2_grid function (its code object, unchanged) bound to globals in which `rpt` is the
shim below, so every line of d2_grid runs as committed and only the ruptures call is replaced. STATS counts the calls and
the exact recomputations (reported by RP_SERIES and RS-E7).
Tests: src/r2_rse7_synthetic_test.py.
"""
import math
import types

import numpy as np

U = 2.0 ** -53
STATS = dict(calls=0, windows=0, steps=0, decisions=0, exact_costs=0)


def reset_stats():
    for k in STATS:
        STATS[k] = 0


def _bound(n, xc, P2):
    g = n * U / (1.0 - n * U)
    return 2.0 * (4.0 * g * (P2 + float(np.abs(xc).max()) * float(np.abs(xc).sum())) + (math.log2(n) + 8.0) * U * P2)


def pelt_l2(X, pen, check="band"):
    """breakpoints of ruptures.Pelt(model="l2", min_size=2, jump=1).fit(X).predict(pen=pen) for X of shape (n, 1) or (n,)
    (see the module docstring). Returns (bkps, info); info: steps, decisions, exact (costs recomputed exactly), max_adm."""
    S = np.asarray(X)
    if S.ndim == 1:
        S = S.reshape(-1, 1)                    # CostL2.fit
    if S.ndim != 2 or S.shape[1] != 1:
        raise ValueError("pelt_l2: one-dimensional signals only")
    n = int(S.shape[0])
    if n < 4:                                   # d2_grid segments only files of >= 4 windows
        raise ValueError(f"pelt_l2: n = {n} < 4")
    if not np.isfinite(S).all() or not np.isfinite(pen) or not pen > 0:
        raise ValueError("pelt_l2: non-finite signal or penalty")

    def cost(t, b):                             # CostL2.error, the same expression on the same array
        return S[t:b].var(axis=0).sum() * (b - t)

    x = S[:, 0].astype(np.float64)
    xc = x - x.mean()
    P1 = np.empty(n + 1); P1[0] = 0.0; np.cumsum(xc, out=P1[1:])
    P2 = np.empty(n + 1); P2[0] = 0.0; np.cumsum(xc * xc, out=P2[1:])
    E0 = _bound(n, xc, float(P2[n]))
    FR = np.empty(n + 1); FR[0] = 0.0          # sum({(0, 0): 0}.values()) = 0
    last = np.zeros(n + 1, dtype=np.int64)
    adm = np.zeros(0, dtype=np.int64)
    n_dec = n_exact = max_adm = 0
    for b in list(range(2, n)) + [n]:
        if b - 2 != 1:
            adm = np.append(adm, b - 2)
        k = len(adm)
        max_adm = max(max_adm, k)
        n_dec += 2 * k
        m = b - adm
        s1 = P1[b] - P1[adm]
        T = FR[adm] + (((P2[b] - P2[adm]) - s1 * s1 / m) + pen)
        E = E0 + 8.0 * U * float(np.abs(T).max())
        exact = {}

        def tot(i):                             # exact total of candidate i (ruptures' arithmetic)
            if i not in exact:
                t = int(adm[i])
                exact[i] = FR[t] + (cost(t, b) + pen)
            return exact[i]
        if check == "all":
            for i in range(k):
                tot(i)
            cand = np.arange(k)
        else:
            cand = np.flatnonzero(T <= T.min() + 2.0 * E)
        ex = np.array([tot(int(i)) for i in cand])
        j = int(cand[int(np.argmin(ex))])       # first minimum (cand ascending = admissible order)
        fb = exact[j]
        FR[b] = fb
        last[b] = adm[j]
        thr = fb + pen
        keep = T <= thr
        band = np.flatnonzero(np.abs(T - thr) <= E) if check != "all" else np.arange(k)
        for i in band:
            keep[i] = tot(int(i)) <= thr
        n_exact += len(exact)
        adm = adm[keep]
    out, b = [], n
    while b > 0:
        out.append(int(b))
        b = int(last[b])
    return out[::-1], dict(steps=n - 1, decisions=n_dec, exact=n_exact, max_adm=max_adm)


class _ExactPelt:
    """the part of the ruptures.Pelt interface d2_grid uses: Pelt(model="l2", min_size=2, jump=1).fit(X).predict(pen)."""

    def __init__(self, model="l2", custom_cost=None, min_size=2, jump=5, params=None):
        if model != "l2" or custom_cost is not None or min_size != 2 or jump != 1 or params is not None:
            raise ValueError(f"exact Pelt: only model='l2', min_size=2, jump=1 (got {model}, {min_size}, {jump})")

    def fit(self, signal):
        self.signal = signal
        return self

    def predict(self, pen):
        bk, info = pelt_l2(self.signal, pen)
        STATS["calls"] += 1
        STATS["windows"] += int(np.asarray(self.signal).shape[0])
        STATS["steps"] += info["steps"]
        STATS["decisions"] += info["decisions"]
        STATS["exact_costs"] += info["exact"]
        return bk


ExactRpt = types.SimpleNamespace(Pelt=_ExactPelt)


def d2_grid_exact(E7):
    """E7.d2_grid with its code unchanged and `rpt` resolved to ExactRpt; every other global is E7's own (the same module
    objects, so a temporary E1.TOPS set by the caller applies as before)."""
    g = dict(E7.__dict__)
    g["rpt"] = ExactRpt
    f = E7.d2_grid
    return types.FunctionType(f.__code__, g, "d2_grid", f.__defaults__, f.__closure__)
