#!/usr/bin/env python
"""
eur_abl.py -- Euréka ablation suite on the V5 model (Track F, chat D31-F; design results/eureka_d31f/STEP1_DESIGN.md,
approved by the author 19/11/2026 20:35). Inference only: the four committed V5 checkpoints
data/models_v2/gae_v2_clean_seed{42,1,2,3}.pt on the defense-time data copy (v9-x3-fold1/3) and the external features
(thesis-r2-external-features). Written before any output.

Every stage of V5 is the record code, imported read only through r2_r1 (whose import guard requires every record
module to come from this repository). A variant swaps ONE function; everything else is the record code:
  latent        p2_dump_seeds23.run_model (8a: the same construction with an empty propagation graph, self loops only)
  distance      per-channel LedoitWolf Mahalanobis (x1_external.model_outputs); 1a diagonal, 1b Euclidean; 4a reference
                fitted on the clean windows of the 12 training patients (leave the scored patient out); 4b / 4c per-file
                baselines of 10 / 30 min (e16_recording_baseline.arm_distances arms a / c)
  members       e17b_latent_family.member (robust z per channel, order statistic, minus a +-15 min running median per
                file); 2a no drift correction, 2b level + spread (running median and running MAD, same window); 3a / 3m /
                3c one member; 3g / 3r the gamma-AEC / reconstruction readout added as a fifth member (as E17)
  ensemble      percentile ranks, equal mean (e22_test_oneshot.final_scalar); budget signal = mean robust z of the same
                parts (p3_levers.member_mean_z)
  detection     p3c_freeze.run_budget (smoothing as a parameter for 5a: 1 / 3 / 9 windows), localizer cpd and hybrid
  k             p3_levers.calibrate on the 15 development patients, seed 42, per variant (V5's own rule)
Arms per variant: own (clip(q, 0.005, 0.02), the variant's own k) and fixed (0.005 for every patient). 6a = V0 fixed;
7a = V0 detector stage; 7b = V0 hybrid stage. A detection curve over a global budget (detector stage) gives the
sensitivity at matched FP/day (reading ii of the design).

Gates (STOP unless PASS):
  G-data   every earlier .npz sha256 = docs/PROVENANCE_V2.md; every external file = R1_SMOKE's pinned sha256
  SMOKE    chb01 + chb03 (+ the first external case) end to end before the full run: R1.0 rows, G-D0, G-x0, G-eng, every
           variant computed once; measured seconds -> projection (STOP if > 10.5 h)
  R1.0-dev / R1.0-test / GE / G-k    r2_r1.r10 unchanged (V0 = the V5 rows; external within |dtp| <= 1, |dfp| <= 2)
  G-D0     the V0 distances recomputed in the variant pass = the stored r2_r1 distances, exactly
  G-x0     V0's scalar and budget signal = e22_test_oneshot.final_scalar and p3_levers.member_mean_z, exactly
  G-eng    run_budget with the smoothing parameter = p3c_freeze.run_budget for V0 (own = L2f, fixed = frozen), exactly
  G-enc    the 8a encoder with the window's own graph = p2_dump_seeds23.run_model (first case of each set), exactly
  G-kv0    V0's k from the variant pass = results/p3_levers/calibration.json (relative 1e-6)
  G-worker every pool job ran the same eur_abl.py / r2_r1.py / record modules as the parent (sha256)
  G-self   unit checks on synthetic arrays at start (member construction = e17b, distances by definition)
Outputs: WORK/eureka/abl/ (run_meta.json, gates.json, data_sha256.csv, r10/, per_subject.csv, errors.csv, curve.csv,
k.csv, jobs.csv, projection.json, SUMMARY.md). The reading is done by src/eur_abl_aggregate.py (committed first).
  python src/eur_abl.py [--workers N]
Test mode (synthetic world, build container only): R2_TEST=1 (see src/eur_abl_synthetic_test.py).
"""
import hashlib
import json
import os
import platform
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
import e16_recording_baseline as E16     # noqa: E402
import e17b_latent_family as F17         # noqa: E402

PS, P3L, P3C, E22, X1, PD, TGV2, R0 = R1.PS, R1.P3L, R1.P3C, R1.E22, R1.X1, R1.PD, R1.TGV2, R1.R0
_OUT = [m.__name__ for m in (E16, F17) if (REPO / "src") not in Path(m.__file__).resolve().parents]
if _OUT:
    raise SystemExit(f"STOP: record modules imported from outside {REPO / 'src'}: {_OUT}")
