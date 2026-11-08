#!/usr/bin/env python
"""
r2_r2.py -- independent research track, stage R2: the four-fold patient-wise CV and the six-model comparison re-executed
on complete data (docs/FUTURE_RESEARCH_PLAN.md rev 2, §6, §9; implementation logged in §12, 08/11, chat D16-F). Kaggle
CPU. Written and tested on synthetic data before any R2 result.

Closed modules are imported READ ONLY and called unchanged (model_cmp_core = the comparison's code, f1_core = its
tensor-loop generalisation, r2_core = stage R0). This file only (1) builds symlink views of the inputs and points
model_cmp_core's npz registry at one of them (`earlier` = the record's .npz, `new` = thesis-r2-chbmit-features), (2)
supplies the fold constants a job uses through model_cmp_core.fold_meta for the duration of that job (`patched_meta`;
the comparison's recorded rule is "the fold's own training constants": on the new data they are recomputed by
f1_core.fold_constants = v9_x3_train_fold's rule), and (3) runs, compares and writes.

Fixed design (re-execution, plan §10 D1): folds = results/v9_x3/fold_manifests.json (partition 0); seed 42; six models
with their recorded recipes -- GAE and MLP-AE by f1_core.train (tensor loop, bit-equal to the record's loops: gates
G-vec, G-mlp), 200 epochs, last epoch kept; Isolation Forest, linear SVM, gradient-boosted trees, 1-D CNN by
model_cmp_core (if_D, sup_train, cnn_train) unchanged; the frozen chain with each model's own label-free k per fold
(f1_core.run_fold / model_cmp_core.run_fold); outputs in the comparison's format so src/model_cmp_aggregate.py (the
pre-registered analyses A-F) runs on them unchanged.

Gates (STOP on failure):
  G-data   every new {case}.npz present once; sha256 = the pinned results/r2/r1_system/smoke/data_sha256.csv (R1's
           G-data proved those files are R0's outputs).
  D0'      new data: n_ref of all 24 cases = results/v9_x3; non-ictal hours equal for the 22 gap-free cases (1e-6 h);
           chb11 / chb21 larger by exactly the non-signal-loss windows of the added files (names and window count = the
           R0 diff report); clean windows of every case = the expected counts (committed, chb11 / chb21 from the R0 diff).
  G-const  earlier data: f1_core.gate_const (fold constants recomputed = the committed fold models', 1e-9); new
           constants reported per fold.
  G-vec, G-mlp   f1_core.gate_vec / gate_mlp (earlier data, CPU).
  R2.0     code paths on the earlier data with the committed models (stage R1.0's role):
             gae  f1_core.gate_GG0 (committed GAE fold checkpoints = results/v9_x3, 48 rows + 185 caught flags exactly)
             if   Isolation Forest, 4 folds = results/model_cmp rows exactly (record ran on Kaggle CPU)
             hgb  trees retrained, 4 folds = results/model_cmp rows exactly (deterministic, record on Kaggle CPU)
             svm  linear SVM retrained, fold 1 = results/model_cmp rows exactly (author 08/11: fold 1 only)
             mlp  committed MLP-AE checkpoints, CPU scoring = results/model_cmp rows within |dtp| <= 1, |dfp| <= 2 per
                  row (the record trained and scored on a GPU; exact rows counted)
             cnn  committed CNN checkpoints (results/model_cmp/ckpt/cnn_fold*.pt), CPU scoring, same tolerance as mlp;
                  reported n/a (not a stop) if the checkpoints are not in the pinned repository
           exact = tp, fp, n_ref per (subject, point, stage) and the own-point k within 1e-6 relative.
  per job  training windows = expected; 3,964 parameters (autoencoders); G2 (last-epoch loss < first).
Jobs (atomic; DONE.json last; a finished job of an attached previous output is reused when the code sha matches):
  run  gae_f{f}, mlp_f{f} (R2_A); if_all, hgb_f{f}, svm_f{f} (R2_B); cnn_f{f} (R2_C) -- new data, new constants
  cf   cf_gae_f{f}, cf_mlp_f{f} (R2_B), cf_cnn_f{f} (R2_C) -- the committed models with their own constants on the new
       data, k recomputed (descriptive counterfactual: rerun - record = data (cf - record) + new models (rerun - cf));
       IF needs none (no training), trees and SVM need none (deterministic: rerun - record is the data effect).
Outputs: WORK/r2/r2_cv/<tag>/ (run_meta.json, gates.json, data_gate.json, d0.json, r20/, jobs/<job>/, model_cmp/ (merged
run rows + gates.json + run_meta.json: the format model_cmp_aggregate.load reads), cf/ (merged cf rows), projection.json).
Reading: src/r2_r2_aggregate.py, committed before any R2 output.
Test mode (synthetic data, build container only): environment R2_TEST (src/r2_r2_synthetic_test.py).
"""
import contextlib
import hashlib
import json
import multiprocessing as mp
import os
import platform
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

import r2_core as R0                     # noqa: E402  (stage R0, read only: log, json, sha256, locate_earlier)
import f1_core as F                      # noqa: E402  (closed, read only: fold_constants, train, encode_D, run_fold, gates)

C = F.C                                  # model_cmp_core (closed, read only)
_OUTSIDE = [m.__name__ for m in (R0, F, C, C.V9E1, C.P3L, C.PS) if (REPO / "src") not in Path(m.__file__).resolve().parents]
if _OUTSIDE:
    raise SystemExit(f"STOP: closed modules imported from outside {REPO / 'src'}: {_OUTSIDE}")

