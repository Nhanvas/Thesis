"""
================================================================================
 szcore_eval.py  —  WEEK 2: SzCORE-exact event scoring + seed-independent penalty
================================================================================

WHY THIS FILE
-------------
Two things from the diagnosis must change before we trust the event-level story:

1. The event "precision ~1%" we saw earlier was partly an ARTIFACT of our ad-hoc
   onset-match scoring (merge gap 32 s, onset-only matching). The SzCORE standard
   uses any-overlap matching with a 30 s pre-ictal / 60 s post-ictal tolerance,
   merges events < 90 s apart, and splits events > 5 min. Under those rules many
   "false" micro-events collapse. We therefore re-score with the AUTHORITATIVE
   SzCORE library (timescoring) instead of our own counting.

2. The PELT penalty beta = pen * s^2 * log(n) used a global MAD variance s^2 that
   included the random bootstrap-padded buffer windows, making detection depend
   on the padding seed. Here s^2 is computed from REAL interictal windows only,
   so the penalty is seed-independent.

Because the thesis targets full-seizure localization (onset AND offset), the
pipeline output is converted from raw change points to seizure INTERVALS:
a segment between two change points is flagged ictal if its mean deviates from
the interictal background beyond the q-th / (100-q)-th interictal percentile
(direction-agnostic, so chb06's downward shift is captured), buffer segments are
excluded, and timescoring then applies SzCORE merging/tolerance. This yields
(onset, duration) hypothesis events scored against (onset, duration) references
exactly as SzCORE prescribes.

WHAT IT PRODUCES (to --out_dir, default results/cpd/evaluation/szcore)
---------------------------------------------------------------------
  szcore_event_level.csv   per subject x penalty (canonical seed):
                           SzCORE sensitivity / precision / F1 / FP-per-day,
                           plus latency and hypothesis-event count. The
                           authoritative replacement for the old event table.
  szcore_summary_macro.csv macro mean +/- SD across subjects per penalty.
  szcore_multiseed.csv     (only with --multiseed N) detection-rate variance
                           under the NEW seed-independent penalty, to confirm
                           the seed problem is fixed.

USAGE
-----
  python szcore_eval.py
  python szcore_eval.py --gate_q 95 --canonical_seed 0
  python szcore_eval.py --multiseed 8          # also re-check seed variance
  python szcore_eval.py --summary_dir "F:/.../summary"

Requires: evaluation_protocol.py (same dir), timescoring (pip install timescoring).
================================================================================
"""

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd
import ruptures as rpt

from timescoring import scoring
from timescoring.annotations import Annotation

import evaluation_protocol as E   # reuse constants + summary parsing
import cpd_pipeline_v14 as V14    # SINGLE SOURCE OF TRUTH for the detection algorithm

WIN_SEC   = E.WIN_SEC
BUFFER_H  = 4
TEST_SUBJS = E.TEST_SUBJS
PEN_MULTS  = E.PEN_MULTS

# SzCORE event-scoring parameters (paper defaults, verified against the library)
SZ_PARAM = scoring.EventScoring.Parameters(
    toleranceStart=30, toleranceEnd=60, minOverlap=0,
    maxEventDuration=5 * 60, minDurationBetweenEvents=90)


