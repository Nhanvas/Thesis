#!/usr/bin/env python
"""
app_val_op.py -- docs/CC_PROMPT_APP_VAL_OP.md: the SzScan application v3's own headless
computation (`web_demo/backend/pipeline_demo.process_subject_headless`), scored against the
VALIDATION annotations (chb10, chb11, chb22) to pick a reported operating point.

Thesis-side script: reads validation annotations, writes only under results/app_eval_v3/,
never writes inside web_demo/. web_demo/backend/pipeline_demo.py is imported READ-ONLY (same
convention as src/eval_application_events.py / src/continuous_eval.py importing other
single-source modules) -- Phase A/Phase B run exactly as the real application runs them; this
script only supplies the event-detection GRID and the scorer on top of the application's own
fused per-file scores and signal-loss flags.

TEST GUARD: this script scores the application's output against held-out TEST seizure
annotations NEVER -- enforce_test_guard() aborts immediately if any of chb03/chb06/chb13/
chb14/chb15/chb16/chb17/chb18 is requested, before anything else runs.

Step 3's grid (8 magnitude percentiles x 6 penalty multipliers x 2 merge gaps = 96 cells per
subject) reuses cpd_pipeline_v14.py's own private helpers (_smooth/_robust_variance/
_cp_magnitude, plus the module's WIN_SEC_DEFAULT) directly, the same "PELT once per pen_mult,
magnitude+merge applied post-hoc on the stored change points" pattern already used by
src/continuous_eval.py's grid_for_subject/verify_fast_grid -- cpd_pipeline_v14.py is never
edited, and the fast grid is verified against a direct cpd_pipeline_v14.detect_events() call
before use (verify_fast_grid below).

Events are mapped back to files the same way web_demo/backend/pipeline_demo.py's own
process_subject_events() does (assign each event to the file containing its ONSET window;
local_offset can exceed that file's own length), then boundary overflow is split into the
next file via src/eval_application_events.py's split_boundary_events() -- reused, not
retyped, the same function the application's own TEST evaluation uses. Per-file scoring
reuses szcore_eval.score_szcore (SZ_PARAM) -- "the same SzCORE scorer used for the
application's test evaluation" (docs/CC_PROMPT_APP_VAL_OP.md Step 4) -- and
eval_application_events._score_from_counts for the pooled sensitivity/precision/F1/FA-per-day
formulas, with one deliberate twist: FA/day's denominator here is recorded time MINUS seizure
time MINUS signal-loss time (this prompt's Step 4), gotten by passing
`duration_s - signal_loss_s` as _score_from_counts's own `duration_s` argument -- that
function already computes `denom_days = (duration_s - seizure_s) / 86400`, so this reuses the
formula unmodified rather than reimplementing it.

Usage
-----
  python src/app_val_op.py                 # gate, all 3 validation subjects, full grid
  python src/app_val_op.py --subjects chb10   # one validation subject (dev only)

Re-running reuses each subject's cached fused scores/flags under
results/app_eval_v3/cache/{subj}_scores.npz instead of re-running Phase A/B.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import ruptures as rpt

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src", ROOT / "src" / "dataprep", ROOT / "src" / "retrain",
           ROOT / "web_demo" / "backend"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import preprocessing as P                                     # noqa: E402 -- read-only
import cpd_pipeline_v14 as V14                                 # noqa: E402 -- read-only, locked
from szcore_eval import score_szcore                           # noqa: E402 -- reused, not retyped
from evaluation_protocol import parse_summary_edf_list          # noqa: E402 -- reused, not retyped
from eval_application_events import _score_from_counts, split_boundary_events  # noqa: E402
import pipeline_demo                                           # noqa: E402 -- web_demo/backend, read-only

VAL_SUBJS = ["chb10", "chb11", "chb22"]
TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]

# Same grid as the thesis (src/continuous_eval.py MAG_PCTS/PEN_MULTS, == src/retrain/final_eval.py).
MAG_PCTS = [40.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0]
PEN_MULTS = [0.3, 0.5, 1.0, 2.0, 5.0, 10.0]
MERGE_GAPS = [90, 300]
WIN_SEC = V14.WIN_SEC_DEFAULT  # 4 -- same constant detect_events itself defaults to

DATASET_DIR = Path("F:/Study/Thesis/Dataset/CHB-MIT")
SUMMARY_DIR = DATASET_DIR / "CHB info" / "summary"

OUT_DIR = ROOT / "results" / "app_eval_v3"
CACHE_DIR = OUT_DIR / "cache"          # on F: (repo root's own drive) -- never committed

PIPELINE_DEMO_PATH = ROOT / "web_demo" / "backend" / "pipeline_demo.py"
REQUIRED_PIPELINE_DEMO_COMMIT = "3336bd7"  # App v3 code: signal-loss rule, merge constant, headless entry

# "Phase A at most 2 workers" (docs/CC_PROMPT_APP_VAL_OP.md) is an upper bound, not a target.
# process_subject_headless's own Phase A holds every file's filtered+raw+bandpass float32
# arrays in RAM simultaneously for the WHOLE subject before Phase B can start (inherent to the
# two-phase design, not a bug here -- pipeline_demo.py is read-only) -- for chb10 (50 h across
# 25 files) that is several GiB on its own. A first attempt at 2 workers was killed by the
# harness for system memory pressure on this machine (~6.7 GiB free of ~16 GiB, chrome/IDE/
# antivirus already resident); 1 worker trades some wall-clock time for a materially smaller
# peak (one file's extra in-flight scratch buffers instead of two).
HEADLESS_MAX_WORKERS = 1


class ValOpError(Exception):
    """Fail-fast: the message is meant to be read directly."""


def log(tag, msg):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    line = f"[{tag}] {time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(OUT_DIR / "run.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def enforce_test_guard(subjects):
    bad = [s for s in subjects if s in TEST_SUBJS]
    if bad:
        raise ValOpError(
            f"TEST guard: subject(s) {bad} are held-out TEST subjects -- this script scores "
            f"the application's output against validation annotations ONLY. Validation "
            f"subjects: {VAL_SUBJS}."
        )
    unknown = sorted(set(subjects) - set(VAL_SUBJS))
    if unknown:
        raise ValOpError(f"Unknown subject(s) {unknown} -- validation subjects are {VAL_SUBJS}.")


# ---------------------------------------------------------------------------------------
# Step 1 -- gate
# ---------------------------------------------------------------------------------------
def _run(cmd):
    return subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)


def run_gate():
    log("GATE", "running python src/verify_provenance.py ...")
    proc = _run([sys.executable, str(ROOT / "src" / "verify_provenance.py")])
    print(proc.stdout)
    if proc.returncode != 0 or "PASS" not in proc.stdout:
        raise ValOpError(
            f"verify_provenance.py did not PASS (exit {proc.returncode}) -- stopping:\n"
            f"{proc.stdout}\n{proc.stderr}"
        )
    log("GATE", "verify_provenance.py PASS")

    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    log("GATE", f"git rev-parse HEAD = {head}")

    pd_commit = _run(["git", "log", "-1", "--format=%H", "--",
                      "web_demo/backend/pipeline_demo.py"]).stdout.strip()
    if not pd_commit.startswith(REQUIRED_PIPELINE_DEMO_COMMIT):
        raise ValOpError(
            f"web_demo/backend/pipeline_demo.py's last commit is {pd_commit[:7] or '(none)'}, "
            f"expected {REQUIRED_PIPELINE_DEMO_COMMIT} (App v3 code) -- stopping, do not proceed."
        )
    dirty = _run(["git", "status", "--porcelain", "--",
                 "web_demo/backend/pipeline_demo.py"]).stdout.strip()
    if dirty:
        raise ValOpError(
            f"web_demo/backend/pipeline_demo.py has uncommitted changes -- stopping:\n{dirty}"
        )
    log("GATE", f"web_demo/backend/pipeline_demo.py confirmed at commit {pd_commit[:7]} "
               f"(App v3 code), working tree clean")
    return dict(head=head, pipeline_demo_commit=pd_commit)


# ---------------------------------------------------------------------------------------
# Step 2 -- application's own headless Phase A + Phase B, per validation subject
# ---------------------------------------------------------------------------------------
def discover_edfs(subj):
    edfs = sorted((DATASET_DIR / subj).glob("*.edf"))
    if not edfs:
        raise ValOpError(f"No EDFs found for {subj} under {DATASET_DIR / subj}")
    return [str(p) for p in edfs]


def _sanitize(fname):
    return fname.replace(".", "_")


def _scores_cache_path(subj):
    return CACHE_DIR / f"{subj}_scores.npz"


def get_subject_scores(subj):
    """Phase A + Phase B through the application's own process_subject_headless (App v3
    item 3; import read-only, never edited). Returns (scores_by_filename, flag_by_filename),
    cached under results/app_eval_v3/cache/{subj}_scores.npz so a re-run skips the ~15-25
    min/subject EEG processing."""
    cache_path = _scores_cache_path(subj)
    if cache_path.exists():
        log("B", f"{subj}: reusing cached fused scores+flags ({cache_path.name})")
        z = np.load(cache_path, allow_pickle=False)
        filenames = [str(f) for f in z["filenames"]]
        scores = {f: z[f"score__{_sanitize(f)}"] for f in filenames}
        flags = {f: z[f"flag__{_sanitize(f)}"].astype(bool) for f in filenames}
        return scores, flags

    edf_paths = discover_edfs(subj)
    log("B", f"{subj}: {len(edf_paths)} EDF(s), calling pipeline_demo.process_subject_headless "
             f"(max_workers={HEADLESS_MAX_WORKERS}, cache under {CACHE_DIR / subj})")
    t0 = time.time()
    scores, flags = pipeline_demo.process_subject_headless(
        edf_paths, cache_dir=CACHE_DIR / subj, max_workers=HEADLESS_MAX_WORKERS,
    )
    elapsed = time.time() - t0
    log("B", f"{subj}: process_subject_headless done in {elapsed / 60:.1f} min "
             f"({len(scores)} file(s))")

    filenames = sorted(scores.keys())
    save_kwargs = {"filenames": np.array(filenames)}
    for f in filenames:
        save_kwargs[f"score__{_sanitize(f)}"] = scores[f]
        save_kwargs[f"flag__{_sanitize(f)}"] = flags[f]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    np.savez(cache_path, **save_kwargs)
    log("B", f"{subj}: fused scores+flags persisted to {cache_path.name}")
    return scores, flags


def load_annotation(subj):
    edfs = parse_summary_edf_list(SUMMARY_DIR / f"{subj}-summary.md")
    return {e["fname"]: {"duration_s": e["duration_s"], "seizures": e["seizures"]} for e in edfs}


# ---------------------------------------------------------------------------------------
# Step 3 -- event grid: PELT once per penalty, magnitude + merge post-hoc
# ---------------------------------------------------------------------------------------
def _mag_threshold(mags, inter_mask, pct):
    if inter_mask is not None and np.any(inter_mask):
        bg = [m for c, m in mags.items() if inter_mask[c]]
    else:
        bg = list(mags.values())
    return float(np.percentile(bg, pct)) if bg else 0.0


def cps_to_merged_events(cps, win_sec, merge_s):
    """Byte-identical to cpd_pipeline_v14.detect_events's own merge loop (cpd_pipeline_v14.py
    lines ~157-164) -- reproduced here (not imported) only so merge_s can be applied post-hoc
    to change points already filtered for a given (pen_mult, mag_pct), without a fresh PELT
    fit; verify_fast_grid below checks this reproduces detect_events exactly."""
    times = sorted(c * win_sec for c in cps)
    events = []
    for t in times:
        if events and t - events[-1][1] <= merge_s:
            events[-1] = (events[-1][0], t + win_sec)
        else:
            events.append((t, t + win_sec))
    return events


def grid_for_subject(score, inter_mask, mag_pcts, pen_mults, merge_gaps):
    """PELT once per pen_mult (docs/CC_PROMPT_APP_VAL_OP.md Step 3); magnitude percentile and
    merge gap applied post-hoc on the stored change points. Reuses cpd_pipeline_v14's own
    private helpers (_smooth/_robust_variance/_cp_magnitude/PELT_MIN_SIZE/PELT_JUMP) so the
    magnitude-threshold and PELT-penalty math can never silently diverge from
    detect_changepoints's own (same pattern as src/continuous_eval.py's grid_for_subject)."""
    smoothed = V14._smooth(np.asarray(score, dtype=float))
    n = len(smoothed)
    out = []
    if n < 10:
        for pm in pen_mults:
            for mag in mag_pcts:
                for ms in merge_gaps:
                    out.append(dict(mag_pct=mag, pen_mult=pm, merge_s=ms, hyp_events=[]))
        return out
    s2 = V14._robust_variance(smoothed, inter_mask)
    algo = rpt.Pelt(model="l2", min_size=V14.PELT_MIN_SIZE, jump=V14.PELT_JUMP).fit(
        smoothed.reshape(-1, 1))
    for pm in pen_mults:
        beta = pm * s2 * np.log(n)
        cps_pen = [c for c in algo.predict(pen=beta) if 0 < c < n]
        mags = {c: V14._cp_magnitude(smoothed, c, 15) for c in cps_pen}
        for mag in mag_pcts:
            thr = _mag_threshold(mags, inter_mask, mag)
            cps = [c for c in cps_pen if mags[c] >= thr]
            for ms in merge_gaps:
                out.append(dict(mag_pct=mag, pen_mult=pm, merge_s=ms,
                                hyp_events=cps_to_merged_events(cps, WIN_SEC, ms)))
    return out


def verify_fast_grid(score, inter_mask, subj):
    """Step 3: "verified on one subject against a direct detect_events call (identical
    events) before use." Checks 4 (pen_mult, mag_pct) cells x 2 merge_s."""
    smoothed = V14._smooth(np.asarray(score, dtype=float))
    n = len(smoothed)
    s2 = V14._robust_variance(smoothed, inter_mask)
    algo = rpt.Pelt(model="l2", min_size=V14.PELT_MIN_SIZE, jump=V14.PELT_JUMP).fit(
        smoothed.reshape(-1, 1))
    for pen_mult in (0.5, 2.0):
        beta = pen_mult * s2 * np.log(n)
        cps_pen = [c for c in algo.predict(pen=beta) if 0 < c < n]
        mags = {c: V14._cp_magnitude(smoothed, c, 15) for c in cps_pen}
        for mag in (50.0, 65.0):
            thr = _mag_threshold(mags, inter_mask, mag)
            cps_fast = [c for c in cps_pen if mags[c] >= thr]
            for merge_s in (90, 300):
                ev_fast = cps_to_merged_events(cps_fast, WIN_SEC, merge_s)
                ev_direct = V14.detect_events(score, pen_mult, min_mag_pct=mag, local_win=15,
                                              win_sec=WIN_SEC, inter_mask=inter_mask,
                                              merge_s=merge_s)
                if ev_fast != ev_direct:
                    raise ValOpError(
                        f"fast-grid verification FAILED on {subj}: pen={pen_mult} mag={mag} "
                        f"merge={merge_s}: fast={len(ev_fast)} direct={len(ev_direct)} events "
                        f"-- stopping before using the fast grid."
                    )
    log("C", f"verify_fast_grid PASS on {subj} (4 cells x 2 merge_s, byte-identical to a "
             f"direct cpd_pipeline_v14.detect_events call)")


