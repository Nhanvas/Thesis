"""Tier 2 driver — resumes CC_REPORT_HANDBACK_PART3_PROMPT.md from chb06 onward.
Real HTTP flow only (login, sequential per-file upload POSTs, Process, poll), mirroring
web_demo/frontend/src/api.js. chb03 is already done and is NOT touched by this script.
"""
import glob
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

import requests

BASE = "http://127.0.0.1:8000"
DATASET_ROOT = "F:/Study/Thesis/Dataset/CHB-MIT"
MEMO = "Tier 2 -- frozen build szscan-frozen-v1"
LOG_PATH = os.path.join(os.path.dirname(__file__), "tier2_progress.log")

SUBJECTS = ["chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]


def log(msg):
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S.%f')[:-3]} UTC] {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def real_files(subject):
    pattern = re.compile(rf"^{re.escape(subject)}[a-z]?_[0-9]+\.edf$")
    d = os.path.join(DATASET_ROOT, subject)
    names = sorted(f for f in os.listdir(d) if pattern.match(f))
    return [os.path.join(d, n) for n in names]


def login(session):
    user = pw = None
    with open("F:/Study/Thesis/Code/web_demo/backend/.env", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("ADMIN_USER="):
                user = line.strip().split("=", 1)[1]
            elif line.startswith("ADMIN_PASS="):
                pw = line.strip().split("=", 1)[1]
    r = session.post(f"{BASE}/api/login", json={"username": user, "password": pw}, timeout=30)
    r.raise_for_status()
    log(f"login ok: {r.json()}")


def get_upload(session):
    r = session.get(f"{BASE}/api/uploads/current", timeout=30)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def process_subject(session, subject):
    files = real_files(subject)
    log(f"=== {subject}: {len(files)} real files on disk ===")
    if not files:
        log(f"{subject}: NO REAL FILES FOUND -- skipping, needs human attention")
        return {"subject": subject, "skipped": "no real files found on disk"}

    cur = get_upload(session)
    if cur is not None:
        log(f"{subject}: a live session already exists ({cur.get('project_id')}) -- resume-safety check")
        if cur.get("project_id") != subject:
            log(f"{subject}: live session belongs to a DIFFERENT subject ({cur.get('project_id')}) -- STOP, needs human decision")
            raise RuntimeError(f"unexpected live session for {cur.get('project_id')} while starting {subject}")
    else:
        r = session.post(f"{BASE}/api/uploads/current", json={"project_id": subject, "memo": MEMO}, timeout=30)
        r.raise_for_status()
        log(f"{subject}: started upload session -- {r.json()}")
        cur = get_upload(session)

    already_named = {f["filename"] for f in cur["files"]} if cur else set()
    t_upload_start = time.time()
    failures = []
    for path in files:
        fname = os.path.basename(path)
        if fname in already_named:
            log(f"{subject}: {fname} already present in session (resume) -- skip re-upload")
            continue
        with open(path, "rb") as fh:
            r = session.post(
                f"{BASE}/api/uploads/current/files",
                files={"file": (fname, fh, "application/octet-stream")},
                timeout=1800,
            )
        if r.status_code >= 400:
            body = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
            log(f"{subject}: UPLOAD FAILED for {fname}: HTTP {r.status_code} {body}")
            failures.append({"filename": fname, "phase": "upload", "error": str(body)})
        else:
            log(f"{subject}: uploaded {fname}")

    # poll until every file is 'uploaded' (or 'error') -- i.e. Phase A done for all
    while True:
        cur = get_upload(session)
        if cur is None:
            raise RuntimeError(f"{subject}: session disappeared while waiting for uploads")
        statuses = {f["filename"]: f["status"] for f in cur["files"]}
        if all(s in ("uploaded", "error") for s in statuses.values()):
            break
        time.sleep(3)
    for f in cur["files"]:
        if f["status"] == "error":
            log(f"{subject}: {f['filename']} errored during Phase A: {f.get('error')}")
            failures.append({"filename": f["filename"], "phase": "phase_a", "error": f.get("error")})
    t_upload_end = time.time()
    log(f"{subject}: upload phase done in {t_upload_end - t_upload_start:.1f}s, "
        f"{sum(1 for s in statuses.values() if s == 'uploaded')} uploaded, "
        f"{sum(1 for s in statuses.values() if s == 'error')} errored")

    if not cur["ready_to_process"]:
        log(f"{subject}: NOT ready_to_process after upload phase -- STOP, needs human decision")
        raise RuntimeError(f"{subject}: not ready_to_process ({cur})")

    r = session.post(f"{BASE}/api/uploads/current/process", json={"project_id": subject, "memo": MEMO}, timeout=30)
    r.raise_for_status()
    log(f"{subject}: Process started")
    t_process_start = time.time()
    while True:
        cur = get_upload(session)
        if cur is None:
            raise RuntimeError(f"{subject}: session disappeared while processing")
        if cur.get("error"):
            log(f"{subject}: PROCESS ERROR: {cur['error']}")
            raise RuntimeError(f"{subject}: process error: {cur['error']}")
        if cur.get("done"):
            break
        time.sleep(5)
    t_process_end = time.time()
    log(f"{subject}: Process done in {t_process_end - t_process_start:.1f}s, "
        f"operating_point={cur.get('operating_point')}")

    r = session.post(f"{BASE}/api/uploads/current/acknowledge", timeout=30)
    r.raise_for_status()
    log(f"{subject}: acknowledged, lock freed")

    return {
        "subject": subject,
        "real_file_count": len(files),
        "uploaded": sum(1 for s in statuses.values() if s == "uploaded"),
        "failures": failures,
        "upload_s": t_upload_end - t_upload_start,
        "process_s": t_process_end - t_process_start,
        "operating_point": cur.get("operating_point"),
    }


def main():
    session = requests.Session()
    login(session)
    cur = get_upload(session)
    if cur is not None:
        log(f"PRE-FLIGHT: live session found at startup: {cur.get('project_id')} -- resume-safety")
    else:
        log("PRE-FLIGHT: no live session at startup")

    results = []
    for subject in SUBJECTS:
        try:
            res = process_subject(session, subject)
        except requests.exceptions.ConnectionError as exc:
            log(f"{subject}: STOPPED -- lost connection to backend (possible OOM kill, like the "
                f"earlier chb06 run): {exc!r}")
            results.append({"subject": subject, "exception": f"connection lost: {exc!r}"})
            with open(os.path.join(os.path.dirname(__file__), "tier2_results.json"), "w") as fh:
                json.dump(results, fh, indent=2)
            raise
        except Exception as exc:
            log(f"{subject}: STOPPED due to exception: {exc!r}")
            results.append({"subject": subject, "exception": repr(exc)})
            with open(os.path.join(os.path.dirname(__file__), "tier2_results.json"), "w") as fh:
                json.dump(results, fh, indent=2)
            raise
        results.append(res)
        with open(os.path.join(os.path.dirname(__file__), "tier2_results.json"), "w") as fh:
            json.dump(results, fh, indent=2)
    log("=== ALL SUBJECTS DONE ===")


if __name__ == "__main__":
    main()
