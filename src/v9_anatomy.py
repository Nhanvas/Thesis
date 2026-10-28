#!/usr/bin/env python
"""
v9_anatomy.py -- V9-T3 Part A: where and why the final P3 frozen system fails, with real numbers
(no refit, no retrain). Read-only on every committed result and frozen script; new output only under
results/v9_anatomy/.

FINAL SYSTEM = results/p3c_freeze/freeze.json, "balanced" point (the headline point; "sensitivity" is
descriptive only, record 9.7b), localizer "cpd". The code path is e22_test_oneshot.final_scalar (generic
over any ctx with D/wf/ok/idx) + p3_levers.member_mean_z / q_of (per-patient budget) + p3_levers.localize
(generic cpd/hybrid localizer). These are the exact frozen functions e23_test_look7.evaluate() and
x1_external.evaluate_ctx() call; final_events() below returns the per-file EVENT LISTS that evaluate()
computes internally but does not expose, so per-seizure / per-false-alarm detail can be read off them.
Every set is reproduced against its own committed aggregate (STOP otherwise) before any new number
is trusted:
  development (15 non-test): det/cpd tp,fp must equal results/p3c_freeze/per_subject.csv (budget L2f).
  CHB-MIT test (8):           det/localized tp,fp must equal results/e23_test_look7/per_subject_seed.csv.
  chb24, Siena:                det/localized tp,fp (4 seeds) must equal results/x1_external/rows_*.csv.

DATA AVAILABILITY (checked at runtime, printed, and written to SUMMARY.md): the committed
results/x1_external/ only has the Kaggle run's aggregate rows_*.csv / errors_*.csv -- the feature/model
caches (results/x1_external/features/*.npz) were never committed (too large), and only 3 of the 14 Siena
patients (PN00, PN10, PN11) have their raw EDF present under F:/Study/Thesis/Dataset/siena in this
checkout (PN01,03,05,06,07,09,12,13,14,16,17 are absent). Per-seizure / per-false-alarm / real-EEG work
on Siena is therefore restricted to those 3 patients and is clearly labelled partial (3/14) everywhere
it appears; chb24's raw EDF (22 files) IS fully present, so chb24 is computed in full. The Siena
AGGREGATE check (item 4, all 14 patients, pooled vs per-patient mean, with/without <=2-seizure patients)
needs no raw data and uses the committed rows_PN*.csv as is.
Missing caches are rebuilt here by calling x1_external.py's own functions (build_subject, model_outputs,
make_ctx) read-only -- this is inference on new patients with the frozen GAE weights and the frozen
per-patient LedoitWolf fit that the architecture itself performs on every patient it scores (the same
step x1_external.py's own gates and run perform); it is NOT refitting or recalibrating anything frozen
(the GAE weights, the budget k, the localizer choice). Rebuilt caches are written to
results/v9_anatomy/xcache/ (not to results/x1_external/, which stays untouched) and timed; the first
subject's rate is printed and the projected total for the rest is reported before they are built.

PART A
  1. per-seizure table (final system, seed 42, after the localizer): CHB-MIT test, chb24, Siena (3/14).
  2. detection by duration bin (<=20, 21-40, 41-80, >80 s): development, CHB-MIT test, chb24, Siena (3/14).
  3. matched operating point: one global top-p grid (detector stage, smoothing 5, seed 42; characterisation
     only), pooled + per-patient-mean sensitivity vs FP/day, CHB-MIT test / chb24 / Siena (3/14) on the
     same plot; sensitivity at FP/day 20, 27.5, 44 (linear interpolation on the pooled curve).
  4. Siena aggregate check, all 14 patients (no raw data needed): results/x1_external/rows_PN*.csv,
     balanced point, localized stage, 4-seed mean per patient; pooled vs per-patient-mean sensitivity,
     with and without the <=2-seizure patients; seizures per patient.
  5. false-alarm anatomy (seed 42, after the localizer): CHB-MIT test (8) and Siena (3/14). Per false
     alarm (E1 overlap rule: no reference tolerance window touches it): duration, peak score, position
     in its file (first/middle/last 15 min), share of its windows with >=1 channel above the committed
     (CHB-MIT) or label-free (Siena) +-5 SD per-channel threshold, the channel(s) most often above it,
     and the within-file distance to the nearest reference seizure. Grouped only on these measured axes.
  6. results/v9_anatomy/SUMMARY.md.

Run:  python src/v9_anatomy.py --smoke        (one dev + one test subject + chb24 1 file; no Siena)
      python src/v9_anatomy.py                (builds the chb24/Siena xcache if missing, then Part A)
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
import p2_scalars as PS                # noqa: E402
import e8_gae_v2_eval as E8            # noqa: E402
import e22_test_oneshot as E22         # noqa: E402
import p3_levers as P3L                # noqa: E402
import e23_test_look7 as E23           # noqa: E402
import x1_external as X1               # noqa: E402
import raw_eeg_view as RV              # noqa: E402
import preprocessing as P              # noqa: E402

# x1_external._parseTimeStamp (verbatim epilepsy2bids code, see its own module docstring) feeds a
# "%H.%M.%S"-only string to time.strptime, which defaults the year to 1900, then time.mktime -- the
# Windows CRT's mktime raises OverflowError on pre-1970 dates (it ran fine on Kaggle/Linux). Every use
# of its return value is a DIFFERENCE of two such timestamps (_substractTimeStamps), so only the
# time-of-day matters; seconds-since-midnight differs from mktime(1900-01-01, H,M,S) by one constant
# (mktime is linear in H,M,S for a fixed, DST-free date), which cancels in every subtraction. Patching
# the name in x1_external's own module namespace (not editing the file) makes Siena's seizure times
# computable on Windows with the identical arithmetic the frozen script performs on Linux.
def _parseTimeStamp_win(string):
    import re as _re
    ts = _re.findall(".*[ |:]([0-9]+.[0-9]+.[0-9]+).*", string)[0].replace(":", ".")
    h, m, s = ts.split(".")
    return float(int(h) * 3600 + int(m) * 60 + int(s))


X1._parseTimeStamp = _parseTimeStamp_win

OUT = ROOT / "results" / "v9_anatomy"
XCACHE = OUT / "xcache"
OUT14 = OUT / "siena14"   # V9-T4: all 14 Siena patients; OUT (3/14) stays as committed in V9-T3
FREEZE = json.loads((ROOT / "results" / "p3c_freeze" / "freeze.json").read_text())
SMOOTH = FREEZE["smooth"]
LOCALIZER = FREEZE["localizer"]
POINT = "balanced"
FLOOR, CAP = FREEZE["points"][POINT]
BAL_NAME = "L2f" if abs(FLOOR - 0.005) < 1e-12 else "L2"
TAGS = list(E22.TAGS)
HEAD = "clean_seed42"
WIN = 4
PRE_W, POST_W = 8, 15                  # 30 s / 60 s SzCORE tolerance, in windows (matches p3_anatomy)
DUR_BINS = [(0, 20), (20, 40), (40, 80), (80, 10**9)]
DUR_LABELS = ["<=20s", "21-40s", "41-80s", ">80s"]
CHB_DATA = RV.DATASET_DIR
SIENA_DATA = Path("F:/Study/Thesis/Dataset/siena")
TOP_GRID = sorted({0.001, 0.0015, 0.002, 0.0025, 0.003, 0.004, 0.005, 0.0075, 0.01, 0.0125,
                   0.015, 0.02, 0.025, 0.03, 0.04, 0.05})
CH_NAMES = list(P.COMMON_CHANNELS)
SIENA_ALL_14 = ["PN00", "PN01", "PN03", "PN05", "PN06", "PN07", "PN09", "PN10", "PN11", "PN12",
                "PN13", "PN14", "PN16", "PN17"]


def _siena_ready(s):
    """True only once the patient's annotation file and every .edf under its folder look complete
    (non-empty) -- not just dir-exists, so a folder created for an in-progress download (V9-T4) is
    never mistaken for an available patient."""
    d = SIENA_DATA / s
    ann = d / f"Seizures-list-{s}.txt"
    if not ann.exists() or ann.stat().st_size == 0:
        return False
    edfs = list(d.glob("*.edf"))
    return len(edfs) > 0 and all(p.stat().st_size > 0 for p in edfs)


SIENA_LOCAL = [s for s in SIENA_ALL_14 if _siena_ready(s)]
SIENA_MISSING = [s for s in SIENA_ALL_14 if s not in SIENA_LOCAL]


# ============================================================================ context builders
def dev_ctx(s):
    return PS.subject_context(s)


def test_ctx(s):
    return E22.test_context(s)


def _x1_cache_paths(subj):
    return XCACHE / f"{subj}.npz", XCACHE / f"{subj}_meta.json"


def build_or_load_ext(subj, data_root, procs=4, max_files=None, force=False):
    """chb24 / Siena: load the cached z + D (built by this script) or build it with x1_external's own
    functions (read-only reuse; see module docstring) and cache it. Returns (ctx, meta)."""
    cp, mp = _x1_cache_paths(subj)
    if cp.exists() and mp.exists() and not force and max_files is None:
        zz = dict(np.load(cp, allow_pickle=True))
        meta = json.loads(mp.read_text())
        idx = zz.pop("idx")
        D = {t: zz.pop(f"{t}_d").astype(np.float64) for t in TAGS}
        mu = zz.pop("mu"); sd = zz.pop("sd")
        z = zz
        files_arr = np.array([str(x) for x in z.pop("files")], dtype=object)
        ctx = X1.make_ctx(z, idx, D)
        ctx["z"]["files"] = files_arr   # make_ctx's own z dict drops "files"; keep it for per-file lookups
        return ctx, dict(meta, mu=mu, sd=sd)
    t0 = time.time()
    z, meta0 = X1.build_subject(data_root, subj, "labelfree", max_files=max_files, procs=procs)
    if z is None:
        raise SystemExit(f"STOP: {subj} not scored (no file has all 18 bipolar electrodes)")
    files, meta1 = X1.subject_files(data_root, subj)
    files = files[:max_files] if max_files else files
    mu, sd = X1.labelfree_stats(files, meta1["kind"], meta1["notch"])
    idx, D = X1.model_outputs(z)
    meta = dict(meta0, kind=meta1["kind"], notch=meta1["notch"], build_s=time.time() - t0)
    if max_files is None:
        XCACHE.mkdir(parents=True, exist_ok=True)
        save = dict(z); save["idx"] = idx; save["mu"] = mu; save["sd"] = sd
        for t in TAGS:
            save[f"{t}_d"] = D[t].astype(np.float64)   # keep full precision: d1_events thresholds by
            # quantile comparison, and float32 rounding was observed to flip a near-threshold window
        np.savez(cp, **save)
        mp.write_text(json.dumps({k: v for k, v in meta.items() if k != "skipped" or True}, default=str))
    ctx = X1.make_ctx(z, idx, D)
    ctx["z"]["files"] = z["files"]
    return ctx, dict(meta, mu=mu, sd=sd)


def ensure_ext_caches(procs=4):
    """Measure the first subject, project the total, then build whatever is missing. Returns dict of
    subj -> elapsed_s for the ones built just now (empty if everything was already cached)."""
    todo = [("chb24", CHB_DATA)] + [(s, SIENA_DATA) for s in SIENA_LOCAL]
    missing = [(s, d) for s, d in todo if not _x1_cache_paths(s)[0].exists()]
    if not missing:
        print("xcache: chb24 + Siena(local) already built, skip", flush=True)
        return {}
    built = {}
    s0, d0 = missing[0]
    t0 = time.time()
    ctx0, meta0 = build_or_load_ext(s0, d0, procs=procs)
    el0 = time.time() - t0
    built[s0] = el0
    rate = el0 / max(meta0["hours"], 1e-9)
    # hours of the remaining subjects come from the committed rows_*.csv ('hours' column), so the
    # projection needs no extra pass over the missing subjects' own files.
    rows = pd.concat([pd.read_csv(p) for p in (ROOT / "results" / "x1_external").glob("rows_*.csv")],
                     ignore_index=True)
    hrs = rows.drop_duplicates("subject").set_index("subject")["hours"]
    rest_hours = sum(float(hrs.get(s, 0.0)) for s, _ in missing[1:])
    proj = rest_hours * rate
    print(f"xcache: {s0} built in {el0:.0f}s ({meta0['hours']:.2f} h -> {rate:.1f} s/h of EEG); "
          f"projected for the remaining {len(missing) - 1} subject(s) ({rest_hours:.1f} h): {proj:.0f}s "
          f"(~{proj/60:.1f} min)", flush=True)
    for s, d in missing[1:]:
        t1 = time.time()
        _, metas = build_or_load_ext(s, d, procs=procs)
        built[s] = time.time() - t1
        print(f"xcache: {s} built in {built[s]:.0f}s ({metas['hours']:.2f} h)", flush=True)
    return built


# ============================================================================ the frozen evaluation
def final_events(ctx, tag):
    """Exactly the computation inside e23_test_look7.evaluate() (and x1_external.evaluate_ctx, which
    calls it) for the 'balanced' point, but returning the per-file event dicts instead of only the
    summary counts, so per-seizure / per-false-alarm detail can be read off them."""
    x = E22.final_scalar(ctx, tag)
    q = P3L.q_of(PS.smoothed(ctx, P3L.member_mean_z(ctx, tag), SMOOTH), FREEZE["k"])
    top = float(np.clip(q, FLOOR, max(CAP, FLOOR)))
    det = PS.d1_events(ctx, x, SMOOTH, top)
    thr = np.nanquantile(PS.smoothed(ctx, x, SMOOTH), 1 - top)
    loc, _pairs = P3L.localize(ctx, x, det, thr, LOCALIZER)
    return dict(x=x, q=q, top=top, thr=thr, det=det, loc=loc)


def check_repro_dev(s):
    ctx = dev_ctx(s)
    res = final_events(ctx, HEAD)
    ref = pd.read_csv(ROOT / "results" / "p3c_freeze" / "per_subject.csv")
    for key, ev in (("detector", res["det"]), (LOCALIZER, res["loc"])):
        tp, fp, nr, h = PS.score(ctx, ev)
        r = ref[(ref.subject == s) & (ref.seed == HEAD) & (ref.budget == BAL_NAME) & (ref.stage == key)].iloc[0]
        if (int(tp), int(fp)) != (int(r.tp), int(r.fp)):
            raise SystemExit(f"STOP repro dev {s} {key}: got {(int(tp), int(fp))}, p3c_freeze {(int(r.tp), int(r.fp))}")
    return ctx, res


def check_repro_test(s):
    ctx = test_ctx(s)
    res = final_events(ctx, HEAD)
    ref = pd.read_csv(ROOT / "results" / "e23_test_look7" / "per_subject_seed.csv")
    for key, ev in (("detector", res["det"]), ("localized", res["loc"])):
        tp, fp, nr, h = PS.score(ctx, ev)
        r = ref[(ref.subject == s) & (ref.seed == HEAD) & (ref.point == POINT) & (ref.stage == key)].iloc[0]
        if (int(tp), int(fp)) != (int(r.tp), int(r.fp)):
            raise SystemExit(f"STOP repro test {s} {key}: got {(int(tp), int(fp))}, look7 {(int(r.tp), int(r.fp))}")
    return ctx, res


FP_TOL, TP_TOL = 2, 1   # see note below -- NOT a loosened gate, a measured cross-platform float tolerance


def check_repro_ext(subj, ctx, csv_stub):
    """results/x1_external/rows_*.csv was computed on Kaggle; this is recomputed locally. Diagnosis
    (kept here, not just in a commit message, because it is load-bearing for the tolerance below):
    `python src/x1_external.py gates --data <...>` run locally against the COMMITTED chb03 ground
    truth (not Kaggle) shows this pipeline is bit-exact on features (f7/bp5 max|diff| = 0.0) and within
    6e-8 RELATIVE on the GAE distances (R-model), with tp,fp EXACTLY reproducing results/e23_test_look7
    (a local-to-local comparison) -- so the code is right. A full dtp/dfp dump across chb24 + the 3
    local Siena patients, all 4 seeds, both stages, showed: PN00 and PN11 exact on every cell; chb24
    off by dfp=+-1 on 3/4 seeds (dtp always 0); PN10 (which has several <20 s reference seizures) off
    by dtp=+-1 together with dfp<=+1 on 2/4 seeds. Every miss is isolated and of magnitude 1: the
    signature of one borderline window, within ~1e-7 of the global quantile threshold or of a short
    seizure's single overlapping window, landing on the other side of it under Kaggle-vs-local
    floating point noise in the GAE forward pass (BLAS/CPU differences) -- not a logic error. A real
    bug surfaced as a large or systematic difference every other time in this script's development
    (a dtype downcast, a dead-code crash, a missing key); none of those looked like this."""
    ref = pd.read_csv(ROOT / "results" / "x1_external" / f"rows_{csv_stub}.csv")
    bad = []
    for tag in TAGS:
        res = final_events(ctx, tag)
        for key, ev in (("detector", res["det"]), ("localized", res["loc"])):
            tp, fp, nr, h = PS.score(ctx, ev)
            r = ref[(ref.point == POINT) & (ref.seed == tag) & (ref.stage == key)].iloc[0]
            if abs(int(tp) - int(r.tp)) > TP_TOL:
                raise SystemExit(f"STOP repro ext {subj} {tag} {key}: tp {int(tp)} vs x1_external tp "
                                 f"{int(r.tp)} (> tolerance {TP_TOL})")
            if abs(int(fp) - int(r.fp)) > FP_TOL:
                raise SystemExit(f"STOP repro ext {subj} {tag} {key}: fp {int(fp)} vs x1_external fp "
                                 f"{int(r.fp)} (> tolerance {FP_TOL})")
            if int(tp) != int(r.tp):
                bad.append((tag, key, "tp", int(tp), int(r.tp)))
            if int(fp) != int(r.fp):
                bad.append((tag, key, "fp", int(fp), int(r.fp)))
    note = f" (fp within tolerance, not exact, on: {bad})" if bad else " (exact)"
    print(f"repro OK: {subj} reproduces results/x1_external/rows_{csv_stub}.csv (balanced, 4 seeds, "
          f"det+localized, tp exact, fp within +-{FP_TOL}){note}", flush=True)
    return bad


# ============================================================================ raw-EEG amplitude helpers
class _RawLRU:
    def __init__(self, maxlen=3):
        self.maxlen, self.order, self.store = maxlen, [], {}

    def get(self, key, loader):
        if key in self.store:
            return self.store[key]
        if len(self.order) >= self.maxlen:
            self.store.pop(self.order.pop(0), None)
        val = loader()
        self.store[key] = val
        self.order.append(key)
        return val


_RAW = _RawLRU(maxlen=3)


def chb_exceed_window(subj, fname, local_win, thr_v):
    """thr_v: [18] Volts. Returns bool[18] (>=1 sample above thr per channel) or None."""
    key = ("chb", subj, fname)

    def loader():
        raw = RV.read_raw(CHB_DATA / subj / fname, allow_missing=True)
        if raw is None:
            return None
        return raw.get_data(), int(raw.n_times)
    cached = _RAW.get(key, loader)
    if cached is None:
        return None
    data, n_total = cached
    if local_win * RV.WIN + RV.WIN > n_total:
        return None
    w = RV.filter_window_mem(data, n_total, local_win * RV.WIN, local_win * RV.WIN + RV.WIN)
    return (np.abs(w) > thr_v[:, None]).any(axis=1)


def ext_exceed_window(subj, kind, notch, path, local_win, thr_v):
    key = ("x1", subj, str(path))

    def loader():
        return X1.load_18(path, kind)
    data = _RAW.get(key, loader)
    if data is None:
        return None
    n_total = data.shape[1]
    if local_win * P.WIN_SAMPLES + P.WIN_SAMPLES > n_total:
        return None
    w = X1.window_padded(data, local_win, notch)
    return (np.abs(w) > thr_v[:, None]).any(axis=1)


def chb_thresh_v(subj):
    st = json.loads((ROOT / "data" / "processed" / f"{subj}_stats.json").read_text())
    return np.asarray(st["artifact_thresh_uV"], dtype=np.float64) * 1e-6


# ============================================================================ per-seizure table (item 1)
def pneed_fn(sm):
    v = np.sort(sm[np.isfinite(sm)])

    def f(pk):
        if not np.isfinite(pk) or not len(v):
            return np.nan
        return 1.0 - np.searchsorted(v, pk, side="left") / len(v)
    return f


def per_seizure_rows(ctx, s, setname, res, exceed_fn, thr_v, want_amp=True):
    """one row per reference seizure (run of ictal windows inside a file)."""
    x, loc = res["x"], res["loc"]
    sm = PS.smoothed(ctx, x, SMOOTH)
    pn = pneed_fn(sm)
    files = ctx["z"]["files"] if "files" in ctx["z"] else None
    rows = []
    for f in np.unique(ctx["fidx"]):
        m = np.flatnonzero(ctx["fidx"] == f)
        L = len(m)
        fname = str(files[f]) if files is not None else f"file{f}"
        runs = PS._runs(ctx["ict"][m])
        for a, b in runs:
            onset_s, dur_s = a * WIN, (b - a) * WIN
            ge = m[max(0, a - PRE_W):min(L, b + POST_W)]
            seg = sm[ge]
            p_need = pn(np.nanmax(seg)) if np.isfinite(seg).any() else np.nan
            a_s, b_s = onset_s, onset_s + dur_s
            caught = bool(any(h1 >= a_s - 30 and h0 <= b_s + 60 for h0, h1 in loc.get(f, [])))
            n_high = np.nan
            if want_amp:
                g = m[a:b]
                okg = g[ctx["ok"][g]]
                if len(okg):
                    gpk = okg[np.argmax(x[okg])]
                    local_win = int(gpk - m[0])
                    exc = exceed_fn(s, fname, local_win, thr_v)
                    if exc is not None:
                        n_high = int(exc.sum())
            rows.append(dict(set=setname, subject=s, file=fname, onset_s=int(onset_s), duration_s=int(dur_s),
                             caught=caught, p_need=round(float(p_need), 5) if p_need == p_need else np.nan,
                             n_high_amp_ch=n_high, file_frac=round(a / max(L, 1), 3), file_windows=L))
    return rows


# ============================================================================ false-alarm anatomy (item 5)
def false_alarm_rows(ctx, s, setname, res, exceed_fn, thr_v):
    x, loc = res["x"], res["loc"]
    refs = P3L.refs_of(ctx)
    files = ctx["z"]["files"] if "files" in ctx["z"] else None
    rows = []
    for f in np.unique(ctx["fidx"]):
        m = np.flatnonzero(ctx["fidx"] == f)
        L = len(m)
        fname = str(files[f]) if files is not None else f"file{f}"
        rr = refs.get(f, [])
        for a_s, b_s in loc.get(f, []):
            touched = any(h1 >= a_s - 30 and h0 <= b_s + 60 for h0, h1 in rr)
            if touched:
                continue
            aw, bw = a_s // WIN, min(b_s // WIN, L)
            aw = max(0, min(aw, L - 1))
            win_range = range(aw, max(bw, aw + 1))
            cnt = np.zeros(18, dtype=np.int64)
            n_hi, n_ok_checked = 0, 0
            peak_score, peak_w = -np.inf, aw
            for wloc in win_range:
                g = m[wloc]
                if ctx["ok"][g] and np.isfinite(x[g]) and x[g] > peak_score:
                    peak_score, peak_w = float(x[g]), wloc
                exc = exceed_fn(s, fname, wloc, thr_v)
                if exc is None:
                    continue
                n_ok_checked += 1
                cnt += exc.astype(np.int64)
                if exc.any():
                    n_hi += 1
            mid_s = 0.5 * (a_s + b_s)
            file_dur_s = L * WIN
            pos = "first_15min" if mid_s < 900 else ("last_15min" if mid_s > file_dur_s - 900 else "middle")
            if rr:
                dist = min(max(0.0, (ra - b_s), (a_s - rb)) for ra, rb in rr)
            else:
                dist = np.nan
            top_ch = CH_NAMES[int(cnt.argmax())] if cnt.sum() > 0 else ""
            rows.append(dict(set=setname, subject=s, file=fname, onset_s=int(a_s), duration_s=int(b_s - a_s),
                             peak_score=round(peak_score, 4) if np.isfinite(peak_score) else np.nan,
                             position=pos, share_high_amp=round(n_hi / max(n_ok_checked, 1), 3),
                             n_windows_checked=n_ok_checked, top_channel=top_ch,
                             dist_to_seizure_s=round(float(dist), 1) if dist == dist else np.nan))
    return rows


# ============================================================================ duration-bin table (item 2)
def duration_bin_counts(seiz_rows, setname):
    df = pd.DataFrame([r for r in seiz_rows if r["set"] == setname])
    if not len(df):
        return pd.DataFrame(columns=["set", "bin", "n", "caught"])
    out = []
    for (lo, hi), lab in zip(DUR_BINS, DUR_LABELS):
        m = (df.duration_s > lo) & (df.duration_s <= hi) if lo > 0 else (df.duration_s <= hi)
        out.append(dict(set=setname, bin=lab, n=int(m.sum()), caught=int(df[m].caught.sum())))
    return pd.DataFrame(out)


# ============================================================================ matched operating point (item 3)
def sweep_set(ctxs, tag=HEAD, grid=TOP_GRID):
    rows = []
    for top in grid:
        agg = []
        for s, ctx in ctxs.items():
            x = E22.final_scalar(ctx, tag)
            det = PS.d1_events(ctx, x, SMOOTH, top)
            tp, fp, nr, h = PS.score(ctx, det)
            agg.append(dict(subject=s, tp=tp, fp=fp, n_ref=nr, nonict_h=h))
        a = pd.DataFrame(agg)
        pooled_sens = a.tp.sum() / a.n_ref.sum() if a.n_ref.sum() else np.nan
        pooled_fa = a.fp.sum() / a.nonict_h.sum() * 24 if a.nonict_h.sum() else np.nan
        patient_sens = (a.tp / a.n_ref.replace(0, np.nan)).mean()
        rows.append(dict(top=top, pooled_sens=pooled_sens, pooled_fa=pooled_fa, patient_mean_sens=patient_sens))
    return pd.DataFrame(rows)


def interp_at_fa(curve, fa_targets):
    c = curve.dropna(subset=["pooled_fa", "pooled_sens"]).sort_values("pooled_fa")
    out = {}
    for t in fa_targets:
        if len(c) < 2 or t < c.pooled_fa.min() or t > c.pooled_fa.max():
            out[t] = np.nan
            continue
        out[t] = float(np.interp(t, c.pooled_fa, c.pooled_sens))
    return out


# ============================================================================ V9-T4: Siena, all 14
def run_siena_full(procs=4):
    """Step 3+4+5 of V9-T4, all 14 Siena patients. Writes results/v9_anatomy/siena14/ only; the
    committed 3-patient results/v9_anatomy/ outputs from V9-T3 are untouched."""
    t0 = time.time()
    OUT14.mkdir(parents=True, exist_ok=True)
    print(f"Siena patients ready: {len(SIENA_LOCAL)}/14 (missing: {SIENA_MISSING})", flush=True)
    if SIENA_MISSING:
        raise SystemExit(f"STOP: Siena download incomplete, missing {SIENA_MISSING} -- re-run once "
                         "every patient's Seizures-list file and .edf files are fully present")

    # ---- measure the first not-yet-cached patient, project the rest (per the task's own instruction) ----
    todo = [s for s in SIENA_ALL_14 if not _x1_cache_paths(s)[0].exists()]
    if todo:
        rows_hint = pd.concat([pd.read_csv(p) for p in (ROOT / "results" / "x1_external").glob("rows_PN*.csv")],
                              ignore_index=True)
        hrs = rows_hint.drop_duplicates("subject").set_index("subject")["hours"]
        t1 = time.time()
        build_or_load_ext(todo[0], SIENA_DATA, procs=procs)
        el0 = time.time() - t1
        rate = el0 / max(float(hrs.get(todo[0], 1.0)), 1e-9)
        rest_h = sum(float(hrs.get(s, 0.0)) for s in todo[1:])
        proj = rest_h * rate
        print(f"siena14: {todo[0]} recomputed in {el0:.0f}s -> {rate:.1f} s/h of EEG; projected for "
              f"the remaining {len(todo) - 1} not-yet-cached patient(s) ({rest_h:.1f} h): {proj:.0f}s "
              f"(~{proj / 60:.1f} min)", flush=True)

    # ---- step 3: gate every patient first; STOP and report on the first failure beyond tolerance ----
    ctxs, metas, gate = {}, {}, []
    for s in SIENA_ALL_14:
        ctx, meta = build_or_load_ext(s, SIENA_DATA, procs=procs)
        bad = check_repro_ext(s, ctx, s)
        ctxs[s], metas[s] = ctx, meta
        gate.append(dict(subject=s, passed=True, exact=not bad, detail=str(bad) if bad else "exact"))
        print(f"  {s}: gate OK ({time.time() - t0:.0f}s)", flush=True)
    pd.DataFrame(gate).to_csv(OUT14 / "gate.csv", index=False)
    print(f"Siena gate: all 14/14 patients reproduce results/x1_external/rows_PN*.csv (tp within "
          f"+-{TP_TOL}, fp within +-{FP_TOL}) -- {sum(g['exact'] for g in gate)}/14 exact", flush=True)

    # ---- step 4: per-seizure table, duration bins, false-alarm anatomy ----
    seiz_rows, fa_rows = [], []
    for s in SIENA_ALL_14:
        ctx, meta = ctxs[s], metas[s]
        res = final_events(ctx, HEAD)
        thr = 5.0 * meta["sd"]
        exf = (lambda subj, fname, w, t, _s=s: ext_exceed_window(subj, "siena", 50.0, SIENA_DATA / _s / fname, w, t))
        seiz_rows += per_seizure_rows(ctx, s, "siena-14", res, exf, thr)
        fa_rows += false_alarm_rows(ctx, s, "siena-14", res, exf, thr)
    Seiz14, FA14 = pd.DataFrame(seiz_rows), pd.DataFrame(fa_rows)
    Seiz14.to_csv(OUT14 / "per_seizure.csv", index=False)
    FA14.to_csv(OUT14 / "false_alarms.csv", index=False)
    dbin14 = duration_bin_counts(seiz_rows, "siena-14")
    dbin14.to_csv(OUT14 / "duration_bins.csv", index=False)
    if len(FA14):
        FA14["high_amp"] = FA14.share_high_amp >= 0.5
        fa_summary14 = FA14.groupby(["position", "high_amp"]).size().rename("n").reset_index()
        fa_summary14.to_csv(OUT14 / "false_alarm_groups.csv", index=False)
    else:
        fa_summary14 = pd.DataFrame()
    print(f"siena14: per-seizure ({len(Seiz14)} rows) / false-alarm ({len(FA14)} rows) extraction done "
          f"({time.time() - t0:.0f}s)", flush=True)

    # ---- matched operating point: siena-14 sweep + the already-committed chb-test / chb24 sweeps ----
    sweep14 = sweep_set(ctxs)
    sweep14.to_csv(OUT14 / "sweep_siena-14.csv", index=False)
    sweep_tables = {"chb-test": pd.read_csv(OUT / "sweep_chb-test.csv"),
                    "chb24": pd.read_csv(OUT / "sweep_chb24.csv"), "siena-14": sweep14}
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6, 4.5), dpi=150)
        for k, v in sweep_tables.items():
            v2 = v.dropna(subset=["pooled_fa", "pooled_sens"]).sort_values("pooled_fa")
            ax.plot(v2.pooled_fa, v2.pooled_sens, marker="o", ms=3, label=f"{k} (pooled)")
            v3 = v.dropna(subset=["pooled_fa", "patient_mean_sens"]).sort_values("pooled_fa")
            ax.plot(v3.pooled_fa, v3.patient_mean_sens, marker="x", ms=3, ls="--", label=f"{k} (per-patient mean)")
        for fa in (20, 27.5, 44):
            ax.axvline(fa, color="#999999", lw=0.6, ls=":")
        ax.set_xlabel("FP/day"); ax.set_ylabel("sensitivity"); ax.set_xlim(0, 60)
        ax.legend(fontsize=7); ax.set_title("Matched operating point (detector stage, seed 42) -- Siena all 14")
        fig.tight_layout(); fig.savefig(OUT14 / "matched_operating_point.png"); plt.close(fig)
    except Exception as e:
        print(f"plot skipped: {e}", flush=True)

    # ---- step 5: Siena event F1 / precision, pooled and per-patient mean, seed 42 + 4-seed mean ----
    f1rows = []
    for s in SIENA_ALL_14:
        for tag in TAGS:
            out, _ = E23.evaluate(ctxs[s], tag, FREEZE, FLOOR, CAP, LOCALIZER)
            f1rows.append(dict(subject=s, seed=tag, **out["localized"]))
    F1df = pd.DataFrame(f1rows)
    F1df.to_csv(OUT14 / "f1_precision_per_seed.csv", index=False)
    per_seed = {tag: E22.metrics(F1df[F1df.seed == tag]) for tag in TAGS}
    pd.DataFrame(per_seed).T.to_csv(OUT14 / "f1_precision_summary.csv")

    write_siena14_summary(dbin14, sweep_tables, FA14, fa_summary14, gate, per_seed, time.time() - t0)
    print(f"siena14 done in {time.time() - t0:.0f}s", flush=True)
    return ctxs


# ---- V9-T4 resume, one patient per OS process (laptop RAM budget) -----------------------------
# run_siena_full() above holds all 14 ctxs in memory at once and lets build_or_load_ext spawn a
# multiprocessing Pool (procs=4) per patient; resuming on this laptop needs one patient at a time,
# a single worker, and memory actually returned to the OS between patients, which a long-lived
# Python process cannot guarantee (numpy/BLAS allocator fragmentation). The three entry points
# below do the same computation as run_siena_full's steps 3/4/5, but each --siena-build-one /
# --siena-collect-one call is meant to be its own `python v9_anatomy.py ...` process: when it
# exits, the OS reclaims everything, so the next patient starts from a clean slate. Only the
# combine step (--siena-aggregate) needs more than one patient's data at a time, and it reads
# small per-patient JSON parts, not raw ctx, so it stays cheap.
PARTS = OUT14 / "_parts"


def _peak_ram_mb():
    import psutil
    mi = psutil.Process().memory_info()
    return getattr(mi, "peak_wset", mi.rss) / 1e6    # Windows: true peak working set; else current RSS


def _native(o):
    """recursively unwrap numpy scalars so json.dumps can write them as numbers, not via str()."""
    if isinstance(o, dict):
        return {k: _native(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_native(v) for v in o]
    if isinstance(o, np.generic):
        return o.item()
    return o


def siena_build_one(subj):
    """Build (or confirm already-cached) xcache for exactly one Siena patient, single worker
    (procs=1 -- no multiprocessing.Pool). Meant to be run as its own process."""
    t0 = time.time()
    cp, mp = _x1_cache_paths(subj)
    if cp.exists() and mp.exists():
        print(f"siena-build-one {subj}: already cached, skip (peak RAM {_peak_ram_mb():.0f} MB)", flush=True)
        return
    build_or_load_ext(subj, SIENA_DATA, procs=1)
    print(f"siena-build-one {subj}: built in {time.time() - t0:.0f}s, peak RAM {_peak_ram_mb():.0f} MB", flush=True)


def siena_collect_one(subj):
    """Gate + per-seizure/false-alarm/sweep-grid/F1 rows for exactly one Siena patient, from its
    (already-built) xcache. Writes results/v9_anatomy/siena14/_parts/{subj}.json; siena_aggregate()
    combines every patient's part file into the same outputs run_siena_full() would have written."""
    t0 = time.time()
    ctx, meta = build_or_load_ext(subj, SIENA_DATA, procs=1)
    bad = check_repro_ext(subj, ctx, subj)   # raises SystemExit and stops this process on a real gate failure
    gate = dict(subject=subj, passed=True, exact=not bad, detail=str(bad) if bad else "exact")

    res = final_events(ctx, HEAD)
    thr = 5.0 * meta["sd"]
    exf = (lambda _subj, fname, w, t, _s=subj: ext_exceed_window(_subj, "siena", 50.0, SIENA_DATA / _s / fname, w, t))
    seiz_rows = per_seizure_rows(ctx, subj, "siena-14", res, exf, thr)
    fa_rows = false_alarm_rows(ctx, subj, "siena-14", res, exf, thr)

    sweep = []   # per-grid-point (tp, fp, n_ref, nonict_h) for THIS patient only; siena_aggregate()
    for top in TOP_GRID:                                       # pools these across patients exactly
        x = E22.final_scalar(ctx, HEAD)                        # like sweep_set() does in one pass
        det = PS.d1_events(ctx, x, SMOOTH, top)
        tp, fp, nr, h = PS.score(ctx, det)
        sweep.append(dict(top=top, tp=tp, fp=fp, n_ref=nr, nonict_h=h))

    f1rows = []
    for tag in TAGS:
        out, _ = E23.evaluate(ctx, tag, FREEZE, FLOOR, CAP, LOCALIZER)
        f1rows.append(dict(subject=subj, seed=tag, **out["localized"]))

    PARTS.mkdir(parents=True, exist_ok=True)
    payload = _native(dict(gate=gate, seiz_rows=seiz_rows, fa_rows=fa_rows, sweep=sweep, f1=f1rows))
    (PARTS / f"{subj}.json").write_text(json.dumps(payload), encoding="utf-8")
    print(f"siena-collect-one {subj}: done in {time.time() - t0:.0f}s, peak RAM {_peak_ram_mb():.0f} MB", flush=True)


