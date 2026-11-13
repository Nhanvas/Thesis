#!/usr/bin/env python
"""
r2_rp4b_synthetic_test.py -- synthetic test of the estimators of src/r2_rp4b.py (no real data):
  (1) design_bw: within columns have patient mean 0, between columns are constant within a patient and equal the mean;
  (2) scenario "between only": the log amplitude ratio acts only through the patient mean (true W_amp = 0, B_amp = 2)
      -> the W_amp interval contains 0 and lies around 0, the B_amp interval excludes 0; the pooled coefficient would mix both;
  (3) scenario "within only": true W_amp = 1.5, B_amp = 0 -> the W_amp interval contains 1.5 and excludes 0, the B_amp
      interval contains 0; conditional logistic gives W_amp near 1.5;
  (4) patients with all seizures caught (or all missed) are counted as not informative by clogit;
  (5) one-class input returns NaN coefficients without failing.
  python src/r2_rp4b_synthetic_test.py      (about 1 min)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r2_rp4b as M  # noqa: E402

CHECKS = []


def check(c, what):
    CHECKS.append(bool(c)); print(("PASS " if c else "FAIL ") + what)


def sim(n_pat, n_sz, w, bb, seed):
    rng = np.random.RandomState(seed)
    rows = []
    for i in range(n_pat):
        mu = rng.normal(0.4, 0.5)                       # patient mean log amplitude ratio
        dmu = rng.normal(3.5, 0.5)                      # patient mean log duration
        for j in range(n_sz):
            a = mu + rng.normal(0, 0.5)
            du = dmu + rng.normal(0, 0.4)
            eta = -0.5 + w * (a - mu) + bb * mu
            rows.append(dict(subject=f"p{i:02d}", amp_ratio=np.exp(a), duration_s=np.exp(du),
                             caught=bool(rng.rand() < 1 / (1 + np.exp(-eta)))))
    return pd.DataFrame(rows)


def main():
    d = sim(10, 5, 1.0, 1.0, 0)
    X = M.design_bw(d)
    g = d.subject.values
    check(np.allclose(pd.Series(X[:, 0]).groupby(g).mean(), 0, atol=1e-12)
          and np.allclose(pd.Series(X[:, 2]).groupby(g).mean(), 0, atol=1e-12), "within columns have patient mean 0")
    check(np.allclose(pd.Series(X[:, 1]).groupby(g).std(ddof=0), 0, atol=1e-12)
          and np.allclose(pd.Series(X[:, 1]).groupby(g).first().values,
                          np.log(d.amp_ratio).groupby(g).mean().values), "between columns = patient means")
    A = sim(60, 10, 0.0, 2.0, 1)
    r = M.bw_fit(A, b=300, seed=42)
    check(r["W_amp_lo"] < 0 < r["W_amp_hi"] and abs(r["W_amp"]) < 0.6, f"between only: W_amp {r['W_amp']:+.2f} "
          f"[{r['W_amp_lo']:+.2f}, {r['W_amp_hi']:+.2f}] contains 0")
    check(r["B_amp_lo"] > 0 and 1.0 < r["B_amp"] < 3.5, f"between only: B_amp {r['B_amp']:+.2f} "
          f"[{r['B_amp_lo']:+.2f}, {r['B_amp_hi']:+.2f}] excludes 0")
    check(r["WminusB_amp_hi"] < 0, "between only: W - B interval excludes 0")
    c = M.clogit(A)
    check(c["W_amp_lo"] < 0 < c["W_amp_hi"], f"between only: clogit W_amp {c['W_amp']:+.2f} contains 0")
    Bd = sim(60, 10, 1.5, 0.0, 2)
    r = M.bw_fit(Bd, b=300, seed=42)
    check(r["W_amp_lo"] > 0 and r["W_amp_lo"] < 1.5 < r["W_amp_hi"], f"within only: W_amp {r['W_amp']:+.2f} "
          f"[{r['W_amp_lo']:+.2f}, {r['W_amp_hi']:+.2f}] contains 1.5, excludes 0")
    check(r["B_amp_lo"] < 0 < r["B_amp_hi"], f"within only: B_amp {r['B_amp']:+.2f} contains 0")
    check(r["n_boot_ok"] == 300, "every bootstrap resample fitted")
    c = M.clogit(Bd)
    check(c["W_amp_lo"] < 1.5 < c["W_amp_hi"] and c["W_amp_lo"] > 0, f"within only: clogit W_amp {c['W_amp']:+.2f} "
          f"[{c['W_amp_lo']:+.2f}, {c['W_amp_hi']:+.2f}]")
    E = Bd.copy()
    E.loc[E.subject.isin(["p00", "p01"]), "caught"] = True
    E.loc[E.subject == "p02", "caught"] = False
    c = M.clogit(E)
    check(c["n_informative_patients"] <= 57 and c["n_patients"] == 60, "all-caught / all-missed patients not informative")
    O = Bd.copy(); O["caught"] = True
    r = M.bw_fit(O, b=10)
    check(np.isnan(r["W_amp"]) and r["n_boot_ok"] == 0, "one class -> NaN, no failure")
    r1, r2 = M.bw_fit(A, b=50, seed=42), M.bw_fit(A, b=50, seed=42)
    check(r1 == r2, "bootstrap is reproducible with the same seed")
    print(f"\n{sum(CHECKS)} / {len(CHECKS)} checks PASS")
    sys.exit(0 if all(CHECKS) else 1)


if __name__ == "__main__":
    main()
