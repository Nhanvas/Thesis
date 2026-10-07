#!/usr/bin/env python
"""
veto_screen.py -- a REAL, label-free veto on the continuous timeline (validation patients only).

Save as  F:\\Study\\Thesis\\Code\\src\\veto_screen.py. Commit docs/PREREG_VETO_SCREEN.md BEFORE running.
    python src/veto_screen.py --stage features      # ~10 min: kurt_max per window from the EDF files
    python src/veto_screen.py --stage eval          # ~5-10 min: event grid on cache

Rule (fixed in the pre-registration; no sweep):
    a window is vetoed if  (it is flagged by the +-5 SD peak rule)  AND  (kurt_max > t)
    where kurt_max = max over the 18 channels of the window's kurtosis, and
    t = the Q-th percentile (Q = 95) of kurt_max over the same patient's UNFLAGGED windows.
    The score of a vetoed window is replaced by the median score of the patient's unflagged windows.
    Neither the rule nor the replacement reads any seizure label. Labels are used afterwards ONLY to measure
    how many ictal windows the rule touched.
Reuses continuous_eval.py unchanged; reads results/oracle_gate_bound/grid_V0.csv as the V0 reference.
"""
import argparse
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kurtosis

warnings.filterwarnings("ignore", message="Scaling factor")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import continuous_eval as CE   # noqa: E402

OUT = ROOT / "results" / "veto_screen_v2"
VAL = list(CE.VAL_SUBJS)
Q = 95
CH = 200


def kurt_path(s):
    return OUT / f"kurt_{s}.npy"


def flag_path(s):
    return OUT / f"flag_{s}.npy"


def stage_features(subjects):
    OUT.mkdir(parents=True, exist_ok=True)
    for s in subjects:
        if kurt_path(s).exists() and flag_path(s).exists():
            continue
        m = CE.load_mask(s)
        stats = json.loads((CE.PROCESSED_DIR / f"{s}_stats.json").read_text())
        thr = np.asarray(stats["artifact_thresh_uV"], dtype=np.float64) * 1e-6
        k = np.full(len(m["is_ictal"]), np.nan, dtype=np.float32)
        fl = np.zeros(len(m["is_ictal"]), dtype=bool)
        t0 = time.time()
        for fname, a, b in m["spans"]:
            a, b = int(a), int(b)
            filtered, nw = CE.filter_file(CE.edf_path(s, fname))
            if nw != b - a:
                raise SystemExit(f"{s}/{fname}: {nw} windows from the EDF vs {b - a} in the mask; stop.")
            for i in range(0, nw, CH):
                x = filtered[i:i + CH].astype(np.float64)
                k[a + i:a + i + len(x)] = kurtosis(x, axis=2, fisher=True).max(axis=1)
                # peak rule from the SIGNAL ONLY, for EVERY window (no ictal / buffer exemption)
                fl[a + i:a + i + len(x)] = np.any(np.abs(x).max(axis=2) > thr[None, :], axis=1)
            del filtered
        np.save(kurt_path(s), k)
        np.save(flag_path(s), fl)
        ok = ~(m["is_ictal"] | m["is_buffer"])
        agree = float((fl[ok] == m["is_artifact"][ok]).mean())
        print(f"{s}: features done in {time.time() - t0:.0f}s; flag vs cached mask agreement on non-ictal, "
              f"non-buffer windows = {agree:.4f}; ictal windows flagged by the rule = {fl[m['is_ictal']].mean():.3f}",
              flush=True)


