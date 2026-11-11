#!/usr/bin/env python
"""
r2_rp.py -- research track, stage RP, steps RP1-RP3 (docs/FUTURE_RESEARCH_PLAN.md §7b; §12 row 11/11 D20-F, written
before any RP output). Kaggle CPU, one notebook RP_RUN. The final report's main model = the thesis system re-run on the
complete data (stage R1), seeds 1-4 without a main seed, k calibrated per seed.

  RP1  train seed 4 with the R1 recipe: r2_r1.train_job, called unchanged (one worker, 1 thread, 200 epochs).
  RP2  k per seed: p3_levers.calibrate (median q_i = 0.005 over the 15 development cases) on each seed's OWN model;
       score every set (development 15, test 8, chb24, Siena 14) with p3c_freeze.run_budget for the 4 recorded arms
       (frozen 0.005 = held-out; L2; L2f = final; S) x stages detector / cpd / hybrid, 5 seeds (1-4 for the report;
       42 descriptive: its own k equals R1's k, so its rows must equal R1's and they measure the size of the k
       correction for the other seeds). Per-window scores of seeds 1-4 saved for test, chb24 and Siena (RP4, RP9).
  RP3  demo model = the seed of 1-4 with the lowest validation loss (final_val of the checkpoint json, written by
       r2_r1.train_job: loss of the recipe on the clean windows of chb10 / chb11 / chb22, no test data); ties within
       1e-9 relative -> the smaller seed number. Written to demo_model.json with its checkpoint, constants and k.

Seeds 1, 2, 3 (and 42) are the committed R1 checkpoints (results/r2/r1_system/run/models); only seed 4 is trained.

Gates (STOP; all before training):
  G-data       sha256 of the 63 dataset files = R1_SMOKE's pinned data_sha256.csv (the files R1 used).
  G-const-new  train_gae_v2.norm_constants on the new data = the constants in the 4 R1 checkpoint jsons; expected
               training / validation window counts = the R1 jsons' n_train / n_val.
  versions     library versions vs R1_RUN's run_meta: equal -> mode "exact"; different -> mode "tolerance".
  RP.0         the 4 R1 checkpoints on the new data, scored by this module's per-seed-k path with every k = R1's k,
               reproduce results/r2/r1_system/run/r13/run (per_subject, errors, q) and k (calibrate on seed 42).
               exact: integers equal, floats relative 1e-9, error pairs equal and in order, k relative 1e-12;
               tolerance: |dtp| <= 1, |dfp| <= 2 per row, n_ref and non-ictal hours equal, k relative 1e-6.
  G-vec        r2_r1.gate_vec unchanged (train_gae_v2.py --smoke vs the tensor loop).
  G-val        validation loss of the 4 R1 checkpoints recomputed with train_job's code = final_val in their jsons
               (exact: equal; tolerance: relative 1e-6) -> seed 4's value is comparable.
Training gates: those of r2_r1.train_seeds (windows = expected, 3,964 parameters, G2).
Outputs: WORK/r2/r1_system/rp/ (run_meta.json, gates.json, data_sha256.csv, models/ (seed 4), training/, rp0/,
rp2/ (per_subject.csv, errors.csv, q.csv, k.json, thresholds.csv, timing.csv, scores/{case}.csv.gz), demo_model.json,
SUMMARY.md). No reading here: the report tables come from src/r2_rp_aggregate.py, committed before RP_RUN runs.
"""
import hashlib
import json
import multiprocessing as mp
import os
import shutil
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

import r2_r1 as R1                      # stage R1 (sha 76cbe51f), read only: views helpers, d_job, train_job, gates

