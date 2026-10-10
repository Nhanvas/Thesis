#!/usr/bin/env python
"""
t1_demo_gate.py -- T1 (web demo rebuilt on the final system, tag p3-frozen): identity gate, effect
of the label-free statistics, and processing time. THESIS SIDE: it reads the chb03 annotation (via
the thesis's own test context) to score; the demo itself never does. Writes only results/t1_demo/
and a scratch cache outside the repo (--cache, deleted at the end unless --keep-cache).

PRE-REGISTRATION (written 2026-10-10, before any run of this script on real data):
  gate  chb03, seed 42, balanced point. The demo pipeline (web_demo/backend/pipeline_demo.py,
        headless path = the same functions as the upload flow) is fed the THESIS z-score statistics
        (data/processed/chb03_stats.json, as x1_external gates) on exactly the 38 files of
        data/testset_v2/chb03.npz. PASS iff its events, scored with the thesis scorer path
        (p2_scalars.score on e22_test_oneshot.test_context), give the look-#7 counts of
        results/e23_test_look7/per_subject_seed.csv for both stages (detector and localized);
        the alarm budget top is reported beside the look-#7 `top`. Reported, not gated: window
        counts and signal-loss flags vs the test set; max relative difference of the per-channel
        distances vs results/p2_test/chb03.npz; max |difference| of the ensemble score vs
        e22_test_oneshot.final_scalar. On FAIL: STOP, nothing else is run; the mismatch is
        explained by mechanism before any change.
  labelfree  the same files with the demo's own label-free statistics (every 10th window of the
        whole recording; the approved divergence): reported as is (tp/fp both stages, statistics
        and score differences). No gate.
  timing  one test subject (default chb16, the shortest), the full headless path (Phase A, Phase
        B, stage 2) 5 times, each with a fresh cache; median seconds per hour of EEG and per stage.
        Run on the author's laptop with nothing else heavy running.
Run (estimated, not measured):
  python src/t1_demo_gate.py gate      --dataset F:/Study/Thesis/Dataset/CHB-MIT    (30-60 min)
  python src/t1_demo_gate.py timing    --dataset F:/Study/Thesis/Dataset/CHB-MIT    (30-60 min)
"""
import argparse
import json
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "dataprep", ROOT / "src" / "retrain", ROOT / "src" / "phaseB",
          ROOT / "src" / "phaseC", ROOT / "web_demo" / "backend"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import pipeline_demo as DEMO           # noqa: E402  (read-only import of the demo pipeline)
import p2_scalars as PS                # noqa: E402
import e22_test_oneshot as E22         # noqa: E402

OUT = ROOT / "results" / "t1_demo"
SUBJ = "chb03"
TAG = DEMO.MODEL_TAG
FROZEN_FILES = ["src/p2_scalars.py", "src/e16_recording_baseline.py", "src/e17b_latent_family.py",
                "src/e18_cpd_localizer.py", "src/e22_test_oneshot.py", "src/p3_levers.py", "src/p3c_freeze.py",
                "src/e23_test_look7.py", "src/c1b_build_trainset.py", "src/p2_dump_seeds23.py",
                "src/retrain/train_gae_v2.py", "src/x1_external.py", "results/p3c_freeze/freeze.json"]


def git(*args):
    return subprocess.run(["git", *args], cwd=str(ROOT), capture_output=True, text=True)


def integrity():
    """frozen code unchanged since the tag that froze it (x1_external since x1-prereg-v2)."""
    lines = []
    for f in FROZEN_FILES:
        tag = "x1-prereg-v2" if f.endswith("x1_external.py") else "p3-frozen"
        if git("cat-file", "-e", f"{tag}:{f}").returncode:
            lines.append(f"{f}: not in {tag} (not checked)")
            continue
        same = git("diff", "--quiet", tag, "--", f).returncode == 0
        lines.append(f"{f}: {'unchanged since ' + tag if same else 'CHANGED since ' + tag}")
    return lines


def thesis_stats():
    st = json.loads((ROOT / "data" / "processed" / f"{SUBJ}_stats.json").read_text())
    return np.asarray(st["ch_mean_uV"], float) * 1e-6, np.asarray(st["ch_std_uV"], float) * 1e-6


def thesis_events(ctx, per_name, names):
    """{filename: events} -> {thesis file index: events} for p2_scalars.score."""
    return {i: [tuple(e) for e in per_name.get(n, [])] for i, n in enumerate(names)}


