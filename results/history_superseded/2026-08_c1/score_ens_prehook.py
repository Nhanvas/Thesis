"""
score_ens.py — CURSOR CPU. The slow half of the pipeline (no GPU).

Loads the ensemble arrays from build_ens.py and runs the CPD grid + SzCORE
scoring, writing final_eval_seed{S}.csv in the format aggregate_final expects.

FAST GRID (bit-identical to szcore_eval.evaluate_subject)
---------------------------------------------------------
The naive path calls evaluate_subject once per mag; each call rebuilds the
timeline and each (mag,pen) cell re-fits PELT — 8 timeline builds + 48 PELT fits
per subject. But in cpd_pipeline_v14.detect_changepoints the smoothing, robust
variance and PELT .fit() depend ONLY on the signal, not on mag/pen; only
predict(pen) (6 values) and the magnitude percentile filter (8 values, cheap)
vary. So per subject we build the timeline ONCE, fit PELT ONCE, predict per pen,
then apply the 8 magnitude thresholds. Same building blocks, same numbers,
~40x fewer PELT fits. Use --verify to PROVE bit-identity on one subject.

Resumable + shardable (a subject is written only when fully done; re-running
skips finished subjects; --only_subjects shards across terminals).

Needs: numpy, ruptures, timescoring + src single-sources (szcore_eval,
cpd_pipeline_v14, evaluation_protocol). NO torch.

USAGE (Cursor)
  # one-time correctness proof on a small subject (runs BOTH paths, diffs):
  python score_ens.py --ens_dir results/retrain/ens --seed 42 --verify chb16 \
      --summary_dir "F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary"
  # seed 42, full grid (fast now):
  python score_ens.py --ens_dir results/retrain/ens --seed 42 \
      --summary_dir "F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary" --out_dir results/retrain
  # seeds 1-4, only the two chosen mags:
  python score_ens.py --ens_dir results/retrain/ens --seed 1 --only_mags 55,65 \
      --summary_dir "F:/..." --out_dir results/retrain
Smoke (stubbed, no timescoring):
  python score_ens.py --smoke
"""
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
for _p in (_here, _os.path.dirname(_here)):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import argparse
import csv
import json
from pathlib import Path

import numpy as np

TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
MAG_PCTS = [40.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0]
COLS = ["seed", "subject", "mag_pct", "pen_mult", "tp", "fp", "n_seizures",
        "n_inter_h", "sensitivity", "precision", "fp_per_day", "window_auroc"]


def _mag_filter(V14, smoothed, cps_pen, mag_pct, local_win, real_inter):
    """Replicates cpd_pipeline_v14.detect_changepoints's magnitude filter exactly."""
    if not (mag_pct and mag_pct > 0 and cps_pen):
        return list(cps_pen)
    mags_d = {c: V14._cp_magnitude(smoothed, c, local_win) for c in cps_pen}
    if real_inter is not None and np.any(real_inter):
        bg = [m for c, m in mags_d.items() if real_inter[c]]
    else:
        bg = list(mags_d.values())
    thr = float(np.percentile(bg, mag_pct)) if bg else 0.0
    return [c for c in cps_pen if mags_d[c] >= thr]


