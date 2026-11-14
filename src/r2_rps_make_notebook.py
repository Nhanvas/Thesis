#!/usr/bin/env python
"""r2_rps_make_notebook.py -- builds the Kaggle notebook RP_SERIES of stage RP, path 2 (docs/FUTURE_RESEARCH_PLAN.md §12
rows 14/11 01:27 and D26-F) from src/r2_rps.py (embedded verbatim with %%writefile; sha256 checked in the notebook). The
repository is cloned at a pinned commit (40-hex hash) holding r2_rp.py, r2_r1.py, r2_core.py (shas checked), the RP_RUN
output (results/r2/r1_system/rp: checkpoints, rp2 rows, scores, k), the R1 checkpoints, R1_SMOKE's pinned data hashes,
the attribution record and RB1c's cases.csv. Nothing to fill in.
  python src/r2_rps_make_notebook.py --run <commit>   -> notebooks/r2/RP_SERIES.ipynb
Test mode (synthetic data, build container only): R2_TEST_REPO / R2_TEST_INPUT / R2_TEST_WORK / R2_TEST_SCRATCH."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R0_SHA = "902d15ad4feb3e8a"                                         # r2_core.py (stage R0)
R1_SHA = "76cbe51ff0180d4a"                                         # r2_r1.py (stage R1, R1_RUN)
RP_SHA = hashlib.sha256((ROOT / "src" / "r2_rp.py").read_bytes()).hexdigest()[:16]     # r2_rp.py (RP_RUN), unchanged
OUTDIR = Path(os.environ.get("R2_NB_OUTDIR", ROOT / "notebooks" / "r2"))
CORE = (ROOT / "src" / "r2_rps.py").read_text()
SHA = hashlib.sha256(CORE.encode()).hexdigest()[:16]
PKGS = '"mne==1.12.1", "torch_geometric==2.7.0", "ruptures==1.1.10", "timescoring==0.0.7"'
RAW = "bonesclarke26/combined-siena-scalp-and-chb-mit-eeg-datasets"


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.strip("\n").splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": t.strip("\n").splitlines(keepends=True)}


def build(commit):
    name = "RP_SERIES"
    cells = [md(f"""
# RP_SERIES — research track, stage RP, path 2: per-window series of the report model (Chapter 2 numbers, RP5, RP9-E1)

