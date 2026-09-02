"""
================================================================================
 weight_seed_robustness_check.py  —  is the weight-grid signal real, or seed-0
                                      noise?
================================================================================
WHY THIS FILE
-------------
weight_sensitivity_sweep.py (single seed=0) found 5 weight points in a local
neighborhood of the locked (0.35, 0.30, 0.35) that appear to beat it:

    w=(0.40,0.35,0.25)  Δsens=+0.0395  ΔFP/day=+0.52
    w=(0.35,0.35,0.30)  Δsens=+0.0263  ΔFP/day=+1.90
    w=(0.35,0.40,0.25)  Δsens=+0.0263  ΔFP/day=+2.76
    w=(0.40,0.40,0.20)  Δsens=+0.0263  ΔFP/day=+1.64
    w=(0.45,0.35,0.20)  Δsens=+0.0263  ΔFP/day=-0.43   <- best: higher sens AND lower FP/day

BUT: PLAN_AND_STATUS.md already documents that detection rate swings +/-2-3%
across different bootstrap-padding seeds (Week 1 finding, before the PELT
penalty was made seed-independent for the *padding-variance* part; padding
STILL uses np.random.choice(inter_scores, ...) seeded per-call). A single
Δsens of +0.026 (2 seizures out of 76) is THE SAME ORDER OF MAGNITUDE as
known seed noise. Before treating any of these 5 points as a real signal
(let alone reopening a pre-Phase-A lock, which needs explicit sign-off per
Core Rule #7), we must confirm the apparent gain survives across multiple
seeds and isn't a lucky roll for seed=0 specifically.

WHAT THIS SCRIPT DOES
----------------------
For the LOCKED point + the 5 flagged candidates (6 points total, not the
full 37-point grid -- keeps runtime bounded), runs N_SEEDS different
np.random.seed() values through the exact same eval_ensemble/build_timeline
path as weight_sensitivity_sweep.py, and reports, per point:
  - mean +/- SD sensitivity and FP/day across seeds
  - a paired comparison against the locked point AT THE SAME SEED each time
    (removes seed as a confound: for seed k, compare candidate_k vs locked_k,
    not candidate_k vs locked's single-seed number)
  - how many of the N_SEEDS the candidate actually beats the locked point
    (a "win rate"; a real signal should win most/all seeds, a noise artifact
    should win roughly at chance / inconsistently)

DOES NOT auto-adopt anything. Reports for review, per the same governance as
weight_sensitivity_sweep.py and Core Rule #7 (this predates Phase A).

PROGRESS: prints a line after each (point, seed) evaluation -- this script
runs 6 points x N_SEEDS x 8 subjects = potentially hours; do not assume it is
stuck if there is a gap, watch the progress lines.

USAGE (Cursor / CPU)
  python weight_seed_robustness_check.py --comp_dir data/processed/components \
      --scores_dir results/cpd/scores --summary_dir "F:\\...\\summary" \
      --outdir results/phaseA_appendix --n_seeds 8

Requires szcore_eval.py, evaluation_protocol.py, cpd_pipeline_v14.py, timescoring.
================================================================================
"""
import argparse
import csv
import os
import glob as _glob
import numpy as np

import szcore_eval as SE
import cpd_pipeline_v14 as V14

TEST_SUBJS = SE.TEST_SUBJS
WIN_SEC = SE.WIN_SEC
PEN, MAG = 1.0, 60.0   # balanced operating point, same as weight_sensitivity_sweep.py

LOCKED_W = (0.35, 0.30, 0.35)
# the 5 candidates flagged by weight_sensitivity_sweep.py's first (radius=0.15,
# step=0.05) run, in the same order they were printed. Hardcoded here rather
# than re-read from the grid CSV so this script is self-contained and its
# provenance is auditable directly from this file.
CANDIDATES = [
    (0.40, 0.35, 0.25),
    (0.35, 0.35, 0.30),
    (0.35, 0.40, 0.25),
    (0.40, 0.40, 0.20),
    (0.45, 0.35, 0.20),
]
POINTS = [("locked", LOCKED_W)] + [(f"cand_{i+1}", c) for i, c in enumerate(CANDIDATES)]


def load_comp(comp_dir, subj):
    def L(name, split):
        p = os.path.join(comp_dir, f"{name}_{subj}_{split}.npy")
        return np.load(p).astype(np.float64) if os.path.exists(p) else None
    return {k: (L(k, "inter"), L(k, "ictal")) for k in ("zrecon", "ztemp", "zgamma")}


