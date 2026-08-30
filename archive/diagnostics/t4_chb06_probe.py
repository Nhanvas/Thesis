#!/usr/bin/env python3
"""
A2 / T4 — chb06 sign-flip + normalization diagnostic (Phase-B GATE for Phase 2).

DIAGNOSTIC. Determines whether chb06's below-chance window AUROC (0.437) is:
  H_flip  : a branch's anomaly score is INVERTED (fixable for free by sign flip),
  H_norm  : a global-z normalization artifact (helped by robust/rolling re-standardization),
  H_repr  : genuine representation failure (ictal ~ interictal; needs Phase 2 / Future Work).

Reads per-branch robust-z components {zrecon,ztemp,zgamma}_chb06_{inter,ictal}.npy and the
ensemble ens_seed42_chb06_{inter,ictal}.npy. Higher score = more anomalous by construction.

Usage:
  python t4_chb06_probe.py \
      --ens_dir results/retrain_v3p1/ens --comp_dir data/processed/components --seed 42
"""
import argparse
from pathlib import Path
import numpy as np

try:
    from sklearn.metrics import roc_auc_score
except Exception:
    roc_auc_score = None


def cohens_d(a, b):
    na, nb = len(a), len(b)
    sp = np.sqrt(((na-1)*a.var(ddof=1) + (nb-1)*b.var(ddof=1)) / (na+nb-2)) if na+nb > 2 else np.nan
    return (b.mean()-a.mean())/sp if sp else np.nan  # >0 => ictal higher (correct direction)


def auroc(y, s):
    return roc_auc_score(y, s) if len(np.unique(y)) > 1 else float("nan")


def robust_z(x, ref):
    med = np.median(ref); mad = np.median(np.abs(ref-med)) + 1e-9
    return (x-med)/(1.4826*mad)


def analyze(name, inter, ictal):
    y = np.concatenate([np.zeros(len(inter)), np.ones(len(ictal))])
    s = np.concatenate([inter, ictal])
    a = auroc(y, s); a_flip = auroc(y, -s)
    d = cohens_d(inter, ictal)
    # robust re-standardization using interictal as reference
    s_rz = np.concatenate([robust_z(inter, inter), robust_z(ictal, inter)])
    a_rz = auroc(y, s_rz)
    verdict = ("INVERTED (flip helps)" if a < 0.45 and a_flip > 0.55 else
               "UNINFORMATIVE (ictal~inter)" if abs(a-0.5) < 0.06 and abs(d) < 0.2 else
               "INFORMATIVE (correct sign)" if a >= 0.55 else "WEAK/mixed")
    return dict(branch=name, n_inter=len(inter), n_ictal=len(ictal),
                auroc=a, auroc_flipped=a_flip, robustz_auroc=a_rz,
                ictal_median=float(np.median(ictal)), inter_median=float(np.median(inter)),
                cohens_d=d, verdict=verdict)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ens_dir", default="results/retrain_v3p1/ens")
    ap.add_argument("--comp_dir", default="data/processed/components")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--subj", default="chb06")
    a = ap.parse_args()
    assert roc_auc_score is not None, "pip install scikit-learn"
    cd, ed = Path(a.comp_dir), Path(a.ens_dir)

    branches = {}
    for br in ["zrecon", "ztemp", "zgamma"]:
        branches[br] = (np.load(cd/f"{br}_{a.subj}_inter.npy").astype(float).ravel(),
                        np.load(cd/f"{br}_{a.subj}_ictal.npy").astype(float).ravel())
    ens = (np.load(ed/f"ens_seed{a.seed}_{a.subj}_inter.npy").astype(float).ravel(),
           np.load(ed/f"ens_seed{a.seed}_{a.subj}_ictal.npy").astype(float).ravel())

    print(f"=== T4 probe: {a.subj} ===")
    print(f"{'branch':9}{'AUROC':>7}{'flip':>7}{'robZ':>7}{'d':>7}  verdict")
    res = []
    for br, (i, c) in branches.items():
        r = analyze(br, i, c); res.append(r)
        print(f"{r['branch']:9}{r['auroc']:7.3f}{r['auroc_flipped']:7.3f}{r['robustz_auroc']:7.3f}"
              f"{r['cohens_d']:7.2f}  {r['verdict']}")
    re = analyze("ensemble", *ens)
    print(f"{'ensemble':9}{re['auroc']:7.3f}{re['auroc_flipped']:7.3f}{re['robustz_auroc']:7.3f}"
          f"{re['cohens_d']:7.2f}  {re['verdict']}")

    # per-branch sign-corrected equal-weight ensemble (flip any branch with AUROC<0.45)
    def signed(i, c, flip): 
        return (-i, -c) if flip else (i, c)
    flips = {r["branch"]: (r["auroc"] < 0.45) for r in res}
    yi = np.zeros(len(branches["zrecon"][0])); yc = np.ones(len(branches["zrecon"][1]))
    ei = sum(signed(*branches[b], flips[b])[0] for b in branches) / 3.0
    ec = sum(signed(*branches[b], flips[b])[1] for b in branches) / 3.0
    a_corr = auroc(np.concatenate([yi, yc]), np.concatenate([ei, ec]))
    print(f"\nflips applied: {flips}")
    print(f"sign-corrected equal-weight ensemble AUROC = {a_corr:.3f} (baseline ensemble {re['auroc']:.3f})")

    # verdict gate
    print("\n=== GATE ===")
    if a_corr > 0.55 and a_corr - re["auroc"] > 0.08:
        print(f"  H_flip SUPPORTED: sign correction lifts chb06 to {a_corr:.3f} -> FREE fix, no GPU.")
    elif re["robustz_auroc"] - re["auroc"] > 0.08:
        print(f"  H_norm SUPPORTED: robust re-z lifts to {re['robustz_auroc']:.3f} -> cheap normfix.")
    elif all(abs(r["auroc"]-0.5) < 0.1 for r in res):
        print("  H_repr SUPPORTED: all branches ~chance & ictal~inter -> representation-limited -> Phase 2/Future Work.")
    else:
        print("  MIXED: inspect per-branch table; partial signal in some branch.")
    print("\nNote: true continuous rolling-z needs the time-interleaved recording; this probe uses the "
          "separated inter/ictal arrays, so H_norm here is a robust-MAD re-z test, not a full rolling-z.")


if __name__ == "__main__":
    main()
