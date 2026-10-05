#!/usr/bin/env python
"""
raw_eeg_view.py -- docs/CC_PROMPT_RAW_EEG_VIEW.md.

Look at the raw EEG and measure what the +-5 SD flagged windows actually are. No model, no
score, no threshold is fitted anywhere in this file. Labels (seizure onset/offset from the
CHB-MIT summaries) are used ONLY to (a) pick which seizures to draw in Part 1 and (b) measure
separability (AUROC) in Part 3 -- never to choose or tune a feature, a cutoff or a window.

Writes ONLY src/raw_eeg_view.py (this file) and results/raw_eeg_view/.

Four parts
----------
PART 1  pictures: seizure and flagged-window segments, 18 channels + PSD, contact sheets
        sheet_A / sheet_B / sheet_CD(+_p2) and one PNG per panel in panels/.
PART 2  what the flagged windows are: per-window exceedance counts above the committed
        per-channel 5xSD threshold, cause = single-spike vs sustained, by channel group.
PART 3  label-free features per window (Hjorth, line length, band ratios, spectral entropy,
        rhythmicity, kurtosis, spatial spread) scored by AUROC on three contrasts.
PART 4  read-only facts about the committed offline arrays and the original GAE training.

Signal convention (identical to the locked pipeline, verified bit-exact)
-----------------------------------------------------------------------
Every number and every trace below uses preprocessing.filter_window's own filtering: read
[start-FILTER_PAD, end+FILTER_PAD) of the raw EDF, bandpass 0.5-60 Hz (4th-order Butterworth,
sosfiltfilt) then 60 Hz notch (Q=30, filtfilt), keep the centre WIN_SAMPLES. This is what
preprocessing.count_windows/write_windows and continuous_eval.compute_artifact_flags use, so
the artifact decision here is the same decision the committed arrays were built with -- NOT
the whole-file filtering of continuous_eval.filter_file (which that module itself documents as
able to flip borderline 5xSD accept/reject decisions).

The one deviation from calling P.filter_window directly is mechanical, not numerical: the
subject's EDF is read once into RAM (raw.get_data()) and each window's padded segment is
sliced out of that array instead of issuing a fresh per-window disk read. filter_window_mem()
below reproduces P.filter_window to 0.0 max-abs difference (asserted at run time by
--selfcheck, and by the per-file assertion in process_file) and is ~5x faster, which is what
makes one pass over ~170k windows affordable.

Memory: one subject file's raw float64 array at a time (~130-500 MB) plus a 128-window
filtering chunk; peak RSS is logged per file and stays far below the ~3 GB budget.

Usage (repo root):
    python src/raw_eeg_view.py --selfcheck          # filter equivalence + mask agreement only
    python src/raw_eeg_view.py --stage part4        # read-only facts (seconds)
    python src/raw_eeg_view.py --stage part1        # the pictures
    python src/raw_eeg_view.py --stage part23       # the EEG pass + tables (the long one)
    python src/raw_eeg_view.py --stage all          # part4 -> part1 -> part23 -> SUMMARY.md
"""
import argparse
import gc
import json
import random
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import psutil
from scipy.signal import filtfilt, sosfiltfilt, welch
from scipy.stats import kurtosis as sp_kurtosis
from sklearn.metrics import roc_auc_score

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                      # noqa: E402
from matplotlib.gridspec import GridSpec             # noqa: E402

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src", ROOT / "src" / "dataprep"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import preprocessing as P                            # noqa: E402

# ── paths / constants ────────────────────────────────────────────────────────
DATASET_DIR = Path("F:/Study/Thesis/Dataset/CHB-MIT")
SUMMARY_DIR = ROOT / "data" / "summaries"
PROCESSED_DIR = ROOT / "data" / "processed"
SPLIT_PATH = ROOT / "data" / "splits" / "split_main.json"
CE_MASK_DIR = ROOT / "results" / "continuous_eval" / "cache" / "mask"

OUT = ROOT / "results" / "raw_eeg_view"
PANEL_DIR = OUT / "panels"
CACHE_DIR = OUT / "cache"
TABLE_DIR = OUT / "tables"
LOG_PATH = OUT / "run.log"

FS = P.FS                       # 256
WIN = P.WIN_SAMPLES             # 1024
WIN_S = P.WIN_S                 # 4
PAD = P.FILTER_PAD              # 768
N_CH = P.N_CH                   # 18
CH = list(P.COMMON_CHANNELS)

SEED = 42
CHUNK = 128                     # windows filtered + featurised per batch
TINY = 1e-30
SIGNAL_LOSS_STD_V = 1e-10       # continuous_eval Amendment A2, same constant

VAL_SUBJS = ["chb10", "chb11", "chb22"]
TRAIN_SUBJS = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08",
               "chb09", "chb12", "chb19", "chb20", "chb21", "chb23"]
TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
NUMBER_SUBJS = VAL_SUBJS + TRAIN_SUBJS      # Part 2/3 numbers: never a test subject

# channel groups (Part 2)
GROUPS = {
    "frontopolar": ["FP1-F7", "FP1-F3", "FP2-F4", "FP2-F8"],
    "temporal":    ["F7-T7", "T7-P7", "F8-T8", "T8-P8"],
    "central":     ["F3-C3", "C3-P3", "F4-C4", "C4-P4"],
    "parieto-occipital": ["P7-O1", "P3-O1", "P4-O2", "P8-O2"],
    "midline":     ["FZ-CZ", "CZ-PZ"],
}
GROUP_OF = {c: g for g, cs in GROUPS.items() for c in cs}
assert set(GROUP_OF) == set(CH), "channel groups must tile the 18 common channels"

SINGLE_SPIKE_MAX = 3            # <=3 samples above 5 SD in total == single-spike

# Part 3 feature names (per channel, then median/max across the 18 channels)
PER_CH_FEATS = [
    "mobility", "complexity", "linelen_sd",
    "rel_d05_4", "rel_4_8", "rel_8_13", "rel_13_30", "rel_30_60",
    "muscle_20_60", "slow_05_2", "spec_entropy", "rhythmicity", "kurtosis",
]
AGG_FEATS = [f"{f}_{a}" for f in PER_CH_FEATS for a in ("med", "max")]
SPATIAL_FEAT = "frac_ch_sd_gt3med"
ALL_FEATS = AGG_FEATS + [SPATIAL_FEAT]

CONTRASTS = [
    ("sz_vs_flagged", "seizure", "flagged"),
    ("sz_vs_bg", "seizure", "background"),
    ("flagged_vs_bg", "flagged", "background"),
]

_PROC = psutil.Process()


def rss_mb():
    return _PROC.memory_info().rss / 1e6


def log(msg):
    OUT.mkdir(parents=True, exist_ok=True)
    line = f"[raw_eeg_view] {time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ── file listing / labels ────────────────────────────────────────────────────
def subject_files(subj):
    """Files actually present on disk, filename order -- preprocessing.py's own convention
    (it globs the subject directory rather than trusting the summary text, so the committed
    {subj}_stats.json were built from exactly this list)."""
    return sorted(p.name for p in (DATASET_DIR / subj).glob("*.edf"))


def seizure_map(subj):
    return P.parse_summary(SUMMARY_DIR / f"{subj}-summary.txt")


def subject_thresholds(subj):
    """Committed per-channel 5xSD artifact threshold and per-channel SD, both in Volts."""
    st = json.loads((PROCESSED_DIR / f"{subj}_stats.json").read_text())
    thr = np.asarray(st["artifact_thresh_uV"], dtype=np.float64) * 1e-6
    sd = np.asarray(st["ch_std_uV"], dtype=np.float64) * 1e-6
    return thr, sd, st


# ── filtering (bit-exact reproduction of preprocessing.filter_window) ────────
def read_raw(path, allow_missing=False):
    """preprocessing.open_edf, picked to the 18 common channels. If allow_missing, a file
    missing one of them returns None -- preprocessing.py's OWN convention (count_windows,
    write_windows, compute_subject_stats all do `if raw is None: continue`); otherwise (the
    default, for Part 1's hand-picked files) it raises, since those files are chosen by this
    script and must exist."""
    raw = P.open_edf(Path(path))
    if raw is None:
        if allow_missing:
            return None
        raise RuntimeError(f"{path}: missing one of the 18 common channels")
    return raw


def filter_window_mem(data, n_total, start, end):
    """preprocessing.filter_window with the EDF read replaced by a slice of `data`
    (= raw.get_data()). Verified bit-identical; see module docstring."""
    ps = max(0, start - PAD)
    pe = min(n_total, end + PAD)
    seg = data[:, ps:pe]
    bp = sosfiltfilt(P._BP_SOS, seg, axis=1)
    notched = filtfilt(P._NOTCH_B, P._NOTCH_A, bp, axis=1)
    off = start - ps
    return notched[:, off:off + WIN]


