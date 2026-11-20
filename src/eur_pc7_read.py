#!/usr/bin/env python
"""eur_pc7_read.py -- reading of PC7, the seed variance of the training recipe (Track F, chat D34-F, 21/11/2026; design
results/eureka_d34f/DESIGN_PC7.md, approved 01:26). Written and committed before any PC7 output. Container / laptop only.

Inputs: the two committed run folders of EUR_PC7_A / EUR_PC7_B, the PC1 control run (results/eureka_d32f/pc1_r0) and
the merged PC1 folder (results/eureka_d32f/pc1, for the arms 10a / 10b of Q5).
Gates (STOP):
  M-gates  every gate of each run PASS (G-pc7plat / G-pc7rep are recorded checks: PASS or DIFF, no stop); the required
           gates present
  M0       V0 rows (per_subject, errors, curve) identical in every run and in pc1_r0 (sorted row sets)
  M1       the reused seeds' R0 and R0s rows identical in the two runs (and R0 = pc1_r0: gate G-pc7r0 of each run)
  M2       every case has V0 x 4 seeds, and R0 / R0s x every seed the run trained or reused, x 2 budgets x 3 stages
Pooling rule (design §3): G-pc7plat and G-pc7rep PASS in both runs -> the primary reading pools every R0 seed;
otherwise it uses the newly trained seeds only and shows PC1's four beside them.
Readings (design §4; per-patient means, own label-free point, after the localizer; development primary):
  Q1 seed table, summary over seeds (mean, SD with chi-square 95 % interval, min, quartiles, max), variance components
     (two-way ANOVA without replication, patient x seed, method of moments)
  Q2 Spearman rho(validation loss, development metric) with a seed bootstrap (B = 10,000); selection gain over every
     subset of 4 seeds (seed bootstrap B = 2,000); training loss the same way; wording rule of the design
  Q3 minimal detectable difference: empirical (random disjoint seed groups of n x patient bootstrap, 2,000 draws) and
     from the variance components (n = 4, 8, 12, 20)
  Q4 V5's 4-seed mean against every 4-seed mean of R0 (percentile)
  Q5 PC1 arms 10a / 10b - R0 with a two-level bootstrap (patient units; seeds within each arm), B = 10,000
  Q6 R0s (k per seed) against R0 (k of seed 42), per seed
Outputs (--out): per_subject.csv, errors.csv, k.csv (merged), seeds.csv, q1_summary.csv, q1_components.csv, q2.csv,
q3.csv, q4.csv, q5.csv, q6.csv, gates.json, T_PC7.md.
  python src/eur_pc7_read.py --runs results/eureka_d34f/pc7_A results/eureka_d34f/pc7_B \
      --ref results/eureka_d32f/pc1_r0 --pc1 results/eureka_d32f/pc1 --out results/eureka_d34f/pc7
"""
import argparse
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

UNIT = {"chb21": "chb01"}                    # chb21 = chb01 recorded 1.5 years later: one resampling unit
SETS = ["development", "test", "chb24", "siena"]
METRICS = ("sens", "f1", "fa")
FILES = ("per_subject.csv", "errors.csv", "curve.csv")
INFO_GATES = {"G-pc7plat", "G-pc7rep"}
REQUIRED = ["G-self", "G-data", "G-pc1const", "G-pc1vec", "G-pc7reuse", "G-pc7plat", "G-pc7rep", "G-guard", "SMOKE",
            "R1.0-dev", "R1.0-test", "GE", "G-k", "G-kv0", "G-D0[full]", "G-x0[full]", "G-eng[full]", "G-worker[full]",
            "G-pc7k", "G-pc7r0"]
B_RHO, B_GAIN, B_Q3, B_Q5, RNG_SEED = 10_000, 2_000, 2_000, 10_000, 0
TAGS4 = ["clean_seed42", "clean_seed1", "clean_seed2", "clean_seed3"]


def canon(d):
    return d.sort_values(list(d.columns), kind="mergesort").reset_index(drop=True)


def set_names(d):
    d = d.copy()
    d["set"] = np.where(d["set"] != "external", d["set"], np.where(d.subject == "chb24", "chb24", "siena"))
    return d


