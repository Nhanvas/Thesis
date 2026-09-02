"""
================================================================================
 diagnose_fp_mechanism.py  (Phase B+ / Step 0 — FP mechanism diagnostic)
================================================================================
WHY THIS FILE EXISTS
---------------------
We know FP/day is high (38.0 balanced / 47.97 high-sens) but we have never
looked at WHAT the ~441 FP events (balanced point) actually are. This script
does not change the algorithm, the threshold, or any lock — it is read-only
introspection on the exact same detection path already used for the locked
numbers (cpd_pipeline_v14.detect_changepoints -> szcore_eval.cps_to_events),
and characterizes every resulting FP event by four candidate mechanisms:

  1. Proximity to an EDF FILE BOUNDARY (recording start/stop, montage change,
     device reconnect) -- a classic source of transient artifact.
  2. Proximity to a SEIZURE EDGE beyond SzCORE tolerance -- "near miss" FPs
     that sit just outside the +/-30s/+60s acceptance window (would indicate
     the tolerance window itself, not the detector, is the limiting factor).
  3. Residual BUFFER-ZONE contamination -- events whose underlying change
     points partially fall in the post-ictal 4h buffer (should be near-zero
     by construction, since cps_to_events already drops deep-buffer CPs
     unless seizure-aligned; this is a sanity check on that mechanism, not a
     new hypothesis).
  4. SESSION / TIME-OF-DAY structure -- e.g. chb17's three recording sessions
     (17a/17b/17c) with baseline drift, or a within-day circadian pattern
     (sleep transition artifacts cluster at particular hours).

HONESTY ABOUT APPROXIMATION
----------------------------
The authoritative TP/FP counts come from the `timescoring` library inside
szcore_eval.score_szcore(). This script independently re-implements the
SzCORE merge (<90s) / split (>5min) / any-overlap-with-tolerance rules to
attach per-EVENT diagnostic features (something timescoring's public API does
not expose per-event). This is an APPROXIMATION of timescoring's internal
event bookkeeping, not a byte-identical reproduction. To guard against silent
drift, the script always prints a self-check: our approximate FP count vs the
authoritative score_szcore() FP count, per subject and pooled. If they
diverge by more than a few percent, treat the per-event breakdown as
indicative only, not exact -- the coarse pattern (which mechanism dominates)
is still informative even if the exact count is off by a handful of events.

WHAT IT PRODUCES (to --out_dir, default results/phaseB/fp_diagnosis)
----------------------------------------------------------------------
  fp_event_diagnostics.csv   one row per FP event, all diagnostic features
  fp_diagnosis_summary.csv   per-subject + pooled enrichment/summary stats
  (stdout)                   self-check table + top-line summary per subject

USAGE
-----
  python diagnose_fp_mechanism.py --summary_dir "F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary"
  python diagnose_fp_mechanism.py --pen 1.0 --mag 60 --boundary_window_s 60
  python diagnose_fp_mechanism.py --pen 0.3 --mag 50   # high-sensitivity point instead

Requires: cpd_pipeline_v14.py, szcore_eval.py, evaluation_protocol.py (same dir),
timescoring, ruptures. Runs entirely on cached scores (CPU, no GPU, no retrain).
================================================================================
"""

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

import cpd_pipeline_v14 as V14
import szcore_eval as SE
import evaluation_protocol as E

WIN_SEC = E.WIN_SEC
TEST_SUBJS = E.TEST_SUBJS
MERGE_GAP_S = 90          # SzCORE minDurationBetweenEvents
SPLIT_MAX_S = 300         # SzCORE maxEventDuration
TOL_START_S = 30
TOL_END_S = 60


