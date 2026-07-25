"""
================================================================================
 event_ablation.py  (Phase B / Week 7)
   Leave-one-signal-out ablation at the EVENT tier (SzCORE), complementing the
   window-AUROC ablation already in auroc_verification.csv.
================================================================================
Rebuilds the ensemble from the exported per-component z-scores and evaluates
each configuration through the AUTHORITATIVE locked scoring path
(szcore_eval.build_timeline_masked -> V14.detect_changepoints -> cps_to_events
-> score_szcore/timescoring) at the balanced operating point (pen=1.0, mag60),
seeded to match the locked run.

CONFIGS (weights renormalised among kept views; CPD penalty/mag are scale-adaptive)
  full(3-view)   = 0.40 zr + 0.35 zt + 0.25 zg      (Decision #19 weight)
  drop_recon     = (0.35 zt + 0.25 zg)/0.60
  drop_temporal  = (0.40 zr + 0.25 zg)/0.65
  drop_gamma     = (0.40 zr + 0.35 zt)/0.75
  recon_only / temporal_only / gamma_only

NOTE (2026-07/08, re-run under the Decision #19 weight):
  Under the NEW weight there is NO separate GPU ensemble cache to disagree with:
  the locked NEW-weight numbers (RESULTS_OF_RECORD §1) are THEMSELVES built from
  these same per-component z-scores on CPU (same path as duration_stratified_
  sensitivity.py, which reproduces the locked pooled sensitivity exactly). So
  'full(3-view)' here is EXPECTED to match the new locked balanced 0.750 (57/76)
  exactly -- this is both the harness-fidelity check AND removes the old
  "0.711 drifts from 0.750" caveat that applied only under the old-weight path.
  The old-weight ens cache (results/cpd/scores/*.npy) is still evaluated below but
  ONLY as a historical cross-check; it is NOT the reference for the new weight.
  ABLATION DELTAS (full vs leave-one-out) are now measured at the CURRENT weight,
  so the table describes the system the thesis actually reports.

USAGE (Cursor / CPU)
  python event_ablation.py --comp_dir data/processed/components \
      --scores_dir results/cpd/scores --summary_dir "F:\\...\\summary" \
      --outdir results/phaseB
Requires szcore_eval.py, evaluation_protocol.py, cpd_pipeline_v14.py, timescoring.
================================================================================
"""
import argparse
import csv
import os
import numpy as np

import szcore_eval as SE
import cpd_pipeline_v14 as V14

TEST_SUBJS = SE.TEST_SUBJS
WIN_SEC = SE.WIN_SEC
WR, WT, WG = 0.40, 0.35, 0.25          # Decision #19 weight (was 0.35, 0.30, 0.35)
LOCKED_REF = {"sensitivity": 0.750, "fp_per_day": 39.77}   # NEW-weight balanced mag60 (RESULTS_OF_RECORD §1)

CONFIGS = {
    "full(3-view)":  lambda r, t, g: WR * r + WT * t + WG * g,
    "drop_recon":    lambda r, t, g: (WT * t + WG * g) / (WT + WG),
    "drop_temporal": lambda r, t, g: (WR * r + WG * g) / (WR + WG),
    "drop_gamma":    lambda r, t, g: (WR * r + WT * t) / (WR + WT),
    "recon_only":    lambda r, t, g: r,
    "temporal_only": lambda r, t, g: t,
    "gamma_only":    lambda r, t, g: g,
}


def load_comp(comp_dir, subj):
    def L(name, split):
        p = os.path.join(comp_dir, f"{name}_{subj}_{split}.npy")
        return np.load(p).astype(np.float64) if os.path.exists(p) else None
    return {k: (L(k, "inter"), L(k, "ictal")) for k in ("zrecon", "ztemp", "zgamma")}


