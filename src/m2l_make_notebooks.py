#!/usr/bin/env python
"""
m2l_make_notebooks.py -- Kaggle notebooks of milestone M2 stream L (chat F2-03; design results/m2l/DESIGN_L2.md):
  M2L_L2_REC      development, scale R (account nhn2mm)
  M2L_L2_ROB      development, scale B (account nhannguyen26)
  M2L_L3_SHORT_A  development segments of 5 and 10 min, chosen arm (nhn2mm)
  M2L_L3_SHORT_B  development segments of 20 and 30 min, chosen arm (nhannguyen26)
  M2L_L3_EVAL     test, chb24, Siena, chosen arm and minimum length (nhn2mm)
Each notebook clones github.com/Nhanvas/Thesis at --ref, asserts the sha256 of every module it runs, then calls
src/m2l_run.py. Test mode (synthetic world, build container only): EUR_TEST_REPO / EUR_TEST_INPUT / EUR_TEST_WORK /
EUR_TEST_SCRATCH.
  python src/m2l_make_notebooks.py [--ref main|<40-hex commit>] [--only L2|L3SHORT|L3EVAL]  -> notebooks/m2l/*.ipynb
"""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = Path(os.environ.get("M2L_NB_OUTDIR", ROOT / "notebooks" / "m2l"))
FILES = ["m2l_core.py", "m2l_run.py", "eur_abl.py", "r2_r1.py", "r2_core.py", "e16_recording_baseline.py",
         "e17b_latent_family.py", "p3c_freeze.py", "p3_levers.py", "p2_scalars.py", "e22_test_oneshot.py",
         "e23_test_look7.py", "x1_external.py", "p2_dump_seeds23.py", "e18_cpd_localizer.py", "e10_kernel_cpd.py",
         "dataprep/preprocessing.py", "continuous_eval.py", "c1b_build_trainset.py", "evaluation_protocol.py"]
PKGS = '"mne==1.12.1", "torch_geometric==2.7.0", "ruptures==1.1.10", "timescoring==0.0.7"'   # = EUR_9A
RAW = "combined-siena-scalp-and-chb-mit-eeg-datasets"
SPEC = {
    "M2L_L2_REC": dict(env=dict(M2L_MODE="L2", M2L_S="R"), tag="l2_rec", account="nhn2mm",
                       inputs=[RAW, "v9-x3-fold1", "v9-x3-fold3"], runtime="≈ 3–3.5 h (computed; the smoke projects)",
                       what="the 15 development patients with the **record** z-score scale (mean / SD of each recording): "
                            "arms R-LW-F, R-LW-N, R-MCD-F, R-MCD-N (+ R-*-FX descriptive)"),
    "M2L_L2_ROB": dict(env=dict(M2L_MODE="L2", M2L_S="B"), tag="l2_rob", account="nhannguyen26",
                       inputs=[RAW, "v9-x3-fold1", "v9-x3-fold3"], runtime="≈ 3–3.5 h (computed; the smoke projects)",
                       what="the 15 development patients with the **robust** z-score scale (median, IQR / 1.349 × c_ch of "
                            "each recording): arms B-LW-F, B-LW-N, B-MCD-F, B-MCD-N (+ B-*-FX descriptive)"),
    "M2L_L3_SHORT_A": dict(env=dict(M2L_MODE="L3SHORT", M2L_SEGS="5,10", M2L_TAG="l3short_a"), tag="l3short_a",
                           account="nhn2mm", inputs=[RAW, "v9-x3-fold1", "v9-x3-fold3"], runtime="≈ 4.5–5 h (computed from L2's measured job times; PROJ stops above 10.5 h)",
                           what="development recordings cut into segments of **5 and 10 min**, the chosen arm "
                                "(results/m2l/l2/selection.json)"),
    "M2L_L3_SHORT_B": dict(env=dict(M2L_MODE="L3SHORT", M2L_SEGS="20,30", M2L_TAG="l3short_b"), tag="l3short_b",
                           account="nhannguyen26", inputs=[RAW, "v9-x3-fold1", "v9-x3-fold3"],
                           runtime="≈ 2.7–3 h (computed from L2's measured job times; PROJ stops above 10.5 h)",
                           what="development recordings cut into segments of **20 and 30 min**, the chosen arm"),
    "M2L_L3_EVAL": dict(env=dict(M2L_MODE="L3EVAL"), tag="l3eval", account="nhn2mm",
                        inputs=[RAW, "v9-x3-fold1", "v9-x3-fold3", "thesis-r2-external-features"],
                        runtime="≈ 3–3.5 h (computed from L2's measured job times; PROJ stops above 10.5 h)",
                        what="**test, chb24 and Siena, scored once** with the chosen arm, its k and the minimum length "
                             "(results/m2l/l3short/minlen.json); V5 control in the same session"),
}
GROUPS = {"L2": ["M2L_L2_REC", "M2L_L2_ROB"], "L3SHORT": ["M2L_L3_SHORT_A", "M2L_L3_SHORT_B"], "L3EVAL": ["M2L_L3_EVAL"]}
sha_of = lambda names: {n: hashlib.sha256((ROOT / "src" / n).read_bytes()).hexdigest()[:16] for n in names}


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.strip("\n").splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": t.strip("\n").splitlines(keepends=True)}


