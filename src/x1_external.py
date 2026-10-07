#!/usr/bin/env python
"""
x1_external.py -- external validation of the P3 FROZEN system (tag p3-frozen) on data never used by the
thesis: CHB-MIT chb24 (the 24th case, outside the 23-subject splits) and the Siena Scalp EEG database
(14 adult patients, PhysioNet). Written 2026-10-07 BEFORE any of these recordings was processed.
Runs on Kaggle (CPU); the repo is copied to a writable folder and the combined dataset is read in place.

PRE-REGISTRATION (nothing below may change after the first result):
  * System = p3-frozen exactly: GAE v2 clean seeds 42, 1, 2, 3 (headline 42); per-patient per-channel
    LedoitWolf distance of the node latent; order statistics 6, 9, 12 + channel mean, each minus its
    +-15 min running median per file; percentile mean; D1 smoothing 5, budget clip(q_i, 0.005, 0.02) with
    k from results/p3c_freeze/freeze.json; kernel-CPD localizer. Code path = e23_test_look7.evaluate().
    The descriptive sensitivity point clip(q_i, 0.0075, 0.02) is reported beside it.
  * Signal path = c1b_build_trainset (band-pass 0.5-60 Hz, notch, 4-s windows, per-subject z-score, CAR ->
    wPLI + AEC, top-k 20 %, band powers, f7). Two declared, label-free adaptations for new data:
    (1) per-subject z-score statistics from EVERY 10th window of the whole recording (no seizure
    exclusion; the thesis's own stats excluded seizures -- the same divergence as the demo, record 11.3);
    the effect is measured on chb03 (stats.json vs label-free) and reported;
    (2) Siena: the 18 CHB-MIT bipolar channels are derived from the referential montage
    (T3=T7, T4=T8, T5=P7, T6=P8), resampled to 256 Hz with scipy resample_poly, notch at the site's mains
    frequency (50 Hz; CHB-MIT 60 Hz). A file missing any needed electrode is skipped (CHB-MIT rule).
  * Labels (seizure times) are read only to score. Scorer = the thesis SzCORE path (e10.score_events).
  * Label sources (amended 2026-10-07 after the label-only inventory, BEFORE any recording was scored):
    chb24: every present chb24_*.edf is scored (its summary lists only the 12 files with seizures; the
    other files are seizure-free; same glob convention as preprocessing.py); Siena: seizure times from the
    SzCORE benchmark's own converter, esl-epfl/epilepsy2bids load_annotations/siena.py (commit d3fb175),
    copied verbatim below -- it corrects the published typos (PN00-3 end time, PN01/PN06/PN11 file names,
    PN10-7.8.9 start time, PN12 layout). The first parser of this script missed 6 seizures and read PN00-3
    as 3,660 s.
  * Reported as is: per set (chb24; Siena) and per subject, 4 seeds, pooled and subject-mean sensitivity,
    precision, F1, FP/day, onset/offset error, short seizures. No gate, no tuning, one run.
GATES before any external result (STOP otherwise):
  R-feat  chb03 file 1 rebuilt here with its committed stats.json equals data/testset_v2/chb03.npz:
          f7 and bp5 max |diff| <= 1e-3, adjacency entries differing <= 0.5 %;
  R-model chb03 from the committed features: per-channel distances within 1e-4 relative of
          results/p2_test/chb03.npz for every seed, and e23.evaluate() reproduces look #7 for chb03
          (balanced point, detector and localized tp/fp, every seed).
Usage on Kaggle (paths found with rglob, never hard-coded):
  python x1_external.py inventory --data DIR        lists recordings and parsed seizures (no scoring)
  python x1_external.py gates --data DIR            R-feat and R-model
  python x1_external.py run --data DIR --subjects chb24 PN00 PN01 ...   (or --all-external)
  python x1_external.py report                      results/x1_external/SUMMARY.md
"""
import argparse
import json
import math
import re
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import filtfilt, iirnotch, resample_poly, sosfiltfilt
from sklearn.covariance import LedoitWolf

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "dataprep", ROOT / "src" / "retrain", ROOT / "src" / "phaseB",
          ROOT / "src" / "phaseC"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import preprocessing as P              # noqa: E402

