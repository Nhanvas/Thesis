#!/usr/bin/env python
"""
file_state_check.py -- is the 'artifact' problem a FILE-LEVEL state, and does a rolling baseline help?

Save as  F:\\Study\\Thesis\\Code\\src\\file_state_check.py  and run from the repo root:
    python src/file_state_check.py

Part 1 (descriptive, masks only, no scores): per recording file, the share of windows flagged by the
        +-5 SD amplitude rule, for validation and test patients.
Part 2 (validation only): how much of the fused-score variance sits BETWEEN files (eta^2),
        and the correlation between a file's mean score and its flagged share.
Part 3 (validation only, pre-registered, ONE configuration, no sweep): rolling robust baseline on the
        fused score -- centered window of 450 windows (30 min), subtract the rolling median, divide by the
        rolling MAD (floor = 0.1 x the subject's median rolling MAD). Applied to the equal-weight score
        and to the no_recon score. Same event grid and A8 rule as continuous_eval / branch_combine_val.
No test score is read. Reuses continuous_eval.py and branch_combine_val.py unchanged.
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import continuous_eval as CE        # noqa: E402
import branch_combine_val as BC     # noqa: E402

OUT = CE.OUT_DIR / "file_state_check"
W = 450                              # 30 min of 4 s windows; fixed before any run
TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]


def rolling_detrend(x):
    s = pd.Series(np.asarray(x, dtype=np.float64))
    med = s.rolling(W, center=True, min_periods=W // 4).median()
    mad = (s - med).abs().rolling(W, center=True, min_periods=W // 4).median()
    floor = 0.1 * float(np.nanmedian(mad.values))
    z = (s - med) / np.maximum(mad.values, max(floor, 1e-9))
    return np.nan_to_num(z.values, nan=0.0)


def file_fractions(subj):
    m = CE.load_mask(subj)
    rows = []
    for fname, s, e in m["spans"]:
        s, e = int(s), int(e)
        bad = m["is_ictal"][s:e] | m["is_buffer"][s:e]
        ok = ~bad
        n = int(ok.sum())
        rows.append(dict(subject=subj, file=str(fname), windows=e - s,
                         flagged_share=float(m["is_artifact"][s:e][ok].mean()) if n else np.nan))
    return pd.DataFrame(rows)


def a8_pick(g):
    ok = g[g.fp_per_day <= 25.0]
    if not len(ok):
        return None
    best = ok.sensitivity.max()
    return ok[ok.sensitivity == best].sort_values(["fp_per_day", "pen_mult", "mag_pct", "merge_s"]).iloc[0].to_dict()


def run_grid(name, scores, subjects):
    path = OUT / f"grid_{name}.csv"
    if path.exists():
        return pd.read_csv(path)
    data = {s: CE.load_subject_data("T", s) for s in subjects}
    grids = {}
    for s in subjects:
        t0 = time.time()
        data[s]["score"] = scores[s]
        grids[s] = CE.grid_for_subject(scores[s], data[s]["inter_mask"], None,
                                       CE.MAG_PCTS, CE.PEN_MULTS, CE.MERGE_GAPS)
        CE.log("FS", f"{name} {s}: grid {time.time() - t0:.0f}s")
    rows = []
    for i in range(len(grids[subjects[0]])):
        ref = grids[subjects[0]][i]
        cells = [CE.score_one_cell(data[s], grids[s][i]["hyp_events"]) for s in subjects]
        rows.append(dict(variant=name, mag_pct=ref["mag_pct"], pen_mult=ref["pen_mult"],
                         merge_s=ref["merge_s"], **CE.pool_cells(cells)))
    g = pd.DataFrame(rows)
    g.to_csv(path, index=False)
    return g


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    val = list(CE.VAL_SUBJS)
    L = ["# File-state check", ""]

    # ---- Part 1: flagged share per file (masks only)
    ff = pd.concat([file_fractions(s) for s in val + TEST_SUBJS], ignore_index=True)
    ff.to_csv(OUT / "flagged_share_per_file.csv", index=False)
    L += ["## 1. Share of windows flagged by the +-5 SD rule, per file", "",
          "| subject | files | median share | files > 50 % | files > 90 % | files < 10 % |", "|---|---|---|---|---|---|"]
    for s in val + TEST_SUBJS:
        x = ff[ff.subject == s].flagged_share.dropna().values
        L.append(f"| {s} | {len(x)} | {np.median(x):.2f} | {(x > .5).sum()} | {(x > .9).sum()} | {(x < .1).sum()} |")
    L.append("")

    # ---- Part 2: between-file variance of the fused score (validation)
    L += ["## 2. Fused score (equal weights), validation, non-ictal and non-buffer windows", "",
          "| subject | eta^2 between files | corr(file mean score, file flagged share) |", "|---|---|---|"]
    scores_eq, scores_nr = {}, {}
    for s in val:
        m = CE.load_mask(s)
        eq = BC.variant_score("equal", s, m["is_signal_loss"])
        nr = BC.variant_score("no_recon", s, m["is_signal_loss"])
        scores_eq[s], scores_nr[s] = eq, nr
        ok = ~(m["is_ictal"] | m["is_buffer"])
        fid = np.full(len(eq), -1)
        for k, (fname, a, b) in enumerate(m["spans"]):
            fid[int(a):int(b)] = k
        x, f = eq[ok], fid[ok]
        mu = x.mean()
        ss_tot = ((x - mu) ** 2).sum()
        ss_b = sum(((x[f == k].mean() - mu) ** 2) * (f == k).sum() for k in np.unique(f))
        fm = np.array([x[f == k].mean() for k in np.unique(f)])
        fs = np.array([m["is_artifact"][fid == k][ok[fid == k]].mean() for k in np.unique(f)])
        L.append(f"| {s} | {ss_b / ss_tot:.3f} | {np.corrcoef(fm, fs)[0, 1]:.3f} |")
    L.append("")

    # ---- Part 3: rolling baseline (one pre-registered configuration)
    variants = {
        "equal": scores_eq,
        "equal_detrend": {s: rolling_detrend(scores_eq[s]) for s in val},
        "no_recon_detrend": {s: rolling_detrend(scores_nr[s]) for s in val},
    }
    summ = []
    for name, sc in variants.items():
        aucs = []
        for s in val:
            y = CE.load_mask(s)["is_ictal"].astype(int)
            aucs.append(roc_auc_score(y, sc[s]))
        g = run_grid(name, sc, val)
        p = a8_pick(g)
        fx = g[(g.mag_pct == 50.0) & (g.pen_mult == 2.0) & (g.merge_s == 90)].iloc[0]
        summ.append(dict(variant=name, window_auroc_all=float(np.mean(aucs)),
                         a8_tp=p["tp"] if p else None, a8_sens=p["sensitivity"] if p else None,
                         a8_fa_day=p["fp_per_day"] if p else None,
                         a8_cell=f"m{p['mag_pct']:.0f}/p{p['pen_mult']}/mg{p['merge_s']}" if p else None,
                         fixed_tp=int(fx.tp), fixed_fa_day=fx.fp_per_day))
        CE.log("FS", f"{name}: {summ[-1]}")
    sdf = pd.DataFrame(summ)
    sdf.to_csv(OUT / "val_summary.csv", index=False)
    L += ["## 3. Rolling baseline (450 windows, centered), validation", "",
          sdf.to_string(index=False, float_format=lambda v: f"{v:.3f}"), "",
          "A8 rule: highest pooled sensitivity with pooled FA/day <= 25. 15 reference events: one or two "
          "matched events is within noise. Nothing here is selected on a test patient."]
    (OUT / "file_state_check.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()