R0, X1, PD, PS, P3L, P3C, E22, TGV2 = R1.R0, R1.X1, R1.PD, R1.PS, R1.P3L, R1.P3C, R1.E22, R1.TGV2
REPO = R1.REPO
R1_RUN = REPO / "results" / "r2" / "r1_system" / "run"
PIN = REPO / "results" / "r2" / "r1_system" / "smoke" / "data_sha256.csv"
R1_TAGS = ["clean_seed42", "clean_seed1", "clean_seed2", "clean_seed3"]
NEW_SEED, NEW_TAG = 4, "clean_seed4"
RP_TAGS = R1_TAGS + [NEW_TAG]
REPORT_TAGS = ["clean_seed1", "clean_seed2", "clean_seed3", NEW_TAG]
K_R1 = float(json.loads((R1_RUN / "r13" / "run" / "k.json").read_text())["k"])
VERSION_KEYS = ("python", "numpy", "scipy", "sklearn", "pandas", "torch", "torch_geometric", "ruptures")
TOL = dict(exact=dict(float_rel=1e-9, k_rel=1e-12, val_rel=0.0),
           tolerance=dict(float_rel=1e-9, k_rel=1e-6, val_rel=1e-6, tp=1, fp=2))
TIE_REL = 1e-9
SCORE_SETS = ("test", "external")                    # RP2b: per-window scores saved for these sets
STATE = dict(mode=None)
log, jdumps, _jdump, sha256_file = R1.log, R1.jdumps, R1._jdump, R1.sha256_file
ROW_INT = ["tp", "fp", "n_ref", "short_tp", "short_n", "review_s", "rec_s"]
ROW_FLOAT = ["top", "nonict_h"]
ROW_KEYS = ["set", "subject", "seed", "budget", "stage"]
ERR_COLS = ["det_on", "det_off", "cpd_on", "cpd_off", "hyb_on", "hyb_off"]


