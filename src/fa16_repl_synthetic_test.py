#!/usr/bin/env python
"""fa16_repl_synthetic_test.py -- full test of the F-A1.6 replication (src/fa16_repl.py, src/fa16_repl_aggregate.py,
src/fa16_repl_make_notebook.py) on SYNTHETIC data (build container only), plus read-only checks on the real clone.

Part R (real clone, read only): R1 the aggregate's reading code reproduces the committed F2 reading of the MLP-AE
  (results/f1_repcv/F2_across_partitions.csv, VERDICT.json) from the record rows; R2 the builder accepts the pin that
  holds fa16_kmeans.py, the FA16 output and the F1 record (fa16_repl.py absent there) and, in a scratch clone, refuses a
  pin whose f1_core.py or fa16_repl.py differs from the local file.
Part E (synthetic world: 24 cases, the real folds and partitions, random committed models): the record is written by the
  record's own code -- results/v9_x3 and results/model_cmp (GAE, MLP-AE, IF; f1 synthetic world + fa16 test), the FA16
  run by src/fa16_kmeans.py itself (= results/fa16/run), the F1 record of partitions 1-5 by f1_core.job (GAE and MLP-AE,
  2 epochs) and its F2 reading by the aggregate's reading code. E1 the run: every gate PASS (D0, G-parts, G-base x 5,
  G-kmD, G-km0 x 2, G-done), km and km_u on partitions 0-5 for 24 cases; E2 the aggregate: A0 / A1 PASS, every table,
  the verdicts; E3 STOP paths: an F1 record GAE row tp + 1 (p3) -> G-base, no K-means row written; one FA16 km_k value
  -> G-kmD; one FA16 km row fp + 1 -> G-km0; the aggregate refuses the stopped run (A0) and an altered committed F2
  reading (A1); E4 the notebook cell by cell = the direct run table for table; an edited embedded cell -> sha assert.
  python src/fa16_repl_synthetic_test.py [--root DIR] [--part R|E|all]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def part_r():
    t = time.time()
    import fa16_repl_aggregate as A
    import f1_aggregate as FA
    R = A.load_record(ROOT / "results" / "model_cmp", ROOT / "results" / "f1_repcv" / "raw")
    _, T5, V = A.reading(FA.per_case(R["per_subject"]), R["auroc"], "mlp", "gae", list(range(6)))
    ref = pd.read_csv(ROOT / "results" / "f1_repcv" / "F2_across_partitions.csv").set_index("quantity")
    for r in T5.itertuples():
        for c in ("mean", "lo", "hi"):
            assert abs(getattr(r, c) - ref.loc[r.quantity, c]) < 1e-12, (r.quantity, c)
    assert V["n_pos"] == 6 and V["verdict"] == "stable advantage of MLP-AE"
    print("R1 the reading code reproduces the committed F2 reading of the MLP-AE (5 quantities, 1e-12; 6 / 6) -> PASS")
    head = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"]).decode().strip()
    files = ("fa16_repl.py", "fa16_repl_make_notebook.py")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        env = dict(os.environ, FA16_NB_OUTDIR=str(td / "nb"))
        p = subprocess.run([sys.executable, str(ROOT / "src" / "fa16_repl_make_notebook.py"), "--run", head], env=env,
                           capture_output=True, text=True)
        assert p.returncode == 0, p.stderr
        cl = td / "clone"
        subprocess.check_call(["git", "clone", "-q", str(ROOT), str(cl)])
        g = ["git", "-C", str(cl), "-c", "user.email=t@t", "-c", "user.name=t"]
        for f in files:
            shutil.copyfile(ROOT / "src" / f, cl / "src" / f)
        mk = [sys.executable, str(cl / "src" / "fa16_repl_make_notebook.py"), "--run"]
        core = (cl / "src" / "f1_core.py").read_bytes()
        (cl / "src" / "f1_core.py").write_bytes(core + b"# other\n")
        subprocess.check_call(g + ["commit", "-qam", "other f1_core"])
        x = subprocess.check_output(g + ["rev-parse", "HEAD"]).decode().strip()
        (cl / "src" / "f1_core.py").write_bytes(core)
        p = subprocess.run(mk + [x], env=env, capture_output=True, text=True)
        assert p.returncode != 0 and f"f1_core.py at {x[:7]} differs" in p.stderr, p.stderr
        subprocess.check_call(g + ["commit", "-qam", "back"])
        rp = (cl / "src" / "fa16_repl.py").read_bytes()
        (cl / "src" / "fa16_repl.py").write_bytes(rp + b"# other\n")
        subprocess.check_call(g + ["add", "src/fa16_repl.py"]); subprocess.check_call(g + ["commit", "-qm", "other repl"])
        y = subprocess.check_output(g + ["rev-parse", "HEAD"]).decode().strip()
        (cl / "src" / "fa16_repl.py").write_bytes(rp)
        p = subprocess.run(mk + [y], env=env, capture_output=True, text=True)
        assert p.returncode != 0 and f"fa16_repl.py at {y[:7]} differs" in p.stderr, p.stderr
    print(f"R2 builder: pin {head[:7]} accepted; a pin with another f1_core.py or fa16_repl.py refused -> PASS")
    print(f"PART R ALL PASS ({time.time() - t:.0f} s)")


GEN_F1 = r"""
import os, sys, json, torch, pandas as pd
from pathlib import Path
REPO = Path(os.environ["THESIS_REPO"])
sys.path.insert(0, str(REPO / "src"))
import f1_core as F
import model_cmp_core as C
C.locate_all(os.environ["FA16R_INPUT"])
raw = REPO / "results" / "f1_repcv" / "raw"
for p in range(1, 6):
    for model in F.MODELS:
        for f in C.FOLDS:
            F.job(p, model, f, torch.device("cpu"), raw)
    pd_ = raw / f"p{p}"
    for n in ("per_subject", "curves", "auroc", "seizures"):
        pd.concat([pd.read_csv(d.parent / f"{n}.csv") for d in sorted((pd_ / "jobs").glob("*/DONE.json"))],
                  ignore_index=True).to_csv(pd_ / f"{n}.csv", index=False)
