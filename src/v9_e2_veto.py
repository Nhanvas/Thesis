#!/usr/bin/env python
"""
v9_e2_veto.py -- V9-E2 (docs/prompts/V9_E2_ARTIFACT_VETO.md).

PART 0 (results/v9_e2/paired/, reads results/v9_e1b/ only, no new model):
  1. Re-print every duration-bin table at seed 42 only, for every arm (results/v9_e1b/duration_bins.csv
     sums G/F over all 4 seeds but B4 over one -- not comparable as printed).
  2. Paired patient bootstrap (B=10,000, same resampled patients for both arms) of the DIFFERENCE in
     per-patient-mean sensitivity at matched FP/day 20/27.5/44 on the system-stage curve
     (results/v9_e1b/sys_sweep.csv), B4-G and F-G, per set (dev, test, Siena-14; chb24 excluded, n=1).
  3. Same paired bootstrap for per-patient-mean F1 at each arm's own calibrated point
     (results/v9_e1b/per_subject.csv, headline seed 42 for G/F).

PART A (results/v9_e2/, one subject per OS process like V9_T4/V9-E1b -- same reason: memory freed
between subjects): veto of competing (muscle/movement/electrode) anomalies.
  Candidate event features, computed on the REAL, pipeline-filtered 18-channel signal of each
  hypothesis event (TP or FP, labelled by the SAME "E1 overlap rule" p2_scalars.caught() already
  uses: a hypothesis event is TP if it overlaps [ref_onset-30s, ref_offset+60s] of ANY reference
  seizure, else FP), label-free:
    f1 high-frequency share: median over channels of Welch power 30-60 Hz / power 0.5-60 Hz (the
       pipeline's own passband stands in for "1-60 Hz" -- nothing outside it survives the filter
       anyway, so a literal 1 Hz low edge is not recoverable and not meaningfully different).
    f2 spatial extent: share of the 18 channels whose median |z| (z = filtered uV / the committed
       label-free per-channel SD) exceeds 5, over the event's own samples.
    f3 frontal-polar dominance: Welch power (0.5-60 Hz) of {FP1-F7,FP1-F3,FP2-F4,FP2-F8} / power of
       all 18 channels.
    f4 single-channel dominance: max channel power / median channel power (same 0.5-60 Hz Welch power).
    f5 event duration (s).
  Raw signal access reuses raw_eeg_view.read_raw (CHB-MIT) / x1_external.load_18 (chb24, Siena) via
  v9_anatomy's own file cache (v9_anatomy._RAW) -- one file load per (subject, file), not per event --
  and the SAME filtfilt+notch convention as raw_eeg_view.read_segment / v9_eeg_samples.ext_read_segment
  (re-implemented here only to add the per-process file cache those two don't need for a handful of
  hand-picked panels but this script does for thousands of events).

  Selection protocol (development patients only, pre-registered in the prompt):
    1. Every event on development patients, 3 arms (G, B4, F) each at its OWN V9-E1b calibrated point,
       labelled TP/FP.
    2. Per feature, AUROC (TP vs FP), pooled over that arm's patients and seeds; the feature with the
       highest mean AUROC (as discriminative power, i.e. max(auc, 1-auc)) averaged over the 3 arms
       wins; its direction (which side associates with FP) is read off the SIGN of the mean signed AUROC.
    3. Per arm, threshold = the most aggressive cut on that feature, in that direction, that keeps
       >= 95% of the arm's OWN development true detections.
    4. Applied ONCE (no re-tuning) to CHB-MIT test, chb24, Siena-14: vetoed events are deleted outright
       (the budget is not refilled; precision necessarily improves at some sensitivity cost).
  Disclosed once, here and in the report: the threshold is picked using development LABELS -- a
  validation-set hyperparameter, exactly like every other frozen constant in this pipeline (k, floor,
  cap, smoothing, merge). The anomaly-detection MODEL itself never sees a seizure label.

READ-ONLY REUSE: v9_e1b_calibrate.py (k_G/k_B4/k_F, one_pass, m_of/x_of/f_signals, ARMS, ALL_SUBS,
SET_OF -- itself built on v9_e1_baselines.py, p3_levers.py, e18_cpd_localizer.py, p2_scalars.py, all
unmodified), v9_anatomy.py (its _RAW file cache, CH_NAMES, CHB_DATA/SIENA_DATA paths, build_or_load_ext
for the Siena/chb24 label-free per-channel SD), raw_eeg_view.py (read_raw, subject_thresholds),
x1_external.py (load_18, filters).

Run:  python src/v9_e2_veto.py --part0                    (fast; Part 0 only, no raw EEG)
      python src/v9_e2_veto.py --smoke                     (chb01, chb10, chb03; ~1-3 min)
      python src/v9_e2_veto.py --eval-one SUBJ              (one subject, one process; Part A events)
      python src/v9_e2_veto.py --select                     (Part A steps 1-3, development only)
      python src/v9_e2_veto.py --apply                       (Part A step 4 + before/after report)
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import welch, sosfiltfilt, filtfilt
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB", ROOT / "src" / "phaseC",
          ROOT / "src" / "dataprep"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import v9_e1b_calibrate as V9E1B        # noqa: E402 -- read-only reuse (patches v9_e1_baselines.EXT)
import v9_anatomy as V9A                # noqa: E402
import p2_scalars as PS                 # noqa: E402
import p3_levers as P3L                 # noqa: E402
import raw_eeg_view as RV               # noqa: E402

V9E1 = V9E1B.V9E1
P = V9A.P
X1 = V9A.X1

OUT = ROOT / "results" / "v9_e2"
PARTS = OUT / "_parts"
PAIRED = OUT / "paired"
E1B = ROOT / "results" / "v9_e1b"

ARMS = V9E1B.ARMS                       # ["G", "B4", "F"]
TAGS = V9E1B.TAGS
DEV = V9E1B.DEV
TEST = V9E1B.TEST
SIENA_ALL_14 = V9E1B.SIENA_ALL_14
ALL_SUBS = V9E1B.ALL_SUBS
SET_OF = V9E1B.SET_OF
FLOOR, CAP, SMOOTH = V9E1B.FLOOR, V9E1B.CAP, V9E1B.SMOOTH
FEATURES = ["f1", "f2", "f3", "f4", "f5"]
FRONTAL = ["FP1-F7", "FP1-F3", "FP2-F4", "FP2-F8"]
CH_NAMES = V9A.CH_NAMES
NOTCH_OF = {"chb24": 60.0, **{s: 50.0 for s in SIENA_ALL_14}}
FP_TARGETS = V9E1B.FP_TARGETS
K_MULT = V9E1B.K_MULT


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


# ============================================================================ raw segment access
def chb_event_segment(subj, fname, t0_s, t1_s):
    key = ("chb", subj, fname)

    def loader():
        raw = RV.read_raw(V9A.CHB_DATA / subj / fname, allow_missing=True)
        if raw is None:
            return None
        return raw.get_data(), int(raw.n_times)
    cached = V9A._RAW.get(key, loader)
    if cached is None:
        return None
    data, n_total = cached
    s = max(0, int(round(t0_s * P.FS)))
    e = min(n_total, int(round(t1_s * P.FS)))
    if e <= s:
        return None
    ps, pe = max(0, s - P.FILTER_PAD), min(n_total, e + P.FILTER_PAD)
    seg = data[:, ps:pe]
    bp = sosfiltfilt(P._BP_SOS, seg, axis=1)
    notched = filtfilt(P._NOTCH_B, P._NOTCH_A, bp, axis=1)
    off = s - ps
    return notched[:, off:off + (e - s)] * 1e6


def ext_event_segment(s, kind, notch, path, t0_s, t1_s):
    key = ("x1", s, str(path))

    def loader():
        return X1.load_18(path, kind)
    data = V9A._RAW.get(key, loader)
    if data is None:
        return None
    n_total = data.shape[1]
    s0 = max(0, int(round(t0_s * P.FS)))
    e0 = min(n_total, int(round(t1_s * P.FS)))
    if e0 <= s0:
        return None
    ps, pe = max(0, s0 - P.FILTER_PAD), min(n_total, e0 + P.FILTER_PAD)
    seg = data[:, ps:pe]
    sos, b, a = X1.filters(notch)
    bp = sosfiltfilt(sos, seg, axis=1)
    notched = filtfilt(b, a, bp, axis=1)
    off = s0 - ps
    return notched[:, off:off + (e0 - s0)] * 1e6


def subject_sd_uV(s):
    """label-free per-channel SD, microvolts -- same stats the pipeline's own 5xSD artifact flag uses."""
    if s in SET_OF and SET_OF[s] in ("chb24", "siena14"):
        data_root = V9A.CHB_DATA if s == "chb24" else V9A.SIENA_DATA
        _, meta = V9A.build_or_load_ext(s, data_root)
        return np.asarray(meta["sd"], dtype=np.float64) * 1e6
    _, sd_v, st = RV.subject_thresholds(s)
    return np.asarray(st["ch_std_uV"], dtype=np.float64)