def seed_num(t):
    return int(str(t).split("seed")[-1])


# ============================================================================ loading and gates
def load(run):
    run = Path(run)
    out = {f: pd.read_csv(run / f) for f in FILES if (run / f).exists()}
    out["gates"] = json.loads((run / "gates.json").read_text())
    out["k"] = pd.read_csv(run / "k.csv")
    out["meta"] = json.loads((run / "run_meta.json").read_text())
    out["train"] = {}
    md = run / "models" / "R0"
    if md.exists():
        for js in sorted(md.glob("gae_v2_clean_seed*.json")):
            if js.name.endswith("_DONE.json"):
                continue
            m = json.loads(js.read_text())
            out["train"][js.stem.replace("gae_v2_", "")] = dict(val_loss=m.get("final_val"), train_loss=m.get("last_loss"),
                                                               first_loss=m.get("first_loss"), epochs=m.get("epochs"))
    return out


def gate_runs(runs):
    bad, info = {}, {}
    for name, r in runs.items():
        g = {x["gate"]: x for x in r["gates"]}
        b = [k for k, x in g.items() if k not in INFO_GATES and x.get("status") != "PASS"]
        b += [f"missing {k}" for k in REQUIRED if k not in g]
        b += [f"{k} {g[k].get('status')}" for k in INFO_GATES if k in g and g[k].get("status") not in ("PASS", "DIFF")]
        if b:
            bad[name] = b
        info[name] = {k: g.get(k, {}).get("status") for k in INFO_GATES} | {"skipped": g.get("G-guard", {}).get("skipped")}
    return bad, info


def m0(runs, ref):
    for f in FILES:
        base = canon(ref[f][ref[f].variant == "V0"]) if f in ref else None
        for name, r in runs.items():
            if f not in r:
                continue
            cur = canon(r[f][r[f].variant == "V0"])
            if base is None:
                base = cur
            elif not cur.equals(base[list(cur.columns)]):
                raise SystemExit(f"STOP M0: {name}: V0 rows of {f} differ")


def m1(runs, reused):
    names = list(runs)
    for f in ("per_subject.csv", "errors.csv"):
        ref_rows = None
        for n in names:
            d = runs[n][f]
            cur = canon(d[d.variant.isin(["R0", "R0s"]) & d.seed.isin(reused)])
            if ref_rows is None:
                ref_rows = cur
            elif not cur.equals(ref_rows):
                raise SystemExit(f"STOP M1: {n}: the reused seeds' R0 / R0s rows of {f} differ between the runs")


def m2(R, seeds_by_variant):
    bad = []
    for (s, v), g in R.groupby(["subject", "variant"]):
        want = set(seeds_by_variant.get(v, []))
        got = g.groupby("seed").size()
        if set(got.index) != want or (got != 6).any():
            bad.append(f"{s}/{v}: seeds {sorted(set(got.index) ^ want)} counts {sorted(set(got.values))}")
    if bad:
        raise SystemExit(f"STOP M2: incomplete rows {bad[:10]}")


# ============================================================================ metrics
def per_patient_seed(R):
    d = R[(R.budget == "own") & (R.stage == "cpd")].copy()
    d["sens"] = d.tp / d.n_ref.where(d.n_ref > 0)
    d["f1"] = 2 * d.tp / (2 * d.tp + d.fp + (d.n_ref - d.tp))
    d["fa"] = d.fp / d.nonict_h * 24
    return d[["set", "variant", "seed", "subject", "sens", "f1", "fa"]]


def seed_values(P):
    return P.groupby(["set", "variant", "seed"])[list(METRICS)].mean().reset_index()


def matrix(P, st, v, met, seeds):
    g = P[(P.set == st) & (P.variant == v) & (P.seed.isin(seeds))].pivot(index="subject", columns="seed", values=met)
    g = g[[s for s in seeds if s in g.columns]]
    return g.dropna(axis=0, how="any")