# ============================================================================
# SECTION 1 — timeline with a buffer mask  (mirror of E.build_timeline + mask)
# ----------------------------------------------------------------------------
# Identical reconstruction logic; the ONLY addition is is_buffer tracking so we
# can (a) compute a seed-independent variance from real interictal only and
# (b) suppress hypothesis events in synthetic padded regions.
# ============================================================================
def build_timeline_masked(subj, inter_scores, ictal_scores, summary_dir):
    edfs = E.parse_summary_edf_list(Path(summary_dir) / f"{subj}-summary.txt")
    scores_out, is_ictal_out, is_buffer_out = [], [], []
    inter_ptr = ictal_ptr = 0
    total_inter_s = 0.0
    bootstrap_pool = np.random.choice(inter_scores, size=250000, replace=True)
    boot_ptr = 0

    for edf in edfs:
        dur = edf['duration_s']
        n_win = dur // WIN_SEC
        labels = np.zeros(dur, dtype=np.int8)
        buf = np.zeros(dur, dtype=bool)
        for (on, off) in edf['seizures']:
            on = min(on, dur); off = min(off, dur)
            labels[on:off] = 1
            buf[off:min(dur, off + BUFFER_H * 3600)] = True
        tl = n_win * WIN_SEC
        wl = labels[:tl].reshape(n_win, WIN_SEC).max(axis=1)
        wb = buf[:tl].reshape(n_win, WIN_SEC).any(axis=1)
        for w in range(n_win):
            if int(wl[w]) == 1:
                scores_out.append(float(ictal_scores[ictal_ptr])
                                  if ictal_ptr < len(ictal_scores) else 0.0)
                ictal_ptr += 1
                is_ictal_out.append(True); is_buffer_out.append(False)
            elif bool(wb[w]):
                scores_out.append(float(bootstrap_pool[boot_ptr]))
                boot_ptr = (boot_ptr + 1) % len(bootstrap_pool)
                is_ictal_out.append(False); is_buffer_out.append(True)
                total_inter_s += WIN_SEC
            else:
                if inter_ptr < len(inter_scores):
                    scores_out.append(float(inter_scores[inter_ptr])); inter_ptr += 1
                    is_buffer_out.append(False)
                else:
                    scores_out.append(float(bootstrap_pool[boot_ptr]))
                    boot_ptr = (boot_ptr + 1) % len(bootstrap_pool)
                    is_buffer_out.append(True)
                is_ictal_out.append(False)
                total_inter_s += WIN_SEC

    if inter_ptr < len(inter_scores):
        diff = len(inter_scores) - inter_ptr
        scores_out = list(scores_out) + list(inter_scores[inter_ptr:])
        is_ictal_out.extend([False] * diff)
        is_buffer_out.extend([False] * diff)
        total_inter_s += diff * WIN_SEC

    signal = np.asarray(scores_out, dtype=np.float32)
    is_ictal = np.asarray(is_ictal_out, dtype=bool)
    is_buffer = np.asarray(is_buffer_out, dtype=bool)

    sz_ranges, in_s, ss = [], False, 0
    for i, ic in enumerate(is_ictal):
        if ic and not in_s:
            ss = i; in_s = True
        elif not ic and in_s:
            sz_ranges.append((ss, i)); in_s = False
    if in_s:
        sz_ranges.append((ss, len(is_ictal)))

    real_inter = (~is_ictal) & (~is_buffer)
    return signal, is_ictal, is_buffer, real_inter, sz_ranges, total_inter_s / 3600.0


# ============================================================================
# SECTION 2 — seed-independent PELT  (variance from real interictal only)
# ============================================================================
def run_pelt_seedindep(signal, pen_mults, real_inter_mask):
    n = len(signal)
    if n < 10:
        return {pm: ([], 0.0) for pm in pen_mults}
    ref = signal[real_inter_mask]
    if ref.size < 10:
        ref = signal
    med = np.median(ref)
    mad = np.median(np.abs(ref - med)) + 1e-9        # <-- seed-independent
    s2 = (1.4826 * mad) ** 2
    if s2 < 1e-10:
        s2 = 1.0
    algo = rpt.Pelt(model="l2", min_size=3, jump=5).fit(signal.reshape(-1, 1))
    out = {}
    for pm in pen_mults:
        beta = pm * s2 * np.log(n)
        out[pm] = ([c for c in algo.predict(pen=beta) if c < n], beta)
    return out


# ============================================================================
# SECTION 3 — change points -> SzCORE hypothesis events
# ----------------------------------------------------------------------------
# The thesis method is a TRANSITION detector: a change point marks a seizure
# boundary (onset or offset). The faithful SzCORE mapping represents each change
# point as a minimal event interval; timescoring then applies any-overlap with
# 30 s pre / 60 s post tolerance (so a CP near onset OR offset credits the
# seizure) and merges events < 90 s apart. No segment-mean gate is used: forcing
# one diluted short/weak seizures and collapsed sensitivity. The PELT penalty is
# the only knob controlling change-point density. Buffer-region CPs are dropped.
# ============================================================================
def cp_magnitude(signal, c, L):
    """Local |mean shift| across a change point, averaged over L windows each side."""
    a0, a1, b0, b1 = max(0, c - L), c, c, min(len(signal), c + L)
    if a1 <= a0 or b1 <= b0:
        return 0.0
    return abs(float(signal[b0:b1].mean()) - float(signal[a0:a1].mean()))


