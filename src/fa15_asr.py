#!/usr/bin/env python
"""
fa15_asr.py -- F-A1.5 (a PROJECT VERIFICATION outside the report, board R204): does ASR in the preprocessing change the
detection of the thesis system once the GAE is retrained on the cleaned signals? Design approved by the author 15/11
12:14 (docs/FUTURE_RESEARCH_PLAN.md §12 15/11 12:40). This module = the DATA part (ASR + statistics + features) and the
smoke; training and scoring reuse src/r2_r1.py unchanged (src/fa15_run.py, written after the smoke).

ASR exactly as src/v9_x6_asr.py (imported, its functions called unchanged): asrpy 0.0.8 with V9-X6's numpy-2 patch,
cutoff 20, ASR.fit on the whole pipeline-filtered file (asrpy's own clean-window calibration, no label), transform with
mem_splits scaled by duration; ONE PROCESS PER FILE (asrpy's per-process memory growth, V9-X6 header). The input of ASR
is the pipeline's whole-file band-pass + notch (continuous_eval.filter_file / x1_external.filter_windows convention).

Insertion (record files unchanged, as r2_rb wraps open_edf): install(mode) patches every loaded copy of
  preprocessing.filter_window (statistics + count pass), continuous_eval.filter_file (features, 5-SD flag),
  x1_external.load_18 (registers which file a loaded array is), x1_external.filter_windows, x1_external.window_padded.
  mode "off"   -> the record functions, untouched (gate G-ident: features = the R0 datasets bit for bit)
  mode "slice" -> no ASR; the padded per-window calls return slices of the whole-file filtered signal (gate G-conv:
                  measures what the change of convention alone does to the statistics; ASR needs whole files, so the
                  ASR arm cannot use the record's 3-s padded windows)
  mode "asr"   -> slices / windows of the ASR-cleaned whole-file signal, read from a per-file cache (float32 .npy on
                  scratch disk, written by the ASR subprocess; computed once per file, deleted after its case)
Everything downstream is the record code: r2_core.stats_record / features_record (CHB-MIT thesis convention, the c1b
build: z-score statistics from every 10th non-ictal non-buffer window, 5-SD flag on the cleaned signal, features) and
r2_core.ext_job (chb24 + Siena, x1 convention, label-free statistics).

Gates (STOP unless noted): G-mod (closed modules from the pinned repository), mode (versions vs R0's run_meta: exact /
tolerance), R0.1 inventory (every raw file sha256 = PhysioNet, r2_core.inventory), G-ref (the R0 reference datasets
found, one copy each), G-conv per case (slice-mode statistics vs R0's: max |d mean| / SD and max relative d SD,
reported for every case; STOP only above 1e-2 -- author 21/11 01:28, option A: the convention of whole-file filtering is
accepted with its size reported), G-lab per case (labels, buffer, signal-loss flags, file index, file lists = the R0 dataset
exactly), G-asr (every file of V9-X6's universe in this part: the 92-seizure rows and the high-amplitude window shares =
results/v9_x6 within 1e-3 absolute; windows in only one set counted; a file beyond 1e-3 is recomputed with the earlier
asrpy chunkings that V9-X6's header documents -- 300-s chunks, asrpy's default mem_splits 3 for files <= 2 h -- and passes
only if one of them reproduces the record within 1e-9: asrpy's asr_process restarts its update grid in every chunk, so
its output depends on mem_splits; diagnosed 21/11, chat D35-F), G-ident (smoke: mode off -> the R0 .npz
bit for bit in mode exact), G-done (every case of the part written), G-worker-sha (every ASR subprocess and feature
job ran this fa15_asr.py: the sha16 each reports = the main process's). Pre-gates, before any long work (a FAIL skips the
run, archives and STOPs): **G-conv-pad** (one CHB-MIT and one external case per notebook: the record's statistics with
30-s padding = whole-file slices within 1e-9 relative -> the G-conv difference is the 3-s padding only, the slices are
aligned) and **G-asr-pre** (named files, e.g. chb06_01, recomputed with the chunking the V9-X6 record used = the record
within 1e-9). RP6 = V9-X6's Measure 1 on every file (same
functions; thresholds = R0's 5-SD thresholds, as V9-X6).

Outputs: WORK/fa15/<tag>/ (gates.json, cases.csv, files.csv, conv.csv, seizures.csv, highamp_windows.csv,
background_windows.csv, g_asr.json, run_meta.json, SUMMARY.md, logs/; smoke: projection.json, split.json) and the
datasets WORK/fa15-asr-chbmit-features-<tag>/ ({case}.npz, {case}_stats.json) and
WORK/fa15-asr-external-features-<tag>/ ({case}_lf.npz). Never committed: .npz, caches.
  python src/fa15_asr.py --clean SPEC.json             (one file, one process: what the prefetch shells out to)
  python src/fa15_asr.py --run --tag T --chb a,b --ext c,d [--asr-only file,...] [--conv-pad a,c]
                         [--asr-pre case:file:chunk_s,...] [--smoke]
Test (synthetic data, build container only): src/fa15_synthetic_test.py.
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import multiprocessing as mp
import os
import platform
import resource
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import filtfilt, iirnotch, sosfiltfilt

REPO = Path(os.environ.get("THESIS_REPO", Path(__file__).resolve().parents[1]))
for _p in ("src", "src/dataprep"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import r2_core as R0                     # noqa: E402  (stage R0, read only)
import preprocessing as P                # noqa: E402  (record, read only)
import continuous_eval as CE             # noqa: E402  (record, read only)
import x1_external as X1                 # noqa: E402  (record, read only)
import v9_x6_asr as V6                   # noqa: E402  (record, read only: run_asr + Measure 1 functions)

_OUTSIDE = [m.__name__ for m in (R0, P, CE, X1, V6) if (REPO / "src") not in Path(m.__file__).resolve().parents]
if _OUTSIDE:
    raise SystemExit(f"STOP G-mod: closed modules imported from outside {REPO / 'src'}: {_OUTSIDE}")

WORK = Path(os.environ.get("FA15_WORK", "/kaggle/working"))
INPUT = R0.INPUT
SCRATCH = Path(os.environ.get("FA15_SCRATCH", "/tmp/fa15"))
CACHE = SCRATCH / "asr_cache"
SPECS = SCRATCH / "specs"
TEST = bool(os.environ.get("FA15_TEST"))
CUTOFF = 20
WS = P.WIN_SAMPLES
N_CH = 18
TOL = dict(conv_rel=1e-2, asr_abs=1e-3, conv_pad=1e-9, asr_explain=1e-9)   # conv_rel: STOP bound (author 21/11, option A)
PAD_LONG_S = 30                                     # G-conv-pad: the record's padding raised from 3 s to 30 s
EXPLAIN_CHUNKS = (300.0, 1e12)                      # V9-X6's earlier chunkings: 300-s chunks; 1e12 -> asrpy's default 3
EXPLAIN_DEFAULT_MAX_H = 2.0                         # mem_splits 3 OOM'd on a 4-h file (V9-X6 header): short files only
SESSION_STOP_H = float(os.environ.get("FA15_SESSION_STOP_H", 11.0))
MIN_FREE_MEM_GB = float(os.environ.get("FA15_MIN_FREE_MEM_GB", 4.5))      # V9-X6's MIN_AVAILABLE_GB
DISK_MARGIN_GB = float(os.environ.get("FA15_DISK_MARGIN_GB", 4.0))
VERSION_KEYS = ("python", "numpy", "scipy", "pandas", "mne")
CODE_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:16]
V6_SHA = hashlib.sha256((REPO / "src" / "v9_x6_asr.py").read_bytes()).hexdigest()[:16]
T0 = float(os.environ.get("FA15_T0", time.time()))
STATE = dict(tag=None, gates=[], phases={})


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def hours():
    return (time.time() - T0) / 3600


def out_dir():
    d = WORK / "fa15" / STATE["tag"]
    d.mkdir(parents=True, exist_ok=True)
    return d


def ds_chb():
    return WORK / f"fa15-asr-chbmit-features-{STATE['tag']}"


def ds_ext():
    return WORK / f"fa15-asr-external-features-{STATE['tag']}"


def _np(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, Path):
        return str(o)
    raise TypeError(type(o))


def jdump(p, obj):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(obj, indent=1, default=_np))


def gate(rec, stop=True):
    STATE["gates"].append(rec)
    jdump(out_dir() / "gates.json", STATE["gates"])
    log(f"{rec['gate']}: {rec['status']} -- {rec.get('summary', '')}")
    if stop and rec["status"] not in ("PASS", "n/a", "NOT GATED"):
        raise SystemExit(f"STOP {rec['gate']}: {rec.get('summary', '')}")


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def machine_info():
    """CPU model, AVX-512 presence and numpy's BLAS: Kaggle assigns machine types whose arithmetic differs under the same
    library versions (chat D34-F, handback Part 28.3) -- recorded in every run_meta from 21/11 (chat D35-F)."""
    info = dict(cpu_model=None, avx512f=None, blas=None)
    try:
        txt = Path("/proc/cpuinfo").read_text()
        info["cpu_model"] = next((l.split(":", 1)[1].strip() for l in txt.splitlines() if l.startswith("model name")), None)
        flags = next((l for l in txt.splitlines() if l.startswith("flags")), "")
        info["avx512f"] = " avx512f" in flags
    except OSError:
        info["cpu_model"] = platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER")
    try:
        b = np.show_config(mode="dicts")["Build Dependencies"]["blas"]
        info["blas"] = f"{b.get('name')} {b.get('version')}"
    except Exception:                    # noqa: BLE001
        pass
    return info


def mem_available_gb():
    try:
        for line in open("/proc/meminfo"):
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) / 1e6
    except OSError:
        pass
    return float("inf")


# ============================================================================ signal path (identical to the record)
def notch_ba(notch):
    if float(notch) == 60.0:
        return P._NOTCH_B, P._NOTCH_A                      # = iirnotch(60, Q=30, fs=256), the pipeline's own
    return iirnotch(float(notch), Q=30, fs=P.FS)            # x1_external.filters (Siena 50 Hz)


def load_raw(path, kind):
    """unfiltered [18, n] float64 V, exactly as the record reads it (P.open_edf / x1_external.load_18); None if a channel
    or electrode is missing."""
    if kind == "chb":
        raw = P.open_edf(Path(path))
        if raw is None:
            return None
        return raw.get_data().astype(np.float64)
    return _ORIG.get("load_18", X1.load_18)(Path(path), kind)


def whole_filtered(data, notch):
    b, a = notch_ba(notch)
    return filtfilt(b, a, sosfiltfilt(P._BP_SOS, data, axis=1), axis=1)


def file_key(path, kind, notch):
    return hashlib.sha1(f"{os.path.realpath(path)}|{kind}|{float(notch)}".encode()).hexdigest()[:20]


# ============================================================================ the wrapper
_ORIG = {}
W = dict(mode="off", mem=None, reg={}, fallback=0)


def _fp(data):
    """fingerprint of a loaded array (the same file loaded twice gives the same value; computed from a strided sample)."""
    return (data.shape, hashlib.sha1(np.ascontiguousarray(data[:, ::997]).tobytes()).hexdigest())


def cleaned(path, kind, notch):
    """[18, n_total] signal of the current mode for one file (slice: whole-file filtered float64; asr: the cached
    ASR-cleaned float32, memory-mapped)."""
    k = file_key(path, kind, notch)
    if W["mem"] is not None and W["mem"][0] == (k, W["mode"]):
        return W["mem"][1]
    if W["mode"] == "slice":
        data = load_raw(path, kind)
        if data is None:
            raise RuntimeError(f"{path}: missing one of the 18 common channels")
        X = whole_filtered(data, notch)
    elif W["mode"] == "asr":
        f = CACHE / f"{k}.npy"
        if not f.exists():                                   # not prefetched: computed now (counted; should not happen)
            W["fallback"] += 1
            run_clean(dict(path=str(path), kind=kind, notch=float(notch), key=k, measure=None))
        X = np.load(f, mmap_mode="r")
    else:
        raise RuntimeError(f"cleaned() in mode {W['mode']}")
    W["mem"] = ((k, W["mode"]), X)
    return X


def _w_filter_file(path):
    if W["mode"] == "off":
        return _ORIG["filter_file"](path)
    if P.open_edf(Path(path)) is None:
        raise RuntimeError(f"{path}: missing one of the 18 common channels")
    X = cleaned(path, "chb", 60.0)
    n = X.shape[1] // WS
    if n == 0:
        raise RuntimeError(f"{path}: shorter than one 4 s window")
    return np.ascontiguousarray(np.asarray(X[:, :n * WS], dtype=np.float64)
                                .reshape(N_CH, n, WS).transpose(1, 0, 2)).astype(np.float32), n


SHIFT = int(os.environ.get("FA15_TEST_SLICE_SHIFT", 0)) if TEST else 0   # synthetic test only: a planted misalignment


def _w_filter_window(raw, start, end):
    if W["mode"] == "off":
        return _ORIG["filter_window"](raw, start, end)
    X = cleaned(raw.filenames[0], "chb", 60.0)
    return np.asarray(X[:, start + SHIFT:end + SHIFT], dtype=np.float64)


def _w_load_18(path, kind):
    data = _ORIG["load_18"](path, kind)
    if data is not None and W["mode"] != "off":
        W["reg"][_fp(data)] = (str(path), kind)
    return data


def _w_filter_windows(data, notch):
    if W["mode"] == "off":
        return _ORIG["filter_windows"](data, notch)
    path, kind = W["reg"][_fp(data)]
    X = cleaned(path, kind, notch)
    n = data.shape[1] // WS
    return np.ascontiguousarray(np.asarray(X[:, :n * WS], dtype=np.float64)
                                .reshape(N_CH, n, WS).transpose(1, 0, 2)).astype(np.float32), n


def _w_window_padded(data, i, notch):
    if W["mode"] == "off":
        return _ORIG["window_padded"](data, i, notch)
    path, kind = W["reg"][_fp(data)]
    X = cleaned(path, kind, notch)
    return np.asarray(X[:, i * WS + SHIFT:(i + 1) * WS + SHIFT], dtype=np.float64)


def install(mode):
    """patch every loaded copy of the record modules (idempotent); mode off = the record functions."""
    if mode not in ("off", "slice", "asr"):
        raise ValueError(mode)
    if not _ORIG:
        _ORIG.update(filter_window=P.filter_window, filter_file=CE.filter_file, load_18=X1.load_18,
                     filter_windows=X1.filter_windows, window_padded=X1.window_padded)
    for name, m in list(sys.modules.items()):
        if m is None:
            continue
        if name.split(".")[-1] == "preprocessing" and hasattr(m, "filter_window"):
            m.filter_window = _w_filter_window
        if name.split(".")[-1] == "continuous_eval" and hasattr(m, "filter_file"):
            m.filter_file = _w_filter_file
        if name.split(".")[-1] == "x1_external" and hasattr(m, "window_padded"):
            m.load_18, m.filter_windows, m.window_padded = _w_load_18, _w_filter_windows, _w_window_padded
    W.update(mode=mode, mem=None)


# ============================================================================ ASR (one process per file)
def run_clean(spec):
    """spec: path, kind, notch, key, measure (dict(subject, file, seizures, thr) or None). Writes CACHE/{key}.npy
    (float32) and CACHE/{key}.json (timing, Measure 1 payload). Raises on failure."""
    CACHE.mkdir(parents=True, exist_ok=True)
    SPECS.mkdir(parents=True, exist_ok=True)
    sp = SPECS / f"{spec['key']}.json"
    sp.write_text(json.dumps(spec, default=_np))
    r = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--clean", str(sp)], capture_output=True,
                       text=True, env=dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                                           MKL_NUM_THREADS="1"))
    if r.returncode != 0 or not (CACHE / f"{spec['key']}.npy").exists():
        raise RuntimeError(f"ASR subprocess failed for {spec['path']}: {r.stdout[-800:]} {r.stderr[-1500:]}")
    return json.loads((CACHE / f"{spec['key']}.json").read_text())


BC_TRIM = []


def guard_block_covariance():
    """asrpy 0.0.8 bug (diagnosed 15/11 in the synthetic test, confirmed on random data): asr_utils.block_covariance
    sizes its output by len(arange(0, n-1, w)) but fills it with len(arange(k, n+k-2, w)) rows; the two differ, and
    ASR.fit raises "cannot reshape", exactly when the calibration (clean-window) sample count n = 2 (mod blocksize = 100),
    i.e. ~1 % of files. Guard: only in that case the last calibration sample is dropped (n-1 = 1 mod 100: both lengths
    agree); every other file runs asrpy unchanged, bit for bit (so V9-X6's 70 files are unaffected). The files where it
    acted are listed (files.csv: bc_trim). Alternative (MATLAB clean_rawdata's ranges for every file): plan §14."""
    import asrpy.asr as AA
    orig = getattr(AA, "_fa15_orig_bc", AA.block_covariance)
    AA._fa15_orig_bc = orig

    def bc(data, window=128):
        n = data.shape[1]
        if (n - 2) % window == 0:
            BC_TRIM.append(int(n))
            data = data[:, :n - 1]
        return orig(data, window=window)
    AA.block_covariance = bc


def clean_cli(spec_path):
    """child: load, filter, ASR (V9-X6's run_asr), Measure 1 (V9-X6's functions), save."""
    spec = json.loads(Path(spec_path).read_text())
    if TEST and os.environ.get("FA15_TEST_FAIL_FILE") and Path(spec["path"]).name == os.environ["FA15_TEST_FAIL_FILE"]:
        raise SystemExit("synthetic test: planted ASR failure")
    t0 = time.time()
    data = load_raw(spec["path"], spec["kind"])
    if data is None:
        raise SystemExit(f"{spec['path']}: missing channel")
    n_total = data.shape[1]
    X = whole_filtered(data, spec["notch"])
    del data
    if spec.get("perturb"):                                  # T2 (chat D35-F): relative last-bit perturbation of the input
        X = X * (1.0 + float(spec["perturb"]))
    t1 = time.time()
    if spec.get("chunk_s"):                                  # diagnostic: an earlier V9-X6 chunking (G-asr-pre, G-asr)
        V6.MEM_SPLIT_CHUNK_S = float(spec["chunk_s"])
    mem_splits = max(3, int(np.ceil(n_total / (V6.MEM_SPLIT_CHUNK_S * P.FS))))       # = V6.run_asr's own formula
    if os.environ.get("FA15_TEST_ASR_IDENTITY"):             # synthetic test of the plumbing only
        Xc = X.copy()
    else:
        guard_block_covariance()
        Xc = V6.run_asr(X, CUTOFF)
    t2 = time.time()
    sha = os.environ.get("FA15_TEST_WORKER_SHA") if TEST and os.environ.get("FA15_TEST_WORKER_SHA") else CODE_SHA
    payload = dict(path=spec["path"], key=spec["key"], n_total=int(n_total), hours=n_total / P.FS / 3600,
                   load_filter_s=round(t1 - t0, 2), asr_s=round(t2 - t1, 2), bc_trim=len(BC_TRIM),
                   chunk_s=float(V6.MEM_SPLIT_CHUNK_S), mem_splits=mem_splits, code_sha=sha,
                   perturb=float(spec.get("perturb") or 0.0),
                   power_removed_total=float(1 - np.mean(Xc ** 2) / max(np.mean(X ** 2), 1e-300)))
    m = spec.get("measure")
    if m:
        payload["measure"] = measure1(X, Xc, n_total, [tuple(s) for s in m["seizures"]], np.asarray(m["thr"], float),
                                      m["subject"], m["file"])
    if spec.get("nocache"):                                  # diagnostic: an empty marker instead of the signal
        (CACHE / f"{spec['key']}.npy").write_bytes(b"")
    else:
        tmp = CACHE / f".{spec['key']}.npy.part.npy"
        np.save(tmp, Xc.astype(np.float32))
        tmp.replace(CACHE / f"{spec['key']}.npy")
    payload["peak_rss_mb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
    payload["total_s"] = round(time.time() - t0, 2)
    (CACHE / f"{spec['key']}.json").write_text(json.dumps(payload, default=_np))


def measure1(X_raw, X_clean, n_total, seizures, thr, subj, fname):
    """V9-X6's process_one, minus its file reading and part writing (the same functions, the same order)."""
    n_windows = n_total // WS
    share_w, Wr = V6.window_shares(X_raw, X_clean, n_windows)
    highamp, background = V6.window_flags(Wr, thr, n_windows, seizures, n_total)
    sz = []
    FS, PRE = P.FS, V6.PREICTAL_S
    for i, (on, off) in enumerate(seizures):
        c_sz_raw = V6.median_channel_rms(X_raw, on * FS, off * FS)
        c_pre_raw = V6.median_channel_rms(X_raw, (on - PRE) * FS, on * FS)
        c_sz_cl = V6.median_channel_rms(X_clean, on * FS, off * FS)
        c_pre_cl = V6.median_channel_rms(X_clean, (on - PRE) * FS, on * FS)
        sz.append(dict(subject=subj, file=fname, cutoff=CUTOFF, seizure_idx=i, onset_s=on, offset_s=off,
                       duration_s=off - on, share_seizure=V6.span_power_ratio(X_raw, X_clean, on * FS, off * FS, n_total),
                       share_preictal60=V6.span_power_ratio(X_raw, X_clean, (on - PRE) * FS, on * FS, n_total),
                       contrast_before=(c_sz_raw / c_pre_raw) if c_pre_raw else float("nan"),
                       contrast_after=(c_sz_cl / c_pre_cl) if c_pre_cl else float("nan")))
    pw = int(PRE // P.WIN_S)
    with np.errstate(invalid="ignore", divide="ignore"):
        cb = V6.window_median_rms(X_raw, n_windows) / V6.preceding_median_rms(X_raw, n_windows, pw)
        ca = V6.window_median_rms(X_clean, n_windows) / V6.preceding_median_rms(X_clean, n_windows, pw)
    hi = np.flatnonzero(highamp)
    return dict(seizures=sz, highamp=dict(win_idx=hi.tolist(), share=share_w[hi].tolist(),
                                          contrast_before=cb[hi].tolist(), contrast_after=ca[hi].tolist()),
                background=dict(share=share_w[background].tolist()))


# ============================================================================ references (R0 datasets) and file plans
def _hits(name, token, exclude=("-rb",)):
    out = []
    for p in sorted(INPUT.rglob(name)):
        parts = "/".join(p.parts)
        if token in parts and not any(x in parts for x in exclude) and WORK not in p.parents and SCRATCH not in p.parents:
            out.append(p)
    return out


def r0_refs(chb, ext):
    """the R0 reference files: thesis-r2-chbmit-features/{case}.npz + _stats.json, thesis-r2-external-features/
    {case}_lf.npz; one copy each (sizes equal), sha256 = R1_SMOKE's pin (results/r2/r1_system/smoke/data_sha256.csv)."""
    refs, bad = {}, []
    pin = {}
    pp = REPO / "results" / "r2" / "r1_system" / "smoke" / "data_sha256.csv"
    if pp.exists():
        d = pd.read_csv(pp)
        pin = {Path(str(r.file)).name: r.sha256 for r in d.itertuples()} if "file" in d.columns else {}
    for c in chb:
        for nm in (f"{c}.npz", f"{c}_stats.json"):
            h = [p for p in _hits(nm, "thesis-r2-chbmit-features") if "stats_earlier" not in p.parts]
            if not h or len({x.stat().st_size for x in h}) != 1:
                bad.append(f"{nm}: {len(h)} copies")
                continue
            refs[nm] = h[0]
    for c in ext:
        nm = f"{c}_lf.npz"
        h = _hits(nm, "thesis-r2-external-features")
        if not h or len({x.stat().st_size for x in h}) != 1:
            bad.append(f"{nm}: {len(h)} copies")
            continue
        refs[nm] = h[0]
    shas = {k: sha256_file(v) for k, v in refs.items()}
    differ = [k for k, v in shas.items() if k in pin and pin[k] != v]
    gate(dict(gate="G-ref", status="PASS" if not bad and not differ else "FAIL", missing=bad, differ_from_pin=differ,
              pinned_checked=sum(k in pin for k in shas), files={k: dict(path=str(v), sha256=shas[k]) for k, v in refs.items()},
              summary=f"{len(refs)} R0 reference files; {sum(k in pin for k in shas)} checked against the pin; "
                      f"missing {bad}; differ {differ}"))
    return refs


def chb_files(case, complete):
    smap = P.parse_summary(R0.summary_path(complete, case))
    out = []
    for p in sorted((Path(complete) / "chbmit" / case).glob("*.edf")):
        if P.open_edf(p) is None:
            continue                                         # skipped by design (record rule)
        out.append(dict(path=str(p), kind="chb", notch=60.0, file=p.name, seizures=smap.get(p.name, [])))
    return out


def ext_files(case, complete):
    files, meta = X1.subject_files(str(complete), case)
    out = []
    for p, sz in files:
        if load_raw(p, meta["kind"]) is None:
            continue
        out.append(dict(path=str(p), kind=meta["kind"], notch=float(meta["notch"]), file=Path(p).name,
                        seizures=[tuple(s) for s in sz]))
    return out


def thresholds(case, kind_set, refs):
    """5-SD thresholds of the R0 data (V volts): CHB thesis cases = the stats json; chb24 / Siena = 5 x label-free SD."""
    if kind_set == "chb":
        st = json.loads(refs[f"{case}_stats.json"].read_text())
        return np.asarray(st["artifact_thresh_uV"], float) * 1e-6
    meta = json.loads(str(np.load(refs[f"{case}_lf.npz"], allow_pickle=True)["meta"]))
    return P.ARTIFACT_SD_MULTIPLIER * np.asarray(meta["labelfree_std_uV"], float) * 1e-6


# ============================================================================ per-case feature job (spawned process)
def _init(env):
    os.environ.update(env)
    R0._limit_threads()


def feature_job(spec):
    """G-conv (mode slice), then the ASR build (mode asr) with the record code; G-lab against the R0 dataset; the case's
    cache files removed. Returns a dict (status, gates, counts, timing)."""
    case, set_, complete, tag, refs = spec["case"], spec["set"], Path(spec["complete"]), spec["tag"], spec["refs"]
    STATE["tag"] = tag
    t0 = time.time()
    logs = out_dir() / "logs"
    res = dict(case=case, set=set_, status="done", code_sha=CODE_SHA)
    try:
        # --- G-conv: statistics with whole-file slices, no ASR, vs R0
        install("slice")
        t = time.time()
        if set_ == "chb":
            st = R0.stats_record(case, complete, logs / f"{case}_conv.log")
            ref = json.loads(Path(refs[f"{case}_stats.json"]).read_text())
            mu, sd = np.asarray(st["ch_mean_uV"]), np.asarray(st["ch_std_uV"])
            mu0, sd0 = np.asarray(ref["ch_mean_uV"]), np.asarray(ref["ch_std_uV"])
            counts = {k: [st[k], ref[k]] for k in ("n_interictal", "n_ictal", "n_rejected")}
        else:
            files, meta = X1.subject_files(str(complete), case)
            mu, sd = X1.labelfree_stats(files, meta["kind"], meta["notch"])
            mu, sd = mu * 1e6, sd * 1e6
            m0 = json.loads(str(np.load(refs[f"{case}_lf.npz"], allow_pickle=True)["meta"]))
            mu0, sd0 = np.asarray(m0["labelfree_mean_uV"]), np.asarray(m0["labelfree_std_uV"])
            counts = {}
        res["conv"] = dict(mean_over_sd=float(np.max(np.abs(mu - mu0) / sd0)),
                           sd_rel=float(np.max(np.abs(sd - sd0) / sd0)), counts=counts, seconds=round(time.time() - t, 1))
        res["conv"]["status"] = "PASS" if max(res["conv"]["mean_over_sd"], res["conv"]["sd_rel"]) <= TOL["conv_rel"] else "FAIL"
        # --- ASR build
        install("asr")
        t = time.time()
        if set_ == "chb":
            st = R0.stats_record(case, complete, logs / f"{case}_asr.log")
            npz = R0.features_record(case, complete, st, ds_chb(), logs / f"{case}_asr.log")
            sdir = ds_chb() / f"_stats_{case}"
            jdump(ds_chb() / f"{case}_stats.json", st)
            shutil.rmtree(sdir, ignore_errors=True)
            new, ref = np.load(npz, allow_pickle=True), np.load(refs[f"{case}.npz"], allow_pickle=True)
            keys = ("is_ictal", "is_buffer", "is_signal_loss", "file_idx", "files")
            res["stats"] = {k: st[k] for k in ("n_interictal", "n_ictal", "n_rejected")}
            res["flag5sd"] = [int(np.asarray(new["is_flag5sd"]).sum()), int(np.asarray(ref["is_flag5sd"]).sum())]
            clean = lambda z: int((~np.asarray(z["is_ictal"], bool) & ~np.asarray(z["is_buffer"], bool)  # noqa: E731
                                   & ~np.asarray(z["is_flag5sd"], bool) & ~np.asarray(z["is_signal_loss"], bool)).sum())
            res["clean"] = [clean(new), clean(ref)]
        else:
            z, meta = R0.ext_job(case, complete, 1, logs / f"{case}_asr.log")
            if z is None:
                raise SystemExit(f"{case}: no scorable file")
            dst = ds_ext() / f"{case}_lf.npz"
            dst.parent.mkdir(parents=True, exist_ok=True)
            tmp = ds_ext() / f".{case}_lf.npz.part.npz"
            np.savez(tmp, **z, meta=json.dumps(meta, default=_np))
            tmp.replace(dst)
            new, ref = np.load(dst, allow_pickle=True), np.load(refs[f"{case}_lf.npz"], allow_pickle=True)
            keys = ("is_ictal", "is_signal_loss", "file_idx", "files")
        lab = {k: bool(np.array_equal(np.asarray(new[k]), np.asarray(ref[k]))) for k in keys}
        res["lab"] = dict(status="PASS" if all(lab.values()) else "FAIL", equal=lab)
        res["build_s"] = round(time.time() - t, 1)
        res["fallback_asr"] = W["fallback"]
    except SystemExit as e:
        res.update(status="STOP", error=str(e))
    except Exception:                    # noqa: BLE001
        res.update(status="FAILED", error=traceback.format_exc()[-3000:])
    finally:
        install("off")
        for k in spec.get("keys", []):
            if not os.environ.get("FA15_KEEP_CACHE"):
                for suf in (".npy",):
                    (CACHE / f"{k}{suf}").unlink(missing_ok=True)
    res["seconds"] = round(time.time() - t0, 1)
    res["peak_rss_mb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
    jdump(out_dir() / "cases" / f"{case}.json", res)
    return res


# ============================================================================ G-ident (smoke)
def ident_job(spec):
    """mode off: the record build of one case = the R0 .npz, every array bit for bit."""
    case, set_, complete, tag, refs = spec["case"], spec["set"], Path(spec["complete"]), spec["tag"], spec["refs"]
    STATE["tag"] = tag
    install("off")
    tmp = SCRATCH / "ident" / case
    shutil.rmtree(tmp, ignore_errors=True)
    t = time.time()
    try:
        if set_ == "chb":
            st = R0.stats_record(case, complete, out_dir() / "logs" / f"{case}_ident.log")
            p = R0.features_record(case, complete, st, tmp, out_dir() / "logs" / f"{case}_ident.log")
            new, ref = np.load(p, allow_pickle=True), np.load(refs[f"{case}.npz"], allow_pickle=True)
        else:
            z, meta = R0.ext_job(case, complete, 1, out_dir() / "logs" / f"{case}_ident.log")
            new, ref = z, np.load(refs[f"{case}_lf.npz"], allow_pickle=True)
        names = sorted(set(ref.files if hasattr(ref, "files") else ref) - {"meta", "skipped_files"})
        eq = {}
        for k in names:
            a, b = np.asarray(new[k]), np.asarray(ref[k])
            eq[k] = bool(a.shape == b.shape and (np.array_equal(a, b, equal_nan=True) if a.dtype.kind == "f"
                                                 else np.array_equal(a, b)))
        return dict(case=case, set=set_, status="PASS" if all(eq.values()) else "FAIL", equal=eq,
                    seconds=round(time.time() - t, 1))
    except Exception:                    # noqa: BLE001
        return dict(case=case, set=set_, status="FAILED", error=traceback.format_exc()[-2000:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ============================================================================ G-asr
def v9_record():
    d = REPO / "results" / "v9_x6"
    sz = pd.read_csv(d / "seizures.csv")
    hi = pd.read_csv(d / "highamp_windows.csv")
    bg = pd.read_csv(d / "background_windows.csv")
    return sz[sz.cutoff == CUTOFF], hi[hi.cutoff == CUTOFF], bg[bg.cutoff == CUTOFF]


def _measure_frames(m, s0, f0):
    """one file's Measure 1 payload -> (seizure rows, high-amplitude rows, background rows) in V9-X6's format."""
    h = m["highamp"]
    hi = [dict(subject=s0, file=f0, cutoff=CUTOFF, win_idx=w, share=a, contrast_before=b, contrast_after=c)
          for w, a, b, c in zip(h["win_idx"], h["share"], h["contrast_before"], h["contrast_after"])]
    bg = [dict(subject=s0, file=f0, cutoff=CUTOFF, share=a) for a in m["background"]["share"]]
    hc = ["subject", "file", "cutoff", "win_idx", "share", "contrast_before", "contrast_after"]
    return pd.DataFrame(m["seizures"]), pd.DataFrame(hi, columns=hc), pd.DataFrame(bg, columns=hc[:3] + ["share"])


def compare_file(sz, hi, bg, s, f, rec):
    """max |difference| per quantity between this run's Measure 1 rows of one file and the V9-X6 record's."""
    rsz, rhi, rbg = rec
    worst, only = {}, 0
    a = sz[(sz.subject == s) & (sz.file == f)].set_index("seizure_idx") if len(sz) else pd.DataFrame()
    b = rsz[(rsz.subject == s) & (rsz.file == f)].set_index("seizure_idx")
    for col in ("share_seizure", "share_preictal60", "contrast_before", "contrast_after"):
        dd = np.nanmax(np.abs(a[col].to_numpy(float) - b[col].reindex(a.index).to_numpy(float))) if len(a) else np.inf
        worst[col] = float(dd) if np.isfinite(dd) else np.inf
    ha = hi[(hi.subject == s) & (hi.file == f)].set_index("win_idx") if len(hi) else pd.DataFrame(columns=["share"])
    hb = rhi[(rhi.subject == s) & (rhi.file == f)].set_index("win_idx")
    com = ha.index.intersection(hb.index)
    only = len(ha.index.symmetric_difference(hb.index))
    worst["highamp_share"] = float(np.nanmax(np.abs(ha.share[com].to_numpy(float) - hb.share[com].to_numpy(float)))) \
        if len(com) else 0.0
    ga = np.sort(bg[(bg.subject == s) & (bg.file == f)].share.to_numpy(float)) if len(bg) else np.zeros(0)
    gb = np.sort(rbg[(rbg.subject == s) & (rbg.file == f)].share.to_numpy(float))
    worst["background_share_sorted"] = float(np.nanmax(np.abs(ga - gb))) if len(ga) == len(gb) and len(ga) else \
        (0.0 if len(ga) == len(gb) else np.inf)
    rows_ok = len(a) == len(b)
    return worst, only, rows_ok, len(a), len(ha), len(hb), len(ga), len(gb)


def recompute(specs, chunk_s, K, perturb=0.0):
    """ASR + Measure 1 of the given files with a given chunking (and optionally a relative input perturbation), in
    subprocesses (no cache kept); {(subject, file): frames}. Keys are suffixed so that the main caches are never
    touched."""
    out = {}

    def one(sp):
        sp = dict(sp, key=f"{sp['key']}_c{int(min(chunk_s, 1e6))}{'_p' if perturb else ''}", chunk_s=chunk_s,
                  nocache=True, perturb=perturb)
        while mem_available_gb() < MIN_FREE_MEM_GB:
            time.sleep(5)
        r = run_clean(sp)
        (CACHE / f"{sp['key']}.npy").unlink(missing_ok=True)
        m = sp["measure"]
        return (m["subject"], m["file"]), _measure_frames(r["measure"], m["subject"], m["file"]), r
    with cf.ThreadPoolExecutor(max(1, K)) as ex:
        for key, frames, r in ex.map(one, specs):
            out[key] = dict(frames=frames, mem_splits=r["mem_splits"], code_sha=r["code_sha"], asr_s=r["asr_s"],
                            perturb=r.get("perturb", 0.0), power_removed_total=r["power_removed_total"],
                            hours=r["hours"])
    return out


def gate_asr(sz, hi, bg, specs_by_file=None, K=1):
    """every file of V9-X6's universe processed here: seizure rows and high-amplitude window shares = the record within
    1e-3 absolute; background shares compared as sorted lists per file. A file beyond 1e-3 is recomputed with V9-X6's
    earlier chunkings (EXPLAIN_CHUNKS; the default 3 only for files <= EXPLAIN_DEFAULT_MAX_H) and is explained when one
    reproduces the record within 1e-9 (author 21/11 01:28). n/a if this part holds none of those files."""
    rec = v9_record()
    rsz = rec[0]
    files = sorted(set(zip(rsz.subject, rsz.file)) & set(zip(sz.subject, sz.file))) if len(sz) else []
    if not files:
        r = dict(gate="G-asr", status="n/a", summary="no file of V9-X6's universe in this part")
        jdump(out_dir() / "g_asr.json", r)
        return r
    worst_all, n_rows, only_all, detail, beyond = {}, 0, 0, [], []
    for s, f in files:
        worst, only, rows_ok, na, nha, nhb, nga, ngb = compare_file(sz, hi, bg, s, f, rec)
        for k, v in worst.items():
            worst_all[k] = max(worst_all.get(k, 0.0), v)
        n_rows += na
        only_all += only
        mx = max(worst.values())
        cls = "exact" if mx <= TOL["asr_explain"] and rows_ok else ("within_tol" if mx <= TOL["asr_abs"] and rows_ok
                                                                     else "beyond")
        detail.append(dict(subject=s, file=f, seizures=na, highamp_here=nha, highamp_record=nhb, background_here=nga,
                           background_record=ngb, max_abs=mx, cls=cls, explained_by=None))
        if cls == "beyond":
            beyond.append((s, f))
    sha_bad = []
    for chunk in EXPLAIN_CHUNKS:
        todo = []
        for s, f in beyond:
            d = next(x for x in detail if (x["subject"], x["file"]) == (s, f))
            sp = (specs_by_file or {}).get((s, f))
            if d["explained_by"] is None and sp is not None and (chunk < 1e6 or sp["hours"] <= EXPLAIN_DEFAULT_MAX_H):
                todo.append(sp)
        if not todo:
            continue
        res = recompute(todo, chunk, K)
        for (s, f), r in res.items():
            d = next(x for x in detail if (x["subject"], x["file"]) == (s, f))
            w, only, rows_ok, *_ = compare_file(*r["frames"], s, f, rec)
            d.setdefault("tried", []).append(dict(chunk_s=chunk, mem_splits=r["mem_splits"], max_abs=max(w.values()),
                                                  asr_s=r["asr_s"]))
            if r["code_sha"] != CODE_SHA:
                sha_bad.append((s, f, r["code_sha"]))
            if max(w.values()) <= TOL["asr_explain"] and rows_ok and only == 0:
                d["explained_by"] = dict(chunk_s=chunk, mem_splits=r["mem_splits"])
                d["cls"] = "explained"
    unexplained = [(d["subject"], d["file"]) for d in detail if d["cls"] == "beyond"]
    counts = {c: sum(d["cls"] == c for d in detail) for c in ("exact", "within_tol", "explained", "beyond")}
    ok = not unexplained and not sha_bad and n_rows == len(rsz.merge(pd.DataFrame(files, columns=["subject", "file"])))
    r = dict(gate="G-asr", status="PASS" if ok else "FAIL", files=len(files), seizure_rows=n_rows, max_abs=worst_all,
             highamp_windows_in_one_set_only=only_all, tol=TOL["asr_abs"], tol_explain=TOL["asr_explain"],
             classes=counts, unexplained=unexplained, worker_sha_bad=sha_bad, detail=detail,
             summary=f"{len(files)} V9-X6 files, {n_rows} seizures; classes {counts}; unexplained {unexplained}; "
                     f"max |diff| at 60-s chunks {max(worst_all.values()):.2e}")
    jdump(out_dir() / "g_asr.json", r)
    return r


def gate_asr_pre(items, plans_all, K):
    """G-asr-pre: each named file recomputed with the chunking the V9-X6 record used = the record within 1e-9."""
    rec = v9_record()
    det, ok = [], True
    by_chunk = {}
    for case, fname, chunk in items:
        sp = next((s for s in plans_all if s["case"] == case and Path(s["path"]).name == fname), None)
        if sp is None:
            det.append(dict(case=case, file=fname, status="FAIL", error="file not in this part's plan"))
            ok = False
            continue
        by_chunk.setdefault(chunk, []).append(sp)
    for chunk, sps in by_chunk.items():
        for (s, f), r in recompute(sps, chunk, K).items():
            w, only, rows_ok, *_ = compare_file(*r["frames"], s, f, rec)
            good = max(w.values()) <= TOL["asr_explain"] and rows_ok and only == 0 and r["code_sha"] == CODE_SHA
            ok &= good
            det.append(dict(case=s, file=f, chunk_s=chunk, mem_splits=r["mem_splits"], max_abs=w, highamp_only=only,
                            code_sha=r["code_sha"], asr_s=r["asr_s"], status="PASS" if good else "FAIL"))
    return dict(gate="G-asr-pre", status="PASS" if ok and det else "FAIL", tol=TOL["asr_explain"], files=det,
                summary=f"{len(det)} file(s) with the record's chunking vs results/v9_x6: "
                        f"{[(d['file'], d.get('mem_splits'), d['status']) for d in det]}")


def _stats_pair(case, set_, complete):
    """(mean, sd) of the record's statistics function for one case in the current wrapper mode (V; CHB thesis = every
    10th non-ictal non-buffer window, external = every 10th window)."""
    if set_ == "chb":
        smap = P.parse_summary(R0.summary_path(complete, case))
        return P.compute_subject_stats(case, Path(complete) / "chbmit", smap)
    files, meta = X1.subject_files(str(complete), case)
    return X1.labelfree_stats(files, meta["kind"], meta["notch"])


def gate_conv_pad(cases, complete):
    """G-conv-pad: the record's statistics with the padding raised to 30 s (mode off) = whole-file slices (mode slice)
    within 1e-9 relative, per case; also the 3-s record value (= G-conv) for scale."""
    det, ok = [], True
    pad0 = P.FILTER_PAD
    for case, set_ in cases:
        t = time.time()
        try:
            install("off")
            P.FILTER_PAD = PAD_LONG_S * P.FS
            mu30, sd30 = _stats_pair(case, set_, complete)
            P.FILTER_PAD = pad0
            mu3, sd3 = _stats_pair(case, set_, complete)
            install("slice")
            mus, sds = _stats_pair(case, set_, complete)
        finally:
            P.FILTER_PAD = pad0
            install("off")
        d30 = max(float(np.max(np.abs(mus - mu30) / sd30)), float(np.max(np.abs(sds - sd30) / sd30)))
        d3 = max(float(np.max(np.abs(mus - mu3) / sd3)), float(np.max(np.abs(sds - sd3) / sd3)))
        good = d30 <= TOL["conv_pad"]
        ok &= good
        det.append(dict(case=case, set=set_, rel_pad30_vs_slice=d30, rel_pad3_vs_slice=d3, seconds=round(time.time() - t, 1),
                        status="PASS" if good else "FAIL"))
    return dict(gate="G-conv-pad", status="PASS" if ok and det else "FAIL", tol=TOL["conv_pad"], cases=det,
                summary="; ".join(f"{d['case']}: 30 s {d['rel_pad30_vs_slice']:.1e}, 3 s {d['rel_pad3_vs_slice']:.1e}"
                                  for d in det))


# ============================================================================ orchestration
def versions():
    import scipy
    v = dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__, pandas=pd.__version__)
    try:
        import mne
        v["mne"] = mne.__version__
    except Exception as e:               # noqa: BLE001
        v["mne"] = f"n/a {e}"
    try:
        import importlib.metadata as im
        v["asrpy"] = im.version("asrpy")
    except Exception as e:               # noqa: BLE001
        v["asrpy"] = f"n/a {e}"
    return v


def gate_mode(v):
    ref = {}
    for sub in ("chb", "ext"):
        p = REPO / "results" / "r2" / "r0_data" / sub / "run_meta.json"
        if p.exists():
            ref[sub] = json.loads(p.read_text()).get("versions", {})
    diff = {s: {k: [v.get(k), r.get(k)] for k in VERSION_KEYS if r.get(k) is not None and v.get(k) != r.get(k)}
            for s, r in ref.items()}
    mode = "exact" if not any(diff.values()) else "tolerance"
    asr_ok = v.get("asrpy") == "0.0.8" or TEST
    gate(dict(gate="mode", status="PASS" if asr_ok else "FAIL", mode=mode, versions=v, differing=diff,
              summary=f"{mode} (versions vs R0's run_meta); asrpy {v.get('asrpy')}"))
    return mode


def plan_case(case, set_, complete, refs):
    files = chb_files(case, complete) if set_ == "chb" else ext_files(case, complete)
    thr = thresholds(case, set_, refs)
    specs = []
    for f in files:
        k = file_key(f["path"], f["kind"], f["notch"])
        specs.append(dict(path=f["path"], kind=f["kind"], notch=f["notch"], key=k, case=case,
                          measure=dict(subject=case, file=f["file"], seizures=[list(s) for s in f["seizures"]],
                                       thr=thr.tolist())))
    hrs = []
    for s in specs:
        try:
            import mne
            r = mne.io.read_raw_edf(s["path"], preload=False, verbose=False)
            hrs.append(r.n_times / r.info["sfreq"] / 3600)
        except Exception:                # noqa: BLE001
            hrs.append(1.0)
    for s, h in zip(specs, hrs):
        s["hours"] = h
    return specs


def run(tag, chb, ext, asr_only=(), smoke=False, notebook="local", commit="local", asr_workers=None, feat_workers=1,
        conv_pad=(), asr_pre=()):
    STATE["tag"] = tag
    t_run = time.time()
    v = versions()
    meta = dict(notebook=notebook, tag=tag, repo_commit=commit, code_sha=CODE_SHA, v9_x6_sha=V6_SHA, versions=v,
                cpu_count=os.cpu_count(), platform=platform.platform(), machine=machine_info(), smoke=smoke,
                chb=list(chb), ext=list(ext),
                asr_only=list(asr_only), conv_pad=list(conv_pad), asr_pre=[list(x) for x in asr_pre], started=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()), test=TEST)
    jdump(out_dir() / "run_meta.json", meta)
    gate(dict(gate="G-mod", status="PASS", summary=f"closed modules from {REPO / 'src'}; fa15_asr {CODE_SHA}, "
                                                   f"v9_x6_asr {V6_SHA}"))
    mode = gate_mode(v)
    t = time.time()
    R0.run_meta(f"fa15_{tag}_inventory", notebook, commit)
    dbs = {}
    chb_inv = sorted(set(chb) | {c for c in list(ext) + [a.split(":")[0] for a in asr_only] if c.startswith("chb")})
    sie_inv = sorted({c for c in list(ext) + [a.split(":")[0] for a in asr_only] if c.startswith("PN")})
    if chb_inv:
        dbs["chbmit"] = chb_inv
    if sie_inv:
        dbs["siena"] = sie_inv
    try:
        inv, cases_df, complete, _ = R0.inventory(dbs)
    except SystemExit as e:
        gate(dict(gate="R0.1-inventory", status="FAIL", summary=str(e)))
    gate(dict(gate="R0.1-inventory", status="PASS", files=int(len(inv)),
              from_physionet=int(inv.source.str.startswith("physionet").sum()),
              summary=f"{len(inv)} files sha256 = PhysioNet ({int(inv.source.str.startswith('physionet').sum())} "
                      f"downloaded)"))
    inv.drop(columns=[c for c in ("path",) if c in inv.columns]).to_csv(out_dir() / "inventory.csv", index=False)
    STATE["phases"]["inventory"] = round(time.time() - t, 1)
    refs = r0_refs(list(chb), list(ext))
    refs_s = {k: str(p) for k, p in refs.items()}
    # plan: per case the files (largest case first), plus the ASR-only files (smoke: timing, G-asr)
    plans = [(c, "chb", plan_case(c, "chb", complete, refs)) for c in chb] + \
            [(c, "ext", plan_case(c, "ext", complete, refs)) for c in ext]
    plans.sort(key=lambda x: -sum(s["hours"] for s in x[2]))
    extra = []
    for a in asr_only:
        c, f = a.split(":")
        set_ = "chb" if c.startswith("chb") and c != "chb24" else "ext"
        if c in chb or c in ext:
            continue
        aux_refs = r0_refs([c] if set_ == "chb" else [], [c] if set_ == "ext" else [])
        refs_s.update({k: str(p) for k, p in aux_refs.items()})
        extra += [s for s in plan_case(c, set_, complete, aux_refs) if Path(s["path"]).name == f]
    ncpu = os.cpu_count() or 1
    K = asr_workers or max(1, ncpu - feat_workers)
    log(f"plan: {len(plans)} cases, {sum(len(p[2]) for p in plans)} files, "
        f"{sum(s['hours'] for p in plans for s in p[2]):.1f} h; ASR-only files {len(extra)}; ASR processes {K}, "
        f"feature processes {feat_workers}; free disk {shutil.disk_usage(SCRATCH.parent if SCRATCH.parent.exists() else '/').free / 1e9:.1f} GB")
    file_rows, case_rows = [], []
    SCRATCH.mkdir(parents=True, exist_ok=True)
    specs_by_file = {(s["measure"]["subject"], s["measure"]["file"]): s for p_ in plans for s in p_[2]}
    specs_by_file.update({(s["measure"]["subject"], s["measure"]["file"]): s for s in extra})
    # ---- pre-gates (author 21/11 01:28): before any long work; a FAIL skips the run, archives and STOPs
    pre_fail = False
    if conv_pad:
        t = time.time()
        g = gate_conv_pad([(c, "chb" if c in chb else "ext") for c in conv_pad], complete)
        gate(g, stop=False)
        pre_fail |= g["status"] != "PASS"
        STATE["phases"]["g_conv_pad"] = round(time.time() - t, 1)
    if asr_pre and not pre_fail:
        t = time.time()
        g = gate_asr_pre(asr_pre, [s for p_ in plans for s in p_[2]] + extra, K)
        gate(g, stop=False)
        pre_fail |= g["status"] != "PASS"
        STATE["phases"]["g_asr_pre"] = round(time.time() - t, 1)
    t = time.time()
    asr_ex = cf.ThreadPoolExecutor(K)
    feat_ex = cf.ProcessPoolExecutor(feat_workers, mp_context=mp.get_context("spawn"), initializer=_init,
                                     initargs=({k: os.environ[k] for k in os.environ if k.startswith(("FA15_", "R2_", "THESIS_", "OMP_", "OPENBLAS_", "MKL_"))},))
    pending = [] if pre_fail else list(plans)
    if pre_fail:
        extra = []
    asr_futs, feat_futs, case_files = {}, {}, {}

    def submit_asr(spec):
        while mem_available_gb() < MIN_FREE_MEM_GB:
            time.sleep(5)
        t1 = time.time()
        r = run_clean(spec)
        r["wall_s"] = round(time.time() - t1, 2)
        return r

    for s in extra:
        asr_futs[asr_ex.submit(submit_asr, s)] = ("__extra__", s)
    stop_reason = None
    try:
        while pending or asr_futs or feat_futs:
            # submit the next case when the disk allows (cache of the case + margin)
            while pending:
                c, set_, specs = pending[0]
                need = sum(s["hours"] for s in specs) * 3600 * P.FS * N_CH * 4 / 1e9
                free = shutil.disk_usage(SCRATCH).free / 1e9
                queued = sum(1 for v_ in asr_futs.values() if v_[0] != "__extra__")
                if hours() > SESSION_STOP_H:
                    stop_reason = f"session guard {SESSION_STOP_H} h"
                    pending.clear()
                    break
                if free - need < DISK_MARGIN_GB and (asr_futs or feat_futs):
                    break
                if queued >= 2 * K:
                    break
                pending.pop(0)
                case_files[c] = dict(set=set_, left=len(specs), keys=[s["key"] for s in specs])
                for s in sorted(specs, key=lambda s: -s["hours"]):
                    asr_futs[asr_ex.submit(submit_asr, s)] = (c, s)
                log(f"{c}: {len(specs)} files queued for ASR ({sum(s['hours'] for s in specs):.1f} h, cache {need:.1f} GB, "
                    f"free disk {free:.1f} GB)")
                if not specs:
                    feat_futs[feat_ex.submit(feature_job, dict(case=c, set=set_, complete=str(complete), tag=tag,
                                                                refs=refs_s, keys=[]))] = c
            if not asr_futs and not feat_futs:
                if pending:
                    continue
                break
            done, _ = cf.wait(list(asr_futs) + list(feat_futs), timeout=30, return_when=cf.FIRST_COMPLETED)
            for fu in done:
                if fu in asr_futs:
                    c, s = asr_futs.pop(fu)
                    r = fu.result()                  # raises -> STOP below
                    row = dict(case=s["case"], file=Path(s["path"]).name, hours=r["hours"], asr_s=r["asr_s"],
                               load_filter_s=r["load_filter_s"], wall_s=r["wall_s"], total_s=r["total_s"],
                               peak_rss_mb=r["peak_rss_mb"], power_removed_total=r["power_removed_total"],
                               bc_trim=r.get("bc_trim", 0), mem_splits=r.get("mem_splits"),
                               code_sha=r.get("code_sha"), asr_only=c == "__extra__")
                    file_rows.append(row)
                    jdump(out_dir() / "measure" / f"{s['case']}__{row['file']}.json", r.get("measure") or {})
                    if c == "__extra__":
                        if not os.environ.get("FA15_KEEP_CACHE"):
                            (CACHE / f"{s['key']}.npy").unlink(missing_ok=True)
                        continue
                    case_files[c]["left"] -= 1
                    if case_files[c]["left"] == 0:
                        feat_futs[feat_ex.submit(feature_job, dict(case=c, set=case_files[c]["set"], complete=str(complete),
                                                                    tag=tag, refs=refs_s, keys=case_files[c]["keys"]))] = c
                        log(f"{c}: ASR done, feature job submitted")
                else:
                    c = feat_futs.pop(fu)
                    r = fu.result()
                    case_rows.append(r)
                    log(f"{c}: {r['status']} ({r['seconds']} s; G-conv {r.get('conv', {}).get('status')}, "
                        f"G-lab {r.get('lab', {}).get('status')})")
                    if r["status"] != "done":
                        raise SystemExit(f"feature job {c}: {r['status']}: {r.get('error')}")
    except SystemExit as e:
        stop_reason = str(e)
    except Exception:                    # noqa: BLE001
        stop_reason = traceback.format_exc()[-2500:]
    finally:
        asr_ex.shutdown(wait=False, cancel_futures=True)
        feat_ex.shutdown(wait=True, cancel_futures=True)
    STATE["phases"]["asr_and_features"] = round(time.time() - t, 1)
    pd.DataFrame(file_rows).to_csv(out_dir() / "files.csv", index=False)
    flat = []
    for r in case_rows:
        flat.append(dict(case=r["case"], set=r["set"], status=r["status"], seconds=r["seconds"], build_s=r.get("build_s"),
                         conv_status=r.get("conv", {}).get("status"), conv_mean_over_sd=r.get("conv", {}).get("mean_over_sd"),
                         conv_sd_rel=r.get("conv", {}).get("sd_rel"), conv_s=r.get("conv", {}).get("seconds"),
                         lab_status=r.get("lab", {}).get("status"), flag5sd_asr=(r.get("flag5sd") or [None, None])[0],
                         flag5sd_r0=(r.get("flag5sd") or [None, None])[1], clean_asr=(r.get("clean") or [None, None])[0],
                         clean_r0=(r.get("clean") or [None, None])[1], fallback_asr=r.get("fallback_asr"),
                         peak_rss_mb=r.get("peak_rss_mb"), hours=sum(x["hours"] for x in file_rows if x["case"] == r["case"])))
    pd.DataFrame(flat).to_csv(out_dir() / "cases.csv", index=False)
    # Measure 1 tables (V9-X6 format)
    sz, hi, bg = [], [], []
    for p in sorted((out_dir() / "measure").glob("*.json")) if (out_dir() / "measure").exists() else []:
        m = json.loads(p.read_text())
        if not m:
            continue
        s0, f0 = p.stem.split("__")
        a_, b_, c_ = _measure_frames(m, s0, f0)
        sz.append(a_), hi.append(b_), bg.append(c_)
    cat = lambda L: pd.concat(L, ignore_index=True) if L else pd.DataFrame()  # noqa: E731
    sz, hi, bg = cat(sz), cat(hi), cat(bg)
    sz.to_csv(out_dir() / "seizures.csv", index=False)
    hi.to_csv(out_dir() / "highamp_windows.csv", index=False)
    bg.to_csv(out_dir() / "background_windows.csv", index=False)
    if pre_fail:
        gate(dict(gate="G-done", status="FAIL", summary="skipped: a pre-gate failed"), stop=False)
    elif stop_reason:
        gate(dict(gate="G-done", status="FAIL", summary=stop_reason[:1500]), stop=False)
    else:
        conv_bad = [r["case"] for r in case_rows if r.get("conv", {}).get("status") != "PASS"]
        lab_bad = [r["case"] for r in case_rows if r.get("lab", {}).get("status") != "PASS"]
        gate(dict(gate="G-conv", status="PASS" if not conv_bad else "FAIL", failed=conv_bad, tol=TOL["conv_rel"],
                  worst=max([max(r["conv"]["mean_over_sd"], r["conv"]["sd_rel"]) for r in case_rows] or [0.0]),
                  summary=f"{len(case_rows)} cases; worst relative difference "
                          f"{max([max(r['conv']['mean_over_sd'], r['conv']['sd_rel']) for r in case_rows] or [0.0]):.2e}; "
                          f"beyond {TOL['conv_rel']}: {conv_bad}"), stop=False)
        gate(dict(gate="G-lab", status="PASS" if not lab_bad else "FAIL", failed=lab_bad,
                  summary=f"labels / buffer / signal loss / file index / files = R0 in {len(case_rows) - len(lab_bad)} "
                          f"of {len(case_rows)} cases"), stop=False)
        t = time.time()
        gate(gate_asr(sz, hi, bg, specs_by_file, K), stop=False)
        STATE["phases"]["g_asr"] = round(time.time() - t, 1)
        done = {r["case"] for r in case_rows if r["status"] == "done"}
        want = set(chb) | set(ext)
        gate(dict(gate="G-done", status="PASS" if done == want else "FAIL", missing=sorted(want - done),
                  summary=f"{len(done)} of {len(want)} cases written"), stop=False)
        shas = {("asr", x["file"]): x.get("code_sha") for x in file_rows} | {("feat", r["case"]): r.get("code_sha")
                                                                              for r in case_rows}
        bad = sorted(f"{k[0]}:{k[1]}={v}" for k, v in shas.items() if v != CODE_SHA)
        gate(dict(gate="G-worker-sha", status="PASS" if shas and not bad else "FAIL", expected=CODE_SHA,
                  jobs=len(shas), differ=bad, summary=f"{len(shas) - len(bad)} of {len(shas)} jobs ran fa15_asr "
                                                        f"{CODE_SHA}; differ {bad[:5]}"), stop=False)
    if smoke and not stop_reason and not pre_fail:
        ident = []
        for c in [x for x in chb][:1] + [x for x in ext if x.startswith("PN")][:1]:
            ident.append(ident_job(dict(case=c, set="chb" if c in chb else "ext", complete=str(complete), tag=tag,
                                        refs=refs_s)))
        gate(dict(gate="G-ident", status=("PASS" if all(r["status"] == "PASS" for r in ident) else "FAIL")
                  if mode == "exact" else "NOT GATED", mode=mode, cases=ident,
                  summary=f"mode off -> R0 .npz bit for bit: {[(r['case'], r['status']) for r in ident]}"
                          + ("" if mode == "exact" else " (versions differ from R0: reported, not gated)")), stop=False)
        projection(file_rows, case_rows, K, feat_workers)
    meta.update(finished=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()), runtime_h=round(hours(), 3),
                phases_s=STATE["phases"], stop_reason=stop_reason,
                peak_rss_self_mb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
                disk_free_gb_end=round(shutil.disk_usage(SCRATCH).free / 1e9, 1))
    jdump(out_dir() / "run_meta.json", meta)
    write_summary()
    failed = [g["gate"] for g in STATE["gates"] if g["status"] not in ("PASS", "n/a", "NOT GATED")]
    return failed


def projection(file_rows, case_rows, K, F):
    """computed estimate (from this run's measured rates) of the data notebooks for every case of F-A1.5, and an LPT
    split into notebooks of <= 10.5 h each. ASR rate = measured ASR seconds per hour of EEG under K concurrent processes
    (upper quartile over files); feature rate = measured feature-job seconds per hour of EEG (max over cases)."""
    fr = pd.DataFrame(file_rows)
    asr_rate = float(np.quantile(fr.wall_s / fr.hours.clip(lower=1e-6), 0.75)) if len(fr) else np.nan
    feat_rate = max([r["seconds"] / max(sum(x["hours"] for x in file_rows if x["case"] == r["case"]), 1e-6)
                     for r in case_rows] or [np.nan])
    hrs = all_case_hours()
    jobs = sorted(hrs.items(), key=lambda x: -x[1])

    def wall(hs):
        if not hs:
            return 0.0
        tot = sum(hs)
        return max(tot * asr_rate / K, tot * feat_rate / F) / 3600 + max(hs) * (asr_rate / K + feat_rate) / 3600 + 0.4

    for n in range(1, min(12, len(jobs)) + 1):
        bins = [[] for _ in range(n)]
        for c, h in jobs:
            i = int(np.argmin([sum(hrs[x] for x in b) for b in bins]))
            bins[i].append(c)
        w = [wall([hrs[x] for x in b]) for b in bins]
        if max(w) <= 10.5:
            break
    split = {chr(ord("a") + i): dict(cases=b, hours=round(sum(hrs[x] for x in b), 1), computed_wall_h=round(w[i], 2),
                                     over_limit=bool(w[i] > 10.5))      # a case too long for one session: split by hand
             for i, b in enumerate(bins) if b}
    rec = dict(asr_s_per_h_per_process_q75=asr_rate, feature_s_per_h=feat_rate, asr_processes=K, feature_processes=F,
               peak_rss_mb_asr=float(fr.peak_rss_mb.max()) if len(fr) else None,
               disk_free_gb=round(shutil.disk_usage(SCRATCH).free / 1e9, 1), mem_total_gb=round(
                   os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1e9, 1),
               largest_case_cache_gb=round(max(hrs.values()) * 3600 * P.FS * N_CH * 4 / 1e9, 1),
               notebooks=len(split), note="computed estimate from the smoke's measured rates (instructions §5 item 6)")
    jdump(out_dir() / "projection.json", rec)
    jdump(out_dir() / "split.json", split)
    log(f"projection: {rec}; split {split}")


TRAIN = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08", "chb09", "chb12", "chb19", "chb20", "chb21", "chb23"]
VAL = ["chb10", "chb11", "chb22"]
TESTC = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
CHB23 = sorted(TRAIN + VAL + TESTC)                      # the thesis cases of r2_r1 (chb24 is external: x1 convention)


def ext_cases():
    return ["chb24"] + sorted(p.stem.replace("rows_", "") for p in (REPO / "results" / "x1_external").glob("rows_PN*.csv"))


def all_case_hours():
    """hours of every F-A1.5 case (23 thesis cases + chb24 + Siena 14) from R0's committed inventories."""
    if TEST and os.environ.get("FA15_TEST_HOURS"):
        return json.loads(os.environ["FA15_TEST_HOURS"])
    chb = pd.read_csv(REPO / "results" / "r2" / "r0_data" / "chb" / "inventory_cases.csv")
    ext = pd.read_csv(REPO / "results" / "r2" / "r0_data" / "ext" / "external_cases.csv")
    out = {c: float(chb[chb.case == c].hours_used_windows.iloc[0]) for c in CHB23}
    out.update({c: float(ext[ext.case == c].hours.iloc[0]) for c in ext_cases()})
    return out


def write_summary():
    L = [f"# F-A1.5 data run {STATE['tag']} (fa15_asr {CODE_SHA}; project verification, board R204)", "",
         "| gate | status | summary |", "|---|---|---|"]
    for g in STATE["gates"]:
        L.append(f"| {g['gate']} | {g['status']} | {str(g.get('summary', '')).replace('|', '/')[:400]} |")
    (out_dir() / "SUMMARY.md").write_text("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--tag", default="local")
    ap.add_argument("--chb", default="")
    ap.add_argument("--ext", default="")
    ap.add_argument("--asr-only", default="")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--conv-pad", default="")
    ap.add_argument("--asr-pre", default="")
    ap.add_argument("--asr-workers", type=int, default=None)
    ap.add_argument("--notebook", default="local")
    ap.add_argument("--commit", default="local")
    a = ap.parse_args()
    if a.clean:
        clean_cli(a.clean)
        return 0
    if a.run:
        sp = lambda s: [x for x in s.split(",") if x]  # noqa: E731
        pre = [(x.split(":")[0], x.split(":")[1], float(x.split(":")[2])) for x in sp(a.asr_pre)]
        failed = run(a.tag, sp(a.chb), sp(a.ext), sp(a.asr_only), a.smoke, a.notebook, a.commit, a.asr_workers,
                     conv_pad=sp(a.conv_pad), asr_pre=pre)
        print("FAILED GATES:", failed if failed else "none")
        return 1 if failed else 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
