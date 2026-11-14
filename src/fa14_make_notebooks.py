#!/usr/bin/env python
"""fa14_make_notebooks.py -- builds the Kaggle notebooks of F-A1.4 (docs/FUTURE_RESEARCH_PLAN.md §12 14/11 23:10, D28-F)
from src/fa14_mech.py (embedded verbatim with %%writefile; sha256 checked in the notebook). The repository is cloned at a
pinned commit (40-hex hash) holding the committed checkpoints and records (results/v9_x3/models, results/model_cmp,
results/f1_repcv/raw, results/r2/r0_data/chb/gates.json, results/r2/r2_cv/a/run_meta.json).
  FA14_P0    partition 0 (the six-model comparison)
  FA14_REPL  partitions 1-5 (the defense-time F1 record)
  python src/fa14_make_notebooks.py --run <commit>   -> notebooks/fa14/FA14_P0.ipynb, FA14_REPL.ipynb
Test mode (synthetic data, build container only): FA14_TEST_REPO / R2_INPUT / FA14_WORK."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = Path(os.environ.get("FA14_NB_OUTDIR", ROOT / "notebooks" / "fa14"))
CORE = (ROOT / "src" / "fa14_mech.py").read_text()
SHA_CORE = hashlib.sha256(CORE.encode()).hexdigest()[:16]
PKGS = '"torch_geometric==2.7.0", "ruptures==1.1.10", "timescoring==0.0.7"'
NB = {"FA14_P0": ((0,), "partition 0 = the six-model comparison (GAE results/v9_x3, MLP-AE results/model_cmp/ckpt)",
                  "about 0.5 h"),
      "FA14_REPL": ((1, 2, 3, 4, 5), "partitions 1-5 = the defense-time F1 record (results/f1_repcv/raw)", "about 1-1.5 h")}


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.strip("\n").splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": t.strip("\n").splitlines(keepends=True)}


def build(commit, name):
    parts, what, rt = NB[name]
    cells = [md(f"""
# {name} — F-A1.4: where the extra false alarms of the GAE come from (no training), {what}

**Plan:** `docs/FUTURE_RESEARCH_PLAN.md` §12 14/11 23:10 (design approved 14/11 23:08). Four arms per fold — the committed
GAE, the committed MLP-AE, the GAE on a time-stable graph per patient (I-fix) and the GAE without edges (I-self) — through
the record's chain; then descriptive tables per held-out case. **Gates before any reading:** G-mod, mode, G-data (earlier
.npz = R0's pinned sha256), G-gcn, G-arm (every job), G-base (the gae / mlp rows = the record exactly; mode exact).
**Accelerator:** None (CPU). **Internet:** ON (pip torch_geometric, git clone) → a verified account.
**Inputs:** `v9-x3-fold1` (nhn2mm) and `v9-x3-fold3` (nhannguyen26) — nothing else (to resume, also this notebook's
previous output). **Output:** `/kaggle/working/fa14/` (→ `results/fa14/`), < 20 MB. **Runtime:** {rt} (computed estimate;
measured in `run_meta.json`). Code: `github.com/Nhanvas/Thesis` at `{commit[:7]}` (read only) + `fa14_mech.py` (sha256
`{SHA_CORE}`) below. **Nothing printed here is a research result.** Do not edit; *Save Version → Save & Run All (Commit)*.
"""), code(f"""
# SETUP: packages + repository at the pinned commit (read only)
import os, sys, subprocess, time, json, hashlib
T_NB = time.time()
NOTEBOOK, REPO_COMMIT, PARTS = "{name}", "{commit}", {list(parts)}
TEST = bool(os.environ.get("FA14_TEST_REPO"))                    # synthetic test in the build container only
WORK = os.environ.get("FA14_WORK", "/kaggle/working")
SRC = os.environ.get("FA14_SCRATCH", "/tmp/fa14") + "/src"
os.makedirs(SRC, exist_ok=True)
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
if TEST:
    REPO = os.environ["FA14_TEST_REPO"]
else:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", {PKGS}])
    REPO = "/tmp/Thesis"
    if not os.path.exists(REPO + "/src/f1_core.py"):
        r = subprocess.run(f"git init -q {{REPO}} && cd {{REPO}} && git remote add origin https://github.com/Nhanvas/Thesis.git "
                           f"&& git fetch -q --depth 1 origin {{REPO_COMMIT}} && git checkout -q FETCH_HEAD", shell=True)
        if r.returncode != 0:
            subprocess.check_call(f"rm -rf {{REPO}} && git clone -q https://github.com/Nhanvas/Thesis.git {{REPO}} "
                                  f"&& cd {{REPO}} && git checkout -q {{REPO_COMMIT}}", shell=True)
    head = subprocess.check_output(["git", "-C", REPO, "rev-parse", "HEAD"]).decode().strip()
    assert head == REPO_COMMIT, f"wrong commit {{head}}"
print("repository", REPO, f"({{time.time()-T_NB:.0f}}s)")
"""), code("%%writefile {SRC}/fa14_mech.py\n" + CORE), code(f"""
# START: sha check of the embedded file, imports
sha = hashlib.sha256(open(f"{{SRC}}/fa14_mech.py", "rb").read()).hexdigest()[:16]
assert sha == "{SHA_CORE}", f"fa14_mech.py: sha {{sha}} != {SHA_CORE} (cell edited?)"
os.environ.update(THESIS_REPO=REPO, FA14_WORK=WORK)
sys.path[:0] = [SRC]
import fa14_mech as M
print("CPU cores:", os.cpu_count(), "| workers:", M.n_workers(), "| partitions:", PARTS)
"""), code("""
# RUN: gates, the jobs (partition x fold; four arms each), merge, G-base; STOPPED if a gate fails (outputs kept)
ERR = None
try:
    M.main(NOTEBOOK, REPO_COMMIT, tuple(PARTS))
except SystemExit as e:
    ERR = str(e)
"""), code("""
# END: summary, measured runtime, outputs
if (M.OUT / "SUMMARY.md").exists():
    print(open(M.OUT / "SUMMARY.md").read())
meta = json.loads(open(M.OUT / "run_meta.json").read()) if (M.OUT / "run_meta.json").exists() else {}
print("MEASURED notebook runtime:", meta.get("runtime_h"), "h")
for p in sorted(M.OUT.rglob("*")):
    if p.is_file() and "jobs" not in p.parts:
        print(p.relative_to(M.WORK), p.stat().st_size)
if ERR:
    raise RuntimeError(f"STOPPED: {ERR}")
""")]
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                       "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / f"{name}.ipynb").write_text(json.dumps(nb, indent=1))
    return OUTDIR / f"{name}.ipynb"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", metavar="COMMIT", required=True, help="40-hex commit holding the checkpoints and records")
    a = ap.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", a.run):
        ap.error("--run takes a 40-hex commit hash, never a tag")
    for name in NB:
        print("built", build(a.run, name))
    print("fa14_mech sha", SHA_CORE)
