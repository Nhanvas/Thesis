"""
================================================================================
 stat_validation.py  —  WEEK 5: statistical validation of locked event results
================================================================================

Adds confidence intervals to the locked SzCORE event-level results so the
reported numbers carry uncertainty, as required for a credible (Q2/Q3) write-up.
Operates on the per-subject CSVs produced by szcore_eval.py at the chosen
operating points -- it does NOT re-run detection.

For each operating point it pools events across subjects (the SzCORE subject-
independent aggregation: "event-based metrics aggregate all events") and reports:

  - Event sensitivity  TP/(TP+FN)  with a Wilson 95% CI (binomial proportion)
  - Precision          TP/(TP+FP)  with a Wilson 95% CI
  - F1                 point estimate
  - FP per day         with an exact Poisson 95% CI on the false-positive count
  - Macro mean +/- SD across subjects (secondary, complements the pooled CI)

Window-level statistics (DeLong CI on AUROC, bootstrap CI on AUC-PR,
Mann-Whitney U with effect size) are already produced by evaluation_protocol.py;
this script completes the EVENT tier.

USAGE
  python stat_validation.py --ops "balanced=szcore_event_level_mag60.csv@1.0;highsens=szcore_event_level_mag70.csv@0.3"
  # paths are resolved relative to --in_dir (default results/cpd/evaluation)

OUTPUT
  locked_phaseA_event_results.csv   one row per operating point, with CIs
================================================================================
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


def wilson_ci(k, n, z=1.96):
    """Wilson 95% CI for a binomial proportion k/n."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z / denom) * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, center - half), min(1.0, center + half))


def poisson_rate_ci(k, exposure_days, alpha=0.05):
    """Exact (Garwood) Poisson 95% CI on a rate = count k over exposure (days)."""
    lo = stats.chi2.ppf(alpha / 2, 2 * k) / 2 if k > 0 else 0.0
    hi = stats.chi2.ppf(1 - alpha / 2, 2 * k + 2) / 2
    return (lo / exposure_days, hi / exposure_days)


def validate_operating_point(df, pen, label, mag_pct=None):
    """mag_pct: required when df mixes multiple mag_pct values in one file
    (e.g. mag_pen_grid_persubject.csv, which has a mag_pct column spanning
    several sweep values). szcore_event_level_mag{60,70}.csv each contain a
    single mag_pct already baked into the filename/rows, so mag_pct=None
    there is fine (kept for backward compatibility)."""
    d = df[df.pen_mult == pen]
    if "mag_pct" in df.columns:
        if mag_pct is None:
            raise ValueError(
                f"'{label}': input has a mag_pct column with multiple values "
                f"({sorted(df.mag_pct.unique())}) but no mag_pct was given in "
                f"the --ops spec -- filtering on pen alone would silently pool "
                f"rows across different mag_pct settings. Use the "
                f"label=csv@pen@mag_pct form for grid-style CSVs.")
        d = d[np.isclose(d.mag_pct, mag_pct)]
    if d.empty:
        raise ValueError(f"no rows at pen={pen}"
                         f"{f', mag_pct={mag_pct}' if mag_pct is not None else ''} "
                         f"in {label}")
    TP = int(d.tp.sum())
    FP = int(d.fp.sum())
    n_sz = int(d.n_seizures.sum())
    FN = n_sz - TP
    inter_h = float(d.n_inter_h.sum())
    inter_days = inter_h / 24.0

    sens = TP / n_sz if n_sz else float("nan")
    prec = TP / (TP + FP) if (TP + FP) else float("nan")
    f1 = (2 * prec * sens / (prec + sens)
          if prec and sens and not np.isnan(prec) else float("nan"))
    fp_day = FP / inter_days if inter_days else float("nan")

    sens_lo, sens_hi = wilson_ci(TP, n_sz)
    prec_lo, prec_hi = wilson_ci(TP, TP + FP)
    fpd_lo, fpd_hi = poisson_rate_ci(FP, inter_days)

    # macro (per-subject) mean +/- SD, complementing the pooled estimate
    sens_macro = d.sensitivity.mean()
    sens_macro_sd = d.sensitivity.std(ddof=1)

    return dict(
        operating_point=label, pen=pen, n_subjects=len(d),
        n_seizures=n_sz, TP=TP, FN=FN, FP=FP, interictal_hours=round(inter_h, 1),
        sensitivity=round(sens, 4),
        sensitivity_CI=f"[{sens_lo:.3f}, {sens_hi:.3f}]",
        sensitivity_macro=f"{sens_macro:.3f} +/- {sens_macro_sd:.3f}",
        precision=round(prec, 4),
        precision_CI=f"[{prec_lo:.3f}, {prec_hi:.3f}]",
        f1=round(f1, 4),
        fp_per_day=round(fp_day, 2),
        fp_per_day_CI=f"[{fpd_lo:.2f}, {fpd_hi:.2f}]")


def main():
    ap = argparse.ArgumentParser(description="Week 5 event-tier statistical validation")
    ap.add_argument("--in_dir", default="results/cpd/evaluation")
    ap.add_argument("--out_dir", default="results/cpd/evaluation")
    ap.add_argument("--ops",
                    default="balanced=szcore_event_level_mag60.csv@1.0;"
                            "highsens=mag_pen_grid_persubject.csv@1.0@50",
                    help="semicolon-separated specs, either label=csv@pen "
                         "(single-mag_pct files like szcore_event_level_mag*.csv) "
                         "or label=csv@pen@mag_pct (grid files with a mag_pct "
                         "column, like mag_pen_grid_persubject.csv). "
                         "Default reflects Decision #16: high-sens is now "
                         "mag50/pen1.0, not the retired mag70/pen0.3.")
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    results = []
    for spec in args.ops.split(";"):
        spec = spec.strip()
        if not spec:
            continue
        label, rest = spec.split("=", 1)
        parts = rest.split("@")
        csv_name, pen = parts[0], float(parts[1])
        mag_pct = float(parts[2]) if len(parts) > 2 else None
        path = in_dir / csv_name
        if not path.exists():
            path = Path(csv_name)        # allow absolute / relative paths too
        df = pd.read_csv(path)
        results.append(validate_operating_point(df, pen, label, mag_pct=mag_pct))

    res = pd.DataFrame(results)
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    res.to_csv(out / "locked_phaseA_event_results.csv", index=False)

    print("=" * 78)
    print("LOCKED PHASE-A EVENT RESULTS (pooled across subjects, 95% CIs)")
    print("=" * 78)
    for r in results:
        print(f"\n[{r['operating_point']}]  pen={r['pen']:g}  "
              f"({r['n_subjects']} subjects, {r['n_seizures']} seizures, "
              f"{r['interictal_hours']:.0f} interictal h)")
        print(f"  Sensitivity : {r['sensitivity']:.3f}  CI {r['sensitivity_CI']}"
              f"   (macro {r['sensitivity_macro']})")
        print(f"  Precision   : {r['precision']:.3f}  CI {r['precision_CI']}")
        print(f"  F1          : {r['f1']:.3f}")
        print(f"  FP / day    : {r['fp_per_day']:.2f}  CI {r['fp_per_day_CI']}")
        print(f"  (TP={r['TP']}  FN={r['FN']}  FP={r['FP']})")

    print(f"\nWrote: {(out / 'locked_phaseA_event_results.csv').resolve()}")


if __name__ == "__main__":
    main()