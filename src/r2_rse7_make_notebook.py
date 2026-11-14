#!/usr/bin/env python
"""r2_rse7_make_notebook.py -- builds the Kaggle notebooks RS_E7_<part> of gate RS-E7 (fix B of RP_SERIES;
docs/FUTURE_RESEARCH_PLAN.md §12 14/11 18:30 (c) and D27-F) from src/r2_rse7.py and src/r2_e7exact.py (embedded verbatim
with %%writefile; sha256 checked in the notebook). The repository is cloned at a pinned commit (40-hex hash) holding the
committed path-2 scores (results/r2/r1_system/rp/rp2/scores) and src/e7_ensemble_cpd.py. The 23 cases are split into
--parts notebooks by LPT on the cost proxy sum over files of n^2 (x 4 seeds), so that the parts end at about the same time.
  python src/r2_rse7_make_notebook.py --run <commit> [--parts 2]   -> notebooks/r2/RS_E7_A.ipynb, RS_E7_B.ipynb, ...
Test mode (synthetic data, build container only): R2_TEST_REPO / R2_TEST_INPUT / R2_TEST_WORK."""
import argparse
import hashlib
import json
import os
import re
import string
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUTDIR = Path(os.environ.get("R2_NB_OUTDIR", ROOT / "notebooks" / "r2"))
CORE = (ROOT / "src" / "r2_rse7.py").read_text()
EXACT = (ROOT / "src" / "r2_e7exact.py").read_text()
SHA_CORE = hashlib.sha256(CORE.encode()).hexdigest()[:16]
SHA_EXACT = hashlib.sha256(EXACT.encode()).hexdigest()[:16]
E7_SHA = hashlib.sha256((ROOT / "src" / "e7_ensemble_cpd.py").read_bytes()).hexdigest()[:16]
PKGS = '"ruptures==1.1.10"'


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.strip("\n").splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": t.strip("\n").splitlines(keepends=True)}


def split(parts):
    import r2_rse7 as RS
    cost = {c: RS.case_cost(c) for c in RS.CASES}
    bins = [[0.0, []] for _ in range(parts)]
    for c in sorted(cost, key=lambda k: (-cost[k], k)):
        b = min(bins, key=lambda v: v[0])
        b[0] += cost[c]; b[1].append(c)
    return [(string.ascii_uppercase[i], sorted(b[1], key=RS.CASES.index), b[0]) for i, b in enumerate(bins)], cost


