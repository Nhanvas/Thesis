#!/usr/bin/env python
"""
c5_diag_edfplus.py -- chat C5b, diagnosis of the full-gate STOP of 25-26/11 (private memory 11,152 MB in the hospital
part, after G1 and every Siena file had passed).

Hypothesis H2 (written before the check): when an EDF+ file holds an annotation signal ("EDF Annotations"), MNE 1.12.1
reads that signal over the WHOLE file while opening it (mne/io/edf/edf.py, RawEDF.__init__, lines 226-236: a call of
_read_segment_file from sample 0 to n_times), and that call allocates its buffer for every signal of the file over the
whole length (np.zeros((len(orig_sel), n))). The block reading of C5b (diag_mne_commit.json) never reaches this read.
  Prediction if H2 holds: (a) the hospital files carry an annotation signal; (b) opening such a file commits about
  (signals other than the annotation signal) x n_times x 8 bytes -- clin01 ~ 9.9 GB, matching the 11.15 GB watchdog
  reading minus the ~1.1 GB base; (c) the same file without the annotation signal opens with no such growth.

Two modes:
  --dir DIR      laptop, header only (never opens a file with MNE): for every EDF in DIR, ordered by decreasing size and
                 named clin01, clin02, ... as src/v9_clinical_run.py, prints whether an annotation signal exists, the
                 number of other signals, the hours of signal in the file and the predicted commit of MNE's open.
                 Prints no file name, label list or header field (privacy, integrity rule 7). Writes nothing.
  --synthetic    a 1-h 512-Hz EDF+ with 49 signals plus an annotation signal, and the same file without it: commit
                 growth of mne.io.read_raw_edf(preload=False) for each (VmData on Linux, private bytes on Windows).
Run: PYTHONUTF8=1 python src/c5_diag_edfplus.py --dir F:/Study/Thesis/Dataset/Clinical
"""
import argparse
import gc
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c5_diag_mne_commit as DG      # noqa: E402  (memory_mb, header_counts)

TAL = "EDF ANNOTATIONS"


def header_info(path):
    """-> dict(annot, n_other, fs, hours, predicted_mb) from the EDF header and the file size only."""
    with open(path, "rb") as fh:
        h = fh.read(256)
        ns = int(h[252:256].decode("ascii").strip())
        hdr = int(h[184:192].decode("ascii").strip())
        rec_dur = float(h[244:252].decode("ascii").strip())
        s = fh.read(ns * 256)
    labels = [s[i * 16:(i + 1) * 16].decode("latin-1").strip().upper() for i in range(ns)]
    nsamp = [int(s[ns * 216 + i * 8: ns * 216 + (i + 1) * 8].decode("ascii").strip()) for i in range(ns)]
    n_rec = (Path(path).stat().st_size - hdr) // (2 * sum(nsamp))
    tal = [i for i, lab in enumerate(labels) if lab == TAL]
    other = [i for i in range(ns) if i not in tal]
    spr = max(nsamp[i] for i in other)                 # MNE's n_times uses the largest rate
    n_times = n_rec * spr
    return dict(annot=bool(tal), n_other=len(other), fs=round(spr / rec_dur),
                hours=round(n_rec * rec_dur / 3600, 3),
                predicted_mb=round(len(other) * n_times * 8 / 1e6) if tal else 0)


def scan(d):
    files = sorted((p for p in Path(d).iterdir() if p.is_file() and p.suffix.lower() == ".edf"),
                   key=lambda p: -p.stat().st_size)
    for i, p in enumerate(files):
        r = header_info(p)
        print(f"clin{i + 1:02d}: annotation signal {'YES' if r['annot'] else 'no'}; {r['n_other']} other signals; "
              f"{r['hours']} h at {r['fs']} Hz; predicted commit of MNE's open {r['predicted_mb']} MB", flush=True)
    print("H2 (a) holds for: " + (", ".join(f"clin{i + 1:02d}" for i, p in enumerate(files)
                                           if header_info(p)["annot"]) or "none"))


