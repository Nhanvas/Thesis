#!/usr/bin/env python
"""r2_rb1_make_notebook.py -- builds notebooks/r2/RB1_DATA.ipynb (stage RB, step RB1; plan §7b, §12 12/11 22:15) from
src/r2_rb1.py (embedded verbatim with %%writefile; sha256 checked in the notebook). The repository is cloned at the
pinned commit COMMIT for the record code (byte-checked by gate G-code), r2_core, r2_rb and the committed R0 / R1_SMOKE /
RB0b outputs the gates read.
  python src/r2_rb1_make_notebook.py
Test mode (synthetic data, build container only): R2_TEST_REPO / R2_TEST_INPUT / R2_TEST_WORK / R2_TEST_SCRATCH."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "360da561fa36a1d909c23324d0059e26ef2fb8f1"        # main after D22-F (RB0b output and reading)
OUTDIR = ROOT / "notebooks" / "r2"
CODE = (ROOT / "src" / "r2_rb1.py").read_text()
SHA = hashlib.sha256(CODE.encode()).hexdigest()[:16]
RAW = "bonesclarke26/combined-siena-scalp-and-chb-mit-eeg-datasets"
PKGS = '"mne==1.12.1", "torch_geometric==2.7.0", "ruptures==1.1.10", "timescoring==0.0.7"'     # = R0's


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.strip("\n").splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": t.strip("\n").splitlines(keepends=True)}


def build():
    name = "RB1_DATA"
    cells = [
        md(f"""
# RB1_DATA — research track, stage RB, step RB1 (chb12 rebuilt with chb12_27–29)

**Plan:** `docs/FUTURE_RESEARCH_PLAN.md` §7b and §12 row 12/11 22:15. **Does:** chb12 rebuilt on all 24 of its files with
the three referential files converted to the 18 bipolar derivations exactly as SzCORE does (`src/r2_rb.py`); gates
G-code, mode, G-raw, G-R0, Job A (= R0's chb12), Job B (labels, counts), G-clip (= RB0b), G-copy; descriptive diff and
clipping tables; dataset folder `thesis-r2-chbmit-features-rb`.
**Accelerator:** None (CPU). **Internet:** ON (pip + git clone only). **Inputs:** `{RAW}` and
`thesis-r2-chbmit-features` (nhn2mm). **Outputs:** `thesis-r2-chbmit-features-rb/` + `r2/r0_data/chb12_ref/rb1/`.
**Runtime:** ≈ 0.5 h (computed from R0's measured 1,222 s for chb12's 20.7 h).
Code: `github.com/Nhanvas/Thesis` at `{COMMIT[:7]}` (record code, read only) + `r2_rb1.py` below (sha256 `{SHA}`).
Gates STOP the notebook (the cell raises `STOPPED: ...`); the dataset folder is written only after every gate passed.
Do not edit; *Save Version → Save & Run All (Commit)*.
"""),
        code(f"""
# SETUP: packages + repository at the pinned commit (read only)
import os, sys, subprocess, time, json, hashlib
T_NB = time.time()
os.environ["R2_T0"] = str(T_NB)
NOTEBOOK, REPO_COMMIT = "{name}", "{COMMIT}"
TEST = bool(os.environ.get("R2_TEST_REPO"))                      # synthetic test in the build container only
WORK = os.environ.get("R2_TEST_WORK", "/kaggle/working")
INPUT = os.environ.get("R2_TEST_INPUT", "/kaggle/input")
SCRATCH = os.environ.get("R2_TEST_SCRATCH", "/tmp/r2")
SRC = SCRATCH + "/src"
os.makedirs(SRC, exist_ok=True)
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
if TEST:
    REPO = os.environ["R2_TEST_REPO"]
else:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", {PKGS}])
    REPO = "/tmp/Thesis"
    if not os.path.exists(REPO + "/src/r2_rb.py"):
        r = subprocess.run(f"git init -q {{REPO}} && cd {{REPO}} && git remote add origin https://github.com/Nhanvas/Thesis.git "
                           f"&& git fetch -q --depth 1 origin {{REPO_COMMIT}} && git checkout -q FETCH_HEAD", shell=True)
        if r.returncode != 0:
            subprocess.check_call(f"rm -rf {{REPO}} && git clone -q https://github.com/Nhanvas/Thesis.git {{REPO}} "
                                  f"&& cd {{REPO}} && git checkout -q {{REPO_COMMIT}}", shell=True)
    head = subprocess.check_output(["git", "-C", REPO, "rev-parse", "HEAD"]).decode().strip()
    assert head == REPO_COMMIT, f"wrong commit {{head}}"
print("repository", REPO, f"({{time.time()-T_NB:.0f}}s)")
"""),
        code(f"%%writefile {{SRC}}/r2_rb1.py\n{CODE}"),
        code(f"""
# START: sha check of the embedded file, imports, run metadata, G-code, mode
sha = hashlib.sha256(open(f"{{SRC}}/r2_rb1.py", "rb").read()).hexdigest()[:16]
assert sha == "{SHA}", f"r2_rb1.py: sha {{sha}} != {SHA} (cell edited?)"
os.environ.update(THESIS_REPO=REPO, R2_WORK=WORK, R2_INPUT=INPUT, R2_SCRATCH=SCRATCH)
for p in (REPO + "/src", SRC):
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)
def stopped(e):
    raise RuntimeError(f"STOPPED: {{e}}") from None