def build(commit, part, cases, share):
    name = f"RS_E7_{part}"
    cells = [md(f"""
# {name} — gate RS-E7 (fix B of RP_SERIES): exact E7 D2 segmentation = ruptures 1.1.10, part {part}

**Plan:** `docs/FUTURE_RESEARCH_PLAN.md` §12 14/11 18:30 (c) and D27-F. **Question:** does `src/r2_e7exact.py` give the
same breakpoints as `ruptures.Pelt(model="l2", min_size=2, jump=1)` inside E7's D2 segmenter, on every file of the
committed path-2 scores? **Rule (fixed before the run):** PASS iff every breakpoint list is equal, for every file, the 4
seeds and the 3 penalties of E7; any difference STOPs. **This part:** {len(cases)} cases ({share:.0%} of the cost proxy):
{", ".join(cases)}. The other part(s) run the rest; the merge in the chat container gives RS-E7.
**Accelerator:** None (CPU). **Internet:** ON (pip ruptures, git clone). **Inputs:** none (the scores are in the
repository). **Output:** `/kaggle/working/r2/r1_system/rp_series/rse7/{part}/` (→ `results/r2/r1_system/rp_series/rse7/{part}/`),
< 5 MB. **Runtime:** see the chat (computed from the container measurement; ruptures is the slow side by design).
Code: `github.com/Nhanvas/Thesis` at `{commit[:7]}` (read only) + `r2_e7exact.py` (sha256 `{SHA_EXACT}`) and `r2_rse7.py`
(sha256 `{SHA_CORE}`) below. Resumable: if the session ends, attach this notebook's output and run again.
**Nothing printed here is a research result.** Do not edit; *Save Version → Save & Run All (Commit)*.
"""), code(f"""
# SETUP: packages + repository at the pinned commit (read only)
import os, sys, subprocess, time, json, hashlib, shutil
T_NB = time.time()
os.environ["R2_T0"] = str(T_NB)
NOTEBOOK, REPO_COMMIT, PART = "{name}", "{commit}", "{part}"
CASES = {json.dumps(cases)}
TEST = bool(os.environ.get("R2_TEST_REPO"))                      # synthetic test in the build container only
WORK = os.environ.get("R2_TEST_WORK", "/kaggle/working")
INPUT = os.environ.get("R2_TEST_INPUT", "/kaggle/input")
SRC = (os.environ.get("R2_TEST_SCRATCH", "/tmp/r2")) + "/src_rse7"
os.makedirs(SRC, exist_ok=True)
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
if TEST:
    REPO = os.environ["R2_TEST_REPO"]
else:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", {PKGS}])
    REPO = "/tmp/Thesis"
    if not os.path.exists(REPO + "/src/e7_ensemble_cpd.py"):
        r = subprocess.run(f"git init -q {{REPO}} && cd {{REPO}} && git remote add origin https://github.com/Nhanvas/Thesis.git "
                           f"&& git fetch -q --depth 1 origin {{REPO_COMMIT}} && git checkout -q FETCH_HEAD", shell=True)
        if r.returncode != 0:
            subprocess.check_call(f"rm -rf {{REPO}} && git clone -q https://github.com/Nhanvas/Thesis.git {{REPO}} "
                                  f"&& cd {{REPO}} && git checkout -q {{REPO_COMMIT}}", shell=True)
    head = subprocess.check_output(["git", "-C", REPO, "rev-parse", "HEAD"]).decode().strip()
    assert head == REPO_COMMIT, f"wrong commit {{head}}"
got = hashlib.sha256(open(f"{{REPO}}/src/e7_ensemble_cpd.py", "rb").read()).hexdigest()[:16]
assert TEST or got == "{E7_SHA}", f"e7_ensemble_cpd.py sha {{got}} != {E7_SHA}"
print("repository", REPO, f"({{time.time()-T_NB:.0f}}s)")
"""), code("%%writefile {SRC}/r2_e7exact.py\n" + EXACT), code("%%writefile {SRC}/r2_rse7.py\n" + CORE), code(f"""
# START: sha checks of the embedded files, imports, run metadata
for f, want in (("r2_e7exact.py", "{SHA_EXACT}"), ("r2_rse7.py", "{SHA_CORE}")):
    sha = hashlib.sha256(open(f"{{SRC}}/{{f}}", "rb").read()).hexdigest()[:16]
    assert sha == want, f"{{f}}: sha {{sha}} != {{want}} (cell edited?)"
os.environ.update(THESIS_REPO=REPO, R2_WORK=WORK, R2_INPUT=INPUT)
sys.path[:0] = [SRC]
import r2_rse7 as RS
W = max(1, min(4, os.cpu_count() or 1))
print("CPU cores:", os.cpu_count(), "| workers:", W, "| cases:", CASES)
META = RS.run_meta(PART, NOTEBOOK, REPO_COMMIT)
"""), code("""
# RUN: G-code, G-in, the jobs (case x seed; ruptures and the exact implementation on every Pelt call), RS-E7 of this part
ERR = None
try:
    REC = RS.run(PART, CASES, W)
except SystemExit as e:
    ERR = str(e)
"""), code("""
# END: measured runtime, outputs; then STOPPED if a gate did not pass (the output is still written)
meta = RS.finish_meta(PART)
if (RS.out_root(PART) / "SUMMARY.md").exists():
    print(open(RS.out_root(PART) / "SUMMARY.md").read())
print(f"MEASURED notebook runtime: {meta['runtime_h']} h")
for p in sorted(RS.out_root(PART).rglob("*")):
    if p.is_file() and "jobs" not in p.parts:
        print(p.relative_to(RS.WORK), p.stat().st_size)
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
    ap.add_argument("--run", metavar="COMMIT", required=True, help="40-hex commit holding rp2/scores and e7_ensemble_cpd.py")
    ap.add_argument("--parts", type=int, default=2)
    a = ap.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", a.run):
        ap.error("--run takes a 40-hex commit hash, never a tag")
    sp, cost = split(a.parts)
    tot = sum(cost.values())
    for part, cases, c in sp:
        print("built", build(a.run, part, cases, c / tot).name, f"cost share {c / tot:.3f}", cases)
    print("r2_rse7 sha", SHA_CORE, "r2_e7exact sha", SHA_EXACT)
