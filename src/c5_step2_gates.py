#!/usr/bin/env python
"""
c5_step2_gates.py -- chat C5, SzScan Step 2: gates on real data (results/c5_szscan/DESIGN_STEP2.md §4), laptop.

  G1  session engine after Step 2 on the 8 test subjects (headless, the app's own functions, mains 60 Hz)
      = the committed application-tier export web_demo/report_handback/tier2_v4/ (every AI event, every file)
  G3  every Siena file through edf_input.load_any = x1_external.load_18's operations (exact); sha256 = PhysioNet.
      Memory-light reference (Step 2a fix): load_18's operations one derivation at a time (the two electrodes over
      the whole file -> difference -> resample_poly); on files <= 1.5 h load_18 itself is also run and must equal it
  G4  mains suggestion per Siena file (and per hospital record, private report): suggested Hz and the two ratios
  G5  bad-electrode rule per Siena file (and per hospital record, private report): flagged electrodes, z and the
      amplitude ratio to the median electrode (a pure robust-z rule may flag a nearly normal electrode when all
      electrodes have almost the same amplitude -- seen on synthetic data; this column checks it on real data)
  G6  memory: peak PRIVATE process memory (private bytes on Windows, anonymous resident memory on Linux), and the
      resident peak (working set / resident set, file pages included) as information, during
      edf_input.load_any and during Phase A per file (the gate number), the memory before the call and the growth
      per hour of EEG (can read 0 when memory freed by the previous step is reused); the traced numpy heap is kept
      as a further column. (Step 2a second fix: the first fix was judged on the
      traced heap only, which does not see memory-mapped file pages; the laptop ran out of memory.)

C5b (25/11): the readers read in blocks (MNE's all-signal buffer, diag_mne_commit.json); before each file (G1: the
largest file of each subject) the memory model predict_mb is checked against the limit and the script STOPs before
reading (exit 4) instead of being killed by the watchdog; load_18 itself runs on a Siena file when its predicted
commit fits.
Memory-light by construction: one file (G3-G6) or one subject (G1) at a time, one worker, temporary caches deleted
after each subject. --smoke runs only the longest Siena file and the shortest test subject first and prints the
peaks; the smoke reports TOO HIGH when its private-memory peak exceeds --max-gb (default 2, the laptop budget).
A watchdog stops the script at once (exit 3, message STOP) if the private memory exceeds --max-gb at any moment.
Run it in the author's own terminal, not as a Claude Code background command: Claude Code stops its background
commands when the system reports memory pressure, whatever this script uses (smoke of 25/11, killed during import).
Private hospital records (--private-dir): nothing about the files (name, header field, date, path) is printed or
written; the report goes to Agent/inbox/C5_STEP2_PRIVATE.md only (never committed).
Outputs (public): results/c5_szscan/step2/ (GATES.md, g1.csv, siena.csv, gates.json; smoke/ for --smoke).
Run: PYTHONUTF8=1 python src/c5_step2_gates.py --chb F:/Study/Thesis/Dataset/CHB-MIT --siena F:/Study/Thesis/Dataset/siena [--private-dir F:/Study/Thesis/Dataset/Clinical] [--smoke]
"""
import argparse
import csv
import gc
import hashlib
import json
import shutil
import subprocess
import sys
import os
import tempfile
import threading
import time
import tracemalloc
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "web_demo" / "backend"
sys.path.insert(0, str(BACKEND))
import pipeline_demo as pdm          # noqa: E402
import edf_input as EI               # noqa: E402

X1 = pdm.X1
TIER2 = ROOT / "web_demo" / "report_handback" / "tier2_v4"
SIENA_SUMS = ROOT / "results" / "r2" / "r0_data" / "ext" / "physionet_SHA256SUMS_siena.txt"
TEST = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
OUT = ROOT / "results" / "c5_szscan" / "step2"
INBOX = ROOT.parent / "Agent" / "inbox"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def _win_counters():
    import ctypes
    from ctypes import wintypes

    class PMC(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
    c = PMC()
    c.cb = ctypes.sizeof(PMC)
    k32 = ctypes.WinDLL("kernel32")
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    ctypes.WinDLL("psapi").GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(c), c.cb)
    return c.WorkingSetSize / 1e6, c.PagefileUsage / 1e6


