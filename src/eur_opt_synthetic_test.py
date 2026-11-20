#!/usr/bin/env python
"""eur_opt_synthetic_test.py -- end-to-end test of EUR_OPT (optimisations O6a / O6b / O7) on SYNTHETIC data
(build container only; never on Kaggle). Chat D32-F, design results/eureka_d32f/DESIGN_O6_O7.md.

World: src/r2_r1_synthetic_test.build_world and its RECORD_GEN, as src/eur_abl_synthetic_test.py.
Checks:
  P1  the EUR_OPT notebook (built by src/eur_make_notebooks.py --only EUR_OPT, run cell by cell, 2 workers): every gate
      PASS incl. G-mix1 (smoke and full) and G-self (O6 K=1, two-mode world, O7 context); exactly V0, O6a, O6b, O7 on
      every case, 4 seeds x 2 arms x 3 stages; output folder opt; mix_diag.csv with K per channel, the flag shares and the
      lag-1 rows of V0 and O7
  N1  (non-circular) O7: the 3-window context recomputed here with plain numpy loops, LedoitWolf per channel, then the
      record member / ensemble functions = the stored O7 scalar; O6b differs from V0; V0 = e22_test_oneshot.final_scalar
  A   the aggregate (unchanged) on the run: A1 PASS, T2 holds the O6a, O6b, O7 rows
Negative path: one module edited after the build -> the notebook refuses to start.
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
    ap.add_argument("--root", default="/tmp/eur_opt_synth")
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
    subprocess.check_call([sys.executable, str(ROOT / "src" / "eur_make_notebooks.py"), "--only", "EUR_OPT"],
                          env=dict(os.environ, EUR_NB_OUTDIR=str(nbdir)))
    nb = nbdir / "EUR_OPT.ipynb"
    srcs = "".join("".join(c["source"]) for c in json.loads(nb.read_text())["cells"])
    assert 'EUR_VARIANTS="V0,O6a,O6b,O7"' in srcs and 'EUR_TAG="opt"' in srcs, "variants not set"

    def nb_env(tag):
        return dict(EUR_TEST_REPO=str(repo), EUR_TEST_INPUT=str(inp), EUR_TEST_WORK=str(root / f"work_{tag}"),
                    EUR_TEST_SCRATCH=str(root / f"scratch_{tag}"), EUR_WORKERS="2", PYTHONHASHSEED="0")

    # ---- P1
    t = time.time()
    print(W.run(root / "runner.py", nb_env("ok"), [nb])[-2500:])
    print(f"P1 notebook {time.time() - t:.0f} s")
    work, scr = root / "work_ok", root / "scratch_ok"
    out = work / "eureka" / "opt"
    g = {x["gate"]: x for x in json.loads((out / "gates.json").read_text())}
    want = ["G-self", "G-data", "SMOKE", "R1.0-dev", "R1.0-test", "GE", "G-k", "G-kv0", "G-D0[smoke]", "G-D0[full]",
            "G-enc[smoke]", "G-enc[full]", "G-mix1[smoke]", "G-mix1[full]", "G-x0[full]", "G-eng[full]", "G-worker[full]"]
    assert all(g.get(w, {}).get("status") == "PASS" for w in want), {w: g.get(w, {}).get("status") for w in want}
    R = pd.read_csv(out / "per_subject.csv")
    assert sorted(R.variant.unique()) == ["O6a", "O6b", "O7", "V0"], R.variant.unique()
    per = R.groupby(["subject", "variant"]).size()
    assert per.min() == per.max() == 4 * 2 * 3 and R.subject.nunique() == 26, per.describe()
    assert not (out / "reference_fits.json").exists(), "the 4a reference pass ran"
    k = pd.read_csv(out / "k.csv")
    assert list(k.variant) == ["V0", "O6a", "O6b", "O7"], k
    meta = json.loads((out / "run_meta.json").read_text())
    assert set(meta["variants"]) == {"V0", "O6a", "O6b", "O7"}, meta["variants"]
    md = pd.read_csv(out / "mix_diag.csv")
    mx = md[md.variant.isin(["mixbic", "mix2"])]
    assert len(mx) == 26 * 4 * 18 * 2, len(mx)
    assert set(mx[mx.variant == "mix2"].K) == {2} and mx[mx.variant == "mixbic"].K.between(1, 4).all()
    assert mx[mx.case == "chb01"].flag_share_outside_largest.notna().all()
    lg = md[md.lag1.notna()] if "lag1" in md else md.iloc[:0]
    assert set(lg.variant) == {"V0", "O7"} and len(lg) == 26 * 4 * 2, len(lg)
    print("P1 PASS: every gate incl. G-mix1; V0, O6a, O6b, O7 x 26 cases x 4 seeds x 2 arms x 3 stages; mix_diag complete; "
          f"O6a K distribution {mx[mx.variant == 'mixbic'].K_used.value_counts().to_dict()}")

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
        _, Z = M.PD.run_model(tag, adj, xn, f7)
        Z = Z.astype(np.float64)
        C = np.empty_like(Z)
        for i in range(len(Z)):
            nb = [j for j in (i - 1, i, i + 1) if 0 <= j < len(Z) and wf[j] == wf[i]]
            C[i] = Z[nb].mean(axis=0)
        D = np.column_stack([LedoitWolf().fit(C[:, c]).mahalanobis(C[:, c]) for c in range(18)])
        D = np.asarray(np.asarray(D, np.float32), np.float64)
        x, m = M.scalar_and_m(lite, M.member_series(D, wf, M.MEMBERS, "level"), [])
        assert np.allclose(x, xm[f"O7|{tag}|x"], rtol=0, atol=1e-12) and np.allclose(m, xm[f"O7|{tag}|m"], rtol=0, atol=1e-9), tag
        assert not np.array_equal(xm[f"O6b|{tag}|x"], xm[f"V0|{tag}|x"]), tag
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
    assert all(f"| {v} |" in t2 for v in ("V0", "O6a", "O6b", "O7")), t2[:500]
    b = pd.read_csv(out / "aggregate" / "bootstrap.csv")
    assert {"O6a - V0", "O6b - V0", "O7 - V0"} <= set(b.comparison)
    print("A PASS: aggregate A1, T2 with the O6a, O6b, O7 rows")

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
