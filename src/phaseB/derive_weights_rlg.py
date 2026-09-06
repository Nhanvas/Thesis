"""
derive_weights_rlg.py — weight surface for the FINAL branch set (recon + latent + gamma).

WHY THIS EXISTS
  The ensemble weights in use were derived for the ORIGINAL branch set
  (reconstruction + temporal + gamma). The temporal branch was later dropped and
  the replacement branch set has been running on equal weights that were never
  re-derived. This script repeats the pre-registered weight-derivation procedure
  for the branch set actually used, so the equal-weight choice can be described
  from a measurement instead of from inheritance.

SCOPE — READ THIS BEFORE INTERPRETING THE OUTPUT
  The original procedure had four steps: sweep the simplex on the validation
  subjects, apply an anti-overfit tie-break, cross-check the result on the
  training subjects, and fall back to equal weights if the two disagree.
  This script performs the first two only. The training-subject components are
  not committed, so the cross-check cannot be run, and its fallback clause
  cannot be evaluated. The output therefore shows where the validation optimum
  lies; it does not by itself establish that equal weighting was the wrong
  choice.

  The surface is scored at the window tier. Window-tier differences in this
  project have repeatedly failed to reach the event tier, so a gap here is not
  evidence of an event-tier gain.

WHAT IT DOES
  1. Loads the committed robust-z components for the 3 VALIDATION subjects.
     The 8 held-out subjects are never read; there is a hard guard for this.
  2. Sweeps the full simplex w_recon + w_latent + w_gamma = 1, step 0.05
     (231 points), scoring each by macro window AUROC across the 3 subjects.
  3. Applies the anti-overfit tie-break: among all weights within 0.005 AUROC of
     the best, choose the one closest to (1/3, 1/3, 1/3).
  4. Scores the EXACT equal-weight point (1/3, 1/3, 1/3), which is not on the
     0.05 lattice, and reports it separately from the nearest lattice point.
  5. Reports the +/-0.05 neighbourhood sensitivity of the adopted point.

USAGE  (run from the repository root)
  python src/phaseB/derive_weights_rlg.py --smoke
  python src/phaseB/derive_weights_rlg.py

OUTPUT
  results/phaseB/tier2/weights_rlg/derive_weights_rlg_grid.csv
  results/phaseB/tier2/weights_rlg/derived_weights_rlg.json
"""
import os as _os
import sys as _sys

# --- flat imports across src/, src/phaseB/, src/retrain/ -------------------
_here = _os.path.dirname(_os.path.abspath(__file__))          # .../src/phaseB
_src = _os.path.dirname(_here)                                # .../src
_tried = [_here, _src,
          _os.path.join(_src, "retrain"),                     # retrain_io lives here
          _os.path.join(_src, "phaseB")]
for _p in _tried:
    if _os.path.isdir(_p) and _p not in _sys.path:
        _sys.path.insert(0, _p)

import argparse
import csv
import json
from pathlib import Path

import numpy as np

try:
    import retrain_io as IO
    import ensemble_recipe as ER
except ModuleNotFoundError as e:                              # fail fast, loudly
    raise SystemExit(
        f"cannot import '{e.name}'.\n"
        f"searched: {_tried}\n"
        "expected retrain_io.py in src/retrain/ and ensemble_recipe.py in src/.\n"
        "run this script from the repository root."
    )

# ---------------------------------------------------------------------------
VAL_SUBJECTS = ("chb10", "chb11", "chb22")
TEST_SUBJECTS = ("chb03", "chb06", "chb13", "chb14", "chb15",
                 "chb16", "chb17", "chb18")
SUBSET = ("zrecon", "zlatent", "zgamma")
STEP = 0.05
TOL = 0.005
EQUAL = (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)

DEFAULT_COMP_DIR = Path("results/phaseB/tier2/ens_val_tf/components")
DEFAULT_OUT_DIR = Path("results/phaseB/tier2/weights_rlg")


