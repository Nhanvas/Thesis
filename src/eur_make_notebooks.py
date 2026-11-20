#!/usr/bin/env python
"""eur_make_notebooks.py -- builds the Kaggle notebooks of the Euréka suite (Track F, chat D31-F).
  EUR_ABL   src/eur_abl.py (ablation suite on the V5 checkpoints; smoke on 2-3 cases first, then the full run)
  EUR_9A    src/eur_9a.py (V5 with label-free z-score statistics; raw EDF verified against PhysioNet; smoke first)
  EUR_DIAG  src/eur_diag.py (diagnostics D1 shifted grids and EV event properties on V5; raw EDF verified)
  EUR_ABL8B src/eur_abl.py with EUR_VARIANTS=V0,8b and EUR_TAG=abl8b (ablation 8b, no encoder; chat D32-F, 20/11)
  EUR_OPT   src/eur_abl.py with EUR_VARIANTS=V0,O6a,O6b,O7 and EUR_TAG=opt (optimisations O6 / O7; chat D32-F, 20/11)
Notebook pin rule (plan §0, board R205): the notebook clones the repository (branch main by default, or --ref COMMIT)
and imports every module FROM THE CLONE; before anything runs it asserts the sha256 of each module against the values
baked in at build time (the local files), so a run can only execute the reviewed code; pool workers import the same
files and report their sha256 (gate G-worker). Rebuild the notebook after any change to a listed file.
  python src/eur_make_notebooks.py [--ref main|<40-hex commit>] [--only EUR_ABL|EUR_9A|EUR_DIAG|EUR_ABL8B|EUR_OPT]  -> notebooks/eureka/*.ipynb
Test mode (synthetic world, build container only): EUR_TEST_REPO / EUR_TEST_INPUT / EUR_TEST_WORK / EUR_TEST_SCRATCH."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = Path(os.environ.get("EUR_NB_OUTDIR", ROOT / "notebooks" / "eureka"))
FILES = ["eur_abl.py", "r2_r1.py", "r2_core.py", "e16_recording_baseline.py", "e17b_latent_family.py", "p3c_freeze.py",
         "p3_levers.py", "p2_scalars.py", "e22_test_oneshot.py", "e23_test_look7.py", "x1_external.py",
         "p2_dump_seeds23.py", "e18_cpd_localizer.py", "e10_kernel_cpd.py"]
FILES_9A = ["eur_9a.py"] + FILES + ["dataprep/preprocessing.py", "continuous_eval.py", "c1b_build_trainset.py",
                                    "evaluation_protocol.py"]
FILES_DIAG = ["eur_diag.py"] + FILES + ["dataprep/preprocessing.py", "continuous_eval.py", "c1b_build_trainset.py",
                                        "evaluation_protocol.py"]
sha_of = lambda names: {n: hashlib.sha256((ROOT / "src" / n).read_bytes()).hexdigest()[:16] for n in names}
SHA = sha_of(FILES)
PKGS = '"torch_geometric==2.7.0", "ruptures==1.1.10", "timescoring==0.0.7"'
PKGS_9A = '"mne==1.12.1", "torch_geometric==2.7.0", "ruptures==1.1.10", "timescoring==0.0.7"'   # = R0 / R1 notebooks


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.strip("\n").splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": t.strip("\n").splitlines(keepends=True)}


def build_abl(ref):
    name = "EUR_ABL"
    cells = [md(f"""
# {name} — Euréka ablation suite on the V5 model (Track F, chat D31-F)

**Design:** `results/eureka_d31f/STEP1_DESIGN.md` (approved 19/11/2026 20:35). Inference only, the four committed V5
checkpoints; 17 variants (1a, 1b, 4a, 4b, 4c, 2a, 2b, 3a, 3m, 3c, 3g, 3r, 5a ×3, 8a) + V0; 6a / 7a / 7b come from V0.
**Runs a SMOKE first** (chb01, chb03, chb24: every gate and every variant once, measured) and STOPs before the full
run if anything differs from the V5 record. **Accelerator:** None (CPU). **Internet:** ON (pip, git clone).
**Inputs (Add Input):** `v9-x3-fold1`, `v9-x3-fold3`, `thesis-r2-external-features`. **Output:** `/kaggle/working/eureka/abl`
(→ `results/eureka_d31f/abl`). **Runtime:** 1.5–2.5 h (computed; the smoke writes `projection.json`).
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
    if not os.path.exists(REPO + "/src/eur_abl.py"):
        subprocess.check_call(f"rm -rf {{REPO}} && git clone -q https://github.com/Nhanvas/Thesis.git {{REPO}} "
                              f"&& cd {{REPO}} && git checkout -q {{REPO_REF}}", shell=True)
    HEAD = subprocess.check_output(["git", "-C", REPO, "rev-parse", "HEAD"]).decode().strip()
