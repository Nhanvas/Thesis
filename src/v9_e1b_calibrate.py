#!/usr/bin/env python
"""
v9_e1b_calibrate.py -- V9-E1b (docs/prompts/V9_E1B_CALIBRATE.md): give B4 and F their own fair
per-patient budget, calibrated the SAME way as G (p3_levers.calibrate / p3_levers.q_of, unchanged),
on development patients only (seed 42), then evaluate G, B4 and F at their own calibrated balanced
point, after the frozen CPD localizer, once, on development, CHB-MIT test, chb24 and all 14 Siena
patients.

WHY: V9-E1 showed B4 and F beat G at matched FP/day, but at the "balanced" point every baseline ran
at ~55-60 FP/day because k=4.0677 was calibrated ONLY for G's own score (p3_levers.py, seed 42, 15
development patients). A fair system comparison needs each arm's per-patient budget calibrated the
same way, on its own score, on development only.

READ-ONLY REUSE: src/v9_e1_baselines.py (V9-E1's own code -- already reported, not re-edited here)
for subject_ctx / cache_D / load_D / final_scalar_from_D / member_mean_z_from_D / evaluate_arm /
sweep_detector / duration_bins / boot_mean_ci / arm_summary / fmt_arm_row / matched_curve /
patient_mean_ci / duration_table / ARM_LABEL / check_ext_repro -- every one of them is generic over
"which D / which k", so none needed editing. src/p3_levers.py for calibrate() (the bisection itself,
UNCHANGED) and q_of/localize/refs_of/err_stats. src/e18_cpd_localizer.py for match_errors.

v9_e1_baselines.EXT only lists chb24 + 3 Siena patients (what V9-T3 had raw EDF for when V9-E1 ran);
V9-T4 has since built the raw-feature xcache for all 14 Siena patients. Rather than edit the frozen
V9-E1 file, this script extends v9_e1_baselines.EXT / .SIENA_MISSING at runtime (a module-attribute
patch, not a file edit -- the same technique v9_anatomy.py used for x1_external._parseTimeStamp) before
calling its functions. v9_e1_baselines.CACHE (results/v9_e1/cache/, gitignored) is reused unchanged --
the new Siena patients' B1-B4 feature cache is written there as an ordinary cache-miss build.

CALIBRATION CONSTRUCTION (same transform-and-average PATTERN as G's own m(t), at the natural level
for each arm -- nothing new invented):
  G:  m(t) = v9_e1_baselines.member_mean_z_from_D(ctx, ctx["D"]["clean_seed42"])     (reproduces k=4.0677)
  B4: m(t) = v9_e1_baselines.member_mean_z_from_D(ctx, D_B4)                         (D_B4 deterministic)
  F:  m(t) = mean(e16_recording_baseline.rz(xg, ok), rz(xb4, ok)) -- the SAME rz-then-average pattern
      as G's m(t) (rz each constituent, then average), applied one level up at the 2-arm fusion level
      instead of the 4-member level, mirroring exactly how F's own detection scalar
      x_F = mean(pct(xg), pct(xb4)) is built one level up from G's x(t) = mean(pct(members)).
k is then calibrated with p3_levers.calibrate(), UNCHANGED: the bisection for which the MEDIAN over
the 15 development patients (seed 42 only) of q_i(k) = 0.005. Gate: recalibrating G this way must
reproduce results/p3c_freeze/freeze.json's k exactly, or the run stops (proof the procedure was
applied correctly before trusting B4/F's k).

Budget/evaluation otherwise identical to V9-E1: top_i = clip(q_i(k_arm), 0.005, 0.02), D1 smoothing 5,
merge 90 s, kernel-CPD localizer (freeze.json's fixed choice) -- only k_arm and m_arm are now each
arm's own instead of all three sharing G's.

ONE SUBJECT PER PROCESS (same V9-T4 lesson, same reason -- B1-B4 feature build and the system-stage
k-sweep below are both heavier per-patient than a cache load): --eval-one SUBJ is meant to be run as
its own OS process, in subject order, one at a time, no multiprocessing.

Run:  python src/v9_e1b_calibrate.py --smoke                 (chb01, chb10, chb03; ~1-5 min)
      python src/v9_e1b_calibrate.py --calibrate              (k_G/k_B4/k_F from development; needs
                                                                 B1-B4 cache for the 15 dev patients)
      python src/v9_e1b_calibrate.py --eval-one SUBJ           (one subject, one process)
      python src/v9_e1b_calibrate.py --aggregate               (combine every --eval-one part file)
      python src/v9_e1b_calibrate.py --report                  (SUMMARY.md + inbox report from the
                                                                 aggregated CSVs; no recomputation)
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB", ROOT / "src" / "phaseC",
          ROOT / "src" / "dataprep"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import v9_e1_baselines as V9E1          # noqa: E402 -- read-only reuse, see module docstring
import p3_levers as P3L                 # noqa: E402
import e18_cpd_localizer as E18         # noqa: E402
import e16_recording_baseline as E16    # noqa: E402
import p2_scalars as PS                 # noqa: E402

OUT = ROOT / "results" / "v9_e1b"
PARTS = OUT / "_parts"
FRZ = ROOT / "results" / "p3c_freeze"
SIENA_ALL_14 = ["PN00", "PN01", "PN03", "PN05", "PN06", "PN07", "PN09", "PN10", "PN11", "PN12",
                "PN13", "PN14", "PN16", "PN17"]

# ---- runtime patch of V9-E1's own module constants (not a file edit -- see module docstring) ----
V9E1.EXT = ["chb24"] + SIENA_ALL_14
V9E1.SIENA_MISSING = []

DEV = V9E1.DEV
TEST = V9E1.TEST
TAGS = V9E1.TAGS
HEAD = "clean_seed42"
FLOOR, CAP, SMOOTH = 0.005, 0.02, 5
ARMS = ["G", "B4", "F"]
ARM_LABEL = {a: V9E1.ARM_LABEL[a] for a in ARMS}
ALL_SUBS = DEV + TEST + ["chb24"] + SIENA_ALL_14
SET_OF = {s: ("dev" if s in DEV else "test" if s in TEST else ("chb24" if s == "chb24" else "siena14"))
          for s in ALL_SUBS}
# system-stage k-sweep grid: 13 log-spaced multipliers of each arm's own calibrated k (same grid size
# as v9_e1_baselines.GRID, same "characterisation only" spirit -- not a gate).
K_MULT = [0.10, 0.20, 0.30, 0.40, 0.50, 0.65, 0.80, 1.00, 1.25, 1.60, 2.00, 3.00, 5.00]
FP_TARGETS = V9E1.FP_TARGETS


def _peak_ram_mb():
    import psutil
    mi = psutil.Process().memory_info()
    return getattr(mi, "peak_wset", mi.rss) / 1e6


def _native(o):
    if isinstance(o, dict):
        return {k: _native(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_native(v) for v in o]
    if isinstance(o, np.generic):
        return o.item()
    return o


def m_of(ctx, D):
    return V9E1.member_mean_z_from_D(ctx, D)


def x_of(ctx, D):
    return V9E1.final_scalar_from_D(ctx, D)


def f_signals(ctx, D_g, D_b4):
    """F's detection scalar and budget signal: the SAME transform-and-average pattern as G's own
    construction (pct-mean for x, rz-mean for m), one level up -- fusing xg/xb4 instead of 4 members."""
    xg, xb = x_of(ctx, D_g), x_of(ctx, D_b4)
    ok = ctx["ok"]
    xf = np.mean([PS.pct(xg, ok), PS.pct(xb, ok)], axis=0)
    mf = np.mean([E16.rz(xg, ok), E16.rz(xb, ok)], axis=0)
    return xf, mf


def one_pass(ctx, x, k, m, refs):
    """budget -> detector -> cpd localizer -> score, at the arm's OWN calibrated k; returns the row
    dicts (detector+localized) plus the matched onset/offset error rows. Mirrors v9_e1_baselines.
    evaluate_arm() exactly, just also returning det/pair so the localizer's own errors can be read."""
    q = P3L.q_of(PS.smoothed(ctx, m, SMOOTH), k)
    top = float(np.clip(q, FLOOR, max(CAP, FLOOR)))
    det = PS.d1_events(ctx, x, SMOOTH, top)
    thr = np.nanquantile(PS.smoothed(ctx, x, SMOOTH), 1 - top)
    loc, pair = P3L.localize(ctx, x, det, thr, "cpd")
    out = {}
    for st, ev in (("detector", det), ("localized", loc)):
        tp, fp, nr, h = PS.score(ctx, ev)
        kk, ns = PS.caught(PS.short_refs(ctx), ev)
        out[st] = dict(tp=tp, fp=fp, n_ref=nr, nonict_h=h, short_tp=kk, short_n=ns, top=top, q_raw=q)
    errs = [dict(onset_err=pair[(f_, h0, h1)][0] - ra, offset_err=pair[(f_, h0, h1)][1] - rb)
            for f_, ra, rb, h0, h1 in E18.match_errors(refs, det)]
    return out, det, loc, errs


