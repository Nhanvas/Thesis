"""RB0b -- full check of the chb12_27-29 conversion and of their amplitude, before RB1 (laptop; descriptive + gates).

Why (plan §12 row 12/11 21:30): RB0 passed every header check, but the RMS of the derived channels was outside the
range of chb12_24 / chb12_32 (chb12_27 1.3-6.5x higher in 17/18 channels; chb12_28 / _29 0.31-1.0x), measured on the
first 10 min of 2 files only. Before the data are used: (1) is our conversion identical to SzCORE's (the converter the
author chose to follow, 12/11 20:57)? (2) is the amplitude a conversion fault (clipped referential channels break the
subtraction) or the recording itself? Every check covers all 24 chb12 files, all channels, the whole recording.

Parts (all outputs under --out):
  A  inputs: every chb12 EDF listed in the summary present; sha256 = PhysioNet (R0 inventory)          [GATE]
  B  conversion vs SzCORE (epilepsy2bids eeg.py, commit d3fb175): per file, the label each of the 19 electrodes
     matched (ours vs SzCORE's `_findChannelIndex`), and max |ours - SzCORE| per derivation over the whole file for
     (B1) SzCORE load + reReferenceToBipolar and (B2) SzCORE standardize(256, ELECTRODES_10_20, "bipolar") exactly
     as convert2bids calls it. Gate: labels identical and B1 max |diff| <= 1e-6 uV (EDF step 0.39 uV)       [GATE]
  C  clipping: share of samples at the digital min / max of each used channel (19 electrodes for the referential
     files, the 18 channels the pipeline reads for the bipolar files); share of 4 s windows with any clipped sample;
     for the referential files, per derivation, the share of samples where either electrode is clipped   [descriptive]
  D  amplitude and 5-SD flags through the pipeline itself (wrapper installed, `continuous_eval.filter_file` = the
     c1b path): per file and channel, window RMS median / IQR / p95 (uV); where each referential file sits among the
     21 bipolar files (min / median / max of their medians, ratio, rank); median RMS per 5-min block for every file;
     `is_flag5sd` with R0's chb12 thresholds (c1b rule) on all windows and on the non-ictal, non-buffer windows
     [descriptive]
  E  spectrum: Welch PSD (0.25 Hz bins, unfiltered derived signals) per file and channel; narrow peaks
     (>= 10 dB above a 5 Hz running median, <= 1 Hz wide); peaks found in a referential file in >= 9 channels and in
     none of the 21 bipolar files are listed                                                              [descriptive]

No decision rule on the amplitude is fixed here: the chat reads the tables and the author decides (plan §10 P2).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path(__file__).resolve().parent
REPO = SRC.parent
for _p in (SRC, SRC / "dataprep"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import r2_rb as RB  # noqa: E402

B1_TOL_UV = 1e-6
SZCORE_COMMIT = "d3fb17526b8a483e292ae9ba2e51b02d5f9128ff"
SZCORE_EEG_SHA256 = "a34b539232f03f494411bb458673a2de8a6626e2a9f0435a6c42a2f6ec7b638b"            # src/epilepsy2bids/eeg.py at SZCORE_COMMIT
SUBJ = "chb12"
WIN = 1024
BLOCK_S = 300
PEAK_DB = 10.0


def log(msg):
    print(f"[RB0b {time.strftime('%H:%M:%S')}] {msg}", flush=True)


def sha256(p):
    return RB.sha256(p)


def sha256_text(p):
    """sha256 of a text file with CRLF normalised to LF (git on Windows may check files out with CRLF)."""
    return hashlib.sha256(Path(p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def jdump(obj, path):
    Path(path).write_text(json.dumps(obj, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))


# ----------------------------------------------------------------------------------------------- SzCORE side
def ensure_resampy():
    """SzCORE's eeg.py imports resampy (which needs numba). If it is not installed, a stub that reproduces resampy
    0.4.3 `core.resample` for equal rates (`if sr_orig == sr_new: return x.copy()`) and refuses anything else is
    used; the three files are at 256 Hz, so standardize(256, ...) only ever takes that branch. Returns what was used."""
    try:
        import resampy
        return f"resampy {resampy.__version__}"
    except ImportError:
        import types
        m = types.ModuleType("resampy")

        def resample(x, sr_orig, sr_new, axis=-1, filter="kaiser_best", **kw):
            if sr_orig == sr_new:
                return x.copy()
            raise RuntimeError("resampy stub: only equal rates are supported")
        m.resample = resample
        m.__version__ = "stub (equal-rate branch of resampy 0.4.3 core.resample)"
        sys.modules["resampy"] = m
        return "stub: equal-rate branch of resampy 0.4.3 core.resample (resampy not installed)"


def load_szcore(eeg_py):
    spec = importlib.util.spec_from_file_location("szcore_eeg", eeg_py)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.Eeg


SZ_TO_OURS = {"T3": "T7", "T5": "P7", "T4": "T8", "T6": "P8"}


def sz_name(pair):
    a, b = pair.split("-")
    return f"{SZ_TO_OURS.get(a, a).upper()}-{SZ_TO_OURS.get(b, b).upper()}"


def szcore_compare(Eeg, path, ours_uV, ours_labels):
    import pyedflib
    with pyedflib.EdfReader(str(path)) as f:
        all_labels = f.getSignalLabels()
    sz_labels = {}
    for e in Eeg.ELECTRODES_10_20:
        i = Eeg._findChannelIndex(all_labels, e, Eeg.Montage.UNIPOLAR)
        sz_labels[SZ_TO_OURS.get(e, e).upper()] = all_labels[i]
    ours_l = {e: l for e, l in ours_labels.items()}
    labels_equal = all(ours_l[e].strip().upper() == sz_labels[e].strip().upper() for e in ours_l)

    ch = list(RB._P().COMMON_CHANNELS)
    out = {"labels_ours": ours_l, "labels_szcore": sz_labels, "labels_equal": bool(labels_equal)}
    for tag in ("B1_reref", "B2_standardize"):
        eeg = Eeg.loadEdf(str(path), Eeg.Montage.UNIPOLAR, Eeg.ELECTRODES_10_20)
        if tag == "B1_reref":
            eeg.reReferenceToBipolar()
        else:
            eeg.standardize(256, Eeg.ELECTRODES_10_20, "bipolar")
        names = [sz_name(c) for c in eeg.channels]
        if sorted(names) != sorted(ch):
            raise SystemExit(f"STOP RB0b: SzCORE derivations {names} do not map to the pipeline's 18")
        sz = np.stack([eeg.data[names.index(c)] for c in ch]).astype(np.float64)
        n = min(sz.shape[1], ours_uV.shape[1])
        d = np.abs(sz[:, :n] - ours_uV[:, :n])
        out[tag] = {"n_samples_szcore": int(sz.shape[1]), "n_samples_ours": int(ours_uV.shape[1]),
                    "max_abs_diff_uV": float(d.max()),
                    "max_abs_diff_uV_per_channel": {c: float(d[i].max()) for i, c in enumerate(ch)}}
        del eeg, sz, d
    return out


# ----------------------------------------------------------------------------------------------- clipping
def clipping(path, referential):
    import pyedflib
    rows = []
    with pyedflib.EdfReader(str(path)) as f:
        labels = [l.strip() for l in f.getSignalLabels()]
        if referential:
            idx = RB.match_electrodes(labels)
            use = {e: idx[e] for e in RB.electrodes()}
        else:
            up = [l.upper() for l in labels]
            use = {c: up.index(c) for c in RB._P().COMMON_CHANNELS}      # first occurrence = what open_edf keeps
        clip = {}
        for name, i in use.items():
            x = f.readSignal(i, digital=True)
            lo, hi = f.getDigitalMinimum(i), f.getDigitalMaximum(i)
            c = (x <= lo) | (x >= hi)
            clip[name] = c
            rows.append({"file": path.name, "channel": name, "label": labels[i], "digital_min": int(lo),
                         "digital_max": int(hi), "n_samples": int(x.size), "clipped_samples": int(c.sum()),
                         "clipped_share": float(c.mean())})
    n = min(v.size for v in clip.values()) // WIN
    anyc = np.zeros(n, dtype=bool)
    for v in clip.values():
        anyc |= v[: n * WIN].reshape(n, WIN).any(axis=1)
    per_file = {"file": path.name, "windows": int(n), "windows_any_clipped": int(anyc.sum()),
                "windows_any_clipped_share": float(anyc.mean())}
    deriv = []
    if referential:
        for a, b in RB.derivations():
            c = clip[a] | clip[b]
            deriv.append({"file": path.name, "channel": f"{a}-{b}", "affected_samples": int(c.sum()),
                          "affected_share": float(c.mean())})
    return rows, per_file, deriv


# ----------------------------------------------------------------------------------------------- spectrum
def peaks(f, psd_db, freqs_ok):
    from scipy.ndimage import median_filter
    base = median_filter(psd_db, size=21, mode="nearest")          # 21 bins x 0.25 Hz = 5 Hz
    ex = psd_db - base
    out = []
    i = 1
    while i < len(f) - 1:
        if freqs_ok[i] and ex[i] >= PEAK_DB and ex[i] >= ex[i - 1] and ex[i] >= ex[i + 1]:
            lo = i
            while lo > 0 and ex[lo - 1] >= PEAK_DB - 3:
                lo -= 1
            hi = i
            while hi < len(f) - 1 and ex[hi + 1] >= PEAK_DB - 3:
                hi += 1
            width = f[hi] - f[lo] + (f[1] - f[0])
            if width <= 1.0:
                out.append((float(f[i]), float(ex[i]), float(width)))
            i = hi + 1
        else:
            i += 1
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--e2b-eeg", required=True, help="epilepsy2bids/src/epilepsy2bids/eeg.py at commit d3fb175")
    ap.add_argument("--pkgs", default=None, help="extra package folder (pyedflib), appended to the END of sys.path")
    ap.add_argument("--allow-other-szcore", action="store_true", help="test only: skip the eeg.py sha256 pin")
    ap.add_argument("--out", default=str(REPO / "results/r2/r0_data/chb12_ref/rb0b"))
    ap.add_argument("--chbmit-dir", default=None, help="CHB-MIT root (default: continuous_eval.DATASET_DIR)")
    ap.add_argument("--summary-dir", default=None, help="default: data/summaries")
    ap.add_argument("--inventory", default=str(REPO / "results/r2/r0_data/chb/inventory.csv"))
    ap.add_argument("--stats", default=str(REPO / "results/r2/r0_data/chb/stats_earlier/chb12_stats.json"))
    a = ap.parse_args(argv)
    t0 = time.time()
    if a.pkgs and a.pkgs not in sys.path:
        sys.path.append(a.pkgs)
    got = sha256_text(a.e2b_eeg)
    if got != SZCORE_EEG_SHA256 and not a.allow_other_szcore:
        raise SystemExit(f"STOP RB0b: {a.e2b_eeg} sha256 {got} != eeg.py at SzCORE commit {SZCORE_COMMIT}")
    resampy_used = ensure_resampy()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    import continuous_eval as CE
    from scipy.signal import welch
    if a.chbmit_dir:
        CE.DATASET_DIR = Path(a.chbmit_dir)
    if a.summary_dir:
        CE.SUMMARY_DIR = Path(a.summary_dir)
    P = RB._P()
    RB.install()
    gates = {}

    # ---------------------------------------------------------------- A inputs
    edfs = CE.list_files(SUBJ)
    import evaluation_protocol as E
    listed = [e["fname"] for e in E.parse_summary_edf_list(CE.SUMMARY_DIR / f"{SUBJ}-summary.txt")]
    present = [e["fname"] for e in edfs]
    inv = pd.read_csv(a.inventory)
    inv = inv[inv["case"] == SUBJ].set_index("file")
    rows = []
    for fn in listed:
        p = CE.edf_path(SUBJ, fn)
        got = sha256(p) if p.exists() else None
        rows.append({"file": fn, "present": p.exists(), "sha256": got,
                     "sha256_physionet": inv.loc[fn, "sha256_physionet"] if fn in inv.index else None,
                     "equal": bool(got is not None and fn in inv.index and got == inv.loc[fn, "sha256_physionet"])})
    A = pd.DataFrame(rows)
    A.to_csv(out / "A_inputs.csv", index=False)
    gates["A_inputs"] = "PASS" if (len(listed) == len(present) and A["equal"].all()
                                    and set(RB.REFERENTIAL) <= set(present)) else "FAIL"
    log(f"A: {len(listed)} listed, {len(present)} present, sha256 equal {int(A['equal'].sum())} -> {gates['A_inputs']}")
    if gates["A_inputs"] != "PASS":
        jdump({"gates": gates}, out / "rb0b.json")
        raise SystemExit("STOP RB0b: inputs (see A_inputs.csv)")

    stats = json.loads(Path(a.stats).read_text())
    thr = np.asarray(stats["artifact_thresh_uV"], dtype=np.float64) * 1e-6
    ch = list(P.COMMON_CHANNELS)
    Eeg = load_szcore(a.e2b_eeg)

    B, C_rows, C_files, C_deriv, D_rows, D_blocks, D_flags, E_peaks = {}, [], [], [], [], [], [], []
    for e in edfs:
        fn = e["fname"]
        path = CE.edf_path(SUBJ, fn)
        ref = fn in RB.REFERENTIAL
        tf = time.time()
        # --- B conversion vs SzCORE
        if ref:
            data, info = RB.derive(path)
            B[fn] = szcore_compare(Eeg, path, data * 1e6, info["labels_used"])
            B[fn]["n_times"] = info["n_times"]
            raw_unf = data
        else:
            raw = P.open_edf(path)
            raw_unf = raw.get_data().astype(np.float64)
            del raw
        # --- C clipping
        r, pf, dv = clipping(path, ref)
        C_rows += r; C_deriv += dv
        pf["referential"] = ref
        C_files.append(pf)
        # --- D amplitude + flags (the pipeline path: wrapper -> continuous_eval.filter_file)
        filt, n = CE.filter_file(path)
        x = filt.astype(np.float64)
        rms = np.sqrt((x ** 2).mean(axis=2)) * 1e6                 # [n, 18] uV
        for i, c in enumerate(ch):
            q = np.percentile(rms[:, i], [25, 50, 75, 95])
            D_rows.append({"file": fn, "referential": ref, "channel": c, "windows": int(n),
                           "rms_q25_uV": q[0], "rms_median_uV": q[1], "rms_q75_uV": q[2], "rms_p95_uV": q[3]})
        bl = BLOCK_S // 4
        for b0 in range(0, n, bl):
            seg = rms[b0:b0 + bl]
            D_blocks.append({"file": fn, "referential": ref, "block_start_s": b0 * 4, "windows": int(len(seg)),
                             **{c: float(np.median(seg[:, i])) for i, c in enumerate(ch)}})
        secs = n * 4
        lab = P.build_labels(secs, e["seizures"]).reshape(n, 4).max(axis=1) == 1
        buf = P.build_buffer_mask(secs, e["seizures"]).reshape(n, 4).any(axis=1)
        peak = np.abs(x).max(axis=2)
        flag_all = (peak > thr[None, :]).any(axis=1)
        flag_c1b = flag_all & ~lab & ~buf
        base = ~lab & ~buf
        D_flags.append({"file": fn, "referential": ref, "windows": int(n), "ictal_windows": int(lab.sum()),
                        "buffer_windows": int((buf & ~lab).sum()), "non_ictal_non_buffer_windows": int(base.sum()),
                        "flag5sd_any_window_share": float(flag_all.mean()),
                        "is_flag5sd_windows": int(flag_c1b.sum()),
                        "is_flag5sd_share_of_non_ictal_non_buffer": float(flag_c1b.sum() / max(1, base.sum())),
                        **{f"exceed_share_{c}": float((peak[:, i] > thr[i]).mean()) for i, c in enumerate(ch)}})
        del filt, x, rms, peak
        # --- E spectrum (unfiltered derived signals)
        f, pxx = welch(raw_unf, fs=256, nperseg=1024, axis=1)
        ok = f >= 0.5
        for i, c in enumerate(ch):
            for fr, prom, w in peaks(f, 10 * np.log10(pxx[i] + 1e-30), ok):
                E_peaks.append({"file": fn, "referential": ref, "channel": c, "freq_hz": fr,
                                "prominence_db": prom, "width_hz": w})
        del raw_unf, pxx
        log(f"{fn}: {'referential' if ref else 'bipolar'}, {n} windows, {time.time() - tf:.1f} s")

    # ---------------------------------------------------------------- gate B + tables
    gB = all(B[f]["labels_equal"] and B[f]["B1_reref"]["max_abs_diff_uV"] <= B1_TOL_UV for f in RB.REFERENTIAL)
    gates["B_szcore_equal"] = "PASS" if gB else "FAIL"
    jdump(B, out / "B_szcore_compare.json")
    pd.DataFrame(C_rows).to_csv(out / "C_clipping_channels.csv", index=False)
    pd.DataFrame(C_files).to_csv(out / "C_clipping_files.csv", index=False)
    pd.DataFrame(C_deriv).to_csv(out / "C_clipping_derivations.csv", index=False)
    D = pd.DataFrame(D_rows)
    D.to_csv(out / "D_rms_files.csv", index=False)
    pd.DataFrame(D_blocks).to_csv(out / "D_rms_blocks_5min.csv", index=False)
    pd.DataFrame(D_flags).to_csv(out / "D_flags.csv", index=False)
    pos = []
    bip = D[~D["referential"]]
    for fn in sorted(RB.REFERENTIAL):
        for c in ch:
            ref_v = float(D[(D.file == fn) & (D.channel == c)]["rms_median_uV"].iloc[0])
            others = bip[bip.channel == c]["rms_median_uV"].to_numpy()
            pos.append({"file": fn, "channel": c, "rms_median_uV": ref_v, "bipolar_files": int(len(others)),
                        "bipolar_min_uV": float(others.min()), "bipolar_median_uV": float(np.median(others)),
                        "bipolar_max_uV": float(others.max()),
                        "ratio_to_bipolar_median": ref_v / float(np.median(others)),
                        "rank_among_bipolar_plus_this": int((others < ref_v).sum()) + 1,
                        "inside_bipolar_range": bool(others.min() <= ref_v <= others.max())})
    pd.DataFrame(pos).to_csv(out / "D_position.csv", index=False)
    Ep = pd.DataFrame(E_peaks, columns=["file", "referential", "channel", "freq_hz", "prominence_db", "width_hz"])
    Ep.to_csv(out / "E_peaks.csv", index=False)
    only = []
    if len(Ep):
        bip_f = set(Ep[~Ep.referential].freq_hz.round(2))
        for (fn, fr), g in Ep[Ep.referential].groupby(["file", Ep.freq_hz.round(2)]):
            if g.channel.nunique() >= 9 and fr not in bip_f:
                only.append({"file": fn, "freq_hz": fr, "channels": int(g.channel.nunique()),
                             "median_prominence_db": float(g.prominence_db.median())})
    pd.DataFrame(only, columns=["file", "freq_hz", "channels", "median_prominence_db"]).to_csv(
        out / "E_peaks_referential_only.csv", index=False)

    import mne, scipy, pyedflib
    res = {"gates": gates, "runtime_s": round(time.time() - t0, 1), "files": len(edfs),
           "b1_tolerance_uV": B1_TOL_UV, "szcore_eeg_py": str(a.e2b_eeg),
           "szcore_eeg_py_sha256_lf": sha256_text(a.e2b_eeg), "szcore_commit": SZCORE_COMMIT, "resampy": resampy_used,
           "versions": {"python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__,
                        "pandas": pd.__version__, "mne": mne.__version__, "pyedflib": pyedflib.__version__}}
    jdump(res, out / "rb0b.json")
    md = [f"# RB0b — chb12_27-29 conversion and amplitude check\n",
          f"Gates: A inputs **{gates['A_inputs']}**, B conversion = SzCORE **{gates['B_szcore_equal']}**; "
          f"runtime {res['runtime_s']} s; {len(edfs)} files.\n",
          "## B conversion vs SzCORE (max |diff| uV, whole file)\n",
          "| file | labels equal | B1 reref | B2 standardize |", "|---|---|---|---|"]
    for f in sorted(RB.REFERENTIAL):
        md.append(f"| {f} | {B[f]['labels_equal']} | {B[f]['B1_reref']['max_abs_diff_uV']:.3g} | "
                  f"{B[f]['B2_standardize']['max_abs_diff_uV']:.3g} |")
    md += ["\n## C clipping (share of 4 s windows with any clipped sample)\n", "| file | windows | share |", "|---|---|---|"]
    for r in C_files:
        md.append(f"| {r['file']} | {r['windows']} | {r['windows_any_clipped_share']:.4f} |")
    md += ["\n## D position of the referential files among the 21 bipolar files (median window RMS)\n",
           "| file | channels inside range | ratio to bipolar median (min / median / max) |", "|---|---|---|"]
    P_ = pd.DataFrame(pos)
    for f, g in P_.groupby("file"):
        md.append(f"| {f} | {int(g.inside_bipolar_range.sum())}/18 | {g.ratio_to_bipolar_median.min():.2f} / "
                  f"{g.ratio_to_bipolar_median.median():.2f} / {g.ratio_to_bipolar_median.max():.2f} |")
    md += ["\n## E narrow spectral peaks in a referential file only (>= 9 channels)\n",
           f"{len(only)} rows (`E_peaks_referential_only.csv`).\n"]
    (out / "SUMMARY.md").write_text("\n".join(md))
    log(f"END gates {gates}; {res['runtime_s']} s")
    RB.uninstall()
    return res


if __name__ == "__main__":
    main()
