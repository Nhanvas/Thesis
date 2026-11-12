"""Synthetic test of stage RB, part 1: the referential -> bipolar wrapper (src/r2_rb.py) and the laptop check
src/r2_rb0b.py. Runs in a container; no real EEG. Every code path, failure paths included (instructions §1 item 15).

World: CHB-MIT root with chb12_24 and chb12_32 (bipolar, 23 channels incl. the duplicate T8-P8 and dummy "-"
channels, as the real files), chb12_27 (19 electrodes + extra electrodes referenced to CS2, dummy "-" channels,
real label order), chb12_28 (bare labels, O1 written "01", EKG channel), chb12_29 (bare labels, 3624 s-like odd
length, one electrode driven past the digital range = clipping); a summary with seizures in 27, 28, 29; an
inventory with their sha256; R0-style stats. A narrow 17 Hz interference with electrode-dependent amplitude is
planted in chb12_27 only.

    python src/r2_rb_synthetic_test.py --e2b-eeg /path/to/epilepsy2bids/src/epilepsy2bids/eeg.py
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path(__file__).resolve().parent
for _p in (SRC, SRC / "dataprep"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import r2_rb as RB  # noqa: E402

FS = 256
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}", flush=True)


def expect_stop(name, fn):
    try:
        fn()
    except RB.StopRB as ex:
        check(name, True, f"(STOP: {str(ex)[:90]})")
        return
    except SystemExit as ex:
        check(name, "STOP" in str(ex), f"(SystemExit: {str(ex)[:90]})")
        return
    check(name, False, "(no STOP)")


# ------------------------------------------------------------------------------------------------ world
def write_edf(path, labels, sig_uV, dig=(-2048, 2047), phys=(-800.0, 800.0)):
    import pyedflib
    heads = []
    for l in labels:
        if l == "-":
            heads.append({"label": "-", "dimension": "uV", "sample_frequency": FS, "physical_min": -1.0,
                          "physical_max": 1.0, "digital_min": -1, "digital_max": 1, "transducer": "",
                          "prefilter": ""})
        else:
            heads.append({"label": l, "dimension": "uV", "sample_frequency": FS, "physical_min": phys[0],
                          "physical_max": phys[1], "digital_min": dig[0], "digital_max": dig[1],
                          "transducer": "", "prefilter": ""})
    sig = [np.clip(s, phys[0], phys[1]) for s in sig_uV]
    pyedflib.highlevel.write_edf(str(path), sig, heads, digital=False)


def electrodes_signals(rng, n, extra=()):
    names = RB.electrodes() + list(extra)
    t = np.arange(n) / FS
    out = {}
    for k, e in enumerate(names):
        w = rng.standard_normal(n)
        w = np.convolve(w, np.ones(8) / 8, mode="same")              # low-pass-ish
        out[e] = 40 * w + 15 * np.sin(2 * np.pi * (6 + k * 0.3) * t + k)
    return out


def bipolar_file(path, rng, n):
    el = electrodes_signals(rng, n)
    chans = [c for c in RB._P().COMMON_CHANNELS]
    labels = chans[:13] + ["-"] + chans[13:16] + ["-", "FT9-FT10", "FT10-T8", "T8-P8"] + chans[16:]
    sig = []
    for l in labels:
        if l == "-":
            sig.append(np.zeros(n))
        elif l in ("FT9-FT10", "FT10-T8"):
            sig.append(30 * rng.standard_normal(n))
        else:
            a, b = l.split("-")
            sig.append(el[a] - el[b])
    write_edf(path, labels, sig)


def referential_file(path, rng, n, style, clip_e=None, interference=False):
    el = electrodes_signals(rng, n, extra=("FT9", "FT10", "CP1"))
    t = np.arange(n) / FS
    if interference:
        for k, e in enumerate(el):
            el[e] = el[e] + (5 + 3 * k) * np.sin(2 * np.pi * 17.0 * t)
    if clip_e:
        el[clip_e][2000:2600] += 2000.0                               # beyond +800 uV -> clipped in the EDF
    order = ["F7", "T7", "P7", "-", "FP1", "F3", "C3", "P3", "O1", "-", "FZ", "CZ", "PZ", "-", "FP2", "F4", "C4",
             "P4", "O2", "F8", "T8", "P8", "FT9", "FT10", "CP1"]
    if style == "cs2":
        ref = 25 * rng.standard_normal(n)
        labels = [("-" if e == "-" else f"{e}-CS2") for e in order]
        sig = [np.zeros(n) if e == "-" else el[e] - ref for e in order]
    else:
        labels = [("-" if e == "-" else ("01" if e == "O1" else e)) for e in order] + ["EKG1-CHIN"]
        sig = [np.zeros(n) if e == "-" else el[e] for e in order] + [200 * np.sin(2 * np.pi * 1.2 * t)]
    write_edf(path, labels, sig)


SUMMARY = """Data Sampling Rate: 256 Hz
*************************

