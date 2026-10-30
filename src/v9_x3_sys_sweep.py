#!/usr/bin/env python
"""
v9_x3_sys_sweep.py -- V9-X3 follow-up analysis (no training; reuses the already-cached GAE/B4
distance dumps from the main run). System-stage k-sweep (p3_levers.sys_sweep /
v9_e1b_calibrate.sys_sweep's own construction, unchanged: sweep k itself, not top-p, around each
case's OWN already-calibrated k0, through the per-patient budget AND the cpd localizer every
time) for all 3 arms -- GAE-CV, kNN-LOO, GAE+kNN-CV -- then matched-FP/day per-case sensitivity
and paired bootstrap, read-only reuse of v9_e2_veto.py's own two helpers
(per_patient_sens_at_fa, paired_boot -- duplicated here, not imported, for the same reason
v9_x3_aggregate.py duplicates paired_boot: v9_e2_veto.py pulls in unrelated heavy raw-EEG code).

Each case's own k0 is its already-calibrated operating point from the main V9-X3 run: k_G per
fold (GAE-CV), k_B4(loo, case) (kNN-LOO), k_F per fold (GAE+kNN-CV) -- results/v9_x3/
fold{k}_seed42_calibration.json, b4_loo_calibration.json, fold{k}_seed42_F_calibration.json.
K_MULT grid = v9_e1b_calibrate.K_MULT (13 log-spaced multipliers, unchanged).

Part A: matched-FP/day sensitivity (20.0, 27.5 FP/day) -- per_patient_sens_at_fa(SYS, subs, arm,
target): pools tp/fp/n_ref/nonict_h over `subs` at each k_mult to find the pooled-FA-matched
k_mult bracket, then interpolates EACH case's own sensitivity in that bracket (so every case is
read at the SAME relative k_mult, not a per-case-matched FP/day -- the established convention,
e.g. v9_e1b_calibrate.matched_curve_k, v9_e2_veto.per_patient_sens_at_fa). Paired bootstrap
(10,000, v9_e2_veto.paired_boot's construction) of the per-case sensitivity difference, all 24
cases, for GAE-kNN, GAE+kNN-GAE, GAE+kNN-kNN, at each target.

Part B: paired bootstrap of per-case F1 and precision at EACH ARM'S OWN point (no sweep -- read
straight from results/v9_x3/combined_per_subject.csv, localized stage), same 3 pairs.

Run: python src/v9_x3_sys_sweep.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB", ROOT / "src" / "phaseC",
          ROOT / "src" / "dataprep"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import p2_scalars as PS                # noqa: E402
import p3_levers as P3L                # noqa: E402
import v9_e1_baselines as V9E1         # noqa: E402
import v9_e1b_calibrate as V9E1B       # noqa: E402
import v9_x3_cv_eval as X3             # noqa: E402
import v9_x3_knn_b4 as KB4             # noqa: E402

OUT = ROOT / "results" / "v9_x3"
SMOOTH, FLOOR, CAP = 5, 0.005, 0.02
K_MULT = V9E1B.K_MULT
FP_TARGETS = [20.0, 27.5]
ALL24 = [f"chb{i:02d}" for i in range(1, 25)]
SUBSET_ALL24 = ALL24


# ------------------------------------------------------------------------------------- sweep
def sweep_case(ctx, x, m, k0):
    sm_m = PS.smoothed(ctx, m, SMOOTH)
    sm_x = PS.smoothed(ctx, x, SMOOTH)
    rows = []
    for mult in K_MULT:
        k = k0 * mult
        q = P3L.q_of(sm_m, k)
        top = float(np.clip(q, FLOOR, max(CAP, FLOOR)))
        det = PS.d1_events(ctx, x, SMOOTH, top)
        thr = np.nanquantile(sm_x, 1 - top)
        loc, _ = P3L.localize(ctx, x, det, thr, "cpd")
        tp, fp, nr, h = PS.score(ctx, loc)
        rows.append(dict(k_mult=mult, k=k, tp=tp, fp=fp, n_ref=nr, nonict_h=h))
    return rows


def build_sys_sweep():
    fp = OUT / "sys_sweep.csv"
    if fp.exists():
        return pd.read_csv(fp)
    rows = []
    b4_cal = json.loads((OUT / "b4_loo_calibration.json").read_text())["k_loo"]

    for fold in (1, 2, 3, 4):
        man = X3.fold_manifest(fold)
        ck, meta = X3.load_fold_ckpt(f"results/v9_x3/models/fold{fold}", fold, 42)
        k_g = json.loads((OUT / f"fold{fold}_seed42_calibration.json").read_text())["k"]
        k_f = json.loads((OUT / f"fold{fold}_seed42_F_calibration.json").read_text())["k_F"]
        for s in man["held_out_cases"]:
            ctx = X3.case_ctx(s)
            Dg = X3.dump_D(ctx, ck, meta, cache_key=f"fold{fold}_seed42/{s}")
            Db = KB4.b4_D(s)
            xg = V9E1.final_scalar_from_D(ctx, Dg); mg = V9E1.member_mean_z_from_D(ctx, Dg)
            for r in sweep_case(ctx, xg, mg, k_g):
                rows.append(dict(subject=s, arm="GAE-CV", seed="42", fold=fold, **r))
            xf, mf = V9E1B.f_signals(ctx, Dg, Db)
            for r in sweep_case(ctx, xf, mf, k_f):
                rows.append(dict(subject=s, arm="GAE+kNN-CV", seed="42", fold=fold, **r))
            print(f"  fold {fold} {s}: GAE-CV + GAE+kNN-CV swept", flush=True)

    for s in ALL24:
        ctx = X3.case_ctx(s)
        Db = KB4.b4_D(s)
        xb = V9E1.final_scalar_from_D(ctx, Db); mb = V9E1.member_mean_z_from_D(ctx, Db)
        for r in sweep_case(ctx, xb, mb, b4_cal[s]):
            rows.append(dict(subject=s, arm="kNN-LOO", seed="42", fold=np.nan, **r))
        print(f"  {s}: kNN-LOO swept", flush=True)

    SYS = pd.DataFrame(rows)
    SYS.to_csv(fp, index=False)
    print(f"wrote {fp}")
    return SYS


# ------------------------------------------------------------------------------------- Part A: matched FP/day
def per_patient_sens_at_fa(SYS, subs, arm, target_fa):
    """v9_e2_veto.per_patient_sens_at_fa, duplicated (see module docstring): pools tp/fp/n_ref/
    nonict_h over `subs` at each k_mult to find the pooled-FA bracket, then interpolates each
    case's OWN sensitivity within that bracket -- same relative k_mult for every case."""
    d = SYS[(SYS.subject.isin(subs)) & (SYS.arm == arm)]
    seeds = sorted(d.seed.unique())
    acc = {}
    for sd in seeds:
        dd = d[d.seed == sd]
        pooled = dd.groupby("k_mult")[["tp", "fp", "n_ref", "nonict_h"]].sum().reset_index()
        pooled["fa"] = pooled.fp / pooled.nonict_h * 24
        pooled = pooled.sort_values("fa").reset_index(drop=True)
        if len(pooled) < 2 or target_fa < pooled.fa.min() or target_fa > pooled.fa.max():
            continue
        pos = int(np.searchsorted(pooled.fa.values, target_fa))
        pos = min(max(pos, 1), len(pooled) - 1)
        lo_row, hi_row = pooled.iloc[pos - 1], pooled.iloc[pos]
        frac = 0.0 if hi_row.fa == lo_row.fa else (target_fa - lo_row.fa) / (hi_row.fa - lo_row.fa)
        km_lo, km_hi = lo_row.k_mult, hi_row.k_mult
        dd2 = dd[dd.k_mult.isin([km_lo, km_hi])]
        piv = dd2.pivot_table(index="subject", columns="k_mult", values=["tp", "n_ref"])
        sens_lo = piv[("tp", km_lo)] / piv[("n_ref", km_lo)]
        sens_hi = piv[("tp", km_hi)] / piv[("n_ref", km_hi)]
        sens_interp = (1 - frac) * sens_lo + frac * sens_hi
        for subj, v in sens_interp.items():
            acc.setdefault(subj, []).append(v)
    if not acc:
        return pd.Series(dtype=float)
    return pd.Series({s: float(np.mean(v)) for s, v in acc.items()})