def sys_sweep(ctx, x, m, k0, refs):
    """system-stage curve (step 4): sweep k itself (not top-p) around the arm's own calibrated k0,
    through the per-patient budget AND the cpd localizer every time -- characterisation only."""
    sm_m = PS.smoothed(ctx, m, SMOOTH)
    sm_x = PS.smoothed(ctx, x, SMOOTH)
    rows = []
    for mult in K_MULT:
        k = k0 * mult
        q = P3L.q_of(sm_m, k)
        top = float(np.clip(q, FLOOR, max(CAP, FLOOR)))
        det = PS.d1_events(ctx, x, SMOOTH, top)
        thr = np.nanquantile(sm_x, 1 - top)
        loc, _ = P3L.localize(ctx, x, det, thr, "cpd")
        tp, fp, nr, h = PS.score(ctx, loc)
        rows.append(dict(k_mult=mult, k=k, tp=tp, fp=fp, n_ref=nr, nonict_h=h))
    return rows


# ============================================================================ step 1: calibration
def calibrate():
    t0 = time.time()
    V9E1.repro_check_G()
    for s in DEV:
        V9E1.cache_D(s)
    mg_list, mb_list, mf_list = [], [], []
    for s in DEV:
        ctx = V9E1.subject_ctx(s)
        Dg = ctx["D"][HEAD]
        Db = V9E1.load_D(s, "B4")
        mg_list.append(PS.smoothed(ctx, m_of(ctx, Dg), SMOOTH))
        mb_list.append(PS.smoothed(ctx, m_of(ctx, Db), SMOOTH))
        _, mf_raw = f_signals(ctx, Dg, Db)
        mf_list.append(PS.smoothed(ctx, mf_raw, SMOOTH))
    k_g = P3L.calibrate(mg_list)
    k_b4 = P3L.calibrate(mb_list)
    k_f = P3L.calibrate(mf_list)
    ref_k = json.load(open(FRZ / "freeze.json"))["k"]
    if abs(k_g - ref_k) > 1e-4:
        raise SystemExit(f"STOP: recalibrated k_G {k_g:.6f} != freeze.json k {ref_k:.6f} -- the "
                          "calibrate() procedure must reproduce G's own committed k before B4/F's "
                          "k can be trusted.")
    cal = dict(k_G=k_g, k_B4=k_b4, k_F=k_f, floor=FLOOR, cap=CAP, smooth=SMOOTH, dev_n=len(DEV),
              elapsed_s=time.time() - t0)
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(cal, open(OUT / "calibration.json", "w"), indent=1)
    print(f"k_G  = {k_g:.6f}  (reproduces freeze.json's {ref_k:.6f})", flush=True)
    print(f"k_B4 = {k_b4:.6f}", flush=True)
    print(f"k_F  = {k_f:.6f}", flush=True)
    print(f"calibrate() done in {cal['elapsed_s']:.0f}s", flush=True)
    return cal


