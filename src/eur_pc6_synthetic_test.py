#!/usr/bin/env python
"""eur_pc6_synthetic_test.py -- end-to-end test of the PC6 training notebooks (EUR_PC6_11a / _11b) and src/eur_pc6_read.py
on SYNTHETIC data (build container only; never on Kaggle). Chat D37-F, design results/eureka_d37f/DESIGN_PC6.md §4, §6.

World: src/r2_r1_synthetic_test.build_world and its RECORD_GEN (as the PC8 test). Graph files: for every case of DEV + TEST
+ EXT (from the record copies the suite reads: v9-x3-fold*, thesis-r2-external-features) a synthetic {case}_g11.npz is written to the input `thesis-pc6-graphs` (11a = the record graph with its channels
permuted, 11b = the record graph with a second permutation; float16, diagonal 0, the record's window count and files) and
its manifest to repo/results/eureka_d37f/pc6_data/manifest.csv. Training: 2 epochs, 2 workers; seeds 42, 1, 2 per arm.
Runs: P0 EUR_PC1_R0 (reference), C EUR_PC7_A / _B (control) + the PC7 reading, P1 EUR_PC6_11a / _11b.
Checks:
  P1  every gate PASS incl. G-g11data, G-pc6view, G-pc7reuse (R0 seed 42 only), G-pc7rep, G-guard (2 chunks), G-pc7k,
      G-pc7r0; V0 x 4, R0 x seed 42, arm x 3 seeds on 26 cases; the arm json names its graph; pc6_views.csv all ok
  N1  (non-circular) (a) f1_core.train('gae') on views of the record .npz written HERE with adj = the 11a graph = the
      stored 11a seed-1 checkpoint exactly; (b) the 11b scalar of chb03 recomputed from model_cmp_core.node_input (the
      training construction) on the 11b graph, a per-window forward with that graph's edges, Ledoit-Wolf per channel = the
      stored scalar; (c) the 11a scalar differs from what the same checkpoint gives on the record graph (the graph is used)
  R   src/eur_pc6_read.py: gates M0 / M1 / M2 / M4, every table (R1, R1m, R5, events, seeds, machines)
Negative paths: NEG1 one graph file changed (its sha256 no longer = the manifest) -> STOP G-g11data; NEG2 a graph file with
one window fewer and a manifest that matches it -> STOP G-pc6view; NEG3 the reader with one run twice -> STOP; NEG4 an
edited module -> the notebook refuses to start.
  python src/eur_pc6_synthetic_test.py [--root DIR]
"""
import argparse
import hashlib
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
import r2_r1_synthetic_test as W        # noqa: E402
import eur_pc6_read as RD6              # noqa: E402

REF_REL = "results/eureka_d32f/pc1_r0"
CTRL_SEEDS = {"A": "42,1,2,3,4,5", "B": "42,1,2,3,6,7"}
ARM_SEEDS = "42,1,2"
P1_ = np.array([3, 0, 1, 2, 7, 4, 5, 6, 11, 8, 9, 10, 15, 12, 13, 14, 17, 16])
P2_ = np.array([17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0])


