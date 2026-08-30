"""
train_gae_multirel.py — Phase C-final / C4-full training. torch + PyG.

Trains MultiRelGAE UNSUPERVISED on the 12 TRAIN subjects' INTERICTAL windows only,
PREREG_01 recipe: Adam 1e-3, cosine, 200 epochs, batch 32, save final, --seeds list.
Checkpoint -> data/models_retrain/gae_multirel_seed{S}.pt (parallel path; rlg untouched).

PERF (lever a): the training loop uses the FAST data path — prepare_dataset() computes
sparse edges ONCE, build_batch_fast() assembles a block-diagonal batch per step without
dense_to_sparse. This removes the host-side bottleneck (GPU==CPU on the reference path
because dense_to_sparse ran 2x/window/epoch). Proven bit-identical to the PyG reference
in gae_joint_multirel --smoke. Use --profile to see the per-batch breakdown.

R2-COLLAPSE MONITOR (condition #2 — catch the S2 failure DURING training):
  logged EVERY epoch to CSV: r2_recon, gate_R2 (‖grad R2‖/‖grad R1‖), r2_loss_share.
  MID-TRAIN KILL: at epoch 20 and 40, if gate_R2 < 0.05 AND r2_recon improved < 5%
  vs epoch 0 -> STOP (clean negative; epoch 40 = where S2's gate hit 0).

SMOKE-FIRST (blocking):
  python src/phaseC/train_gae_multirel.py --smoke                 # synthetic
  python src/phaseC/train_gae_multirel.py --profile --smoke_subject chb10 \
      --a1_dir <..> --a2_dir data/processed --feat_dir <..>       # per-batch breakdown
  python src/phaseC/train_gae_multirel.py --smoke_subject chb10 --a1_dir <..> ...  # real ETA (no warmup)
Only after those pass + a GPU-measured ETA is acceptable:
  python src/phaseC/train_gae_multirel.py --seeds 42 --a1_dir <..> --a2_dir data/processed ...
"""
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
_src = _os.path.dirname(_here)
for _p in (_src, _here, _os.path.join(_src, "retrain"),
           _os.path.join(_src, "dataprep"), _os.path.join(_src, "phaseB")):
    if _os.path.isdir(_p) and _p not in _sys.path:
        _sys.path.insert(0, _p)

import argparse
import csv
import time
from pathlib import Path

import numpy as np
import torch

import gae_joint_multirel as M

TRAIN = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08",
         "chb09", "chb12", "chb19", "chb20", "chb21", "chb23"]
TEST = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}

KILL_GATE = 0.05
KILL_IMPROVE = 0.05
KILL_EPOCHS = (20, 40)


def load_train_arrays(a1_dir, a2_dir, feat_dir, subjs, suffix):
    A1, A2, X = [], [], []
    a1_dir, a2_dir, feat_dir = Path(a1_dir), Path(a2_dir), Path(feat_dir)
    for s in subjs:
        a1 = np.load(a1_dir / f"{s}_interictal_adjs{suffix}.npy", mmap_mode="r")
        a2 = np.load(a2_dir / f"{s}_interictal_te_topk20.npy", mmap_mode="r")
        xf = np.load(feat_dir / f"{s}_interictal_features.npy", mmap_mode="r")
        assert len(a1) == len(a2) == len(xf), \
            f"{s}: R1/R2/feat len {len(a1)}/{len(a2)}/{len(xf)} — run build_te_adj first"
        A1.append(np.asarray(a1)); A2.append(np.asarray(a2)); X.append(np.asarray(xf))
    return (np.concatenate(A1).astype(np.float32),
            np.concatenate(A2).astype(np.float32),
            np.concatenate(X).astype(np.float32))


def _grad_ratio(model):
    g1 = sum(p.grad.norm().item() for p in model.encoder.r1_params() if p.grad is not None)
    g2 = sum(p.grad.norm().item() for p in model.encoder.r2_params() if p.grad is not None)
    return g2 / (g1 + 1e-12), g1, g2


