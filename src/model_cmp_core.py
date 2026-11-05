#!/usr/bin/env python
"""
model_cmp_core.py -- model comparison, rev 2 (docs/MODEL_COMPARISON_PLAN.md rev 2, author 03/11 00:39).

Where does the GAE stand among single models of other families? Five rows, one per family, on the 4-fold
patient-wise CV already used for the GAE (results/v9_x3/folds.json: deterministic rule, committed before any
training; 24 CHB-MIT cases, chb01 + chb21 = one subject, always in the same fold):
  gae   graph autoencoder, label-free  -- the thesis GAE per fold (results/v9_x3/models/fold{k}, 200 epochs,
        committed checkpoints; NOT retrained)
  if    Isolation Forest, label-free   -- per patient, per channel, on the node input (classical anomaly detection)
  svm   linear SVM, supervised         -- trained on the other 3 folds' patients (labels)
  hgb   gradient-boosted trees, supervised
  cnn   1-D CNN, supervised            -- convolution across the 18 montage channels of one window
Every model sees the same 4 s window: 18 channels x the GAE's 30-d node input (adjacency row / max 18, band
powers per-window min-max 5, f7 standardised with the fold's own training constants, clipped +-4, mapped to
[0, 1] 7). Everything downstream is the frozen chain, imported read-only from the repository at a pinned commit:
percentile scalar -> smoothing 5 -> per-patient budget clip(q_i(k), 0.005, 0.02), k calibrated per fold on that
fold's TRAINING cases by p3_levers.calibrate (median q_i = 0.005, label-free) -> merge 90 s -> kernel CPD ->
SzCORE (v9_e1_baselines.evaluate_arm, the call that produced results/v9_x3).
  label-free models: per-channel distance D -> e17b members (6/9/12 + mean, +-15 min drift) -> percentile mean
  (x) and robust-z member mean (m, budget) -- v9_e1_baselines.final_scalar_from_D / member_mean_z_from_D.
  supervised models: P(seizure) per window -> percentile (x); the probability itself is the budget signal (m)
  (one scale for every patient; a robust z of mostly-zero probabilities is degenerate).
No early stopping anywhere: CNN 30 epochs (last epoch kept), trees 200 iterations, SVM to convergence.

Outputs per model and fold (held-out cases): tp/fp at the own label-free point and at the fixed 0.005 point
(detector and localized), the detector-stage curve over v9_e1_baselines.GRID, window AUROC, and per-seizure
caught/missed with the record's overlap rule (onset - 30 s, offset + 60 s; v9_final_hard._runs_caught), keyed
(subject, file, onset_s) so it joins results/v9_v1/part1_descriptors.csv (amplitude ratio, duration).

Gates: D0 data identity (n_ref and non-ictal hours of all 24 cases = results/v9_x3/fold*_seed42_per_subject.csv;
clean training-window counts = each fold model's json); GG the GAE row reproduces results/v9_x3 exactly (k per
fold within 1e-6 relative, tp/fp per case and stage exactly) and results/v9_final/hard/gae_cv_seizures.csv (185 seizures).
"""
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(os.environ.get("THESIS_REPO", Path(__file__).resolve().parents[1]))
for _p in ("src", "src/retrain", "src/phaseB", "src/phaseC", "src/dataprep"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import p2_scalars as PS                  # noqa: E402
import p3_levers as P3L                  # noqa: E402
import v9_e1_baselines as V9E1           # noqa: E402

X3 = REPO / "results" / "v9_x3"
MAN = json.loads((X3 / "fold_manifests.json").read_text())
FOLDS = [1, 2, 3, 4]
ALL = sorted({c for f in FOLDS for c in MAN[str(f)]["held_out_cases"]})          # 24 cases
FOLD_OF = {c: f for f in FOLDS for c in MAN[str(f)]["held_out_cases"]}
FLOOR, CAP, SMOOTH, WIN = 0.005, 0.02, 5, 4
PRE, POST = 30, 60
GRID = list(V9E1.GRID)
N_CH, IN_DIM = 18, 30
MODELS = ["gae", "if", "svm", "hgb", "cnn"]
SUPERVISED = ["svm", "hgb", "cnn"]
CNN_EPOCHS, CNN_BATCH, CNN_LR = 30, 256, 1e-3


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ============================================================================ data
_NPZ, _CACHE = {}, {}


def locate_all(input_root="/kaggle/input"):
    hits = {}
    for p in sorted(Path(input_root).rglob("chb*.npz")):
        if p.stem in ALL:
            hits.setdefault(p.stem, []).append(p)
    missing = [s for s in ALL if s not in hits]
    if missing:
        raise SystemExit(f"STOP D0: no .npz under {input_root} for {missing}")
    for s, ps in hits.items():
        if len({q.stat().st_size for q in ps}) != 1:
            raise SystemExit(f"STOP D0: copies of {s} differ in size: {[str(q) for q in ps]}")
        _NPZ[s] = ps[0]
    log(f"D0: found all {len(ALL)} cases")


def npz(s):
    return np.load(_NPZ[s], allow_pickle=True)


def make_ctx(s):
    """window bookkeeping, same fields as v9_x3_cv_eval.case_ctx (idx = every non-signal-loss window)."""
    if s in _CACHE:
        return _CACHE[s]
    z = npz(s)
    ok = ~z["is_signal_loss"].astype(bool)
    idx = np.flatnonzero(ok)
    ict = z["is_ictal"].astype(bool)
    fidx = z["file_idx"].astype(int)
    fl5 = z["is_flag5sd"].astype(bool) if "is_flag5sd" in z.files else np.zeros(len(ict), bool)
    ctx = dict(s=s, z=z, idx=idx, n=len(ict), ok=ok, fidx=fidx, wf=fidx[idx], ict=ict, ict_ok=ict & ok, fl5=fl5,
               nonict=~ict & ~z["is_buffer"].astype(bool) & ok, nh=float((~ict & ok).sum()) * WIN / 3600,
               files=[str(f) for f in z["files"]] if "files" in z.files else None)
    _CACHE[s] = ctx
    return ctx


def clean_mask(z):
    return ~z["is_ictal"] & ~z["is_buffer"] & ~z["is_signal_loss"] & ~z["is_flag5sd"]


def fold_meta(f):
    return json.loads((X3 / "models" / f"fold{f}" / f"gae_fold{f}_seed42.json").read_text())


def node_input(z, idx, meta, clip=True):
    """(n, 18, 30) node input of the GAE for the given windows, the fold model's own f7 constants; dump
    convention for non-finite values (v9_x3_cv_eval.dump_D). clip=False keeps f7 standardised but unclipped
    (an affine map of raw f7: the input of the per-patient Isolation Forest, which is affine-invariant)."""
    adj = z["adj"][idx].astype(np.float32)
    adj[~np.isfinite(adj).all(axis=(1, 2))] = 0.0
    bp5 = z["bp5"][idx].astype(np.float32)
    bp5[~np.isfinite(bp5)] = 0.0
    f7 = z["f7"][idx].astype(np.float64)
    An = adj / (adj.max(axis=(1, 2), keepdims=True) + 1e-8)
    mn, mx = bp5.min(axis=1, keepdims=True), bp5.max(axis=1, keepdims=True)
    xn = (bp5 - mn) / (mx - mn + 1e-8)
    mu, sd, c = np.array(meta["add_mean"]), np.array(meta["add_std"]), meta["clip"]
    fz = (f7 - mu) / sd
    fa = (np.clip(fz, -c, c) + c) / (2 * c) if clip else fz
    X = np.concatenate([An, xn, fa.astype(np.float32)], axis=2).astype(np.float32)
    return np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0), adj, xn.astype(np.float32), fa.astype(np.float32)