log = R1.log

TAGS, DEV, TEST, TRAIN = R1.TAGS, list(R1.DEV), list(R1.TEST), list(R1.TRAIN)
EXT = list(R1.EXT)
K_RECORD = R1.K_RECORD
SCR = R1.SCRATCH / "eur"
MEMBERS = tuple(F17.MEMBERS.values())                   # (6, 9, 12, "mean") -- V5
ARMS = {"own": (0.005, P3C.CAP), "fixed": (0.005, 0.005)}
CURVE_TOPS = (0.003, 0.004, 0.005, 0.0065, 0.0075, 0.01)
REFUSE_H = 10.5
TEST_MODE = bool(os.environ.get("R2_TEST"))
WIDTH = 451                                               # +-15 min running window (e17b_latent_family.member)


def _v(dist="maha", enc="own", members=MEMBERS, drift="level", extra=(), smooth=5, text=""):
    return dict(dist=dist, enc=enc, members=tuple(members), drift=drift, extra=tuple(extra), smooth=smooth, text=text)


VARIANTS = {
    "V0": _v(text="V5 system"),
    "1a": _v(dist="diag", text="diagonal covariance instead of Mahalanobis"),
    "1b": _v(dist="eucl", text="Euclidean distance instead of Mahalanobis"),
    "4a": _v(dist="ref", text="reference = clean windows of the training patients (leave-self-out)"),
    "4b": _v(dist="base10", text="reference = first 10 min of each file"),
    "4c": _v(dist="base30", text="reference = first 30 min of each file"),
    "2a": _v(drift="none", text="no drift correction"),
    "2b": _v(drift="levspread", text="drift correction of level and spread"),
    "3a": _v(members=(9,), text="one member: 9th largest"),
    "3m": _v(members=("mean",), text="one member: channel mean"),
    "3c": _v(members=(1,), text="one member: largest"),
    "3g": _v(extra=("gamma",), text="+ gamma-AEC readout (fifth member)"),
    "3r": _v(extra=("recon",), text="+ reconstruction-error readout (fifth member)"),
    "5a1": _v(smooth=1, text="smoothing 1 window"),
    "5a3": _v(smooth=3, text="smoothing 3 windows"),
    "5a9": _v(smooth=9, text="smoothing 9 windows"),
    "8a": _v(enc="self", text="no edges at inference (self loops only)"),
}
STATE = R1.STATE


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


CODE_FILES = {n: Path(m.__file__) for n, m in (("eur_abl", sys.modules[__name__]), ("r2_r1", R1), ("e16", E16),
                                                ("e17b", F17), ("p3c_freeze", P3C), ("p3_levers", P3L),
                                                ("p2_scalars", PS), ("e22", E22), ("x1_external", X1),
                                                ("p2_dump_seeds23", PD))}
CODE_SHA = sha16(__file__)


def code_shas():
    return {n: sha16(p) for n, p in CODE_FILES.items()}


# ============================================================================ inputs
def build_views(dev, test, ext):
    """links SCRATCH/r1_views/{earlier,ext} as r2_r1.build_views does (earlier = v9-x3-fold* record .npz; ext =
    thesis-r2-external-features), without the new CHB-MIT dataset, which this suite does not use. Symlink, else hard
    link, else copy (Windows)."""
    import shutil
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
def model_inputs(z):
    """the inputs of x1_external.model_outputs (verbatim construction)."""
    idx = np.flatnonzero(~z["is_signal_loss"].astype(bool))
    adj = z["adj"][idx].astype(np.float32); adj[~np.isfinite(adj).all(axis=(1, 2))] = 0.0
    bp5 = z["bp5"][idx].astype(np.float32); bp5[~np.isfinite(bp5)] = 0.0
    f7 = z["f7"][idx].astype(np.float64)
    xn = (bp5 - bp5.min(axis=1, keepdims=True)) / (bp5.max(axis=1, keepdims=True) - bp5.min(axis=1, keepdims=True) + 1e-8)
    return idx, adj, xn, f7