import numpy as np, pandas as pd
import r2_rb1 as B
print("CPU cores:", os.cpu_count())
try:
    META = B.start(NOTEBOOK, REPO_COMMIT)
except SystemExit as e:
    stopped(e)
"""),
        code("""
# G-raw (24 chb12 EDFs + summary = PhysioNet), G-R0 (R0 dataset = pinned hashes), views
try:
    RAW_PATHS, EDFS = B.gate_raw()
    R0_PATHS, R0_INV = B.gate_r0()
    VIEWS = B.build_views(RAW_PATHS)
except SystemExit as e:
    stopped(e)
"""),
        code("""
# Job A (wrapper + 21 bipolar files) and Job B (wrapper + 24 files) in parallel; gates A and B
try:
    DONE = B.run_jobs(VIEWS, workers=2)
    A = B.gate_A(DONE, R0_PATHS)
    BB = B.gate_B(DONE, EDFS, A)
except SystemExit as e:
    stopped(e)
"""),
        code("""
# clipping of the three referential files per 4 s window; G-clip (sums = RB0b's committed tables); diff report
try:
    CLIP = B.clipping(RAW_PATHS, BB)
    DIFF = B.diff_report(DONE, A, BB)
except SystemExit as e:
    stopped(e)
print(json.dumps({k: DIFF[k] for k in ("files_added", "seizures", "ictal_windows", "clean_windows", "flag5sd_windows")}))
print(json.dumps({k: CLIP[k] for k in ("seizures", "seizures_with_clipped_samples", "clean_windows_with_clipped_samples",
                                       "by_class")}))
"""),
        code("""
# dataset folder thesis-r2-chbmit-features-rb (23 cases copied with hash check + chb12 new) and the new pin
try:
    PIN_NEW = B.build_dataset(DONE, R0_PATHS, R0_INV)
except SystemExit as e:
    stopped(e)
B.summary_md(DIFF, CLIP)
"""),
        code("""
# END: measured runtime and the list of outputs
import shutil
shutil.rmtree(B.R0.SCRATCH / "rb1_build", ignore_errors=True)
meta = B.R0.finish_meta()
ZIP = shutil.make_archive(str(B.R0.WORK / "rb1_results"), "zip", root_dir=str(B.out_dir().parent), base_dir="rb1")
print("small results archive for git:", ZIP, f"{os.path.getsize(ZIP) / 1e6:.1f} MB")
print(f"MEASURED notebook runtime: {meta['runtime_h']} h | phases (s): {meta['phases_s']}")
for d in (B.out_dir(), B.DS_RB):
    print(d, "->", sorted(p.name for p in d.iterdir()))
print(open(B.out_dir() / "SUMMARY.md").read())
"""),
    ]
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                       "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    p = OUTDIR / f"{name}.ipynb"
    p.write_text(json.dumps(nb, indent=1))
    print(p, "r2_rb1 sha", SHA)
    return p


if __name__ == "__main__":
    build()
