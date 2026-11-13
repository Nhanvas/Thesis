#!/usr/bin/env python
"""
r2_rpdm1.py -- research track, stage RP, step RP-dm group 1 (chat D25-F, approved 14/11 01:07): the Chapter 2 numbers of
report version A2 (path 2, board R190) that follow from committed files without any run (REPORT_REVISION_PLAN.md §9.2,
A2 column). Read only; writes results/r2/r1_system/rp/rpdm/group1.csv and SUMMARY.md.

  F-R170.1  scored hours per set: results/r2/r0_data/chb/inventory_cases.csv, column hours_used_windows (the complete
            copy; chb12_27-29 are not read by the record loader, so path 2 excludes them)
  F-R170.2  training windows: results/r2/r1_system/rp/models/gae_v2_clean_seed4.json n_train (seeds 1-3 = R1's gate
            R1.1-training, run/SUMMARY.md: same data, same count)
  F-R170.3  k per seed: results/r2/r1_system/rp/rp2/k.json
  F-R170.4  validation loss per seed: results/r2/r1_system/rp/demo_model.json
  F-R170.6  application model: demo_model.json (seed 3, lowest validation loss)
  F-dm.3b   largest per-patient budget among the 15 development patients, per seed: clip(q_raw, 0.005, 0.02) of
            rp2/q.csv (+ the median q_raw, = 0.005 by the calibration rule of k)
  F-dm.6    5-SD flag share of the non-seizure training windows (non-ictal, non-buffer) of the 12 training patients, all
            files: R0's counts (stats_earlier/*.json n_rejected, n_interictal; chb21 from diff_chb11_chb21.json
            counts_complete). The submitted report's 46 % came from a file sample (results/raw_eeg_view: seizure files + 2
            random files per training patient, all files of the validation patients); this is the all-file value.
Not here (need a run): F-dm.7 (flag share of seizure windows: chb12's seizure windows under R0's thresholds are not in a
committed file), F-dm.8 (from RP7), F-dm.1, .2, .3a, .4, .5, .9 (RP_SERIES).

Run: python src/r2_rpdm1.py      (seconds)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
R0 = ROOT / "results" / "r2" / "r0_data" / "chb"
RUN = ROOT / "results" / "r2" / "r1_system" / "run"
RP = ROOT / "results" / "r2" / "r1_system" / "rp"
OUT = RP / "rpdm"
TRAIN = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08", "chb09", "chb12", "chb19", "chb20", "chb21", "chb23"]
VAL = ["chb10", "chb11", "chb22"]
TEST = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
SEEDS = [1, 2, 3, 4]


def main():
    rows = []
    add = lambda i, item, value, source, note="": rows.append(dict(id=i, item=item, value=value, source=source, note=note))  # noqa: E731
    inv = pd.read_csv(R0 / "inventory_cases.csv").set_index("case")
    for name, cases in (("training", TRAIN), ("validation", VAL), ("test", TEST)):
        add("F-R170.1", f"scored hours, {name}", round(float(inv.loc[cases, "hours_used_windows"].sum()), 2),
            "results/r2/r0_data/chb/inventory_cases.csv (hours_used_windows)",
            f"seizures in used files {int(inv.loc[cases, 'seizures_in_used_files'].sum())}")
    s4 = json.loads((RP / "models" / "gae_v2_clean_seed4.json").read_text())
    n4 = s4.get("n_train", s4.get("meta", {}).get("n_train"))
    n4 = int(sum(n4.values())) if isinstance(n4, dict) else int(n4)
    add("F-R170.2", "training windows (clean, 12 training patients), every seed", n4,
        "results/r2/r1_system/rp/models/gae_v2_clean_seed4.json", "seed 4; seeds 1-3 = R1 gate R1.1-training n_train 270758 (run/SUMMARY.md), same data")
    k = json.loads((RP / "rp2" / "k.json").read_text())["k"]
    dm = json.loads((RP / "demo_model.json").read_text())
    for s in SEEDS:
        add("F-R170.3", f"k, seed {s}", round(float(k[f"clean_seed{s}"]), 4), "results/r2/r1_system/rp/rp2/k.json")
    for s in SEEDS:
        add("F-R170.4", f"validation loss, seed {s}", round(float(dm["validation_loss"][str(s)]), 6),
            "results/r2/r1_system/rp/demo_model.json")
    add("F-R170.6", "application model (lowest validation loss)", f"seed {dm['seed']}", "results/r2/r1_system/rp/demo_model.json",
        f"checkpoint {dm['checkpoint']}")
    q = pd.read_csv(RP / "rp2" / "q.csv")
    q = q[q.set == "development"].copy()
    if q.subject.nunique() != 15:
        raise SystemExit("STOP: rp2/q.csv does not hold 15 development patients")
    q["p"] = q.q_raw.clip(0.005, 0.02)
    for s in SEEDS:
        d = q[q.seed == f"clean_seed{s}"]
        i = d.p.idxmax()
        add("F-dm.3b", f"largest development budget, seed {s}", round(float(d.p.max()), 4),
            "results/r2/r1_system/rp/rp2/q.csv", f"patient {d.loc[i, 'subject']}; median q_raw {d.q_raw.median():.5f}; "
            f"patients at the upper limit 0.02: {int((d.p >= 0.02).sum())}")
    dif = json.loads((R0 / "diff_chb11_chb21.json").read_text())
    rej = cln = 0
    for c in TRAIN:
        st = json.loads((R0 / "stats_earlier" / f"{c}_stats.json").read_text())
        cnt = dif[c]["counts_complete"] if c in dif else st
        rej += int(cnt["n_rejected"]); cln += int(cnt["n_interictal"])
    add("F-dm.6", "5-SD flag share of non-seizure training windows (12 training patients, all files)",
        round(rej / (rej + cln), 4), "results/r2/r0_data/chb/stats_earlier/*.json + diff_chb11_chb21.json (chb21 complete)",
        f"flagged {rej}, not flagged {cln} (computed)")
    T = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    T.to_csv(OUT / "group1.csv", index=False)
    L = ["# RP-dm group 1 — Chapter 2 numbers of version A2 from committed files (no run)\n",
         "Script `src/r2_rpdm1.py`. Values are read from the named files; derived values are computed.\n",
         "| ID | item | value | source | note |", "|---|---|---|---|---|"]
    L += [f"| {r.id} | {r.item} | {r.value} | `{r.source}` | {r.note} |" for r in T.itertuples()]
    L += ["\nNot here (need a run): F-dm.7 (flag share of seizure windows; chb12's seizure windows under R0's thresholds are "
          "not in a committed file), F-dm.8 (from RP7, application seed 3 with label-free statistics vs RP2 seed 3), "
          "F-dm.1, F-dm.2, F-dm.3a, F-dm.4, F-dm.5, F-dm.9 (RP_SERIES, design to approve)."]
    (OUT / "SUMMARY.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(T.to_string(index=False))


if __name__ == "__main__":
    main()