def encode(tag, adj, xn, f7, prop="own"):
    """p2_dump_seeds23.run_model's construction; prop 'self' = empty propagation graph (GCN self loops only). The node
    input keeps the window's own connectivity row in both cases (as F-A1.4's I-self)."""
    import torch
    from torch_geometric.data import Data, Batch
    from torch_geometric.utils import dense_to_sparse
    import gae_joint as G
    E8 = R1.E8
    ck = PD.CKPT / f"gae_v2_{tag}.pt"
    meta = json.loads(ck.with_suffix(".json").read_text())
    mu, sd, clip = np.array(meta["add_mean"]), np.array(meta["add_std"]), meta["clip"]
    fa = ((np.clip((f7 - mu) / sd, -clip, clip) + clip) / (2 * clip)).astype(np.float32)
    model = G.GAEModel(in_dim=meta["in_dim"], bands=meta["out_x"])
    model.load_state_dict(torch.load(str(ck), map_location="cpu"), strict=True)
    model.eval()
    n = len(adj)
    Z = np.empty((n, G.N_CH, G.LATENT_DIM), np.float32)
    with torch.no_grad():
        for s in range(0, n, E8.CHUNK):
            e = min(s + E8.CHUNK, n)
            dl = []
            for i in range(s, e):
                A = torch.tensor(adj[i]); An = A / (A.amax() + 1e-8)
                xt = torch.cat([torch.tensor(xn[i].astype(np.float32)), torch.tensor(fa[i])], dim=1)
                ei, ew = dense_to_sparse(A if prop == "own" else torch.zeros_like(A))
                dl.append(Data(x=torch.cat([An, xt], dim=1), edge_index=ei, edge_attr=ew))
            b = Batch.from_data_list(dl)
            Z[s:e] = model.encoder(b.x, b.edge_index, b.edge_attr).view(b.num_graphs, G.N_CH, G.LATENT_DIM).numpy()
    return Z


def d_maha(Z):
    from sklearn.covariance import LedoitWolf
    return np.column_stack([LedoitWolf().fit(Z[:, c, :].astype(np.float64)).mahalanobis(Z[:, c, :].astype(np.float64))
                            for c in range(Z.shape[1])]).astype(np.float64)


def d_diag(Z):
    X = Z.astype(np.float64)
    mu, var = X.mean(axis=0), X.var(axis=0) + 1e-12
    return (((X - mu) ** 2) / var).sum(axis=2)


def d_eucl(Z):
    X = Z.astype(np.float64)
    return ((X - X.mean(axis=0)) ** 2).sum(axis=2)


def d_ref(Z, loc, prec):
    """squared Mahalanobis distance of each channel's latent to a fixed reference (loc: C x d, prec: C x d x d)."""
    X = Z.astype(np.float64) - loc[None]
    return np.einsum("ncd,cde,nce->nc", X, prec, X)


def conv(D, ext):
    """record convention: CHB-MIT distances stored as float32 and read back as float64; external kept float64."""
    return np.asarray(D, np.float64) if ext else np.asarray(np.asarray(D, np.float32), np.float64)


def _roll_med(v, wf):
    out = np.empty_like(v)
    for f in np.unique(wf):
        w = np.flatnonzero(wf == f)
        out[w] = pd.Series(v[w]).rolling(WIDTH, min_periods=1, center=True).median().values
    return out


def member_series(D, wf, ks, drift):
    """e17b_latent_family.member for drift 'level' (identical construction); 'none' and 'levspread' change only the
    correction step."""
    okk = np.ones(len(D), bool)
    Zc = np.column_stack([E16.rz(D[:, j], okk) for j in range(D.shape[1])])
    out = []
    for k in ks:
        v = Zc.mean(axis=1) if k == "mean" else -np.sort(-Zc, axis=1)[:, k - 1]
        if drift == "level":
            o = v.copy()
            for f in np.unique(wf):                      # identical loop to e17b_latent_family.member
                w = np.flatnonzero(wf == f)
                o[w] = v[w] - pd.Series(v[w]).rolling(WIDTH, min_periods=1, center=True).median().values
            v = o
        elif drift == "levspread":
            med = _roll_med(v, wf)
            v = (v - med) / (_roll_med(np.abs(v - med), wf) + 1e-9)
        elif drift != "none":
            raise ValueError(drift)
        out.append(v)
    return out


def scalar_and_m(lite, parts_valid, extra_full=()):
    full = [PS._full(lite, p) for p in parts_valid] + list(extra_full)
    x = np.mean([PS.pct(v, lite["ok"]) for v in full], axis=0)
    m = np.mean([E16.rz(v, lite["ok"]) for v in full], axis=0)
    return x, m


