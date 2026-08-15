"""
eval_local.py — LOCAL CPU, no timeout, full log. Runs the FULL mag x pen grid + Pareto frontier +
option-A operating points + Wilson/Poisson CIs for seed-42, reading the pre-dumped components
(zrecon/ztemp/zgamma) from disk. NO GPU: the GAE/LSTM forward pass was already done on Kaggle
(dump_components.py); only the CPD grid (pure CPU) runs here.

Reuses final_eval.report() unchanged -> identical frontier/option-A/CI logic and CSV outputs as the
Kaggle path, so this is the same evaluation, just offline.

    python src/retrain/eval_local.py \
        --comp_dir data/processed/components_retrain \
        --summary_dir "F:/Study/Thesis/Code/data/.../summary" \
        --out_dir results/retrain_v3 --seed 42
"""
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
for _p in (_here, _os.path.dirname(_here)):          # src/retrain/ and src/ (flat)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import argparse
from pathlib import Path

import numpy as np

import retrain_io as IO
import ensemble_recipe as ER
import szcore_eval as SE
import final_eval as FE


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--comp_dir", required=True, help="dir with {zrecon,ztemp,zgamma}_{subj}_{inter,ictal}.npy")
    ap.add_argument("--summary_dir", required=True, help="dir with chb*-summary.txt")
    ap.add_argument("--out_dir", default="results/retrain_v3")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--weights", default="0.3334,0.3333,0.3333")
    ap.add_argument("--bootstrap_seed", type=int, default=0)
    ap.add_argument("--only_mags", default="", help="comma list e.g. 70,55 ; empty = full grid")
    a = ap.parse_args()
    weights = tuple(float(x) for x in a.weights.split(","))
    assert abs(sum(weights) - 1.0) < 1e-6, "weights must sum to 1"
    mags = [float(x) for x in a.only_mags.split(",")] if a.only_mags else list(FE.MAG_PCTS)
    print(f"comp_dir={a.comp_dir} | weights={weights} | mags={mags}", flush=True)

    persubj, waur = [], {}
    for s in IO.TEST_SUBJS:
        ens_i, ens_c = ER.ensemble_for_subject(a.comp_dir, s, weights=weights)
        waur[s] = IO.window_auroc(ens_i, ens_c)
        for mag in mags:
            print(f"    {s} mag={mag} ...", flush=True)
            np.random.seed(a.bootstrap_seed)                       # v2 padding-seed fix (as in run_seed)
            rows = SE.evaluate_subject(s, ens_i, ens_c, a.summary_dir, min_mag_pct=mag, local_win=15)
            for r in rows:
                persubj.append(dict(seed=a.seed, subject=s, mag_pct=mag, pen_mult=r["pen_mult"],
                                    tp=r["tp"], fp=r["fp"], n_seizures=r["n_seizures"],
                                    n_inter_h=r["n_inter_h"], sensitivity=r["sensitivity"],
                                    precision=r.get("precision", float("nan")),
                                    fp_per_day=r["fp_per_day"]))
        print(f"  {s}: window AUROC {waur[s]:.4f}", flush=True)

    # reuse the locked report(): frontier + option-A + CIs + CSVs (single seed -> multiseed cols NaN)
    FE.report({a.seed: persubj}, {a.seed: waur}, weights, a.out_dir)


if __name__ == "__main__":
    main()