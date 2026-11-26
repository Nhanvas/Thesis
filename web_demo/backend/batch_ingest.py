"""batch_ingest.py — create subjects in the application's database through the SAME upload flow
the Create New panel drives (upload_manager: start_session -> add_file -> Phase A threads ->
Phase B worker process -> Process -> database), without clicking through the browser.

Used for the application-tier evaluation (project instructions 11.5): a frozen build, a CLEAN
database, the 8 test subjects. It reads EDF files only — never a summary file, never an
annotation. It refuses to run when the database already holds a subject (clean-database rule).

  python batch_ingest.py --dataset F:/Study/Thesis/Dataset/CHB-MIT --subjects chb03 chb06 ...
  python batch_ingest.py --dataset ... --all          (the 8 test subjects of the application tier)

C5 Step 2: any subject id (no allowlist); --append adds subjects to a database that already holds some (existing ids
are skipped); --mode / --mains / --interpolate set the study's engine settings; --private-dir ingests every EDF of a
folder as its own PRIVATE study (ids <prefix>01, <prefix>02, ... by decreasing file size, as src/v9_clinical_run's
rule; neutral file names; nothing about the original files is printed or logged). Files are copied in 1-MB chunks.

Writes a timing log (wall-clock seconds per subject, hours of EEG) to --log (default
`uploads/_ingest_log_c5c.csv`, inside web_demo/; the defense-time `_ingest_timing.csv` is left as it is).

C5c (26/11): --id-suffix stores a subject under another id (e.g. chb24 a second time in file mode as chb24-file);
the log is appended across runs (one row per subject, written as it finishes); each row carries the peak memory of
this process and its worker processes (private memory on Windows, resident elsewhere; sampled every 0.5 s), and
--max-gb stops the run (exit 3) before the machine runs out of memory.
"""
import argparse
import csv
import os
import re
import sys
import threading
import time
from pathlib import Path

import db
import upload_manager as um

MEMO = "application-tier run"
TEST_SUBJECTS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]


def subject_edfs(subject: str, edf_dir: Path) -> list[Path]:
    """A subject's EDF files, by name only — never a summary or annotation file.

    CHB-MIT splits one subject (chb17) into lettered segments (chb17a_03.edf, chb17b_57.edf,
    chb17c_02.edf, ...); every other test subject uses a plain {subject}_NN.edf name. The pattern
    below covers both, and is anchored so it never matches a different subject's files
    (chb1_01.edf, chb170_01.edf and chb03_01.edf must not count toward "chb17")."""
    pattern = re.compile(rf"^{re.escape(subject)}[a-z]?_\d+\.edf$")
    hits = sorted(p for p in edf_dir.iterdir() if p.is_file() and pattern.match(p.name))
    if hits or subject.lower().startswith("chb"):
        return hits
    # other datasets (e.g. Siena PNxx/PNxx-N.edf): every .edf of the subject's folder, by name
    return sorted(p for p in edf_dir.iterdir() if p.is_file() and p.suffix.lower() == ".edf")


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


class TreeMemory:
    """Peak memory (MB) of this process and its children, sampled every 0.5 s: private bytes on Windows (what the
    system commits), resident elsewhere. Above limit_mb: message and os._exit(3) (C5c; the laptop is in daily use)."""
    def __init__(self, limit_mb=None):
        import psutil
        self.ps, self.me, self.limit = psutil, psutil.Process(), limit_mb
        self.peak, self._stop = 0.0, False
        threading.Thread(target=self._run, daemon=True).start()

    def now(self):
        tot = 0.0
        for pr in [self.me] + self.me.children(recursive=True):
            try:
                mi = pr.memory_info()
                tot += getattr(mi, "private", 0) or mi.rss
            except (self.ps.NoSuchProcess, self.ps.AccessDenied):
                pass
        return tot / 1e6

    def _run(self):
        while not self._stop:
            m = self.now()
            self.peak = max(self.peak, m)
            if self.limit and m > self.limit:
                print(f"STOP: memory of the ingest (this process + workers) {m:.0f} MB > limit {self.limit:.0f} MB",
                      flush=True)
                os._exit(3)
            time.sleep(0.5)

    def reset(self):
        self.peak = self.now()


MEM = None


