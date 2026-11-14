#!/usr/bin/env python
"""
fa14_aggregate.py -- reading of F-A1.4 (src/fa14_mech.py outputs). Written and committed before any F-A1.4 output
(docs/FUTURE_RESEARCH_PLAN.md §12 14/11 23:10). Descriptive: no threshold (P2); every statistic per case, then the
per-patient (macro) mean over the 24 cases; patient bootstrap B = 10,000, rng 0, chb01 + chb21 one unit (23 units), the
convention of src/model_cmp_aggregate.boot_diff (statistic = mean over the cases of the resampled units); partitions read
side by side and as the mean over the partitions present (per case first, then the same bootstrap).

Gates (STOP): A0 -- partition 0 rows give the record's totals (1,129 / 827 false alarms at the own point, 920 / 650 at
0.005, localized) unless --allow-test; A1 -- every partition read has `G-base p{r}` PASS in its gates.json, 24 cases per
arm in rows / f3a / desc, the F3-A identity log(FA_a / FA_m) = budget + seizure-share - fragmentation terms holds to
1e-12 on the pooled counts.

Tables (results/fa14/aggregate/):
  counts.csv        per partition, arm, point: summed scorer tp / fp (localized) and per-patient sensitivity, FP/day, F1
  interventions.csv per partition (and mean): share of the GAE's excess false alarms (over the MLP-AE) removed by each
                    arm, pooled = (FP_gae - FP_arm) / (FP_gae - FP_mlp) with its bootstrap CI; per-patient differences
                    arm - gae in FP/day, sensitivity, F1
  f3a.csv           F3-A terms of log(FA_arm / FA_mlp), own and fixed point, localized and detector
  h1.csv            input-focal dR (and minus the other background windows), member differences; mlpfocal, armfocal and
                    the asymmetry mlpfocal - armfocal; every (pair, phi, tau)
  h1nb.csv          neighbour shares: arm-only, mlp-only, not recruited, control, all (chance), and their differences
  h1fa.csv          share of arm-only / mlp-only false-alarm peaks in input-focal windows minus the base rate
  h2.csv, smooth.csv, h3.csv, desc.csv
  SUMMARY.md
  python src/fa14_aggregate.py --runs results/fa14 [--out results/fa14/aggregate] [--allow-test]
  (--runs is searched recursively: results/fa14/P0/p0 and results/fa14/REPL/p1 ... p5 = the two notebooks' outputs)
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

B, RNG = 10_000, 0
P0_TOTALS = {("gae", "own"): 1129, ("mlp", "own"): 827, ("gae", "fixed0.005"): 920, ("mlp", "fixed0.005"): 650}
ARMS = ("gae", "mlp", "ifix", "iself")
PAIRS = (("gae", "mlp"), ("ifix", "mlp"), ("iself", "mlp"))


def unit(s):
    return "chb01+chb21" if s in ("chb01", "chb21") else s


class Boot:
    """resampling of the 23 units; statistics are means (or ratios of sums) over the cases of the resampled units."""

    def __init__(self, cases, b=B, seed=RNG):
        self.cases = sorted(cases)
        units = sorted({unit(s) for s in self.cases})
        self.U = np.array([[i for i, s in enumerate(self.cases) if unit(s) == u] for u in units], dtype=object)
        rng = np.random.default_rng(seed)
        self.pick = rng.integers(0, len(units), size=(b, len(units)))
        # weight matrix: how many times each case is drawn in each replicate
        W = np.zeros((b, len(self.cases)))
        for ui, members in enumerate(self.U):
            cnt = (self.pick == ui).sum(1)
            for i in members:
                W[:, i] += cnt
        self.W = W

    def mean(self, v):
        """v: per-case values (Series indexed by case or array in self.cases order); NaN cases dropped."""
        v = self._vec(v)
        ok = np.isfinite(v)
        if not ok.any():
            return dict(est=np.nan, lo=np.nan, hi=np.nan, n=0)
        Wk = self.W[:, ok]
        den = Wk.sum(1)
        st = np.where(den > 0, (Wk * v[ok]).sum(1) / np.maximum(den, 1e-12), np.nan)
        return dict(est=float(v[ok].mean()), lo=float(np.nanpercentile(st, 2.5)), hi=float(np.nanpercentile(st, 97.5)),
                    n=int(ok.sum()))

    def ratio(self, num, den):
        """sum(num) / sum(den) over the resampled cases."""
        n, d = self._vec(num), self._vec(den)
        ok = np.isfinite(n) & np.isfinite(d)
        sn, sd = (self.W[:, ok] * n[ok]).sum(1), (self.W[:, ok] * d[ok]).sum(1)
        st = np.where(sd != 0, sn / np.where(sd != 0, sd, 1), np.nan)
        est = n[ok].sum() / d[ok].sum() if d[ok].sum() != 0 else np.nan
        return dict(est=float(est), lo=float(np.nanpercentile(st, 2.5)), hi=float(np.nanpercentile(st, 97.5)),
                    n=int(ok.sum()))

    def _vec(self, v):
        if isinstance(v, pd.Series):
            return v.reindex(self.cases).to_numpy(dtype=float)
        return np.asarray(v, dtype=float)


def per_case(d):
    d = d.copy()
    d["sens"] = d.tp / d.n_ref
    d["f1"] = 2 * d.tp / (2 * d.tp + d.fp + (d.n_ref - d.tp))
    d["fp_day"] = d.fp / d.nonict_h * 24
    return d


def load(runs):
    P = {}
    for pdir in sorted(Path(runs).rglob("p[0-9]*")):
        if not pdir.is_dir() or not (pdir / "rows.csv").exists() or {"jobs", "aggregate"} & set(pdir.parts):
            continue
        p = int(pdir.name[1:])
        if p in P:
            raise SystemExit(f"STOP A1: partition {p} found twice under {runs}")
        P[p] = {t: pd.read_csv(pdir / f"{t}.csv") for t in ("rows", "seiz", "f3a", "h1", "h1nb", "h1fa", "h2", "smooth",
                                                           "h3", "desc") if (pdir / f"{t}.csv").exists()}
    gates = []
    for g in sorted(Path(runs).rglob("gates.json")):
        if "aggregate" not in g.parts:
            gates += json.loads(g.read_text())
    return P, gates


def check(P, gates, allow_test):
    passed = {g["gate"] for g in gates if g.get("status") == "PASS"}
    bad = []
    for p, T in P.items():
        if f"G-base p{p}" not in passed:
            bad.append(f"p{p}: G-base not PASS")
        for t in ("rows", "f3a", "desc", "h1", "h2"):
            if t not in T:
                bad.append(f"p{p}: {t}.csv missing")
        if "rows" in T:
            r = T["rows"]
            for a in ARMS:
                n = r[(r.arm == a) & (r.point == "own") & (r.stage == "localized")].subject.nunique()
                if n != 24:
                    bad.append(f"p{p}: {a} has {n} of 24 cases")
        if "desc" in T and T["desc"].subject.nunique() != 24:
            bad.append(f"p{p}: desc has {T['desc'].subject.nunique()} cases")
    if bad:
        raise SystemExit(f"STOP A1: {bad}")
    if 0 in P and not allow_test:
        r = P[0]["rows"]
        for (a, pt), want in P0_TOTALS.items():
            got = int(r[(r.arm == a) & (r.point == pt) & (r.stage == "localized")].fp.sum())
            if got != want:
                raise SystemExit(f"STOP A0: partition 0 {a} {pt}: {got} false alarms, record {want}")


def f3a_terms(g, a, m):
    """pooled F3-A terms of log(FA_a / FA_m) from per-case counts (rows of one point / stage)."""
    A, M = g[g.arm == a], g[g.arm == m]
    Ta, Tm, Fa, Fm = A.t_ev.sum(), M.t_ev.sum(), A.t_fa.sum(), M.t_fa.sum()
    na, nm = A.n_fa.sum(), M.n_fa.sum()
    lhs = np.log(na / nm)
    budget = np.log(Ta / Tm)
    share = np.log((Fa / Ta) / (Fm / Tm))                # log((1 - s_a) / (1 - s_m))
    frag = np.log((Fa / na) / (Fm / nm))                 # log(L_a / L_m)
    return dict(log_ratio=lhs, budget=budget, seizure_share=share, fragmentation=-frag,
                identity_error=abs(lhs - (budget + share - frag)), n_fa_arm=int(na), n_fa_ref=int(nm),
                T_arm_h=Ta / 3600, T_ref_h=Tm / 3600, s_arm=1 - Fa / Ta, s_ref=1 - Fm / Tm, L_arm_s=Fa / na,
                L_ref_s=Fm / nm)


def boot_f3a(bt, g, a, m):
    """bootstrap of the F3-A terms (ratio of resampled sums)."""
    keys = ("t_ev", "t_fa", "n_fa")
    va = {k: g[g.arm == a].set_index("subject")[k] for k in keys}
    vm = {k: g[g.arm == m].set_index("subject")[k] for k in keys}
    W = bt.W
    S = {}
    for side, v in (("a", va), ("m", vm)):
        for k in keys:
            S[side + k] = W @ v[k].reindex(bt.cases).to_numpy(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        terms = dict(log_ratio=np.log(S["an_fa"] / S["mn_fa"]), budget=np.log(S["at_ev"] / S["mt_ev"]),
                     seizure_share=np.log((S["at_fa"] / S["at_ev"]) / (S["mt_fa"] / S["mt_ev"])),
                     fragmentation=-np.log((S["at_fa"] / S["an_fa"]) / (S["mt_fa"] / S["mn_fa"])))
    return {f"{k}_lo": float(np.nanpercentile(v, 2.5)) for k, v in terms.items()} | \
        {f"{k}_hi": float(np.nanpercentile(v, 97.5)) for k, v in terms.items()}


def row(label, r):
    return dict(label, est=r["est"], lo=r["lo"], hi=r["hi"], n=r["n"])


def analyse(P):
    cases = sorted(P[min(P)]["rows"].subject.unique())
    bt = Boot(cases)
    parts = sorted(P)
    out = {k: [] for k in ("counts", "interventions", "f3a", "h1", "h1nb", "h1fa", "h2", "smooth", "h3", "desc")}

    def both(table, key, fn):
        """fn(T) -> per-case Series for each partition; one row per partition + the mean over partitions."""
        per = {}
        for p in parts:
            s = fn(P[p])
            if s is None:
                continue
            per[p] = s
            out[table].append(row(dict(key, partition=str(p)), bt.mean(s)))
        if len(per) > 1:
            m = pd.concat(per.values(), axis=1).mean(axis=1, skipna=False)
            out[table].append(row(dict(key, partition="mean"), bt.mean(m)))

    # counts and interventions
    for p in parts:
        r = per_case(P[p]["rows"])
        loc = r[r.stage == "localized"]
        for (a, pt), g in loc.groupby(["arm", "point"]):
            out["counts"].append(dict(partition=str(p), arm=a, point=pt, tp=int(g.tp.sum()), fp=int(g.fp.sum()),
                                      n_ref=int(g.n_ref.sum()), sens=g.sens.mean(), fp_day=g.fp_day.mean(),
                                      f1=g.f1.mean()))
    for pt in ("own", "fixed0.005"):
        for a in ("ifix", "iself"):
            num, den = {}, {}
            for p in parts:
                loc = P[p]["rows"][(P[p]["rows"].stage == "localized") & (P[p]["rows"].point == pt)]
                fp = loc.pivot_table(index="subject", columns="arm", values="fp")
                num[p], den[p] = fp["gae"] - fp[a], fp["gae"] - fp["mlp"]
                out["interventions"].append(row(dict(partition=str(p), point=pt, arm=a, stat="share_of_excess_removed"),
                                                bt.ratio(num[p], den[p])))
            if len(parts) > 1:
                out["interventions"].append(row(dict(partition="sum", point=pt, arm=a, stat="share_of_excess_removed"),
                                                bt.ratio(sum(num.values()), sum(den.values()))))
            for metric in ("fp_day", "sens", "f1"):
                def fn(T, metric=metric, a=a, pt=pt):
                    loc = per_case(T["rows"])
                    loc = loc[(loc.stage == "localized") & (loc.point == pt)].pivot_table(index="subject", columns="arm",
                                                                                         values=metric)
                    return loc[a] - loc["gae"]
                both("interventions", dict(point=pt, arm=a, stat=f"d_{metric}_vs_gae"), fn)
        def fn_ref(T, pt=pt):
            loc = per_case(T["rows"])
            loc = loc[(loc.stage == "localized") & (loc.point == pt)].pivot_table(index="subject", columns="arm",
                                                                                 values="fp_day")
            return loc["mlp"] - loc["gae"]
        both("interventions", dict(point=pt, arm="mlp", stat="d_fp_day_vs_gae"), fn_ref)
    # F3-A
    for p in parts:
        f = P[p]["f3a"]
        for (pt, st), g in f.groupby(["point", "stage"]):
            for a, m in PAIRS + (("gae", "ifix"), ("gae", "iself")):
                t = f3a_terms(g, a, m)
                out["f3a"].append(dict(partition=str(p), point=pt, stage=st, arm=a, ref=m, **t, **boot_f3a(bt, g, a, m)))
    # H1
    for arm, ref in PAIRS:
        for phi in sorted(P[parts[0]]["h1"].phi.unique()):
            for tau in sorted(P[parts[0]]["h1"].tau.unique()):
                k = dict(arm=arm, ref=ref, phi=phi, tau=tau)
                sel = lambda T, d: T["h1"][(T["h1"].arm == arm) & (T["h1"].phi == phi) & (T["h1"].tau == tau)  # noqa
                                           & (T["h1"].definition == d)].set_index("subject")
                both("h1", dict(k, stat="input_dR"), lambda T: sel(T, "input").dR.where(sel(T, "input").n > 0))
                both("h1", dict(k, stat="input_dR_minus_other"),
                     lambda T: (sel(T, "input").dR - sel(T, "input").dR_other).where(sel(T, "input").n > 0))
                for mk in (6, 9, 12):
                    both("h1", dict(k, stat=f"input_dm{mk}"),
                         lambda T, mk=mk: sel(T, "input")[f"dm{mk}"].where(sel(T, "input").n > 0))
                both("h1", dict(k, stat="mlpfocal_dR"), lambda T: sel(T, "mlpfocal").dR.where(sel(T, "mlpfocal").n > 0))
                both("h1", dict(k, stat="armfocal_dR_swap"),
                     lambda T: sel(T, "armfocal").dR.where(sel(T, "armfocal").n > 0))
                both("h1", dict(k, stat="asymmetry"),
                     lambda T: (sel(T, "mlpfocal").dR.where(sel(T, "mlpfocal").n > 0)
                                - sel(T, "armfocal").dR.where(sel(T, "armfocal").n > 0)))
                # neighbours
                def nbshare(T, cat, col="nb"):
                    d = T["h1nb"]
                    d = d[(d.arm == arm) & (d.phi == phi) & (d.tau == tau)].set_index("subject")
                    if not len(d):
                        return None
                    return (d[f"{col}_{cat}"] / d[f"n_{cat}"]).where(d[f"n_{cat}"] > 0)
                if arm != "iself":
                    for cat in ("armonly", "mlponly", "notrec", "ctl", "all"):
                        both("h1nb", dict(k, stat=f"share_nb_{cat}"), lambda T, cat=cat: nbshare(T, cat))
                    both("h1nb", dict(k, stat="armonly_minus_all"),
                         lambda T: nbshare(T, "armonly") - nbshare(T, "all"))
                    both("h1nb", dict(k, stat="armonly_minus_mlponly"),
                         lambda T: nbshare(T, "armonly") - nbshare(T, "mlponly"))
                    both("h1nb", dict(k, stat="armonly_minus_notrec"),
                         lambda T: nbshare(T, "armonly") - nbshare(T, "notrec"))
                    both("h1nb", dict(k, stat="armonly_minus_ctl"),
                         lambda T: nbshare(T, "armonly") - nbshare(T, "ctl"))
                both("h1nb", dict(k, stat="window_graph_armonly_minus_all"),
                     lambda T: nbshare(T, "armonly", "nbw") - nbshare(T, "all", "nbw"))
            # false-alarm peaks
            def fa(T, which):
                d = T["h1fa"]
                d = d[(d.arm == arm) & (d.phi == phi)].set_index("subject")
                base = d.focal_nonict / d.n_nonict
                return (d[f"focal_{which}"] / d[f"n_{which}"]).where(d[f"n_{which}"] > 0) - base
            both("h1fa", dict(arm=arm, ref=ref, phi=phi, stat="armonly_focal_minus_base"), lambda T: fa(T, "armonly"))
            both("h1fa", dict(arm=arm, ref=ref, phi=phi, stat="refonly_focal_minus_base"), lambda T: fa(T, "refonly"))
            both("h1fa", dict(arm=arm, ref=ref, phi=phi, stat="asymmetry"),
                 lambda T: fa(T, "armonly") - fa(T, "refonly"))
        # H2
        for stat in ("slope_J", "slope_ddeg_sd", "flip_effect", "mean_delta"):
            both("h2", dict(arm=arm, ref=ref, stat=stat),
                 lambda T, stat=stat: T["h2"][T["h2"].arm == arm].set_index("subject")[stat])
        # H3
        def h3(T, col):
            d = T["h3"]
            a = d[d.arm == arm].set_index(["subject", "file", "onset_s"])[col]
            m = d[d.arm == ref].set_index(["subject", "file", "onset_s"])[col]
            return (a - m).groupby(level=0).mean()
        both("h3", dict(arm=arm, ref=ref, stat="d_peak"), lambda T: h3(T, "peak"))
        both("h3", dict(arm=arm, ref=ref, stat="d_p_need"), lambda T: h3(T, "p_need"))
        both("smooth", dict(arm=arm, ref=ref, stat="d_lag1"),
             lambda T: T["smooth"][T["smooth"].arm == arm].set_index("subject").lag1
             - T["smooth"][T["smooth"].arm == ref].set_index("subject").lag1)
    for col in ("neighbour_share", "isolated_share", "mean_jaccard", "fixed_neighbour_share", "window_edges",
                "fixed_edges"):
        both("desc", dict(stat=col), lambda T, col=col: T["desc"].set_index("subject")[col])
    return {k: pd.DataFrame(v) for k, v in out.items()}


def summary(R, parts):
    def g(df, **kw):
        d = df
        for k, v in kw.items():
            d = d[d[k] == v]
        return d
    L = ["# F-A1.4 reading (fa14_aggregate.py)", "", f"Partitions: {parts}. Per-patient means over 24 cases, patient "
         "bootstrap 95 % CI (23 units, B = 10,000). Descriptive (no threshold).", "",
         "## Counts (localized)", "", "| partition | arm | point | tp | fp | sens | FP/day | F1 |", "|---|---|---|---|---|---|---|---|"]
    for r in R["counts"].itertuples():
        L.append(f"| {r.partition} | {r.arm} | {r.point} | {r.tp} | {r.fp} | {r.sens:.3f} | {r.fp_day:.1f} | {r.f1:.3f} |")
    L += ["", "## Share of the GAE's excess false alarms removed by the interventions", "",
          "| partition | point | arm | share [CI] |", "|---|---|---|---|"]
    for r in g(R["interventions"], stat="share_of_excess_removed").itertuples():
        L.append(f"| {r.partition} | {r.point} | {r.arm} | {r.est:.2f} [{r.lo:.2f}, {r.hi:.2f}] |")
    L += ["", "## F3-A (localized), log(FA_arm / FA_ref) = budget + seizure share + fragmentation", "",
          "| partition | point | arm / ref | log ratio | budget | seizure share | fragmentation |", "|---|---|---|---|---|---|---|"]
    for r in g(R["f3a"], stage="localized").itertuples():
        L.append(f"| {r.partition} | {r.point} | {r.arm} / {r.ref} | {r.log_ratio:+.3f} | {r.budget:+.3f} "
                 f"[{r.budget_lo:+.3f}, {r.budget_hi:+.3f}] | {r.seizure_share:+.3f} [{r.seizure_share_lo:+.3f}, "
                 f"{r.seizure_share_hi:+.3f}] | {r.fragmentation:+.3f} [{r.fragmentation_lo:+.3f}, "
                 f"{r.fragmentation_hi:+.3f}] |")
    for name, tab in (("H1 (phi 4, tau 2)", g(R["h1"], phi=4.0, tau=2.0)), ("H1 neighbours (phi 4, tau 2)",
                      g(R["h1nb"], phi=4.0, tau=2.0)) if len(R["h1nb"]) else ("H1 neighbours", R["h1nb"]),
                      ("H1 false-alarm peaks (phi 4)", g(R["h1fa"], phi=4.0)) if len(R["h1fa"]) else ("H1fa", R["h1fa"]),
                      ("H2", R["h2"]), ("H3", R["h3"]), ("Smoothness", R["smooth"]), ("Descriptive", R["desc"])):
        L += ["", f"## {name}", "", "| partition | arm | stat | est [CI] | n |", "|---|---|---|---|---|"]
        for r in tab.itertuples():
            L.append(f"| {r.partition} | {getattr(r, 'arm', '')} | {r.stat} | {r.est:+.4f} [{r.lo:+.4f}, {r.hi:+.4f}] | "
                     f"{r.n} |")
    L += ["", "The full grid (phi 3 / 4 / 5 x tau 1.5 / 2 / 3) is in h1.csv, h1nb.csv, h1fa.csv."]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/fa14")
    ap.add_argument("--out", default=None)
    ap.add_argument("--allow-test", action="store_true")
    a = ap.parse_args()
    out = Path(a.out or Path(a.runs) / "aggregate")
    P, gates = load(a.runs)
    if not P:
        raise SystemExit(f"STOP A1: no partition output under {a.runs}")
    check(P, gates, a.allow_test)
    R = analyse(P)
    bad = R["f3a"][R["f3a"].identity_error > 1e-12]
    if len(bad):
        raise SystemExit(f"STOP A1: F3-A identity error {bad.identity_error.max()}")
    out.mkdir(parents=True, exist_ok=True)
    for k, v in R.items():
        v.to_csv(out / f"{k}.csv", index=False)
    (out / "SUMMARY.md").write_text(summary(R, sorted(P)))
    (out / "gates.json").write_text(json.dumps([dict(gate="A0", status="PASS" if 0 in P else "n/a",
                                                     allow_test=a.allow_test),
                                                dict(gate="A1", status="PASS", partitions=sorted(P))], indent=1))
    print(f"aggregate: partitions {sorted(P)}; A0 / A1 PASS; tables in {out}")


if __name__ == "__main__":
    main()
