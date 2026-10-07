#!/usr/bin/env python
"""
ceiling_check.py -- how visible is each seizure in the fused score, with and without the
high-amplitude ("artifact"-flagged) windows in the reference set?

Save as F:\\Study\\Thesis\\Code\\src\\ceiling_check.py ; run from the repo root:
    python src/ceiling_check.py

Cache only (continuous_eval scope-T fused score + masks). No EDF is read, nothing is trained.
For each seizure (a contiguous run of ictal windows):
    peak   = max of the 15-window centered moving average inside the seizure (what the CPD stage sees)
    e_all  = share of ordinary non-ictal windows whose smoothed score >= peak
    e_clean= same, after also removing windows flagged by the +-5 SD rule
A small e means the seizure stands out. If e_clean is much smaller than e_all for many seizures,
removing high-amplitude windows has headroom; if the two are close, it does not.
The labels are used only to locate seizures for this diagnostic. Nothing is selected from it.
Validation and test are summarized separately and descriptively.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import continuous_eval as CE   # noqa: E402

VAL = list(CE.VAL_SUBJS)
TEST = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
MA = 15
OUT = CE.OUT_DIR / "ceiling_check"


def runs(mask):
    d = np.diff(np.concatenate([[0], mask.astype(int), [0]]))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for subj in VAL + TEST:
        m = CE.load_mask(subj)
        sc = np.asarray(CE.load_subject_data("T", subj)["score"], dtype=np.float64)
        sm = pd.Series(sc).rolling(MA, center=True, min_periods=1).mean().values
        base = ~(m["is_ictal"] | m["is_buffer"] | m["is_signal_loss"])
        clean = base & ~m["is_artifact"]
        ref_all, ref_clean = np.sort(sm[base]), np.sort(sm[clean])
        for a, b in runs(m["is_ictal"]):
            peak = sm[a:b].max()
            e_all = 1 - np.searchsorted(ref_all, peak, side="left") / len(ref_all)
            e_cl = 1 - np.searchsorted(ref_clean, peak, side="left") / len(ref_clean)
            rows.append(dict(set="val" if subj in VAL else "test", subject=subj, start=int(a), n_win=int(b - a),
                             e_all=e_all, e_clean=e_cl))
        print(subj, "seizure runs:", sum(1 for r in rows if r["subject"] == subj),
              "| flagged share of reference:", round(1 - clean.sum() / base.sum(), 3))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "per_seizure.csv", index=False)

    L = ["# Seizure visibility with and without high-amplitude windows in the reference", "",
         "e = share of reference windows whose smoothed score is >= the seizure's peak (smaller = more visible).", "",
         "| set | subject | seizures | median e_all | median e_clean | e_all <= 5% | e_clean <= 5% | e_all <= 2% | e_clean <= 2% |",
         "|---|---|---|---|---|---|---|---|---|"]
    for key, g in list(df.groupby(["set", "subject"])) + [((s, "ALL"), x) for s, x in df.groupby("set")]:
        L.append(f"| {key[0]} | {key[1]} | {len(g)} | {g.e_all.median():.3f} | {g.e_clean.median():.3f} | "
                 f"{(g.e_all <= .05).sum()} | {(g.e_clean <= .05).sum()} | "
                 f"{(g.e_all <= .02).sum()} | {(g.e_clean <= .02).sum()} |")
    L += ["", "Counts of seizures are over contiguous ictal runs, which can differ slightly from the annotated "
              "seizure count where a seizure crosses a file boundary. Descriptive only."]
    (OUT / "ceiling_check.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
