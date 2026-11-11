#!/usr/bin/env python
"""r2_rp_make_notebooks.py -- builds the Kaggle notebook RP_RUN of stage RP (RP1 seed 4, RP2 k per seed + rescoring,
RP3 demo-model rule; docs/FUTURE_RESEARCH_PLAN.md §7b, §12 row 11/11 D20-F) from src/r2_rp.py (embedded verbatim with
%%writefile; sha256 checked in the notebook). The repository is cloned at a pinned commit (40-hex hash) holding r2_r1.py
(sha 76cbe51f), the R1_RUN output (results/r2/r1_system/run: checkpoints, r13/run rows, run_meta) and R1_SMOKE's pinned
data hashes. Nothing to fill in.
  python src/r2_rp_make_notebooks.py --run <commit>   -> notebooks/r2/RP_RUN.ipynb
Test mode (synthetic data, build container only): R2_TEST_REPO / R2_TEST_INPUT / R2_TEST_WORK / R2_TEST_SCRATCH."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R0_SHA = "902d15ad4feb3e8a"                                         # r2_core.py (stage R0)
R1_SHA = "76cbe51ff0180d4a"                                         # r2_r1.py (stage R1, R1_RUN)
OUTDIR = Path(os.environ.get("R2_NB_OUTDIR", ROOT / "notebooks" / "r2"))
CORE = (ROOT / "src" / "r2_rp.py").read_text()
SHA = hashlib.sha256(CORE.encode()).hexdigest()[:16]
PKGS = '"mne==1.12.1", "torch_geometric==2.7.0", "ruptures==1.1.10", "timescoring==0.0.7"'


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.strip("\n").splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": t.strip("\n").splitlines(keepends=True)}


def build(commit):
    name = "RP_RUN"
    cells = [md(f"""
# RP_RUN — research track, stage RP: seed 4, k per seed, demo-model rule (numbers for the final report)