def assign_events_to_files(hyp_events_global, filenames_sorted, offsets_win, n_windows_by_file):
    """Mirrors web_demo/backend/pipeline_demo.py process_subject_events's own assignment loop
    exactly: each event is assigned to the file containing its ONSET window; local_offset =
    local_onset + event duration, which can exceed that file's own length -- the overflow is
    split into the next file by split_boundary_events (reused below from
    src/eval_application_events.py, the application's own TEST-evaluation scorer)."""
    file_events = {f: [] for f in filenames_sorted}
    for onset_s, offset_s in hyp_events_global:
        onset_win = onset_s / WIN_SEC
        for f in filenames_sorted:
            lo = offsets_win[f]
            hi = lo + n_windows_by_file[f]
            if lo <= onset_win < hi:
                local_onset = (onset_win - lo) * WIN_SEC
                local_offset = local_onset + (offset_s - onset_s)
                file_events[f].append((local_onset, local_offset))
                break
    return file_events


def events_to_df(subj, file_events, filenames_sorted):
    rows = []
    eid = 0
    for f in filenames_sorted:
        for onset, offset in file_events[f]:
            eid += 1
            rows.append(dict(subject=subj, file_name=f, event_id=eid, onset_s=onset,
                             offset_s=offset, source="AI", review_status=""))
    cols = ["subject", "file_name", "event_id", "onset_s", "offset_s", "source", "review_status"]
    return pd.DataFrame(rows, columns=cols)


