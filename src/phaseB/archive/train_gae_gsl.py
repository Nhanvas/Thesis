"""
train_gae_gsl.py — retrain the S2 GAE+GSL (gae_joint_gsl.GAEModel) label-free on interictal
windows. Same pre-registered split / optimiser / schedule as train_gae_joint.py; the ONLY
additions are the GSL layer (learned graph) and an L1 sparsity term on A_L.

PREREG (inherits 01): train 12 TRAIN interictal, val 3 VAL interictal (subject-level),
never touch ictal or the 8 TEST. Adam 1e-3, cosine, 200 epochs, save final. seed 42 canonical.

Kaggle cells:
    !python gae_joint_gsl.py --selftest                 # 5s CPU: shapes+grad
    !python train_gae_gsl.py --smoke                     # ~2 min GPU: loop runs
    !python train_gae_gsl.py --seeds 42                   # full POC (1 seed)
    !python train_gae_gsl.py --seeds 42 --gate_closed --out_dir /kaggle/working/gae_gsl_closed  # self-check
"""
import argparse, time
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
import gae_joint_gsl as G

TRAIN_SUBJS = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08",
               "chb09", "chb12", "chb19", "chb20", "chb21", "chb23"]
VAL_SUBJS = ["chb10", "chb11", "chb22"]
TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
LAMBDA_SPARSE = 1e-3        # L1 on A_L; keeps the learned graph sparse (tune only on VAL if needed)


class WinDS(Dataset):
    def __init__(self, adj_dir, feat_dir, subjs, suffix, max_windows=None):
        self.A, self.X = [], []
        t0 = time.time()
        for s in subjs:
            adjs = np.load(Path(adj_dir) / f"{s}_interictal_adjs{suffix}.npy", mmap_mode="r")
            fts = np.load(Path(feat_dir) / f"{s}_interictal_features.npy", mmap_mode="r")
            n = len(adjs) if max_windows is None else min(max_windows, len(adjs))
            self.A.append(np.asarray(adjs[:n], dtype=np.float32))
            self.X.append(np.asarray(fts[:n], dtype=np.float32))
            print(f"  loaded {s}: {n} interictal windows")
        self.A = np.concatenate(self.A); self.X = np.concatenate(self.X)
        print(f"  total {len(self.A)} windows in {time.time()-t0:.1f}s")

    def __len__(self): return len(self.A)
    def __getitem__(self, i): return self.A[i], self.X[i]


def set_seed(seed):
    torch.manual_seed(seed); np.random.seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def run_epoch(model, loader, opt, device, train, lam_sparse):
    model.train() if train else model.eval()
    tot = tot_g = nb = 0.0
    ctx = torch.enable_grad() if train else torch.no_grad()
    with ctx:
        for A_np, X_np in loader:
            A_topk, Xn, A_tgt = G.build_inputs(A_np.numpy(), X_np.numpy(), device)
            sc, A_L, g = model(Xn, A_topk, A_tgt)
            loss = sc.mean() + lam_sparse * A_L.abs().mean()
            if train:
                opt.zero_grad(); loss.backward(); opt.step()
            tot += float(sc.mean().detach()); tot_g += float(g.detach()); nb += 1
    return tot / max(nb, 1), tot_g / max(nb, 1)


def main():
    ap = argparse.ArgumentParser()
    base = "/kaggle/input/datasets/nhn2mm"
    ap.add_argument("--adj_dir", default=f"{base}/chbmit-topk20")
    ap.add_argument("--feat_dir", default=f"{base}/chbmit-processed")
    ap.add_argument("--suffix", default="_topk20")
    ap.add_argument("--out_dir", default="/kaggle/working/gae_gsl")
    ap.add_argument("--epochs", type=int, default=200)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--lam_sparse", type=float, default=LAMBDA_SPARSE)
    ap.add_argument("--seeds", type=int, nargs="+", default=[42])
    ap.add_argument("--gate_closed", action="store_true", help="freeze g=0 (baseline-equivalence self-check)")
    ap.add_argument("--force_g", type=float, default=None,
                    help="freeze gate: 1.0=pure learned graph, 0.0=pure top-k20; overrides --gate_closed")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    fg = a.force_g if a.force_g is not None else (0.0 if a.gate_closed else None)
    print(f"device={device}  force_g={fg}  lam_sparse={a.lam_sparse}")

    if a.smoke:
        tr_s, va_s, ep, seeds, maxw = TRAIN_SUBJS[:1], VAL_SUBJS[:1], 2, [42], 2000
        print("SMOKE — loop check only")
    else:
        tr_s, va_s, ep, seeds, maxw = TRAIN_SUBJS, VAL_SUBJS, a.epochs, a.seeds, None

    print("Building TRAIN (interictal, 12 subj) ..."); tr = WinDS(a.adj_dir, a.feat_dir, tr_s, a.suffix, maxw)
    print("Building VAL (interictal, 3 subj) ...");    va = WinDS(a.adj_dir, a.feat_dir, va_s, a.suffix, maxw)

    for seed in seeds:
        print(f"\n=== SEED {seed} ==="); set_seed(seed)
        g = torch.Generator().manual_seed(seed)
        tl = DataLoader(tr, batch_size=a.batch, shuffle=True, generator=g)
        vl = DataLoader(va, batch_size=a.batch, shuffle=False)
        model = G.GAEModel().to(device)
        model.gsl.force_g = fg
        opt = torch.optim.Adam(model.parameters(), lr=a.lr)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=ep)
        trc, vac = [], []
        for e in range(ep):
            tr_l, tr_g = run_epoch(model, tl, opt, device, True, a.lam_sparse)
            sched.step()
            va_l, va_g = run_epoch(model, vl, None, device, False, a.lam_sparse)
            trc.append(tr_l); vac.append(va_l)
            if e < 3 or (e + 1) % 20 == 0 or e == ep - 1:
                print(f"  [seed {seed}] ep {e+1:3}/{ep}  train={tr_l:.6f}  val={va_l:.6f}  g={tr_g:.4f}")
        out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
        ck = out / f"gae_gsl_seed{seed}.pt"
        torch.save(model.state_dict(), str(ck))
        np.savez(out / f"gsl_loss_curves_seed{seed}.npz", train=np.array(trc), val=np.array(vac))
        print(f"  [seed {seed}] SAVED {ck.name} | final train={trc[-1]:.6f} val={vac[-1]:.6f} | final g={tr_g:.4f}")
    print("\nDONE. Next: val_gate.py --gae_module gae_joint_gsl --ckpt <ckpt> --suffix _topk20")


if __name__ == "__main__":
    main()
