#!/usr/bin/env python
"""
p2_dump_seeds23.py -- stage P2 infrastructure (author request 2026-10-07: every P2 step on 4 seeds).
Scores v2 clean seeds 2 and 3 on the 15 NON-TEST subjects exactly as E8 (recon joint score, graph-mean
latent, latent std) and E14 (per-channel LedoitWolf distance of the node latent), and keeps the node
latents (float16) for the per-recording baseline step E16. Seeds 42 and 1 already exist in
results/e8_gae_v2/scores (recon/lat/latstd), results/e14_spatial_recruitment/pernode (distances) and
results/e15_patient_adaptation/pernode ({tag}_s0_Z, node latents).
No labels are read. No evaluation. TEST GUARD.

Reproduction gate (before anything is written for a subject): clean_seed42 recomputed by THIS code on
the first 1,024 windows must equal the E8 cache (recon and mean latent) within 1e-5 / 1e-4.

Output: results/p2_seeds/{subj}.npz with idx, {tag}_recon, {tag}_lat, {tag}_latstd,
        {tag}_d (n x 18 float32), {tag}_Z (n x 18 x 16 float16), for tag in clean_seed2, clean_seed3.
Run:
  python src/p2_dump_seeds23.py --smoke      (chb01, 2,048 windows, ~1 min)
  python src/p2_dump_seeds23.py              (estimated 30-90 min CPU, not measured; ~0.7 GB)
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.covariance import LedoitWolf

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "dataprep", ROOT / "src" / "retrain",
          ROOT / "src" / "phaseB", ROOT / "src" / "phaseC"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import e8_gae_v2_eval as E8            # noqa: E402

TEST = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}
OUT = ROOT / "results" / "p2_seeds"
CKPT = ROOT / "data" / "models_v2"
TAGS = ["clean_seed2", "clean_seed3"]


def run_model(tag, adj, Xn_all, f7):
    import torch
    from torch_geometric.data import Data, Batch
    from torch_geometric.utils import dense_to_sparse
    import gae_joint as G
    ck = CKPT / f"gae_v2_{tag}.pt"
    meta = json.loads(ck.with_suffix(".json").read_text())
    mu, sd, clip = np.array(meta["add_mean"]), np.array(meta["add_std"]), meta["clip"]
    fa = ((np.clip((f7 - mu) / sd, -clip, clip) + clip) / (2 * clip)).astype(np.float32)
    model = G.GAEModel(in_dim=meta["in_dim"], bands=meta["out_x"])
    model.load_state_dict(torch.load(str(ck), map_location="cpu"), strict=True)
    model.eval()
    ox = meta["out_x"]; n = len(adj)
    rec = np.empty(n, np.float32)
    Z = np.empty((n, G.N_CH, G.LATENT_DIM), np.float32)
    with torch.no_grad():
        for s in range(0, n, E8.CHUNK):
            e = min(s + E8.CHUNK, n)
            dl = []
            for i in range(s, e):
                A = torch.tensor(adj[i]); An = A / (A.amax() + 1e-8)
                xt = torch.cat([torch.tensor(Xn_all[i].astype(np.float32)), torch.tensor(fa[i])], dim=1)
                ei, ew = dense_to_sparse(A)
                dl.append(Data(x=torch.cat([An, xt], dim=1), edge_index=ei, edge_attr=ew, A=A, Xt=xt))
            b = Batch.from_data_list(dl); B = b.num_graphs
            zz = model.encoder(b.x, b.edge_index, b.edge_attr)
            zp = zz.view(B, G.N_CH, G.LATENT_DIM)
            Ah = torch.clamp(torch.bmm(zp, zp.transpose(1, 2)), 0.0, 1.0)
            Xh = model.x_decoder(zz).view(B, G.N_CH, ox)
            A_ = b.A.view(B, G.N_CH, G.N_CH); X_ = b.Xt.view(B, G.N_CH, ox)
            rec[s:e] = (((A_ - Ah) ** 2).mean(dim=(1, 2)) + G.LAMBDA * ((X_ - Xh) ** 2).mean(dim=(1, 2))).numpy()
            Z[s:e] = zp.numpy()
    return rec, Z


def dump_subject(subj, smoke=False):
    if subj in TEST or subj not in E8.SUBJS:
        raise SystemExit(f"TEST GUARD: {subj}")
    out = OUT / f"{subj}{'_SMOKE' if smoke else ''}.npz"
    if out.exists() and not smoke:
        print(f"{subj}: exists, skip"); return
    t0 = time.time()
    z = np.load(E8.DATA / f"{subj}.npz", allow_pickle=True)
    cache = np.load(E8.OUT / "scores" / f"{subj}.npz")
    idx = np.flatnonzero(~z["is_signal_loss"])
    if not np.array_equal(idx, cache["idx"]):
        raise SystemExit(f"{subj}: window index differs from the E8 cache")
    if smoke:
        idx = idx[:2048]
    adj = z["adj"][idx].astype(np.float32); adj[~np.isfinite(adj).all(axis=(1, 2))] = 0.0
    bp5 = z["bp5"][idx].astype(np.float32); bp5[~np.isfinite(bp5)] = 0.0
    f7 = z["f7"][idx].astype(np.float64)
    Xn_all = (bp5 - bp5.min(axis=1, keepdims=True)) / (bp5.max(axis=1, keepdims=True)
                                                      - bp5.min(axis=1, keepdims=True) + 1e-8)
    # reproduction gate on seed 42
    r42, Z42 = run_model("clean_seed42", adj[:1024], Xn_all[:1024], f7[:1024])
    e_r = float(np.abs(r42 - cache["clean_seed42_recon"][:1024]).max())
    e_l = float(np.abs(Z42.mean(axis=1) - cache["clean_seed42_lat"][:1024]).max())
    if e_r > 1e-5 or e_l > 1e-4:
        raise SystemExit(f"STOP {subj}: reproduction of E8 seed 42 failed (recon {e_r:.1e}, lat {e_l:.1e})")
    res = {"idx": idx}
    for tag in TAGS:
        rec, Z = run_model(tag, adj, Xn_all, f7)
        D = np.empty((len(idx), Z.shape[1]), np.float32)
        for c in range(Z.shape[1]):
            Zc = Z[:, c, :].astype(np.float64)
            D[:, c] = LedoitWolf().fit(Zc).mahalanobis(Zc)
        res[f"{tag}_recon"] = rec
        res[f"{tag}_lat"] = Z.mean(axis=1)
        res[f"{tag}_latstd"] = Z.std(axis=1, ddof=1)
        res[f"{tag}_d"] = D
        res[f"{tag}_Z"] = Z.astype(np.float16)
        print(f"  {subj} {tag}: done ({time.time()-t0:.0f}s)", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez(out, **res)
    print(f"{subj}: {len(idx)} windows, reproduction recon {e_r:.1e} lat {e_l:.1e}, {time.time()-t0:.0f}s", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--subjects", nargs="+", default=E8.SUBJS)
    a = ap.parse_args()
    subs = ["chb01"] if a.smoke else a.subjects
    for s in subs:
        dump_subject(s, smoke=a.smoke)


if __name__ == "__main__":
    main()
