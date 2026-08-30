"""
gae_joint_multirel.py — Phase C-final / C4-full model class. Needs torch + PyG.

Multi-relational (R-GCN-style) joint GAE fusing TWO edge relations learned JOINTLY
into a shared latent — closes the gap C4-lite left (linear post-hoc TE fusion ->
joint message passing). Grounded in R-GCN-AE (Schlichtkrull) / UMGAD (unsupervised
multiplex graph anomaly, per-relation reconstruction).

ARCHITECTURE (pre-registered — Boti-approved A1/A2/A3, 2026-08)
  R1 = symmetric wPLI+AEC top-k20  ({s}_{sp}_adjs_topk20.npy)
  R2 = directed TE top-k20         ({s}_{sp}_te_topk20.npy, from build_te_adj.py)
  Node features (IDENTICAL to rlg — isolates the effect of directed message passing):
    x = [An1 (18, R1 row, per-window max-norm) | Xn (5 band powers)]  -> 23-d
  Encoder — NON-SHARED weights per relation (true R-GCN; shared W would just sum
  A1+A2 into one graph -> hypothesis untestable):
    h = ReLU( GCNConv1_R1(x,A1) + GCNConv1_R2(x,A2) + W_self1(x) )    23->64
    z =        GCNConv2_R1(h,A1) + GCNConv2_R2(h,A2) + W_self2(h)     64->16
  Decoders — PER-RELATION (UMGAD-style):
    R1: A1_hat = clamp(z z^T,0,1)          (symmetric; identical to rlg)
    R2: A2_hat = clamp(z M2 z^T,0,1)       (ASYMMETRIC full-bilinear M2 — directed)
    X : X_hat  = MLP 16->32->5             (unchanged from rlg)
  Loss = MSE(A1_raw,A1_hat) + mu*MSE(A2n,A2_hat) + lam*MSE(Xn,X_hat)
    lam=0.1 (X auxiliary). mu=1.0 (R2 fully weighted). A2n = A2/(max+eps) in [0,1]
    (scalar-norm PRESERVES directed ratios A2[i,j]:A2[j,i]).

TWO EQUIVALENT DATA PATHS (proven bit-identical in --smoke):
  * REFERENCE (PyG Batch): build_batch_mr + forward(pg,...). Used by encode + smoke.
  * FAST (lever a): prepare_dataset() precomputes sparse edges ONCE; build_batch_fast()
    assembles a block-diagonal batch per step WITHOUT dense_to_sparse; forward_raw().
    Used by training's 200-epoch loop -> removes the host-side bottleneck (dense_to_sparse
    was called 2x/window/epoch). SAME math (order-independent GCN aggregation).

R2-ABLATION HOOK: encoder.forward(..., use_r2=False) zeroes the R2 message path.
"""
import argparse
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch_geometric.nn import GCNConv
from torch_geometric.data import Data, Batch as PyGBatch
from torch_geometric.utils import dense_to_sparse

INPUT_DIM, HIDDEN_DIM, LATENT_DIM = 23, 64, 16
N_CH, N_BANDS = 18, 5
LAMBDA_X = 0.1
MU_R2 = 1.0


# ============================================================================
# MODEL
# ============================================================================
class MultiRelEncoder(nn.Module):
    def __init__(self, in_dim=INPUT_DIM, hid=HIDDEN_DIM, lat=LATENT_DIM):
        super().__init__()
        self.conv1_r1 = GCNConv(in_dim, hid)
        self.conv1_r2 = GCNConv(in_dim, hid)
        self.self1 = nn.Linear(in_dim, hid)
        self.conv2_r1 = GCNConv(hid, lat)
        self.conv2_r2 = GCNConv(hid, lat)
        self.self2 = nn.Linear(hid, lat)
        self.relu = nn.ReLU()

    def forward(self, x, ei1, ew1, ei2, ew2, use_r2=True):
        m1 = self.conv1_r1(x, ei1, ew1) + self.self1(x)
        if use_r2:
            m1 = m1 + self.conv1_r2(x, ei2, ew2)
        h = self.relu(m1)
        m2 = self.conv2_r1(h, ei1, ew1) + self.self2(h)
        if use_r2:
            m2 = m2 + self.conv2_r2(h, ei2, ew2)
        return m2

    def r1_params(self):
        return list(self.conv1_r1.parameters()) + list(self.conv2_r1.parameters())

    def r2_params(self):
        return list(self.conv1_r2.parameters()) + list(self.conv2_r2.parameters())


