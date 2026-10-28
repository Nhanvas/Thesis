#!/usr/bin/env python
"""
v9_e3_short.py -- V9-E3 (docs/prompts/V9_E3_SHORT_SEIZURE.md): short-seizure branch, multi-scale score.

WHY: seizures <= 20s are the main miss (CHB-MIT test 7/24 caught, G seed 42; similar B4/F --
results/v9_e2/). Likely cause: 4-s windows + the 5-window (20s) moving average dilute an 8-16s burst
before the per-patient budget ranks it. Development has only 3 seizures <= 20s -> S1 is NOT tuned on
development (every constant below is fixed from the mechanism, pre-registered); development is only
used for the label-free budget calibration (unchanged) and as the non-inferiority check.

WHERE THE FROZEN CHAIN SMOOTHS (checked against the code, not just the prose):
  x = v9_e1_baselines.final_scalar_from_D(ctx, D) (arm G) / v9_e1b_calibrate.f_signals(...)[0] (arm F)
      is the per-window ensemble score (percentile-mean of e17b_latent_family.member() order statistics
      for G; percentile-mean of pct(G),pct(B4) for F) -- NO temporal smoothing yet. This is "the frozen
      ensemble score per window, before smoothing" the prompt asks for.
  Smoothing (p2_scalars.smoothed, a per-file centred rolling mean, min_periods=1) first happens
  DOWNSTREAM of x, in two unrelated places: (a) p2_scalars.d1_events(), to build the detector's
  supra-threshold runs and its own quantile threshold; (b) p3_levers.q_of applied to a SEPARATE signal
  m(t) (member-mean-z), to size the per-patient budget top_i. Smoothing is NOT a single named stage --
  it is baked into d1_events' own internal call to p2_scalars.smoothed(). S1 therefore pre-smooths x
  itself (5 windows and 2 windows, the two branches), takes the max of their within-patient percentiles,
  and feeds the RESULT into d1_events with smooth=1 (a no-op: rolling window of width 1) so x is not
  smoothed a second time. The budget signal m(t) is untouched by S1 (same m, same k as V9-E1b) --
  nothing in the prompt's construction touches it, and recalibrating it with the SAME m reproduces the
  SAME k (checked below, --gate), so S1 reuses V9-E1b's k_G/k_F rather than re-deriving a new number
  that would necessarily come out identical.

S1 CONSTRUCTION (fixed now, both arms G and F):
  x_long  = p2_scalars.pct(p2_scalars.smoothed(ctx, x, 5), ok)    (the frozen path, unchanged)
  x_short = p2_scalars.pct(p2_scalars.smoothed(ctx, x, 2), ok)    (8s; the new branch)
  x_s1    = max(x_long, x_short) per window (elementwise)          (same p2_scalars.pct as the frozen
                                                                     chain uses everywhere else -- no
                                                                     new percentile code)
  budget: top_i = clip(q_i(k_arm), 0.005, 0.02), q_i from q_of(smoothed(m, 5), k_arm); k_arm = V9-E1b's
          own k_G / k_F (results/v9_e1b/calibration.json), reproduced here as a gate, not re-tuned.
  detector: p2_scalars.d1_events(ctx, x_s1, smooth=1, top_i)  (merge 90s is inside d1_events already)
  localizer: p3_levers.localize(ctx, x_s1, det, thr, "cpd")   (frozen kernel-CPD, unchanged)

S1 + VETO (only if results/v9_e2/selection.json exists): applies V9-E2's PRE-REGISTERED, UNCHANGED
  per-arm threshold to S1's own localized events. V9-E2 selected feature f5 = event duration, direction
  "low_is_fp" (short events are the artifact signal) -- label-free and raw-EEG-free (duration = offset -
  onset, no signal read needed), so this costs nothing extra. If a different feature were ever selected,
  the code falls back to v9_e2_veto.event_features() (raw EEG) for that feature only; disclosed via the
  `veto_fast_path` flag written into results/v9_e3/veto_info.json.

ADOPTION RULE (fixed in the prompt, per arm): S1 is adopted if (a) the paired bootstrap difference
  (S1 - no-S1) in per-patient-mean sensitivity at 27.5 FP/day on DEVELOPMENT has a 95% CI lower bound
  >= -0.05, AND (b) the pooled <=20s duration-bin caught-count over CHB-MIT test + chb24 + Siena-14
  increases (S1 > baseline, seed 42, using results/v9_e2/paired/duration_bins_seed42.csv as the
  already-seed42-only baseline -- v9_e1b's own duration_bins.csv sums G/F over 4 seeds, not comparable).

READ-ONLY REUSE: v9_e1_baselines.py / v9_e1b_calibrate.py (subject_ctx, cache_D, load_D,
final_scalar_from_D, member_mean_z_from_D, f_signals, m_of, x_of, arm_summary, fmt_arm_row,
duration_bins, duration_table, patient_mean_ci, boot_mean_ci, ARM_LABEL, DEV/TEST/SIENA_ALL_14/
ALL_SUBS/SET_OF/K_MULT/FP_TARGETS/TAGS), p2_scalars.py (smoothed, pct, d1_events, score, caught,
short_refs), p3_levers.py (q_of, calibrate, localize, refs_of, err_stats), e18_cpd_localizer.py
(match_errors), v9_e2_veto.py (per_patient_sens_at_fa, paired_boot, paired_f1_at_point, vetoed,
event_features -- fallback path only). Nothing in any of these files is modified.

Run:  python src/v9_e3_short.py --smoke                    (chb01, chb10, chb03; timing projection)
      python src/v9_e3_short.py --gate                      (reproduce k_G/k_F from v9_e1b; cheap)
      python src/v9_e3_short.py --eval-one SUBJ              (one subject, one process)
      python src/v9_e3_short.py --aggregate                   (combine parts, paired bootstrap, report)
      python src/v9_e3_short.py --report                       (rebuild report only, no recompute)
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
import v9_e1_baselines as V9E1          # noqa: E402 -- read-only reuse
import v9_e1b_calibrate as V9E1B        # noqa: E402
import v9_e2_veto as V9E2               # noqa: E402 -- read-only reuse (fallback veto path, bootstrap helpers)
import p2_scalars as PS                 # noqa: E402
import p3_levers as P3L                 # noqa: E402
import e18_cpd_localizer as E18         # noqa: E402

OUT = ROOT / "results" / "v9_e3"
PARTS = OUT / "_parts"
PAIRED = OUT / "paired"
E1B = ROOT / "results" / "v9_e1b"
E2 = ROOT / "results" / "v9_e2"

DEV = V9E1B.DEV
TEST = V9E1B.TEST
SIENA_ALL_14 = V9E1B.SIENA_ALL_14
ALL_SUBS = V9E1B.ALL_SUBS
SET_OF = V9E1B.SET_OF
TAGS = V9E1B.TAGS
HEAD = V9E1B.HEAD
K_MULT = V9E1B.K_MULT
FP_TARGETS = V9E1B.FP_TARGETS
FLOOR, CAP = V9E1B.FLOOR, V9E1B.CAP
SMOOTH_LONG, SMOOTH_SHORT, SMOOTH_BUDGET = 5, 2, 5
ARMS = ["G", "F"]
ARM_LABEL = {a: V9E1.ARM_LABEL[a] for a in ARMS}


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


# ============================================================================ S1 construction
def s1_score(ctx, x):
    ok = ctx["ok"]
    long_pct = PS.pct(PS.smoothed(ctx, x, SMOOTH_LONG), ok)
    short_pct = PS.pct(PS.smoothed(ctx, x, SMOOTH_SHORT), ok)
    return np.maximum(long_pct, short_pct)


def one_pass_s1(ctx, x, k, m, refs):
    """S1's analogue of v9_e1b_calibrate.one_pass: x_s1 already carries both branches' smoothing + the
    percentile max, so d1_events/thr use smooth=1 (identity) -- NOT a second smoothing pass. m (budget
    signal) and k are untouched by S1; same floor/cap/merge(90s, inside d1_events)/CPD localizer."""
    x_s1 = s1_score(ctx, x)
    q = P3L.q_of(PS.smoothed(ctx, m, SMOOTH_BUDGET), k)
    top = float(np.clip(q, FLOOR, max(CAP, FLOOR)))
    det = PS.d1_events(ctx, x_s1, 1, top)
    thr = np.nanquantile(PS.smoothed(ctx, x_s1, 1), 1 - top)
    loc, pair = P3L.localize(ctx, x_s1, det, thr, "cpd")
    out = {}
    for st, ev in (("detector", det), ("localized", loc)):
        tp, fp, nr, h = PS.score(ctx, ev)
        kk, ns = PS.caught(PS.short_refs(ctx), ev)
        out[st] = dict(tp=tp, fp=fp, n_ref=nr, nonict_h=h, short_tp=kk, short_n=ns, top=top, q_raw=q)
    errs = [dict(onset_err=pair[(f_, h0, h1)][0] - ra, offset_err=pair[(f_, h0, h1)][1] - rb)
            for f_, ra, rb, h0, h1 in E18.match_errors(refs, det)]
    return out, det, loc, errs, x_s1


def sys_sweep_s1(ctx, x, m, k0, refs):
    """system-stage curve: sweep k around the arm's own k0 (unchanged grid), through S1's budget +
    detector + CPD localizer every point. x_s1 itself does not depend on k (only top_i does)."""
    x_s1 = s1_score(ctx, x)
    sm_m = PS.smoothed(ctx, m, SMOOTH_BUDGET)
    sm_x = PS.smoothed(ctx, x_s1, 1)
    rows = []
    for mult in K_MULT:
        k = k0 * mult
        q = P3L.q_of(sm_m, k)
        top = float(np.clip(q, FLOOR, max(CAP, FLOOR)))
        det = PS.d1_events(ctx, x_s1, 1, top)
        thr = np.nanquantile(sm_x, 1 - top)
        loc, _ = P3L.localize(ctx, x_s1, det, thr, "cpd")
        tp, fp, nr, h = PS.score(ctx, loc)
        rows.append(dict(k_mult=mult, k=k, tp=tp, fp=fp, n_ref=nr, nonict_h=h))
    return rows


# ============================================================================ S1 + veto (cheap path: f5 = duration)
def load_veto_selection():
    fp = E2 / "selection.json"
    if not fp.exists():
        return None
    return json.load(open(fp))


def apply_veto_to_loc(ctx, s, setname, loc, sel, arm, files=None):
    """V9-E2's pre-registered, UNCHANGED per-arm threshold applied to S1's own localized events.
    feature f5 (event duration) needs no raw EEG (duration = offset - onset); any other feature falls
    back to v9_e2_veto.event_features() (disclosed via the caller's veto_fast_path flag)."""
    feat, direction = sel["feature"], sel["direction"]
    thr = sel["thresholds"].get(arm)
    if thr is None:
        return loc, True
    out = {}
    fast = feat == "f5"
    sd_uV = None if fast else V9E2.subject_sd_uV(s)
    for f, evs in loc.items():
        for a, b in evs:
            if fast:
                v = float(b - a)
            else:
                v = V9E2.event_features(s, setname, f, a, b, files, sd_uV)[feat]
            keep = not (v > thr if direction == "high_is_fp" else (np.isfinite(v) and v < thr))
            if keep:
                out.setdefault(f, []).append((a, b))
    return out, fast


# ============================================================================ step 0: gate (k_G/k_F reproduction)
def gate():
    """S1 does not retune the budget: m(t)/k are untouched by the long/short branches. Recalibrating
    with the SAME m reproduces the SAME k_G/k_F as v9_e1b/calibration.json -- checked here, STOP if not,
    exactly the reproduction-gate pattern used throughout this project."""
    t0 = time.time()
    cal_ref = json.load(open(E1B / "calibration.json"))
    V9E1.repro_check_G()
    for s in DEV:
        V9E1.cache_D(s)
    mg_list, mb_list, mf_list = [], [], []
    for s in DEV:
        ctx = V9E1.subject_ctx(s)
        Dg = ctx["D"][HEAD]
        Db = V9E1.load_D(s, "B4")
        mg_list.append(PS.smoothed(ctx, V9E1B.m_of(ctx, Dg), SMOOTH_BUDGET))
        mb_list.append(PS.smoothed(ctx, V9E1B.m_of(ctx, Db), SMOOTH_BUDGET))
        _, mf_raw = V9E1B.f_signals(ctx, Dg, Db)
        mf_list.append(PS.smoothed(ctx, mf_raw, SMOOTH_BUDGET))
    k_g = P3L.calibrate(mg_list)
    k_f = P3L.calibrate(mf_list)
    bad = []
    if abs(k_g - cal_ref["k_G"]) > 1e-4:
        bad.append(("k_G", k_g, cal_ref["k_G"]))
    if abs(k_f - cal_ref["k_F"]) > 1e-4:
        bad.append(("k_F", k_f, cal_ref["k_F"]))
    if bad:
        raise SystemExit(f"STOP: S1's budget signal m(t) is untouched, so recalibrating must reproduce "
                          f"v9_e1b/calibration.json exactly -- mismatch: {bad}")
    cal = dict(k_G=cal_ref["k_G"], k_F=cal_ref["k_F"], floor=FLOOR, cap=CAP, elapsed_s=time.time() - t0)
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(cal, open(OUT / "calibration.json", "w"), indent=1)
    print(f"gate OK: recalibrating on the SAME m(t) reproduces k_G={k_g:.6f}, k_F={k_f:.6f} "
          f"(v9_e1b/calibration.json) in {cal['elapsed_s']:.0f}s -- S1 reuses these k's unchanged.", flush=True)
    return cal


# ============================================================================ step 1: eval-one subject
def eval_one(s):
    t0 = time.time()
    cal = json.load(open(OUT / "calibration.json"))
    k_g, k_f = cal["k_G"], cal["k_F"]
    ctx = V9E1.subject_ctx(s)
    V9E1.cache_D(s)
    Db = V9E1.load_D(s, "B4")
    refs = P3L.refs_of(ctx)
    setname = SET_OF[s]
    files = ctx["z"]["files"] if "files" in ctx["z"] else None
    sel = load_veto_selection()
    fast_flags = []

    rows, sweep_rows, sys_rows, dur_rows, err_rows = [], [], [], [], []

    def record(arm, seed, x, m, k):
        out, det, loc, errs, _ = one_pass_s1(ctx, x, k, m, refs)
        for st, v in out.items():
            rows.append(dict(subject=s, arm=arm, seed=seed, variant="S1", stage=st, **v))
        for e in errs:
            err_rows.append(dict(subject=s, arm=arm, seed=seed, variant="S1", **e))
        for r_ in sys_sweep_s1(ctx, x, m, k, refs):
            sys_rows.append(dict(subject=s, arm=arm, seed=seed, variant="S1", **r_))
        bins = V9E1.duration_bins(ctx, loc)
        for (lo, hi), (caught, n) in bins.items():
            dur_rows.append(dict(subject=s, arm=arm, seed=seed, variant="S1", lo=lo, hi=hi, caught=caught, n=n))

        if sel is not None:
            loc_v, fast = apply_veto_to_loc(ctx, s, setname, loc, sel, arm, files)
            fast_flags.append(fast)
            tp, fp, nr, h = PS.score(ctx, loc_v)
            kk, ns = PS.caught(PS.short_refs(ctx), loc_v)
            rows.append(dict(subject=s, arm=arm, seed=seed, variant="S1_veto", stage="localized",
                             tp=tp, fp=fp, n_ref=nr, nonict_h=h, short_tp=kk, short_n=ns,
                             top=out["localized"]["top"], q_raw=out["localized"]["q_raw"]))
            bins_v = V9E1.duration_bins(ctx, loc_v)
            for (lo, hi), (caught, n) in bins_v.items():
                dur_rows.append(dict(subject=s, arm=arm, seed=seed, variant="S1_veto", lo=lo, hi=hi,
                                     caught=caught, n=n))

    for tag in TAGS:
        Dg = ctx["D"][tag]
        record("G", tag, V9E1B.x_of(ctx, Dg), V9E1B.m_of(ctx, Dg), k_g)

    for tag in TAGS:
        Dg = ctx["D"][tag]
        xf, mf = V9E1B.f_signals(ctx, Dg, Db)
        record("F", tag, xf, mf, k_f)

    PARTS.mkdir(parents=True, exist_ok=True)
    payload = _native(dict(rows=rows, sweep=sweep_rows, sys=sys_rows, dur=dur_rows, err=err_rows,
                           veto_fast_path=all(fast_flags) if fast_flags else None))
    (PARTS / f"{s}.json").write_text(json.dumps(payload), encoding="utf-8")
    print(f"eval-one {s}: done in {time.time() - t0:.0f}s, peak RAM {_peak_ram_mb():.0f} MB", flush=True)


# ============================================================================ step 2: aggregate
def aggregate():
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
    fast_flags = [parts[s]["veto_fast_path"] for s in ALL_SUBS if parts[s]["veto_fast_path"] is not None]

    R = pd.DataFrame(rows)
    SYS = pd.DataFrame(sys_rows)
    DB = pd.DataFrame(dur_rows)
    ERR = pd.DataFrame(err_rows)
    OUT.mkdir(parents=True, exist_ok=True)
    R.to_csv(OUT / "per_subject.csv", index=False)
    pd.DataFrame(sweep_rows).to_csv(OUT / "sweep.csv", index=False)
    SYS.to_csv(OUT / "sys_sweep.csv", index=False)
    DB.to_csv(OUT / "duration_bins.csv", index=False)
    ERR.to_csv(OUT / "loc_errors.csv", index=False)
    if fast_flags:
        json.dump(dict(veto_fast_path_every_subject=bool(all(fast_flags)), feature=load_veto_selection()["feature"]),
                  open(OUT / "veto_info.json", "w"), indent=1)

    paired = paired_stats(R, SYS)
    print(f"aggregate: {len(ALL_SUBS)} subjects combined -> {OUT}", flush=True)
    build_report(R, SYS, DB, ERR, paired)


# ============================================================================ paired bootstrap vs no-S1 baseline
def paired_stats(R, SYS):
    """S1 vs the SAME arm's own V9-E1b baseline (no short branch): per-patient-mean sensitivity diff at
    matched FP/day (system-stage curve), and per-patient-mean F1 diff at the arm's own calibrated point."""
    SYS_base = pd.read_csv(E1B / "sys_sweep.csv")
    R_base = pd.read_csv(E1B / "per_subject.csv")
    PAIRED.mkdir(parents=True, exist_ok=True)

    sens_rows = []
    for setname, subs in (("dev", DEV), ("test", TEST), ("siena14", SIENA_ALL_14)):
        for arm in ARMS:
            for t in FP_TARGETS:
                s1_sens = V9E2.per_patient_sens_at_fa(SYS, subs, arm, t)
                base_sens = V9E2.per_patient_sens_at_fa(SYS_base, subs, arm, t)
                if not len(s1_sens) or not len(base_sens):
                    sens_rows.append(dict(set=setname, arm=arm, fa_target=t, mean_diff=np.nan,
                                          ci_lo=np.nan, ci_hi=np.nan, share_gt0=np.nan, n_patients=0))
                    continue
                r = V9E2.paired_boot(s1_sens, base_sens)
                sens_rows.append(dict(set=setname, arm=arm, fa_target=t, **r))
    SENS = pd.DataFrame(sens_rows)
    SENS.to_csv(PAIRED / "paired_sens.csv", index=False)

    R_s1 = R[R.variant == "S1"]
    f1_rows = []
    for setname, subs in (("dev", DEV), ("test", TEST), ("siena14", SIENA_ALL_14)):
        for arm in ARMS:
            s1_f1 = V9E2.paired_f1_at_point(R_s1, subs, arm, headline=HEAD)
            base_f1 = V9E2.paired_f1_at_point(R_base, subs, arm, headline=HEAD)
            r = V9E2.paired_boot(s1_f1, base_f1)
            f1_rows.append(dict(set=setname, arm=arm, **r))
    F1 = pd.DataFrame(f1_rows)
    F1.to_csv(PAIRED / "paired_f1.csv", index=False)
    return dict(sens=SENS, f1=F1)


def adoption_verdict(SENS, DB):
    """fixed adoption rule: dev paired sens diff @ 27.5 FP/day CI lower bound >= -0.05 AND the pooled
    <=20s duration-bin caught count over test+chb24+siena14 increases vs the seed42-only baseline."""
    base_db = pd.read_csv(E2 / "paired" / "duration_bins_seed42.csv") if (E2 / "paired" / "duration_bins_seed42.csv").exists() else None
    verdicts = {}
    for arm in ARMS:
        r = SENS[(SENS.set == "dev") & (SENS.arm == arm) & (SENS.fa_target == 27.5)]
        non_inferior = bool(len(r) and np.isfinite(r.iloc[0].ci_lo) and r.iloc[0].ci_lo >= -0.05)
        s1_le20 = DB[(DB.arm == arm) & (DB.variant == "S1") & (DB.seed == HEAD) &
                    (DB.set.isin(["test", "chb24", "siena14"])) & (DB.lo == 0) & (DB.hi == 20)]
        s1_caught = int(s1_le20.caught.sum())
        if base_db is not None:
            b = base_db[(base_db.arm == arm) & (base_db.set.isin(["test", "chb24", "siena14"])) &
                       (base_db.lo == 0) & (base_db.hi == 20)]
            base_caught = int(b.caught.sum())
        else:
            base_caught = None
        le20_increase = bool(base_caught is not None and s1_caught > base_caught)
        adopted = bool(non_inferior and le20_increase)
        verdicts[arm] = dict(non_inferior=non_inferior, ci_lo=float(r.iloc[0].ci_lo) if len(r) else np.nan,
                             s1_le20_caught=s1_caught, base_le20_caught=base_caught,
                             le20_increase=le20_increase, adopted=adopted)
    return verdicts


# ============================================================================ report
def fmt_dur_table(DB, setname, variant):
    L = ["```", "arm                                    <=20s      21-40s     41-80s     >80s"]
    for arm in ARMS:
        d = DB[(DB.set == setname) & (DB.arm == arm) & (DB.variant == variant) & (DB.seed == HEAD)]
        g = d.groupby(["lo", "hi"])[["caught", "n"]].sum()
        cells = []
        for lo, hi in V9E1.DUR_BINS:
            if (lo, hi) in g.index:
                r = g.loc[(lo, hi)]
                cells.append(f"{int(r.caught)}/{int(r.n)}" if r.n else "-")
            else:
                cells.append("-")
        L.append(f"{ARM_LABEL[arm]:38s} " + "  ".join(f"{c:9s}" for c in cells))
    L.append("```")
    return L


def fmt_paired_table(df, label, extra_col=None):
    L = [f"\n{label}\n```"]
    for _, r in df.iterrows():
        extra = f"{extra_col}={r[extra_col]:g} " if extra_col else ""
        L.append(f"{r.set:10s} {r.arm:4s} {extra}mean diff {r.mean_diff:+.3f}  95% CI "
                 f"[{r.ci_lo:+.3f}, {r.ci_hi:+.3f}]  P(diff>0) {r.share_gt0:.3f}  (n={r.n_patients})")
    L.append("```")
    return L


def section(L, R, DB, subs, setname, title):
    L.append(f"\n## {title} ({len(subs)} patients)\n")
    for variant, label in (("S1", "S1 (multi-scale max fusion)"), ("S1_veto", "S1 + veto (V9-E2 threshold, unchanged)")):
        d = R[(R.subject.isin(subs)) & (R.variant == variant) & (R.stage == "localized")]
        if not len(d):
            continue
        L += [f"\n### {label}\n", "```",
             "arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day"]
        for arm in ARMS:
            s = V9E1.arm_summary(d, subs, arm)
            L.append(V9E1.fmt_arm_row(ARM_LABEL[arm], s))
        L.append("```")
    L.append("\n### Sensitivity by seizure duration bin, S1, seed 42 (E1 overlap rule)\n")
    L += fmt_dur_table(DB, setname, "S1")
    if (DB.variant == "S1_veto").any():
        L.append("\n### Sensitivity by seizure duration bin, S1 + veto, seed 42\n")
        L += fmt_dur_table(DB, setname, "S1_veto")


def build_report(R, SYS, DB, ERR, paired):
    has_veto = (R.variant == "S1_veto").any()
    verdicts = adoption_verdict(paired["sens"], DB) if (E2 / "paired" / "duration_bins_seed42.csv").exists() else None
    veto_info_fp = OUT / "veto_info.json"
    veto_info = json.load(open(veto_info_fp)) if veto_info_fp.exists() else None

    L = ["# V9-E3 -- short-seizure branch (multi-scale score)\n",
         "Full tables: `results/v9_e3/*.csv`, `results/v9_e3/paired/*.csv`. Code: `src/v9_e3_short.py` "
         "(new; reuses src/v9_e1_baselines.py, src/v9_e1b_calibrate.py, src/p3_levers.py, "
         "src/p2_scalars.py, src/e18_cpd_localizer.py and (for the veto fast path) src/v9_e2_veto.py, "
         "all read-only).\n",
         "S1 = max(pct(smoothed(x,5)), pct(smoothed(x,2))) per window, x = the frozen ensemble score "
         "before any smoothing (v9_e1_baselines.final_scalar_from_D for G, v9_e1b_calibrate.f_signals "
         "for F); fed into the SAME budget (k_G/k_F reused unchanged from v9_e1b, reproduction gated "
         "below), merge 90s, kernel-CPD localizer. See the module docstring of src/v9_e3_short.py for "
         "exactly where smoothing happens in the frozen chain and why S1 uses smooth=1 downstream of "
         "its own two-branch smoothing (no double smoothing).\n"]

    cal = json.load(open(OUT / "calibration.json")) if (OUT / "calibration.json").exists() else None
    if cal is not None:
        L.append(f"Gate: recalibrating on the SAME budget signal m(t) reproduces k_G = {cal['k_G']:.6f}, "
                 f"k_F = {cal['k_F']:.6f} (results/v9_e1b/calibration.json) exactly -- S1 does not retune "
                 "the budget, only the detection scalar x.\n")

    if veto_info is not None:
        L.append(f"S1 + veto: V9-E2's selected feature is **{veto_info['feature']}**"
                 f"{' (event duration -- no raw EEG needed; applied directly to S1 own event boundaries)' if veto_info['feature'] == 'f5' else ''}"
                 f", threshold unchanged, fast path used for every subject: {veto_info['veto_fast_path_every_subject']}.\n")
    elif not has_veto:
        L.append("S1 + veto: `results/v9_e2/selection.json` not found when `--eval-one` ran -- not reported.\n")

    section(L, R, DB, DEV, "dev", "Development")
    section(L, R, DB, TEST, "test", "CHB-MIT held-out test")
    section(L, R, DB, ["chb24"], "chb24", "chb24")
    section(L, R, DB, SIENA_ALL_14, "siena14", "Siena, all 14 patients")

    L += fmt_paired_table(paired["sens"], "## Paired bootstrap (B=10,000): per-patient-mean sensitivity "
                          "difference, S1 minus the SAME arm WITHOUT the short branch (system-stage "
                          "curve, matched FP/day)", extra_col="fa_target")
    L += fmt_paired_table(paired["f1"], "## Paired bootstrap (B=10,000): per-patient-mean F1 difference, "
                          "S1 minus no-S1, each arm's OWN calibrated point")

    L.append("\n### Localizer onset/offset |error| (median seconds, pooled matched events, all seeds, S1)\n")
    L.append("```")
    for arm in ARMS:
        e = ERR[(ERR.arm == arm) & (ERR.variant == "S1")]
        if not len(e):
            L.append(f"{ARM_LABEL[arm]:38s} not available")
            continue
        _, on_s = P3L.err_stats(e, "onset_err")
        _, off_s = P3L.err_stats(e, "offset_err")
        L.append(f"{ARM_LABEL[arm]:38s} onset {on_s} | offset {off_s}")
    L.append("```")

    L.append("\n## Adoption verdict (fixed rule: dev paired-sens-diff @ 27.5 FP/day 95% CI lower bound "
             ">= -0.05 AND pooled test+chb24+Siena-14 <=20s detections increase vs the no-S1 seed42 "
             "baseline)\n")
    if verdicts is None:
        L.append("results/v9_e2/paired/duration_bins_seed42.csv not found -- cannot score the <=20s "
                 "half of the rule; verdict withheld.")
    else:
        for arm in ARMS:
            v = verdicts[arm]
            L.append(f"- {ARM_LABEL[arm]}: dev sens-diff CI lower bound {v['ci_lo']:+.3f} "
                     f"({'pass' if v['non_inferior'] else 'FAIL'} >= -0.05); pooled <=20s caught "
                     f"{v['s1_le20_caught']} (S1) vs {v['base_le20_caught']} (no-S1) "
                     f"({'pass' if v['le20_increase'] else 'FAIL'} increase) "
                     f"-> **{'ADOPTED' if v['adopted'] else 'NOT adopted'}**")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "SUMMARY.md").write_text("\n".join(L), encoding="utf-8")
    inbox = ROOT.parent / "Agent" / "inbox" / "V9_E3_REPORT.md"
    inbox.parent.mkdir(parents=True, exist_ok=True)
    inbox.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))
    print(f"\nWrote results/v9_e3/SUMMARY.md and {inbox}")