WORK = Path(os.environ.get("R2_WORK", "/kaggle/working"))
INPUT = Path(os.environ.get("R2_INPUT", "/kaggle/input"))
SCRATCH = Path(os.environ.get("R2_SCRATCH", "/tmp/r2"))
OUT_ROOT = WORK / "r2" / "r2_cv"
VIEWS = SCRATCH / "r2_views"
FOLDS, ALL, MAN = list(C.FOLDS), list(C.ALL), C.MAN
GAP = ("chb11", "chb21")
SEED = 42
EPOCHS = int(os.environ.get("R2_TEST_EPOCHS", 200)) if os.environ.get("R2_TEST") else 200   # the recipe: 200
R0_DIFF = REPO / "results" / "r2" / "r0_data" / "chb" / "diff_chb11_chb21.json"
PIN = REPO / "results" / "r2" / "r1_system" / "smoke" / "data_sha256.csv"
MC = REPO / "results" / "model_cmp"
TOL = dict(k_rel=1e-6, x_tp=1, x_fp=2, h=1e-6)
SESSION_STOP_H, REFUSE_H = 11.3, 10.5
_ORIG_FOLD_META = C.fold_meta            # the committed fold models' metas (record)
STATE = dict(tag=None, phases={}, notes=[], gates=[])
T0 = float(os.environ.get("R2_T0", time.time()))
log = R0.log
jdumps, _jdump, sha256_file = R0.jdumps, R0._jdump, R0.sha256_file
CODE_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:16]


def hours():
    return (time.time() - T0) / 3600


def out_dir(tag=None):
    d = OUT_ROOT / (tag or STATE["tag"])
    d.mkdir(parents=True, exist_ok=True)
    return d


def phase(name, t):
    STATE["phases"][name] = round(time.time() - t, 1)
    log(f"phase {name}: {STATE['phases'][name]:.0f} s")


def gate(rec):
    """record a gate in gates.json; STOP (SystemExit) unless PASS (status 'n/a' is recorded and does not stop)."""
    STATE["gates"].append(rec)
    _jdump(out_dir() / "gates.json", STATE["gates"])
    log(f"{rec['gate']}: {rec['status']}" + (f" ({rec.get('summary')})" if rec.get("summary") else ""))
    if rec["status"] not in ("PASS", "n/a"):
        raise SystemExit(f"{rec['gate']} {rec['status']}: {jdumps({k: v for k, v in rec.items() if k != 'detail'})[:1500]}")


def run_meta(tag, notebook, repo_commit):
    STATE["tag"] = tag
    import scipy
    import sklearn
    import torch
    vers = dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
                sklearn=sklearn.__version__, pandas=pd.__version__, torch=torch.__version__)
    for mod in ("torch_geometric", "ruptures"):
        try:
            vers[mod] = __import__(mod).__version__
        except Exception as e:          # noqa: BLE001
            vers[mod] = f"not importable: {e}"
    meta = dict(notebook=notebook, tag=tag, repo_commit=repo_commit, r2_r2_sha=CODE_SHA,
                f1_core_sha=F.sha16(F.__file__), model_cmp_core_sha=F.sha16(C.__file__), r2_core_sha=F.sha16(R0.__file__),
                started=time.strftime("%Y-%m-%d %H:%M:%S %Z"), cpu_count=os.cpu_count(), platform=platform.platform(),
                ram_gb=round(_ram_gb(), 1), versions=vers, epochs=EPOCHS, seed=SEED, test_mode=bool(os.environ.get("R2_TEST")))
    _jdump(out_dir() / "run_meta.json", meta)
    log("run_meta", jdumps({k: meta[k] for k in ("notebook", "repo_commit", "cpu_count", "ram_gb", "versions")}))
    return meta


def finish_meta(extra=None):
    p = out_dir() / "run_meta.json"
    meta = json.loads(p.read_text())
    meta.update(finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"), runtime_h=round(hours(), 3), phases_s=STATE["phases"],
                notes=STATE["notes"], peak_rss_self_mb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1))
    meta.update(extra or {})
    _jdump(p, meta)
    return meta


def _ram_gb():
    return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1e9


# ============================================================================ views + npz registry
def _new_hits(c):
    return [p for p in sorted(INPUT.rglob(f"{c}.npz")) if "thesis-r2-chbmit-features" in str(p)
            and "r0_jobs" not in p.parts and SCRATCH not in p.parents and WORK not in p.parents]


def build_views():
    """SCRATCH/r2_views/{earlier,new}/{case}.npz -> the record's .npz (v9-x3-fold* inputs, r2_core.locate_earlier) and
    thesis-r2-chbmit-features. Returns {kind: {case: source path}}."""
    t = time.time()
    shutil.rmtree(VIEWS, ignore_errors=True)
    src = {"earlier": {}, "new": {}}
    for c in ALL:
        src["earlier"][c] = R0.locate_earlier(c)
        hits = _new_hits(c)
        if not hits:
            raise SystemExit(f"STOP G-data: thesis-r2-chbmit-features/{c}.npz not found under {INPUT}")
        if len({h.stat().st_size for h in hits}) != 1:
            raise SystemExit(f"STOP G-data: copies of {c}.npz differ in size: {hits}")
        src["new"][c] = hits[0]
    for kind in src:
        d = VIEWS / kind
        d.mkdir(parents=True, exist_ok=True)
        for c, p in src[kind].items():
            (d / f"{c}.npz").symlink_to(p)
    phase("views", t)
    return {k: {c: str(p) for c, p in v.items()} for k, v in src.items()}


