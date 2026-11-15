#!/usr/bin/env python
"""fa15_make_notebooks.py -- builds the Kaggle notebooks of F-A1.5 (project verification outside the report, board R204;
plan §12 15/11 12:40):
  --smoke COMMIT  notebooks/fa15/FA15_SMOKE.ipynb   chb17 (CHB-MIT thesis convention, every file) + PN00 (Siena, x1
                  convention) + two ASR-only files of V9-X6's universe (chb06_01, a 4-h file; chb24_01); gates, measured
                  ASR / feature rates, memory, disk, G-ident; projection.json + split.json for the data notebooks
  --data COMMIT   notebooks/fa15/FA15_DATA_<x>.ipynb, one per part of results/fa15/smoke/split.json at COMMIT
Each clones github.com/Nhanvas/Thesis at the pinned COMMIT (40-hex, never a tag) and checks the sha256 of fa15_asr.py.
Inputs: the raw dataset (bonesclarke26/combined-siena-scalp-and-chb-mit-eeg-datasets), thesis-r2-chbmit-features
(nhn2mm), thesis-r2-external-features (norncreades). Internet ON (pip, git, PhysioNet SHA256SUMS). CPU.
Test (synthetic data, build container only): src/fa15_synthetic_test.py runs the notebook cells with FA15_TEST_* paths."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "notebooks" / "fa15"
RAW = "bonesclarke26/combined-siena-scalp-and-chb-mit-eeg-datasets"
PKGS = '"asrpy==0.0.8", "mne==1.12.1", "torch_geometric==2.7.0", "ruptures==1.1.10", "timescoring==0.0.7"'
SMOKE = dict(chb=["chb17"], ext=["PN00"], asr_only=["chb06:chb06_01.edf", "chb24:chb24_01.edf"])


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.strip("\n").splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": t.strip("\n").splitlines(keepends=True)}


def sha_at(commit, rel):
    if commit == "WORKTREE":
        return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()[:16]
    return hashlib.sha256(subprocess.check_output(["git", "-C", str(ROOT), "show", f"{commit}:{rel}"])).hexdigest()[:16]


def build(name, commit, tag, chb, ext, asr_only, smoke, runtime):
    sha = sha_at(commit, "src/fa15_asr.py")
    cells = [
        md(f"""
# {name} — F-A1.5, project verification (not part of the report; board R204)

**Plan:** `docs/FUTURE_RESEARCH_PLAN.md` §12 15/11 12:40. **Does:** ASR exactly as V9-X6 (asrpy 0.0.8, cutoff 20, per-file
calibration, one process per file) on the pipeline-filtered signal, then the record's statistics and features on the
cleaned signal; gates G-conv, G-lab, G-asr{', G-ident and the projection of the data notebooks' if smoke else ''}.
**Cases:** CHB-MIT {chb or '—'}; external {ext or '—'}{('; ASR only: ' + ', '.join(asr_only)) if asr_only else ''}.
**Accelerator:** None (CPU). **Internet:** ON. **Inputs:** `{RAW}`, `thesis-r2-chbmit-features` (nhn2mm),
`thesis-r2-external-features` (norncreades).
**Runtime:** {runtime}. Code: `github.com/Nhanvas/Thesis` at `{commit[:7]}`; `src/fa15_asr.py` sha256 `{sha}` (checked).
A gate failure is recorded; the END cell archives the results, then raises `STOPPED: ...`.
Do not edit; *Save Version → Save & Run All (Commit)*.
"""),
        code(f"""
# SETUP: packages + repository at the pinned commit (read only)
import os, sys, subprocess, time, json, hashlib, shutil
T_NB = time.time()
os.environ["FA15_T0"] = os.environ["R2_T0"] = str(T_NB)
NOTEBOOK, REPO_COMMIT, TAG = "{name}", "{commit}", "{tag}"
TEST = bool(os.environ.get("FA15_TEST_REPO"))                    # synthetic test in the build container only
WORK = os.environ.get("FA15_TEST_WORK", "/kaggle/working")
INPUT = os.environ.get("FA15_TEST_INPUT", "/kaggle/input")
SCRATCH = os.environ.get("FA15_TEST_SCRATCH", "/tmp/fa15")
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
if TEST:
    REPO = os.environ["FA15_TEST_REPO"]
else:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", {PKGS}])
    REPO = "/tmp/Thesis"
    if not os.path.exists(REPO + "/src/fa15_asr.py"):
        r = subprocess.run(f"git init -q {{REPO}} && cd {{REPO}} && git remote add origin https://github.com/Nhanvas/Thesis.git "
                           f"&& git fetch -q --depth 1 origin {{REPO_COMMIT}} && git checkout -q FETCH_HEAD", shell=True)
        if r.returncode != 0:
            subprocess.check_call(f"rm -rf {{REPO}} && git clone -q https://github.com/Nhanvas/Thesis.git {{REPO}} "
                                  f"&& cd {{REPO}} && git checkout -q {{REPO_COMMIT}}", shell=True)
    head = subprocess.check_output(["git", "-C", REPO, "rev-parse", "HEAD"]).decode().strip()
    assert head == REPO_COMMIT, f"wrong commit {{head}}"
sha = hashlib.sha256(open(REPO + "/src/fa15_asr.py", "rb").read()).hexdigest()[:16]
assert TEST or sha == "{sha}", f"fa15_asr.py sha {{sha}} != {sha}"
os.environ.update(THESIS_REPO=REPO, FA15_WORK=WORK, FA15_SCRATCH=SCRATCH, R2_WORK=WORK, R2_INPUT=INPUT,
                  R2_SCRATCH=SCRATCH + "/r2")
sys.path.insert(0, REPO + "/src")
print("repository", REPO, "CPU cores", os.cpu_count(), f"({{time.time()-T_NB:.0f}}s)")
"""),
        code(f"""
# RUN: inventory (every raw file sha256 = PhysioNet), ASR per file (one process each), statistics + features per case
# (record code), gates; results in WORK/fa15/{tag}/, datasets in WORK/fa15-asr-*-features-{tag}/
import fa15_asr as F
CHB, EXT, ASR_ONLY = {json.dumps(chb)}, {json.dumps(ext)}, {json.dumps(asr_only)}
if TEST and os.environ.get("FA15_TEST_CASES"):                   # the synthetic world holds a few cases only
    CHB, EXT, ASR_ONLY = json.loads(os.environ["FA15_TEST_CASES"])
FAILED = F.run(TAG, CHB, EXT, ASR_ONLY, smoke={smoke}, notebook=NOTEBOOK, commit=REPO_COMMIT)
print("failed gates:", FAILED or "none")
"""),
        code(f"""
# END: archive the results (small files), measured runtime; datasets stay in WORK for "Output -> New Dataset"
OUT = os.path.join(WORK, "fa15", TAG)
for d in ("specs",):
    shutil.rmtree(os.path.join(SCRATCH, d), ignore_errors=True)
ZIP = shutil.make_archive(os.path.join(WORK, f"fa15_{{TAG}}_results"), "zip", root_dir=os.path.join(WORK, "fa15"), base_dir=TAG)
print("results archive:", ZIP, f"{{os.path.getsize(ZIP) / 1e6:.1f}} MB")
for dname in sorted(os.listdir(WORK)):
    if dname.startswith("fa15-asr-"):
        fs = os.listdir(os.path.join(WORK, dname))
        print("dataset folder", dname, len(fs), "files", f"{{sum(os.path.getsize(os.path.join(WORK, dname, f)) for f in fs) / 1e9:.2f}} GB")
print(open(os.path.join(OUT, "SUMMARY.md")).read())
print("MEASURED notebook runtime (h):", round((time.time() - T_NB) / 3600, 3))
if FAILED:
    raise RuntimeError(f"STOPPED: failed gates {{FAILED}} (results archived)")
"""),
    ]
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                       "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    p = OUTDIR / f"{name}.ipynb"
    p.write_text(json.dumps(nb, indent=1))
    print("written", p, "fa15_asr sha", sha)
    return nb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke")
    ap.add_argument("--data")
    a = ap.parse_args()
    for c in (a.smoke, a.data):
        if c and c != "WORKTREE" and not re.fullmatch(r"[0-9a-f]{40}", c):
            raise SystemExit("pin a 40-hex commit hash (never a tag)")
    if a.smoke:
        build("FA15_SMOKE", a.smoke, "smoke", SMOKE["chb"], SMOKE["ext"], SMOKE["asr_only"], True,
              "≈ 1–2 h (computed: chb17 21 h + PN00 3.2 h + 5 h of ASR-only files at the laptop's 135 s per hour of EEG "
              "on 3 processes, up to 3 × on Kaggle, + features ≈ 0.3 h)")
    if a.data:
        split = json.loads(subprocess.check_output(["git", "-C", str(ROOT), "show",
                                                    f"{a.data}:results/fa15/smoke/split.json"]))
        for part, d in split.items():
            chb = [c for c in d["cases"] if c.startswith("chb") and c != "chb24"]
            ext = [c for c in d["cases"] if c == "chb24" or c.startswith("PN")]
            build(f"FA15_DATA_{part.upper()}", a.data, part, chb, ext, [], False,
                  f"≈ {d['computed_wall_h']} h (computed from the smoke's measured rates; {d['hours']} h of EEG)")


if __name__ == "__main__":
    main()
