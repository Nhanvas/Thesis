#!/usr/bin/env python
"""
fa16_repl_aggregate.py -- verification and reading of the F-A1.6 replication over partitions 0-5 (src/fa16_repl.py;
plan §12 17/11 08:10). Written and committed before any output of FA16_REPL exists.

Rows: GAE and MLP-AE = the record (partition 0 results/model_cmp, partitions 1-5 results/f1_repcv/raw/p{r}; the run's
G-base proves the GAE rows reproduce on Kaggle); K-means `km` (primary) and `km_u` (u-CBLOF, secondary) = the run
(partition 0 equal to FA16_KMEANS by gate G-km0).

Checks (STOP):
  A0  every run gate present and PASS (D0, G-parts, G-base x 5, G-kmD, G-km0 x 2, G-done); 24 cases x 2 points x 2
      stages for km and km_u in partitions 0-5; n_ref and non-seizure hours of every case = partition 0's
  A1  the reading code (f1_aggregate.per_case / boot_mean and the F2 rule, used unchanged) reproduces the committed F2
      reading of the MLP-AE from the record: results/f1_repcv/F2_across_partitions.csv (mean, lo, hi; 1e-12) and
      VERDICT.json (n_pos, verdict)
Reading (the F1 / F2 reading of the record applied unchanged to K-means; unit = per-case mean over the 24 cases, own
label-free point, after CPD):
  per partition: sensitivity, precision, F1, FP/day, window AUROC, seizures caught, false alarms of gae, mlp, km, km_u;
  across partitions: mean +- SD and range (SD = sensitivity to the partition, not uncertainty);
  K-means - GAE per partition: paired subject bootstrap (23 units, B = 10,000, rng 0) of dF1, dSens, dFP/day;
  across partitions: n_pos (partitions with dF1 > 0) and the bootstrap CI of the across-partition mean (each case's
  difference averaged over partitions) of dF1, dSens, dFP/day, dAUROC, dF1 at the fixed 0.005 point;
  F2 rule: "stable advantage of K-means" iff dF1 > 0 in >= ceil(0.8 P) partitions AND CI low > 0; "stable advantage
  of the GAE" iff dF1 < 0 in >= ceil(0.8 P) AND CI high < 0; otherwise "not stable".
  Secondary, descriptive: km_u - GAE, km_u - km, km - MLP-AE with the same statistics.
  python src/fa16_repl_aggregate.py <dir with the notebook output> [--out results/fa16/repl]
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import f1_aggregate as FA  # noqa: E402

GATES = {"D0": 1, "G-parts": 1, "G-base": 5, "G-kmD": 1, "G-km0": 2, "G-done": 1}
MODELS = ("gae", "mlp", "km", "km_u")
PAIRS = (("km", "gae"), ("km_u", "gae"), ("km_u", "km"), ("km", "mlp"))
NAMES = dict(gae="GAE", mlp="MLP-AE", km="K-means", km_u="K-means (u-CBLOF)")


def stop(msg):
    raise SystemExit(f"STOP {msg}")


def load_record(mc, f1raw):
    T = {}
    for t in ("per_subject", "curves", "auroc"):
        x = pd.read_csv(mc / f"{t}.csv")
        x = x[x.model.isin(("gae", "mlp"))].copy()
        x["partition"] = 0
        parts = [x] + [pd.read_csv(f1raw / f"p{p}" / f"{t}.csv").assign(partition=p) for p in range(1, 6)]
        T[t] = pd.concat(parts, ignore_index=True)
    return T


def reading(per, au, a, b, parts):
    own = per[(per.point == "own") & (per.stage == "localized")]
    fix = per[(per.point == "fixed0.005") & (per.stage == "localized")]

    def delta(tab, met):
        w = tab.pivot_table(index=["partition", "subject"], columns="model", values=met)
        return (w[a] - w[b]).rename(f"d_{met}")
    dF1, dF1x, dS, dFP = delta(own, "f1"), delta(fix, "f1"), delta(own, "sens"), delta(own, "fp_day")
    dAU = au.pivot_table(index=["partition", "subject"], columns="model", values="auroc").pipe(lambda w: w[a] - w[b])
    rows = []
    for p in parts:
        m_, lo, hi, _ = FA.boot_mean(dF1.loc[p])
        s_, slo, shi, _ = FA.boot_mean(dS.loc[p])
        f_, flo, fhi, _ = FA.boot_mean(dFP.loc[p])
        rows.append(dict(model=a, reference=b, partition=p, dF1=m_, dF1_lo=lo, dF1_hi=hi, dSens=s_, dSens_lo=slo,
                         dSens_hi=shi, dFP_day=f_, dFP_lo=flo, dFP_hi=fhi, dAUROC=dAU.loc[p].mean(),
                         wins=int((dF1.loc[p] > 0).sum()), losses=int((dF1.loc[p] < 0).sum())))
    T4 = pd.DataFrame(rows)
    across = {}
    for name, ser in (("dF1", dF1), ("dF1_fixed0005", dF1x), ("dSens", dS), ("dFP_day", dFP), ("dAUROC", dAU)):
        across[name] = FA.boot_mean(ser.groupby(level="subject").mean())[:3]
    need = math.ceil(0.8 * len(parts))
    n_pos, n_neg = int((T4.dF1 > 0).sum()), int((T4.dF1 < 0).sum())
    mean, lo, hi = across["dF1"]
    if n_pos >= need and lo > 0:
        verdict = f"stable advantage of {NAMES[a]}"
    elif n_neg >= need and hi < 0:
        verdict = f"stable advantage of {NAMES[b]}"
    else:
        verdict = "not stable"
    T5 = pd.DataFrame([dict(model=a, reference=b, quantity=k, mean=v[0], lo=v[1], hi=v[2]) for k, v in across.items()])
    V = dict(model=a, reference=b, partitions=parts, n_pos=n_pos, n_neg=n_neg, need=need, dF1_mean=mean, dF1_lo=lo,
             dF1_hi=hi, verdict=verdict)
    return T4, T5, V


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("indir")
    ap.add_argument("--out", default=str(ROOT / "results" / "fa16" / "repl"))
    ap.add_argument("--mc", default=str(ROOT / "results" / "model_cmp"))
    ap.add_argument("--f1", default=str(ROOT / "results" / "f1_repcv"))
    a = ap.parse_args()
    out, mc, f1 = Path(a.out), Path(a.mc), Path(a.f1)
    hits = sorted(Path(a.indir).rglob("fa16_repl/gates.json"))
    if len(hits) != 1:
        stop(f"A0: expected one fa16_repl/gates.json under {a.indir}, found {len(hits)}")
    run = hits[0].parent
    # A0
    gates = json.loads((run / "gates.json").read_text())
    cnt = {}
    for g in gates:
        if g["status"] != "PASS":
            stop(f"A0: gate {g['gate']} {g['status']}")
        cnt[g["gate"]] = cnt.get(g["gate"], 0) + 1
    if any(cnt.get(k, 0) != v for k, v in GATES.items()):
        stop(f"A0: gate counts {cnt} (need {GATES})")
    rk = pd.read_csv(run / "per_subject.csv")
    rk = rk[rk.model.isin(("km", "km_u"))]
    for (m, p), g in rk.groupby(["model", "partition"]):
        if len(g) != 96 or g.subject.nunique() != 24:
            stop(f"A0: {m} partition {p}: {len(g)} rows, {g.subject.nunique()} cases")
    if sorted(set(map(tuple, rk[["model", "partition"]].drop_duplicates().values.tolist()))) != \
            sorted((m, p) for m in ("km", "km_u") for p in range(6)):
        stop("A0: K-means arms do not cover partitions 0-5")
    # A1: the reading code reproduces the committed F2 reading of the MLP-AE
    R = load_record(mc, f1 / "raw")
    per_r = FA.per_case(R["per_subject"])
    _, T5r, Vr = reading(per_r, R["auroc"], "mlp", "gae", list(range(6)))
    ref = pd.read_csv(f1 / "F2_across_partitions.csv").set_index("quantity")
    vref = json.loads((f1 / "VERDICT.json").read_text())
    bad = [(r.quantity, c) for r in T5r.itertuples() for c in ("mean", "lo", "hi")
           if abs(getattr(r, c) - ref.loc[r.quantity, c]) > 1e-12]
    vmap = {"stable advantage of MLP-AE": "stable advantage of the MLP-AE", "stable advantage of GAE":
            "stable advantage of the GAE", "not stable": "not stable"}
    if bad or Vr["n_pos"] != vref["n_pos"] or not vref["verdict"].startswith(vmap[Vr["verdict"]]):
        stop(f"A1: committed F2 reading not reproduced: {bad}, n_pos {Vr['n_pos']} vs {vref['n_pos']}, {Vr['verdict']}")
    print("A0 / A1 PASS")
    # rows
    T = {t: pd.concat([R[t], pd.read_csv(run / f"{t}.csv").query("model in ('km', 'km_u')")], ignore_index=True)
         for t in ("per_subject", "curves", "auroc")}
    per = FA.per_case(T["per_subject"])
    ref0 = per[per.partition == 0].drop_duplicates("subject").set_index("subject")[["n_ref", "nonict_h"]]
    for (p, m), g in per.groupby(["partition", "model"]):
        x = g.drop_duplicates("subject").set_index("subject")[["n_ref", "nonict_h"]].reindex(ref0.index)
        if not ((x.n_ref == ref0.n_ref).all() and (np.abs(x.nonict_h - ref0.nonict_h) < 1e-6).all()):
            stop(f"A0: {m} partition {p}: n_ref / non-seizure hours differ from partition 0")
    own = per[(per.point == "own") & (per.stage == "localized")]
    au = T["auroc"]
    parts = list(range(6))
    T1 = []
    for (p, m), g in own.groupby(["partition", "model"]):
        T1.append(dict(partition=p, model=m, sens=g.sens.mean(), prec=g.prec.mean(), f1=g.f1.mean(),
                       fp_day=g.fp_day.mean(), auroc=au[(au.partition == p) & (au.model == m)].auroc.mean(),
                       seizures_caught=int(g.tp.sum()), n_ref=int(g.n_ref.sum()), false_alarms=int(g.fp.sum())))
    T1 = pd.DataFrame(T1)
    T2 = []
    for m in MODELS:
        x = T1[T1.model == m]
        for met in ("sens", "prec", "f1", "fp_day", "auroc", "seizures_caught", "false_alarms"):
            T2.append(dict(model=m, metric=met, mean=x[met].mean(), sd=x[met].std(ddof=1), min=x[met].min(),
                           max=x[met].max(), n_partitions=len(x)))
    T2 = pd.DataFrame(T2)
    T4s, T5s, Vs = [], [], []
    for a_, b_ in PAIRS:
        t4, t5, v = reading(per, au, a_, b_, parts)
        T4s.append(t4); T5s.append(t5); Vs.append(v)
    T4, T5 = pd.concat(T4s, ignore_index=True), pd.concat(T5s, ignore_index=True)
    out.mkdir(parents=True, exist_ok=True)
    for name, df in (("per_partition", T1), ("across_partitions", T2), ("diff_per_partition", T4),
                     ("diff_across_partitions", T5)):
        df.to_csv(out / f"{name}.csv", index=False)
    (out / "VERDICT.json").write_text(json.dumps(Vs, indent=1, default=float))
    meta = json.loads((run / "run_meta.json").read_text())
    (out / "gates_all.json").write_text(json.dumps(dict(gates=gates, run_meta=meta), indent=1, default=str))
    v = Vs[0]
    L = ["# F-A1.6 replication -- K-means over the six patient partitions (CHB-MIT, 24 cases / 23 subjects)\n",
         f"Run: {meta.get('notebook')} at {str(meta.get('repo_commit'))[:7]}, code sha {meta.get('code_sha')}, "
         f"measured runtime {meta.get('runtime_h')} h. A0 / A1 PASS. Partition 0 = the comparison of the report "
         "(seed 42); 1-5 = the random partitions of the F1 record (seed = partition). Per-case means, own label-free "
         "point, after CPD.\n",
         "## Per partition\n", "```", T1.round(3).to_string(index=False), "```",
         "\n## Across partitions (SD = sensitivity to the partition, not uncertainty)\n", "```",
         T2.round(3).to_string(index=False), "```",
         "\n## Differences per partition (paired subject bootstrap, 23 units)\n", "```", T4.round(3).to_string(index=False),
         "```", "\n## Differences across partitions (each case averaged over partitions; subject bootstrap)\n", "```",
         T5.round(3).to_string(index=False), "```",
         f"\n**F2 rule (primary: K-means - GAE):** dF1 > 0 in {v['n_pos']} / 6 (need {v['need']}); across-partition "
         f"mean dF1 {v['dF1_mean']:+.3f} [{v['dF1_lo']:+.3f}, {v['dF1_hi']:+.3f}] -> **{v['verdict']}**.",
         "Secondary (descriptive): " + "; ".join(f"{NAMES[x['model']]} - {NAMES[x['reference']]}: {x['n_pos']} / 6, "
                                                f"{x['dF1_mean']:+.3f} [{x['dF1_lo']:+.3f}, {x['dF1_hi']:+.3f}], "
                                                f"{x['verdict']}" for x in Vs[1:]) + "\n"]
    (out / "SUMMARY.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
