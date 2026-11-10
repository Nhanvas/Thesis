#!/usr/bin/env python
"""r2_r3_make_notebooks.py -- builds the stage R3 Kaggle notebooks R3_p1 ... R3_p5 of the independent track
(docs/FUTURE_RESEARCH_PLAN.md rev 2, §7 and §9; §12 row 10/11, chat D18-F) from src/r2_r3.py (embedded verbatim with
%%writefile; sha256 checked in the notebook). The repository is cloned at a pinned COMMIT HASH (never a tag; plan §12
08/11 19:10) for the closed code (f1_core, model_cmp_core, r2_core, r2_r2), the committed F1 checkpoints
(results/f1_repcv/raw), R2_A's measured times (results/r2/r2_cv/a) and the pinned data hashes. Nothing to fill in.
  python src/r2_r3_make_notebooks.py --runs COMMIT     -> notebooks/r2/R3_p1.ipynb ... R3_p5.ipynb
Approved layout (author 09/11 21:11): no separate smoke notebook (each notebook runs every gate and R3.0 before any
training and STOPs on failure); R3.0 + counterfactual with the committed F1 checkpoints; five notebooks in parallel.
Test mode (synthetic data, build container only): environment R2_TEST_REPO / R2_TEST_INPUT / R2_TEST_WORK /
R2_TEST_SCRATCH (src/r2_r3_synthetic_test.py)."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R0_SHA = "902d15ad4feb3e8a"                                         # r2_core.py of stage R0 (dataset provenance)
R2_SHA = "542968bb851bc05c"                                         # r2_r2.py as run in stage R2
OUTDIR = Path(os.environ.get("R2_NB_OUTDIR", ROOT / "notebooks" / "r2"))
CORE = (ROOT / "src" / "r2_r3.py").read_text()
SHA = hashlib.sha256(CORE.encode()).hexdigest()[:16]
PKGS = '"mne==1.12.1", "torch_geometric==2.7.0", "ruptures==1.1.10", "timescoring==0.0.7"'
INPUTS = ("`thesis-r2-chbmit-features` (R0 dataset) + `v9-x3-fold1` + `v9-x3-fold3` (the record's earlier features; "
          "all 24 cases are in these two)")


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.strip("\n").splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": t.strip("\n").splitlines(keepends=True)}


def est_text(p):
    """runtime line from the committed R2_A measurements (computed estimate, same rule as r2_r3.projection)."""
    import math
    fits = [json.loads(x.read_text()) for x in (ROOT / "results" / "r2" / "r2_cv" / "a" / "jobs").glob("*/fit.json")]
    if len(fits) != 8:
        return "computed in the notebook (gate R3-projection)"
    ms = {m: max(f["ms_per_step"] for f in fits if f["model"] == m) for m in ("gae", "mlp")}
    sc = {m: max(f["seconds"] - f["fit_s"] for f in fits if f["model"] == m) for m in ("gae", "mlp")}
    parts = json.loads((ROOT / "results" / "f1_repcv" / "partitions.json").read_text())["partitions"]
    cc = {}
    for f in (1, 2, 3, 4):
        cc.update({s: int(n) for s, n in json.loads((ROOT / "results" / "v9_x3" / "models" / f"fold{f}" /
                                                    f"gae_fold{f}_seed42.json").read_text())["n_train"].items()})
    d = json.loads((ROOT / "results" / "r2" / "r0_data" / "chb" / "diff_chb11_chb21.json").read_text())
    for s in ("chb11", "chb21"):
        cc[s] = int(d[s]["clean_windows"][1])
    est = []
    for f, v in parts[str(p)]["folds"].items():
        n = sum(cc[s] for s in v["train_cases"])
        for m in ("gae", "mlp"):
            est.append((ms[m] * 200 * math.ceil(n / 32) / 1000 + sc[m]) / 3600 * 1.10)
    load = [0.0] * 4
    for e in sorted(est, reverse=True):
        i = load.index(min(load)); load[i] += e
    return (f"computed estimate ≈ {max(load) + 0.3:.1f} h on 4 workers (R2_A's measured CPU step and scoring times × "
            f"this partition's training windows, × 1.10; + ≈ 0.3 h of gates and counterfactual); R2_A measured 7.68 h")


def head(name, p, ref, est):
    return md(f"""
# {name} — independent track, stage R3 (repeated patient partitions on complete data), partition {p}

