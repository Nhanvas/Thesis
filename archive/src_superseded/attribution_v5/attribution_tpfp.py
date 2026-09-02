"""
================================================================================
 attribution_tpfp.py  —  STAGE 2 of ATTRIBUTION REDESIGN (PRE-REGISTRATION v3.1)
 TEST D ONLY: does attribution CONCENTRATION discriminate TP from FP detections?
================================================================================
Implements EXACTLY §4 / §4.1 / §4.2 / §4.4 of ATTRIBUTION_PREREGISTRATION_v3_1.md.
No test beyond D is implemented. No falsification criterion is altered.
Stage 1's |z| and Gini machinery is REUSED by import (§7 ordering), never re-defined.

READ D2 FIRST (§7 Stage 2: "FIRST CHECK ON OUTPUT: D2").
  If concentration is redundant with (anomaly score + event duration), this script
  prints REDUNDANT and DOES NOT compute the D3 operating curve at all - so that no
  triage narrative can be built from an artifact that should not exist.

--------------------------------------------------------------------------------
SPECIFICATION CONFLICT IN §4, AND HOW IT IS RESOLVED (documented, not silent)
--------------------------------------------------------------------------------
§4 states BOTH of the following, and they are not compatible:
  (i)  "One detected event from cpd_pipeline_v14.detect_events at mag60/pen1.0"
  (ii) "Reference counts: 57 TP, 461 FP, 39.77 FP/day"
`V14.detect_events` does NOT apply the post-ictal buffer don't-care layer, which
lives in `szcore_eval.cps_to_events` and is part of the LOCKED evaluation path that
produced 57/461 (it is the fix that un-zeroed chb16 and rescued chb06). Running
detect_events verbatim yields MORE hypothesis events than 461, and D3 - which is
anchored to the locked balanced point (0.750 sens, 39.77 FP/day) - would then be
anchored to a different event set than the one it reports on.

RESOLUTION: the event unit is defined by the REFERENCE COUNTS, not by the function
name. Events are built on the locked evaluation path
    V14.detect_changepoints(..., min_mag_pct=60, inter_mask=real_inter)
      -> SZ.cps_to_events(...)                      [buffer don't-care layer]
      -> merge at 90 s, split at 300 s              [merging logic OF detect_events
                                                     / SzCORE EventScoring params]
and a HARD GUARD aborts unless the pooled result reproduces TP=57, FP=461,
sensitivity=0.750, FP/day=39.77 (operating rule #5: a new harness must reproduce
the locked numbers before it is trusted). Disable only for the synthetic self-test.

--------------------------------------------------------------------------------
TWO NON-OBVIOUS CORRECTNESS PROBLEMS, AND THEIR GUARDS
--------------------------------------------------------------------------------
1. PADDED WINDOWS HAVE NO PER-NODE DATA. `build_timeline_masked` reconstructs the
   timeline with BOOTSTRAP-RESAMPLED scores in post-ictal buffer regions and in any
   tail overflow. Those windows have a score but NO corresponding row in the
   per-node arrays. Computing Gini over them would silently mix real attribution
   with resampled noise. This script therefore rebuilds the timeline while
   recording, per window, its source (`inter` row j / `ictal` row i / `pad`), drops
   `pad` windows from every per-event computation, and reports how many were
   dropped. GUARD: the rebuilt score timeline must be bit-comparable
   (np.allclose) to `szcore_eval.build_timeline_masked` under the same seed,
   otherwise the index map is untrustworthy and the script aborts.

2. THE QUARANTINED OLD-WEIGHT ENSEMBLE CACHE. `szcore_eval.load_scores` reads
   `{subj}_ens_{inter,ictal}.npy` - exactly the old-weight cache that caused the
   §13/§14 drift. This script NEVER calls it: the ensemble is built from components
   through `ensemble_recipe.build_ensemble` at weight (0.40, 0.35, 0.25). GUARD: the
   script refuses to run if `--comp_dir` resolves inside `history_superseded` or if
   any `*_ens_*.npy` file is visible in it.

USAGE (CPU only, no retraining, ~30-60 min)
  python attribution_tpfp.py \
      --comp_dir data/processed/components \
      --pernode_root data/pernode \
      --summary_dir "F:\\Study\\Thesis\\Dataset\\CHB-MIT\\CHB info\\summary" \
      --outdir results/attribution_v3

SELF-TEST (synthetic, no real data needed)
  python attribution_tpfp.py --selftest
================================================================================
"""
import argparse
import glob
import json
import os
import platform
import sys
from datetime import datetime, timezone

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score

# Stage 1 machinery, reused by import (§7): |z|, Gini, entropy, top-5 mass
from attribution_v3 import (gini, norm_entropy, topk_mass, abs_z, find_pernode,
                            bootstrap_median_ci, MAD_EPS, N_CH, TOPK, CH_NAMES)

