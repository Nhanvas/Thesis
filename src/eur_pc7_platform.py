#!/usr/bin/env python
"""eur_pc7_platform.py -- PC7, descriptive check added AFTER the reading (Track F, chat D34-F, 21/11/2026; approved by the
author 11:40). Not part of DESIGN_PC7.md's reading rule: written after G-pc7rep of EUR_PC7_B came back DIFF (same
library versions, different training arithmetic). Question: do the seeds trained on EUR_PC7_B's machine differ from those
trained on the machine of EUR_PC7_A and PC1 (whose arithmetic matched, G-pc7rep PASS)?
Evidence of the machine type: ms per training step from each checkpoint's _DONE.json. Test: difference of group means of
each seed-level metric (seeds.csv of src/eur_pc7_read.py), two-sided permutation p over 20,000 relabellings (rng 0).
  python src/eur_pc7_platform.py --read results/eureka_d34f/pc7 --runs results/eureka_d34f/pc7_A results/eureka_d34f/pc7_B \
      --ref results/eureka_d32f/pc1_r0
Outputs (in --read): platform.csv, platform.md.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

SETS = ["development", "test", "chb24", "siena"]
METRICS = ("sens", "f1", "fa")
N_PERM, RNG_SEED = 20_000, 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--read", required=True)
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--ref", required=True)
    a = ap.parse_args()
    rd = Path(a.read)
    S = pd.read_csv(rd / "seeds.csv")
    ms = {}
    for d in [Path(a.ref)] + [Path(r) for r in a.runs]:
        for f in sorted((d / "models" / "R0").glob("*_DONE.json")):
            j = json.loads(f.read_text())
            ms.setdefault(j["tag"], j["ms_per_step"])            # reused seeds: the reference's (PC1) training
    S["ms_per_step"] = S.seed.map(ms)
    S["machine"] = np.where(S.origin == "pc7_B", "B (G-pc7rep DIFF)", "A + PC1 (G-pc7rep PASS)")
    rng = np.random.default_rng(RNG_SEED)
    rows = []
    for st in SETS:
        for met in METRICS:
            c = f"{st}_R0_{met}"
            a_ = S.loc[S.machine.str.startswith("A"), c].to_numpy(float)
            b_ = S.loc[S.machine.str.startswith("B"), c].to_numpy(float)
            d = b_.mean() - a_.mean()
            allv, n = np.r_[a_, b_], len(b_)
            perm = np.array([(lambda p: allv[p[:n]].mean() - allv[p[n:]].mean())(rng.permutation(len(allv)))
                             for _ in range(N_PERM)])
            rows.append(dict(set=st, metric=met, n_a=len(a_), n_b=len(b_), mean_a=a_.mean(), mean_b=b_.mean(), diff_b_minus_a=d,
                             p_perm=float((np.abs(perm) >= abs(d)).mean()), sd_a=a_.std(ddof=1), sd_b=b_.std(ddof=1)))
    T = pd.DataFrame(rows)
    T.to_csv(rd / "platform.csv", index=False)
    g = S.groupby("machine").ms_per_step.agg(["min", "max", "count"])
    L = ["# PC7 — machine check (descriptive, added after the reading)", "",
         "Written after G-pc7rep of EUR_PC7_B came back DIFF (same library versions, different training arithmetic); not "
         "part of the reading rule of `DESIGN_PC7.md`. Two-sided permutation test of the difference of group means "
         f"({N_PERM:,} relabellings).", "", "Training speed (ms per step, from the checkpoints' _DONE.json):", "",
         "| machine group | seeds | ms per step |", "|---|---|---|"]
    for m, r in g.iterrows():
        L.append(f"| {m} | {int(r['count'])} | {r['min']:.2f}–{r['max']:.2f} |")
    L += ["", "| set | metric | A + PC1 mean (n) | B mean (n) | B − (A + PC1) | permutation p |", "|---|---|---|---|---|---|"]
    for _, r in T.iterrows():
        f = (lambda x: f"{x:.1f}") if r.metric == "fa" else (lambda x: f"{x:.3f}")
        L.append(f"| {r.set} | {r.metric} | {f(r.mean_a)} ({r.n_a}) | {f(r.mean_b)} ({r.n_b}) | {r.diff_b_minus_a:+.3f} | {r.p_perm:.3f} |")
    (rd / "platform.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