def gate_D0():
    bad = []
    ref = pd.concat([pd.read_csv(X3 / f"fold{f}_seed42_per_subject.csv") for f in FOLDS])
    ref = ref[ref.stage == "localized"]
    for s in ALL:
        tp, fp, nr, h = PS.score(make_ctx(s), {})
        r = ref[ref.subject == s].iloc[0]
        if nr != int(r.n_ref) or abs(h - float(r.nonict_h)) > 1e-6:
            bad.append((s, (nr, h), (int(r.n_ref), float(r.nonict_h))))
    for f in FOLDS:
        for s, n in fold_meta(f)["n_train"].items():
            if int(clean_mask(npz(s)).sum()) != int(n):
                bad.append((f"fold{f}", s, "clean windows", int(clean_mask(npz(s)).sum()), n))
    if bad:
        raise SystemExit(f"STOP D0 (data identity): {bad}")
    log("D0 PASS: n_ref and non-ictal hours of 24 cases = results/v9_x3; clean training-window counts = fold models")
    return dict(gate="D0", status="PASS")


# ============================================================================ scores per model
def d_from_Z(Z):
    from sklearn.covariance import LedoitWolf
    D = np.empty((Z.shape[0], Z.shape[1]), np.float32)
    for c in range(Z.shape[1]):
        Zc = Z[:, c, :].astype(np.float64)
        D[:, c] = LedoitWolf().fit(Zc).mahalanobis(Zc)
    return D.astype(np.float64)


