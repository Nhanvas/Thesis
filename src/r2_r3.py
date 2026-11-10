#!/usr/bin/env python
"""
r2_r3.py -- independent research track, stage R3: F1 + F2 (repeated random patient-wise 4-fold CV of the GAE and the
MLP-AE) re-executed on complete data (docs/FUTURE_RESEARCH_PLAN.md rev 2, §7, §9; design approved by the author 09/11
21:11: R3-a no separate smoke notebook, R3-b R3.0 gate + counterfactual with the committed F1 checkpoints, R3-c five
notebooks in parallel; implementation logged in §12, 10/11, chat D18-F). Kaggle CPU. Written and tested on synthetic data
before any R3 output exists.

Closed modules are imported READ ONLY and called unchanged: f1_core (partitions, seeds, fold constants, the tensor
training loop, the frozen chain per fold, the gates G-const / G-vec / G-mlp), model_cmp_core (through f1_core), r2_r2
(stage R2: views, G-data, D0', expected counts, worker set-up; its sha is checked: 542968bb). The only runtime pointer set
here is r2_r2.OUT_ROOT -> WORK/r2/r3_repcv, so that r2_r2's gate and run-metadata helpers write into this stage's folder
(tag = p{r}); nothing in r2_r2's logic changes.

Fixed design (plan §7 = rev 1 §3 applied unchanged to the R0 data): partition r in 1..5 of results/f1_repcv/partitions.json
(committed 905212a), seed r; GAE + MLP-AE, the thesis fold recipe (f1_core.train: 200 epochs, batch 32, Adam 1e-3, cosine,
last epoch kept); fold constants recomputed on the new data by f1_core.fold_constants (= v9_x3_train_fold's rule); the
frozen chain with the fold's own label-free k (f1_core.run_fold). Partition 0 = R2_A (results/r2/r2_cv/a, not rerun here).

Gates of one notebook R3_p{r} (STOP on failure; all of them before any training):
  G-data      the 24 new {case}.npz present once, sha256 = the pinned results/r2/r1_system/smoke/data_sha256.csv (r2_r2)
  D0'         new data: n_ref = record for 24 cases; non-ictal hours = record (22) / record + added files (chb11, chb21);
              clean windows = expected (r2_r2.gate_d0prime, unchanged)
  R3-projection  wall time of this notebook (computed from R2_A's measured CPU step and scoring times, LPT over the
              workers) + elapsed <= 10.5 h (the stage rule; otherwise the partition is split by the chat)
  G-const, G-vec, G-mlp   f1_core's gates on the earlier data (unchanged: partition 0 constants = committed fold models;
              tensor loop = PyG loop; MLP-AE loop = model_cmp_core.mlp_train)
  G-const-p   earlier data: this partition's fold constants recomputed = the committed F1 checkpoint metas (relative
              1e-9); their training cases, held-out cases and seed identical; the total clean-window count (the F1
              json's n_train) = the sum over the training cases
  R3.0-gae, R3.0-mlp   the 8 committed F1 checkpoints of this partition (results/f1_repcv/raw/p{r}/jobs/*, trained on a
              GPU in the record; scoring there was on the CPU) scored on the earlier data by this module's path = the
              record rows results/f1_repcv/raw/p{r}/per_subject.csv on (model, fold, subject, point, stage) within
              |dtp| <= 1, |dfp| <= 2 per row, n_ref exact, no row missing (the R2 tolerance for GPU-trained models);
              exact rows, own-point k vs the record's and caught flags reported; checkpoint sha256 recorded
Jobs (atomic, one spawned process each, DONE.json last, resumable from an attached previous output with the same code
sha; a job is not started when its projected end passes the session limit, checked again when it starts):
  r30/{model}_fold{f}       the gate jobs above (earlier view)
  jobs/{model}_fold{f}      training on the new data with the new constants, then the frozen chain (F1 format, partition
                            column kept); expected training windows, 3,964 parameters, G2
  cfjobs/cf_{model}_fold{f} counterfactual: the committed F1 checkpoint with its own constants on the new data, k
                            recomputed (rerun - record = data (cf - record) + new models (rerun - cf))
Outputs: WORK/r2/r3_repcv/p{r}/ in the layout of results/f1_repcv/raw/p{r}/ (run_meta.json, gates.json, jobs/, merged
per_subject / curves / auroc / seizures / training_log .csv) + r30/, cf/, cfjobs/, data_gate.json, d0.json,
fold_constants.csv, fold_metas_new.json, projection.json, jobs.json, SUMMARY.md. Reading: src/r2_r3_aggregate.py,
committed before any R3 output.
Test mode (synthetic data, build container only): environment R2_TEST (src/r2_r3_synthetic_test.py).
"""
import hashlib
import json
import multiprocessing as mp
import os
import resource
import shutil
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(os.environ.get("THESIS_REPO", Path(__file__).resolve().parents[1]))
for _p in ("src", "src/dataprep", "src/retrain", "src/phaseB", "src/phaseC"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import r2_r2 as R2                       # noqa: E402  (stage R2, read only)

F, C, R0 = R2.F, R2.C, R2.R0
R2_SHA = "542968bb851bc05c"              # r2_r2.py as run by R2_SMOKE / R2_A / R2_B / R2_C
if Path(R2.__file__).resolve().parent != (REPO / "src").resolve():
    raise SystemExit(f"STOP: r2_r2 imported from outside {REPO / 'src'}: {R2.__file__}")
if R2.CODE_SHA != R2_SHA and not os.environ.get("R2_TEST"):
    raise SystemExit(f"STOP: r2_r2.py sha {R2.CODE_SHA} != {R2_SHA} (the code R2 ran)")

OUT_ROOT = R2.WORK / "r2" / "r3_repcv"
R2.OUT_ROOT = OUT_ROOT                   # r2_r2's gate() / out_dir() / run_meta() write into this stage (tag p{r})
F1RAW = REPO / "results" / "f1_repcv" / "raw"
R2A = REPO / "results" / "r2" / "r2_cv" / "a"
PARTS = (1, 2, 3, 4, 5)
MODELS = F.MODELS                        # ("gae", "mlp")
FOLDS = R2.FOLDS
EPOCHS = R2.EPOCHS                       # 200 (the recipe); reduced only in test mode
TOL = R2.TOL
SESSION_STOP_H, REFUSE_H = R2.SESSION_STOP_H, R2.REFUSE_H
CODE_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:16]
STATE = R2.STATE
log, jdumps, _jdump, sha256_file = R2.log, R2.jdumps, R2._jdump, R2.sha256_file
gate, hours = R2.gate, R2.hours