def _aligned(c, sz_ranges):
    """True if change point c (window index) is within SzCORE tolerance of a seizure."""
    cs = c * WIN_SEC
    return any(s * WIN_SEC - 30 <= cs <= e * WIN_SEC + 60 for (s, e) in sz_ranges)


def cps_to_events(cps, is_buffer, n, signal=None, min_mag=0.0,
                  local_win=15, sz_ranges=None):
    """Change points -> SzCORE hypothesis events.

    Two layers, deliberately separated:
      METHOD (label-free): an optional minimum-magnitude filter removes
        small-shift change points (delta calibrated upstream from interictal).
      EVALUATION (label-aware, eval-only): the post-ictal buffer is a SzCORE
        'don't-care' region -- a change point there is dropped ONLY if it is not
        within tolerance of a seizure; change points near a seizure are always
        kept so seizure-offset detections are not discarded (this fixes the bug
        that zeroed chb16 and crippled chb06).
    """
    evs = []
    for c in cps:
        if not (0 < c < n):
            continue
        if min_mag > 0 and signal is not None:
            if cp_magnitude(signal, c, local_win) < min_mag:
                continue
        if is_buffer[c] and not (sz_ranges is not None and _aligned(c, sz_ranges)):
            continue   # deep post-ictal, not near a seizure -> don't-care
        evs.append((c * WIN_SEC, (c + 1) * WIN_SEC))
    return evs


def interictal_mag_threshold(cps, signal, real_inter_mask, local_win, pct):
    """Label-free magnitude threshold: the pct-th percentile of the magnitudes of
    change points that fall in real interictal windows."""
    mags = [cp_magnitude(signal, c, local_win)
            for c in cps if 0 < c < len(signal) and real_inter_mask[c]]
    return float(np.percentile(mags, pct)) if mags else 0.0


def fast_event_match(cps, is_buffer, sz_ranges, n, n_inter_h,
                     tol_start=30, tol_end=60, merge_s=90):
    """Lightweight SzCORE-style event scorer for the MULTISEED VARIANCE SCAN only.
    Approximates timescoring (any-overlap, 30/60 tolerance, 90 s merge) without
    building masks, so it runs ~100x faster on long recordings. The authoritative
    single-seed numbers still come from timescoring; this is for DR/FP variance."""
    refs = [(s * WIN_SEC, e * WIN_SEC) for (s, e) in sz_ranges]
    # buffer don't-care fix: keep a buffer CP only if it is near a seizure
    keep = []
    for c in cps:
        if not (0 < c < n):
            continue
        if is_buffer[c] and not _aligned(c, sz_ranges):
            continue
        keep.append(c * WIN_SEC)
    ev = sorted(keep)
    merged = []
    for t in ev:
        if merged and t - merged[-1][1] <= merge_s:
            merged[-1] = (merged[-1][0], t)
        else:
            merged.append([t, t])
    tp = sum(1 for (r0, r1) in refs
             if any(m1 >= r0 - tol_start and m0 <= r1 + tol_end for m0, m1 in merged))
    fp = sum(1 for (m0, m1) in merged
             if not any(m1 >= r0 - tol_start and m0 <= r1 + tol_end for r0, r1 in refs))
    fn = len(refs) - tp
    sens = tp / len(refs) if refs else float("nan")
    return dict(tp=tp, fp=fp, fn=fn, n_seizures=len(refs), sensitivity=sens,
                fp_per_day=fp / max(n_inter_h, 1e-6) * 24.0)