_GAE = {}


def gae_model(f):
    import torch
    import gae_joint as G
    if f not in _GAE:
        meta = fold_meta(f)
        m = G.GAEModel(in_dim=meta["in_dim"], bands=meta["out_x"])
        m.load_state_dict(torch.load(str(X3 / "models" / f"fold{f}" / f"gae_fold{f}_seed42.pt"),
                                     map_location="cpu"), strict=True)
        _GAE[f] = (m.eval(), meta)
    return _GAE[f]


def gae_D(f, ctx, chunk=2048):
    """node latent of the fold's GAE on every valid window, vectorised batching (edges = nonzero(A_batch) +
    18*b == dense_to_sparse per window + Batch.from_data_list), CPU; then the per-channel LedoitWolf D."""
    import torch
    model, meta = gae_model(f)
    _, adj, xn, fa = node_input(ctx["z"], ctx["idx"], meta)
    Z = np.empty((len(adj), N_CH, 16), np.float32)
    with torch.no_grad():
        for s in range(0, len(adj), chunk):
            A = torch.tensor(adj[s:s + chunk]); B = A.shape[0]
            An = A / (A.amax(dim=(1, 2), keepdim=True) + 1e-8)
            x = torch.cat([An, torch.tensor(xn[s:s + chunk]), torch.tensor(fa[s:s + chunk])], 2).reshape(B * N_CH, -1)
            b, i, j = A.nonzero(as_tuple=True)
            ei = torch.stack([b * N_CH + i, b * N_CH + j])
            Z[s:s + chunk] = model.encoder(x, ei, A[b, i, j]).view(B, N_CH, 16).numpy()
    return d_from_Z(Z)


def if_D(ctx, seed=42):
    """per patient, per channel IsolationForest (200 trees, 256 samples, as V9-E1 B3) on the node input with
    unclipped standardised f7 -- fold-independent (affine-invariant), label-free; D = -score_samples."""
    from sklearn.ensemble import IsolationForest
    X, *_ = node_input(ctx["z"], ctx["idx"], fold_meta(1), clip=False)
    D = np.empty((len(X), N_CH), np.float64)
    for c in range(N_CH):
        m = IsolationForest(n_estimators=200, max_samples=256, random_state=seed).fit(X[:, c, :])
        D[:, c] = -m.score_samples(X[:, c, :])
    return D


