#!/usr/bin/env python
"""
fa1_readonly.py -- Track F, chat D25-F, version A1 requests F-A1.1 and F-A1.2 (REPORT_REVISION_PLAN.md rev 6
section 0.2; board R192, R194). READ ONLY: no model, no EEG signal, no score is computed; nothing outside the two
output places below is written.

PART A -- F-A1.2 (public; output committed under results/fa1/):
  every figure file and every text file of F:/Study/Thesis/Defense/ except Defense/clinical/ (hospital material):
  (1) inventory.csv -- relative path, size, sha16 of every image / document file (png, jpg, svg, pdf, pptx);
  (2) hits.csv + INVENTORY.md -- in every text file (py, md, csv, txt, json, ipynb; < 2 MB) the lines that contain one
      of KEYS (panel titles and the EDF files of the deck panels p16-p18, p31-p35), at most 40 per file;
  (3) copies of every selection*.csv and every *.py under Defense/ (except clinical/) into results/fa1/defense_copy/
      (path flattened with "__"), so the chat can read the selection rules and the drawing scripts themselves.
  Defense/notes text is NOT copied (only its matching lines go to hits.csv).

PART B -- F-A1.1 (private; output ONLY Agent/inbox/FA1_1_CLINICAL_REPORT.md, never committed):
  (1) Defense/clinical/run/SUMMARY.md and Defense/clinical/clin0X_header.md (written by V9-T2 / V9-C1 under their
      privacy rules) are copied into the report after the privacy gate;
  (2) numeric EDF header facts of the two hospital files (clin01 = larger, clin02 = smaller, as V9-T2): sampling rate
      of every EEG signal, number of signals, header duration vs duration from the real file size (truncated header),
      the 19 electrodes of the 18 bipolar derivations found / missing with the alias used (x1_external.SIENA_MAP; same label normalisation as
      v9_clinical_run.clin_load_18);
  (3) SzScan: subject ids in web_demo/backend/szscan.db and folders in web_demo/backend/uploads -- names printed only
      when they are one of the allowed CHB-MIT ids (db.ALLOWED_SUBJECTS); every other entry is only counted.

PRIVACY GATE (both parts): the patient field (EDF+ name sub-field and the whole field), the file-name stems and the
start date of the two hospital EDF headers are read into memory only, never printed. Any output line that contains one
of them (case-insensitive; spaces / underscores normalised; phrases of >= 5 characters) is dropped and counted; a file
copy containing one is skipped and counted. Part B STOPs if a copied report would contain one.

Run (Git Bash, from F:/Study/Thesis/Code):
  python src/fa1_readonly.py --root F:/Study/Thesis            # both parts
  python src/fa1_readonly.py --root <dir> --part a|b           # one part
"""
import argparse
import csv
import hashlib
import re
import shutil
import sqlite3
import sys
import time
import unicodedata
from pathlib import Path

ROOT_CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_CODE / "src"))

IMG_EXT = {".png", ".jpg", ".jpeg", ".svg", ".pdf", ".pptx"}
TXT_EXT = {".py", ".md", ".csv", ".txt", ".json", ".ipynb"}
MAX_TXT = 2 * 1024 * 1024
MAX_HITS = 40
KEYS = ["annotated", "lost by the app", "lost by app", "found only", "found by the final", "typical", "unseen",
        "lowest amplitude", "best seizure", "selection rule", "selection", "pn10", "pn11", "chb24", "auroc",
        "chb03_01", "chb03_34", "chb06_01", "chb06_04", "chb13_", "chb14_06", "chb14_29", "chb15_06", "chb15_15",
        "chb16_17", "flagged event", "false alarm", "missed", "detected"]
ALIAS = {"T3": "T7", "T4": "T8", "T5": "P7", "T6": "P8"}            # = x1_external.SIENA_MAP
BIPOLAR_E = ["FP1", "F7", "T7", "P7", "O1", "F3", "C3", "P3", "FP2", "F4", "C4", "P4", "O2", "F8", "T8", "P8", "FZ",
             "CZ", "PZ"]