def fast_grid_rows(SE, V14, rpt, subj, ei, ec, summary_dir, mags,
                   bootstrap_seed, local_win=15):
    np.random.seed(bootstrap_seed)                      # same reseed point as before
    signal, is_ictal, is_buffer, real_inter, sz_ranges, n_inter_h = \
        SE.build_timeline_masked(subj, ei, ec, summary_dir)
    ref_iv = [(s * SE.WIN_SEC, e * SE.WIN_SEC) for (s, e) in sz_ranges]
    total_dur_s = len(signal) * SE.WIN_SEC

    smoothed = V14._smooth(np.asarray(signal, dtype=float))
    n = len(smoothed)
    rows = []
    if n < 10:
        for pm in SE.PEN_MULTS:
            for mag in mags:
                sc = SE.score_szcore(ref_iv, [], total_dur_s, n_inter_h)
                rows.append(dict(subject=subj, mag_pct=mag, pen_mult=pm,
                                 n_seizures=len(sz_ranges), **sc,
                                 n_inter_h=round(n_inter_h, 2)))
        return rows

    s2 = V14._robust_variance(smoothed, real_inter)
    algo = rpt.Pelt(model="l2", min_size=V14.PELT_MIN_SIZE,
                    jump=V14.PELT_JUMP).fit(smoothed.reshape(-1, 1))   # ONCE
    for pm in SE.PEN_MULTS:
        beta = pm * s2 * np.log(n)
        cps_pen = [c for c in algo.predict(pen=beta) if 0 < c < n]
        for mag in mags:
            cps = _mag_filter(V14, smoothed, cps_pen, mag, local_win, real_inter)
            hyp_iv = SE.cps_to_events(cps, is_buffer, n, sz_ranges=sz_ranges)
            sc = SE.score_szcore(ref_iv, hyp_iv, total_dur_s, n_inter_h)
            lat = SE.matched_latency(ref_iv, hyp_iv)
            rows.append(dict(subject=subj, mag_pct=mag, pen_mult=pm,
                             n_seizures=len(sz_ranges), **sc, mean_lat_s=lat,
                             n_inter_h=round(n_inter_h, 2)))
    return rows


def done_subjects(csv_path):
    if not csv_path.exists():
        return set()
    with open(csv_path) as f:
        return {r["subject"] for r in csv.DictReader(f)}


