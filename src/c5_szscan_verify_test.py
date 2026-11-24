#!/usr/bin/env python
"""
c5_szscan_verify_test.py -- synthetic test of src/c5_szscan_verify.py (chat C5, Step 1).

A synthetic world in a temporary folder: CHB-MIT-like bipolar EDF files written byte by byte (23 signals in a
non-thesis order, a duplicated T8-P8, a dummy channel, a partial last window, a 60-Hz line and a high-amplitude
stretch), cached by the APPLICATION'S OWN Phase A (`pipeline_demo.process_file_phase_a`), a temporary database written by
the application's own `db.create_subject_with_files`, a PhysioNet-style checksum file, a summary with an hour >= 24 and a
committed-style export. Then:
  T0  every check PASS on the clean world (V1-V6), the UI formatter run with node;
  F1-F8 one fault each -> the matching check FAILS (and only the checks that should);
  T9  STOP when the database holds a subject id that is not chbNN;
  T10 the independent reader reports a truncated file (records in the header > records in the file);
  T11 V7 on the synthetic chb01 files (real FastAPI app, temporary state, Phase B with the real GAE checkpoint).
Run: PYTHONUTF8=1 python src/c5_szscan_verify_test.py   (prints ALL PASS or the failing items; exit code 1 on failure)
"""
import csv
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import c5_szscan_verify as V                      # noqa: E402

V.import_backend()
import db                                         # noqa: E402
import pipeline_demo as pdm                       # noqa: E402
import waveform_serving as ws                     # noqa: E402

CHB_ORDER = ["-", "FP1-F7", "F7-T7", "T7-P7", "P7-O1", "FP1-F3", "F3-C3", "C3-P3", "P3-O1", "FP2-F4", "F4-C4",
             "C4-P4", "P4-O2", "FP2-F8", "F8-T8", "T8-P8", "P8-O2", "CZ-PZ", "FZ-CZ", "P7-T7", "T7-FT9", "FT10-T8",
             "T8-P8"]                             # FZ-CZ / CZ-PZ swapped on purpose; T8-P8 twice; a dummy channel
RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))
    print(f"{'PASS' if cond else 'FAIL'}  {name}  {detail}", flush=True)


def synth(seconds, seed, fs=256, n=len(CHB_ORDER), dup_equal=True):
    rng = np.random.default_rng(seed)
    t = np.arange(int(seconds * fs)) / fs
    x = rng.normal(0, 40, (n, len(t))) + 15 * np.sin(2 * np.pi * 60 * t)[None]
    x[:, int(200 * fs):int(230 * fs)] *= 6               # a high-amplitude stretch
    if dup_equal:
        x[CHB_ORDER.index("T8-P8", 16)] = x[CHB_ORDER.index("T8-P8")]
    x[0] = 0.0                                           # dummy channel
    return x