sys.path.insert(0, os.environ["FA16_REAL"] + "/src")
import fa16_repl_aggregate as A, f1_aggregate as FA
R = A.load_record(REPO / "results" / "model_cmp", raw)
_, T5, V = A.reading(FA.per_case(R["per_subject"]), R["auroc"], "mlp", "gae", list(range(6)))
T5.drop(columns=["model", "reference"]).to_csv(REPO / "results" / "f1_repcv" / "F2_across_partitions.csv", index=False)
vm = {"stable advantage of MLP-AE": "stable advantage of the MLP-AE (without message passing)",
      "stable advantage of GAE": "stable advantage of the GAE", "not stable": "not stable"}
(REPO / "results" / "f1_repcv" / "VERDICT.json").write_text(json.dumps(dict(V, verdict=vm[V["verdict"]]), default=float))
print("F1 record p1-p5 + F2 reading generated:", V["verdict"])
"""

RUN = r"""
import os, sys
sys.path[:0] = [os.environ['FA16_REAL'] + '/src', os.environ['THESIS_REPO'] + '/src']
import fa16_repl as M
M.main('synthetic', 'local', os.environ['FA16R_INPUT'])
"""


def part_e(root):
    import f1_synthetic_test as F1S
    from fa16_synthetic_test import COMMIT_IF, RUN as RUN16, run
    from r2_r1_synthetic_test import RUNNER
    t = time.time()
    root.mkdir(parents=True, exist_ok=True)
    repo, inp = F1S.build(root)
    F1S.make_committed(repo, inp)
    base = dict(THESIS_REPO=str(repo), FA16_INPUT=str(inp), FA16R_INPUT=str(inp), FA16_REAL=str(ROOT),
                F1_EPOCHS="2", OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONHASHSEED="0")
    for n, body in (("commit_if.py", COMMIT_IF), ("run_fa16.py", RUN16), ("gen_f1.py", GEN_F1), ("run_repl.py", RUN),
                    ("runner.py", RUNNER)):
        (root / n).write_text(body)
    run([root / "commit_if.py"], base)
    run([root / "run_fa16.py"], dict(base, FA16_OUT=str(root / "fa16out" / "fa16")))
    dst = repo / "results" / "fa16" / "run" / "fa16"
    shutil.copytree(root / "fa16out" / "fa16", dst)
    print(run([root / "gen_f1.py"], base).strip().splitlines()[-1], f"(world + FA16 + F1 record: {time.time() - t:.0f} s)")

    def env(tag):
        return dict(base, FA16R_OUT=str(root / f"w_{tag}" / "fa16_repl"))

    def gates(tag):
        return json.loads((root / f"w_{tag}" / "fa16_repl" / "gates.json").read_text())

    t1 = time.time()
    run([root / "run_repl.py"], env("main"))
    G = gates("main")
    cnt = {}
    for g in G:
        assert g["status"] == "PASS", g
        cnt[g["gate"]] = cnt.get(g["gate"], 0) + 1
    assert cnt == {"D0": 1, "G-parts": 1, "G-base": 5, "G-kmD": 1, "G-km0": 2, "G-done": 1}, cnt
    out = root / "w_main" / "fa16_repl"
    per = pd.read_csv(out / "per_subject.csv")
    for m in ("km", "km_u"):
        for p in range(6):
            assert per[(per.model == m) & (per.partition == p)].subject.nunique() == 24, (m, p)
    print(f"E1 run: every gate PASS ({cnt}); km and km_u on partitions 0-5 for 24 cases ({time.time() - t1:.0f} s)")
    agg = run([ROOT / "src" / "fa16_repl_aggregate.py", root / "w_main", "--out", root / "agg",
               "--mc", repo / "results" / "model_cmp", "--f1", repo / "results" / "f1_repcv"], base)
    assert "A0 / A1 PASS" in agg
    V = json.loads((root / "agg" / "VERDICT.json").read_text())
    assert [(v["model"], v["reference"]) for v in V] == [("km", "gae"), ("km_u", "gae"), ("km_u", "km"), ("km", "mlp")]
    t4 = pd.read_csv(root / "agg" / "diff_per_partition.csv")
    assert len(t4) == 4 * 6 and set(t4.partition) == set(range(6))
    for n in ("per_partition", "across_partitions", "diff_across_partitions"):
        assert len(pd.read_csv(root / "agg" / f"{n}.csv")), n
    print(f"E2 aggregate: A0 / A1 PASS; per partition, across, differences, verdicts ({V[0]['verdict']}) -> PASS")
    # E3 STOP paths
    f1p3 = repo / "results" / "f1_repcv" / "raw" / "p3" / "per_subject.csv"
    keep = f1p3.read_bytes()
    d = pd.read_csv(f1p3)
    i = d.index[(d.model == "gae") & (d.point == "own") & (d.stage == "localized")][4]
    d.loc[i, "tp"] += 1; d.to_csv(f1p3, index=False)
    run([root / "run_repl.py"], env("stopbase"), expect_fail="STOP G-base")
    p2 = pd.read_csv(root / "w_stopbase" / "fa16_repl" / "per_subject.csv")
    assert not ({"km", "km_u"} & set(p2.model))
    run([ROOT / "src" / "fa16_repl_aggregate.py", root / "w_stopbase", "--out", root / "agg_x",
         "--mc", repo / "results" / "model_cmp", "--f1", repo / "results" / "f1_repcv"], base, expect_fail="STOP A0")
    f1p3.write_bytes(keep)
    kk = dst / "km_k.csv"
    keep = kk.read_bytes()
    d = pd.read_csv(kk); d.loc[d.index[100], "k"] += 1; d.to_csv(kk, index=False)
    run([root / "run_repl.py"], env("stopkmd"), expect_fail="STOP G-kmD")
    kk.write_bytes(keep)
    ps = dst / "per_subject.csv"
    keep = ps.read_bytes()
    d = pd.read_csv(ps)
    i = d.index[(d.model == "km_u") & (d.point == "fixed0.005") & (d.stage == "detector")][9]
    d.loc[i, "fp"] += 1; d.to_csv(ps, index=False)
    run([root / "run_repl.py"], env("stopkm0"), expect_fail="STOP G-km0")
    ps.write_bytes(keep)
    f2 = repo / "results" / "f1_repcv" / "F2_across_partitions.csv"
    keep = f2.read_bytes()
    d = pd.read_csv(f2); d.loc[0, "lo"] += 1e-6; d.to_csv(f2, index=False)
    run([ROOT / "src" / "fa16_repl_aggregate.py", root / "w_main", "--out", root / "agg_y",
         "--mc", repo / "results" / "model_cmp", "--f1", repo / "results" / "f1_repcv"], base, expect_fail="STOP A1")
    f2.write_bytes(keep)
    print("E3 STOP paths: F1 record GAE row tp + 1 -> G-base (no K-means row); FA16 km_k value -> G-kmD; FA16 km_u row "
          "fp + 1 -> G-km0; the aggregate refuses the stopped run (A0) and an altered F2 reading (A1) -> PASS")
    # E4 notebook
    nbdir = root / "nb"
    subprocess.check_call([sys.executable, str(ROOT / "src" / "fa16_repl_make_notebook.py"), "--run", "0" * 40],
                          env=dict(os.environ, FA16_NB_OUTDIR=str(nbdir)), stdout=subprocess.DEVNULL)
    nbenv = dict(base, FA16R_TEST_REPO=str(repo), FA16R_TEST_INPUT=str(inp), FA16R_TEST_WORK=str(root / "w_nb"))
    t3 = time.time()
    run([root / "runner.py", nbdir / "FA16_REPL.ipynb"], nbenv)
    for n in ("per_subject", "curves", "auroc", "seizures", "km_k"):
        a_ = pd.read_csv(out / f"{n}.csv"); b_ = pd.read_csv(root / "w_nb" / "fa16_repl" / f"{n}.csv")
        if n == "km_k":
            a_, b_ = a_.drop(columns="seconds"), b_.drop(columns="seconds")
        pd.testing.assert_frame_equal(a_, b_, check_exact=True)
    nb = json.loads((nbdir / "FA16_REPL.ipynb").read_text())
    ci = next(i for i, c in enumerate(nb["cells"]) if "".join(c["source"]).startswith("%%writefile"))
    nb["cells"][ci]["source"].append("# edited\n")
    (nbdir / "edited.ipynb").write_text(json.dumps(nb))
    shutil.rmtree(root / "w_nb")
    run([root / "runner.py", nbdir / "edited.ipynb"], nbenv, expect_fail="cell edited or wrong commit")
    print(f"E4 notebook cell by cell = the direct run (km_k without its timing column); an edited embedded cell -> sha "
          f"assert -> PASS ({time.time() - t3:.0f} s)")
    print(f"PART E ALL PASS ({time.time() - t:.0f} s)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--part", default="all", choices=["R", "E", "all"])
    a = ap.parse_args()
    if a.part in ("R", "all"):
        part_r()
    if a.part in ("E", "all"):
        part_e(Path(a.root) if a.root else Path(tempfile.mkdtemp(prefix="fa16r_test_")))
    print("ALL PASS" if a.part == "all" else f"PART {a.part} PASS")


if __name__ == "__main__":
    main()
