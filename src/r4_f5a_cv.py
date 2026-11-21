#!/usr/bin/env python
"""
r4_f5a_cv.py -- F5a Part B: the offset diagnosis on the CV models (GAE and MLP-AE, partitions 0-5, 4 folds each = 48
committed checkpoints), extraction run (Track F, chat D36-F; design results/r4_f5a/DESIGN_F5A.md §10, approved by the
author 21/11/2026 12:43). Inference only, written before any Part B output.

Models (committed, never retrained): partition 0 = R2_A results/r2/r2_cv/a/jobs/{model}_f{f}/{model}_fold{f}_seed42.pt;
partitions 1-5 = R3 results/r2/r3_repcv/p{p}/jobs/{model}_fold{f}/{model}_p{p}_fold{f}_seed{p}.pt, each with its json
meta (fold constants of the complete data). Data: thesis-r2-chbmit-features (complete data, 24 cases, out-of-fold).
Record code imported READ ONLY: r2_r2 (views, G-data, D0', worker set-up), f1_core (manifests, build, encode_D,
evaluate_case), model_cmp_core (make_ctx, scalars, calibrate), p3_levers / p2_scalars / e18_cpd_localizer (chain).
Per job (model, partition, fold): k recomputed on the fold's training cases (gate G-k = the job's committed fit.json k,
relative 1e-6); for every held-out case, f1_core.evaluate_case (the record function) must give the job's committed
per_subject rows (own / fixed0.005 x detector / localized: tp, fp, n_ref) and seizure caught flags exactly (G-rows);
then the extraction of r4_f5a (arms own = clip(q, 0.005, 0.02) and fixed = 0.005; detector / localizer / hybrid rows,
matched error pairs with the event record, per-seizure segments of the unsmoothed scalar x) with G-eng (its detector and
localizer counts = the record rows). Model-free series (f7) are written once per case (partition 0 GAE jobs).
Outputs WORK/r4/f5a_cv/: run_meta.json, gates.json, data_sha256.csv, data_gate.json, d0.json, events.csv, rows.csv,
seizures.csv, series.csv.gz (model, partition, seizure index, window, ok, ictal, x), mf_series.csv.gz, jobs.csv,
projection.json, SUMMARY.md. No reading here: src/r4_f5a_cv_aggregate.py (committed first).
  python src/r4_f5a_cv.py [--workers N] [--smoke-only]
Test mode (synthetic world, build container only): R2_TEST=1 (see src/r4_f5a_cv_synthetic_test.py).
"""
import hashlib
import json
import os
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

import r2_r2 as R2                       # noqa: E402  (record, read only; its own import guard)

F, C = R2.F, R2.C
PS, P3L = C.PS, C.P3L
E18 = P3L.E18
_OUT = [m.__name__ for m in (F, C, PS, P3L, E18) if (REPO / "src") not in Path(m.__file__).resolve().parents]
if _OUT:
    raise SystemExit(f"STOP: record modules imported from outside {REPO / 'src'}: {_OUT}")
log = R2.log

PARTS = (0, 1, 2, 3, 4, 5)
MODELS = ("gae", "mlp")
FOLDS = (1, 2, 3, 4)
WIN, MARGIN, SMOOTH = C.WIN, P3L.MARGIN, C.SMOOTH
ARMS = {"own": (C.FLOOR, C.CAP), "fixed": (0.005, 0.005)}
REC_POINT = {"own": "own", "fixed": "fixed0.005"}
SEG_PRE_S, SEG_POST_S = 300, 300
EXTRA_W = 2 * MARGIN
MF = ("ll", "d", "t", "a", "b", "g", "pow")
REFUSE_H = 10.5
TEST_MODE = bool(os.environ.get("R2_TEST"))
TAG = os.environ.get("F5A_TAG", "f5a_cv")
STATE = R2.STATE
TOL_K = 1e-6

CODE_FILES = {n: Path(m.__file__) for n, m in (("r4_f5a_cv", sys.modules[__name__]), ("r2_r2", R2), ("f1_core", F),
                                                ("model_cmp_core", C), ("p3_levers", P3L), ("p2_scalars", PS),
                                                ("e18", E18))}


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


CODE_SHA = sha16(__file__)


def code_shas():
    return {n: sha16(p) for n, p in CODE_FILES.items()}


