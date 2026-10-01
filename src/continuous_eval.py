#!/usr/bin/env python
"""
continuous_eval.py -- docs/CC_PROMPT_CONTINUOUS_EVAL.md, Gates + Steps A/B/C.

Runs the locked thesis pipeline, UNCHANGED, on the real continuous CHB-MIT timeline (every
window scored, files in file-name order, window i = [4i, 4i+4) s of its file -- exactly as
the application does), under two fitting scopes:

  Scope T (thesis)  -- z-score / LedoitWolf / per-branch median-MAD / CPD variance+magnitude
                        background fitted on windows that are not ictal, not in the 4h
                        post-seizure buffer, not artifact-rejected (inter_mask passed to
                        cpd_pipeline_v14.detect_changepoints).
  Scope W (application) -- the same, fitted on every window (no mask), inter_mask=None.

Never calls szcore_eval.build_timeline_masked (that reconstructs the resampled/masked offline
timeline this evaluation deliberately does NOT use). Reuses, never re-implements:
  dataprep.preprocessing  (open_edf, filter coefficients _BP_SOS/_NOTCH_B/_NOTCH_A, WIN_SAMPLES,
                            build_labels, build_buffer_mask, COMMON_CHANNELS)
  dataprep.graph_construction (apply_car, compute_wpli, compute_aec, combine_adjacency,
                            apply_topk_threshold, DEFAULT_ALPHA, DEFAULT_KEEP_RATIO)
  dataprep.feature_extraction (compute_band_powers)
  dataprep.compute_gamma_aec (make_gamma_filter, compute_gamma_scores_batch)
  retrain.gae_joint        (GAEModel, load_checkpoint, build_batch, joint_score -- the GAE
                            scoring used for the committed ens_seed42_* arrays)
  ensemble_recipe          (build_ensemble_subset, CANDIDATES['rlg'])
  cpd_pipeline_v14         (detect_changepoints -- PELT/magnitude filter; the merge-into-events
                            step is inlined below, byte-identical to detect_events's own loop,
                            so pen_mult's one PELT fit can be reused across the merge_s grid
                            -- verified against detect_events directly in --verify_fast_grid)
  szcore_eval               (score_szcore, matched_latency, per_interval_match, SZ_PARAM,
                            WIN_SEC, TEST_SUBJS, PEN_MULTS -- SCORING functions only)
  evaluation_protocol       (parse_summary_edf_list)

web_demo/backend/pipeline_demo.py was READ (never imported/edited) to confirm the application's
own continuous recipe (whole-file zero-phase filtering, subject-wide unmasked z-score/LedoitWolf/
robust-z, rlg subset) -- Scope W reproduces it from the canonical modules above, independently.

Design note on the artifact mask: unlike src/diag_application_gap.py (which had to re-derive
filtered windows purely to decide artifact status, since it only had already-scored application
output to work from), this script already holds the whole-file zero-phase-filtered windows used
for THIS run's own scoring -- so the artifact check (peak abs sample vs. the committed per-channel
5xSD threshold from data/processed/{subj}_stats.json) is read directly off those same windows
instead of re-deriving them via preprocessing.filter_window's per-window padding. This is strictly
more consistent (same filtered signal drives both the artifact decision and the score) and avoids
redoing ~90 min of filtering; the difference between whole-file and per-window zero-phase filtering
away from a file boundary is negligible relative to the 5xSD threshold.

Usage:
  python src/continuous_eval.py --smoke                       # one validation file
  python src/continuous_eval.py --stage score --subjects chb10   # one validation patient
  python src/continuous_eval.py --stage score                 # all 11 subjects, both scopes
  python src/continuous_eval.py --stage gates                  # G1, G2
  python src/continuous_eval.py --stage abc                    # Steps A, B, C + SUMMARY.md
  python src/continuous_eval.py --stage all                    # score -> gates -> abc
"""
import argparse
import gc
import hashlib
import json
import sys
import time
from pathlib import Path

import psutil

import numpy as np
import pandas as pd
import torch
from scipy.signal import sosfiltfilt, filtfilt
from scipy.stats import pearsonr, spearmanr
from sklearn.covariance import LedoitWolf
from sklearn.metrics import roc_auc_score
import ruptures as rpt

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src", ROOT / "src" / "dataprep", ROOT / "src" / "retrain"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import preprocessing as P            # noqa: E402
import graph_construction as GC      # noqa: E402
import feature_extraction as FE      # noqa: E402
import compute_gamma_aec as GA       # noqa: E402
import gae_joint as G                # noqa: E402
import ensemble_recipe as ER         # noqa: E402
import cpd_pipeline_v14 as V14       # noqa: E402
import szcore_eval as SE             # noqa: E402
import evaluation_protocol as E      # noqa: E402

torch.set_num_threads(1)

# ── constants ────────────────────────────────────────────────────────────────
WIN_SEC = P.WIN_S                       # 4
N_CH = len(P.COMMON_CHANNELS)           # 18
DATASET_DIR = Path("F:/Study/Thesis/Dataset/CHB-MIT")
SUMMARY_DIR = ROOT / "data" / "summaries"
PROCESSED_DIR = ROOT / "data" / "processed"
CKPT_PATH = ROOT / "data" / "models_retrain" / "gae_joint_seed42.pt"
CKPT_SHA256 = "dea06cb533df1c7d0520ae21c4cbb1b8a938297f937366bc9915b040726ea108"
UPLOADS_DIR = ROOT / "web_demo" / "backend" / "uploads"

OUT_DIR = ROOT / "results" / "continuous_eval"
CACHE_DIR = OUT_DIR / "cache"
LOG_PATH = OUT_DIR / "run.log"

VAL_SUBJS = ["chb10", "chb11", "chb22"]
TEST_SUBJS = list(SE.TEST_SUBJS)        # 8
ALL_SUBJS = VAL_SUBJS + TEST_SUBJS      # 11
SCOPES = ("T", "W")

MAG_PCTS = [40.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0]   # same grid as the thesis (score_ens.py)
PEN_MULTS = list(SE.PEN_MULTS)                                 # [0.3,0.5,1.0,2.0,5.0,10.0]
MERGE_GAPS = [90, 300]
FIXED_MAG, FIXED_PEN, FIXED_MERGE = 50.0, 2.0, 90

D0A_TABLE9 = dict(sensitivity=0.618, precision=0.129, f1=0.213, fp_per_day=27.4)


# ── logging ──────────────────────────────────────────────────────────────────
def log(tag, msg):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    line = f"[{tag}] {time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ── model / filters (lazy singletons) ───────────────────────────────────────
_MODEL = None
_GAMMA = None


def get_model():
    global _MODEL
    if _MODEL is None:
        actual = hashlib.sha256(CKPT_PATH.read_bytes()).hexdigest()
        assert actual == CKPT_SHA256, f"checkpoint hash mismatch: {actual}"
        _MODEL = G.load_checkpoint(CKPT_PATH, "cpu")
        _MODEL.eval()
    return _MODEL


def get_gamma_filter():
    global _GAMMA
    if _GAMMA is None:
        _GAMMA = GA.make_gamma_filter()
    return _GAMMA


_PROC = psutil.Process()


def rss_mb():
    return _PROC.memory_info().rss / 1e6


def sys_avail_mb():
    return psutil.virtual_memory().available / 1e6


def median_mad(x):
    med = float(np.median(x))
    mad = float(np.median(np.abs(x - med))) + 1e-9
    return med, mad


# ── file listing ─────────────────────────────────────────────────────────────
def list_files(subj):
    """evaluation_protocol.parse_summary_edf_list, filtered to files actually present under
    DATASET_DIR/{subj}/ -- matching preprocessing.py's own convention (it globs
    `(raw_dir/subject_id).glob("*.edf")` rather than trusting the summary text, so the
    committed chb11_stats.json etc. were already built only from the files that exist).
    On this machine chb11_12/13/14.edf are listed in the summary but absent from the local
    dataset copy (chb11: summary lists 35 files, 31 present, gap=[12,13,14,15].edf; every
    other subject used here has 0 gap -- verified once, logged here every time it matters)."""
    edfs = E.parse_summary_edf_list(SUMMARY_DIR / f"{subj}-summary.txt")
    present = {p.name for p in (DATASET_DIR / subj).glob("*.edf")}
    kept = [e for e in edfs if e["fname"] in present]
    missing = [e["fname"] for e in edfs if e["fname"] not in present]
    if missing:
        log("G2", f"{subj}: {len(missing)} summary-listed file(s) absent from the local "
                  f"dataset copy, skipped (matches preprocessing.py's own glob convention): "
                  f"{missing}")
    return kept


def edf_path(subj, fname):
    return DATASET_DIR / subj / fname


# ── Phase 0: whole-file zero-phase filter (byte-for-byte the application's own convention:
#    process_file_phase_a filters the WHOLE recording in one sosfiltfilt/filtfilt pass, not
#    per-window or per-chunk). A chunked/padded-segment version was tried to bound memory,
#    and was numerically close (max abs diff ~7e-6 on a ~2.6e-3 scale) but NOT worth the risk:
#    a discrete operation downstream (apply_topk_threshold's top-20% cutoff) can flip on tiny
#    per-window noise, and gate G1 requires >=0.999 Pearson against the application's actual
#    whole-file-filtered scores. The earlier OOM kills that motivated chunking turned out to
#    be caused by duplicate concurrent processes (see run.log ~18:00-18:20), not by this
#    function's own peak -- a single clean process holds at most two float64 intermediates at
#    once (data->bp->notched, each freed before the next is created), which measured safe. ──
def filter_file(path):
    raw = P.open_edf(path)
    if raw is None:
        raise RuntimeError(f"{path}: missing one of the 18 common channels")
    n_windows = int(raw.n_times) // P.WIN_SAMPLES
    if n_windows == 0:
        raise RuntimeError(f"{path}: shorter than one 4 s window")
    data = raw.get_data()
    del raw
    bp = sosfiltfilt(P._BP_SOS, data, axis=1)
    del data
    notched = filtfilt(P._NOTCH_B, P._NOTCH_A, bp, axis=1)
    del bp
    usable = n_windows * P.WIN_SAMPLES
    filtered = np.ascontiguousarray(
        notched[:, :usable].reshape(N_CH, n_windows, P.WIN_SAMPLES).transpose(1, 0, 2)
    ).astype(np.float32)
    del notched
    gc.collect()
    return filtered, n_windows