def pdir(p):
    d = OUT_ROOT / f"p{int(p)}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def phase(name, t):
    R2.phase(name, t)


# ============================================================================ run metadata (F1 keys added)
def run_meta(p, notebook, repo_commit):
    """r2_r2.run_meta + the keys src/f1_aggregate.py reads (partition, seed, core_sha, partitions_sha, epochs)."""
    p = int(p)
    if p not in PARTS:
        raise SystemExit(f"STOP: partition {p} is not one of {PARTS} (partition 0 = R2_A)")
    meta = R2.run_meta(f"p{p}", notebook, repo_commit)
    meta.update(partition=p, seed=F.seed_of(p), r2_r3_sha=CODE_SHA, r2_r2_sha=R2.CODE_SHA, core_sha=CODE_SHA,
                partitions_sha=F.sha16(F.PARTITIONS), f1_record_core_sha=_f1_record_meta(p).get("core_sha"))
    _jdump(pdir(p) / "run_meta.json", meta)
    log(f"partition {p}, seed {meta['seed']}, r2_r3 {CODE_SHA}, partitions {meta['partitions_sha']}")
    return meta


def _f1_record_meta(p):
    f = F1RAW / f"p{int(p)}" / "run_meta.json"
    return json.loads(f.read_text()) if f.exists() else {}


def finish_meta(p):
    jobs = sorted(x.parent.name for x in (pdir(p) / "jobs").glob("*/DONE.json"))
    return R2.finish_meta(dict(jobs_done=len(jobs), notebook_runtime_h=round(hours(), 3)))


# ============================================================================ checkpoints of the F1 record
def f1_paths(p, model, f):
    jd = F1RAW / f"p{int(p)}" / "jobs" / f"{model}_fold{int(f)}"
    stem = f"{model}_p{int(p)}_fold{int(f)}_seed{F.seed_of(p)}"
    return jd / f"{stem}.pt", jd / f"{stem}.json"


