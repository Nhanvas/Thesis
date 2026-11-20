#!/usr/bin/env python
"""fa15_synthetic_test.py -- end-to-end test of src/fa15_asr.py and notebooks/fa15/FA15_SMOKE.ipynb on SYNTHETIC EDF
files (build container only; never on real data). Instructions §1 item 15: every gate, both conventions (CHB-MIT thesis,
x1 external for chb24 and Siena), the failure paths.

World = the RB1c synthetic world (src/r2_rb1c_synthetic_test.build_world: chb01 with a planted x6 stretch, chb11, chb12
with two referential files that the record skips by design, chb24, Siena PN05 at 512 Hz with a planted stretch), laid
out as the Kaggle raw dataset (one EDF absent, one changed byte) and as a fake PhysioNet (file:// SHA256SUMS), as in
src/r2_rb1c_notebook_test.py. In a SEPARATE process, with the record code only:
  - the R0 reference datasets (r2_core.stats_record / features_record; r2_core.ext_job) for chb01, chb11, chb12, chb24,
    PN05 -> input/thesis-r2-chbmit-features, input/thesis-r2-external-features (+ R0 run_meta with these versions);
  - the "V9-X6 record" for chb01_01 and chb24_01 by V9-X6's own path (v9_x6_asr.whole_file_filtered + run_asr + its
    Measure 1 functions; thresholds = the references' 5-SD thresholds) -> repo/results/v9_x6/*.csv.
G-conv: on this world the record's 3-s padded per-window filtering differs from whole-file filtering by ~0.75 % of
window RMS, which moves the statistics by up to 2.5e-3 SD -- reported, below the STOP bound 1e-2 (author 21/11 01:28).
Rev 21/11 (chat D35-F): the V9-X6 record of chb01_01 is built with 300-s chunks (asrpy mem_splits 3 on this 5-min file),
as V9-X6's early files were, so the run's 60-s chunks differ beyond 1e-3 there and G-asr must explain it by the 300-s
recomputation; chb24_01 is built with 60-s chunks (exact). Pre-gates G-conv-pad (chb11, PN05) and G-asr-pre (chb01_01,
300 s) run in the smoke and in a data notebook built by fa15_make_notebooks.build_data. Notebooks are written to the
test root, never into the repository.
Checks: FA15_SMOKE runs to the end; every gate PASS (mode exact, R0.1 with two files from PhysioNet, G-ref, G-conv, G-lab,
G-asr, G-done, G-ident); the chb12 referential files are skipped by design; the datasets hold every case, their labels =
the references and their features differ from them (ASR acted); the chb01 statistics changed (planted stretch cleaned);
the ASR-only file was measured and its cache removed; projection.json and split.json written; the Measure 1 tables
hold the V9-X6 columns; G-asr classes (chb01_01 explained by 300-s chunks, chb24_01 exact); G-conv-pad (30 s <= 1e-9,
3 s visibly larger); G-worker-sha. Failure paths (each STOPs at the end of the notebook with the results archived): a
V9-X6 record value of chb24_01 + 0.01 -> G-asr FAIL (unexplained by any chunking); an R0 reference SD x 1.05 -> G-conv
FAIL (above 1e-2); one R0 buffer flag flipped -> G-lab and G-ident FAIL; an ASR subprocess failing on one file -> G-done
FAIL; slices shifted by one sample -> G-conv-pad FAIL and the run skipped; a chb01_01 record value + 1e-6 -> G-asr-pre
FAIL and the run skipped; a worker reporting another code sha -> G-worker-sha FAIL.
Not covered: the real files' size, Kaggle's speed, memory and disk (the smoke measures them); the memory / disk guards
(they only wait).
  python src/fa15_synthetic_test.py [--root DIR]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import r2_rb1c_synthetic_test as Wd  # noqa: E402
import r2_rb1c_notebook_test as NBT  # noqa: E402
import fa15_make_notebooks as MK  # noqa: E402

RES = []
CASES = [["chb01", "chb11"], ["chb24", "PN05"], ["chb12:chb12_06.edf"], ["chb11", "PN05"],
         [["chb01", "chb01_01.edf", 300.0]]]

REFB = r'''
import json, os, sys, numpy as np, pandas as pd, platform
from pathlib import Path
repo, root = Path(sys.argv[1]), Path(sys.argv[2])
os.environ.update(THESIS_REPO=str(repo), R2_WORK=str(root / "_rw"), R2_INPUT=str(root / "_ri"), R2_SCRATCH=str(root / "_rs"))
sys.path.insert(0, str(repo / "src")); sys.path.insert(0, str(repo / "src" / "dataprep"))
import r2_core as R0, preprocessing as P, v9_x6_asr as V6, scipy, mne
R0.STATE["tag"] = "ref"
import shutil
view = root / "view_fa15"                      # hard links, not symlinks: x1's rglob does not follow symlinked folders
for db in ("chbmit", "siena"):
    if not (view / db).exists():
        shutil.copytree(root / db, view / db, copy_function=os.link)
dc = root / "input" / "thesis-r2-chbmit-features" / "thesis-r2-chbmit-features"
de = root / "input" / "thesis-r2-external-features" / "thesis-r2-external-features"
dc.mkdir(parents=True, exist_ok=True); de.mkdir(parents=True, exist_ok=True)
for case in ("chb01", "chb11", "chb12"):
    st = R0.stats_record(case, view, root / f"ref_{case}.log")
    (dc / f"{case}_stats.json").write_text(json.dumps(st))
    p = R0.features_record(case, view, st, root / "_refbuild", root / f"ref_{case}.log")
    p.replace(dc / f"{case}.npz")
for case in ("chb24", "PN05"):
    z, meta = R0.ext_job(case, view, 1, root / f"ref_{case}.log")
    np.savez(de / f"{case}_lf.npz", **z, meta=json.dumps(meta))
v = dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__, pandas=pd.__version__, mne=mne.__version__)
for sub in ("chb", "ext"):
    d = repo / "results" / "r2" / "r0_data" / sub
    d.mkdir(parents=True, exist_ok=True)
    (d / "run_meta.json").write_text(json.dumps(dict(versions=v)))
# V9-X6 record on two files by V9-X6's own code path
sz, hi, bg = [], [], []
for case, f, thr in (("chb01", "chb01_01.edf", np.asarray(json.loads((dc / "chb01_stats.json").read_text())["artifact_thresh_uV"]) * 1e-6),
                     ("chb24", "chb24_01.edf", 5.0 * np.asarray(json.loads(str(np.load(de / "chb24_lf.npz", allow_pickle=True)["meta"]))["labelfree_std_uV"]) * 1e-6)):
    path = root / "chbmit" / case / f
    X, n_total = V6.whole_file_filtered(path)
    V6.MEM_SPLIT_CHUNK_S = 300.0 if f == "chb01_01.edf" else 60.0      # chb01_01: an early V9-X6 chunking
    Xc = V6.run_asr(X, 20)
    smap = P.parse_summary(root / "chbmit" / case / f"{case}-summary.txt")
    seizures = smap[f]
    n_windows = n_total // 1024
    share_w, Wr = V6.window_shares(X, Xc, n_windows)
    hiamp, back = V6.window_flags(Wr, thr, n_windows, seizures, n_total)
    for i, (on, off) in enumerate(seizures):
        a, b = V6.median_channel_rms(X, on * 256, off * 256), V6.median_channel_rms(X, (on - 60) * 256, on * 256)
        c, d = V6.median_channel_rms(Xc, on * 256, off * 256), V6.median_channel_rms(Xc, (on - 60) * 256, on * 256)
        sz.append(dict(subject=case, file=f, cutoff=20, seizure_idx=i, onset_s=on, offset_s=off, duration_s=off - on,
                       share_seizure=V6.span_power_ratio(X, Xc, on * 256, off * 256, n_total),
                       share_preictal60=V6.span_power_ratio(X, Xc, (on - 60) * 256, on * 256, n_total),
                       contrast_before=a / b, contrast_after=c / d, n_ictal=None, ictal_channels=None, focal_generalized=None))
    for w in np.flatnonzero(hiamp):
        hi.append(dict(subject=case, file=f, cutoff=20, win_idx=int(w), share=float(share_w[w]), contrast_before=None, contrast_after=None))
    for s in share_w[back]:
        bg.append(dict(subject=case, file=f, cutoff=20, share=float(s)))
d = repo / "results" / "v9_x6"
d.mkdir(parents=True, exist_ok=True)
pd.DataFrame(sz).to_csv(d / "seizures.csv", index=False)
pd.DataFrame(hi).to_csv(d / "highamp_windows.csv", index=False)
pd.DataFrame(bg).to_csv(d / "background_windows.csv", index=False)
print("references built", len(sz), len(hi), len(bg), flush=True)
'''


def check(name, ok, detail=""):
    RES.append((name, bool(ok)))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}", flush=True)


def env(root, tag, extra=None):
    e = NBT.nb_env(root, tag)
    e = {k: v for k, v in e.items() if not k.startswith("R2_TEST_RB")}
    e.update(FA15_TEST="1", FA15_TEST_REPO=str(root / "repo"), FA15_TEST_INPUT=str(root / "input"),
             FA15_TEST_WORK=str(root / f"work_{tag}"), FA15_TEST_SCRATCH=str(root / f"scratch_{tag}"),
             FA15_TEST_CASES=json.dumps(CASES), FA15_DISK_MARGIN_GB="0.1", FA15_MIN_FREE_MEM_GB="0.5",
             FA15_TEST_HOURS=json.dumps({"chb01": 30.0, "chb04": 156.0, "chb24": 21.0, "PN00": 3.2, "PN05": 2.0}),
             FA15_TEST_FAIL_FILE="")
    e.update(extra or {})
    return e


RUNNER = r'''
if __name__ == "__main__":   # spawn workers re-import this file as __mp_main__: they must not re-run the notebook
    import json, os, re, sys, time, traceback
    from pathlib import Path
    nb_path, out = sys.argv[1], sys.argv[2]
    nb = json.loads(Path(nb_path).read_text())
    ns, err, t = {"__name__": "__main__"}, None, time.time()
    try:
        for i, c in enumerate(nb["cells"]):
            if c["cell_type"] != "code":
                continue
            try:
                exec(compile("".join(c["source"]), f"{Path(nb_path).name}[cell {i}]", "exec"), ns)
            except RuntimeError as e:
                err = str(e)
                break
    except BaseException as e:
        traceback.print_exc()
        err = f"CRASH {type(e).__name__}: {e}"
    print(f"--- {Path(nb_path).name} {'STOPPED' if err else 'done'} in {time.time() - t:.0f} s", flush=True)
    Path(out).write_text(json.dumps(dict(err=err)))
'''


def run_nb(nbp, e):
    """the notebook's cells in a FRESH process (as a Kaggle kernel: no test module on sys.path or in __main__)."""
    d = Path(e["FA15_TEST_WORK"]).parent / "_runner"
    d.mkdir(exist_ok=True)
    (d / "run.py").write_text(RUNNER)
    out = d / f"{Path(e['FA15_TEST_WORK']).name}.json"
    full = {k: v for k, v in os.environ.items() if not k.startswith(("FA15_", "R2_"))}
    full.update(e)
    subprocess.run([sys.executable, "-I", str(d / "run.py"), str(nbp), str(out)], env=full, cwd=str(d))
    err = json.loads(out.read_text())["err"] if out.exists() else "CRASH: runner wrote nothing"
    return {}, err