# ============================================================================ event features
def spectral_features(seg_uV):
    n = seg_uV.shape[1]
    if n < 8:
        return None
    nperseg = min(n, 512)
    freqs, psd = welch(seg_uV, fs=P.FS, nperseg=nperseg, axis=1)

    def bp(lo, hi):
        m = (freqs >= lo) & (freqs < hi)
        return psd[:, m].sum(axis=1) if m.any() else np.zeros(psd.shape[0])
    p_total = bp(0.5, 60.0)
    p_gamma = bp(30.0, 60.0)
    f1 = float(np.median(p_gamma / np.maximum(p_total, 1e-12)))
    idx = [CH_NAMES.index(c) for c in FRONTAL if c in CH_NAMES]
    f3 = float(p_total[idx].sum() / max(p_total.sum(), 1e-12)) if idx else float("nan")
    f4 = float(p_total.max() / max(np.median(p_total), 1e-12))
    return f1, f3, f4


def amplitude_feature(seg_uV, sd_uV):
    z = np.abs(seg_uV) / np.maximum(sd_uV[:, None], 1e-6)
    med = np.median(z, axis=1)
    return float((med > 5).mean())


def event_features(s, setname, f_idx, a_s, b_s, files, sd_uV):
    fname = str(files[f_idx]) if files is not None and f_idx < len(files) else None
    if setname == "dev" or setname == "test":
        seg = chb_event_segment(s, fname, a_s, b_s) if fname else None
    else:
        kind = "chb" if setname == "chb24" else "siena"
        notch = NOTCH_OF[s]
        data_root = V9A.CHB_DATA if s == "chb24" else V9A.SIENA_DATA
        path = data_root / s / fname
        seg = ext_event_segment(s, kind, notch, path, a_s, b_s) if fname else None
    if seg is None or seg.shape[1] < 8:
        return dict(f1=np.nan, f2=np.nan, f3=np.nan, f4=np.nan, f5=float(b_s - a_s))
    spec = spectral_features(seg)
    f1, f3, f4 = spec if spec is not None else (np.nan, np.nan, np.nan)
    f2 = amplitude_feature(seg, sd_uV)
    return dict(f1=f1, f2=f2, f3=f3, f4=f4, f5=float(b_s - a_s))


