"""Stage RB (rebuild with chb12_27-29, board R170 / R176) -- part 1: referential -> 18 bipolar wrapper.

chb12_27 (electrodes referenced to CS2, labels "FP1-CS2" ...), chb12_28 and chb12_29 (bare electrode labels, O1
written "01") are the only CHB-MIT files not stored as the 18 bipolar derivations. `preprocessing.open_edf` returns
None for them, so every earlier run skipped them.

Conversion = the one in SzCORE's own CHB-MIT converter (esl-epfl/epilepsy2bids, commit d3fb175, 2026-04-10,
`bids/chbmit/convert2bids.py`: these three files are loaded as unipolar 10-20 electrodes and re-referenced to the
double banana; `eeg.py` `_electrodeSynonymRegex`: O1 matches "O1" or "01", T7/T3, P7/T5, T8/T4, P8/T6 synonyms):
each derivation A-B = electrode A minus electrode B, sample by sample, in float64. A common reference cancels exactly.

Author decision 12/11 20:57: follow SzCORE. Our matcher differs only where SzCORE would silently zero-fill a missing
electrode or take the first of several matching labels: here a missing or duplicated electrode STOPs. For these three
files every electrode is present exactly once (RB0), so both give the same signal; the laptop check RB0b compares the
two outputs sample by sample.

No record module is edited. `install()` replaces `preprocessing.open_edf` in the running process (and in processes
forked after it); every reader of the pipeline calls it through the module (`compute_subject_stats`,
`count_windows`, `continuous_eval.filter_file`, `filter_file_per_window`, `c1b` signal-loss flags,
`x1_external.load_18`). The original function is called first; the conversion is used only when it returns None AND
the file is one of the three, identified by name and sha256.
"""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

import numpy as np

# The three referential files: sha256 = PhysioNet SHA256SUMS (results/r2/r0_data/chb/inventory.csv, RB0).
REFERENTIAL = {
    "chb12_27.edf": "3f850341d86a547ddde2cb145dddfc3d0f963738ae2d0a5ff8bdda646978869b",
    "chb12_28.edf": "46783d0e45c494a5e904f80315700daf98b966957ebb770b08d6666fafee7780",
    "chb12_29.edf": "033299f599912cd2a11e90c4e84b506efb07d1b454786e3d2a8547aeb4e8cc76",
}
FS = 256
REF_SUFFIXES = ("-CS2",)                     # the only reference suffix in these files (RB0)
SYNONYMS = {"01": "O1", "T3": "T7", "T5": "P7", "T4": "T8", "T6": "P8"}   # SzCORE's synonym set

_ORIG = None          # the record's preprocessing.open_edf
_SHA_OK: dict = {}    # (path, size, mtime) -> True, per process


class StopRB(RuntimeError):
    """A condition that must stop the run (missing / duplicated electrode, wrong file, wrong rate)."""


_SRC = Path(__file__).resolve().parent


def _P():
    """The record module as the pipeline imports it: top-level `preprocessing` (src/dataprep on sys.path)."""
    import sys
    for d in (_SRC, _SRC / "dataprep"):
        if str(d) not in sys.path:
            sys.path.insert(0, str(d))
    import preprocessing as P
    return P


def _all_P():
    """Every loaded copy of the module (top-level and package import), so no reader escapes the patch."""
    import sys
    mods = [_P()]
    m = sys.modules.get("dataprep.preprocessing")
    if m is not None and m is not mods[0]:
        mods.append(m)
    return mods


def derivations():
    """[(A, B)] in the pipeline's channel order (preprocessing.COMMON_CHANNELS)."""
    return [tuple(c.split("-")) for c in _P().COMMON_CHANNELS]


def electrodes():
    return sorted({e for ab in derivations() for e in ab})          # 19 electrodes


def sha256(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def _check_file(path: Path):
    name = path.name
    if name not in REFERENTIAL:
        raise StopRB(f"STOP RB: {name} is not one of the three referential files")
    st = path.stat()
    key = (str(path.resolve()), st.st_size, st.st_mtime_ns)
    if key not in _SHA_OK:
        got = sha256(path)
        if got != REFERENTIAL[name]:
            raise StopRB(f"STOP RB: {name} sha256 {got} != PhysioNet {REFERENTIAL[name]}")
        _SHA_OK[key] = True


def normalise(label: str) -> str:
    """Upper case, strip, drop the reference suffix, apply the SzCORE synonyms."""
    n = label.upper().strip()
    for suf in REF_SUFFIXES:
        if n.endswith(suf):
            n = n[: -len(suf)]
    return SYNONYMS.get(n, n)


def match_electrodes(labels):
    """{electrode: index} for the 19 electrodes; STOP if one is missing or matches more than one label."""
    norm = [normalise(l) for l in labels]
    out, bad = {}, []
    for e in electrodes():
        hits = [i for i, n in enumerate(norm) if n == e]
        if len(hits) != 1:
            bad.append(f"{e}: {len(hits)} labels {[labels[i] for i in hits]}")
        else:
            out[e] = hits[0]
    if bad:
        raise StopRB("STOP RB: electrodes not found exactly once: " + "; ".join(bad))
    return out


def derive(path):
    """(data [18, n] float64 in volts, info dict) for one of the three files."""
    import mne
    path = Path(path)
    _check_file(path)
    raw = mne.io.read_raw_edf(str(path), preload=False, verbose=False)
    fs = float(raw.info["sfreq"])
    if int(round(fs)) != FS or abs(fs - FS) > 1e-9:
        raise StopRB(f"STOP RB: {path.name} sampled at {fs} Hz")
    labels = list(raw.ch_names)
    idx = match_electrodes(labels)
    names = electrodes()
    X = raw.get_data(picks=[idx[e] for e in names]).astype(np.float64)
    pos = {e: i for i, e in enumerate(names)}
    data = np.stack([X[pos[a]] - X[pos[b]] for a, b in derivations()])
    info = {"file": path.name, "sfreq": fs, "n_times": int(raw.n_times),
            "labels_used": {e: labels[idx[e]] for e in names}}
    return data, info


def to_raw(data):
    """An mne RawArray with the pipeline's 18 channel names (what preprocessing.open_edf returns for a bipolar file)."""
    import mne
    info = mne.create_info(list(_P().COMMON_CHANNELS), FS, ch_types="eeg", verbose=False)
    return mne.io.RawArray(data, info, verbose=False)


def open_edf_rb(edf_path):
    """Drop-in for preprocessing.open_edf: the record's result, or the converted file for the three files."""
    raw = _ORIG(edf_path)
    if raw is not None:
        return raw
    if Path(edf_path).name not in REFERENTIAL:
        return None                                   # the record's behaviour for every other file
    data, _ = derive(edf_path)
    return to_raw(data)


def install():
    """Point preprocessing.open_edf at open_edf_rb in this process (idempotent). Returns the record's function."""
    global _ORIG
    mods = _all_P()
    if _ORIG is None:
        _ORIG = mods[0].open_edf
        if getattr(_ORIG, "__name__", "") != "open_edf":
            raise StopRB(f"STOP RB: preprocessing.open_edf is already replaced by {_ORIG!r}")
    for m in mods:
        m.open_edf = open_edf_rb
    os.environ["R2_RB_WRAPPER"] = "1"
    return _ORIG


def installed() -> bool:
    return all(getattr(m.open_edf, "__name__", "") == "open_edf_rb" for m in _all_P())


def uninstall():
    global _ORIG
    if _ORIG is not None:
        for m in _all_P():
            m.open_edf = _ORIG
        _ORIG = None
    os.environ.pop("R2_RB_WRAPPER", None)
