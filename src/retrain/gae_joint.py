"""
gae_joint.py — Reconstructed joint-GAE model class + verified scoring.

PURPOSE (PHA 1, code artifact #1): reconstruct the joint-GAE architecture as a clean,
importable module and PROVE it is byte-compatible with the retained checkpoint
`best_model_joint_lambda01.pt` BEFORE any training code is written. If this module loads
the checkpoint with strict=True and reproduces the chb13 sanity AUROC (~0.836), the class
is correct and the only remaining unknown is the training loop.

Architecture + scoring are VERIFIED against thesis-cpd-final.ipynb (cells 2/4/5/7) and the
checkpoint state_dict keys:
    encoder.conv1.lin.weight (64,23) · encoder.conv2.lin.weight (16,64)
    x_decoder.net.0 (32,16) · x_decoder.net.2 (5,32)

Run on Kaggle (GPU + graph datasets present). CPU works too but is slow.
    python gae_joint.py --validate
"""
import argparse
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch_geometric.nn import GCNConv
from torch_geometric.data import Data, Batch as PyGBatch
from torch_geometric.utils import dense_to_sparse

# --- Constants (pinned from notebook cell 2; do NOT change) ------------------
INPUT_DIM, HIDDEN_DIM, LATENT_DIM = 23, 64, 16
N_CH, N_BANDS = 18, 5
LAMBDA = 0.1                      # joint loss: MSE(A_raw, Â) + LAMBDA * MSE(Xn, X̂)
BIAS_FINGERPRINT = 0.8676        # encoder.conv1.bias.abs().max() of the trained checkpoint


# ============================================================================
# MODEL  (module names chosen to match the checkpoint state_dict exactly)
# ============================================================================
class GAEEncoder(nn.Module):
    def __init__(self, in_dim=INPUT_DIM, hid=HIDDEN_DIM, lat=LATENT_DIM):
        super().__init__()
        self.conv1 = GCNConv(in_dim, hid)
        self.conv2 = GCNConv(hid, lat)
        self.relu = nn.ReLU()

    def forward(self, x, edge_index, edge_weight=None):
        h = self.relu(self.conv1(x, edge_index, edge_weight))
        return self.conv2(h, edge_index, edge_weight)


class XDecoder(nn.Module):
    """MLP 16 -> 32 -> 5. net.0 = Linear(16,32), net.1 = ReLU, net.2 = Linear(32,5)."""
    def __init__(self, lat=LATENT_DIM, hid=32, bands=N_BANDS):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(lat, hid), nn.ReLU(), nn.Linear(hid, bands))

    def forward(self, z):
        return self.net(z)


class GAEModel(nn.Module):
    def __init__(self, in_dim=INPUT_DIM, hid=HIDDEN_DIM, lat=LATENT_DIM, bands=N_BANDS):
        super().__init__()
        self.encoder = GAEEncoder(in_dim, hid, lat)
        self.x_decoder = XDecoder(lat, 32, bands)

    def forward(self, x, edge_index, edge_weight, batch_size, n_ch=N_CH):
        """Returns (z, A_hat, X_hat). Used for TRAINING (loss needs both heads).
        Inference reuses encoder + x_decoder directly (see score_windows)."""
        z = self.encoder(x, edge_index, edge_weight)
        zpg = z.view(batch_size, n_ch, -1)
        A_hat = torch.clamp(torch.bmm(zpg, zpg.transpose(1, 2)), 0.0, 1.0)
        X_hat = self.x_decoder(z).view(batch_size, n_ch, -1)
        return z, A_hat, X_hat


# ============================================================================
# INPUT CONSTRUCTION  (VERIFIED — identical for train and inference)
# ============================================================================
def build_batch(A, Xt, device):
    """A:[B,18,18] raw, Xt:[B,18,5] raw -> PyG batch + normalised targets (An unused as
    target; A_raw is the A-reconstruction target, Xn is the X target)."""
    A = A.to(device); Xt = Xt.to(device)
    An = A / (A.amax(dim=(1, 2), keepdim=True) + 1e-8)          # node-feat only
    Xmn = Xt.amin(dim=1, keepdim=True); Xmx = Xt.amax(dim=1, keepdim=True)
    Xn = (Xt - Xmn) / (Xmx - Xmn + 1e-8)                        # per-window, per-band
    B = A.shape[0]
    dl = [Data(x=torch.cat([An[b], Xn[b]], dim=1),
               edge_index=dense_to_sparse(A[b])[0],
               edge_attr=dense_to_sparse(A[b])[1]) for b in range(B)]   # edges from RAW A
    pg = PyGBatch.from_data_list(dl).to(device)
    return pg, A, Xn, B


