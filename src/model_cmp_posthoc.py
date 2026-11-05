#!/usr/bin/env python
"""
model_cmp_posthoc.py -- POST-HOC checks of the model comparison rev 2, written AFTER the pre-registered analysis
(src/model_cmp_aggregate.py) was read on 03/11 22:15. Labelled post-hoc everywhere; never a headline.
Why: the own label-free point lets each model's budget rule set its own alarm rate (supervised models ended at
~34-35 FP/day vs the GAE's 28.4), so the registered own-point F1 mixes model quality with budget behaviour. The
fixed 0.005 point (same flagged-time share for every model) is already in the registered table A but had no
bootstrap; window AUROC (table A) had none either. Same paired subject bootstrap as analysis B (23 units, B = 10,000).
  python src/model_cmp_posthoc.py [--res results/model_cmp]   -> posthoc_bootstrap.csv
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
U = lambda s: "chb01" if s in ("chb01", "chb21") else s   # noqa: E731


def boot(a, r, B=10_000, seed=0):
    d = (a - r).dropna()
    units = sorted({U(s) for s in d.index})
    by = {u: [s for s in d.index if U(s) == u] for u in units}
    rng = np.random.default_rng(seed)
    st = [d.loc[[s for u in rng.choice(units, len(units)) for s in by[u]]].mean() for _ in range(B)]
    return dict(diff=d.mean(), lo=np.percentile(st, 2.5), hi=np.percentile(st, 97.5),
                wins=int((d > 0).sum()), losses=int((d < 0).sum()), n_cases=len(d), n_units=len(units))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", default=str(ROOT / "results" / "model_cmp"))
    res = Path(ap.parse_args().res)
    per = pd.read_csv(res / "per_subject.csv")
    au = pd.read_csv(res / "auroc.csv")
    fx = per[(per.point == "fixed0.005") & (per.stage == "localized")].copy()
    fx["f1"] = 2 * fx.tp / (2 * fx.tp + fx.fp + (fx.n_ref - fx.tp))
    fx["sens"] = fx.tp / fx.n_ref
    fx["fp_day"] = fx.fp / fx.nonict_h * 24
    rows = []
    for m in [m for m in ["mlp", "if", "svm", "hgb", "cnn"] if m in set(per.model)]:
        for col in ("f1", "sens", "fp_day"):
            a = fx[fx.model == m].set_index("subject")[col]
            r = fx[fx.model == "gae"].set_index("subject")[col]
            rows.append(dict(model=m, reference="gae", metric=f"{col}@fixed0.005", **boot(a, r)))
        rows.append(dict(model=m, reference="gae", metric="window_auroc",
                         **boot(au[au.model == m].set_index("subject").auroc,
                                au[au.model == "gae"].set_index("subject").auroc)))
    out = pd.DataFrame(rows)
    out.to_csv(res / "posthoc_bootstrap.csv", index=False)
    print("POST-HOC (not pre-registered):")
    print(out.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
