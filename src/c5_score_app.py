#!/usr/bin/env python
"""
c5_score_app.py -- chat C5c (Track C), Step 2b, design item C12: how good each subject of the review application is,
scored OUTSIDE the application.

The application never reads an annotation (integrity rule 8; web_demo/backend/tests/test_guards.py). This script reads
the application's database READ ONLY (SQLite read-only URI), takes every AI event of every public subject (CHB-MIT
`chbNN`, Siena `PNxx`; a suffix such as `chb24-file` = the same recording stored a second time, e.g. in the other
engine mode), and scores it against the annotations with the application-tier scorer of the thesis:
  - per file, SzCORE event scoring through `szcore_eval.score_szcore` (SZ_PARAM; 30 / 60-s tolerances, merge < 90 s,
    split > 300 s), counts accumulated per subject; sensitivity / precision / F1 / FP per day from the counts with
    `eval_application_events._score_from_counts` (FP per day on the recorded time minus seizure time);
  - events that run past the end of their file (session engine: one change point run over the concatenated files)
    are split onto the next file with `eval_application_events.split_boundary_events` -- all reused, never retyped;
  - annotations from `x1_external.subject_files` (CHB-MIT summary; Siena: SzCORE's own epilepsy2bids parser, copied
    verbatim there), i.e. the files of the external evaluation of the thesis.
Every AI event counts, before review (review status ignored; human events dropped), as in the application tier.

Private studies (hospital records) are skipped -- they have no annotation; only their number is printed.

Gate S0 (written before the run): the 8 test subjects stored in session mode reproduce the committed application-tier
result `results/application_eval_v4/per_subject.csv` (seizures, detected, false alarms) exactly -- the scorer and the
annotation path are then the ones of the thesis. Gate S1 (C5c, added 26/11 after the Windows failure of the Siena
parser, before any real run): per file, the reference seizures counted here = F2-03's L3 rows (`n_ref`), for every
file L3 scored -- the annotation path on the laptop equals the Kaggle one. Siena list times are read through
`siena_clock` (Windows' mktime refuses the parser's 1900 dates; same differences, see `_clock_seconds`). Training patients are marked "seen in training" (the GAE was trained
on their seizure-free windows); the 3 validation patients helped choose settings; test, chb24 and Siena are unseen.

Outputs: results/c5_szscan/step2/score_app/ (per_subject.csv, SUMMARY.md, gates.json). Per-group values are per-patient
means (the thesis's macro average); they describe the demo, they are not new results of the thesis (V5 stays the
number source; integrity rule 4).

Run: PYTHONUTF8=1 python src/c5_score_app.py --chb F:/Study/Thesis/Dataset/CHB-MIT --siena F:/Study/Thesis/Dataset/siena
"""
import argparse
import contextlib
import csv
import json
import time
import re
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "web_demo" / "backend"
for _p in (ROOT / "src", ROOT / "src" / "dataprep"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import eval_application_events as EA      # noqa: E402  (read only: split_boundary_events, _score_from_counts)
from szcore_eval import score_szcore      # noqa: E402

OUT = ROOT / "results" / "c5_szscan" / "step2" / "score_app"
REF_V4 = ROOT / "results" / "application_eval_v4" / "per_subject.csv"
REF_L3 = ROOT / "results" / "m2l" / "l3eval" / "per_file.csv"
TRAIN = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08", "chb09", "chb12", "chb19", "chb20", "chb21", "chb23"]
VALID = ["chb10", "chb11", "chb22"]
TEST = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
ID_RE = re.compile(r"^(chb\d\d|PN\d\d)(.*)$")


def group_of(base):
    if base in TEST:
        return "test"
    if base in VALID:
        return "validation"
    if base in TRAIN:
        return "training (seen in training)"
    if base == "chb24":
        return "chb24"
    if base.startswith("PN"):
        return "Siena"
    return "other CHB-MIT"


def db_read(db_path):
    con = sqlite3.connect(f"file:{Path(db_path).as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    subs = [dict(r) for r in con.execute("SELECT id, mode, mains_hz, private FROM subjects ORDER BY id")]
    files = [dict(r) for r in con.execute("SELECT id, subject_id, filename, duration_seconds FROM files "
                                          "ORDER BY subject_id, filename")]
    events = [dict(r) for r in con.execute("SELECT file_id, source, onset_sec, offset_sec, review_status FROM events")]
    con.close()
    return subs, files, events


def annotations(base, chb_root, siena_root):
    """{file name: [(onset_s, offset_s), ...]}. CHB-MIT: the subject's summary through preprocessing.parse_summary
    (the thesis's own parser; x1_external.chb_subject is not used because its file glob `chbNN_*.edf` misses chb17's
    lettered files); Siena: x1_external.siena_subject (SzCORE's epilepsy2bids parser, copied verbatim there)."""
    root = chb_root if base.startswith("chb") else siena_root
    if root is None:
        raise SystemExit(f"STOP: {base} needs --{'chb' if base.startswith('chb') else 'siena'}")
    if base.startswith("chb"):
        import preprocessing as P
        summ = sorted(Path(root).rglob(f"{base}-summary.txt")) or sorted(Path(root).rglob(f"{base}-summary.md"))
        if not summ:
            raise SystemExit(f"STOP: {base}-summary.txt / .md not found under {root}")
        return {fn: list(sz) for fn, sz in P.parse_summary(summ[0]).items()}
    import x1_external as X1
    with siena_clock(X1):
        files, _ = X1.siena_subject(root, base)
    return {p.name: list(sz) for p, sz in files}


def _clock_seconds(string):
    """x1_external._parseTimeStamp (SzCORE's epilepsy2bids parser) returns time.mktime of a struct with only the hour,
    minute and second, i.e. a date in 1900; Windows' mktime refuses dates before 1970 (OverflowError on the laptop,
    C5c 26/11). The parser only ever uses DIFFERENCES of two such values (with +24 h on a day shift), and on the same
    date mktime is the second of the day plus a constant, so the second of the day gives the same differences. The
    time string is found and validated exactly as the original (same regex, same strptime format)."""
    stamp = re.findall(".*[ |:]([0-9]+.[0-9]+.[0-9]+).*", string)[0]
    t = time.strptime(stamp.replace(":", "."), "%H.%M.%S")
    return float(t.tm_hour * 3600 + t.tm_min * 60 + t.tm_sec)


@contextlib.contextmanager
def siena_clock(X1):
    """Inside the block, x1_external's parser uses _clock_seconds (the record module itself is not changed)."""
    orig = X1._parseTimeStamp
    X1._parseTimeStamp = _clock_seconds
    try:
        yield
    finally:
        X1._parseTimeStamp = orig


def score_subject(sid, base, sfiles, events, uploads, ann):
    """Counts of one subject (all its files) -> dict, plus the per-file rows."""
    fids = {f["id"]: f for f in sfiles}
    # A recording the subject's annotation does not list has no seizure -- the convention of x1_external.chb_subject
    # (`sz.get(f, [])`), used by F2-03's L3 run: chb24's summary lists only its seizure files (C5c 27/11). Counted
    # per subject; gate S1 checks the per-file seizure counts against L3 for every file L3 scored.
    unlisted = [f["filename"] for f in sfiles if f["filename"] not in ann]
    ann = {**ann, **{fn: [] for fn in unlisted}}
    frows = []
    for f in sfiles:
        score_p = uploads / sid / f"{Path(f['filename']).stem}.score.npy"
        if not score_p.exists():
            raise SystemExit(f"STOP: {score_p} not found (n_windows of the file)")
        frows.append(dict(subject=sid, file_name=f["filename"], duration_s=float(f["duration_seconds"]),
                          n_windows=int(np.load(score_p, mmap_mode="r").shape[0]), status="done"))
    files_df = pd.DataFrame(frows)
    ev = [dict(subject=sid, file_name=fids[e["file_id"]]["filename"], event_id=i, onset_s=float(e["onset_sec"]),
               offset_s=float(e["offset_sec"]), source=e["source"], review_status=e["review_status"] or "")
          for i, e in enumerate(events) if e["file_id"] in fids and e["source"] == "AI"]
    ev_df = pd.DataFrame(ev, columns=EA.REQUIRED_EVENT_COLS)
    ev_df, bstats = EA.split_boundary_events(ev_df, files_df)
    tp = fp = n_ref = 0
    dur = sz_s = 0.0
    per_file = {}
    for fr in frows:
        ref = ann[fr["file_name"]]
        hyp = [(r.onset_s, r.offset_s) for r in ev_df[ev_df["file_name"] == fr["file_name"]].itertuples()]
        s_s = sum(b - a for a, b in ref)
        sc = score_szcore(ref, hyp, total_dur_s=fr["duration_s"], n_inter_h=max(fr["duration_s"] - s_s, 0.0) / 3600)
        tp += sc["tp"]; fp += sc["fp"]; n_ref += sc["n_ref"]; dur += fr["duration_s"]; sz_s += s_s
        per_file[fr["file_name"]] = sc["n_ref"]
    row = dict(subject=sid, base=base, group=group_of(base), files=len(frows), hours=round(dur / 3600, 4),
               ai_events=len(ev), events_crossing_files=bstats[sid]["n_crossed"], files_not_in_annotation=len(unlisted))
    row.update(EA._score_from_counts(tp, fp, n_ref, dur, sz_s))
    row["_n_ref_by_file"] = per_file
    return row


def gate_s0(rows):
    if not REF_V4.exists():
        return dict(PASS=None, note=f"{REF_V4} not found")
    ref = pd.read_csv(REF_V4).set_index("subject")
    got = {r["subject"]: r for r in rows if r["subject"] in TEST and r["mode"] == "session"}
    if set(got) != set(TEST):
        return dict(PASS=None, note=f"test subjects in session mode present: {sorted(got)}")
    diff = [s for s in TEST if (got[s]["seizures"], got[s]["detected"], got[s]["false_alarms"])
            != (int(ref.loc[s, "seizures"]), int(ref.loc[s, "detected"]), int(ref.loc[s, "false_alarms"]))]
    return dict(PASS=not diff, differ=diff, reference=str(REF_V4.relative_to(ROOT)))


def gate_s1(rows):
    """Annotation path on this machine = the one of F2-03's L3 run on Kaggle: per file, the number of reference
    seizures counted by the scorer equals L3's committed `n_ref` (seed 42, B-MCD-F rows), for every file of the
    database that L3 scored (test, chb24, Siena)."""
    if not REF_L3.exists():
        return dict(PASS=None, note=f"{REF_L3} not found")
    ref = {}
    with open(REF_L3, newline="") as fh:
        for r in csv.DictReader(fh):
            if r["seed"] == "clean_seed42" and r["budget"] == "B-MCD-F":
                ref[(r["subject"], r["file"])] = int(r["n_ref"])
    seen = differ = 0
    bad = []
    for r in rows:
        for fn, n in r["_n_ref_by_file"].items():
            k = (r["base"], fn)
            if k in ref:
                seen += 1
                if ref[k] != n:
                    differ += 1
                    bad.append(f"{r['subject']}/{fn}: {n} vs L3 {ref[k]}")
    if not seen:
        return dict(PASS=None, note="no database file is among L3's files")
    return dict(PASS=differ == 0, files_compared=seen, differ=bad[:20], reference=str(REF_L3.relative_to(ROOT)))


def fmt(v, d=3):
    return v if isinstance(v, str) else f"{v:.{d}f}"


def write(out, rows, gates, n_private, smoke):
    out.mkdir(parents=True, exist_ok=True)
    rows = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]
    df = pd.DataFrame(rows)
    df.to_csv(out / "per_subject.csv", index=False)
    (out / "gates.json").write_text(json.dumps(gates, indent=1, default=str), encoding="utf-8")
    L = [f"# SzScan subjects scored outside the application (chat C5c, Step 2b){' — SMOKE' if smoke else ''}", "",
         "Every AI event of every public subject of the application's database, before review, against the "
         "annotations (SzCORE event scoring, application-tier scorer of the thesis; `src/c5_score_app.py`). "
         f"Private studies skipped: {n_private}. Group values are per-patient means; they describe the demo "
         "database, not new thesis results (V5 stays the number source).", "",
         f"Gate S0 (test subjects, session mode = committed application-tier result `application_eval_v4`): "
         f"**{ {True: 'PASS', False: 'FAIL', None: 'not run'}[gates['S0']['PASS']] }** "
         f"{gates['S0'].get('differ') or gates['S0'].get('note') or ''}", "",
         f"Gate S1 (reference seizures per file = F2-03's L3 rows): "
         f"**{ {True: 'PASS', False: 'FAIL', None: 'not run'}[gates['S1']['PASS']] }** "
         f"{gates['S1'].get('files_compared', '')} files compared {gates['S1'].get('differ') or gates['S1'].get('note') or ''}",
         "",
         "| group | mode | subjects | hours | seizures | detected | sensitivity (mean) | F1 (mean) | FP/day (mean) |",
         "|---|---|---|---|---|---|---|---|---|"]
    for (g, m), d in df.groupby(["group", "mode"], sort=True):
        f1 = pd.to_numeric(d["f1"], errors="coerce")
        fpd = pd.to_numeric(d["false_alarms_per_day"], errors="coerce")
        L.append(f"| {g} | {m} | {len(d)} | {d['hours'].sum():.1f} | {int(d['seizures'].sum())} | "
                 f"{int(d['detected'].sum())} | {d.loc[d['seizures'] > 0, 'sensitivity'].mean():.3f} | "
                 f"{f1.mean():.3f} | {fpd.mean():.1f} |")
    L += ["", "Sensitivity mean over subjects with at least one seizure; F1 'undefined' (no detection, no seizure) "
          "left out of the mean. A file the subject's annotation does not list counts as seizure-free (x1_external's "
          f"convention, as F2-03's L3): {int(df['files_not_in_annotation'].sum())} such file(s).", "", "| subject | group | mode | files | hours | seizures | detected | false alarms "
          "| sensitivity | precision | F1 | FP/day | events crossing a file end |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['subject']} | {r['group']} | {r['mode']} | {r['files']} | {r['hours']:.2f} | {r['seizures']} "
                 f"| {r['detected']} | {r['false_alarms']} | {fmt(r['sensitivity'])} | {fmt(r['precision'])} | "
                 f"{fmt(r['f1'])} | {fmt(r['false_alarms_per_day'], 1)} | {r['events_crossing_files']} |")
    (out / "SUMMARY.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chb", default=None, help="CHB-MIT root (x1_external layout)")
    ap.add_argument("--siena", default=None, help="Siena root (x1_external layout)")
    ap.add_argument("--db", default=str(BACKEND / "szscan.db"))
    ap.add_argument("--uploads", default=str(BACKEND / "uploads"))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--subjects", nargs="*", default=None, help="only these subject ids")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args(argv)
    subs, files, events = db_read(a.db)
    uploads = Path(a.uploads)
    n_private, rows, ann_cache = 0, [], {}
    for s in subs:
        if s["private"]:
            n_private += 1
            continue
        if a.subjects and s["id"] not in a.subjects:
            continue
        m = ID_RE.match(s["id"])
        if not m:
            print(f"{s['id']}: not a CHB-MIT or Siena id, skipped", flush=True)
            continue
        base = m.group(1)
        if base not in ann_cache:
            ann_cache[base] = annotations(base, a.chb, a.siena)
        sfiles = [f for f in files if f["subject_id"] == s["id"]]
        r = score_subject(s["id"], base, sfiles, events, uploads, ann_cache[base])
        r["mode"] = s["mode"]
        rows.append(r)
        print(f"{s['id']} ({r['group']}, {s['mode']}): {r['detected']} / {r['seizures']} seizures, "
              f"{r['false_alarms']} false alarms, {r['hours']:.1f} h", flush=True)
    if not rows:
        raise SystemExit("STOP: no public subject scored")
    gates = dict(S0=gate_s0(rows), S1=gate_s1(rows))
    out = Path(a.out) / "smoke" if a.smoke else Path(a.out)
    write(out, rows, gates, n_private, a.smoke)
    print(json.dumps({k: v.get("PASS") for k, v in gates.items()}), f"report: {out / 'SUMMARY.md'}")
    return gates


if __name__ == "__main__":
    main()