# ── Correction C1 (docs/CC_PROMPT_CONTINUOUS_EVAL.md, 2026-10-01): Scope T's SCORED SIGNAL
#    must use preprocessing.filter_window -- the locked thesis pipeline's own per-window,
#    FILTER_PAD-padded filtering (exactly what write_windows/count_windows use to build the
#    committed offline arrays) -- not whole-file filtering. Scope W keeps filter_file() (the
#    application's own convention, needed for gate G1). This is slower (one raw.get_data() read
#    per window instead of one per file) but is what "Scope T is the locked pipeline, unchanged"
#    requires; the artifact mask already used filter_window (see compute_artifact_flags below),
#    only the scored signal itself was, until this correction, filtered the fast whole-file way.
def filter_file_per_window(path):
    raw = P.open_edf(path)
    if raw is None:
        raise RuntimeError(f"{path}: missing one of the 18 common channels")
    n_windows = int(raw.n_times) // P.WIN_SAMPLES
    if n_windows == 0:
        raise RuntimeError(f"{path}: shorter than one 4 s window")
    filtered = np.empty((n_windows, N_CH, P.WIN_SAMPLES), dtype=np.float32)
    for i in range(n_windows):
        w = P.filter_window(raw, i * P.WIN_SAMPLES, i * P.WIN_SAMPLES + P.WIN_SAMPLES)
        filtered[i] = w.astype(np.float32)
    del raw
    gc.collect()
    return filtered, n_windows


# ── artifact mask: preprocessing.filter_window (per-window, 3 s padding), NOT the whole-file
#    filtered array. Verified necessary, not optional: on chb16, using the whole-file-filtered
#    array's peak amplitude for the 5xSD check gave background windows whose raw zrecon only
#    rank-correlated at rho=0.39 with the committed offline interictal array (vs rho=1.0 for
#    ictal windows, which are never artifact-checked) -- a few borderline threshold-crossing
#    windows flip accept/reject on numerically tiny filtering differences near the hard cutoff,
#    which then desynchronizes every later window's POSITION in the retained-interictal
#    sequence (not just the borderline window's own value). Switching to filter_window (the
#    same per-window, 3 s-padded convention preprocessing.count_windows/write_windows use, and
#    the one src/diag_application_gap.py already validated for exactly this purpose) restored
#    rho=0.9977 and an exact count match (6428/6428) on chb16. Costs ~80 min extra across the
#    test subjects (diag_application_gap.py's own measured figure) but is not optional for G2.
def compute_artifact_flags(raw, n_windows, wl, wb, artifact_threshold):
    art = np.zeros(n_windows, dtype=bool)
    for i in range(n_windows):
        if wl[i] or wb[i]:
            continue
        w = P.filter_window(raw, i * P.WIN_SAMPLES, i * P.WIN_SAMPLES + P.WIN_SAMPLES)
        if np.any(np.abs(w).max(axis=1) > artifact_threshold):
            art[i] = True
    return art


# ── Amendment A2 (docs/CC_PROMPT_CONTINUOUS_EVAL.md, 2026-10-01, root cause in
#    results/continuous_eval/chb17b_69_inspect.txt): hardware signal-loss (flat-lined raw
#    EEG, e.g. chb17b_69.edf local windows 694-860) was found numerically undefined through
#    the GAE/connectivity pipeline, corrupting gate G2's rank correlation for chb17
#    (rho_inter 0.6973) even though the window counts matched exactly. Flag is on the RAW
#    (unfiltered) signal, fixed threshold, no annotation -- real EEG ~1e-5 V, flat ~1e-22 V.
SIGNAL_LOSS_STD_V = 1e-10


def compute_signal_loss_flags(raw, n_windows):
    """Window i is signal-loss if the std of the raw segment is below SIGNAL_LOSS_STD_V on
    every one of the 18 channels. raw is preload=False (P.open_edf), so each
    raw.get_data(start=,stop=) call reads only this one window's [18, WIN_SAMPLES] segment
    from disk -- bounded memory regardless of file length, same streaming pattern already
    used per-window above (compute_artifact_flags, preprocessing.filter_window)."""
    flags = np.zeros(n_windows, dtype=bool)
    for i in range(n_windows):
        seg = raw.get_data(start=i * P.WIN_SAMPLES, stop=(i + 1) * P.WIN_SAMPLES)
        flags[i] = bool(np.all(seg.std(axis=1) < SIGNAL_LOSS_STD_V))
    return flags


# ── per-window connectivity/features/GAE/gamma (mirrors pipeline_demo.process_subject_phase_b) ─
def compute_window_components(zscored, model, gamma_b, gamma_a):
    """zscored: [N,18,1024] float64. Returns dict(zrecon_raw[N], graph_z[N,16], zgamma_raw[N])."""
    n = zscored.shape[0]
    adjacency = np.empty((n, N_CH, N_CH), dtype=np.float32)
    band_powers = np.empty((n, N_CH, 5), dtype=np.float32)
    for i in range(n):
        w = zscored[i]
        car = GC.apply_car(w)
        wpli = GC.compute_wpli(car)
        aec = GC.compute_aec(car)
        A = GC.combine_adjacency(wpli, aec, alpha=GC.DEFAULT_ALPHA)
        A = GC.apply_topk_threshold(A, keep_ratio=GC.DEFAULT_KEEP_RATIO)
        adjacency[i] = A.astype(np.float32)
        band_powers[i] = FE.compute_band_powers(w)

    A_t = torch.tensor(adjacency, dtype=torch.float32)
    X_t = torch.tensor(band_powers, dtype=torch.float32)
    pg, A_batch, Xn_batch, B = G.build_batch(A_t, X_t, "cpu")
    with torch.no_grad():
        z = model.encoder(pg.x, pg.edge_index, pg.edge_attr)
        graph_z = z.view(B, N_CH, G.LATENT_DIM).mean(dim=1)
        zrecon_raw = G.joint_score(model, pg, A_batch, Xn_batch, B, per_node=False)
    zrecon_raw = zrecon_raw.cpu().numpy().astype(np.float64)
    graph_z_np = graph_z.cpu().numpy().astype(np.float64)

    zscored_f32 = zscored.astype(np.float32)
    zgamma_raw = np.empty(n, dtype=np.float32)
    for s in range(0, n, GA.BATCH_SIZE):
        e = min(s + GA.BATCH_SIZE, n)
        zgamma_raw[s:e] = GA.compute_gamma_scores_batch(zscored_f32[s:e], gamma_b, gamma_a)

    return dict(zrecon_raw=zrecon_raw, graph_z=graph_z_np, zgamma_raw=zgamma_raw.astype(np.float64))


def zscore(filtered, ch_mean, ch_std):
    return (filtered.astype(np.float64) - ch_mean[None, :, None]) / ch_std[None, :, None]


CHUNK_WINDOWS = 256   # ~17 min of EEG/chunk; bounds peak RAM regardless of file length


def score_file_chunked(filtered, ch_mean, ch_std, model, gamma_b, gamma_a, chunk=CHUNK_WINDOWS):
    """Same math as zscore() + compute_window_components() applied to the whole file at
    once (every op therein is per-window independent -- no cross-window state), but bounds
    peak RAM to O(chunk) instead of O(file length): a whole chb06 file z-scored to float64
    is ~500+ MB, which combined with its own float32 copy for gamma and the still-alive
    float32 `filtered` was enough to OOM-kill this run under this machine's memory pressure."""
    n = filtered.shape[0]
    zrecon_raw = np.empty(n, dtype=np.float64)
    graph_z = np.empty((n, G.LATENT_DIM), dtype=np.float64)
    zgamma_raw = np.empty(n, dtype=np.float64)
    for s in range(0, n, chunk):
        e = min(s + chunk, n)
        zsc = zscore(filtered[s:e], ch_mean, ch_std)
        comp = compute_window_components(zsc, model, gamma_b, gamma_a)
        zrecon_raw[s:e] = comp["zrecon_raw"]
        graph_z[s:e] = comp["graph_z"]
        zgamma_raw[s:e] = comp["zgamma_raw"]
        del zsc, comp
    return dict(zrecon_raw=zrecon_raw, graph_z=graph_z, zgamma_raw=zgamma_raw)


# ── per-subject: filter + mask + both scopes ────────────────────────────────
def mask_cache_path(subj):
    return CACHE_DIR / "mask" / f"{subj}.npz"


def scores_cache_path(scope, subj):
    return CACHE_DIR / "scores" / f"{scope}_{subj}.npy"


def load_mask(subj):
    z = np.load(mask_cache_path(subj), allow_pickle=True)
    spans = [tuple(x) for x in z["spans"]]
    sz_ranges = [tuple(int(v) for v in x) for x in z["sz_ranges"]]
    return dict(is_ictal=z["is_ictal"], is_buffer=z["is_buffer"], is_artifact=z["is_artifact"],
                is_signal_loss=z["is_signal_loss"], spans=spans, sz_ranges=sz_ranges)