def _guard_no_test(comp_dir: Path) -> None:
    """Fail loudly if this script is ever pointed at held-out data."""
    if "_test" in str(comp_dir).replace("\\", "/").lower():
        raise SystemExit(f"REFUSED: comp_dir looks like held-out data: {comp_dir}")
    for s in TEST_SUBJECTS:
        if list(comp_dir.glob(f"*_{s}_*.npy")):
            raise SystemExit(
                f"REFUSED: found held-out subject {s} in {comp_dir}. "
                "This script is validation-only.")


def load_components(comp_dir: Path, subj: str, split: str) -> dict:
    """{'zrecon': arr, 'zlatent': arr, 'zgamma': arr} for one subject/split.
    Arrays on disk are already robust-z (median/MAD, inter+ictal pooled per
    subject) — the same arrays build_ensemble_subset consumes."""
    out = {}
    for key in SUBSET:
        f = comp_dir / f"{key}_{subj}_{split}.npy"
        if not f.exists():
            raise SystemExit(f"missing component: {f}")
        out[key] = np.load(f)
    return out


def macro_auroc(comps: dict, weights) -> tuple:
    """comps: {subj: {'inter': {...}, 'ictal': {...}}}. Returns (macro, per_subject)."""
    per = {}
    for subj, c in comps.items():
        ens_i = ER.build_ensemble_subset(c["inter"], SUBSET, weights=list(weights))
        ens_c = ER.build_ensemble_subset(c["ictal"], SUBSET, weights=list(weights))
        per[subj] = IO.window_auroc(ens_i, ens_c)
    vals = [v for v in per.values() if v == v]
    return (float(np.mean(vals)) if vals else float("nan")), per


