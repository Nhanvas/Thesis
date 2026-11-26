#!/usr/bin/env python
"""
c5_verify2.py -- chat C5c (Track C), Step 2b, gate G9: the Step 1 verification of SzScan (src/c5_szscan_verify.py,
record module, unchanged) extended to the Step 2 application: both engine modes, referential inputs (Siena, hospital
records), 512-Hz inputs, the mains frequency of each study, private studies.

READ ONLY on the application's state (database opened read-only; upload cache only read). Every file of every subject
in the database (or of --subjects), every one of the 18 channels, the whole recording.

  V1 source     sha256 of the EDF copy the app keeps and of the dataset's EDF = PhysioNet's list (CHB-MIT, Siena;
                private studies: no public list, not checked); the app's cached signal `{stem}.raw.npy` = the EDF
                re-read by an INDEPENDENT reader written from the EDF specification (no MNE): bipolar inputs -> the
                signal with the derivation's label; referential inputs -> difference of the two electrodes (labels
                normalised as x1_external.load_18: upper case, "EEG" and spaces removed, one reference suffix
                removed, T3/T4/T5/T6 -> T7/T8/P7/P8), resampled to 256 Hz by scipy's resample_poly when the file is
                not at 256 Hz (the same function as the app -- the resampler is not independent; stated).
                Derivations with an electrode the app interpolated (named in the file's notice) are reported, not
                compared (the interpolation was checked in the synthetic test E10).
  V2 channels   the app's list = the 18 thesis derivations in order; each cached channel = the independent derivation.
  V3 amplitude  `waveform_serving.get_waveform` (the endpoint's function) over the whole file in 10-min pages of
                1,200 buckets: every bucket min / max = the independent signal in µV, raw and filtered.
  V4 time       CHB-MIT: database start = EDF header start = summary start, durations (as Step 1); Siena: database
                start = EDF header start, duration = records present x record duration; private: database start = the
                neutral epoch (elapsed time), duration as above; windows = floor(duration / 4 s); every event inside
                its file, events of a file sorted and not overlapping; file mode: no event in a file shorter than the
                engine's minimum; the UI time formatter (node) on start, middle and end of every file.
  V5 filter     `{stem}.filtered.npy` = an independent zero-phase Butterworth band-pass (order 4, 0.5-60 Hz) and an
                iirnotch at THE STUDY'S mains frequency (Q 30), every sample; the UI label template shows the study's
                mains frequency (static).
  V6 events     the 8 test subjects in session mode = the committed application-tier export (tier2_v4) exactly;
                other subjects: no committed reference (file mode is compared with F2-03's L3 rows in gate G2).
Memory: the EDF is read in record chunks with ordinary file reads (no memory map); each needed signal goes to a
temporary int16 row file, then one derivation at a time is formed in memory; the peak private memory of each file
is recorded (psutil sampler).

Outputs (public subjects only): results/c5_szscan/step2/g9/ (VERIFY2.md, per_file.csv, channels.csv, gates.json);
--smoke: the longest public file only, results/c5_szscan/step2/g9/smoke/. Private studies (--private): only a count
table in Agent/inbox/C5_G9_PRIVATE.md (neutral names; no header field, no date).

Run: PYTHONUTF8=1 python src/c5_verify2.py --chb F:/Study/Thesis/Dataset/CHB-MIT --siena F:/Study/Thesis/Dataset/siena [--private] [--smoke]
"""
import argparse
import csv
import json
import math
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.signal import resample_poly

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src",):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import c5_szscan_verify as V1      # noqa: E402  (record module of Step 1; helpers imported read only)

