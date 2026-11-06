#!/usr/bin/env python
"""r2_synthetic_test.py -- end-to-end test of the stage R0 notebooks on SYNTHETIC EDF files (build container only;
never on Kaggle, never on real data). Builds:
  physionet/   a fake PhysioNet tree (CHB-MIT-like and Siena-like EDF files, summaries, seizure lists) + SHA256SUMS.txt,
               served through file:// URLs (R2_PHYSIONET_*), so downloads use the real code path;
  input/       a fake Kaggle input: the raw copy with two gap files ABSENT and one file CORRUPTED (both must come from
               'PhysioNet'), plus v9-x3-fold1/3 with the EARLIER .npz built by the record code on the earlier file set;
  repo/        a copy of the repository whose data/summaries and data/processed/*_stats.json for the synthetic cases
               come from the record code on the earlier file set (= what the laptop committed).
Then runs R0_SMOKE, R0_CHB, R0_EXT cell by cell (the %%writefile cell is emulated) and checks: every gate PASS,
datasets complete, gap files downloaded, diff report, external hours; and two negative paths: a perturbed committed
stats.json must STOP G-stats, a flipped flag in an earlier .npz must STOP G-feat.
  python src/r2_synthetic_test.py [--root DIR]
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

ROOT = Path(__file__).resolve().parents[1]
CHB18 = ["FP1-F7", "F7-T7", "T7-P7", "P7-O1", "FP1-F3", "F3-C3", "C3-P3", "P3-O1", "FP2-F4", "F4-C4", "C4-P4", "P4-O2",
         "FP2-F8", "F8-T8", "T8-P8", "P8-O2", "FZ-CZ", "CZ-PZ"]
EXTRA = ["P7-T7", "T7-FT9", "FT9-FT10", "FT10-T8", "T8-P8"]          # real CHB files repeat T8-P8 (-> 'T8-P8-1')
SIENA_EL = ["Fp1", "F3", "C3", "P3", "O1", "F7", "T3", "T5", "Fz", "Cz", "Pz", "Fp2", "F4", "C4", "P4", "O2", "F8",
            "T4", "T6", "F9"]
MIN = 60
# case -> list of (file, minutes, seizures [(on, off) s], flat window range or None)
CHB = {
    "chb03": [("chb03_01.edf", 8, [], (50, 56)), ("chb03_02.edf", 8, [(300, 340)], None)],
    "chb11": [("chb11_01.edf", 6, [], None), ("chb11_02.edf", 6, [(200, 236)], None), ("chb11_03.edf", 5, [], None),
              ("chb11_04.edf", 5, [], None), ("chb11_12.edf", 6, [], None), ("chb11_13.edf", 6, [(100, 130)], None)],
    "chb12": [("chb12_01.edf", 6, [(120, 150)], None), ("chb12_27.edf", 5, [(60, 90)], None)],
    "chb21": [("chb21_01.edf", 6, [], None), ("chb21_11.edf", 6, [], None), ("chb21_12.edf", 6, [(250, 280)], None)],
    "chb24": [("chb24_01.edf", 6, [(150, 190)], None), ("chb24_02.edf", 6, [], None)],
}
SIENA = {"PN00": [("PN00-1.edf", 7, (60, 100)), ("PN00-2.edf", 6, (200, 230))],
         "PN03": [("PN03-1.edf", 6, (120, 150))]}
GAP = {"chb11_12.edf", "chb11_13.edf", "chb21_11.edf"}            # absent from the fake Kaggle copy and the laptop copy
CORRUPT = "chb03_02.edf"                                           # different bytes on the fake Kaggle copy


def write_chb_edf(path, minutes, seizures, flat, seed, missing=None):
    import pyedflib
    rng = np.random.default_rng(seed)
    labels = [c for c in CHB18 if c != missing] + EXTRA
    n = minutes * MIN * 256
    t = np.arange(n) / 256
    sig = []
    for i, _ in enumerate(labels):
        x = rng.normal(0, 25 + 2 * (i % 7), n) + 15 * np.sin(2 * np.pi * (6 + i % 5) * t + i)
        for on, off in seizures:
            a, b = on * 256, off * 256
            x[a:b] += 180 * np.sin(2 * np.pi * 3 * t[a:b])
        for k in rng.integers(0, n - 512, 3):                       # brief artifacts (5 SD flags)
            x[k:k + 128] += rng.choice([-1, 1]) * 900
        if flat is not None:
            x[flat[0] * 1024:flat[1] * 1024] = 0.0
        sig.append(np.clip(x, -2900, 2900))
    w = pyedflib.EdfWriter(str(path), len(labels), file_type=pyedflib.FILETYPE_EDF)
    w.setSignalHeaders([dict(label=l, dimension="uV", sample_frequency=256, physical_max=3000, physical_min=-3000,
                             digital_max=32767, digital_min=-32768, transducer="", prefilter="") for l in labels])
    w.writeSamples(sig)
    w.close()


def write_siena_edf(path, minutes, seizure, seed):
    import pyedflib
    rng = np.random.default_rng(seed)
    labels = [f"EEG {e}" for e in SIENA_EL] + ["EKG EKG"]
    n = minutes * MIN * 512
    t = np.arange(n) / 512
    sig = []
    for i, _ in enumerate(labels):
        x = rng.normal(0, 20 + i % 6, n) + 10 * np.sin(2 * np.pi * (8 + i % 4) * t)
        a, b = seizure[0] * 512, seizure[1] * 512
        x[a:b] += 150 * np.sin(2 * np.pi * 4 * t[a:b])
        x += 12 * np.sin(2 * np.pi * 50 * t)
        sig.append(np.clip(x, -2900, 2900))
    w = pyedflib.EdfWriter(str(path), len(labels), file_type=pyedflib.FILETYPE_EDF)
    w.setSignalHeaders([dict(label=l, dimension="uV", sample_frequency=512, physical_max=3000, physical_min=-3000,
                             digital_max=32767, digital_min=-32768, transducer="", prefilter="") for l in labels])
    w.writeSamples(sig)
    w.close()


def hms(s):
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def chb_summary(case, files):
    L = ["Data Sampling Rate: 256 Hz", "*" * 25, "", "Channels in EDF Files:", "*" * 22]
    L += [f"Channel {i + 1}: {c}" for i, c in enumerate(CHB18 + EXTRA)] + [""]
    t = 10 * 3600
    for f, m, sz, _ in files:
        if case == "chb24":
            if not sz:
                continue                                           # chb24 lists only the files with seizures
            L += [f"File Name: {f}", f"Number of Seizures in File: {len(sz)}"]
        else:
            L += [f"File Name: {f}", f"File Start Time: {hms(t)}", f"File End Time: {hms(t + m * MIN)}",
                  f"Number of Seizures in File: {len(sz)}"]
        for k, (a, b) in enumerate(sz):
            pre = f"Seizure {k + 1} " if case in ("chb24", "chb12") else "Seizure "
            L += [f"{pre}Start Time: {a} seconds", f"{pre}End Time: {b} seconds"]
        L.append("")
        t += m * MIN + 600
    return "\n".join(L) + "\n"


def siena_list(case, files):
    L = [f"Patient id number:{int(case[2:])}", ""]
    t = 9 * 3600
    for k, (f, m, (a, b)) in enumerate(files):
        dot = lambda s: f"{s // 3600:02d}.{s % 3600 // 60:02d}.{s % 60:02d}"   # noqa: E731
        L += [f"Seizure n {k + 1}", f"File name: {f}", f"Registration start time: {dot(t)}",
              f"Registration end time: {dot(t + m * MIN)}", f"Seizure start time: {dot(t + a)}",
              f"Seizure end time: {dot(t + b)}", ""]
        t += m * MIN + 900
    return "\n".join(L) + "\n"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build_world(root):
    root = Path(root)
    if root.exists():
        shutil.rmtree(root)
    phys = root / "physionet"
    for db in ("chbmit", "siena"):
        (phys / db).mkdir(parents=True)
    seed = 0
    for case, files in CHB.items():
        d = phys / "chbmit" / case
        d.mkdir()
        for f, m, sz, flat in files:
            seed += 1
            write_chb_edf(d / f, m, sz, flat, seed, missing="FZ-CZ" if f == "chb12_27.edf" else None)
        (d / f"{case}-summary.txt").write_text(chb_summary(case, files))
    for case, files in SIENA.items():
        d = phys / "siena" / case
        d.mkdir()
        for f, m, s in files:
            seed += 1
            write_siena_edf(d / f, m, s, seed)
        (d / f"Seizures-list-{case}.txt").write_text(siena_list(case, files))
    for db in ("chbmit", "siena"):
        lines = [f"{sha(p)} {p.relative_to(phys / db).as_posix()}" for p in sorted((phys / db).rglob("*")) if p.is_file()]
        (phys / db / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n")
    # fake Kaggle raw copy: gap files absent, one file corrupted
    raw = root / "input" / "combined-siena-scalp-and-chb-mit-eeg-datasets"
    for db in ("chbmit", "siena"):
        for p in sorted((phys / db).rglob("*")):
            if p.is_file() and p.name != "SHA256SUMS.txt" and p.name not in GAP:
                q = raw / db / p.relative_to(phys / db)
                q.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(p, q)
    c = next((raw / "chbmit").rglob(CORRUPT))
    b = bytearray(c.read_bytes())
    b[-100] ^= 0xFF
    c.write_bytes(bytes(b))
    # laptop copy (earlier set) and the fake repository
    lap = root / "laptop" / "CHB-MIT"
    for case in CHB:
        (lap / case).mkdir(parents=True)
        for p in (phys / "chbmit" / case).iterdir():
            if p.name not in GAP:
                shutil.copyfile(p, lap / case / p.name)
    repo = root / "repo"
    shutil.copytree(ROOT / "src", repo / "src", ignore=shutil.ignore_patterns("__pycache__"))
    for sub in ("data/summaries", "data/processed", "results/x1_external", "results/p3c_freeze"):
        shutil.copytree(ROOT / sub, repo / sub)
    for case in CHB:
        if case != "chb24":
            shutil.copyfile(phys / "chbmit" / case / f"{case}-summary.txt", repo / "data" / "summaries" / f"{case}-summary.txt")
    return root, phys, raw, lap, repo


RECORD = r'''
import json, sys, numpy as np
from pathlib import Path
repo, lap, out1, out3 = map(Path, sys.argv[1:5])
for p in ("src", "src/dataprep", "src/retrain", "src/phaseB", "src/phaseC"):
    sys.path.insert(0, str(repo / p))
import preprocessing as P, continuous_eval as CE, c1b_build_trainset as C1B, v9_x3_build_chb24 as B24
CE.DATASET_DIR = lap
B24.RAW_DIR = lap; B24.SUMMARY_PATH = lap / "chb24" / "chb24-summary.txt"
cases = sys.argv[5].split(",")
for i, case in enumerate(cases):
    out = out1 if i % 2 == 0 else out3
    if case != "chb24":
        smap = P.parse_summary(repo / "data" / "summaries" / f"{case}-summary.txt")
        m, s = P.compute_subject_stats(case, lap, smap)
        thr = P.ARTIFACT_SD_MULTIPLIER * s
        ni, nc, nr = P.count_windows(case, lap, smap, thr)
        st = {"subject_id": case, "n_interictal": ni, "n_ictal": nc, "n_rejected": nr, "ratio": round(ni / max(nc, 1), 1),
              "ch_mean_uV": (m * 1e6).tolist(), "ch_std_uV": (s * 1e6).tolist(), "artifact_thresh_uV": (thr * 1e6).tolist()}
        (repo / "data" / "processed" / f"{case}_stats.json").write_text(json.dumps(st, indent=2))
        C1B.build(case, out_dir=out, allow_test=True)
    else:
        B24.OUT = out / "_b24"; B24.XCACHE = out / "_none.npz"
        B24.build()
        (out / "_b24" / "chb24.npz").replace(out / "chb24.npz")
        import shutil; shutil.rmtree(out / "_b24")
    print("record built", case, flush=True)
'''


def run_notebook(nb_path, env):
    """executes the code cells in one namespace (as Kaggle would); %%writefile is emulated with IPython-style {var}."""
    os.environ.update(env)
    nb = json.loads(Path(nb_path).read_text())
    ns = {"__name__": "__main__"}
    t = time.time()
    for i, c in enumerate(nb["cells"]):
        if c["cell_type"] != "code":
            continue
        src = "".join(c["source"])
        if src.startswith("%%writefile"):
            first, body = src.split("\n", 1)
            path = re.sub(r"\{(\w+)\}", lambda m: str(ns[m.group(1)]), first.split(None, 1)[1].strip())
            Path(path).write_text(body if body.endswith("\n") else body + "\n")
            continue
        exec(compile(src, f"{Path(nb_path).name}[cell {i}]", "exec"), ns)
    print(f"--- {Path(nb_path).name} done in {time.time() - t:.0f} s")
    for k in ("R",):
        sys.modules.pop("r2_core", None)
    return ns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/tmp/r2_synth")
    a = ap.parse_args()
    t0 = time.time()
    root, phys, raw, lap, repo = build_world(a.root)
    out1 = root / "input" / "v9-x3-fold1"
    out3 = root / "input" / "v9-x3-fold3"
    out1.mkdir(parents=True)
    out3.mkdir(parents=True)
    rec = root / "record_build.py"
    rec.write_text(RECORD)
    subprocess.check_call([sys.executable, "-I", str(rec), str(repo), str(lap), str(out1), str(out3), ",".join(CHB)])
    subprocess.check_call([sys.executable, str(ROOT / "src" / "r2_make_notebooks.py")])
    print(f"world built in {time.time() - t0:.0f} s")

    def env(tag):
        return dict(R2_TEST="1", R2_TEST_EARLIER_MISSING=json.dumps({"chb11": ["chb11_12.edf", "chb11_13.edf"],
                                                                     "chb21": ["chb21_11.edf"]}),
                    R2_TEST_REPO=str(repo), R2_TEST_INPUT=str(root / "input"), R2_TEST_WORK=str(root / f"work_{tag}"),
                    R2_TEST_SCRATCH=str(root / f"scratch_{tag}"), R2_TEST_CASES=",".join(CHB),
                    R2_PHYSIONET_CHBMIT=(phys / "chbmit").as_uri() + "/", R2_PHYSIONET_SIENA=(phys / "siena").as_uri() + "/")

    nbdir = ROOT / "notebooks" / "r2"
    results = {}
    # ---- R0_SMOKE
    run_notebook(nbdir / "R0_SMOKE.ipynb", env("smoke"))
    sm = root / "work_smoke" / "r2" / "r0_data" / "smoke"
    inv = __import__("pandas").read_csv(sm / "inventory.csv")
    src = dict(zip(inv.file, inv.source))
    assert all(src[f].startswith("physionet: absent") for f in GAP), src
    assert src[CORRUPT] == "physionet: Kaggle copy differs", src[CORRUPT]
    g = json.loads((sm / "gates.json").read_text())
    assert g["status"] == "PASS" and g["G_stats"]["chb11"]["status"] == "PASS", g
    assert len(g["G_feat"]) == 3 and all(v["status"] == "PASS" for v in g["G_feat"].values()), g["G_feat"]
    assert (sm / "projection.json").exists()
    results["R0_SMOKE"] = "PASS"
    # ---- R0_CHB
    run_notebook(nbdir / "R0_CHB.ipynb", env("chb"))
    ch = root / "work_chb"
    g = json.loads((ch / "r2" / "r0_data" / "chb" / "gates.json").read_text())
    assert g["status"] == "PASS", g["status"]
    assert set(g["G_stats"]) == set(CHB) and g["G_stats"]["chb24"]["status"].startswith("n/a"), g["G_stats"].keys()
    assert all(v["status"] == "PASS" for c, v in g["G_stats"].items() if c != "chb24")
    assert all(v["status"] == "PASS" for v in g["G_feat"].values()) and set(g["G_feat"]) == set(CHB)
    ds = ch / "thesis-r2-chbmit-features"
    assert sorted(p.name for p in ds.glob("*.npz")) == sorted(f"{c}.npz" for c in CHB)
    z11 = np.load(ds / "chb11.npz", allow_pickle=True)
    assert [str(x) for x in z11["files"]] == [f for f, *_ in CHB["chb11"]], z11["files"]
    z12 = np.load(ds / "chb12.npz", allow_pickle=True)
    assert [str(x) for x in z12["skipped_files"]] == ["chb12_27.edf"]
    d = json.loads((ch / "r2" / "r0_data" / "chb" / "diff_chb11_chb21.json").read_text())
    assert d["chb11"]["files_added"] == ["chb11_12.edf", "chb11_13.edf"] and d["chb21"]["files_added"] == ["chb21_11.edf"]
    assert d["chb11"]["seizure_windows_identical_in_common_files"] is True
    assert d["chb11"]["seizure_windows_in_added_files"] > 0                      # synthetic chb11_13 has a seizure
    assert d["chb21"]["seizure_windows_identical_in_common_files"] is True and d["chb21"]["seizure_windows_in_added_files"] == 0
    st11 = json.loads((ds / "chb11_stats.json").read_text())
    assert st11["r2"]["files_globbed"] == [f for f, *_ in CHB["chb11"]]
    results["R0_CHB"] = "PASS"
    # ---- R0_EXT
    run_notebook(nbdir / "R0_EXT.ipynb", env("ext"))
    ex = root / "work_ext" / "thesis-r2-external-features"
    assert sorted(p.name for p in ex.glob("*_lf.npz")) == sorted(["chb24_lf.npz"] + [f"{c}_lf.npz" for c in SIENA])
    m = json.loads(str(np.load(ex / "PN00_lf.npz", allow_pickle=True)["meta"]))
    assert m["kind"] == "siena" and len(m["labelfree_std_uV"]) == 18 and int(np.load(ex / "PN00_lf.npz", allow_pickle=True)["is_ictal"].sum()) > 0
    results["R0_EXT"] = "PASS"
    # ---- R0_EXT resume: the previous output attached as an input -> every case skipped, files identical
    prev = root / "input" / "r0-ext-previous-output" / "thesis-r2-external-features"
    shutil.copytree(ex, prev)
    run_notebook(nbdir / "R0_EXT.ipynb", env("ext2"))
    ex2 = root / "work_ext2" / "thesis-r2-external-features"
    assert all(sha(ex / p.name) == sha(p) for p in ex2.glob("*_lf.npz")) and len(list(ex2.glob("*_lf.npz"))) == 3
    shutil.rmtree(prev.parent)
    results["R0_EXT resume"] = "PASS (previous output reused, files identical)"
    # ---- negative paths: G-stats and G-feat must STOP
    sj = repo / "data" / "processed" / "chb11_stats.json"
    keep = sj.read_text()
    st = json.loads(keep)
    st["ch_std_uV"][3] *= 1 + 1e-5
    sj.write_text(json.dumps(st))
    try:
        run_notebook(nbdir / "R0_SMOKE.ipynb", env("neg1"))
        raise AssertionError("G-stats did not stop")
    except RuntimeError as e:
        assert "STOPPED" in str(e) and "G-stats" in str(e), e
        results["negative G-stats"] = "STOP as expected"
    sj.write_text(keep)
    ref = out1 / "chb03.npz"
    keepb = ref.read_bytes()
    z = dict(np.load(ref, allow_pickle=True))
    i = int(np.flatnonzero(~z["is_ictal"])[5])
    z["is_flag5sd"] = z["is_flag5sd"].copy()
    z["is_flag5sd"][i] = ~z["is_flag5sd"][i]
    np.savez(ref, **z)
    try:
        run_notebook(nbdir / "R0_CHB.ipynb", env("neg2"))
        raise AssertionError("G-feat did not stop")
    except RuntimeError as e:
        assert "STOPPED" in str(e) and "chb03" in str(e), e
        assert not (root / "work_neg2" / "thesis-r2-chbmit-features").exists(), "dataset written after a failed gate"
        results["negative G-feat"] = "STOP as expected, no dataset written"
    ref.write_bytes(keepb)
    print(json.dumps(results, indent=1))
    print(f"ALL SYNTHETIC TESTS PASS in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
