#!/usr/bin/env python
"""
c5_step2b_test.py -- chat C5c, Step 2b: synthetic and replay tests of the new offline tools, run before any real use.

  B1 c5_score_app replays the committed application-tier export of the 8 test subjects (web_demo/report_handback/
     tier2_v4: every file, every AI event) through a temporary database in the application's schema and the committed
     CHB-MIT summaries (data/summaries; preprocessing.parse_summary): per-subject seizures,
     detected and false alarms = results/application_eval_v4/per_subject.csv exactly (gate S0 PASS).
  B2 a private study in the database is skipped (counted, never scored, never named in the output).
  B3 a suffixed id (chb03-file) is scored with chb03's annotation and its own mode; S0 reads only the session-mode
     test subjects.
  B4 Siena annotation path: a Seizures-list file in the standard format -> the planted seizure; an event on it = 1 TP,
     an event elsewhere = 1 FP.
  B5 an event running past its file's end is split onto the next file (application-tier rule) and counted once.
  B4c Siena clock (C5c, after the laptop's Windows failure, 26/11): every branch of SzCORE's Siena parser (standard,
     day shift, the PN12-type entry, PN01, PN00-3, PN10-7.8.9) gives the same seizures through siena_clock as through
     the original on this machine; with time.mktime refusing dates before 1970 (Windows) the original fails and
     siena_clock still gives them; the original function is restored afterwards.
  B1 also checks gate S1 (reference seizures per file = F2-03's L3 rows) on the replayed test files.
  B6 c5_verify2 (G9) on synthetic studies in a temporary database and upload cache built by the application's own
     code (bipolar CHB-like 256 Hz; referential Siena-like 512 Hz with a 50-Hz study; referential EDF+ hospital-like
     private study): V1, V2, V3, V5 PASS; a planted error in a cached channel and a swapped channel are caught;
     the private study appears only as counts in the private report; peak traced memory per file bounded.

Run: PYTHONUTF8=1 python src/c5_step2b_test.py
"""
import csv
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src", ROOT / "src" / "dataprep", ROOT / "web_demo" / "backend"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import c5_score_app as SA      # noqa: E402

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}", flush=True)


SCHEMA = """
CREATE TABLE subjects (id TEXT PRIMARY KEY, mode TEXT, mains_hz REAL, private INTEGER);
CREATE TABLE files (id INTEGER PRIMARY KEY, subject_id TEXT, filename TEXT, duration_seconds REAL);
CREATE TABLE events (id INTEGER PRIMARY KEY, file_id INTEGER, source TEXT, onset_sec REAL, offset_sec REAL,
                     review_status TEXT);
"""


class TmpDB:
    def __init__(self, path, uploads):
        self.con = sqlite3.connect(path)
        self.con.executescript(SCHEMA)
        self.up = uploads

    def subject(self, sid, mode="session", private=0):
        self.con.execute("INSERT INTO subjects VALUES (?, ?, 60.0, ?)", (sid, mode, private))

    def file(self, sid, fn, dur, n_win):
        cur = self.con.execute("INSERT INTO files (subject_id, filename, duration_seconds) VALUES (?, ?, ?)",
                               (sid, fn, dur))
        (self.up / sid).mkdir(parents=True, exist_ok=True)
        np.save(self.up / sid / f"{Path(fn).stem}.score.npy", np.zeros(n_win, np.float32))
        return cur.lastrowid

    def event(self, fid, a, b, src="AI", st="Unseen"):
        self.con.execute("INSERT INTO events (file_id, source, onset_sec, offset_sec, review_status) "
                         "VALUES (?, ?, ?, ?, ?)", (fid, src, a, b, st))

    def close(self):
        self.con.commit()
        self.con.close()


