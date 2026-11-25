# M2L_L3_EVAL Version 1 — timeout at 12 h: diagnosis (chat F2-03, 25/11/2026)

**Outcome.** Version 1 (account `nhn2mm`, commit `2a06a77`, m2l_core `9690cac7f91f52b2`) was cancelled by Kaggle after
43,214 s. **No L3 result was produced**: scoring never started, and the per-recording files were written only to the
session scratch (`/tmp/r2`), which is not saved. Test, chb24 and Siena therefore remain unscored by the per-recording
protocol; Version 2 is still the one scoring (design `results/m2l/DESIGN_L2.md`). The log is `log.txt` beside this file
(the Kaggle log as downloaded by the author).

## What the log shows (all 6,318 lines read)

| time (s) | event |
|---|---|
| 84–223 | run_meta, G-sel PASS (B-MCD-F, k 9.914209, minimum length 30 min), G-raw PASS (294 EDF), G-data, G-c PASS |
| 296–638 | V5 control: R1.0-test PASS (0 rows differ), GE PASS |
| 714 | smoke (one 1-h CHB-MIT file) and PROJ PASS: projected total 3.71 h |
| 728 | four workers open four Siena files at once — the build order is file size, so these are the four largest recordings: PN14-3 (11.67 h), PN01-1 (13.49 h), PN03-1 (12.95 h), PN03-2 (11.27 h), all 512 Hz |
| 795 | **two new workers start, 67 s later** |
| 795–12,320 | the other jobs start one after another (reader warnings of the Siena and CHB-MIT files) |
| 12,320 | last activity (3.42 h) |
| 12,320–43,214 | **8.6 h without any line**; no `rec: … jobs done`, no error, no STOP |

With `maxtasksperchild=1` every job runs in a new worker, so a new worker means an earlier one has ended. A job on an
11–13 h recording cannot finish in 67 s (L2 measured about 2 min of build per hour of EEG), a skipped recording
(missing electrode) ends within about a second of opening the header, and a job error returns a message that stops the
run at once. Two workers therefore **died** about a minute into the four largest recordings. The build then continued
on schedule (activity stops near PROJ's 3.71 h), and the parent waited for the lost results until the 12-h limit.

## Measurements (`src/m2l_diag_v1.py`, synthetic data, re-runnable anywhere)

- **M1 — memory of one job's reader and filter** (`x1_external.load_18` + `filter_windows`, fresh interpreter, VmHWM):
  Siena layout 512 Hz: 1.01 GB at 1 h, 1.82 GB at 2 h → **807 MB per hour of recording**; CHB-MIT layout 256 Hz:
  1.48 GB at 2 h, 2.75 GB at 4 h → **637 MB per hour**.
- **M2 — a worker after its imports** (m2l_core, torch): 0.75–0.92 GB.
- **Computed:** the four largest Siena recordings together need about 44 GB (model without safety margin), on a Kaggle
  CPU session of about 30 GB RAM, while the parent process also holds several GB. The OS kills a process when memory
  runs out.
- **M3 — the hang mechanism, reproduced on Python 3.13.18** (the Kaggle version): `multiprocessing.Pool` (spawn,
  `maxtasksperchild=1`, as `r2_r1._pool`) with two workers killed by SIGKILL → the other 10 jobs return, then the parent
  waits without any exception. This is a known limitation of `multiprocessing.Pool` (CPython issue 22393, "Pool
  shouldn't hang forever if a worker process dies unexpectedly", open); `concurrent.futures.ProcessPoolExecutor`
  raises `BrokenProcessPool` instead.

**Why L2 and L3-short did not meet it:** they ran CHB-MIT only (recordings ≤ 4 h, ≤ 2.8 GB per job by M1).

**Measurement defect found:** `peak_rss_mb` of every L2 job is 4,607.6 MB — `getrusage(RUSAGE_SELF).ru_maxrss` keeps the
parent's high-water mark across fork / exec, so no run had measured a job's own memory. Not determinable from the log:
which recordings, and how many (at least two), were lost.

## Cause and fix

Cause: the L3 code (chat F2-03) scheduled jobs by file size with no memory model (PROJ projected time only), on a pool
that cannot report a dead worker. Fix (approved by the author 25/11 08:52; `src/m2l_sched.py`, `m2l_run.main_l3eval`;
`m2l_core.py` unchanged, so SzScan's file engine (chat C5) is unaffected):
1. memory-aware admission — estimate per job (BASE 950 MB + 810 / 640 MB per hour at 512 / 256 Hz) × 1.25; a job starts
   only if the running estimates plus its own fit in 85 % of MemAvailable; the largest recording first, reserved at
   1.5 × until its measured peak recalibrates the model;
2. `ProcessPoolExecutor`: a dead worker → STOP at once naming the recordings in flight; a job running longer than
   max(45 min, 4 × its projected time) → STOP (G-watchdog);
3. each job's own peak (VmHWM) and start / end times recorded; gate G-sched checks the admitted estimates never
   exceeded the budget;
4. PROJ simulates the memory-aware admission; STOP if one recording's estimate exceeds the budget or the total exceeds
   10.5 h;
5. synthetic test: U3 (model, over-budget STOP, simulation), P5 (one-job budget: no two jobs overlap; every
   per-recording array identical to the earlier Pool path, G-sched-equal), NEG7 (SIGKILL → STOP naming the recording,
   no hang), NEG8 (stalled job → G-watchdog), NEG9 (budget below an estimate → PROJ), all under a wall-clock limit.

No number of the protocol changes: the jobs are `m2l_core.rec_job` / `score_job` unchanged; only their timing does.
Projected Version 2 runtime (computed, 294 recordings, 441.7 h of EEG): about 4–5 h depending on the budget.