def eval_ensemble(subj, ens_in, ens_ic, summary_dir, pen, min_mag_pct, seed):
    np.random.seed(seed)
    signal, is_ictal, is_buffer, real_inter, sz_ranges, n_inter_h = \
        SE.build_timeline_masked(subj, ens_in, ens_ic, summary_dir)
    ref_iv = [(s * WIN_SEC, e * WIN_SEC) for (s, e) in sz_ranges]
    total_dur_s = len(signal) * WIN_SEC
    cps, _ = V14.detect_changepoints(signal, pen, min_mag_pct=min_mag_pct,
                                     local_win=15, inter_mask=real_inter)
    hyp_iv = SE.cps_to_events(cps, is_buffer, len(signal), sz_ranges=sz_ranges)
    sc = SE.score_szcore(ref_iv, hyp_iv, total_dur_s, n_inter_h)
    sc["n_seizures"] = len(sz_ranges); sc["n_inter_h"] = n_inter_h
    return sc


def pooled(per, subjs):
    tp = sum(per[s]["tp"] for s in subjs if s in per)
    nz = sum(per[s]["n_seizures"] for s in subjs if s in per)
    fp = sum(per[s]["fp"] for s in subjs if s in per)
    h = sum(per[s]["n_inter_h"] for s in subjs if s in per)
    return (tp / nz if nz else float("nan"),
            fp / h * 24 if h else float("nan"), tp, nz)


