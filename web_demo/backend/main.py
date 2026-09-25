"""FastAPI app — SzScan web demo backend.

Scope as of Step 3 (DEMO_BUILD_HANDOFF.md §6 row 3): session auth (login/logout), the
subjects-listing/search/delete endpoints, and the Create New panel's upload + two-stage
processing endpoints (SZSCAN_SPEC_v5.md §5.5), backed by upload_manager.py's singleton
session. Everything under Analysis (Step 4+) is not implemented here.

Session mechanism (SZSCAN_SPEC_v5.md §4, CLAUDE.md): an in-memory token keyed to the admin
username, carried in an HttpOnly cookie. This is explicitly NOT a real security mechanism —
no password hashing, no expiry, no CSRF protection — a symbolic access gate is all the spec
asks for. Do not extend this into something it isn't.
"""
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import attribution as attr
import db
import upload_manager as um
import waveform_serving as ws

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

ADMIN_USER = os.environ.get("ADMIN_USER", "")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "")
SESSION_COOKIE = "szscan_session"

# token -> username. In-memory by design (dev-only demo, single process, see module docstring).
_sessions: dict[str, str] = {}

app = FastAPI(title="SzScan demo backend")

# Vite dev server default origin. Credentials (cookies) required for the session cookie to
# round-trip cross-origin during `npm run dev`.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    db.init_db()


class LoginRequest(BaseModel):
    username: str
    password: str


def _current_user(request: Request) -> str | None:
    token = request.cookies.get(SESSION_COOKIE)
    if token is None:
        return None
    return _sessions.get(token)


def _require_auth(request: Request) -> str:
    user = _current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not logged in")
    return user


@app.post("/api/login")
def login(payload: LoginRequest, response: Response):
    if not (
        secrets.compare_digest(payload.username, ADMIN_USER)
        and secrets.compare_digest(payload.password, ADMIN_PASS)
    ):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    token = secrets.token_urlsafe(32)
    _sessions[token] = payload.username
    response.set_cookie(
        SESSION_COOKIE, token, httponly=True, samesite="lax", secure=False
    )
    return {"username": payload.username}


@app.post("/api/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get(SESSION_COOKIE)
    if token is not None:
        _sessions.pop(token, None)
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}


@app.get("/api/session")
def session(request: Request):
    user = _current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not logged in")
    return {"username": user}


@app.get("/api/subjects")
def subjects(request: Request):
    _require_auth(request)
    return db.list_subjects()


@app.delete("/api/subjects/{subject_id}")
def delete_subject(subject_id: str, request: Request):
    _require_auth(request)
    db.delete_subject(subject_id)
    return {"ok": True}


# ── Analysis screen (Step 4, CC_STEP4_PROMPT.md): Panel EEG + toolbar + scrub ───────────

