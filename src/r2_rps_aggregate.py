#!/usr/bin/env python
"""
r2_rps_aggregate.py -- reading of RP_SERIES (stage RP, path 2; docs/FUTURE_RESEARCH_PLAN.md §12 rows 14/11 01:27 and
D26-F). Written, tested on synthetic data and committed BEFORE the RP_SERIES output exists. Descriptive: no pass / fail
threshold on any result (plan P2). Produces the Chapter 2 numbers of report version A2 (REPORT_REVISION_PLAN.md §9.2,
A2 column: F-dm.1, .2, .3a, .4, .5, .7, .9), F-RP5.1 (Chapter3_4_outline_A8.md Part C) and the RP9-E1 figure.

Selection rules (fixed here, before any output):
  macro (the report's form): for each method and cell (smoothing x top-p, or parameter x p), per seed the per-patient
     mean sensitivity (patients with seizures) and the per-patient mean FP/day (all patients of the group); then the
     4-seed means. The best cell = the highest 4-seed-mean sensitivity among cells whose 4-seed-mean FP/day <= 25 (ties:
     lower FP/day, then table order). Reported: sensitivity and FP/day 4-seed mean +- SD (ddof 1), per-patient F1 and
     precision (4-seed means), the cell, and the micro values at the same cell.
  micro (the thesis's design criterion, = e16_recording_baseline.best / e10 / p3b_diag): per seed the pooled sensitivity
     and pooled FP/day of the group, 4-seed means, best cell at pooled FP/day <= 25 (labelled "micro-averaged").
  groups: Table 6 is read on all 15 development patients, the 12 training and the 3 validation patients (the GAE was
     trained on the training patients' clean windows; A-latent leaves the evaluated training patient out of the fit).
  F-dm.3a: the D1b grid at smoothing 5 (the system's) and over every smoothing.
  F-dm.4-5, F-dm.9: e16's own aggregation (median over patients of the 4-seed means).
  F-dm.7: pooled over the 12 training patients: flagged seizure windows / seizure windows (all, and without signal loss).
  F-RP5.1: per primary seed, the record's L1 / L2 / L3 / D7 rows of cmd_eval7; 4-seed mean +- SD of the macro AUROC, the
     prior, AUROC - prior and the panel without chb15.
Gates (STOP):
  A0 the selection code reproduces the thesis values from the committed record grids: e16 (S9 base 0.612, arms a 0.191,
     b 0.582, c 0.295, d 0.487, e 0.628 with their cells; seizure z 4.72 / 4.08 / 4.62; drift 0.851 / 0.845 / 0.083 /
     0.459 / 0.459), e7 (D1 0.479, D2 0.213), e10 (D1 0.489 at 19.78, K 0.250 at 5.78), p3b D1b (smoothing 5: 0.668, top
     0.005, 20.0) — read from the committed SUMMARY files, compared to the printed precision.
  A1 every RP_SERIES gate PASS (G-grid, G-data, RS.0, G-alat, RS-attr, G-flags) and every table complete.
Outputs (--out, default <series>/aggregate): table6.csv, table7.csv, budget.csv, drift.csv, seizure_z.csv, flags.csv,
rp5.csv, rp5_per_seed.csv, e1_figure.png, gates.json, SUMMARY.md.
  python src/r2_rps_aggregate.py --series results/r2/r1_system/rp_series [--out DIR]
  python src/r2_rps_aggregate.py --a0-only
"""
import argparse
import json
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(os.environ.get("THESIS_REPO", Path(__file__).resolve().parents[1]))
REC = REPO / "results"
TRAIN = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08", "chb09", "chb12", "chb19", "chb20", "chb21", "chb23"]
VAL = ["chb10", "chb11", "chb22"]
DEV = TRAIN + VAL
TAGS = ["clean_seed1", "clean_seed2", "clean_seed3", "clean_seed4"]
GROUPS = {"all15": DEV, "train12": TRAIN, "val3": VAL}
CAP = 25.0
T6_KINDS = ["A_latent", "E16a", "E16c", "E16d", "S9base", "E16b", "E16e"]
T7_DET = ["D1", "E7_D2", "E10_K", "E10_D1"]
GATES = ["G-grid", "G-data", "RS.0", "G-alat", "RS-attr", "G-flags"]


