"""backfill_pernode.py — Step 7 (CC_STEP7_PROMPT.md Part 1 item 3): produce `{stem}.pernode.npy`
for every file that already exists in the DB, without re-running CPD/Stage 2 (which would write
new events and lose review states).

Step 7 fix round 2 (CC_STEP7_FIX2_PROMPT.md Part 2) added a second, separate entry point,
`backfill_baselines()` below (run via `python backfill_pernode.py --baseline`): computes and
writes `{subj}/pernode_baseline.npy` for every subject currently in the DB, reading ONLY each
file's already-cached `.pernode.npy` (produced by `main()` below or by the live Process flow) —
never runs the model, never re-reads raw EDFs, never touches CPD or the events table. Deliberately
a separate function (different inputs — `.pernode.npy`, not `.filtered.npy`; different output —
one small baseline file per subject, not one array per file) rather than folded into `main()`.

Scope, deliberately narrow:
  - Groups the DB's `files` rows by subject_id (the same grouping pipeline_demo.process_subject_
    phase_b originally used to fit its subject-wide z-score/LedoitWolf/robust-z stats).
  - Loads each file's ALREADY-CACHED `{stem}.filtered.npy` (Phase A's output, written when the
    file was first uploaded) instead of re-reading the source EDF — this is the exact array Phase
    B originally consumed, so re-running Phase B's model-scoring step on it reproduces the
    existing `{stem}.score.npy` bit-for-bit (verified by the sha256 before/after check this
    script's caller runs separately — this script itself never writes to `.score.npy`).
  - Calls `pipeline_demo.process_subject_phase_b(..., pernode_out=...)` — the SAME function the
    live Process flow now uses (see pipeline_worker.py) — and keeps only the new `pernode_out`
    dict; the returned ensemble `scores` dict is discarded unread, never written anywhere.
  - Never calls `cpd_pipeline_v14.detect_events` / `process_subject_events` / `db.create_subject_
    with_files` — no event is created, edited or renumbered by this script.

Note on the prompt's "Phase A only" wording: per-node reconstruction scores require a GAE model
forward pass, which in this codebase's Phase A/Phase B split lives in Phase B (Phase A is just
open/filter/window, no model). This script therefore runs Phase B's model-scoring step (reusing
already-cached Phase A output), NOT Stage 2/CPD — see the report's Part 1 section for the reading
adopted here.

If a file's `.filtered.npy` cache is missing, it is skipped and listed — the attribution API's
"not available for this file" path (Part 2) covers it live.
"""
import sys
from pathlib import Path

import numpy as np

import db
import pipeline_demo as pd

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"


def _cache_dir(subject_id: str) -> Path:
    return UPLOAD_DIR / subject_id


def main() -> None:
    conn = db.get_connection()
    rows = conn.execute("SELECT subject_id, filename FROM files ORDER BY subject_id, id").fetchall()
    conn.close()

    by_subject: dict[str, list[str]] = {}
    for r in rows:
        by_subject.setdefault(r["subject_id"], []).append(r["filename"])

    produced: list[str] = []
    skipped: list[str] = []

    for subject_id, filenames in sorted(by_subject.items()):
        cache_dir = _cache_dir(subject_id)
        filtered_by_filename = {}
        missing = []
        for fn in filenames:
            stem = Path(fn).stem
            fpath = cache_dir / f"{stem}.filtered.npy"
            if fpath.exists():
                filtered_by_filename[fn] = np.load(fpath)
            else:
                missing.append(fn)

        for fn in missing:
            skipped.append(f"{subject_id}/{fn} (no cached .filtered.npy)")

        if not filtered_by_filename:
            continue

        pernode_out: dict = {}
        print(f"[{subject_id}] running Phase B model-scoring for {sorted(filtered_by_filename)} "
              f"(pernode only — ensemble score result discarded, never written)")
        pd.process_subject_phase_b(filtered_by_filename, pernode_out=pernode_out)

        for fn, arr in pernode_out.items():
            stem = Path(fn).stem
            out_path = cache_dir / f"{stem}.pernode.npy"
            np.save(out_path, arr)
            produced.append(str(out_path.relative_to(UPLOAD_DIR)))
            print(f"  wrote {out_path.relative_to(UPLOAD_DIR)}  shape={arr.shape}  dtype={arr.dtype}")

    print("\n=== backfill_pernode summary ===")
    print(f"produced ({len(produced)}):")
    for p in produced:
        print(f"  {p}")
    print(f"skipped ({len(skipped)}):")
    for s in skipped:
        print(f"  {s}")


def backfill_baselines() -> None:
    """CC_STEP7_FIX2_PROMPT.md Part 2: compute + write `{subj}/pernode_baseline.npy` for every
    subject currently in the DB, reading only each file's already-cached `.pernode.npy` —
    never runs the model, never re-reads a raw EDF, never touches CPD/the events table.

    If any of a subject's files is missing its `.pernode.npy` cache, that whole subject is
    skipped (not a partial baseline built from a subset of its files) — run `main()` above
    first to fill any gaps, then re-run this.
    """
    conn = db.get_connection()
    rows = conn.execute("SELECT subject_id, filename FROM files ORDER BY subject_id, id").fetchall()
    conn.close()

    by_subject: dict[str, list[str]] = {}
    for r in rows:
        by_subject.setdefault(r["subject_id"], []).append(r["filename"])

    produced: list[str] = []
    skipped: list[str] = []

    for subject_id, filenames in sorted(by_subject.items()):
        cache_dir = _cache_dir(subject_id)
        pernode_arrays = []
        missing = []
        for fn in filenames:
            stem = Path(fn).stem
            ppath = cache_dir / f"{stem}.pernode.npy"
            if ppath.exists():
                pernode_arrays.append(np.load(ppath))
            else:
                missing.append(fn)

        if missing:
            skipped.append(f"{subject_id} (missing .pernode.npy for {missing} — whole subject skipped)")
            continue

        baseline = pd.compute_pernode_baseline(pernode_arrays)
        out_path = cache_dir / pd.PERNODE_BASELINE_FILENAME
        np.save(out_path, baseline)
        produced.append(str(out_path.relative_to(UPLOAD_DIR)))
        print(f"  wrote {out_path.relative_to(UPLOAD_DIR)}  shape={baseline.shape}  "
              f"dtype={baseline.dtype}  (from {len(pernode_arrays)} files)")

    print("\n=== backfill_baselines summary ===")
    print(f"produced ({len(produced)}):")
    for p in produced:
        print(f"  {p}")
    print(f"skipped ({len(skipped)}):")
    for s in skipped:
        print(f"  {s}")


if __name__ == "__main__":
    if "--baseline" in sys.argv:
        sys.exit(backfill_baselines())
    sys.exit(main())
