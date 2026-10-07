#!/usr/bin/env python
"""
veto_screen_test.py -- ONE-SHOT application of the pre-registered kurtosis veto to the TEST patients.

Save as F:\\Study\\Thesis\\Code\\src\\veto_screen_test.py. Run only after docs/PREREG_VETO_SCREEN_ADDENDUM2.md is committed.
    python src/veto_screen_test.py --stage features     # ~15 min (EDF read)
    python src/veto_screen_test.py --stage eval         # ~40 min (two event grids over 8 patients)
Nothing is tuned: rule, Q = 95 and the operating cell are those fixed on validation (veto_screen_v2.py).
Reuses veto_screen_v2 (OUT dir, apply_veto, stage_features) and continuous_eval unchanged. Do not run twice with
different settings; a second run with the same settings only reproduces the first.
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import continuous_eval as CE        # noqa: E402
import veto_screen_v2 as V          # noqa: E402

TEST = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
FIXED_CELLS = [(75.0, 5.0, 300), (50.0, 2.0, 90)]     # first = the cell chosen on validation for the veto
OUT = V.OUT / "test"


def grid_pooled(scores, subjects, data):
    grids = {}
    for s in subjects:
        t0 = time.time()
        data[s]["score"] = scores[s]
        grids[s] = CE.grid_for_subject(scores[s], data[s]["inter_mask"], None, CE.MAG_PCTS, CE.PEN_MULTS, CE.MERGE_GAPS)
        print(f"  {s}: grid {time.time() - t0:.0f}s", flush=True)
    rows, per = [], {}
    for i in range(len(grids[subjects[0]])):
        ref = grids[subjects[0]][i]
        cells = [CE.score_one_cell(data[s], grids[s][i]["hyp_events"]) for s in subjects]
        rows.append(dict(mag_pct=ref["mag_pct"], pen_mult=ref["pen_mult"], merge_s=ref["merge_s"], **CE.pool_cells(cells)))
        per[(ref["mag_pct"], ref["pen_mult"], ref["merge_s"])] = {s: c for s, c in zip(subjects, cells)}
    return pd.DataFrame(rows), per


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["features", "eval"], required=True)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if a.stage == "features":
        V.stage_features(TEST)
        return
    for s in TEST:
        if not V.kurt_path(s).exists() or not V.flag_path(s).exists():
            raise SystemExit(f"missing features for {s}: run --stage features first")
    data0 = {s: CE.load_subject_data("T", s) for s in TEST}
    sc0 = {s: np.asarray(data0[s]["score"], dtype=np.float64).copy() for s in TEST}
    print("V0 grid (cached score)")
    g0, per0 = grid_pooled(sc0, TEST, data0)
    g0.to_csv(OUT / "grid_V0_test.csv", index=False)

    # reproduction check against the earlier full test grid, if its columns allow it
    ref_csv = ROOT / "results" / "continuous_eval" / "stepC_full_test_grid_scopeT.csv"
    if ref_csv.exists():
        r = pd.read_csv(ref_csv)
        if {"mag_pct", "pen_mult", "merge_s", "tp", "fp"} <= set(r.columns):
            for m, p, g in FIXED_CELLS:
                x = r[(r.mag_pct == m) & (r.pen_mult == p) & (r.merge_s == g)]
                y = g0[(g0.mag_pct == m) & (g0.pen_mult == p) & (g0.merge_s == g)]
                if len(x) and len(y) and (int(x.iloc[0].tp) != int(y.iloc[0].tp) or int(x.iloc[0].fp) != int(y.iloc[0].fp)):
                    raise SystemExit(f"V0 test grid does not reproduce stepC at m{m}/p{p}/mg{g}: "
                                     f"{int(y.iloc[0].tp)}/{int(y.iloc[0].fp)} vs {int(x.iloc[0].tp)}/{int(x.iloc[0].fp)}. Stop.")
            print("V0 reproduces stepC_full_test_grid_scopeT.csv at both fixed cells")
        else:
            print("stepC columns differ from expectation; reproduction check skipped:", list(r.columns))

    data1 = {s: CE.load_subject_data("T", s) for s in TEST}
    sc1, diag = {}, []
    for s in TEST:
        sc, veto, fl, m, t = V.apply_veto(s)
        sc1[s] = sc
        ict, buf = m["is_ictal"], m["is_buffer"]
        diag.append(dict(subject=s, threshold=t, windows=len(sc), vetoed_share=float(veto.mean()),
                         ictal_flagged=float(fl[ict].mean()), ictal_vetoed=float(veto[ict].mean()),
                         flagged_nonictal_vetoed=float(veto[fl & ~ict & ~buf].mean())))
    print("veto grid")
    g1, per1 = grid_pooled(sc1, TEST, data1)
    g1.to_csv(OUT / "grid_veto_test.csv", index=False)
    pd.DataFrame(diag).to_csv(OUT / "veto_diagnostics_test.csv", index=False)

    def best(x):
        ok = x[x.fp_per_day <= 25.0]
        if not len(ok):
            return None
        b = ok.sensitivity.max()
        return ok[ok.sensitivity == b].sort_values(["fp_per_day", "pen_mult", "mag_pct", "merge_s"]).iloc[0]

    L = ["# Kurtosis veto -- ONE-SHOT on the test patients (8 patients)", "",
         "| cell | variant | matched / reference events | sensitivity | FP | FA/day |", "|---|---|---|---|---|---|"]
    for m, p, g in FIXED_CELLS:
        for name, x in (("V0", g0), ("veto", g1)):
            r = x[(x.mag_pct == m) & (x.pen_mult == p) & (x.merge_s == g)].iloc[0]
            L.append(f"| m{m:.0f}/p{p}/mg{g} | {name} | {int(r.tp)} / {int(r.n_ref)} | {r.sensitivity:.3f} | {int(r.fp)} | {r.fp_per_day:.1f} |")
    L += ["", "Descriptive, not a selected operating point: best pooled sensitivity with FA/day <= 25 on the test grid.", ""]
    for name, x in (("V0", g0), ("veto", g1)):
        b = best(x)
        if b is not None:
            L.append(f"- {name}: {int(b.tp)} / {int(b.n_ref)} matched, sensitivity {b.sensitivity:.3f}, FA/day {b.fp_per_day:.1f}, "
                     f"cell m{b.mag_pct:.0f}/p{b.pen_mult}/mg{int(b.merge_s)}")
    L += ["", "## Per patient at the validation cell (m75/p5.0/mg300)", "",
          "| patient | V0 matched/ref | V0 FP | veto matched/ref | veto FP |", "|---|---|---|---|---|"]
    cell = FIXED_CELLS[0]
    for s in TEST:
        a0, a1 = per0[cell][s], per1[cell][s]
        L.append(f"| {s} | {int(a0['tp'])}/{int(a0.get('n_ref', 0))} | {int(a0['fp'])} | {int(a1['tp'])}/{int(a1.get('n_ref', 0))} | {int(a1['fp'])} |")
    L += ["", "## What the rule touched (labels used only for this diagnostic)", "",
          pd.DataFrame(diag).to_string(index=False, float_format=lambda v: f"{v:.3f}"), "",
          "This is a one-shot result. The test patients were scored several times earlier in the work; "
          "the report states that."]
    (OUT / "summary_test.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
