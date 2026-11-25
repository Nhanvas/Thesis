#!/usr/bin/env python
"""
m2l_sched.py -- memory-aware job scheduler of the M2L per-recording build (chat F2-03, 25/11/2026; approved by the author
25/11 08:52). Written after the diagnosis of M2L_L3_EVAL Version 1 and before any L3 output.

Diagnosis (results/m2l/l3eval_v1_timeout/DIAGNOSIS.md): Version 1 sorted the jobs by file size, so the four longest Siena
recordings (PN14-3 11.7 h, PN01-1 13.5 h, PN03-1 13.0 h, PN03-2 11.3 h, 512 Hz) started together on 4 workers; their
peak memory (computed from the measured model below, about 38 GB) exceeded the session's RAM; the OS killed two
workers 67 s after they started; multiprocessing.Pool does not report a lost task (CPython issue 22393, reproduced on
Python 3.13.18), so the parent waited 8.6 h for two results that never came, until the 12-h limit. No L3 result was
produced (scoring never started).

This module changes WHEN a job runs, never WHAT it computes: every job is m2l_core.rec_job / score_job unchanged.
  memory model   peak MB of one job = (BASE_MB + hours x MB_PER_H(sfreq)) x SAFETY, measured 25/11 on synthetic EDF
                 files with the record reader and filter (x1_external.load_18 + filter_windows; src/m2l_diag_v1.py M1):
                 Siena path 512 Hz 1.01 GB at 1 h, 1.82 GB at 2 h (807 MB per hour); CHB-MIT path 256 Hz 1.48 GB at
                 2 h, 2.75 GB at 4 h (637 MB per hour); a worker after its imports (m2l_core, torch) 0.75-0.92 GB (M2).
                 Slopes rounded up to 810 / 640, BASE_MB 950; SAFETY 1.25.
  budget         BUDGET_FRAC x MemAvailable when the build starts (the parent's own memory is already excluded)
  admission      largest estimate first; a job starts only if the estimates of the running jobs plus its own fit in the
                 budget (and a worker is free); while the first (largest) job is not yet measured it is reserved at
                 UNCAL x its estimate; when it ends, every estimate is scaled by max(1, measured / model)
  dead worker    concurrent.futures.ProcessPoolExecutor raises BrokenProcessPool when a worker dies -> STOP at once,
                 naming the recordings in flight (never a silent wait)
  watchdog       a job running longer than max(WATCHDOG_MIN_S, WATCHDOG_X x its projected time) -> STOP
  measurement    each job reports its own peak (VmHWM of /proc/self/status; ru_maxrss is inherited across exec and gave
                 the parent's 4,607.6 MB for every L2 job); start / end times for the G-sched self-check
Test hooks (synthetic world only, R2_TEST=1): M2L_TEST_KILL=<file> (the job kills itself), M2L_TEST_HANG=<file>,
M2L_TEST_BUDGET_MB, M2L_TEST_WATCHDOG_S.
"""
import os
import signal
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from concurrent.futures.process import BrokenProcessPool
from pathlib import Path

import m2l_core as M

R1 = M.R1
log = M.log
BASE_MB = 950.0                          # worker after imports (measured 0.92 GB) -- rounded up
MB_PER_H = {256: 640.0, 512: 810.0}      # measured slopes, rounded up (see header)
SAFETY = 1.25
UNCAL = 1.5
BUDGET_FRAC = 0.85
WATCHDOG_MIN_S, WATCHDOG_X = 2700.0, 4.0
POLL_S = 15.0


def mb_per_h(sfreq):
    """measured slope; other rates: the 512-Hz slope scaled by the rate, never below the 256-Hz slope."""
    s = int(round(float(sfreq)))
    return MB_PER_H.get(s, max(MB_PER_H[256], MB_PER_H[512] * s / 512.0))


def estimate_mb(hours, sfreq):
    return (BASE_MB + float(hours) * mb_per_h(sfreq)) * SAFETY


def edf_header(path):
    """(hours, sfreq) from the EDF header only."""
    import mne
    raw = mne.io.read_raw_edf(str(path), preload=False, verbose=False)
    return float(raw.n_times / raw.info["sfreq"] / 3600), float(raw.info["sfreq"])


