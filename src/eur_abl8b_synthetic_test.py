#!/usr/bin/env python
"""eur_abl8b_synthetic_test.py -- end-to-end test of EUR_ABL8B (ablation 8b, no encoder) on SYNTHETIC data
(build container only; never on Kaggle). Chat D32-F, design results/eureka_d32f/DESIGN_8B.md.

World: src/r2_r1_synthetic_test.build_world and its RECORD_GEN, as src/eur_abl_synthetic_test.py.
Checks:
  P1  the EUR_ABL8B notebook (built by src/eur_make_notebooks.py --only EUR_ABL8B, run cell by cell, 2 workers): every
      gate PASS (G-self, G-data, SMOKE, R1.0-dev / -test, GE, G-k, G-kv0, G-D0, G-enc, G-x0, G-eng, G-worker); exactly
      the variants V0 and 8b on every case, 4 seeds x 2 arms x 3 stages; output folder abl8b; the 4a reference pass
      skipped (no reference_fits.json)
  N1  (non-circular) node_x = an independent float32 construction of the encoder input (written here from the record
      formula, numpy only); the 8b scalar of one case = the record member / ensemble functions applied to the LedoitWolf
      distances of that independent input; 8b differs from V0; V0's scalar = e22_test_oneshot.final_scalar
  A   the aggregate (src/eur_abl_aggregate.py, unchanged) on the run: A1 PASS, T2 holds the 8b row
Negative paths: one module edited after the build -> the notebook refuses to start (sha assert); an unknown variant in
EUR_VARIANTS -> STOP.
  python src/eur_abl8b_synthetic_test.py [--root DIR]
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import r2_r1_synthetic_test as W        # noqa: E402  (world builder, record generator, notebook runner: unchanged)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/tmp/eur_abl8b_synth")
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
    subprocess.check_call([sys.executable, str(ROOT / "src" / "eur_make_notebooks.py"), "--only", "EUR_ABL8B"],
                          env=dict(os.environ, EUR_NB_OUTDIR=str(nbdir)))
    nb = nbdir / "EUR_ABL8B.ipynb"
    srcs = "".join("".join(c["source"]) for c in json.loads(nb.read_text())["cells"])
    assert 'EUR_VARIANTS="V0,8b"' in srcs and 'EUR_TAG="abl8b"' in srcs, "variants not set"

    def nb_env(tag):
        return dict(EUR_TEST_REPO=str(repo), EUR_TEST_INPUT=str(inp), EUR_TEST_WORK=str(root / f"work_{tag}"),
                    EUR_TEST_SCRATCH=str(root / f"scratch_{tag}"), EUR_WORKERS="2", PYTHONHASHSEED="0")

    # ---- P1
    t = time.time()
    print(W.run(root / "runner.py", nb_env("ok"), [nb])[-2500:])
    print(f"P1 notebook {time.time() - t:.0f} s")
    work, scr = root / "work_ok", root / "scratch_ok"
    out = work / "eureka" / "abl8b"
    g = {x["gate"]: x for x in json.loads((out / "gates.json").read_text())}
    want = ["G-self", "G-data", "SMOKE", "R1.0-dev", "R1.0-test", "GE", "G-k", "G-kv0", "G-D0[smoke]", "G-D0[full]",
            "G-enc[smoke]", "G-enc[full]", "G-x0[full]", "G-eng[full]", "G-worker[full]"]
    assert all(g.get(w, {}).get("status") == "PASS" for w in want), {w: g.get(w, {}).get("status") for w in want}
    R = pd.read_csv(out / "per_subject.csv")
    assert sorted(R.variant.unique()) == ["8b", "V0"], R.variant.unique()
    per = R.groupby(["subject", "variant"]).size()
    assert per.min() == per.max() == 4 * 2 * 3 and R.subject.nunique() == 26, per.describe()
    assert not (out / "reference_fits.json").exists(), "the 4a reference pass ran"
    k = pd.read_csv(out / "k.csv")
    assert list(k.variant) == ["V0", "8b"], k
    meta = json.loads((out / "run_meta.json").read_text())
    assert set(meta["variants"]) == {"V0", "8b"}, meta["variants"]
    print("P1 PASS: every gate; V0 + 8b x 26 cases x 4 seeds x 2 arms x 3 stages; 4a pass skipped; folder abl8b")

    # ---- N1
    env = dict(os.environ, **base, R2_WORK=str(work), R2_SCRATCH=str(scr))
    code = r'''
import os, sys, json, numpy as np
sys.path.insert(0, os.environ["R1_SRC"])
if __name__ == "__main__":
    import eur_abl as M
    R1 = M.R1
    M.PD.CKPT = R1.REPO / "data" / "models_v2"
    from sklearn.covariance import LedoitWolf
    z, _ = R1.load_case("chb03", "earlier")
    idx, adj, xn, f7 = M.model_inputs(z)
    ok = ~z["is_signal_loss"].astype(bool); fidx = z["file_idx"].astype(int)
    lite = dict(n=int(len(ok)), idx=idx, ok=ok, fidx=fidx); wf = fidx[idx]
    xm = np.load(M.SCR / "xm" / "chb03.npz")
    ctx, _ = R1.ctx_from_store("chb03", "earlier", "r10")
    for tag in M.TAGS:
        meta = json.loads((M.PD.CKPT / f"gae_v2_{tag}.json").read_text())
        mu, sd, clip = np.array(meta["add_mean"]), np.array(meta["add_std"]), meta["clip"]
        fa = ((np.clip((f7 - mu) / sd, -clip, clip) + clip) / (2 * clip)).astype(np.float32)
        A = adj.astype(np.float32)
        An = A / (A.max(axis=(1, 2), keepdims=True) + np.float32(1e-8))
        Xi = np.concatenate([An, xn.astype(np.float32), fa], axis=2).astype(np.float32)
        Xm = M.node_x(tag, adj, xn, f7)
        assert Xm.shape == Xi.shape == (len(adj), 18, 30), (Xm.shape, Xi.shape)
        assert np.array_equal(Xm, Xi), np.abs(Xm - Xi).max()
        D = np.column_stack([LedoitWolf().fit(Xi[:, c].astype(np.float64)).mahalanobis(Xi[:, c].astype(np.float64))
                             for c in range(18)])
        D = np.asarray(np.asarray(D, np.float32), np.float64)
        x, m = M.scalar_and_m(lite, M.member_series(D, wf, M.MEMBERS, "level"), [])
        assert np.array_equal(x, xm[f"8b|{tag}|x"]) and np.array_equal(m, xm[f"8b|{tag}|m"]), tag
        assert not np.array_equal(xm[f"8b|{tag}|x"], xm[f"V0|{tag}|x"]), tag
        assert np.array_equal(xm[f"V0|{tag}|x"], M.E22.final_scalar(ctx, tag)), tag
    print("N1 PASS")
'''
    (root / "n1.py").write_text(code)
    print(W.run(root / "n1.py", env)[-200:])

    # ---- A
    p = subprocess.run([sys.executable, str(ROOT / "src" / "eur_abl_aggregate.py"), "--run", str(out)],
                       env=dict(os.environ, R2_TEST="1", THESIS_REPO=str(repo)), capture_output=True, text=True)
    print(p.stdout[-1200:], p.stderr[-1200:])
    assert p.returncode == 0 and "A1 PASS" in p.stdout, "aggregate failed"
    t2 = (out / "aggregate" / "T2.md").read_text()
    assert "| 8b |" in t2 and "| V0 |" in t2, t2[:500]
    b = pd.read_csv(out / "aggregate" / "bootstrap.csv")
    assert "8b - V0" in set(b.comparison)
    print("A PASS: aggregate A1, T2 with the 8b row")

    # ---- negative paths
    m = repo / "src" / "e17b_latent_family.py"
    keepm = m.read_text()
    m.write_text(keepm + "\n# edited\n")
    W.run(root / "runner.py", nb_env("neg1"), [nb], expect_fail="modules differ")
    m.write_text(keepm)
    print("NEG1 PASS: an edited module stops the notebook before it starts")
    code2 = r'''
import os, sys
sys.path.insert(0, os.environ["R1_SRC"])
if __name__ == "__main__":
    os.environ["EUR_VARIANTS"] = "V0,9z"
    import eur_abl as M
    try:
        M.selected()
    except SystemExit as e:
        assert "unknown variants" in str(e); print("NEG2 PASS")
    else:
        raise AssertionError("unknown variant accepted")
'''
    (root / "neg2.py").write_text(code2)
    print(W.run(root / "neg2.py", env)[-100:])
    print(f"ALL PASS in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
