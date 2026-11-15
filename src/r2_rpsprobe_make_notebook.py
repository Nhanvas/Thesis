#!/usr/bin/env python
"""r2_rpsprobe_make_notebook.py -- builds the Kaggle notebook RPS_PROBE (second diagnosis step of the slow RP_SERIES
pass A; docs/FUTURE_RESEARCH_PLAN.md §12 15/11 11:30, D27-F) from src/r2_e7exact.py, src/r2_rps.py and src/r2_rpsprobe.py
(embedded verbatim with %%writefile; sha256 checked in the notebook); the SETUP cell is RP_SERIES' (same pinned clone,
same sha checks of r2_core / r2_r1 / r2_rp).
  python src/r2_rpsprobe_make_notebook.py --run <commit>   -> notebooks/r2/RPS_PROBE.ipynb
Test mode (synthetic data, build container only): R2_TEST_REPO / R2_TEST_INPUT / R2_TEST_WORK / R2_TEST_SCRATCH."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R0_SHA = "902d15ad4feb3e8a"
R1_SHA = "76cbe51ff0180d4a"
RP_SHA = hashlib.sha256((ROOT / "src" / "r2_rp.py").read_bytes()).hexdigest()[:16]
OUTDIR = Path(os.environ.get("R2_NB_OUTDIR", ROOT / "notebooks" / "r2"))
FILES = {f: (ROOT / "src" / f).read_text() for f in ("r2_e7exact.py", "r2_rps.py", "r2_rpsprobe.py")}
SHAS = {f: hashlib.sha256(t.encode()).hexdigest()[:16] for f, t in FILES.items()}
PKGS = '"mne==1.12.1", "torch_geometric==2.7.0", "ruptures==1.1.10", "timescoring==0.0.7"'


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.strip("\n").splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": t.strip("\n").splitlines(keepends=True)}


def build(commit):
    name = "RPS_PROBE"
    cells = [md(f"""
# RPS_PROBE — step timing of RP_SERIES' series_job on real development patients (diagnosis; timing only)

**Plan:** `docs/FUTURE_RESEARCH_PLAN.md` §12 15/11 11:30 (D27-F). **Does:** G-data, versions; then **chb10, then chb23**,
in the main process: every step of RP_SERIES' series_job timed and logged at once (lines `PROBE {{...}}`), the e16 arms
and the Table 7 detectors also profiled per seed (`profiles/`). The final scalar is checked against the RPS_DEVX export.
**You may stop the notebook as soon as the log shows the slow step** (the output folder then holds what finished:
use *Save Version* only after it ends, or copy the log lines).
**Accelerator:** None (CPU). **Internet:** ON. **Inputs:** `thesis-r2-chbmit-features` + `thesis-r2-external-features`.
**Output:** `/kaggle/working/r2/r1_system/rps_probe/` (→ `results/r2/r1_system/rps_probe/`), < 1 MB.
**Runtime:** unknown by design (chb10 took 16,054 s inside RP_SERIES; this probe measures where).
Code: `github.com/Nhanvas/Thesis` at `{commit[:7]}` (read only) + {", ".join(f"`{f}` (sha256 `{s}`)" for f, s in SHAS.items())}
below. **Nothing printed here is a research result.** Do not edit; *Save Version → Save & Run All (Commit)*.
"""), code(f"""
# SETUP: packages + repository at the pinned commit (read only)
import os, sys, subprocess, time, json, hashlib, shutil
T_NB = time.time()
os.environ["R2_T0"] = str(T_NB)
NOTEBOOK, REPO_COMMIT = "{name}", "{commit}"
TEST = bool(os.environ.get("R2_TEST_REPO"))                      # synthetic test in the build container only
WORK = os.environ.get("R2_TEST_WORK", "/kaggle/working")
INPUT = os.environ.get("R2_TEST_INPUT", "/kaggle/input")
SCRATCH = os.environ.get("R2_TEST_SCRATCH", "/tmp/r2")
SRC = SCRATCH + "/src_probe"
os.makedirs(SRC, exist_ok=True)
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
if TEST:
    REPO = os.environ["R2_TEST_REPO"]
else:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", {PKGS}])
    REPO = "/tmp/Thesis"
    if not os.path.exists(REPO + "/src/r2_rp.py"):
        r = subprocess.run(f"git init -q {{REPO}} && cd {{REPO}} && git remote add origin https://github.com/Nhanvas/Thesis.git "
                           f"&& git fetch -q --depth 1 origin {{REPO_COMMIT}} && git checkout -q FETCH_HEAD", shell=True)
        if r.returncode != 0:
            subprocess.check_call(f"rm -rf {{REPO}} && git clone -q https://github.com/Nhanvas/Thesis.git {{REPO}} "
                                  f"&& cd {{REPO}} && git checkout -q {{REPO_COMMIT}}", shell=True)
    head = subprocess.check_output(["git", "-C", REPO, "rev-parse", "HEAD"]).decode().strip()
    assert head == REPO_COMMIT, f"wrong commit {{head}}"
for f, want in (("r2_core.py", "{R0_SHA}"), ("r2_r1.py", "{R1_SHA}"), ("r2_rp.py", "{RP_SHA}")):
    got = hashlib.sha256(open(f"{{REPO}}/src/{{f}}", "rb").read()).hexdigest()[:16]
    assert TEST or got == want, f"{{f}} sha {{got}} != {{want}}"
print("repository", REPO, f"({{time.time()-T_NB:.0f}}s)")
""")] + [code("%%writefile {SRC}/" + f + "\n" + t) for f, t in FILES.items()] + [code(f"""
# START: sha checks, imports, run metadata, versions vs R1_RUN (mode)
for f, want in {json.dumps(SHAS)}.items():
    sha = hashlib.sha256(open(f"{{SRC}}/{{f}}", "rb").read()).hexdigest()[:16]
    assert sha == want, f"{{f}}: sha {{sha}} != {{want}} (cell edited?)"
os.environ.update(THESIS_REPO=REPO, R2_WORK=WORK, R2_INPUT=INPUT, R2_SCRATCH=SCRATCH)
sys.path[:0] = [SRC, REPO + "/src"]
import pandas as pd, numpy as np
import torch
torch.set_num_threads(1)
def stopped(e):
    raise RuntimeError(f"STOPPED: {{e}}") from None
import r2_rpsprobe as PR
RP, R1 = PR.RP, PR.R1
W = R1.n_workers()
print("CPU cores:", os.cpu_count(), "| workers:", W)
META = R1.run_meta(PR.TAG, NOTEBOOK, REPO_COMMIT)
MODE, VDIFF = RP.check_versions(META)
print("mode:", MODE, "| version differences vs R1_RUN:", VDIFF)
"""), code("""
# VIEWS + G-data, then the probe: chb10, then chb23 (main process, steps logged as they end)
try:
    V = RP.build_views()
    RP.gate_data(V)
    PR.run(["chb10", "chb23"])
except SystemExit as e:
    stopped(e)
"""), code("""
# END: SUMMARY.md, measured runtime, outputs
print(PR.summary_md())
meta = R1.finish_meta(dict(mode=RP.STATE["mode"]))
print(f"MEASURED notebook runtime: {meta['runtime_h']} h")
for p in sorted(R1.out_dir().rglob("*")):
    if p.is_file():
        print(p.relative_to(R1.OUT_ROOT), p.stat().st_size)
""")]
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                       "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / f"{name}.ipynb").write_text(json.dumps(nb, indent=1))
    return OUTDIR / f"{name}.ipynb"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", metavar="COMMIT", required=True)
    a = ap.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", a.run):
        ap.error("--run takes a 40-hex commit hash, never a tag")
    print("built", build(a.run).name, SHAS)
