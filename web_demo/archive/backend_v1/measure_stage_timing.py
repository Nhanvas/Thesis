"""measure_stage_timing.py — pre-freeze technical timing measurement (CC_STAGE_TIMING_REPORT.md).

NOT the final thesis report numbers. This is a standalone script measuring where wall-clock
time currently goes across the demo's Phase A / Phase B / Stage 2 pipeline, per stage,
expressed as seconds per hour of EEG (so it's comparable regardless of how much EEG a run
happens to cover).

Reads the subject's real `.edf` files straight from the dataset directory
(F:/Study/Thesis/Dataset/CHB-MIT/{subject}/{subject}_*.edf`, per CLAUDE.md's documented
dataset layout) — never `web_demo/backend/uploads/` and never the app's DB. This script makes
no DB writes, no cache writes (`process_file_phase_a` is called with `cache_dir=None`), and
touches no upload/session state; the only file it writes is its own report,
`web_demo/CC_STAGE_TIMING_REPORT.md`.

Default subject `chb16`: CC_STEP9_PHASE1B_REPORT.md's fastest fully-real subject already
processed by the demo.

Usage: `python measure_stage_timing.py [subject_id]`
"""
import argparse
import statistics
import time
from pathlib import Path

import pipeline_demo as pd

DATASET_ROOT = Path("F:/Study/Thesis/Dataset/CHB-MIT")
REPORT_PATH = Path(__file__).resolve().parent.parent / "CC_STAGE_TIMING_REPORT.md"
N_REPEATS = 5
DIVERGENCE_FLAG_PCT = 2.0

# Order matches the pipeline's actual stage sequence (Phase A -> Phase B's three timed
# sub-stages plus its "everything else" residual -> Stage 2's CPD call).
STAGE_KEYS = [
    "ingest_filter",
    "adjacency_bandpower",
    "gae_scoring",
    "gamma_aec",
    "subject_stats_and_fits",
    "cpd",
]
STAGE_LABELS = {
    "ingest_filter": "Phase A: ingest + filter (process_file_phase_a, summed over files)",
    "adjacency_bandpower": "Phase B: CAR/wPLI/AEC/top-k + band powers",
    "gae_scoring": "Phase B: build_batch + GAE encoder + joint_score (x2)",
    "gamma_aec": "Phase B: compute_gamma_scores_batch",
    "subject_stats_and_fits": "Phase B: subject z-score stats + checkpoint load + LedoitWolf + robust-z fits",
    "cpd": "Stage 2: calibrate_operating_point + detect_events",
}


def _edf_files(subject_id: str) -> list[Path]:
    subj_dir = DATASET_ROOT / subject_id
    files = sorted(subj_dir.glob(f"{subject_id}_*.edf"))
    if not files:
        raise SystemExit(f"No .edf files found for {subject_id} under {subj_dir}")
    return files


