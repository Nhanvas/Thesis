#!/usr/bin/env python
"""
c5_szscan_verify.py -- chat C5 (Track C, Euréka), Step 1: verification of the review application SzScan as it is
today, against the author's checklist (board R216) and the EDF upload error seen at the defense.

READ ONLY on the application's state: the database is opened with SQLite's read-only URI mode, the upload cache
(`web_demo/backend/uploads/`) is only read (memory-mapped), nothing in `web_demo/` or `src/` is changed. V7 runs the
real FastAPI app on a TEMPORARY database and a TEMPORARY upload folder (patched module paths), never the real ones.

CHB-MIT ONLY. The script STOPs if the application's database holds a subject whose id is not `chbNN` (hospital
records must never enter a committed report; integrity rule 7). It writes only public CHB-MIT file names.

Checks (each on EVERY file of EVERY subject in the database, every one of the 18 channels, the whole recording):
  V1 source     sha256 of the EDF copy the app keeps (uploads/<subject>/<file>.edf) and of the dataset's EDF =
                PhysioNet SHA256SUMS (committed copy); the app's cached signal `{stem}.raw.npy` = the EDF re-read by an
                INDEPENDENT reader (numpy, written from the EDF specification; no MNE), every sample, every channel.
  V2 channels   the app's channel list = the 18 thesis derivations in the thesis order (literal list below, typed
                independently of the app); each cached channel = the EDF signal WITH THAT LABEL (not position);
                duplicated labels (CHB-MIT T8-P8) reported: which copy is used, and whether the copies are equal.
  V3 amplitude  the waveform function the endpoint calls (`waveform_serving.get_waveform`, exact call of main.py)
                returns µV: every bucket min / max over the whole file (10-min pages, 1,200 px) = the independent
                signal in µV; raw and filtered. Static: the endpoint calls that function; the EEG panel draws
                `raw_uv` / `filtered_uv` (no z-scored array reaches the browser).
  V4 time       file start time in the database = EDF header start time = CHB-MIT summary "File Start Time" (hours
                >= 24 taken modulo 24); duration in the database = EDF header records x record duration = summary
                End - Start; cached windows = floor(duration / 4 s); every event inside its file; the UI's time
                formatter (`frontend/src/time.js`, run with node) = start + offset for start, middle and end of
                every file.
  V5 filter     `{stem}.filtered.npy` = an independent whole-file zero-phase Butterworth band-pass (order 4,
                0.5-60 Hz) followed by an iirnotch (60 Hz, Q 30), every sample; the label shown in the UI
                (`AnalysisScreen.jsx`) states the same numbers as the code constants; frequency response printed.
  V6 events     the AI events in the database = the committed application-tier export
                `web_demo/report_handback/tier2_v4/` (the run scored 0.528, SUMMARY of `results/application_eval_v4/`)
                — onset, offset, file; review statuses and human events counted.
  V7 upload     FastAPI TestClient on temporary state: project id `chb01` (the defense case); chb01 files uploaded
                under a test id; non-EDF extension; referential EDF; 512-Hz EDF; truncated EDF; garbage bytes; peak
                memory of reading one file and of its Phase A (tracemalloc). Expectations are written in V7_CASES
                before the run; the observed toast / status is reported for every case.

Run (laptop, Git Bash, from F:/Study/Thesis/Code):
  PYTHONUTF8=1 python src/c5_szscan_verify.py --dataset F:/Study/Thesis/Dataset/CHB-MIT --smoke
  PYTHONUTF8=1 python src/c5_szscan_verify.py --dataset F:/Study/Thesis/Dataset/CHB-MIT
Outputs: results/c5_szscan/ (VERIFY.md, per_file.csv, channels.csv, v7_upload.csv, gates.json, run_meta.json);
smoke: results/c5_szscan/smoke/.
"""
import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import tracemalloc
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.signal import butter, filtfilt, iirnotch, sosfiltfilt, sosfreqz, freqz

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "web_demo" / "backend"
FRONTEND = ROOT / "web_demo" / "frontend" / "src"
DEFAULT_SUMS = ROOT / "results" / "r2" / "r0_data" / "chb" / "physionet_SHA256SUMS_chbmit.txt"
DEFAULT_TIER2 = ROOT / "web_demo" / "report_handback" / "tier2_v4"
DEFAULT_OUT = ROOT / "results" / "c5_szscan"

# The 18 bipolar derivations of the thesis (report Section 2.1.1), typed here independently of the application.
THESIS_CHANNELS = ["FP1-F7", "F7-T7", "T7-P7", "P7-O1", "FP1-F3", "F3-C3", "C3-P3", "P3-O1", "FP2-F4", "F4-C4",
                   "C4-P4", "P4-O2", "FP2-F8", "F8-T8", "T8-P8", "P8-O2", "FZ-CZ", "CZ-PZ"]
FS = 256
WIN = 1024                      # 4 s at 256 Hz
TOL_UV = 1e-3                   # µV; float32 rounding of a ±10 mV signal is < 1e-3 µV; one CHB-MIT LSB ≈ 0.195 µV
TOL_ENV_UV = 0.006              # µV; the endpoint rounds to 2 decimals
PAGE_S, PAGE_PX = 600.0, 1200   # V3 pages
UNIT = {"uv": 1e-6, "mv": 1e-3, "v": 1.0, "nv": 1e-9}


