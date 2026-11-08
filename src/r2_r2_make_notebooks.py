#!/usr/bin/env python
"""r2_r2_make_notebooks.py -- builds the stage R2 Kaggle notebooks of the independent track (docs/FUTURE_RESEARCH_PLAN.md
rev 2, §6 and §9; §12 row 08/11, chat D16-F) from src/r2_r2.py (embedded verbatim with %%writefile; sha256 checked in
the notebook). The repository is cloned at a pinned git ref (tag or commit; the resolved commit is recorded in
run_meta.json) for the closed code, the committed checkpoints and the record results. Nothing to fill in.
  python src/r2_r2_make_notebooks.py --smoke REF        -> notebooks/r2/R2_SMOKE.ipynb (REF must hold src/r2_r2.py's
                                                         inputs: R1_SMOKE's data_sha256.csv, the R0 diff report and, if
                                                         approved, results/model_cmp/ckpt/cnn_fold*.pt)
  python src/r2_r2_make_notebooks.py --runs COMMIT      -> notebooks/r2/R2_A / R2_B / R2_C.ipynb, cloned at COMMIT (a
                                                         commit hash, never a tag), which must hold the committed R2_SMOKE
                                                         output (projection.json) and the CNN checkpoints
R2_C (plan §12 08/11 19:10, chat D17-F): gate R2.0-cnn runs FIRST -- the committed CNN fold checkpoints (all four must be
in the pinned repository; sha256 recorded) scored on the earlier data = the record's CNN rows within |dtp| <= 1,
|dfp| <= 2 per row (the 08/11 09:30 tolerance); the notebook STOPs before any CNN training on failure. R2_C runs on at
most 2 workers (CNN training memory was not measured by R2_SMOKE). src/r2_r2.py is unchanged (= the smoke's code).
Test mode (synthetic data, build container only): environment R2_TEST_REPO / R2_TEST_INPUT / R2_TEST_WORK /
R2_TEST_SCRATCH (src/r2_r2_synthetic_test.py)."""
import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R0_SHA = "902d15ad4feb3e8a"                                         # r2_core.py of stage R0 (dataset provenance)
OUTDIR = Path(os.environ.get("R2_NB_OUTDIR", ROOT / "notebooks" / "r2"))
CORE = (ROOT / "src" / "r2_r2.py").read_text()
SHA = hashlib.sha256(CORE.encode()).hexdigest()[:16]
PKGS = '"mne==1.12.1", "torch_geometric==2.7.0", "ruptures==1.1.10", "timescoring==0.0.7"'
INPUTS = ("`thesis-r2-chbmit-features` (R0 dataset) + `v9-x3-fold1` + `v9-x3-fold3` (the record's earlier features; "
          "all 24 cases are in these two)")


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.strip("\n").splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": t.strip("\n").splitlines(keepends=True)}


def head(name, ref, what, outputs, est):
    return md(f"""
# {name} — independent track, stage R2 (four-fold CV and six models on complete data)

**Plan:** `docs/FUTURE_RESEARCH_PLAN.md` rev 2, §6 and §9; implementation in §12 (08/11, D16-F). **Does:** {what}
**Accelerator:** None (CPU). **Internet:** ON (package install and repository clone only). **Inputs:** {INPUTS}.
**Outputs:** {outputs}. **Runtime:** {est}.
Code: `github.com/Nhanvas/Thesis` at `{ref}` (closed code, committed checkpoints and record results, all read only; the
resolved commit is written to `run_meta.json`) + `r2_r2.py` below (sha256 `{SHA}`). Gates STOP the notebook (the cell
raises `STOPPED: ...`). **Nothing printed here is a research result.** Do not edit; *Save Version → Save & Run All (Commit)*.
""")


def setup(name, ref):
    return code(f"""
# SETUP: packages + repository at the pinned ref (read only)
import os, sys, subprocess, time, json, hashlib
T_NB = time.time()
os.environ["R2_T0"] = str(T_NB)
NOTEBOOK, REPO_REF = "{name}", "{ref}"
TEST = bool(os.environ.get("R2_TEST_REPO"))                      # synthetic test in the build container only
WORK = os.environ.get("R2_TEST_WORK", "/kaggle/working")
INPUT = os.environ.get("R2_TEST_INPUT", "/kaggle/input")
SCRATCH = os.environ.get("R2_TEST_SCRATCH", "/tmp/r2")
SRC = SCRATCH + "/src_r2"
os.makedirs(SRC, exist_ok=True)
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
if TEST:
    REPO = os.environ["R2_TEST_REPO"]
    REPO_COMMIT = "synthetic"
else:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", {PKGS}])
    REPO = "/tmp/Thesis"
    if not os.path.exists(REPO + "/src/r2_core.py"):
        subprocess.check_call(f"rm -rf {{REPO}} && git clone -q https://github.com/Nhanvas/Thesis.git {{REPO}} "
                              f"&& cd {{REPO}} && git checkout -q {{REPO_REF}}", shell=True)
    REPO_COMMIT = subprocess.check_output(["git", "-C", REPO, "rev-parse", "HEAD"]).decode().strip()
r0 = hashlib.sha256(open(REPO + "/src/r2_core.py", "rb").read()).hexdigest()[:16]
assert TEST or r0 == "{R0_SHA}", f"r2_core.py sha {{r0}} != {R0_SHA}"
print("repository", REPO, "at", REPO_REF, "=", REPO_COMMIT, f"({{time.time()-T_NB:.0f}}s)")
""")