# ----------------------------------------------------------------------------- EDF header (stdlib, no signal read)
def edf_header(path):
    with open(path, "rb") as f:
        h = f.read(256)
        ns = int(h[252:256].decode("ascii", "replace").strip())
        rest = f.read(ns * 256)
    def field(off, width):
        return [rest[off + i * width: off + (i + 1) * width].decode("latin-1").strip() for i in range(ns)]
    o = 0
    labels = field(o, 16); o += ns * 16
    o += ns * 80 + ns * 8 * 5 + ns * 80                                  # transducer, dims/min/max, prefilter
    nsamp = [int(x) for x in field(o, 8)]
    hdr_bytes = int(h[184:192].decode("ascii").strip())
    n_rec = int(h[236:244].decode("ascii").strip())
    dur = float(h[244:252].decode("ascii").strip())
    size = Path(path).stat().st_size
    rec_bytes = 2 * sum(nsamp)
    real_rec = (size - hdr_bytes) / rec_bytes if rec_bytes else float("nan")
    return dict(patient=h[8:88].decode("latin-1").strip(), recording=h[88:168].decode("latin-1").strip(),
                startdate=h[168:176].decode("latin-1").strip(), labels=labels, nsamp=nsamp, dur=dur,
                n_rec=n_rec, real_rec=real_rec, size=size)


def clinical_files(root):
    d = None
    for name in ("Clinical", "clinical"):
        if (root / "Dataset" / name).is_dir():
            d = root / "Dataset" / name
            break
    if d is None:
        return []
    fs = sorted([p for p in d.iterdir() if p.suffix.lower() == ".edf"], key=lambda p: -p.stat().st_size)
    return fs


def norm(s):
    """lower case, Vietnamese diacritics removed (d-stroke -> d), runs of spaces / underscores -> one space."""
    s = unicodedata.normalize("NFKD", s.replace("\u0111", "d").replace("\u0110", "D"))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[\s_]+", " ", s.lower()).strip()


def gate_phrases(root):
    """secret phrases from the hospital EDF headers and file names; held in memory only."""
    out = set()
    for p in clinical_files(root):
        hd = edf_header(p)
        out.add(norm(p.stem))
        pat = hd["patient"]
        parts = pat.split(" ")
        if len(parts) >= 4:                                            # EDF+: code sex birthdate name
            out.add(norm(parts[3]))
            out.add(norm(" ".join(parts[3:])))
        out.add(norm(pat))
        if hd["startdate"]:
            out.add(norm(hd["startdate"]))
    return {x for x in out if len(x) >= 5 and x not in {"x x x x", "x x x"}}


class Gate:
    def __init__(self, phrases):
        self.ph = phrases
        self.dropped = 0

    def bad(self, text):
        t = norm(text)
        return any(p in t for p in self.ph)

    def line(self, text):
        if self.bad(text):
            self.dropped += 1
            return None
        return text


def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