def b1_b3(root):
    t2 = ROOT / "web_demo" / "report_handback" / "tier2_v4"
    chb = root / "chb"
    for s in SA.TEST:
        d = chb / s
        d.mkdir(parents=True)
        shutil.copy(ROOT / "data" / "summaries" / f"{s}-summary.txt", d)
    fl = pd.read_csv(t2 / "files.csv")
    up = root / "uploads"
    db = TmpDB(root / "t.db", up)
    ids = {}
    for sid in list(SA.TEST) + ["chb03-file"]:
        base = sid.split("-")[0]
        db.subject(sid, "file" if sid.endswith("-file") else "session")
        for r in fl[fl["subject"] == base].itertuples():
            ids[(sid, r.file_name)] = db.file(sid, r.file_name, r.duration_s, r.n_windows)
    for s in SA.TEST:
        ev = pd.read_csv(t2 / f"{s}_events.csv")
        for r in ev.itertuples():
            db.event(ids[(s, r.file_name)], r.onset_s, r.offset_s, r.source, r.review_status)
    db.event(ids[("chb03-file", "chb03_01.edf")], 10.0, 70.0)    # one false alarm in the suffixed study
    db.subject("clin01", private=1)
    db.file("clin01", "rec01.edf", 3600.0, 900)
    db.close()
    out = root / "out_b1"
    g = SA.main(["--chb", str(chb), "--db", str(root / "t.db"), "--uploads", str(up), "--out", str(out)])
    check("B1 test subjects replayed = application_eval_v4 per subject (gate S0)", g["S0"]["PASS"] is True,
          str(g["S0"]))
    df = pd.read_csv(out / "per_subject.csv")
    ref = pd.read_csv(SA.REF_V4)
    tot = df[df["subject"].isin(SA.TEST)][["seizures", "detected", "false_alarms"]].sum()
    check("B1 totals 76 seizures / 33 detected (the application tier's 0.528 run)",
          (int(tot["seizures"]), int(tot["detected"])) == (76, int(ref["detected"].sum())) == (76, 33),
          f"{int(tot['detected'])} / {int(tot['seizures'])}")
    md = (out / "SUMMARY.md").read_text(encoding="utf-8")
    check("B1 gate S1: reference seizures per file = L3 rows (231 test files + chb03-file's 38)",
          g["S1"]["PASS"] is True and g["S1"]["files_compared"] == len(fl) + 38, str(g["S1"])[:120])
    check("B2 private study skipped, counted, never named", "clin01" not in md and "rec01" not in md
          and "Private studies skipped: 1" in md)
    r3 = df[df["subject"] == "chb03-file"].iloc[0]
    check("B3 suffixed id scored with chb03's annotation, own mode", r3["mode"] == "file" and r3["seizures"] == 7
          and r3["detected"] == 0 and r3["false_alarms"] == 1, f"{r3.to_dict()}")


def b4_b5(root):
    sie = root / "siena" / "PN99"
    sie.mkdir(parents=True)
    (sie / "Seizures-list-PN99.txt").write_text(
        "Seizure n 1\nFile name: PN99-1.edf\nRegistration start time: 10.00.00\nRegistration end time: 12.00.00\n"
        "Seizure start time: 10.30.00\nSeizure end time: 10.31.00\n\n")
    (sie / "PN99-1.edf").touch()                 # x1_external.siena_subject lists the EDF names
    (sie / "PN99-2.edf").touch()
    up = root / "up2"
    db = TmpDB(root / "s.db", up)
    db.subject("PN99")
    f1 = db.file("PN99", "PN99-1.edf", 7200.0, 1800)
    f2 = db.file("PN99", "PN99-2.edf", 3600.0, 900)
    db.event(f1, 1795.0, 1870.0)          # on the seizure (1800-1860 s)
    db.event(f1, 5000.0, 5060.0)          # false alarm
    db.event(f1, 7150.0, 7260.0)          # runs 60 s past the end of PN99-1 into PN99-2
    db.close()
    g = SA.main(["--siena", str(root / "siena"), "--db", str(root / "s.db"), "--uploads", str(up),
                 "--out", str(root / "out_b4")])
    r = pd.read_csv(root / "out_b4" / "per_subject.csv").iloc[0]
    check("B4 Siena annotation path: seizure found once, one false alarm elsewhere",
          (r["seizures"], r["detected"]) == (1, 1), f"{r.to_dict()}")
    check("B5 event crossing a file end split and counted (crossing 1; FP = 2 pieces scored per file)",
          r["events_crossing_files"] == 1 and r["false_alarms"] == 3 and g["S0"]["PASS"] is None,
          f"false alarms {r['false_alarms']}")