SCRIPT_VERSION = "attribution_tpfp.py / pre-registration v3.1 / Stage 2 (Test D)"

# ---- LOCKED balanced operating point (RESULTS_OF_RECORD; do not re-derive) ----
PEN_MULT = 1.0
MIN_MAG_PCT = 60
LOCAL_WIN = 15
MERGE_S = 90                 # SzCORE minDurationBetweenEvents
MAX_EVENT_S = 5 * 60         # SzCORE maxEventDuration
TOL_START, TOL_END = 30, 60
NEAR_MISS_S = 5 * 60         # §4.2 near-miss radius
LOCK = dict(tp=57, fp=461, sensitivity=0.750, fp_per_day=39.77)


# ============================================================================
# GUARDS
# ============================================================================
def guard_component_dir(comp_dir):
    ap = os.path.abspath(comp_dir).replace("\\", "/")
    if "history_superseded" in ap.lower():
        raise RuntimeError(
            f"REFUSED: --comp_dir resolves inside a quarantined directory:\n  {ap}\n"
            "The old-weight ensemble cache must never be read (operating rule #6).")
    stray = [p for p in glob.glob(os.path.join(comp_dir, "**", "*_ens_*.npy"),
                                  recursive=True)]
    if stray:
        raise RuntimeError(
            "REFUSED: quarantined-style ensemble cache files are visible in "
            f"--comp_dir:\n  " + "\n  ".join(stray[:5]) +
            "\nBuild the ensemble from components via ensemble_recipe instead.")


# ============================================================================
# TIMELINE + PER-NODE INDEX MAP  (mirror of szcore_eval.build_timeline_masked)
# ============================================================================
SRC_INTER, SRC_ICTAL, SRC_PAD = 0, 1, 2


def build_timeline_indexmap(subj, inter_scores, ictal_scores, summary_dir, E, WIN_SEC):
    """Byte-for-byte mirror of szcore_eval.build_timeline_masked, additionally
    recording per timeline window: source array (inter / ictal / pad) and row index.
    RNG consumption is identical, so under the same seed the score timelines match."""
    from pathlib import Path
    edfs = E.parse_summary_edf_list(Path(summary_dir) / f"{subj}-summary.txt")
    scores_out, kind_out, idx_out = [], [], []
    inter_ptr = ictal_ptr = 0
    bootstrap_pool = np.random.choice(inter_scores, size=250000, replace=True)
    boot_ptr = 0
    BUFFER_H = 4

    for edf in edfs:
        dur = edf["duration_s"]
        n_win = dur // WIN_SEC
        labels = np.zeros(dur, dtype=np.int8)
        buf = np.zeros(dur, dtype=bool)
        for (on, off) in edf["seizures"]:
            on = min(on, dur); off = min(off, dur)
            labels[on:off] = 1
            buf[off:min(dur, off + BUFFER_H * 3600)] = True
        tl = n_win * WIN_SEC
        wl = labels[:tl].reshape(n_win, WIN_SEC).max(axis=1)
        wb = buf[:tl].reshape(n_win, WIN_SEC).any(axis=1)
        for w in range(n_win):
            if int(wl[w]) == 1:
                if ictal_ptr < len(ictal_scores):
                    scores_out.append(float(ictal_scores[ictal_ptr]))
                    kind_out.append(SRC_ICTAL); idx_out.append(ictal_ptr)
                else:
                    scores_out.append(0.0)
                    kind_out.append(SRC_PAD); idx_out.append(-1)
                ictal_ptr += 1
            elif bool(wb[w]):
                scores_out.append(float(bootstrap_pool[boot_ptr]))
                boot_ptr = (boot_ptr + 1) % len(bootstrap_pool)
                kind_out.append(SRC_PAD); idx_out.append(-1)
            else:
                if inter_ptr < len(inter_scores):
                    scores_out.append(float(inter_scores[inter_ptr]))
                    kind_out.append(SRC_INTER); idx_out.append(inter_ptr)
                    inter_ptr += 1
                else:
                    scores_out.append(float(bootstrap_pool[boot_ptr]))
                    boot_ptr = (boot_ptr + 1) % len(bootstrap_pool)
                    kind_out.append(SRC_PAD); idx_out.append(-1)

    if inter_ptr < len(inter_scores):
        for j in range(inter_ptr, len(inter_scores)):
            scores_out.append(float(inter_scores[j]))
            kind_out.append(SRC_INTER); idx_out.append(j)

    return (np.asarray(scores_out, dtype=np.float32),
            np.asarray(kind_out, dtype=np.int8),
            np.asarray(idx_out, dtype=np.int64))


