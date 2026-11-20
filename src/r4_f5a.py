#!/usr/bin/env python
"""
r4_f5a.py -- F5a offset verification and diagnosis on the V5 model, extraction run (Track F, chat D36-F; design
results/r4_f5a/DESIGN_F5A.md, approved by the author 21/11/2026 02:37). Inference only, written before any F5a output.

What it does (Kaggle CPU): the four committed V5 checkpoints data/models_v2/gae_v2_clean_seed{42,1,2,3}.pt on the
defense-time data copy (v9-x3-fold1/3) and the external features (thesis-r2-external-features), through the record code
imported READ ONLY via r2_r1 (r2_r1.r10 = distances + record scoring + gates R1.0-dev / R1.0-test / GE / G-k). Then, per
case, seed and arm (own = L2f, fixed = frozen), from the same quantities as p3c_freeze.run_budget:
  events.csv   one row per matched pair (e18_cpd_localizer.match_errors on the detector events): reference, detector
               event, threshold, localizer boundaries and acceptance (e18.cpd_event), search window, run-rule boundaries
               (e18.run_event), hybrid boundaries (p3_levers.localize), above-threshold runs inside the event, references
               covered by the event, and the six signed errors (= run_budget's, gate G-eng)
  seizures.csv one row per annotated seizure: file length, segment stored, matched flags
  series.csv.gz per annotated seizure, every window of [onset - 300 s, offset + 300 s] widened to each matched event
               +- 30 windows (inside the file): ok, ictal, x (unsmoothed final scalar) and m (member-mean robust z) of the
               4 seeds, and model-free series from the cache's f7 node features (channel mean of the per-channel patient
               robust z of log line length, the 5 log band powers and the log total power; no labels)
Gates (STOP unless PASS): G-self, G-data, SMOKE (chb01, chb03, first external case; projection <= 10.5 h), R1.0-dev,
R1.0-test, GE, G-k (r2_r1.r10), G-eng, G-seg, G-mf, G-worker-sha. No reading here: src/r4_f5a_aggregate.py (committed
first) makes every table.
  python src/r4_f5a.py [--workers N] [--smoke-only]
Test mode (synthetic world, build container only): R2_TEST=1 (see src/r4_f5a_synthetic_test.py).
"""
import hashlib
import os
import platform
import shutil
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

if platform.system() == "Windows" and "resource" not in sys.modules:      # r2_r1 logs peak memory with `resource`
    import types
    _r = types.ModuleType("resource")
    _r.RUSAGE_SELF, _r.RUSAGE_CHILDREN = 0, -1
    _r.getrusage = lambda *_: types.SimpleNamespace(ru_maxrss=0)
    sys.modules["resource"] = _r