def run_budget_s(ctx, s, tag, x, q, floor, cap, name, rows, errs, smooth):
    """p3c_freeze.run_budget with the smoothing as a parameter (identical otherwise; gate G-eng)."""
    E18 = P3C.E18
    top = P3C.budget(q, floor, cap)
    det = PS.d1_events(ctx, x, smooth, top)
    thr = np.nanquantile(PS.smoothed(ctx, x, smooth), 1 - top)
    stages, pairs = {"detector": det}, {}
    for mode in ("cpd", "hybrid"):
        stages[mode], pairs[mode] = P3L.localize(ctx, x, det, thr, mode)
    rec_s = ctx["n"] * PS.WIN
    for st, ev in stages.items():
        tp, fp, nr, h = PS.score(ctx, ev)
        k, ns = PS.caught(PS.short_refs(ctx), ev)
        rows.append(dict(subject=s, seed=tag, budget=name, stage=st, top=top, tp=tp, fp=fp, n_ref=nr, nonict_h=h,
                         short_tp=k, short_n=ns, review_s=float(sum(b - a for v in ev.values() for a, b in v)), rec_s=rec_s))
    for f, ra, rb, h0, h1 in E18.match_errors(P3L.refs_of(ctx), det):
        c0, c1 = pairs["cpd"][(f, h0, h1)]; y0, y1 = pairs["hybrid"][(f, h0, h1)]
        errs.append(dict(subject=s, seed=tag, budget=name, det_on=h0 - ra, det_off=h1 - rb, cpd_on=c0 - ra,
                         cpd_off=c1 - rb, hyb_on=y0 - ra, hyb_off=y1 - rb))


def self_checks():
    """G-self: member_series('level') = e17b_latent_family.member exactly; distances by definition."""
    rng = np.random.default_rng(0)
    D = rng.gamma(2.0, 1.0, (900, 18)); wf = np.repeat([0, 1, 2], 300)
    bad = []
    for k in MEMBERS:
        if not np.array_equal(member_series(D, wf, (k,), "level")[0], F17.member(D, wf, k)):
            bad.append(f"member {k}")
    Z = rng.normal(0, 1, (500, 18, 16)).astype(np.float32)
    X = Z.astype(np.float64)
    if not np.allclose(d_eucl(Z)[:, 3], ((X[:, 3] - X[:, 3].mean(0)) ** 2).sum(1)):
        bad.append("eucl")
    if not np.allclose(d_diag(Z)[:, 5], (((X[:, 5] - X[:, 5].mean(0)) ** 2) / X[:, 5].var(0)).sum(1), rtol=1e-6):
        bad.append("diag")
    from sklearn.covariance import LedoitWolf
    lw = LedoitWolf().fit(X[:, 2])
    loc = np.zeros((18, 16)); prec = np.tile(np.eye(16), (18, 1, 1)); loc[2], prec[2] = lw.location_, lw.precision_
    if not np.allclose(d_ref(Z, loc, prec)[:, 2], lw.mahalanobis(X[:, 2]), rtol=1e-8):
        bad.append("ref vs sklearn mahalanobis")
    lv = member_series(D, wf, (9,), "levspread")[0]
    if not np.isfinite(lv).all():
        bad.append("levspread finite")
    R1.gate(dict(gate="G-self", status="PASS" if not bad else "FAIL", bad=bad,
                 summary="member construction = e17b; distances by definition" if not bad else str(bad)))


# ============================================================================ pool jobs
def _job_meta(t, **kw):
    import resource
    return dict(kw, shas=code_shas(), s=round(time.time() - t, 1),
                peak_rss_mb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1))


def p1_job(a):
    """training patient: latents of the 4 seeds; every 10th clean window (thesis training mask) kept for the 4a
    reference."""
    case, = a
    t = time.time()
    try:
        PD.CKPT = REPO / "data" / "models_v2"
        z, _ = R1.load_case(case, "earlier")
        idx, adj, xn, f7 = model_inputs(z)
        clean = np.asarray(TGV2.mask(z, "clean"), bool)[idx]
        sel = np.flatnonzero(clean)[::10]
        d = SCR / "p1"
        d.mkdir(parents=True, exist_ok=True)
        out = {}
        for tag in TAGS:
            _, Zt = PD.run_model(tag, adj, xn, f7)
            out[tag] = Zt[sel].astype(np.float32)
        np.savez(d / f".{case}.npz", **out)
        (d / f".{case}.npz").replace(d / f"{case}.npz")
        return _job_meta(t, case=case, job="p1", n_sub=int(len(sel)))
    except Exception:                    # noqa: BLE001
        return dict(case=case, job="p1", error=traceback.format_exc()[-3000:])