# ============================================================================
# EVENT CONSTRUCTION + LABELLING
# ============================================================================
def merge_and_split(single_win_events, merge_s=MERGE_S, max_dur=MAX_EVENT_S):
    """Merging logic of V14.detect_events + SzCORE maxEventDuration splitting."""
    ev = []
    for (t0, t1) in sorted(single_win_events):
        if ev and t0 - ev[-1][1] <= merge_s:
            ev[-1] = (ev[-1][0], t1)
        else:
            ev.append((t0, t1))
    out = []
    for (t0, t1) in ev:
        while t1 - t0 > max_dur:
            out.append((t0, t0 + max_dur))
            t0 += max_dur
        out.append((t0, t1))
    return out


def label_events(events, ref_iv):
    """TP if the event overlaps a reference within SzCORE tolerance, else FP.
    near_miss: an FP within NEAR_MISS_S of any reference event (§4.2)."""
    labels, near = [], []
    for (h0, h1) in events:
        hit = any(h1 >= r0 - TOL_START and h0 <= r1 + TOL_END for (r0, r1) in ref_iv)
        labels.append(1 if hit else 0)
        if hit or not ref_iv:
            near.append(False)
        else:
            d = min(max(r0 - h1, h0 - r1, 0.0) for (r0, r1) in ref_iv)
            near.append(bool(d <= NEAR_MISS_S))
    return np.asarray(labels, dtype=int), np.asarray(near, dtype=bool)