def write_edf(path, n_sig, hours, fs, annot):
    """EDF (Kemp et al. 1992) or EDF+C (Kemp & Olivan 2003) with a time-keeping annotation per 1-s record."""
    n_rec = int(hours * 3600)
    labels = ["EEG Fp1", "EEG F7"] + [f"EEG X{i:02d}" for i in range(n_sig - 2)]
    nsamp = [fs] * n_sig
    dmin, dmax, pmin, pmax = ["-32768"] * n_sig, ["32767"] * n_sig, ["-3276.8"] * n_sig, ["3276.7"] * n_sig
    if annot:
        labels.append("EDF Annotations"); nsamp.append(30)
        dmin.append("-32768"); dmax.append("32767"); pmin.append("-1"); pmax.append("1")
    ns = len(labels)

    def f(v, w):
        return str(v)[:w].ljust(w).encode("ascii")
    hdr = (f("0", 8) + f("X X X X", 80) + f("Startdate X X X X", 80) + f("01.01.01", 8) + f("00.00.00", 8)
           + f(256 * (ns + 1), 8) + f("EDF+C" if annot else "", 44) + f(n_rec, 8) + f(1, 8) + f(ns, 4))
    for w, vals in ((16, labels), (80, [""] * ns), (8, ["uV"] * n_sig + ([""] if annot else [])), (8, pmin),
                    (8, pmax), (8, dmin), (8, dmax), (80, [""] * ns), (8, nsamp), (32, [""] * ns)):
        hdr += b"".join(f(v, w) for v in vals)
    rng = np.random.default_rng(0)
    with open(path, "wb") as fh:
        fh.write(hdr)
        for k in range(0, n_rec, 600):
            m = min(600, n_rec - k)
            sig = rng.integers(-2000, 2000, size=(m, n_sig * fs), dtype=np.int16).tobytes()
            if not annot:
                fh.write(sig)
                continue
            rows = []
            for j in range(m):
                tal = f"+{k + j}\x14\x14\x00".encode("ascii").ljust(60, b"\x00")
                rows.append(sig[j * n_sig * fs * 2:(j + 1) * n_sig * fs * 2] + tal)
            fh.write(b"".join(rows))


def open_growth(path):
    import mne
    import threading
    gc.collect()
    base, peak, stop = DG.memory_mb()["commit"], [0.0], [False]

    def mon():
        while not stop[0]:
            peak[0] = max(peak[0], DG.memory_mb()["commit"])
            time.sleep(0.005)
    th = threading.Thread(target=mon, daemon=True)
    th.start()
    raw = mne.io.read_raw_edf(str(path), preload=False, verbose="ERROR")
    stop[0] = True
    th.join()
    n = raw.n_times
    del raw
    return round(max(peak[0], DG.memory_mb()["commit"]) - base, 1), n


def synthetic():
    with tempfile.TemporaryDirectory() as d:
        res = {}
        for annot in (True, False):
            p = Path(d) / f"syn_{annot}.edf"
            write_edf(p, 49, 1.0, 512, annot)
            g, n = open_growth(p)
            res[annot] = g
            print(f"synthetic 49 signals, 1 h, 512 Hz, annotation signal {annot}: commit growth at open {g} MB "
                  f"(all-signal buffer {49 * n * 8 / 1e6:.0f} MB)", flush=True)
            p.unlink()
        print("H2 mechanism " + ("reproduced" if res[True] > 0.8 * 49 * n * 8 / 1e6 > 5 * max(res[False], 1)
                                 else "NOT reproduced"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir")
    ap.add_argument("--synthetic", action="store_true")
    a = ap.parse_args()
    if a.synthetic:
        synthetic()
    if a.dir:
        scan(a.dir)


if __name__ == "__main__":
    main()
