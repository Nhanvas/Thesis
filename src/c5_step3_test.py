#!/usr/bin/env python
"""
c5_step3_test.py -- chat C5c, Step 3: synthetic test of c5_step3_clips.py and c5_step3_report.py before any real use.
A temporary database in the application's schema (the columns the scripts read) and upload caches with planted events,
seizures, scores and signal loss, whose correct selection is known by hand from PROTOCOL_STEP3.md §3:
  T1 version 24: hospital 5 highest + 5 random + 6 controls (5 in the 80-min, 1 in the 15-min recording: 6 x 15 / 95
     rounds to 1), anchors =
     Siena found PN93, PN91 (durations 70 / 60 s nearest the median 70), missed PN94, false alarm PN92; CHB-MIT found
     chb03 (tie with chb13 -> smaller id), missed chb06, false alarms chb13 (score 9) and chb14 (7) -- one per patient
  T2 the 5 highest are the 5 highest-score events; the event inside signal loss is never chosen; random ones from the rest
  T3 controls >= 5 min from every event, not in the first or last minute, no signal loss, no two overlapping
  T4 every clip image's signal = the filtered cache x 1e6 at the key's start (60 s, 18 derivations), exactly
  T5 same seed -> the same key; a non-empty output folder is refused
  T6 the review page and the key hold no planted name (the database's notice text) and no hospital time of day
  T7 version 18: 4 + 3 + 5 hospital, anchors one per category and dataset
  T9 Windows emulation: time.mktime refuses dates before 1970 during the whole test; no test file is still
     memory-mapped when the scripts have returned (Windows cannot delete a mapped file)
  T8 report: complete answers -> REVIEW.md counts add up to the clips, no hospital file name in it; one missing answer
     -> STOP
Run: PYTHONUTF8=1 python src/c5_step3_test.py
"""
import csv
import gc
import re
import shutil
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import c5_step3_clips as C           # noqa: E402
import c5_step3_report as R          # noqa: E402

RES = []


