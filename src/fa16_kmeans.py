#!/usr/bin/env python
"""
fa16_kmeans.py -- F-A1.6: a K-means baseline in the six-model comparison (request of Track A, board R208; design
approved by the author 17/11 01:22, docs/FUTURE_RESEARCH_PLAN.md §12 17/11 01:30, chat D30-F).

Question. Under the same windows, folds and post-score chain as the six-model comparison (results/model_cmp: 4-fold
patient-wise CV, 24 CHB-MIT cases of the defense-time data copy, chb01 + chb21 one subject, seed 42), how does a
label-free K-means baseline compare with the GAE at its own label-free operating point?

Arm 'km' -- built exactly like the Isolation Forest arm (model_cmp_core.if_D): per patient and per channel, on every
valid window, the GAE node input with unclipped standardised f7 (model_cmp_core.node_input(..., fold_meta(1),
clip=False)); label-free and fold-independent. Rule, fixed before the run:
  scaling   per feature, centre on the median and divide by the interquartile range over the patient's own windows
            (sklearn RobustScaler; a feature with IQR 0 keeps scale 1 -- the sparse adjacency entries, already in
            [0, 1]); Bouman, Bukhsh & Heskes 2024, JMLR 25 (jmlr.org/papers/v25/23-0570): distance methods are
            scale-sensitive, median / IQR are less affected by anomalies than mean / SD.
  clusters  k in 2..10 with the largest mean silhouette (Rousseeuw 1987, DOI 10.1016/0377-0427(87)90125-7; among the
            best of 30 indices in Arbelaitz et al. 2013, DOI 10.1016/j.patcog.2012.07.021), computed on a random
            sample of 5,000 windows (numpy default_rng(42), without replacement; all windows if fewer); ties -> the
            smaller k. KMeans(k, n_init=10, random_state=42) on the sample for the selection, then refitted with the
            chosen k on every window.
  score     D = Euclidean distance of each window to its nearest centroid in the scaled space (Chandola, Banerjee &
            Kumar 2009, DOI 10.1145/1541880.1541882: clustering-based anomaly score)  -> arm 'km' (primary).
Arm 'km_u' (secondary, author 17/11 01:43, option A; same fit): the unweighted cluster-based local outlier factor
(u-CBLOF; He, Xu & Deng 2003, DOI 10.1016/S0167-8655(03)00003-5; unweighted as evaluated by Goldstein & Uchida 2016,
DOI 10.1371/journal.pone.0152173): clusters sorted by size are split into large and small with alpha = 0.9, beta = 5,
operationalised as PyOD's CBLOF (Zhao, Nasrullah & Li 2019, JMLR 20(96); first index meeting both conditions, else the
alpha one, else the beta one); a window of a large cluster scores its distance to its own centroid, a window of a small
cluster its distance to the nearest large-cluster centroid; no valid split (e.g. two equal clusters) -> every cluster
large, km_u = km. Why: the synthetic test found that the silhouette rule can give a compact far group of windows a
cluster of its own (k = 2, 1 % of the windows), which makes their distance small -- a known property of the
nearest-centroid score that u-CBLOF exists to remove.
Diagnostic (after scoring; labels never enter either arm): per case x channel, the share of all windows and of the
seizure windows that fall in small clusters (km_k.csv, columns diag_*).
Then the identical chain as the Isolation Forest arm: model_cmp_core.run_fold('km', f, ..., 'D') (robust z, members
6 / 9 / 12 + mean with the +-15 min drift correction, percentile ensemble, smoothing 5, per-patient budget with k per
fold calibrated on the fold's training cases, merge 90 s, kernel change point localizer, SzCORE scoring).

Gates (STOP before the K-means arm is run if any fails):
  D0     data identity (model_cmp_core.gate_D0)
  G-mini the GAE fold-1 chb12 row = the committed CV (model_cmp_run.mini_gate)
  GG     the GAE row reproduces results/v9_x3 and results/v9_final/hard/gae_cv_seizures.csv (model_cmp_core.gate_GG)
  GG-mc  the GAE rows = the committed results/model_cmp rows (per_subject both points and stages, curves, seizures,
         window AUROC)
  G-IF   the Isolation Forest rows = the committed results/model_cmp rows (the same tables; k per fold within 1e-6 rel)
  G-km   every channel of every case has a valid number of clusters and both K-means arms cover the 24 cases
The record code (model_cmp_core.py, model_cmp_run.py) is imported unchanged from the clone at the pinned commit;
this file is embedded in the notebook with its sha256 checked (plan §0 notebook rule, board R205; single process,
no pool workers).

Outputs (OUT, default /kaggle/working/fa16): per_subject.csv, curves.csv, auroc.csv, seizures.csv (gae, if, km, km_u),
km_k.csv (one row per case x channel: chosen k, silhouette by k, IQR-0 features, smallest cluster share, small
clusters, seconds; diag_* = the small-cluster diagnostic),
gates.json, jobs.json, projection.json, run_meta.json. Nothing here is a result before src/fa16_aggregate.py.
"""
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

