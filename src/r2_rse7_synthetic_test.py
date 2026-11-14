#!/usr/bin/env python
"""r2_rse7_synthetic_test.py -- tests of fix B (src/r2_e7exact.py) and of gate RS-E7 (src/r2_rse7.py, the notebook builder)
on SYNTHETIC data (build container only; never on Kaggle, never on real data).
Checks:
  X1  pelt_l2 = ruptures.Pelt(model="l2", min_size=2, jump=1) breakpoints on 900 synthetic series (n = 4 ... 500, six
      kinds incl. exact ties, piecewise-constant runs, a median-filled constant stretch, integer values, a large offset,
      random walks), the 3 penalties of E7 computed as d2_grid computes them; and with check="all" (every total exact at
      every step) -> E never let a decision through wrongly;
  X2  the bound E holds: max |prefix-sum cost - numpy cost| / E over 20,000 random segments of real-size series < 1;
  X3  d2_grid_exact(E7) gives exactly the rows of E7.d2_grid (segmentation + scoring, e1 grid) on a synthetic patient
      with signal-loss windows, ictal runs and short files; its code object is E7's; the shim refuses other parameters;
  X4  RS_E7 notebooks (built by the builder, run as Kaggle would) on a synthetic repository holding scores of the 23
      cases: every gate PASS; the merge gives RS-E7 PASS with 92 jobs; the call count per job = 3 x files of >= 4 windows;
  X5  STOP paths: a planted wrong segmentation (another r2_e7exact.py on the path) -> RS-E7[part] FAIL with the
      localisation; ruptures version != 1.1.10 -> G-code; a scores file missing -> G-in; merge with a missing part or a
      duplicated part -> FAIL;
  X6  resume: a part stopped by the session limit (NOT DONE) is completed by a second run with the first output
      attached; reused jobs byte-identical; the merge PASSES.
  python src/r2_rse7_synthetic_test.py [--root /tmp/rse7_synth] [--quick]
"""
import argparse
import importlib
import json
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import ruptures as rpt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import r2_e7exact as E7X                     # noqa: E402

RUNNER = r'''
import json, re, sys, time
from pathlib import Path
if __name__ == "__main__":
    nb = json.loads(Path(sys.argv[1]).read_text())
    ns = {"__name__": "__main__"}
    for i, c in enumerate(nb["cells"]):
        if c["cell_type"] != "code":
            continue
        src = "".join(c["source"])
        if src.startswith("%%writefile"):
            first, body = src.split("\n", 1)
            path = re.sub(r"\{(\w+)\}", lambda m: str(ns[m.group(1)]), first.split(None, 1)[1].strip())
            Path(path).write_text(body if body.endswith("\n") else body + "\n")
            continue
        exec(compile(src, f"{Path(sys.argv[1]).name}[cell {i}]", "exec"), ns)
'''


def ref(X, pen):
    return rpt.Pelt(model="l2", min_size=2, jump=1).fit(X).predict(pen=pen)


