#!/usr/bin/env python
"""
eur_v1_read.py -- reader of EUR_V1 (milestone M2, item V1; chat F2-02; design results/m2_v1/DESIGN_V1.md §5). Committed
BEFORE the run's outputs exist. Reads the run folder (default results/m2_v1/run) and writes results/m2_v1/reading/:
  T_V1.md            the tables below in one file
  curve.csv          (a) per set x stage x budget: per-patient mean sensitivity [patient-bootstrap 95 % CI], seed SD,
                     seizures found / annotated (4-seed mean), realized review share (per-patient mean and pooled), FP/day,
                     events per hour; chance reference (scores circularly shifted within files) beside it and the paired
                     difference V5 - chance [CI]
  rank.csv           (b) per set x method (b1 V5's own events, b2 peak-centred 120-s clips) x rate: the same columns
  missed.csv         (c) every annotated seizure at 5 % and 10 % of windows flagged (detector and cpd stages): seeds that
                     caught it (0-4), descriptors (results/v9_v1/part1_descriptors.csv), an empty registry column
  missed_summary.csv (c) counts and descriptor medians, caught by all / some / no seed
  fig_v1_curve.png   seizures found against the share of the recording reviewed, one panel per set
Rules (design §5, fixed before the run): sets development (15), test (8), chb24, Siena (14); per-patient values = the
4-seed mean (chance: mean over seeds and shifts) of tp / n_ref (patients with >= 1 seizure), fp / non-ictal h x 24,
review_s / rec_s, n_events / recorded h; per-patient mean over the set; patient bootstrap B = 10,000, rng 0, units =
patients with chb01 + chb21 one unit (the statistic is the mean over the patients of the drawn units); paired: the same
draw for V5 and chance. No pass / fail threshold.
Reader gates (STOP unless PASS): M0 every expected row present (cases x seeds x budgets x stages; chance cases x seeds x
shifts x budgets; ranked cases x seeds x 15); M1 every gate of the run PASS (the expected list); M2 sum of the per-seizure
flags = the scorer's tp wherever the scorer's reference count equals the annotated count; M3 the V5 own point of the run
(own cpd per-patient mean on test) is recomputed from own_rows.csv and equals the b1 'all' rows.
  python src/eur_v1_read.py [--run DIR] [--out DIR]
"""
import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(os.environ.get("THESIS_REPO", Path(__file__).resolve().parents[1]))
B, RNG = 10_000, 0
UNIT = {"chb21": "chb01"}
GATES = ["G-self-v1", "G-data", "R1.0-dev", "R1.0-test", "GE", "G-v5own[smoke]", "G-curve[smoke]", "G-worker[smoke]",
         "SMOKE", "G-k", "G-kv1", "G-v5own[full]", "G-curve[full]", "G-worker[full]"]
SETS = ("development", "test", "chb24", "siena")
DESC_SET = {"development": "development", "test": "chb-test", "chb24": "chb24", "siena": "siena"}


def stop(msg):
    raise SystemExit(f"STOP {msg}")


def set_label(row_set, subject):
    if row_set == "external":
        return "chb24" if subject == "chb24" else "siena"
    return row_set


def boot_mean(per_patient, units, rng_seed=RNG, b=B):
    """per_patient: Series indexed by patient. Returns (point, lo, hi) of the mean over patients, units resampled."""
    pp = per_patient.dropna()
    if len(pp) == 0:
        return np.nan, np.nan, np.nan
    u = pd.Series([units.get(p, p) for p in pp.index], index=pp.index)
    groups = [pp[u == g].to_numpy() for g in sorted(u.unique())]
    rng = np.random.default_rng(rng_seed)
    draws = rng.integers(0, len(groups), size=(b, len(groups)))
    sums = np.array([g.sum() for g in groups]); cnt = np.array([len(g) for g in groups])
    stat = sums[draws].sum(1) / cnt[draws].sum(1)
    return float(pp.mean()), float(np.quantile(stat, 0.025)), float(np.quantile(stat, 0.975))