# ════════════════════════════════════════════════════════════════════ independent EDF reader (Kemp et al. 1992)
def edf_header(path):
    """Header of an EDF / EDF+ file read from the bytes, per the published specification."""
    path = Path(path)
    with open(path, "rb") as fh:
        h = fh.read(256)
        if len(h) < 256:
            raise ValueError("file shorter than the 256-byte EDF header")
        ns = int(h[252:256].decode("ascii").strip())
        s = fh.read(ns * 256)
    def field(off, width, i):
        start = ns * off + i * width
        return s[start:start + width].decode("latin-1").strip()
    sig = []
    offs = dict(label=(0, 16), transducer=(16, 80), physdim=(96, 8), physmin=(104, 8), physmax=(112, 8),
                digmin=(120, 8), digmax=(128, 8), prefilter=(136, 80), nsamp=(216, 8))
    for i in range(ns):
        d = {k: field(o, w, i) for k, (o, w) in offs.items()}
        for k in ("physmin", "physmax"):
            d[k] = float(d[k])
        for k in ("digmin", "digmax", "nsamp"):
            d[k] = int(d[k])
        sig.append(d)
    hdr_bytes = int(h[184:192].decode("ascii").strip())
    n_rec_hdr = int(h[236:244].decode("ascii").strip())
    rec_dur = float(h[244:252].decode("ascii").strip())
    rec_samples = sum(d["nsamp"] for d in sig)
    size = path.stat().st_size
    n_rec_file = (size - hdr_bytes) // (2 * rec_samples)
    return dict(startdate=h[168:176].decode("ascii"), starttime=h[176:184].decode("ascii"), hdr_bytes=hdr_bytes,
                n_rec_hdr=n_rec_hdr, n_rec_file=int(n_rec_file), rec_dur=rec_dur, ns=ns, signals=sig,
                rec_samples=rec_samples, size=size,
                trailing_bytes=int((size - hdr_bytes) - n_rec_file * 2 * rec_samples))


def edf_signal_volts(path, hdr, idx):
    """One signal as float64 volts over the records present in the file (min of header count and file size)."""
    n_rec = hdr["n_rec_file"] if hdr["n_rec_hdr"] < 0 else min(hdr["n_rec_hdr"], hdr["n_rec_file"])
    mm = np.memmap(path, dtype="<i2", mode="r", offset=hdr["hdr_bytes"], shape=(n_rec, hdr["rec_samples"]))
    start = sum(hdr["signals"][j]["nsamp"] for j in range(idx))
    s = hdr["signals"][idx]
    dig = np.asarray(mm[:, start:start + s["nsamp"]], dtype=np.float64).reshape(-1)
    del mm
    gain = (s["physmax"] - s["physmin"]) / (s["digmax"] - s["digmin"])
    phys = (dig - s["digmin"]) * gain + s["physmin"]
    return phys * unit_scale(s["physdim"])


def unit_scale(dim):
    """Physical dimension of an EDF signal -> factor to volts."""
    d = dim.strip().replace("\u03bc", "u").replace("\u00b5", "u").lower()
    if d not in UNIT:
        raise ValueError(f"unknown physical dimension {dim!r}")
    return UNIT[d]


def label_index(hdr):
    """{normalised label: [indices]} -- labels upper-cased and stripped, as the montage names are written."""
    out = {}
    for i, s in enumerate(hdr["signals"]):
        out.setdefault(s["label"].upper().strip(), []).append(i)
    return out


def write_edf(path, labels, fs, data_uv, starttime="12.00.00", startdate="01.01.01", rec_dur=1,
              phys=(-6400.0, 6400.0), header_records=None, physdim="uV"):
    """Minimal EDF writer (16-bit) -- synthetic test files and V7 test files only."""
    data_uv = np.asarray(data_uv, float)
    ns, n = data_uv.shape
    spr = int(fs * rec_dur)
    n_rec = n // spr
    dmin, dmax = -32768, 32767
    def f(x, w):
        t = str(x)[:w]
        return t + " " * (w - len(t))
    h = f("0", 8) + f("X X X X", 80) + f("Startdate X X X X", 80) + f(startdate, 8) + f(starttime, 8)
    h += f(256 + 256 * ns, 8) + f("", 44) + f(n_rec if header_records is None else header_records, 8)
    h += f(rec_dur, 8) + f(ns, 4)
    for key, w in (("label", 16), ("tr", 80), ("dim", 8), ("pmin", 8), ("pmax", 8), ("dmin", 8), ("dmax", 8),
                   ("pre", 80), ("ns", 8), ("res", 32)):
        for i in range(ns):
            v = dict(label=labels[i], tr="", dim=physdim, pmin=phys[0], pmax=phys[1], dmin=dmin, dmax=dmax,
                     pre="", ns=spr, res="")[key]
            h += f(v, w)
    gain = (phys[1] - phys[0]) / (dmax - dmin)
    dig = np.clip(np.round((data_uv[:, :n_rec * spr] - phys[0]) / gain + dmin), dmin, dmax).astype("<i2")
    body = dig.reshape(ns, n_rec, spr).transpose(1, 0, 2).tobytes()
    Path(path).write_bytes(h.encode("latin-1") + body)


# ════════════════════════════════════════════════════════════════════ independent filter (V5)
def indep_filters(notch_hz=60.0):
    sos = butter(4, [0.5, 60.0], btype="bandpass", fs=FS, output="sos")
    b, a = iirnotch(notch_hz, 30.0, fs=FS)
    return sos, b, a


def indep_filter(x, notch_hz=60.0):
    sos, b, a = indep_filters(notch_hz)
    return filtfilt(b, a, sosfiltfilt(sos, x))


def freq_response(notch_hz=60.0):
    """|H|^2 of each one-pass filter (zero-phase = squared magnitude), in dB, at a few frequencies."""
    sos, b, a = indep_filters(notch_hz)
    f = np.array([0.25, 0.5, 1.0, 45.0, 50.0, 59.0, 60.0, 61.0, 70.0])
    _, hb = sosfreqz(sos, worN=f, fs=FS)
    _, hn = freqz(b, a, worN=f, fs=FS)
    db = 20 * np.log10(np.maximum(np.abs(hb * hn) ** 2, 1e-30))
    return {float(fi): round(float(d), 2) for fi, d in zip(f, db)}