# ============================================================================
# PER-SUBJECT EXTRACTION
# ============================================================================
def extract_subject(subj, comp_dir, pernode_root, summary_dir, E, SZ, V14, ER,
                    win_sec, seed=0, verbose=True):
    zi = ER.load_components(comp_dir, subj, "inter")
    zc = ER.load_components(comp_dir, subj, "ictal")
    ens_inter = ER.build_ensemble(*zi)
    ens_ictal = ER.build_ensemble(*zc)

    # --- locked timeline (authoritative) + index-mapped mirror ---------------
    np.random.seed(seed)
    signal, is_ictal, is_buffer, real_inter, sz_ranges, n_inter_h = \
        SZ.build_timeline_masked(subj, ens_inter, ens_ictal, summary_dir)
    np.random.seed(seed)
    sig2, kind, idx = build_timeline_indexmap(subj, ens_inter, ens_ictal,
                                              summary_dir, E, win_sec)
    if sig2.shape != signal.shape or not np.allclose(sig2, signal, atol=1e-6):
        raise RuntimeError(
            f"{subj}: INDEX-MAP GUARD FAILED - the rebuilt timeline does not match "
            f"szcore_eval.build_timeline_masked (shapes {sig2.shape} vs "
            f"{signal.shape}). Per-node indexing would be silently wrong. ABORT.")

    # --- locked detection path ---------------------------------------------
    cps, _ = V14.detect_changepoints(signal, PEN_MULT, min_mag_pct=MIN_MAG_PCT,
                                     local_win=LOCAL_WIN, inter_mask=real_inter)
    hyp_single = SZ.cps_to_events(cps, is_buffer, len(signal), sz_ranges=sz_ranges)
    ref_iv = [(s * win_sec, e * win_sec) for (s, e) in sz_ranges]
    sc = SZ.score_szcore(ref_iv, hyp_single, len(signal) * win_sec, n_inter_h)

    events = merge_and_split(hyp_single)
    labels, near = label_events(events, ref_iv)

    # --- per-node baseline ---------------------------------------------------
    p_int = find_pernode(pernode_root, subj, "inter")
    p_ict = find_pernode(pernode_root, subj, "ictal")
    if p_int is None or p_ict is None:
        raise FileNotFoundError(f"{subj}: per-node arrays not found under {pernode_root}")
    pn_inter = np.load(p_int).astype(float)
    pn_ictal = np.load(p_ict).astype(float)
    inter_med = np.median(pn_inter, axis=0)
    inter_mad = np.median(np.abs(pn_inter - inter_med), axis=0) + MAD_EPS

    rows, n_dropped, n_pad_win = [], 0, 0
    for e_i, ((t0, t1), lab, nm) in enumerate(zip(events, labels, near)):
        w0, w1 = int(t0 // win_sec), int(np.ceil(t1 / win_sec))
        w1 = min(w1, len(signal))
        if w1 <= w0:
            n_dropped += 1
            continue
        ww = np.arange(w0, w1)
        k = kind[ww]
        n_pad_win += int(np.sum(k == SRC_PAD))
        feats = []
        if np.any(k == SRC_ICTAL):
            ii = idx[ww][k == SRC_ICTAL]
            ii = ii[(ii >= 0) & (ii < pn_ictal.shape[0])]
            if ii.size:
                feats.append(pn_ictal[ii])
        if np.any(k == SRC_INTER):
            jj = idx[ww][k == SRC_INTER]
            jj = jj[(jj >= 0) & (jj < pn_inter.shape[0])]
            if jj.size:
                feats.append(pn_inter[jj])
        if not feats:
            n_dropped += 1          # entirely padded event: no per-node evidence
            continue
        F = np.vstack(feats)
        az = abs_z(F, inter_med, inter_mad)
        rows.append(dict(
            subject=subj, event_idx=e_i, t_start=float(t0), t_end=float(t1),
            duration_s=float(t1 - t0), n_windows=int(ww.size),
            n_windows_resolved=int(F.shape[0]),
            label=int(lab), label_str="TP" if lab else "FP",
            near_miss=bool(nm),
            fp_class=("TP" if lab else ("near_miss_FP" if nm else "remote_FP")),
            gini=gini(az), entropy_norm=norm_entropy(az), top5_mass=topk_mass(az),
            mean_anomaly_score=float(np.mean(signal[w0:w1])),
            max_anomaly_score=float(np.max(signal[w0:w1])),
            top5_channels="|".join(CH_NAMES[i] for i in np.argsort(az)[::-1][:TOPK]),
        ))

    if verbose:
        print(f"  {subj}: timescoring TP={sc['tp']:>2} FP={sc['fp']:>3} "
              f"sens={sc['sensitivity']:.3f} | events={len(events)} "
              f"(TP {int(labels.sum())} / FP {int((1-labels).sum())}, "
              f"near-miss {int(near.sum())}) | dropped={n_dropped} "
              f"pad-win={n_pad_win}")
    return rows, sc, dict(subject=subj, n_events=len(events),
                          n_dropped_no_pernode=n_dropped, n_pad_windows=n_pad_win,
                          n_inter_h=n_inter_h)


# ============================================================================
# INFERENCE  (§4: subject-stratified; cluster bootstrap over the 8 subjects)
# ============================================================================
def per_subject_auc(df, col, fn=roc_auc_score):
    """AUROC/AUPRC computed WITHIN each subject (immune to subject-level offsets)."""
    out = {}
    for s, d in df.groupby("subject"):
        y = d["label"].values
        if y.min() == y.max():
            continue
        out[s] = float(fn(y, d[col].values))
    return out


def cluster_bootstrap(subjects, stat_fn, rng, n_boot=2000):
    """One replicate = resample the 8 SUBJECTS with replacement, keeping each
    drawn subject's events intact (§4). Events are never resampled within."""
    subs = np.asarray(subjects)
    vals = []
    for _ in range(n_boot):
        draw = subs[rng.integers(0, subs.size, size=subs.size)]
        v = stat_fn(list(draw))
        if np.isfinite(v):
            vals.append(v)
    if not vals:
        return (np.nan, np.nan, np.nan)
    vals = np.asarray(vals)
    return (float(np.mean(vals)), float(np.percentile(vals, 2.5)),
            float(np.percentile(vals, 97.5)))


def within_subject_z(df, cols):
    """Within-subject standardization (§4): required before any pooled model,
    because Gini and score are systematically offset between subjects."""
    X = df[cols].astype(float).copy()
    for s, d in df.groupby("subject"):
        for c in cols:
            v = d[c].astype(float)
            sd = v.std(ddof=0)
            X.loc[d.index, c] = (v - v.mean()) / (sd if sd > 1e-12 else 1.0)
    return X.values


def model_subject_auroc(df, cols, subjects=None):
    """Fit a pooled logistic model on within-subject standardized covariates,
    then evaluate AUROC WITHIN each subject and average. Returns mean AUROC."""
    d = df if subjects is None else df[df.subject.isin(subjects)]
    if d["label"].nunique() < 2:
        return np.nan
    X = within_subject_z(d, cols)
    y = d["label"].values
    try:
        m = LogisticRegression(max_iter=2000, solver="lbfgs").fit(X, y)
    except Exception:
        return np.nan
    p = m.predict_proba(X)[:, 1]
    dd = d.assign(_p=p)
    aucs = [roc_auc_score(g["label"].values, g["_p"].values)
            for _, g in dd.groupby("subject") if g["label"].nunique() == 2]
    return float(np.mean(aucs)) if aucs else np.nan


# ============================================================================
# MAIN ANALYSIS
# ============================================================================
def analyse(df, outdir, rng, n_boot=2000, n_perm=1000):
    import pandas as pd
    res = {}
    subs = sorted(df.subject.unique())

    # ---------------- D1 -----------------------------------------------------
    a_raw = per_subject_auc(df, "gini")
    p_raw = per_subject_auc(df, "gini", average_precision_score)
    res["D1_per_subject_auroc"] = {k: round(v, 4) for k, v in a_raw.items()}
    res["D1_auroc_mean"] = float(np.mean(list(a_raw.values()))) if a_raw else np.nan
    res["D1_auprc_mean"] = float(np.mean(list(p_raw.values()))) if p_raw else np.nan

    def _auroc_of(dr):
        v = [a_raw[s] for s in dr if s in a_raw]
        return float(np.mean(v)) if v else np.nan

    def _auprc_of(dr):
        v = [p_raw[s] for s in dr if s in p_raw]
        return float(np.mean(v)) if v else np.nan

    _, lo, hi = cluster_bootstrap(subs, _auroc_of, rng, n_boot)
    res["D1_auroc_ci"] = [lo, hi]
    _, plo, phi = cluster_bootstrap(subs, _auprc_of, rng, n_boot)
    res["D1_auprc_ci"] = [plo, phi]
    res["D1_pass"] = bool(np.isfinite(lo) and lo > 0.5)

    # ---------------- D2  (DECISIVE - read this first) -----------------------
    NUIS = ["mean_anomaly_score", "duration_s"]
    FULL = NUIS + ["gini"]
    a_nuis = model_subject_auroc(df, NUIS)
    a_full = model_subject_auroc(df, FULL)
    res["D2_auroc_nuisance(score+duration)"] = a_nuis
    res["D2_auroc_full(+concentration)"] = a_full
    res["D2_auroc_concentration_alone"] = res["D1_auroc_mean"]
    res["D2_incremental_auroc"] = (a_full - a_nuis
                                   if np.isfinite(a_full) and np.isfinite(a_nuis)
                                   else np.nan)

    def _incr_of(dr):
        d = df[df.subject.isin(set(dr))]
        return model_subject_auroc(d, FULL) - model_subject_auroc(d, NUIS)

    _, ilo, ihi = cluster_bootstrap(subs, _incr_of, rng, max(500, n_boot // 4))
    res["D2_incremental_auroc_ci"] = [ilo, ihi]
    res["D2_pass"] = bool(np.isfinite(ilo) and np.isfinite(ihi) and
                          (ilo > 0 or ihi < 0))

    # subject-stratified permutation of concentration (§4)
    obs = res["D2_incremental_auroc"]
    cnt = 0
    for _ in range(n_perm):
        dp = df.copy()
        for s, g in df.groupby("subject"):
            dp.loc[g.index, "gini"] = rng.permutation(g["gini"].values)
        v = model_subject_auroc(dp, FULL) - model_subject_auroc(dp, NUIS)
        if np.isfinite(v) and v >= obs:
            cnt += 1
    res["D2_permutation_p"] = float((cnt + 1) / (n_perm + 1))

    # duration distributions, reported so overlap is directly visible (§4.1)
    for lab, name in [(1, "TP"), (0, "FP")]:
        d = df[df.label == lab]["duration_s"]
        res[f"duration_{name}_median_iqr"] = [float(d.median()),
                                              float(d.quantile(.25)),
                                              float(d.quantile(.75))]

    # ---------------- D4  (mechanism control, §4.2) --------------------------
    grp = df.groupby("fp_class")["gini"].agg(["size", "median"])
    res["D4_group_gini_median"] = {k: [int(v["size"]), float(v["median"])]
                                   for k, v in grp.iterrows()}
    tp_nm = per_subject_auc(df[df.fp_class != "remote_FP"], "gini")
    tp_rm = per_subject_auc(df[df.fp_class != "near_miss_FP"], "gini")
    res["D4_auroc_TP_vs_nearmiss"] = (float(np.mean(list(tp_nm.values())))
                                      if tp_nm else np.nan)
    res["D4_auroc_TP_vs_remote"] = (float(np.mean(list(tp_rm.values())))
                                    if tp_rm else np.nan)

    # ---------------- D3  (ONLY if D1 and D2 both pass, §4.4) ----------------
    if res["D1_pass"] and res["D2_pass"]:
        res["D3_status"] = "computed (D1 and D2 both passed)"
        res.update(loso_operating_curve(df, outdir))
    else:
        res["D3_status"] = ("NOT COMPUTED - " +
                            ("D2 failed: concentration is redundant with anomaly "
                             "score + duration. Per §4 D2: STOP, make no operational "
                             "claim, do not build a triage narrative."
                             if not res["D2_pass"] else
                             "D1 failed: bootstrap AUROC CI includes 0.5."))
    return res


def loso_operating_curve(df, outdir):
    """§4.4 leave-one-subject-out threshold selection on within-subject percentile
    rank of Gini. Only reached if D1 and D2 pass."""
    import pandas as pd
    df = df.copy()
    df["gini_pct"] = df.groupby("subject")["gini"].rank(pct=True)
    subs = sorted(df.subject.unique())
    grid = np.round(np.arange(0.05, 1.00, 0.05), 2)
    held_tp_kept = held_tp = held_fp_removed = held_fp = 0
    per_sub = []
    for s in subs:
        tr, te = df[df.subject != s], df[df.subject == s]
        best, best_rm = None, -1.0
        for thr in grid:                       # keep events with pct >= thr
            k = tr[tr.gini_pct >= thr]
            sens_loss = 1.0 - (k.label.sum() / max(tr.label.sum(), 1))
            fp_removed = 1.0 - ((k.label == 0).sum() / max((tr.label == 0).sum(), 1))
            if sens_loss <= 0.05 and fp_removed > best_rm:
                best, best_rm = thr, fp_removed
        if best is None:
            best = 0.0
        k = te[te.gini_pct >= best]
        held_tp_kept += int(k.label.sum()); held_tp += int(te.label.sum())
        held_fp_removed += int((te.label == 0).sum() - (k.label == 0).sum())
        held_fp += int((te.label == 0).sum())
        per_sub.append(dict(subject=s, threshold=best,
                            tp_kept=int(k.label.sum()), tp_total=int(te.label.sum()),
                            fp_removed=int((te.label == 0).sum() - (k.label == 0).sum()),
                            fp_total=int((te.label == 0).sum())))
    pd.DataFrame(per_sub).to_csv(
        os.path.join(outdir, "tpfp_loso_operating_point.csv"), index=False)
    sens_ret = held_tp_kept / max(held_tp, 1)
    fp_red = held_fp_removed / max(held_fp, 1)
    return dict(D3_loso_sensitivity_retained=float(sens_ret),
                D3_loso_sensitivity_loss_pp=float((1 - sens_ret) * 100),
                D3_loso_fp_removed_frac=float(fp_red),
                D3_relevance_met=bool(fp_red >= 0.20 and (1 - sens_ret) <= 0.05))


# ============================================================================
# RUN
# ============================================================================
def run(comp_dir, pernode_root, summary_dir, outdir, subjects, seed,
        lock_guard=True, n_boot=2000, n_perm=1000):
    import pandas as pd
    import evaluation_protocol as E
    import szcore_eval as SZ
    import cpd_pipeline_v14 as V14
    import ensemble_recipe as ER

    guard_component_dir(comp_dir)
    os.makedirs(outdir, exist_ok=True)
    win_sec = E.WIN_SEC
    print(SCRIPT_VERSION)
    print(f"weight={ER.ENS_WEIGHTS}  mag{MIN_MAG_PCT}/pen{PEN_MULT}  seed={seed}\n")

    rows, diag = [], []
    TP = FP = N_REF = 0
    inter_h = 0.0
    for subj in subjects:
        r, sc, d = extract_subject(subj, comp_dir, pernode_root, summary_dir,
                                   E, SZ, V14, ER, win_sec, seed=seed)
        rows.extend(r); diag.append(d)
        TP += sc["tp"]; FP += sc["fp"]; N_REF += sc["n_ref"]
        inter_h += d["n_inter_h"]

    sens = TP / max(N_REF, 1)
    fpd = FP / max(inter_h, 1e-9) * 24.0
    print(f"\nPOOLED (locked-path reproduction): TP={TP}/{N_REF} FP={FP} "
          f"sens={sens:.3f} FP/day={fpd:.2f}")
    if lock_guard:
        bad = (TP != LOCK["tp"] or FP != LOCK["fp"]
               or abs(sens - LOCK["sensitivity"]) > 0.002
               or abs(fpd - LOCK["fp_per_day"]) > 0.5)
        if bad:
            raise RuntimeError(
                "LOCK GUARD FAILED: this harness does not reproduce the locked "
                f"balanced operating point.\n  got   TP={TP} FP={FP} "
                f"sens={sens:.3f} FP/day={fpd:.2f}\n  locked TP={LOCK['tp']} "
                f"FP={LOCK['fp']} sens={LOCK['sensitivity']} "
                f"FP/day={LOCK['fp_per_day']}\nDo NOT interpret any Test D number "
                "until this matches (operating rule #5).")
        print("LOCK GUARD PASSED - harness reproduces the locked numbers.\n")

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(outdir, "tpfp_events.csv"), index=False)
    pd.DataFrame(diag).to_csv(os.path.join(outdir, "tpfp_diagnostics.csv"), index=False)

    rng = np.random.default_rng(seed)
    res = analyse(df, outdir, rng, n_boot=n_boot, n_perm=n_perm)

    print("--- D2 (DECISIVE, read first) ---")
    print(f"  AUROC nuisance(score+duration) = {res['D2_auroc_nuisance(score+duration)']:.4f}")
    print(f"  AUROC +concentration           = {res['D2_auroc_full(+concentration)']:.4f}")
    print(f"  incremental                    = {res['D2_incremental_auroc']:+.4f} "
          f"CI {res['D2_incremental_auroc_ci']}")
    print(f"  permutation p                  = {res['D2_permutation_p']:.4f}")
    print(f"  D2 PASS = {res['D2_pass']}")
    print("--- D1 ---")
    print(f"  AUROC {res['D1_auroc_mean']:.4f} CI {res['D1_auroc_ci']} | "
          f"AUPRC {res['D1_auprc_mean']:.4f} CI {res['D1_auprc_ci']} | "
          f"PASS = {res['D1_pass']}")
    print("--- D4 ---")
    print(f"  {res['D4_group_gini_median']}")
    print(f"  AUROC TP vs near-miss = {res['D4_auroc_TP_vs_nearmiss']}, "
          f"TP vs remote = {res['D4_auroc_TP_vs_remote']}")
    print("--- D3 ---")
    print(f"  {res['D3_status']}")

    res["_provenance"] = dict(
        script=SCRIPT_VERSION, run_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        weight=list(ER.ENS_WEIGHTS), operating_point=f"mag{MIN_MAG_PCT}/pen{PEN_MULT}",
        seed=seed, n_boot=n_boot, n_perm=n_perm, comp_dir=os.path.abspath(comp_dir),
        pernode_root=os.path.abspath(pernode_root), lock_guard=lock_guard,
        pooled_TP=TP, pooled_FP=FP, pooled_sensitivity=sens, pooled_fp_per_day=fpd,
        event_unit=("locked eval path: detect_changepoints -> cps_to_events "
                    "(buffer don't-care) -> merge 90s -> split 300s; see module "
                    "docstring for the §4 specification conflict and its resolution"),
        python=platform.python_version(), numpy=np.__version__)
    with open(os.path.join(outdir, "tpfp_summary.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, default=str)

    make_figure(df, outdir)
    print(f"\nOutputs -> {os.path.abspath(outdir)}")
    return df, res


def make_figure(df, outdir):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    order = ["TP", "near_miss_FP", "remote_FP"]
    data = [df[df.fp_class == g]["gini"].values for g in order]
    lbl = [g for g, d in zip(order, data) if d.size]
    try:
        axes[0].boxplot([d for d in data if d.size], showfliers=False, tick_labels=lbl)
    except TypeError:
        axes[0].boxplot([d for d in data if d.size], showfliers=False, labels=lbl)
    axes[0].set_ylabel("Gini of |z|"); axes[0].set_title("D4 - concentration by event class")
    axes[0].grid(axis="y", alpha=.3)
    axes[1].scatter(df.duration_s, df.gini, c=df.label, cmap="coolwarm", s=14, alpha=.6)
    axes[1].set_xscale("log"); axes[1].set_xlabel("event duration (s, log)")
    axes[1].set_ylabel("Gini of |z|")
    axes[1].set_title("D2 confound - duration vs concentration (red = TP)")
    axes[1].grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "tpfp_concentration.png"), dpi=160)
    plt.close(fig)


# ============================================================================
# SELF-TEST
# ============================================================================
def selftest():
    import pandas as pd
    print("=== SELF-TEST (synthetic) ===")
    ok = True

    # merge/split
    ev = merge_and_split([(0, 4), (40, 44), (400, 404)])
    print(f" merge: {ev} (expect 2 events)"); ok &= len(ev) == 2
    ev2 = merge_and_split([(t, t + 4) for t in range(0, 800, 40)])
    print(f" split at 300s: {len(ev2)} events, max dur "
          f"{max(b-a for a,b in ev2)} (expect <=300)")
    ok &= max(b - a for a, b in ev2) <= MAX_EVENT_S

    # labelling
    lab, nm = label_events([(100, 110), (500, 510), (100000, 100010)], [(90, 200)])
    print(f" labels={lab.tolist()} near_miss={nm.tolist()} "
          f"(expect [1,0,0] / [F,T,F])")
    ok &= lab.tolist() == [1, 0, 0] and nm.tolist() == [False, True, False]

    # comp-dir guard
    os.makedirs("/home/claude/fake2/history_superseded/x", exist_ok=True)
    try:
        guard_component_dir("/home/claude/fake2/history_superseded/x"); ok = False
        print(" GUARD quarantine: FAILED TO FIRE")
    except RuntimeError:
        print(" GUARD quarantine fired correctly")
    os.makedirs("/home/claude/fake2/comp", exist_ok=True)
    np.save("/home/claude/fake2/comp/chb03_ens_inter.npy", np.zeros(3))
    try:
        guard_component_dir("/home/claude/fake2/comp"); ok = False
        print(" GUARD stray-ens-cache: FAILED TO FIRE")
    except RuntimeError:
        print(" GUARD stray-ens-cache fired correctly")
    os.remove("/home/claude/fake2/comp/chb03_ens_inter.npy")

    # end-to-end on a synthetic 2-subject cohort
    root = "/home/claude/fake2"
    cdir, pdir, sdir = f"{root}/comp", f"{root}/pernode", f"{root}/summary"
    for d in (cdir, pdir, sdir):
        os.makedirs(d, exist_ok=True)
    rng = np.random.default_rng(1)
    for subj in ["chbXX", "chbYY"]:
        n_i, n_c = 4000, 120
        for k, amp in [("zrecon", 4.0), ("ztemp", 3.0), ("zgamma", 5.0)]:
            np.save(f"{cdir}/{k}_{subj}_inter.npy", rng.normal(0, 1, n_i))
            np.save(f"{cdir}/{k}_{subj}_ictal.npy", rng.normal(amp, 1, n_c))
        np.save(f"{pdir}/{subj}_interictal_pernode.npy", rng.normal(0, 1, (n_i, N_CH)))
        pn = rng.normal(0, 1, (n_c, N_CH)); pn[:, [4, 5]] += 5.0
        np.save(f"{pdir}/{subj}_ictal_pernode.npy", pn)
        with open(f"{sdir}/{subj}-summary.txt", "w") as f:
            for h, (a, b) in enumerate([(600, 840), (1200, 1440)]):
                f.write(f"File Name: {subj}_{h}.edf\nFile Start Time: 0{h}:00:00\n"
                        f"File End Time: 0{h+1}:00:00\nNumber of Seizures in File: 1\n"
                        f"Seizure Start Time: {a} seconds\n"
                        f"Seizure End Time: {b} seconds\n\n")
    df, res = run(cdir, pdir, sdir, f"{root}/out", ["chbXX", "chbYY"], seed=0,
                  lock_guard=False, n_boot=200, n_perm=50)
    ok &= len(df) > 0 and {"gini", "label", "duration_s"} <= set(df.columns)
    print(f" end-to-end: {len(df)} events, "
          f"{int(df.label.sum())} TP / {int((1-df.label).sum())} FP")
    ok &= df.n_windows_resolved.min() >= 1
    print(f" no event has 0 resolved windows: OK")
    for fn in ["tpfp_events.csv", "tpfp_summary.json", "tpfp_diagnostics.csv",
               "tpfp_concentration.png"]:
        e = os.path.exists(f"{root}/out/{fn}"); ok &= e
        print(f" output {fn}: {'OK' if e else 'MISSING'}")
    print(f" D3 gating honoured: {res['D3_status'][:60]}")

    # D3 is gated off above, so exercise the LOSO path directly on a crafted frame
    r3 = np.random.default_rng(3)
    n = 40
    fr = pd.DataFrame(dict(
        subject=np.repeat([f"s{i}" for i in range(4)], n),
        label=np.tile(np.r_[np.ones(8), np.zeros(n - 8)].astype(int), 4)))
    fr["gini"] = np.where(fr.label == 1, r3.normal(.75, .03, len(fr)),
                          r3.normal(.35, .05, len(fr)))
    out3 = loso_operating_curve(fr, f"{root}/out")
    print(f" D3 LOSO unit test: sens_retained={out3['D3_loso_sensitivity_retained']:.3f} "
          f"fp_removed={out3['D3_loso_fp_removed_frac']:.3f} "
          f"relevance_met={out3['D3_relevance_met']} (expect near 1.0 / high / True)")
    ok &= out3["D3_loso_sensitivity_retained"] > 0.9 and out3["D3_relevance_met"]
    ok &= os.path.exists(f"{root}/out/tpfp_loso_operating_point.csv")

    print("\n=== SELF-TEST", "PASSED" if ok else "FAILED", "===")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="Test D - TP-vs-FP triage (pre-reg v3.1)")
    ap.add_argument("--comp_dir", default=None)
    ap.add_argument("--pernode_root", default=None)
    ap.add_argument("--summary_dir", default=None)
    ap.add_argument("--outdir", default="results/attribution_v3")
    ap.add_argument("--subjects", nargs="+",
                    default=["chb03", "chb06", "chb13", "chb14",
                             "chb15", "chb16", "chb17", "chb18"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n_boot", type=int, default=2000)
    ap.add_argument("--n_perm", type=int, default=1000)
    ap.add_argument("--skip_lock_guard", action="store_true",
                    help="ONLY for synthetic testing; never use on real data")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not (a.comp_dir and a.pernode_root and a.summary_dir):
        ap.error("--comp_dir, --pernode_root and --summary_dir are required")
    run(a.comp_dir, a.pernode_root, a.summary_dir, a.outdir, a.subjects, a.seed,
        lock_guard=not a.skip_lock_guard, n_boot=a.n_boot, n_perm=a.n_perm)


if __name__ == "__main__":
    main()