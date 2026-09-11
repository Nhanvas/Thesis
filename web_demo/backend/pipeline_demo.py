"""
pipeline_demo.py — SzScan web demo's label-free, continuous re-implementation of the
locked thesis pipeline (`rlg`: zrecon + zlatent + zgamma, equal 1/3 weights).

Scope of this file (Step 1 of 9, see DEMO_BUILD_HANDOFF.md §6): `process_file()` only —
stage 1 of the two-stage architecture in SZSCAN_SPEC_v5.md §1.3. It runs the moment one
file finishes uploading and stops BEFORE change-point detection. `process_subject()`
(PELT + operating point) belongs to a later step and is not implemented here.

Read SZSCAN_SPEC_v5.md §1 before touching this file — it is the measured justification
for every divergence from the thesis pipeline below (see the two `# TODO(step3)` markers).

Never edit/copy the modules this file imports from (`src/dataprep/*`, `src/retrain/gae_joint.py`,
`src/ensemble_recipe.py`) — they are single-source, shared with the thesis. Read-only.
"""
import argparse
import hashlib
import sys
import time
from pathlib import Path

import numpy as np
import torch
from scipy.signal import sosfiltfilt, filtfilt
from sklearn.covariance import LedoitWolf

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

N_CH = len(preprocessing.COMMON_CHANNELS)  # 18

# ── Checkpoint identity — never trust the filename alone (CLAUDE.md "Model identity") ──
CHECKPOINT_PATH = REPO_ROOT / "data" / "models_retrain" / "gae_joint_seed42.pt"
CHECKPOINT_SHA256 = "dea06cb533df1c7d0520ae21c4cbb1b8a938297f937366bc9915b040726ea108"