def _meminfo(key):
    for ln in open("/proc/meminfo"):
        if ln.startswith(key + ":"):
            return float(ln.split()[1]) / 1024.0
    return float("nan")


def memory_budget_mb():
    """BUDGET_FRAC x MemAvailable now (MB); the test world may fix it (M2L_TEST_BUDGET_MB)."""
    if M.TEST_MODE and os.environ.get("M2L_TEST_BUDGET_MB"):
        return float(os.environ["M2L_TEST_BUDGET_MB"]), dict(source="test override")
    avail, total = _meminfo("MemAvailable"), _meminfo("MemTotal")
    return BUDGET_FRAC * avail, dict(source="MemAvailable", mem_available_mb=round(avail), mem_total_mb=round(total))


def vmhwm_mb():
    try:
        for ln in open("/proc/self/status"):
            if ln.startswith("VmHWM:"):
                return float(ln.split()[1]) / 1024.0
    except OSError:
        pass
    return float("nan")


def _test_hooks(a):
    if not M.TEST_MODE:
        return
    name = Path(str(a[2])).name if len(a) > 2 else ""
    if name and name == os.environ.get("M2L_TEST_KILL"):
        os.kill(os.getpid(), signal.SIGKILL)
    if name and name == os.environ.get("M2L_TEST_HANG"):
        time.sleep(10 ** 6)


def rec_job(a):
    """m2l_core.rec_job unchanged + the worker's own peak memory."""
    _test_hooks(a)
    r = M.rec_job(a)
    r["vmhwm_mb"] = round(vmhwm_mb(), 1)
    return r


def score_job(a):
    r = M.score_job(a)
    r["vmhwm_mb"] = round(vmhwm_mb(), 1)
    return r


def watchdog_s(expected_s):
    lo, x = WATCHDOG_MIN_S, WATCHDOG_X
    if M.TEST_MODE and os.environ.get("M2L_TEST_WATCHDOG_S"):
        lo, x = float(os.environ["M2L_TEST_WATCHDOG_S"]), 0.0
    return max(lo, x * float(expected_s))


# ============================================================================ the scheduler
def simulate(est, dur, workers, budget, first_alone_uncal=True):
    """the admission rule of run() on estimated memory and projected durations -> (makespan s, max concurrency)."""
    order = sorted(range(len(est)), key=lambda i: -est[i])
    pending, running, t, conc = list(order), [], 0.0, 0     # running: (end, i)
    first = order[0] if order else None
    measured = False
    while pending or running:
        def held():
            return sum(est[i] * (UNCAL if (i == first and not measured and first_alone_uncal) else 1.0)
                       for _, i in running)
        started = True
        while started and pending and len(running) < workers:
            started = False
            for i in list(pending):
                need = est[i] * (UNCAL if (i == first and not measured) else 1.0)
                if not running or held() + min(need, budget) <= budget:
                    running.append((t + dur[i], i))
                    pending.remove(i)
                    started = True
                    break
        conc = max(conc, len(running))
        running.sort()
        end, i = running.pop(0)
        t = end
        if i == first:
            measured = True
    return t, conc


def _kill(ex):
    for p in list(getattr(ex, "_processes", {}).values()):
        try:
            p.kill()
        except Exception:                # noqa: BLE001
            pass
    ex.shutdown(wait=False, cancel_futures=True)


