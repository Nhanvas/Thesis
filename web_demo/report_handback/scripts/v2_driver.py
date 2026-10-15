"""Overnight Part 3 v2 driver -- real HTTP flow (login, sequential per-file upload POSTs,
Process, poll), same method as CC_STEP9_PHASE2/CC_CHB13_REUPLOAD, per
web_demo/CC_REPORT_HANDBACK_PART3_PROMPT.md sections 2-4 and web_demo/CC_OVERNIGHT_RUN_PROMPT.md
step D. Does not touch src/*.py, does not review events, does not add Human events.
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE = "http://127.0.0.1:8000"
REPO_ROOT = Path("F:/Study/Thesis/Code")
BACKEND_DIR = REPO_ROOT / "web_demo" / "backend"
load_dotenv(BACKEND_DIR / ".env")
DATASET_ROOT = Path("F:/Study/Thesis/Dataset/CHB-MIT")
MEMO = "frozen build szscan-frozen-v2"
SUBJECTS = ["chb06", "chb03", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]

SCRATCH = Path(r"F:/tmp/claude/F--Study-Thesis-Code/eb45abf2-8a65-4fbf-a6bc-27598250282c/scratchpad")
LOG_PATH = SCRATCH / "driver_log.txt"
RESULTS_PATH = SCRATCH / "driver_results.json"
STATE_PATH = SCRATCH / "current_subject.txt"
PID_PATH = SCRATCH / "backend_pid.txt"

ADMIN_USER = os.environ["ADMIN_USER"]
ADMIN_PASS = os.environ["ADMIN_PASS"]

FILE_RE_TEMPLATE = r"^{subject}[a-z]?_[0-9]+\.edf$"

session = requests.Session()
results = {}
if RESULTS_PATH.exists():
    try:
        results = json.loads(RESULTS_PATH.read_text())
    except Exception:
        results = {}


def log(msg):
    ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    line = f"[{ts} UTC] {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def save_results():
    RESULTS_PATH.write_text(json.dumps(results, indent=2))


def set_state(subject):
    STATE_PATH.write_text(subject)


def list_subject_files(subject):
    pattern = re.compile(FILE_RE_TEMPLATE.format(subject=subject))
    d = DATASET_ROOT / subject
    return sorted(p for p in d.iterdir() if pattern.match(p.name))


def backend_pid():
    try:
        return int(PID_PATH.read_text().strip())
    except Exception:
        return None


def wait_for_backend(timeout=120):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{BASE}/api/session", timeout=5)
            if r.status_code in (200, 401):
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)
    return False


def start_backend():
    log("Starting backend: python -m uvicorn main:app --port 8000")
    proc = subprocess.Popen(
        ["python", "-m", "uvicorn", "main:app", "--port", "8000"],
        cwd=str(BACKEND_DIR),
        stdout=open(SCRATCH / "backend_restart.log", "a"),
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )
    PID_PATH.write_text(str(proc.pid))
    if not wait_for_backend():
        raise RuntimeError("Backend did not come up after restart")
    log(f"Backend up, pid={proc.pid}")
    return proc.pid


def login():
    r = session.post(f"{BASE}/api/login", json={"username": ADMIN_USER, "password": ADMIN_PASS}, timeout=15)
    r.raise_for_status()
    log("Logged in")


def is_backend_alive():
    try:
        r = requests.get(f"{BASE}/api/session", timeout=5)
        return r.status_code in (200, 401)
    except requests.exceptions.RequestException:
        return False


def ensure_backend_alive_or_restart():
    if is_backend_alive():
        return False  # no restart needed
    log("Backend unreachable -- waiting 15s and re-checking before declaring it down")
    time.sleep(15)
    if is_backend_alive():
        return False
    log("Backend confirmed down. Restarting the SAME checkout with the SAME command/settings (no code/setting change).")
    start_backend()
    login()
    return True  # restarted


def clear_any_stale_session():
    """Best-effort: if a session from a previous crashed attempt is sitting there, get rid
    of it (discard, not delete-processed-data) so start_upload doesn't 409. Only acts on a
    session that isn't mid-Process (discard_upload already refuses that itself)."""
    try:
        r = session.get(f"{BASE}/api/uploads/current", timeout=10)
    except requests.exceptions.RequestException:
        return
    if r.status_code == 404:
        return
    snap = r.json()
    if snap.get("done"):
        session.post(f"{BASE}/api/uploads/current/acknowledge", timeout=10)
        log("Acknowledged a leftover completed session before starting fresh.")
        return
    if not snap.get("processing"):
        try:
            dr = session.delete(f"{BASE}/api/uploads/current", timeout=10)
            log(f"Discarded a leftover non-processing session ({dr.status_code}).")
        except requests.exceptions.RequestException:
            pass


