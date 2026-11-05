#!/usr/bin/env python
"""f1_make_notebooks.py -- builds the Track F1/F2 Kaggle notebooks (docs/FUTURE_RESEARCH_PLAN.md rev 1) from
src/f1_core.py, src/f1_run.py and results/f1_repcv/partitions.json (embedded verbatim with %%writefile; sha256 checked in
the notebook). The repository is cloned at the pinned commit for the frozen chain, model_cmp_core.py, the committed CV
checkpoints and the reference results (read only). Nothing to fill in.
  python src/f1_make_notebooks.py [--parts 1 2 3 4 5]   -> notebooks/track_f/F1_SMOKE.ipynb, F1_p{r}.ipynb
Test mode (synthetic data, this container only): environment F1_TEST_REPO / F1_TEST_INPUT / F1_TEST_WORK."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "1e653fa233344f262379bfc11b8c8b172fe0d562"
OUTDIR = ROOT / "notebooks" / "track_f"
CORE = (ROOT / "src" / "f1_core.py").read_text()
RUN = (ROOT / "src" / "f1_run.py").read_text()
PARTS = (ROOT / "results" / "f1_repcv" / "partitions.json").read_text()
SHA = {n: hashlib.sha256(t.encode()).hexdigest()[:16] for n, t in (("core", CORE), ("run", RUN), ("parts", PARTS))}
ACCOUNTS = ["account 1 (Nhân2mm)", "account 2 (nhannguyen26)", "account 3 (Nhancoding)", "account 4 (Norn Creades)"]


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.strip("\n").splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": t.strip("\n").splitlines(keepends=True)}


def build(name, p, run_full, account):
    what = (f"partition {p} (seed {p}): GAE + MLP autoencoder, 4 folds each (8 jobs), 200 epochs" if run_full else
            "SMOKE ONLY (partition 1): gates + 2-epoch end-to-end + measured speed of the parallel workers")
    cells = [
        md(f"""
# {name} — Track F1/F2, repeated random patient-wise 4-fold CV (FUTURE_RESEARCH_PLAN.md rev 1)

**Runs:** {what}. **Account:** {account}. **Accelerator:** None (CPU) *or* GPU T4 x2 — the code uses whichever is set
(chosen from the smoke measurement). **Internet:** on. **Inputs:** public datasets `v9-x3-fold1` + `v9-x3-fold3`
(all 24 CHB-MIT cases); to resume an interrupted run, also add this notebook's previous version output.
Code: `github.com/Nhanvas/Thesis` at `{COMMIT[:7]}` (read only) + `f1_core.py` (sha256 `{SHA['core']}`), `f1_run.py`
(`{SHA['run']}`) and `partitions.json` (`{SHA['parts']}`) below.
Order: setup → D0 → gates (G-const, G-vec, G-mlp, GG0) → smoke (2-epoch end-to-end + speed, projection) →
{'full run (each job written as soon as it ends) → ' if run_full else ''}`/kaggle/working/f1_repcv/p{p}/`.
**Nothing printed here is a result** until verification (`src/f1_aggregate.py`). Do not edit;
*Save Version → Save & Run All (Commit)*.
"""),
        code(f"""
# SETUP: packages + repository at the pinned commit (read only)
import os, sys, subprocess, time, json, hashlib
T_NB = time.time()
os.environ["F1_T0"] = str(T_NB)
NOTEBOOK, P, RUN_FULL = "{name}", {p}, {run_full}
REPO_COMMIT = "{COMMIT}"
TEST = bool(os.environ.get("F1_TEST_REPO"))                      # synthetic test in the build container only
WORK = os.environ.get("F1_TEST_WORK", "/kaggle/working")
INPUT = os.environ.get("F1_TEST_INPUT", "/kaggle/input")
SRC = WORK + "/f1_src"
os.makedirs(SRC, exist_ok=True)
if TEST:
    REPO = os.environ["F1_TEST_REPO"]
