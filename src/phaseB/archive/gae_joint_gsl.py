"""
gae_joint_gsl.py — S2 variant: joint GAE with a per-window LEARNED sparse graph (GSL),
residual-gated with the fixed top-k20 adjacency. Dense batched GCN (no torch_geometric).

Design (per docs 03/04 + Lit_review: GraphS4mer/IRENE/GTS family, label-free):
  node band feats Xn --proj--> emb --inner-product--> S(sym) --softplus,top-k STE--> A_L
  A_final = g*A_L + (1-g)*A_topk20 ,  g = sigmoid(gate_logit)   [gate_init<<0 => g~0 => baseline]
  encoder = 2-layer dense GCN on A_final ; node feat x = [rownorm(A_final)(18), Xn(5)] = 23
  A-decoder = clamp(Z Zᵀ,0,1) ; X-decoder MLP 16->32->5 ; target A = raw top-k20 (physio anchor)
  anomaly score = MSE(A_raw, Â) + LAMBDA*MSE(Xn, X̂)   (identical objective to baseline)

Exports the same API names as gae_joint (GAEModel, load_checkpoint, score_windows, N_CH, ...)
so val_gate.py --gae_module gae_joint_gsl works unchanged.

INTEGRITY: reads only the baseline _topk20 adjacency + features; learns structure label-free
from interictal. TEST subjects never enter training/gating.
"""
import argparse
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn

# constants (pinned to baseline; do NOT change)
INPUT_DIM, HIDDEN_DIM, LATENT_DIM = 23, 64, 16
N_CH, N_BANDS = 18, 5
LAMBDA = 0.1
KEEP_EDGES = 30            # ~20% of 153 undirected pairs (matches locked top-k20 density)


def dense_gcn_norm(A):
    """Symmetric GCN normalisation of a dense adjacency. A:[B,N,N] nonneg -> [B,N,N]."""
    N = A.shape[-1]
    I = torch.eye(N, device=A.device).unsqueeze(0)
    Ah = A + I
    deg = Ah.sum(-1)
    dinv = deg.pow(-0.5)
    dinv = torch.where(torch.isinf(dinv), torch.zeros_like(dinv), dinv)
    return dinv.unsqueeze(2) * Ah * dinv.unsqueeze(1)


class GSLLayer(nn.Module):
    """Per-window learned sparse adjacency, residual-gated with the fixed top-k20 graph."""
    def __init__(self, n_bands=N_BANDS, emb=16, keep=KEEP_EDGES, gate_init=-6.0):
        super().__init__()
        self.proj = nn.Sequential(nn.Linear(n_bands, emb), nn.ReLU(), nn.Linear(emb, emb))
        self.gate_logit = nn.Parameter(torch.tensor(float(gate_init)))
        self.keep = keep
        self.force_g = None   # None=learn gate; 0.0=pure top-k20 (self-check); 1.0=pure learned graph

    def forward(self, Xn, A_topk):
        # Xn:[B,18,5] ; A_topk:[B,18,18] raw baseline adjacency
        B, N, _ = A_topk.shape
        h = self.proj(Xn)                                  # [B,18,emb]
        S = torch.bmm(h, h.transpose(1, 2))                # [B,18,18]
        S = 0.5 * (S + S.transpose(1, 2))
        diag = torch.eye(N, device=S.device).bool().unsqueeze(0)
        S = S.masked_fill(diag, -1e9)                      # no self-loops in candidate
        w = torch.nn.functional.softplus(S)                # nonneg edge weights
        w = w.masked_fill(diag, 0.0)
        # exact top-k STE mask (hard selection, grad flows through magnitudes w)
        k = min(2 * self.keep, N * N)
        flat = w.reshape(B, -1)
        idx = flat.topk(k, dim=1).indices
        mask = torch.zeros_like(flat).scatter_(1, idx, 1.0).view(B, N, N)
        A_L = mask * w
        A_L = 0.5 * (A_L + A_L.transpose(1, 2))            # keep undirected
        g = torch.sigmoid(self.gate_logit)
        if self.force_g is not None:
            g = torch.full_like(g, float(self.force_g))
        A_final = g * A_L + (1.0 - g) * A_topk
        return A_final, A_L, g


class GAEModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.gsl = GSLLayer()
        self.lin1 = nn.Linear(INPUT_DIM, HIDDEN_DIM)       # dense GCN layer 1
        self.lin2 = nn.Linear(HIDDEN_DIM, LATENT_DIM)      # dense GCN layer 2
        self.relu = nn.ReLU()
        self.x_decoder = nn.Sequential(nn.Linear(LATENT_DIM, 32), nn.ReLU(),
                                       nn.Linear(32, N_BANDS))

    def encode(self, Xn, A_topk):
        A_final, A_L, g = self.gsl(Xn, A_topk)
        An = A_final / (A_final.amax(dim=(1, 2), keepdim=True) + 1e-8)   # node-feat rows
        x = torch.cat([An, Xn], dim=2)                     # [B,18,23]
        Anorm = dense_gcn_norm(A_final)
        H = self.relu(Anorm @ self.lin1(x))
        Z = Anorm @ self.lin2(H)                           # [B,18,16]
        return Z, A_L, g

    def forward(self, Xn, A_topk, A_target, per_node=False):
        Z, A_L, g = self.encode(Xn, A_topk)
        Ah = torch.clamp(torch.bmm(Z, Z.transpose(1, 2)), 0.0, 1.0)
        Xh = self.x_decoder(Z)
        if per_node:
            score = (((A_target - Ah) ** 2).mean(2) + LAMBDA * ((Xn - Xh) ** 2).mean(2))
        else:
            score = (((A_target - Ah) ** 2).mean((1, 2)) + LAMBDA * ((Xn - Xh) ** 2).mean((1, 2)))
        return score, A_L, g


# ---- input construction (raw top-k20 adj + raw feats -> A_topk, Xn, A_target) ----
def build_inputs(A_np, X_np, device):
    A = torch.as_tensor(A_np, dtype=torch.float32, device=device)      # [B,18,18] raw
    Xt = torch.as_tensor(X_np, dtype=torch.float32, device=device)     # [B,18,5] raw
    if A.dim() == 2:
        A = A.unsqueeze(0); Xt = Xt.unsqueeze(0)
    Xmn = Xt.amin(dim=1, keepdim=True); Xmx = Xt.amax(dim=1, keepdim=True)
    Xn = (Xt - Xmn) / (Xmx - Xmn + 1e-8)
    return A, Xn, A                                                     # A_topk, Xn, A_target(=raw A)


def score_windows(model, adj_path, feat_path, device, batch_size=512, per_node=False):
    """Raw joint recon score per window. Same signature/semantics as gae_joint.score_windows."""
    adjs = np.load(adj_path, mmap_mode="r")
    feats = np.load(feat_path, mmap_mode="r")
    out = []; model.eval()
    with torch.no_grad():
        for s in range(0, len(adjs), batch_size):
            e = min(s + batch_size, len(adjs))
            A_topk, Xn, A_tgt = build_inputs(adjs[s:e].astype(np.float32),
                                             feats[s:e].astype(np.float32), device)
            sc, _, _ = model(Xn, A_topk, A_tgt, per_node=per_node)
            out.append(sc.cpu().numpy().astype(np.float32))
    return np.concatenate(out, axis=0)


def load_checkpoint(model_path, device):
    model = GAEModel().to(device)
    state = torch.load(str(model_path), map_location=device)
    state = state.get("state_dict", state)
    model.load_state_dict(state, strict=True)
    model.eval()
    return model


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true", help="random-tensor forward/shape/grad check (CPU ok)")
    a = ap.parse_args()
    if a.selftest:
        dev = torch.device("cpu")
        m = GAEModel().to(dev)
        A = torch.rand(8, 18, 18); A = 0.5 * (A + A.transpose(1, 2))
        X = torch.randn(8, 18, 5)
        A_topk, Xn, A_tgt = build_inputs(A.numpy(), X.numpy(), dev)
        sc, A_L, g = m(Xn, A_topk, A_tgt)
        print("score", tuple(sc.shape), "A_L", tuple(A_L.shape), "g", float(g.detach()))
        loss = sc.mean() + 1e-3 * A_L.abs().mean()
        loss.backward()
        gnorm = sum(p.grad.abs().sum().item() for p in m.parameters() if p.grad is not None)
        print("edges/window ~", int((A_L[0] > 0).sum().item()), "| grad_norm", round(gnorm, 4),
              "| PASS" if gnorm > 0 and sc.shape == (8,) else "| FAIL")