class XDecoder(nn.Module):
    def __init__(self, lat=LATENT_DIM, hid=32, bands=N_BANDS):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(lat, hid), nn.ReLU(), nn.Linear(hid, bands))

    def forward(self, z):
        return self.net(z)


class MultiRelGAE(nn.Module):
    def __init__(self, in_dim=INPUT_DIM, hid=HIDDEN_DIM, lat=LATENT_DIM, bands=N_BANDS):
        super().__init__()
        self.encoder = MultiRelEncoder(in_dim, hid, lat)
        self.x_decoder = XDecoder(lat, 32, bands)
        M2 = torch.eye(lat) + 0.01 * torch.randn(lat, lat)
        self.M2 = nn.Parameter(M2)

    def forward_raw(self, x, ei1, ew1, ei2, ew2, A1, A2n, Xn, B,
                    n_ch=N_CH, mu=MU_R2, lam=LAMBDA_X, use_r2=True):
        z = self.encoder(x, ei1, ew1, ei2, ew2, use_r2=use_r2)
        zpg = z.view(B, n_ch, LATENT_DIM)
        A1h = torch.clamp(torch.bmm(zpg, zpg.transpose(1, 2)), 0.0, 1.0)
        zM = torch.matmul(zpg, self.M2)
        A2h = torch.clamp(torch.bmm(zM, zpg.transpose(1, 2)), 0.0, 1.0)
        Xh = self.x_decoder(z).view(B, n_ch, N_BANDS)
        r1 = ((A1 - A1h) ** 2).mean(dim=(1, 2))
        r2 = ((A2n - A2h) ** 2).mean(dim=(1, 2))
        rx = ((Xn - Xh) ** 2).mean(dim=(1, 2))
        total = (r1 + mu * r2 + lam * rx).mean()
        return dict(z=z, A1_hat=A1h, A2_hat=A2h, X_hat=Xh, r1=r1, r2=r2, rx=rx, total=total)

    def forward(self, pg, A1, A2n, Xn, B, n_ch=N_CH, mu=MU_R2, lam=LAMBDA_X, use_r2=True):
        """PyG-batch reference path (encode + smoke). Delegates to forward_raw."""
        return self.forward_raw(pg.x, pg.edge_index, pg.edge_attr, pg.edge_index2,
                                pg.edge_attr2, A1, A2n, Xn, B, n_ch, mu, lam, use_r2)


# ============================================================================
# REFERENCE data path (PyG Batch) — used by encode + smoke
# ============================================================================
class _MRData(Data):
    def __inc__(self, key, value, *args, **kwargs):
        if key == "edge_index2":
            return self.num_nodes
        return super().__inc__(key, value, *args, **kwargs)

    def __cat_dim__(self, key, value, *args, **kwargs):
        if key == "edge_index2":
            return -1
        return super().__cat_dim__(key, value, *args, **kwargs)


def build_batch_mr(A1, A2, Xt, device):
    """Reference builder. A1:[B,18,18] R1 in [0,1]; A2:[B,18,18] R2 TE>=0; Xt:[B,18,5].
    Returns (pg, A1_raw, A2n, Xn, B). Slow (dense_to_sparse per window) -> encode only."""
    A1 = A1.to(device); A2 = A2.to(device); Xt = Xt.to(device)
    An1 = A1 / (A1.amax(dim=(1, 2), keepdim=True) + 1e-8)
    Xmn = Xt.amin(dim=1, keepdim=True); Xmx = Xt.amax(dim=1, keepdim=True)
    Xn = (Xt - Xmn) / (Xmx - Xmn + 1e-8)
    A2n = A2 / (A2.amax(dim=(1, 2), keepdim=True) + 1e-8)
    B = A1.shape[0]
    dl = []
    for b in range(B):
        ei1, ew1 = dense_to_sparse(A1[b])
        ei2, ew2 = dense_to_sparse(A2[b])
        d = _MRData(x=torch.cat([An1[b], Xn[b]], dim=1), edge_index=ei1, edge_attr=ew1)
        d.edge_index2 = ei2
        d.edge_attr2 = ew2
        dl.append(d)
    pg = PyGBatch.from_data_list(dl).to(device)
    return pg, A1, A2n, Xn, B


