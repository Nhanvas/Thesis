#!/usr/bin/env python
"""r2_rpsdevx_synthetic_test.py -- test of RPS_DEVX (src/r2_rpsdevx.py + its builder) on SYNTHETIC data (build container
only). World: the RP_SERIES synthetic world built by src/r2_rps_synthetic_test.py (--root, default /tmp/rps_synth: the
stage-RP synthetic datasets, the committed synthetic RP_RUN output).
Checks: the notebook PASSES in mode exact (G-data, RS.0-dev: every run_budget row of the 15 development patients = the
synthetic rp2/per_subject.csv, error pairs and q equal); 15 score files with the window masks = the dataset's flags and
x_s1..x_s4 finite on ok windows; x of seed 3 = an independent recomputation through r2_rps' own path for one patient
(chb01); negative path: one development row of rp2/per_subject.csv changed -> STOP RS.0-dev.
  python src/r2_rpsdevx_synthetic_test.py [--world /tmp/rps_synth]
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
DEV = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08", "chb09", "chb10", "chb11", "chb12", "chb19", "chb20", "chb21",
       "chb22", "chb23"]
TEST = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
RUNNER = (ROOT / "src" / "r2_rse7_synthetic_test.py").read_text().split("RUNNER = r'''", 1)[1].split("'''", 1)[0]
CHECK = r'''
import os, sys
import numpy as np, pandas as pd
if __name__ == "__main__":
    sys.path[:0] = [os.environ["SRCD"], os.environ["THESIS_REPO"] + "/src"]
    import torch
    torch.set_num_threads(1)                      # as the pool workers (r2_r1._init_worker)
    import r2_rps as RS
    RP, R1 = RS.RP, RS.R1
    R1.STATE["tag"] = "chk"
    RP.set_tags(list(RS.TAGS))                    # as the pool workers (r2_rp._init)
    RP.build_views()
    RS.PD.CKPT = RP.ckpt_dir_all(RS.RP_DIR / "models")
    z, _ = R1.load_case("chb01", "new")
    idx, D, _ = RS.model_outputs_z(z)
    ctx = R1.chb_ctx("chb01", z, idx, {t: D[t].astype(np.float32) for t in R1.TAGS})
    x = RS.E22.final_scalar(ctx, "clean_seed3")
    e = pd.read_csv(os.environ["EXPORT"], float_precision="round_trip")   # pandas default parser is not round-trip exact
    assert np.array_equal(e.x_s3.values, x, equal_nan=True), "x_s3 differs"
    for k, f in (("ictal", "is_ictal"), ("buffer", "is_buffer"), ("flag5sd", "is_flag5sd"), ("file_idx", "file_idx")):
        assert np.array_equal(e[k].values, z[f].astype(int)), k
    assert np.array_equal(e.ok.values, (~z["is_signal_loss"].astype(bool)).astype(int))
    print("CHECK PASS")
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", default="/tmp/rps_synth")
    a = ap.parse_args()
    t0 = time.time()
    w = Path(a.world)
    repo, inp = w / "repo", w / "input"
    assert (repo / "results/r2/r1_system/rp/rp2/per_subject.csv").exists(), "build the world: src/r2_rps_synthetic_test.py"
    ds = inp / "datasets/u/thesis-r2-chbmit-features/thesis-r2-chbmit-features"
    n_sz = sum(int((np.diff(np.r_[0, np.load(ds / f"{c}.npz", allow_pickle=True)["is_ictal"].astype(int)]) == 1).sum())
               for c in TEST)
    root = w / "devx"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir()
    (root / "runner.py").write_text(RUNNER)
    subprocess.check_call([sys.executable, str(ROOT / "src/r2_rpsdevx_make_notebook.py"), "--run", "0" * 40],
                          env=dict(os.environ, R2_NB_OUTDIR=str(root)), stdout=subprocess.DEVNULL)
    nb = root / "RPS_DEVX.ipynb"

    def run(tag, repo_dir, expect_fail=None):
        env = {k: v for k, v in os.environ.items() if not k.startswith(("R2_", "THESIS_"))}
        env.update(R2_TEST="1", R2_TEST_REPO=str(repo_dir), R2_TEST_INPUT=str(inp), R2_TEST_WORK=str(root / f"work_{tag}"),
                   R2_TEST_SCRATCH=str(root / f"scr_{tag}"), OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                   MKL_NUM_THREADS="1", PYTHONHASHSEED="0", R2_TEST_N_TEST_SEIZURES=str(n_sz))
        p = subprocess.run([sys.executable, str(root / "runner.py"), str(nb)], env=env, capture_output=True, text=True)
        tail = p.stdout[-3000:] + "\n" + p.stderr[-3000:]
        if expect_fail:
            assert p.returncode != 0 and expect_fail in tail, tail
        else:
            assert p.returncode == 0, tail
        return tail
    run("ok", repo)
    out = root / "work_ok/r2/r1_system/rps_devx"
    g = {x["gate"]: x for x in json.loads((out / "gates.json").read_text())}
    assert g["G-data"]["status"] == "PASS" and g["RS.0-dev"]["status"] == "PASS", g
    r0 = g["RS.0-dev"]
    assert r0["mode"] == "exact" and r0["exact_rows"] == r0["rows"] == r0["rows_expected"] == 15 * 4 * 4 * 3, r0
    assert r0["error_groups_differ"] == 0 and r0["q_differ"] == 0 and r0["files"] == 15, r0
    for c in DEV:
        e = pd.read_csv(out / "scores_dev" / f"{c}.csv.gz")
        ok = e.ok.values.astype(bool)
        assert all(np.isfinite(e[f"x_s{s}"].values[ok]).all() for s in (1, 2, 3, 4)), c
    for f in ("SUMMARY.md", "run_meta.json", "timing.csv", "rs0/per_subject.csv"):
        assert (out / f).exists(), f
    print("RPS_DEVX PASS (mode exact; RS.0-dev every row exact; 15 score files)")
    (root / "check.py").write_text(CHECK)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("R2_", "THESIS_"))}
    env.update(R2_TEST="1", THESIS_REPO=str(repo), R2_INPUT=str(inp), R2_WORK=str(root / "chk_work"),
               R2_SCRATCH=str(root / "chk_scr"), SRCD=str(root / "scr_ok/src_devx"), EXPORT=str(out / "scores_dev/chb01.csv.gz"),
               OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONHASHSEED="0",
               R2_TEST_N_TEST_SEIZURES=str(n_sz))
    p = subprocess.run([sys.executable, str(root / "check.py")], env=env, capture_output=True, text=True)
    assert p.returncode == 0 and "CHECK PASS" in p.stdout, p.stdout[-2000:] + p.stderr[-3000:]
    print("independent recomputation of chb01 seed 3 and its masks = the export")
    neg = root / "repo_neg"
    shutil.copytree(repo, neg, symlinks=True)
    ps = neg / "results/r2/r1_system/rp/rp2/per_subject.csv"
    ps.unlink()
    d = pd.read_csv(repo / "results/r2/r1_system/rp/rp2/per_subject.csv")
    i = d.index[(d["set"] == "development") & (d.subject == "chb05") & (d.seed == "clean_seed2")][0]
    d.loc[i, "tp"] += 1
    d.to_csv(ps, index=False)
    run("neg", neg, expect_fail="RS.0-dev FAIL")
    print("negative: one development row of rp2 changed -> STOP RS.0-dev")
    print(f"ALL PASS ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
