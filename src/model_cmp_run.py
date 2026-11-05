#!/usr/bin/env python
"""
model_cmp_run.py -- driver of the two Kaggle notebooks of the model comparison rev 2
(docs/MODEL_COMPARISON_PLAN.md rev 2). Each (model, fold) job is atomic: its rows are appended to the output
CSVs as soon as it finishes, and a job is not started if the session is past SAFE_H (Kaggle stops at 12 h);
skipped jobs are listed in jobs.json for the next run. Nothing here is a result before verification.

Outputs (OUT, default /kaggle/working/model_cmp): per_subject.csv, curves.csv, auroc.csv, seizures.csv,
training_log.csv, jobs.json, gates.json, run_meta.json, ckpt/cnn_fold*.pt.
"""
import json
import os
import platform
import subprocess
import time
from pathlib import Path

import numpy as np
import pandas as pd

import model_cmp_core as C

OUT = Path(os.environ.get("MC_OUT", "/kaggle/working/model_cmp"))
T0 = time.time()
SAFE_H = 10.5
GATES, JOBS = [], []


def _json(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, indent=1, default=str))


def gate(rec):
    GATES.append(rec); _json("gates.json", GATES)


def hours():
    return (time.time() - T0) / 3600


def _append(rows, name):
    if rows:
        df = pd.DataFrame(rows)
        p = OUT / name
        df.to_csv(p, mode="a", header=not p.exists(), index=False)


