#!/usr/bin/env python
"""
m2l_diag_v1.py -- diagnosis of M2L_L3_EVAL Version 1 (timeout at 12 h, 24-25/11/2026; chat F2-03). Re-runs the three
measurements behind results/m2l/l3eval_v1_timeout/DIAGNOSIS.md on synthetic data (no EEG, any machine):
  M1  peak memory of the record reader + filter (x1_external.load_18 + filter_windows, the first steps of
      m2l_core.rec_job) on synthetic EDF files: Siena layout at 512 Hz (34 signals, 1 h and 2 h) and CHB-MIT layout
      at 256 Hz (23 signals, 2 h and 4 h); each in a fresh interpreter, VmHWM
  M2  a worker's memory after its imports (m2l_core, torch)
  M3  multiprocessing.Pool (spawn, maxtasksperchild=1, as r2_r1._pool) with two workers killed by SIGKILL (as the OOM
      killer): the other jobs finish, then the parent waits without an error (CPython issue 22393)
  PYTHONUTF8=1 python src/m2l_diag_v1.py [--out DIR]     (needs mne, edfio; about 2 min, < 3 GB)
"""
import argparse
import multiprocessing as mp
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MAKE = r'''
import sys, numpy as np, mne
hours, out, layout = float(sys.argv[1]), sys.argv[2], sys.argv[3]
if layout == "siena":
    eeg = ["Fp1","F3","C3","P3","O1","F7","T3","T5","Fc1","Fc5","Cp1","Cp5","F9","Fz","Cz","Pz","Fp2","F4","C4","P4",
           "O2","F8","T4","T6","Fc2","Fc6","Cp2","Cp6","F10"]
    names, fs = [f"EEG {c}" for c in eeg] + ["EKG EKG", "SPO2", "HR", "1", "2"], 512
else:
    names = ["FP1-F7","F7-T7","T7-P7","P7-O1","FP1-F3","F3-C3","C3-P3","P3-O1","FP2-F4","F4-C4","C4-P4","P4-O2",
             "FP2-F8","F8-T8","T8-P8-0","P8-O2","FZ-CZ","CZ-PZ","P7-T7","T7-FT9","FT9-FT10","FT10-T8","T8-P8-1"]
    fs = 256
n = int(hours * 3600 * fs)
d = (np.random.default_rng(0).standard_normal((len(names), n), dtype=np.float32) * 40e-6).astype(np.float64)
raw = mne.io.RawArray(d, mne.create_info(names, fs, "eeg"), verbose=False); del d
mne.export.export_raw(out, raw, fmt="edf", physical_range=(-2e-3, 2e-3), overwrite=True, verbose=False)
'''

MEASURE = r'''
import sys, warnings
from pathlib import Path
repo = Path(sys.argv[3])
for p in ("src", "src/dataprep"): sys.path.insert(0, str(repo / p))
warnings.simplefilter("ignore")
import x1_external as X1, preprocessing as P
import numpy as np
def hwm():
    return [float(l.split()[1]) / 1024 for l in open("/proc/self/status") if l.startswith("VmHWM")][0]
path, kind = Path(sys.argv[1]), sys.argv[2]
data = X1.load_18(path, kind)
filt, n = X1.filter_windows(data, 60.0 if kind == "chb" else 50.0)
seg = data[:, :n * P.WIN_SAMPLES].reshape(data.shape[0], n, P.WIN_SAMPLES)
sl = np.all(seg.std(axis=2) < 1e-10, axis=0)
print(f"{hwm():.0f}")
'''

IMPORTS = r'''
import os, sys
sys.path.insert(0, os.environ["THESIS_REPO"] + "/src")
import m2l_core, torch
print([float(l.split()[1]) / 1024 for l in open("/proc/self/status") if l.startswith("VmHWM")][0])
'''


def _job(i):
    if i in (0, 1):
        time.sleep(0.5)
        os.kill(os.getpid(), signal.SIGKILL)
    time.sleep(0.2)
    return i


def m3():
    pool = mp.get_context("spawn").Pool(4, maxtasksperchild=1)
    got, it = [], pool.imap_unordered(_job, range(12))
    try:
        while True:
            got.append(it.next(timeout=20))
    except StopIteration:
        res = f"finished normally ({len(got)}/12)"
    except mp.TimeoutError:
        res = f"HANG: {len(got)}/12 results after 20 s without an exception; missing {sorted(set(range(12)) - set(got))}"
    pool.terminate()
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/m2l_diag_v1")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "make.py").write_text(MAKE)
    (out / "measure.py").write_text(MEASURE)
    (out / "imports.py").write_text(IMPORTS)
    rows = []
    for layout, kind, hrs in (("siena", "siena", (1, 2)), ("chb", "chb", (2, 4))):
        for h in hrs:
            f = out / f"{layout}_{h}h.edf"
            subprocess.run([sys.executable, "-I", str(out / "make.py"), str(h), str(f), layout], check=True,
                           capture_output=True)
            p = subprocess.run([sys.executable, "-I", str(out / "measure.py"), str(f), kind, str(ROOT)], check=True,
                               capture_output=True, text=True)
            rows.append((layout, h, float(p.stdout.strip().splitlines()[-1])))
            f.unlink()
    for layout in ("siena", "chb"):
        (h0, m0), (h1, m1) = [(h, m) for l_, h, m in rows if l_ == layout]
        slope = (m1 - m0) / (h1 - h0)
        print(f"M1 {layout}: {h0} h {m0:.0f} MB, {h1} h {m1:.0f} MB -> {slope:.0f} MB per hour (intercept "
              f"{m0 - slope * h0:.0f} MB)")
    p = subprocess.run([sys.executable, str(out / "imports.py")], env=dict(os.environ, THESIS_REPO=str(ROOT), R2_TEST="1"),
                       capture_output=True, text=True)
    print(f"M2 worker after imports: {p.stdout.strip().splitlines()[-1] if p.stdout.strip() else p.stderr[-300:]} MB")
    print(f"M3 Pool with two killed workers (Python {sys.version.split()[0]}): {m3()}")


if __name__ == "__main__":
    main()