def sup_train(f, kind, out_dir=None, smoke=False):
    """supervised model of fold f, trained on the fold's training cases' windows (signal loss and 4 h post-ictal
    buffer excluded), class-weighted, one fixed configuration, no early stopping. Returns (predict_fn, meta)."""
    meta = fold_meta(f)
    Xs, ys = [], []
    for s in MAN[str(f)]["train_cases"]:
        z = npz(s)
        idx = np.flatnonzero(~z["is_signal_loss"].astype(bool) & ~z["is_buffer"].astype(bool))
        X, *_ = node_input(z, idx, meta)
        Xs.append(X); ys.append(z["is_ictal"][idx].astype(np.int8))
    X, y = np.concatenate(Xs), np.concatenate(ys)
    del Xs
    if smoke:
        rng = np.random.default_rng(42)
        sel = np.concatenate([np.flatnonzero(y == 1)[:300], rng.choice(np.flatnonzero(y == 0), 3000, replace=False)])
        X, y = X[sel], y[sel]
    t0 = time.time()
    info = dict(model=kind, fold=f, n_train=int(len(y)), n_ictal=int(y.sum()), smoke=smoke)
    if kind in ("svm", "hgb"):
        import warnings
        from sklearn.exceptions import ConvergenceWarning
        Xf = X.reshape(len(X), -1)
        if kind == "svm":
            from sklearn.pipeline import make_pipeline
            from sklearn.preprocessing import StandardScaler
            from sklearn.svm import LinearSVC
            clf = make_pipeline(StandardScaler(), LinearSVC(C=1.0, class_weight="balanced", dual=False,
                                                            max_iter=10000, random_state=42))
        else:
            from sklearn.ensemble import HistGradientBoostingClassifier
            clf = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1, max_leaf_nodes=31,
                                                 class_weight="balanced", early_stopping=False, random_state=42)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", ConvergenceWarning)
            clf.fit(Xf, y)
        info["converged"] = not any(issubclass(x.category, ConvergenceWarning) for x in w)
        if kind == "svm":
            info["n_iter"] = int(clf[-1].n_iter_)
            pred = lambda Xn: 1.0 / (1.0 + np.exp(-clf.decision_function(Xn.reshape(len(Xn), -1))))  # noqa: E731
        else:
            info["n_iter"] = int(clf.n_iter_)
            pred = lambda Xn: clf.predict_proba(Xn.reshape(len(Xn), -1))[:, 1]  # noqa: E731
        info["fit_s"] = round(time.time() - t0, 1)
        log(f"[{kind}] fold {f}: fitted on {len(y)} windows ({int(y.sum())} ictal) in {info['fit_s']}s, "
            f"iterations {info['n_iter']}, converged {info['converged']}")
        return pred, info, []
    return cnn_train(X, y, info, out_dir, smoke)


def build_cnn():
    import torch
    import torch.nn as nn

    class CNN(nn.Module):
        """input (B, 30, 18): the 30 node features as input channels, convolution across the 18 montage
        channels (code order: 4 bipolar chains of 4 + FZ-CZ, CZ-PZ); global average + max pooling -> logit."""
        def __init__(self):
            super().__init__()
            self.conv = nn.Sequential(nn.Conv1d(IN_DIM, 32, 3, padding=1), nn.ReLU(),
                                      nn.Conv1d(32, 32, 3, padding=1), nn.ReLU())
            self.head = nn.Linear(64, 1)

        def forward(self, x):
            h = self.conv(x)
            return self.head(torch.cat([h.mean(dim=2), h.amax(dim=2)], dim=1)).squeeze(1)
    return CNN()


