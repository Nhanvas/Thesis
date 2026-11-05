#!/usr/bin/env python
"""model_cmp_make_notebooks.py -- builds the two Kaggle notebooks of the model comparison rev 2 from
src/model_cmp_core.py and src/model_cmp_run.py (embedded verbatim with %%writefile). The repository is cloned at
the pinned commit for the frozen chain, the fold checkpoints and the reference results. Nothing to fill in.
  python src/model_cmp_make_notebooks.py        -> notebooks/model_cmp/MC2_*.ipynb"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "6c5d4d8a83e707e9ab9a9c6e161e5c2f9936fff8"
OUTDIR = ROOT / "notebooks" / "model_cmp"
CORE = (ROOT / "src" / "model_cmp_core.py").read_text()
RUN = (ROOT / "src" / "model_cmp_run.py").read_text()
SHA = {n: hashlib.sha256(t.encode()).hexdigest()[:16] for n, t in (("core", CORE), ("run", RUN))}

NB = {
    "MC2_A_label_free_and_classical": dict(
        gpu=False, account="account 1 (Nhân2mm)",
        what="GAE (gate GG: must reproduce the committed CV exactly), Isolation Forest, linear SVM, gradient-boosted trees",
        smoke="R.supervised(['svm', 'hgb'], smoke=True)",
        full="R.unsupervised(('gae', 'if'))\n    R.supervised(['hgb', 'svm'])"),
    "MC2_B_cnn": dict(
        gpu=True, account="account 2 (nhannguyen26)", what="1-D CNN (supervised), 4 folds, 30 epochs each",
        smoke="R.supervised(['cnn'], smoke=True)", full="R.supervised(['cnn'])"),
    "MC3_mlp_folds12": dict(
        gpu=True, account="account 3 (Nhancoding)", what="MLP autoencoder (the GAE without message passing), folds 1 and 2, 200 epochs each",
        smoke="R.mlp([1, 2], DEVICE, smoke=True)", full="R.mlp([1, 2], DEVICE)"),
    "MC3_mlp_folds34": dict(
        gpu=True, account="account 4 (Norn Creades)", what="MLP autoencoder (the GAE without message passing), folds 3 and 4, 200 epochs each",
        smoke="R.mlp([3, 4], DEVICE, smoke=True)", full="R.mlp([3, 4], DEVICE)"),
}
BUILD = [n for n in NB if n.startswith("MC3_")]     # MC2_* already ran (03/11); rebuild them only on purpose


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.strip("\n").splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": t.strip("\n").splitlines(keepends=True)}


def build(name, cfg):
    cells = [
        md(f"""
# {name} — model comparison rev 2 (MODEL_COMPARISON_PLAN.md rev 2)

**Runs:** {cfg['what']}. **Account:** {cfg['account']}. **Accelerator:** {'GPU T4 x2' if cfg['gpu'] else 'None (CPU)'}. **Internet:** on.
**Inputs:** public datasets `v9-x3-fold1` + `v9-x3-fold3` (all 24 CHB-MIT cases). Code: `github.com/Nhanvas/Thesis` at
`{COMMIT[:7]}` (read only) + `model_cmp_core.py` (sha256 `{SHA['core']}`) and `model_cmp_run.py` (sha256 `{SHA['run']}`) below.
4-fold patient-wise CV (`results/v9_x3/folds.json`), seed 42, no early stopping, frozen downstream chain.
Order: setup → D0 → smoke (G-mini + a small end-to-end run, measured time) → full run → `/kaggle/working/model_cmp/`.
**Nothing printed here is a result** until verification (`src/model_cmp_aggregate.py`). Do not edit; *Save Version → Save & Run All (Commit)*.
"""),
        code(f"""
# SETUP: packages + repository at the pinned commit (read only)
import os, sys, subprocess, time, json, hashlib
T_NB = time.time()
NOTEBOOK = "{name}"
REPO_COMMIT = "{COMMIT}"
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",
                       "torch_geometric==2.7.0", "ruptures==1.1.10", "timescoring==0.0.7"])
