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
  G6  memory: traced peak of edf_input.load_any and of Phase A per file (MB and MB per hour of EEG)

Memory-light by construction: one file (G3-G6) or one subject (G1) at a time, one worker, temporary caches deleted
after each subject. --smoke runs only the longest Siena file and the shortest test subject first and prints the
traced peaks; the smoke reports TOO HIGH when its traced peak exceeds --max-gb (default 2, the laptop budget).
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
import tempfile
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


def traced(fn, *a, **k):
    gc.collect()
    tracemalloc.start()
    t0 = time.time()
    try:
        out = fn(*a, **k)
    finally:
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    return out, peak / 1e6, time.time() - t0


def rowwise_ref(p):
    """x1_external.load_18 (Siena branch) one derivation at a time: same picks, same differences, same resample_poly
    (per-row resample_poly = the 2-D call bit for bit, synthetic test E10)."""
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
    for a, b in X1.BIPOLAR:
        X = raw.get_data(picks=[names[a], names[b]])          # float64 already; load_18's astype is a copy
        d = X[0] - X[1]
        del X
        yield d if fs == 256 else resample_poly(d, 256 // g, fs // g)


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
                         hours=round(hours, 2), seconds=round(secs, 1), traced_peak_mb=round(peak, 1)))
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
    tmp = Path(tempfile.mkdtemp(prefix="c5g6_"))
    try:
        try:
            (d_app, meta), peak_load, s_load = traced(EI.load_any, p, mains="auto", workdir=tmp)
            r.update(suggested_hz=meta["notch_hz"])
        except EI.InputError as e:
            r.update(suggested_hz="none", note=str(e)[:120])
            (d_app, meta), peak_load, s_load = traced(EI.load_any, p, mains=50.0, workdir=tmp)
        r.update(montage=meta["montage"], fs_in=meta["fs_in"], r50=round(meta["mains_ratios"][0], 2),
                 r60=round(meta["mains_ratios"][1], 2), bad=" ".join(meta["bad"]), bad_ratio=bad_ratio(meta),
                 max_z=round(max(t["z"] for t in meta["electrodes"]), 2), load_peak_mb=round(peak_load, 1),
                 load_s=round(s_load, 1))
        hours = d_app.shape[1] / 256 / 3600
        r["g3_equal"] = g3_equal(p, d_app)
        if hours <= 1.5:                                 # load_18 itself = the row-wise reference (small files)
            d_x1 = X1.load_18(p, "siena")
            r["g3_load18_equal"] = bool(d_x1.shape == d_app.shape and np.array_equal(np.asarray(d_app), d_x1))
            del d_x1
        del d_app
        if meta["data_path"] is not None:
            Path(meta["data_path"]).unlink(missing_ok=True)
        gc.collect()
        res, peak_a, s_a = traced(pdm.process_file_phase_a, str(p), None, tmp / "pa", mains=50.0)
        del res                                          # closes the memory maps before the folder is removed
        gc.collect()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    r.update(hours=round(hours, 3), phase_a_peak_mb=round(peak_a, 1),
             phase_a_mb_per_hour=round(peak_a / max(hours, 1e-9), 1), phase_a_s=round(s_a, 1))
    print(f"G3-G6 {p.parent.name}/{p.name}: {r}", flush=True)
    return r


