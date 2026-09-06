"""
train_gae_joint.py — reconstructed training loop for the joint GAE (PHA 1, step 1).

Depends on gae_joint.py. Model identity is established by reproducing the committed
held-out component arrays from the checkpoint, never by a hard-coded constant: filenames,
sizes and legacy fingerprints are not identity evidence, and reasoning from them once led
this project to the wrong conclusion about which checkpoint was canonical. Run the
provenance check for the current verdict. The ONLY new thing here is the training loop;
the model, input construction, and loss are the verified ones.

PRE-REGISTERED (PREREG 01): train on interictal windows of 12 TRAIN subjects, validate on
3 held-out VAL subjects (subject-level), never touch ictal or the 8 TEST subjects. Loss is
the joint anomaly score itself. Adam lr=1e-3, cosine, 200 epochs, no early stopping, save
final epoch. Multi-seed {42,1,2,3,4}; seed 42 canonical. Nothing tuned on test.

Run on Kaggle (GPU + graph datasets). Smoke first, then full:
    # in a cell, after %%writefile gae_joint.py / train_gae_joint.py:
    !python train_gae_joint.py --smoke      # 1 subj, 2 epochs — verifies the loop runs
    !python train_gae_joint.py --seeds 42 1 2 3 4     # full multi-seed
"""
import argparse
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from torch_geometric.utils import dense_to_sparse

import gae_joint as G   # validated module: GAEModel, constants, score_windows

# --- Pre-registered split (notebook cell 2 = the original joint-model contract) ---
TRAIN_SUBJS = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08",
               "chb09", "chb12", "chb19", "chb20", "chb21", "chb23"]
VAL_SUBJS = ["chb10", "chb11", "chb22"]
TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]


# ============================================================================
# Data: build one PyG Data per interictal window (normalisation == gae_joint.build_batch)
# ============================================================================
def make_window_data(A_np, X_np):
    A = torch.tensor(A_np, dtype=torch.float32)          # [18,18] raw
    Xt = torch.tensor(X_np, dtype=torch.float32)         # [18,5]  raw
    An = A / (A.amax() + 1e-8)
    Xn = (Xt - Xt.amin(dim=0, keepdim=True)) / (Xt.amax(dim=0, keepdim=True)
                                                - Xt.amin(dim=0, keepdim=True) + 1e-8)
    ei, ew = dense_to_sparse(A)                           # edges from RAW A
    x = torch.cat([An, Xn], dim=1)                        # [18,23]
    # store raw A and Xn as targets; dim0==18==num_nodes so PyG concatenates cleanly
    return Data(x=x, edge_index=ei, edge_attr=ew, A=A, Xn=Xn)


def load_subject(adj_dir, feat_dir, subj, suffix, max_windows=None):
    adjs = np.load(Path(adj_dir) / f"{subj}_interictal_adjs{suffix}.npy", mmap_mode="r")
    feats = np.load(Path(feat_dir) / f"{subj}_interictal_features.npy", mmap_mode="r")
    n = len(adjs) if max_windows is None else min(max_windows, len(adjs))
    return [make_window_data(np.asarray(adjs[i]), np.asarray(feats[i])) for i in range(n)]


def build_dataset(adj_dir, feat_dir, subjs, suffix, max_windows=None):
    t0 = time.time(); ds = []
    for s in subjs:
        w = load_subject(adj_dir, feat_dir, s, suffix, max_windows)
        ds.extend(w)
        print(f"  loaded {s}: {len(w)} interictal windows")
    print(f"  total {len(ds)} windows in {time.time()-t0:.1f}s")
    return ds


# ============================================================================
# Loss (VERIFIED joint objective) on a PyG batch
# ============================================================================
def batch_loss(model, batch, device):
    batch = batch.to(device)
    B = batch.num_graphs
    z = model.encoder(batch.x, batch.edge_index, batch.edge_attr)
    zpg = z.view(B, G.N_CH, G.LATENT_DIM)
    Ah = torch.clamp(torch.bmm(zpg, zpg.transpose(1, 2)), 0.0, 1.0)
    Xh = model.x_decoder(z).view(B, G.N_CH, G.N_BANDS)
    A = batch.A.view(B, G.N_CH, G.N_CH)
    Xn = batch.Xn.view(B, G.N_CH, G.N_BANDS)
    mse_A = ((A - Ah) ** 2).mean(dim=(1, 2))
    mse_X = ((Xn - Xh) ** 2).mean(dim=(1, 2))
    return (mse_A + G.LAMBDA * mse_X).mean()