# ============================================================================
# SECTION 1 — file-boundary map + start-time parsing (window-index space)
# ----------------------------------------------------------------------------
# Mirrors szcore_eval.build_timeline_masked's file loop EXACTLY (same file
# order via evaluation_protocol.parse_summary_edf_list, same n_win formula),
# but only tracks cumulative window counts + metadata -- no scores needed.
# ============================================================================
def file_window_map(subj, summary_dir):
    path = Path(summary_dir) / f"{subj}-summary.txt"
    edfs = E.parse_summary_edf_list(path)
    text = path.read_text()
    start_times = dict(re.findall(
        r'File Name:\s*(\S+\.edf)\s+File Start Time:\s*(\S+)', text))
    idx = 0
    out = []
    for edf in edfs:
        n_win = edf['duration_s'] // WIN_SEC
        fname = edf['fname']
        m = re.match(r'^(chb\d+[a-c]?)_', fname)
        session = m.group(1) if m else subj
        out.append(dict(fname=fname, start_idx=idx, end_idx=idx + n_win,
                        start_time=start_times.get(fname), session=session))
        idx += n_win
    return out, idx  # idx = total windows covered by real files (excl. any trailing tail)


def hour_of_day_at(window_idx, file_map):
    """Approximate wall-clock hour for a window index, via its containing
    file's start time + offset. Returns None if outside any known file
    (e.g. the trailing leftover-interictal tail appended after all files)."""
    for f in file_map:
        if f['start_idx'] <= window_idx < f['end_idx']:
            st = f['start_time']
            if not st:
                return None
            try:
                h, mi, s = (int(x) for x in st.split(':'))
            except ValueError:
                return None
            offset_s = (window_idx - f['start_idx']) * WIN_SEC
            total_h = (h + (mi * 60 + s + offset_s) / 3600.0) % 24
            return total_h
    return None


def session_at(window_idx, file_map):
    for f in file_map:
        if f['start_idx'] <= window_idx < f['end_idx']:
            return f['session']
    return 'tail'


# ============================================================================
# SECTION 2 — approximate SzCORE merge/split/match (see module docstring)
# ============================================================================
def merge_simple(intervals, gap):
    intervals = sorted(intervals)
    merged = []
    for s, e in intervals:
        if merged and s - merged[-1][1] <= gap:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return merged


def merge_with_members(items, gap):
    """items: list of (start, end, [member_cp_idx, ...]), sorted by start."""
    items = sorted(items, key=lambda x: x[0])
    merged = []
    for s, e, mem in items:
        if merged and s - merged[-1][1] <= gap:
            merged[-1] = [merged[-1][0], max(merged[-1][1], e), merged[-1][2] + mem]
        else:
            merged.append([s, e, list(mem)])
    return [tuple(x) for x in merged]


def split_long(items, max_dur):
    out = []
    for s, e, mem in items:
        dur = e - s
        if dur <= max_dur:
            out.append((s, e, mem))
            continue
        n_chunks = int(np.ceil(dur / max_dur))
        chunk = dur / n_chunks
        for i in range(n_chunks):
            cs, ce = s + i * chunk, s + (i + 1) * chunk
            cmem = [c for c in mem if cs <= c * WIN_SEC < ce]
            out.append((cs, ce, cmem))
    return out


def build_final_hyp_events(cps, is_buffer, signal, sz_ranges):
    """Recover the exact surviving-CP set that szcore_eval.cps_to_events would
    keep (mag filter already applied inside detect_changepoints; this
    reproduces only the buffer-drop condition), then merge (<90s) and split
    (>5min) exactly like SzCORE, carrying underlying CP membership along."""
    survived = [c for c in cps if 0 < c < len(signal)
                and not (is_buffer[c] and not SE._aligned(c, sz_ranges))]
    items = [(c * WIN_SEC, (c + 1) * WIN_SEC, [c]) for c in survived]
    merged = merge_with_members(items, MERGE_GAP_S)
    final = split_long(merged, SPLIT_MAX_S)
    return final, survived


def build_extended_merged_ref(sz_ranges):
    ref_ext = [(max(0, s * WIN_SEC - TOL_START_S), e * WIN_SEC + TOL_END_S)
               for (s, e) in sz_ranges]
    return merge_simple(ref_ext, MERGE_GAP_S)