REPO = Path(os.environ.get("THESIS_REPO", Path(__file__).resolve().parents[1]))
for _p in ("src", "src/dataprep", "src/retrain", "src/phaseB", "src/phaseC"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import r2_r1 as R1                       # noqa: E402  (import guard: record modules from REPO/src only)

PS, P3L, P3C, E22, X1, R0 = R1.PS, R1.P3L, R1.P3C, R1.E22, R1.X1, R1.R0
E18 = P3C.E18
if (REPO / "src") not in Path(E18.__file__).resolve().parents:
    raise SystemExit(f"STOP: e18_cpd_localizer imported from outside {REPO / 'src'}")
log = R1.log

TAGS, DEV, TEST, EXT = R1.TAGS, list(R1.DEV), list(R1.TEST), list(R1.EXT)
K_RECORD = R1.K_RECORD
ARMS = {"own": R1.ARMS["L2f"], "fixed": R1.ARMS["frozen"]}
WIN, MARGIN, SMOOTH = PS.WIN, P3L.MARGIN, P3C.SMOOTH
SEG_PRE_S, SEG_POST_S = 300, 300          # segment around each annotated seizure (seconds)
EXTRA_W = 2 * MARGIN                      # every matched event +- 30 windows (D5b margin 30) inside the segment
MF = ("ll", "d", "t", "a", "b", "g", "pow")   # f7 columns 5, 0..4, log total power
REFUSE_H = 10.5
TEST_MODE = bool(os.environ.get("R2_TEST"))
TAG = os.environ.get("F5A_TAG", "f5a_v5")
STATE = R1.STATE

CODE_FILES = {n: Path(m.__file__) for n, m in (("r4_f5a", sys.modules[__name__]), ("r2_r1", R1), ("p3c_freeze", P3C),
                                                ("p3_levers", P3L), ("p2_scalars", PS), ("e22", E22),
                                                ("x1_external", X1), ("e18", E18))}


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


CODE_SHA = sha16(__file__)


def code_shas():
    return {n: sha16(p) for n, p in CODE_FILES.items()}


# ============================================================================ inputs (as eur_abl.build_views / gate_data)
def build_views(dev, test, ext):
    """SCRATCH/r1_views/{earlier,ext}: earlier = the v9-x3-fold* record .npz; ext = thesis-r2-external-features.
    Symlink, else hard link, else copy (Windows)."""
    t = time.time()
    shutil.rmtree(R1.VIEWS, ignore_errors=True)
    src = {"earlier": {c: R0.locate_earlier(c) for c in list(dev) + list(test)},
           "ext": {c: R1._one_copy([p for p in sorted(R1.INPUT.rglob(f"{c}_lf.npz"))
                                    if R1._under(p, "thesis-r2-external-features")], f"{c}_lf.npz") for c in ext}}
    for kind, m in src.items():
        d = R1.VIEWS / kind
        d.mkdir(parents=True, exist_ok=True)
        for c, p in m.items():
            dst = d / (f"{c}_lf.npz" if kind == "ext" else f"{c}.npz")
            for how in (dst.symlink_to, lambda q: os.link(q, dst), lambda q: shutil.copyfile(q, dst)):
                try:
                    how(p)
                    break
                except OSError:
                    continue
    R1.phase("views", t)
    return src


def gate_data(src):
    rows, bad = [], []
    prov = R0.provenance_v2()
    pin_f = REPO / "results" / "r2" / "r1_system" / "smoke" / "data_sha256.csv"
    pin = pd.read_csv(pin_f) if pin_f.exists() else pd.DataFrame(columns=["dataset", "file", "sha256"])
    pin = pin[pin.dataset == "thesis-r2-external-features"].set_index("file").sha256.to_dict()
    for kind, m in src.items():
        for c, p in m.items():
            s = R0.sha256_file(p)
            want = (prov.get(c, (None, None))[1] if kind == "earlier" else pin.get(Path(p).name))
            rows.append(dict(kind=kind, case=c, file=Path(p).name, bytes=Path(p).stat().st_size, sha256=s, want=want,
                             source=str(p)))
            if want is None and not TEST_MODE:
                bad.append(f"{c}: no pinned sha256")
            elif want is not None and s != want:
                bad.append(f"{c}: sha256 {s[:16]} != {want[:16]}")
    pd.DataFrame(rows).to_csv(R1.out_dir() / "data_sha256.csv", index=False)
    R1.gate(dict(gate="G-data", status="PASS" if not bad else "FAIL", files=len(rows), bad=bad[:20],
                 pinned=int(sum(r["want"] is not None for r in rows)),
                 summary=f"{len(rows)} files hashed, {len(bad)} differ" + (" (test mode: unpinned allowed)" if TEST_MODE else "")))


# ============================================================================ building blocks
def robust_z_cols(V, valid):
    """V: n x c; per column robust z over the valid rows (median, 1.4826 MAD); NaN elsewhere."""
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
    """model-free series (full window axis): channel mean of the per-channel patient robust z of log line length, the
    five log band powers (delta .. gamma) and the log total power (log of the summed band powers). f7: n x 18 x 7 =
    [log band power x 5 (delta, theta, alpha, beta, gamma), log line length, signed-log kurtosis]."""
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
    """number of runs of the smoothed scalar above the threshold inside the detector event [aw, bw) (windows)."""
    a = np.nan_to_num(sm_f[aw:bw], nan=-np.inf) > thr
    return int(np.sum(a[1:] & ~a[:-1]) + (1 if len(a) and a[0] else 0))


def self_checks():
    """G-self: unit checks of the building blocks on synthetic arrays."""
    rng = np.random.default_rng(0)
    n = 400
    ok = np.ones(n, bool); ok[10:14] = False
    f7 = rng.normal(0, 1, (n, 18, 7))
    f7[200:220, :, 5] += 5.0                          # a planted line-length rise on every channel
    s = mf_series(f7, ok)
    c1 = all(np.isnan(s[k][10:14]).all() and np.isfinite(s[k][ok]).all() for k in MF)
    c2 = s["ll"][200:220].min() > 2.5 and abs(np.median(s["ll"][ok])) < 0.3
    lin = np.log(np.exp(f7[..., :5]).sum(-1))
    c3 = np.allclose(robust_z_cols(lin, ok)[ok].mean(1), s["pow"][ok])
    sm = np.zeros(30); sm[[3, 4, 9, 20, 21, 22]] = 1.0
    c4 = above_runs(sm, 0.5, 0, 30) == 3 and above_runs(sm, 0.5, 4, 21) == 3 and above_runs(sm, 0.5, 5, 9) == 0
    ok_all = bool(c1 and c2 and c3 and c4)
    R1.gate(dict(gate="G-self", status="PASS" if ok_all else "FAIL", checks=dict(nan_mask=bool(c1), planted_ll=bool(c2),
                 log_total_power=bool(c3), runs=bool(c4)), summary="model-free series and run count on synthetic arrays"))


def _job_meta(t, **kw):
    import resource
    return dict(kw, shas=code_shas(), s=round(time.time() - t, 1),
                peak_rss_mb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1))