def set_seed(seed):
    torch.manual_seed(seed); np.random.seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


# ============================================================================
# One seed
# ============================================================================
def train_seed(seed, train_ds, val_ds, epochs, batch, lr, device,
               adj_dir, feat_dir, suffix, out_dir):
    set_seed(seed)
    g = torch.Generator().manual_seed(seed)
    tl = DataLoader(train_ds, batch_size=batch, shuffle=True, generator=g)
    vl = DataLoader(val_ds, batch_size=batch, shuffle=False)

    model = G.GAEModel().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)

    tr_curve, va_curve = [], []
    for ep in range(epochs):
        model.train(); tot = 0.0; nb = 0
        for batch in tl:
            opt.zero_grad()
            loss = batch_loss(model, batch, device)
            loss.backward(); opt.step()
            tot += loss.item(); nb += 1
        sched.step()
        tr = tot / max(nb, 1)

        model.eval(); vtot = 0.0; vnb = 0
        with torch.no_grad():
            for batch in vl:
                vtot += batch_loss(model, batch, device).item(); vnb += 1
        va = vtot / max(vnb, 1)
        tr_curve.append(tr); va_curve.append(va)
        if ep < 3 or (ep + 1) % 20 == 0 or ep == epochs - 1:
            print(f"  [seed {seed}] epoch {ep+1:3}/{epochs}  train={tr:.6f}  val={va:.6f}")

    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    ckpt = out / f"gae_joint_seed{seed}.pt"
    torch.save(model.state_dict(), str(ckpt))
    np.savez(out / f"gae_loss_curves_seed{seed}.npz",
             train=np.array(tr_curve), val=np.array(va_curve))

    # immediate sanity: retrained model's chb13 recon AUROC (reuses validated scorer)
    from sklearn.metrics import roc_auc_score
    si = G.score_windows(model, Path(adj_dir) / f"chb13_interictal_adjs{suffix}.npy",
                         Path(feat_dir) / "chb13_interictal_features.npy", device)
    sc = G.score_windows(model, Path(adj_dir) / f"chb13_ictal_adjs{suffix}.npy",
                         Path(feat_dir) / "chb13_ictal_features.npy", device)
    auc = roc_auc_score(np.r_[np.zeros(len(si)), np.ones(len(sc))], np.r_[si, sc])
    print(f"  [seed {seed}] SAVED {ckpt.name} | final train={tr_curve[-1]:.6f} "
          f"val={va_curve[-1]:.6f} | chb13 AUROC={auc:.4f}")
    return auc


def main():
    ap = argparse.ArgumentParser()
    base = "/kaggle/input/datasets/nhn2mm"
    ap.add_argument("--adj_dir", default=f"{base}/chbmit-topk20")
    ap.add_argument("--feat_dir", default=f"{base}/chbmit-processed")
    ap.add_argument("--suffix", default="_topk20")
    ap.add_argument("--out_dir", default="/kaggle/working/gae_retrain")
    ap.add_argument("--epochs", type=int, default=200)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 1, 2, 3, 4])
    ap.add_argument("--smoke", action="store_true",
                    help="1 train + 1 val subject, 2 epochs, 2000 windows — verify loop only")
    a = ap.parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={device}")

    if a.smoke:
        tr_s, va_s, ep, seeds, maxw = TRAIN_SUBJS[:1], VAL_SUBJS[:1], 2, [42], 2000
        print("SMOKE MODE — loop check only, results not meaningful")
    else:
        tr_s, va_s, ep, seeds, maxw = TRAIN_SUBJS, VAL_SUBJS, a.epochs, a.seeds, None

    print("Building TRAIN dataset (interictal, 12 subjects) ...")
    train_ds = build_dataset(a.adj_dir, a.feat_dir, tr_s, a.suffix, maxw)
    print("Building VAL dataset (interictal, 3 held-out subjects) ...")
    val_ds = build_dataset(a.adj_dir, a.feat_dir, va_s, a.suffix, maxw)

    results = {}
    for s in seeds:
        print(f"\n=== SEED {s} ===")
        results[s] = train_seed(s, train_ds, val_ds, ep, a.batch, a.lr, device,
                                a.adj_dir, a.feat_dir, a.suffix, a.out_dir)
    print("\nDONE. chb13 AUROC per seed:", {k: round(v, 4) for k, v in results.items()})


if __name__ == "__main__":
    main()
