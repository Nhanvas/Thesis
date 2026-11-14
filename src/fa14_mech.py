#!/usr/bin/env python
"""
fa14_mech.py -- F-A1.4 (report version A1, Section 4.3.6): where do the extra false alarms of the GAE come from, against
the same autoencoder without message passing (MLP-AE)? Design approved by the author 14/11 23:08
(docs/FUTURE_RESEARCH_PLAN.md §12 14/11 23:10, chat D28-F). Kaggle CPU. Written and tested on synthetic data before any
F-A1.4 output. No training.

Closed modules are imported READ ONLY and called unchanged: r2_core (locate_earlier), f1_core (manifest, run_fold,
encode_D, committed_gae, build), model_cmp_core (npz registry, node_input, d_from_Z, scalars, PRE / POST), v9_e1_baselines
(evaluate_arm), p2_scalars, p3_levers, e16_recording_baseline (rz), graph_construction (apply_topk_threshold).

Partitions: 0 = the six-model comparison (GAE results/v9_x3/models/fold{f}, MLP-AE results/model_cmp/ckpt/mlp_fold{f}.pt,
fold constants = model_cmp_core.fold_meta); 1-5 = the defense-time F1 record (results/f1_repcv/raw/p{r}/jobs/
{gae,mlp}_fold{f}/). Data = the earlier .npz (v9-x3-fold1 + v9-x3-fold3), the copy every one of these records used.

Arms (per fold; each case is scored by the fold model that holds it out, the fold's training cases only for k):
  gae    the committed GAE fold model through f1_core.encode_D (the record's code path)
  mlp    the committed MLP-AE fold model through f1_core.encode_D
  ifix   the GAE with its propagation graph replaced by one time-stable graph per patient: pairs selected by
         graph_construction.apply_topk_threshold on the selection frequency of every pair over the patient's valid
         windows (same 20 % density, ties kept), weight = the pair's mean weight when selected; node input unchanged
  iself  the GAE with no edges (self-loops only)
Per arm: Ledoit-Wolf per patient and channel (model_cmp_core.d_from_Z) and k per fold on the fold's training cases
(f1_core.run_fold -> model_cmp_core.calibrate) by their recorded rules.

Gates (STOP): G-mod (closed modules from the pinned repository); mode (library versions vs R2_A's run_meta: exact or
tolerance); G-data (each earlier .npz located by r2_core.locate_earlier, sha256 = R0's results/r2/r0_data/chb/gates.json
references); G-gcn (the GCN self weight 1 / (1 + sum_j w_ij) used for the descriptive neighbour share = torch_geometric's
gcn_norm on real windows); G-arm (in every job: this module's encoder with the window's own graph = f1_core.encode_D, bit
for bit, on every held-out case); G-base (after the jobs, per partition: the gae and mlp rows = the record -- partition 0
results/model_cmp/per_subject.csv + seizures.csv, partitions 1-5 results/f1_repcv/raw/p{r}/per_subject.csv + seizures.csv
-- tp, fp, n_ref of every (fold, subject, point, stage), own-point k 1e-6 relative, caught flags; exact in mode exact,
|dtp| <= 1, |dfp| <= 2 in mode tolerance; partition 0 also the totals 1,129 / 827 (own, localized) and 920 / 650
(fixed 0.005, localized)). A partition whose G-base fails keeps only its rows (for diagnosis); its analysis tables are
removed and the notebook STOPs at the end.

Per held-out case (descriptive tables; the reading is src/fa14_aggregate.py, committed before any output):
  rows.csv   scorer rows of every arm (tp, fp, n_ref, nonict_h, top, k)
  seiz.csv   per seizure and arm: caught (record rule), peak smoothed score over onset - 30 s .. offset + 60 s and the
             share of the patient's valid windows at or above it (H3)
  f3a.csv    per arm, point (own / fixed0.005), stage (detector / localized): events, event time, false-alarm events
             (no overlap with any reference widened by PRE / POST), their time -> FA = T (1 - s) / L
  h1.csv     per pair (arm vs mlp), definition, phi, tau: windows, mean R_arm - R_mlp (R = channels with robust z >= tau)
             on focal background windows and on the other background windows, mean difference of the 6th / 9th / 12th
             largest robust z; definitions: input (model-free: per-channel log power of f7, robust z within the patient,
             max >= phi and <= 2 channels >= 2), mlpfocal (§8.3: MLP-AE top z >= phi and R_mlp(2) <= 2; statistic arm -
             mlp) and armfocal (the swap: focal by the arm, statistic mlp - arm)
  h1nb.csv   per pair, phi, tau on input-focal windows, channels other than the focal one: counts of arm-only, mlp-only,
             not-recruited, input-level control (1 <= z_mlp < tau) and all channels, each with how many are neighbours
             of the focal channel in the arm's propagation graph (gae: the window's graph; ifix: the patient's fixed
             graph; iself: none) and in the window's graph
  h1fa.csv   per pair, phi: peaks of arm-only false alarms (own point, localized; no overlap with an mlp detector event)
             and of mlp-only false alarms in input-focal windows, beside the base rate over the valid non-ictal windows
  h2.csv     per pair: slope of z_arm - z_mlp on the edge change of the channel between consecutive valid background
             windows of a file (Jaccard distance of the neighbour sets; |change of weighted degree| / its SD), within
             deciles of the channel's input amplitude, and the isolated <-> connected contrast
  smooth.csv per arm: lag-1 autocorrelation of the member-mean robust z over consecutive valid background windows
  desc.csv   per case: GCN neighbour share (1 - self weight), isolated-node share, mean Jaccard, the fixed graph's share
Outputs: WORK/fa14/p{r}/jobs/f{f}/ (atomic, DONE.json last), merged WORK/fa14/p{r}/*.csv, gates.json, run_meta.json,
SUMMARY.md. Test mode (synthetic data, build container only): environment FA14_TEST (src/fa14_synthetic_test.py).
"""
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

