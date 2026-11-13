#!/usr/bin/env python
"""r2_rb1c_synthetic_test.py -- end-to-end test of src/r2_rb1c.py on SYNTHETIC EDF files (build container only; never on
real data). Instructions §1 item 15: every gate, every case type, every file, the failure paths.

World (EDF files written by pyedflib, helpers of src/r2_rb1_synthetic_test.py):
  CHB-MIT  chb01  2 bipolar files; chb01_02 has a planted high-amplitude stretch (every electrode x6, one electrode past
                  the digital limit) = the cause the survey must find;
           chb11  3 bipolar files; the "earlier" statistic is built on the first 2 (as R0's chb11 / chb21: committed
                  earlier statistic + committed relative change);
           chb12  2 bipolar + chb12_27 (referenced to CS2, x5 before its seizure) + chb12_28 (bare labels): read only
                  through the wrapper r2_rb (24-file case of RB1);
           chb24  1 bipolar file: statistic gated, flags not gated (no committed count, as on the laptop).
  Siena    PN05   2 referential files at 512 Hz ("EEG Fp1", "EEG T3", ...; seizure list in the standard format); one
                  planted stretch: every electrode x6 + one electrode past the digital limit.
  The "committed" references of the fake repository are produced by the RECORD code in a separate process
  (r2_core.stats_record / features_record with the wrapper installed; x1 windows from the file lengths), never by
  r2_rb1c. Independent references in this process use pyedflib and numpy only.
Checks: gates PASS (chb24 flags NOT GATED); the planted stretch is found in chb01 and PN05 (no-clip SD lower, largest
file, top windows inside the stretch); sampled windows = an independent re-implementation of both sampling rules;
windows with clipped samples = an independent pyedflib count; flag grid consistent (record x5 = gate count; monotone;
the "same count" multiplier brackets the record count); robust scales of normal data = sigma; shares sum to 1; failure
paths STOP at their gate.
  python src/r2_rb1c_synthetic_test.py [--root DIR]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import r2_rb1_synthetic_test as T  # noqa: E402

RES = []
FS = 256
# case -> file -> (seconds, seizures, kind, extras); seizures late in a file (the 4 h buffer covers the rest)
WORLD = {
    "chb01": {"chb01_01.edf": (300, [(250, 280)], "bip", {}),
              "chb01_02.edf": (400, [], "bip", dict(boost=(40, 120, 6.0), spike=("C3", 60, 64)))},
    "chb11": {"chb11_01.edf": (300, [(260, 290)], "bip", {}), "chb11_02.edf": (300, [], "bip", {}),
              "chb11_12.edf": (300, [], "bip", dict(boost=(0, 60, 3.0)))},
    "chb12": {"chb12_06.edf": (300, [(250, 280)], "bip", {}), "chb12_08.edf": (300, [], "bip", {}),
              "chb12_27.edf": (300, [(220, 250)], "cs2", dict(boost=(0, 100, 5.0))),
              "chb12_28.edf": (300, [(240, 260)], "bare", {})},
    "chb24": {"chb24_01.edf": (300, [(250, 270)], "bip", {})},
}
REFERENTIAL = ["chb12_27.edf", "chb12_28.edf"]
SIENA = {"PN05-2.edf": (400, [(300, 340)], {}), "PN05-4.edf": (400, [], dict(boost=(80, 160, 6.0), spike=("C3", 112, 124)))}
SIENA_NAME = {"T7": "T3", "T8": "T4", "P7": "T5", "P8": "T6"}


def check(name, ok, detail=""):
    RES.append((name, bool(ok)))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}", flush=True)


# ------------------------------------------------------------------------------------------------ world
def bip(path, rng, secs, seizures, boost=None, spike=None):
    n = secs * FS
    el = T.electrode_signals(rng, n, seizures)
    if boost:
        a, b, g = boost
        for e in el:
            el[e][a * FS:b * FS] *= g
    if spike:
        e, a, b = spike
        el[e][a * FS:b * FS] += 2500.0                                    # past +800 uV -> at the digital limit
    labels = T.CHB18[:13] + ["-"] + T.CHB18[13:16] + ["-", "FT9-FT10", "FT10-T8", "T8-P8"] + T.CHB18[16:]
    sig = []
    for l in labels:
        if l == "-":
            sig.append(np.zeros(n))
        elif l in ("FT9-FT10", "FT10-T8"):
            sig.append(30 * rng.standard_normal(n))
        else:
            a_, b_ = l.split("-")
            sig.append(el[a_] - el[b_])
    T.write_edf(path, labels, sig)


def siena_edf(path, rng, secs, seizures, boost=None, spike=None):
    import pyedflib
    fs = 512
    n = secs * fs
    names = T.ELEC
    t = np.arange(n) / fs
    sig, heads = [], []
    for k, e in enumerate(names):
        x = 40 * np.convolve(rng.standard_normal(n), np.ones(16) / 16, mode="same") + 15 * np.sin(2 * np.pi * (5 + 0.4 * k) * t)
        for on, off in seizures:
            x[on * fs:off * fs] += (70 + 8 * k) * np.sin(2 * np.pi * 3 * t[on * fs:off * fs] + 0.3 * k)
        if boost:
            a, b, g = boost
            x[a * fs:b * fs] *= g
        if spike and spike[0] == e:
            x[spike[1] * fs:spike[2] * fs] += 5000.0
        lab = "EEG " + (SIENA_NAME.get(e, e).capitalize() if e not in ("FZ", "CZ", "PZ") else e[0] + e[1].lower())
        lab = lab.replace("Fp1", "Fp1").replace("Fp2", "Fp2")
        heads.append({"label": lab, "dimension": "uV", "sample_frequency": fs, "physical_min": -1500.0,
                      "physical_max": 1500.0, "digital_min": -32768, "digital_max": 32767, "transducer": "", "prefilter": ""})
        sig.append(np.clip(x, -1500.0, 1500.0))
    heads.append({"label": "EKG EKG", "dimension": "uV", "sample_frequency": fs, "physical_min": -3000.0,
                  "physical_max": 3000.0, "digital_min": -32768, "digital_max": 32767, "transducer": "", "prefilter": ""})
    sig.append(300 * np.sin(2 * np.pi * 1.1 * t))
    pyedflib.highlevel.write_edf(str(path), sig, heads, digital=False)


def chb_summary(files):
    L = ["Data Sampling Rate: 256 Hz", "*" * 25, "", "Channels in EDF Files:", "*" * 22]
    L += [f"Channel {i + 1}: {c}" for i, c in enumerate(T.CHB18)] + [""]
    t = 10 * 3600
    for f, (secs, sz, kind, _) in files.items():
        if kind == "cs2":
            L += ["Channels changed:", "*" * 17] + [f"Channel {i + 1}: {e}-CS2" for i, e in enumerate(T.ELEC)] + [""]
        L += [f"File Name: {f}", f"File Start Time: {T.hms(t)}", f"File End Time: {T.hms(t + secs)}",
              f"Number of Seizures in File: {len(sz)}"]
        for k, (a, b) in enumerate(sz):
            L += [f"Seizure {k + 1} Start Time: {a} seconds", f"Seizure {k + 1} End Time:  {b} seconds"]
        L.append("")
        t += secs + 10
    return "\n".join(L) + "\n"


def siena_list():
    L = ["Seizures list of patient PN05", ""]
    t = 10 * 3600
    for f, (secs, sz, _) in SIENA.items():
        for a, b in sz:
            L += [f"File name: {f}", f"Registration start time: {T.hms(t).replace(':', '.')}",
                  f"Registration end time: {T.hms(t + secs).replace(':', '.')}",
                  f"Seizure start time: {T.hms(t + a).replace(':', '.')}",
                  f"Seizure end time: {T.hms(t + b).replace(':', '.')}", ""]
        t += secs + 600
    return "\n".join(L) + "\n"


REF = r'''
import json, os, sys, numpy as np
from pathlib import Path
repo, out = Path(sys.argv[1]), Path(sys.argv[2])
jobs, refmap = json.loads(sys.argv[3]), json.loads(sys.argv[4])
os.environ.update(THESIS_REPO=str(repo), R2_WORK=str(out / "_w"), R2_INPUT=str(out / "_i"), R2_SCRATCH=str(out / "_s"))
sys.path.insert(0, str(repo / "src")); sys.path.insert(0, str(repo / "src" / "dataprep"))
import r2_rb as RB
RB.REFERENTIAL.clear(); RB.REFERENTIAL.update(refmap); RB.install()
import r2_core as R0
for tag, case, view, feats in jobs:
    st = R0.stats_record(case, Path(view), out / f"{tag}_stats.log")
    (out / f"{tag}_stats.json").write_text(json.dumps(st))
    if feats:
        npz = R0.features_record(case, Path(view), st, out / f"build_{tag}", out / f"{tag}_feat.log")
        z = np.load(npz, allow_pickle=True)
        fl = z["is_flag5sd"].astype(bool)
        clean = ~z["is_ictal"].astype(bool) & ~z["is_buffer"].astype(bool) & ~z["is_signal_loss"].astype(bool) & ~fl
        files = [str(f) for f in z["files"]]
        fi = z["file_idx"].astype(int)
        added = np.isin(np.array(files)[fi], list(refmap))
        (out / f"{tag}_counts.json").write_text(json.dumps(dict(flag5sd=int(fl.sum()), clean=int(clean.sum()),
            flag_common=int((fl & ~added).sum()), flag_added=int((fl & added).sum()), files=files)))
print("references built", flush=True)
'''


def build_world(root):
    import pyedflib
    root = Path(root)
    if root.exists():
        shutil.rmtree(root)
    rng = np.random.default_rng(23)
    chb = root / "chbmit"
    repo = root / "repo"
    shutil.copytree(ROOT / "src", repo / "src", ignore=shutil.ignore_patterns("__pycache__"))
    (repo / "data" / "summaries").mkdir(parents=True)
    rows = []
    for case, files in WORLD.items():
        d = chb / case
        d.mkdir(parents=True)
        for f, (secs, sz, kind, ex) in files.items():
            if kind == "bip":
                bip(d / f, rng, secs, sz, **ex)
            else:
                T.referential_file(d / f, rng, secs, sz, kind, **ex)
        (repo / "data" / "summaries" / f"{case}-summary.txt").write_text(chb_summary(files))
        (d / f"{case}-summary.txt").write_text(chb_summary(files))
        for p in sorted(d.iterdir()):
            r = dict(db="chbmit", relpath=f"{case}/{p.name}", case=case, file=p.name, sha256_physionet=T.sha(p),
                     hours=WORLD[case].get(p.name, (0,))[0] / 3600 if p.suffix == ".edf" else None)
            rows.append(r)
    # earlier view of chb11 (first 2 files)
    ev = root / "view_earlier" / "chbmit" / "chb11"
    ev.mkdir(parents=True)
    for f in ("chb11_01.edf", "chb11_02.edf"):
        shutil.copyfile(chb / "chb11" / f, ev / f)
    sroot = root / "siena" / "PN05"
    sroot.mkdir(parents=True)
    for f, (secs, sz, ex) in SIENA.items():
        siena_edf(sroot / f, rng, secs, sz, **ex)
    (sroot / "Seizures-list-PN05.txt").write_text(siena_list())
    erows = [dict(db="siena", relpath=f"PN05/{p.name}", case="PN05", file=p.name, sha256_physionet=T.sha(p))
             for p in sorted(sroot.iterdir())]
    r0 = repo / "results" / "r2" / "r0_data"
    (r0 / "chb" / "stats_earlier").mkdir(parents=True)
    (r0 / "ext").mkdir(parents=True)
    pd.DataFrame(rows).to_csv(r0 / "chb" / "inventory.csv", index=False)
    pd.DataFrame(erows).to_csv(r0 / "ext" / "inventory.csv", index=False)
    win = 0
    for f in SIENA:
        with pyedflib.EdfReader(str(sroot / f)) as e:
            win += (int(e.getNSamples()[0]) // 2) // 1024
    pd.DataFrame([dict(case="chb24", windows=0), dict(case="PN05", windows=win)]).to_csv(r0 / "ext" / "external_cases.csv",
                                                                                         index=False)
    # references by the record code
    refmap = {f: T.sha(chb / "chb12" / f) for f in REFERENTIAL}
    jobs = [("chb01", "chb01", str(root), True), ("chb11", "chb11", str(root), True),
            ("chb11_earlier", "chb11", str(root / "view_earlier"), False), ("chb12", "chb12", str(root), True),
            ("chb24", "chb24", str(root), False)]
    work = root / "ref"
    work.mkdir()
    (root / "ref_build.py").write_text(REF)
    subprocess.check_call([sys.executable, str(root / "ref_build.py"), str(repo), str(work), json.dumps(jobs),
                           json.dumps(refmap)], cwd=str(root))
    S = {t: json.loads((work / f"{t}_stats.json").read_text()) for t, *_ in jobs}
    K = {t: json.loads((work / f"{t}_counts.json").read_text()) for t, *_x, f in jobs if f}
    for c in ("chb01", "chb24"):
        (r0 / "chb" / "stats_earlier" / f"{c}_stats.json").write_text(json.dumps(S[c]))
    (r0 / "chb" / "stats_earlier" / "chb12_stats.json").write_text(json.dumps(S["chb01"]))   # the pre-RB1 file: unused
    e, c = S["chb11_earlier"], S["chb11"]
    (r0 / "chb" / "stats_earlier" / "chb11_stats.json").write_text(json.dumps(e))
    sd0, mu0 = np.array(e["ch_std_uV"]), np.array(e["ch_mean_uV"])
    rel = {"ch_mean_uV (change / earlier SD)": dict(per_channel=((np.array(c["ch_mean_uV"]) - mu0) / sd0).tolist()),
           "ch_std_uV (relative change)": dict(per_channel=(np.array(c["ch_std_uV"]) / sd0 - 1).tolist()),
           "artifact_thresh_uV (relative change)": dict(
               per_channel=(np.array(c["artifact_thresh_uV"]) / np.array(e["artifact_thresh_uV"]) - 1).tolist())}
    (r0 / "chb" / "diff_chb11_chb21.json").write_text(json.dumps({"chb11": dict(stats_rel_change=rel)}))
    rb1 = r0 / "chb12_ref" / "rb1"
    (rb1 / "stats").mkdir(parents=True)
    (rb1 / "stats" / "chb12_stats.json").write_text(json.dumps(S["chb12"]))
    k = K["chb12"]
    (rb1 / "diff_chb12.json").write_text(json.dumps({"chb12": dict(flag5sd_in_common_files=[0, k["flag_common"]],
                                                                   flag5sd_in_added_files=k["flag_added"],
                                                                   clean_windows=[0, k["clean"]])}))
    det = {c_: dict(counts=dict(flag5sd=K[c_]["flag5sd"], clean=K[c_]["clean"])) for c_ in ("chb01", "chb11", "chb12")}
    det["chb24"] = dict(counts=dict(windows=1))
    (repo / "results" / "r2" / "r1_system" / "run").mkdir(parents=True)
    (repo / "results" / "r2" / "r1_system" / "run" / "data_gate.json").write_text(json.dumps(dict(detail=det)))
    return root, repo, chb, refmap, K


def run(root, tag, cases="chb01,chb11,chb12,chb24,PN05"):
    repo = root / "repo"
    env = dict(os.environ, R2_TEST="1", R2_TEST_RB_REFERENTIAL=json.dumps({f: T.sha(root / "chbmit" / "chb12" / f)
                                                                         for f in REFERENTIAL}))
    out = root / f"rb1c_{tag}"
    shutil.rmtree(out, ignore_errors=True)
    p = subprocess.run([sys.executable, str(repo / "src" / "r2_rb1c.py"), "--chbmit-dir", str(root / "chbmit"),
                        "--siena-dir", str(root / "siena"), "--out", str(out), "--procs", "2", "--cases", cases],
                       env=env, capture_output=True, text=True, cwd=str(root))
    print(p.stdout[-1200:], p.stderr[-1500:], flush=True)
    return p.returncode, p.stdout + p.stderr, out


# ------------------------------------------------------------------------------------------------ independent refs
def expected_chb(files):
    """compute_subject_stats' window selection, re-implemented on per-second arrays."""
    rows, counter = [], 0
    for fn in sorted(files):
        secs, sz = files[fn][0], files[fn][1]
        n = secs * FS // 1024
        lab, buf = np.zeros(n * 4, bool), np.zeros(n * 4, bool)
        for on, off in sz:
            lab[on:min(n * 4, off)] = True
            buf[off:min(n * 4, off + 4 * 3600)] = True
        for i in range(n):
            if lab[4 * i:4 * i + 4].any() or buf[4 * i:4 * i + 4].any():
                continue
            counter += 1
            if counter % 10 == 0:
                rows.append((fn, i))
    return rows


