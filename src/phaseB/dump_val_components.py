"""
dump_val_components.py — KAGGLE GPU. Generate per-branch robust-z components for VAL
(chb10/11/22), seed 42, for branch_ablation.py (E1 + latent integration test).
Saves 4 branches: zrecon, ztemp, zgamma (validated build_subject_components) and
zlatent (robust-z of GAE latent-space Mahalanobis distance — the E2 winner).

Robust to Kaggle unzipping .pt into folders (marker-based rebuild). Explicit paths only.

USAGE (Kaggle GPU):
    python dump_val_components.py --gae_dir <gae-s5> --lstm_dir <gae-s5> \
        --gamma_dir <auto> --adj_dir <topk20> --feat_dir <processed>
"""
import argparse, os, shutil, zipfile
from pathlib import Path
import numpy as np
import retrain_io as IO

VAL = ["chb10", "chb11", "chb22"]
TEST = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}


def rebuild_ckpt(root, marker, out):
    if os.path.exists(out) and zipfile.is_zipfile(out):
        return out
    for r, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(r, f)
            if marker in f and f.endswith(".pt") and zipfile.is_zipfile(p):
                return p
    cands = [r for r, _, fs in os.walk(root) if "data.pkl" in fs and marker in r]
    assert cands, f"no ckpt archive for marker '{marker}' under {root}"
    arch = cands[0]; parent, name = os.path.dirname(arch), os.path.basename(arch)
    z = shutil.make_archive(out[:-3], "zip", root_dir=parent, base_dir=name); os.replace(z, out)
    return out


def latent_pool(model, adj_path, feat_path, device, G, batch=512):
    import torch
    adjs = np.load(adj_path, mmap_mode="r"); feats = np.load(feat_path, mmap_mode="r")
    Z = []; model.eval()
    with torch.no_grad():
        for s in range(0, len(adjs), batch):
            e = min(s + batch, len(adjs))
            A = torch.tensor(adjs[s:e].astype(np.float32)); Xt = torch.tensor(feats[s:e].astype(np.float32))
            pg, A, Xn, B = G.build_batch(A, Xt, device)
            z = model.encoder(pg.x, pg.edge_index, pg.edge_attr).view(B, G.N_CH, G.LATENT_DIM)
            Z.append(z.mean(dim=1).cpu().numpy().astype(np.float32))
    return np.concatenate(Z, 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gae_dir", default="/kaggle/input/datasets/norncreades/gae-s5")
    ap.add_argument("--lstm_dir", default="/kaggle/input/datasets/norncreades/gae-s5")
    ap.add_argument("--gamma_dir", required=True)
    ap.add_argument("--adj_dir", default="/kaggle/input/datasets/nhn2mm/chbmit-topk20")
    ap.add_argument("--feat_dir", default="/kaggle/input/datasets/nhn2mm/chbmit-processed")
    ap.add_argument("--suffix", default="_topk20")
    ap.add_argument("--subjects", default=",".join(VAL))
    ap.add_argument("--out_dir", default="/kaggle/working/val_components")
    a = ap.parse_args()

    subjs = a.subjects.split(",")
    leak = [s for s in subjs if s in TEST]
    if leak:
        raise SystemExit(f"INTEGRITY ABORT: TEST subject(s) {leak} — dump VAL only.")

    import torch
    from sklearn.covariance import LedoitWolf
    import gae_joint as G
    import lstm_temporal as T
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={dev}  subjects={subjs}")

    gae_pt = rebuild_ckpt(a.gae_dir, "gae_joint_seed42", "/kaggle/working/gae_joint_seed42.pt")
    lstm_pt = rebuild_ckpt(a.lstm_dir, "lstm_temporal_seed42", "/kaggle/working/lstm_temporal_seed42.pt")
    print("gae  ckpt ->", gae_pt); print("lstm ckpt ->", lstm_pt)

    gae = G.GAEModel().to(dev)
    gsd = torch.load(gae_pt, map_location=dev); gae.load_state_dict(gsd.get("state_dict", gsd), strict=True); gae.eval()
    lstm = T.LSTMPredictor(in_dim=18 * 16).to(dev)
    lsd = torch.load(lstm_pt, map_location=dev); lstm.load_state_dict(lsd.get("state_dict", lsd), strict=True); lstm.eval()

    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    for subj in subjs:
        # 3 validated branches
        comp = IO.build_subject_components(gae, lstm, subj, a.adj_dir, a.feat_dir, a.gamma_dir, a.suffix, dev)
        for key, (zi, zc) in comp.items():
            np.save(out / f"{key}_{subj}_inter.npy", np.asarray(zi, dtype=np.float32))
            np.save(out / f"{key}_{subj}_ictal.npy", np.asarray(zc, dtype=np.float32))
        # latent branch (E2 winner): robust-z of Mahalanobis to interictal manifold
        ai = Path(a.adj_dir) / f"{subj}_interictal_adjs{a.suffix}.npy"
        ac = Path(a.adj_dir) / f"{subj}_ictal_adjs{a.suffix}.npy"
        fi = Path(a.feat_dir) / f"{subj}_interictal_features.npy"
        fc = Path(a.feat_dir) / f"{subj}_ictal_features.npy"
        Zi = latent_pool(gae, ai, fi, dev, G); Zc = latent_pool(gae, ac, fc, dev, G)
        cov = LedoitWolf().fit(Zi)
        di, dc = cov.mahalanobis(Zi).astype(np.float64), cov.mahalanobis(Zc).astype(np.float64)
        zli, zlc = IO.robust_z(di, dc)
        np.save(out / f"zlatent_{subj}_inter.npy", np.asarray(zli, dtype=np.float32))
        np.save(out / f"zlatent_{subj}_ictal.npy", np.asarray(zlc, dtype=np.float32))
        print(f"  {subj}: saved zrecon/ztemp/zgamma/zlatent  n_inter={len(zli)} n_ictal={len(zlc)}")
    print(f"\nDONE -> {out}. Next: python branch_ablation.py --comp {out}")


if __name__ == "__main__":
    main()