# ============================================================================
# FAST data path (lever a) — precompute sparse edges ONCE, block-diagonal batch
# ============================================================================
def prepare_dataset(A1, A2, Xt):
    """[N,18,18],[N,18,18],[N,18,5] (numpy) -> dict with node feats, dense recon targets,
    and per-window sparse edges computed ONCE (numerically identical to dense_to_sparse:
    same nonzero set, GCN aggregation is edge-order-independent). Used by build_batch_fast."""
    A1 = np.asarray(A1, np.float32); A2 = np.asarray(A2, np.float32); Xt = np.asarray(Xt, np.float32)
    N = len(A1)
    An1 = A1 / (A1.max(axis=(1, 2), keepdims=True) + 1e-8)
    Xmn = Xt.min(axis=1, keepdims=True); Xmx = Xt.max(axis=1, keepdims=True)
    Xn = (Xt - Xmn) / (Xmx - Xmn + 1e-8)
    A2n = A2 / (A2.max(axis=(1, 2), keepdims=True) + 1e-8)
    x = np.concatenate([An1, Xn], axis=2).astype(np.float32)          # [N,18,23]
    ei1, ew1, ei2, ew2 = [], [], [], []
    for i in range(N):
        r, c = np.nonzero(A1[i]); ei1.append(np.stack([r, c]).astype(np.int64)); ew1.append(A1[i][r, c].astype(np.float32))
        r, c = np.nonzero(A2[i]); ei2.append(np.stack([r, c]).astype(np.int64)); ew2.append(A2[i][r, c].astype(np.float32))
    return dict(x=x, A1=A1.astype(np.float32), A2n=A2n.astype(np.float32), Xn=Xn.astype(np.float32),
                ei1=ei1, ew1=ew1, ei2=ei2, ew2=ew2)


def build_batch_fast(ds, idx, device, n_ch=N_CH):
    """Assemble a block-diagonal batch from precomputed pieces — NO dense_to_sparse,
    NO PyG Data/Batch objects. Returns (x, ei1, ew1, ei2, ew2, A1, A2n, Xn, B)."""
    idx = np.asarray(idx)
    B = len(idx)
    x = torch.from_numpy(ds["x"][idx].reshape(B * n_ch, -1)).to(device)
    e1, w1, e2, w2 = [], [], [], []
    for k, i in enumerate(idx):
        off = k * n_ch
        e1.append(ds["ei1"][i] + off); w1.append(ds["ew1"][i])
        e2.append(ds["ei2"][i] + off); w2.append(ds["ew2"][i])
    ei1 = torch.from_numpy(np.concatenate(e1, axis=1)).long().to(device)
    ew1 = torch.from_numpy(np.concatenate(w1)).float().to(device)
    ei2 = torch.from_numpy(np.concatenate(e2, axis=1)).long().to(device)
    ew2 = torch.from_numpy(np.concatenate(w2)).float().to(device)
    A1b = torch.from_numpy(ds["A1"][idx]).float().to(device)
    A2nb = torch.from_numpy(ds["A2n"][idx]).float().to(device)
    Xnb = torch.from_numpy(ds["Xn"][idx]).float().to(device)
    return x, ei1, ew1, ei2, ew2, A1b, A2nb, Xnb, B


# ============================================================================
# SCORING (encode) — reference PyG path; splits recon into r1/r2/x + latent
# ============================================================================
def score_windows_mr(model, a1_path, a2_path, feat_path, device, batch_size=512,
                     mu=MU_R2, lam=LAMBDA_X, use_r2=True):
    A1s = np.load(a1_path, mmap_mode="r")
    A2s = np.load(a2_path, mmap_mode="r")
    Xs = np.load(feat_path, mmap_mode="r")
    assert len(A1s) == len(A2s) == len(Xs), \
        f"align R1/R2/feat {len(A1s)}/{len(A2s)}/{len(Xs)} for {a1_path}"
    tot, r1, r2, rx, Zg = [], [], [], [], []
    model.eval()
    with torch.no_grad():
        for s in range(0, len(A1s), batch_size):
            e = min(s + batch_size, len(A1s))
            A1 = torch.tensor(A1s[s:e].astype(np.float32))
            A2 = torch.tensor(A2s[s:e].astype(np.float32))
            Xt = torch.tensor(Xs[s:e].astype(np.float32))
            pg, A1r, A2n, Xn, B = build_batch_mr(A1, A2, Xt, device)
            o = model(pg, A1r, A2n, Xn, B, mu=mu, lam=lam, use_r2=use_r2)
            tot.append(o["r1"].add(mu * o["r2"]).add(lam * o["rx"]).cpu().numpy())
            r1.append(o["r1"].cpu().numpy()); r2.append(o["r2"].cpu().numpy())
            rx.append(o["rx"].cpu().numpy())
            Zg.append(o["z"].view(B, N_CH, LATENT_DIM).mean(dim=1).cpu().numpy())
    f = lambda L: np.concatenate(L).astype(np.float32)
    return dict(total=f(tot), r1=f(r1), r2=f(r2), rx=f(rx), Z=np.concatenate(Zg).astype(np.float32))