# ============================================================================ helpers identical to r4_f5a.py
def robust_z_cols(V, valid):
    out = np.full(V.shape, np.nan)
    for j in range(V.shape[1]):
        v = V[valid, j]
        v = v[np.isfinite(v)]
        if not len(v):
            continue
        med = np.median(v)
        mad = 1.4826 * np.median(np.abs(v - med))
        out[valid, j] = (V[valid, j] - med) / (mad + 1e-9)
    return out


def mf_series(f7, ok):
    f7 = np.asarray(f7, np.float64)
    cols = {"ll": f7[..., 5], "d": f7[..., 0], "t": f7[..., 1], "a": f7[..., 2], "b": f7[..., 3], "g": f7[..., 4]}
    with np.errstate(over="ignore", invalid="ignore"):
        mx = np.max(f7[..., :5], axis=-1)
        cols["pow"] = mx + np.log(np.sum(np.exp(f7[..., :5] - mx[..., None]), axis=-1))
    out = {}
    for k in MF:
        Zc = robust_z_cols(cols[k], ok)
        with np.errstate(invalid="ignore"):
            out[k] = np.where(ok, np.nanmean(np.where(np.isfinite(Zc), Zc, np.nan), axis=1), np.nan) \
                if ok.any() else np.full(len(ok), np.nan)
    return out


def above_runs(sm_f, thr, aw, bw):
    a = np.nan_to_num(sm_f[aw:bw], nan=-np.inf) > thr
    return int(np.sum(a[1:] & ~a[:-1]) + (1 if len(a) and a[0] else 0))


# ============================================================================ checkpoints
def ckpt_paths(model, p, f):
    if int(p) == 0:
        jd = REPO / "results" / "r2" / "r2_cv" / "a" / "jobs" / f"{model}_f{f}"
        stem = f"{model}_fold{f}_seed42"
    else:
        jd = REPO / "results" / "r2" / "r3_repcv" / f"p{p}" / "jobs" / f"{model}_fold{f}"
        stem = f"{model}_p{p}_fold{f}_seed{F.seed_of(p)}"
    return jd, jd / f"{stem}.pt", jd / f"{stem}.json"


def load_model(model, p, f):
    import torch
    jd, pt, js = ckpt_paths(model, p, f)
    for q in (pt, js, jd / "per_subject.csv", jd / "seizures.csv", jd / "fit.json"):
        if not q.exists():
            raise SystemExit(f"STOP: committed file missing: {q}")
    meta = json.loads(js.read_text())
    m = F.build(model)
    m.load_state_dict(torch.load(str(pt), map_location="cpu"), strict=True)
    return m.eval(), meta, jd, R2.sha256_file(pt)