# ============================================================================ TP/FP labelling (E1 overlap rule)
def label_events(loc, refs):
    """per-hypothesis-event label, the SAME rule as p2_scalars.caught(): TP if it overlaps
    [ref_onset-30s, ref_offset+60s] of any reference in its file, else FP. Returns
    (f, a, b, label, matched_ref_dur_or_nan)."""
    out = []
    for f, evs in loc.items():
        rr = refs.get(f, [])
        for a, b in evs:
            m = [(ra, rb) for ra, rb in rr if b >= ra - 30 and a <= rb + 60]
            if m:
                ra, rb = min(m, key=lambda x: x[0])
                out.append((f, a, b, "TP", float(rb - ra)))
            else:
                out.append((f, a, b, "FP", np.nan))
    return out


# ============================================================================ Part A: --eval-one
def eval_one(s):
    """budget+CPD (one_pass) is run per arm-seed first (fast, no raw EEG); every resulting event,
    across ALL arm-seeds, is then processed FILE BY FILE (not arm-seed by arm-seed) so each raw EDF
    is decoded exactly once regardless of how many arm-seeds reference it -- some CHB-MIT subjects
    (chb01: 42 files) would otherwise have their files re-decoded up to 9x (4 G seeds + B4 + 4 F
    seeds), the dominant cost once budget caches already exist."""
    t0 = time.time()
    cal = json.load(open(E1B / "calibration.json"))
    ctx = V9E1.subject_ctx(s)
    Db = V9E1.load_D(s, "B4")
    refs = P3L.refs_of(ctx)
    files = ctx["z"]["files"] if "files" in ctx["z"] else None
    sd_uV = subject_sd_uV(s)
    setname = SET_OF[s]

    labeled = []   # (arm, seed, file, onset_s, offset_s, label, ref_dur)

    def compute(arm, seed, x, m, k):
        _, det, loc, _ = V9E1B.one_pass(ctx, x, k, m, refs)
        for f_, a_, b_, label, ref_dur in label_events(loc, refs):
            labeled.append((arm, seed, f_, a_, b_, label, ref_dur))

    for tag in TAGS:
        Dg = ctx["D"][tag]
        compute("G", tag, V9E1B.x_of(ctx, Dg), V9E1B.m_of(ctx, Dg), cal["k_G"])

    compute("B4", "-", V9E1B.x_of(ctx, Db), V9E1B.m_of(ctx, Db), cal["k_B4"])

    for tag in TAGS:
        Dg = ctx["D"][tag]
        xf, mf = V9E1B.f_signals(ctx, Dg, Db)
        compute("F", tag, xf, mf, cal["k_F"])

    by_file = {}
    for item in labeled:
        by_file.setdefault(item[2], []).append(item)

    events = []
    for f_ in sorted(by_file):
        for arm, seed, _f, a_, b_, label, ref_dur in by_file[f_]:
            feats = event_features(s, setname, f_, a_, b_, files, sd_uV)
            events.append(dict(subject=s, set=setname, arm=arm, seed=seed, file=int(f_),
                               onset_s=float(a_), offset_s=float(b_), label=label,
                               ref_dur=ref_dur, **feats))

    PARTS.mkdir(parents=True, exist_ok=True)
    (PARTS / f"{s}.json").write_text(json.dumps(_native(dict(events=events))), encoding="utf-8")
    print(f"eval-one {s}: {len(events)} events, done in {time.time() - t0:.0f}s, "
          f"peak RAM {_peak_ram_mb():.0f} MB", flush=True)


