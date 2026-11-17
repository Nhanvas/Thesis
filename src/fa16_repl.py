#!/usr/bin/env python
"""
fa16_repl.py -- F-A1.6 replication: the K-means baseline over the five random patient partitions of the defense-time F1
record (author 17/11 07:40, option 2: "is the K-means advantage stable over partitions?"; plan §12 17/11 08:10, chat
D30-F). Partition 0 = the run FA16_KMEANS (results/fa16/run, every gate PASS); partitions 1-5 = results/f1_repcv/
partitions.json, the folds of the F1 record (GAE and MLP-AE trained per partition, seed = partition; record rows in
results/f1_repcv/raw/p{r}/).

The K-means arms are label-free and fold-independent (src/fa16_kmeans.py: per patient and channel, robust scaling,
k by silhouette, KMeans seed 42 on every valid window of the patient), so their distances are the same in every
partition: they are fitted once per case. What changes with the partition is the fold assignment and the k of the
alarm budget, calibrated on each fold's own training cases (f1_core.run_fold, the partition-aware chain of the F1
record, unchanged).

Order (every gate STOPs; nothing of the K-means arms is read before the gates):
  D0      data identity (model_cmp_run.setup -> model_cmp_core.gate_D0)
  G-parts partitions.json sha16 = the F1 record's partitions_sha; partition 0's folds = results/v9_x3/folds.json's
  G-base  the committed F1 GAE fold checkpoints of partitions 1-5 (results/f1_repcv/raw/p{r}/jobs/gae_fold{f}/), scored
          by f1_core.encode_D + f1_core.run_fold, reproduce the F1 record rows exactly: per_subject (both points and
          stages: tp, fp, n_ref; own-point k within 1e-6 relative), curves (tp, fp), seizures (caught), auroc (1e-9);
          R3.0 / FA14 reproduced these rows exactly on Kaggle CPU
  G-kmD   the K-means fits of the 24 cases (fa16_kmeans.km_from_X, unchanged) = FA16_KMEANS's km_k.csv in every column
          but the timing (k, silhouettes, windows, IQR-0 features, cluster shares, small clusters, diagnostic): same fits
  G-km0   partition 0 through f1_core.run_fold with these distances = FA16_KMEANS's km and km_u rows (the same tables,
          tolerances of G-base): the partition-aware chain equals the model comparison's chain for the K-means arms
Then km and km_u for partitions 1-5 (20 folds each), written per partition as it ends.

Outputs (OUT, default /kaggle/working/fa16_repl): per_subject.csv, curves.csv, auroc.csv, seizures.csv (gae = the
regenerated record rows of p1-5; km, km_u of p0-p5; column partition), km_k.csv, gates.json, jobs.json, run_meta.json.
Read by src/fa16_repl_aggregate.py (committed before the run). One process, no pool workers.
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

CODE_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:16]
OUT = Path(os.environ.get("FA16R_OUT", "/kaggle/working/fa16_repl"))
PARTS = (1, 2, 3, 4, 5)
T0 = time.time()
KEYS = dict(per_subject=["fold", "subject", "point", "stage"], curves=["subject", "top"],
            seizures=["subject", "file", "onset_s"], auroc=["subject"])
KM_COLS = ["subject", "channel", "k", "silhouette", "sil_by_k", "n_windows", "n_sample", "iqr0_features",
           "min_cluster_share", "small_clusters", "small_rule", "share_small", "n_iter", "diag_ictal_windows",
           "diag_ictal_share_small", "diag_nonictal_share_small"]


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def _json(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, indent=1, default=str))


def _append(rows, name):
    if not len(rows):
        return
    df = pd.DataFrame(rows)
    p = OUT / name
    df.to_csv(p, mode="a", header=not p.exists(), index=False)


def compare(mine, ref, k_rel=1e-6):
    """mine / ref: {table: DataFrame} of ONE model and ONE partition. tp / fp exact, k of the own rows within k_rel,
    caught exact, auroc within 1e-9; same row sets. Returns (status, detail)."""
    bad, n = [], {}
    for t, kk in KEYS.items():
        a, b = mine[t].reset_index(drop=True), ref[t].reset_index(drop=True)
        if t != "per_subject":
            kk = [c for c in kk if c in a.columns and c in b.columns]
        m = a.merge(b, on=kk, suffixes=("", "_ref"))
        n[t] = (len(a), len(b), len(m))
        if not (len(a) == len(b) == len(m)) or len(a) == 0:
            bad.append((t, "rows", len(a), len(b), len(m)))
            continue
        if t in ("per_subject", "curves"):
            d = m[(m.tp != m.tp_ref) | (m.fp != m.fp_ref)]
            if t == "per_subject":
                d = pd.concat([d, m[m.n_ref != m.n_ref_ref]])
            bad += [(t, *[getattr(r, x) for x in kk], (int(r.tp), int(r.fp)), (int(r.tp_ref), int(r.fp_ref)))
                    for r in d.head(10).itertuples()]
        if t == "per_subject":
            o = m[m.point == "own"]
            rel = (o.k - o.k_ref).abs() / o.k_ref.abs()
            if not (rel <= k_rel).all():
                bad.append((t, "k", float(rel.max())))
        if t == "seizures" and (m.caught != m.caught_ref).any():
            bad.append((t, "caught differs", int((m.caught != m.caught_ref).sum())))
        if t == "auroc":
            d = (m.auroc - m.auroc_ref).abs()
            if not (d.fillna(0) <= 1e-9).all() or (m.auroc.isna() != m.auroc_ref.isna()).any():
                bad.append((t, "auroc", float(d.max())))
    return ("PASS" if not bad else "FAIL"), dict(rows=str(n), mismatches=str(bad))


def tables(P, Cc, A, S):
    return dict(per_subject=pd.DataFrame(P), curves=pd.DataFrame(Cc), auroc=pd.DataFrame(A), seizures=pd.DataFrame(S))


def record_tables(d, model, p=None):
    out = {}
    for t in KEYS:
        x = pd.read_csv(Path(d) / f"{t}.csv")
        x = x[x.model == model]
        if p is not None and "partition" in x.columns:
            x = x[x.partition == p]
        out[t] = x
    return out


def main(notebook, repo_commit, input_root="/kaggle/input", parts=PARTS):
    import f1_core as F
    import fa16_kmeans as K
    import model_cmp_core as C
    import model_cmp_run as R
    import sklearn
    import torch
    R.OUT = OUT
    OUT.mkdir(parents=True, exist_ok=True)
    fa16_run = C.REPO / "results" / "fa16" / "run" / "fa16"
    f1raw = C.REPO / "results" / "f1_repcv" / "raw"
    meta = dict(notebook=notebook, repo_commit=repo_commit, code_sha=CODE_SHA, parts=list(parts),
                shas={n: sha16(m.__file__) for n, m in (("fa16_kmeans", K), ("f1_core", F), ("model_cmp_core", C),
                                                         ("model_cmp_run", R))},
                versions=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
                              sklearn=sklearn.__version__, torch=torch.__version__), cpu_count=os.cpu_count(),
                started=time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    ref_meta = json.loads((fa16_run / "run_meta.json").read_text())
    meta["versions_equal_fa16"] = all(meta["versions"].get(k) == v for k, v in ref_meta["versions"].items())
    _json("run_meta.json", meta)
    jobs = []

    def finish(err=None):
        meta.update(runtime_h=round((time.time() - T0) / 3600, 3), finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    stopped=err)
        _json("run_meta.json", meta)
        _json("jobs.json", jobs)

    def gate(g):
        R.gate(g)
        C.log(f"{g['gate']} {g['status']}: {({k: v for k, v in g.items() if k not in ('gate', 'status')})}")
        if g["status"] != "PASS":
            finish(f"STOP {g['gate']}")
            raise SystemExit(f"STOP {g['gate']}: see gates.json")

    # D0
    R.setup(input_root)
    # G-parts
    want = None
    for fj in f1raw.glob("p*/jobs/*/fit.json"):
        want = json.loads(fj.read_text())["partitions_sha"]
        break
    got = sha16(F.PARTITIONS)
    m0 = F.manifest(0)
    p0ok = all(sorted(m0[f]["held_out_cases"]) == sorted(C.MAN[str(f)]["held_out_cases"]) for f in C.FOLDS)
    gate(dict(gate="G-parts", status="PASS" if (got == want and p0ok) else "FAIL", partitions_sha=got,
              record_sha=want, partition0_folds_equal=p0ok))
    # G-base: the F1 GAE checkpoints of partitions 1-5 reproduce the record rows
    import torch as _t
    for p in parts:
        t0 = time.time()
        P_, C_, A_, S_, ks = [], [], [], [], {}
        for f in F.manifest(p):
            jd = f1raw / f"p{p}" / "jobs" / f"gae_fold{f}"
            pt = jd / f"gae_p{p}_fold{f}_seed{F.seed_of(p)}.pt"
            if not pt.exists():
                gate(dict(gate="G-base", status="FAIL", partition=p, missing=str(pt)))
            mdl = F.build("gae")
            mdl.load_state_dict(_t.load(str(pt), map_location="cpu"), strict=True)
            mdl.eval()
            mt = json.loads(pt.with_suffix(".json").read_text())
            a, b, c, d, k, sec = F.run_fold("gae", p, f, F.manifest(p)[f],
                                             lambda ctx, mdl=mdl, mt=mt: F.encode_D("gae", mdl, mt, ctx))
            P_ += a; C_ += b; A_ += c; S_ += d; ks[f] = k
            jobs.append(dict(model="gae", partition=p, fold=f, status="done", seconds=round(sec), k=k,
                             checkpoint_sha256=hashlib.sha256(pt.read_bytes()).hexdigest()))
        mine = tables(P_, C_, A_, S_)
        st, det = compare(mine, record_tables(f1raw / f"p{p}", "gae", p))
        for t, df in mine.items():
            _append(df.to_dict("records"), f"{t}.csv")
        _json("jobs.json", jobs)
        gate(dict(gate="G-base", status=st, partition=p, seconds=round(time.time() - t0), **det))
    # K-means fits (once per case) + G-kmD
    cache, krows = {}, []
    t0 = time.time()
    for s in C.ALL:
        ctx = C.make_ctx(s)
        X, *_ = C.node_input(ctx["z"], ctx["idx"], C.fold_meta(1), clip=False)
        D, Du, small, infos = K.km_from_X(X)
        cache[s] = (D, Du)
        rows = K.diag_rows(s, ctx, small, infos)
        krows += rows
        _append(rows, "km_k.csv")
        C.log(f"[km] {s}: {len(ctx['idx'])} windows, k = {[i['k'] for i in infos]} ({time.time() - t0:.0f}s)")
    jobs.append(dict(model="km_fit", partition=-1, fold=0, status="done", seconds=round(time.time() - t0)))

    b = pd.read_csv(fa16_run / "km_k.csv")[KM_COLS].sort_values(["subject", "channel"]).reset_index(drop=True)
    a2 = pd.read_csv(OUT / "km_k.csv")[KM_COLS].sort_values(["subject", "channel"]).reset_index(drop=True)
    try:
        pd.testing.assert_frame_equal(a2, b, check_exact=True, check_dtype=False)
        st, det = "PASS", "every column equal (24 x 18 rows)"
    except AssertionError as e:
        st, det = "FAIL", str(e)[:1500]
    gate(dict(gate="G-kmD", status=st, rows=len(a2), detail=det))
    # G-km0: partition 0 through the partition-aware chain = FA16_KMEANS's rows
    for model, j in (("km", 0), ("km_u", 1)):
        P_, C_, A_, S_ = [], [], [], []
        for f in F.manifest(0):
            a_, b_, c_, d_, k, sec = F.run_fold(model, 0, f, F.manifest(0)[f], lambda ctx, j=j: cache[ctx["s"]][j])
            P_ += a_; C_ += b_; A_ += c_; S_ += d_
            jobs.append(dict(model=model, partition=0, fold=f, status="done", seconds=round(sec), k=k))
        mine = tables(P_, C_, A_, S_)
        ref = record_tables(fa16_run, model)

        st, det = compare(mine, ref)
        for t, df in mine.items():
            _append(df.to_dict("records"), f"{t}.csv")
        gate(dict(gate="G-km0", status=st, model=model, **det))
    # the K-means arms on partitions 1-5
    for p in parts:
        for model, j in (("km", 0), ("km_u", 1)):
            for f in F.manifest(p):
                a_, b_, c_, d_, k, sec = F.run_fold(model, p, f, F.manifest(p)[f], lambda ctx, j=j: cache[ctx["s"]][j])
                for t, rows in (("per_subject", a_), ("curves", b_), ("auroc", c_), ("seizures", d_)):
                    _append(rows, f"{t}.csv")
                jobs.append(dict(model=model, partition=p, fold=f, status="done", seconds=round(sec), k=k))
        _json("jobs.json", jobs)
        C.log(f"partition {p} done ({(time.time() - T0) / 3600:.2f} h)")
    per = pd.read_csv(OUT / "per_subject.csv")
    cov = {f"{m}_p{p}": int(per[(per.model == m) & (per.partition == p)].subject.nunique())
           for m in ("km", "km_u") for p in (0, *parts)}
    gate(dict(gate="G-done", status="PASS" if all(v == len(C.ALL) for v in cov.values()) else "FAIL", coverage=cov))
    finish(None)
    C.log(f"done in {(time.time() - T0) / 3600:.2f} h")


if __name__ == "__main__":
    sys.exit(main(os.environ.get("FA16R_NOTEBOOK", "local"), os.environ.get("FA16R_COMMIT", "local"),
                  os.environ.get("FA16R_INPUT", "/kaggle/input")))
