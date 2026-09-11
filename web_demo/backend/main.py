"""FastAPI app — SzScan web demo backend.

Scope of this file (Step 2 of 9, see DEMO_BUILD_HANDOFF.md §6): session auth (login/logout)
and a subjects-listing endpoint. Create/upload/process (Step 3) and everything under
Analysis (Step 4+) are not implemented here.

Session mechanism (SZSCAN_SPEC_v5.md §4, CLAUDE.md): an in-memory token keyed to the admin
username, carried in an HttpOnly cookie. This is explicitly NOT a real security mechanism —
no password hashing, no expiry, no CSRF protection — a symbolic access gate is all the spec
asks for. Do not extend this into something it isn't.
"""
import os
import secrets

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import db

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