def _run_once(edf_paths: list[Path]) -> tuple[dict, float, float]:
    """One full repeat: Phase A per file (never touching cache_dir/uploads/), Phase B once,
    Stage 2 once. Returns (bucket_seconds, total_wallclock_seconds, subject_total_hours)."""
    t_wall_start = time.perf_counter()

    filtered_by_filename: dict = {}
    t_ingest_filter = 0.0
    total_seconds_of_eeg = 0.0
    for edf_path in edf_paths:
        t0 = time.perf_counter()
        phase_a = pd.process_file_phase_a(str(edf_path))
        t_ingest_filter += time.perf_counter() - t0
        filtered_by_filename[phase_a.filename] = phase_a.filtered
        total_seconds_of_eeg += phase_a.file_duration_seconds

    phase_b_timing: dict = {}
    scores = pd.process_subject_phase_b(filtered_by_filename, timing=phase_b_timing)

    events_timing: dict = {}
    pd.process_subject_events(scores, timing=events_timing)

    total_wallclock = time.perf_counter() - t_wall_start
    subject_total_hours = total_seconds_of_eeg / 3600.0

    buckets = {
        "ingest_filter": t_ingest_filter,
        "adjacency_bandpower": phase_b_timing["adjacency_bandpower"],
        "gae_scoring": phase_b_timing["gae_scoring"],
        "gamma_aec": phase_b_timing["gamma_aec"],
        "subject_stats_and_fits": phase_b_timing["subject_stats_and_fits"],
        "cpd": events_timing["cpd"],
    }
    return buckets, total_wallclock, subject_total_hours


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("subject_id", nargs="?", default="chb16")
    args = parser.parse_args()
    subject_id = args.subject_id

    edf_paths = _edf_files(subject_id)
    print(f"subject: {subject_id}  ({len(edf_paths)} files from {DATASET_ROOT / subject_id})")

    per_run_rate: list[dict] = []       # per run: {stage: seconds/hour}
    per_run_total_rate: list[float] = []  # per run: total_wallclock seconds/hour
    per_run_hours: list[float] = []
    per_run_divergence_pct: list[float] = []

    for run_idx in range(1, N_REPEATS + 1):
        print(f"run {run_idx}/{N_REPEATS} ...")
        buckets, total_wallclock, subject_total_hours = _run_once(edf_paths)
        per_run_hours.append(subject_total_hours)

        sum_of_buckets = sum(buckets.values())
        pct_diff = abs(sum_of_buckets - total_wallclock) / total_wallclock * 100.0 if total_wallclock > 0 else 0.0
        per_run_divergence_pct.append(pct_diff)

        rate = {k: v / subject_total_hours for k, v in buckets.items()}
        per_run_rate.append(rate)
        per_run_total_rate.append(total_wallclock / subject_total_hours)

        flag = "  <-- FLAGGED (>2%)" if pct_diff > DIVERGENCE_FLAG_PCT else ""
        print(
            f"  subject_hours={subject_total_hours:.3f}  total_wallclock={total_wallclock:.2f}s  "
            f"sum_of_buckets={sum_of_buckets:.2f}s  divergence={pct_diff:.2f}%{flag}"
        )

    def _median_min_max(vals):
        return statistics.median(vals), min(vals), max(vals)

    stage_summary = {key: _median_min_max([r[key] for r in per_run_rate]) for key in STAGE_KEYS}
    total_summary = _median_min_max(per_run_total_rate)

    lines: list[str] = []
    lines.append("# CC_STAGE_TIMING_REPORT.md — per-stage timing breakdown")
    lines.append("")
    lines.append(
        "**Pre-freeze technical measurement — NOT the final thesis report numbers.** Produced by "
        "`web_demo/backend/measure_stage_timing.py`, purely additive instrumentation on top of the "
        "existing pipeline (see that script's and `pipeline_demo.py`'s `timing=` docstrings). Reads "
        f"real `.edf` files directly from `{DATASET_ROOT}/{subject_id}/` — never "
        "`web_demo/backend/uploads/`, never the app's DB."
    )
    lines.append("")
    lines.append(f"Subject: **{subject_id}** ({len(edf_paths)} files). Repeats: **{N_REPEATS}**.")
    lines.append("")
    lines.append("## Per-stage breakdown (seconds per hour of EEG)")
    lines.append("")
    lines.append("| Stage | Median | Min | Max |")
    lines.append("|---|---|---|---|")
    for key in STAGE_KEYS:
        med, lo, hi = stage_summary[key]
        lines.append(f"| {STAGE_LABELS[key]} | {med:.3f} | {lo:.3f} | {hi:.3f} |")
    med, lo, hi = total_summary
    lines.append(f"| **Total (outer wall-clock cross-check)** | **{med:.3f}** | {lo:.3f} | {hi:.3f} |")
    lines.append("")
    lines.append(
        "\"Total\" is measured by an independent outer wall-clock timer wrapping the whole run "
        "(Phase A over every file, then Phase B, then Stage 2) — not a sum of the stage rows above. "
        "See the per-run divergence table below for how closely the two agree."
    )
    lines.append("")
    lines.append("## Per-run sum-of-buckets vs. total wall-clock")
    lines.append("")
    lines.append("| Run | Subject hours | Total wall-clock (s) | Sum of buckets (s) | Divergence |")
    lines.append("|---|---|---|---|---|")
    any_flagged = False
    for i in range(N_REPEATS):
        total_s = per_run_total_rate[i] * per_run_hours[i]
        sum_s = sum(per_run_rate[j][k] for j, k in [(i, key) for key in STAGE_KEYS]) * per_run_hours[i]
        pct = per_run_divergence_pct[i]
        flagged = pct > DIVERGENCE_FLAG_PCT
        any_flagged = any_flagged or flagged
        marker = " **FLAGGED**" if flagged else ""
        lines.append(
            f"| {i + 1} | {per_run_hours[i]:.3f} | {total_s:.2f} | {sum_s:.2f} | {pct:.2f}%{marker} |"
        )
    lines.append("")
    lines.append(
        f"Divergence flag threshold: >{DIVERGENCE_FLAG_PCT:g}%. "
        + ("**At least one run exceeded it — see marked row(s) above.**" if any_flagged
           else "No run exceeded it.")
    )
    lines.append("")
    lines.append("## Raw per-run rates (seconds per hour of EEG)")
    lines.append("")
    header = "| Run | " + " | ".join(STAGE_KEYS) + " | total |"
    lines.append(header)
    lines.append("|" + "---|" * (len(STAGE_KEYS) + 2))
    for i in range(N_REPEATS):
        row = [f"{per_run_rate[i][key]:.3f}" for key in STAGE_KEYS]
        lines.append(f"| {i + 1} | " + " | ".join(row) + f" | {per_run_total_rate[i]:.3f} |")
    lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nwrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
