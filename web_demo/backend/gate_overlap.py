"""gate_overlap.py -- chb03-only overlap check between the identity gate's thesis-statistics run
and the demo's own label-free run (T1 run, gate-only; never imported by main.py, upload_manager.py
or pipeline_worker.py -- the application tier never uses this, same status as stats_override).

Reads the Phase A cache that `src/t1_demo_gate.py gate --keep-cache` leaves under
`F:/Study/Thesis/Agent/t1_demo/cache/gate/` ({stem}.filtered.npy, .flag.npy, .moments.npy -- the
same layout `t1_demo_gate.cmd_gate` itself reads back, see that function's filt/flags/moms loads).
Runs Phase B + Stage 2 (pipeline_demo.process_subject_phase_b / .process_subject_events) twice on
chb03: once fed the thesis's z-score statistics (data/processed/chb03_stats.json, ch_mean_uV /
ch_std_uV x 1e-6, exactly as t1_demo_gate.thesis_stats()), once with stats_override=None (the
demo's own label-free statistics). Compares the two runs' LOCALIZED events per file: event counts,
and overlap (any non-empty intersection in seconds, within the same file -- events never cross a
file). Writes the per-event table to web_demo/report_handback/gate_overlap_chb03.csv.

Reads no annotation, calls no thesis function that reads one (same guard as pipeline_demo.py).

  python gate_overlap.py [--cache F:/Study/Thesis/Agent/t1_demo/cache/gate] [--out ...]
"""
import argparse
import csv
import json
from pathlib import Path

import numpy as np

import pipeline_demo as pd

SUBJ = "chb03"
DEFAULT_OUT = Path(__file__).resolve().parents[1] / "report_handback" / "gate_overlap_chb03.csv"


def thesis_stats():
    st = json.loads((pd.REPO_ROOT / "data" / "processed" / f"{SUBJ}_stats.json").read_text())
    return np.asarray(st["ch_mean_uV"], float) * 1e-6, np.asarray(st["ch_std_uV"], float) * 1e-6


def load_cache(cache_dir: Path):
    stems = sorted(p.name[: -len(".filtered.npy")] for p in cache_dir.glob("*.filtered.npy"))
    if not stems:
        raise SystemExit(f"STOP: no {{stem}}.filtered.npy under {cache_dir} -- run "
                          "`python src/t1_demo_gate.py gate --keep-cache` first")
    names = [f"{s}.edf" for s in stems]
    filt = {n: np.load(cache_dir / f"{s}.filtered.npy", mmap_mode="r") for n, s in zip(names, stems)}
    flags = {n: np.load(cache_dir / f"{s}.flag.npy") for n, s in zip(names, stems)}
    moms = {n: np.load(cache_dir / f"{s}.moments.npy") for n, s in zip(names, stems)}
    return names, filt, flags, moms


def run(filt, flags, moms, stats_override):
    b = pd.process_subject_phase_b(filt, flags, moms, stats_override=stats_override)
    trace = {}
    events, budget = pd.process_subject_events(b.scores, flags, b.dists, trace=trace)
    return {f: [(e.onset_sec, e.offset_sec) for e in v] for f, v in events.items()}, budget


def overlaps(a, b):
    return a[0] < b[1] and b[0] < a[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache", default="F:/Study/Thesis/Agent/t1_demo/cache/gate")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    a = ap.parse_args()
    names, filt, flags, moms = load_cache(Path(a.cache))

    print(f"{len(names)} files from the cache: {names}")
    print("thesis-statistics run ...", flush=True)
    ev_t, budget_t = run(filt, flags, moms, thesis_stats())
    print("label-free run ...", flush=True)
    ev_l, budget_l = run(filt, flags, moms, None)

    rows = []
    n_t = n_l = n_l_overlapping = n_t_overlapped = 0
    for n in names:
        et, el = ev_t.get(n, []), ev_l.get(n, [])
        n_t += len(et)
        n_l += len(el)
        t_hit = [False] * len(et)
        for j, le in enumerate(el):
            hit = [i for i, te in enumerate(et) if overlaps(le, te)]
            if hit:
                n_l_overlapping += 1
                for i in hit:
                    t_hit[i] = True
            rows.append(dict(file=n, run="label_free", event_id=j, onset_s=round(le[0], 3),
                              offset_s=round(le[1], 3), overlapped=bool(hit)))
        n_t_overlapped += sum(t_hit)
        for i, te in enumerate(et):
            rows.append(dict(file=n, run="thesis_stat", event_id=i, onset_s=round(te[0], 3),
                              offset_s=round(te[1], 3), overlapped=t_hit[i]))

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "run", "event_id", "onset_s", "offset_s", "overlapped"])
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["file"], r["run"], r["event_id"])))

    print(f"demo (label-free) localized events = {n_l}")
    print(f"thesis-stat localized events = {n_t}")
    print(f"label-free events overlapping a thesis-stat event = {n_l_overlapping} / {n_l}")
    print(f"thesis-stat events overlapped by a label-free event = {n_t_overlapped} / {n_t}")
    print(f"alarm budget: thesis-stat top {budget_t.top:.6f} q {budget_t.q:.6f} | "
          f"label-free top {budget_l.top:.6f} q {budget_l.q:.6f}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
