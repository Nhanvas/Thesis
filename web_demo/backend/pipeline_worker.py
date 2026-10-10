"""pipeline_worker.py — standalone CLI entry points for the two CPU-heavy stages of
pipeline_demo.py (Phase B, and stage-2 Process: detector + localizer), run as a genuinely separate OS
process launched via subprocess.Popen from upload_manager.py. Both stages run the final thesis
system (pipeline_demo.py: GAE v2 latent anomaly, per-patient alarm budget, kernel-CPD localizer).

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
    """Phase B of the final system: per-file ensemble score (key = filename) and per-channel
    latent distance (key = "dist__" + filename) in one .npz; the channel-panel arrays are also
    written next to each file's `.filtered.npy` in the (still-draft) subject directory, which
    `_finalize_draft_dir` (upload_manager.py) later moves as one unit."""
    filtered_paths = payload["filtered_paths"]
    res = pd.process_subject_phase_b_from_paths(
        filtered_paths, payload["flag_paths"], payload["moments_paths"]
    )
    arrays = dict(res.scores)
    arrays.update({f"dist__{fn}": d for fn, d in res.dists.items()})
    np.savez(out_path, **arrays)
    for fn, d in res.dists.items():
        filtered_path = Path(filtered_paths[fn])
        stem = filtered_path.name.removesuffix(".filtered.npy")
        np.save(filtered_path.with_name(f"{stem}.pernode.npy"), d.astype(np.float32))
    any_filtered_path = Path(next(iter(filtered_paths.values())))
    np.save(any_filtered_path.with_name(pd.PERNODE_BASELINE_FILENAME), res.baseline)


_FLAG_KEY_PREFIX = "flag__"
_DIST_KEY_PREFIX = "dist__"


def _run_process_events(payload: dict, out_path: str) -> None:
    with np.load(payload["score_npz_path"]) as data:
        scores, flags, dists = {}, {}, {}
        for key in data.files:
            if key.startswith(_FLAG_KEY_PREFIX):
                flags[key[len(_FLAG_KEY_PREFIX):]] = data[key]
            elif key.startswith(_DIST_KEY_PREFIX):
                dists[key[len(_DIST_KEY_PREFIX):]] = data[key]
            else:
                scores[key] = data[key]
    file_events, budget = pd.process_subject_events(scores, flags, dists)
    result = {
        "alarm_budget": budget.top,
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