def use_view(kind):
    """point model_cmp_core's npz registry at one view (clears its window-bookkeeping cache)."""
    C._NPZ.clear()
    C._CACHE.clear()
    C.locate_all(str(VIEWS / kind))
    STATE["view"] = kind


@contextlib.contextmanager
def patched_meta(metas):
    """model_cmp_core.fold_meta(f) -> metas[f] for the duration of a job (the code that reads the fold constants --
    node_input via sup_train / sup_score / if_D -- runs unchanged); restored afterwards."""
    C.fold_meta = lambda f: metas[int(f)]
    try:
        yield
    finally:
        C.fold_meta = _ORIG_FOLD_META


# ============================================================================ expected counts, metas
def r0_diff():
    return json.loads(R0_DIFF.read_text())


def expected_clean():
    """clean training-window count per case on the new data: the committed fold metas (f1_core.clean_counts) with
    chb11 / chb21 from the R0 diff report."""
    with patched_meta({f: _ORIG_FOLD_META(f) for f in FOLDS}):
        cc = F.clean_counts()
    d = r0_diff()
    for s in GAP:
        cc[s] = int(d[s]["clean_windows"][1])
    return cc


def new_metas():
    """fold constants recomputed on the CURRENT view (must be 'new') by f1_core.fold_constants (= v9_x3_train_fold's
    rule), in the committed metas' format."""
    assert STATE.get("view") == "new", "new_metas() needs the new view"
    cc, out = expected_clean(), {}
    for f in FOLDS:
        tr = sorted(MAN[str(f)]["train_cases"])
        mu, sd = F.fold_constants(tr)
        rec = _ORIG_FOLD_META(f)
        out[f] = dict(fold=f, seed=SEED, in_dim=rec["in_dim"], out_x=rec["out_x"], clip=rec["clip"],
                      add_mean=mu.tolist(), add_std=sd.tolist(), train_cases=tr,
                      held_out_cases=list(MAN[str(f)]["held_out_cases"]), n_train={s: cc[s] for s in tr})
    return out


def sup_counts():
    """windows a supervised model trains on per fold (model_cmp_core.sup_train: not signal loss, not buffer), current view."""
    out = {}
    for f in FOLDS:
        n = 0
        for s in MAN[str(f)]["train_cases"]:
            z = C.npz(s)
            n += int((~z["is_signal_loss"].astype(bool) & ~z["is_buffer"].astype(bool)).sum())
        out[f] = n
    return out


# ============================================================================ gates on data
def gate_data(src, pin=PIN):
    t = time.time()
    rows = [dict(dataset="thesis-r2-chbmit-features", file=f"{c}.npz", bytes=Path(p).stat().st_size,
                 sha256=sha256_file(p), source=p) for c, p in sorted(src["new"].items())]
    pd.DataFrame(rows).to_csv(out_dir() / "data_sha256.csv", index=False)
    pv = pd.read_csv(pin)
    pv = pv[pv.dataset == "thesis-r2-chbmit-features"].set_index("file").sha256.to_dict()
    bad = [r["file"] for r in rows if pv.get(r["file"]) != r["sha256"]]
    rec = dict(gate="G-data", status="PASS" if not bad else "FAIL", pinned=str(pin.relative_to(REPO)) if REPO in pin.parents
               else str(pin), files=len(rows), differ=bad, summary=f"{len(rows)} new .npz, sha256 = pinned R1_SMOKE hashes")
    _jdump(out_dir() / "data_gate.json", rec)
    phase("gate_data", t)
    gate(rec)


def gate_d0prime():
    """D0' on the new view (module docstring)."""
    assert STATE.get("view") == "new"
    t = time.time()
    ref = pd.concat([pd.read_csv(C.X3 / f"fold{f}_seed42_per_subject.csv") for f in FOLDS])
    ref = ref[ref.stage == "localized"].set_index("subject")
    diff, exp = r0_diff(), expected_clean()
    bad, det = [], {}
    for s in ALL:
        ctx = C.make_ctx(s)
        _tp, _fp, nr, h = C.PS.score(ctx, {})
        r = ref.loc[s]
        z = ctx["z"]
        clean = int(C.clean_mask(z).sum())
        d = dict(n_ref=int(nr), n_ref_record=int(r.n_ref), nonict_h=h, nonict_h_record=float(r.nonict_h), clean=clean,
                 clean_expected=exp[s])
        ok = int(nr) == int(r.n_ref) and clean == exp[s]
        if s in GAP:
            files = [str(x) for x in z["files"]]
            added = [i for i, fn in enumerate(files) if fn in diff[s]["files_added"]]
            in_added = np.isin(ctx["fidx"], added)
            add_ok = int((in_added & ctx["ok"]).sum())
            want_h = float(r.nonict_h) + add_ok * C.WIN / 3600
            d.update(files_added=[files[i] for i in added], windows=int(ctx["n"]),
                     windows_expected=int(diff[s]["windows_complete"]), added_ictal=int((in_added & ctx["ict"]).sum()),
                     nonict_h_expected=want_h)
            ok = ok and sorted(d["files_added"]) == sorted(diff[s]["files_added"]) and d["windows"] == d["windows_expected"] \
                and d["added_ictal"] == 0 and abs(h - want_h) <= TOL["h"]
        else:
            ok = ok and abs(h - float(r.nonict_h)) <= TOL["h"]
        d["ok"] = bool(ok)
        det[s] = d
        if not ok:
            bad.append(s)
    rec = dict(gate="D0'", status="PASS" if not bad else "FAIL", bad=bad, detail=det,
               summary="24 cases: n_ref = record; non-ictal hours = record (22) / record + added files (chb11, chb21); "
                       "clean windows = expected")
    _jdump(out_dir() / "d0.json", rec)
    phase("gate_d0", t)
    gate(rec)
    C._CACHE.clear()


