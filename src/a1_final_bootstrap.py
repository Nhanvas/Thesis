"""a1_final_bootstrap.py -- report version A1: patient-level bootstrap of the FINAL system's per-patient (macro)
sensitivity and FP/day on the 8 CHB-MIT test patients, 4-seed means (seeds 42, 1, 2, 3), from committed files only.

Method = the defense-time scripts, unchanged: per subject the 4-seed mean of tp, fp, n_ref, nonict_h after the localizer;
B = 10,000 resamples of the 8 subjects with replacement, numpy default_rng(0); 95 % percentile intervals.
Inputs: results/e22_test_oneshot/per_subject_seed.csv (held-out, stage localized),
        results/e23_test_look7/per_subject_seed.csv (point balanced, stage localized).
Gates (STOP on mismatch, 3 decimals): with the same resample sequence the script must reproduce
  G1 held-out subject-mean sensitivity 0.498 [0.226, 0.770]      (results/e22_test_oneshot/BOOTSTRAP.md)
  G2 final - held-out subject-mean sensitivity +0.070 [0.000, 0.201] (results/e23_test_look7/SUMMARY.md)
Usage: python -I a1_final_bootstrap.py <repo root>
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

B = 10_000
root = Path(sys.argv[1])
cols = ["tp", "fp", "n_ref", "nonict_h"]
h = pd.read_csv(root / "results/e22_test_oneshot/per_subject_seed.csv")
f = pd.read_csv(root / "results/e23_test_look7/per_subject_seed.csv")
H = h[h.stage == "localized"].groupby("subject")[cols].mean()
F = f[(f.point == "balanced") & (f.stage == "localized")].groupby("subject")[cols].mean().loc[H.index]
assert len(H) == 8 and (h[h.stage == "localized"].groupby("subject").size() == 4).all()
subs = np.array(H.index)


def stats(idx):
    a, b = F.loc[idx], H.loc[idx]
    fs, hs = (a.tp / a.n_ref).mean(), (b.tp / b.n_ref).mean()
    ff, hf = (a.fp / a.nonict_h * 24).mean(), (b.fp / b.nonict_h * 24).mean()
    return np.array([hs, fs, fs - hs, hf, ff, ff - hf])


names = ["held-out sensitivity", "final sensitivity", "final - held-out sensitivity",
         "held-out FP/day", "final FP/day", "final - held-out FP/day"]
rng = np.random.default_rng(0)
bs = np.array([stats(rng.choice(subs, len(subs), replace=True)) for _ in range(B)])
pt = stats(subs)
ci = np.percentile(bs, [2.5, 97.5], axis=0).T

r = lambda x: round(float(x) + 0.0, 3)
g1 = (r(pt[0]), r(ci[0][0]), r(ci[0][1])) == (0.498, 0.226, 0.770)
g2 = (r(pt[2]), r(ci[2][0]), r(ci[2][1])) == (0.070, 0.000, 0.201)
print(f"G1 held-out reproduced: {g1} ({pt[0]:.3f} [{ci[0][0]:.3f}, {ci[0][1]:.3f}])")
print(f"G2 difference reproduced: {g2} ({pt[2]:+.3f} [{ci[2][0]:+.3f}, {ci[2][1]:+.3f}])")
if not (g1 and g2):
    sys.exit("STOP: a gate failed; no value is reported")
print("\nquantity (8 test patients, 4-seed means, per-patient mean)   point   95 % interval")
for n, p, (lo, hi) in zip(names, pt, ci):
    print(f"{n:40s} {p:+8.3f}  [{lo:+8.3f}, {hi:+8.3f}]")