def paired_boot(a, b, n=10_000, seed=0):
    """v9_e2_veto.paired_boot, duplicated (see module docstring)."""
    rng = np.random.default_rng(seed)
    subs = sorted(set(a.index) & set(b.index))
    av, bv = a.loc[subs].values, b.loc[subs].values
    N = len(subs)
    diffs = np.empty(n)
    for i in range(n):
        idx = rng.integers(0, N, N)
        diffs[i] = av[idx].mean() - bv[idx].mean()
    return dict(mean_diff=float(diffs.mean()), ci_lo=float(np.percentile(diffs, 2.5)),
                ci_hi=float(np.percentile(diffs, 97.5)), share_gt0=float((diffs > 0).mean()), n=N)


PAIRS = [("GAE-CV", "kNN-LOO", "GAE-kNN"), ("GAE+kNN-CV", "GAE-CV", "GAE+kNN-GAE"),
         ("GAE+kNN-CV", "kNN-LOO", "GAE+kNN-kNN")]


def part_a(SYS):
    rows = []
    sens_cache = {}
    for t in FP_TARGETS:
        for arm in ("GAE-CV", "kNN-LOO", "GAE+kNN-CV"):
            sens_cache[(arm, t)] = per_patient_sens_at_fa(SYS, SUBSET_ALL24, arm, t)
        for a_arm, b_arm, label in PAIRS:
            sa, sb = sens_cache[(a_arm, t)], sens_cache[(b_arm, t)]
            if not len(sa) or not len(sb):
                rows.append(dict(fa_target=t, pair=label, mean_diff=np.nan, ci_lo=np.nan,
                                  ci_hi=np.nan, share_gt0=np.nan, n=0))
                continue
            rows.append(dict(fa_target=t, pair=label, **paired_boot(sa, sb)))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "paired_sens_matched_fa.csv", index=False)

    mean_sens_rows = []
    for t in FP_TARGETS:
        for arm in ("GAE-CV", "kNN-LOO", "GAE+kNN-CV"):
            s = sens_cache[(arm, t)]
            mean_sens_rows.append(dict(fa_target=t, arm=arm, n=len(s),
                                       mean_sens=float(s.mean()) if len(s) else np.nan))
    mdf = pd.DataFrame(mean_sens_rows)
    mdf.to_csv(OUT / "mean_sens_matched_fa.csv", index=False)
    return mdf, df


