"""
================================================================================
 weight_sensitivity_sweep.py  —  ensemble-weight sensitivity check (VERIFICATION,
                                  not re-tuning)
================================================================================
WHY THIS FILE
-------------
The locked ensemble weights (w_recon=0.35, w_temp=0.30, w_gamma=0.35) were
chosen during pipeline development (pre-Phase-A, documented only as "coarse
0.1 steps, then fine sweep confirmed" in experiment_history_v11_to_v13.md,
Part 4 -- no surviving table of the sweep itself). This predates Phase A, so
it is a DIFFERENT tier of lock than mag_pct/pen_mult (Core Rule #7: "reopening
this needs explicit user sign-off first").

This script answers a narrower, safer question than "is 0.35/0.30/0.35
optimal?": **does the locked point sit on a flat/robust region of the
performance surface, or is there a neighboring point that is materially
better?** It does NOT re-tune and does NOT change any lock. It:
  1. Confirms harness fidelity first (same check as event_ablation.py) --
     the locked ensemble scores must reproduce ~0.750 sens / 38.0 FP-day
     through this exact harness before any weight-grid number is trusted.
  2. Sweeps a LOCAL neighborhood around (0.35, 0.30, 0.35) on the 2-simplex
     (step=0.05, sum=1 exactly), at the LOCKED operating point only
     (pen=1.0, mag=60 -- balanced). This is deliberately NOT a full re-tune
     of pen/mag together with weights (that combinatorial explosion is out
     of scope and would take hours); it isolates the weight question alone.
  3. Reports the full grid + flags the locked point's rank + flags any
     point that beats it by more than a stated margin (both on sensitivity
     AND without a corresponding FP/day blowup).
  4. Explicitly does NOT auto-select the "best" grid point as a
     replacement. If something beats the lock, it is reported for you and
     Boti to review together -- not auto-adopted.

WHAT THIS SCRIPT DOES NOT DO
-----------------------------
  - Does NOT sweep pen_mult or min_mag_pct jointly with weights (already
    swept separately in mag_pen_grid_sweep.py; combining both here would be
    a much larger, slower grid with no clear added value for THIS question).
  - Does NOT touch upstream GAE/LSTM/gamma training. Pure CPU, cached
    components only (Core Rule #9).
  - Does NOT overwrite any locked CSV. Writes to a separate output file.

CAVEAT (same as event_ablation.py): the exported per-component z-scores come
from a fresh GPU run and do NOT bit-reproduce the locked ensemble exactly.
CONFIRMED IN PRACTICE (2026-07 run): the direct-file-read locked ensemble
scores 0.750/38.0 exactly, but the SAME weights (0.35,0.30,0.35) REBUILT from
the 3 separate cached components scores 0.7105/39.25 in the grid -- a real
~3-TP closure gap, not a bug. Consequence: NEVER compare a grid row's absolute
sensitivity to the file-read 0.750. All grid rows (including the locked-weight
row) share this same gap, so RELATIVE ranking among grid rows remains valid;
only the grid's own locked-weight row is a valid baseline for grid comparisons.

PROGRESS: this loop takes a long time (each grid point = 8 x build_timeline +
PELT). A per-point progress line is printed as it runs so you can see it is
alive rather than silently running for hours (added after a ~1h run gave no
visible output until completion).

USAGE (Cursor / CPU)
  python weight_sensitivity_sweep.py --comp_dir data/processed/components \
      --scores_dir results/cpd/scores --summary_dir "F:\\...\\summary" \
      --outdir results/phaseA_appendix --step 0.05 --radius 0.15

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

# locked reference point (Proposed_solution_updated_v4.md §5; experiment_history
# v11-v13 Part 4) -- what we are checking the neighborhood of, NOT re-deriving.
LOCKED_W = (0.35, 0.30, 0.35)
LOCKED_REF = {"sensitivity": 0.750, "fp_per_day": 38.0}   # balanced mag60/pen1.0
PEN, MAG = 1.0, 60.0   # balanced operating point only -- do not also sweep pen/mag here


def simplex_neighbors(center, step, radius):
    """All (wr, wt, wg) with wr+wt+wg=1, each on the `step` grid, within
    L1 radius of `center`. Includes the center itself. Deterministic order."""
    cr, ct, cg = center
    lo_r, hi_r = max(0.0, cr - radius), min(1.0, cr + radius)
    lo_t, hi_t = max(0.0, ct - radius), min(1.0, ct + radius)
    pts = []
    n_steps = int(round(radius / step))
    grid = [round(step * k, 10) for k in range(-n_steps, n_steps + 1)]
    for dr in grid:
        wr = round(cr + dr, 10)
        if wr < 0 or wr > 1:
            continue
        for dt in grid:
            wt = round(ct + dt, 10)
            if wt < 0 or wt > 1:
                continue
            wg = round(1.0 - wr - wt, 10)
            if wg < -1e-9 or wg > 1 + 1e-9:
                continue
            wg = max(0.0, min(1.0, wg))
            if abs((wr + wt + wg) - 1.0) > 1e-6:
                continue
            if abs(wg - cg) > radius + 1e-9:
                continue  # keep the sweep genuinely local in all 3 coords
            pts.append((wr, wt, wg))
    # de-dup (rounding can create near-duplicates) and sort for determinism
    seen, out = set(), []
    for p in pts:
        key = (round(p[0], 6), round(p[1], 6), round(p[2], 6))
        if key not in seen:
            seen.add(key)
            out.append(p)
    out.sort()
    return out


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
    ap = argparse.ArgumentParser(description="Ensemble-weight sensitivity check "
                                             "(verification, not re-tuning)")
    ap.add_argument("--comp_dir", default="data/processed/components")
    ap.add_argument("--scores_dir", default="results/cpd/scores")
    ap.add_argument("--summary_dir", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--subjs", default=",".join(TEST_SUBJS))
    ap.add_argument("--outdir", default="results/phaseA_appendix")
    ap.add_argument("--step", type=float, default=0.05,
                    help="grid step on each weight coordinate")
    ap.add_argument("--radius", type=float, default=0.15,
                    help="L1 neighborhood radius around the locked weights "
                         "(0.15 => e.g. w_recon in [0.20, 0.50])")
    ap.add_argument("--beat_margin", type=float, default=0.02,
                    help="a grid point must beat the locked sensitivity by "
                         "more than this AND not increase FP/day by more "
                         "than beat_fp_margin to be flagged as 'materially better'")
    ap.add_argument("--beat_fp_margin", type=float, default=3.0,
                    help="max FP/day increase tolerated for a 'materially "
                         "better' flag (absolute FP/day units)")
    args = ap.parse_args()
    subjs = args.subjs.split(",")
    os.makedirs(args.outdir, exist_ok=True)
    print(f"[diag] outputs -> {os.path.abspath(args.outdir)}")

    # ---- robust comp_dir discovery (mirrors event_ablation.py) ----
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
    if not subjs:
        print("[error] no subjects with complete components found -- aborting.")
        return

    # ---- MANDATORY harness-fidelity check (same as event_ablation.py) ----
    print("\n[fidelity] evaluating LOCKED ens through this harness "
          f"(expect ~{LOCKED_REF['sensitivity']:.3f} / {LOCKED_REF['fp_per_day']:.1f})")
    locked_per = {}
    for s in subjs:
        ei = os.path.join(args.scores_dir, f"{s}_ens_inter.npy")
        ec = os.path.join(args.scores_dir, f"{s}_ens_ictal.npy")
        if os.path.exists(ei) and os.path.exists(ec):
            locked_per[s] = eval_ensemble(s, np.load(ei).astype(np.float64),
                                          np.load(ec).astype(np.float64),
                                          args.summary_dir, PEN, MAG, args.seed)
    file_read_sens = None
    if locked_per:
        se, fp, tp, nz, fpn = pooled(locked_per, list(locked_per))
        file_read_sens = se
        print(f"[fidelity] LOCKED ens (read directly from {args.scores_dir}): "
              f"sens={se:.3f} ({tp}/{nz})  FP/day={fp:.1f}   "
              f"(ref {LOCKED_REF['sensitivity']}/{LOCKED_REF['fp_per_day']})")
        drift_vs_ref = abs(se - LOCKED_REF["sensitivity"])
        if drift_vs_ref > 0.03:
            print(f"[WARNING] the locked scores file itself drifts {drift_vs_ref:.3f} "
                  f"from LOCKED_REF -- check --scores_dir points to the right cache.")
    else:
        print(f"[WARNING] {args.scores_dir}/{{subj}}_ens_inter.npy not found -- cannot "
              f"run this direct-file check at all.")

    # ---- build the local weight grid and evaluate every point ----
    grid = simplex_neighbors(LOCKED_W, args.step, args.radius)
    print(f"\n[grid] {len(grid)} weight combinations within L1 radius "
          f"{args.radius} of locked ({LOCKED_W[0]:.2f}, {LOCKED_W[1]:.2f}, "
          f"{LOCKED_W[2]:.2f}), step={args.step}")
    print(f"[grid] fixed operating point: pen={PEN}, mag={MAG} (balanced -- "
          f"NOT re-sweeping pen/mag here, see Decision #16 for that)")
    print(f"[grid] IMPORTANT: every row below, INCLUDING the row at exactly the "
          f"locked weights, is an ensemble REBUILT from the 3 separate cached "
          f"components (zrecon/ztemp/zgamma), not read from {args.scores_dir}. "
          f"Per Core Rule #7 / event_ablation.py's own caveat, GPU re-export is "
          f"NOT bit-reproducible -- the grid's own locked-weight row can "
          f"legitimately differ from the direct-file-read number above. This is "
          f"a KNOWN closure gap, not a new bug. The grid is therefore only valid "
          f"for RELATIVE ranking among grid rows (all built the same way, so the "
          f"gap affects them equally) -- do NOT compare a grid row's absolute "
          f"sensitivity to the file-read 0.750 above; compare grid rows to each "
          f"other and to the grid's own locked-weight row instead.")

    rows = []
    locked_row = None
    for gi, (wr, wt, wg) in enumerate(grid, 1):
        per = {}
        for s in subjs:
            zr_i, zr_c = comps[s]["zrecon"]; zt_i, zt_c = comps[s]["ztemp"]; zg_i, zg_c = comps[s]["zgamma"]
            ens_i = wr * zr_i + wt * zt_i + wg * zg_i
            ens_c = wr * zr_c + wt * zt_c + wg * zg_c
            per[s] = eval_ensemble(s, ens_i, ens_c, args.summary_dir, PEN, MAG, args.seed)
        se, fp, tp, nz, fpn = pooled(per, subjs)
        is_locked_point = (abs(wr - LOCKED_W[0]) < 1e-6 and
                          abs(wt - LOCKED_W[1]) < 1e-6 and
                          abs(wg - LOCKED_W[2]) < 1e-6)
        row = dict(w_recon=wr, w_temp=wt, w_gamma=wg,
                  sensitivity=round(se, 4), tp=tp, n_seizures=nz,
                  fp_per_day=round(fp, 2), is_locked_point=is_locked_point)
        rows.append(row)
        if is_locked_point:
            locked_row = row
        print(f"  [{gi}/{len(grid)}] w=({wr:.2f},{wt:.2f},{wg:.2f})  "
             f"sens={se:.4f}  FP/day={fp:.2f}"
             f"{'  <- LOCKED POINT' if is_locked_point else ''}", flush=True)

    if locked_row is None:
        print("[WARNING] the exact locked point (0.35,0.30,0.35) was not generated "
              "by the grid step/radius chosen -- widen --radius or check --step "
              "divides evenly. Cannot rank the lock without it.")
    else:
        rows_sorted = sorted(rows, key=lambda r: -r["sensitivity"])
        rank = next(i for i, r in enumerate(rows_sorted, 1)
                   if r["w_recon"] == locked_row["w_recon"]
                   and r["w_temp"] == locked_row["w_temp"])
        print(f"\n[rank] locked point (0.35,0.30,0.35): sensitivity={locked_row['sensitivity']:.4f}, "
              f"FP/day={locked_row['fp_per_day']:.2f}  -- rank {rank}/{len(rows)} "
              f"by sensitivity in this local grid")

        # flag any point that is "materially better": higher sensitivity by more
        # than beat_margin AND FP/day does not increase by more than beat_fp_margin
        beats = [r for r in rows
                if not r["is_locked_point"]
                and r["sensitivity"] - locked_row["sensitivity"] > args.beat_margin
                and r["fp_per_day"] - locked_row["fp_per_day"] <= args.beat_fp_margin]
        beats.sort(key=lambda r: -r["sensitivity"])
        print(f"\n[flag] points beating the lock by >{args.beat_margin:.2f} sensitivity "
              f"AND FP/day increase <={args.beat_fp_margin:.1f}: {len(beats)} found")
        for r in beats[:10]:
            print(f"    w=({r['w_recon']:.2f},{r['w_temp']:.2f},{r['w_gamma']:.2f})  "
                 f"sens={r['sensitivity']:.4f}  FP/day={r['fp_per_day']:.2f}  "
                 f"(Δsens={r['sensitivity']-locked_row['sensitivity']:+.4f}, "
                 f"ΔFP/day={r['fp_per_day']-locked_row['fp_per_day']:+.2f})")
        if not beats:
            print("    (none -- the locked point is NOT dominated within this "
                 "local neighborhood under this criterion)")
        print("\n[note] This script does NOT auto-adopt any of the above. If "
             "'beats' is non-empty, review with Boti before considering any "
             "change -- this predates Phase A and needs explicit sign-off "
             "per Core Rule #7.")

    # ---- write full grid CSV ----
    out_path = os.path.join(args.outdir, "weight_sensitivity_grid.csv")
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"\n  [saved] {os.path.abspath(out_path)}")
    print("\n  Paste the [fidelity], [rank], and [flag] lines back for review.\n")


if __name__ == "__main__":
    main()