def ingest(subject: str, edf_dir: Path = None, edfs: list = None, mode: str = "session", mains="auto",
           private: bool = False, interpolate: bool = False, memo: str = MEMO, sid: str = None) -> dict:
    edfs = edfs if edfs is not None else subject_edfs(subject, edf_dir)
    if not edfs:
        raise SystemExit(f"STOP: no EDF for {subject}")
    sid = sid or subject
    t0 = time.time()
    if MEM:
        MEM.reset()
    session = um.start_session(sid, memo, mode, mains, private, interpolate)
    for p in edfs:
        with open(p, "rb") as fh:
            tmp, _, _ = um.save_upload_stream(fh)
        um.add_file(session, um.neutral_name(session) if private else p.name, tmp)
    wait(lambda: session.snapshot()["ready_to_process"], f"{sid} upload", 6 * 3600, session)
    um.start_process(session, sid, memo)
    wait(lambda: session.snapshot()["done"], f"{sid} process", 6 * 3600, session)
    um.acknowledge_done()
    elapsed = time.time() - t0
    files = db.list_files_by_filename(sid)
    hours = sum(f["duration_seconds"] for f in files) / 3600.0
    rejected = [] if private else sorted({p.name for p in edfs} - {f["filename"] for f in files})
    return dict(subject=sid, mode=mode, mains=session.mains_resolved, files=len(files), edf_present=len(edfs),
                rejected=" ".join(rejected), hours=round(hours, 4), seconds=round(elapsed, 1),
                s_per_hour=round(elapsed / max(hours, 1e-9), 2),
                peak_mem_mb=round(MEM.peak, 0) if MEM else "")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", required=True, help="folder holding chbNN/ subfolders of EDF files")
    ap.add_argument("--subjects", nargs="*", default=[])
    ap.add_argument("--all", action="store_true", help="the 8 test subjects (application tier)")
    ap.add_argument("--append", action="store_true", help="add to a database that already holds subjects")
    ap.add_argument("--mode", default="session", choices=list(db.ENGINE_MODES))
    ap.add_argument("--mains", default="auto", help="auto | 50 | 60")
    ap.add_argument("--interpolate", action="store_true")
    ap.add_argument("--private-dir", default=None, help="every EDF of this folder as its own private study")
    ap.add_argument("--private-prefix", default="clin")
    ap.add_argument("--log", default=str(um.UPLOAD_DIR / "_ingest_log_c5c.csv"))   # C5c columns (+ peak_mem_mb)
    ap.add_argument("--id-suffix", default="", help="store each subject as <subject><suffix> (e.g. -file)")
    ap.add_argument("--max-gb", type=float, default=None, help="stop (exit 3) above this memory of the ingest")
    a = ap.parse_args()
    global MEM
    try:
        MEM = TreeMemory(a.max_gb * 1000 if a.max_gb else None)
    except ImportError:
        if a.max_gb:
            raise SystemExit("STOP: --max-gb needs psutil")
    subjects = TEST_SUBJECTS if a.all else a.subjects
    if not subjects and not a.private_dir:
        raise SystemExit("STOP: no subject given")
    db.init_db()
    existing = [s["id"] for s in db.list_subjects()]
    if existing and not a.append:
        raise SystemExit(f"STOP: the database already holds {existing}; the application tier needs a clean "
                         "database (move szscan.db and uploads/ aside first), or pass --append.")
    jobs = [(s, dict(edf_dir=Path(a.dataset) / s, sid=s + a.id_suffix)) for s in subjects
            if s + a.id_suffix not in existing]
    if a.private_dir:
        priv = sorted((p for p in Path(a.private_dir).iterdir() if p.is_file() and p.suffix.lower() == ".edf"),
                      key=lambda p: -p.stat().st_size)
        jobs += [(f"{a.private_prefix}{i + 1:02d}", dict(edfs=[p], private=True)) for i, p in enumerate(priv)
                 if f"{a.private_prefix}{i + 1:02d}" not in existing]
    rows = []
    for s, kw in jobs:
        print(f"{s}: ingesting ...", flush=True)
        r = ingest(s, mode=a.mode, mains=a.mains, interpolate=a.interpolate, **kw)
        rows.append(r)
        print(f"{r['subject']}: {r['files']} files ({r['edf_present']} EDF present), {r['hours']:.2f} h, "
              f"{r['seconds']:.0f} s, {r['s_per_hour']:.1f} s per hour of EEG, peak memory {r['peak_mem_mb']} MB"
              + (f", rejected: {r['rejected']}" if r["rejected"] else ""), flush=True)
        log = Path(a.log)
        log.parent.mkdir(parents=True, exist_ok=True)
        new = not log.exists() or log.stat().st_size == 0
        with open(log, "a", newline="") as fh:            # appended across runs (C5c)
            w = csv.DictWriter(fh, fieldnames=list(r))
            if new:
                w.writeheader()
            w.writerow(r)
    tot_h = sum(r["hours"] for r in rows); tot_s = sum(r["seconds"] for r in rows)
    print(f"TOTAL {len(rows)} subjects, {tot_h:.2f} h, {tot_s:.0f} s, {tot_s / max(tot_h, 1e-9):.1f} s per hour of EEG")


if __name__ == "__main__":
    sys.exit(main())