print("repository", REPO, HEAD, f"({{time.time()-T_NB:.0f}}s)")
"""), code(f"""
# START: sha256 of every module (the reviewed code only), environment, imports
WANT = {json.dumps(SHA)}
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
bad = {{n: sha(f"{{REPO}}/src/{{n}}") for n in WANT if sha(f"{{REPO}}/src/{{n}}") != WANT[n]}}
assert not bad, f"modules differ from the reviewed code (rebuild the notebook or pin the right commit): {{bad}}"
os.environ.update(THESIS_REPO=REPO, R2_WORK=WORK, R2_INPUT=INPUT, R2_SCRATCH=SCRATCH, OMP_NUM_THREADS="1",
                  OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
if TEST:
    os.environ["R2_TEST"] = "1"
sys.path[:0] = [REPO + "/src"]
import eur_abl as M
assert M.__file__ == f"{{REPO}}/src/eur_abl.py", M.__file__
print("CPU cores:", os.cpu_count(), "| eur_abl", M.CODE_SHA, "| variants", list(M.VARIANTS))
"""), code("""
# RUN: G-self, G-data, SMOKE (R1.0 rows, G-D0, G-enc, G-x0, G-eng, projection), then the full run
ERR = None
try:
    M.main(NOTEBOOK, HEAD, workers=int(os.environ.get("EUR_WORKERS", "0")) or None)
except SystemExit as e:
    ERR = str(e)
"""), code("""
# END: gates, projection, outputs, measured runtime
OUT = os.path.join(WORK, "eureka", "abl")
for f in ("gates.json", "smoke/gates.json", "projection.json", "k.csv", "run_meta.json"):
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
    return name, cells


def build_9a(ref):
    name = "EUR_9A"
    sha = sha_of(FILES_9A)
    cells = [md(f"""
# {name} — V5 with label-free z-score statistics on CHB-MIT (Track F, chat D31-F)

**Design:** `results/eureka_d31f/STEP1_DESIGN.md` §3 (approved 19/11/2026 20:35). One change to V5: the per-patient
z-score statistics of the 23 CHB-MIT cases are computed by the record function **without** the seizure map (every 10th
window of every file), then the features are rebuilt by the record builder and scored with the four committed V5
checkpoints (k recalibrated by V5's rule, and at the record's k). The raw EDF are verified against PhysioNet's SHA256SUMS
in this session. **Runs a SMOKE first** (chb08: the record statistics and the first 2 files' features reproduce the
record) and the V5 control (R1.0) before the long build; STOPs on any difference.
**Accelerator:** None (CPU). **Internet:** ON (pip, git clone, PhysioNet checksums and missing files).
**Inputs (Add Input):** `combined-siena-scalp-and-chb-mit-eeg-datasets` (raw EDF), `v9-x3-fold1`, `v9-x3-fold3`.
**Output:** `/kaggle/working/eureka/9a` (→ `results/eureka_d31f/9a`; small files only). **Runtime:** ≈ 3–4 h (computed
from R0's measured statistics and feature rates; the run writes `projection.json` and STOPs if it projects > 10.5 h).
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
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", {PKGS_9A}])
    REPO = "/tmp/Thesis"
    if not os.path.exists(REPO + "/src/eur_9a.py"):
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
import eur_9a as M
assert M.__file__ == f"{{REPO}}/src/eur_9a.py", M.__file__
print("CPU cores:", os.cpu_count(), "| eur_9a", M.sha16(M.__file__), "| cases", len(M.CASES), "| smoke", M.SMOKE_CASE)
"""), code("""
# RUN: G-raw (PhysioNet), G-data, SMOKE (G-stats0, G-feat0), V5 control (R1.0, G-k), PROJ, label-free build
# (G-struct), scoring (k recalibrated; record k)
ERR = None
try:
    M.main(NOTEBOOK, HEAD, workers=int(os.environ.get("EUR_WORKERS", "0")) or None)
except SystemExit as e:
    ERR = str(e)
"""), code("""
# END: gates, projection, outputs, measured runtime
OUT = os.path.join(WORK, "eureka", "9a")
for f in ("gates.json", "projection.json", "run_meta.json", "r13/lf/k.json"):
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
    return name, cells


def build_diag(ref):
    name = "EUR_DIAG"
    sha = sha_of(FILES_DIAG)
    cells = [md(f"""
# {name} — diagnostics D1 and EV on the V5 model (Track F, chat D31-F)

**Design:** `src/eur_diag.py` docstring, `results/eureka_d31f/STEP1_DESIGN.md` §4 and `ROADMAP_LOGBOOK.md` (approved
19/11/2026 20:35 / 20:39). **D1:** the short seizures (< 20 s) rebuilt from the raw EDF on grids shifted by 0, +1, +2,
+3 s and scored against each patient's unshifted V5 quantities (upper bound of a 2 s hop). **EV:** properties of V5's own
flagged events (rhythm, waveform, field, artifact signatures, evolution, duration) as robust z against the patient's
background; development decides by the fixed rule, the rest is descriptive. Inference only; raw EDF verified against
PhysioNet in the session; V5 reproduced first (R1.0, GE, G-k), then G-ev, G-s0, G-extstats.
**Accelerator:** None (CPU). **Internet:** ON (pip, git clone, PhysioNet checksums and missing files).
**Inputs (Add Input):** `combined-siena-scalp-and-chb-mit-eeg-datasets`, `v9-x3-fold1`, `v9-x3-fold3`,
`thesis-r2-external-features`. **Output:** `/kaggle/working/eureka/diag` (→ `results/eureka_d31f/diag`; small files only).
**Runtime:** ≈ 1.5–2.5 h (computed: R1.0 0.25 h measured in EUR_ABL + one read of every file of 38 patients ≈ 1,100 h of
EEG + the external statistics). Code: `github.com/Nhanvas/Thesis` ref `{ref}`; every module's sha256 is asserted below.
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
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", {PKGS_9A}])
    REPO = "/tmp/Thesis"
    if not os.path.exists(REPO + "/src/eur_diag.py"):
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
import eur_diag as M
assert M.__file__ == f"{{REPO}}/src/eur_diag.py", M.__file__
print("CPU cores:", os.cpu_count(), "| eur_diag", M.sha16(M.__file__), "| cases", len(M.DEV + M.TEST + M.EXT))
"""), code("""
# RUN: G-raw, G-data, V5 (R1.0, GE, G-k), per-patient D1 + EV jobs, G-ev, G-s0, G-extstats, G-worker, readings
ERR = None
try:
    M.main(NOTEBOOK, HEAD, workers=int(os.environ.get("EUR_WORKERS", "0")) or None)
except SystemExit as e:
    ERR = str(e)
"""), code("""
# END: gates, readings, outputs, measured runtime
OUT = os.path.join(WORK, "eureka", "diag")
for f in ("gates.json", "D1.md", "EV.md", "run_meta.json"):
    p = os.path.join(OUT, f)
    if os.path.exists(p):
        print("=====", f); print(open(p).read()[:6000])
for root, _, fs in os.walk(OUT):
    for f in sorted(fs):
        p = os.path.join(root, f); print(os.path.relpath(p, WORK), os.path.getsize(p))
print(f"MEASURED notebook runtime: {(time.time() - T_NB) / 3600:.3f} h")
if ERR:
    raise RuntimeError(f"STOPPED: {ERR}")
""")]
    return name, cells


def build_abl8b(ref):
    """EUR_ABL's notebook with two environment values: only V0 and 8b, output folder abl8b."""
    name, cells = build_abl(ref)
    name = "EUR_ABL8B"
    cells[0] = md(f"""
# {name} — ablation 8b on the V5 model: no encoder (Track F, chat D32-F)

**Design:** `results/eureka_d32f/DESIGN_8B.md` (approved by the author 20/11/2026). One factor: the per-channel
Ledoit–Wolf Mahalanobis distance is taken on the 30-value node input the GAE receives instead of its 16-value latent;
the rest of V5 is the record code (members, drift correction, percentiles, budget with k recalibrated, localizer). V0 is
recomputed in the same run (record gates, paired differences). **Runs a SMOKE first** (chb01, chb03, chb24) and STOPs
before the full run if anything differs from the V5 record. **Accelerator:** None (CPU). **Internet:** ON (pip, git clone).
**Inputs (Add Input):** `v9-x3-fold1`, `v9-x3-fold3`, `thesis-r2-external-features`. **Output:**
`/kaggle/working/eureka/abl8b` (→ `results/eureka_d32f/abl8b`). **Runtime:** ≈ 0.5–0.9 h (computed from EUR_ABL's
measured 0.868 h for 17 variants; the smoke writes `projection.json`).
Code: `github.com/Nhanvas/Thesis` ref `{ref}`; every module's sha256 is asserted below.
**Nothing printed here is a research result.** Do not edit; *Save Version → Save & Run All (Commit)*.
""")
    src = "".join(cells[2]["source"])
    src = src.replace('os.environ.update(THESIS_REPO=REPO,', 'os.environ.update(EUR_VARIANTS="V0,8b", EUR_TAG="abl8b", THESIS_REPO=REPO,', 1)
    assert "EUR_VARIANTS" in src
    cells[2] = code(src)
    src = "".join(cells[1]["source"]).replace('NOTEBOOK, REPO_REF = "EUR_ABL"', f'NOTEBOOK, REPO_REF = "{name}"', 1)
    assert name in src
    cells[1] = code(src)
    src = "".join(cells[4]["source"]).replace('OUT = os.path.join(WORK, "eureka", "abl")', 'OUT = os.path.join(WORK, "eureka", "abl8b")', 1)
    assert "abl8b" in src
    cells[4] = code(src)
    return name, cells


def build_opt(ref):
    """EUR_ABL's notebook with EUR_VARIANTS=V0,O6a,O6b,O7 and the output folder opt."""
    name, cells = build_abl(ref)
    name = "EUR_OPT"
    cells[0] = md(f"""
# {name} — optimisations O6 and O7 on the V5 model (Track F, chat D32-F)

**Design:** `results/eureka_d32f/DESIGN_O6_O7.md` (approved by the author 20/11/2026 14:14). Inference only, the four
V5 checkpoints. **O6a / O6b:** each channel's normal latent modelled per patient as a mixture of Gaussian components
(K by BIC 1–4 / K = 2), score = the smallest Mahalanobis distance to a component. **O7:** the latent averaged over the
previous, own and next window before V5's distance. V0 recomputed in the same run; k recalibrated per variant; the rest
is V5's code. Selection on the development patients by the R214 rule written in the design. **Runs a SMOKE first**
(chb01, chb03, chb24; gates incl. G-mix1) and STOPs before the full run if anything differs from the V5 record.
**Accelerator:** None (CPU). **Internet:** ON (pip, git clone). **Inputs (Add Input):** `v9-x3-fold1`, `v9-x3-fold3`,
`thesis-r2-external-features`. **Output:** `/kaggle/working/eureka/opt` (→ `results/eureka_d32f/opt`). **Runtime:** ≈ 1–1.5 h
(computed; the smoke writes `projection.json`). Code: `github.com/Nhanvas/Thesis` ref `{ref}`; module sha256 asserted below.
**Nothing printed here is a research result.** Do not edit; *Save Version → Save & Run All (Commit)*.
""")
    src = "".join(cells[2]["source"]).replace('os.environ.update(THESIS_REPO=REPO,',
                                               'os.environ.update(EUR_VARIANTS="V0,O6a,O6b,O7", EUR_TAG="opt", THESIS_REPO=REPO,', 1)
    assert "EUR_VARIANTS" in src
    cells[2] = code(src)
    src = "".join(cells[1]["source"]).replace('NOTEBOOK, REPO_REF = "EUR_ABL"', f'NOTEBOOK, REPO_REF = "{name}"', 1)
    assert name in src
    cells[1] = code(src)
    src = "".join(cells[4]["source"]).replace('OUT = os.path.join(WORK, "eureka", "abl")', 'OUT = os.path.join(WORK, "eureka", "opt")', 1)
    assert '"opt"' in src
    cells[4] = code(src)
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
    ap.add_argument("--only", choices=["EUR_ABL", "EUR_9A", "EUR_DIAG", "EUR_ABL8B", "EUR_OPT"])
    a = ap.parse_args()
    if a.ref != "main" and not re.fullmatch(r"[0-9a-f]{40}", a.ref):
        ap.error("--ref takes main or a 40-hex commit hash, never a tag")
    if a.only in (None, "EUR_ABL"):
        print("built", write(*build_abl(a.ref)), SHA)
    if a.only in (None, "EUR_9A"):
        print("built", write(*build_9a(a.ref)), sha_of(FILES_9A))
    if a.only in (None, "EUR_DIAG"):
        print("built", write(*build_diag(a.ref)), sha_of(FILES_DIAG))
    if a.only == "EUR_ABL8B":                     # built only on request (the other notebooks are records of runs)
        print("built", write(*build_abl8b(a.ref)), SHA)
    if a.only == "EUR_OPT":
        print("built", write(*build_opt(a.ref)), SHA)