import r2_core as R0                     # noqa: E402  (stage R0, read only: locate_earlier, INPUT)
import f1_core as F                      # noqa: E402  (closed, read only)
import graph_construction as GC          # noqa: E402  (record, read only: apply_topk_threshold)

C = F.C                                  # model_cmp_core (closed, read only)
V9E1, PS, P3L = C.V9E1, C.PS, C.P3L
E16 = sys.modules.get("e16_recording_baseline") or __import__("e16_recording_baseline")
_OUTSIDE = [m.__name__ for m in (R0, F, C, V9E1, PS, P3L, E16, GC)
            if (REPO / "src") not in Path(m.__file__).resolve().parents]
if _OUTSIDE:
    raise SystemExit(f"STOP G-mod: closed modules imported from outside {REPO / 'src'}: {_OUTSIDE}")

WORK = Path(os.environ.get("FA14_WORK", "/kaggle/working"))
SCRATCH = Path(os.environ.get("FA14_SCRATCH", "/tmp/fa14"))
OUT = WORK / "fa14"
VIEW = SCRATCH / "view"
TEST = bool(os.environ.get("FA14_TEST"))
MC = REPO / "results" / "model_cmp"
F1RAW = REPO / "results" / "f1_repcv" / "raw"
R0GATES = REPO / "results" / "r2" / "r0_data" / "chb" / "gates.json"
R2A_META = REPO / "results" / "r2" / "r2_cv" / "a" / "run_meta.json"
FOLDS = (1, 2, 3, 4)
PARTS = (0, 1, 2, 3, 4, 5)
ARMS = ("gae", "mlp", "ifix", "iself")
BASE = dict(gae="gae", mlp="mlp", ifix="gae", iself="gae")
PAIRS = (("gae", "mlp"), ("ifix", "mlp"), ("iself", "mlp"))
TAUS = (1.5, 2.0, 3.0)
PHIS = (3.0, 4.0, 5.0)
MEMBER_K = (6, 9, 12)
BAND_WIDTH = np.array([3.5, 4.0, 5.0, 17.0, 30.0])        # c1b_build_trainset.BANDS widths (Hz)
N_CH, LAT, WIN = 18, 16, 4
TOL = dict(k_rel=1e-6, x_tp=1, x_fp=2)
VERSION_KEYS = ("python", "numpy", "scipy", "sklearn", "pandas", "torch", "torch_geometric")
SESSION_STOP_H = float(os.environ.get("FA14_SESSION_STOP_H", 11.0))
CODE_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:16]
P0_TOTALS = {("gae", "own"): 1129, ("mlp", "own"): 827, ("gae", "fixed0.005"): 920, ("mlp", "fixed0.005"): 650}
T0 = time.time()
STATE = dict(gates=[], mode=None)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def hours():
    return (time.time() - T0) / 3600


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _jdump(p, obj):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(obj, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))


def gate(rec, stop=True):
    STATE["gates"].append(rec)
    _jdump(OUT / "gates.json", STATE["gates"])
    log(f"{rec['gate']}: {rec['status']} {rec.get('summary', '')}")
    if stop and rec["status"] not in ("PASS", "n/a"):
        write_summary()
        raise SystemExit(f"STOPPED: {rec['gate']} {rec['status']}: {rec.get('summary', '')}")


# ============================================================================ environment
def versions():
    import scipy
    import sklearn
    import torch
    v = dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__, sklearn=sklearn.__version__,
             pandas=pd.__version__, torch=torch.__version__)
    try:
        import torch_geometric
        v["torch_geometric"] = torch_geometric.__version__
    except ImportError:
        v["torch_geometric"] = None
    return v


def gate_mode():
    """exact when the library versions equal R2_A's (the run that reproduced the record exactly on Kaggle CPU)."""
    ref = json.loads(R2A_META.read_text())["versions"]
    mine = versions()
    diff = {k: (mine.get(k), ref.get(k)) for k in VERSION_KEYS if mine.get(k) != ref.get(k)}
    STATE["mode"] = "exact" if not diff else "tolerance"
    gate(dict(gate="mode", status="PASS", mode=STATE["mode"], versions=mine, differing=diff,
              summary=f"{STATE['mode']} (versions vs R2_A: {diff or 'equal'})"))
    return STATE["mode"]


def run_meta(notebook, commit, parts):
    _jdump(OUT / "run_meta.json", dict(notebook=notebook, repo_commit=commit, parts=list(parts), code_sha=CODE_SHA,
                                        f1_core_sha=F.sha16(F.__file__), model_cmp_core_sha=F.sha16(C.__file__),
                                        started=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                                        cpu_count=os.cpu_count(), platform=platform.platform(), versions=versions(),
                                        test_mode=TEST))


def finish_meta(extra):
    p = OUT / "run_meta.json"
    m = json.loads(p.read_text()) if p.exists() else {}
    m.update(extra, finished=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()), runtime_h=round(hours(), 3),
             peak_rss_self_mb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1))
    _jdump(p, m)