File Name: chb12_24.edf
File Start Time: 13:06:00
File End Time: 13:11:00
Number of Seizures in File: 0

File Name: chb12_27.edf
File Start Time: 16:07:06
File End Time: 16:12:06
Number of Seizures in File: 1
Seizure 1 Start Time: 120 seconds
Seizure 1 End Time: 150 seconds

File Name: chb12_28.edf
File Start Time: 17:07:00
File End Time: 17:12:00
Number of Seizures in File: 1
Seizure 1 Start Time: 40 seconds
Seizure 1 End Time: 60 seconds

File Name: chb12_29.edf
File Start Time: 18:07:19
File End Time: 18:12:23
Number of Seizures in File: 2
Seizure 1 Start Time: 30 seconds
Seizure 1 End Time: 50 seconds
Seizure 2 Start Time: 200 seconds
Seizure 2 End Time: 230 seconds

File Name: chb12_32.edf
File Start Time: 21:09:00
File End Time: 21:14:00
Number of Seizures in File: 0
"""


def build_world(root):
    rng = np.random.default_rng(7)
    d = root / "CHB-MIT" / "chb12"
    d.mkdir(parents=True)
    n5 = 300 * FS
    bipolar_file(d / "chb12_24.edf", rng, n5)
    bipolar_file(d / "chb12_32.edf", rng, n5)
    referential_file(d / "chb12_27.edf", rng, n5, "cs2", interference=True)
    referential_file(d / "chb12_28.edf", rng, n5, "bare")
    referential_file(d / "chb12_29.edf", rng, 304 * FS + 100, "bare", clip_e="O1")
    sd = root / "summaries"
    sd.mkdir()
    (sd / "chb12-summary.txt").write_text(SUMMARY)
    inv = [{"case": "chb12", "file": p.name, "sha256_physionet": RB.sha256(p)} for p in sorted(d.glob("*.edf"))]
    pd.DataFrame(inv).to_csv(root / "inventory.csv", index=False)
    thr = [150.0] * 18
    (root / "chb12_stats.json").write_text(json.dumps({"artifact_thresh_uV": thr}))
    return d


def independent_derive(path):
    """Ground truth with another reader (pyedflib physical values) and a hand-written label table."""
    import pyedflib
    with pyedflib.EdfReader(str(path)) as f:
        labels = [l.strip().upper() for l in f.getSignalLabels()]
        table = {}
        for i, l in enumerate(labels):
            e = l[:-4] if l.endswith("-CS2") else l
            e = "O1" if e == "01" else e
            table.setdefault(e, i)
        X = {e: f.readSignal(table[e]) for e in RB.electrodes()}
    return np.stack([X[a] - X[b] for a, b in RB.derivations()]) * 1e-6


# ------------------------------------------------------------------------------------------------ tests
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--e2b-eeg", required=True)
    a = ap.parse_args(argv)
    t0 = time.time()
    tmp = Path(tempfile.mkdtemp(prefix="rbsyn_"))
    d = build_world(tmp)
    real_ref = dict(RB.REFERENTIAL)
    RB.REFERENTIAL.clear()
    RB.REFERENTIAL.update({p.name: RB.sha256(p) for p in d.glob("chb12_2[789].edf")})
    import mne
    P = RB._P()
    orig = P.open_edf
    check("record open_edf returns None for the three referential files",
          all(orig(d / f) is None for f in RB.REFERENTIAL))
    check("record open_edf reads the bipolar files", orig(d / "chb12_24.edf") is not None)

    # --- T1 matching and values
    for f, style in (("chb12_27.edf", "cs2"), ("chb12_28.edf", "bare"), ("chb12_29.edf", "bare")):
        data, info = RB.derive(d / f)
        exp_lab = {e: (f"{e}-CS2" if style == "cs2" else ("01" if e == "O1" else e)) for e in RB.electrodes()}
        check(f"T1 {f}: 19 electrodes matched to the right labels",
              {e: l.upper() for e, l in info["labels_used"].items()} == exp_lab)
        truth = independent_derive(d / f)
        diff = float(np.abs(data - truth).max())
        check(f"T1 {f}: derivations = independent reader (max |diff| {diff:.2e} V)", diff <= 1e-12)
        check(f"T1 {f}: shape 18 x n_times", data.shape == (18, info["n_times"]))

    # --- T2 SzCORE side (also proves the harness of r2_rb0b)
    import r2_rb0b as B0
    Eeg = B0.load_szcore(a.e2b_eeg)
    for f in sorted(RB.REFERENTIAL):
        data, info = RB.derive(d / f)
        r = B0.szcore_compare(Eeg, d / f, data * 1e6, info["labels_used"])
        check(f"T2 {f}: SzCORE matches the same labels", r["labels_equal"])
        check(f"T2 {f}: SzCORE reref = ours (max |diff| {r['B1_reref']['max_abs_diff_uV']:.2e} uV)",
              r["B1_reref"]["max_abs_diff_uV"] <= B0.B1_TOL_UV)
        print(f"     B2 standardize max |diff| {r['B2_standardize']['max_abs_diff_uV']:.3e} uV (reported, not gated)")

    # --- T3 wrapper behaviour
    RB.install()
    check("T3 install: every loaded preprocessing copy patched", RB.installed())
    RB.install()
    check("T3 install is idempotent", RB.installed() and RB._ORIG is orig)
    raw24_o, raw24_w = orig(d / "chb12_24.edf"), P.open_edf(d / "chb12_24.edf")
    check("T3 bipolar file: wrapper returns the record's result",
          raw24_w.ch_names == raw24_o.ch_names and np.array_equal(raw24_w.get_data(), raw24_o.get_data()))
    rw = P.open_edf(d / "chb12_27.edf")
    data27, _ = RB.derive(d / "chb12_27.edf")
    check("T3 referential file: 18 pipeline channels in order, values = derive",
          rw.ch_names == list(P.COMMON_CHANNELS) and np.array_equal(rw.get_data(), data27))
    other = tmp / "other"
    other.mkdir()
    shutil.copy(d / "chb12_27.edf", other / "chb99_01.edf")
    check("T3 a referential file not in the list: None (record behaviour)", P.open_edf(other / "chb99_01.edf") is None)

    # --- T4 RawArray is a drop-in for the file raw (every reader of the pipeline), on a bipolar file
    import continuous_eval as CE
    import x1_external as X1
    data24 = raw24_o.get_data()
    arr = RB.to_raw(data24)
    n = int(raw24_o.n_times) // P.WIN_SAMPLES
    same = all(np.array_equal(P.filter_window(raw24_o, i * 1024, i * 1024 + 1024),
                              P.filter_window(arr, i * 1024, i * 1024 + 1024)) for i in range(n))
    check("T4 preprocessing.filter_window: RawArray = file raw (all windows)", same)
    check("T4 continuous_eval.compute_signal_loss_flags: RawArray = file raw",
          np.array_equal(CE.compute_signal_loss_flags(raw24_o, n), CE.compute_signal_loss_flags(arr, n)))
    check("T4 n_times / sfreq equal", arr.n_times == raw24_o.n_times and arr.info["sfreq"] == raw24_o.info["sfreq"])
    # whole-file filter + load_18 through the wrapper on a referential file
    filt, nw = CE.filter_file(d / "chb12_27.edf")
    from scipy.signal import sosfiltfilt, filtfilt
    man = filtfilt(P._NOTCH_B, P._NOTCH_A, sosfiltfilt(P._BP_SOS, data27, axis=1), axis=1)
    man = np.ascontiguousarray(man[:, :nw * 1024].reshape(18, nw, 1024).transpose(1, 0, 2)).astype(np.float32)
    check("T4 continuous_eval.filter_file through the wrapper = manual filter of the derivations", np.array_equal(filt, man))
    check("T4 x1_external.load_18(kind='chb') through the wrapper = derive",
          np.array_equal(X1.load_18(d / "chb12_27.edf", "chb"), data27))
    # stats and counts (preprocessing's own loops) see the referential files once installed
    smap = P.parse_summary(tmp / "summaries" / "chb12-summary.txt")
    m_w, s_w = P.compute_subject_stats("chb12", tmp / "CHB-MIT", smap)
    cw = P.count_windows("chb12", tmp / "CHB-MIT", smap, 5 * s_w)
    RB.uninstall()
    check("T3 uninstall restores the record function", P.open_edf is orig and not RB.installed())
    m_o, s_o = P.compute_subject_stats("chb12", tmp / "CHB-MIT", smap)
    co = P.count_windows("chb12", tmp / "CHB-MIT", smap, 5 * s_w)
    check("T4 compute_subject_stats / count_windows include the three files only with the wrapper",
          not np.array_equal(s_w, s_o) and sum(cw) > sum(co), f"windows {sum(co)} -> {sum(cw)}")
    # forked workers inherit the patch
    RB.install()
    import multiprocessing as mp
    with mp.get_context("fork").Pool(1) as pool:
        name = pool.apply(_child_name)
    check("T3 a forked worker sees the patch", name == "open_edf_rb", name)
    RB.uninstall()

    # --- T5 failure paths of the wrapper
    def variant(fname, mutate):
        q = tmp / "neg"
        q.mkdir(exist_ok=True)
        rng = np.random.default_rng(3)
        n2 = 60 * FS
        el = electrodes_signals(rng, n2)
        labels, sig = mutate([e for e in RB.electrodes()], [el[e] for e in RB.electrodes()])
        p = q / fname
        if p.exists():
            p.unlink()
        write_edf(p, labels, sig)
        RB.REFERENTIAL[fname] = RB.sha256(p)
        RB._SHA_OK.clear()
        return p
    p = variant("chb12_27.edf", lambda L, S: ([l for l in L if l != "O1"], [s for l, s in zip(L, S) if l != "O1"]))
    expect_stop("T5 missing electrode -> STOP", lambda: RB.derive(p))
    p = variant("chb12_28.edf", lambda L, S: (L + ["F3-CS2"], S + [S[L.index("F3")]]))
    expect_stop("T5 electrode present twice -> STOP", lambda: RB.derive(p))
    p = variant("chb12_29.edf", lambda L, S: (L, S))
    RB.REFERENTIAL["chb12_29.edf"] = "0" * 64
    RB._SHA_OK.clear()
    expect_stop("T5 listed name, different content (sha256) -> STOP", lambda: RB.derive(p))
    expect_stop("T5 a file that is not one of the three -> STOP", lambda: RB.derive(other / "chb99_01.edf"))
    import pyedflib
    p512 = tmp / "neg" / "chb12_28.edf"
    p512.unlink()
    heads = [{"label": e, "dimension": "uV", "sample_frequency": 512, "physical_min": -800.0, "physical_max": 800.0,
              "digital_min": -2048, "digital_max": 2047, "transducer": "", "prefilter": ""} for e in RB.electrodes()]
    pyedflib.highlevel.write_edf(str(p512), [np.zeros(512 * 8) for _ in heads], heads)
    RB.REFERENTIAL["chb12_28.edf"] = RB.sha256(p512)
    RB._SHA_OK.clear()
    expect_stop("T5 sampling rate != 256 Hz -> STOP", lambda: RB.derive(p512))
    RB.REFERENTIAL.clear()
    RB.REFERENTIAL.update({q.name: RB.sha256(q) for q in d.glob("chb12_2[789].edf")})
    RB._SHA_OK.clear()

    # --- T6 the laptop check end to end
    out = tmp / "rb0b"
    common = ["--e2b-eeg", a.e2b_eeg, "--chbmit-dir", str(tmp / "CHB-MIT"), "--summary-dir", str(tmp / "summaries"),
              "--inventory", str(tmp / "inventory.csv"), "--stats", str(tmp / "chb12_stats.json")]
    res = B0.main(common + ["--out", str(out)])
    check("T6 rb0b: gates A and B PASS", res["gates"] == {"A_inputs": "PASS", "B_szcore_equal": "PASS"}, str(res["gates"]))
    files = {"A_inputs.csv", "B_szcore_compare.json", "C_clipping_channels.csv", "C_clipping_files.csv",
             "C_clipping_derivations.csv", "D_rms_files.csv", "D_rms_blocks_5min.csv", "D_flags.csv",
             "D_position.csv", "E_peaks.csv", "E_peaks_referential_only.csv", "rb0b.json", "SUMMARY.md"}
    check("T6 rb0b: every output written", files <= {x.name for x in out.iterdir()})
    C = pd.read_csv(out / "C_clipping_channels.csv")
    o1 = C[(C.file == "chb12_29.edf") & (C.channel == "O1")].iloc[0]
    others = C[~((C.file == "chb12_29.edf") & (C.channel == "O1"))]
    check("T6 rb0b C: the planted clipping found exactly (O1 of chb12_29, 600 samples), nowhere else",
          o1.clipped_samples == 600 and int(others.clipped_samples.sum()) == 0,
          f"O1 {o1.clipped_samples}, others {int(others.clipped_samples.sum())}")
    Dv = pd.read_csv(out / "C_clipping_derivations.csv")
    aff = Dv[(Dv.file == "chb12_29.edf") & (Dv.affected_samples > 0)].channel.tolist()
    check("T6 rb0b C: the derivations using O1 are the affected ones", sorted(aff) == ["P3-O1", "P7-O1"], str(aff))
    Fl = pd.read_csv(out / "D_flags.csv")
    exp_w = {"chb12_24.edf": 75, "chb12_27.edf": 75, "chb12_28.edf": 75, "chb12_29.edf": 76, "chb12_32.edf": 75}
    check("T6 rb0b D: windows per file", dict(zip(Fl.file, Fl.windows)) == exp_w, str(dict(zip(Fl.file, Fl.windows))))
    r29 = Fl[Fl.file == "chb12_29.edf"].iloc[0]
    check("T6 rb0b D: ictal / buffer / base windows of chb12_29 by the record's rules",
          (r29.ictal_windows, r29.non_ictal_non_buffer_windows) == (14, 7),
          f"ictal {r29.ictal_windows}, base {r29.non_ictal_non_buffer_windows}")
    Pz = pd.read_csv(out / "D_position.csv")
    check("T6 rb0b D: position table 3 files x 18 channels, 2 bipolar files each",
          len(Pz) == 54 and (Pz.bipolar_files == 2).all())
    Eo = pd.read_csv(out / "E_peaks_referential_only.csv")
    hit = Eo[(Eo.file == "chb12_27.edf") & (np.abs(Eo.freq_hz - 17.0) < 0.3)]
    check("T6 rb0b E: the planted 17 Hz interference of chb12_27 found, in no other file",
          len(hit) == 1 and set(Eo.file) == {"chb12_27.edf"}, Eo.to_string()[:200])
    check("T6 rb0b leaves the wrapper uninstalled", not RB.installed())
    # failure paths of rb0b
    bad = tmp / "inventory_bad.csv"
    iv = pd.read_csv(tmp / "inventory.csv")
    iv.loc[iv.file == "chb12_24.edf", "sha256_physionet"] = "f" * 64
    iv.to_csv(bad, index=False)
    cbad = [x if x != str(tmp / "inventory.csv") else str(bad) for x in common]
    expect_stop("T6 rb0b: an input sha256 differs from PhysioNet -> STOP A", lambda: B0.main(cbad + ["--out", str(tmp / "rb0b_badA")]))
    RB.uninstall()
    real_derive = RB.derive

    def swapped(path):
        data, info = real_derive(path)
        return data[[1, 0] + list(range(2, 18))], info
    RB.derive = swapped
    try:
        res2 = B0.main(common + ["--out", str(tmp / "rb0b_badB")])
    finally:
        RB.derive = real_derive
        RB.uninstall()
    check("T6 rb0b: a wrong conversion (two derivations swapped) -> gate B FAIL", res2["gates"]["B_szcore_equal"] == "FAIL")

    # --- T7 SzCORE pin and the resampy stub
    crlf = tmp / "eeg_crlf.py"
    crlf.write_bytes(Path(a.e2b_eeg).read_bytes().replace(b"\n", b"\r\n"))
    check("T7 eeg.py pin holds for a CRLF checkout", B0.sha256_text(crlf) == B0.SZCORE_EEG_SHA256)
    mod = tmp / "eeg_mod.py"
    mod.write_text(Path(a.e2b_eeg).read_text() + "\n# changed\n")
    expect_stop("T7 another eeg.py -> STOP", lambda: B0.main(["--e2b-eeg", str(mod)] + common[2:] + ["--out", str(tmp / "rb0b_badpin")]))
    RB.uninstall()
    saved = sys.modules.pop("resampy", None)
    import builtins
    real_import = builtins.__import__

    def no_resampy(name, *args, **kw):
        if name == "resampy":
            raise ImportError("hidden for the test")
        return real_import(name, *args, **kw)
    builtins.__import__ = no_resampy
    try:
        used = B0.ensure_resampy()
    finally:
        builtins.__import__ = real_import
    check("T7 resampy missing -> stub used", used.startswith("stub"), used)
    Eeg2 = B0.load_szcore(a.e2b_eeg)
    for f in sorted(RB.REFERENTIAL):
        data, info = RB.derive(d / f)
        r = B0.szcore_compare(Eeg2, d / f, data * 1e6, info["labels_used"])
        check(f"T7 {f}: SzCORE standardize with the stub = ours", r["B2_standardize"]["max_abs_diff_uV"] <= B0.B1_TOL_UV
              and r["B1_reref"]["max_abs_diff_uV"] <= B0.B1_TOL_UV)
    import resampy as stub
    try:
        stub.resample(np.zeros(10), 512, 256)
        ok = False
    except RuntimeError:
        ok = True
    check("T7 the stub refuses a real resampling", ok)
    sys.modules.pop("resampy", None)
    if saved is not None:
        sys.modules["resampy"] = saved

    RB.REFERENTIAL.clear()
    RB.REFERENTIAL.update(real_ref)
    shutil.rmtree(tmp)
    n_fail = sum(1 for _, ok, _ in RESULTS if not ok)
    print(f"\n{len(RESULTS)} checks, {n_fail} failed, {time.time() - t0:.0f} s -> {'ALL PASS' if n_fail == 0 else 'FAIL'}")
    return n_fail


def _child_name():
    return RB._P().open_edf.__name__


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
