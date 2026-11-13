#!/usr/bin/env python
"""
fa1_readonly_test.py -- synthetic test of src/fa1_readonly.py (no real data). Builds a fake F:/Study/Thesis tree in a
temporary folder: two fake hospital EDF headers (protected patient names, file stems, start dates; one header truncated,
one 512 Hz signal set with T3/T5 aliases and C3 present), a Defense/ tree with figures, a drawing script, a selection
table, a notes file and a script that leak a protected name, and Defense/clinical/run/SUMMARY.md. Checks every path of
both parts, including the STOP paths of part B.

  python src/fa1_readonly_test.py        (seconds)
"""
import csv
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "fa1_readonly.py"
NAME1, NAME2 = "Tran_Van_Secretname", "Le_Thi_Hiddenname"
CHECKS = []


def check(cond, what):
    CHECKS.append((bool(cond), what))
    print(("PASS " if cond else "FAIL ") + what)


def edf(path, patient, start, labels, ns_per_rec, n_rec_header, n_rec_real, dur=1.0):
    ns = len(labels)
    def f(s, w):
        return s.ljust(w)[:w].encode("latin-1")
    hdr_bytes = 256 + 256 * ns
    h = (f("0", 8) + f(patient, 80) + f("Startdate X X X X", 80) + f(start, 8) + f("10.00.00", 8) + f(str(hdr_bytes), 8)
         + f("", 44) + f(str(n_rec_header), 8) + f(f"{dur:g}", 8) + f(str(ns), 4))
    h += b"".join(f(l, 16) for l in labels) + b"".join(f("", 80) for _ in labels)
    for _ in range(5):
        h += b"".join(f("0", 8) for _ in labels)
    h += b"".join(f("", 80) for _ in labels) + b"".join(f(str(n), 8) for n in ns_per_rec)
    h += b"".join(f("", 32) for _ in labels)
    assert len(h) == hdr_bytes
    with open(path, "wb") as fh:
        fh.write(h)
        fh.write(b"\x00" * (2 * sum(ns_per_rec) * n_rec_real))


def build(root, leak_summary=False):
    cl = root / "Dataset" / "Clinical"; cl.mkdir(parents=True)
    e19 = ["Fp1", "F7", "T3", "T5", "O1", "F3", "C3", "P3", "Fp2", "F4", "C4", "P4", "O2", "F8", "T4", "T6", "Fz", "Cz",
           "Pz"]
    edf(cl / f"{NAME1}.edf", f"X M 01-JAN-1970 {NAME1}", "01.02.25", e19 + ["EDF Annotations"], [256] * 19 + [60],
        n_rec_header=10, n_rec_real=40)                                      # larger, truncated header (10 vs 40)
    e18 = [e for e in e19 if e != "Pz"]                                     # Pz missing
    edf(cl / f"{NAME2}.edf", f"Y F 02-FEB-1980 {NAME2}", "03.04.25", e18, [512] * 18, n_rec_header=5, n_rec_real=5)
    d = root / "Defense"
    (d / "slides" / "figs" / "final").mkdir(parents=True)
    (d / "slides" / "figs" / "final" / "item2_missed.png").write_bytes(b"png1")
    (d / "slides" / "figs" / "p31_chb06.png").write_bytes(b"png2")
    (d / "slides" / "draw_deck.py").write_text('"""SELECTION RULE: missed seizure of chb06_01, annotated 1724-1738"""\n',
                                                encoding="utf-8")
    (d / "slides" / "leak.py").write_text(f"# chb06_01 drawn for {NAME1.replace('_', ' ')}\n", encoding="utf-8")
    (d / "slides" / "figs" / "selection.csv").write_text("item,rule\np31,typical AUROC closest to the mean\n",
                                                         encoding="utf-8")
    (d / "slides" / "note2.md").write_text("chb24 panel for L\u00ea Th\u1ecb Hiddenname\n", encoding="utf-8")
    (d / "notes").mkdir()
    (d / "notes" / "old.md").write_text(f"chb24 detected panel\nhospital file {NAME2} flagged event\n", encoding="utf-8")
    (d / "notes" / "rule.py").write_text("# selection rule in notes\n", encoding="utf-8")
    (d / "clinical" / "run").mkdir(parents=True)
    s = "# V9-C1 SUMMARY\nFrozen final system (seed 42, balanced point)\nclin01 35 events 4.78 %\n"
    if leak_summary:
        s += f"source {NAME1}\n"
    (d / "clinical" / "run" / "SUMMARY.md").write_text(s, encoding="utf-8")
    (d / "clinical" / "run" / "selection.csv").write_text("annotated hospital\n", encoding="utf-8")