def reference_fits(train_cases):
    """per seed, per channel: LedoitWolf on the pooled subsample of the training patients, once with all of them
    (for every other case) and once leaving each training patient out (for that patient)."""
    from sklearn.covariance import LedoitWolf
    t = time.time()
    sub = {c: np.load(SCR / "p1" / f"{c}.npz") for c in train_cases}
    fits, counts = {}, {}
    for tag in TAGS:
        for excl in [None] + list(train_cases):
            use = [c for c in train_cases if c != excl]
            if not use:
                continue
            X = np.concatenate([sub[c][tag] for c in use]).astype(np.float64)
            loc = np.empty((X.shape[1], X.shape[2])); prec = np.empty((X.shape[1], X.shape[2], X.shape[2]))
            for c in range(X.shape[1]):
                lw = LedoitWolf().fit(X[:, c, :])
                loc[c], prec[c] = lw.location_, lw.precision_
            key = f"{tag}|{excl or 'all'}"
            fits[key + "|loc"], fits[key + "|prec"] = loc, prec
            counts[key] = dict(patients=len(use), windows=int(len(X)), excluded=excl)
    np.savez(SCR / "ref_fits.npz", **fits)
    R1.phase("reference_fits", t)
    return counts


def prep_job(a):
    """one case: every variant's ensemble scalar x and budget signal m, 4 seeds (stored in SCR/xm/<case>.npz).
    Returns the seed-42 smoothed m of each variant (development cases, for k) and the G-D0 / G-enc checks."""
    case, src, want_smm, check_enc, variants = a
    t = time.time()
    try:
        PD.CKPT = REPO / "data" / "models_v2"
        ext = src == "ext"
        z, _ = R1.load_case(case, src)
        idx, adj, xn, f7 = model_inputs(z)
        ok = ~z["is_signal_loss"].astype(bool)
        fidx = z["file_idx"].astype(int)
        lite = dict(n=int(len(ok)), idx=idx, ok=ok, fidx=fidx)
        wf = fidx[idx]
        stored = np.load(R1.DSTORE / "r10" / f"{case}.npz")
        if not np.array_equal(stored["idx"], idx):
            raise SystemExit(f"{case}: window index differs from the stored r10 distances")
        fits = np.load(SCR / "ref_fits.npz") if any(VARIANTS[v]["dist"] == "ref" for v in variants) else None
        fkey = case if case in TRAIN else "all"
        gam = (PS._full(lite, np.asarray(z["zgamma_raw"], np.float64)[idx])
               if (not ext and "zgamma_raw" in getattr(z, "files", z)) else None)
        store, smm, d0_bad, enc_bad, na = {}, {}, [], None, []
        for tag in TAGS:
            rec, Z = PD.run_model(tag, adj, xn, f7)
            D0raw = d_maha(Z)
            Ds = {"maha": conv(D0raw, ext)}
            if not np.array_equal(Ds["maha"], np.asarray(stored[f"{tag}_d"], np.float64)):
                d0_bad.append(tag)
            need = {VARIANTS[v]["dist"] for v in variants} | {"enc_" + VARIANTS[v]["enc"] for v in variants}
            if "diag" in need:
                Ds["diag"] = conv(d_diag(Z), ext)
            if "eucl" in need:
                Ds["eucl"] = conv(d_eucl(Z), ext)
            if "ref" in need and f"{tag}|{fkey}|loc" in fits.files:
                Ds["ref"] = conv(d_ref(Z, fits[f"{tag}|{fkey}|loc"], fits[f"{tag}|{fkey}|prec"]), ext)
            if "base10" in need:
                Ds["base10"] = conv(E16.arm_distances("a", D0raw, Z, wf)[0], ext)
            if "base30" in need:
                Ds["base30"] = conv(E16.arm_distances("c", D0raw, Z, wf)[0], ext)
            if "enc_self" in need:
                Ds["self"] = conv(d_maha(encode(tag, adj, xn, f7, "self")), ext)
            if check_enc and tag == TAGS[0]:
                enc_bad = float(np.abs(encode(tag, adj, xn, f7, "own") - Z).max())
            recf = PS._full(lite, rec.astype(np.float64))
            for vid in variants:
                v = VARIANTS[vid]
                key = "self" if v["enc"] == "self" else v["dist"]
                if key not in Ds or ("gamma" in v["extra"] and gam is None):
                    na.append(vid)
                    continue
                extra = [gam if e == "gamma" else recf for e in v["extra"]]
                x, m = scalar_and_m(lite, member_series(Ds[key], wf, v["members"], v["drift"]), extra)
                store[f"{vid}|{tag}|x"], store[f"{vid}|{tag}|m"] = x, m
                if want_smm and tag == "clean_seed42":
                    smm[vid] = PS.smoothed(lite, m, v["smooth"])
        d = SCR / "xm"
        d.mkdir(parents=True, exist_ok=True)
        np.savez(d / f".{case}.npz", **store)
        (d / f".{case}.npz").replace(d / f"{case}.npz")
        return _job_meta(t, case=case, src=src, job="prep", smm=smm, d0_bad=d0_bad, enc_maxabs=enc_bad,
                         na=sorted(set(na)), hours=float(len(ok) * PS.WIN / 3600))
    except SystemExit as e:
        return dict(case=case, src=src, job="prep", error=f"STOP: {e}")
    except Exception:                    # noqa: BLE001
        return dict(case=case, src=src, job="prep", error=traceback.format_exc()[-3000:])