def memory_mb() -> tuple[float, float]:
    """(resident MB, private MB) of this process.
    resident = working set on Windows / resident set on Linux: everything in physical memory, file pages included.
    private  = private bytes on Windows / anonymous resident memory on Linux: what the operating system cannot give
               back without paging. Clean file pages (the caches Phase B reads) are resident but not private: Windows
               reclaims them when memory is short, so the watchdog limit applies to private memory (author 25/11 13:34)."""
    if os.name == "nt":
        try:
            import psutil
            mi = psutil.Process().memory_info()
            return mi.rss / 1e6, mi.private / 1e6
        except ImportError:
            return _win_counters()
    rss = anon = 0.0
    with open("/proc/self/status") as fh:
        for line in fh:
            if line.startswith("VmRSS:"):
                rss = int(line.split()[1]) / 1e3
            elif line.startswith("RssAnon:"):
                anon = int(line.split()[1]) / 1e3
    return rss, anon


def process_mb() -> float:
    """Resident memory in MB (see memory_mb)."""
    return memory_mb()[0]


class Watch:
    """Samples the process memory every 0.1 s; records the peaks (resident and private); stops the script at once if
    the PRIVATE memory exceeds the limit."""
    def __init__(self, limit_mb):
        self.limit, self.peak, self.peak_private, self._stop = limit_mb, 0.0, 0.0, False
        self.t = threading.Thread(target=self._run, daemon=True)
        self.t.start()

    def _run(self):
        while not self._stop:
            rss, priv = memory_mb()
            self.peak, self.peak_private = max(self.peak, rss), max(self.peak_private, priv)
            if self.limit and priv > self.limit:
                print(f"STOP: private process memory {priv:.0f} MB > limit {self.limit:.0f} MB (watchdog); "
                      f"nothing written", flush=True)
                os._exit(3)
            time.sleep(0.1)

    def reset(self):
        self.peak, self.peak_private = memory_mb()

    def close(self):
        self._stop = True


WATCH = None
LAST = {}


def traced(fn, *a, **k):
    """-> (output, peak PRIVATE memory MB during the call, seconds); LAST holds the resident peak, the private and
    resident memory before the call and the traced numpy heap peak."""
    gc.collect()
    base_rss, base = memory_mb()
    WATCH.reset()
    tracemalloc.start()
    t0 = time.time()
    try:
        out = fn(*a, **k)
    finally:
        _, heap = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    rss, priv = memory_mb()
    LAST.update(base_mb=base, base_rss_mb=base_rss, rss_peak_mb=max(WATCH.peak, rss), heap_mb=heap / 1e6)
    return out, max(WATCH.peak_private, priv), time.time() - t0


