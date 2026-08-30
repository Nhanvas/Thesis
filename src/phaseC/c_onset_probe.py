"""
c_onset_probe.py — Phase C, (C) go/no-go. CURSOR CPU. NO change to any locked file.

DIAGNOSIS UNDER TEST
  Across latent/TE/median, window/representation gains die at CPD. Level-PELT on the
  MEAN-smoothed anomaly detects a shift in LEVEL; median killed interictal spikes but
  BLUNTED onset -> lost sensitivity at low FP. The want: suppress ISOLATED interictal
  spikes WITHOUT blunting the sustained onset. That is a PERSISTENCE/ACCUMULATION
  problem (a 1-window spike != a multi-window onset). This probe asks ONE decisive
  question on the committed rlg VAL timelines:

    Do TRUE-ONSET windows separate from the HIGH-INTERICTAL windows that generate FPs
    BETTER under a persistence/accumulation statistic (CUSUM, run-length, derivative)
    than under the raw LEVEL that PELT currently uses?

  AUROC(onset vs high-interictal), pooled over VAL, per statistic:
    - level      s(t)                              (what PELT sees now)
    - deriv      s(t) - s(t-1) on smoothed         (rate of change)
    - cusum      g(t)=max(0,g(t-1)+(s-ref-k))      (label-free ref/k from interictal)
    - persist    run-length of consecutive s>ref+k (sustained-elevation count)

  GO   if best(cusum,persist,deriv) - level >= +0.05 AUROC (headroom real) -> build the
       onset-sensitive detector (flag-gated in cpd_pipeline_v14, PELT default byte-exact).
  STOP if <= +0.02 (no headroom; FPs are broad drift, not spikes, OR VAL is blind) ->
       lock rlg, report (C) as no-headroom-on-VAL. Between = borderline, inspect.

Reuses szcore_eval.build_timeline_masked (LOCKED) + V14._smooth for the real path.

USAGE (Cursor)
  python src/phaseC/c_onset_probe.py \
    --ens_dir results/phaseB/tier2/ens_val_tf/rlg --seed 42 \
    --summary_dir "F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary"
Smoke (synthetic timeline, no timescoring/EDF):
  python src/phaseC/c_onset_probe.py --smoke
"""
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
_src = _os.path.dirname(_here)
for _p in (_src, _here, _os.path.join(_src, "retrain"), _os.path.join(_src, "dataprep")):
    if _os.path.isdir(_p) and _p not in _sys.path:
        _sys.path.insert(0, _p)

import argparse
import numpy as np
from sklearn.metrics import roc_auc_score

VAL = ["chb10", "chb11", "chb22"]
TEST = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}
ONSET_WIN = 3        # first 3 windows (12 s) of each seizure = "onset"
HIGH_PCT = 95.0      # interictal windows above this level-percentile = FP-generators


# ---- statistics: level(smoothed)=what PELT sees; alternatives probe the RATE axis
# (onset rises FAST, interictal drift rises SLOW; MA-smoothing already handles isolated
#  spikes -> persistence is NOT the remaining lever, rate-of-rise is). label-free.
def _stats(raw, smoothed, inter_mask):
    ref = float(np.median(smoothed[inter_mask])) if inter_mask.any() else float(np.median(smoothed))
    mad = float(np.median(np.abs(smoothed[inter_mask] - ref))) if inter_mask.any() else \
        float(np.median(np.abs(smoothed - ref)))
    scale = 1.4826 * mad + 1e-9
    k = 0.5 * scale
    level = smoothed                                   # PELT input (already MA-smoothed)
    deriv = np.diff(smoothed, prepend=smoothed[:1])    # 1-step rate of rise (smoothed)
    # centered slope over +/-W (robust rate of rise)
    W = 5
    slope = np.zeros_like(smoothed)
    for t in range(len(smoothed)):
        a, b = max(0, t - W), min(len(smoothed), t + W + 1)
        slope[t] = (smoothed[b - 1] - smoothed[a]) / max(1, (b - 1 - a))
    # classic one-sided upward CUSUM on the RAW anomaly (accumulation, resets)
    rref = float(np.median(raw[inter_mask])) if inter_mask.any() else float(np.median(raw))
    rmad = float(np.median(np.abs(raw[inter_mask] - rref))) if inter_mask.any() else \
        float(np.median(np.abs(raw - rref)))
    rk = 0.5 * (1.4826 * rmad + 1e-9)
    cusum = np.zeros_like(raw); acc = 0.0
    for t in range(len(raw)):
        acc = max(0.0, acc + (raw[t] - rref - rk)); cusum[t] = acc
    return dict(level=level, deriv=deriv, slope=slope, cusum=cusum)


def _onset_mask(sz_ranges, n, k=ONSET_WIN):
    m = np.zeros(n, dtype=bool)
    for (s, e) in sz_ranges:
        m[s:min(s + k, e if e > s else s + 1)] = True
    return m


def _auroc(stat, pos, neg):
    y = np.r_[np.ones(pos.sum()), np.zeros(neg.sum())]
    sc = np.r_[stat[pos], stat[neg]]
    if pos.sum() == 0 or neg.sum() == 0:
        return float("nan")
    return float(roc_auc_score(y, sc))