else:
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
print("repository", REPO, f"({{time.time()-T_NB:.0f}}s)")
"""),
        code("%%writefile {SRC}/f1_core.py\n" + CORE),
        code("%%writefile {SRC}/f1_run.py\n" + RUN),
        code("%%writefile {SRC}/partitions.json\n" + PARTS),
        code(f"""
# START: sha check of the embedded files, imports, run metadata, data gate D0 (hard stop on wrong data)
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
for fn, want in (("f1_core.py", "{SHA['core']}"), ("f1_run.py", "{SHA['run']}"), ("partitions.json", "{SHA['parts']}")):
    assert sha(f"{{SRC}}/{{fn}}") == want, f"{{fn}}: sha {{sha(f'{{SRC}}/{{fn}}')}} != {{want}} (cell edited?)"
os.environ.update(THESIS_REPO=REPO, F1_PARTITIONS=SRC + "/partitions.json", F1_OUT=WORK + "/f1_repcv", F1_INPUT=INPUT)
sys.path.insert(0, SRC)
import pandas as pd, torch
import f1_run as R
print("torch", torch.__version__, "| GPUs:", torch.cuda.device_count(), "| CPU cores:", os.cpu_count())
try:
    R.run_meta(NOTEBOOK, P)
    R.setup(P, INPUT)
except SystemExit as e:
    raise RuntimeError(f"STOPPED: {{e}}") from None
"""),
        code("""
# GATES (CPU, about 10 min): G-const, G-vec (training loop = PyG loop), G-mlp (= model comparison loop), GG0 (chain on
# partition 0 with the committed GAE checkpoints = results/v9_x3 exactly)
try:
    R.gates(P)
except SystemExit as e:
    raise RuntimeError(f"STOPPED: {e}") from None
print("GATES PASS")
"""),
        code("""
# SMOKE (always): one 2-epoch end-to-end job per model + speed of the parallel workers -> projection.json
try:
    proj = R.smoke(P)
except SystemExit as e:
    raise RuntimeError(f"STOPPED: {e}") from None
print(json.dumps({k: proj[k] for k in ("mode", "workers", "devices", "ms_per_step", "projected_wall_h", "fits")}, indent=1))
"""),
    ]
    if run_full:
        cells.append(code("""
# FULL RUN: 8 jobs (GAE + MLP-AE x 4 folds) on the parallel workers; each job written as soon as it ends
t_full = time.time()
try:
    R.import_previous(P, INPUT)
    R.full(P)
except SystemExit as e:
    raise RuntimeError(f"STOPPED: {e}") from None
print(f"FULL done in {(time.time()-t_full)/3600:.2f} h")
"""))
    cells.append(code("""
# END: merge, gates, jobs, unverified summary, measured runtime
n_done = R.merge(P)
print(json.dumps(R.GATES, indent=1, default=str))
jf = R.OUT / f"p{P}" / "jobs.json"
print(jf.read_text() if jf.exists() else "(no full run)")
R.summary(P)
mf = R.OUT / f"p{P}" / "run_meta.json"
meta = json.loads(mf.read_text())
meta.update(notebook_runtime_h=round((time.time() - T_NB) / 3600, 3), finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"),
            jobs_done=n_done)
mf.write_text(json.dumps(meta, indent=1))
print(f"MEASURED notebook runtime: {meta['notebook_runtime_h']} h; jobs done: {n_done} of 8")
print(sorted(os.listdir(R.OUT / f"p{P}")))
"""))
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                       "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / f"{name}.ipynb").write_text(json.dumps(nb, indent=1))
    return OUTDIR / f"{name}.ipynb"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    a = ap.parse_args()
    built = [build("F1_SMOKE", 1, False, ACCOUNTS[0])]
    for i, p in enumerate(a.parts):
        built.append(build(f"F1_p{p}", p, True, ACCOUNTS[i % 4]))
    print("built", [b.name for b in built], SHA)


if __name__ == "__main__":
    main()