def process_subject(subj, log_tag_prefix="G", force=False):
    """Memory-bounded: never holds more than ONE file's filtered EEG in RAM at a time
    (holding a whole subject's filtered windows at once -- e.g. ~3-4 GiB for a large
    subject like chb06 -- was observed to OOM-kill the process on this machine). Filters
    each file at most twice: once in the combined mask+ScopeT+W-stats-accumulation pass,
    once more in a second pass for Scope W's own z-scored components (Scope W's channel
    stats are subject-wide and unknown until every file's raw sum/sumsq is seen, so its
    per-window components can only be computed after that first pass finishes)."""
    mpath = mask_cache_path(subj)
    tpath = scores_cache_path("T", subj)
    wpath = scores_cache_path("W", subj)
    if not force and mpath.exists() and tpath.exists() and wpath.exists():
        log(f"{log_tag_prefix}2", f"{subj}: cached, skip")
        return
    t0 = time.time()
    (CACHE_DIR / "mask").mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / "scores").mkdir(parents=True, exist_ok=True)

    edfs = list_files(subj)
    fnames_sorted = [e["fname"] for e in edfs]   # parse_summary_edf_list already sorts by fname
    stats = json.loads((PROCESSED_DIR / f"{subj}_stats.json").read_text())
    artifact_threshold = np.asarray(stats["artifact_thresh_uV"], dtype=np.float64) * 1e-6
    ch_mean_T = np.asarray(stats["ch_mean_uV"], dtype=np.float64) * 1e-6
    ch_std_T = np.asarray(stats["ch_std_uV"], dtype=np.float64) * 1e-6

    need_T = force or not tpath.exists()
    need_W = force or not wpath.exists()
    need_mask = force or not mpath.exists()
    model = get_model()
    gamma_b, gamma_a = get_gamma_filter()

    # ---- Pass 1 (one file in RAM at a time): mask, Scope T raw components, Scope W's
    #      subject-wide sum/sumsq accumulation (E[X^2]-E[X]^2 -- well-conditioned here,
    #      the bandpass-filtered signal has ~zero mean, so no cancellation risk). ----
    is_ictal_parts, is_buffer_parts, is_artifact_parts, is_signal_loss_parts, spans = [], [], [], [], []
    raw_T_zrecon, raw_T_graph_z, raw_T_zgamma = [], [], []
    sum_parts, sumsq_parts = [], []
    n_windows_total = 0
    cur = 0
    for edf in edfs:
        fname = edf["fname"]
        filtered, n_windows = filter_file(edf_path(subj, fname))

        if need_mask:
            n_secs_covered = n_windows * WIN_SEC
            seizure_list = edf["seizures"]
            labels = P.build_labels(n_secs_covered, seizure_list)
            buf = P.build_buffer_mask(n_secs_covered, seizure_list)
            wl = labels.reshape(n_windows, WIN_SEC).max(axis=1) == 1
            wb = buf.reshape(n_windows, WIN_SEC).any(axis=1)
            raw_for_artifact = P.open_edf(edf_path(subj, fname))
            art = compute_artifact_flags(raw_for_artifact, n_windows, wl, wb, artifact_threshold)
            sl = compute_signal_loss_flags(raw_for_artifact, n_windows)   # Amendment A2
            del raw_for_artifact
            is_ictal_parts.append(wl); is_buffer_parts.append(wb); is_artifact_parts.append(art)
            is_signal_loss_parts.append(sl)
            spans.append((fname, cur, cur + n_windows))
            n_art = int(art.sum())
        else:
            n_art = -1
        cur += n_windows

        if need_T:
            comp = score_file_chunked(filtered, ch_mean_T, ch_std_T, model, gamma_b, gamma_a)
            raw_T_zrecon.append(comp["zrecon_raw"])
            raw_T_graph_z.append(comp["graph_z"])
            raw_T_zgamma.append(comp["zgamma_raw"])
            del comp

        if need_W:
            n_windows_total += n_windows
            for s in range(0, n_windows, CHUNK_WINDOWS):
                e = min(s + CHUNK_WINDOWS, n_windows)
                f64 = filtered[s:e].astype(np.float64)
                sum_parts.append(f64.sum(axis=2))
                sumsq_parts.append((f64 * f64).sum(axis=2))
                del f64

        del filtered
        gc.collect()
        log(f"{log_tag_prefix}2", f"{subj}/{fname}: pass1 {n_windows} windows "
                                  f"(artifacts={n_art}) rss={rss_mb():.0f}MB "
                                  f"sys_avail={sys_avail_mb():.0f}MB")

    if need_mask:
        is_ictal = np.concatenate(is_ictal_parts)
        is_buffer = np.concatenate(is_buffer_parts)
        is_artifact = np.concatenate(is_artifact_parts)
        is_signal_loss = np.concatenate(is_signal_loss_parts)
        sz_ranges = []
        in_s, ss = False, 0
        for i, ic in enumerate(is_ictal):
            if ic and not in_s:
                ss, in_s = i, True
            elif not ic and in_s:
                sz_ranges.append((ss, i)); in_s = False
        if in_s:
            sz_ranges.append((ss, len(is_ictal)))
        np.savez(mpath, is_ictal=is_ictal, is_buffer=is_buffer, is_artifact=is_artifact,
                 is_signal_loss=is_signal_loss,
                 spans=np.array(spans, dtype=object), sz_ranges=np.array(sz_ranges, dtype=object))
    else:
        m = load_mask(subj)
        is_ictal, is_buffer, is_artifact = m["is_ictal"], m["is_buffer"], m["is_artifact"]
        is_signal_loss = m["is_signal_loss"]
    background_mask = (~is_ictal) & (~is_buffer) & (~is_artifact)
    fit_mask_T = background_mask & (~is_signal_loss)        # Amendment A2
    fit_mask_W = ~is_signal_loss                             # Amendment A2

    # ---- finalize Scope T (fit LedoitWolf/robust-z on background_mask only, apply to all) ----
    if need_T:
        all_graph_z = np.concatenate(raw_T_graph_z, axis=0)
        all_zrecon = np.concatenate(raw_T_zrecon)
        all_zgamma = np.concatenate(raw_T_zgamma)
        del raw_T_graph_z, raw_T_zrecon, raw_T_zgamma
        cov = LedoitWolf().fit(all_graph_z[fit_mask_T])
        zlatent = cov.mahalanobis(all_graph_z)
        med_r, mad_r = median_mad(all_zrecon[fit_mask_T])
        med_l, mad_l = median_mad(zlatent[fit_mask_T])
        med_g, mad_g = median_mad(all_zgamma[fit_mask_T])
        zr = (all_zrecon - med_r) / mad_r
        zl = (zlatent - med_l) / mad_l
        zg = (all_zgamma - med_g) / mad_g
        ens_T = ER.build_ensemble_subset({"zrecon": zr, "zlatent": zl, "zgamma": zg},
                                         ER.CANDIDATES["rlg"]).astype(np.float64)
        ens_T[is_signal_loss] = 0.0   # Amendment A2
        np.save(tpath, ens_T.astype(np.float32))
        log(f"{log_tag_prefix}2", f"{subj}: Scope T done ({len(ens_T)} windows, "
                                  f"background={int(background_mask.sum())}, "
                                  f"signal_loss={int(is_signal_loss.sum())})")

    # ---- Pass 2 (only if Scope W needed; one file in RAM at a time): subject-wide
    #      unmasked stats finalized from Pass 1's accumulators, then re-filter + score ----
    if need_W:
        window_len = P.WIN_SAMPLES
        count = n_windows_total * window_len
        ch_mean_W = np.concatenate(sum_parts, axis=0).sum(axis=0) / count
        ch_meansq_W = np.concatenate(sumsq_parts, axis=0).sum(axis=0) / count
        del sum_parts, sumsq_parts
        ch_var_W = np.maximum(ch_meansq_W - ch_mean_W * ch_mean_W, 0.0)
        ch_std_W = np.sqrt(ch_var_W)
        ch_std_W = np.where(ch_std_W > 0, ch_std_W, 1.0)

        raw_W_zrecon, raw_W_graph_z, raw_W_zgamma = [], [], []
        for edf in edfs:
            filtered, _ = filter_file(edf_path(subj, edf["fname"]))
            comp = score_file_chunked(filtered, ch_mean_W, ch_std_W, model, gamma_b, gamma_a)
            raw_W_zrecon.append(comp["zrecon_raw"])
            raw_W_graph_z.append(comp["graph_z"])
            raw_W_zgamma.append(comp["zgamma_raw"])
            del filtered, comp
            gc.collect()
            log(f"{log_tag_prefix}1", f"{subj}/{edf['fname']}: pass2 (Scope W) done "
                                      f"rss={rss_mb():.0f}MB sys_avail={sys_avail_mb():.0f}MB")

        all_graph_z = np.concatenate(raw_W_graph_z, axis=0)
        all_zrecon = np.concatenate(raw_W_zrecon)
        all_zgamma = np.concatenate(raw_W_zgamma)
        cov = LedoitWolf().fit(all_graph_z[fit_mask_W])
        zlatent = cov.mahalanobis(all_graph_z)
        med_r, mad_r = median_mad(all_zrecon[fit_mask_W])
        med_l, mad_l = median_mad(zlatent[fit_mask_W])
        med_g, mad_g = median_mad(all_zgamma[fit_mask_W])
        zr = (all_zrecon - med_r) / mad_r
        zl = (zlatent - med_l) / mad_l
        zg = (all_zgamma - med_g) / mad_g
        ens_W = ER.build_ensemble_subset({"zrecon": zr, "zlatent": zl, "zgamma": zg},
                                         ER.CANDIDATES["rlg"]).astype(np.float64)
        ens_W[is_signal_loss] = 0.0   # Amendment A2
        np.save(wpath, ens_W.astype(np.float32))
        log(f"{log_tag_prefix}1", f"{subj}: Scope W done ({len(ens_W)} windows, "
                                  f"signal_loss={int(is_signal_loss.sum())})")

    log(f"{log_tag_prefix}2", f"{subj}: subject total {time.time()-t0:.1f}s")


def run_score_stage(subjects, force=False):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for subj in subjects:
        process_subject(subj, force=force)


def subject_hours(subj):
    return sum(e["duration_s"] for e in list_files(subj)) / 3600.0


def recompute_scope_t(subj):
    """Correction C1: rebuild Scope T's score cache using preprocessing.filter_window (locked
    thesis per-window filtering) for the scored signal, instead of filter_file()'s whole-file
    filtering. Reuses the cached artifact mask (is_ictal/is_buffer/is_artifact) UNCHANGED --
    that mask already used filter_window (see compute_artifact_flags) and is not recomputed
    here. Streams one file's per-window-filtered array into the GAE/adjacency/gamma pass at a
    time (memory-bounded, same pattern as process_subject's Pass 1)."""
    t0 = time.time()
    (CACHE_DIR / "scores").mkdir(parents=True, exist_ok=True)
    tpath = scores_cache_path("T", subj)

    m = load_mask(subj)
    is_ictal, is_buffer, is_artifact = m["is_ictal"], m["is_buffer"], m["is_artifact"]
    is_signal_loss = m["is_signal_loss"]
    background_mask = (~is_ictal) & (~is_buffer) & (~is_artifact)
    fit_mask_T = background_mask & (~is_signal_loss)   # Amendment A2

    edfs = list_files(subj)
    fnames_sorted = [e["fname"] for e in edfs]
    stats = json.loads((PROCESSED_DIR / f"{subj}_stats.json").read_text())
    ch_mean_T = np.asarray(stats["ch_mean_uV"], dtype=np.float64) * 1e-6
    ch_std_T = np.asarray(stats["ch_std_uV"], dtype=np.float64) * 1e-6

    model = get_model()
    gamma_b, gamma_a = get_gamma_filter()

    raw_zrecon, raw_graph_z, raw_zgamma = [], [], []
    for f in fnames_sorted:
        filtered, n_windows = filter_file_per_window(edf_path(subj, f))
        comp = score_file_chunked(filtered, ch_mean_T, ch_std_T, model, gamma_b, gamma_a)
        raw_zrecon.append(comp["zrecon_raw"])
        raw_graph_z.append(comp["graph_z"])
        raw_zgamma.append(comp["zgamma_raw"])
        del filtered, comp
        gc.collect()
        log("G2", f"{subj}/{f}: Scope T (per-window filter, Correction C1) done "
                  f"rss={rss_mb():.0f}MB sys_avail={sys_avail_mb():.0f}MB")

    all_graph_z = np.concatenate(raw_graph_z, axis=0)
    all_zrecon = np.concatenate(raw_zrecon)
    all_zgamma = np.concatenate(raw_zgamma)
    del raw_graph_z, raw_zrecon, raw_zgamma
    if len(all_zrecon) != len(is_ictal):
        raise RuntimeError(f"{subj}: per-window-filtered window count ({len(all_zrecon)}) != "
                           f"cached mask length ({len(is_ictal)}) -- mask is stale for this file set")

    cov = LedoitWolf().fit(all_graph_z[fit_mask_T])
    zlatent = cov.mahalanobis(all_graph_z)
    med_r, mad_r = median_mad(all_zrecon[fit_mask_T])
    med_l, mad_l = median_mad(zlatent[fit_mask_T])
    med_g, mad_g = median_mad(all_zgamma[fit_mask_T])
    zr = (all_zrecon - med_r) / mad_r
    zl = (zlatent - med_l) / mad_l
    zg = (all_zgamma - med_g) / mad_g
    ens_T = ER.build_ensemble_subset({"zrecon": zr, "zlatent": zl, "zgamma": zg},
                                     ER.CANDIDATES["rlg"]).astype(np.float64)
    ens_T[is_signal_loss] = 0.0   # Amendment A2
    np.save(tpath, ens_T.astype(np.float32))
    elapsed = time.time() - t0
    log("G2", f"{subj}: Scope T (Correction C1 + Amendment A2) done ({len(ens_T)} windows, "
             f"background={int(background_mask.sum())}, "
             f"signal_loss={int(is_signal_loss.sum())}) in {elapsed:.1f}s")
    return elapsed


