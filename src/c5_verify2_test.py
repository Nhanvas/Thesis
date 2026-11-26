"""
c5_verify2_test.py -- test B6 of src/c5_step2b_test.py (chat C5c): gate G9 (src/c5_verify2.py) on synthetic studies
created by the application's own ingest (batch_ingest.ingest) in a temporary database and upload folder:
  chb98  bipolar CHB-like, 256 Hz, 60-Hz study, session engine, two 20-min files
  PN98   referential Siena-like ("EEG Fp1" ...), 512 Hz, 50-Hz study, file engine, one 35-min and one 10-min file
  clin01 referential hospital-like EDF+ ("EEG T3-REF" ..., 30 other signals, annotation signal), 256 Hz, 50-Hz study,
         private, C3 x12 and interpolated
Expected: V1, V2, V3, V4 (no node -> formatter not run), V5 PASS on the public files; file mode: no event in the 10-min
file; the private study only in the inbox report, V1-V5 PASS on its 16 non-interpolated derivations; a +2-µV error
planted in one cached sample and two swapped cached channels are caught (V1 / V2 FAIL on that file only).
"""
import hashlib
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "web_demo" / "backend"
for _p in (str(BACKEND), str(ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def run(root, check):
    import c5_step2_test as T          # synthetic EDF writers (write_edf, write_edfplus, eeg, CHB23, REF19)
    import db
    import upload_manager as um
    import batch_ingest as BI
    import c5_verify2 as G
    real = (db.DB_PATH, um.UPLOAD_DIR, G.CHB_SUMS, G.SIENA_SUMS, G.INBOX)
    base = root / "b6"
    db.DB_PATH = base / "app.db"
    um.UPLOAD_DIR = base / "uploads"
    um.UPLOAD_DIR.mkdir(parents=True)
    G.INBOX = base / "inbox"
    try:
        db.init_db()
        chb, sie, hosp = base / "chb" / "chb98", base / "siena" / "PN98", base / "hosp"
        for d in (chb, sie, hosp):
            d.mkdir(parents=True)
        T.write_edf(chb / "chb98_01.edf", T.CHB23, 256, T.eeg(23, 1200, 256, 61, 60), starttime="10.00.00")
        T.write_edf(chb / "chb98_02.edf", T.CHB23, 256, T.eeg(23, 1200, 256, 62, 60), starttime="10.20.00")
        sl = [f"EEG {e.capitalize()}" for e in T.REF19] + ["EKG", "SPO2"]
        x = T.eeg(21, 35 * 60, 512, 63, 50)
        x[:19, 900 * 512:960 * 512] *= 5
        T.write_edfplus(sie / "PN98-1.edf", sl, [512] * 21, list(x), annot=False)
        T.write_edfplus(sie / "PN98-2.edf", sl, [512] * 21, list(T.eeg(21, 600, 512, 64, 50)), annot=False)
        hl = [f"EEG {e}-REF" for e in T.REF19] + [f"POL X{i}" for i in range(30)]
        xh = T.eeg(49, 1800, 256, 65, 50)
        xh[T.REF19.index("C3")] *= 12
        T.write_edfplus(hosp / "Nguyen Van A.edf", hl, [256] * 49, list(xh))
        sums = base / "sums.txt"
        sums.write_text("".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()} {p.parent.name}/{p.name}\n"
                                for p in list(chb.glob("*.edf")) + list(sie.glob("*.edf"))))
        G.CHB_SUMS = G.SIENA_SUMS = sums
        BI.ingest("chb98", edf_dir=chb, mode="session", mains="60")
        BI.ingest("PN98", edf_dir=sie, mode="file", mains="50")
        BI.ingest("clin01", edfs=[hosp / "Nguyen Van A.edf"], mode="session", mains="50", private=True,
                  interpolate=True)
        args = ["--chb", str(base / "chb"), "--siena", str(base / "siena"), "--db", str(db.DB_PATH),
                "--uploads", str(um.UPLOAD_DIR), "--out", str(base / "out"), "--private"]
        g = G.main(args)
        check("B6 G9 synthetic: V1, V2, V3, V4, V5 PASS (bipolar 256 Hz; referential 512 Hz, 50-Hz study)",
              all(g[k]["PASS"] for k in ("V1", "V2", "V3", "V4", "V5")), str({k: g[k]["PASS"] for k in g}))
        import csv
        rows = list(csv.DictReader(open(base / "out" / "per_file.csv", encoding="utf-8")))
        short = [r for r in rows if r["file"] == "PN98-2.edf"][0]
        check("B6 file mode: the 10-min file holds no event", short.get("short_file_no_event") == "True"
              and short["events_ai"] == "0")
        pub = (base / "out" / "VERIFY2.md").read_text(encoding="utf-8") + (base / "out" / "per_file.csv").read_text()
        priv = (G.INBOX / "C5_G9_PRIVATE.md").read_text(encoding="utf-8")
        check("B6 private study only in the inbox report; no name anywhere", "clin01" not in pub and "Nguyen" not in pub
              and "Nguyen" not in priv and "clin01" in priv)
        pr = [ln for ln in priv.splitlines() if ln.startswith("| clin01")][0].split("|")
        check("B6 private study: V1-V5 PASS, C3 interpolated and not compared",
              [c.strip() for c in pr[5:10]] == ["True"] * 5 and pr[10].strip() == "C3", "|".join(pr[5:11]))
        chans = list(csv.DictReader(open(base / "out" / "channels.csv", encoding="utf-8")))
        check("B6 every public channel compared (18 x 4 files)", sum(c["compared"] == "yes" for c in chans) == 72)
        # planted errors
        rp = um.UPLOAD_DIR / "chb98" / "chb98_01.raw.npy"
        r0 = np.load(rp)
        r1 = r0.copy(); r1[100, 5, 10] += 2e-6
        np.save(rp, r1)
        g1 = G.main(args[:-1] + ["--subjects", "chb98", "--out", str(base / "out1")])
        rows1 = {r["file"]: r for r in csv.DictReader(open(base / "out1" / "per_file.csv", encoding="utf-8"))}
        check("B6 planted 2-µV error caught (V1 FAIL on that file only)", g1["V1"]["PASS"] is False
              and rows1["chb98_01.edf"]["V1"] == "False" and rows1["chb98_02.edf"]["V1"] == "True",
              f"largest difference {float(rows1['chb98_01.edf']['V1_raw_max_abs_diff_uv']):.3f} µV")
        r2 = r0.copy(); r2[:, [3, 4]] = r2[:, [4, 3]]
        np.save(rp, r2)
        g2 = G.main(args[:-1] + ["--subjects", "chb98", "--out", str(base / "out2")])
        check("B6 swapped cached channels caught (V2 FAIL)", g2["V2"]["PASS"] is False)
        np.save(rp, r0)
    finally:
        db.DB_PATH, um.UPLOAD_DIR, G.CHB_SUMS, G.SIENA_SUMS, G.INBOX = real
        shutil.rmtree(base, ignore_errors=True)
