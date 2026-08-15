"""
final_eval.py — PREREG_03 §3-4: ONE end-to-end evaluation on the 8 TEST subjects.

Given the weights derived on non-test (derive_weights.py -> derived_weights.json):
  1. For each model seed k in {42,1,2,3,4}: load GAE seed-k + LSTM seed-k, build
     robust-z components for the 8 test subjects, form the weighted ensemble
     (single-source ensemble_recipe), run the full mag% x pen grid through the
     single-source detector (cpd_pipeline_v14 via szcore_eval.evaluate_subject),
     pool per (mag,pen), and record per-subject window AUROC.
  2. Canonical seed-42: compute the FULL Pareto frontier; pick the two reported
     operating points by the PRE-REGISTERED option-A rule
        balanced  = frontier point with FP/day nearest 40
        high-sens = max sensitivity among frontier points with FP/day <= 75.
  3. Report seed-42 point estimates + 95% CIs (Wilson sens/prec, Poisson FP/day),
     window macro AUROC, and — at the SAME two (mag,pen) fixed from the canonical
     seed — the 5-seed mean +/- SD. ONE pass; whatever it gives is the headline.

Integrity: weights come from non-test; operating points from a fixed rule; the
operating point is fixed by the canonical seed and seed variance is measured AT
that fixed point (not re-selected per seed, which would conflate op-instability
with detection variance). Numbers are reported as-is.

Reseeding note: np.random is reseeded to --bootstrap_seed (default 0) IMMEDIATELY
before every evaluate_subject() call — the fix from mag_pen_grid_sweep_v2.py. This
is the CPD timeline-padding seed and is distinct from the model seed k.

USAGE (Kaggle GPU)
  python final_eval.py --input_root /kaggle/input \
      --weights_json /kaggle/working/prereg03/derived_weights.json \
      --summary_dir /kaggle/input/chb-summaries \
      --out_dir /kaggle/working/prereg03
Smoke (no torch/timescoring/data):
  python final_eval.py --smoke
"""
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
for _p in (_here, _os.path.dirname(_here)):      # src/retrain/ and src/ (flat)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import argparse
import csv
import json
from pathlib import Path

import numpy as np

import retrain_io as IO
import stat_validation as ST     # single source for Wilson / Poisson CIs

MAG_PCTS = [40.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0]  # == mag_pen_grid_v2
DEFAULT_PENS = [0.3, 0.5, 1.0, 2.0, 5.0, 10.0]               # == E.PEN_MULTS
MODEL_SEEDS = [42, 1, 2, 3, 4]


# ============================================================================
# pooling (micro) — mirrors mag_pen_grid_sweep_v2 pooled aggregation
# ============================================================================
def pool_grid(persubj_rows):
    """persubj_rows: list of dict(subject,mag_pct,pen_mult,tp,fp,n_seizures,n_inter_h).
    Returns pooled rows per (mag_pct, pen_mult)."""
    key_to = {}
    for r in persubj_rows:
        key_to.setdefault((r["mag_pct"], r["pen_mult"]), []).append(r)
    pooled = []
    for (mag, pen), rs in key_to.items():
        tp = sum(r["tp"] for r in rs); fp = sum(r["fp"] for r in rs)
        nsz = sum(r["n_seizures"] for r in rs); h = sum(r["n_inter_h"] for r in rs)
        sens = tp / nsz if nsz else float("nan")
        fp_day = fp / h * 24 if h else float("nan")
        prec = tp / (tp + fp) if (tp + fp) else float("nan")
        f1 = (2 * prec * sens / (prec + sens)) if (prec and sens) else float("nan")
        pooled.append(dict(mag_pct=mag, pen_mult=pen, TP=tp, FN=nsz - tp, FP=fp,
                           n_seizures=nsz, interictal_hours=round(h, 2),
                           sensitivity=round(sens, 4), precision=round(prec, 4),
                           f1=round(f1, 4), fp_per_day=round(fp_day, 3)))
    return pooled