def series(rng, kind, n):
    if kind == 0:
        return rng.normal(size=n)
    if kind == 1:
        return np.repeat(rng.normal(size=n), int(rng.integers(2, 30)))[:n]
    if kind == 2:
        return rng.integers(0, 3, size=n).astype(float)
    if kind == 3:
        x = rng.random(n); x[n // 4:n // 2] = np.median(x); return x
    if kind == 4:
        return np.cumsum(rng.normal(size=n)) + 5.0
    return np.round(rng.random(n), 2) + 1e6


def pens_of(x):
    dif = np.diff(x)
    sigma = 1.4826 * np.median(np.abs(dif - np.median(dif))) / np.sqrt(2) + 1e-9
    return [c * sigma ** 2 * np.log(len(x)) for c in (1.0, 3.0, 10.0)]


def x1(n_series, nmax):
    rng = np.random.default_rng(11)
    bad = bad_all = calls = 0
    t_r = t_e = 0.0
    for i in range(n_series):
        n = int(rng.integers(4, nmax)) if i >= 30 else 4 + i % 6
        x = series(rng, i % 6, n)
        X = x.reshape(-1, 1)
        for pen in pens_of(x):
            t = time.perf_counter(); a = ref(X, pen); t_r += time.perf_counter() - t
            t = time.perf_counter(); b, _ = E7X.pelt_l2(X, pen); t_e += time.perf_counter() - t
            c, _ = E7X.pelt_l2(X, pen, check="all")
            calls += 1
            bad += a != b
            bad_all += a != c
            if a != b or a != c:
                print("X1 DIFF", i, i % 6, n, a[:6], b[:6], c[:6])
    assert bad == 0 and bad_all == 0, (bad, bad_all)
    print(f"X1 PASS: {calls} calls equal to ruptures (band and check=all); ruptures {t_r:.0f} s, exact {t_e:.1f} s")


def x2(n_seg=20000):
    rng = np.random.default_rng(12)
    worst = 0.0
    for k in range(20):
        n = int(rng.integers(1000, 15000))
        x = series(rng, k % 6, n) if k % 6 != 5 else rng.random(n) + 1e3
        S = x.reshape(-1, 1)
        xc = x - x.mean()
        P1 = np.r_[0.0, np.cumsum(xc)]; P2 = np.r_[0.0, np.cumsum(xc * xc)]
        E = E7X._bound(n, xc, float(P2[n]))
        for _ in range(n_seg // 20):
            t = int(rng.integers(0, n - 2)); b = int(rng.integers(t + 2, n + 1))
            s1 = P1[b] - P1[t]
            ca = (P2[b] - P2[t]) - s1 * s1 / (b - t)
            cn = S[t:b].var(axis=0).sum() * (b - t)
            worst = max(worst, abs(ca - cn) / E)
    assert worst < 1.0, worst
    print(f"X2 PASS: max |prefix-sum cost - numpy cost| / E = {worst:.2e}")


def synth_patient(rng, nfiles=6):
    lens = [int(rng.integers(300, 900)) for _ in range(nfiles)] + [3, 2]          # two short files
    n = sum(lens)
    fidx = np.repeat(np.arange(len(lens)), lens)
    x = rng.random(n) * 0.6
    ict = np.zeros(n, bool)
    for f in range(nfiles):
        m = np.flatnonzero(fidx == f)
        if f % 2 == 0:
            a = m[0] + int(rng.integers(50, len(m) - 60)); ict[a:a + int(rng.integers(5, 30))] = True
            x[ict] += 0.4
    sl = np.zeros(n, bool); sl[100:140] = True; sl[700:705] = True
    x[sl] = np.nan
    return dict(is_ictal=ict, is_signal_loss=sl, file_idx=fidx), x


def x3():
    import e1_normal_definition as E1
    import e7_ensemble_cpd as E7
    D2 = E7X.d2_grid_exact(E7)
    assert D2.__code__ is E7.d2_grid.__code__ and D2.__globals__["rpt"] is E7X.ExactRpt
    rng = np.random.default_rng(13)
    old = (E1.SMOOTH, E1.TOPS)
    E1.SMOOTH, E1.TOPS = [1, 3, 5, 15], [0.05, 0.02, 0.01, 0.005, 0.002, 0.001]
    try:
        for k in range(3):
            d, x = synth_patient(rng)
            a = E7.d2_grid(d, np.nan_to_num(x, nan=0.3))
            E7X.reset_stats()
            b = D2(d, np.nan_to_num(x, nan=0.3))
            assert a == b, (k, [r for r, s in zip(a, b) if r != s][:2])
            assert E7X.STATS["calls"] == 3 * 6, E7X.STATS
    finally:
        E1.SMOOTH, E1.TOPS = old
    for kw in (dict(jump=5), dict(min_size=3), dict(model="rbf")):
        try:
            E7X.ExactRpt.Pelt(**{**dict(model="l2", min_size=2, jump=1), **kw})
            raise AssertionError(f"shim accepted {kw}")
        except ValueError:
            pass
    print("X3 PASS: d2_grid_exact rows = E7.d2_grid rows (3 patients x 3 penalties x 6 tops); shim guards")


def world(root):
    """a repository with scores of the 23 cases (small) and the real e7_ensemble_cpd.py."""
    import r2_rse7 as RS
    repo = root / "repo"
    sc = repo / "results/r2/r1_system/rp/rp2/scores"
    sc.mkdir(parents=True)
    (repo / "src").mkdir()
    shutil.copyfile(ROOT / "src/e7_ensemble_cpd.py", repo / "src/e7_ensemble_cpd.py")
    rng = np.random.default_rng(14)
    for c in RS.CASES:
        lens = [int(rng.integers(40, 260)) for _ in range(int(rng.integers(1, 4)))] + ([3] if c == "chb17" else [])
        n = sum(lens)
        fidx = np.repeat(np.arange(len(lens)), lens)
        ok = np.ones(n, bool)
        if c in ("chb17", "PN10"):
            ok[10:40] = False
        df = pd.DataFrame(dict(window=np.arange(n), file_idx=fidx, t_in_file_s=0, ok=ok.astype(int), ictal=0))
        for s in (1, 2, 3, 4):
            v = series(rng, (s + len(c)) % 6, n) if s != 4 else rng.random(n)
            df[f"x_s{s}"] = np.where(ok, v, np.nan); df[f"xs_s{s}"] = df[f"x_s{s}"]
        df.to_csv(sc / f"{c}.csv.gz", index=False)
    return repo


def nb_run(root, nb, tag, extra=None, expect_fail=None):
    env = dict(os.environ, R2_TEST_REPO=str(root / "repo"), R2_TEST_INPUT=str(root / f"input_{tag}"),
               R2_TEST_WORK=str(root / f"work_{tag}"), R2_TEST_SCRATCH=str(root / f"scr_{tag}"), PYTHONHASHSEED="0")
    env.update(extra or {})
    (root / f"input_{tag}").mkdir(exist_ok=True)
    p = subprocess.run([sys.executable, str(root / "runner.py"), str(nb)], env=env, capture_output=True, text=True)
    tail = p.stdout[-3000:] + "\n" + p.stderr[-3000:]
    if expect_fail is None:
        assert p.returncode == 0, tail
    else:
        assert p.returncode != 0 and expect_fail in tail, tail
    return tail


def x4_x6(root):
    import r2_rse7 as RS
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    world(root)
    (root / "runner.py").write_text(RUNNER)
    nbdir = root / "nb"
    subprocess.check_call([sys.executable, str(ROOT / "src/r2_rse7_make_notebook.py"), "--run", "0" * 40, "--parts", "2"],
                          env=dict(os.environ, R2_NB_OUTDIR=str(nbdir)), stdout=subprocess.DEVNULL)
    nbs = sorted(nbdir.glob("RS_E7_*.ipynb"))
    assert [p.stem for p in nbs] == ["RS_E7_A", "RS_E7_B"], nbs
    parts = []
    for nb in nbs:
        tag = nb.stem[-1]
        nb_run(root, nb, tag)
        o = root / f"work_{tag}/r2/r1_system/rp_series/rse7/{tag}"
        g = {x["gate"]: x["status"] for x in json.loads((o / "gates.json").read_text())}
        assert g == {"G-code": "PASS", "G-in": "PASS", f"RS-E7[{tag}]": "PASS"}, g
        parts.append(o)
    env = dict(os.environ, THESIS_REPO=str(root / "repo"))
    m = subprocess.run([sys.executable, str(ROOT / "src/r2_rse7.py"), "--merge", *map(str, parts), "--out",
                        str(root / "merged")], env=env, capture_output=True, text=True)
    assert m.returncode == 0, m.stdout + m.stderr
    gm = json.loads((root / "merged/gate.json").read_text())
    assert gm["status"] == "PASS" and gm["jobs"] == 92 and gm["unequal"] == 0, gm
    F = pd.read_csv(root / "merged/files.csv")
    for c in RS.CASES:
        s = pd.read_csv(root / f"repo/results/r2/r1_system/rp/rp2/scores/{c}.csv.gz")
        nf = int((s.groupby("file_idx").size() >= 4).sum())
        assert (F[F.case == c].groupby("seed").size() == 3 * nf).all(), c
    print(f"X4 PASS: RS_E7_A + RS_E7_B every gate PASS; merge RS-E7 PASS, 92 jobs, {len(F)} calls")
    # X5 merge negatives
    m = subprocess.run([sys.executable, str(ROOT / "src/r2_rse7.py"), "--merge", str(parts[0]), "--out",
                        str(root / "merged_missing")], env=env, capture_output=True, text=True)
    assert m.returncode != 0 and "jobs missing" in (root / "merged_missing/gate.json").read_text()
    m = subprocess.run([sys.executable, str(ROOT / "src/r2_rse7.py"), "--merge", str(parts[0]), str(parts[0]),
                        str(parts[1]), "--out", str(root / "merged_dup")], env=env, capture_output=True, text=True)
    assert m.returncode != 0 and "more than once" in (root / "merged_dup/gate.json").read_text()
    print("X5 PASS: merge with a missing part / a duplicated part -> FAIL")
    nbA = nbs[0]
    # X5 planted wrong segmentation (test hook R2_TEST_E7X_FILE, honoured only in the synthetic test mode)
    bug = root / "bug"
    bug.mkdir()
    src = (ROOT / "src/r2_e7exact.py").read_text().replace("keep = T <= thr", "keep = T <= thr - 0.5 * pen")
    assert src != (ROOT / "src/r2_e7exact.py").read_text()
    (bug / "r2_e7exact.py").write_text(src)
    tail = nb_run(root, nbA, "bug", dict(R2_TEST_E7X_FILE=str(bug / "r2_e7exact.py")), expect_fail="RS-E7[A] FAIL")
    print("X5 PASS: planted wrong segmentation -> " + [l for l in tail.splitlines() if "RS-E7[A]" in l][-1][:160])
    # ruptures version
    (root / "ver").mkdir()
    (root / "ver/sitecustomize.py").write_text("import ruptures\nruptures.__version__ = '1.1.9'\n")
    nb_run(root, nbA, "ver", dict(PYTHONPATH=str(root / "ver")), expect_fail="G-code FAIL")
    print("X5 PASS: ruptures 1.1.9 -> G-code STOP")
    # missing scores file
    shutil.copytree(root / "repo", root / "repo_miss")
    case_a = json.loads(nbA.read_text())["cells"][1]["source"]
    first = [l for l in case_a if l.startswith("CASES")][0]
    victim = json.loads(first.split("=", 1)[1])[0]
    (root / f"repo_miss/results/r2/r1_system/rp/rp2/scores/{victim}.csv.gz").unlink()
    nb_run(root, nbA, "miss", dict(R2_TEST_REPO=str(root / "repo_miss")), expect_fail="G-in FAIL")
    print(f"X5 PASS: {victim} scores missing -> G-in STOP")
    # X6 resume
    nb_run(root, nbA, "lim", dict(R2_RSE7_LIMIT_H="0"), expect_fail="NOT DONE")
    prev = root / "work_lim"
    g = {x["gate"]: x for x in json.loads((prev / "r2/r1_system/rp_series/rse7/A/gates.json").read_text())}
    assert g["RS-E7[A]"]["status"] == "NOT DONE" and g["RS-E7[A]"]["jobs"] == 0, g["RS-E7[A]"]
    # half done: copy the finished jobs of the passing run A into a fake previous output (as Kaggle's attached output)
    half = root / "input_res/prev_output/r2/r1_system/rp_series/rse7/A/jobs"
    half.mkdir(parents=True)
    done_files = sorted((parts[0] / "jobs").glob("*.DONE.json"))[: len(list((parts[0] / "jobs").glob("*.DONE.json"))) // 2]
    for p in done_files:
        shutil.copyfile(p, half / p.name)
        shutil.copyfile(p.with_name(p.name.replace(".DONE.json", ".csv")), half / p.name.replace(".DONE.json", ".csv"))
    tail = nb_run(root, nbA, "res")
    assert f"({len(done_files)} reused)" in tail, tail[-1500:]
    o = root / "work_res/r2/r1_system/rp_series/rse7/A"
    for p in done_files:
        a = (o / "jobs" / p.name.replace(".DONE.json", ".csv")).read_bytes()
        assert a == p.with_name(p.name.replace(".DONE.json", ".csv")).read_bytes()
    m = subprocess.run([sys.executable, str(ROOT / "src/r2_rse7.py"), "--merge", str(o), str(parts[1]), "--out",
                        str(root / "merged_res")], env=env, capture_output=True, text=True)
    assert m.returncode == 0, m.stdout + m.stderr
    print(f"X6 PASS: session limit -> NOT DONE; resumed with {len(done_files)} jobs reused (byte-identical); merge PASS")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/tmp/rse7_synth")
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    x1(300 if a.quick else 900, 300 if a.quick else 500)
    x2()
    x3()
    x4_x6(Path(a.root))
    print(f"ALL PASS ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
