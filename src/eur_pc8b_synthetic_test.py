#!/usr/bin/env python
"""eur_pc8b_synthetic_test.py -- end-to-end test of PC8b (EUR_PC8_d / _e and src/eur_pc8b_read.py) on SYNTHETIC data
(build container only; never on Kaggle). Chat D37-F, design results/eureka_d37f/DESIGN_PC8B.md.

Step 0 runs src/eur_pc8_synthetic_test.py --root ROOT first (PC8 end to end on the changed eur_abl.py: regression), and
PC8b then runs in the same synthetic world: its reference run (PC1's R0), control runs (PC7-like) with the PC7 reading,
the three PC8 runs and the PC8 reading are the inputs of the PC8b reader, exactly as on the real data.
Runs: P1 the two PC8b notebooks (built by src/eur_make_notebooks.py --only EUR_PC8B, run cell by cell) with test seeds
42,1,2 per arm (two chunks) and R0 = seed 42 reused.
Checks:
  P1  every gate PASS incl. G-pc8cols, G-pc7reuse, G-pc7plat, G-pc7rep, G-guard (2 chunks), G-pc7k, G-pc7r0; V0 x 4
      seeds, R0 x seed 42 only, the arm x 42 / 1 / 2 on every case; arm json in_dim / out_x = 25 / 7 (P8d), 12 / 12 (P8e);
      G-pc8cols lists the kept columns by name; run_meta holds cpu_model and arm_seeds_by_arm
  N1  (non-circular) (a) P8e seed 1 re-trained in the main process with columns chosen BY NAME from the test's own list =
      the pool worker's checkpoint exactly; (b) the P8e scalar of chb03 recomputed from model_cmp_core.node_input (the
      TRAINING construction), columns 18-29 cut by numpy, a per-window forward, Ledoit-Wolf per channel = the stored
      scalar; (c) parameters of P8d / P8e = the formula of the GCN encoder and the decoder
  U   add_sets (unseen = validation + test, validation) and split_lists (ast) on known inputs
  R   src/eur_pc8b_read.py on the two runs, the P8c run, the PC8 reading, the control, the reference, the PC1-like folder
      and the PC7 reading: every gate (M-gates, M0, M1, M2, M4, M5, M6, M7), every table; the merged P8c rows = the PC8
      run's rows; unseen = 11 patients
Negative paths: NEG1 G-pc8cols FAILs when P8e's columns differ from the design (direct call); NEG2 a PC8 reading P8c row
changed -> STOP M6; NEG3 the PC8 reading's P8c - R0 changed -> STOP M7; NEG4 a split source with another validation set ->
STOP M5; NEG5 an edited pinned module -> EUR_PC8_d refuses to start; NEG6 --p8c given the P8a run -> STOP; NEG7 a PC8b
run's R0 seed-42 row changed -> STOP M1; NEG8 the same run twice -> STOP.
  python src/eur_pc8b_synthetic_test.py [--root DIR]
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
import r2_r1_synthetic_test as W        # noqa: E402  (world builder, notebook runner: unchanged)
import eur_pc8b_read as RB              # noqa: E402

REF_REL = "results/eureka_d32f/pc1_r0"
ARM_SEEDS = "42,1,2"
DIMS = {"P8d": (25, 7), "P8e": (12, 12)}
NAMES = ([f"adj{c}" for c in range(18)] + [f"rel_{b}" for b in ("delta", "theta", "alpha", "beta", "gamma")] +
         [f"logbp_{b}" for b in ("delta", "theta", "alpha", "beta", "gamma")] + ["log_linelen", "slog_kurtosis"])


def unit_checks(root):
    P = pd.DataFrame(dict(set=["development"] * 3 + ["test"] * 2 + ["external"], variant="R0", seed="s",
                          subject=["chb01", "chb10", "chb22", "chb03", "chb06", "s01"], sens=1.0, f1=1.0, fa=1.0))
    Q = RB.add_sets(P, ["chb10", "chb22"], ["chb03", "chb06"])
    assert sorted(Q[Q.set == "unseen"].subject) == ["chb03", "chb06", "chb10", "chb22"]
    assert sorted(Q[Q.set == "validation"].subject) == ["chb10", "chb22"] and len(Q[Q.set == "development"]) == 3
    tr, va = RB.split_lists()
    assert va == ["chb10", "chb11", "chb22"] and len(tr) == 12 and "chb21" in tr, (tr, va)
    bad = root / "bad_split.py"
    bad.write_text("TRAIN = ['chb01']\n")
    try:
        RB.split_lists(bad)
    except SystemExit as e:
        assert "STOP M5" in str(e)
    else:
        raise SystemExit("expected a STOP")
    print("U PASS: add_sets (unseen, validation); split_lists read with ast; missing VAL -> STOP")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/tmp/eur_pc8b_synth")
    a = ap.parse_args()
    t0 = time.time()
    root = Path(a.root)
    root.mkdir(parents=True, exist_ok=True)
    unit_checks(root)

    # ---- step 0: PC8 end to end in the same world (regression of eur_abl.py; inputs of the PC8b reader)
    t = time.time()
    p = subprocess.run([sys.executable, str(ROOT / "src" / "eur_pc8_synthetic_test.py"), "--root", str(root)],
                       capture_output=True, text=True)
    (root / "pc8_test.log").write_text(p.stdout + p.stderr)
    assert p.returncode == 0 and "ALL PASS" in p.stdout, p.stdout[-2000:] + p.stderr[-2000:]
    print(f"step 0 PASS: src/eur_pc8_synthetic_test.py ALL PASS on the changed eur_abl.py ({time.time() - t:.0f} s)")
    repo, inp = root / "repo", root / "input" / "datasets" / "u"
    ref, pc1, pc7, pc8 = repo / REF_REL, root / "pc1_like", root / "pc7_read", root / "read"
    ctrl = {part: root / f"work_c{part}" / "eureka" / f"pc7_{part}" for part in ("A", "B")}
    p8 = {arm: root / f"work_{arm[-1]}" / "eureka" / f"pc8_{arm[-1]}" for arm in ("P8a", "P8b", "P8c")}
    for x in [ref, pc1, pc7, pc8, *ctrl.values(), *p8.values()]:
        assert x.exists(), x
    base = dict(R2_TEST="1", THESIS_REPO=str(repo), R2_INPUT=str(inp), R1_SRC=str(repo / "src"), OMP_NUM_THREADS="1",
                OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONHASHSEED="0", EUR_PC1_EPOCHS="2")
    nbdir = root / "notebooks"
    subprocess.check_call([sys.executable, str(ROOT / "src" / "eur_make_notebooks.py"), "--only", "EUR_PC8B"],
                          env=dict(os.environ, EUR_NB_OUTDIR=str(nbdir)))

    def nb_env(tag, **kw):
        return dict(EUR_TEST_REPO=str(repo), EUR_TEST_INPUT=str(inp), EUR_TEST_WORK=str(root / f"work_{tag}"),
                    EUR_TEST_SCRATCH=str(root / f"scratch_{tag}"), EUR_WORKERS="2", PYTHONHASHSEED="0",
                    EUR_PC1_EPOCHS="2", **kw)

    # ---- P1: the two PC8b notebooks
    outs = {}
    seeds = [f"clean_seed{s}" for s in ARM_SEEDS.split(",")]
    for arm in ("P8d", "P8e"):
        part = arm[-1]
        nb = nbdir / f"EUR_PC8_{part}.ipynb"
        srcs = "".join("".join(c["source"]) for c in json.loads(nb.read_text())["cells"])
        assert (f'EUR_VARIANTS="V0,R0,{arm}"' in srcs and f'EUR_TAG="pc8_{part}"' in srcs and 'EUR_ARM_SEEDS_R0="42"' in srcs
                and 'EUR_ARM_REUSE_R0="42"' in srcs and 'EUR_ARM_SEEDS="42,1,2,3,4,5,6,7"' in srcs
                and "DESIGN_PC8B.md" in srcs), arm
        t = time.time()
        print(W.run(root / "runner.py", nb_env(part, EUR_TEST_ARM_SEEDS=ARM_SEEDS), [nb])[-1200:])
        print(f"P1 {arm} notebook {time.time() - t:.0f} s")
        out = root / f"work_{part}" / "eureka" / f"pc8_{part}"
        g = {x["gate"]: x for x in json.loads((out / "gates.json").read_text())}
        want = RB.P8.REQUIRED
        assert all(g.get(w, {}).get("status") == "PASS" for w in want), {w: g.get(w, {}).get("status") for w in want}
        assert len(g["G-guard"]["chunks"]) == 2 and not g["G-guard"]["skipped"], g["G-guard"]
        assert g["G-pc7reuse"]["reused"] == ["R0/clean_seed42"], g["G-pc7reuse"]
        kept = g["G-pc8cols"]["arms"][arm]["keep_in"]
        want_kept = [n for n in NAMES if not (n.startswith("rel_") if arm == "P8d" else n.startswith("adj"))]
        assert kept == want_kept, (arm, kept)
        R = pd.read_csv(out / "per_subject.csv")
        for v, ss in (("V0", RB.TAGS4), ("R0", ["clean_seed42"]), (arm, seeds)):
            d = R[R.variant == v]
            per = d.groupby(["subject", "seed"]).size()
            assert set(d.seed) == set(ss) and per.min() == per.max() == 6 and d.subject.nunique() == 26, (v, set(d.seed))
        js = json.loads((out / "models" / arm / "gae_v2_clean_seed1.json").read_text())
        assert (js["in_dim"], js["out_x"]) == DIMS[arm], (arm, js["in_dim"], js["out_x"])
        meta = json.loads((out / "run_meta.json").read_text())
        assert meta.get("cpu_model") and meta["arm_seeds_by_arm"][arm] == seeds and meta["arm_seeds_by_arm"]["R0"] == ["clean_seed42"]
        assert not (out / "models" / "R0" / "gae_v2_clean_seed1.pt").exists(), "R0 must not be trained in PC8b"
        outs[arm] = out
    print("P1 PASS: two notebooks, every gate incl. G-pc8cols (kept columns by name) / G-pc7reuse / G-pc7rep / G-guard / "
          "G-pc7k / G-pc7r0; V0 x 4, R0 x seed 42, arm x 3 seeds, 26 cases; dimensions 25 / 7 and 12 / 12; CPU model")

    # ---- N1
    code = r'''
import os, sys, json, numpy as np
sys.path.insert(0, os.environ["R1_SRC"])
if __name__ == "__main__":
    import torch
    import eur_abl as M
    import model_cmp_core as C
    import gae_joint as G
    from pathlib import Path
    from torch_geometric.utils import dense_to_sparse
    from sklearn.covariance import LedoitWolf
    R1 = M.R1
    NAMES = json.loads(os.environ["N1_NAMES"])
    M.build_views(M.DEV, M.TEST, [])
    meta, _, _ = M._pc1_meta()
    R1.point_npz(M.TRAIN + M.VAL, "earlier")
    # (a) P8e seed 1, columns by name (drop the connectivity row; target unchanged)
    ki = [i for i, n in enumerate(NAMES) if not n.startswith("adj")]
    ko = list(range(len(NAMES[18:])))
    mine, info, _ = M.train_masked(M.TRAIN, meta, 1, ki, ko, 2, tag=" N1a")
    sd = torch.load(Path(os.environ["N1_E"]) / "models" / "P8e" / "gae_v2_clean_seed1.pt")
    d = max(float((mine.state_dict()[k] - sd[k]).abs().max()) for k in sd)
    assert d == 0.0, d
    # (c) parameters = 64 * in + 64 + 64 * 16 + 16 + 16 * 32 + 32 + 32 * out + out
    for arm, (i_, o_, n_) in {"P8d": (25, 7, 3479), "P8e": (12, 12, 2812)}.items():
        n = sum(q.numel() for q in G.GAEModel(in_dim=i_, bands=o_).parameters())
        assert n == 64 * i_ + 64 + 64 * 16 + 16 + 16 * 32 + 32 + 32 * o_ + o_ == n_, (arm, n)
    # (b) P8e scalar of chb03 from the training construction
    oute = Path(os.environ["N1_E"])
    M.PD.CKPT = R1.REPO / "data" / "models_v2"
    z, _ = R1.load_case("chb03", "earlier")
    idx, _, _, _ = M.model_inputs(z)
    ok = ~z["is_signal_loss"].astype(bool); fidx = z["file_idx"].astype(int)
    lite = dict(n=int(len(ok)), idx=idx, ok=ok, fidx=fidx); wf = fidx[idx]
    X30, adj, _, _ = C.node_input(z, idx, meta)
    adj = np.asarray(z["adj"][idx], np.float32)
    xm = np.load(Path(os.environ["N1_SCR_E"]) / "eur" / "xm" / "chb03.npz")
    worst = 0.0
    for tag in ("clean_seed42", "clean_seed1", "clean_seed2"):
        mm = G.GAEModel(in_dim=12, bands=12); mm.load_state_dict(torch.load(oute / "models" / "P8e" / f"gae_v2_{tag}.pt")); mm.eval()
        Z = np.empty((len(idx), 18, 16), np.float32)
        with torch.no_grad():
            for i in range(len(idx)):
                A = torch.tensor(adj[i] if np.isfinite(adj[i]).all() else np.zeros_like(adj[i]))
                ei, ew = dense_to_sparse(A)
                Z[i] = mm.encoder(torch.tensor(np.ascontiguousarray(X30[i][:, 18:30])), ei, ew).numpy()
        D = np.column_stack([LedoitWolf().fit(Z[:, c].astype(np.float64)).mahalanobis(Z[:, c].astype(np.float64))
                             for c in range(18)])
        D = np.asarray(np.asarray(D, np.float32), np.float64)
        x, m = M.scalar_and_m(lite, M.member_series(D, wf, M.MEMBERS, "level"), [])
        worst = max(worst, float(np.nanmax(np.abs(x - xm[f"P8e|{tag}|x"]))))
    assert worst <= 1e-6, worst
    print(f"N1 PASS: P8e seed 1 reproduced exactly (columns by name); P8e scalar recomputed (max |dx| {worst:.1e}); parameters")
'''
    (root / "n1b.py").write_text(code)
    print(W.run(root / "n1b.py", dict(base, R2_WORK=str(root / "work_n1b"), R2_SCRATCH=str(root / "scratch_n1b"),
                                     EUR_TAG="pc8b_n1", N1_NAMES=json.dumps(NAMES), N1_E=str(outs["P8e"]),
                                     N1_SCR_E=str(root / "scratch_e")))[-300:])

    # ---- R: the reader
    def reader(tag, runs=None, p8c=None, pc8_dir=None, extra=()):
        r_ = runs or [str(outs["P8d"]), str(outs["P8e"])]
        return subprocess.run([sys.executable, str(ROOT / "src" / "eur_pc8b_read.py"), "--runs", *r_,
                               "--p8c", str(p8c or p8["P8c"]), "--pc8", str(pc8_dir or pc8),
                               "--control", str(ctrl["A"]), str(ctrl["B"]), "--ref", str(ref), "--pc1", str(pc1),
                               "--pc7", str(pc7), "--out", str(root / tag), *extra], capture_output=True, text=True)

    p = reader("read_b")
    print(p.stdout[-2500:], p.stderr[-2000:])
    assert p.returncode == 0 and "M-gates / M0 / M1 / M2 / M5 / M6 PASS" in p.stdout and "M7 PASS" in p.stdout \
        and "M4 PASS" in p.stdout, "reader failed"
    rd = root / "read_b"
    for f in ("per_subject.csv", "errors.csv", "k.csv", "seeds.csv", "machines.csv", "r1.csv", "r5.csv", "r6.csv",
              "r1_machine.csv", "events.csv", "gates.json", "T_PC8B.md"):
        assert (rd / f).exists() and (rd / f).stat().st_size > 50, f
    gj = json.loads((rd / "gates.json").read_text())
    assert len(gj["unseen"]["validation"]) == 3 and len(gj["unseen"]["test"]) == 8, gj["unseen"]
    M_ = pd.read_csv(rd / "per_subject.csv")
    c = pd.read_csv(p8["P8c"] / "per_subject.csv")
    assert RB.RD.canon(c[c.variant == "P8c"]).equals(RB.RD.canon(M_[M_.variant == "P8c"][list(c.columns)]))
    r1 = pd.read_csv(rd / "r1.csv")
    assert set(r1.arm) == {"10a", "P8c", "P8d", "P8e"} and set(r1.set) == set(RB.SETS), (set(r1.arm), set(r1.set))
    u = r1[(r1.set == "unseen")]
    assert (u.patients == 11).all() and set(u[u.reading == "primary"].arm) == {"P8d", "P8e"}
    assert (u.ci_lo <= u["diff"]).all() and (u["diff"] <= u.ci_hi).all()
    r5 = pd.read_csv(rd / "r5.csv")
    assert set(r5.arm) == {"R0", "P8d", "P8e"} and (r5[r5.set == "unseen"].p8c_seeds == 3).all()
    r1u = r1[(r1.set == "unseen") & (r1.arm == "P8c")].set_index("metric")["diff"]
    r5u = r5[(r5.set == "unseen") & (r5.arm == "R0")].set_index("metric")["diff"]
    assert np.allclose(r1u.sort_index().values, -r5u.sort_index().values, atol=1e-12)        # R0 - P8c = -(P8c - R0)
    r6 = pd.read_csv(rd / "r6.csv")
    assert set(r6.set) == {"unseen", "development"} and set(r6.arm) == {"P8d", "P8e"}
    print("R PASS: reader gates M-gates / M0 / M1 / M2 / M4 / M5 / M6 / M7, every table; P8c rows = the PC8 run's; "
          "unseen = 11 patients; R0 - P8c = -(P8c - R0)")

    # ---- negative paths
    neg = r'''
import os, sys
sys.path.insert(0, os.environ["R1_SRC"])
if __name__ == "__main__":
    import eur_abl as M
    R1 = M.R1
    R1.OUT_ROOT = R1.WORK / "eureka"; R1.STATE["tag"] = os.environ["EUR_TAG"]
    R1.out_dir().mkdir(parents=True, exist_ok=True)
    M.PC1_ARMS["P8e"] = (list(range(17, 30)), list(range(12)))
    try:
        M.pc8_columns(["P8e"])
    except SystemExit as e:
        assert "G-pc8cols FAIL" in str(e), str(e)[:300]
        print("NEG1 PASS: G-pc8cols FAIL")
    else:
        raise SystemExit("expected a STOP")
'''
    (root / "negb.py").write_text(neg)
    print(W.run(root / "negb.py", dict(base, R2_WORK=str(root / "work_negb"), R2_SCRATCH=str(root / "scratch_negb"),
                                      EUR_TAG="negb1"))[-200:])

    def fails(tag, want, **kw):
        q = reader(tag, **kw)
        assert q.returncode != 0 and want in (q.stdout + q.stderr), (tag, q.stdout[-500:] + q.stderr[-500:])
        print(f"{tag} PASS: {want}")

    b2 = root / "negb2_pc8"
    shutil.copytree(pc8, b2)
    x = pd.read_csv(b2 / "per_subject.csv"); i = x.index[x.variant == "P8c"][0]; x.loc[i, "fp"] += 1
    x.to_csv(b2 / "per_subject.csv", index=False)
    fails("NEGB2", "STOP M6", pc8_dir=b2)
    b3 = root / "negb3_pc8"
    shutil.copytree(pc8, b3)
    x = pd.read_csv(b3 / "r1.csv")
    x.loc[(x.arm == "P8c") & (x.set == "test") & (x.metric == "sens"), "diff"] += 1e-6
    x.to_csv(b3 / "r1.csv", index=False)
    fails("NEGB3", "STOP M7", pc8_dir=b3)
    b4 = root / "negb4_split.py"
    b4.write_text((ROOT / "src" / "retrain" / "train_gae_v2.py").read_text().replace('VAL = ["chb10", "chb11", "chb22"]',
                                                                                     'VAL = ["chb10", "chb11"]', 1))
    assert 'VAL = ["chb10", "chb11"]' in b4.read_text()
    fails("NEGB4", "STOP M5", extra=("--split-src", str(b4)))
    m = repo / "src" / "eur_abl.py"
    keep = m.read_text()
    m.write_text(keep + "\n# edited\n")
    W.run(root / "runner.py", nb_env("negb5", EUR_TEST_ARM_SEEDS=ARM_SEEDS), [nbdir / "EUR_PC8_d.ipynb"],
          expect_fail="modules differ")
    m.write_text(keep)
    print("NEGB5 PASS: an edited module stops EUR_PC8_d before it starts")
    fails("NEGB6", "must be the PC8 run of arm P8c", p8c=p8["P8a"])
    b7 = root / "negb7_run"
    shutil.copytree(outs["P8e"], b7)
    x = pd.read_csv(b7 / "per_subject.csv"); i = x.index[x.variant == "R0"][0]; x.loc[i, "fp"] += 1
    x.to_csv(b7 / "per_subject.csv", index=False)
    fails("NEGB7", "STOP M1", runs=[str(outs["P8d"]), str(b7)])
    fails("NEGB8", "same run twice", runs=[str(outs["P8d"]), str(outs["P8d"])])
    print(f"ALL PASS in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
