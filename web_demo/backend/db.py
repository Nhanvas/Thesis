"""SQLite schema + queries for subjects/files/events (SZSCAN_SPEC_v5.md §5.1-§5.3).

Scope as of Step 3 (DEMO_BUILD_HANDOFF.md §6 row 3): create-subject-with-files (atomic,
per §5.1's "subject + every child file row appears at once"), event bulk-insert, the
subject/file listing query (now with real Alert/Status derivation and embedded child files
for search — see SZSCAN_SPEC_v5.md §5.4), search, and subject deletion. Event REVIEW
(Accept/Reject/Uncertain, Select Range, comments) is Step 5+ scope — this file only writes
AI events at review_status='Unseen' (SPEC §5.3: nothing has been reviewed yet).
"""
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "szscan.db"

# SZSCAN_SPEC_v5.md §2 / CLAUDE.md — the fixed 8-subject held-out test allowlist. Not a
# numeric threshold pulled from a model file (CLAUDE.md's "never hardcode a threshold" is
# about pipeline parameters); this list IS the source of truth, spelled out verbatim there.
ALLOWED_SUBJECTS = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS subjects (
    id         TEXT PRIMARY KEY,                    -- e.g. 'chb06', == the typed Project ID
    memo       TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS files (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id       TEXT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    filename         TEXT NOT NULL,
    start_time       TEXT NOT NULL,                 -- ISO datetime from EDF header (meas_date)
    duration_seconds REAL NOT NULL,
    status           TEXT NOT NULL DEFAULT 'View'
                     CHECK (status IN ('View', 'Viewing', 'Viewed'))
);

CREATE TABLE IF NOT EXISTS events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id       INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    source        TEXT NOT NULL CHECK (source IN ('AI', 'Human')),
    onset_sec     REAL NOT NULL,
    offset_sec    REAL NOT NULL,
    review_status TEXT CHECK (review_status IN ('Accept', 'Reject', 'Uncertain', 'Unseen')
                              OR review_status IS NULL),
    comment       TEXT NOT NULL DEFAULT ''
);

