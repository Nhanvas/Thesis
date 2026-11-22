#!/usr/bin/env python
"""eur_pc8_synthetic_test.py -- end-to-end test of PC8 (EUR_PC8_a / _b / _c and src/eur_pc8_read.py) on SYNTHETIC data
(build container only; never on Kaggle). Chat D37-F, design results/eureka_d37f/DESIGN_PC8.md.

World: src/r2_r1_synthetic_test.build_world and its RECORD_GEN (as the other EUR tests). Training: 2 epochs
(EUR_PC1_EPOCHS, read only in test mode); 2 workers.
Runs: P0 the reference EUR_PC1_R0 (copied to repo/results/eureka_d32f/pc1_r0); C the control EUR_PC7_A / _B (test seeds
A = 42,1,2,3 reused + 4,5; B = 42,1,2,3 reused + 6,7) and the PC7 reader on them (its q5.csv for gate M4); P1 the three
PC8 notebooks (built by src/eur_make_notebooks.py --only EUR_PC8, run cell by cell) with test seeds 42,1,2 per arm (two
chunks) and R0 = seed 42 reused (the notebook's own EUR_ARM_SEEDS_R0 / EUR_ARM_REUSE_R0).
Checks:
  P1  every gate PASS incl. G-pc8cols, G-pc7reuse, G-pc7plat, G-pc7rep (exact in one container), G-guard (2 chunks),
      G-pc7k, G-pc7r0; V0 x 4 seeds, R0 x seed 42 only, the arm x 42 / 1 / 2 on every case; arm json in_dim / out_x
      = 25 / 7, 28 / 10, 7 / 7; run_meta holds cpu_model and arm_seeds_by_arm
  N1  (non-circular) (a) P8a seed 1 re-trained in the main process with columns chosen BY NAME from the test's own list =
      the pool worker's checkpoint exactly; (b) the P8c scalar of chb03 recomputed from model_cmp_core.node_input (the
      TRAINING construction), columns 23-29 cut by numpy, a per-window forward, Ledoit-Wolf per channel = the stored
      scalar; (c) the number of parameters of each arm = the formula of the GCN encoder and the decoder
  U   two_level on a known world (arm = R0 + delta per patient, identical seeds -> every draw = delta); wording rule
  R   src/eur_pc8_read.py on the three runs, the control, the reference, a PC1-like folder and the PC7 reading: every
      gate, every table; the control = PC7's primary seeds (pooled here: one container, G-pc7rep PASS); the merged
      control rows = the control runs' R0 rows exactly
Negative paths: NEG1 G-pc8cols FAILs when an arm's columns differ from the design (direct call) and when seed 42 is not
among the arm seeds; NEG2 a PC8 run's R0 seed-42 row changed -> the reader STOPs (M1); NEG3 a control run's V0 row
changed -> STOP (M0); NEG4 PC7's q5 changed -> STOP (M4); NEG5 an edited pinned module -> the notebook refuses to start;
NEG6 two runs of the same arm -> STOP.
  python src/eur_pc8_synthetic_test.py [--root DIR]
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
import eur_pc8_read as RD8              # noqa: E402

REF_REL = "results/eureka_d32f/pc1_r0"
CTRL_SEEDS = {"A": "42,1,2,3,4,5", "B": "42,1,2,3,6,7"}
ARM_SEEDS = "42,1,2"
DIMS = {"P8a": (25, 7), "P8b": (28, 10), "P8c": (7, 7)}
NAMES = ([f"adj{c}" for c in range(18)] + [f"rel_{b}" for b in ("delta", "theta", "alpha", "beta", "gamma")] +
         [f"logbp_{b}" for b in ("delta", "theta", "alpha", "beta", "gamma")] + ["log_linelen", "slog_kurtosis"])


def unit_checks():
    rng = np.random.default_rng(3)
    subj = ["chb01", "chb21", "chb02", "chb03", "chb05"]
    base = rng.normal(0.8, 0.1, (5, 1)) + np.zeros((5, 6))
    groups = {"R0": base, "A": base[:, :3] - 0.2, "B": base[:, :4] + 0.05}
    point, bs = RD8.two_level(groups, "R0", rng, 200, subj)
    assert abs(point["A"] + 0.2) < 1e-12 and abs(point["B"] - 0.05) < 1e-12, point
    assert np.allclose(bs["A"], -0.2) and np.allclose(bs["B"], 0.05)
    assert RD8.wording("sens", -0.3, -0.1) == "loses" and RD8.wording("sens", -0.1, 0.1) == "no measurable difference"
    assert RD8.wording("fa", 0.5, 2.0) == "more false alarms" and RD8.wording("f1", 0.01, 0.02) == "gains"
    print("U PASS: two-level bootstrap on a known world; wording rule")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/tmp/eur_pc8_synth")
    a = ap.parse_args()
    t0 = time.time()
    unit_checks()
    root = Path(a.root)
    repo, inp = W.build_world(root)
    for name, body in (("record_gen.py", W.RECORD_GEN), ("runner.py", W.RUNNER)):
        (root / name).write_text(body)
    base = dict(R2_TEST="1", THESIS_REPO=str(repo), R2_INPUT=str(inp), R1_SRC=str(repo / "src"), OMP_NUM_THREADS="1",
                OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONHASHSEED="0", EUR_PC1_EPOCHS="2")
    print(W.run(root / "record_gen.py", dict(base, R2_WORK=str(root / "gen_work"), R2_SCRATCH=str(root / "gen_scratch")))[-300:])
    nbdir = root / "notebooks"
    for only in ("EUR_PC1", "EUR_PC7", "EUR_PC8"):
        subprocess.check_call([sys.executable, str(ROOT / "src" / "eur_make_notebooks.py"), "--only", only],
                              env=dict(os.environ, EUR_NB_OUTDIR=str(nbdir)))

    def nb_env(tag, **kw):
        return dict(EUR_TEST_REPO=str(repo), EUR_TEST_INPUT=str(inp), EUR_TEST_WORK=str(root / f"work_{tag}"),
                    EUR_TEST_SCRATCH=str(root / f"scratch_{tag}"), EUR_WORKERS="2", PYTHONHASHSEED="0",
                    EUR_PC1_EPOCHS="2", **kw)

    # ---- P0: the reference run (PC1's R0, synthetic)
    t = time.time()
    print(W.run(root / "runner.py", nb_env("ref"), [nbdir / "EUR_PC1_R0.ipynb"])[-400:])
    ref = repo / REF_REL
    ref.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(root / "work_ref" / "eureka" / "pc1_R0", ref)
    print(f"P0 PASS: reference EUR_PC1_R0 ({time.time() - t:.0f} s) copied to {REF_REL}")

    # ---- C: the control (PC7-like) and its reading
    ctrl = {}
    for part in ("A", "B"):
        t = time.time()
        print(W.run(root / "runner.py", nb_env(f"c{part}", EUR_TEST_ARM_SEEDS=CTRL_SEEDS[part]),
                    [nbdir / f"EUR_PC7_{part}.ipynb"])[-400:])
        ctrl[part] = root / f"work_c{part}" / "eureka" / f"pc7_{part}"
        print(f"C {part} control notebook {time.time() - t:.0f} s")
    pc1 = root / "pc1_like"
    pc1.mkdir(exist_ok=True)
    rr = pd.read_csv(ref / "per_subject.csv")
    pd.concat([rr[rr.variant == "V0"], rr[rr.variant == "R0"].assign(variant="10a"),
               rr[rr.variant == "R0"].assign(variant="10b")]).to_csv(pc1 / "per_subject.csv", index=False)
    pc7 = root / "pc7_read"
    p = subprocess.run([sys.executable, str(ROOT / "src" / "eur_pc7_read.py"), "--runs", str(ctrl["A"]), str(ctrl["B"]),
                        "--ref", str(ref), "--pc1", str(pc1), "--out", str(pc7)], capture_output=True, text=True)
    assert p.returncode == 0, p.stdout[-1500:] + p.stderr[-1500:]
    print("C PASS: control runs and the PC7 reading (q5.csv)")

    # ---- P1: the three PC8 notebooks
    outs = {}
    seeds = [f"clean_seed{s}" for s in ARM_SEEDS.split(",")]
    for arm in ("P8a", "P8b", "P8c"):
        part = arm[-1]
        nb = nbdir / f"EUR_PC8_{part}.ipynb"
        srcs = "".join("".join(c["source"]) for c in json.loads(nb.read_text())["cells"])
        assert (f'EUR_VARIANTS="V0,R0,{arm}"' in srcs and f'EUR_TAG="pc8_{part}"' in srcs and 'EUR_ARM_SEEDS_R0="42"' in srcs
                and 'EUR_ARM_REUSE_R0="42"' in srcs and 'EUR_ARM_SEEDS="42,1,2,3,4,5,6,7"' in srcs), arm
        t = time.time()
        print(W.run(root / "runner.py", nb_env(part, EUR_TEST_ARM_SEEDS=ARM_SEEDS), [nb])[-1200:])
        print(f"P1 {arm} notebook {time.time() - t:.0f} s")
        out = root / f"work_{part}" / "eureka" / f"pc8_{part}"
        g = {x["gate"]: x for x in json.loads((out / "gates.json").read_text())}
        want = RD8.REQUIRED
        assert all(g.get(w, {}).get("status") == "PASS" for w in want), {w: g.get(w, {}).get("status") for w in want}
        assert len(g["G-guard"]["chunks"]) == 2 and not g["G-guard"]["skipped"], g["G-guard"]
        assert g["G-pc7reuse"]["reused"] == ["R0/clean_seed42"], g["G-pc7reuse"]
        R = pd.read_csv(out / "per_subject.csv")
        for v, ss in (("V0", RD8.TAGS4), ("R0", ["clean_seed42"]), (arm, seeds)):
            d = R[R.variant == v]
            per = d.groupby(["subject", "seed"]).size()
            assert set(d.seed) == set(ss) and per.min() == per.max() == 6 and d.subject.nunique() == 26, (v, set(d.seed))
        js = json.loads((out / "models" / arm / "gae_v2_clean_seed1.json").read_text())
        assert (js["in_dim"], js["out_x"]) == DIMS[arm], (arm, js["in_dim"], js["out_x"])
        meta = json.loads((out / "run_meta.json").read_text())
        assert meta.get("cpu_model") and meta["arm_seeds_by_arm"][arm] == seeds and meta["arm_seeds_by_arm"]["R0"] == ["clean_seed42"]
        assert not (out / "models" / "R0" / "gae_v2_clean_seed1.pt").exists(), "R0 must not be trained in PC8"
        outs[arm] = out
    print("P1 PASS: three notebooks, every gate incl. G-pc8cols / G-pc7reuse / G-pc7rep / G-guard / G-pc7k / G-pc7r0; "
          "V0 x 4, R0 x seed 42, arm x 3 seeds, 26 cases; arm dimensions; CPU model recorded")

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
    # (a) P8a seed 1, columns by name
    drop = {"logbp_delta", "logbp_theta", "logbp_alpha", "logbp_beta", "logbp_gamma"}
    ki = [i for i, n in enumerate(NAMES) if n not in drop]
    ko = [i for i, n in enumerate(NAMES[18:]) if n not in drop]
    mine, info, _ = M.train_masked(M.TRAIN, meta, 1, ki, ko, 2, tag=" N1a")
    sd = torch.load(Path(os.environ["N1_A"]) / "models" / "P8a" / "gae_v2_clean_seed1.pt")
    d = max(float((mine.state_dict()[k] - sd[k]).abs().max()) for k in sd)
    assert d == 0.0, d
    # (c) parameters = 64 * in + 64 + 64 * 16 + 16 + 16 * 32 + 32 + 32 * out + out
    for arm, (i_, o_) in {"P8a": (25, 7), "P8b": (28, 10), "P8c": (7, 7)}.items():
        n = sum(q.numel() for q in G.GAEModel(in_dim=i_, bands=o_).parameters())
        assert n == 64 * i_ + 64 + 64 * 16 + 16 + 16 * 32 + 32 + 32 * o_ + o_, (arm, n)
    # (b) P8c scalar of chb03 from the training construction
    outc = Path(os.environ["N1_C"])
    M.PD.CKPT = R1.REPO / "data" / "models_v2"
    z, _ = R1.load_case("chb03", "earlier")
    idx, _, _, _ = M.model_inputs(z)
    ok = ~z["is_signal_loss"].astype(bool); fidx = z["file_idx"].astype(int)
    lite = dict(n=int(len(ok)), idx=idx, ok=ok, fidx=fidx); wf = fidx[idx]
    X30, adj, _, _ = C.node_input(z, idx, meta)
    adj = np.asarray(z["adj"][idx], np.float32)
    xm = np.load(Path(os.environ["N1_SCR_C"]) / "eur" / "xm" / "chb03.npz")
    worst = 0.0
    for tag in ("clean_seed42", "clean_seed1", "clean_seed2"):
        mm = G.GAEModel(in_dim=7, bands=7); mm.load_state_dict(torch.load(outc / "models" / "P8c" / f"gae_v2_{tag}.pt")); mm.eval()
        Z = np.empty((len(idx), 18, 16), np.float32)
        with torch.no_grad():
            for i in range(len(idx)):
                A = torch.tensor(adj[i] if np.isfinite(adj[i]).all() else np.zeros_like(adj[i]))
                ei, ew = dense_to_sparse(A)
                Z[i] = mm.encoder(torch.tensor(np.ascontiguousarray(X30[i][:, 23:30])), ei, ew).numpy()
        D = np.column_stack([LedoitWolf().fit(Z[:, c].astype(np.float64)).mahalanobis(Z[:, c].astype(np.float64))
                             for c in range(18)])
        D = np.asarray(np.asarray(D, np.float32), np.float64)
        x, m = M.scalar_and_m(lite, M.member_series(D, wf, M.MEMBERS, "level"), [])
        worst = max(worst, float(np.nanmax(np.abs(x - xm[f"P8c|{tag}|x"]))))
    assert worst <= 1e-6, worst
    print(f"N1 PASS: P8a seed 1 reproduced exactly (columns by name); P8c scalar recomputed (max |dx| {worst:.1e}); parameters")
'''
    (root / "n1.py").write_text(code)
    print(W.run(root / "n1.py", dict(base, R2_WORK=str(root / "work_n1"), R2_SCRATCH=str(root / "scratch_n1"),
                                    EUR_TAG="pc8_n1", N1_NAMES=json.dumps(NAMES), N1_A=str(outs["P8a"]),
                                    N1_C=str(outs["P8c"]), N1_SCR_C=str(root / "scratch_c")))[-300:])

    # ---- R: the reader
    rd = root / "read"
    cmd = [sys.executable, str(ROOT / "src" / "eur_pc8_read.py"), "--runs", *[str(outs[x]) for x in ("P8a", "P8b", "P8c")],
           "--control", str(ctrl["A"]), str(ctrl["B"]), "--ref", str(ref), "--pc1", str(pc1), "--pc7", str(pc7)]
    p = subprocess.run(cmd + ["--out", str(rd)], capture_output=True, text=True)
    print(p.stdout[-2500:], p.stderr[-2000:])
    assert p.returncode == 0 and "M-gates / M0 / M1 / M2 PASS" in p.stdout and "M4 PASS" in p.stdout, "reader failed"
    for f in ("per_subject.csv", "errors.csv", "k.csv", "seeds.csv", "r1.csv", "r1_machine.csv", "r2.csv", "events.csv",
              "machines.csv",
              "gates.json", "T_PC8.md"):
        assert (rd / f).exists() and (rd / f).stat().st_size > 50, f
    gj = json.loads((rd / "gates.json").read_text())
    prim = json.loads((pc7 / "gates.json").read_text())["primary_seeds"]
    assert sorted(gj["r0_control"]) == sorted(prim) and len(prim) == 8, (gj["r0_control"], prim)   # pooled in one container
    M_ = pd.read_csv(rd / "per_subject.csv")
    for part, ss in (("A", ["clean_seed42", "clean_seed1", "clean_seed2", "clean_seed3", "clean_seed4", "clean_seed5"]),
                     ("B", ["clean_seed6", "clean_seed7"])):
        c = pd.read_csv(ctrl[part] / "per_subject.csv")
        a_ = RD8.RD.canon(c[(c.variant == "R0") & c.seed.isin(ss)])
        b_ = RD8.RD.canon(M_[(M_.variant == "R0") & M_.seed.isin(ss)][list(c.columns)])
        assert a_.equals(b_), part
    r1 = pd.read_csv(rd / "r1.csv")
    assert set(r1.arm) == {"10a", "P8a", "P8b", "P8c"} and set(r1.set) == {"development", "test", "chb24", "siena"}
    assert (r1[r1.set == "development"].ci_lo <= r1[r1.set == "development"]["diff"]).all()
    # R1m: in one container every run has G-pc7rep PASS -> the matched control = the control runs' trained seeds
    r1m = pd.read_csv(rd / "r1_machine.csv")
    mm = gj["machine_matched"]
    assert all(v["arm_rep"] == "PASS" and sorted(v["control_seeds"]) == sorted(f"clean_seed{s}" for s in (4, 5, 6, 7))
               for v in mm.values()), mm
    assert set(r1m.arm) == {"P8a", "P8b", "P8c"} and (r1m.r0_seeds == 4).all() and (r1m.reading == "secondary").all()
    print("R PASS: reader gates M0 / M1 / M2 / M4, every table (incl. R1m machine-matched); merged control rows = the "
          "control runs' rows")

    # ---- negative paths
    neg = r'''
import os, sys
sys.path.insert(0, os.environ["R1_SRC"])
if __name__ == "__main__":
    import eur_abl as M
    R1 = M.R1
    R1.OUT_ROOT = R1.WORK / "eureka"; R1.STATE["tag"] = os.environ["EUR_TAG"]
    R1.out_dir().mkdir(parents=True, exist_ok=True)
    mode = os.environ["NEG"]
    if mode == "cols":
        M.PC1_ARMS["P8b"] = ([i for i in range(30) if i != 29], [i for i in range(12) if i != 11])
    try:
        M.pc8_columns(["P8b"])
    except SystemExit as e:
        assert "G-pc8cols FAIL" in str(e), str(e)[:300]
        print(f"NEG1 {mode} PASS: G-pc8cols FAIL")
    else:
        raise SystemExit("expected a STOP")
'''
    (root / "neg.py").write_text(neg)
    common = dict(base, R2_WORK=str(root / "work_neg"), R2_SCRATCH=str(root / "scratch_neg"))
    print(W.run(root / "neg.py", dict(common, NEG="cols", EUR_TAG="neg1a"))[-200:])
    print(W.run(root / "neg.py", dict(common, NEG="seed", EUR_TAG="neg1b", EUR_ARM_SEEDS_P8b="1,2,3"))[-200:])

    def reader_fails(tag, want, runs=None, control=None, pc7_dir=None):
        r_ = runs or [str(outs[x]) for x in ("P8a", "P8b", "P8c")]
        c_ = control or [str(ctrl["A"]), str(ctrl["B"])]
        q = subprocess.run([sys.executable, str(ROOT / "src" / "eur_pc8_read.py"), "--runs", *r_, "--control", *c_,
                            "--ref", str(ref), "--pc1", str(pc1), "--pc7", str(pc7_dir or pc7), "--out", str(root / tag)],
                           capture_output=True, text=True)
        assert q.returncode != 0 and want in (q.stdout + q.stderr), (tag, q.stdout[-500:] + q.stderr[-500:])
        print(f"{tag} PASS: {want}")

    bad = root / "neg2_run"
    shutil.copytree(outs["P8b"], bad)
    x = pd.read_csv(bad / "per_subject.csv"); i = x.index[(x.variant == "R0")][0]; x.loc[i, "fp"] += 1
    x.to_csv(bad / "per_subject.csv", index=False)
    reader_fails("NEG2", "STOP M1", runs=[str(outs["P8a"]), str(bad), str(outs["P8c"])])
    badc = root / "neg3_ctrl"
    shutil.copytree(ctrl["B"], badc)
    x = pd.read_csv(badc / "per_subject.csv"); i = x.index[(x.variant == "V0")][0]; x.loc[i, "tp"] += 1
    x.to_csv(badc / "per_subject.csv", index=False)
    reader_fails("NEG3", "STOP M0", control=[str(ctrl["A"]), str(badc)])
    badq = root / "neg4_pc7"
    shutil.copytree(pc7, badq)
    x = pd.read_csv(badq / "q5.csv")
    x.loc[(x.comparison == "10a - R0") & (x.set == "development") & (x.metric == "sens"), "diff"] += 1e-6
    x.to_csv(badq / "q5.csv", index=False)
    reader_fails("NEG4", "STOP M4", pc7_dir=badq)
    reader_fails("NEG6", "one run per arm", runs=[str(outs["P8a"]), str(outs["P8a"]), str(outs["P8c"])])
    m = repo / "src" / "eur_abl.py"
    keep = m.read_text()
    m.write_text(keep + "\n# edited\n")
    W.run(root / "runner.py", nb_env("neg5", EUR_TEST_ARM_SEEDS=ARM_SEEDS), [nbdir / "EUR_PC8_a.ipynb"],
          expect_fail="modules differ")
    m.write_text(keep)
    print("NEG5 PASS: an edited module stops the notebook before it starts")
    print(f"ALL PASS in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
