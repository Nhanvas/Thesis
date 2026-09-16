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


def list_subjects() -> list[dict]:
    """Subjects with derived §5.1 columns, each with its child files embedded (small demo
    dataset — this keeps SZSCAN_SPEC_v5.md §5.4's filename search simple: no separate
    per-subject fetch needed to search inside collapsed rows)."""
    conn = get_connection()
    subject_rows = conn.execute(
        "SELECT id, memo FROM subjects ORDER BY created_at"
    ).fetchall()
    alert_by_file = _alert_counts_by_file(conn)

    result = []
    for srow in subject_rows:
        file_rows = conn.execute(
            "SELECT id, filename, start_time, duration_seconds, status FROM files "
            "WHERE subject_id = ? ORDER BY start_time",
            (srow["id"],),
        ).fetchall()
        # file_rows is already sorted by start_time (meas_date) ascending, so its own
        # position IS the C17 "Recording N" display ordering — a separate concern from
        # edf_order.py's filename-based sort (SPEC §1.5's event-offset assignment).
        files = [
            _file_row(f, alert_by_file.get(f["id"], 0), i + 1)
            for i, f in enumerate(file_rows)
        ]
        subject_alert = sum(f["alert"] for f in files)
        starts = [f["start_time"] for f in file_rows if f["start_time"]]
        total_duration = sum(f["duration_seconds"] for f in file_rows)
        result.append(
            {
                "id": srow["id"],
                "no_files": len(file_rows),
                "start_date": _recording_label(1, min(starts)) if starts else None,
                "duration": _format_duration(total_duration) if file_rows else "",
                "alert": subject_alert,
                "status": _subject_status([f["status"] for f in files]),
                "memo": srow["memo"],
                "files": files,
            }
        )
    conn.close()
    return result


def delete_subject(subject_id: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
    conn.commit()
    conn.close()