# ============================================================================ step 2: eval-one subject
def eval_one(s):
    t0 = time.time()
    cal = json.load(open(OUT / "calibration.json"))
    k_g, k_b4, k_f = cal["k_G"], cal["k_B4"], cal["k_F"]
    ctx = V9E1.subject_ctx(s)
    V9E1.cache_D(s)
    Db = V9E1.load_D(s, "B4")
    refs = P3L.refs_of(ctx)

    rows, sweep_rows, sys_rows, dur_rows, err_rows = [], [], [], [], []

    def record(arm, seed, x, m, k):
        out, det, loc, errs = one_pass(ctx, x, k, m, refs)
        for st, v in out.items():
            rows.append(dict(subject=s, arm=arm, seed=seed, stage=st, **v))
        for e in errs:
            err_rows.append(dict(subject=s, arm=arm, seed=seed, **e))
        for r_ in V9E1.sweep_detector(ctx, x, V9E1.GRID):
            sweep_rows.append(dict(subject=s, arm=arm, seed=seed, **r_))
        for r_ in sys_sweep(ctx, x, m, k, refs):
            sys_rows.append(dict(subject=s, arm=arm, seed=seed, **r_))
        bins = V9E1.duration_bins(ctx, loc)
        for (lo, hi), (caught, n) in bins.items():
            dur_rows.append(dict(subject=s, arm=arm, seed=seed, lo=lo, hi=hi, caught=caught, n=n))

    for tag in TAGS:
        Dg = ctx["D"][tag]
        record("G", tag, x_of(ctx, Dg), m_of(ctx, Dg), k_g)

    record("B4", "-", x_of(ctx, Db), m_of(ctx, Db), k_b4)

    for tag in TAGS:
        Dg = ctx["D"][tag]
        xf, mf = f_signals(ctx, Dg, Db)
        record("F", tag, xf, mf, k_f)

    PARTS.mkdir(parents=True, exist_ok=True)
    payload = _native(dict(rows=rows, sweep=sweep_rows, sys=sys_rows, dur=dur_rows, err=err_rows))
    (PARTS / f"{s}.json").write_text(json.dumps(payload), encoding="utf-8")
    print(f"eval-one {s}: done in {time.time() - t0:.0f}s, peak RAM {_peak_ram_mb():.0f} MB", flush=True)


