"""
pipeline_demo.py — SzScan web demo's label-free, continuous re-implementation of the
locked thesis pipeline (`rlg`: zrecon + zlatent + zgamma, equal 1/3 weights).

Scope of this file as of Step 3 (see DEMO_BUILD_HANDOFF.md §6 row 3 / CC_STEP3_PROMPT.md §1):
the two-phase per-subject architecture required by SZSCAN_SPEC_v5.md §1.6(a) plus stage 2
(PELT + label-free operating point + event-to-file assignment, SPEC §1.5/§5.5).

Phase split (resolves the two `# TODO(step3)` markers that used to sit in process_file()):

  Phase A — process_file_phase_a(edf_path): runs the moment ONE file finishes uploading.
    Open the 18 common channels, bandpass+notch filter the whole recording once, cut into
    4 s windows. Cheap (no adjacency/GAE/gamma), needs nothing from sibling files. This is
    what flips a file's status icon from the spinning circle to the uploaded state in the
    Create New panel (UI/A1c). Returns filtered-but-not-z-scored windows.

  Phase B — process_subject_phase_b(phase_a_by_filename): runs once, when the LAST file of
    the subject currently in the Create New panel finishes Phase A. Concatenates every
    file's raw windows fit so far, computes the z-score mean/std AND the LedoitWolf fit for
    zlatent on that combined set (SPEC §1.6a — both must be subject-wide, not per-file), then
    runs the rest of the pipeline (CAR -> adjacency -> band powers -> GAE -> zrecon/zlatent/
    zgamma) per file using those subject-wide statistics. Per SPEC §1.6a's own table, robust-z
    is *not* a divergence — the thesis already fits it on "the whole window set" available at
    that stage — so here that means fitting robust-z's median/MAD per branch on the
    concatenated subject-wide raw score arrays too, then applying that fit per file. Returns
    one continuous ensemble-score array per file (each exactly as long as that file's own
    window count) — what stage 2 below concatenates.

  Stage 2 — process_subject_events(): runs on "Process" click. Concatenates the per-file
    Phase B scores in FILENAME order (SPEC §5.5 is explicit that this is filename order, not
    upload order), calibrates a label-free per-subject operating point (SPEC §8 O1 — see
    calibrate_operating_point()), runs cpd_pipeline_v14.detect_events() once on the whole
    concatenated timeline, then assigns each returned event back to its file by the
    cumulative-offset construction in SPEC §1.5 (no lookup module — offsets fall out of the
    per-file score lengths by construction).

Read SZSCAN_SPEC_v5.md §1 before touching this file — it is the measured justification for
every divergence from the thesis pipeline.

Never edit/copy the modules this file imports from (`src/dataprep/*`, `src/retrain/gae_joint.py`,
`src/ensemble_recipe.py`, `src/cpd_pipeline_v14.py`, `src/retrain/fp_budget_operating_point.py`) —
they are single-source, shared with the thesis. Read-only.
"""
import argparse
import hashlib
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import torch
from scipy.signal import sosfiltfilt, filtfilt
from sklearn.covariance import LedoitWolf

# Phase B runs on a background thread (upload_manager.py), never the main thread — torch's
# default multi-threaded OpenMP/MKL backend has a known hang when its thread pool is first
# touched from a non-main thread on Windows. Single-threaded is also plenty fast here: the
# model is tiny (see gae_joint.py) and per-window CPU cost is dominated by adjacency/band-
# power (numpy/scipy), not the GAE forward pass.
torch.set_num_threads(1)