def run_meta(notebook, extra=None):
    import sklearn
    meta = dict(notebook=notebook, python=platform.python_version(), sklearn=sklearn.__version__, numpy=np.__version__,
                pandas=pd.__version__, started=time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    try:
        meta["repo_commit"] = subprocess.check_output(["git", "-C", str(C.REPO), "rev-parse", "HEAD"]).decode().strip()
    except Exception as e:                                   # noqa: BLE001
        meta["repo_commit"] = f"unknown ({e})"
    try:
        import torch
        meta.update(torch=torch.__version__, gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)
    except Exception:                                        # noqa: BLE001
        pass
    meta.update(extra or {})
    _json("run_meta.json", meta)
    print(json.dumps(meta, indent=1))


def setup(input_root="/kaggle/input"):
    C.locate_all(input_root)
    gate(C.gate_D0())


def mini_gate():
    """smoke: GAE fold 1 on its held-out chb12 with the committed fold-1 k -> committed tp/fp (both stages)."""
    t0 = time.time()
    k = json.loads((C.X3 / "fold1_seed42_calibration.json").read_text())["k"]
    ctx = C.make_ctx("chb12")
    x, m = C.scalars("D", ctx, C.gae_D(1, ctx))
    out, _, _ = C.V9E1.evaluate_arm(ctx, x, k, C.FLOOR, C.CAP, C.SMOOTH, m=m)
    ref = pd.read_csv(C.X3 / "fold1_seed42_per_subject.csv")
    ref = ref[ref.subject == "chb12"].set_index("stage")
    got = {st: (out[st]["tp"], out[st]["fp"]) for st in ("detector", "localized")}
    want = {st: (int(ref.loc[st, "tp"]), int(ref.loc[st, "fp"])) for st in got}
    ok = got == want
    C.log(f"G-mini {'PASS' if ok else 'FAIL'}: GAE fold 1, chb12 -> {got}, committed {want} ({time.time()-t0:.0f}s)")
    gate(dict(gate="G-mini", status="PASS" if ok else "FAIL", got=str(got), ref=str(want), seconds=round(time.time() - t0)))
    return ok, time.time() - t0


def _job(model, f, fn):
    if hours() > SAFE_H:
        JOBS.append(dict(model=model, fold=f, status="NOT RUN (session time)")); _json("jobs.json", JOBS)
        C.log(f"[{model}] fold {f}: NOT RUN, session at {hours():.2f} h")
        return None
    t0 = time.time()
    res = fn()
    JOBS.append(dict(model=model, fold=f, status="done", seconds=round(time.time() - t0)))
    _json("jobs.json", JOBS)
    return res


# ============================================================================ label-free models
def unsupervised(models=("gae", "if")):
    if_cache = {}

    def if_score(ctx):
        if ctx["s"] not in if_cache:
            if_cache[ctx["s"]] = C.if_D(ctx)
        return if_cache[ctx["s"]]

    for model in models:
        P, S, ks = [], [], {}
        for f in C.FOLDS:
            fn = (lambda f=f: C.run_fold("gae", f, lambda ctx: C.gae_D(f, ctx), "D")) if model == "gae" else \
                 (lambda f=f: C.run_fold("if", f, if_score, "D"))
            r = _job(model, f, fn)
            if r is None:
                continue
            p, c, a, s, k = r
            _append(p, "per_subject.csv"); _append(c, "curves.csv"); _append(a, "auroc.csv"); _append(s, "seizures.csv")
            P += p; S += s; ks[f] = k
        if model == "gae":
            if len(ks) != 4:
                raise SystemExit("STOP: the GAE gate needs all 4 folds")
            g = C.gate_GG(P, S, ks)
            gate(g)
            if g["status"] != "PASS":
                raise SystemExit("STOP gate GG: the GAE row does not reproduce results/v9_x3 -- see gates.json")


# ============================================================================ supervised models
def supervised(models, smoke=False):
    for model in models:
        for f in C.FOLDS:
            if smoke and f > 1:
                break

            def job(model=model, f=f):
                pred, info, rows = C.sup_train(f, model, OUT, smoke=smoke)
                _append(rows, "training_log.csv" if not smoke else "training_log_SMOKE.csv")
                _json(f"fit_{model}_fold{f}{'_SMOKE' if smoke else ''}.json", info)
                if smoke:
                    ctx = C.make_ctx(C.MAN["1"]["held_out_cases"][0])
                    x, m = C.scalars("P", ctx, C.sup_score(pred, ctx, f))
                    out, _, _ = C.V9E1.evaluate_arm(ctx, x, 0.0, C.FLOOR, C.CAP, C.SMOOTH, m=None)   # fixed 0.005
                    C.log(f"[{model}] SMOKE fold 1 {ctx['s']} (small subset, not a result): localized "
                          f"tp={out['localized']['tp']} fp={out['localized']['fp']}")
                    return None
                return C.run_fold(model, f, lambda ctx: C.sup_score(pred, ctx, f), "P"), info

            r = _job(model, f, job) if not smoke else job()
            if r is None:
                continue
            (p, c, a, s, k), info = r
            if model == "cnn" and info.get("G2") != "PASS":
                gate(dict(gate="G2", model=model, fold=f, status="FAIL", detail="training loss did not fall"))
            _append(p, "per_subject.csv"); _append(c, "curves.csv"); _append(a, "auroc.csv"); _append(s, "seizures.csv")


def summary():
    p = OUT / "per_subject.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    d = d[(d.point == "own") & (d.stage == "localized")]
    s = d.assign(sens=d.tp / d.n_ref, fp_day=d.fp / d.nonict_h * 24,
                 f1=2 * d.tp / (2 * d.tp + d.fp + (d.n_ref - d.tp))).groupby("model")[["sens", "fp_day", "f1"]].mean()
    s["n_cases"] = d.groupby("model").size()
    print("\nUNVERIFIED per-case means (own label-free point, after CPD) -- not a result before verification:")
    print(s.round(3).to_string())


# ============================================================================ MLP autoencoder (plan section 9, 04/11)
def mlp(folds, device, smoke=False):
    if smoke:
        model, info, rows = C.mlp_train(folds[0], device, OUT, smoke=True)
        ctx = C.make_ctx(C.MAN[str(folds[0])]["held_out_cases"][0])
        D = C.mlp_D(model, folds[0], ctx, device)
        if not np.isfinite(D).all():
            raise SystemExit("STOP smoke: non-finite MLP-AE distance")
        ms = C.mlp_step_ms(device)
        steps = sum(sum(C.fold_meta(f)["n_train"].values()) // C.MLP_BATCH + 1 for f in folds)
        proj_h = ms / 1000 * steps * C.MLP_EPOCHS / 3600 * 1.15 + 0.1 * len(folds)
        _json("projection.json", dict(ms_per_step=ms, steps_per_epoch_total=steps, epochs=C.MLP_EPOCHS,
                                      projected_h=proj_h, safe_h=SAFE_H, elapsed_h=hours()))
        C.log(f"[mlp] SMOKE: 2 epochs ok, D finite on {ctx['s']}; measured {ms:.2f} ms/step -> projected "
              f"{proj_h:.2f} h for folds {folds}")
        if proj_h + hours() > SAFE_H:
            raise SystemExit(f"projected {proj_h:.2f} h does not fit the session ({SAFE_H} h)")
        return
    for f in folds:
        def job(f=f):
            model, info, rows = C.mlp_train(f, device, OUT)
            _append(rows, "training_log.csv")
            _json(f"fit_mlp_fold{f}.json", info)
            gate(dict(gate="G2", model="mlp", fold=f, status=info["G2"], first=info["first_loss"], last=info["last_loss"]))
            if info["G2"] != "PASS":
                raise SystemExit(f"MLP-AE fold {f} did not train (loss did not fall)")
            return C.run_fold("mlp", f, lambda ctx: C.mlp_D(model, f, ctx, device), "D")
        r = _job("mlp", f, job)
        if r is None:
            continue
        p, c, a, s, k = r
        _append(p, "per_subject.csv"); _append(c, "curves.csv"); _append(a, "auroc.csv"); _append(s, "seizures.csv")
