#!/usr/bin/env python
"""
c5_diag_mne_commit.py -- chat C5b, diagnosis of the Step 2 smoke STOP (25/11: private memory 9,902 MB on PN14-3).

Hypothesis H1 (written before the run): MNE's EDF reader (mne 1.12.1, mne/io/edf/edf.py, _read_segment_file)
allocates np.zeros((ALL signals of the file, samples requested)) whatever the picks. Reading two electrodes over the
whole file therefore commits n_signals x n_samples x 8 bytes. On Windows that counts in private bytes (commit charge)
although the rows never written are not touched; on Linux it shows in VmData, not in resident memory -- which is why
the synthetic tests of C5 (resident memory) did not see it.
  Prediction if H1 holds: commit growth of a whole-file read ~ (n_signals + 2) x n x 8 B; of a read in blocks of
  --block-s seconds ~ n_signals x block x 8 B + 2 x n x 8 B (the output rows).
  If the whole-file growth is only ~ 2 x n x 8 B, H1 is rejected and the cause is in our own code.

Measures, on ONE EDF, the process memory while reading the first derivation's two electrodes (Fp1, F7) with
raw.get_data: (a) over the whole file, (b) in blocks; checks (a) == (b) bit for bit. Memory columns:
  commit   = private bytes on Windows (psutil), VmData on Linux (anonymous memory reserved, touched or not)
  resident = working set / resident set
Refuses to run when the predicted whole-file commit exceeds --max-gb (default 1.5). Light imports only (numpy, mne,
psutil). Public data only (Siena); prints the number of signals, never a label list or a header field.
Output: printed lines and results/c5_szscan/step2/diag_mne_commit.json.
Run: PYTHONUTF8=1 python src/c5_diag_mne_commit.py --edf F:/Study/Thesis/Dataset/siena/PN00/PN00-4.edf
"""
import argparse
import gc
import json
import os
import platform
import threading
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "c5_szscan" / "step2" / "diag_mne_commit.json"
ALIASES = {"T3": "T7", "T4": "T8", "T5": "P7", "T6": "P8"}      # x1_external.SIENA_MAP


def memory_mb():
    """-> dict(commit, resident) in MB (see the module docstring)."""
    if os.name == "nt":
        import psutil
        mi = psutil.Process().memory_info()
        return dict(commit=mi.private / 1e6, resident=mi.rss / 1e6)
    d = {}
    with open("/proc/self/status") as fh:
        for line in fh:
            k, _, v = line.partition(":")
            if k in ("VmData", "VmRSS"):
                d[k] = int(v.split()[0]) / 1e3
    return dict(commit=d["VmData"], resident=d["VmRSS"])


class Peak:
    def __init__(self):
        self.base = memory_mb()
        self.peak = dict(self.base)
        self._stop = False
        self.t = threading.Thread(target=self._run, daemon=True)
        self.t.start()

    def _run(self):
        while not self._stop:
            m = memory_mb()
            for k in m:
                self.peak[k] = max(self.peak[k], m[k])
            time.sleep(0.005)

    def done(self):
        self._stop = True
        self.t.join()
        m = memory_mb()
        for k in m:
            self.peak[k] = max(self.peak[k], m[k])
        return {f"{k}_growth_mb": round(self.peak[k] - self.base[k], 1) for k in self.base} | \
               {f"{k}_before_mb": round(self.base[k], 1) for k in self.base}


def header_counts(path):
    """Number of signals, data records in the file and samples per record (EDF specification, Kemp et al. 1992)."""
    with open(path, "rb") as fh:
        h = fh.read(256)
        ns = int(h[252:256].decode("ascii").strip())
        hdr_bytes = int(h[184:192].decode("ascii").strip())
        s = fh.read(ns * 256)
    nsamp = [int(s[ns * 216 + i * 8: ns * 216 + (i + 1) * 8].decode("ascii").strip()) for i in range(ns)]
    n_rec = (Path(path).stat().st_size - hdr_bytes) // (2 * sum(nsamp))
    return ns, n_rec, nsamp


def norm(ch):
    n = ch.upper().replace("EEG", "").strip().replace(" ", "")
    return ALIASES.get(n, n)


def run(edf, block_s=600, max_gb=1.5, out=OUT):
    import mne
    ns, n_rec, nsamp = header_counts(edf)
    raw = mne.io.read_raw_edf(str(edf), preload=False, verbose="ERROR")
    names = {}
    for ch in raw.ch_names:
        names.setdefault(norm(ch), ch)
    picks = [names["FP1"], names["F7"]]
    n, fs = int(raw.n_times), int(round(raw.info["sfreq"]))
    n_read = len(raw.ch_names)            # signals MNE keeps (annotation channels excluded)
    step = block_s * fs
    pred = dict(whole_mb=round((n_read + 2) * n * 8 / 1e6, 1),
                blocks_mb=round((n_read * min(step, n) + 2 * n) * 8 / 1e6, 1),
                rows_only_mb=round(2 * n * 8 / 1e6, 1))
    res = dict(file=Path(edf).name, platform=platform.platform(), mne=mne.__version__, numpy=np.__version__,
               signals_in_header=ns, signals_read_by_mne=n_read, fs=fs, hours=round(n / fs / 3600, 3),
               block_s=block_s, predicted_if_H1=pred)
    print(f"{res['file']}: {ns} signals in the header ({n_read} read by MNE), {res['hours']} h at {fs} Hz")
    print(f"predicted commit growth if H1: whole-file {pred['whole_mb']} MB, blocks {pred['blocks_mb']} MB "
          f"(rows alone {pred['rows_only_mb']} MB)")
    if pred["whole_mb"] > max_gb * 1000:
        raise SystemExit(f"STOP: predicted whole-file commit {pred['whole_mb']} MB > {max_gb * 1000:.0f} MB; "
                         f"choose a shorter file")

    gc.collect()
    p = Peak()
    t0 = time.time()
    whole = raw.get_data(picks=picks)
    res["whole"] = p.done() | dict(seconds=round(time.time() - t0, 2))
    print(f"(a) whole-file read: {res['whole']}")

    gc.collect()
    p = Peak()
    t0 = time.time()
    blocks = np.empty((2, n))
    for a in range(0, n, step):
        b = min(n, a + step)
        blocks[:, a:b] = raw.get_data(picks=picks, start=a, stop=b)
    res["blocks"] = p.done() | dict(seconds=round(time.time() - t0, 2))
    print(f"(b) read in {block_s}-s blocks: {res['blocks']}")

    res["equal_bit_for_bit"] = bool(np.array_equal(whole, blocks))
    g = res["whole"]["commit_growth_mb"]
    res["reading"] = ("H1 supported: the whole-file read commits about the all-signal buffer"
                      if g > 0.6 * pred["whole_mb"] and res["blocks"]["commit_growth_mb"] < 0.6 * g
                      else "H1 not supported: the whole-file commit growth is not the all-signal buffer")
    print(f"equal bit for bit: {res['equal_bit_for_bit']}; {res['reading']}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"written {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--edf", required=True)
    ap.add_argument("--block-s", type=int, default=600)
    ap.add_argument("--max-gb", type=float, default=1.5)
    a = ap.parse_args()
    run(a.edf, a.block_s, a.max_gb)


if __name__ == "__main__":
    main()
