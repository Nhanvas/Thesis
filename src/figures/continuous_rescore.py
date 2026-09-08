"""
continuous_rescore.py -- shared recomputation module for Fig 2.10, Fig 3.4, Fig 3.10
(docs/FIGURE_ROUND4.md §3, "build by recomputation").

Recomputes the "rlg" ensemble anomaly score (zrecon + zlatent + zgamma, equal weights --
ensemble_recipe.CANDIDATES["rlg"]) on EVERY 4 s window of one continuous chb13 recording,
with NO artifact rejection, so t_seconds = window_index * 4 is a real, gap-free time axis.
This is the "approved deviation" of Round 4 §3: the committed score arrays cannot support a
time axis (segment-ordered, bootstrap-substituted, drift by the rejected-window count), so
these three figures recompute rather than read them.

FIXED (taken from committed files, never refit on the chosen recording):
  - checkpoint            data/models_retrain/gae_joint_seed42.pt
  - z-score stats         data/processed/chb13_stats.json (ch_mean_uV, ch_std_uV)
  - adjacency/feature construction: graph_construction.py / feature_extraction.py,
    unmodified (compute_wpli, compute_aec, combine_adjacency @ DEFAULT_ALPHA,
    apply_topk_threshold @ DEFAULT_KEEP_RATIO; compute_band_powers)
  - gamma AEC formula     compute_gamma_aec.compute_gamma_scores_batch, unmodified
  - robust-z calibration (median/MAD) and the latent-Mahalanobis covariance: fit ONCE on
    the committed data/processed/chb13_{interictal,ictal}_{adjs_topk20,features}.npy and
    gamma_aec_chb13_{inter,ictal}.npy arrays (the same data the study used), never refit on
    the newly scored recording. See fit_calibration() for exactly which basis each branch
    uses -- this is reported to the console so the choice is not silent.

RECOMPUTED (every window of the chosen file, artifact rejection dropped on purpose --
keeping every window is what gives a real, gap-free time axis):
  - bandpass + notch filtering (preprocessing.filter_window)
  - z-scoring against the committed chb13 stats
  - adjacency + band-power features
  - GAE reconstruction error, latent Mahalanobis distance, gamma AEC
  - equal-weight fused score = mean(zrecon, zlatent, zgamma)

Does NOT import szcore_eval.build_timeline_masked anywhere (forbidden by
docs/FIGURE_ROUND4.md §3.1 for these three figures) -- that function is what produces the
substituted timeline these figures exist to avoid.
"""
import os as _os, sys as _sys
from pathlib import Path
_here = _os.path.dirname(_os.path.abspath(__file__))
_src = _os.path.dirname(_here)
for _p in (_here, _src, str(Path(_src) / "dataprep"), str(Path(_src) / "retrain")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import json

import numpy as np
import torch
from scipy.signal import butter, filtfilt
from sklearn.covariance import LedoitWolf

import preprocessing as P
from graph_construction import (apply_car, compute_wpli, compute_aec, combine_adjacency,
                                apply_topk_threshold, DEFAULT_ALPHA, DEFAULT_KEEP_RATIO)
from feature_extraction import compute_band_powers
from compute_gamma_aec import make_gamma_filter, compute_gamma_scores_batch, GAMMA_LOW, GAMMA_HIGH
import gae_joint as G

ROOT = Path(_src).parent
PROC = ROOT / "data" / "processed"
CKPT = ROOT / "data" / "models_retrain" / "gae_joint_seed42.pt"
SUBJ = "chb13"
DEVICE = torch.device("cpu")


# ============================================================================
# Windowing a continuous recording -- no artifact rejection
# ============================================================================
def build_continuous_windows(edf_path, stats):
    """Every non-overlapping 4 s window of one EDF file: bandpass + notch
    (preprocessing.filter_window), z-scored with the committed chb13 stats. NO
    artifact rejection -- every window is kept, which is the entire point of these
    three figures (t_seconds = window_index * 4 is then a real, gap-free axis)."""
    raw = P.open_edf(Path(edf_path))
    if raw is None:
        raise RuntimeError(f"{edf_path}: missing one of the 18 common channels")
    n_samples = int(raw.n_times)
    n_windows = n_samples // P.WIN_SAMPLES
    ch_mean = np.asarray(stats["ch_mean_uV"], dtype=np.float64) * 1e-6
    ch_std = np.asarray(stats["ch_std_uV"], dtype=np.float64) * 1e-6

    windows = np.empty((n_windows, 18, P.WIN_SAMPLES), dtype=np.float32)
    for i in range(n_windows):
        start = i * P.WIN_SAMPLES
        end = start + P.WIN_SAMPLES
        w = P.filter_window(raw, start, end)
        w = (w - ch_mean[:, None]) / ch_std[:, None]
        windows[i] = w.astype(np.float32)
    return windows, n_windows


# ============================================================================
# Per-window raw component scores (recon MSE, gamma-band AEC, GAE latent Z)
# ============================================================================
def raw_recon_and_latent(model, windows, batch_size=512):
    """Returns (raw_recon [N], Z_pooled [N,16]) -- the GAE joint MSE score and the
    graph-mean-pooled 16-d latent, for every window. Adjacency/features are built
    fresh per window with the committed graph_construction.py / feature_extraction.py
    functions (the "adjacency trap" allowance already used by Fig 1.2/2.4/2.5:
    no committed adjacency array exists for arbitrary new windows, so it is
    legitimately rebuilt from the locked construction functions)."""
    n = len(windows)
    recon = np.empty(n, dtype=np.float32)
    Zpooled = np.empty((n, G.LATENT_DIM), dtype=np.float32)
    model.eval()
    with torch.no_grad():
        for s in range(0, n, batch_size):
            e = min(s + batch_size, n)
            batch = windows[s:e]
            A_batch = np.empty((e - s, 18, 18), dtype=np.float32)
            F_batch = np.empty((e - s, 18, 5), dtype=np.float32)
            for k, w in enumerate(batch):
                wc = apply_car(w.astype(np.float64))
                wpli = compute_wpli(wc, fs=P.FS)
                aec = compute_aec(wc)
                A = combine_adjacency(wpli, aec, alpha=DEFAULT_ALPHA)
                A_batch[k] = apply_topk_threshold(A, keep_ratio=DEFAULT_KEEP_RATIO)
                F_batch[k] = compute_band_powers(w.astype(np.float64))
            At = torch.tensor(A_batch); Ft = torch.tensor(F_batch)
            pg, Anrm, Xn, B = G.build_batch(At, Ft, DEVICE)
            sc = G.joint_score(model, pg, Anrm, Xn, B, per_node=False)
            recon[s:e] = sc.cpu().numpy().astype(np.float32)
            z = model.encoder(pg.x, pg.edge_index, pg.edge_attr).view(B, G.N_CH, G.LATENT_DIM)
            Zpooled[s:e] = z.mean(dim=1).cpu().numpy().astype(np.float32)
    return recon, Zpooled


def raw_gamma_stageA(windows, b, a):
    """compute_gamma_aec's own scoring formula (gamma-band filter -> Hilbert envelope
    -> log -> top-20% Pearson correlation), applied window-by-window in batches of 256
    exactly as compute_gamma_aec.process_subject does -- no reimplementation."""
    N = len(windows)
    out = np.empty(N, dtype=np.float32)
    for s in range(0, N, 256):
        e = min(s + 256, N)
        out[s:e] = compute_gamma_scores_batch(windows[s:e].astype(np.float32), b, a)
    return out


# ============================================================================
# Calibration: fit robust-z (median/MAD) and the latent covariance ONCE, on the
# committed data/processed arrays. Never refit on the chosen recording.
# ============================================================================
def fit_calibration(subj=SUBJ, verbose=True):
    model = G.load_checkpoint(str(CKPT), DEVICE)
    stats = json.loads((PROC / f"{subj}_stats.json").read_text())

    # ---- committed windows (inter = artifact-rejected 12,452; ictal = all 144) ----
    win_inter = np.load(PROC / f"{subj}_interictal.npy", mmap_mode="r")
    win_ictal = np.load(PROC / f"{subj}_ictal.npy", mmap_mode="r")
    adj_inter = np.load(PROC / f"{subj}_interictal_adjs_topk20.npy", mmap_mode="r")
    adj_ictal = np.load(PROC / f"{subj}_ictal_adjs_topk20.npy", mmap_mode="r")
    feat_inter = np.load(PROC / f"{subj}_interictal_features.npy", mmap_mode="r")
    feat_ictal = np.load(PROC / f"{subj}_ictal_features.npy", mmap_mode="r")
    gamma_inter = np.load(PROC / f"gamma_aec_{subj}_inter.npy")
    gamma_ictal = np.load(PROC / f"gamma_aec_{subj}_ictal.npy")

    # ---- zrecon: raw GAE MSE on the COMMITTED adjacency/feature arrays (not rebuilt
    # from raw windows -- these are the exact arrays the study scored), median/MAD
    # fit pooled inter+ictal (the pinned retrain_io.robust_z recipe). ----
    def score_from_committed(adj_path_arr, feat_path_arr):
        out = []
        model.eval()
        with torch.no_grad():
            for s in range(0, len(adj_path_arr), 512):
                e = min(s + 512, len(adj_path_arr))
                A = torch.tensor(np.asarray(adj_path_arr[s:e]).astype(np.float32))
                Xt = torch.tensor(np.asarray(feat_path_arr[s:e]).astype(np.float32))
                pg, Anrm, Xn, B = G.build_batch(A, Xt, DEVICE)
                sc = G.joint_score(model, pg, Anrm, Xn, B, per_node=False)
                out.append(sc.cpu().numpy().astype(np.float32))
        return np.concatenate(out, axis=0)

    recon_i = score_from_committed(adj_inter, feat_inter)
    recon_c = score_from_committed(adj_ictal, feat_ictal)
    recon_pool = np.concatenate([recon_i, recon_c])
    recon_med = float(np.median(recon_pool))
    recon_mad = float(np.median(np.abs(recon_pool - recon_med)) + 1e-9)

    # ---- zlatent: LedoitWolf covariance fit on committed INTERICTAL-only pooled Z
    # (the pinned build_ens_tier2.latent_component recipe: label-free, TEST-valid).
    # R4 §3.1: "load it if it is committed; if it is not, fit it on the committed
    # data/processed/chb13_interictal.npy array" -- no committed covariance object
    # exists anywhere in the repo (checked: no .pkl/.npy under results/ or data/
    # matching "cov" or "ledoitwolf"), so it is fit here, on that exact array. ----
    def pooled_Z(adj_arr, feat_arr):
        Z = []
        model.eval()
        with torch.no_grad():
            for s in range(0, len(adj_arr), 512):
                e = min(s + 512, len(adj_arr))
                A = torch.tensor(np.asarray(adj_arr[s:e]).astype(np.float32))
                Xt = torch.tensor(np.asarray(feat_arr[s:e]).astype(np.float32))
                pg, _, _, B = G.build_batch(A, Xt, DEVICE)
                z = model.encoder(pg.x, pg.edge_index, pg.edge_attr).view(B, G.N_CH, G.LATENT_DIM)
                Z.append(z.mean(dim=1).cpu().numpy().astype(np.float32))
        return np.concatenate(Z, 0)

    Zi = pooled_Z(adj_inter, feat_inter)
    Zc = pooled_Z(adj_ictal, feat_ictal)
    cov = LedoitWolf().fit(Zi)
    dist_i = cov.mahalanobis(Zi)
    dist_c = cov.mahalanobis(Zc)
    dist_pool = np.concatenate([dist_i, dist_c])
    latent_med = float(np.median(dist_pool))
    latent_mad = float(np.median(np.abs(dist_pool - latent_med)) + 1e-9)

    # ---- zgamma: TWO-stage robust_z, matching the committed on-disk recipe exactly.
    # Stage A (inside compute_gamma_aec.py, already applied to the committed
    # gamma_aec_{subj}_{inter,ictal}.npy files): raw gamma AEC -> median/MAD fit on
    # INTERICTAL raw scores only, applied to both splits. That stage-A median/MAD was
    # never saved, so it is recovered here by recomputing raw gamma AEC on the
    # committed chb13_interictal.npy array (same formula, same data).
    # Stage B (inside build_ens_tier2.rlg_components / retrain_io.robust_z): the
    # stage-A-normalised values (i.e. the committed gamma_aec_*.npy files themselves)
    # get a SECOND median/MAD, pooled inter+ictal -- this is what "zgamma" means in
    # the ensemble. ----
    b, a = make_gamma_filter()
    gamma_raw_inter = raw_gamma_stageA(win_inter, b, a)
    stageA_med = float(np.median(gamma_raw_inter))
    stageA_mad = float(np.median(np.abs(gamma_raw_inter - stageA_med)) + 1e-9)

    gamma_pool_stageB = np.concatenate([gamma_inter, gamma_ictal])
    stageB_med = float(np.median(gamma_pool_stageB))
    stageB_mad = float(np.median(np.abs(gamma_pool_stageB - stageB_med)) + 1e-9)

    if verbose:
        print(f"[calibration/{subj}] fit ONLY from committed files (never refit on the "
             f"chosen recording):")
        print(f"  zrecon : median/MAD fit on pooled committed "
             f"{subj}_{{interictal,ictal}}_adjs_topk20.npy + _features.npy "
             f"(n={len(recon_pool)}) -> med={recon_med:.6f} mad={recon_mad:.6f}")
        print(f"  zlatent: LedoitWolf covariance FIT on committed {subj}_interictal.npy "
             f"only (n={len(Zi)}, label-free) -- no committed covariance object exists "
             f"in the repo, so it was fit here per R4 §3.1's fallback instruction. "
             f"median/MAD of the Mahalanobis distance fit pooled inter+ictal (n="
             f"{len(dist_pool)}) -> med={latent_med:.6f} mad={latent_mad:.6f}")
        print(f"  zgamma : stage A (interictal-only) median/MAD recovered from committed "
             f"{subj}_interictal.npy (n={len(gamma_raw_inter)}) -> "
             f"med={stageA_med:.6f} mad={stageA_mad:.6f}; stage B (pooled, on the "
             f"committed gamma_aec_{subj}_{{inter,ictal}}.npy files themselves, n="
             f"{len(gamma_pool_stageB)}) -> med={stageB_med:.6f} mad={stageB_mad:.6f}")

    return dict(model=model, stats=stats, gamma_filter=(b, a),
               recon_med=recon_med, recon_mad=recon_mad,
               latent_cov=cov, latent_med=latent_med, latent_mad=latent_mad,
               gamma_stageA_med=stageA_med, gamma_stageA_mad=stageA_mad,
               gamma_stageB_med=stageB_med, gamma_stageB_mad=stageB_mad)


# ============================================================================
# Score one continuous recording end-to-end
# ============================================================================
def score_continuous_file(edf_path, calib):
    windows, n_windows = build_continuous_windows(edf_path, calib["stats"])
    t_seconds = np.arange(n_windows) * P.WIN_S

    raw_recon, Zpooled = raw_recon_and_latent(calib["model"], windows)
    zrecon = (raw_recon - calib["recon_med"]) / calib["recon_mad"]

    dist = calib["latent_cov"].mahalanobis(Zpooled.astype(np.float64))
    zlatent = (dist - calib["latent_med"]) / calib["latent_mad"]

    b, a = calib["gamma_filter"]
    raw_gamma = raw_gamma_stageA(windows, b, a)
    stageA = (raw_gamma - calib["gamma_stageA_med"]) / calib["gamma_stageA_mad"]
    zgamma = (stageA - calib["gamma_stageB_med"]) / calib["gamma_stageB_mad"]

    fused = (zrecon + zlatent + zgamma) / 3.0

    return dict(t_seconds=t_seconds, n_windows=n_windows,
               zrecon=zrecon.astype(np.float32), zlatent=zlatent.astype(np.float32),
               zgamma=zgamma.astype(np.float32), fused=fused.astype(np.float32),
               windows=windows)