def run(fn, specs, est_mb, expected_s, workers, budget_mb, what):
    """run fn over specs under the memory budget; returns the results in completion order, each with est_mb (as
    admitted), t0 / t1 (s from the build start) and vmhwm_mb. STOP (SystemExit) on a dead worker, a job error, a job
    over the watchdog, or an estimate above the budget."""
    import multiprocessing as mp
    if not specs:
        return []
    est = [float(e) for e in est_mb]
    over = [(Path(str(specs[i][2])).name, round(est[i])) for i in range(len(specs)) if est[i] > budget_mb]
    if over:
        raise SystemExit(f"STOP {what}: memory estimate above the budget {budget_mb:.0f} MB: {over[:5]}")
    order = sorted(range(len(specs)), key=lambda i: -est[i])
    first, measured, scale = order[0], False, 1.0
    pending = list(order)
    running = {}                                              # future -> i
    starts, out, T = {}, [], time.time()
    ex = ProcessPoolExecutor(max_workers=max(1, int(workers)), mp_context=mp.get_context("spawn"),
                             initializer=R1._init_worker, initargs=(R1._env(),), max_tasks_per_child=1)
    name = lambda i: f"{specs[i][0]}:{Path(str(specs[i][2])).name}"
    try:
        while pending or running:
            def held():
                return sum(est[j] * scale * (UNCAL if (j == first and not measured) else 1.0) for j in running.values())
            started = True
            while started and pending and len(running) < workers:
                started = False
                for i in list(pending):
                    need = min(est[i] * scale * (UNCAL if (i == first and not measured) else 1.0), budget_mb)
                    if not running or held() + need <= budget_mb:
                        f = ex.submit(fn, specs[i])
                        running[f] = i
                        starts[i] = time.time()
                        pending.remove(i)
                        started = True
                        break
            done, _ = wait(list(running), timeout=POLL_S, return_when=FIRST_COMPLETED)
            for f in done:
                i = running.pop(f)
                try:
                    r = f.result()
                except BrokenProcessPool:
                    inflight = [name(i)] + [name(j) for j in running.values()]
                    raise SystemExit(f"STOP {what}: a worker died (killed from outside -- most likely out of memory); "
                                     f"recordings in flight: {inflight}; budget {budget_mb:.0f} MB")
                if r.get("error"):
                    raise SystemExit(f"{what} {r.get('case')} {r.get('file', '')}: {r['error']}")
                r.update(est_mb=round(est[i] * scale, 1), t0=round(starts[i] - T, 1), t1=round(time.time() - T, 1))
                out.append(r)
                if i == first and not measured:
                    measured = True
                    model = est[i] / SAFETY
                    hw = float(r.get("vmhwm_mb") or float("nan"))
                    scale = max(1.0, hw / model) if hw == hw else 1.0
                    log(f"{what}: first job {name(i)} measured {hw:.0f} MB against the model {model:.0f} MB "
                        f"(estimates x {scale:.3f} from now)")
                log(f"{what}: {len(out)}/{len(specs)} done -- {name(i)} {r.get('s', 0):.0f} s, "
                    f"peak {r.get('vmhwm_mb', float('nan')):.0f} MB (est {est[i] * scale:.0f})")
            now = time.time()
            for f, i in running.items():
                lim = watchdog_s(expected_s[i])
                if now - starts[i] > lim:
                    raise SystemExit(f"STOP {what}: G-watchdog FAIL -- {name(i)} running {now - starts[i]:.0f} s "
                                     f"(limit {lim:.0f} s)")
    except BaseException:
        _kill(ex)
        raise
    ex.shutdown(wait=True)
    log(f"{what}: {len(out)} jobs done")
    return out


def gate_sched(jobs, budget_mb, label):
    """G-sched: from the recorded start / end times, the admitted estimates in flight never exceeded the budget, and
    every job reported its own peak memory."""
    ev = sorted([(j["t0"], j["est_mb"]) for j in jobs] + [(j["t1"], -j["est_mb"]) for j in jobs],
                key=lambda e: (e[0], e[1]))
    cur, peak = 0.0, 0.0
    for _, d in ev:
        cur += d
        peak = max(peak, cur)
    hw = [j.get("vmhwm_mb") for j in jobs]
    missing = sum(1 for v in hw if not (isinstance(v, (int, float)) and v == v and v > 0))
    ratio = max((j["vmhwm_mb"] / j["est_mb"] for j in jobs if j.get("vmhwm_mb") and j["est_mb"] > 0), default=float("nan"))
    ok = peak <= budget_mb * (1 + 1e-9) + 1e-6 or len(jobs) <= 1
    R1.gate(dict(gate=f"G-sched[{label}]", status="PASS" if ok and not missing else "FAIL", jobs=len(jobs),
                 budget_mb=round(budget_mb), peak_estimate_in_flight_mb=round(peak), missing_peak=missing,
                 max_measured_over_estimate=round(ratio, 3),
                 max_measured_mb=round(max([v for v in hw if v], default=0.0)),
                 summary=f"{len(jobs)} jobs; estimates in flight <= {peak:.0f} of {budget_mb:.0f} MB; measured peak "
                         f"<= {max([v for v in hw if v], default=0.0):.0f} MB (max measured / estimate {ratio:.2f})"))