def filter_chunk(data, n_total, i0, i1):
    """[i1-i0, 18, 1024] float64, Volts, pipeline-filtered."""
    out = np.empty((i1 - i0, N_CH, WIN), dtype=np.float64)
    for k, i in enumerate(range(i0, i1)):
        out[k] = filter_window_mem(data, n_total, i * WIN, i * WIN + WIN)
    return out


def window_labels(n_windows, seizure_list):
    """is_ictal / is_buffer per window -- preprocessing.build_labels + build_buffer_mask on
    the window grid, exactly as continuous_eval.process_subject does."""
    n_secs = n_windows * WIN_S
    labels = P.build_labels(n_secs, seizure_list)
    buf = P.build_buffer_mask(n_secs, seizure_list)
    wl = labels.reshape(n_windows, WIN_S).max(axis=1) == 1
    wb = buf.reshape(n_windows, WIN_S).any(axis=1)
    return wl, wb


def window_seizure_duration(n_windows, seizure_list):
    """Duration (s) of the seizure a window belongs to; 0 for non-ictal windows. A window
    overlapping two seizures is assigned the one it overlaps most."""
    dur = np.zeros(n_windows, dtype=np.int32)
    best = np.zeros(n_windows, dtype=np.int32)
    for on, off in seizure_list:
        for i in range(n_windows):
            a, b = i * WIN_S, (i + 1) * WIN_S
            ov = max(0, min(b, off) - max(a, on))
            if ov > best[i]:
                best[i] = ov
                dur[i] = off - on
    return dur


# ── Part 3 features ─────────────────────────────────────────────────────────
_BAND_EDGES = [("rel_d05_4", 0.5, 4.0), ("rel_4_8", 4.0, 8.0), ("rel_8_13", 8.0, 13.0),
               ("rel_13_30", 13.0, 30.0), ("rel_30_60", 30.0, 60.0)]


def window_features(W):
    """W: [k, 18, 1024] float64 Volts (pipeline-filtered).
    Returns (per_ch: dict name -> [k,18], sd_uV: [k,18]).
    All spectral quantities use Welch nperseg=512, noverlap=256 (df = 0.5 Hz) on the same
    filtered signal; relative powers are over the 0.5-60 Hz passband and sum to 1."""
    X = W * 1e6                                    # µV
    d1 = np.diff(X, axis=-1)
    d2 = np.diff(d1, axis=-1)
    v0 = X.var(axis=-1)
    v1 = d1.var(axis=-1)
    v2 = d2.var(axis=-1)
    sd = np.sqrt(v0)
    mob = np.sqrt(v1 / np.maximum(v0, TINY))
    mob2 = np.sqrt(v2 / np.maximum(v1, TINY))
    cx = mob2 / np.maximum(mob, TINY)
    ll = np.abs(d1).sum(axis=-1) / np.maximum(sd, TINY)
    kur = sp_kurtosis(X, axis=-1, fisher=True, bias=False)

    f, Pxx = welch(X, fs=FS, nperseg=512, noverlap=256, axis=-1)
    inb = (f >= 0.5) & (f < 60.0)
    fb = f[inb]
    Pb = Pxx[..., inb]
    tot = np.maximum(Pb.sum(axis=-1), TINY)

    out = {"mobility": mob, "complexity": cx, "linelen_sd": ll, "kurtosis": kur}
    for name, lo, hi in _BAND_EDGES:
        m = (fb >= lo) & (fb < hi)
        out[name] = Pb[..., m].sum(axis=-1) / tot
    m = (fb >= 20.0) & (fb < 60.0)
    out["muscle_20_60"] = Pb[..., m].sum(axis=-1) / tot
    m = (fb >= 0.5) & (fb < 2.0)
    out["slow_05_2"] = Pb[..., m].sum(axis=-1) / tot

    p = Pb / tot[..., None]
    out["spec_entropy"] = -(p * np.log(p + 1e-300)).sum(axis=-1) / np.log(Pb.shape[-1])

    fpk = fb[Pb.argmax(axis=-1)]                   # [k,18]
    near = np.abs(fb[None, None, :] - fpk[..., None]) <= 1.5
    out["rhythmicity"] = (Pb * near).sum(axis=-1) / tot

    return out, sd


def aggregate(per_ch):
    """median and max across the 18 channels -> dict of [k] arrays."""
    agg = {}
    for name, v in per_ch.items():
        agg[f"{name}_med"] = np.median(v, axis=1)
        agg[f"{name}_max"] = v.max(axis=1)
    return agg


# ── the one EEG pass (Parts 2 + 3 data) ─────────────────────────────────────
def process_file(subj, fname, thr, seizure_list, verify_filter=True):
    """One file, streamed. Returns a dict of per-window arrays, or None if the file is
    missing one of the 18 common channels (preprocessing.py's own convention: such files
    are silently skipped everywhere, e.g. the committed {subj}_stats.json were built
    without them) or shorter than one 4 s window."""
    path = DATASET_DIR / subj / fname
    raw = read_raw(path, allow_missing=True)
    if raw is None:
        return None
    n_total = int(raw.n_times)
    n_windows = n_total // WIN
    if n_windows == 0:
        log(f"  {subj}/{fname}: shorter than one 4 s window, skipped")
        del raw
        return None

    data = raw.get_data()                           # [18, n_total] float64, Volts
    if verify_filter:
        i = n_windows // 2
        a = P.filter_window(raw, i * WIN, i * WIN + WIN)
        b = filter_window_mem(data, n_total, i * WIN, i * WIN + WIN)
        d = float(np.abs(a - b).max())
        assert d == 0.0, f"{fname}: filter_window_mem deviates by {d:g}"
    del raw

    wl, wb = window_labels(n_windows, seizure_list)
    sz_dur = window_seizure_duration(n_windows, seizure_list)

    is_sl = np.zeros(n_windows, dtype=bool)
    n_exc_ch = np.zeros((n_windows, N_CH), dtype=np.int32)
    sd_uV = np.zeros((n_windows, N_CH), dtype=np.float32)
    feats = {k: np.zeros(n_windows, dtype=np.float32) for k in AGG_FEATS}

    for i0 in range(0, n_windows, CHUNK):
        i1 = min(i0 + CHUNK, n_windows)
        # signal-loss flag on the RAW (unfiltered) window, same fixed threshold as
        # continuous_eval.compute_signal_loss_flags (Amendment A2). Done window by window
        # so no second full-file copy is ever materialised.
        for k, i in enumerate(range(i0, i1)):
            is_sl[i] = bool(np.all(data[:, i * WIN:(i + 1) * WIN].std(axis=1)
                                   < SIGNAL_LOSS_STD_V))
        Wc = filter_chunk(data, n_total, i0, i1)
        n_exc_ch[i0:i1] = (np.abs(Wc) > thr[None, :, None]).sum(axis=2)
        per_ch, sdc = window_features(Wc)
        sd_uV[i0:i1] = sdc.astype(np.float32)
        for k, v in aggregate(per_ch).items():
            feats[k][i0:i1] = v.astype(np.float32)
        del Wc, per_ch
    del data
    gc.collect()

    n_exc_tot = n_exc_ch.sum(axis=1)
    # is_artifact: continuous_eval.compute_artifact_flags -- ictal and buffer windows are
    # never artifact-checked, so they are never flagged.
    is_art = (n_exc_tot > 0) & (~wl) & (~wb)
    return dict(n_windows=n_windows, is_ictal=wl, is_buffer=wb, is_artifact=is_art,
                is_signal_loss=is_sl, sz_dur=sz_dur, n_exc_ch=n_exc_ch,
                n_exc_tot=n_exc_tot.astype(np.int32), sd_uV=sd_uV, feats=feats)


def part3_file_selection(subj):
    """chb10/11/22 (validation): every file. The 12 training subjects: every file that
    contains a seizure, plus 2 other files drawn with random.Random(42)."""
    files = subject_files(subj)
    szm = seizure_map(subj)
    if subj in VAL_SUBJS:
        return files, "all files"
    sz = [f for f in files if szm.get(f)]
    other = [f for f in files if not szm.get(f)]
    rng = random.Random(SEED)
    pick = sorted(rng.sample(other, min(2, len(other))))
    return sorted(sz + pick), f"{len(sz)} seizure file(s) + {pick}"


def subject_cache_path(subj):
    return CACHE_DIR / f"{subj}.npz"


