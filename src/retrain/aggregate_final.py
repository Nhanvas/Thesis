"""
aggregate_final.py — gather per-seed raw grids -> Pareto frontier, option-A
operating points, 95% CIs, and 5-seed mean+/-SD. Runs on Cursor (CPU only; no
torch / torch_geometric / timescoring needed — the heavy GPU work is already
baked into the final_eval_seed*.csv files).

Two modes, chosen automatically by what CSVs are present:

  * ONLY seed 42 present  -> "frontier" mode: print the seed-42 Pareto frontier
    and the two option-A operating points, and print the exact --only_mags to use
    for the remaining seeds in phase 2. Writes final_eval_frontier_seed42.csv.

  * seed 42 + >=1 other   -> "lock" mode: full report() -> final_eval_locked.csv
    (drop-in for RESULTS_OF_RECORD §16) + multiseed + window-AUROC CSVs.

USAGE (Cursor)
  python aggregate_final.py --in_dir results/retrain --weights 0.3334,0.3333,0.3333 \
      --out_dir results/retrain
"""
import argparse
import csv
import glob
import os
from pathlib import Path

import numpy as np

import final_eval as FE
import retrain_io as IO


def load_seed_csvs(in_dir):
    """-> (all_persubj {seed: rows}, all_waur {seed: {subj: auroc}})."""
    all_ps, all_wa = {}, {}
    files = sorted(glob.glob(os.path.join(in_dir, "final_eval_seed*.csv")))
    if not files:
        raise SystemExit(f"no final_eval_seed*.csv in {in_dir}")
    for fp in files:
        with open(fp) as f:
            rows = list(csv.DictReader(f))
        for r in rows:
            sd = int(float(r["seed"]))
            row = dict(subject=r["subject"], mag_pct=float(r["mag_pct"]),
                       pen_mult=float(r["pen_mult"]), tp=int(float(r["tp"])),
                       fp=int(float(r["fp"])), n_seizures=int(float(r["n_seizures"])),
                       n_inter_h=float(r["n_inter_h"]))
            all_ps.setdefault(sd, []).append(row)
            wa = r.get("window_auroc", "")
            if wa not in ("", "nan"):
                all_wa.setdefault(sd, {})[r["subject"]] = float(wa)
        print(f"  loaded {os.path.basename(fp)}: {len(rows)} rows")
    return all_ps, all_wa


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_dir", default="results/retrain")
    ap.add_argument("--weights", required=True, help="'wr,wt,wg' used for the run")
    ap.add_argument("--out_dir", default="results/retrain")
    ap.add_argument("--ensemble_tag", type=int, default=99,
                    help="seed tag of the deep seed-ensemble (from build_seed_ensemble)")
    a = ap.parse_args()
    weights = tuple(float(x) for x in a.weights.split(","))
    ETAG = a.ensemble_tag

    all_ps, all_wa = load_seed_csvs(a.in_dir)
    deep = all_ps.pop(ETAG, None)          # deep ensemble handled separately
    deep_wa = all_wa.pop(ETAG, None)
    seeds = sorted(all_ps)                  # single-seed variance seeds only
    print(f"\nsingle-seed(s) present: {seeds}"
          f"{'  + deep-ensemble seed ' + str(ETAG) if deep else ''}")

    # ---- deep-ensemble headline (primary), if present ----
    if deep is not None and len({r['mag_pct'] for r in deep}) >= len(FE.MAG_PCTS):
        deep_headline(deep, deep_wa or {}, weights, a.out_dir, ETAG)

    if IO.CANON_SEED not in all_ps:
        if deep is not None:
            return
        raise SystemExit("seed 42 (canonical) is required — run phase 1 first")

    # ---- frontier mode (only seed 42) ----
    if len(seeds) == 1:
        pooled = IO.mark_pareto(FE.pool_grid(all_ps[IO.CANON_SEED]))
        sel = IO.select_operating_points_optionA(pooled, target_fp=40.0, fp_cap=75.0)
        bal, hs = sel["balanced"], sel["highsens"]
        print("\n=== seed-42 Pareto frontier (sorted by FP/day) ===")
        for r in sorted([r for r in pooled if r["on_pareto_frontier"]],
                        key=lambda r: r["fp_per_day"]):
            tag = ""
            if (r["mag_pct"], r["pen_mult"]) == (bal["mag_pct"], bal["pen_mult"]):
                tag += "  <- BALANCED"
            if (r["mag_pct"], r["pen_mult"]) == (hs["mag_pct"], hs["pen_mult"]):
                tag += "  <- HIGH-SENS"
            print(f"  mag{r['mag_pct']:g}/pen{r['pen_mult']:g}: "
                  f"sens={r['sensitivity']:.3f} FP/day={r['fp_per_day']:.2f}{tag}")
        out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
        with open(out / "final_eval_frontier_seed42.csv", "w", newline="") as f:
            cols = ["mag_pct", "pen_mult", "TP", "FN", "FP", "n_seizures",
                    "interictal_hours", "sensitivity", "precision", "f1",
                    "fp_per_day", "on_pareto_frontier"]
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader()
            w.writerows(sorted(pooled, key=lambda r: (r["mag_pct"], r["pen_mult"])))
        mags = sorted({bal["mag_pct"], hs["mag_pct"]})
        print(f"\n[PHASE 2] run the other seeds with:")
        print(f"    --only_mags {','.join(f'{m:g}' for m in mags)}")
        print(f"  (balanced = mag{bal['mag_pct']:g}/pen{bal['pen_mult']:g}, "
              f"high-sens = mag{hs['mag_pct']:g}/pen{hs['pen_mult']:g})")
        return

    # ---- lock mode (>=2 single seeds incl. 42): fixed-op mean±SD ----
    FE.report(all_ps, all_wa, weights, a.out_dir)

    # ---- diagnostic: per-seed option-A (each seed picks its OWN op point) ----
    perseed_optionA(all_ps, seeds, a.out_dir)


