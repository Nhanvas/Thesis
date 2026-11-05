#!/usr/bin/env python
"""
f1_run.py -- driver of the Track F1/F2 Kaggle notebooks (docs/FUTURE_RESEARCH_PLAN.md rev 1). One notebook = one
partition p, both models (GAE, MLP-AE), 4 folds = 8 atomic jobs, run by W parallel worker processes:
  Accelerator None    -> W = min(4, CPU cores) workers on the CPU, 1 thread each (deterministic);
  Accelerator GPU T4x2 -> W = 4 workers, alternating cuda:0 / cuda:1.
Order: setup (D0) -> gates (G-const, GG0, G-vec, G-mlp) -> smoke (one tiny end-to-end job per model + timing of W
concurrent workers -> projection.json; the full run is refused if it cannot fit) -> full run -> merge.
Each job writes its own folder and DONE.json last; a job is started only if its projected end is before
SESSION_STOP_H. A previous version's output attached as input is reused job by job (same code and partitions sha only).
Nothing printed here is a result before verification (src/f1_aggregate.py).
"""
import json
import multiprocessing as mp
import os
import platform
import shutil
import subprocess
import time
from pathlib import Path

import numpy as np
import pandas as pd

import f1_core as F

OUT = Path(os.environ.get("F1_OUT", "/kaggle/working/f1_repcv"))
T0 = float(os.environ.get("F1_T0", time.time()))
os.environ["F1_T0"] = str(T0)        # spawned workers import this module with the parent's environment
SESSION_STOP_H = 11.3            # Kaggle stops a session at 12 h
REFUSE_H = 10.5                  # the full run is refused if its projected wall time exceeds this
GATES = []
PROJ = {}


def hours():
    return (time.time() - T0) / 3600


def _json(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, default=str)); tmp.replace(path)


def gate(rec, p):
    GATES.append(rec); _json(OUT / f"p{p}" / "gates.json", GATES)
    if rec.get("status") != "PASS":
        raise SystemExit(f"STOP gate {rec.get('gate')}: {rec}")


# ============================================================================ devices
GB_PER_WORKER = float(os.environ.get("F1_GB_PER_WORKER", 6.0))   # host-RAM budget per worker (largest fold ~3.5 GB estimated, not measured; peak RSS is recorded per job)