def _verify_checkpoint(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {path}")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != CHECKPOINT_SHA256:
        raise RuntimeError(
            f"Checkpoint hash mismatch for {path}: expected {CHECKPOINT_SHA256}, got {actual}. "
            "Refusing to load an unverified checkpoint — see CLAUDE.md 'Model identity'."
        )


def _robust_z(x: np.ndarray) -> np.ndarray:
    """Median/MAD robust-z, fit on the whole input array. Mirrors retrain_io.robust_z's
    pooled-fit convention (SPEC §8 item O3 — confirmed not a divergence), written locally
    because retrain_io.robust_z takes two pre-split arrays and concatenates them, which
    doesn't fit this file's single continuous array."""
    med = np.median(x)
    mad = np.median(np.abs(x - med)) + 1e-9
    return (x - med) / mad


def process_file(edf_path: str, device: str = "cpu", timing: dict | None = None) -> np.ndarray:
    """Label-free continuous ensemble score for one EDF file, stopping before change-point
    detection. See SZSCAN_SPEC_v5.md §1.3 for the full pipeline diagram this implements.

    Parameters
    ----------
    timing : dict, optional
        If given, filled in-place with a wall-clock stage breakdown (seconds), used by the
        CLI to diagnose the gap vs. CLAUDE.md's ~15 s/hour estimate. Purely diagnostic --
        does not affect the returned score.

    Returns
    -------
    score : np.ndarray, shape [n_windows]
        Ensemble robust-z score, one value per non-overlapping 4 s window.
    """
    t_start = time.perf_counter()

    _verify_checkpoint(CHECKPOINT_PATH)
    model = gae_joint.load_checkpoint(CHECKPOINT_PATH, device)

    # 1. Open + channel select.
    raw = preprocessing.open_edf(edf_path)
    if raw is None:
        raise ValueError(
            f"{edf_path}: missing one or more of the 18 common channels "
            f"({preprocessing.COMMON_CHANNELS}) — refusing to silently drop this file."
        )

    n_windows = int(raw.n_times) // preprocessing.WIN_SAMPLES
    if n_windows == 0:
        raise ValueError(f"{edf_path}: shorter than one 4 s window — nothing to score.")

    # 2. Window + filter, NO artifact rejection (SPEC §1.6(a) drops it entirely so the
    #    window <-> second mapping stays exactly 1-to-1: t_seconds = window_index * 4).
    #
    # Filter the WHOLE continuous recording once (same filter objects preprocessing.py
    # builds at import time: _BP_SOS via sosfiltfilt, then _NOTCH_B/_NOTCH_A via filtfilt)
    # instead of calling preprocessing.filter_window() per window, which re-reads a padded
    # slice and re-runs both zero-phase filters on it 3600+ times per file. This is also
    # slightly MORE correct than the per-window version: filter_window()'s padding exists
    # only to suppress filtfilt edge-transients at every 4 s window boundary, whereas a
    # single continuous pass has edge effects solely at the true start/end of the file.
    t0 = time.perf_counter()
    data = raw.get_data()  # [18, n_total_samples], float64
    bp = sosfiltfilt(preprocessing._BP_SOS, data, axis=1)
    notched = filtfilt(preprocessing._NOTCH_B, preprocessing._NOTCH_A, bp, axis=1)
    usable = n_windows * preprocessing.WIN_SAMPLES
    filtered = np.ascontiguousarray(
        notched[:, :usable].reshape(N_CH, n_windows, preprocessing.WIN_SAMPLES).transpose(1, 0, 2)
    )
    t_windowing_filter = time.perf_counter() - t0

    # 3. Z-score per channel, stats fit on THIS FILE's windows.
    # TODO(step3): revisit once multi-file subject upload exists — z-scoring a file the moment
    # it finishes uploading is in tension with fitting stats across the whole subject if sibling
    # files are still uploading. SPEC says these stats should be fit on the whole subject; this
    # CLI test only has one file, so file-level == subject-level here.
    ch_mean = filtered.mean(axis=(0, 2))
    ch_std = filtered.std(axis=(0, 2))
    ch_std = np.where(ch_std > 0, ch_std, 1.0)
    zscored = (filtered - ch_mean[None, :, None]) / ch_std[None, :, None]

    # 4. Adjacency (top-k 20%, NOT graph_construction.build_adjacency's fixed threshold)
    #    + 5. Band powers, per window.
    t0 = time.perf_counter()
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
    t_adjacency_bandpower = time.perf_counter() - t0

    # 6. GAE forward -> zrecon (raw reconstruction MSE) + graph-level latent Z.
    t0 = time.perf_counter()
    A_t = torch.tensor(adjacency, dtype=torch.float32)
    X_t = torch.tensor(band_powers, dtype=torch.float32)
    pg, A_batch, Xn_batch, B = gae_joint.build_batch(A_t, X_t, device)

    model.eval()
    with torch.no_grad():
        z = model.encoder(pg.x, pg.edge_index, pg.edge_attr)
        graph_z = z.view(B, N_CH, gae_joint.LATENT_DIM).mean(dim=1)  # mirrors latent_anomaly.latent_pool
        zrecon_raw = gae_joint.joint_score(model, pg, A_batch, Xn_batch, B, per_node=False)

    zrecon_raw = zrecon_raw.cpu().numpy().astype(np.float64)
    graph_z_np = graph_z.cpu().numpy().astype(np.float64)
    t_gae_forward = time.perf_counter() - t0

    # 7. zlatent — LedoitWolf fit on THIS FILE's graph-level Z.
    # TODO(step3): same file-vs-subject caveat as the z-score TODO above — LedoitWolf should
    # eventually fit on the whole subject's Z, not one file's.
    cov = LedoitWolf().fit(graph_z_np)
    zlatent_raw = cov.mahalanobis(graph_z_np)

    # 8. zgamma — continuous, batched, on the z-scored windows (SPEC §8 item O5).
    t0 = time.perf_counter()
    gamma_b, gamma_a = compute_gamma_aec.make_gamma_filter()
    zgamma_raw = np.empty(n_windows, dtype=np.float32)
    zscored_f32 = zscored.astype(np.float32)
    for s in range(0, n_windows, compute_gamma_aec.BATCH_SIZE):
        e = min(s + compute_gamma_aec.BATCH_SIZE, n_windows)
        zgamma_raw[s:e] = compute_gamma_aec.compute_gamma_scores_batch(
            zscored_f32[s:e], gamma_b, gamma_a
        )
    t_zgamma = time.perf_counter() - t0

    # 9. Robust-z each branch, fit on the whole file's array for that branch.
    zr = _robust_z(zrecon_raw)
    zl = _robust_z(zlatent_raw)
    zg = _robust_z(zgamma_raw.astype(np.float64))

    # 10. Ensemble — reuse the single source (rlg subset, default equal weights).
    score = ensemble_recipe.build_ensemble_subset(
        {"zrecon": zr, "zlatent": zl, "zgamma": zg},
        subset=ensemble_recipe.CANDIDATES["rlg"],
    )

    t_total = time.perf_counter() - t_start
    if timing is not None:
        named = t_windowing_filter + t_adjacency_bandpower + t_gae_forward + t_zgamma
        timing["windowing_filter"] = t_windowing_filter
        timing["adjacency_bandpower"] = t_adjacency_bandpower
        timing["gae_forward"] = t_gae_forward
        timing["zgamma"] = t_zgamma
        # Everything not individually timed above: checkpoint verify + model load,
        # open_edf/channel select, per-channel z-score, LedoitWolf fit + mahalanobis,
        # robust-z, and the ensemble sum.
        timing["other"] = t_total - named
        timing["total"] = t_total

    return score.astype(np.float64)


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

    total_t = timing.get("total", elapsed_s)
    stage_names = [
        ("windowing + filter_window loop", "windowing_filter"),
        ("adjacency + band-power loop", "adjacency_bandpower"),
        ("GAE build_batch + forward (batched)", "gae_forward"),
        ("zgamma compute_gamma_scores_batch loop", "zgamma"),
        ("other (checkpoint verify, LedoitWolf, robust-z, ensemble, ...)", "other"),
    ]
    print("\nstage breakdown (wall-clock, measured inside process_file):")
    for label, key in stage_names:
        t = timing.get(key, float("nan"))
        pct = (100.0 * t / total_t) if total_t > 0 else float("nan")
        print(f"  {t:7.2f} s  ({pct:5.1f}%)  {label}")
    print(f"  {total_t:7.2f} s  (100.0%)  total")