def train_one_seed(A1, A2, X, seed, epochs, device, log_path, mu, lam,
                   batch=32, lr=1e-3, kill=True):
    torch.manual_seed(seed); np.random.seed(seed)
    model = M.MultiRelGAE().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    ds = M.prepare_dataset(A1, A2, X)                     # sparse edges ONCE (lever a)
    n = len(A1); idx = np.arange(n)

    rows = []; r2_recon_ep0 = None
    for ep in range(epochs):
        t_ep = time.time()
        model.train(); np.random.shuffle(idx)
        acc = dict(total=0.0, r1=0.0, r2=0.0, rx=0.0, gate=0.0, nb=0)
        for s in range(0, n, batch):
            b = idx[s:s + batch]
            xs, ei1, ew1, ei2, ew2, A1b, A2nb, Xnb, B = M.build_batch_fast(ds, b, device)
            o = model.forward_raw(xs, ei1, ew1, ei2, ew2, A1b, A2nb, Xnb, B, mu=mu, lam=lam)
            opt.zero_grad(); o["total"].backward()
            gate, _, _ = _grad_ratio(model)
            opt.step()
            acc["total"] += o["total"].item(); acc["r1"] += o["r1"].mean().item()
            acc["r2"] += o["r2"].mean().item(); acc["rx"] += o["rx"].mean().item()
            acc["gate"] += gate; acc["nb"] += 1
        sched.step()
        nb = acc["nb"]; r2_recon = acc["r2"] / nb; tot = acc["total"] / nb
        gate_ep = acc["gate"] / nb; share = (mu * r2_recon) / (tot + 1e-12)
        sec = time.time() - t_ep
        if r2_recon_ep0 is None:
            r2_recon_ep0 = r2_recon
        rows.append(dict(epoch=ep, total=round(tot, 6), r1=round(acc["r1"] / nb, 6),
                         r2_recon=round(r2_recon, 6), rx=round(acc["rx"] / nb, 6),
                         gate_R2=round(gate_ep, 5), r2_loss_share=round(share, 5),
                         lr=round(sched.get_last_lr()[0], 6), sec=round(sec, 2)))
        if ep % 10 == 0 or ep == epochs - 1:
            print(f"  ep{ep:3d} total={tot:.5f} r2_recon={r2_recon:.5f} "
                  f"gate_R2={gate_ep:.4f} share={share:.4f} {sec:.1f}s")
        if kill and ep in KILL_EPOCHS:
            improve = 1.0 - (r2_recon / (r2_recon_ep0 + 1e-12))
            if gate_ep < KILL_GATE and improve < KILL_IMPROVE:
                print(f"\n*** R2-COLLAPSE at epoch {ep}: gate_R2={gate_ep:.4f} < {KILL_GATE}, "
                      f"r2_recon improve={improve*100:.1f}% < {KILL_IMPROVE*100:.0f}%. "
                      f"STOP (clean negative — same failure class as S2). ***")
                _write_log(log_path, rows)
                return model, rows, True
    _write_log(log_path, rows)
    return model, rows, False


def _write_log(log_path, rows):
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"  [log] {log_path}")


def _eta_from_rows(rows, n_win, n_full=12 * 18000, epochs=200):
    """ms/window from epochs>=1 (EXCLUDE epoch-0 warmup) + extrapolated ETA."""
    secs = [r["sec"] for r in rows[1:]] or [r["sec"] for r in rows]
    ms_win = 1000.0 * (sum(secs) / len(secs)) / n_win
    eta_h = ms_win * n_full * epochs / 1000 / 3600
    return ms_win, eta_h