def log(*a):
    print(*a, flush=True)


# ============================================================================ selection (generic)
def _subject_table(df, keys):
    g = df.groupby(keys + ["seed", "subject"])[["tp", "fp", "n_ref", "nonict_h"]].sum().reset_index()
    g["sens"] = (g.tp / g.n_ref).where(g.n_ref > 0)
    g["fa"] = g.fp / g.nonict_h * 24
    g["prec"] = (g.tp / (g.tp + g.fp)).where(g.tp + g.fp > 0)
    g["f1"] = 2 * g.tp / (2 * g.tp + g.fp + (g.n_ref - g.tp))
    return g


def per_seed(df, keys):
    """per seed and cell: macro (per-patient mean) and micro (pooled) sensitivity and FP/day."""
    g = _subject_table(df, keys)
    mac = g.groupby(keys + ["seed"]).agg(sens=("sens", "mean"), fa=("fa", "mean"), prec=("prec", "mean"),
                                         f1=("f1", "mean"), patients=("subject", "nunique")).reset_index()
    p = df.groupby(keys + ["seed"])[["tp", "fp", "n_ref", "nonict_h"]].sum().reset_index()
    p["msens"] = p.tp / p.n_ref
    p["mfa"] = p.fp / p.nonict_h * 24
    return mac.merge(p[keys + ["seed", "msens", "mfa", "tp", "fp", "n_ref"]], on=keys + ["seed"])


def select(df, keys, rule, cap=CAP):
    """best cell under the macro or micro rule (module docstring). Returns a dict, or None if no cell is feasible."""
    s = per_seed(df, keys)
    m = s.groupby(keys).agg(sens=("sens", "mean"), sens_sd=("sens", "std"), fa=("fa", "mean"), fa_sd=("fa", "std"),
                            prec=("prec", "mean"), f1=("f1", "mean"), msens=("msens", "mean"), msens_sd=("msens", "std"),
                            mfa=("mfa", "mean"), mfa_sd=("mfa", "std"), seeds=("seed", "nunique"),
                            patients=("patients", "max")).reset_index()
    sk, fk = ("sens", "fa") if rule == "macro" else ("msens", "mfa")
    q = m[m[fk] <= cap]
    if not len(q):
        return None
    q = q.assign(_o=np.arange(len(q))).sort_values([sk, fk, "_o"], ascending=[False, True, True])
    r = q.iloc[0]
    cell = {k: r[k] for k in keys}
    ps = s.merge(pd.DataFrame([cell]), on=keys)
    return dict(rule=rule, **{f"cell_{k}": v for k, v in cell.items()},
                sens=float(r.sens), sens_sd=float(r.sens_sd), fa=float(r.fa), fa_sd=float(r.fa_sd), prec=float(r.prec),
                f1=float(r.f1), micro_sens=float(r.msens), micro_sens_sd=float(r.msens_sd), micro_fa=float(r.mfa),
                micro_fa_sd=float(r.mfa_sd), seeds=int(r.seeds), patients=int(r.patients),
                per_seed_sens="|".join(f"{v:.3f}" for v in ps.sort_values("seed").sens),
                per_seed_micro="|".join(f"{v:.3f}" for v in ps.sort_values("seed").msens))


def e16_median(df, cols):
    """e16 aggregation: per patient the mean over seeds, then the median over patients."""
    return df.groupby("subject")[cols].mean(numeric_only=True).median()


# ============================================================================ A0: the record
def _summary_lines(path):
    out = {}
    for ln in Path(path).read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(\S+)\s+([\d.]+) \((\d+), ([\d.]+), ([\d.]+)\)", ln)
        if m:
            out[m.group(1)] = (float(m.group(2)), int(m.group(3)), float(m.group(4)), float(m.group(5)))
    return out