def upload_file(subject, path, attempt_limit=4):
    for attempt in range(1, attempt_limit + 1):
        try:
            with open(path, "rb") as fh:
                r = session.post(
                    f"{BASE}/api/uploads/current/files",
                    files={"file": (path.name, fh, "application/octet-stream")},
                    timeout=600,
                )
            if r.status_code == 200:
                return None
            else:
                msg = f"{r.status_code} {r.text[:300]}"
                log(f"{subject}: upload FAILED for {path.name}: {msg}")
                return msg
        except requests.exceptions.RequestException as e:
            log(f"{subject}: upload exception for {path.name}, attempt {attempt}/{attempt_limit}: {e}")
            if not is_backend_alive():
                raise  # let caller treat this as a possible OOM/crash
            time.sleep(5 * attempt)
    return f"gave up after {attempt_limit} attempts"


def process_subject(subject):
    if subject in results and results[subject].get("status") == "ok":
        log(f"{subject}: already recorded as ok, skipping")
        return

    set_state(subject)
    files = list_subject_files(subject)
    log(f"{subject}: {len(files)} real files found on disk under {DATASET_ROOT / subject}")
    if not files:
        results[subject] = {"status": "no_files_found"}
        save_results()
        return

    clear_any_stale_session()

    t0 = time.time()
    try:
        r = session.post(f"{BASE}/api/uploads/current", json={"project_id": subject, "memo": MEMO}, timeout=30)
    except requests.exceptions.RequestException as e:
        log(f"{subject}: could not even start session ({e}) -- treating as backend down")
        if ensure_backend_alive_or_restart():
            results[subject] = {"status": "oom_or_crash_before_start", "error": str(e)}
        else:
            results[subject] = {"status": "start_failed", "error": str(e)}
        save_results()
        return

    if r.status_code != 200:
        log(f"{subject}: start_upload failed {r.status_code} {r.text[:300]}")
        results[subject] = {"status": "start_failed", "error": f"{r.status_code} {r.text[:300]}"}
        save_results()
        return

    log(f"{subject}: session started, uploading {len(files)} files sequentially")
    failed_files = []
    crashed = False
    for p in files:
        try:
            err = upload_file(subject, p)
        except requests.exceptions.RequestException as e:
            log(f"{subject}: backend appears down mid-upload of {p.name}: {e}")
            crashed = True
            break
        if err:
            failed_files.append({"file": p.name, "error": err})

    if crashed:
        restarted = ensure_backend_alive_or_restart()
        results[subject] = {
            "status": "oom_or_crash",
            "phase": "upload",
            "files_attempted": len(files),
            "failed_files": failed_files,
            "backend_restarted": restarted,
        }
        save_results()
        log(f"{subject}: recorded as OOM/crash during upload; moving on to next subject.")
        return

    t_upload_all_sent = time.time()
    log(f"{subject}: all {len(files)} upload POSTs sent in {t_upload_all_sent - t0:.1f}s, {len(failed_files)} file(s) rejected outright; "
        f"now waiting for Phase A (background per-file processing, concurrency 2) to settle every file to uploaded/error")

    # Phase A runs in background threads on the backend (bounded by
    # _PHASE_A_MAX_CONCURRENCY=2), so a file's upload POST returning 200 only means it was
    # accepted, not that it has finished Phase A yet. Poll until every file the session
    # knows about is no longer "uploading" before judging readiness -- checking once,
    # immediately after the last POST, is wrong and was the bug in the first attempt at
    # this run (recorded chb06 as "not_ready" with 12/18 files still mid-Phase-A).
    poll_fail_streak = 0
    phase_a_timeout_s = 3600  # generous; a real crash is caught via poll_fail_streak below
    phase_a_deadline = time.time() + phase_a_timeout_s
    snap = None
    while True:
        if time.time() > phase_a_deadline:
            log(f"{subject}: Phase A did not settle within {phase_a_timeout_s}s -- treating as stuck/failed")
            results[subject] = {"status": "phase_a_timeout", "failed_files": failed_files, "snapshot": snap}
            save_results()
            return
        try:
            r = session.get(f"{BASE}/api/uploads/current", timeout=15)
            poll_fail_streak = 0
        except requests.exceptions.RequestException as e:
            poll_fail_streak += 1
            log(f"{subject}: poll exception while waiting for Phase A ({poll_fail_streak}): {e}")
            if poll_fail_streak >= 6:
                restarted = ensure_backend_alive_or_restart()
                results[subject] = {
                    "status": "oom_or_crash", "phase": "phase_a_wait",
                    "failed_files": failed_files, "backend_restarted": restarted,
                }
                save_results()
                log(f"{subject}: recorded as OOM/crash while Phase A was still running; moving on.")
                return
            time.sleep(5)
            continue

        if r.status_code != 200:
            log(f"{subject}: poll returned {r.status_code} while waiting for Phase A: {r.text[:300]}")
            time.sleep(5)
            continue

        snap = r.json()
        still_uploading = [f["filename"] for f in snap["files"] if f["status"] == "uploading"]
        if not still_uploading:
            break
        time.sleep(5)

    t_upload_done = time.time()
    per_file_errors = [f for f in snap["files"] if f["status"] == "error"]
    for f in per_file_errors:
        log(f"{subject}: file-level error recorded by Phase A for {f['filename']}: {f['error']}")
        failed_files.append({"file": f["filename"], "error": f["error"]})
        # Drop it from the session so the remaining, successfully-uploaded files can still
        # be Processed -- per instruction ("record it... and continue"), a single bad file
        # must not block the whole subject.
        try:
            session.delete(f"{BASE}/api/uploads/current/files/{f['filename']}", timeout=15)
        except requests.exceptions.RequestException as e:
            log(f"{subject}: could not remove errored file {f['filename']} from session: {e}")
    log(f"{subject}: upload+Phase A settled in {t_upload_done - t0:.1f}s, {len(failed_files)} file(s) failed total")

    try:
        snap = session.get(f"{BASE}/api/uploads/current", timeout=15).json()
    except requests.exceptions.RequestException as e:
        log(f"{subject}: backend down re-checking readiness after dropping errored files: {e}")
        restarted = ensure_backend_alive_or_restart()
        results[subject] = {"status": "oom_or_crash", "phase": "post_error_removal", "failed_files": failed_files, "backend_restarted": restarted}
        save_results()
        return

    if not snap.get("ready_to_process"):
        log(f"{subject}: not ready_to_process even after removing errored files -- snapshot: {json.dumps(snap)[:800]}")
        results[subject] = {"status": "not_ready", "failed_files": failed_files, "snapshot": snap}
        save_results()
        return

    try:
        r = session.post(f"{BASE}/api/uploads/current/process", json={"project_id": subject, "memo": MEMO}, timeout=30)
    except requests.exceptions.RequestException as e:
        log(f"{subject}: backend down calling Process: {e}")
        restarted = ensure_backend_alive_or_restart()
        results[subject] = {"status": "oom_or_crash", "phase": "process_call", "failed_files": failed_files, "backend_restarted": restarted}
        save_results()
        return

    if r.status_code != 200:
        log(f"{subject}: Process call failed {r.status_code} {r.text[:300]}")
        results[subject] = {"status": "process_failed", "error": f"{r.status_code} {r.text[:300]}", "failed_files": failed_files}
        save_results()
        return

    t_process_start = time.time()
    log(f"{subject}: Process started, polling...")

    poll_fail_streak = 0
    while True:
        time.sleep(5)
        try:
            r = session.get(f"{BASE}/api/uploads/current", timeout=15)
            poll_fail_streak = 0
        except requests.exceptions.RequestException as e:
            poll_fail_streak += 1
            log(f"{subject}: poll exception ({poll_fail_streak}): {e}")
            if poll_fail_streak >= 6:  # ~30-60s of sustained failure -> treat as crash
                restarted = ensure_backend_alive_or_restart()
                results[subject] = {
                    "status": "oom_or_crash",
                    "phase": "processing",
                    "elapsed_before_crash_s": time.time() - t_process_start,
                    "failed_files": failed_files,
                    "backend_restarted": restarted,
                }
                save_results()
                log(f"{subject}: recorded as OOM/crash during Process; moving on to next subject.")
                return
            continue

        if r.status_code != 200:
            log(f"{subject}: poll returned {r.status_code}: {r.text[:300]}")
            continue
        snap = r.json()
        if snap.get("error"):
            log(f"{subject}: processing error field set: {snap['error']}")
            results[subject] = {"status": "process_error", "error": snap["error"], "failed_files": failed_files}
            save_results()
            return
        if snap.get("done"):
            break

    t_done = time.time()
    log(f"{subject}: DONE. upload={t_upload_done - t0:.1f}s process={t_done - t_process_start:.1f}s total={t_done - t0:.1f}s op_point={snap.get('operating_point')}")

    results[subject] = {
        "status": "ok",
        "n_files_on_disk": len(files),
        "n_files_uploaded_ok": len(files) - len(failed_files),
        "failed_files": failed_files,
        "upload_s": round(t_upload_done - t0, 1),
        "process_s": round(t_done - t_process_start, 1),
        "total_s": round(t_done - t0, 1),
        "operating_point": snap.get("operating_point"),
        "t_start_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0)),
        "t_done_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t_done)),
    }
    save_results()

    try:
        session.post(f"{BASE}/api/uploads/current/acknowledge", timeout=15)
        log(f"{subject}: acknowledged, lock freed for next subject")
    except requests.exceptions.RequestException as e:
        log(f"{subject}: acknowledge failed ({e}); will attempt clear_any_stale_session next subject")


def main():
    login()
    set_state("")

    for i, subject in enumerate(SUBJECTS):
        log(f"=== Starting subject {i+1}/{len(SUBJECTS)}: {subject} ===")
        process_subject(subject)

        if subject == "chb06" and results.get("chb06", {}).get("status") == "ok":
            r6 = results["chb06"]
            hours = 66.74
            rate_s_per_h = r6["total_s"] / hours
            remaining_hours = 38 + 33 + 26 + 40 + 19 + 21 + 36  # chb03,13,14,15,16,17,18
            est_remaining_s = rate_s_per_h * remaining_hours
            finish = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + est_remaining_s))
            log(f"ESTIMATE after chb06: measured rate {rate_s_per_h:.2f}s/hour-of-EEG; "
                f"remaining {remaining_hours}h of EEG across 7 subjects -> "
                f"est. {est_remaining_s/60:.1f} min more -> estimated finish {finish}")

    set_state("")
    log("=== All subjects processed (or recorded as failed/skipped). Driver finished. ===")


if __name__ == "__main__":
    main()