# ============================================================================ the job
def extract_case(model, p, f, ctx, x, m, k, set_rows, events, seizures, parts, mf_parts, want_mf):
    """the r4_f5a extraction for one held-out case (arms own / fixed). Returns G-eng problems."""
    bad = []
    case = ctx["s"]
    ok, fidx = ctx["ok"], ctx["fidx"]
    files = np.unique(fidx)
    fwin = {fi: np.flatnonzero(fidx == fi) for fi in files}
    refs = P3L.refs_of(ctx)
    sm = PS.smoothed(ctx, x, SMOOTH)
    q = P3L.q_of(PS.smoothed(ctx, m, SMOOTH), k)
    seg_need = {}
    for arm, (fl, cp) in ARMS.items():
        top = float(np.clip(q, fl, max(cp, fl))) if arm == "own" else fl
        det = PS.d1_events(ctx, x, SMOOTH, top)
        thr = np.nanquantile(sm, 1 - top)
        loc_c, pair_c = P3L.localize(ctx, x, det, thr, "cpd")
        loc_h, pair_h = P3L.localize(ctx, x, det, thr, "hybrid")
        for st, ev in (("detector", det), ("cpd", loc_c), ("hybrid", loc_h)):
            tp, fp, nr, h = PS.score(ctx, ev)
            set_rows.append(dict(model=model, partition=p, fold=f, subject=case, arm=arm, stage=st, top=top, tp=tp, fp=fp,
                                 n_ref=nr, nonict_h=h))
        for f_, ra, rb, h0, h1 in E18.match_errors(refs, det):
            mw = fwin[f_]
            xf, okf, smf = x[mw], ok[mw], sm[mw]
            aw, bw = h0 // WIN, h1 // WIN
            ca, cb, used = E18.cpd_event(xf, okf, aw, bw, MARGIN)
            ua, ub = E18.run_event(xf, okf, aw, bw, MARGIN, thr)
            s0, s1 = max(0, aw - MARGIN), min(len(xf), bw + MARGIN)
            c0, c1 = pair_c[(f_, h0, h1)]
            y0, y1 = pair_h[(f_, h0, h1)]
            if (c0, c1) != (ca * WIN, cb * WIN):
                bad.append(f"{case} {arm} file {f_} event {h0}: localizer pair differs")
            nref = sum(1 for (a_, b_) in refs.get(f_, []) if b_ > h0 and a_ < h1)
            events.append(dict(model=model, partition=p, fold=f, subject=case, arm=arm, file=int(f_), n_file=int(len(xf)),
                               ref_on=int(ra), ref_off=int(rb), ref_dur=int(rb - ra), det_a=int(h0), det_b=int(h1),
                               ev_dur=int(h1 - h0), top=float(top), thr=float(thr), q_raw=float(q), used_cpd=bool(used),
                               cpd_a=int(ca * WIN), cpd_b=int(cb * WIN), win_a=int(s0 * WIN), win_b=int(s1 * WIN),
                               run_a=int(ua * WIN), run_b=int(ub * WIN), hyb_a=int(y0), hyb_b=int(y1),
                               n_runs=above_runs(smf, thr, aw, bw), n_refs=int(nref),
                               det_on=int(h0 - ra), det_off=int(h1 - rb), cpd_on=int(c0 - ra), cpd_off=int(c1 - rb),
                               hyb_on=int(y0 - ra), hyb_off=int(y1 - rb)))
            key = (int(f_), int(ra), int(rb))
            lo, hi = seg_need.get(key, (aw - EXTRA_W, bw + EXTRA_W))
            seg_need[key] = (min(lo, aw - EXTRA_W), max(hi, bw + EXTRA_W))
    mf = mf_series(np.asarray(ctx["z"]["f7"]), ok) if want_mf else None
    for fi in files:
        mw = fwin[fi]
        nf = len(mw)
        for (ra, rb) in refs.get(fi, []):
            sid = f"{case}|{int(fi)}|{int(ra)}"
            lo0, hi0 = max(0, ra // WIN - SEG_PRE_S // WIN), min(nf, rb // WIN + SEG_POST_S // WIN)
            need = seg_need.get((int(fi), int(ra), int(rb)))
            lo, hi = (min(lo0, max(0, need[0])), max(hi0, min(nf, need[1]))) if need else (lo0, hi0)
            seizures.append(dict(model=model, partition=p, fold=f, subject=case, sz=sid, file=int(fi), n_file=int(nf),
                                 ref_on=int(ra), ref_off=int(rb), seg_a=int(lo * WIN), seg_b=int(hi * WIN),
                                 matched=need is not None))
            w = np.arange(lo, hi)
            g = mw[w]
            parts.append(pd.DataFrame(dict(model=model, partition=p, sz=sid, w=w.astype(int), ok=ok[g].astype(int),
                                           ict=ctx["ict"][g].astype(int), x=x[g])))
            if want_mf:
                w0 = np.arange(lo0, hi0)
                g0 = mw[w0]
                d = dict(sz=sid, w=w0.astype(int), ok=ok[g0].astype(int))
                for kk in MF:
                    d[f"mf_{kk}"] = mf[kk][g0]
                mf_parts.append(pd.DataFrame(d))
    return bad


def cv_job(a):
    model, p, f = a
    t = time.time()
    try:
        R2.use_view("new")
        mdl, meta, jd, ck_sha = load_model(model, p, f)
        man = F.manifest(p)[int(f)]
        if sorted(man["train_cases"]) != sorted(meta["train_cases"]) or list(man["held_out_cases"]) != list(meta["held_out_cases"]):
            raise SystemExit(f"{model} p{p} f{f}: checkpoint meta cases differ from the manifest")
        D_fn = lambda ctx: F.encode_D(model, mdl, meta, ctx)          # noqa: E731
        ms = []
        for s in sorted(man["train_cases"]):
            ctx = C.make_ctx(s)
            ms.append((ctx, C.scalars("D", ctx, D_fn(ctx))[1]))
        k = C.calibrate(ms)
        del ms
        k_rec = float(json.loads((jd / "fit.json").read_text())["k"])
        per_rec = pd.read_csv(jd / "per_subject.csv")
        seiz_rec = pd.read_csv(jd / "seizures.csv")
        rows_bad, eng_bad = [], []
        set_rows, events, seizures, parts, mf_parts = [], [], [], [], []
        for s in man["held_out_cases"]:
            ctx = C.make_ctx(s)
            x, m = C.scalars("D", ctx, D_fn(ctx))
            per, _cur, _au, seiz = F.evaluate_case(model, p, f, ctx, x, m, k)
            pr = per_rec[per_rec.subject == s].set_index(["point", "stage"])
            for r in per:
                key = (r["point"], r["stage"])
                if key not in pr.index or any(int(pr.loc[key, c]) != int(r[c]) for c in ("tp", "fp", "n_ref")):
                    rows_bad.append(f"{s} {key}")
            sr = seiz_rec[seiz_rec.subject == s].sort_values(["file", "onset_s"])
            mine = pd.DataFrame(seiz).sort_values(["file", "onset_s"]) if seiz else pd.DataFrame(columns=sr.columns)
            if len(sr) != len(mine) or not np.array_equal(sr.caught.astype(bool).values, mine.caught.astype(bool).values):
                rows_bad.append(f"{s} caught flags")
            n0 = len(set_rows)
            eng_bad += extract_case(model, p, f, ctx, x, m, k, set_rows, events, seizures, parts, mf_parts,
                                    want_mf=(int(p) == 0 and model == "gae"))
            mine_rows = pd.DataFrame(set_rows[n0:])
            for arm, point in REC_POINT.items():
                for st, rst in (("detector", "detector"), ("cpd", "localized")):
                    a_ = mine_rows[(mine_rows.arm == arm) & (mine_rows.stage == st)]
                    b_ = [r for r in per if r["point"] == point and r["stage"] == rst]
                    if len(a_) != 1 or len(b_) != 1 or (int(a_.tp.iloc[0]), int(a_.fp.iloc[0])) != (b_[0]["tp"], b_[0]["fp"]):
                        eng_bad.append(f"{s} {arm} {st}: extraction counts differ from evaluate_case")
        d = R2.SCRATCH / "f5acv"
        d.mkdir(parents=True, exist_ok=True)
        stem = f"{model}_p{p}_f{f}"
        (pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()).to_pickle(d / f"{stem}_x.pkl")
        if mf_parts:
            pd.concat(mf_parts, ignore_index=True).to_pickle(d / f"{stem}_mf.pkl")
        import resource
        return dict(model=model, partition=int(p), fold=int(f), k=k, k_rec=k_rec, rows_bad=rows_bad, eng_bad=eng_bad,
                    set_rows=set_rows, events=events, seizures=seizures, ckpt_sha256=ck_sha, shas=code_shas(),
                    s=round(time.time() - t, 1), peak_rss_mb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
                    held_out=list(man["held_out_cases"]), mf=bool(mf_parts))
    except SystemExit as e:
        return dict(model=model, partition=p, fold=f, error=f"STOP: {e}")
    except Exception:                    # noqa: BLE001
        return dict(model=model, partition=p, fold=f, error=traceback.format_exc()[-3000:])


def _run(specs, workers, what):
    out = []
    if not specs:
        return out
    if workers <= 1:
        R2._init_worker(R2._env())
        it, pool = map(cv_job, specs), None
    else:
        import multiprocessing as mp
        pool = mp.get_context("spawn").Pool(min(workers, len(specs)), initializer=R2._init_worker,
                                            initargs=(R2._env(),), maxtasksperchild=1)
        it = pool.imap_unordered(cv_job, specs)
    try:
        for r in it:
            if r.get("error"):
                raise SystemExit(f"{what} {r['model']} p{r['partition']} f{r['fold']}: {r['error']}")
            out.append(r)
            log(f"{what} {r['model']} p{r['partition']} f{r['fold']} done ({r['s']} s)")
    finally:
        if pool is not None:
            pool.terminate()
    return out


def gates_of(res, label):
    kb = {f"{r['model']} p{r['partition']} f{r['fold']}": (r["k"], r["k_rec"]) for r in res
          if abs(r["k"] - r["k_rec"]) > TOL_K * abs(r["k_rec"])}
    R2.gate(dict(gate=f"G-k[{label}]", status="PASS" if not kb else "FAIL", bad=kb,
                 summary=f"k recomputed = committed fit.json k (relative 1e-6) in {len(res)} jobs" if not kb else str(kb)))
    rb = {f"{r['model']} p{r['partition']} f{r['fold']}": r["rows_bad"][:5] for r in res if r["rows_bad"]}
    R2.gate(dict(gate=f"G-rows[{label}]", status="PASS" if not rb else "FAIL", bad=rb,
                 summary=f"evaluate_case rows and caught flags = the committed per_subject / seizures in {len(res)} jobs"
                 if not rb else str(rb)))
    eb = {f"{r['model']} p{r['partition']} f{r['fold']}": r["eng_bad"][:5] for r in res if r["eng_bad"]}
    R2.gate(dict(gate=f"G-eng[{label}]", status="PASS" if not eb else "FAIL", bad=eb,
                 pairs=int(sum(len(r["events"]) for r in res)),
                 summary=f"extraction counts = evaluate_case ({sum(len(r['events']) for r in res)} pairs)" if not eb else str(eb)))
    seg = []
    for r in res:
        S = pd.DataFrame(r["seizures"])
        for ev in r["events"]:
            s = S[(S.subject == ev["subject"]) & (S.file == ev["file"]) & (S.ref_on == ev["ref_on"])]
            need_a = max(0, ev["win_a"] - MARGIN * WIN)
            need_b = min(ev["n_file"] * WIN, ev["win_b"] + MARGIN * WIN)
            if len(s) != 1 or s.seg_a.iloc[0] > need_a or s.seg_b.iloc[0] < need_b:
                seg.append(f"{r['model']} p{r['partition']} {ev['subject']} {ev['file']} {ev['ref_on']}")
    R2.gate(dict(gate=f"G-seg[{label}]", status="PASS" if not seg else "FAIL", bad=seg[:20],
                 summary="every search window +- 15 windows lies inside its stored segment" if not seg else str(seg[:5])))
    want = code_shas()
    wb = sorted({f"{r['model']} p{r['partition']} f{r['fold']}" for r in res if r["shas"] != want})
    R2.gate(dict(gate=f"G-worker-sha[{label}]", status="PASS" if not wb else "FAIL", bad=wb, want=want,
                 summary=f"{len(res)} jobs ran r4_f5a_cv {want['r4_f5a_cv']}, r2_r2 {want['r2_r2']}, f1_core {want['f1_core']}"))


def write_outputs(res):
    o = R2.out_dir()
    pd.DataFrame([e for r in res for e in r["events"]]).to_csv(o / "events.csv", index=False)
    pd.DataFrame([e for r in res for e in r["set_rows"]]).to_csv(o / "rows.csv", index=False)
    pd.DataFrame([e for r in res for e in r["seizures"]]).to_csv(o / "seizures.csv", index=False)
    d = R2.SCRATCH / "f5acv"
    key = lambda r: (r["model"], r["partition"], r["fold"])                          # noqa: E731
    X = pd.concat([pd.read_pickle(d / f"{r['model']}_p{r['partition']}_f{r['fold']}_x.pkl") for r in sorted(res, key=key)],
                  ignore_index=True)
    X.to_csv(o / "series.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    mfs = [d / f"{r['model']}_p{r['partition']}_f{r['fold']}_mf.pkl" for r in sorted(res, key=key) if r["mf"]]
    if mfs:
        pd.concat([pd.read_pickle(q) for q in mfs], ignore_index=True).to_csv(
            o / "mf_series.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    pd.DataFrame([dict(model=r["model"], partition=r["partition"], fold=r["fold"], k=r["k"], k_rec=r["k_rec"], s=r["s"],
                       peak_rss_mb=r["peak_rss_mb"], pairs=len(r["events"]), ckpt_sha256=r["ckpt_sha256"])
                  for r in sorted(res, key=key)]).to_csv(o / "jobs.csv", index=False)