def f1_model(p, model, f):
    """the committed F1 checkpoint of (partition, model, fold) and its meta (constants of the earlier data)."""
    import torch
    pt, js = f1_paths(p, model, f)
    if not pt.exists() or not js.exists():
        raise SystemExit(f"STOP: F1 checkpoint missing in the pinned repository: {pt}")
    meta = json.loads(js.read_text())
    m = F.build(model)
    m.load_state_dict(torch.load(str(pt), map_location="cpu"), strict=True)
    return m.eval(), meta


# ============================================================================ constants
def new_metas(p):
    """fold constants of partition p recomputed on the CURRENT view (must be 'new'), in f1_core.new_meta's format, with
    the expected clean-window counts of the new data (committed counts; chb11 / chb21 from the R0 diff)."""
    assert STATE.get("view") == "new", "new_metas() needs the new view"
    cc, out = R2.expected_clean(), {}
    for f, man in F.manifest(p).items():
        tr = sorted(man["train_cases"])
        mu, sd = F.fold_constants(tr)
        out[int(f)] = dict(partition=int(p), fold=int(f), seed=F.seed_of(p), in_dim=F.IN_DIM, out_x=F.OUT_X, clip=4.0,
                           add_mean=mu.tolist(), add_std=sd.tolist(), train_cases=tr,
                           held_out_cases=list(man["held_out_cases"]), n_train={s: cc[s] for s in tr})
    return out


def gate_const_p(p):
    """earlier view: partition p's fold constants recomputed = the committed F1 checkpoint metas (relative 1e-9);
    training / held-out cases, seed and clean-window counts identical."""
    assert STATE.get("view") == "earlier"
    t = time.time()
    worst, bad = 0.0, []
    for f, man in F.manifest(p).items():
        mu, sd = F.fold_constants(sorted(man["train_cases"]))
        cc = {s: int(C.clean_mask(C.npz(s)).sum()) for s in sorted(man["train_cases"])}
        for model in MODELS:
            ref = json.loads(f1_paths(p, model, f)[1].read_text())
            if sorted(ref["train_cases"]) != sorted(man["train_cases"]) or \
                    list(ref["held_out_cases"]) != list(man["held_out_cases"]):
                bad.append((model, f, "cases differ from partitions.json"))
            if int(ref["seed"]) != F.seed_of(p) or int(ref.get("partition", p)) != int(p):
                bad.append((model, f, "seed / partition"))
            for got, want in ((mu, ref["add_mean"]), (sd, ref["add_std"])):
                r = float(np.max(np.abs(got - np.array(want)) / np.maximum(np.abs(np.array(want)), 1e-12)))
                worst = max(worst, r)
                if r > 1e-9:
                    bad.append((model, f, "constants", r))
            if int(ref["n_train"]) != sum(cc.values()):              # f1_core.job stores the total (training info)
                bad.append((model, f, "clean-window count", int(ref["n_train"]), sum(cc.values())))
    C._CACHE.clear()
    phase("gate_const_p", t)
    gate(dict(gate="G-const-p", status="PASS" if not bad else "FAIL", max_rel=worst, bad=str(bad),
              summary=f"partition {p}: fold constants on the earlier data = the F1 checkpoints' (max rel {worst:.1e}); "
                      "cases, seed, clean counts identical"))


def const_report(p, metas):
    rows = []
    for f in FOLDS:
        rec = json.loads(f1_paths(p, "gae", f)[1].read_text())
        for key in ("add_mean", "add_std"):
            a, b = np.asarray(metas[f][key]), np.asarray(rec[key])
            rows.append(dict(partition=p, fold=f, key=key,
                             max_rel_change=float(np.max(np.abs(a - b) / np.maximum(np.abs(b), 1e-12)))))
        tr = metas[f]["train_cases"]
        rows.append(dict(partition=p, fold=f, key="n_train", new=int(sum(metas[f]["n_train"].values())),
                         record=int(rec["n_train"]),                     # the F1 json holds the total
                         gap_cases_in_training=",".join(s for s in R2.GAP if s in tr)))
    pd.DataFrame(rows).to_csv(pdir(p) / "fold_constants.csv", index=False)
    _jdump(pdir(p) / "fold_metas_new.json", metas)
    return rows


