"""upload_manager.py — the Create New panel's server-side state machine.

Scope (Step 3, DEMO_BUILD_HANDOFF.md §6 row 3 / SZSCAN_SPEC_v5.md §5.5): one in-process
singleton session backing the Create New panel, enforcing the system-wide "exactly one
subject processed at a time, even minimized" rule (SPEC §5.5) and running the two-phase
pipeline from pipeline_demo.py as files upload and as "Process" is clicked.

Deliberately NOT a multi-session manager: SPEC's own constraint (one subject in flight,
system-wide) means a single module-level `_current` slot is the correct amount of state,
not an accident of laziness. A session survives across HTTP requests as plain Python
process memory — fine for this single-process, single-admin-user dev demo (CLAUDE.md: the
whole auth/session model here is explicitly not a real security mechanism either).
"""
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

import db
import pipeline_demo as pd

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
_WORKER_SCRIPT = Path(__file__).resolve().parent / "pipeline_worker.py"

# Phase B and stage-2 Process run in a genuinely separate OS process (subprocess.Popen
# launching pipeline_worker.py), not a thread of the API server and not a
# concurrent.futures.ProcessPoolExecutor worker either. Measured cause: on this Windows dev
# machine, invoking the GAE/PELT pipeline from either a threading.Thread OR a
# ProcessPoolExecutor worker hangs at 0% CPU indefinitely — reproducible only when launched
# from inside this uvicorn-hosted process (an identical call from a plain, non-uvicorn
# Python process never hangs, including a ProcessPoolExecutor there). A subprocess.Popen
# child is a plain CreateProcess call with none of multiprocessing's spawn bootstrap or
# asyncio-loop inheritance, and that reliably does not hang. Phase A (mne + scipy filtering
# only, no torch) does not show this and stays a plain background thread (see _run_phase_a)
# so its cooperative cancel_check flag keeps working (that needs shared memory a subprocess
# wouldn't have).

REJECTED_SUBJECT_MESSAGE = "This demo is restricted to the held-out test subjects."
REJECTED_FILE_MESSAGE = "File rejected — unsupported format or channel configuration."
BLOCKED_MESSAGE = "Processing another subject. Please wait before creating a new one"


class UploadManagerError(Exception):
    """Carries the exact user-facing toast text (SZSCAN_SPEC_v5.md §2 / §5.5)."""

    def __init__(self, toast: str, status_code: int = 400):
        super().__init__(toast)
        self.toast = toast
        self.status_code = status_code


@dataclass
class FileEntry:
    filename: str
    path: Path
    status: str = "uploading"  # uploading | uploaded | error
    error: Optional[str] = None
    cancel_flag: threading.Event = field(default_factory=threading.Event)
    phase_a: Optional[pd.PhaseAResult] = None
    score: Optional[object] = None


class UploadSession:
    def __init__(self, project_id: str, memo: str):
        # CC_STEP3_FIX3_PROMPT.md: Project ID/Memo stay editable in the frontend for the
        # whole draft — session_id is the stable, immutable key upload storage is keyed by
        # (see add_file), independent of whatever the user later retypes into Project ID.
        # `project_id`/`memo` below are just the session's current values; start_process()
        # is what re-validates and locks them in for good.
        self.session_id = secrets.token_hex(8)
        self.project_id = project_id
        self.memo = memo
        self.files: dict[str, FileEntry] = {}
        self.lock = threading.RLock()
        self.generation = 0
        self.phase_b_running = False
        self.phase_b_done = False
        self.processing = False
        self.done = False
        self.error: Optional[str] = None
        self.op_pen_mult: Optional[float] = None
        self.op_rate_per_day: Optional[float] = None

    def snapshot(self) -> dict:
        with self.lock:
            return {
                "project_id": self.project_id,
                "memo": self.memo,
                "files": [
                    {
                        "filename": f.filename,
                        "status": f.status,
                        "error": f.error,
                    }
                    for f in self.files.values()
                ],
                "phase_b_done": self.phase_b_done,
                "ready_to_process": (
                    len(self.files) > 0
                    and all(f.status == "uploaded" for f in self.files.values())
                    and not self.processing
                    and not self.done
                ),
                "processing": self.processing,
                "done": self.done,
                "error": self.error,
                "operating_point": (
                    {"pen_mult": self.op_pen_mult, "event_rate_per_day": self.op_rate_per_day}
                    if self.done
                    else None
                ),
            }


