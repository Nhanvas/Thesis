#!/usr/bin/env python
"""
c5_g2_test.py -- chat C5c, Step 2c: tests of src/c5_g2.py before the Kaggle runs (build container / laptop; synthetic
data only).
  T1 labels() = m2l_core.features' scorer labels (seizure windows; CHB-MIT 4-h buffer; none for Siena) on a synthetic
     18-derivation recording with two seizures
  T2 g2_job on a synthetic CHB-MIT-like EDF (40 min, 256 Hz, one seizure) and a Siena-like referential EDF (35 min,
     512 Hz, 50 Hz), with deletion refused while a file is still memory-mapped (as Windows; laptop 27/11): no error,
     every field present, the scratch cache removed, the job's module shas = the parent's;
     events = engine_file.run_file on the application's own Phase A caches (the upload path) for the same file
  T3 compare(): an equal row -> no difference; q off by 1e-6 relative -> 'q'; one more false alarm -> 'fp'; NaN q on
     both sides (short recording) -> equal
  T4 gate_g2 writes g2.csv before a FAIL stops the run
Run: PYTHONUTF8=1 python src/c5_g2_test.py
"""
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import c5_step2_test as T            # noqa: E402  (synthetic EDF writers)
import c5_g2 as G                    # noqa: E402

RES = []


def check(name, ok, detail=""):
    RES.append((name, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}", flush=True)


def t1():
    M = G.M
    n, secs = 300, 300 * M.WIN
    sz = [(200, 240), (700, 712)]
    data = np.random.default_rng(1).normal(0, 2e-5, (18, n * M.WS))
    mu, sd = np.zeros(18), np.ones(18) * 2e-5
    for kind in ("chb", "siena"):
        ref = M.features(data, 60.0, sz, (mu, sd), buffer=(kind == "chb"))
        lab, buf = G.labels(n, sz, kind)
        check(f"T1 labels = m2l_core.features ({kind})", np.array_equal(lab, ref["is_ictal"])
              and np.array_equal(buf, ref["is_buffer"]), f"{int(lab.sum())} seizure windows, {int(buf.sum())} buffer")


def t2(root):
    import pipeline_demo as pdm
    import engine_file as EF
    chb = root / "chb95_01.edf"
    x = T.eeg(23, 40 * 60, 256, 81, 60)
    x[:, 600 * 256:660 * 256] *= 6
    T.write_edf(chb, T.CHB23, 256, x)
    sie = root / "PN95-1.edf"
    xs = T.eeg(20, 35 * 60, 512, 82, 50)
    xs[:19, 900 * 512:960 * 512] *= 6
    T.write_edfplus(sie, [f"EEG {e.capitalize()}" for e in T.REF19] + ["EKG"], [512] * 20, list(xs), annot=False)
    parent = {**G.M.code_shas(), **G.app_shas()}
    # Windows refuses to delete a file that is still memory-mapped (PermissionError, WinError 32; laptop 27/11). Linux
    # allows it, so here a deletion of a file still listed in /proc/self/maps raises the same error.
    real_unlink = Path.unlink

    def win_unlink(self, missing_ok=False):
        try:
            maps = open("/proc/self/maps").read()
        except OSError:
            maps = ""
        if str(Path(self).resolve()) in maps:
            raise PermissionError(32, "The process cannot access the file because it is being used by another process",
                                  str(self))
        return real_unlink(self, missing_ok=missing_ok)
    Path.unlink = win_unlink
    try:
        _t2_files(root, chb, sie, parent, pdm, EF)
    finally:
        Path.unlink = real_unlink


def _t2_files(root, chb, sie, parent, pdm, EF):
    for p, kind, notch, sz in ((chb, "chb", 60.0, [(600, 660)]), (sie, "siena", 50.0, [(900, 960)])):
        scratch = root / "scr"
        r = G.g2_job(("case", "set", str(p), kind, notch, sz, str(scratch)))
        ok = "error" not in r and all(k in r for k in ("q", "top", "short", "valid", "n", "events", "tp", "fp",
                                                        "n_ref", "vmhwm_mb", "shas"))
        check(f"T2 g2_job {kind}: no error, every field", ok, r.get("error", "")[-300:] if not ok else
              f"{r['events']} events, tp {r['tp']}, fp {r['fp']}, n_ref {r['n_ref']}, {r['s']} s")
        if not ok:
            continue
        check(f"T2 g2_job {kind}: scratch cache removed, shas = parent", not any((scratch / "case").glob("*/*"))
              and r["shas"] == parent)
        cache = root / f"pa_{kind}"
        pa = pdm.process_file_phase_a(str(p), None, cache, mains=notch)
        res = EF.run_file(np.load(pa.filtered_path, mmap_mode="r"), np.load(pa.flag_path), np.load(pa.fsamp_path))
        check(f"T2 g2_job {kind}: events / q / top = engine_file on the application's Phase A caches",
              len(res["events"]) == r["events"] and res["q"] == r["q"] and res["top"] == r["top"]
              and r["n_ref"] == 1, f"{len(res['events'])} events")


def t3():
    class Ref:
        pass
    ref = Ref()
    row = dict(short=False, n=900, valid=900, events=3, tp=1, fp=2, n_ref=1, q=4.123456789, top=0.01)
    for k, v in row.items():
        setattr(ref, k, v)
    check("T3 equal row -> no difference", G.compare(row, ref) == [])
    check("T3 q off by 1e-6 relative -> 'q'", G.compare({**row, "q": row["q"] * (1 + 1e-6)}, ref) == ["q"])
    check("T3 one more false alarm -> 'fp'", G.compare({**row, "fp": 3}, ref) == ["fp"])
    ref.q, ref.short = float("nan"), True
    check("T3 NaN q both sides (short) -> equal", G.compare({**row, "q": float("nan"), "short": True}, ref) == [])


def t4(root):
    import pandas as pd
    class Ref:
        pass
    ref = Ref()
    for k, v in dict(short=False, n=900, valid=900, events=3, tp=1, fp=2, n_ref=1, q=4.0, top=0.01).items():
        setattr(ref, k, v)
    rows = [dict(subject="chb95", file="chb95_01.edf", short=False, n=900, valid=900, events=3, tp=1, fp=3, n_ref=1,
                 q=4.0, top=0.01)]
    G.R1.OUT_ROOT = root / "o4"
    G.R1.STATE["tag"] = "t4"
    try:
        G.gate_g2(rows, {("chb95", "chb95_01.edf"): ref}, "t4", G.R1.out_dir())
        stopped = False
    except SystemExit:
        stopped = True
    g = pd.read_csv(G.R1.out_dir() / "g2.csv")
    check("T4 FAIL stops after g2.csv is written", stopped and len(g) == 1 and g.differ[0] == "fp")


def main():
    root = Path(tempfile.mkdtemp(prefix="c5g2t_"))
    try:
        t1()
        t2(root)
        t3()
        t4(root)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    bad = [r for r in RES if not r[1]]
    print(f"\n{'ALL PASS' if not bad else f'{len(bad)} FAIL'} ({len(RES)} checks)")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