def df_to_file_events(events_df, filenames_sorted):
    out = {f: [] for f in filenames_sorted}
    if len(events_df) == 0:
        return out
    for row in events_df.itertuples():
        out[row.file_name].append((float(row.onset_s), float(row.offset_s)))
    return out


# ---------------------------------------------------------------------------------------
# Step 4 -- scoring (same SzCORE scorer as the application's test evaluation)
# ---------------------------------------------------------------------------------------
def precompute_file_stats(filenames_sorted, scores_by_filename, flag_by_filename, annotation):
    """Per file: reference seizures (file-relative seconds, from the annotation), and the
    non-ictal signal-loss seconds excluded from the FA/day denominator (Step 4) -- mirrors
    src/continuous_eval.py's Amendment A2 rule (noninter_h/excluded_h): a signal-loss window
    that overlaps an annotated seizure is NOT double-subtracted from the denominator."""
    stats = {}
    for f in filenames_sorted:
        n_windows_f = len(scores_by_filename[f])
        dur_s = float(annotation[f]["duration_s"])
        seizures = annotation[f]["seizures"]
        seizure_s = float(sum(off - on for on, off in seizures))
        n_sec = max(int(np.ceil(dur_s)), n_windows_f * WIN_SEC)
        labels_sec = P.build_labels(n_sec, seizures)
        is_ictal_win = np.zeros(n_windows_f, dtype=bool)
        for i in range(n_windows_f):
            s0, s1 = i * WIN_SEC, (i + 1) * WIN_SEC
            is_ictal_win[i] = bool(labels_sec[s0:s1].any())
        flags_f = flag_by_filename[f]
        signal_loss_s = float(int(np.sum(flags_f & (~is_ictal_win))) * WIN_SEC)
        stats[f] = dict(n_windows=n_windows_f, duration_s=dur_s, seizure_s=seizure_s,
                        signal_loss_s=signal_loss_s, ref_iv=seizures)
    return stats


