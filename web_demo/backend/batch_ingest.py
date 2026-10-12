"""batch_ingest.py — create subjects in the application's database through the SAME upload flow
the Create New panel drives (upload_manager: start_session -> add_file -> Phase A threads ->
Phase B worker process -> Process -> database), without clicking through the browser.

Used for the application-tier evaluation (project instructions 11.5): a frozen build, a CLEAN
database, the 8 test subjects. It reads EDF files only — never a summary file, never an
annotation. It refuses to run when the database already holds a subject (clean-database rule).

  python batch_ingest.py --dataset F:/Study/Thesis/Dataset/CHB-MIT --subjects chb03 chb06 ...
  python batch_ingest.py --dataset ... --all          (the 8 allow-listed subjects)

Writes a timing log (wall-clock seconds per subject, hours of EEG) to --log (default
`uploads/_ingest_timing.csv`, inside web_demo/).
"""
import argparse
import csv
import re
import sys
import time
from pathlib import Path

import db
import upload_manager as um

MEMO = "application-tier run"


def subject_edfs(subject: str, edf_dir: Path) -> list[Path]:
    """A subject's EDF files, by name only — never a summary or annotation file.

    CHB-MIT splits one subject (chb17) into lettered segments (chb17a_03.edf, chb17b_57.edf,
    chb17c_02.edf, ...); every other test subject uses a plain {subject}_NN.edf name. The pattern
    below covers both, and is anchored so it never matches a different subject's files
    (chb1_01.edf, chb170_01.edf and chb03_01.edf must not count toward "chb17")."""
    pattern = re.compile(rf"^{re.escape(subject)}[a-z]?_\d+\.edf$")
    return sorted(p for p in edf_dir.iterdir() if p.is_file() and pattern.match(p.name))


def wait(cond, what, timeout_s, session):
    t0 = time.time()
    while not cond():
        snap = session.snapshot()
        if snap["error"]:
            raise SystemExit(f"STOP: {what}: {snap['error']}")
        if any(f["status"] == "error" for f in snap["files"]):
            bad = [(f["filename"], f["error"]) for f in snap["files"] if f["status"] == "error"]
            raise SystemExit(f"STOP: {what}: file error {bad}")
        if time.time() - t0 > timeout_s:
            raise SystemExit(f"STOP: {what}: timeout after {timeout_s} s")
        um.poll_tick(session)
        time.sleep(1.0)


def ingest(subject: str, edf_dir: Path) -> dict:
    edfs = subject_edfs(subject, edf_dir)
    if not edfs:
        raise SystemExit(f"STOP: no {subject}[a-z]?_NN.edf under {edf_dir}")
    t0 = time.time()
    session = um.start_session(subject, MEMO)
    for p in edfs:
        tmp = um.save_upload_to_tmp(p.read_bytes())
        um.add_file(session, p.name, tmp)
    wait(lambda: session.snapshot()["ready_to_process"], f"{subject} upload", 6 * 3600, session)
    um.start_process(session, subject, MEMO)
    wait(lambda: session.snapshot()["done"], f"{subject} process", 6 * 3600, session)
    um.acknowledge_done()
    elapsed = time.time() - t0
    files = db.list_files_by_filename(subject)
    hours = sum(f["duration_seconds"] for f in files) / 3600.0
    rejected = sorted({p.name for p in edfs} - {f["filename"] for f in files})
    return dict(subject=subject, files=len(files), edf_present=len(edfs), rejected=" ".join(rejected),
                hours=round(hours, 4), seconds=round(elapsed, 1), s_per_hour=round(elapsed / max(hours, 1e-9), 2))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", required=True, help="folder holding chbNN/ subfolders of EDF files")
    ap.add_argument("--subjects", nargs="*", default=[])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--log", default=str(um.UPLOAD_DIR / "_ingest_timing.csv"))
    a = ap.parse_args()
    subjects = sorted(db.ALLOWED_SUBJECTS) if a.all else a.subjects
    if not subjects or set(subjects) - db.ALLOWED_SUBJECTS:
        raise SystemExit(f"STOP: subjects must be among {sorted(db.ALLOWED_SUBJECTS)}")
    db.init_db()
    existing = [s["id"] for s in db.list_subjects()]
    if existing:
        raise SystemExit(f"STOP: the database already holds {existing}; the application tier needs a clean "
                         "database (move szscan.db and uploads/ aside first).")
    rows = []
    for s in subjects:
        print(f"{s}: ingesting ...", flush=True)
        r = ingest(s, Path(a.dataset) / s)
        rows.append(r)
        print(f"{s}: {r['files']} files ({r['edf_present']} EDF present), {r['hours']:.2f} h, "
              f"{r['seconds']:.0f} s, {r['s_per_hour']:.1f} s per hour of EEG"
              + (f", rejected: {r['rejected']}" if r["rejected"] else ""), flush=True)
        Path(a.log).parent.mkdir(parents=True, exist_ok=True)
        with open(a.log, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader(); w.writerows(rows)
    tot_h = sum(r["hours"] for r in rows); tot_s = sum(r["seconds"] for r in rows)
    print(f"TOTAL {len(rows)} subjects, {tot_h:.2f} h, {tot_s:.0f} s, {tot_s / max(tot_h, 1e-9):.1f} s per hour of EEG")


if __name__ == "__main__":
    sys.exit(main())