def gates_earlier():
    """G-const, G-vec, G-mlp on the earlier view (f1_core, unchanged)."""
    assert STATE.get("view") == "earlier"
    t = time.time()
    gate(F.gate_const())
    gate(F.gate_vec())
    gate(F.gate_mlp())
    C._CACHE.clear()
    phase("gates_earlier", t)


def const_report(metas):
    rows = []
    for f in FOLDS:
        rec = _ORIG_FOLD_META(f)
        for key in ("add_mean", "add_std"):
            a, b = np.asarray(metas[f][key]), np.asarray(rec[key])
            rows.append(dict(fold=f, key=key, max_rel_change=float(np.max(np.abs(a - b) / np.maximum(np.abs(b), 1e-12)))))
        rows.append(dict(fold=f, key="n_train", new=int(sum(metas[f]["n_train"].values())),
                         record=int(sum(rec["n_train"].values()))))
    pd.DataFrame(rows).to_csv(out_dir() / "fold_constants.csv", index=False)
    _jdump(out_dir() / "fold_metas_new.json", metas)
    return rows


# ============================================================================ workers
def _env():
    return {k: os.environ[k] for k in os.environ if k.startswith(("R2_", "THESIS_", "OMP_", "OPENBLAS_", "MKL_", "F1_"))} | \
        dict(R2_SYS_PATH=os.pathsep.join(sys.path), R2_TAG=STATE["tag"] or "")


def _init_worker(env):
    os.environ.update(env)
    for q in env.get("R2_SYS_PATH", "").split(os.pathsep):
        if q and q not in sys.path:
            sys.path.insert(0, q)
    try:
        import torch
        torch.set_num_threads(1)
    except Exception:                    # noqa: BLE001
        pass
    R0._limit_threads()
    STATE["tag"] = env.get("R2_TAG") or None