OUT = ROOT / "results" / "x1_external"
FEAT = OUT / "features"
TAGS = ["clean_seed42", "clean_seed1", "clean_seed2", "clean_seed3"]
FS = P.FS
SIENA_MAP = {"T3": "T7", "T4": "T8", "T5": "P7", "T6": "P8"}
BIPOLAR = [tuple(c.split("-")) for c in P.COMMON_CHANNELS]
EXPECTED = {"chb24": 16, "siena_total": 47}      # published counts; printed beside the parsed ones


# ----------------------------------------------------------------------------- discovery and labels
def find(data, pattern):
    return sorted(Path(data).rglob(pattern))


def chb_subject(data, subj):
    summ = [p for p in find(data, f"{subj}-summary.txt")]
    if not summ:
        raise SystemExit(f"STOP: {subj}-summary.txt not found under {data}")
    sz = P.parse_summary(summ[0])                     # insertion order = summary order
    edfs = {p.name: p for p in find(data, f"{subj}_*.edf")}
    files = [(edfs[f], sz.get(f, [])) for f in sorted(edfs)]          # every present file (preprocessing glob)
    missing = [f for f in sz if f not in edfs]
    if missing:
        raise SystemExit(f"STOP {subj}: summary lists files that are not present: {missing}")
    return files, dict(kind="chb", notch=60.0, summary=str(summ[0]), listed=len(sz), present=len(files))


# ---- verbatim from esl-epfl/epilepsy2bids, src/epilepsy2bids/load_annotations/siena.py, commit d3fb175
# (functions _parseTimeStamp, _substractTimeStamps, _loadSeizures, _correctEdfFileNameTypos; only imports
#  adapted). This is the SzCORE benchmark's own conversion of the Siena annotations.
import os
import time as _time


def _parseTimeStamp(string: str) -> float:
    timeStamp = re.findall(".*[ |:]([0-9]+.[0-9]+.[0-9]+).*", string)[0]
    return _time.mktime(_time.strptime(timeStamp.replace(":", "."), "%H.%M.%S"))


def _substractTimeStamps(time1: float, time2: float) -> float:
    difference = time1 - time2
    if difference < 0:
        difference += 24 * 60 * 60  # Correct for day shift
    return difference


def _loadSeizures(edfFile: str) -> list:
    subject = os.path.basename(os.path.dirname(edfFile))
    correctedEdfFileName = _correctEdfFileNameTypos(edfFile)
    seizures = []
    summaryFile = Path(os.path.dirname(edfFile)) / f"Seizures-list-{subject}.txt"
    with open(summaryFile, "r") as summary:
        line = summary.readline()
        while line:
            if re.search(r"File name: {} *\n".format(correctedEdfFileName), line):
                firstLine = summary.readline()
                if correctedEdfFileName == "PN01.edf":
                    registrationStart = _parseTimeStamp(firstLine)
                    _ = summary.readline()
                    _ = summary.readline()
                    for _ in range(2):
                        _ = summary.readline()
                        start = _parseTimeStamp(summary.readline())
                        end = _parseTimeStamp(summary.readline())
                        _ = summary.readline()
                        seizures.append((_substractTimeStamps(start, registrationStart),
                                         (_substractTimeStamps(end, registrationStart))))
                elif correctedEdfFileName == "PN00-3.edf":  # seizure last 1hour
                    registrationStart = _parseTimeStamp(firstLine)
                    _ = summary.readline()
                    start = _parseTimeStamp(summary.readline())
                    end = _parseTimeStamp(summary.readline())
                    end = _parseTimeStamp("Seizure end time: 18.29.29\n")  # correct time
                    seizures.append((_substractTimeStamps(start, registrationStart),
                                     (_substractTimeStamps(end, registrationStart))))
                elif correctedEdfFileName == "PN10-7.8.9.edf":  # seizure last 1hour
                    if firstLine == "Registration start time:1 6.49.25\n":  # extra space
                        firstLine = "Registration start time:16.49.25\n"
                    registrationStart = _parseTimeStamp(firstLine)
                    _ = summary.readline()
                    start = _parseTimeStamp(summary.readline())
                    end = _parseTimeStamp(summary.readline())
                    seizures.append((_substractTimeStamps(start, registrationStart),
                                     (_substractTimeStamps(end, registrationStart))))
                elif "Seizure start time: " in firstLine:  # PN12 exception
                    start = _parseTimeStamp(firstLine)
                    end = _parseTimeStamp(summary.readline())
                    seizures.append((_substractTimeStamps(start, registrationStart),
                                     (_substractTimeStamps(end, registrationStart))))
                elif "Registration start time:" in firstLine:  # Standard format
                    registrationStart = _parseTimeStamp(firstLine)
                    _ = summary.readline()
                    start = _parseTimeStamp(summary.readline())
                    end = _parseTimeStamp(summary.readline())
                    seizures.append((_substractTimeStamps(start, registrationStart),
                                     (_substractTimeStamps(end, registrationStart))))
                else:
                    raise ValueError("Unknown format for Siena summary file.")
            line = summary.readline()
    return seizures