def start(tag):
    return code(f"""
# START: sha check of the embedded file, imports, run metadata
sha = hashlib.sha256(open(f"{{SRC}}/r2_r2.py", "rb").read()).hexdigest()[:16]
assert sha == "{SHA}", f"r2_r2.py: sha {{sha}} != {SHA} (cell edited?)"
os.environ.update(THESIS_REPO=REPO, R2_WORK=WORK, R2_INPUT=INPUT, R2_SCRATCH=SCRATCH)
sys.path.insert(0, SRC)
import pandas as pd, numpy as np
import torch
torch.set_num_threads(1)
import r2_r2 as R2
print("CPU cores:", os.cpu_count(), "| RAM GB:", round(R2._ram_gb(), 1), "| workers:", R2.n_workers())
META = R2.run_meta("{tag}", NOTEBOOK, REPO_COMMIT)
def stopped(e):
    raise RuntimeError(f"STOPPED: {{e}}") from None
""")


DATA = """
# VIEWS + G-data (sha256 = R1_SMOKE's pinned hashes) + D0' and the new fold constants (new data)
try:
    SRCS = R2.build_views()
    R2.gate_data(SRCS)
    R2.use_view("new")
    R2.gate_d0prime()
    METAS = R2.new_metas()
    SUPN = R2.sup_counts()
except SystemExit as e:
    stopped(e)
print(pd.DataFrame(R2.const_report(METAS)).to_string(index=False))
print("supervised training windows per fold:", SUPN)
"""

EARLIER = """
# G-const, G-vec, G-mlp on the earlier data (f1_core, unchanged)
try:
    R2.use_view("earlier")
    R2.gates_earlier()
except SystemExit as e:
    stopped(e)
"""


def end():
    return code("""
# END: SUMMARY.md, measured runtime, list of outputs
print(R2.summary_md())
meta = R2.finish_meta()
print(f"MEASURED notebook runtime: {meta['runtime_h']} h | phases (s): {meta['phases_s']}")
for p in sorted(R2.out_dir().rglob("*")):
    if p.is_file() and "/jobs/" not in str(p) and "/cfjobs/" not in str(p):
        print(p.relative_to(R2.OUT_ROOT), p.stat().st_size)
""")


def save(name, cells):
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                       "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / f"{name}.ipynb").write_text(json.dumps(nb, indent=1))
    return OUTDIR / f"{name}.ipynb"