# ============================================================================ Part A: --select (development only)
def load_events(subs):
    rows = []
    for s in subs:
        fp = PARTS / f"{s}.json"
        if not fp.exists():
            raise SystemExit(f"STOP: missing event part file for {s} -- run --eval-one {s} first")
        rows += json.loads(fp.read_text())["events"]
    return pd.DataFrame(rows)


def auroc_table(E, subs, arms=ARMS):
    """per feature, per arm: pooled AUROC (TP=1) over `subs`' events. Returns DataFrame."""
    rows = []
    for arm in arms:
        d = E[(E.subject.isin(subs)) & (E.arm == arm)]
        y = (d.label == "TP").astype(int).values
        if y.sum() == 0 or (1 - y).sum() == 0:
            continue
        for feat in FEATURES:
            v = d[feat].values
            ok = np.isfinite(v)
            if ok.sum() < 10 or len(set(y[ok])) < 2:
                continue
            auc = float(roc_auc_score(y[ok], v[ok]))
            rows.append(dict(arm=arm, feature=feat, auc=auc, n=int(ok.sum())))
    return pd.DataFrame(rows)


def select():
    t0 = time.time()
    E = load_events(DEV)
    E.to_csv(OUT / "events_dev.csv", index=False)
    auc = auroc_table(E, DEV)
    auc.to_csv(OUT / "auroc_dev.csv", index=False)
    mean_power = auc.assign(power=lambda d: np.maximum(d.auc, 1 - d.auc)).groupby("feature").power.mean()
    mean_signed = auc.groupby("feature").auc.mean()
    best_feat = mean_power.idxmax()
    direction = "high_is_fp" if mean_signed[best_feat] < 0.5 else "low_is_fp"

    thresholds = {}
    for arm in ARMS:
        d = E[(E.subject.isin(DEV)) & (E.arm == arm) & (E.label == "TP")]
        v = d[best_feat].values
        v = v[np.isfinite(v)]
        if not len(v):
            thresholds[arm] = None
            continue
        pct = 95.0 if direction == "high_is_fp" else 5.0
        thresholds[arm] = float(np.percentile(v, pct))

    sel = dict(feature=best_feat, direction=direction, mean_power=float(mean_power[best_feat]),
              mean_signed_auc=float(mean_signed[best_feat]), thresholds=thresholds,
              mean_power_all_features={k: float(v) for k, v in mean_power.items()},
              elapsed_s=time.time() - t0)
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(sel, open(OUT / "selection.json", "w"), indent=1)
    print(f"selected feature: {best_feat} (direction {direction}, mean AUROC power "
          f"{mean_power[best_feat]:.3f}); per-arm thresholds: {thresholds}", flush=True)
    print(f"all features' mean AUROC power: {dict(mean_power.round(3))}", flush=True)
    return sel


def vetoed(row, feat, direction, thr):
    v = row[feat]
    if thr is None or not np.isfinite(v):
        return False
    return v > thr if direction == "high_is_fp" else v < thr