def _correctEdfFileNameTypos(filename: str) -> str:
    correctedEdfFileName = os.path.basename(filename)
    if correctedEdfFileName == "PN01-1.edf":
        correctedEdfFileName = "PN01.edf"
    elif correctedEdfFileName == "PN06-1.edf":
        correctedEdfFileName = "PNO6-1.edf"  # big o instead of 0
    elif correctedEdfFileName == "PN06-2.edf":
        correctedEdfFileName = "PNO6-2.edf"  # big o instead of 0
    elif correctedEdfFileName == "PN06-4.edf":
        correctedEdfFileName = "PNO6-4.edf"  # big o instead of 0
    elif correctedEdfFileName == "PN11-1.edf":
        correctedEdfFileName = "PN11-.edf"
    return correctedEdfFileName
# ---- end of the verbatim copy


def siena_subject(data, subj):
    lists = find(data, f"Seizures-list-{subj}.txt")
    if not lists:
        raise SystemExit(f"STOP: Seizures-list-{subj}.txt not found under {data}")
    edfs = sorted(p for p in lists[0].parent.glob(f"{subj}*.edf"))
    files = []
    for p in edfs:
        sz = _loadSeizures(str(p))
        files.append((p, [(int(math.floor(a)), int(math.ceil(b))) for a, b in sz]))
    return files, dict(kind="siena", notch=50.0, summary=str(lists[0]), listed=len(edfs), present=len(files))


def subject_files(data, subj):
    return chb_subject(data, subj) if subj.startswith("chb") else siena_subject(data, subj)