def c1_scores_cache_path(subj):
    return CACHE_DIR / "scores" / f"T_c1_{subj}.npy"


def recompute_scope_t_c1(subj):
    """Amendment A6 (docs/CC_PROMPT_CONTINUOUS_EVAL.md, 2026-10-01): reproduction-only Scope T
    recompute using the literal Correction C1 fit -- background_mask, signal-loss windows
    INCLUDED in the robust-z median/MAD and LedoitWolf fits, exactly as the committed offline
    arrays were fitted. Used only to gate G2 for a subject with flagged windows (chb17); never
    used for Steps A/B/C, which stay on the Amendment-A2-fitted cache. Written to a separate
    cache path (c1_scores_cache_path) -- never overwrites scores_cache_path('T', subj)."""
    t0 = time.time()
    (CACHE_DIR / "scores").mkdir(parents=True, exist_ok=True)
    cpath = c1_scores_cache_path(subj)

    m = load_mask(subj)
    is_ictal, is_buffer, is_artifact = m["is_ictal"], m["is_buffer"], m["is_artifact"]
    background_mask = (~is_ictal) & (~is_buffer) & (~is_artifact)

    edfs = list_files(subj)
    fnames_sorted = [e["fname"] for e in edfs]
    stats = json.loads((PROCESSED_DIR / f"{subj}_stats.json").read_text())
    ch_mean_T = np.asarray(stats["ch_mean_uV"], dtype=np.float64) * 1e-6
    ch_std_T = np.asarray(stats["ch_std_uV"], dtype=np.float64) * 1e-6

    model = get_model()
    gamma_b, gamma_a = get_gamma_filter()

    raw_zrecon, raw_graph_z, raw_zgamma = [], [], []
    for f in fnames_sorted:
        filtered, n_windows = filter_file_per_window(edf_path(subj, f))
        comp = score_file_chunked(filtered, ch_mean_T, ch_std_T, model, gamma_b, gamma_a)
        raw_zrecon.append(comp["zrecon_raw"])
        raw_graph_z.append(comp["graph_z"])
        raw_zgamma.append(comp["zgamma_raw"])
        del filtered, comp
        gc.collect()
        log("G2", f"{subj}/{f}: Scope T (Correction C1 fit, Amendment A6 reproduction) done "
                  f"rss={rss_mb():.0f}MB sys_avail={sys_avail_mb():.0f}MB")

    all_graph_z = np.concatenate(raw_graph_z, axis=0)
    all_zrecon = np.concatenate(raw_zrecon)
    all_zgamma = np.concatenate(raw_zgamma)
    del raw_graph_z, raw_zrecon, raw_zgamma
    if len(all_zrecon) != len(is_ictal):
        raise RuntimeError(f"{subj}: per-window-filtered window count ({len(all_zrecon)}) != "
                           f"cached mask length ({len(is_ictal)}) -- mask is stale for this file set")

    cov = LedoitWolf().fit(all_graph_z[background_mask])
    zlatent = cov.mahalanobis(all_graph_z)
    med_r, mad_r = median_mad(all_zrecon[background_mask])
    med_l, mad_l = median_mad(zlatent[background_mask])
    med_g, mad_g = median_mad(all_zgamma[background_mask])
    zr = (all_zrecon - med_r) / mad_r
    zl = (zlatent - med_l) / mad_l
    zg = (all_zgamma - med_g) / mad_g
    ens_T = ER.build_ensemble_subset({"zrecon": zr, "zlatent": zl, "zgamma": zg},
                                     ER.CANDIDATES["rlg"])
    np.save(cpath, ens_T.astype(np.float32))
    elapsed = time.time() - t0
    log("G2", f"{subj}: Scope T (Correction C1 fit, Amendment A6) done ({len(ens_T)} windows, "
             f"background={int(background_mask.sum())}) in {elapsed:.1f}s -> {cpath}")
    return elapsed


def run_rescore_t_stage(subjects):
    """Driver for Correction C1: discard old whole-file-filtered Scope T cache (done by the
    caller before this runs), recompute each subject's Scope T with filter_file_per_window,
    one subject at a time, printing an ETA after the first subject finishes."""
    total_hours = sum(subject_hours(s) for s in subjects)
    hours_done = 0.0
    t_start = time.time()
    for i, subj in enumerate(subjects):
        h = subject_hours(subj)
        log("G2", f"Correction C1 rescore: starting {subj} ({h:.1f} h, subject {i+1}/{len(subjects)})")
        elapsed = recompute_scope_t(subj)
        hours_done += h
        if i == 0:
            rate_s_per_h = elapsed / h if h > 0 else float("nan")
            remaining_h = total_hours - hours_done
            eta_s = rate_s_per_h * remaining_h
            eta_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + eta_s))
            log("G2", f"Correction C1 rescore: {subj} took {elapsed:.1f}s for {h:.1f}h "
                      f"({rate_s_per_h:.1f}s/h) -- estimated finish for remaining "
                      f"{remaining_h:.1f}h across {len(subjects)-1} subjects: {eta_str} "
                      f"(+{eta_s/60:.1f} min from now)")
    log("G2", f"Correction C1 rescore: all {len(subjects)} subjects done in "
             f"{time.time()-t_start:.1f}s ({(time.time()-t_start)/60:.1f} min)")


# ── Amendment A2 (docs/CC_PROMPT_CONTINUOUS_EVAL.md, 2026-10-01): backfill the signal-loss
#    flag into every subject's already-cached mask (is_ictal/is_buffer/is_artifact/spans/
#    sz_ranges untouched -- those came from a separate, unrelated raw pass and are not
#    recomputed here), then refit Scope T and Scope W excluding flagged windows. ──────────────
def backfill_signal_loss(subjects):
    """Computes is_signal_loss for every window of every subject directly from the raw EDF
    (one window read at a time via compute_signal_loss_flags, bounded memory), reusing each
    subject's cached spans so file boundaries line up exactly with the existing mask. Rewrites
    cache/mask/{subj}.npz with is_signal_loss added; every other cached field is carried over
    unchanged. Writes results/continuous_eval/signal_loss.csv (per-subject flagged window
    count and the hours it removes from the FA/day denominator)."""
    rows = []
    for subj in subjects:
        z = np.load(mask_cache_path(subj), allow_pickle=True)
        is_ictal = z["is_ictal"]; is_buffer = z["is_buffer"]; is_artifact = z["is_artifact"]
        spans = [tuple(x) for x in z["spans"]]
        sz_ranges = z["sz_ranges"]

        flags_parts = []
        for (fname, s, e) in spans:
            raw = P.open_edf(edf_path(subj, fname))
            flags = compute_signal_loss_flags(raw, e - s)
            del raw
            flags_parts.append(flags)
            n_f = int(flags.sum())
            if n_f:
                log("A2", f"{subj}/{fname}: {n_f}/{e-s} windows flagged signal-loss")
        is_signal_loss = np.concatenate(flags_parts)
        if len(is_signal_loss) != len(is_ictal):
            raise RuntimeError(f"{subj}: signal-loss window count ({len(is_signal_loss)}) != "
                               f"cached mask length ({len(is_ictal)})")

        np.savez(mask_cache_path(subj), is_ictal=is_ictal, is_buffer=is_buffer,
                 is_artifact=is_artifact, is_signal_loss=is_signal_loss,
                 spans=np.array(spans, dtype=object), sz_ranges=sz_ranges)

        n_flagged = int(is_signal_loss.sum())
        excluded_h = float((is_signal_loss & (~is_ictal)).sum()) * WIN_SEC / 3600.0
        rows.append(dict(subject=subj, n_windows=len(is_signal_loss), n_flagged=n_flagged,
                         flagged_pct=round(100.0 * n_flagged / len(is_signal_loss), 4),
                         excluded_hours=round(excluded_h, 4)))
        log("A2", f"{subj}: {n_flagged}/{len(is_signal_loss)} windows flagged signal-loss "
                 f"({excluded_h:.3f} h excluded from the FA/day denominator)")

    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "signal_loss.csv", index=False)
    log("A2", f"signal_loss.csv written: {int(df.n_flagged.sum())} flagged windows total "
             f"across {len(subjects)} subjects")
    return df