def append_rows(csv_path, rows):
    new = not csv_path.exists()
    with open(csv_path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerows(rows)


def run(seed, subjs, grid_fn, wa, csv_path):
    already = done_subjects(csv_path)
    if already:
        print(f"  resuming — done: {sorted(already)}")
    for subj in subjs:
        if subj in already:
            print(f"  skip {subj} (done)"); continue
        rows = grid_fn(subj)
        for r in rows:
            r["seed"] = seed
            r["window_auroc"] = round(wa.get(subj, float("nan")), 4)
        append_rows(csv_path, rows)
        print(f"  wrote {subj} ({len(rows)} rows)", flush=True)


def _verify(SE, V14, rpt, subj, ei, ec, summary_dir, bootstrap_seed, local_win,
            mags=None):
    """Run BOTH the original evaluate_subject (per mag) and the fast grid on ONE
    subject; assert identical tp/fp for every (mag,pen). Pass a short `mags` list
    (e.g. [50,60]) for a fast proof — 2 mags is enough to catch any refactor bug."""
    mags = mags or MAG_PCTS
    print(f"[verify] {subj}: mags={mags}. running ORIGINAL path (slow) ...", flush=True)
    orig = {}
    for mag in mags:
        np.random.seed(bootstrap_seed)
        for r in SE.evaluate_subject(subj, ei, ec, summary_dir,
                                     min_mag_pct=mag, local_win=local_win):
            orig[(mag, r["pen_mult"])] = (r["tp"], r["fp"])
        print(f"[verify]   original mag{mag:g} done", flush=True)
    print(f"[verify] {subj}: running FAST path ...", flush=True)
    fast = {}
    for r in fast_grid_rows(SE, V14, rpt, subj, ei, ec, summary_dir, mags,
                            bootstrap_seed, local_win):
        fast[(r["mag_pct"], r["pen_mult"])] = (r["tp"], r["fp"])
    diffs = [(k, orig[k], fast[k]) for k in orig if orig[k] != fast.get(k)]
    if diffs:
        print(f"[verify] MISMATCH in {len(diffs)} cells (showing 5):")
        for k, o, f in diffs[:5]:
            print(f"    mag{k[0]:g}/pen{k[1]:g}: orig{o} vs fast{f}")
        raise SystemExit("fast grid is NOT bit-identical — do not use")
    print(f"[verify] PASS — {len(orig)} cells identical. Fast grid is safe.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ens_dir", default="results/retrain/ens")
    ap.add_argument("--seed", type=int, required=False)
    ap.add_argument("--summary_dir", default="data/summaries")
    ap.add_argument("--out_dir", default="results/retrain")
    ap.add_argument("--only_mags", default=None)
    ap.add_argument("--only_subjects", default=None)
    ap.add_argument("--verify", default=None,
                    help="subject id to bit-verify fast vs original, then exit")
    ap.add_argument("--bootstrap_seed", type=int, default=0)
    ap.add_argument("--local_win", type=int, default=15)
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()

    if a.smoke:
        pens = [0.3, 0.5, 1.0, 2.0, 5.0, 10.0]

        def stub_grid(subj):
            rows = []
            for mag in MAG_PCTS:
                base = int(50 * (1 - mag / 100.0))
                for i, p in enumerate(pens):
                    rows.append(dict(subject=subj, mag_pct=mag, pen_mult=p,
                                     tp=max(0, base - i), fp=int(20 * (1 - mag / 100)),
                                     n_seizures=10, n_inter_h=10.0,
                                     sensitivity=0.5, precision=0.1, fp_per_day=5.0))
            return rows
        wa = {s: 0.8 for s in TEST_SUBJS}
        out = Path("/tmp/score_smoke"); out.mkdir(parents=True, exist_ok=True)
        cp = out / "final_eval_seed42.csv"
        if cp.exists():
            cp.unlink()
        run(42, TEST_SUBJS[:3], stub_grid, wa, cp)
        n3 = len(done_subjects(cp))
        run(42, TEST_SUBJS, stub_grid, wa, cp)
        n8 = len(done_subjects(cp))
        assert n3 == 3 and n8 == 8, (n3, n8)
        cp2 = out / "final_eval_seed1.csv"
        if cp2.exists():
            cp2.unlink()

        def stub_grid_2mags(subj):
            return [r for r in stub_grid(subj) if r["mag_pct"] in (55.0, 65.0)]
        run(1, TEST_SUBJS, stub_grid_2mags, wa, cp2)
        with open(cp2) as f:
            seen = {float(r["mag_pct"]) for r in csv.DictReader(f)}
        assert seen == {55.0, 65.0}, seen
        print("\n[SMOKE] resume + only_mags PASS")
        return

    assert a.seed is not None, "--seed required"
    import ruptures as rpt
    import szcore_eval as SE
    import cpd_pipeline_v14 as V14

    ens_dir = Path(a.ens_dir)

    def load(subj):
        ei = np.load(ens_dir / f"ens_seed{a.seed}_{subj}_inter.npy")
        ec = np.load(ens_dir / f"ens_seed{a.seed}_{subj}_ictal.npy")
        return ei, ec

    if a.verify:
        ei, ec = load(a.verify)
        vmags = ([float(x) for x in a.only_mags.split(",")] if a.only_mags else None)
        _verify(SE, V14, rpt, a.verify, ei, ec, a.summary_dir,
                a.bootstrap_seed, a.local_win, mags=vmags)
        return

    mags = ([float(x) for x in a.only_mags.split(",")] if a.only_mags else MAG_PCTS)
    subjs = (a.only_subjects.split(",") if a.only_subjects else TEST_SUBJS)
    wa_path = ens_dir / f"window_auroc_seed{a.seed}.json"
    wa = json.loads(wa_path.read_text()) if wa_path.exists() else {}

    def grid_fn(subj):
        ei, ec = load(subj)
        return fast_grid_rows(SE, V14, rpt, subj, ei, ec, a.summary_dir, mags,
                              a.bootstrap_seed, a.local_win)

    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    csv_path = out / f"final_eval_seed{a.seed}.csv"
    print(f"seed {a.seed} | mags {mags} | subjects {subjs}\n-> {csv_path}")
    run(a.seed, subjs, grid_fn, wa, csv_path)
    print("Done. When all seeds present, run aggregate_final.py.")


if __name__ == "__main__":
    main()