def classify_events(final_hyp, ref_merged):
    """Any-overlap match against the tolerance-extended, merged reference.
    Returns (tp_events, fp_events) as lists of (s, e, members)."""
    tp, fp = [], []
    for s, e, mem in final_hyp:
        hit = any(e >= rs and s <= re_ for (rs, re_) in ref_merged)
        (tp if hit else fp).append((s, e, mem))
    return tp, fp


# ============================================================================
# SECTION 3 — vectorized nearest-boundary distance (windows -> seconds)
# ============================================================================
def nearest_dist_s(query_window_idx, boundary_window_indices):
    """query_window_idx: 1D array of window indices (float ok, will be used
    as position). boundary_window_indices: sorted 1D int array of reference
    positions. Returns distance in SECONDS to the nearest boundary."""
    if len(boundary_window_indices) == 0:
        return np.full(len(query_window_idx), np.inf)
    b = np.asarray(boundary_window_indices)
    pos = np.searchsorted(b, query_window_idx)
    pos = np.clip(pos, 1, len(b) - 1)
    left = b[pos - 1]
    right = b[pos]
    d = np.minimum(np.abs(query_window_idx - left), np.abs(query_window_idx - right))
    return d * WIN_SEC


# ============================================================================
# SECTION 4 — per-subject diagnosis
# ============================================================================
def load_scores(scores_dir, subj):
    i = Path(scores_dir) / f"{subj}_ens_inter.npy"
    c = Path(scores_dir) / f"{subj}_ens_ictal.npy"
    if not (i.exists() and c.exists()):
        return None, None
    return np.load(str(i)), np.load(str(c))