# ----------------------------------------------------------------------------- part A
def part_a(root, gate, out):
    dfn = root / "Defense"
    if not dfn.is_dir():
        raise SystemExit(f"STOP: {dfn} not found")
    out.mkdir(parents=True, exist_ok=True)
    cp = out / "defense_copy"
    if cp.exists():
        shutil.rmtree(cp)
    cp.mkdir()
    files = [p for p in dfn.rglob("*") if p.is_file() and "clinical" not in [x.lower() for x in p.relative_to(dfn).parts]]
    inv, hits, copied, skipped = [], [], [], 0
    for p in sorted(files):
        rel = p.relative_to(dfn).as_posix()
        if gate.bad(rel):
            gate.dropped += 1
            continue
        ext = p.suffix.lower()
        if ext in IMG_EXT:
            inv.append(dict(path=rel, bytes=p.stat().st_size, sha16=sha16(p)))
        if ext in TXT_EXT and p.stat().st_size < MAX_TXT:
            text = p.read_text(encoding="utf-8", errors="replace")
            n = 0
            for i, ln in enumerate(text.splitlines(), 1):
                low = ln.lower()
                keys = [k for k in KEYS if k in low]
                if keys and n < MAX_HITS:
                    ok = gate.line(ln.strip()[:240])
                    if ok is not None:
                        hits.append(dict(path=rel, line=i, keys="|".join(keys), text=ok))
                        n += 1
            is_sel = p.name.lower().startswith("selection") and ext == ".csv"
            if (ext == ".py" or is_sel) and not rel.lower().startswith("notes/"):
                if gate.bad(text):
                    skipped += 1
                    continue
                dst = cp / rel.replace("/", "__")
                shutil.copyfile(p, dst)
                copied.append(rel)
    with open(out / "inventory.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["path", "bytes", "sha16"]); w.writeheader(); w.writerows(inv)
    with open(out / "hits.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["path", "line", "keys", "text"]); w.writeheader(); w.writerows(hits)
    total = sum((cp / c.replace("/", "__")).stat().st_size for c in copied)
    if total > 20 * 1024 * 1024:
        raise SystemExit(f"STOP: copies total {total / 1e6:.1f} MB > 20 MB; nothing is to be committed")
    by_dir = {}
    for r in inv:
        k = r["path"].rsplit("/", 1)[0] if "/" in r["path"] else "."
        by_dir[k] = by_dir.get(k, 0) + 1
    L = ["# F-A1.2 inventory of Defense/ (read only; Defense/clinical/ excluded)\n",
         f"- figure / document files: {len(inv)} (inventory.csv); text lines matching the deck keys: {len(hits)} "
         f"(hits.csv); scripts and selection tables copied: {len(copied)} (defense_copy/); copies skipped by the privacy "
         f"gate: {skipped}; lines / paths dropped by the gate: {gate.dropped}\n",
         "\n## Figure files per folder\n", "| folder | files |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in sorted(by_dir.items())]
    L += ["\n## Copied\n"] + [f"- {c}" for c in copied]
    (out / "INVENTORY.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"part A: {len(inv)} figure files, {len(hits)} hits, {len(copied)} copies, gate dropped {gate.dropped}, "
          f"skipped {skipped}")


# ----------------------------------------------------------------------------- part B
def part_b(root, gate, report):
    alias_map = ALIAS
    try:                                                               # the run's own map, if importable
        import x1_external as X1
        if X1.SIENA_MAP != ALIAS:
            raise SystemExit(f"STOP: x1_external.SIENA_MAP {X1.SIENA_MAP} differs from {ALIAS}")
    except ImportError:
        pass
    L = ["# F-A1.1 -- hospital records (PRIVATE: Agent/inbox only, never committed)\n"]
    cf = clinical_files(root)
    if len(cf) != 2:
        raise SystemExit(f"STOP: expected 2 hospital EDF files, found {len(cf)}")
    for tag, p in zip(("clin01", "clin02"), cf):
        hd = edf_header(p)
        eeg = [(lab, ns) for lab, ns in zip(hd["labels"], hd["nsamp"]) if "annotation" not in lab.lower()]
        rates = sorted({ns / hd["dur"] for _, ns in eeg}) if hd["dur"] else []
        names = {}
        for lab, _ in eeg:
            n = lab.upper().replace("EEG", "").strip().replace(" ", "")      # = v9_clinical_run.clin_load_18
            names.setdefault(alias_map.get(n, n), n)
        found = {e: names[e] for e in BIPOLAR_E if e in names}
        miss = [e for e in BIPOLAR_E if e not in names]
        alias = {e: v for e, v in found.items() if v != e}
        L += [f"## {tag}\n",
              f"- signals in header: {len(hd['labels'])} ({len(eeg)} non-annotation); sampling rates of those (Hz): "
              f"{', '.join(f'{r:g}' for r in rates)}",
              f"- record duration {hd['dur']:g} s; records in header {hd['n_rec']}; records from the file size "
              f"{hd['real_rec']:.2f} -> duration header {hd['n_rec'] * hd['dur'] / 3600:.3f} h, from file size "
              f"{hd['real_rec'] * hd['dur'] / 3600:.3f} h",
              f"- electrodes of the 18 derivations found: {len(found)} of 19; missing: {miss or 'none'}; "
              f"read through an alias: {alias or 'none'}\n"]
    for rel in ("Defense/clinical/run/SUMMARY.md", "Defense/clinical/clin01_header.md",
                "Defense/clinical/clin02_header.md"):
        q = root / rel
        L.append(f"## {rel}\n")
        if not q.exists():
            L.append("(not found)\n")
            continue
        t = q.read_text(encoding="utf-8", errors="replace")
        if gate.bad(t):
            raise SystemExit(f"STOP: {rel} contains a protected phrase; nothing written")
        L += ["```", t.rstrip(), "```\n"]
    figs = root / "Defense" / "clinical" / "run"
    if figs.is_dir():
        L.append(f"- files in Defense/clinical/run/: {sum(1 for x in figs.rglob('*') if x.is_file())}\n")
    import importlib.util
    spec = importlib.util.spec_from_file_location("szdb", ROOT_CODE / "web_demo" / "backend" / "db.py")
    allowed = set()
    try:
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); allowed = set(m.ALLOWED_SUBJECTS)
    except Exception as ex:                                            # report, do not guess
        L.append(f"- db.ALLOWED_SUBJECTS not readable: {type(ex).__name__}")
    L.append("## SzScan\n")
    L.append(f"- allowed subjects in the code: {sorted(allowed)}")
    dbp = ROOT_CODE / "web_demo" / "backend" / "szscan.db"
    if dbp.exists():
        con = sqlite3.connect(f"file:{dbp.as_posix()}?mode=ro", uri=True)
        ids = [r[0] for r in con.execute("SELECT id FROM subjects")]
        nf = dict(con.execute("SELECT subject_id, COUNT(*) FROM files GROUP BY subject_id").fetchall())
        con.close()
        ok = sorted(i for i in ids if i in allowed)
        L.append(f"- szscan.db subjects: {len(ids)}; allowed ids {[(i, nf.get(i, 0)) for i in ok]}; "
                 f"other ids: {len(ids) - len(ok)} (files: {sum(v for k, v in nf.items() if k not in allowed)})")
    else:
        L.append("- szscan.db not found")
    up = ROOT_CODE / "web_demo" / "backend" / "uploads"
    if up.is_dir():
        dirs = [d.name for d in up.iterdir() if d.is_dir()]
        ok = sorted(d for d in dirs if d in allowed)
        other = [d for d in dirs if d not in allowed]
        L.append(f"- uploads folders: {len(dirs)}; allowed {ok}; other {len(other)} "
                 f"(names starting with '_': {sum(1 for d in other if d.startswith('_'))})")
        edf_other = [x for x in up.rglob("*.edf") if x.parent.name not in allowed]
        L.append(f"- EDF files in uploads outside the allowed subject folders: {len(edf_other)}")
    out = "\n".join(L) + "\n"
    if gate.bad(out):
        raise SystemExit("STOP: the report would contain a protected phrase; nothing written")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(out, encoding="utf-8")
    print(f"part B: written {report} ({len(out)} characters)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--part", choices=["a", "b", "both"], default="both")
    ap.add_argument("--out", default=str(ROOT_CODE / "results" / "fa1"))
    ap.add_argument("--report", default=None)
    a = ap.parse_args()
    root = Path(a.root)
    t0 = time.time()
    gate = Gate(gate_phrases(root))
    print(f"privacy gate: {len(gate.ph)} protected phrases (not shown)")
    if a.part in ("a", "both"):
        part_a(root, gate, Path(a.out))
    if a.part in ("b", "both"):
        part_b(root, Gate(gate.ph), Path(a.report) if a.report else root / "Agent" / "inbox" / "FA1_1_CLINICAL_REPORT.md")
    print(f"done in {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main()
