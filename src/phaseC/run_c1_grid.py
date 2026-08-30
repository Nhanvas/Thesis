"""
run_c1_grid.py — Phase C / C1. CURSOR CPU. Thin driver: score an ensemble VAL grid
with a SWAPPABLE pre-CPD smoother, reusing the LOCKED scorer (score_ens ->
szcore_eval -> cpd_pipeline_v14) VERBATIM. The ONLY thing this changes is the
module global cpd_pipeline_v14.SMOOTHER, read by _smooth() at call time. Nothing in
the scoring/CPD/SzCORE math is duplicated here.

WHY: C1 targets FP/precision by replacing the locked 15-window MEAN pre-CPD smoother
with a MEDIAN (isolated interictal spikes -> spurious change points under a mean;
a median removes them while the multi-window seizure burst survives). Default
"ma15" reproduces the §0/rlg grids byte-identical (fidelity anchor).

Same ensemble as rlg (recon+latent+gamma) is re-scored under each smoother -> the
challenger is a smoother swap, NOT a new branch. Grids land where g2_val_gate reads
them: <out_dir>/final_eval_seed{S}.csv.

USAGE (Cursor CPU)
  # fidelity anchor: must reproduce the committed rlg VAL grid byte-exact
  python src/phaseC/run_c1_grid.py --smoother ma15 \
    --ens_dir results/phaseB/tier2/ens_val_tf/rlg \
    --summary_dir "F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary" \
    --out_dir results/phaseC/c1/rlg_ma15
  # challengers (same ens, better smoother)
  python src/phaseC/run_c1_grid.py --smoother median15 ... --out_dir results/phaseC/c1/rlg_median15
  python src/phaseC/run_c1_grid.py --smoother median9  ... --out_dir results/phaseC/c1/rlg_median9
Smoke:
  python src/phaseC/run_c1_grid.py --smoke
"""
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))          # .../src/phaseC
_src  = _os.path.dirname(_here)                               # .../src
for _p in (_src, _here,
           _os.path.join(_src, "retrain"),
           _os.path.join(_src, "dataprep"),
           _os.path.join(_src, "phaseB")):
    if _os.path.isdir(_p) and _p not in _sys.path:
        _sys.path.insert(0, _p)

import argparse

VALID = {"ma15", "median15", "median9", "median5"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoother", default="ma15", help="ma15 (locked) | median15 | median9 | median5")
    ap.add_argument("--ens_dir", required=False)
    ap.add_argument("--seed", default="42")
    ap.add_argument("--only_subjects", default="chb10,chb11,chb22")
    ap.add_argument("--summary_dir", default="data/summaries")
    ap.add_argument("--out_dir", required=False)
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()

    import cpd_pipeline_v14 as V14   # SAME cached module score_ens will import

    if a.smoke:
        import numpy as np, pandas as pd
        rng = np.random.default_rng(0); n = 4000; sig = rng.normal(0, 1, n)
        for c in rng.choice(n, 30, replace=False): sig[c] += 6      # isolated spikes
        sig[2000:2020] += 5                                         # burst
        base = pd.Series(sig).rolling(15, min_periods=1, center=True).mean().values
        assert float(np.abs(V14._smooth(sig) - base).max()) == 0.0, "ma15 != locked MA"
        V14.SMOOTHER = "median15"
        assert not np.allclose(V14._smooth(sig), base), "median did not change output"
        V14.SMOOTHER = "ma15"
        print("[SMOKE] ma15==locked MA (Δ=0); median15 differs; global switch works. PASS")
        return

    if a.smoother not in VALID:
        raise SystemExit(f"--smoother must be one of {sorted(VALID)}")
    if not (a.ens_dir and a.out_dir):
        raise SystemExit("--ens_dir and --out_dir required")

    V14.SMOOTHER = a.smoother                       # <-- the only injection
    print(f"[C1] SMOOTHER = {V14.SMOOTHER}  (locked scorer reused verbatim)")

    import score_ens                                # locked harness, imported after global set
    _sys.argv = ["score_ens.py",
                 "--ens_dir", a.ens_dir, "--seed", str(a.seed),
                 "--only_subjects", a.only_subjects,
                 "--summary_dir", a.summary_dir, "--out_dir", a.out_dir]
    score_ens.main()


if __name__ == "__main__":
    main()