def apply_veto(s):
    m = CE.load_mask(s)
    sc = np.asarray(CE.load_subject_data("T", s)["score"], dtype=np.float64).copy()
    k = np.load(kurt_path(s)).astype(np.float64)
    fl = np.load(flag_path(s))                    # signal-only flag, ictal windows NOT exempt
    sl = m["is_signal_loss"]
    unfl = ~fl & ~sl & ~np.isnan(k)
    t = np.percentile(k[unfl], Q)
    veto = fl & ~sl & (k > t)
    med = float(np.median(sc[~fl & ~sl]))
    sc[veto] = med
    return sc, veto, fl, m, t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["features", "eval"], required=True)
    a = ap.parse_args()
    if a.stage == "features":
        stage_features(VAL)
        return
    for s in VAL:
        if not kurt_path(s).exists():
            raise SystemExit(f"missing {kurt_path(s)}: run --stage features first")
    ref_path = ROOT / "results" / "oracle_gate_bound" / "grid_V0.csv"
    if not ref_path.exists():
        raise SystemExit("results/oracle_gate_bound/grid_V0.csv missing: run oracle_gate_bound.py first")
    v0 = pd.read_csv(ref_path)

    data = {s: CE.load_subject_data("T", s) for s in VAL}
    grids, diag = {}, []
    for s in VAL:
        sc, veto, fl, m, t = apply_veto(s)
        data[s]["score"] = sc
        ict, buf = m["is_ictal"], m["is_buffer"]
        diag.append(dict(subject=s, threshold=t, windows=len(sc), vetoed_share=float(veto.mean()),
                         ictal_flagged=float(fl[ict].mean()), ictal_vetoed=float(veto[ict].mean()), flagged_nonictal_vetoed=float(veto[fl & ~ict & ~buf].mean()),
                         seizures_over_half_vetoed=sum(1 for x, y in CE_runs(ict) if veto[x:y].mean() > 0.5),
                         seizures=len(CE_runs(ict))))
        t0 = time.time()
        grids[s] = CE.grid_for_subject(sc, data[s]["inter_mask"], None, CE.MAG_PCTS, CE.PEN_MULTS, CE.MERGE_GAPS)
        print(f"{s}: grid {time.time() - t0:.0f}s", flush=True)
    rows = []
    for i in range(len(grids[VAL[0]])):
        ref = grids[VAL[0]][i]
        cells = [CE.score_one_cell(data[s], grids[s][i]["hyp_events"]) for s in VAL]
        rows.append(dict(mag_pct=ref["mag_pct"], pen_mult=ref["pen_mult"], merge_s=ref["merge_s"], **CE.pool_cells(cells)))
    g = pd.DataFrame(rows)
    g.to_csv(OUT / "grid_veto.csv", index=False)

    def a8(x):
        ok = x[x.fp_per_day <= 25.0]
        best = ok.sensitivity.max()
        return ok[ok.sensitivity == best].sort_values(["fp_per_day", "pen_mult", "mag_pct", "merge_s"]).iloc[0]

    def fixed(x):
        return x[(x.mag_pct == 50.0) & (x.pen_mult == 2.0) & (x.merge_s == 90)].iloc[0]

    L = ["# Veto screen v2 (kurt_max, Q=95; flag computed from the signal for every window) -- validation only", "",
         "| variant | A8 matched/15 | A8 sens | A8 FA/day | cell | at 50/2.0/90: TP | FA/day | min FA/day with TP >= 5 |",
         "|---|---|---|---|---|---|---|---|"]
    for name, x in (("V0 (cached)", v0), ("veto", g)):
        p, f = a8(x), fixed(x)
        L.append(f"| {name} | {int(p.tp)} | {p.sensitivity:.3f} | {p.fp_per_day:.1f} | "
                 f"m{p.mag_pct:.0f}/p{p.pen_mult}/mg{int(p.merge_s)} | {int(f.tp)} | {f.fp_per_day:.1f} | "
                 f"{x[x.tp >= 5].fp_per_day.min():.1f} |")
    d = pd.DataFrame(diag)
    d.to_csv(OUT / "veto_diagnostics.csv", index=False)
    L += ["", "## What the rule touched (labels used only here, after the rule was applied)", "",
          d.to_string(index=False, float_format=lambda v: f"{v:.3f}"), "",
          f"Pooled ictal windows vetoed: {np.average(d.ictal_vetoed, weights=[1] * len(d)):.3f} (unweighted mean over patients).",
          "", "Pre-registered criteria: (1) A8 matched >= 8/15; (2) mean ictal-window veto share <= 0.15; "
              "(3) no validation seizure has more than half of its windows vetoed."]
    (OUT / "summary.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


def CE_runs(mask):
    d = np.diff(np.concatenate([[0], mask.astype(int), [0]]))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


if __name__ == "__main__":
    main()