_manager_lock = threading.Lock()
_current: Optional[UploadSession] = None


def get_current() -> Optional[UploadSession]:
    return _current


def start_session(project_id: str, memo: str) -> UploadSession:
    global _current
    with _manager_lock:
        if _current is not None:
            raise UploadManagerError(BLOCKED_MESSAGE, status_code=409)
        if project_id not in db.ALLOWED_SUBJECTS:
            raise UploadManagerError(REJECTED_SUBJECT_MESSAGE, status_code=422)
        _current = UploadSession(project_id, memo)
        return _current


def discard_session() -> None:
    """Closing an idle draft (panel's × before Process has run) — drops everything, never
    touches the DB, and frees the system-wide lock."""
    global _current
    with _manager_lock:
        _current = None


def acknowledge_done() -> None:
    """Called once the frontend has shown the completion state and refetched the subject
    list — frees the lock for the next Create New. Kept separate from the background
    Process thread finishing so a slow poller can never miss the done=True transition."""
    global _current
    with _manager_lock:
        if _current is not None and _current.done:
            _current = None


def _draft_dir(session: UploadSession) -> Path:
    """Keyed by the session's immutable internal id, not the mutable Project ID text —
    see UploadSession.__init__ and CC_STEP3_FIX3_PROMPT.md §3."""
    return UPLOAD_DIR / f"_draft_{session.session_id}"


def add_file(session: UploadSession, filename: str, tmp_path: Path) -> None:
    dest_dir = _draft_dir(session)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename
    shutil.move(str(tmp_path), str(dest_path))

    entry = FileEntry(filename=filename, path=dest_path)
    with session.lock:
        session.files[filename] = entry
        session.phase_b_done = False
        session.generation += 1

    threading.Thread(target=_run_phase_a, args=(session, entry), daemon=True).start()


def _run_phase_a(session: UploadSession, entry: FileEntry) -> None:
    try:
        result = pd.process_file_phase_a(
            str(entry.path), cancel_check=entry.cancel_flag.is_set, cache_dir=entry.path.parent
        )
    except pd.CancelledError:
        with session.lock:
            session.files.pop(entry.filename, None)
            entry.path.unlink(missing_ok=True)
        return
    except pd.UnsupportedEdfError:
        with session.lock:
            entry.status = "error"
            entry.error = REJECTED_FILE_MESSAGE
        return
    except Exception as exc:  # pragma: no cover - unexpected pipeline failure
        with session.lock:
            entry.status = "error"
            entry.error = f"Unexpected error while reading this file: {exc}"
        return

    with session.lock:
        if session.files.get(entry.filename) is not entry:
            return  # removed/cancelled while phase A was running
        entry.phase_a = result
        entry.status = "uploaded"

    _maybe_run_phase_b(session)


def remove_file(session: UploadSession, filename: str) -> None:
    """Both SPEC §5.5 icons act through this: the spinning-circle stop button (status still
    'uploading' -> sets the cancel flag, the running Phase A thread removes itself) and the
    ✕ once-uploaded icon (status 'uploaded'/'error' -> removed immediately)."""
    with session.lock:
        entry = session.files.get(filename)
        if entry is None:
            return
        if entry.status == "uploading":
            entry.cancel_flag.set()
            return
        session.files.pop(filename, None)
        session.phase_b_done = False
        session.generation += 1
        if entry.path.exists():
            entry.path.unlink()

    _maybe_run_phase_b(session)