def recompute_scope_w(subj):
    """Rebuilds Scope W's score cache (whole-file filter_file, the application's own
    convention) with signal-loss windows excluded from the robust-z median/MAD and LedoitWolf
    fits (fit_mask_W = ~is_signal_loss). Scope W's own channel z-score stats (ch_mean_W/
    ch_std_W) stay subject-wide and unmasked, exactly as before -- not one of the four fits
    Amendment A2 lists. Flagged windows get their fused score forced to 0 after fitting.
    Reuses the cached mask (is_signal_loss, backfilled by backfill_signal_loss) unchanged;
    same two-pass, one-file-in-RAM-at-a-time pattern as process_subject's own Scope W path."""
    t0 = time.time()
    (CACHE_DIR / "scores").mkdir(parents=True, exist_ok=True)
    wpath = scores_cache_path("W", subj)

    m = load_mask(subj)
    is_signal_loss = m["is_signal_loss"]
    edfs = list_files(subj)
    model = get_model()
    gamma_b, gamma_a = get_gamma_filter()

    sum_parts, sumsq_parts = [], []
    n_windows_total = 0
    for edf in edfs:
        filtered, n_windows = filter_file(edf_path(subj, edf["fname"]))
        n_windows_total += n_windows
        for s in range(0, n_windows, CHUNK_WINDOWS):
            e = min(s + CHUNK_WINDOWS, n_windows)
            f64 = filtered[s:e].astype(np.float64)
            sum_parts.append(f64.sum(axis=2))
            sumsq_parts.append((f64 * f64).sum(axis=2))
            del f64
        del filtered
        gc.collect()
        log("G1", f"{subj}/{edf['fname']}: A2 rescore W pass1 {n_windows} windows "
                  f"rss={rss_mb():.0f}MB sys_avail={sys_avail_mb():.0f}MB")

    window_len = P.WIN_SAMPLES
    count = n_windows_total * window_len
    ch_mean_W = np.concatenate(sum_parts, axis=0).sum(axis=0) / count
    ch_meansq_W = np.concatenate(sumsq_parts, axis=0).sum(axis=0) / count
    del sum_parts, sumsq_parts
    ch_var_W = np.maximum(ch_meansq_W - ch_mean_W * ch_mean_W, 0.0)
    ch_std_W = np.sqrt(ch_var_W)
    ch_std_W = np.where(ch_std_W > 0, ch_std_W, 1.0)

    raw_zrecon, raw_graph_z, raw_zgamma = [], [], []
    for edf in edfs:
        filtered, _ = filter_file(edf_path(subj, edf["fname"]))
        comp = score_file_chunked(filtered, ch_mean_W, ch_std_W, model, gamma_b, gamma_a)
        raw_zrecon.append(comp["zrecon_raw"]); raw_graph_z.append(comp["graph_z"])
        raw_zgamma.append(comp["zgamma_raw"])
        del filtered, comp
        gc.collect()
        log("G1", f"{subj}/{edf['fname']}: A2 rescore W pass2 done "
                  f"rss={rss_mb():.0f}MB sys_avail={sys_avail_mb():.0f}MB")

    all_graph_z = np.concatenate(raw_graph_z, axis=0)
    all_zrecon = np.concatenate(raw_zrecon)
    all_zgamma = np.concatenate(raw_zgamma)
    if len(all_zrecon) != len(is_signal_loss):
        raise RuntimeError(f"{subj}: W window count ({len(all_zrecon)}) != cached mask length "
                           f"({len(is_signal_loss)}) -- mask is stale for this file set")

    fit_mask_W = ~is_signal_loss
    cov = LedoitWolf().fit(all_graph_z[fit_mask_W])
    zlatent = cov.mahalanobis(all_graph_z)
    med_r, mad_r = median_mad(all_zrecon[fit_mask_W])
    med_l, mad_l = median_mad(zlatent[fit_mask_W])
    med_g, mad_g = median_mad(all_zgamma[fit_mask_W])
    zr = (all_zrecon - med_r) / mad_r
    zl = (zlatent - med_l) / mad_l
    zg = (all_zgamma - med_g) / mad_g
    ens_W = ER.build_ensemble_subset({"zrecon": zr, "zlatent": zl, "zgamma": zg},
                                     ER.CANDIDATES["rlg"]).astype(np.float64)
    ens_W[is_signal_loss] = 0.0
    np.save(wpath, ens_W.astype(np.float32))
    elapsed = time.time() - t0
    log("G1", f"{subj}: Scope W (Amendment A2) done ({len(ens_W)} windows, "
             f"signal_loss={int(is_signal_loss.sum())}) in {elapsed:.1f}s")
    return elapsed


def run_rescore_w_stage(subjects):
    """Driver for Amendment A2's Scope W refit, mirroring run_rescore_t_stage."""
    total_hours = sum(subject_hours(s) for s in subjects)
    hours_done = 0.0
    t_start = time.time()
    for i, subj in enumerate(subjects):
        h = subject_hours(subj)
        log("G1", f"Amendment A2 rescore W: starting {subj} ({h:.1f} h, subject {i+1}/{len(subjects)})")
        elapsed = recompute_scope_w(subj)
        hours_done += h
        if i == 0:
            rate_s_per_h = elapsed / h if h > 0 else float("nan")
            remaining_h = total_hours - hours_done
            eta_s = rate_s_per_h * remaining_h
            eta_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + eta_s))
            log("G1", f"Amendment A2 rescore W: {subj} took {elapsed:.1f}s for {h:.1f}h "
                      f"({rate_s_per_h:.1f}s/h) -- estimated finish for remaining "
                      f"{remaining_h:.1f}h across {len(subjects)-1} subjects: {eta_str} "
                      f"(+{eta_s/60:.1f} min from now)")
    log("G1", f"Amendment A2 rescore W: all {len(subjects)} subjects done in "
             f"{time.time()-t_start:.1f}s ({(time.time()-t_start)/60:.1f} min)")


# ── Gates ─────────────────────────────────────────────────────────────────────
def gate_g1():
    """Scope W continuous fused scores reproduce the application's {stem}.score.npy on all
    231 test files: Pearson >= 0.999 per file."""
    rows = []
    for subj in TEST_SUBJS:
        ens_W = np.load(scores_cache_path("W", subj))
        mask = load_mask(subj)
        for (fname, s, e) in mask["spans"]:
            app_path = UPLOADS_DIR / subj / f"{Path(fname).stem}.score.npy"
            app = np.load(app_path)
            mine = ens_W[s:e]
            if len(app) != len(mine):
                r = float("nan")
            else:
                r, _ = pearsonr(app, mine)
            rows.append(dict(subject=subj, fname=fname, n=e - s, pearson_r=round(float(r), 6)))
            log("G1", f"{subj}/{fname}: r={r:.6f}")
    df = pd.DataFrame(rows)
    passed = bool((df.pearson_r >= 0.999).all())
    df.to_csv(OUT_DIR / "g1_pearson.csv", index=False)
    log("G1", f"G1 {'PASS' if passed else 'FAIL'} -- min r = {df.pearson_r.min():.6f}, "
              f"{(df.pearson_r < 0.999).sum()} file(s) below 0.999")
    return passed, df


def gate_g2():
    """Scope T scores at the retained interictal and ictal windows rank-match the committed
    offline arrays (Spearman >= 0.99 per patient, counts equal).

    Amendment A2: counts/match are judged on the FULL retained sets (unaffected by signal-loss
    -- the flag changes no window's ictal/background membership), but the Spearman correlation
    is computed only on windows not flagged signal-loss. mine_* and off_* share the same window
    order and length whenever counts match, so the same positional subset (is_signal_loss
    restricted to is_ictal / background, in that same order) is dropped from BOTH arrays --
    the score of a flagged window is numerically undefined in both computations, not just
    this run's own. The number of windows dropped this way is reported per subject.

    Amendment A6: the committed offline arrays were fitted with signal-loss windows INCLUDED,
    so for a subject with any flagged window (gated by c1_scores_cache_path existing -- chb17),
    G2 itself is evaluated on the Correction C1 fit (recompute_scope_t_c1's cache), not the
    Amendment-A2 fit, over the same windows-not-flagged comparison -- a true reproduction
    check. The Amendment-A2-fitted agreement is still computed and reported beside it
    (rho_*_a2 columns) as the effect of A2, not used to gate. A subject with no flagged window
    has no C1-specific cache, so its gate and its reported A2 value are identically the same
    computation -- G2 is unchanged for it."""
    ens_dir = ROOT / "results" / "phaseB" / "tier2" / "ens_test_tf" / "rlg"
    rows = []
    for subj in TEST_SUBJS:
        ens_a2 = np.load(scores_cache_path("T", subj))
        c1_path = c1_scores_cache_path(subj)
        has_c1 = c1_path.exists()
        ens_gate = np.load(c1_path) if has_c1 else ens_a2

        mask = load_mask(subj)
        is_ictal, is_buffer, is_artifact = mask["is_ictal"], mask["is_buffer"], mask["is_artifact"]
        is_signal_loss = mask["is_signal_loss"]
        background = (~is_ictal) & (~is_buffer) & (~is_artifact)

        mine_ictal_gate, mine_inter_gate = ens_gate[is_ictal], ens_gate[background]
        mine_ictal_a2, mine_inter_a2 = ens_a2[is_ictal], ens_a2[background]
        off_ictal = np.load(ens_dir / f"ens_seed42_{subj}_ictal.npy")
        off_inter = np.load(ens_dir / f"ens_seed42_{subj}_inter.npy")

        ictal_match = len(mine_ictal_gate) == len(off_ictal)
        inter_match = len(mine_inter_gate) == len(off_inter)
        m1 = min(len(mine_ictal_gate), len(off_ictal))
        m2 = min(len(mine_inter_gate), len(off_inter))

        sl_ictal = is_signal_loss[is_ictal][:m1]
        sl_inter = is_signal_loss[background][:m2]
        keep_ictal = ~sl_ictal
        keep_inter = ~sl_inter
        n_flagged_ictal = int(sl_ictal.sum())
        n_flagged_inter = int(sl_inter.sum())

        def _rho(mine, off, m, keep):
            a, b = mine[:m][keep], off[:m][keep]
            r, _ = spearmanr(a, b) if len(a) >= 2 else (float("nan"), None)
            return round(float(r), 4)

        rho_ictal = _rho(mine_ictal_gate, off_ictal, m1, keep_ictal)
        rho_inter = _rho(mine_inter_gate, off_inter, m2, keep_inter)
        rho_ictal_a2 = _rho(mine_ictal_a2, off_ictal, m1, keep_ictal) if has_c1 else rho_ictal
        rho_inter_a2 = _rho(mine_inter_a2, off_inter, m2, keep_inter) if has_c1 else rho_inter

        subj_pass = (ictal_match and inter_match and rho_ictal >= 0.99 and rho_inter >= 0.99)
        rows.append(dict(subject=subj, fit=("C1" if has_c1 else "A2"),
                         n_mine_ictal=len(mine_ictal_gate), n_off_ictal=len(off_ictal),
                         ictal_count_match=ictal_match, n_flagged_ictal=n_flagged_ictal,
                         rho_ictal=rho_ictal, rho_ictal_a2=rho_ictal_a2,
                         n_mine_inter=len(mine_inter_gate), n_off_inter=len(off_inter),
                         inter_count_match=inter_match, n_flagged_inter=n_flagged_inter,
                         rho_inter=rho_inter, rho_inter_a2=rho_inter_a2,
                         g2_pass=subj_pass))
        log("G2", f"{subj}: fit={'C1' if has_c1 else 'A2'} ictal {len(mine_ictal_gate)}/{len(off_ictal)} "
                  f"(flagged={n_flagged_ictal}) rho={rho_ictal:.4f} (A2={rho_ictal_a2:.4f}) | "
                  f"inter {len(mine_inter_gate)}/{len(off_inter)} (flagged={n_flagged_inter}) "
                  f"rho={rho_inter:.4f} (A2={rho_inter_a2:.4f}) -> {'PASS' if subj_pass else 'FAIL'}")
    df = pd.DataFrame(rows)
    passed = bool(df.g2_pass.all())
    df.to_csv(OUT_DIR / "g2_spearman.csv", index=False)
    log("G2", f"G2 {'PASS' if passed else 'FAIL'}")
    return passed, df


