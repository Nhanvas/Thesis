#!/usr/bin/env python
"""r2_rb1b_synthetic_test.py -- end-to-end test of src/r2_rb1b.py on SYNTHETIC EDF files (build container only).

World = the RB1 test world (src/r2_rb1_synthetic_test.py) with one planted cause: chb12_27 is 5x larger on every
electrode before its first seizure (0-120 s). The RB1 notebook runs on it first (its outputs become the "committed"
RB1 results of the fake repository), then r2_rb1b.py runs as the laptop would. Checks: every gate PASS; the planted
cause is found (removing chb12_27 before its first seizure brings B's SD back near A's; its share of the squared
deviation is far above its share of windows); the sampled-window list = an independent re-implementation of the
sampling rule; per-window shares sum to 1; robust scales of normal data = sigma; flag rows consistent; failure paths
STOP at their gate (raw byte, RB1 SD, RB1 flag count, RB0b file count, RB0b channel count).
  python src/r2_rb1b_synthetic_test.py [--root DIR]
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


def check(name, ok, detail=""):
    RES.append((name, bool(ok)))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}", flush=True)


def run_rb1b(root, tag):
    repo = root / "repo"
    env = dict(os.environ, R2_TEST="1",
               R2_TEST_RB_REFERENTIAL=json.dumps({f: T.sha(root / "input" / T.RAWNAME / "chbmit" / "chb12" / f)
                                                  for f in T.NEW}))
    out = root / f"rb1b_{tag}"
    shutil.rmtree(out, ignore_errors=True)
    p = subprocess.run([sys.executable, str(repo / "src" / "r2_rb1b.py"), "--chbmit-dir",
                        str(root / "input" / T.RAWNAME / "chbmit"), "--out", str(out)],
                       env=env, capture_output=True, text=True, cwd=str(root))
    print(p.stdout[-1500:], p.stderr[-1500:], flush=True)
    return p.returncode, p.stdout + p.stderr, out


def expected_sampled(files, summary_seizures, n_windows):
    """independent re-implementation of compute_subject_stats' window selection (per-second arrays)."""
    rows, counter = [], 0
    for fn in sorted(files):
        n = n_windows[fn]
        secs = n * 4
        lab = np.zeros(secs, bool)
        buf = np.zeros(secs, bool)
        for on, off in summary_seizures.get(fn, []):
            lab[max(0, on):min(secs, off)] = True
            buf[off:min(secs, off + 4 * 3600)] = True
        for i in range(n):
            if lab[4 * i:4 * i + 4].any() or buf[4 * i:4 * i + 4].any():
                continue
            counter += 1
            if counter % 10 == 0:
                rows.append((fn, i))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/tmp/rb1b_synth")
    a = ap.parse_args()
    t0 = time.time()
    files = dict(T.FILES)
    secs, sz, kind, ex = files["chb12_27.edf"]
    files["chb12_27.edf"] = (secs, sz, kind, dict(ex, boost=(0, 120, 5.0)))
    T.FILES = files
    root, raw, ds, repo = T.build_world(a.root)
    subprocess.check_call([sys.executable, str(ROOT / "src" / "r2_rb1_make_notebook.py")])
    ns, err = T.run_notebook(ROOT / "notebooks" / "r2" / "RB1_DATA.ipynb", T.env(root, "ok"))
    check("RB1 notebook on the world: no STOP", err is None, err or "")
    rb1 = repo / "results" / "r2" / "r0_data" / "chb12_ref" / "rb1"
    shutil.copytree(root / "work_ok" / "r2" / "r0_data" / "chb12_ref" / "rb1", rb1)

    # ------------------------------------------------------------ positive run
    rc, txt, out = run_rb1b(root, "ok")
    check("RB1b: exit 0", rc == 0, txt[-300:] if rc else "")
    R = json.loads((out / "rb1b.json").read_text())
    check("every gate PASS (G-in, G-stats, G-flags, G-clip)",
          {k: v["status"] for k, v in R["gates"].items()} == {"G-in": "PASS", "G-stats": "PASS", "G-clip": "PASS",
                                                              "G-flags": "PASS"}, str(R["gates"])[:300])
    Sc = pd.read_csv(out / "scenarios.csv")
    sd_rows = Sc[Sc.kind == "SD (record statistic)"].set_index("scenario")
    b = sd_rows.loc["B: 24 files (RB1)", "median_change_vs_A"]
    b_no27 = sd_rows.loc["B without chb12_27 before its first seizure", "median_change_vs_A"]
    check("planted cause visible: B's SD rises vs A, and without chb12_27's first 120 s the rise mostly disappears",
          b > 0.05 and abs(b_no27) < 0.35 * b, f"(B {b:+.3f}, without the stretch {b_no27:+.3f})")
    C = pd.read_csv(out / "contributions.csv")
    check("planted cause visible: its share of B's squared deviation far above its share of windows",
          (C.chb12_27_before_first_seizure > 3 * C.share_of_windows_pre27).all(),
          f"(median share {C.chb12_27_before_first_seizure.median():.2f} vs windows {C.share_of_windows_pre27.iloc[0]:.3f})")
    W = pd.read_csv(out / "sampled_windows.csv.gz")
    for tag, fl in (("A", [f for f in T.FILES if f not in T.NEW]), ("B", list(T.FILES))):
        n_windows = {f: (T.FILES[f][0] * T.FS) // 1024 for f in fl}
        exp = expected_sampled(fl, {f: T.FILES[f][1] for f in fl}, n_windows)
        got = list(zip(W[W.set == tag].file, W[W.set == tag].window))
        check(f"sampled windows of set {tag} = independent re-implementation of the rule", got == exp,
              f"({len(got)} vs {len(exp)})")
    sh = W.filter(like="share_FP1-F7")
    check("per-window shares sum to 1 per set and channel",
          all(abs(W[W.set == s][[c for c in W.columns if c.startswith("share_") and c != "share_mean_over_channels"]].sum()
                  - 1).max() < 1e-9 for s in ("A", "B")) and len(sh.columns) == 1)
    F = pd.read_csv(out / "unflagged_windows.csv")
    u = F[F.change == "unflagged with B"]
    check("unflagged rows: peak above A's threshold and not above B's",
          bool(((u.max_peak_over_thr_A > 1) & (u.max_peak_over_thr_B <= 1)).all()), f"({len(u)} windows)")
    code = ("import sys,numpy as np; sys.path.insert(0, sys.argv[1]); import r2_rb1b as M;"
            "x=np.random.default_rng(0).normal(0,3e-5,(400,18,1024)).astype(np.float32); i,m=M.robust_scales(x);"
            "print(float(np.abs(i/3e-5-1).max()), float(np.abs(m/3e-5-1).max()))")
    v = subprocess.check_output([sys.executable, "-c", code, str(repo / "src")], text=True).split()
    check("robust scales of normal data = sigma (IQR/1.349, MAD x 1.4826)", max(map(float, v)) < 0.01, str(v))
    check("summary written", (out / "SUMMARY.md").exists())

    # ------------------------------------------------------------ failure paths
    def neg(tag, gate, path, mutate):
        keep = path.read_bytes()
        mutate(path)
        rc_, txt_, _ = run_rb1b(root, tag)
        path.write_bytes(keep)
        check(f"STOP at {gate}", rc_ != 0 and f"STOP RB1b: {gate}" in txt_, txt_.strip().splitlines()[-1][:120])

    def flip(p):
        b_ = bytearray(p.read_bytes())
        b_[-7] ^= 0xFF
        p.write_bytes(bytes(b_))

    def sd_up(p):
        s = json.loads(p.read_text())
        s["ch_std_uV"][5] *= 1 + 1e-5
        p.write_text(json.dumps(s))

    def flag_up(p):
        s = json.loads(p.read_text())
        s["chb12"]["flag5sd_in_common_files"][1] += 1
        p.write_text(json.dumps(s))

    def csv_up(col, row_filter):
        def f(p):
            d = pd.read_csv(p, dtype={"label": str})
            k = d.index[row_filter(d)][0]
            d.loc[k, col] += 1
            d.to_csv(p, index=False)
        return f
    neg("n_in", "G-in", raw / "chbmit" / "chb12" / "chb12_24.edf", flip)
    neg("n_stats", "G-stats", rb1 / "stats" / "chb12_stats.json", sd_up)
    neg("n_flags", "G-flags", rb1 / "diff_chb12.json", flag_up)
    rb0b = repo / "results" / "r2" / "r0_data" / "chb12_ref" / "rb0b"
    neg("n_clipf", "G-clip", rb0b / "C_clipping_files.csv", csv_up("windows_any_clipped", lambda d: d.file == "chb12_06.edf"))
    neg("n_clipc", "G-clip", rb0b / "C_clipping_channels.csv",
        csv_up("clipped_samples", lambda d: (d.file == "chb12_29.edf") & (d.channel == "CZ")))

    n_ok = sum(r[1] for r in RES)
    print(f"\n{n_ok}/{len(RES)} checks PASS in {time.time() - t0:.0f} s")
    print("ALL PASS" if n_ok == len(RES) else "FAILURES: " + "; ".join(r[0] for r in RES if not r[1]))
    sys.exit(0 if n_ok == len(RES) else 1)


if __name__ == "__main__":
    main()