def cnn_train(X, y, info, out_dir, smoke):
    import torch
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(42); np.random.seed(42)
    torch.backends.cudnn.deterministic = True; torch.backends.cudnn.benchmark = False
    model = build_cnn().to(dev)
    Xt = torch.tensor(X.transpose(0, 2, 1).copy(), device=dev)          # (n, 30, 18)
    yt = torch.tensor(y.astype(np.float32), device=dev)
    pos_w = torch.tensor(float((y == 0).sum()) / max(1.0, float(y.sum())), device=dev)
    lossf = torch.nn.BCEWithLogitsLoss(pos_weight=pos_w)
    epochs = 2 if smoke else CNN_EPOCHS
    opt = torch.optim.Adam(model.parameters(), lr=CNN_LR)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    g = torch.Generator().manual_seed(42)
    rows, t0 = [], time.time()
    for ep in range(epochs):
        model.train(); tot = 0.0
        perm = torch.randperm(len(yt), generator=g).to(dev)
        for i in range(0, len(yt), CNN_BATCH):
            ii = perm[i:i + CNN_BATCH]
            opt.zero_grad(); l = lossf(model(Xt[ii]), yt[ii]); l.backward(); opt.step()
            tot += l.item() * len(ii)
        sched.step()
        rows.append(dict(model="cnn", fold=info["fold"], epoch=ep + 1, train_loss=tot / len(yt),
                         s=round(time.time() - t0, 1)))
        if ep < 2 or (ep + 1) % 5 == 0 or ep == epochs - 1:
            log(f"[cnn] fold {info['fold']} epoch {ep+1}/{epochs} loss {rows[-1]['train_loss']:.5f} ({rows[-1]['s']}s)")
    info.update(epochs=epochs, fit_s=round(time.time() - t0, 1), n_params=sum(p.numel() for p in model.parameters()),
                first_loss=rows[0]["train_loss"], last_loss=rows[-1]["train_loss"],
                G2="PASS" if rows[-1]["train_loss"] < rows[0]["train_loss"] else "FAIL", device=str(dev))
    if out_dir is not None:
        Path(out_dir, "ckpt").mkdir(parents=True, exist_ok=True)
        torch.save(model.state_dict(), Path(out_dir, "ckpt", f"cnn_fold{info['fold']}{'_SMOKE' if smoke else ''}.pt"))
    model.eval()

    def pred(Xn):
        out = []
        with torch.no_grad():
            for s in range(0, len(Xn), 8192):
                xb = torch.tensor(Xn[s:s + 8192].transpose(0, 2, 1).copy(), device=dev)
                out.append(torch.sigmoid(model(xb)).cpu().numpy())
        return np.concatenate(out).astype(np.float64)
    return pred, info, rows


def sup_score(pred, ctx, f):
    X, *_ = node_input(ctx["z"], ctx["idx"], fold_meta(f))
    return pred(X)


# ============================================================================ chain + outputs
def scalars(kind, ctx, v):
    """kind 'D' -> per-channel distance through the frozen members; kind 'P' -> supervised probability."""
    if kind == "D":
        return V9E1.final_scalar_from_D(ctx, v), V9E1.member_mean_z_from_D(ctx, v)
    full = PS._full(ctx, np.asarray(v, dtype=np.float64))
    return PS.pct(full, ctx["ok"]), full


def calibrate(ms):
    return float(P3L.calibrate([PS.smoothed(c, m, SMOOTH) for c, m in ms]))


def seizure_rows(model, ctx, loc):
    rows = []
    for f, rr in P3L.refs_of(ctx).items():
        for a, b in rr:
            hit = any(h1 >= a - PRE and h0 <= b + POST for h0, h1 in loc.get(f, []))
            rows.append(dict(model=model, subject=ctx["s"], fold=FOLD_OF[ctx["s"]],
                             file=ctx["files"][int(f)] if ctx["files"] else int(f), onset_s=int(a),
                             duration_s=int(b - a), caught=bool(hit)))
    return rows