def poll_tick(session: UploadSession) -> None:
    """Called on every GET /api/uploads/current (see main.py) as a self-healing safety net.

    Observed on this Windows dev machine: rarely (not reproduced with any known trigger),
    a file finishing Phase A does not end up launching Phase B even though every file is
    already 'uploaded' — no exception is logged, and re-entering the exact same check from
    here always immediately proceeds correctly. Since the frontend polls this endpoint every
    couple of seconds anyway, re-running the (idempotent, lock-guarded) trigger check on every
    poll bounds the worst case to one poll interval regardless of whatever the root cause is,
    without needing to chase a race that would not reproduce under deliberate testing.
    """
    _maybe_run_phase_b(session)


def _maybe_run_phase_b(session: UploadSession) -> None:
    with session.lock:
        if not session.files:
            return
        if any(f.status == "uploading" for f in session.files.values()):
            return
        if session.phase_b_running or session.phase_b_done:
            return
        session.phase_b_running = True
        gen = session.generation
        filtered_paths = {
            fn: str(f.phase_a.filtered_path)
            for fn, f in session.files.items()
            if f.status == "uploaded"
        }
    if not filtered_paths:
        with session.lock:
            session.phase_b_running = False
        return

    threading.Thread(
        target=_run_phase_b, args=(session, gen, filtered_paths), daemon=True
    ).start()


def _run_worker(mode: str, payload: dict, out_suffix: str) -> Path:
    """Launches pipeline_worker.py as a separate process, waits for it to finish, and
    returns the path to its output file (caller reads and deletes it). Raises
    RuntimeError with stderr's tail if the worker exits non-zero."""
    work_dir = UPLOAD_DIR / "_work"
    work_dir.mkdir(parents=True, exist_ok=True)
    in_fd, in_name = tempfile.mkstemp(suffix=".in.json", dir=str(work_dir))
    with open(in_fd, "w") as fh:
        json.dump(payload, fh)
    out_fd, out_name = tempfile.mkstemp(suffix=out_suffix, dir=str(work_dir))
    os.close(out_fd)

    try:
        proc = subprocess.run(
            [sys.executable, str(_WORKER_SCRIPT), mode, in_name, out_name],
            capture_output=True, text=True, cwd=str(_WORKER_SCRIPT.parent),
        )
        if proc.returncode != 0:
            raise RuntimeError(f"{mode} worker failed: {proc.stderr[-2000:]}")
        return Path(out_name)
    finally:
        Path(in_name).unlink(missing_ok=True)


def _run_phase_b(session: UploadSession, gen: int, filtered_paths: dict) -> None:
    try:
        out_path = _run_worker("phase_b", {"filtered_paths": filtered_paths}, ".npz")
        with np.load(out_path) as data:
            scores = {fn: data[fn] for fn in data.files}
        out_path.unlink(missing_ok=True)
    except Exception as exc:  # pragma: no cover - unexpected pipeline failure
        with session.lock:
            session.phase_b_running = False
            session.error = f"Processing error: {exc}"
        return

    with session.lock:
        session.phase_b_running = False
        if gen != session.generation:
            # The file set changed mid-run (a file was added/removed/cancelled); whichever
            # mutation did that already re-triggered (or will re-trigger) another run.
            return
        for fn, score in scores.items():
            if fn in session.files:
                session.files[fn].score = score
        session.phase_b_done = True


def start_process(session: UploadSession, project_id: str, memo: str) -> None:
    """SZSCAN_SPEC_v5.md §5.5 / CC_STEP3_FIX3_PROMPT.md: Project ID/Memo are editable
    everywhere up to this call — `project_id`/`memo` here are whatever is in the fields at
    the exact instant PROCESS is clicked, not whatever the session started with. This is
    the allowlist's one point of final authority: if it fails, nothing is bound or locked
    (the session keeps its previous project_id/memo untouched, files stay listed, caller
    gets the same rejection toast as the early upload-time check) and the caller can just
    fix the field and click PROCESS again."""
    project_id = project_id.strip()
    with session.lock:
        if session.processing or session.done:
            raise UploadManagerError("Already processing.", status_code=409)
        if not session.files or any(f.status != "uploaded" for f in session.files.values()):
            raise UploadManagerError("Not all files have finished uploading yet.", status_code=409)
        if project_id not in db.ALLOWED_SUBJECTS:
            raise UploadManagerError(REJECTED_SUBJECT_MESSAGE, status_code=422)
        session.project_id = project_id
        session.memo = memo
        session.processing = True

    threading.Thread(target=_wait_phase_b_then_process, args=(session,), daemon=True).start()