def score_job(a):
    """one case: run_budget_s for every variant x seed x arm (+ the detector curve); for V0 also p3c_freeze.run_budget
    and the scalar / budget-signal identity with the record functions (G-eng, G-x0)."""
    case, src, ks, set_name, variants = a
    t = time.time()
    try:
        ctx, _ = R1.ctx_from_store(case, src, "r10")
        xm = np.load(SCR / "xm" / f"{case}.npz")
        rows, errs, curve, x0_bad, eng_bad = [], [], [], [], []
        for tag in TAGS:
            for vid in variants:
                if f"{vid}|{tag}|x" not in xm.files:
                    continue
                v = VARIANTS[vid]
                x, m = xm[f"{vid}|{tag}|x"], xm[f"{vid}|{tag}|m"]
                q = P3L.q_of(PS.smoothed(ctx, m, v["smooth"]), ks[vid])
                r_, e_ = [], []
                for arm, (fl, cp) in ARMS.items():
                    run_budget_s(ctx, case, tag, x, q, fl, cp, arm, r_, e_, v["smooth"])
                rows += [dict(r, variant=vid, set=set_name, q_raw=q, k=ks[vid]) for r in r_]
                errs += [dict(e, variant=vid, set=set_name) for e in e_]
                sm = PS.smoothed(ctx, x, v["smooth"])
                for top in CURVE_TOPS:
                    det = PS.d1_events(ctx, x, v["smooth"], top)
                    tp, fp, nr, h = PS.score(ctx, det)
                    curve.append(dict(subject=case, seed=tag, variant=vid, set=set_name, top=top, tp=tp, fp=fp,
                                      n_ref=nr, nonict_h=h))
                del sm
                if vid == "V0":
                    if not (np.array_equal(x, E22.final_scalar(ctx, tag)) and
                            np.array_equal(m, P3L.member_mean_z(ctx, tag))):
                        x0_bad.append(tag)
                    rr, ee = [], []
                    for arm, rec_arm in (("own", "L2f"), ("fixed", "frozen")):
                        fl, cp = R1.ARMS[rec_arm]
                        P3C.run_budget(ctx, case, tag, x, q, fl, cp, arm, rr, ee)
                    if not (pd.DataFrame(rr).equals(pd.DataFrame(r_)) and pd.DataFrame(ee).equals(pd.DataFrame(e_))):
                        eng_bad.append(tag)
        return _job_meta(t, case=case, src=src, job="score", rows=rows, errs=errs, curve=curve, x0_bad=x0_bad,
                         eng_bad=eng_bad)
    except SystemExit as e:
        return dict(case=case, src=src, job="score", error=f"STOP: {e}")
    except Exception:                    # noqa: BLE001
        return dict(case=case, src=src, job="score", error=traceback.format_exc()[-3000:])


def _run(fn, specs, workers, what):
    out = []
    if not specs:
        return out
    if workers <= 1:
        R1._init_worker(R1._env())
        it = map(fn, specs)
        pool = None
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
    return "external" if src == "ext" else ("development" if case in DEV else "test")