def extract_job(a):
    """one case: run_budget (record) and the event / seizure / series extraction for 4 seeds x 2 arms."""
    case, src, set_name = a
    t = time.time()
    try:
        ctx, _ = R1.ctx_from_store(case, src, "r10")
        z, _ = R1.load_case(case, src)
        ok, fidx = ctx["ok"], ctx["fidx"]
        files = np.unique(fidx)
        fwin = {f: np.flatnonzero(fidx == f) for f in files}
        mf = mf_series(np.asarray(z["f7"]), ok)
        mf_bad = int(sum((~np.isfinite(mf[k][ok])).sum() for k in MF))
        refs = P3L.refs_of(ctx)
        X, M = {}, {}
        events, eng_bad, seg_need = [], [], {}
        for tag in TAGS:
            x = E22.final_scalar(ctx, tag)
            m = P3L.member_mean_z(ctx, tag)
            X[tag], M[tag] = x, m
            q = P3L.q_of(PS.smoothed(ctx, m, SMOOTH), K_RECORD)
            sm = PS.smoothed(ctx, x, SMOOTH)
            for arm, (fl, cp) in ARMS.items():
                rr, ee = [], []
                P3C.run_budget(ctx, case, tag, x, q, fl, cp, arm, rr, ee)       # the record function
                top = P3C.budget(q, fl, cp)
                det = PS.d1_events(ctx, x, SMOOTH, top)
                thr = np.nanquantile(sm, 1 - top)
                _, pair_c = P3L.localize(ctx, x, det, thr, "cpd")
                _, pair_h = P3L.localize(ctx, x, det, thr, "hybrid")
                mine = []
                for f, ra, rb, h0, h1 in E18.match_errors(refs, det):
                    mw = fwin[f]
                    xf, okf, smf = x[mw], ok[mw], sm[mw]
                    aw, bw = h0 // WIN, h1 // WIN
                    ca, cb, used = E18.cpd_event(xf, okf, aw, bw, MARGIN)
                    ua, ub = E18.run_event(xf, okf, aw, bw, MARGIN, thr)
                    s0, s1 = max(0, aw - MARGIN), min(len(xf), bw + MARGIN)
                    c0, c1 = pair_c[(f, h0, h1)]
                    y0, y1 = pair_h[(f, h0, h1)]
                    if (c0, c1) != (ca * WIN, cb * WIN):
                        eng_bad.append(f"{tag} {arm} file {f} event {h0}: cpd {c0, c1} vs {ca * WIN, cb * WIN}")
                    nref = sum(1 for (a_, b_) in refs.get(f, []) if b_ > h0 and a_ < h1)
                    ev = dict(set=set_name, subject=case, seed=tag, arm=arm, file=int(f), n_file=int(len(xf)),
                              ref_on=int(ra), ref_off=int(rb), ref_dur=int(rb - ra), det_a=int(h0), det_b=int(h1),
                              ev_dur=int(h1 - h0), top=float(top), thr=float(thr), q_raw=float(q), used_cpd=bool(used),
                              cpd_a=int(ca * WIN), cpd_b=int(cb * WIN), win_a=int(s0 * WIN), win_b=int(s1 * WIN),
                              run_a=int(ua * WIN), run_b=int(ub * WIN), hyb_a=int(y0), hyb_b=int(y1),
                              n_runs=above_runs(smf, thr, aw, bw), n_refs=int(nref),
                              det_on=int(h0 - ra), det_off=int(h1 - rb), cpd_on=int(c0 - ra), cpd_off=int(c1 - rb),
                              hyb_on=int(y0 - ra), hyb_off=int(y1 - rb))
                    mine.append(dict(subject=case, seed=tag, budget=arm, det_on=ev["det_on"], det_off=ev["det_off"],
                                     cpd_on=ev["cpd_on"], cpd_off=ev["cpd_off"], hyb_on=ev["hyb_on"],
                                     hyb_off=ev["hyb_off"]))
                    events.append(ev)
                    key = (int(f), int(ra), int(rb))
                    lo, hi = seg_need.get(key, (aw - EXTRA_W, bw + EXTRA_W))
                    seg_need[key] = (min(lo, aw - EXTRA_W), max(hi, bw + EXTRA_W))
                if not pd.DataFrame(mine).equals(pd.DataFrame(ee)):
                    eng_bad.append(f"{tag} {arm}: errors differ from run_budget ({len(mine)} vs {len(ee)} pairs)")
        # ---- segments per annotated seizure
        seizures, parts, seg_bad = [], [], []
        for f in files:
            mw = fwin[f]
            nf = len(mw)
            for (ra, rb) in refs.get(f, []):
                lo = ra // WIN - SEG_PRE_S // WIN
                hi = rb // WIN + SEG_POST_S // WIN
                need = seg_need.get((int(f), int(ra), int(rb)))
                if need:
                    lo, hi = min(lo, need[0]), max(hi, need[1])
                lo, hi = max(0, lo), min(nf, hi)
                sid = f"{case}|{int(f)}|{int(ra)}"
                seizures.append(dict(set=set_name, subject=case, sz=sid, file=int(f), n_file=int(nf), ref_on=int(ra),
                                     ref_off=int(rb), seg_a=int(lo * WIN), seg_b=int(hi * WIN), matched=need is not None))
                w = np.arange(lo, hi)
                g = mw[w]
                d = dict(sz=[sid] * len(w), subject=[case] * len(w), file=[int(f)] * len(w), w=w.astype(int),
                         ok=ok[g].astype(int), ict=ctx["ict"][g].astype(int))
                for tag in TAGS:
                    s_ = tag.split("seed")[1]
                    d[f"x{s_}"] = X[tag][g]
                    d[f"m{s_}"] = M[tag][g]
                for k in MF:
                    d[f"mf_{k}"] = mf[k][g]
                parts.append(pd.DataFrame(d))
        S = pd.DataFrame(seizures)
        for ev in events:                        # G-seg: search window +- 15 more windows inside the stored segment
            s = S[(S.file == ev["file"]) & (S.ref_on == ev["ref_on"])]
            need_a = max(0, ev["win_a"] - MARGIN * WIN)
            need_b = min(ev["n_file"] * WIN, ev["win_b"] + MARGIN * WIN)
            if len(s) != 1 or s.seg_a.iloc[0] > need_a or s.seg_b.iloc[0] < need_b:
                seg_bad.append(f"{ev['seed']} {ev['arm']} file {ev['file']} ref {ev['ref_on']}")
        series = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
        d = R1.SCRATCH / "f5a"
        d.mkdir(parents=True, exist_ok=True)
        series.to_pickle(d / f"{case}.pkl")
        return _job_meta(t, case=case, src=src, job="extract", events=events, seizures=seizures, eng_bad=eng_bad,
                         seg_bad=seg_bad, mf_bad=mf_bad, n_series=int(len(series)),
                         hours=float(len(ok) * WIN / 3600))
    except SystemExit as e:
        return dict(case=case, src=src, job="extract", error=f"STOP: {e}")
    except Exception:                    # noqa: BLE001
        return dict(case=case, src=src, job="extract", error=traceback.format_exc()[-3000:])


