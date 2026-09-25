"""pipeline_worker.py — standalone CLI entry points for the two CPU-heavy stages of
pipeline_demo.py (Phase B, and stage-2 Process/PELT), run as a genuinely separate OS
process launched via subprocess.Popen from upload_manager.py.

Why a subprocess instead of a background thread or a concurrent.futures.ProcessPoolExecutor
worker: measured on this Windows dev machine, BOTH a threading.Thread and a
ProcessPoolExecutor worker hang indefinitely at 0% CPU when the GAE/PELT pipeline is invoked
from inside the uvicorn-hosted process — reproducible only in that hosting context; the
identical call in a plain, non-uvicorn Python process (this script, run directly) never
hangs. A subprocess.Popen child is a fully independent OS process created via a normal
CreateProcess call, with none of multiprocessing's spawn bootstrap or asyncio-loop
inheritance from the parent — and that reliably does not hang. See upload_manager.py's
`_run_worker` for the calling side.

Talks to the parent over two small JSON files (input, output) plus paths to the .npy/.npz
arrays already sitting on disk — never large arrays over stdio/pipes.
"""
import argparse
import json
from pathlib import Path

import numpy as np

import pipeline_demo as pd


def _run_phase_b(payload: dict, out_path: str) -> None:
    filtered_paths = payload["filtered_paths"]
    pernode = {}
    pernode_baseline: dict = {}
    scores = pd.process_subject_phase_b_from_paths(
        filtered_paths, pernode_out=pernode, pernode_baseline_out=pernode_baseline
    )
    np.savez(out_path, **scores)
    # Step 7 (CC_STEP7_PROMPT.md Part 1 item 1): persist the per-node array next to the
    # already-written `{stem}.filtered.npy`/`.raw.npy` in the same (still-draft) directory —
    # `_finalize_draft_dir` in upload_manager.py moves the whole directory as one unit once
    # Process locks in the subject id, so this rides along automatically. Never touches
    # `.score.npy` or any other existing output.
    for fn, arr in pernode.items():
        filtered_path = Path(filtered_paths[fn])
        stem = filtered_path.name.removesuffix(".filtered.npy")
        pernode_path = filtered_path.with_name(f"{stem}.pernode.npy")
        np.save(pernode_path, arr)
    if "baseline" in pernode_baseline:
        # Step 7 fix round 2 (CC_STEP7_FIX2_PROMPT.md Part 1): same rides-along mechanism as
        # the per-file `.pernode.npy` arrays above — written into this still-draft directory
        # under a subject-agnostic name (the subject id/Project ID isn't locked in yet at this
        # point, see pipeline_demo.PERNODE_BASELINE_FILENAME's own comment), so it ends up at
        # `uploads/{subject_id}/pernode_baseline.npy` once `_finalize_draft_dir` moves the
        # whole directory.
        any_filtered_path = Path(next(iter(filtered_paths.values())))
        baseline_path = any_filtered_path.with_name(pd.PERNODE_BASELINE_FILENAME)
        np.save(baseline_path, pernode_baseline["baseline"])


def _run_process_events(payload: dict, out_path: str) -> None:
    with np.load(payload["score_npz_path"]) as data:
        scores = {fn: data[fn] for fn in data.files}
    file_events, op = pd.process_subject_events(scores)
    result = {
        "pen_mult": op.pen_mult,
        "event_rate_per_day": op.event_rate_per_day,
        "grid": op.grid,
        "events": {
            fn: [[e.onset_sec, e.offset_sec] for e in evs] for fn, evs in file_events.items()
        },
    }
    Path(out_path).write_text(json.dumps(result))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["phase_b", "process_events"])
    parser.add_argument("in_path", help="JSON file with this mode's input payload")
    parser.add_argument("out_path", help="Where to write the result (.npz for phase_b, .json for process_events)")
    args = parser.parse_args()

    payload = json.loads(Path(args.in_path).read_text())
    if args.mode == "phase_b":
        _run_phase_b(payload, args.out_path)
    else:
        _run_process_events(payload, args.out_path)


if __name__ == "__main__":
    main()
