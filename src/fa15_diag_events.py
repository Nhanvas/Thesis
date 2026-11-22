#!/usr/bin/env python
"""
fa15_diag_events.py -- F-A1.5 / PC5 descriptive diagnostic of the reading (chat D35-F, 22/11; written AFTER the reading
of results/fa15/reading was seen -- logged as such in plan §12; no gate, no claim beyond description).
Question: are the ASR arm's extra false alarms more flagged time (budget) or the same time split into more, shorter
events (fragmentation, as PC1's 10a)? From the committed rows only (per_subject.csv: top = window budget, review_s =
flagged seconds, rec_s = recorded seconds, tp + fp = events), stage cpd, per set and evaluation, per arm: mean budget,
mean flagged fraction, events per patient-seed, mean event length (s), FP per day.
  python src/fa15_diag_events.py [--out results/fa15/reading]
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
import fa15_aggregate as A               # noqa: E402  (this chat's reading: row loading)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "results" / "fa15" / "reading"))
    a = ap.parse_args()
    C = pd.concat([A.load_rows(REPO / "results/r2/r1_system/rp/rp2/per_subject.csv", "control"),
                   A.load_rows(REPO / "results/fa15/fa15_ctrl/run/per_subject.csv", "control")], ignore_index=True)
    X = pd.concat([A.load_rows(REPO / f"results/fa15/{d}/run/per_subject.csv", "asr") for d in ("fa15_asr_a", "fa15_asr_b")],
                  ignore_index=True)
    rows = []
    for name, D in (("control", C), ("asr", X)):
        for st in A.SETS:
            for ev, b in A.EVALS.items():
                g = D[(D.set == st) & (D.budget == b) & (D.stage == "cpd")]
                n_ev = g.tp + g.fp
                rows.append(dict(arm=name, set=st, evaluation=ev, rows=len(g), budget_top=g.top.mean(),
                                 flagged_fraction=(g.review_s / g.rec_s).mean(), events_per_patient_seed=n_ev.mean(),
                                 mean_event_s=g.review_s.sum() / max(n_ev.sum(), 1), fp_per_day=(g.fp / g.nonict_h * 24).mean()))
    d = pd.DataFrame(rows)
    Path(a.out).mkdir(parents=True, exist_ok=True)
    d.to_csv(Path(a.out) / "diag_events.csv", index=False)
    print(d.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