def sd_ci(x):
    x = np.asarray(x, float)
    n = len(x)
    s = x.std(ddof=1)
    lo = np.sqrt((n - 1) * s ** 2 / stats.chi2.ppf(0.975, n - 1))
    hi = np.sqrt((n - 1) * s ** 2 / stats.chi2.ppf(0.025, n - 1))
    return s, lo, hi


def anova2(Y):
    """two-way ANOVA without replication on Y (patients x seeds); method-of-moments variance components."""
    Y = np.asarray(Y, float)
    P, S = Y.shape
    gm = Y.mean()
    rp, cs = Y.mean(axis=1), Y.mean(axis=0)
    ms_seed = P * ((cs - gm) ** 2).sum() / (S - 1)
    ms_pat = S * ((rp - gm) ** 2).sum() / (P - 1)
    res = Y - rp[:, None] - cs[None, :] + gm
    ms_res = (res ** 2).sum() / ((P - 1) * (S - 1))
    v_seed = max(0.0, (ms_seed - ms_res) / P)
    v_pat = max(0.0, (ms_pat - ms_res) / S)
    return dict(patients=P, seeds=S, ms_seed=ms_seed, ms_pat=ms_pat, ms_res=ms_res, var_seed=v_seed, var_patient=v_pat,
                var_res=ms_res, seed_share_nonpatient=v_seed / (v_seed + ms_res) if (v_seed + ms_res) > 0 else np.nan,
                sd_seed=np.sqrt(v_seed), sd_res=np.sqrt(ms_res))


def unit_draw(subjects, rng, B):
    """patient-unit bootstrap index matrix: returns (unit index of each subject, B x U resampled units)."""
    units = pd.Series([UNIT.get(x, x) for x in subjects])
    uids = list(dict.fromkeys(units))
    uix = np.array([uids.index(u) for u in units])
    return uix, rng.integers(0, len(uids), size=(B, len(uids))), len(uids)


def unit_mean(d, uix, draws, U):
    """mean over the subjects of the resampled units (sum of the units' subject values / number of subjects)."""
    sums = np.bincount(uix, weights=d, minlength=U)
    ns = np.bincount(uix, minlength=U).astype(float)
    return sums[draws].sum(axis=-1) / ns[draws].sum(axis=-1)


def spearman_boot(val, y, rng, B):
    val, y = np.asarray(val, float), np.asarray(y, float)
    rho = stats.spearmanr(val, y).statistic
    n = len(val)
    bs = np.empty(B)
    for b in range(B):
        i = rng.integers(0, n, n)
        bs[b] = stats.spearmanr(val[i], y[i]).statistic if np.unique(val[i]).size > 2 else np.nan
    return float(rho), float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))


def selection_gain(val, y, combos):
    """over every subset (rows of `combos`, positions into val / y): y of the lowest-val seed minus the subset mean;
    returns the mean gain and the share of subsets where the chosen seed is at or above the subset median."""
    V, Yc = val[combos], y[combos]
    pick = Yc[np.arange(len(combos)), V.argmin(axis=1)]
    gain = pick - Yc.mean(axis=1)
    return float(gain.mean()), float((pick >= np.median(Yc, axis=1)).mean())


def gain_boot(val, y, rng, B, k=4):
    n = len(val)
    combos = np.array(list(itertools.combinations(range(n), k)))
    g, share = selection_gain(val, y, combos)
    bs = np.empty(B)
    for b in range(B):
        i = rng.integers(0, n, n)
        bs[b] = selection_gain(val[i], y[i], combos)[0]
    return g, share, float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