# ------------------------------------------------------------------------------------- Part B: own point, F1 + precision
def per_case_metric_at_own_point(combined, arm, metric):
    d = combined[(combined.arm == arm) & (combined.stage == "localized")].copy()
    if metric == "f1":
        d["val"] = 2 * d.tp / (2 * d.tp + d.fp + (d.n_ref - d.tp))
    else:
        d["val"] = d.tp / (d.tp + d.fp)
    return d.set_index("subject").val


def part_b():
    combined = pd.read_csv(OUT / "combined_per_subject.csv")
    rows = []
    for metric in ("f1", "precision"):
        vals = {arm: per_case_metric_at_own_point(combined, arm, metric)
                for arm in ("GAE-CV", "kNN-LOO", "GAE+kNN-CV")}
        for a_arm, b_arm, label in PAIRS:
            r = paired_boot(vals[a_arm], vals[b_arm])
            rows.append(dict(metric=metric, pair=label, **r))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "paired_f1_precision_own_point.csv", index=False)
    return df


def main():
    SYS = build_sys_sweep()
    mean_sens, paired_sens = part_a(SYS)
    paired_f1p = part_b()

    L = ["# V9-X3 -- system-stage k-sweep: matched FP/day sensitivity + paired F1/precision\n",
         "No training; reuses the cached GAE/B4 distance dumps from the main V9-X3 run. K_MULT = "
         "v9_e1b_calibrate.K_MULT (13 log-spaced multipliers of each case's OWN already-"
         "calibrated k); matched FP/day = pooled-curve bracket (v9_e2_veto.per_patient_sens_at_fa's "
         "construction), 24 cases.\n",
         "\n## Per-case-mean sensitivity at matched FP/day (all 24 cases)\n```"]
    piv = mean_sens.pivot_table(index="arm", columns="fa_target", values="mean_sens")
    L.append(piv.round(3).to_string())
    L.append("```")

    L.append("\n## Paired bootstrap, per-case sensitivity at matched FP/day (10,000 draws, all 24 cases)\n```")
    for _, r in paired_sens.iterrows():
        L.append(f"FP/day {r.fa_target:5.1f}  {r.pair:14s} mean diff {r.mean_diff:+.3f}  "
                 f"95% CI [{r.ci_lo:+.3f}, {r.ci_hi:+.3f}]  P(diff>0) {r.share_gt0:.3f}  (n={r.n:.0f})")
    L.append("```")

    L.append("\n## Paired bootstrap, per-case F1 and precision at each arm's OWN calibrated point "
              "(10,000 draws, all 24 cases)\n```")
    for _, r in paired_f1p.iterrows():
        L.append(f"{r.metric:10s} {r.pair:14s} mean diff {r.mean_diff:+.3f}  95% CI "
                 f"[{r.ci_lo:+.3f}, {r.ci_hi:+.3f}]  P(diff>0) {r.share_gt0:.3f}  (n={r.n:.0f})")
    L.append("```")

    (OUT / "SYS_SWEEP_SUMMARY.md").write_text("\n".join(L), encoding="utf-8")
    print(f"wrote {OUT / 'SYS_SWEEP_SUMMARY.md'}")
    print("\n".join(L))


if __name__ == "__main__":
    main()
