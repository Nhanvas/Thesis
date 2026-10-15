"""Ad hoc timing script for CC_PART2_PART4_PROMPT.md Part B.

Repeats Phase A / Phase B / Stage 2 on ONE reference recording (chb06_01.edf, the four-hour
file behind CLAUDE.md's 9.76 s/hour figure) 5 times, using pipeline_demo.py's own instrumented
functions (same ones the app calls) and existing timing= dicts -- same pattern as
web_demo/backend/measure_stage_timing.py, but pinned to this single file rather than a whole
subject, and using process_subject_events() (the FIXED_PEN_MULT/FIXED_MAG_PCT path the live
app actually runs) rather than the old calibrate_operating_point() grid search.

Never touches the DB, never touches web_demo/backend/uploads/ (process_file_phase_a called
with cache_dir=None). Writes web_demo/report_handback/timing_repeated.csv only (a data output,
not code -- CC_PART2_PART4_PROMPT.md exempts report_handback/ from the "no code changes" rule).
This script itself lives outside web_demo/ entirely.
"""
import csv
import statistics
import sys
import time
from pathlib import Path

REPO_ROOT = Path("F:/Study/Thesis/Code")
BACKEND_DIR = REPO_ROOT / "web_demo" / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import pipeline_demo as pd  # noqa: E402

EDF_PATH = Path("F:/Study/Thesis/Dataset/CHB-MIT/chb06/chb06_01.edf")
OUT_CSV = REPO_ROOT / "web_demo" / "report_handback" / "timing_repeated.csv"
N_REPEATS = 5

STAGE_KEYS = [
    "ingest_filter",
    "adjacency_bandpower",
    "gae_scoring",
    "gamma_aec",
    "subject_stats_and_fits",
    "cpd",
    "total",
]


def run_once():
    t_wall_start = time.perf_counter()

    t0 = time.perf_counter()
    phase_a = pd.process_file_phase_a(str(EDF_PATH), cache_dir=None)
    t_ingest_filter = time.perf_counter() - t0
    eeg_hours = phase_a.file_duration_seconds / 3600.0

    phase_b_timing: dict = {}
    scores = pd.process_subject_phase_b({phase_a.filename: phase_a.filtered}, timing=phase_b_timing)

    events_timing: dict = {}
    pd.process_subject_events(scores, timing=events_timing)

    total_wallclock = time.perf_counter() - t_wall_start

    buckets = {
        "ingest_filter": t_ingest_filter,
        "adjacency_bandpower": phase_b_timing["adjacency_bandpower"],
        "gae_scoring": phase_b_timing["gae_scoring"],
        "gamma_aec": phase_b_timing["gamma_aec"],
        "subject_stats_and_fits": phase_b_timing["subject_stats_and_fits"],
        "cpd": events_timing["cpd"],
        "total": total_wallclock,
    }
    return buckets, eeg_hours


def main():
    print(f"file: {EDF_PATH}")
    if not EDF_PATH.exists():
        raise SystemExit(f"missing: {EDF_PATH}")

    rows = []
    per_run_rate = {k: [] for k in STAGE_KEYS}

    for run_idx in range(1, N_REPEATS + 1):
        print(f"run {run_idx}/{N_REPEATS} ...")
        buckets, eeg_hours = run_once()
        sum_of_buckets = sum(v for k, v in buckets.items() if k != "total")
        pct = abs(sum_of_buckets - buckets["total"]) / buckets["total"] * 100.0
        print(f"  eeg_hours={eeg_hours:.4f}  total={buckets['total']:.2f}s  "
              f"sum_of_buckets={sum_of_buckets:.2f}s  divergence={pct:.2f}%")
        for stage in STAGE_KEYS:
            seconds = buckets[stage]
            rows.append(dict(run=run_idx, stage=stage, seconds=seconds, eeg_hours=eeg_hours))
            per_run_rate[stage].append(seconds / eeg_hours)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["run", "stage", "seconds", "eeg_hours"])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"\nwrote {OUT_CSV}")

    print("\nstage, median s/h, min s/h, max s/h")
    for stage in STAGE_KEYS:
        vals = per_run_rate[stage]
        print(f"{stage}: median={statistics.median(vals):.4f} min={min(vals):.4f} max={max(vals):.4f}")


if __name__ == "__main__":
    main()