def per_patient(df, keys):
    """per-patient values (seed-averaged; for chance also shift-averaged)."""
    d = df.copy()
    d["sens"] = np.where(d.n_ref > 0, d.tp / d.n_ref.where(d.n_ref > 0), np.nan)
    d["fpd"] = d.fp / d.nonict_h * 24
    d["rev"] = d.review_s / d.rec_s
    if "n_events" in d:
        d["evh"] = d.n_events / (d.rec_s / 3600)
    if "N" in d:
        d["evh"] = d.N / d.hours
    cols = [c for c in ("sens", "fpd", "rev", "evh", "tp", "n_ref", "review_s", "rec_s") if c in d]
    return d.groupby(keys + ["subject"])[cols].mean().reset_index()


def seed_sd(df, keys):
    d = df.copy()
    d["sens"] = np.where(d.n_ref > 0, d.tp / d.n_ref.where(d.n_ref > 0), np.nan)
    m = d.groupby(keys + ["seed"]).sens.mean().reset_index()
    return m.groupby(keys).sens.std(ddof=1)


def summarise(pp, keys, sd=None):
    out = []
    for k, g in pp.groupby(keys):
        g = g.set_index("subject")
        s, lo, hi = boot_mean(g.sens, UNIT)
        k = k if isinstance(k, tuple) else (k,)
        r = dict(zip(keys, k), patients=int(len(g)), sens=s, sens_lo=lo, sens_hi=hi,
                 found=float(g.tp.sum()), annotated=float(g.n_ref.sum()), fp_day=float(g.fpd.mean()),
                 review_pct=100 * float(g.rev.mean()), review_pooled_pct=100 * float(g.review_s.sum() / g.rec_s.sum()),
                 events_per_h=float(g.evh.mean()))
        if sd is not None:
            r["sens_seed_sd"] = float(sd.get(k if len(k) > 1 else k[0], np.nan))
        out.append(r)
    return pd.DataFrame(out)


def paired_diff(a, b_, keys):
    """V5 - chance per patient, paired patient bootstrap."""
    m = a.merge(b_, on=keys + ["subject"], suffixes=("", "_null"))
    out = []
    for k, g in m.groupby(keys):
        d = (g.sens - g.sens_null)
        d.index = g.subject
        s, lo, hi = boot_mean(d, UNIT)
        k = k if isinstance(k, tuple) else (k,)
        out.append(dict(zip(keys, k), d_sens=s, d_lo=lo, d_hi=hi))
    return pd.DataFrame(out)