def build_files_df(subj, filenames_sorted, file_stats):
    rows = [dict(subject=subj, file_name=f, duration_s=file_stats[f]["duration_s"],
                 n_windows=file_stats[f]["n_windows"], status="success")
            for f in filenames_sorted]
    return pd.DataFrame(rows)


def score_cell_for_subject(filenames_sorted, file_stats, file_events_split):
    tp = fp = n_ref = 0
    dur_sum = seizure_sum = sl_sum = 0.0
    for f in filenames_sorted:
        fs = file_stats[f]
        hyp_iv = file_events_split.get(f, [])
        # n_inter_h=1.0: dummy -- score_szcore's own fp_per_day is unused here, only
        # tp/fp/n_ref are accumulated; the pooled FA/day is recomputed below with this
        # script's own (recorded - seizure - signal-loss) denominator.
        sc = score_szcore(fs["ref_iv"], hyp_iv, total_dur_s=fs["duration_s"], n_inter_h=1.0)
        tp += sc["tp"]; fp += sc["fp"]; n_ref += sc["n_ref"]
        dur_sum += fs["duration_s"]; seizure_sum += fs["seizure_s"]; sl_sum += fs["signal_loss_s"]
    return dict(tp=tp, fp=fp, n_ref=n_ref, duration_s=dur_sum, seizure_s=seizure_sum,
               signal_loss_s=sl_sum)


