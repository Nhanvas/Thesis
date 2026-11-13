#!/usr/bin/env python
"""r2_rb1c_make_notebook.py -- builds notebooks/r2/RB1C_SURVEY.ipynb (stage RB, step RB1c on Kaggle; plan §12 13/11
18:10). RB1c moved from the laptop to Kaggle CPU (author 13/11 17:56: the laptop's free memory cannot hold the run; long,
complex or memory-heavy verification runs go to Kaggle). The notebook clones the repository at COMMIT (r2_rb1c.py
with the chb24-summary fix and the resume cache, sha256 checked; the committed inventories, statistics and counts the
gates read), verifies every raw EDF against PhysioNet with R0's own `r2_core.inventory` (Kaggle copy first, PhysioNet
download for a missing or different file) into a view of symlinks, runs `src/r2_rb1c.py` on that view with 4
processes and archives its output folder.
  python src/r2_rb1c_make_notebook.py
Test (synthetic data, build container only): src/r2_rb1c_notebook_test.py (R2_TEST_REPO / _INPUT / _WORK / _SCRATCH)."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "e86adb5aab230a8ce0673da29ac988401cd5f1e6"        # main after the RB1c fix (D23F4)
OUTDIR = ROOT / "notebooks" / "r2"
RAW = "bonesclarke26/combined-siena-scalp-and-chb-mit-eeg-datasets"
PKGS = '"mne==1.12.1", "torch_geometric==2.7.0", "ruptures==1.1.10", "timescoring==0.0.7"'     # = R0's
SCRIPT_SHA = hashlib.sha256(
    subprocess.check_output(["git", "-C", str(ROOT), "show", f"{COMMIT}:src/r2_rb1c.py"])).hexdigest()[:16]


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.strip("\n").splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": t.strip("\n").splitlines(keepends=True)}


def build():
    name = "RB1C_SURVEY"
    cells = [
        md(f"""
# RB1C_SURVEY — research track, stage RB, step RB1c (robustness of the z-score statistic, every case)

**Plan:** `docs/FUTURE_RESEARCH_PLAN.md` §7b and §12 rows 13/11 09:30, 14:40, 18:10. **Does:** every CHB-MIT case (24;
chb12 with chb12_27–29 through the wrapper) and every Siena patient (14): the record statistic re-run with per-window
sums (gate: = the committed statistics), SD without windows holding clipped samples, MAD, IQR, concentration of the
statistic; CHB-MIT: 5-SD flags and clean windows under each scale (gate: = the committed counts). Descriptive.
**Accelerator:** None (CPU). **Internet:** ON (pip, git clone, PhysioNet SHA256SUMS and any missing file).
**Input:** `{RAW}` only. **Output:** `rb1c_results.zip` (folder `rb1c/`, a few MB).
**Runtime:** ≈ 2–2.5 h (computed: the laptop's measured 16.6 s per hour of EEG on 1 process, 1,124 h of EEG, 4
processes, + hashing ≈ 0.3 h).
Code: `github.com/Nhanvas/Thesis` at `{COMMIT[:7]}`; `src/r2_rb1c.py` sha256 `{SCRIPT_SHA}` (checked).
A gate failure stops the run; the END cell still archives what was written, then raises `STOPPED: ...`.
Do not edit; *Save Version → Save & Run All (Commit)*.
"""),
        code(f"""
# SETUP: packages + repository at the pinned commit (read only)
import os, sys, subprocess, time, json, hashlib, shutil
T_NB = time.time()
os.environ["R2_T0"] = str(T_NB)
NOTEBOOK, REPO_COMMIT = "{name}", "{COMMIT}"
TEST = bool(os.environ.get("R2_TEST_REPO"))                      # synthetic test in the build container only
WORK = os.environ.get("R2_TEST_WORK", "/kaggle/working")
INPUT = os.environ.get("R2_TEST_INPUT", "/kaggle/input")
SCRATCH = os.environ.get("R2_TEST_SCRATCH", "/tmp/r2")
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
if TEST:
    REPO = os.environ["R2_TEST_REPO"]
else:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", {PKGS}])
    REPO = "/tmp/Thesis"
    if not os.path.exists(REPO + "/src/r2_rb1c.py"):
        r = subprocess.run(f"git init -q {{REPO}} && cd {{REPO}} && git remote add origin https://github.com/Nhanvas/Thesis.git "
                           f"&& git fetch -q --depth 1 origin {{REPO_COMMIT}} && git checkout -q FETCH_HEAD", shell=True)
        if r.returncode != 0:
            subprocess.check_call(f"rm -rf {{REPO}} && git clone -q https://github.com/Nhanvas/Thesis.git {{REPO}} "
                                  f"&& cd {{REPO}} && git checkout -q {{REPO_COMMIT}}", shell=True)
    head = subprocess.check_output(["git", "-C", REPO, "rev-parse", "HEAD"]).decode().strip()
    assert head == REPO_COMMIT, f"wrong commit {{head}}"
