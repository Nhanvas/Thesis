#!/usr/bin/env python
"""eur_pc1_synthetic_test.py -- end-to-end test of the retraining ablations PC1 (EUR_PC1_R0 / _10a / _10b) on SYNTHETIC
data (build container only; never on Kaggle). Chat D32-F, design results/eureka_d32f/DESIGN_PC1.md.

World: src/r2_r1_synthetic_test.build_world and its RECORD_GEN (as the other EUR tests). Training: 2 epochs
(EUR_PC1_EPOCHS, read only in test mode; the notebooks train 200).
Checks:
  P1  the three notebooks (built by src/eur_make_notebooks.py --only EUR_PC1, run cell by cell, 2 workers): every gate
      PASS incl. G-pc1const and G-pc1vec; 4 checkpoints per arm with the kept columns (input 30 / 23 / 28, target
      12 / 5 / 10); exactly V0 and the arm on every case, 4 seeds x 2 arms x 3 stages; pc1_training.json
  N1  (non-circular) (a) f1_core.train('gae') on the training cases, seed 42, 2 epochs = the stored R0 seed-42 checkpoint
      exactly (R0 is the thesis recipe); (b) train_masked for 10b seed 1 recomputed here = the stored checkpoint (the
      pool worker = the main process); (c) the 10b distance recomputed with model_cmp_core.node_input (the TRAINING
      construction, not node_x), the columns dropped by index here, a per-window PyG forward, LedoitWolf per channel and
      the record member / ensemble functions = the stored 10b scalar of chb03
  M   src/eur_pc1_merge.py on the three runs: M0 PASS, aggregate A1 PASS, T_PC1.md with 10a - R0, 10b - R0, R0 - V0
Negative paths: NEG1 an edited training module (f1_core.py) stops the notebook; NEG2 one run's V0 rows changed -> the merge STOPs (M0);
NEG3 a checkpoint json whose window count differs from V5's -> the training job STOPs.
  python src/eur_pc1_synthetic_test.py [--root DIR]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import r2_r1_synthetic_test as W        # noqa: E402  (world builder, record generator, notebook runner: unchanged)

ARMS = {"R0": (30, 12), "10a": (23, 5), "10b": (28, 10)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/tmp/eur_pc1_synth")
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
    subprocess.check_call([sys.executable, str(ROOT / "src" / "eur_make_notebooks.py"), "--only", "EUR_PC1"],
                          env=dict(os.environ, EUR_NB_OUTDIR=str(nbdir)))

    def nb_env(tag):
        return dict(EUR_TEST_REPO=str(repo), EUR_TEST_INPUT=str(inp), EUR_TEST_WORK=str(root / f"work_{tag}"),
                    EUR_TEST_SCRATCH=str(root / f"scratch_{tag}"), EUR_WORKERS="2", PYTHONHASHSEED="0",
                    EUR_PC1_EPOCHS="2")

    # ---- P1
    outs = {}
    for arm, (din, dout) in ARMS.items():
        nb = nbdir / f"EUR_PC1_{arm}.ipynb"
        srcs = "".join("".join(c["source"]) for c in json.loads(nb.read_text())["cells"])
        assert f'EUR_VARIANTS="V0,{arm}"' in srcs and f'EUR_TAG="pc1_{arm}"' in srcs, f"{arm}: variants not set"
        t = time.time()
        print(W.run(root / "runner.py", nb_env(arm), [nb])[-1500:])
        print(f"P1 {arm} notebook {time.time() - t:.0f} s")
        out = root / f"work_{arm}" / "eureka" / f"pc1_{arm}"
        g = {x["gate"]: x for x in json.loads((out / "gates.json").read_text())}
        want = ["G-self", "G-data", "G-pc1const", "G-pc1vec", "SMOKE", "R1.0-dev", "R1.0-test", "GE", "G-k", "G-kv0",
                "G-D0[smoke]", "G-D0[full]", "G-enc[smoke]", "G-enc[full]", "G-x0[full]", "G-eng[full]", "G-worker[full]"]
        assert all(g.get(w, {}).get("status") == "PASS" for w in want), {w: g.get(w, {}).get("status") for w in want}
        assert g["G-pc1vec"]["max_abs_diff"] == 0.0, g["G-pc1vec"]
        R = pd.read_csv(out / "per_subject.csv")
        assert sorted(R.variant.unique()) == sorted(["V0", arm]), R.variant.unique()
        per = R.groupby(["subject", "variant"]).size()
        assert per.min() == per.max() == 4 * 2 * 3 and R.subject.nunique() == 26, per.describe()
        md = out / "models" / arm
        for tg in ("clean_seed42", "clean_seed1", "clean_seed2", "clean_seed3"):
            js = json.loads((md / f"gae_v2_{tg}.json").read_text())
            assert js["in_dim"] == din and js["out_x"] == dout and len(js["keep_in"]) == din, (arm, tg, js["in_dim"])
            assert js["epochs"] == 2 and js["G2"] == "PASS" and (md / f"gae_v2_{tg}_DONE.json").exists()
        tr = json.loads((out / "pc1_training.json").read_text())
        assert len(tr) == 4 and not any("error" in r for r in tr), tr
        outs[arm] = out
    print("P1 PASS: three notebooks, every gate incl. G-pc1const / G-pc1vec (exact); 4 checkpoints per arm with the kept "
          "columns; V0 + arm x 26 cases x 4 seeds x 2 arms x 3 stages")

    # ---- N1
    env = dict(os.environ, **base, R2_WORK=str(root / "work_10b"), R2_SCRATCH=str(root / "scratch_10b"),
               EUR_TAG="pc1_10b", N1_R0=str(outs["R0"] / "models" / "R0"))
    code = r'''
import os, sys, json, numpy as np
sys.path.insert(0, os.environ["R1_SRC"])
if __name__ == "__main__":
    import torch
    import eur_abl as M
    import f1_core as F
    import model_cmp_core as C
    import gae_joint as G
    from pathlib import Path
    from torch_geometric.utils import dense_to_sparse
    from sklearn.covariance import LedoitWolf
    R1 = M.R1
    M.build_views(M.DEV, M.TEST, [])
    meta, _, _ = M._pc1_meta()
    R1.point_npz(M.TRAIN + M.VAL, "earlier")
    # (a) R0 = the recipe
    ref, _, _ = F.train("gae", M.TRAIN, meta, 42, torch.device("cpu"), epochs=2, tag=" N1a")
    sd = torch.load(Path(os.environ["N1_R0"]) / "gae_v2_clean_seed42.pt")
    d = max(float((ref.state_dict()[k] - sd[k]).abs().max()) for k in sd)
    assert d == 0.0, d
    # (b) 10b seed 1 reproduced
    ki, ko = [i for i in range(30) if i not in (22, 27)], [i for i in range(12) if i not in (4, 9)]
    mine, _, _ = M.train_masked(M.TRAIN, meta, 1, ki, ko, 2, tag=" N1b")
    sd = torch.load(M.arm_dir("10b") / "gae_v2_clean_seed1.pt")
    d = max(float((mine.state_dict()[k] - sd[k]).abs().max()) for k in sd)
    assert d == 0.0, d
    # (c) 10b distance of chb03 recomputed independently
    M.PD.CKPT = R1.REPO / "data" / "models_v2"
    z, _ = R1.load_case("chb03", "earlier")
    idx, _, _, _ = M.model_inputs(z)
    ok = ~z["is_signal_loss"].astype(bool); fidx = z["file_idx"].astype(int)
    lite = dict(n=int(len(ok)), idx=idx, ok=ok, fidx=fidx); wf = fidx[idx]
    X30, adj, _, _ = C.node_input(z, idx, meta)
    adj = np.asarray(z["adj"][idx], np.float32)
    xm = np.load(M.SCR / "xm" / "chb03.npz")
    worst = 0.0
    for tag in M.TAGS:
        ck = M.arm_dir("10b") / f"gae_v2_{tag}.pt"
        mm = G.GAEModel(in_dim=28, bands=10); mm.load_state_dict(torch.load(ck)); mm.eval()
        Z = np.empty((len(idx), 18, 16), np.float32)
        with torch.no_grad():
            for i in range(len(idx)):
                A = torch.tensor(np.nan_to_num(adj[i]) if np.isfinite(adj[i]).all() else np.zeros_like(adj[i]))
                ei, ew = dense_to_sparse(A)
                Z[i] = mm.encoder(torch.tensor(np.delete(X30[i], (22, 27), axis=1)), ei, ew).numpy()
        D = np.column_stack([LedoitWolf().fit(Z[:, c].astype(np.float64)).mahalanobis(Z[:, c].astype(np.float64))
                             for c in range(18)])
        D = np.asarray(np.asarray(D, np.float32), np.float64)
        x, m = M.scalar_and_m(lite, M.member_series(D, wf, M.MEMBERS, "level"), [])
        worst = max(worst, float(np.nanmax(np.abs(x - xm[f"10b|{tag}|x"]))))
    assert worst <= 1e-6, worst
    print(f"N1 PASS: R0 = f1_core.train exactly; 10b seed 1 reproduced exactly; 10b scalar recomputed (max |dx| {worst:.1e})")
'''
    (root / "n1.py").write_text(code)
    print(W.run(root / "n1.py", env)[-300:])

    # ---- M
    mo = root / "merged"
    p = subprocess.run([sys.executable, str(ROOT / "src" / "eur_pc1_merge.py"), "--runs", *map(str, outs.values()),
                        "--out", str(mo)], env=dict(os.environ, R2_TEST="1", THESIS_REPO=str(repo)), capture_output=True,
                       text=True)
    print(p.stdout[-2500:], p.stderr[-1500:])
    assert p.returncode == 0 and "M0 PASS" in p.stdout and "A1 PASS" in p.stdout, "merge failed"
    t = (mo / "T_PC1.md").read_text()
    assert all(s in t for s in ("10a - R0", "10b - R0", "R0 - V0")), t
    T2 = (mo / "aggregate" / "T2.md").read_text()
    assert all(f"| {v} |" in T2 for v in ("V0", "R0", "10a", "10b")), T2[:500]
    print("M PASS: merge M0, aggregate A1, T_PC1 and T2 with every arm")

    # ---- negative paths
    m = repo / "src" / "f1_core.py"      # a training module, pinned for PC1 only
    keepm = m.read_text()
    m.write_text(keepm + "\n# edited\n")
    W.run(root / "runner.py", nb_env("neg1"), [nbdir / "EUR_PC1_10a.ipynb"], expect_fail="modules differ")
    m.write_text(keepm)
    print("NEG1 PASS: an edited module stops the notebook before it starts")
    bad = root / "neg2_run"
    shutil.copytree(outs["10b"], bad)
    ps = pd.read_csv(bad / "per_subject.csv")
    i = ps.index[ps.variant == "V0"][0]
    ps.loc[i, "tp"] = ps.loc[i, "tp"] + 1
    ps.to_csv(bad / "per_subject.csv", index=False)
    p = subprocess.run([sys.executable, str(ROOT / "src" / "eur_pc1_merge.py"), "--runs", str(outs["R0"]), str(bad),
                        "--out", str(root / "neg2_out")], env=dict(os.environ, R2_TEST="1", THESIS_REPO=str(repo)),
                       capture_output=True, text=True)
    assert p.returncode != 0 and "STOP M0" in (p.stdout + p.stderr), p.stdout[-500:] + p.stderr[-500:]
    print("NEG2 PASS: changed V0 rows stop the merge")
    code3 = r'''
import os, sys, json
sys.path.insert(0, os.environ["R1_SRC"])
if __name__ == "__main__":
    os.environ["EUR_TAG"] = "pc1_neg3"
    import eur_abl as M
    M.build_views(M.DEV, M.TEST, [])
    js = M.REPO / "data" / "models_v2" / "gae_v2_clean_seed42.json"
    keep = js.read_text(); m = json.loads(keep)
    s0 = sorted(m["n_train"])[0]; m["n_train"][s0] += 1
    js.write_text(json.dumps(m))
    try:
        r = M.train_arm_job(("10a", "clean_seed42", 1))
    finally:
        js.write_text(keep)
    assert "error" in r and "training windows" in r["error"], r
    print("NEG3 PASS")
'''
    (root / "neg3.py").write_text(code3)
    print(W.run(root / "neg3.py", dict(base, R2_WORK=str(root / "work_neg3"), R2_SCRATCH=str(root / "scratch_neg3")))[-100:])
    print(f"ALL PASS in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