def smoke(ref):
    n = "R2_SMOKE"
    return save(n, [
        head(n, ref,
             "G-data, D0′ and the new fold constants; G-const, G-vec, G-mlp (earlier data); **R2.0** — the record's code "
             "paths on the earlier data with the committed models (GAE folds exactly = `results/v9_x3`; Isolation Forest "
             "and gradient-boosted trees, 4 folds, and linear SVM fold 1, exactly = `results/model_cmp`; MLP-AE and CNN "
             "checkpoints within |Δtp| ≤ 1, |Δfp| ≤ 2 per row); step timing of the autoencoders and the CNN with 4 "
             "concurrent workers; a small end-to-end job of every model on the new data and one counterfactual job "
             "(code path; written, not read); projection of R2_A / R2_B / R2_C (computed estimate).",
             "`/kaggle/working/r2/r2_cv/smoke/` (→ `results/r2/r2_cv/smoke/`)",
             "measured (computed estimate ≈ 1.5–2.5 h; the SVM fold-1 gate ≈ 1 h runs beside the others)"),
        setup(n, ref), code("%%writefile {SRC}/r2_r2.py\n" + CORE), start("smoke"), code(DATA), code(EARLIER),
        code("""
# TIMING: ms per training step (GAE, MLP-AE, CNN) with 4 concurrent workers, on real windows (earlier view)
try:
    TIMING = R2.run_jobs([dict(stage="timing", name=f"t{i}", kind="timing", view="earlier") for i in range(4)], 4)
except SystemExit as e:
    stopped(e)
print([t.get("timing") for t in TIMING])
"""),
        code("""
# R2.0: the record's code paths on the earlier data with the committed models (exact / tolerance; module docstring)
try:
    R20 = R2.run_jobs(R2.r20_specs(cnn=R2.cnn_ckpt(1).exists()), R2.n_workers())
    R20_READ = R2.r20_read(R20)
except SystemExit as e:
    stopped(e)
print(pd.DataFrame([dict(name=r["name"], status=r["status"], seconds=r.get("seconds"), peak_mb=r.get("peak_rss_mb"))
                    for r in R20]).to_string(index=False))
"""),
        code("""
# CODE PATH on the new data: a small job per model (2 epochs / small subsets) + one counterfactual fold (not read)
try:
    SM = R2.run_jobs(R2.run_specs(["gae", "mlp", "if", "hgb", "svm", "cnn"], METAS, smoke=True, epochs=2)
                     + [dict(s, stage="smoke") for s in R2.cf_specs(["gae"], folds=[1])], R2.n_workers())
except SystemExit as e:
    stopped(e)
bad = [r for r in SM if r["status"] not in ("done", "reused")]
if bad:
    stopped(f"smoke jobs failed: {bad}")
print(pd.DataFrame([dict(name=r["name"], status=r["status"], seconds=r.get("seconds"), peak_mb=r.get("peak_rss_mb"))
                    for r in SM]).to_string(index=False))
"""),
        code("""
# PROJECTION of R2_A / R2_B / R2_C (computed estimate from the measurements above)
PROJ = R2.projection(TIMING, R20, METAS, SUPN)
print(json.dumps({k: PROJ[k] for k in ("ms_per_step", "workers", "wall_h", "fits", "peak_gb")}, indent=1))
"""),
        end(),
    ])


CNN_GATE = """
# R2.0-cnn FIRST (plan §12 08/11 19:10): the committed CNN fold checkpoints on the EARLIER data, CPU scoring = the record's
# CNN rows (results/model_cmp/per_subject.csv) within |dtp| <= 1, |dfp| <= 2 per row, n_ref exact; exact rows counted.
# All four checkpoints must be present (sha256 recorded). STOP here, before any CNN training, on any failure.
W = min(int(PROJ["workers"]["R2_C"]), W_CAP)
try:
    MISSING = [f for f in R2.FOLDS if not R2.cnn_ckpt(f).exists()]
    if MISSING:
        raise SystemExit(f"STOP R2.0-cnn: CNN checkpoints absent from the pinned repository for folds {MISSING}")
    CKPT = {f"cnn_fold{f}.pt": R2.sha256_file(R2.cnn_ckpt(f)) for f in R2.FOLDS}
    G0 = R2.run_jobs([s for s in R2.r20_specs(cnn=True) if s["model"] == "cnn"], W)
    BAD = [r for r in G0 if r.get("status") not in ("done", "reused")]
    if BAD:
        R2.gate(dict(gate="R2.0-jobs", status="FAIL", failed=BAD, summary=f"{len(BAD)} R2.0-cnn jobs failed"))
    JD = R2.out_dir() / "r20"
    ROWS = sum((pd.read_csv(JD / f"cnn_f{f}" / "per_subject.csv").to_dict("records") for f in R2.FOLDS), [])
    CG = R2._compare(ROWS, "cnn", "tolerance")
    R2._jdump(JD / "r20_summary.json", dict(cnn=CG, checkpoints_sha256=CKPT))
    R2.gate(dict(gate="R2.0-cnn", **CG, checkpoints_sha256=CKPT,
                 summary=f"{CG['rows']} rows, {CG['exact_rows']} exact, max |dtp| {CG['max_abs_dtp']}, |dfp| "
                         f"{CG['max_abs_dfp']}, own-point k rel {CG['k_max_rel']:.1e} (tolerance)"))
except SystemExit as e:
    stopped(e)
print(pd.DataFrame([dict(name=r["name"], status=r["status"], seconds=r.get("seconds"), peak_mb=r.get("peak_rss_mb"))
                    for r in G0]).to_string(index=False))
"""


def _proj_text():
    """runtime line of each run notebook from the committed R2_SMOKE projection (computed estimate)."""
    p = ROOT / "results" / "r2" / "r2_cv" / "smoke" / "projection.json"
    if not p.exists():
        return {n: "R2_SMOKE projection" for n in ("R2_A", "R2_B", "R2_C")}
    w = json.loads(p.read_text())["wall_h"]
    return {"R2_A": f"computed estimate ≈ {w['R2_A']:.1f} h (R2_SMOKE projection, 4 workers)",
            "R2_B": f"computed estimate ≈ {w['R2_B']:.1f} h (R2_SMOKE projection, 2 workers)",
            "R2_C": "computed estimate ≈ 1.8 h (R2_SMOKE per-job estimates on 2 workers + the R2.0-cnn gate)"}