def compare(out, ctx, names, z, label):
    """counts, flags, distances, score and scorer counts of one demo run against the thesis."""
    r = dict(run=label)
    n_here = [out["n_windows"][n] for n in names]
    n_test = [int((z["file_idx"] == i).sum()) for i in range(len(names))]
    r["windows_equal"] = n_here == n_test
    flags = np.concatenate([out["flags"][n] for n in names])
    r["signal_loss_equal"] = bool(np.array_equal(flags, z["is_signal_loss"].astype(bool)))
    D = np.concatenate([out["dists"][n][~out["flags"][n]] for n in names])
    Dt = ctx["D"][TAG]
    if D.shape == Dt.shape:
        rel = np.abs(D - Dt) / (np.abs(Dt) + 1e-6)
        r["dist_max_rel_diff"] = float(rel.max()); r["dist_share_rel_gt_1e-4"] = float((rel > 1e-4).mean())
    x = np.concatenate([out["scores"][n] for n in names])
    r["score_max_abs_diff"] = float(np.max(np.abs(x - E22.final_scalar(ctx, TAG))))
    for stage, ev in (("detector", out["detector"]), ("localized", out["events"])):
        tp, fp, nr, h = PS.score(ctx, thesis_events(ctx, ev, names))
        r[f"{stage}_tp"], r[f"{stage}_fp"], r["n_ref"], r["nonict_h"] = tp, fp, nr, h
    r["top"] = out["budget"].top
    r["q"] = out["budget"].q
    return r


