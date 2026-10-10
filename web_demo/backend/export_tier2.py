"""export_tier2.py — export every AI event of the application's database BEFORE any review, in
the format the thesis-side scorer reads (src/eval_application_events.py):

  {out}/files.csv              subject, file_name, duration_s, n_windows, status
  {out}/{subject}_events.csv   subject, file_name, event_id, onset_s, offset_s, source, review_status
  {out}/MANIFEST.txt           git commit of the build, export time, sha256 of each CSV

Reads the database and the per-file score cache only (n_windows = length of `{stem}.score.npy`);
never an annotation. No calendar date is written (start times are not exported). `status` is
"done" for every file: a file row exists only after its subject finished processing
(db.create_subject_with_files is atomic). Refuses to export if any AI event was already reviewed.

  python export_tier2.py --out ../report_handback/tier2_v4
"""
import argparse
import csv
import hashlib
import subprocess
import time
from pathlib import Path

import numpy as np

import db
import upload_manager as um


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"STOP: {out} is not empty (one export per run)")
    out.mkdir(parents=True, exist_ok=True)
    files_rows, n_events = [], 0
    for s in db.list_subjects():
        sid = s["id"]
        ev_rows = []
        for f in db.list_files_by_filename(sid):
            score = um.UPLOAD_DIR / sid / f"{Path(f['filename']).stem}.score.npy"
            n_win = int(np.load(score, mmap_mode="r").shape[0])
            files_rows.append(dict(subject=sid, file_name=f["filename"], duration_s=f["duration_seconds"],
                                   n_windows=n_win, status="done"))
            for e in db.list_events(f["id"]):
                if e["source"] == "AI" and e["review_status"] not in (None, "Unseen"):
                    raise SystemExit(f"STOP: {sid}/{f['filename']} event {e['id']} already reviewed "
                                     f"({e['review_status']}); the export must precede review")
                ev_rows.append(dict(subject=sid, file_name=f["filename"], event_id=e["id"],
                                    onset_s=e["onset_sec"], offset_s=e["offset_sec"], source=e["source"],
                                    review_status=e["review_status"] or ""))
        with open(out / f"{sid}_events.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["subject", "file_name", "event_id", "onset_s", "offset_s",
                                               "source", "review_status"])
            w.writeheader(); w.writerows(ev_rows)
        n_events += len(ev_rows)
    with open(out / "files.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["subject", "file_name", "duration_s", "n_windows", "status"])
        w.writeheader(); w.writerows(files_rows)
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                                cwd=str(Path(__file__).resolve().parent)).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no", "--", "web_demo/backend", "src"], capture_output=True,
                               text=True, cwd=str(Path(__file__).resolve().parents[2])).stdout.strip()
    except OSError:
        commit, dirty = "unknown", ""
    lines = [f"commit {commit}", f"uncommitted changes in web_demo/backend or src: {'YES' if dirty else 'no'}",
             f"exported {time.strftime('%H:%M:%S')} (local time; no date written)",
             f"subjects {len({r['subject'] for r in files_rows})}, files {len(files_rows)}, events {n_events}"]
    for p in sorted(out.glob("*.csv")):
        lines.append(f"sha256 {hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}")
    (out / "MANIFEST.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
