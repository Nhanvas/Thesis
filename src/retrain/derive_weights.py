"""
derive_weights.py — PREREG_03 §2: derive ensemble weights on NON-TEST data.

WHAT IT DOES (non-test only; the 8 test subjects are NEVER touched here)
  1. Builds robust-z components (zrecon/ztemp/zgamma) for the 3 VAL subjects
     (chb10,11,22) and the 12 TRAIN subjects, using the ADOPTED canonical
     seed-42 GAE + seed-42 LSTM (Gate R-GAE / R-LSTM PASS).
  2. Sweeps the full weight simplex (wr+wt+wg=1, step 0.05) maximising VAL macro
     window AUROC (rank-based -> stable on 3 subjects).
  3. Anti-overfit tie-break: among weights within 0.005 AUROC of the best, picks
     the one closest to equal (1/3,1/3,1/3) — the concrete repair for Decision
     #19's fragile margin.
  4. TRAIN cross-check (12 subjects): recomputes the objective on TRAIN; reports
     whether the VAL-optimal weights are near-optimal on TRAIN too. If they
     disagree sharply, the pre-registered fallback is equal weights — this script
     REPORTS the disagreement and a recommendation but does NOT auto-adopt
     (Boti signs off; re-lock is a later manual step).
  5. Weight-sensitivity: VAL objective change under +/-0.05 perturbations.
  6. Writes derived_weights.json (read by final_eval.py) + derive_weights_grid.csv.

This is window-AUROC only: no CPD, no summary files, no test data — deliberately
light and fully non-test.

USAGE (Kaggle GPU)
  python derive_weights.py --input_root /kaggle/input --out_dir /kaggle/working/prereg03
Smoke (no torch/data):
  python derive_weights.py --smoke
"""
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
for _p in (_here, _os.path.dirname(_here)):      # src/retrain/ and src/ (flat)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import argparse
import csv
import json
from pathlib import Path

import numpy as np

import retrain_io as IO

TOL = 0.005          # tie-break window on VAL macro AUROC
STEP = 0.05


# ============================================================================
# objective: VAL/TRAIN macro window AUROC of the ensemble for a given weight
# ============================================================================
def macro_auroc_for_weight(comps_by_subj, weight):
    """comps_by_subj: {subj: components-dict}. Returns (macro, {subj: auroc})."""
    per = {}
    for s, comp in comps_by_subj.items():
        ens_i, ens_c = IO.ensemble_from_components(comp, weight)
        per[s] = IO.window_auroc(ens_i, ens_c)
    macro = float(np.nanmean(list(per.values())))
    return macro, per


def sweep(comps_by_subj, step=STEP):
    """Full simplex sweep -> list of dict(w, objective, per_subject)."""
    rows = []
    for w in IO.simplex_grid(step):
        macro, per = macro_auroc_for_weight(comps_by_subj, w)
        rows.append(dict(w=w, objective=macro, per_subject=per))
    return rows


# ============================================================================
# component loading (Kaggle GPU) — canonical seed 42 for both branches
# ============================================================================
def load_all_components(input_root, suffix, seed=IO.CANON_SEED):
    import torch
    import gae_joint as G
    import lstm_temporal as T
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={dev}")

    adj_dir = IO.find_data_dir(input_root, f"chb13_interictal_adjs{suffix}.npy")
    feat_dir = IO.find_data_dir(input_root, "chb13_interictal_features.npy")
    gamma_dir = IO.find_gamma_dir(input_root)
    gae_ck = IO.find_ckpts(input_root, "gae_joint_seed")
    lstm_ck = IO.find_ckpts(input_root, "lstm_temporal_seed")
    print(f"adj_dir   = {adj_dir}")
    print(f"feat_dir  = {feat_dir}")
    print(f"gamma_dir = {gamma_dir}")
    print(f"GAE seeds = {sorted(gae_ck)} | LSTM seeds = {sorted(lstm_ck)} (using {seed})")
    if seed not in gae_ck or seed not in lstm_ck:
        raise SystemExit(f"canonical seed {seed} missing (GAE {sorted(gae_ck)}, "
                         f"LSTM {sorted(lstm_ck)})")

    gae = G.GAEModel().to(dev)
    gsd = IO.load_state(gae_ck[seed]); gae.load_state_dict(gsd.get("state_dict", gsd), strict=True); gae.eval()
    lstm = T.LSTMPredictor(in_dim=18 * 16).to(dev)   # flat-Z (288), PREREG_02 L0
    lsd = IO.load_state(lstm_ck[seed]); lstm.load_state_dict(lsd.get("state_dict", lsd), strict=True); lstm.eval()

    def build(subjs):
        out = {}
        for s in subjs:
            out[s] = IO.build_subject_components(gae, lstm, s, adj_dir, feat_dir,
                                                 gamma_dir, suffix, dev)
            print(f"  components built: {s}")
        return out

    print("\n[VAL] building components (chb10,11,22)")
    val = build(IO.VAL_SUBJS)
    print("[TRAIN] building components (12 subjects, cross-check)")
    train = build(IO.TRAIN_SUBJS)
    return val, train