def main():
    ap = argparse.ArgumentParser(description="Multi-seed robustness check for the "
                                             "5 weight-grid candidates vs the lock")
    ap.add_argument("--comp_dir", default="data/processed/components")
    ap.add_argument("--summary_dir", required=True)
    ap.add_argument("--subjs", default=",".join(TEST_SUBJS))
    ap.add_argument("--outdir", default="results/phaseA_appendix")
    ap.add_argument("--n_seeds", type=int, default=8,
                    help="number of bootstrap-padding seeds to test (8, matching "
                         "the seed-robustness precedent already run for the main "
                         "pipeline in PLAN_AND_STATUS.md Week 1)")
    args = ap.parse_args()
    subjs = args.subjs.split(",")
    os.makedirs(args.outdir, exist_ok=True)
    print(f"[diag] outputs -> {os.path.abspath(args.outdir)}")

    probe = f"zrecon_{subjs[0]}_inter.npy"
    if not os.path.exists(os.path.join(args.comp_dir, probe)):
        hits = _glob.glob(os.path.join(".", "**", probe), recursive=True)
        if hits:
            args.comp_dir = os.path.dirname(hits[0])
            print(f"[diag] components not at default; using {os.path.abspath(args.comp_dir)}")
    print(f"[diag] components dir: {os.path.abspath(args.comp_dir)}")

    comps = {}
    for s in subjs:
        c = load_comp(args.comp_dir, s)
        if not all(c[k][0] is not None and c[k][1] is not None for k in c):
            print(f"[warn] {s}: components missing -> skipped")
            continue
        ni = min(len(c["zrecon"][0]), len(c["ztemp"][0]), len(c["zgamma"][0]))
        nc = min(len(c["zrecon"][1]), len(c["ztemp"][1]), len(c["zgamma"][1]))
        comps[s] = {k: (c[k][0][:ni], c[k][1][:nc]) for k in c}
    subjs = [s for s in subjs if s in comps]
    if not subjs:
        print("[error] no subjects with complete components found -- aborting.")
        return

    print(f"\n[plan] {len(POINTS)} weight points x {args.n_seeds} seeds x "
         f"{len(subjs)} subjects = {len(POINTS) * args.n_seeds * len(subjs)} "
         f"total evaluations. This will take a while -- progress below.\n")

    # rows[point_name][seed] = (sens, fp_per_day, tp, nz)
    results = {name: {} for name, _ in POINTS}
    total_evals = len(POINTS) * args.n_seeds
    done = 0
    for name, (wr, wt, wg) in POINTS:
        for seed in range(args.n_seeds):
            per = {}
            for s in subjs:
                zr_i, zr_c = comps[s]["zrecon"]; zt_i, zt_c = comps[s]["ztemp"]; zg_i, zg_c = comps[s]["zgamma"]
                ens_i = wr * zr_i + wt * zt_i + wg * zg_i
                ens_c = wr * zr_c + wt * zt_c + wg * zg_c
                per[s] = eval_ensemble(s, ens_i, ens_c, args.summary_dir, PEN, MAG, seed)
            se, fp, tp, nz = pooled(per, subjs)
            results[name][seed] = (se, fp, tp, nz)
            done += 1
            print(f"  [{done}/{total_evals}] {name} w=({wr:.2f},{wt:.2f},{wg:.2f}) "
                 f"seed={seed}: sens={se:.4f} FP/day={fp:.2f}", flush=True)

    # ---- paired comparison: candidate vs locked AT THE SAME SEED ----
    print("\n" + "=" * 78)
    print("PAIRED COMPARISON (candidate vs locked, same seed each time)")
    print("=" * 78)
    summary_rows = []
    locked_sens = np.array([results["locked"][k][0] for k in range(args.n_seeds)])
    locked_fp = np.array([results["locked"][k][1] for k in range(args.n_seeds)])
    print(f"\nlocked (0.35,0.30,0.35): sens={locked_sens.mean():.4f} +/- "
         f"{locked_sens.std(ddof=1):.4f}   FP/day={locked_fp.mean():.2f} +/- "
         f"{locked_fp.std(ddof=1):.2f}")
    summary_rows.append(dict(point="locked", w_recon=LOCKED_W[0], w_temp=LOCKED_W[1],
                            w_gamma=LOCKED_W[2], sens_mean=round(locked_sens.mean(), 4),
                            sens_sd=round(locked_sens.std(ddof=1), 4),
                            fp_per_day_mean=round(locked_fp.mean(), 2),
                            fp_per_day_sd=round(locked_fp.std(ddof=1), 2),
                            win_rate_vs_locked=None, mean_paired_delta_sens=None))

    for i, (wr, wt, wg) in enumerate(CANDIDATES):
        name = f"cand_{i+1}"
        cand_sens = np.array([results[name][k][0] for k in range(args.n_seeds)])
        cand_fp = np.array([results[name][k][1] for k in range(args.n_seeds)])
        paired_delta = cand_sens - locked_sens          # per-seed, paired
        wins = int(np.sum(paired_delta > 0))
        print(f"\ncand_{i+1} ({wr:.2f},{wt:.2f},{wg:.2f}): "
             f"sens={cand_sens.mean():.4f} +/- {cand_sens.std(ddof=1):.4f}   "
             f"FP/day={cand_fp.mean():.2f} +/- {cand_fp.std(ddof=1):.2f}")
        print(f"  paired Δsens per seed: {[round(d, 4) for d in paired_delta]}")
        print(f"  wins vs locked (same seed): {wins}/{args.n_seeds}   "
             f"mean paired Δsens: {paired_delta.mean():+.4f}")
        from scipy import stats as _stats
        # one-sided sign test: H0 = candidate has no real edge (wins at 50%
        # chance like a coin flip against seed noise). This scales correctly
        # with n_seeds, unlike a fixed "wins >= n_seeds-1" cutoff (which was
        # too lenient at small n_seeds, e.g. 2/3 wins passing a fixed rule).
        p_sign = _stats.binomtest(wins, args.n_seeds, p=0.5, alternative='greater').pvalue
        verdict = ("LIKELY REAL (sign test p={:.3f} < 0.05, consistent direction, "
                  "mean paired gain > 0.01)".format(p_sign)
                  if p_sign < 0.05 and paired_delta.mean() > 0.01
                  else "AMBIGUOUS (some seeds favor candidate, not statistically "
                       "distinguishable from chance at n_seeds={})".format(args.n_seeds)
                  if 0 < wins < args.n_seeds
                  else "NOT SUPPORTED (does not beat the lock in any tested seed)"
                  if wins == 0
                  else "AMBIGUOUS (wins every seed but n_seeds={} is too small for "
                       "the sign test to be significant -- run more seeds)".format(args.n_seeds))
        print(f"  verdict: {verdict}")
        summary_rows.append(dict(point=name, w_recon=wr, w_temp=wt, w_gamma=wg,
                                sens_mean=round(cand_sens.mean(), 4),
                                sens_sd=round(cand_sens.std(ddof=1), 4),
                                fp_per_day_mean=round(cand_fp.mean(), 2),
                                fp_per_day_sd=round(cand_fp.std(ddof=1), 2),
                                win_rate_vs_locked=f"{wins}/{args.n_seeds}",
                                mean_paired_delta_sens=round(float(paired_delta.mean()), 4)))

    out_path = os.path.join(args.outdir, "weight_seed_robustness_summary.csv")
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys())); w.writeheader(); w.writerows(summary_rows)

    # also dump the raw per-seed numbers for full auditability
    raw_path = os.path.join(args.outdir, "weight_seed_robustness_raw.csv")
    with open(raw_path, "w", newline="") as f:
        fieldnames = ["point", "w_recon", "w_temp", "w_gamma", "seed", "sensitivity",
                     "fp_per_day", "tp", "n_seizures"]
        w = csv.DictWriter(f, fieldnames=fieldnames); w.writeheader()
        for name, (wr, wt, wg) in POINTS:
            for seed in range(args.n_seeds):
                se, fp, tp, nz = results[name][seed]
                w.writerow(dict(point=name, w_recon=wr, w_temp=wt, w_gamma=wg,
                               seed=seed, sensitivity=round(se, 4),
                               fp_per_day=round(fp, 2), tp=tp, n_seizures=nz))

    print(f"\n  [saved] {os.path.abspath(out_path)}")
    print(f"  [saved] {os.path.abspath(raw_path)}")
    print("\n  This script does NOT auto-adopt any candidate. Paste the paired-"
         "comparison block back for review before any lock decision.\n")


if __name__ == "__main__":
    main()