def evaluate_case(model, ctx, x, m, k):
    from sklearn.metrics import roc_auc_score
    per, seiz = [], []
    out, _det, loc = V9E1.evaluate_arm(ctx, x, k, FLOOR, CAP, SMOOTH, m=m)
    for st, v in out.items():
        per.append(dict(model=model, fold=FOLD_OF[ctx["s"]], subject=ctx["s"], point="own", stage=st, k=k, **v))
    seiz += seizure_rows(model, ctx, loc)
    out0, _, _ = V9E1.evaluate_arm(ctx, x, k, FLOOR, CAP, SMOOTH, m=None)
    for st, v in out0.items():
        per.append(dict(model=model, fold=FOLD_OF[ctx["s"]], subject=ctx["s"], point="fixed0.005", stage=st, k=np.nan, **v))
    cur = [dict(model=model, fold=FOLD_OF[ctx["s"]], subject=ctx["s"], **r) for r in V9E1.sweep_detector(ctx, x, GRID)]
    ok = ctx["ok"]; y = ctx["ict"][ok].astype(int)
    au = dict(model=model, fold=FOLD_OF[ctx["s"]], subject=ctx["s"],
              auroc=float(roc_auc_score(y, x[ok])) if 0 < y.sum() < len(y) else np.nan)
    return per, cur, [au], seiz


def run_fold(model, f, score_fn, kind):
    """score_fn(ctx) -> D (kind 'D') or probability (kind 'P'). k from this fold's training cases; held-out
    cases evaluated. Returns per, cur, auroc, seizures, k."""
    t0 = time.time()
    ms = []
    for s in MAN[str(f)]["train_cases"]:
        ctx = make_ctx(s)
        ms.append((ctx, scalars(kind, ctx, score_fn(ctx))[1]))
    k = calibrate(ms)
    del ms
    P, Cc, A, S = [], [], [], []
    for s in MAN[str(f)]["held_out_cases"]:
        ctx = make_ctx(s)
        x, m = scalars(kind, ctx, score_fn(ctx))
        p, c, a, z = evaluate_case(model, ctx, x, m, k)
        P += p; Cc += c; A += a; S += z
    log(f"[{model}] fold {f}: k = {k:.6f}; held-out {MAN[str(f)]['held_out_cases']} scored ({time.time()-t0:.0f}s)")
    return P, Cc, A, S, k


def gate_GG(per, seiz, ks):
    """the GAE row must reproduce results/v9_x3 and results/v9_final/hard/gae_cv_seizures.csv: tp/fp of 48 rows and
    185 caught flags exactly; k per fold within 1e-6 relative (Kaggle numpy 2.1.3 / sklearn 1.6.1 vs the laptop's
    numpy 2.4.4 / sklearn 1.8.0 move the bisection by ~1e-8 relative; first Kaggle run 03/11: 1.4e-8 - 9.3e-8)."""
    bad = []
    for f in FOLDS:
        kr = json.loads((X3 / f"fold{f}_seed42_calibration.json").read_text())["k"]
        if abs(ks[f] - kr) > 1e-6 * abs(kr):      # plan section 9, 03/11 08:00: float tolerance across library versions
            bad.append((f"fold{f} k", ks[f], kr))
    ref = pd.concat([pd.read_csv(X3 / f"fold{f}_seed42_per_subject.csv") for f in FOLDS])
    mine = pd.DataFrame(per)
    mine = mine[mine.point == "own"]
    mg = mine.merge(ref, on=["subject", "stage"], suffixes=("", "_ref"))
    if len(mg) != 48:
        bad.append(("rows", len(mg), 48))
    diff = mg[(mg.tp != mg.tp_ref) | (mg.fp != mg.fp_ref)]
    bad += [(r.subject, r.stage, (int(r.tp), int(r.fp)), (int(r.tp_ref), int(r.fp_ref))) for r in diff.itertuples()]
    sref = pd.read_csv(REPO / "results" / "v9_final" / "hard" / "gae_cv_seizures.csv")
    sm = pd.DataFrame(seiz).merge(sref, on=["subject", "file", "onset_s"], suffixes=("", "_ref"))
    if len(sm) != len(sref) or len(sm) != len(seiz):
        bad.append(("seizure rows", len(sm), len(sref), len(seiz)))
    sbad = sm[sm.caught != sm.caught_ref]
    if len(sbad):
        bad.append(("seizure caught differs", len(sbad)))
    status = "PASS" if not bad else "FAIL"
    log(f"GG {status}: GAE row vs results/v9_x3 (k x4, tp/fp 48 rows) and gae_cv_seizures.csv ({len(sm)} seizures); {bad}")
    return dict(gate="GG", status=status, mismatches=str(bad))