def joint_score(model, pg, A, Xn, B, per_node=False):
    """Joint reconstruction score. per_node=False -> scalar [B]; True -> [B,18]."""
    z = model.encoder(pg.x, pg.edge_index, pg.edge_attr)
    zpg = z.view(B, N_CH, LATENT_DIM)
    Ah = torch.clamp(torch.bmm(zpg, zpg.transpose(1, 2)), 0.0, 1.0)
    Xh = model.x_decoder(z).view(B, N_CH, N_BANDS)
    if per_node:
        return (((A - Ah) ** 2).mean(dim=2) + LAMBDA * ((Xn - Xh) ** 2).mean(dim=2))
    return (((A - Ah) ** 2).mean(dim=(1, 2)) + LAMBDA * ((Xn - Xh) ** 2).mean(dim=(1, 2)))


def score_windows(model, adj_path, feat_path, device, batch_size=512, per_node=False):
    """Raw joint MSE score per window (NOT z-normalised). Mirrors notebook cells 5/7/8."""
    adjs = np.load(adj_path, mmap_mode="r")
    feats = np.load(feat_path, mmap_mode="r")
    out = []
    model.eval()
    with torch.no_grad():
        for s in range(0, len(adjs), batch_size):
            e = min(s + batch_size, len(adjs))
            A = torch.tensor(adjs[s:e].astype(np.float32))
            Xt = torch.tensor(feats[s:e].astype(np.float32))
            pg, A, Xn, B = build_batch(A, Xt, device)
            sc = joint_score(model, pg, A, Xn, B, per_node=per_node)
            out.append(sc.cpu().numpy().astype(np.float32))
    return np.concatenate(out, axis=0)


def load_checkpoint(model_path, device):
    model = GAEModel().to(device)
    state = torch.load(str(model_path), map_location=device)
    state = state.get("state_dict", state)
    model.load_state_dict(state, strict=True)      # strict=True proves key/shape match
    model.eval()
    return model


# ============================================================================
# VALIDATION  (the whole point of this artifact)
# ============================================================================
def validate(adj_dir, feat_dir, model_path, suffix, device, batch_size):
    from sklearn.metrics import roc_auc_score
    print(f"device={device}")
    model = load_checkpoint(model_path, device)
    print("strict load: OK (all keys/shapes match reconstructed class)")

    bmax = model.encoder.conv1.bias.abs().max().item()
    print(f"bias fingerprint = {bmax:.4f}  (expect ~{BIAS_FINGERPRINT})")
    assert bmax > 0.005, "random-init detected — wrong checkpoint"

    adj_dir, feat_dir = Path(adj_dir), Path(feat_dir)
    si = score_windows(model, adj_dir / f"chb13_interictal_adjs{suffix}.npy",
                       feat_dir / "chb13_interictal_features.npy", device, batch_size)
    sc = score_windows(model, adj_dir / f"chb13_ictal_adjs{suffix}.npy",
                       feat_dir / "chb13_ictal_features.npy", device, batch_size)
    y = np.concatenate([np.zeros(len(si)), np.ones(len(sc))])
    auc = roc_auc_score(y, np.concatenate([si, sc]))
    print(f"chb13 recon AUROC = {auc:.4f}  (expect ~0.836)")

    # per-node self-consistency (cell-8 check)
    pn = score_windows(model, adj_dir / f"chb13_interictal_adjs{suffix}.npy",
                       feat_dir / "chb13_interictal_features.npy", device, batch_size,
                       per_node=True)
    err = float(np.max(np.abs(pn.mean(axis=1) - si)))
    print(f"per-node self-check max|mean_node - scalar| = {err:.2e}  (expect < 1e-5)")

    ok = (bmax > 0.5) and (auc >= 0.78) and (err < 1e-5)
    print("\nCLASS VALIDATION:", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--adj_dir", default="/kaggle/input/datasets/nhn2mm/chbmit-topk20")
    ap.add_argument("--feat_dir", default="/kaggle/input/datasets/nhn2mm/chbmit-processed")
    ap.add_argument("--model", default="/kaggle/input/datasets/nhn2mm/gae-joint-model/best_model_joint_lambda01.pt")
    ap.add_argument("--suffix", default="_topk20")
    ap.add_argument("--batch_size", type=int, default=512)
    ap.add_argument("--validate", action="store_true")
    a = ap.parse_args()
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if a.validate:
        validate(a.adj_dir, a.feat_dir, a.model, a.suffix, dev, a.batch_size)
    else:
        print("Pass --validate to run the checkpoint validation.")