def fmt(v, nd=3):
    return "—" if v is None or (isinstance(v, float) and not np.isfinite(v)) else f"{v:.{nd}f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=str(ROOT / "results" / "m2_v1" / "run"))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    run = Path(a.run)
    out = Path(a.out) if a.out else run.parent / "reading"
    out.mkdir(parents=True, exist_ok=True)
    rd = lambda f: pd.read_csv(run / f, float_precision="round_trip")
    for f in ("grid.csv", "null.csv", "rank.csv", "seizures.csv", "own_rows.csv", "gates.json", "run_meta.json"):
        if not (run / f).exists():
            stop(f"M0: {f} missing in {run}")
    meta = json.loads((run / "run_meta.json").read_text())
    grid, null, rank, seiz, own = rd("grid.csv"), rd("null.csv"), rd("rank.csv"), rd("seizures.csv"), rd("own_rows.csv")
    rank["rate"] = rank.rate.astype(str)
    for d in (grid, null, rank, seiz, own):
        d["S"] = [set_label(s, p) for s, p in zip(d.set, d.subject)]
    cases = sorted(own.subject.unique())
    seeds = sorted(own.seed.unique())
    G, ST, NS, RATES = meta["grid"], meta["stages"], meta["nshift"], meta["rates"]
    # ---- M0
    want = dict(grid=len(cases) * len(seeds) * len(G) * len(ST), null=len(cases) * len(seeds) * NS * len(G),
                rank=len(cases) * len(seeds) * (2 * len(RATES) + 1))
    got = dict(grid=len(grid.drop_duplicates(["subject", "seed", "stage", "top"])),
               null=len(null.drop_duplicates(["subject", "seed", "shift", "top"])),
               rank=len(rank.drop_duplicates(["subject", "seed", "method", "rate"])))
    if got != want or len(grid) != want["grid"]:
        stop(f"M0: rows {got} != expected {want}")
    # ---- M1
    gates = {g["gate"]: g["status"] for g in json.loads((run / "gates.json").read_text())}
    miss = [g for g in GATES if gates.get(g) != "PASS"]
    if miss:
        stop(f"M1: gates not PASS / absent: {miss}")
    # ---- M2
    sc = seiz.groupby(["subject", "seed", "stage", "top"]).agg(caught=("caught", "sum"), n=("caught", "size")).reset_index()
    mg = grid.merge(sc, on=["subject", "seed", "stage", "top"], how="left")
    comp = mg[mg.n_ref == mg.n.fillna(0)]
    bad = comp[comp.caught.fillna(0) != comp.tp]
    if len(bad):
        stop(f"M2: per-seizure flags != tp in {len(bad)} rows: {bad.head(5).to_dict('records')}")
    n_noncomp = int((mg.n_ref != mg.n.fillna(0)).sum())
    # ---- M3
    oc = own[(own.budget == "own") & (own.stage == "cpd")][["subject", "seed", "tp", "fp"]]
    ba = rank[(rank.method == "b1") & (rank.rate == "all")][["subject", "seed", "tp", "fp"]]
    m3 = oc.merge(ba, on=["subject", "seed"], suffixes=("", "_b1"))
    if len(m3) != len(oc) or not ((m3.tp == m3.tp_b1) & (m3.fp == m3.fp_b1)).all():
        stop("M3: b1 'all' rows != the own cpd rows")
    print(f"M0-M3 PASS (rows {got}; {n_noncomp} grid rows where the scorer merged / split references, flags descriptive)")

    # ---- (a) curve
    pg = per_patient(grid, ["S", "stage", "top"])
    pn = per_patient(null, ["S", "top"])
    ca = summarise(pg, ["S", "stage", "top"], seed_sd(grid, ["S", "stage", "top"]))
    cn = summarise(pn, ["S", "top"]).add_prefix("null_").rename(columns={"null_S": "S", "null_top": "top"})
    dd = paired_diff(pg[pg.stage == "detector"].drop(columns="stage"), pn, ["S", "top"])
    curve = ca.merge(cn, on=["S", "top"], how="left").merge(dd.assign(stage="detector"), on=["S", "stage", "top"],
                                                            how="left")
    po = per_patient(own.assign(n_events=np.nan), ["S", "budget", "stage"])
    own_pt = summarise(po, ["S", "budget", "stage"])
    curve.to_csv(out / "curve.csv", index=False)
    own_pt.to_csv(out / "own_point.csv", index=False)
    # ---- (b) ranked events
    pr = per_patient(rank, ["S", "method", "rate"])
    rk = summarise(pr, ["S", "method", "rate"], seed_sd(rank, ["S", "method", "rate"]))
    rk.to_csv(out / "rank.csv", index=False)
    # ---- (c) missed at 5 % and 10 %
    sub = seiz[seiz.top.isin([0.05, 0.10])]
    per_s = sub.groupby(["S", "subject", "stage", "top", "file", "file_idx", "ref_i", "on_s", "off_s"]).caught.agg(
        ["sum", "size"]).reset_index().rename(columns={"sum": "seeds_caught", "size": "seeds"})
    per_s["duration_s"] = per_s.off_s - per_s.on_s
    dsc_f = ROOT / "results" / "v9_v1" / "part1_descriptors.csv"
    if dsc_f.exists():
        dsc = pd.read_csv(dsc_f)
        dsc["fbase"] = dsc.file.astype(str).map(lambda s: Path(s.replace("\\", "/")).name)
        joined = []
        for _, r in per_s.iterrows():
            cand = dsc[(dsc.set == DESC_SET[r.S]) & (dsc.subject == r.subject)
                       & (dsc.fbase == Path(str(r.file).replace("\\", "/")).name)]
            cand = cand.assign(gap=(cand.onset_s - r.on_s).abs())
            c = cand[cand.gap <= 8].sort_values("gap")
            joined.append(dict(desc_join="matched" if len(c) else "none",
                               amp_ratio=c.amp_ratio.iloc[0] if len(c) else np.nan,
                               desc_duration_s=c.duration_s.iloc[0] if len(c) else np.nan,
                               spatial_extent=c.spatial_extent.iloc[0] if len(c) else np.nan,
                               dom_freq_hz=c.dom_freq_hz.iloc[0] if len(c) else np.nan))
        per_s = pd.concat([per_s.reset_index(drop=True), pd.DataFrame(joined)], axis=1)
    per_s["registry_row"] = ""
    per_s.to_csv(out / "missed.csv", index=False)
    per_s["group"] = np.select([per_s.seeds_caught == per_s.seeds, per_s.seeds_caught == 0], ["all", "none"], "some")
    agg = dict(seizures=("ref_i", "size"), median_duration_s=("duration_s", "median"))
    if "amp_ratio" in per_s:
        agg["median_amp_ratio"] = ("amp_ratio", "median")
    ms = per_s.groupby(["S", "stage", "top", "group"]).agg(**agg).reset_index()
    ms.to_csv(out / "missed_summary.csv", index=False)

    # ---- T_V1.md
    L = [f"# V1 — seizures found against the share of the recording reviewed (V5, 4 seeds; run {meta.get('repo_commit')})",
         "", "Per-patient means; [patient-bootstrap 95 % CI]; review = event time opened / recorded time; chance = scores "
         "circularly shifted within each file. Development includes the 12 training patients (optimistic); test, chb24 "
         "and Siena descriptive. Reader gates M0–M3 PASS.", ""]
    for S in SETS:
        L += [f"## {S} — (a) budget sweep, detector stage (cpd beside)", "",
              "| windows flagged | review % | sensitivity [CI] | found / annotated | FP/day | cpd sensitivity | cpd review % | "
              "chance sensitivity | V5 − chance [CI] |", "|---|---|---|---|---|---|---|---|---|"]
        c = curve[curve.S == S]
        for top in G:
            d_ = c[(c.stage == "detector") & np.isclose(c.top, top)]
            p_ = c[(c.stage == "cpd") & np.isclose(c.top, top)]
            if not len(d_):
                continue
            d_, p_ = d_.iloc[0], p_.iloc[0]
            L.append(f"| {100*top:g} % | {fmt(d_.review_pct, 2)} | {fmt(d_.sens)} [{fmt(d_.sens_lo)}, {fmt(d_.sens_hi)}] | "
                     f"{d_.found:.2f} / {d_.annotated:.0f} | {fmt(d_.fp_day, 1)} | {fmt(p_.sens)} | {fmt(p_.review_pct, 2)} | "
                     f"{fmt(d_.null_sens)} | {fmt(d_.d_sens, 3)} [{fmt(d_.d_lo)}, {fmt(d_.d_hi)}] |")
        o = own_pt[(own_pt.S == S) & (own_pt.budget == "own") & (own_pt.stage == "cpd")]
        if len(o):
            o = o.iloc[0]
            L += ["", f"V5's own label-free point (cpd): sensitivity {fmt(o.sens)} [{fmt(o.sens_lo)}, {fmt(o.sens_hi)}], "
                      f"review {fmt(o.review_pct, 2)} %, {fmt(o.fp_day, 1)} FP/day.", ""]
        L += [f"### {S} — (b) top-N events per hour of EEG", "",
              "| method | rate (/h) | events / h | review % | sensitivity [CI] | found / annotated | FP/day |",
              "|---|---|---|---|---|---|---|"]
        for _, r in rk[rk.S == S].sort_values(["method", "rate"], key=lambda s: s if s.name == "method" else
                                                 pd.to_numeric(s, errors="coerce").fillna(1e9)).iterrows():
            L.append(f"| {r.method} | {r.rate} | {fmt(r.events_per_h, 2)} | {fmt(r.review_pct, 2)} | {fmt(r.sens)} "
                     f"[{fmt(r.sens_lo)}, {fmt(r.sens_hi)}] | {r.found:.2f} / {r.annotated:.0f} | {fmt(r.fp_day, 1)} |")
        L += ["", f"### {S} — (c) seizures by seeds that caught them (5 % / 10 % of windows flagged)", "",
              "| stage | flagged | caught by all 4 | some | none | median duration (none) s | median amplitude ratio (none) |",
              "|---|---|---|---|---|---|---|"]
        for st in ST:
            for top in (0.05, 0.10):
                g = ms[(ms.S == S) & (ms.stage == st) & np.isclose(ms.top, top)].set_index("group")
                n_ = lambda k: int(g.seizures.get(k, 0))
                md_ = g.median_duration_s.get("none", np.nan)
                ma_ = g.median_amp_ratio.get("none", np.nan) if "median_amp_ratio" in g else np.nan
                L.append(f"| {st} | {100*top:g} % | {n_('all')} | {n_('some')} | {n_('none')} | {fmt(md_, 0)} | {fmt(ma_, 2)} |")
        L.append("")
    (out / "T_V1.md").write_text("\n".join(L) + "\n")

    # ---- figure
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker  # noqa: F401
    blue, orange, gray, ink = "#2a78d6", "#eb6834", "#8a8984", "#52514e"
    fig, axs = plt.subplots(1, 4, figsize=(15, 3.9), sharey=True)
    for ax, S in zip(axs, SETS):
        c = curve[curve.S == S].sort_values("top")
        d_, p_ = c[c.stage == "detector"], c[c.stage == "cpd"]
        ax.fill_between(d_.review_pct, d_.sens_lo, d_.sens_hi, color=blue, alpha=0.15, lw=0)
        ax.plot(d_.review_pct, d_.sens, color=blue, lw=2, marker="o", ms=4, label="V5 (detector)")
        ax.plot(p_.review_pct, p_.sens, color=orange, lw=2, ls="--", label="V5 (change point stage)")
        ax.plot(d_.null_review_pct, d_.null_sens, color=gray, lw=2, ls=":", label="chance (shifted scores)")
        o = own_pt[(own_pt.S == S) & (own_pt.budget == "own") & (own_pt.stage == "cpd")]
        if len(o):
            ax.plot(o.review_pct, o.sens, marker="D", ms=8, color=ink, ls="none", label="V5 own label-free point")
        ax.set_xscale("log"); ax.set_ylim(0, 1.02); ax.set_title(S, color=ink)
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.set_xlabel("share of the recording reviewed (%)", color=ink)
        ax.grid(True, color="#e6e5e1", lw=0.6); ax.spines[["top", "right"]].set_visible(False)
    axs[0].set_ylabel("seizures found (per-patient mean)", color=ink)
    axs[0].legend(frameon=False, fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(out / "fig_v1_curve.png", dpi=150)
    print(f"written {out}: T_V1.md, curve.csv, own_point.csv, rank.csv, missed.csv, missed_summary.csv, fig_v1_curve.png")


if __name__ == "__main__":
    main()
