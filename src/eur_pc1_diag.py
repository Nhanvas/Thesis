#!/usr/bin/env python
"""eur_pc1_diag.py -- diagnostics of the PC1 reading (Track F, chat D33-F, 20/11/2026). Read only; container only.

Two findings of the PC1 merge (results/eureka_d32f/pc1/T_PC1.md) were not predicted by DESIGN_PC1.md section 3 and are
diagnosed here from the committed outputs before they are interpreted (instructions section 1 item 18):
  (1) 10a - R0: FP/day rose (+26) where H10a predicted a fall. Candidate causes told apart:
      (a) a larger alarm budget (k recalibrated lower)  -> check: share of windows flagged (`top`) per variant;
      (b) fragmentation: the same budget split into more, shorter events -> check: events, seconds per event and
          seizures found at the FIXED 0.5 % budget (identical budget for every variant).
  (2) R0 - V0 (retraining on CPU): sensitivity fell. Candidate causes told apart:
      (a) a failed / unconverged training -> check: first / last training loss and validation loss of every seed;
      (b) one seed -> check: per-seed sensitivity and the per-patient means without that seed;
      (c) a shift common to every seed -> check: same, by set.
Gate D0: the per-patient means recomputed here equal the aggregate's per_subject_means.csv (own budget, CPD stage).
Outputs (--out): events.csv, budget.csv, training.csv, seeds.csv, exclude_seed.csv, gates.json, DIAG_PC1.md.
  python src/eur_pc1_diag.py --merged results/eureka_d32f/pc1 \
      --runs results/eureka_d32f/pc1_r0 results/eureka_d32f/pc1_10a results/eureka_d32f/pc1_10b \
      --out results/eureka_d32f/pc1/diag
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import eur_abl_aggregate as AGG          # noqa: E402

VARS = ["V0", "R0", "10a", "10b"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--merged", required=True)
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    merged, out = Path(a.merged), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    R, _, _, _, _ = AGG.load_run(merged)
    R = R[R.variant.isin(VARS)].copy()
    gates = []

    # D0 -- the per-patient means used below equal the aggregate's
    P = AGG.per_subject(R)
    ref = pd.read_csv(merged / "aggregate" / "per_subject_means.csv")
    key = ["set", "variant", "arm", "stage", "subject"]
    m = P.merge(ref, on=key, suffixes=("", "_ref"))
    m = m[m.variant.isin(VARS)]
    worst = max(float(np.nanmax(np.abs(m[c] - m[c + "_ref"]))) for c in ("sens", "f1", "fa"))
    ok = len(m) == len(P) and worst <= 1e-12
    gates.append(dict(gate="D0", status="PASS" if ok else "FAIL", rows=int(len(m)), max_abs_diff=worst))
    if not ok:
        (out / "gates.json").write_text(json.dumps(gates, indent=1))
        raise SystemExit(f"STOP D0: {gates[-1]}")

    # (1) events at each budget (CPD stage, every seed pooled; development and test)
    C = R[R.stage == "cpd"].copy()
    C["ev"] = C.tp + C.fp
    ev = (C[C.set.isin(["development", "test"])]
          .groupby(["set", "arm", "variant"])
          .agg(tp=("tp", "sum"), fp=("fp", "sum"), events=("ev", "sum"), review_s=("review_s", "sum"),
               rec_s=("rec_s", "sum"), n_ref=("n_ref", "sum")).reset_index())
    ev["flagged_time_pct"] = 100 * ev.review_s / ev.rec_s
    ev["s_per_event"] = ev.review_s / ev.events
    ev.to_csv(out / "events.csv", index=False)
    bud = (C[C.arm == "own"].groupby(["set", "variant", "seed"]).top.mean().unstack("seed"))
    bud["mean"] = bud.mean(axis=1)
    bud.reset_index().to_csv(out / "budget.csv", index=False)

    # (2a) training of the retrained arms
    trows = []
    for r in a.runs:
        for f in sorted(Path(r).glob("models/*/gae_v2_clean_seed*.json")):
            if f.name.endswith("_DONE.json"):
                continue
            d = json.loads(f.read_text())
            trows.append(dict(arm=d["arm"], seed=d["seed"], n_params=d["n_params"], n_train=d["n_train"],
                              first_loss=d["first_loss"], last_loss=d["last_loss"], final_val=d["final_val"]))
    T = pd.DataFrame(trows).sort_values(["arm", "seed"])
    T.to_csv(out / "training.csv", index=False)

    # (2b, c) per-seed sensitivity and FP/day (per-patient mean over the set), own budget, CPD
    O = C[C.arm == "own"].copy()
    O["sens"] = O.tp / O.n_ref.where(O.n_ref > 0)
    O["fa"] = O.fp / O.nonict_h * 24
    S = (O.groupby(["set", "variant", "seed", "subject"])[["sens", "fa"]].mean()
         .groupby(["set", "variant", "seed"]).mean().reset_index())
    S.to_csv(out / "seeds.csv", index=False)
    X = []
    for excl in (None, "clean_seed2"):
        g = O if excl is None else O[O.seed != excl]
        q = g.groupby(["set", "variant", "subject"])[["sens", "fa"]].mean().groupby(["set", "variant"]).mean()
        q = q.reset_index()
        q["seeds"] = "all 4" if excl is None else "without seed 2"
        X.append(q)
    X = pd.concat(X, ignore_index=True)
    X.to_csv(out / "exclude_seed.csv", index=False)
    (out / "gates.json").write_text(json.dumps(gates, indent=1))

    # report
    L = ["# DIAG_PC1 — diagnostics of the PC1 reading (D33-F, 20/11)", "",
         "Read only, from the committed PC1 outputs (`src/eur_pc1_diag.py`; gate D0 = the per-patient means equal the "
         f"aggregate's: {gates[0]['status']}, {gates[0]['rows']} rows). CPD stage; every seed pooled for counts.", "",
         "## 1 · Why 10a has more false alarms (H10a predicted fewer)", "",
         "Share of windows flagged at the own label-free point (mean over patients and seeds, %):", ""]
    for st in ("development", "test"):
        L.append(f"- {st}: " + ", ".join(f"{v} {100 * bud.loc[(st, v), 'mean']:.2f}" for v in VARS))
    L += ["", "| set | budget | variant | events | seizures found | false alarms | s per event | flagged time % |",
          "|---|---|---|---|---|---|---|---|"]
    for _, r in ev.sort_values(["set", "arm", "variant"]).iterrows():
        L.append(f"| {r.set} | {r.arm} | {r.variant} | {int(r.events)} | {int(r.tp)} / {int(r.n_ref)} | {int(r.fp)} | "
                 f"{r.s_per_event:.1f} | {r.flagged_time_pct:.2f} |")
    L += ["", "## 2 · Training of the retrained arms", "",
          "| arm | seed | parameters | training windows | first loss | last loss | validation loss |",
          "|---|---|---|---|---|---|---|"]
    for _, r in T.iterrows():
        L.append(f"| {r.arm} | {r.seed} | {r.n_params} | {r.n_train} | {r.first_loss:.5f} | {r.last_loss:.5f} | "
                 f"{r.final_val:.5f} |")
    L += ["", "## 3 · Sensitivity per seed (per-patient mean, own point, CPD) and without seed 2", "",
          "| set | variant | seed 42 | seed 1 | seed 2 | seed 3 | all 4 | without seed 2 |", "|---|---|---|---|---|---|---|---|"]
    for st in ("development", "test", "chb24", "siena"):
        for v in VARS:
            s = S[(S.set == st) & (S.variant == v)].set_index("seed").sens
            x = X[(X.set == st) & (X.variant == v)].set_index("seeds").sens
            L.append(f"| {st} | {v} | " + " | ".join(f"{s.get(f'clean_seed{i}', np.nan):.3f}" for i in (42, 1, 2, 3))
                     + f" | {x['all 4']:.3f} | {x['without seed 2']:.3f} |")
    (out / "DIAG_PC1.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
