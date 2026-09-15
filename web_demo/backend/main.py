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

import db
import upload_manager as um

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