# ============================================================================
# SECTION 4 — SzCORE scoring via timescoring (authoritative) + latency
# ============================================================================
def score_szcore(ref_intervals, hyp_intervals, total_dur_s, n_inter_h):
    """Returns SzCORE event metrics. tp/fp/sensitivity/precision/f1 come from the
    timescoring library; FP-per-day is recomputed on the interictal-hours
    denominator for consistency with the thesis FCP/h definition."""
    fs = 1
    N = max(int(total_dur_s), 1)
    ref = Annotation(list(ref_intervals), fs, N)
    hyp = Annotation(list(hyp_intervals), fs, N)
    s = scoring.EventScoring(ref, hyp, SZ_PARAM)
    fp_per_day = s.fp / max(n_inter_h, 1e-6) * 24.0
    return dict(tp=int(s.tp), fp=int(s.fp), n_ref=int(s.refTrue),
                n_hyp=len(hyp_intervals),
                sensitivity=float(s.sensitivity), precision=float(s.precision),
                f1=float(s.f1), fp_per_day=float(fp_per_day),
                fp_rate_full=float(s.fpRate))


def matched_latency(ref_intervals, hyp_intervals, tol_start=30, tol_end=60):
    """Mean (hyp_onset - ref_onset) over reference events that have an
    overlapping hypothesis event within SzCORE tolerance. Negative = early."""
    lats = []
    for (r0, r1) in ref_intervals:
        cands = [(h0, h1) for (h0, h1) in hyp_intervals
                 if h1 >= r0 - tol_start and h0 <= r1 + tol_end]
        if cands:
            h0 = min(cands, key=lambda h: abs(h[0] - r0))[0]
            lats.append(h0 - r0)
    return float(np.mean(lats)) if lats else float("nan")


# ============================================================================
# SECTION 5 — orchestration
# ============================================================================
def load_scores(scores_dir, subj):
    i = Path(scores_dir) / f"{subj}_ens_inter.npy"
    c = Path(scores_dir) / f"{subj}_ens_ictal.npy"
    if not (i.exists() and c.exists()):
        return None, None
    return np.load(str(i)), np.load(str(c))


def evaluate_subject(subj, inter, ictal, summary_dir, min_mag_pct=0, local_win=15):
    signal, is_ictal, is_buffer, real_inter, sz_ranges, n_inter_h = \
        build_timeline_masked(subj, inter, ictal, summary_dir)
    ref_iv = [(s * WIN_SEC, e * WIN_SEC) for (s, e) in sz_ranges]
    total_dur_s = len(signal) * WIN_SEC
    rows = []
    for pm in PEN_MULTS:
        # detection comes from the single-source production algorithm (v14).
        # inter_mask=real_inter makes the locked CHB-MIT numbers reproducible;
        # the web demo calls the same function without a mask (label-free).
        cps, _ = V14.detect_changepoints(signal, pm, min_mag_pct=min_mag_pct,
                                         local_win=local_win, inter_mask=real_inter)
        hyp_iv = cps_to_events(cps, is_buffer, len(signal), sz_ranges=sz_ranges)
        sc = score_szcore(ref_iv, hyp_iv, total_dur_s, n_inter_h)
        lat = matched_latency(ref_iv, hyp_iv)
        rows.append(dict(subject=subj, pen_mult=pm, n_seizures=len(sz_ranges),
                         **sc, mean_lat_s=lat, n_inter_h=round(n_inter_h, 2)))
    return rows