BACKEND, FRONTEND = V1.BACKEND, V1.FRONTEND
CH = V1.THESIS_CHANNELS
FS, WIN, TOL_UV, TOL_ENV_UV, PAGE_S, PAGE_PX = V1.FS, V1.WIN, V1.TOL_UV, V1.TOL_ENV_UV, V1.PAGE_S, V1.PAGE_PX
CHB_SUMS = V1.DEFAULT_SUMS
SIENA_SUMS = ROOT / "results" / "r2" / "r0_data" / "ext" / "physionet_SHA256SUMS_siena.txt"
TIER2 = V1.DEFAULT_TIER2
OUT = ROOT / "results" / "c5_szscan" / "step2" / "g9"
INBOX = ROOT.parent / "Agent" / "inbox"
ID_RE = re.compile(r"^(chb\d\d|PN\d\d)(.*)$")
TEST = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
PRIVATE_EPOCH = "1970-01-01T00:00:00+00:00"
# electrode-name convention of x1_external.load_18 (typed here, not imported from the app)
ALIAS = {"T3": "T7", "T4": "T8", "T5": "P7", "T6": "P8"}
SUFFIXES = ("-REF", "-LE", "-AVG", "-AV", "-CAR", "-A1", "-A2", "-M1", "-M2", "-REF1")
PAIRS = [tuple(c.split("-")) for c in CH]
ELECTRODES = sorted({e for p in PAIRS for e in p})
CHUNK_BYTES = 64 << 20


# ════════════════════════════════════════════════════════════════════ memory sampler
class Peak:
    def __init__(self):
        try:
            import psutil
            self.p = psutil.Process()
        except ImportError:
            self.p = None
        self.peak, self.stop = 0.0, True

    def now(self):
        if self.p is None:
            return float("nan")
        mi = self.p.memory_info()
        return (getattr(mi, "private", 0) or mi.rss) / 1e6

    def __enter__(self):
        self.peak, self.stop = self.now(), False
        self.base = self.peak

        def run():
            while not self.stop:
                self.peak = max(self.peak, self.now())
                time.sleep(0.05)
        self.th = threading.Thread(target=run, daemon=True)
        self.th.start()
        return self

    def __exit__(self, *a):
        self.stop = True
        self.th.join()
        self.peak = max(self.peak, self.now())


# ════════════════════════════════════════════════════════════════════ independent EDF reading
def norm(label, ext):
    n = label.upper().replace("EEG", "").strip().replace(" ", "")
    n = ALIAS.get(n, n)
    if ext:
        for s in SUFFIXES:
            if n.endswith(s) and len(n) > len(s):
                n = n[: -len(s)]
                break
        n = ALIAS.get(n, n)
    return n


def montage(hdr):
    """('bipolar', {derivation: index}) | ('referential', {electrode: index}) | (None, {})."""
    lab = V1.label_index(hdr)
    if all(c in lab for c in CH):
        return "bipolar", {c: lab[c][0] for c in CH}
    exact = {}
    for i, s in enumerate(hdr["signals"]):
        exact[norm(s["label"], False)] = i               # last signal with a name, as x1_external.load_18's dict
    if all(e in exact for e in ELECTRODES):
        return "referential", {e: exact[e] for e in ELECTRODES}
    ext = {}
    for i, s in enumerate(hdr["signals"]):
        ext.setdefault(norm(s["label"], True), i)        # first signal with a name
    if all(e in ext for e in ELECTRODES):
        return "referential", {e: ext[e] for e in ELECTRODES}
    return None, {}


def n_records(hdr):
    return hdr["n_rec_file"] if hdr["n_rec_hdr"] < 0 else min(hdr["n_rec_hdr"], hdr["n_rec_file"])