# ============================================================================ step 3: aggregate
def aggregate():
    cal = json.load(open(OUT / "calibration.json"))
    parts = {}
    for s in ALL_SUBS:
        fp = PARTS / f"{s}.json"
        if not fp.exists():
            raise SystemExit(f"STOP: missing part file for {s} -- run --eval-one {s} first")
        parts[s] = json.loads(fp.read_text())

    rows = [r for s in ALL_SUBS for r in parts[s]["rows"]]
    sweep_rows = [r for s in ALL_SUBS for r in parts[s]["sweep"]]
    sys_rows = [r for s in ALL_SUBS for r in parts[s]["sys"]]
    err_rows = [r for s in ALL_SUBS for r in parts[s]["err"]]
    dur_rows = [dict(r, set=SET_OF[s]) for s in ALL_SUBS for r in parts[s]["dur"]]

    R = pd.DataFrame(rows)
    SW = pd.DataFrame(sweep_rows)
    SYS = pd.DataFrame(sys_rows)
    DB = pd.DataFrame(dur_rows)
    ERR = pd.DataFrame(err_rows)
    OUT.mkdir(parents=True, exist_ok=True)
    R.to_csv(OUT / "per_subject.csv", index=False)
    SW.to_csv(OUT / "sweep.csv", index=False)
    SYS.to_csv(OUT / "sys_sweep.csv", index=False)
    DB.to_csv(OUT / "duration_bins.csv", index=False)
    ERR.to_csv(OUT / "loc_errors.csv", index=False)

    V9E1.check_ext_repro(R)
    print(f"aggregate: {len(ALL_SUBS)} subjects combined -> {OUT}", flush=True)
    build_report(R, SW, SYS, DB, ERR, cal)


# ============================================================================ system-stage curve (by k, not top)
def matched_curve_k(SYS, subs, arm):
    d = SYS[(SYS.subject.isin(subs)) & (SYS.arm == arm)]
    if not len(d):
        return None
    out = {}
    for tag in sorted(d.seed.unique()):
        g = d[d.seed == tag].groupby("k_mult")[["tp", "fp", "n_ref", "nonict_h"]].sum().reset_index()
        g["sens"] = g.tp / g.n_ref
        g["fa"] = g.fp / g.nonict_h * 24
        pm = d[d.seed == tag].assign(se=lambda x: x.tp / x.n_ref, fd=lambda x: x.fp / x.nonict_h * 24)
        pm = pm.groupby("k_mult")[["se", "fd"]].mean().reset_index()
        g = g.merge(pm, on="k_mult").dropna(subset=["fa", "se"]).sort_values("fa")
        for t in FP_TARGETS:
            if len(g) < 2 or t < g.fa.min() or t > g.fa.max():
                out.setdefault(t, []).append(np.nan)
            else:
                out.setdefault(t, []).append(float(np.interp(t, g.fa, g.se)))
    return {t: (float(np.nanmean(v)), float(np.nanstd(v, ddof=1)) if len(v) > 1 else 0.0) for t, v in out.items()}


