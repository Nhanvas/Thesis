"""
seed_check_slopegate.py — Phase C, pre-one-shot gate. CURSOR CPU.

The s75 slope-gate Pareto-improves rlg at the headline (B=3.6) on seed 42. Before
spending the single TEST exposure we must confirm the win is NOT seed-42-specific
(§0 seed-stability was 0.648 ± 0.011). This re-scores rlg (slope0) and s75 on EVERY
seed whose rlg VAL ensemble is present, using the LOCKED scorer verbatim (only
cpd_pipeline_v14.MIN_SLOPE_PCT is toggled), and reports per-seed ΔF1 and sensitivity
at the matched low-FP budget.

PRE-REGISTERED VERDICT (state before running)
  s75 must, at matched B=3.6 FP/day, satisfy on EACH available seed:
      F1(s75) >= F1(rlg)  AND  sens(s75) >= sens(rlg) - 0.02
  PASS on ALL seeds       -> win is seed-robust; proceed to one-shot TEST.
  PASS on majority only    -> report as seed-sensitive; decide case-by-case.
  FAIL (seed-42-only)      -> do NOT burn one-shot; win is fragile.

Pooling is SzCORE-correct, reused from g2_val_gate (reftrue / shared_at_budget).

USAGE
  python src/phaseC/seed_check_slopegate.py \
    --ens_dir results/phaseB/tier2/ens_val_tf/rlg \
    --summary_dir "F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary" \
    --slope_pct 75 --budget 3.6 --out_root results/phaseC/c_onset/seedcheck
Smoke:
  python src/phaseC/seed_check_slopegate.py --smoke
"""
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
_src = _os.path.dirname(_here)
for _p in (_src, _here, _os.path.join(_src, "retrain"), _os.path.join(_src, "dataprep"),
           _os.path.join(_src, "phaseB")):
    if _os.path.isdir(_p) and _p not in _sys.path:
        _sys.path.insert(0, _p)

import argparse
import glob
import re
from pathlib import Path
import pandas as pd


def discover_seeds(ens_dir):
    seeds = set()
    for f in glob.glob(str(Path(ens_dir) / "ens_seed*_chb10_inter.npy")):
        m = re.search(r"ens_seed(\d+)_", Path(f).name)
        if m:
            seeds.add(int(m.group(1)))
    return sorted(seeds)


def score_one(ens_dir, seed, slope_pct, subjects, summary_dir, out_dir):
    import cpd_pipeline_v14 as V14
    import score_ens
    V14.MIN_SLOPE_PCT = float(slope_pct)
    _sys.argv = ["score_ens.py", "--ens_dir", str(ens_dir), "--seed", str(seed),
                 "--only_subjects", subjects, "--summary_dir", summary_dir,
                 "--out_dir", str(out_dir)]
    score_ens.main()
    V14.MIN_SLOPE_PCT = 0.0
    return pd.read_csv(Path(out_dir) / f"final_eval_seed{seed}.csv")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ens_dir")
    ap.add_argument("--summary_dir", default="data/summaries")
    ap.add_argument("--subjects", default="chb10,chb11,chb22")
    ap.add_argument("--slope_pct", type=float, default=75.0)
    ap.add_argument("--budget", type=float, default=3.6)
    ap.add_argument("--out_root", default="results/phaseC/c_onset/seedcheck")
    ap.add_argument("--seeds", default=None, help="comma list; default = auto-discover")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()

    from g2_val_gate import reftrue, shared_at_budget

    if a.smoke:
        # two synthetic grids per 'seed'; s75 shifts one FP off at the budget cell
        def mkgrid(better):
            rows = []
            for subj, rt in (("chb10", 7), ("chb11", 5), ("chb22", 3)):
                for m in (70, 80):
                    for p in (5.0, 10.0):
                        fp = (15 if (m == 80 and p == 10.0) else 40) - (2 if better else 0)
                        tp = 2
                        rows.append(dict(seed=42, subject=subj, mag_pct=m, pen_mult=p, tp=tp,
                                         fp=max(fp, 0), n_seizures=rt, n_inter_h=120.0,
                                         sensitivity=tp / rt, precision=tp / (tp + max(fp, 0)),
                                         fp_per_day=max(fp, 0) / 5.0, window_auroc=0.9))
            return pd.DataFrame(rows)
        rlg, s75 = mkgrid(False), mkgrid(True)
        rt = reftrue(rlg)
        cr = shared_at_budget(rlg, rt, 8.0); cs = shared_at_budget(s75, rt, 8.0)
        print(f"[SMOKE] rlg F1={cr['f1']:.3f}  s75 F1={cs['f1']:.3f}  ΔF1={cs['f1']-cr['f1']:+.3f}")
        print("[SMOKE] PASS")
        return

    seeds = [int(x) for x in a.seeds.split(",")] if a.seeds else discover_seeds(a.ens_dir)
    if not seeds:
        raise SystemExit(f"no ens_seed*_chb10_inter.npy found in {a.ens_dir}")
    print(f"seeds found: {seeds}   slope_pct={a.slope_pct}   budget B={a.budget} FP/day\n")
    print(f"{'seed':>5} | {'rlg F1':>7}{'rlg sens':>9} | {'s75 F1':>7}{'s75 sens':>9} | "
          f"{'ΔF1':>7}{'Δsens':>7}  verdict")

    all_pass = True
    for sd in seeds:
        root = Path(a.out_root)
        g_rlg = score_one(a.ens_dir, sd, 0.0, a.subjects, a.summary_dir, root / f"seed{sd}/slope0")
        g_s75 = score_one(a.ens_dir, sd, a.slope_pct, a.subjects, a.summary_dir, root / f"seed{sd}/slope{int(a.slope_pct)}")
        rt = reftrue(g_rlg)
        cr = shared_at_budget(g_rlg, rt, a.budget)
        cs = shared_at_budget(g_s75, rt, a.budget)
        dF1, dS = cs["f1"] - cr["f1"], cs["sens"] - cr["sens"]
        ok = (cs["f1"] >= cr["f1"]) and (cs["sens"] >= cr["sens"] - 0.02)
        all_pass &= ok
        print(f"{sd:>5} | {cr['f1']:7.3f}{cr['sens']:9.3f} | {cs['f1']:7.3f}{cs['sens']:9.3f} | "
              f"{dF1:+7.3f}{dS:+7.3f}  {'PASS' if ok else 'FAIL'}")

    print(f"\n[SEED-ROBUSTNESS] {'ALL PASS -> win seed-robust; proceed to one-shot TEST.' if all_pass else 'NOT all seeds pass -> win is seed-sensitive; do NOT burn one-shot yet.'}")


if __name__ == "__main__":
    main()
