#!/usr/bin/env python
"""
diag_detector_ceiling.py -- read-only diagnostic on cached continuous-timeline scores.

VALIDATION PATIENTS ONLY (chb10, chb11, chb22). Refuses any test subject.
Reads results/continuous_eval/cache/{mask,scores}; writes only results/diag_detector_ceiling/.
Selects nothing; every number is descriptive input for a later, pre-registered decision.

Q1  FP anatomy of the locked PELT detector (Scope T) at 50/2.0/90 and 75/5/300:
    for every change point -> direction (rise/fall of the smoothed score) and distance to
    the nearest file boundary (files are concatenated in file-name order);
    for every merged event not overlapping [onset-30 s, offset+60 s] of a seizure ->
    falls-only? near a file boundary? onset window flagged by the +-5 SD rule?
Q2  The same PELT change points with falling and boundary change points removed
    (a construction check, scored with the same SzCORE scorer).
Q3  Detector-independent check: a plain threshold detector on the same score,
    smoothing computed inside each file, per-patient threshold = the patient's own
    (1-p) quantile of the smoothed score (label-free), merge 90 s.
    Curve of sensitivity vs FA/day, with and without the oracle removal of windows
    flagged by the +-5 SD rule (oracle = uses the cached flag, not a deployable rule).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src", ROOT / "src" / "dataprep"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import cpd_pipeline_v14 as V14   # noqa: E402
import szcore_eval as SE         # noqa: E402

WIN = 4
VAL = ["chb10", "chb11", "chb22"]
TEST = set(SE.TEST_SUBJS)
assert not (set(VAL) & TEST), "TEST GUARD: a test subject is in the subject list"

CACHE = ROOT / "results" / "continuous_eval" / "cache"
OUT = ROOT / "results" / "diag_detector_ceiling"
OUT.mkdir(parents=True, exist_ok=True)
TOL_PRE, TOL_POST = 30, 60
NEAR_BOUNDARY_W = 15          # 60 s, the width of the locked moving average


def load(subj):
    if subj in TEST:
        raise SystemExit(f"TEST GUARD: refusing {subj}")
    z = np.load(CACHE / "mask" / f"{subj}.npz", allow_pickle=True)
    score = np.load(CACHE / "scores" / f"T_{subj}.npy").astype(float)
    m = {k: z[k] for k in ("is_ictal", "is_buffer", "is_artifact", "is_signal_loss")}
    spans = [(str(a), int(b), int(c)) for a, b, c in z["spans"]]
    szr = [(int(a), int(b)) for a, b in z["sz_ranges"]]
    if len(score) != len(m["is_ictal"]):
        raise SystemExit(f"{subj}: score length {len(score)} != mask length {len(m['is_ictal'])}")
    ref_iv = [(s * WIN, e * WIN) for s, e in szr]
    noninter_h = float((~m["is_ictal"] & ~m["is_signal_loss"]).sum()) * WIN / 3600
    return dict(subj=subj, score=score, spans=spans, ref_iv=ref_iv, n=len(score),
                noninter_h=noninter_h, **m)


def scor(d, hyp):
    s = SE.score_szcore(d["ref_iv"], hyp, d["n"] * WIN, d["noninter_h"])
    return int(s["tp"]), int(s["fp"]), int(s["n_ref"])


def pool(rows):
    tp = sum(r[0] for r in rows); fp = sum(r[1] for r in rows); nr = sum(r[2] for r in rows)
    return tp, fp, nr


def overlaps_seizure(ev, ref_iv):
    a, b = ev
    return any(b >= r0 - TOL_PRE and a <= r1 + TOL_POST for r0, r1 in ref_iv)


def merge_cps(cps, merge_s):
    """Same loop as cpd_pipeline_v14.detect_events, but keeps the member change points."""
    out = []
    for c in sorted(cps):
        t = c * WIN
        if out and t - out[-1][1] <= merge_s:
            out[-1] = (out[-1][0], t + WIN, out[-1][2] + [c])
        else:
            out.append((t, t + WIN, [c]))
    return out


# ---------------------------------------------------------------- Q1 + Q2
def q1_q2(data):
    anat, cp_rows, q2 = [], [], []
    for mag, pen, ms in [(50.0, 2.0, 90), (75.0, 5.0, 300)]:
        res_full, res_clean = [], []
        for d in data:
            inter = (~d["is_ictal"]) & (~d["is_buffer"]) & (~d["is_artifact"]) & (~d["is_signal_loss"])
            cps, sm = V14.detect_changepoints(d["score"], pen, min_mag_pct=mag, local_win=15,
                                              inter_mask=inter)
            # reproduction check against the module's own detect_events
            ev_ref = V14.detect_events(d["score"], pen, min_mag_pct=mag, local_win=15,
                                       inter_mask=inter, merge_s=ms)
            ev = merge_cps(cps, ms)
            if [(a, b) for a, b, _ in ev] != [(a, b) for a, b in ev_ref]:
                raise SystemExit(f"{d['subj']}: merge reimplementation differs from detect_events")
            bounds = np.array([s for _, s, _ in d["spans"][1:]])
            rise = {c: V14._cp_slope(sm, c, 15) > 0 for c in cps}
            nearb = {c: bool(len(bounds) and np.min(np.abs(bounds - c)) <= NEAR_BOUNDARY_W) for c in cps}
            for c in cps:
                cp_rows.append(dict(point=f"{int(mag)}_{pen}_{ms}", subject=d["subj"], cp=c,
                                    rise=rise[c], near_boundary=nearb[c],
                                    flagged=bool(d["is_artifact"][c]), ictal=bool(d["is_ictal"][c])))
            n_fp = n_fp_fall = n_fp_bound = n_fp_flag = 0
            for a, b, members in ev:
                if overlaps_seizure((a, b), d["ref_iv"]):
                    continue
                n_fp += 1
                n_fp_fall += all(not rise[c] for c in members)
                n_fp_bound += any(nearb[c] for c in members)
                n_fp_flag += bool(d["is_artifact"][members[0]])
            anat.append(dict(point=f"{int(mag)}_{pen}_{ms}", subject=d["subj"],
                             n_events=len(ev), n_fp_approx=n_fp, fp_falls_only=n_fp_fall,
                             fp_near_file_boundary=n_fp_bound, fp_onset_flagged=n_fp_flag,
                             n_file_boundaries=len(bounds)))
            res_full.append(scor(d, [(a, b) for a, b in ev_ref]))
            keep = [c for c in cps if rise[c] and not nearb[c]]
            res_clean.append(scor(d, [(a, b) for a, b, _ in merge_cps(keep, ms)]))
        for name, rows in (("locked PELT", res_full), ("rises only, no boundary CPs", res_clean)):
            tp, fp, nr = pool(rows)
            h = sum(d["noninter_h"] for d in data)
            q2.append(dict(point=f"{int(mag)}_{pen}_{ms}", variant=name, tp=tp, n_ref=nr, fp=fp,
                           sensitivity=round(tp / nr, 4), fa_per_day=round(fp / h * 24, 2)))
    return pd.DataFrame(anat), pd.DataFrame(cp_rows), pd.DataFrame(q2)


# ---------------------------------------------------------------- Q3
def smooth_per_file(score, spans, w):
    out = np.empty_like(score)
    for _, s, e in spans:
        out[s:e] = pd.Series(score[s:e]).rolling(w, min_periods=1, center=True).mean().values
    return out


def runs_to_events(above, spans, merge_s):
    ev = []
    for _, s, e in spans:                      # never let an event cross a file boundary
        a = above[s:e]
        i = 0
        while i < len(a):
            if a[i]:
                j = i
                while j < len(a) and a[j]:
                    j += 1
                ev.append(((s + i) * WIN, (s + j) * WIN))
                i = j
            else:
                i += 1
    merged = []
    for a, b in ev:
        if merged and a - merged[-1][1] <= merge_s:
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    return merged


def q3(data):
    rows = []
    for oracle in (False, True):
        for w in (1, 3, 5, 15):
            for p in (0.05, 0.02, 0.01, 0.005, 0.002, 0.001):
                res = []
                for d in data:
                    sm = smooth_per_file(d["score"], d["spans"], w)
                    valid = ~d["is_signal_loss"]
                    if oracle:
                        valid = valid & ~(d["is_artifact"] & ~d["is_ictal"])   # oracle uses labels
                    thr = np.quantile(sm[~d["is_signal_loss"]], 1 - p)       # label-free threshold
                    above = (sm > thr) & valid
                    res.append(scor(d, runs_to_events(above, d["spans"], 90)))
                tp, fp, nr = pool(res)
                h = sum(d["noninter_h"] for d in data)
                rows.append(dict(oracle_flag_removed=oracle, smooth_windows=w, top_fraction=p,
                                 tp=tp, n_ref=nr, fp=fp, sensitivity=round(tp / nr, 4),
                                 fa_per_day=round(fp / h * 24, 2),
                                 per_subject_tp="/".join(str(r[0]) for r in res)))
    return pd.DataFrame(rows)


def main():
    data = [load(s) for s in VAL]
    for d in data:
        print(f"{d['subj']}: {d['n']} windows, {len(d['spans'])} files, {len(d['ref_iv'])} seizures, "
              f"flagged share {d['is_artifact'].mean():.3f}, non-ictal h {d['noninter_h']:.2f}")
    anat, cps, q2 = q1_q2(data)
    curve = q3(data)
    anat.to_csv(OUT / "q1_fp_anatomy.csv", index=False)
    cps.to_csv(OUT / "q1_changepoints.csv", index=False)
    q2.to_csv(OUT / "q2_rise_only.csv", index=False)
    curve.to_csv(OUT / "q3_threshold_curve.csv", index=False)
    cp_tab = cps.groupby(["point", "ictal"])[["rise", "near_boundary", "flagged"]].mean().round(3)
    with open(OUT / "SUMMARY.md", "w", encoding="utf-8") as f:
        f.write("# diag_detector_ceiling -- validation only, descriptive\n\n")
        f.write("## Q1 FP anatomy (approximate match: overlap with [onset-30, offset+60])\n\n")
        f.write(anat.to_string(index=False) + "\n\n")
        f.write("Share of change points that rise / sit within 60 s of a file boundary / sit in a "
                "flagged window, split by whether the change point is inside a seizure:\n\n")
        f.write(cp_tab.to_string() + "\n\n")
        f.write("## Q2 locked PELT vs rises-only without boundary change points (SzCORE)\n\n")
        f.write(q2.to_string(index=False) + "\n\n")
        f.write("## Q3 threshold detector, per-file smoothing, per-patient quantile threshold\n\n")
        f.write(curve.to_string(index=False) + "\n")
    print((OUT / "SUMMARY.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