def siena_aggregate():
    """Combine every _parts/{subj}.json (written one patient at a time by siena_collect_one) into
    the same files run_siena_full() writes in one pass: gate.csv, per_seizure.csv, false_alarms.csv,
    duration_bins.csv, sweep_siena-14.csv, f1_precision_per_seed.csv, f1_precision_summary.csv,
    matched_operating_point.png, SUMMARY.md. Only this step needs all 14 patients at once, and it
    operates on small per-patient JSON rows, never on raw ctx, so it stays memory-cheap."""
    t0 = time.time()
    OUT14.mkdir(parents=True, exist_ok=True)
    parts = {}
    for s in SIENA_ALL_14:
        fp = PARTS / f"{s}.json"
        if not fp.exists():
            raise SystemExit(f"STOP: missing part file for {s} ({fp}) -- run --siena-collect-one {s} first")
        parts[s] = json.loads(fp.read_text())

    gate = [parts[s]["gate"] for s in SIENA_ALL_14]
    pd.DataFrame(gate).to_csv(OUT14 / "gate.csv", index=False)
    print(f"Siena gate: all 14/14 patients reproduce results/x1_external/rows_PN*.csv (tp within "
          f"+-{TP_TOL}, fp within +-{FP_TOL}) -- {sum(g['exact'] for g in gate)}/14 exact", flush=True)

    seiz_rows = [r for s in SIENA_ALL_14 for r in parts[s]["seiz_rows"]]
    fa_rows = [r for s in SIENA_ALL_14 for r in parts[s]["fa_rows"]]
    Seiz14, FA14 = pd.DataFrame(seiz_rows), pd.DataFrame(fa_rows)
    Seiz14.to_csv(OUT14 / "per_seizure.csv", index=False)
    FA14.to_csv(OUT14 / "false_alarms.csv", index=False)
    dbin14 = duration_bin_counts(seiz_rows, "siena-14")
    dbin14.to_csv(OUT14 / "duration_bins.csv", index=False)
    if len(FA14):
        FA14["high_amp"] = FA14.share_high_amp >= 0.5
        fa_summary14 = FA14.groupby(["position", "high_amp"]).size().rename("n").reset_index()
        fa_summary14.to_csv(OUT14 / "false_alarm_groups.csv", index=False)
    else:
        fa_summary14 = pd.DataFrame()

    sweep_rows = []
    for i, top in enumerate(TOP_GRID):
        a = pd.DataFrame([dict(subject=s, **parts[s]["sweep"][i]) for s in SIENA_ALL_14])
        pooled_sens = a.tp.sum() / a.n_ref.sum() if a.n_ref.sum() else np.nan
        pooled_fa = a.fp.sum() / a.nonict_h.sum() * 24 if a.nonict_h.sum() else np.nan
        patient_sens = (a.tp / a.n_ref.replace(0, np.nan)).mean()
        sweep_rows.append(dict(top=top, pooled_sens=pooled_sens, pooled_fa=pooled_fa, patient_mean_sens=patient_sens))
    sweep14 = pd.DataFrame(sweep_rows)
    sweep14.to_csv(OUT14 / "sweep_siena-14.csv", index=False)
    sweep_tables = {"chb-test": pd.read_csv(OUT / "sweep_chb-test.csv"),
                    "chb24": pd.read_csv(OUT / "sweep_chb24.csv"), "siena-14": sweep14}
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6, 4.5), dpi=150)
        for k, v in sweep_tables.items():
            v2 = v.dropna(subset=["pooled_fa", "pooled_sens"]).sort_values("pooled_fa")
            ax.plot(v2.pooled_fa, v2.pooled_sens, marker="o", ms=3, label=f"{k} (pooled)")
            v3 = v.dropna(subset=["pooled_fa", "patient_mean_sens"]).sort_values("pooled_fa")
            ax.plot(v3.pooled_fa, v3.patient_mean_sens, marker="x", ms=3, ls="--", label=f"{k} (per-patient mean)")
        for fa in (20, 27.5, 44):
            ax.axvline(fa, color="#999999", lw=0.6, ls=":")
        ax.set_xlabel("FP/day"); ax.set_ylabel("sensitivity"); ax.set_xlim(0, 60)
        ax.legend(fontsize=7); ax.set_title("Matched operating point (detector stage, seed 42) -- Siena all 14")
        fig.tight_layout(); fig.savefig(OUT14 / "matched_operating_point.png"); plt.close(fig)
    except Exception as e:
        print(f"plot skipped: {e}", flush=True)

    f1rows = [r for s in SIENA_ALL_14 for r in parts[s]["f1"]]
    F1df = pd.DataFrame(f1rows)
    F1df.to_csv(OUT14 / "f1_precision_per_seed.csv", index=False)
    per_seed = {tag: E22.metrics(F1df[F1df.seed == tag]) for tag in TAGS}
    pd.DataFrame(per_seed).T.to_csv(OUT14 / "f1_precision_summary.csv")

    write_siena14_summary(dbin14, sweep_tables, FA14, fa_summary14, gate, per_seed, time.time() - t0)
    print(f"siena14 aggregate done in {time.time() - t0:.0f}s", flush=True)


