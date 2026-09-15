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
    scores = pd.process_subject_phase_b_from_paths(payload["filtered_paths"])
    np.savez(out_path, **scores)


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