**Plan:** `docs/FUTURE_RESEARCH_PLAN.md` §7b; choices in §12 (11/11 D20-F). **Does:** G-data (63 dataset files = the pinned
R1 hashes), G-const-new, library versions vs R1_RUN (mode exact / tolerance), **RP.0** (the R1 checkpoints reproduce the R1
rows), G-vec, G-val; **RP1** training of seed 4 (R1 recipe, 200 epochs, 1 worker); **RP2** k per seed + scoring of every
set (seeds 1–4 + 42), per-window scores (test, chb24, Siena); **RP3** demo model (lowest validation loss).
**Accelerator:** None (CPU). **Internet:** ON. **Inputs:** `thesis-r2-chbmit-features` + `thesis-r2-external-features`
(to resume: also this notebook's previous output). **Outputs:** `/kaggle/working/r2/r1_system/rp/`
(→ `results/r2/r1_system/rp/`). **Runtime:** ≈ 4.5 h (computed estimate: training ≈ 3.9 h from R1's measured 8.26 ms per
step, gates and scoring ≈ 0.6 h).
Code: `github.com/Nhanvas/Thesis` at `{commit[:7]}` (read only) + `r2_rp.py` below (sha256 `{SHA}`). Gates STOP the
notebook (`STOPPED: ...`). **Nothing printed here is a research result.** Do not edit; *Save Version → Save & Run All (Commit)*.
"""), code(f"""
# SETUP: packages + repository at the pinned commit (read only)
import os, sys, subprocess, time, json, hashlib
T_NB = time.time()
os.environ["R2_T0"] = str(T_NB)
NOTEBOOK, REPO_COMMIT = "{name}", "{commit}"
TEST = bool(os.environ.get("R2_TEST_REPO"))                      # synthetic test in the build container only
WORK = os.environ.get("R2_TEST_WORK", "/kaggle/working")
INPUT = os.environ.get("R2_TEST_INPUT", "/kaggle/input")
SCRATCH = os.environ.get("R2_TEST_SCRATCH", "/tmp/r2")
SRC = SCRATCH + "/src_rp"
os.makedirs(SRC, exist_ok=True)
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
if TEST:
    REPO = os.environ["R2_TEST_REPO"]
else:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", {PKGS}])
    REPO = "/tmp/Thesis"
    if not os.path.exists(REPO + "/src/r2_r1.py"):
        r = subprocess.run(f"git init -q {{REPO}} && cd {{REPO}} && git remote add origin https://github.com/Nhanvas/Thesis.git "
                           f"&& git fetch -q --depth 1 origin {{REPO_COMMIT}} && git checkout -q FETCH_HEAD", shell=True)
        if r.returncode != 0:
            subprocess.check_call(f"rm -rf {{REPO}} && git clone -q https://github.com/Nhanvas/Thesis.git {{REPO}} "
                                  f"&& cd {{REPO}} && git checkout -q {{REPO_COMMIT}}", shell=True)
    head = subprocess.check_output(["git", "-C", REPO, "rev-parse", "HEAD"]).decode().strip()
    assert head == REPO_COMMIT, f"wrong commit {{head}}"
for f, want in (("r2_core.py", "{R0_SHA}"), ("r2_r1.py", "{R1_SHA}")):
    got = hashlib.sha256(open(f"{{REPO}}/src/{{f}}", "rb").read()).hexdigest()[:16]
    assert TEST or got == want, f"{{f}} sha {{got}} != {{want}}"
print("repository", REPO, f"({{time.time()-T_NB:.0f}}s)")
"""), code("%%writefile {SRC}/r2_rp.py\n" + CORE), code(f"""
# START: sha check of the embedded file, imports, run metadata, library versions vs R1_RUN (mode)
sha = hashlib.sha256(open(f"{{SRC}}/r2_rp.py", "rb").read()).hexdigest()[:16]
assert sha == "{SHA}", f"r2_rp.py: sha {{sha}} != {SHA} (cell edited?)"
os.environ.update(THESIS_REPO=REPO, R2_WORK=WORK, R2_INPUT=INPUT, R2_SCRATCH=SCRATCH)
sys.path[:0] = [SRC, REPO + "/src"]
import pandas as pd, numpy as np
import torch
torch.set_num_threads(1)
import r2_rp as RP
R1 = RP.R1
W = R1.n_workers()
print("CPU cores:", os.cpu_count(), "| torch threads:", torch.get_num_threads(), "| workers:", W)
META = R1.run_meta("rp", NOTEBOOK, REPO_COMMIT)
MODE, VDIFF = RP.check_versions(META)
print("mode:", MODE, "| version differences vs R1_RUN:", VDIFF)
def stopped(e):
    raise RuntimeError(f"STOPPED: {{e}}") from None
"""), code("""
# VIEWS + G-data (pinned hashes) + G-const-new (constants and window counts = the R1 checkpoints)
try:
    V = RP.build_views()
    RP.gate_data(V)
    RP.gate_const_new(V)
except SystemExit as e:
    stopped(e)
"""), code("""
# RP.0: the 4 R1 checkpoints on the new data, this notebook's per-seed-k path with every k = R1's k, = R1's rows
try:
    G0 = RP.rp0(W)
except SystemExit as e:
    stopped(e)
print(G0["summary"])
"""), code("""
# G-vec (train_gae_v2.py --smoke vs the tensor loop) + G-val (validation loss of the R1 checkpoints recomputed)
try:
    R1.gate_vec(seed=42)
    RP.gate_val(W)
except SystemExit as e:
    stopped(e)
"""), code("""
# RP1: train seed 4 (r2_r1.train_job unchanged; 1 worker, 1 thread; resumable)
MODELS = R1.out_dir() / "models"
EPOCHS = int(os.environ.get("R2_TEST_EPOCHS", 200)) if TEST else 200        # the recipe: 200 (test mode only fewer)
try:
    TS = RP.train_seed4(V, EPOCHS, MODELS)
except SystemExit as e:
    stopped(e)
print(pd.DataFrame(TS)[["seed", "n_train", "ms_per_step", "fit_s", "peak_rss_mb"]].to_string(index=False))
"""), code("""
# RP2: k per seed + scoring of every set (seeds 1-4 and 42) + per-window scores (written; read only by the aggregate)
try:
    KMAP = RP.rp2(MODELS, W)
except SystemExit as e:
    stopped(e)
print("RP2 written:", sorted(p.name for p in (R1.out_dir() / "rp2").iterdir()))
"""), code("""
# RP3: demo model = lowest validation loss among seeds 1-4 (rule fixed in the plan before this run)
try:
    DEMO = RP.rp3(MODELS, KMAP)
except SystemExit as e:
    stopped(e)
print("demo model: seed", DEMO["seed"])
"""), code("""
# END: SUMMARY.md, measured runtime, outputs
print(RP.summary_md())
meta = R1.finish_meta(dict(r2_rp_sha256=hashlib.sha256(open(f"{SRC}/r2_rp.py", "rb").read()).hexdigest(), mode=RP.STATE["mode"]))
print(f"MEASURED notebook runtime: {meta['runtime_h']} h | phases (s): {meta['phases_s']}")
for p in sorted(R1.out_dir().rglob("*")):
    if p.is_file() and "scores" not in p.parts:
        print(p.relative_to(R1.OUT_ROOT), p.stat().st_size)
print("scores:", len(list((R1.out_dir() / "rp2" / "scores").glob("*.csv.gz"))), "files")
""")]
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                       "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / f"{name}.ipynb").write_text(json.dumps(nb, indent=1))
    return OUTDIR / f"{name}.ipynb"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", metavar="COMMIT", required=True, help="40-hex commit holding the R1_RUN output")
    a = ap.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", a.run):
        ap.error("--run takes a 40-hex commit hash, never a tag")
    print("built", build(a.run).name, "r2_rp sha", SHA)