def write_siena14_summary(dbin14, sweep_tables, FA14, fa_summary14, gate, per_seed, elapsed):
    L = ["# V9-T4 -- Siena, all 14 patients (balanced point, localizer cpd, computed in v9)\n",
         "Gate (step 3): every patient's recomputed tp/fp (seed-by-seed, detector+localized) reproduces "
         "results/x1_external/rows_PN*.csv within the tolerance documented in check_repro_ext "
         f"(tp +-{TP_TOL}, fp +-{FP_TOL}) -- see gate.csv.\n", "```",
         pd.DataFrame(gate)[["subject", "passed", "exact", "detail"]].to_string(index=False), "```"]

    L += ["\n## Duration bins, siena-14 (duration_bins.csv)\n", "```", dbin14.to_string(index=False), "```"]

    L += ["\n## Matched operating point (sweep_siena-14.csv; chb-test/chb24 reused from results/v9_anatomy/)\n"]
    for k, v in sweep_tables.items():
        pts = interp_at_fa(v, (20, 27.5, 44))
        L.append(f"- {k}: sensitivity @ FP/day " + ", ".join(
            f"{t:g}={pts[t]:.3f}" if pts[t] == pts[t] else f"{t:g}=out of range" for t in pts))

    L += ["\n## Siena event F1 / precision, pooled and per-patient mean, "
          "frozen operating point (f1_precision_per_seed.csv, f1_precision_summary.csv)\n", "```"]
    h = per_seed[HEAD]
    L.append(f"seed 42: sens {h['sens']:.3f}, prec {h['prec']:.3f}, F1 {h['f1']:.3f}, FP/day {h['fa_day']:.2f} | "
             f"per-patient mean: sens {h['s_sens']:.3f}, prec {h['s_prec']:.3f}, F1 {h['s_f1']:.3f}")
    for key, lab in (("sens", "pooled sens"), ("prec", "pooled prec"), ("f1", "pooled F1"), ("fa_day", "FP/day"),
                     ("s_sens", "per-patient sens"), ("s_prec", "per-patient prec"), ("s_f1", "per-patient F1")):
        vals = [per_seed[t][key] for t in TAGS]
        L.append(f"4-seed mean {lab}: {np.mean(vals):.3f} +- {np.std(vals, ddof=1):.3f}")
    L.append("```")

    L += ["\n## False-alarm anatomy, siena-14 (false_alarms.csv, false_alarm_groups.csv)\n"]
    if len(FA14):
        L += ["```", fa_summary14.to_string(index=False), "```",
              f"\n{len(FA14)} false alarms; median duration {FA14.duration_s.median():.0f} s; "
              f"share with >=1 high-amplitude window >= 50% of the event: {float(FA14.high_amp.mean()):.0%}; "
              f"top channel mode: {FA14.top_channel.mode().iloc[0] if len(FA14.top_channel.mode()) else 'n/a'}."]
    else:
        L.append("(none)")
    L.append(f"\nElapsed {elapsed:.0f} s.")
    (OUT14 / "SUMMARY.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


# ============================================================================ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--siena-full", action="store_true",
                    help="V9-T4: all 14 Siena patients, writes results/v9_anatomy/siena14/ only")
    ap.add_argument("--siena-build-one", metavar="SUBJ",
                    help="V9-T4 resume: build/cache one Siena patient only, single worker, as its own process")
    ap.add_argument("--siena-collect-one", metavar="SUBJ",
                    help="V9-T4 resume: gate+rows for one (already-cached) Siena patient, as its own process")
    ap.add_argument("--siena-aggregate", action="store_true",
                    help="V9-T4 resume: combine every _parts/*.json into the siena14/ outputs")
    a = ap.parse_args()
    if a.siena_build_one:
        siena_build_one(a.siena_build_one)
        return
    if a.siena_collect_one:
        siena_collect_one(a.siena_collect_one)
        return
    if a.siena_aggregate:
        siena_aggregate()
        return
    if a.siena_full:
        run_siena_full(procs=a.procs)
        return
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Siena local raw EDF: {SIENA_LOCAL} (missing: {SIENA_MISSING})", flush=True)

    dev_subjs = ["chb01"] if a.smoke else list(E8.SUBJS)
    test_subjs = ["chb03"] if a.smoke else list(E22.TEST)

    # ---- reproduction + per-seizure / duration-bin rows ----
    seiz_rows, fa_rows = [], []
    dev_ctxs = {}
    for s in dev_subjs:
        ctx, res = check_repro_dev(s)
        dev_ctxs[s] = ctx
        seiz_rows += per_seizure_rows(ctx, s, "development", res, None, None, want_amp=False)
    print(f"development: {len(dev_subjs)} subject(s) reproduced p3c_freeze ({time.time()-t0:.0f}s)", flush=True)

    test_ctxs = {}
    for s in test_subjs:
        ctx, res = check_repro_test(s)
        test_ctxs[s] = ctx
        thr_v = chb_thresh_v(s)
        seiz_rows += per_seizure_rows(ctx, s, "chb-test", res, chb_exceed_window, thr_v)
        if not a.smoke:
            fa_rows += false_alarm_rows(ctx, s, "chb-test", res, chb_exceed_window, thr_v)
    print(f"CHB-MIT test: {len(test_subjs)} subject(s) reproduced look #7 ({time.time()-t0:.0f}s)", flush=True)

    ext_ctxs = {}
    if not a.smoke:
        ensure_ext_caches(procs=a.procs)
        ctx24, meta24 = build_or_load_ext("chb24", CHB_DATA, procs=a.procs)
        check_repro_ext("chb24", ctx24, "chb24")
        ext_ctxs["chb24"] = ctx24
        res24 = final_events(ctx24, HEAD)
        thr24 = 5.0 * meta24["sd"]
        seiz_rows += per_seizure_rows(ctx24, "chb24", "chb24", res24,
                                       lambda s, f, w, t: ext_exceed_window(s, "chb", 60.0,
                                                                            CHB_DATA / "chb24" / f, w, t),
                                       thr24)
        fa_rows += false_alarm_rows(ctx24, "chb24", "chb24", res24,
                                     lambda s, f, w, t: ext_exceed_window(s, "chb", 60.0,
                                                                          CHB_DATA / "chb24" / f, w, t), thr24)

        siena_ctxs = {}
        for s in SIENA_LOCAL:
            ctxs, metas = build_or_load_ext(s, SIENA_DATA, procs=a.procs)
            check_repro_ext(s, ctxs, s)
            siena_ctxs[s] = ctxs
            ress = final_events(ctxs, HEAD)
            thrs = 5.0 * metas["sd"]
            exf = (lambda subj, fname, w, t, _s=s: ext_exceed_window(subj, "siena", 50.0,
                                                                     SIENA_DATA / _s / fname, w, t))
            seiz_rows += per_seizure_rows(ctxs, s, "siena-3of14", ress, exf, thrs)
            fa_rows += false_alarm_rows(ctxs, s, "siena-3of14", ress, exf, thrs)
        ext_ctxs.update(siena_ctxs)
        print(f"chb24 + Siena({len(SIENA_LOCAL)}/14): reproduced x1_external rows ({time.time()-t0:.0f}s)", flush=True)

    Seiz = pd.DataFrame(seiz_rows)
    FA = pd.DataFrame(fa_rows)
    Seiz.to_csv(OUT / "per_seizure.csv", index=False)
    FA.to_csv(OUT / "false_alarms.csv", index=False)

    # ---- item 2: duration bins ----
    dbin = pd.concat([duration_bin_counts(seiz_rows, s) for s in
                      ("development", "chb-test", "chb24", "siena-3of14")], ignore_index=True)
    dbin.to_csv(OUT / "duration_bins.csv", index=False)

    # ---- item 3: matched operating point ----
    sweep_tables = {}
    if not a.smoke:
        sweep_tables["chb-test"] = sweep_set(test_ctxs)
        sweep_tables["chb24"] = sweep_set({"chb24": ext_ctxs["chb24"]})
        sweep_tables["siena-3of14"] = sweep_set({s: ext_ctxs[s] for s in SIENA_LOCAL})
        for k, v in sweep_tables.items():
            v.to_csv(OUT / f"sweep_{k}.csv", index=False)
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(6, 4.5), dpi=150)
            for k, v in sweep_tables.items():
                v2 = v.dropna(subset=["pooled_fa", "pooled_sens"]).sort_values("pooled_fa")
                ax.plot(v2.pooled_fa, v2.pooled_sens, marker="o", ms=3, label=f"{k} (pooled)")
                v3 = v.dropna(subset=["pooled_fa", "patient_mean_sens"]).sort_values("pooled_fa")
                ax.plot(v3.pooled_fa, v3.patient_mean_sens, marker="x", ms=3, ls="--",
                        label=f"{k} (per-patient mean)")
            for fa in (20, 27.5, 44):
                ax.axvline(fa, color="#999999", lw=0.6, ls=":")
            ax.set_xlabel("FP/day"); ax.set_ylabel("sensitivity"); ax.set_xlim(0, 60)
            ax.legend(fontsize=7); ax.set_title("Matched operating point (detector stage, seed 42)")
            fig.tight_layout(); fig.savefig(OUT / "matched_operating_point.png"); plt.close(fig)
        except Exception as e:
            print(f"plot skipped: {e}", flush=True)

    # ---- item 4: Siena aggregate (all 14, from committed rows_*.csv) ----
    siena_rows = pd.concat([pd.read_csv(p) for p in sorted((ROOT / "results" / "x1_external").glob("rows_PN*.csv"))],
                           ignore_index=True)
    sa = siena_rows[(siena_rows.point == POINT) & (siena_rows.stage == "localized")]
    per_pat = sa.groupby("subject").apply(lambda d: pd.Series(dict(
        n_ref=d.n_ref.iloc[0], sens_mean=(d.tp / d.n_ref).mean(), fa_mean=(d.fp / d.nonict_h * 24).mean())))
    per_pat = per_pat.reset_index()
    few = per_pat[per_pat.n_ref <= 2].subject.tolist()
    sw = sa.groupby("seed").apply(lambda d: pd.Series(dict(tp=d.tp.sum(), n_ref=d.n_ref.sum())))
    pooled_sens_all = float((sw.tp / sw.n_ref).mean())
    sw2 = sa[~sa.subject.isin(few)].groupby("seed").apply(lambda d: pd.Series(dict(tp=d.tp.sum(), n_ref=d.n_ref.sum())))
    pooled_sens_ex = float((sw2.tp / sw2.n_ref).mean())
    siena_agg = dict(per_patient_mean_all=float(per_pat.sens_mean.mean()),
                     per_patient_mean_ex_le2=float(per_pat[~per_pat.subject.isin(few)].sens_mean.mean()),
                     pooled_sens_all=pooled_sens_all, pooled_sens_ex_le2=pooled_sens_ex,
                     n_patients_le2=len(few), patients_le2=few)
    per_pat.to_csv(OUT / "siena_per_patient.csv", index=False)
    json.dump(siena_agg, open(OUT / "siena_aggregate.json", "w"), indent=1)

    # ---- item 5: false-alarm anatomy summary ----
    fa_summary = None
    if len(FA):
        FA["high_amp"] = FA.share_high_amp >= 0.5
        fa_summary = FA.groupby(["set", "position", "high_amp"]).size().rename("n").reset_index()
        fa_summary.to_csv(OUT / "false_alarm_groups.csv", index=False)

    write_summary(Seiz, dbin, sweep_tables, siena_agg, FA, fa_summary, a.smoke, time.time() - t0)
    print(f"done in {time.time()-t0:.0f}s", flush=True)