def diagnose_subject(subj, inter, ictal, summary_dir, pen, mag, local_win,
                     boundary_window_s, seed):
    np.random.seed(seed)
    signal, is_ictal, is_buffer, real_inter, sz_ranges, n_inter_h = \
        SE.build_timeline_masked(subj, inter, ictal, summary_dir)
    n = len(signal)

    cps, _ = V14.detect_changepoints(signal, pen, min_mag_pct=mag,
                                     local_win=local_win, inter_mask=real_inter)
    final_hyp, survived_cps = build_final_hyp_events(cps, is_buffer, signal, sz_ranges)
    ref_merged = build_extended_merged_ref(sz_ranges)
    tp_events, fp_events = classify_events(final_hyp, ref_merged)

    # ---- self-check vs authoritative timescoring ----
    ref_iv = [(s * WIN_SEC, e * WIN_SEC) for (s, e) in sz_ranges]
    hyp_iv_auth = SE.cps_to_events(cps, is_buffer, n, sz_ranges=sz_ranges)
    total_dur_s = n * WIN_SEC
    sc = SE.score_szcore(ref_iv, hyp_iv_auth, total_dur_s, n_inter_h)
    approx_fp, approx_tp = len(fp_events), len(tp_events)

    # ---- file boundary map ----
    file_map, files_covered = file_window_map(subj, summary_dir)
    boundaries = sorted(set(
        [f['start_idx'] for f in file_map] + [f['end_idx'] for f in file_map]))
    boundaries = np.array(boundaries, dtype=float)

    # ---- seizure edge map (window index space) ----
    sz_edges = np.array(sorted(set(
        [s for (s, e) in sz_ranges] + [e for (s, e) in sz_ranges])), dtype=float)

    # ---- null base rate: fraction of the whole recorded surface near a boundary ----
    w_idx = np.arange(files_covered, dtype=float)
    null_dist = nearest_dist_s(w_idx, boundaries)
    null_pct_near_boundary = float(np.mean(null_dist <= boundary_window_s))

    rows = []
    for (s, e, mem) in fp_events:
        center_w = (s + e) / 2.0 / WIN_SEC
        dist_boundary = float(nearest_dist_s(np.array([center_w]), boundaries)[0])
        dist_sz = (float(nearest_dist_s(np.array([center_w]), sz_edges)[0])
                  if len(sz_edges) else float('inf'))
        frac_buffer = float(np.mean([is_buffer[c] for c in mem])) if mem else float('nan')
        mags = [V14._cp_magnitude(signal, c, local_win) for c in mem]
        rows.append(dict(
            subject=subj, onset_s=round(s, 1), end_s=round(e, 1),
            duration_s=round(e - s, 1), n_underlying_cps=len(mem),
            mean_cp_magnitude=round(float(np.mean(mags)), 4) if mags else None,
            dist_to_file_boundary_s=round(dist_boundary, 1),
            near_boundary=(dist_boundary <= boundary_window_s),
            dist_to_seizure_edge_s=(round(dist_sz, 1) if np.isfinite(dist_sz) else None),
            frac_underlying_windows_in_buffer=round(frac_buffer, 3) if mem else None,
            session=session_at(int(round(center_w)), file_map),
            hour_of_day=(round(h, 2) if (h := hour_of_day_at(int(round(center_w)), file_map)) is not None else None),
        ))

    fp_df = pd.DataFrame(rows)
    n_fp = len(fp_df)
    pct_near_boundary = float(fp_df['near_boundary'].mean()) if n_fp else float('nan')
    enrichment = (pct_near_boundary / null_pct_near_boundary
                 if null_pct_near_boundary > 0 else float('nan'))

    summary = dict(
        subject=subj, pen=pen, mag=mag,
        approx_fp=approx_fp, authoritative_fp=sc['fp'],
        approx_tp=approx_tp, authoritative_tp=sc['tp'],
        fp_count_match=(abs(approx_fp - sc['fp']) <= max(2, round(0.05 * max(sc['fp'], 1)))),
        n_inter_h=round(n_inter_h, 2),
        pct_fp_near_boundary=round(pct_near_boundary, 4) if n_fp else None,
        null_pct_near_boundary=round(null_pct_near_boundary, 4),
        boundary_enrichment=round(enrichment, 2) if n_fp else None,
        median_n_underlying_cps=(float(fp_df['n_underlying_cps'].median()) if n_fp else None),
        median_cp_magnitude=(float(fp_df['mean_cp_magnitude'].median()) if n_fp else None),
        median_dist_to_seizure_edge_s=(float(fp_df['dist_to_seizure_edge_s'].median()) if n_fp else None),
        pct_fp_with_buffer_contamination=(
            float((fp_df['frac_underlying_windows_in_buffer'] > 0).mean()) if n_fp else None),
        n_sessions=len(set(f['session'] for f in file_map)),
    )
    return fp_df, summary


