#!/usr/bin/env python
"""r2_r1_make_notebooks.py -- builds the stage R1 Kaggle notebooks of the independent track (docs/FUTURE_RESEARCH_PLAN.md
rev 2, §5 and §9; plan §12 rows from 07/11 D15-F) from src/r2_r1.py (embedded verbatim with %%writefile; sha256 checked
in the notebook). The repository is cloned at a pinned commit for the record code, the committed checkpoints and
results it reads, and r2_core.py (stage R0, sha checked). Nothing to fill in.
  python src/r2_r1_make_notebooks.py                 -> notebooks/r2/R1_SMOKE.ipynb (clone pinned at tag r2-r0)
  python src/r2_r1_make_notebooks.py --run <commit>  -> also notebooks/r2/R1_RUN.ipynb, cloned at <commit>, which must
                                                        hold the committed R1_SMOKE output (data hashes are pinned to it)
Test mode (synthetic data, build container only): environment R2_TEST_REPO / R2_TEST_INPUT / R2_TEST_WORK /
R2_TEST_SCRATCH (src/r2_r1_synthetic_test.py)."""
import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE_COMMIT = "1b83b03996ebcc655825a735c076753838cd6a2d"            # tag r2-r0 (plan §12 row 07/11 15:48)
R0_SHA = "902d15ad4feb3e8a"                                         # r2_core.py of stage R0 (dataset provenance)
OUTDIR = Path(os.environ.get("R2_NB_OUTDIR", ROOT / "notebooks" / "r2"))          # env: synthetic test only
CORE = (ROOT / "src" / "r2_r1.py").read_text()
SHA = hashlib.sha256(CORE.encode()).hexdigest()[:16]
PKGS = '"mne==1.12.1", "torch_geometric==2.7.0", "ruptures==1.1.10", "timescoring==0.0.7"'
INPUTS = ("`thesis-r2-chbmit-features` + `thesis-r2-external-features` (R0 datasets) + `v9-x3-fold1` + `v9-x3-fold3` "
          "(earlier features of the record; R0 found all 24 cases in these two)")


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.strip("\n").splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": t.strip("\n").splitlines(keepends=True)}


def head(name, commit, what, inputs, outputs, est):
    return md(f"""
# {name} — independent track, stage R1 (the thesis system on complete data)

**Plan:** `docs/FUTURE_RESEARCH_PLAN.md` rev 2, §5 and §9; implementation choices in §12 (07/11 D15-F). **Does:** {what}
**Accelerator:** None (CPU). **Internet:** ON (package install and repository clone only). **Inputs:** {inputs}.
**Outputs:** {outputs}. **Runtime:** {est}.
Code: `github.com/Nhanvas/Thesis` at `{commit[:7]}` (record code, committed checkpoints and results, `r2_core.py` sha
`{R0_SHA}`; all read only) + `r2_r1.py` below (sha256 `{SHA}`). Gates STOP the notebook (the cell raises
`STOPPED: ...`). **Nothing printed here is a research result.** Do not edit; *Save Version → Save & Run All (Commit)*.
""")


def setup(name, commit):
    return code(f"""
# SETUP: packages + repository at the pinned commit (read only)
import os, sys, subprocess, time, json, hashlib
T_NB = time.time()
os.environ["R2_T0"] = str(T_NB)
NOTEBOOK, REPO_COMMIT = "{name}", "{commit}"
TEST = bool(os.environ.get("R2_TEST_REPO"))                      # synthetic test in the build container only
WORK = os.environ.get("R2_TEST_WORK", "/kaggle/working")
INPUT = os.environ.get("R2_TEST_INPUT", "/kaggle/input")
SCRATCH = os.environ.get("R2_TEST_SCRATCH", "/tmp/r2")
SRC = SCRATCH + "/src_r1"
os.makedirs(SRC, exist_ok=True)
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
if TEST:
    REPO = os.environ["R2_TEST_REPO"]
else:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", {PKGS}])
    REPO = "/tmp/Thesis"
    if not os.path.exists(REPO + "/src/r2_core.py"):
        r = subprocess.run(f"git init -q {{REPO}} && cd {{REPO}} && git remote add origin https://github.com/Nhanvas/Thesis.git "
                           f"&& git fetch -q --depth 1 origin {{REPO_COMMIT}} && git checkout -q FETCH_HEAD", shell=True)
        if r.returncode != 0:
            subprocess.check_call(f"rm -rf {{REPO}} && git clone -q https://github.com/Nhanvas/Thesis.git {{REPO}} "
                                  f"&& cd {{REPO}} && git checkout -q {{REPO_COMMIT}}", shell=True)
    head = subprocess.check_output(["git", "-C", REPO, "rev-parse", "HEAD"]).decode().strip()
    assert head == REPO_COMMIT, f"wrong commit {{head}}"
r0 = hashlib.sha256(open(REPO + "/src/r2_core.py", "rb").read()).hexdigest()[:16]
assert TEST or r0 == "{R0_SHA}", f"r2_core.py sha {{r0}} != {R0_SHA}"
print("repository", REPO, f"({{time.time()-T_NB:.0f}}s)")
""")


