#!/usr/bin/env python
"""r2_rpsprobe_synthetic_test.py -- test of RPS_PROBE (src/r2_rpsprobe.py + its builder) on SYNTHETIC data (build container
only). World: the RP_SERIES synthetic world (src/r2_rps_synthetic_test.py, default /tmp/rps_synth) with the synthetic
RPS_DEVX export of src/r2_rpsdevx_synthetic_test.py copied into its repository. Checks: the notebook runs to the end; every
step of both cases is logged in probe.csv (load, model_outputs_z, x_equals_rpsdevx = True for the 4 seeds, the e16 parts,
d1b, table7 with its detector seconds, alat_save, case_total); one profile per case, seed and part; SUMMARY.md written.
  python src/r2_rpsprobe_synthetic_test.py [--world /tmp/rps_synth]"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RUNNER = (ROOT / "src" / "r2_rse7_synthetic_test.py").read_text().split("RUNNER = r'''", 1)[1].split("'''", 1)[0]
TEST = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", default="/tmp/rps_synth")
    a = ap.parse_args()
    t0 = time.time()
    w = Path(a.world)
    devx = w / "devx/work_ok/r2/r1_system/rps_devx/scores_dev"
    assert devx.exists(), "run src/r2_rpsdevx_synthetic_test.py first"
    root = w / "probe"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir()
    repo = root / "repo"
    shutil.copytree(w / "repo", repo, symlinks=True)
    shutil.copytree(devx, repo / "results/r2/r1_system/rps_devx/scores_dev")
    inp = w / "input"
    ds = inp / "datasets/u/thesis-r2-chbmit-features/thesis-r2-chbmit-features"
    n_sz = sum(int((np.diff(np.r_[0, np.load(ds / f"{c}.npz", allow_pickle=True)["is_ictal"].astype(int)]) == 1).sum())
               for c in TEST)
    (root / "runner.py").write_text(RUNNER)
    subprocess.check_call([sys.executable, str(ROOT / "src/r2_rpsprobe_make_notebook.py"), "--run", "0" * 40],
                          env=dict(os.environ, R2_NB_OUTDIR=str(root)), stdout=subprocess.DEVNULL)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("R2_", "THESIS_"))}
    env.update(R2_TEST="1", R2_TEST_REPO=str(repo), R2_TEST_INPUT=str(inp), R2_TEST_WORK=str(root / "work"),
               R2_TEST_SCRATCH=str(root / "scr"), OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
               PYTHONHASHSEED="0", R2_TEST_N_TEST_SEIZURES=str(n_sz))
    p = subprocess.run([sys.executable, str(root / "runner.py"), str(root / "RPS_PROBE.ipynb")], env=env,
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stdout[-3000:] + p.stderr[-3000:]
    out = root / "work/r2/r1_system/rps_probe"
    df = pd.read_csv(out / "probe.csv")
    for c in ("chb10", "chb23"):
        s = df[df.case == c]
        steps = set(s.step)
        need = {"load", "model_outputs_z", "x_equals_rpsdevx", "ctx_final_scalar_budget", "e16_total", "d1b_grid",
                "table7_total", "alat_save", "case_total", "e16_S9base_scalar", "e16_d_scalar", "e16_E16d_grid"}
        assert need <= steps, (c, need - steps)
        assert s[s.step == "x_equals_rpsdevx"].value.astype(str).eq("True").sum() == 4, s[s.step == "x_equals_rpsdevx"]
        t7 = s[s.step == "table7_total"]
        assert len(t7) == 4 and {"t7_pelt_s", "t7_e7_s", "t7_e10_s"} <= set(t7.columns), t7
        assert len(list((out / "profiles").glob(f"{c}_*.txt"))) == 8, c
    assert (out / "SUMMARY.md").exists()
    print(f"RPS_PROBE PASS: every step of chb10 and chb23 logged, x = RPS_DEVX export for 4 seeds, 16 profiles "
          f"({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