# ============================================================================ Part A: --apply
def rescored(ctx, loc_events, keep_mask):
    """rebuild a per-file event dict from a (filtered) flat event list, then PS.score it."""
    out = {}
    for ev, keep in zip(loc_events, keep_mask):
        if not keep:
            continue
        out.setdefault(ev["file"], []).append((ev["onset_s"], ev["offset_s"]))
    return PS.score(ctx, out)


def apply_veto():
    t0 = time.time()
    sel = json.load(open(OUT / "selection.json"))
    feat, direction, thr = sel["feature"], sel["direction"], sel["thresholds"]
    E = load_events(ALL_SUBS)
    E.to_csv(OUT / "events_all.csv", index=False)
    E["vetoed"] = [vetoed(r, feat, direction, thr.get(r["arm"])) for _, r in E.iterrows()]

    before_ref = pd.read_csv(E1B / "per_subject.csv")
    before_rows, after_rows, lost_rows = [], [], []
    for s in ALL_SUBS:
        ctx = V9E1.subject_ctx(s)
        shorts = PS.short_refs(ctx)
        for arm in ARMS:
            seeds = TAGS if arm in ("G", "F") else ["-"]
            for seed in seeds:
                d = E[(E.subject == s) & (E.arm == arm) & (E.seed == seed)]
                events = d.to_dict("records")
                keep_all = [True] * len(events)
                keep_after = [not e["vetoed"] for e in events]
                for keep, bucket in ((keep_all, before_rows), (keep_after, after_rows)):
                    per_file = {}
                    for ev, k in zip(events, keep):
                        if k:
                            per_file.setdefault(ev["file"], []).append((ev["onset_s"], ev["offset_s"]))
                    tp, fp, nr, h = PS.score(ctx, per_file)
                    kk, ns = PS.caught(shorts, per_file)
                    bucket.append(dict(subject=s, arm=arm, seed=seed, stage="localized",
                                       tp=tp, fp=fp, n_ref=nr, nonict_h=h, short_tp=kk, short_n=ns))
                for ev in events:
                    if ev["label"] == "TP" and ev["vetoed"]:
                        lost_rows.append(dict(subject=s, set=SET_OF[s], arm=arm, seed=seed,
                                              ref_dur=ev["ref_dur"], onset_s=ev["onset_s"],
                                              offset_s=ev["offset_s"]))
        print(f"  {s}: scored before/after ({time.time() - t0:.0f}s)", flush=True)

    Rb, Ra = pd.DataFrame(before_rows), pd.DataFrame(after_rows)
    Rb.to_csv(OUT / "per_subject_before.csv", index=False)
    Ra.to_csv(OUT / "per_subject_after.csv", index=False)
    pd.DataFrame(lost_rows).to_csv(OUT / "lost_seizures.csv", index=False)

    # sanity gate: "before" must reproduce v9_e1b's own committed localized-stage numbers exactly
    bad = []
    for _, r in Rb.iterrows():
        ref = before_ref[(before_ref.subject == r.subject) & (before_ref.arm == r.arm) &
                         (before_ref.seed == r.seed) & (before_ref.stage == "localized")]
        if not len(ref):
            continue
        rr = ref.iloc[0]
        if (int(r.tp), int(r.fp)) != (int(rr.tp), int(rr.fp)):
            bad.append((r.subject, r.arm, r.seed, int(r.tp), int(r.fp), int(rr.tp), int(rr.fp)))
    if bad:
        raise SystemExit(f"STOP: before-veto rescoring does not reproduce v9_e1b/per_subject.csv: {bad[:5]}")
    print(f"gate OK: before-veto rescoring reproduces results/v9_e1b/per_subject.csv exactly "
          f"({len(Rb)} rows checked).", flush=True)

    auc_test_siena = auroc_table(E, TEST + SIENA_ALL_14)
    auc_test_siena.to_csv(OUT / "auroc_test_siena.csv", index=False)
    print(f"apply_veto done in {time.time() - t0:.0f}s", flush=True)
    return Rb, Ra, pd.DataFrame(lost_rows), auc_test_siena, sel


