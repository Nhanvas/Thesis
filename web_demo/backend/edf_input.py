"""edf_input.py — C5 Step 2 (results/c5_szscan/DESIGN_STEP2.md C4–C7): any EDF in, the 18 thesis derivations out.

  bipolar input      (CHB-MIT: the 18 derivation labels present)  -> preprocessing.open_edf, exactly as before Step 2;
                     a rate other than 256 Hz is resampled with scipy's resample_poly (as for every other input)
  referential input  (Siena, hospital: the 19 electrodes of the 10-20 system present, names normalised as
                     x1_external.load_18: upper case, 'EEG' and spaces removed, T3/T4/T5/T6 -> T7/T8/P7/P8; a second
                     try also strips a reference suffix such as '-REF' or '-LE')
                     -> only those 19 electrodes are read -> optional spherical-spline interpolation of bad electrodes
                     (MNE, as src/v9_clinical_run.clin_load_18) -> the 18 bipolar differences -> resample_poly to
                     256 Hz. Without interpolation this is x1_external.load_18's non-CHB branch operation for operation
                     (gate G3 checks equality on every Siena file).

Written rules (DESIGN_STEP2.md §3, fixed before any run):
  mains suggestion   every 10th 4-s window of the 18 derivations; per window and channel the mean power of the
                     1-Hz band around 50 (60) Hz divided by the median power of its flanks 45-49 + 51-55 Hz
                     (55-59 + 61-65 Hz); median over all windows and channels -> r50, r60; the larger wins if it is
                     >= 3 and the two differ; otherwise no suggestion (the user chooses).
  bad electrode      (referential only) robust amplitude = IQR / 1.349 of each electrode, band-passed 0.5-60 Hz,
                     over every 10th 4-s window (3-s padding, as the statistics windows); robust z across the 19
                     electrodes = (amp - median) / (1.4826 MAD); bad if z > 5 (PREP's deviation default) or
                     amp < 0.1 µV (flat); more than 3 bad -> the file is refused.
  truncated header   records used = those present in the file; a notice gives the declared and the present duration.
  duplicate labels   the first signal with a label (preprocessing.open_edf, SzCORE's converter).

The EDF header is read here by a small reader written from the specification (Kemp et al. 1992,
DOI 10.1016/0013-4694(92)90009-7) — only the signal labels, rates and record counts are used; the patient, recording
and date fields are never returned.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from scipy.signal import butter, resample_poly, sosfiltfilt

import pipeline_demo as pd

P = pd.preprocessing
X1 = pd.X1
FS = P.FS                                   # 256
WIN = P.WIN_SAMPLES                         # 1024
BIPOLAR = X1.BIPOLAR                        # [(a, b)] x 18, thesis order
ELECTRODES = sorted({e for pair in BIPOLAR for e in pair})   # the 19 electrodes, x1_external order
ALIASES = X1.SIENA_MAP                      # T3->T7, T4->T8, T5->P7, T6->P8
REF_SUFFIXES = ("-REF", "-LE", "-AVG", "-AV", "-CAR", "-A1", "-A2", "-M1", "-M2", "-REF1")
SUB = P.STATS_SUBSAMPLE                     # every 10th window
BAD_Z, FLAT_V, MAX_BAD = 5.0, 0.1e-6, 3
MAINS_MIN_RATIO = 3.0


class InputError(ValueError):
    """User-facing refusal; the message is shown as the file's error toast."""


