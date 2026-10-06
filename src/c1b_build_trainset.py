#!/usr/bin/env python
"""
c1b_build_trainset.py -- one consistent data source for the GAE v2 training (option C).

For every file of the 12 training and 3 validation subjects, on the application's own signal
path (continuous_eval.filter_file + z-scoring with the committed stats.json), per 4 s window:
  adj   [18,18] float16  CAR -> wPLI + AEC -> top-k 20 %   (unchanged graph, = GAE v1 input)
  bp5   [18,5]  float32  feature_extraction.compute_band_powers (unchanged, = GAE v1 input)
  f7    [18,7]  float32  ADDED node features, no per-window normalisation:
                         log band power x5 (Welch as compute_band_powers), log line length,
                         signed log1p excess kurtosis
  zgamma_raw     float32  gamma-AEC readout input, as continuous_eval.compute_window_components
  flags is_ictal, is_buffer (4 h post-seizure), is_flag5sd, is_signal_loss, file_idx
Two training variants are cut from this one set inside the training notebook:
  clean = not ictal, not buffer, not flagged, not signal loss   (the v1 definition)
  all   = not ictal, not buffer, not signal loss                (flagged windows included)
is_flag5sd uses the locked rule (any channel's peak |x| above its stats.json 5-SD threshold) on
the whole-file-filtered window; it only defines the 'clean' subset here and is never an
evaluation label. Seizure times come from the CHB-MIT summaries of TRAINING/VALIDATION subjects
only (training-data construction; the application never reads them).

  python src/c1b_build_trainset.py --smoke   # chb10, first file only
  python src/c1b_build_trainset.py           # all 15 subjects (resumable: finished ones skipped)
TEST GUARD: refuses every test subject. Writes only data/trainset_v2/.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.signal import welch
from scipy.stats import kurtosis

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "dataprep", ROOT / "src" / "phaseB",
          ROOT / "src" / "phaseC", ROOT / "src" / "retrain"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import continuous_eval as CE  # noqa: E402
import szcore_eval as SE      # noqa: E402

P = CE.P
SUBJS = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08", "chb09", "chb12",
         "chb19", "chb20", "chb21", "chb23", "chb10", "chb11", "chb22"]
assert not (set(SUBJS) & set(SE.TEST_SUBJS)), "TEST GUARD"
OUT = ROOT / "data" / "trainset_v2"
OUT.mkdir(parents=True, exist_ok=True)
FS = 256
BANDS = [(0.5, 4), (4, 8), (8, 13), (13, 30), (30, 60)]


def f7(W):
    """W [n,18,1024] z-scored -> [n,18,7]."""
    f, psd = welch(W, fs=FS, nperseg=FS * 2, noverlap=FS, axis=-1)
    out = np.empty(W.shape[:2] + (7,), dtype=np.float32)
    for i, (lo, hi) in enumerate(BANDS):
        idx = np.where((f >= lo) & (f <= hi))[0]
        out[..., i] = np.log(psd[..., idx].mean(axis=-1) + 1e-30)
    out[..., 5] = np.log(np.abs(np.diff(W, axis=-1)).mean(axis=-1) + 1e-30)
    k = kurtosis(W, axis=-1, fisher=True)
    out[..., 6] = np.sign(k) * np.log1p(np.abs(k))
    return out


def graph_and_bp(zw):
    n = zw.shape[0]
    adj = np.empty((n, 18, 18), dtype=np.float16)
    bp = np.empty((n, 18, 5), dtype=np.float32)
    for i in range(n):
        car = CE.GC.apply_car(zw[i])
        A = CE.GC.combine_adjacency(CE.GC.compute_wpli(car), CE.GC.compute_aec(car),
                                    alpha=CE.GC.DEFAULT_ALPHA)
        adj[i] = CE.GC.apply_topk_threshold(A, keep_ratio=CE.GC.DEFAULT_KEEP_RATIO).astype(np.float16)
        bp[i] = CE.FE.compute_band_powers(zw[i])
    return adj, bp


def build(subj, max_files=None):
    if subj in SE.TEST_SUBJS:
        raise SystemExit(f"TEST GUARD: {subj}")
    out = OUT / (f"{subj}_SMOKE.npz" if max_files else f"{subj}.npz")
    if out.exists():
        print(f"{subj}: exists, skip"); return
    t0 = time.time()
    stats = json.loads((CE.PROCESSED_DIR / f"{subj}_stats.json").read_text())
    mu = np.asarray(stats["ch_mean_uV"], dtype=np.float64) * 1e-6
    sd = np.asarray(stats["ch_std_uV"], dtype=np.float64) * 1e-6
    thr = np.asarray(stats["artifact_thresh_uV"], dtype=np.float64) * 1e-6
    edfs = CE.list_files(subj)
    if max_files:
        edfs = edfs[:max_files]
    gb, ga = CE.get_gamma_filter()
    parts = {k: [] for k in ("adj", "bp5", "f7", "zgamma_raw", "is_ictal", "is_buffer", "is_flag5sd",
                             "is_signal_loss", "file_idx")}
    kept, skipped = [], []
    for edf in edfs:
        try:
            filt, n = CE.filter_file(CE.edf_path(subj, edf["fname"]))
        except RuntimeError as ex:
            # same rule as the thesis preprocessing (preprocessing.open_edf returns None):
            # a file without all 18 common channels is skipped, never imputed
            if "missing one of the 18 common channels" in str(ex):
                skipped.append(edf["fname"])
                print(f"  {subj}/{edf['fname']}: SKIPPED (missing common channel)", flush=True)
                continue
            raise
        fi = len(kept)
        kept.append(edf["fname"])
        secs = n * CE.WIN_SEC
        lab = P.build_labels(secs, edf["seizures"]).reshape(n, CE.WIN_SEC).max(axis=1) == 1
        buf = P.build_buffer_mask(secs, edf["seizures"]).reshape(n, CE.WIN_SEC).any(axis=1)
        raw = P.open_edf(CE.edf_path(subj, edf["fname"]))
        sl = CE.compute_signal_loss_flags(raw, n)
        del raw
        flag = (np.abs(filt.astype(np.float64)).max(axis=2) > thr[None, :]).any(axis=1) & ~lab & ~buf
        for s in range(0, n, CE.CHUNK_WINDOWS):
            e = min(s + CE.CHUNK_WINDOWS, n)
            zw = CE.zscore(filt[s:e], mu, sd)
            a, b = graph_and_bp(zw)
            parts["adj"].append(a); parts["bp5"].append(b); parts["f7"].append(f7(zw))
            zf = zw.astype(np.float32)
            zg = np.empty(e - s, dtype=np.float32)
            for q in range(0, e - s, CE.GA.BATCH_SIZE):
                r = min(q + CE.GA.BATCH_SIZE, e - s)
                zg[q:r] = CE.GA.compute_gamma_scores_batch(zf[q:r], gb, ga)
            parts["zgamma_raw"].append(zg)
        parts["is_ictal"].append(lab); parts["is_buffer"].append(buf)
        parts["is_flag5sd"].append(flag); parts["is_signal_loss"].append(sl)
        parts["file_idx"].append(np.full(n, fi, dtype=np.int16))
        del filt
        print(f"  {subj}/{edf['fname']}: {n} windows, flagged {int(flag.sum())} "
              f"({time.time()-t0:.0f}s)", flush=True)
    data = {k: np.concatenate(v) for k, v in parts.items()}
    if not np.isfinite(data["f7"][~data["is_signal_loss"]]).all():
        raise SystemExit(f"{subj}: non-finite added features outside signal-loss windows")
    np.savez(out, files=np.array(kept, dtype=object),
             skipped_files=np.array(skipped, dtype=object), **data)
    n = len(data["is_ictal"])
    print(f"{subj}: {n} windows, ictal {int(data['is_ictal'].sum())}, flagged "
          f"{int(data['is_flag5sd'].sum())}, skipped files {skipped}, saved {out.name}, "
          f"{time.time()-t0:.0f}s", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--subjects", nargs="+", default=SUBJS)
    a = ap.parse_args()
    if a.smoke:
        build("chb10", max_files=1); return
    bad = set(a.subjects) - set(SUBJS)
    if bad:
        raise SystemExit(f"not a training/validation subject: {sorted(bad)}")
    T0 = time.time()
    for s in a.subjects:
        build(s)
    print(f"ALL DONE {time.time()-T0:.0f}s")


if __name__ == "__main__":
    main()
