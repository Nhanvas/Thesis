#!/usr/bin/env python
"""
attribution_diagnostics.py — ATTRIBUTION_SPEC §4.7 internal validity + A2/D4 seed robustness.

LABEL-FREE. Answers three questions before any label is scored:
  (i)  seed robustness — do the 4 GAE seeds agree on the ranking?
  (ii) subject-level bias — is top-1 constant within a subject (= GAE quirk, not ictal signal)?
  (iii) C1 consistency — are rankings more alike within a subject than across, vs a random null?
"""
import csv, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import numpy as np
from scipy.stats import spearmanr

OUT   = ROOT / "results" / "attribution_v6"
SRC   = OUT / "attribution_scores.csv"
SEEDS = [42, 1, 2, 3]
NPERM, SEED = 2000, 42


def main():
    if not SRC.is_file():
        print(f"[FATAL] missing {SRC}", file=sys.stderr); sys.exit(1)

    S = {}
    for r in csv.DictReader(open(SRC)):
        if r["agg"] != "p95":
            continue
        S.setdefault((int(r["seed"]), r["subject"], int(r["seizure_idx"])),
                     np.zeros(18))[int(r["ch_idx"])] = float(r["score"])
    keys = sorted({(s, k) for (sd, s, k) in S if sd == 42})
    print(f"loaded {len(keys)} seizures x {len(SEEDS)} seeds (p95)\n")

    # (i) seed robustness
    top_agree, rho_seed = [], []
    for (s, k) in keys:
        v = [S[(sd, s, k)] for sd in SEEDS]
        t = [int(np.argmax(x)) for x in v]
        top_agree.append(sum(1 for x in t[1:] if x == t[0]) / (len(SEEDS) - 1))
        rho_seed += [spearmanr(v[0], v[i]).statistic for i in range(1, len(v))]
    print("(i) SEED ROBUSTNESS (seed42 vs 1/2/3)")
    print(f"    top-1 agreement : {np.mean(top_agree):.3f}  "
          f"(all 3 agree on {np.mean([a == 1.0 for a in top_agree])*100:.0f}% of seizures)")
    print(f"    Spearman rho    : {np.mean(rho_seed):.3f} +- {np.std(rho_seed):.3f}\n")

    # (ii) within-subject top-1 concentration vs null
    rng = np.random.default_rng(SEED)
    print("(ii) WITHIN-SUBJECT TOP-1 CONCENTRATION (seed42)")
    print(f"     {'subject':<9}{'n_sz':>5}{'distinct':>9}{'max_share':>11}{'null_p95':>10}  verdict")
    rows = []
    for subj in sorted({s for s, _ in keys}):
        ks = [k for s, k in keys if s == subj]
        t = [int(np.argmax(S[(42, subj, k)])) for k in ks]
        n = len(ks)
        share = max(np.bincount(t, minlength=18)) / n
        null = np.array([max(np.bincount(rng.integers(0, 18, n), minlength=18)) / n
                         for _ in range(NPERM)])
        p95 = float(np.percentile(null, 95))
        flag = "CONCENTRATED" if share > p95 else "ok"
        rows.append({"subject": subj, "n_seizures": n, "distinct_top1": len(set(t)),
                     "max_share": round(float(share), 3), "null_p95": round(p95, 3),
                     "verdict": flag})
        print(f"     {subj:<9}{n:>5}{len(set(t)):>9}{share:>11.3f}{p95:>10.3f}  {flag}")

    # (iii) C1 consistency: within- vs across-subject rank similarity
    def mean_pair_rho(pairs):
        return float(np.mean([spearmanr(S[(42, a, b)], S[(42, c, d)]).statistic
                              for (a, b), (c, d) in pairs])) if pairs else np.nan
    within = [(x, y) for i, x in enumerate(keys) for y in keys[i + 1:] if x[0] == y[0]]
    across = [(x, y) for i, x in enumerate(keys) for y in keys[i + 1:] if x[0] != y[0]]
    sel = rng.choice(len(across), size=min(3000, len(across)), replace=False)
    w, a = mean_pair_rho(within), mean_pair_rho([across[i] for i in sel])
    print(f"\n(iii) C1 CONSISTENCY (mean pairwise Spearman of s)")
    print(f"      within-subject  : {w:.3f}  (n={len(within)} pairs)")
    print(f"      across-subject  : {a:.3f}  (n={len(sel)} sampled pairs)")
    print(f"      delta           : {w - a:+.3f}")

    with open(OUT / "attribution_diagnostics.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
    print(f"\nwrote {OUT / 'attribution_diagnostics.csv'}")


if __name__ == "__main__":
    main()