def write_graphs(inp, repo, cases_ext):
    out = inp / "thesis-pc6-graphs" / "graphs"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in sorted(inp.rglob("*.npz")):
        if "thesis-pc6-graphs" in p.parts or "thesis-r2-chbmit-features" in p.parts:   # the record copies only
            continue
        c = p.name.replace("_lf.npz", "").replace(".npz", "")
        if p.name.endswith("_lf.npz") != (c in cases_ext) or any(r["case"] == c for r in rows):
            continue
        z = np.load(p, allow_pickle=True)
        if "adj" not in z.files or "files" not in z.files:
            continue
        g = np.asarray(z["adj"])
        a11 = g[:, P1_][:, :, P1_].astype(np.float16)
        b11 = g[:, P2_][:, :, P2_].astype(np.float16)
        f = out / f"{c}_g11.npz"
        np.savez_compressed(f, adj_11a=a11, adj_11b=b11, files=z["files"], n_windows=len(g))
        rows.append(dict(case=c, file=f.name, bytes=f.stat().st_size, sha256=hashlib.sha256(f.read_bytes()).hexdigest(),
                         n_windows=len(g)))
    m = repo / "results" / "eureka_d37f" / "pc6_data"
    m.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).drop_duplicates("case").sort_values("case").to_csv(m / "manifest.csv", index=False)
    return out, m / "manifest.csv"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/tmp/eur_pc6_synth")
    a = ap.parse_args()
    t0 = time.time()
    root = Path(a.root)
    repo, inp = W.build_world(root)
    for name, body in (("record_gen.py", W.RECORD_GEN), ("runner.py", W.RUNNER)):
        (root / name).write_text(body)
    base = dict(R2_TEST="1", THESIS_REPO=str(repo), R2_INPUT=str(inp), R1_SRC=str(repo / "src"), OMP_NUM_THREADS="1",
                OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONHASHSEED="0", EUR_PC1_EPOCHS="2")
    print(W.run(root / "record_gen.py", dict(base, R2_WORK=str(root / "gen_work"), R2_SCRATCH=str(root / "gen_scratch")))[-300:])
    sys.path.insert(0, str(repo / "src"))
    ext = json.loads(subprocess.check_output([sys.executable, "-c", "import sys; sys.path.insert(0, sys.argv[1]); "
                                              "import r2_r1 as R; import json; print(json.dumps(R.EXT))", str(repo / "src")],
                                             env=dict(os.environ, **base)).decode().strip().splitlines()[-1])
    gdir, man = write_graphs(inp, repo, set(ext))
    print(f"graphs: {len(pd.read_csv(man))} files ({gdir})")
    nbdir = root / "notebooks"
    for only in ("EUR_PC1", "EUR_PC7", "EUR_PC6"):
        subprocess.check_call([sys.executable, str(ROOT / "src" / "eur_make_notebooks.py"), "--only", only],
                              env=dict(os.environ, EUR_NB_OUTDIR=str(nbdir)))

    def nb_env(tag, **kw):
        return dict(EUR_TEST_REPO=str(repo), EUR_TEST_INPUT=str(inp), EUR_TEST_WORK=str(root / f"work_{tag}"),
                    EUR_TEST_SCRATCH=str(root / f"scratch_{tag}"), EUR_WORKERS="2", PYTHONHASHSEED="0",
                    EUR_PC1_EPOCHS="2", **kw)

    # ---- P0 + C
    print(W.run(root / "runner.py", nb_env("ref"), [nbdir / "EUR_PC1_R0.ipynb"])[-300:])
    ref = repo / REF_REL
    ref.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(root / "work_ref" / "eureka" / "pc1_R0", ref)
    ctrl = {}
    for part in ("A", "B"):
        print(W.run(root / "runner.py", nb_env(f"c{part}", EUR_TEST_ARM_SEEDS=CTRL_SEEDS[part]),
                    [nbdir / f"EUR_PC7_{part}.ipynb"])[-300:])
        ctrl[part] = root / f"work_c{part}" / "eureka" / f"pc7_{part}"
    pc1 = root / "pc1_like"
    pc1.mkdir(exist_ok=True)
    rr = pd.read_csv(ref / "per_subject.csv")
    pd.concat([rr[rr.variant == "V0"], rr[rr.variant == "R0"].assign(variant="10a"),
               rr[rr.variant == "R0"].assign(variant="10b")]).to_csv(pc1 / "per_subject.csv", index=False)
    pc7 = root / "pc7_read"
    p = subprocess.run([sys.executable, str(ROOT / "src" / "eur_pc7_read.py"), "--runs", str(ctrl["A"]), str(ctrl["B"]),
                        "--ref", str(ref), "--pc1", str(pc1), "--out", str(pc7)], capture_output=True, text=True)
    assert p.returncode == 0, p.stdout[-1500:] + p.stderr[-1500:]
    print("P0 / C PASS: reference, control runs, PC7 reading")

    # ---- P1
    outs = {}
    seeds = [f"clean_seed{s}" for s in ARM_SEEDS.split(",")]
    for arm in ("11a", "11b"):
        nb = nbdir / f"EUR_PC6_{arm}.ipynb"
        srcs = "".join("".join(c["source"]) for c in json.loads(nb.read_text())["cells"])
        assert f'EUR_VARIANTS="V0,R0,{arm}"' in srcs and f'EUR_TAG="pc6_{arm}"' in srcs and 'EUR_ARM_REUSE_R0="42"' in srcs
        t = time.time()
        print(W.run(root / "runner.py", nb_env(arm, EUR_TEST_ARM_SEEDS=ARM_SEEDS), [nb])[-800:])
        print(f"P1 {arm} notebook {time.time() - t:.0f} s")
        out = root / f"work_{arm}" / "eureka" / f"pc6_{arm}"
        g = {x["gate"]: x for x in json.loads((out / "gates.json").read_text())}
        assert all(g.get(w, {}).get("status") == "PASS" for w in RD6.REQUIRED), {w: g.get(w, {}).get("status") for w in RD6.REQUIRED}
        assert len(g["G-guard"]["chunks"]) == 2 and not g["G-guard"]["skipped"] and g["G-pc7reuse"]["reused"] == ["R0/clean_seed42"]
        R = pd.read_csv(out / "per_subject.csv")
        for v, ss in (("V0", RD6.TAGS4), ("R0", ["clean_seed42"]), (arm, seeds)):
            d = R[R.variant == v]
            per = d.groupby(["subject", "seed"]).size()
            assert set(d.seed) == set(ss) and per.min() == per.max() == 6 and d.subject.nunique() == 26, (v, set(d.seed))
        js = json.loads((out / "models" / arm / "gae_v2_clean_seed1.json").read_text())
        assert js["graph"] == f"adj_{arm}" and js["in_dim"] == 30 and js["out_x"] == 12, js
        assert pd.read_csv(out / "pc6_views.csv").ok.all()
        outs[arm] = out
    print("P1 PASS: both notebooks, every gate incl. G-g11data / G-pc6view / G-pc7reuse / G-pc7rep / G-guard / G-pc7k / "
          "G-pc7r0; V0 x 4, R0 x seed 42, arm x 3 seeds on 26 cases; graph named in the arm json")

    # ---- N1
    code = r'''
import os, sys, json, numpy as np
sys.path.insert(0, os.environ["R1_SRC"])
if __name__ == "__main__":
    import torch
    from pathlib import Path
    import eur_abl as M
    import f1_core as F
    import model_cmp_core as C
    import gae_joint as G
    from torch_geometric.utils import dense_to_sparse
    from sklearn.covariance import LedoitWolf
    R1 = M.R1
    M.build_views(M.DEV, M.TEST, M.EXT)
    gdir = Path(os.environ["N1_G"])
    # (a) views written here, f1_core.train
    vd = Path(os.environ["N1_V"]); vd.mkdir(parents=True, exist_ok=True)
    for c in M.TRAIN + M.VAL:
        ref = np.load(R1.VIEWS / "earlier" / f"{c}.npz", allow_pickle=True)
        z = {k: ref[k] for k in ref.files}
        z["adj"] = np.load(gdir / f"{c}_g11.npz", allow_pickle=True)["adj_11a"]
        np.savez(vd / f"{c}.npz", **z)
        C._NPZ[c] = vd / f"{c}.npz"
    C._CACHE.clear()
    meta, _, _ = M._pc1_meta()
    mine, _, _ = F.train("gae", M.TRAIN, meta, 1, torch.device("cpu"), epochs=2, tag=" N1a")
    sd = torch.load(Path(os.environ["N1_A"]) / "models" / "11a" / "gae_v2_clean_seed1.pt")
    d = max(float((mine.state_dict()[k] - sd[k]).abs().max()) for k in sd)
    assert d == 0.0, d
    # (b) 11b scalar of chb03 from the training construction
    M.PD.CKPT = R1.REPO / "data" / "models_v2"
    z, _ = R1.load_case("chb03", "earlier")
    idx, _, _, _ = M.model_inputs(z)
    ok = ~z["is_signal_loss"].astype(bool); fidx = z["file_idx"].astype(int)
    lite = dict(n=int(len(ok)), idx=idx, ok=ok, fidx=fidx); wf = fidx[idx]
    gb = np.load(gdir / "chb03_g11.npz", allow_pickle=True)["adj_11b"]
    zz = {"adj": gb, "bp5": z["bp5"], "f7": z["f7"]}
    X30, adj, _, _ = C.node_input(zz, idx, meta)
    xm = np.load(Path(os.environ["N1_SCR"]) / "eur" / "xm" / "chb03.npz")
    worst, moved = 0.0, 0.0
    outb = Path(os.environ["N1_B"])
    for tag in ("clean_seed42", "clean_seed1", "clean_seed2"):
        mm = G.GAEModel(in_dim=30, bands=12); mm.load_state_dict(torch.load(outb / "models" / "11b" / f"gae_v2_{tag}.pt")); mm.eval()
        Z = np.empty((len(idx), 18, 16), np.float32)
        with torch.no_grad():
            for i in range(len(idx)):
                A = torch.tensor(adj[i])
                ei, ew = dense_to_sparse(A)
                Z[i] = mm.encoder(torch.tensor(X30[i]), ei, ew).numpy()
        D = np.column_stack([LedoitWolf().fit(Z[:, c].astype(np.float64)).mahalanobis(Z[:, c].astype(np.float64))
                             for c in range(18)])
        D = np.asarray(np.asarray(D, np.float32), np.float64)
        x, m = M.scalar_and_m(lite, M.member_series(D, wf, M.MEMBERS, "level"), [])
        worst = max(worst, float(np.nanmax(np.abs(x - xm[f"11b|{tag}|x"]))))
        # (c) the same checkpoint on the record graph gives another scalar
        _, adj0, xn0, f70 = M.model_inputs(z)
        D0 = M.conv(M.d_maha(M.encode(tag, adj0, xn0, f70, ckpt_dir=outb / "models" / "11b")), False)
        x0, _ = M.scalar_and_m(lite, M.member_series(D0, wf, M.MEMBERS, "level"), [])
        moved = max(moved, float(np.nanmax(np.abs(x0 - xm[f"11b|{tag}|x"]))))
    assert worst <= 1e-6 and moved > 1e-3, (worst, moved)
    print(f"N1 PASS: 11a seed 1 = f1_core.train on views written here; 11b scalar recomputed (max |dx| {worst:.1e}); "
          f"record graph gives another scalar (max |dx| {moved:.2e})")
'''
    (root / "n1.py").write_text(code)
    print(W.run(root / "n1.py", dict(base, R2_WORK=str(root / "work_n1"), R2_SCRATCH=str(root / "scratch_n1"),
                                    EUR_TAG="pc6_n1", N1_G=str(gdir), N1_V=str(root / "n1_views"), N1_A=str(outs["11a"]),
                                    N1_B=str(outs["11b"]), N1_SCR=str(root / "scratch_11b")))[-300:])

    # ---- R
    rd = root / "read"
    cmd = [sys.executable, str(ROOT / "src" / "eur_pc6_read.py"), "--runs", str(outs["11a"]), str(outs["11b"]),
           "--control", str(ctrl["A"]), str(ctrl["B"]), "--ref", str(ref), "--pc1", str(pc1), "--pc7", str(pc7)]
    p = subprocess.run(cmd + ["--out", str(rd)], capture_output=True, text=True)
    print(p.stdout[-1500:], p.stderr[-1500:])
    assert p.returncode == 0 and "M-gates / M0 / M1 / M2 PASS" in p.stdout and "M4 PASS" in p.stdout, "reader failed"
    for f in ("per_subject.csv", "errors.csv", "k.csv", "seeds.csv", "r1.csv", "r1_machine.csv", "r5.csv", "events.csv",
              "machines.csv", "gates.json", "T_PC6.md"):
        assert (rd / f).exists() and (rd / f).stat().st_size > 50, f
    r1 = pd.read_csv(rd / "r1.csv")
    assert set(r1.arm) == {"11a", "11b"} and set(pd.read_csv(rd / "r5.csv").arm) == {"11a"}
    print("R PASS: reader gates M0 / M1 / M2 / M4, every table")

    # ---- negative paths
    neg = r'''
import os, sys
sys.path.insert(0, os.environ["R1_SRC"])
if __name__ == "__main__":
    import eur_abl as M
    R1 = M.R1
    R1.OUT_ROOT = R1.WORK / "eureka"; R1.STATE["tag"] = os.environ["EUR_TAG"]
    R1.out_dir().mkdir(parents=True, exist_ok=True)
    M.build_views(M.DEV, M.TEST, M.EXT)
    want = os.environ["NEG_WANT"]
    try:
        M.pc6_prepare(["11a"])
    except SystemExit as e:
        assert want in str(e), str(e)[:300]
        print(f"NEG PASS: {want}")
    else:
        raise SystemExit("expected a STOP")
'''
    (root / "neg.py").write_text(neg)

    def neg_input(name, edit):
        d = root / name
        if d.exists():
            shutil.rmtree(d)
        shutil.copytree(inp, d)
        edit(d)
        return d

    def flip(d):
        f = d / "thesis-pc6-graphs" / "graphs" / "chb03_g11.npz"
        b = bytearray(f.read_bytes()); b[-30] ^= 0xFF; f.write_bytes(bytes(b))

    i1 = neg_input("input_neg1", flip)
    print(W.run(root / "neg.py", dict(base, R2_INPUT=str(i1), R2_WORK=str(root / "work_neg1"),
                                      R2_SCRATCH=str(root / "scratch_neg1"), EUR_TAG="neg1", NEG_WANT="G-g11data FAIL"))[-200:])
    repo2 = root / "repo_neg2"
    if repo2.exists():
        shutil.rmtree(repo2)
    shutil.copytree(repo, repo2, ignore=shutil.ignore_patterns("__pycache__"))

    def short(d):
        f = d / "thesis-pc6-graphs" / "graphs" / "chb03_g11.npz"
        z = dict(np.load(f, allow_pickle=True))
        z["adj_11a"] = z["adj_11a"][:-1]
        np.savez_compressed(f, **z)
        m = pd.read_csv(repo2 / "results" / "eureka_d37f" / "pc6_data" / "manifest.csv")
        m.loc[m.case == "chb03", "sha256"] = hashlib.sha256(f.read_bytes()).hexdigest()
        m.to_csv(repo2 / "results" / "eureka_d37f" / "pc6_data" / "manifest.csv", index=False)

    i2 = neg_input("input_neg2", short)
    print(W.run(root / "neg.py", dict(base, THESIS_REPO=str(repo2), R1_SRC=str(repo2 / "src"), R2_INPUT=str(i2),
                                      R2_WORK=str(root / "work_neg2"), R2_SCRATCH=str(root / "scratch_neg2"),
                                      EUR_TAG="neg2", NEG_WANT="G-pc6view FAIL"))[-200:])
    q = subprocess.run([sys.executable, str(ROOT / "src" / "eur_pc6_read.py"), "--runs", str(outs["11a"]), str(outs["11a"]),
                        "--control", str(ctrl["A"]), str(ctrl["B"]), "--ref", str(ref), "--pc1", str(pc1), "--pc7", str(pc7),
                        "--out", str(root / "neg3")], capture_output=True, text=True)
    assert q.returncode != 0 and "one run per arm" in (q.stdout + q.stderr)
    print("NEG3 PASS: one run twice stops the reader")
    m = repo / "src" / "eur_abl.py"
    keep = m.read_text()
    m.write_text(keep + "\n# edited\n")
    W.run(root / "runner.py", nb_env("neg4", EUR_TEST_ARM_SEEDS=ARM_SEEDS), [nbdir / "EUR_PC6_11a.ipynb"],
          expect_fail="modules differ")
    m.write_text(keep)
    print("NEG4 PASS: an edited module stops the notebook before it starts")
    print(f"ALL PASS in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
