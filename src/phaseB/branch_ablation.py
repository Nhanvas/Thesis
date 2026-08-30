"""
branch_ablation.py — E1 + latent integration. Auto-discovers the per-branch components
present in --comp (zrecon, ztemp, zgamma, and optionally zlatent), then scores every
equal-weight subset on the VAL subjects (interictal vs ictal). Faithful to the locked
combine (equal mean of robust-z components). CPU-only. TEST guarded.

Key rows to compare:
  recon+temp+gamma   = locked baseline ensemble
  latent+temp+gamma  = proposed (recon branch replaced by the E2 latent-score)
  temp+gamma         = drop the GAE branch entirely

Run:
    python branch_ablation.py --comp /kaggle/working/val_components
"""
import argparse, os
from itertools import combinations
from pathlib import Path
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score

VAL = ["chb10", "chb11", "chb22"]
TEST = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}


def discover_branches(comp, subjs):
    pres = set()
    for f in os.listdir(comp):
        for s in subjs:
            tag = f"_{s}_inter.npy"
            if f.endswith(tag):
                pres.add(f[:-len(tag)])
    order = ["zrecon", "zlatent", "ztemp", "zgamma"]
    return [b for b in order if b in pres] + sorted(pres - set(order))


def load_branch(comp, br, subj, split):
    return np.load(Path(comp) / f"{br}_{subj}_{split}.npy").astype(np.float64).ravel()


def subj_scores(comp, subset, subj):
    zi = np.mean([load_branch(comp, b, subj, "inter") for b in subset], axis=0)
    zc = np.mean([load_branch(comp, b, subj, "ictal") for b in subset], axis=0)
    y = np.r_[np.zeros(len(zi)), np.ones(len(zc))]
    return roc_auc_score(y, np.r_[zi, zc]), average_precision_score(y, np.r_[zi, zc])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--comp", default="/kaggle/working/val_components")
    ap.add_argument("--subjs", nargs="+", default=VAL)
    a = ap.parse_args()
    leak = [s for s in a.subjs if s in TEST]
    if leak:
        raise SystemExit(f"INTEGRITY ABORT: TEST subject(s) {leak} — VAL only.")

    branches = discover_branches(a.comp, a.subjs)
    print("branches found:", branches)
    subsets = []
    for r in range(len(branches), 0, -1):
        subsets += [list(c) for c in combinations(branches, r)]

    rows = []
    for sub in subsets:
        aus, aps, per = [], [], []
        for s in a.subjs:
            au, ap_ = subj_scores(a.comp, sub, s)
            aus.append(au); aps.append(ap_); per.append(au)
        rows.append(("+".join(b.replace("z", "") for b in sub), np.mean(aus), np.mean(aps), per))

    rows.sort(key=lambda r: r[1], reverse=True)
    print(f"\n{'subset':24}{'macroAUROC':>12}{'macroAUPRC':>12}   " + "".join(f"{s:>9}" for s in a.subjs))
    for name, au, ap_, per in rows:
        print(f"{name:24}{au:12.4f}{ap_:12.4f}   " + "".join(f"{p:9.3f}" for p in per))

    def get(n): return next((r for r in rows if r[0] == n), None)
    base = get("recon+temp+gamma"); prop = get("latent+temp+gamma"); drop = get("temp+gamma")
    print("\n--- decision rows ---")
    for tag, r in [("baseline recon+temp+gamma", base), ("proposed latent+temp+gamma", prop),
                   ("drop-GAE  temp+gamma", drop)]:
        if r: print(f"  {tag:28} macroAUROC {r[1]:.4f}  macroAUPRC {r[2]:.4f}  per {['%.3f'%x for x in r[3]]}")


if __name__ == "__main__":
    main()