# ----------------------------------------------------------------------------
def profile_batches(subj, a1_dir, a2_dir, feat_dir, suffix, n_batches=40, batch=32):
    """Confirm the bottleneck by NUMBER before trusting lever (a): time the OLD
    per-batch dense_to_sparse (build_batch_mr) vs the NEW build_batch_fast vs
    forward vs backward. Prints per-batch ms for each."""
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    A1, A2, X = load_train_arrays(a1_dir, a2_dir, feat_dir, [subj], suffix)
    model = M.MultiRelGAE().to(dev); opt = torch.optim.Adam(model.parameters(), 1e-3)
    idx = np.arange(len(A1)); np.random.shuffle(idx)

    def sync():
        if dev.type == "cuda":
            torch.cuda.synchronize()

    # OLD: build_batch_mr (dense_to_sparse x2/window) per batch
    t_old = 0.0
    for k in range(n_batches):
        b = idx[k * batch:(k + 1) * batch]
        t0 = time.time()
        M.build_batch_mr(torch.tensor(A1[b]), torch.tensor(A2[b]), torch.tensor(X[b]), dev); sync()
        t_old += time.time() - t0

    # NEW: prepare_dataset ONCE, then build_batch_fast per batch
    t0 = time.time(); ds = M.prepare_dataset(A1, A2, X); t_prep = time.time() - t0
    t_new = 0.0
    for k in range(n_batches):
        b = idx[k * batch:(k + 1) * batch]
        t0 = time.time(); M.build_batch_fast(ds, b, dev); sync(); t_new += time.time() - t0

    # forward / backward on the fast path
    t_fwd = t_bwd = 0.0
    for k in range(n_batches):
        b = idx[k * batch:(k + 1) * batch]
        xs, e1, w1, e2, w2, A1b, A2nb, Xnb, B = M.build_batch_fast(ds, b, dev)
        t0 = time.time(); o = model.forward_raw(xs, e1, w1, e2, w2, A1b, A2nb, Xnb, B); sync()
        t_fwd += time.time() - t0
        opt.zero_grad(); t0 = time.time(); o["total"].backward(); sync(); t_bwd += time.time() - t0
        opt.step()

    per = lambda t: 1000.0 * t / n_batches
    print(f"\n[PROFILE] device={dev}  batch={batch}  n_batches={n_batches}  ({subj})")
    print(f"  OLD build_batch_mr (dense_to_sparse x2/win): {per(t_old):7.2f} ms/batch")
    print(f"  NEW build_batch_fast (edges precomputed)   : {per(t_new):7.2f} ms/batch  "
          f"(+prepare_dataset one-time {t_prep:.1f}s)")
    print(f"  forward                                    : {per(t_fwd):7.2f} ms/batch")
    print(f"  backward                                   : {per(t_bwd):7.2f} ms/batch")
    old_step = per(t_old) + per(t_fwd) + per(t_bwd)
    new_step = per(t_new) + per(t_fwd) + per(t_bwd)
    print(f"  => est step OLD {old_step:.2f} ms | NEW {new_step:.2f} ms | "
          f"speedup {old_step/max(new_step,1e-9):.2f}x")
    print(f"  If build_batch_mr >> forward+backward, the bottleneck WAS dense_to_sparse "
          f"and lever (a) is the right fix.")


def synthetic_smoke():
    dev = torch.device("cpu"); rng = np.random.default_rng(0); N = 128
    A1 = rng.random((N, 18, 18)).astype(np.float32); A1 = (A1 + A1.transpose(0, 2, 1)) / 2
    A1 *= (A1 > 0.8); A2 = (rng.random((N, 18, 18)) * (rng.random((N, 18, 18)) > 0.8)).astype(np.float32)
    for i in range(N):
        np.fill_diagonal(A1[i], 0); np.fill_diagonal(A2[i], 0)
    A2[0] = 0.0
    X = rng.random((N, 18, 5)).astype(np.float32)
    print("[SMOKE] synthetic train (fast path), 5 epochs, kill disabled")
    _, rows, _ = train_one_seed(A1, A2, X, seed=0, epochs=5, device=dev,
                                log_path="/tmp/c4full_smoke_log.csv",
                                mu=M.MU_R2, lam=M.LAMBDA_X, batch=16, kill=False)
    losses = [r["total"] for r in rows]
    assert all(np.isfinite(losses)) and losses[-1] <= losses[0] + 1e-6, f"loss: {losses}"
    assert all(r["gate_R2"] > 0 for r in rows), "R2 gate zero from start"
    print(f"[SMOKE] loss {losses[0]:.4f}->{losses[-1]:.4f} finite/decreasing; "
          f"gate_R2[-1]={rows[-1]['gate_R2']:.3f}  PASS")