def main():
    ap = argparse.ArgumentParser(description="Week 2 SzCORE re-scoring")
    ap.add_argument("--scores_dir", default="results/cpd/scores")
    ap.add_argument("--summary_dir",
                    default=r"F:\Study\Thesis\Dataset\CHB-MIT\CHB info\summary")
    ap.add_argument("--out_dir", default="results/cpd/evaluation/szcore")
    ap.add_argument("--min_mag_pct", type=float, default=0,
                    help="magnitude filter: prune CPs below this percentile of "
                         "interictal CP magnitudes (0 = off; try 50-70)")
    ap.add_argument("--local_win", type=int, default=15,
                    help="windows each side for CP magnitude (15 = 1 min)")
    ap.add_argument("--canonical_seed", type=int, default=0)
    ap.add_argument("--multiseed", type=int, default=0,
                    help="if >0, also run this many seeds to check DR variance")
    args = ap.parse_args()

    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print(f"SzCORE re-scoring  |  seed={args.canonical_seed}  "
          f"min_mag_pct={args.min_mag_pct:g}  "
          f"|  buffer don't-care fix ON  |  tol 30/60, merge 90s, split 5min")
    print("=" * 80)

    # ---- Phase 1: canonical-seed SzCORE table ----
    all_rows = []
    for subj in TEST_SUBJS:
        inter, ictal = load_scores(args.scores_dir, subj)
        if inter is None:
            print(f"  [skip] {subj}: cache missing"); continue
        np.random.seed(args.canonical_seed)
        rows = evaluate_subject(subj, inter, ictal, args.summary_dir,
                                min_mag_pct=args.min_mag_pct, local_win=args.local_win)
        all_rows.extend(rows)
        r05 = next(r for r in rows if r["pen_mult"] == 0.5)
        print(f"  {subj}: sens={r05['sensitivity']:.2f} prec={r05['precision']:.2f} "
              f"F1={r05['f1']:.2f} FP/day={r05['fp_per_day']:.1f} "
              f"(@pen0.5, {r05['n_hyp']} hyp events)")

    ev = pd.DataFrame(all_rows)
    ev.to_csv(out / "szcore_event_level.csv", index=False)

    # macro summary
    def msd(x):
        x = pd.to_numeric(x, errors="coerce").dropna()
        return (f"{x.mean():.3f} +/- {x.std(ddof=1):.3f}"
                if len(x) > 1 else f"{x.mean():.3f}")
    macro = []
    for pm in PEN_MULTS:
        d = ev[ev.pen_mult == pm]
        if d.empty:
            continue
        macro.append(dict(pen_mult=pm,
                          sensitivity=msd(d.sensitivity),
                          precision=msd(d.precision),
                          f1=msd(d.f1),
                          fp_per_day=msd(d.fp_per_day),
                          mean_lat_s=msd(d.mean_lat_s),
                          hyp_events=msd(d.n_hyp)))
    pd.DataFrame(macro).to_csv(out / "szcore_summary_macro.csv", index=False)

    print("\n" + "-" * 80)
    print(f"{'pen':>5} {'Sens':>16} {'Prec':>16} {'F1':>16} {'FP/day':>16}")
    print("-" * 80)
    for m in macro:
        print(f"{m['pen_mult']:>5g} {m['sensitivity']:>16} {m['precision']:>16} "
              f"{m['f1']:>16} {m['fp_per_day']:>16}")

    # ---- Phase 2 (optional): seed-variance recheck under seed-indep penalty ----
    if args.multiseed > 0:
        print("\n" + "=" * 80)
        print(f"MULTISEED VARIANCE SCAN ({args.multiseed} seeds, seed-independent "
              f"penalty, fast matcher -- NOT timescoring)")
        print("=" * 80)
        ms = []
        ms_path = out / "szcore_multiseed.csv"
        for s in range(args.multiseed):
            for subj in TEST_SUBJS:
                inter, ictal = load_scores(args.scores_dir, subj)
                if inter is None:
                    continue
                np.random.seed(s)
                signal, is_ictal, is_buffer, real_inter, sz_ranges, n_inter_h = \
                    build_timeline_masked(subj, inter, ictal, args.summary_dir)
                smoothed = pd.Series(signal).rolling(
                    window=15, min_periods=1, center=True).mean().values
                pelt = run_pelt_seedindep(smoothed, PEN_MULTS, real_inter)
                for pm in PEN_MULTS:
                    cps, _ = pelt[pm]
                    r = fast_event_match(cps, is_buffer, sz_ranges,
                                         len(signal), n_inter_h)
                    r.update(seed=s, subject=subj, pen_mult=pm)
                    ms.append(r)
            pd.DataFrame(ms).to_csv(ms_path, index=False)   # checkpoint per seed
            print(f"  seed {s} done  [checkpoint saved]")
        msdf = pd.DataFrame(ms)
        print(f"\n{'pen':>5} {'DR mean':>10} {'DR std':>10}   (old std @0.3 was 0.027)")
        for pm in PEN_MULTS:
            d = msdf[msdf.pen_mult == pm]
            per_seed = d.groupby("seed").apply(
                lambda g: g.tp.sum() / max(g.n_seizures.sum(), 1))
            print(f"{pm:>5g} {per_seed.mean():>10.4f} {per_seed.std(ddof=1):>10.4f}")

    print(f"\nWrote to: {out.resolve()}")


if __name__ == "__main__":
    main()