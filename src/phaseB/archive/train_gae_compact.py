"""
train_gae_compact.py — S3-lane model upgrade. Retrain the baseline joint GAE with an
added Deep-SVDD compactness term so the interictal latent manifold contracts around a
center c -> ictal windows sit farther out -> the E2 latent-Mahalanobis readout sharpens.
Architecture + recon loss are IDENTICAL to gae_joint.GAEModel (recon readout stays valid).

Loss = recon(mse_A + LAMBDA*mse_X)  +  lam_eff * mean_j (pool(Z)_j - c_j)^2
  - warmup epochs: recon only; then freeze c = mean interictal pooled-Z; auto-balance
    lam_eff so compactness contributes ~lam_c x the recon magnitude (no VAL tuning).
PREREG (inherits 01): interictal-only, 12 TRAIN / 3 VAL, never touch ictal/8-TEST. seed 42.

Kaggle:
    !python train_gae_compact.py --smoke
    !python train_gae_compact.py --seeds 42 --adj_dir <topk20> --feat_dir <processed>
Score the result (latent readout):
    !python latent_anomaly.py --ckpt /kaggle/working/gae_compact/gae_compact_seed42.pt \
        --adj_dir <topk20> --feat_dir <processed>
"""
import argparse, time
from pathlib import Path
import numpy as np
import torch
from torch_geometric.loader import DataLoader
import gae_joint as G
import train_gae_joint as TR   # reuse make_window_data / build_dataset / splits / set_seed


def pooled_z(model, batch, device):
    B = batch.num_graphs
    z = model.encoder(batch.x, batch.edge_index, batch.edge_attr)
    zpg = z.view(B, G.N_CH, G.LATENT_DIM)
    return zpg, B


def recon_terms(zpg, batch, B):
    Ah = torch.clamp(torch.bmm(zpg, zpg.transpose(1, 2)), 0.0, 1.0)
    Xh_in = zpg.reshape(B * G.N_CH, G.LATENT_DIM)
    return Ah, Xh_in


def batch_loss(model, batch, device, c, lam_eff):
    batch = batch.to(device)
    zpg, B = pooled_z(model, batch, device)
    Ah = torch.clamp(torch.bmm(zpg, zpg.transpose(1, 2)), 0.0, 1.0)
    Xh = model.x_decoder(zpg.reshape(B * G.N_CH, G.LATENT_DIM)).view(B, G.N_CH, G.N_BANDS)
    A = batch.A.view(B, G.N_CH, G.N_CH); Xn = batch.Xn.view(B, G.N_CH, G.N_BANDS)
    mse_A = ((A - Ah) ** 2).mean(dim=(1, 2)); mse_X = ((Xn - Xh) ** 2).mean(dim=(1, 2))
    recon = (mse_A + G.LAMBDA * mse_X).mean()
    if c is None:
        return recon, recon.detach(), torch.zeros((), device=device)
    pool = zpg.mean(dim=1)                       # [B,16] graph embedding
    comp = ((pool - c) ** 2).mean(dim=1).mean()  # scale-free compactness
    return recon + lam_eff * comp, recon.detach(), comp.detach()


def compute_center(model, loader, device):
    model.eval(); tot = None; n = 0
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device); zpg, B = pooled_z(model, batch, device)
            s = zpg.mean(dim=1).sum(dim=0)
            tot = s if tot is None else tot + s; n += B
    c = tot / max(n, 1)
    c[c.abs() < 1e-6] = 1e-6                      # Deep-SVDD: avoid all-zero center
    return c


def ref_scales(model, loader, device, c):
    model.eval(); rs, cs, k = 0.0, 0.0, 0
    with torch.no_grad():
        for batch in loader:
            _, r, cm = batch_loss(model, batch, device, c, 0.0)
            rs += float(r); cs += float(cm); k += 1
            if k >= 20:
                break
    return rs / max(k, 1), cs / max(k, 1)


def main():
    ap = argparse.ArgumentParser()
    base = "/kaggle/input/datasets/nhn2mm"
    ap.add_argument("--adj_dir", default=f"{base}/chbmit-topk20")
    ap.add_argument("--feat_dir", default=f"{base}/chbmit-processed")
    ap.add_argument("--suffix", default="_topk20")
    ap.add_argument("--out_dir", default="/kaggle/working/gae_compact")
    ap.add_argument("--epochs", type=int, default=200)
    ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--lam_c", type=float, default=0.5,
                    help="compactness weight RELATIVE to recon magnitude (0.5 = half). Auto-balanced.")
    ap.add_argument("--seeds", type=int, nargs="+", default=[42])
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={dev}  lam_c(rel)={a.lam_c}  warmup={a.warmup}")

    if a.smoke:
        tr_s, va_s, ep, wu, seeds, maxw = TR.TRAIN_SUBJS[:1], TR.VAL_SUBJS[:1], 4, 2, [42], 2000
        print("SMOKE — loop check")
    else:
        tr_s, va_s, ep, wu, seeds, maxw = TR.TRAIN_SUBJS, TR.VAL_SUBJS, a.epochs, a.warmup, a.seeds, None

    print("Building TRAIN ..."); train_ds = TR.build_dataset(a.adj_dir, a.feat_dir, tr_s, a.suffix, maxw)
    print("Building VAL ...");   val_ds = TR.build_dataset(a.adj_dir, a.feat_dir, va_s, a.suffix, maxw)

    for seed in seeds:
        print(f"\n=== SEED {seed} ==="); TR.set_seed(seed)
        g = torch.Generator().manual_seed(seed)
        tl = DataLoader(train_ds, batch_size=a.batch, shuffle=True, generator=g)
        vl = DataLoader(val_ds, batch_size=a.batch, shuffle=False)
        model = G.GAEModel().to(dev)
        opt = torch.optim.Adam(model.parameters(), lr=a.lr)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=ep)
        c, lam_eff = None, 0.0
        for e in range(ep):
            if e == wu:                                  # freeze center + auto-balance
                c = compute_center(model, tl, dev)
                r_ref, c_ref = ref_scales(model, tl, dev, c)
                lam_eff = a.lam_c * r_ref / (c_ref + 1e-8)
                print(f"  [center frozen] r_ref={r_ref:.5f} c_ref={c_ref:.5f} lam_eff={lam_eff:.4f}")
            model.train(); tr_r = tr_c = nb = 0.0
            for batch in tl:
                opt.zero_grad(); loss, r, cm = batch_loss(model, batch, dev, c, lam_eff)
                loss.backward(); opt.step(); tr_r += float(r); tr_c += float(cm); nb += 1
            sched.step()
            if e < 3 or (e + 1) % 20 == 0 or e == ep - 1:
                print(f"  [seed {seed}] ep {e+1:3}/{ep}  recon={tr_r/nb:.6f}  comp={tr_c/nb:.6f}")
        out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
        ck = out / f"gae_compact_seed{seed}.pt"
        torch.save(model.state_dict(), str(ck))
        np.save(out / f"center_seed{seed}.npy", c.detach().cpu().numpy())
        print(f"  [seed {seed}] SAVED {ck.name}")
    print("\nDONE. Score latent: latent_anomaly.py --ckpt <gae_compact_seedN.pt> ...")


if __name__ == "__main__":
    main()