def check(name, ok, detail=""):
    RES.append((name, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}", flush=True)


def build(root):
    up, db = root / "uploads", root / "app.db"
    con = sqlite3.connect(db)
    con.executescript("""CREATE TABLE subjects (id TEXT PRIMARY KEY, mode TEXT, mains_hz REAL, private INTEGER);
CREATE TABLE files (id INTEGER PRIMARY KEY, subject_id TEXT, filename TEXT, duration_seconds REAL, notice TEXT);
CREATE TABLE events (id INTEGER PRIMARY KEY, file_id INTEGER, source TEXT, onset_sec REAL, offset_sec REAL);""")
    rng = np.random.default_rng(5)
    truth = {}

    def rec(sid, fn, minutes, private, mains, events, loss=(), notice=""):
        n = int(minutes * 60 / 4)
        d = up / sid
        d.mkdir(parents=True, exist_ok=True)
        flt = rng.normal(0, 2e-5, (n, 18, 1024)).astype(np.float32)
        raw = rng.normal(0, 2e-5, (n, 18, 1024)).astype(np.float32)
        for w in loss:
            raw[w] = 0.0
        score = rng.uniform(0, 1, n).astype(np.float32)
        for (a, b, pk) in events:
            score[int(a // 4)] = pk
        stem = Path(fn).stem
        np.save(d / f"{stem}.filtered.npy", flt)
        np.save(d / f"{stem}.raw.npy", raw)
        np.save(d / f"{stem}.score.npy", score)
        if not con.execute("SELECT 1 FROM subjects WHERE id = ?", (sid,)).fetchone():
            con.execute("INSERT INTO subjects VALUES (?, 'session', ?, ?)", (sid, mains, private))
        cur = con.execute("INSERT INTO files (subject_id, filename, duration_seconds, notice) VALUES (?, ?, ?, ?)",
                          (sid, fn, n * 4.0, notice))
        for (a, b, pk) in events:
            con.execute("INSERT INTO events (file_id, source, onset_sec, offset_sec) VALUES (?, 'AI', ?, ?)",
                        (cur.lastrowid, a, b))
        truth[(sid, fn)] = dict(flt=d / f"{stem}.filtered.npy", events=events, loss=set(loss), dur=n * 4.0)
    ev1 = [(100.0 + 200 * k, 140.0 + 200 * k, 2.0 + k) for k in range(12)]       # peaks 2 ... 13
    rec("clin01", "rec01.edf", 80, 1, 50.0, ev1)
    rec("clin02", "rec01.edf", 15, 1, 50.0, [(400.0, 440.0, 99.0)], loss=range(95, 115),
        notice="Electrode(s) C3 looked disconnected or flat and were interpolated. Nguyen Van A")
    chb = root / "chb"
    for sid, ev in (("chb03", [(300.0, 350.0, 3.0)]), ("chb06", [(600.0, 640.0, 5.0)]),
                    ("chb13", [(300.0, 350.0, 3.0), (100.0, 130.0, 9.0)]), ("chb14", [(500.0, 540.0, 7.0)])):
        rec(sid, f"{sid}_01.edf", 15, 0, 60.0, ev)
        (chb / sid).mkdir(parents=True)
        (chb / sid / f"{sid}-summary.txt").write_text(
            f"File Name: {sid}_01.edf\nNumber of Seizures in File: 1\nSeizure 1 Start Time: 300 seconds\n"
            "Seizure 1 End Time: 360 seconds\n\n", encoding="utf-8")
    sie = root / "siena"
    for sid, (a, b), ev in (("PN91", (300, 360), [(300.0, 350.0, 3.0)]), ("PN92", (300, 400), [(300.0, 380.0, 3.0),
                            (700.0, 740.0, 8.0)]), ("PN93", (300, 370), [(310.0, 360.0, 3.0)]), ("PN94", (300, 360), [])):
        rec(sid, f"{sid}-1.edf", 15, 0, 50.0, ev)
        (sie / sid).mkdir(parents=True)
        (sie / sid / f"{sid}-1.edf").touch()
        hh = lambda s: f"{10 + s // 3600:02d}.{(s % 3600) // 60:02d}.{s % 60:02d}"  # noqa: E731
        (sie / sid / f"Seizures-list-{sid}.txt").write_text(
            f"Seizure n 1\nFile name: {sid}-1.edf\nRegistration start time: 10.00.00\nRegistration end time: 10.15.00\n"
            f"Seizure start time: {hh(a)}\nSeizure end time: {hh(b)}\n\n", encoding="utf-8")
    con.commit()
    con.close()
    return db, up, chb, sie, truth


def run(db, up, chb, sie, out, version=24, seed=C.SEED):
    return C.main(["--chb", str(chb), "--siena", str(sie), "--db", str(db), "--uploads", str(up), "--out", str(out),
                   "--version", str(version), "--seed", str(seed)])


def key(out):
    with open(out / "key.csv", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def win_mktime(real):
    """time.mktime as on Windows: dates before 1970 raise (the Siena parser met this on the laptop, C5c2)."""
    def f(tt):
        if tt[0] < 1970:
            raise OverflowError("mktime argument out of range (Windows emulation)")
        return real(tt)
    return f


def mapped_under(root):
    """files under root still memory-mapped by this process (Linux /proc; Windows would refuse to delete them)."""
    maps = Path("/proc/self/maps")
    if not maps.exists():
        return []
    r = str(Path(root).resolve())
    return sorted({ln.split(None, 5)[5] for ln in maps.read_text(encoding="utf-8").splitlines()
                   if len(ln.split(None, 5)) == 6 and ln.split(None, 5)[5].startswith(r)})


def body(root):
    db, up, chb, sie, truth = build(root)
    out = root / "out24"
    run(db, up, chb, sie, out)
    k = key(out)
    hs = [r for r in k if r["source"] == "hospital"]
    an = {(r["dataset"], r["set"], r["study"]) for r in k if r["source"] == "anchor"}
    cnt = {s: sum(r["set"] == s for r in hs) for s in ("flagged, highest score", "flagged, random", "control")}
    ctl = {s: sum(r["set"] == "control" and r["study"] == s for r in hs) for s in ("clin01", "clin02")}
    check("T1 version 24: 5 + 5 + 6 hospital (controls 5 + 1), 24 clips",
          list(cnt.values()) == [5, 5, 6] and ctl == {"clin01": 5, "clin02": 1} and len(k) == 24, f"{cnt} {ctl}")
    want = {("Siena", "seizure found", "PN93"), ("Siena", "seizure found", "PN91"), ("Siena", "seizure missed", "PN94"),
            ("Siena", "false alarm", "PN92"), ("CHB-MIT", "seizure found", "chb03"),
            ("CHB-MIT", "seizure missed", "chb06"), ("CHB-MIT", "false alarm", "chb13"),
            ("CHB-MIT", "false alarm", "chb14")}
    check("T1 anchors = the hand-derived selection (median duration, highest score, one per patient)", an == want,
          str(sorted(an ^ want)))
    top = sorted(float(r["peak_score"]) for r in hs if r["set"] == "flagged, highest score")
    rnd = [r for r in hs if r["set"] == "flagged, random"]
    check("T2 the 5 highest = peaks 9 ... 13; the event in signal loss (peak 99) never chosen; random from the rest",
          top == [9.0, 10.0, 11.0, 12.0, 13.0] and all(float(r["peak_score"]) < 9 for r in rnd)
          and not any(float(r["peak_score"]) == 99.0 for r in hs), str(top))
    ok = True
    for r in hs:
        if r["set"] != "control":
            continue
        t = truth[(r["study"], r["file"])]
        s = float(r["clip_start_s"])
        ok &= all(s >= b + 300 or s + 60 <= a - 300 for a, b, _ in t["events"])
        ok &= 60 <= s and s + 60 <= t["dur"] - 60
        ok &= not any(w in t["loss"] for w in range(int(s // 4), int(np.ceil((s + 60) / 4))))
    starts = sorted((r["study"], float(r["clip_start_s"])) for r in hs if r["set"] == "control")
    ok &= all(not (a[0] == b[0] and b[1] - a[1] < 60) for a, b in zip(starts, starts[1:]))
    check("T3 controls >= 5 min from events, not first / last minute, no signal loss, not overlapping", ok)
    bad = []
    for r in k:
        t = truth[(r["study"], r["file"])]
        flt = np.load(t["flt"])
        x = flt.transpose(1, 0, 2).reshape(18, -1).astype(np.float64)
        a = int(round(float(r["clip_start_s"]) * 256))
        rec = C.Rec(dict(id=0, subject_id=r["study"], filename=r["file"], duration_seconds=t["dur"], notice=""),
                    dict(mains_hz=50.0), up)
        if not np.array_equal(rec.signal(float(r["clip_start_s"])), x[:, a:a + 15360] * 1e6):
            bad.append(r["clip"])
    check("T4 clip signal = filtered cache x 1e6 at the key's start (every clip)", not bad, str(bad))
    out2 = root / "out24b"
    run(db, up, chb, sie, out2)
    same = key(out2) == k
    try:
        run(db, up, chb, sie, out)
        refused = False
    except SystemExit:
        refused = True
    check("T5 same seed -> same key; non-empty output refused", same and refused)
    html = (out / "review.html").read_text(encoding="utf-8")
    kt = (out / "key.csv").read_text(encoding="utf-8")
    check("T6 no planted name, no notice text, no time of day in the page or the key",
          "Nguyen" not in html + kt and "disconnected" not in html + kt and "10.00.00" not in html
          and "C3 được nội suy" in html)
    out18 = root / "out18"
    run(db, up, chb, sie, out18, version=18)
    k18 = key(out18)
    h18 = [sum(r["source"] == "hospital" and r["set"] == s for r in k18)
           for s in ("flagged, highest score", "flagged, random", "control")]
    a18 = sorted((r["dataset"], r["set"]) for r in k18 if r["source"] == "anchor")
    check("T7 version 18: 4 + 3 + 5 hospital, one anchor per category and dataset",
          h18 == [4, 3, 5] and len(a18) == 6 and len(set(a18)) == 6, f"{h18} {a18}")
    ans = root / "answers.csv"
    classes = ["Nền bình thường", "Nhiễu: cơ", "Cơn động kinh (dạng ictal)"]
    with open(ans, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["clip", "class", "confidence", "show_me", "seconds", "gain_halved", "comment"])
        for i, r in enumerate(k):
            w.writerow([r["clip"], classes[i % 3], 1 + i % 5, ["yes", "no", "unsure"][i % 3], 20 + i, "no", ""])
    pub = root / "pub"
    R.main(["--private", str(out), "--answers", str(ans), "--public", str(pub)])
    md = (pub / "REVIEW.md").read_text(encoding="utf-8")
    row = [ln for ln in md.splitlines() if ln.startswith("| **clips**")][0]
    n_h = sum(int(x) for x in row.strip("| ").split(" | ")[1:])
    check("T8 report: hospital counts add up (16), anchors listed (8), no hospital file name",
          n_h == 16 and sum(bool(re.match(r"\| C\d\d \|", ln)) for ln in md.splitlines()) == 8 and "rec01" not in md, row)
    rows = list(csv.reader(open(ans, encoding="utf-8-sig")))
    rows[3][1] = ""
    with open(ans, "w", newline="", encoding="utf-8-sig") as fh:
        csv.writer(fh).writerows(rows)
    try:
        R.main(["--private", str(out), "--answers", str(ans), "--public", str(root / "pub2")])
        stopped = False
    except SystemExit:
        stopped = True
    check("T8 a clip without a class -> STOP", stopped)


def main():
    root = Path(tempfile.mkdtemp(prefix="c5s3t_"))
    real = time.mktime
    time.mktime = win_mktime(real)
    try:
        body(root)
    finally:
        time.mktime = real
    gc.collect()
    left = mapped_under(root)
    check("T9 Windows emulation: no file of the test still memory-mapped after the scripts return; "
          "dates before 1970 refused by mktime throughout", not left, str(left[:3]))
    shutil.rmtree(root, ignore_errors=True)
    bad = [r for r in RES if not r[1]]
    print(f"\n{'ALL PASS' if not bad else f'{len(bad)} FAIL'} ({len(RES)} checks)")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