# ============================================================================ phases
def variant_pass(cases_src, workers, ks=None, check_enc=(), label="full"):
    """prep (x, m per variant), k per variant, scoring. ks given (smoke) -> no calibration."""
    variants = list(VARIANTS)
    t = time.time()
    specs = sorted([(c, s, c in DEV, c in check_enc, variants) for c, s in cases_src], key=lambda a: -_size(a[0], a[1]))
    prep = _run(prep_job, specs, workers, f"prep[{label}]")
    R1.phase(f"prep_{label}", t)
    d0_bad = {r["case"]: r["d0_bad"] for r in prep if r["d0_bad"]}
    R1.gate(dict(gate=f"G-D0[{label}]", status="PASS" if not d0_bad else "FAIL", bad=d0_bad,
                 summary=f"V0 distances = stored r10 distances in {len(prep)} cases x {len(TAGS)} seeds" if not d0_bad
                 else str(d0_bad)))
    enc = {r["case"]: r["enc_maxabs"] for r in prep if r["enc_maxabs"] is not None}
    if check_enc:
        R1.gate(dict(gate=f"G-enc[{label}]", status="PASS" if enc and max(enc.values()) == 0.0 else "FAIL", max_abs=enc,
                     summary=f"8a encoder with the window graph = run_model: max |dZ| {enc}"))
    if ks is None:
        ks = {}
        for vid in variants:
            sm = [r["smm"][vid] for r in prep if r["case"] in DEV and vid in r["smm"]]
            ks[vid] = float(P3L.calibrate(sm)) if len(sm) == len(DEV) else float("nan")
        rel = abs(ks["V0"] - K_RECORD) / abs(K_RECORD)
        R1.gate(dict(gate="G-kv0", status="PASS" if rel <= R1.TOL["k_rel"] else "FAIL", k=ks["V0"], k_record=K_RECORD,
                     rel=rel, summary=f"V0 k {ks['V0']:.9f} vs record {K_RECORD:.9f} (relative {rel:.1e})"))
    pd.DataFrame([dict(variant=v, k=k, text=VARIANTS[v]["text"]) for v, k in ks.items()]).to_csv(
        R1.out_dir() / "k.csv", index=False)
    t = time.time()
    specs = sorted([(c, s, ks, set_of(c, s), variants) for c, s in cases_src], key=lambda a: -_size(a[0], a[1]))
    sc = _run(score_job, specs, workers, f"score[{label}]")
    R1.phase(f"score_{label}", t)
    x0 = {r["case"]: r["x0_bad"] for r in sc if r["x0_bad"]}
    eng = {r["case"]: r["eng_bad"] for r in sc if r["eng_bad"]}
    R1.gate(dict(gate=f"G-x0[{label}]", status="PASS" if not x0 else "FAIL", bad=x0,
                 summary="V0 scalar and budget signal = the record functions" if not x0 else str(x0)))
    R1.gate(dict(gate=f"G-eng[{label}]", status="PASS" if not eng else "FAIL", bad=eng,
                 summary="run_budget_s = p3c_freeze.run_budget for V0 (own = L2f, fixed = frozen)" if not eng else str(eng)))
    want = code_shas()
    wbad = sorted({r["case"] for r in prep + sc if r["shas"] != want})
    R1.gate(dict(gate=f"G-worker[{label}]", status="PASS" if not wbad else "FAIL", bad=wbad, want=want,
                 summary=f"{len(prep) + len(sc)} jobs ran eur_abl {want['eur_abl']}, r2_r1 {want['r2_r1']}"))
    na = {r["case"]: r["na"] for r in prep if r["na"]}
    jobs = pd.DataFrame([dict(case=r["case"], job=r["job"], s=r["s"], peak_rss_mb=r["peak_rss_mb"],
                              hours=r.get("hours")) for r in prep + sc])
    return prep, sc, ks, na, jobs


def write_outputs(sc, label):
    o = R1.out_dir()
    pd.DataFrame([r for x in sc for r in x["rows"]]).to_csv(o / f"per_subject{label}.csv", index=False)
    pd.DataFrame([r for x in sc for r in x["errs"]]).to_csv(o / f"errors{label}.csv", index=False)
    pd.DataFrame([r for x in sc for r in x["curve"]]).to_csv(o / f"curve{label}.csv", index=False)