# ============================================================================ smoke
def smoke():
    t0 = time.time()
    cal_ref = json.load(open(E1B / "calibration.json"))
    for s in ["chb01", "chb10", "chb03"]:
        ctx = V9E1.subject_ctx(s)
        V9E1.cache_D(s)
        Db = V9E1.load_D(s, "B4")
        refs = P3L.refs_of(ctx)
        Dg = ctx["D"][HEAD]
        out, det, loc, errs, x_s1 = one_pass_s1(ctx, V9E1B.x_of(ctx, Dg), cal_ref["k_G"], V9E1B.m_of(ctx, Dg), refs)
        xf, mf = V9E1B.f_signals(ctx, Dg, Db)
        one_pass_s1(ctx, xf, cal_ref["k_F"], mf, refs)
        sys_sweep_s1(ctx, V9E1B.x_of(ctx, Dg), V9E1B.m_of(ctx, Dg), cal_ref["k_G"], refs)
        print(f"  {s}: G localized tp/fp = {out['localized']['tp']}/{out['localized']['fp']} "
              f"(frozen-no-S1 reference available in results/v9_e1b/per_subject.csv)", flush=True)
    el = time.time() - t0
    n_full = len(ALL_SUBS)
    print(f"smoke done in {el:.0f}s (3 subjects, 2 arms x 4 seeds each) -> projected total for "
         f"--eval-one over all {n_full} subjects: ~{el / 3 * n_full / 60:.0f} min "
         "(characterisation only; no raw-EEG decoding needed -- D is already cached for every subject).",
         flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--eval-one", metavar="SUBJ")
    ap.add_argument("--aggregate", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.smoke:
        smoke()
    elif a.gate:
        gate()
    elif a.eval_one:
        eval_one(a.eval_one)
    elif a.aggregate:
        aggregate()
    elif a.report:
        R = pd.read_csv(OUT / "per_subject.csv")
        SYS = pd.read_csv(OUT / "sys_sweep.csv")
        DB = pd.read_csv(OUT / "duration_bins.csv")
        ERR = pd.read_csv(OUT / "loc_errors.csv")
        paired = dict(sens=pd.read_csv(PAIRED / "paired_sens.csv"), f1=pd.read_csv(PAIRED / "paired_f1.csv"))
        build_report(R, SYS, DB, ERR, paired)
    else:
        raise SystemExit("pass --smoke, --gate, --eval-one SUBJ, --aggregate or --report")


if __name__ == "__main__":
    main()