# ── Wire up imports to the read-only thesis modules (same sys.path convention as
#    src/attribution_pipeline.py: add the directories, then import bare module names) ──
REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (REPO_ROOT / "src", REPO_ROOT / "src" / "dataprep", REPO_ROOT / "src" / "retrain"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import preprocessing          # src/dataprep/preprocessing.py
import graph_construction     # src/dataprep/graph_construction.py
import feature_extraction     # src/dataprep/feature_extraction.py
import compute_gamma_aec      # src/dataprep/compute_gamma_aec.py
import gae_joint               # src/retrain/gae_joint.py
import ensemble_recipe         # src/ensemble_recipe.py
import cpd_pipeline_v14        # src/cpd_pipeline_v14.py
import fp_budget_operating_point as fp_budget  # src/retrain/fp_budget_operating_point.py

N_CH = len(preprocessing.COMMON_CHANNELS)  # 18

# ── Checkpoint identity — never trust the filename alone (CLAUDE.md "Model identity") ──
CHECKPOINT_PATH = REPO_ROOT / "data" / "models_retrain" / "gae_joint_seed42.pt"
CHECKPOINT_SHA256 = "dea06cb533df1c7d0520ae21c4cbb1b8a938297f937366bc9915b040726ea108"

# SPEC §8 O1: read the demo's target budget from the locked source file at runtime, never
# hardcode the number. "balanced" is the demo's fixed target (no UI control to pick a
# profile — CLAUDE.md "no evaluation metric in the UI").
FP_BUDGET_PROFILE = "balanced"
TARGET_FP_PER_DAY = fp_budget.BUDGETS[FP_BUDGET_PROFILE]

# SPEC §8 O1's calibration grid: reuse the locked pen_mult grid from the same eval module
# fp_budget_operating_point.py itself depends on (final_eval.DEFAULT_PENS), rather than
# inventing a new grid. Imported lazily below via fp_budget's own import of final_eval.
import final_eval as _final_eval  # noqa: E402  (src/retrain/final_eval.py, same sys.path)
PEN_MULT_GRID = list(_final_eval.DEFAULT_PENS)

# cpd_pipeline_v14.detect_events's own default; SPEC §8 O2 says use PELT params as locked
# in that file — this one is a keyword default there, not something demo code should re-pick.
MIN_MAG_PCT = 60


def _verify_checkpoint(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {path}")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != CHECKPOINT_SHA256:
        raise RuntimeError(
            f"Checkpoint hash mismatch for {path}: expected {CHECKPOINT_SHA256}, got {actual}. "
            "Refusing to load an unverified checkpoint — see CLAUDE.md 'Model identity'."
        )


def _median_mad(x: np.ndarray) -> tuple[float, float]:
    med = float(np.median(x))
    mad = float(np.median(np.abs(x - med))) + 1e-9
    return med, mad


class UnsupportedEdfError(ValueError):
    """Raised when an uploaded file isn't a readable EDF or is missing one of the 18
    common channels — the backend's cue to show SPEC §2's exact rejection toast."""


class CancelledError(Exception):
    """Raised by process_file_phase_a when the caller's cancel_check fires mid-run."""


@dataclass
class PhaseAResult:
    filename: str
    filtered: np.ndarray       # [n_windows, 18, WIN_SAMPLES] float32, filtered, NOT z-scored
    n_windows: int
    start_time: datetime       # from the EDF header (raw.info['meas_date']) — never user-entered
    file_duration_seconds: float  # true recording length (raw.n_times / sfreq)
    filtered_path: Optional[Path] = None  # set when cache_dir given — see process_file_phase_a
    raw_path: Optional[Path] = None  # set when cache_dir given — continuous unfiltered windows,
    # added in Step 4 (CC_STEP4_PROMPT.md) for Panel EEG's raw/filtered dual-view (SPEC §6.4:
    # "raw is never fully hidden"). Same [n_windows, 18, WIN_SAMPLES] float32 layout as
    # `filtered`/`filtered_path`, just skipping the bandpass+notch step.


def process_file_phase_a(
    edf_path: str, cancel_check=None, cache_dir: Optional[Path] = None
) -> PhaseAResult:
    """Phase A (SPEC §1.6a / CC_STEP3_PROMPT.md §1): open, filter, window ONE file. No
    z-scoring, no adjacency, no model — those need subject-wide stats (Phase B).

    Parameters
    ----------
    cancel_check : callable, optional
        Called at each cheap checkpoint (open / after filtering / after windowing); if it
        returns True, raises CancelledError so the caller can drop this file's upload
        (SPEC §5.5's per-file "stop" button on the spinning-circle icon).
    cache_dir : Path, optional
        When given, the filtered windows are ALSO written to `{cache_dir}/{stem}.filtered.npy`
        and the path recorded on the result. upload_manager.py uses this so Phase B can run in
        a separate OS process (see process_subject_phase_b_from_paths) and hand it a handful of
        file paths instead of hundreds of MB of arrays over a multiprocessing pipe — sending
        that much data directly through ProcessPoolExecutor's call queue reliably deadlocks on
        Windows (observed here: a worker process would sit at 0% CPU indefinitely after import).
    """
    def _check():
        if cancel_check is not None and cancel_check():
            raise CancelledError(edf_path)

    _check()
    try:
        raw = preprocessing.open_edf(edf_path)
    except Exception as exc:  # mne raises a variety of exceptions for non-EDF/corrupt input
        raise UnsupportedEdfError(f"{edf_path}: could not be read as EDF ({exc})") from exc
    if raw is None:
        raise UnsupportedEdfError(
            f"{edf_path}: missing one or more of the 18 common channels "
            f"({preprocessing.COMMON_CHANNELS})."
        )

    n_windows = int(raw.n_times) // preprocessing.WIN_SAMPLES
    if n_windows == 0:
        raise UnsupportedEdfError(f"{edf_path}: shorter than one 4 s window — nothing to score.")

    start_time = raw.info["meas_date"]
    if start_time is None:
        raise UnsupportedEdfError(f"{edf_path}: EDF header has no start time (meas_date).")
    file_duration_seconds = float(raw.n_times) / float(raw.info["sfreq"])

    _check()
    # Filter the WHOLE continuous recording once (see Step 1's rationale, unchanged): a
    # single continuous zero-phase pass instead of per-window filter_window() calls, both
    # faster and slightly more correct (edge effects only at the true file start/end).
    data = raw.get_data()  # [18, n_total_samples], float64
    bp = sosfiltfilt(preprocessing._BP_SOS, data, axis=1)
    notched = filtfilt(preprocessing._NOTCH_B, preprocessing._NOTCH_A, bp, axis=1)
    usable = n_windows * preprocessing.WIN_SAMPLES
    filtered = np.ascontiguousarray(
        notched[:, :usable].reshape(N_CH, n_windows, preprocessing.WIN_SAMPLES).transpose(1, 0, 2)
    )
    # Step 4 (CC_STEP4_PROMPT.md): Panel EEG's raw/filtered dual-view needs the SAME
    # continuous windowing applied to the untouched signal, not just `filtered` — reuse
    # `data` (already read above, pre-filter) rather than re-reading the EDF.
    raw_windows = np.ascontiguousarray(
        data[:, :usable].reshape(N_CH, n_windows, preprocessing.WIN_SAMPLES).transpose(1, 0, 2)
    )
    _check()

    # Stored as float32 (not float64) purely to keep memory bounded while every file of a
    # subject's raw windows sits in RAM until Phase B runs — a multi-hour, multi-file subject
    # would otherwise use ~2x the RAM for no measurable precision benefit at this stage
    # (band powers / adjacency downstream are float32 already).
    filtered = filtered.astype(np.float32)
    raw_windows = raw_windows.astype(np.float32)
    filtered_path = None
    raw_path = None
    if cache_dir is not None:
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        filtered_path = cache_dir / f"{Path(edf_path).stem}.filtered.npy"
        np.save(filtered_path, filtered)
        raw_path = cache_dir / f"{Path(edf_path).stem}.raw.npy"
        np.save(raw_path, raw_windows)

    return PhaseAResult(
        filename=Path(edf_path).name,
        filtered=filtered,
        n_windows=n_windows,
        start_time=start_time,
        file_duration_seconds=file_duration_seconds,
        filtered_path=filtered_path,
        raw_path=raw_path,
    )


def process_subject_phase_b(
    filtered_by_filename: dict[str, np.ndarray], device: str = "cpu"
) -> dict[str, np.ndarray]:
    """Phase B (SPEC §1.6a / CC_STEP3_PROMPT.md §1): subject-wide z-score + LedoitWolf +
    robust-z fits, rest of the pipeline run per file. Returns {filename: ensemble score
    array}, each exactly as long as that file's own window count.

    Takes plain filtered-window arrays (Phase A's output), not PhaseAResult objects —
    deliberately, so this function's only "large" input is exactly what it needs, which
    matters when it's invoked in a separate process (see process_subject_phase_b_from_paths):
    passing PhaseAResult objects across that boundary would carry the same arrays either way,
    but keeping this function's signature array-only makes the disk hand-off in the
    process-pool wrapper the obvious place to look, not something buried in a dataclass.
    """
    filenames_sorted = sorted(filtered_by_filename.keys())
    if not filenames_sorted:
        return {}

    # 1-2. Subject-wide z-score stats, fit on every currently-uploaded file's windows.
    all_filtered = np.concatenate(
        [filtered_by_filename[f] for f in filenames_sorted], axis=0
    ).astype(np.float64)
    ch_mean = all_filtered.mean(axis=(0, 2))
    ch_std = all_filtered.std(axis=(0, 2))
    ch_std = np.where(ch_std > 0, ch_std, 1.0)
    del all_filtered

    _verify_checkpoint(CHECKPOINT_PATH)
    model = gae_joint.load_checkpoint(CHECKPOINT_PATH, device)
    model.eval()

    gamma_b, gamma_a = compute_gamma_aec.make_gamma_filter()

    # 3. Per file: z-score with SUBJECT-wide stats, then adjacency/band-power/GAE/gamma.
    per_file_raw: dict[str, dict] = {}
    for f in filenames_sorted:
        filtered = filtered_by_filename[f].astype(np.float64)
        n_windows = filtered.shape[0]
        zscored = (filtered - ch_mean[None, :, None]) / ch_std[None, :, None]

        adjacency = np.empty((n_windows, N_CH, N_CH), dtype=np.float32)
        band_powers = np.empty((n_windows, N_CH, 5), dtype=np.float32)
        for i in range(n_windows):
            window = zscored[i]
            car = graph_construction.apply_car(window)
            wpli = graph_construction.compute_wpli(car)
            aec = graph_construction.compute_aec(car)
            A = graph_construction.combine_adjacency(wpli, aec, alpha=graph_construction.DEFAULT_ALPHA)
            A = graph_construction.apply_topk_threshold(A, keep_ratio=graph_construction.DEFAULT_KEEP_RATIO)
            adjacency[i] = A.astype(np.float32)
            band_powers[i] = feature_extraction.compute_band_powers(window)

        A_t = torch.tensor(adjacency, dtype=torch.float32)
        X_t = torch.tensor(band_powers, dtype=torch.float32)
        pg, A_batch, Xn_batch, B = gae_joint.build_batch(A_t, X_t, device)

        with torch.no_grad():
            z = model.encoder(pg.x, pg.edge_index, pg.edge_attr)
            graph_z = z.view(B, N_CH, gae_joint.LATENT_DIM).mean(dim=1)
            zrecon_raw = gae_joint.joint_score(model, pg, A_batch, Xn_batch, B, per_node=False)

        zrecon_raw = zrecon_raw.cpu().numpy().astype(np.float64)
        graph_z_np = graph_z.cpu().numpy().astype(np.float64)

        zgamma_raw = np.empty(n_windows, dtype=np.float32)
        zscored_f32 = zscored.astype(np.float32)
        for s in range(0, n_windows, compute_gamma_aec.BATCH_SIZE):
            e = min(s + compute_gamma_aec.BATCH_SIZE, n_windows)
            zgamma_raw[s:e] = compute_gamma_aec.compute_gamma_scores_batch(
                zscored_f32[s:e], gamma_b, gamma_a
            )

        per_file_raw[f] = dict(
            zrecon_raw=zrecon_raw, graph_z=graph_z_np, zgamma_raw=zgamma_raw.astype(np.float64)
        )

    # 4. zlatent — LedoitWolf fit on the SUBJECT-wide concatenated graph-level Z (SPEC §1.6a).
    all_graph_z = np.concatenate([per_file_raw[f]["graph_z"] for f in filenames_sorted], axis=0)
    cov = LedoitWolf().fit(all_graph_z)
    for f in filenames_sorted:
        per_file_raw[f]["zlatent_raw"] = cov.mahalanobis(per_file_raw[f]["graph_z"])

    # 5. Robust-z — SPEC §1.6a's table: NOT a divergence, thesis already fits this on the
    # whole window set available at that stage. Here "the whole window set" is the subject's
    # concatenated per-branch raw arrays; fit median/MAD subject-wide, apply per file.
    all_zrecon = np.concatenate([per_file_raw[f]["zrecon_raw"] for f in filenames_sorted])
    all_zlatent = np.concatenate([per_file_raw[f]["zlatent_raw"] for f in filenames_sorted])
    all_zgamma = np.concatenate([per_file_raw[f]["zgamma_raw"] for f in filenames_sorted])
    med_r, mad_r = _median_mad(all_zrecon)
    med_l, mad_l = _median_mad(all_zlatent)
    med_g, mad_g = _median_mad(all_zgamma)

    scores: dict[str, np.ndarray] = {}
    for f in filenames_sorted:
        zr = (per_file_raw[f]["zrecon_raw"] - med_r) / mad_r
        zl = (per_file_raw[f]["zlatent_raw"] - med_l) / mad_l
        zg = (per_file_raw[f]["zgamma_raw"] - med_g) / mad_g
        score = ensemble_recipe.build_ensemble_subset(
            {"zrecon": zr, "zlatent": zl, "zgamma": zg},
            subset=ensemble_recipe.CANDIDATES["rlg"],
        )
        scores[f] = score.astype(np.float64)

    return scores


def process_subject_phase_b_from_paths(
    filtered_paths: dict[str, str], device: str = "cpu"
) -> dict[str, np.ndarray]:
    """Process-pool entry point for Phase B (see upload_manager.py's `_executor`). Takes
    filename -> filtered_path (from PhaseAResult.filtered_path) and loads each array from
    disk INSIDE the worker process, instead of the caller passing the arrays themselves —
    ProcessPoolExecutor's call queue reliably deadlocks on Windows when asked to move a few
    hundred MB of numpy data through it, but a handful of path strings is negligible.
    """
    filtered_by_filename = {fn: np.load(p) for fn, p in filtered_paths.items()}
    return process_subject_phase_b(filtered_by_filename, device=device)


@dataclass
class OperatingPointResult:
    pen_mult: float
    event_rate_per_day: float
    grid: list[tuple[float, int, float]]  # (pen_mult, n_events, rate_per_day) for every value tried


def calibrate_operating_point(global_score: np.ndarray, total_hours: float) -> OperatingPointResult:
    """SPEC §8 O1 — label-free, per-subject operating-point calibration.

    The live subject has no ground truth, so the thesis's SzCORE FP/day (which needs
    interictal labels) can't be computed. Approximate it the same way SPEC §1.6a's
    label-free equivalence argument justifies elsewhere: treat the WHOLE recording as the
    interictal-equivalent denominator (seizure prevalence is ~0.2%, so this is numerically
    indistinguishable from a true interictal-only rate). For each pen_mult in the grid,
    run detect_events() and count events/24h of the subject's total recording; pick the
    pen_mult whose resulting rate is closest to fp_budget.BUDGETS["balanced"] (read live from
    src/retrain/fp_budget_operating_point.py, never hardcoded — SPEC §8 O1).
    """
    grid: list[tuple[float, int, float]] = []
    best: tuple[float, float] | None = None  # (pen_mult, |rate - target|)
    best_rate = 0.0
    for pen_mult in PEN_MULT_GRID:
        events = cpd_pipeline_v14.detect_events(global_score, pen_mult, min_mag_pct=MIN_MAG_PCT)
        rate_per_day = (len(events) / total_hours * 24.0) if total_hours > 0 else 0.0
        grid.append((pen_mult, len(events), rate_per_day))
        diff = abs(rate_per_day - TARGET_FP_PER_DAY)
        if best is None or diff < best[1]:
            best = (pen_mult, diff)
            best_rate = rate_per_day

    return OperatingPointResult(pen_mult=best[0], event_rate_per_day=best_rate, grid=grid)


@dataclass
class FileEvent:
    onset_sec: float
    offset_sec: float


def process_subject_events(
    scores_by_filename: dict[str, np.ndarray],
) -> tuple[dict[str, list[FileEvent]], OperatingPointResult]:
    """Stage 2 (SPEC §5.5 / §1.5): concatenate per-file Phase B scores in FILENAME order,
    run PELT once on the whole timeline at a label-free-calibrated operating point, then
    assign each event back to its file by cumulative offset. No lookup module needed —
    SPEC §1.5 is explicit that this falls out of the per-file score lengths by construction.
    """
    win_sec = float(preprocessing.WIN_S)
    filenames_sorted = sorted(scores_by_filename.keys())

    offsets: dict[str, int] = {}
    cur = 0
    for f in filenames_sorted:
        offsets[f] = cur
        cur += len(scores_by_filename[f])
    total_windows = cur
    total_hours = (total_windows * win_sec) / 3600.0

    global_score = np.concatenate([scores_by_filename[f] for f in filenames_sorted])
    op = calibrate_operating_point(global_score, total_hours)
    events_global = cpd_pipeline_v14.detect_events(global_score, op.pen_mult, min_mag_pct=MIN_MAG_PCT)

    file_events: dict[str, list[FileEvent]] = {f: [] for f in filenames_sorted}
    for onset_s, offset_s in events_global:
        onset_win = onset_s / win_sec
        for f in filenames_sorted:
            lo = offsets[f]
            hi = lo + len(scores_by_filename[f])
            if lo <= onset_win < hi:
                local_onset = (onset_win - lo) * win_sec
                local_offset = local_onset + (offset_s - onset_s)
                file_events[f].append(FileEvent(onset_sec=local_onset, offset_sec=local_offset))
                break

    return file_events, op


def process_file(edf_path: str, device: str = "cpu", timing: dict | None = None) -> np.ndarray:
    """Single-file convenience wrapper (Phase A then Phase B on just that one file) — kept
    for the Step 1 CLI smoke test below, where file-level == subject-level by construction.
    """
    t_start = time.perf_counter()
    t0 = time.perf_counter()
    phase_a = process_file_phase_a(edf_path)
    t_phase_a = time.perf_counter() - t0

    t0 = time.perf_counter()
    scores = process_subject_phase_b({phase_a.filename: phase_a.filtered})
    t_phase_b = time.perf_counter() - t0

    if timing is not None:
        timing["phase_a"] = t_phase_a
        timing["phase_b"] = t_phase_b
        timing["total"] = time.perf_counter() - t_start

    return scores[phase_a.filename]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Dev CLI for pipeline_demo.process_file — Step 1 smoke test / timing "
                     "(DEMO_BUILD_HANDOFF.md §6, row 1). Not a clinical readout."
    )
    parser.add_argument("--edf_path", required=True, help="Path to one .edf file")
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    edf_path = Path(args.edf_path)

    timing: dict = {}
    t0 = time.perf_counter()
    score = process_file(str(edf_path), device=args.device, timing=timing)
    elapsed_s = time.perf_counter() - t0

    n_windows = len(score)
    window_s = preprocessing.WIN_SAMPLES / preprocessing.FS  # 4.0 s
    hours_of_eeg = (n_windows * window_s) / 3600.0
    rate_s_per_hour = elapsed_s / hours_of_eeg if hours_of_eeg > 0 else float("nan")

    print(f"file: {edf_path.name}")
    print(f"windows: {n_windows}")
    print(f"score.shape: {score.shape}")
    print(
        f"score min/max/mean: {score.min():.4f} / {score.max():.4f} / {score.mean():.4f}  "
        "(sanity check only -- not a clinical readout)"
    )
    print(f"wall-clock time: {elapsed_s:.2f} s")
    print(f"rate: {rate_s_per_hour:.2f} s per hour of EEG  (target: ~15 s/hour, CLAUDE.md)")
    print(f"\nstage breakdown: phase A (open/filter/window) {timing['phase_a']:.2f} s, "
          f"phase B (adjacency/GAE/gamma/ensemble) {timing['phase_b']:.2f} s, "
          f"total {timing['total']:.2f} s")

    total_hours = hours_of_eeg
    op = calibrate_operating_point(score, total_hours)
    print(f"\noperating-point calibration (SPEC §8 O1, target {TARGET_FP_PER_DAY:g} FP/day):")
    for pen_mult, n_events, rate in op.grid:
        marker = "  <-- chosen" if pen_mult == op.pen_mult else ""
        print(f"  pen_mult={pen_mult:5g}  events={n_events:3d}  rate={rate:7.2f}/day{marker}")