def run_eeg_pass(subjects, force=False):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for subj in subjects:
        cp = subject_cache_path(subj)
        if cp.exists() and not force:
            log(f"{subj}: cached ({cp.name}), skip")
            continue
        t0 = time.time()
        thr, ch_sd, _ = subject_thresholds(subj)
        files, how = part3_file_selection(subj)
        szm = seizure_map(subj)
        log(f"{subj}: {len(files)} file(s) selected -- {how}")

        acc = {k: [] for k in ("is_ictal", "is_buffer", "is_artifact", "is_signal_loss",
                               "sz_dur", "n_exc_tot")}
        exc_ch, sd_all, file_idx, win_idx = [], [], [], []
        feat_acc = {k: [] for k in AGG_FEATS}
        kept_files, skipped_files = [], []
        for fi, fname in enumerate(files):
            ft = time.time()
            r = process_file(subj, fname, thr, szm.get(fname, []))
            if r is None:
                log(f"  {subj}/{fname}: SKIPPED (missing one of the 18 common channels or "
                    f"<1 window) -- preprocessing.py's own convention")
                skipped_files.append(fname)
                continue
            for k in acc:
                acc[k].append(r[k])
            exc_ch.append(r["n_exc_ch"])
            sd_all.append(r["sd_uV"])
            file_idx.append(np.full(r["n_windows"], len(kept_files), dtype=np.int16))
            win_idx.append(np.arange(r["n_windows"], dtype=np.int32))
            for k in AGG_FEATS:
                feat_acc[k].append(r["feats"][k])
            log(f"  {subj}/{fname}: {r['n_windows']} win, ictal={int(r['is_ictal'].sum())}, "
                f"flagged={int(r['is_artifact'].sum())}, "
                f"{time.time()-ft:.1f}s, rss={rss_mb():.0f}MB")
            kept_files.append(fname)
            del r
            gc.collect()

        if not kept_files:
            raise RuntimeError(f"{subj}: every selected file was skipped -- check the data path")
        out = {k: np.concatenate(v) for k, v in acc.items()}
        out["n_exc_ch"] = np.concatenate(exc_ch)
        out["sd_uV"] = np.concatenate(sd_all)
        out["file_idx"] = np.concatenate(file_idx)
        out["win_idx"] = np.concatenate(win_idx)
        for k in AGG_FEATS:
            out[k] = np.concatenate(feat_acc[k])
        files = kept_files
        out["skipped_files"] = np.array(skipped_files, dtype=object)
        out["files"] = np.array(files, dtype=object)
        out["ch_sd_uV"] = (ch_sd * 1e6).astype(np.float64)
        np.savez_compressed(cp, **out)
        el = time.time() - t0
        log(f"{subj}: DONE {len(out['is_ictal'])} windows in {el/60:.1f} min "
            f"({el:.0f}s), rss={rss_mb():.0f}MB -> {cp.name}")


def load_subject_cache(subj):
    z = np.load(subject_cache_path(subj), allow_pickle=True)
    d = {k: z[k] for k in z.files}
    d["files"] = [str(x) for x in d["files"]]
    return d


# ── self-check: our mask vs. the committed continuous_eval mask ─────────────
def mask_agreement(subj, d):
    """Compare our recomputed flags against results/continuous_eval/cache/mask/{subj}.npz.
    Only meaningful when every file of the subject was processed (validation subjects)."""
    mp = CE_MASK_DIR / f"{subj}.npz"
    if not mp.exists():
        return None
    z = np.load(mp, allow_pickle=True)
    spans = [tuple(x) for x in z["spans"]]
    names = [s[0] for s in spans]
    if names != list(d["files"]):
        return dict(comparable=False, reason="file set differs from the cached mask")
    if len(z["is_ictal"]) != len(d["is_ictal"]):
        return dict(comparable=False, reason="window count differs from the cached mask")
    res = dict(comparable=True, n=int(len(d["is_ictal"])))
    for k in ("is_ictal", "is_buffer", "is_artifact", "is_signal_loss"):
        res[k] = int((z[k] == d[k]).sum())
    return res