# ════════════════════════════════════════════════════════════════════ header (specification reader)
def header(path) -> dict:
    path = Path(path)
    with open(path, "rb") as fh:
        h = fh.read(256)
        if len(h) < 256:
            raise InputError("Not an EDF file (shorter than its 256-byte header).")
        try:
            ns = int(h[252:256].decode("ascii").strip())
            hdr_bytes = int(h[184:192].decode("ascii").strip())
            n_rec_hdr = int(h[236:244].decode("ascii").strip())
            rec_dur = float(h[244:252].decode("ascii").strip())
        except ValueError as exc:
            raise InputError("Not an EDF file (header fields unreadable).") from exc
        s = fh.read(ns * 256)
    if ns <= 0 or len(s) < ns * 256 or rec_dur <= 0:
        raise InputError("Not an EDF file (signal table incomplete).")

    def field(off, width, i):
        a = ns * off + i * width
        return s[a:a + width].decode("latin-1").strip()
    labels = [field(0, 16, i) for i in range(ns)]
    nsamp = [int(field(216, 8, i)) for i in range(ns)]
    rec_samples = sum(nsamp)
    size = path.stat().st_size
    n_rec_file = max(0, (size - hdr_bytes) // (2 * rec_samples)) if rec_samples else 0
    return dict(labels=labels, nsamp=nsamp, rec_dur=rec_dur, n_rec_hdr=n_rec_hdr, n_rec_file=int(n_rec_file))


def truncation_notice(h: dict) -> str:
    if h["n_rec_hdr"] > 0 and h["n_rec_hdr"] > h["n_rec_file"]:
        dh, ph = h["n_rec_hdr"] * h["rec_dur"] / 3600, h["n_rec_file"] * h["rec_dur"] / 3600
        return (f"The file header declares {dh:.2f} h but the file holds {ph:.2f} h of signal; "
                f"the {ph:.2f} h present are used.")
    return ""


# ════════════════════════════════════════════════════════════════════ montage detection
def norm_label(ch: str) -> str:
    """x1_external.load_18's normalisation."""
    n = ch.upper().replace("EEG", "").strip().replace(" ", "")
    return ALIASES.get(n, n)


def norm_label_ext(ch: str) -> str:
    n = norm_label(ch)
    for suf in REF_SUFFIXES:
        if n.endswith(suf) and len(n) > len(suf):
            n = n[: -len(suf)]
            break
    return ALIASES.get(n, n)


def classify(labels: list[str]) -> tuple[str | None, dict]:
    """('bipolar', {}) | ('referential', {electrode: original label}) | (None, {})."""
    up = {l.upper().strip() for l in labels}
    if all(c in up for c in P.COMMON_CHANNELS):
        return "bipolar", {}
    for fn in (norm_label, norm_label_ext):
        names = {}
        for ch in labels:
            if fn is norm_label:
                names[fn(ch)] = ch                # x1_external.load_18's own dict (G3: identical to the record)
            else:
                names.setdefault(fn(ch), ch)      # first signal with a name (duplicate labels)
        if all(e in names for e in ELECTRODES):
            return "referential", {e: names[e] for e in ELECTRODES}
    return None, {}


# ════════════════════════════════════════════════════════════════════ written rules
def _sampled_windows(n_windows: int) -> np.ndarray:
    return np.flatnonzero((np.arange(n_windows) + 1) % SUB == 0)


def bad_electrode_table(X, fs: int, n: int | None = None) -> list[dict]:
    """X = [19, n] volts at fs (ELECTRODES order) or a callable (start, stop) -> [19, stop-start] that reads them
    from the file (memory-light); -> per electrode amp (V), robust z, bad flag (rule above)."""
    get = X if callable(X) else (lambda a, b: X[:, a:b])
    n = X.shape[1] if n is None else n
    win, pad = int(4 * fs), int(3 * fs)
    nw = n // win
    idx = _sampled_windows(nw)
    if len(idx) == 0:
        raise InputError("Recording too short (fewer than 10 windows of 4 s).")
    sos = butter(4, [0.5, 60.0], btype="bandpass", fs=fs, output="sos")
    S = None                                     # = np.concatenate of the windows, filled in place (memory-light)
    for k, i in enumerate(idx):
        a, b = max(0, i * win - pad), min(n, (i + 1) * win + pad)
        f = sosfiltfilt(sos, get(a, b), axis=1)
        if S is None:
            S = np.empty((f.shape[0], len(idx) * win))
        S[:, k * win:(k + 1) * win] = f[:, i * win - a:i * win - a + win]
    q = np.array([np.percentile(row, [75, 25]) for row in S])     # per electrode = the 2-D call (synthetic test)
    q75, q25 = q[:, 0], q[:, 1]
    amp = (q75 - q25) / 1.349
    med = np.median(amp)
    mad = 1.4826 * np.median(np.abs(amp - med))
    z = (amp - med) / mad if mad > 0 else np.zeros_like(amp)
    return [dict(electrode=e, amp_uv=float(a * 1e6), z=float(zz), bad=bool(zz > BAD_Z or a < FLAT_V))
            for e, a, zz in zip(ELECTRODES, amp, z)]


def mains_ratios(data18: np.ndarray) -> tuple[float, float]:
    nw = data18.shape[1] // WIN
    idx = _sampled_windows(nw)
    if len(idx) == 0:
        return float("nan"), float("nan")
    f = np.fft.rfftfreq(WIN, 1 / FS)                         # 0.25-Hz bins
    hann = np.hanning(WIN)

    def ratio(pw, c, lo_flank, hi_flank):
        band = pw[:, :, (f >= c - 0.5) & (f <= c + 0.5)].mean(axis=2)
        fl = pw[:, :, ((f >= lo_flank[0]) & (f <= lo_flank[1])) | ((f >= hi_flank[0]) & (f <= hi_flank[1]))]
        return band / np.maximum(np.median(fl, axis=2), 1e-300)
    r50, r60 = [], []
    for k in range(0, len(idx), 200):                        # 200 windows at a time (memory-light)
        seg = np.stack([np.asarray(data18[:, i * WIN:(i + 1) * WIN]) for i in idx[k:k + 200]])   # [w, 18, 1024]
        seg = seg - seg.mean(axis=2, keepdims=True)
        pw = np.abs(np.fft.rfft(seg * hann, axis=2)) ** 2
        r50.append(ratio(pw, 50.0, (45, 49), (51, 55)))
        r60.append(ratio(pw, 60.0, (55, 59), (61, 65)))
    return float(np.median(np.concatenate(r50))), float(np.median(np.concatenate(r60)))


def suggest_mains(data18: np.ndarray) -> tuple[float | None, float, float]:
    r50, r60 = mains_ratios(data18)
    if not (np.isfinite(r50) and np.isfinite(r60)) or max(r50, r60) < MAINS_MIN_RATIO or r50 == r60:
        return None, r50, r60
    return (50.0 if r50 > r60 else 60.0), r50, r60


# ════════════════════════════════════════════════════════════════════ loaders
def _resample(data: np.ndarray, fs: int) -> np.ndarray:
    if fs == FS:
        return data
    g = math.gcd(fs, FS)
    return resample_poly(data, FS // g, fs // g, axis=1)


BLOCK_S = 600            # seconds read per block (19 electrodes x 600 s x 512 Hz x 8 B = 47 MB)


def _alloc(shape, workdir, name):
    """RAM array, or a float64 .npy memory map in `workdir` (deleted by the caller) for long recordings."""
    if workdir is None:
        return np.empty(shape, np.float64), None
    import os
    import tempfile
    fd, tmp = tempfile.mkstemp(prefix=f"_c5_{name}_", suffix=".npy", dir=str(workdir))
    os.close(fd)
    path = Path(tmp)
    return np.lib.format.open_memmap(path, mode="w+", dtype=np.float64, shape=shape), path


def drop_temp(path) -> None:
    """Delete a temporary disk copy. On Windows a file still memory-mapped cannot be deleted; then it is left for the
    caller's folder clean-up instead of hiding the error that is being raised (Step 2a fix)."""
    if path is None:
        return
    import gc
    gc.collect()
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass


def interpolation_matrix(names: dict, bads: list) -> np.ndarray:
    """MNE's spherical-spline interpolation (interpolate_bads, mode 'accurate', standard 10-20 positions) as a linear
    map [n_bad, 19]: obtained by interpolating the 19 unit vectors, so applying it block by block equals MNE's
    whole-recording interpolation up to floating-point rounding (synthetic test)."""
    import mne
    info = mne.create_info(list(ELECTRODES), sfreq=float(FS), ch_types="eeg")
    raw = mne.io.RawArray(np.eye(len(ELECTRODES)), info, verbose="ERROR")
    raw.set_montage(mne.channels.make_standard_montage("standard_1020"), on_missing="ignore", match_case=False)
    raw.info["bads"] = list(bads)
    raw.interpolate_bads(reset_bads=True, mode="accurate", verbose="ERROR")
    out = raw.get_data()
    return out[[ELECTRODES.index(b) for b in bads]]


def load_bipolar(path):
    """CHB-MIT path, unchanged: preprocessing.open_edf -> get_data (volts)."""
    raw = P.open_edf(str(path))
    if raw is None:
        raise InputError("One or more of the 18 derivations is missing.")
    fs = int(round(raw.info["sfreq"]))
    if abs(raw.info["sfreq"] - fs) > 1e-6:
        raise InputError(f"Sampling rate {raw.info['sfreq']} Hz is not an integer rate.")
    data = np.asarray(raw.get_data(), dtype=np.float64)     # get_data is float64; no second copy (Step 2a fix)
    return _resample(data, fs), raw.info["meas_date"], fs


def load_referential(path, names: dict, interpolate: bool, workdir=None):
    """The 19 electrodes -> (bad-electrode table) -> optional interpolation -> 18 differences -> 256 Hz.

    Memory-light (C5 Step 2a, measured: the whole-recording version peaked at 15.1 GB on an 11.7-h 512-Hz Siena file):
    the electrodes are read in blocks of BLOCK_S seconds (MNE, not preloaded), the 18 differences are written at the
    file's own rate into a float64 array (on disk in `workdir` when given), then resampled one derivation at a time.
    Without interpolation the values equal x1_external.load_18 bit for bit (block reads, per-row resample_poly and
    the differences are each exact; gate G3)."""
    import mne
    raw = mne.io.read_raw_edf(str(path), preload=False, verbose="ERROR")
    fs_f = float(raw.info["sfreq"])
    fs = int(round(fs_f))
    if abs(fs_f - fs) > 1e-6:
        raise InputError(f"Sampling rate {fs_f} Hz is not an integer rate.")
    meas_date = raw.info["meas_date"]
    picks = [names[e] for e in ELECTRODES]
    n = int(raw.n_times)

    def get(a, b):
        return raw.get_data(picks=picks, start=a, stop=b)
    table = bad_electrode_table(get, fs, n)
    bads = [t["electrode"] for t in table if t["bad"]]
    if len(bads) > MAX_BAD:
        raise InputError(f"{len(bads)} electrodes look disconnected or flat ({', '.join(bads)}); "
                         f"more than {MAX_BAD} cannot be interpolated.")
    M = interpolation_matrix(names, bads) if (bads and interpolate) else None
    bad_idx = [ELECTRODES.index(b) for b in bads]
    pos = {e: i for i, e in enumerate(ELECTRODES)}
    nat, nat_path = _alloc((len(BIPOLAR), n), workdir, "native")
    step = BLOCK_S * fs
    for a in range(0, n, step):
        b = min(n, a + step)
        X = get(a, b)
        if M is not None:
            X[bad_idx] = M @ X
        for r, (e1, e2) in enumerate(BIPOLAR):
            nat[r, a:b] = X[pos[e1]] - X[pos[e2]]
        del X
    del raw
    if fs == FS:
        data, data_path = nat, nat_path
    else:
        g = math.gcd(fs, FS)
        up, down = FS // g, fs // g
        n_out = -(-n * up // down)
        data, data_path = _alloc((len(BIPOLAR), n_out), workdir, "data")
        for r in range(len(BIPOLAR)):
            data[r] = resample_poly(np.asarray(nat[r]), up, down)
        del nat
        drop_temp(nat_path)
    return data, meas_date, fs, table, (bads if interpolate else []), bads, data_path


def load_any(path, mains="auto", interpolate=False, mains_fallback=None, workdir=None) -> tuple[np.ndarray, dict]:
    """-> (data [18, n] volts at 256 Hz, meta). meta: montage, fs_in, meas_date, notch_hz, mains_ratios, notices,
    bad (electrodes flagged), interpolated. Raises InputError with a user-facing message.
    mains_fallback (auto only): the study's mains frequency already decided by an earlier file, used when this
    file's own signal gives no suggestion (with a notice); a clear suggestion that differs is returned as such and
    refused by the caller."""
    h = header(path)
    montage, names = classify(h["labels"])
    if montage is None:
        raise InputError("Neither the 18 bipolar derivations nor the 19 electrodes of the 10-20 system were found.")
    notices = []
    tn = truncation_notice(h)
    if tn:
        notices.append(tn)
    meta = dict(montage=montage, bad=[], interpolated=[], electrodes=None, data_path=None)
    try:
        if montage == "bipolar":
            data, meas_date, fs = load_bipolar(path)
        else:
            data, meas_date, fs, table, interp, bads, data_path = load_referential(path, names, interpolate, workdir)
            meta.update(electrodes=table, bad=bads, interpolated=interp, data_path=data_path)
            if bads and interp:
                notices.append(f"Electrode(s) {', '.join(bads)} looked disconnected or flat and were interpolated "
                               f"from their neighbours.")
            elif bads:
                notices.append(f"Electrode(s) {', '.join(bads)} look disconnected or flat (not interpolated); "
                               f"derivations using them may raise false alarms.")
    except InputError:
        raise
    except Exception as exc:      # mne raises many kinds of errors on unreadable files
        raise InputError("The file could not be read as EDF.") from exc
    try:
        return _finish(data, meta, notices, fs, meas_date, mains, mains_fallback)
    except BaseException as exc:
        if meta["data_path"] is not None:            # no temporary disk copy is left behind on a refused file
            import traceback
            traceback.clear_frames(exc.__traceback__)  # the finished frames still hold the memory map
            del data
            drop_temp(meta["data_path"])
        raise


def _finish(data, meta, notices, fs, meas_date, mains, mains_fallback):
    if data.shape[1] < WIN:
        raise InputError("Shorter than one 4-s window; nothing to score.")
    if mains == "auto":
        hz, r50, r60 = suggest_mains(data)
        if hz is None and mains_fallback is not None:
            hz = float(mains_fallback)
            notices.append(f"No clear mains line in this file; the study's {hz:.0f} Hz is used.")
        if hz is None:
            raise InputError(f"The mains frequency could not be determined from the signal (50 Hz ratio {r50:.1f}, "
                             f"60 Hz ratio {r60:.1f}); start again and choose 50 or 60 Hz.")
    else:
        hz = float(mains)
        r50, r60 = mains_ratios(data)
    meta.update(fs_in=fs, meas_date=meas_date, notch_hz=float(hz), mains_ratios=(r50, r60), notices=notices)
    return data, meta