**Plan:** `docs/FUTURE_RESEARCH_PLAN.md` §12 rows 14/11 01:27 (design) and D26-F (implementation). **Does:** G-grid,
G-data (63 dataset files = the pinned hashes), versions vs R1_RUN (mode exact / tolerance); **pass A**: distances and
latents of the 15 development and 8 test patients with the path-2 checkpoints (seeds 1–4), **RS.0** (they reproduce
`rp2/per_subject.csv` and `rp2/scores`), Table 6 arms (S9 base, e16 arms a–e), drift diagnostics, D1b grid, Table 7
detectors, RP9-E1 data; **A-latent** (G-alat, leave-one-patient-out fits on the training latents); **RP5** (RS-attr, then
the channel ranking per seed); **flags**: every raw EDF of the 12 training patients verified against PhysioNet, the 5-SD
flag rule on their seizure windows (G-flags: = the R0 dataset window by window).
**Accelerator:** None (CPU). **Internet:** ON (pip, git clone, PhysioNet SHA256SUMS and any missing file).
**Inputs:** `thesis-r2-chbmit-features` + `thesis-r2-external-features` + `{RAW}`.
**Output:** `/kaggle/working/r2/r1_system/rp_series/` (→ `results/r2/r1_system/rp_series/`), a few MB.
**Runtime:** ≈ 1.5–2.5 h (computed estimate, not measured: distances ≈ 1 s per hour of EEG for 4 seeds (R1_SMOKE),
959 h; the thesis experiments' recorded run times scaled to 4 seeds; raw-file hashing and filtering of 566 h ≈ 0.5 h).
Code: `github.com/Nhanvas/Thesis` at `{commit[:7]}` (read only) + `r2_rps.py` below (sha256 `{SHA}`). Gates STOP the
notebook (`STOPPED: ...`). **Nothing printed here is a research result.** Do not edit; *Save Version → Save & Run All (Commit)*.
"""), code(f"""
# SETUP: packages + repository at the pinned commit (read only)
import os, sys, subprocess, time, json, hashlib, shutil
T_NB = time.time()
os.environ["R2_T0"] = str(T_NB)
NOTEBOOK, REPO_COMMIT = "{name}", "{commit}"
TEST = bool(os.environ.get("R2_TEST_REPO"))                      # synthetic test in the build container only
WORK = os.environ.get("R2_TEST_WORK", "/kaggle/working")
INPUT = os.environ.get("R2_TEST_INPUT", "/kaggle/input")
SCRATCH = os.environ.get("R2_TEST_SCRATCH", "/tmp/r2")
SRC = SCRATCH + "/src_rps"
os.makedirs(SRC, exist_ok=True)
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
if TEST:
    REPO = os.environ["R2_TEST_REPO"]
else:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", {PKGS}])
    REPO = "/tmp/Thesis"
    if not os.path.exists(REPO + "/src/r2_rp.py"):
        r = subprocess.run(f"git init -q {{REPO}} && cd {{REPO}} && git remote add origin https://github.com/Nhanvas/Thesis.git "
                           f"&& git fetch -q --depth 1 origin {{REPO_COMMIT}} && git checkout -q FETCH_HEAD", shell=True)
        if r.returncode != 0:
            subprocess.check_call(f"rm -rf {{REPO}} && git clone -q https://github.com/Nhanvas/Thesis.git {{REPO}} "
                                  f"&& cd {{REPO}} && git checkout -q {{REPO_COMMIT}}", shell=True)
    head = subprocess.check_output(["git", "-C", REPO, "rev-parse", "HEAD"]).decode().strip()
    assert head == REPO_COMMIT, f"wrong commit {{head}}"
for f, want in (("r2_core.py", "{R0_SHA}"), ("r2_r1.py", "{R1_SHA}"), ("r2_rp.py", "{RP_SHA}")):
    got = hashlib.sha256(open(f"{{REPO}}/src/{{f}}", "rb").read()).hexdigest()[:16]
    assert TEST or got == want, f"{{f}} sha {{got}} != {{want}}"
print("repository", REPO, f"({{time.time()-T_NB:.0f}}s)")
"""), code("%%writefile {SRC}/r2_rps.py\n" + CORE), code(f"""
# START: sha check of the embedded file, imports, run metadata, library versions vs R1_RUN (mode), G-grid
sha = hashlib.sha256(open(f"{{SRC}}/r2_rps.py", "rb").read()).hexdigest()[:16]
assert sha == "{SHA}", f"r2_rps.py: sha {{sha}} != {SHA} (cell edited?)"
os.environ.update(THESIS_REPO=REPO, R2_WORK=WORK, R2_INPUT=INPUT, R2_SCRATCH=SCRATCH)
sys.path[:0] = [SRC, REPO + "/src"]
import pandas as pd, numpy as np
import torch
torch.set_num_threads(1)
def stopped(e):
    raise RuntimeError(f"STOPPED: {{e}}") from None
import r2_rps as RS
RP, R1 = RS.RP, RS.R1
W = R1.n_workers()
print("CPU cores:", os.cpu_count(), "| torch threads:", torch.get_num_threads(), "| workers:", W)
META = R1.run_meta(RS.TAG, NOTEBOOK, REPO_COMMIT)
MODE, VDIFF = RP.check_versions(META)
print("mode:", MODE, "| version differences vs R1_RUN:", VDIFF)
SCR = R1.SCRATCH / "rps"
shutil.rmtree(SCR, ignore_errors=True); SCR.mkdir(parents=True)
try:
    RS.gate_grid()
except SystemExit as e:
    stopped(e)
"""), code("""
# VIEWS + G-data (pinned hashes of the R0 datasets)
try:
    V = RP.build_views()
    RP.gate_data(V)
except SystemExit as e:
    stopped(e)
"""), code("""
# PASS A: series of the 15 development + 8 test patients, seeds 1-4; RS.0 (= rp2 rows and scores); development tables
try:
    RES, CK, KMAP = RS.pass_a(W, SCR)
    RS.rs0(RES)
    RS.write_dev(RES)
    RS.timing(RES)
except SystemExit as e:
    stopped(e)
"""), code("""
# A-LATENT: leave-one-patient-out Ledoit-Wolf on the training patients' clean latents (G-alat), scored like C
try:
    RS.a_latent(W, SCR, CK, RES)
except SystemExit as e:
    stopped(e)
"""), code("""
# RP5: RS-attr (alignment, code path on the committed scores), then the channel ranking with each seed as primary
try:
    RS.rp5(SCR)
except SystemExit as e:
    stopped(e)
"""), code("""
# FLAGS (F-dm.7): raw EDF of the 12 training patients verified against PhysioNet (r2_core.inventory), then the 5-SD flag
# rule on every window with the R0 thresholds; G-flags = the R0 dataset window by window
R0 = RS.R0
try:
    R0.run_meta(RS.TAG + "_inventory", NOTEBOOK, REPO_COMMIT)
    INV, CASES, COMPLETE, _ = R0.inventory({"chbmit": list(RS.TRAIN)})
    inv_out = R1.out_dir() / "inventory"
    inv_out.mkdir(exist_ok=True)
    for f in sorted(R0.out_dir().iterdir()):
        if f.is_file():
            shutil.copy(f, inv_out)
    REF = os.environ.get("R2_TEST_FLAGS_REF") if TEST else None          # synthetic test: its own R0-built references
    FL = RS.flags(W, COMPLETE, REF)
except SystemExit as e:
    stopped(e)
print(FL.to_string(index=False))
"""), code("""
# END: SUMMARY.md, measured runtime, outputs
print(RS.summary_md())
meta = R1.finish_meta(dict(r2_rps_sha256=hashlib.sha256(open(f"{SRC}/r2_rps.py", "rb").read()).hexdigest(), mode=RP.STATE["mode"]))
print(f"MEASURED notebook runtime: {meta['runtime_h']} h | phases (s): {meta['phases_s']}")
for p in sorted(R1.out_dir().rglob("*")):
    if p.is_file():
        print(p.relative_to(R1.OUT_ROOT), p.stat().st_size)
""")]
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                       "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / f"{name}.ipynb").write_text(json.dumps(nb, indent=1))
    return OUTDIR / f"{name}.ipynb"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", metavar="COMMIT", required=True, help="40-hex commit holding src/r2_rps.py and the RP output")
    a = ap.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", a.run):
        ap.error("--run takes a 40-hex commit hash, never a tag")
    print("built", build(a.run).name, "r2_rps sha", SHA)