def build_world(root):
    ds, up = root / "dataset", root / "uploads"
    (ds / "chb03").mkdir(parents=True); (ds / "chb01").mkdir(parents=True); (up / "chb03").mkdir(parents=True)
    V.write_edf(ds / "chb03" / "chb03_01.edf", CHB_ORDER, 256, synth(20 * 60 + 2.5, 1), starttime="12.00.00")
    V.write_edf(ds / "chb03" / "chb03_02.edf", CHB_ORDER, 256, synth(15 * 60, 2), starttime="01.10.00")
    for name, seed in (("chb01_01.edf", 3), ("chb01_03.edf", 4)):
        V.write_edf(ds / "chb01" / name, CHB_ORDER, 256, synth(10 * 60, seed), starttime="09.00.00")
    (ds / "chb03" / "chb03-summary.txt").write_text(
        "Data Sampling Rate: 256 Hz\n\nFile Name: chb03_01.edf\nFile Start Time: 12:00:00\nFile End Time: 12:20:02\n"
        "Number of Seizures in File: 0\n\nFile Name: chb03_02.edf\nFile Start Time: 25:10:00\nFile End Time: 25:25:00\n"
        "Number of Seizures in File: 1\nSeizure Start Time: 1 seconds\nSeizure End Time: 2 seconds\n")
    sums = root / "SHA256SUMS.txt"
    sums.write_text("".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.parent.name}/{p.name}\n"
                            for p in sorted(ds.rglob("*.edf"))))
    db.DB_PATH = root / "szscan.db"
    db.init_db()
    files, ev = [], {}
    events = {"chb03_01.edf": [(100.0, 160.0)], "chb03_02.edf": [(400.0, 500.0), (800.0, 820.0)]}
    for name in ("chb03_01.edf", "chb03_02.edf"):
        shutil.copy(ds / "chb03" / name, up / "chb03" / name)
        pa = pdm.process_file_phase_a(str(up / "chb03" / name), None, up / "chb03")
        np.save(up / "chb03" / f"{Path(name).stem}.score.npy", np.zeros(pa.n_windows))
        files.append(dict(filename=name, start_time=pa.start_time.isoformat(), duration_seconds=pa.file_duration_seconds))
        ev[name] = [dict(onset_sec=a, offset_sec=b) for a, b in events[name]]
    db.create_subject_with_files("chb03", "", files, ev)
    t2 = root / "tier2"; t2.mkdir()
    with open(t2 / "chb03_events.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["subject", "file_name", "event_id", "onset_s", "offset_s", "source", "review_status"])
        k = 1
        for name, evs in events.items():
            for a, b in evs:
                w.writerow(["chb03", name, k, a, b, "AI", "Unseen"]); k += 1
    with open(t2 / "files.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["subject", "file_name", "duration_s", "n_windows", "status"])
        for f in files:
            w.writerow(["chb03", f["filename"], f["duration_seconds"], 0, "done"])
    return ds, up, sums, t2


def run(root, ds, up, sums, t2, tag, extra=()):
    out = root / f"out_{tag}"
    if out.exists():
        shutil.rmtree(out)
    g = V.main(["--dataset", str(ds), "--db", str(db.DB_PATH), "--uploads", str(up), "--sums", str(sums),
                "--tier2", str(t2), "--out", str(out), "--skip-v7", *extra])
    return {k: v.get("PASS") for k, v in g.items() if isinstance(v, dict) and "PASS" in v}


def sql(q, args=()):
    con = db.get_connection(); con.execute(q, args); con.commit(); con.close()


def main():
    root = Path(tempfile.mkdtemp(prefix="c5_test_"))
    try:
        ds, up, sums, t2 = build_world(root)
        g = run(root, ds, up, sums, t2, "clean")
        check("T0 clean world: V1-V6 PASS", all(g[k] for k in ("V1", "V2", "V3", "V4", "V5", "V6")), str(g))
        rep = (root / "out_clean" / "VERIFY.md").read_text(encoding="utf-8")
        check("T0 duplicate T8-P8 reported", "['T8-P8']" in rep)
        check("T0 UI formatter ran (node) incl. summary hour 25", json.loads(
            (root / "out_clean" / "gates.json").read_text())["V4_ui"]["cases"] == 6)
        rows = list(csv.DictReader(open(root / "out_clean" / "per_file.csv", encoding="utf-8")))
        check("T0 dropped tail of chb03_01 = 2 s (2.5 s of signal, records of 1 s)",
              float(rows[0]["dropped_tail_s"]) == 2.0, rows[0]["dropped_tail_s"])

        def expect(tag, g, failing):
            others = {k for k in ("V1", "V2", "V3", "V4", "V5", "V6")} - set(failing)
            check(f"{tag}: {'/'.join(failing)} FAIL, others PASS",
                  all(g[k] is False for k in failing) and all(g[k] for k in others), str(g))

        # F1 one byte of the app's EDF copy
        p = up / "chb03" / "chb03_01.edf"; b = bytearray(p.read_bytes()); b[5000] ^= 1; p.write_bytes(bytes(b))
        expect("F1 flipped byte in the app's EDF copy", run(root, ds, up, sums, t2, "f1"), ["V1"])
        shutil.copy(ds / "chb03" / "chb03_01.edf", p)
        # F2 two cached channels swapped (raw and filtered)
        for key in ("raw", "filtered"):
            q = up / "chb03" / f"chb03_02.{key}.npy"; a = np.load(q); keep = a.copy()
            a[:, [0, 1]] = a[:, [1, 0]]; np.save(q, a)
            if key == "raw":
                keep_raw = keep
            else:
                keep_flt = keep
        g = run(root, ds, up, sums, t2, "f2")
        check("F2 swapped channels: V1 and V2 FAIL", g["V1"] is False and g["V2"] is False, str(g))
        chans = list(csv.DictReader(open(root / "out_f2" / "channels.csv", encoding="utf-8")))
        m = [c for c in chans if c["file"] == "chb03_02.edf" and c["channel"] == "FP1-F7"][0]
        check("F2 diagnostic names the label the cache holds", m["cache_matches_label"].startswith("F7-T7"),
              m["cache_matches_label"])
        np.save(up / "chb03" / "chb03_02.raw.npy", keep_raw); np.save(up / "chb03" / "chb03_02.filtered.npy", keep_flt)
        # F3 endpoint returning volts-like (z-scored scale) values
        orig = ws.get_waveform
        def bad(*a, **k):
            w = orig(*a, **k)
            w["raw_uv"] = (np.asarray(w["raw_uv"]) / 40.0).round(2).tolist()
            return w
        ws.get_waveform = bad
        expect("F3 endpoint not in µV", run(root, ds, up, sums, t2, "f3"), ["V3"])
        ws.get_waveform = orig
        # F4 start time shifted by one hour in the database
        con = db.get_connection(); st = con.execute("SELECT start_time FROM files WHERE filename='chb03_01.edf'").fetchone()[0]; con.close()
        sql("UPDATE files SET start_time=? WHERE filename='chb03_01.edf'", (st.replace("T12:", "T13:"),))
        expect("F4 start time shifted", run(root, ds, up, sums, t2, "f4"), ["V4"])
        sql("UPDATE files SET start_time=? WHERE filename='chb03_01.edf'", (st,))
        # F5 event beyond the end of its file (and V6 differs as well)
        sql("UPDATE events SET offset_sec=5000 WHERE onset_sec=800")
        expect("F5 event outside its file", run(root, ds, up, sums, t2, "f5"), ["V4", "V6"])
        sql("UPDATE events SET offset_sec=820 WHERE onset_sec=800")
        # F6 filtered cache computed with a 50-Hz notch
        q = up / "chb03" / "chb03_01.filtered.npy"; keep = np.load(q)
        h = V.edf_header(ds / "chb03" / "chb03_01.edf"); lab = V.label_index(h)
        alt = keep.copy()
        for c, ch in enumerate(V.THESIS_CHANNELS):
            x = V.indep_filter(V.edf_signal_volts(ds / "chb03" / "chb03_01.edf", h, lab[ch][0]), 50.0)
            alt[:, c, :] = x[:keep.shape[0] * 1024].reshape(-1, 1024).astype(np.float32)
        np.save(q, alt)
        g = run(root, ds, up, sums, t2, "f6")
        check("F6 50-Hz notch in the cache: V5 FAIL (V3 filtered envelope too)", g["V5"] is False and g["V1"] and g["V6"], str(g))
        np.save(q, keep)
        # F7 UI label that does not match the code
        fe = root / "fe"; shutil.copytree(V.FRONTEND, fe)
        s = (fe / "screens" / "AnalysisScreen.jsx").read_text(encoding="utf-8")
        (fe / "screens" / "AnalysisScreen.jsx").write_text(s.replace("0.5-60 Hz + 60 Hz notch", "0.5-70 Hz + 50 Hz notch"),
                                                          encoding="utf-8")
        V.FRONTEND = fe
        expect("F7 UI filter label differs from the code", run(root, ds, up, sums, t2, "f7"), ["V5"])
        V.FRONTEND = ROOT / "web_demo" / "frontend" / "src"
        # F8 an AI event moved (V6 only)
        sql("UPDATE events SET onset_sec=101 WHERE onset_sec=100")
        expect("F8 event differs from the committed export", run(root, ds, up, sums, t2, "f8"), ["V6"])
        sql("UPDATE events SET onset_sec=100 WHERE onset_sec=101")
        # F9 summary start time disagrees with the header
        sp = ds / "chb03" / "chb03-summary.txt"; ss = sp.read_text()
        sp.write_text(ss.replace("File Start Time: 12:00:00", "File Start Time: 12:00:05"))
        expect("F9 summary start differs from the header", run(root, ds, up, sums, t2, "f9"), ["V4"])
        sp.write_text(ss)
        # T9 STOP on a non-chbNN subject
        sql("INSERT INTO subjects (id, memo) VALUES ('clin01', '')")
        try:
            run(root, ds, up, sums, t2, "t9"); check("T9 STOP on a non-CHB-MIT subject id", False)
        except SystemExit as e:
            check("T9 STOP on a non-CHB-MIT subject id", "not chbNN" in str(e))
        sql("DELETE FROM subjects WHERE id='clin01'")
        # T10 truncated file seen by the independent reader
        tp = root / "trunc.edf"; bb = (ds / "chb01" / "chb01_01.edf").read_bytes(); h = V.edf_header(ds / "chb01" / "chb01_01.edf")
        tp.write_bytes(bb[:h["hdr_bytes"] + (len(bb) - h["hdr_bytes"]) // 2])
        ht = V.edf_header(tp)
        check("T10 truncated file: records in header > records in file", ht["n_rec_hdr"] == 600 and ht["n_rec_file"] == 300,
              f"{ht['n_rec_hdr']} / {ht['n_rec_file']}")
        # T11 V7 on synthetic chb01 files
        out7 = root / "out_v7"; out7.mkdir()
        real_db = db.DB_PATH
        rows7 = V.run_v7(ds, out7, phase_b_timeout_s=900)
        check("T11 V7 leaves the database path as it was", db.DB_PATH == real_db)
        obs = {r["case"]: r for r in rows7}
        for cid in ("U1", "U2", "U3", "U4", "U5", "U6", "U7", "U9"):
            check(f"T11 V7 {cid} as expected", obs[cid]["as_expected"] == "yes", obs[cid]["observed"])
        check("T11 V7 U8 and U10 observed", bool(obs["U8"]["observed"]) and "MB" in obs["U10"]["observed"],
              obs["U8"]["observed"] + " | " + obs["U10"]["observed"])
    finally:
        shutil.rmtree(root, ignore_errors=True)
    bad = [r for r in RESULTS if not r[1]]
    print(f"\n{'ALL PASS' if not bad else f'{len(bad)} FAIL'} ({len(RESULTS)} checks)")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