# ============================================================================ data view (earlier .npz)
def build_view():
    """VIEW/{case}.npz -> the earlier .npz (r2_core.locate_earlier); sha256 = R0's committed references (G-data)."""
    t = time.time()
    refs = json.loads(R0GATES.read_text())["references"]
    shutil.rmtree(VIEW, ignore_errors=True)
    VIEW.mkdir(parents=True, exist_ok=True)
    rep, bad = {}, []
    for c in C.ALL:
        p = R0.locate_earlier(c)
        h = sha256_file(p)
        want = refs.get(c, {}).get("sha256")
        rep[c] = dict(path=str(p), sha256=h, pinned=want, equal=h == want)
        if h != want:
            bad.append(c)
        (VIEW / f"{c}.npz").symlink_to(p)
    gate(dict(gate="G-data", status="PASS" if not bad else "FAIL", files=rep, seconds=round(time.time() - t, 1),
              summary=f"{len(rep)} earlier .npz, sha256 = R0 references for {len(rep) - len(bad)}; differing {bad}"))
    set_view()


def set_view():
    C._NPZ.clear()
    C._CACHE.clear()
    C.locate_all(str(VIEW))


# ============================================================================ models
def ckpt_path(p, model, f):
    if int(p) == 0:
        return (C.X3 / "models" / f"fold{f}" / f"gae_fold{f}_seed42.pt") if model == "gae" else \
            (MC / "ckpt" / f"mlp_fold{f}.pt")
    return F1RAW / f"p{int(p)}" / "jobs" / f"{model}_fold{f}" / f"{model}_p{int(p)}_fold{f}_seed{F.seed_of(p)}.pt"


def load_model(p, model, f):
    """the committed fold model of the record and the constants it was scored with."""
    import torch
    pt = ckpt_path(p, model, f)
    if not pt.exists():
        raise SystemExit(f"STOP G-ckpt: checkpoint missing in the pinned repository: {pt}")
    if int(p) == 0:
        meta = C.fold_meta(f)
    else:
        meta = json.loads(pt.with_suffix(".json").read_text())
    m = F.build(model)
    m.load_state_dict(torch.load(str(pt), map_location="cpu"), strict=True)
    return m.eval(), meta, sha256_file(pt)


def valid_adj(ctx):
    """the adjacency of every valid window as model_cmp_core.node_input makes it (float32; non-finite windows -> 0)."""
    adj = ctx["z"]["adj"][ctx["idx"]].astype(np.float32)
    adj[~np.isfinite(adj).all(axis=(1, 2))] = 0.0
    return adj


def fixed_graph(adj):
    """one time-stable graph per patient: pairs = apply_topk_threshold on the selection frequency (20 %, ties kept),
    weight = the pair's mean weight when selected; symmetric, zero diagonal (float32)."""
    sel = adj > 0
    cnt = sel.sum(0)
    freq = cnt / max(1, len(adj))
    wmean = np.where(cnt > 0, adj.sum(0, dtype=np.float64) / np.maximum(cnt, 1), 0.0)
    keep = GC.apply_topk_threshold(freq) > 0
    G = np.where(keep, wmean, 0.0)
    np.fill_diagonal(G, 0.0)
    return G.astype(np.float32)


def encode_Z(model, meta, ctx, prop=None, chunk=2048):
    """node latents of the GAE on every valid window -- f1_core.encode_D's construction, with the propagation graph
    optionally replaced (prop None = the window's own graph; "self" = no edges; an (18, 18) array = that graph for
    every window). The node input always uses the window's own connectivity row."""
    import torch
    model = model.cpu().eval()
    X30, adj, xn, fa = C.node_input(ctx["z"], ctx["idx"], meta)
    Z = np.empty((len(adj), N_CH, LAT), np.float32)
    P0 = None if prop is None or isinstance(prop, str) else torch.tensor(np.asarray(prop, dtype=np.float32))
    with torch.no_grad():
        for s in range(0, len(adj), chunk):
            A = torch.tensor(adj[s:s + chunk]); B = A.shape[0]
            An = A / (A.amax(dim=(1, 2), keepdim=True) + 1e-8)
            x = torch.cat([An, torch.tensor(xn[s:s + chunk]), torch.tensor(fa[s:s + chunk])], 2).reshape(B * N_CH, -1)
            if prop is None:
                P = A
            elif isinstance(prop, str) and prop == "self":
                P = torch.zeros_like(A)
            else:
                P = P0.expand(B, N_CH, N_CH)
            b, i, j = P.nonzero(as_tuple=True)
            ei = torch.stack([b * N_CH + i, b * N_CH + j])
            Z[s:s + chunk] = model.encoder(x, ei, P[b, i, j]).view(B, N_CH, LAT).numpy()
    return Z


# ============================================================================ analysis (pure functions on arrays)
def rz_cols(D):
    """per-channel robust z over every valid window -- the construction of e17b_latent_family.member."""
    okk = np.ones(len(D), bool)
    return np.column_stack([E16.rz(D[:, j], okk) for j in range(D.shape[1])]).astype(np.float64)


def input_amplitude(f7v):
    """model-free per-channel input amplitude: log of the summed band power of f7 (log mean PSD x bandwidth), robust z
    per channel over the patient's valid windows."""
    lp = f7v[..., :5].astype(np.float64) + np.log(BAND_WIDTH)
    m = lp.max(axis=-1, keepdims=True)
    tot = (m + np.log(np.exp(lp - m).sum(-1, keepdims=True)))[..., 0]
    return rz_cols(tot)


def input_focal(A, phi):
    return (A.max(1) >= phi) & ((A >= 2.0).sum(1) <= 2)


def model_focal(Zc, phi):
    return (Zc.max(1) >= phi) & ((Zc >= 2.0).sum(1) <= 2)


def members(Zc):
    srt = -np.sort(-Zc, axis=1)
    return {k: srt[:, k - 1] for k in MEMBER_K}


