#!/usr/bin/env python
"""eur_pc1_merge.py -- reading of the retraining ablations PC1 (Track F, chat D32-F, 20/11/2026; design
results/eureka_d32f/DESIGN_PC1.md). Container only; reads the three committed run folders of EUR_PC1_R0 / _10a / _10b.

(1) M0: every run's V0 rows (per_subject, errors, curve) are identical as sets of rows (sorted; the row order follows
    the parallel pool) (the same V5 checkpoints and chain) -> STOP if not.
(2) The three runs are merged into one folder (V0 once, the arms R0, 10a, 10b) and src/eur_abl_aggregate.py (unchanged)
    makes T2 against V0 -- the R214 reading of the design (an arm replaces V5 only if arm - V0 passes on development).
(3) The FEATURE effect, the primary reading of the ablation: arm - R0 (both retrained here with the same recipe; only the
    node input differs), paired patient bootstrap as the aggregate (B = 10,000, rng 0, chb01 + chb21 one unit), own
    label-free point after the localizer, every set; plus R0 - V0 (the effect of retraining on CPU, descriptive).
Outputs (--out): the merged run files, aggregate/ (T2.md ...), pc1_feature.csv, T_PC1.md.
  python src/eur_pc1_merge.py --runs results/eureka_d32f/pc1_R0 results/eureka_d32f/pc1_10a results/eureka_d32f/pc1_10b \
      --out results/eureka_d32f/pc1
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import eur_abl_aggregate as AGG          # noqa: E402

FILES = ("per_subject.csv", "errors.csv", "curve.csv")


def canon(d):
    return d.sort_values(list(d.columns), kind="mergesort").reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    runs = [Path(r) for r in a.runs]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    merged, gates, ks, na = {f: [] for f in FILES}, [], [], {}
    v0 = None
    for i, r in enumerate(runs):
        cur = {f: pd.read_csv(r / f) for f in FILES}
        this_v0 = {f: canon(d[d.variant == "V0"]) for f, d in cur.items()}    # row order = pool order: compared sorted
        if v0 is None:
            v0 = this_v0
            for f in FILES:
                merged[f].append(this_v0[f])
        else:
            for f in FILES:
                if not this_v0[f].equals(v0[f]):
                    raise SystemExit(f"STOP M0: {r.name}: V0 rows of {f} differ from {runs[0].name}")
        for f in FILES:
            merged[f].append(cur[f][cur[f].variant != "V0"])
        k = pd.read_csv(r / "k.csv")
        ks.append(k if i == 0 else k[k.variant != "V0"])
        gates += json.loads((r / "gates.json").read_text())
        if (r / "not_available.json").exists():
            na.update(json.loads((r / "not_available.json").read_text()))
    print(f"M0 PASS: V0 rows identical in {len(runs)} runs")
    for f in FILES:
        pd.concat(merged[f], ignore_index=True).to_csv(out / f, index=False)
    pd.concat(ks, ignore_index=True).to_csv(out / "k.csv", index=False)
    (out / "gates.json").write_text(json.dumps(gates, indent=1, default=str))
    (out / "not_available.json").write_text(json.dumps(na))
    p = subprocess.run([sys.executable, str(ROOT / "src" / "eur_abl_aggregate.py"), "--run", str(out)],
                       capture_output=True, text=True, env=dict(os.environ))
    print(p.stdout[-1500:], p.stderr[-1500:])
    if p.returncode != 0:
        raise SystemExit("STOP: the aggregate failed")
    R, _, _, _, _ = AGG.load_run(out)
    P = AGG.per_subject(R)
    rng = np.random.default_rng(AGG.RNG_SEED)
    rows = []
    arms = [v for v in ("10a", "10b") if v in set(P.variant)]
    comps = [(v, "R0", f"{v} - R0 (feature effect)") for v in arms] + [("R0", "V0", "R0 - V0 (retraining on CPU)")]
    for st in AGG.SETS:
        g = P[(P.set == st) & (P.arm == "own") & (P.stage == "cpd")]
        for va, vb, name in comps:
            A = g[g.variant == va].set_index("subject")
            Bb = g[g.variant == vb].set_index("subject")
            if not len(A) or not len(Bb):
                continue
            for met in ("sens", "f1", "fa"):
                rows.append(dict(set=st, comparison=name, metric=met,
                                 reading="primary" if st == "development" else "descriptive",
                                 **AGG.boot_pair(A[met], Bb[met], rng)))
    T = pd.DataFrame(rows)
    T.to_csv(out / "pc1_feature.csv", index=False)
    L =["# Table T_PC1 — retraining ablations (feature effect)", "",
         "Per-patient means after the change point localizer, 4 seeds, own label-free point. Paired patient bootstrap "
         "(chb01 + chb21 one unit). Development = primary; test, chb24, Siena descriptive. R0 = the GAE retrained here "
         "with the full input (same recipe and platform as 10a / 10b).", "",
         "| comparison | set | Δ sensitivity | Δ F1 | Δ FP/day |", "|---|---|---|---|---|"]
    for (name, st), g in T.groupby(["comparison", "set"], sort=False):
        def c(m, dec=3):
            r = g[g.metric == m]
            if not len(r):
                return "—"
            r = r.iloc[0]
            return f"{r['diff']:+.{dec}f}" + (f" [{r.ci_lo:+.{dec}f}, {r.ci_hi:+.{dec}f}]" if np.isfinite(r.ci_lo) else "")
        L.append(f"| {name} | {st} | {c('sens')} | {c('f1')} | {c('fa', 1)} |")
    (out / "T_PC1.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