def b4c(root):
    import time as _t
    import x1_external as X1
    sl = root / "sl"
    lists = {
        "PN96": ("Seizure n 1\nFile name: PN96-1.edf\nRegistration start time: 23.50.00\nRegistration end time: 01.50.00\n"
                 "Seizure start time: 00.10.05\nSeizure end time: 00.11.07\n\n"
                 "Seizure n 2\nFile name: PN96-1.edf\nSeizure start time: 01.00.00\nSeizure end time: 01.01.30\n\n"
                 "Seizure n 3\nFile name: PN96-2.edf\nRegistration start time: 10:00:00\nRegistration end time: 11:00:00\n"
                 "Seizure start time: 10:20:00\nSeizure end time: 10:21:00\n\n", ["PN96-1.edf", "PN96-2.edf"]),
        "PN01": ("File name: PN01.edf\nRegistration start time: 19.00.44\nRegistration end time: 09.39.14\n\n"
                 "Seizure n 1\nStart time: 21.51.02\nEnd time: 21.51.56\n\nSeizure n 2\nStart time: 07.53.17\n"
                 "End time: 07.54.31\n\n", ["PN01-1.edf"]),
        "PN00": ("File name: PN00-3.edf\nRegistration start time: 18.15.44\nRegistration end time: 18.57.13\n"
                 "Seizure start time: 18.28.29\nSeizure end time: 18.29.29\n\n", ["PN00-3.edf"]),
        "PN10": ("File name: PN10-7.8.9.edf\nRegistration start time:1 6.49.25\nRegistration end time: 19.00.00\n"
                 "Seizure start time: 17.00.00\nSeizure end time: 17.01.00\n\n", ["PN10-7.8.9.edf"]),
    }
    for subj, (txt, edfs) in lists.items():
        (sl / subj).mkdir(parents=True)
        (sl / subj / f"Seizures-list-{subj}.txt").write_text(txt)
        for e in edfs:
            (sl / subj / e).touch()
    # Reference = the original parser run on Linux (sandbox, 26/11), hand-checked against the list texts above
    # (e.g. PN01: 19.00.44 -> 21.51.02 = 10,218 s; 07.53.17 the next day = 46,353 s; PN96 entry 2 uses entry 1's start).
    expected = {"PN96": [[(1205, 1267), (4200, 4290)], [(1200, 1260)]], "PN01": [[(10218, 10272), (46353, 46427)]],
                "PN00": [[(765, 825)]], "PN10": [[(635, 695)]]}
    seiz = lambda res: [[tuple(z) for z in sz] for _, sz in res]  # noqa: E731
    with SA.siena_clock(X1):
        new = {s_: seiz(X1.siena_subject(sl, s_)[0]) for s_ in lists}
    check("B4c every Siena parser branch through siena_clock = the original parser's output", new == expected, str(new))
    try:
        orig = {s_: seiz(X1.siena_subject(sl, s_)[0]) for s_ in lists}
        check("B4c the original parser works on this machine and agrees", orig == expected)
    except OverflowError:
        check("B4c the original parser refuses on this machine (Windows mktime before 1970) -- the reason for siena_clock",
              True)
    real_mk = _t.mktime

    def win_mktime(t):
        if t.tm_year < 1970:
            raise OverflowError("mktime argument out of range")
        return real_mk(t)
    _t.mktime = win_mktime
    try:
        try:
            X1.siena_subject(sl, "PN96")
            fails = False
        except OverflowError:
            fails = True
        with SA.siena_clock(X1):
            win = {s_: seiz(X1.siena_subject(sl, s_)[0]) for s_ in lists}
    finally:
        _t.mktime = real_mk
    check("B4c Windows-like mktime: original fails, siena_clock gives the same seizures; original restored",
          fails and win == expected and X1._parseTimeStamp.__name__ == "_parseTimeStamp")


def main():
    root = Path(tempfile.mkdtemp(prefix="c5s2b_"))
    try:
        b1_b3(root)
        b4c(root)
        b4_b5(root)
        try:
            import c5_verify2_test as VT
            VT.run(root, check)
        except ModuleNotFoundError as e:
            if e.name != "c5_verify2_test":
                raise
            print("B6 not run: c5_verify2_test not present")
    finally:
        shutil.rmtree(root, ignore_errors=True)
    bad = [r for r in RESULTS if not r[1]]
    print(f"\n{'ALL PASS' if not bad else f'{len(bad)} FAIL'} ({len(RESULTS)} checks)")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
