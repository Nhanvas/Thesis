"""
================================================================================
 cpd_pipeline_v14.py  —  LOCKED production CPD algorithm (single source of truth)
================================================================================

WHY v14 EXISTS
--------------
v13 was the CPD production stage, but two ALGORITHM-level improvements emerged
during the rigor phase and were only present in the evaluation scripts:

  1. seed-independent PELT penalty   (variance s^2 from the interictal/background
     distribution, not the bootstrap-padded global signal -> deterministic)
  2. magnitude filter                (prune small-magnitude change points that
     cause over-segmentation; threshold calibrated from background CP magnitudes)

Both are label-free and belong in the detection algorithm itself. The buffer
"don't-care" handling and SzCORE scoring are EVALUATION-ONLY (they use seizure
labels) and deliberately stay OUT of this file.

This module is the ONE place the detection algorithm lives. Both the evaluation
(szcore_eval.py) and the future web demo should call `detect_events` so the
demo can never run a different (older) algorithm than the one we report.

LABEL-FREE BY DESIGN
--------------------
A newly monitored patient has no seizure labels, so the demo path computes the
PELT variance and the magnitude threshold from the WHOLE recording. Because
seizures are ~0.2% of windows, whole-signal robust statistics are numerically
indistinguishable from interictal-only statistics; `verify_label_free_equivalence`
checks this on any given timeline. For locking the CHB-MIT results, an optional
`inter_mask` reproduces the evaluation path exactly.

PUBLIC API
----------
    detect_events(score_timeline, pen_mult, min_mag_pct=60, local_win=15,
                  win_sec=4, inter_mask=None, merge_s=90)
        -> list of (onset_s, end_s) seizure-event intervals (merged)

    detect_changepoints(...)   -> raw kept change-point window indices (no merge)

This file performs NO scoring and needs NO labels to run.
================================================================================
"""

import numpy as np
import pandas as pd
import ruptures as rpt

WIN_SEC_DEFAULT = 4
SMOOTH_WIN = 15          # 1-min centered moving average (matches v13)
PELT_MIN_SIZE = 3
PELT_JUMP = 5


# ----------------------------------------------------------------------------
def _smooth(score_timeline):
    return pd.Series(score_timeline).rolling(
        window=SMOOTH_WIN, min_periods=1, center=True).mean().values


def _robust_variance(signal, mask=None):
    """MAD-based variance. mask selects the background sample (interictal if known,
    else the whole signal -- equivalent at ~0.2% seizure prevalence)."""
    ref = signal[mask] if (mask is not None and np.any(mask)) else signal
    med = np.median(ref)
    mad = np.median(np.abs(ref - med)) + 1e-9
    s2 = (1.4826 * mad) ** 2
    return s2 if s2 > 1e-10 else 1.0


def _cp_magnitude(signal, c, L):
    a0, a1, b0, b1 = max(0, c - L), c, c, min(len(signal), c + L)
    if a1 <= a0 or b1 <= b0:
        return 0.0
    return abs(float(signal[b0:b1].mean()) - float(signal[a0:a1].mean()))


def detect_changepoints(score_timeline, pen_mult, min_mag_pct=60, local_win=15,
                        inter_mask=None):
    """Label-free change-point detection: seed-independent PELT + magnitude filter.
    Returns the kept change-point window indices."""
    smoothed = _smooth(np.asarray(score_timeline, dtype=float))
    n = len(smoothed)
    if n < 10:
        return [], smoothed
    s2 = _robust_variance(smoothed, inter_mask)
    beta = pen_mult * s2 * np.log(n)
    algo = rpt.Pelt(model="l2", min_size=PELT_MIN_SIZE, jump=PELT_JUMP).fit(
        smoothed.reshape(-1, 1))
    cps = [c for c in algo.predict(pen=beta) if 0 < c < n]

    if min_mag_pct and min_mag_pct > 0 and cps:
        mags = {c: _cp_magnitude(smoothed, c, local_win) for c in cps}
        # threshold from background CP magnitudes (interictal if known, else all)
        if inter_mask is not None and np.any(inter_mask):
            bg = [m for c, m in mags.items() if inter_mask[c]]
        else:
            bg = list(mags.values())
        thr = float(np.percentile(bg, min_mag_pct)) if bg else 0.0
        cps = [c for c in cps if mags[c] >= thr]
    return cps, smoothed


def detect_events(score_timeline, pen_mult, min_mag_pct=60, local_win=15,
                  win_sec=WIN_SEC_DEFAULT, inter_mask=None, merge_s=90):
    """Full detection -> merged seizure-event intervals (onset_s, end_s).
    This is what the web demo calls. Label-free unless inter_mask is supplied."""
    cps, _ = detect_changepoints(score_timeline, pen_mult, min_mag_pct,
                                 local_win, inter_mask)
    times = sorted(c * win_sec for c in cps)
    events = []
    for t in times:
        if events and t - events[-1][1] <= merge_s:
            events[-1] = (events[-1][0], t + win_sec)
        else:
            events.append((t, t + win_sec))
    return events


# ----------------------------------------------------------------------------
def verify_label_free_equivalence(score_timeline, inter_mask, pen_mult,
                                  min_mag_pct=60, local_win=15):
    """Confirms the demo path (whole-signal stats) matches the eval path
    (interictal stats) on a given timeline. Returns a small report dict."""
    cps_lf, _ = detect_changepoints(score_timeline, pen_mult, min_mag_pct,
                                    local_win, inter_mask=None)
    cps_la, _ = detect_changepoints(score_timeline, pen_mult, min_mag_pct,
                                    local_win, inter_mask=inter_mask)
    set_lf, set_la = set(cps_lf), set(cps_la)
    inter = len(set_lf & set_la)
    union = len(set_lf | set_la) or 1
    return dict(n_label_free=len(cps_lf), n_label_aware=len(cps_la),
                jaccard=round(inter / union, 4),
                identical=(set_lf == set_la))


if __name__ == "__main__":
    # self-test at REALISTIC seizure prevalence (~0.2%, as in CHB-MIT)
    rng = np.random.default_rng(0)
    n = 50000
    sig = rng.normal(0, 1, n)
    inter = np.ones(n, bool)
    for start in (8000, 18000, 27000, 36000, 44000):   # 5 events x 20 windows = 0.2%
        sig[start:start + 20] += 5
        inter[start:start + 20] = False

    ev = detect_events(sig, pen_mult=1.0, min_mag_pct=60, inter_mask=inter)
    print(f"detected {len(ev)} merged events (label-aware lock path)")
    rep = verify_label_free_equivalence(sig, inter, pen_mult=1.0, min_mag_pct=60)
    print("label-free (demo) vs label-aware (lock):", rep)
    # At realistic prevalence the two paths should agree closely.
    print(f"\nFor LOCKING CHB-MIT: use inter_mask -> exact match to szcore_eval.")
    print(f"For the DEMO (no labels): label-free path, jaccard={rep['jaccard']} "
          f"on this synthetic background.")
    assert rep["jaccard"] > 0.85, "label-free path diverges too much"
    print("OK: paths agree at realistic prevalence.")