def devices():
    """W = min(4, CPU cores, host RAM / 6 GB) workers; GPU mode alternates cuda:0 / cuda:1."""
    import torch
    mem_gb = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1e9
    w = max(1, min(4, os.cpu_count() or 1, int(mem_gb // GB_PER_WORKER)))
    n_gpu = torch.cuda.device_count()
    if n_gpu:
        return [f"cuda:{i % n_gpu}" for i in range(w)], "gpu"
    return ["cpu"] * w, "cpu"


def _init(slots, env):
    os.environ.update(env)
    import sys
    for q in env.get("F1_SYS_PATH", "").split(os.pathsep):
        if q and q not in sys.path:
            sys.path.insert(0, q)
    import torch
    torch.set_num_threads(1)
    os.environ["F1_DEVICE"] = slots.get()


def _env():
    import sys
    return dict(THESIS_REPO=str(F.REPO), F1_PARTITIONS=str(F.PARTITIONS), F1_EPOCHS=str(F.EPOCHS), F1_OUT=str(OUT),
                F1_T0=str(T0), F1_SYS_PATH=os.pathsep.join(sys.path), F1_INPUT=os.environ.get("F1_INPUT", "/kaggle/input"))


def _worker_setup():
    import torch
    F.C.locate_all(os.environ["F1_INPUT"])
    return torch.device(os.environ["F1_DEVICE"])


def _timing_worker(_):
    dev = _worker_setup()
    return dict(device=str(dev), **F.timing(dev))


def _job_worker(spec):
    p, model, f, proj_h = spec
    dev = _worker_setup()
    if hours() + proj_h * 1.15 > SESSION_STOP_H:
        return dict(model=model, partition=p, fold=f, status="NOT RUN (session time)", projected_h=proj_h)
    try:
        return F.job(p, model, f, dev, OUT)
    except BaseException as e:                                            # noqa: BLE001
        import traceback
        jd = OUT / f"p{p}" / "jobs" / f"{model}_fold{f}"
        jd.mkdir(parents=True, exist_ok=True)
        (jd / "FAILED.txt").write_text(traceback.format_exc())
        return dict(model=model, partition=p, fold=f, status=f"FAILED: {e}")


def _pool(devs):
    ctx = mp.get_context("spawn")
    slots = ctx.Manager().Queue()
    for d in devs:
        slots.put(d)
    return ctx.Pool(len(devs), initializer=_init, initargs=(slots, _env()))


# ============================================================================ notebook steps
def run_meta(notebook, p, extra=None):
    import sklearn
    import torch
    meta = dict(notebook=notebook, partition=p, seed=F.seed_of(p), python=platform.python_version(),
                numpy=np.__version__, sklearn=sklearn.__version__, pandas=pd.__version__, torch=torch.__version__,
                cpu_count=os.cpu_count(), gpus=[torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())],
                epochs=F.EPOCHS, started=time.strftime("%Y-%m-%d %H:%M:%S %Z"), core_sha=F.sha16(F.__file__),
                run_sha=F.sha16(__file__), partitions_sha=F.sha16(F.PARTITIONS),
                model_cmp_core_sha=F.sha16(Path(F.C.__file__)))
    try:
        meta["repo_commit"] = subprocess.check_output(["git", "-C", str(F.REPO), "rev-parse", "HEAD"]).decode().strip()
    except Exception as e:                                               # noqa: BLE001
        meta["repo_commit"] = f"unknown ({e})"
    meta.update(extra or {})
    _json(OUT / f"p{p}" / "run_meta.json", meta)
    print(json.dumps(meta, indent=1))
    return meta


def setup(p, input_root="/kaggle/input"):
    os.environ["F1_INPUT"] = input_root
    F.C.locate_all(input_root)
    gate(F.C.gate_D0(), p)


def gates(p):
    gate(F.gate_const(), p)
    gate(F.gate_vec(), p)
    gate(F.gate_mlp(), p)
    g = F.gate_GG0()
    PROJ["score_s_per_fold"] = float(np.mean(g["fold_seconds"]))
    gate(g, p)
    F.C._CACHE.clear()


def smoke(p):
    """one tiny end-to-end job per model (2 epochs, 2000 windows, one held-out case), then W concurrent timing
    workers -> projected wall time of the full run (LPT schedule over W workers)."""
    import torch
    t0 = time.time()
    for model in F.MODELS:
        F.job(p, model, 1, torch.device("cpu"), OUT, smoke=True)
    devs, mode = devices()
    with _pool(devs) as pool:
        tm = pool.map(_timing_worker, range(len(devs)))
    ms = {m: float(np.median([t[m] for t in tm])) for m in F.MODELS}
    jobs = []
    for model in F.MODELS:
        for f, man in F.manifest(p).items():
            n = sum(F.clean_counts()[s] for s in man["train_cases"])
            steps = F.EPOCHS * ((n + F.BATCH - 1) // F.BATCH)
            sc = PROJ.get("score_s_per_fold", 120) * 3          # single-thread scoring, conservative x3
            jobs.append(dict(model=model, fold=f, n_train=n, proj_h=(ms[model] * steps / 1000 + sc) / 3600 * 1.10))
    jobs.sort(key=lambda j: -j["proj_h"])
    load = [0.0] * len(devs)
    for j in jobs:                                              # LPT: longest job to the least-loaded worker
        i = int(np.argmin(load)); load[i] += j["proj_h"]
    PROJ.update(mode=mode, workers=len(devs), devices=devs, ms_per_step=ms, timing_workers=tm, jobs=jobs,
                projected_wall_h=max(load), smoke_s=round(time.time() - t0), elapsed_h=hours(),
                fits=hours() + max(load) <= REFUSE_H)
    _json(OUT / f"p{p}" / "projection.json", PROJ)
    F.log(f"SMOKE: mode {mode}, {len(devs)} workers, ms/step under concurrency {ms}; projected wall time "
          f"{max(load):.2f} h (+ {hours():.2f} h elapsed) -> {'FITS' if PROJ['fits'] else 'DOES NOT FIT'}")
    return PROJ


def import_previous(p, input_root="/kaggle/input"):
    """reuse finished jobs of a previous version of this notebook attached as input (same code and partitions)."""
    core, parts_sha = F.sha16(F.__file__), F.sha16(F.PARTITIONS)
    got = []
    for d in Path(input_root).rglob(f"f1_repcv/p{p}/jobs/*/DONE.json"):
        done = json.loads(d.read_text())
        if done.get("core_sha") != core or done.get("partitions_sha") != parts_sha:
            F.log(f"not reused (different code or partitions): {d.parent}")
            continue
        dst = OUT / f"p{p}" / "jobs" / d.parent.name
        if not (dst / "DONE.json").exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(d.parent, dst)
            got.append(d.parent.name)
    F.log(f"reused finished jobs from a previous version: {got or 'none'}")
    return got


def full(p, refuse_if_not_fit=True):
    if refuse_if_not_fit and not PROJ.get("fits", False):
        raise SystemExit(f"projected {PROJ.get('projected_wall_h')} h does not fit the session ({REFUSE_H} h); "
                         "jobs that fit can be run with full(p, refuse_if_not_fit=False)")
    done = {d.parent.name for d in (OUT / f"p{p}" / "jobs").glob("*/DONE.json")}
    todo = [j for j in PROJ["jobs"] if f"{j['model']}_fold{j['fold']}" not in done]
    devs, _ = devices()
    res = [dict(model=m.split("_fold")[0], partition=p, fold=int(m.split("_fold")[1]), status="reused") for m in done]
    if todo:
        with _pool(devs) as pool:
            for r in pool.imap_unordered(_job_worker, [(p, j["model"], j["fold"], j["proj_h"]) for j in todo], 1):
                res.append(r); _json(OUT / f"p{p}" / "jobs.json", res)
                F.log(f"job finished: {r}")
    _json(OUT / f"p{p}" / "jobs.json", res)
    failed = [r for r in res if r["status"] not in ("done", "reused")]
    if failed:
        F.log(f"jobs not done: {failed}")
    return res


def merge(p):
    jd = OUT / f"p{p}" / "jobs"
    for name in ("per_subject", "curves", "auroc", "seizures", "training_log"):
        parts = [pd.read_csv(d.parent / f"{name}.csv") for d in sorted(jd.glob("*/DONE.json"))]
        if parts:
            pd.concat(parts, ignore_index=True).to_csv(OUT / f"p{p}" / f"{name}.csv", index=False)
    n_done = len(list(jd.glob("*/DONE.json")))
    F.log(f"merged {n_done} of 8 jobs of partition {p}")
    return n_done


def summary(p):
    f = OUT / f"p{p}" / "per_subject.csv"
    if not f.exists():
        return
    d = pd.read_csv(f)
    d = d[(d.point == "own") & (d.stage == "localized")]
    s = d.assign(sens=d.tp / d.n_ref, fp_day=d.fp / d.nonict_h * 24,
                 f1=2 * d.tp / (2 * d.tp + d.fp + (d.n_ref - d.tp))).groupby("model")[["sens", "fp_day", "f1"]].mean()
    s["n_cases"] = d.groupby("model").size()
    print("\nUNVERIFIED per-case means (own point, after CPD) -- not a result before verification:")
    print(s.round(3).to_string())
