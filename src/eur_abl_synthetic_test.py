#!/usr/bin/env python
"""eur_abl_synthetic_test.py -- end-to-end test of EUR_ABL on SYNTHETIC data (build container only; never on Kaggle).

World: src/r2_r1_synthetic_test.build_world (23 CHB-MIT-like cases in v9-x3-fold1/3, chb24 / PN00 / PN01 as external
features, four randomly initialised checkpoints in the record format) and its RECORD_GEN, which writes the fake record
files (p3c_freeze, e23, e22, x1 rows, calibration.json) with r2_r1's own R1.0 path. So the R1.0 / GE gates here test the
mechanics; their equivalence with the real V5 record is gate R1.0 on Kaggle (proven exact on 07/11, R1_RUN).
Checks:
  P1  the EUR_ABL notebook (built by src/eur_make_notebooks.py, run cell by cell in a fresh interpreter, 2 workers):
      every gate PASS (G-self, G-data, SMOKE, R1.0-dev / -test, GE, G-k, G-kv0, G-D0, G-enc, G-x0, G-eng, G-worker);
      every variant scored on every case except 3g on the external cases; outputs written
  N1  (non-circular) the 4a reference of a training patient is fitted WITHOUT that patient: recomputed here from the
      stored subsamples, LedoitWolf on the other training patients = the stored fit, exactly; and the 'all' fit = all 12
  N2  (non-circular) 8a latents differ from the window-graph latents (the propagation really changed), and V0's stored
      x for one case = e22_test_oneshot.final_scalar recomputed here from r2_r1's stored distances
  A   the aggregate on the run: A1 PASS, every table written (A0 reported only: synthetic record)
Negative paths: one p3c_freeze row tp + 1 -> STOP R1.0-dev (in the SMOKE, before the full run); one x1 row fp + 3 ->
STOP GE; one module edited after the build -> the notebook refuses to start (sha assert).
  python src/eur_abl_synthetic_test.py [--root DIR]
"""
import argparse
import json
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
    return {g["gate"]: g for g in json.loads((work / "eureka" / "abl" / "gates.json").read_text())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/tmp/eur_abl_synth")
    a = ap.parse_args()
    t0 = time.time()
    root = Path(a.root)
    repo, inp = W.build_world(root)
    for name, body in (("record_gen.py", W.RECORD_GEN), ("runner.py", W.RUNNER)):
        (root / name).write_text(body)
    base = dict(R2_TEST="1", THESIS_REPO=str(repo), R2_INPUT=str(inp), R1_SRC=str(repo / "src"), OMP_NUM_THREADS="1",
                OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONHASHSEED="0")
    print(W.run(root / "record_gen.py", dict(base, R2_WORK=str(root / "gen_work"), R2_SCRATCH=str(root / "gen_scratch")))[-300:])
    nbdir = root / "notebooks"
    subprocess.check_call([sys.executable, str(ROOT / "src" / "eur_make_notebooks.py")], env=dict(os.environ, EUR_NB_OUTDIR=str(nbdir)))
    nb = nbdir / "EUR_ABL.ipynb"

    def nb_env(tag):
        return dict(EUR_TEST_REPO=str(repo), EUR_TEST_INPUT=str(inp), EUR_TEST_WORK=str(root / f"work_{tag}"),
                    EUR_TEST_SCRATCH=str(root / f"scratch_{tag}"), EUR_WORKERS="2", PYTHONHASHSEED="0")

    # ---- P1: the full notebook
    t = time.time()
    print(W.run(root / "runner.py", nb_env("ok"), [nb])[-2500:])
    print(f"P1 notebook {time.time() - t:.0f} s")
    work, scr = root / "work_ok", root / "scratch_ok"
    g = gates(work)
    want = ["G-self", "G-data", "SMOKE", "R1.0-dev", "R1.0-test", "GE", "G-k", "G-kv0", "G-D0[smoke]", "G-D0[full]",
            "G-enc[smoke]", "G-enc[full]", "G-x0[full]", "G-eng[full]", "G-worker[full]"]
    assert all(g.get(w, {}).get("status") == "PASS" for w in want), {w: g.get(w, {}).get("status") for w in want}
    out = work / "eureka" / "abl"
    R = pd.read_csv(out / "per_subject.csv")
    variants = sorted(R.variant.unique())
    assert len(variants) == 17, variants
    na = json.loads((out / "not_available.json").read_text())
    assert set(na) == {"chb24", "PN00", "PN01"} and all(v == ["3g"] for v in na.values()), na
    per = R.groupby(["subject", "variant"]).size()
    assert per.min() == per.max() == 4 * 2 * 3, per.describe()
    assert R.subject.nunique() == 26, R.subject.nunique()
    for f in ("errors.csv", "curve.csv", "k.csv", "jobs.csv", "projection.json", "reference_fits.json", "SUMMARY.md",
              "smoke/per_subject.csv", "r10/dev_per_subject.csv"):
        assert (out / f).exists(), f
    k = pd.read_csv(out / "k.csv").set_index("variant").k
    assert np.isfinite(k).all() and k.nunique() > 3, k
    print("P1 PASS: every gate, 17 variants x 26 cases x 4 seeds x 2 arms x 3 stages; 3g n/a on the 3 external cases")

    # ---- N1: leave-self-out reference
    sys.path[:0] = [str(repo / "src" / "retrain"), str(repo / "src")]
    from sklearn.covariance import LedoitWolf
    fits = np.load(scr / "eur" / "ref_fits.npz")
    sub = {c: np.load(scr / "eur" / "p1" / f"{c}.npz") for c in W.TRAIN}
    tag = "clean_seed1"
    for excl in ("chb05", None):
        use = [c for c in W.TRAIN if c != excl]
        X = np.concatenate([sub[c][tag] for c in use]).astype(np.float64)
        lw = LedoitWolf().fit(X[:, 7, :])
        key = f"{tag}|{excl or 'all'}"
        assert np.array_equal(fits[key + "|loc"][7], lw.location_) and np.array_equal(fits[key + "|prec"][7], lw.precision_)
    assert not np.array_equal(fits[f"{tag}|chb05|loc"], fits[f"{tag}|all|loc"])
    print("N1 PASS: the 4a reference of a training patient excludes it; 'all' = the 12 training patients")

    # ---- N2: 8a really changes propagation; V0 x = the record function
    env = dict(os.environ, **base, R2_WORK=str(work), R2_SCRATCH=str(scr), EUR_ROOT=str(root))
    code = r'''
import os, sys, numpy as np
sys.path.insert(0, os.environ["R1_SRC"])
if __name__ == "__main__":
    import eur_abl as M
    R1 = M.R1
    M.PD.CKPT = R1.REPO / "data" / "models_v2"
    z, _ = R1.load_case("chb03", "earlier")
    idx, adj, xn, f7 = M.model_inputs(z)
    Zo = M.encode("clean_seed42", adj, xn, f7, "own"); Zs = M.encode("clean_seed42", adj, xn, f7, "self")
    _, Zr = M.PD.run_model("clean_seed42", adj, xn, f7)
    assert np.array_equal(Zo, Zr) and np.abs(Zo - Zs).max() > 1e-3, np.abs(Zo - Zs).max()
    ctx, _ = R1.ctx_from_store("chb03", "earlier", "r10")
    xm = np.load(M.SCR / "xm" / "chb03.npz")
    for t in M.TAGS:
        assert np.array_equal(xm[f"V0|{t}|x"], M.E22.final_scalar(ctx, t))
        assert not np.array_equal(xm[f"V0|{t}|x"], xm[f"1b|{t}|x"])
    print("N2 PASS")
'''
    (root / "n2.py").write_text(code)
    print(W.run(root / "n2.py", env)[-200:])

    # ---- A: aggregate on the synthetic run
    p = subprocess.run([sys.executable, str(ROOT / "src" / "eur_abl_aggregate.py"), "--run", str(out)],
                       env=dict(os.environ, R2_TEST="1", THESIS_REPO=str(repo)), capture_output=True, text=True)
    print(p.stdout[-1500:], p.stderr[-1500:])
    assert p.returncode == 0 and "A1 PASS" in p.stdout, "aggregate failed"
    for f in ("summary.csv", "bootstrap.csv", "errors_table.csv", "matched.csv", "candidates.csv", "T2.md"):
        assert (out / "aggregate" / f).exists(), f
    b = pd.read_csv(out / "aggregate" / "bootstrap.csv")
    assert {"1b - V0", "6a: fixed 0.5 % - per-patient budget", "7b: hybrid - localizer"} <= set(b.comparison)
    print("A PASS: aggregate A1 and every table")

    # ---- negative paths
    rec = repo / "results" / "p3c_freeze" / "per_subject.csv"
    keep = rec.read_text()
    d = pd.read_csv(rec)
    i = d[(d.subject == "chb01") & (d.budget == "L2f") & (d.stage == "cpd")].index[0]
    d.loc[i, "tp"] += 1
    d.to_csv(rec, index=False)
    tail = W.run(root / "runner.py", nb_env("neg1"), [nb], expect_fail="R1.0-dev")
    assert not (root / "work_neg1" / "eureka" / "abl" / "per_subject.csv").exists()
    rec.write_text(keep)
    print("NEG1 PASS: a changed record row stops the SMOKE (R1.0-dev) before the full run")
    xf = repo / "results" / "x1_external" / "rows_chb24.csv"
    keepx = xf.read_text()
    d = pd.read_csv(xf)
    d.loc[d.index[0], "fp"] += 3
    d.to_csv(xf, index=False)
    W.run(root / "runner.py", nb_env("neg2"), [nb], expect_fail="GE")
    xf.write_text(keepx)
    print("NEG2 PASS: an external record row fp + 3 stops at GE")
    m = repo / "src" / "e17b_latent_family.py"
    keepm = m.read_text()
    m.write_text(keepm + "\n# edited\n")
    W.run(root / "runner.py", nb_env("neg3"), [nb], expect_fail="modules differ")
    m.write_text(keepm)
    print("NEG3 PASS: an edited module stops the notebook before it starts")
    print(f"ALL PASS in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