# ============================================================================ Part 0
def duration_bins_seed42():
    DB = pd.read_csv(E1B / "duration_bins.csv")
    rows = []
    for setname in ("dev", "test", "chb24", "siena14"):
        for arm in ARMS:
            seed = "clean_seed42" if arm in ("G", "F") else "-"
            d = DB[(DB.set == setname) & (DB.arm == arm) & (DB.seed == seed)]
            g = d.groupby(["lo", "hi"])[["caught", "n"]].sum().reset_index()
            for _, r in g.iterrows():
                rows.append(dict(set=setname, arm=arm, lo=r.lo, hi=r.hi, caught=int(r.caught), n=int(r.n)))
    out = pd.DataFrame(rows)
    PAIRED.mkdir(parents=True, exist_ok=True)
    out.to_csv(PAIRED / "duration_bins_seed42.csv", index=False)
    return out


def per_patient_sens_at_fa(SYS, subs, arm, target_fa):
    d = SYS[(SYS.subject.isin(subs)) & (SYS.arm == arm)]
    seeds = sorted(d.seed.unique())
    acc = {}
    for sd in seeds:
        dd = d[d.seed == sd]
        pooled = dd.groupby("k_mult")[["tp", "fp", "n_ref", "nonict_h"]].sum().reset_index()
        pooled["fa"] = pooled.fp / pooled.nonict_h * 24
        pooled = pooled.sort_values("fa").reset_index(drop=True)
        if len(pooled) < 2 or target_fa < pooled.fa.min() or target_fa > pooled.fa.max():
            continue
        pos = int(np.searchsorted(pooled.fa.values, target_fa))
        pos = min(max(pos, 1), len(pooled) - 1)
        lo_row, hi_row = pooled.iloc[pos - 1], pooled.iloc[pos]
        frac = 0.0 if hi_row.fa == lo_row.fa else (target_fa - lo_row.fa) / (hi_row.fa - lo_row.fa)
        km_lo, km_hi = lo_row.k_mult, hi_row.k_mult
        dd2 = dd[dd.k_mult.isin([km_lo, km_hi])]
        piv = dd2.pivot_table(index="subject", columns="k_mult", values=["tp", "n_ref"])
        sens_lo = piv[("tp", km_lo)] / piv[("n_ref", km_lo)]
        sens_hi = piv[("tp", km_hi)] / piv[("n_ref", km_hi)]
        sens_interp = (1 - frac) * sens_lo + frac * sens_hi
        for subj, v in sens_interp.items():
            acc.setdefault(subj, []).append(v)
    if not acc:
        return pd.Series(dtype=float)
    return pd.Series({s: float(np.mean(v)) for s, v in acc.items()})


def paired_boot(a, b, n=10_000, seed=0):
    rng = np.random.default_rng(seed)
    subs = sorted(set(a.index) & set(b.index))
    av, bv = a.loc[subs].values, b.loc[subs].values
    N = len(subs)
    diffs = np.empty(n)
    for i in range(n):
        idx = rng.integers(0, N, N)
        diffs[i] = av[idx].mean() - bv[idx].mean()
    return dict(mean_diff=float(diffs.mean()), ci_lo=float(np.percentile(diffs, 2.5)),
               ci_hi=float(np.percentile(diffs, 97.5)), share_gt0=float((diffs > 0).mean()), n_patients=N)


def paired_f1_at_point(R, subs, arm, headline="clean_seed42"):
    d = R[(R.subject.isin(subs)) & (R.arm == arm) & (R.stage == "localized")]
    if arm in ("G", "F"):
        d = d[d.seed == headline]
    d = d.assign(f1=2 * d.tp / (2 * d.tp + d.fp + (d.n_ref - d.tp)))
    return d.set_index("subject").f1


def part0():
    t0 = time.time()
    db = duration_bins_seed42()
    PAIRED.mkdir(parents=True, exist_ok=True)

    SYS = pd.read_csv(E1B / "sys_sweep.csv")
    sens_rows = []
    for setname, subs in (("dev", DEV), ("test", TEST), ("siena14", SIENA_ALL_14)):
        g_sens = {t: per_patient_sens_at_fa(SYS, subs, "G", t) for t in FP_TARGETS}
        for arm in ("B4", "F"):
            a_sens = {t: per_patient_sens_at_fa(SYS, subs, arm, t) for t in FP_TARGETS}
            for t in FP_TARGETS:
                if not len(g_sens[t]) or not len(a_sens[t]):
                    sens_rows.append(dict(set=setname, pair=f"{arm}-G", fa_target=t, mean_diff=np.nan,
                                          ci_lo=np.nan, ci_hi=np.nan, share_gt0=np.nan, n_patients=0))
                    continue
                r = paired_boot(a_sens[t], g_sens[t])
                sens_rows.append(dict(set=setname, pair=f"{arm}-G", fa_target=t, **r))
    SENS = pd.DataFrame(sens_rows)
    SENS.to_csv(PAIRED / "paired_sens.csv", index=False)

    R = pd.read_csv(E1B / "per_subject.csv")
    f1_rows = []
    for setname, subs in (("dev", DEV), ("test", TEST), ("siena14", SIENA_ALL_14)):
        g_f1 = paired_f1_at_point(R, subs, "G")
        for arm in ("B4", "F"):
            a_f1 = paired_f1_at_point(R, subs, arm)
            r = paired_boot(a_f1, g_f1)
            f1_rows.append(dict(set=setname, pair=f"{arm}-G", **r))
    F1 = pd.DataFrame(f1_rows)
    F1.to_csv(PAIRED / "paired_f1.csv", index=False)

    print(f"Part 0 done in {time.time() - t0:.0f}s -> {PAIRED}", flush=True)
    return db, SENS, F1