def build(name, ref):
    s = SPEC[name]
    sha = sha_of(FILES)
    inputs = ", ".join(f"`{x}`" for x in s["inputs"])
    cells = [md(f"""
# {name} — label-free per-recording protocol, SzScan 1.0 baseline (Track F, milestone M2, chat F2-03)

**Design:** `results/m2l/DESIGN_L2.md` (approved by the author 23/11/2026 14:19). This notebook: {s['what']}.
Every quantity V5 fits per patient (z-score statistics, per-channel latent reference, percentiles, alarm budget) is
fitted on the recording itself; the four V5 checkpoints, inference only; raw EDF verified against PhysioNet in the
session; the V5 control (R1.0) and the code-path gates run first and STOP on any difference.
**Account:** `{s['account']}`. **Accelerator:** None (CPU). **Internet:** ON (pip, git clone, PhysioNet checksums).
**Inputs (Add Input):** {inputs}.
**Output:** `/kaggle/working/m2l/{s['tag']}` (→ `results/m2l/{s['tag']}`; small files only). **Runtime:** {s['runtime']}.
Code: `github.com/Nhanvas/Thesis` ref `{ref}`; every module's sha256 is asserted below.
**Nothing printed here is a research result.** Do not edit; *Save Version → Save & Run All (Commit)*.
"""), code(f"""
# SETUP: packages + repository (read only)
import os, sys, subprocess, time, json, hashlib
T_NB = time.time()
NOTEBOOK, REPO_REF = "{name}", "{ref}"
TEST = bool(os.environ.get("EUR_TEST_REPO"))                     # synthetic test in the build container only
WORK = os.environ.get("EUR_TEST_WORK", "/kaggle/working")
INPUT = os.environ.get("EUR_TEST_INPUT", "/kaggle/input")
SCRATCH = os.environ.get("EUR_TEST_SCRATCH", "/tmp/r2")
if TEST:
    REPO = os.environ["EUR_TEST_REPO"]; HEAD = "test"
else:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", {PKGS}])
    REPO = "/tmp/Thesis"
    if not os.path.exists(REPO + "/src/m2l_run.py"):
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
                  OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", **{json.dumps(s['env'])})
if TEST:
    os.environ["R2_TEST"] = "1"
sys.path[:0] = [REPO + "/src"]
import m2l_run as M
assert M.__file__ == f"{{REPO}}/src/m2l_run.py", M.__file__
print("CPU cores:", os.cpu_count(), "| mode", os.environ["M2L_MODE"], "| m2l_core", M.M.sha16(M.M.__file__))
"""), code("""
# RUN: gates, smoke / control, per-recording build, scoring
ERR = None
try:
    M.main(NOTEBOOK, HEAD, workers=int(os.environ.get("M2L_WORKERS", "0")) or None)
except SystemExit as e:
    ERR = str(e)
"""), code(f"""
# END: gates, projection, outputs, measured runtime
OUT = os.path.join(WORK, "m2l", "{s['tag']}")
for f in ("gates.json", "projection.json", "k.json", "smoke.json", "run_meta.json"):
    p = os.path.join(OUT, f)
    if os.path.exists(p):
        print("=====", f); print(open(p).read()[:4000])
for root, _, fs in os.walk(OUT):
    for f in sorted(fs):
        p = os.path.join(root, f); print(os.path.relpath(p, WORK), os.path.getsize(p))
print(f"MEASURED notebook runtime: {{(time.time() - T_NB) / 3600:.3f}} h")
if ERR:
    raise RuntimeError(f"STOPPED: {{ERR}}")
""")]
    return name, cells


def write(name, cells):
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                       "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / f"{name}.ipynb").write_text(json.dumps(nb, indent=1))
    return OUTDIR / f"{name}.ipynb"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="main", help="branch main (default) or a 40-hex commit")
    ap.add_argument("--only", choices=list(GROUPS))
    a = ap.parse_args()
    if a.ref != "main" and not re.fullmatch(r"[0-9a-f]{40}", a.ref):
        ap.error("--ref takes main or a 40-hex commit hash, never a tag")
    for g, names in GROUPS.items():
        if a.only in (None, g):
            for n in names:
                print("built", write(*build(n, a.ref)))
    print("module sha16:", sha_of(FILES))