# ============================================================================ MLP autoencoder (plan section 9, 04/11)
MLP_EPOCHS, MLP_BATCH, MLP_LR = 200, 32, 1e-3


def build_mlp_ae():
    """the GAE with message passing removed: encoder Linear 30 -> 64 -> 16 per channel (ReLU between), the thesis
    decoders unchanged (inner-product adjacency, MLP 16 -> 32 -> 12). Attribute names as gae_joint.GAEModel; 3,964
    parameters (= the GAE: a GCNConv layer and a Linear layer of the same size have the same parameters)."""
    import torch.nn as nn
    import gae_joint as G

    class Enc(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv1, self.conv2, self.relu = nn.Linear(IN_DIM, 64), nn.Linear(64, 16), nn.ReLU()

        def forward(self, x):
            return self.conv2(self.relu(self.conv1(x)))

    class AE(nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = Enc()
            self.x_decoder = G.XDecoder(16, 32, 12)
    return AE()


def mlp_loss(model, A, X30, Xt, return_Z=False):
    """train_gae_v2.batch_loss with the encoder swapped: MSE(A, clamp(Z Z^T)) + 0.1 MSE(X12, Xhat) per window.
    A raw adjacency (B,18,18); X30 node input (B,18,30); Xt reconstruction target (B,18,12)."""
    import torch
    import gae_joint as G
    B = A.shape[0]
    z = model.encoder(X30.reshape(B * N_CH, IN_DIM))
    zp = z.view(B, N_CH, 16)
    Ah = torch.clamp(torch.bmm(zp, zp.transpose(1, 2)), 0.0, 1.0)
    Xh = model.x_decoder(z).view(B, N_CH, 12)
    per = ((A - Ah) ** 2).mean(dim=(1, 2)) + G.LAMBDA * ((Xt - Xh) ** 2).mean(dim=(1, 2))
    return (per, zp) if return_Z else per


def _mlp_tensors(cases, meta, device, mask_fn, max_windows=None):
    import torch
    A, X, T = [], [], []
    for s in cases:
        z = npz(s)
        idx = np.flatnonzero(mask_fn(z))
        if max_windows:
            idx = idx[:max_windows]
        X30, adj, xn, fa = node_input(z, idx, meta)
        A.append(adj); X.append(X30); T.append(np.concatenate([xn, fa], axis=2))
    cat = lambda L: torch.tensor(np.concatenate(L), device=device)  # noqa: E731
    return cat(A), cat(X), cat(T)


def mlp_train(f, device, out_dir=None, smoke=False, seed=42):
    """the GAE fold recipe (v9_x3_train_fold.py): the fold's training cases, variant 'clean' windows, the fold
    model's own f7 constants, Adam 1e-3, cosine T_max = epochs, batch 32, 200 epochs, last epoch kept, seed 42,
    window order = torch DataLoader(shuffle=True, generator seeded 42). No validation subset, no early stopping."""
    import torch
    meta = fold_meta(f)
    cases = MAN[str(f)]["train_cases"][:1] if smoke else MAN[str(f)]["train_cases"]
    A, X, T = _mlp_tensors(cases, meta, device, clean_mask, 2000 if smoke else None)
    n = len(A)
    if not smoke and n != sum(meta["n_train"].values()):
        raise SystemExit(f"STOP: fold {f} training windows {n} != GAE fold model {sum(meta['n_train'].values())}")
    torch.manual_seed(seed); np.random.seed(seed)
    torch.backends.cudnn.deterministic = True; torch.backends.cudnn.benchmark = False
    g = torch.Generator().manual_seed(seed)
    model = build_mlp_ae().to(device)
    n_params = sum(p.numel() for p in model.parameters())
    if n_params != 3964:
        raise SystemExit(f"STOP: MLP-AE parameter count {n_params} != 3964")
    epochs = 2 if smoke else MLP_EPOCHS
    opt = torch.optim.Adam(model.parameters(), lr=MLP_LR)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    rows, t0 = [], time.time()
    for ep in range(epochs):
        model.train()
        tot = torch.zeros((), device=device)
        torch.empty((), dtype=torch.int64).random_(generator=g)    # DataLoader iterator base-seed draw
        perm = torch.randperm(n, generator=g).to(device)
        torch.randperm(n, generator=g)                             # RandomSampler tail draw at exhaustion
        for i in range(0, n, MLP_BATCH):
            ii = perm[i:i + MLP_BATCH]
            opt.zero_grad()
            loss = mlp_loss(model, A[ii], X[ii], T[ii]).mean()
            loss.backward(); opt.step()
            tot += loss.detach() * len(ii)
        sched.step()
        rows.append(dict(model="mlp", fold=f, epoch=ep + 1, train_loss=float(tot) / n, s=round(time.time() - t0, 1)))
        if ep < 3 or (ep + 1) % 20 == 0 or ep == epochs - 1:
            log(f"[mlp] fold {f} epoch {ep+1}/{epochs} loss {rows[-1]['train_loss']:.6f} ({rows[-1]['s']}s)")
    info = dict(model="mlp", fold=f, n_train=n, epochs=epochs, n_params=n_params, smoke=smoke,
                first_loss=rows[0]["train_loss"], last_loss=rows[-1]["train_loss"], fit_s=round(time.time() - t0, 1),
                G2="PASS" if rows[-1]["train_loss"] < rows[0]["train_loss"] else "FAIL", device=str(device))
    if out_dir is not None:
        Path(out_dir, "ckpt").mkdir(parents=True, exist_ok=True)
        torch.save(model.state_dict(), Path(out_dir, "ckpt", f"mlp_fold{f}{'_SMOKE' if smoke else ''}.pt"))
    return model.eval(), info, rows


def mlp_D(model, f, ctx, device, chunk=8192):
    """node latent of the MLP-AE on every valid window (dump convention as the GAE) -> per-channel LedoitWolf D."""
    import torch
    X30, *_ = node_input(ctx["z"], ctx["idx"], fold_meta(f))
    Z = np.empty((len(X30), N_CH, 16), np.float32)
    with torch.no_grad():
        for s in range(0, len(X30), chunk):
            xb = torch.tensor(X30[s:s + chunk], device=device)
            Z[s:s + chunk] = model.encoder(xb.reshape(-1, IN_DIM)).view(-1, N_CH, 16).cpu().numpy()
    return d_from_Z(Z)


def mlp_step_ms(device, n_steps=300):
    """measured ms per training step (batch 32) on fold-1 windows, for the runtime projection."""
    import torch
    A, X, T = _mlp_tensors(MAN["1"]["train_cases"][:1], fold_meta(1), device, clean_mask, 20000)
    model = build_mlp_ae().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=MLP_LR)
    for rep in range(2):
        if device.type == "cuda":
            torch.cuda.synchronize()
        t0 = time.time()
        for k in range(n_steps):
            ii = torch.randint(0, len(A), (MLP_BATCH,), device=device)
            opt.zero_grad(); mlp_loss(model, A[ii], X[ii], T[ii]).mean().backward(); opt.step()
        if device.type == "cuda":
            torch.cuda.synchronize()
        dt = (time.time() - t0) / n_steps
    return dt * 1000
