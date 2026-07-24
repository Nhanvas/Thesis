"""
================================================================================
 weight_candidate_crosscheck.py  —  cand_1 across BOTH operating points +
                                     per-subject breakdown (esp. chb06)
================================================================================
WHY THIS FILE
-------------
weight_sensitivity_sweep.py (wide radius=0.30, 127 points) + weight_seed_
robustness_check.py (8-seed paired test) both point to cand_1 = (w_recon=0.40,
w_temp=0.35, w_gamma=0.25) as a real, seed-robust improvement over the locked
(0.35, 0.30, 0.35) -- 7/8 seed wins (sign test p=0.035), sits in a genuine
plateau of w_temp-heavy configurations, not an isolated spike.

BUT both of those checks only ran at ONE operating point (balanced,
mag60/pen1.0). Two things must be confirmed before any lock change:

  1. Does cand_1's gain hold at the OTHER locked operating point (high-sens,
     mag50/pen1.0, Decision #16)? A weight change that only helps one
     operating point and hurts the other is not a clean win.

  2. Is the pooled-sensitivity gain coming at chb06's expense? This is
     EXACTLY the "label-free tradeoff" pattern already documented and
     REJECTED once before (Decision #10, topology extension: pooled TP
     unchanged 57=57 because chb06 gained 2 while the other 7 lost 2 each --
     net redistribution, not a real improvement). If cand_1 shows the same
     pattern, it must be flagged the same way and NOT adopted.

WHAT THIS SCRIPT DOES
----------------------
For {locked, cand_1} x {balanced (mag60/pen1.0), high_sens (mag50/pen1.0)}
x 8 seeds x 8 subjects:
  - reports pooled sens/FP-day per (weight, operating_point), mean+/-SD over seeds
  - reports PER-SUBJECT tp (mean over 8 seeds) for both weights at both points,
    so chb06 (and every other subject) can be inspected individually, not just
    the pooled number
  - flags explicitly if chb06's mean TP goes DOWN under cand_1 while pooled
    TP goes up (the tradeoff-redistribution signature to watch for)

Does NOT auto-adopt anything. Pure CPU, cached components only (Core Rule #9).

USAGE (Cursor / CPU)
  python weight_candidate_crosscheck.py --comp_dir data/processed/components \
      --summary_dir "F:\\...\\summary" --outdir results/phaseA_appendix --n_seeds 8

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

LOCKED_W = (0.35, 0.30, 0.35)
CAND1_W = (0.40, 0.35, 0.25)
WEIGHTS = [("locked", LOCKED_W), ("cand_1", CAND1_W)]

# the two locked operating points (RESULTS_OF_RECORD.md §1/§10)
OPERATING_POINTS = [("balanced", 60.0, 1.0), ("high_sens", 50.0, 1.0)]


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
    ap = argparse.ArgumentParser(description="cand_1 cross-operating-point + "
                                             "per-subject (esp. chb06) crosscheck")
    ap.add_argument("--comp_dir", default="data/processed/components")
    ap.add_argument("--summary_dir", required=True)
    ap.add_argument("--subjs", default=",".join(TEST_SUBJS))
    ap.add_argument("--outdir", default="results/phaseA_appendix")
    ap.add_argument("--n_seeds", type=int, default=8)
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

    total = len(WEIGHTS) * len(OPERATING_POINTS) * args.n_seeds
    print(f"\n[plan] {len(WEIGHTS)} weights x {len(OPERATING_POINTS)} operating "
         f"points x {args.n_seeds} seeds x {len(subjs)} subjects = "
         f"{total * len(subjs)} total evaluations.\n")

    # raw[(wname, opname, seed)][subj] = score-dict
    raw = {}
    done = 0
    for wname, (wr, wt, wg) in WEIGHTS:
        for opname, mag, pen in OPERATING_POINTS:
            for seed in range(args.n_seeds):
                per = {}
                for s in subjs:
                    zr_i, zr_c = comps[s]["zrecon"]; zt_i, zt_c = comps[s]["ztemp"]; zg_i, zg_c = comps[s]["zgamma"]
                    ens_i = wr * zr_i + wt * zt_i + wg * zg_i
                    ens_c = wr * zr_c + wt * zt_c + wg * zg_c
                    per[s] = eval_ensemble(s, ens_i, ens_c, args.summary_dir, pen, mag, seed)
                raw[(wname, opname, seed)] = per
                se, fp, tp, nz = pooled(per, subjs)
                done += 1
                print(f"  [{done}/{total}] {wname}/{opname} seed={seed}: "
                     f"sens={se:.4f} FP/day={fp:.2f}", flush=True)

    # ---- pooled summary per (weight, operating_point), mean+/-SD over seeds ----
    print("\n" + "=" * 78)
    print("POOLED SUMMARY (mean +/- SD over seeds)")
    print("=" * 78)
    pooled_rows = []
    pooled_cache = {}
    for wname, _ in WEIGHTS:
        for opname, mag, pen in OPERATING_POINTS:
            sens_list, fp_list = [], []
            for seed in range(args.n_seeds):
                per = raw[(wname, opname, seed)]
                se, fp, tp, nz = pooled(per, subjs)
                sens_list.append(se); fp_list.append(fp)
            sens_arr, fp_arr = np.array(sens_list), np.array(fp_list)
            pooled_cache[(wname, opname)] = (sens_arr, fp_arr)
            print(f"  {wname:8s} / {opname:9s}: sens={sens_arr.mean():.4f} +/- "
                 f"{sens_arr.std(ddof=1):.4f}   FP/day={fp_arr.mean():.2f} +/- "
                 f"{fp_arr.std(ddof=1):.2f}")
            pooled_rows.append(dict(weight=wname, operating_point=opname,
                                   sens_mean=round(sens_arr.mean(), 4),
                                   sens_sd=round(sens_arr.std(ddof=1), 4),
                                   fp_per_day_mean=round(fp_arr.mean(), 2),
                                   fp_per_day_sd=round(fp_arr.std(ddof=1), 2)))

    print("\n--- paired delta (cand_1 - locked), same seed, per operating point ---")
    for opname, mag, pen in OPERATING_POINTS:
        locked_sens, locked_fp = pooled_cache[("locked", opname)]
        cand_sens, cand_fp = pooled_cache[("cand_1", opname)]
        d_sens = cand_sens - locked_sens
        wins = int(np.sum(d_sens > 0))
        from scipy import stats as _stats
        p_sign = _stats.binomtest(wins, args.n_seeds, p=0.5, alternative='greater').pvalue
        print(f"  {opname}: mean paired Δsens={d_sens.mean():+.4f}  wins={wins}/{args.n_seeds}  "
             f"sign-test p={p_sign:.3f}   mean ΔFP/day={cand_fp.mean()-locked_fp.mean():+.2f}")

    # ---- per-subject breakdown (mean TP over 8 seeds), esp. chb06 ----
    print("\n" + "=" * 78)
    print("PER-SUBJECT BREAKDOWN (mean TP over seeds) -- watch for redistribution")
    print("=" * 78)
    persubj_rows = []
    for opname, mag, pen in OPERATING_POINTS:
        print(f"\n--- {opname} (mag={mag}, pen={pen}) ---")
        print(f"  {'subject':8s} {'locked_tp':>10s} {'cand1_tp':>10s} {'delta':>7s} {'n_sz':>5s}")
        for s in subjs:
            locked_tps = [raw[("locked", opname, seed)][s]["tp"] for seed in range(args.n_seeds)]
            cand_tps = [raw[("cand_1", opname, seed)][s]["tp"] for seed in range(args.n_seeds)]
            nz = raw[("locked", opname, 0)][s]["n_seizures"]
            l_mean, c_mean = np.mean(locked_tps), np.mean(cand_tps)
            delta = c_mean - l_mean
            flag = " <-- WATCH (down under cand_1)" if delta < -0.01 else ""
            print(f"  {s:8s} {l_mean:>10.2f} {c_mean:>10.2f} {delta:>+7.2f} {nz:>5d}{flag}")
            persubj_rows.append(dict(operating_point=opname, subject=s,
                                    locked_tp_mean=round(l_mean, 3),
                                    cand1_tp_mean=round(c_mean, 3),
                                    delta=round(delta, 3), n_seizures=nz))

    chb06_deltas = [r["delta"] for r in persubj_rows if r["subject"] == "chb06"]
    other_deltas = [r["delta"] for r in persubj_rows if r["subject"] != "chb06"]
    print(f"\n[chb06 check] chb06 mean delta across operating points: "
         f"{np.mean(chb06_deltas):+.3f}   (other subjects mean delta: "
         f"{np.mean(other_deltas):+.3f})")
    if np.mean(chb06_deltas) < -0.05 and np.mean(other_deltas) > 0:
        print("[WARNING] this looks like the label-free tradeoff pattern from "
             "Decision #10 (topology extension) -- chb06 loses while others gain. "
             "Do NOT adopt cand_1 without addressing this explicitly.")
    else:
        print("[note] no clear chb06-specific tradeoff signature detected in this run.")

    out1 = os.path.join(args.outdir, "weight_candidate_crosscheck_pooled.csv")
    with open(out1, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(pooled_rows[0].keys())); w.writeheader(); w.writerows(pooled_rows)
    out2 = os.path.join(args.outdir, "weight_candidate_crosscheck_persubject.csv")
    with open(out2, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(persubj_rows[0].keys())); w.writeheader(); w.writerows(persubj_rows)
    print(f"\n  [saved] {os.path.abspath(out1)}")
    print(f"  [saved] {os.path.abspath(out2)}")
    print("\n  This script does NOT auto-adopt cand_1. Paste both summary blocks "
         "back for review before any lock decision.\n")


if __name__ == "__main__":
    main()