def start(tag):
    return code(f"""
# START: sha check of the embedded file, imports, run metadata
sha = hashlib.sha256(open(f"{{SRC}}/r2_r1.py", "rb").read()).hexdigest()[:16]
assert sha == "{SHA}", f"r2_r1.py: sha {{sha}} != {SHA} (cell edited?)"
os.environ.update(THESIS_REPO=REPO, R2_WORK=WORK, R2_INPUT=INPUT, R2_SCRATCH=SCRATCH)
sys.path.insert(0, SRC)
import pandas as pd, numpy as np
import torch
torch.set_num_threads(1)
import r2_r1 as R1
print("CPU cores:", os.cpu_count(), "| torch threads:", torch.get_num_threads(), "| workers:", R1.n_workers())
META = R1.run_meta("{tag}", NOTEBOOK, REPO_COMMIT)
def stopped(e):
    raise RuntimeError(f"STOPPED: {{e}}") from None
""")


def end():
    return code("""
# END: SUMMARY.md, measured runtime, list of outputs
print(R1.summary_md())
meta = R1.finish_meta()
print(f"MEASURED notebook runtime: {meta['runtime_h']} h | phases (s): {meta['phases_s']}")
for p in sorted(R1.out_dir().rglob("*")):
    if p.is_file():
        print(p.relative_to(R1.OUT_ROOT), p.stat().st_size)
""")


def save(name, cells):
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                       "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / f"{name}.ipynb").write_text(json.dumps(nb, indent=1))
    return OUTDIR / f"{name}.ipynb"


def smoke():
    n = "R1_SMOKE"
    return save(n, [
        head(n, SMOKE_COMMIT,
             "G-data (the attached R0 datasets: every file hashed, statistics and window counts = R0's committed outputs, "
             "R0's G-feat re-read on the 13 cases this notebook reads); G-const and G-count (earlier data = committed "
             "checkpoint metas); **R1.0 on chb01 (development) and chb03 (test)** and **GE on PN00** with the committed "
             "checkpoints; **G-vec** on the thesis recipe (`train_gae_v2.py --smoke` verbatim vs the tensor loop); a "
             "**2-epoch training job** per seed on the full new training data (4 workers, speed under load); the R1.3 "
             "code path once on the 2-epoch models (chb01 + chb10 for k, chb03, PN00; written, not read); projection "
             "of R1_RUN (computed estimate).",
             INPUTS, "`/kaggle/working/r2/r1_system/smoke/` (→ `results/r2/r1_system/smoke/`)",
             "measured (computed estimate ≈ 0.7–1.5 h)"),
        setup(n, SMOKE_COMMIT), code("%%writefile {SRC}/r2_r1.py\n" + CORE), start("smoke"),
        code("""
# VIEWS + G-data: the attached datasets are R0's outputs (sha256 recorded); R0's G-feat re-read on the cases read here
FEAT = [c for c in R1.TRAIN if c not in R1.GAP] + ["chb03", "chb10"]
try:
    V = R1.build_views()
    G = R1.gate_data(V, feat_cases=FEAT, workers=R1.n_workers())
except SystemExit as e:
    stopped(e)
print({c: d["ok"] for c, d in G["detail"].items()})
print({c: (r["status"], r.get("f7"), r.get("bp5"), r.get("adj")) for c, r in G["gfeat_reread"].items()})
"""),
        code("""
# G-const + G-count on the earlier data (train_gae_v2.norm_constants and clean masks = the committed checkpoint metas)
try:
    R1.gate_const_count()
except SystemExit as e:
    stopped(e)
"""),
        code("""
# R1.0 (chb01 development, chb03 test) + GE (PN00): committed checkpoints reproduce the record (exact / tolerance)
try:
    R10, R10_TIMING = R1.r10(["chb01"], ["chb03"], ["PN00"])
except SystemExit as e:
    stopped(e)
for g in R10:
    print(g["gate"], g["status"], "|", g["summary"])
print(R10_TIMING[["case", "src", "eeg_h", "valid", "d_s", "score_s", "peak_rss_mb"]].to_string(index=False))
"""),
        code("""
# G-vec on the thesis recipe: train_gae_v2.py --smoke (verbatim) vs the tensor loop, new chb01, 2,000 windows, 2 epochs
try:
    GV = R1.gate_vec(seed=42)
except SystemExit as e:
    stopped(e)
print(GV["summary"], "| exact:", GV["exact"])
"""),
        code("""
# 2-EPOCH JOBS: the R1.1 job on the full new training data, 4 seeds in parallel (1 thread each): counts, G2, speed
SM = R1.out_dir() / "models"
try:
    TS = R1.train_seeds(V, [42, 1, 2, 3], 2, SM, R1.out_dir() / "training", smoke=True)
except SystemExit as e:
    stopped(e)
print(pd.DataFrame(TS)[["seed", "n_train", "ms_per_step", "fit_s", "load_s", "val_and_sanity_s", "peak_rss_mb"]].to_string(index=False))
"""),
        code("""
# R1.3 CODE PATH on the 2-epoch models (not a result: files written under r13/path_check, nothing printed from them)
try:
    K, _, _ = R1.r13(["chb01", "chb10"], ["chb03"], ["PN00"], SM, "path_check")
except SystemExit as e:
    stopped(e)
print("R1.3 path ran:", sorted(p.name for p in (R1.out_dir() / "r13" / "path_check").iterdir()))
"""),
        code("""
# PROJECTION of R1_RUN (computed estimate from the measurements above)
gfeat_s = R1.STATE["phases"]["gate_data"] / max(1, len(FEAT))
PROJ = R1.projection(R10_TIMING, TS, V, gfeat_s_per_case=gfeat_s)
print(json.dumps(PROJ, indent=1))
"""),
        end(),
    ])


