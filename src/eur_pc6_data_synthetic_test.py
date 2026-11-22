#!/usr/bin/env python
"""eur_pc6_data_synthetic_test.py -- end-to-end test of the EUR_PC6_DATA notebook (src/eur_pc6_data.py) on SYNTHETIC EDF
files (build container only; never on Kaggle, never on real data). Chat D37-F, design results/eureka_d37f/DESIGN_PC6.md §3.

World: the EUR_DIAG test world (src/eur_diag_synthetic_test.build_world: 23 CHB-MIT-like cases with a fake PhysioNet and
SHA256SUMS served by file://, a corrupted and an absent file on the fake Kaggle copy, the earlier .npz built by the record
code; chb24 and Siena PN00 / PN01 with their label-free .npz built by r2_core's R0.4 path), its record rows and models.
Checks
  P1  EUR_PC6_DATA (built by src/eur_make_notebooks.py --only EUR_PC6_DATA, run cell by cell): every gate PASS (G-raw,
      G-data, G-stack[smoke], G-feat0, PROJ, G-stack, G-struct, G-adj, G-edges, G-worker[pool], G-done); a graph file for
      every case with the record's window count; manifest sha256 = the files; in one container the rebuilt combined graph
      equals the record graph exactly in every case; no EDF and no feature .npz in the output (only graphs/*_g11.npz)
  N1  (non-circular) chb03 and PN00: wPLI-only and AEC-only top-20 % graphs recomputed here from the raw EDF without the
      builders or the wrapper (continuous_eval.filter_file + the committed z-score statistics for CHB-MIT; x1_external's
      loader, filter and label-free statistics for Siena; then graph_construction directly) = adj_11a / adj_11b exactly on
      the first file's windows
  N2  the two arm graphs differ from each other and from the record graph in some windows, and every arm graph has 30 or
      more edges per chain window (top 20 % of 153 pairs; ties kept)
Negative paths: NEG1 the wrapper not installed (PC6_TEST_NO_INSTALL) -> STOP at G-stack in the smoke; NEG2 the record
graph of one test case changed in 5 % of its windows (a copy of the Kaggle input) -> STOP at G-adj; NEG3 an edited module
-> the notebook stops before it starts.
  python src/eur_pc6_data_synthetic_test.py [--root DIR]
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import r2_r1_synthetic_test as RR       # noqa: E402
import eur_9a_synthetic_test as T9      # noqa: E402
import eur_diag_synthetic_test as D     # noqa: E402

N1 = r'''
import json, sys, os
from pathlib import Path
import numpy as np
repo, graphs = map(Path, sys.argv[1:3])
for p in ("src", "src/dataprep", "src/retrain", "src/phaseB", "src/phaseC"):
    sys.path.insert(0, str(repo / p))
import continuous_eval as CE
import x1_external as X1
GC = CE.GC
def topk(A):
    return GC.apply_topk_threshold(A, keep_ratio=GC.DEFAULT_KEEP_RATIO).astype(np.float16)
def graphs_of(zw):
    w_, a_ = [], []
    for i in range(zw.shape[0]):
        car = GC.apply_car(zw[i])
        w_.append(topk(GC.compute_wpli(car))); a_.append(topk(GC.compute_aec(car)))
    return np.array(w_), np.array(a_)
if __name__ == "__main__":
    out = {}
    # CHB-MIT chb03, first file: the record signal path (filter_file, committed statistics) without the builder
    view = Path(sys.argv[3])
    st = json.loads((repo / "data" / "processed" / "chb03_stats.json").read_text())
    mu = np.asarray(st["ch_mean_uV"], np.float64) * 1e-6; sd = np.asarray(st["ch_std_uV"], np.float64) * 1e-6
    CE.DATASET_DIR = view / "chbmit"
    first = CE.list_files("chb03")[0]["fname"]
    filt, n = CE.filter_file(CE.edf_path("chb03", first))
    zw = CE.zscore(filt[:n], mu, sd)
    w_, a_ = graphs_of(zw)
    g = np.load(graphs / "chb03_g11.npz", allow_pickle=True)
    assert np.array_equal(w_, g["adj_11a"][:n]) and np.array_equal(a_, g["adj_11b"][:n]), "chb03 differs"
    out["chb03"] = int(n)
    # Siena PN00, first file: x1's loader, filter and label-free statistics, without the builder
    comp = Path(sys.argv[4])
    files, meta = X1.subject_files(str(comp), "PN00")
    mu2, sd2 = X1.labelfree_stats(files, meta["kind"], meta["notch"])
    data = X1.load_18(files[0][0], meta["kind"])
    filt2, n2 = X1.filter_windows(data, meta["notch"])
    zw2 = (filt2[:n2].astype(np.float64) - mu2[None, :, None]) / sd2[None, :, None]
    w2, a2 = graphs_of(zw2)
    g2 = np.load(graphs / "PN00_g11.npz", allow_pickle=True)
    assert np.array_equal(w2, g2["adj_11a"][:n2]) and np.array_equal(a2, g2["adj_11b"][:n2]), "PN00 differs"
    out["PN00"] = int(n2)
    print("N1 OK", json.dumps(out))
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/tmp/eur_pc6d_synth")
    a = ap.parse_args()
    t0 = time.time()
    root = Path(a.root)
    phys, raw, lap, repo, sp = D.build_world(root)
    f1, f3 = root / "input" / "v9-x3-fold1" / "fold1", root / "input" / "v9-x3-fold3" / "fold3"
    f1.mkdir(parents=True)
    f3.mkdir(parents=True)
    for n, txt in (("record.py", T9.RECORD), ("models.py", T9.MODELS), ("record_gen.py", D.RECORD_GEN_EXT),
                   ("runner.py", RR.RUNNER), ("ext_build.py", D.EXT_BUILD), ("n1.py", N1)):
        (root / n).write_text(txt)
    RR.run(root / "record.py", {}, [repo, lap / "", f1, f3, ",".join(T9.CASES)])
    comp = root / "complete_view"
    (comp / "chbmit").mkdir(parents=True)
    shutil.copytree(phys / "chb24", comp / "chbmit" / "chb24")
    shutil.copytree(sp, comp / "siena")
    dx = root / "input" / "thesis-r2-external-features" / "thesis-r2-external-features"
    print(RR.run(root / "ext_build.py", dict(R2_TEST="1", THESIS_REPO=str(repo)),
                 [repo, comp, dx, ",".join(["chb24"] + list(D.EXT_SIENA))]).strip().splitlines()[-1])
    for p in dx.glob("_*.log"):
        p.unlink()
    RR.run(root / "models.py", {}, [repo, f1, f3, root / "tmp_models"])
    genv = dict(THESIS_REPO=str(repo), R2_WORK=str(root / "work_gen"), R2_INPUT=str(root / "input"),
                R2_SCRATCH=str(root / "scratch_gen"), R2_TEST="1", R1_SRC=str(repo / "src"), OMP_NUM_THREADS="1")
    print(RR.run(root / "record_gen.py", genv).strip().splitlines()[-1])
    env = dict(os.environ, EUR_NB_OUTDIR=str(root / "notebooks"))
    p = subprocess.run([sys.executable, str(repo / "src" / "eur_make_notebooks.py"), "--only", "EUR_PC6_DATA"], env=env,
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stderr[-2000:]
    nb = root / "notebooks" / "EUR_PC6_DATA.ipynb"

    def env_nb(tag, **kw):
        e = D.env_for(root, repo, tag)
        e.update(PC6_TEST_SMOKE_CASE=T9.SMOKE, **kw)
        return e

    # ---- P1
    t = time.time()
    out = RR.run(root / "runner.py", env_nb("ok"), [nb])
    print(out.strip()[-2000:])
    w = root / "work_ok" / "eureka" / "pc6_data"
    gates = {g["gate"]: g["status"] for g in json.loads((w / "gates.json").read_text())}
    need = ("G-raw", "G-data", "G-stack[smoke]", "G-feat0", "PROJ", "G-stack", "G-struct", "G-adj", "G-edges",
            "G-worker[pool]", "G-done")
    assert all(gates.get(n) == "PASS" for n in need), gates
    import pandas as pd
    C = pd.read_csv(w / "cases.csv")
    cases = T9.CASES + ["chb24"] + list(D.EXT_SIENA)
    assert sorted(C.case) == sorted(cases), sorted(C.case)
    assert C.adj_exact_chain.all() and (C.adj_frac_differing_all == 0).all(), C[["case", "adj_frac_differing_all"]]
    M = pd.read_csv(w / "manifest.csv")
    for r in M.itertuples():
        f = w / "graphs" / r.file
        assert hashlib.sha256(f.read_bytes()).hexdigest() == r.sha256, r.file
        g = np.load(f, allow_pickle=True)
        src = (root / "scratch_ok" / "r1_views" / ("ext" if r.case in cases[23:] else "earlier") /
               (f"{r.case}_lf.npz" if r.case in cases[23:] else f"{r.case}.npz"))
        ref = np.load(src, allow_pickle=True)
        assert g["adj_11a"].shape == g["adj_11b"].shape == ref["adj"].shape and int(g["n_windows"]) == len(ref["adj"]), r.case
    bad = [q for q in w.rglob("*") if q.suffix.lower() == ".edf" or (q.suffix == ".npz" and not q.name.endswith("_g11.npz"))]
    assert not bad, bad
    print(f"P1 PASS: every gate; {len(M)} graph files with the record's windows; manifest sha256; combined graph = record "
          f"exactly in every case; no EDF / feature .npz in the output ({time.time() - t:.0f} s)")

    # ---- N1
    view = root / "scratch_ok" / "view" / "earlier"
    print(RR.run(root / "n1.py", dict(R2_TEST="1", THESIS_REPO=str(repo)), [repo, w / "graphs", view, comp]).strip()[-200:])
    print("N1 PASS: chb03 and PN00 arm graphs recomputed from the raw EDF without the builders = the stored graphs")

    # ---- N2
    diff_ab = diff_rec = 0
    for r in M.itertuples():
        g = np.load(w / "graphs" / r.file, allow_pickle=True)
        ref_p = (root / "scratch_ok" / "r1_views" / ("ext" if r.case in cases[23:] else "earlier") /
                 (f"{r.case}_lf.npz" if r.case in cases[23:] else f"{r.case}.npz"))
        ref = np.load(ref_p, allow_pickle=True)
        sl = np.asarray(ref["is_signal_loss"], bool)
        iu = np.triu_indices(18, 1)
        for k in ("adj_11a", "adj_11b"):
            ne = (g[k][:, iu[0], iu[1]] != 0).sum(axis=1)[~sl]
            assert ne.min() >= 30, (r.case, k, ne.min())
        diff_ab += int((np.asarray(g["adj_11a"]) != np.asarray(g["adj_11b"])).any(axis=(1, 2)).sum())
        diff_rec += int((np.asarray(g["adj_11a"]) != np.asarray(ref["adj"])).any(axis=(1, 2)).sum())
    assert diff_ab > 0 and diff_rec > 0, (diff_ab, diff_rec)
    print(f"N2 PASS: 11a differs from 11b in {diff_ab} windows and from the record in {diff_rec}; >= 30 edges per chain window")

    # ---- NEG1: the wrapper not installed -> G-stack
    RR.run(root / "runner.py", env_nb("neg1", PC6_TEST_NO_INSTALL="1"), [nb], expect_fail="G-stack")
    print("NEG1 PASS: without the wrapper the smoke stops at G-stack")

    # ---- NEG2: a record graph changed in 5 % of one test case's windows -> G-adj
    inp2 = root / "input_neg2"
    if inp2.exists():
        shutil.rmtree(inp2)
    shutil.copytree(root / "input", inp2, symlinks=False)
    q = next(inp2.rglob("chb03.npz"))
    z = dict(np.load(q, allow_pickle=True))
    adj = z["adj"].copy()
    k = max(1, len(adj) // 20)
    adj[:k] = adj[:k] * np.float16(0.5)
    z["adj"] = adj
    np.savez(q.with_suffix(".tmp.npz"), **z)
    q.with_suffix(".tmp.npz").replace(q)
    RR.run(root / "runner.py", env_nb("neg2", EUR_TEST_INPUT=str(inp2)), [nb], expect_fail="G-adj")
    print("NEG2 PASS: a changed record graph stops the run at G-adj")

    # ---- NEG3
    cp = T9.clone_repo(root, repo, "repo_neg3")
    with open(cp / "src" / "eur_pc6_data.py", "a") as f:
        f.write("# edited\n")
    RR.run(root / "runner.py", D.env_for(root, cp, "neg3"), [nb], expect_fail="modules differ")
    print("NEG3 PASS: an edited module stops the notebook before it starts")
    print(f"ALL PASS in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