def main(notebook="EUR_ABL", repo_commit="local", workers=None, smoke_only=False):
    R1.OUT_ROOT = R1.WORK / "eureka"
    workers = int(workers or os.environ.get("EUR_WORKERS") or R1.n_workers())
    meta = R1.run_meta("abl", notebook, repo_commit)
    meta.update(eur_abl_sha=CODE_SHA, code_shas=code_shas(), variants=VARIANTS, workers=workers)
    R1._jdump(R1.out_dir() / "run_meta.json", meta)
    self_checks()
    src = build_views(DEV, TEST, EXT)
    gate_data(src)
    # ---- SMOKE (the small check before the full run): chb01 + chb03 (+ first external case), measured
    t = time.time()
    s_dev, s_test, s_ext = [DEV[0]], [TEST[0]], EXT[:1]
    STATE["tag"] = "abl/smoke"
    R1.r10(s_dev, s_test, s_ext, workers=min(workers, 3), with_k=False)
    p1 = _run(p1_job, [(c,) for c in s_dev], 1, "p1[smoke]")
    reference_fits(s_dev)
    cs = [(c, "earlier") for c in s_dev + s_test] + [(c, "ext") for c in s_ext]
    prep, sc, _, na, jobs = variant_pass(cs, min(workers, 3), ks={v: K_RECORD for v in VARIANTS},
                                         check_enc=set(s_dev + s_test + s_ext), label="smoke")
    write_outputs(sc, "")
    jobs.to_csv(R1.out_dir() / "jobs.csv", index=False)
    smoke_s = time.time() - t
    h_smoke = sum(r["hours"] for r in prep)
    h_all = sum(float(np.load(R1.VIEWS / ("ext" if c in EXT else "earlier") / (f"{c}_lf.npz" if c in EXT else f"{c}.npz"),
                              allow_pickle=True)["is_ictal"].shape[0]) * PS.WIN / 3600 for c in DEV + TEST + EXT)
    proj = dict(smoke_s=round(smoke_s, 1), smoke_eeg_h=round(h_smoke, 2), all_eeg_h=round(h_all, 1), workers=workers,
                note="computed: smoke seconds x (all hours / smoke hours) / workers x 1.3 (training-patient pass 1)",
                projected_h=round(smoke_s * (h_all / max(h_smoke, 1e-9)) / max(workers, 1) * 1.3 / 3600, 2),
                not_available=na)
    STATE["tag"] = "abl"
    R1._jdump(R1.out_dir() / "projection.json", proj)
    R1.gate(dict(gate="SMOKE", status="PASS" if proj["projected_h"] <= REFUSE_H else "FAIL", **proj,
                 summary=f"smoke {smoke_s:.0f} s on {h_smoke:.1f} h of EEG; full run projected {proj['projected_h']} h"))
    if smoke_only:
        return
    # ---- FULL
    t = time.time()
    R1.r10(DEV, TEST, EXT, workers=workers, with_k=True)
    R1.phase("r10_full", t)
    t = time.time()
    p1 = _run(p1_job, [(c,) for c in TRAIN], workers, "p1")
    counts = reference_fits(TRAIN)
    R1._jdump(R1.out_dir() / "reference_fits.json", counts)
    R1.phase("p1", t)
    cs = [(c, "earlier") for c in DEV + TEST] + [(c, "ext") for c in EXT]
    prep, sc, ks, na, jobs = variant_pass(cs, workers, check_enc={DEV[0], TEST[0], EXT[0]} if EXT else {DEV[0], TEST[0]})
    write_outputs(sc, "")
    jobs.to_csv(R1.out_dir() / "jobs.csv", index=False)
    R1._jdump(R1.out_dir() / "not_available.json", na)
    R1.finish_meta(dict(ks=ks))
    (R1.out_dir() / "SUMMARY.md").write_text(
        f"# EUR_ABL run ({notebook}, commit {repo_commit})\n\nEvery gate PASS (gates.json). Variants: "
        f"{', '.join(VARIANTS)}. Rows: per_subject.csv; errors.csv; curve.csv; k.csv. Not available: {na}.\n"
        "No reading here: src/eur_abl_aggregate.py makes the tables (committed before this run).\n")
    log("EUR_ABL done")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int)
    ap.add_argument("--smoke-only", action="store_true")
    a = ap.parse_args()
    main(workers=a.workers, smoke_only=a.smoke_only)
