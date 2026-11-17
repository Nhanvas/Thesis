#!/usr/bin/env python
"""fa16_repl_make_notebook.py -- builds the Kaggle notebook of the F-A1.6 replication (src/fa16_repl.py; plan §12 17/11
08:10, chat D30-F). src/fa16_repl.py is embedded verbatim (%%writefile; sha256 checked in the notebook). The repository is
cloned at a pinned commit (40-hex) that holds the record code and files it reads (src/f1_core.py, src/fa16_kmeans.py,
src/model_cmp_core.py, src/model_cmp_run.py, results/f1_repcv, results/fa16/run, results/v9_x3, results/model_cmp); the
notebook imports them from the clone and asserts their sha256. Notebook pin rule (plan §0, R205): the builder refuses a
commit whose copy of any of these modules differs from the local file, or whose fa16_repl.py (if present) differs from the
embedded one. One process, no pool workers.
  python src/fa16_repl_make_notebook.py --run <commit>   -> notebooks/fa16/FA16_REPL.ipynb
Test mode (synthetic world, build container only): FA16R_TEST_REPO / FA16R_TEST_INPUT / FA16R_TEST_WORK; --run 000...0."""
import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = Path(os.environ.get("FA16_NB_OUTDIR", ROOT / "notebooks" / "fa16"))
NAME = "FA16_REPL"
CORE = (ROOT / "src" / "fa16_repl.py").read_text()
CLONE = ("fa16_kmeans.py", "f1_core.py", "model_cmp_core.py", "model_cmp_run.py")
SHA = {n: hashlib.sha256((ROOT / "src" / n).read_bytes()).hexdigest()[:16] for n in ("fa16_repl.py",) + CLONE}
PKGS = '"torch_geometric==2.7.0", "ruptures==1.1.10", "timescoring==0.0.7"'


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.strip("\n").splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": t.strip("\n").splitlines(keepends=True)}