def gate_a0():
    bad, det = [], {}
    e16 = REC / "e16_recording_baseline"
    for suf, kinds in (("a", ["S9base", "E16a"]), ("bcd", ["E16b", "E16c", "E16d"]), ("ef", ["E16e"])):
        want = _summary_lines(e16 / f"SUMMARY_{suf}.md")
        gr = pd.read_csv(e16 / f"grid_per_subject_{suf}.csv")
        gr["seed"] = gr["seed"].astype(str)
        for k in kinds:
            r = select(gr[gr.kind == k], ["smooth", "top"], "micro")
            got = (round(r["micro_sens"], 3), int(r["cell_smooth"]), float(r["cell_top"]), round(r["micro_fa"], 2))
            ok = got == (want[k][0], want[k][1], want[k][2], want[k][3])
            det[f"e16 {k}"] = dict(got=got, want=want[k], ok=ok)
            bad += [] if ok else [f"e16 {k}"]
    zs = {}
    for suf in ("bcd", "ef"):
        txt = (e16 / f"SUMMARY_{suf}.md").read_text(encoding="utf-8")
        for k, v in re.findall(r"^(\S+)\s+seizure z ([\d.]+)", txt, re.M):
            zs[k] = float(v)
    M = pd.concat([pd.read_csv(e16 / f"mechanism_{s}.csv") for s in ("bcd", "ef")])
    for k in ("S9base", "E16b", "E16e"):
        got = round(float(e16_median(M[M.kind == k], ["sz_median_z"])["sz_median_z"]), 2)
        det[f"seizure z {k}"] = dict(got=got, want=zs[k], ok=got == zs[k])
        bad += [] if got == zs[k] else [f"seizure z {k}"]
    txt = (e16 / "SUMMARY_ef.md").read_text(encoding="utf-8")
    dl = dict(re.findall(r"(\w+) ([\d.]+)", [ln for ln in txt.splitlines() if ln.startswith("S9base  drift")][0]))
    Dg = pd.read_csv(e16 / "diagnostics_ef.csv")
    gm = e16_median(Dg[Dg.kind == "S9base"].drop(columns=["seed"]), list(dl))
    for k, v in dl.items():
        ok = round(float(gm[k]), 3) == float(v)
        det[f"drift {k}"] = dict(got=round(float(gm[k]), 3), want=float(v), ok=ok)
        bad += [] if ok else [f"drift {k}"]
    e7 = pd.read_csv(REC / "e7_ensemble_cpd" / "grid_per_subject.csv")
    e7 = e7[e7.score == "G0"].assign(seed="record")
    for det_, want in (("D1", 0.479), ("D2", 0.213)):
        r = select(e7[e7.detector == det_], ["param", "top"], "micro")
        ok = round(r["micro_sens"], 3) == want
        det[f"e7 {det_}"] = dict(got=round(r["micro_sens"], 3), want=want, ok=ok)
        bad += [] if ok else [f"e7 {det_}"]
    e10 = pd.read_csv(REC / "e10_kernel_cpd" / "grid_per_subject.csv")
    for det_, want in (("D1", (0.489, 15.0, 0.02, 19.78)), ("K", (0.250, 4.0, 0.2, 5.78))):
        r = select(e10[e10.det == det_], ["param", "p"], "micro")
        got = (round(r["micro_sens"], 3), float(r["cell_param"]), float(r["cell_p"]), round(r["micro_fa"], 2))
        ok = got == want
        det[f"e10 {det_}"] = dict(got=got, want=want, ok=ok)
        bad += [] if ok else [f"e10 {det_}"]
    p3 = pd.read_csv(REC / "p3b_diag" / "grid.csv")
    p3 = p3[p3.subject.isin(DEV)]
    r = select(p3[p3.smooth == 5], ["smooth", "top"], "micro")
    got = (round(r["micro_sens"], 3), float(r["cell_top"]), round(r["micro_fa"], 1))
    det["p3b D1b smooth 5"] = dict(got=got, want=(0.668, 0.005, 20.0), ok=got == (0.668, 0.005, 20.0))
    bad += [] if got == (0.668, 0.005, 20.0) else ["p3b D1b"]
    return dict(gate="A0", status="PASS" if not bad else "FAIL", bad=bad, detail=det)


