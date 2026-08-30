"""
run_slopegate_grid.py — Phase C / (C) onset slope-gate. CURSOR CPU. Thin driver:
sets cpd_pipeline_v14.MIN_SLOPE_PCT then reuses the LOCKED scorer (score_ens ->
szcore_eval -> cpd_pipeline_v14) VERBATIM. Nothing in the scoring/CPD/SzCORE math is
duplicated. MIN_SLOPE_PCT=0 reproduces the rlg VAL grid byte-identical (fidelity).

The slope-gate keeps only change-points whose local signed RISE >= the percentile of
background interictal CP rises -> rejects high-level interictal PLATEAUS (FP source on
chb10, where level-PELT is below chance) while keeping rising onsets. Same rlg ensemble;
the challenger is a CP-filter, not a new branch.

USAGE (Cursor CPU)
  # fidelity anchor: must reproduce committed rlg VAL grid byte-exact
  python src/phaseC/run_slopegate_grid.py --min_slope_pct 0 \
    --ens_dir results/phaseB/tier2/ens_val_tf/rlg \
    --summary_dir "F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary" \
    --out_dir results/phaseC/c_onset/slope0
  # challengers
  python src/phaseC/run_slopegate_grid.py --min_slope_pct 75 ... --out_dir results/phaseC/c_onset/slope75
  python src/phaseC/run_slopegate_grid.py --min_slope_pct 90 ... --out_dir results/phaseC/c_onset/slope90
Smoke:
  python src/phaseC/run_slopegate_grid.py --smoke
"""
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
_src = _os.path.dirname(_here)
for _p in (_src, _here, _os.path.join(_src, "retrain"), _os.path.join(_src, "dataprep"),
           _os.path.join(_src, "phaseB")):
    if _os.path.isdir(_p) and _p not in _sys.path:
        _sys.path.insert(0, _p)

import argparse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min_slope_pct", type=float, default=0.0,
                    help="0 = OFF (locked, byte-exact); 60/75/90 = slope-gate strength")
    ap.add_argument("--ens_dir")
    ap.add_argument("--seed", default="42")
    ap.add_argument("--only_subjects", default="chb10,chb11,chb22")
    ap.add_argument("--summary_dir", default="data/summaries")
    ap.add_argument("--out_dir")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()

    import cpd_pipeline_v14 as V14

    if a.smoke:
        import numpy as np
        rng = np.random.default_rng(0); n = 6000
        sig = rng.normal(0, 1, n)
        for c in rng.choice(n, 40, replace=False): sig[c] += 6     # spikes
        sig[3000:3040] += 4                                        # rising onset burst
        inter = np.ones(n, bool); inter[3000:3040] = False
        V14.MIN_SLOPE_PCT = 0
        ev0 = V14.detect_events(sig, 1.0, 60, inter_mask=inter)
        V14.MIN_SLOPE_PCT = 75
        ev1 = V14.detect_events(sig, 1.0, 60, inter_mask=inter)
        V14.MIN_SLOPE_PCT = 0
        assert len(ev1) <= len(ev0), "slope-gate should not add events"
        print(f"[SMOKE] slope-gate off={len(ev0)} events -> pct75={len(ev1)} events (fewer/equal). PASS")
        return

    if not (a.ens_dir and a.out_dir):
        raise SystemExit("--ens_dir and --out_dir required")
    V14.MIN_SLOPE_PCT = float(a.min_slope_pct)         # the only injection
    print(f"[C-onset] MIN_SLOPE_PCT = {V14.MIN_SLOPE_PCT}  (locked scorer reused verbatim)")

    import score_ens
    _sys.argv = ["score_ens.py",
                 "--ens_dir", a.ens_dir, "--seed", str(a.seed),
                 "--only_subjects", a.only_subjects,
                 "--summary_dir", a.summary_dir, "--out_dir", a.out_dir]
    score_ens.main()


if __name__ == "__main__":
    main()
