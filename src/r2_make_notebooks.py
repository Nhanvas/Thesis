#!/usr/bin/env python
"""r2_make_notebooks.py -- builds the stage R0 Kaggle notebooks of the independent track (docs/FUTURE_RESEARCH_PLAN.md
rev 2, §4 and §9) from src/r2_core.py (embedded verbatim with %%writefile; sha256 checked in the notebook). The
repository is cloned at the pinned commit for the record code it imports read only (preprocessing, c1b, chb24 builder,
x1_external, committed stats.json, summaries, x1 rows). Nothing to fill in.
  python src/r2_make_notebooks.py            -> notebooks/r2/R0_SMOKE.ipynb, R0_CHB.ipynb, R0_EXT.ipynb
Test mode (synthetic data, build container only): environment R2_TEST_REPO / R2_TEST_INPUT / R2_TEST_WORK /
R2_TEST_SCRATCH / R2_TEST_CASES / R2_PHYSIONET_* (src/r2_synthetic_test.py)."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "235682a652392ec40fc001ff5ad60dfa77fa8e28"
OUTDIR = ROOT / "notebooks" / "r2"
CORE = (ROOT / "src" / "r2_core.py").read_text()
SHA = hashlib.sha256(CORE.encode()).hexdigest()[:16]
RAW = "bonesclarke26/combined-siena-scalp-and-chb-mit-eeg-datasets"
PKGS = '"mne==1.12.1", "torch_geometric==2.7.0", "ruptures==1.1.10", "timescoring==0.0.7"'


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.strip("\n").splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": t.strip("\n").splitlines(keepends=True)}


def head(name, what, inputs, outputs, est):
    return md(f"""
# {name} — independent track, stage R0 (data rebuild on complete data)

**Plan:** `docs/FUTURE_RESEARCH_PLAN.md` rev 2, §4 and §9. **Does:** {what}
**Accelerator:** None (CPU). **Internet:** ON (PhysioNet `SHA256SUMS.txt` and any file that is absent or different on
Kaggle). **Inputs:** {inputs}. **Outputs:** {outputs}. **Runtime:** {est}.
Code: `github.com/Nhanvas/Thesis` at `{COMMIT[:7]}` (record code, read only) + `r2_core.py` below (sha256 `{SHA}`).
Gates STOP the notebook (the cell raises `STOPPED: ...`); nothing after a failed gate is written. **Nothing printed here is
a result** of the research; it is data preparation. Do not edit; *Save Version → Save & Run All (Commit)*.
""")


def setup(name):
    return code(f"""
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
    if not os.path.exists(REPO + "/src/c1b_build_trainset.py"):
        r = subprocess.run(f"git init -q {{REPO}} && cd {{REPO}} && git remote add origin https://github.com/Nhanvas/Thesis.git "
                           f"&& git fetch -q --depth 1 origin {{REPO_COMMIT}} && git checkout -q FETCH_HEAD", shell=True)
        if r.returncode != 0:
            subprocess.check_call(f"rm -rf {{REPO}} && git clone -q https://github.com/Nhanvas/Thesis.git {{REPO}} "
                                  f"&& cd {{REPO}} && git checkout -q {{REPO_COMMIT}}", shell=True)
    head = subprocess.check_output(["git", "-C", REPO, "rev-parse", "HEAD"]).decode().strip()
    assert head == REPO_COMMIT, f"wrong commit {{head}}"
print("repository", REPO, f"({{time.time()-T_NB:.0f}}s)")
""")


def start(tag):
    return code(f"""
# START: sha check of the embedded file, imports, run metadata
sha = hashlib.sha256(open(f"{{SRC}}/r2_core.py", "rb").read()).hexdigest()[:16]
assert sha == "{SHA}", f"r2_core.py: sha {{sha}} != {SHA} (cell edited?)"
os.environ.update(THESIS_REPO=REPO, R2_WORK=WORK, R2_INPUT=INPUT, R2_SCRATCH=SCRATCH)
sys.path.insert(0, SRC)
import pandas as pd, numpy as np
import r2_core as R
print("CPU cores:", os.cpu_count())
META = R.run_meta("{tag}", NOTEBOOK, REPO_COMMIT)
CASES = os.environ["R2_TEST_CASES"].split(",") if os.environ.get("R2_TEST_CASES") else None
def stopped(e):
    raise RuntimeError(f"STOPPED: {{e}}") from None
""")


def end(extra=""):
    return code(f"""
# END: measured runtime and the list of outputs
{extra}
meta = R.finish_meta()
print(f"MEASURED notebook runtime: {{meta['runtime_h']}} h | phases (s): {{meta['phases_s']}}")
print(json.dumps(meta["rates"], indent=1))
for d in (R.out_dir(), R.DS_CHB, R.DS_EXT):
    if d.exists():
        print(d, "->", sorted(p.name for p in d.iterdir())[:60])
""")


def save(name, cells):
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                       "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / f"{name}.ipynb").write_text(json.dumps(nb, indent=1))
    return OUTDIR / f"{name}.ipynb"


def smoke():
    n = "R0_SMOKE"
    return save(n, [
        head(n, "R0.1 inventory of **every** CHB-MIT and Siena file (sha256 vs PhysioNet, missing files downloaded); "
                "G-stats on the whole earlier chb11 file set; G-feat on chb11's first 2 files; a parallel probe (one other "
                "chb11 file per worker, G-feat on each) to measure speed under load; x1-convention features of PN00 "
                "(speed, memory, hours vs the x1 record); projection of R0_CHB and R0_EXT.",
             f"`{RAW}` (raw EEG) + `v9-x3-fold1` + `v9-x3-fold3` (earlier features)",
             "`/kaggle/working/r2/r0_data/smoke/` (inventory, checks, gates, projection, logs); no dataset",
             "measured (expected well under 2 h)"),
        setup(n), code("%%writefile {SRC}/r2_core.py\n" + CORE), start("smoke"),
        code("""