REPO = "/tmp/Thesis"
if not os.path.exists(REPO + "/src/p2_scalars.py"):
    r = subprocess.run(f"git init -q {{REPO}} && cd {{REPO}} && git remote add origin https://github.com/Nhanvas/Thesis.git "
                       f"&& git fetch -q --depth 1 origin {{REPO_COMMIT}} && git checkout -q FETCH_HEAD", shell=True)
    if r.returncode != 0:
        subprocess.check_call(f"rm -rf {{REPO}} && git clone -q https://github.com/Nhanvas/Thesis.git {{REPO}} "
                              f"&& cd {{REPO}} && git checkout -q {{REPO_COMMIT}}", shell=True)
head = subprocess.check_output(["git", "-C", REPO, "rev-parse", "HEAD"]).decode().strip()
assert head == REPO_COMMIT, f"wrong commit {{head}}"
os.makedirs("/kaggle/working/mc_src", exist_ok=True)
print("repository at", head, f"({{time.time()-T_NB:.0f}}s)")
"""),
        code("%%writefile /kaggle/working/mc_src/model_cmp_core.py\n" + CORE),
        code("%%writefile /kaggle/working/mc_src/model_cmp_run.py\n" + RUN),
        code(f"""
# START: imports, run metadata, data gate D0 (hard stop on wrong data)
os.environ["THESIS_REPO"] = REPO
os.environ["MC_OUT"] = "/kaggle/working/model_cmp"
sys.path.insert(0, "/kaggle/working/mc_src")
import pandas as pd
import model_cmp_core as C
import model_cmp_run as R
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
{'import torch' + chr(10) + 'assert torch.cuda.is_available(), "No GPU: set Accelerator = GPU T4 x2"' + chr(10) + 'DEVICE = torch.device("cuda")' if cfg['gpu'] else ''}
try:
    R.run_meta(NOTEBOOK, dict(core_sha=sha("/kaggle/working/mc_src/model_cmp_core.py"),
                              run_sha=sha("/kaggle/working/mc_src/model_cmp_run.py")))
    R.setup("/kaggle/input")
except SystemExit as e:
    raise RuntimeError(f"STOPPED: {{e}}") from None
"""),
        code(f"""
# SMOKE (always first): G-mini gate + a small end-to-end run of each model of this notebook; measured time
t_smoke = time.time()
try:
    ok, _ = R.mini_gate()
    if not ok:
        raise SystemExit("gate G-mini failed: the GAE fold-1 chb12 row does not reproduce the committed CV")
    {cfg['smoke']}
except SystemExit as e:
    raise RuntimeError(f"STOPPED: {{e}}") from None
print(f"SMOKE PASS in {{time.time()-t_smoke:.0f}}s")
"""),
        code(f"""
# FULL RUN (each model x fold written as soon as it ends)
t_full = time.time()
try:
    {cfg['full']}
except SystemExit as e:
    raise RuntimeError(f"STOPPED: {{e}}") from None
print(f"FULL done in {{(time.time()-t_full)/3600:.2f}} h")
"""),
        code("""
# END: gates, jobs, unverified summary, measured runtime
print(json.dumps(R.GATES, indent=1, default=str))
print(json.dumps(R.JOBS, indent=1, default=str))
R.summary()
meta = json.load(open("/kaggle/working/model_cmp/run_meta.json"))
meta.update(notebook_runtime_h=round((time.time() - T_NB) / 3600, 3), finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"))
json.dump(meta, open("/kaggle/working/model_cmp/run_meta.json", "w"), indent=1)
print(f"MEASURED notebook runtime: {meta['notebook_runtime_h']} h")
print(sorted(os.listdir("/kaggle/working/model_cmp")))
"""),
    ]
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                       "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / f"{name}.ipynb").write_text(json.dumps(nb, indent=1))


for n in BUILD:
    build(n, NB[n])
print("built", BUILD, "core", SHA["core"], "run", SHA["run"])
