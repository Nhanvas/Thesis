#!/usr/bin/env python
"""
lab_protocol_eval.py -- docs/CC_PROMPT_LAB_PROTOCOL.md: laboratory evaluation protocol on
the real continuous timeline.

Pre-registered 2026-10-01 before any result of this protocol exists (docs/CC_PROMPT_LAB_
PROTOCOL.md was committed alone, before this script ran). Separates the laboratory
evaluation of the MODEL (this file) from the deployment evaluation of the APPLICATION
(src/app_val_op.py). Uses ONLY src/continuous_eval.py's own cache
(results/continuous_eval/cache/{mask,scores}/) -- no EDF is re-read, no model is run; this
file is pure numpy/PELT/SzCORE arithmetic on arrays already on disk.

Protocol (both conventions declared up front, see docs/CC_PROMPT_LAB_PROTOCOL.md for the
full rationale):

  1. Detector side: a window is masked (±5 SD artifact rule OR the signal-loss rule -- same
     cached is_artifact/is_signal_loss flags src/continuous_eval.py's own Scope T mask
     already carries) and forced to fused score 0 before smoothing, ICTAL INCLUDED -- this
     differs from the committed Scope T cache, which only zeros is_signal_loss (Amendment
     A2); is_artifact is excluded from Scope T's FIT but its raw score is still on the
     cached timeline. Scope T's own fits are unchanged: the same background mask
     (~ictal & ~buffer & ~artifact & ~signal_loss) is reused as the PELT/magnitude
     background (`fit_mask` below), never recomputed.
  2. Evaluation side: the existing post-seizure buffer (is_buffer, 4h, same-file, from
     preprocessing.build_buffer_mask -- already baked into the cached mask) is a don't-care
     region. A hypothesis event whose ONSET window falls in it and that does not overlap an
     annotated seizure within SzCORE tolerance is dropped entirely (neither TP nor FP);
     overlap uses szcore_eval.per_interval_match (the library's own match assignment, reused
     rather than reimplemented).
  3. FA/day denominator = recorded time - seizure time - don't-care time - masked time, a
     DISJOINT per-window partition in that priority order (ictal first, then masked, then
     don't-care) so the three subtracted components never double-count a window -- see
     load_subject_data's own comment.
  4. Scoring otherwise exactly SzCORE via timescoring (szcore_eval.score_szcore, SZ_PARAM),
     files already concatenated in file-name order by src/continuous_eval.py's own cache,
     change points from the cached Scope T (Amendment A2) fused scores via cpd_pipeline_v14
     (same locked CPD code every other eval script in this repo uses).

Steps A-D are exactly docs/CC_PROMPT_LAB_PROTOCOL.md's own list:
  A. Validation-only grid (8 mag_pct x 6 pen_mult x 2 merge_s), Amendment A8 selection
     (max pooled sensitivity s.t. pooled FA/day <= 25, ties lower FA/day then lower penalty)
     plus the sensitivity==precision point for information.
  B. Test scored ONCE at the A8 point -- no other test point is ever computed.
  C. Window-level macro AUROC on test under the same conventions, beside the all-windows
     reference (recomputed fresh from cache here, not hardcoded -- lands at ~0.621, matching
     results/continuous_eval/stepC_tables.json's own window_auroc_macro).
  D. Cost of masking on test: seizures with >=1 masked window, and seizures entirely masked.

Usage
-----
  python src/lab_protocol_eval.py
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import ruptures as rpt
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src",):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import cpd_pipeline_v14 as V14                                   # noqa: E402 -- read-only, locked
from szcore_eval import SZ_PARAM, score_szcore, per_interval_match  # noqa: E402 -- reused, not retyped

VAL_SUBJS = ["chb10", "chb11", "chb22"]
TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
ALL_SUBJS = VAL_SUBJS + TEST_SUBJS

MAG_PCTS = [40.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0]
PEN_MULTS = [0.3, 0.5, 1.0, 2.0, 5.0, 10.0]
MERGE_GAPS = [90, 300]
WIN_SEC = V14.WIN_SEC_DEFAULT  # 4

CONT_EVAL_CACHE = ROOT / "results" / "continuous_eval" / "cache"
OUT_DIR = ROOT / "results" / "lab_protocol"

ALL_WINDOWS_TEST_AUROC_DOC_REF = 0.621  # docs/CC_PROMPT_LAB_PROTOCOL.md Step C's own citation


class LabProtocolError(Exception):
    """Fail-fast: the message is meant to be read directly."""


def log(tag, msg):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    line = f"[{tag}] {time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(OUT_DIR / "run.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ---------------------------------------------------------------------------------------
# Cached mask/score loading (src/continuous_eval.py's own cache -- read-only here)
# ---------------------------------------------------------------------------------------
def mask_cache_path(subj):
    return CONT_EVAL_CACHE / "mask" / f"{subj}.npz"


def scores_cache_path(subj):
    return CONT_EVAL_CACHE / "scores" / f"T_{subj}.npy"


def load_subject_data(subj):
    mpath, spath = mask_cache_path(subj), scores_cache_path(subj)
    if not mpath.exists() or not spath.exists():
        raise LabProtocolError(
            f"{subj}: missing cached mask ({mpath}) or Scope T score ({spath}) -- "
            f"src/continuous_eval.py's score stage must have already run; this script "
            f"never recomputes them (no EDF re-read, no model run)."
        )
    z = np.load(mpath, allow_pickle=True)
    is_ictal = z["is_ictal"]; is_buffer = z["is_buffer"]; is_artifact = z["is_artifact"]
    is_signal_loss = z["is_signal_loss"]
    sz_ranges = [tuple(int(v) for v in x) for x in z["sz_ranges"]]

    ens_T = np.load(spath).astype(np.float64)
    if len(ens_T) != len(is_ictal):
        raise LabProtocolError(
            f"{subj}: score length ({len(ens_T)}) != mask length ({len(is_ictal)}) -- "
            f"cache is stale/inconsistent."
        )

    masked = is_artifact | is_signal_loss
    # Step 1: masked windows forced to fused score 0 (the robust-z median), BEFORE
    # smoothing -- ictal included. The committed Scope T array only zeros is_signal_loss
    # (Amendment A2); is_artifact is excluded from Scope T's own FIT but its raw score is
    # still present on that cached timeline, so this additionally zeros it here. Idempotent
    # on the windows already zeroed by Amendment A2.
    score_masked = ens_T.copy()
    score_masked[masked] = 0.0

    # Scope T's own background mask, UNCHANGED (src/continuous_eval.py's background_mask &
    # ~is_signal_loss) -- "Scope T fits are unchanged: their background mask already
    # excludes these windows." Reused as the PELT/magnitude background below.
    fit_mask = (~is_ictal) & (~is_buffer) & (~is_artifact) & (~is_signal_loss)

    n_windows = len(ens_T)
    total_dur_s = float(n_windows * WIN_SEC)
    seizure_s = float(int(is_ictal.sum()) * WIN_SEC)
    # Disjoint priority for the FA/day denominator's reported breakdown (Step 3): ictal
    # first (never excluded elsewhere), then masked (detector-side, applies regardless of
    # context), then don't-care (evaluation-side, post-ictal only) -- a window that is both
    # masked and in the post-ictal buffer is counted under "masked", not "don't-care", so
    # the three subtracted components never double-count the same window.
    masked_s = float(int((masked & (~is_ictal)).sum()) * WIN_SEC)
    dontcare_s = float(int((is_buffer & (~is_ictal) & (~masked)).sum()) * WIN_SEC)
    denom_s = total_dur_s - seizure_s - masked_s - dontcare_s
    n_inter_h = denom_s / 3600.0

    ref_iv = [(s * WIN_SEC, e * WIN_SEC) for (s, e) in sz_ranges]

    return dict(subject=subj, ens_T_raw=ens_T, score_masked=score_masked, fit_mask=fit_mask,
               is_ictal=is_ictal, is_buffer=is_buffer, masked=masked, sz_ranges=sz_ranges,
               ref_iv=ref_iv, n_windows=n_windows, total_dur_s=total_dur_s,
               seizure_s=seizure_s, masked_s=masked_s, dontcare_s=dontcare_s,
               n_inter_h=n_inter_h)


# ---------------------------------------------------------------------------------------
# Event grid: PELT once per penalty, magnitude + merge post-hoc (same pattern as
# src/continuous_eval.py's grid_for_subject / src/app_val_op.py's grid_for_subject)
# ---------------------------------------------------------------------------------------
def _mag_threshold(mags, inter_mask, pct):
    if inter_mask is not None and np.any(inter_mask):
        bg = [m for c, m in mags.items() if inter_mask[c]]
    else:
        bg = list(mags.values())
    return float(np.percentile(bg, pct)) if bg else 0.0


def cps_to_merged_events(cps, win_sec, merge_s):
    """Byte-identical to cpd_pipeline_v14.detect_events's own merge loop -- reproduced here
    (not imported) so merge_s can be applied post-hoc without a fresh PELT fit;
    verify_fast_grid below checks this against detect_events directly."""
    times = sorted(c * win_sec for c in cps)
    events = []
    for t in times:
        if events and t - events[-1][1] <= merge_s:
            events[-1] = (events[-1][0], t + win_sec)
        else:
            events.append((t, t + win_sec))
    return events


def grid_for_subject(score, inter_mask, mag_pcts, pen_mults, merge_gaps):
    smoothed = V14._smooth(np.asarray(score, dtype=float))
    n = len(smoothed)
    out = []
    if n < 10:
        for pm in pen_mults:
            for mag in mag_pcts:
                for ms in merge_gaps:
                    out.append(dict(mag_pct=mag, pen_mult=pm, merge_s=ms, hyp_events=[]))
        return out
    s2 = V14._robust_variance(smoothed, inter_mask)
    algo = rpt.Pelt(model="l2", min_size=V14.PELT_MIN_SIZE, jump=V14.PELT_JUMP).fit(
        smoothed.reshape(-1, 1))
    for pm in pen_mults:
        beta = pm * s2 * np.log(n)
        cps_pen = [c for c in algo.predict(pen=beta) if 0 < c < n]
        mags = {c: V14._cp_magnitude(smoothed, c, 15) for c in cps_pen}
        for mag in mag_pcts:
            thr = _mag_threshold(mags, inter_mask, mag)
            cps = [c for c in cps_pen if mags[c] >= thr]
            for ms in merge_gaps:
                out.append(dict(mag_pct=mag, pen_mult=pm, merge_s=ms,
                                hyp_events=cps_to_merged_events(cps, WIN_SEC, ms)))
    return out


def verify_fast_grid(score, inter_mask, subj):
    smoothed = V14._smooth(np.asarray(score, dtype=float))
    n = len(smoothed)
    s2 = V14._robust_variance(smoothed, inter_mask)
    algo = rpt.Pelt(model="l2", min_size=V14.PELT_MIN_SIZE, jump=V14.PELT_JUMP).fit(
        smoothed.reshape(-1, 1))
    for pen_mult in (0.5, 2.0):
        beta = pen_mult * s2 * np.log(n)
        cps_pen = [c for c in algo.predict(pen=beta) if 0 < c < n]
        mags = {c: V14._cp_magnitude(smoothed, c, 15) for c in cps_pen}
        for mag in (50.0, 65.0):
            thr = _mag_threshold(mags, inter_mask, mag)
            cps_fast = [c for c in cps_pen if mags[c] >= thr]
            for merge_s in (90, 300):
                ev_fast = cps_to_merged_events(cps_fast, WIN_SEC, merge_s)
                ev_direct = V14.detect_events(score, pen_mult, min_mag_pct=mag, local_win=15,
                                              win_sec=WIN_SEC, inter_mask=inter_mask,
                                              merge_s=merge_s)
                if ev_fast != ev_direct:
                    raise LabProtocolError(
                        f"fast-grid verification FAILED on {subj}: pen={pen_mult} mag={mag} "
                        f"merge={merge_s}: fast={len(ev_fast)} direct={len(ev_direct)} events."
                    )
    log("GRID", f"verify_fast_grid PASS on {subj} (4 cells x 2 merge_s, byte-identical to a "
               f"direct cpd_pipeline_v14.detect_events call)")


# ---------------------------------------------------------------------------------------
# Don't-care filtering + SzCORE scoring (Step 2 / Step 4)
# ---------------------------------------------------------------------------------------
def per_seizure_latencies(ref_iv, hyp_iv, tol_start, tol_end):
    lats = []
    for (r0, r1) in ref_iv:
        cands = [(h0, h1) for (h0, h1) in hyp_iv if h1 >= r0 - tol_start and h0 <= r1 + tol_end]
        if cands:
            h0 = min(cands, key=lambda h: abs(h[0] - r0))[0]
            lats.append(h0 - r0)
    return lats


def apply_dontcare_and_score(data, hyp_events):
    """Step 2: drop a hyp event entirely (not TP, not FP) when its onset window is in the
    post-ictal don't-care buffer AND it does not overlap any seizure within SzCORE
    tolerance (per_interval_match -- the library's own match assignment, reused). Kept
    events are scored exactly as SzCORE (score_szcore, same SZ_PARAM)."""
    matches = per_interval_match(data["ref_iv"], hyp_events, data["total_dur_s"]) if hyp_events else []
    kept, n_dropped = [], 0
    for ev, m in zip(hyp_events, matches):
        onset_win = int(round(ev[0] / WIN_SEC))
        if data["is_buffer"][onset_win] and not m["matched"]:
            n_dropped += 1
            continue
        kept.append(ev)
    sc = score_szcore(data["ref_iv"], kept, data["total_dur_s"], data["n_inter_h"])
    lats = per_seizure_latencies(data["ref_iv"], kept, SZ_PARAM.toleranceStart, SZ_PARAM.toleranceEnd)
    return dict(tp=sc["tp"], fp=sc["fp"], n_ref=sc["n_ref"], sensitivity=sc["sensitivity"],
               precision=sc["precision"], f1=sc["f1"], fp_per_day=sc["fp_per_day"],
               n_inter_h=data["n_inter_h"], latencies=lats, n_dropped_dontcare=n_dropped,
               total_dur_s=data["total_dur_s"], seizure_s=data["seizure_s"],
               masked_s=data["masked_s"], dontcare_s=data["dontcare_s"])


def pool_cells(cells):
    tp = sum(c["tp"] for c in cells); fp = sum(c["fp"] for c in cells)
    n_ref = sum(c["n_ref"] for c in cells); h = sum(c["n_inter_h"] for c in cells)
    sens = tp / n_ref if n_ref else float("nan")
    prec = tp / (tp + fp) if (tp + fp) else float("nan")
    f1 = (2 * prec * sens / (prec + sens)
         if (prec + sens) and prec == prec and sens == sens else float("nan"))
    fa = fp / h * 24.0 if h else float("nan")
    lats = [l for c in cells for l in c["latencies"]]
    return dict(tp=tp, fp=fp, n_ref=n_ref, sensitivity=sens, precision=prec, f1=f1,
               fp_per_day=fa, n_inter_h=h, latencies=lats,
               n_dropped_dontcare=sum(c["n_dropped_dontcare"] for c in cells),
               total_dur_s=sum(c["total_dur_s"] for c in cells),
               seizure_s=sum(c["seizure_s"] for c in cells),
               masked_s=sum(c["masked_s"] for c in cells),
               dontcare_s=sum(c["dontcare_s"] for c in cells))


def grid_row(mag, pen, ms, subject, sc):
    lats = sc["latencies"]
    return dict(mag_pct=mag, pen_mult=pen, merge_s=ms, subject=subject,
               seizures=sc["n_ref"], detected=sc["tp"], false_alarms=sc["fp"],
               sensitivity=sc["sensitivity"], precision=sc["precision"], f1=sc["f1"],
               fp_per_day=sc["fp_per_day"],
               median_latency_s=float(np.median(lats)) if lats else float("nan"),
               n_latency=len(lats),
               recorded_hours=round(sc["total_dur_s"] / 3600.0, 4),
               seizure_hours=round(sc["seizure_s"] / 3600.0, 4),
               dontcare_hours=round(sc["dontcare_s"] / 3600.0, 4),
               masked_hours=round(sc["masked_s"] / 3600.0, 4),
               denom_hours=round(sc["n_inter_h"], 4),
               n_dropped_dontcare=sc["n_dropped_dontcare"])


# ---------------------------------------------------------------------------------------
# Step A -- validation grid + selection
# ---------------------------------------------------------------------------------------
def select_operating_points(grid_df):
    pooled = grid_df[grid_df.subject == "POOLED"].copy()

    # Amendment A8 rule: maximize pooled validation sensitivity s.t. pooled FA/day <= 25;
    # ties by lower FA/day, then lower penalty.
    ok = pooled[pooled.fp_per_day <= 25.0]
    if len(ok) == 0:
        raise LabProtocolError("Amendment A8 rule: no grid cell has pooled validation FA/day <= 25.")
    ok = ok.sort_values(by=["sensitivity", "fp_per_day", "pen_mult"], ascending=[False, True, True])
    a8_row = ok.iloc[0].to_dict()

    # Information only: sensitivity and precision closest to equal.
    pooled["abs_gap"] = (pooled["sensitivity"] - pooled["precision"]).abs()
    info_row = pooled.loc[pooled["abs_gap"].idxmin()].to_dict()
    return a8_row, info_row


def run_step_a(all_data):
    # Verifies the fast-grid ALGORITHM (PELT once per penalty, magnitude/merge post-hoc)
    # against a direct cpd_pipeline_v14.detect_events call -- a code-correctness check, not
    # a per-subject data check, so one validation subject is enough (each direct call is a
    # full independent PELT fit, ~150s on a 45k-window series; redundant per subject).
    verify_fast_grid(all_data[VAL_SUBJS[0]]["score_masked"], all_data[VAL_SUBJS[0]]["fit_mask"],
                     VAL_SUBJS[0])

    per_subj_grid = {}
    for s in VAL_SUBJS:
        t0 = time.time()
        per_subj_grid[s] = grid_for_subject(all_data[s]["score_masked"], all_data[s]["fit_mask"],
                                            MAG_PCTS, PEN_MULTS, MERGE_GAPS)
        log("A", f"{s}: 96-cell grid built in {time.time() - t0:.1f}s")

    n_cells = len(per_subj_grid[VAL_SUBJS[0]])
    rows = []
    t0 = time.time()
    for i in range(n_cells):
        ref = per_subj_grid[VAL_SUBJS[0]][i]
        mag, pen, ms = ref["mag_pct"], ref["pen_mult"], ref["merge_s"]
        cells = []
        for s in VAL_SUBJS:
            cell = per_subj_grid[s][i]
            assert (cell["mag_pct"], cell["pen_mult"], cell["merge_s"]) == (mag, pen, ms)
            sc = apply_dontcare_and_score(all_data[s], cell["hyp_events"])
            cells.append(sc)
            rows.append(grid_row(mag, pen, ms, s, sc))
        rows.append(grid_row(mag, pen, ms, "POOLED", pool_cells(cells)))
    log("A", f"scored {n_cells} grid cells x {len(VAL_SUBJS)} subject(s) in {time.time() - t0:.1f}s")

    grid_df = pd.DataFrame(rows)
    grid_df.to_csv(OUT_DIR / "stepA_grid.csv", index=False)
    log("A", f"stepA_grid.csv written ({len(grid_df)} rows)")

    a8_row, info_row = select_operating_points(grid_df)
    log("A", f"Amendment A8: mag={a8_row['mag_pct']:g} pen={a8_row['pen_mult']:g} "
             f"merge={a8_row['merge_s']:g} sens={a8_row['sensitivity']:.3f} "
             f"FA/day={a8_row['fp_per_day']:.2f}")
    log("A", f"Info point (sens==prec): mag={info_row['mag_pct']:g} pen={info_row['pen_mult']:g} "
             f"merge={info_row['merge_s']:g} sens={info_row['sensitivity']:.3f} "
             f"prec={info_row['precision']:.3f}")
    return grid_df, a8_row, info_row


# ---------------------------------------------------------------------------------------
# Step B -- test, scored ONCE at the A8 point
# ---------------------------------------------------------------------------------------
def run_step_b(all_data, a8_row):
    mag, pen, ms = a8_row["mag_pct"], a8_row["pen_mult"], a8_row["merge_s"]
    cells = {}
    t0 = time.time()
    for s in TEST_SUBJS:
        d = all_data[s]
        ev = V14.detect_events(d["score_masked"], pen, min_mag_pct=mag, local_win=15,
                               win_sec=WIN_SEC, inter_mask=d["fit_mask"], merge_s=ms)
        cells[s] = apply_dontcare_and_score(d, ev)
    log("B", f"scored {len(TEST_SUBJS)} test subjects at the single A8 point "
             f"(mag={mag:g} pen={pen:g} merge={ms:g}) in {time.time() - t0:.1f}s. "
             f"No other test point is computed.")

    rows = [grid_row(mag, pen, ms, s, cells[s]) for s in TEST_SUBJS]
    rows.append(grid_row(mag, pen, ms, "POOLED", pool_cells(list(cells.values()))))
    rows.append(grid_row(mag, pen, ms, "POOLED_no_chb17",
                         pool_cells([cells[s] for s in TEST_SUBJS if s != "chb17"])))
    stepB_df = pd.DataFrame(rows)
    stepB_df.to_csv(OUT_DIR / "stepB.csv", index=False)
    pooled = stepB_df[stepB_df.subject == "POOLED"].iloc[0]
    log("B", f"pooled: sens={pooled['sensitivity']:.3f} prec={pooled['precision']:.3f} "
             f"FA/day={pooled['fp_per_day']:.2f} median_latency_s={pooled['median_latency_s']:.1f}")
    return stepB_df


# ---------------------------------------------------------------------------------------
# Step C -- window-level macro AUROC on test
# ---------------------------------------------------------------------------------------
def run_step_c(all_data):
    aurocs_new, aurocs_all = {}, {}
    for s in TEST_SUBJS:
        d = all_data[s]
        subset = d["is_ictal"] | d["fit_mask"]
        y = d["is_ictal"][subset].astype(int)
        sc = d["score_masked"][subset]
        aurocs_new[s] = float(roc_auc_score(y, sc)) if 0 < y.sum() < len(y) else float("nan")

        y_all = d["is_ictal"].astype(int)
        aurocs_all[s] = (float(roc_auc_score(y_all, d["ens_T_raw"]))
                         if 0 < y_all.sum() < len(y_all) else float("nan"))
    macro_new = float(np.nanmean(list(aurocs_new.values())))
    macro_all = float(np.nanmean(list(aurocs_all.values())))
    log("C", f"window-level macro AUROC (test): lab-protocol-conventions={macro_new:.4f}, "
             f"all-windows={macro_all:.4f} (docs cite {ALL_WINDOWS_TEST_AUROC_DOC_REF:g})")
    df = pd.DataFrame([
        dict(subject=s, auroc_lab_protocol=aurocs_new[s], auroc_all_windows=aurocs_all[s])
        for s in TEST_SUBJS
    ] + [dict(subject="MACRO", auroc_lab_protocol=macro_new, auroc_all_windows=macro_all)])
    df.to_csv(OUT_DIR / "stepC_auroc.csv", index=False)
    return dict(macro_new=macro_new, macro_all=macro_all, per_subject_new=aurocs_new,
               per_subject_all=aurocs_all)


# ---------------------------------------------------------------------------------------
# Step D -- cost of masking
# ---------------------------------------------------------------------------------------
def run_step_d(all_data):
    rows = []
    tot_seiz = tot_any = tot_all = 0
    for s in TEST_SUBJS:
        d = all_data[s]
        masked = d["masked"]
        n_seiz = len(d["sz_ranges"])
        n_any = n_all = 0
        for (ss, se) in d["sz_ranges"]:
            seg = masked[ss:se]
            if seg.any():
                n_any += 1
            if seg.all():
                n_all += 1
        rows.append(dict(subject=s, n_seizures=n_seiz, n_any_masked_window=n_any,
                         n_entirely_masked=n_all))
        tot_seiz += n_seiz; tot_any += n_any; tot_all += n_all
    rows.append(dict(subject="POOLED", n_seizures=tot_seiz, n_any_masked_window=tot_any,
                     n_entirely_masked=tot_all))
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "masking_cost.csv", index=False)
    log("D", f"masking cost (test): {tot_any}/{tot_seiz} seizures have >=1 masked window, "
             f"{tot_all}/{tot_seiz} entirely masked")
    return df


def write_denominators_csv(all_data):
    rows = [dict(subject=s, recorded_hours=round(all_data[s]["total_dur_s"] / 3600.0, 4),
                seizure_hours=round(all_data[s]["seizure_s"] / 3600.0, 4),
                dontcare_hours=round(all_data[s]["dontcare_s"] / 3600.0, 4),
                masked_hours=round(all_data[s]["masked_s"] / 3600.0, 4),
                denom_hours=round(all_data[s]["n_inter_h"], 4))
            for s in ALL_SUBJS]
    pd.DataFrame(rows).to_csv(OUT_DIR / "denominators.csv", index=False)


# ---------------------------------------------------------------------------------------
# SUMMARY.md
# ---------------------------------------------------------------------------------------
def write_readme():
    (OUT_DIR / "README.md").write_text(
        "# results/lab_protocol/ -- producing script\n\n"
        "`stepA_grid.csv`, `stepB.csv`, `stepC_auroc.csv`, `masking_cost.csv`, "
        "`denominators.csv`, `SUMMARY.md`, `run.log` <- `src/lab_protocol_eval.py` "
        "(docs/CC_PROMPT_LAB_PROTOCOL.md). Reads only results/continuous_eval/cache/ "
        "(mask + Scope T scores) -- never writes there, never re-reads an EDF, never runs "
        "the model.\n",
        encoding="utf-8")


def build_summary_md(grid_df, a8_row, info_row, stepB_df, stepC, stepD_df, elapsed_s):
    lines = ["# Laboratory evaluation protocol -- SUMMARY", ""]
    lines.append(
        "docs/CC_PROMPT_LAB_PROTOCOL.md (pre-registered 2026-10-01, committed alone before "
        "this ran). Real continuous timeline, no reconstruction, no resampling; two "
        "declared conventions (detector-side masking, evaluation-side post-ictal "
        "don't-care) on top of the cached Scope T (Amendment A2) fused scores -- separate "
        "from, and never merged with, the application's deployment evaluation "
        "(src/app_val_op.py)."
    )
    lines.append("")
    lines.append(f"wall-clock time: {elapsed_s / 60:.1f} min")
    lines.append("")

    lines.append("## Step A -- validation grid + operating-point selection")
    lines.append("")
    lines.append(f"8 magnitude percentiles x 6 penalty multipliers x 2 merge gaps = "
                f"{len(grid_df) // 4} cells, scored pooled across {', '.join(VAL_SUBJS)} "
                f"(`stepA_grid.csv`, {len(grid_df)} rows).")
    lines.append("")
    lines.append("**Amendment A8 rule (reported result):** maximize pooled validation "
                 "sensitivity subject to pooled validation FA/day <= 25; ties by lower "
                 "FA/day, then lower penalty.")
    lines.append("")
    lines.append(f"- mag_pct = {a8_row['mag_pct']:g}, pen_mult = {a8_row['pen_mult']:g}, "
                 f"merge_s = {a8_row['merge_s']:g}")
    lines.append(f"- pooled: sensitivity={a8_row['sensitivity']:.4f} "
                 f"precision={a8_row['precision']:.4f} f1={a8_row['f1']:.4f} "
                 f"FA/day={a8_row['fp_per_day']:.2f} seizures={a8_row['seizures']} "
                 f"detected={a8_row['detected']} false_alarms={a8_row['false_alarms']}")
    lines.append("")
    lines.append("**Information only (sensitivity == precision):**")
    lines.append("")
    lines.append(f"- mag_pct = {info_row['mag_pct']:g}, pen_mult = {info_row['pen_mult']:g}, "
                 f"merge_s = {info_row['merge_s']:g}")
    lines.append(f"- pooled: sensitivity={info_row['sensitivity']:.4f} "
                 f"precision={info_row['precision']:.4f} f1={info_row['f1']:.4f} "
                 f"FA/day={info_row['fp_per_day']:.2f}")
    lines.append("")

    lines.append("## Step B -- test, scored ONCE at the Amendment A8 point")
    lines.append("")
    lines.append("No other test point is computed or reported. Nothing chosen after this "
                 "step is seen.")
    lines.append("")
    cols = ["subject", "seizures", "detected", "false_alarms", "sensitivity", "precision",
           "f1", "fp_per_day", "median_latency_s", "n_latency", "recorded_hours",
           "seizure_hours", "dontcare_hours", "masked_hours", "denom_hours"]
    lines.append("```")
    lines.append(stepB_df[cols].to_string(index=False))
    lines.append("```")
    lines.append("")

    lines.append("## Step C -- window-level macro AUROC on test")
    lines.append("")
    lines.append(f"- lab-protocol conventions (negatives = non-ictal, not masked, not "
                 f"don't-care): **{stepC['macro_new']:.4f}**")
    lines.append(f"- all-windows (no exclusions, recomputed fresh from the same cache): "
                 f"**{stepC['macro_all']:.4f}** (docs cite {ALL_WINDOWS_TEST_AUROC_DOC_REF:g})")
    lines.append("")
    lines.append("Per subject in `stepC_auroc.csv`.")
    lines.append("")

    lines.append("## Step D -- cost of masking (test)")
    lines.append("")
    pooled_d = stepD_df[stepD_df.subject == "POOLED"].iloc[0]
    lines.append(f"{pooled_d['n_any_masked_window']}/{pooled_d['n_seizures']} test seizures "
                f"have at least one masked window; {pooled_d['n_entirely_masked']}/"
                f"{pooled_d['n_seizures']} are entirely masked.")
    lines.append("")
    lines.append("```")
    lines.append(stepD_df.to_string(index=False))
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------------------
def main():
    t_start = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    log("LOAD", f"loading cached mask + Scope T scores for {len(ALL_SUBJS)} subjects "
               f"from {CONT_EVAL_CACHE} (no EDF re-read, no model run)")
    all_data = {s: load_subject_data(s) for s in ALL_SUBJS}
    write_denominators_csv(all_data)

    grid_df, a8_row, info_row = run_step_a(all_data)
    stepB_df = run_step_b(all_data, a8_row)
    stepC = run_step_c(all_data)
    stepD_df = run_step_d(all_data)

    elapsed_s = time.time() - t_start
    summary = build_summary_md(grid_df, a8_row, info_row, stepB_df, stepC, stepD_df, elapsed_s)
    (OUT_DIR / "SUMMARY.md").write_text(summary, encoding="utf-8")
    write_readme()
    log("DONE", f"SUMMARY.md written. total wall-clock: {elapsed_s / 60:.1f} min")


if __name__ == "__main__":
    main()
