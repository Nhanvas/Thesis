#!/usr/bin/env python
"""r2_rb1_synthetic_test.py -- end-to-end test of notebooks/r2/RB1_DATA.ipynb on SYNTHETIC EDF files (build container
only; never on Kaggle, never on real data). Instructions §1 item 15: every gate, every file, every channel, the failure
paths.

World (all written by pyedflib, read by the code under test through mne / its own numpy EDF reader):
  input/combined-siena-scalp-and-chb-mit-eeg-datasets/chbmit/chb12/  4 bipolar files (real CHB layout: dummy '-'
      channels, duplicated T8-P8; seizures; a flat-lined stretch = signal loss; brief artifacts = 5-SD flags; one file
      whose length is not a multiple of 4 s) + chb12_27 (electrodes referenced to CS2; 2 seizures; one electrode
      saturating at +600 uV = a pile-up below the header limit), chb12_28 (bare labels, O1 written "01"; 1 seizure; one
      electrode clipped), chb12_29 (bare labels; 2 seizures; a common-mode excursion of every electrode past +800 uV
      over one whole 4 s window = clipped everywhere, so the derivations are exactly 0 there = signal loss; partial
      clipping elsewhere); the summary; a decoy chb03 file.
  input/thesis-r2-chbmit-features/thesis-r2-chbmit-features/  the 'R0 dataset': chb12 built by R0's own code
      (r2_core.stats_record + features_record, no wrapper: the three files are skipped as in R0) + 23 small decoy cases
      + inventory.csv.
  repo/  a copy of src/ with: data/summaries/chb12-summary.txt (synthetic), results/r2/r0_data/chb/{inventory.csv,
      run_meta.json (versions of this container -> mode exact), stats_earlier/chb12_stats.json},
      results/r2/r1_system/smoke/data_sha256.csv (pin of the R0 dataset + 15 external rows),
      results/r2/r0_data/chb12_ref/rb0b/C_clipping_*.csv written by r2_rb0b.clipping (pyedflib; the laptop's code).
Independent references in this file use pyedflib and numpy only (no record module is imported in this process).
  python src/r2_rb1_synthetic_test.py [--root DIR]
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FS = 256
CHB18 = ["FP1-F7", "F7-T7", "T7-P7", "P7-O1", "FP1-F3", "F3-C3", "C3-P3", "P3-O1", "FP2-F4", "F4-C4", "C4-P4", "P4-O2",
         "FP2-F8", "F8-T8", "T8-P8", "P8-O2", "FZ-CZ", "CZ-PZ"]
ELEC = sorted({e for c in CHB18 for e in c.split("-")})
RAWNAME = "combined-siena-scalp-and-chb-mit-eeg-datasets"
DSNAME = "thesis-r2-chbmit-features"
# file -> (seconds, seizures, kind, extras)
FILES = {
    "chb12_06.edf": (300, [(60, 90)], "bip", dict(flat=(200, 216))),
    "chb12_08.edf": (302, [], "bip", {}),                         # 75 full windows + 2 s
    "chb12_24.edf": (300, [], "bip", {}),
    "chb12_27.edf": (300, [(120, 150), (200, 230)], "cs2", dict(pileup=("FZ", 20, 40))),
    "chb12_28.edf": (300, [(40, 60)], "bare", dict(clip=("O1", 100, 103))),
    "chb12_29.edf": (304, [(30, 50), (200, 230)], "bare", dict(cm_window=60, clip=("C3", 250, 251))),
    "chb12_32.edf": (300, [(200, 230)], "bip", {}),
}
NEW = ["chb12_27.edf", "chb12_28.edf", "chb12_29.edf"]
EXPECT = {"chb12_27.edf": 2, "chb12_28.edf": 1, "chb12_29.edf": 2}
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}", flush=True)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ------------------------------------------------------------------------------------------------ world
def write_edf(path, labels, sig_uV):
    import pyedflib
    heads = []
    for l in labels:
        dummy = l == "-"
        heads.append({"label": l, "dimension": "uV", "sample_frequency": FS,
                      "physical_min": -1.0 if dummy else -800.0, "physical_max": 1.0 if dummy else 800.0,
                      "digital_min": -1 if dummy else -2048, "digital_max": 1 if dummy else 2047,
                      "transducer": "", "prefilter": ""})
    sig = [np.clip(s, h["physical_min"], h["physical_max"]) for s, h in zip(sig_uV, heads)]
    pyedflib.highlevel.write_edf(str(path), sig, heads, digital=False)


def electrode_signals(rng, n, seizures, extra=()):
    names = ELEC + list(extra)
    t = np.arange(n) / FS
    out = {}
    for k, e in enumerate(names):
        w = np.convolve(rng.standard_normal(n), np.ones(8) / 8, mode="same")
        x = 40 * w + 15 * np.sin(2 * np.pi * (6 + 0.3 * k) * t + k)
        for on, off in seizures:                                   # electrode-dependent: survives the subtraction
            a, b = on * FS, off * FS
            x[a:b] += (60 + 9 * k) * np.sin(2 * np.pi * 3 * t[a:b] + 0.4 * k)
        for s0 in rng.integers(0, n - 200, 2):                     # brief artifacts (5-SD flags)
            x[s0:s0 + 64] += (300 + 20 * k) * (1 if k % 2 else -1)
        out[e] = x
    return out


def bipolar_file(path, rng, secs, seizures, flat=None):
    n = secs * FS
    el = electrode_signals(rng, n, seizures)
    labels = CHB18[:13] + ["-"] + CHB18[13:16] + ["-", "FT9-FT10", "FT10-T8", "T8-P8"] + CHB18[16:]
    sig = []
    for l in labels:
        if l == "-":
            sig.append(np.zeros(n))
        elif l in ("FT9-FT10", "FT10-T8"):
            sig.append(30 * rng.standard_normal(n))
        else:
            a, b = l.split("-")
            sig.append(el[a] - el[b])
    if flat:
        for s in sig:
            s[flat[0] * FS:flat[1] * FS] = 0.0
    write_edf(path, labels, sig)


def referential_file(path, rng, secs, seizures, style, pileup=None, clip=None, cm_window=None, boost=None):
    n = secs * FS
    el = electrode_signals(rng, n, seizures, extra=("FT9", "FT10", "CP1"))
    if boost:                                                      # a high-amplitude stretch (used by the RB1b test)
        a, b, g = boost
        for e in el:
            el[e][a * FS:b * FS] *= g
    if pileup:                                                     # amplifier-like saturation below the header limit
        e, a, b = pileup
        seg = el[e][a * FS:b * FS]
        el[e][a * FS:b * FS] = np.minimum(seg + 900, 600.0)       # every sample of the span at 600 uV
    if clip:
        e, a, b = clip
        el[e][a * FS:b * FS] += 2000.0
    if cm_window is not None:                                      # every electrode past +800 uV for one whole window
        for e in el:
            el[e][cm_window * 1024:(cm_window + 1) * 1024] = 950.0
    order = ["F7", "T7", "P7", "-", "FP1", "F3", "C3", "P3", "O1", "-", "FZ", "CZ", "PZ", "-", "FP2", "F4", "C4",
             "P4", "O2", "F8", "T8", "P8", "FT9", "FT10", "CP1"]
    if style == "cs2":
        labels = [("-" if e == "-" else f"{e}-CS2") for e in order]
        sig = [np.zeros(n) if e == "-" else el[e] for e in order]
    else:
        labels = [("-" if e == "-" else ("01" if e == "O1" else e)) for e in order] + ["EKG1-CHIN"]
        sig = [np.zeros(n) if e == "-" else el[e] for e in order] + [200 * np.sin(2 * np.pi * 1.2 * np.arange(n) / FS)]
    write_edf(path, labels, sig)


def hms(s):
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def summary_text():
    L = ["Data Sampling Rate: 256 Hz", "*" * 25, "", "Channels in EDF Files:", "*" * 22]
    L += [f"Channel {i + 1}: {c}" for i, c in enumerate(CHB18)] + [""]
    t = 10 * 3600
    for f, (secs, sz, kind, _) in FILES.items():
        if kind == "cs2":
            L += ["Channels changed:", "*" * 17] + [f"Channel {i + 1}: {e}-CS2" for i, e in enumerate(ELEC)] + [""]
        L += [f"File Name: {f}", f"File Start Time: {hms(t)}", f"File End Time: {hms(t + secs)}",
              f"Number of Seizures in File: {len(sz)}"]
        for k, (a, b) in enumerate(sz):
            L += [f"Seizure {k + 1} Start Time: {a} seconds", f"Seizure {k + 1} End Time:  {b} seconds"]
        L.append("")
        t += secs + 10
    return "\n".join(L) + "\n"


R0_BUILD = r'''
import json, os, sys, numpy as np, pandas as pd
from pathlib import Path
repo, rawroot, out, rb0b = map(Path, sys.argv[1:5])
os.environ.update(THESIS_REPO=str(repo), R2_WORK=str(out / "_w"), R2_INPUT=str(out / "_i"), R2_SCRATCH=str(out / "_s"))
sys.path.insert(0, str(repo / "src"))
import r2_core as R0
st = R0.stats_record("chb12", rawroot, out / "stats.log")              # R0's path: the three files return None
npz = R0.features_record("chb12", rawroot, st, out / "build", out / "feat.log")
(out / "chb12_stats.json").write_text(json.dumps(st, indent=2))
os.replace(npz, out / "chb12.npz")
import r2_rb0b as RB0B
C, F, D = [], [], []
for p in sorted((rawroot / "chbmit" / "chb12").glob("*.edf")):
    ref = p.name in json.loads(sys.argv[5])
    r, pf, dv = RB0B.clipping(p, ref)
    pf["referential"] = ref
    C += r; F.append(pf); D += dv
rb0b.mkdir(parents=True, exist_ok=True)
pd.DataFrame(C).to_csv(rb0b / "C_clipping_channels.csv", index=False)
pd.DataFrame(F).to_csv(rb0b / "C_clipping_files.csv", index=False)
pd.DataFrame(D).to_csv(rb0b / "C_clipping_derivations.csv", index=False)
print("R0 reference built", flush=True)
'''


def build_world(root):
    root = Path(root)
    if root.exists():
        shutil.rmtree(root)
    rng = np.random.default_rng(11)
    raw = root / "input" / RAWNAME
    d = raw / "chbmit" / "chb12"
    d.mkdir(parents=True)
    for f, (secs, sz, kind, ex) in FILES.items():
        if kind == "bip":
            bipolar_file(d / f, rng, secs, sz, **ex)
        else:
            referential_file(d / f, rng, secs, sz, kind, **ex)
    (d / "chb12-summary.txt").write_text(summary_text())
    (raw / "chbmit" / "chb03").mkdir()
    bipolar_file(raw / "chbmit" / "chb03" / "chb03_01.edf", rng, 60, [])          # decoy, never read
    # fake repository
    repo = root / "repo"
    shutil.copytree(ROOT / "src", repo / "src", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "data" / "summaries", repo / "data" / "summaries")
    (repo / "data" / "summaries" / "chb12-summary.txt").write_text(summary_text())
    import pyedflib
    rows = []
    for p in sorted(d.iterdir()):
        r = dict(db="chbmit", relpath=f"chb12/{p.name}", case="chb12", file=p.name, sha256_physionet=sha(p))
        if p.suffix == ".edf":
            with pyedflib.EdfReader(str(p)) as f:
                r.update(n_times=int(f.getNSamples()[0]), sfreq=256.0)
        rows.append(r)
    r0 = repo / "results" / "r2" / "r0_data"
    (r0 / "chb" / "stats_earlier").mkdir(parents=True)
    pd.DataFrame(rows).to_csv(r0 / "chb" / "inventory.csv", index=False)
    import mne, scipy
    import platform
    vers = dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__, mne=mne.__version__)
    (r0 / "chb" / "run_meta.json").write_text(json.dumps({"versions": vers}))
    # R0's chb12 and RB0b's tables, by their own code, in a separate process
    work = root / "r0ref"
    work.mkdir()
    (root / "r0_build.py").write_text(R0_BUILD)
    subprocess.check_call([sys.executable, str(root / "r0_build.py"), str(repo), str(raw), str(work),
                           str(r0 / "chb12_ref" / "rb0b"), json.dumps(NEW)], cwd=str(root))
    shutil.copyfile(work / "chb12_stats.json", r0 / "chb" / "stats_earlier" / "chb12_stats.json")
    # the R0 dataset: chb12 by R0's code + 23 decoys
    ds = root / "input" / DSNAME / DSNAME
    ds.mkdir(parents=True)
    shutil.copyfile(work / "chb12.npz", ds / "chb12.npz")
    shutil.copyfile(work / "chb12_stats.json", ds / "chb12_stats.json")
    for i in range(1, 25):
        c = f"chb{i:02d}"
        if c == "chb12":
            continue
        np.savez(ds / f"{c}.npz", f7=rng.random((5, 18, 7)).astype(np.float32), files=np.array([f"{c}_01.edf"], dtype=object))
        (ds / f"{c}_stats.json").write_text(json.dumps({"subject_id": c, "x": float(rng.random())}))
    shutil.copyfile(r0 / "chb" / "inventory.csv", ds / "inventory.csv")
    pin = [dict(dataset=DSNAME, file=p.name, bytes=p.stat().st_size, sha256=sha(p), source=str(p))
           for p in sorted(ds.iterdir()) if p.name != "inventory.csv"]
    pin += [dict(dataset="thesis-r2-external-features", file=f"PN{i:02d}_lf.npz", bytes=1, sha256=f"{i:064x}", source="x")
            for i in range(15)]
    (repo / "results" / "r2" / "r1_system" / "smoke").mkdir(parents=True)
    pd.DataFrame(pin).to_csv(repo / "results" / "r2" / "r1_system" / "smoke" / "data_sha256.csv", index=False)
    return root, raw, ds, repo


# ------------------------------------------------------------------------------------------------ notebook runner
def run_notebook(nb_path, env):
    """code cells in one namespace (as Kaggle); %%writefile emulated; a fresh import of the module per run."""
    os.environ.update(env)
    [sys.modules.pop(m, None) for m in ("r2_rb1", "r2_core", "r2_rb")]
    nb = json.loads(Path(nb_path).read_text())
    ns = {"__name__": "__main__"}
    t = time.time()
    err = None
    for i, c in enumerate(nb["cells"]):
        if c["cell_type"] != "code":
            continue
        src = "".join(c["source"])
        if src.startswith("%%writefile"):
            first, body = src.split("\n", 1)
            path = re.sub(r"\{(\w+)\}", lambda m: str(ns[m.group(1)]), first.split(None, 1)[1].strip())
            Path(path).write_text(body if body.endswith("\n") else body + "\n")
            continue
        try:
            exec(compile(src, f"{Path(nb_path).name}[cell {i}]", "exec"), ns)
        except RuntimeError as e:
            err = str(e)
            break
    print(f"--- {Path(nb_path).name} {'STOPPED' if err else 'done'} in {time.time() - t:.0f} s", flush=True)
    return ns, err


def env(root, tag, **extra):
    e = dict(R2_TEST="1", R2_TEST_REPO=str(root / "repo"), R2_TEST_INPUT=str(root / "input"),
             R2_TEST_WORK=str(root / f"work_{tag}"), R2_TEST_SCRATCH=str(root / f"scratch_{tag}"),
             R2_TEST_RB1_EXPECT=json.dumps(EXPECT),
             R2_TEST_RB_REFERENTIAL=json.dumps({f: sha(root / "input" / RAWNAME / "chbmit" / "chb12" / f) for f in NEW}))
    e.update(extra)
    return e


def gates_of(root, tag):
    p = root / f"work_{tag}" / "r2" / "r0_data" / "chb12_ref" / "rb1" / "gates.json"
    return json.loads(p.read_text()) if p.exists() else {"gates": []}


def ds_written(root, tag):
    return (root / f"work_{tag}" / "thesis-r2-chbmit-features-rb").exists()


# ------------------------------------------------------------------------------------------------ independent refs
def ref_labels(secs_total_windows, seizures):
    """per-second label arrays (a different formulation from the gate's interval rule)."""
    n = secs_total_windows
    s = np.zeros(n * 4, bool)
    b = np.zeros(n * 4, bool)
    for on, off in seizures:
        s[max(0, on):min(n * 4, off)] = True
        b[off:min(n * 4, off + 4 * 3600)] = True
    return s.reshape(n, 4).any(axis=1), b.reshape(n, 4).any(axis=1)


def ref_clip(path):
    """per-window any-electrode clipped samples, by pyedflib (digital) and a hand label table."""
    import pyedflib
    with pyedflib.EdfReader(str(path)) as f:
        labels = [l.strip().upper() for l in f.getSignalLabels()]
        tab = {}
        for i, l in enumerate(labels):
            e = l[:-4] if l.endswith("-CS2") else l
            e = "O1" if e == "01" else e
            tab.setdefault(e, i)
        cl = {}
        for e in ELEC:
            x = f.readSignal(tab[e], digital=True)
            cl[e] = (x <= f.getDigitalMinimum(tab[e])) | (x >= f.getDigitalMaximum(tab[e]))
            if e == "FZ":
                fz = x
    n = len(cl[ELEC[0]]) // 1024
    a = np.zeros(len(cl[ELEC[0]]), bool)
    for v in cl.values():
        a |= v
    return a, a[:n * 1024].reshape(n, 1024).sum(axis=1), fz


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/tmp/rb1_synth")
    a = ap.parse_args()
    t0 = time.time()
    root, raw, ds, repo = build_world(a.root)
    print(f"world built in {time.time() - t0:.0f} s", flush=True)
    subprocess.check_call([sys.executable, str(ROOT / "src" / "r2_rb1_make_notebook.py")])
    NB = ROOT / "notebooks" / "r2" / "RB1_DATA.ipynb"
    rawd = raw / "chbmit" / "chb12"

    # ================================================================ 1. positive run, mode exact
    ns, err = run_notebook(NB, env(root, "ok"))
    check("positive run: no STOP", err is None, err or "")
    g = gates_of(root, "ok")
    names = [x["gate"] for x in g["gates"]]
    check("positive run: mode exact, every gate PASS in order",
          g["mode"] == "exact" and all(x["status"] == "PASS" for x in g["gates"]) and names == [
              "G-code", "G-raw", "G-R0", "Job A = R0 (wrapper + 21 bipolar files)", "Job B (wrapper + 24 files)",
              "G-clip", "G-copy"], str(names))
    jA = next(x for x in g["gates"] if x["gate"].startswith("Job A"))["detail"]
    check("Job A: bit-equal to R0's chb12 for every array, skipped [] vs the three files",
          all(jA["bit_equal"].values()) and jA["skipped_as_expected"] and len(jA["bit_equal"]) >= 9, str(jA["bit_equal"]))
    out = root / "work_ok" / "r2" / "r0_data" / "chb12_ref" / "rb1"
    dsr = root / "work_ok" / "thesis-r2-chbmit-features-rb"
    names_ds = sorted(p.name for p in dsr.iterdir())
    want_ds = sorted([f"chb{i:02d}.npz" for i in range(1, 25)] + [f"chb{i:02d}_stats.json" for i in range(1, 25)]
                     + ["inventory.csv", "RB1_NOTE.md"])
    check("dataset folder: 24 npz + 24 stats + inventory + note", names_ds == want_ds, str(set(names_ds) ^ set(want_ds)))
    same = all(sha(dsr / p.name) == sha(p) for p in ds.iterdir() if not p.name.startswith("chb12"))
    check("dataset folder: the 23 other cases and inventory are byte copies of R0", same)
    Z = np.load(dsr / "chb12.npz", allow_pickle=True)
    files = [str(x) for x in Z["files"]]
    check("new chb12: every file in summary order, nothing skipped", files == sorted(FILES) and len(Z["skipped_files"]) == 0,
          str(files))
    import pyedflib
    ok_lab, det = True, {}
    for i, f in enumerate(files):
        ix = np.flatnonzero(np.asarray(Z["file_idx"]) == i)
        with pyedflib.EdfReader(str(rawd / f)) as e:
            n = int(e.getNSamples()[0]) // 1024
        li, lb = ref_labels(n, FILES[f][1])
        det[f] = (len(ix), n, bool(np.array_equal(Z["is_ictal"][ix], li)), bool(np.array_equal(Z["is_buffer"][ix], lb)))
        ok_lab &= len(ix) == n and det[f][2] and det[f][3]
    check("new chb12: windows per file and ictal / buffer labels = independent per-second recomputation", ok_lab, str(det))
    i29 = files.index("chb12_29.edf")
    ix29 = np.flatnonzero(np.asarray(Z["file_idx"]) == i29)
    check("chb12_29: the window clipped on every electrode is a signal-loss window (derivations exactly 0)",
          bool(Z["is_signal_loss"][ix29][60]) and int(Z["is_signal_loss"][ix29].sum()) == 1)
    i06 = files.index("chb12_06.edf")
    check("bipolar flat stretch still flagged signal loss (chb12_06, 4 windows)",
          int(Z["is_signal_loss"][np.asarray(Z["file_idx"]) == i06].sum()) == 4)
    # the common files' features differ from R0's only through the statistics: kurtosis invariant, log powers shifted
    R0z = np.load(ds / "chb12.npz", allow_pickle=True)
    stA = json.loads((ds / "chb12_stats.json").read_text())
    stB = json.loads((dsr / "chb12_stats.json").read_text())
    rf = [str(x) for x in R0z["files"]]
    kmax, pmax = 0.0, 0.0
    shift = -2 * np.log(np.asarray(stB["ch_std_uV"]) / np.asarray(stA["ch_std_uV"]))
    for j, f in enumerate(rf):
        ia = np.flatnonzero(np.asarray(R0z["file_idx"]) == j)
        ib = np.flatnonzero(np.asarray(Z["file_idx"]) == files.index(f))
        ok = ~np.asarray(R0z["is_signal_loss"])[ia]
        fa, fb = np.asarray(R0z["f7"])[ia][ok], np.asarray(Z["f7"])[ib][ok]
        kmax = max(kmax, float(np.abs(fa[..., 6] - fb[..., 6]).max()))
        pmax = max(pmax, float(np.abs((fb[..., 1:5] - fa[..., 1:5]) - shift[None, :, None]).max()))
    check("common files: kurtosis feature unchanged and log band powers shifted by -2 log(SD ratio) (only the stats changed)",
          kmax < 1e-3 and pmax < 1e-3, f"(kurtosis {kmax:.1e}, log power {pmax:.1e})")
    # clipping vs independent pyedflib reading
    W = pd.read_csv(out / "clipping_windows.csv")
    S = pd.read_csv(out / "clipping_seizures.csv")
    ok_c, sz_c = True, 0
    for f in NEW:
        anyc, win, fz = ref_clip(rawd / f)
        mine = W[W.file == f].sort_values("window").any_clipped_samples.to_numpy()
        ok_c &= np.array_equal(mine, win)
        for on, off in FILES[f][1]:
            sz_c += int(anyc[on * FS:off * FS].any())
    check("clipping per window = independent pyedflib reading (all three files)", ok_c)
    check("clipping per seizure = independent count", int((S.any_clipped_samples > 0).sum()) == sz_c and len(S) == 5,
          f"({int((S.any_clipped_samples > 0).sum())} vs {sz_c})")
    T = pd.read_csv(out / "clipping_histogram_tails.csv")
    tz = T[(T.file == "chb12_27.edf") & (T.electrode == "FZ")].iloc[0]
    fz = ref_clip(rawd / "chb12_27.edf")[2]
    fz_vals, fz_cnt = np.unique(fz[(fz > -2048) & (fz < 2047)], return_counts=True)
    check("histogram tail: the pile-up below the header limit is listed first (chb12_27 FZ)",
          int(tz.top1_value) == int(fz_vals[np.argmax(fz_cnt)]) and tz.top1_share_of_tail > 0.5 and tz.at_digital_max == 0,
          f"(value {tz.top1_value}, share {tz.top1_share_of_tail:.2f})")
    W2 = W.copy()
    ww = W2[(W2.file == "chb12_29.edf") & (W2.window == 60)].iloc[0]
    check("window table carries the labels (chb12_29 window 60: 1024 clipped samples, signal loss, 18 derivations)",
          ww.any_clipped_samples == 1024 and bool(ww.is_signal_loss) and ww.derivations_affected == 18)
    pin_new = pd.read_csv(out / "data_sha256.csv")
    pin_old = pd.read_csv(repo / "results" / "r2" / "r1_system" / "smoke" / "data_sha256.csv")
    m = pin_new.file.str.startswith("chb12")
    check("new pin: 63 rows, only the two chb12 rows changed, = the dataset files",
          len(pin_new) == 63 and pin_new[~m].reset_index(drop=True)[["dataset", "file", "sha256"]].equals(
              pin_old[~pin_old.file.str.startswith("chb12")].reset_index(drop=True)[["dataset", "file", "sha256"]])
          and all(pin_new[pin_new.file == n].sha256.iloc[0] == sha(dsr / n) for n in ("chb12.npz", "chb12_stats.json")))
    D = json.loads((out / "diff_chb12.json").read_text())["chb12"]
    want_add = {f: (FILES[f][0] * FS) // 1024 for f in NEW}
    check("diff report: files, windows and seizures added",
          D["files_added"] == NEW and D["windows_added"] == want_add and D["seizures"] == [2, 7]
          and D["clean_windows"][1] == int(((~Z["is_ictal"]) & (~Z["is_buffer"]) & (~Z["is_signal_loss"]) & (~Z["is_flag5sd"])).sum()),
          str({k: D[k] for k in ("windows_added", "seizures")}))
    meta = json.loads((out / "run_meta.json").read_text())
    check("run metadata: runtime measured, SUMMARY written", "runtime_h" in meta and (out / "SUMMARY.md").exists())
    # G-copy failure path, function level (a copy that corrupts one byte): STOP, dataset folder unchanged
    good = sha(dsr / "chb01.npz")

    def bad_copy(s, d):
        shutil.copyfile(s, d)
        if Path(d).name == "chb05.npz":
            b = bytearray(Path(d).read_bytes())
            b[-3] ^= 0xFF
            Path(d).write_bytes(bytes(b))
    bn = Path(ns["DONE"]["B"]["npz"])                               # the END cell removed the build folder
    bn.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(dsr / "chb12.npz", bn)
    try:
        ns["B"].build_dataset(ns["DONE"], ns["R0_PATHS"], ns["R0_INV"], copy=bad_copy)
        check("G-copy: a corrupted copy STOPs", False)
    except SystemExit as e:
        check("G-copy: a corrupted copy STOPs, the dataset folder is untouched and no partial folder is left",
              "G-copy" in str(e) and sha(dsr / "chb01.npz") == good
              and not (root / "work_ok" / ".rb1_dataset_partial").exists(), str(e)[:80])

    # ================================================================ 2. negative paths (each STOPs at its gate, no dataset)
    def neg(tag, gate_name, **extra):
        _, err = run_notebook(NB, env(root, tag, **extra))
        gs = gates_of(root, tag)["gates"]
        last = gs[-1] if gs else {}
        check(f"STOP at {gate_name}", err is not None and last.get("gate", "").startswith(gate_name)
              and last.get("status") == "FAIL" and not ds_written(root, tag), (err or "no STOP")[:110])

    pre = repo / "src" / "dataprep" / "preprocessing.py"
    keep = pre.read_text()
    pre.write_text(keep + "\n# edited\n")
    neg("n_code", "G-code")
    pre.write_text(keep)
    wrong = json.loads(env(root, "x")["R2_TEST_RB_REFERENTIAL"])
    wrong["chb12_28.edf"] = "0" * 64
    neg("n_ref", "G-code", R2_TEST_RB_REFERENTIAL=json.dumps(wrong))
    tgt = rawd / "chb12_32.edf"
    keepb = tgt.read_bytes()
    b = bytearray(keepb)
    b[-10] ^= 0xFF
    tgt.write_bytes(bytes(b))
    neg("n_raw", "G-raw")
    tgt.write_bytes(keepb)
    st5 = ds / "chb05_stats.json"
    keep5 = st5.read_text()
    st5.write_text(keep5.replace('"x"', '"y"'))
    neg("n_r0", "G-R0")
    st5.write_text(keep5)
    neg("n_expect", "Job B", R2_TEST_RB1_EXPECT=json.dumps({"chb12_27.edf": 3, "chb12_28.edf": 1, "chb12_29.edf": 2}))
    cc = repo / "results" / "r2" / "r0_data" / "chb12_ref" / "rb0b" / "C_clipping_channels.csv"
    keepc = cc.read_text()
    C = pd.read_csv(cc, dtype={"label": str})
    k = C.index[(C.file == "chb12_28.edf") & (C.channel == "O1")][0]
    C.loc[k, "clipped_samples"] += 1
    C.to_csv(cc, index=False)
    neg("n_clip", "G-clip")
    cc.write_text(keepc)
    # a referential file with an electrode twice (C4 for C3): inventory and REFERENTIAL agree -> the wrapper STOPs in Job B
    f28 = rawd / "chb12_28.edf"
    keep28 = f28.read_bytes()
    bb = bytearray(keep28)
    hdr = bytes(bb[256:256 + 16 * 30]).decode("ascii")
    pos = [i for i in range(0, len(hdr), 16) if hdr[i:i + 16].strip() == "C3"][0]
    bb[256 + pos:256 + pos + 16] = b"C4".ljust(16)
    f28.write_bytes(bytes(bb))
    invp = repo / "results" / "r2" / "r0_data" / "chb" / "inventory.csv"
    keepinv = invp.read_text()
    inv = pd.read_csv(invp)
    inv.loc[inv.file == "chb12_28.edf", "sha256_physionet"] = sha(f28)
    inv.to_csv(invp, index=False)
    r2 = json.loads(env(root, "x")["R2_TEST_RB_REFERENTIAL"])
    neg("n_dup", "Job B", R2_TEST_RB_REFERENTIAL=json.dumps(r2))
    gs = gates_of(root, "n_dup")["gates"]
    check("  ... the STOP comes from the wrapper (electrode not found exactly once)",
          bool(gs) and "electrodes not found exactly once" in gs[-1].get("error", ""), gs[-1].get("error", "")[-120:] if gs else "")
    f28.write_bytes(keep28)
    invp.write_text(keepinv)

    # ================================================================ 3. Job A: exact vs tolerance on a float-level difference
    stp = repo / "results" / "r2" / "r0_data" / "chb" / "stats_earlier" / "chb12_stats.json"
    keepst = stp.read_text()
    st = json.loads(keepst)
    st["ch_std_uV"][3] *= 1 + 1e-7
    stp.write_text(json.dumps(st, indent=2))
    neg("n_exact", "Job A")
    rm = repo / "results" / "r2" / "r0_data" / "chb" / "run_meta.json"
    keeprm = rm.read_text()
    v = json.loads(keeprm)
    v["versions"]["numpy"] = "0.0.0"
    rm.write_text(json.dumps(v))
    _, err = run_notebook(NB, env(root, "tol"))
    g = gates_of(root, "tol")
    check("tolerance mode (numpy differs from R0's): the same 1e-7 difference passes Job A, every gate PASS",
          err is None and g["mode"] == "tolerance" and all(x["status"] == "PASS" for x in g["gates"])
          and ds_written(root, "tol"), (err or "")[:100])
    stp.write_text(keepst)
    rm.write_text(keeprm)

    n_ok = sum(r[1] for r in RESULTS)
    print(f"\n{n_ok}/{len(RESULTS)} checks PASS in {time.time() - t0:.0f} s")
    print("ALL PASS" if n_ok == len(RESULTS) else "FAILURES: " + "; ".join(r[0] for r in RESULTS if not r[1]))
    sys.exit(0 if n_ok == len(RESULTS) else 1)


if __name__ == "__main__":
    main()