def build_new_view():
    """SCRATCH/r2_views/new/{case}.npz -> thesis-r2-chbmit-features (r2_r2.build_views without the earlier copy, which
    this run does not use). Symlink, else hard link, else copy."""
    t = time.time()
    shutil.rmtree(R2.VIEWS, ignore_errors=True)
    src = {"new": {}}
    for c in R2.ALL:
        hits = R2._new_hits(c)
        if not hits:
            raise SystemExit(f"STOP G-data: thesis-r2-chbmit-features/{c}.npz not found under {R2.INPUT}")
        if len({h.stat().st_size for h in hits}) != 1:
            raise SystemExit(f"STOP G-data: copies of {c}.npz differ in size: {hits}")
        src["new"][c] = hits[0]
    d = R2.VIEWS / "new"
    d.mkdir(parents=True, exist_ok=True)
    for c, p in src["new"].items():
        dst = d / f"{c}.npz"
        for how in (dst.symlink_to, lambda q: os.link(q, dst), lambda q: shutil.copyfile(q, dst)):
            try:
                how(p)
                break
            except OSError:
                continue
    R2.phase("views", t)
    return {"new": {c: str(p) for c, p in src["new"].items()}}


def main(notebook="F5A_CV", repo_commit="local", workers=None, smoke_only=False):
    R2.OUT_ROOT = R2.WORK / "r4"
    workers = int(workers or os.environ.get("F5A_WORKERS") or R2.n_workers())
    meta = R2.run_meta(TAG, notebook, repo_commit)
    meta.update(r4_f5a_cv_sha=CODE_SHA, code_shas=code_shas(), workers=workers, partitions=list(PARTS))
    try:
        meta["cpu_model"] = next((ln.split(":", 1)[1].strip() for ln in open("/proc/cpuinfo") if ln.startswith("model name")),
                                 None)
    except OSError:
        meta["cpu_model"] = None
    R2._jdump(R2.out_dir() / "run_meta.json", meta)
    src = build_new_view()
    R2.gate_data(src)
    R2.use_view("new")
    R2.gate_d0prime()
    # ---- SMOKE: one GAE and one MLP-AE fold of partition 0, measured
    t = time.time()
    STATE["tag"] = f"{TAG}/smoke"
    res = _run([("gae", 0, 1), ("mlp", 0, 1)], min(workers, 2), "smoke")
    gates_of(res, "smoke")
    write_outputs(res)
    smoke_s = time.time() - t
    per_job = {r["model"]: r["s"] for r in res}
    n_jobs = len(PARTS) * len(FOLDS)
    proj = dict(smoke_s=round(smoke_s, 1), job_s=per_job, workers=workers,
                note="computed: (gae job s + mlp job s) x 24 / workers x 1.15 (fold sizes differ)",
                projected_h=round((per_job["gae"] + per_job["mlp"]) * n_jobs / max(workers, 1) * 1.15 / 3600, 2))
    STATE["tag"] = TAG
    R2._jdump(R2.out_dir() / "projection.json", proj)
    R2.gate(dict(gate="SMOKE", status="PASS" if proj["projected_h"] <= REFUSE_H else "FAIL", **proj,
                 summary=f"smoke {smoke_s:.0f} s; full run projected {proj['projected_h']} h"))
    if smoke_only:
        return
    # ---- FULL: 48 jobs, the largest first (GAE before MLP-AE)
    t = time.time()
    specs = [(m, p, f) for m in MODELS for p in PARTS for f in FOLDS]
    res = _run(specs, workers, "cv")
    R2.phase("cv_full", t)
    gates_of(res, "full")
    write_outputs(res)
    R2.finish_meta(dict(pairs=int(sum(len(r["events"]) for r in res)), jobs=len(res)))
    (R2.out_dir() / "SUMMARY.md").write_text(
        f"# F5A_CV run ({notebook}, commit {repo_commit})\n\nEvery gate PASS (gates.json). Outputs: events.csv, rows.csv, "
        "seizures.csv, series.csv.gz, mf_series.csv.gz, jobs.csv. No reading here: src/r4_f5a_cv_aggregate.py "
        "(committed before this run).\n", encoding="utf-8")
    log("F5A_CV done")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int)
    ap.add_argument("--smoke-only", action="store_true")
    a = ap.parse_args()
    main(workers=a.workers, smoke_only=a.smoke_only)