K_RANGE = tuple(range(2, 11))
N_SIL = 5000
SEED = 42
N_INIT = 10
CODE_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:16]
OUT = Path(os.environ.get("FA16_OUT", "/kaggle/working/fa16"))
T0 = time.time()


# ============================================================================ the K-means arm (pure functions)
def large_clusters(size, alpha=0.9, beta=5.0):
    """boolean per cluster: True = large (CBLOF, He et al. 2003), operationalised as PyOD's CBLOF
    _set_small_large_clusters: clusters sorted by size (descending, stable); alpha boundaries i (1 <= i < k) where the
    i largest hold >= alpha * n windows, beta boundaries i where size(i-th) / size(i+1-th) >= beta; the boundary is the
    first i in both lists, else the first alpha one, else the first beta one; none -> every cluster large (PyOD
    raises here; we keep the plain score). Returns (large, rule)."""
    size = np.asarray(size, dtype=np.float64)
    k, n = len(size), size.sum()
    order = np.argsort(-size, kind="stable")
    al, be = [], []
    for i in range(1, k):
        if size[order[:i]].sum() >= n * alpha:
            al.append(i)
        if size[order[i]] > 0 and size[order[i - 1]] / size[order[i]] >= beta:
            be.append(i)
    both = sorted(set(al) & set(be))
    if both:
        b, rule = both[0], "alpha+beta"
    elif al:
        b, rule = al[0], "alpha"
    elif be:
        b, rule = be[0], "beta"
    else:
        return np.ones(k, bool), "none"
    large = np.zeros(k, bool)
    large[order[:b]] = True
    return large, rule


def km_channel(X, n_sil=None):
    """X (n, 30) node input of one channel. Returns (D, Du, small, info): D = distance to the nearest centroid after
    robust scaling (arm km), Du = u-CBLOF score of the same fit (arm km_u), small = window in a small cluster; k chosen
    by the largest mean silhouette on a seeded sample (ties -> smaller k)."""
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import RobustScaler
    n_sil = N_SIL if n_sil is None else n_sil
    t0 = time.time()
    X = np.asarray(X, dtype=np.float64)
    if not np.isfinite(X).all():
        raise SystemExit("STOP G-km: non-finite node input")
    q25, q75 = np.percentile(X, [25, 75], axis=0)
    iqr0 = int((q75 - q25 == 0).sum())
    Xs = RobustScaler().fit_transform(X)
    n = len(Xs)
    sub = np.sort(np.random.default_rng(SEED).choice(n, n_sil, replace=False)) if n > n_sil else np.arange(n)
    S = Xs[sub]
    n_distinct = len(np.unique(S, axis=0))
    sil = {}
    for k in K_RANGE:
        if k >= n_distinct:                                  # silhouette needs 2 .. n_samples - 1 labels
            continue
        lab = KMeans(n_clusters=k, n_init=N_INIT, random_state=SEED).fit_predict(S)
        if len(np.unique(lab)) < 2 or len(np.unique(lab)) >= len(S):
            continue
        sil[k] = float(silhouette_score(S, lab))
    if not sil:
        raise SystemExit(f"STOP G-km: no valid number of clusters (distinct sampled windows {n_distinct})")
    best = max(sil.values())
    k = min(kk for kk, v in sil.items() if v == best)
    km = KMeans(n_clusters=k, n_init=N_INIT, random_state=SEED).fit(Xs)
    dist = km.transform(Xs)
    D = dist.min(axis=1)
    lab = dist.argmin(axis=1)
    size = np.bincount(lab, minlength=k)
    large, rule = large_clusters(size)
    small = ~large[lab]
    Du = np.where(small, dist[:, large].min(axis=1), D)
    info = dict(k=int(k), silhouette=best, sil_by_k=json.dumps({str(a): round(b, 6) for a, b in sil.items()}),
                n_windows=int(n), n_sample=int(len(S)), iqr0_features=iqr0, min_cluster_share=float(size.min() / n),
                small_clusters=int((~large).sum()), small_rule=rule, share_small=float(small.mean()),
                n_iter=int(km.n_iter_), seconds=round(time.time() - t0, 2))
    return D.astype(np.float64), Du.astype(np.float64), small, info