def score_grid_cell(subj, filenames_sorted, offsets_win, file_stats, files_df, hyp_events_global):
    n_windows_by_file = {f: file_stats[f]["n_windows"] for f in filenames_sorted}
    file_events_raw = assign_events_to_files(hyp_events_global, filenames_sorted, offsets_win,
                                             n_windows_by_file)
    events_df = events_to_df(subj, file_events_raw, filenames_sorted)
    if len(events_df):
        events_df, _ = split_boundary_events(events_df, files_df)
    file_events_split = df_to_file_events(events_df, filenames_sorted)
    return score_cell_for_subject(filenames_sorted, file_stats, file_events_split)


# ---------------------------------------------------------------------------------------
# Orchestration: Steps 2-4 -> val_grid.csv
# ---------------------------------------------------------------------------------------
def run_val_grid(subjects):
    subj_ctx = {}
    for subj in subjects:
        scores, flags = get_subject_scores(subj)
        annotation = load_annotation(subj)
        missing = [f for f in scores if f not in annotation]
        if missing:
            raise ValOpError(f"{subj}: file(s) absent from the annotation: {missing}")

        filenames_sorted = sorted(scores.keys())
        offsets_win, cur = {}, 0
        for f in filenames_sorted:
            offsets_win[f] = cur
            cur += len(scores[f])
        global_score = np.concatenate([scores[f] for f in filenames_sorted])
        global_flags = np.concatenate([flags[f] for f in filenames_sorted])
        inter_mask = ~global_flags

        file_stats = precompute_file_stats(filenames_sorted, scores, flags, annotation)
        files_df = build_files_df(subj, filenames_sorted, file_stats)
        verify_fast_grid(global_score, inter_mask, subj)

        subj_ctx[subj] = dict(filenames_sorted=filenames_sorted, offsets_win=offsets_win,
                              global_score=global_score, inter_mask=inter_mask,
                              file_stats=file_stats, files_df=files_df)
        log("C", f"{subj}: {len(filenames_sorted)} files, {len(global_score)} windows "
                 f"({len(global_score) * WIN_SEC / 3600:.2f} h), "
                 f"{int(global_flags.sum())} signal-loss window(s)")

    log("C", "building per-subject grids (PELT once per penalty, magnitude+merge post-hoc)")
    per_subj_grid = {}
    for subj in subjects:
        ctx = subj_ctx[subj]
        t0 = time.time()
        per_subj_grid[subj] = grid_for_subject(ctx["global_score"], ctx["inter_mask"],
                                               MAG_PCTS, PEN_MULTS, MERGE_GAPS)
        log("C", f"{subj}: {len(per_subj_grid[subj])}-cell grid built in {time.time() - t0:.1f}s")

    n_cells = len(per_subj_grid[subjects[0]])
    rows = []
    t0 = time.time()
    for i in range(n_cells):
        ref_cell = per_subj_grid[subjects[0]][i]
        mag, pen, ms = ref_cell["mag_pct"], ref_cell["pen_mult"], ref_cell["merge_s"]
        pooled_acc = dict(tp=0, fp=0, n_ref=0, duration_s=0.0, seizure_s=0.0, signal_loss_s=0.0)
        for subj in subjects:
            ctx = subj_ctx[subj]
            cell = per_subj_grid[subj][i]
            assert cell["mag_pct"] == mag and cell["pen_mult"] == pen and cell["merge_s"] == ms
            sc = score_grid_cell(subj, ctx["filenames_sorted"], ctx["offsets_win"],
                                 ctx["file_stats"], ctx["files_df"], cell["hyp_events"])
            row = dict(mag_pct=mag, pen_mult=pen, merge_s=ms, subject=subj,
                      hours=round(sc["duration_s"] / 3600.0, 4),
                      signal_loss_hours=round(sc["signal_loss_s"] / 3600.0, 4),
                      **_score_from_counts(sc["tp"], sc["fp"], sc["n_ref"],
                                           sc["duration_s"] - sc["signal_loss_s"], sc["seizure_s"]))
            rows.append(row)
            for k in ("tp", "fp", "n_ref", "duration_s", "seizure_s", "signal_loss_s"):
                pooled_acc[k] += sc[k]
        pooled_row = dict(mag_pct=mag, pen_mult=pen, merge_s=ms, subject="POOLED",
                         hours=round(pooled_acc["duration_s"] / 3600.0, 4),
                         signal_loss_hours=round(pooled_acc["signal_loss_s"] / 3600.0, 4),
                         **_score_from_counts(pooled_acc["tp"], pooled_acc["fp"],
                                              pooled_acc["n_ref"],
                                              pooled_acc["duration_s"] - pooled_acc["signal_loss_s"],
                                              pooled_acc["seizure_s"]))
        rows.append(pooled_row)
    log("C", f"scored {n_cells} grid cells x {len(subjects)} subject(s) in "
             f"{time.time() - t0:.1f}s")
    return pd.DataFrame(rows), subj_ctx