def subject_smoke(subj, a1_dir, a2_dir, feat_dir, suffix, epochs=6):
    assert subj not in TEST, f"{subj} is TEST — smoke on VAL/TRAIN only"
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    A1, A2, X = load_train_arrays(a1_dir, a2_dir, feat_dir, [subj], suffix)
    print(f"[SMOKE] {subj}: {len(A1)} interictal windows, {epochs} epochs on {dev} (fast path)")
    _, rows, _ = train_one_seed(A1, A2, X, seed=0, epochs=epochs, device=dev,
                                log_path=f"/tmp/c4full_smoke_{subj}.csv",
                                mu=M.MU_R2, lam=M.LAMBDA_X, kill=False)
    losses = [r["total"] for r in rows]
    assert all(np.isfinite(losses)) and losses[-1] <= losses[0] + 1e-6, f"loss: {losses}"
    ms_win, eta_h = _eta_from_rows(rows, len(A1))
    devname = "GPU" if torch.cuda.is_available() else "CPU"
    print(f"[SMOKE] {subj}: loss {losses[0]:.4f}->{losses[-1]:.4f} finite/decreasing")
    print(f"[SMOKE] ~{ms_win:.3f} ms/window/epoch on {devname} (epoch-0 warmup EXCLUDED)")
    print(f"[SMOKE] ETA full 200ep on ~216000 win ≈ {eta_h:.1f} h/seed (extrapolated from {devname})")
    print("[SMOKE] PASS — commit the full run only if this ETA is acceptable.")


# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="42")
    ap.add_argument("--epochs", type=int, default=200)
    ap.add_argument("--a1_dir", default="/kaggle/input/datasets/nhn2mm/chbmit-topk20")
    ap.add_argument("--a2_dir", default="data/processed")
    ap.add_argument("--feat_dir", default="/kaggle/input/datasets/nhn2mm/chbmit-processed")
    ap.add_argument("--suffix", default="_topk20")
    ap.add_argument("--out_dir", default="data/models_retrain")
    ap.add_argument("--log_dir", default="results/phaseC/c4full/train_logs")
    ap.add_argument("--mu", type=float, default=M.MU_R2)
    ap.add_argument("--lam", type=float, default=M.LAMBDA_X)
    ap.add_argument("--no_kill", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--smoke_subject", default=None)
    ap.add_argument("--profile", action="store_true", help="per-batch bottleneck breakdown (needs --smoke_subject)")
    a = ap.parse_args()

    if a.smoke:
        synthetic_smoke(); return
    if a.profile:
        if not a.smoke_subject:
            raise SystemExit("--profile needs --smoke_subject <subj>")
        profile_batches(a.smoke_subject, a.a1_dir, a.a2_dir, a.feat_dir, a.suffix); return
    if a.smoke_subject:
        subject_smoke(a.smoke_subject, a.a1_dir, a.a2_dir, a.feat_dir, a.suffix); return

    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={dev}  TRAIN={TRAIN}")
    A1, A2, X = load_train_arrays(a.a1_dir, a.a2_dir, a.feat_dir, TRAIN, a.suffix)
    print(f"train set: {len(A1)} interictal windows (12 subjects)")
    Path(a.out_dir).mkdir(parents=True, exist_ok=True)

    for sd in [int(s) for s in a.seeds.split(",")]:
        print(f"\n=== seed {sd} ===")
        log = str(Path(a.log_dir) / f"train_multirel_seed{sd}.csv")
        model, rows, collapsed = train_one_seed(
            A1, A2, X, seed=sd, epochs=a.epochs, device=dev, log_path=log,
            mu=a.mu, lam=a.lam, kill=not a.no_kill)
        if collapsed:
            print(f"seed {sd}: COLLAPSED — checkpoint NOT saved."); continue
        out = Path(a.out_dir) / f"gae_multirel_seed{sd}.pt"
        torch.save(model.state_dict(), out)
        ms_win, eta_h = _eta_from_rows(rows, len(A1), n_full=len(A1), epochs=a.epochs)
        print(f"seed {sd}: saved {out}  final r2_recon={rows[-1]['r2_recon']} "
              f"gate_R2={rows[-1]['gate_R2']} | ~{ms_win:.3f} ms/win, {eta_h:.1f}h actual")


if __name__ == "__main__":
    main()