def run(root, *args):
    return subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), *args], capture_output=True, text=True)


def main():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t) / "Thesis"; out = Path(t) / "out"; rep = Path(t) / "inbox" / "R.md"
        build(root)
        r = run(root, "--out", str(out), "--report", str(rep))
        check(r.returncode == 0, f"both parts run (rc {r.returncode}) {r.stderr[-300:]}")
        allout = "".join(p.read_text(encoding="utf-8", errors="replace") for p in out.rglob("*") if p.is_file())
        allout += rep.read_text(encoding="utf-8") if rep.exists() else ""
        allout += r.stdout
        for secret in (NAME1, NAME2, NAME1.replace("_", " "), NAME2.replace("_", " "), "01.02.25", "03.04.25"):
            check(secret.lower() not in allout.lower(), f"protected phrase never in any output: {secret[:3]}...")
        inv = list(csv.DictReader(open(out / "inventory.csv", encoding="utf-8")))
        check({x["path"] for x in inv} == {"slides/figs/final/item2_missed.png", "slides/figs/p31_chb06.png"},
              "inventory = the 2 figures, clinical excluded")
        hits = list(csv.DictReader(open(out / "hits.csv", encoding="utf-8")))
        check(any(h["path"] == "slides/draw_deck.py" and "annotated" in h["keys"] for h in hits), "hit in drawing script")
        check(any(h["path"] == "notes/old.md" and h["text"].startswith("chb24") for h in hits), "clean notes line kept")
        check(not any(h["path"].startswith("clinical") for h in hits), "no hit from Defense/clinical")
        cp = {p.name for p in (out / "defense_copy").iterdir()}
        check(cp == {"slides__draw_deck.py", "slides__figs__selection.csv"},
              f"copies = script + selection; leaking script and notes not copied ({sorted(cp)})")
        md = (out / "INVENTORY.md").read_text(encoding="utf-8")
        check("copies skipped by the privacy gate: 1" in md, "skipped copy counted")
        check("lines / paths dropped by the gate: 3" in md, "dropped lines counted (leak.py, notes, diacritic spelling)")
        R = rep.read_text(encoding="utf-8")
        check("sampling rates of those (Hz): 256" in R and "sampling rates of those (Hz): 512" in R, "rates 256 / 512")
        check("19 non-annotation" in R, "annotation signal excluded")
        check("duration header 0.003 h, from file size 0.011 h" in R, "truncated header: duration from the file size")
        check("found: 19 of 19; missing: none" in R and "'T7': 'T3'" in R and "'P7': 'T5'" in R,
              "clin01 all electrodes, aliases T3/T5/T4/T6 reported")
        check("found: 18 of 19; missing: ['PZ']" in R, "clin02 missing electrode reported")
        check("seed 42" in R and "35 events" in R, "SUMMARY copied")
        check("szscan.db" in R and "uploads" in R or "szscan.db not found" in R, "SzScan section present")
        # STOP path: SUMMARY leaks a name -> no report written
        root2 = Path(t) / "T2"; rep2 = Path(t) / "inbox2" / "R.md"
        build(root2, leak_summary=True)
        r2 = run(root2, "--part", "b", "--report", str(rep2))
        check(r2.returncode != 0 and "STOP" in (r2.stdout + r2.stderr) and not rep2.exists(),
              "part B STOPs and writes nothing when SUMMARY leaks a name")
        check(NAME1.lower() not in (r2.stdout + r2.stderr).lower(), "STOP message does not print the name")
        # STOP path: not exactly 2 hospital files
        root3 = Path(t) / "T3"; build(root3)
        next((root3 / "Dataset" / "Clinical").glob("*.edf")).unlink()
        r3 = run(root3, "--part", "b", "--report", str(Path(t) / "x.md"))
        check(r3.returncode != 0 and "expected 2 hospital EDF files" in r3.stdout + r3.stderr, "STOP on 1 hospital file")
        r4 = run(Path(t) / "none", "--part", "a", "--out", str(Path(t) / "o4"))
        check(r4.returncode != 0 and "STOP" in r4.stdout + r4.stderr, "part A STOPs without Defense/")
    n_fail = sum(1 for ok, _ in CHECKS if not ok)
    print(f"\n{len(CHECKS) - n_fail} / {len(CHECKS)} checks PASS")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