def _mean(v):
    return float(np.mean(v)) if len(v) else np.nan


def h1_rows(Za, Zm, A, bg, phi, tau):
    """input-focal, mlp-focal and the swap (arm-focal) statistics for one (phi, tau)."""
    Ra, Rm = (Za >= tau).sum(1), (Zm >= tau).sum(1)
    out = []
    fin = input_focal(A, phi) & bg
    oth = bg & ~fin
    ma, mm = members(Za), members(Zm)
    r = dict(definition="input", n=int(fin.sum()), dR=_mean((Ra - Rm)[fin]), n_other=int(oth.sum()),
             dR_other=_mean((Ra - Rm)[oth]))
    for k in MEMBER_K:
        r[f"dm{k}"] = _mean((ma[k] - mm[k])[fin])
        r[f"dm{k}_other"] = _mean((ma[k] - mm[k])[oth])
    out.append(r)
    fm = model_focal(Zm, phi) & bg
    out.append(dict(definition="mlpfocal", n=int(fm.sum()), dR=_mean((Ra - Rm)[fm])))
    fa = model_focal(Za, phi) & bg
    out.append(dict(definition="armfocal", n=int(fa.sum()), dR=_mean((Rm - Ra)[fa])))
    return out


def h1nb_counts(Za, Zm, A, bg, phi, tau, prop_graph, win_adj):
    """input-focal windows: channels other than the focal (argmax input amplitude) one, by category, with how many are
    neighbours of the focal channel in the arm's propagation graph and in the window's own graph."""
    fin = np.flatnonzero(input_focal(A, phi) & bg)
    if not len(fin):
        return {}
    fstar = A[fin].argmax(1)
    za, zm = Za[fin], Zm[fin]
    other = np.ones((len(fin), N_CH), bool)
    other[np.arange(len(fin)), fstar] = False
    wrow = win_adj[fin, fstar, :] > 0
    if prop_graph is None:
        prow = np.zeros_like(wrow)
    elif isinstance(prop_graph, str) and prop_graph == "window":
        prow = wrow
    else:
        prow = np.asarray(prop_graph)[fstar, :] > 0
    cats = dict(armonly=(za >= tau) & (zm < tau), mlponly=(zm >= tau) & (za < tau), notrec=za < tau,
                ctl=(zm >= 1.0) & (zm < tau), all=np.ones_like(za, bool))
    out = {}
    for name, m in cats.items():
        m = m & other
        out[f"n_{name}"] = int(m.sum())
        out[f"nb_{name}"] = int((m & prow).sum())
        out[f"nbw_{name}"] = int((m & wrow).sum())
    return out


def consecutive_pairs(idx, wf, bg):
    """indices w (into the valid-window arrays) whose previous valid window is the previous window of the same file;
    both background."""
    w = np.arange(1, len(idx))
    ok = (idx[w] - idx[w - 1] == 1) & (wf[w] == wf[w - 1]) & bg[w] & bg[w - 1]
    return w[ok]


def edge_change(win_adj, w):
    """per channel, between window w - 1 and w: Jaccard distance of the neighbour sets, |change of weighted degree|,
    isolated <-> connected flip."""
    N1, N0 = win_adj[w] > 0, win_adj[w - 1] > 0
    inter, union = (N1 & N0).sum(2), (N1 | N0).sum(2)
    J = np.where(union > 0, 1.0 - inter / np.maximum(union, 1), 0.0)
    d1, d0 = win_adj[w].sum(2, dtype=np.float64), win_adj[w - 1].sum(2, dtype=np.float64)
    return J, np.abs(d1 - d0), (d1 == 0) != (d0 == 0)


def _within(v, g):
    """v demeaned within groups g (both 1-D)."""
    s = pd.Series(v).groupby(g).transform("mean").to_numpy()
    return v - s


def h2_row(Za, Zm, A, win_adj, w):
    if not len(w):
        return dict(n_pairs=0)
    J, dd, flip = edge_change(win_adj, w)
    delta = (Za[w] - Zm[w]).ravel()
    amp = A[w].ravel()
    dec = np.minimum((pd.Series(amp).rank(pct=True, method="first").to_numpy() * 10).astype(int), 9)
    Jv, dv, fv = J.ravel(), dd.ravel(), flip.ravel()
    sd = dv.std() if dv.std() > 0 else 1.0
    yt, Jt, dt = _within(delta, dec), _within(Jv, dec), _within(dv / sd, dec)
    bJ = float((Jt * yt).sum() / (Jt * Jt).sum()) if (Jt * Jt).sum() > 0 else np.nan
    bd = float((dt * yt).sum() / (dt * dt).sum()) if (dt * dt).sum() > 0 else np.nan
    flip_eff = float(yt[fv].mean() - yt[~fv].mean()) if fv.any() and (~fv).any() else np.nan
    return dict(n_pairs=int(len(w)), n_obs=int(len(delta)), slope_J=bJ, slope_ddeg_sd=bd, flip_effect=flip_eff,
                mean_J=float(Jv.mean()), flip_share=float(fv.mean()), mean_delta=float(delta.mean()))


def lag1(m_full, idx, w):
    """lag-1 autocorrelation of a full-length series over the consecutive valid background pairs w."""
    if len(w) < 3:
        return np.nan
    a, b = m_full[idx[w]], m_full[idx[w - 1]]
    if a.std() == 0 or b.std() == 0:
        return np.nan
    return float(np.corrcoef(a, b)[0, 1])