def km_from_X(X, n_sil=None):
    """X (n, 18, 30) -> D, Du (n, 18), small (n, 18) and one info row per channel."""
    D = np.empty((X.shape[0], X.shape[1]), np.float64)
    Du = np.empty_like(D)
    small = np.zeros(D.shape, bool)
    infos = []
    for c in range(X.shape[1]):
        D[:, c], Du[:, c], small[:, c], inf = km_channel(X[:, c, :], n_sil)
        infos.append(dict(channel=c, **inf))
    return D, Du, small, infos


def diag_rows(s, ctx, small, infos):
    """the small-cluster diagnostic, computed after scoring (labels never enter an arm)."""
    ict = ctx["ict"][ctx["idx"]].astype(bool)
    return [dict(subject=s, **i, diag_ictal_windows=int(ict.sum()),
                 diag_ictal_share_small=float(small[ict, c].mean()) if ict.any() else np.nan,
                 diag_nonictal_share_small=float(small[~ict, c].mean())) for c, i in enumerate(infos)]


# ============================================================================ run (Kaggle)
def _json(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, indent=1, default=str))


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def compare_rows(model, mine_dir, ref_dir, k_rel=1e-6):
    """the rows of `model` written by this run (mine_dir) against the committed results/model_cmp rows (ref_dir):
    per_subject (both points and stages; tp / fp exactly, k of the own rows within k_rel), curves (tp / fp exactly),
    seizures (caught exactly), auroc (within 1e-9). Returns a gate record."""
    bad = []
    keys = dict(per_subject=["subject", "point", "stage"], curves=["subject", "top"],
                seizures=["subject", "file", "onset_s"], auroc=["subject"])
    n = {}
    for t, kk in keys.items():
        a = pd.read_csv(Path(mine_dir) / f"{t}.csv")
        b = pd.read_csv(Path(ref_dir) / f"{t}.csv")
        a, b = a[a.model == model], b[b.model == model]
        m = a.merge(b, on=kk, suffixes=("", "_ref"))
        n[t] = (len(a), len(b), len(m))
        if not (len(a) == len(b) == len(m)) or len(a) == 0:
            bad.append((t, "rows", len(a), len(b), len(m)))
            continue
        if t in ("per_subject", "curves"):
            d = m[(m.tp != m.tp_ref) | (m.fp != m.fp_ref)]
            bad += [(t, *[getattr(r, x) for x in kk], (int(r.tp), int(r.fp)), (int(r.tp_ref), int(r.fp_ref)))
                    for r in d.head(20).itertuples()]
        if t == "per_subject":
            o = m[m.point == "own"]
            rel = (o.k - o.k_ref).abs() / o.k_ref.abs()
            if not (rel <= k_rel).all():
                bad.append((t, "k", float(rel.max())))
        if t == "seizures":
            d = m[m.caught != m.caught_ref]
            if len(d):
                bad.append((t, "caught differs", len(d)))
        if t == "auroc":
            d = (m.auroc - m.auroc_ref).abs()
            if not (d.fillna(0) <= 1e-9).all() or (m.auroc.isna() != m.auroc_ref.isna()).any():
                bad.append((t, "auroc", float(d.max())))
    return dict(status="PASS" if not bad else "FAIL", rows=str(n), mismatches=str(bad))


