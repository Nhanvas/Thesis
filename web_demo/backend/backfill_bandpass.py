"""backfill_bandpass.py — one-time backfill for the "collapse EEG filter toggles to 2 real
ones" change (CC_FIX_FILTERSTAGES_REPORT.md): produces `{stem}.bandpass.npy` for every file
already in the DB, so waveform_serving.get_waveform (which now unconditionally reads that
cache alongside `.raw.npy`/`.filtered.npy`) doesn't 404 on subjects processed before this
change.

Scope, deliberately narrow, same pattern as backfill_pernode.py:
  - Groups the DB's `files` rows by subject_id.
  - For each file whose `.bandpass.npy` is missing but whose original `.edf` is still present
    under `uploads/{subject_id}/`, re-runs `pipeline_demo.process_file_phase_a` on that EDF
    with `cache_dir` pointed at the subject's upload folder.
  - This is the exact same production code path the original upload used, so the re-written
    `.raw.npy`/`.filtered.npy` are bit-identical to what's already on disk (verified below by
    comparing bytes before overwriting) — this script's only NET effect is the new
    `.bandpass.npy` file. Never touches the DB, events, or `.score.npy`/`.pernode.npy`.
  - A file with no `.bandpass.npy` and no `.edf` on disk is skipped and listed — there's no
    source left to recompute it from.
"""
import sys
from pathlib import Path

import numpy as np

import db
import pipeline_demo as pd

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"


def main(subject_filter: set[str] | None = None) -> None:
    conn = db.get_connection()
    rows = conn.execute("SELECT subject_id, filename FROM files ORDER BY subject_id, id").fetchall()
    conn.close()

    by_subject: dict[str, list[str]] = {}
    for r in rows:
        if subject_filter is not None and r["subject_id"] not in subject_filter:
            continue
        by_subject.setdefault(r["subject_id"], []).append(r["filename"])

    produced: list[str] = []
    skipped: list[str] = []
    already_ok: list[str] = []

    for subject_id, filenames in sorted(by_subject.items()):
        cache_dir = UPLOAD_DIR / subject_id
        for fn in filenames:
            stem = Path(fn).stem
            bp_path = cache_dir / f"{stem}.bandpass.npy"
            if bp_path.exists():
                already_ok.append(f"{subject_id}/{fn}")
                continue

            edf_path = cache_dir / fn
            if not edf_path.exists():
                skipped.append(f"{subject_id}/{fn} (no .bandpass.npy and no source .edf)")
                continue

            raw_path = cache_dir / f"{stem}.raw.npy"
            filtered_path = cache_dir / f"{stem}.filtered.npy"
            before_raw = raw_path.read_bytes() if raw_path.exists() else None
            before_filtered = filtered_path.read_bytes() if filtered_path.exists() else None

            print(f"[{subject_id}] re-running Phase A on {fn} to produce {bp_path.name}")
            pd.process_file_phase_a(str(edf_path), cache_dir=cache_dir)

            if before_raw is not None:
                after_raw = raw_path.read_bytes()
                assert after_raw == before_raw, (
                    f"{subject_id}/{fn}: .raw.npy changed on re-run — refusing to trust this backfill"
                )
            if before_filtered is not None:
                after_filtered = filtered_path.read_bytes()
                assert after_filtered == before_filtered, (
                    f"{subject_id}/{fn}: .filtered.npy changed on re-run — refusing to trust this backfill"
                )

            produced.append(f"{subject_id}/{fn}")

    print("\n=== backfill_bandpass summary ===")
    print(f"produced ({len(produced)}):")
    for p in produced:
        print(f"  {p}")
    print(f"already had .bandpass.npy ({len(already_ok)})")
    print(f"skipped ({len(skipped)}):")
    for s in skipped:
        print(f"  {s}")


if __name__ == "__main__":
    # Optional: python backfill_bandpass.py chb16 chb03 — restrict to given subject_id(s).
    # No args = every subject in the DB.
    main(set(sys.argv[1:]) or None)