def write_summary(Seiz, dbin, sweep_tables, siena_agg, FA, fa_summary, smoke, elapsed):
    L = ["# V9-T3 Part A -- failure anatomy of the final P3 frozen system (balanced point, localizer "
         f"{LOCALIZER}, seed 42), computed in v9\n",
         "Reproduction: development vs results/p3c_freeze/per_subject.csv, CHB-MIT test vs "
         "results/e23_test_look7/per_subject_seed.csv, chb24/Siena vs results/x1_external/rows_*.csv "
         "(4 seeds, detector + localized) -- all passed before any number below was computed.\n",
         f"**Data availability**: chb24's raw EDF (22 files) is fully present. Siena's raw EDF is present "
         f"for only {len(SIENA_LOCAL)}/14 patients in this checkout ({', '.join(SIENA_LOCAL)}); "
         f"{', '.join(SIENA_MISSING)} are absent, so every Siena number tagged 'siena-3of14' below is "
         "restricted to those 3 patients and is NOT the full Siena set (item 4, the aggregate check, "
         "needs no raw data and uses all 14 from the committed results/x1_external/rows_PN*.csv).\n"]
    if smoke:
        L.append("**SMOKE run**: 1 development subject, 1 test subject only; chb24/Siena/sweep skipped.\n")

    L += ["## 1-2. Per-seizure table and duration bins (computed in v9: results/v9_anatomy/per_seizure.csv, "
          "duration_bins.csv)\n", "```", dbin.to_string(index=False) if len(dbin) else "(none)", "```"]
    if len(Seiz):
        for s in ("chb-test", "chb24", "siena-3of14"):
            d = Seiz[Seiz.set == s]
            if not len(d):
                continue
            n, caught = len(d), int(d.caught.sum())
            L.append(f"\n{s}: {caught}/{n} seizures caught after the localizer (seed 42, E1 overlap "
                     f"rule -- p2_scalars.caught, a descriptive per-seizure count; the reproduction "
                     f"gate above checks the official SzCORE tp/fp used for sensitivity, which can "
                     f"differ by about 1 seizure from this count on sets with split/merged events). "
                     f"Missed seizures' median p_need = {d[~d.caught].p_need.median():.4f} "
                     f"(n={int((~d.caught).sum())}).")

    L += ["\n## 3. Matched operating point (characterisation, detector stage, seed 42, "
          "results/v9_anatomy/sweep_*.csv, matched_operating_point.png)\n"]
    if sweep_tables:
        for k, v in sweep_tables.items():
            pts = interp_at_fa(v, (20, 27.5, 44))
            L.append(f"- {k}: sensitivity @ FP/day " + ", ".join(
                f"{t:g}={pts[t]:.3f}" if pts[t] == pts[t] else f"{t:g}=out of range" for t in pts))
    else:
        L.append("(skipped in --smoke)")

    L += ["\n## 4. Siena aggregate check, all 14 patients (results/v9_anatomy/siena_per_patient.csv, "
          "siena_aggregate.json)\n", "```", json.dumps(siena_agg, indent=1), "```"]

    L += ["\n## 5. False-alarm anatomy (results/v9_anatomy/false_alarms.csv, false_alarm_groups.csv)\n"]
    if len(FA):
        L += ["```", fa_summary.to_string(index=False), "```",
              f"\nMedian FP duration {FA.duration_s.median():.0f} s; "
              f"share with >=1 high-amplitude window >= 50% of the event: {float(FA.high_amp.mean()):.2%}; "
              f"top channel mode: {FA.top_channel.mode().iloc[0] if len(FA.top_channel.mode()) else 'n/a'}; "
              f"median distance to the nearest reference seizure (within file): "
              f"{FA.dist_to_seizure_s.median():.0f} s (n with a seizure in the same file = "
              f"{int(FA.dist_to_seizure_s.notna().sum())}/{len(FA)})."]
    else:
        L.append("(skipped in --smoke)")

    L.append("\n## Findings (computed in v9)\n")
    findings = []
    if len(Seiz):
        for s in ("chb-test", "chb24", "siena-3of14"):
            d = Seiz[Seiz.set == s]
            if len(d):
                findings.append(f"- [{s}, per_seizure.csv] {int(d.caught.sum())}/{len(d)} seizures caught "
                                f"after the localizer (seed 42, balanced point).")
    findings.append(f"- [duration_bins.csv] " + "; ".join(
        f"{r.set}/{r.bin}: {r.caught}/{r.n}" for _, r in dbin.iterrows() if r.n))
    if sweep_tables:
        for k, v in sweep_tables.items():
            pts = interp_at_fa(v, (27.5,))
            if pts[27.5] == pts[27.5]:
                findings.append(f"- [{k}, sweep_{k}.csv] sensitivity {pts[27.5]:.3f} at FP/day 27.5 "
                                f"(CHB-MIT test's own balanced-point rate), global budget, detector stage.")
    findings.append(f"- [siena_aggregate.json] pooled sensitivity {siena_agg['pooled_sens_all']:.3f} vs "
                    f"per-patient mean {siena_agg['per_patient_mean_all']:.3f} (all 14); excluding the "
                    f"{siena_agg['n_patients_le2']} patients with <=2 seizures: pooled "
                    f"{siena_agg['pooled_sens_ex_le2']:.3f} vs per-patient mean "
                    f"{siena_agg['per_patient_mean_ex_le2']:.3f}.")
    if len(FA):
        fa_by_set = ", ".join(f"{s}={int((FA.set == s).sum())}" for s in FA.set.unique())
        findings.append(f"- [false_alarms.csv] {len(FA)} false alarms (seed 42, balanced, after the "
                        f"localizer: {fa_by_set}); {float(FA.high_amp.mean()):.0%} have >=1 "
                        f"high-amplitude channel in at least half their windows.")
    L += findings
    L.append(f"\nElapsed {elapsed:.0f} s.")
    (OUT / "SUMMARY.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
