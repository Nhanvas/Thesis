#!/usr/bin/env python
"""
c1_nodefeat.py -- step C1 of option C (augment the GAE node features; keep the GAE central).

Measured reason (src/dataprep/feature_extraction.py + src/retrain/train_gae_joint.py):
the current node features lose every trace of amplitude TWICE -- band powers are z-scored per
window across channels and bands, then min-max scaled per band across channels per window.
The GAE therefore cannot see how strong a channel is relative to the patient's own baseline,
which is the information that separated seizures from high-amplitude non-seizure windows
(raw_eeg_view Part 3; E5 vs E6 controlled comparison).

Added node features (6 per channel), computed on the stored per-subject z-scored windows
(data/processed/{subj}_interictal.npy), so they are already relative to the patient's baseline:
  5  log band power (delta, theta, alpha, beta, gamma), same Welch settings as
     feature_extraction.compute_band_powers, but WITHOUT the per-window normalisation
  1  log line length (mean |x[t+1]-x[t]|)
Standardisation follows Tang et al. (ICLR 2022, Appendix A): z-normalise with the mean and
standard deviation of the TRAINING data (12 training subjects, interictal), one constant per
feature, written to data/processed/nodefeat6_train_norm.json and applied at train and score time.

Outputs (raw, unstandardised, float32 [N, 18, 6]):
  data/processed/{subj}_interictal_nodefeat6.npy  for the 12 training + 3 validation subjects
  data/processed/{subj}_ictal_nodefeat6.npy       for the 3 validation subjects (sanity AUROC)
TEST GUARD: refuses every test subject.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.signal import welch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import szcore_eval as SE  # noqa: E402

PROC = ROOT / "data" / "processed"
TRAIN = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08", "chb09", "chb12",
         "chb19", "chb20", "chb21", "chb23"]
VAL = ["chb10", "chb11", "chb22"]
assert not (set(TRAIN + VAL) & set(SE.TEST_SUBJS)), "TEST GUARD"
FS = 256
BANDS = [(0.5, 4), (4, 8), (8, 13), (13, 30), (30, 60)]
CHUNK = 2000


def nodefeat6(W):
    """W: [n, 18, 1024] -> [n, 18, 6] float32 (log band power x5, log line length)."""
    f, psd = welch(W, fs=FS, nperseg=FS * 2, noverlap=FS, axis=-1)
    out = np.empty(W.shape[:2] + (6,), dtype=np.float32)
    for i, (lo, hi) in enumerate(BANDS):
        idx = np.where((f >= lo) & (f <= hi))[0]
        out[..., i] = np.log(psd[..., idx].mean(axis=-1) + 1e-30)
    out[..., 5] = np.log(np.abs(np.diff(W, axis=-1)).mean(axis=-1) + 1e-30)
    return out


def process(subj, label):
    src = PROC / f"{subj}_{label}.npy"
    dst = PROC / f"{subj}_{label}_nodefeat6.npy"
    if dst.exists():
        print(f"  {dst.name}: exists, skip"); return dst
    X = np.load(src, mmap_mode="r")
    if X.ndim != 3 or X.shape[1:] != (18, 1024):
        raise SystemExit(f"{src.name}: unexpected shape {X.shape}")
    mm = np.lib.format.open_memmap(str(dst), mode="w+", dtype=np.float32, shape=(X.shape[0], 18, 6))
    t0 = time.time()
    for s in range(0, X.shape[0], CHUNK):
        e = min(s + CHUNK, X.shape[0])
        mm[s:e] = nodefeat6(np.asarray(X[s:e], dtype=np.float64))
    mm.flush(); del mm
    print(f"  {dst.name}: {X.shape[0]} windows, {time.time()-t0:.0f}s", flush=True)
    return dst


def main():
    T0 = time.time()
    for s in TRAIN + VAL:
        process(s, "interictal")
    for s in VAL:
        process(s, "ictal")
    # training-set constants (12 training subjects, interictal, all channels pooled)
    n, s1, s2 = 0, np.zeros(6), np.zeros(6)
    for s in TRAIN:
        F = np.load(PROC / f"{s}_interictal_nodefeat6.npy", mmap_mode="r").reshape(-1, 6).astype(np.float64)
        if not np.isfinite(F).all():
            raise SystemExit(f"{s}: non-finite node features")
        n += len(F); s1 += F.sum(0); s2 += (F * F).sum(0)
    mu = s1 / n; sd = np.sqrt(np.maximum(s2 / n - mu * mu, 1e-12))
    norm = dict(features=["logbp_delta", "logbp_theta", "logbp_alpha", "logbp_beta", "logbp_gamma",
                          "log_linelen"], mean=mu.tolist(), std=sd.tolist(), n_rows=int(n),
                subjects=TRAIN)
    (PROC / "nodefeat6_train_norm.json").write_text(json.dumps(norm, indent=1))
    print("train norm:", {k: (round(m, 3), round(v, 3)) for k, m, v in zip(norm["features"], mu, sd)})
    # sanity: does the added information separate ictal from interictal on validation subjects?
    from sklearn.metrics import roc_auc_score
    for s in VAL:
        a = np.load(PROC / f"{s}_interictal_nodefeat6.npy", mmap_mode="r")
        b = np.load(PROC / f"{s}_ictal_nodefeat6.npy", mmap_mode="r")
        za, zb = ((np.asarray(a) - mu) / sd).mean(1), ((np.asarray(b) - mu) / sd).mean(1)
        y = np.r_[np.zeros(len(za)), np.ones(len(zb))]
        aucs = [roc_auc_score(y, np.r_[za[:, k], zb[:, k]]) for k in range(6)]
        print(f"  {s}: ictal vs interictal AUROC per feature (channel mean):", [round(x, 3) for x in aucs])
    print(f"DONE {time.time()-T0:.0f}s")


if __name__ == "__main__":
    main()