# ============================================================================ projection (computed estimate)
def projection(p, metas, workers):
    """per-job hours from R2_A's measured CPU times (committed in the pinned repository): the slowest fold's ms per step
    of each model under 4 concurrent workers x this partition's steps + the slowest scoring time, x 1.10; gate and
    counterfactual jobs from R2_B's measured counterfactual scoring, x 1.5; LPT over the workers."""
    fits = {json.loads(x.read_text())["name"]: json.loads(x.read_text()) for x in (R2A / "jobs").glob("*/fit.json")}
    cfits = {}
    for x in (REPO / "results" / "r2" / "r2_cv" / "b" / "cfjobs").glob("*/fit.json"):
        cfits[json.loads(x.read_text())["name"]] = json.loads(x.read_text())
    if len(fits) != 8:
        raise SystemExit(f"STOP: R2_A's 8 fit.json not found in the pinned repository ({sorted(fits)})")
    ms = {m: max(fits[f"{m}_f{f}"]["ms_per_step"] for f in FOLDS) for m in MODELS}
    sc = {m: max(fits[f"{m}_f{f}"]["seconds"] - fits[f"{m}_f{f}"]["fit_s"] for f in FOLDS) for m in MODELS}
    cf = {m: max([cfits[k]["seconds"] for k in cfits if k.startswith(f"cf_{m}_")] or [300.0]) for m in MODELS}
    est = {}
    for f in FOLDS:
        n = int(sum(metas[f]["n_train"].values()))
        for m in MODELS:
            est[f"{m}_fold{f}"] = (ms[m] * EPOCHS * ((n + F.BATCH - 1) // F.BATCH) / 1000 + sc[m]) / 3600 * 1.10
            est[f"cf_{m}_fold{f}"] = cf[m] / 3600 * 1.5
    load = [0.0] * workers
    for name in sorted(est, key=lambda x: -est[x]):
        i = int(np.argmin(load)); load[i] += est[name]
    r30 = 2 * max(cf.values()) * 1.5 / 3600                     # 8 gate jobs on the workers: about two rounds
    out = dict(partition=p, workers=workers, ms_per_step=ms, score_s=sc, cf_s=cf, est_h=est, r30_h=r30,
               wall_h=max(load) + r30, elapsed_h=hours(), source="results/r2/r2_cv/a/jobs/*/fit.json (measured, "
               "R2_A, Kaggle CPU 4 workers) and results/r2/r2_cv/b/cfjobs/*/fit.json", computed_estimate=True)
    out["fits"] = bool(out["elapsed_h"] + out["wall_h"] <= REFUSE_H)
    _jdump(pdir(p) / "projection.json", out)
    gate(dict(gate="R3-projection", status="PASS" if out["fits"] else "FAIL", wall_h=round(out["wall_h"], 2),
              elapsed_h=round(out["elapsed_h"], 2), limit_h=REFUSE_H,
              summary=f"computed estimate {out['wall_h']:.2f} h on {workers} workers + {out['elapsed_h']:.2f} h elapsed "
                      f"<= {REFUSE_H} h"))
    return out


# ============================================================================ jobs (run in spawned workers)
def _jd(spec):
    return OUT_ROOT / f"p{int(spec['partition'])}" / spec["stage"] / spec["name"]


def _write(jd, per, cur, au, seiz, train_rows=None):
    for nm, rr in (("per_subject", per), ("curves", cur), ("auroc", au), ("seizures", seiz)):
        pd.DataFrame(rr).to_csv(jd / f"{nm}.csv", index=False)
    if train_rows is not None:
        pd.DataFrame(train_rows).to_csv(jd / "training_log.csv", index=False)


def _score(model, mdl, meta, p, f):
    return F.run_fold(model, int(p), int(f), F.manifest(p)[int(f)], lambda ctx: F.encode_D(model, mdl, meta, ctx))


def _k_r30(spec, jd, dev):
    """gate job: the committed F1 checkpoint (its own constants) on the earlier view."""
    p, model, f = int(spec["partition"]), spec["model"], int(spec["fold"])
    mdl, meta = f1_model(p, model, f)
    per, cur, au, seiz, k, sec = _score(model, mdl, meta, p, f)
    _write(jd, per, cur, au, seiz)
    return dict(model=model, partition=p, fold=f, k=k, score_s=round(sec, 1),
                checkpoint_sha256=sha256_file(f1_paths(p, model, f)[0]))


def _k_cf(spec, jd, dev):
    """counterfactual: the committed F1 checkpoint with its own (earlier-data) constants on the new view."""
    p, model, f = int(spec["partition"]), spec["model"], int(spec["fold"])
    mdl, meta = f1_model(p, model, f)
    per, cur, au, seiz, k, sec = _score(model, mdl, meta, p, f)
    _write(jd, per, cur, au, seiz)
    return dict(model=model, partition=p, fold=f, k=k, score_s=round(sec, 1))


def _k_train(spec, jd, dev):
    """training on the new data with the new fold constants (f1_core.train, the thesis fold recipe), then the chain."""
    p, model, f = int(spec["partition"]), spec["model"], int(spec["fold"])
    meta = spec["meta"]
    seed = F.seed_of(p)
    mdl, info, rows = F.train(model, meta["train_cases"], meta, seed, dev, epochs=spec.get("epochs", EPOCHS),
                              tag=f" p{p} f{f}")
    exp = int(sum(meta["n_train"].values()))
    if info["n_train"] != exp:
        raise SystemExit(f"STOP: {model} p{p} fold {f}: training windows {info['n_train']} != expected {exp}")
    if info["n_params"] != 3964:
        raise SystemExit(f"STOP: {model} p{p} fold {f}: {info['n_params']} parameters")
    if info["G2"] != "PASS":
        raise SystemExit(f"STOP G2: {model} p{p} fold {f} (loss did not fall)")
    stem = f"{model}_p{p}_fold{f}_seed{seed}"
    R2.torch_save(mdl, jd / f"{stem}.pt")
    _jdump(jd / f"{stem}.json", dict(meta, model=model, **{k: v for k, v in info.items() if k != "model"}))
    per, cur, au, seiz, k, sec = _score(model, mdl, meta, p, f)
    _write(jd, per, cur, au, seiz, [dict(r, partition=p, fold=f) for r in rows])
    return dict(model=model, partition=p, fold=f, k=k, score_s=round(sec, 1),
                **{x: info[x] for x in ("n_train", "epochs", "batch", "lr", "seed", "n_params", "first_loss", "last_loss",
                                        "fit_s", "load_s", "ms_per_step", "device", "G2", "torch")})


_KINDS = dict(r30=_k_r30, cf=_k_cf, train=_k_train)


def job(spec):
    """one atomic job in a spawned worker; fit.json and DONE.json written last (F1 keys core_sha / partitions_sha)."""
    t0 = time.time()
    jd = _jd(spec)
    if jd.exists():
        shutil.rmtree(jd)
    jd.mkdir(parents=True)
    try:
        if spec.get("est_h") is not None and hours() + float(spec["est_h"]) * 1.15 > SESSION_STOP_H:
            shutil.rmtree(jd)
            return dict(name=spec["name"], stage=spec["stage"], partition=spec["partition"],
                        status="NOT RUN (session time at start)", est_h=spec["est_h"])
        import torch
        R2.use_view(spec["view"])
        res = _KINDS[spec["kind"]](spec, jd, torch.device("cpu"))
        res.update(name=spec["name"], stage=spec["stage"], status="done", seconds=round(time.time() - t0, 1),
                   code_sha=CODE_SHA, core_sha=CODE_SHA, partitions_sha=F.sha16(F.PARTITIONS), view=spec["view"],
                   peak_rss_mb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1))
        _jdump(jd / "fit.json", res)
        _jdump(jd / "DONE.json", dict(status="done", code_sha=CODE_SHA, core_sha=CODE_SHA,
                                      partitions_sha=res["partitions_sha"], seconds=res["seconds"],
                                      peak_rss_mb=res["peak_rss_mb"], epochs=res.get("epochs"), seed=F.seed_of(spec["partition"])))
        log(f"job p{spec['partition']}/{spec['stage']}/{spec['name']} done in {res['seconds']:.0f}s "
            f"(peak {res['peak_rss_mb']:.0f} MB)")
        return res
    except BaseException as e:           # noqa: BLE001
        (jd / "FAILED.txt").write_text(traceback.format_exc())
        return dict(name=spec["name"], stage=spec["stage"], partition=spec["partition"],
                    status=f"FAILED: {e}"[:500], seconds=round(time.time() - t0, 1))


# ============================================================================ specs, pool, reuse, merge
def r30_specs(p):
    return [dict(stage="r30", name=f"{m}_fold{f}", kind="r30", model=m, fold=f, partition=int(p), view="earlier")
            for m in MODELS for f in FOLDS]


def run_specs(p, metas, epochs=None):
    sp = [dict(stage="jobs", name=f"{m}_fold{f}", kind="train", model=m, fold=f, partition=int(p), view="new",
               meta=metas[f], **({"epochs": epochs} if epochs else {})) for m in MODELS for f in FOLDS]
    sp += [dict(stage="cfjobs", name=f"cf_{m}_fold{f}", kind="cf", model=m, fold=f, partition=int(p), view="new")
           for m in MODELS for f in FOLDS]
    return sp


def import_previous(p):
    """finished jobs of an attached previous output of this partition (same code sha) are copied into this run."""
    got = []
    for stage in ("r30", "jobs", "cfjobs"):
        for d in sorted(R2.INPUT.rglob(f"r2/r3_repcv/p{int(p)}/{stage}/*/DONE.json")):
            done = json.loads(d.read_text())
            if done.get("code_sha") != CODE_SHA:
                log(f"not reused (different code sha {done.get('code_sha')}): {d.parent}")
                continue
            dst = pdir(p) / stage / d.parent.name
            if not (dst / "DONE.json").exists():
                shutil.rmtree(dst, ignore_errors=True)
                shutil.copytree(d.parent, dst)
                got.append(f"{stage}/{d.parent.name}")
    log(f"partition {p}: reused finished jobs: {got or 'none'}")
    return got


def run_jobs(p, specs, workers, est_h=None, label="jobs"):
    """LPT order (longest first) on `workers` spawned processes, one task per process (fresh memory, measured peak);
    finished jobs (DONE.json) are kept; a job whose projected end passes the session limit is not started (checked
    here from now, and again in the worker when it starts). Progress in p{r}/progress_<label>.json."""
    est_h = est_h or {}
    done = [s for s in specs if (_jd(s) / "DONE.json").exists()]
    todo = [dict(s, est_h=est_h.get(s["name"])) for s in specs if s not in done]
    res = [dict(json.loads((_jd(s) / "fit.json").read_text()), status="reused") for s in done]
    todo.sort(key=lambda s: -(s.get("est_h") or 0.0))
    runnable = []
    for s in todo:
        if s.get("est_h") and hours() + s["est_h"] * 1.15 > SESSION_STOP_H:
            res.append(dict(name=s["name"], stage=s["stage"], partition=p, status="NOT RUN (session time)"))
        else:
            runnable.append(s)
    if runnable:
        ctx = mp.get_context("spawn")
        with ctx.Pool(min(workers, len(runnable)), initializer=R2._init_worker, initargs=(R2._env(),),
                      maxtasksperchild=1) as pool:
            for r in pool.imap_unordered(job, runnable, 1):
                res.append(r)
                _jdump(pdir(p) / f"progress_{label}.json", res)
    _jdump(pdir(p) / f"progress_{label}.json", res)
    return res


def r30_read(p, res):
    """R3.0 gates: the committed F1 checkpoints on the earlier data = the F1 record rows (tolerance), per model."""
    t = time.time()
    failed = [r for r in res if r.get("status") not in ("done", "reused")]
    if failed:
        gate(dict(gate="R3.0-jobs", status="FAIL", failed=failed, summary=f"{len(failed)} R3.0 jobs failed"))
    ref = pd.read_csv(F1RAW / f"p{int(p)}" / "per_subject.csv")
    rseiz = pd.read_csv(F1RAW / f"p{int(p)}" / "seizures.csv")
    fits = {}
    for x in F1RAW.glob(f"p{int(p)}/jobs/*/fit.json"):
        fj = json.loads(x.read_text())
        fits[(fj["model"], int(fj["fold"]))] = fj
    jd = pdir(p) / "r30"
    out = {}
    for model in MODELS:
        mine = pd.concat([pd.read_csv(jd / f"{model}_fold{f}" / "per_subject.csv") for f in FOLDS], ignore_index=True)
        rr = ref[ref.model == model]
        key = ["fold", "subject", "point", "stage"]
        mg = rr.merge(mine, on=key, suffixes=("_ref", ""), how="outer", indicator=True)
        missing = int((mg._merge != "both").sum())
        mg = mg[mg._merge == "both"]
        dtp, dfp = (mg.tp - mg.tp_ref).abs(), (mg.fp - mg.fp_ref).abs()
        nref_bad = int((mg.n_ref != mg.n_ref_ref).sum())
        exact = int(((dtp == 0) & (dfp == 0) & (mg.n_ref == mg.n_ref_ref)).sum())
        kr = []
        for f in FOLDS:
            got = json.loads((jd / f"{model}_fold{f}" / "fit.json").read_text())["k"]
            want = float(fits[(model, f)]["k"])
            kr.append(abs(got - want) / max(abs(want), 1e-12))
        ms = pd.concat([pd.read_csv(jd / f"{model}_fold{f}" / "seizures.csv") for f in FOLDS], ignore_index=True)
        sk = ["subject", "file", "onset_s"]
        sm = rseiz[rseiz.model == model][sk + ["caught"]].merge(ms[sk + ["caught"]], on=sk, suffixes=("_ref", ""))
        caught_diff = int((sm.caught.astype(bool) != sm.caught_ref.astype(bool)).sum())
        ok = missing == 0 and nref_bad == 0 and len(mg) == 24 * 4 and int(dtp.max()) <= TOL["x_tp"] \
            and int(dfp.max()) <= TOL["x_fp"]
        bad = mg[(dtp > 0) | (dfp > 0)][["fold", "subject", "point", "stage", "tp_ref", "tp", "fp_ref", "fp"]]
        sha = {f"{model}_fold{f}": json.loads((jd / f"{model}_fold{f}" / "fit.json").read_text())["checkpoint_sha256"]
               for f in FOLDS}
        c = dict(status="PASS" if ok else "FAIL", rows=len(mg), exact_rows=exact, missing=missing, n_ref_differ=nref_bad,
                 max_abs_dtp=int(dtp.max()) if len(mg) else 0, max_abs_dfp=int(dfp.max()) if len(mg) else 0,
                 k_max_rel=float(max(kr)), seizures=len(sm), caught_differ=caught_diff, tolerance="|dtp| <= 1, |dfp| <= 2",
                 differing_rows=bad.to_dict("records")[:50], checkpoints_sha256=sha)
        out[model] = c
        gate(dict(gate=f"R3.0-{model}", **c,
                  summary=f"{c['rows']} rows, {c['exact_rows']} exact, max |dtp| {c['max_abs_dtp']}, |dfp| "
                          f"{c['max_abs_dfp']}, own-point k rel {c['k_max_rel']:.1e}, caught flags differing "
                          f"{caught_diff}/{len(sm)}"))
    _jdump(jd / "r30_summary.json", out)
    phase("r30_read", t)
    return out


def merge(p):
    """jobs/ -> p{r}/*.csv (the F1 layout read by src/f1_aggregate.py); cfjobs/ -> cf/; r30/ -> r30/*.csv."""
    out = {}
    for stage, dest in (("jobs", pdir(p)), ("cfjobs", pdir(p) / "cf"), ("r30", pdir(p) / "r30")):
        dest.mkdir(parents=True, exist_ok=True)
        dirs = [x.parent for x in sorted((pdir(p) / stage).glob("*/DONE.json"))]
        for nm in ("per_subject", "curves", "auroc", "seizures", "training_log"):
            parts = [pd.read_csv(x / f"{nm}.csv") for x in dirs if (x / f"{nm}.csv").exists()
                     and (x / f"{nm}.csv").stat().st_size > 1]
            parts = [q for q in parts if len(q.columns)]
            if parts:
                pd.concat(parts, ignore_index=True).to_csv(dest / f"{nm}.csv", index=False)
        out[stage] = [x.name for x in dirs]
    return out


def write_jobs(p, results):
    rows = [dict(model=r.get("model"), partition=int(p), fold=r.get("fold"), name=r["name"], stage=r.get("stage"),
                 status="done" if r["status"] in ("done", "reused") else r["status"], reused=r["status"] == "reused",
                 seconds=r.get("seconds"), peak_rss_mb=r.get("peak_rss_mb"), ms_per_step=r.get("ms_per_step"))
            for r in results]
    _jdump(pdir(p) / "jobs.json", rows)
    return rows


def summary_md(p, extra=()):
    return R2.summary_md(extra)