sha = hashlib.sha256(open(REPO + "/src/r2_rb1c.py", "rb").read()).hexdigest()[:16]
assert sha == "{SCRIPT_SHA}", f"r2_rb1c.py sha {{sha}} != {SCRIPT_SHA}"
print("repository", REPO, f"({{time.time()-T_NB:.0f}}s)")
"""),
        code("""
# INVENTORY: every CHB-MIT and Siena file verified by sha256 against PhysioNet (R0's r2_core.inventory: Kaggle copy
# first, PhysioNet download for a missing / different file; STOP if a file cannot be verified) -> view of symlinks
os.environ.update(THESIS_REPO=REPO, R2_WORK=WORK, R2_INPUT=INPUT, R2_SCRATCH=SCRATCH)
sys.path.insert(0, REPO + "/src")
def stopped(e):
    raise RuntimeError(f"STOPPED: {e}") from None
import r2_core as R0
print("CPU cores:", os.cpu_count())
try:
    META = R0.run_meta("rb1c_kaggle_inventory", NOTEBOOK, REPO_COMMIT)
    INV, CASES, COMPLETE, _ = R0.inventory({"chbmit": None, "siena": None})
except SystemExit as e:
    stopped(e)
print(INV.source.value_counts().to_dict())
"""),
        code("""
# RUN: src/r2_rb1c.py on the verified view, 4 processes (spawn); its gates STOP it; output WORK/r2/r0_data/rb1c
OUT = os.path.join(WORK, "r2", "r0_data", "rb1c")
os.makedirs(OUT, exist_ok=True)
PROCS = max(1, min(4, os.cpu_count() or 1))
cmd = [sys.executable, REPO + "/src/r2_rb1c.py", "--chbmit-dir", str(COMPLETE / "chbmit"),
       "--siena-dir", str(COMPLETE / "siena"), "--out", OUT, "--procs", str(PROCS)]
if TEST and os.environ.get("R2_TEST_RB1C_CASES"):                # the synthetic world holds 5 cases only
    cmd += ["--cases", os.environ["R2_TEST_RB1C_CASES"]]
t = time.time()
with open(os.path.join(OUT, "run.log"), "w") as logf:
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=REPO)
    for line in p.stdout:
        logf.write(line)
        if "RuntimeWarning" not in line and "read_raw_edf" not in line and not line.startswith("  "):
            print(line, end="")
    RC = p.wait()
R0.STATE["phases"]["rb1c"] = round(time.time() - t, 1)
print("r2_rb1c exit code", RC, f"({time.time() - t:.0f} s)")
"""),
        code("""
# END: provenance (Kaggle inventory, run metadata), archive, measured runtime; STOP after archiving if a gate failed
prov = os.path.join(OUT, "kaggle_inventory")
os.makedirs(prov, exist_ok=True)
meta = R0.finish_meta(dict(rb1c_exit_code=RC, procs=PROCS))
for f in sorted(R0.out_dir().iterdir()):
    shutil.copy(f, prov)
shutil.rmtree(os.path.join(OUT, "_cache"), ignore_errors=True)    # resume cache: not part of the results
ZIP = shutil.make_archive(os.path.join(WORK, "rb1c_results"), "zip", root_dir=os.path.dirname(OUT), base_dir="rb1c")
print("results archive:", ZIP, f"{os.path.getsize(ZIP) / 1e6:.1f} MB")
print(f"MEASURED notebook runtime: {meta['runtime_h']} h | phases (s): {meta['phases_s']}")
print(sorted(os.listdir(OUT)))
if os.path.exists(os.path.join(OUT, "SUMMARY.md")):
    print(open(os.path.join(OUT, "SUMMARY.md")).read())
if RC != 0:
    stopped(f"r2_rb1c exit code {RC}; see rb1c/run.log and rb1c/rb1c.json (archived)")
"""),
    ]
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                       "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    p = OUTDIR / f"{name}.ipynb"
    p.write_text(json.dumps(nb, indent=1))
    print("written", p, "script sha", SCRIPT_SHA)
    return p


if __name__ == "__main__":
    build()