# ── change points -> merged events (byte-identical to cpd_pipeline_v14.detect_events's own
#    merge loop; separated out so PELT (pen_mult-only) can be fit once and reused across the
#    merge_s grid -- verified below in verify_fast_grid). No buffer don't-care exclusion: every
#    position on the continuous timeline can produce a false alarm. ─────────────────────────
def cps_to_merged_events(cps, win_sec, merge_s):
    times = sorted(c * win_sec for c in cps)
    events = []
    for t in times:
        if events and t - events[-1][1] <= merge_s:
            events[-1] = (events[-1][0], t + win_sec)
        else:
            events.append((t, t + win_sec))
    return events


def verify_fast_grid(subj="chb10"):
    """Verify the fast grid (one PELT fit per pen_mult, then merge_s/mag applied post-hoc)
    reproduces cpd_pipeline_v14.detect_events called directly, for one validation patient,
    scope T, at a couple of grid cells."""
    ens_T = np.load(scores_cache_path("T", subj))
    mask = load_mask(subj)
    background = ((~mask["is_ictal"]) & (~mask["is_buffer"]) & (~mask["is_artifact"])
                  & (~mask["is_signal_loss"]))
    smoothed = V14._smooth(np.asarray(ens_T, dtype=float))
    n = len(smoothed)
    s2 = V14._robust_variance(smoothed, background)
    algo = rpt.Pelt(model="l2", min_size=V14.PELT_MIN_SIZE, jump=V14.PELT_JUMP).fit(
        smoothed.reshape(-1, 1))
    for pen_mult in (0.5, 2.0):
        beta = pen_mult * s2 * np.log(n)
        cps_pen = [c for c in algo.predict(pen=beta) if 0 < c < n]
        for mag in (50.0, 65.0):
            mags = {c: V14._cp_magnitude(smoothed, c, 15) for c in cps_pen}
            bg = [m for c, m in mags.items() if background[c]]
            thr = float(np.percentile(bg, mag)) if bg else 0.0
            cps_fast = [c for c in cps_pen if mags[c] >= thr]
            for merge_s in (90, 300):
                ev_fast = cps_to_merged_events(cps_fast, WIN_SEC, merge_s)
                ev_direct = V14.detect_events(ens_T, pen_mult, min_mag_pct=mag, local_win=15,
                                              win_sec=WIN_SEC, inter_mask=background,
                                              merge_s=merge_s)
                assert ev_fast == ev_direct, (
                    f"fast-grid mismatch subj={subj} pen={pen_mult} mag={mag} merge={merge_s}: "
                    f"{len(ev_fast)} vs {len(ev_direct)} events")
    log("A", f"verify_fast_grid PASS on {subj} (4 cells x 2 merge_s, byte-identical to detect_events)")


def grid_for_subject(score, inter_mask, sz_ranges, mag_pcts, pen_mults, merge_gaps):
    """PELT once per pen_mult (Execution rule 3), magnitude + merge applied post-hoc.
    Returns list of dict(mag_pct, pen_mult, merge_s, hyp_events=[(onset_s,end_s),...])."""
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
        if inter_mask is not None and np.any(inter_mask):
            bg = [m for c, m in mags.items() if inter_mask[c]]
        else:
            bg = list(mags.values())
        for mag in mag_pcts:
            thr = float(np.percentile(bg, mag)) if bg else 0.0
            cps = [c for c in cps_pen if mags[c] >= thr]
            for ms in merge_gaps:
                out.append(dict(mag_pct=mag, pen_mult=pm, merge_s=ms,
                                hyp_events=cps_to_merged_events(cps, WIN_SEC, ms)))
    return out


def sz_ranges_to_seconds(sz_ranges, offset_windows):
    return [((s + offset_windows) * WIN_SEC, (e + offset_windows) * WIN_SEC) for (s, e) in sz_ranges]


# ── per-subject data for Steps A/B/C ────────────────────────────────────────
def load_subject_data(scope, subj):
    score = np.load(scores_cache_path(scope, subj))
    mask = load_mask(subj)
    is_ictal = mask["is_ictal"]
    is_signal_loss = mask["is_signal_loss"]
    n_windows = len(score)
    if scope == "T":
        inter_mask = (~is_ictal) & (~mask["is_buffer"]) & (~mask["is_artifact"]) & (~is_signal_loss)
    else:
        inter_mask = ~is_signal_loss   # Amendment A2: CPD variance/magnitude fit, both scopes
    ref_iv = [(s * WIN_SEC, e * WIN_SEC) for (s, e) in mask["sz_ranges"]]
    n_ictal_windows = int(is_ictal.sum())
    # Amendment A2: non-ictal signal-loss windows are excluded from the FA/day denominator;
    # excluded hours are reported per subject (also in results/continuous_eval/signal_loss.csv).
    noninter_h = int((~is_ictal & ~is_signal_loss).sum()) * WIN_SEC / 3600.0
    excluded_h = int((~is_ictal & is_signal_loss).sum()) * WIN_SEC / 3600.0
    total_dur_s = n_windows * WIN_SEC
    return dict(subject=subj, score=score, inter_mask=inter_mask, is_ictal=is_ictal,
                ref_iv=ref_iv, n_windows=n_windows, noninter_h=noninter_h,
                excluded_h=excluded_h, n_signal_loss=int(is_signal_loss.sum()),
                total_dur_s=total_dur_s, spans=mask["spans"])


def score_one_cell(data, hyp_events):
    sc = SE.score_szcore(data["ref_iv"], hyp_events, data["total_dur_s"], data["noninter_h"])
    lat = SE.matched_latency(data["ref_iv"], hyp_events)
    return dict(tp=sc["tp"], fp=sc["fp"], n_ref=sc["n_ref"], fn=sc["n_ref"] - sc["tp"],
               sensitivity=sc["sensitivity"], precision=sc["precision"], f1=sc["f1"],
               fp_per_day=sc["fp_per_day"], n_inter_h=data["noninter_h"], mean_lat_s=lat)


def pool_cells(cells):
    tp = sum(c["tp"] for c in cells); fp = sum(c["fp"] for c in cells)
    n_ref = sum(c["n_ref"] for c in cells); h = sum(c["n_inter_h"] for c in cells)
    sens = tp / n_ref if n_ref else float("nan")
    prec = tp / (tp + fp) if (tp + fp) else float("nan")
    f1 = 2 * prec * sens / (prec + sens) if (prec + sens) and prec == prec and sens == sens else float("nan")
    fa = fp / h * 24.0 if h else float("nan")
    return dict(tp=tp, fp=fp, n_ref=n_ref, fn=n_ref - tp, sensitivity=sens, precision=prec,
               f1=f1, fp_per_day=fa, n_inter_h=h)


def per_seizure_latencies(ref_iv, hyp_iv, tol_start=30, tol_end=60):
    lats = []
    for (r0, r1) in ref_iv:
        cands = [(h0, h1) for (h0, h1) in hyp_iv if h1 >= r0 - tol_start and h0 <= r1 + tol_end]
        if cands:
            h0 = min(cands, key=lambda h: abs(h[0] - r0))[0]
            lats.append(h0 - r0)
    return lats


def window_auroc_macro(scope, subjects):
    aucs = {}
    for subj in subjects:
        data = load_subject_data(scope, subj)
        y = data["is_ictal"].astype(int)
        if y.sum() == 0 or y.sum() == len(y):
            aucs[subj] = float("nan"); continue
        aucs[subj] = float(roc_auc_score(y, data["score"]))
    macro = float(np.nanmean(list(aucs.values())))
    return macro, aucs