# ============================================================================ A1 + tables
def gate_a1(series):
    gl = {g["gate"]: g for g in json.loads((Path(series) / "gates.json").read_text())}
    bad = [g for g in GATES if gl.get(g, {}).get("status") != "PASS"]
    g = pd.read_csv(Path(series) / "grid_e16.csv")
    n_e16 = len(DEV) * len(TAGS) * len(T6_KINDS) * 4 * 6
    if len(g) != n_e16 or set(g.kind) != set(T6_KINDS) or set(g.subject) != set(DEV):
        bad.append(f"grid_e16 rows {len(g)} (expected {n_e16})")
    d1b = pd.read_csv(Path(series) / "grid_d1b.csv")
    if len(d1b) != len(DEV) * len(TAGS) * 5 * 9:
        bad.append(f"grid_d1b rows {len(d1b)}")
    t7 = pd.read_csv(Path(series) / "table7.csv")
    n_t7 = len(DEV) * len(TAGS) * (2 + 3 * 6 + 6 + 3 * 5)
    if len(t7) != n_t7:
        bad.append(f"table7 rows {len(t7)} (expected {n_t7})")
    fl = pd.read_csv(Path(series) / "flags.csv")
    if sorted(fl.case) != sorted(TRAIN):
        bad.append("flags cases")
    for s in TAGS:
        if not (Path(series) / "rp5" / f"seed{int(s[-1])}" / "attribution_tests.csv").exists():
            bad.append(f"rp5 seed {s}")
    return dict(gate="A1", status="PASS" if not bad else "FAIL", bad=bad, mode=gl.get("RS.0", {}).get("mode"))


def table6(series):
    g = pd.read_csv(Path(series) / "grid_e16.csv")
    rows = []
    for k in T6_KINDS:
        for gname, subs in GROUPS.items():
            for rule in ("macro", "micro"):
                r = select(g[(g.kind == k) & g.subject.isin(subs)], ["smooth", "top"], rule)
                rows.append(dict(kind=k, group=gname, **(r or dict(rule=rule))))
    return pd.DataFrame(rows)


def table7(series):
    d1b = pd.read_csv(Path(series) / "grid_d1b.csv").rename(columns={"smooth": "param", "top": "p"})
    t7 = pd.read_csv(Path(series) / "table7.csv")
    rows = []
    for det in T7_DET:
        src = d1b if det == "D1" else t7[t7.detector == det]
        for rule in ("macro", "micro"):
            r = select(src, ["param", "p"], rule)
            rows.append(dict(detector=det, **(r or dict(rule=rule))))
    pel = t7[t7.detector == "PELT_locked"]
    for pt, gg in pel.groupby("param"):
        s = per_seed(gg, ["param"])
        rows.append(dict(detector="PELT_locked", rule="point", cell_param=pt, cell_p=np.nan, sens=s.sens.mean(),
                         sens_sd=s.sens.std(), fa=s.fa.mean(), fa_sd=s.fa.std(), prec=s.prec.mean(), f1=s.f1.mean(),
                         micro_sens=s.msens.mean(), micro_sens_sd=s.msens.std(), micro_fa=s.mfa.mean(),
                         micro_fa_sd=s.mfa.std(), seeds=int(s.seed.nunique()), patients=int(s.patients.max())))
    return pd.DataFrame(rows)


def budget(series):
    d1b = pd.read_csv(Path(series) / "grid_d1b.csv")
    rows = []
    for name, src in (("smoothing 5", d1b[d1b.smooth == 5]), ("any smoothing", d1b)):
        for rule in ("macro", "micro"):
            rows.append(dict(scope=name, **(select(src, ["smooth", "top"], rule) or dict(rule=rule))))
    return pd.DataFrame(rows)


