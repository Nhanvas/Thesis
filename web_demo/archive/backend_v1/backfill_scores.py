"""backfill_scores.py — CC_FIX_SCORECACHE_PROMPT.md Task 1b: backfill `{stem}.score.npy` for
subjects that were processed before Task 1a wired the live Process flow to persist it.

Root cause (CC_CHB06_DIAG_REPORT.md / CC_FIX_MINITIMELINE_REPORT.md §4): before Task 1a, the
live Create-New/Process flow never wrote `{stem}.score.npy` to the persistent per-subject
directory — only a one-time backfill (CC_STEP5_REPORT.md) ever did, for two subjects that no
longer exist in this DB. `waveform_serving.get_timeline()` then raises `FileNotFoundError` for
every subject actually in the DB today.

Safety model, deliberately conservative:
  - Recomputes the subject-wide ensemble score exactly as the live Process flow does —
    `pipeline_demo.process_subject_phase_b_from_paths` over every one of the subject's cached
    `{stem}.filtered.npy` files (the production code path, same one CC_CHB06_DIAG_REPORT.md §4
    used) — never re-reads the source EDF, never re-runs Phase A.
  - Re-runs `process_subject_events` on the recomputed scores and compares its output against
    every 'AI'-source event already stored in the DB for that subject, file by file: every
    event, onset AND offset, must match exactly. On any mismatch, nothing is written for that
    subject and the mismatch is reported — a subject's `.score.npy` files are written only when
    the recomputation is proven to reproduce the exact events already on record.
  - Never calls `db.create_subject_with_files` / any DB write — read-only against the DB.
  - Never overwrites an existing `.score.npy` — if one is already on disk for a file, it is
    left untouched; the recomputed array is only diffed against it (max abs difference reported)
    for confidence, never written.
  - One subject at a time, single process (no subprocess/threading) — this script both
    recomputes and validates in-process, unlike the live flow's separate `pipeline_worker.py`
    subprocess (that separation exists only to dodge a Windows uvicorn-hosted-process hang,
    irrelevant to this standalone CLI script).

Usage: `python backfill_scores.py [subject_id ...]` — no args backfills all 8 allowlisted
subjects (db.ALLOWED_SUBJECTS).
"""
import sys
import time
from pathlib import Path

import numpy as np

import db
import pipeline_demo as pd

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"


def _subject_dir(subject_id: str) -> Path:
    return UPLOAD_DIR / subject_id


def _db_ai_events(subject_id: str) -> dict[str, list[tuple[float, float]]]:
    """{filename: [(onset_sec, offset_sec), ...]} for every 'AI'-source event currently
    stored for this subject, sorted by onset_sec — never reads review_status/comment."""
    conn = db.get_connection()
    rows = conn.execute(
        """
        SELECT f.filename AS filename, e.onset_sec AS onset_sec, e.offset_sec AS offset_sec
        FROM files f JOIN events e ON e.file_id = f.id
        WHERE f.subject_id = ? AND e.source = 'AI'
        ORDER BY f.filename, e.onset_sec ASC
        """,
        (subject_id,),
    ).fetchall()
    conn.close()
    out: dict[str, list[tuple[float, float]]] = {}
    for r in rows:
        out.setdefault(r["filename"], []).append((r["onset_sec"], r["offset_sec"]))
    return out


def backfill_subject(subject_id: str) -> None:
    print(f"\n=== {subject_id} ===")
    conn = db.get_connection()
    filenames = [
        r["filename"]
        for r in conn.execute(
            "SELECT filename FROM files WHERE subject_id = ? ORDER BY id", (subject_id,)
        ).fetchall()
    ]
    conn.close()
    if not filenames:
        print("  no files in DB — skipping")
        return

    subj_dir = _subject_dir(subject_id)
    missing_before = []
    filtered_paths = {}
    for fn in filenames:
        stem = Path(fn).stem
        filtered_path = subj_dir / f"{stem}.filtered.npy"
        if not filtered_path.exists():
            print(f"  MISSING {stem}.filtered.npy — cannot recompute, skipping subject")
            return
        filtered_paths[fn] = str(filtered_path)
        if not (subj_dir / f"{stem}.score.npy").exists():
            missing_before.append(fn)

    if not missing_before:
        print(f"  before: {len(filenames)} files, 0 missing .score.npy — nothing to do")
        return

    print(f"  before: {len(filenames)} files, {len(missing_before)} missing .score.npy")
    print(f"  recomputing subject-wide scores from {len(filenames)} cached .filtered.npy files...")
    t0 = time.perf_counter()
    scores = pd.process_subject_phase_b_from_paths(filtered_paths)
    file_events, op = pd.process_subject_events(scores)
    wall = time.perf_counter() - t0
    print(f"  wall-clock: {wall:.1f}s (phase B recompute + process_subject_events)")

    db_events = _db_ai_events(subject_id)
    all_match = True
    for fn in sorted(filtered_paths):
        recomputed = sorted((ev.onset_sec, ev.offset_sec) for ev in file_events.get(fn, []))
        stored = sorted(db_events.get(fn, []))
        if recomputed != stored:
            all_match = False
            print(f"  MISMATCH {fn}: recomputed={recomputed}  db={stored}")
        else:
            print(f"  match     {fn}: {len(recomputed)} event(s)")

    if not all_match:
        print(f"  >>> {subject_id}: event mismatch found — writing NOTHING for this subject")
        return

    print(f"  {subject_id}: every file's recomputed events match the DB exactly "
          f"({sum(len(v) for v in db_events.values())} event(s) total)")

    written = []
    for fn in filenames:
        stem = Path(fn).stem
        score_path = subj_dir / f"{stem}.score.npy"
        recomputed_score = scores[fn]
        if score_path.exists():
            existing = np.load(score_path)
            if existing.shape == recomputed_score.shape:
                max_diff = float(np.max(np.abs(existing.astype(np.float64) - recomputed_score.astype(np.float64))))
            else:
                max_diff = float("nan")
            print(f"  exists    {stem}.score.npy — NOT overwritten "
                  f"(max abs diff vs. recomputed: {max_diff})")
            continue
        np.save(score_path, recomputed_score)
        written.append(f"{stem}.score.npy")
        print(f"  wrote     {stem}.score.npy  shape={recomputed_score.shape}  dtype={recomputed_score.dtype}")

    missing_after = [
        fn for fn in filenames if not (subj_dir / f"{Path(fn).stem}.score.npy").exists()
    ]
    print(f"  after: {len(filenames)} files, {len(missing_after)} missing .score.npy "
          f"({len(written)} written)")


def main() -> None:
    subject_ids = sys.argv[1:] or sorted(db.ALLOWED_SUBJECTS)
    t_start = time.perf_counter()
    for subject_id in subject_ids:
        backfill_subject(subject_id)
    print(f"\n=== total wall-clock: {time.perf_counter() - t_start:.1f}s ===")


if __name__ == "__main__":
    main()