def eval_ensemble(subj, ens_in, ens_ic, summary_dir, pen, min_mag_pct, seed=0):
    np.random.seed(seed)     # mirror szcore_eval.main() determinism
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
            fp / h * 24 if h else float("nan"), tp, nz, fp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--comp_dir", default="data/processed/components")
    ap.add_argument("--scores_dir", default="results/cpd/scores")
    ap.add_argument("--summary_dir", default=".")
    ap.add_argument("--pen", type=float, default=1.0)
    ap.add_argument("--min_mag_pct", type=float, default=60)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--subjs", default=",".join(TEST_SUBJS))
    ap.add_argument("--outdir", default="results/phaseB")
    args = ap.parse_args()
    subjs = args.subjs.split(",")
    os.makedirs(args.outdir, exist_ok=True)
    print(f"[diag] outputs -> {os.path.abspath(args.outdir)}")
    # robust comp_dir discovery (guard against download path surprises)
    import glob as _glob
    probe = f"zrecon_{subjs[0]}_inter.npy"
    if not os.path.exists(os.path.join(args.comp_dir, probe)):
        hits = _glob.glob(os.path.join(".", "**", probe), recursive=True)
        if hits:
            args.comp_dir = os.path.dirname(hits[0])
            print(f"[diag] components not at default; using {os.path.abspath(args.comp_dir)}")
        else:
            print(f"[diag] WARNING: {probe} not found anywhere under cwd; check --comp_dir")
    print(f"[diag] components dir: {os.path.abspath(args.comp_dir)}")

    # ---- component alignment + presence ----
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

    # ---- OLD-WEIGHT ens cache: historical cross-check only (NOT the new reference) ----
    print("\n[old-weight x-check] evaluating the OLD-weight ens cache through this harness")
    print("                     (informational only; the NEW-weight reference is 'full(3-view)' below)")
    locked_per = {}
    for s in subjs:
        ei = os.path.join(args.scores_dir, f"{s}_ens_inter.npy")
        ec = os.path.join(args.scores_dir, f"{s}_ens_ictal.npy")
        if os.path.exists(ei) and os.path.exists(ec):
            locked_per[s] = eval_ensemble(s, np.load(ei).astype(np.float64),
                                          np.load(ec).astype(np.float64),
                                          args.summary_dir, args.pen, args.min_mag_pct, args.seed)
    if locked_per:
        se, fp, tp, nz, fpn = pooled(locked_per, list(locked_per))
        print(f"[old-weight x-check] OLD ens cache: sens={se:.3f} ({tp}/{nz})  FP/day={fp:.1f}   "
              f"(this is the OLD 0.35/0.30/0.35 ensemble; expect it NOT to equal the new numbers)")

    # ---- run all configs ----
    results = {}
    for name, fn in CONFIGS.items():
        per = {}
        for s in subjs:
            zr_i, zr_c = comps[s]["zrecon"]; zt_i, zt_c = comps[s]["ztemp"]; zg_i, zg_c = comps[s]["zgamma"]
            ens_i = fn(zr_i, zt_i, zg_i); ens_c = fn(zr_c, zt_c, zg_c)
            per[s] = eval_ensemble(s, ens_i, ens_c, args.summary_dir,
                                   args.pen, args.min_mag_pct, args.seed)
        results[name] = per

    # ---- report ----
    full_sens = pooled(results["full(3-view)"], subjs)[0]
    full_tp = pooled(results["full(3-view)"], subjs)[2]
    full_nz = pooled(results["full(3-view)"], subjs)[3]
    # NEW-weight fidelity: full(3-view) from components should reproduce the locked balanced (0.750 = 57/76)
    ref_s = LOCKED_REF["sensitivity"]
    match = "MATCH" if abs(full_sens - ref_s) < 1e-3 else f"DRIFT {full_sens - ref_s:+.4f}"
    print(f"\n[fidelity NEW weight] full(3-view) = {full_sens:.4f} ({full_tp}/{full_nz})   "
          f"vs locked balanced {ref_s} (57/76)  ->  {match}")
    if match != "MATCH":
        print("   (if DRIFT: the component set here is not the one that produced §1; report the drift honestly,")
        print("    deltas remain valid within this self-consistent set — same handling as the old-weight run.)")
    print("\nEVENT-TIER ABLATION (balanced pen=%.1f / mag%d, pooled over %d subjects)"
          % (args.pen, args.min_mag_pct, len(subjs)))
    print(f"{'config':<15}{'sens':>8}{'TP/nSz':>10}{'FP/day':>9}{'Δsens vs full':>15}")
    print("-" * 57)
    rows = []
    for name in CONFIGS:
        se, fp, tp, nz, fpn = pooled(results[name], subjs)
        dse = se - full_sens
        tag = "" if name == "full(3-view)" else f"{dse:+.3f}"
        print(f"{name:<15}{se:>8.3f}{f'{tp}/{nz}':>10}{fp:>9.1f}{tag:>15}")
        rows.append(dict(config=name, sensitivity=round(se, 4), tp=tp, n_seizures=nz,
                         fp_per_day=round(fp, 2), delta_sens_vs_full=round(dse, 4)))
    print("-" * 57)
    # cost of dropping each view = full - drop_X
    print("\nCONTRIBUTION (sensitivity lost by removing each view):")
    for view, drop in [("recon(GAE)", "drop_recon"), ("temporal", "drop_temporal"), ("gamma", "drop_gamma")]:
        cost = full_sens - pooled(results[drop], subjs)[0]
        print(f"  remove {view:<12}: Δsens = {cost:+.3f}")

    # per-subject full-vs-drop for the write-up
    with open(os.path.join(args.outdir, "event_ablation_pooled.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    persub = []
    for name in CONFIGS:
        for s in subjs:
            r = results[name][s]
            persub.append(dict(config=name, subject=s, tp=r["tp"], fp=r["fp"],
                               n_seizures=r["n_seizures"],
                               sensitivity=round(r["tp"] / r["n_seizures"], 3) if r["n_seizures"] else 0))
    with open(os.path.join(args.outdir, "event_ablation_persubject.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(persub[0].keys())); w.writeheader(); w.writerows(persub)
    print(f"\n  [saved] {os.path.abspath(os.path.join(args.outdir, 'event_ablation_pooled.csv'))}")
    print(f"  [saved] {os.path.abspath(os.path.join(args.outdir, 'event_ablation_persubject.csv'))}")
    print("\n  Paste the ABLATION table + CONTRIBUTION lines + the [fidelity] line back to me.\n")


if __name__ == "__main__":
    main()