@app.get("/api/subjects/{subject_id}")
def get_subject_detail(subject_id: str, request: Request):
    _require_auth(request)
    subject = db.get_subject(subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found.")
    return subject


def _file_detail(file_id: int) -> dict | None:
    """Shared shape for every file-returning Analysis endpoint (GET + both status-transition
    POSTs) — all three must carry `channels`/`usable_duration_seconds` since AnalysisScreen
    calls setFileMeta(...) on whichever response it gets back from any of them."""
    f = db.get_file(file_id)
    if f is None:
        return None
    raw_path, _ = ws._cache_paths(f["subject_id"], f["filename"], um.UPLOAD_DIR)
    f["channels"] = ws.CHANNELS
    f["usable_duration_seconds"] = ws.usable_duration_seconds(raw_path)
    return f


@app.get("/api/files/{file_id}")
def get_file(file_id: int, request: Request):
    _require_auth(request)
    f = _file_detail(file_id)
    if f is None:
        raise HTTPException(status_code=404, detail="File not found.")
    return f


@app.post("/api/files/{file_id}/viewing")
def mark_file_viewing(file_id: int, request: Request):
    """Opening a file's Analysis screen for the first time (SPEC §5.2's 'Viewing (đang xem
    dở, tiến độ tự lưu)') — only fires View -> Viewing, never touches an already-Viewed
    file (see db.set_file_status_if)."""
    _require_auth(request)
    if db.get_file(file_id) is None:
        raise HTTPException(status_code=404, detail="File not found.")
    db.set_file_status_if(file_id, "Viewing", only_if_current="View")
    return _file_detail(file_id)


@app.post("/api/files/{file_id}/viewed")
def mark_file_viewed(file_id: int, request: Request):
    _require_auth(request)
    if db.get_file(file_id) is None:
        raise HTTPException(status_code=404, detail="File not found.")
    db.set_file_status(file_id, "Viewed")
    return _file_detail(file_id)


@app.get("/api/files/{file_id}/waveform")
def get_waveform(
    file_id: int,
    start_sec: float,
    end_sec: float,
    width_px: int,
    request: Request,
):
    """Panel EEG's only data endpoint (SPEC §6.4 / DEMO_BUILD_HANDOFF.md §5): one call per
    visible-window change, returning both raw and filtered decimated envelopes together so
    a filter-toggle click never needs a second round trip. Amplitude-scale changes are pure
    frontend and never reach this endpoint at all."""
    _require_auth(request)
    f = db.get_file(file_id)
    if f is None:
        raise HTTPException(status_code=404, detail="File not found.")
    return ws.get_waveform(f["subject_id"], f["filename"], um.UPLOAD_DIR, start_sec, end_sec, width_px)


# ── Mini-timeline + Panel Event (Step 5, CC_STEP5_PROMPT.md §6.3/§6.5) ──────────────────

@app.get("/api/files/{file_id}/timeline")
def get_timeline(file_id: int, request: Request):
    """Mini-timeline's score row — read-only, from the Phase-B score cache (see
    waveform_serving.get_timeline's docstring). Never re-runs any part of the pipeline."""
    _require_auth(request)
    f = db.get_file(file_id)
    if f is None:
        raise HTTPException(status_code=404, detail="File not found.")
    try:
        return ws.get_timeline(f["subject_id"], f["filename"], um.UPLOAD_DIR)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/files/{file_id}/events")
def get_file_events(file_id: int, request: Request):
    _require_auth(request)
    if db.get_file(file_id) is None:
        raise HTTPException(status_code=404, detail="File not found.")
    return db.list_events(file_id)


class CreateEventRequest(BaseModel):
    onset_sec: float
    offset_sec: float


@app.post("/api/files/{file_id}/events")
def create_event(file_id: int, payload: CreateEventRequest, request: Request):
    """Select Range (Step 6, SPEC §6.6) — the only way a Human event is created. The two
    clicks that produced onset_sec/offset_sec may land in either order (right-to-left drag,
    item 13) — sorted here so a reversed drag still yields onset < offset rather than being
    rejected or stored negative."""
    _require_auth(request)
    if db.get_file(file_id) is None:
        raise HTTPException(status_code=404, detail="File not found.")
    onset, offset = sorted((payload.onset_sec, payload.offset_sec))
    if offset <= onset:
        raise HTTPException(status_code=422, detail="Event must have a positive duration.")
    event_id = db.create_event(file_id, onset, offset)
    return db.get_event(event_id)


class UpdateEventRequest(BaseModel):
    review_status: str | None = None
    comment: str | None = None
    onset_sec: float | None = None
    offset_sec: float | None = None


@app.patch("/api/events/{event_id}")
def update_event(event_id: int, payload: UpdateEventRequest, request: Request):
    """AI event review (Accept/Reject/Uncertain) and/or comment, per SPEC §6.5. `Unseen`
    is the unreviewed default, not a value this endpoint can set back to — there is no
    'un-review' control in the spec'd expand panel (only 3 buttons: Accept/Reject/
    Uncertain). Human events carry no review_status at all (§6.5: 'Human event tự confirm
    khi tạo nên không cần review') — only their comment, and (Step 6, Edit) their
    onset/offset, can be updated here."""
    _require_auth(request)
    event = db.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found.")
    if payload.review_status is not None:
        if event["source"] != "AI":
            raise HTTPException(
                status_code=422, detail="Only AI events carry a review status."
            )
        if payload.review_status not in ("Accept", "Reject", "Uncertain"):
            raise HTTPException(
                status_code=422,
                detail="review_status must be one of Accept/Reject/Uncertain.",
            )
    if payload.onset_sec is not None or payload.offset_sec is not None:
        # Edit (SPEC §6.6's reading, CC_STEP6_PROMPT.md item 11): re-drawing a Human
        # event's range via the same 2-click Select Range flow. An AI event's onset/offset
        # is immutable (§6.5) — Reject-and-redraw is its only path.
        if event["source"] != "Human":
            raise HTTPException(
                status_code=422, detail="Only Human-added events can have their onset/offset edited."
            )
        if payload.onset_sec is None or payload.offset_sec is None:
            raise HTTPException(
                status_code=422, detail="Both onset_sec and offset_sec are required to edit a range."
            )
        onset, offset = sorted((payload.onset_sec, payload.offset_sec))
        if offset <= onset:
            raise HTTPException(status_code=422, detail="Event must have a positive duration.")
        db.update_event_times(event_id, onset, offset)
    db.update_event(event_id, review_status=payload.review_status, comment=payload.comment)
    return db.get_event(event_id)


# ── Channel Attribution Panel (Step 7, CC_STEP7_PROMPT.md §2.2) ────────────────────────

@app.get("/api/events/{event_id}/attribution")
def get_event_attribution(event_id: int, request: Request):
    """Works for AI and Human events identically — computed fresh from the per-node cache
    on every call (never cached in the DB), so an edited Human event's range change is
    reflected immediately."""
    _require_auth(request)
    event = db.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found.")
    f = db.get_file(event["file_id"])
    if f is None:
        raise HTTPException(status_code=404, detail="File not found.")
    return attr.get_event_attribution(event, f, um.UPLOAD_DIR)


class AttributionStatusRequest(BaseModel):
    statuses: dict[str, str]  # {channel: 'Accept'|'Reject'}


@app.put("/api/events/{event_id}/attribution-status")
def put_event_attribution_status(event_id: int, payload: AttributionStatusRequest, request: Request):
    """Save (§2.2) — replaces the stored per-channel status set with exactly what the panel
    shows. `Clear all` is just this endpoint called with an empty `statuses` dict once Save
    is pressed (SPEC's Save-persists pattern, same as the AI event review)."""
    _require_auth(request)
    if db.get_event(event_id) is None:
        raise HTTPException(status_code=404, detail="Event not found.")
    for ch, status in payload.statuses.items():
        if ch not in attr.CHANNELS:
            raise HTTPException(status_code=422, detail=f"Unknown channel: {ch}")
        if status not in ("Accept", "Reject"):
            raise HTTPException(status_code=422, detail="status must be Accept or Reject.")
    db.set_attribution_status(event_id, payload.statuses)
    return {"ok": True}


@app.delete("/api/events/{event_id}")
def delete_event(event_id: int, request: Request):
    """Human-added events only (SPEC §6.5's Delete/Edit pair) — AI events can never be
    deleted, only Rejected (§6.5: 'muốn sửa thì Reject rồi tự tạo event mới')."""
    _require_auth(request)
    event = db.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found.")
    if event["source"] != "Human":
        raise HTTPException(status_code=422, detail="Only Human-added events can be deleted.")
    db.delete_event(event_id)
    return {"ok": True}


# ── Create New panel: upload + two-stage processing (SZSCAN_SPEC_v5.md §5.5) ───────────
# Singleton session (upload_manager.py) — SPEC's own "exactly one subject processed at a
# time, system-wide, even minimized" rule means there is nothing to key by; the frontend
# never sends a session id.

class StartUploadRequest(BaseModel):
    project_id: str
    memo: str = ""


def _require_session(request: Request) -> um.UploadSession:
    _require_auth(request)
    session = um.get_current()
    if session is None:
        raise HTTPException(status_code=404, detail="No Create New session in progress.")
    return session


@app.post("/api/uploads/current")
def start_upload(payload: StartUploadRequest, request: Request):
    _require_auth(request)
    try:
        session = um.start_session(payload.project_id.strip(), payload.memo)
    except um.UploadManagerError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.toast) from exc
    return session.snapshot()