-- Channel Attribution Panel (Step 7, CC_STEP7_PROMPT.md §2.2): per-channel Accept/Reject,
-- keyed by CHANNEL NAME (not index) so an edited Human event keeps its channel judgments.
-- Deleting an event deletes its rows explicitly in delete_event() below — never relies on
-- the FK pragma alone (SQLite's `PRAGMA foreign_keys` is connection-scoped and the prompt
-- asks for this to be explicit).
CREATE TABLE IF NOT EXISTS attribution_status (
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    channel  TEXT NOT NULL,
    status   TEXT NOT NULL CHECK (status IN ('Accept', 'Reject')),
    PRIMARY KEY (event_id, channel)
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def _format_duration(seconds: float) -> str:
    """SZSCAN_SPEC_v5.md §5.1: HH:MM:SS if < 24h, else 'Nd:HH:MM:SS'."""
    total = int(round(seconds))
    days, rem = divmod(total, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    if days > 0:
        return f"{days}d:{h:02d}:{m:02d}:{s:02d}"
    return f"{h:02d}:{m:02d}:{s:02d}"


def _recording_label(n: int, iso: str | None) -> str | None:
    """SZSCAN_SPEC_v5.md §5.1 (C17, 2026-09): 'Recording N, HH:MM:SS' — never an absolute
    date. CHB-MIT/PhysioNet applies a fixed per-subject date shift to de-identify
    recordings, so meas_date's year/date is fabricated (only the time-of-day and the
    relative ordering/spacing between a subject's own recordings are real) — see the spec
    footnote under §5.1's table. N is this file's 1-based position when the subject's files
    are sorted by meas_date ascending (N=1 = earliest); callers pass N, this function only
    formats. This ordering is display-only and separate from the filename-based sort used
    for event-offset assignment (SPEC §1.5) — see edf_order.py's own docstring for that
    same "which file an event belongs to" vs "what position a file displays at" split."""
    if not iso:
        return None
    dt = datetime.fromisoformat(iso)
    return f"Recording {n}, {dt.strftime('%H:%M:%S')}"


def _file_status_badge(status: str) -> str:
    return status  # file-level status has no fraction, shown as-is (SPEC §5.2)


def _subject_status(file_statuses: list[str]) -> str:
    """SZSCAN_SPEC_v5.md §5.2: View if ALL 'View', Viewed if ALL 'Viewed', else
    'Viewing (x/N)' with x = count of 'Viewed'."""
    n = len(file_statuses)
    if n == 0:
        return "View"
    if all(s == "View" for s in file_statuses):
        return "View"
    if all(s == "Viewed" for s in file_statuses):
        return "Viewed"
    viewed = sum(1 for s in file_statuses if s == "Viewed")
    return f"Viewing ({viewed}/{n})"


def create_subject_with_files(
    subject_id: str,
    memo: str,
    files: list[dict],
    events_by_filename: dict[str, list[dict]],
) -> None:
    """Atomic per SZSCAN_SPEC_v5.md §5.1: the subject row and every child file row (and
    their AI events) appear together, or not at all — a subject mid-pipeline must never
    show up in the table.

    `files`: [{filename, start_time (ISO str), duration_seconds}, ...]
    `events_by_filename`: {filename: [{onset_sec, offset_sec}, ...]}
    """
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO subjects (id, memo) VALUES (?, ?)", (subject_id, memo)
        )
        for f in files:
            cur = conn.execute(
                "INSERT INTO files (subject_id, filename, start_time, duration_seconds, status) "
                "VALUES (?, ?, ?, ?, 'View')",
                (subject_id, f["filename"], f["start_time"], f["duration_seconds"]),
            )
            file_id = cur.lastrowid
            for ev in events_by_filename.get(f["filename"], []):
                conn.execute(
                    "INSERT INTO events (file_id, source, onset_sec, offset_sec, review_status) "
                    "VALUES (?, 'AI', ?, ?, 'Unseen')",
                    (file_id, ev["onset_sec"], ev["offset_sec"]),
                )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _alert_counts_by_file(conn: sqlite3.Connection) -> dict[int, int]:
    """SZSCAN_SPEC_v5.md §5.3: Alert = (AI events not Rejected) + (Human events). i.e.
    every event NOT (source='AI' AND review_status='Reject')."""
    rows = conn.execute(
        """
        SELECT file_id, COUNT(*) AS n
        FROM events
        WHERE NOT (source = 'AI' AND review_status = 'Reject')
        GROUP BY file_id
        """
    ).fetchall()
    return {row["file_id"]: row["n"] for row in rows}


def _file_row(row: sqlite3.Row, alert: int, recording_n: int) -> dict:
    return {
        "id": row["id"],
        "filename": row["filename"],
        "start_date": _recording_label(recording_n, row["start_time"]),
        "duration": _format_duration(row["duration_seconds"]),
        "alert": alert,
        "status": _file_status_badge(row["status"]),
    }


def _subject_dict(conn: sqlite3.Connection, srow: sqlite3.Row, alert_by_file: dict[int, int]) -> dict:
    file_rows = conn.execute(
        "SELECT id, filename, start_time, duration_seconds, status FROM files "
        "WHERE subject_id = ? ORDER BY start_time",
        (srow["id"],),
    ).fetchall()
    # file_rows is already sorted by start_time (meas_date) ascending, so its own
    # position IS the C17 "Recording N" display ordering — a separate concern from
    # edf_order.py's filename-based sort (SPEC §1.5's event-offset assignment). Step 4
    # (CC_STEP4_PROMPT.md) reuses this same ordering for Previous/Next and the file
    # dropdown, rather than inventing a second file order for the Analysis screen.
    files = [
        _file_row(f, alert_by_file.get(f["id"], 0), i + 1)
        for i, f in enumerate(file_rows)
    ]
    subject_alert = sum(f["alert"] for f in files)
    starts = [f["start_time"] for f in file_rows if f["start_time"]]
    total_duration = sum(f["duration_seconds"] for f in file_rows)
    return {
        "id": srow["id"],
        "no_files": len(file_rows),
        "start_date": _recording_label(1, min(starts)) if starts else None,
        "duration": _format_duration(total_duration) if file_rows else "",
        "alert": subject_alert,
        "status": _subject_status([f["status"] for f in files]),
        "memo": srow["memo"],
        "files": files,
    }


def list_subjects() -> list[dict]:
    """Subjects with derived §5.1 columns, each with its child files embedded (small demo
    dataset — this keeps SZSCAN_SPEC_v5.md §5.4's filename search simple: no separate
    per-subject fetch needed to search inside collapsed rows)."""
    conn = get_connection()
    subject_rows = conn.execute(
        "SELECT id, memo FROM subjects ORDER BY created_at"
    ).fetchall()
    alert_by_file = _alert_counts_by_file(conn)
    result = [_subject_dict(conn, srow, alert_by_file) for srow in subject_rows]
    conn.close()
    return result


def get_subject(subject_id: str) -> dict | None:
    """Single-subject fetch for the Analysis screen (Step 4, CC_STEP4_PROMPT.md §6.1):
    header alert count, Previous/Next, file dropdown, Progress x/N — all derived from the
    same file list/ordering as the Database screen's table (list_subjects above)."""
    conn = get_connection()
    srow = conn.execute("SELECT id, memo FROM subjects WHERE id = ?", (subject_id,)).fetchone()
    if srow is None:
        conn.close()
        return None
    alert_by_file = _alert_counts_by_file(conn)
    result = _subject_dict(conn, srow, alert_by_file)
    conn.close()
    return result


def get_file(file_id: int) -> dict | None:
    """Single-file fetch for the Analysis screen header/toolbar (Step 4). Recording N is
    this file's own 1-based position among its subject's files sorted by start_time — same
    ordering _subject_dict uses, computed independently here so a direct file fetch doesn't
    need the whole subject payload."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id, subject_id, filename, start_time, duration_seconds, status "
        "FROM files WHERE id = ?",
        (file_id,),
    ).fetchone()
    if row is None:
        conn.close()
        return None
    alert_by_file = _alert_counts_by_file(conn)
    siblings = conn.execute(
        "SELECT id FROM files WHERE subject_id = ? ORDER BY start_time",
        (row["subject_id"],),
    ).fetchall()
    conn.close()
    recording_n = next((i + 1 for i, s in enumerate(siblings) if s["id"] == row["id"]), 1)
    file_dict = _file_row(row, alert_by_file.get(row["id"], 0), recording_n)
    file_dict["subject_id"] = row["subject_id"]
    file_dict["start_time"] = row["start_time"]
    file_dict["duration_seconds"] = row["duration_seconds"]
    return file_dict


def set_file_status(file_id: int, status: str) -> None:
    conn = get_connection()
    conn.execute("UPDATE files SET status = ? WHERE id = ?", (status, file_id))
    conn.commit()
    conn.close()


def set_file_status_if(file_id: int, status: str, only_if_current: str) -> None:
    """Conditional status transition — used for the View -> Viewing auto-transition
    (SPEC §5.2) so opening an already-Viewed file's Analysis screen never regresses it."""
    conn = get_connection()
    conn.execute(
        "UPDATE files SET status = ? WHERE id = ? AND status = ?",
        (status, file_id, only_if_current),
    )
    conn.commit()
    conn.close()


def delete_subject(subject_id: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
    conn.commit()
    conn.close()


# ── Panel Event (Step 5, CC_STEP5_PROMPT.md §6.5) ───────────────────────────────────────

def _event_row(row: sqlite3.Row, index: int) -> dict:
    """`name` ('Event N') is derived from onset-ascending position at read time, not stored
    — SPEC §6.6's 'a new event inserts at its correct time position, not appended to the
    end' is naturally satisfied this way with no renumbering bookkeeping needed later."""
    return {
        "id": row["id"],
        "file_id": row["file_id"],
        "name": f"Event {index + 1}",
        "source": row["source"],
        "onset_sec": row["onset_sec"],
        "offset_sec": row["offset_sec"],
        "duration_sec": row["offset_sec"] - row["onset_sec"],
        "review_status": row["review_status"],
        "comment": row["comment"],
    }


def list_events(file_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, file_id, source, onset_sec, offset_sec, review_status, comment "
        "FROM events WHERE file_id = ? ORDER BY onset_sec ASC, id ASC",
        (file_id,),
    ).fetchall()
    conn.close()
    return [_event_row(r, i) for i, r in enumerate(rows)]


def get_event(event_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT id, file_id, source, onset_sec, offset_sec, review_status, comment "
        "FROM events WHERE id = ?",
        (event_id,),
    ).fetchone()
    if row is None:
        conn.close()
        return None
    # Recompute this event's onset-ordered index within its own file, same rule as
    # list_events, so a single-event fetch (e.g. after PATCH) carries the same `name`.
    siblings = conn.execute(
        "SELECT id FROM events WHERE file_id = ? ORDER BY onset_sec ASC, id ASC",
        (row["file_id"],),
    ).fetchall()
    conn.close()
    index = next((i for i, s in enumerate(siblings) if s["id"] == row["id"]), 0)
    return _event_row(row, index)


def update_event(event_id: int, review_status: str | None = None, comment: str | None = None) -> None:
    conn = get_connection()
    if review_status is not None:
        conn.execute("UPDATE events SET review_status = ? WHERE id = ?", (review_status, event_id))
    if comment is not None:
        conn.execute("UPDATE events SET comment = ? WHERE id = ?", (comment, event_id))
    conn.commit()
    conn.close()


def update_event_times(event_id: int, onset_sec: float, offset_sec: float) -> None:
    """Edit (SPEC §6.6/§6.5) — redrawing a Human event's onset/offset via Select Range-style
    marking. Never called for an AI event (main.py enforces that; an AI event's onset/offset
    is immutable per §6.5 — Reject-and-redraw is its only path)."""
    conn = get_connection()
    conn.execute(
        "UPDATE events SET onset_sec = ?, offset_sec = ? WHERE id = ?",
        (onset_sec, offset_sec, event_id),
    )
    conn.commit()
    conn.close()


def delete_event(event_id: int) -> None:
    conn = get_connection()
    # Explicit, not relying on the FK pragma alone (§2.2) — this connection does enable
    # PRAGMA foreign_keys, but the attribution table's own delete is spelled out regardless.
    conn.execute("DELETE FROM attribution_status WHERE event_id = ?", (event_id,))
    conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()


# ── Select Range (Step 6, CC_STEP6_PROMPT.md §6.6) ──────────────────────────────────────

def create_event(file_id: int, onset_sec: float, offset_sec: float) -> int:
    """The only way a Human event comes into existence. Always `review_status=NULL` — a
    Human event self-confirms on creation and carries no review-status axis at all (SPEC
    §6.5), unlike an AI event's 'Unseen' default."""
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO events (file_id, source, onset_sec, offset_sec, review_status, comment) "
        "VALUES (?, 'Human', ?, ?, NULL, '')",
        (file_id, onset_sec, offset_sec),
    )
    conn.commit()
    event_id = cur.lastrowid
    conn.close()
    return event_id


# ── Export (Step 8, CC_STEP8_PROMPT.md) ─────────────────────────────────────────────────

def list_files_by_filename(subject_id: str) -> list[dict]:
    """File order for the .txt export (SZSCAN_SPEC_v5.md §7.1): file-NAME order, the
    original CHB-MIT convention -- deliberately NOT `_subject_dict`'s meas_date/
    start_time order (C17), which only drives the UI's 'Recording N' display and
    Previous/Next."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, subject_id, filename, start_time, duration_seconds, status "
        "FROM files WHERE subject_id = ? ORDER BY filename",
        (subject_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Channel Attribution Panel (Step 7, CC_STEP7_PROMPT.md §2.2) ────────────────────────

def get_attribution_status(event_id: int) -> dict[str, str]:
    """{channel: 'Accept'|'Reject'} for every channel that has been reviewed on this event.
    A channel absent from the dict is unset (SPEC's default, never a stored third value)."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT channel, status FROM attribution_status WHERE event_id = ?", (event_id,)
    ).fetchall()
    conn.close()
    return {r["channel"]: r["status"] for r in rows}


def set_attribution_status(event_id: int, statuses: dict[str, str]) -> None:
    """Save (§2.2): replaces the stored set with exactly what the panel shows — an empty
    dict (after Clear all) stores nothing, i.e. clears every prior status for this event.
    Never called on every keystroke/click; only on the panel's own Save button."""
    conn = get_connection()
    conn.execute("DELETE FROM attribution_status WHERE event_id = ?", (event_id,))
    conn.executemany(
        "INSERT INTO attribution_status (event_id, channel, status) VALUES (?, ?, ?)",
        [(event_id, ch, st) for ch, st in statuses.items()],
    )
    conn.commit()
    conn.close()