def run_subject(subj, signal, is_ictal, real_inter, sz_ranges, smooth_fn):
    n = len(signal)
    raw = np.asarray(signal, dtype=float)
    smoothed = smooth_fn(raw)
    stats = _stats(raw, smoothed, real_inter)
    onset = _onset_mask(sz_ranges, n)
    # hard negatives = high-interictal FP-generators (top-percentile of level among interictal)
    inter_levels = smoothed[real_inter]
    thr = np.percentile(inter_levels, HIGH_PCT) if inter_levels.size else np.inf
    high_inter = real_inter & (smoothed >= thr)
    out = {}
    for name, st in stats.items():
        out[name] = dict(vs_high=_auroc(st, onset, high_inter),
                         vs_all=_auroc(st, onset, real_inter))
    return out, int(onset.sum()), int(high_inter.sum())


def _pool_print(per_subj):
    names = ["level", "deriv", "slope", "cusum"]
    # per-subject consistency check (is the headroom broad or one-subject?)
    print(f"\n{'per-subj':9}{'level':>8}{'slope':>8}{'Δ(slope−level)':>16}")
    for s in per_subj:
        lv = per_subj[s]["level"]["vs_high"]; sl = per_subj[s]["slope"]["vs_high"]
        print(f"{s:9}{lv:8.3f}{sl:8.3f}{sl - lv:+16.3f}")
    print(f"\n{'statistic':9}{'AUROC onset-vs-HIGHinter':>26}{'AUROC onset-vs-ALLinter':>25}")
    base_high = np.nanmean([per_subj[s]["level"]["vs_high"] for s in per_subj])
    macro = {}
    for nm in names:
        vh = np.nanmean([per_subj[s][nm]["vs_high"] for s in per_subj])
        va = np.nanmean([per_subj[s][nm]["vs_all"] for s in per_subj])
        macro[nm] = vh
        tag = "  <-- PELT uses this" if nm == "level" else f"   Δ vs level = {vh - base_high:+.3f}"
        print(f"{nm:9}{vh:26.3f}{va:25.3f}{tag}")
    best_alt = max(macro[n] for n in ("deriv", "slope", "cusum"))
    head = best_alt - macro["level"]
    print(f"\n[HEADROOM] best(deriv,slope,cusum) − level = {head:+.3f}  (onset-vs-HIGHinter, macro VAL)")
    if head >= 0.05:
        print("  -> GO: onset-sensitive detector has headroom. Build it (flag-gated).")
    elif head <= 0.02:
        print("  -> STOP: no headroom on VAL. (C) will not survive CPD; lock rlg, report honestly.")
    else:
        print("  -> BORDERLINE: inspect per-subject before committing.")


def _smoke():
    import pandas as pd
    rng = np.random.default_rng(0); n = 12000
    sig = rng.normal(0, 1, n)
    real_inter = np.ones(n, bool); is_ictal = np.zeros(n, bool)
    # (a) isolated interictal spikes (MA already handles these): 1-window, high
    for c in rng.choice(np.arange(300, n - 300), 50, replace=False):
        sig[c] += 6.0
    # (b) SLOW interictal drift bumps (the real FP source): rise over ~150 win to +2.5
    for c in rng.choice(np.arange(400, n - 400), 6, replace=False):
        ramp = np.linspace(0, 2.5, 150)
        sig[c:c + 150] += np.r_[ramp, ramp[::-1]][:min(150, n - c)][:150] if c + 150 <= n else 0
        real_inter[c:c + 150] = real_inter[c:c + 150]   # still interictal
    # (c) seizure onsets: rise FAST (within ~5 win) to +4, sustained 25 win
    sz = []
    for s0 in (2000, 5000, 9000):
        fast = np.clip(np.linspace(0, 4, 5), 0, 4)
        sig[s0:s0 + 5] += fast; sig[s0 + 5:s0 + 25] += 4.0
        is_ictal[s0:s0 + 25] = True; real_inter[s0:s0 + 25] = False
        real_inter[s0 + 25:min(n, s0 + 25 + 3600)] = False
        sz.append((s0, s0 + 25))
    smooth = lambda x: pd.Series(x).rolling(15, min_periods=1, center=True).mean().values
    per = {}
    per["synthetic"], no, nh = run_subject("synthetic", sig, is_ictal, real_inter, sz, smooth)
    print(f"[SMOKE] onset windows={no}  high-interictal (slow-drift) negatives={nh}")
    _pool_print(per)
    print("[SMOKE] plumbing PASS (direction depends on whether onset rate separates from drift)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ens_dir")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--summary_dir", default="data/summaries")
    ap.add_argument("--subjects", default=None)
    ap.add_argument("--allow_test", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    if a.smoke:
        return _smoke()

    subjs = a.subjects.split(",") if a.subjects else VAL
    leak = [s for s in subjs if s in TEST]
    if leak and not a.allow_test:
        raise SystemExit(f"INTEGRITY ABORT: TEST subject(s) {leak}. This is a VAL probe.")

    import szcore_eval as SE
    import cpd_pipeline_v14 as V14
    from pathlib import Path
    ed = Path(a.ens_dir)
    per = {}
    for subj in subjs:
        ei = np.load(ed / f"ens_seed{a.seed}_{subj}_inter.npy")
        ec = np.load(ed / f"ens_seed{a.seed}_{subj}_ictal.npy")
        signal, is_ictal, is_buffer, real_inter, sz_ranges, _ = \
            SE.build_timeline_masked(subj, ei, ec, a.summary_dir)
        per[subj], no, nh = run_subject(subj, signal, is_ictal, real_inter, sz_ranges,
                                        lambda x: V14._smooth(x, method="ma15"))
        print(f"  {subj}: onset_win={no}  high_inter_neg={nh}  n={len(signal)}")
    _pool_print(per)


if __name__ == "__main__":
    main()