# R0.1 INVENTORY: PhysioNet SHA256SUMS -> every needed file hashed (Kaggle copy, else PhysioNet download) -> views
try:
    INV, CASES_DF, COMPLETE, EARLIER = R.inventory({"chbmit": None, "siena": None})
except SystemExit as e:
    stopped(e)
print(CASES_DF.to_string(index=False))
print(json.load(open(R.out_dir() / "checks.json")))
"""),
        code("""
# R0.2 SMOKE GATES on chb11 (earlier file set): G-stats (whole set), G-feat (first 2 files), parallel probe
try:
    G = R.smoke_probe_files(CASES_DF, EARLIER, case="chb11", n_first=2)
except SystemExit as e:
    stopped(e)
print(json.dumps(G, indent=1, default=str)[:4000])
"""),
        code("""
# R0.4 SMOKE: PN00 with the x1 convention (label-free statistics) -> speed, memory, hours vs the x1 record
try:
    EXT = R.run_ext(CASES_DF, COMPLETE, ["PN00"], out_folder=R.SCRATCH / "smoke_ext")
except SystemExit as e:
    stopped(e)
print(EXT.to_string(index=False))
r = EXT.iloc[0]
EXT_RATE = float(r.wall_s) / float(r.hours)
"""),
        code("""
# PROJECTION (computed estimate from the measurements above): wall time of R0_CHB and R0_EXT; split if > 10.5 h
PROJ = R.projection(CASES_DF, ext_rate_s_per_h=EXT_RATE)
print(json.dumps(PROJ, indent=1))
"""),
        end(),
    ])


def chb():
    n = "R0_CHB"
    return save(n, [
        head(n, "R0.1 inventory of CHB-MIT (24 cases); R0.2 gates G-stats (23 cases) and G-feat (24 cases) on the earlier "
                "file set — for the 22 cases without a gap (and chb24) this build is the new data; R0.3 chb11 and chb21 "
                "on every file + diff report. Writes the dataset folder only after every gate passed.",
             f"`{RAW}` (raw EEG) + `v9-x3-fold1` + `v9-x3-fold3` (earlier features)",
             "`/kaggle/working/thesis-r2-chbmit-features/` (→ dataset `thesis-r2-chbmit-features`) and "
             "`/kaggle/working/r2/r0_data/chb/` (→ `results/r2/r0_data/chb/`)",
             "see `projection.json` of R0_SMOKE"),
        setup(n), code("%%writefile {SRC}/r2_core.py\n" + CORE), start("chb"),
        code("""
# R0.1 INVENTORY (CHB-MIT)
try:
    INV, CASES_DF, COMPLETE, EARLIER = R.inventory({"chbmit": CASES})
except SystemExit as e:
    stopped(e)
print(CASES_DF.to_string(index=False))
"""),
        code("""
# R0.2 + R0.3: every case on the earlier view (G-stats, build, G-feat; STOP at the first failure), then chb11 / chb21
# on the complete view; dataset folder + diff report only after every gate passed
try:
    GATES, DONE = R.run_chb(CASES_DF, COMPLETE, EARLIER, cases=CASES)
except SystemExit as e:
    stopped(e)
print("G-stats:", {c: g["status"] for c, g in GATES["G_stats"].items()})
print("G-feat:", {c: g["status"] for c, g in GATES["G_feat"].items()})
print(open(R.out_dir() / "diff_chb11_chb21.md").read() if (R.out_dir() / "diff_chb11_chb21.md").exists() else "")
"""),
        end(),
    ])


def ext():
    n = "R0_EXT"
    return save(n, [
        head(n, "R0.1 inventory of chb24 + Siena; R0.4 x1-convention features (label-free statistics) of chb24 and the 14 "
                "Siena patients, saved as `{case}_lf.npz`; hours and non-ictal hours compared with the x1 record "
                "(descriptive; feature identity is gate GE of R1). Resumes from a previous version's output if attached.",
             f"`{RAW}` (raw EEG); to resume, also this notebook's previous output",
             "`/kaggle/working/thesis-r2-external-features/` (→ dataset `thesis-r2-external-features`) and "
             "`/kaggle/working/r2/r0_data/ext/` (→ `results/r2/r0_data/ext/`)",
             "see `projection.json` of R0_SMOKE"),
        setup(n), code("%%writefile {SRC}/r2_core.py\n" + CORE), start("ext"),
        code("""
# R0.1 INVENTORY (chb24 + Siena)
R.import_previous(R.DS_EXT, "*_lf.npz")
try:
    INV, CASES_DF, COMPLETE, EARLIER = R.inventory({"chbmit": ["chb24"], "siena": None})
except SystemExit as e:
    stopped(e)
print(CASES_DF.to_string(index=False))
EXT_CASES = ["chb24"] + sorted(CASES_DF[CASES_DF.db == "siena"].case)
print(EXT_CASES)
"""),
        code("""
# R0.4: external features, one subject at a time (x1_external.build_subject, unchanged)
try:
    EXT = R.run_ext(CASES_DF, COMPLETE, EXT_CASES)
except SystemExit as e:
    stopped(e)
print(EXT.to_string(index=False))
print("Siena hours:", round(EXT[EXT.case.str.startswith("PN")].hours.sum(), 2), "| chb24 hours:", EXT[EXT.case == "chb24"].hours.tolist())
"""),
        end(),
    ])


if __name__ == "__main__":
    built = [smoke(), chb(), ext()]
    print("built", [b.name for b in built], "r2_core sha", SHA)