def pooled_point_ci(persubj_rows, mag, pen, label):
    """Pool the per-subject rows at one (mag,pen) and attach 95% CIs — mirrors
    stat_validation.validate_operating_point (Wilson sens/prec, Poisson FP/day)."""
    rs = [r for r in persubj_rows
          if abs(r["mag_pct"] - mag) < 1e-9 and abs(r["pen_mult"] - pen) < 1e-9]
    TP = sum(r["tp"] for r in rs); FP = sum(r["fp"] for r in rs)
    n_sz = sum(r["n_seizures"] for r in rs); FN = n_sz - TP
    inter_h = sum(r["n_inter_h"] for r in rs); inter_days = inter_h / 24.0
    sens = TP / n_sz if n_sz else float("nan")
    prec = TP / (TP + FP) if (TP + FP) else float("nan")
    f1 = (2 * prec * sens / (prec + sens)) if (prec and sens) else float("nan")
    fp_day = FP / inter_days if inter_days else float("nan")
    s_lo, s_hi = ST.wilson_ci(TP, n_sz)
    p_lo, p_hi = ST.wilson_ci(TP, TP + FP)
    f_lo, f_hi = ST.poisson_rate_ci(FP, inter_days)
    per_sens = [r["tp"] / r["n_seizures"] if r["n_seizures"] else float("nan") for r in rs]
    return dict(operating_point=label, mag_pct=mag, pen=pen, n_subjects=len(rs),
                n_seizures=n_sz, TP=TP, FN=FN, FP=FP,
                interictal_hours=round(inter_h, 1),
                sensitivity=round(sens, 4),
                sensitivity_CI=f"[{s_lo:.3f}, {s_hi:.3f}]",
                sensitivity_macro=f"{np.nanmean(per_sens):.3f} +/- {np.nanstd(per_sens, ddof=1):.3f}",
                precision=round(prec, 4), precision_CI=f"[{p_lo:.3f}, {p_hi:.3f}]",
                f1=round(f1, 4), fp_per_day=round(fp_day, 2),
                fp_per_day_CI=f"[{f_lo:.2f}, {f_hi:.2f}]")


# ============================================================================
# production per-seed run (Kaggle GPU) — builds components, runs the grid
# ============================================================================
def run_seed(seed, weights, dirs, bootstrap_seed=0, subjs=None, mags=None):
    """Returns (persubj_rows, {subj: window_auroc}) for one model seed."""
    import torch
    import gae_joint as G
    import lstm_temporal as T
    import szcore_eval as SE       # imports timescoring + cpd_pipeline_v14

    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    subjs = subjs or IO.TEST_SUBJS
    mags = mags or MAG_PCTS
    adj_dir, feat_dir, gamma_dir, gae_ck, lstm_ck, suffix, summary_dir = dirs

    gae = G.GAEModel().to(dev)
    gsd = IO.load_state(gae_ck[seed]); gae.load_state_dict(gsd.get("state_dict", gsd), strict=True); gae.eval()
    lstm = T.LSTMPredictor(in_dim=18 * 16).to(dev)
    lsd = IO.load_state(lstm_ck[seed]); lstm.load_state_dict(lsd.get("state_dict", lsd), strict=True); lstm.eval()

    persubj, waur = [], {}
    for s in subjs:
        comp = IO.build_subject_components(gae, lstm, s, adj_dir, feat_dir,
                                           gamma_dir, suffix, dev)
        ens_i, ens_c = IO.ensemble_from_components(comp, weights)
        waur[s] = IO.window_auroc(ens_i, ens_c)
        for mag in mags:
            np.random.seed(bootstrap_seed)   # reseed before EVERY call (v2 fix)
            rows = SE.evaluate_subject(s, ens_i, ens_c, summary_dir,
                                       min_mag_pct=mag, local_win=15)
            for r in rows:
                persubj.append(dict(seed=seed, subject=s, mag_pct=mag,
                                    pen_mult=r["pen_mult"], tp=r["tp"], fp=r["fp"],
                                    n_seizures=r["n_seizures"],
                                    n_inter_h=r["n_inter_h"],
                                    sensitivity=r["sensitivity"],
                                    precision=r.get("precision", float("nan")),
                                    fp_per_day=r["fp_per_day"]))
        print(f"    seed {seed} {s}: window AUROC {waur[s]:.4f}", flush=True)
    return persubj, waur


