#!/usr/bin/env python
"""
branch_combine_val.py -- label-free comparison of ways to combine the three branch scores
(zrecon, zlatent, zgamma) on the CONTINUOUS timeline, VALIDATION patients only.

Save as src/branch_combine_val.py. Reuses src/continuous_eval.py unchanged (import).
Nothing is selected on the test patients. Test components are only computed (stage 'components'
with --subjects <test>) so that one pre-registered variant can be scored once afterwards.

Stages
  components  -- per-branch robust-z (zr, zl, zg) via continuous_eval.recompute_scope_t_c1.
                 For a subject with 0 signal-loss windows this equals the Scope T (A2) fit.
                 Writes cache/scores/T_c1_<subj>_components.npz (+ T_c1_<subj>.npy). Does NOT
                 touch the existing T_<subj>.npy caches. Skips subjects whose npz exists.
  eval        -- reproduction gate, then window AUROC + event grid for each variant on
                 chb10, chb11, chb22; writes results/continuous_eval/branch_combine/.

Usage (from the repo root, one process at a time):
  python src/branch_combine_val.py --stage components --subjects chb11
  python src/branch_combine_val.py --stage components --subjects chb10 chb22
  python src/branch_combine_val.py --stage eval
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import continuous_eval as CE  # noqa: E402

OUT = CE.OUT_DIR / "branch_combine"
GATE_TOL = 1e-3          # float32 cache vs float64 recomputation (robust-z values reach ~1e3)

# Pre-registered variants (fixed here, before any event-level number is read). Nothing else is tried.
VARIANTS = {
    "equal":        lambda zr, zl, zg: (zr + zl + zg) / 3.0,            # reference = system of record
    "w_10_45_45":   lambda zr, zl, zg: 0.10 * zr + 0.45 * zl + 0.45 * zg,  # window-tier optimum on validation
    "no_recon":     lambda zr, zl, zg: 0.5 * zl + 0.5 * zg,
    "median3":      lambda zr, zl, zg: np.median(np.vstack([zr, zl, zg]), axis=0),   # one hot branch cannot dominate
    "min_lat_gam":  lambda zr, zl, zg: np.minimum(zl, zg),               # both non-recon branches must agree
}


def comp_path(subj):
    return CE.c1_components_cache_path(subj)


def stage_components(subjects):
    for s in subjects:
        if comp_path(s).exists():
            CE.log("BC", f"{s}: components cached, skip")
            continue
        m = CE.load_mask(s)
        if int(m["is_signal_loss"].sum()) != 0:
            raise SystemExit(f"{s} has signal-loss windows: C1 fit != A2 fit; not used here")
        t0 = time.time()
        CE.recompute_scope_t_c1(s)
        CE.log("BC", f"{s}: components done in {time.time()-t0:.0f}s ({CE.subject_hours(s):.1f} h of EEG)")


def load_comps(s):
    z = np.load(comp_path(s))
    return z["zr"].astype(np.float64), z["zl"].astype(np.float64), z["zg"].astype(np.float64)


def variant_score(name, s, is_signal_loss):
    zr, zl, zg = load_comps(s)
    sc = np.asarray(VARIANTS[name](zr, zl, zg), dtype=np.float64)
    sc[is_signal_loss] = 0.0          # Amendment A2, as in the main cache
    return sc


def gate(subjects):
    """Reproduction gate: the 'equal' variant must reproduce the cached Scope T score."""
    ok = True
    for s in subjects:
        d = CE.load_subject_data("T", s)
        m = CE.load_mask(s)
        mine = variant_score("equal", s, m["is_signal_loss"])
        diff = float(np.max(np.abs(mine - d["score"].astype(np.float64))))
        CE.log("BC", f"gate {s}: max|equal - cached T| = {diff:.3e} (tol {GATE_TOL})")
        ok &= diff <= GATE_TOL
    if not ok:
        raise SystemExit("GATE FAILED: equal-weight recomputation does not reproduce the cached Scope T "
                         "score; stop and report, do not interpret any variant.")


def a8_pick(gdf):
    ok = gdf[gdf.fp_per_day <= 25.0]
    if not len(ok):
        return None
    best = ok.sensitivity.max()
    c = ok[ok.sensitivity == best].sort_values(["fp_per_day", "pen_mult", "mag_pct", "merge_s"])
    return c.iloc[0].to_dict()


def run_variant(name, subjects):
    rows_path = OUT / f"grid_{name}.csv"
    if rows_path.exists():
        CE.log("BC", f"{name}: grid cached, skip")
        return pd.read_csv(rows_path)
    data = {s: CE.load_subject_data("T", s) for s in subjects}
    masks = {s: CE.load_mask(s) for s in subjects}
    grids = {}
    for s in subjects:
        t0 = time.time()
        score = variant_score(name, s, masks[s]["is_signal_loss"])
        data[s]["score"] = score
        grids[s] = CE.grid_for_subject(score, data[s]["inter_mask"], None,
                                       CE.MAG_PCTS, CE.PEN_MULTS, CE.MERGE_GAPS)
        CE.log("BC", f"{name} {s}: grid done in {time.time()-t0:.0f}s")
    rows = []
    n_cells = len(grids[subjects[0]])
    for i in range(n_cells):
        ref = grids[subjects[0]][i]
        cells = []
        for s in subjects:
            c = grids[s][i]
            assert (c["mag_pct"], c["pen_mult"], c["merge_s"]) == (ref["mag_pct"], ref["pen_mult"], ref["merge_s"])
            cells.append(CE.score_one_cell(data[s], c["hyp_events"]))
        pooled = CE.pool_cells(cells)
        per = {f"tp_{s}": cells[j]["tp"] for j, s in enumerate(subjects)}
        rows.append(dict(variant=name, mag_pct=ref["mag_pct"], pen_mult=ref["pen_mult"],
                         merge_s=ref["merge_s"], **pooled, **per))
    gdf = pd.DataFrame(rows)
    gdf.to_csv(rows_path, index=False)
    return gdf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["components", "eval"], required=True)
    ap.add_argument("--subjects", nargs="+", default=list(CE.VAL_SUBJS))
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if a.stage == "components":
        stage_components(a.subjects)
        return

    subjects = list(CE.VAL_SUBJS)
    for s in subjects:
        if not comp_path(s).exists():
            raise SystemExit(f"missing components for {s}: run --stage components first")
    gate(subjects)

    lines = ["# Branch combination on the continuous timeline -- VALIDATION only", "",
             "Variants fixed in advance; no test patient used. Gate passed (equal-weight recomputation "
             "reproduces the cached Scope T score).", ""]
    summary = []
    for name in VARIANTS:
        # window-level, all windows, macro over the 3 validation patients
        aucs = []
        for s in subjects:
            m = CE.load_mask(s)
            y = m["is_ictal"].astype(int)
            aucs.append(roc_auc_score(y, variant_score(name, s, m["is_signal_loss"])))
        g = run_variant(name, subjects)
        pick = a8_pick(g)
        fixed = g[(g.mag_pct == 50.0) & (g.pen_mult == 2.0) & (g.merge_s == 90)].iloc[0]
        row = dict(variant=name, window_auroc_all=float(np.mean(aucs)),
                   a8_mag=pick["mag_pct"] if pick else None, a8_pen=pick["pen_mult"] if pick else None,
                   a8_merge=pick["merge_s"] if pick else None,
                   a8_tp=pick["tp"] if pick else None, a8_sens=pick["sensitivity"] if pick else None,
                   a8_fa_day=pick["fp_per_day"] if pick else None,
                   fixed_tp=int(fixed.tp), fixed_sens=fixed.sensitivity, fixed_fa_day=fixed.fp_per_day)
        summary.append(row)
        CE.log("BC", f"{name}: AUROC={row['window_auroc_all']:.4f} A8 tp={row['a8_tp']} "
                     f"sens={row['a8_sens']} FA={row['a8_fa_day']}")
    sdf = pd.DataFrame(summary)
    sdf.to_csv(OUT / "val_summary.csv", index=False)
    lines.append(sdf.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    lines += ["", "A8 rule: highest pooled validation sensitivity with pooled FA/day <= 25 "
                  "(ties: lower FA/day, lower penalty). n_ref is small (13 seizures): a difference of "
                  "one or two matched events is within noise."]
    (OUT / "val_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()