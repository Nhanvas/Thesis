#!/usr/bin/env python
"""eur_pc7_synthetic_test.py -- end-to-end test of PC7 (EUR_PC7_A / _B and src/eur_pc7_read.py) on SYNTHETIC data
(build container only; never on Kaggle). Chat D34-F, design results/eureka_d34f/DESIGN_PC7.md.

World: src/r2_r1_synthetic_test.build_world and its RECORD_GEN (as the other EUR tests). Training: 2 epochs
(EUR_PC1_EPOCHS, read only in test mode). Seeds (test mode only, EUR_TEST_ARM_SEEDS): A = 42,1,2,3 reused + 4,5,6
(2 workers -> two chunks), B = 42,1,2,3 reused + 7,8.
Checks:
  P0  the reference run: EUR_PC1_R0 (2 epochs) run here and copied to repo/results/eureka_d32f/pc1_r0
  P1  EUR_PC7_A and EUR_PC7_B (built by src/eur_make_notebooks.py --only EUR_PC7, run cell by cell, 2 workers): every gate
      PASS incl. G-pc7reuse, G-pc7plat, G-pc7rep (exact in one container), G-guard, G-pc7k, G-pc7r0; V0 x 4 seeds, R0 / R0s x
      7 (A) / 6 (B) seeds on every case; k.csv with one R0s k per seed
  N1  (non-circular) (a) the new seed-5 checkpoint = f1_core.train('gae', training cases, seed 5, 2 epochs) exactly;
      (b) R0s rows of seed 42 = R0 rows of seed 42 except k / q (k per seed of seed 42 = the k of seed 42); (c) node_x
      with an arm checkpoint json = node_x with the V5 json, exactly; (d) the per-seed k of R0s for seed 6 recomputed
      here with p3_levers.calibrate from the stored development scalars = k.csv
  U   reader statistics on known worlds: ANOVA components recover simulated SDs; the selection gain = a brute-force loop;
      the unit bootstrap mean with every unit once = the plain mean; chi-square SD interval contains the true SD
  R   src/eur_pc7_read.py on the two runs, the reference and a PC1-like folder: every gate, pooled N = 9, every table
Negative paths: NEG1 a reference log with a changed epoch-1 loss -> G-pc7rep DIFF and the run is not stopped; NEG2 a
changed reference R0 row -> G-pc7r0 STOP; NEG3 a changed reference k -> G-pc7k STOP; NEG4 the guard with a tiny limit ->
only the first chunk trains, the rest is listed in G-guard; NEG5 run B's reused R0 row changed -> the reader STOPs (M1);
NEG6 an edited pinned module -> the notebook refuses to start.
  python src/eur_pc7_synthetic_test.py [--root DIR]
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
import eur_pc7_read as RD               # noqa: E402

REF_REL = "results/eureka_d32f/pc1_r0"
SEEDS = {"A": "42,1,2,3,4,5,6", "B": "42,1,2,3,7,8"}


def unit_checks():
    rng = np.random.default_rng(1)
    P, S = 15, 400
    Y = 0.8 + rng.normal(0, 0.10, (P, 1)) + rng.normal(0, 0.04, (1, S)) + rng.normal(0, 0.06, (P, S))
    c = RD.anova2(Y)
    assert abs(c["sd_seed"] - 0.04) < 0.006 and abs(c["sd_res"] - 0.06) < 0.004, c
    val, y = rng.normal(size=9), rng.normal(size=9)
    import itertools
    combos = np.array(list(itertools.combinations(range(9), 4)))
    g, share = RD.selection_gain(val, y, combos)
    gl, sl = [], []
    for cmb in itertools.combinations(range(9), 4):
        cmb = list(cmb)
        j = cmb[int(np.argmin(val[cmb]))]
        gl.append(y[j] - y[cmb].mean()); sl.append(y[j] >= np.median(y[cmb]))
    assert abs(g - np.mean(gl)) < 1e-12 and abs(share - np.mean(sl)) < 1e-12
    subj = ["chb01", "chb21", "chb02", "chb03"]
    uix, _, U = RD.unit_draw(subj, rng, 1)
    d = np.array([1.0, 3.0, 5.0, 7.0])
    assert abs(RD.unit_mean(d, uix, np.arange(U)[None, :], U)[0] - d.mean()) < 1e-12
    x = rng.normal(0, 0.05, 20)
    s, lo, hi = RD.sd_ci(x)
    assert lo < 0.05 < hi and lo < s < hi
    print("U PASS: ANOVA components, selection gain (brute force), unit bootstrap mean, chi-square SD interval")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/tmp/eur_pc7_synth")
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
    for only in ("EUR_PC1", "EUR_PC7"):
        subprocess.check_call([sys.executable, str(ROOT / "src" / "eur_make_notebooks.py"), "--only", only],
                              env=dict(os.environ, EUR_NB_OUTDIR=str(nbdir)))

    def nb_env(tag, **kw):
        return dict(EUR_TEST_REPO=str(repo), EUR_TEST_INPUT=str(inp), EUR_TEST_WORK=str(root / f"work_{tag}"),
                    EUR_TEST_SCRATCH=str(root / f"scratch_{tag}"), EUR_WORKERS="2", PYTHONHASHSEED="0",
                    EUR_PC1_EPOCHS="2", **kw)

    # ---- P0: the reference run (PC1's R0, synthetic)
    t = time.time()
    print(W.run(root / "runner.py", nb_env("ref"), [nbdir / "EUR_PC1_R0.ipynb"])[-600:])
    ref = repo / REF_REL
    ref.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(root / "work_ref" / "eureka" / "pc1_R0", ref)
    print(f"P0 PASS: reference EUR_PC1_R0 ({time.time() - t:.0f} s) copied to {REF_REL}")

    # ---- P1
    outs = {}
    for part in ("A", "B"):
        nb = nbdir / f"EUR_PC7_{part}.ipynb"
        srcs = "".join("".join(c["source"]) for c in json.loads(nb.read_text())["cells"])
        assert 'EUR_VARIANTS="V0,R0,R0s"' in srcs and f'EUR_TAG="pc7_{part}"' in srcs and "EUR_PC7_REF" in srcs, part
        t = time.time()
        print(W.run(root / "runner.py", nb_env(part, EUR_TEST_ARM_SEEDS=SEEDS[part]), [nb])[-1500:])
        print(f"P1 {part} notebook {time.time() - t:.0f} s")
        out = root / f"work_{part}" / "eureka" / f"pc7_{part}"
        g = {x["gate"]: x for x in json.loads((out / "gates.json").read_text())}
        want = ["G-self", "G-data", "G-pc1const", "G-pc1vec", "G-pc7reuse", "G-pc7plat", "G-pc7rep", "G-guard", "SMOKE",
                "R1.0-dev", "R1.0-test", "GE", "G-k", "G-kv0", "G-D0[full]", "G-x0[full]", "G-eng[full]",
                "G-worker[full]", "G-pc7k", "G-pc7r0"]
        assert all(g.get(w, {}).get("status") == "PASS" for w in want), {w: g.get(w, {}).get("status") for w in want}
        seeds = [f"clean_seed{s}" for s in SEEDS[part].split(",")]
        assert len(g["G-guard"]["chunks"]) == (2 if part == "A" else 1) and not g["G-guard"]["skipped"], g["G-guard"]
        R = pd.read_csv(out / "per_subject.csv")
        for v, ss in (("V0", RD.TAGS4), ("R0", seeds), ("R0s", seeds)):
            d = R[R.variant == v]
            per = d.groupby(["subject", "seed"]).size()
            assert set(d.seed) == set(ss) and per.min() == per.max() == 6 and d.subject.nunique() == 26, (v, set(d.seed))
        k = pd.read_csv(out / "k.csv")
        assert set(k[k.variant == "R0s"].seed) == set(seeds), k
        outs[part] = out
    print("P1 PASS: both notebooks, every gate incl. G-pc7reuse / G-pc7plat / G-pc7rep / G-guard / G-pc7k / G-pc7r0; "
          "V0 x 4, R0 / R0s x every seed, 26 cases")

    # ---- N1
    code = r'''
import os, sys, json, numpy as np, pandas as pd
sys.path.insert(0, os.environ["R1_SRC"])
if __name__ == "__main__":
    import torch
    import eur_abl as M
    import f1_core as F
    from pathlib import Path
    R1 = M.R1
    M.build_views(M.DEV, M.TEST, [])
    meta, _, _ = M._pc1_meta()
    R1.point_npz(M.TRAIN + M.VAL, "earlier")
    out = Path(os.environ["N1_OUT"])
    ref, _, _ = F.train("gae", M.TRAIN, meta, 5, torch.device("cpu"), epochs=2, tag=" N1a")
    sd = torch.load(out / "models" / "R0" / "gae_v2_clean_seed5.pt")
    d = max(float((ref.state_dict()[k] - sd[k]).abs().max()) for k in sd)
    assert d == 0.0, d
    R = pd.read_csv(out / "per_subject.csv")
    cols = [c for c in R.columns if c not in ("variant", "k", "q_raw")]
    a = R[(R.variant == "R0") & (R.seed == "clean_seed42")][cols].sort_values(cols).reset_index(drop=True)
    b = R[(R.variant == "R0s") & (R.seed == "clean_seed42")][cols].sort_values(cols).reset_index(drop=True)
    assert len(a) and a.equals(b), "R0s seed 42 differs from R0 seed 42"
    M.PD.CKPT = R1.REPO / "data" / "models_v2"
    z, _ = R1.load_case("chb03", "earlier")
    idx, adj, xn, f7 = M.model_inputs(z)
    js = json.loads((out / "models" / "R0" / "gae_v2_clean_seed5.json").read_text())
    assert np.array_equal(M.node_x("clean_seed42", adj, xn, f7, js), M.node_x("clean_seed42", adj, xn, f7))
    # (d) R0s k of seed 6 from the stored development budget signals (scratch xm), smoothed by the record function
    xm_dir = Path(os.environ["N1_SCR"]) / "eur" / "xm"
    sms = []
    for c in M.DEV:
        ctx, _ = R1.ctx_from_store(c, "earlier", "r10")
        sms.append(M.PS.smoothed(ctx, np.load(xm_dir / f"{c}.npz")["R0s|clean_seed6|m"], 5))
    k6 = float(M.P3L.calibrate(sms))
    kc = pd.read_csv(out / "k.csv")
    kk = float(kc[(kc.variant == "R0s") & (kc.seed == "clean_seed6")].k.iloc[0])
    assert k6 == kk, (k6, kk)
    print("N1 PASS: seed 5 = f1_core.train exactly; R0s seed 42 = R0 seed 42; node_x arm json = V5 json; R0s k seed 6 recomputed")
'''
    (root / "n1.py").write_text(code)
    print(W.run(root / "n1.py", dict(base, R2_WORK=str(root / "work_A"), R2_SCRATCH=str(root / "scratch_A"),
                                    EUR_TAG="pc7_A", N1_OUT=str(outs["A"]), N1_SCR=str(root / "scratch_A")))[-300:])

    # ---- R: the reader (PC1-like folder: the reference R0 rows renamed 10a / 10b)
    pc1 = root / "pc1_like"
    pc1.mkdir(exist_ok=True)
    rr = pd.read_csv(ref / "per_subject.csv")
    pd.concat([rr[rr.variant == "V0"], rr[rr.variant == "R0"].assign(variant="10a"),
               rr[rr.variant == "R0"].assign(variant="10b")]).to_csv(pc1 / "per_subject.csv", index=False)
    rd = root / "read"
    p = subprocess.run([sys.executable, str(ROOT / "src" / "eur_pc7_read.py"), "--runs", str(outs["A"]), str(outs["B"]),
                        "--ref", str(ref), "--pc1", str(pc1), "--out", str(rd)], capture_output=True, text=True)
    print(p.stdout[-3000:], p.stderr[-2000:])
    assert p.returncode == 0 and "M-gates / M0 / M1 / M2 PASS" in p.stdout, "reader failed"
    gj = json.loads((rd / "gates.json").read_text())
    assert gj["pooled"] and len(gj["primary_seeds"]) == 9, gj
    for f in ("seeds.csv", "q1_summary.csv", "q1_components.csv", "q2.csv", "q3.csv", "q4.csv", "q5.csv", "q6.csv", "T_PC7.md"):
        assert (rd / f).exists() and (rd / f).stat().st_size > 50, f
    q5 = pd.read_csv(rd / "q5.csv")
    Rm = pd.read_csv(rd / "per_subject.csv")
    assert len(Rm[(Rm.variant == "R0")].seed.unique()) == 9 and len(q5) > 0
    print("R PASS: reader gates, pooled N = 9, every table")

    # ---- negative paths (direct calls in a fresh interpreter)
    neg = r'''
import os, sys, json, shutil, numpy as np, pandas as pd
sys.path.insert(0, os.environ["R1_SRC"])
if __name__ == "__main__":
    import eur_abl as M
    from pathlib import Path
    R1 = M.R1
    mode = os.environ["NEG"]
    M.build_views(M.DEV, M.TEST, [])
    R1.point_npz(M.TRAIN + M.VAL, "earlier")
    R1.OUT_ROOT = R1.WORK / "eureka"; R1.STATE["tag"] = os.environ["EUR_TAG"]
    R1.out_dir().mkdir(parents=True, exist_ok=True)
    meta, _, _ = M._pc1_meta()
    if mode == "rep":
        shutil.copyfile(Path(os.environ["SRC_META"]), R1.out_dir() / "run_meta.json")
        M.pc7_platform_checks(meta)
        g = {x["gate"]: x for x in R1.STATE["gates"]}
        assert g["G-pc7rep"]["status"] == "DIFF" and g["G-pc7plat"]["status"] == "PASS", g
        print("NEG1 PASS: G-pc7rep DIFF recorded, no stop")
    elif mode in ("r0", "k"):
        for f in ("per_subject.csv", "errors.csv", "k.csv"):
            shutil.copyfile(Path(os.environ["SRC_RUN"]) / f, R1.out_dir() / f)
        kk = pd.read_csv(R1.out_dir() / "k.csv")
        ks = {"R0": float(kk[kk.variant == "R0"].k.iloc[0])}
        try:
            M.pc7_final_gates(ks)
        except SystemExit as e:
            want = "G-pc7r0 FAIL" if mode == "r0" else "G-pc7k FAIL"
            assert want in str(e), str(e)[:300]
            print(f"NEG {mode} PASS: {want}")
        else:
            raise SystemExit("expected a STOP")
    elif mode == "guard":
        res = M.train_chunks([("R0", "clean_seed30", 2), ("R0", "clean_seed31", 2), ("R0", "clean_seed32", 2)], 1)
        g = [x for x in R1.STATE["gates"] if x["gate"] == "G-guard"][-1]
        assert len(res) == 1 and g["skipped"] == ["R0/clean_seed31", "R0/clean_seed32"], g
        print("NEG4 PASS: guard trained one chunk, skipped the rest")
'''
    (root / "neg.py").write_text(neg)

    def neg_ref(name, edit):
        d = repo / "results" / "neg" / name
        shutil.rmtree(d, ignore_errors=True)
        shutil.copytree(ref, d)
        edit(d)
        return f"results/neg/{name}"

    def ed_log(d):
        f = d / "models" / "R0" / "training_log_clean_seed42.csv"
        x = pd.read_csv(f); x.loc[x.epoch == 1, "train_loss"] += 1e-9; x.to_csv(f, index=False)

    def ed_row(d):
        x = pd.read_csv(d / "per_subject.csv"); i = x.index[x.variant == "R0"][0]; x.loc[i, "fp"] += 1
        x.to_csv(d / "per_subject.csv", index=False)

    def ed_k(d):
        x = pd.read_csv(d / "k.csv"); x.loc[x.variant == "R0", "k"] *= 1.001; x.to_csv(d / "k.csv", index=False)

    common = dict(base, R2_WORK=str(root / "work_neg"), R2_SCRATCH=str(root / "scratch_neg"))
    print(W.run(root / "neg.py", dict(common, NEG="rep", EUR_TAG="neg1", EUR_PC7_REF=neg_ref("log", ed_log),
                                      SRC_META=str(outs["A"] / "run_meta.json")))[-200:])
    print(W.run(root / "neg.py", dict(common, NEG="r0", EUR_TAG="neg2", EUR_PC7_REF=neg_ref("row", ed_row),
                                      EUR_ARM_REUSE="42,1,2,3", SRC_RUN=str(outs["A"])))[-200:])
    print(W.run(root / "neg.py", dict(common, NEG="k", EUR_TAG="neg3", EUR_PC7_REF=neg_ref("k", ed_k),
                                      EUR_ARM_REUSE="42,1,2,3", SRC_RUN=str(outs["A"])))[-200:])
    print(W.run(root / "neg.py", dict(common, NEG="guard", EUR_TAG="neg4", EUR_PC7_REF=REF_REL,
                                      EUR_TEST_GUARD_H="1e-9"))[-200:])
    badB = root / "negB"
    shutil.copytree(outs["B"], badB)
    x = pd.read_csv(badB / "per_subject.csv"); i = x.index[(x.variant == "R0") & (x.seed == "clean_seed1")][0]
    x.loc[i, "tp"] += 1; x.to_csv(badB / "per_subject.csv", index=False)
    p = subprocess.run([sys.executable, str(ROOT / "src" / "eur_pc7_read.py"), "--runs", str(outs["A"]), str(badB),
                        "--ref", str(ref), "--pc1", str(pc1), "--out", str(root / "neg5")], capture_output=True, text=True)
    assert p.returncode != 0 and "STOP M1" in (p.stdout + p.stderr), p.stdout[-500:] + p.stderr[-500:]
    print("NEG5 PASS: a changed reused row in one run stops the reader (M1)")
    m = repo / "src" / "eur_abl.py"
    keep = m.read_text()
    m.write_text(keep + "\n# edited\n")
    W.run(root / "runner.py", nb_env("neg6", EUR_TEST_ARM_SEEDS=SEEDS["B"]), [nbdir / "EUR_PC7_B.ipynb"],
          expect_fail="modules differ")
    m.write_text(keep)
    print("NEG6 PASS: an edited module stops the notebook before it starts")
    print(f"ALL PASS in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