def main(notebook, repo_commit, input_root="/kaggle/input", folds=(1, 2, 3, 4), smoke_case=None):
    import model_cmp_core as C
    import model_cmp_run as R
    R.OUT = OUT                                               # every model_cmp_run writer goes to this run's folder
    OUT.mkdir(parents=True, exist_ok=True)
    import sklearn
    meta = dict(notebook=notebook, repo_commit=repo_commit, code_sha=CODE_SHA,
                model_cmp_core_sha=sha16(C.__file__), model_cmp_run_sha=sha16(R.__file__),
                versions=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
                              sklearn=sklearn.__version__), cpu_count=os.cpu_count(),
                rule=dict(k_range=list(K_RANGE), n_sil=N_SIL, seed=SEED, n_init=N_INIT, scaler="RobustScaler",
                          distance="euclidean to nearest centroid"),
                started=time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    try:
        import torch
        meta["versions"]["torch"] = torch.__version__
    except Exception:                                         # noqa: BLE001
        pass
    _json("run_meta.json", meta)
    ref = C.REPO / "results" / "model_cmp"

    def finish(err=None):
        meta.update(runtime_h=round((time.time() - T0) / 3600, 3), finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    stopped=err)
        _json("run_meta.json", meta)

    def stop(msg):
        finish(msg)
        raise SystemExit(msg)

    R.setup(input_root)                                       # D0 (STOPs inside on wrong data)
    ok, _ = R.mini_gate()
    if not ok:
        stop("STOP G-mini: the GAE fold-1 chb12 row does not reproduce the committed CV")
    # smoke: the K-means arm on one case, measured; projection for the 24 cases (information, not a stop)
    s0 = smoke_case or C.MAN["1"]["held_out_cases"][0]
    t = time.time()
    ctx = C.make_ctx(s0)
    X, *_ = C.node_input(ctx["z"], ctx["idx"], C.fold_meta(1), clip=False)
    D0_, Du0, sm0, inf0 = km_from_X(X)
    sec = time.time() - t
    if not (np.isfinite(D0_).all() and np.isfinite(Du0).all()):
        stop(f"STOP smoke: non-finite K-means distance on {s0}")
    n_all = sum(len(C.make_ctx(s)["idx"]) for s in C.ALL)
    proj_h = sec / 3600 * (0.5 * len(C.ALL) + 0.5 * n_all / len(ctx["idx"]))   # half fixed (selection), half ~ n
    _json("projection.json", dict(case=s0, windows=int(len(ctx["idx"])), seconds=round(sec, 1),
                                  windows_all=int(n_all), projected_km_h=round(proj_h, 3),
                                  k_chosen=[i["k"] for i in inf0]))
    C.log(f"[km] smoke {s0}: {len(ctx['idx'])} windows, 18 channels in {sec:.0f}s, k = {[i['k'] for i in inf0]}; "
          f"projected K-means arm {proj_h:.2f} h (computed)")
    # the record arms first: GAE (GG inside), then the committed-row gates
    R.unsupervised(("gae", "if"))                             # STOPs on GG
    for model, name in (("gae", "GG-mc"), ("if", "G-IF")):
        g = dict(gate=name, model=model, **compare_rows(model, OUT, ref))
        R.gate(g)
        C.log(f"{name} {g['status']}: {model} rows vs results/model_cmp {g['rows']} {g['mismatches']}")
        if g["status"] != "PASS":
            stop(f"STOP {name}: the {model} rows do not reproduce results/model_cmp -- see gates.json")
    # the K-means arms (fold-independent per case; one fit gives km and km_u; km_k.csv written per case as it ends)
    cache = {s0: (D0_, Du0)}                                  # the smoke case (deterministic: same fit)
    R._append(diag_rows(s0, ctx, sm0, inf0), "km_k.csv")

    def fit(c):
        s = c["s"]
        if s not in cache:
            X, *_ = C.node_input(c["z"], c["idx"], C.fold_meta(1), clip=False)
            D, Du, small, infos = km_from_X(X)
            R._append(diag_rows(s, c, small, infos), "km_k.csv")
            cache[s] = (D, Du)
        return cache[s]

    for model, j in (("km", 0), ("km_u", 1)):
        for f in folds:
            r = R._job(model, f, lambda f=f, model=model, j=j: C.run_fold(model, f, lambda c: fit(c)[j], "D"))
            if r is None:
                continue
            p, c, a, s, k = r
            R._append(p, "per_subject.csv"); R._append(c, "curves.csv"); R._append(a, "auroc.csv")
            R._append(s, "seizures.csv")
    kk = pd.read_csv(OUT / "km_k.csv")
    pk = pd.read_csv(OUT / "per_subject.csv")
    cov = {m: int(pk[pk.model == m].subject.nunique()) for m in ("km", "km_u")}
    ok = kk.subject.nunique() == len(C.ALL) and len(kk) == 18 * len(C.ALL) and all(v == len(C.ALL) for v in cov.values())
    g = dict(gate="G-km", status="PASS" if ok else "FAIL", cases=int(kk.subject.nunique()), rows=int(len(kk)),
             arm_cases=cov, k_counts=kk.k.value_counts().sort_index().to_dict(),
             small_rule_counts=kk.small_rule.value_counts().to_dict())
    R.gate(g)
    R.summary()
    finish(None if g["status"] == "PASS" else "G-km FAIL")
    C.log(f"done in {(time.time() - T0) / 3600:.2f} h; G-km {g['status']}")
    if g["status"] != "PASS":
        raise SystemExit("STOP G-km: not every case x channel has a K-means fit or an arm misses cases")


if __name__ == "__main__":
    sys.exit(main(os.environ.get("FA16_NOTEBOOK", "local"), os.environ.get("FA16_COMMIT", "local"),
                  os.environ.get("FA16_INPUT", "/kaggle/input")))
