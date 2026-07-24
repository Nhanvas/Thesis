"""
window_tier_newweight.py — recompute the WINDOW / SAMPLE tier (RESULTS_OF_RECORD §2)
and the ensemble window-AUROC of §8.1 under the Decision #19 weight (0.40, 0.35, 0.25).

WHY: §2 (macro AUROC ~0.80) and §8.1's ensemble AUROC (0.796) were computed on the
OLD-weight ens cache and were never regenerated during the weight change (Decisions
#19/#20 touched the event tier only). Window AUROC = AUROC of the ensemble score, which
IS weight-dependent. This script rebuilds the ensemble from components with the new
weight (via ensemble_recipe.build_ensemble) and re-runs the already-LOCKED stat functions
from evaluation_protocol.py (DeLong CI, AUC-PR bootstrap CI, unsupervised operating point,
Mann-Whitney) WITHOUT modifying that file.

It also recomputes each component's standalone window AUROC as a sanity check: those are
weight-INDEPENDENT and must reproduce auroc_verification.csv (recon ~0.671 / temporal
~0.647 / gamma ~0.755). ONLY the ensemble AUROC should change with the weight.

USAGE (CPU):
  python window_tier_newweight.py \
      --comp_dir data/processed/components \
      --outdir results/cpd/evaluation \
      --op_percentile 95
Outputs: eval_window_level_newweight.csv, eval_stat_tests_newweight.csv,
         window_component_auroc_newweight.csv
Requires: evaluation_protocol.py, ensemble_recipe.py, sklearn/scipy/ruptures (as EP needs).
"""
import argparse
import csv
import glob
import os

import numpy as np
from sklearn.metrics import roc_auc_score

import evaluation_protocol as EP
from ensemble_recipe import ENS_WEIGHTS, build_ensemble, load_components, COMPONENT_KEYS

TEST_SUBJS = EP.TEST_SUBJS


def discover_comp_dir(comp_dir, subj0):
    probe = f"zrecon_{subj0}_inter.npy"
    if os.path.exists(os.path.join(comp_dir, probe)):
        return comp_dir
    hits = glob.glob(os.path.join(".", "**", probe), recursive=True)
    if hits:
        d = os.path.dirname(hits[0])
        print(f"[diag] components not at default; using {os.path.abspath(d)}")
        return d
    print(f"[diag] WARNING: {probe} not found under cwd; check --comp_dir")
    return comp_dir


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--comp_dir", default="data/processed/components")
    ap.add_argument("--outdir", default="results/cpd/evaluation")
    ap.add_argument("--op_percentile", type=float, default=95)
    ap.add_argument("--n_boot", type=int, default=1000)
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    comp_dir = discover_comp_dir(args.comp_dir, TEST_SUBJS[0])
    print(f"[diag] components dir: {os.path.abspath(comp_dir)}")
    print(f"[diag] ENS_WEIGHTS (Decision #19) = {ENS_WEIGHTS}\n")

    win_rows, stat_rows, comp_rows, aurocs = [], [], [], []
    for subj in TEST_SUBJS:
        try:
            zi = load_components(comp_dir, subj, "inter")
            zc = load_components(comp_dir, subj, "ictal")
        except FileNotFoundError as e:
            print(f"[skip] {subj}: missing component {e}")
            continue
        ens_i, ens_c = build_ensemble(*zi), build_ensemble(*zc)
        y = np.concatenate([np.zeros(len(ens_i)), np.ones(len(ens_c))])
        s = np.concatenate([ens_i, ens_c])
        auroc, (a_lo, a_hi) = EP.delong_auroc_ci(y, s)
        auprc, (p_lo, p_hi) = EP.auprc_bootstrap_ci(y, s, n_boot=args.n_boot)
        op = EP.operating_point_metrics(ens_i, ens_c, args.op_percentile)
        mw = EP.mannwhitney_effect(ens_i, ens_c)
        prevalence = 100.0 * len(ens_c) / (len(ens_i) + len(ens_c))
        aurocs.append(auroc)

        win_rows.append(dict(
            subject=subj, n_inter=len(ens_i), n_ictal=len(ens_c),
            prevalence_pct=round(prevalence, 4),
            auroc=round(auroc, 4), auroc_lo=round(a_lo, 4), auroc_hi=round(a_hi, 4),
            auprc=round(auprc, 4), auprc_lo=round(p_lo, 4), auprc_hi=round(p_hi, 4),
            op_threshold=round(op["threshold"], 4),
            sensitivity=round(op["sensitivity"], 4), specificity=round(op["specificity"], 4),
            precision=round(op["precision"], 4), f1=round(op["f1"], 4), fpr=round(op["fpr"], 4)))
        stat_rows.append(dict(subject=subj, U=mw["U"], p_value=mw["p"],
                              effect_r=round(mw["r"], 4)))

        # component standalone AUROC (weight-INDEPENDENT sanity check)
        crow = dict(subject=subj)
        for key, zi_a, zc_a in zip(COMPONENT_KEYS, zi, zc):
            yy = np.concatenate([np.zeros(len(zi_a)), np.ones(len(zc_a))])
            ss = np.concatenate([zi_a, zc_a])
            crow[key] = round(roc_auc_score(yy, ss), 4)
        crow["ensemble"] = round(auroc, 4)
        comp_rows.append(crow)

        print(f"[{subj}] ens AUROC={auroc:.4f} [{a_lo:.3f},{a_hi:.3f}]  "
              f"AUC-PR={auprc:.4f}  sens@P{args.op_percentile:g}={op['sensitivity']:.3f}  "
              f"|  recon={crow['zrecon']} temp={crow['ztemp']} gamma={crow['zgamma']}")

    if aurocs:
        print(f"\n[MACRO] window AUROC (NEW weight) = {np.mean(aurocs):.4f}   "
              f"(old-weight ensemble was ~0.796)")
        for key in COMPONENT_KEYS + ("ensemble",):
            vals = [r[key] for r in comp_rows]
            note = "  (weight-independent; must match auroc_verification.csv)" \
                if key in COMPONENT_KEYS else "  (weight-DEPENDENT; this is the new number)"
            print(f"        macro {key:<9} AUROC = {np.mean(vals):.4f}{note}")

    def dump(rows, name):
        if not rows:
            return
        with open(os.path.join(args.outdir, name), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"  [saved] {os.path.abspath(os.path.join(args.outdir, name))}")

    print()
    dump(win_rows, "eval_window_level_newweight.csv")
    dump(stat_rows, "eval_stat_tests_newweight.csv")
    dump(comp_rows, "window_component_auroc_newweight.csv")
    print("\n  Paste the per-subject lines + the [MACRO] block back to me.")


if __name__ == "__main__":
    main()