def extract(path, hdr, idxs, tmp):
    """One pass over the file in record chunks (ordinary reads): the digital samples of each signal in idxs -> its own
    int16 row file in tmp. Returns {idx: Path}."""
    n_rec, rs = n_records(hdr), hdr["rec_samples"]
    starts = np.cumsum([0] + [s["nsamp"] for s in hdr["signals"]])
    k = max(1, CHUNK_BYTES // (2 * rs))
    outs = {i: open(tmp / f"sig{i}.i16", "wb") for i in idxs}
    try:
        with open(path, "rb") as fh:
            fh.seek(hdr["hdr_bytes"])
            done = 0
            while done < n_rec:
                m = min(k, n_rec - done)
                blk = np.fromfile(fh, dtype="<i2", count=m * rs).reshape(m, rs)
                for i in idxs:
                    outs[i].write(np.ascontiguousarray(blk[:, starts[i]:starts[i + 1]]).tobytes())
                done += m
                del blk
    finally:
        for f in outs.values():
            f.close()
    return {i: tmp / f"sig{i}.i16" for i in idxs}


def volts(hdr, i, p):
    """Signal i in volts (float64), Step 1's formula (c5_szscan_verify.edf_signal_volts)."""
    s = hdr["signals"][i]
    dig = np.fromfile(p, dtype="<i2").astype(np.float64)
    gain = (s["physmax"] - s["physmin"]) / (s["digmax"] - s["digmin"])
    return ((dig - s["digmin"]) * gain + s["physmin"]) * V1.unit_scale(s["physdim"])


def interpolated_of(notice):
    m = re.search(r"Electrode\(s\) ([A-Z0-9, ]+) looked disconnected or flat and were interpolated", notice or "")
    return {e.strip() for e in m.group(1).split(",")} if m else set()


# ════════════════════════════════════════════════════════════════════ static checks
def static_checks():
    out = {}
    _, pdm = V1.import_backend()
    P = pdm.preprocessing
    sos, b, a = V1.indep_filters(60.0)
    out["code_bandpass_equals_butter4_0.5_60"] = bool(np.array_equal(P._BP_SOS, sos))
    out["code_notch_function_equals_iirnotch_q30"] = all(
        np.array_equal(np.asarray(pdm.notch_coefficients(h)[0]), V1.indep_filters(h)[1])
        and np.array_equal(np.asarray(pdm.notch_coefficients(h)[1]), V1.indep_filters(h)[2]) for h in (50.0, 60.0))
    screen = (FRONTEND / "screens" / "AnalysisScreen.jsx").read_text(encoding="utf-8")
    out["ui_label_template"] = bool(re.search(r"Preprocessed \(0\.5-60 Hz \+ \$\{fileMeta\.mains_hz \?\? 60\} Hz notch\)",
                                              screen))
    dbsrc = (BACKEND / "db.py").read_text(encoding="utf-8")
    out["api_file_carries_study_mains"] = 'file_dict["mains_hz"] = srow["mains_hz"]' in dbsrc
    main_src = (BACKEND / "main.py").read_text(encoding="utf-8")
    out["endpoint_calls_get_waveform"] = bool(re.search(r"ws\.get_waveform\(", main_src))
    out["app_channels_equal_thesis"] = list(P.COMMON_CHANNELS) == CH
    out["freq_response_db_50"] = V1.freq_response(50.0)
    return out


# ════════════════════════════════════════════════════════════════════ per file
def check_file(f, subj, roots, sums, summ, ev_db, ev_ref, ws, min_s):
    sid, fn, kind, base = subj["id"], f["filename"], subj["kind"], subj["base"]
    stem = Path(fn).stem
    up = roots["uploads"] / sid
    row = dict(subject=sid, file=fn, mode=subj["mode"], mains_hz=subj["mains_hz"])
    chans = []
    t0 = time.perf_counter()
    copy_edf = up / fn
    src_edf = (roots["chb"] if kind == "chb" else roots["siena"]) / base / fn if kind != "private" else None
    want = sums.get(f"{base}/{fn}") if kind != "private" else None
    row["copy_present"] = copy_edf.exists()
    if kind == "private":
        row["sha"] = "no public list"
        sha_ok = True
    else:
        row["copy_sha_ok"] = copy_edf.exists() and want is not None and V1.sha256(copy_edf) == want
        row["dataset_sha_ok"] = src_edf is not None and src_edf.exists() and want is not None and V1.sha256(src_edf) == want
        sha_ok = row["copy_sha_ok"]
    edf = copy_edf if copy_edf.exists() else src_edf
    hdr = V1.edf_header(edf)
    mtg, idx = montage(hdr)
    row["montage"] = mtg
    raw_mm = np.load(up / f"{stem}.raw.npy", mmap_mode="r")
    flt_mm = np.load(up / f"{stem}.filtered.npy", mmap_mode="r")
    n_win = raw_mm.shape[0]
    usable = n_win * WIN
    rec_dur = hdr["rec_dur"]
    n_rec = n_records(hdr)
    sig_ids = sorted(set(idx.values()))
    rates = {i: hdr["signals"][i]["nsamp"] / rec_dur for i in sig_ids}
    fs_in = rates[sig_ids[0]] if sig_ids else float("nan")
    row["fs_in"] = fs_in
    row["rates_equal"] = len(set(rates.values())) == 1
    edf_dur = n_rec * rec_dur
    row["n_windows_cache"], row["n_windows_expected"] = n_win, int(edf_dur * FS) // WIN
    row["windows_ok"] = (n_win == int(edf_dur * FS) // WIN and raw_mm.shape[1:] == (18, WIN)
                         and flt_mm.shape == raw_mm.shape)
    interp = interpolated_of(f.get("notice", ""))
    row["interpolated"] = " ".join(sorted(interp))
    notch = float(subj["mains_hz"])
    # V3 pages first (small: 18 x 1,200 x 2 per page), then one channel at a time
    pages = []
    start = 0.0
    dur_u = usable / FS
    v3_names_ok = True
    while start < dur_u:
        end = min(dur_u, start + PAGE_S)
        w = ws.get_waveform(sid, fn, roots["uploads"], start, end, PAGE_PX)
        v3_names_ok &= w["channels"] == CH
        pages.append((start, end, np.asarray(w["raw_uv"], np.float32), np.asarray(w["filtered_uv"], np.float32)))
        start = end
    tmp = Path(tempfile.mkdtemp(prefix="c5v2_", dir=roots["tmp"]))
    v1_max = v5_max = v3_raw = v3_flt = 0.0
    v1_ok = v2_ok = bool(mtg) and row["rates_equal"]
    try:
        paths = extract(edf, hdr, sig_ids, tmp) if mtg else {}
        up_, down_ = 1, 1
        if mtg and abs(fs_in - FS) > 1e-9:
            g = math.gcd(int(round(fs_in)), FS)
            up_, down_ = FS // g, int(round(fs_in)) // g
        for c, ch in enumerate(CH):
            cr = dict(subject=sid, file=fn, channel=ch)
            if not mtg:
                cr["present"] = False
                chans.append(cr)
                continue
            e1, e2 = PAIRS[c]
            if mtg == "referential" and (e1 in interp or e2 in interp):
                cr["compared"] = "interpolated electrode (not compared)"
                chans.append(cr)
                continue
            if mtg == "bipolar":
                x = volts(hdr, idx[ch], paths[idx[ch]])
            else:
                x = volts(hdr, idx[e1], paths[idx[e1]])
                x -= volts(hdr, idx[e2], paths[idx[e2]])
            if up_ != down_:
                x = resample_poly(x, up_, down_)
            x = x[:usable]
            app = np.asarray(raw_mm[:, c, :], np.float64).reshape(-1)
            d = float(np.max(np.abs(app - x))) * 1e6 if len(x) == usable else float("inf")
            del app
            fi = V1.indep_filter(x, notch)
            appf = np.asarray(flt_mm[:, c, :], np.float64).reshape(-1)
            df = float(np.max(np.abs(appf - fi))) * 1e6
            del appf
            cr.update(raw_max_abs_diff_uv=d, filtered_max_abs_diff_uv=df, compared="yes")
            if d > TOL_UV:
                v1_ok = v2_ok = False
            v1_max, v5_max = max(v1_max, d), max(v5_max, df)
            # V3 for this channel
            for (a0, a1, renv, fenv) in pages:
                a_, b_ = int(round(a0 * FS)), int(round(a1 * FS))
                edges = np.round(np.linspace(0, b_ - a_, PAGE_PX + 1)).astype(np.int64)
                for env, sig in ((renv, x), (fenv, fi)):
                    seg = sig[a_:b_] * 1e6
                    lo = edges[:-1]
                    hi = np.minimum(np.maximum(edges[1:], lo + 1), b_ - a_)
                    mins = np.array([seg[l:h].min() for l, h in zip(lo, hi)])
                    maxs = np.array([seg[l:h].max() for l, h in zip(lo, hi)])
                    dd = float(max(np.max(np.abs(env[c, :, 0] - mins)), np.max(np.abs(env[c, :, 1] - maxs))))
                    if env is renv:
                        v3_raw = max(v3_raw, dd)
                    else:
                        v3_flt = max(v3_flt, dd)
            del x, fi
            chans.append(cr)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    row["channels_compared"] = sum(c.get("compared") == "yes" for c in chans)
    row["V1_raw_max_abs_diff_uv"] = v1_max
    row["V1"] = bool(sha_ok and v1_ok and row["windows_ok"])
    row["V2"] = bool(v2_ok and row["channels_compared"] + len(
        [c for c in chans if str(c.get("compared", "")).startswith("interpolated")]) == 18)
    row["V5_filtered_max_abs_diff_uv"] = v5_max
    row["V5_data"] = bool(row["channels_compared"] > 0 and v5_max <= TOL_UV)
    row["V3_pages"] = len(pages)
    row["V3_raw_env_max_abs_diff_uv"], row["V3_filtered_env_max_abs_diff_uv"] = v3_raw, v3_flt
    row["V3"] = bool(v3_names_ok and row["channels_compared"] > 0 and v3_raw <= TOL_ENV_UV and v3_flt <= TOL_ENV_UV)
    # V4
    hdr_start = V1.hms_to_s(hdr["starttime"])
    if kind == "private":
        row["start_ok"] = f["start_time"] == PRIVATE_EPOCH
        case_start = 0
    else:
        db_start = datetime.fromisoformat(f["start_time"])
        row["start_ok"] = (db_start.hour * 3600 + db_start.minute * 60 + db_start.second) == hdr_start
        case_start = hdr_start
        if kind == "chb":
            s_t = summ.get(fn)
            if s_t and s_t[0]:
                row["start_summary_eq_edf"] = V1.hms_to_s(s_t[0]) % 86400 == hdr_start
    row["duration_db_eq_edf"] = abs(f["duration_seconds"] - edf_dur) < 1e-6
    evs = sorted((e for e in ev_db if e["file_id"] == f["id"]), key=lambda e: e["onset_sec"])
    ai = [e for e in evs if e["source"] == "AI"]
    row["events_ai"] = len(ai)
    row["events_inside_file"] = all(0 <= e["onset_sec"] < e["offset_sec"] <= usable / FS + 1e-9 for e in ai) \
        if subj["mode"] == "file" else all(0 <= e["onset_sec"] < e["offset_sec"] for e in ai)
    row["events_sorted_disjoint"] = all(a["offset_sec"] <= b["onset_sec"] for a, b in zip(ai, ai[1:]))
    if subj["mode"] == "file" and edf_dur < min_s:
        row["short_file_no_event"] = len(ai) == 0
    row["V4_core"] = bool(row["start_ok"] and row["duration_db_eq_edf"] and row["events_inside_file"]
                          and row["events_sorted_disjoint"] and row.get("start_summary_eq_edf", True)
                          and row.get("short_file_no_event", True) and 0 <= edf_dur - usable / FS < 4)
    # V6
    ref = ev_ref.get((sid, fn)) if (sid in TEST and subj["mode"] == "session") else None
    if ref is None:
        row["V6"] = "no committed reference"
    else:
        got = sorted((round(e["onset_sec"], 6), round(e["offset_sec"], 6)) for e in ai)
        row["V6"] = bool(got == sorted(ref))
    row["seconds"] = round(time.perf_counter() - t0, 1)
    row["hours"] = edf_dur / 3600
    case = dict(start_iso=f["start_time"], dur=f["duration_seconds"], usable=usable / FS, hdr_start=case_start,
                file=fn, subject=sid)
    return row, chans, case


# ════════════════════════════════════════════════════════════════════ report
GATE_KEYS = ("V1", "V2", "V3", "V4_core", "V5_data")


def gates_of(rows, static, ui):
    g = {}
    for k in GATE_KEYS:
        ok = sum(r.get(k) is True for r in rows)
        g[k] = dict(pass_files=ok, files=len(rows), PASS=(ok == len(rows) and len(rows) > 0))
    g["V2"]["PASS"] &= static["app_channels_equal_thesis"]
    g["V3"]["PASS"] &= static["endpoint_calls_get_waveform"]
    g["V4"] = dict(PASS=g["V4_core"]["PASS"] and (ui is None or ui[0]), ui_cases=None if ui is None else ui[1],
                   node_run=ui is not None)
    g["V5"] = dict(PASS=g["V5_data"]["PASS"] and static["ui_label_template"] and static["api_file_carries_study_mains"]
                   and static["code_bandpass_equals_butter4_0.5_60"] and static["code_notch_function_equals_iirnotch_q30"])
    v6 = [r["V6"] for r in rows]
    g["V6"] = dict(match=sum(v is True for v in v6), differ=sum(v is False for v in v6),
                   no_reference=sum(v == "no committed reference" for v in v6),
                   PASS=None if not any(v is True or v is False for v in v6) else not any(v is False for v in v6))
    return g


def write_public(out, rows, chans, static, ui, meta, smoke):
    out.mkdir(parents=True, exist_ok=True)
    g = gates_of(rows, static, ui)
    (out / "gates.json").write_text(json.dumps(g, indent=1, default=str), encoding="utf-8")
    (out / "run_meta.json").write_text(json.dumps(meta, indent=1, default=str), encoding="utf-8")
    for name, data in (("per_file.csv", rows), ("channels.csv", chans)):
        keys = sorted({k for r in data for k in r}, key=lambda k: (k not in ("subject", "file", "channel"), k))
        with open(out / name, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows(data)
    res = {True: "PASS", False: "FAIL", None: "not run"}
    mx = lambda k: max((r[k] for r in rows), default=0)  # noqa: E731
    L = [f"# SzScan verification after Step 2 (gate G9, chat C5c){' — SMOKE' if smoke else ''}", "",
         f"Code `src/c5_verify2.py` (helpers of the Step 1 record module `src/c5_szscan_verify.py`); commit "
         f"`{meta['commit']}` (uncommitted changes in web_demo/ or src/: {meta['dirty']}); {len(rows)} files, "
         f"{meta['hours']:.1f} h of EEG, subjects {', '.join(meta['subjects'])}; run {meta['seconds']:.0f} s; peak "
         f"private memory per file {meta['peak_mb_max']:.0f} MB. Read only. Private studies: "
         f"{meta['private_note']}.", "", "| check | result | detail |", "|---|---|---|",
         f"| V1 source (sha256; cache = independent reader) | {res[g['V1']['PASS']]} | {g['V1']['pass_files']} / "
         f"{g['V1']['files']} files; largest difference {mx('V1_raw_max_abs_diff_uv'):.2e} µV (tolerance {TOL_UV}) |",
         f"| V2 channels (18 names, order, derivation) | {res[g['V2']['PASS']]} | {g['V2']['pass_files']} / "
         f"{g['V2']['files']} files; app list = thesis list {static['app_channels_equal_thesis']} |",
         f"| V3 µV on screen (endpoint function, whole file) | {res[g['V3']['PASS']]} | raw {mx('V3_raw_env_max_abs_diff_uv'):.3f}, "
         f"filtered {mx('V3_filtered_env_max_abs_diff_uv'):.3f} µV (tolerance {TOL_ENV_UV}) |",
         f"| V4 time and events | {res[g['V4']['PASS']]} | {g['V4_core']['pass_files']} / {g['V4_core']['files']} files; "
         f"UI formatter {'not run (node not found)' if ui is None else f'{ui[1]} cases, ' + ('all equal' if ui[0] else 'differ')} |",
         f"| V5 filter at the study's mains | {res[g['V5']['PASS']]} | largest difference {mx('V5_filtered_max_abs_diff_uv'):.2e} µV; "
         f"UI label template {static['ui_label_template']}; API carries the study's mains {static['api_file_carries_study_mains']} |",
         f"| V6 events = committed export (test subjects, session) | {res[g['V6']['PASS']]} | {g['V6']['match']} equal, "
         f"{g['V6']['differ']} differ, {g['V6']['no_reference']} without a committed reference |", "",
         "## By subject", "", "| subject | mode | mains | montage | input Hz | files | hours | V1 | V2 | V3 | V4 | V5 | V6 | "
         "AI events | peak MB |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    by = {}
    for r in rows:
        by.setdefault(r["subject"], []).append(r)
    for s, rs in by.items():
        ok = lambda k: sum(r[k] is True for r in rs)  # noqa: E731
        v6 = sum(r["V6"] is True for r in rs)
        L.append(f"| {s} | {rs[0]['mode']} | {rs[0]['mains_hz']:.0f} | {rs[0]['montage']} | {rs[0]['fs_in']:.0f} | "
                 f"{len(rs)} | {sum(r['hours'] for r in rs):.1f} | {ok('V1')} | {ok('V2')} | {ok('V3')} | "
                 f"{ok('V4_core')} | {ok('V5_data')} | {v6 if any(r['V6'] != 'no committed reference' for r in rs) else '—'} | "
                 f"{sum(r['events_ai'] for r in rs)} | {max(r['mem_peak_mb'] for r in rs):.0f} |")
    bad = [r for r in rows if not all(r.get(k) is True for k in GATE_KEYS) or r["V6"] is False]
    if bad:
        L += ["", "## Files with a failing check", "", "| subject | file | V1 | V2 | V3 | V4 | V5 | V6 |", "|---|---|---|---|---|---|---|---|"]
        for r in bad[:200]:
            L.append(f"| {r['subject']} | {r['file']} | {r['V1']} | {r['V2']} | {r['V3']} | {r['V4_core']} | "
                     f"{r['V5_data']} | {r['V6']} |")
    L += ["", "Not covered: the resampler for inputs not at 256 Hz is scipy's resample_poly, the same function as the "
          "app (not independent); derivations with an interpolated electrode are not compared (test E10); upload paths "
          "(Step 1 V7) are covered by the synthetic test E7 and the backend tests, not re-run here; file-mode events "
          "against the per-recording protocol = gate G2.", "",
          "Per file: `per_file.csv`; per channel: `channels.csv`; gates: `gates.json`."]
    (out / "VERIFY2.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return g


def write_private(rows):
    INBOX.mkdir(parents=True, exist_ok=True)
    L = ["# G9 -- private studies (PRIVATE, laptop only; never commit)", "",
         "| study | recording | input Hz | hours | V1 | V2 | V3 | V4 | V5 | interpolated | largest raw diff µV | "
         "largest filtered diff µV | AI events | peak MB |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['subject']} | {r['file']} | {r['fs_in']:.0f} | {r['hours']:.2f} | {r['V1']} | {r['V2']} | "
                 f"{r['V3']} | {r['V4_core']} | {r['V5_data']} | {r['interpolated'] or 'none'} | "
                 f"{r['V1_raw_max_abs_diff_uv']:.2e} | {r['V5_filtered_max_abs_diff_uv']:.2e} | {r['events_ai']} | "
                 f"{r['mem_peak_mb']:.0f} |")
    (INBOX / "C5_G9_PRIVATE.md").write_text("\n".join(L) + "\n", encoding="utf-8")


# ════════════════════════════════════════════════════════════════════ main
def db_read(db_path):
    con = sqlite3.connect(f"file:{Path(db_path).as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    subs = [dict(r) for r in con.execute("SELECT id, mode, mains_hz, private FROM subjects ORDER BY id")]
    files = [dict(r) for r in con.execute("SELECT id, subject_id, filename, start_time, duration_seconds, notice "
                                          "FROM files ORDER BY subject_id, filename")]
    events = [dict(r) for r in con.execute("SELECT id, file_id, source, onset_sec, offset_sec, review_status "
                                           "FROM events")]
    con.close()
    return subs, files, events


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chb", default=None)
    ap.add_argument("--siena", default=None)
    ap.add_argument("--db", default=str(BACKEND / "szscan.db"))
    ap.add_argument("--uploads", default=str(BACKEND / "uploads"))
    ap.add_argument("--subjects", nargs="*", default=None)
    ap.add_argument("--private", action="store_true", help="also check the private studies (inbox report only)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--tmp", default=None, help="folder for the temporary signal rows (default: system temp)")
    ap.add_argument("--smoke", action="store_true", help="the longest public file only")
    a = ap.parse_args(argv)
    t0 = time.time()
    subs, files, events = db_read(a.db)
    ws, _ = V1.import_backend()
    import engine_file as EF       # noqa: E402  (backend on sys.path after import_backend)
    min_s = EF.settings()["min_minutes"] * 60
    roots = dict(uploads=Path(a.uploads), chb=Path(a.chb) if a.chb else None, siena=Path(a.siena) if a.siena else None,
                 tmp=a.tmp)
    sums = {}
    if a.chb:
        sums.update(V1.load_sums(CHB_SUMS))
    if a.siena:
        sums.update(V1.load_sums(SIENA_SUMS))
    ev_ref = V1.load_ref_events(TIER2)
    static = static_checks()
    todo = []
    for s in subs:
        if a.subjects and s["id"] not in a.subjects:
            continue
        if s["private"]:
            if not a.private:
                continue
            s.update(kind="private", base=s["id"])
        else:
            m = ID_RE.match(s["id"])
            if not m:
                print(f"{s['id']}: not a CHB-MIT or Siena id, skipped")
                continue
            s.update(base=m.group(1), kind="chb" if m.group(1).startswith("chb") else "siena")
            if roots[s["kind"]] is None:
                raise SystemExit(f"STOP: {s['id']} needs --{s['kind']}")
        for f in files:
            if f["subject_id"] == s["id"]:
                todo.append((s, f))
    if a.smoke:
        pub = [t for t in todo if t[0]["kind"] != "private"]
        todo = [max(pub, key=lambda t: t[1]["duration_seconds"])] if pub else []
    if not todo:
        raise SystemExit("STOP: nothing to check")
    rows, chans, cases, prows, summ = [], [], [], [], {}
    for i, (s, f) in enumerate(todo):
        if s["kind"] == "chb" and s["base"] not in summ:
            summ[s["base"]] = V1.read_summary_times(V1.find_summary(roots["chb"], s["base"]))
        with Peak() as pk:
            r, c, case = check_file(f, s, roots, sums, summ.get(s["base"], {}), events, ev_ref, ws, min_s)
        r["mem_peak_mb"] = pk.peak
        if s["kind"] == "private":
            prows.append(r)
            print(f"[{i + 1}/{len(todo)}] private study {s['id']}: checked ({r['seconds']:.0f} s)", flush=True)
        else:
            rows.append(r); chans += c; cases.append(case)
            print(f"[{i + 1}/{len(todo)}] {s['id']} {f['filename']}: V1 {r['V1']} V2 {r['V2']} V3 {r['V3']} "
                  f"V4 {r['V4_core']} V5 {r['V5_data']} V6 {r['V6']} ({r['seconds']:.0f} s, {pk.peak:.0f} MB)", flush=True)
    with tempfile.TemporaryDirectory() as td:
        ui = V1.ui_time_check(cases, td) if cases else None
    commit, dirty = V1.git_state()
    meta = dict(commit=commit, dirty=dirty, seconds=time.time() - t0, hours=sum(r["hours"] for r in rows),
                subjects=sorted({r["subject"] for r in rows}), smoke=a.smoke,
                peak_mb_max=max([r["mem_peak_mb"] for r in rows + prows] or [0]),
                private_note=(f"{len(prows)} recording(s) checked, report in the private inbox" if prows
                              else "not checked in this run"))
    if a.smoke and rows:
        per_h = sum(r["seconds"] for r in rows) / max(meta["hours"], 1e-9)
        tot_h = sum(f["duration_seconds"] for f in files) / 3600
        meta.update(smoke_seconds_per_hour=round(per_h, 1), full_run_projection_h=round(per_h * tot_h / 3600, 2))
        print(f"SMOKE: {per_h:.1f} s per hour of EEG on the longest file; {tot_h:.1f} h in the database -> full run "
              f"≈ {per_h * tot_h / 3600:.2f} h (computed); peak memory {meta['peak_mb_max']:.0f} MB")
    if prows:
        write_private(prows)
    if rows:
        out = Path(a.out) if a.out else (OUT / "smoke" if a.smoke else OUT)
        g = write_public(out, rows, chans, static, ui, meta, a.smoke)
        print(json.dumps({k: v.get("PASS") for k, v in g.items() if isinstance(v, dict) and "PASS" in v}))
        print(f"report: {out / 'VERIFY2.md'}")
        return g
    return {}


if __name__ == "__main__":
    main()