# ============================================================================ report
def fmt_dur_table(db, setname):
    L = ["```", "arm                                    <=20s      21-40s     41-80s     >80s"]
    for arm in ARMS:
        d = db[(db.set == setname) & (db.arm == arm)].set_index(["lo", "hi"])
        cells = []
        for lo, hi in V9E1.DUR_BINS:
            if (lo, hi) in d.index:
                r = d.loc[(lo, hi)]
                cells.append(f"{int(r.caught)}/{int(r.n)}" if r.n else "-")
            else:
                cells.append("-")
        L.append(f"{V9E1B.ARM_LABEL[arm]:38s} " + "  ".join(f"{c:9s}" for c in cells))
    L.append("```")
    return L


def fmt_paired_table(df, label):
    L = [f"\n{label}\n```"]
    for _, r in df.iterrows():
        extra = f"fa_target={r.fa_target:g} " if "fa_target" in df.columns else ""
        L.append(f"{r.set:10s} {r.pair:6s} {extra}mean diff {r.mean_diff:+.3f}  95% CI "
                 f"[{r.ci_lo:+.3f}, {r.ci_hi:+.3f}]  P(diff>0) {r.share_gt0:.3f}  (n={r.n_patients})")
    L.append("```")
    return L


def before_after_section(L, Rb, Ra, subs, setname, title):
    L.append(f"\n## {title} ({len(subs)} patients)\n")
    for label, R in (("before veto", Rb), ("after veto", Ra)):
        L += [f"### {label}\n", "```",
             "arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day"]
        for arm in ARMS:
            s = V9E1.arm_summary(R, subs, arm)
            L.append(V9E1.fmt_arm_row(V9E1B.ARM_LABEL[arm], s))
        L.append("```")
    return L