def _run(fn, specs, workers, what):
    out = []
    if not specs:
        return out
    if workers <= 1:
        R1._init_worker(R1._env())
        it, pool = map(fn, specs), None
    else:
        pool = R1._pool(min(workers, len(specs)))
        it = pool.imap_unordered(fn, specs)
    try:
        for r in it:
            if r.get("error"):
                raise SystemExit(f"{what} {r['case']}: {r['error']}")
            out.append(r)
            log(f"{what} {r['case']} done ({r['s']} s)")
    finally:
        if pool is not None:
            pool.terminate()
    return out


def _size(case, src):
    p = R1.VIEWS / src / (f"{case}_lf.npz" if src == "ext" else f"{case}.npz")
    return p.stat().st_size


def set_of(case, src):
    if src == "ext":
        return "chb24" if case.startswith("chb") else "siena"
    return "development" if case in DEV else "test"


def extract_pass(cases_src, workers, label):
    t = time.time()
    specs = sorted([(c, s, set_of(c, s)) for c, s in cases_src], key=lambda a: -_size(a[0], a[1]))
    res = _run(extract_job, specs, workers, f"extract[{label}]")
    R1.phase(f"extract_{label}", t)
    eng = {r["case"]: r["eng_bad"][:5] for r in res if r["eng_bad"]}
    R1.gate(dict(gate=f"G-eng[{label}]", status="PASS" if not eng else "FAIL", bad=eng,
                 pairs=int(sum(len(r["events"]) for r in res)),
                 summary=f"extracted boundaries and errors = p3c_freeze.run_budget in {len(res)} cases x {len(TAGS)} seeds "
                         f"x {len(ARMS)} arms ({sum(len(r['events']) for r in res)} pairs)" if not eng else str(eng)))
    seg = {r["case"]: r["seg_bad"][:5] for r in res if r["seg_bad"]}
    R1.gate(dict(gate=f"G-seg[{label}]", status="PASS" if not seg else "FAIL", bad=seg,
                 summary="every search window +- 15 windows lies inside its stored segment" if not seg else str(seg)))
    mfb = {r["case"]: r["mf_bad"] for r in res if r["mf_bad"]}
    R1.gate(dict(gate=f"G-mf[{label}]", status="PASS" if not mfb else "FAIL", bad=mfb,
                 summary="model-free series finite on every valid window" if not mfb else str(mfb)))
    want = code_shas()
    wbad = sorted({r["case"] for r in res if r["shas"] != want})
    R1.gate(dict(gate=f"G-worker-sha[{label}]", status="PASS" if not wbad else "FAIL", bad=wbad, want=want,
                 summary=f"{len(res)} jobs ran r4_f5a {want['r4_f5a']}, r2_r1 {want['r2_r1']}, e18 {want['e18']}"))
    return res