def run(comp_dir: Path, out_dir: Path, step: float, tol: float) -> None:
    _guard_no_test(comp_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    comps = {}
    for s in VAL_SUBJECTS:
        comps[s] = {"inter": load_components(comp_dir, s, "inter"),
                    "ictal": load_components(comp_dir, s, "ictal")}
        n_i = len(next(iter(comps[s]["inter"].values())))
        n_c = len(next(iter(comps[s]["ictal"].values())))
        print(f"[load] {s}: {n_i} interictal, {n_c} ictal windows")

    grid_rows = []
    for w in IO.simplex_grid(step):
        macro, per = macro_auroc(comps, w)
        grid_rows.append({"w": w, "objective": macro, "per": per})

    chosen_w, chosen_row, tied = IO.pick_weights_tiebreak_equal(grid_rows, tol=tol)
    valid = [r for r in grid_rows if r["objective"] == r["objective"]]
    best_row = max(valid, key=lambda r: r["objective"])
    best = best_row["objective"]

    # The exact equal-weight point is NOT on the 0.05 lattice. Score it directly,
    # and keep the nearest lattice point separately so the two are never confused.
    eq_macro, eq_per = macro_auroc(comps, EQUAL)
    eq_lattice = min(grid_rows,
                     key=lambda r: sum((a - b) ** 2 for a, b in zip(r["w"], EQUAL)))
    equal_in_tolerance = (best - eq_macro) <= tol

    # +/- 0.05 neighbourhood of the adopted point
    nb = []
    for w in IO.neighbours_pm(chosen_w, step):
        m, _ = macro_auroc(comps, w)
        nb.append({"w": [round(x, 4) for x in w], "macro_auroc": round(m, 6)})

    grid_path = out_dir / "derive_weights_rlg_grid.csv"
    with open(grid_path, "w", newline="") as f:
        wtr = csv.writer(f)
        wtr.writerow(["w_recon", "w_latent", "w_gamma", "val_macro_auroc",
                      *[f"auroc_{s}" for s in VAL_SUBJECTS]])
        for r in grid_rows:
            wtr.writerow([f"{r['w'][0]:.2f}", f"{r['w'][1]:.2f}", f"{r['w'][2]:.2f}",
                          f"{r['objective']:.6f}",
                          *[f"{r['per'][s]:.6f}" for s in VAL_SUBJECTS]])
        wtr.writerow([f"{EQUAL[0]:.6f}", f"{EQUAL[1]:.6f}", f"{EQUAL[2]:.6f}",
                      f"{eq_macro:.6f}",
                      *[f"{eq_per[s]:.6f}" for s in VAL_SUBJECTS]])

    summary = {
        "procedure_steps_performed": ["simplex sweep on validation subjects",
                                      "anti-overfit tie-break toward equal"],
        "procedure_steps_not_performed": ["training-subject cross-check "
                                          "(components not committed)"],
        "scoring_tier": "window (macro AUROC across validation subjects)",
        "branch_set": list(SUBSET),
        "subjects": list(VAL_SUBJECTS),
        "simplex_step": step,
        "tie_break_tolerance": tol,
        "n_grid_points": len(grid_rows),
        "best_weights": [round(x, 4) for x in best_row["w"]],
        "best_objective": round(best, 6),
        "n_within_tolerance": len(tied),
        "tiebreak_adopted_weights": [round(x, 4) for x in chosen_w],
        "tiebreak_adopted_objective": round(chosen_row["objective"], 6),
        "equal_weights_exact": [round(x, 6) for x in EQUAL],
        "equal_weights_objective": round(eq_macro, 6),
        "equal_weights_per_subject": {k: round(v, 6) for k, v in eq_per.items()},
        "nearest_lattice_to_equal": [round(x, 4) for x in eq_lattice["w"]],
        "nearest_lattice_objective": round(eq_lattice["objective"], 6),
        "gap_best_minus_equal_exact": round(best - eq_macro, 6),
        "equal_within_tolerance_of_best": bool(equal_in_tolerance),
        "neighbourhood_pm_step": nb,
    }
    (out_dir / "derived_weights_rlg.json").write_text(json.dumps(summary, indent=2))

    print("\n--- weight surface, validation subjects, window tier ---")
    print(f"grid points                    : {len(grid_rows)}")
    print(f"best macro AUROC               : {best:.4f}  at {tuple(round(x,2) for x in best_row['w'])}")
    print(f"EXACT equal-weight macro AUROC : {eq_macro:.4f}  at (1/3, 1/3, 1/3)")
    print(f"  per subject                  : " +
          "  ".join(f"{s} {eq_per[s]:.4f}" for s in VAL_SUBJECTS))
    print(f"nearest lattice point to equal : {eq_lattice['objective']:.4f}  "
          f"at {tuple(round(x,2) for x in eq_lattice['w'])}")
    print(f"gap (best - exact equal)       : {best - eq_macro:.4f}")
    print(f"equal within {tol} of best     : {equal_in_tolerance}")
    print(f"points within {tol} of best    : {len(tied)}")
    print(f"tie-break would adopt          : {tuple(round(x,2) for x in chosen_w)}")
    print(f"\n[saved] {grid_path}")
    print(f"[saved] {out_dir / 'derived_weights_rlg.json'}")


def smoke() -> None:
    g = IO.simplex_grid(STEP)
    assert len(g) == 231, len(g)
    assert all(abs(sum(w) - 1.0) < 1e-9 for w in g)
    rows = [{"w": w, "objective": 0.9 - 0.001 * i} for i, w in enumerate(g)]
    cw, _, tied = IO.pick_weights_tiebreak_equal(rows, tol=TOL)
    a = np.array([1.0, 2.0, 3.0])
    _ = ER.build_ensemble_subset({"zrecon": a, "zlatent": a, "zgamma": a},
                                 SUBSET, weights=list(EQUAL))
    _ = IO.neighbours_pm(cw, STEP)
    print(f"smoke OK: {len(g)} grid points, {len(tied)} tied, chosen {cw}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--comp_dir", default=str(DEFAULT_COMP_DIR))
    ap.add_argument("--out_dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--step", type=float, default=STEP)
    ap.add_argument("--tol", type=float, default=TOL)
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    if a.smoke:
        smoke()
        return
    run(Path(a.comp_dir), Path(a.out_dir), a.step, a.tol)


if __name__ == "__main__":
    main()