def drift(series):
    Dg = pd.read_csv(Path(series) / "diagnostics.csv")
    cols = ["drift_iqr_over_mad", "tail_share_top_quartile_files", "top_files_with_seizure", "flag_share_top_files",
            "flag_share_other_files"]
    gm = e16_median(Dg[Dg.kind == "S9base"].drop(columns=["seed"]), cols)
    per = Dg[Dg.kind == "S9base"].groupby("seed")[cols].median()
    return pd.DataFrame([dict(item=c, value=float(gm[c]), per_seed_median="|".join(f"{v:.3f}" for v in per[c])) for c in cols])


def seizure_z(series):
    M = pd.read_csv(Path(series) / "mechanism.csv")
    rows = []
    for k in ["S9base", "E16e", "E16b", "A_latent", "E16a", "E16c", "E16d"]:
        q = M[M.kind == k]
        rows.append(dict(kind=k, sz_median_z=float(e16_median(q, ["sz_median_z"])["sz_median_z"]),
                         flag_median_z=float(e16_median(q, ["flag_median_z"])["flag_median_z"]),
                         per_seed="|".join(f"{v:.2f}" for v in q.groupby("seed").sz_median_z.median())))
    return pd.DataFrame(rows)


def flags_table(series):
    F = pd.read_csv(Path(series) / "flags.csv")
    tot = dict(case="pooled (12 training patients)", **{c: int(F[c].sum()) for c in
               ("windows", "ictal", "ictal_flagged", "ictal_ok", "ictal_ok_flagged", "base", "base_flagged")})
    F = pd.concat([F, pd.DataFrame([tot])], ignore_index=True)
    F["ictal_flag_share"] = F.ictal_flagged / F.ictal
    F["ictal_ok_flag_share"] = F.ictal_ok_flagged / F.ictal_ok
    F["base_flag_share"] = F.base_flagged / F.base
    return F


def rp5(series):
    rows, per = [], []
    for s in TAGS:
        n = int(s[-1])
        d = Path(series) / "rp5" / f"seed{n}"
        su = pd.read_csv(d / "attribution_summary.csv")
        te = pd.read_csv(d / "attribution_tests.csv").set_index("test")
        a = su[su.panel == "ALL focal (primary)"].iloc[0]
        x15 = su[su.panel.str.startswith("focal excl. chb15")].iloc[0]
        per.append(dict(seed=n, macro_auroc=a.macro_AUROC, ci_lo=a.AUROC_CI_lo, ci_hi=a.AUROC_CI_hi, p_perm=a.p_perm,
                        prior=a.macro_AUROC_prior, delta_prior=a.delta_vs_prior,
                        delta_prior_ci_lo=te.loc["L2 anatomical prior", "CI_lo"],
                        delta_prior_ci_hi=te.loc["L2 anatomical prior", "CI_hi"],
                        sibling_T=te.loc["L3 matched vs swapped", "value"], sibling_p=te.loc["L3 matched vs swapped", "p"],
                        d7=te.loc["D7 subject-constant (as registered)", "value"], auroc_excl_chb15=x15.macro_AUROC,
                        n_focal=int(a.n_seizures)))
    P = pd.DataFrame(per)
    for c in ("macro_auroc", "prior", "delta_prior", "sibling_T", "d7", "auroc_excl_chb15"):
        rows.append(dict(item=c, mean=float(P[c].mean()), sd=float(P[c].std()), per_seed="|".join(f"{v:.4f}" for v in P[c])))
    return pd.DataFrame(rows), P