def cmd_gate(a):
    t_start = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    cache = Path(a.cache) / "gate"
    z = np.load(ROOT / "data" / "testset_v2" / f"{SUBJ}.npz", allow_pickle=True)
    names = [Path(str(f)).name for f in z["files"]]
    if names != sorted(names):
        raise SystemExit("STOP: test-set file order is not file-name order; the window axes would not align")
    edfs = [Path(a.dataset) / SUBJ / n for n in names]
    missing = [str(p) for p in edfs if not p.exists()]
    if missing:
        raise SystemExit(f"STOP: EDF files not found: {missing[:5]}")
    ctx = E22.test_context(SUBJ)
    L7 = pd.read_csv(ROOT / "results" / "e23_test_look7" / "per_subject_seed.csv")
    want = {st: L7[(L7.point == "balanced") & (L7.subject == SUBJ) & (L7.seed == TAG) & (L7.stage == st)].iloc[0]
            for st in ("detector", "localized")}
    lines = ["# T1 -- demo rebuilt on the final system: identity gate on chb03 (seed 42, balanced point)\n",
             "Frozen code integrity:", *[f"- {s}" for s in integrity()], ""]

    tm = {}
    mu, sd = thesis_stats()
    print("gate: demo pipeline with the thesis statistics ...", flush=True)
    outT = DEMO.process_subject_headless([str(p) for p in edfs], cache_dir=cache, stats_override=(mu, sd), timing=tm)
    rT = compare(outT, ctx, names, z, "thesis statistics")
    rT.update(seconds=round(tm["total"], 1), hours=round(sum(outT["n_windows"].values()) * DEMO.WIN_S / 3600, 3))
    ok = all((rT[f"{st}_tp"], rT[f"{st}_fp"]) == (int(want[st].tp), int(want[st].fp)) for st in ("detector", "localized"))
    lines += ["## Gate (thesis statistics)\n", "```",
              f"detector   demo tp/fp {rT['detector_tp']}/{rT['detector_fp']}  look #7 {int(want['detector'].tp)}/{int(want['detector'].fp)}",
              f"localized  demo tp/fp {rT['localized_tp']}/{rT['localized_fp']}  look #7 {int(want['localized'].tp)}/{int(want['localized'].fp)}",
              f"alarm budget top {rT['top']:.6f} (look #7 {float(want['localized'].top):.6f}), q {rT['q']:.6f}",
              f"windows per file equal {rT['windows_equal']}, signal-loss flags equal {rT['signal_loss_equal']}",
              f"per-channel distance max relative diff {rT.get('dist_max_rel_diff', float('nan')):.2e} "
              f"(share > 1e-4: {rT.get('dist_share_rel_gt_1e-4', float('nan')):.4f})",
              f"ensemble score max |diff| {rT['score_max_abs_diff']:.2e}", "```",
              f"\n**GATE {'PASS' if ok else 'FAIL'}**\n"]
    res = dict(gate=rT, gate_pass=ok)
    if ok:
        print("gate PASS; label-free statistics ...", flush=True)
        stem = {n: Path(n).stem for n in names}
        filt = {n: np.load(cache / f"{stem[n]}.filtered.npy", mmap_mode="r") for n in names}
        flags = {n: np.load(cache / f"{stem[n]}.flag.npy") for n in names}
        moms = {n: np.load(cache / f"{stem[n]}.moments.npy") for n in names}
        b = DEMO.process_subject_phase_b(filt, flags, moms)
        trace = {}
        ev, budget = DEMO.process_subject_events(b.scores, flags, b.dists, trace=trace)
        outL = dict(n_windows={n: len(flags[n]) for n in names}, flags=flags, dists=b.dists, scores=b.scores,
                    events={f: [(e.onset_sec, e.offset_sec) for e in v] for f, v in ev.items()},
                    detector=trace["detector"], budget=budget)
        rL = compare(outL, ctx, names, z, "label-free statistics (the demo)")
        mu_l, sd_l = b.stats
        rL["stats_mean_max_abs_uV"] = float(np.max(np.abs(mu_l - mu)) * 1e6)
        rL["stats_std_rel_diff"] = [round(float(v), 4) for v in (sd_l - sd) / sd]
        lines += ["## Label-free statistics (what the demo runs)\n", "```",
                  f"detector   tp/fp {rL['detector_tp']}/{rL['detector_fp']}",
                  f"localized  tp/fp {rL['localized_tp']}/{rL['localized_fp']}   (n_ref {rL['n_ref']})",
                  f"alarm budget top {rL['top']:.6f}, q {rL['q']:.6f}",
                  f"z-score std relative diff per channel vs thesis statistics: {rL['stats_std_rel_diff']}",
                  f"z-score mean max |diff| {rL['stats_mean_max_abs_uV']:.3f} uV",
                  f"per-channel distance max relative diff {rL.get('dist_max_rel_diff', float('nan')):.2e}",
                  f"ensemble score max |diff| {rL['score_max_abs_diff']:.2e}", "```"]
        res["labelfree"] = rL
    lines.append(f"\nElapsed {time.time() - t_start:.0f} s (demo run with thesis statistics: {rT['seconds']} s "
                 f"for {rT['hours']} h).")
    (OUT / "GATE.md").write_text("\n".join(lines), encoding="utf-8")
    (OUT / "gate.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print("\n".join(lines))
    if not a.keep_cache:
        shutil.rmtree(cache, ignore_errors=True)
    if not ok:
        sys.exit(1)


def cmd_timing(a):
    OUT.mkdir(parents=True, exist_ok=True)
    edfs = sorted((Path(a.dataset) / a.subject).glob(f"{a.subject}_*.edf"))
    if not edfs:
        raise SystemExit(f"STOP: no EDF for {a.subject}")
    rows = []
    for k in range(a.runs):
        cache = Path(a.cache) / f"timing_{k}"
        shutil.rmtree(cache, ignore_errors=True)
        tm = {}
        out = DEMO.process_subject_headless([str(p) for p in edfs], cache_dir=cache, timing=tm)
        hours = sum(out["n_windows"].values()) * DEMO.WIN_S / 3600
        rows.append(dict(run=k + 1, subject=a.subject, files=len(out["n_windows"]), hours=round(hours, 3),
                         **{f"{s}_s": round(v, 1) for s, v in tm.items()}, s_per_hour=round(tm["total"] / hours, 2)))
        print(rows[-1], flush=True)
        shutil.rmtree(cache, ignore_errors=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "timing.csv", index=False)
    med = statistics.median(df.s_per_hour)
    stages = [c for c in ("phase_a_s", "stats_s", "features_s", "gae_s", "distances_and_score_s", "events_s") if c in df]
    L = [f"# T1 -- processing time of the rebuilt demo pipeline ({a.subject}, {df.hours.iloc[0]} h, {a.runs} runs)\n",
         "Full headless path (open, filter, statistics, graph and features, GAE, distances, score, alarm budget, "
         "detector, localizer), same functions as the upload flow, CPU.\n", "```", df.to_string(index=False), "```",
         f"\n**Median {med:.2f} s per hour of EEG** (range {df.s_per_hour.min():.2f}-{df.s_per_hour.max():.2f}).",
         "Median per stage (s): " + ", ".join(f"{c[:-2]} {df[c].median():.1f}" for c in stages)]
    (OUT / "TIMING.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    for name in ("gate", "timing"):
        s = sp.add_parser(name)
        s.add_argument("--dataset", required=True)
        s.add_argument("--cache", default="F:/Study/Thesis/Agent/t1_demo/cache")
        s.add_argument("--keep-cache", action="store_true")
        if name == "timing":
            s.add_argument("--subject", default="chb16")
            s.add_argument("--runs", type=int, default=5)
    a = ap.parse_args()
    cmd_gate(a) if a.cmd == "gate" else cmd_timing(a)


if __name__ == "__main__":
    main()