# ============================================================================ report
def write_set_section(L, R, SW, SYS, DB, ERR, subs, setname, title):
    summaries = {}
    L += [f"\n## {title} ({len(subs)} patients)\n",
          "### Each arm's OWN calibrated balanced point (floor 0.005 / cap 0.02, k per arm), after the CPD localizer\n",
          "```", "arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day"]
    for arm in ARMS:
        s = V9E1.arm_summary(R, subs, arm)
        summaries[arm] = s
        L.append(V9E1.fmt_arm_row(ARM_LABEL[arm], s))
    L.append("```")

    L += ["\n### Sensitivity by seizure duration bin (localized stage; headline seed 42 for G/F)\n", "```",
          "arm                                    <=20s      21-40s     41-80s     >80s"]
    for arm in ARMS:
        bins = V9E1.duration_table(DB, subs, arm, setname)
        if bins is None:
            L.append(f"{ARM_LABEL[arm]:38s} not available")
            continue
        cells = []
        for b in V9E1.DUR_BINS:
            c, n = bins.get(b, (0, 0))
            cells.append(f"{c}/{n}" if n else "-")
        L.append(f"{ARM_LABEL[arm]:38s} " + "  ".join(f"{c:9s}" for c in cells))
    L.append("```")

    L += ["\n### Patient bootstrap 95% CI for the per-patient-mean sensitivity (headline seed 42, B = 10,000)\n", "```"]
    for arm in ARMS:
        ci = V9E1.patient_mean_ci(R, subs, arm)
        if ci is None:
            L.append(f"{ARM_LABEL[arm]:38s} not available")
            continue
        L.append(f"{ARM_LABEL[arm]:38s} {ci[0]:.3f}  [{ci[1]:.3f}, {ci[2]:.3f}]")
    L.append("```")

    L += ["\n### Localizer onset/offset |error| (median seconds, pooled matched events, all seeds)\n", "```"]
    for arm in ARMS:
        e = ERR[(ERR.subject.isin(subs)) & (ERR.arm == arm)]
        if not len(e):
            L.append(f"{ARM_LABEL[arm]:38s} not available")
            continue
        _, on_s = P3L.err_stats(e, "onset_err")
        _, off_s = P3L.err_stats(e, "offset_err")
        L.append(f"{ARM_LABEL[arm]:38s} onset {on_s} | offset {off_s}")
    L.append("```")

    L += [f"\n### System-stage curve (sweep k, per-patient budget + CPD localizer every point): "
          f"per-patient-mean sensitivity @ FP/day {', '.join(str(t) for t in FP_TARGETS)}\n", "```"]
    for arm in ARMS:
        c = matched_curve_k(SYS, subs, arm)
        if c is None:
            L.append(f"{ARM_LABEL[arm]:38s} not available")
            continue
        L.append(f"{ARM_LABEL[arm]:38s} " + "  ".join(
            f"{t:.1f}:{c[t][0]:.3f}+-{c[t][1]:.3f}" if np.isfinite(c[t][0]) else f"{t:.1f}:NA" for t in FP_TARGETS))
    L.append("```")
    return summaries


def build_report(R, SW, SYS, DB, ERR, cal):
    L = ["# V9-E1b -- fair per-arm calibration of the per-patient budget, then one evaluation\n",
         "Full tables: `results/v9_e1b/*.csv`. Code: `src/v9_e1b_calibrate.py` (new; reuses "
         "src/v9_e1_baselines.py and every frozen script it calls, read-only; v9_e1_baselines.EXT/"
         "SIENA_MISSING are widened at runtime -- a module-attribute patch, not a file edit -- now "
         "that V9-T4 built the raw-feature cache for all 14 Siena patients).\n",
         f"k calibrated with `p3_levers.calibrate()` UNCHANGED (median over the 15 development patients, "
         f"seed 42, of q_i(k) = 0.005), applied to each arm's OWN per-patient budget signal: "
         f"k_G = {cal['k_G']:.6f} (reproduces freeze.json exactly), k_B4 = {cal['k_B4']:.6f}, "
         f"k_F = {cal['k_F']:.6f}. Same floor/cap for every arm (clip(q_i(k), 0.005, 0.02)), same "
         f"smoothing ({cal['smooth']}), same merge (90 s), same kernel-CPD localizer. Calibrated on "
         "development only -- nothing on CHB-MIT test, chb24 or Siena influenced k.\n",
         "Full detail of the calibration construction (B4's and F's own 'member mean z' budget signal, "
         "the natural generalisation of G's): see the module docstring of `src/v9_e1b_calibrate.py`.\n"]

    write_set_section(L, R, SW, SYS, DB, ERR, DEV, "dev", "Development (train + validation)")
    write_set_section(L, R, SW, SYS, DB, ERR, TEST, "test", "CHB-MIT held-out test")
    write_set_section(L, R, SW, SYS, DB, ERR, ["chb24"], "chb24", "chb24 (all 14 Siena + chb24 now fully recomputed)")
    write_set_section(L, R, SW, SYS, DB, ERR, SIENA_ALL_14, "siena14", "Siena, all 14 patients")

    L.append(f"\n## Runtime measured\ncalibrate(): {cal['elapsed_s']:.0f}s. Per-subject eval timing: see "
             "each --eval-one call's own stdout (printed elapsed seconds + peak RAM); every step is "
             "resumable (per-subject part file under results/v9_e1b/_parts/).")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "SUMMARY.md").write_text("\n".join(L), encoding="utf-8")
    inbox = ROOT.parent / "Agent" / "inbox" / "V9_E1B_REPORT.md"
    inbox.parent.mkdir(parents=True, exist_ok=True)
    inbox.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))
    print(f"\nWrote results/v9_e1b/SUMMARY.md and {inbox}")