def private_report(pdir):
    """Hospital records: counts only, no file attribute printed or written except durations and electrode names."""
    files = sorted((p for p in Path(pdir).iterdir() if p.is_file() and p.suffix.lower() == ".edf"),
                   key=lambda p: -p.stat().st_size)
    L = ["# C5 Step 2 -- hospital records (PRIVATE, laptop only; never commit)", "",
         "Records named by decreasing file size (clin01 = larger), as src/v9_clinical_run.py.", "",
         "| record | hours | suggested mains | r50 | r60 | electrodes flagged (z) | load peak MB | Phase A peak MB |",
         "|---|---|---|---|---|---|---|---|"]
    for i, p in enumerate(files):
        lab = f"clin{i + 1:02d}"
        tmp = Path(tempfile.mkdtemp(prefix="c5priv_"))
        try:
            (d, meta), peak_l, _ = traced(EI.load_any, p, mains="auto", workdir=tmp)
            sug = f"{meta['notch_hz']:.0f} Hz"
        except EI.InputError:
            (d, meta), peak_l, _ = traced(EI.load_any, p, mains=50.0, workdir=tmp)
            sug = "none"
        hours = d.shape[1] / 256 / 3600
        del d
        if meta["data_path"] is not None:
            Path(meta["data_path"]).unlink(missing_ok=True)
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
        peak = max([r["traced_peak_mb"] for r in g1rows] + [srows[0]["phase_a_peak_mb"], srows[0].get("load_peak_mb", 0)])
        print(f"SMOKE: traced peak {peak:.0f} MB (G1 {shortest}, Siena {smoke_file.parent.name}/{smoke_file.name}); "
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
                sha_bad=[r["file"] for r in srows if r["sha_ok"] is False]),
        G4=dict(suggested_50=sum(r.get("suggested_hz") == 50.0 for r in srows),
                suggested_60=sum(r.get("suggested_hz") == 60.0 for r in srows),
                none=sum(r.get("suggested_hz") == "none" for r in srows)),
        G5=dict(files_flagged=sum(bool(r.get("bad")) for r in srows),
                flagged=[f"{r['file']}: {r['bad']}" for r in srows if r.get("bad")]),
        G6=dict(max_phase_a_peak_mb=max(r["phase_a_peak_mb"] for r in srows),
                max_load_peak_mb=max(r["load_peak_mb"] for r in srows),
                max_phase_a_mb_per_hour=max(r["phase_a_mb_per_hour"] for r in srows),
                max_g1_peak_mb=max(r["traced_peak_mb"] for r in g1rows)),
    )
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=str(ROOT)).stdout.strip()
    (out / "gates.json").write_text(json.dumps(dict(commit=commit, smoke=a.smoke, gates=gates), indent=1, default=str),
                                    encoding="utf-8")
    L = [f"# SzScan Step 2 gates{' — SMOKE' if a.smoke else ''}", "", f"Commit `{commit}`.", "",
         f"- **G1** session engine = committed application-tier events: {'PASS' if gates['G1']['PASS'] else 'FAIL'} "
         f"({gates['G1']['subjects']} subjects, {gates['G1']['files_differ']} files differ)",
         f"- **G3** Siena through edf_input = x1_external.load_18: {'PASS' if gates['G3']['PASS'] else 'FAIL'} "
         f"({gates['G3']['files']} files, load_18 itself on {gates['G3']['load18_checked']} files <= 1.5 h; sha256 not matching PhysioNet: {gates['G3']['sha_bad'] or 'none'})",
         f"- **G4** mains suggestion on Siena: 50 Hz {gates['G4']['suggested_50']}, 60 Hz {gates['G4']['suggested_60']}, "
         f"none {gates['G4']['none']}",
         f"- **G5** bad-electrode rule on Siena: {gates['G5']['files_flagged']} files flagged "
         f"{gates['G5']['flagged'] or ''}",
         f"- **G6** traced peak: load max {gates['G6']['max_load_peak_mb']:.0f} MB, "
         f"Phase A max {gates['G6']['max_phase_a_peak_mb']:.0f} MB "
         f"({gates['G6']['max_phase_a_mb_per_hour']:.0f} MB per hour of EEG); G1 per subject max "
         f"{gates['G6']['max_g1_peak_mb']:.0f} MB", "",
         "Per row: `g1.csv`, `siena.csv`. Hospital records: private report in Agent/inbox only."]
    (out / "GATES.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(json.dumps({k: v.get("PASS") for k, v in gates.items() if "PASS" in v}))


if __name__ == "__main__":
    main()