def fa_events(events, refs):
    """events {file: [(a, b), ...]} -> list of (file, a, b, is_false_alarm) with the record's PRE / POST rule."""
    out = []
    for f, evs in events.items():
        rr = refs.get(f, [])
        for a, b in evs:
            hit = any(b >= ra - C.PRE and a <= rb + C.POST for ra, rb in rr)
            out.append((f, a, b, not hit))
    return out


def f3a_counts(events, refs):
    ev = fa_events(events, refs)
    fa = [e for e in ev if e[3]]
    return dict(n_ev=len(ev), t_ev=float(sum(b - a for _, a, b, _ in ev)), n_fa=len(fa),
                t_fa=float(sum(b - a for _, a, b, _ in fa)))


def overlaps(ev_list, f, a, b):
    return any(b >= x0 and a <= x1 for x0, x1 in ev_list.get(f, []))


def peak_window(xs_full, fidx, f, a, b, ok):
    """global window index of the highest smoothed score inside event (a, b) of file f (valid windows only)."""
    m = np.flatnonzero(fidx == f)
    i0, i1 = int(a // WIN), max(int(a // WIN) + 1, int(b // WIN))
    w = m[i0:i1]
    w = w[ok[w]]
    if not len(w):
        return None
    return int(w[np.nanargmax(xs_full[w])])


def seizure_peaks(xs_full, ok, fidx, refs):
    vals = xs_full[ok & np.isfinite(xs_full)]
    out = []
    for f, rr in refs.items():
        m = np.flatnonzero(fidx == f)
        t = np.arange(len(m)) * WIN
        for a, b in rr:
            w = m[(t + WIN > a - C.PRE) & (t < b + C.POST)]
            w = w[ok[w]]
            if not len(w):
                out.append(dict(file=int(f), onset_s=int(a), duration_s=int(b - a), peak=np.nan, p_need=np.nan))
                continue
            pk = float(np.nanmax(xs_full[w]))
            out.append(dict(file=int(f), onset_s=int(a), duration_s=int(b - a), peak=pk,
                            p_need=float((vals >= pk).mean())))
    return out


def gcn_self_weight(win_adj):
    """GCN self weight per node and window: 1 / (1 + sum_j w_ij) (add_remaining_self_loops fill 1, symmetric norm)."""
    return 1.0 / (1.0 + win_adj.sum(2, dtype=np.float64))


# ============================================================================ per case
def analyze_case(ctx, arm_out, G, p, f):
    """every descriptive table of one held-out case from the four arms' outputs."""
    s = ctx["s"]
    idx, ok, fidx = ctx["idx"], ctx["ok"], ctx["fidx"]
    wf = fidx[idx]
    bg = ctx["nonict"][idx]
    nonict_v = ~ctx["ict"][idx]
    refs = P3L.refs_of(ctx)
    A = input_amplitude(ctx["z"]["f7"][idx])
    adj = valid_adj(ctx)
    Z = {a: rz_cols(arm_out[a]["D"]) for a in ARMS}
    xs = {a: PS.smoothed(ctx, arm_out[a]["x"], C.SMOOTH) for a in ARMS}
    key = dict(partition=int(p), fold=int(f), subject=s)
    T = {k: [] for k in ("f3a", "h1", "h1nb", "h1fa", "h2", "smooth", "h3", "desc")}
    for a in ARMS:
        for point in ("own", "fixed0.005"):
            for stage in ("detector", "localized"):
                ev = arm_out[a]["events"][point][stage]
                T["f3a"].append(dict(key, arm=a, point=point, stage=stage, **f3a_counts(ev, refs)))
        for r in seizure_peaks(xs[a], ok, fidx, refs):
            T["h3"].append(dict(key, arm=a, **r))
    w = consecutive_pairs(idx, wf, bg)
    for a in ARMS:
        T["smooth"].append(dict(key, arm=a, lag1=lag1(arm_out[a]["m"], idx, w), n_pairs=int(len(w))))
    fin_all = {phi: input_focal(A, phi) for phi in PHIS}
    for arm, ref in PAIRS:
        pk = dict(key, arm=arm, ref=ref)
        for phi in PHIS:
            for tau in TAUS:
                for r in h1_rows(Z[arm], Z[ref], A, bg, phi, tau):
                    T["h1"].append(dict(pk, phi=phi, tau=tau, **r))
                prop = "window" if arm == "gae" else (G if arm == "ifix" else None)
                c = h1nb_counts(Z[arm], Z[ref], A, bg, phi, tau, prop, adj)
                if c:
                    T["h1nb"].append(dict(pk, phi=phi, tau=tau, **c))
            # false-alarm peaks (own point, localized)
            loc_a, loc_r = arm_out[arm]["events"]["own"]["localized"], arm_out[ref]["events"]["own"]["localized"]
            det_a, det_r = arm_out[arm]["events"]["own"]["detector"], arm_out[ref]["events"]["own"]["detector"]
            pos = np.full(ctx["n"], False)
            pos[idx] = fin_all[phi]
            cnt = dict(n_armonly=0, focal_armonly=0, n_refonly=0, focal_refonly=0)
            for (fi, a0, b0, isfa) in fa_events(loc_a, refs):
                if isfa and not overlaps(det_r, fi, a0, b0):
                    pw = peak_window(xs[arm], fidx, fi, a0, b0, ok)
                    if pw is not None:
                        cnt["n_armonly"] += 1; cnt["focal_armonly"] += int(pos[pw])
            for (fi, a0, b0, isfa) in fa_events(loc_r, refs):
                if isfa and not overlaps(det_a, fi, a0, b0):
                    pw = peak_window(xs[ref], fidx, fi, a0, b0, ok)
                    if pw is not None:
                        cnt["n_refonly"] += 1; cnt["focal_refonly"] += int(pos[pw])
            T["h1fa"].append(dict(pk, phi=phi, **cnt, n_nonict=int(nonict_v.sum()),
                                  focal_nonict=int((fin_all[phi] & nonict_v).sum())))
        T["h2"].append(dict(pk, **h2_row(Z[arm], Z[ref], A, adj, w)))
    sw = gcn_self_weight(adj)
    swG = 1.0 / (1.0 + G.sum(1, dtype=np.float64))
    J = edge_change(adj, w)[0] if len(w) else np.zeros((0, N_CH))
    T["desc"].append(dict(key, n_valid=int(len(idx)), n_bg=int(bg.sum()), neighbour_share=float((1 - sw).mean()),
                          isolated_share=float((adj.sum(2) == 0).mean()), mean_jaccard=float(J.mean()) if len(J) else np.nan,
                          fixed_edges=int((G > 0).sum() // 2), fixed_neighbour_share=float((1 - swG).mean()),
                          window_edges=float((adj > 0).sum((1, 2)).mean() / 2)))
    return T


# ============================================================================ jobs (p, f)
def arm_fold(p, f, arm, man):
    """scores of one arm on one fold: rows of f1_core.run_fold (the record's code path) + the held-out cases' D, x, m and
    events at the own and the fixed point (V9E1.evaluate_arm, the call evaluate_case makes)."""
    model, meta, sha = load_model(p, BASE[arm], f)
    cache, graphs = {}, {}
    held = set(man["held_out_cases"])

    def D_fn(ctx):
        if arm in ("gae", "mlp"):
            D = F.encode_D(arm, model, meta, ctx)
        elif arm == "ifix":
            G = fixed_graph(valid_adj(ctx))
            graphs[ctx["s"]] = G
            D = C.d_from_Z(encode_Z(model, meta, ctx, prop=G))
        else:
            D = C.d_from_Z(encode_Z(model, meta, ctx, prop="self"))
        if ctx["s"] in held:
            cache[ctx["s"]] = D
        return D

    per, cur, au, seiz, k, sec = F.run_fold(arm, int(p), int(f), man, D_fn)
    out = {}
    for s in man["held_out_cases"]:
        ctx = C.make_ctx(s)
        D = cache[s]
        x, m = C.scalars("D", ctx, D)
        o_own, det, loc = V9E1.evaluate_arm(ctx, x, k, C.FLOOR, C.CAP, C.SMOOTH, m=m)
        o_fix, det0, loc0 = V9E1.evaluate_arm(ctx, x, k, C.FLOOR, C.CAP, C.SMOOTH, m=None)
        out[s] = dict(D=D, x=x, m=m, events=dict(own=dict(detector=det, localized=loc),
                                                    **{"fixed0.005": dict(detector=det0, localized=loc0)}))
        if arm == "gae":           # G-arm: this module's encoder with the window's own graph = f1_core.encode_D
            D2 = C.d_from_Z(encode_Z(model, meta, ctx, prop=None))
            if not np.array_equal(D2, D):
                raise SystemExit(f"STOP G-arm: p{p} fold {f} {s}: encode_Z(window graph) != f1_core.encode_D "
                                 f"(max |diff| {np.nanmax(np.abs(D2 - D))})")
    info = dict(arm=arm, k=k, score_s=round(sec, 1), checkpoint=str(ckpt_path(p, BASE[arm], f).relative_to(REPO)),
                checkpoint_sha256=sha)
    return per, seiz, out, graphs, info


def job_dir(p, f):
    return OUT / f"p{int(p)}" / "jobs" / f"f{int(f)}"


TABLES = ("rows", "seiz", "f3a", "h1", "h1nb", "h1fa", "h2", "smooth", "h3", "desc")


def job(spec):
    """one (partition, fold): the four arms, G-arm, then the analysis of the fold's held-out cases. Atomic."""
    p, f = int(spec["p"]), int(spec["f"])
    jd = job_dir(p, f)
    if (jd / "DONE.json").exists():
        return dict(p=p, f=f, status="exists")
    if hours() > SESSION_STOP_H:
        return dict(p=p, f=f, status="NOT RUN (session time)")
    shutil.rmtree(jd, ignore_errors=True)
    jd.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    try:
        import torch
        torch.set_num_threads(1)
        man = F.manifest(p)[f]
        rows, seiz, outs, infos, G = [], [], {}, [], {}
        for arm in ARMS:
            per, sz, out, graphs, info = arm_fold(p, f, arm, man)
            rows += [dict(r, partition=p) for r in per]
            seiz += [dict(r, arm=arm, partition=p) for r in sz]
            outs[arm] = out
            infos.append(info)
            G.update(graphs)
        T = {k: [] for k in TABLES[2:]}
        for s in man["held_out_cases"]:
            ctx = C.make_ctx(s)
            res = analyze_case(ctx, {a: outs[a][s] for a in ARMS}, G[s], p, f)
            for k, v in res.items():
                T[k] += v
        pd.DataFrame(rows).rename(columns={"model": "arm"}).to_csv(jd / "rows.csv", index=False)
        pd.DataFrame(seiz).drop(columns=["model"], errors="ignore").to_csv(jd / "seiz.csv", index=False)
        for k, v in T.items():
            pd.DataFrame(v).to_csv(jd / f"{k}.csv", index=False)
        _jdump(jd / "fit.json", dict(p=p, f=f, arms=infos, seconds=round(time.time() - t0, 1),
                                     held_out=man["held_out_cases"],
                                     peak_rss_mb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)))
        _jdump(jd / "DONE.json", dict(status="done", code_sha=CODE_SHA, seconds=round(time.time() - t0, 1)))
        C._CACHE.clear()
        return dict(p=p, f=f, status="done", seconds=round(time.time() - t0, 1))
    except SystemExit as e:
        (jd / "FAILED.txt").write_text(str(e))
        return dict(p=p, f=f, status="STOP", error=str(e))
    except Exception:
        (jd / "FAILED.txt").write_text(traceback.format_exc())
        return dict(p=p, f=f, status="FAILED", error=traceback.format_exc()[-2000:])


def _init_worker(env):
    os.environ.update(env)
    import torch
    torch.set_num_threads(1)
    set_view()


def import_previous():
    """finished jobs of an attached previous output (same code sha) are copied in and reused."""
    n = 0
    for d in sorted(R0.INPUT.rglob("fa14/p*/jobs/f*/DONE.json")) if R0.INPUT.exists() else []:
        try:
            if json.loads(d.read_text()).get("code_sha") != CODE_SHA:
                continue
        except Exception:
            continue
        p, f = int(d.parent.parent.parent.name[1:]), int(d.parent.name[1:])
        dst = job_dir(p, f)
        if not (dst / "DONE.json").exists():
            shutil.copytree(d.parent, dst, dirs_exist_ok=True)
            n += 1
    if n:
        log(f"resume: {n} finished jobs imported from an attached previous output")
    return n


def n_workers(gb_per_worker=5.0):
    try:
        ram = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1e9
    except (ValueError, OSError):
        ram = 16.0
    return max(1, min(4, os.cpu_count() or 1, int(ram // gb_per_worker)))


def run_jobs(parts, workers=None):
    specs = [dict(p=p, f=f) for p in parts for f in FOLDS]
    todo = [s for s in specs if not (job_dir(s["p"], s["f"]) / "DONE.json").exists()]
    w = workers or n_workers()
    log(f"jobs: {len(specs)} ({len(specs) - len(todo)} reused), {len(todo)} to run on {w} workers")
    env = {k: v for k, v in os.environ.items() if k.startswith(("FA14_", "THESIS_", "OMP_", "MKL_"))}
    env.update(OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
    res = []
    if todo:
        if w == 1:
            _init_worker(env)
            res = [job(s) for s in todo]
        else:
            with mp.get_context("spawn").Pool(w, initializer=_init_worker, initargs=(env,)) as pool:
                for r in pool.imap_unordered(job, todo):
                    log(f"job p{r['p']} f{r['f']}: {r['status']} {r.get('seconds', '')}")
                    res.append(r)
    _jdump(OUT / "jobs.json", res)
    bad = [r for r in res if r["status"] not in ("done", "exists")]
    stops = [r for r in bad if r["status"] == "STOP"]
    if stops:
        name = "G-arm" if any("G-arm" in r["error"] for r in stops) else "G-jobs"
        gate(dict(gate=name, status="FAIL", jobs=stops, summary=f"{len(stops)} jobs stopped: {stops[0]['error']}"))
    gate(dict(gate="G-jobs", status="PASS" if not bad else "FAIL", failed=bad,
              summary=f"{len(specs)} jobs, {len(bad)} not done" + (f": {bad[0].get('error', bad[0]['status'])[:400]}"
                                                                   if bad else "")))
    gate(dict(gate="G-arm", status="PASS", summary="encode_Z(window graph) = f1_core.encode_D on every held-out case"))


# ============================================================================ merge + G-base
def merge(p):
    pdir = OUT / f"p{int(p)}"
    for t in TABLES:
        parts = [pd.read_csv(job_dir(p, f) / f"{t}.csv") for f in FOLDS
                 if (job_dir(p, f) / f"{t}.csv").exists() and (job_dir(p, f) / f"{t}.csv").stat().st_size > 1]
        if parts:
            pd.concat(parts, ignore_index=True).to_csv(pdir / f"{t}.csv", index=False)
    fits = [json.loads((job_dir(p, f) / "fit.json").read_text()) for f in FOLDS]
    _jdump(pdir / "fits.json", fits)


def record(p):
    if int(p) == 0:
        rows = pd.read_csv(MC / "per_subject.csv")
        seiz = pd.read_csv(MC / "seizures.csv")
        rows["fold"] = rows["fold"].astype(int)
        return rows, seiz
    return pd.read_csv(F1RAW / f"p{int(p)}" / "per_subject.csv"), pd.read_csv(F1RAW / f"p{int(p)}" / "seizures.csv")


def gate_base(p):
    pdir = OUT / f"p{int(p)}"
    mine = pd.read_csv(pdir / "rows.csv")
    mseiz = pd.read_csv(pdir / "seiz.csv")
    ref, rseiz = record(p)
    key = ["fold", "subject", "point", "stage"]
    out, ok_all = {}, True
    for model in ("gae", "mlp"):
        rr = ref[ref.model == model]
        mm = mine[mine.arm == model]
        mg = rr.merge(mm, on=key, suffixes=("_ref", ""), how="outer", indicator=True)
        missing = int((mg._merge != "both").sum())
        mg = mg[mg._merge == "both"]
        dtp, dfp = (mg.tp - mg.tp_ref).abs(), (mg.fp - mg.fp_ref).abs()
        nref_bad = int((mg.n_ref != mg.n_ref_ref).sum())
        exact = int(((dtp == 0) & (dfp == 0) & (mg.n_ref == mg.n_ref_ref)).sum())
        kk = mg[(mg.point == "own") & mg.k_ref.notna()]
        krel = float(np.max(np.abs(kk.k - kk.k_ref) / np.maximum(np.abs(kk.k_ref), 1e-12))) if len(kk) else np.inf
        sk = ["subject", "file", "onset_s"]
        sm = rseiz[rseiz.model == model][sk + ["caught"]].merge(mseiz[mseiz.arm == model][sk + ["caught"]], on=sk,
                                                                 suffixes=("_ref", ""), how="outer", indicator=True)
        s_missing = int((sm._merge != "both").sum())
        sm = sm[sm._merge == "both"]
        caught_diff = int((sm.caught.astype(bool) != sm.caught_ref.astype(bool)).sum())
        n_rows = 24 * 2 * 2
        if STATE["mode"] == "exact":
            ok = (missing == 0 and len(mg) == n_rows and exact == len(mg) and krel <= TOL["k_rel"]
                  and s_missing == 0 and caught_diff == 0)
        else:
            ok = (missing == 0 and len(mg) == n_rows and nref_bad == 0 and int(dtp.max()) <= TOL["x_tp"]
                  and int(dfp.max()) <= TOL["x_fp"] and s_missing == 0)
        tot = {pt: int(mm[(mm.point == pt) & (mm.stage == "localized")].fp.sum()) for pt in ("own", "fixed0.005")}
        tot_ref = {pt: int(rr[(rr.point == pt) & (rr.stage == "localized")].fp.sum()) for pt in ("own", "fixed0.005")}
        if int(p) == 0 and not TEST:
            # the record itself must hold the numbers the report states (1,129 / 827 own; 920 / 650 at 0.005)
            ok = ok and all(tot_ref[pt] == P0_TOTALS[(model, pt)] for pt in tot_ref)
            if STATE["mode"] == "exact":
                ok = ok and tot == tot_ref
        bad = mg[(dtp > 0) | (dfp > 0)][key + ["tp_ref", "tp", "fp_ref", "fp"]].to_dict("records")[:50]
        out[model] = dict(status="PASS" if ok else "FAIL", rows=len(mg), exact_rows=exact, missing=missing,
                          n_ref_differ=nref_bad, max_abs_dtp=int(dtp.max()) if len(mg) else -1,
                          max_abs_dfp=int(dfp.max()) if len(mg) else -1, k_max_rel=krel, seizures=len(sm),
                          seizures_missing=s_missing, caught_differ=caught_diff, fp_localized=tot,
                          fp_localized_record=tot_ref, differing_rows=bad)
        ok_all &= ok
    g = dict(gate=f"G-base p{int(p)}", status="PASS" if ok_all else "FAIL", mode=STATE["mode"], **out,
             summary="; ".join(f"{m}: {o['status']} {o['rows']} rows, {o['exact_rows']} exact, k {o['k_max_rel']:.1e}, "
                               f"caught differ {o['caught_differ']}/{o['seizures']}, fp own/fixed "
                               f"{o['fp_localized']['own']}/{o['fp_localized']['fixed0.005']}" for m, o in out.items()))
    gate(g, stop=False)
    if not ok_all:
        for t in TABLES[2:]:
            (pdir / f"{t}.csv").unlink(missing_ok=True)
    return ok_all


# ============================================================================ G-gcn
def gate_gcn(case=None, n=256):
    """the self weight 1 / (1 + sum_j w_ij) = torch_geometric's gcn_norm (self loops) on real windows."""
    import torch
    from torch_geometric.nn.conv.gcn_conv import gcn_norm
    ctx = C.make_ctx(case or C.ALL[0])
    adj = valid_adj(ctx)[:n]
    A = torch.tensor(adj)
    b, i, j = A.nonzero(as_tuple=True)
    ei = torch.stack([b * N_CH + i, b * N_CH + j])
    ei2, w2 = gcn_norm(ei, A[b, i, j], num_nodes=len(adj) * N_CH, add_self_loops=True)
    self_ = ei2[0] == ei2[1]
    got = np.zeros(len(adj) * N_CH)
    got[ei2[0][self_].numpy()] = w2[self_].numpy()
    want = gcn_self_weight(adj).ravel()
    err = float(np.max(np.abs(got - want)))
    C._CACHE.clear()
    gate(dict(gate="G-gcn", status="PASS" if err <= 1e-6 else "FAIL", max_abs=err,
              summary=f"self weight 1/(1 + sum w) vs gcn_norm on {len(adj)} windows of {ctx['s']}: max |diff| {err:.1e}"))


# ============================================================================ notebook driver
def write_summary(extra=()):
    L = [f"# F-A1.4 run ({time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}; code {CODE_SHA}; mode {STATE['mode']})",
         "", "| gate | status | summary |", "|---|---|---|"]
    L += [f"| {g['gate']} | {g['status']} | {str(g.get('summary', ''))[:300]} |" for g in STATE["gates"]]
    L += ["", *extra]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "SUMMARY.md").write_text("\n".join(L) + "\n")


def main(notebook, commit, parts, workers=None):
    OUT.mkdir(parents=True, exist_ok=True)
    run_meta(notebook, commit, parts)
    gate(dict(gate="G-mod", status="PASS", summary=f"closed modules from {REPO / 'src'}"))
    gate_mode()
    build_view()
    gate_gcn()
    import_previous()
    run_jobs(parts, workers)
    fails = []
    for p in parts:
        merge(p)
        if not gate_base(p):
            fails.append(p)
    finish_meta(dict(parts_failed_G_base=fails))
    write_summary()
    if fails:
        raise SystemExit(f"STOPPED: G-base failed for partitions {fails} (rows kept; analysis tables removed)")
    log(f"END: partitions {list(parts)} done; G-base PASS; output {OUT}")