# ============================================================================ smoke
def smoke():
    t0 = time.time()
    V9E1.repro_check_G()
    subs = ["chb01", "chb10", "chb03"]
    for s in subs:
        V9E1.cache_D(s)
    print(f"smoke: B1-B4 cache ready for {subs} ({time.time() - t0:.0f}s)", flush=True)
    # a tiny calibration using just these 3 patients, purely to exercise the code path (not the real k)
    mg_list, mb_list, mf_list = [], [], []
    for s in subs:
        ctx = V9E1.subject_ctx(s)
        Dg = ctx["D"][HEAD]
        Db = V9E1.load_D(s, "B4")
        mg_list.append(PS.smoothed(ctx, m_of(ctx, Dg), SMOOTH))
        mb_list.append(PS.smoothed(ctx, m_of(ctx, Db), SMOOTH))
        _, mf_raw = f_signals(ctx, Dg, Db)
        mf_list.append(PS.smoothed(ctx, mf_raw, SMOOTH))
    k_g, k_b4, k_f = P3L.calibrate(mg_list), P3L.calibrate(mb_list), P3L.calibrate(mf_list)
    print(f"smoke calibration (3 patients, NOT the real dev k): k_G={k_g:.4f} k_B4={k_b4:.4f} k_F={k_f:.4f}", flush=True)
    cal = dict(k_G=k_g, k_B4=k_b4, k_F=k_f, floor=FLOOR, cap=CAP, smooth=SMOOTH)
    smoke_out = OUT / "smoke"
    smoke_out.mkdir(parents=True, exist_ok=True)
    json.dump(cal, open(smoke_out / "calibration.json", "w"), indent=1)
    t1 = time.time()
    s0 = subs[0]
    ctx = V9E1.subject_ctx(s0)
    Dg, Db = ctx["D"][HEAD], V9E1.load_D(s0, "B4")
    refs = P3L.refs_of(ctx)
    one_pass(ctx, x_of(ctx, Dg), k_g, m_of(ctx, Dg), refs)
    one_pass(ctx, x_of(ctx, Db), k_b4, m_of(ctx, Db), refs)
    xf, mf = f_signals(ctx, Dg, Db)
    one_pass(ctx, xf, k_f, mf, refs)
    sys_rows = sys_sweep(ctx, x_of(ctx, Dg), m_of(ctx, Dg), k_g, refs)
    el = time.time() - t1
    n_full = len(DEV) + len(TEST) + 1 + len(SIENA_ALL_14)
    print(f"smoke: one subject's full eval (3 arms, {len(sys_rows)} k-grid points for G alone) took "
          f"{el:.0f}s -> projected total for --eval-one over all {n_full} subjects: "
          f"~{el * n_full / 60:.0f} min (characterisation only; per-subject cost varies with recording "
          "length and event count).", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--eval-one", metavar="SUBJ")
    ap.add_argument("--aggregate", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.smoke:
        smoke()
    elif a.calibrate:
        calibrate()
    elif a.eval_one:
        eval_one(a.eval_one)
    elif a.aggregate:
        aggregate()
    elif a.report:
        cal = json.load(open(OUT / "calibration.json"))
        R = pd.read_csv(OUT / "per_subject.csv")
        SW = pd.read_csv(OUT / "sweep.csv")
        SYS = pd.read_csv(OUT / "sys_sweep.csv")
        DB = pd.read_csv(OUT / "duration_bins.csv")
        ERR = pd.read_csv(OUT / "loc_errors.csv")
        build_report(R, SW, SYS, DB, ERR, cal)
    else:
        raise SystemExit("pass --smoke, --calibrate, --eval-one SUBJ, --aggregate or --report")


if __name__ == "__main__":
    main()