# ============================================================================
# assemble + report + write (shared by production and --smoke)
# ============================================================================
def report(all_persubj, all_waur, weights, out_dir, canon=IO.CANON_SEED):
    """all_persubj: {seed: persubj_rows}. all_waur: {seed: {subj: auroc}}."""
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    seeds = sorted(all_persubj, key=lambda s: (s != canon, s))  # canon first

    # ---- canonical-seed frontier + option-A ----
    canon_rows = all_persubj[canon]
    pooled = IO.mark_pareto(pool_grid(canon_rows))
    sel = IO.select_operating_points_optionA(pooled, target_fp=40.0, fp_cap=75.0)
    bal, hs = sel["balanced"], sel["highsens"]
    print("\n" + "=" * 74)
    print(f"CANONICAL seed-{canon} Pareto frontier + option-A selection")
    print("=" * 74)
    for r in sorted([r for r in pooled if r["on_pareto_frontier"]],
                    key=lambda r: r["fp_per_day"]):
        tag = ""
        if (r["mag_pct"], r["pen_mult"]) == (bal["mag_pct"], bal["pen_mult"]):
            tag += "  <- BALANCED (FP/day nearest 40)"
        if (r["mag_pct"], r["pen_mult"]) == (hs["mag_pct"], hs["pen_mult"]):
            tag += "  <- HIGH-SENS (max sens, FP/day<=75)"
        print(f"  mag{r['mag_pct']:g}/pen{r['pen_mult']:g}: "
              f"sens={r['sensitivity']:.3f} FP/day={r['fp_per_day']:.2f}{tag}")
    for n in sel["notes"]:
        print(f"  [note] {n}")

    # ---- canonical-seed point estimates + CIs at the two ops ----
    bal_ci = pooled_point_ci(canon_rows, bal["mag_pct"], bal["pen_mult"], "balanced")
    hs_ci = pooled_point_ci(canon_rows, hs["mag_pct"], hs["pen_mult"], "high-sensitivity")

    # ---- 5-seed mean+/-SD at the SAME two fixed (mag,pen) ----
    def multiseed_at(mag, pen):
        per_seed = []
        for sd in seeds:
            p = pool_grid([r for r in all_persubj[sd]
                           if abs(r["mag_pct"] - mag) < 1e-9
                           and abs(r["pen_mult"] - pen) < 1e-9])[0]
            per_seed.append((sd, p["sensitivity"], p["fp_per_day"]))
        S = np.array([x[1] for x in per_seed]); F = np.array([x[2] for x in per_seed])
        return per_seed, (S.mean(), S.std(ddof=1)), (F.mean(), F.std(ddof=1))
    bal_ms = multiseed_at(bal["mag_pct"], bal["pen_mult"])
    hs_ms = multiseed_at(hs["mag_pct"], hs["pen_mult"])

    # ---- window macro AUROC (seed42 + mean+/-SD) ----
    def macro_waur(sd):
        return float(np.nanmean(list(all_waur[sd].values())))
    waur_canon = macro_waur(canon)
    waur_all = np.array([macro_waur(sd) for sd in seeds])

    # ---- print headline ----
    print("\n" + "=" * 74)
    print("NEW HEADLINE (rebuilt pipeline) — report as-is")
    print("=" * 74)
    print(f"weights (recon,temporal,gamma) = "
          f"({weights[0]:.2f},{weights[1]:.2f},{weights[2]:.2f})")
    for lbl, ci, ms in [("BALANCED", bal_ci, bal_ms), ("HIGH-SENS", hs_ci, hs_ms)]:
        print(f"\n[{lbl}]  mag{ci['mag_pct']:g}/pen{ci['pen']:g}  "
              f"(TP/FN/FP {ci['TP']}/{ci['FN']}/{ci['FP']}, {ci['n_seizures']} sz)")
        print(f"  seed-{canon}: sensitivity {ci['sensitivity']:.3f} {ci['sensitivity_CI']}"
              f"  |  FP/day {ci['fp_per_day']:.2f} {ci['fp_per_day_CI']}"
              f"  |  prec {ci['precision']:.3f}  F1 {ci['f1']:.3f}")
        print(f"  5-seed: sensitivity {ms[1][0]:.3f} +/- {ms[1][1]:.3f}"
              f"  |  FP/day {ms[2][0]:.2f} +/- {ms[2][1]:.2f}")
    print(f"\nwindow macro AUROC: seed-{canon} {waur_canon:.3f}  |  "
          f"5-seed {waur_all.mean():.3f} +/- {waur_all.std(ddof=1):.3f}")

    # ---- write CSVs ----
    # 1) full per-subject (all seeds/mag/pen)
    with open(out / "final_eval_persubject.csv", "w", newline="") as f:
        cols = ["seed", "subject", "mag_pct", "pen_mult", "tp", "fp", "n_seizures",
                "n_inter_h", "sensitivity", "precision", "fp_per_day"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader()
        for sd in seeds:
            w.writerows(all_persubj[sd])
    # 2) canonical-seed pooled frontier
    with open(out / "final_eval_frontier_seed{}.csv".format(canon), "w", newline="") as f:
        cols = ["mag_pct", "pen_mult", "TP", "FN", "FP", "n_seizures",
                "interictal_hours", "sensitivity", "precision", "f1",
                "fp_per_day", "on_pareto_frontier"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader()
        w.writerows(sorted(pooled, key=lambda r: (r["mag_pct"], r["pen_mult"])))
    # 3) locked-style 2-op table (drop-in for RESULTS_OF_RECORD §16)
    with open(out / "final_eval_locked.csv", "w", newline="") as f:
        cols = list(bal_ci.keys())
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        w.writerow(bal_ci); w.writerow(hs_ci)
    # 4) multiseed at the two fixed ops
    with open(out / "final_eval_multiseed.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["operating_point", "mag_pct", "pen_mult", "seed",
                    "sensitivity", "fp_per_day"])
        for lbl, ci, ms in [("balanced", bal_ci, bal_ms), ("high-sensitivity", hs_ci, hs_ms)]:
            for (sd, se, fp) in ms[0]:
                w.writerow([lbl, ci["mag_pct"], ci["pen"], sd, f"{se:.4f}", f"{fp:.3f}"])
            w.writerow([lbl, ci["mag_pct"], ci["pen"], "MEAN",
                        f"{ms[1][0]:.4f}", f"{ms[2][0]:.3f}"])
            w.writerow([lbl, ci["mag_pct"], ci["pen"], "SD",
                        f"{ms[1][1]:.4f}", f"{ms[2][1]:.3f}"])
    # 5) window AUROC per subject/seed + macro
    with open(out / "final_eval_window_auroc.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["seed"] + IO.TEST_SUBJS + ["macro"])
        for sd in seeds:
            w.writerow([sd] + [f"{all_waur[sd].get(s, float('nan')):.4f}" for s in IO.TEST_SUBJS]
                       + [f"{macro_waur(sd):.4f}"])
        w.writerow(["MEAN"] + [""] * len(IO.TEST_SUBJS) + [f"{waur_all.mean():.4f}"])
        w.writerow(["SD"] + [""] * len(IO.TEST_SUBJS) + [f"{waur_all.std(ddof=1):.4f}"])

    for name in ["final_eval_locked.csv", "final_eval_frontier_seed{}.csv".format(canon),
                 "final_eval_multiseed.csv", "final_eval_window_auroc.csv",
                 "final_eval_persubject.csv"]:
        print(f"[saved] {out / name}")
    print("\nNext: review, then re-lock (ROR §16; archive §1-§15). "
          "Update ensemble_recipe.ENS_WEIGHTS to the derived values.")
    return dict(balanced=bal_ci, highsens=hs_ci, window_auroc_seed=waur_canon)


# ============================================================================
# synthetic data for --smoke (per-subject rows with a real trade-off surface)
# ============================================================================
def _synth_persubj(seed, pens):
    rng = np.random.default_rng(100 + seed)
    n_sz = {s: n for s, n in zip(IO.TEST_SUBJS, [7, 10, 12, 8, 20, 3, 5, 11])}  # sum 76
    inter_h = {s: h for s, h in zip(IO.TEST_SUBJS, [20, 40, 18, 22, 15, 25, 30, 28])}
    rows = []
    for mi, mag in enumerate(MAG_PCTS):
        for pi, pen in enumerate(pens):
            a = 0.5 * (1 - mi / (len(MAG_PCTS) - 1)) + 0.5 * (1 - pi / (len(pens) - 1))
            S = np.clip(0.55 + 0.32 * a + rng.normal(0, 0.01), 0, 1)   # 0.55..0.87
            F = max(5.0, 20 + 90 * a + rng.normal(0, 3))               # 20..110
            tp_tot = int(round(S * 76)); H = sum(inter_h.values())
            fp_tot = int(round(F * H / 24))
            # distribute proportionally
            tp_left, fp_left = tp_tot, fp_tot
            for i, s in enumerate(IO.TEST_SUBJS):
                last = (i == len(IO.TEST_SUBJS) - 1)
                tp = tp_left if last else min(n_sz[s], int(round(tp_tot * n_sz[s] / 76)))
                fp = fp_left if last else int(round(fp_tot * inter_h[s] / H))
                tp = min(tp, n_sz[s]); tp_left -= tp; fp_left -= fp
                rows.append(dict(seed=seed, subject=s, mag_pct=mag, pen_mult=pen,
                                 tp=max(0, tp), fp=max(0, fp), n_seizures=n_sz[s],
                                 n_inter_h=inter_h[s],
                                 sensitivity=tp / n_sz[s], precision=float("nan"),
                                 fp_per_day=fp / inter_h[s] * 24))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input_root", default="/kaggle/input")
    ap.add_argument("--weights_json", default="/kaggle/working/prereg03/derived_weights.json")
    ap.add_argument("--weights", default=None,
                    help="override 'wr,wt,wg' (else read recommended_weights from json)")
    ap.add_argument("--suffix", default="_topk20")
    ap.add_argument("--summary_dir", default="/kaggle/input/chb-summaries")
    ap.add_argument("--out_dir", default="/kaggle/working/prereg03")
    ap.add_argument("--bootstrap_seed", type=int, default=0)
    ap.add_argument("--seeds", default=",".join(str(s) for s in MODEL_SEEDS))
    ap.add_argument("--seed_run", type=int, default=None,
                    help="run exactly ONE model seed and SAVE its raw grid to "
                         "final_eval_seed{N}.csv (multi-account workflow). No lock.")
    ap.add_argument("--only_mags", default=None,
                    help="comma list of mag_pct to run (e.g. '60,55'); default = "
                         "full grid. Use the full grid for seed 42; only the two "
                         "chosen mags for the other seeds.")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()

    if a.smoke:
        print("[SMOKE] synthetic per-subject grid (real trade-off surface)")
        # unit-check pool_grid on a tiny hand-verifiable example
        tiny = [dict(subject="x", mag_pct=60.0, pen_mult=1.0, tp=3, fp=10,
                     n_seizures=5, n_inter_h=24.0),
                dict(subject="y", mag_pct=60.0, pen_mult=1.0, tp=4, fp=20,
                     n_seizures=5, n_inter_h=24.0)]
        p = pool_grid(tiny)[0]
        assert p["TP"] == 7 and p["FP"] == 30 and abs(p["sensitivity"] - 0.7) < 1e-9
        assert abs(p["fp_per_day"] - 15.0) < 1e-9, p     # 30 fp / 48h * 24
        pens = DEFAULT_PENS
        all_ps = {sd: _synth_persubj(sd, pens) for sd in MODEL_SEEDS}
        all_wa = {sd: {s: float(np.clip(0.72 + np.random.default_rng(sd * 9 + i)
                                        .normal(0, 0.02), 0, 1))
                       for i, s in enumerate(IO.TEST_SUBJS)} for sd in MODEL_SEEDS}
        res = report(all_ps, all_wa, (0.40, 0.35, 0.25), "/tmp/prereg03_smoke_eval")
        assert res["balanced"]["fp_per_day"] > 0
        assert "[" in res["balanced"]["sensitivity_CI"]
        # balanced FP/day should be the frontier point nearest 40
        assert abs(res["balanced"]["fp_per_day"] - 40) <= 35, res["balanced"]["fp_per_day"]
        assert res["highsens"]["fp_per_day"] <= 75.01, res["highsens"]["fp_per_day"]
        print("\n[SMOKE] PASS")
        return

    # ---- production ----
    if a.weights:
        weights = tuple(float(x) for x in a.weights.split(","))
    else:
        wj = json.loads(Path(a.weights_json).read_text())
        weights = tuple(wj["recommended_weights"])
        print(f"[weights] recommended from {a.weights_json}: {weights}")
    assert abs(sum(weights) - 1.0) < 1e-6, "weights must sum to 1"

    adj_dir = IO.find_data_dir(a.input_root, f"chb13_interictal_adjs{a.suffix}.npy")
    feat_dir = IO.find_data_dir(a.input_root, "chb13_interictal_features.npy")
    gamma_dir = IO.find_gamma_dir(a.input_root)
    gae_ck = IO.find_ckpts(a.input_root, "gae_joint_seed")
    lstm_ck = IO.find_ckpts(a.input_root, "lstm_temporal_seed")
    dirs = (adj_dir, feat_dir, gamma_dir, gae_ck, lstm_ck, a.suffix, a.summary_dir)
    mags = ([float(x) for x in a.only_mags.split(",")] if a.only_mags else MAG_PCTS)

    # ---- multi-account path: run ONE seed, save its raw grid, stop ----
    if a.seed_run is not None:
        sd = a.seed_run
        assert sd in gae_ck and sd in lstm_ck, f"seed {sd} checkpoints missing"
        print(f"[seed_run] seed {sd}, mags={mags}, weights={weights}")
        persubj, waur = run_seed(sd, weights, dirs, a.bootstrap_seed, mags=mags)
        out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
        fp = out / f"final_eval_seed{sd}.csv"
        with open(fp, "w", newline="") as f:
            cols = ["seed", "subject", "mag_pct", "pen_mult", "tp", "fp",
                    "n_seizures", "n_inter_h", "sensitivity", "precision",
                    "fp_per_day", "window_auroc"]
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader()
            for r in persubj:
                r = dict(r); r["window_auroc"] = round(waur.get(r["subject"], float("nan")), 4)
                w.writerow(r)
        print(f"[saved] {fp}  ({len(persubj)} rows) -> download this to Cursor")
        print("Next: gather all seed CSVs in Cursor and run aggregate_final.py")
        return

    # ---- single-session path: all seeds + lock in one go ----
    seeds = [int(s) for s in a.seeds.split(",")
             if int(s) in gae_ck and int(s) in lstm_ck]
    print(f"model seeds available: {seeds} (canonical {IO.CANON_SEED})")
    assert IO.CANON_SEED in seeds, "canonical seed 42 required for the headline"
    all_ps, all_wa = {}, {}
    for sd in seeds:
        print(f"\n[seed {sd}] building components + grid on 8 test subjects")
        all_ps[sd], all_wa[sd] = run_seed(sd, weights, dirs, a.bootstrap_seed, mags=mags)
    report(all_ps, all_wa, weights, a.out_dir)


if __name__ == "__main__":
    main()
