#!/usr/bin/env python
"""
v9_e4_knn24.py -- V9-E4 (docs/prompts/V9_E4_KNN24.md): B4 (12 per-channel node features -> per-patient
kNN distance) evaluated on every CHB-MIT case, chb01-chb24 (24 cases; chb21 is the same subject as
chb01, recorded 1.5 years later).

WHY: B4 has no trained component -- every fit (robust-z, kNN index) is per patient and label-free; only
its budget constant k_B4 came from the 15 development patients (results/v9_e1b, V9-E1b). It can
therefore be scored on all 24 cases, a larger sample than the 8 CHB-MIT test patients used by V9-E1/
V9-E1b, giving a per-patient picture of which cases are hard for this baseline.

READ-ONLY REUSE: src/v9_e1_baselines.py (V9-E1's own code) for subject_ctx / cache_D / load_D /
final_scalar_from_D / member_mean_z_from_D / sweep_detector / duration_bins / boot_mean_ci /
arm_summary / fmt_arm_row / patient_mean_ci / check_ext_repro / repro_check_G / DEV / TEST / DUR_BINS /
FP_TARGETS -- none of these needed editing (arm_summary/fmt_arm_row/patient_mean_ci are generic over a
column named "arm"; this script's "arm" values are "loo" and "fixed_dev", never "G"/"F", so they take
the single-row metrics path unchanged). src/v9_e1b_calibrate.py for matched_curve_k (the system-stage
curve helper, generic over "arm"+"seed"+"k_mult"; this script's rows carry a constant seed="-", matching
B4's own single-pass seed slot in v9_e1_baselines). src/p3_levers.py for calibrate() (the bisection
itself, UNCHANGED), q_of, refs_of, localize, err_stats. src/e18_cpd_localizer.py for match_errors.

B4's construction (unchanged from V9-E1/V9-E1b): 12 raw per-channel features (bp5 5 + f7 7), robust-z'd
per channel per patient (label-free), Euclidean distance to the 10th nearest neighbour in a random
20000-window subsample of the same patient (|time offset| > 60 s excluded), random_state=42 -- cached
once per subject in results/v9_e1/cache/<subj>.npz (b4 array; already built for all 24 CHB-MIT cases by
V9-E1/V9-E1b, reused here as a pure cache load, no new feature extraction). Downstream: e17b order
statistics (6/9/12 + channel mean) -> percentile-mean final scalar (x) and rz-mean member signal (m,
v9_e1_baselines.member_mean_z_from_D) -> D1 smoothing 5 -> per-patient budget clip(q_i(k), 0.005, 0.02)
-> merge 90 s (PS.d1_events) -> kernel-CPD localizer (P3L.localize, mode "cpd") -> SzCORE scorer.

CALIBRATION, two variants, both reported:
  loo        leave-one-case-out k_B4: for case s, k_B4(s) = p3_levers.calibrate() on the smoothed m(t) of
             every OTHER case, UNCHANGED (median q_i(k) = 0.005). chb01 and chb21 are the same subject
             (recorded 1.5 years apart): whichever of the two is being evaluated, BOTH chb01 and chb21
             are excluded from its calibration set (never calibrate each other), so case s's calibration
             set is 22 cases when s in {chb01, chb21}, 23 cases otherwise.
  fixed_dev  k_B4 = 11.618332922327152, results/v9_e1b/calibration.json's value (calibrated once on the
             15 development patients only, seed 42; V9-E1b) -- loaded verbatim, not recomputed, reported
             for reference per the prompt.
Same floor/cap (clip(q_i(k), 0.005, 0.02)), smoothing (5), merge (90 s) and localizer (cpd) for both.

ONE SUBJECT PER PROCESS (same V9-T4/V9-E1b lesson): --prep SUBJ (build the case's own smoothed m(t), the
only thing the leave-one-out calibration needs from a full per-subject context) and --eval-one SUBJ (the
full detector+localizer+score pass, at both k variants, plus the system-stage k-sweep) are each meant to
run as their own OS process, in subject order, one at a time, no multiprocessing. --prep is needed
because leave-one-out calibration requires every OTHER case's m(t) signal before any case's own k is
known; --calibrate itself (reading the 24 small cached arrays and running 24 independent bisections) is
cheap and single-process.

"Hard patient" (step 5 of the prompt, definition fixed from the literature exclusion rule already used
in V9-E1 Part C, Clin Exp Pediatr 2026 DOI 10.3345/cep.2026.01011): mean seizure duration < 30 s. Listed
per case from the case's own reference seizures (annotation-derived, same as every tp/ref/sensitivity
number in this report); not label-free, and not a gate -- descriptive, with a two-sided Mann-Whitney U
on per-case sensitivity (loo, localized) between the hard and the other cases.

Run:  python src/v9_e4_knn24.py --smoke                  (chb01, chb10, chb03; ~1-5 min, not measured)
      python src/v9_e4_knn24.py --prep SUBJ                (one case's own process; needs its own ctx)
      python src/v9_e4_knn24.py --calibrate                (24 leave-one-out k's + the fixed dev k;
                                                               needs every case's --prep done first)
      python src/v9_e4_knn24.py --eval-one SUBJ             (one case, one process; needs --calibrate)
      python src/v9_e4_knn24.py --aggregate                 (combine every --eval-one part file)
      python src/v9_e4_knn24.py --report                    (SUMMARY.md + inbox report; no recomputation)
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB", ROOT / "src" / "phaseC",
          ROOT / "src" / "dataprep"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import v9_e1_baselines as V9E1          # noqa: E402 -- read-only reuse, see module docstring
import v9_e1b_calibrate as V9E1B        # noqa: E402 -- read-only reuse (matched_curve_k only)
import p3_levers as P3L                 # noqa: E402
import e18_cpd_localizer as E18         # noqa: E402
import e22_test_oneshot as E22          # noqa: E402
import p2_scalars as PS                 # noqa: E402

OUT = ROOT / "results" / "v9_e4"
PARTS = OUT / "_parts"
MDIR = OUT / "_m"
E1B_CAL = ROOT / "results" / "v9_e1b" / "calibration.json"

ALL24 = [f"chb{i:02d}" for i in range(1, 25)]
FORMER_DEV = list(V9E1.DEV)
FORMER_TEST = list(V9E1.TEST)
SAME_SUBJECT = {"chb01", "chb21"}       # chb21 recorded 1.5 y after chb01, same patient
SET_OF = {s: ("dev" if s in FORMER_DEV else "test" if s in FORMER_TEST else "chb24") for s in ALL24}
FLOOR, CAP, SMOOTH = 0.005, 0.02, 5
ARMS = ["loo", "fixed_dev"]
ARM_LABEL = {"loo": "B4, leave-one-case-out k", "fixed_dev": "B4, fixed dev-15 k (reference)"}
K_MULT = V9E1B.K_MULT                   # 13 log-spaced multipliers around each case's own k
FP_TARGETS = V9E1.FP_TARGETS
DUR_BINS = V9E1.DUR_BINS
HARD_DUR_S = 30.0


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


def seizure_stats(refs):
    durs = [b - a for rr in refs.values() for a, b in rr]
    n = len(durs)
    return dict(n_sz=n, med_dur=float(np.median(durs)) if n else float("nan"),
               mean_dur=float(np.mean(durs)) if n else float("nan"))


def one_pass(ctx, x, k, m, refs):
    """budget -> detector -> cpd localizer -> score, at this case's own k. Mirrors
    v9_e1b_calibrate.one_pass exactly (same frozen downstream chain, B4 only)."""
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
    """system-stage curve (step 4): sweep k itself around this case's own k0, through the per-patient
    budget AND the cpd localizer every time -- characterisation only. Same grid as v9_e1b."""
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


# ============================================================================ step 1: prep (one subject)
def prep(s):
    t0 = time.time()
    ctx = V9E1.subject_ctx(s)
    V9E1.cache_D(s)
    D = V9E1.load_D(s, "B4")
    m = PS.smoothed(ctx, m_of(ctx, D), SMOOTH)
    MDIR.mkdir(parents=True, exist_ok=True)
    np.save(MDIR / f"{s}.npy", m)
    print(f"prep {s}: m-signal cached ({len(m)} windows, {time.time()-t0:.0f}s)", flush=True)


# ============================================================================ step 2: calibrate
def calibrate():
    t0 = time.time()
    V9E1.repro_check_G()
    ms = {}
    for s in ALL24:
        fp = MDIR / f"{s}.npy"
        if not fp.exists():
            raise SystemExit(f"STOP: missing m-signal cache for {s} -- run --prep {s} first")
        ms[s] = np.load(fp)
    k_loo = {}
    for s in ALL24:
        excl = {s} | (SAME_SUBJECT if s in SAME_SUBJECT else set())
        calib_set = [ms[t] for t in ALL24 if t not in excl]
        k_loo[s] = P3L.calibrate(calib_set)
        print(f"  k_B4(loo, {s}) = {k_loo[s]:.6f}  ({len(calib_set)} other cases)", flush=True)
    k_fixed = json.load(open(E1B_CAL))["k_B4"]
    cal = dict(k_loo=k_loo, k_fixed_dev=k_fixed, floor=FLOOR, cap=CAP, smooth=SMOOTH,
              elapsed_s=time.time() - t0)
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(cal, open(OUT / "calibration.json", "w"), indent=1)
    print(f"k_B4 fixed (dev-15, results/v9_e1b) = {k_fixed:.6f}", flush=True)
    print(f"calibrate() done in {cal['elapsed_s']:.0f}s", flush=True)
    return cal


# ============================================================================ step 3: eval-one subject
def eval_one(s):
    t0 = time.time()
    cal = json.load(open(OUT / "calibration.json"))
    k_loo, k_fixed = cal["k_loo"][s], cal["k_fixed_dev"]
    ctx = V9E1.subject_ctx(s)
    V9E1.cache_D(s)
    D = V9E1.load_D(s, "B4")
    refs = P3L.refs_of(ctx)
    x, m = x_of(ctx, D), m_of(ctx, D)

    rows, sys_rows, dur_rows, err_rows = [], [], [], []

    def record(arm, k):
        out, det, loc, errs = one_pass(ctx, x, k, m, refs)
        for st, v in out.items():
            rows.append(dict(subject=s, arm=arm, seed="-", stage=st, **v))
        for e in errs:
            err_rows.append(dict(subject=s, arm=arm, **e))
        for r_ in sys_sweep(ctx, x, m, k, refs):
            sys_rows.append(dict(subject=s, arm=arm, seed="-", **r_))
        bins = V9E1.duration_bins(ctx, loc)
        for (lo, hi), (caught, n) in bins.items():
            dur_rows.append(dict(subject=s, arm=arm, lo=lo, hi=hi, caught=caught, n=n))

    record("loo", k_loo)
    record("fixed_dev", k_fixed)

    PARTS.mkdir(parents=True, exist_ok=True)
    payload = _native(dict(rows=rows, sys=sys_rows, dur=dur_rows, err=err_rows, sz=seizure_stats(refs)))
    (PARTS / f"{s}.json").write_text(json.dumps(payload), encoding="utf-8")
    print(f"eval-one {s}: done in {time.time() - t0:.0f}s, peak RAM {_peak_ram_mb():.0f} MB", flush=True)


# ============================================================================ step 4: aggregate
def aggregate():
    cal = json.load(open(OUT / "calibration.json"))
    parts = {}
    for s in ALL24:
        fp = PARTS / f"{s}.json"
        if not fp.exists():
            raise SystemExit(f"STOP: missing part file for {s} -- run --eval-one {s} first")
        parts[s] = json.loads(fp.read_text())

    rows = [r for s in ALL24 for r in parts[s]["rows"]]
    sys_rows = [r for s in ALL24 for r in parts[s]["sys"]]
    err_rows = [r for s in ALL24 for r in parts[s]["err"]]
    dur_rows = [dict(r, set=SET_OF[s]) for s in ALL24 for r in parts[s]["dur"]]
    sz_rows = [dict(subject=s, set=SET_OF[s], **parts[s]["sz"]) for s in ALL24]

    R = pd.DataFrame(rows)
    SYS = pd.DataFrame(sys_rows)
    DB = pd.DataFrame(dur_rows)
    ERR = pd.DataFrame(err_rows)
    SZ = pd.DataFrame(sz_rows)
    SZ["hard"] = SZ.mean_dur < HARD_DUR_S
    OUT.mkdir(parents=True, exist_ok=True)
    R.to_csv(OUT / "per_subject.csv", index=False)
    SYS.to_csv(OUT / "sys_sweep.csv", index=False)
    DB.to_csv(OUT / "duration_bins.csv", index=False)
    ERR.to_csv(OUT / "loc_errors.csv", index=False)
    SZ.to_csv(OUT / "seizure_stats.csv", index=False)
    print(f"aggregate: {len(ALL24)} cases combined -> {OUT}", flush=True)
    build_report(R, SYS, DB, ERR, SZ, cal)


# ============================================================================ aggregate-group helpers
def duration_table(DB, subs, arm):
    d = DB[(DB.subject.isin(subs)) & (DB.arm == arm)]
    if not len(d):
        return None
    g = d.groupby(["lo", "hi"])[["caught", "n"]].sum()
    return {(lo, hi): (int(r.caught), int(r.n)) for (lo, hi), r in g.iterrows()}


def write_group_section(L, R, SYS, DB, ERR, subs, title):
    L += [f"\n## {title} ({len(subs)} cases)\n",
          "### Each k variant's balanced point (floor 0.005 / cap 0.02), after the CPD localizer\n",
          "```", "arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day"]
    summaries = {}
    for arm in ARMS:
        s = V9E1.arm_summary(R, subs, arm)
        summaries[arm] = s
        L.append(V9E1.fmt_arm_row(ARM_LABEL[arm], s))
    L.append("```")

    L += ["\n### Sensitivity by seizure duration bin (localized stage)\n", "```",
          "arm                                    <=20s      21-40s     41-80s     >80s"]
    for arm in ARMS:
        bins = duration_table(DB, subs, arm)
        if bins is None:
            L.append(f"{ARM_LABEL[arm]:38s} not available")
            continue
        cells = []
        for b in DUR_BINS:
            c, n = bins.get(b, (0, 0))
            cells.append(f"{c}/{n}" if n else "-")
        L.append(f"{ARM_LABEL[arm]:38s} " + "  ".join(f"{c:9s}" for c in cells))
    L.append("```")

    L += ["\n### Patient bootstrap 95% CI for the per-case-mean sensitivity (B = 10,000)\n", "```"]
    for arm in ARMS:
        ci = V9E1.patient_mean_ci(R, subs, arm)
        if ci is None:
            L.append(f"{ARM_LABEL[arm]:38s} not available")
            continue
        L.append(f"{ARM_LABEL[arm]:38s} {ci[0]:.3f}  [{ci[1]:.3f}, {ci[2]:.3f}]")
    L.append("```")

    L += ["\n### Localizer onset/offset |error| (median seconds, pooled matched events)\n", "```"]
    for arm in ARMS:
        e = ERR[(ERR.subject.isin(subs)) & (ERR.arm == arm)]
        if not len(e):
            L.append(f"{ARM_LABEL[arm]:38s} not available")
            continue
        _, on_s = P3L.err_stats(e, "onset_err")
        _, off_s = P3L.err_stats(e, "offset_err")
        L.append(f"{ARM_LABEL[arm]:38s} onset {on_s} | offset {off_s}")
    L.append("```")

    L += [f"\n### System-stage curve (sweep k, per-case budget + CPD localizer every point): "
          f"per-case-mean sensitivity @ FP/day {', '.join(str(t) for t in FP_TARGETS)}\n", "```"]
    for arm in ARMS:
        c = V9E1B.matched_curve_k(SYS, subs, arm)
        if c is None:
            L.append(f"{ARM_LABEL[arm]:38s} not available")
            continue
        L.append(f"{ARM_LABEL[arm]:38s} " + "  ".join(
            f"{t:.1f}:{c[t][0]:.3f}+-{c[t][1]:.3f}" if np.isfinite(c[t][0]) else f"{t:.1f}:NA" for t in FP_TARGETS))
    L.append("```")
    return summaries


def write_percase_table(L, R, SZ, cal, subs, title):
    L += [f"\n### {title}\n", "```",
          "case    set    n_sz  med_dur  mean_dur  hard   k_loo       | tp/ref    FP  sens   prec   F1    FP/day  "
          "|| fixed-dev sens  FP/day"]
    d_loo = R[(R.arm == "loo") & (R.stage == "localized")].set_index("subject")
    d_fix = R[(R.arm == "fixed_dev") & (R.stage == "localized")].set_index("subject")
    sz = SZ.set_index("subject")
    for s in subs:
        if s not in d_loo.index:
            continue
        rl, rf, z = d_loo.loc[s], d_fix.loc[s], sz.loc[s]
        prec_l = rl.tp / (rl.tp + rl.fp) if (rl.tp + rl.fp) else float("nan")
        f1_l = 2 * rl.tp / (2 * rl.tp + rl.fp + (rl.n_ref - rl.tp)) if rl.n_ref else float("nan")
        sens_l = rl.tp / rl.n_ref if rl.n_ref else float("nan")
        fa_l = rl.fp / rl.nonict_h * 24 if rl.nonict_h else float("nan")
        sens_f = rf.tp / rf.n_ref if rf.n_ref else float("nan")
        fa_f = rf.fp / rf.nonict_h * 24 if rf.nonict_h else float("nan")
        L.append(f"{s:6s} {z.set:6s} {int(z.n_sz):4d}  {z.med_dur:6.1f}  {z.mean_dur:7.1f}  "
                 f"{'Y' if z.hard else '-':4s}  {cal['k_loo'][s]:9.4f}  | {rl.tp:5.1f}/{rl.n_ref:4.0f}  "
                 f"{rl.fp:4.0f}  {sens_l:.3f}  {prec_l:.3f}  {f1_l:.3f}  {fa_l:6.2f}  "
                 f"|| {sens_f:.3f}  {fa_f:6.2f}")
    L.append("```")


def hard_patient_section(L, R, SZ):
    L.append("\n## Hard-patient table (mean seizure duration < 30 s, loo k, localized stage)\n")
    d = R[(R.arm == "loo") & (R.stage == "localized")].copy()
    d["sens"] = d.tp / d.n_ref
    sz = SZ.set_index("subject")
    d["hard"] = d.subject.map(sz.hard)
    hard_cases = sorted(d[d.hard].subject.tolist())
    other_cases = sorted(d[~d.hard].subject.tolist())
    L.append(f"- hard (mean seizure duration < {HARD_DUR_S:.0f} s): {', '.join(hard_cases) if hard_cases else '(none)'}")
    L.append(f"- other: {', '.join(other_cases)}")
    hs, os_ = d[d.hard].sens.dropna().values, d[~d.hard].sens.dropna().values
    L.append(f"- per-case sensitivity: hard mean {np.mean(hs):.3f} (n={len(hs)}), other mean {np.mean(os_):.3f} "
             f"(n={len(os_)})" if len(hs) and len(os_) else "- per-case sensitivity: one group empty, no comparison.")
    if len(hs) >= 1 and len(os_) >= 1:
        U, p = mannwhitneyu(hs, os_, alternative="two-sided")
        L.append(f"- Mann-Whitney U (two-sided, descriptive, not a gate): U = {U:.1f}, p = {p:.4f}")


# ============================================================================ report
def build_report(R, SYS, DB, ERR, SZ, cal):
    L = ["# V9-E4 -- kNN baseline (B4) on every CHB-MIT case\n",
         "Full tables: `results/v9_e4/*.csv`. Code: `src/v9_e4_knn24.py` (new; reuses "
         "src/v9_e1_baselines.py, src/v9_e1b_calibrate.py (matched_curve_k only) and every frozen "
         "script they call, read-only).\n",
         "24 cases, chb01-chb24, same file rules as the thesis (files missing one of the 18 channels "
         "skipped, e.g. chb12_27/28/29). chb21 is the same subject as chb01 (recorded 1.5 years later): "
         "every aggregate below is reported twice, once over all 24 cases and once with chb21 removed "
         "(23 subjects), plus separately for the former development (15) and former CHB-MIT test (8) "
         "groups; chb24 (1 case) sits outside both of those former groups.\n",
         "Two k_B4 variants, both reported at every case and every aggregate: **loo** = leave-one-case-out "
         "(`p3_levers.calibrate()` UNCHANGED, median q_i(k) = 0.005, run on every OTHER case's smoothed "
         "member-mean-z signal; chb01 and chb21 exclude EACH OTHER too, so neither ever calibrates on the "
         "other); **fixed_dev** = k_B4 = "
         f"{cal['k_fixed_dev']:.6f} (results/v9_e1b/calibration.json, calibrated once on the 15 "
         "development patients only, V9-E1b) -- loaded verbatim, not recomputed, for reference. Same "
         "floor/cap (clip(q_i(k), 0.005, 0.02)), smoothing (5), merge (90 s) and kernel-CPD localizer for "
         "both. Everything downstream of B4's own per-channel distance (e17b order statistics, percentile-"
         "mean final scalar, member-mean-z budget signal, localizer, SzCORE scorer) is the frozen P3 chain "
         "used unmodified by V9-E1/V9-E1b.\n"]

    write_percase_table(L, R, SZ, cal, ALL24, "Per-case table, all 24 cases")

    no21 = [s for s in ALL24 if s != "chb21"]
    for subs, title in ((ALL24, "All 24 CHB-MIT cases"),
                        (no21, "All cases with chb21 removed (23 subjects)"),
                        (FORMER_DEV, "Former development group (15 patients)"),
                        (FORMER_TEST, "Former CHB-MIT test group (8 patients)")):
        write_group_section(L, R, SYS, DB, ERR, subs, title)

    hard_patient_section(L, R, SZ)

    L.append(f"\n## Runtime measured\ncalibrate(): {cal['elapsed_s']:.0f}s (reads 24 cached m-signal "
             "arrays, 24 independent bisections). Per-subject --prep and --eval-one timing: each call's "
             "own stdout (printed elapsed seconds + peak RAM); every step is resumable (per-subject m-"
             "signal cache under results/v9_e4/_m/, part file under results/v9_e4/_parts/).")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "SUMMARY.md").write_text("\n".join(L), encoding="utf-8")
    inbox = ROOT.parent / "Agent" / "inbox" / "V9_E4_REPORT.md"
    inbox.parent.mkdir(parents=True, exist_ok=True)
    inbox.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))
    print(f"\nWrote results/v9_e4/SUMMARY.md and {inbox}")


# ============================================================================ smoke
def smoke():
    t0 = time.time()
    V9E1.repro_check_G()
    subs = ["chb01", "chb10", "chb03"]
    for s in subs:
        V9E1.cache_D(s)
    print(f"smoke: B4 cache ready for {subs} ({time.time() - t0:.0f}s)", flush=True)
    t1 = time.time()
    ms = {}
    for s in subs:
        ctx = V9E1.subject_ctx(s)
        D = V9E1.load_D(s, "B4")
        ms[s] = PS.smoothed(ctx, m_of(ctx, D), SMOOTH)
    k_loo = {s: P3L.calibrate([ms[t] for t in subs if t != s]) for s in subs}
    print(f"smoke leave-one-out k (3 cases, NOT the real 24-case loo k): "
          + ", ".join(f"{s}={k_loo[s]:.4f}" for s in subs), flush=True)
    k_fixed = json.load(open(E1B_CAL))["k_B4"]
    s0 = subs[0]
    ctx = V9E1.subject_ctx(s0)
    D = V9E1.load_D(s0, "B4")
    refs = P3L.refs_of(ctx)
    x, m = x_of(ctx, D), m_of(ctx, D)
    one_pass(ctx, x, k_loo[s0], m, refs)
    one_pass(ctx, x, k_fixed, m, refs)
    sys_rows = sys_sweep(ctx, x, m, k_loo[s0], refs)
    el = time.time() - t1
    print(f"smoke: one case's full eval (2 k variants, {len(sys_rows)} k-grid points each) took "
          f"{el:.0f}s -> projected total for --prep + --eval-one over all {len(ALL24)} cases: "
          f"~{el * len(ALL24) / 60:.0f} min (characterisation only; per-case cost varies with recording "
          "length and event count; --prep is the lighter of the two per-case steps, one ctx build + one "
          "smoothed-signal save, no localizer sweep).", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--prep", metavar="SUBJ")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--eval-one", metavar="SUBJ")
    ap.add_argument("--aggregate", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.smoke:
        smoke()
    elif a.prep:
        prep(a.prep)
    elif a.calibrate:
        calibrate()
    elif a.eval_one:
        eval_one(a.eval_one)
    elif a.aggregate:
        aggregate()
    elif a.report:
        cal = json.load(open(OUT / "calibration.json"))
        R = pd.read_csv(OUT / "per_subject.csv")
        SYS = pd.read_csv(OUT / "sys_sweep.csv")
        DB = pd.read_csv(OUT / "duration_bins.csv")
        ERR = pd.read_csv(OUT / "loc_errors.csv")
        SZ = pd.read_csv(OUT / "seizure_stats.csv")
        build_report(R, SYS, DB, ERR, SZ, cal)
    else:
        raise SystemExit("pass --smoke, --prep SUBJ, --calibrate, --eval-one SUBJ, --aggregate or --report")


if __name__ == "__main__":
    main()
