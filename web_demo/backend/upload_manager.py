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
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

import db
import pipeline_demo as pd

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
_WORKER_SCRIPT = Path(__file__).resolve().parent / "pipeline_worker.py"

# Phase A used to get one threading.Thread per file the instant its upload completed, with
# no cap -- fine for a couple of files, but a real 18-file/66h subject spawned 18 of them at
# once and OOM-killed the process (each Phase A thread holds a full mne Raw load + scipy
# filtering pass in memory). Bounding it to a small fixed pool caps peak memory to that many
# files' worth regardless of how many are queued or how fast they upload. 4 is a compromise
# between throughput and headroom on this CPU-only dev machine (CLAUDE.md) -- low enough that
# 4 concurrent Raw loads comfortably fit without re-creating the OOM, high enough that a
# typical multi-file subject still pipelines rather than serializing to 1-at-a-time.
_PHASE_A_MAX_CONCURRENCY = 2
_phase_a_executor = ThreadPoolExecutor(
    max_workers=_PHASE_A_MAX_CONCURRENCY, thread_name_prefix="phase_a"
)

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

# C5 Step 2: the subject allowlist of the defense demo is gone; a Project ID is a neutral label (db.SUBJECT_ID_RE).
REJECTED_SUBJECT_MESSAGE = ("Project ID: 1-32 letters, digits, '_' or '-' (start with a letter or digit). "
                            "Never type a patient's name.")
EXISTING_SUBJECT_MESSAGE = "A study with this Project ID already exists. Choose another Project ID."
REJECTED_SETTINGS_MESSAGE = "Unknown engine mode or mains frequency."
REJECTED_FILE_MESSAGE = "File rejected — unsupported format or channel configuration."
REJECTED_FILE_PREFIX = "File rejected — "
CHUNK_BYTES = 1 << 20


def _check_project_id(project_id: str) -> None:
    if not db.SUBJECT_ID_RE.match(project_id or ""):
        raise UploadManagerError(REJECTED_SUBJECT_MESSAGE, status_code=422)
    if db.get_subject(project_id) is not None:
        raise UploadManagerError(EXISTING_SUBJECT_MESSAGE, status_code=422)
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
    dist: Optional[object] = None  # [n_windows, 18] per-channel latent distance (Phase B)


