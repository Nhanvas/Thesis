"""
gae_gate_report.py — Gate R-GAE evaluation (PHA 1, step 1 acceptance).

For every retrained checkpoint (gae_joint_seed*.pt in --ckpt_dir), score all 8 TEST subjects'
interictal + ictal windows with the VERIFIED joint scorer, compute per-subject recon AUROC,
aggregate mean±SD across seeds, and evaluate the pre-registered acceptance gates G1–G4.

Per-subject recon AUROC is rank-based, so it is invariant to the downstream robust-z
normalisation — i.e. these numbers are directly comparable to the locked zrecon AUROCs.

Also dumps raw recon scores for the canonical seed (reused later as the zrecon component).

Run on Kaggle after training:
    !python gae_gate_report.py --ckpt_dir /kaggle/working/gae_retrain --canonical 42
"""
import argparse
import glob
import re
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import roc_auc_score

import gae_joint as G

TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]

# Locked reference: recon-standalone AUROC (verified window-tier run == auroc_verification.csv)
LOCKED = {"chb03": 0.659, "chb06": 0.300, "chb13": 0.836, "chb14": 0.662,
          "chb15": 0.790, "chb16": 0.647, "chb17": 0.601, "chb18": 0.871}
LOCKED_MACRO = 0.671


def recon_auroc(model, subj, adj_dir, feat_dir, suffix, device, batch, dump_dir=None):
    si = G.score_windows(model, Path(adj_dir) / f"{subj}_interictal_adjs{suffix}.npy",
                         Path(feat_dir) / f"{subj}_interictal_features.npy", device, batch)
    sc = G.score_windows(model, Path(adj_dir) / f"{subj}_ictal_adjs{suffix}.npy",
                         Path(feat_dir) / f"{subj}_ictal_features.npy", device, batch)
    if dump_dir is not None:
        d = Path(dump_dir); d.mkdir(parents=True, exist_ok=True)
        np.save(d / f"raw_recon_{subj}_inter.npy", si)
        np.save(d / f"raw_recon_{subj}_ictal.npy", sc)
    y = np.r_[np.zeros(len(si)), np.ones(len(sc))]
    return float(roc_auc_score(y, np.r_[si, sc]))


def main():
    ap = argparse.ArgumentParser()
    base = "/kaggle/input/datasets/nhn2mm"
    ap.add_argument("--adj_dir", default=f"{base}/chbmit-topk20")
    ap.add_argument("--feat_dir", default=f"{base}/chbmit-processed")
    ap.add_argument("--suffix", default="_topk20")
    ap.add_argument("--ckpt_dir", default="/kaggle/working/gae_retrain")
    ap.add_argument("--canonical", type=int, default=42)
    ap.add_argument("--batch", type=int, default=512)
    ap.add_argument("--out_dir", default="/kaggle/working/gae_retrain")
    a = ap.parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    ckpts = sorted(glob.glob(str(Path(a.ckpt_dir) / "gae_joint_seed*.pt")))
    seeds = [int(re.search(r"seed(\d+)", c).group(1)) for c in ckpts]
    print(f"device={device} | seeds found: {seeds}")

    per_seed = {}   # seed -> {subj: auroc}
    for ck, sd in zip(ckpts, seeds):
        model = G.load_checkpoint(ck, device)
        dump = Path(a.out_dir) / "components_raw" if sd == a.canonical else None
        per_seed[sd] = {s: recon_auroc(model, s, a.adj_dir, a.feat_dir, a.suffix,
                                       device, a.batch, dump) for s in TEST_SUBJS}
        macro = np.mean(list(per_seed[sd].values()))
        print(f"  seed {sd}: macro recon AUROC = {macro:.4f}")

    # ---- aggregate ----
    print("\n" + "=" * 74)
    print(f"{'subj':7}{'locked':>8}{'mean':>8}{'sd':>7}{'min':>7}{'max':>7}{'|Δ|':>7}")
    print("-" * 74)
    gate3_fail = []
    means = {}
    for s in TEST_SUBJS:
        vals = np.array([per_seed[sd][s] for sd in seeds])
        m, sd_ = vals.mean(), (vals.std(ddof=1) if len(vals) > 1 else 0.0)
        means[s] = m
        d = abs(m - LOCKED[s])
        tag = ""
        if s != "chb06" and d > 0.10:
            gate3_fail.append(s); tag = "  <-- G3"
        if s == "chb06" and m > 0.45:
            gate3_fail.append(s); tag = "  <-- G3(chb06)"
        print(f"{s:7}{LOCKED[s]:>8.3f}{m:>8.3f}{sd_:>7.3f}{vals.min():>7.3f}"
              f"{vals.max():>7.3f}{d:>7.3f}{tag}")

    macro_vals = np.array([np.mean(list(per_seed[sd].values())) for sd in seeds])
    mm, msd = macro_vals.mean(), (macro_vals.std(ddof=1) if len(macro_vals) > 1 else 0.0)
    lo, hi = mm - 2 * msd, mm + 2 * msd
    print("-" * 74)
    print(f"MACRO   {LOCKED_MACRO:>8.3f}{mm:>8.3f}{msd:>7.3f}")

    # ---- gates ----
    can = per_seed.get(a.canonical, per_seed[seeds[0]])
    g1 = can["chb13"] >= 0.78
    g2_band = 0.64 <= mm <= 0.70
    g2_ci = (lo <= LOCKED_MACRO <= hi) if msd > 0 else g2_band
    g2 = g2_band and g2_ci
    g3 = len(gate3_fail) == 0

    print("\nGATES:")
    print(f"  G1 chb13>=0.78 (seed {a.canonical}): {can['chb13']:.3f}  -> {'PASS' if g1 else 'FAIL'}")
    print(f"  G2 macro in [0.64,0.70]={g2_band}; locked 0.671 in [{lo:.3f},{hi:.3f}]={g2_ci}"
          f"  -> {'PASS' if g2 else 'FAIL'}")
    print(f"  G3 per-subject stability: {'PASS' if g3 else 'FAIL ' + str(gate3_fail)}")

    if g1 and g2 and g3:
        print("\nVERDICT: PASS — faithful reconstruction. Adopt canonical seed as system-of-record.")
    elif g1 and g3 and mm > 0.70:
        print("\nVERDICT: ABOVE BAND — NOT auto-reject. Run divergence audit (PREREG §6):")
        print("         (i) confirm no leak (train never saw test/ictal),")
        print("         (ii) stable-high across seeds (sd small?), (iii) explain mechanism vs loss curve.")
    else:
        print("\nVERDICT: FAIL/BELOW — reconstruction likely wrong. Debug before adopting.")

    # ---- save ----
    import csv
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    with open(out / "gae_gate_report.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["subject", "locked"] + [f"seed{s}" for s in seeds] + ["mean", "sd"])
        for s in TEST_SUBJS:
            vals = [per_seed[sd][s] for sd in seeds]
            w.writerow([s, LOCKED[s]] + [f"{v:.4f}" for v in vals]
                       + [f"{np.mean(vals):.4f}", f"{np.std(vals, ddof=1) if len(vals)>1 else 0:.4f}"])
    print(f"\nWrote {out/'gae_gate_report.csv'}  |  raw recon (seed {a.canonical}) -> {out/'components_raw'}")


if __name__ == "__main__":
    main()