def runs(commit):
    built = []
    est_txt = _proj_text()
    prj = """
PROJ_FILE = R2.REPO / "results" / "r2" / "r2_cv" / "smoke" / "projection.json"
assert PROJ_FILE.exists(), "the pinned commit lacks R2_SMOKE's projection.json"
PROJ = json.loads(PROJ_FILE.read_text())
"""
    for n, tag, what, models, cf, est in (
            ("R2_A", "a", "the GAE and the MLP-AE, 4 folds each (8 jobs), trained on the new data with the new fold "
             "constants (200 epochs, seed 42), scored by the frozen chain with each fold's own k. This is also "
             "partition 0 of stage R3.", ["gae", "mlp"], [], est_txt["R2_A"]),
            ("R2_B", "b", "Isolation Forest (4 folds, one job), gradient-boosted trees and linear SVM (4 folds each) on the "
             "new data; counterfactual: the committed GAE and MLP-AE fold models on the new data (scoring only).",
             ["if", "hgb", "svm"], ["gae", "mlp"], est_txt["R2_B"]),
            ("R2_C", "c", "**first the gate R2.0-cnn** (the committed CNN fold checkpoints scored on the earlier data = "
             "the record's CNN rows within |Δtp| ≤ 1, |Δfp| ≤ 2 per row; STOP before any training on failure or if a "
             "checkpoint is absent); then the 1-D CNN, 4 folds (30 epochs, CPU, at most 2 workers) on the new data; "
             "counterfactual: the committed CNN fold models on the new data (scoring only).",
             ["cnn"], ["cnn"], est_txt["R2_C"])):
        cells = [head(n, commit, what + " Gates: G-data, D0′ (and G-const, G-vec, G-mlp). **Resumable:** attach this "
                      "notebook's previous output; finished jobs are reused (code sha checked).",
                      f"`/kaggle/working/r2/r2_cv/{tag}/` (→ `results/r2/r2_cv/{tag}/`; job checkpoints ≈ 20–30 KB)", est),
                 setup(n, commit), code("%%writefile {SRC}/r2_r2.py\n" + CORE), start(tag), code(prj + DATA)]
        if tag == "a":
            cells.append(code(EARLIER))
        if tag == "c":
            cells.append(code("W_CAP = 2   # plan §12 08/11 19:10: CNN training memory not measured by the smoke\n" + CNN_GATE))
        wline = (f'W = min(int(PROJ["workers"]["{n}"]), W_CAP)   # at most 2 workers (plan §12 08/11 19:10)' if tag == "c"
                 else f'W = int(PROJ["workers"]["{n}"])')
        cells.append(code(f"""
# JOBS ({n}): resumed jobs reused; LPT order on the projected workers; a job that cannot finish in the session waits
R2.import_previous("jobs"); R2.import_previous("cfjobs")
{wline}
SPECS = R2.run_specs({models!r}, METAS) + R2.cf_specs({cf!r})
print("workers", W, "| jobs", [s["name"] for s in SPECS], "| projected wall h", PROJ["wall_h"]["{n}"])
try:
    RES = R2.run_jobs(SPECS, W, est_h=PROJ["est_h"])
except SystemExit as e:
    stopped(e)
print(pd.DataFrame([dict(name=r["name"], status=r["status"], seconds=r.get("seconds"), peak_mb=r.get("peak_rss_mb"))
                    for r in RES]).to_string(index=False))
"""))
        cells.append(code("""
# MERGE: run rows -> model_cmp/ (the comparison's format), counterfactual rows -> cf/
GOT = R2.finalise_model_cmp(None)
CFD, CFGOT = R2.merge("cfjobs", "cf")
print("run jobs merged:", GOT, "| counterfactual jobs merged:", CFGOT)
NOT_DONE = [r for r in RES if r["status"] not in ("done", "reused")]
if NOT_DONE:
    print("NOT DONE (rerun this notebook with its output attached):", NOT_DONE)
"""))
        cells.append(end())
        built.append(save(n, cells))
    return built


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", metavar="REF", help="build R2_SMOKE cloned at REF (tag or commit)")
    ap.add_argument("--runs", metavar="COMMIT", help="build R2_A, R2_B, R2_C cloned at COMMIT (holds R2_SMOKE's output)")
    a = ap.parse_args()
    if not (a.smoke or a.runs):
        ap.error("nothing to build: --smoke REF and/or --runs COMMIT")
    built = ([smoke(a.smoke)] if a.smoke else []) + (runs(a.runs) if a.runs else [])
    print("built", [b.name for b in built], "r2_r2 sha", SHA)