def rowwise_ref(p):
    """x1_external.load_18 (Siena branch) one derivation at a time: same picks, same differences, same resample_poly
    (per-row resample_poly = the 2-D call bit for bit, synthetic test E10). C5b: the two electrodes are read in blocks
    of edf_input.BLOCK_S seconds (MNE commits a buffer for every signal of the file over the samples requested;
    block reads equal the whole-file read bit for bit, results/c5_szscan/step2/diag_mne_commit.json). Independent of
    the app's reader (which reads the 19 electrodes once into a row file)."""
    import math
    import mne
    from scipy.signal import resample_poly
    raw = mne.io.read_raw_edf(str(p), preload=False, verbose=False)
    names = {}
    for ch in raw.ch_names:
        n = ch.upper().replace("EEG", "").strip().replace(" ", "")
        names[X1.SIENA_MAP.get(n, n)] = ch
    fs = int(round(raw.info["sfreq"]))
    g = math.gcd(fs, 256)
    n, step = int(raw.n_times), EI.BLOCK_S * fs
    for a, b in X1.BIPOLAR:
        d = np.empty(n)
        for s0 in range(0, n, step):
            s1 = min(n, s0 + step)
            X = raw.get_data(picks=[names[a], names[b]], start=s0, stop=s1)
            d[s0:s1] = X[0] - X[1]
            del X
        yield d if fs == 256 else resample_poly(d, 256 // g, fs // g)


def predict_mb(p):
    """Memory model of one file (C5b, written before the run; instructions §4): from the EDF header, the largest of
    (0) the bad-electrode table: the 19 electrodes over every 10th window, plus one padded read (10 s of every signal),
    (1) one read block: MNE's all-signal buffer + the 19 electrodes three times (block, MNE's output, the row
        written) + MNE's 10-MB record chunk and its copies (20 MB),
    (2) one derivation at the input rate: two electrode rows and their difference, plus the 256-Hz output,
    (3) Phase A per channel at 256 Hz: x, band-pass, notch (float64) and three float32 copies, plus the window view.
    Synthetic check (test E11, 49 signals, 1 h, 512 Hz): measured committed growth 224 MB.
    Returns (predicted growth MB, signals, input samples, output samples, fs)."""
    h = EI.header(p)
    fs = max(int(round(k / h["rec_dur"])) for k in h["nsamp"])
    n_in = h["n_rec_file"] * max(h["nsamp"])
    n_out = n_in * 256 // fs
    block = EI.BLOCK_S * fs
    n_sig = len(h["labels"])
    m0 = 19 * (n_in // 10) * 8 + n_sig * 10 * fs * 8
    m1 = (n_sig + 3 * 19) * block * 8 + 20e6
    m2 = 3 * n_in * 8 + n_out * 8
    m3 = 3 * n_out * 8 + 3 * n_out * 4 + n_out * 8
    return max(m0, m1, m2, m3) / 1e6, n_sig, n_in, n_out, fs


def admit(p, what):
    """STOP before reading when the private memory now + the predicted growth exceeds the limit (no file attribute of
    a private record is printed: `what` is a neutral label)."""
    pred, *_ = predict_mb(p)
    now = memory_mb()[1]
    if WATCH.limit and now + pred > WATCH.limit:
        print(f"STOP before reading {what}: private memory {now:.0f} MB + predicted {pred:.0f} MB > limit "
              f"{WATCH.limit:.0f} MB; nothing written", flush=True)
        sys.exit(4)
    return pred


def g3_equal(p, d_app):
    ok = True
    for r, ref in enumerate(rowwise_ref(p)):
        ok &= bool(ref.shape[0] == d_app.shape[1] and np.array_equal(np.asarray(d_app[r]), ref))
    return ok


def tier2_events():
    ev, files = {}, {}
    for s in TEST:
        with open(TIER2 / f"{s}_events.csv", newline="") as fh:
            for r in csv.DictReader(fh):
                if r["source"] == "AI":
                    ev.setdefault((s, r["file_name"]), []).append((round(float(r["onset_s"]), 6),
                                                                    round(float(r["offset_s"]), 6)))
    with open(TIER2 / "files.csv", newline="") as fh:
        for r in csv.DictReader(fh):
            files.setdefault(r["subject"], []).append(r["file_name"])
    return ev, files


def g1(chb, subjects):
    ev, files = tier2_events()
    rows = []
    for s in subjects:
        edfs = [Path(chb) / s / f for f in sorted(files[s])]
        admit(max(edfs, key=lambda q: q.stat().st_size), s)
        tmp = Path(tempfile.mkdtemp(prefix=f"c5g1_{s}_"))
        try:
            out, peak, secs = traced(pdm.process_subject_headless, [str(p) for p in edfs], cache_dir=tmp, max_workers=1)
            out = dict(events=out["events"], n_windows=out["n_windows"])   # drop arrays / memory maps
            gc.collect()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        diff = 0
        for f in files[s]:
            got = sorted((round(a, 6), round(b, 6)) for a, b in out["events"].get(f, []))
            want = sorted(ev.get((s, f), []))
            diff += got != want
        hours = sum(out["n_windows"].values()) * 4 / 3600
        rows.append(dict(subject=s, files=len(files[s]), files_differ=diff, events=sum(len(v) for v in out["events"].values()),
                         hours=round(hours, 2), seconds=round(secs, 1), mem_peak_mb=round(peak, 1),
                         mem_before_mb=round(LAST["base_mb"], 1), resident_peak_mb=round(LAST["rss_peak_mb"], 1),
                         heap_peak_mb=round(LAST["heap_mb"], 1)))
        print(f"G1 {s}: {rows[-1]}", flush=True)
    return rows


def siena_files(root):
    return sorted(Path(root).rglob("PN*.edf"))


def bad_ratio(meta):
    amps = np.array([t["amp_uv"] for t in meta["electrodes"]])
    med = float(np.median(amps))
    return " ".join(f"{t['electrode']}:{t['amp_uv'] / med:.2f}" for t in meta["electrodes"] if t["bad"])


def siena_one(p, sums):
    r = dict(subject=p.parent.name, file=p.name, size_mb=round(p.stat().st_size / 1e6, 1))
    want = sums.get(f"{p.parent.name}/{p.name}")
    r["sha_ok"] = (sha256(p) == want) if want else "not listed"
    r["predicted_mb"] = round(admit(p, f"{p.parent.name}/{p.name}"), 1)
    tmp = Path(tempfile.mkdtemp(prefix="c5g6_"))
    try:
        try:
            (d_app, meta), peak_load, s_load = traced(EI.load_any, p, mains="auto", workdir=tmp)
            r.update(suggested_hz=meta["notch_hz"])
            load_heap = LAST["heap_mb"]
        except EI.InputError as e:
            r.update(suggested_hz="none", note=str(e)[:120])
            (d_app, meta), peak_load, s_load = traced(EI.load_any, p, mains=50.0, workdir=tmp)
            load_heap = LAST["heap_mb"]
        load_rss = LAST["rss_peak_mb"]
        r.update(montage=meta["montage"], fs_in=meta["fs_in"], r50=round(meta["mains_ratios"][0], 2),
                 r60=round(meta["mains_ratios"][1], 2), bad=" ".join(meta["bad"]), bad_ratio=bad_ratio(meta),
                 max_z=round(max(t["z"] for t in meta["electrodes"]), 2), load_mem_mb=round(peak_load, 1),
                 load_resident_mb=round(load_rss, 1), load_heap_mb=round(load_heap, 1), load_s=round(s_load, 1))
        hours = d_app.shape[1] / 256 / 3600
        r["g3_equal"] = g3_equal(p, d_app)
        _, n_sig, n_in, n_out, _ = predict_mb(p)        # load_18 itself = the row-wise reference, when it fits
        need = ((n_sig + 19) * n_in + 18 * n_out) * 8 / 1e6
        if memory_mb()[1] + need < WATCH.limit - 200:
            d_x1 = X1.load_18(p, "siena")
            r["g3_load18_equal"] = bool(d_x1.shape == d_app.shape and np.array_equal(np.asarray(d_app), d_x1))
            del d_x1
        else:
            r["g3_load18_skipped_mb"] = round(need)
        EI.drop_temp(meta["data_path"], d_app)
        del d_app
        gc.collect()
        res, peak_a, s_a = traced(pdm.process_file_phase_a, str(p), None, tmp / "pa", mains=50.0)
        base_a, heap_a, rss_a = LAST["base_mb"], LAST["heap_mb"], LAST["rss_peak_mb"]
        del res                                          # closes the memory maps before the folder is removed
        gc.collect()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    r.update(hours=round(hours, 3), phase_a_mem_mb=round(peak_a, 1), phase_a_mem_before_mb=round(base_a, 1),
             phase_a_resident_mb=round(rss_a, 1),
             phase_a_growth_mb_per_hour=round((peak_a - base_a) / max(hours, 1e-9), 1),
             phase_a_heap_mb=round(heap_a, 1), phase_a_s=round(s_a, 1))
    print(f"G3-G6 {p.parent.name}/{p.name}: {r}", flush=True)
    return r


def private_report(pdir):
    """Hospital records: counts only, no file attribute printed or written except durations and electrode names."""
    files = sorted((p for p in Path(pdir).iterdir() if p.is_file() and p.suffix.lower() == ".edf"),
                   key=lambda p: -p.stat().st_size)
    L = ["# C5 Step 2 -- hospital records (PRIVATE, laptop only; never commit)", "",
         "Records named by decreasing file size (clin01 = larger), as src/v9_clinical_run.py.", "",
         "| record | hours | suggested mains | r50 | r60 | electrodes flagged (z) | load memory peak MB | Phase A memory peak MB |",
         "|---|---|---|---|---|---|---|---|"]
    for i, p in enumerate(files):
        lab = f"clin{i + 1:02d}"
        admit(p, lab)
        tmp = Path(tempfile.mkdtemp(prefix="c5priv_"))
        try:
            (d, meta), peak_l, _ = traced(EI.load_any, p, mains="auto", workdir=tmp)
            sug = f"{meta['notch_hz']:.0f} Hz"
        except EI.InputError:
            (d, meta), peak_l, _ = traced(EI.load_any, p, mains=50.0, workdir=tmp)
            sug = "none"
        hours = d.shape[1] / 256 / 3600
        EI.drop_temp(meta["data_path"], d)
        del d
        gc.collect()
        amps = np.median([t["amp_uv"] for t in meta["electrodes"]])
        flagged = ", ".join(f"{t['electrode']} (z {t['z']:.1f}, x{t['amp_uv'] / amps:.2f})"
                            for t in meta["electrodes"] if t["bad"]) or "none"
        try:
            res, peak_a, _ = traced(pdm.process_file_phase_a, str(p), None, tmp / "pa", mains=50.0)
            del res
            gc.collect()
        except Exception as e:      # noqa: BLE001  (message only, never a path)
            peak_a = float("nan")
            flagged += f"; Phase A error {type(e).__name__}"
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        r50, r60 = meta["mains_ratios"]
        L.append(f"| {lab} | {hours:.2f} | {sug} | {r50:.1f} | {r60:.1f} | {flagged} | {peak_l:.0f} | {peak_a:.0f} |")
        trunc = [n for n in meta["notices"] if "declares" in n]
        if trunc:
            L.append(f"|  | notice: {trunc[0]} | | | | | | |")
        print(f"private {lab}: done", flush=True)
    INBOX.mkdir(parents=True, exist_ok=True)
    (INBOX / "C5_STEP2_PRIVATE.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chb", required=True)
    ap.add_argument("--siena", required=True)
    ap.add_argument("--private-dir", default=None)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--max-gb", type=float, default=2.0)
    a = ap.parse_args()
    global WATCH
    WATCH = Watch(a.max_gb * 1000)
    try:
        import psutil
        print(f"available system memory at start: {psutil.virtual_memory().available / 1e6:.0f} MB; "
              f"this process {memory_mb()[0]:.0f} MB resident, {memory_mb()[1]:.0f} MB private; "
              f"private limit {a.max_gb * 1000:.0f} MB", flush=True)
    except ImportError:
        print(f"this process {memory_mb()[0]:.0f} MB resident, {memory_mb()[1]:.0f} MB private; "
              f"private limit {a.max_gb * 1000:.0f} MB (psutil not installed)", flush=True)
    out = OUT / "smoke" if a.smoke else OUT
    out.mkdir(parents=True, exist_ok=True)
    sums = {}
    for line in SIENA_SUMS.read_text().splitlines():
        parts = line.split()
        if len(parts) == 2:
            sums[parts[1].lstrip("*").removeprefix("./")] = parts[0].lower()
    sf = siena_files(a.siena)
    if not sf:
        raise SystemExit(f"STOP: no PN*.edf under {a.siena}")
    smoke_file = max(sf, key=lambda p: p.stat().st_size)
    if a.smoke:
        ev, files = tier2_events()
        shortest = min(TEST, key=lambda s: sum((Path(a.chb) / s / f).stat().st_size for f in files[s]))
        g1rows = g1(a.chb, [shortest])
        srows = [siena_one(smoke_file, sums)]
        peak = max([r["mem_peak_mb"] for r in g1rows] + [srows[0]["phase_a_mem_mb"], srows[0]["load_mem_mb"]])
        print(f"SMOKE: private memory peak {peak:.0f} MB (G1 {shortest}, Siena {smoke_file.parent.name}/{smoke_file.name}); "
              f"limit {a.max_gb * 1000:.0f} MB -> {'OK' if peak <= a.max_gb * 1000 else 'TOO HIGH'}")
    else:
        g1rows = g1(a.chb, TEST)
        srows = [siena_one(p, sums) for p in sf]
        if a.private_dir:
            private_report(a.private_dir)
    for name, rows in (("g1.csv", g1rows), ("siena.csv", srows)):
        keys = sorted({k for r in rows for k in r}, key=lambda k: (k not in ("subject", "file"), k))
        with open(out / name, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(rows)
    gates = dict(
        G1=dict(PASS=all(r["files_differ"] == 0 for r in g1rows), subjects=len(g1rows),
                files_differ=sum(r["files_differ"] for r in g1rows)),
        G3=dict(PASS=all(r["g3_equal"] is True for r in srows)
                and all(r.get("g3_load18_equal", True) is True for r in srows), files=len(srows),
                load18_checked=sum("g3_load18_equal" in r for r in srows),
                load18_skipped=sum("g3_load18_skipped_mb" in r for r in srows),
                sha_bad=[r["file"] for r in srows if r["sha_ok"] is False]),
        G4=dict(suggested_50=sum(r.get("suggested_hz") == 50.0 for r in srows),
                suggested_60=sum(r.get("suggested_hz") == 60.0 for r in srows),
                none=sum(r.get("suggested_hz") == "none" for r in srows)),
        G5=dict(files_flagged=sum(bool(r.get("bad")) for r in srows),
                flagged=[f"{r['file']}: {r['bad']}" for r in srows if r.get("bad")]),
        G6=dict(max_phase_a_mem_mb=max(r["phase_a_mem_mb"] for r in srows),
                max_load_mem_mb=max(r["load_mem_mb"] for r in srows),
                max_phase_a_growth_mb_per_hour=max(r["phase_a_growth_mb_per_hour"] for r in srows),
                max_g1_mem_mb=max(r["mem_peak_mb"] for r in g1rows),
                max_predicted_mb=max(r["predicted_mb"] for r in srows)),
    )
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=str(ROOT)).stdout.strip()
    (out / "gates.json").write_text(json.dumps(dict(commit=commit, smoke=a.smoke, gates=gates), indent=1, default=str),
                                    encoding="utf-8")
    L = [f"# SzScan Step 2 gates{' — SMOKE' if a.smoke else ''}", "", f"Commit `{commit}`.", "",
         f"- **G1** session engine = committed application-tier events: {'PASS' if gates['G1']['PASS'] else 'FAIL'} "
         f"({gates['G1']['subjects']} subjects, {gates['G1']['files_differ']} files differ)",
         f"- **G3** Siena through edf_input = x1_external.load_18: {'PASS' if gates['G3']['PASS'] else 'FAIL'} "
         f"({gates['G3']['files']} files, load_18 itself on {gates['G3']['load18_checked']} files, skipped on {gates['G3']['load18_skipped']} (predicted above the limit); sha256 not matching PhysioNet: {gates['G3']['sha_bad'] or 'none'})",
         f"- **G4** mains suggestion on Siena: 50 Hz {gates['G4']['suggested_50']}, 60 Hz {gates['G4']['suggested_60']}, "
         f"none {gates['G4']['none']}",
         f"- **G5** bad-electrode rule on Siena: {gates['G5']['files_flagged']} files flagged "
         f"{gates['G5']['flagged'] or ''}",
         f"- **G6** private memory peak (resident peaks, file pages included, in the CSVs): load max {gates['G6']['max_load_mem_mb']:.0f} MB, "
         f"Phase A max {gates['G6']['max_phase_a_mem_mb']:.0f} MB; G1 per subject max "
         f"{gates['G6']['max_g1_mem_mb']:.0f} MB", "",
         "Per row: `g1.csv`, `siena.csv`. Hospital records: private report in Agent/inbox only."]
    (out / "GATES.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(json.dumps({k: v.get("PASS") for k, v in gates.items() if "PASS" in v}))


if __name__ == "__main__":
    main()