def write_outputs(res):
    o = R1.out_dir()
    pd.DataFrame([e for r in res for e in r["events"]]).to_csv(o / "events.csv", index=False)
    pd.DataFrame([s for r in res for s in r["seizures"]]).to_csv(o / "seizures.csv", index=False)
    parts = [pd.read_pickle(R1.SCRATCH / "f5a" / f"{r['case']}.pkl") for r in sorted(res, key=lambda r: r["case"])]
    S = pd.concat(parts, ignore_index=True)
    S.to_csv(o / "series.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    pd.DataFrame([dict(case=r["case"], job=r["job"], s=r["s"], peak_rss_mb=r["peak_rss_mb"], hours=r["hours"],
                       pairs=len(r["events"]), series_rows=r["n_series"]) for r in res]).to_csv(o / "jobs.csv", index=False)


# ============================================================================ main
def main(notebook="F5A_V5", repo_commit="local", workers=None, smoke_only=False):
    R1.OUT_ROOT = R1.WORK / "r4"
    workers = int(workers or os.environ.get("F5A_WORKERS") or R1.n_workers())
    meta = R1.run_meta(TAG, notebook, repo_commit)
    meta.update(r4_f5a_sha=CODE_SHA, code_shas=code_shas(), arms=ARMS, workers=workers, k=K_RECORD)
    R1._jdump(R1.out_dir() / "run_meta.json", meta)
    self_checks()
    src = build_views(DEV, TEST, EXT)
    gate_data(src)
    # ---- SMOKE: chb01 + chb03 + first external case, measured
    t = time.time()
    s_dev, s_test, s_ext = [DEV[0]], [TEST[0]], EXT[:1]
    STATE["tag"] = f"{TAG}/smoke"
    R1.r10(s_dev, s_test, s_ext, workers=min(workers, 3), with_k=False)
    cs = [(c, "earlier") for c in s_dev + s_test] + [(c, "ext") for c in s_ext]
    res = extract_pass(cs, min(workers, 3), "smoke")
    write_outputs(res)
    smoke_s = time.time() - t
    h_smoke = sum(r["hours"] for r in res)
    h_all = sum(float(np.load(R1.VIEWS / ("ext" if c in EXT else "earlier") / (f"{c}_lf.npz" if c in EXT else f"{c}.npz"),
                              allow_pickle=True)["is_ictal"].shape[0]) * WIN / 3600 for c in DEV + TEST + EXT)
    proj = dict(smoke_s=round(smoke_s, 1), smoke_eeg_h=round(h_smoke, 2), all_eeg_h=round(h_all, 1), workers=workers,
                note="computed: smoke seconds x (all hours / smoke hours) / workers",
                projected_h=round(smoke_s * (h_all / max(h_smoke, 1e-9)) / max(workers, 1) / 3600, 2))
    STATE["tag"] = TAG
    R1._jdump(R1.out_dir() / "projection.json", proj)
    R1.gate(dict(gate="SMOKE", status="PASS" if proj["projected_h"] <= REFUSE_H else "FAIL", **proj,
                 summary=f"smoke {smoke_s:.0f} s on {h_smoke:.1f} h of EEG; full run projected {proj['projected_h']} h"))
    if smoke_only:
        return
    # ---- FULL
    t = time.time()
    R1.r10(DEV, TEST, EXT, workers=workers, with_k=True)
    R1.phase("r10_full", t)
    cs = [(c, "earlier") for c in DEV + TEST] + [(c, "ext") for c in EXT]
    res = extract_pass(cs, workers, "full")
    write_outputs(res)
    R1.finish_meta(dict(pairs=int(sum(len(r["events"]) for r in res)),
                        seizures=int(sum(len(r["seizures"]) for r in res))))
    (R1.out_dir() / "SUMMARY.md").write_text(
        f"# F5A_V5 run ({notebook}, commit {repo_commit})\n\nEvery gate PASS (gates.json). Outputs: events.csv, "
        "seizures.csv, series.csv.gz, jobs.csv, r10/. No reading here: src/r4_f5a_aggregate.py makes the tables "
        "(committed before this run).\n", encoding="utf-8")
    log("F5A_V5 done")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int)
    ap.add_argument("--smoke-only", action="store_true")
    a = ap.parse_args()
    main(workers=a.workers, smoke_only=a.smoke_only)
