#!/usr/bin/env python
"""eur_v1_synthetic_test.py -- end-to-end test of EUR_V1 on SYNTHETIC data (build container only; never on Kaggle).

World: src/r2_r1_synthetic_test.build_world + RECORD_GEN (as src/eur_abl_synthetic_test.py). The committed EUR_ABL
reference that EUR_V1 must reproduce (results/eureka_d31f/abl: per_subject, errors, curve, k) is MADE in the world by
running the EUR_ABL notebook (variants V0 only) and copying its outputs into the world's repository -- so gates G-v5own
and G-curve are tested against an independent code path (eur_abl.score_job), not against EUR_V1's own output.
Checks:
  P1  EUR_V1 notebook (built by src/eur_make_notebooks.py --only EUR_V1, run cell by cell, 2 workers): every gate PASS;
      outputs complete
  N1  (non-circular) per-seizure flags = a brute-force rule written here (hypotheses merged when < 90 s apart; a seizure
      is caught if a merged hypothesis overlaps [onset - 30 s, offset + 60 s]) for every seizure <= 300 s that lies
      > 90 s from any other seizure, every grid row
  N2  (non-circular) one case: the shifted scores flag the same number of windows as the real scores at every budget, and
      the chance rows differ from the real rows somewhere
  N3  (non-circular) b2 clips recomputed here from the stored ensemble score of one case: at most 120 s, > 90 s apart,
      N = min(ceil(r x hours), candidates); b1 'all' = the own cpd row
  R   the reader on the run: M0-M3 PASS, every table and the figure written
Negative paths: an EUR_ABL V0 own row tp + 1 -> STOP G-v5own in the SMOKE; a curve.csv row fp + 1 -> STOP G-curve in the
SMOKE; one module edited after the build -> the notebook refuses to start (sha assert); reader on a run with a gate
removed -> STOP M1.
  python src/eur_v1_synthetic_test.py [--root DIR]
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import r2_r1_synthetic_test as W        # noqa: E402  (world builder, record generator, notebook runner: unchanged)


def gates(work):
    return {g["gate"]: g for g in json.loads((work / "eureka" / "v1" / "gates.json").read_text())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/tmp/eur_v1_synth")
    ap.add_argument("--reuse", action="store_true", help="development only: reuse an existing world and reference")
    a = ap.parse_args()
    t0 = time.time()
    root = Path(a.root)
    reuse = a.reuse and (root / "repo" / "results" / "eureka_d31f" / "abl" / "k.csv").exists()
    if reuse:                             # development only: keep the world and its EUR_ABL reference, refresh V1 code
        repo, inp = root / "repo", root / "input"
        for f in ("eur_v1.py", "eur_v1_read.py", "eur_make_notebooks.py"):
            shutil.copyfile(ROOT / "src" / f, repo / "src" / f)
        for d in root.glob("work_*"):
            if d.name != "work_abl":
                shutil.rmtree(d)
        for d in root.glob("scratch_*"):
            if d.name != "scratch_abl":
                shutil.rmtree(d)
    else:
        repo, inp = W.build_world(root)
    for name, body in (("record_gen.py", W.RECORD_GEN), ("runner.py", W.RUNNER)):
        (root / name).write_text(body)
    base = dict(R2_TEST="1", THESIS_REPO=str(repo), R2_INPUT=str(inp), R1_SRC=str(repo / "src"), OMP_NUM_THREADS="1",
                OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONHASHSEED="0")
    if not reuse:
        print(W.run(root / "record_gen.py", dict(base, R2_WORK=str(root / "gen_work"), R2_SCRATCH=str(root / "gen_scratch")))[-300:])
    nbdir = root / "notebooks"
    for only in ("EUR_ABL", "EUR_V1"):
        subprocess.check_call([sys.executable, str(ROOT / "src" / "eur_make_notebooks.py"), "--only", only],
                              env=dict(os.environ, EUR_NB_OUTDIR=str(nbdir)))

    def nb_env(tag, **kw):
        return dict(EUR_TEST_REPO=str(repo), EUR_TEST_INPUT=str(inp), EUR_TEST_WORK=str(root / f"work_{tag}"),
                    EUR_TEST_SCRATCH=str(root / f"scratch_{tag}"), EUR_WORKERS="2", PYTHONHASHSEED="0", **kw)

    # ---- the EUR_ABL reference (V0 only), copied into the world's repository
    ref = repo / "results" / "eureka_d31f" / "abl"
    if not reuse:
        t = time.time()
        print(W.run(root / "runner.py", nb_env("abl", EUR_VARIANTS="V0"), [nbdir / "EUR_ABL.ipynb"])[-600:])
        abl_out = root / "work_abl" / "eureka" / "abl"
        ref.mkdir(parents=True, exist_ok=True)
        for f in ("per_subject.csv", "errors.csv", "curve.csv", "k.csv"):
            shutil.copyfile(abl_out / f, ref / f)
        print(f"EUR_ABL reference made in {time.time() - t:.0f} s")

    # ---- P1
    t = time.time()
    nb = nbdir / "EUR_V1.ipynb"
    print(W.run(root / "runner.py", nb_env("ok", EUR_V1_NSHIFT="3"), [nb])[-2500:])
    print(f"P1 notebook {time.time() - t:.0f} s")
    work, scr = root / "work_ok", root / "scratch_ok"
    g = gates(work)
    want = ["G-self-v1", "G-data", "R1.0-dev", "R1.0-test", "GE", "G-v5own[smoke]", "G-curve[smoke]", "G-worker[smoke]",
            "SMOKE", "G-k", "G-kv1", "G-v5own[full]", "G-curve[full]", "G-worker[full]"]
    assert all(g.get(w, {}).get("status") == "PASS" for w in want), {w: g.get(w, {}).get("status") for w in want}
    out = work / "eureka" / "v1"
    grid, null, rank = (pd.read_csv(out / f) for f in ("grid.csv", "null.csv", "rank.csv"))
    seiz, own = pd.read_csv(out / "seizures.csv"), pd.read_csv(out / "own_rows.csv")
    ncase = own.subject.nunique()
    assert ncase == 26 and len(grid) == 26 * 4 * 16 * 2 and len(null) == 26 * 4 * 3 * 16 and len(rank) == 26 * 4 * 15, \
        (ncase, len(grid), len(null), len(rank))
    for f in ("own_errors.csv", "k.csv", "jobs.csv", "projection.json", "SUMMARY.md", "smoke/grid.csv", "run_meta.json"):
        assert (out / f).exists(), f
    print("P1 PASS: every gate; 26 cases x 4 seeds x 16 budgets x 2 stages; chance 3 shifts; ranked 15 per case-seed")

    # ---- N1-N3 (non-circular checks in the world's interpreter)
    env = dict(os.environ, **base, R2_WORK=str(work), R2_SCRATCH=str(scr))
    code = r'''
import os, sys, math, json, numpy as np, pandas as pd
sys.path.insert(0, os.environ["R1_SRC"])
if __name__ == "__main__":
    import eur_v1 as V
    R1, PS, E22, P3L = V.R1, V.PS, V.E22, V.P3L
    out = R1.WORK / "eureka" / "v1"
    seiz = pd.read_csv(out / "seizures.csv"); grid = pd.read_csv(out / "grid.csv"); rank = pd.read_csv(out / "rank.csv")
    own = pd.read_csv(out / "own_rows.csv")
    checked = 0
    for case, src in (("chb03", "earlier"), ("chb05", "earlier"), ("PN00", "ext")):
        ctx, _ = R1.ctx_from_store(case, src, "r10")
        refs = P3L.refs_of(ctx)
        flat = [(f, a, b) for f, v in refs.items() for a, b in v]
        for tag in ("clean_seed42", "clean_seed2"):
            x = E22.final_scalar(ctx, tag)
            for top in (0.005, 0.05, 0.2):
                det = PS.d1_events(ctx, x, 5, top)
                for i, (f, a, b) in enumerate(flat):
                    if b - a > 300 or any(j != i and g == f and (abs(a2 - b) < 90 or abs(a - b2) < 90 or (a2 < b and b2 > a))
                                          for j, (g, a2, b2) in enumerate(flat)):
                        continue
                    hyp = []
                    for e0, e1 in sorted(det.get(f, [])):
                        if hyp and e0 - hyp[-1][1] < 90: hyp[-1] = (hyp[-1][0], max(e1, hyp[-1][1]))
                        else: hyp.append((e0, e1))
                    brute = any(h1 > a - 30 and h0 < b + 60 for h0, h1 in hyp)
                    row = seiz[(seiz.subject == case) & (seiz.seed == tag) & (seiz.stage == "detector") & np.isclose(seiz.top, top)
                               & (seiz.file_idx == f) & (seiz.on_s == a)]
                    assert len(row) == 1 and int(row.caught.iloc[0]) == int(brute), (case, tag, top, f, a, len(row))
                    checked += 1
    assert checked > 20, checked
    print(f"N1 PASS: {checked} seizure flags = the brute-force rule")
    # N2
    ctx, _ = R1.ctx_from_store("chb03", "earlier", "r10")
    x = E22.final_scalar(ctx, "clean_seed1")
    xs = V.shift_scalar(ctx, x, V.shift_rng("chb03", "clean_seed1", 0))
    for top in V.GRID:
        a1 = PS.smoothed(ctx, x, 5); a2 = PS.smoothed(ctx, xs, 5)
        assert np.isfinite(a1).sum() == np.isfinite(a2).sum()
    nl = pd.read_csv(out / "null.csv")
    m = nl[(nl.subject == "chb03") & (nl.seed == "clean_seed1") & (nl["shift"] == 0)].merge(
        grid[(grid.subject == "chb03") & (grid.seed == "clean_seed1") & (grid.stage == "detector")], on="top", suffixes=("", "_r"))
    assert len(m) == 16 and ((m.tp != m.tp_r) | (m.fp != m.fp_r)).any()
    print("N2 PASS: shifted scores keep the valid-window count; chance rows differ from real rows")
    # N3
    for case, src in (("chb03", "earlier"), ("PN01", "ext")):
        ctx, _ = R1.ctx_from_store(case, src, "r10")
        sm = PS.smoothed(ctx, E22.final_scalar(ctx, "clean_seed3"), 5)
        H = ctx["n"] * 4 / 3600
        c = V.nms_candidates(sm, ctx["fidx"], 10 ** 9)
        for f in set(e[0] for e in c):
            ev = sorted((e[1], e[2]) for e in c if e[0] == f)
            assert all(b - a <= 120 for a, b in ev) and all(a2 - b1 > 90 for (_, b1), (a2, _) in zip(ev, ev[1:]))
        r = rank[(rank.subject == case) & (rank.seed == "clean_seed3") & (rank.method == "b2")]
        for _, q in r.iterrows():
            assert int(q.N) == min(len(c), math.ceil(float(q.rate) * H - 1e-9)), (case, q.rate, q.N, len(c))
    oc = own[(own.budget == "own") & (own.stage == "cpd")].merge(rank[rank.method == "b1"][rank.rate.astype(str) == "all"],
                                                                 on=["subject", "seed"], suffixes=("", "_b"))
    assert len(oc) == 26 * 4 and (oc.tp == oc.tp_b).all() and (oc.fp == oc.fp_b).all()
    print("N3 PASS: b2 clips <= 120 s and > 90 s apart, N = min(ceil(r x h), candidates); b1 all = own cpd rows")
'''
    (root / "n.py").write_text(code)
    print(W.run(root / "n.py", env)[-600:])

    # ---- R: reader
    p = subprocess.run([sys.executable, str(ROOT / "src" / "eur_v1_read.py"), "--run", str(out), "--out", str(root / "reading")],
                       env=dict(os.environ, THESIS_REPO=str(ROOT)), capture_output=True, text=True)
    print(p.stdout[-1500:], p.stderr[-2500:])
    assert p.returncode == 0 and "M0-M3 PASS" in p.stdout, "reader failed"
    for f in ("T_V1.md", "curve.csv", "own_point.csv", "rank.csv", "missed.csv", "missed_summary.csv", "fig_v1_curve.png"):
        assert (root / "reading" / f).exists(), f
    print("R PASS: reader M0-M3 and every table and the figure")

    # ---- negative paths
    neg = root / "neg_run"
    shutil.copytree(out, neg)
    gj = json.loads((neg / "gates.json").read_text())
    (neg / "gates.json").write_text(json.dumps([x for x in gj if x["gate"] != "G-curve[full]"]))
    p = subprocess.run([sys.executable, str(ROOT / "src" / "eur_v1_read.py"), "--run", str(neg), "--out", str(root / "rneg")],
                       env=dict(os.environ, THESIS_REPO=str(ROOT)), capture_output=True, text=True)
    assert p.returncode != 0 and "M1" in (p.stdout + p.stderr), p.stdout[-500:] + p.stderr[-500:]
    print("NEG0 PASS: the reader stops (M1) when a run gate is absent")
    for f, col, tag in (("per_subject.csv", "tp", "G-v5own"), ("curve.csv", "fp", "G-curve")):
        rf = ref / f
        keep = rf.read_text()
        d = pd.read_csv(rf)
        sel = (d.subject == "chb01") & (d.variant == "V0")
        if f == "per_subject.csv":
            sel &= (d.budget == "own") & (d.stage == "cpd")
        d.loc[d[sel].index[0], col] += 1
        d.to_csv(rf, index=False)
        W.run(root / "runner.py", nb_env(f"neg_{tag}", EUR_V1_NSHIFT="1"), [nb], expect_fail=tag)
        assert not (root / f"work_neg_{tag}" / "eureka" / "v1" / "grid.csv").exists()
        rf.write_text(keep)
        print(f"NEG PASS: a changed EUR_ABL {f} row stops the SMOKE at {tag} before the full run")
    m = repo / "src" / "eur_v1.py"
    keepm = m.read_text()
    m.write_text(keepm + "\n# edited\n")
    W.run(root / "runner.py", nb_env("neg_sha"), [nb], expect_fail="modules differ")
    m.write_text(keepm)
    print("NEG PASS: an edited module stops the notebook before it starts")
    print(f"ALL PASS in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