# ---------------------------------------------------------------------------------------
# Step 5 -- selection
# ---------------------------------------------------------------------------------------
def select_operating_points(grid_df):
    pooled = grid_df[grid_df.subject == "POOLED"].copy()
    pooled["fa_day_num"] = pd.to_numeric(pooled["false_alarms_per_day"], errors="coerce")
    pooled["sensitivity"] = pd.to_numeric(pooled["sensitivity"], errors="coerce")
    pooled["precision"] = pd.to_numeric(pooled["precision"], errors="coerce")

    # Amendment A8 rule: maximize pooled validation sensitivity s.t. pooled FA/day <= 25;
    # ties by lower FA/day, then lower penalty.
    ok = pooled[pooled.fa_day_num <= 25.0]
    if len(ok) == 0:
        raise ValOpError("Amendment A8 rule: no grid cell has pooled validation FA/day <= 25.")
    ok = ok.sort_values(by=["sensitivity", "fa_day_num", "pen_mult"],
                        ascending=[False, True, True])
    a8_row = ok.iloc[0].to_dict()

    # Step A rule (information): sensitivity and precision closest to equal.
    pooled["abs_gap"] = (pooled["sensitivity"] - pooled["precision"]).abs()
    stepA_row = pooled.loc[pooled["abs_gap"].idxmin()].to_dict()

    return a8_row, stepA_row


