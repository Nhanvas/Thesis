#!/usr/bin/env python
"""
v9_x3_build_chb24.py -- V9-X3 prep (docs/prompts/V9_X3_CV_PREP.md): chb24 has no committed
data/processed/chb24_stats.json and no data/trainset_v2|testset_v2 array -- it was never part of
the original 23-subject split. V9-X3's fold rule puts chb24 in fold 3 (held out there) and
therefore a TRAINING subject for folds 1, 2 and 4, so its per-subject training array (adj, bp5,
f7, is_ictal, is_buffer, is_flag5sd, is_signal_loss, file_idx) must exist in the SAME format and
under the SAME convention as every other subject's array in data/trainset_v2|testset_v2:
preprocessing.compute_subject_stats (per-channel mean/std from subsampled interictal windows,
excluding ictal + the 4 h buffer) -> 5xSD artifact threshold -> c1b_build_trainset's own
per-window construction (CE.filter_file whole-file zero-phase filter, CE.zscore, graph_and_bp,
f7). This is DIFFERENT from results/v9_anatomy/xcache/chb24.npz (built by v9_anatomy.py /
x1_external.py with label-free stats -- every 10th window of the WHOLE recording, seizures
included, no committed stats.json needed -- the deliberate "true external deployment" condition
for V9-T3/V9-E1/V9-E4). That cache's adj/bp5/f7 are z-scored with different per-channel mu/sd and
are therefore NOT reusable for V9-X3 training/scoring, which must match train_gae_v2.py's own
input convention exactly. Read-only reuse, no frozen file edited: dataprep.preprocessing
(compute_subject_stats, build_labels, build_buffer_mask, open_edf, ARTIFACT_SD_MULTIPLIER),
continuous_eval (filter_file, compute_signal_loss_flags, edf_path, zscore, CHUNK_WINDOWS),
c1b_build_trainset (f7, graph_and_bp -- the exact per-window feature functions),
evaluation_protocol.parse_summary_edf_list.

chb24's own files: F:/Study/Thesis/Dataset/CHB-MIT/chb24 (22 EDFs + chb24-summary.txt; confirmed
present in full by v9_anatomy.py's own documented finding). Read directly from the dataset tree,
not copied into data/summaries/ or data/processed/ (outside this task's committed paths:
src/v9_x3_*.py, results/v9_x3/).

Output: results/v9_x3/chb24.npz -- same fields as data/trainset_v2/*.npz MINUS zgamma_raw (not
used by train_gae_v2.mask()/load_set() or by the frozen G-arm scoring chain -- v9_e1_baselines.py
member_mean_z_from_D / final_scalar_from_D consume only the per-channel GAE-latent distance D,
never zgamma_raw; omitting it avoids the extra gamma-filter pass). PLUS results/v9_x3/
chb24_stats.json, same shape as the committed data/processed/{subj}_stats.json.
Cross-check (printed, not a STOP): file list, per-file window count and is_ictal/is_signal_loss
agreement against results/v9_anatomy/xcache/chb24.npz, which used the SAME file set and the SAME
is_ictal/signal-loss logic (only the z-scoring differs) -- a mismatch would mean the file lists
have diverged and must be investigated before any fold uses this array.

Run:  python src/v9_x3_build_chb24.py --smoke   (chb24_01.edf only, ~1-2 min)
      python src/v9_x3_build_chb24.py           (all 22 files, not measured before this run)
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "dataprep", ROOT / "src" / "phaseB",
          ROOT / "src" / "phaseC", ROOT / "src" / "retrain"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import continuous_eval as CE          # noqa: E402
import preprocessing as P             # noqa: E402
import c1b_build_trainset as C1B      # noqa: E402

SUBJ = "chb24"
RAW_DIR = CE.DATASET_DIR               # F:/Study/Thesis/Dataset/CHB-MIT (env CHBMIT_DIR overrides)
SUMMARY_PATH = RAW_DIR / SUBJ / f"{SUBJ}-summary.txt"
OUT = ROOT / "results" / "v9_x3"
XCACHE = ROOT / "results" / "v9_anatomy" / "xcache" / f"{SUBJ}.npz"


def list_files_local():
    """CE.list_files reads via evaluation_protocol.parse_summary_edf_list, which requires a
    'File Start/End Time' header that chb24-summary.txt does NOT have (confirmed by inspection --
    unlike every other CHB-MIT subject's summary file); that parser silently returns 0 files for
    chb24. Use preprocessing.parse_summary instead (index-agnostic on Start/End Time lines, no
    header dependency -- the same parser x1_external.py's chb_subject() uses for chb24, for the
    same reason), restricted to EDFs actually present (same glob convention as
    continuous_eval.list_files / preprocessing.process_subject).

    SECOND chb24 quirk (found by a first run of this script: only 12 of the 22 present files were
    built): unlike every other CHB-MIT subject, chb24-summary.txt has a 'File Name:' entry ONLY
    for the 12 files that contain a seizure -- the 10 purely-interictal files have NO entry at
    all (not even 'Number of Seizures in File: 0'). v9_anatomy.py / x1_external.py already handle
    this correctly: they glob every present chb24_*.edf directly and look up seizures by filename
    (defaulting to none), never iterating the summary dict itself. Mirrored here."""
    sz = P.parse_summary(SUMMARY_PATH)                       # {fname: [(onset, offset), ...]}, seizure files only
    present = sorted(p.name for p in (RAW_DIR / SUBJ).glob("*.edf"))
    return [dict(fname=f, seizures=sz.get(f, [])) for f in present]


def build_stats():
    out = OUT / f"{SUBJ}_stats.json"
    if out.exists():
        print(f"{SUBJ}_stats.json: exists, reusing"); return json.loads(out.read_text())
    t0 = time.time()
    seizure_map = P.parse_summary(SUMMARY_PATH)
    ch_mean, ch_std = P.compute_subject_stats(SUBJ, RAW_DIR, seizure_map)
    thr = P.ARTIFACT_SD_MULTIPLIER * ch_std
    stats = dict(subject_id=SUBJ, ch_mean_uV=(ch_mean * 1e6).tolist(), ch_std_uV=(ch_std * 1e6).tolist(),
                 artifact_thresh_uV=(thr * 1e6).tolist(), elapsed_s=round(time.time() - t0))
    OUT.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(stats, indent=1))
    print(f"{SUBJ}_stats.json built in {time.time()-t0:.0f}s, mean artifact thresh "
          f"{thr.mean()*1e6:.1f} uV", flush=True)
    return stats


def build(max_files=None):
    out = OUT / (f"{SUBJ}_SMOKE.npz" if max_files else f"{SUBJ}.npz")
    if out.exists():
        print(f"{out.name}: exists, skip"); return
    t0 = time.time()
    stats = build_stats()
    mu = np.asarray(stats["ch_mean_uV"], dtype=np.float64) * 1e-6
    sd = np.asarray(stats["ch_std_uV"], dtype=np.float64) * 1e-6
    thr = np.asarray(stats["artifact_thresh_uV"], dtype=np.float64) * 1e-6
    edfs = list_files_local()
    if max_files:
        edfs = edfs[:max_files]
    parts = {k: [] for k in ("adj", "bp5", "f7", "is_ictal", "is_buffer", "is_flag5sd",
                             "is_signal_loss", "file_idx")}
    kept, skipped = [], []
    for edf in edfs:
        path = RAW_DIR / SUBJ / edf["fname"]
        try:
            filt, n = CE.filter_file(path)
        except RuntimeError as ex:
            if "missing one of the 18 common channels" in str(ex):
                skipped.append(edf["fname"])
                print(f"  {SUBJ}/{edf['fname']}: SKIPPED (missing common channel)", flush=True)
                continue
            raise
        fi = len(kept)
        kept.append(edf["fname"])
        secs = n * CE.WIN_SEC
        lab = P.build_labels(secs, edf["seizures"]).reshape(n, CE.WIN_SEC).max(axis=1) == 1
        buf = P.build_buffer_mask(secs, edf["seizures"]).reshape(n, CE.WIN_SEC).any(axis=1)
        raw = P.open_edf(path)
        sl = CE.compute_signal_loss_flags(raw, n)
        del raw
        flag = (np.abs(filt.astype(np.float64)).max(axis=2) > thr[None, :]).any(axis=1) & ~lab & ~buf
        for s in range(0, n, CE.CHUNK_WINDOWS):
            e = min(s + CE.CHUNK_WINDOWS, n)
            zw = CE.zscore(filt[s:e], mu, sd)
            a, b = C1B.graph_and_bp(zw)
            parts["adj"].append(a); parts["bp5"].append(b); parts["f7"].append(C1B.f7(zw))
        parts["is_ictal"].append(lab); parts["is_buffer"].append(buf)
        parts["is_flag5sd"].append(flag); parts["is_signal_loss"].append(sl)
        parts["file_idx"].append(np.full(n, fi, dtype=np.int16))
        del filt
        print(f"  {SUBJ}/{edf['fname']}: {n} windows, flagged {int(flag.sum())} "
              f"({time.time()-t0:.0f}s)", flush=True)
    data = {k: np.concatenate(v) for k, v in parts.items()}
    if not np.isfinite(data["f7"][~data["is_signal_loss"]]).all():
        raise SystemExit(f"{SUBJ}: non-finite added features outside signal-loss windows")
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez(out, files=np.array(kept, dtype=object), skipped_files=np.array(skipped, dtype=object), **data)
    n = len(data["is_ictal"])
    print(f"{SUBJ}: {n} windows, ictal {int(data['is_ictal'].sum())}, buffer "
          f"{int(data['is_buffer'].sum())}, flagged {int(data['is_flag5sd'].sum())}, "
          f"skipped files {skipped}, saved {out.name}, {time.time()-t0:.0f}s", flush=True)
    if not max_files and XCACHE.exists():
        xz = np.load(XCACHE, allow_pickle=True)
        same_files = list(xz["files"]) == kept
        same_n = int(xz["is_ictal"].sum()) == int(data["is_ictal"].sum()) and len(xz["is_ictal"]) == n
        same_sl = int(xz["is_signal_loss"].sum()) == int(data["is_signal_loss"].sum())
        print(f"cross-check vs {XCACHE}: files match={same_files}, n/ictal match={same_n}, "
              f"signal-loss count match={same_sl} (z-scoring differs by design, see module docstring)",
              flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    if not SUMMARY_PATH.exists():
        raise SystemExit(f"{SUMMARY_PATH}: not found")
    build(max_files=1 if a.smoke else None)


if __name__ == "__main__":
    main()