# ============================================================================ readings
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--pc1", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RNG_SEED)
    runs = {Path(r).name: load(r) for r in a.runs}
    ref = load(a.ref)
    bad, info = gate_runs(runs)
    if bad:
        raise SystemExit(f"STOP M-gates: {bad}")
    reused = sorted({t for r in runs.values() for t in r["meta"].get("arm_reuse", [])}, key=seed_num)
    m0(runs, ref)
    m1(runs, reused)
    names = list(runs)
    # merge: V0 once; reused seeds once (first run); every run's own trained seeds
    trained = {n: [t for t in runs[n]["meta"]["arm_seeds"] if t not in reused] for n in names}
    parts = {f: [] for f in ("per_subject.csv", "errors.csv")}
    for i, n in enumerate(names):
        for f in parts:
            d = runs[n][f]
            keep = (d.variant.isin(["R0", "R0s"]) & d.seed.isin(trained[n])) | \
                   ((d.variant.isin(["R0", "R0s"]) | (d.variant == "V0")) & (i == 0) & ~d.seed.isin(sum(trained.values(), [])))
            parts[f].append(d[keep])
    R = pd.concat(parts["per_subject.csv"], ignore_index=True)
    E = pd.concat(parts["errors.csv"], ignore_index=True)
    R.to_csv(out / "per_subject.csv", index=False)
    E.to_csv(out / "errors.csv", index=False)
    present = {n: sorted(set(runs[n]["per_subject.csv"].query("variant == 'R0'").seed) - set(reused), key=seed_num)
               for n in names}
    all_seeds = reused + sum(present.values(), [])
    m2(R, {"V0": TAGS4, "R0": all_seeds, "R0s": all_seeds})
    ks = pd.concat([runs[n]["k"].assign(run=n) for n in names], ignore_index=True)
    ks.to_csv(out / "k.csv", index=False)
    pooled = all(info[n]["G-pc7plat"] == "PASS" and info[n]["G-pc7rep"] == "PASS" for n in names)
    primary = all_seeds if pooled else sum(present.values(), [])
    print(f"M-gates / M0 / M1 / M2 PASS; seeds: reused {reused}, trained {present}; pooled {pooled} -> primary N = {len(primary)}")
    R = set_names(R)
    P = per_patient_seed(R)
    SV = seed_values(P)

    # training losses
    tr = {}
    for n in names:
        tr.update(runs[n]["train"])
    for t in reused:
        tr[t] = ref["train"].get(t, tr.get(t))
    seeds_tab = []
    for t in all_seeds:
        r = dict(seed=t, origin="PC1 (reused)" if t in reused else next(n for n in names if t in present[n]),
                 in_primary=t in primary, **{k: tr.get(t, {}).get(k) for k in ("val_loss", "train_loss", "first_loss", "epochs")})
        for st in SETS:
            for v in ("R0", "R0s"):
                row = SV[(SV.set == st) & (SV.variant == v) & (SV.seed == t)]
                for met in METRICS:
                    r[f"{st}_{v}_{met}"] = float(row[met].iloc[0]) if len(row) else np.nan
        seeds_tab.append(r)
    ST = pd.DataFrame(seeds_tab)
    ST.to_csv(out / "seeds.csv", index=False)

    # Q1
    q1 = []
    for st in SETS:
        for v in ("R0", "R0s", "V0"):
            seeds = primary if v != "V0" else TAGS4
            for met in METRICS:
                x = SV[(SV.set == st) & (SV.variant == v) & SV.seed.isin(seeds)][met].dropna().values
                if len(x) < 2:
                    continue
                s, lo, hi = sd_ci(x)
                q1.append(dict(set=st, variant=v, metric=met, n_seeds=len(x), mean=x.mean(), sd=s, sd_lo=lo, sd_hi=hi,
                               min=x.min(), q25=np.percentile(x, 25), median=np.median(x), q75=np.percentile(x, 75),
                               max=x.max()))
    Q1 = pd.DataFrame(q1)
    Q1.to_csv(out / "q1_summary.csv", index=False)
    comp = []
    for st in ("development", "test", "siena"):
        for met in METRICS:
            Y = matrix(P, st, "R0", met, primary)
            if Y.shape[0] >= 2 and Y.shape[1] >= 2:
                comp.append(dict(set=st, metric=met, **anova2(Y.values)))
    QC = pd.DataFrame(comp)
    QC.to_csv(out / "q1_components.csv", index=False)

    # Q2
    q2 = []
    vt = ST[ST.seed.isin(primary)].set_index("seed").loc[primary]
    for crit in ("val_loss", "train_loss"):
        for st in SETS:
            for met in ("sens", "f1"):
                y = vt[f"{st}_R0_{met}"].values.astype(float)
                c = vt[crit].values.astype(float)
                if np.isnan(c).any() or np.isnan(y).any() or len(y) < 5:
                    continue
                rho, rlo, rhi = spearman_boot(c, y, rng, B_RHO)
                g, share, glo, ghi = gain_boot(c, y, rng, B_GAIN)
                picks = bool(rho < 0 and rhi < 0 and glo > 0)
                q2.append(dict(criterion=crit, set=st, metric=met, n_seeds=len(y), rho=rho, rho_lo=rlo, rho_hi=rhi,
                               gain_mean=g, gain_lo=glo, gain_hi=ghi, share_at_or_above_median=share,
                               reading="primary" if (st == "development" and crit == "val_loss") else "secondary",
                               wording="picks the better detector" if picks else "no evidence that it picks the better detector"))
    Q2 = pd.DataFrame(q2)
    Q2.to_csv(out / "q2.csv", index=False)

    # Q3
    q3 = []
    for met in METRICS:
        Y = matrix(P, "development", "R0", met, primary)
        if Y.shape[1] < 2:
            continue
        subj = list(Y.index)
        uix, draws, U = unit_draw(subj, rng, B_Q3)
        A = Y.values
        S = A.shape[1]
        comps = QC[(QC.set == "development") & (QC.metric == met)]
        for n in (4, 8, 10):
            if 2 * n > S:
                continue
            nul = np.empty(B_Q3)
            for b in range(B_Q3):
                perm = rng.permutation(S)
                d = A[:, perm[:n]].mean(axis=1) - A[:, perm[n:2 * n]].mean(axis=1)
                nul[b] = unit_mean(d, uix, draws[b], U)
            q3.append(dict(metric=met, n_per_arm=n, method="empirical (disjoint seed groups x patient bootstrap)",
                           mdd95=float((np.percentile(nul, 97.5) - np.percentile(nul, 2.5)) / 2), mdd80=np.nan))
        if len(comps):
            c = comps.iloc[0]
            for n in (4, 8, 12, 20):
                se = np.sqrt(2 * c.var_seed / n + 2 * c.var_res / (n * c.patients))
                q3.append(dict(metric=met, n_per_arm=n, method="variance components", mdd95=1.96 * se, mdd80=2.80 * se))
    Q3 = pd.DataFrame(q3)
    Q3.to_csv(out / "q3.csv", index=False)

    # Q4
    q4 = []
    for st in SETS:
        for met in METRICS:
            v5 = SV[(SV.set == st) & (SV.variant == "V0")][met].mean()
            x = SV[(SV.set == st) & (SV.variant == "R0") & SV.seed.isin(primary)].set_index("seed")[met].reindex(primary).values
            if np.isnan(x).any() or len(x) < 4:
                continue
            means = np.array([x[list(c)].mean() for c in itertools.combinations(range(len(x)), 4)])
            q4.append(dict(set=st, metric=met, v5_mean=v5, r0_mean=x.mean(), r0_4seed_q025=np.percentile(means, 2.5),
                           r0_4seed_q975=np.percentile(means, 97.5), v5_percentile=float((means <= v5).mean() * 100)))
    Q4 = pd.DataFrame(q4)
    Q4.to_csv(out / "q4.csv", index=False)

    # Q5
    q5 = []
    pc1 = Path(a.pc1)
    if (pc1 / "per_subject.csv").exists():
        Pa = per_patient_seed(set_names(pd.read_csv(pc1 / "per_subject.csv")))
        old = pd.read_csv(pc1 / "pc1_feature.csv") if (pc1 / "pc1_feature.csv").exists() else pd.DataFrame()
        for arm in ("10a", "10b"):
            for st in SETS:
                for met in METRICS:
                    Am = matrix(Pa, st, arm, met, TAGS4)
                    Rm = matrix(P, st, "R0", met, primary)
                    subj = [s for s in Am.index if s in Rm.index]
                    if not subj:
                        continue
                    Av, Rv = Am.loc[subj].values, Rm.loc[subj].values
                    diff = float((Av.mean(axis=1) - Rv.mean(axis=1)).mean())
                    lo = hi = np.nan
                    if len(subj) >= 2:
                        uix, draws, U = unit_draw(subj, rng, B_Q5)
                        bs = np.empty(B_Q5)
                        for b in range(B_Q5):
                            sa = rng.integers(0, Av.shape[1], Av.shape[1])
                            sr = rng.integers(0, Rv.shape[1], Rv.shape[1])
                            bs[b] = unit_mean(Av[:, sa].mean(axis=1) - Rv[:, sr].mean(axis=1), uix, draws[b], U)
                        lo, hi = np.percentile(bs, 2.5), np.percentile(bs, 97.5)
                    o = old[(old.get("set") == st) & (old.get("comparison") == f"{arm} - R0 (feature effect)")
                            & (old.get("metric") == met)] if len(old) else pd.DataFrame()
                    q5.append(dict(comparison=f"{arm} - R0", set=st, metric=met, r0_seeds=Rv.shape[1], diff=diff,
                                   ci_lo=lo, ci_hi=hi, pc1_diff=o["diff"].iloc[0] if len(o) else np.nan,
                                   pc1_ci_lo=o.ci_lo.iloc[0] if len(o) else np.nan,
                                   pc1_ci_hi=o.ci_hi.iloc[0] if len(o) else np.nan,
                                   reading="primary" if st == "development" else "descriptive"))
    Q5 = pd.DataFrame(q5)
    Q5.to_csv(out / "q5.csv", index=False)

    # Q6
    q6 = ST[["seed", "in_primary", "development_R0_sens", "development_R0s_sens", "development_R0_f1",
             "development_R0s_f1", "development_R0_fa", "development_R0s_fa"]].copy()
    q6.to_csv(out / "q6.csv", index=False)

    gates = dict(m_gates="PASS", m0="PASS", m1="PASS", m2="PASS", info=info, reused=reused, trained=present,
                 pooled=pooled, primary_seeds=primary)
    (out / "gates.json").write_text(json.dumps(gates, indent=1, default=str), encoding="utf-8")
    (out / "T_PC7.md").write_text(report(ST, Q1, QC, Q2, Q3, Q4, Q5, q6, gates), encoding="utf-8")
    print((out / "T_PC7.md").read_text(encoding="utf-8")[:6000])


