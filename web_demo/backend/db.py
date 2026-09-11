"""SQLite schema for subjects/files (SZSCAN_SPEC_v5.md §5.1). Schema only — no seed data.

Scope of this file (Step 2 of 9, see DEMO_BUILD_HANDOFF.md §6): schema + a subjects listing
query. Create/upload/process (Step 3) and event review (Step 5+) are not implemented here.

Column semantics, derived rather than stored redundantly (SZSCAN_SPEC_v5.md §5.1-§5.3):
- No. files   = COUNT(files) for the subject; a file row shows 1 implicitly.
- Start date  = MIN(files.start_time) for the subject; a file row shows its own start_time.
- Duration    = SUM(files.duration_seconds) for the subject; a file row shows its own.
- Alert       = COUNT(events) where NOT (source='AI' AND review_status='Reject') (§5.3).
- Status      = derived from files.status per §5.2 (View / Viewing (x/N) / Viewed); not
                stored at subject level.
- Memo        = free text, subject-level only. Never auto-generated from the model.

`events` is included now even though no Step 2 endpoint touches it, because Alert (a §5.1
column) is only meaningful once events exist — defining it here avoids a schema migration
later. No event-review behavior (Accept/Reject/Select Range/etc., §5.6-§6.6) is built yet.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "szscan.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS subjects (
    id         TEXT PRIMARY KEY,                    -- e.g. 'chb06'
    memo       TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS files (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id       TEXT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    filename         TEXT NOT NULL,
    start_time       TEXT NOT NULL,                 -- from EDF header, never user-entered
    duration_seconds INTEGER NOT NULL,
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


def list_subjects() -> list[dict]:
    """Subjects with derived §5.1 columns. Returns [] until Step 3 creates real subjects."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT s.id, s.memo,
               COUNT(f.id) AS no_files,
               MIN(f.start_time) AS start_date,
               COALESCE(SUM(f.duration_seconds), 0) AS duration_seconds
        FROM subjects s
        LEFT JOIN files f ON f.subject_id = s.id
        GROUP BY s.id
        ORDER BY s.created_at
        """
    ).fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "no_files": row["no_files"],
            "start_date": row["start_date"],
            "duration_seconds": row["duration_seconds"],
            "memo": row["memo"],
        }
        for row in rows
    ]
