#!/usr/bin/env python
"""r4_f5a_make_notebook.py -- builds the Kaggle notebook F5A_V5 (F5a offset diagnosis on V5; Track F, chat D36-F;
design results/r4_f5a/DESIGN_F5A.md). Notebook pin rule (plan §0, board R205): the notebook clones the repository at the
given ref and imports every module FROM THE CLONE; before anything runs it asserts the sha256 of each listed module
against the values baked in here (the local files), so a run can only execute the reviewed code; pool workers report
their sha256 (gate G-worker-sha). Rebuild after any change to a listed file.
  python src/r4_f5a_make_notebook.py [--ref main|<40-hex commit>]   -> notebooks/r4/F5A_V5.ipynb
Test mode (synthetic world, build container only): F5A_TEST_REPO / F5A_TEST_INPUT / F5A_TEST_WORK / F5A_TEST_SCRATCH."""
import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = Path(os.environ.get("F5A_NB_OUTDIR", ROOT / "notebooks" / "r4"))
FILES = ["r4_f5a.py", "r2_r1.py", "r2_core.py", "e16_recording_baseline.py", "e17b_latent_family.py", "p3c_freeze.py",
         "p3_levers.py", "p2_scalars.py", "e22_test_oneshot.py", "e23_test_look7.py", "x1_external.py",
         "p2_dump_seeds23.py", "e18_cpd_localizer.py", "e10_kernel_cpd.py"]
PKGS = '"torch_geometric==2.7.0", "ruptures==1.1.10", "timescoring==0.0.7"'


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.strip("\n").splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": t.strip("\n").splitlines(keepends=True)}


def build(ref):
    name = "F5A_V5"
    sha = {n: hashlib.sha256((ROOT / "src" / n).read_bytes()).hexdigest()[:16] for n in FILES}
    cells = [md(f"""
# {name} — F5a offset verification and diagnosis on the V5 model (Track F, chat D36-F)

**Design:** `results/r4_f5a/DESIGN_F5A.md` (approved 21/11/2026 02:37). Inference only, the four committed V5
checkpoints; no training. **Runs a SMOKE first** (chb01, chb03, chb24: R1.0 / GE rows and the extraction, measured) and
STOPs before the full run if anything differs from the V5 record. **Accelerator:** None (CPU). **Internet:** ON (pip,
git clone). **Inputs (Add Input):** `v9-x3-fold1`, `v9-x3-fold3`, `thesis-r2-external-features`.
**Output:** `/kaggle/working/r4/f5a_v5` (→ `results/r4_f5a/v5`). **Runtime:** ≈ 0.3–0.6 h (computed; the smoke writes
`projection.json`). Code: `github.com/Nhanvas/Thesis` ref `{ref}`; every module's sha256 is asserted below.
**Nothing printed here is a research result.** Do not edit; *Save Version → Save & Run All (Commit)*.
"""), code(f"""
# SETUP: packages + repository (read only)
import os, sys, subprocess, time, json, hashlib
T_NB = time.time()
NOTEBOOK, REPO_REF = "{name}", "{ref}"
TEST = bool(os.environ.get("F5A_TEST_REPO"))                     # synthetic test in the build container only
WORK = os.environ.get("F5A_TEST_WORK", "/kaggle/working")
INPUT = os.environ.get("F5A_TEST_INPUT", "/kaggle/input")
SCRATCH = os.environ.get("F5A_TEST_SCRATCH", "/tmp/r2")
if TEST:
    REPO = os.environ["F5A_TEST_REPO"]; HEAD = "test"
else:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", {PKGS}])
    REPO = "/tmp/Thesis"
    if not os.path.exists(REPO + "/src/r4_f5a.py"):
        subprocess.check_call(f"rm -rf {{REPO}} && git clone -q https://github.com/Nhanvas/Thesis.git {{REPO}} "
                              f"&& cd {{REPO}} && git checkout -q {{REPO_REF}}", shell=True)
    HEAD = subprocess.check_output(["git", "-C", REPO, "rev-parse", "HEAD"]).decode().strip()
print("repository", REPO, HEAD, f"({{time.time()-T_NB:.0f}}s)")
"""), code(f"""
# START: sha256 of every module (the reviewed code only), environment, imports
WANT = {json.dumps(sha)}
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
bad = {{n: sha(f"{{REPO}}/src/{{n}}") for n in WANT if sha(f"{{REPO}}/src/{{n}}") != WANT[n]}}
assert not bad, f"modules differ from the reviewed code (rebuild the notebook or pin the right commit): {{bad}}"
os.environ.update(THESIS_REPO=REPO, R2_WORK=WORK, R2_INPUT=INPUT, R2_SCRATCH=SCRATCH, OMP_NUM_THREADS="1",
                  OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
if TEST:
    os.environ["R2_TEST"] = "1"
sys.path[:0] = [REPO + "/src"]
import r4_f5a as M
assert M.__file__ == f"{{REPO}}/src/r4_f5a.py", M.__file__
print("CPU cores:", os.cpu_count(), "| r4_f5a", M.CODE_SHA)
"""), code("""
# RUN: G-self, G-data, SMOKE (R1.0 / GE rows, extraction gates, projection), then the full run
ERR = None
try:
    M.main(NOTEBOOK, HEAD, workers=int(os.environ.get("F5A_WORKERS", "0")) or None)
except SystemExit as e:
    ERR = str(e)
"""), code("""
# END: gates, projection, outputs, measured runtime
OUT = os.path.join(WORK, "r4", "f5a_v5")
for f in ("gates.json", "smoke/gates.json", "projection.json", "run_meta.json"):
    p = os.path.join(OUT, f)
    if os.path.exists(p):
        print("=====", f); print(open(p).read()[:4000])
for root, _, fs in os.walk(OUT):
    for f in sorted(fs):
        p = os.path.join(root, f); print(os.path.relpath(p, WORK), os.path.getsize(p))
print(f"MEASURED notebook runtime: {(time.time() - T_NB) / 3600:.3f} h")
if ERR:
    raise RuntimeError(f"STOPPED: {ERR}")
""")]
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                       "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    p = OUTDIR / f"{name}.ipynb"
    p.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("written", p, "ref", ref, sha)
    return p


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="main")
    build(ap.parse_args().ref)