# ============================================================================
# SECTION 5 — orchestration
# ============================================================================
def main():
    ap = argparse.ArgumentParser(description="Step 0: FP mechanism diagnostic")
    ap.add_argument("--scores_dir", default="results/cpd/scores")
    ap.add_argument("--summary_dir",
                    default=r"F:\Study\Thesis\Dataset\CHB-MIT\CHB info\summary")
    ap.add_argument("--out_dir", default="results/phaseB/fp_diagnosis")
    ap.add_argument("--pen", type=float, default=1.0, help="balanced point default")
    ap.add_argument("--mag", type=float, default=60, help="balanced point default")
    ap.add_argument("--local_win", type=int, default=15)
    ap.add_argument("--boundary_window_s", type=float, default=60,
                    help="how close (s) to a file boundary counts as 'near'")
    ap.add_argument("--canonical_seed", type=int, default=0)
    ap.add_argument("--subjs", default=",".join(TEST_SUBJS))
    args = ap.parse_args()

    subjs = args.subjs.split(",")
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    print("=" * 88)
    print(f"FP MECHANISM DIAGNOSIS  |  pen={args.pen:g}  mag={args.mag:g}  "
          f"boundary_window={args.boundary_window_s:g}s")
    print("(read-only introspection on the locked v14 detection path; "
          "no threshold/algorithm change)")
    print("=" * 88)

    all_fp_rows, summaries = [], []
    for subj in subjs:
        inter, ictal = load_scores(args.scores_dir, subj)
        if inter is None:
            print(f"  [skip] {subj}: cached ensemble scores not found")
            continue
        fp_df, summ = diagnose_subject(subj, inter, ictal, args.summary_dir,
                                       args.pen, args.mag, args.local_win,
                                       args.boundary_window_s, args.canonical_seed)
        all_fp_rows.append(fp_df)
        summaries.append(summ)
        match_flag = "OK" if summ["fp_count_match"] else "**MISMATCH**"
        print(f"  {subj}: approx_fp={summ['approx_fp']:>4}  authoritative_fp="
              f"{summ['authoritative_fp']:>4}  [{match_flag}]   "
              f"near_boundary={summ['pct_fp_near_boundary']}"
              f" (null={summ['null_pct_near_boundary']}, "
              f"enrich={summ['boundary_enrichment']})   "
              f"median_dist_to_seizure_edge_s={summ['median_dist_to_seizure_edge_s']}")

    if not all_fp_rows:
        print("\nNo subjects processed -- check --scores_dir / --summary_dir.")
        return

    fp_all = pd.concat(all_fp_rows, ignore_index=True)
    fp_all.to_csv(out / "fp_event_diagnostics.csv", index=False)

    summ_df = pd.DataFrame(summaries)
    summ_df.to_csv(out / "fp_diagnosis_summary.csv", index=False)

    # ---- pooled self-check ----
    total_approx_fp = summ_df['approx_fp'].sum()
    total_auth_fp = summ_df['authoritative_fp'].sum()
    rel_err = abs(total_approx_fp - total_auth_fp) / max(total_auth_fp, 1)
    print("\n" + "-" * 88)
    print(f"SELF-CHECK (pooled): approx FP={total_approx_fp}  vs  "
          f"authoritative (timescoring) FP={total_auth_fp}  "
          f"(rel. error {rel_err:.1%})")
    if rel_err > 0.05:
        print("  ** WARNING: approximation drifted >5% from the authoritative "
              "scorer. Treat per-event breakdown below as indicative of the "
              "DOMINANT mechanism only, not an exact count. **")
    else:
        print("  Approximation tracks the authoritative scorer closely -- "
              "per-event breakdown below can be read with confidence.")

    # ---- pooled mechanism summary ----
    print("\nPOOLED FP CHARACTERIZATION (all subjects, all FP events):")
    n_fp_total = len(fp_all)
    print(f"  Total FP events (approx): {n_fp_total}")
    print(f"  Median duration: {fp_all['duration_s'].median():.1f}s   "
          f"Median n_underlying_cps: {fp_all['n_underlying_cps'].median():.1f}")
    print(f"  % near a file boundary (<= {args.boundary_window_s:g}s): "
          f"{fp_all['near_boundary'].mean():.1%}   "
          f"(pooled null base rate: {summ_df['null_pct_near_boundary'].mean():.1%})")
    print(f"  Median distance to nearest seizure edge: "
          f"{fp_all['dist_to_seizure_edge_s'].median():.1f}s")
    buf_contam = (fp_all['frac_underlying_windows_in_buffer'] > 0).mean()
    print(f"  % of FP events with ANY underlying CP still touching the buffer "
          f"zone: {buf_contam:.1%}  (expect near 0 -- confirms the buffer-fix "
          f"already removed this source)")

    print(f"\nWrote:")
    print(f"  {(out / 'fp_event_diagnostics.csv').resolve()}")
    print(f"  {(out / 'fp_diagnosis_summary.csv').resolve()}")
    print("\nGửi 2 file CSV này lại để đọc và kết luận cơ chế FP chiếm ưu thế.")


if __name__ == "__main__":
    main()