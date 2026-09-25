"""attribution.py — Channel Attribution Panel backend (Step 7, CC_STEP7_PROMPT.md Part 2;
formula closed in Step 7 fix round 2, CC_STEP7_FIX2_PROMPT.md Part 1).

Computes an event's 18-channel attribution ON READ from the per-file `{stem}.pernode.npy`
cache (Part 1) plus the subject's persisted `pernode_baseline.npy` (fix round 2) — never
cached in the DB itself, so an edited Human event (its range changes) always gets fresh
scores. Only per-channel Accept/Reject review status is persisted (db.py's
`attribution_status` table).

Definition (CC_STEP7_FIX2_REPORT.md has the full provenance):
  1. Windows of an event: the windows whose 4 s span [4i, 4i+4) overlaps [onset_sec,
     offset_sec] — the same overlap criterion `src/attribution_pipeline.py`'s
     `_blocks_for_subject` uses (there, via a label-derived per-second array; here, directly
     from the event's own onset/offset, which the demo already has for both AI and Human
     events — no labels needed). Always at least the window containing the onset. Clamped to
     the file's usable window count.
  2-3. Aggregation and score shown per channel — CLOSED (no longer PROVISIONAL), 2026-09-25:
     score = 95th percentile of |robust-z| across the event's windows, per channel:
       z = |(window - med) / mad|          # per window, per channel
       score = percentile(z, 95, axis=0)   # [18], event-level
     `med`/`mad` are the subject's persisted whole-subject baseline (see
     `pipeline_demo.compute_pernode_baseline`) — median/MAD over every window of every file
     belonging to the subject, no 1.4826 factor. Exact same formula as
     `src/attribution_pipeline.py`'s `cmd_score` (lines ~514-520); the only difference is
     baseline scope (whole-subject recording here vs. interictal-only there), which is the
     divergence already recorded in `SZSCAN_SPEC_v5.md` §1.6 item 1, not a new one — the
     interictal-only baseline is off-limits per CLAUDE.md guard 3.
     Rank = position by the unrounded score, highest first, unaffected by status.
"""
from pathlib import Path

import numpy as np

import db
import pipeline_demo as pd

WIN_S = pd.preprocessing.WIN_S  # 4.0
CHANNELS = pd.preprocessing.COMMON_CHANNELS  # 18 names, pipeline order


def _pernode_path(subject_id: str, filename: str, upload_dir: Path) -> Path:
    stem = Path(filename).stem
    return Path(upload_dir) / subject_id / f"{stem}.pernode.npy"


def _baseline_path(subject_id: str, upload_dir: Path) -> Path:
    return Path(upload_dir) / subject_id / pd.PERNODE_BASELINE_FILENAME


def _event_windows(onset_sec: float, offset_sec: float, n_windows: int) -> tuple[int, int]:
    """Item 1: window i spans [4i, 4i+4). Included if that span overlaps [onset, offset).
    Always at least the window containing the onset. Clamped to [0, n_windows-1]."""
    lo = int(onset_sec // WIN_S)
    # Last window whose start (4*i) is still < offset_sec (i.e. its span overlaps the event,
    # not just touches its boundary) — for a zero/negative-length remainder this still keeps
    # at least `lo` via the max() below.
    hi = int(np.ceil(offset_sec / WIN_S)) - 1
    hi = max(hi, lo)
    lo = max(0, min(lo, n_windows - 1))
    hi = max(0, min(hi, n_windows - 1))
    return lo, hi


def get_event_attribution(event: dict, file_row: dict, upload_dir: Path) -> dict:
    """GET /api/events/{id}/attribution's payload. Works identically for AI and Human
    events — attribution is computed from the event's own onset/offset either way."""
    pernode_path = _pernode_path(file_row["subject_id"], file_row["filename"], upload_dir)
    baseline_path = _baseline_path(file_row["subject_id"], upload_dir)
    if not pernode_path.exists() or not baseline_path.exists():
        # Same shape for both causes (missing `.pernode.npy` — Step 7 Part 4 item 12 — and a
        # not-yet-backfilled subject missing its baseline, fix round 2 Part 1): never silently
        # compute the baseline on the fly.
        return {
            "available": False,
            "event_id": event["id"],
            "event_name": event["name"],
            "message": "Attribution is not available for this file.",
        }

    pernode = np.load(pernode_path, mmap_mode="r")  # [n_windows, 18] float32
    n_windows = pernode.shape[0]
    lo, hi = _event_windows(event["onset_sec"], event["offset_sec"], n_windows)
    window_scores = np.asarray(pernode[lo : hi + 1]).astype(np.float64)  # [k, 18]

    baseline = np.load(baseline_path).astype(np.float64)  # [2, 18]: row 0 = median, row 1 = MAD
    med, mad = baseline[0], baseline[1]
    z = np.abs((window_scores - med) / mad)  # [k, 18], per window per channel
    per_channel = np.percentile(z, 95, axis=0)  # items 2-3: p95 |robust-z|, event-level score
    order = np.argsort(-per_channel)  # item 3: rank = position by score, highest first
    rank_of = np.empty(len(CHANNELS), dtype=int)
    rank_of[order] = np.arange(1, len(CHANNELS) + 1)

    saved_status = db.get_attribution_status(event["id"])
    rows = [
        {
            "channel": CHANNELS[i],
            "score": round(float(per_channel[i]), 6),
            "rank": int(rank_of[i]),
            "status": saved_status.get(CHANNELS[i]),
        }
        for i in range(len(CHANNELS))
    ]
    rows.sort(key=lambda r: r["rank"])

    return {
        "available": True,
        "event_id": event["id"],
        "event_name": event["name"],
        "window_lo": lo,
        "window_hi": hi,
        "window_lo_sec": lo * WIN_S,
        "window_hi_sec": (hi + 1) * WIN_S,
        "n_windows_used": hi - lo + 1,
        "rows": rows,
    }