def deep_headline(deep_rows, deep_wa, weights, out_dir, tag):
    """Primary headline for the deep seed-ensemble: frontier + option-A + 95% CIs."""
    pooled = IO.mark_pareto(FE.pool_grid(deep_rows))
    sel = IO.select_operating_points_optionA(pooled, target_fp=40.0, fp_cap=75.0)
    bal, hs = sel["balanced"], sel["highsens"]
    bal_ci = FE.pooled_point_ci(deep_rows, bal["mag_pct"], bal["pen_mult"], "balanced")
    hs_ci = FE.pooled_point_ci(deep_rows, hs["mag_pct"], hs["pen_mult"], "high-sensitivity")
    macro_wa = float(np.nanmean(list(deep_wa.values()))) if deep_wa else float("nan")
    print("\n" + "=" * 74)
    print(f"PRIMARY HEADLINE — DEEP SEED-ENSEMBLE (mean of seeds, tag {tag})")
    print("=" * 74)
    print(f"weights (recon,temporal,gamma) = ({weights[0]:.2f},{weights[1]:.2f},{weights[2]:.2f})")
    for lbl, ci in [("BALANCED", bal_ci), ("HIGH-SENS", hs_ci)]:
        print(f"\n[{lbl}]  mag{ci['mag_pct']:g}/pen{ci['pen']:g}  "
              f"(TP/FN/FP {ci['TP']}/{ci['FN']}/{ci['FP']}, {ci['n_seizures']} sz)")
        print(f"  sensitivity {ci['sensitivity']:.3f} {ci['sensitivity_CI']}"
              f"  |  FP/day {ci['fp_per_day']:.2f} {ci['fp_per_day_CI']}"
              f"  |  prec {ci['precision']:.3f}  F1 {ci['f1']:.3f}")
    print(f"\nwindow macro AUROC (deep ensemble) = {macro_wa:.3f}")
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    with open(out / "final_eval_deepensemble_locked.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(bal_ci.keys())); w.writeheader()
        w.writerow(bal_ci); w.writerow(hs_ci)
    with open(out / "final_eval_deepensemble_frontier.csv", "w", newline="") as f:
        cols = ["mag_pct", "pen_mult", "TP", "FN", "FP", "n_seizures",
                "interictal_hours", "sensitivity", "precision", "f1",
                "fp_per_day", "on_pareto_frontier"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader()
        w.writerows(sorted(pooled, key=lambda r: (r["mag_pct"], r["pen_mult"])))
    print(f"[saved] {out / 'final_eval_deepensemble_locked.csv'}")


def perseed_optionA(all_ps, seeds, out_dir):
    """For each seed with a FULL grid, apply the option-A rule to ITS OWN frontier
    and report the resulting sensitivity. Separates genuine model-seed variance
    from the artifact of fixing the operating point on the canonical seed."""
    full = [sd for sd in seeds
            if len({r["mag_pct"] for r in all_ps[sd]}) >= len(FE.MAG_PCTS)]
    if len(full) < 2:
        print("\n[per-seed option-A] skipped — seeds 1-4 need the FULL grid "
              "(re-run score_ens without --only_mags).")
        return
    print("\n" + "=" * 74)
    print("DIAGNOSTIC — per-seed option-A (each seed at ITS OWN chosen op point)")
    print("=" * 74)
    bal_s, hs_s, out_rows = [], [], []
    for sd in full:
        pooled = IO.mark_pareto(FE.pool_grid(all_ps[sd]))
        sel = IO.select_operating_points_optionA(pooled, target_fp=40.0, fp_cap=75.0)
        b, h = sel["balanced"], sel["highsens"]
        bal_s.append(b["sensitivity"]); hs_s.append(h["sensitivity"])
        out_rows.append((sd, b, h))
        print(f"  seed {sd}:  balanced mag{b['mag_pct']:g}/pen{b['pen_mult']:g} "
              f"sens={b['sensitivity']:.3f} FP/day={b['fp_per_day']:.1f}  |  "
              f"high-sens mag{h['mag_pct']:g}/pen{h['pen_mult']:g} "
              f"sens={h['sensitivity']:.3f} FP/day={h['fp_per_day']:.1f}")
    bal_s, hs_s = np.array(bal_s), np.array(hs_s)
    print(f"\n  per-seed-optimal balanced  sens = {bal_s.mean():.3f} +/- {bal_s.std(ddof=1):.3f}")
    print(f"  per-seed-optimal high-sens sens = {hs_s.mean():.3f} +/- {hs_s.std(ddof=1):.3f}")
    print("  (compare with the fixed-op mean±SD above: if these are higher/tighter,"
          " the fixed-op SD was inflated by op-point transfer, not model variance)")
    out = Path(out_dir)
    with open(out / "final_eval_perseed_optionA.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["seed", "op", "mag_pct", "pen_mult", "sensitivity", "fp_per_day"])
        for sd, b, h in out_rows:
            w.writerow([sd, "balanced", b["mag_pct"], b["pen_mult"],
                        f"{b['sensitivity']:.4f}", f"{b['fp_per_day']:.3f}"])
            w.writerow([sd, "high-sensitivity", h["mag_pct"], h["pen_mult"],
                        f"{h['sensitivity']:.4f}", f"{h['fp_per_day']:.3f}"])
    print(f"[saved] {out / 'final_eval_perseed_optionA.csv'}")


if __name__ == "__main__":
    main()