@app.get("/api/uploads/current")
def get_upload(request: Request):
    session = _require_session(request)
    um.poll_tick(session)
    return session.snapshot()


@app.delete("/api/uploads/current")
def discard_upload(request: Request):
    _require_auth(request)
    session = um.get_current()
    if session is not None and session.processing:
        raise HTTPException(status_code=409, detail="Cannot discard while Process is running.")
    um.discard_session()
    return {"ok": True}


@app.post("/api/uploads/current/acknowledge")
def acknowledge_upload(request: Request):
    _require_auth(request)
    um.acknowledge_done()
    return {"ok": True}


@app.post("/api/uploads/current/files")
async def upload_file(request: Request, file: UploadFile = File(...)):
    session = _require_session(request)
    filename = Path(file.filename).name
    if not filename.lower().endswith(".edf"):
        raise HTTPException(status_code=422, detail=um.REJECTED_FILE_MESSAGE)
    with session.lock:
        if filename in session.files:
            raise HTTPException(status_code=409, detail=f"{filename} is already in this list.")
        if session.processing or session.done:
            raise HTTPException(status_code=409, detail="Cannot add files while Process is running.")
    data = await file.read()
    tmp_path = um.save_upload_to_tmp(data)
    um.add_file(session, filename, tmp_path)
    return session.snapshot()


@app.delete("/api/uploads/current/files/{filename}")
def remove_upload_file(filename: str, request: Request):
    session = _require_session(request)
    um.remove_file(session, filename)
    return session.snapshot()


class ProcessRequest(BaseModel):
    project_id: str
    memo: str = ""


@app.post("/api/uploads/current/process")
def process_upload(payload: ProcessRequest, request: Request):
    session = _require_session(request)
    try:
        um.start_process(session, payload.project_id, payload.memo)
    except um.UploadManagerError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.toast) from exc
    return session.snapshot()