# ════════════════════════════════════════════════════════════════════ helpers
def sha256(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def load_sums(path):
    sums = {}
    for line in Path(path).read_text().splitlines():
        p = line.strip().split(maxsplit=1)
        if len(p) == 2 and re.fullmatch(r"[0-9a-fA-F]{64}", p[0]):
            rel = p[1].strip().lstrip("*")
            sums[rel[2:] if rel.startswith("./") else rel] = p[0].lower()
    if not sums:
        raise SystemExit(f"STOP: no parsable line in {path}")
    return sums


def hms_to_s(t):
    h, m, s = (int(x) for x in re.split(r"[:.]", t.strip()))
    return h * 3600 + m * 60 + s


def read_summary_times(path):
    """{file name: (start 'HH:MM:SS', end 'HH:MM:SS')} -- only the name and the two time lines are read."""
    out, cur = {}, None
    if path is None or not Path(path).exists():
        return out
    for line in Path(path).read_text(errors="replace").splitlines():
        m = re.match(r"\s*File Name:\s*(\S+)", line)
        if m:
            cur = m.group(1).strip()
            out[cur] = [None, None]
            continue
        m = re.match(r"\s*File Start Time:\s*(\S+)", line)
        if m and cur:
            out[cur][0] = m.group(1)
        m = re.match(r"\s*File End Time:\s*(\S+)", line)
        if m and cur:
            out[cur][1] = m.group(1)
    return {k: tuple(v) for k, v in out.items()}


def find_summary(dataset, sid, summary_dir=None):
    for p in ([Path(summary_dir) / f"{sid}-summary.txt", Path(summary_dir) / f"{sid}-summary.md"] if summary_dir
              else []) + [Path(dataset) / sid / f"{sid}-summary.txt", Path(dataset) / sid / f"{sid}-summary.md",
                          Path(dataset) / "CHB info" / "summary" / f"{sid}-summary.md"]:
        if p.exists():
            return p
    return None


def db_read(db_path):
    con = sqlite3.connect(f"file:{Path(db_path).as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    subs = [r["id"] for r in con.execute("SELECT id FROM subjects ORDER BY id")]
    files = [dict(r) for r in con.execute("SELECT id, subject_id, filename, start_time, duration_seconds "
                                          "FROM files ORDER BY subject_id, filename")]
    events = [dict(r) for r in con.execute("SELECT id, file_id, source, onset_sec, offset_sec, review_status "
                                           "FROM events ORDER BY file_id, onset_sec, id")]
    con.close()
    return subs, files, events


def import_backend():
    for p in (BACKEND,):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    import waveform_serving as ws          # noqa: E402  (imports pipeline_demo, the app's own code)
    import pipeline_demo as pdm            # noqa: E402
    return ws, pdm


# ════════════════════════════════════════════════════════════════════ static checks (V3, V5)
def static_checks():
    out = {}
    main_src = (BACKEND / "main.py").read_text(encoding="utf-8")
    out["endpoint_calls_get_waveform"] = bool(re.search(
        r"return ws\.get_waveform\(f\[\"subject_id\"\], f\[\"filename\"\], um\.UPLOAD_DIR, start_sec, end_sec, "
        r"width_px\)", main_src))
    panel = (FRONTEND / "components" / "EegPanel.jsx").read_text(encoding="utf-8")
    out["panel_draws_raw_uv"] = "drawSeries(waveform.raw_uv" in panel
    out["panel_draws_filtered_uv"] = "waveform.filtered_uv" in panel
    api = (FRONTEND / "api.js").read_text(encoding="utf-8")
    out["frontend_fetches_waveform_endpoint"] = "/waveform?start_sec=" in api
    ws_src = (BACKEND / "waveform_serving.py").read_text(encoding="utf-8")
    out["waveform_reads_raw_and_filtered_cache"] = ('f"{stem}.raw.npy"' in ws_src and 'f"{stem}.filtered.npy"' in ws_src)
    screen = (FRONTEND / "screens" / "AnalysisScreen.jsx").read_text(encoding="utf-8")
    m = re.search(r'label="Preprocessed \(([^)]*)\)"', screen)
    out["ui_filter_label"] = m.group(1) if m else None
    nums = re.findall(r"[\d.]+", m.group(1)) if m else []
    out["ui_label_numbers"] = nums
    _, pdm = import_backend()
    P = pdm.preprocessing
    sos, b, a = indep_filters(60.0)
    out["code_bandpass_equals_butter4_0.5_60"] = bool(np.array_equal(P._BP_SOS, sos))
    out["code_notch_equals_iirnotch_60_q30"] = bool(np.array_equal(P._NOTCH_B, b) and np.array_equal(P._NOTCH_A, a))
    out["code_notch_hz"] = float(pdm.NOTCH_HZ)
    out["ui_label_matches_code"] = (nums == ["0.5", "60", "60"] and out["code_bandpass_equals_butter4_0.5_60"]
                                    and out["code_notch_equals_iirnotch_60_q30"] and pdm.NOTCH_HZ == 60.0)
    out["app_channels"] = list(pdm.preprocessing.COMMON_CHANNELS)
    out["app_channels_equal_thesis"] = list(pdm.preprocessing.COMMON_CHANNELS) == THESIS_CHANNELS
    out["freq_response_db"] = freq_response(60.0)
    return out


# ════════════════════════════════════════════════════════════════════ per-file checks V1-V6
def check_file(f, ds_dir, up_dir, sums, summ, ev_db, ev_ref, ws, timings):
    sid, fn = f["subject_id"], f["filename"]
    stem = Path(fn).stem
    row = dict(subject=sid, file=fn)
    chans = []
    t0 = time.perf_counter()
    copy_edf, src_edf = up_dir / sid / fn, ds_dir / sid / fn
    want = sums.get(f"{sid}/{fn}")
    row["physionet_sum_listed"] = want is not None
    row["copy_present"] = copy_edf.exists()
    row["copy_sha_ok"] = (sha256(copy_edf) == want) if (copy_edf.exists() and want) else False
    row["dataset_sha_ok"] = (sha256(src_edf) == want) if (src_edf.exists() and want) else False
    edf = copy_edf if copy_edf.exists() else src_edf
    hdr = edf_header(edf)
    row["edf_read"] = "app copy" if copy_edf.exists() else "dataset"
    row["n_rec_hdr"], row["n_rec_file"], row["trailing_bytes"] = hdr["n_rec_hdr"], hdr["n_rec_file"], hdr["trailing_bytes"]
    fs_ok = all(s["nsamp"] == int(FS * hdr["rec_dur"]) for s in hdr["signals"])
    row["all_signals_256Hz"] = fs_ok
    lab = label_index(hdr)
    raw_mm = np.load(up_dir / sid / f"{stem}.raw.npy", mmap_mode="r")
    flt_mm = np.load(up_dir / sid / f"{stem}.filtered.npy", mmap_mode="r")
    n_win = raw_mm.shape[0]
    n_rec = min(hdr["n_rec_hdr"], hdr["n_rec_file"]) if hdr["n_rec_hdr"] >= 0 else hdr["n_rec_file"]
    n_samp = n_rec * int(FS * hdr["rec_dur"])
    row["n_windows_cache"] = n_win
    row["n_windows_expected"] = n_samp // WIN
    row["windows_ok"] = (n_win == n_samp // WIN and raw_mm.shape[1:] == (18, WIN) and flt_mm.shape == raw_mm.shape)
    score_p = up_dir / sid / f"{stem}.score.npy"
    row["score_len_ok"] = score_p.exists() and int(np.load(score_p, mmap_mode="r").shape[0]) == n_win
    usable = n_win * WIN
    raw_ind = np.empty((18, usable), np.float32)
    flt_ind = np.empty((18, usable), np.float32)
    v1_max, v5_max, v2_ok, v1_ok = 0.0, 0.0, True, True
    for c, ch in enumerate(THESIS_CHANNELS):
        idxs = lab.get(ch, [])
        cr = dict(subject=sid, file=fn, channel=ch, n_with_label=len(idxs))
        if not idxs:
            cr.update(present=False)
            chans.append(cr); v2_ok = v1_ok = False
            continue
        x = edf_signal_volts(edf, hdr, idxs[0])
        if len(idxs) > 1:
            dup = [float(np.max(np.abs(edf_signal_volts(edf, hdr, j) - x)) * 1e6) for j in idxs[1:]]
            cr["duplicates_max_abs_diff_uv"] = max(dup)
        app = np.asarray(raw_mm[:, c, :], np.float64).reshape(-1)
        d = float(np.max(np.abs(app - x[:usable]))) * 1e6
        cr["raw_max_abs_diff_uv"] = d
        if d > TOL_UV:
            # which EDF signal (if any) does the cached channel equal? (diagnostic for V2)
            best = None
            for lbl, js in lab.items():
                for j in js:
                    if hdr["signals"][j]["nsamp"] != int(FS * hdr["rec_dur"]):
                        continue
                    dj = float(np.max(np.abs(app - edf_signal_volts(edf, hdr, j)[:usable]))) * 1e6
                    if best is None or dj < best[1]:
                        best = (f"{lbl}#{j}", dj)
            cr["cache_matches_label"] = best[0] if best and best[1] <= TOL_UV else "none"
            v1_ok = False
            if best and best[1] <= TOL_UV and best[0].split("#")[0] != ch:
                v2_ok = False
        fi = indep_filter(x)[:usable]
        appf = np.asarray(flt_mm[:, c, :], np.float64).reshape(-1)
        df = float(np.max(np.abs(appf - fi))) * 1e6
        cr["filtered_max_abs_diff_uv"] = df
        raw_ind[c] = x[:usable]
        flt_ind[c] = fi
        v1_max, v5_max = max(v1_max, d), max(v5_max, df)
        cr["present"] = True
        chans.append(cr)
    row["V1_raw_max_abs_diff_uv"] = v1_max
    row["V1"] = bool(row["copy_sha_ok"] and v1_ok and row["windows_ok"] and fs_ok)
    row["V2"] = bool(v2_ok and all(c.get("present") for c in chans))
    row["V5_filtered_max_abs_diff_uv"] = v5_max
    row["V5_data"] = bool(v5_max <= TOL_UV)
    t1 = time.perf_counter()

    # V3 -- the endpoint's own function, whole file in pages; buckets compared to the independent signal in µV
    dur = usable / FS
    v3_raw, v3_flt, v3_ok, pages = 0.0, 0.0, True, 0
    start = 0.0
    while start < dur:
        end = min(dur, start + PAGE_S)
        w = ws.get_waveform(sid, fn, up_dir, start, end, PAGE_PX)
        if w["channels"] != THESIS_CHANNELS:
            v3_ok = False
        a_ = int(round(start * FS)); b_ = int(round(end * FS))
        edges = np.round(np.linspace(0, b_ - a_, PAGE_PX + 1)).astype(np.int64)
        for key, ind in (("raw_uv", raw_ind), ("filtered_uv", flt_ind)):
            got = np.asarray(w[key], float)                         # [18, n_buckets, 2]
            seg = ind[:, a_:b_].astype(np.float64) * 1e6
            mins = np.empty((18, PAGE_PX)); maxs = np.empty((18, PAGE_PX))
            for bk in range(PAGE_PX):
                lo = edges[bk]; hi = min(max(edges[bk + 1], lo + 1), b_ - a_)
                mins[:, bk] = seg[:, lo:hi].min(axis=1); maxs[:, bk] = seg[:, lo:hi].max(axis=1)
            dd = float(max(np.max(np.abs(got[:, :, 0] - mins)), np.max(np.abs(got[:, :, 1] - maxs))))
            if key == "raw_uv":
                v3_raw = max(v3_raw, dd)
            else:
                v3_flt = max(v3_flt, dd)
        pages += 1
        start = end
    row["V3_pages"] = pages
    row["V3_raw_env_max_abs_diff_uv"] = v3_raw
    row["V3_filtered_env_max_abs_diff_uv"] = v3_flt
    row["V3"] = bool(v3_ok and v3_raw <= TOL_ENV_UV and v3_flt <= TOL_ENV_UV)
    t2 = time.perf_counter()

    # V4 -- time
    db_start = datetime.fromisoformat(f["start_time"])
    hdr_start = hms_to_s(hdr["starttime"])
    row["db_start_hms"] = db_start.strftime("%H:%M:%S")
    row["edf_start_hms"] = hdr["starttime"].replace(".", ":")
    row["start_db_eq_edf"] = (db_start.hour * 3600 + db_start.minute * 60 + db_start.second) == hdr_start
    edf_dur = n_rec * hdr["rec_dur"]
    row["duration_db_s"], row["duration_edf_s"] = f["duration_seconds"], edf_dur
    row["duration_db_eq_edf"] = abs(f["duration_seconds"] - edf_dur) < 1e-6
    s_t = summ.get(fn)
    if s_t and s_t[0]:
        row["summary_start"], row["summary_end"] = s_t
        row["start_summary_eq_edf"] = hms_to_s(s_t[0]) % 86400 == hdr_start
        if s_t[1]:
            sd = (hms_to_s(s_t[1]) - hms_to_s(s_t[0])) % 86400
            row["summary_duration_s"] = sd
            row["duration_summary_eq_edf"] = abs(sd - edf_dur) <= 1.0
    else:
        row["summary_start"] = "not in summary"
    row["dropped_tail_s"] = edf_dur - usable / FS
    evs = [e for e in ev_db if e["file_id"] == f["id"]]
    row["events_db"] = len(evs)
    row["events_inside_file"] = all(0 <= e["onset_sec"] < e["offset_sec"] <= usable / FS + 1e-9 for e in evs)
    v4 = (row["start_db_eq_edf"] and row["duration_db_eq_edf"] and row["events_inside_file"]
          and row.get("start_summary_eq_edf", True) and row.get("duration_summary_eq_edf", True)
          and 0 <= row["dropped_tail_s"] < 4)
    row["V4_core"] = bool(v4)

    # V6 -- events against the committed application-tier export
    ai = sorted((round(e["onset_sec"], 6), round(e["offset_sec"], 6)) for e in evs if e["source"] == "AI")
    row["events_ai"], row["events_human"] = len(ai), sum(e["source"] == "Human" for e in evs)
    row["events_reviewed"] = sum(e["source"] == "AI" and e["review_status"] not in (None, "Unseen") for e in evs)
    ref = ev_ref.get((sid, fn))
    if ref is None:
        row["V6"] = "no committed reference"
    else:
        row["events_ref"] = len(ref)
        row["V6"] = bool(ai == sorted(ref))
    timings.append(dict(file=fn, hours=edf_dur / 3600, v1_v2_v5_s=t1 - t0, v3_s=t2 - t1))
    del raw_ind, flt_ind
    return row, chans, dict(start_iso=f["start_time"], dur=f["duration_seconds"], usable=usable / FS,
                            hdr_start=hdr_start, file=fn, subject=sid)


def load_ref_events(tier2):
    out = {}
    tier2 = Path(tier2)
    for p in sorted(tier2.glob("chb*_events.csv")):
        with open(p, newline="") as fh:
            for r in csv.DictReader(fh):
                if r["source"] == "AI":
                    out.setdefault((r["subject"], r["file_name"]), []).append(
                        (round(float(r["onset_s"]), 6), round(float(r["offset_s"]), 6)))
    # files of the export without events have an empty list
    fp = tier2 / "files.csv"
    if fp.exists():
        with open(fp, newline="") as fh:
            for r in csv.DictReader(fh):
                out.setdefault((r["subject"], r["file_name"]), [])
    return out


def ui_time_check(cases, workdir):
    """Runs frontend/src/time.js's formatFileTime with node on every case; returns (ok, n, details) or None."""
    node = shutil.which("node")
    if node is None:
        return None
    workdir = Path(workdir)
    (workdir / "time.mjs").write_text((FRONTEND / "time.js").read_text(encoding="utf-8"), encoding="utf-8")
    tests = []
    for c in cases:
        for off in (0.0, round(c["usable"] / 2, 3), max(0.0, c["usable"] - 1.0)):
            exp = int(c["hdr_start"] + off) % 86400
            want = f"{exp // 3600:02d}:{exp % 3600 // 60:02d}:{exp % 60:02d}"
            if c["dur"] >= 86400:
                want = f"d{int(off // 86400) + 1} " + want
            tests.append(dict(file=c["file"], iso=c["start_iso"], off=off, dur=c["dur"], want=want))
    (workdir / "cases.json").write_text(json.dumps(tests), encoding="utf-8")
    (workdir / "run.mjs").write_text(
        "import {formatFileTime} from './time.mjs';import fs from 'fs';"
        "const t=JSON.parse(fs.readFileSync('cases.json','utf8'));"
        "fs.writeFileSync('out.json',JSON.stringify(t.map(c=>formatFileTime(c.iso,c.off,c.dur))));",
        encoding="utf-8")
    subprocess.run([node, "run.mjs"], cwd=str(workdir), check=True, capture_output=True, text=True)
    got = json.loads((workdir / "out.json").read_text(encoding="utf-8"))
    bad = [dict(t, got=g) for t, g in zip(tests, got) if g != t["want"]]
    return (not bad, len(tests), bad[:10])


# ════════════════════════════════════════════════════════════════════ V7 -- upload paths on temporary state
V7_CASES = [
    # id, what, expectation written before the run (the observed outcome is reported beside it)
    ("U1", "start a session with project id chb01 (the defense case)", "rejected: 422 'This demo is restricted to the held-out test subjects.'"),
    ("U2", "project id chb03, upload chb01_01.edf (no seizure)", "accepted (Phase A ok): the app does not check that a file belongs to the subject"),
    ("U3", "same session, upload chb01_03.edf (with a seizure)", "accepted (Phase A ok)"),
    ("U4", "Phase B of that session (two chb01 files under chb03)", "runs (GAE + distances); nothing written to the real database"),
    ("U5", "upload a file named .txt", "rejected: 422 'File rejected — unsupported format or channel configuration.'"),
    ("U6", "referential EDF, 19 electrodes named 'EEG Fp1-REF' …, 256 Hz", "file error 'File rejected — unsupported format or channel configuration.'"),
    ("U7", "bipolar EDF with the 18 names at 512 Hz", "file error 'File rejected …'"),
    ("U8", "chb01_01.edf truncated to half its data, header unchanged", "not specified in advance: observed behaviour reported"),
    ("U9", "garbage bytes named .edf", "file error 'File rejected …'"),
    ("U10", "memory: bytes held by the upload handler; tracemalloc peak of Phase A on chb01_01", "measured"),
]


def run_v7(dataset, out_dir, phase_b_timeout_s=1800):
    rows = []
    ds = Path(dataset)
    tmp = Path(tempfile.mkdtemp(prefix="c5_v7_"))
    os.environ.setdefault("ADMIN_USER", "c5_v7_user")
    os.environ.setdefault("ADMIN_PASS", "c5_v7_pass")
    import_backend()
    import db                                 # noqa: E402
    import upload_manager as um               # noqa: E402
    real_db, real_up = db.DB_PATH, um.UPLOAD_DIR
    db.DB_PATH = tmp / "szscan_v7.db"
    um.UPLOAD_DIR = tmp / "uploads"
    um.UPLOAD_DIR.mkdir(parents=True)
    try:
        import main                           # noqa: E402
        from fastapi.testclient import TestClient
        exp = {c[0]: (c[1], c[2]) for c in V7_CASES}
        user, pw = main.ADMIN_USER, main.ADMIN_PASS
        with TestClient(main.app) as cl:
            r = cl.post("/api/login", json=dict(username=user, password=pw))
            assert r.status_code == 200, f"V7 login failed {r.status_code}"

            def rec(cid, observed, ok=None):
                rows.append(dict(case=cid, what=exp[cid][0], expected=exp[cid][1], observed=observed,
                                 as_expected="" if ok is None else ("yes" if ok else "NO")))

            def wait_files(timeout=900):
                t0 = time.time()
                while time.time() - t0 < timeout:
                    s = cl.get("/api/uploads/current").json()
                    if all(x["status"] != "uploading" for x in s["files"]):
                        return s
                    time.sleep(0.5)
                return cl.get("/api/uploads/current").json()

            def upload(name, data):
                return cl.post("/api/uploads/current/files", files={"file": (name, data, "application/octet-stream")})

            def status_of(snap, name):
                for x in snap["files"]:
                    if x["filename"] == name:
                        return f"{x['status']}" + (f": {x['error']}" if x["error"] else "")
                return "not listed (removed)"

            # U1
            r = cl.post("/api/uploads/current", json=dict(project_id="chb01", memo=""))
            rec("U1", f"{r.status_code} {r.json().get('detail')}",
                r.status_code == 422 and r.json().get("detail") == um.REJECTED_SUBJECT_MESSAGE)
            # U2-U4
            assert cl.post("/api/uploads/current", json=dict(project_id="chb03", memo="")).status_code == 200
            f1, f3 = ds / "chb01" / "chb01_01.edf", ds / "chb01" / "chb01_03.edf"
            for cid, p in (("U2", f1), ("U3", f3)):
                if not p.exists():
                    rec(cid, f"not run: {p.name} not found in the dataset"); continue
                r = upload(p.name, p.read_bytes())
                snap = wait_files()
                rec(cid, f"{r.status_code}; {status_of(snap, p.name)}", "uploaded" == status_of(snap, p.name))
            t0 = time.time(); snap = None
            while time.time() - t0 < phase_b_timeout_s:
                snap = cl.get("/api/uploads/current").json()
                if snap["phase_b_done"] or snap["error"]:
                    break
                time.sleep(2)
            rec("U4", (f"phase_b_done={snap['phase_b_done']} error={snap['error']} after {time.time() - t0:.0f} s"
                       if snap else "no session"), bool(snap and snap["phase_b_done"] and not snap["error"]))
            cl.delete("/api/uploads/current")
            # U5-U9 in one fresh session
            assert cl.post("/api/uploads/current", json=dict(project_id="chb03", memo="")).status_code == 200
            r = upload("notes.txt", b"hello")
            rec("U5", f"{r.status_code} {r.json().get('detail')}",
                r.status_code == 422 and r.json().get("detail") == um.REJECTED_FILE_MESSAGE)
            rng = np.random.default_rng(0)
            refl = ["EEG Fp1-REF", "EEG Fp2-REF", "EEG F3-REF", "EEG F4-REF", "EEG C3-REF", "EEG C4-REF", "EEG P3-REF",
                    "EEG P4-REF", "EEG O1-REF", "EEG O2-REF", "EEG F7-REF", "EEG F8-REF", "EEG T3-REF", "EEG T4-REF",
                    "EEG T5-REF", "EEG T6-REF", "EEG Fz-REF", "EEG Cz-REF", "EEG Pz-REF"]
            p6 = tmp / "u6_ref.edf"; write_edf(p6, refl, 256, rng.normal(0, 30, (19, 256 * 60)))
            p7 = tmp / "u7_512.edf"; write_edf(p7, THESIS_CHANNELS, 512, rng.normal(0, 30, (18, 512 * 60)))
            p9 = tmp / "u9_garbage.edf"; p9.write_bytes(rng.integers(0, 255, 50000, dtype=np.uint8).tobytes())
            for cid, p in (("U6", p6), ("U7", p7), ("U9", p9)):
                upload(p.name, p.read_bytes())
                snap = wait_files()
                st = status_of(snap, p.name)
                rec(cid, st, st == f"error: {um.REJECTED_FILE_MESSAGE}")
            if f1.exists():
                b = f1.read_bytes(); h = edf_header(f1)
                half = h["hdr_bytes"] + (len(b) - h["hdr_bytes"]) // 2
                p8 = tmp / "u8_trunc.edf"; p8.write_bytes(b[:half])
                upload(p8.name, p8.read_bytes())
                snap = wait_files()
                st = status_of(snap, p8.name)
                extra = ""
                fa = um.get_current().files.get(p8.name) if um.get_current() else None
                if fa is not None and fa.phase_a is not None:
                    extra = (f"; header says {h['n_rec_hdr']} s, file holds {edf_header(p8)['n_rec_file']} s, "
                             f"app windows {fa.phase_a.n_windows}, app duration {fa.phase_a.file_duration_seconds:.0f} s")
                rec("U8", st + extra)
            else:
                rec("U8", "not run: chb01_01.edf not found")
            t0 = time.time()                  # let any Phase B started by this session finish before discarding
            while time.time() - t0 < phase_b_timeout_s:
                s_ = cl.get("/api/uploads/current").json()
                if s_["phase_b_done"] or s_["error"] or not any(x["status"] == "uploaded" for x in s_["files"]):
                    break
                time.sleep(2)
            cl.delete("/api/uploads/current")
        # U10 -- memory of the upload handler (bytes object = file size, by the code) and Phase A peak
        if f1.exists():
            import pipeline_demo as pdm       # noqa: E402
            size = f1.stat().st_size
            tracemalloc.start()
            pa = pdm.process_file_phase_a(str(f1), None, tmp / "u10")
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            hours = pa.file_duration_seconds / 3600
            rec("U10", f"upload handler holds the whole file in memory (main.py `await file.read()`): {size / 1e6:.1f} MB "
                       f"for {hours:.2f} h x {edf_header(f1)['ns']} signals; Phase A traced peak {peak / 1e6:.0f} MB "
                       f"({peak / 1e6 / hours:.0f} MB per hour of EEG, 18 channels)")
    finally:
        db.DB_PATH, um.UPLOAD_DIR = real_db, real_up
        shutil.rmtree(tmp, ignore_errors=True)
    with open(Path(out_dir) / "v7_upload.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["case", "what", "expected", "observed", "as_expected"])
        w.writeheader(); w.writerows(rows)
    return rows


# ════════════════════════════════════════════════════════════════════ report
def write_report(out, rows, chans, static, ui, v7, meta, smoke):
    def n_ok(key):
        vals = [r.get(key) for r in rows]
        return sum(v is True for v in vals), len(vals)
    gates = {}
    for k in ("V1", "V2", "V3", "V4_core", "V5_data"):
        ok, n = n_ok(k)
        gates[k] = dict(pass_files=ok, files=n, PASS=(ok == n and n > 0))
    gates["V2"]["PASS"] = gates["V2"]["PASS"] and static["app_channels_equal_thesis"]
    gates["V3"]["PASS"] = gates["V3"]["PASS"] and all(static[k] for k in (
        "endpoint_calls_get_waveform", "panel_draws_raw_uv", "panel_draws_filtered_uv",
        "frontend_fetches_waveform_endpoint", "waveform_reads_raw_and_filtered_cache"))
    gates["V4_ui"] = dict(PASS=None if ui is None else ui[0], cases=None if ui is None else ui[1])
    gates["V4"] = dict(PASS=gates["V4_core"]["PASS"] and (ui is None or ui[0]), node_run=ui is not None)
    gates["V5"] = dict(PASS=gates["V5_data"]["PASS"] and static["ui_label_matches_code"])
    v6 = [r["V6"] for r in rows]
    gates["V6"] = dict(match=sum(v is True for v in v6), differ=sum(v is False for v in v6),
                       no_reference=sum(v == "no committed reference" for v in v6),
                       PASS=(sum(v is False for v in v6) == 0 and sum(v is True for v in v6) > 0))
    if v7 is not None:
        gates["V7"] = dict(cases=len(v7), not_as_expected=[r["case"] for r in v7 if r["as_expected"] == "NO"])
    (out / "gates.json").write_text(json.dumps(gates, indent=1, default=str), encoding="utf-8")
    (out / "run_meta.json").write_text(json.dumps(meta, indent=1, default=str), encoding="utf-8")
    for name, data in (("per_file.csv", rows), ("channels.csv", chans)):
        keys = sorted({k for r in data for k in r}, key=lambda k: (k not in ("subject", "file", "channel"), k))
        with open(out / name, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(data)

    L = [f"# SzScan verification (chat C5, Step 1){' — SMOKE' if smoke else ''}", "",
         f"Code `src/c5_szscan_verify.py`; repository commit `{meta['commit']}` "
         f"(uncommitted changes in web_demo/ or src/: {meta['dirty']}); run time {meta['seconds']:.0f} s; "
         f"subjects {', '.join(meta['subjects'])}; files {len(rows)}; {meta['hours']:.2f} h of EEG. "
         "Read only on the application's database and upload cache. Every check covers every file, every one of the "
         "18 channels and the whole recording of every subject in the database.", "",
         "| check | result | detail |", "|---|---|---|"]
    def res(p):
        return "PASS" if p is True else ("FAIL" if p is False else "not run")
    L.append(f"| V1 source (sha256, cached signal = independent EDF reader) | {res(gates['V1']['PASS'])} | "
             f"{gates['V1']['pass_files']} / {gates['V1']['files']} files; largest difference "
             f"{max((r['V1_raw_max_abs_diff_uv'] for r in rows), default=0):.2e} µV (tolerance {TOL_UV} µV) |")
    L.append(f"| V2 channels (18 names, order, label match) | {res(gates['V2']['PASS'])} | app list = thesis list: "
             f"{static['app_channels_equal_thesis']}; {gates['V2']['pass_files']} / {gates['V2']['files']} files |")
    L.append(f"| V3 amplitude in µV (endpoint function, whole file) | {res(gates['V3']['PASS'])} | "
             f"largest bucket difference raw {max((r['V3_raw_env_max_abs_diff_uv'] for r in rows), default=0):.3f} µV, "
             f"filtered {max((r['V3_filtered_env_max_abs_diff_uv'] for r in rows), default=0):.3f} µV "
             f"(tolerance {TOL_ENV_UV} µV); static checks "
             f"{sum(bool(static[k]) for k in ('endpoint_calls_get_waveform', 'panel_draws_raw_uv', 'panel_draws_filtered_uv', 'frontend_fetches_waveform_endpoint', 'waveform_reads_raw_and_filtered_cache'))} / 5 |")
    L.append(f"| V4 time (start, duration, events, UI formatter) | {res(gates['V4']['PASS'])} | "
             f"{gates['V4_core']['pass_files']} / {gates['V4_core']['files']} files; UI formatter "
             f"{'not run (node not found)' if ui is None else f'{ui[1]} cases, ' + ('all equal' if ui[0] else f'{len(ui[2])}+ differ')} |")
    L.append(f"| V5 filter (data + label) | {res(gates['V5']['PASS'])} | largest difference "
             f"{max((r['V5_filtered_max_abs_diff_uv'] for r in rows), default=0):.2e} µV; UI label "
             f"'{static['ui_filter_label']}'; code notch {static['code_notch_hz']} Hz |")
    L.append(f"| V6 events = committed application-tier export | {res(gates['V6']['PASS'])} | "
             f"{gates['V6']['match']} files equal, {gates['V6']['differ']} differ, "
             f"{gates['V6']['no_reference']} without a committed reference |")
    if v7 is not None:
        L.append(f"| V7 upload paths | see table | {len(v7)} cases; not as expected: "
                 f"{', '.join(gates['V7']['not_as_expected']) or 'none'} |")
    L += ["", "## Facts recorded (not pass / fail)", ""]
    dups = [c for c in chans if c.get("n_with_label", 0) > 1]
    if dups:
        mx = max(c.get("duplicates_max_abs_diff_uv", 0) for c in dups)
        L.append(f"- Labels present more than once in the EDF (the app uses the first): "
                 f"{sorted({c['channel'] for c in dups})} in {len({(c['subject'], c['file']) for c in dups})} files; "
                 f"largest difference between the copies {mx:.3f} µV.")
    L.append(f"- Dropped tail (shorter than one 4-s window): up to {max((r['dropped_tail_s'] for r in rows), default=0):.0f} s per file.")
    nosum = [r["file"] for r in rows if r.get("summary_start") == "not in summary"]
    if nosum:
        L.append(f"- Files whose summary gives no start time: {len(nosum)} (V4 uses the EDF header for them).")
    rev = sum(r["events_reviewed"] for r in rows); hum = sum(r["events_human"] for r in rows)
    L.append(f"- Events in the database: {sum(r['events_ai'] for r in rows)} AI ({rev} already reviewed), {hum} human.")
    L.append(f"- Frequency response of band-pass x notch, zero-phase (dB): {static['freq_response_db']}.")
    L.append(f"- The amplitude control sets µV per half channel row (`EegPanel.jsx`: pxPerUv = (rowHeight/2 − 3) / "
             f"amplitude), not µV/mm as on clinical viewers (information).")
    if v7 is not None:
        L += ["", "## V7 — upload paths (temporary database and upload folder)", "",
              "| case | what | expected (written before the run) | observed | as expected |", "|---|---|---|---|---|"]
        for r in v7:
            L.append(f"| {r['case']} | {r['what']} | {r['expected']} | {r['observed']} | {r['as_expected']} |")
    bad = [r for r in rows if not all(r.get(k) is True for k in ("V1", "V2", "V3", "V4_core", "V5_data"))
           or r["V6"] is False]
    if bad:
        L += ["", "## Files with a failing check", "", "| subject | file | V1 | V2 | V3 | V4 | V5 | V6 |",
              "|---|---|---|---|---|---|---|---|"]
        for r in bad[:200]:
            L.append(f"| {r['subject']} | {r['file']} | {r['V1']} | {r['V2']} | {r['V3']} | {r['V4_core']} | "
                     f"{r['V5_data']} | {r['V6']} |")
    if ui is not None and not ui[0]:
        L += ["", "UI formatter differences (first 10): " + json.dumps(ui[2])]
    L += ["", "Per-file values: `per_file.csv`; per channel: `channels.csv`; gates: `gates.json`."]
    (out / "VERIFY.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return gates


def git_state():
    try:
        c = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=str(ROOT)).stdout.strip()
        d = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no", "--", "web_demo", "src"],
                           capture_output=True, text=True, cwd=str(ROOT)).stdout.strip()
        return c or "unknown", "YES" if d else "no"
    except OSError:
        return "unknown", "unknown"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", required=True, help="folder with chbNN/ subfolders of the CHB-MIT EDF files")
    ap.add_argument("--db", default=str(BACKEND / "szscan.db"))
    ap.add_argument("--uploads", default=str(BACKEND / "uploads"))
    ap.add_argument("--sums", default=str(DEFAULT_SUMS))
    ap.add_argument("--tier2", default=str(DEFAULT_TIER2))
    ap.add_argument("--summary-dir", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--smoke", action="store_true", help="first file of the first subject; measures speed")
    ap.add_argument("--skip-v7", action="store_true")
    a = ap.parse_args(argv)
    t0 = time.time()
    ds, up = Path(a.dataset), Path(a.uploads)
    for p in (ds, up, Path(a.db), Path(a.sums)):
        if not p.exists():
            raise SystemExit(f"STOP: not found: {p}")
    subs, files, events = db_read(a.db)
    if any(not re.fullmatch(r"chb\d\d", s) for s in subs):
        raise SystemExit("STOP: the database holds a subject id that is not chbNN; this check is for CHB-MIT only "
                         "(no hospital record may enter a committed report).")
    if not files:
        raise SystemExit("STOP: the database holds no file")
    sums, ev_ref = load_sums(a.sums), load_ref_events(a.tier2)
    out = Path(a.out) if a.out else (DEFAULT_OUT / "smoke" if a.smoke else DEFAULT_OUT)
    out.mkdir(parents=True, exist_ok=True)
    ws, _ = import_backend()
    static = static_checks()
    if a.smoke:
        files = files[:1]
    rows, chans, cases, timings = [], [], [], []
    summ_cache = {}
    for i, f in enumerate(files):
        sid = f["subject_id"]
        if sid not in summ_cache:
            summ_cache[sid] = read_summary_times(find_summary(ds, sid, a.summary_dir))
        r, c, case = check_file(f, ds, up, sums, summ_cache[sid], events, ev_ref, ws, timings)
        rows.append(r); chans += c; cases.append(case)
        print(f"[{i + 1}/{len(files)}] {sid} {f['filename']}: V1 {r['V1']} V2 {r['V2']} V3 {r['V3']} "
              f"V4 {r['V4_core']} V5 {r['V5_data']} V6 {r['V6']} ({timings[-1]['v1_v2_v5_s'] + timings[-1]['v3_s']:.1f} s)",
              flush=True)
    with tempfile.TemporaryDirectory() as td:
        ui = ui_time_check(cases, td)
    v7 = None if (a.skip_v7 or a.smoke) else run_v7(ds, out)
    hours = sum(t["hours"] for t in timings)
    commit, dirty = git_state()
    meta = dict(commit=commit, dirty=dirty, seconds=time.time() - t0, hours=hours,
                subjects=sorted({f["subject_id"] for f in files}), python=sys.version.split()[0],
                numpy=np.__version__, smoke=a.smoke)
    try:
        import psutil
        meta["peak_rss_mb"] = round(psutil.Process().memory_info().rss / 1e6, 1)
    except ImportError:
        pass
    if a.smoke:
        per_h = sum(t["v1_v2_v5_s"] + t["v3_s"] for t in timings) / max(hours, 1e-9)
        _, all_files, _ = db_read(a.db)
        tot_h = sum(f["duration_seconds"] for f in all_files) / 3600
        meta["smoke_seconds_per_hour_of_eeg"] = round(per_h, 2)
        meta["full_run_projection_h_computed"] = round(per_h * tot_h / 3600, 2)
        meta["full_run_hours_of_eeg"] = round(tot_h, 2)
        print(f"SMOKE: {per_h:.1f} s per hour of EEG; {tot_h:.1f} h in the database -> full V1-V6 run "
              f"≈ {per_h * tot_h / 3600:.2f} h (computed, plus V7 ≈ the Phase B of two 1-h files)")
    gates = write_report(out, rows, chans, static, ui, v7, meta, a.smoke)
    print(json.dumps({k: v.get("PASS") for k, v in gates.items() if isinstance(v, dict) and "PASS" in v}))
    print(f"report: {out / 'VERIFY.md'}")
    return gates


if __name__ == "__main__":
    main()
