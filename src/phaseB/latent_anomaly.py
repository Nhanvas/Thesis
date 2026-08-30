"""
latent_anomaly.py — E2. Score seizure anomaly by DISTANCE in the GAE latent space
(Mahalanobis to the interictal manifold) instead of reconstruction MSE. Tests whether the
GAE representation separates ictal even where recon magnitude inverts (chb10: ictal
reconstructs *better* due to hypersynchrony -> recon-MSE has the wrong polarity).

GAE-only: needs the baseline GAE ckpt + adj(_topk20) + features. No LSTM, no gamma.
VAL only (chb10/11/22); TEST guarded. Prints recon-AUROC (reference) vs latent-AUROC/AUPRC.

Usage (Kaggle):
    python latent_anomaly.py --gae_dir /kaggle/input/datasets/norncreades/gae-s5 \
        --adj_dir /kaggle/input/datasets/nhn2mm/chbmit-topk20 \
        --feat_dir /kaggle/input/datasets/nhn2mm/chbmit-processed
"""
import argparse, os, shutil, zipfile
from pathlib import Path
import numpy as np
import torch
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.covariance import LedoitWolf
import gae_joint as G

VAL = ["chb10", "chb11", "chb22"]
TEST = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}


def rebuild_ckpt(root, marker="gae_joint_seed42", out="/kaggle/working/gae_joint_seed42.pt"):
    if os.path.exists(out) and zipfile.is_zipfile(out):
        return out
    for r, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(r, f)
            if marker in f and f.endswith(".pt") and zipfile.is_zipfile(p):
                return p
    cands = [r for r, _, fs in os.walk(root) if "data.pkl" in fs and marker in r]
    assert cands, f"no gae ckpt archive (marker '{marker}') under {root}"
    arch = cands[0]; parent, name = os.path.dirname(arch), os.path.basename(arch)
    z = shutil.make_archive(out[:-3], "zip", root_dir=parent, base_dir=name); os.replace(z, out)
    return out


def latent_pool(model, adj_path, feat_path, device, batch=512):
    adjs = np.load(adj_path, mmap_mode="r"); feats = np.load(feat_path, mmap_mode="r")
    Z = []; model.eval()
    with torch.no_grad():
        for s in range(0, len(adjs), batch):
            e = min(s + batch, len(adjs))
            A = torch.tensor(adjs[s:e].astype(np.float32)); Xt = torch.tensor(feats[s:e].astype(np.float32))
            pg, A, Xn, B = G.build_batch(A, Xt, device)
            z = model.encoder(pg.x, pg.edge_index, pg.edge_attr).view(B, G.N_CH, G.LATENT_DIM)
            Z.append(z.mean(dim=1).cpu().numpy().astype(np.float32))   # graph-level [B,16]
    return np.concatenate(Z, 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gae_dir", default="/kaggle/input/datasets/norncreades/gae-s5")
    ap.add_argument("--ckpt", default=None, help="explicit .pt (e.g. a retrained gae_compact); skips rebuild")
    ap.add_argument("--adj_dir", default="/kaggle/input/datasets/nhn2mm/chbmit-topk20")
    ap.add_argument("--feat_dir", default="/kaggle/input/datasets/nhn2mm/chbmit-processed")
    ap.add_argument("--suffix", default="_topk20")
    ap.add_argument("--subjs", nargs="+", default=VAL)
    a = ap.parse_args()
    leak = [s for s in a.subjs if s in TEST]
    if leak:
        raise SystemExit(f"INTEGRITY ABORT: TEST subject(s) {leak} — VAL only.")

    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = a.ckpt if a.ckpt else rebuild_ckpt(a.gae_dir)
    print("ckpt ->", ckpt, "| device", dev)
    model = G.load_checkpoint(ckpt, dev)

    print(f"\n{'subj':8}{'recon_AU':>10}{'latent_AU':>11}{'latent_AP':>11}{'n_int':>8}{'n_ict':>8}")
    rA, lA, lP = [], [], []
    for s in a.subjs:
        ai = Path(a.adj_dir) / f"{s}_interictal_adjs{a.suffix}.npy"
        ac = Path(a.adj_dir) / f"{s}_ictal_adjs{a.suffix}.npy"
        fi = Path(a.feat_dir) / f"{s}_interictal_features.npy"
        fc = Path(a.feat_dir) / f"{s}_ictal_features.npy"
        # recon branch (reference)
        ri = G.score_windows(model, ai, fi, dev); rc = G.score_windows(model, ac, fc, dev)
        y = np.r_[np.zeros(len(ri)), np.ones(len(rc))]
        rauc = roc_auc_score(y, np.r_[ri, rc])
        # latent Mahalanobis (fit interictal manifold, score both)
        Zi = latent_pool(model, ai, fi, dev); Zc = latent_pool(model, ac, fc, dev)
        cov = LedoitWolf().fit(Zi)
        di, dc = cov.mahalanobis(Zi), cov.mahalanobis(Zc)
        y2 = np.r_[np.zeros(len(di)), np.ones(len(dc))]; s2 = np.r_[di, dc]
        lauc = roc_auc_score(y2, s2); lap = average_precision_score(y2, s2)
        rA.append(rauc); lA.append(lauc); lP.append(lap)
        print(f"{s:8}{rauc:10.4f}{lauc:11.4f}{lap:11.4f}{len(di):8d}{len(dc):8d}")
    print(f"\n{'MACRO':8}{np.mean(rA):10.4f}{np.mean(lA):11.4f}{np.mean(lP):11.4f}")
    print("\nRef: recon macro ~0.592, chb10 0.268 (inverted).")
    print("KEEP latent-score if chb10 latent_AU > 0.5 AND latent macro >= recon macro.")


if __name__ == "__main__":
    main()