def run(commit):
    n = "R1_RUN"
    return save(n, [
        head(n, commit,
             "G-data (hashes pinned to R1_SMOKE's committed `data_sha256.csv`; R0's G-feat re-read on the 22 gap-free "
             "cases); G-const, G-count; **R1.0 in full** (15 development + 8 test cases, 4 seeds, every record row) + "
             "**G-k** + **GE** (chb24 + Siena 14); G-vec; **R1.1** training of 4 seeds, 200 epochs (4 workers; refused "
             "if the measured step time projects past the session); **R1.2** k; **R1.3** scoring of every set. "
             "**Resumable:** attach this notebook's previous output and finished seeds are reused (code sha and "
             "checkpoint hash checked).",
             INPUTS + "; to resume, also this notebook's previous output",
             "`/kaggle/working/r2/r1_system/run/` (→ `results/r2/r1_system/run/`; checkpoints ≈ 20 KB each)",
             "see `projection.json` of R1_SMOKE"),
        setup(n, commit), code("%%writefile {SRC}/r2_r1.py\n" + CORE), start("run"),
        code("""
# RESUME + VIEWS + G-data (hashes pinned to the smoke's)
MODELS = R1.out_dir() / "models"
R1.import_models(MODELS)
PIN = R1.REPO / "results" / "r2" / "r1_system" / "smoke" / "data_sha256.csv"
assert PIN.exists() or os.environ.get("R2_TEST"), "the pinned commit lacks R1_SMOKE's data_sha256.csv"
try:
    V = R1.build_views()
    G = R1.gate_data(V, feat_cases=[c for c in R1.CHB if c not in R1.GAP], workers=R1.n_workers(), pin=PIN)
except SystemExit as e:
    stopped(e)
"""),
        code("""
# G-const + G-count; R1.0 in full + G-k + GE (committed checkpoints, earlier data / R0.4 features)
try:
    R1.gate_const_count()
    R10, R10_TIMING = R1.r10(R1.DEV, R1.TEST, R1.EXT, with_k=True)
except SystemExit as e:
    stopped(e)
for g in R10:
    print(g["gate"], g["status"], "|", g["summary"])
"""),
        code("""
# G-vec; step timing (4 concurrent workers) -> projected training hours; R1.1 training, 4 seeds x 200 epochs
try:
    R1.gate_vec(seed=42)
    TT = R1.step_timing()
    EPOCHS = int(os.environ.get("R2_TEST_EPOCHS", 200)) if TEST else 200        # the recipe: 200 (test mode only fewer)
    exp, _ = R1.expected_counts(V)
    proj_h = (int(np.ceil(sum(exp.values()) / 32)) * EPOCHS * max(TT["ms_per_step"]) / 1000 + 900) / 3600
    R1.STATE["notes"].append(dict(step_timing=TT, projected_training_h=round(proj_h, 2)))
    print("step timing", TT, "| projected training (computed estimate):", round(proj_h, 2), "h")
    TS = R1.train_seeds(V, [42, 1, 2, 3], EPOCHS, MODELS, R1.out_dir() / "training", projected_h=proj_h)
except SystemExit as e:
    stopped(e)
print(pd.DataFrame(TS)[["seed", "n_train", "ms_per_step", "fit_s", "peak_rss_mb"]].to_string(index=False))
"""),
        code("""
# R1.2 k + R1.3 scoring of every set with the new checkpoints (written; read only by the committed aggregate script)
try:
    K, _, _ = R1.r13(R1.DEV, R1.TEST, R1.EXT, MODELS, "run")
except SystemExit as e:
    stopped(e)
print("R1.3 written:", sorted(p.name for p in (R1.out_dir() / "r13" / "run").iterdir()))
"""),
        end(),
    ])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", metavar="COMMIT", help="also build R1_RUN, cloned at COMMIT (must hold R1_SMOKE's output)")
    a = ap.parse_args()
    built = [smoke()] + ([run(a.run)] if a.run else [])
    print("built", [b.name for b in built], "r2_r1 sha", SHA)