# ── Step A: validation-patient grid search, operating-point selection ───────
# Amendment A3 (docs/CC_PROMPT_CONTINUOUS_EVAL.md): Scope W Steps A/B/C are dropped -- Scope W
# is gated by G1 only; its operating point and test result come from the application's own
# rerun, not this evaluation. Scope T only, below.
def run_step_a():
    scope = "T"
    val_data = {s: load_subject_data(scope, s) for s in VAL_SUBJS}
    per_subj_grids = {}
    for i, s in enumerate(VAL_SUBJS):
        d = val_data[s]
        t_grid0 = time.time()
        per_subj_grids[s] = grid_for_subject(d["score"], d["inter_mask"], None,
                                              MAG_PCTS, PEN_MULTS, MERGE_GAPS)
        grid_elapsed = time.time() - t_grid0
        log("A", f"scope {scope} {s}: grid done ({len(per_subj_grids[s])} cells) in {grid_elapsed:.1f}s")
        if i == 0:
            # Amendment A3: estimated finish time of Step B, extrapolated from this (the first
            # validation patient's) grid -- Step B fits PELT for only 2 operating points per
            # test subject (not the full len(PEN_MULTS)-penalty grid), so its PELT cost is
            # approximated as 2/len(PEN_MULTS) of one subject's full grid, times 8 test subjects.
            per_point_s = grid_elapsed / len(PEN_MULTS)
            step_b_eta_s = per_point_s * 2 * len(TEST_SUBJS)
            eta_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + step_b_eta_s))
            log("A", f"estimated Step B finish time (rough, extrapolated from this grid): "
                     f"{eta_str} (+{step_b_eta_s/60:.1f} min from now)")

    n_cells = len(per_subj_grids[VAL_SUBJS[0]])
    cell_rows = []
    for i in range(n_cells):
        mag = per_subj_grids[VAL_SUBJS[0]][i]["mag_pct"]
        pen = per_subj_grids[VAL_SUBJS[0]][i]["pen_mult"]
        ms = per_subj_grids[VAL_SUBJS[0]][i]["merge_s"]
        cells = []
        for s in VAL_SUBJS:
            cell = per_subj_grids[s][i]
            assert cell["mag_pct"] == mag and cell["pen_mult"] == pen and cell["merge_s"] == ms
            cells.append(score_one_cell(val_data[s], cell["hyp_events"]))
        pooled = pool_cells(cells)
        row = dict(scope=scope, mag_pct=mag, pen_mult=pen, merge_s=ms, **pooled)
        cell_rows.append(row)

    gdf = pd.DataFrame(cell_rows)
    gdf["abs_gap"] = (gdf.sensitivity - gdf.precision).abs()
    selected = gdf.loc[gdf.abs_gap.idxmin()].to_dict()

    fa_ok = gdf[gdf.fp_per_day <= 25.0]
    best_fa25 = (fa_ok.loc[fa_ok.sensitivity.idxmax()].to_dict()
                if len(fa_ok) else None)

    fixed_rows = gdf[(gdf.mag_pct == FIXED_MAG) & (gdf.pen_mult == FIXED_PEN) &
                     (gdf.merge_s == FIXED_MERGE)]
    fixed = fixed_rows.iloc[0].to_dict() if len(fixed_rows) else None

    result = {scope: dict(selected=selected, best_fa_le_25=best_fa25, fixed_50_2_0=fixed)}
    log("A", f"scope {scope}: selected mag={selected['mag_pct']} pen={selected['pen_mult']} "
             f"merge={selected['merge_s']} sens={selected['sensitivity']:.3f} "
             f"prec={selected['precision']:.3f} FA/day={selected['fp_per_day']:.2f}")

    pd.DataFrame(cell_rows).to_csv(OUT_DIR / "stepA_grid.csv", index=False)
    with open(OUT_DIR / "stepA_selected.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=float)
    return result


# ── Step B: test patients, Scope T only, at its selected point + 50/2.0/merge90. Each point
#    calls V14.detect_events directly (one PELT fit for that point's own pen_mult) -- Amendment
#    A3's "PELT only for the penalties those two points need", not the full PEN_MULTS grid. ──
def run_step_b(step_a_result):
    scope = "T"
    rows = []
    macro_auroc, _ = window_auroc_macro(scope, TEST_SUBJS)
    for label, mag, pen, ms in (
        ("selected", step_a_result[scope]["selected"]["mag_pct"],
         step_a_result[scope]["selected"]["pen_mult"],
         step_a_result[scope]["selected"]["merge_s"]),
        ("fixed_50_2.0", FIXED_MAG, FIXED_PEN, FIXED_MERGE),
    ):
        per_patient = []
        for subj in TEST_SUBJS:
            d = load_subject_data(scope, subj)
            ev = V14.detect_events(d["score"], pen, min_mag_pct=mag, local_win=15,
                                   win_sec=WIN_SEC, inter_mask=d["inter_mask"], merge_s=ms)
            cell = score_one_cell(d, ev)
            per_patient.append(dict(scope=scope, point=label, mag_pct=mag, pen_mult=pen,
                                    merge_s=ms, subject=subj, **cell))
        pooled = pool_cells(per_patient)
        rows.extend(per_patient)
        rows.append(dict(scope=scope, point=label, mag_pct=mag, pen_mult=pen, merge_s=ms,
                         subject="POOLED", window_auroc_macro=macro_auroc, **pooled))
        log("B", f"scope {scope} @ {label} (m{mag:g}/p{pen:g}/merge{ms}): "
                 f"pooled TP={pooled['tp']} FP={pooled['fp']} sens={pooled['sensitivity']:.3f} "
                 f"prec={pooled['precision']:.3f} FA/day={pooled['fp_per_day']:.2f} "
                 f"macroAUROC={macro_auroc:.3f}")
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "stepB.csv", index=False)
    return df


# ── Step C: results of record ────────────────────────────────────────────────
def run_step_c(step_a_result, step_b_df):
    # Amendment A3: Scope W Steps A/B/C are dropped -- Scope T only, results of record.
    tables = {}
    scope = "T"
    sel = step_a_result[scope]["selected"]
    mag, pen, ms = sel["mag_pct"], sel["pen_mult"], sel["merge_s"]
    per_patient = []
    all_lat = []
    for subj in TEST_SUBJS:
        d = load_subject_data(scope, subj)
        ev = V14.detect_events(d["score"], pen, min_mag_pct=mag, local_win=15,
                               win_sec=WIN_SEC, inter_mask=d["inter_mask"], merge_s=ms)
        cell = score_one_cell(d, ev)
        lats = per_seizure_latencies(d["ref_iv"], ev)
        all_lat.extend(lats)
        per_patient.append(dict(subject=subj, n_seizures=cell["n_ref"], detected=cell["tp"],
                                false_alarms=cell["fp"], sensitivity=round(cell["sensitivity"], 4),
                                precision=round(cell["precision"], 4), f1=round(cell["f1"], 4),
                                fp_per_day=round(cell["fp_per_day"], 3),
                                n_signal_loss=d["n_signal_loss"],
                                excluded_h=round(d["excluded_h"], 4)))
    pooled = pool_cells([score_one_cell(load_subject_data(scope, s),
                                        V14.detect_events(load_subject_data(scope, s)["score"], pen,
                                                          min_mag_pct=mag, local_win=15, win_sec=WIN_SEC,
                                                          inter_mask=load_subject_data(scope, s)["inter_mask"],
                                                          merge_s=ms))
                        for s in TEST_SUBJS])
    macro_auroc, per_subj_auroc = window_auroc_macro(scope, TEST_SUBJS)
    tables[scope] = dict(
        operating_point=dict(mag_pct=mag, pen_mult=pen, merge_s=ms),
        per_patient=per_patient, pooled=pooled,
        latency_s=dict(n=len(all_lat),
                       mean=float(np.mean(all_lat)) if all_lat else float("nan"),
                       median=float(np.median(all_lat)) if all_lat else float("nan"),
                       min=float(np.min(all_lat)) if all_lat else float("nan"),
                       max=float(np.max(all_lat)) if all_lat else float("nan"),
                       values=[round(v, 1) for v in all_lat]),
        window_auroc_macro=macro_auroc, window_auroc_per_subject=per_subj_auroc,
    )
    log("C", f"scope {scope} results-of-record: pooled sens={pooled['sensitivity']:.3f} "
             f"prec={pooled['precision']:.3f} FA/day={pooled['fp_per_day']:.2f} "
             f"macroAUROC={macro_auroc:.3f} n_latency={len(all_lat)}")

    # full post-hoc test grid, Scope T only, for the operating-curve figure
    full_rows = []
    grids = {s: grid_for_subject(load_subject_data("T", s)["score"], load_subject_data("T", s)["inter_mask"],
                                 None, MAG_PCTS, PEN_MULTS, MERGE_GAPS) for s in TEST_SUBJS}
    n_cells = len(grids[TEST_SUBJS[0]])
    for i in range(n_cells):
        mag = grids[TEST_SUBJS[0]][i]["mag_pct"]; pen = grids[TEST_SUBJS[0]][i]["pen_mult"]
        ms = grids[TEST_SUBJS[0]][i]["merge_s"]
        cells = [score_one_cell(load_subject_data("T", s), grids[s][i]["hyp_events"]) for s in TEST_SUBJS]
        pooled = pool_cells(cells)
        full_rows.append(dict(scope="T", mag_pct=mag, pen_mult=pen, merge_s=ms,
                              post_hoc=True, not_used_for_selection=True, **pooled))
    pd.DataFrame(full_rows).to_csv(OUT_DIR / "stepC_full_test_grid_scopeT.csv", index=False)
    log("C", f"full post-hoc TEST grid (Scope T, {len(full_rows)} cells) written -- "
             f"operating-curve figure only, not used for any selection")

    with open(OUT_DIR / "stepC_tables.json", "w", encoding="utf-8") as f:
        json.dump(tables, f, indent=2, default=float)
    return tables


# ── SUMMARY.md ────────────────────────────────────────────────────────────────
def write_readme():
    (OUT_DIR / "README.md").write_text(
        "# results/continuous_eval/ -- producing scripts\n\n"
        "- `step0.csv` <- `src/continuous_eval_step0.py`\n"
        "- everything else (`cache/`, `signal_loss.csv`, `g1_*.csv`, `g2_*.csv`, `stepA_*`, "
        "`stepB.csv`, `stepC_*`, `SUMMARY.md`) <- `src/continuous_eval.py` "
        "(docs/CC_PROMPT_CONTINUOUS_EVAL.md, Amendment A2)\n",
        encoding="utf-8")