def e1_figure(series, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    e = pd.read_csv(Path(series) / "e1_chb03_seed3.csv").sort_values("window")
    files = sorted(e.file_idx.unique())
    lens = {f: int((e.file_idx == f).sum()) for f in files}
    off, tt = {}, np.zeros(len(e))
    acc = 0
    for f in files:
        off[f] = acc
        acc += e[e.file_idx == f].t_in_file_s.max() + 4
    tt = (e.t_in_file_s + e.file_idx.map(off)).values / 60.0
    fig, ax = plt.subplots(2, 1, figsize=(10, 5), sharex=True)
    for a, y, title in ((ax[0], e.s9.values, "(a) before correction"), (ax[1], e.s9_corrected.values, "(b) after correction")):
        a.plot(tt, y, lw=0.5, color="0.25")
        if a is ax[0]:
            a.plot(tt, e.running_median.values, lw=1.2, color="tab:orange", label="running median (±15 min)")
            a.legend(loc="upper right", fontsize=8, frameon=False)
        ict = e.ictal.values.astype(bool)
        for i0 in np.flatnonzero(np.diff(np.r_[0, ict.astype(int)]) == 1):
            i1 = i0 + np.argmin(ict[i0:]) if not ict[i0:].all() else len(ict)
            a.axvspan(tt[i0], tt[i1 - 1] + 4 / 60, color="tab:red", alpha=0.2, lw=0)
        for f in files[1:]:
            a.axvline(off[f] / 60.0, ls="--", color="0.5", lw=0.8)
        a.set_ylabel("9th-largest member")
        a.set_title(title, fontsize=9, loc="left")
    ax[1].set_xlabel("time (min), chb03 files 1–3 laid end to end")
    fig.tight_layout()
    fig.savefig(Path(out) / "e1_figure.png", dpi=200)
    plt.close(fig)
    return lens


def fmt(r, rule):
    if r is None or pd.isna(r.get("sens", np.nan)):
        return "no cell <= 25 FP/day"
    if rule == "macro":
        return f"{r['sens']:.3f} ± {r['sens_sd']:.3f} at {r['fa']:.1f} ± {r['fa_sd']:.1f} FP/day (micro {r['micro_sens']:.3f} at {r['micro_fa']:.1f})"
    return f"{r['micro_sens']:.3f} ± {r['micro_sens_sd']:.3f} at {r['micro_fa']:.1f} FP/day (macro {r['sens']:.3f} at {r['fa']:.1f})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--series")
    ap.add_argument("--out")
    ap.add_argument("--a0-only", action="store_true")
    a = ap.parse_args()
    a0 = gate_a0()
    log(f"A0 {a0['status']}" + (f": {a0['bad']}" if a0["bad"] else ""))
    if a.a0_only:
        if a0["status"] != "PASS":
            raise SystemExit("STOP A0")
        return
    series = Path(a.series)
    out = Path(a.out) if a.out else series / "aggregate"
    out.mkdir(parents=True, exist_ok=True)
    gates = [a0]
    if a0["status"] != "PASS":
        (out / "gates.json").write_text(json.dumps(gates, indent=1, default=str))
        raise SystemExit(f"STOP A0: {a0['bad']}")
    a1 = gate_a1(series)
    gates.append(a1)
    (out / "gates.json").write_text(json.dumps(gates, indent=1, default=str))
    log(f"A1 {a1['status']}" + (f": {a1['bad']}" if a1["bad"] else ""))
    if a1["status"] != "PASS":
        raise SystemExit(f"STOP A1: {a1['bad']}")
    T6, T7, BU, DR, SZ, FL = table6(series), table7(series), budget(series), drift(series), seizure_z(series), flags_table(series)
    R5, R5s = rp5(series)
    for name, df in (("table6", T6), ("table7", T7), ("budget", BU), ("drift", DR), ("seizure_z", SZ), ("flags", FL),
                     ("rp5", R5), ("rp5_per_seed", R5s)):
        df.to_csv(out / f"{name}.csv", index=False)
    e1_figure(series, out)
    pick = lambda df, **kw: df.loc[np.logical_and.reduce([df[k] == v for k, v in kw.items()])].iloc[0].to_dict()  # noqa: E731
    L = ["# RP_SERIES — Chapter 2 numbers of version A2, F-RP5.1, RP9-E1 (path-2 model, seeds 1–4)\n",
         f"Script `src/r2_rps_aggregate.py` (committed before the run). Gates: A0 {a0['status']}, A1 {a1['status']} "
         f"(RS.0 mode {a1['mode']}). Macro = per-patient mean (the report's form); micro = pooled (the thesis's design "
         "criterion). Best cell at FP/day <= 25; 4-seed mean ± SD.\n",
         "## F-dm.1 Table 6 — normal reference (development patients; e16 grid)\n",
         "| reference | group | macro (report) | micro (design criterion) | macro cell |", "|---|---|---|---|---|"]
    names = {"A_latent": "A. other patients (latent, training fit, patient left out)", "E16a": "B. first 10 min of each file",
             "E16c": "B. first 30 min of each file", "E16d": "B. causal 30-min window", "S9base": "C. whole recording (S9 base)",
             "E16b": "C + level-and-spread drift correction (e16 b)", "E16e": "C + level-only drift correction (e16 e)"}
    for k in T6_KINDS:
        for gname in GROUPS:
            ma, mi = pick(T6, kind=k, group=gname, rule="macro"), pick(T6, kind=k, group=gname, rule="micro")
            cell = f"({int(ma['cell_smooth'])}, {ma['cell_top']})" if not pd.isna(ma.get("cell_smooth", np.nan)) else "—"
            L.append(f"| {names[k]} | {gname} | {fmt(ma, 'macro')} | {fmt(mi, 'micro')} | {cell} |")
    L += ["\n## F-dm.2 Table 7 — detection on the final score (development patients)\n",
          "| detector | macro | micro | macro cell |", "|---|---|---|---|"]
    for det in T7_DET:
        ma, mi = pick(T7, detector=det, rule="macro"), pick(T7, detector=det, rule="micro")
        cell = f"({ma.get('cell_param')}, {ma.get('cell_p')})" if not pd.isna(ma.get("sens", np.nan)) else "—"
        L.append(f"| {det} | {fmt(ma, 'macro')} | {fmt(mi, 'micro')} | {cell} |")
    for r in T7[T7.rule == "point"].to_dict("records"):
        L.append(f"| PELT locked {r['cell_param']} | {r['sens']:.3f} ± {r['sens_sd']:.3f} at {r['fa']:.1f} FP/day | "
                 f"{r['micro_sens']:.3f} at {r['micro_fa']:.1f} | point |")
    L += ["\n## F-dm.3a best single development budget (D1b grid, final score)\n"]
    for r in BU.to_dict("records"):
        L.append(f"- {r['scope']}, {r['rule']}: top {r.get('cell_top')} (smoothing {r.get('cell_smooth')}) → {fmt(r, r['rule'])}")
    L += ["\n## F-dm.4–5 drift under S9 base (median over patients of 4-seed means)\n"]
    L += [f"- {r['item']}: {r['value']:.3f} (per seed {r['per_seed_median']})" for r in DR.to_dict("records")]
    L += ["\n## F-dm.9 median robust z of the seizure windows (development patients)\n"]
    L += [f"- {r['kind']}: {r['sz_median_z']:.2f} (flagged non-seizure {r['flag_median_z']:.2f}; per seed {r['per_seed']})"
          for r in SZ.to_dict("records")]
    pf = FL.iloc[-1]
    L += ["\n## F-dm.7 5-SD flag share of the seizure windows (12 training patients, R0 thresholds)\n",
          f"- pooled: {int(pf.ictal_flagged)} of {int(pf.ictal)} seizure windows = {pf.ictal_flag_share:.3f}; without signal "
          f"loss {pf.ictal_ok_flag_share:.3f}; non-seizure, non-buffer windows {pf.base_flag_share:.3f} (= F-dm.6 check)"]
    L += ["\n## F-RP5.1 channel ranking (62 focal test seizures, each seed as primary)\n",
          "| item | mean ± SD | per seed (1–4) |", "|---|---|---|"]
    L += [f"| {r['item']} | {r['mean']:.4f} ± {r['sd']:.4f} | {r['per_seed']} |" for r in R5.to_dict("records")]
    L += ["\nPer seed: `rp5_per_seed.csv`. RP9-E1: `e1_figure.png` (chb03 files 1–3, seed 3)."]
    (out / "SUMMARY.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    log("\n".join(L))


if __name__ == "__main__":
    main()