def build(commit):
    checks = ",\n".join(f'    (f"{{REPO}}/src/{n}", "{SHA[n]}")' for n in CLONE)
    cells = [md(f"""
# {NAME} — F-A1.6 replication: K-means over the five random patient partitions (Track F, chat D30-F)

**Plan:** `docs/FUTURE_RESEARCH_PLAN.md` §12 17/11 08:10 (author 17/11 07:40). Partitions 1–5 of `results/f1_repcv/partitions.json`
(the F1 record). **Gates before any K-means row:** D0, G-parts, G-base (the F1 GAE checkpoints of p1–p5 reproduce the record
rows), G-kmD (the K-means fits = FA16_KMEANS's), G-km0 (partition 0 = FA16_KMEANS's rows); then `km` and `km_u` on p1–p5, G-done.
**Accelerator:** None (CPU). **Internet:** ON (pip, git clone) → a verified account.
**Inputs:** `v9-x3-fold1` and `v9-x3-fold3` — nothing else. **Output:** `/kaggle/working/fa16_repl/` (→ `results/fa16/repl_run`),
< 20 MB. **Runtime:** about 1.5–2 h (computed estimate; measured in `run_meta.json`).
Code: `github.com/Nhanvas/Thesis` at `{commit[:7]}` (read only: {", ".join(f"`{n}` `{SHA[n]}`" for n in CLONE)}) +
`fa16_repl.py` (sha256 `{SHA['fa16_repl.py']}`) below. **Nothing printed here is a research result.** Do not edit;
*Save Version → Save & Run All (Commit)*.
"""), code(f"""
# SETUP: packages + repository at the pinned commit (read only)
import os, sys, subprocess, time, json, hashlib
T_NB = time.time()
NOTEBOOK, REPO_COMMIT = "{NAME}", "{commit}"
TEST = bool(os.environ.get("FA16R_TEST_REPO"))                   # synthetic test in the build container only
WORK = os.environ.get("FA16R_TEST_WORK", "/kaggle/working")
INPUT = os.environ.get("FA16R_TEST_INPUT", "/kaggle/input")
SRC = WORK + "/fa16r_src"
os.makedirs(SRC, exist_ok=True)
if TEST:
    REPO = os.environ["FA16R_TEST_REPO"]
else:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", {PKGS}])
    REPO = "/tmp/Thesis"
    if not os.path.exists(REPO + "/src/model_cmp_core.py"):
        r = subprocess.run(f"git init -q {{REPO}} && cd {{REPO}} && git remote add origin https://github.com/Nhanvas/Thesis.git "
                           f"&& git fetch -q --depth 1 origin {{REPO_COMMIT}} && git checkout -q FETCH_HEAD", shell=True)
        if r.returncode != 0:
            subprocess.check_call(f"rm -rf {{REPO}} && git clone -q https://github.com/Nhanvas/Thesis.git {{REPO}} "
                                  f"&& cd {{REPO}} && git checkout -q {{REPO_COMMIT}}", shell=True)
    head = subprocess.check_output(["git", "-C", REPO, "rev-parse", "HEAD"]).decode().strip()
    assert head == REPO_COMMIT, f"wrong commit {{head}}"
print("repository", REPO, f"({{time.time()-T_NB:.0f}}s)")
"""), code("%%writefile {SRC}/fa16_repl.py\n" + CORE), code(f"""
# START: sha checks (embedded file; record code in the clone), imports
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
for path, want in ((f"{{SRC}}/fa16_repl.py", "{SHA['fa16_repl.py']}"),
{checks}):
    assert sha(path) == want, f"{{path}}: sha {{sha(path)}} != {{want}} (cell edited or wrong commit?)"
if os.path.exists(f"{{REPO}}/src/fa16_repl.py"):
    assert sha(f"{{REPO}}/src/fa16_repl.py") == "{SHA['fa16_repl.py']}", "the clone holds another fa16_repl.py"
os.environ.update(THESIS_REPO=REPO, FA16R_OUT=WORK + "/fa16_repl")
sys.path[:0] = [SRC, REPO + "/src"]
import fa16_repl as M
import model_cmp_core as C
import fa16_kmeans as K
assert M.__file__ == f"{{SRC}}/fa16_repl.py" and C.__file__ == f"{{REPO}}/src/model_cmp_core.py" \\
    and K.__file__ == f"{{REPO}}/src/fa16_kmeans.py", (M.__file__, C.__file__, K.__file__)
print("CPU cores:", os.cpu_count(), "| fa16_repl", M.CODE_SHA)
"""), code("""
# RUN: D0, G-parts, G-base (GAE p1-p5), K-means fits + G-kmD, G-km0, km / km_u on p1-p5, G-done
ERR = None
try:
    M.main(NOTEBOOK, REPO_COMMIT, INPUT)
except SystemExit as e:
    ERR = str(e)
"""), code("""
# END: gates, jobs, measured runtime, outputs
for f in ("gates.json", "run_meta.json"):
    p = M.OUT / f
    if p.exists():
        print(f, open(p).read()[:4000])
for p in sorted(M.OUT.rglob("*")):
    if p.is_file():
        print(p.relative_to(WORK), p.stat().st_size)
print(f"MEASURED notebook runtime: {(time.time() - T_NB) / 3600:.3f} h")
if ERR:
    raise RuntimeError(f"STOPPED: {ERR}")
""")]
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                       "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / f"{NAME}.ipynb").write_text(json.dumps(nb, indent=1))
    return OUTDIR / f"{NAME}.ipynb"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", metavar="COMMIT", required=True, help="40-hex commit holding the record code and files")
    a = ap.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", a.run):
        ap.error("--run takes a 40-hex commit hash, never a tag")
    if a.run != "0" * 40:                       # plan §0 notebook rule (R205)
        for n in CLONE + ("fa16_repl.py",):
            p = subprocess.run(["git", "-C", str(ROOT), "show", f"{a.run}:src/{n}"], capture_output=True)
            if p.returncode != 0:
                if n == "fa16_repl.py":
                    continue
                ap.error(f"src/{n} is not in commit {a.run[:7]}")
            if p.stdout != (ROOT / "src" / n).read_bytes():
                ap.error(f"src/{n} at {a.run[:7]} differs from the local file: pin a commit that holds this code")
        for rel in ("results/fa16/run/fa16/km_k.csv", "results/f1_repcv/raw/p5/jobs/gae_fold4/fit.json"):
            if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", f"{a.run}:{rel}"]).returncode != 0:
                ap.error(f"{rel} is not in commit {a.run[:7]}")
    print("built", build(a.run), SHA)