def report(ST, Q1, QC, Q2, Q3, Q4, Q5, q6, g):
    f3 = lambda x: "—" if x is None or not np.isfinite(x) else f"{x:.3f}"
    f1 = lambda x: "—" if x is None or not np.isfinite(x) else f"{x:.1f}"
    fmt = {"sens": f3, "f1": f3, "fa": f1}
    L = ["# Table T_PC7 — seed variance of the training recipe (R0 retrained, Kaggle CPU)", "",
         f"Design `results/eureka_d34f/DESIGN_PC7.md` (written before the run). Seeds reused from PC1: {', '.join(g['reused'])}; "
         f"trained: {', '.join(sum(g['trained'].values(), []))}. Pooling rule: G-pc7plat / G-pc7rep "
         f"{json.dumps({k: {kk: vv for kk, vv in v.items() if kk != 'skipped'} for k, v in g['info'].items()})} -> "
         f"**{'pooled' if g['pooled'] else 'new seeds only'}, N = {len(g['primary_seeds'])}** in the primary reading. "
         "Per-patient means, own label-free point, after the localizer; development = 15 patients (primary).", "",
         "## Seeds", "", "| seed | origin | validation loss | training loss | dev sensitivity | dev F1 | dev FP/day | test sensitivity |",
         "|---|---|---|---|---|---|---|---|"]
    for _, r in ST.iterrows():
        L.append(f"| {r.seed} | {r.origin}{'' if r.in_primary else ' (not in primary)'} | {r.val_loss:.5f} | {r.train_loss:.5f} | "
                 f"{f3(r.development_R0_sens)} | {f3(r.development_R0_f1)} | {f1(r.development_R0_fa)} | {f3(r.test_R0_sens)} |")
    L += ["", "## Q1 — spread over seeds (R0; V0 = V5's four trainings)", "",
          "| set | variant | metric | seeds | mean | SD [95 % interval] | min | median | max |", "|---|---|---|---|---|---|---|---|---|"]
    for _, r in Q1.iterrows():
        f = fmt[r.metric]
        L.append(f"| {r.set} | {r.variant} | {r.metric} | {r.n_seeds} | {f(r['mean'])} | {f(r.sd)} [{f(r.sd_lo)}, {f(r.sd_hi)}] | "
                 f"{f(r['min'])} | {f(r['median'])} | {f(r['max'])} |")
    L += ["", "Variance components (patient x seed, R0): ", "", "| set | metric | patients | seeds | SD seed (shared) | SD patient x seed | seed share of non-patient variance |",
          "|---|---|---|---|---|---|---|"]
    for _, r in QC.iterrows():
        f = fmt[r.metric]
        L.append(f"| {r.set} | {r.metric} | {r.patients} | {r.seeds} | {f(r.sd_seed)} | {f(r.sd_res)} | {r.seed_share_nonpatient:.2f} |")
    L += ["", "## Q2 — does the loss pick the better detector?", "",
          "| criterion | set | metric | Spearman rho [95 %] | selection gain, 4 seeds [95 %] | chosen >= subset median | reading | wording |",
          "|---|---|---|---|---|---|---|---|"]
    for _, r in Q2.iterrows():
        L.append(f"| {r.criterion} | {r.set} | {r.metric} | {r.rho:+.2f} [{r.rho_lo:+.2f}, {r.rho_hi:+.2f}] | "
                 f"{r.gain_mean:+.3f} [{r.gain_lo:+.3f}, {r.gain_hi:+.3f}] | {r.share_at_or_above_median:.2f} | {r.reading} | {r.wording} |")
    L += ["", "## Q3 — minimal detectable difference of an arm − control comparison (development; lower bounds)", "",
          "| metric | seeds per arm | method | MDD 95 % | MDD 80 % power |", "|---|---|---|---|---|"]
    for _, r in Q3.iterrows():
        f = fmt[r.metric]
        L.append(f"| {r.metric} | {r.n_per_arm} | {r.method} | {f(r.mdd95)} | {f(r.mdd80)} |")
    L += ["", "## Q4 — V5's four trainings in the distribution of 4-seed means of R0 (descriptive; other platform)", "",
          "| set | metric | V5 | R0 mean | R0 4-seed means, central 95 % | V5 percentile |", "|---|---|---|---|---|---|"]
    for _, r in Q4.iterrows():
        f = fmt[r.metric]
        L.append(f"| {r.set} | {r.metric} | {f(r.v5_mean)} | {f(r.r0_mean)} | {f(r.r0_4seed_q025)} – {f(r.r0_4seed_q975)} | {r.v5_percentile:.0f} |")
    L += ["", "## Q5 — PC1 re-read with the training variance (two-level bootstrap)", "",
          "| comparison | set | metric | R0 seeds | Δ [95 %, patients + seeds] | PC1: Δ [95 %, patients only, 4 R0 seeds] | reading |",
          "|---|---|---|---|---|---|---|"]
    for _, r in Q5.iterrows():
        f = fmt[r.metric]
        L.append(f"| {r.comparison} | {r.set} | {r.metric} | {r.r0_seeds} | {f(r['diff'])} [{f(r.ci_lo)}, {f(r.ci_hi)}] | "
                 f"{f(r.pc1_diff)} [{f(r.pc1_ci_lo)}, {f(r.pc1_ci_hi)}] | {r.reading} |")
    L += ["", "## Q6 — k per seed (R0s) against the k of seed 42 (R0), development", "",
          "| seed | sensitivity R0 | sensitivity R0s | F1 R0 | F1 R0s | FP/day R0 | FP/day R0s |", "|---|---|---|---|---|---|---|"]
    for _, r in q6.iterrows():
        L.append(f"| {r.seed} | {f3(r.development_R0_sens)} | {f3(r.development_R0s_sens)} | {f3(r.development_R0_f1)} | "
                 f"{f3(r.development_R0s_f1)} | {f1(r.development_R0_fa)} | {f1(r.development_R0s_fa)} |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