**Plan:** `docs/FUTURE_RESEARCH_PLAN.md` rev 2, §7 and §9; implementation in §12 (10/11, D18-F). **Does:** partition {p}
of `results/f1_repcv/partitions.json` (seed {p}): **first every gate** — G-data, D0′, R3-projection, G-const, G-vec, G-mlp,
G-const-p and **R3.0** (the 8 committed F1 checkpoints of this partition scored on the earlier data = the F1 record rows
within |Δtp| ≤ 1, |Δfp| ≤ 2 per row); the notebook STOPs before any training on a failure. Then 8 trainings on the new data
(GAE and MLP-AE × 4 folds; 200 epochs; new fold constants; the frozen chain with each fold's own k) and 8 counterfactual
scorings (the F1 checkpoints on the new data). **Resumable:** attach this notebook's previous output; finished jobs are
reused (code sha checked).
**Accelerator:** None (CPU). **Internet:** ON (package install and repository clone only). **Inputs:** {INPUTS}.
**Outputs:** `/kaggle/working/r2/r3_repcv/p{p}/` (→ `results/r2/r3_repcv/p{p}/`; checkpoints ≈ 20 KB each). **Runtime:** {est}.
Code: `github.com/Nhanvas/Thesis` at `{ref}` (closed code, the committed F1 checkpoints, R2_A's measurements and the pinned
data hashes, all read only) + `r2_r3.py` below (sha256 `{SHA}`). **Nothing printed here is a research result.** Do not edit;
*Save Version → Save & Run All (Commit)*.
""")


def setup(name, ref):
    return code(f"""
# SETUP: packages + repository at the pinned commit (read only)
import os, sys, subprocess, time, json, hashlib
T_NB = time.time()
os.environ["R2_T0"] = str(T_NB)
NOTEBOOK, REPO_REF = "{name}", "{ref}"
TEST = bool(os.environ.get("R2_TEST_REPO"))                      # synthetic test in the build container only
WORK = os.environ.get("R2_TEST_WORK", "/kaggle/working")
INPUT = os.environ.get("R2_TEST_INPUT", "/kaggle/input")
SCRATCH = os.environ.get("R2_TEST_SCRATCH", "/tmp/r2")
SRC = SCRATCH + "/src_r3"
os.makedirs(SRC, exist_ok=True)
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
if TEST:
    REPO = os.environ["R2_TEST_REPO"]
    REPO_COMMIT = "synthetic"
else:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", {PKGS}])
    REPO = "/tmp/Thesis"
    if not os.path.exists(REPO + "/src/r2_r2.py"):
        subprocess.check_call(f"rm -rf {{REPO}} && git clone -q https://github.com/Nhanvas/Thesis.git {{REPO}} "
                              f"&& cd {{REPO}} && git checkout -q {{REPO_REF}}", shell=True)
    REPO_COMMIT = subprocess.check_output(["git", "-C", REPO, "rev-parse", "HEAD"]).decode().strip()
    assert REPO_COMMIT == REPO_REF, f"clone at {{REPO_COMMIT}} != pinned {{REPO_REF}}"
for f, want in (("r2_core.py", "{R0_SHA}"), ("r2_r2.py", "{R2_SHA}")):
    got = hashlib.sha256(open(REPO + "/src/" + f, "rb").read()).hexdigest()[:16]
    assert TEST or got == want, f"{{f}} sha {{got}} != {{want}}"
print("repository", REPO, "at", REPO_REF, "=", REPO_COMMIT, f"({{time.time()-T_NB:.0f}}s)")
""")


def start(p):
    return code(f"""
# START: sha check of the embedded file, imports, run metadata
P = {p}
sha = hashlib.sha256(open(f"{{SRC}}/r2_r3.py", "rb").read()).hexdigest()[:16]
assert sha == "{SHA}", f"r2_r3.py: sha {{sha}} != {SHA} (cell edited?)"
os.environ.update(THESIS_REPO=REPO, R2_WORK=WORK, R2_INPUT=INPUT, R2_SCRATCH=SCRATCH)
sys.path.insert(0, SRC)
import pandas as pd, numpy as np
import torch
torch.set_num_threads(1)
import r2_r3 as R3
R2 = R3.R2
W = R2.n_workers()
print("CPU cores:", os.cpu_count(), "| RAM GB:", round(R2._ram_gb(), 1), "| workers:", W)
META = R3.run_meta(P, NOTEBOOK, REPO_COMMIT)
def stopped(e):
    raise RuntimeError(f"STOPPED: {{e}}") from None
""")


DATA = """
# VIEWS + G-data (sha256 = R1_SMOKE's pinned hashes) + D0' (new data) + this partition's new fold constants + projection
try:
    SRCS = R2.build_views()
    R2.gate_data(SRCS)
    R2.use_view("new")
    R2.gate_d0prime()
    METAS = R3.new_metas(P)
    print(pd.DataFrame(R3.const_report(P, METAS)).to_string(index=False))
    PROJ = R3.projection(P, METAS, W)
except SystemExit as e:
    stopped(e)
print("projected wall h (computed estimate):", round(PROJ["wall_h"], 2), "| per job:",
      {k: round(v, 2) for k, v in PROJ["est_h"].items()})
"""

EARLIER = """
# G-const, G-vec, G-mlp (f1_core, unchanged) and G-const-p (this partition's constants = the F1 checkpoints'), earlier data
try:
    R2.use_view("earlier")
    R2.gates_earlier()
    R3.gate_const_p(P)
except SystemExit as e:
    stopped(e)
"""

R30 = """
# R3.0: the 8 committed F1 checkpoints of this partition on the EARLIER data = the F1 record rows (|dtp| <= 1, |dfp| <= 2
# per row, n_ref exact). STOP here, before any training, on a failure. Finished jobs of an attached previous output reused.
try:
    R3.import_previous(P)
    R30 = R3.run_jobs(P, R3.r30_specs(P), W, label="r30")
    R30_READ = R3.r30_read(P, R30)
except SystemExit as e:
    stopped(e)
print(pd.DataFrame([dict(name=r["name"], status=r["status"], seconds=r.get("seconds"), peak_mb=r.get("peak_rss_mb"))
                    for r in R30]).to_string(index=False))
"""

JOBS = """
# JOBS: 8 trainings on the new data (LPT order: longest first) + 8 counterfactual scorings; a job that cannot finish in the
# session is not started (rerun this notebook with its output attached: finished jobs are reused)
SPECS = R3.run_specs(P, METAS)
print("workers", W, "| jobs", [s["name"] for s in SPECS])
try:
    RES = R3.run_jobs(P, SPECS, W, est_h=PROJ["est_h"], label="jobs")
except SystemExit as e:
    stopped(e)
R3.write_jobs(P, RES)
print(pd.DataFrame([dict(name=r["name"], status=r["status"], seconds=r.get("seconds"), peak_mb=r.get("peak_rss_mb"),
                         ms_step=r.get("ms_per_step")) for r in RES]).to_string(index=False))
"""

MERGE = """
# MERGE: jobs -> p{r}/*.csv (the F1 layout), counterfactual -> cf/, gate jobs -> r30/
GOT = R3.merge(P)
print({k: len(v) for k, v in GOT.items()})
NOT_DONE = [r for r in RES if r["status"] not in ("done", "reused")]
if NOT_DONE:
    print("NOT DONE (rerun this notebook with its output attached):", NOT_DONE)
"""


def end():
    return code("""
# END: SUMMARY.md, measured runtime, list of outputs
print(R3.summary_md(P))
meta = R3.finish_meta(P)
print(f"MEASURED notebook runtime: {meta['runtime_h']} h | jobs done: {meta['jobs_done']} | phases (s): {meta['phases_s']}")
for p in sorted(R3.pdir(P).rglob("*")):
    if p.is_file() and "/jobs/" not in str(p) and "/cfjobs/" not in str(p) and "/r30/" not in str(p):
        print(p.relative_to(R3.OUT_ROOT), p.stat().st_size)
""")


def save(name, cells):
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                       "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / f"{name}.ipynb").write_text(json.dumps(nb, indent=1))
    return OUTDIR / f"{name}.ipynb"


def runs(commit):
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise SystemExit(f"--runs needs a full 40-character commit hash, never a tag: {commit!r}")
    built = []
    for p in (1, 2, 3, 4, 5):
        n = f"R3_p{p}"
        built.append(save(n, [head(n, p, commit, est_text(p)), setup(n, commit),
                              code("%%writefile {SRC}/r2_r3.py\n" + CORE), start(p), code(DATA), code(EARLIER),
                              code(R30), code(JOBS), code(MERGE), end()]))
    return built


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", metavar="COMMIT", required=True, help="build R3_p1 ... R3_p5 cloned at COMMIT (40-hex hash)")
    a = ap.parse_args()
    built = runs(a.runs)
    print("built", [b.name for b in built], "r2_r3 sha", SHA)