def sha16(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def out_dir():
    return R1.out_dir()


# ============================================================================ tags in every process
def set_tags(tags):
    """the record modules loop over a module-level TAGS list (r2_r1.chb_ctx / d_job, x1_external.model_outputs); it is
    pointed here, in each process, like r2_r1 points PD.CKPT. No record file is edited."""
    R1.TAGS = list(tags)
    X1.TAGS = list(tags)


def _init(env, tags):
    R1._init_worker(env)
    set_tags(tags)


def _pool(n, tags):
    return mp.get_context("spawn").Pool(n, initializer=_init, initargs=(R1._env(), list(tags)), maxtasksperchild=1)


def _run(fn, specs, workers, tags, what):
    out = []
    if not specs:
        return out
    with _pool(min(workers, len(specs)), tags) as pool:
        for r in pool.imap_unordered(fn, specs):
            if r.get("error"):
                pool.terminate()
                raise SystemExit(f"{what} {r.get('case', r.get('tag'))}: {r['error']}")
            out.append(r)
            log(f"{what} {r.get('case', r.get('tag'))} done ({r.get('d_s', r.get('score_s', r.get('s')))} s)")
    return out


# ============================================================================ views + G-data
def build_views():
    """symlink views SCRATCH/r1_views/{new,ext} (the R1 layout, without the earlier .npz: RP reads only the new data)."""
    t = time.time()
    shutil.rmtree(R1.VIEWS, ignore_errors=True)
    src = {"new": {}, "new_stats": {}, "ext": {}}
    for c in R0.CHB_CASES:
        src["new"][c] = R1._one_copy([p for p in sorted(R1.INPUT.rglob(f"{c}.npz"))
                                      if R1._under(p, "thesis-r2-chbmit-features")], f"thesis-r2-chbmit-features/{c}.npz")
        src["new_stats"][c] = R1._one_copy([p for p in sorted(R1.INPUT.rglob(f"{c}_stats.json"))
                                            if R1._under(p, "thesis-r2-chbmit-features") and "stats_earlier" not in p.parts],
                                           f"thesis-r2-chbmit-features/{c}_stats.json")
    for c in R1.EXT:
        src["ext"][c] = R1._one_copy([p for p in sorted(R1.INPUT.rglob(f"{c}_lf.npz"))
                                      if R1._under(p, "thesis-r2-external-features")], f"thesis-r2-external-features/{c}_lf.npz")
    out = {"new": {}, "ext": {}}
    for kind in ("new", "ext"):
        (R1.VIEWS / kind).mkdir(parents=True, exist_ok=True)
        for c, p in src[kind].items():
            q = R1.VIEWS / kind / (f"{c}_lf.npz" if kind == "ext" else f"{c}.npz")
            q.symlink_to(p)
            out[kind][c] = q
    for c, p in src["new_stats"].items():
        (R1.VIEWS / "new" / f"{c}_stats.json").symlink_to(p)
    out["src"] = {k: {c: str(p) for c, p in v.items()} for k, v in src.items()}
    R1.phase("views", t)
    return out


def gate_data(views):
    """G-data: every dataset file hashed; the set of files and every sha256 = the pinned R1_SMOKE data_sha256.csv."""
    t = time.time()
    rows = []
    for c, p in views["new"].items():
        st = R1.VIEWS / "new" / f"{c}_stats.json"
        rows.append(dict(dataset="thesis-r2-chbmit-features", file=f"{c}.npz", bytes=p.stat().st_size, sha256=sha256_file(p),
                         source=views["src"]["new"][c]))
        rows.append(dict(dataset="thesis-r2-chbmit-features", file=f"{c}_stats.json", bytes=st.stat().st_size,
                         sha256=sha256_file(st), source=views["src"]["new_stats"][c]))
    for c, p in views["ext"].items():
        rows.append(dict(dataset="thesis-r2-external-features", file=f"{c}_lf.npz", bytes=p.stat().st_size,
                         sha256=sha256_file(p), source=views["src"]["ext"][c]))
    pd.DataFrame(rows).to_csv(out_dir() / "data_sha256.csv", index=False)
    pin = pd.read_csv(PIN)
    pv = pin.set_index(["dataset", "file"]).sha256.to_dict()
    got = {(r["dataset"], r["file"]): r["sha256"] for r in rows}
    differ = sorted(f"{d}/{f}" for (d, f) in set(pv) | set(got) if pv.get((d, f)) != got.get((d, f)))
    rec = dict(gate="G-data", status="PASS" if not differ else "FAIL", files_hashed=len(rows), pinned_files=len(pv),
               pin=str(PIN.relative_to(REPO)), differ=differ,
               summary=f"{len(rows)} files hashed = pinned R1_SMOKE hashes" if not differ else f"{len(differ)} differ")
    R1.phase("gate_data", t)
    R1.gate(rec)
    return rec


def r1_json(tag):
    return json.loads((R1_RUN / "models" / f"gae_v2_{tag}.json").read_text())


def gate_const_new(views):
    """G-const-new: the f7 constants of the new data and the expected window counts = those of the 4 R1 checkpoints."""
    t = time.time()
    mu, sd = TGV2.norm_constants(R1.VIEWS / "new", "clean")
    exp, exp_val = R1.expected_counts(views)
    rel, bad = 0.0, []
    for tag in R1_TAGS:
        m = r1_json(tag)
        for got, key in ((mu, "add_mean"), (sd, "add_std")):
            want = np.asarray(m[key])
            rel = max(rel, float(np.max(np.abs(got - want) / np.maximum(np.abs(want), 1e-12))))
        if {k: int(v) for k, v in m["n_train"].items()} != exp or {k: int(v) for k, v in m["n_val"].items()} != exp_val:
            bad.append(tag)
    rec = dict(gate="G-const-new", status="PASS" if rel <= 1e-9 and not bad else "FAIL", max_rel=rel, counts_differ=bad,
               n_train=int(sum(exp.values())), n_val=exp_val,
               summary=f"constants max relative difference {rel:.1e}; n_train {sum(exp.values())}")
    R1.phase("gate_const_new", t)
    R1.gate(rec)


def check_versions(meta):
    """mode 'exact' when the library versions equal R1_RUN's, else 'tolerance' (rule fixed before the run)."""
    r1v = json.loads((R1_RUN / "run_meta.json").read_text())["versions"]
    diff = {k: (r1v.get(k), meta["versions"].get(k)) for k in VERSION_KEYS if r1v.get(k) != meta["versions"].get(k)}
    STATE["mode"] = "exact" if not diff else "tolerance"
    R1.STATE["notes"].append(dict(versions_vs_r1=diff, mode=STATE["mode"]))
    log(f"versions vs R1_RUN: {'equal' if not diff else diff} -> mode {STATE['mode']}")
    return STATE["mode"], diff


# ============================================================================ distances, smm, per-seed-k scoring
def distances(cases_src, ckpt_dir, label, tags, workers):
    t = time.time()
    specs = sorted([(c, s, str(ckpt_dir), label, False) for c, s in cases_src], key=lambda a: -R1._size(a[0], a[1]))
    res = {r["case"]: r for r in _run(R1.d_job, specs, workers, tags, f"D[{label}]")}
    bad = [c for c, r in res.items() if not r["finite"]]
    if bad:
        raise SystemExit(f"STOP: non-finite distances for {bad} ({label})")
    R1.phase(f"D_{label}", t)
    return res


def smm_job(a):
    """smoothed member mean m(t) of every tag for one development case (input of p3_levers.calibrate)."""
    case, src, label = a
    t = time.time()
    try:
        ctx, _ = R1.ctx_from_store(case, src, label)
        smm = {tag: PS.smoothed(ctx, P3L.member_mean_z(ctx, tag), P3C.SMOOTH) for tag in R1.TAGS}
        return dict(case=case, smm=smm, s=round(time.time() - t, 1))
    except Exception:                    # noqa: BLE001
        return dict(case=case, error=traceback.format_exc()[-3000:])


def calibrate_per_seed(label, tags, workers):
    res = {r["case"]: r for r in _run(smm_job, [(c, "new", label) for c in R1.DEV], workers, tags, f"smm[{label}]")}
    return {tag: float(P3L.calibrate([res[c]["smm"][tag] for c in R1.DEV])) for tag in tags}


def score_k_job(a):
    """one case: for every tag, q at that tag's own k, then p3c_freeze.run_budget for the 4 arms (the loop of
    r2_r1.score_job with one k per tag; with every k equal it is r2_r1.score_job -- proven by gate RP.0). Optionally the
    per-window scores of the report seeds (x = e22 final scalar, xs = smoothed with 5 windows) and the thresholds."""
    case, src, label, kmap, set_name, save_dir = a
    t = time.time()
    try:
        ctx, _ = R1.ctx_from_store(case, src, label)
        rows, errs, qrows, thr_rows, cols = [], [], [], [], {}
        for tag in R1.TAGS:
            x = E22.final_scalar(ctx, tag)
            q = P3L.q_of(PS.smoothed(ctx, P3L.member_mean_z(ctx, tag), P3C.SMOOTH), kmap[tag])
            qrows.append(dict(set=set_name, subject=case, seed=tag, k=kmap[tag], q_raw=q))
            for name, (fl, cp) in R1.ARMS.items():
                P3C.run_budget(ctx, case, tag, x, q, fl, cp, name, rows, errs)
            if save_dir and tag in REPORT_TAGS:
                xs = PS.smoothed(ctx, x, P3C.SMOOTH)
                s = tag.replace("clean_seed", "s")
                cols[f"x_{s}"], cols[f"xs_{s}"] = x, xs
                for name, (fl, cp) in R1.ARMS.items():
                    top = P3C.budget(q, fl, cp)
                    thr_rows.append(dict(set=set_name, subject=case, seed=tag, budget=name, top=top,
                                         thr=float(np.nanquantile(xs, 1 - top))))
        for r in rows + errs:
            r["set"] = set_name
        if save_dir:
            n = int(ctx["n"])
            df = pd.DataFrame(dict(window=np.arange(n), file_idx=np.asarray(ctx["fidx"]), t_in_file_s=0,
                                   ok=np.asarray(ctx["ok"]).astype(int), ictal=np.asarray(ctx["ict"]).astype(int)))
            for f in np.unique(ctx["fidx"]):
                m = np.flatnonzero(np.asarray(ctx["fidx"]) == f)
                df.loc[m, "t_in_file_s"] = np.arange(len(m)) * E22.WIN
            for k_, v in cols.items():
                df[k_] = np.asarray(v, dtype=np.float32)
            Path(save_dir).mkdir(parents=True, exist_ok=True)
            df.to_csv(Path(save_dir) / f"{case}.csv.gz", index=False, float_format="%.7g", compression="gzip")
        return dict(case=case, rows=rows, errs=errs, q=qrows, thr=thr_rows, score_s=round(time.time() - t, 1))
    except Exception:                    # noqa: BLE001
        return dict(case=case, error=traceback.format_exc()[-3000:])


def all_cases():
    return [(c, "new") for c in R1.DEV + R1.TEST] + [(c, "ext") for c in R1.EXT]


def scoring(label, kmap, tags, workers, save_scores=None):
    t = time.time()
    specs = sorted([(c, s, label, kmap, R1.set_of(c, s), str(save_scores) if (save_scores and R1.set_of(c, s) in SCORE_SETS)
                     else None) for c, s in all_cases()], key=lambda a: -R1._size(a[0], a[1]))
    res = {r["case"]: r for r in _run(score_k_job, specs, workers, tags, f"score[{label}]")}
    R1.phase(f"score_{label}", t)
    order = [c for c, _ in all_cases()]
    return {k: pd.DataFrame([r for c in order for r in res[c][k]]) for k in ("rows", "errs", "q", "thr")}


# ============================================================================ RP.0
def _cmp_rows(mine, ref, mode):
    keys = ROW_KEYS
    mg = mine.merge(ref, on=keys, how="outer", suffixes=("", "_ref"), indicator=True)
    bad = [dict(r) for _, r in mg[mg._merge != "both"][keys + ["_merge"]].iterrows()]
    b = mg[mg._merge == "both"]
    tol = TOL[mode]
    ints = ROW_INT if mode == "exact" else ["n_ref"]
    for c in ints:
        d = b[b[c].astype(np.int64) != b[f"{c}_ref"].astype(np.int64)]
        bad += [dict(**{k: r[k] for k in keys}, col=c, got=int(r[c]), want=int(r[f"{c}_ref"])) for _, r in d.iterrows()]
    if mode == "tolerance":
        for c, lim in (("tp", tol["tp"]), ("fp", tol["fp"])):
            d = b[(b[c].astype(np.int64) - b[f"{c}_ref"].astype(np.int64)).abs() > lim]
            bad += [dict(**{k: r[k] for k in keys}, col=c, got=int(r[c]), want=int(r[f"{c}_ref"])) for _, r in d.iterrows()]
    for c in (ROW_FLOAT if mode == "exact" else ["nonict_h"]):
        a_, r_ = b[c].astype(float).values, b[f"{c}_ref"].astype(float).values
        rel = np.abs(a_ - r_) / np.maximum(np.abs(r_), 1e-12)
        for i in np.flatnonzero(rel > tol["float_rel"]):
            r = b.iloc[i]
            bad.append(dict(**{k: r[k] for k in keys}, col=c, got=float(a_[i]), want=float(r_[i])))
    exact = int(((b.tp.astype(int) == b.tp_ref.astype(int)) & (b.fp.astype(int) == b.fp_ref.astype(int))).sum())
    return int(len(b)), exact, bad


def _cmp_errors(mine, ref):
    keys = ["set", "subject", "seed", "budget"]
    ga = {k: g[ERR_COLS].astype(int).values.tolist() for k, g in mine.groupby(keys)} if len(mine) else {}
    gb = {k: g[ERR_COLS].astype(int).values.tolist() for k, g in ref.groupby(keys)} if len(ref) else {}
    bad = [dict(group=str(k), got=ga.get(k), want=gb.get(k)) for k in sorted(set(ga) | set(gb), key=str)
           if ga.get(k) != gb.get(k)]
    return int(len(ref)), bad


def rp0(workers):
    """RP.0: the committed R1 checkpoints on the new data, this module's path with every k = R1's k, = R1's r13/run."""
    t = time.time()
    mode = STATE["mode"]
    tol = TOL[mode]
    distances(all_cases(), R1_RUN / "models", "rp0", R1_TAGS, workers)
    k42 = calibrate_per_seed("rp0", R1_TAGS, workers)["clean_seed42"]
    sc = scoring("rp0", {t_: K_R1 for t_ in R1_TAGS}, R1_TAGS, workers)
    o = out_dir() / "rp0"
    o.mkdir(parents=True, exist_ok=True)
    sc["rows"].to_csv(o / "per_subject.csv", index=False)
    sc["errs"].to_csv(o / "errors.csv", index=False)
    sc["q"].to_csv(o / "q.csv", index=False)
    ref_rows = pd.read_csv(R1_RUN / "r13" / "run" / "per_subject.csv")
    ref_errs = pd.read_csv(R1_RUN / "r13" / "run" / "errors.csv")
    ref_q = pd.read_csv(R1_RUN / "r13" / "run" / "q.csv")
    n, exact, bad = _cmp_rows(sc["rows"], ref_rows, mode)
    ne, ebad = _cmp_errors(sc["errs"], ref_errs)
    qm = sc["q"].merge(ref_q, on=["set", "subject", "seed"], suffixes=("", "_ref"), how="outer", indicator=True)
    qrel = (qm.q_raw - qm.q_raw_ref).abs() / qm.q_raw_ref.abs().clip(lower=1e-12)
    qbad = int((qm._merge != "both").sum() + (qrel > tol["float_rel"]).sum())
    krel = abs(k42 - K_R1) / abs(K_R1)
    ok = not bad and krel <= tol["k_rel"] and (mode == "tolerance" or (not ebad and not qbad))
    rec = dict(gate="RP.0", status="PASS" if ok else "FAIL", mode=mode, rows=n, exact_rows=exact, mismatches=bad[:50],
               n_mismatch=len(bad), error_pairs=ne, error_groups_differ=len(ebad), error_mismatches=ebad[:10],
               q_rows=int(len(qm)), q_differ=qbad, k_seed42=k42, k_r1=K_R1, k_rel=krel,
               summary=f"mode {mode}: {n} rows ({exact} exact), {ne} error pairs ({len(ebad)} groups differ), "
                       f"q {qbad} differ, k relative {krel:.1e}")
    R1.phase("rp0", t)
    R1.gate(rec)
    return rec


# ============================================================================ G-val
def val_job(a):
    """validation loss of one checkpoint with the code of r2_r1.train_job (clean windows of the 3 validation cases,
    chunks of 512, sum / windows)."""
    tag, ckpt_dir = a
    t = time.time()
    try:
        import torch
        import f1_core as F
        import model_cmp_core as C
        m = json.loads((Path(ckpt_dir) / f"gae_v2_{tag}.json").read_text())
        meta = dict(add_mean=m["add_mean"], add_std=m["add_std"], clip=m["clip"])
        model = F.build("gae")
        model.load_state_dict(torch.load(str(Path(ckpt_dir) / f"gae_v2_{tag}.pt"), map_location="cpu"), strict=True)
        model.eval()
        R1.point_npz(R1.TRAIN + R1.VAL, "new")
        dev = torch.device("cpu")
        vl, nv = 0.0, {}
        with torch.no_grad():
            for s in R1.VAL:
                A, X, T = C._mlp_tensors([s], meta, dev, lambda z: TGV2.mask(z, "clean"))
                nv[s] = int(len(A))
                for i in range(0, len(A), 512):
                    vl += float(F._loss("gae", model, A[i:i + 512], X[i:i + 512], T[i:i + 512]).sum())
        return dict(tag=tag, val=vl / max(1, sum(nv.values())), want=m.get("final_val"), n_val=nv, s=round(time.time() - t, 1))
    except Exception:                    # noqa: BLE001
        return dict(tag=tag, error=traceback.format_exc()[-3000:])


def gate_val(workers):
    t = time.time()
    res = _run(val_job, [(tag, str(R1_RUN / "models")) for tag in R1_TAGS], workers, R1_TAGS, "G-val")
    tol = TOL[STATE["mode"]]["val_rel"]
    det = {r["tag"]: dict(recomputed=r["val"], json=r["want"], rel=abs(r["val"] - r["want"]) / abs(r["want"]), n_val=r["n_val"])
           for r in res}
    bad = [tag for tag, d in det.items() if d["rel"] > tol]
    rec = dict(gate="G-val", status="PASS" if not bad else "FAIL", mode=STATE["mode"], detail=det, bad=bad,
               summary=f"validation loss of the 4 R1 checkpoints recomputed: max relative difference "
                       f"{max(d['rel'] for d in det.values()):.1e}")
    R1.phase("gate_val", t)
    R1.gate(rec)


# ============================================================================ RP1 training
def train_seed4(views, epochs, models_dir):
    """RP1: r2_r1.train_seeds([4]) unchanged (train_job: f7 constants on the new data, window counts, G2, validation
    loss, sanity AUROC, checkpoint in the record format). Resumable through r2_r1.import_models."""
    R1.import_models(models_dir)
    proj = None
    if not (models_dir / f"gae_v2_{NEW_TAG}_DONE.json").exists():
        tt = R1.step_timing(workers=1)
        exp, _ = R1.expected_counts(views)
        proj = (int(np.ceil(sum(exp.values()) / 32)) * epochs * max(tt["ms_per_step"]) / 1000 + 900) / 3600
        R1.STATE["notes"].append(dict(step_timing_1_worker=tt, projected_training_h=round(proj, 2)))
        log(f"step timing (1 worker) {tt} -> projected training {proj:.2f} h (computed estimate)")
    return R1.train_seeds(views, [NEW_SEED], epochs, models_dir, out_dir() / "training", projected_h=proj)


def ckpt_dir_all(models_dir):
    """one folder with the 4 R1 checkpoints and seed 4 (symlinks), for x1_external.model_outputs (PD.CKPT)."""
    d = R1.SCRATCH / "rp_ckpt"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    for tag in R1_TAGS:
        for suf in (".pt", ".json"):
            (d / f"gae_v2_{tag}{suf}").symlink_to(R1_RUN / "models" / f"gae_v2_{tag}{suf}")
    for suf in (".pt", ".json"):
        (d / f"gae_v2_{NEW_TAG}{suf}").symlink_to(Path(models_dir).resolve() / f"gae_v2_{NEW_TAG}{suf}")
    return d


def merge_stores(src_labels, label):
    """the 5-tag distance store = the 4 R1 tags of RP.0 + seed 4 (same windows, checked)."""
    t = time.time()
    d = R1.DSTORE / label
    d.mkdir(parents=True, exist_ok=True)
    for c, _ in all_cases():
        parts = [np.load(R1.DSTORE / s / f"{c}.npz") for s in src_labels]
        if not all(np.array_equal(parts[0]["idx"], p["idx"]) for p in parts):
            raise SystemExit(f"STOP: window index differs between distance stores for {c}")
        arrs = {k: p[k] for p in parts for k in p.files if k != "idx"}
        if sorted(arrs) != sorted(f"{t_}_d" for t_ in RP_TAGS):
            raise SystemExit(f"STOP: distance store of {c} holds {sorted(arrs)}")
        np.savez(d / f"{c}.npz", idx=parts[0]["idx"], **arrs)
    R1.phase(f"merge_{label}", t)


# ============================================================================ RP2 + RP3
def rp2(models_dir, workers):
    t = time.time()
    ck = ckpt_dir_all(models_dir)
    distances(all_cases(), ck, "s4", [NEW_TAG], workers)
    merge_stores(["rp0", "s4"], "rp")
    kmap = calibrate_per_seed("rp", RP_TAGS, workers)
    o = out_dir() / "rp2"
    o.mkdir(parents=True, exist_ok=True)
    _jdump(o / "k.json", dict(k=kmap, k_r1=K_R1, cases=list(R1.DEV), rule="p3_levers.calibrate on each seed's own model: "
                              "median over the 15 development cases of q_i(k) = 0.005"))
    log("RP2 k per seed: " + jdumps(kmap))
    sc = scoring("rp", kmap, RP_TAGS, workers, save_scores=o / "scores")
    sc["rows"].to_csv(o / "per_subject.csv", index=False)
    sc["errs"].to_csv(o / "errors.csv", index=False)
    sc["q"].to_csv(o / "q.csv", index=False)
    sc["thr"].to_csv(o / "thresholds.csv", index=False)
    n_want = (len(R1.DEV) + len(R1.TEST) + len(R1.EXT)) * len(RP_TAGS) * len(R1.ARMS) * 3
    rec = dict(gate="RP2-complete", status="PASS" if len(sc["rows"]) == n_want else "FAIL", rows=int(len(sc["rows"])),
               expected=n_want, k=kmap, scores_files=len(list((o / "scores").glob("*.csv.gz"))),
               scores_mb=round(sum(p.stat().st_size for p in (o / "scores").glob("*.csv.gz")) / 1e6, 2),
               summary=f"{len(sc['rows'])} rows (expected {n_want}); per-window scores of "
                       f"{len(list((o / 'scores').glob('*.csv.gz')))} cases")
    R1.phase("rp2", t)
    R1.gate(rec)
    return kmap


def choose_demo(vals):
    """RP3 rule: lowest validation loss among seeds 1-4; values within TIE_REL (relative) of the minimum -> smaller seed."""
    lo = min(vals.values())
    tied = sorted(s for s, v in vals.items() if (v - lo) / abs(lo) <= TIE_REL)
    return tied[0], tied


def rp3(models_dir, kmap):
    vals, src = {}, {}
    for tag in REPORT_TAGS:
        p = (Path(models_dir) if tag == NEW_TAG else R1_RUN / "models") / f"gae_v2_{tag}.json"
        vals[int(tag.split("seed")[1])] = float(json.loads(p.read_text())["final_val"])
        src[tag] = p
    seed, tied = choose_demo(vals)
    tag = f"clean_seed{seed}"
    m = json.loads(src[tag].read_text())
    pt = src[tag].with_suffix(".pt")
    rp_, rr_ = pt.resolve(), Path(REPO).resolve()
    rel = str(rp_.relative_to(rr_)) if rr_ in rp_.parents else f"results/r2/r1_system/rp/models/{pt.name}"
    d = dict(rule="lowest validation loss (final_val: loss of the recipe on the clean windows of chb10, chb11, chb22; no "
                  "test data) among seeds 1-4; ties within 1e-9 relative -> smaller seed", validation_loss=vals, tied=tied,
             seed=seed, tag=tag, checkpoint=rel, checkpoint_sha256=sha256_file(pt), k=kmap[tag],
             add_mean=m["add_mean"], add_std=m["add_std"], clip=m["clip"], budget_final=[0.005, P3C.CAP], smooth=P3C.SMOOTH,
             localizer="cpd")
    _jdump(out_dir() / "demo_model.json", d)
    R1.gate(dict(gate="RP3-demo", status="PASS", seed=seed, validation_loss=vals,
                 summary=f"demo model = seed {seed} (validation losses {jdumps(vals)})"))
    return d


def summary_md():
    L = [f"# RP_RUN — gates and timing (no research number; mode {STATE['mode']})\n", "| gate | status | summary |",
         "|---|---|---|"]
    L += [f"| {g['gate']} | {g['status']} | {g.get('summary', '')} |" for g in R1.STATE["gates"]]
    L += ["", f"Phases (s): {jdumps(R1.STATE['phases'])}", "", "Tables: `python src/r2_rp_aggregate.py --rp "
          "results/r2/r1_system/rp` (committed before this run)."]
    (out_dir() / "SUMMARY.md").write_text("\n".join(L) + "\n")
    return "\n".join(L)