class UploadSession:
    def __init__(self, project_id: str, memo: str, mode: str = "session", mains="auto", private: bool = False,
                 interpolate: bool = False):
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
        self.alarm_budget: Optional[float] = None  # p_i of the frozen system (never shown in the UI)
        # C5 Step 2 settings, fixed for the whole session (DESIGN_STEP2.md C2, C5, C7, C9)
        self.mode = mode                  # "session" | "file"
        self.mains = mains                # "auto" | 50.0 | 60.0
        self.mains_resolved: Optional[float] = None if mains == "auto" else float(mains)
        self.private = bool(private)
        self.interpolate = bool(interpolate)
        self.next_rec = 0                 # private sessions: neutral file names rec01.edf, rec02.edf, ...
        self.file_events: Optional[dict] = None   # file engine: events computed in Phase B
        self.file_meta: dict = {}

    def snapshot(self) -> dict:
        with self.lock:
            return {
                "project_id": self.project_id,
                "memo": self.memo,
                "mode": self.mode,
                "mains": self.mains,
                "mains_resolved": self.mains_resolved,
                "private": self.private,
                "interpolate": self.interpolate,
                "files": [
                    {
                        "filename": f.filename,
                        "status": f.status,
                        "error": f.error,
                        "notice": (f.phase_a.notice if f.phase_a is not None else ""),
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
            }


_manager_lock = threading.Lock()
_current: Optional[UploadSession] = None


def get_current() -> Optional[UploadSession]:
    return _current


def _norm_mains(mains):
    if mains in ("auto", None, ""):
        return "auto"
    try:
        v = float(mains)
    except (TypeError, ValueError):
        raise UploadManagerError(REJECTED_SETTINGS_MESSAGE, status_code=422)
    if v not in (50.0, 60.0):
        raise UploadManagerError(REJECTED_SETTINGS_MESSAGE, status_code=422)
    return v


def start_session(project_id: str, memo: str, mode: str = "session", mains="auto", private: bool = False,
                  interpolate: bool = False) -> UploadSession:
    global _current
    with _manager_lock:
        if _current is not None:
            raise UploadManagerError(BLOCKED_MESSAGE, status_code=409)
        _check_project_id(project_id)
        if mode not in db.ENGINE_MODES:
            raise UploadManagerError(REJECTED_SETTINGS_MESSAGE, status_code=422)
        _current = UploadSession(project_id, memo, mode, _norm_mains(mains), private, interpolate)
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


def neutral_name(session: UploadSession) -> str:
    """Private sessions: the next neutral file name (the original name is never stored, DESIGN_STEP2.md C9)."""
    with session.lock:
        session.next_rec += 1
        return f"rec{session.next_rec:02d}.edf"


def anonymise_header(path: Path) -> None:
    """Private sessions: overwrite the patient, recording, start-date and start-time fields of the app's own EDF copy
    (bytes 8-184 of the fixed header); the signals are untouched. The original upload is not changed."""
    with open(path, "r+b") as fh:
        head = fh.read(256)
        if len(head) < 256:
            return
        fh.seek(8)
        fh.write(b"X".ljust(80) + b"Startdate X X X X".ljust(80) + b"01.01.85" + b"00.00.00")


def add_file(session: UploadSession, filename: str, tmp_path: Path) -> None:
    if session.private:
        anonymise_header(tmp_path)
    dest_dir = _draft_dir(session)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename
    shutil.move(str(tmp_path), str(dest_path))

    entry = FileEntry(filename=filename, path=dest_path)
    with session.lock:
        session.files[filename] = entry
        session.phase_b_done = False
        session.generation += 1

    _phase_a_executor.submit(_run_phase_a, session, entry)


def _run_phase_a(session: UploadSession, entry: FileEntry) -> None:
    try:
        result = pd.process_file_phase_a(
            str(entry.path), cancel_check=entry.cancel_flag.is_set, cache_dir=entry.path.parent,
            mains=session.mains, interpolate=session.interpolate, private=session.private,
            mains_fallback=session.mains_resolved if session.mains == "auto" else None,
        )
    except pd.CancelledError:
        with session.lock:
            session.files.pop(entry.filename, None)
            entry.path.unlink(missing_ok=True)
        return
    except pd.UnsupportedEdfError as exc:
        with session.lock:
            entry.status = "error"
            entry.error = REJECTED_FILE_PREFIX + str(exc)
        return
    except Exception as exc:  # pragma: no cover - unexpected pipeline failure
        with session.lock:
            entry.status = "error"
            entry.error = ("Unexpected error while reading this file." if session.private
                           else f"Unexpected error while reading this file: {exc}")
        return

    # one mains frequency per session (the subject's statistics pool every file)
    with session.lock:
        if session.mains_resolved is None:
            session.mains_resolved = result.notch_hz
        elif session.mains_resolved != result.notch_hz:
            entry.status = "error"
            entry.error = (f"{REJECTED_FILE_PREFIX}this file's mains frequency ({result.notch_hz:.0f} Hz) differs "
                           f"from the session's ({session.mains_resolved:.0f} Hz).")
            return

    # Phase B and stage 2 read every array back from disk inside the worker process; keeping
    # the whole-file arrays in this server's memory for every uploaded file is not needed.
    result.filtered = None
    result.moments = None
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
        # App v3 item 1 (CC_PROMPT_APP_V3_CODE.md): Amendment A2 signal-loss flags, same
        # path-not-array convention as filtered_paths above.
        flag_paths = {
            fn: str(f.phase_a.flag_path)
            for fn, f in session.files.items()
            if f.status == "uploaded"
        }
        moments_paths = {
            fn: str(f.phase_a.moments_path)
            for fn, f in session.files.items()
            if f.status == "uploaded"
        }
        fsamp_paths = {
            fn: str(f.phase_a.fsamp_path)
            for fn, f in session.files.items()
            if f.status == "uploaded"
        }
        mode = session.mode
    if not filtered_paths:
        with session.lock:
            session.phase_b_running = False
        return

    threading.Thread(
        target=_run_phase_b, args=(session, gen, filtered_paths, flag_paths, moments_paths, fsamp_paths, mode),
        daemon=True,
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


def _run_phase_b(session: UploadSession, gen: int, filtered_paths: dict, flag_paths: dict,
                 moments_paths: dict, fsamp_paths: Optional[dict] = None, mode: str = "session") -> None:
    file_events = None
    try:
        out_path = _run_worker(
            "phase_b_file" if mode == "file" else "phase_b",
            {"filtered_paths": filtered_paths, "flag_paths": flag_paths, "moments_paths": moments_paths,
             "fsamp_paths": fsamp_paths or {}},
            ".npz",
        )
        with np.load(out_path) as data:
            scores = {fn: data[fn] for fn in data.files if not fn.startswith(("dist__", "__events__"))}
            dists = {fn[len("dist__"):]: data[fn] for fn in data.files if fn.startswith("dist__")}
            if "__events__" in data.files:
                file_events = json.loads(str(data["__events__"]))
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
                session.files[fn].dist = dists[fn]
        if file_events is not None:
            session.file_events = file_events["events"]
            session.file_meta = file_events["meta"]
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
        _check_project_id(project_id)
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
                dists = {fn: f.dist for fn, f in session.files.items()}
                phase_a_by_filename = {fn: f.phase_a for fn, f in session.files.items()}
                break
        time.sleep(0.3)

    _finalize_draft_dir(session)
    _run_process(session, scores, dists, phase_a_by_filename)


def _run_process(session: UploadSession, scores: dict, dists: dict, phase_a_by_filename: dict) -> None:
    try:
        score_npz = UPLOAD_DIR / "_work"
        score_npz.mkdir(parents=True, exist_ok=True)
        score_npz_fd, score_npz_name = tempfile.mkstemp(suffix=".npz", dir=str(score_npz))
        os.close(score_npz_fd)
        # App v3 item 1 (CC_PROMPT_APP_V3_CODE.md): Amendment A2 signal-loss flags, tiny
        # bool arrays embedded in the same score npz (stage-2 subprocess only ever gets file
        # paths/arrays — see pipeline_worker.py's `_run_process_events` / `_FLAG_KEY_PREFIX`,
        # never the raw signal itself) so it can build `inter_mask` for `detect_events`.
        savez_payload = dict(scores)
        for fn, phase_a in phase_a_by_filename.items():
            savez_payload[f"flag__{fn}"] = phase_a.flag
            savez_payload[f"dist__{fn}"] = dists[fn]
        np.savez(score_npz_name, **savez_payload)

        if session.mode == "file":
            # file engine: events were computed per file in Phase B (engine_file.run_file)
            Path(score_npz_name).unlink(missing_ok=True)
            file_events = session.file_events or {}
            tops = [m["top"] for m in session.file_meta.values() if not m["short"]]
            alarm_budget = float(np.mean(tops)) if tops else 0.0
            import engine_file as EF
            engine = EF.describe()
        else:
            out_path = _run_worker("process_events", {"score_npz_path": score_npz_name}, ".json")
            Path(score_npz_name).unlink(missing_ok=True)
            result = json.loads(out_path.read_text())
            out_path.unlink(missing_ok=True)
            alarm_budget = result["alarm_budget"]
            file_events = result["events"]  # {filename: [[onset_sec, offset_sec], ...]}
            engine = SESSION_ENGINE

        files_payload = []
        events_payload = {}
        for fn, phase_a in phase_a_by_filename.items():
            notice = phase_a.notice
            if session.mode == "file" and session.file_meta.get(fn, {}).get("short"):
                import engine_file as EF
                notice = (notice + " " if notice else "") + (
                    f"Shorter than {EF.settings()['min_minutes']} min of signal: the each-file engine flags nothing "
                    f"in it.")
            files_payload.append(
                {
                    "filename": fn,
                    "start_time": (db.PRIVATE_EPOCH if session.private or phase_a.start_time is None
                                   else phase_a.start_time.isoformat()),
                    "duration_seconds": phase_a.file_duration_seconds,
                    "notice": notice,
                }
            )
            events_payload[fn] = [
                {"onset_sec": onset, "offset_sec": offset}
                for onset, offset in file_events.get(fn, [])
            ]

        # Persist the subject-wide ensemble score (waveform_serving.get_timeline's cache —
        # CC_FIX_SCORECACHE_PROMPT.md Task 1a) BEFORE the subject exists in the DB, so a
        # write failure here fails the whole Process through the except below rather than
        # leaving a subject row with no score cache. `_finalize_draft_dir` (already run by
        # the caller) has moved the draft directory to its final uploads/{project_id}/ path
        # by this point.
        subject_dir = UPLOAD_DIR / session.project_id
        for fn, score in scores.items():
            np.save(subject_dir / f"{Path(fn).stem}.score.npy", score)

        db.create_subject_with_files(session.project_id, session.memo, files_payload, events_payload,
                                     mode=session.mode, mains_hz=session.mains_resolved or 60.0,
                                     private=session.private, engine=engine)
    except Exception as exc:  # pragma: no cover - unexpected pipeline/DB failure
        with session.lock:
            session.processing = False
            session.error = f"Processing error: {exc}"
        return

    with session.lock:
        session.processing = False
        session.done = True
        session.alarm_budget = alarm_budget


SESSION_ENGINE = ("whole session: V5 application chain (label-free statistics pooled over the study's files), "
                  "GAE v2 seed 42, k 4.0677")


def save_upload_to_tmp(data: bytes) -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(suffix=".edf", dir=str(UPLOAD_DIR))
    with open(fd, "wb") as fh:
        fh.write(data)
    return Path(tmp_name)


def save_upload_stream(fileobj) -> tuple[Path, int, str]:
    """C5 Step 2 (DESIGN_STEP2.md C8): copy an upload to disk in 1-MB chunks (never the whole file in memory);
    returns (path, size in bytes, sha256)."""
    import hashlib
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(suffix=".edf", dir=str(UPLOAD_DIR))
    h, size = hashlib.sha256(), 0
    with open(fd, "wb") as out:
        while True:
            chunk = fileobj.read(CHUNK_BYTES)
            if not chunk:
                break
            out.write(chunk)
            h.update(chunk)
            size += len(chunk)
    return Path(tmp_name), size, h.hexdigest()