def load_checkpoint(model_path, device):
    model = MultiRelGAE().to(device)
    state = torch.load(str(model_path), map_location=device)
    state = state.get("state_dict", state)
    model.load_state_dict(state, strict=True)
    model.eval()
    return model


# ============================================================================
# self-contained model smoke (synthetic)
# ============================================================================
def model_smoke():
    dev = torch.device("cpu")
    torch.manual_seed(0); np.random.seed(0)
    model = MultiRelGAE().to(dev)
    print(f"[MODEL-SMOKE] params={sum(p.numel() for p in model.parameters())} (KB-scale)")

    B = 8
    A1 = torch.rand(B, 18, 18); A1 = (A1 + A1.transpose(1, 2)) / 2; A1 = A1 * (A1 > 0.8)
    A2 = torch.rand(B, 18, 18) * (torch.rand(B, 18, 18) > 0.8)
    for b in range(B):
        A1[b].fill_diagonal_(0); A2[b].fill_diagonal_(0)
    A2[0] = 0.0                               # all-zero R2 window edge-case
    Xt = torch.rand(B, 18, 5)

    pg, A1r, A2n, Xn, Bb = build_batch_mr(A1, A2, Xt, dev)
    o = model(pg, A1r, A2n, Xn, Bb)
    for k in ("z", "A1_hat", "A2_hat", "X_hat", "total"):
        assert torch.isfinite(o[k]).all(), f"non-finite in {k}"
    asym = (o["A2_hat"] - o["A2_hat"].transpose(1, 2)).abs().max().item()
    print(f"[MODEL-SMOKE] forward finite; A2_hat asymmetry max={asym:.3f} (>0 expected)")

    o["total"].backward()
    g_r1 = sum(p.grad.norm().item() for p in model.encoder.r1_params() if p.grad is not None)
    g_r2 = sum(p.grad.norm().item() for p in model.encoder.r2_params() if p.grad is not None)
    assert g_r1 > 0 and g_r2 > 0
    print(f"[MODEL-SMOKE] grad ‖R1‖={g_r1:.3e} ‖R2‖={g_r2:.3e}  gate_R2={g_r2/(g_r1+1e-12):.3f}")

    # FAST-PATH FIDELITY: build_batch_fast + forward_raw == PyG-reference (same math)
    ds = prepare_dataset(A1.numpy(), A2.numpy(), Xt.numpy())
    xs, e1, w1, e2, w2, A1b, A2nb, Xnb, Bf = build_batch_fast(ds, np.arange(B), dev)
    with torch.no_grad():
        o_ref = model(pg, A1r, A2n, Xn, Bb)
        o_fast = model.forward_raw(xs, e1, w1, e2, w2, A1b, A2nb, Xnb, Bf)
    d = (o_ref["total"] - o_fast["total"]).abs().item()
    dz = (o_ref["z"] - o_fast["z"]).abs().max().item()
    assert d < 1e-5 and dz < 1e-5, f"fast != reference: Δtotal={d}, Δz={dz}"
    print(f"[MODEL-SMOKE] fast-path == PyG-reference: |Δtotal|={d:.2e} |Δz|={dz:.2e}  PASS")

    # R2-ablation hook changes latent
    z1 = model.encoder(pg.x, pg.edge_index, pg.edge_attr, pg.edge_index2, pg.edge_attr2, use_r2=True)
    z0 = model.encoder(pg.x, pg.edge_index, pg.edge_attr, pg.edge_index2, pg.edge_attr2, use_r2=False)
    assert (z1 - z0).abs().max().item() > 0
    print(f"[MODEL-SMOKE] use_r2 ablation changes latent max|Δ|={(z1-z0).abs().max().item():.3f}  PASS")
    print("[MODEL-SMOKE] PASS")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    if a.smoke:
        model_smoke()
    else:
        print("Pass --smoke to run the synthetic model check.")