# ----------------------------------------------------------------------------- signal path
def load_18(path, kind):
    """18 CHB-MIT bipolar channels at 256 Hz in volts, or None if a channel/electrode is missing."""
    import mne
    if kind == "chb":
        raw = P.open_edf(path)
        if raw is None:
            return None
        if int(round(raw.info["sfreq"])) != FS:
            raise SystemExit(f"STOP {path.name}: CHB-MIT file at {raw.info['sfreq']} Hz")
        return raw.get_data().astype(np.float64)
    raw = mne.io.read_raw_edf(str(path), preload=False, verbose=False)
    names = {}
    for ch in raw.ch_names:
        n = ch.upper().replace("EEG", "").strip().replace(" ", "")
        names[SIENA_MAP.get(n, n)] = ch
    need = sorted({e for pair in BIPOLAR for e in pair})
    if any(e not in names for e in need):
        return None
    raw.pick([names[e] for e in need])
    X = raw.get_data().astype(np.float64)
    pos = {e: i for i, e in enumerate(need)}
    data = np.stack([X[pos[a]] - X[pos[b]] for a, b in BIPOLAR])
    fs = int(round(raw.info["sfreq"]))
    if fs != FS:
        g = math.gcd(fs, FS)
        data = resample_poly(data, FS // g, fs // g, axis=1)
    return data


def filters(notch):
    b, a = iirnotch(notch, Q=30, fs=FS)
    return P._BP_SOS, b, a


def filter_windows(data, notch):
    """identical to continuous_eval.filter_file after get_data (whole-file zero-phase filtering)."""
    sos, b, a = filters(notch)
    n = data.shape[1] // P.WIN_SAMPLES
    f = filtfilt(b, a, sosfiltfilt(sos, data, axis=1), axis=1)
    return np.ascontiguousarray(f[:, :n * P.WIN_SAMPLES].reshape(18, n, P.WIN_SAMPLES).transpose(1, 0, 2)).astype(np.float32), n


def window_padded(data, i, notch):
    """identical to preprocessing.filter_window (3-s padding) for the statistics pass."""
    sos, b, a = filters(notch)
    s, e = i * P.WIN_SAMPLES, (i + 1) * P.WIN_SAMPLES
    p0, p1 = max(0, s - P.FILTER_PAD), min(data.shape[1], e + P.FILTER_PAD)
    f = filtfilt(b, a, sosfiltfilt(sos, data[:, p0:p1], axis=1), axis=1)
    return f[:, s - p0:s - p0 + P.WIN_SAMPLES]


def labelfree_stats(files, kind, notch):
    """per-channel mean/std over every 10th window of the whole recording (label-free)."""
    acc, cnt = [], 0
    for path, _ in files:
        data = load_18(path, kind)
        if data is None:
            continue
        for i in range(data.shape[1] // P.WIN_SAMPLES):
            cnt += 1
            if cnt % P.STATS_SUBSAMPLE == 0:
                acc.append(window_padded(data, i, notch))
    X = np.concatenate(acc, axis=1)
    sd = X.std(axis=1, ddof=1); sd[sd <= 0] = 1.0
    return X.mean(axis=1), sd


def file_features(args):
    path, seizures, kind, notch, mu, sd, fi = args
    import c1b_build_trainset as C1B
    data = load_18(path, kind)
    if data is None:
        return dict(file=path.name, skipped=True)
    filt, n = filter_windows(data, notch)
    seg = data[:, :n * P.WIN_SAMPLES].reshape(18, n, P.WIN_SAMPLES)
    sl = np.all(seg.std(axis=2) < 1e-10, axis=0)
    secs = n * P.WIN_S
    lab = P.build_labels(secs, seizures).reshape(n, P.WIN_S).max(axis=1) == 1
    adj, bp5, f7 = [], [], []
    for s in range(0, n, 256):
        zw = (filt[s:s + 256].astype(np.float64) - mu[None, :, None]) / sd[None, :, None]
        a_, b_ = C1B.graph_and_bp(zw)
        adj.append(a_); bp5.append(b_); f7.append(C1B.f7(zw))
    return dict(file=path.name, skipped=False, adj=np.concatenate(adj), bp5=np.concatenate(bp5),
                f7=np.concatenate(f7), is_ictal=lab, is_signal_loss=sl, n=n, file_idx=fi)


def build_subject(data_root, subj, stats_mode="labelfree", stats_json=None, max_files=None, procs=4):
    files, meta = subject_files(data_root, subj)
    files = files[:max_files] if max_files else files
    t0 = time.time()
    if stats_mode == "json":
        st = json.loads(Path(stats_json).read_text())
        mu = np.asarray(st["ch_mean_uV"], float) * 1e-6; sd = np.asarray(st["ch_std_uV"], float) * 1e-6
    else:
        mu, sd = labelfree_stats(files, meta["kind"], meta["notch"])
    print(f"{subj}: statistics ({stats_mode}) {time.time()-t0:.0f}s", flush=True)
    jobs = [(p, s, meta["kind"], meta["notch"], mu, sd, i) for i, (p, s) in enumerate(files)]
    with Pool(processes=procs, maxtasksperchild=1) as pool:
        res = pool.map(file_features, jobs)
    kept = [r for r in res if not r["skipped"]]
    skipped = [r["file"] for r in res if r["skipped"]]
    if not kept:
        print(f"{subj}: every file lacks a needed electrode -> subject not scored ({skipped})", flush=True)
        return None, dict(meta, skipped=skipped, hours=0.0)
    for k, r in enumerate(kept):
        r["file_idx"] = k
    out = {k: np.concatenate([r[k] for r in kept]) for k in ("adj", "bp5", "f7", "is_ictal", "is_signal_loss")}
    out["file_idx"] = np.concatenate([np.full(r["n"], r["file_idx"], np.int16) for r in kept])
    out["files"] = np.array([r["file"] for r in kept], dtype=object)
    hours = len(out["file_idx"]) * P.WIN_S / 3600
    print(f"{subj}: {len(kept)} files ({len(skipped)} skipped: {skipped}), {hours:.1f} h, "
          f"{time.time()-t0:.0f}s ({(time.time()-t0)/max(hours, 1e-9):.0f} s per hour of EEG)", flush=True)
    return out, dict(meta, skipped=skipped, hours=hours)


# ----------------------------------------------------------------------------- model and scoring
def model_outputs(z):
    import p2_dump_seeds23 as PD
    idx = np.flatnonzero(~z["is_signal_loss"].astype(bool))
    adj = z["adj"][idx].astype(np.float32); adj[~np.isfinite(adj).all(axis=(1, 2))] = 0.0
    bp5 = z["bp5"][idx].astype(np.float32); bp5[~np.isfinite(bp5)] = 0.0
    f7 = z["f7"][idx].astype(np.float64)
    xn = (bp5 - bp5.min(axis=1, keepdims=True)) / (bp5.max(axis=1, keepdims=True) - bp5.min(axis=1, keepdims=True) + 1e-8)
    D = {}
    for tag in TAGS:
        _, Z = PD.run_model(tag, adj, xn, f7)
        D[tag] = np.column_stack([LedoitWolf().fit(Z[:, c, :].astype(np.float64)).mahalanobis(Z[:, c, :].astype(np.float64))
                                  for c in range(Z.shape[1])]).astype(np.float64)
    return idx, D


def make_ctx(z, idx, D):
    n = len(z["is_ictal"]); ok = ~z["is_signal_loss"].astype(bool); fidx = z["file_idx"].astype(int)
    ict = z["is_ictal"].astype(bool)
    zz = dict(is_ictal=ict, is_signal_loss=~ok, file_idx=fidx, is_buffer=np.zeros(n, bool))
    return dict(s="ext", z=zz, idx=idx, D=D, Z={t: None for t in TAGS}, n=n, ok=ok, fidx=fidx, wf=fidx[idx],
                ict=ict, ict_ok=ict & ok, nonict=~ict & ok, nh=float((~ict & ok).sum()) * P.WIN_S / 3600)


def evaluate_ctx(ctx, subj, set_name, rows, erows):
    import e23_test_look7 as E23
    cfg = json.loads((ROOT / "results" / "p3c_freeze" / "freeze.json").read_text())
    for pt, (fl, cp) in cfg["points"].items():
        for tag in TAGS:
            out, errs = E23.evaluate(ctx, tag, cfg, fl, cp, cfg["localizer"])
            for st, v in out.items():
                rows.append(dict(set=set_name, subject=subj, point=pt, seed=tag, stage=st, **v))
            erows += [dict(set=set_name, subject=subj, point=pt, seed=tag, **e) for e in errs]


# ----------------------------------------------------------------------------- commands
def cmd_inventory(a):
    edf = find(a.data, "*.edf")
    print(f"EDF files under {a.data}: {len(edf)}")
    tops = pd.Series([str(p.relative_to(a.data)).split("/")[0] for p in edf]).value_counts()
    print("top-level folders with EDF:\n" + tops.to_string())
    for pat in ("chb24-summary.txt", "chb03-summary.txt", "Seizures-list-*.txt"):
        print(f"{pat}: {[str(p) for p in find(a.data, pat)][:20]}")
    sub = ["chb24"] + sorted({re.sub(r"Seizures-list-(.*)\.txt", r"\1", p.name) for p in find(a.data, "Seizures-list-*.txt")})
    total = 0
    for s in sub:
        try:
            files, meta = subject_files(a.data, s)
        except SystemExit as e:
            print(e); continue
        n_sz = sum(len(v) for _, v in files)
        total += n_sz if meta["kind"] == "siena" else 0
        durs = [b - a_ for _, v in files for a_, b in v]
        for p_, v in files:
            if v:
                print(f"    {p_.name}: {v}")
        print(f"{s:6s} {meta['kind']:5s} files present {meta['present']:3d} (listed {meta['listed']:3d}) seizures {n_sz:3d} "
              f"durations s {sorted(durs)[:12]}")
    print(f"Siena seizures parsed in present files: {total} (published total, to verify: {EXPECTED['siena_total']}); chb24 (to verify: {EXPECTED['chb24']})")
    import mne
    for pat in ("chb24_01.edf", "PN00-1.edf"):
        hits = find(a.data, pat)
        if hits:
            r = mne.io.read_raw_edf(str(hits[0]), preload=False, verbose=False)
            print(f"{pat}: sfreq {r.info['sfreq']}, {r.n_times / r.info['sfreq'] / 3600:.2f} h, channels {r.ch_names}")
    for p in find(a.data, "Seizures-list-PN00.txt")[:1]:
        print("---- first lines of", p.name); print("\n".join(p.read_text(errors="ignore").splitlines()[:16]))


def cmd_gates(a):
    import e23_test_look7 as E23
    ref = np.load(ROOT / "data" / "testset_v2" / "chb03.npz", allow_pickle=True)
    z1, _ = build_subject(a.data, "chb03", "json", ROOT / "data" / "processed" / "chb03_stats.json", max_files=1, procs=1)
    m = ref["file_idx"] == 0
    if m.sum() != len(z1["file_idx"]):
        raise SystemExit(f"STOP R-feat: chb03 file 1 has {len(z1['file_idx'])} windows here, {int(m.sum())} committed")
    d_f7 = float(np.nanmax(np.abs(z1["f7"] - ref["f7"][m]))); d_bp = float(np.nanmax(np.abs(z1["bp5"] - ref["bp5"][m])))
    d_adj = float((np.abs(z1["adj"].astype(np.float32) - ref["adj"][m].astype(np.float32)) > 1e-3).mean())
    print(f"R-feat chb03 file 1: f7 {d_f7:.2e}, bp5 {d_bp:.2e}, adjacency entries differing {d_adj:.4%}", flush=True)
    if d_f7 > 1e-3 or d_bp > 1e-3 or d_adj > 0.005:
        raise SystemExit("STOP R-feat")
    z = {k: ref[k] for k in ("adj", "bp5", "f7", "is_ictal", "is_signal_loss", "file_idx")}
    idx, D = model_outputs(z)
    dmp = np.load(ROOT / "results" / "p2_test" / "chb03.npz")
    if not np.array_equal(idx, dmp["idx"]):
        raise SystemExit("STOP R-model: window index differs from results/p2_test/chb03.npz")
    for tag in TAGS:
        rel = float(np.max(np.abs(D[tag] - dmp[f"{tag}_d"]) / (np.abs(dmp[f"{tag}_d"]) + 1e-6)))
        print(f"R-model distances {tag}: max relative diff {rel:.2e}", flush=True)
        if rel > 1e-4:
            raise SystemExit("STOP R-model (distances)")
    rows, er = [], []
    evaluate_ctx(make_ctx(z, idx, D), "chb03", "gate", rows, er)
    R = pd.DataFrame(rows); L7 = pd.read_csv(ROOT / "results" / "e23_test_look7" / "per_subject_seed.csv")
    for tag in TAGS:
        for st in ("detector", "localized"):
            g = R[(R.point == "balanced") & (R.seed == tag) & (R.stage == st)].iloc[0]
            w = L7[(L7.point == "balanced") & (L7.subject == "chb03") & (L7.seed == tag) & (L7.stage == st)].iloc[0]
            if (int(g.tp), int(g.fp)) != (int(w.tp), int(w.fp)):
                raise SystemExit(f"STOP R-model {tag} {st}: {(int(g.tp), int(g.fp))} vs look #7 {(int(w.tp), int(w.fp))}")
    print("GATES OK: R-feat and R-model (look #7 reproduced for chb03, 4 seeds)", flush=True)


def cmd_run(a):
    OUT.mkdir(parents=True, exist_ok=True); FEAT.mkdir(parents=True, exist_ok=True)
    if not (OUT / "GATES_OK").exists() and not a.force_without_gates:
        raise SystemExit("STOP: run 'gates' first (it writes results/x1_external/GATES_OK)")
    subs = list(a.subjects)
    if a.all_external:
        subs = ["chb24"] + sorted({re.sub(r"Seizures-list-(.*)\.txt", r"\1", p.name) for p in find(a.data, "Seizures-list-*.txt")})
    for s in subs:
        fz = FEAT / f"{s}{'_lf' if s == 'chb03' else ''}.npz"
        if (OUT / f"rows_{fz.stem}.csv").exists():
            print(f"{s}: done, skip"); continue
        if fz.exists():
            z = dict(np.load(fz, allow_pickle=True)); meta = json.loads(str(z.pop("meta")))
        else:
            z, meta = build_subject(a.data, s, "labelfree", procs=a.procs)
            if z is None:
                pd.DataFrame([dict(subject=s, not_scored="no file with all electrodes")]).to_csv(OUT / f"notscored_{s}.csv", index=False)
                continue
            np.savez(fz, **z, meta=json.dumps({k: v for k, v in meta.items()}))
        idx, D = model_outputs(z)
        rows, er = [], []
        set_name = "chb03-labelfree" if s == "chb03" else ("chb24" if s.startswith("chb") else "siena")
        evaluate_ctx(make_ctx(z, idx, D), s, set_name, rows, er)
        pd.DataFrame(rows).assign(hours=meta["hours"], skipped=len(meta["skipped"])).to_csv(OUT / f"rows_{fz.stem}.csv", index=False)
        pd.DataFrame(er).to_csv(OUT / f"errors_{fz.stem}.csv", index=False)
        print(f"{s}: scored ({set_name})", flush=True)


def cmd_report(a):
    import e22_test_oneshot as E22
    R = pd.concat([pd.read_csv(p) for p in sorted(OUT.glob("rows_*.csv"))], ignore_index=True)
    ns = sorted(p.stem.replace("notscored_", "") for p in OUT.glob("notscored_*.csv"))
    Er = pd.concat([pd.read_csv(p) for p in sorted(OUT.glob("errors_*.csv")) if p.stat().st_size > 2], ignore_index=True) \
        if any(p.stat().st_size > 2 for p in OUT.glob("errors_*.csv")) else pd.DataFrame()
    L = ["# X1 -- external validation of the P3 frozen system (no tuning, one run)\n",
         "Gates R-feat and R-model passed before any external recording was scored.\n",
         f"Subjects not scored (no file with all 19 electrodes): {ns or 'none'}\n"]
    for set_name in ("chb24", "siena", "chb03-labelfree"):
        Q = R[R.set == set_name]
        if not len(Q):
            continue
        L += [f"## {set_name}\n", "```", "point        stage      seed          tp/ref  FP   sens   prec   F1    FP/day | s-sens s-FP/day | short"]
        for pt in ("balanced", "sensitivity"):
            for st in ("detector", "localized"):
                for tag in TAGS:
                    d = Q[(Q.point == pt) & (Q.stage == st) & (Q.seed == tag)]
                    if not len(d):
                        continue
                    m = E22.metrics(d)
                    L.append(f"{pt:12s} {st:10s} {tag:13s} {m['tp']:3.0f}/{m['n_ref']:3.0f} {m['fp']:4.0f}  {m['sens']:.3f}  "
                             f"{m['prec']:.3f}  {m['f1']:.3f} {m['fa_day']:6.2f} | {m['s_sens']:.3f} {m['s_fa']:6.2f} | {m['short']}")
        L.append("```")
        p42 = Q[(Q.point == "balanced") & (Q.stage == "localized") & (Q.seed == "clean_seed42")]
        L += ["\nPer subject, balanced point, seed 42, after the localizer:\n", "```",
              p42.assign(fa_day=p42.fp / p42.nonict_h * 24)[["subject", "tp", "n_ref", "fp", "fa_day", "top", "q_raw", "hours", "skipped"]]
              .round(4).to_string(index=False), "```"]
        if len(Er):
            e = Er[(Er.set == set_name) & (Er.point == "balanced")]
            if len(e):
                L.append(f"\nOnset/offset |error| (balanced, n = {len(e)}): detector {e.det_on.abs().median():.0f}/{e.det_off.abs().median():.0f} s, "
                         f"CPD {e.cpd_on.abs().median():.0f}/{e.cpd_off.abs().median():.0f} s, hybrid {e.hyb_on.abs().median():.0f}/{e.hyb_off.abs().median():.0f} s")
    if (R.set == "chb03-labelfree").any():
        L7 = pd.read_csv(ROOT / "results" / "e23_test_look7" / "per_subject_seed.csv")
        w = L7[(L7.subject == "chb03") & (L7.point == "balanced") & (L7.stage == "localized")]
        L.append(f"\nchb03 with the thesis statistics (look #7): tp {w.tp.tolist()}, fp {w.fp.tolist()} (4 seeds) -- effect of the "
                 "label-free statistics on a known patient.")
    (OUT / "SUMMARY.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    for name in ("inventory", "gates", "run"):
        s = sp.add_parser(name); s.add_argument("--data", required=True)
        if name == "run":
            s.add_argument("--subjects", nargs="*", default=[]); s.add_argument("--all-external", action="store_true")
            s.add_argument("--procs", type=int, default=4); s.add_argument("--force-without-gates", action="store_true")
    sp.add_parser("report")
    a = ap.parse_args()
    if a.cmd == "inventory":
        cmd_inventory(a)
    elif a.cmd == "gates":
        cmd_gates(a); OUT.mkdir(parents=True, exist_ok=True); (OUT / "GATES_OK").write_text("ok")
    elif a.cmd == "run":
        cmd_run(a)
    else:
        cmd_report(a)


if __name__ == "__main__":
    main()