def n_workers(gb_per_worker=6.0):
    return max(1, min(4, os.cpu_count() or 1, int(_ram_gb() // gb_per_worker)))


# ============================================================================ models from checkpoints
def committed_mlp(f):
    import torch
    m = C.build_mlp_ae()
    m.load_state_dict(torch.load(str(MC / "ckpt" / f"mlp_fold{f}.pt"), map_location="cpu"), strict=True)
    return m.eval()


def cnn_ckpt(f):
    return MC / "ckpt" / f"cnn_fold{f}.pt"


def cnn_pred_from(model):
    """the prediction function of model_cmp_core.cnn_train (CPU)."""
    import torch

    def pred(Xn):
        out = []
        with torch.no_grad():
            for s in range(0, len(Xn), 8192):
                xb = torch.tensor(Xn[s:s + 8192].transpose(0, 2, 1).copy())
                out.append(torch.sigmoid(model(xb)).cpu().numpy())
        return np.concatenate(out).astype(np.float64)
    return pred


def committed_cnn(f):
    import torch
    m = C.build_cnn()
    m.load_state_dict(torch.load(str(cnn_ckpt(f)), map_location="cpu"), strict=True)
    return m.eval()


# ============================================================================ one job
def _job_dir(stage, name):
    return out_dir() / stage / name


def _write(jd, per, cur, au, seiz, extra_rows=None):
    for nm, rr in (("per_subject", per), ("curves", cur), ("auroc", au), ("seizures", seiz)):
        pd.DataFrame(rr).to_csv(jd / f"{nm}.csv", index=False)
    if extra_rows:
        pd.DataFrame(extra_rows).to_csv(jd / "training_log.csv", index=False)


def _strip(rows):
    """f1_core.run_fold rows carry a partition column; the comparison's format has none."""
    return [{k: v for k, v in r.items() if k != "partition"} for r in rows]


def job(spec):
    """spec = dict(stage, name, kind, model, fold(s), view, metas?, epochs?, smoke?). Runs in a spawned worker."""
    t0 = time.time()
    stage, name = spec["stage"], spec["name"]
    jd = _job_dir(stage, name)
    if jd.exists():
        shutil.rmtree(jd)
    jd.mkdir(parents=True)
    try:
        import torch
        use_view(spec["view"])
        metas = {int(k): v for k, v in spec["metas"].items()} if spec.get("metas") else None
        res = _JOBS[spec["kind"]](spec, metas, jd, torch.device("cpu"))
        res.update(name=name, stage=stage, status="done", seconds=round(time.time() - t0, 1), code_sha=CODE_SHA,
                   peak_rss_mb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1))
        _jdump(jd / "fit.json", res)
        _jdump(jd / "DONE.json", dict(status="done", code_sha=CODE_SHA, seconds=res["seconds"], peak_rss_mb=res["peak_rss_mb"]))
        log(f"job {stage}/{name} done in {res['seconds']:.0f}s (peak {res['peak_rss_mb']:.0f} MB)")
        return res
    except BaseException as e:           # noqa: BLE001
        (jd / "FAILED.txt").write_text(traceback.format_exc())
        return dict(name=name, stage=stage, status=f"FAILED: {e}"[:500], seconds=round(time.time() - t0, 1))


def _ae(spec, metas, jd, dev):
    """GAE / MLP-AE fold job: train on the new data with the new fold constants, then the frozen chain."""
    kind, f = spec["model"], int(spec["fold"])
    meta = metas[f]
    smoke = bool(spec.get("smoke"))
    cases = meta["train_cases"]
    mdl, info, rows = F.train(kind, cases[:1] if smoke else cases, meta, SEED, dev, epochs=spec.get("epochs", EPOCHS),
                              max_windows=2000 if smoke else None, tag=f" {spec['name']}")
    exp = int(sum(meta["n_train"].values()))
    if not smoke and info["n_train"] != exp:
        raise SystemExit(f"STOP: {kind} fold {f}: training windows {info['n_train']} != expected {exp}")
    if info["G2"] != "PASS":
        raise SystemExit(f"STOP G2: {kind} fold {f} (loss did not fall)")
    torch_save(mdl, jd / f"{kind}_fold{f}_seed{SEED}{'_SMOKE' if smoke else ''}.pt")
    _jdump(jd / f"{kind}_fold{f}_seed{SEED}.json", dict(meta, model=kind, **{k: v for k, v in info.items() if k != "model"}))
    if smoke:
        ctx = C.make_ctx(meta["held_out_cases"][0])
        D = F.encode_D(kind, mdl, meta, ctx)
        if not np.isfinite(D).all():
            raise SystemExit(f"STOP smoke: non-finite {kind} distance on {ctx['s']}")
        cal = C.make_ctx(cases[0])
        k = C.calibrate([(cal, C.scalars("D", cal, F.encode_D(kind, mdl, meta, cal))[1])])
        per, cur, au, seiz = F.evaluate_case(kind, 0, f, ctx, *C.scalars("D", ctx, D), k)
    else:
        per, cur, au, seiz, k, _s = F.run_fold(kind, 0, f, MAN[str(f)], lambda ctx: F.encode_D(kind, mdl, meta, ctx))
    _write(jd, _strip(per), _strip(cur), _strip(au), _strip(seiz), [dict(r, fold=f) for r in rows])
    return dict(model=kind, fold=f, k=k, **{x: info[x] for x in ("n_train", "epochs", "n_params", "first_loss", "last_loss",
                                                                 "fit_s", "ms_per_step", "G2")})


def torch_save(model, path):
    import torch
    torch.save({k: v.cpu() for k, v in model.state_dict().items()}, path)


def _if(spec, metas, jd, dev):
    """Isolation Forest, every fold in one job (per-case D cached across folds, as model_cmp_run.unsupervised)."""
    cache = {}

    def score(ctx):
        if ctx["s"] not in cache:
            cache[ctx["s"]] = C.if_D(ctx)
        return cache[ctx["s"]]
    P, Cc, A, S, ks = [], [], [], [], {}
    folds = spec.get("folds", FOLDS)
    with (patched_meta(metas) if metas else contextlib.nullcontext()):
        for f in folds:
            p, c, a, s, k = C.run_fold("if", f, score, "D")
            P += p; Cc += c; A += a; S += s; ks[f] = k
    _write(jd, P, Cc, A, S)
    return dict(model="if", folds=folds, k=ks)


def _sup(spec, metas, jd, dev):
    """linear SVM / trees / CNN fold job: model_cmp_core.sup_train + run_fold unchanged (fold constants via fold_meta)."""
    kind, f = spec["model"], int(spec["fold"])
    smoke = bool(spec.get("smoke"))
    with (patched_meta(metas) if metas else contextlib.nullcontext()):
        pred, info, rows = C.sup_train(f, kind, jd, smoke=smoke)
        if kind == "cnn" and info.get("G2") != "PASS":
            raise SystemExit(f"STOP G2: cnn fold {f} (loss did not fall)")
        if smoke:
            ctx = C.make_ctx(MAN[str(f)]["held_out_cases"][0])
            x, m = C.scalars("P", ctx, C.sup_score(pred, ctx, f))
            out, _, _ = C.V9E1.evaluate_arm(ctx, x, 0.0, C.FLOOR, C.CAP, C.SMOOTH, m=None)
            per = [dict(model=kind, fold=f, subject=ctx["s"], point="fixed0.005", stage=st, k=np.nan, **v)
                   for st, v in out.items()]
            _write(jd, per, [], [], [], rows)
            return dict(info, model=kind, fold=f)
        p, c, a, s, k = C.run_fold(kind, f, lambda ctx: C.sup_score(pred, ctx, f), "P")
    _write(jd, p, c, a, s, rows)
    return dict(info, model=kind, fold=f, k=k)


def _cf(spec, metas, jd, dev):
    """counterfactual / record code path: a committed model (with its committed constants) on the current view, k
    recomputed on the fold's training cases."""
    kind, f = spec["model"], int(spec["fold"])
    meta = _ORIG_FOLD_META(f)
    if kind == "gae":
        mdl, _ = F.committed_gae(f)
        p, c, a, s, k, _s = F.run_fold("gae", 0, f, MAN[str(f)], lambda ctx: F.encode_D("gae", mdl, meta, ctx))
        p, c, a, s = map(_strip, (p, c, a, s))
    elif kind == "mlp":
        mdl = committed_mlp(f)
        p, c, a, s, k, _s = F.run_fold("mlp", 0, f, MAN[str(f)], lambda ctx: F.encode_D("mlp", mdl, meta, ctx))
        p, c, a, s = map(_strip, (p, c, a, s))
    elif kind == "cnn":
        pred = cnn_pred_from(committed_cnn(f))
        p, c, a, s, k = C.run_fold("cnn", f, lambda ctx: C.sup_score(pred, ctx, f), "P")
    else:
        raise SystemExit(f"STOP: no counterfactual for {kind}")
    _write(jd, p, c, a, s)
    return dict(model=kind, fold=f, k=k)


def _gg0(spec, metas, jd, dev):
    g = F.gate_GG0()
    _jdump(jd / "gate.json", g)
    return dict(model="gae", gate=g)


def _timing(spec, metas, jd, dev):
    """ms per training step of both autoencoders (f1_core.timing) and of the CNN (batch 256) on real windows."""
    import torch
    out = dict(F.timing(dev))
    z0 = C.npz(MAN["1"]["train_cases"][0])
    X, *_ = C.node_input(z0, np.arange(min(20000, len(z0["is_ictal"]))), _ORIG_FOLD_META(1))
    torch.manual_seed(0)
    m = C.build_cnn()
    opt = torch.optim.Adam(m.parameters(), lr=C.CNN_LR)
    Xt = torch.tensor(X.transpose(0, 2, 1).copy())
    y = torch.zeros(len(Xt))
    lossf = torch.nn.BCEWithLogitsLoss()
    for rep in range(2):
        t = time.time()
        for _ in range(100):
            ii = torch.randint(0, len(Xt), (C.CNN_BATCH,))
            opt.zero_grad(); lossf(m(Xt[ii]), y[ii]).backward(); opt.step()
        out["cnn"] = (time.time() - t) / 100 * 1000
    return dict(timing=out)


_JOBS = dict(ae=_ae, iforest=_if, sup=_sup, cf=_cf, gg0=_gg0, timing=_timing)


# ============================================================================ pools, reuse, merge
def import_previous(stage):
    """finished jobs of an attached previous output (same code sha) are copied into this run."""
    got = []
    for d in sorted(INPUT.rglob(f"r2/r2_cv/*/{stage}/*/DONE.json")):
        done = json.loads(d.read_text())
        if done.get("code_sha") != CODE_SHA:
            log(f"not reused (different code sha {done.get('code_sha')}): {d.parent}")
            continue
        dst = _job_dir(stage, d.parent.name)
        if not (dst / "DONE.json").exists():
            shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(d.parent, dst)
            got.append(d.parent.name)
    log(f"{stage}: reused finished jobs: {got or 'none'}")
    return got


def run_jobs(specs, workers, est_h=None):
    """LPT order (longest first) on `workers` spawned processes, one task per process (fresh memory, measured peak);
    a job whose projected end passes the session limit is not started. Returns the job records."""
    done = [s for s in specs if (_job_dir(s["stage"], s["name"]) / "DONE.json").exists()]
    todo = [s for s in specs if s not in done]
    res = [dict(json.loads((_job_dir(s["stage"], s["name"]) / "fit.json").read_text()), status="reused") for s in done]
    todo.sort(key=lambda s: -(est_h or {}).get(s["name"], 0.0))
    runnable = []
    for s in todo:
        if est_h and hours() + est_h.get(s["name"], 0.0) * 1.15 > SESSION_STOP_H:
            res.append(dict(name=s["name"], stage=s["stage"], status="NOT RUN (session time)"))
        else:
            runnable.append(s)
    if runnable:
        ctx = mp.get_context("spawn")
        with ctx.Pool(min(workers, len(runnable)), initializer=_init_worker, initargs=(_env(),), maxtasksperchild=1) as pool:
            for r in pool.imap_unordered(job, runnable, 1):
                res.append(r)
                _jdump(out_dir() / "jobs.json", res)
    _jdump(out_dir() / "jobs.json", res)
    return res


def merge(stage, folder, names=None):
    """concatenate the finished jobs of a stage into out/<folder>/ (the comparison's file set)."""
    d = out_dir() / folder
    d.mkdir(parents=True, exist_ok=True)
    jd = out_dir() / stage
    dirs = [p.parent for p in sorted(jd.glob("*/DONE.json")) if names is None or p.parent.name in names]
    for nm in ("per_subject", "curves", "auroc", "seizures", "training_log"):
        parts = [pd.read_csv(x / f"{nm}.csv") for x in dirs if (x / f"{nm}.csv").exists() and (x / f"{nm}.csv").stat().st_size > 1]
        parts = [p for p in parts if len(p.columns)]
        if parts:
            pd.concat(parts, ignore_index=True).to_csv(d / f"{nm}.csv", index=False)
    return d, [x.name for x in dirs]


def finalise_model_cmp(names):
    """out/model_cmp/: merged run rows + gates.json + run_meta.json (+ jobs.json) = what model_cmp_aggregate.load reads."""
    d, got = merge("jobs", "model_cmp", names)
    _jdump(d / "gates.json", [g for g in STATE["gates"] if g.get("status") == "PASS"])     # n/a gates stay in ../gates.json
    meta = json.loads((out_dir() / "run_meta.json").read_text())
    _jdump(d / "run_meta.json", dict(meta, notebook=meta["notebook"]))
    jobs = json.loads((out_dir() / "jobs.json").read_text()) if (out_dir() / "jobs.json").exists() else []
    _jdump(d / "jobs.json", [dict(model=j.get("model"), fold=j.get("fold"), name=j["name"],
                                  status="done" if j["status"] in ("done", "reused") else j["status"],
                                  seconds=j.get("seconds")) for j in jobs if j.get("stage") == "jobs"])
    return got


# ============================================================================ R2.0: record code paths on the earlier data
def _compare(mine, model, tol, folds=None):
    """rows of one model vs results/model_cmp/per_subject.csv on (subject, point, stage): exact or within tolerance."""
    ref = pd.read_csv(MC / "per_subject.csv")
    ref = ref[ref.model == model]
    if folds is not None:
        ref = ref[ref.fold.isin(folds)]
    m = pd.DataFrame(mine)
    mg = ref.merge(m, on=["subject", "point", "stage"], suffixes=("_ref", ""), how="outer", indicator=True)
    missing = int((mg._merge != "both").sum())
    mg = mg[mg._merge == "both"]
    dtp, dfp = (mg.tp - mg.tp_ref).abs(), (mg.fp - mg.fp_ref).abs()
    exact = int(((dtp == 0) & (dfp == 0) & (mg.n_ref == mg.n_ref_ref)).sum())
    nref_bad = int((mg.n_ref != mg.n_ref_ref).sum())
    kk = mg[(mg.point == "own") & mg.k_ref.notna()]
    krel = float(np.max(np.abs(kk.k - kk.k_ref) / np.maximum(np.abs(kk.k_ref), 1e-12))) if len(kk) else 0.0
    if tol == "exact":
        ok = missing == 0 and exact == len(mg) and krel <= TOL["k_rel"]
    else:
        ok = missing == 0 and nref_bad == 0 and int(dtp.max()) <= TOL["x_tp"] and int(dfp.max()) <= TOL["x_fp"]
    bad = mg[(dtp > 0) | (dfp > 0)][["fold", "subject", "point", "stage", "tp_ref", "tp", "fp_ref", "fp"]].to_dict("records")
    return dict(status="PASS" if ok else "FAIL", rows=len(mg), exact_rows=exact, missing=missing, n_ref_differ=nref_bad,
                max_abs_dtp=int(dtp.max()) if len(mg) else 0, max_abs_dfp=int(dfp.max()) if len(mg) else 0,
                k_max_rel=krel, tolerance=tol, differing_rows=bad[:50])


def r20_specs(cnn=True):
    sp = [dict(stage="r20", name="gae", kind="gg0", model="gae", view="earlier"),
          dict(stage="r20", name="if", kind="iforest", model="if", view="earlier"),
          dict(stage="r20", name="svm_f1", kind="sup", model="svm", fold=1, view="earlier")]
    sp += [dict(stage="r20", name=f"hgb_f{f}", kind="sup", model="hgb", fold=f, view="earlier") for f in FOLDS]
    sp += [dict(stage="r20", name=f"mlp_f{f}", kind="cf", model="mlp", fold=f, view="earlier") for f in FOLDS]
    if cnn:
        sp += [dict(stage="r20", name=f"cnn_f{f}", kind="cf", model="cnn", fold=f, view="earlier") for f in FOLDS]
    return sp


def r20_read(res):
    """turn the R2.0 jobs into gates (STOP on failure, except CNN absent = n/a)."""
    t = time.time()
    failed = [r for r in res if r.get("status") not in ("done", "reused")]
    if failed:
        gate(dict(gate="R2.0-jobs", status="FAIL", failed=failed, summary=f"{len(failed)} R2.0 jobs failed"))
    jd = out_dir() / "r20"
    g = json.loads((jd / "gae" / "gate.json").read_text())
    gate(dict(g, gate="R2.0-gae (GG0)", summary=f"committed GAE fold models = results/v9_x3; {g.get('mismatches')}"))
    rows = lambda names: sum((pd.read_csv(jd / n / "per_subject.csv").to_dict("records") for n in names), [])  # noqa: E731
    out = {}
    for model, names, tol, folds in (("if", ["if"], "exact", None), ("hgb", [f"hgb_f{f}" for f in FOLDS], "exact", None),
                                     ("svm", ["svm_f1"], "exact", [1]),
                                     ("mlp", [f"mlp_f{f}" for f in FOLDS], "tolerance", None),
                                     ("cnn", [f"cnn_f{f}" for f in FOLDS], "tolerance", None)):
        present = [n for n in names if (jd / n / "DONE.json").exists()]
        if model == "cnn" and not present:
            gate(dict(gate="R2.0-cnn", status="n/a", summary="CNN checkpoints not in the pinned repository; not gated"))
            continue
        c = _compare(rows(present), model, tol, folds)
        out[model] = c
        gate(dict(gate=f"R2.0-{model}", **c,
                  summary=f"{c['rows']} rows, {c['exact_rows']} exact, max |dtp| {c['max_abs_dtp']}, |dfp| "
                          f"{c['max_abs_dfp']}, k rel {c['k_max_rel']:.1e} ({tol})"))
    _jdump(jd / "r20_summary.json", out)
    phase("r20_read", t)
    return out


# ============================================================================ run and counterfactual specs
def run_specs(models, metas, smoke=False, epochs=None):
    sp = []
    mj = {str(f): m for f, m in metas.items()}
    for model in models:
        if model in ("gae", "mlp"):
            for f in FOLDS[:1] if smoke else FOLDS:
                sp.append(dict(stage="smoke" if smoke else "jobs", name=f"{model}_f{f}", kind="ae", model=model, fold=f,
                               view="new", metas=mj, smoke=smoke, **({"epochs": epochs} if epochs else {})))
        elif model == "if":
            sp.append(dict(stage="smoke" if smoke else "jobs", name="if_all", kind="iforest", model="if", view="new",
                           metas=mj, **({"folds": [1]} if smoke else {})))
        else:
            for f in FOLDS[:1] if smoke else FOLDS:
                sp.append(dict(stage="smoke" if smoke else "jobs", name=f"{model}_f{f}", kind="sup", model=model, fold=f,
                               view="new", metas=mj, smoke=smoke))
    return sp


def cf_specs(models, folds=None):
    return [dict(stage="cfjobs", name=f"cf_{m}_f{f}", kind="cf", model=m, fold=f, view="new")
            for m in models for f in (folds or FOLDS) if m != "cnn" or cnn_ckpt(f).exists()]


# ============================================================================ projection (smoke)
def projection(timing, r20_res, metas, sup_n, workers_ae=4, limit_h=REFUSE_H):
    """computed estimates for R2_A (autoencoders), R2_B (IF + trees + SVM + cf) and R2_C (CNN + cf) from measured
    times: ms/step under 4 concurrent workers, the R2.0 jobs' seconds and peak memory, scaled by training-set sizes."""
    ms = {k: float(np.median([t["timing"][k] for t in timing])) for k in ("gae", "mlp", "cnn")}
    rmap = {r["name"]: r for r in r20_res if r.get("status") in ("done", "reused")}
    score_s = rmap.get("gae", {}).get("gate", {}).get("seconds", 600) / 4 * 3          # single-thread, conservative x3
    est = {}
    for f in FOLDS:
        n = sum(metas[f]["n_train"].values())
        steps = EPOCHS * ((n + 31) // 32)
        for m in ("gae", "mlp"):
            est[f"{m}_f{f}"] = (ms[m] * steps / 1000 + score_s) / 3600 * 1.10
    rec_jobs = {(j["model"], j["fold"]): j["seconds"] for j in json.loads((MC / "gates_all.json").read_text())["jobs"]}
    rec_fit = lambda m, f: json.loads((MC / "raw" / "A2" / f"fit_{m}_fold{f}.json").read_text())["n_train"]  # noqa: E731
    svm1 = rmap.get("svm_f1", {}).get("seconds", rec_jobs[("svm", 1)])
    for f in FOLDS:
        scale = sup_n[f] / rec_fit("svm", f)
        est[f"svm_f{f}"] = svm1 * rec_jobs[("svm", f)] / rec_jobs[("svm", 1)] * scale / 3600 * 1.10
        hg = rmap.get(f"hgb_f{f}", {}).get("seconds", rec_jobs[("hgb", f)])
        est[f"hgb_f{f}"] = hg * scale / 3600 * 1.10
        est[f"cnn_f{f}"] = (ms["cnn"] * C.CNN_EPOCHS * ((sup_n[f] + C.CNN_BATCH - 1) // C.CNN_BATCH) / 1000 + score_s) / 3600 * 1.15
        for m in ("gae", "mlp", "cnn"):
            est[f"cf_{m}_f{f}"] = score_s / 3600 * 1.5
    est["if_all"] = rmap.get("if", {}).get("seconds", 1200) / 3600 * 1.10
    peak = {m: max([r.get("peak_rss_mb", 0) for n, r in rmap.items() if n.startswith(m)] or [0]) / 1024
            for m in ("svm", "hgb", "if", "cnn", "mlp", "gae")}
    peak_cnn_train = 3.0 * sup_n[max(sup_n, key=sup_n.get)] * 540 * 4 / 1e9 + 1.0           # X, transposed copy, tensors
    ram = _ram_gb()

    def lpt(names, w):
        load = [0.0] * w
        for n in sorted(names, key=lambda x: -est[x]):
            i = int(np.argmin(load)); load[i] += est[n]
        return max(load)

    def workers_for(gb):
        return max(1, min(4, os.cpu_count() or 1, int(0.8 * ram // max(gb, 1.0))))
    groups = dict(R2_A=[f"{m}_f{f}" for m in ("gae", "mlp") for f in FOLDS],
                  R2_B=["if_all"] + [f"{m}_f{f}" for m in ("hgb", "svm") for f in FOLDS]
                  + [f"cf_{m}_f{f}" for m in ("gae", "mlp") for f in FOLDS],
                  R2_C=[f"cnn_f{f}" for f in FOLDS] + [f"cf_cnn_f{f}" for f in FOLDS])
    w = dict(R2_A=workers_ae, R2_B=workers_for(max(peak["svm"], peak["hgb"]) * 1.15), R2_C=workers_for(peak_cnn_train))
    out = dict(ms_per_step=ms, score_s=score_s, est_h=est, peak_gb=peak, peak_cnn_train_gb_est=peak_cnn_train,
               ram_gb=ram, workers=w, sup_train_windows=sup_n,
               wall_h={g: lpt(n, w[g]) + 0.3 for g, n in groups.items()}, groups=groups)
    out["fits"] = {g: h <= limit_h for g, h in out["wall_h"].items()}
    _jdump(out_dir() / "projection.json", out)
    return out


def summary_md(extra=()):
    L = [f"# R2 {STATE['tag']} -- gates and timing (no research number)\n", "| gate | status | summary |", "|---|---|---|"]
    L += [f"| {g['gate']} | {g['status']} | {g.get('summary', '')} |" for g in STATE["gates"]]
    L += ["", f"Phases (s): {jdumps(STATE['phases'])}", *extra]
    (out_dir() / "SUMMARY.md").write_text("\n".join(L) + "\n")
    return "\n".join(L)