def build_report():
    db = pd.read_csv(PAIRED / "duration_bins_seed42.csv") if (PAIRED / "duration_bins_seed42.csv").exists() else None
    sens_p = pd.read_csv(PAIRED / "paired_sens.csv") if (PAIRED / "paired_sens.csv").exists() else None
    f1_p = pd.read_csv(PAIRED / "paired_f1.csv") if (PAIRED / "paired_f1.csv").exists() else None
    has_part_a = (OUT / "selection.json").exists() and (OUT / "per_subject_after.csv").exists()

    L = ["# V9-E2 -- paired comparison + competing-anomaly (artifact) veto\n",
         "Full tables: `results/v9_e2/*.csv`, `results/v9_e2/paired/*.csv`. Code: `src/v9_e2_veto.py` "
         "(new; reuses src/v9_e1b_calibrate.py, src/v9_e1_baselines.py, src/v9_anatomy.py and every "
         "frozen script they call, read-only).\n",
         "## Part 0 -- fixes and paired statistics on the existing V9-E1b outputs\n"]

    if db is not None:
        L.append("### Duration-bin tables, seed 42 only for every arm (B4 is deterministic; "
                 "results/v9_e1b's own table summed G/F over 4 seeds, not comparable to B4's one)\n")
        for setname, title in (("dev", "development"), ("test", "CHB-MIT test"), ("chb24", "chb24"),
                               ("siena14", "Siena-14")):
            L.append(f"\n**{title}**")
            L += fmt_dur_table(db, setname)

    if sens_p is not None:
        L += fmt_paired_table(sens_p, "### Paired bootstrap (B=10,000): per-patient-mean sensitivity "
                              "difference at matched FP/day, system-stage curve (chb24 excluded, n=1)")
    if f1_p is not None:
        L += fmt_paired_table(f1_p, "### Paired bootstrap (B=10,000): per-patient-mean F1 difference, "
                              "each arm's OWN calibrated point (chb24 excluded, n=1)")

    L.append("\n## Part A -- veto of competing anomalies (pre-registered on development, applied once)\n")
    if has_part_a:
        sel = json.load(open(OUT / "selection.json"))
        auc_dev = pd.read_csv(OUT / "auroc_dev.csv")
        auc_ts = pd.read_csv(OUT / "auroc_test_siena.csv")
        Rb = pd.read_csv(OUT / "per_subject_before.csv")
        Ra = pd.read_csv(OUT / "per_subject_after.csv")
        lost = pd.read_csv(OUT / "lost_seizures.csv")

        L += [f"Selected feature: **{sel['feature']}** (direction: veto events where the feature is "
             f"{'HIGH' if sel['direction'] == 'high_is_fp' else 'LOW'}; mean AUROC power "
             f"{sel['mean_power']:.3f}, mean signed AUROC {sel['mean_signed_auc']:.3f}, averaged over "
             "G/B4/F on development). Threshold per arm (development, keeps >=95% of that arm's own "
             f"true detections): {json.dumps(sel['thresholds'])}.\n",
             "Disclosure: the threshold uses development LABELS (a validation-set hyperparameter, same "
             "status as k/floor/cap/smoothing/merge elsewhere in this pipeline); the anomaly-detection "
             "model itself never sees a seizure label.\n",
             "\n### AUROC table, every candidate feature, development (TP vs FP, pooled per arm)\n",
             "```", auc_dev.pivot(index="feature", columns="arm", values="auc").round(3).to_string(), "```",
             "\n### Same AUROCs measured on CHB-MIT test + Siena-14 (descriptive only, NOT used to "
             "pick the feature or threshold)\n",
             "```", auc_ts.pivot(index="feature", columns="arm", values="auc").round(3).to_string(), "```"]

        before_after_section(L, Rb, Ra, DEV, "dev", "Development")
        before_after_section(L, Rb, Ra, TEST, "test", "CHB-MIT held-out test")
        before_after_section(L, Rb, Ra, ["chb24"], "chb24", "chb24")
        before_after_section(L, Rb, Ra, SIENA_ALL_14, "siena14", "Siena, all 14 patients")

        L.append("\n### Seizures lost to the veto (true detections whose only matching event was "
                 "vetoed; subject, set, arm, seed, reference-seizure duration)\n")
        if len(lost):
            L += ["```", lost[["subject", "set", "arm", "seed", "ref_dur"]].sort_values(
                ["set", "arm", "ref_dur"]).to_string(index=False), "```"]
        else:
            L.append("(none)")
    else:
        L.append("Part A not yet run: `--eval-one SUBJ` for every subject, then `--select`, then "
                 "`--apply`.")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "SUMMARY.md").write_text("\n".join(L), encoding="utf-8")
    inbox = ROOT.parent / "Agent" / "inbox" / "V9_E2_REPORT.md"
    inbox.parent.mkdir(parents=True, exist_ok=True)
    inbox.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))
    print(f"\nWrote results/v9_e2/SUMMARY.md and {inbox}")


# ============================================================================ smoke
def smoke():
    t0 = time.time()
    for s in ["chb01", "chb10", "chb03"]:
        eval_one(s)
    E = load_events(["chb01", "chb10", "chb03"])
    print(E.groupby(["arm", "label"]).size(), flush=True)
    auc = auroc_table(E, ["chb01", "chb10", "chb03"])
    print(auc, flush=True)
    el = time.time() - t0
    print(f"smoke done in {el:.0f}s -> projected total for --eval-one over all {len(ALL_SUBS)} "
         f"subjects: ~{el / 3 * len(ALL_SUBS) / 60:.0f} min (characterisation only)", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--part0", action="store_true")
    ap.add_argument("--eval-one", metavar="SUBJ")
    ap.add_argument("--select", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.smoke:
        smoke()
    elif a.part0:
        part0()
        build_report()
    elif a.eval_one:
        eval_one(a.eval_one)
    elif a.select:
        select()
    elif a.apply:
        apply_veto()
        build_report()
    elif a.report:
        build_report()
    else:
        raise SystemExit("pass --smoke, --part0, --eval-one SUBJ, --select, --apply or --report")


if __name__ == "__main__":
    main()