def gates(work, tag="smoke"):
    p = work / "fa15" / tag / "gates.json"
    return {g["gate"]: g for g in json.loads(p.read_text())} if p.exists() else {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/tmp/fa15_test")
    a = ap.parse_args()
    t0 = time.time()
    root, repo, chb, refmap, K = Wd.build_world(a.root)
    NBT.layout(root)
    (root / "refb.py").write_text(REFB)
    subprocess.check_call([sys.executable, str(root / "refb.py"), str(repo), str(root)], cwd=str(root))
    shutil.copytree(ROOT / "results" / "x1_external", repo / "results" / "x1_external", dirs_exist_ok=True)
    MK.OUTDIR = root / "nb"                       # never into the repository
    MK.build("FA15_SMOKE", "WORKTREE", "smoke", MK.SMOKE["chb"], MK.SMOKE["ext"], MK.SMOKE["asr_only"], True, "test")
    nbp = MK.OUTDIR / "FA15_SMOKE.ipynb"

    # ---- positive run
    ns, err = run_nb(nbp, env(root, "ok"))
    work = root / "work_ok"
    G = gates(work)
    check("FA15_SMOKE: every cell ran, no STOP", err is None, str(err)[:400])
    want = ["G-mod", "mode", "R0.1-inventory", "G-ref", "G-conv-pad", "G-asr-pre", "G-conv", "G-lab", "G-asr", "G-done",
            "G-worker-sha", "G-ident"]
    check("every gate PASS (incl. mode exact and G-ident)", all(G.get(g, {}).get("status") == "PASS" for g in want)
          and G["mode"].get("mode") == "exact", str({g: G.get(g, {}).get("status") for g in want}))
    inv = pd.read_csv(work / "fa15" / "smoke" / "inventory.csv")
    src = dict(zip(inv.file, inv.source))
    check("inventory: chb01_01 (absent) and chb11_02 (changed) from PhysioNet",
          src.get("chb01_01.edf", "").startswith("physionet") and src.get("chb11_02.edf", "").startswith("physionet"))
    dc, de = work / "fa15-asr-chbmit-features-smoke", work / "fa15-asr-external-features-smoke"
    have = sorted(p.name for p in dc.iterdir()) + sorted(p.name for p in de.iterdir())
    check("datasets hold every case (chb01, chb11 npz + stats; chb24, PN05 lf.npz)",
          set(have) == {"chb01.npz", "chb01_stats.json", "chb11.npz", "chb11_stats.json", "chb24_lf.npz", "PN05_lf.npz"},
          str(have))
    rc = root / "input" / "thesis-r2-chbmit-features" / "thesis-r2-chbmit-features"
    re_ = root / "input" / "thesis-r2-external-features" / "thesis-r2-external-features"
    diff = {}
    for c in ("chb01", "chb11"):
        n, r = np.load(dc / f"{c}.npz", allow_pickle=True), np.load(rc / f"{c}.npz", allow_pickle=True)
        diff[c] = bool(not np.array_equal(n["f7"], r["f7"], equal_nan=True)) and list(n["files"]) == list(r["files"])
    for c in ("chb24", "PN05"):
        n, r = np.load(de / f"{c}_lf.npz", allow_pickle=True), np.load(re_ / f"{c}_lf.npz", allow_pickle=True)
        diff[c] = bool(not np.array_equal(n["bp5"], r["bp5"], equal_nan=True))
    check("ASR acted: features differ from the references in every case (labels equal: G-lab)", all(diff.values()), str(diff))
    s_new = json.loads((dc / "chb01_stats.json").read_text())
    s_ref = json.loads((rc / "chb01_stats.json").read_text())
    sd_ratio = np.asarray(s_new["ch_std_uV"]) / np.asarray(s_ref["ch_std_uV"])
    check("chb01: the planted x6 stretch is cleaned -> the statistics' SD falls", float(np.median(sd_ratio)) < 0.95,
          f"median SD ratio {np.median(sd_ratio):.3f}")
    fr = pd.read_csv(work / "fa15" / "smoke" / "files.csv")
    check("chb12's referential files are skipped by design (only chb12_06 as ASR-only)",
          not fr.file.str.contains("chb12_2").any() and (fr.file == "chb12_06.edf").sum() == 1 and
          bool(fr[fr.file == "chb12_06.edf"].asr_only.iloc[0]), str(fr.file.tolist()))
    check("caches removed after their cases", not any((root / "scratch_ok" / "asr_cache").glob("*.npy")))
    sz = pd.read_csv(work / "fa15" / "smoke" / "seizures.csv")
    check("Measure 1 tables in the V9-X6 format (every seizure of every processed file)",
          {"subject", "file", "cutoff", "seizure_idx", "share_seizure", "contrast_before", "contrast_after"} <= set(sz.columns)
          and sorted(zip(sz.subject, sz.file)) == sorted([("PN05", "PN05-2.edf"), ("chb01", "chb01_01.edf"),
                                                          ("chb11", "chb11_01.edf"), ("chb12", "chb12_06.edf"),
                                                          ("chb24", "chb24_01.edf")]), f"{len(sz)} seizure rows")
    check("asrpy block_covariance guard acted on chb12_06 only (its calibration length = 2 mod 100) and the file completed",
          dict(zip(fr.file, fr.bc_trim)) == {f: int(f == "chb12_06.edf") for f in fr.file}, str(dict(zip(fr.file, fr.bc_trim))))
    ga = json.loads((work / "fa15" / "smoke" / "g_asr.json").read_text())
    cls = {d["file"]: (d["cls"], (d.get("explained_by") or {}).get("mem_splits")) for d in ga["detail"]}
    check("G-asr: chb01_01 beyond 1e-3 at 60-s chunks and explained by the 300-s recomputation; chb24_01 exact",
          ga["files"] == 2 and cls == {"chb01_01.edf": ("explained", 3), "chb24_01.edf": ("exact", None)}
          and ga["max_abs"]["share_preictal60"] > 1e-3, f"{cls} {ga['max_abs']}")
    gp = G["G-conv-pad"]["cases"]
    check("G-conv-pad: 30-s padding = slices (<= 1e-9) in both conventions; 3-s padding visibly different (> 1e-5)",
          len(gp) == 2 and all(d["rel_pad30_vs_slice"] <= 1e-9 and d["rel_pad3_vs_slice"] > 1e-5 for d in gp),
          str([(d["case"], d["rel_pad30_vs_slice"], d["rel_pad3_vs_slice"]) for d in gp]))
    gpre = G["G-asr-pre"]["files"]
    check("G-asr-pre: chb01_01 with 300-s chunks (mem_splits 3) = the record within 1e-9",
          len(gpre) == 1 and gpre[0]["mem_splits"] == 3 and max(gpre[0]["max_abs"].values()) <= 1e-9, str(gpre))
    check("G-worker-sha: every ASR subprocess and feature job reported this fa15_asr.py",
          G["G-worker-sha"]["jobs"] == len(fr) + 4 and not G["G-worker-sha"]["differ"], G["G-worker-sha"]["summary"])
    check("no diagnostic marker or cache left in the scratch cache", not any((root / "scratch_ok" / "asr_cache").glob("*.npy")))
    pj = work / "fa15" / "smoke"
    split = json.loads((pj / "split.json").read_text()) if (pj / "split.json").exists() else {}
    check("projection.json and split.json written; every test case in one part",
          (pj / "projection.json").exists() and sorted(c for d in split.values() for c in d["cases"]) ==
          sorted(json.loads(env(root, "x")["FA15_TEST_HOURS"])), str(split))
    zp = work / "fa15_smoke_results.zip"
    check("results archive written", zp.exists() and "smoke/SUMMARY.md" in zipfile.ZipFile(zp).namelist())

    # ---- failure paths
    def neg(tag, mutate, restore, want_fail, extra=None):
        mutate()
        try:
            ns, err = run_nb(nbp, env(root, tag, extra=extra))
        finally:
            restore()
        G = gates(root / f"work_{tag}")
        bad = {g: G.get(g, {}).get("status") for g in want_fail}
        check(f"STOP path {tag}: {want_fail} FAIL, notebook STOPPED after archiving",
              err is not None and "STOPPED" in err and all(v == "FAIL" for v in bad.values())
              and (root / f"work_{tag}" / "fa15_smoke_results.zip").exists(), f"{bad} | {str(err)[:150]}")

    rec = repo / "results" / "v9_x6" / "seizures.csv"
    keep = rec.read_bytes()

    def m1():
        d = pd.read_csv(rec)
        d.loc[d.file == "chb24_01.edf", "share_seizure"] += 0.01
        d.to_csv(rec, index=False)
    neg("asrrec", m1, lambda: rec.write_bytes(keep), ["G-asr"])

    sp = rc / "chb11_stats.json"
    keep2 = sp.read_bytes()

    def m2():
        s = json.loads(keep2)
        s["ch_std_uV"] = [x * 1.05 for x in s["ch_std_uV"]]
        sp.write_text(json.dumps(s))
    neg("conv", m2, lambda: sp.write_bytes(keep2), ["G-conv"])

    zp_ = rc / "chb01.npz"
    keep3 = zp_.read_bytes()

    def m3():
        z = dict(np.load(zp_, allow_pickle=True))
        z["is_buffer"] = z["is_buffer"].copy()
        z["is_buffer"][0] = ~z["is_buffer"][0]
        np.savez(zp_, **z)
        if not str(zp_).endswith(".npz"):
            pass
    neg("lab", m3, lambda: zp_.write_bytes(keep3), ["G-lab", "G-ident"])
    neg("asrfail", lambda: None, lambda: None, ["G-done"], dict(FA15_TEST_FAIL_FILE="chb11_02.edf"))
    neg("pad", lambda: None, lambda: None, ["G-conv-pad", "G-done"], dict(FA15_TEST_SLICE_SHIFT="1"))
    check("pad: the run was skipped after the pre-gate (no case written)",
          not (root / "work_pad" / "fa15-asr-chbmit-features-smoke").exists()
          and gates(root / "work_pad").get("G-done", {}).get("summary", "").startswith("skipped"))

    def m4():
        d = pd.read_csv(rec)
        d.loc[d.file == "chb01_01.edf", "share_preictal60"] += 1e-6
        d.to_csv(rec, index=False)
    neg("asrpre", m4, lambda: rec.write_bytes(keep), ["G-asr-pre", "G-done"])
    neg("sha", lambda: None, lambda: None, ["G-worker-sha"],
        dict(FA15_TEST_WORKER_SHA="deadbeefdeadbeef", FA15_TEST_CASES=json.dumps(CASES[:3])))

    # ---- a data notebook built by the builder's data path (not smoke: no G-ident, no projection)
    MK.build_data("WORKTREE")
    nbd = MK.OUTDIR / "FA15_DATA_B.ipynb"
    src = "".join(json.loads(nbd.read_text())["cells"][2]["source"])
    check("builder: FA15_DATA_B carries G-conv-pad [chb08, PN16] and G-asr-pre chb06_01 at 300 s; FA15_DATA_A PN00",
          '["chb08", "PN16"]' in src and '"chb06_01.edf", 300.0' in src and
          '"PN00"]' in "".join(json.loads((MK.OUTDIR / "FA15_DATA_A.ipynb").read_text())["cells"][2]["source"]))
    ns, err = run_nb(nbd, env(root, "data", extra=dict(FA15_TEST_CASES=json.dumps(CASES))))
    Gd = gates(root / "work_data", "b")
    check("data notebook (tag b) runs to the end; every gate PASS; no G-ident / projection (not smoke)",
          err is None and all(Gd.get(g, {}).get("status") == "PASS" for g in want if g != "G-ident")
          and "G-ident" not in Gd and not (root / "work_data" / "fa15" / "b" / "split.json").exists(),
          f"{err} {[(g, Gd.get(g, {}).get('status')) for g in want]}")

    n_ok = sum(r[1] for r in RES)
    print(f"\n{n_ok}/{len(RES)} checks PASS in {time.time() - t0:.0f} s")
    print("ALL PASS" if n_ok == len(RES) else "FAILURES: " + "; ".join(r[0] for r in RES if not r[1]))
    sys.exit(0 if n_ok == len(RES) else 1)


if __name__ == "__main__":
    main()
