# CC_STAGE_TIMING_REPORT.md — per-stage timing breakdown

**Pre-freeze technical measurement — NOT the final thesis report numbers.** Produced by `web_demo/backend/measure_stage_timing.py`, purely additive instrumentation on top of the existing pipeline (see that script's and `pipeline_demo.py`'s `timing=` docstrings). Reads real `.edf` files directly from `F:\Study\Thesis\Dataset\CHB-MIT/chb16/` — never `web_demo/backend/uploads/`, never the app's DB.

Subject: **chb16** (19 files). Repeats: **5**.

## Per-stage breakdown (seconds per hour of EEG)

| Stage | Median | Min | Max |
|---|---|---|---|
| Phase A: ingest + filter (process_file_phase_a, summed over files) | 1.202 | 1.140 | 1.836 |
| Phase B: CAR/wPLI/AEC/top-k + band powers | 4.905 | 4.659 | 5.805 |
| Phase B: build_batch + GAE encoder + joint_score (x2) | 0.225 | 0.220 | 0.272 |
| Phase B: compute_gamma_scores_batch | 1.725 | 1.634 | 1.900 |
| Phase B: subject z-score stats + checkpoint load + LedoitWolf + robust-z fits | 0.358 | 0.349 | 0.539 |
| Stage 2: calibrate_operating_point + detect_events | 2.631 | 2.369 | 2.764 |
| **Total (outer wall-clock cross-check)** | **10.829** | 10.694 | 12.472 |

"Total" is measured by an independent outer wall-clock timer wrapping the whole run (Phase A over every file, then Phase B, then Stage 2) — not a sum of the stage rows above. See the per-run divergence table below for how closely the two agree.

## Per-run sum-of-buckets vs. total wall-clock

| Run | Subject hours | Total wall-clock (s) | Sum of buckets (s) | Divergence |
|---|---|---|---|---|
| 1 | 19.000 | 224.19 | 224.16 | 0.01% |
| 2 | 19.000 | 205.49 | 205.46 | 0.02% |
| 3 | 19.000 | 236.97 | 236.94 | 0.01% |
| 4 | 19.000 | 205.76 | 205.73 | 0.02% |
| 5 | 19.000 | 203.18 | 203.15 | 0.01% |

Divergence flag threshold: >2%. No run exceeded it.

## Raw per-run rates (seconds per hour of EEG)

| Run | ingest_filter | adjacency_bandpower | gae_scoring | gamma_aec | subject_stats_and_fits | cpd | total |
|---|---|---|---|---|---|---|---|
| 1 | 1.836 | 5.084 | 0.232 | 1.738 | 0.539 | 2.369 | 11.800 |
| 2 | 1.140 | 4.742 | 0.224 | 1.725 | 0.351 | 2.631 | 10.815 |
| 3 | 1.340 | 5.805 | 0.272 | 1.900 | 0.391 | 2.764 | 12.472 |
| 4 | 1.202 | 4.905 | 0.225 | 1.658 | 0.358 | 2.480 | 10.829 |
| 5 | 1.175 | 4.659 | 0.220 | 1.634 | 0.349 | 2.656 | 10.694 |