def _finalize_draft_dir(session: UploadSession) -> None:
    """Relocates the session's session-id-keyed draft directory to the conventional
    uploads/{project_id}/ path (CC_STEP3_REPORT.md §3 — what Step 4+ expects) now that
    start_process has validated and locked in the final Project ID. Only called after
    phase_b_done is confirmed, so nothing (the phase_b worker subprocess included) is still
    reading from the draft directory when it's moved."""
    draft_dir = _draft_dir(session)
    if not draft_dir.exists():
        return
    final_dir = UPLOAD_DIR / session.project_id
    if final_dir.exists():
        shutil.rmtree(final_dir, ignore_errors=True)
    shutil.move(str(draft_dir), str(final_dir))


def _wait_phase_b_then_process(session: UploadSession) -> None:
    """SZSCAN_SPEC_v5.md §5.5 gates PROCESS on upload completion only ("every file shows
    the uploaded icon"), not on Phase B (the subject-wide z-score/LedoitWolf fit + per-file
    scoring that must run before PELT — see pipeline_demo.py / CC_STEP3_FIX2_PROMPT.md).
    Phase A finishing (files all 'uploaded') and Phase B finishing are two different
    moments; if Phase B is still running when the user clicks PROCESS, this waits for it
    behind the already-existing full-panel "Processing subject..." loading state instead
    of the button itself staying disabled."""
    _maybe_run_phase_b(session)  # idempotent nudge — same missed-trigger safety poll_tick guards
    while True:
        with session.lock:
            if session.error:
                session.processing = False
                return
            if session.phase_b_done:
                scores = {fn: f.score for fn, f in session.files.items()}
                phase_a_by_filename = {fn: f.phase_a for fn, f in session.files.items()}
                break
        time.sleep(0.3)

    _finalize_draft_dir(session)
    _run_process(session, scores, phase_a_by_filename)


def _run_process(session: UploadSession, scores: dict, phase_a_by_filename: dict) -> None:
    try:
        score_npz = UPLOAD_DIR / "_work"
        score_npz.mkdir(parents=True, exist_ok=True)
        score_npz_fd, score_npz_name = tempfile.mkstemp(suffix=".npz", dir=str(score_npz))
        os.close(score_npz_fd)
        np.savez(score_npz_name, **scores)

        out_path = _run_worker("process_events", {"score_npz_path": score_npz_name}, ".json")
        Path(score_npz_name).unlink(missing_ok=True)
        result = json.loads(out_path.read_text())
        out_path.unlink(missing_ok=True)

        op_pen_mult = result["pen_mult"]
        op_rate_per_day = result["event_rate_per_day"]
        file_events = result["events"]  # {filename: [[onset_sec, offset_sec], ...]}

        files_payload = []
        events_payload = {}
        for fn, phase_a in phase_a_by_filename.items():
            files_payload.append(
                {
                    "filename": fn,
                    "start_time": phase_a.start_time.isoformat(),
                    "duration_seconds": phase_a.file_duration_seconds,
                }
            )
            events_payload[fn] = [
                {"onset_sec": onset, "offset_sec": offset}
                for onset, offset in file_events.get(fn, [])
            ]

        db.create_subject_with_files(session.project_id, session.memo, files_payload, events_payload)
    except Exception as exc:  # pragma: no cover - unexpected pipeline/DB failure
        with session.lock:
            session.processing = False
            session.error = f"Processing error: {exc}"
        return

    with session.lock:
        session.processing = False
        session.done = True
        session.op_pen_mult = op_pen_mult
        session.op_rate_per_day = op_rate_per_day


def save_upload_to_tmp(data: bytes) -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(suffix=".edf", dir=str(UPLOAD_DIR))
    with open(fd, "wb") as fh:
        fh.write(data)
    return Path(tmp_name)
