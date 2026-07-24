"""
================================================================================
 test_cross_view_consensus.py  (falsification test -- NOT a v14/v15 change)
================================================================================
PRE-REGISTERED HYPOTHESIS
--------------------------
Most FP events arise because exactly ONE of the three ensemble components
(recon / temporal / gamma) has a transient spurious fluctuation large enough
to push the weighted ensemble score over threshold, while the other two
components stay quiet. Genuine ictal transitions, by contrast, are typically
corroborated by >=2/3 components (per the event-tier ablation: no subject
fails all three views simultaneously except chb06).

PRE-REGISTERED TEST DESIGN (fixed BEFORE looking at results)
---------------------------------------------------------------
For every change point already emitted at the LOCKED balanced operating
point (pen=1.0, mag=60), independently reconstruct each of the 3 component
timelines (zrecon, ztemp, zgamma), smooth each identically to the ensemble
(1-min centered MA), and mark component v "elevated" at CP c if:
    smoothed_v[c-tol : c+tol+1].max() > median(smoothed_v) + elevation_k * MAD_std(smoothed_v)
with elevation_k=1.0, tol=2 windows (+/-8s) -- round, label-free, not tuned.
An event survives a hypothetical "2-of-3 consensus" filter iff >=2 of its
3 components are elevated at (at least one of) its underlying CPs.

PRE-REGISTERED PASS/FAIL CRITERION
-------------------------------------
  FP_removal_rate = fraction of FP events that WOULD be dropped by 2-of-3
  TP_removal_rate = fraction of TP-contributing CPs that WOULD ALSO be
                    dropped by the exact same rule (collateral damage to
                    real detections)
  PASS (worth engineering into v15) iff:
      FP_removal_rate >= 0.30   AND   FP_removal_rate / max(TP_removal_rate, 0.01) >= 3.0
  Otherwise: FAIL -- report as a negative result, do not implement in v14/v15.

This script does NOT change the algorithm or re-lock anything. It only
diagnoses whether the consensus idea is worth building. It reuses the exact
merge/split/match logic already validated (self-checked against the
authoritative timescoring FP count) in diagnose_fp_mechanism.py.

CAVEAT (GPU non-reproducibility, same as event_ablation.py)
--------------------------------------------------------------
Re-exported components (zrecon/ztemp/zgamma) do not bit-reproduce the locked
ensemble (closure err ~2, per Core Rule #7). This script uses the CACHED
ENSEMBLE scores (authoritative) to determine which CPs are TP/FP, and only
uses the components to check view-agreement AT those CP locations -- so the
TP/FP classification itself is unaffected by component drift; only the
elevation check could be mildly noisy if components drifted. Acceptable for
a feasibility/falsification test.

USAGE
-----
  python test_cross_view_consensus.py \
      --scores_dir results/cpd/scores --comp_dir data/processed/components \
      --summary_dir "F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary"

Requires: diagnose_fp_mechanism.py, cpd_pipeline_v14.py, szcore_eval.py,
evaluation_protocol.py (same dir). CPU only, no GPU, no retrain.
================================================================================
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import cpd_pipeline_v14 as V14
import szcore_eval as SE
import evaluation_protocol as E
import diagnose_fp_mechanism as FPD  # reuse validated merge/split/match logic

WIN_SEC = E.WIN_SEC
TEST_SUBJS = E.TEST_SUBJS
COMPONENTS = ["zrecon", "ztemp", "zgamma"]

# ---- pre-registered constants (do not tune after seeing results) ----
ELEVATION_K = 1.0
TOL_WIN = 2
FP_REMOVAL_MIN = 0.30
SELECTIVITY_MIN = 3.0


# ============================================================================
# Loading
# ============================================================================
def load_ensemble(scores_dir, subj):
    i = Path(scores_dir) / f"{subj}_ens_inter.npy"
    c = Path(scores_dir) / f"{subj}_ens_ictal.npy"
    if not (i.exists() and c.exists()):
        return None, None
    return np.load(str(i)), np.load(str(c))


def load_component(comp_dir, subj, name):
    i = Path(comp_dir) / f"{name}_{subj}_inter.npy"
    c = Path(comp_dir) / f"{name}_{subj}_ictal.npy"
    if not (i.exists() and c.exists()):
        return None, None
    return np.load(str(i)).astype(np.float64), np.load(str(c)).astype(np.float64)


def build_component_timeline(subj, comp_inter, comp_ictal, summary_dir, seed):
    """Same window structure as the ensemble timeline (is_ictal/is_buffer only
    depend on file/seizure metadata, not on the score values), so window index
    c means the identical physical 4s window across ensemble and every
    component, as long as the array LENGTHS match and the seed is reset."""
    np.random.seed(seed)
    signal, _, _, _, _, _ = SE.build_timeline_masked(
        subj, comp_inter, comp_ictal, summary_dir)
    return signal


# ============================================================================
# Elevation check
# ============================================================================
def elevation_threshold(smoothed):
    med = np.median(smoothed)
    mad = np.median(np.abs(smoothed - med)) + 1e-9
    return med + ELEVATION_K * 1.4826 * mad


def is_elevated(smoothed, cp_indices, thresh, n, tol=TOL_WIN):
    for c in cp_indices:
        lo, hi = max(0, c - tol), min(n, c + tol + 1)
        if smoothed[lo:hi].max() > thresh:
            return True
    return False


# ============================================================================
# Per-subject test
# ============================================================================
def test_subject(subj, scores_dir, comp_dir, summary_dir, pen, mag, local_win, seed):
    inter, ictal = load_ensemble(scores_dir, subj)
    if inter is None:
        return None, None

    np.random.seed(seed)
    signal, is_ictal, is_buffer, real_inter, sz_ranges, n_inter_h = \
        SE.build_timeline_masked(subj, inter, ictal, summary_dir)
    n = len(signal)

    cps, _ = V14.detect_changepoints(signal, pen, min_mag_pct=mag,
                                     local_win=local_win, inter_mask=real_inter)
    final_hyp, _ = FPD.build_final_hyp_events(cps, is_buffer, signal, sz_ranges)
    ref_merged = FPD.build_extended_merged_ref(sz_ranges)
    tp_events, fp_events = FPD.classify_events(final_hyp, ref_merged)

    # load + smooth each component, aligned window-for-window to the ensemble
    comp_smoothed = {}
    comp_thresh = {}
    missing = []
    for name in COMPONENTS:
        ci, cc = load_component(comp_dir, subj, name)
        if ci is None:
            missing.append(name)
            continue
        comp_signal = build_component_timeline(subj, ci, cc, summary_dir, seed)
        if len(comp_signal) != n:
            print(f"  [warn] {subj}/{name}: length mismatch ({len(comp_signal)} vs "
                 f"{n} ensemble windows) -- skipping this component for this subject")
            missing.append(name)
            continue
        smoothed = V14._smooth(comp_signal)
        comp_smoothed[name] = smoothed
        comp_thresh[name] = elevation_threshold(smoothed)
    if len(comp_smoothed) < 3:
        print(f"  [skip] {subj}: missing component(s) {missing} in {comp_dir}")
        return None, None

    def n_views_elevated(mem):
        return sum(is_elevated(comp_smoothed[v], mem, comp_thresh[v], n)
                  for v in COMPONENTS)

    rows = []
    for (s, e, mem) in fp_events:
        nv = n_views_elevated(mem)
        rows.append(dict(subject=subj, event_type="FP", onset_s=s, n_views=nv,
                         would_be_removed=(nv < 2)))
    for (s, e, mem) in tp_events:
        nv = n_views_elevated(mem)
        rows.append(dict(subject=subj, event_type="TP", onset_s=s, n_views=nv,
                         would_be_removed=(nv < 2)))
    df = pd.DataFrame(rows)

    n_fp, n_tp = len(fp_events), len(tp_events)
    fp_removal = float(df[df.event_type == "FP"]["would_be_removed"].mean()) if n_fp else float("nan")
    tp_removal = float(df[df.event_type == "TP"]["would_be_removed"].mean()) if n_tp else float("nan")
    selectivity = fp_removal / max(tp_removal, 0.01) if n_fp and n_tp else float("nan")

    summ = dict(subject=subj, n_fp=n_fp, n_tp=n_tp,
               fp_removal_rate=round(fp_removal, 4) if n_fp else None,
               tp_removal_rate=round(tp_removal, 4) if n_tp else None,
               selectivity_ratio=round(selectivity, 2) if n_fp and n_tp else None)
    return df, summ


# ============================================================================
# Orchestration
# ============================================================================
def main():
    ap = argparse.ArgumentParser(description="Falsification test: cross-view CP consensus")
    ap.add_argument("--scores_dir", default="results/cpd/scores")
    ap.add_argument("--comp_dir", default="data/processed/components")
    ap.add_argument("--summary_dir",
                    default=r"F:\Study\Thesis\Dataset\CHB-MIT\CHB info\summary")
    ap.add_argument("--out_dir", default="results/phaseB/cross_view_consensus")
    ap.add_argument("--pen", type=float, default=1.0)
    ap.add_argument("--mag", type=float, default=60)
    ap.add_argument("--local_win", type=int, default=15)
    ap.add_argument("--canonical_seed", type=int, default=0)
    ap.add_argument("--subjs", default=",".join(TEST_SUBJS))
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    print("=" * 88)
    print("CROSS-VIEW CP CONSENSUS -- FALSIFICATION TEST (pre-registered, not tuned)")
    print(f"elevation_k={ELEVATION_K}  tol_win={TOL_WIN} (+/-{TOL_WIN*WIN_SEC}s)  "
         f"consensus=2-of-3")
    print(f"PASS iff  FP_removal_rate >= {FP_REMOVAL_MIN:.2f}  AND  "
         f"FP_removal_rate/TP_removal_rate >= {SELECTIVITY_MIN:.1f}")
    print("=" * 88)

    all_rows, summaries = [], []
    for subj in args.subjs.split(","):
        df, summ = test_subject(subj, args.scores_dir, args.comp_dir,
                               args.summary_dir, args.pen, args.mag,
                               args.local_win, args.canonical_seed)
        if df is None:
            continue
        all_rows.append(df)
        summaries.append(summ)
        print(f"  {subj}: n_fp={summ['n_fp']:>3}  n_tp={summ['n_tp']:>3}   "
             f"FP_removal={summ['fp_removal_rate']}   TP_removal={summ['tp_removal_rate']}"
             f"   selectivity={summ['selectivity_ratio']}")

    if not all_rows:
        print("\nNo subjects processed -- check --scores_dir / --comp_dir / --summary_dir.")
        return

    events_df = pd.concat(all_rows, ignore_index=True)
    events_df.to_csv(out / "cross_view_events.csv", index=False)
    summ_df = pd.DataFrame(summaries)
    summ_df.to_csv(out / "cross_view_summary.csv", index=False)

    # ---- pooled verdict ----
    fp_all = events_df[events_df.event_type == "FP"]
    tp_all = events_df[events_df.event_type == "TP"]
    pooled_fp_removal = float(fp_all["would_be_removed"].mean()) if len(fp_all) else float("nan")
    pooled_tp_removal = float(tp_all["would_be_removed"].mean()) if len(tp_all) else float("nan")
    pooled_selectivity = pooled_fp_removal / max(pooled_tp_removal, 0.01)

    verdict = (pooled_fp_removal >= FP_REMOVAL_MIN and pooled_selectivity >= SELECTIVITY_MIN)

    print("\n" + "-" * 88)
    print(f"POOLED (all subjects, n_fp={len(fp_all)}, n_tp={len(tp_all)}):")
    print(f"  FP_removal_rate = {pooled_fp_removal:.3f}   "
         f"(need >= {FP_REMOVAL_MIN:.2f})")
    print(f"  TP_removal_rate = {pooled_tp_removal:.3f}   (collateral damage to real detections)")
    print(f"  selectivity = FP_removal/TP_removal = {pooled_selectivity:.2f}   "
         f"(need >= {SELECTIVITY_MIN:.1f})")
    print(f"\n  VERDICT: {'PASS -- worth engineering into v15' if verdict else 'FAIL -- negative result, do NOT implement'}")

    print(f"\nWrote:")
    print(f"  {(out / 'cross_view_events.csv').resolve()}")
    print(f"  {(out / 'cross_view_summary.csv').resolve()}")
    print("\nGửi 2 file CSV này lại để đọc và xác nhận PASS/FAIL trước khi quyết định bước tiếp.")


if __name__ == "__main__":
    main()