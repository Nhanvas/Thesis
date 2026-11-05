#!/usr/bin/env python
"""
f1_core.py -- Track F1/F2 (docs/FUTURE_RESEARCH_PLAN.md rev 1): repeated random patient-wise 4-fold CV of the GAE and
of the MLP autoencoder (the GAE without message passing). Partition-aware generalisation of the closed model
comparison (src/model_cmp_core.py, imported read-only, never edited): every fold list, every normalisation constant
and every k comes from the partition being run (results/f1_repcv/partitions.json); nothing is tied to the committed
folds except partition 0, which is only used for gates.

Per (partition p, model, fold f) job:
  1. f7 normalisation constants from the fold's training cases (clean windows; the computation of
     v9_x3_train_fold.norm_constants_fold, float64 running sums, cases in sorted order);
  2. training: the thesis fold recipe (variant "clean" windows of the training cases, node input 30 = adjacency row /
     max 18 + band powers per-window min-max 5 + f7 standardised, clipped +-4, mapped to [0, 1] 7; Adam 1e-3, cosine
     T_max = 200, batch 32, 200 epochs, last epoch kept, no validation subset, no early stopping), seed = the
     partition's seed. GAE = gae_joint.GAEModel (GCNConv 30 -> 64 -> 16, decoders as the thesis); MLP-AE =
     model_cmp_core.build_mlp_ae (Linear 30 -> 64 -> 16, same decoders). Both 3,964 parameters. The batches are
     built with tensors instead of the PyG DataLoader; the window order reproduces DataLoader(shuffle=True,
     generator=seed) exactly (gate G-vec: identical weights to the PyG loop on CPU);
  3. the frozen downstream chain, unchanged (v9_e1_baselines.evaluate_arm via the model comparison's construction):
     per-channel LedoitWolf distance of the 16-d node latent -> members 6/9/12 + mean with +-15 min drift ->
     percentile mean (x) / robust-z member mean (m) -> smoothing 5 -> per-patient budget clip(q_i(k), 0.005, 0.02),
     k calibrated on the fold's own training cases (median q_i = 0.005, label-free) -> merge 90 s -> kernel CPD ->
     SzCORE; plus the fixed 0.005 point, the detector curve over v9_e1_baselines.GRID, window AUROC, per-seizure caught.

Gates (f1_run.py calls them; STOP on failure): D0 data identity (model_cmp_core.gate_D0); G-const (partition 0's
constants recomputed here = the committed fold models' constants); GG0 (this module's chain, run on partition 0 with
the committed GAE fold checkpoints, reproduces results/v9_x3 and the 185 caught flags exactly; k within 1e-6
relative); G-vec (the tensor training loop gives the same weights as the PyG DataLoader loop of v9_x3_train_fold.py,
CPU, real windows); G-mlp (this module's MLP-AE loop = model_cmp_core.mlp_train, CPU); per job: training-window count
= the committed clean-window counts of the training cases, parameter count 3,964, G2 (last-epoch loss < first).
"""
import hashlib
import json
import os
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(os.environ.get("THESIS_REPO", Path(__file__).resolve().parents[1]))
for _p in ("src", "src/retrain", "src/phaseB", "src/phaseC", "src/dataprep"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import model_cmp_core as C               # noqa: E402  (closed code, read only)

V9E1 = C.V9E1
PARTITIONS = Path(os.environ.get("F1_PARTITIONS", REPO / "results" / "f1_repcv" / "partitions.json"))
EPOCHS = int(os.environ.get("F1_EPOCHS", 200))       # 200 = the registered recipe; any other value is a test only
BATCH, LR, N_CH, IN_DIM, OUT_X, LAT = 32, 1e-3, 18, 30, 12, 16
MODELS = ("gae", "mlp")


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def sha16(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


# ============================================================================ partitions
_PARTS = None


def parts():
    global _PARTS
    if _PARTS is None:
        _PARTS = json.loads(PARTITIONS.read_text())["partitions"]
    return _PARTS


def manifest(p):
    """{fold (int): dict(held_out_cases, train_cases)} of partition p."""
    return {int(k): v for k, v in parts()[str(p)]["folds"].items()}


def seed_of(p):
    return int(parts()[str(p)]["seed"])


# ============================================================================ normalisation constants + window counts
def clean_counts():
    """clean training-window count of every case, read from the committed fold models' metas (each case is a
    training case of three of them); STOP if they disagree."""
    out = {}
    for f in C.FOLDS:
        for s, n in C.fold_meta(f)["n_train"].items():
            if s in out and out[s] != int(n):
                raise SystemExit(f"STOP: committed clean-window counts of {s} differ between fold models")
            out[s] = int(n)
    if sorted(out) != sorted(C.ALL):
        raise SystemExit(f"STOP: clean-window counts missing for {sorted(set(C.ALL) - set(out))}")
    return out


def fold_constants(train_cases):
    """v9_x3_train_fold.norm_constants_fold on the fold's training cases (sorted), clean windows, float64 sums."""
    n, s1, s2 = 0, np.zeros(7), np.zeros(7)
    for s in sorted(train_cases):
        z = C.npz(s)
        F = z["f7"][C.clean_mask(z)].reshape(-1, 7).astype(np.float64)
        if not np.isfinite(F).all():
            raise SystemExit(f"STOP: {s}: non-finite f7 inside the training mask")
        n += len(F); s1 += F.sum(0); s2 += (F * F).sum(0)
    mu = s1 / n
    return mu, np.sqrt(np.maximum(s2 / n - mu * mu, 1e-12))


def new_meta(p, f):
    man = manifest(p)[f]
    mu, sd = fold_constants(man["train_cases"])
    cc = clean_counts()
    return dict(partition=int(p), fold=int(f), seed=seed_of(p), in_dim=IN_DIM, out_x=OUT_X, clip=4.0,
                add_mean=mu.tolist(), add_std=sd.tolist(), train_cases=sorted(man["train_cases"]),
                held_out_cases=list(man["held_out_cases"]), n_train={s: cc[s] for s in sorted(man["train_cases"])})


# ============================================================================ training (tensor batches)
def _loss(kind, model, A, X, T):
    """train_gae_v2.batch_loss (kind 'gae') / model_cmp_core.mlp_loss (kind 'mlp') on tensor batches:
    MSE(A_raw, clamp(Z Z^T, 0, 1)) + 0.1 MSE([xn, fa], X_hat) per window."""
    import torch
    import gae_joint as G
    B = A.shape[0]
    if kind == "gae":
        b_, r_, c_ = A.nonzero(as_tuple=True)                        # = dense_to_sparse per window + Batch offsets
        ei = torch.stack([b_ * N_CH + r_, b_ * N_CH + c_])
        z = model.encoder(X.reshape(B * N_CH, IN_DIM), ei, A[b_, r_, c_])
    else:
        z = model.encoder(X.reshape(B * N_CH, IN_DIM))
    zp = z.view(B, N_CH, LAT)
    Ah = torch.clamp(torch.bmm(zp, zp.transpose(1, 2)), 0.0, 1.0)
    Xh = model.x_decoder(z).view(B, N_CH, OUT_X)
    return ((A - Ah) ** 2).mean(dim=(1, 2)) + G.LAMBDA * ((T - Xh) ** 2).mean(dim=(1, 2))


def build(kind):
    import gae_joint as G
    return G.GAEModel(in_dim=IN_DIM, bands=OUT_X) if kind == "gae" else C.build_mlp_ae()


def train(kind, cases, meta, seed, device, epochs=None, max_windows=None, tag=""):
    """the thesis fold recipe; window order = torch DataLoader(shuffle=True, generator seeded `seed`): per epoch one
    int64 draw (iterator base seed), one randperm (the order), one tail randperm at exhaustion."""
    import torch
    epochs = EPOCHS if epochs is None else epochs
    t_load = time.time()
    A, X, T = C._mlp_tensors(sorted(cases), meta, device, C.clean_mask, max_windows)
    n = len(A)
    t_load = time.time() - t_load
    torch.manual_seed(seed); np.random.seed(seed)
    torch.backends.cudnn.deterministic = True; torch.backends.cudnn.benchmark = False
    g = torch.Generator().manual_seed(seed)
    model = build(kind).to(device)
    n_params = sum(q.numel() for q in model.parameters())
    if n_params != 3964:
        raise SystemExit(f"STOP: {kind} parameter count {n_params} != 3964")
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    rows, t0 = [], time.time()
    for ep in range(epochs):
        model.train()
        tot = torch.zeros((), device=device)
        torch.empty((), dtype=torch.int64).random_(generator=g)
        perm = torch.randperm(n, generator=g).to(device)
        torch.randperm(n, generator=g)
        for i in range(0, n, BATCH):
            ii = perm[i:i + BATCH]
            opt.zero_grad()
            loss = _loss(kind, model, A[ii], X[ii], T[ii]).mean()
            loss.backward(); opt.step()
            tot += loss.detach() * len(ii)
        sched.step()
        rows.append(dict(model=kind, epoch=ep + 1, train_loss=float(tot) / n, s=round(time.time() - t0, 1)))
        if ep < 2 or (ep + 1) % 20 == 0 or ep == epochs - 1:
            log(f"[{kind}{tag}] epoch {ep+1}/{epochs} loss {rows[-1]['train_loss']:.6f} ({rows[-1]['s']}s)")
    steps = epochs * ((n + BATCH - 1) // BATCH)
    info = dict(model=kind, n_train=int(n), epochs=epochs, batch=BATCH, lr=LR, seed=int(seed), n_params=n_params,
                first_loss=rows[0]["train_loss"], last_loss=rows[-1]["train_loss"], fit_s=round(time.time() - t0, 1),
                load_s=round(t_load, 1), ms_per_step=round((time.time() - t0) / steps * 1000, 3), device=str(device),
                G2="PASS" if rows[-1]["train_loss"] < rows[0]["train_loss"] else "FAIL", torch=torch.__version__)
    return model.eval(), info, rows


# ============================================================================ per-channel distance D
def encode_D(kind, model, meta, ctx, chunk=2048):
    """node latent on every valid window (dump convention of v9_x3_cv_eval.dump_D / model_cmp_core.node_input), on
    CPU, then the per-channel LedoitWolf Mahalanobis distance. kind 'gae' = model_cmp_core.gae_D with an explicit
    model; kind 'mlp' = model_cmp_core.mlp_D on CPU."""
    import torch
    model = model.cpu().eval()
    X30, adj, xn, fa = C.node_input(ctx["z"], ctx["idx"], meta)
    Z = np.empty((len(adj), N_CH, LAT), np.float32)
    with torch.no_grad():
        for s in range(0, len(adj), chunk):
            if kind == "gae":
                A = torch.tensor(adj[s:s + chunk]); B = A.shape[0]
                An = A / (A.amax(dim=(1, 2), keepdim=True) + 1e-8)
                x = torch.cat([An, torch.tensor(xn[s:s + chunk]), torch.tensor(fa[s:s + chunk])], 2).reshape(B * N_CH, -1)
                b, i, j = A.nonzero(as_tuple=True)
                ei = torch.stack([b * N_CH + i, b * N_CH + j])
                Z[s:s + chunk] = model.encoder(x, ei, A[b, i, j]).view(B, N_CH, LAT).numpy()
            else:
                xb = torch.tensor(X30[s:s + chunk])
                Z[s:s + chunk] = model.encoder(xb.reshape(-1, IN_DIM)).view(-1, N_CH, LAT).numpy()
    return C.d_from_Z(Z)


# ============================================================================ chain + outputs
def seizure_rows(model, p, f, ctx, loc):
    rows = []
    for fi, rr in C.P3L.refs_of(ctx).items():
        for a, b in rr:
            hit = any(h1 >= a - C.PRE and h0 <= b + C.POST for h0, h1 in loc.get(fi, []))
            rows.append(dict(model=model, partition=p, subject=ctx["s"], fold=f,
                             file=ctx["files"][int(fi)] if ctx["files"] else int(fi), onset_s=int(a),
                             duration_s=int(b - a), caught=bool(hit)))
    return rows


def evaluate_case(model, p, f, ctx, x, m, k):
    """model_cmp_core.evaluate_case with the fold and partition given explicitly."""
    from sklearn.metrics import roc_auc_score
    per = []
    out, _det, loc = V9E1.evaluate_arm(ctx, x, k, C.FLOOR, C.CAP, C.SMOOTH, m=m)
    for st, v in out.items():
        per.append(dict(model=model, partition=p, fold=f, subject=ctx["s"], point="own", stage=st, k=k, **v))
    seiz = seizure_rows(model, p, f, ctx, loc)
    out0, _, _ = V9E1.evaluate_arm(ctx, x, k, C.FLOOR, C.CAP, C.SMOOTH, m=None)
    for st, v in out0.items():
        per.append(dict(model=model, partition=p, fold=f, subject=ctx["s"], point="fixed0.005", stage=st, k=np.nan, **v))
    cur = [dict(model=model, partition=p, fold=f, subject=ctx["s"], **r) for r in V9E1.sweep_detector(ctx, x, C.GRID)]
    ok = ctx["ok"]; y = ctx["ict"][ok].astype(int)
    au = dict(model=model, partition=p, fold=f, subject=ctx["s"],
              auroc=float(roc_auc_score(y, x[ok])) if 0 < y.sum() < len(y) else np.nan)
    return per, cur, [au], seiz


def run_fold(model, p, f, man, D_fn):
    """D_fn(ctx) -> per-channel distance. k from the fold's training cases; held-out cases evaluated."""
    t0 = time.time()
    ms = []
    for s in sorted(man["train_cases"]):
        ctx = C.make_ctx(s)
        ms.append((ctx, C.scalars("D", ctx, D_fn(ctx))[1]))
    k = C.calibrate(ms)
    del ms
    P, Cc, A, S = [], [], [], []
    for s in man["held_out_cases"]:
        ctx = C.make_ctx(s)
        x, m = C.scalars("D", ctx, D_fn(ctx))
        a, b, c, d = evaluate_case(model, p, f, ctx, x, m, k)
        P += a; Cc += b; A += c; S += d
    log(f"[{model}] partition {p} fold {f}: k = {k:.6f}; held-out {man['held_out_cases']} scored ({time.time()-t0:.0f}s)")
    return P, Cc, A, S, k, time.time() - t0


# ============================================================================ gates
def gate_const():
    """partition 0: constants and training-window counts computed here = the committed fold models' metas."""
    worst, bad = 0.0, []
    for f in C.FOLDS:
        ref = C.fold_meta(f)
        mu, sd = fold_constants(manifest(0)[f]["train_cases"])
        for got, want in ((mu, ref["add_mean"]), (sd, ref["add_std"])):
            r = float(np.max(np.abs(got - np.array(want)) / np.maximum(np.abs(want), 1e-12)))
            worst = max(worst, r)
            if r > 1e-9:
                bad.append((f, r))
        if sorted(ref["n_train"]) != sorted(manifest(0)[f]["train_cases"]):
            bad.append((f, "training cases differ from the committed fold model"))
    st = "PASS" if not bad else "FAIL"
    log(f"G-const {st}: partition-0 constants vs committed fold models, max relative difference {worst:.2e}")
    return dict(gate="G-const", status=st, max_rel=worst, bad=str(bad))


def committed_gae(f):
    import torch
    meta = C.fold_meta(f)
    m = build("gae")
    m.load_state_dict(torch.load(str(C.X3 / "models" / f"fold{f}" / f"gae_fold{f}_seed42.pt"), map_location="cpu"),
                      strict=True)
    return m.eval(), meta


def gate_GG0():
    """this module's chain on partition 0 with the committed GAE fold checkpoints = results/v9_x3 (tp/fp of 48 rows
    and the 185 caught flags exactly, k within 1e-6 relative; model_cmp_core.gate_GG)."""
    t0 = time.time()
    P, S, ks, secs = [], [], {}, []
    for f in C.FOLDS:
        model, meta = committed_gae(f)
        p_, _c, _a, s_, k, sec = run_fold("gae", 0, f, manifest(0)[f], lambda ctx: encode_D("gae", model, meta, ctx))
        P += p_; S += s_; ks[f] = k; secs.append(sec)
    g = C.gate_GG(P, S, ks)
    g.update(gate="GG0", seconds=round(time.time() - t0), fold_seconds=[round(x) for x in secs])
    return g


def _pyg_reference_train(cases, meta, seed, epochs, max_windows):
    """v9_x3_train_fold.py's loop verbatim (PyG Data objects + DataLoader), CPU, on the given windows."""
    import torch
    from torch_geometric.loader import DataLoader
    import train_gae_v2 as TGV2
    mu, sd = np.array(meta["add_mean"]), np.array(meta["add_std"])
    ds = []
    for s in sorted(cases):
        z = C.npz(s)
        idx = np.flatnonzero(TGV2.mask(z, "clean"))[:max_windows]
        adj = z["adj"][idx].astype(np.float32)
        xn = TGV2.bp_minmax(z["bp5"][idx].astype(np.float32))
        fa = TGV2.scale_add(z["f7"][idx].astype(np.float64), mu, sd)
        ds += [TGV2.window_data(adj[i], xn[i], fa[i]) for i in range(len(idx))]
    TGV2.set_seed(seed)
    g = torch.Generator().manual_seed(seed)
    model = build("gae")
    tl = DataLoader(ds, batch_size=BATCH, shuffle=True, generator=g)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    for _ in range(epochs):
        model.train()
        for b in tl:
            opt.zero_grad()
            TGV2.batch_loss(model, b, torch.device("cpu")).mean().backward(); opt.step()
        sched.step()
    return model


def _maxdiff(m1, m2):
    a, b = m1.state_dict(), m2.state_dict()
    return float(max((a[k].cpu() - b[k].cpu()).abs().max().item() for k in a))


def gate_vec(max_windows=2000, epochs=2):
    """the tensor training loop = the PyG DataLoader loop of v9_x3_train_fold.py (CPU, partition-0 fold-1 first
    training case, committed fold-1 constants, seed 42)."""
    import torch
    t0 = time.time()
    case = sorted(manifest(0)[1]["train_cases"])[:1]
    meta = C.fold_meta(1)
    ref = _pyg_reference_train(case, meta, 42, epochs, max_windows)
    mine, _, _ = train("gae", case, meta, 42, torch.device("cpu"), epochs=epochs, max_windows=max_windows, tag=" G-vec")
    d = _maxdiff(ref, mine)
    st = "PASS" if d <= 1e-6 else "FAIL"
    log(f"G-vec {st}: tensor loop vs PyG DataLoader loop, max |weight difference| = {d:.3e} ({time.time()-t0:.0f}s)")
    return dict(gate="G-vec", status=st, max_abs_diff=d, exact=d == 0.0, case=case[0], windows=max_windows, epochs=epochs)


def gate_mlp(epochs=2):
    """this module's MLP-AE loop = model_cmp_core.mlp_train (the run of the model comparison), CPU, smoke subset."""
    import torch
    t0 = time.time()
    ref, _, _ = C.mlp_train(1, torch.device("cpu"), smoke=True)
    case = C.MAN["1"]["train_cases"][:1]
    mine, _, _ = train("mlp", case, C.fold_meta(1), 42, torch.device("cpu"), epochs=epochs, max_windows=2000, tag=" G-mlp")
    d = _maxdiff(ref, mine)
    st = "PASS" if d <= 1e-6 else "FAIL"
    log(f"G-mlp {st}: MLP-AE loop vs model_cmp_core.mlp_train, max |weight difference| = {d:.3e} ({time.time()-t0:.0f}s)")
    return dict(gate="G-mlp", status=st, max_abs_diff=d, exact=d == 0.0)


# ============================================================================ one job = (partition, model, fold)
def job(p, model, f, device, out_root, smoke=False):
    """train + score one fold; every output written under out_root/p{p}/jobs/{model}_fold{f}/ (smoke: .../smoke/),
    DONE.json written last (a job without DONE.json does not exist)."""
    import resource
    import torch
    t0 = time.time()
    jd = Path(out_root) / f"p{p}" / ("smoke" if smoke else "jobs") / f"{model}_fold{f}"
    jd.mkdir(parents=True, exist_ok=True)
    man = manifest(p)[f]
    meta = new_meta(p, f)
    seed = seed_of(p)
    cases = meta["train_cases"]
    mdl, info, rows = train(model, cases[:1] if smoke else cases, meta, seed, device,
                            epochs=2 if smoke else None, max_windows=2000 if smoke else None, tag=f" p{p} f{f}")
    if not smoke and info["n_train"] != sum(meta["n_train"].values()):
        raise SystemExit(f"STOP: {model} p{p} fold {f}: training windows {info['n_train']} != committed clean "
                         f"counts {sum(meta['n_train'].values())}")
    tag = f"{model}_p{p}_fold{f}_seed{seed}" + ("_SMOKE" if smoke else "")
    torch.save({k: v.cpu() for k, v in mdl.state_dict().items()}, jd / f"{tag}.pt")
    (jd / f"{tag}.json").write_text(json.dumps(dict(meta, model=model, **{k: v for k, v in info.items()
                                                                          if k != "model"}), indent=1))
    pd.DataFrame([dict(r, partition=p, fold=f) for r in rows]).to_csv(jd / "training_log.csv", index=False)
    if smoke:
        ctx = C.make_ctx(man["held_out_cases"][0])
        D = encode_D(model, mdl, meta, ctx)
        if not np.isfinite(D).all():
            raise SystemExit(f"STOP smoke: non-finite {model} distance on {ctx['s']}")
        cal = C.make_ctx(cases[0])
        k = C.calibrate([(cal, C.scalars("D", cal, encode_D(model, mdl, meta, cal))[1])])
        per, cur, au, seiz = evaluate_case(model, p, f, ctx, *C.scalars("D", ctx, D), k)
        res = (per, cur, au, seiz, k, 0.0)
    else:
        res = run_fold(model, p, f, man, lambda ctx: encode_D(model, mdl, meta, ctx))
    per, cur, au, seiz, k, score_s = res
    for name, rr in (("per_subject", per), ("curves", cur), ("auroc", au), ("seizures", seiz)):
        pd.DataFrame(rr).to_csv(jd / f"{name}.csv", index=False)
    fit = dict(info, partition=p, fold=f, k=k, score_s=round(score_s, 1), smoke=smoke,
               peak_rss_mb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
               core_sha=sha16(Path(__file__)), partitions_sha=sha16(PARTITIONS))
    (jd / "fit.json").write_text(json.dumps(fit, indent=1))
    if info["G2"] != "PASS":
        raise SystemExit(f"STOP G2: {model} p{p} fold {f} did not train (loss did not fall)")
    (jd / "DONE.json").write_text(json.dumps(dict(status="done", seconds=round(time.time() - t0), **{
        k: fit[k] for k in ("core_sha", "partitions_sha", "device", "epochs", "seed")}), indent=1))
    log(f"[{model}] p{p} fold {f} {'SMOKE ' if smoke else ''}done in {time.time()-t0:.0f}s "
        f"(train {info['fit_s']}s, {info['ms_per_step']} ms/step, peak RSS {fit['peak_rss_mb']} MB)")
    return dict(model=model, partition=p, fold=f, status="done", seconds=round(time.time() - t0),
                ms_per_step=info["ms_per_step"], device=str(device))


def timing(device, n_steps=300, n_windows=20000):
    """measured ms per training step (batch 32) of both models on real windows (fold-1 first training case)."""
    import torch
    meta = C.fold_meta(1)
    A, X, T = C._mlp_tensors(sorted(manifest(0)[1]["train_cases"])[:1], meta, device, C.clean_mask, n_windows)
    out = {}
    for kind in MODELS:
        model = build(kind).to(device)
        opt = torch.optim.Adam(model.parameters(), lr=LR)
        for rep in range(2):                                   # rep 0 = warm-up
            if device.type == "cuda":
                torch.cuda.synchronize(device)
            t0 = time.time()
            for _ in range(n_steps):
                ii = torch.randint(0, len(A), (BATCH,), device=device)
                opt.zero_grad(); _loss(kind, model, A[ii], X[ii], T[ii]).mean().backward(); opt.step()
            if device.type == "cuda":
                torch.cuda.synchronize(device)
            out[kind] = (time.time() - t0) / n_steps * 1000
    return out
