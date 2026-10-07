#!/usr/bin/env python
"""
veto_rule_check.py -- label-free rule on the training-patient features (read-only, seconds).
Rule: among windows flagged by the +-5 SD peak rule, veto those whose feature exceeds the q-th percentile of
the same patient's UNFLAGGED windows. Reports, per patient, the share of ictal windows vetoed (cost) and the
share of flagged non-ictal windows vetoed (benefit). Reads results/continuous_eval/artifact_feature_explore/features.csv.

Save as F:\\Study\\Thesis\\Code\\src\\veto_rule_check.py ; run from the repo root:  python src/veto_rule_check.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
d = pd.read_csv(ROOT / "results" / "continuous_eval" / "artifact_feature_explore" / "features.csv")
d["grp"] = np.where(d.ictal, "ictal", np.where(d.buffer, "buffer", np.where(d.flag_rule, "flagged", "background")))
for f in ["kurt_max", "crest_max"]:
    for q in (90, 95, 99):
        rows = []
        for s, g in d.groupby("subject"):
            t = np.percentile(g.loc[~g.flag_rule, f], q)
            v = g.flag_rule & (g[f] > t)
            rows.append((s, float(v[g.grp == "ictal"].mean()), float(v[g.grp == "flagged"].mean())))
        r = pd.DataFrame(rows, columns=["subject", "ictal_windows_vetoed", "flagged_windows_vetoed"])
        print(f"== {f}  q={q}")
        print(r.round(3).to_string(index=False))
