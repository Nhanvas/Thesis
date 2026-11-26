#!/usr/bin/env python
"""
c5_g2_make_notebooks.py -- Kaggle notebooks of gate G2 (chat C5c, Track C; src/c5_g2.py):
  C5_G2_CHB    the 8 test patients + chb24 (231 + 22 recordings)
  C5_G2_SIENA  the 14 Siena patients (41 recordings)
Each notebook clones github.com/Nhanvas/Thesis at --ref, asserts the sha256 of every module and committed file it
uses (the m2l modules of F2-03's L3 run, c5_g2.py, the application modules, the L3 rows and the selection files), then
calls src/c5_g2.py. Built in the style of src/m2l_make_notebooks.py (same packages, same raw input as M2L_L3_EVAL).
  python src/c5_g2_make_notebooks.py [--ref main|<40-hex commit>]  -> notebooks/c5/*.ipynb
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

import m2l_make_notebooks as MK

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "notebooks" / "c5"
FILES = ["src/" + f for f in MK.FILES] + ["src/c5_g2.py", "web_demo/backend/pipeline_demo.py",
                                          "web_demo/backend/engine_file.py", "web_demo/backend/edf_input.py",
                                          "results/m2l/l3eval/per_file.csv", "results/m2l/l2/selection.json",
                                          "results/m2l/l3short/minlen.json", "data/models_v2/gae_v2_clean_seed42.pt",
                                          "results/p3c_freeze/freeze.json"]
SPEC = {
    "C5_G2_CHB": dict(set="chb", what="the 8 test patients and chb24 (253 recordings, about 300 h)",
                      runtime="≈ 2–4 h (computed: the laptop's measured Phase A + engine rate x 1.45 on 4 workers; "
                              "PROJ measures it on a 1-h recording and stops above 10.5 h)"),
    "C5_G2_SIENA": dict(set="siena", what="the 14 Siena patients (41 recordings, 141 h, 512 Hz)",
                        runtime="≈ 1.5–3 h (computed as above; PROJ stops above 10.5 h)"),
}
sha_of = lambda names: {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest()[:16] for n in names}


def build(name, ref):
    s = SPEC[name]
    sha = sha_of(FILES)
    cells = [MK.md(f"""
# {name} — SzScan file engine against F2-03's L3 rows (gate G2; Track C, chat C5c)

**What:** {s['what']}: each recording goes through the review application's own path (Phase A of
`web_demo/backend/pipeline_demo.py`, then `engine_file.run_file`, the "each file on its own" mode SzScan 1.0) and its
events are scored with L3's scorer; **gate G2** = every recording equal to F2-03's committed L3 row (B-MCD-F, seed 42:
events, tp, fp, seizures, short, windows; q and top within 1e-9). Raw EDF verified against PhysioNet in the session
(the L3 inventory). A smoke recording is compared before the build (STOP on a difference).
**Account:** one with Internet (chosen by the author). **Accelerator:** None (CPU). **Internet:** ON (pip, git clone,
PhysioNet checksums).
**Input (Add Input):** `{MK.RAW}`.
**Output:** `/kaggle/working/c5g2/c5g2_{s['set']}` (→ `results/c5_szscan/step2/g2/c5g2_{s['set']}`; small files only).
**Runtime:** {s['runtime']}.
Code: `github.com/Nhanvas/Thesis` ref `{ref}`; the sha256 of every module and committed file used is asserted below.
Do not edit; *Save Version → Save & Run All (Commit)*.
"""), MK.code(f"""
# SETUP: packages + repository (read only)
import os, sys, subprocess, time, json, hashlib
T_NB = time.time()
NOTEBOOK, REPO_REF = "{name}", "{ref}"
WORK, INPUT, SCRATCH = "/kaggle/working", "/kaggle/input", "/tmp/r2"
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", {MK.PKGS}])
REPO = "/tmp/Thesis"
if not os.path.exists(REPO + "/src/c5_g2.py"):
    subprocess.check_call(f"rm -rf {{REPO}} && git clone -q https://github.com/Nhanvas/Thesis.git {{REPO}} "
                          f"&& cd {{REPO}} && git checkout -q {{REPO_REF}}", shell=True)
HEAD = subprocess.check_output(["git", "-C", REPO, "rev-parse", "HEAD"]).decode().strip()
print("repository", REPO, HEAD, f"({{time.time()-T_NB:.0f}}s)")
"""), MK.code(f"""
# START: sha256 of every module and committed file used (the reviewed code only), environment, imports
WANT = {json.dumps(sha)}
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
bad = {{n: sha(f"{{REPO}}/{{n}}") for n in WANT if sha(f"{{REPO}}/{{n}}") != WANT[n]}}
assert not bad, f"files differ from the reviewed ones (rebuild the notebook or pin the right commit): {{bad}}"
os.environ.update(THESIS_REPO=REPO, R2_WORK=WORK, R2_INPUT=INPUT, R2_SCRATCH=SCRATCH, OMP_NUM_THREADS="1",
                  OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", C5G2_SET="{s['set']}")
sys.path[:0] = [REPO + "/src"]
import c5_g2 as G
assert G.__file__ == f"{{REPO}}/src/c5_g2.py", G.__file__
print("CPU cores:", os.cpu_count(), "| set", os.environ["C5G2_SET"])
"""), MK.code("""
# RUN: inventory (PhysioNet), smoke + PROJ, every recording through the application, gate G2
ERR = None
try:
    G.main(NOTEBOOK, HEAD, workers=int(os.environ.get("C5G2_WORKERS", "0")) or None)
except SystemExit as e:
    ERR = str(e)
"""), MK.code(f"""
# END: gates, outputs, measured runtime
OUT = os.path.join(WORK, "c5g2", "c5g2_{s['set']}")
for f in ("gates.json", "projection.json", "smoke.json", "SUMMARY.md"):
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
    a = ap.parse_args()
    if a.ref != "main" and not re.fullmatch(r"[0-9a-f]{40}", a.ref):
        ap.error("--ref takes main or a 40-hex commit hash, never a tag")
    for n in SPEC:
        print("built", write(*build(n, a.ref)))