# ============================================================================
# synthetic components for --smoke (recon+gamma informative, temporal weak)
# ============================================================================
def _synth_components(subjs, seed=0, n_i=800, n_c=60):
    rng = np.random.default_rng(seed)
    out = {}
    for k, s in enumerate(subjs):
        # ictal shifted up in recon & gamma (informative), temporal barely (weak)
        zr_i = rng.normal(0, 1, n_i); zr_c = rng.normal(1.4, 1, n_c)
        zg_i = rng.normal(0, 1, n_i); zg_c = rng.normal(1.6, 1, n_c)
        zt_i = rng.normal(0, 1, n_i); zt_c = rng.normal(0.25, 1, n_c)
        out[s] = {"zrecon": (zr_i, zr_c), "ztemp": (zt_i, zt_c), "zgamma": (zg_i, zg_c)}
    return out


# ============================================================================
def derive(val_comps, train_comps, out_dir, step=STEP, tol=TOL):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)

    # ---- VAL sweep + pick ----
    val_rows = sweep(val_comps, step)
    chosen_w, chosen_row, tied = IO.pick_weights_tiebreak_equal(val_rows, tol)
    best_obj = max(r["objective"] for r in val_rows)
    print("\n" + "=" * 70)
    print("PREREG 03 §2 — weight derivation on NON-TEST")
    print("=" * 70)
    print(f"VAL best macro AUROC = {best_obj:.4f}  ({len(tied)} weight(s) within {tol})")
    print(f"chosen (tie-break -> nearest equal): "
          f"w=({chosen_w[0]:.2f},{chosen_w[1]:.2f},{chosen_w[2]:.2f})  "
          f"VAL AUROC={chosen_row['objective']:.4f}")
    print(f"  per-VAL-subject: "
          + ", ".join(f"{s}:{a:.3f}" for s, a in chosen_row["per_subject"].items()))

    # ---- TRAIN cross-check ----
    train_rows = sweep(train_comps, step)
    tr_by_w = {r["w"]: r["objective"] for r in train_rows}
    tr_best_w = max(train_rows, key=lambda r: r["objective"])
    tr_at_chosen = tr_by_w[chosen_w]
    tr_gap = tr_best_w["objective"] - tr_at_chosen
    crosscheck_ok = tr_gap <= 0.01     # "near-optimal on TRAIN too"
    print(f"\nTRAIN cross-check (12 subjects):")
    print(f"  TRAIN best   : w=({tr_best_w['w'][0]:.2f},{tr_best_w['w'][1]:.2f},"
          f"{tr_best_w['w'][2]:.2f}) AUROC={tr_best_w['objective']:.4f}")
    print(f"  chosen on TR : AUROC={tr_at_chosen:.4f} (gap {tr_gap:+.4f}) -> "
          f"{'CONSISTENT' if crosscheck_ok else 'DISAGREES SHARPLY'}")

    equal_w = min(IO.simplex_grid(step), key=IO._dist_to_equal)
    recommend = chosen_w if crosscheck_ok else equal_w
    if not crosscheck_ok:
        print(f"  -> pre-registered fallback recommended: EQUAL weights "
              f"({equal_w[0]:.2f},{equal_w[1]:.2f},{equal_w[2]:.2f}). "
              f"NOT auto-adopted — review with Boti.")

    # ---- weight-sensitivity around the chosen point (VAL objective) ----
    print("\nweight-sensitivity (+/-0.05 moves, VAL macro AUROC):")
    sens_rows = []
    for nb in IO.neighbours_pm(chosen_w, step):
        m, _ = macro_auroc_for_weight(val_comps, nb)
        d = m - chosen_row["objective"]
        sens_rows.append(dict(w=nb, val_auroc=m, delta=d))
        print(f"  ({nb[0]:.2f},{nb[1]:.2f},{nb[2]:.2f}): {m:.4f}  Δ={d:+.4f}")
    max_abs = max((abs(r["delta"]) for r in sens_rows), default=0.0)
    print(f"  max |Δ VAL AUROC| under +/-0.05 = {max_abs:.4f}")

    # ---- write grid CSV (VAL + TRAIN objective per weight) ----
    grid_path = out / "derive_weights_grid.csv"
    with open(grid_path, "w", newline="") as f:
        wtr = csv.writer(f)
        wtr.writerow(["w_recon", "w_temporal", "w_gamma", "val_macro_auroc",
                      "train_macro_auroc", "within_tol_of_val_best",
                      "is_chosen"])
        for r in val_rows:
            wtr.writerow([f"{r['w'][0]:.2f}", f"{r['w'][1]:.2f}", f"{r['w'][2]:.2f}",
                          f"{r['objective']:.4f}", f"{tr_by_w[r['w']]:.4f}",
                          int(best_obj - r["objective"] <= tol),
                          int(r["w"] == chosen_w)])

    # ---- write derived_weights.json (consumed by final_eval.py) ----
    result = dict(
        chosen_weights=list(chosen_w),
        equal_weights=list(equal_w),
        recommended_weights=list(recommend),
        val_macro_auroc=round(chosen_row["objective"], 4),
        val_per_subject={s: round(a, 4) for s, a in chosen_row["per_subject"].items()},
        val_best_macro_auroc=round(best_obj, 4),
        n_tied_within_tol=len(tied),
        train_best_weights=list(tr_best_w["w"]),
        train_macro_auroc_at_chosen=round(tr_at_chosen, 4),
        train_best_macro_auroc=round(tr_best_w["objective"], 4),
        train_crosscheck_gap=round(tr_gap, 4),
        train_crosscheck_ok=bool(crosscheck_ok),
        weight_sensitivity_max_abs_delta=round(max_abs, 4),
        tie_break="nearest-equal within 0.005 AUROC (PREREG_03 §2)",
        note=("recommended_weights = chosen unless TRAIN disagrees sharply, "
              "in which case equal weights (fallback). Boti signs off before "
              "final_eval / re-lock."))
    wpath = out / "derived_weights.json"
    wpath.write_text(json.dumps(result, indent=2))
    print(f"\n[saved] {grid_path}")
    print(f"[saved] {wpath}")
    print(f"\nRECOMMENDED weights for final_eval: "
          f"({recommend[0]:.2f},{recommend[1]:.2f},{recommend[2]:.2f})  "
          f"[chosen={'==recommended' if recommend==chosen_w else 'differs (see fallback)'}]")
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input_root", default="/kaggle/input")
    ap.add_argument("--suffix", default="_topk20")
    ap.add_argument("--out_dir", default="/kaggle/working/prereg03")
    ap.add_argument("--seed", type=int, default=IO.CANON_SEED)
    ap.add_argument("--smoke", action="store_true",
                    help="run pure-logic self-test on synthetic components (no torch/data)")
    a = ap.parse_args()

    if a.smoke:
        print("[SMOKE] synthetic components (recon+gamma informative, temporal weak)")
        val = _synth_components(IO.VAL_SUBJS, seed=1)
        train = _synth_components(IO.TRAIN_SUBJS, seed=2)
        res = derive(val, train, "/tmp/prereg03_smoke")
        w = res["chosen_weights"]
        assert abs(sum(w) - 1.0) < 1e-6, "weights must sum to 1"
        assert w[1] <= max(w[0], w[2]) + 1e-9, \
            "temporal weight should not dominate on weak-temporal synthetic data"
        assert 0.0 <= res["val_macro_auroc"] <= 1.0
        print("\n[SMOKE] PASS")
        return

    val, train = load_all_components(a.input_root, a.suffix, a.seed)
    derive(val, train, a.out_dir, STEP, TOL)


if __name__ == "__main__":
    main()