# ---------------------------------------------------------------------------------------
# Step 6 -- SELECTED.md
# ---------------------------------------------------------------------------------------
def _subject_rows_table(grid_df, row):
    sub = grid_df[(grid_df.mag_pct == row["mag_pct"]) & (grid_df.pen_mult == row["pen_mult"]) &
                 (grid_df.merge_s == row["merge_s"])]
    cols = ["subject", "seizures", "detected", "false_alarms", "sensitivity", "precision",
           "f1", "false_alarms_per_day", "hours", "signal_loss_hours"]
    return sub[cols].to_string(index=False)


def build_selected_md(grid_df, a8_row, stepA_row, gate_info, elapsed_s):
    lines = ["# Application v3 -- validation operating point -- SELECTED", ""]
    lines.append(
        "docs/CC_PROMPT_APP_VAL_OP.md. The application v3's own headless computation "
        "(web_demo/backend/pipeline_demo.process_subject_headless), scored against the "
        "validation annotations (chb10, chb11, chb22) -- never read by the application "
        "itself. Not applied to any application constant here; the selected values go to "
        "Project 2 in a separate instruction."
    )
    lines.append("")
    lines.append(f"- repo HEAD: `{gate_info['head']}`")
    lines.append(f"- `web_demo/backend/pipeline_demo.py` commit: "
                 f"`{gate_info['pipeline_demo_commit']}` (App v3 code)")
    lines.append(f"- wall-clock time: {elapsed_s / 60:.1f} min")
    lines.append("")

    for title, rule_desc, row in (
        ("Amendment A8 rule (reported result)",
         "Maximize pooled validation sensitivity subject to pooled validation FA/day <= 25; "
         "ties by lower FA/day, then lower penalty.", a8_row),
        ("Step A rule (information)",
         "Sensitivity and precision closest to equal.", stepA_row),
    ):
        lines.append(f"## {title}")
        lines.append("")
        lines.append(rule_desc)
        lines.append("")
        lines.append(f"- mag_pct = {row['mag_pct']:g}, pen_mult = {row['pen_mult']:g}, "
                     f"merge_s = {row['merge_s']:g}")
        lines.append(f"- pooled: sensitivity={row['sensitivity']:.4f} "
                     f"precision={row['precision']:.4f} f1={row['f1']} "
                     f"FA/day={row['false_alarms_per_day']} seizures={row['seizures']} "
                     f"detected={row['detected']} false_alarms={row['false_alarms']}")
        lines.append("")
        lines.append("Per subject (and pooled):")
        lines.append("")
        lines.append("```")
        lines.append(_subject_rows_table(grid_df, row))
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def write_readme():
    (OUT_DIR / "README.md").write_text(
        "# results/app_eval_v3/ -- producing script\n\n"
        "`val_grid.csv`, `SELECTED.md`, `run.log` <- `src/app_val_op.py` "
        "(docs/CC_PROMPT_APP_VAL_OP.md). `cache/` holds the application's own headless Phase "
        "A/B intermediates and per-subject fused scores -- never committed, safe to delete "
        "and let the script rebuild.\n",
        encoding="utf-8")


# ---------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--subjects", nargs="+", default=VAL_SUBJS,
                    help="validation subjects to run (default: all three)")
    args = ap.parse_args()

    enforce_test_guard(args.subjects)

    t_start = time.time()
    gate_info = run_gate()

    grid_df, _ = run_val_grid(args.subjects)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    grid_df.to_csv(OUT_DIR / "val_grid.csv", index=False)
    log("DONE", f"val_grid.csv written ({len(grid_df)} rows)")

    a8_row, stepA_row = select_operating_points(grid_df)
    elapsed_s = time.time() - t_start
    summary = build_selected_md(grid_df, a8_row, stepA_row, gate_info, elapsed_s)
    (OUT_DIR / "SELECTED.md").write_text(summary, encoding="utf-8")
    write_readme()
    log("DONE", f"SELECTED.md written. Amendment A8: mag={a8_row['mag_pct']:g} "
               f"pen={a8_row['pen_mult']:g} merge={a8_row['merge_s']:g} "
               f"sens={a8_row['sensitivity']:.3f} FA/day={a8_row['false_alarms_per_day']}")
    log("DONE", f"total wall-clock: {elapsed_s / 60:.1f} min")


if __name__ == "__main__":
    main()
