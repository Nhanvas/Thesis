#!/usr/bin/env python
"""
attribution_synthetic_spread.py — ATTRIBUTION_SPEC A2/D6.1, gate G-S4'.

Only the synthetic CONSTRUCTION is corrected: generalized == all 18 channels elevated,
focal == 1-2 channels. Metric (normalised entropy of s) and threshold (p<0.05) are unchanged
from D6. AUROC is undefined at |S|=18 and is deliberately not computed there.
"""
import sys, csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src",):
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

import numpy as np
from scipy.stats import mannwhitneyu
from attribution_synthetic_check import (PN, OUT, VAL, TEST, R, SEED, NCH,
                                         spreads, load_len_distribution)

ALPHA, KS = 2.0, [1, 2, 4, 12, 18]


def run(subjects, lens, tag):
    rng = np.random.default_rng(SEED)
    inter = {s: np.load(PN / f"{s}_interictal_pernode.npy") for s in subjects}
    res = {}
    for k in KS:
        S = np.zeros((R, NCH))
        for r in range(R):
            A = inter[subjects[rng.integers(len(subjects))]]
            L = min(int(lens[rng.integers(len(lens))]), A.shape[0] // 4)
            st = int(rng.integers(0, A.shape[0] - L))
            blk = A[st:st + L].copy()
            base = np.delete(A, np.arange(st, st + L), axis=0)
            blk[:, rng.choice(NCH, size=k, replace=False)] *= ALPHA
            med = np.median(base, axis=0)
            mad = np.median(np.abs(base - med), axis=0) + 1e-9
            S[r] = np.percentile(np.abs((blk - med) / mad), 95, axis=0)
        res[k] = spreads(S)
        print(f"  {tag:<4} a={ALPHA} |S|={k:<3} spread={res[k].mean():.4f} "
              f"(sd {res[k].std():.4f})" + ("   [AUROC undefined]" if k == NCH else ""))
    return res


def main():
    lens = load_len_distribution()
    out = {}
    for tag, subs in [("VAL", VAL), ("TEST", TEST)]:
        print(f"--- {tag} ---"); out[tag] = run(subs, lens, tag); print()

    rows = [{"panel": t, "alpha": ALPHA, "n_injected": k,
             "spread_mean": round(float(v.mean()), 4),
             "spread_sd": round(float(v.std()), 4)}
            for t, d in out.items() for k, v in d.items()]
    with open(OUT / "synthetic_spread.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"wrote {OUT / 'synthetic_spread.csv'}")

    v = out["VAL"]
    _, p_g = mannwhitneyu(v[18], v[1], alternative="greater")
    _, p_2 = mannwhitneyu(v[18], v[1], alternative="two-sided")
    print(f"\n=== G-S4' (VAL, D6.1) ===")
    print(f"  spread(|S|=18) = {v[18].mean():.4f}   spread(|S|=1) = {v[1].mean():.4f}")
    print(f"  one-sided p = {p_g:.3e} | two-sided p = {p_2:.3e}")
    print("  VERDICT:", "PASS — proceed to real labels"
          if p_g < 0.05 else
          "FAIL — normalised entropy is not a usable diffuseness metric here; "
          "redesign the generalized branch of §4.5 and report as a methodological negative")


if __name__ == "__main__":
    main()