def write_summary(g1_pass, g1_df, g2_pass, g2_df, step_a=None, step_b=None, step_c=None,
                  elapsed_s=None, stopped_at=None):
    lines = ["# Continuous-timeline evaluation -- SUMMARY", "",
            "docs/CC_PROMPT_CONTINUOUS_EVAL.md. Locked thesis pipeline, unchanged, run on the "
            "real continuous timeline (every window scored, files concatenated in file-name "
            "order), two fitting scopes (T = background-fitted, W = whole-recording-fitted).", ""]

    lines.append("## Gate G1 -- Scope W reproduces the application's own scores")
    lines.append("")
    lines.append(f"Per-file Pearson r >= 0.999 on all {len(g1_df)} test files. "
                f"min r = {g1_df.pearson_r.min():.6f}. **G1: {'PASS' if g1_pass else 'FAIL'}**")
    lines.append("")
    lines.append("G1 results per file, grouped by subject:")
    lines.append("")
    for subj in TEST_SUBJS:
        sub = g1_df[g1_df.subject == subj]
        if not len(sub):
            continue
        n_below = int((sub.pearson_r < 0.999).sum())
        lines.append(f"**{subj}** -- {len(sub)} files, min r = {sub.pearson_r.min():.6f}, "
                    f"{n_below} below 0.999:")
        lines.append(sub[["fname", "n", "pearson_r"]].to_string(index=False))
        lines.append("")

    lines.append("## Gate G2 -- Scope T rank-matches the committed offline arrays")
    lines.append("")
    lines.append("Amendment A6: `fit`/`rho_*` are the gating computation (Correction C1 fit, "
                "flagged windows included, for a subject with any flagged window -- chb17; "
                "otherwise identical to A2). `rho_*_a2` is the Amendment-A2-fitted agreement "
                "(flagged windows excluded from the fit), reported for information -- what "
                "Steps A/B/C actually use -- not used to gate. Both over windows not flagged.")
    lines.append("")
    lines.append(g2_df.to_string(index=False))
    lines.append("")
    lines.append(f"**G2: {'PASS' if g2_pass else 'FAIL'}**")
    lines.append("")

    if stopped_at:
        lines.append(f"**Stopped after {stopped_at} failed. Steps A/B/C not run.**")
        (OUT_DIR / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
        return

    lines.append("**Amendment A3 (before Step A): Scope W is computed through G1 only. Steps "
                "A, B and C below are Scope T only -- Scope W's operating point and test result "
                "come from the application's own rerun, not this script -- regardless of "
                "whether G1 passed (Amendment A1: G1 failing does not stop this run).**")
    lines.append("")

    lines.append("## Step A -- validation patients (chb10, chb11, chb22): selected operating point")
    lines.append("")
    sel = step_a["T"]["selected"]
    lines.append(f"Scope T: mag_pct={sel['mag_pct']:g} pen_mult={sel['pen_mult']:g} "
                f"merge_s={sel['merge_s']:g}  (sens={sel['sensitivity']:.3f} "
                f"prec={sel['precision']:.3f} |gap|={sel['abs_gap']:.4f} "
                f"FA/day={sel['fp_per_day']:.2f})")
    fa25 = step_a["T"]["best_fa_le_25"]
    lines.append(f"  best point with FA/day<=25 (info only): "
                f"{fa25 if fa25 is not None else 'none on the grid'}")
    fixed = step_a["T"]["fixed_50_2_0"]
    lines.append(f"  @ 50/2.0/merge90: sens={fixed['sensitivity']:.3f} "
                f"prec={fixed['precision']:.3f} FA/day={fixed['fp_per_day']:.2f}")
    lines.append("")

    lines.append("## Step B -- test patients at Scope T's selected point and at 50/2.0/merge90")
    lines.append("")
    lines.append(step_b[step_b.subject == "POOLED"].to_string(index=False))
    lines.append("")

    if step_c is None:
        lines.append("## Step C -- results of record")
        lines.append("")
        lines.append("Running (full post-hoc Scope T test grid for the operating-curve figure) "
                    "-- this file will be rewritten when it finishes.")
        lines.append("")
        if elapsed_s is not None:
            lines.append(f"Wall-clock time so far: {elapsed_s:.1f} s ({elapsed_s/3600:.2f} h).")
        (OUT_DIR / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
        return

    lines.append("## Step C -- results of record")
    lines.append("")
    lines.append("| row | sens | prec | F1 | FA/day | macro window AUROC |")
    lines.append("|---|---|---|---|---|---|")
    lines.append(f"| offline reconstructed (Table 9) | {D0A_TABLE9['sensitivity']} | "
                f"{D0A_TABLE9['precision']} | {D0A_TABLE9['f1']} | {D0A_TABLE9['fp_per_day']} | -- |")
    p = step_c["T"]["pooled"]
    op = step_c["T"]["operating_point"]
    lines.append(f"| Scope T continuous (m{op['mag_pct']:g}/p{op['pen_mult']:g}"
                f"/merge{op['merge_s']:g}) | {p['sensitivity']:.3f} | {p['precision']:.3f} | "
                f"{p['f1']:.3f} | {p['fp_per_day']:.2f} | "
                f"{step_c['T']['window_auroc_macro']:.3f} |")
    lines.append("")

    e1 = step_c["T"]["pooled"]["sensitivity"] < D0A_TABLE9["sensitivity"] and \
        step_c["T"]["pooled"]["fp_per_day"] > D0A_TABLE9["fp_per_day"]
    gap_offline_app = abs(D0A_TABLE9["sensitivity"] - 0.2105) + abs(D0A_TABLE9["fp_per_day"] - 52.4)

    # Amendment A3: Scope W's continuous number is no longer computed here -- E2 compares
    # Scope T against the application's own pooled result (results/application_eval/pooled.json)
    # instead, since that is now where Scope W's test result comes from.
    app_pooled_path = ROOT / "results" / "application_eval" / "pooled.json"
    e2 = None
    gap_t_app = None
    if app_pooled_path.exists():
        app = json.loads(app_pooled_path.read_text())
        gap_t_app = abs(step_c["T"]["pooled"]["sensitivity"] - app["sensitivity"]) + \
            abs(step_c["T"]["pooled"]["fp_per_day"] - app["false_alarms_per_day"])
        e2 = gap_t_app < gap_offline_app

    lines.append("## Pre-registered expectations")
    lines.append("")
    lines.append(f"E1 (Scope T sens < 0.618 and FA/day > 27.4): {'MET' if e1 else 'NOT MET'}")
    if e2 is None:
        lines.append("E2 (Scope T-W gap small vs. offline-application gap): not evaluated -- "
                    "results/application_eval/pooled.json not found (Amendment A3: Scope W's "
                    "test result comes from the application's own rerun).")
    else:
        lines.append(f"E2 (Scope T vs. application's own pooled result, gap small vs. "
                    f"offline-application gap): {'MET' if e2 else 'NOT MET'} "
                    f"(T-application gap={gap_t_app:.2f}, offline-application gap="
                    f"{gap_offline_app:.2f})")
    lines.append("")
    if elapsed_s is not None:
        lines.append(f"Wall-clock time: {elapsed_s:.1f} s ({elapsed_s/3600:.2f} h).")
    (OUT_DIR / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all",
                    choices=["score", "rescore_t", "a2", "a6", "gates", "abc", "stepc", "all"])
    ap.add_argument("--subjects", default=None, help="comma list; default = all 11")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--smoke", action="store_true", help="one validation file only")
    a = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    if a.smoke:
        edfs = list_files("chb10")
        f = edfs[0]["fname"]
        filtered, n_windows = filter_file(edf_path("chb10", f))
        log("SMOKE", f"chb10/{f}: filtered OK, {n_windows} windows, shape={filtered.shape}")
        model = get_model()
        gamma_b, gamma_a = get_gamma_filter()
        stats = json.loads((PROCESSED_DIR / "chb10_stats.json").read_text())
        ch_mean = np.asarray(stats["ch_mean_uV"], np.float64) * 1e-6
        ch_std = np.asarray(stats["ch_std_uV"], np.float64) * 1e-6
        zsc = zscore(filtered[:8], ch_mean, ch_std)
        comp = compute_window_components(zsc, model, gamma_b, gamma_a)
        log("SMOKE", f"components OK: zrecon={comp['zrecon_raw'][:3]} zgamma={comp['zgamma_raw'][:3]}")
        print("SMOKE PASS")
        return

    subjects = a.subjects.split(",") if a.subjects else ALL_SUBJS

    if a.stage in ("score", "all"):
        run_score_stage(subjects, force=a.force)

    if a.stage == "score":
        print(f"score stage done in {time.time()-t0:.1f}s")
        return

    if a.stage == "rescore_t":
        run_rescore_t_stage(subjects)
        print(f"rescore_t stage done in {time.time()-t0:.1f}s")
        return

    if a.stage == "a2":
        # Amendment A2 (docs/CC_PROMPT_CONTINUOUS_EVAL.md, 2026-10-01): backfill the
        # signal-loss flag for every subject, refit Scope T and Scope W excluding flagged
        # windows, then fall through into gates (and, if G2 passes, Steps A/B/C) below --
        # no waiting between steps.
        backfill_signal_loss(subjects)
        run_rescore_t_stage(subjects)
        run_rescore_w_stage(subjects)
        log("A2", f"Amendment A2 rescore done in {time.time()-t0:.1f}s -- continuing to gates")

    if a.stage == "a6":
        # Amendment A6: reproduction-only Correction C1 recompute (flagged windows included in
        # the fit) for every subject with any flagged window, used only to gate G2 -- Steps
        # A/B/C still use the Amendment-A2-fitted cache, untouched here.
        sl_df = pd.read_csv(OUT_DIR / "signal_loss.csv")
        flagged_subjs = sl_df[sl_df.n_flagged > 0].subject.tolist()
        for s in flagged_subjs:
            recompute_scope_t_c1(s)
        log("A6", f"Amendment A6 C1-fit reproduction recompute done for {flagged_subjs} in "
                 f"{time.time()-t0:.1f}s -- continuing to gates")

    if a.stage in ("gates", "abc", "all", "a2", "a6"):
        g1_pass, g1_df = gate_g1()
        g2_pass, g2_df = gate_g2()
        # Amendment A1 (docs/CC_PROMPT_CONTINUOUS_EVAL.md, 2026-09-30): G2 gates Scope T:
        # G2 failing stops the run, same as before. G1 gates Scope W only: G1 failing does
        # NOT stop the run -- Steps A/B/C proceed for Scope T in full; Scope W is still
        # computed and reported (write_summary puts it in a separate, clearly-labeled table)
        # but no Scope W operating point is proposed. Only G2 is a hard stop now.
        if not g2_pass:
            write_readme()
            write_summary(g1_pass, g1_df, g2_pass, g2_df, elapsed_s=time.time() - t0,
                         stopped_at="G2")
            print(f"STOPPED: gate G2 failed. See {OUT_DIR / 'SUMMARY.md'}")
            return
        if not g1_pass:
            print(f"G1 FAILED (Amendment A1: gates Scope W only) -- continuing with Scope T "
                 f"(gated by G2, which passed). Scope W will be computed and reported but not "
                 f"used to propose an operating point.")

    if a.stage == "gates":
        print(f"gates stage done in {time.time()-t0:.1f}s (G1 {'PASS' if g1_pass else 'FAIL'}, "
             f"G2 {'PASS' if g2_pass else 'FAIL'})")
        return

    if a.stage in ("abc", "all", "a2", "a6"):
        # Amendment A3 order: Step A -> Step B -> write SUMMARY.md immediately -> Step C (full
        # Scope T test grid for the curve) last. Amendment A4: after [SUMMARY] written, stop
        # and wait for an explicit instruction -- Step C runs separately via --stage stepc.
        verify_fast_grid("chb10")

        t_a0 = time.time()
        step_a = run_step_a()
        log("A", f"[A] done in {time.time()-t_a0:.1f}s")

        t_b0 = time.time()
        step_b = run_step_b(step_a)
        log("B", f"[B] done in {time.time()-t_b0:.1f}s")

        write_readme()
        write_summary(g1_pass, g1_df, g2_pass, g2_df, step_a, step_b, step_c=None,
                     elapsed_s=time.time() - t0)
        log("SUMMARY", f"[SUMMARY] written (gates + Step A + Step B; Step C pending) "
                       f"-> {OUT_DIR / 'SUMMARY.md'}")
        print(f"Amendment A4: stopping after [SUMMARY] written -- Step C not started. "
             f"Run with --stage stepc to continue. See {OUT_DIR / 'SUMMARY.md'}")
        return

    if a.stage == "stepc":
        # Amendment A4: the explicit instruction to run Step C, after [SUMMARY] written.
        g1_pass, g1_df = gate_g1()
        g2_pass, g2_df = gate_g2()
        with open(OUT_DIR / "stepA_selected.json", encoding="utf-8") as f:
            step_a = json.load(f)
        step_b = pd.read_csv(OUT_DIR / "stepB.csv")

        t_c0 = time.time()
        step_c = run_step_c(step_a, step_b)
        log("C", f"[C] done in {time.time()-t_c0:.1f}s")

        write_readme()
        write_summary(g1_pass, g1_df, g2_pass, g2_df, step_a, step_b, step_c,
                     elapsed_s=time.time() - t0)
        print(f"ALL DONE in {time.time()-t0:.1f}s "
             f"(G1 {'PASS' if g1_pass else 'FAIL -- Scope T only, Amendment A1'}). "
             f"See {OUT_DIR / 'SUMMARY.md'}")


if __name__ == "__main__":
    main()