def expected_siena():
    rows, cnt = [], 0
    for f in sorted(SIENA):
        for i in range(SIENA[f][0] * 256 // 1024):
            cnt += 1
            if cnt % 10 == 0:
                rows.append((f, i))
    return rows


def clipped_windows(path, kind):
    """per-window clipped samples by pyedflib (digital): CHB bipolar first occurrence of the 18 derivations; referential
    the 19 electrodes; Siena the 19 electrodes at 512 Hz."""
    import pyedflib
    with pyedflib.EdfReader(str(path)) as f:
        labels = [l.strip().upper() for l in f.getSignalLabels()]
        if kind == "bip":
            idx = [labels.index(c) for c in T.CHB18]
            w = 1024
        else:
            tab = {}
            for i, l in enumerate(labels):
                e = l.replace("EEG", "").strip()
                e = e[:-4] if e.endswith("-CS2") else e
                e = {"01": "O1", "T3": "T7", "T4": "T8", "T5": "P7", "T6": "P8"}.get(e, e)
                tab.setdefault(e, i)
            idx = [tab[e] for e in T.ELEC]
            w = 1024 if kind == "ref" else 2048
        a = None
        for i in idx:
            x = f.readSignal(i, digital=True)
            c = (x <= f.getDigitalMinimum(i)) | (x >= f.getDigitalMaximum(i))
            a = c if a is None else (a | c)
    n = len(a) // w
    return a[:n * w].reshape(n, w).sum(axis=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/tmp/rb1c_synth")
    a = ap.parse_args()
    t0 = time.time()
    root, repo, chb, refmap, K = build_world(a.root)
    rc, txt, out = run(root, "ok")
    check("RB1c: exit 0", rc == 0, txt[-400:] if rc else "")
    R = json.loads((out / "rb1c.json").read_text())
    g = {c: {k: v["status"] for k, v in gg.items()} for c, gg in R["gates"].items()}
    want = {c: {"G-in": "PASS", "G-stats": "PASS", "G-flags": "PASS"} for c in ("chb01", "chb11", "chb12")}
    want["chb24"] = {"G-in": "PASS", "G-stats": "PASS", "G-flags": "NOT GATED"}
    want["PN05"] = {"G-in": "PASS", "G-stats": "PASS"}
    check("gates: PASS everywhere, chb24 flags NOT GATED, Siena statistics only", g == want, str(g))
    C = pd.read_csv(out / "cases.csv").set_index("case")
    Ch = pd.read_csv(out / "channels.csv")
    Fi = pd.read_csv(out / "files.csv")
    Tw = pd.read_csv(out / "top_windows.csv")
    G = pd.read_csv(out / "flag_grid.csv")
    # sampled windows and clipped windows = independent
    for case, files in WORLD.items():
        exp = expected_chb(files)
        clip = {f: clipped_windows(chb / case / f, "bip" if files[f][2] == "bip" else "ref") for f in files}
        n_cl = sum(int(clip[f][i] > 0) for f, i in exp)
        check(f"{case}: sampled windows = independent rule; windows with clipped samples = pyedflib",
              int(C.loc[case, "sampled_windows"]) == len(exp) and int(C.loc[case, "sampled_with_clipped"]) == n_cl,
              f"({C.loc[case, 'sampled_windows']} vs {len(exp)}; clipped {C.loc[case, 'sampled_with_clipped']} vs {n_cl})")
    exp = expected_siena()
    clip = {f: clipped_windows(root / "siena" / "PN05" / f, "siena") for f in SIENA}
    n_cl = sum(int(clip[f][i] > 0) for f, i in exp)
    check("PN05: sampled windows = independent rule; windows with clipped samples = pyedflib",
          int(C.loc["PN05", "sampled_windows"]) == len(exp) and int(C.loc["PN05", "sampled_with_clipped"]) == n_cl,
          f"({C.loc['PN05', 'sampled_windows']} vs {len(exp)}; clipped {C.loc['PN05', 'sampled_with_clipped']} vs {n_cl})")
    # planted stretches found
    sz_sampled = {"chb01": 0, "PN05": sum(1 for f, i in expected_siena()
                                          if any(4 * i < b and 4 * i + 4 > a for a, b in SIENA[f][1]))}
    for case, f, (a_, b_) in (("chb01", "chb01_02.edf", (40, 120)), ("PN05", "PN05-4.edf", (80, 160))):
        rows = expected_chb(WORLD["chb01"]) if case == "chb01" else expected_siena()
        inside = {(ff, i) for ff, i in rows if ff == f and 4 * i >= a_ and 4 * i + 4 <= b_}
        top = Tw[Tw.case == case].head(len(inside) + sz_sampled[case])
        check(f"{case}: planted stretch found (no-clip SD lower, largest file, its sampled windows among the top)",
              C.loc[case, "noclip_vs_record_median"] < -0.05 and C.loc[case, "top_file"] == f and len(inside) > 0
              and inside <= set(zip(top.file, top.window)),
              f"(no-clip {C.loc[case, 'noclip_vs_record_median']:+.3f}, top file {C.loc[case, 'top_file']}, "
              f"{len(inside)} sampled windows inside, + {sz_sampled[case]} seizure windows (Siena: label-free))")
    check("chb12: the boosted chb12_27 is the largest file", C.loc["chb12", "top_file"] == "chb12_27.edf")
    # flag grid
    ok_g, det = True, []
    for case in ("chb01", "chb11", "chb12", "chb24"):
        n_rec = int(C.loc[case, "flagged_record"])
        gg = G[G.case == case]
        r5 = int(gg[(gg.scale == "record") & (gg.multiplier == 5)].flagged.iloc[0])
        mono = all((np.diff(gg[gg.scale == s].sort_values("multiplier").flagged.to_numpy()) <= 0).all() for s in gg.scale.unique())
        br = all((int(gg[(gg.scale == s) & (gg.multiplier == m)].flagged.iloc[0]) >= n_rec) == (m < C.loc[case, f"multiplier_same_count_{s}"])
                 for s in ("noclip", "mad", "iqr") for m in gg.multiplier.unique()
                 if not np.isclose(m, C.loc[case, f"multiplier_same_count_{s}"]))
        ok_g &= (r5 == n_rec) and mono and br
        det.append(f"{case}: x5 {r5}/{n_rec} mono {mono} bracket {br}")
    check("flag grid: record x5 = gate count; monotone in the multiplier; same-count multiplier brackets the record count",
          ok_g, "; ".join(det))
    check("record flag and clean counts = the record code's (chb01, chb11, chb12)",
          all(int(C.loc[c, "flagged_record"]) == K[c]["flag5sd"] and int(C.loc[c, "clean_record"]) == K[c]["clean"]
              for c in ("chb01", "chb11", "chb12")))
    check("channels: 18 rows per case; files: shares of deviation and of windows sum to 1 per case",
          (Ch.groupby("case").size() == 18).all()
          and (Fi.groupby("case").share_of_deviation.sum().sub(1).abs() < 1e-9).all()
          and (Fi.groupby("case").share_of_windows.sum().sub(1).abs() < 1e-9).all())
    code = ("import sys,numpy as np; sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[1]+'/dataprep');"
            "import r2_rb1c as M; x=np.random.default_rng(0).normal(0,3e-5,(300,18,1024));"
            "S=x.sum(axis=2); SS=(x*x).sum(axis=2); sc,_=M.scales_from(S,SS,x.astype(np.float32),np.zeros(300,int));"
            "print(max(float(np.abs(sc[k]/30-1).max()) for k in ('record','noclip','mad','iqr')))")
    v = float(subprocess.check_output([sys.executable, "-c", code, str(repo / "src")], text=True).split()[-1])
    check("scales of normal data = sigma (SD, no-clip SD, MAD x 1.4826, IQR / 1.349)", v < 0.01, f"(max rel {v:.4f})")
    check("summary written", (out / "SUMMARY.md").exists() and "chb24" in (out / "SUMMARY.md").read_text())

    # ------------------------------------------------------------ failure paths
    r0 = repo / "results" / "r2" / "r0_data"

    def neg(tag, gate, path, mutate, cases):
        keep = path.read_bytes()
        mutate(path)
        rc_, txt_, _ = run(root, tag, cases)
        path.write_bytes(keep)
        last = [l for l in txt_.strip().splitlines() if "STOP RB1c" in l]
        check(f"STOP at {gate} ({tag})", rc_ != 0 and any(f"STOP RB1c: {gate}" in l for l in last),
              (last or txt_.strip().splitlines())[-1][:140])

    def flip(p):
        b_ = bytearray(p.read_bytes())
        b_[-9] ^= 0xFF
        p.write_bytes(bytes(b_))

    def js(f):
        def m(p):
            d = json.loads(p.read_text())
            f(d)
            p.write_text(json.dumps(d))
        return m
    neg("in_chb", "G-in", chb / "chb01" / "chb01_02.edf", flip, "chb01")
    extra = chb / "chb24" / "chb24_99.edf"
    shutil.copyfile(chb / "chb24" / "chb24_01.edf", extra)
    neg("in_extra", "G-in", extra, lambda p: None, "chb24")
    extra.unlink()
    neg("in_siena", "G-in", root / "siena" / "PN05" / "PN05-2.edf", flip, "PN05")
    neg("st_chb01", "G-stats", r0 / "chb" / "stats_earlier" / "chb01_stats.json",
        js(lambda d: d["ch_std_uV"].__setitem__(3, d["ch_std_uV"][3] * (1 + 1e-5))), "chb01")
    neg("st_chb11", "G-stats", r0 / "chb" / "diff_chb11_chb21.json",
        js(lambda d: d["chb11"]["stats_rel_change"]["ch_std_uV (relative change)"]["per_channel"].__setitem__(0, 0.5)), "chb11")
    neg("st_chb12", "G-stats", r0 / "chb12_ref" / "rb1" / "stats" / "chb12_stats.json",
        js(lambda d: d["ch_mean_uV"].__setitem__(7, d["ch_mean_uV"][7] + 1e-3 * d["ch_std_uV"][7])), "chb12")
    neg("st_siena", "G-stats", r0 / "ext" / "external_cases.csv",
        lambda p: p.write_text(p.read_text().replace(f"PN05,{int(pd.read_csv(p).set_index('case').loc['PN05','windows'])}",
                                                     "PN05,1")), "PN05")
    neg("fl_chb01", "G-flags", repo / "results" / "r2" / "r1_system" / "run" / "data_gate.json",
        js(lambda d: d["detail"]["chb01"]["counts"].__setitem__("flag5sd", d["detail"]["chb01"]["counts"]["flag5sd"] + 1)), "chb01")
    neg("fl_chb12", "G-flags", r0 / "chb12_ref" / "rb1" / "diff_chb12.json",
        js(lambda d: d["chb12"]["clean_windows"].__setitem__(1, d["chb12"]["clean_windows"][1] - 1)), "chb12")

    n_ok = sum(r[1] for r in RES)
    print(f"\n{n_ok}/{len(RES)} checks PASS in {time.time() - t0:.0f} s")
    print("ALL PASS" if n_ok == len(RES) else "FAILURES: " + "; ".join(r[0] for r in RES if not r[1]))
    sys.exit(0 if n_ok == len(RES) else 1)


if __name__ == "__main__":
    main()