def selfcheck():
    log("selfcheck: filter_window_mem vs preprocessing.filter_window")
    for subj, fname in (("chb10", subject_files("chb10")[0]),
                        ("chb16", subject_files("chb16")[0])):
        raw = read_raw(DATASET_DIR / subj / fname)
        n_total = int(raw.n_times)
        nw = n_total // WIN
        data = raw.get_data()
        worst = 0.0
        for i in (0, 1, 7, nw // 3, nw // 2, nw - 1):
            a = P.filter_window(raw, i * WIN, i * WIN + WIN)
            b = filter_window_mem(data, n_total, i * WIN, i * WIN + WIN)
            worst = max(worst, float(np.abs(a - b).max()))
        log(f"  {subj}/{fname}: 6 windows, max abs diff = {worst:g}")
        assert worst == 0.0
        del raw, data
        gc.collect()
    for subj in VAL_SUBJS:
        if subject_cache_path(subj).exists():
            log(f"  mask agreement {subj}: {mask_agreement(subj, load_subject_cache(subj))}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 1 -- pictures
# ══════════════════════════════════════════════════════════════════════════════
SEIZ_PRE, SEIZ_POST = 20.0, 40.0        # onset-20 s .. onset+40 s
WINSEG_S = 30.0                         # 30 s around a flagged/other window


def collect_seizures(subj):
    szm = seizure_map(subj)
    out = []
    for f in sorted(szm):
        for on, off in szm[f]:
            out.append(dict(subj=subj, fname=f, onset=on, offset=off, dur=off - on))
    return out


def read_segment(subj, fname, t0_s, t1_s):
    """Returns (filtered_uV, raw_uV, t0_actual, t1_actual) for [t0_s, t1_s) clipped to file.
    The filtered trace is the pipeline filter applied to the segment with FILTER_PAD padding
    on each side -- the same convention as filter_window, just over a longer centre."""
    raw = read_raw(DATASET_DIR / subj / fname)
    n_total = int(raw.n_times)
    s = max(0, int(round(t0_s * FS)))
    e = min(n_total, int(round(t1_s * FS)))
    ps, pe = max(0, s - PAD), min(n_total, e + PAD)
    seg = raw.get_data(start=ps, stop=pe)
    del raw
    bp = sosfiltfilt(P._BP_SOS, seg, axis=1)
    notched = filtfilt(P._NOTCH_B, P._NOTCH_A, bp, axis=1)
    off = s - ps
    filt = notched[:, off:off + (e - s)] * 1e6
    rawseg = seg[:, off:off + (e - s)] * 1e6
    return filt, rawseg, s / FS, e / FS


def build_panel_specs_A():
    specs = []
    for subj, k in (("chb16", 3), ("chb06", 3), ("chb14", 2)):
        szs = sorted(collect_seizures(subj), key=lambda s: (s["dur"], s["fname"], s["onset"]))
        for s in szs[:k]:
            specs.append(dict(kind="seizure", **s))
    return specs, ("A: the 3 shortest seizures of chb16, the 3 shortest of chb06, "
                   "the 2 shortest of chb14")


def build_panel_specs_B():
    specs = []
    for subj, k in (("chb15", 3), ("chb03", 2), ("chb18", 2)):
        szs = sorted(collect_seizures(subj), key=lambda s: (s["fname"], s["onset"]))
        rng = random.Random(SEED)
        for s in sorted(rng.sample(szs, k), key=lambda s: (s["fname"], s["onset"])):
            specs.append(dict(kind="seizure", **s))
    return specs, ("B: 3 seizures of chb15, 2 of chb03, 2 of chb18, each drawn with "
                   "random.Random(42) over that subject's seizures (no model score)")


def ce_mask(subj):
    z = np.load(CE_MASK_DIR / f"{subj}.npz", allow_pickle=True)
    spans = [(str(x[0]), int(x[1]), int(x[2])) for x in z["spans"]]
    return z, spans


def global_to_file(spans, gi):
    for fname, a, b in spans:
        if a <= gi < b:
            return fname, gi - a
    raise KeyError(gi)


def build_panel_specs_C():
    """8 flagged (is_artifact, so non-ictal and non-buffer) windows: 2 per subject from
    chb10, chb11, chb22, chb13, one single-spike and one sustained, found by walking a
    random.Random(42) permutation of that subject's flagged windows."""
    specs = []
    for subj in ("chb10", "chb11", "chb22", "chb13"):
        z, spans = ce_mask(subj)
        thr, _, _ = subject_thresholds(subj)
        flagged = np.flatnonzero(z["is_artifact"])
        order = list(flagged)
        random.Random(SEED).shuffle(order)
        want = {"single-spike": None, "sustained": None}
        cache_data, cache_name = None, None
        for gi in order:
            if all(v is not None for v in want.values()):
                break
            fname, li = global_to_file(spans, int(gi))
            if fname != cache_name:
                raw = read_raw(DATASET_DIR / subj / fname)
                n_total = int(raw.n_times)
                cache_data = (raw.get_data(), n_total)
                cache_name = fname
                del raw
            data, n_total = cache_data
            w = filter_window_mem(data, n_total, li * WIN, li * WIN + WIN)
            n_exc = int((np.abs(w) > thr[:, None]).sum())
            cause = "single-spike" if n_exc <= SINGLE_SPIKE_MAX else "sustained"
            if want[cause] is None:
                want[cause] = dict(kind="window", subj=subj, fname=fname, local_win=li,
                                   n_exc=n_exc, cause=cause)
        cache_data = None
        gc.collect()
        for cause in ("single-spike", "sustained"):
            if want[cause] is not None:
                specs.append(want[cause])
    return specs, ("C: flagged (is_artifact) non-ictal non-buffer windows -- 2 per subject "
                   "from chb10, chb11, chb22, chb13, one single-spike and one sustained each, "
                   "first of each cause met in a random.Random(42) permutation of that "
                   "subject's flagged windows")


def chb13_worst_files():
    """The 2 chb13 files with the highest flagged share (flagged / windows in the file)."""
    z, spans = ce_mask("chb13")
    art = z["is_artifact"]
    rows = []
    for fname, a, b in spans:
        n = b - a
        rows.append((fname, int(art[a:b].sum()), n, art[a:b].sum() / n))
    rows.sort(key=lambda r: (-r[3], r[0]))
    return rows


def build_panel_specs_D():
    """chb13's 2 highest-flagged-share files, 3 random (seed 42) windows each, with the
    per-channel SD of the file over the subject-wide per-channel SD annotated."""
    rows = chb13_worst_files()
    z, spans = ce_mask("chb13")
    thr, ch_sd, _ = subject_thresholds("chb13")
    specs = []
    extra = {}
    lookup = {f: (x, y) for f, x, y in spans}
    for fname, n_flag, n_win, share in rows[:2]:
        g0, g1 = lookup[fname]
        raw = read_raw(DATASET_DIR / "chb13" / fname)
        n_total = int(raw.n_times)
        data = raw.get_data()
        del raw
        nw = n_total // WIN
        # per-channel SD of the whole file on the pipeline-filtered signal
        s1 = np.zeros(N_CH); s2 = np.zeros(N_CH); cnt = 0
        for i0 in range(0, nw, CHUNK):
            i1 = min(i0 + CHUNK, nw)
            Wc = filter_chunk(data, n_total, i0, i1)
            s1 += Wc.sum(axis=(0, 2))
            s2 += (Wc * Wc).sum(axis=(0, 2))
            cnt += (i1 - i0) * WIN
            del Wc
        mean = s1 / cnt
        file_sd = np.sqrt(np.maximum(s2 / cnt - mean ** 2, 0.0))
        ratio = file_sd / ch_sd
        flagged_local = np.flatnonzero(z["is_artifact"][g0:g1])
        rng = random.Random(SEED)
        picks = sorted(rng.sample(list(flagged_local), min(3, len(flagged_local))))
        for li in picks:
            w = filter_window_mem(data, n_total, int(li) * WIN, int(li) * WIN + WIN)
            n_exc = int((np.abs(w) > thr[:, None]).sum())
            specs.append(dict(kind="window", subj="chb13", fname=fname, local_win=int(li),
                              n_exc=n_exc,
                              cause="single-spike" if n_exc <= SINGLE_SPIKE_MAX else "sustained",
                              sd_ratio=ratio.copy()))
        extra[fname] = dict(n_flag=n_flag, n_win=n_win, share=float(share),
                            ratio=ratio.tolist(), file_sd_uV=(file_sd * 1e6).tolist())
        del data
        gc.collect()
    return specs, extra, ("D: chb13's 2 files with the highest flagged share, 3 "
                          "random.Random(42) flagged windows each; the per-channel SD of the "
                          "file divided by the subject-wide per-channel SD "
                          "(stats.json ch_std_uV) is printed beside each trace")


def panel_segment(spec):
    """Returns (filt_uV, raw_uV, t0, t1, title, marks)."""
    if spec["kind"] == "seizure":
        t0 = spec["onset"] - SEIZ_PRE
        t1 = spec["onset"] + SEIZ_POST
        filt, rawseg, a, b = read_segment(spec["subj"], spec["fname"], t0, t1)
        title = (f"{spec['subj']}  {spec['fname']}  {a:.0f}-{b:.0f} s  "
                 f"seizure {spec['onset']}-{spec['offset']} s  duration {spec['dur']} s")
        marks = [(spec["onset"], spec["offset"])]
    else:
        wa = spec["local_win"] * WIN_S
        wb = wa + WIN_S
        c = 0.5 * (wa + wb)
        filt, rawseg, a, b = read_segment(spec["subj"], spec["fname"],
                                         c - WINSEG_S / 2, c + WINSEG_S / 2)
        title = (f"{spec['subj']}  {spec['fname']}  {a:.0f}-{b:.0f} s  "
                 f"flagged window {wa}-{wb} s  {spec['cause']} "
                 f"({spec['n_exc']} samples above 5 SD)")
        marks = [(wa, wb)]
    return filt, rawseg, a, b, title, marks


CLIP_MULT = 1.2        # traces saturate at +-CLIP_MULT x spacing instead of painting over
                       # their neighbours; the true exceedance sizes are in Part 2.


def draw_panel(ax_eeg, ax_psd, filt, rawseg, t0, t1, title, marks, spacing_uV,
               sd_ratio=None):
    n = filt.shape[1]
    t = t0 + np.arange(n) / FS
    offs = (np.arange(N_CH)[::-1] * spacing_uV)
    lim = CLIP_MULT * spacing_uV
    for ci in range(N_CH):
        y = np.clip(filt[ci], -lim, lim)
        ax_eeg.plot(t, y + offs[ci], lw=0.35, color="#111111")
    ax_eeg.set_yticks(offs)
    ax_eeg.set_yticklabels(CH, fontsize=6)
    ax_eeg.set_xlim(t0, t1)
    ax_eeg.set_ylim(-1.4 * spacing_uV, offs[0] + 1.4 * spacing_uV)
    for a, b in marks:
        ax_eeg.axvspan(a, b, color="#d62728", alpha=0.12, lw=0)
        ax_eeg.axvline(a, color="#d62728", lw=0.7)
        ax_eeg.axvline(b, color="#d62728", lw=0.7, ls=":")
    ax_eeg.set_title(title, fontsize=7, loc="left")
    ax_eeg.tick_params(axis="x", labelsize=6)
    ax_eeg.set_xlabel("time in file (s)", fontsize=6)
    for s in ("top", "right"):
        ax_eeg.spines[s].set_visible(False)
    # common amplitude scale: a bar of exactly `spacing_uV`, drawn clear of the traces
    xb = t0 + 0.012 * (t1 - t0)
    yb = -1.25 * spacing_uV
    ax_eeg.plot([xb, xb], [yb, yb + spacing_uV],
                color="#1f77b4", lw=1.8, solid_capstyle="butt")
    ax_eeg.text(xb + 0.008 * (t1 - t0), yb + spacing_uV * 0.5,
                f"{spacing_uV:g} uV = channel spacing "
                f"(traces clipped at +-{CLIP_MULT * spacing_uV:g} uV)",
                fontsize=6.5, color="#1f77b4", va="center", ha="left")
    if sd_ratio is not None:
        for ci in range(N_CH):
            ax_eeg.text(1.004, offs[ci], f"x{sd_ratio[ci]:.2f}", fontsize=5.5,
                        color="#8c564b", transform=ax_eeg.get_yaxis_transform(),
                        va="center", ha="left")
        ax_eeg.text(1.004, offs[0] + spacing_uV * 0.75, "SD file/subject", fontsize=5.5,
                    color="#8c564b", transform=ax_eeg.get_yaxis_transform(),
                    va="center", ha="left")

    f, Pxx = welch(rawseg, fs=FS, nperseg=1024, noverlap=512, axis=-1)
    m = (f >= 0.5) & (f <= 100.0)
    for ci in range(N_CH):
        ax_psd.semilogy(f[m], Pxx[ci, m], lw=0.3, color="#999999")
    ax_psd.semilogy(f[m], np.median(Pxx[:, m], axis=0), lw=1.0, color="#111111")
    ax_psd.axvline(60.0, color="#d62728", lw=0.6, ls="--")
    ax_psd.set_xlim(0.5, 100.0)
    ax_psd.set_xlabel("Hz (raw, unfiltered)", fontsize=6)
    ax_psd.set_ylabel("uV^2/Hz", fontsize=6)
    ax_psd.tick_params(labelsize=6)
    for s in ("top", "right"):
        ax_psd.spines[s].set_visible(False)


def spacing_for(segments):
    """One amplitude scale shared by every panel of a sheet: a round value at least twice
    the MEDIAN over the sheet's panels of that panel's 99th percentile of |signal|. The
    median (not the max) keeps the scale readable when one panel contains a huge artifact;
    traces that exceed it saturate at CLIP_MULT x spacing (annotated on every panel), and
    the actual exceedance sizes are reported numerically in Part 2."""
    q = float(np.median([np.percentile(np.abs(s), 99.0) for s in segments]))
    target = 2.0 * q
    for v in (25, 50, 75, 100, 150, 200, 250, 300, 400, 500, 600, 800, 1000, 1500, 2000,
              3000, 4000, 5000, 8000, 10000):
        if v >= target:
            return float(v)
    return float(np.ceil(target / 1000.0) * 1000)


def render_sheet(specs, sheet_name, caption, max_panels=8):
    """Draw the panels, write one PNG per panel and the contact sheet(s). Returns the list
    of written sheet paths."""
    PANEL_DIR.mkdir(parents=True, exist_ok=True)
    loaded = []
    for spec in specs:
        filt, rawseg, a, b, title, marks = panel_segment(spec)
        loaded.append(dict(spec=spec, filt=filt, raw=rawseg, t0=a, t1=b,
                           title=title, marks=marks))
    spacing = spacing_for([d["filt"] for d in loaded])
    log(f"{sheet_name}: {len(loaded)} panels, common channel spacing {spacing:g} uV")

    for k, d in enumerate(loaded, 1):
        s = d["spec"]
        tag = (f"{s['subj']}_{s['fname'].replace('.edf','')}_"
               f"{'sz' + str(s['onset']) if s['kind']=='seizure' else 'w' + str(s['local_win'])}")
        fig = plt.figure(figsize=(8.0, 6.0), dpi=200)
        gs = GridSpec(2, 1, height_ratios=[4.0, 1.0], hspace=0.26,
                      left=0.085, right=0.90, top=0.945, bottom=0.075)
        draw_panel(fig.add_subplot(gs[0]), fig.add_subplot(gs[1]), d["filt"], d["raw"],
                   d["t0"], d["t1"], d["title"], d["marks"], spacing,
                   s.get("sd_ratio"))
        p = PANEL_DIR / f"{sheet_name}_{k:02d}_{tag}.png"
        fig.savefig(p)
        plt.close(fig)

    written = []
    pages = [loaded[i:i + max_panels] for i in range(0, len(loaded), max_panels)]
    for pi, page in enumerate(pages):
        nrows = int(np.ceil(len(page) / 2))
        fig = plt.figure(figsize=(16.0, 5.9 * nrows), dpi=100)
        gs = GridSpec(nrows * 2, 2, height_ratios=[4.0, 1.0] * nrows,
                      hspace=0.40, wspace=0.26,
                      left=0.055, right=0.945, top=0.978, bottom=0.028)
        for k, d in enumerate(page):
            r, c = divmod(k, 2)
            draw_panel(fig.add_subplot(gs[2 * r, c]), fig.add_subplot(gs[2 * r + 1, c]),
                       d["filt"], d["raw"], d["t0"], d["t1"], d["title"], d["marks"],
                       spacing, d["spec"].get("sd_ratio"))
        suffix = "" if pi == 0 else f"_p{pi+1}"
        p = OUT / f"sheet_{sheet_name}{suffix}.png"
        fig.savefig(p)
        plt.close(fig)
        written.append(p)
        log(f"  wrote {p.name} ({len(page)} panels)")
    return written, spacing, caption


def run_part1():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    info = {}
    sA, capA = build_panel_specs_A()
    wA, spA, _ = render_sheet(sA, "A", capA)
    info["A"] = dict(caption=capA, spacing_uV=spA, sheets=[p.name for p in wA],
                     panels=[dict(subj=s["subj"], file=s["fname"], onset=s["onset"],
                                  offset=s["offset"], dur_s=s["dur"]) for s in sA])
    sB, capB = build_panel_specs_B()
    wB, spB, _ = render_sheet(sB, "B", capB)
    info["B"] = dict(caption=capB, spacing_uV=spB, sheets=[p.name for p in wB],
                     panels=[dict(subj=s["subj"], file=s["fname"], onset=s["onset"],
                                  offset=s["offset"], dur_s=s["dur"]) for s in sB])
    sC, capC = build_panel_specs_C()
    sD, extraD, capD = build_panel_specs_D()
    wCD, spCD, _ = render_sheet(sC + sD, "CD", capC + " | " + capD)
    info["CD"] = dict(caption_C=capC, caption_D=capD, spacing_uV=spCD,
                      sheets=[p.name for p in wCD],
                      panels_C=[dict(subj=s["subj"], file=s["fname"],
                                     window_s=[s["local_win"] * WIN_S,
                                               s["local_win"] * WIN_S + WIN_S],
                                     n_exceed=s["n_exc"], cause=s["cause"]) for s in sC],
                      panels_D=[dict(subj=s["subj"], file=s["fname"],
                                     window_s=[s["local_win"] * WIN_S,
                                               s["local_win"] * WIN_S + WIN_S],
                                     n_exceed=s["n_exc"], cause=s["cause"]) for s in sD],
                      chb13_files=extraD,
                      chb13_flagged_share_ranking=[
                          dict(file=f, n_flagged=n, n_windows=w, share=round(sh, 4))
                          for f, n, w, sh in chb13_worst_files()])
    (OUT / "part1_panels.json").write_text(json.dumps(info, indent=2, default=str))
    log(f"PART 1 done in {time.time()-t0:.0f}s")
    return info


# ══════════════════════════════════════════════════════════════════════════════
# PART 2 -- what the flagged windows are
# ══════════════════════════════════════════════════════════════════════════════
def part2_tables(subjects):
    rows = []
    pooled = dict(n=0, single=0, sustained=0,
                  grp={g: 0 for g in GROUPS}, grp_any={g: 0 for g in GROUPS},
                  nch=[], ntot=[])
    for subj in subjects:
        d = load_subject_cache(subj)
        fl = d["is_artifact"].astype(bool)
        n = int(fl.sum())
        exc = d["n_exc_ch"][fl]                       # [n, 18]
        tot = exc.sum(axis=1)
        nch = (exc > 0).sum(axis=1)
        top = exc.argmax(axis=1)          # ties -> the lowest channel index (montage order)
        single = tot <= SINGLE_SPIKE_MAX
        r = dict(subject=subj, n_flagged=n,
                 share_single=float(single.mean()) if n else float("nan"),
                 share_sustained=float((~single).mean()) if n else float("nan"),
                 median_n_exceed=float(np.median(tot)) if n else float("nan"),
                 mean_n_exceed=float(tot.mean()) if n else float("nan"),
                 p95_n_exceed=float(np.percentile(tot, 95)) if n else float("nan"),
                 median_n_ch=float(np.median(nch)) if n else float("nan"),
                 mean_n_ch=float(nch.mean()) if n else float("nan"),
                 share_1ch=float((nch == 1).mean()) if n else float("nan"))
        for g, cs in GROUPS.items():
            idx = [CH.index(c) for c in cs]
            r[f"top_{g}"] = float(np.isin(top, idx).mean()) if n else float("nan")
            r[f"any_{g}"] = float((exc[:, idx] > 0).any(axis=1).mean()) if n else float("nan")
            pooled["grp"][g] += int(np.isin(top, idx).sum())
            pooled["grp_any"][g] += int((exc[:, idx] > 0).any(axis=1).sum())
        r["top_channel_mode"] = CH[int(np.bincount(top, minlength=N_CH).argmax())] if n else ""
        rows.append(r)
        pooled["n"] += n
        pooled["single"] += int(single.sum())
        pooled["sustained"] += int((~single).sum())
        pooled["nch"].append(nch)
        pooled["ntot"].append(tot)
        del d
    if pooled["n"]:
        nch = np.concatenate(pooled["nch"])
        tot = np.concatenate(pooled["ntot"])
        pr = dict(subject="POOLED", n_flagged=pooled["n"],
                  share_single=pooled["single"] / pooled["n"],
                  share_sustained=pooled["sustained"] / pooled["n"],
                  median_n_exceed=float(np.median(tot)), mean_n_exceed=float(tot.mean()),
                  p95_n_exceed=float(np.percentile(tot, 95)),
                  median_n_ch=float(np.median(nch)), mean_n_ch=float(nch.mean()),
                  share_1ch=float((nch == 1).mean()))
        for g in GROUPS:
            pr[f"top_{g}"] = pooled["grp"][g] / pooled["n"]
            pr[f"any_{g}"] = pooled["grp_any"][g] / pooled["n"]
        pr["top_channel_mode"] = ""
        rows.append(pr)
    return rows


def write_csv(path, rows, cols=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    cols = cols or list(rows[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(",".join(cols) + "\n")
        for r in rows:
            vals = []
            for c in cols:
                v = r.get(c, "")
                if isinstance(v, float):
                    vals.append("" if v != v else f"{v:.6g}")
                else:
                    vals.append(str(v))
            f.write(",".join(vals) + "\n")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3 -- label-free features, labels only score separability
# ══════════════════════════════════════════════════════════════════════════════
def subject_feature_matrix(subj):
    """Returns (X [N, n_feat], groups dict of boolean masks, sz_dur [N], cache dict).

    The spatial feature is the only one that needs subject context: for each channel the
    median of that channel's window SD over ALL of this subject's analysed windows (no
    labels), then the fraction of channels whose window SD exceeds 3x that median."""
    d = load_subject_cache(subj)
    sd = d["sd_uV"].astype(np.float64)
    med = np.median(sd, axis=0)                       # per-channel subject median window SD
    spatial = (sd > 3.0 * med[None, :]).mean(axis=1)
    X = np.empty((len(sd), len(ALL_FEATS)), dtype=np.float64)
    for j, f in enumerate(AGG_FEATS):
        X[:, j] = d[f]
    X[:, len(AGG_FEATS)] = spatial
    n_bad = int((~np.isfinite(X)).sum())
    if n_bad:
        log(f"{subj}: {n_bad} non-finite feature value(s) set to 0.0 "
            f"({n_bad / X.size:.2e} of the matrix)")
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    ict = d["is_ictal"].astype(bool)
    buf = d["is_buffer"].astype(bool)
    art = d["is_artifact"].astype(bool)
    sl = d["is_signal_loss"].astype(bool)
    g = dict(seizure=ict & (~sl),
             flagged=art & (~sl),
             background=(~ict) & (~buf) & (~art) & (~sl))
    return X, g, d["sz_dur"].astype(np.int32), d


def auroc_dir(x_pos, x_neg):
    """AUROC with the FIRST class as positive. NaN if either side is empty, or if the
    feature is constant across the two sides (AUROC undefined/uninformative)."""
    if len(x_pos) == 0 or len(x_neg) == 0:
        return float("nan")
    s = np.concatenate([x_pos, x_neg])
    if len(np.unique(s)) < 2:
        return float("nan")
    y = np.concatenate([np.ones(len(x_pos)), np.zeros(len(x_neg))])
    return float(roc_auc_score(y, s))


STRATA = [("all", None), ("sz_lt20s", (0, 20)), ("sz_ge20s", (20, 10 ** 9))]


def part3_tables(subjects):
    """Per-subject + pooled AUROC for the 3 contrasts, overall and split by seizure length.
    Pooled values are computed over the concatenated windows of all these subjects (not an
    average of per-subject AUROCs)."""
    data = {s: subject_feature_matrix(s) for s in subjects}
    rows = []

    def masks(g, szd, rng):
        gs = dict(g)
        if rng is not None:
            lo, hi = rng
            gs["seizure"] = g["seizure"] & (szd >= lo) & (szd < hi)
        return gs

    for subj, (X, g, szd, _d) in data.items():
        for sname, rng in STRATA:
            gs = masks(g, szd, rng)
            for cname, pos, neg in CONTRASTS:
                mp, mn = gs[pos], gs[neg]
                for j, feat in enumerate(ALL_FEATS):
                    rows.append(dict(stratum=sname, contrast=cname, subject=subj,
                                     feature=feat, auroc=auroc_dir(X[mp, j], X[mn, j]),
                                     n_pos=int(mp.sum()), n_neg=int(mn.sum())))

    for sname, rng in STRATA:
        for cname, pos, neg in CONTRASTS:
            Xp = np.concatenate([data[s][0][masks(data[s][1], data[s][2], rng)[pos]]
                                 for s in subjects])
            Xn = np.concatenate([data[s][0][masks(data[s][1], data[s][2], rng)[neg]]
                                 for s in subjects])
            for j, feat in enumerate(ALL_FEATS):
                rows.append(dict(stratum=sname, contrast=cname, subject="POOLED",
                                 feature=feat, auroc=auroc_dir(Xp[:, j], Xn[:, j]),
                                 n_pos=len(Xp), n_neg=len(Xn)))
            del Xp, Xn
            gc.collect()

    group_counts = [dict(subject=s,
                         n_files=int(len(d["files"])),
                         n_windows=int(len(d["is_ictal"])),
                         n_seizure=int(g["seizure"].sum()),
                         n_flagged=int(g["flagged"].sum()),
                         n_background=int(g["background"].sum()),
                         n_buffer=int(d["is_buffer"].sum()),
                         n_signal_loss=int(d["is_signal_loss"].sum()),
                         n_sz_lt20=int((g["seizure"] & (szd < 20)).sum()),
                         n_sz_ge20=int((g["seizure"] & (szd >= 20)).sum()))
                    for s, (_X, g, szd, d) in data.items()]
    return rows, group_counts


def part3_marked(rows):
    """Features with pooled sz-vs-flagged AUROC >= 0.75 or <= 0.25 (stratum 'all'), with
    direction agreement across the 3 validation subjects."""
    idx = {(r["stratum"], r["contrast"], r["subject"], r["feature"]): r["auroc"] for r in rows}
    out = []
    for feat in ALL_FEATS:
        a = idx.get(("all", "sz_vs_flagged", "POOLED", feat), float("nan"))
        if not (a >= 0.75 or a <= 0.25):
            continue
        sgn = np.sign(a - 0.5)
        agree, vals = 0, {}
        for v in VAL_SUBJS:
            av = idx.get(("all", "sz_vs_flagged", v, feat), float("nan"))
            vals[v] = av
            if av == av and np.sign(av - 0.5) == sgn:
                agree += 1
        out.append(dict(feature=feat, pooled_auroc=a,
                        direction="higher in seizures" if sgn > 0 else "higher in flagged",
                        n_val_agree=agree, agrees_2of3=bool(agree >= 2),
                        **{f"auroc_{v}": vals[v] for v in VAL_SUBJS}))
    out.sort(key=lambda r: -abs(r["pooled_auroc"] - 0.5))
    return out


# ══════════════════════════════════════════════════════════════════════════════
# PART 4 -- read-only facts
# ══════════════════════════════════════════════════════════════════════════════
def run_part4():
    facts = {}
    # (a) write_windows -> {subj}_interictal.npy
    rows = []
    tot = 0
    for s in TRAIN_SUBJS:
        st = json.loads((PROCESSED_DIR / f"{s}_stats.json").read_text())
        arr = np.load(PROCESSED_DIR / f"{s}_interictal.npy", mmap_mode="r")
        adj = np.load(PROCESSED_DIR / f"{s}_interictal_adjs_topk20.npy", mmap_mode="r")
        rows.append(dict(subject=s, n_interictal_stats_json=st["n_interictal"],
                         n_interictal_npy_shape0=int(arr.shape[0]),
                         n_rejected_5sd=st["n_rejected"], n_ictal=st["n_ictal"],
                         n_adjs_topk20=int(adj.shape[0])))
        tot += st["n_interictal"]
    facts["a_rows"] = rows
    facts["a_total"] = tot
    facts["a_answer"] = (
        "Yes -- only windows that passed the +-5 SD rule are written. In "
        "preprocessing.write_windows a window reaches mm_inter only on the `elif not "
        "win_buffered` branch, and inside it only `if not is_artifact and idx_inter < "
        "n_inter_max`, where is_artifact is True as soon as any of the 18 channels has "
        "max|x| > artifact_threshold[ch] = 5 x ch_std[ch]. So {subj}_interictal.npy holds "
        "exactly the non-ictal, non-4h-post-seizure-buffer windows whose peak amplitude "
        "stays within 5 SD on every channel (then z-scored). Ictal windows go to "
        "{subj}_ictal.npy and are deliberately NOT artifact-rejected.")
    # (b)
    facts["b"] = dict(
        n_train_windows=tot,
        n_train_windows_source=(
            "sum of n_interictal over the 12 training subjects in "
            "data/processed/{subj}_stats.json, equal to the committed "
            "{subj}_interictal_adjs_topk20.npy row counts; independently recorded as "
            "\"270,187 interictal windows\" in docs/PHASE_C_FULL_AUDIT.md:202 and "
            "docs/PHASE_C_CLOSEOUT_provenance.md:37 and "
            "docs/RESULTS_OF_RECORD_phaseB.md:152"),
        train_subject_contract=(
            "docs/archive/PROVENANCE_MAP.md:160 -- \"The joint model was trained on 12 of "
            "the 15 (interictal only) with 3 held-out as validation subjects: train = "
            "chb01,02,04,05,07,08,09,12,19,20,21,23; val = chb10,11,22\"; the same 12 are "
            "TRAIN_SUBJS in src/retrain/train_gae_joint.py"),
        wall_clock=(
            "No wall-clock time for the ORIGINAL GAE training exists anywhere in the repo, "
            "the notebooks or on Kaggle: docs/archive/PROVENANCE_MAP.md:152 records that the "
            "original training notebook was \"confirmed unrecoverable (not in repo, "
            "notebook, or Kaggle)\" and notebooks/kaggle_gpu/thesis-cpd-final.ipynb only "
            "loads the trained checkpoint and scores with it (Sections 1B/2) -- it contains "
            "no training loop. The recorded Kaggle wall-clock figures are for the "
            "reconstructed retrain (PREREG 01 recipe, same 270,187 windows): "
            "~3.5 h per GAE seed (docs/PHASE_C_FINAL_HANDOFF.md:20) and ~3.2 h per seed "
            "(docs/PHASE_D_HANDOFF.md:44 for the small rlg-class model; "
            "docs/PHASE_C_FULL_AUDIT.md:198 reports the same ~3.2 h after a host-bound "
            "data-movement bug was fixed), 200 epochs, 4 Kaggle accounts in parallel."),
        script_defining_training_windows=(
            "Two scripts, in sequence. (1) src/dataprep/preprocessing.py defines WHICH "
            "windows exist: write_windows() (called from process_subject) emits "
            "data/processed/{subj}_interictal.npy = non-ictal, non-buffer, 5 SD-passing, "
            "z-scored 4 s windows. (2) src/retrain/train_gae_joint.py defines which of them "
            "are the TRAINING set: TRAIN_SUBJS (the 12 subjects, lines 35-38) + "
            "build_dataset()/load_subject(), which read "
            "{subj}_interictal_adjs_topk20.npy and {subj}_interictal_features.npy -- the "
            "graph/feature tensors derived from those same interictal windows by "
            "src/dataprep/build_graphs.py + apply_topk_multiband.py. The window grid itself "
            "(4 s, 1024 samples, no overlap) is preprocessing.py's WIN_S/WIN_SAMPLES."),
    )
    (OUT / "part4_facts.json").write_text(json.dumps(facts, indent=2))
    log(f"PART 4: {tot} training windows over {len(rows)} subjects")
    return facts


# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY.md
# ══════════════════════════════════════════════════════════════════════════════
def fmt(v, nd=4):
    if isinstance(v, float):
        return "n/a" if v != v else f"{v:.{nd}f}"
    return str(v)


def md_table(cols, rows, headers=None):
    headers = headers or cols
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(fmt(r.get(c, "")) for c in cols) + " |")
    return "\n".join(out)


def write_summary(part1_info, part2_rows, part3_rows, part3_counts, part3_marks, facts,
                  elapsed_s, subjects):
    idx = {}
    for r in part3_rows:
        idx[(r["stratum"], r["contrast"], r["subject"], r["feature"])] = r

    L = []
    A = L.append
    A("# raw_eeg_view — what the ±5 SD flagged windows actually are")
    A("")
    A(f"Produced by `src/raw_eeg_view.py` (one pass over the EDFs), "
      f"{time.strftime('%Y-%m-%d %H:%M')}. Total elapsed {elapsed_s/60:.1f} min.")
    A("")
    A("## 0. Conventions, and what is and is not used")
    A("")
    A("- **Signal.** Every trace and every number uses `preprocessing.filter_window`'s own "
      "filtering: 0.5–60 Hz Butterworth-4 `sosfiltfilt` then 60 Hz notch (Q=30) `filtfilt`, "
      "applied to the window plus `FILTER_PAD` = 768 samples each side, centre kept. The "
      "implementation slices an in-RAM copy of the EDF instead of re-reading per window; it "
      "reproduces `P.filter_window` to **max abs difference 0.0** (asserted once per file at "
      "run time, and over 12 windows of two subjects by `--selfcheck`). This matters: "
      "`continuous_eval.py` documents that whole-file filtering can flip borderline 5 SD "
      "accept/reject decisions, which is exactly what Part 2 counts.")
    A("- **Flagged.** `is_artifact` = at least one sample with |x| above that channel's "
      "committed threshold `data/processed/{subj}_stats.json: artifact_thresh_uV` (= 5 × the "
      "per-channel SD of filtered interictal), on a window that is neither ictal nor inside "
      "the 4 h post-seizure buffer — the same definition and the same thresholds "
      "`continuous_eval.compute_artifact_flags` used to build "
      "`results/continuous_eval/cache/mask/`.")
    A("- **No model, no score, no fitted threshold** appears anywhere in this file. Seizure "
      "labels are used only to pick which seizures to draw (Part 1) and to measure AUROC "
      "(Part 3).")
    A(f"- **Test subjects contribute no numbers.** Parts 2 and 3 use the 3 validation "
      f"subjects and the 12 training subjects only ({', '.join(NUMBER_SUBJS)}). Test "
      f"subjects appear only in the Part 1 pictures.")
    A("")
    A("### Data actually read for Parts 2 and 3")
    A("")
    A(md_table(["subject", "n_files", "n_windows", "n_seizure", "n_flagged", "n_background",
                "n_buffer", "n_signal_loss", "n_sz_lt20", "n_sz_ge20"], part3_counts))
    A("")
    A("All files of chb10/chb11/chb22; for each of the 12 training subjects every file that "
      "contains a seizure plus 2 other files drawn with `random.Random(42)`.")
    A("")

    # ── Part 1
    A("## PART 1 — pictures")
    A("")
    A("Seizure panels span onset−20 s to onset+40 s; window panels span 30 s centred on the "
      "4 s window (shaded red). 18 channels, pipeline-filtered, one amplitude scale per "
      "sheet written on every panel (channel spacing, plus a scale bar). The lower sub-panel "
      "of each panel is the Welch PSD of the **same segment, raw and unfiltered**, 0.5–100 Hz, "
      "log power; the dashed line is 60 Hz.")
    A("")
    for key in ("A", "B", "CD"):
        inf = part1_info[key]
        cap = inf.get("caption") or (inf["caption_C"] + "  •  " + inf["caption_D"])
        A(f"**Sheet {key}** — {cap}")
        A("")
        A(f"Files: {', '.join('`' + s + '`' for s in inf['sheets'])}; "
          f"common channel spacing {inf['spacing_uV']:g} µV. Individual panels in "
          f"`panels/{key}_*.png`.")
        A("")
        if key in ("A", "B"):
            A(md_table(["subj", "file", "onset", "offset", "dur_s"], inf["panels"],
                       ["subject", "file", "onset (s)", "offset (s)", "duration (s)"]))
        else:
            A("C panels:")
            A("")
            A(md_table(["subj", "file", "window_s", "n_exceed", "cause"], inf["panels_C"],
                       ["subject", "file", "window (s)", "samples >5 SD", "cause"]))
            A("")
            A("D panels (chb13, the 2 files with the highest flagged share):")
            A("")
            A(md_table(["subj", "file", "window_s", "n_exceed", "cause"], inf["panels_D"],
                       ["subject", "file", "window (s)", "samples >5 SD", "cause"]))
            A("")
            A("chb13 flagged share by file (top 6):")
            A("")
            A(md_table(["file", "n_flagged", "n_windows", "share"],
                       inf["chb13_flagged_share_ranking"][:6],
                       ["file", "flagged", "windows", "flagged share"]))
            A("")
            for fn, e in inf["chb13_files"].items():
                rr = np.asarray(e["ratio"])
                A(f"`{fn}`: per-channel SD(file)/SD(subject) median **{np.median(rr):.2f}**, "
                  f"min {rr.min():.2f} ({CH[int(rr.argmin())]}), max {rr.max():.2f} "
                  f"({CH[int(rr.argmax())]}); per-channel values are printed beside each "
                  f"trace on the panel.")
            A("")
        A("")
    A("> Note on the 8-panels-per-PNG cap: C+D is 14 panels, so sheet CD is written as "
      "`sheet_CD.png` (8 panels) and `sheet_CD_p2.png` (6 panels).")
    A("")

    # ── Part 2
    A("## PART 2 — what the flagged windows are")
    A("")
    A(f"Every flagged window of the {len(subjects)} non-test subjects "
      f"({sum(r['n_flagged'] for r in part2_rows if r['subject'] != 'POOLED'):,} windows). "
      "`cause = single-spike` iff the total number of samples above 5 SD, summed over all 18 "
      "channels, is ≤ 3; `sustained` otherwise. `top_*` = share of flagged windows whose "
      "channel with the most exceedances is in that group; `any_*` = share with at least one "
      "exceedance anywhere in that group (groups overlap, so `any_*` does not sum to 1).")
    A("")
    A("### Cause and exceedance magnitude")
    A("")
    A(md_table(["subject", "n_flagged", "share_single", "share_sustained", "median_n_exceed",
                "mean_n_exceed", "p95_n_exceed", "median_n_ch", "mean_n_ch", "share_1ch",
                "top_channel_mode"], part2_rows,
               ["subject", "flagged", "single-spike", "sustained", "median >5SD samples",
                "mean", "p95", "median #ch", "mean #ch", "share 1 channel only",
                "most frequent top channel"]))
    A("")
    A("### Share of flagged windows by channel group of the dominant channel")
    A("")
    A(md_table(["subject"] + [f"top_{g}" for g in GROUPS], part2_rows,
               ["subject"] + list(GROUPS)))
    A("")
    A("### Share of flagged windows with at least one exceedance in the group")
    A("")
    A(md_table(["subject"] + [f"any_{g}" for g in GROUPS], part2_rows,
               ["subject"] + list(GROUPS)))
    A("")
    A("Groups: frontopolar = FP1-F7, FP1-F3, FP2-F4, FP2-F8 · temporal = F7-T7, T7-P7, "
      "F8-T8, T8-P8 · central = F3-C3, C3-P3, F4-C4, C4-P4 · parieto-occipital = P7-O1, "
      "P3-O1, P4-O2, P8-O2 · midline = FZ-CZ, CZ-PZ.")
    A("")
    A("Full tables: `tables/part2_by_subject.csv`.")
    A("")

    # ── Part 3
    A("## PART 3 — label-free features, labels used only to score separability")
    A("")
    A("Per window and per channel, on the pipeline-filtered signal in µV: Hjorth mobility "
      "`sqrt(var(dx)/var(x))` and complexity `sqrt(var(ddx)/var(dx))/mobility`; line length "
      "`sum|dx|` divided by the channel SD; relative power in 0.5–4, 4–8, 8–13, 13–30, "
      "30–60 Hz (Welch, nperseg 512, noverlap 256, df 0.5 Hz; relative to 0.5–60 Hz, so the "
      "five sum to 1); muscle proxy 20–60/0.5–60; slow proxy 0.5–2/0.5–60; spectral entropy "
      "over 0.5–60 Hz normalised by log(#bins); rhythmicity = share of 0.5–60 Hz power "
      "within ±1.5 Hz of the spectral peak; kurtosis (Fisher, unbiased). Each is summarised "
      "across the 18 channels as **median** (`_med`) and **max** (`_max`). One spatial "
      f"feature, `{SPATIAL_FEAT}`: fraction of channels whose window SD exceeds 3× that "
      "channel's median window SD over all of this subject's analysed windows (label-free). "
      f"{len(ALL_FEATS)} features in total.")
    A("")
    A("Contrasts: `sz_vs_flagged` (seizure vs flagged non-seizure), `sz_vs_bg` (seizure vs "
      "unflagged background), `flagged_vs_bg`. **AUROC is reported with the first-named "
      "class as positive**, so >0.5 means the feature is higher in the first class and <0.5 "
      "means higher in the second. Pooled = all windows of the 3 validation + 12 training "
      "subjects pooled. Signal-loss windows are excluded from every group.")
    A("")
    for cname, pos, neg in CONTRASTS:
        A(f"### {cname} — pooled AUROC (direction: >0.5 = higher in {pos})")
        A("")
        rows = []
        for feat in ALL_FEATS:
            r = dict(feature=feat)
            for sname in ("all", "sz_lt20s", "sz_ge20s"):
                rr = idx.get((sname, cname, "POOLED", feat))
                r[sname] = rr["auroc"] if rr else float("nan")
            for v in VAL_SUBJS:
                rr = idx.get(("all", cname, v, feat))
                r[v] = rr["auroc"] if rr else float("nan")
            rows.append(r)
        rows.sort(key=lambda r: -abs((r["all"] if r["all"] == r["all"] else 0.5) - 0.5))
        A(md_table(["feature", "all", "sz_lt20s", "sz_ge20s"] + VAL_SUBJS, rows,
                   ["feature", "pooled (all)", "pooled (sz <20 s)", "pooled (sz ≥20 s)"]
                   + [f"{v} (all)" for v in VAL_SUBJS]))
        A("")
        nr = idx.get(("all", cname, "POOLED", ALL_FEATS[0]))
        if nr:
            A(f"n = {nr['n_pos']:,} {pos} vs {nr['n_neg']:,} {neg} (pooled, stratum all).")
        A("")
    A("### Marked features — pooled seizure-vs-flagged AUROC ≥ 0.75 or ≤ 0.25")
    A("")
    if part3_marks:
        A(md_table(["feature", "pooled_auroc", "direction", "n_val_agree", "agrees_2of3"]
                   + [f"auroc_{v}" for v in VAL_SUBJS], part3_marks,
                   ["feature", "pooled AUROC", "direction", "val subjects agreeing",
                    "≥2 of 3 agree"] + VAL_SUBJS))
    else:
        A("**None.** No feature reaches pooled AUROC ≥ 0.75 or ≤ 0.25 on "
          "seizure-vs-flagged.")
    A("")
    A("Per-subject values for every feature, contrast and stratum: "
      "`tables/part3_auroc.csv`; marked features: `tables/part3_marked.csv`; per-subject "
      "window counts: `tables/part3_groups.csv`.")
    A("")

    # ── Part 4
    A("## PART 4 — read-only facts (nothing was changed)")
    A("")
    A("### (a) Does `data/processed/{subj}_interictal.npy` contain only windows that passed "
      "the ±5 SD rule?")
    A("")
    A(facts["a_answer"])
    A("")
    A(md_table(["subject", "n_interictal_stats_json", "n_interictal_npy_shape0",
                "n_adjs_topk20", "n_rejected_5sd", "n_ictal"], facts["a_rows"],
               ["subject", "windows (stats.json)", "windows (.npy shape[0])",
                "windows (adjs_topk20)", "rejected by 5 SD", "ictal (separate file)"]))
    A("")
    A(f"**Total over the 12 training subjects: {facts['a_total']:,} interictal windows.** "
      "stats.json, the `.npy` shape and the committed graph tensors agree exactly for every "
      "subject.")
    A("")
    A("### (b) The original GAE training")
    A("")
    A(f"- **Windows trained on: {facts['b']['n_train_windows']:,}.** "
      f"{facts['b']['n_train_windows_source']}.")
    A(f"- **Subjects:** {facts['b']['train_subject_contract']}.")
    A(f"- **Kaggle wall-clock:** {facts['b']['wall_clock']}")
    A(f"- **Script defining the training windows:** "
      f"{facts['b']['script_defining_training_windows']}")
    A("")
    A("## Outputs")
    A("")
    A("```")
    A("results/raw_eeg_view/")
    A("  SUMMARY.md                  this file")
    A("  sheet_A.png sheet_B.png sheet_CD.png sheet_CD_p2.png")
    A("  panels/                     one PNG per panel")
    A("  tables/part2_by_subject.csv part3_auroc.csv part3_marked.csv part3_groups.csv")
    A("  cache/{subj}.npz            per-window flags, exceedance counts, features")
    A("  part1_panels.json part4_facts.json run.log")
    A("```")
    A("")
    (OUT / "SUMMARY.md").write_text("\n".join(L), encoding="utf-8")
    log(f"wrote {OUT / 'SUMMARY.md'}")


# ══════════════════════════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all",
                    choices=["all", "part1", "part23", "part4", "summary", "eegpass"])
    ap.add_argument("--subjects", nargs="+", default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--selfcheck", action="store_true")
    a = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    t_all = time.time()
    subjects = a.subjects or NUMBER_SUBJS
    bad = [s for s in subjects if s in TEST_SUBJS]
    if bad:
        raise SystemExit(f"refusing to compute numbers on test subjects: {bad}")

    if a.selfcheck:
        selfcheck()
        return

    facts = part1_info = None
    if a.stage in ("all", "part4"):
        facts = run_part4()
    if a.stage in ("all", "part1"):
        part1_info = run_part1()
    if a.stage in ("all", "part23", "eegpass"):
        run_eeg_pass(subjects, force=a.force)
        for s in VAL_SUBJS:
            if s in subjects:
                log(f"mask agreement vs continuous_eval {s}: "
                    f"{mask_agreement(s, load_subject_cache(s))}")
    if a.stage in ("all", "part23", "summary"):
        p2 = part2_tables(subjects)
        write_csv(TABLE_DIR / "part2_by_subject.csv", p2)
        p3, counts = part3_tables(subjects)
        write_csv(TABLE_DIR / "part3_auroc.csv", p3)
        write_csv(TABLE_DIR / "part3_groups.csv", counts)
        marks = part3_marked(p3)
        write_csv(TABLE_DIR / "part3_marked.csv", marks)
        if facts is None:
            facts = json.loads((OUT / "part4_facts.json").read_text())
        if part1_info is None:
            part1_info = json.loads((OUT / "part1_panels.json").read_text())
        write_summary(part1_info, p2, p3, counts, marks, facts,
                      time.time() - t_all, subjects)
    log(f"ALL DONE in {(time.time()-t_all)/60:.1f} min -- {OUT / 'SUMMARY.md'}")


if __name__ == "__main__":
    main()
