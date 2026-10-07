#!/usr/bin/env python
"""
p2_test_bootstrap.py -- patient-level uncertainty of look #6 (no new look: reads the committed
outputs of e22_test_oneshot.py only; no model is run, no label is re-read).
Per test subject: 4-seed-mean TP, n_ref, FP, non-ictal hours, for the frozen P2 system after the
localizer and for E (P1 frozen). B = 10,000 resamples of the 8 subjects with replacement (seed 0);
95 % percentile intervals of final - E (pooled sensitivity, subject-mean sensitivity, FP/day) and of
the final system's own pooled and subject-mean sensitivity; all 8 and without chb15 (20 of 76
seizures). Seed SD measures initialisation only; this measures patient-to-patient uncertainty.
Run:  python src/p2_test_bootstrap.py        (seconds)
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "results" / "e22_test_oneshot"
B = 10_000


def main():
    R = pd.read_csv(D / "per_subject_seed.csv"); R = R[R.stage == "localized"]
    E = pd.read_csv(D / "reference_E.csv")
    cols = ["tp", "fp", "n_ref", "nonict_h"]
    F = R.groupby("subject")[cols].mean(); Eg = E.groupby("subject")[cols].mean().loc[F.index]
    subs = np.array(F.index)

    def stats(idx):
        f, e = F.loc[idx], Eg.loc[idx]
        fs, es = f.tp.sum() / f.n_ref.sum(), e.tp.sum() / e.n_ref.sum()
        fm, em = (f.tp / f.n_ref).mean(), (e.tp / e.n_ref).mean()
        return np.array([fs, fm, fs - es, fm - em,
                         f.fp.sum() / f.nonict_h.sum() * 24 - e.fp.sum() / e.nonict_h.sum() * 24])

    rng = np.random.default_rng(0)
    names = ("final pooled sens", "final subject-mean sens", "diff pooled sens", "diff subject-mean sens", "diff FP/day")
    lines = ["# Look #6 -- patient-level bootstrap (8 test subjects, 4-seed means, B = 10,000)\n", "```",
             "set             quantity                   point   95 % interval"]
    for lab, pool in (("all 8", subs), ("without chb15", subs[subs != "chb15"])):
        pt = stats(pool)
        bs = np.array([stats(rng.choice(pool, len(pool), replace=True)) for _ in range(B)])
        for j, n in enumerate(names):
            lo, hi = np.percentile(bs[:, j], [2.5, 97.5])
            lines.append(f"{lab:15s} {n:25s} {pt[j]:+7.3f}  [{lo:+7.3f}, {hi:+7.3f}]")
    lines.append("```")
    (D / "BOOTSTRAP.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
